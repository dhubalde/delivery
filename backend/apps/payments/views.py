from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404

from apps.orders.models import Order
from apps.payments.models import Payment
from apps.payments.services import PaymentService, CashConfirmationError


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
