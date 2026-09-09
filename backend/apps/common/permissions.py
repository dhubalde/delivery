from rest_framework import permissions

from apps.tenancy.models import PlatformUser


def get_profile(user):
    if not user or not user.is_authenticated:
        return None
    try:
        return user.platform_profile
    except PlatformUser.DoesNotExist:
        return None


class IsAdmin(permissions.BasePermission):
    """Active platform user with ADMIN role. Tenant scope comes from the JWT-bound request."""

    message = "Solo ADMIN."

    def has_permission(self, request, view):
        profile = get_profile(request.user)
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and profile is not None
            and profile.role == "ADMIN"
        )


class IsMaster(permissions.BasePermission):
    """Platform owner: superuser without profile, or profile with null merchant."""

    message = "Solo plataforma."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        profile = get_profile(user)
        if profile is None:
            return user.is_superuser
        return profile.is_platform


class HasAssignedCompany(permissions.BasePermission):
    """Internal staff may only act on assigned companies. Masters bypass."""

    message = "Empresa no asignada."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        profile = get_profile(user)
        if profile is None:
            return user.is_superuser
        if user.is_superuser or profile.role == "MASTER":
            return True
        return True  # object-level check below narrows scope

    def has_object_permission(self, request, view, obj):
        user = request.user
        profile = get_profile(user)
        if profile is None:
            return user.is_superuser
        if user.is_superuser or profile.role == "MASTER":
            return True
        merchant_id = getattr(obj, "merchant_id", None) or getattr(obj, "pk", None)
        assigned = set(profile.assigned_merchants.values_list("pk", flat=True))
        if profile.merchant_id is not None:
            assigned.add(profile.merchant_id)
        return merchant_id in assigned
