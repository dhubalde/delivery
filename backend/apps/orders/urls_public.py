from django.urls import path

from apps.orders.views import PublicOrderCreateView
from apps.payments.views import PublicOrderPayView

urlpatterns = [
    path("orders", PublicOrderCreateView.as_view(), name="public-order-create"),
    path("orders/", PublicOrderCreateView.as_view(), name="public-order-create-slash"),
    path("orders/<int:pk>/pay", PublicOrderPayView.as_view(), name="public-order-pay"),
    path("orders/<int:pk>/pay/", PublicOrderPayView.as_view(), name="public-order-pay-slash"),
]
