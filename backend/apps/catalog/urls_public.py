from django.urls import path

from apps.catalog.views_public import CatalogStatPublicView, PublicCategoryListView, PublicFlavorListView, PublicProductListView

urlpatterns = [
    path("<slug:slug>/stat", CatalogStatPublicView.as_view(), name="public-catalog-stat"),
    path("<slug:slug>/stat/", CatalogStatPublicView.as_view(), name="public-catalog-stat-slash"),
    path("<slug:slug>/products", PublicProductListView.as_view(), name="public-product-list"),
    path("<slug:slug>/products/", PublicProductListView.as_view(), name="public-product-list-slash"),
    path("<slug:slug>/flavors", PublicFlavorListView.as_view(), name="public-flavor-list"),
    path("<slug:slug>/flavors/", PublicFlavorListView.as_view(), name="public-flavor-list-slash"),
    path("<slug:slug>/categories", PublicCategoryListView.as_view(), name="public-category-list"),
    path("<slug:slug>/categories/", PublicCategoryListView.as_view(), name="public-category-list-slash"),
]
