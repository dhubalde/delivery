import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.catalog.tests.factories import MerchantFactory
from apps.closing.models import CashClosure
from apps.closing.services import AlreadyClosedError, CashClosureService, NotAdminError
from apps.orders.models import Order
from apps.orders.tests.factories import OrderFactory
from apps.payments.models import Payment
from apps.payments.tests.factories import PaymentFactory
from apps.tenancy.models import EmployeeRole
from apps.tenancy.tests.factories import EmployeeFactory, EmployeeRoleFactory

pytestmark = pytest.mark.django_db


def _admin_for(merchant):
    emp = EmployeeFactory(merchant=merchant)
    EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.ADMIN)
    return emp


def _today():
    return timezone.localdate()


class TestBrCie01AdminOnlyAndImmutable:
    def test_close_requires_admin(self):
        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        closure = CashClosureService.close(merchant, _today(), admin)
        assert closure.pk is not None
        assert closure.total_efectivo == Decimal("0.00")

    def test_non_admin_cajero_rejected(self):
        merchant = MerchantFactory()
        emp = EmployeeFactory(merchant=merchant)
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.CAJERO)
        with pytest.raises(NotAdminError):
            CashClosureService.close(merchant, _today(), emp)

    def test_employee_without_role_rejected(self):
        merchant = MerchantFactory()
        emp = EmployeeFactory(merchant=merchant)
        with pytest.raises(NotAdminError):
            CashClosureService.close(merchant, _today(), emp)

    def test_inactive_admin_rejected(self):
        merchant = MerchantFactory()
        emp = EmployeeFactory(merchant=merchant, is_active=False)
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.ADMIN)
        with pytest.raises(NotAdminError):
            CashClosureService.close(merchant, _today(), emp)

    def test_cashier_different_merchant_rejected(self):
        m1 = MerchantFactory()
        m2 = MerchantFactory()
        admin_m2 = _admin_for(m2)
        with pytest.raises(NotAdminError):
            CashClosureService.close(m1, _today(), admin_m2)

    def test_duplicate_date_rejected(self):
        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        CashClosureService.close(merchant, _today(), admin)
        with pytest.raises(AlreadyClosedError):
            CashClosureService.close(merchant, _today(), admin)

    def test_unique_constraint_enforced_at_db(self):
        from django.db import IntegrityError

        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        CashClosure.objects.create(
            merchant=merchant, business_date=_today(), cashier=admin, ticket_payload={}
        )
        with pytest.raises(IntegrityError):
            CashClosure.objects.create(
                merchant=merchant, business_date=_today(), cashier=admin, ticket_payload={}
            )

    def test_closure_is_immutable_via_save(self):
        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        closure = CashClosureService.close(merchant, _today(), admin)
        closure.total_efectivo = Decimal("999.00")
        with pytest.raises(ValidationError):
            closure.save()

    def test_closure_cannot_be_deleted(self):
        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        closure = CashClosureService.close(merchant, _today(), admin)
        with pytest.raises(ValidationError):
            closure.delete()

    def test_ticket_payload_generated(self):
        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        closure = CashClosureService.close(merchant, _today(), admin)
        assert closure.ticket_payload["merchant_id"] == merchant.pk
        assert closure.ticket_payload["cashier_id"] == admin.pk
        assert closure.ticket_payload["business_date"] == _today().isoformat()
        assert "totals" in closure.ticket_payload


class TestBrCie02FiveTotals:
    def test_ticket_includes_five_totals(self):
        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        day = _today()
        o1 = OrderFactory(merchant=merchant, business_date=day, state=Order.State.ENTREGADO)
        o2 = OrderFactory(merchant=merchant, business_date=day, state=Order.State.CANCELADO)
        o3 = OrderFactory(merchant=merchant, business_date=day, state=Order.State.ENTREGADO)
        PaymentFactory(order=o1, method=Payment.Method.EFECTIVO, amount=Decimal("100.00"), status=Payment.Status.CONFIRMED)
        PaymentFactory(order=o1, method=Payment.Method.BILLETERA, amount=Decimal("200.00"), status=Payment.Status.CONFIRMED)
        PaymentFactory(order=o3, method=Payment.Method.TARJETA, amount=Decimal("300.00"), status=Payment.Status.CONFIRMED)
        closure = CashClosureService.close(merchant, day, admin)
        assert closure.total_efectivo == Decimal("100.00")
        assert closure.total_billeteras == Decimal("200.00")
        assert closure.total_tarjetas == Decimal("300.00")
        assert closure.total_entregados == 2
        assert closure.total_rechazados == 1
        totals = closure.ticket_payload["totals"]
        assert totals["EFECTIVO"] == "100.00"
        assert totals["BILLETERAS_VIRTUALES"] == "200.00"
        assert totals["TARJETAS"] == "300.00"
        assert totals["TOTAL_ENTREGADOS"] == 2
        assert totals["TOTAL_RECHAZADOS"] == 1

    def test_totals_exclude_other_merchant_and_other_day(self):
        m1 = MerchantFactory()
        m2 = MerchantFactory()
        admin = _admin_for(m1)
        day = _today()
        yesterday = day - datetime.timedelta(days=1)
        o_today = OrderFactory(merchant=m1, business_date=day, state=Order.State.ENTREGADO)
        o_yesterday = OrderFactory(merchant=m1, business_date=yesterday, state=Order.State.ENTREGADO)
        o_other_merchant = OrderFactory(merchant=m2, business_date=day, state=Order.State.ENTREGADO)
        PaymentFactory(order=o_today, method=Payment.Method.EFECTIVO, amount=Decimal("500.00"), status=Payment.Status.CONFIRMED)
        PaymentFactory(order=o_yesterday, method=Payment.Method.EFECTIVO, amount=Decimal("999.00"), status=Payment.Status.CONFIRMED)
        PaymentFactory(order=o_other_merchant, method=Payment.Method.EFECTIVO, amount=Decimal("999.00"), status=Payment.Status.CONFIRMED)
        closure = CashClosureService.close(m1, day, admin)
        assert closure.total_efectivo == Decimal("500.00")
        assert closure.total_entregados == 1


class TestBrCie03EfectivoConfirmedOnly:
    def test_efectivo_excludes_pending_and_rejected(self):
        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        day = _today()
        o = OrderFactory(merchant=merchant, business_date=day, state=Order.State.ENTREGADO)
        PaymentFactory(order=o, method=Payment.Method.EFECTIVO, amount=Decimal("100.00"), status=Payment.Status.CONFIRMED)
        PaymentFactory(order=o, method=Payment.Method.EFECTIVO, amount=Decimal("200.00"), status=Payment.Status.PENDING)
        PaymentFactory(order=o, method=Payment.Method.EFECTIVO, amount=Decimal("300.00"), status=Payment.Status.REJECTED)
        closure = CashClosureService.close(merchant, day, admin)
        assert closure.total_efectivo == Decimal("100.00")

    def test_billeteras_tarjetas_exclude_non_confirmed(self):
        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        day = _today()
        o = OrderFactory(merchant=merchant, business_date=day, state=Order.State.ENTREGADO)
        PaymentFactory(order=o, method=Payment.Method.BILLETERA, amount=Decimal("150.00"), status=Payment.Status.CONFIRMED)
        Payment.objects.create(order=o, method=Payment.Method.BILLETERA, amount=Decimal("999.00"), status=Payment.Status.PENDING)
        PaymentFactory(order=o, method=Payment.Method.TARJETA, amount=Decimal("250.00"), status=Payment.Status.CONFIRMED)
        Payment.objects.create(order=o, method=Payment.Method.TARJETA, amount=Decimal("999.00"), status=Payment.Status.PENDING)
        closure = CashClosureService.close(merchant, day, admin)
        assert closure.total_billeteras == Decimal("150.00")
        assert closure.total_tarjetas == Decimal("250.00")

    def test_efectivo_sum_multiple_confirmed(self):
        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        day = _today()
        o1 = OrderFactory(merchant=merchant, business_date=day, state=Order.State.ENTREGADO)
        o2 = OrderFactory(merchant=merchant, business_date=day, state=Order.State.ENTREGADO)
        PaymentFactory(order=o1, method=Payment.Method.EFECTIVO, amount=Decimal("400.00"), status=Payment.Status.CONFIRMED)
        PaymentFactory(order=o2, method=Payment.Method.EFECTIVO, amount=Decimal("600.00"), status=Payment.Status.CONFIRMED)
        closure = CashClosureService.close(merchant, day, admin)
        assert closure.total_efectivo == Decimal("1000.00")


class TestBrCie07TotalRechazadosOnlyCancelledToday:
    def test_rechazados_counts_only_cancelado_today(self):
        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        day = _today()
        yesterday = day - datetime.timedelta(days=1)
        OrderFactory(merchant=merchant, business_date=day, state=Order.State.CANCELADO)
        OrderFactory(merchant=merchant, business_date=day, state=Order.State.CANCELADO)
        OrderFactory(merchant=merchant, business_date=yesterday, state=Order.State.CANCELADO)
        OrderFactory(merchant=merchant, business_date=day, state=Order.State.ENTREGADO)
        OrderFactory(merchant=merchant, business_date=day, state=Order.State.RECIBIDO)
        closure = CashClosureService.close(merchant, day, admin)
        assert closure.total_rechazados == 2

    def test_rechazados_excludes_other_merchant(self):
        m1 = MerchantFactory()
        m2 = MerchantFactory()
        admin = _admin_for(m1)
        day = _today()
        OrderFactory(merchant=m1, business_date=day, state=Order.State.CANCELADO)
        OrderFactory(merchant=m2, business_date=day, state=Order.State.CANCELADO)
        closure = CashClosureService.close(m1, day, admin)
        assert closure.total_rechazados == 1

    def test_rechazados_zero_when_none_cancelled(self):
        merchant = MerchantFactory()
        admin = _admin_for(merchant)
        day = _today()
        OrderFactory(merchant=merchant, business_date=day, state=Order.State.ENTREGADO)
        closure = CashClosureService.close(merchant, day, admin)
        assert closure.total_rechazados == 0
