from django.urls import path

from apps.payments.views import PaymentConfirmTransferView

urlpatterns = [
    path("payments/<int:pk>/confirm-transfer", PaymentConfirmTransferView.as_view()),
    path("payments/<int:pk>/confirm-transfer/", PaymentConfirmTransferView.as_view()),
]
