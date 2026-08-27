from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.catalog.models import Category, Product, ProductFlavor
from apps.catalog.tests.factories import (
    CategoryFactory,
    FlavorFactory,
    MerchantFactory,
    ProductFactory,
)

pytestmark = pytest.mark.django_db


def make_unsaved_product(**overrides):
    data = dict(
        merchant=MerchantFactory(),
        name="Chocolate 1kg",
        price=Decimal("8500.00"),
        product_type=Product.ProductType.POTE,
        pote_size="KG_1",
        min_flavors=3,
        max_flavors=4,
    )
    data.update(overrides)
    return Product(**data)


def make_pote_product(product_type, pote_size="KG_1"):
    """Create a POTE product with the given pote_size for policy testing."""
    if pote_size in ("KG_1", "KG_HALF"):
        min_flavors = 3
        max_flavors = 4
    else:  # KG_QUARTER
        min_flavors = 2
        max_flavors = 3
    return Product(
        product_type=product_type,
        pote_size=pote_size,
        min_flavors=min_flavors,
        max_flavors=max_flavors,
    )


class TestBrCat01ExactlyOneCategory:
    def test_br_cat_01_clean_rejects_missing_category(self):
        product = make_unsaved_product(category=None)
        with pytest.raises(ValidationError) as excinfo:
            product.clean()
        assert "category" in excinfo.value.message_dict

    def test_br_cat_01_db_rejects_null_category(self):
        merchant = MerchantFactory()
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Product.objects.create(
                    merchant=merchant,
                    name="Bombon chocolate",
                    price=Decimal("4500.00"),
                    product_type=Product.ProductType.UNIT,
                )

    def test_br_cat_01_product_with_category_persists(self):
        product = ProductFactory()
        assert product.category_id is not None
        assert Product.objects.filter(pk=product.pk).exists()


class TestProductTypeConsistency:
    def test_clean_requires_size_and_bounds_for_pote(self):
        product = make_unsaved_product(
            category=CategoryFactory(), pote_size=None
        )
        with pytest.raises(ValidationError) as excinfo:
            product.clean()
        assert "pote_size" in excinfo.value.message_dict

    def test_clean_rejects_pote_fields_on_unit(self):
        product = make_unsaved_product(
            category=CategoryFactory(),
            product_type=Product.ProductType.UNIT,
            pote_size=None,
            min_flavors=None,
            max_flavors=None,
            name="Torta helada",
        )
        product.pote_size = Product.PoteSize.KG_HALF
        with pytest.raises(ValidationError) as excinfo:
            product.clean()
        assert "product_type" in excinfo.value.message_dict


class TestProductFlavor:
    def test_pair_is_unique(self):
        product = ProductFactory()
        flavor = FlavorFactory(merchant=product.merchant)
        ProductFlavor.objects.create(product=product, flavor=flavor)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProductFlavor.objects.create(product=product, flavor=flavor)

    def test_rejects_cross_merchant_pair(self):
        product = ProductFactory()
        foreign_flavor = FlavorFactory()
        row = ProductFlavor(product=product, flavor=foreign_flavor)
        with pytest.raises(ValidationError):
            row.clean()

    def test_denormalizes_merchant_from_product(self):
        product = ProductFactory()
        flavor = FlavorFactory(merchant=product.merchant)
        row = ProductFlavor.objects.create(product=product, flavor=flavor)
        assert row.merchant_id == product.merchant_id


class TestSoftDelete:
    def test_deleted_product_hidden_from_default_manager(self):
        product = ProductFactory()
        product.delete()
        assert not Product.objects.filter(pk=product.pk).exists()
        assert Product.all_objects.filter(pk=product.pk).exists()

    def test_queryset_delete_soft_deletes(self):
        product = ProductFactory()
        Product.objects.filter(pk=product.pk).delete()
        assert not Product.objects.filter(pk=product.pk).exists()
        assert Product.all_objects.get(pk=product.pk).deleted_at is not None


class TestCategoryScoping:
    def test_category_name_unique_per_merchant_only(self):
        merchant = MerchantFactory()
        other = MerchantFactory()
        CategoryFactory(merchant=merchant, name="Cucuruchos")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                CategoryFactory(merchant=merchant, name="Cucuruchos")
        CategoryFactory(merchant=other, name="Cucuruchos")
