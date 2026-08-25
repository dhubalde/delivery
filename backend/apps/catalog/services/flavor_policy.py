from apps.catalog.models import Product


class FlavorPolicyError(Exception):
    """Base error for flavor selection rule violations."""


class FlavorSelectionRequiredError(FlavorPolicyError):
    """BR-CAT-03: a pote product was selected without any flavors."""


class FlavorsNotAllowedError(FlavorPolicyError):
    """BR-CAT-06: flavors were sent for a unit product."""


class PoteFlavorPolicy:
    """Validates cart-add flavor selections by product type.

    Covers BR-CAT-03 and BR-CAT-06. Flavor-count bounds for potes
    (BR-CAT-04/05) plug into ``validate`` in Fase 2.
    """

    @staticmethod
    def validate(product, flavor_ids):
        ids = list(flavor_ids or [])
        if product.product_type == Product.ProductType.POTE:
            if not ids:
                raise FlavorSelectionRequiredError(
                    "Pote products require at least one flavor."
                )
            return ids
        if ids:
            raise FlavorsNotAllowedError(
                "Unit products do not accept flavor selections."
            )
        return ids
