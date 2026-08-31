from apps.orders.models import Order


class InvalidTransitionError(Exception):
    pass


class GuardViolationError(InvalidTransitionError):
    pass


TERMINAL_STATES = {Order.State.ENTREGADO, Order.State.CANCELADO}

TRANSITIONS = {
    (Order.State.RECIBIDO, Order.State.PREPARACION): None,
    (Order.State.PREPARACION, Order.State.FACTURACION): "cash_declared",
    (Order.State.FACTURACION, Order.State.LOGISTICA): None,
    (Order.State.LOGISTICA, Order.State.ENTREGADO): None,
    (Order.State.RECIBIDO, Order.State.CANCELADO): None,
    (Order.State.LOGISTICA, Order.State.CANCELADO): None,
}


def _check_guard(order, guard):
    if guard == "cash_declared" and not order.cash_declared:
        try:
            payments = list(order.payments.all())
        except Exception:
            payments = []
        needs_cash = any(getattr(p, "method", None) == "EFECTIVO" and getattr(p, "status", None) != "CONFIRMED" for p in payments)
        if payments and not needs_cash:
            return
        if not payments:
            return
        raise GuardViolationError("cash_declared required for PREPARACION -> FACTURACION")


class OrderStateMachine:
    @staticmethod
    def can_transition(from_state, to_state):
        return (from_state, to_state) in TRANSITIONS

    @staticmethod
    def is_terminal(state):
        return state in TERMINAL_STATES

    @staticmethod
    def validate(order, to_state):
        from_state = order.state
        if from_state in TERMINAL_STATES:
            raise InvalidTransitionError(f"{from_state} is terminal, no outgoing transitions")
        if (from_state, to_state) not in TRANSITIONS:
            raise InvalidTransitionError(f"Invalid transition {from_state} -> {to_state}")
        guard = TRANSITIONS[(from_state, to_state)]
        if guard:
            _check_guard(order, guard)

    @staticmethod
    def allowed_targets(from_state):
        return [to for (frm, to) in TRANSITIONS if frm == from_state]
