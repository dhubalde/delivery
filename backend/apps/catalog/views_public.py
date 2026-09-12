from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from apps.catalog.models import Category, Flavor, Product, CatalogStat
from apps.catalog.serializers import CategorySerializer, FlavorSerializer, ProductSerializer
from apps.tenancy.models import Merchant


def _get_merchant_by_slug(slug):
    merchant = Merchant.all_objects.filter(slug=slug).first()
    if merchant is None or merchant.deleted_at is not None or not merchant.is_active:
        from django.http import Http404

        raise Http404(f"No Merchant matches slug={slug}")
    return merchant


class PublicCatalogAggregateView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def get(self, request, slug):
        merchant = _get_merchant_by_slug(slug)
        categories = Category.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("position", "name")
        products = Product.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("name")
        flavors = Flavor.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("name")
        try:
            stat_obj, _created = CatalogStat.objects.get_or_create(merchant_id=merchant.pk)
            stats = {"visit_count": stat_obj.visit_count, "buyer_count": stat_obj.buyer_count}
        except Exception:
            stats = {"visit_count": 0, "buyer_count": 0}
        cat_data = CategorySerializer(categories, many=True).data
        prod_data = ProductSerializer(products, many=True, context={"request": request}).data
        flav_data = FlavorSerializer(flavors, many=True).data
        merchant_data = {
            "id": merchant.pk,
            "slug": merchant.slug,
            "name": merchant.name,
            "is_active": merchant.is_active,
            "logo_url": getattr(merchant, "resolved_logo_url", "") or "",
        }
        return Response(
            {
                "merchant": merchant_data,
                "categories": cat_data,
                "products": prod_data,
                "flavors": flav_data,
                "stats": stats,
            }
        )


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


class CatalogStatPublicView(generics.GenericAPIView):
    """Public endpoint: GET returns stats, POST increments visit count."""

    permission_classes = [permissions.AllowAny]

    def _get_merchant(self):
        return _get_merchant_by_slug(self.kwargs["slug"])

    def post(self, request, slug):
        merchant = self._get_merchant()
        obj, created = CatalogStat.objects.get_or_create(merchant_id=merchant.pk)
        obj.visit_count += 1
        obj.save()
        return Response({"visit_count": obj.visit_count, "buyer_count": obj.buyer_count})

    def get(self, request, slug):
        merchant = self._get_merchant()
        obj, created = CatalogStat.objects.get_or_create(merchant_id=merchant.pk)
        return Response({"visit_count": obj.visit_count, "buyer_count": obj.buyer_count})
