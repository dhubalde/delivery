from rest_framework import generics, permissions

from apps.catalog.models import Category, Flavor, Product
from apps.catalog.serializers import CategorySerializer, FlavorSerializer, ProductSerializer


def _resolve_merchant_id(request):
    mid = getattr(request, "tenant_merchant_id", None)
    if mid is not None:
        return mid
    slug = request.query_params.get("merchant_slug")
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


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        category_id = self.request.query_params.get("category", None)
        search = self.request.query_params.get("search", None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        if search is not None:
            queryset = queryset.filter(name__istartswith=search)
        return queryset


class FlavorListView(generics.ListAPIView):
    serializer_class = FlavorSerializer

    def get_queryset(self):
        queryset = Flavor.objects.all()
        category_id = self.request.query_params.get("category", None)
        search = self.request.query_params.get("search", None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        if search is not None:
            queryset = queryset.filter(name__istartswith=search)
        return queryset
