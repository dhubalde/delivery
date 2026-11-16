import pytest
from rest_framework.test import APIClient

from apps.catalog.tests.factories import MerchantFactory
from apps.tenancy.tests.factories import PlatformUserFactory

pytestmark = pytest.mark.django_db


def _master_client(username="cboss"):
    from django.contrib.auth.models import User

    User.objects.create_superuser(username, password="Pass123!")
    client = APIClient()
    login = client.post(
        "/api/auth/token/", {"username": username, "password": "Pass123!"}, format="json"
    )
    assert login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


class TestMerchantPaymentConfig:
    def test_master_sets_mp_credentials_and_response_hides_them(self):
        client = _master_client()
        comp = MerchantFactory()
        response = client.patch(
            f"/api/master/companies/{comp.pk}/",
            {"mp_access_token": "TEST-ACCESS", "mp_webhook_secret": "WHSEC"},
            format="json",
        )
        assert response.status_code == 200
        comp.refresh_from_db()
        assert comp.mp_access_token == "TEST-ACCESS"
        assert comp.mp_webhook_secret == "WHSEC"
        # Secrets never come back in responses.
        assert "mp_access_token" not in response.json()
        assert "mp_webhook_secret" not in response.json()

    def test_public_merchant_endpoint_never_exposes_credentials(self):
        m = MerchantFactory(mp_access_token="TEST-ACCESS", mp_webhook_secret="WHSEC")
        client = APIClient()
        client.credentials(HTTP_X_MERCHANT_SLUG=m.slug)
        data = client.get("/api/v1/merchant/").json()
        assert "mp_access_token" not in data
        assert "mp_webhook_secret" not in data
