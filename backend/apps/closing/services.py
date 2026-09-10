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


class NotAllowedError(ClosureError):
    pass


NotAdminError = NotAllowedError


class AlreadyClosedError(ClosureError):
    pass


class CashClosureService:
    @staticmethod
    @transaction.atomic
    def close(merchant, business_date, cashier=None, closed_by=None):
        """Any active employee of the merchant (any role) or any active
        platform user of the merchant may close (rotating shifts)."""
        closed_by = closed_by or {}
        if cashier is not None:
            if getattr(cashier, "deleted_at", None) is not None or not getattr(cashier, "is_active", True):
                raise NotAllowedError("Cashier inactive or deleted")
            if cashier.merchant_id != merchant.pk:
                raise NotAllowedError("Cashier does not belong to merchant")
            closer_name = cashier.display_name
            closer_role = "EMPLOYEE"
            closer_username = ""
        elif closed_by.get("username") and closed_by.get("merchant_id") == merchant.pk:
            closer_name = closed_by["username"]
            closer_role = closed_by.get("role", "")
            closer_username = closed_by["username"]
            cashier = None
        else:
            raise NotAllowedError("Close requires an active employee or user of the merchant")

        from apps.closing.models import CashClosure

        if CashClosure.objects.filter(merchant=merchant, business_date=business_date).exists():
            raise AlreadyClosedError(f"Already closed for {business_date}")

        def _sum(method):
            result = Payment.objects.filter(
                order__merchant=merchant,
                order__business_date=business_date,
                method=method,
                status=Payment.Status.CONFIRMED,
            ).exclude(order__state=Order.State.CANCELADO).aggregate(total=Sum("amount"))
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

        total = total_efectivo + total_billeteras + total_tarjetas
        ticket_payload = {
            "merchant_id": merchant.pk,
            "merchant_slug": getattr(merchant, "slug", ""),
            "business_date": business_date.isoformat() if hasattr(business_date, "isoformat") else str(business_date),
            "cashier_id": cashier.pk if cashier is not None else None,
            "cashier_name": closer_name,
            "closed_by": {"username": closer_username, "role": closer_role},
            "totals": {
                "EFECTIVO": _fmt(total_efectivo),
                "BILLETERAS_VIRTUALES": _fmt(total_billeteras),
                "TARJETAS": _fmt(total_tarjetas),
                "TOTAL": _fmt(total),
                "TOTAL_ENTREGADOS": total_entregados,
                "TOTAL_RECHAZADOS": total_rechazados,
            },
            "closed_at": timezone.now().isoformat(),
        }

        closure = CashClosure.objects.create(
            merchant=merchant,
            business_date=business_date,
            cashier=cashier,
            closed_by_username=closer_username,
            closed_by_role=closer_role,
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
