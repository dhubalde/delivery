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

from apps.tenancy.views import (
    BranchDetailView,
    BranchListCreateView,
    EmployeeDetailView,
    EmployeeListCreateView,
    PasswordChangeView,
    ResetConfirmView,
    ResetRequestView,
    UserDetailView,
    UserListCreateView,
    UserSessionListView,
    UserSessionRevokeView,
)

urlpatterns += [
    path("employees/", EmployeeListCreateView.as_view(), name="employee-list-create"),
    path("employees/<int:pk>/", EmployeeDetailView.as_view(), name="employee-detail"),
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("users/change-password/", PasswordChangeView.as_view(), name="password-change"),
    path("users/reset-request/", ResetRequestView.as_view(), name="reset-request"),
    path("users/reset-confirm/", ResetConfirmView.as_view(), name="reset-confirm"),
    path("users/<int:pk>/sessions/", UserSessionListView.as_view(), name="user-sessions"),
    path("users/<int:pk>/sessions/revoke/", UserSessionRevokeView.as_view(), name="user-sessions-revoke"),
    path("branches/", BranchListCreateView.as_view(), name="branch-list-create"),
    path("branches/<int:pk>/", BranchDetailView.as_view(), name="branch-detail"),
]
