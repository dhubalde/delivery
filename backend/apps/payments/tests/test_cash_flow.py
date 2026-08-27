from decimal import Decimal

import pytest

from apps.orders.models import Order
from apps.orders.services import OrderService
from apps.orders.tests.factories import OrderFactory
from apps.payments.models import Payment
from apps.payments.services import CashConfirmationError, PaymentService, PaymentValidationError
from apps.payments.tests.factories import PaymentFactory

pytestmark = pytest.mark.django_db


class TestBrPay04Collection:
    def test_br_pay_04_courier_collects_keeps_pending(self):
        order = OrderFactory(total=Decimal("1000.00"), fulfillment=Order.Fulfillment.DELIVERY)
        pays = PaymentService.declare_payments(order, [{"method": "EFECTIVO", "amount": "1000.00"}])
        pay = pays[0]
        PaymentService.collect_cash_by_courier(pay.pk, courier_user="courier1")
        pay.refresh_from_db()
        assert pay.status == Payment.Status.PENDING
        assert pay.collected_by == "courier1"

    def test_br_pay_04_pickup_collected_at_counter_still_pending_until_confirm(self):
        order = OrderFactory(total=Decimal("500.00"), fulfillment=Order.Fulfillment.PICKUP)
        pays = PaymentService.declare_payments(order, [{"method": "EFECTIVO", "amount": "500.00"}])
        assert pays[0].status == Payment.Status.PENDING
        assert pays[0].is_blinking is True


class TestBrPay05CashierConfirm:
    def test_br_pay_05_confirm_stops_blinking_and_sums(self):
        order = OrderFactory(total=Decimal("1000.00"))
        pays = PaymentService.declare_payments(order, [{"method": "EFECTIVO", "amount": "1000.00"}])
        pay = pays[0]
        assert pay.is_blinking is True
        confirmed = PaymentService.confirm_cash(pay.pk, cashier_user="cashier1")
        assert confirmed.status == Payment.Status.CONFIRMED
        assert confirmed.is_blinking is False
        assert confirmed.confirmed_at is not None
        assert PaymentService.efectivo_confirmed_total(order) == Decimal("1000.00")

    def test_br_pay_05_confirm_sets_collected_by(self):
        order = OrderFactory(total=Decimal("600.00"))
        pay = PaymentFactory(order=order, amount=Decimal("600.00"), status=Payment.Status.PENDING)
        PaymentService.confirm_cash(pay.pk, cashier_user="cashier2")
        pay.refresh_from_db()
        assert pay.collected_by == "cashier2"
        assert pay.confirmed_at is not None

    def test_br_pay_05_double_confirm_rejected(self):
        order = OrderFactory(total=Decimal("400.00"))
        pay = PaymentFactory(order=order, amount=Decimal("400.00"), status=Payment.Status.PENDING)
        PaymentService.confirm_cash(pay.pk)
        with pytest.raises(CashConfirmationError):
            PaymentService.confirm_cash(pay.pk)

    def test_br_pay_05_confirm_non_efectivo_rejected(self):
        order = OrderFactory(total=Decimal("400.00"))
        pay = PaymentFactory(order=order, method=Payment.Method.BILLETERA, amount=Decimal("400.00"), status=Payment.Status.CONFIRMED)
        with pytest.raises(CashConfirmationError):
            PaymentService.confirm_cash(pay.pk)


class TestBrPay06CashTimingGuard:
    def test_br_pay_06_pickup_requires_confirmed_before_logistica(self):
        order = OrderFactory(total=Decimal("1000.00"), state=Order.State.FACTURACION, fulfillment=Order.Fulfillment.PICKUP)
        PaymentFactory(order=order, method=Payment.Method.EFECTIVO, amount=Decimal("1000.00"), status=Payment.Status.PENDING)
        with pytest.raises(PaymentValidationError, match="PICKUP cash must be CONFIRMED"):
            OrderService.transition(order.pk, Order.State.LOGISTICA)

    def test_br_pay_06_pickup_confirmed_allows_logistica(self):
        order = OrderFactory(total=Decimal("1000.00"), state=Order.State.FACTURACION, fulfillment=Order.Fulfillment.PICKUP)
        PaymentFactory(order=order, method=Payment.Method.EFECTIVO, amount=Decimal("1000.00"), status=Payment.Status.CONFIRMED)
        result = OrderService.transition(order.pk, Order.State.LOGISTICA)
        assert result.state == Order.State.LOGISTICA

    def test_br_pay_06_delivery_pending_allows_logistica(self):
        order = OrderFactory(total=Decimal("1000.00"), state=Order.State.FACTURACION, fulfillment=Order.Fulfillment.DELIVERY)
        PaymentFactory(order=order, method=Payment.Method.EFECTIVO, amount=Decimal("1000.00"), status=Payment.Status.PENDING)
        result = OrderService.transition(order.pk, Order.State.LOGISTICA)
        assert result.state == Order.State.LOGISTICA

    def test_br_pay_06_no_payment_blocks_logistica(self):
        order = OrderFactory(total=Decimal("500.00"), state=Order.State.FACTURACION, fulfillment=Order.Fulfillment.DELIVERY)
        with pytest.raises(PaymentValidationError, match="at least one payment"):
            OrderService.transition(order.pk, Order.State.LOGISTICA)

    def test_br_pay_06_digital_must_be_confirmed(self):
        order = OrderFactory(total=Decimal("500.00"), state=Order.State.FACTURACION, fulfillment=Order.Fulfillment.DELIVERY)
        Payment.objects.create(order=order, method=Payment.Method.BILLETERA, amount=Decimal("500.00"), status=Payment.Status.PENDING)
        with pytest.raises(PaymentValidationError, match="Digital payment"):
            OrderService.transition(order.pk, Order.State.LOGISTICA)

    def test_br_pay_06_delivery_plus_digital_confirmed_ok(self):
        order = OrderFactory(total=Decimal("1000.00"), state=Order.State.FACTURACION, fulfillment=Order.Fulfillment.DELIVERY)
        PaymentFactory(order=order, method=Payment.Method.EFECTIVO, amount=Decimal("600.00"), status=Payment.Status.PENDING)
        Payment.objects.create(order=order, method=Payment.Method.TARJETA, amount=Decimal("400.00"), status=Payment.Status.CONFIRMED, gateway_ref="MP-MOCK-XYZ")
        result = OrderService.transition(order.pk, Order.State.LOGISTICA)
        assert result.state == Order.State.LOGISTICA
