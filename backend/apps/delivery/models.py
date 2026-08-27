from django.db import models

from apps.common.models import BaseModel


class DeliveryConfig(BaseModel):
    class Modo(models.TextChoices):
        PROPIO = "PROPIO", "Propio"
        TERCERIZADO = "TERCERIZADO", "Tercerizado"

    class Cobro(models.TextChoices):
        EN_PEDIDO = "EN_PEDIDO", "En pedido"
        EN_ENTREGA = "EN_ENTREGA", "En entrega"

    class Calculo(models.TextChoices):
        POR_ZONA = "POR_ZONA", "Por zona"
        FIJO = "FIJO", "Fijo"
        GRATIS_MONTO = "GRATIS_MONTO", "Gratis sobre monto"
        POR_DISTANCIA = "POR_DISTANCIA", "Por distancia"

    merchant = models.OneToOneField(
        "tenancy.Merchant",
        on_delete=models.CASCADE,
        related_name="delivery_config",
    )
    modo = models.CharField(max_length=12, choices=Modo.choices, default=Modo.PROPIO)
    cobro = models.CharField(max_length=10, choices=Cobro.choices, default=Cobro.EN_PEDIDO)
    calculo = models.CharField(max_length=13, choices=Calculo.choices, default=Calculo.FIJO)
    flat_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    free_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    third_party_fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["merchant"]),
        ]

    def __str__(self):
        return f"DeliveryConfig {self.merchant_id} {self.modo}/{self.cobro}/{self.calculo}"


class Zone(BaseModel):
    merchant = models.ForeignKey(
        "tenancy.Merchant",
        on_delete=models.CASCADE,
        related_name="zones",
    )
    name = models.CharField(max_length=120)
    base_fee = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "name"],
                name="uniq_zone_name_per_merchant",
            ),
        ]
        indexes = [
            models.Index(fields=["merchant", "name"]),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.base_fee})"
