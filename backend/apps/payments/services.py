from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.payments.gateways.mercado_pago import MercadoPagoError, MercadoPagoGateway
from apps.payments.gateways.mercadopago_mock import MercadoPagoMockGateway
from apps.payments.models import Payment


class PaymentValidationError(Exception):
    pass


class CashConfirmationError(Exception):
    pass


class MPNotConfiguredError(Exception):
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
        from apps.audit.services import emit

        for pay in created:
            emit(
                merchant_id=order.merchant_id,
                actor=actor,
                entity="Payment",
                entity_id=pay.pk,
                action="PAYMENT",
                old_value=None,
                new_value={"method": pay.method, "amount": str(pay.amount), "status": pay.status},
            )
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
        from apps.audit.services import emit

        emit(
            merchant_id=payment.order.merchant_id,
            actor=cashier_user,
            entity="Payment",
            entity_id=payment.pk,
            action="CASH_MOVEMENT",
            old_value={"status": Payment.Status.PENDING},
            new_value={"status": Payment.Status.CONFIRMED, "collected_by": payment.collected_by},
        )
        return payment

    @staticmethod
    @transaction.atomic
    def confirm_transfer(payment_id, confirmed_by=None):
        """Operator confirms a manual bank-transfer payment after seeing the deposit."""
        payment = Payment.objects.select_for_update().get(pk=payment_id)
        if not getattr(payment, "order", None):
            raise CashConfirmationError("Payment has no order")
        if payment.method != Payment.Method.TRANSFER:
            raise CashConfirmationError("Only TRANSFER payments can be confirmed via this flow")
        if payment.status != Payment.Status.PENDING:
            raise CashConfirmationError(f"Payment status is {payment.status}, expected PENDING")
        payment.status = Payment.Status.CONFIRMED
        payment.confirmed_at = timezone.now()
        if confirmed_by is not None:
            payment.collected_by = str(confirmed_by)
        payment.save(update_fields=["status", "confirmed_at", "collected_by", "updated_at"])
        from apps.audit.services import emit

        emit(
            merchant_id=payment.order.merchant_id,
            actor=confirmed_by,
            entity="Payment",
            entity_id=payment.pk,
            action="PAYMENT",
            old_value={"status": Payment.Status.PENDING, "method": Payment.Method.TRANSFER},
            new_value={"status": Payment.Status.CONFIRMED, "collected_by": payment.collected_by},
        )
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
    def create_checkout(order, *, success_url: str, notification_url: str) -> Payment:
        """Create (or reuse) the Mercado Pago Checkout Pro preference for an
        order's pending ONLINE payment. Reusing an existing preference keeps
        this endpoint idempotent without any extra key."""
        payment = order.payments.filter(
            method=Payment.Method.ONLINE, status=Payment.Status.PENDING
        ).first()
        try:
            gateway = MercadoPagoGateway.for_merchant(order.merchant)
        except MercadoPagoError as e:
            raise MPNotConfiguredError(str(e))
        if payment is None:
            raise PaymentValidationError("Order is not waiting for an online payment")
        if payment.checkout_url and payment.gateway_ref:
            return payment
        try:
            gateway = MercadoPagoGateway.for_merchant(order.merchant)
        except MercadoPagoError as e:
            raise MPNotConfiguredError(str(e))
        preference = gateway.create_preference(
            items=[
                {
                    "title": f"Pedido #{order.code}",
                    "quantity": 1,
                    "unit_price": float(order.total),
                    "currency_id": "ARS",
                }
            ],
            external_reference=str(order.pk),
            back_urls={
                "success": success_url,
                "failure": success_url,
                "pending": success_url,
            },
            notification_url=notification_url,
        )
        payment.checkout_url = preference["init_point"]
        payment.gateway_ref = preference["id"]
        payment.save(update_fields=["checkout_url", "gateway_ref", "updated_at"])
        return payment

    @staticmethod
    def fetch_gateway_payment(merchant, data_id) -> dict:
        """Fetch a payment resource from Mercado Pago via the merchant's own
        gateway (kept on the service so tests can stub it in one place)."""
        gateway = MercadoPagoGateway.for_merchant(merchant)
        return gateway.get_payment(data_id)

    @staticmethod
    def apply_gateway_result(order, mp_payment: dict) -> Payment:
        """Update the order's ONLINE payment from a Mercado Pago payment
        resource (webhook or manual fetch). Idempotent: terminal payments are
        never overwritten."""
        from django.db import transaction

        from apps.audit.services import emit

        with transaction.atomic():
            payment = (
                order.payments.select_for_update()
                .filter(method=Payment.Method.ONLINE)
                .first()
            )
            if payment is None:
                raise PaymentValidationError("Order has no online payment")
            if payment.status in (Payment.Status.CONFIRMED, Payment.Status.REJECTED):
                return payment
            payment.status = mp_payment["status"]
            payment.method = mp_payment["method"]
            if mp_payment.get("mp_id"):
                payment.gateway_ref = mp_payment["mp_id"]
            if payment.status == Payment.Status.CONFIRMED:
                payment.confirmed_at = timezone.now()
            payment.save(
                update_fields=["status", "method", "gateway_ref", "confirmed_at", "updated_at"]
            )
            emit(
                merchant_id=order.merchant_id,
                actor=None,
                entity="Payment",
                entity_id=payment.pk,
                action="PAYMENT",
                old_value={"status": Payment.Status.PENDING},
                new_value={"status": payment.status, "method": payment.method, "gateway_ref": payment.gateway_ref},
            )
            return payment

    @staticmethod
    def validate_online_paid(order) -> None:
        """An order with an unpaid ONLINE payment cannot leave the intake
        state: it becomes workable only once Mercado Pago confirms the charge."""
        from apps.orders.state_machine import GuardViolationError

        pending_online = order.payments.filter(
            method=Payment.Method.ONLINE, status=Payment.Status.PENDING
        ).exists()
        if pending_online:
            raise GuardViolationError(
                "Order has a pending online payment; it enters the board once Mercado Pago confirms it"
            )

    @staticmethod
    def efectivo_confirmed_total(order):
        return sum(
            p.amount for p in order.payments.filter(method=Payment.Method.EFECTIVO, status=Payment.Status.CONFIRMED)
        )
