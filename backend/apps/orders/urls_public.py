from django.urls import path

from apps.orders.views import PublicOrderCreateView

urlpatterns = [
    path("orders", PublicOrderCreateView.as_view(), name="public-order-create"),
    path("orders/", PublicOrderCreateView.as_view(), name="public-order-create-slash"),
]
