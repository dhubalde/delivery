from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404

from apps.orders.models import Order
from apps.payments.gateways.mercado_pago import MercadoPagoError, MercadoPagoGateway
from apps.payments.models import Payment
from apps.payments.services import (
    MPNotConfiguredError,
    PaymentService,
    PaymentValidationError,
    CashConfirmationError,
)


def _resolve_active_merchant(slug):
    from apps.tenancy.models import Merchant

    merchant = Merchant.all_objects.filter(slug=slug).first()
    if merchant is None or merchant.deleted_at is not None or not merchant.is_active:
        return None
    return merchant


def _base_url(request) -> str:
    """Origin with trailing slash. Frontend routes and /api/* both resolve
    under it (the web app proxies /api to the backend)."""
    return request.build_absolute_uri("/")


class BaseCheckoutView(APIView):
    def _create(self, request, order):
        base = _base_url(request)
        merchant = order.merchant
        try:
            pay = PaymentService.create_checkout(
                order,
                success_url=f"{base}{merchant.slug}/my-orders",
                notification_url=f"{base}api/payments/webhook/{merchant.slug}/",
            )
        except MPNotConfiguredError as e:
            return Response({"error": {"code": "MP_NOT_CONFIGURED", "message": str(e)}}, status=409)
        except PaymentValidationError as e:
            return Response({"error": {"code": "INVALID_PAYMENT_STATE", "message": str(e)}}, status=409)
        return Response({"id": pay.pk, "preference_id": pay.gateway_ref, "init_point": pay.checkout_url})


class PublicOrderPayView(BaseCheckoutView):
    """Customer checkout: create/reuse the Mercado Pago preference for a
    just-created order. Idempotent by design (existing preference is reused)."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, slug, pk):
        merchant = _resolve_active_merchant(slug)
        if merchant is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "Unknown merchant"}}, status=404)
        order = get_object_or_404(Order, pk=pk, merchant=merchant)
        return self._create(request, order)


class OrderPaymentLinkView(BaseCheckoutView):
    """Staff: generate a payment link for a phone order (send it to the
    customer, e.g. via WhatsApp). The order enters the board once paid."""

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, pk):
        order = get_object_or_404(Order.objects.select_related("merchant"), pk=pk)
        profile = getattr(request.user, "platform_profile", None)
        if profile is not None and profile.role != "ADMIN" and profile.merchant_id != order.merchant_id:
            return Response({"error": {"code": "TENANT_MISMATCH", "message": "Order belongs to another merchant."}}, status=403)
        return self._create(request, order)


class MercadoPagoWebhookView(APIView):
    """Public Mercado Pago notifications: /api/payments/webhook/<merchant-slug>/.
    Signature is validated when the merchant has a webhook secret; the payment
    state itself is always re-fetched from the MP API with the merchant token."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, merchant_slug):
        merchant = _resolve_active_merchant(merchant_slug)
        if merchant is None:
            return Response(status=404)
        body = request.data if isinstance(request.data, dict) else {}
        data_id = (
            request.query_params.get("data.id")
            or request.query_params.get("id")
            or ((body.get("data") or {}).get("id"))
        )
        ntype = request.query_params.get("type") or request.query_params.get("topic") or body.get("type")
        if ntype != "payment":
            return Response(status=200)
        if not data_id:
            return Response(status=200)
        secret = merchant.mp_webhook_secret
        if secret and not MercadoPagoGateway.validate_signature(
            request.headers.get("X-Signature"),
            request.headers.get("X-Request-Id"),
            str(data_id),
            secret,
        ):
            return Response({"error": {"code": "INVALID_SIGNATURE"}}, status=401)
        try:
            mp_payment = PaymentService.fetch_gateway_payment(merchant, data_id)
        except MercadoPagoError:
            # Let Mercado Pago retry: the notification was not processed.
            return Response(status=502)
        ref = mp_payment.get("external_reference") or ""
        try:
            order_id = int(ref)
        except (TypeError, ValueError):
            return Response(status=200)
        order = Order.objects.filter(pk=order_id, merchant=merchant).first()
        if order is None:
            return Response(status=200)
        try:
            PaymentService.apply_gateway_result(order, mp_payment)
        except PaymentValidationError:
            return Response(status=200)
        return Response(status=200)



class PaymentConfirmTransferView(APIView):
    """Staff confirmation of a manual bank-transfer payment (operator saw the deposit)."""

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, pk):
        payment = get_object_or_404(
            Payment.objects.select_related("order"),
            pk=pk,
        )
        order: Order = payment.order
        profile = getattr(request.user, "platform_profile", None)
        if profile is not None:
            if profile.role != "ADMIN" and profile.merchant_id != order.merchant_id:
                return Response(
                    {"error": {"code": "TENANT_MISMATCH", "message": "Payment belongs to another merchant."}},
                    status=403,
                )
            sector = getattr(profile, "sector", None)
            if profile.role != "ADMIN" and sector not in (None, "TODAS", order.state):
                return Response(
                    {"error": {"code": "SECTOR_FORBIDDEN", "message": f"This user only operates {sector}."}},
                    status=403,
                )
        try:
            updated = PaymentService.confirm_transfer(payment.pk, confirmed_by=str(request.user))
        except CashConfirmationError as e:
            return Response({"error": {"code": "INVALID_PAYMENT_STATE", "message": str(e)}}, status=409)
        return Response({"id": updated.pk, "status": updated.status, "method": updated.method})
