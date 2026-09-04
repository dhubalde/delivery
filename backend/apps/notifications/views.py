import logging

from django.utils import timezone

from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.notifications.models import Notification, NotificationRecipientType, NotificationType
from apps.notifications.serializers import NotificationSerializer

logger = logging.getLogger(__name__)

LOGISTICS_REMINDER_MINUTES = 15


def _require_merchant_id(request):
    mid = getattr(request, "tenant_merchant_id", None)
    if mid is not None:
        return mid
    slug = request.query_params.get("merchant_slug") or request.headers.get("X-Merchant-Slug") or request.META.get("HTTP_X_MERCHANT_SLUG")
    if slug:
        from apps.tenancy.models import Merchant
        m = Merchant.objects.filter(slug=slug).first()
        if m:
            return m.pk
    raw = request.query_params.get("merchant_id") or request.headers.get("X-Merchant-Id") or request.META.get("HTTP_X_MERCHANT_ID")
    if raw:
        try:
            return int(raw)
        except (ValueError, TypeError):
            pass
    raise ValidationError({"merchant": "merchant context required (merchant_slug, X-Merchant-Slug or X-Merchant-Id header)"})


def _maybe_create_cash_reminders(mid: int) -> None:
    """Auto-create PAYMENT_PENDING reminders for cash orders stuck in LOGISTICA/FACTURACION.

    Only creates a notification if no PAYMENT_PENDING notification for that order
    exists in the last LOGISTICS_REMINDER_MINUTES minutes. Wrapped in try/except
    so listing never breaks.
    """
    try:
        from datetime import timedelta

        from apps.orders.models import Order
        from apps.payments.models import Payment

        cutoff = timezone.now() - timedelta(minutes=LOGISTICS_REMINDER_MINUTES)
        # Orders in logistics/billing with pending cash payment older than 15 min
        orders = (
            Order.objects.for_merchant(mid)
            .filter(
                state__in=[Order.State.LOGISTICA, Order.State.FACTURACION],
                payments__method=Payment.Method.EFECTIVO,
                payments__status=Payment.Status.PENDING,
                updated_at__lte=cutoff,
            )
            .distinct()
        )
        for order in orders:
            recent_exists = Notification.all_objects.filter(
                merchant_id=mid,
                order=order,
                type=NotificationType.PAYMENT_PENDING,
                created_at__gte=cutoff,
            ).exists()
            if recent_exists:
                continue
            try:
                Notification.objects.create(
                    merchant_id=mid,
                    recipient_type=NotificationRecipientType.EMPLOYEE,
                    order=order,
                    type=NotificationType.PAYMENT_PENDING,
                    message=f"Pago en efectivo pendiente para pedido #{order.code} - lleva {LOGISTICS_REMINDER_MINUTES}min en logistica",
                )
            except Exception as e:
                logger.warning("Failed to create cash reminder for order %s: %s", order.pk, e)
    except Exception as e:
        logger.warning("Cash reminder check failed for merchant %s: %s", mid, e)


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        # Best-effort reminder generation - never break listing
        _maybe_create_cash_reminders(mid)
        qs = Notification.objects.for_merchant(mid).order_by("-created_at")
        unread = self.request.query_params.get("unread")
        if unread == "true":
            qs = qs.filter(is_read=False)
        recipient_type = self.request.query_params.get("recipient_type")
        if recipient_type in (NotificationRecipientType.EMPLOYEE, NotificationRecipientType.CUSTOMER):
            qs = qs.filter(recipient_type=recipient_type)
        return qs


class NotificationDetailView(generics.RetrieveAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        return Notification.objects.for_merchant(mid)


class NotificationDeleteView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    http_method_names = ["delete"]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        return Notification.objects.for_merchant(mid)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationMarkReadView(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["post"]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        return Notification.objects.for_merchant(mid)

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_read = True
        instance.save(update_fields=["is_read", "updated_at"])
        return Response(NotificationSerializer(instance, context={"request": request}).data)


class NotificationMarkAllReadView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    http_method_names = ["post"]

    def post(self, request):
        mid = _require_merchant_id(self.request)
        updated = Notification.objects.filter(merchant_id=mid, is_read=False).update(is_read=True)
        return Response({"updated": updated})