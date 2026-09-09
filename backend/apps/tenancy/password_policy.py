import re
from datetime import timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError

MIN_LEN = 8
MAX_LEN = 12
ROTATION_DAYS = 180
RESET_TTL_MINUTES = 20

SESSION_CAPS = {
    "MASTER": 2,
    "INTERNAL": 3,
    "OPERATIVE": 2,
}


def validate_password_complexity(password):
    errors = []
    if not (MIN_LEN <= len(password) <= MAX_LEN):
        errors.append(f"password must be {MIN_LEN}-{MAX_LEN} characters.")
    if not re.search(r"[0-9]", password):
        errors.append("password needs at least one number.")
    if not re.search(r"[A-Z]", password):
        errors.append("password needs at least one uppercase letter.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("password needs at least one special character.")
    if errors:
        raise ValidationError({"password": errors})
    return password


def is_master_user(user, profile=None):
    if profile is None:
        profile = getattr(user, "platform_profile", None)
    if profile is None:
        return user.is_superuser
    if profile.is_platform and profile.role == "MASTER":
        return True
    return user.is_superuser


def password_expired(user, profile=None):
    """Masters never expire. Internals rotate every ROTATION_DAYS. Operatives never."""
    if profile is None:
        profile = getattr(user, "platform_profile", None)
    if profile is None:
        return False
    if profile.is_platform and profile.role == "MASTER":
        return False
    if not profile.is_platform:
        return False
    changed_at = profile.password_changed_at
    if changed_at is None:
        return True
    return timezone.now() - changed_at > timedelta(days=ROTATION_DAYS)


def session_cap_for(user, profile=None):
    if profile is None:
        profile = getattr(user, "platform_profile", None)
    if is_master_user(user, profile):
        return SESSION_CAPS["MASTER"]
    if profile is not None and profile.is_platform:
        return SESSION_CAPS["INTERNAL"]
    return SESSION_CAPS["OPERATIVE"]
