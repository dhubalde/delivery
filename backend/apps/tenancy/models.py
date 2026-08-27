from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel


class Merchant(BaseModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    vertical = models.CharField(max_length=20, default="ICE_CREAM")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Schedule(BaseModel):
    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, related_name="schedules"
    )
    weekday = models.SmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "weekday"],
                name="uniq_schedule_per_merchant_weekday",
            ),
            models.CheckConstraint(
                condition=models.Q(weekday__gte=0) & models.Q(weekday__lte=6),
                name="schedule_weekday_0_6",
            ),
        ]
        indexes = [
            models.Index(fields=["merchant", "weekday"]),
        ]

    def clean(self):
        errors = {}
        if self.weekday is not None and not 0 <= self.weekday <= 6:
            errors["weekday"] = "Weekday must be 0 (Mon) to 6 (Sun)."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.merchant} weekday={self.weekday}"


class TimeRange(models.Model):
    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="time_ranges"
    )
    opens_at = models.TimeField()
    closes_at = models.TimeField()

    class Meta:
        ordering = ["opens_at"]
        indexes = [
            models.Index(fields=["schedule", "opens_at"]),
        ]

    def clean(self):
        errors = {}
        if self.opens_at is not None and self.closes_at is not None:
            if self.opens_at >= self.closes_at:
                errors["closes_at"] = "closes_at must be after opens_at."
        if self.schedule_id and self.opens_at and self.closes_at:
            qs = TimeRange.objects.filter(schedule_id=self.schedule_id)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            for other in qs:
                if not (self.closes_at <= other.opens_at or self.opens_at >= other.closes_at):
                    errors["opens_at"] = "Time ranges must not overlap within the same day."
                    break
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.schedule} {self.opens_at}-{self.closes_at}"


class SpecialDate(BaseModel):
    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, related_name="special_dates"
    )
    date = models.DateField()
    is_closed = models.BooleanField(default=True)
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "date"],
                name="uniq_special_date_per_merchant",
            ),
        ]
        indexes = [
            models.Index(fields=["merchant", "date"]),
        ]

    def __str__(self):
        return f"{self.merchant} {self.date} closed={self.is_closed}"


class Employee(BaseModel):
    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, related_name="employees"
    )
    display_name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["merchant", "is_active"]),
            models.Index(fields=["merchant", "display_name"]),
        ]
        ordering = ["display_name"]

    def clean(self):
        errors = {}
        if not self.display_name or not str(self.display_name).strip():
            errors["display_name"] = "display_name is required."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.display_name} ({self.merchant_id})"


class EmployeeRole(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CAJERO = "CAJERO", "Cajero"
        PREPARADOR = "PREPARADOR", "Preparador"
        REPARTIDOR = "REPARTIDOR", "Repartidor"
        TOMA_PEDIDOS = "TOMA_PEDIDOS", "Toma Pedidos"

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="employee_roles"
    )
    role = models.CharField(max_length=13, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "role"],
                name="uniq_employee_role",
            ),
        ]
        indexes = [
            models.Index(fields=["employee", "role"]),
        ]
        ordering = ["role"]

    def clean(self):
        if self.role not in {c[0] for c in self.Role.choices}:
            raise ValidationError({"role": f"Invalid role {self.role}"})

    def __str__(self):
        return f"{self.employee_id} {self.role}"
