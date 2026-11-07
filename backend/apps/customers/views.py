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


def _validate_email(value):
    from django.core.validators import validate_email as _dj_validate
    from django.core.exceptions import ValidationError as _DjValidationError

    try:
        _dj_validate(value)
    except _DjValidationError:
        return False
    return True


def _validate_address(value):
    """Address must include a street number (same rule as checkout)."""
    import re

    text = (value or "").strip()
    if not text:
        return False
    return re.search(r"\d", text) is not None


def _customer_payload(customer, merchant):
    return {
        "id": customer.pk,
        "email": customer.email,
        "phone": customer.phone,
        "name": customer.name,
        "default_address": customer.default_address,
        "merchant_slug": merchant.slug,
        "merchant_id": merchant.pk,
    }


class CustomerRegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, slug):
        _check_customer_auth_gate()
        merchant = _get_merchant_by_slug_or_404(slug)
        data = request.data or {}
        email = (data.get("email") or "").strip().lower()
        phone = (data.get("phone") or "").strip()
        name = (data.get("name") or "").strip()
        address = (data.get("default_address") or data.get("address") or "").strip()
        password = data.get("password") or ""
        if not email or not phone or not name or not password or not address:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "email, phone, name, address, password required"}}, status=400)
        if not _validate_email(email):
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "invalid email"}}, status=400)
        if not _validate_address(address):
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "address must include street number"}}, status=400)
        if len(password) < 6:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "password too short"}}, status=400)
        if Customer.objects.filter(merchant=merchant, email=email).exists():
            return Response({"error": {"code": "CONFLICT", "message": "Email already registered for this merchant"}}, status=409)
        if Customer.objects.filter(merchant=merchant, phone=phone).exists():
            return Response({"error": {"code": "CONFLICT", "message": "Phone already registered for this merchant"}}, status=409)
        customer = Customer(merchant=merchant, email=email, phone=phone, name=name, default_address=address)
        customer.set_password(password)
        customer.save()
        tokens = get_tokens_for_customer(customer)
        return Response(
            {
                "customer": _customer_payload(customer, merchant),
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
        identifier = (data.get("email") or data.get("phone") or "").strip()
        password = data.get("password") or ""
        if not identifier or not password:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "email (or phone) and password required"}}, status=400)
        customer = Customer.objects.filter(merchant=merchant, email=identifier.lower()).first()
        if customer is None:
            customer = Customer.objects.filter(merchant=merchant, phone=identifier).first()
        if customer is None:
            return Response({"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}}, status=401)
        if not customer.check_password(password):
            return Response({"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}}, status=401)
        tokens = get_tokens_for_customer(customer)
        return Response(
            {
                "customer": _customer_payload(customer, merchant),
                "tokens": tokens,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            },
            status=200,
        )


class CustomerMeView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    http_method_names = ["get", "patch"]

    def _get_customer(self, request, slug):
        _check_customer_auth_gate()
        merchant = _get_merchant_by_slug_or_404(slug)
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Customer "):
            return None, Response({"error": {"code": "AUTH_REQUIRED", "message": "Customer token required"}}, status=401)
        token_str = header.split(" ", 1)[1].strip()
        try:
            from rest_framework_simplejwt.tokens import AccessToken

            token = AccessToken(token_str)
        except Exception:
            return None, Response({"error": {"code": "INVALID_TOKEN", "message": "Invalid Customer token"}}, status=401)
        mid = token.get("mid")
        cid = token.get("cid")
        if mid is None or cid is None:
            return None, Response({"error": {"code": "INVALID_TOKEN", "message": "Missing mid/cid"}}, status=401)
        try:
            mid = int(mid)
            cid = int(cid)
        except Exception:
            return None, Response({"error": {"code": "INVALID_TOKEN", "message": "Invalid mid/cid"}}, status=401)
        if mid != merchant.pk:
            return None, Response({"error": {"code": "TENANT_MISMATCH", "message": "Customer token not valid for this merchant"}}, status=403)
        try:
            customer = Customer.objects.get(pk=cid, merchant_id=mid)
        except Customer.DoesNotExist:
            return None, Response({"error": {"code": "NOT_FOUND", "message": "Customer not found"}}, status=404)
        return (merchant, customer), None

    def get(self, request, slug):
        result, error = self._get_customer(request, slug)
        if error is not None:
            return error
        merchant, customer = result
        payload = _customer_payload(customer, merchant)
        payload["merchant"] = merchant.slug
        return Response(payload, status=200)

    def patch(self, request, slug):
        """Update editable profile fields: name, phone, default_address."""
        result, error = self._get_customer(request, slug)
        if error is not None:
            return error
        merchant, customer = result
        data = request.data or {}
        if "name" in data:
            name = (data.get("name") or "").strip()
            if not name:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": "name cannot be empty"}}, status=400)
            customer.name = name
        if "phone" in data:
            phone = (data.get("phone") or "").strip()
            if not phone:
                return Response({"error": {"code": "VALIDATION_ERROR", "message": "phone cannot be empty"}}, status=400)
            if Customer.objects.filter(merchant=merchant, phone=phone).exclude(pk=customer.pk).exists():
                return Response({"error": {"code": "CONFLICT", "message": "Phone already registered for this merchant"}}, status=409)
            customer.phone = phone
        if "default_address" in data or "address" in data:
            address = (data.get("default_address") or data.get("address") or "").strip()
            if not _validate_address(address):
                return Response({"error": {"code": "VALIDATION_ERROR", "message": "address must include street number"}}, status=400)
            customer.default_address = address
        customer.save()
        return Response(_customer_payload(customer, merchant), status=200)
