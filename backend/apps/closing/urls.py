from django.urls import path

from apps.closing.views import CashCloseView

urlpatterns = [
    path("cash/close/", CashCloseView.as_view(), name="cash-close"),
    path("cash/close", CashCloseView.as_view(), name="cash-close-no-slash"),
]
