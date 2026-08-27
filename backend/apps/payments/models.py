from django.db import models

from apps.common.models import BaseModel


class Payment(BaseModel):
    class Method(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        BILLETERA = "BILLETERA", "Billetera"
        TARJETA = "TARJETA", "Tarjeta"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REJECTED = "REJECTED", "Rejected"

    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="payments"
    )
    method = models.CharField(max_length=10, choices=Method.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    gateway_ref = models.CharField(max_length=120, null=True, blank=True)
    collected_by = models.CharField(max_length=120, null=True, blank=True)
    collected_by_employee = models.ForeignKey(
        "tenancy.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="collected_payments",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["status", "method"]),
        ]
        ordering = ["-created_at"]

    @property
    def is_blinking(self):
        return self.method == self.Method.EFECTIVO and self.status == self.Status.PENDING

    def __str__(self):
        return f"{self.method} {self.amount} {self.status}"
