from django.urls import path

from apps.catalog.views import PublicCategoryListView, PublicFlavorListView, PublicMenuView, PublicProductListView

urlpatterns = [
    path("products/", PublicProductListView.as_view(), name="public-product-list"),
    path("flavors/", PublicFlavorListView.as_view(), name="public-flavor-list"),
    path("categories/", PublicCategoryListView.as_view(), name="public-category-list"),
    path("menu/", PublicMenuView.as_view(), name="public-menu"),
]
