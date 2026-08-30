from django.urls import path

from apps.orders.views import OrderBoardView, OrderDetailView, OrderTransitionView

urlpatterns = [
    path("orders/", OrderBoardView.as_view(), name="order-board"),
    path("orders", OrderBoardView.as_view(), name="order-board-no-slash"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>", OrderDetailView.as_view(), name="order-detail-no-slash"),
    path("orders/<int:pk>/transition/", OrderTransitionView.as_view(), name="order-transition"),
    path("orders/<int:pk>/transition", OrderTransitionView.as_view(), name="order-transition-no-slash"),
]
