from django.urls import path

from apps.catalog.views import FlavorListView, ProductDetailView, ProductListView

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("flavors/", FlavorListView.as_view(), name="flavor-list"),
]
