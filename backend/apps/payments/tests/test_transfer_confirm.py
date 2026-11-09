"""Red: operator confirms an intentionally-pending transfer payment (manual orders).

Rules under test:
- POST /api/v1/payments/<id>/confirm-transfer (staff JWT) confirms a PENDING TRANSFER payment.
- Only same-merchant staff may confirm (TENANT_MISMATCH → 403).
- Non-TRANSFER methods cannot be confirmed through this flow.
- Unauthenticated requests → 401.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.tests.factories import MerchantFactory
from apps.orders.models import Order
from apps.orders.tests.factories import OrderFactory
from apps.payments.models import Payment
from apps.payments.tests.factories import PaymentFactory
from apps.tenancy.models import PlatformUser

pytestmark = pytest.mark.django_db


def _staff_client(user, merchant):
    refresh = RefreshToken.for_user(user)
    refresh["merchant_id"] = merchant.pk
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


def _admin_user(merchant, username="admin_conf", role="ADMIN"):
    user = User.objects.create_user(username=username, password="pass")
    profile = PlatformUser.objects.create(user=user, merchant=merchant, role=role)
    PlatformUser.objects.filter(pk=profile.pk).update(must_change_password=False)
    return user


def _transfer_order(merchant):
    order = OrderFactory(merchant=merchant, state=Order.State.RECIBIDO)
    return PaymentFactory(order=order, method=Payment.Method.TRANSFER, status=Payment.Status.PENDING)


class TestConfirmTransferEndpoint:
    URL = "/api/v1/payments/{pk}/confirm-transfer"

    def test_confirms_pending_transfer(self):
        merchant = MerchantFactory(slug="transacme")
        payment = _transfer_order(merchant)
        client = _staff_client(_admin_user(merchant), merchant)
        resp = client.post(self.URL.format(pk=payment.pk), format="json")
        assert resp.status_code == 200, resp.content
        payment.refresh_from_db()
        assert payment.status == Payment.Status.CONFIRMED
        assert payment.confirmed_at is not None

    def test_other_merchant_staff_forbidden(self):
        acme = MerchantFactory(slug="acmeconf")
        other = MerchantFactory(slug="otherconf")
        payment = _transfer_order(acme)
        client = _staff_client(_admin_user(other, username="other_cajero", role="CAJERO"), other)
        resp = client.post(self.URL.format(pk=payment.pk), format="json")
        assert resp.status_code == 403, resp.content
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PENDING

    def test_non_transfer_method_rejected(self):
        merchant = MerchantFactory(slug="noefect")
        payment = PaymentFactory(
            order=OrderFactory(merchant=merchant, state=Order.State.RECIBIDO),
            method=Payment.Method.EFECTIVO,
            status=Payment.Status.PENDING,
        )
        client = _staff_client(_admin_user(merchant), merchant)
        resp = client.post(self.URL.format(pk=payment.pk), format="json")
        assert resp.status_code == 409, resp.content
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PENDING

    def test_already_confirmed_rejected(self):
        merchant = MerchantFactory(slug="alrdycf")
        payment = _transfer_order(merchant)
        PaymentService = _service()
        PaymentService.confirm_transfer(payment.pk)
        client = _staff_client(_admin_user(merchant), merchant)
        resp = client.post(self.URL.format(pk=payment.pk), format="json")
        assert resp.status_code == 409, resp.content

    def test_unauthenticated_401(self):
        merchant = MerchantFactory(slug="anonconf")
        payment = _transfer_order(merchant)
        client = APIClient()
        resp = client.post(self.URL.format(pk=payment.pk), format="json")
        assert resp.status_code == 401, resp.content


def _service():
    from apps.payments.services import PaymentService

    return PaymentService
