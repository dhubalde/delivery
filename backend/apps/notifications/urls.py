from django.urls import path

from apps.notifications.views import (
    NotificationDeleteView,
    NotificationDetailView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("unread/", NotificationListView.as_view(), name="notification-unread"),
    path("<int:pk>/", NotificationDetailView.as_view(), name="notification-detail"),
    path("<int:pk>/delete/", NotificationDeleteView.as_view(), name="notification-delete"),
    path("<int:pk>/mark-read/", NotificationMarkReadView.as_view(), name="notification-mark-read"),
    path("mark-all-read/", NotificationMarkAllReadView.as_view(), name="notification-mark-all-read"),
]