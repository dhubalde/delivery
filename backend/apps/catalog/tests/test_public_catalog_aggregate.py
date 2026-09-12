import pytest
from rest_framework.test import APIClient

from apps.catalog.tests.factories import CategoryFactory, FlavorFactory, MerchantFactory, ProductFactory

pytestmark = pytest.mark.django_db


def _make_catalog(merchant):
    cat = CategoryFactory(merchant=merchant, name="Helados", position=1, is_active=True)
    cat2 = CategoryFactory(merchant=merchant, name="Postres", position=2, is_active=True)
    p1 = ProductFactory(merchant=merchant, category=cat, name="Pote 1kg", price="100.00", product_type="UNIT", pote_size=None, min_flavors=None, max_flavors=None, is_active=True)
    p2 = ProductFactory(merchant=merchant, category=cat2, name="Bombo", price="50.00", product_type="UNIT", pote_size=None, min_flavors=None, max_flavors=None, is_active=True)
    f1 = FlavorFactory(merchant=merchant, category=cat, name="Dulce")
    f2 = FlavorFactory(merchant=merchant, category=cat, name="Choco")
    return {"categories": [cat, cat2], "products": [p1, p2], "flavors": [f1, f2]}


class TestPublicCatalogAggregate:
    """PR2 2.1 + 2.4 2.6 2.7 — catalog aggregate"""

    def test_aggregate_returns_merchant_catalog_allow_any(self):
        merchant = MerchantFactory(slug="acme", is_active=True)
        data = _make_catalog(merchant)
        client = APIClient()
        resp = client.get(f"/api/public/{merchant.slug}/catalog")
        assert resp.status_code == 200, resp.content
        body = resp.json()
        assert body["merchant"]["slug"] == "acme"
        assert len(body["categories"]) == 2
        assert len(body["products"]) == 2
        assert len(body["flavors"]) == 2
        assert "stats" in body
        # Ensure data belongs to acme
        names = {c["name"] for c in body["categories"]}
        assert "Helados" in names

    def test_aggregate_with_slash_also_200(self):
        merchant = MerchantFactory(slug="acme2", is_active=True)
        _make_catalog(merchant)
        client = APIClient()
        resp = client.get(f"/api/public/{merchant.slug}/catalog/")
        assert resp.status_code == 200

    def test_aggregate_no_auth_required_allow_any(self):
        merchant = MerchantFactory(slug="acme3")
        _make_catalog(merchant)
        client = APIClient()
        # No Authorization header at all
        resp = client.get(f"/api/public/{merchant.slug}/catalog")
        assert resp.status_code == 200
        # Even with Bearer garbage? Should still allow? AllowAny ignores auth
        resp2 = client.get(f"/api/public/{merchant.slug}/catalog", HTTP_AUTHORIZATION="Bearer garbage")
        assert resp2.status_code == 200

    def test_aggregate_unknown_slug_404(self):
        client = APIClient()
        resp = client.get("/api/public/ghost/catalog")
        assert resp.status_code == 404

    def test_aggregate_inactive_merchant_404_threat(self):
        merchant = MerchantFactory(slug="inactive", is_active=False)
        _make_catalog(merchant)
        client = APIClient()
        resp = client.get(f"/api/public/{merchant.slug}/catalog")
        assert resp.status_code == 404, f"inactive should 404 got {resp.status_code}"

    def test_cross_merchant_isolation_excludes_beta(self):
        acme = MerchantFactory(slug="acme")
        beta = MerchantFactory(slug="beta")
        _make_catalog(acme)
        # beta has distinct catalog
        cat_b = CategoryFactory(merchant=beta, name="BetaCat")
        ProductFactory(merchant=beta, category=cat_b, name="BetaProd", price="999.00", product_type="UNIT", pote_size=None, min_flavors=None, max_flavors=None)
        FlavorFactory(merchant=beta, name="BetaFlavor")
        client = APIClient()
        resp = client.get(f"/api/public/{acme.slug}/catalog")
        assert resp.status_code == 200
        body = resp.json()
        names = {p["name"] for p in body["products"]}
        assert "BetaProd" not in names
        flav_names = {f["name"] for f in body["flavors"]}
        assert "BetaFlavor" not in flav_names
        cat_names = {c["name"] for c in body["categories"]}
        assert "BetaCat" not in cat_names
        # also beta endpoint should not contain acme products
        resp2 = client.get(f"/api/public/{beta.slug}/catalog")
        body2 = resp2.json()
        names2 = {p["name"] for p in body2["products"]}
        assert "Pote 1kg" not in names2

    def test_aggregate_filters_only_active(self):
        merchant = MerchantFactory(slug="acme4")
        cat = CategoryFactory(merchant=merchant, name="ActiveCat", is_active=True)
        CategoryFactory(merchant=merchant, name="InactiveCat", is_active=False)
        ProductFactory(merchant=merchant, category=cat, name="ActiveProd", is_active=True, price="10.00", product_type="UNIT", pote_size=None, min_flavors=None, max_flavors=None)
        ProductFactory(merchant=merchant, category=cat, name="InactiveProd", is_active=False, price="10.00", product_type="UNIT", pote_size=None, min_flavors=None, max_flavors=None)
        client = APIClient()
        resp = client.get(f"/api/public/{merchant.slug}/catalog")
        body = resp.json()
        cat_names = {c["name"] for c in body["categories"]}
        assert "InactiveCat" not in cat_names
        prod_names = {p["name"] for p in body["products"]}
        assert "InactiveProd" not in prod_names
