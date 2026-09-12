from django.urls import path

from apps.customers.views import CustomerLoginView, CustomerMeView, CustomerRegisterView

urlpatterns = [
    path("customers/register", CustomerRegisterView.as_view(), name="customer-register"),
    path("customers/register/", CustomerRegisterView.as_view(), name="customer-register-slash"),
    path("customers/login", CustomerLoginView.as_view(), name="customer-login"),
    path("customers/login/", CustomerLoginView.as_view(), name="customer-login-slash"),
    path("customers/me", CustomerMeView.as_view(), name="customer-me"),
    path("customers/me/", CustomerMeView.as_view(), name="customer-me-slash"),
]
