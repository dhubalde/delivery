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
        has_flavors = product.min_flavors is not None and product.max_flavors is not None and not (product.min_flavors == 0 and product.max_flavors == 0)
        if product.product_type == Product.ProductType.POTE:
            if has_flavors:
                if not ids:
                    raise FlavorSelectionRequiredError("Pote products require at least one flavor.")
                min_flavors = product.min_flavors
                max_flavors = product.max_flavors
                if len(ids) < min_flavors:
                    raise FlavorPolicyError(f"Pote products require at least {min_flavors} flavor(s), got {len(ids)}.")
                if len(ids) > max_flavors:
                    raise FlavorPolicyError(f"Pote products require at most {max_flavors} flavor(s), got {len(ids)}.")
                return ids
            if not ids:
                raise FlavorSelectionRequiredError("Pote products require at least one flavor.")
            if product.pote_size in (Product.PoteSize.KG_1, Product.PoteSize.KG_HALF):
                min_flavors, max_flavors = 1, 4
            elif product.pote_size == Product.PoteSize.KG_QUARTER:
                min_flavors, max_flavors = 1, 3
            else:
                min_flavors, max_flavors = 1, 4
            if len(ids) < min_flavors or len(ids) > max_flavors:
                raise FlavorPolicyError(f"Pote requires {min_flavors}-{max_flavors} flavors, got {len(ids)}.")
            return ids
        if has_flavors:
            if not ids:
                raise FlavorSelectionRequiredError("Product requires flavor selection.")
            if len(ids) < product.min_flavors or len(ids) > product.max_flavors:
                raise FlavorPolicyError(f"Requires {product.min_flavors}-{product.max_flavors} flavors, got {len(ids)}.")
            return ids
        if ids:
            raise FlavorsNotAllowedError("Unit products do not accept flavor selections.")
        return ids
