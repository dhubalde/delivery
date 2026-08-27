import datetime
from decimal import Decimal

import factory
from django.utils import timezone

from apps.catalog.tests.factories import MerchantFactory
from apps.orders.models import Order


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    merchant = factory.SubFactory(MerchantFactory)
    code = factory.Sequence(lambda n: n + 1)
    customer_name = "Test Customer"
    customer_phone = "1122334455"
    fulfillment = Order.Fulfillment.DELIVERY
    state = Order.State.RECIBIDO
    business_date = factory.LazyFunction(lambda: timezone.localdate())
    items_total = Decimal("1000.00")
    delivery_fee = Decimal("0.00")
    discount = Decimal("0.00")
    total = Decimal("1000.00")
    cash_declared = False
