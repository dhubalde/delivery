from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.common.utils import get_business_date
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.closing.models import CashClosure
from apps.closing.services import AlreadyClosedError, CashClosureService, NotAdminError
from apps.orders.models import Order
from apps.payments.models import Payment


def _resolve_merchant_id(request):
    mid = getattr(request, "tenant_merchant_id", None)
    if mid is not None:
        return mid
    slug = request.query_params.get("merchant_slug") or request.headers.get("X-Merchant-Slug") or request.META.get("HTTP_X_MERCHANT_SLUG")
    if slug:
        try:
            from apps.tenancy.models import Merchant
            m = Merchant.objects.filter(slug=slug).first()
            if m:
                return m.pk
            m = Merchant.all_objects.filter(slug=slug).first()
            if m:
                return m.pk
        except Exception:
            pass
    raw = request.query_params.get("merchant_id") or request.headers.get("X-Merchant-Id") or request.META.get("HTTP_X_MERCHANT_ID")
    if raw:
        try:
            return int(raw)
        except (ValueError, TypeError):
            return None
    return None


def _resolve_cashier(request, merchant_id):
    from apps.tenancy.models import Employee
    eid = request.headers.get("X-Employee-Id") or request.META.get("HTTP_X_EMPLOYEE_ID")
    if not eid:
        eid = request.headers.get("X-Cashier-Id") or request.META.get("HTTP_X_CASHIER_ID")
    if not eid:
        eid = request.query_params.get("employee_id") or request.query_params.get("cashier_id")
    if eid:
        try:
            emp = Employee.objects.filter(pk=int(eid), merchant_id=merchant_id).first()
            if emp:
                return emp
        except Exception:
            pass
    from apps.tenancy.models import EmployeeRole
    admin_ids = EmployeeRole.objects.filter(role=EmployeeRole.Role.ADMIN, employee__merchant_id=merchant_id, employee__is_active=True).values_list("employee_id", flat=True)
    emp = Employee.objects.filter(pk__in=list(admin_ids), merchant_id=merchant_id, is_active=True).first()
    if emp:
        return emp
    return Employee.objects.filter(merchant_id=merchant_id, is_active=True).first()


def _parse_business_date(request):
    raw = request.query_params.get("business_date")
    if raw:
        try:
            from datetime import date as _date
            return _date.fromisoformat(raw)
        except Exception:
            pass
    return get_business_date()


def _parse_business_date_range(request):
    """Parse optional business_date and business_date_to query params into a (start, end) tuple."""
    from datetime import date as _date
    start_raw = request.query_params.get("business_date")
    end_raw = request.query_params.get("business_date_to")
    try:
        start = _date.fromisoformat(start_raw) if start_raw else None
    except Exception:
        start = None
    try:
        end = _date.fromisoformat(end_raw) if end_raw else None
    except Exception:
        end = None
    if start is None and end is None:
        today = get_business_date()
        return today, today
    if start is None:
        start = end
    if end is None:
        end = start
    return start, end


def _compute_preview(merchant, start_date, end_date):
    def _sum(method):
        result = Payment.objects.filter(
            order__merchant=merchant,
            order__business_date__gte=start_date,
            order__business_date__lte=end_date,
            method=method,
            status=Payment.Status.CONFIRMED,
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0.00")
    total_efectivo = _sum(Payment.Method.EFECTIVO)
    total_billeteras = _sum(Payment.Method.BILLETERA)
    total_tarjetas = _sum(Payment.Method.TARJETA)
    total_entregados = Order.objects.filter(
        merchant=merchant,
        business_date__gte=start_date,
        business_date__lte=end_date,
        state=Order.State.ENTREGADO,
    ).count()
    total_rechazados = Order.objects.filter(
        merchant=merchant,
        business_date__gte=start_date,
        business_date__lte=end_date,
        state=Order.State.CANCELADO,
    ).count()
    def _fmt(d):
        return format(d.quantize(Decimal("0.00")), "f")
    total = total_efectivo + total_billeteras + total_tarjetas
    totals = {
        "EFECTIVO": _fmt(total_efectivo),
        "BILLETERAS_VIRTUALES": _fmt(total_billeteras),
        "TARJETAS": _fmt(total_tarjetas),
        "TOTAL": _fmt(total),
        "TOTAL_ENTREGADOS": total_entregados,
        "TOTAL_RECHAZADOS": total_rechazados,
    }
    return totals


class CashCloseView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        mid = _resolve_merchant_id(request)
        if mid is None:
            return Response({"error": {"code": "MERCHANT_REQUIRED", "message": "merchant context required"}}, status=400)
        from apps.tenancy.models import Merchant
        merchant = Merchant.objects.filter(pk=mid).first() or Merchant.all_objects.filter(pk=mid).first()
        if merchant is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "Merchant not found"}}, status=404)
        start_date, end_date = _parse_business_date_range(request)
        closure = CashClosure.objects.filter(merchant=merchant, business_date=start_date).first()
        if closure is not None:
            totals = closure.ticket_payload.get("totals") if closure.ticket_payload else None
            if not totals:
                totals = {
                    "EFECTIVO": format(closure.total_efectivo, ".2f"),
                    "BILLETERAS_VIRTUALES": format(closure.total_billeteras, ".2f"),
                    "TARJETAS": format(closure.total_tarjetas, ".2f"),
                    "TOTAL": format(closure.total_efectivo + closure.total_billeteras + closure.total_tarjetas, ".2f"),
                    "TOTAL_ENTREGADOS": closure.total_entregados,
                    "TOTAL_RECHAZADOS": closure.total_rechazados,
                }
            elif "TOTAL" not in totals:
                try:
                    _t = Decimal(totals.get("EFECTIVO", "0")) + Decimal(totals.get("BILLETERAS_VIRTUALES", "0")) + Decimal(totals.get("TARJETAS", "0"))
                    totals = {**totals, "TOTAL": format(_t.quantize(Decimal("0.00")), "f")}
                except Exception:
                    pass
            return Response({
                "totals": totals,
                "ticket_payload": closure.ticket_payload,
                "already_closed": True,
                "id": closure.pk,
                "business_date": str(closure.business_date),
            }, status=200)
        totals = _compute_preview(merchant, start_date, end_date)
        cashier = _resolve_cashier(request, merchant.pk)
        date_str = f"{start_date.isoformat()} to {end_date.isoformat()}" if start_date != end_date else start_date.isoformat()
        ticket_preview = {
            "merchant_id": merchant.pk,
            "merchant_slug": getattr(merchant, "slug", ""),
            "business_date": date_str,
            "cashier_id": getattr(cashier, "pk", None),
            "cashier_name": getattr(cashier, "display_name", "") if cashier else "",
            "totals": totals,
            "closed_at": None,
        }
        return Response({"totals": totals, "ticket_payload": ticket_preview, "already_closed": False}, status=200)

    def post(self, request):
        mid = _resolve_merchant_id(request)
        if mid is None:
            return Response({"error": {"code": "MERCHANT_REQUIRED", "message": "merchant context required"}}, status=400)
        from apps.tenancy.models import Merchant
        merchant = Merchant.objects.filter(pk=mid).first() or Merchant.all_objects.filter(pk=mid).first()
        if merchant is None:
            return Response({"error": {"code": "NOT_FOUND", "message": "Merchant not found"}}, status=404)
        business_date = get_business_date()
        cashier = _resolve_cashier(request, merchant.pk)
        try:
            closure = CashClosureService.close(merchant, business_date, cashier)
        except NotAdminError as e:
            return Response({"error": {"code": "FORBIDDEN", "message": str(e)}}, status=403)
        except AlreadyClosedError as e:
            return Response({"error": {"code": "ALREADY_CLOSED", "message": str(e)}}, status=409)
        return Response({
            "id": closure.pk,
            "business_date": str(closure.business_date),
            "totals": closure.ticket_payload.get("totals"),
            "ticket_payload": closure.ticket_payload,
            "already_closed": True,
        }, status=201)
