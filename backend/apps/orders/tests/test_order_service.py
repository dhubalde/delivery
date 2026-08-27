import pytest

from apps.orders.models import Order
from apps.orders.services import OrderService
from apps.orders.state_machine import GuardViolationError, InvalidTransitionError
from apps.orders.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db


class TestOrderServiceTransition:
    def test_service_transition_persists_and_refreshes_business_date(self):
        order = OrderFactory(state=Order.State.RECIBIDO)
        result = OrderService.transition(order.pk, Order.State.PREPARACION)
        result.refresh_from_db()
        assert result.state == Order.State.PREPARACION

    def test_service_cancel_only_from_recibido(self):
        order = OrderFactory(state=Order.State.RECIBIDO)
        result = OrderService.cancel(order.pk)
        assert result.state == Order.State.CANCELADO

    def test_service_cancel_from_other_state_fails(self):
        order = OrderFactory(state=Order.State.PREPARACION)
        with pytest.raises(InvalidTransitionError):
            OrderService.cancel(order.pk)

    def test_service_forward_only_enforced(self):
        order = OrderFactory(state=Order.State.PREPARACION, cash_declared=True)
        OrderService.transition(order.pk, Order.State.FACTURACION)
        order.refresh_from_db()
        assert order.state == Order.State.FACTURACION
        with pytest.raises(InvalidTransitionError):
            OrderService.transition(order.pk, Order.State.PREPARACION)

    def test_service_guard_enforced_atomic(self):
        order = OrderFactory(state=Order.State.PREPARACION, cash_declared=False)
        with pytest.raises(GuardViolationError):
            OrderService.transition(order.pk, Order.State.FACTURACION)
        order.refresh_from_db()
        assert order.state == Order.State.PREPARACION

    def test_service_full_happy_path_to_entregado(self):
        order = OrderFactory(state=Order.State.RECIBIDO)
        OrderService.transition(order.pk, Order.State.PREPARACION)
        order.refresh_from_db()
        order.cash_declared = True
        order.save(update_fields=["cash_declared"])
        OrderService.transition(order.pk, Order.State.FACTURACION)
        OrderService.transition(order.pk, Order.State.LOGISTICA)
        OrderService.transition(order.pk, Order.State.ENTREGADO)
        order.refresh_from_db()
        assert order.state == Order.State.ENTREGADO
        with pytest.raises(InvalidTransitionError):
            OrderService.transition(order.pk, Order.State.CANCELADO)
