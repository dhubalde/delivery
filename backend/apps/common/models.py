from django.db import models
from django.utils import timezone


class BaseModelQuerySet(models.QuerySet):
    def live(self):
        return self.filter(deleted_at__isnull=True)

    def delete(self):
        return super().update(deleted_at=timezone.now())


class TenantQuerySet(BaseModelQuerySet):
    def for_merchant(self, merchant_id):
        if merchant_id is None:
            from apps.common.context import TenantIsolationError

            raise TenantIsolationError("merchant_id required (BR-X-01 fail-closed)")
        return self.filter(merchant_id=merchant_id)

    def for_current_tenant(self):
        from apps.common.context import require_tenant_merchant_id

        return self.for_merchant(require_tenant_merchant_id())


class LiveObjectsManager(models.Manager):
    """Default manager that hides soft-deleted rows (ADR-016)."""

    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db).live()


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = LiveObjectsManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])
        return 0, {}


class IdempotencyKey(models.Model):
    key = models.CharField(max_length=64)
    merchant = models.ForeignKey(
        "tenancy.Merchant", null=True, blank=True, on_delete=models.CASCADE, related_name="idempotency_keys"
    )
    endpoint = models.CharField(max_length=500)
    request_hash = models.CharField(max_length=64)
    response_snapshot = models.JSONField(default=dict, blank=True)
    status_code = models.PositiveSmallIntegerField(default=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["key", "endpoint"], name="uniq_idempotency_key_endpoint"),
        ]
        indexes = [
            models.Index(fields=["key", "endpoint"]),
            models.Index(fields=["merchant", "key"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.key} {self.endpoint}"
