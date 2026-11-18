"""Mercado Pago Checkout Pro gateway adapter.

All HTTP is done through an injectable session so tests never touch the
network. Card data never passes through our server: the customer pays on the
Mercado Pago side and we learn the result from the payment resource + webhook.

The default session is built on the standard library on purpose: this app ships
with a minimal dependency set, and importing a third-party HTTP client that is
not declared in requirements.txt would break every `manage.py` command on a
clean install.
"""

import hashlib
import hmac
import json as _json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from apps.payments.models import Payment


class MercadoPagoError(Exception):
    pass


class _StdlibResponse:
    """Minimal stand-in for requests.Response: only what the gateway reads."""

    def __init__(self, status_code: int, body: bytes = b""):
        self.status_code = status_code
        self._body = body or b""

    def json(self):
        return _json.loads(self._body.decode() or "{}")


class _StdlibSession:
    """HTTP session with the same shape as requests.Session, no third-party deps.

    Keeping the shape means tests can inject fakes and callers can swap the
    transport, while the app boots on a bare Django install.
    """

    def post(self, url, json=None, headers=None, timeout=None):
        data = _json.dumps(json).encode() if json is not None else None
        merged = {"Content-Type": "application/json", **(headers or {})}
        return self._send("POST", url, data=data, headers=merged, timeout=timeout)

    def get(self, url, headers=None, timeout=None):
        return self._send("GET", url, data=None, headers=headers, timeout=timeout)

    @staticmethod
    def _send(method, url, *, data, headers, timeout):
        request = Request(url, data=data, headers=headers or {}, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                return _StdlibResponse(getattr(response, "status", 200), response.read())
        except HTTPError as exc:
            # Mirror requests: an error status is still a response the caller inspects.
            try:
                body = exc.read()
            except (OSError, AttributeError):
                body = b""
            return _StdlibResponse(exc.code, body)
        except URLError as exc:
            raise MercadoPagoError(f"network error: {exc.reason}") from exc


class MercadoPagoGateway:
    API_URL = "https://api.mercadopago.com"
    TIMEOUT = 15

    def __init__(self, access_token: str, webhook_secret: str | None = None, session=None):
        if not access_token:
            raise MercadoPagoError("Mercado Pago access token required")
        self.access_token = access_token
        self.webhook_secret = webhook_secret
        self.session = session or _StdlibSession()

    @classmethod
    def for_merchant(cls, merchant) -> "MercadoPagoGateway":
        token = getattr(merchant, "mp_access_token", None)
        if not token:
            raise MercadoPagoError("Merchant has no Mercado Pago credentials configured")
        return cls(token, webhook_secret=getattr(merchant, "mp_webhook_secret", None))

    # ------------------------------------------------------------------ API

    def create_preference(
        self,
        *,
        items,
        external_reference: str,
        back_urls,
        notification_url: str,
    ) -> dict:
        """Create a Checkout Pro preference. Returns {'id', 'init_point'}."""
        payload = {
            "items": list(items),
            "external_reference": str(external_reference),
            "back_urls": back_urls,
            "notification_url": notification_url,
        }
        resp = self.session.post(
            f"{self.API_URL}/checkout/preferences",
            json=payload,
            headers=self._headers(),
            timeout=self.TIMEOUT,
        )
        if resp.status_code >= 400:
            raise MercadoPagoError(f"preference failed: HTTP {resp.status_code}")
        data = resp.json()
        init_point = data.get("init_point") or data.get("sandbox_init_point")
        if not data.get("id") or not init_point:
            raise MercadoPagoError("preference response missing id/init_point")
        return {"id": str(data["id"]), "init_point": init_point}

    def get_payment(self, payment_id: str | int) -> dict:
        """Fetch a payment and normalize it to our Payment domain."""
        resp = self.session.get(
            f"{self.API_URL}/v1/payments/{payment_id}",
            headers=self._headers(),
            timeout=self.TIMEOUT,
        )
        if resp.status_code >= 400:
            raise MercadoPagoError(f"payment fetch failed: HTTP {resp.status_code}")
        data = resp.json()
        return {
            "mp_id": str(data.get("id", "")),
            "status": self._map_status(data.get("status")),
            "method": self._map_method(data.get("payment_method_id")),
            "amount": data.get("transaction_amount"),
            "external_reference": data.get("external_reference"),
        }

    # ------------------------------------------------------------- mapping

    @staticmethod
    def _map_status(mp_status) -> str:
        if mp_status == "approved":
            return Payment.Status.CONFIRMED
        if mp_status in ("rejected", "cancelled"):
            return Payment.Status.REJECTED
        return Payment.Status.PENDING

    @staticmethod
    def _map_method(payment_method_id) -> str:
        # account_money = the customer's Mercado Pago wallet; anything else is a card.
        return Payment.Method.BILLETERA if payment_method_id == "account_money" else Payment.Method.TARJETA

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    # ------------------------------------------------------------ webhook

    @staticmethod
    def validate_signature(x_signature: str | None, x_request_id: str | None, data_id: str | None, secret: str) -> bool:
        """Validate the x-signature header per MP docs: HMAC-SHA256 of the
        manifest ``id:<data.id>;request-id:<x-request-id>;ts:<ts>;`` (missing
        pairs omitted) compared against the ``v1`` hash."""
        if not x_signature or not secret:
            return False
        ts = None
        v1 = None
        for part in x_signature.split(","):
            name, _, value = part.strip().partition("=")
            if name == "ts":
                ts = value
            elif name == "v1":
                v1 = value
        if not ts or not v1:
            return False
        parts = []
        if data_id:
            parts.append(f"id:{data_id.lower()}")
        if x_request_id:
            parts.append(f"request-id:{x_request_id}")
        parts.append(f"ts:{ts}")
        manifest = ";".join(parts) + ";"
        expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, v1)
