from django.urls import path

from apps.catalog.views import (
    CatalogStatView,
    CategoryDetailView,
    CategoryListCreateView,
    FlavorDetailView,
    FlavorListCreateView,
    FlavorListView,
    ProductDetailView,
    ProductListCreateView,
)

ProductListView = ProductListCreateView
FlavorListView = FlavorListCreateView

urlpatterns = [
    path("stat/", CatalogStatView.as_view(), name="catalog-stat"),
    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path("categories/<int:pk>/", CategoryDetailView.as_view(), name="category-detail"),
    path("products/", ProductListCreateView.as_view(), name="product-list-create"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("flavors/", FlavorListCreateView.as_view(), name="flavor-list-create"),
    path("flavors/<int:pk>/", FlavorDetailView.as_view(), name="flavor-detail"),
    path("products-legacy/", ProductListView.as_view(), name="product-list-legacy"),
    path("flavors-legacy/", FlavorListView.as_view(), name="flavor-list-legacy"),
]
