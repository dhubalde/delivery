from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        SOFT_DELETE = "SOFT_DELETE", "Soft Delete"
        STATE_TRANSITION = "STATE_TRANSITION", "State Transition"
        PAYMENT = "PAYMENT", "Payment"
        CASH_MOVEMENT = "CASH_MOVEMENT", "Cash Movement"
        CLOSURE = "CLOSURE", "Closure"

    merchant = models.ForeignKey(
        "tenancy.Merchant", null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events"
    )
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events"
    )
    entity = models.CharField(max_length=80)
    entity_id = models.BigIntegerField()
    action = models.CharField(max_length=20, choices=Action.choices)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "entity", "entity_id"]),
            models.Index(fields=["merchant", "created_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("AuditEvent is append-only: updates not allowed")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditEvent is append-only: deletes not allowed")
