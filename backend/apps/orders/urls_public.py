from django.urls import path

from apps.orders.views_public import PublicOrderCreateView

urlpatterns = [
    path("", PublicOrderCreateView.as_view(), name="public-order-create"),
]
