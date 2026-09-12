import pytest
from django.db import IntegrityError

from apps.catalog.tests.factories import MerchantFactory
from apps.customers.models import Customer
from apps.customers.tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


class TestCustomerModel:
    def test_create_customer_with_merchant_fk(self):
        m = MerchantFactory(slug="acme")
        c = CustomerFactory(merchant=m, phone="555-1000", name="Alice")
        assert c.pk is not None
        assert c.merchant_id == m.pk
        assert c.phone == "555-1000"

    def test_unique_phone_per_merchant_constraint(self):
        m = MerchantFactory(slug="acme")
        CustomerFactory(merchant=m, phone="555-1000")
        with pytest.raises(IntegrityError):
            CustomerFactory(merchant=m, phone="555-1000")

    def test_same_phone_across_merchants_allowed(self):
        m1 = MerchantFactory(slug="acme")
        m2 = MerchantFactory(slug="beta")
        c1 = CustomerFactory(merchant=m1, phone="555-1000")
        c2 = CustomerFactory(merchant=m2, phone="555-1000")
        assert c1.pk != c2.pk
        assert Customer.objects.filter(phone="555-1000").count() == 2

    def test_phone_filter_scoped_by_merchant(self):
        m1 = MerchantFactory(slug="acme")
        m2 = MerchantFactory(slug="beta")
        CustomerFactory(merchant=m1, phone="555-1000")
        CustomerFactory(merchant=m2, phone="555-2000")
        assert Customer.objects.filter(merchant=m1, phone="555-1000").exists()
        assert not Customer.objects.filter(merchant=m2, phone="555-1000").exists()

    def test_password_hash_and_check(self):
        m = MerchantFactory(slug="acme")
        c = Customer(merchant=m, phone="555-3000", name="Bob")
        c.set_password("s3cret!")
        c.save()
        c.refresh_from_db()
        assert c.password_hash != "s3cret!"
        assert c.check_password("s3cret!") is True
        assert c.check_password("wrong") is False

    def test_soft_delete_hides_from_default_manager(self):
        c = CustomerFactory()
        cid = c.pk
        c.delete()
        assert not Customer.objects.filter(pk=cid).exists()
        assert Customer.all_objects.filter(pk=cid).exists()
        assert Customer.all_objects.get(pk=cid).deleted_at is not None
