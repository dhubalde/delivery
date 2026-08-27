from django.db import models

from apps.common.models import BaseModel


class Order(BaseModel):
    class State(models.TextChoices):
        RECIBIDO = "RECIBIDO", "Recibido"
        PREPARACION = "PREPARACION", "Preparacion"
        FACTURACION = "FACTURACION", "Facturacion"
        LOGISTICA = "LOGISTICA", "Logistica"
        ENTREGADO = "ENTREGADO", "Entregado"
        CANCELADO = "CANCELADO", "Cancelado"

    class Fulfillment(models.TextChoices):
        DELIVERY = "DELIVERY", "Delivery"
        PICKUP = "PICKUP", "Pickup"

    merchant = models.ForeignKey(
        "tenancy.Merchant", on_delete=models.CASCADE, related_name="orders"
    )
    code = models.PositiveIntegerField()
    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=40, blank=True)
    fulfillment = models.CharField(max_length=8, choices=Fulfillment.choices)
    state = models.CharField(
        max_length=12, choices=State.choices, default=State.RECIBIDO
    )
    business_date = models.DateField()
    address = models.TextField(blank=True)
    items_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cash_declared = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "business_date", "code"],
                name="uniq_order_code_per_merchant_day",
            ),
        ]
        indexes = [
            models.Index(fields=["merchant", "state", "business_date"]),
        ]
        ordering = ["-business_date", "-code"]

    def __str__(self):
        return f"Order {self.code} {self.state}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="order_items"
    )
    product_name = models.CharField(max_length=160)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    flavors = models.JSONField(default=list, blank=True)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
