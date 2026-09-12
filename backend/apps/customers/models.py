from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from apps.common.models import BaseModel


class Customer(BaseModel):
    merchant = models.ForeignKey(
        "tenancy.Merchant", on_delete=models.CASCADE, related_name="customers"
    )
    phone = models.CharField(max_length=40)
    name = models.CharField(max_length=120)
    password_hash = models.CharField(max_length=128)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "phone"],
                name="uniq_customer_phone_per_merchant",
            ),
        ]
        indexes = [
            models.Index(fields=["merchant", "phone"]),
        ]
        ordering = ["name"]

    def set_password(self, raw_password: str) -> None:
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return f"{self.name} ({self.phone}) [{self.merchant_id}]"
