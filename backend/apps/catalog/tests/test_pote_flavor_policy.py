import pytest

from apps.catalog.models import Product
from apps.catalog.services.flavor_policy import (
    FlavorsNotAllowedError,
    FlavorSelectionRequiredError,
    PoteFlavorPolicy,
)


def make_product(product_type, pote_size=None):
    """Create a Product for policy testing with the given type and pote_size."""
    if product_type == Product.ProductType.POTE and pote_size is not None:
        if pote_size in ("KG_1", "KG_HALF"):
            min_flavors = 3
            max_flavors = 4
        else:  # KG_QUARTER
            min_flavors = 2
            max_flavors = 3
    else:
        min_flavors = 0
        max_flavors = 0
    return Product(
        product_type=product_type,
        pote_size=pote_size,
        min_flavors=min_flavors,
        max_flavors=max_flavors,
    )


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
        # KG_QUARTER allows max 2 flavors, so [7, 8] should pass
        pote = make_product(Product.ProductType.POTE, pote_size="KG_QUARTER")
        assert PoteFlavorPolicy.validate(pote, [7, 8]) == [7, 8]


class TestBrCat06UnitProductsZeroFlavors:
    def test_br_cat_06_flavors_on_unit_rejected(self):
        unit = make_product(Product.ProductType.UNIT)
        with pytest.raises(FlavorsNotAllowedError):
            PoteFlavorPolicy.validate(unit, [7])

    def test_br_cat_06_empty_selection_accepted(self):
        unit = make_product(Product.ProductType.UNIT)
        assert PoteFlavorPolicy.validate(unit, []) == []
