import datetime

from django.db import transaction
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.common.permissions import IsAdmin, IsMaster
from apps.tenancy.models import AuditEntry, Merchant, Employee, PlatformUser, Schedule, SpecialDate, TimeRange
from apps.tenancy.models import Branch
from apps.tenancy.serializers import (
    BranchSerializer,
    CompanyOnboardingSerializer,
    EmployeeSerializer,
    InternalUserSerializer,
    PlatformUserSerializer,
)


def _requester_profile(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None
    try:
        return user.platform_profile
    except PlatformUser.DoesNotExist:
        return None


def _is_full_master(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not user.is_active:
        return False
    profile = _requester_profile(request)
    if profile is None:
        return user.is_superuser
    return profile.is_platform and profile.role == "MASTER"


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict."
    default_code = "conflict"


def _resolve_merchant_id(request):
    mid = getattr(request, "tenant_merchant_id", None)
    if mid is not None:
        return mid
    slug = request.query_params.get("merchant_slug") or request.headers.get("X-Merchant-Slug") or request.META.get("HTTP_X_MERCHANT_SLUG")
    if slug:
        try:
            from apps.tenancy.models import Merchant

            m = Merchant.objects.filter(slug=slug).first()
            if m:
                return m.pk
            m = Merchant.all_objects.filter(slug=slug).first()
            if m:
                return m.pk
        except Exception:
            pass
    raw = request.query_params.get("merchant_id") or request.headers.get("X-Merchant-Id") or request.META.get("HTTP_X_MERCHANT_ID")
    if raw:
        try:
            return int(raw)
        except (ValueError, TypeError):
            return None
    return None


def _require_merchant_id(request):
    mid = _resolve_merchant_id(request)
    if mid is None:
        raise ValidationError({"merchant": "merchant context required (merchant_slug, merchant_id or X-Merchant-Slug header)"})
    return mid


def _parse_time(value, field_name):
    if not isinstance(value, str):
        raise ValidationError({field_name: "Time must be HH:MM string."})
    try:
        return datetime.datetime.strptime(value, "%H:%M").time()
    except ValueError:
        raise ValidationError({field_name: "Invalid time format, expected HH:MM."})


def _validate_ranges(raw_ranges):
    if raw_ranges is None:
        raise ValidationError({"ranges": "ranges is required."})
    if not isinstance(raw_ranges, list):
        raise ValidationError({"ranges": "ranges must be a list."})
    parsed = []
    for idx, item in enumerate(raw_ranges):
        if not isinstance(item, dict):
            raise ValidationError({"ranges": f"ranges[{idx}] must be an object."})
        opens_raw = item.get("opens_at")
        closes_raw = item.get("closes_at")
        if opens_raw is None or closes_raw is None:
            raise ValidationError({"ranges": f"ranges[{idx}] requires opens_at and closes_at."})
        opens = _parse_time(opens_raw, "opens_at")
        closes = _parse_time(closes_raw, "closes_at")
        if opens >= closes:
            raise ValidationError({"closes_at": "closes_at must be after opens_at."})
        parsed.append((opens, closes))
    parsed.sort(key=lambda x: x[0])
    for i in range(1, len(parsed)):
        prev_close = parsed[i - 1][1]
        curr_open = parsed[i][0]
        curr_close = parsed[i][1]
        if curr_open < prev_close:
            raise ValidationError({"opens_at": "Time ranges must not overlap within the same day."})
    return parsed


def _serialize_schedule(schedule):
    ranges = list(schedule.time_ranges.order_by("opens_at").values("opens_at", "closes_at"))
    out = []
    for r in ranges:
        oa = r["opens_at"]
        ca = r["closes_at"]
        if hasattr(oa, "strftime"):
            oa = oa.strftime("%H:%M")
        else:
            oa = str(oa)[:5]
        if hasattr(ca, "strftime"):
            ca = ca.strftime("%H:%M")
        else:
            ca = str(ca)[:5]
        out.append({"opens_at": oa, "closes_at": ca})
    return {"id": schedule.pk, "weekday": schedule.weekday, "time_ranges": out}


class ScheduleListUpsertView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        mid = _require_merchant_id(request)
        qs = Schedule.objects.for_merchant(mid).prefetch_related("time_ranges").order_by("weekday")
        data = [_serialize_schedule(s) for s in qs]
        return Response(data)

    def put(self, request):
        mid = _require_merchant_id(request)
        weekday = request.data.get("weekday")
        ranges = request.data.get("ranges")
        if weekday is None:
            raise ValidationError({"weekday": "weekday is required."})
        try:
            weekday = int(weekday)
        except (TypeError, ValueError):
            raise ValidationError({"weekday": "weekday must be integer 0-6."})
        if not 0 <= weekday <= 6:
            raise ValidationError({"weekday": "Weekday must be 0 (Mon) to 6 (Sun)."})
        parsed = _validate_ranges(ranges)
        with transaction.atomic():
            schedule, _ = Schedule.objects.get_or_create(merchant_id=mid, weekday=weekday)
            schedule.time_ranges.all().delete()
            objs = [TimeRange(schedule=schedule, opens_at=o, closes_at=c) for o, c in parsed]
            if objs:
                TimeRange.objects.bulk_create(objs)
        schedule.refresh_from_db()
        return Response(_serialize_schedule(schedule), status=status.HTTP_200_OK)


class ScheduleDeleteView(APIView):
    permission_classes = [permissions.AllowAny]

    def delete(self, request, pk):
        mid = _require_merchant_id(request)
        try:
            schedule = Schedule.objects.for_merchant(mid).get(pk=pk)
        except Schedule.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        Schedule.all_objects.filter(pk=schedule.pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SpecialDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialDate
        fields = ["id", "date", "is_closed", "reason"]
        read_only_fields = ["id"]


class SpecialDateListCreateView(generics.ListCreateAPIView):
    serializer_class = SpecialDateSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        return SpecialDate.objects.for_merchant(mid).order_by("date")

    def perform_create(self, serializer):
        mid = _require_merchant_id(self.request)
        try:
            serializer.save(merchant_id=mid)
        except Exception as e:
            from django.db import IntegrityError

            if isinstance(e, IntegrityError):
                raise ValidationError({"date": "Special date already exists for this merchant."})
            raise


class SpecialDateDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SpecialDateSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        return SpecialDate.objects.for_merchant(mid)

    def perform_update(self, serializer):
        try:
            serializer.save()
        except Exception as e:
            from django.db import IntegrityError

            if isinstance(e, IntegrityError):
                raise ValidationError({"date": "Special date already exists for this merchant."})
            raise

    def perform_destroy(self, instance):
        SpecialDate.all_objects.filter(pk=instance.pk).delete()


class MerchantSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(required=False, allow_null=True)
    logo_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Merchant
        fields = ["id", "name", "slug", "vertical", "is_active", "logo", "logo_url"]
        read_only_fields = ["id", "slug"]


class MerchantDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        mid = _require_merchant_id(request)
        try:
            m = Merchant.objects.get(pk=mid)
        except Merchant.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(MerchantSerializer(m, context={"request": request}).data)

    def patch(self, request):
        mid = _require_merchant_id(request)
        try:
            m = Merchant.objects.get(pk=mid)
        except Merchant.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        ser = MerchantSerializer(m, data=request.data, partial=True, context={"request": request})
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def put(self, request):
        return self.patch(request)


class MerchantLogoUploadView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        mid = _require_merchant_id(request)
        try:
            m = Merchant.objects.get(pk=mid)
        except Merchant.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        f = request.FILES.get("logo") or request.FILES.get("file")
        if not f:
            url = request.data.get("logo_url")
            if url:
                m.logo_url = url
                if m.logo:
                    m.logo.delete(save=False)
                    m.logo = None
                m.save(update_fields=["logo_url", "logo", "updated_at"])
                return Response(MerchantSerializer(m, context={"request": request}).data)
            raise ValidationError({"logo": "logo file or logo_url required."})
        m.logo = f
        m.logo_url = ""
        m.save(update_fields=["logo", "logo_url", "updated_at"])
        return Response(MerchantSerializer(m, context={"request": request}).data)


class PublicMerchantView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        slug = request.query_params.get("slug") or request.headers.get("X-Merchant-Slug") or "ice-zone"
        if slug == "zona-ice":
            slug = "ice-zone"
        m = Merchant.objects.filter(slug=slug).first() or Merchant.objects.first()
        if not m:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(MerchantSerializer(m, context={"request": request}).data)


class EmployeeListCreateView(generics.ListCreateAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        return Employee.objects.for_merchant(mid).order_by("fullname")

    def perform_create(self, serializer):
        mid = _require_merchant_id(self.request)
        try:
            serializer.save(merchant_id=mid)
        except Exception as e:
            from django.db import IntegrityError

            if isinstance(e, IntegrityError):
                raise ValidationError({"fullname": "Employee already exists for this merchant."})
            raise


class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        mid = _resolve_merchant_id(self.request)
        return Employee.objects.for_merchant(mid)

    def perform_destroy(self, instance):
        Employee.all_objects.filter(pk=instance.pk).delete()


class SeatLimitExceeded(ValidationError):
    status_code = status.HTTP_409_CONFLICT
    default_detail = {"seats": "Seat limit reached for this merchant."}
    default_code = "seat_limit_reached"


class UserListCreateView(generics.ListCreateAPIView):
    serializer_class = PlatformUserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        return PlatformUser.objects.for_merchant(mid).order_by("user__username")

    def perform_create(self, serializer):
        mid = _require_merchant_id(self.request)
        with transaction.atomic():
            merchant = Merchant.objects.select_for_update().get(pk=mid)
            active = PlatformUser.objects.filter(
                merchant_id=mid, user__is_active=True
            ).count()
            if active >= merchant.seat_limit:
                raise SeatLimitExceeded()
            profile = serializer.save()
        if profile.role == "ADMIN":
            AuditEntry.objects.create(
                actor=self.request.user,
                action="USER_GRANTED_ADMIN",
                merchant_id=mid,
                detail={"username": profile.user.username},
            )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlatformUserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        return PlatformUser.objects.for_merchant(mid)

    def perform_update(self, serializer):
        profile = serializer.save()
        if serializer.validated_data.get("role") == "ADMIN":
            AuditEntry.objects.create(
                actor=self.request.user,
                action="USER_GRANTED_ADMIN",
                merchant_id=profile.merchant_id,
                detail={"username": profile.user.username},
            )

    def perform_destroy(self, instance):
        instance.user.is_active = False
        instance.user.save(update_fields=["is_active"])


class CompanyOnboardingView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMaster]

    def get(self, request):
        profile = _requester_profile(request)
        queryset = Merchant.objects.order_by("name")
        if not _is_full_master(request) and profile is not None:
            assigned = set(profile.assigned_merchants.values_list("pk", flat=True))
            if profile.merchant_id is not None:
                assigned.add(profile.merchant_id)
            queryset = queryset.filter(pk__in=assigned)
        return Response(
            [
                {
                    "id": m.pk,
                    "name": m.name,
                    "slug": m.slug,
                    "seat_limit": m.seat_limit,
                    "has_branches": m.has_branches,
                    "is_active": m.is_active,
                }
                for m in queryset
            ]
        )

    def post(self, request):
        from django.contrib.auth.models import User
        from django.db import IntegrityError

        serializer = CompanyOnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if Merchant.objects.filter(slug=data["slug"]).exists():
            raise Conflict({"slug": "slug already taken."})
        try:
            with transaction.atomic():
                merchant = Merchant.objects.create(
                    name=data["name"],
                    slug=data["slug"],
                    logo_url=data.get("logo_url") or None,
                    seat_limit=data.get("seat_limit", 10),
                    has_branches=data.get("has_branches", False),
                )
                user = User(username=data["admin_username"])
                user.set_password(data["admin_password"])
                user.save()
                PlatformUser.objects.create(
                    user=user,
                    merchant=merchant,
                    role="ADMIN",
                    kind=PlatformUser.Kind.PERSONAL,
                    must_change_password=True,
                )
                AuditEntry.objects.create(
                    actor=request.user,
                    action="COMPANY_ONBOARDED",
                    merchant=merchant,
                    detail={"slug": merchant.slug, "seat_limit": merchant.seat_limit},
                )
        except IntegrityError:
            raise Conflict({"detail": "Onboarding conflict, nothing was created."})
        return Response(
            {
                "merchant": {
                    "id": merchant.pk,
                    "name": merchant.name,
                    "slug": merchant.slug,
                    "seat_limit": merchant.seat_limit,
                    "has_branches": merchant.has_branches,
                },
                "admin": {"username": user.username, "must_change_password": True},
            },
            status=status.HTTP_201_CREATED,
        )


class MasterCompanyDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMaster]

    def _scoped(self, request, pk):
        queryset = Merchant.objects.filter(pk=pk)
        if not _is_full_master(request):
            profile = _requester_profile(request)
            assigned = set()
            if profile is not None:
                assigned = set(profile.assigned_merchants.values_list("pk", flat=True))
                if profile.merchant_id is not None:
                    assigned.add(profile.merchant_id)
            queryset = queryset.filter(pk__in=assigned)
        return queryset.first()

    def get(self, request, pk):
        merchant = self._scoped(request, pk)
        if merchant is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "Company not found."}}, status=404)
        return Response(_serialize_company(merchant))

    def patch(self, request, pk):
        from apps.tenancy.serializers import SEAT_TIERS

        if not _is_full_master(request):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only MASTER edits companies.")
        merchant = Merchant.objects.filter(pk=pk).first()
        if merchant is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "Company not found."}}, status=404)
        data = request.data or {}
        if "name" in data:
            merchant.name = data["name"]
        if "logo_url" in data:
            merchant.logo_url = data["logo_url"] or None
        if "seat_limit" in data:
            try:
                seats = int(data["seat_limit"])
            except (TypeError, ValueError):
                seats = -1
            if seats not in SEAT_TIERS:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": f"seat_limit must be one of {SEAT_TIERS}."}}, status=400)
            merchant.seat_limit = seats
        if "has_branches" in data:
            merchant.has_branches = bool(data["has_branches"])
        if "is_active" in data:
            merchant.is_active = bool(data["is_active"])
        merchant.save()
        AuditEntry.objects.create(
            actor=request.user,
            action="COMPANY_UPDATED",
            merchant=merchant,
            detail={"seat_limit": merchant.seat_limit, "has_branches": merchant.has_branches},
        )
        return Response(_serialize_company(merchant))

    def delete(self, request, pk):
        if not _is_full_master(request):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only MASTER deactivates companies.")
        merchant = Merchant.objects.filter(pk=pk).first()
        if merchant is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "Company not found."}}, status=404)
        merchant.is_active = False
        merchant.save(update_fields=["is_active"])
        AuditEntry.objects.create(
            actor=request.user,
            action="COMPANY_DEACTIVATED",
            merchant=merchant,
            detail={},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


def _serialize_company(merchant):
    return {
        "id": merchant.pk,
        "name": merchant.name,
        "slug": merchant.slug,
        "seat_limit": merchant.seat_limit,
        "has_branches": merchant.has_branches,
        "is_active": merchant.is_active,
        "logo_url": merchant.logo_url,
        "active_users": PlatformUser.objects.filter(
            merchant_id=merchant.pk, user__is_active=True
        ).count(),
    }


class InternalUserListCreateView(generics.ListCreateAPIView):
    serializer_class = InternalUserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMaster]

    def get_queryset(self):
        if _is_full_master(self.request):
            return PlatformUser.objects.filter(merchant__isnull=True).order_by(
                "user__username"
            )
        profile = _requester_profile(self.request)
        if profile is None:
            return PlatformUser.objects.none()
        return PlatformUser.objects.filter(pk=profile.pk)

    def perform_create(self, serializer):
        if not _is_full_master(self.request):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only MASTER creates internal users.")
        profile = serializer.save()
        AuditEntry.objects.create(
            actor=self.request.user,
            action="INTERNAL_USER_CREATED",
            detail={"username": profile.user.username, "role": profile.role},
        )


class InternalUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InternalUserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMaster]

    def get_queryset(self):
        if _is_full_master(self.request):
            return PlatformUser.objects.filter(merchant__isnull=True)
        profile = _requester_profile(self.request)
        if profile is None:
            return PlatformUser.objects.none()
        return PlatformUser.objects.filter(pk=profile.pk)

    def perform_update(self, serializer):
        if not _is_full_master(self.request):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only MASTER edits internal users.")
        profile = serializer.save()
        AuditEntry.objects.create(
            actor=self.request.user,
            action="INTERNAL_USER_UPDATED",
            detail={"username": profile.user.username, "role": profile.role},
        )

    def perform_destroy(self, instance):
        if not _is_full_master(self.request):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only MASTER deactivates internal users.")
        instance.user.is_active = False
        instance.user.save(update_fields=["is_active"])


class AuditListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMaster]

    def get_queryset(self):
        queryset = AuditEntry.objects.order_by("-created_at")
        if _is_full_master(self.request):
            return queryset
        profile = _requester_profile(self.request)
        if profile is None:
            return AuditEntry.objects.none()
        assigned = set(profile.assigned_merchants.values_list("pk", flat=True))
        if profile.merchant_id is not None:
            assigned.add(profile.merchant_id)
        return queryset.filter(merchant_id__in=assigned)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()[:200]
        return Response(
            [
                {
                    "id": e.pk,
                    "actor": e.actor.username if e.actor_id else None,
                    "action": e.action,
                    "merchant": e.merchant.slug if e.merchant_id else None,
                    "detail": e.detail,
                    "created_at": e.created_at,
                }
                for e in queryset
            ]
        )


def _require_branches_enabled(request, mid):
    merchant = Merchant.objects.filter(pk=mid).first()
    if merchant is None or not merchant.has_branches:
        raise NotFound({"branches": "Branches module is not enabled for this merchant."})


class BranchListCreateView(generics.ListCreateAPIView):
    serializer_class = BranchSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        _require_branches_enabled(self.request, mid)
        return Branch.objects.for_merchant(mid).order_by("name")

    def perform_create(self, serializer):
        mid = _require_merchant_id(self.request)
        _require_branches_enabled(self.request, mid)
        serializer.save(merchant_id=mid)


class BranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BranchSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        _require_branches_enabled(self.request, mid)
        return Branch.objects.for_merchant(mid)


class PasswordChangeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from django.utils import timezone

        from apps.tenancy.password_policy import validate_password_complexity

        current = (request.data or {}).get("current_password", "")
        new_password = (request.data or {}).get("new_password", "")
        user = request.user
        if not user.check_password(current):
            return Response({"error": {"code": "BAD_PASSWORD", "message": "Current password is wrong."}}, status=400)
        try:
            validate_password_complexity(new_password)
        except ValidationError as e:
            return Response({"error": {"code": "WEAK_PASSWORD", "message": e.detail}}, status=422)
        user.set_password(new_password)
        user.save(update_fields=["password"])
        profile = _requester_profile(request)
        if profile is not None:
            profile.must_change_password = False
            profile.password_changed_at = timezone.now()
            profile.save(update_fields=["must_change_password", "password_changed_at"])
        AuditEntry.objects.create(
            actor=user,
            action="PASSWORD_CHANGED",
            merchant_id=getattr(profile, "merchant_id", None),
            detail={},
        )
        return Response({"ok": True})


def _revoke_all_sessions(target_user, actor=None, action="SESSION_REVOKED"):
    from django.utils import timezone

    from apps.tenancy.models import SessionRecord

    now = timezone.now()
    revoked = (
        SessionRecord.objects.filter(user=target_user, revoked_at__isnull=True).update(
            revoked_at=now
        )
    )
    if revoked:
        profile = getattr(target_user, "platform_profile", None)
        AuditEntry.objects.create(
            actor=actor,
            action=action,
            merchant_id=getattr(profile, "merchant_id", None),
            detail={"username": target_user.username, "revoked": revoked},
        )
    return revoked


def _issue_reset_token(target_user, created_by, minutes=20):
    import hashlib
    import secrets
    from datetime import timedelta

    from django.utils import timezone

    from apps.tenancy.models import PasswordResetToken

    _revoke_all_sessions(target_user, actor=created_by, action="SESSION_REVOKED_ON_RESET")
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    PasswordResetToken.objects.create(
        user=target_user,
        token_hash=token_hash,
        created_by=created_by,
        expires_at=timezone.now() + timedelta(minutes=minutes),
    )
    return raw


class ResetRequestView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def post(self, request):
        from django.contrib.auth.models import User

        mid = _require_merchant_id(request)
        username = (request.data or {}).get("username", "")
        target = User.objects.filter(
            username=username, platform_profile__merchant_id=mid, is_active=True
        ).first()
        if target is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "User not found."}}, status=404)
        raw = _issue_reset_token(target, request.user)
        AuditEntry.objects.create(
            actor=request.user,
            action="PASSWORD_RESET_ISSUED",
            merchant_id=mid,
            detail={"username": username},
        )
        return Response({"reset_token": raw, "expires_minutes": 20})


class MasterResetRequestView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMaster]

    def post(self, request):
        from django.contrib.auth.models import User
        from django.db.models import Q

        username = (request.data or {}).get("username", "")
        target = (
            User.objects.filter(username=username, is_active=True)
            .filter(
                Q(platform_profile__merchant__isnull=True)
                | Q(platform_profile__isnull=True, is_superuser=True)
            )
            .first()
        )
        if target is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "User not found."}}, status=404)
        if target.pk == request.user.pk:
            return Response({"error": {"code": "SELF_RESET_FORBIDDEN", "message": "Ask another master."}}, status=403)
        raw = _issue_reset_token(target, request.user)
        AuditEntry.objects.create(
            actor=request.user,
            action="PASSWORD_RESET_ISSUED",
            detail={"username": username},
        )
        return Response({"reset_token": raw, "expires_minutes": 20})


class ResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import hashlib

        from django.utils import timezone

        from apps.tenancy.models import PasswordResetToken
        from apps.tenancy.password_policy import validate_password_complexity

        raw = (request.data or {}).get("token", "")
        new_password = (request.data or {}).get("new_password", "")
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        record = PasswordResetToken.objects.filter(token_hash=token_hash).first()
        if record is None or record.is_burned or record.expires_at < timezone.now():
            return Response({"error": {"code": "TOKEN_INVALID", "message": "Token invalid or expired."}}, status=410)
        try:
            validate_password_complexity(new_password)
        except ValidationError as e:
            return Response({"error": {"code": "WEAK_PASSWORD", "message": e.detail}}, status=422)
        user = record.user
        user.set_password(new_password)
        user.save(update_fields=["password"])
        profile = getattr(user, "platform_profile", None)
        if profile is not None:
            profile.must_change_password = False
            profile.password_changed_at = timezone.now()
            profile.save(update_fields=["must_change_password", "password_changed_at"])
        record.used_at = timezone.now()
        record.save(update_fields=["used_at"])
        AuditEntry.objects.create(
            actor=user,
            action="PASSWORD_RESET_USED",
            merchant_id=getattr(profile, "merchant_id", None),
            detail={},
        )
        return Response({"ok": True})


def _serialize_session(record):
    return {
        "jti_prefix": record.jti[:8],
        "created_at": record.created_at,
        "active": record.is_active,
    }


class UserSessionListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        from django.contrib.auth.models import User

        from apps.tenancy.models import SessionRecord

        mid = _require_merchant_id(request)
        target = User.objects.filter(
            pk=pk, platform_profile__merchant_id=mid
        ).first()
        if target is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "User not found."}}, status=404)
        records = SessionRecord.objects.filter(user=target).order_by("-created_at")[:50]
        return Response([_serialize_session(r) for r in records])


class UserSessionRevokeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        from django.contrib.auth.models import User
        from django.utils import timezone

        from apps.tenancy.models import SessionRecord

        mid = _require_merchant_id(request)
        target = User.objects.filter(
            pk=pk, platform_profile__merchant_id=mid
        ).first()
        if target is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "User not found."}}, status=404)
        jti = (request.data or {}).get("jti")
        queryset = SessionRecord.objects.filter(user=target, revoked_at__isnull=True)
        if jti:
            queryset = queryset.filter(jti__startswith=jti)
        revoked = queryset.update(revoked_at=timezone.now())
        AuditEntry.objects.create(
            actor=request.user,
            action="SESSION_REVOKED",
            merchant_id=mid,
            detail={"username": target.username, "revoked": revoked},
        )
        return Response({"revoked": revoked})


class MasterSessionListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMaster]

    def get(self, request):
        from django.contrib.auth.models import User

        from apps.tenancy.models import SessionRecord

        username = request.query_params.get("username", "")
        target = User.objects.filter(username=username).first()
        if target is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "User not found."}}, status=404)
        records = SessionRecord.objects.filter(user=target).order_by("-created_at")[:50]
        return Response([_serialize_session(r) for r in records])


class MasterSessionRevokeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMaster]

    def post(self, request):
        from django.contrib.auth.models import User
        from django.utils import timezone

        from apps.tenancy.models import SessionRecord

        username = (request.data or {}).get("username", "")
        target = User.objects.filter(username=username).first()
        if target is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "User not found."}}, status=404)
        revoked = SessionRecord.objects.filter(
            user=target, revoked_at__isnull=True
        ).update(revoked_at=timezone.now())
        AuditEntry.objects.create(
            actor=request.user,
            action="SESSION_REVOKED",
            detail={"username": username, "revoked": revoked},
        )
        return Response({"revoked": revoked})
