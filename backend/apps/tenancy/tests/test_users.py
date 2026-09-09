import pytest
from rest_framework.test import APIClient

from apps.tenancy.models import AuditEntry, PlatformUser
from apps.tenancy.tests.factories import BranchFactory, PlatformUserFactory

pytestmark = pytest.mark.django_db


def _authed(profile):
    client = APIClient()
    login = client.post(
        "/api/auth/token/",
        {"username": profile.user.username, "password": "Pass123!"},
        format="json",
    )
    assert login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


def _admin(merchant=None, **kwargs):
    kwargs.setdefault("role", "ADMIN")
    if merchant is not None:
        kwargs["merchant"] = merchant
    return PlatformUserFactory(**kwargs)


class TestUsersCrud:
    def test_cajero_cannot_create_user(self):
        cajero = PlatformUserFactory(role="CAJERO")
        client = _authed(cajero)
        response = client.post(
            "/api/v1/users/",
            {"username": "nuevo", "password": "Pass123!", "role": "CAJERO"},
            format="json",
        )
        assert response.status_code == 403

    def test_anonymous_cannot_list_users(self):
        response = APIClient().get("/api/v1/users/")
        assert response.status_code == 401

    def test_admin_creates_user_with_must_change(self):
        admin = _admin()
        client = _authed(admin)
        response = client.post(
            "/api/v1/users/",
            {"username": "caja1", "password": "Pass123!", "role": "CAJERO"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["username"] == "caja1"
        assert response.data["must_change_password"] is True
        assert response.data["merchant_id"] == admin.merchant_id
        assert AuditEntry.objects.filter(action="USER_GRANTED_ADMIN").count() == 0

    def test_admin_grant_is_audited(self):
        admin = _admin()
        client = _authed(admin)
        response = client.post(
            "/api/v1/users/",
            {"username": "jefe2", "password": "Pass123!", "role": "ADMIN"},
            format="json",
        )
        assert response.status_code == 201
        entry = AuditEntry.objects.filter(action="USER_GRANTED_ADMIN").first()
        assert entry is not None
        assert entry.detail["username"] == "jefe2"
        assert entry.actor_id == admin.user_id

    def test_seat_limit_enforced(self):
        admin = _admin()
        admin.merchant.seat_limit = 1
        admin.merchant.save(update_fields=["seat_limit"])
        client = _authed(admin)
        response = client.post(
            "/api/v1/users/",
            {"username": "extra", "password": "Pass123!", "role": "CAJERO"},
            format="json",
        )
        assert response.status_code == 409

    def test_deactivated_user_frees_seat(self):
        admin = _admin()
        admin.merchant.seat_limit = 2
        admin.merchant.save(update_fields=["seat_limit"])
        client = _authed(admin)
        created = client.post(
            "/api/v1/users/",
            {"username": "temp", "password": "Pass123!", "role": "CAJERO"},
            format="json",
        )
        assert created.status_code == 201
        temp_id = created.data["id"]
        delete = client.delete(f"/api/v1/users/{temp_id}/")
        assert delete.status_code == 204
        temp = PlatformUser.objects.get(pk=temp_id)
        assert temp.user.is_active is False
        # Seats full would be admin + temp; temp deactivated so this must succeed.
        retry = client.post(
            "/api/v1/users/",
            {"username": "temp2", "password": "Pass123!", "role": "CAJERO"},
            format="json",
        )
        assert retry.status_code == 201

    def test_branch_must_belong_to_merchant(self):
        admin = _admin()
        other_branch = BranchFactory()
        client = _authed(admin)
        response = client.post(
            "/api/v1/users/",
            {
                "username": "suc",
                "password": "Pass123!",
                "role": "CAJERO",
                "branch_id": other_branch.pk,
            },
            format="json",
        )
        assert response.status_code in (400, 422)

    def test_admin_lists_only_own_merchant(self):
        admin_a = _admin()
        admin_b = _admin()
        client = _authed(admin_a)
        response = client.get("/api/v1/users/")
        assert response.status_code == 200
        assert {u["merchant_id"] for u in response.data} == {admin_a.merchant_id}
        assert admin_b.merchant_id not in {u["merchant_id"] for u in response.data}
