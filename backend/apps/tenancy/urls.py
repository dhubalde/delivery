from django.urls import path

from apps.tenancy.views import (
    MerchantDetailView,
    MerchantLogoUploadView,
    PublicMerchantView,
    ScheduleDeleteView,
    ScheduleListUpsertView,
    SpecialDateDetailView,
    SpecialDateListCreateView,
)

urlpatterns = [
    path("schedules/", ScheduleListUpsertView.as_view(), name="schedule-list-upsert"),
    path("schedules/<int:pk>/", ScheduleDeleteView.as_view(), name="schedule-delete"),
    path("special-dates/", SpecialDateListCreateView.as_view(), name="special-date-list-create"),
    path("special-dates/<int:pk>/", SpecialDateDetailView.as_view(), name="special-date-detail"),
    path("merchant/", MerchantDetailView.as_view(), name="merchant-detail"),
    path("merchant/logo/", MerchantLogoUploadView.as_view(), name="merchant-logo-upload"),
    path("merchant/public/", PublicMerchantView.as_view(), name="merchant-public"),
]
