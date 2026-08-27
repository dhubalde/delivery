from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import Product, Flavor
from apps.catalog.serializers import ProductSerializer, FlavorSerializer


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