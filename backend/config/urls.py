from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

from apps.tenancy.auth import WorkZoneTokenView
from apps.tenancy.views import (
    AuditListView,
    CompanyOnboardingView,
    InternalUserDetailView,
    InternalUserListCreateView,
    MasterCompanyDetailView,
    MasterResetRequestView,
    MasterSessionListView,
    MasterSessionRevokeView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/token/", WorkZoneTokenView.as_view(), name="token-obtain"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/master/companies/", CompanyOnboardingView.as_view(), name="company-onboard"),
    path("api/master/companies/<int:pk>/", MasterCompanyDetailView.as_view(), name="company-detail"),
    path("api/master/users/", InternalUserListCreateView.as_view(), name="internal-user-list"),
    path("api/master/users/<int:pk>/", InternalUserDetailView.as_view(), name="internal-user-detail"),
    path("api/master/users/reset-request/", MasterResetRequestView.as_view(), name="master-reset-request"),
    path("api/master/sessions/", MasterSessionListView.as_view(), name="master-sessions"),
    path("api/master/sessions/revoke/", MasterSessionRevokeView.as_view(), name="master-sessions-revoke"),
    path("api/master/audit/", AuditListView.as_view(), name="audit-list"),
    path("api/catalog/", include("apps.catalog.urls")),
    path("api/v1/", include("apps.catalog.urls")),
    path("api/v1/", include("apps.tenancy.urls")),
    path("api/v1/", include("apps.delivery.urls")),
    path("api/v1/", include("apps.orders.urls")),
    path("api/v1/", include("apps.closing.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/public/", include("apps.catalog.urls_public")),
    path("api/public/<slug:slug>/", include("apps.orders.urls_public")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
