from django.urls import path

from apps.delivery.views import DeliveryConfigView, ZoneDetailView, ZoneListCreateView

urlpatterns = [
    path("delivery-config/", DeliveryConfigView.as_view(), name="delivery-config"),
    path("zones/", ZoneListCreateView.as_view(), name="zone-list-create"),
    path("zones/<int:pk>/", ZoneDetailView.as_view(), name="zone-detail"),
]
