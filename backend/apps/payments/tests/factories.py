from decimal import Decimal

import factory

from apps.orders.tests.factories import OrderFactory
from apps.payments.models import Payment


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    order = factory.SubFactory(OrderFactory)
    method = Payment.Method.EFECTIVO
    amount = Decimal("500.00")
    status = Payment.Status.PENDING
