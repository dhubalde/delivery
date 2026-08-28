from django.urls import path

from apps.catalog.views import CategoryDetailView, CategoryListCreateView, FlavorListView, ProductListView

urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path("categories/<int:pk>/", CategoryDetailView.as_view(), name="category-detail"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("flavors/", FlavorListView.as_view(), name="flavor-list"),
]
