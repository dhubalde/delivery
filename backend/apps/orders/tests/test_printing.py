import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.test import APIClient

from apps.catalog.tests.factories import MerchantFactory
from apps.orders.models import Order, PrintJob
from apps.orders.tests.factories import OrderFactory
from apps.tenancy.tests.factories import PlatformUserFactory

pytestmark = pytest.mark.django_db


def _login(username):
    client = APIClient()
    response = client.post(
        "/api/auth/token/", {"username": username, "password": "Pass123!"}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


def _admin(merchant):
    return PlatformUserFactory(role="ADMIN", merchant=merchant, must_change_password=False)


def _transition(client, order, to_state):
    return client.post(
        f"/api/v1/orders/{order.pk}/transition/",
        {"to_state": to_state},
        format="json",
    )


class TestOrderSearchFilters:
    """CONSULTAS searches past tickets by code and by customer name/phone."""

    def test_filter_by_code(self):
        merchant = MerchantFactory()
        OrderFactory(merchant=merchant, code=7)
        OrderFactory(merchant=merchant, code=9)
        client = APIClient()
        client.credentials(HTTP_X_MERCHANT_SLUG=merchant.slug)
        data = client.get("/api/v1/orders/", {"code": 7}).json()
        assert [o["code"] for o in data] == [7]

    def test_filter_by_customer_name_and_phone(self):
        merchant = MerchantFactory()
        OrderFactory(merchant=merchant, code=1, customer_name="María López", customer_phone="+543446000111")
        OrderFactory(merchant=merchant, code=2, customer_name="Juan Pérez", customer_phone="+543446000222")
        client = APIClient()
        client.credentials(HTTP_X_MERCHANT_SLUG=merchant.slug)
        by_name = client.get("/api/v1/orders/", {"customer": "maría"}).json()
        assert [o["code"] for o in by_name] == [1]
        by_phone = client.get("/api/v1/orders/", {"customer": "6000222"}).json()
        assert [o["code"] for o in by_phone] == [2]

    def test_search_never_leaks_other_merchants(self):
        a = MerchantFactory()
        b = MerchantFactory()
        OrderFactory(merchant=a, code=1, customer_name="María López")
        OrderFactory(merchant=b, code=1, customer_name="María López")
        client = APIClient()
        client.credentials(HTTP_X_MERCHANT_SLUG=a.slug)
        data = client.get("/api/v1/orders/", {"customer": "maría"}).json()
        assert all(o["merchant_id"] == a.pk for o in data)


class TestPrintJobCreation:
    def test_transition_to_preparacion_creates_job_when_flag_on(self):
        merchant = MerchantFactory(print_tickets=True)
        admin = _admin(merchant)
        order = OrderFactory(merchant=merchant, state=Order.State.RECIBIDO)
        response = _transition(_login(admin.user.username), order, "PREPARACION")
        assert response.status_code == 200
        job = PrintJob.objects.filter(order=order).first()
        assert job is not None
        assert job.printed_at is None

    def test_no_job_when_flag_off(self):
        merchant = MerchantFactory()  # print_tickets defaults to False
        admin = _admin(merchant)
        order = OrderFactory(merchant=merchant, state=Order.State.RECIBIDO)
        response = _transition(_login(admin.user.username), order, "PREPARACION")
        assert response.status_code == 200
        assert not PrintJob.objects.filter(order=order).exists()

    def test_other_states_do_not_create_jobs(self):
        merchant = MerchantFactory(print_tickets=True)
        admin = _admin(merchant)
        order = OrderFactory(merchant=merchant, state=Order.State.PREPARACION)
        _transition(_login(admin.user.username), order, "FACTURACION")
        assert not PrintJob.objects.filter(order=order).exists()


class TestPrintJobQueue:
    def test_list_returns_unprinted_jobs_for_this_merchant(self):
        merchant = MerchantFactory(print_tickets=True)
        admin = _admin(merchant)
        job_pending = PrintJob.objects.create(
            merchant=merchant, order=OrderFactory(merchant=merchant)
        )
        PrintJob.objects.create(
            merchant=merchant,
            order=OrderFactory(merchant=merchant),
            printed_at=timezone.now(),
        )
        other = MerchantFactory()
        PrintJob.objects.create(merchant=other, order=OrderFactory(merchant=other))
        data = _login(admin.user.username).get("/api/v1/print-jobs/").json()
        assert [j["id"] for j in data] == [job_pending.id]
        assert data[0]["order"]["code"] is not None

    def test_mark_printed_and_reprint_count(self):
        merchant = MerchantFactory(print_tickets=True)
        admin = _admin(merchant)
        job = PrintJob.objects.create(
            merchant=merchant, order=OrderFactory(merchant=merchant)
        )
        client = _login(admin.user.username)
        first = client.post(f"/api/v1/print-jobs/{job.pk}/printed/")
        assert first.status_code == 200
        assert first.json()["printed_count"] == 1
        # Paper jam: print it again later, the count keeps track.
        second = client.post(f"/api/v1/print-jobs/{job.pk}/printed/")
        assert second.json()["printed_count"] == 2
        # Once printed it leaves the pending queue.
        remaining = client.get("/api/v1/print-jobs/").json()
        assert job.pk not in [j["id"] for j in remaining]
