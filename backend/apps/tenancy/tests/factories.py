import factory

from apps.catalog.tests.factories import MerchantFactory
from apps.tenancy.models import Employee, EmployeeRole


class EmployeeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Employee

    merchant = factory.SubFactory(MerchantFactory)
    display_name = factory.Sequence(lambda n: f"Empleado {n}")
    is_active = True


class EmployeeRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmployeeRole

    employee = factory.SubFactory(EmployeeFactory)
    role = EmployeeRole.Role.CAJERO
