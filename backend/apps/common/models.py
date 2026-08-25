from django.db import models
from django.utils import timezone


class BaseModelQuerySet(models.QuerySet):
    def live(self):
        return self.filter(deleted_at__isnull=True)

    def delete(self):
        return super().update(deleted_at=timezone.now())


class TenantQuerySet(BaseModelQuerySet):
    def for_merchant(self, merchant_id):
        return self.filter(merchant_id=merchant_id)


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
