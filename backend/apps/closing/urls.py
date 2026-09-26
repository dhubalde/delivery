from django.urls import path

from apps.closing.views import CashCloseView, CashDailyView

urlpatterns = [
    path("cash/close/", CashCloseView.as_view(), name="cash-close"),
    path("cash/close", CashCloseView.as_view(), name="cash-close-no-slash"),
    path("cash/daily/", CashDailyView.as_view(), name="cash-daily"),
    path("cash/daily", CashDailyView.as_view(), name="cash-daily-no-slash"),
]
