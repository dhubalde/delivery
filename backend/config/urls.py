from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/catalog/", include("apps.catalog.urls")),
    path("api/v1/", include("apps.catalog.urls")),
    path("api/v1/", include("apps.tenancy.urls")),
    path("api/v1/", include("apps.delivery.urls")),
    path("api/v1/", include("apps.orders.urls")),
    path("api/public/", include("apps.orders.urls_public")),
    path("api/public/<slug:slug>/orders", include("apps.orders.urls_public")),
    path("api/public/<slug:slug>/orders/", include("apps.orders.urls_public")),
]
