"""Smoke 4.4: /acme catalog, /acme/checkout guest, register→linked order, /beta empty, POST /public/orders→404 + cross-slug isolation."""
import pytest
from datetime import time
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.tests.factories import CategoryFactory, ProductFactory, MerchantFactory, FlavorFactory
from apps.orders.models import Order
from apps.tenancy.models import Schedule, TimeRange

pytestmark = pytest.mark.django_db


def _open_merchant(slug, active=True):
    m = MerchantFactory(slug=slug, is_active=active)
    # open 24h for today
    now = timezone.now()
    weekday = now.date().weekday()
    sched, _ = Schedule.objects.get_or_create(merchant=m, weekday=weekday)
    TimeRange.objects.get_or_create(schedule=sched, opens_at=time(0, 0), closes_at=time(23, 59, 59))
    return m


def _make_product(merchant, name="Pote 1kg", price="100.00"):
    cat = CategoryFactory(merchant=merchant, name=f"Cat-{merchant.slug}", is_active=True)
    p = ProductFactory(merchant=merchant, category=cat, name=name, price=price, product_type="UNIT", pote_size=None, min_flavors=None, max_flavors=None, is_active=True)
    FlavorFactory(merchant=merchant, category=cat, name=f"Flavor-{merchant.slug}")
    return p


def _order_payload(product):
    return {
        "customer_name": "Guest",
        "customer_phone": "555-0000",
        "fulfillment": "DELIVERY",
        "address": "Calle 123",
        "items": [{"product_id": product.pk, "quantity": 1}],
        "payments": [{"method": "EFECTIVO", "amount": str(product.price)}],
    }


class TestSmokeCatalogIsolation:
    """Phase 4.4 smoke — covers isolation, guest, auth-link, beta empty, bare 404, cross-slug."""

    def test_smoke_acme_catalog_checkout_register_linked_beta_isolated_bare_404(self):
        client = APIClient()
        # setup two merchants with disjoint catalogs
        acme = _open_merchant("acme")
        beta = _open_merchant("beta")
        p_acme = _make_product(acme, name="AcmeProd", price="100.00")
        p_beta = _make_product(beta, name="BetaProd", price="200.00")

        # 1) /acme catalog 200 with isolated products
        resp = client.get(f"/api/public/{acme.slug}/catalog")
        assert resp.status_code == 200, resp.content
        body = resp.json()
        assert body["merchant"]["slug"] == "acme"
        prod_names = {p["name"] for p in body["products"]}
        assert "AcmeProd" in prod_names
        assert "BetaProd" not in prod_names

        # 2) /acme/checkout as guest — POST orders without Customer JWT → 201 guest
        payload = _order_payload(p_acme)
        resp2 = client.post(f"/api/public/{acme.slug}/orders", data=payload, format="json", HTTP_IDEMPOTENCY_KEY="smoke-guest-acme")
        assert resp2.status_code == 201, resp2.content
        order_guest = Order.objects.get(pk=resp2.json()["id"])
        assert order_guest.customer is None
        assert order_guest.merchant_id == acme.pk

        # 3) register on acme → linked order
        reg = client.post(f"/api/public/{acme.slug}/customers/register", data={"phone": "555-9000", "name": "Alice", "password": "secret123"}, format="json")
        assert reg.status_code == 201, reg.content
        access = reg.json()["access"]
        payload2 = _order_payload(p_acme)
        resp3 = client.post(f"/api/public/{acme.slug}/orders", data=payload2, format="json", HTTP_AUTHORIZATION=f"Customer {access}", HTTP_IDEMPOTENCY_KEY="smoke-linked-acme")
        assert resp3.status_code == 201, resp3.content
        order_linked = Order.objects.get(pk=resp3.json()["id"])
        assert order_linked.customer is not None
        assert order_linked.customer.phone == "555-9000"

        # 4) /beta catalog isolated — no acme data
        resp4 = client.get(f"/api/public/{beta.slug}/catalog")
        assert resp4.status_code == 200
        body4 = resp4.json()
        prod_names4 = {p["name"] for p in body4["products"]}
        assert "BetaProd" in prod_names4
        assert "AcmeProd" not in prod_names4
        assert len(body4["products"]) == 1

        # ensure beta has no linked order leakage from acme token (cross-slug)
        payload_beta = _order_payload(p_beta)
        resp5 = client.post(f"/api/public/{beta.slug}/orders", data=payload_beta, format="json", HTTP_AUTHORIZATION=f"Customer {access}", HTTP_IDEMPOTENCY_KEY="smoke-cross-beta")
        assert resp5.status_code == 201, resp5.content
        order_cross = Order.objects.get(pk=resp5.json()["id"])
        # acme token on beta must NOT link
        assert order_cross.customer is None, "cross-merchant Customer token must not link"
        assert order_cross.merchant_id == beta.pk

        # 5) POST /public/orders without slug → 404 (bare public path removed)
        resp6 = client.post("/api/public/orders", data={}, format="json", HTTP_IDEMPOTENCY_KEY="smoke-bare-404")
        assert resp6.status_code == 404
        resp7 = client.post("/api/public/orders/", data={}, format="json", HTTP_IDEMPOTENCY_KEY="smoke-bare-404-slash")
        assert resp7.status_code == 404

        # 6) mismatched token does not block guest (already covered but explicit)
        assert Order.objects.filter(merchant=acme).count() >= 2
        assert Order.objects.filter(merchant=beta).count() >= 1
