import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.tenancy.models import AuditEntry, SessionRecord
from apps.tenancy.tests.factories import PlatformUserFactory

pytestmark = pytest.mark.django_db


def _authed(username, password="Pass123!"):
    client = APIClient()
    login = client.post(
        "/api/auth/token/", {"username": username, "password": password}, format="json"
    )
    assert login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client, login


class TestMasterKeys:
    def test_reset_profile_less_superuser(self):
        master = User.objects.create_superuser("rootless", password="Pass123!")
        other = User.objects.create_superuser("othermaster", password="Pass123!")
        client, _ = _authed("othermaster")
        response = client.post(
            "/api/master/users/reset-request/", {"username": "rootless"}, format="json"
        )
        assert response.status_code == 200
        assert master is not None
        raw = response.data["reset_token"]
        done = APIClient().post(
            "/api/v1/users/reset-confirm/",
            {"token": raw, "new_password": "Root123!"},
            format="json",
        )
        assert done.status_code == 200

    def test_reset_issue_revokes_sessions(self):
        admin = PlatformUserFactory(role="ADMIN")
        target = PlatformUserFactory(role="CAJERO", merchant=admin.merchant)
        tclient, tlogin = _authed(target.user.username)
        assert tlogin.status_code == 200
        assert SessionRecord.objects.filter(
            user=target.user, revoked_at__isnull=True
        ).exists()
        aclient, _ = _authed(admin.user.username)
        issued = aclient.post(
            "/api/v1/users/reset-request/",
            {"username": target.user.username},
            format="json",
        )
        assert issued.status_code == 200
        assert not SessionRecord.objects.filter(
            user=target.user, revoked_at__isnull=True
        ).exists()
        stale = tclient.get("/api/v1/employees/")
        assert stale.status_code == 401

    def test_admin_lists_and_kills_session(self):
        admin = PlatformUserFactory(role="ADMIN")
        target = PlatformUserFactory(role="CAJERO", merchant=admin.merchant)
        _authed(target.user.username)
        aclient, _ = _authed(admin.user.username)
        listed = aclient.get(f"/api/v1/users/{target.pk}/sessions/")
        assert listed.status_code == 200
        assert len(listed.data) == 1
        killed = aclient.post(
            f"/api/v1/users/{target.pk}/sessions/revoke/", {}, format="json"
        )
        assert killed.status_code == 200
        assert killed.data["revoked"] == 1
        assert AuditEntry.objects.filter(action="SESSION_REVOKED").exists()

    def test_cross_merchant_session_forbidden(self):
        admin = PlatformUserFactory(role="ADMIN")
        other = PlatformUserFactory(role="CAJERO")
        aclient, _ = _authed(admin.user.username)
        assert aclient.get(f"/api/v1/users/{other.pk}/sessions/").status_code == 404
        assert (
            aclient.post(
                f"/api/v1/users/{other.pk}/sessions/revoke/", {}, format="json"
            ).status_code
            == 404
        )
