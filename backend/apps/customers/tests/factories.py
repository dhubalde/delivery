import factory
from django.contrib.auth.hashers import make_password

from apps.catalog.tests.factories import MerchantFactory
from apps.customers.models import Customer


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    merchant = factory.SubFactory(MerchantFactory)
    phone = factory.Sequence(lambda n: f"555-{1000+n}")
    name = factory.Sequence(lambda n: f"Customer {n}")
    password_hash = factory.LazyFunction(lambda: make_password("secret123"))
