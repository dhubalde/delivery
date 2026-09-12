import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.catalog.tests.factories import CategoryFactory, ProductFactory, MerchantFactory


pytestmark = pytest.mark.django_db


class TestDuplicatePublicOrdersRoute:
    """PR1 1.4 RED — duplicate shadows slug: POST /public/orders→404 vs POST /public/{slug}/orders→201"""

    def _make_product(self, merchant):
        # Ensure merchant is open now for is_open check
        from datetime import time
        from django.utils import timezone
        from apps.tenancy.models import Schedule, TimeRange

        now = timezone.now()
        weekday = now.date().weekday()
        sched, _ = Schedule.objects.get_or_create(merchant=merchant, weekday=weekday)
        # Create time range covering whole day
        TimeRange.objects.get_or_create(schedule=sched, opens_at=time(0, 0), closes_at=time(23, 59, 59))
        cat = CategoryFactory(merchant=merchant, name="Cat1")
        p = ProductFactory(merchant=merchant, category=cat, price="100.00", product_type="UNIT", pote_size=None, min_flavors=None, max_flavors=None)
        return p

    def _order_payload(self, product):
        return {
            "customer_name": "Guest",
            "customer_phone": "555-0000",
            "fulfillment": "DELIVERY",
            "address": "Test 123",
            "items": [{"product_id": product.pk, "quantity": 1}],
            "payments": [{"method": "EFECTIVO", "amount": "100.00"}],
        }

    def test_root_public_orders_without_slug_returns_404(self):
        client = APIClient()
        # This must be 404 after dedup — no slug-less route
        resp = client.post(
            "/api/public/orders",
            data={},
            format="json",
            HTTP_IDEMPOTENCY_KEY="k-root-404",
        )
        assert resp.status_code == 404, f"Expected 404 for slug-less root, got {resp.status_code} body={resp.content!r}"

    def test_root_public_orders_slash_without_slug_returns_404(self):
        client = APIClient()
        resp = client.post(
            "/api/public/orders/",
            data={},
            format="json",
            HTTP_IDEMPOTENCY_KEY="k-root-slash-404",
        )
        assert resp.status_code == 404

    def test_slug_public_orders_succeeds(self):
        merchant = MerchantFactory(slug="acme")
        product = self._make_product(merchant)
        client = APIClient()
        payload = self._order_payload(product)
        resp = client.post(
            f"/api/public/{merchant.slug}/orders",
            data=payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="k-acme-1",
        )
        assert resp.status_code == 201, f"Expected 201 for slug route, got {resp.status_code} body={resp.content!r}"
        assert resp.data["total"] == "100.00"

    def test_slug_public_orders_with_trailing_slash_succeeds(self):
        merchant = MerchantFactory(slug="acme2")
        product = self._make_product(merchant)
        client = APIClient()
        payload = self._order_payload(product)
        resp = client.post(
            f"/api/public/{merchant.slug}/orders/",
            data=payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="k-acme2-1",
        )
        assert resp.status_code == 201

    def test_config_has_single_slug_include_for_orders(self):
        from django.conf import settings
        from pathlib import Path
        text = Path(settings.BASE_DIR / "config" / "urls.py").read_text()
        count_orders = text.count('include("apps.orders.urls_public")')
        assert count_orders == 1, f"Expected exactly 1 include for orders, found {count_orders}"
        assert 'api/public/<slug:slug>/' in text
        # Ensure bare duplicate removed
        assert text.count('path("api/public/", include("apps.orders') == 0

    def test_orders_urls_public_has_no_root_path(self):
        from pathlib import Path
        from django.conf import settings
        text = Path(settings.BASE_DIR / "apps" / "orders" / "urls_public.py").read_text()
        # bare paths "" or "/" must be gone
        assert 'name="public-order-create-root"' not in text
        assert 'path("",' not in text
        assert 'path("/",' not in text
