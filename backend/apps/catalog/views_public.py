from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from apps.catalog.models import Category, Flavor, Product
from apps.catalog.serializers import CategorySerializer, FlavorSerializer, ProductSerializer
from apps.tenancy.models import Merchant


def _get_merchant_by_slug(slug):
    merchant = Merchant.objects.filter(slug=slug).first()
    if merchant is None:
        merchant = Merchant.all_objects.filter(slug=slug).first()
    return get_object_or_404(Merchant.objects.all(), slug=slug) if merchant is None else merchant


class PublicCategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        merchant = _get_merchant_by_slug(self.kwargs["slug"])
        return Category.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("position", "name")


class PublicProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        merchant = _get_merchant_by_slug(self.kwargs["slug"])
        qs = Product.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("name")
        category_id = self.request.query_params.get("category")
        if category_id is not None:
            try:
                qs = qs.filter(category_id=int(category_id))
            except ValueError:
                pass
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__istartswith=search)
        return qs


class PublicFlavorListView(generics.ListAPIView):
    serializer_class = FlavorSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        merchant = _get_merchant_by_slug(self.kwargs["slug"])
        qs = Flavor.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("name")
        category_id = self.request.query_params.get("category")
        if category_id is not None:
            try:
                qs = qs.filter(category_id=int(category_id))
            except ValueError:
                pass
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__istartswith=search)
        return qs
