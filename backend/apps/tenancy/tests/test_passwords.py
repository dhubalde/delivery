from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from apps.tenancy.models import PasswordResetToken, SessionRecord
from apps.tenancy.tests.factories import PlatformUserFactory

pytestmark = pytest.mark.django_db


def _authed(profile, password="Pass123!"):
    client = APIClient()
    login = client.post(
        "/api/auth/token/",
        {"username": profile.user.username, "password": password},
        format="json",
    )
    assert login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client, login


class TestPasswordPolicy:
    def test_weak_password_rejected_on_create(self):
        admin = PlatformUserFactory(role="ADMIN")
        client, _ = _authed(admin)
        response = client.post(
            "/api/v1/users/",
            {"username": "weak", "password": "caja123", "role": "CAJERO"},
            format="json",
        )
        assert response.status_code == 400
        assert not User.objects.filter(username="weak").exists()

    def test_must_change_blocks_other_endpoints(self):
        admin = PlatformUserFactory(role="ADMIN")
        client, _ = _authed(admin)
        created = client.post(
            "/api/v1/users/",
            {"username": "fresh", "password": "Pass123!", "role": "CAJERO"},
            format="json",
        )
        assert created.status_code == 201
        fresh_client = APIClient()
        fresh_login = fresh_client.post(
            "/api/auth/token/",
            {"username": "fresh", "password": "Pass123!"},
            format="json",
        )
        assert fresh_login.status_code == 200
        fresh_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {fresh_login.data['access']}"
        )
        blocked = fresh_client.get("/api/v1/employees/")
        assert blocked.status_code == 403
        changed = fresh_client.post(
            "/api/v1/users/change-password/",
            {"current_password": "Pass123!", "new_password": "NewPass1!"},
            format="json",
        )
        assert changed.status_code == 200
        allowed = fresh_client.get("/api/v1/employees/")
        assert allowed.status_code == 200

    def test_wrong_current_password_rejected(self):
        admin = PlatformUserFactory(role="ADMIN")
        client, _ = _authed(admin)
        response = client.post(
            "/api/v1/users/change-password/",
            {"current_password": "Nope123!", "new_password": "NewPass1!"},
            format="json",
        )
        assert response.status_code == 400

    def test_internal_rotation_expiry(self):
        tech = PlatformUserFactory(role="TECNICO", merchant=None, must_change_password=False)
        tech.password_changed_at = timezone.now() - timedelta(days=200)
        tech.save(update_fields=["password_changed_at"])
        client = APIClient()
        response = client.post(
            "/api/auth/token/",
            {"username": tech.user.username, "password": "Pass123!"},
            format="json",
        )
        assert response.status_code == 401

    def test_master_never_expires(self):
        master = User.objects.create_superuser("oldboss", password="Pass123!")
        client = APIClient()
        response = client.post(
            "/api/auth/token/",
            {"username": "oldboss", "password": "Pass123!"},
            format="json",
        )
        assert response.status_code == 200
        assert master.is_superuser


class TestPasswordReset:
    def test_full_reset_flow_burns_token(self):
        admin = PlatformUserFactory(role="ADMIN")
        target = PlatformUserFactory(role="CAJERO", merchant=admin.merchant)
        client, _ = _authed(admin)
        issued = client.post(
            "/api/v1/users/reset-request/", {"username": target.user.username}, format="json"
        )
        assert issued.status_code == 200
        raw = issued.data["reset_token"]
        anon = APIClient()
        weak = anon.post(
            "/api/v1/users/reset-confirm/",
            {"token": raw, "new_password": "short"},
            format="json",
        )
        assert weak.status_code == 422
        done = anon.post(
            "/api/v1/users/reset-confirm/",
            {"token": raw, "new_password": "Reset123!"},
            format="json",
        )
        assert done.status_code == 200
        assert PasswordResetToken.objects.get(user=target.user).is_burned
        reuse = anon.post(
            "/api/v1/users/reset-confirm/",
            {"token": raw, "new_password": "Again123!"},
            format="json",
        )
        assert reuse.status_code == 410
        login = anon.post(
            "/api/auth/token/",
            {"username": target.user.username, "password": "Reset123!"},
            format="json",
        )
        assert login.status_code == 200

    def test_master_cannot_reset_self(self):
        master = User.objects.create_superuser("selfboss", password="Pass123!")
        client = APIClient()
        login = client.post(
            "/api/auth/token/",
            {"username": "selfboss", "password": "Pass123!"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = client.post(
            "/api/master/users/reset-request/", {"username": "selfboss"}, format="json"
        )
        assert response.status_code == 403
        assert master.is_superuser


class TestSessionCaps:
    def test_third_login_evicts_oldest(self):
        cajero = PlatformUserFactory(role="CAJERO")
        tokens = []
        for _ in range(3):
            client = APIClient()
            login = client.post(
                "/api/auth/token/",
                {"username": cajero.user.username, "password": "Pass123!"},
                format="json",
            )
            assert login.status_code == 200
            tokens.append(login.data["access"])
        assert SessionRecord.objects.filter(
            user=cajero.user, revoked_at__isnull=True
        ).count() == 2
        first = APIClient()
        first.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens[0]}")
        assert first.get("/api/v1/employees/").status_code == 401
        last = APIClient()
        last.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens[2]}")
        assert last.get("/api/v1/employees/").status_code == 200
