import hashlib
import hmac

import pytest

from apps.payments.gateways.mercado_pago import MercadoPagoError, MercadoPagoGateway


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class FakeSession:
    """Records requests so tests assert on the exact HTTP calls (no network)."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"method": "POST", "url": url, "json": json, "headers": headers})
        return self.responses.pop(0)

    def get(self, url, headers=None, timeout=None):
        self.calls.append({"method": "GET", "url": url, "headers": headers})
        return self.responses.pop(0)


pytestmark = pytest.mark.django_db


def test_create_preference_posts_payload_and_returns_init_point():
    sess = FakeSession([FakeResponse({"id": "pref-1", "init_point": "https://mp/p/ref-1"})])
    gw = MercadoPagoGateway("TEST-TOKEN", session=sess)
    pref = gw.create_preference(
        items=[{"title": "Pedido #12", "quantity": 1, "unit_price": 1500.0, "currency_id": "ARS"}],
        external_reference="12",
        back_urls={"success": "https://x/ok", "failure": "https://x/fail", "pending": "https://x/pending"},
        notification_url="https://x/api/payments/webhook/demo-mercado/",
    )
    assert pref == {"id": "pref-1", "init_point": "https://mp/p/ref-1"}
    call = sess.calls[0]
    assert call["url"] == "https://api.mercadopago.com/checkout/preferences"
    assert call["headers"]["Authorization"] == "Bearer TEST-TOKEN"
    assert call["json"]["external_reference"] == "12"
    assert call["json"]["notification_url"] == "https://x/api/payments/webhook/demo-mercado/"


def test_get_payment_maps_status_method_and_amount():
    sess = FakeSession(
        [
            FakeResponse({"id": 99, "status": "approved", "payment_method_id": "account_money", "transaction_amount": 1500.0, "external_reference": "12"}),
            FakeResponse({"id": 100, "status": "approved", "payment_method_id": "master", "transaction_amount": 800.0, "external_reference": "13"}),
            FakeResponse({"id": 101, "status": "rejected", "payment_method_id": "visa", "transaction_amount": 500.0, "external_reference": "14"}),
            FakeResponse({"id": 102, "status": "in_process", "payment_method_id": "visa", "transaction_amount": 500.0, "external_reference": "15"}),
        ]
    )
    gw = MercadoPagoGateway("TEST-TOKEN", session=sess)
    p1 = gw.get_payment(99)
    assert p1 == {"mp_id": "99", "status": "CONFIRMED", "method": "BILLETERA", "amount": 1500.0, "external_reference": "12"}
    assert gw.get_payment(100)["method"] == "TARJETA"
    assert gw.get_payment(101)["status"] == "REJECTED"
    assert gw.get_payment(102)["status"] == "PENDING"
    assert sess.calls[0]["url"] == "https://api.mercadopago.com/v1/payments/99"


def test_validate_signature_uses_mp_manifest():
    secret = "whsec-abc"
    data_id = "123456789"
    request_id = "req-1"
    ts = "1700000000000"
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{ts};"
    v1 = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    assert MercadoPagoGateway.validate_signature(f"ts={ts},v1={v1}", request_id, data_id, secret) is True
    assert MercadoPagoGateway.validate_signature(f"ts={ts},v1={'0' * len(v1)}", request_id, data_id, secret) is False


def test_validate_signature_omits_missing_pairs():
    secret = "whsec-abc"
    # No data.id available (notification without it): only request-id and ts go in the manifest.
    manifest = "request-id:req-2;ts:1700000000001;"
    v1 = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    assert MercadoPagoGateway.validate_signature("ts=1700000000001,v1=" + v1, "req-2", None, secret) is True


def test_for_merchant_requires_token():
    with pytest.raises(MercadoPagoError):
        MercadoPagoGateway.for_merchant(type("M", (), {"mp_access_token": None})())
