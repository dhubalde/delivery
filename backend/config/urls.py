from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/catalog/", include("apps.catalog.urls")),
    path("api/public/<slug:slug>/orders", include("apps.orders.urls_public")),
    path("api/public/<slug:slug>/orders/", include("apps.orders.urls_public")),
    path("api/public/<slug:slug>/", include("apps.catalog.urls_public")),
]