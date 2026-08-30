from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel


class Category(BaseModel):
    merchant = models.ForeignKey(
        "tenancy.Merchant", on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=120)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "name"], name="uniq_category_name_per_merchant"
            ),
        ]
        indexes = [
            models.Index(fields=["merchant", "is_active", "position"]),
        ]

    def __str__(self):
        return self.name


class Product(BaseModel):
    class ProductType(models.TextChoices):
        POTE = "POTE", "Pote"
        UNIT = "UNIT", "Unit"

    class PoteSize(models.TextChoices):
        KG_1 = "KG_1", "1kg"
        KG_HALF = "KG_HALF", "1/2kg"
        KG_QUARTER = "KG_QUARTER", "1/4kg"

    merchant = models.ForeignKey(
        "tenancy.Merchant", on_delete=models.CASCADE, related_name="products"
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_type = models.CharField(max_length=4, choices=ProductType.choices)
    pote_size = models.CharField(
        max_length=10, choices=PoteSize.choices, null=True, blank=True
    )
    min_flavors = models.SmallIntegerField(null=True, blank=True)
    max_flavors = models.SmallIntegerField(null=True, blank=True)
    image_url = models.URLField(blank=True, null=True, max_length=500)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(product_type="POTE")
                    | models.Q(pote_size__isnull=True)
                ),
                name="unit_has_no_pote_size",
            ),
        ]
        indexes = [
            models.Index(fields=["merchant", "category", "is_active"]),
        ]

    def clean(self):
        errors = {}
        if self.category_id is None:
            errors["category"] = "A product must belong to exactly one category."
        if self.product_type == self.ProductType.POTE:
            if self.pote_size is None and (self.min_flavors is not None or self.max_flavors is not None):
                errors["pote_size"] = "Pote products with flavors require size."
        if self.product_type == self.ProductType.UNIT:
            if self.pote_size is not None:
                errors["product_type"] = "Unit products must not define pote_size."
        if self.min_flavors is not None or self.max_flavors is not None:
            if self.min_flavors is None or self.max_flavors is None:
                errors["min_flavors"] = "Both min_flavors and max_flavors must be set or both null."
            elif not (1 <= self.min_flavors <= self.max_flavors <= 4):
                errors["min_flavors"] = "Require 1 <= min <= max <= 4."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name


class Flavor(BaseModel):
    merchant = models.ForeignKey(
        "tenancy.Merchant", on_delete=models.CASCADE, related_name="flavors"
    )
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="flavors"
    )
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "name"], name="uniq_flavor_name_per_merchant"
            ),
        ]

    def __str__(self):
        return self.name


class ProductFlavor(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="suggested_flavors"
    )
    flavor = models.ForeignKey(
        Flavor, on_delete=models.CASCADE, related_name="suggested_products"
    )
    merchant = models.ForeignKey(
        "tenancy.Merchant", on_delete=models.CASCADE, editable=False
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "flavor"], name="uniq_product_flavor"
            ),
        ]

    def clean(self):
        if (
            self.product_id
            and self.flavor_id
            and self.flavor.merchant_id != self.product.merchant_id
        ):
            raise ValidationError(
                "Flavor must belong to the same merchant as the product."
            )

    def save(self, *args, **kwargs):
        if self.product_id:
            self.merchant_id = self.product.merchant_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} -> {self.flavor}"
