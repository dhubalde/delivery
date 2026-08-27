import pytest

from apps.orders.models import Order
from apps.orders.state_machine import (
    GuardViolationError,
    InvalidTransitionError,
    OrderStateMachine,
)
from apps.orders.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db


class TestT14FiveStates:
    def test_t14_all_valid_forward_transitions(self):
        order = OrderFactory(state=Order.State.RECIBIDO)
        OrderStateMachine.validate(order, Order.State.PREPARACION)
        order.state = Order.State.PREPARACION
        order.cash_declared = True
        OrderStateMachine.validate(order, Order.State.FACTURACION)
        order.state = Order.State.FACTURACION
        OrderStateMachine.validate(order, Order.State.LOGISTICA)
        order.state = Order.State.LOGISTICA
        OrderStateMachine.validate(order, Order.State.ENTREGADO)

    def test_t14_terminal_states(self):
        assert OrderStateMachine.is_terminal(Order.State.ENTREGADO) is True
        assert OrderStateMachine.is_terminal(Order.State.CANCELADO) is True
        assert OrderStateMachine.is_terminal(Order.State.RECIBIDO) is False


class TestT15ForwardOnly:
    def test_br_ord_01_backward_transition_rejected(self):
        order = OrderFactory(state=Order.State.PREPARACION)
        with pytest.raises(InvalidTransitionError):
            OrderStateMachine.validate(order, Order.State.RECIBIDO)

    def test_br_ord_01_skip_state_rejected(self):
        order = OrderFactory(state=Order.State.RECIBIDO)
        with pytest.raises(InvalidTransitionError):
            OrderStateMachine.validate(order, Order.State.FACTURACION)

    def test_br_ord_01_terminal_no_outgoing(self):
        for terminal in [Order.State.ENTREGADO, Order.State.CANCELADO]:
            order = OrderFactory(state=terminal)
            with pytest.raises(InvalidTransitionError):
                OrderStateMachine.validate(order, Order.State.RECIBIDO)
            with pytest.raises(InvalidTransitionError):
                OrderStateMachine.validate(order, Order.State.PREPARACION)

    def test_br_ord_01_invalid_pair_raises(self):
        order = OrderFactory(state=Order.State.LOGISTICA)
        with pytest.raises(InvalidTransitionError):
            OrderStateMachine.validate(order, Order.State.FACTURACION)

    def test_br_ord_03_guard_cash_declared_required(self):
        order = OrderFactory(state=Order.State.PREPARACION, cash_declared=False)
        with pytest.raises(GuardViolationError):
            OrderStateMachine.validate(order, Order.State.FACTURACION)

    def test_br_ord_03_guard_passes_when_cash_declared(self):
        order = OrderFactory(state=Order.State.PREPARACION, cash_declared=True)
        OrderStateMachine.validate(order, Order.State.FACTURACION)


class TestT16CancellationOnlyFromRecibido:
    def test_br_ord_02_cancel_from_recibido_allowed(self):
        order = OrderFactory(state=Order.State.RECIBIDO)
        OrderStateMachine.validate(order, Order.State.CANCELADO)

    def test_br_ord_02_cancel_from_preparacion_rejected(self):
        order = OrderFactory(state=Order.State.PREPARACION)
        with pytest.raises(InvalidTransitionError):
            OrderStateMachine.validate(order, Order.State.CANCELADO)

    def test_br_ord_02_cancel_from_facturacion_rejected(self):
        order = OrderFactory(state=Order.State.FACTURACION)
        with pytest.raises(InvalidTransitionError):
            OrderStateMachine.validate(order, Order.State.CANCELADO)

    def test_br_ord_02_cancel_from_logistica_rejected(self):
        order = OrderFactory(state=Order.State.LOGISTICA)
        with pytest.raises(InvalidTransitionError):
            OrderStateMachine.validate(order, Order.State.CANCELADO)

    def test_br_ord_06_cancelado_only_from_recibido(self):
        order = OrderFactory(state=Order.State.ENTREGADO)
        with pytest.raises(InvalidTransitionError):
            OrderStateMachine.validate(order, Order.State.CANCELADO)
