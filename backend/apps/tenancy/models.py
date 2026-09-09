from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel


class Merchant(BaseModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    vertical = models.CharField(max_length=20, default="ICE_CREAM")
    is_active = models.BooleanField(default=True)
    logo = models.ImageField(upload_to="merchant_logos/", null=True, blank=True)
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    seat_limit = models.PositiveIntegerField(default=10)
    has_branches = models.BooleanField(default=False)

    @property
    def resolved_logo_url(self):
        if self.logo:
            try:
                return self.logo.url
            except Exception:
                pass
        return self.logo_url or ""

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
    fullname = models.CharField(max_length=120)
    cuil = models.CharField(max_length=13)
    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    display_name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["merchant", "is_active"]),
            models.Index(fields=["merchant", "fullname"]),
        ]
        ordering = ["fullname"]
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "cuil"],
                name="unique_employee_cuil_per_merchant",
            ),
        ]

    def clean(self):
        errors = {}
        if not self.fullname or not str(self.fullname).strip():
            errors["fullname"] = "fullname is required."
        if not self.cuil or not str(self.cuil).strip():
            errors["cuil"] = "cuil is required."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.fullname} ({self.merchant_id})"


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


class Branch(BaseModel):
    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, related_name="branches"
    )
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["merchant", "is_active"]),
        ]
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "name"],
                name="unique_branch_name_per_merchant",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.merchant_id})"


class PlatformUser(BaseModel):
    """System login profile: identity separate from the Employee HR record."""

    class Kind(models.TextChoices):
        PERSONAL = "PERSONAL", "Personal"
        STATION = "STATION", "Station"

    user = models.OneToOneField(
        "auth.User", on_delete=models.CASCADE, related_name="platform_profile"
    )
    # Null merchant = platform owner (master/internal), scoped via assigned_merchants.
    merchant = models.ForeignKey(
        Merchant, null=True, blank=True, on_delete=models.CASCADE, related_name="platform_users"
    )
    role = models.CharField(max_length=20)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.PERSONAL)
    sector = models.CharField(max_length=20, null=True, blank=True)
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.SET_NULL, related_name="platform_users"
    )
    assigned_merchants = models.ManyToManyField(Merchant, blank=True, related_name="assigned_staff")
    must_change_password = models.BooleanField(default=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["merchant", "role"]),
        ]

    @property
    def is_platform(self):
        return self.merchant_id is None

    def __str__(self):
        return f"{self.user} [{self.role}] ({self.merchant_id})"


class AuditEntry(models.Model):
    actor = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_entries"
    )
    action = models.CharField(max_length=120)
    merchant = models.ForeignKey(
        Merchant, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_entries"
    )
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "created_at"]),
        ]

    def __str__(self):
        return f"{self.created_at} {self.actor_id} {self.action} {self.merchant_id}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="password_reset_tokens"
    )
    token_hash = models.CharField(max_length=64, unique=True)
    created_by = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]

    @property
    def is_burned(self):
        return self.used_at is not None

    def __str__(self):
        return f"reset {self.user_id} used={self.is_burned}"


class SessionRecord(models.Model):
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="session_records"
    )
    jti = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["user", "revoked_at"]),
        ]

    @property
    def is_active(self):
        return self.revoked_at is None

    def __str__(self):
        return f"session {self.user_id} active={self.is_active}"
