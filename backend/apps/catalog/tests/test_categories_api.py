import pytest
from rest_framework.test import APIClient

from apps.catalog.tests.factories import CategoryFactory, MerchantFactory

pytestmark = pytest.mark.django_db


def test_list_returns_categories():
    merchant = MerchantFactory(slug="ice-zone")
    CategoryFactory(merchant=merchant, name="Helados", position=1)
    CategoryFactory(merchant=merchant, name="Postres", position=2)
    client = APIClient()
    resp = client.get("/api/catalog/categories/", {"merchant_slug": "ice-zone"})
    assert resp.status_code == 200
    data = resp.json()
    if isinstance(data, dict) and "results" in data:
        data = data["results"]
    assert len(data) == 2
    names = {c["name"] for c in data}
    assert "Helados" in names


def test_create_as_admin_with_merchant_header():
    merchant = MerchantFactory(slug="ice-zone")
    client = APIClient()
    resp = client.post(
        "/api/catalog/categories/",
        {"name": "Tortas", "is_active": True, "position": 3},
        format="json",
        HTTP_X_MERCHANT_ID=str(merchant.pk),
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Tortas"


def test_soft_delete_hides_from_list():
    merchant = MerchantFactory(slug="ice-zone")
    cat = CategoryFactory(merchant=merchant, name="Borrar")
    client = APIClient()
    resp = client.delete(f"/api/catalog/categories/{cat.pk}/", HTTP_X_MERCHANT_ID=str(merchant.pk))
    assert resp.status_code == 204
    resp = client.get("/api/catalog/categories/", {"merchant_slug": "ice-zone"})
    data = resp.json()
    if isinstance(data, dict) and "results" in data:
        data = data["results"]
    assert all(c["id"] != cat.pk for c in data)
