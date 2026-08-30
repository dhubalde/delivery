import hashlib
from decimal import Decimal

from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Flavor, Product
from apps.catalog.services.flavor_policy import FlavorPolicyError, PoteFlavorPolicy
from apps.common.models import IdempotencyKey
from apps.orders.models import Order, OrderItem
from apps.orders.services import OrderService
from apps.orders.state_machine import GuardViolationError, InvalidTransitionError
from apps.payments.gateways.mercadopago_mock import MercadoPagoMockGateway
from apps.payments.models import Payment
from apps.tenancy.models import Merchant
from apps.tenancy.services.hours import is_open


def _resolve_merchant_id(request):
    mid = getattr(request, "tenant_merchant_id", None)
    if mid is not None:
        return mid
    slug = request.query_params.get("merchant_slug") or request.headers.get("X-Merchant-Slug") or request.META.get("HTTP_X_MERCHANT_SLUG")
    if slug:
        try:
            m = Merchant.objects.filter(slug=slug).first()
            if m:
                return m.pk
            m = Merchant.all_objects.filter(slug=slug).first()
            if m:
                return m.pk
        except Exception:
            pass
    raw = request.query_params.get("merchant_id") or request.headers.get("X-Merchant-Id") or request.META.get("HTTP_X_MERCHANT_ID")
    if raw:
        try:
            return int(raw)
        except (ValueError, TypeError):
            return None
    return None


def _serialize_order(order):
    items = []
    for it in order.items.all():
        items.append({"id": it.pk, "product_id": it.product_id, "product_name": it.product_name, "unit_price": str(it.unit_price), "quantity": it.quantity, "flavors": it.flavors, "line_total": str(it.line_total)})
    payments = []
    try:
        for p in order.payments.all():
            payments.append({"id": p.pk, "method": p.method, "amount": str(p.amount), "status": p.status, "gateway_ref": p.gateway_ref})
    except Exception:
        pass
    return {"id": order.pk, "code": order.code, "merchant_id": order.merchant_id, "customer_name": order.customer_name, "customer_phone": order.customer_phone, "fulfillment": order.fulfillment, "state": order.state, "business_date": str(order.business_date), "address": order.address, "items_total": str(order.items_total), "delivery_fee": str(order.delivery_fee), "discount": str(order.discount), "total": str(order.total), "cash_declared": order.cash_declared, "items": items, "payments": payments, "created_at": order.created_at.isoformat() if hasattr(order, "created_at") and order.created_at else None}


class PublicOrderCreateView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, slug):
        key = request.headers.get("Idempotency-Key") or request.META.get("HTTP_IDEMPOTENCY_KEY") or request.META.get("HTTP_IDEMPOTENCY-KEY")
        if not key:
            return Response({"error": {"code": "IDEMPOTENCY_KEY_REQUIRED", "message": "Idempotency-Key header required"}}, status=400)
        merchant = get_object_or_404(Merchant, slug=slug)
        try:
            open_val = is_open(merchant)
        except Exception:
            open_val = True
        if not open_val:
            return Response({"error": {"code": "SCHEDULE_CLOSED", "message": "Local cerrado (BR-HRS-02)"}}, status=409)
        endpoint = request.path
        body = request.body or b""
        req_hash = hashlib.sha256(body).hexdigest()
        existing = IdempotencyKey.objects.filter(key=key, endpoint=endpoint).first()
        if existing is not None:
            if existing.request_hash != req_hash:
                return Response({"error": {"code": "IDEMPOTENCY_KEY_REUSED", "message": "Idempotency-Key already used with different payload"}}, status=409)
            cached = (existing.response_snapshot or {}).get("body", existing.response_snapshot)
            status_code = existing.status_code or 201
            resp = Response(cached, status=status_code)
            resp["Idempotency-Replayed"] = "true"
            return resp
        data = request.data or {}
        items = data.get("items")
        payments = data.get("payments")
        fulfillment = data.get("fulfillment") or "DELIVERY"
        if not isinstance(items, list) or len(items) == 0:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "items required", "details": {"items": "At least one item required"}}}, status=400)
        if not isinstance(payments, list) or len(payments) == 0:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "payments required", "details": {"payments": "At least one payment required"}}}, status=400)
        if fulfillment not in (Order.Fulfillment.DELIVERY, Order.Fulfillment.PICKUP):
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Invalid fulfillment", "details": {"fulfillment": "Must be DELIVERY or PICKUP"}}}, status=400)
        allowed_methods = {c[0] for c in Payment.Method.choices}
        for p in payments:
            if p.get("method") not in allowed_methods:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": f"Invalid method {p.get('method')}", "details": {"payments": f"Invalid method {p.get('method')}"}}}, status=400)
            try:
                amt = Decimal(str(p.get("amount")))
            except Exception:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": "Invalid amount", "details": {"payments": "Invalid amount"}}}, status=400)
            if amt <= Decimal("0"):
                return Response({"error": {"code": "VALIDATION_ERROR", "message": "Amount must be > 0", "details": {"payments": "Amount must be > 0"}}}, status=400)
        validated_items = []
        items_total = Decimal("0.00")
        for idx, it in enumerate(items):
            pid = it.get("product_id")
            qty = it.get("quantity")
            flavor_ids = it.get("flavor_ids") or []
            if pid is None or qty is None:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": "product_id and quantity required", "details": {f"items[{idx}]": "product_id and quantity required"}}}, status=400)
            try:
                qty = int(qty)
            except Exception:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": "Invalid quantity", "details": {f"items[{idx}].quantity": "Invalid quantity"}}}, status=400)
            if qty < 1:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": "quantity must be >=1", "details": {f"items[{idx}].quantity": "quantity must be >=1"}}}, status=400)
            try:
                product = Product.objects.get(pk=pid)
            except Product.DoesNotExist:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": f"Product {pid} not found", "details": {f"items[{idx}].product_id": f"Product {pid} not found"}}}, status=400)
            if product.merchant_id != merchant.pk:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": f"Product {pid} does not belong to merchant {slug}", "details": {f"items[{idx}].product_id": "Product does not belong to merchant"}}}, status=400)
            if not isinstance(flavor_ids, list):
                return Response({"error": {"code": "VALIDATION_ERROR", "message": "flavor_ids must be list", "details": {f"items[{idx}].flavor_ids": "must be list"}}}, status=400)
            if flavor_ids:
                cnt = Flavor.objects.filter(pk__in=flavor_ids, merchant=merchant).count()
                if cnt != len(flavor_ids):
                    return Response({"error": {"code": "VALIDATION_ERROR", "message": "Invalid flavor_ids", "details": {f"items[{idx}].flavor_ids": "One or more flavors not found for merchant"}}}, status=400)
            try:
                PoteFlavorPolicy.validate(product, flavor_ids)
            except FlavorPolicyError as e:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": str(e), "details": {f"items[{idx}].flavor_ids": str(e)}}}, status=400)
            line_total = Decimal(str(product.price)) * Decimal(str(qty))
            items_total += line_total
            validated_items.append({"product": product, "quantity": qty, "flavor_ids": list(flavor_ids), "line_total": line_total})
        delivery_fee = Decimal("0.00")
        if fulfillment == Order.Fulfillment.DELIVERY:
            try:
                from apps.delivery.models import DeliveryConfig
                from apps.delivery.services import DeliveryFeeCalculator
                cfg = DeliveryConfig.objects.filter(merchant=merchant).first()
                if cfg is not None:
                    delivery_fee = DeliveryFeeCalculator.calc(cfg, items_total=items_total)
            except Exception:
                delivery_fee = Decimal("0.00")
        total = items_total + delivery_fee
        pay_sum = sum(Decimal(str(p["amount"])) for p in payments)
        if pay_sum != total:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": f"Payment amounts sum {pay_sum} != order total {total} (BR-PAY-05)", "details": {"payments": f"Payment amounts sum {pay_sum} != order total {total} (BR-PAY-05)"}}}, status=400)
        today = timezone.localdate()
        with transaction.atomic():
            max_code = Order.objects.filter(merchant=merchant, business_date=today).aggregate(m=Max("code"))["m"] or 0
            code = max_code + 1
            order = Order.objects.create(merchant=merchant, code=code, customer_name=data.get("customer_name") or "Guest", customer_phone=data.get("customer_phone") or "", fulfillment=fulfillment, state=Order.State.RECIBIDO, business_date=today, address=data.get("address") or "", items_total=items_total, delivery_fee=delivery_fee, discount=Decimal("0.00"), total=total, cash_declared=any(p["method"] == Payment.Method.EFECTIVO for p in payments))
            for vi in validated_items:
                prod = vi["product"]
                flavors_payload = []
                if vi["flavor_ids"]:
                    fls = Flavor.objects.filter(pk__in=vi["flavor_ids"])
                    flavors_payload = [{"id": f.pk, "name": f.name} for f in fls]
                OrderItem.objects.create(order=order, product=prod, product_name=prod.name, unit_price=Decimal(str(prod.price)), quantity=vi["quantity"], flavors=flavors_payload, line_total=vi["line_total"])
            for p in payments:
                method = p["method"]
                amount = Decimal(str(p["amount"]))
                if method == Payment.Method.EFECTIVO:
                    Payment.objects.create(order=order, method=method, amount=amount, status=Payment.Status.PENDING)
                else:
                    gw = MercadoPagoMockGateway.process(method, amount, order_id=order.pk)
                    st = Payment.Status.CONFIRMED if gw["status"] == "CONFIRMED" else Payment.Status.REJECTED
                    Payment.objects.create(order=order, method=method, amount=amount, status=st, gateway_ref=gw.get("gateway_ref"))
        body_resp = {"id": order.pk, "code": order.code, "total": str(order.total)}
        snapshot = {"body": body_resp, "content_type": "application/json"}
        try:
            IdempotencyKey.objects.create(key=key, merchant=merchant, endpoint=endpoint, request_hash=req_hash, response_snapshot=snapshot, status_code=201)
        except Exception:
            pass
        resp = Response(body_resp, status=201)
        resp["Idempotency-Key"] = key
        return resp


class OrderBoardView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        mid = _resolve_merchant_id(request)
        qs = Order.objects.all().prefetch_related("items", "payments").order_by("-business_date", "-code")
        if mid is not None:
            qs = qs.filter(merchant_id=mid)
        state = request.query_params.get("state")
        if state:
            qs = qs.filter(state=state)
        business_date = request.query_params.get("business_date")
        if business_date:
            qs = qs.filter(business_date=business_date)
        data = [_serialize_order(o) for o in qs]
        return Response(data)


class OrderDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        mid = _resolve_merchant_id(request)
        qs = Order.objects.all().prefetch_related("items", "payments")
        if mid is not None:
            qs = qs.filter(merchant_id=mid)
        order = get_object_or_404(qs, pk=pk)
        return Response(_serialize_order(order))


class OrderTransitionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        mid = _resolve_merchant_id(request)
        qs = Order.objects.all()
        if mid is not None:
            qs = qs.filter(merchant_id=mid)
        order = get_object_or_404(qs, pk=pk)
        to_state = (request.data or {}).get("to_state")
        if not to_state:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "to_state required"}}, status=400)
        if to_state not in Order.State.values:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": f"Invalid to_state {to_state}"}}, status=400)
        try:
            updated = OrderService.transition(order.pk, to_state)
        except (InvalidTransitionError, GuardViolationError) as e:
            return Response({"error": {"code": "INVALID_TRANSITION", "message": str(e)}}, status=409)
        except Order.DoesNotExist:
            return Response({"error": {"code": "NOT_FOUND", "message": "Order not found"}}, status=404)
        if to_state == Order.State.ENTREGADO:
            try:
                pending_cash = Payment.objects.filter(order_id=updated.pk, method=Payment.Method.EFECTIVO, status=Payment.Status.PENDING)
                for p in pending_cash:
                    p.status = Payment.Status.CONFIRMED
                    p.confirmed_at = timezone.now()
                    p.save(update_fields=["status", "confirmed_at", "updated_at"])
            except Exception:
                pass
        updated = Order.objects.prefetch_related("items", "payments").get(pk=updated.pk)
        return Response(_serialize_order(updated))
