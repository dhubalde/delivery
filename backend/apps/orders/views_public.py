import hashlib
import json
from decimal import Decimal

from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Flavor, Product
from apps.catalog.services.flavor_policy import FlavorPolicyError
from apps.catalog.services.flavor_policy import PoteFlavorPolicy
from apps.common.models import IdempotencyKey
from apps.orders.models import Order, OrderItem
from apps.payments.gateways.mercadopago_mock import MercadoPagoMockGateway
from apps.payments.models import Payment
from apps.tenancy.models import Merchant
from apps.tenancy.services.hours import is_open


class PublicOrderCreateView(APIView):
    permission_classes = [AllowAny]
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
            order = Order.objects.create(
                merchant=merchant,
                code=code,
                customer_name="Guest",
                customer_phone="",
                fulfillment=fulfillment,
                state=Order.State.RECIBIDO,
                business_date=today,
                items_total=items_total,
                delivery_fee=delivery_fee,
                discount=Decimal("0.00"),
                total=total,
                cash_declared=any(p["method"] == Payment.Method.EFECTIVO for p in payments),
            )
            for vi in validated_items:
                prod = vi["product"]
                flavors_payload = []
                if vi["flavor_ids"]:
                    fls = Flavor.objects.filter(pk__in=vi["flavor_ids"])
                    flavors_payload = [{"id": f.pk, "name": f.name} for f in fls]
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    product_name=prod.name,
                    unit_price=Decimal(str(prod.price)),
                    quantity=vi["quantity"],
                    flavors=flavors_payload,
                    line_total=vi["line_total"],
                )
            for p in payments:
                method = p["method"]
                amount = Decimal(str(p["amount"]))
                if method == Payment.Method.EFECTIVO:
                    Payment.objects.create(order=order, method=method, amount=amount, status=Payment.Status.PENDING)
                else:
                    gw = MercadoPagoMockGateway.process(method, amount, order_id=order.pk)
                    status = Payment.Status.CONFIRMED if gw["status"] == "CONFIRMED" else Payment.Status.REJECTED
                    Payment.objects.create(order=order, method=method, amount=amount, status=status, gateway_ref=gw.get("gateway_ref"))

        body_resp = {"id": order.pk, "code": order.code, "total": str(order.total)}
        snapshot = {"body": body_resp, "content_type": "application/json"}
        try:
            IdempotencyKey.objects.create(key=key, merchant=merchant, endpoint=endpoint, request_hash=req_hash, response_snapshot=snapshot, status_code=201)
        except Exception:
            pass
        resp = Response(body_resp, status=201)
        resp["Idempotency-Key"] = key
        return resp
