import datetime

from django.db import transaction
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenancy.models import Merchant, Schedule, SpecialDate, TimeRange


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
