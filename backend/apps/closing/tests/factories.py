import datetime
from decimal import Decimal

import factory
from django.utils import timezone

from apps.closing.models import CashClosure
from apps.tenancy.tests.factories import EmployeeFactory


class CashClosureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CashClosure

    merchant = factory.SubFactory("apps.catalog.tests.factories.MerchantFactory")
    business_date = factory.LazyFunction(lambda: timezone.localdate())
    cashier = factory.SubFactory(EmployeeFactory)
    total_efectivo = Decimal("0.00")
    total_billeteras = Decimal("0.00")
    total_tarjetas = Decimal("0.00")
    total_entregados = 0
    total_rechazados = 0
    ticket_payload = factory.LazyFunction(dict)
