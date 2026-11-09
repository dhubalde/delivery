"""Red: manual order entry from kanban — source=MANUAL + TRANSFER payment method.

Rules under test:
- PublicOrderCreateView accepts `source` in {"WEB","MANUAL"}; anything else/missing → WEB.
- MANUAL source is persisted and visible on the board serializer.
- Payment method TRANSFER is recorded as PENDING without going through the gateway.
- EFECTIVO keeps its current behavior (PENDING + cash_declared=True).
"""
import pytest
from datetime import time
from rest_framework.test import APIClient
from django.utils import timezone

from apps.catalog.tests.factories import CategoryFactory, ProductFactory, MerchantFactory
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.tenancy.models import Schedule, TimeRange

pytestmark = pytest.mark.django_db


def _open_merchant(slug, active=True):
    m = MerchantFactory(slug=slug, is_active=active)
    now = timezone.now()
    weekday = now.date().weekday()
    sched, _ = Schedule.objects.get_or_create(merchant=m, weekday=weekday)
    TimeRange.objects.get_or_create(schedule=sched, opens_at=time(0, 0), closes_at=time(23, 59, 59))
    return m


def _make_product(merchant, name="Pote 1kg", price="100.00"):
    cat = CategoryFactory(merchant=merchant, name=f"Cat-{merchant.slug}", is_active=True)
    p = ProductFactory(merchant=merchant, category=cat, name=name, price=price, product_type="UNIT", pote_size=None, min_flavors=None, max_flavors=None, is_active=True)
    return p


def _post_order(client, slug, product, *, source=None, method="EFECTIVO", amount=None):
    payload = {
        "customer_name": "Guest",
        "customer_phone": "555-0000",
        "fulfillment": "DELIVERY",
        "address": "Calle 123",
        "items": [{"product_id": product.pk, "quantity": 1}],
        "payments": [{"method": method, "amount": str(amount if amount is not None else product.price)}],
    }
    if source is not None:
        payload["source"] = source
    return client.post(
        f"/api/public/{slug}/orders",
        data=payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=f"manual-{method}-{source}",
    )


def _get_board(client, merchant):
    return client.get("/api/v1/orders", HTTP_X_MERCHANT_ID=str(merchant.pk))


class TestManualOrderSource:

    def test_manual_source_accepted_and_visible_on_board(self):
        merchant = _open_merchant("manualsrc")
        product = _make_product(merchant)
        client = APIClient()
        resp = _post_order(client, merchant.slug, product, source="MANUAL")
        assert resp.status_code == 201, resp.content
        board = _get_board(client, merchant)
        assert board.status_code == 200
        sources = {o["code"]: o.get("source") for o in board.json()}
        assert sources[resp.json()["code"]] == "MANUAL"

    def test_missing_or_invalid_source_defaults_to_web(self):
        merchant = _open_merchant("manualdef")
        product = _make_product(merchant)
        client = APIClient()
        resp_missing = _post_order(client, merchant.slug, product)
        assert resp_missing.status_code == 201
        resp_invalid = _post_order(client, merchant.slug, product, source="HACK", method="EFECTIVO", amount="100.00")
        assert resp_invalid.status_code == 201, resp_invalid.content
        board = _get_board(client, merchant).json()
        sources = {o["code"]: o.get("source") for o in board}
        assert sources[resp_missing.json()["code"]] == "WEB"
        assert sources[resp_invalid.json()["code"]] == "WEB"

    def test_transfer_payment_recorded_pending_without_gateway(self):
        merchant = _open_merchant("manualtrans")
        product = _make_product(merchant)
        client = APIClient()
        resp = _post_order(client, merchant.slug, product, source="MANUAL", method="TRANSFER")
        assert resp.status_code == 201, resp.content
        order = Order.objects.get(pk=resp.json()["id"])
        pays = list(order.payments.all())
        assert len(pays) == 1
        assert pays[0].method == "TRANSFER"
        assert pays[0].status == Payment.Status.PENDING
        assert pays[0].gateway_ref in (None, "")

    def test_transfer_method_rejected_amount_mismatch_still_validates(self):
        merchant = _open_merchant("manualamt")
        product = _make_product(merchant)
        client = APIClient()
        resp = _post_order(client, merchant.slug, product, source="MANUAL", method="TRANSFER", amount="50.00")
        assert resp.status_code == 400, resp.content
