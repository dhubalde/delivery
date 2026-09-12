import pytest
from rest_framework.test import APIClient

from apps.catalog.tests.factories import MerchantFactory
from apps.customers.models import Customer
from apps.customers.auth import get_tokens_for_customer

pytestmark = pytest.mark.django_db


def _register(client, slug, phone="555-2000", name="Alice", password="secret123"):
    return client.post(f"/api/public/{slug}/customers/register", data={"phone": phone, "name": name, "password": password}, format="json")


def _login(client, slug, phone="555-2000", password="secret123"):
    return client.post(f"/api/public/{slug}/customers/login", data={"phone": phone, "password": password}, format="json")


class TestCustomerRegister:
    def test_register_creates_customer_and_returns_jwt_with_mid_cid(self):
        merchant = MerchantFactory(slug="acme", is_active=True)
        client = APIClient()
        resp = _register(client, merchant.slug)
        assert resp.status_code == 201, resp.content
        body = resp.json()
        assert "access" in body
        assert "refresh" in body or "tokens" in body
        # decode token to check claims
        from rest_framework_simplejwt.tokens import AccessToken

        access = body.get("access") or body["tokens"]["access"]
        payload = AccessToken(access).payload
        assert int(payload["mid"]) == merchant.pk
        assert int(payload["cid"]) == body["customer"]["id"]
        assert Customer.objects.filter(merchant=merchant, phone="555-2000").exists()

    def test_register_duplicate_phone_same_merchant_409(self):
        merchant = MerchantFactory(slug="acme")
        client = APIClient()
        resp1 = _register(client, merchant.slug, phone="555-1000")
        assert resp1.status_code == 201
        resp2 = _register(client, merchant.slug, phone="555-1000")
        assert resp2.status_code == 409

    def test_register_same_phone_across_merchants_allowed(self):
        m1 = MerchantFactory(slug="acme")
        m2 = MerchantFactory(slug="beta")
        client = APIClient()
        resp1 = _register(client, m1.slug, phone="555-1000")
        assert resp1.status_code == 201
        resp2 = _register(client, m2.slug, phone="555-1000")
        assert resp2.status_code == 201
        assert Customer.objects.filter(phone="555-1000").count() == 2

    def test_register_inactive_merchant_404(self):
        merchant = MerchantFactory(slug="ghost", is_active=False)
        client = APIClient()
        resp = _register(client, merchant.slug)
        assert resp.status_code == 404

    def test_register_unknown_slug_404(self):
        client = APIClient()
        resp = _register(client, "ghost2")
        assert resp.status_code == 404

    def test_register_missing_fields_400(self):
        merchant = MerchantFactory(slug="acme")
        client = APIClient()
        resp = client.post(f"/api/public/{merchant.slug}/customers/register", data={"phone": ""}, format="json")
        assert resp.status_code == 400


class TestCustomerLogin:
    def test_login_returns_scoped_jwt(self):
        merchant = MerchantFactory(slug="acme")
        client = APIClient()
        _register(client, merchant.slug, phone="555-2000", password="s3cret!")
        resp = _login(client, merchant.slug, phone="555-2000", password="s3cret!")
        assert resp.status_code == 200, resp.content
        from rest_framework_simplejwt.tokens import AccessToken

        access = resp.json()["access"]
        payload = AccessToken(access).payload
        assert int(payload["mid"]) == merchant.pk

    def test_login_wrong_password_401(self):
        merchant = MerchantFactory(slug="acme")
        client = APIClient()
        _register(client, merchant.slug, phone="555-2000", password="correct")
        resp = _login(client, merchant.slug, phone="555-2000", password="wrong")
        assert resp.status_code == 401

    def test_login_unknown_phone_401_no_leak(self):
        merchant = MerchantFactory(slug="acme")
        client = APIClient()
        resp = _login(client, merchant.slug, phone="unknown", password="anything")
        assert resp.status_code == 401

    def test_login_cross_merchant_phone_not_found_401(self):
        m1 = MerchantFactory(slug="acme")
        m2 = MerchantFactory(slug="beta")
        client = APIClient()
        _register(client, m1.slug, phone="555-2000", password="secret123")
        resp = _login(client, m2.slug, phone="555-2000", password="secret123")
        assert resp.status_code == 401, "phone scoped to merchant, beta should not find it"


class TestCustomerMe:
    def test_me_returns_profile_for_valid_customer_token(self):
        merchant = MerchantFactory(slug="acme")
        client = APIClient()
        reg = _register(client, merchant.slug, phone="555-2000")
        access = reg.json()["access"]
        resp = client.get(f"/api/public/{merchant.slug}/customers/me", HTTP_AUTHORIZATION=f"Customer {access}")
        assert resp.status_code == 200, resp.content
        body = resp.json()
        assert body["phone"] == "555-2000"
        assert body["merchant_slug"] == "acme"

    def test_me_cross_merchant_jwt_rejected_403(self):
        acme = MerchantFactory(slug="acme")
        beta = MerchantFactory(slug="beta")
        client = APIClient()
        reg = _register(client, acme.slug, phone="555-2000")
        access = reg.json()["access"]
        resp = client.get(f"/api/public/{beta.slug}/customers/me", HTTP_AUTHORIZATION=f"Customer {access}")
        assert resp.status_code in (401, 403), f"expected 401/403 got {resp.status_code} {resp.content}"

    def test_me_missing_token_401(self):
        merchant = MerchantFactory(slug="acme")
        client = APIClient()
        resp = client.get(f"/api/public/{merchant.slug}/customers/me")
        assert resp.status_code == 401

    def test_me_bearer_prefix_rejected_401_threat(self):
        merchant = MerchantFactory(slug="acme")
        client = APIClient()
        reg = _register(client, merchant.slug, phone="555-2000")
        access = reg.json()["access"]
        # Use Bearer instead of Customer — must fail
        resp = client.get(f"/api/public/{merchant.slug}/customers/me", HTTP_AUTHORIZATION=f"Bearer {access}")
        assert resp.status_code == 401, f"Bearer on customer/me should 401, got {resp.status_code}"

    def test_me_customer_prefix_with_bearer_token_401(self):
        """Ensure platform Bearer token does not auth as customer (prefix isolation)."""
        merchant = MerchantFactory(slug="acme")
        # Create a PlatformUser token (WorkZone) - we can synthesize simplejwt with merchant_id claim
        from django.contrib.auth.models import User
        from apps.tenancy.models import PlatformUser
        from rest_framework_simplejwt.tokens import RefreshToken

        user = User.objects.create_user(username="admin_acme", password="pass")
        PlatformUser.objects.create(user=user, merchant=merchant, role="ADMIN")
        refresh = RefreshToken.for_user(user)
        refresh["merchant_id"] = merchant.pk
        access = str(refresh.access_token)
        client = APIClient()
        resp = client.get(f"/api/public/{merchant.slug}/customers/me", HTTP_AUTHORIZATION=f"Customer {access}")
        # This access token has no mid/cid → should 401
        assert resp.status_code == 401

    def test_me_invalid_token_401(self):
        merchant = MerchantFactory(slug="acme")
        client = APIClient()
        resp = client.get(f"/api/public/{merchant.slug}/customers/me", HTTP_AUTHORIZATION="Customer invalid.token.here")
        assert resp.status_code == 401
