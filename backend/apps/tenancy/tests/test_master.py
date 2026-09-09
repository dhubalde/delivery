import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.catalog.tests.factories import MerchantFactory
from apps.tenancy.models import AuditEntry, Merchant
from apps.tenancy.tests.factories import PlatformUserFactory

pytestmark = pytest.mark.django_db


def _client_for(user):
    client = APIClient()
    login = client.post(
        "/api/auth/token/", {"username": user.username, "password": "Pass123!"}, format="json"
    )
    assert login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


def _master(username="boss"):
    master = User.objects.create_superuser(username, password="Pass123!")
    return _client_for(master), master


def _internal(role="TECNICO", password="Pass123!"):
    profile = PlatformUserFactory(
        role=role, merchant=None, kind="PERSONAL", must_change_password=False
    )
    profile.user.set_password(password)
    profile.user.save()
    return profile


class TestMasterPanel:
    def test_master_lists_all_companies(self):
        MerchantFactory(slug="listed-a")
        MerchantFactory(slug="listed-b")
        client, _ = _master()
        response = client.get("/api/master/companies/")
        assert response.status_code == 200
        assert {c["slug"] for c in response.data} >= {"listed-a", "listed-b"}

    def test_assigned_internal_lists_only_assigned(self):
        client, _ = _master()
        onboard = client.post(
            "/api/master/companies/",
            {
                "name": "A", "slug": "comp-a", "seat_limit": 10,
                "admin_username": "adm-a", "admin_password": "Pass123!",
            },
            format="json",
        )
        assert onboard.status_code == 201
        onboard2 = client.post(
            "/api/master/companies/",
            {
                "name": "B", "slug": "comp-b", "seat_limit": 10,
                "admin_username": "adm-b", "admin_password": "Pass123!",
            },
            format="json",
        )
        assert onboard2.status_code == 201
        tech = _internal()
        tech.assigned_merchants.set([Merchant.objects.get(slug="comp-a").pk])
        tclient = _client_for(tech.user)
        response = tclient.get("/api/master/companies/")
        assert response.status_code == 200
        assert {c["slug"] for c in response.data} == {"comp-a"}

    def test_master_creates_internal_user_with_assignments(self):
        client, master = _master()
        comp = MerchantFactory(slug="assigned-co")
        response = client.post(
            "/api/master/users/",
            {
                "username": "tec1", "password": "Pass123!", "role": "TECNICO",
                "assigned_merchants": [comp.pk],
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["assigned_merchants"][0]["slug"] == "assigned-co"
        entry = AuditEntry.objects.filter(action="INTERNAL_USER_CREATED").first()
        assert entry is not None
        assert entry.actor_id == master.pk

    def test_junior_cannot_create_internal_user(self):
        _master()
        junior = _internal(role="JUNIOR")
        jclient = _client_for(junior.user)
        response = jclient.post(
            "/api/master/users/",
            {"username": "tec2", "password": "Pass123!", "role": "TECNICO"},
            format="json",
        )
        assert response.status_code == 403
        assert not User.objects.filter(username="tec2").exists()

    def test_assign_companies_patch(self):
        client, _ = _master()
        tech = _internal()
        comp = MerchantFactory(slug="patched-co")
        response = client.patch(
            f"/api/master/users/{tech.pk}/",
            {"assigned_merchants": [comp.pk]},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["assigned_merchants"][0]["slug"] == "patched-co"

    def test_audit_scoped_to_assigned(self):
        client, _ = _master()
        client.post(
            "/api/master/companies/",
            {
                "name": "C", "slug": "comp-c", "seat_limit": 10,
                "admin_username": "adm-c", "admin_password": "Pass123!",
            },
            format="json",
        )
        tech = _internal()
        tech.assigned_merchants.set([Merchant.objects.get(slug="comp-c").pk])
        tclient = _client_for(tech.user)
        response = tclient.get("/api/master/audit/")
        assert response.status_code == 200
        merchants = {e["merchant"] for e in response.data}
        assert merchants <= {"comp-c", None}
        mall = client.get("/api/master/audit/")
        assert mall.status_code == 200
        assert len(mall.data) >= len(response.data)

    def test_operative_admin_forbidden_on_master(self):
        _master()
        operative = PlatformUserFactory(role="ADMIN")
        oclient = _client_for(operative.user)
        assert oclient.get("/api/master/companies/").status_code == 403
        assert oclient.get("/api/master/audit/").status_code == 403
