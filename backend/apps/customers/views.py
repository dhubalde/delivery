from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.auth import CustomerJWTAuthentication, get_tokens_for_customer
from apps.customers.models import Customer
from apps.tenancy.models import Merchant


def _check_customer_auth_gate():
    if not getattr(settings, "CUSTOMER_AUTH_ENABLED", True):
        from django.http import Http404

        raise Http404("Customer auth disabled")


def _get_merchant_by_slug_or_404(slug):
    """Resolve active merchant by slug or 404. Includes inactive check."""
    merchant = Merchant.all_objects.filter(slug=slug).first()
    if merchant is None:
        from django.http import Http404

        raise Http404(f"No Merchant matches the given query. slug={slug}")
    if merchant.deleted_at is not None or not merchant.is_active:
        from django.http import Http404

        raise Http404(f"No Merchant matches the given query. slug={slug} (inactive)")
    # Also ensure live manager can find it — but inactive check above covers.
    return merchant


class CustomerRegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, slug):
        _check_customer_auth_gate()
        merchant = _get_merchant_by_slug_or_404(slug)
        data = request.data or {}
        phone = (data.get("phone") or "").strip()
        name = (data.get("name") or "").strip()
        password = data.get("password") or ""
        if not phone or not name or not password:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "phone, name, password required"}}, status=400)
        if len(password) < 6:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "password too short"}}, status=400)
        if Customer.objects.filter(merchant=merchant, phone=phone).exists():
            return Response({"error": {"code": "CONFLICT", "message": "Phone already registered for this merchant"}}, status=409)
        customer = Customer(merchant=merchant, phone=phone, name=name)
        customer.set_password(password)
        customer.save()
        tokens = get_tokens_for_customer(customer)
        return Response(
            {
                "customer": {"id": customer.pk, "phone": customer.phone, "name": customer.name, "merchant_slug": merchant.slug, "merchant_id": merchant.pk},
                "tokens": tokens,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            },
            status=201,
        )


class CustomerLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, slug):
        _check_customer_auth_gate()
        merchant = _get_merchant_by_slug_or_404(slug)
        data = request.data or {}
        phone = (data.get("phone") or "").strip()
        password = data.get("password") or ""
        if not phone or not password:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "phone and password required"}}, status=400)
        try:
            customer = Customer.objects.get(merchant=merchant, phone=phone)
        except Customer.DoesNotExist:
            return Response({"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid phone or password"}}, status=401)
        if not customer.check_password(password):
            return Response({"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid phone or password"}}, status=401)
        tokens = get_tokens_for_customer(customer)
        return Response(
            {
                "customer": {"id": customer.pk, "phone": customer.phone, "name": customer.name, "merchant_slug": merchant.slug, "merchant_id": merchant.pk},
                "tokens": tokens,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            },
            status=200,
        )


class CustomerMeView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def get(self, request, slug):
        _check_customer_auth_gate()
        merchant = _get_merchant_by_slug_or_404(slug)
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Customer "):
            return Response({"error": {"code": "AUTH_REQUIRED", "message": "Customer token required"}}, status=401)
        token_str = header.split(" ", 1)[1].strip()
        try:
            from rest_framework_simplejwt.tokens import AccessToken

            token = AccessToken(token_str)
        except Exception:
            return Response({"error": {"code": "INVALID_TOKEN", "message": "Invalid Customer token"}}, status=401)
        mid = token.get("mid")
        cid = token.get("cid")
        if mid is None or cid is None:
            return Response({"error": {"code": "INVALID_TOKEN", "message": "Missing mid/cid"}}, status=401)
        try:
            mid = int(mid)
            cid = int(cid)
        except Exception:
            return Response({"error": {"code": "INVALID_TOKEN", "message": "Invalid mid/cid"}}, status=401)
        if mid != merchant.pk:
            return Response({"error": {"code": "TENANT_MISMATCH", "message": "Customer token not valid for this merchant"}}, status=403)
        try:
            customer = Customer.objects.get(pk=cid, merchant_id=mid)
        except Customer.DoesNotExist:
            return Response({"error": {"code": "NOT_FOUND", "message": "Customer not found"}}, status=404)
        return Response(
            {
                "id": customer.pk,
                "phone": customer.phone,
                "name": customer.name,
                "merchant_slug": merchant.slug,
                "merchant_id": merchant.pk,
                "merchant": merchant.slug,
            },
            status=200,
        )
