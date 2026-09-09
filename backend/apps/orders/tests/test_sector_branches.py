import pytest
from rest_framework.test import APIClient

from apps.orders.models import Order
from apps.orders.tests.factories import OrderFactory
from apps.tenancy.tests.factories import PlatformUserFactory

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


class TestBranchesCrud:
    def _admin_client(self, **merchant_kwargs):
        from apps.catalog.tests.factories import MerchantFactory

        merchant_kwargs.setdefault("has_branches", True)
        merchant = MerchantFactory(**merchant_kwargs)
        admin = PlatformUserFactory(role="ADMIN", merchant=merchant)
        return _authed(admin), merchant

    def test_gate_disabled_by_default(self):
        from apps.catalog.tests.factories import MerchantFactory

        merchant = MerchantFactory(has_branches=False)
        admin = PlatformUserFactory(role="ADMIN", merchant=merchant)
        client = _authed(admin)
        assert client.get("/api/v1/branches/").status_code == 404
        assert (
            client.post("/api/v1/branches/", {"name": "X"}, format="json").status_code
            == 404
        )

    def test_crud_scoped(self):
        client, merchant = self._admin_client()
        created = client.post(
            "/api/v1/branches/", {"name": "Centro", "phone": "123"}, format="json"
        )
        assert created.status_code == 201
        assert created.data["merchant_id"] == merchant.pk
        listed = client.get("/api/v1/branches/")
        assert listed.status_code == 200
        assert {b["name"] for b in listed.data} == {"Centro"}
        patched = client.patch(
            f"/api/v1/branches/{created.data['id']}/",
            {"phone": "999"},
            format="json",
        )
        assert patched.status_code == 200
        assert patched.data["phone"] == "999"

    def test_cajero_forbidden(self):
        from apps.catalog.tests.factories import MerchantFactory

        merchant = MerchantFactory(has_branches=True)
        cajero = PlatformUserFactory(role="CAJERO", merchant=merchant)
        client = _authed(cajero)
        assert client.get("/api/v1/branches/").status_code == 403


class TestSectorGuard:
    def test_station_operates_own_sector(self):
        station = PlatformUserFactory(
            role="PREPARADOR", kind="STATION", sector="PREPARACION"
        )
        order = OrderFactory(merchant=station.merchant, state=Order.State.PREPARACION)
        order.cash_declared = True
        order.save(update_fields=["cash_declared"])
        client = _authed(station)
        response = client.post(
            f"/api/v1/orders/{order.pk}/transition/", {"to_state": "FACTURACION"}, format="json"
        )
        assert response.status_code in (200, 201, 204)

    def test_station_blocked_outside_sector(self):
        station = PlatformUserFactory(
            role="PREPARADOR", kind="STATION", sector="PREPARACION"
        )
        order = OrderFactory(merchant=station.merchant, state=Order.State.LOGISTICA)
        client = _authed(station)
        response = client.post(
            f"/api/v1/orders/{order.pk}/transition/", {"to_state": "ENTREGADO"}, format="json"
        )
        assert response.status_code == 403

    def test_admin_bypasses_sector(self):
        admin = PlatformUserFactory(role="ADMIN")
        order = OrderFactory(merchant=admin.merchant, state=Order.State.RECIBIDO)
        client = _authed(admin)
        response = client.post(
            f"/api/v1/orders/{order.pk}/transition/", {"to_state": "PREPARACION"}, format="json"
        )
        assert response.status_code in (200, 201, 204)

    def test_anonymous_keeps_legacy_behavior(self):
        order = OrderFactory(state=Order.State.RECIBIDO)
        response = APIClient().post(
            f"/api/v1/orders/{order.pk}/transition/",
            {"to_state": "PREPARACION"},
            format="json",
        )
        assert response.status_code in (200, 201, 204)
