"""Red: timezone-aware opening hours + manual phone-order overrides.

Rules under test:
- is_open() must evaluate schedules in the business timezone (America/Argentina/Buenos_Aires),
  not UTC: an AR evening time maps to the next UTC day, so weekday/date must be local.
- A manual phone order (source=MANUAL) may be created even when the schedule is closed
  (the operator decides: the caller ordered by phone).
- A manual order whose phone matches a registered customer links to that customer,
  without any Customer JWT (the web flow keeps requiring the JWT to link).
"""
import pytest
from datetime import time, datetime
from zoneinfo import ZoneInfo
from django.utils import timezone as djtz
from rest_framework.test import APIClient

from apps.catalog.tests.factories import CategoryFactory, ProductFactory, MerchantFactory
from apps.tenancy.services.hours import is_open
from apps.tenancy.models import Schedule, TimeRange

pytestmark = pytest.mark.django_db

AR = ZoneInfo("America/Argentina/Buenos_Aires")


def _schedule(merchant, weekday):
    sched, _ = Schedule.objects.get_or_create(merchant=merchant, weekday=weekday)
    TimeRange.objects.get_or_create(schedule=sched, opens_at=time(15, 0), closes_at=time(23, 0))
    return sched


def _merchant(slug="tzmerchant"):
    return MerchantFactory(slug=slug, is_active=True)


def _product_for(merchant):
    cat = CategoryFactory(merchant=merchant, name=f"Cat-{merchant.slug}", is_active=True)
    return ProductFactory(merchant=merchant, category=cat, name="Pote", price="100.00", product_type="UNIT", pote_size=None, min_flavors=None, max_flavors=None, is_active=True)


def _payload(product, phone="555-0000", source=None):
    payload = {
        "customer_name": "Invitado T",
        "customer_phone": phone,
        "fulfillment": "DELIVERY",
        "address": "Calle 123",
        "items": [{"product_id": product.pk, "quantity": 1}],
        "payments": [{"method": "EFECTIVO", "amount": "100.00"}],
    }
    if source:
        payload["source"] = source
    return payload


class TestIsOpenTimezone:
    def test_ar_evening_maps_to_local_weekday_not_utc_next_day(self):
        """2026-01-10 21:00 AR == 2026-01-11 00:00 UTC: schedule is on the AR date."""
        merchant = _merchant("tzeve")
        _schedule(merchant, weekday=5)  # Saturday = AR weekday of 2026-01-10
        dt_utc = datetime(2026, 1, 11, 0, 0, tzinfo=ZoneInfo("UTC"))  # 21:00 AR Sat
        assert is_open(merchant, dt=dt_utc) is True

    def test_live_now_uses_local_weekday(self):
        """is_open() without dt must look up the schedule of the AR-local weekday."""
        merchant = _merchant("tzlive")
        ar_now = djtz.now().astimezone(AR)
        _schedule(merchant, weekday=ar_now.date().weekday())
        in_range = time(15, 0) <= ar_now.time() < time(23, 0)
        if in_range:
            assert is_open(merchant) is True

    def test_merchant_without_schedules_defaults_open(self):
        merchant = _merchant("nosched")
        assert is_open(merchant) is True


class TestManualOrderOverrides:
    def test_manual_order_created_while_schedule_closed(self):
        merchant = _merchant("manualclosed")
        _schedule(merchant, weekday=(djtz.now().astimezone(AR).date().weekday() + 1) % 7)
        # Schedule exists only for the *next* weekday: today is closed (unless wrap).
        merchant_p = _product_for(merchant)
        client = APIClient()
        resp = client.post(
            f"/api/public/{merchant.slug}/orders",
            data=_payload(merchant_p, source="MANUAL"),
            format="json",
            HTTP_IDEMPOTENCY_KEY="manual-closed",
        )
        assert resp.status_code == 201, resp.content

    def test_web_order_closed_still_rejected(self):
        merchant = _merchant("webclosed")
        _schedule(merchant, weekday=(djtz.now().astimezone(AR).date().weekday() + 1) % 7)
        merchant_p = _product_for(merchant)
        client = APIClient()
        resp = client.post(
            f"/api/public/{merchant.slug}/orders",
            data=_payload(merchant_p),
            format="json",
            HTTP_IDEMPOTENCY_KEY="web-closed",
        )
        assert resp.status_code == 409, resp.content

    def test_manual_order_links_registered_customer_by_phone(self):
        from apps.orders.models import Order

        merchant = _merchant("linkphone")
        client = APIClient()
        product = _product_for(merchant)
        reg = client.post(
            f"/api/public/{merchant.slug}/customers/register",
            data={"email": "link@example.com", "phone": "+543424508000", "name": "Cliente Registrado", "default_address": "San Martin 1234", "password": "secreto123"},
            format="json",
        )
        assert reg.status_code == 201, reg.content
        resp = client.post(
            f"/api/public/{merchant.slug}/orders",
            data=_payload(product, phone="+543424508000", source="MANUAL"),
            format="json",
            HTTP_IDEMPOTENCY_KEY="manual-link",
        )
        assert resp.status_code == 201, resp.content
        order = Order.objects.get(pk=resp.json()["id"])
        assert order.customer is not None
        assert order.customer.email == "link@example.com"

    def test_web_order_same_phone_stays_guest(self):
        from apps.orders.models import Order

        merchant = _merchant("weblink")
        client = APIClient()
        product = _product_for(merchant)
        client.post(
            f"/api/public/{merchant.slug}/customers/register",
            data={"email": "web@example.com", "phone": "+543425080001", "name": "Web Cliente", "default_address": "San Martin 5678", "password": "secreto123"},
            format="json",
        )
        resp = client.post(
            f"/api/public/{merchant.slug}/orders",
            data=_payload(product, phone="+543425080001"),
            format="json",
            HTTP_IDEMPOTENCY_KEY="web-guest",
        )
        assert resp.status_code == 201, resp.content
        order = Order.objects.get(pk=resp.json()["id"])
        assert order.customer is None
