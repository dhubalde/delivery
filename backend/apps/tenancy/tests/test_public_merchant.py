"""Public merchant lookup must answer for the requested slug only.

Every storefront URL is brand-first (`/<slug>`), so a typo or a removed slug
must fail loudly instead of silently serving another company's data.
"""

import pytest
from rest_framework.test import APIClient

from apps.catalog.tests.factories import MerchantFactory

pytestmark = pytest.mark.django_db


class TestPublicMerchantLookup:
    def test_unknown_slug_is_not_found(self):
        MerchantFactory(slug="ice-zone")
        response = APIClient().get("/api/v1/merchant/public/", {"slug": "heladeria-inexistente"})
        assert response.status_code == 404

    def test_missing_slug_is_not_found(self):
        MerchantFactory(slug="ice-zone")
        response = APIClient().get("/api/v1/merchant/public/")
        assert response.status_code == 404

    def test_returns_the_requested_merchant_not_the_first_one(self):
        MerchantFactory(slug="ice-zone", name="Ice Zone")
        MerchantFactory(slug="deco-a-deco", name="Deco a Deco")
        response = APIClient().get("/api/v1/merchant/public/", {"slug": "deco-a-deco"})
        assert response.status_code == 200
        assert response.json()["slug"] == "deco-a-deco"
        assert response.json()["name"] == "Deco a Deco"
