import pytest
from rest_framework.test import APIClient

from apps.catalog.tests.factories import MerchantFactory
from apps.tenancy.models import AuditEntry
from apps.tenancy.tests.factories import PlatformUserFactory

pytestmark = pytest.mark.django_db


def _master_client(username="cboss"):
    from django.contrib.auth.models import User

    master = User.objects.create_superuser(username, password="Pass123!")
    client = APIClient()
    login = client.post(
        "/api/auth/token/", {"username": username, "password": "Pass123!"}, format="json"
    )
    assert login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


def _tech_client(company):
    tech = PlatformUserFactory(role="TECNICO", merchant=None)
    tech.assigned_merchants.set([company.pk])
    client = APIClient()
    login = client.post(
        "/api/auth/token/",
        {"username": tech.user.username, "password": "Pass123!"},
        format="json",
    )
    assert login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


class TestCompanyDetail:
    def test_master_updates_seats_and_flags(self):
        client = _master_client()
        comp = MerchantFactory(seat_limit=10, has_branches=False)
        response = client.patch(
            f"/api/master/companies/{comp.pk}/",
            {"seat_limit": 30, "has_branches": True, "name": "Nuevo nombre"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["seat_limit"] == 30
        assert response.data["has_branches"] is True
        assert "active_users" in response.data
        entry = AuditEntry.objects.filter(action="COMPANY_UPDATED").first()
        assert entry is not None
        assert entry.merchant_id == comp.pk

    def test_invalid_tier_rejected(self):
        client = _master_client()
        comp = MerchantFactory()
        response = client.patch(
            f"/api/master/companies/{comp.pk}/", {"seat_limit": 99}, format="json"
        )
        assert response.status_code == 400

    def test_deactivate(self):
        client = _master_client()
        comp = MerchantFactory()
        response = client.delete(f"/api/master/companies/{comp.pk}/")
        assert response.status_code == 204
        comp.refresh_from_db()
        assert comp.is_active is False

    def test_assigned_tech_reads_but_cannot_write(self):
        comp = MerchantFactory()
        tclient = _tech_client(comp)
        assert tclient.get(f"/api/master/companies/{comp.pk}/").status_code == 200
        assert (
            tclient.patch(
                f"/api/master/companies/{comp.pk}/", {"seat_limit": 30}, format="json"
            ).status_code
            == 403
        )
        other = MerchantFactory()
        assert tclient.get(f"/api/master/companies/{other.pk}/").status_code == 404


class TestCompanyList:
    def test_list_exposes_table_flags_without_secrets(self):
        client = _master_client()
        comp = MerchantFactory(
            print_tickets=True,
            mp_access_token="APP-USR-123",
            mp_webhook_secret="whsec-abc",
        )
        response = client.get("/api/master/companies/")
        assert response.status_code == 200
        row = next(r for r in response.data if r["id"] == comp.pk)
        assert row["print_tickets"] is True
        assert row["has_online_payments"] is True
        # Credentials are write-only: the table never receives them.
        assert "mp_access_token" not in row
        assert "mp_webhook_secret" not in row

    def test_list_reports_missing_payment_credentials(self):
        client = _master_client()
        comp = MerchantFactory()
        response = client.get("/api/master/companies/")
        row = next(r for r in response.data if r["id"] == comp.pk)
        assert row["has_online_payments"] is False
        assert row["print_tickets"] is False
