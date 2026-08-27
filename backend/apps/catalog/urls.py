from django.urls import path

from apps.catalog.views import FlavorListView, ProductListView

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("flavors/", FlavorListView.as_view(), name="flavor-list"),
]