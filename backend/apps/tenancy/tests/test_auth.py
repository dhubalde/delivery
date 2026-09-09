import pytest
from rest_framework.test import APIClient

from apps.tenancy.models import Employee
from apps.tenancy.tests.factories import (
    EmployeeFactory,
    PlatformUserFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


def _login(username, password):
    client = APIClient()
    response = client.post(
        "/api/auth/token/", {"username": username, "password": password}, format="json"
    )
    return client, response


class TestJwtLogin:
    def test_login_returns_token_with_tenant_claims(self):
        profile = PlatformUserFactory(role="CAJERO")
        _, response = _login(profile.user.username, "Pass123!")
        assert response.status_code == 200
        assert response.data["access"]
        assert response.data["user"]["role"] == "CAJERO"
        assert response.data["user"]["merchant_id"] == profile.merchant_id

    def test_invalid_credentials_401(self):
        UserFactory(username="nobody")
        _, response = _login("nobody", "Wrong123!")
        assert response.status_code == 401
        assert "access" not in response.data


class TestTokenBoundTenant:
    def test_spoofed_slug_is_ignored(self):
        profile_a = PlatformUserFactory(role="ADMIN")
        profile_b = PlatformUserFactory(role="ADMIN")
        EmployeeFactory(merchant=profile_a.merchant, cuil="20111111111")
        EmployeeFactory(merchant=profile_b.merchant, cuil="20222222222")
        client, login = _login(profile_a.user.username, "Pass123!")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = client.get(
            "/api/v1/employees/", {"merchant_slug": profile_b.merchant.slug}
        )
        assert response.status_code == 200
        merchant_ids = {e["merchant_id"] for e in response.data}
        assert merchant_ids == {profile_a.merchant_id}

    def test_master_token_rejected_on_tenant_endpoint(self):
        from django.contrib.auth.models import User

        master = User.objects.create_superuser("master", password="Pass123!")
        client, login = _login("master", "Pass123!")
        assert master.is_superuser
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = client.get("/api/v1/employees/")
        assert response.status_code == 403

    def test_header_flow_still_works_without_token(self):
        profile = PlatformUserFactory(role="ADMIN")
        EmployeeFactory(merchant=profile.merchant, cuil="20333333333")
        client = APIClient()
        response = client.get(
            "/api/v1/employees/", {"merchant_slug": profile.merchant.slug}
        )
        assert response.status_code == 200
        assert {e["merchant_id"] for e in response.data} == {profile.merchant_id}
        assert Employee.objects.count() >= 1
