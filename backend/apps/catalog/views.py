from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Category, Flavor, Product
from apps.catalog.serializers import CategorySerializer, FlavorSerializer, ProductSerializer
from apps.common.context import get_tenant_merchant_id
from apps.tenancy.models import Merchant


def _get_merchant_by_slug(slug: str) -> Merchant:
    return get_object_or_404(Merchant, slug=slug)


def _resolve_merchant(request) -> Merchant | None:
    mid = get_tenant_merchant_id() or getattr(request, "tenant_merchant_id", None)
    if mid:
        try:
            return Merchant.objects.get(pk=mid)
        except Exception:
            pass
    slug = request.data.get("merchant_slug") or request.query_params.get("merchant_slug") or request.headers.get("X-Merchant-Slug")
    if slug:
        try:
            return Merchant.objects.get(slug=slug)
        except Exception:
            pass
    try:
        return Merchant.objects.filter(slug="ice-zone").first() or Merchant.objects.first()
    except Exception:
        return None


class ProductListView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Product.objects.all().prefetch_related("suggested_flavors__flavor")
        merchant_slug = self.request.query_params.get("merchant_slug")
        if merchant_slug:
            queryset = queryset.filter(merchant__slug=merchant_slug)
        category_id = self.request.query_params.get("category", None)
        search = self.request.query_params.get("search", None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        if search is not None:
            queryset = queryset.filter(name__istartswith=search)
        return queryset

    def perform_create(self, serializer):
        merchant = _resolve_merchant(self.request)
        if merchant is None:
            from rest_framework.exceptions import ValidationError as DRFValidationError

            raise DRFValidationError({"merchant": "No merchant resolved (provide merchant_slug or auth)."})
        serializer.save(merchant=merchant)


class FlavorListView(generics.ListAPIView):
    serializer_class = FlavorSerializer

    def get_queryset(self):
        queryset = Flavor.objects.all()
        merchant_slug = self.request.query_params.get("merchant_slug")
        if merchant_slug:
            queryset = queryset.filter(merchant__slug=merchant_slug)
        category_id = self.request.query_params.get("category", None)
        search = self.request.query_params.get("search", None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        if search is not None:
            queryset = queryset.filter(name__istartswith=search)
        return queryset


class PublicProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get_queryset(self):
        slug = self.kwargs.get("slug") or ""
        merchant = _get_merchant_by_slug(slug)
        queryset = Product.objects.filter(merchant=merchant, is_active=True).prefetch_related("suggested_flavors__flavor")
        category_id = self.request.query_params.get("category", None)
        search = self.request.query_params.get("search", None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        if search is not None:
            queryset = queryset.filter(name__istartswith=search)
        return queryset.order_by("id")


class PublicFlavorListView(generics.ListAPIView):
    serializer_class = FlavorSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get_queryset(self):
        slug = self.kwargs.get("slug") or ""
        merchant = _get_merchant_by_slug(slug)
        queryset = Flavor.objects.filter(merchant=merchant, is_active=True)
        category_id = self.request.query_params.get("category", None)
        search = self.request.query_params.get("search", None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        if search is not None:
            queryset = queryset.filter(name__istartswith=search)
        return queryset.order_by("id")


class PublicCategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get_queryset(self):
        slug = self.kwargs.get("slug") or ""
        merchant = _get_merchant_by_slug(slug)
        return Category.objects.filter(merchant=merchant, is_active=True).order_by("position", "id")


class PublicMenuView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request: Request, slug: str):
        merchant = _get_merchant_by_slug(slug)
        categories = Category.objects.filter(merchant=merchant, is_active=True).order_by("position", "id")
        cat_data = CategorySerializer(categories, many=True).data
        try:
            from apps.tenancy.services.hours import is_open, next_open_at

            open_val = is_open(merchant)
            nxt = next_open_at(merchant)
            nxt_iso = nxt.isoformat() if nxt else None
        except Exception:
            open_val = True
            nxt_iso = None
        return Response(
            {
                "categories": cat_data,
                "is_open": open_val,
                "isOpen": open_val,
                "closed": not open_val,
                "next_open_at": nxt_iso,
            }
        )