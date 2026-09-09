import factory
from django.contrib.auth.models import User
from django.utils import timezone

from apps.catalog.tests.factories import MerchantFactory
from apps.tenancy.models import Branch, Employee, EmployeeRole, PlatformUser


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall("set_password", "Pass123!")


class BranchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Branch

    merchant = factory.SubFactory(MerchantFactory)
    name = factory.Sequence(lambda n: f"Sucursal {n}")
    is_active = True


class PlatformUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlatformUser

    user = factory.SubFactory(UserFactory)
    merchant = factory.SubFactory(MerchantFactory)
    role = "CAJERO"
    kind = PlatformUser.Kind.PERSONAL
    must_change_password = False
    password_changed_at = factory.LazyFunction(timezone.now)


class EmployeeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Employee

    merchant = factory.SubFactory(MerchantFactory)
    display_name = factory.Sequence(lambda n: f"Empleado {n}")
    fullname = factory.Sequence(lambda n: f"Empleado {n}")
    cuil = factory.Sequence(lambda n: f"209999999{n:02d}")
    is_active = True


class EmployeeRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmployeeRole

    employee = factory.SubFactory(EmployeeFactory)
    role = EmployeeRole.Role.CAJERO
