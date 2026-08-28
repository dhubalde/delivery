from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.orders.models import Order
from apps.payments.models import Payment
from apps.tenancy.models import EmployeeRole
from apps.tenancy.services.roles import has_role


class ClosureError(Exception):
    pass


class NotAdminError(ClosureError):
    pass


class AlreadyClosedError(ClosureError):
    pass


class CashClosureService:
    @staticmethod
    @transaction.atomic
    def close(merchant, business_date, cashier):
        if cashier is None:
            raise NotAdminError("Cashier required")
        if getattr(cashier, "deleted_at", None) is not None or not getattr(cashier, "is_active", True):
            raise NotAdminError("Cashier inactive or deleted")
        if cashier.merchant_id != merchant.pk:
            raise NotAdminError("Cashier does not belong to merchant")
        if not has_role(cashier, EmployeeRole.Role.ADMIN):
            raise NotAdminError("Only ADMIN can close cash (BR-CIE-01)")

        from apps.closing.models import CashClosure

        if CashClosure.objects.filter(merchant=merchant, business_date=business_date).exists():
            raise AlreadyClosedError(f"Already closed for {business_date}")

        def _sum(method):
            result = Payment.objects.filter(
                order__merchant=merchant,
                order__business_date=business_date,
                method=method,
                status=Payment.Status.CONFIRMED,
            ).aggregate(total=Sum("amount"))
            return result["total"] or Decimal("0.00")

        total_efectivo = _sum(Payment.Method.EFECTIVO)
        total_billeteras = _sum(Payment.Method.BILLETERA)
        total_tarjetas = _sum(Payment.Method.TARJETA)

        total_entregados = Order.objects.filter(
            merchant=merchant, business_date=business_date, state=Order.State.ENTREGADO
        ).count()

        total_rechazados = Order.objects.filter(
            merchant=merchant, business_date=business_date, state=Order.State.CANCELADO
        ).count()

        def _fmt(d):
            return format(d.quantize(Decimal("0.00")), "f")

        ticket_payload = {
            "merchant_id": merchant.pk,
            "merchant_slug": getattr(merchant, "slug", ""),
            "business_date": business_date.isoformat() if hasattr(business_date, "isoformat") else str(business_date),
            "cashier_id": cashier.pk,
            "cashier_name": cashier.display_name,
            "totals": {
                "EFECTIVO": _fmt(total_efectivo),
                "BILLETERAS_VIRTUALES": _fmt(total_billeteras),
                "TARJETAS": _fmt(total_tarjetas),
                "TOTAL_ENTREGADOS": total_entregados,
                "TOTAL_RECHAZADOS": total_rechazados,
            },
            "closed_at": timezone.now().isoformat(),
        }

        closure = CashClosure.objects.create(
            merchant=merchant,
            business_date=business_date,
            cashier=cashier,
            total_efectivo=total_efectivo,
            total_billeteras=total_billeteras,
            total_tarjetas=total_tarjetas,
            total_entregados=total_entregados,
            total_rechazados=total_rechazados,
            ticket_payload=ticket_payload,
        )
        from apps.audit.services import emit

        emit(
            merchant_id=merchant.pk,
            actor=cashier,
            entity="CashClosure",
            entity_id=closure.pk,
            action="CLOSURE",
            old_value=None,
            new_value={"business_date": str(business_date), "totals": ticket_payload["totals"]},
        )
        return closure
