from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.payments.gateways.mercadopago_mock import MercadoPagoMockGateway
from apps.payments.models import Payment


class PaymentValidationError(Exception):
    pass


class CashConfirmationError(Exception):
    pass


class PaymentService:
    @staticmethod
    @transaction.atomic
    def declare_payments(order, payments_data, actor=None):
        if not payments_data:
            raise PaymentValidationError("At least one payment method required (BR-PAY-01)")
        total_declared = sum(Decimal(str(p["amount"])) for p in payments_data)
        if total_declared != order.total:
            raise PaymentValidationError(
                f"Payment amounts sum {total_declared} != order total {order.total} (BR-PAY-05)"
            )
        allowed = {c[0] for c in Payment.Method.choices}
        created = []
        for p in payments_data:
            method = p["method"]
            amount = Decimal(str(p["amount"]))
            if method not in allowed:
                raise PaymentValidationError(f"Invalid method {method}")
            if amount <= Decimal("0"):
                raise PaymentValidationError("Amount must be > 0")
            if method == Payment.Method.EFECTIVO:
                pay = Payment.objects.create(
                    order=order,
                    method=method,
                    amount=amount,
                    status=Payment.Status.PENDING,
                )
                created.append(pay)
            else:
                gw = MercadoPagoMockGateway.process(method, amount, order_id=order.pk)
                status = Payment.Status.CONFIRMED if gw["status"] == "CONFIRMED" else Payment.Status.REJECTED
                pay = Payment.objects.create(
                    order=order,
                    method=method,
                    amount=amount,
                    status=status,
                    gateway_ref=gw.get("gateway_ref"),
                )
                created.append(pay)
        if any(m == Payment.Method.EFECTIVO for m in [p["method"] for p in payments_data]):
            order.cash_declared = True
            order.save(update_fields=["cash_declared", "updated_at"])
        return created

    @staticmethod
    @transaction.atomic
    def confirm_cash(payment_id, cashier_user=None):
        payment = Payment.objects.select_for_update().get(pk=payment_id)
        if payment.method != Payment.Method.EFECTIVO:
            raise CashConfirmationError("Only EFECTIVO payments can be confirmed via cash flow")
        if payment.status != Payment.Status.PENDING:
            raise CashConfirmationError(f"Payment status is {payment.status}, expected PENDING")
        payment.status = Payment.Status.CONFIRMED
        payment.confirmed_at = timezone.now()
        if cashier_user is not None:
            payment.collected_by = str(cashier_user)
        payment.save(update_fields=["status", "confirmed_at", "collected_by", "updated_at"])
        return payment

    @staticmethod
    @transaction.atomic
    def reject_cash(payment_id, cashier_user=None):
        payment = Payment.objects.select_for_update().get(pk=payment_id)
        if payment.method != Payment.Method.EFECTIVO:
            raise CashConfirmationError("Only EFECTIVO payments can be rejected via cash flow")
        if payment.status != Payment.Status.PENDING:
            raise CashConfirmationError(f"Payment status is {payment.status}, expected PENDING")
        payment.status = Payment.Status.REJECTED
        if cashier_user is not None:
            payment.collected_by = str(cashier_user)
        payment.save(update_fields=["status", "collected_by", "updated_at"])
        return payment

    @staticmethod
    @transaction.atomic
    def collect_cash_by_courier(payment_id, courier_user=None):
        payment = Payment.objects.select_for_update().get(pk=payment_id)
        if payment.method != Payment.Method.EFECTIVO:
            raise CashConfirmationError("Only EFECTIVO can be collected by courier")
        if payment.status != Payment.Status.PENDING:
            raise CashConfirmationError("Payment must be PENDING to mark collected")
        if courier_user is not None:
            payment.collected_by = str(courier_user)
            payment.save(update_fields=["collected_by", "updated_at"])
        return payment

    @staticmethod
    def validate_for_logistics(order):
        payments = list(order.payments.all())
        if not payments:
            raise PaymentValidationError("FACTURACION->LOGISTICA requires at least one payment (BR-PAY-04/06)")
        total = sum(p.amount for p in payments)
        if total != order.total:
            raise PaymentValidationError(f"Payments sum {total} != order total {order.total} (BR-PAY-05)")
        for p in payments:
            if p.status == Payment.Status.REJECTED:
                raise PaymentValidationError(f"Payment {p.pk} is REJECTED (BR-PAY-07)")
            if p.method in (Payment.Method.BILLETERA, Payment.Method.TARJETA):
                if p.status != Payment.Status.CONFIRMED:
                    raise PaymentValidationError(f"Digital payment {p.pk} must be CONFIRMED")
        cash_payments = [p for p in payments if p.method == Payment.Method.EFECTIVO]
        if cash_payments and order.fulfillment == order.Fulfillment.PICKUP:
            for cp in cash_payments:
                if cp.status != Payment.Status.CONFIRMED:
                    raise PaymentValidationError(
                        "PICKUP cash must be CONFIRMED before LOGISTICA (BR-PAY-06)"
                    )

    @staticmethod
    def efectivo_confirmed_total(order):
        return sum(
            p.amount for p in order.payments.filter(method=Payment.Method.EFECTIVO, status=Payment.Status.CONFIRMED)
        )
