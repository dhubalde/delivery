"""Online payments (Mercado Pago Checkout Pro): pay endpoints, webhook and guards."""

import pytest
from rest_framework.test import APIClient

from apps.catalog.tests.factories import MerchantFactory, UnitProductFactory
from apps.orders.models import Order
from apps.orders.tests.factories import OrderFactory
from apps.payments.models import Payment
from apps.tenancy.tests.factories import PlatformUserFactory

pytestmark = pytest.mark.django_db


def _login(username):
    client = APIClient()
    response = client.post(
        "/api/auth/token/", {"username": username, "password": "Pass123!"}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


def _admin(merchant):
    return PlatformUserFactory(role="ADMIN", merchant=merchant, must_change_password=False)


def _transition(client, order, to_state):
    return client.post(
        f"/api/v1/orders/{order.pk}/transition/",
        {"to_state": to_state},
        format="json",
    )


class FakeGateway:
    """Stands in for MercadoPagoGateway in endpoints/webhook tests (no network)."""

    def __init__(self):
        self.created = 0
        self.fetched = 0
        self.preference = {"id": "pref-1", "init_point": "https://mp/pref-1"}
        self.payment = {
            "mp_id": "99",
            "status": "CONFIRMED",
            "method": "BILLETERA",
            "amount": 1000.0,
            "external_reference": None,
        }

    @classmethod
    def for_merchant(cls, merchant):
        return cls()

    def create_preference(self, *, items, external_reference, back_urls, notification_url):
        self.created += 1
        return dict(self.preference)

    def get_payment(self, payment_id):
        self.fetched += 1
        data = dict(self.payment)
        data["external_reference"] = str(data["external_reference"])
        return data


@pytest.fixture
def fake_gateway(monkeypatch):
    """Replace the gateway factory in services so every caller gets one shared fake."""
    gw = FakeGateway()

    class GatewayStub:
        for_merchant = staticmethod(lambda merchant: gw)

    monkeypatch.setattr("apps.payments.services.MercadoPagoGateway", GatewayStub)
    return gw


class TestOrderCreationWithOnlinePayment:
    def test_public_order_accepts_online_method_as_pending(self):
        merchant = MerchantFactory()
        product = UnitProductFactory(category__merchant=merchant, merchant=merchant)
        client = APIClient()
        response = client.post(
            f"/api/public/{merchant.slug}/orders",
            {
                "items": [{"product_id": product.pk, "quantity": 1, "flavor_ids": []}],
                "payments": [{"method": "ONLINE", "amount": "8500.00"}],
                "fulfillment": "DELIVERY",
                "customer_name": "Ana",
                "customer_phone": "3424508000",
                "address": "San Martín 1234",
            },
            format="json",
            headers={"Idempotency-Key": "pay-on-1"},
        )
        assert response.status_code == 201, response.json()
        order = Order.objects.get(pk=response.json()["id"])
        pay = order.payments.first()
        assert pay.method == Payment.Method.ONLINE
        assert pay.status == Payment.Status.PENDING
        assert pay.amount == order.total


class TestPayEndpoints:
    def test_public_pay_creates_preference_and_is_idempotent(self, fake_gateway):
        merchant = MerchantFactory(mp_access_token="TEST-TOKEN")
        order = OrderFactory(merchant=merchant)
        Payment.objects.create(order=order, method=Payment.Method.ONLINE, amount=order.total, status=Payment.Status.PENDING)
        client = APIClient()
        r1 = client.post(f"/api/public/{merchant.slug}/orders/{order.pk}/pay")
        assert r1.status_code == 200, r1.json()
        assert r1.json()["init_point"] == "https://mp/pref-1"
        pay = order.payments.first()
        pay.refresh_from_db()
        assert pay.checkout_url == "https://mp/pref-1"
        assert pay.gateway_ref == "pref-1"
        r2 = client.post(f"/api/public/{merchant.slug}/orders/{order.pk}/pay")
        assert r2.status_code == 200
        assert r2.json()["init_point"] == "https://mp/pref-1"
        assert fake_gateway.created == 1  # reused, not re-created

    def test_pay_requires_credentials(self):
        merchant = MerchantFactory()  # no token
        order = OrderFactory(merchant=merchant)
        client = APIClient()
        r = client.post(f"/api/public/{merchant.slug}/orders/{order.pk}/pay")
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "MP_NOT_CONFIGURED"

    def test_staff_generates_payment_link(self, fake_gateway):
        merchant = MerchantFactory(mp_access_token="TEST-TOKEN")
        admin = _admin(merchant)
        order = OrderFactory(merchant=merchant, source=Order.Source.MANUAL)
        Payment.objects.create(order=order, method=Payment.Method.ONLINE, amount=order.total, status=Payment.Status.PENDING)
        client = _login(admin.user.username)
        r = client.post(f"/api/v1/orders/{order.pk}/payment-link/")
        assert r.status_code == 200, r.json()
        assert r.json()["init_point"] == "https://mp/pref-1"


class TestWebhook:
    def _merchant_with_order(self, **kw):
        merchant = MerchantFactory(mp_access_token="TEST-TOKEN", **kw)
        order = OrderFactory(merchant=merchant)
        Payment.objects.create(order=order, method=Payment.Method.ONLINE, amount=order.total, status=Payment.Status.PENDING)
        return merchant, order

    def test_confirms_online_payment_idempotently(self, fake_gateway):
        merchant, order = self._merchant_with_order()
        fake_gateway.payment["external_reference"] = str(order.pk)
        client = APIClient()
        body = {"type": "payment", "data": {"id": "99"}}
        r1 = client.post(f"/api/payments/webhook/{merchant.slug}/", body, format="json")
        assert r1.status_code == 200
        pay = order.payments.first()
        pay.refresh_from_db()
        assert pay.status == Payment.Status.CONFIRMED
        assert pay.method == Payment.Method.BILLETERA
        assert pay.gateway_ref == "99"
        assert pay.confirmed_at is not None
        # Replayed notification must be a no-op.
        r2 = client.post(f"/api/payments/webhook/{merchant.slug}/", body, format="json")
        assert r2.status_code == 200
        pay.refresh_from_db()
        assert pay.status == Payment.Status.CONFIRMED
        assert fake_gateway.fetched == 2  # both notifications hit the API, but the update is idempotent

    def test_bad_signature_rejected(self, fake_gateway):
        merchant, order = self._merchant_with_order(mp_webhook_secret="WHSEC")
        fake_gateway.payment["external_reference"] = str(order.pk)
        client = APIClient()
        client.credentials(HTTP_X_SIGNATURE="ts=1,v1=deadbeef", HTTP_X_REQUEST_ID="req-1")
        r = client.post(f"/api/payments/webhook/{merchant.slug}/", {"type": "payment", "data": {"id": "99"}}, format="json")
        assert r.status_code == 401
        order.payments.first().refresh_from_db()
        assert order.payments.first().status == Payment.Status.PENDING

    def test_non_payment_notification_ignored(self, fake_gateway):
        merchant, order = self._merchant_with_order()
        client = APIClient()
        r = client.post(f"/api/payments/webhook/{merchant.slug}/", {"type": "merchant_order", "data": {"id": "1"}}, format="json")
        assert r.status_code == 200
        order.payments.first().refresh_from_db()
        assert order.payments.first().status == Payment.Status.PENDING


class TestEntryGuards:
    def test_board_hides_pending_online_orders(self):
        merchant = MerchantFactory()
        cod = OrderFactory(merchant=merchant)
        Payment.objects.create(order=cod, method=Payment.Method.EFECTIVO, amount=cod.total, status=Payment.Status.PENDING)
        online = OrderFactory(merchant=merchant)
        Payment.objects.create(order=online, method=Payment.Method.ONLINE, amount=online.total, status=Payment.Status.PENDING)
        client = APIClient()
        client.credentials(HTTP_X_MERCHANT_SLUG=merchant.slug)
        data = client.get("/api/v1/orders/").json()
        codes = {o["code"] for o in data}
        assert cod.code in codes
        assert online.code not in codes

    def test_transition_blocked_until_payment_confirmed(self, fake_gateway):
        merchant = MerchantFactory(mp_access_token="TEST-TOKEN")
        admin = _admin(merchant)
        order = OrderFactory(merchant=merchant)
        Payment.objects.create(order=order, method=Payment.Method.ONLINE, amount=order.total, status=Payment.Status.PENDING)
        client = _login(admin.user.username)
        r = _transition(client, order, "PREPARACION")
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "INVALID_TRANSITION"
        # After MP confirms the payment, the order enters and can be prepared.
        fake_gateway.payment["external_reference"] = str(order.pk)
        hook = APIClient()
        assert hook.post(f"/api/payments/webhook/{merchant.slug}/", {"type": "payment", "data": {"id": "99"}}, format="json").status_code == 200
        client2 = APIClient()
        client2.credentials(HTTP_X_MERCHANT_SLUG=merchant.slug)
        assert order.code in {o["code"] for o in client2.get("/api/v1/orders/").json()}
        r2 = _transition(client, order, "PREPARACION")
        assert r2.status_code == 200
