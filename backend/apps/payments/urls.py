from django.urls import path

from apps.payments.views import MercadoPagoWebhookView, OrderPaymentLinkView, PaymentConfirmTransferView

urlpatterns = [
    path("payments/<int:pk>/confirm-transfer", PaymentConfirmTransferView.as_view()),
    path("payments/<int:pk>/confirm-transfer/", PaymentConfirmTransferView.as_view()),
    path("orders/<int:pk>/payment-link", OrderPaymentLinkView.as_view()),
    path("orders/<int:pk>/payment-link/", OrderPaymentLinkView.as_view()),
]
