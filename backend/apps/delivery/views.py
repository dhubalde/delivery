from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.delivery.models import DeliveryConfig, Zone
from apps.delivery.services import ConfigImmutableError, DeliveryConfigService, DeliveryFeeError


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


class DeliveryConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryConfig
        fields = ["id", "modo", "cobro", "calculo", "flat_amount", "free_threshold", "third_party_fixed_amount"]
        read_only_fields = ["id"]


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ["id", "name", "base_fee"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("name is required.")
        return str(value).strip()


def _get_or_create_config(merchant):
    try:
        return DeliveryConfigService.get_or_create(merchant)
    except Exception:
        from django.db import IntegrityError

        cfg = DeliveryConfig.all_objects.filter(merchant=merchant).first()
        if cfg is not None:
            if cfg.deleted_at is not None:
                cfg.deleted_at = None
                cfg.save(update_fields=["deleted_at", "updated_at"])
            return cfg
        raise


class DeliveryConfigView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        mid = _require_merchant_id(request)
        from apps.tenancy.models import Merchant

        merchant = Merchant.objects.filter(pk=mid).first() or Merchant.all_objects.filter(pk=mid).first()
        if merchant is None:
            return Response({"detail": "Merchant not found."}, status=status.HTTP_404_NOT_FOUND)
        config = _get_or_create_config(merchant)
        return Response(DeliveryConfigSerializer(config).data)

    def put(self, request):
        mid = _require_merchant_id(request)
        from apps.tenancy.models import Merchant

        merchant = Merchant.objects.filter(pk=mid).first() or Merchant.all_objects.filter(pk=mid).first()
        if merchant is None:
            return Response({"detail": "Merchant not found."}, status=status.HTTP_404_NOT_FOUND)
        config = _get_or_create_config(merchant)
        serializer = DeliveryConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated = DeliveryConfigService.update_config(merchant, **serializer.validated_data)
        except ConfigImmutableError as e:
            raise ValidationError({"modo": str(e)})
        except DeliveryFeeError as e:
            raise ValidationError({"non_field_errors": str(e)})
        return Response(DeliveryConfigSerializer(updated).data)


class ZoneListCreateView(generics.ListCreateAPIView):
    serializer_class = ZoneSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        return Zone.objects.for_merchant(mid).order_by("name")

    def perform_create(self, serializer):
        mid = _require_merchant_id(self.request)
        try:
            serializer.save(merchant_id=mid)
        except Exception as e:
            from django.db import IntegrityError

            if isinstance(e, IntegrityError):
                raise ValidationError({"name": "Zone name already exists for this merchant."})
            raise


class ZoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ZoneSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        mid = _require_merchant_id(self.request)
        return Zone.objects.for_merchant(mid)

    def perform_update(self, serializer):
        try:
            serializer.save()
        except Exception as e:
            from django.db import IntegrityError

            if isinstance(e, IntegrityError):
                raise ValidationError({"name": "Zone name already exists for this merchant."})
            raise

    def perform_destroy(self, instance):
        Zone.all_objects.filter(pk=instance.pk).delete()
        try:
            instance.delete()
        except Exception:
            pass
