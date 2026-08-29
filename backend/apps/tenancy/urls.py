from django.urls import path

from apps.tenancy.views import ScheduleDeleteView, ScheduleListUpsertView, SpecialDateDetailView, SpecialDateListCreateView

urlpatterns = [
    path("schedules/", ScheduleListUpsertView.as_view(), name="schedule-list-upsert"),
    path("schedules/<int:pk>/", ScheduleDeleteView.as_view(), name="schedule-delete"),
    path("special-dates/", SpecialDateListCreateView.as_view(), name="special-date-list-create"),
    path("special-dates/<int:pk>/", SpecialDateDetailView.as_view(), name="special-date-detail"),
]
