from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.state_machine import OrderStateMachine


class OrderService:
    @staticmethod
    @transaction.atomic
    def transition(order_id, to_state, actor=None, reason=None):
        order = Order.objects.select_for_update().get(pk=order_id)
        old_state = order.state
        OrderStateMachine.validate(order, to_state)
        if old_state == Order.State.FACTURACION and to_state == Order.State.LOGISTICA:
            from apps.payments.services import PaymentService

            PaymentService.validate_for_logistics(order)
        order.state = to_state
        update_fields = ["state", "updated_at"]
        if to_state == Order.State.CANCELADO:
            if reason:
                order.cancel_reason = reason[:500]
                update_fields.append("cancel_reason")
            order.canceled_at = timezone.now()
            update_fields.append("canceled_at")
        order.save(update_fields=update_fields)
        from apps.notifications.signals import notify_state_transition

        notify_state_transition(order, old_state)
        from apps.audit.services import emit

        emit(
            merchant_id=order.merchant_id,
            actor=actor,
            entity="Order",
            entity_id=order.pk,
            action="STATE_TRANSITION",
            old_value={"state": old_state},
            new_value={"state": to_state},
        )
        return order

    @staticmethod
    @transaction.atomic
    def cancel(order_id, actor=None):
        return OrderService.transition(order_id, Order.State.CANCELADO, actor=actor)
