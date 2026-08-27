import pytest
from django.db import IntegrityError

from apps.orders.models import Order
from apps.orders.state_machine import OrderStateMachine
from apps.tenancy.models import Employee, EmployeeRole
from apps.tenancy.services.roles import (
    can_transition,
    effective_permissions,
    has_any_role,
    has_role,
)
from apps.tenancy.tests.factories import EmployeeFactory, EmployeeRoleFactory

pytestmark = pytest.mark.django_db


class TestBrRol01FiveBaseRoles:
    def test_create_all_five_roles(self):
        emp = EmployeeFactory()
        for role in [c[0] for c in EmployeeRole.Role.choices]:
            EmployeeRole.objects.create(employee=emp, role=role)
        assert emp.employee_roles.count() == 5

    def test_role_choices_exactly_five(self):
        choices = {c[0] for c in EmployeeRole.Role.choices}
        assert choices == {"ADMIN", "CAJERO", "PREPARADOR", "REPARTIDOR", "TOMA_PEDIDOS"}

    def test_unique_employee_role_constraint(self):
        emp = EmployeeFactory()
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.ADMIN)
        with pytest.raises(IntegrityError):
            EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.ADMIN)

    def test_invalid_role_rejected_by_choices(self):
        emp = EmployeeFactory()
        with pytest.raises(Exception):
            er = EmployeeRole(employee=emp, role="INVALID")
            er.full_clean()

    def test_soft_delete_employee_hides_from_default_manager(self):
        emp = EmployeeFactory()
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.CAJERO)
        emp.delete()
        assert Employee.objects.filter(pk=emp.pk).count() == 0
        assert Employee.all_objects.filter(pk=emp.pk).count() == 1

    def test_collected_by_employee_fk_nullable_transition(self):
        from apps.orders.tests.factories import OrderFactory
        from apps.payments.models import Payment

        emp = EmployeeFactory()
        order = OrderFactory()
        pay = Payment.objects.create(
            order=order,
            method=Payment.Method.EFECTIVO,
            amount=order.total,
            status=Payment.Status.PENDING,
            collected_by="legacy string",
            collected_by_employee=emp,
        )
        assert pay.collected_by_employee_id == emp.pk
        assert pay.collected_by == "legacy string"

    def test_collected_by_employee_fk_is_nullable_set_null(self):
        from apps.payments.models import Payment

        field = Payment._meta.get_field("collected_by_employee")
        assert field.null is True
        assert field.remote_field.on_delete.__name__ == "SET_NULL"

    def test_soft_delete_employee_keeps_payment_fk_intact(self):
        from apps.orders.tests.factories import OrderFactory
        from apps.payments.models import Payment

        emp = EmployeeFactory()
        order = OrderFactory()
        pay = Payment.objects.create(
            order=order,
            method=Payment.Method.EFECTIVO,
            amount=order.total,
            status=Payment.Status.PENDING,
            collected_by_employee=emp,
        )
        emp.delete()
        pay.refresh_from_db()
        assert pay.collected_by_employee_id == emp.pk
        assert Employee.objects.filter(pk=emp.pk).count() == 0
        assert Employee.all_objects.filter(pk=emp.pk).count() == 1


class TestBrRol02MultiRoleUnion:
    def test_employee_has_multiple_roles(self):
        emp = EmployeeFactory()
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.CAJERO)
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.PREPARADOR)
        assert has_role(emp, EmployeeRole.Role.CAJERO) is True
        assert has_role(emp, EmployeeRole.Role.PREPARADOR) is True
        assert has_role(emp, EmployeeRole.Role.ADMIN) is False

    def test_has_any_role_union(self):
        emp = EmployeeFactory()
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.REPARTIDOR)
        assert has_any_role(emp, [EmployeeRole.Role.REPARTIDOR, EmployeeRole.Role.ADMIN]) is True
        assert has_any_role(emp, [EmployeeRole.Role.ADMIN, EmployeeRole.Role.CAJERO]) is False

    def test_effective_permissions_is_union(self):
        emp = EmployeeFactory()
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.CAJERO)
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.PREPARADOR)
        perms = effective_permissions(emp)
        assert "confirm_cash" in perms
        assert "mark_terminado" in perms
        assert "view_route" not in perms

    def test_effective_permissions_includes_role_names(self):
        emp = EmployeeFactory()
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.ADMIN)
        perms = effective_permissions(emp)
        assert "ADMIN" in perms

    def test_inactive_employee_has_no_permissions(self):
        emp = EmployeeFactory(is_active=False)
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.ADMIN)
        assert has_role(emp, EmployeeRole.Role.ADMIN) is False
        assert effective_permissions(emp) == set()

    def test_no_roles_gives_empty_permissions(self):
        emp = EmployeeFactory()
        assert effective_permissions(emp) == set()
        assert has_any_role(emp, [EmployeeRole.Role.ADMIN]) is False


class TestBrRol04OffPeakAllRoles:
    def test_employee_with_all_five_roles_passes_all_checks(self):
        emp = EmployeeFactory()
        for role in [c[0] for c in EmployeeRole.Role.choices]:
            EmployeeRole.objects.create(employee=emp, role=role)
        for role in [c[0] for c in EmployeeRole.Role.choices]:
            assert has_role(emp, role) is True
        perms = effective_permissions(emp)
        for role in [c[0] for c in EmployeeRole.Role.choices]:
            assert role in perms
        assert "confirm_cash" in perms
        assert "mark_terminado" in perms
        assert "view_route" in perms
        assert "create_order" in perms
        assert "manage_merchant" in perms

    def test_off_peak_employee_can_access_all_transitions(self):
        emp = EmployeeFactory()
        for role in [c[0] for c in EmployeeRole.Role.choices]:
            EmployeeRole.objects.create(employee=emp, role=role)
        assert can_transition(emp, "RECIBIDO", "PREPARACION") is True
        assert can_transition(emp, "PREPARACION", "FACTURACION") is True
        assert can_transition(emp, "FACTURACION", "LOGISTICA") is True
        assert can_transition(emp, "LOGISTICA", "ENTREGADO") is True
        assert can_transition(emp, "RECIBIDO", "CANCELADO") is True

    def test_off_peak_employee_passes_state_machine_guards(self):
        from apps.orders.tests.factories import OrderFactory

        emp = EmployeeFactory()
        for role in [c[0] for c in EmployeeRole.Role.choices]:
            EmployeeRole.objects.create(employee=emp, role=role)
        order = OrderFactory(state=Order.State.RECIBIDO)
        OrderStateMachine.validate(order, Order.State.PREPARACION)
        assert can_transition(emp, order.state, Order.State.PREPARACION) is True
        order.state = Order.State.PREPARACION
        order.cash_declared = True
        order.save(update_fields=["state", "cash_declared"])
        OrderStateMachine.validate(order, Order.State.FACTURACION)
        assert can_transition(emp, order.state, Order.State.FACTURACION) is True
        order.state = Order.State.FACTURACION
        order.save(update_fields=["state"])
        from apps.payments.models import Payment

        Payment.objects.create(
            order=order, method=Payment.Method.BILLETERA, amount=order.total, status=Payment.Status.CONFIRMED
        )
        OrderStateMachine.validate(order, Order.State.LOGISTICA)
        assert can_transition(emp, order.state, Order.State.LOGISTICA) is True
        order.state = Order.State.LOGISTICA
        order.save(update_fields=["state"])
        OrderStateMachine.validate(order, Order.State.ENTREGADO)
        assert can_transition(emp, order.state, Order.State.ENTREGADO) is True

    def test_single_role_employee_cannot_access_unrelated_transition(self):
        emp = EmployeeFactory()
        EmployeeRoleFactory(employee=emp, role=EmployeeRole.Role.PREPARADOR)
        assert can_transition(emp, "LOGISTICA", "ENTREGADO") is False
        assert can_transition(emp, "FACTURACION", "LOGISTICA") is False
        assert can_transition(emp, "PREPARACION", "FACTURACION") is True

    def test_deleted_employee_loses_all_access(self):
        emp = EmployeeFactory()
        for role in [c[0] for c in EmployeeRole.Role.choices]:
            EmployeeRole.objects.create(employee=emp, role=role)
        emp.delete()
        assert has_role(emp, EmployeeRole.Role.ADMIN) is False
        assert can_transition(emp, "RECIBIDO", "PREPARACION") is False
