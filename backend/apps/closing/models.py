from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel


class CashClosure(BaseModel):
    merchant = models.ForeignKey(
        "tenancy.Merchant", on_delete=models.CASCADE, related_name="cash_closures"
    )
    business_date = models.DateField()
    cashier = models.ForeignKey(
        "tenancy.Employee",
        on_delete=models.PROTECT,
        related_name="closures_closed",
    )
    total_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_billeteras = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_tarjetas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_entregados = models.PositiveIntegerField(default=0)
    total_rechazados = models.PositiveIntegerField(default=0)
    ticket_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "business_date"],
                name="uniq_closure_per_merchant_date",
            ),
        ]
        indexes = [
            models.Index(fields=["merchant", "business_date"]),
        ]
        ordering = ["-business_date"]

    def save(self, *args, **kwargs):
        if self.pk is not None and CashClosure.all_objects.filter(pk=self.pk).exists():
            raise ValidationError("CashClosure is immutable")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("CashClosure cannot be deleted")

    def __str__(self):
        return f"Closure {self.merchant_id} {self.business_date}"
