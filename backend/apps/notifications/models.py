from django.db import models

from apps.common.models import BaseModel


class NotificationType(models.TextChoices):
    NEW_ORDER = "NEW_ORDER", "Nuevo pedido"
    ORDER_STATE_CHANGE = "ORDER_STATE_CHANGE", "Cambio de estado"
    PAYMENT_PENDING = "PAYMENT_PENDING", "Pago pendiente"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Pago confirmado"
    SYSTEM = "SYSTEM", "Sistema"


class NotificationRecipientType(models.TextChoices):
    EMPLOYEE = "EMPLOYEE", "Empleado"
    CUSTOMER = "CUSTOMER", "Cliente"


class Notification(BaseModel):
    merchant = models.ForeignKey(
        "tenancy.Merchant", on_delete=models.CASCADE, related_name="notifications"
    )
    recipient_type = models.CharField(max_length=20, choices=NotificationRecipientType.choices)
    recipient_name = models.CharField(max_length=120, blank=True, default="")
    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="notifications", null=True, blank=True
    )
    message = models.TextField()
    type = models.CharField(max_length=30, choices=NotificationType.choices)
    is_read = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["merchant", "is_read"]),
            models.Index(fields=["merchant", "recipient_type"]),
        ]
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Notification {self.pk} [{self.type}] {self.is_read}"

    @property
    def summary(self) -> str:
        return f"{self.get_recipient_type_display()}: {self.message[:80]}"