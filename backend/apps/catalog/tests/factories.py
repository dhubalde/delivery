from decimal import Decimal

import factory

from apps.catalog.models import Category, Flavor, Product
from apps.tenancy.models import Merchant


class MerchantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Merchant

    name = "Heladeria Sur"
    slug = factory.Sequence(lambda n: f"heladeria-{n}")


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    merchant = factory.SubFactory(MerchantFactory)
    name = factory.Sequence(lambda n: f"Category {n}")


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    category = factory.SubFactory(CategoryFactory)
    merchant = factory.SelfAttribute("category.merchant")
    name = factory.Sequence(lambda n: f"Pote {n}")
    price = Decimal("8500.00")
    product_type = Product.ProductType.POTE
    pote_size = Product.PoteSize.KG_1
    min_flavors = 3
    max_flavors = 4


class UnitProductFactory(ProductFactory):
    name = factory.Sequence(lambda n: f"Bombo {n}")
    product_type = Product.ProductType.UNIT
    pote_size = None
    min_flavors = None
    max_flavors = None


class FlavorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Flavor

    merchant = factory.SubFactory(MerchantFactory)
    name = factory.Sequence(lambda n: f"Dulce de leche {n}")
