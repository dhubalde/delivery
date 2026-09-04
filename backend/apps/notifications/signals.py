from django.db.models import signals as django_signals
from django.dispatch import receiver

from apps.notifications.models import Notification, NotificationType, NotificationRecipientType
from apps.orders.models import Order
from apps.payments.models import Payment


def create_order_notification(order, recipient_type, recipient_name, message, ntype):
    Notification.objects.create(
        merchant_id=order.merchant_id,
        recipient_type=recipient_type,
        recipient_name=recipient_name,
        order=order,
        message=message,
        type=ntype,
    )


def notify_state_transition(order, old_state):
    """Create minimal notifications: customer on RECIBIDO and LOGISTICA,
    cashier when a LOGISTICA order gets cancelled."""
    if not order.merchant_id:
        return
    state = order.state

    # Customer: order received
    if state == Order.State.RECIBIDO and old_state != Order.State.RECIBIDO:
        create_order_notification(
            order, NotificationRecipientType.CUSTOMER, order.customer_name,
            f"Tu pedido #{order.code} fue recibido", NotificationType.ORDER_STATE_CHANGE,
        )
    # Customer: order in preparation
    elif state == Order.State.PREPARACION and old_state != Order.State.PREPARACION:
        create_order_notification(
            order, NotificationRecipientType.CUSTOMER, order.customer_name,
            f"Tu pedido #{order.code} está en preparación", NotificationType.ORDER_STATE_CHANGE,
        )
    # Customer: order going to logistics
    elif state == Order.State.LOGISTICA and old_state != Order.State.LOGISTICA:
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
    if not created or not instance.merchant_id:
        return
    if instance.state == Order.State.RECIBIDO:
        # Customer gets notified when their order is first received
        create_order_notification(
            instance, NotificationRecipientType.CUSTOMER, instance.customer_name,
            f"Tu pedido #{instance.code} fue recibido",
            NotificationType.NEW_ORDER,
        )


@receiver(django_signals.post_save, sender=Payment)
def _on_payment_created(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.method == Payment.Method.EFECTIVO and instance.status == Payment.Status.PENDING:
        order = instance.order
        if order and order.merchant_id:
            create_order_notification(
                order, NotificationRecipientType.EMPLOYEE, "Cajero",
                f"Pago en efectivo pendiente para pedido #{order.code}",
                NotificationType.PAYMENT_PENDING,
            )