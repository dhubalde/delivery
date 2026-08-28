from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.audit.services import emit
from apps.catalog.tests.factories import MerchantFactory
from apps.closing.tests.factories import CashClosureFactory
from apps.orders.models import Order
from apps.orders.services import OrderService
from apps.orders.tests.factories import OrderFactory
from apps.payments.models import Payment
from apps.payments.services import PaymentService
from apps.tenancy.models import EmployeeRole
from apps.tenancy.tests.factories import EmployeeFactory, EmployeeRoleFactory


pytestmark = pytest.mark.django_db


class TestAuditTrailBrX03:
    def test_state_transition_logged(self):
        o = OrderFactory(state=Order.State.RECIBIDO)
        OrderService.transition(o.pk, Order.State.PREPARACION)
        ev = AuditEvent.objects.filter(entity="Order", entity_id=o.pk, action="STATE_TRANSITION").first()
        assert ev is not None
        assert ev.merchant_id == o.merchant_id
        assert ev.old_value == {"state": "RECIBIDO"}
        assert ev.new_value == {"state": "PREPARACION"}

    def test_cancellation_logged_with_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="auditor")
        o = OrderFactory(state=Order.State.RECIBIDO)
        OrderService.transition(o.pk, Order.State.CANCELADO, actor=user)
        ev = AuditEvent.objects.filter(entity="Order", entity_id=o.pk).first()
        assert ev.actor_user_id == user.pk

    def test_payment_logged(self):
        o = OrderFactory(total=Decimal("1000.00"))
        PaymentService.declare_payments(o, [{"method": Payment.Method.BILLETERA, "amount": "1000.00"}])
        assert AuditEvent.objects.filter(entity="Payment", action="PAYMENT").exists()
        ev = AuditEvent.objects.filter(action="PAYMENT").first()
        assert ev.new_value["method"] == "BILLETERA"

    def test_cash_movement_logged(self):
        o = OrderFactory()
        pay = PaymentService.declare_payments(o, [{"method": Payment.Method.EFECTIVO, "amount": str(o.total)}])[0]
        assert AuditEvent.objects.filter(action="PAYMENT").exists()
        before = AuditEvent.objects.filter(action="CASH_MOVEMENT").count()
        PaymentService.confirm_cash(pay.pk, cashier_user="cashier1")
        assert AuditEvent.objects.filter(action="CASH_MOVEMENT").count() == before + 1
        ev = AuditEvent.objects.filter(action="CASH_MOVEMENT").first()
        assert ev.old_value == {"status": "PENDING"}
        assert ev.new_value["status"] == "CONFIRMED"

    def test_closure_logged(self):
        from apps.closing.services import CashClosureService
        from django.utils import timezone

        m = MerchantFactory()
        admin = EmployeeFactory(merchant=m)
        EmployeeRoleFactory(employee=admin, role=EmployeeRole.Role.ADMIN)
        closure = CashClosureService.close(m, timezone.localdate(), admin)
        ev = AuditEvent.objects.filter(entity="CashClosure", entity_id=closure.pk, action="CLOSURE").first()
        assert ev is not None
        assert ev.merchant_id == m.pk

    def test_emit_in_same_transaction(self):
        o = OrderFactory(state=Order.State.RECIBIDO)
        OrderService.transition(o.pk, Order.State.PREPARACION)
        ev = AuditEvent.objects.get(entity="Order", entity_id=o.pk)
        o.refresh_from_db()
        assert o.state == "PREPARACION"
        assert ev is not None

    def test_audit_append_only_no_update(self):
        m = MerchantFactory()
        ev = emit(merchant_id=m.pk, entity="Test", entity_id=1, action="CREATE", old_value=None, new_value={"x": 1})
        ev.new_value = {"x": 2}
        with pytest.raises(ValueError, match="append-only"):
            ev.save()

    def test_audit_append_only_no_delete(self):
        m = MerchantFactory()
        ev = emit(merchant_id=m.pk, entity="Test", entity_id=2, action="CREATE", old_value=None, new_value={})
        with pytest.raises(ValueError, match="append-only"):
            ev.delete()

    def test_emit_stores_merchant_and_values(self):
        m = MerchantFactory()
        ev = emit(merchant_id=m, entity="Product", entity_id=99, action="UPDATE", old_value={"name": "a"}, new_value={"name": "b"})
        assert ev.merchant_id == m.pk
        assert ev.old_value == {"name": "a"}
        assert ev.new_value == {"name": "b"}
        assert ev.created_at is not None
