from decimal import Decimal

import pytest

from apps.orders.models import Order
from apps.orders.services import OrderService
from apps.orders.tests.factories import OrderFactory
from apps.payments.models import Payment
from apps.payments.services import CashConfirmationError, PaymentService, PaymentValidationError

pytestmark = pytest.mark.django_db


class TestBrPay01DeclarePayments:
    def test_br_pay_01_single_efectivo_allowed(self):
        order = OrderFactory(total=Decimal("1000.00"))
        pays = PaymentService.declare_payments(order, [{"method": "EFECTIVO", "amount": "1000.00"}])
        assert len(pays) == 1
        assert pays[0].method == Payment.Method.EFECTIVO

    def test_br_pay_01_multiple_methods_allowed(self):
        order = OrderFactory(total=Decimal("1000.00"))
        pays = PaymentService.declare_payments(
            order, [{"method": "EFECTIVO", "amount": "600.00"}, {"method": "BILLETERA", "amount": "400.00"}]
        )
        assert len(pays) == 2
        methods = {p.method for p in pays}
        assert methods == {"EFECTIVO", "BILLETERA"}

    def test_br_pay_01_three_methods_allowed(self):
        order = OrderFactory(total=Decimal("1000.00"))
        pays = PaymentService.declare_payments(
            order,
            [
                {"method": "EFECTIVO", "amount": "400.00"},
                {"method": "BILLETERA", "amount": "300.00"},
                {"method": "TARJETA", "amount": "300.00"},
            ],
        )
        assert len(pays) == 3


class TestBrPay02DigitalSync:
    def test_br_pay_02_billetera_confirmed_sync(self):
        order = OrderFactory(total=Decimal("500.00"))
        pays = PaymentService.declare_payments(order, [{"method": "BILLETERA", "amount": "500.00"}])
        assert pays[0].status == Payment.Status.CONFIRMED
        assert pays[0].gateway_ref is not None
        assert pays[0].gateway_ref.startswith("MP-MOCK-")

    def test_br_pay_02_tarjeta_confirmed_sync(self):
        order = OrderFactory(total=Decimal("700.00"))
        pays = PaymentService.declare_payments(order, [{"method": "TARJETA", "amount": "700.00"}])
        assert pays[0].status == Payment.Status.CONFIRMED
        assert pays[0].gateway_ref is not None

    def test_br_pay_02_digital_not_pending(self):
        order = OrderFactory(total=Decimal("300.00"))
        pays = PaymentService.declare_payments(order, [{"method": "BILLETERA", "amount": "300.00"}])
        assert pays[0].status != Payment.Status.PENDING


class TestBrPay03CashPending:
    def test_br_pay_03_efectivo_pending_blinking(self):
        order = OrderFactory(total=Decimal("800.00"))
        pays = PaymentService.declare_payments(order, [{"method": "EFECTIVO", "amount": "800.00"}])
        assert pays[0].status == Payment.Status.PENDING
        assert pays[0].is_blinking is True
        assert pays[0].gateway_ref is None

    def test_br_pay_03_cash_sets_cash_declared(self):
        order = OrderFactory(total=Decimal("800.00"), cash_declared=False)
        PaymentService.declare_payments(order, [{"method": "EFECTIVO", "amount": "800.00"}])
        order.refresh_from_db()
        assert order.cash_declared is True


class TestBrPay05SumValidation:
    def test_br_pay_05_sum_must_equal_total(self):
        order = OrderFactory(total=Decimal("1000.00"))
        with pytest.raises(PaymentValidationError, match="BR-PAY-05"):
            PaymentService.declare_payments(order, [{"method": "EFECTIVO", "amount": "900.00"}])

    def test_br_pay_05_sum_exceeds_total_rejected(self):
        order = OrderFactory(total=Decimal("1000.00"))
        with pytest.raises(PaymentValidationError):
            PaymentService.declare_payments(
                order, [{"method": "EFECTIVO", "amount": "600.00"}, {"method": "BILLETERA", "amount": "500.00"}]
            )

    def test_br_pay_05_mixed_sum_exact(self):
        order = OrderFactory(total=Decimal("1000.00"))
        pays = PaymentService.declare_payments(
            order, [{"method": "EFECTIVO", "amount": "400.00"}, {"method": "TARJETA", "amount": "600.00"}]
        )
        assert sum(p.amount for p in pays) == Decimal("1000.00")


class TestBrPayEdgeDigitalRejected:
    def test_br_pay_07_rejected_payment_blocked_at_logistics(self):
        order = OrderFactory(total=Decimal("500.00"), state=Order.State.FACTURACION, fulfillment=Order.Fulfillment.DELIVERY)
        Payment.objects.create(order=order, method=Payment.Method.TARJETA, amount=Decimal("500.00"), status=Payment.Status.REJECTED)
        with pytest.raises(PaymentValidationError, match="REJECTED"):
            PaymentService.validate_for_logistics(order)

    def test_br_pay_05_pending_not_counted_as_efectivo(self):
        order = OrderFactory(total=Decimal("1000.00"))
        PaymentService.declare_payments(order, [{"method": "EFECTIVO", "amount": "1000.00"}])
        assert PaymentService.efectivo_confirmed_total(order) == Decimal("0")
        assert order.payments.filter(status=Payment.Status.CONFIRMED).count() == 0
