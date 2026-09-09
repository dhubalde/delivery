from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.tenancy.models import PlatformUser, SessionRecord
from apps.tenancy.password_policy import password_expired, session_cap_for


def _claims_for_user(user: User) -> dict:
    try:
        profile = user.platform_profile
    except PlatformUser.DoesNotExist:
        profile = None
    if profile is None:
        # Superusers without a profile act as platform masters.
        if user.is_superuser:
            return {"merchant_id": None, "role": "MASTER", "kind": "PERSONAL"}
        return {"merchant_id": None, "role": "", "kind": "PERSONAL"}
    return {
        "merchant_id": profile.merchant_id,
        "role": profile.role,
        "kind": profile.kind,
        "branch_id": profile.branch_id,
    }


class WorkZoneTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        for key, value in _claims_for_user(user).items():
            token[key] = value
        return token

    def validate(self, attrs):
        from apps.tenancy.models import PlatformUser

        data = super().validate(attrs)
        try:
            profile = self.user.platform_profile
        except PlatformUser.DoesNotExist:
            profile = None
        if password_expired(self.user, profile):
            raise AuthenticationFailed(
                {"password": "Password expired, change required."}, code="password_expired"
            )
        _register_session(self.user, data["access"])
        claims = _claims_for_user(self.user)
        data["user"] = {
            "username": self.user.username,
            "role": claims["role"],
            "merchant_id": claims["merchant_id"],
            "kind": claims.get("kind"),
            "sector": getattr(profile, "sector", None),
            "must_change_password": getattr(profile, "must_change_password", False),
        }
        return data


def _register_session(user, access_token):
    from rest_framework_simplejwt.tokens import AccessToken

    jti = AccessToken(access_token).get("jti")
    cap = session_cap_for(user)
    active = list(
        SessionRecord.objects.filter(user=user, revoked_at__isnull=True).order_by("created_at")
    )
    overflow = len(active) - cap + 1
    if overflow > 0:
        for record in active[:overflow]:
            record.revoked_at = timezone.now()
            record.save(update_fields=["revoked_at"])
    SessionRecord.objects.create(user=user, jti=jti)


class WorkZoneTokenView(TokenObtainPairView):
    serializer_class = WorkZoneTokenSerializer
