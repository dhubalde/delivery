from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.catalog.models import Category, Flavor, Product, CatalogStat
from apps.catalog.serializers import CategorySerializer, FlavorSerializer, ProductSerializer
from apps.tenancy.models import Merchant


def _resolve_merchant_id(request):
    mid = getattr(request, "tenant_merchant_id", None)
    if mid is not None:
        return mid
    slug = request.query_params.get("merchant_slug") or request.headers.get("X-Merchant-Slug") or request.META.get("HTTP_X_MERCHANT_SLUG")
    if slug:
        try:
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


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Category.objects.all().order_by("position", "name")
        mid = _resolve_merchant_id(self.request)
        if mid is not None:
            qs = qs.filter(merchant_id=mid)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            val = str(is_active).lower()
            qs = qs.filter(is_active=val in ("1", "true", "yes"))
        return qs

    def perform_create(self, serializer):
        mid = _resolve_merchant_id(self.request)
        if mid is None:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"merchant": "merchant context required (merchant_slug, merchant_id or X-Merchant-Id header)"})
        serializer.save(merchant_id=mid)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Category.objects.all()
        mid = _resolve_merchant_id(self.request)
        if mid is not None:
            qs = qs.filter(merchant_id=mid)
        return qs

    def perform_destroy(self, instance):
        instance.delete()


class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Product.objects.all().order_by("name")
        mid = _resolve_merchant_id(self.request)
        if mid is not None:
            qs = qs.filter(merchant_id=mid)
        category_id = self.request.query_params.get("category")
        if category_id is not None:
            try:
                qs = qs.filter(category_id=int(category_id))
            except ValueError:
                pass
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__istartswith=search)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            val = str(is_active).lower()
            qs = qs.filter(is_active=val in ("1", "true", "yes"))
        return qs

    def perform_create(self, serializer):
        mid = _resolve_merchant_id(self.request)
        if mid is None:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"merchant": "merchant context required"})
        category_id = serializer.validated_data.get("category_id")
        if category_id is not None:
            from apps.catalog.models import Category as CatModel

            cat = CatModel.objects.filter(pk=category_id).first() or CatModel.all_objects.filter(pk=category_id).first()
            if cat and cat.merchant_id != mid:
                from rest_framework.exceptions import ValidationError

                raise ValidationError({"category_id": "Category belongs to different merchant."})
        serializer.save(merchant_id=mid)


ProductListView = ProductListCreateView


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Product.objects.all()
        mid = _resolve_merchant_id(self.request)
        if mid is not None:
            qs = qs.filter(merchant_id=mid)
        return qs

    def perform_update(self, serializer):
        mid = _resolve_merchant_id(self.request)
        category_id = serializer.validated_data.get("category_id")
        if category_id is not None and mid is not None:
            from apps.catalog.models import Category as CatModel

            cat = CatModel.objects.filter(pk=category_id).first() or CatModel.all_objects.filter(pk=category_id).first()
            if cat and cat.merchant_id != mid:
                from rest_framework.exceptions import ValidationError

                raise ValidationError({"category_id": "Category belongs to different merchant."})
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()


class FlavorListCreateView(generics.ListCreateAPIView):
    serializer_class = FlavorSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Flavor.objects.all().order_by("name")
        mid = _resolve_merchant_id(self.request)
        if mid is not None:
            qs = qs.filter(merchant_id=mid)
        category_id = self.request.query_params.get("category")
        if category_id is not None:
            try:
                qs = qs.filter(category_id=int(category_id))
            except ValueError:
                pass
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__istartswith=search)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            val = str(is_active).lower()
            qs = qs.filter(is_active=val in ("1", "true", "yes"))
        return qs

    def perform_create(self, serializer):
        mid = _resolve_merchant_id(self.request)
        if mid is None:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"merchant": "merchant context required"})
        category_id = serializer.validated_data.get("category_id")
        if category_id is not None:
            from apps.catalog.models import Category as CatModel

            cat = CatModel.objects.filter(pk=category_id).first() or CatModel.all_objects.filter(pk=category_id).first()
            if cat and cat.merchant_id != mid:
                from rest_framework.exceptions import ValidationError

                raise ValidationError({"category_id": "Category belongs to different merchant."})
        serializer.save(merchant_id=mid)


FlavorListView = FlavorListCreateView


class FlavorDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FlavorSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Flavor.objects.all()
        mid = _resolve_merchant_id(self.request)
        if mid is not None:
            qs = qs.filter(merchant_id=mid)
        return qs

    def perform_destroy(self, instance):
        instance.delete()


class CatalogStatView(generics.GenericAPIView):
    """Endpoint to increment visit count and get catalog stats (visitors vs buyers)."""

    def post(self, request, *args, **kwargs):
        """Increment visit count for the merchant."""
        mid = _resolve_merchant_id(request)
        if mid is None:
            return Response({"error": "merchant context required"}, status=status.HTTP_400_BAD_REQUEST)
        obj, created = CatalogStat.objects.get_or_create(merchant_id=mid)
        obj.visit_count += 1
        obj.save()
        return Response({"visit_count": obj.visit_count}, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        """Get catalog stats: visit count and buyer count."""
        mid = _resolve_merchant_id(request)
        if mid is None:
            return Response({"error": "merchant context required"}, status=status.HTTP_400_BAD_REQUEST)
        obj, created = CatalogStat.objects.get_or_create(merchant_id=mid)
        return Response(
            {"visit_count": obj.visit_count, "buyer_count": obj.buyer_count},
            status=status.HTTP_200_OK,
        )