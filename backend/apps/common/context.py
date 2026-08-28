from contextvars import ContextVar

tenant_merchant_id: ContextVar[int | None] = ContextVar("tenant_merchant_id", default=None)


class TenantIsolationError(RuntimeError):
    pass


def set_tenant_merchant_id(merchant_id: int | None):
    tenant_merchant_id.set(merchant_id)


def get_tenant_merchant_id() -> int | None:
    return tenant_merchant_id.get()


def require_tenant_merchant_id() -> int:
    mid = tenant_merchant_id.get()
    if mid is None:
        raise TenantIsolationError("Tenant context required but not set (BR-X-01 fail-closed)")
    return mid
