from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Branch, Employee, EmployeeRole, PlatformUser


class EmployeeSerializer(serializers.ModelSerializer):
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=EmployeeRole.Role.choices),
        required=False,
        allow_empty=True,
        write_only=True,
    )

    class Meta:
        model = Employee
        fields = [
            "id",
            "fullname",
            "cuil",
            "address",
            "city",
            "is_active",
            "merchant_id",
            "roles",
        ]
        read_only_fields = ["id", "merchant_id"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data["roles"] = list(
                instance.employee_roles.values_list("role", flat=True)
            )
        except Exception:
            data["roles"] = []
        return data

    def create(self, validated_data):
        roles = validated_data.pop("roles", [])
        employee = super().create(validated_data)
        if roles:
            EmployeeRole.objects.bulk_create(
                [EmployeeRole(employee=employee, role=r) for r in roles]
            )
        return employee

    def update(self, instance, validated_data):
        roles = validated_data.pop("roles", None)
        employee = super().update(instance, validated_data)
        if roles is not None:
            employee.employee_roles.all().delete()
            if roles:
                EmployeeRole.objects.bulk_create(
                    [EmployeeRole(employee=employee, role=r) for r in roles]
                )
        return employee


OPERATIVE_ROLES = [c[0] for c in EmployeeRole.Role.choices]

INTERNAL_ROLES = ["MASTER", "ADMIN", "DEV", "TECNICO", "JUNIOR"]


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "address", "phone", "is_active", "merchant_id"]
        read_only_fields = ["id", "merchant_id"]

SEAT_TIERS = [10, 20, 30]


class CompanyOnboardingSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    slug = serializers.SlugField(max_length=120)
    logo_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    seat_limit = serializers.ChoiceField(choices=SEAT_TIERS, default=10)
    has_branches = serializers.BooleanField(default=False)
    admin_username = serializers.CharField(max_length=150)
    admin_password = serializers.CharField(write_only=True, allow_blank=False)

    def validate_admin_username(self, value):
        if User.objects.filter(username=value).exists():
            raise ValidationError({"admin_username": "username already taken."})
        return value

    def validate_admin_password(self, value):
        from .password_policy import validate_password_complexity

        validate_password_complexity(value)
        return value


class InternalUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    assigned_merchants = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = PlatformUser
        fields = [
            "id",
            "username",
            "password",
            "role",
            "assigned_merchants",
            "is_active",
            "must_change_password",
        ]
        read_only_fields = ["id", "must_change_password"]

    def validate_role(self, value):
        if value not in INTERNAL_ROLES:
            raise ValidationError(f"role must be one of {INTERNAL_ROLES}.")
        return value

    def validate_password(self, value):
        from .password_policy import validate_password_complexity

        validate_password_complexity(value)
        return value

    def _resolve_merchants(self, ids):
        from .models import Merchant

        merchants = list(Merchant.objects.filter(pk__in=ids))
        if len(merchants) != len(set(ids)):
            raise ValidationError({"assigned_merchants": "Unknown merchant id."})
        return merchants

    def create(self, validated_data):
        username = validated_data.pop("username", None)
        password = validated_data.pop("password", None)
        merchant_ids = validated_data.pop("assigned_merchants", [])
        is_active = validated_data.pop("is_active", True)
        if not username:
            raise ValidationError({"username": "username is required."})
        if not password:
            raise ValidationError({"password": "password is required."})
        if User.objects.filter(username=username).exists():
            raise ValidationError({"username": "username already taken."})
        with transaction.atomic():
            user = User(username=username, is_active=is_active)
            user.set_password(password)
            user.save()
            profile = PlatformUser.objects.create(
                user=user,
                merchant=None,
                must_change_password=True,
                **validated_data,
            )
            if merchant_ids:
                profile.assigned_merchants.set(self._resolve_merchants(merchant_ids))
        return profile

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("username", None)
        merchant_ids = validated_data.pop("assigned_merchants", None)
        is_active = validated_data.pop("is_active", None)
        with transaction.atomic():
            profile = super().update(instance, validated_data)
            if password:
                profile.user.set_password(password)
                profile.user.save(update_fields=["password"])
                profile.must_change_password = True
                profile.save(update_fields=["must_change_password"])
            if is_active is not None and profile.user.is_active != is_active:
                profile.user.is_active = is_active
                profile.user.save(update_fields=["is_active"])
            if merchant_ids is not None:
                profile.assigned_merchants.set(self._resolve_merchants(merchant_ids))
        return profile

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["username"] = instance.user.username
        data["is_active"] = instance.user.is_active
        data["assigned_merchants"] = [
            {"id": m.pk, "name": m.name, "slug": m.slug}
            for m in instance.assigned_merchants.all()
        ]
        return data


class PlatformUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    branch_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    branch = serializers.SerializerMethodField(read_only=True)
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = PlatformUser
        fields = [
            "id",
            "username",
            "password",
            "role",
            "kind",
            "sector",
            "branch_id",
            "branch",
            "is_active",
            "must_change_password",
            "merchant_id",
        ]
        read_only_fields = ["id", "must_change_password", "merchant_id"]
        extra_kwargs = {
            "role": {"required": False},
            "kind": {"required": False},
        }

    def get_branch(self, instance):
        if instance.branch_id is None:
            return None
        return {"id": instance.branch_id, "name": instance.branch.name}

    def validate_role(self, value):
        if value not in OPERATIVE_ROLES:
            raise ValidationError(f"role must be one of {OPERATIVE_ROLES}.")
        return value

    def validate_password(self, value):
        from .password_policy import validate_password_complexity

        validate_password_complexity(value)
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        mid = getattr(request, "tenant_merchant_id", None) if request else None
        branch_id = attrs.get("branch_id")
        if branch_id is not None:
            try:
                branch = Branch.objects.for_merchant(mid).get(pk=branch_id)
            except Branch.DoesNotExist:
                raise ValidationError({"branch_id": "Branch not found in this merchant."})
            attrs["branch"] = branch
        attrs.pop("branch_id", None)
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        mid = getattr(request, "tenant_merchant_id", None)
        username = validated_data.pop("username", None)
        password = validated_data.pop("password", None)
        if not username:
            raise ValidationError({"username": "username is required."})
        if not password:
            raise ValidationError({"password": "password is required."})
        if User.objects.filter(username=username).exists():
            raise ValidationError({"username": "username already taken."})
        is_active = validated_data.pop("is_active", True)
        with transaction.atomic():
            user = User(username=username, is_active=is_active)
            user.set_password(password)
            user.save()
            profile = PlatformUser.objects.create(
                user=user,
                merchant_id=mid,
                must_change_password=True,
                **validated_data,
            )
        return profile

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("username", None)
        is_active = validated_data.pop("is_active", None)
        with transaction.atomic():
            profile = super().update(instance, validated_data)
            if password:
                profile.user.set_password(password)
                profile.user.save(update_fields=["password"])
                profile.must_change_password = True
                profile.save(update_fields=["must_change_password"])
            if is_active is not None and profile.user.is_active != is_active:
                profile.user.is_active = is_active
                profile.user.save(update_fields=["is_active"])
        return profile

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["username"] = instance.user.username
        data["is_active"] = instance.user.is_active
        return data