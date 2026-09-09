import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.tenancy.models import AuditEntry, Merchant
from apps.tenancy.tests.factories import PlatformUserFactory

pytestmark = pytest.mark.django_db

PAYLOAD = {
    "name": "Pizzeria Don Juan",
    "slug": "pizzeria-don-juan",
    "seat_limit": 20,
    "has_branches": True,
    "admin_username": "juan-admin",
    "admin_password": "Pass123!",
}


def _master_client():
    master = User.objects.create_superuser("boss", password="Pass123!")
    client = APIClient()
    login = client.post(
        "/api/auth/token/", {"username": "boss", "password": "Pass123!"}, format="json"
    )
    assert login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client, master


class TestCompanyOnboarding:
    def test_happy_path_creates_all(self):
        client, master = _master_client()
        response = client.post("/api/master/companies/", PAYLOAD, format="json")
        assert response.status_code == 201
        merchant = Merchant.objects.get(slug="pizzeria-don-juan")
        assert merchant.seat_limit == 20
        assert merchant.has_branches is True
        assert response.data["admin"]["username"] == "juan-admin"
        assert response.data["admin"]["must_change_password"] is True
        admin_user = User.objects.get(username="juan-admin")
        assert admin_user.platform_profile.merchant_id == merchant.pk
        assert admin_user.platform_profile.role == "ADMIN"
        entry = AuditEntry.objects.filter(action="COMPANY_ONBOARDED").first()
        assert entry is not None
        assert entry.actor_id == master.pk
        assert entry.merchant_id == merchant.pk

    def test_duplicate_slug_409_and_nothing_created(self):
        client, _ = _master_client()
        assert client.post("/api/master/companies/", PAYLOAD, format="json").status_code == 201
        count_merchants = Merchant.objects.count()
        count_users = User.objects.count()
        dup = dict(PAYLOAD, admin_username="other-admin", name="Other Name")
        response = client.post("/api/master/companies/", dup, format="json")
        assert response.status_code == 409
        assert Merchant.objects.count() == count_merchants
        assert User.objects.count() == count_users
        assert not User.objects.filter(username="other-admin").exists()

    def test_duplicate_admin_username_rolls_back_merchant(self):
        client, _ = _master_client()
        User.objects.create_user("taken-admin", password="Pass123!")
        count_merchants = Merchant.objects.count()
        bad = dict(PAYLOAD, slug="brand-new-slug", admin_username="taken-admin")
        response = client.post("/api/master/companies/", bad, format="json")
        assert response.status_code in (400, 409)
        assert not Merchant.objects.filter(slug="brand-new-slug").exists()
        assert Merchant.objects.count() == count_merchants

    def test_invalid_tier_rejected(self):
        client, _ = _master_client()
        bad = dict(PAYLOAD, slug="tier-test", seat_limit=99)
        response = client.post("/api/master/companies/", bad, format="json")
        assert response.status_code == 400
        assert not Merchant.objects.filter(slug="tier-test").exists()

    def test_operative_admin_forbidden(self):
        operative = PlatformUserFactory(role="ADMIN")
        client = APIClient()
        login = client.post(
            "/api/auth/token/",
            {"username": operative.user.username, "password": "Pass123!"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = client.post("/api/master/companies/", PAYLOAD, format="json")
        assert response.status_code == 403
        assert not Merchant.objects.filter(slug="pizzeria-don-juan").exists()
