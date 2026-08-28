import hashlib
import json

import pytest
from django.db import IntegrityError
from django.test import RequestFactory

from apps.catalog.tests.factories import MerchantFactory, ProductFactory
from apps.common.context import TenantIsolationError, get_tenant_merchant_id, set_tenant_merchant_id
from apps.common.middleware import IdempotencyMiddleware, TenantContextMiddleware
from apps.common.models import IdempotencyKey
from apps.orders.tests.factories import OrderFactory
from apps.payments.models import Payment
from apps.payments.tests.factories import PaymentFactory
from apps.tenancy.tests.factories import EmployeeFactory


pytestmark = pytest.mark.django_db


class TestTenantIsolationBrX01:
    def test_for_merchant_scopes_orders(self):
        m1 = MerchantFactory()
        m2 = MerchantFactory()
        o1 = OrderFactory(merchant=m1)
        o2 = OrderFactory(merchant=m2)
        from apps.orders.models import Order

        assert list(Order.objects.for_merchant(m1.pk)) == [o1]
        assert o2 not in Order.objects.for_merchant(m1.pk)

    def test_for_merchant_scopes_products(self):
        m1 = MerchantFactory()
        m2 = MerchantFactory()
        p1 = ProductFactory(merchant=m1, category__merchant=m1)
        p2 = ProductFactory(merchant=m2, category__merchant=m2)
        from apps.catalog.models import Product

        assert p1 in Product.objects.for_merchant(m1.pk)
        assert p2 not in Product.objects.for_merchant(m1.pk)

    def test_for_merchant_requires_merchant_id(self):
        from apps.orders.models import Order

        with pytest.raises(TenantIsolationError):
            list(Order.objects.for_merchant(None))

    def test_for_current_tenant_fail_closed(self):
        set_tenant_merchant_id(None)
        from apps.orders.models import Order

        with pytest.raises(TenantIsolationError):
            list(Order.objects.for_current_tenant())

    def test_for_current_tenant_filters_when_set(self):
        m = MerchantFactory()
        o = OrderFactory(merchant=m)
        other = OrderFactory(merchant=MerchantFactory())
        set_tenant_merchant_id(m.pk)
        try:
            from apps.orders.models import Order

            qs = Order.objects.for_current_tenant()
            assert o in qs
            assert other not in qs
        finally:
            set_tenant_merchant_id(None)

    def test_middleware_sets_from_header(self):
        m = MerchantFactory()
        factory = RequestFactory()
        req = factory.get("/api/v1/orders", HTTP_X_MERCHANT_ID=str(m.pk))
        TenantContextMiddleware(lambda r: r).process_request(req)
        assert req.tenant_merchant_id == m.pk
        assert get_tenant_merchant_id() == m.pk
        set_tenant_merchant_id(None)

    def test_middleware_resolves_slug(self):
        m = MerchantFactory(slug="helado-test-slug")
        factory = RequestFactory()
        req = factory.get(f"/api/public/{m.slug}/menu")
        TenantContextMiddleware(lambda r: r).process_request(req)
        assert req.tenant_merchant_id == m.pk
        set_tenant_merchant_id(None)


class TestIdempotencyBrX02:
    def test_unique_constraint(self):
        m = MerchantFactory()
        IdempotencyKey.objects.create(key="k1", endpoint="/api/orders", request_hash="abc", response_snapshot={}, status_code=201)
        with pytest.raises(IntegrityError):
            IdempotencyKey.objects.create(key="k1", endpoint="/api/orders", request_hash="abc", response_snapshot={}, status_code=201)

    def test_middleware_replay_same_hash(self):
        m = MerchantFactory()
        body = json.dumps({"total": 100}).encode()
        h = hashlib.sha256(body).hexdigest()
        IdempotencyKey.objects.create(
            key="dup-key", endpoint="/api/orders", merchant=m, request_hash=h,
            response_snapshot={"body": {"id": 1}, "content_type": "application/json"}, status_code=201,
        )
        factory = RequestFactory()
        req = factory.post("/api/orders", data=body, content_type="application/json", HTTP_IDEMPOTENCY_KEY="dup-key")
        req.META["HTTP_IDEMPOTENCY_KEY"] = "dup-key"
        middleware = IdempotencyMiddleware(lambda r: None)
        resp = middleware.process_request(req)
        assert resp is not None
        assert resp.status_code == 201
        assert resp["Idempotency-Replayed"] == "true"

    def test_middleware_mismatch_hash_returns_409(self):
        m = MerchantFactory()
        IdempotencyKey.objects.create(
            key="k-conflict", endpoint="/api/orders", merchant=m, request_hash="original",
            response_snapshot={"body": {}}, status_code=201,
        )
        factory = RequestFactory()
        req = factory.post("/api/orders", data=b'{"different": true}', content_type="application/json", HTTP_IDEMPOTENCY_KEY="k-conflict")
        middleware = IdempotencyMiddleware(lambda r: None)
        resp = middleware.process_request(req)
        assert resp is not None
        assert resp.status_code == 409

    def test_no_key_passthrough(self):
        factory = RequestFactory()
        req = factory.post("/api/orders", data=b"{}", content_type="application/json")
        middleware = IdempotencyMiddleware(lambda r: None)
        assert middleware.process_request(req) is None

    def test_response_stored_after_request(self):
        factory = RequestFactory()
        body = b'{"x": 1}'
        req = factory.post("/api/orders", data=body, content_type="application/json", HTTP_IDEMPOTENCY_KEY="new-key-store")
        middleware = IdempotencyMiddleware(lambda r: None)
        assert middleware.process_request(req) is None
        from django.http import JsonResponse

        resp = JsonResponse({"created": True}, status=201)
        middleware.process_response(req, resp)
        assert IdempotencyKey.objects.filter(key="new-key-store", endpoint="/api/orders").exists()


class TestSoftDeleteBrX04:
    def test_soft_delete_hides_from_default_manager(self):
        p = ProductFactory()
        pid = p.pk
        p.delete()
        from apps.catalog.models import Product

        assert not Product.objects.filter(pk=pid).exists()
        assert Product.all_objects.filter(pk=pid).exists()
        assert Product.all_objects.get(pk=pid).deleted_at is not None

    def test_soft_delete_order(self):
        o = OrderFactory()
        o.delete()
        from apps.orders.models import Order

        assert not Order.objects.filter(pk=o.pk).exists()
        assert Order.all_objects.filter(pk=o.pk).exists()

    def test_soft_delete_payment(self):
        pay = PaymentFactory()
        pay.delete()
        assert not Payment.objects.filter(pk=pay.pk).exists()
        assert Payment.all_objects.filter(pk=pay.pk).exists()

    def test_soft_delete_employee(self):
        emp = EmployeeFactory()
        emp.delete()
        from apps.tenancy.models import Employee

        assert not Employee.objects.filter(pk=emp.pk).exists()
        assert Employee.all_objects.filter(pk=emp.pk).exists()

    def test_bulk_queryset_delete_is_soft(self):
        m = MerchantFactory()
        OrderFactory(merchant=m)
        OrderFactory(merchant=m)
        from apps.orders.models import Order

        Order.objects.for_merchant(m.pk).delete()
        assert Order.objects.for_merchant(m.pk).count() == 0
        assert Order.all_objects.filter(merchant=m).count() == 2

    def test_deleted_payment_excluded_from_default(self):
        pay = PaymentFactory(status=Payment.Status.CONFIRMED)
        pay.delete()
        assert Payment.objects.filter(status=Payment.Status.CONFIRMED).count() == 0
