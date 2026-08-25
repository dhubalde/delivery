import pytest

from apps.catalog.models import Product
from apps.catalog.services.flavor_policy import (
    FlavorsNotAllowedError,
    FlavorSelectionRequiredError,
    PoteFlavorPolicy,
)


def make_product(product_type):
    return Product(product_type=product_type, min_flavors=3, max_flavors=4)


class TestBrCat03PoteRequiresFlavorSelection:
    def test_br_cat_03_empty_selection_rejected(self):
        pote = make_product(Product.ProductType.POTE)
        with pytest.raises(FlavorSelectionRequiredError):
            PoteFlavorPolicy.validate(pote, [])

    def test_br_cat_03_none_selection_rejected(self):
        pote = make_product(Product.ProductType.POTE)
        with pytest.raises(FlavorSelectionRequiredError):
            PoteFlavorPolicy.validate(pote, None)

    def test_br_cat_03_nonempty_selection_passes_through(self):
        pote = make_product(Product.ProductType.POTE)
        assert PoteFlavorPolicy.validate(pote, [7, 8]) == [7, 8]


class TestBrCat06UnitProductsZeroFlavors:
    def test_br_cat_06_flavors_on_unit_rejected(self):
        unit = make_product(Product.ProductType.UNIT)
        with pytest.raises(FlavorsNotAllowedError):
            PoteFlavorPolicy.validate(unit, [7])

    def test_br_cat_06_empty_selection_accepted(self):
        unit = make_product(Product.ProductType.UNIT)
        assert PoteFlavorPolicy.validate(unit, []) == []
