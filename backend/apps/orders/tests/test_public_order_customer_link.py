import pytest
from datetime import time
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.tests.factories import CategoryFactory, MerchantFactory, ProductFactory
from apps.customers.models import Customer
from apps.orders.models import Order
from apps.tenancy.models import Schedule, TimeRange

pytestmark = pytest.mark.django_db


def _make_open_product(merchant, price="100.00"):
    now = timezone.now()
    weekday = now.date().weekday()
    sched, _ = Schedule.objects.get_or_create(merchant=merchant, weekday=weekday)
    TimeRange.objects.get_or_create(schedule=sched, opens_at=time(0, 0), closes_at=time(23, 59, 59))
    cat = CategoryFactory(merchant=merchant, name="Cat1")
    p = ProductFactory(merchant=merchant, category=cat, price=price, product_type="UNIT", pote_size=None, min_flavors=None, max_flavors=None)
    return p


def _order_payload(product, customer_name="Guest"):
    return {
        "customer_name": customer_name,
        "customer_phone": "555-0000",
        "fulfillment": "DELIVERY",
        "address": "Test 123",
        "items": [{"product_id": product.pk, "quantity": 1}],
        "payments": [{"method": "EFECTIVO", "amount": str(product.price)}],
    }


def _register_customer(client, slug, phone="555-2000", password="secret123"):
    return client.post(f"/api/public/{slug}/customers/register", data={"phone": phone, "name": "Alice", "password": password}, format="json")


class TestPublicOrderGuestAndAuth:
    def test_guest_order_succeeds_without_customer_jwt(self):
        merchant = MerchantFactory(slug="acme")
        product = _make_open_product(merchant)
        client = APIClient()
        payload = _order_payload(product)
        resp = client.post(f"/api/public/{merchant.slug}/orders", data=payload, format="json", HTTP_IDEMPOTENCY_KEY="k-guest-1")
        assert resp.status_code == 201, resp.content
        order = Order.objects.get(pk=resp.json()["id"])
        assert order.customer is None
        assert order.merchant_id == merchant.pk

    def test_authenticated_order_links_customer(self):
        merchant = MerchantFactory(slug="acme")
        product = _make_open_product(merchant)
        client = APIClient()
        reg = _register_customer(client, merchant.slug, phone="555-2000")
        assert reg.status_code == 201, reg.content
        access = reg.json()["access"]
        payload = _order_payload(product, customer_name="Alice")
        resp = client.post(f"/api/public/{merchant.slug}/orders", data=payload, format="json", HTTP_AUTHORIZATION=f"Customer {access}", HTTP_IDEMPOTENCY_KEY="k-auth-1")
        assert resp.status_code == 201, resp.content
        order = Order.objects.get(pk=resp.json()["id"])
        assert order.customer is not None
        assert order.customer.phone == "555-2000"
        assert order.customer.merchant_id == merchant.pk

    def test_mismatched_customer_token_does_not_block_creates_guest(self):
        acme = MerchantFactory(slug="acme")
        beta = MerchantFactory(slug="beta")
        prod_acme = _make_open_product(acme, price="100.00")
        client = APIClient()
        # register customer for beta
        reg = _register_customer(client, beta.slug, phone="555-2000")
        assert reg.status_code == 201
        beta_token = reg.json()["access"]
        # post to acme with beta token — should still create guest order, not fail, not link
        payload = _order_payload(prod_acme)
        resp = client.post(f"/api/public/{acme.slug}/orders", data=payload, format="json", HTTP_AUTHORIZATION=f"Customer {beta_token}", HTTP_IDEMPOTENCY_KEY="k-mismatch-1")
        assert resp.status_code == 201, resp.content
        order = Order.objects.get(pk=resp.json()["id"])
        assert order.customer is None, "mismatched mid must not link"
        assert order.merchant_id == acme.pk

    def test_invalid_customer_token_fallback_to_guest(self):
        merchant = MerchantFactory(slug="acme")
        product = _make_open_product(merchant)
        client = APIClient()
        payload = _order_payload(product)
        resp = client.post(f"/api/public/{merchant.slug}/orders", data=payload, format="json", HTTP_AUTHORIZATION="Customer invalid.token.here", HTTP_IDEMPOTENCY_KEY="k-invalid-1")
        assert resp.status_code == 201
        order = Order.objects.get(pk=resp.json()["id"])
        assert order.customer is None

    def test_bearer_token_does_not_link_customer_guest(self):
        """Threat: Bearer prefix must not be treated as Customer — guest order."""
        merchant = MerchantFactory(slug="acme")
        product = _make_open_product(merchant)
        client = APIClient()
        reg = _register_customer(client, merchant.slug, phone="555-2000")
        access = reg.json()["access"]
        payload = _order_payload(product)
        # Send same token but with Bearer prefix — should be ignored
        resp = client.post(f"/api/public/{merchant.slug}/orders", data=payload, format="json", HTTP_AUTHORIZATION=f"Bearer {access}", HTTP_IDEMPOTENCY_KEY="k-bearer-1")
        assert resp.status_code == 201
        order = Order.objects.get(pk=resp.json()["id"])
        assert order.customer is None, "Bearer must not link as Customer"

    def test_guest_order_allow_any_no_bearer_required(self):
        merchant = MerchantFactory(slug="acme")
        product = _make_open_product(merchant)
        client = APIClient()
        payload = _order_payload(product)
        # No auth header at all
        resp = client.post(f"/api/public/{merchant.slug}/orders", data=payload, format="json", HTTP_IDEMPOTENCY_KEY="k-allow-1")
        assert resp.status_code == 201

    def test_order_cross_merchant_product_rejected(self):
        acme = MerchantFactory(slug="acme")
        beta = MerchantFactory(slug="beta")
        prod_beta = _make_open_product(beta)
        # need acme open too
        _make_open_product(acme)
        client = APIClient()
        payload = _order_payload(prod_beta)
        resp = client.post(f"/api/public/{acme.slug}/orders", data=payload, format="json", HTTP_IDEMPOTENCY_KEY="k-cross-prod-1")
        assert resp.status_code == 400
        assert "does not belong" in resp.json()["error"]["message"]

    def test_order_inactive_merchant_404(self):
        merchant = MerchantFactory(slug="inactive", is_active=False)
        # Even with product, should 404 before validation
        client = APIClient()
        resp = client.post(f"/api/public/{merchant.slug}/orders", data={}, format="json", HTTP_IDEMPOTENCY_KEY="k-inactive-1")
        assert resp.status_code == 404
