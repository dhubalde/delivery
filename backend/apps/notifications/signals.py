from datetime import timedelta

from django.db.models import signals as django_signals
from django.dispatch import receiver
from django.utils import timezone

from apps.notifications.models import Notification, NotificationType, NotificationRecipientType
from apps.orders.models import Order
from apps.payments.models import Payment


def _has_recent_notification(order, ntype, recipient_type=None, seconds=60):
    """Return True if a notification for same order+type (+recipient) exists within seconds."""
    if not order or not order.pk:
        return False
    cutoff = timezone.now() - timedelta(seconds=seconds)
    qs = Notification.all_objects.filter(order=order, type=ntype, created_at__gte=cutoff)
    if recipient_type:
        qs = qs.filter(recipient_type=recipient_type)
    return qs.exists()


def create_order_notification(order, recipient_type, recipient_name, message, ntype):
    # Global dedup: prevent exact duplicate message for same order+type+recipient within 60s.
    # This allows distinct state messages (preparacion vs logistica) to coexist, but blocks repeats.
    if order and order.pk:
        cutoff = timezone.now() - timedelta(seconds=60)
        if Notification.all_objects.filter(
            order=order, type=ntype, recipient_type=recipient_type, message=message, created_at__gte=cutoff
        ).exists():
            return None
    # Extra guard for RECIBIDO: NEW_ORDER and ORDER_STATE_CHANGE with "recibido" are semantically same event.
    # If either exists recently, suppress the other to avoid 2 notifications for one order creation.
    # This must NOT block other state messages (preparacion/logistica) which also use ORDER_STATE_CHANGE.
    if "recibido" in message.lower() and ntype in (NotificationType.NEW_ORDER, NotificationType.ORDER_STATE_CHANGE) and order and order.pk:
        cutoff = timezone.now() - timedelta(seconds=60)
        if Notification.all_objects.filter(
            order=order,
            type__in=[NotificationType.NEW_ORDER, NotificationType.ORDER_STATE_CHANGE],
            created_at__gte=cutoff,
        ).exists():
            return None
    return Notification.objects.create(
        merchant_id=order.merchant_id,
        recipient_type=recipient_type,
        recipient_name=recipient_name,
        order=order,
        message=message,
        type=ntype,
    )


def notify_state_transition(order, old_state):
    """Create minimal notifications: customer ONLY on LOGISTICA ("esta en camino"),
    cashier when a LOGISTICA order gets cancelled.
    Customer policy (LOGISTICA-only): the customer bell must not notify on
    RECIBIDO or PREPARACION, only when the order is on its way."""
    if not order.merchant_id:
        return
    state = order.state

    # Customer: order going to logistics (sole customer notification)
    if state == Order.State.LOGISTICA and old_state != Order.State.LOGISTICA:
        create_order_notification(
            order, NotificationRecipientType.CUSTOMER, order.customer_name,
            f"Tu pedido #{order.code} está en camino", NotificationType.ORDER_STATE_CHANGE,
        )
    # Cashier: order cancelled after having been in logistics
    elif state == Order.State.CANCELADO and old_state == Order.State.LOGISTICA:
        create_order_notification(
            order, NotificationRecipientType.EMPLOYEE, "Cajero",
            f"Pedido #{order.code} cancelado después de haber salido por logística",
            NotificationType.ORDER_STATE_CHANGE,
        )


@receiver(django_signals.post_save, sender=Order)
def _on_order_created(sender, instance, created, **kwargs):
    # Customer policy (LOGISTICA-only): no CUSTOMER notification on order
    # creation (RECIBIDO). The customer bell only notifies on LOGISTICA.
    return


@receiver(django_signals.post_save, sender=Payment)
def _on_payment_created(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.method == Payment.Method.EFECTIVO and instance.status == Payment.Status.PENDING:
        order = instance.order
        if order and order.merchant_id:
            # Gate: only notify immediately if order is already in LOGISTICA/FACTURACION.
            # This prevents early notification at RECIBIDO and before logistics.
            # Periodic engine (_maybe_create_cash_reminders) handles the 45min reminder.
            if order.state not in (Order.State.LOGISTICA, Order.State.FACTURACION):
                return
            # Dedup: avoid repeat PAYMENT_PENDING within 60s (e.g., multiple Payment creates)
            if _has_recent_notification(order, NotificationType.PAYMENT_PENDING, NotificationRecipientType.EMPLOYEE, seconds=60):
                return
            create_order_notification(
                order, NotificationRecipientType.EMPLOYEE, "Cajero",
                f"Pago en efectivo pendiente para pedido #{order.code}",
                NotificationType.PAYMENT_PENDING,
            )