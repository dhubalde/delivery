from django.urls import path

from apps.orders.views import PublicOrderCreateView

urlpatterns = [
    path("<slug:slug>/orders", PublicOrderCreateView.as_view(), name="public-order-create"),
    path("<slug:slug>/orders/", PublicOrderCreateView.as_view(), name="public-order-create-slash"),
    path("", PublicOrderCreateView.as_view(), name="public-order-create-root"),
    path("/", PublicOrderCreateView.as_view(), name="public-order-create-root-slash"),
]
