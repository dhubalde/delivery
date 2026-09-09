import base64
import hashlib
import json

from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from apps.common.context import set_tenant_merchant_id, tenant_merchant_id


def _verified_jwt_payload(request):
    """Decode AND verify the Bearer JWT signature. Returns payload dict or None."""
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        from rest_framework_simplejwt.tokens import UntypedToken

        return dict(UntypedToken(token).payload)
    except Exception:
        return None


def _decode_jwt_merchant_id(request):
    payload = _verified_jwt_payload(request)
    if not payload:
        return None
    try:
        mid = payload.get("merchant_id")
        if mid is not None:
            return int(mid)
    except Exception:
        return None
    return None


def _is_tenant_api_path(path):
    return path.startswith("/api/v1/") or path.startswith("/api/catalog/") or path.startswith("/api/master/")


def _is_public_path(path):
    return (
        path.startswith("/api/public/")
        or path.startswith("/api/auth/")
        or path.startswith("/admin/")
    )


PASSWORD_CHANGE_PATHS = (
    "/api/v1/users/change-password/",
    "/api/v1/users/reset-confirm/",
    "/api/auth/token/",
    "/api/auth/token/refresh/",
)


def _password_change_required(path):
    return not path.startswith(PASSWORD_CHANGE_PATHS)


def _session_revoked(payload):
    jti = (payload or {}).get("jti")
    if not jti:
        return False
    try:
        from apps.tenancy.models import SessionRecord

        return SessionRecord.objects.filter(jti=jti, revoked_at__isnull=False).exists()
    except Exception:
        return False


def _must_change_password(payload):
    user_id = (payload or {}).get("user_id")
    if not user_id:
        return False
    try:
        from apps.tenancy.models import PlatformUser
        from django.contrib.auth.models import User

        user = User.objects.filter(pk=user_id).first()
        if user is None:
            return False
        profile = getattr(user, "platform_profile", None)
        return bool(profile and profile.must_change_password)
    except Exception:
        return False


class TenantContextMiddleware(MiddlewareMixin):
    def process_request(self, request):
        from django.conf import settings

        path = request.path or ""
        payload = _verified_jwt_payload(request)
        if payload is not None:
            # A platform (master) token MUST never act as a tenant.
            # Master routes are the exception: masters operate there.
            if (
                payload.get("merchant_id") is None
                and _is_tenant_api_path(path)
                and not path.startswith("/api/master/")
            ):
                return JsonResponse(
                    {"error": {"code": "MASTER_TENANT_FORBIDDEN", "message": "Master tokens are only valid on /master/* routes."}},
                    status=403,
                )
            revoked = _session_revoked(payload)
            if revoked:
                return JsonResponse(
                    {"error": {"code": "SESSION_REVOKED", "message": "Session was revoked by a newer login."}},
                    status=401,
                )
            must_change = _must_change_password(payload)
            if must_change and _password_change_required(path):
                return JsonResponse(
                    {"error": {"code": "PASSWORD_CHANGE_REQUIRED", "message": "Change your password first."}},
                    status=403,
                )
            mid = _decode_jwt_merchant_id(request)
            set_tenant_merchant_id(mid)
            request.tenant_merchant_id = mid
            return None
        if getattr(settings, "AUTH_V2", False) and _is_tenant_api_path(path) and not _is_public_path(path):
            return JsonResponse(
                {"error": {"code": "AUTH_REQUIRED", "message": "Valid JWT required."}},
                status=401,
            )
        mid = None
        header_mid = request.META.get("HTTP_X_MERCHANT_ID")
        if header_mid:
            try:
                mid = int(header_mid)
            except ValueError:
                mid = None
        if mid is None:
            path = request.path or ""
            if path.startswith("/api/public/"):
                parts = path.strip("/").split("/")
                if len(parts) >= 3:
                    slug = parts[2]
                    try:
                        from apps.tenancy.models import Merchant

                        m = Merchant.all_objects.filter(slug=slug).first()
                        if m is None:
                            m = Merchant.objects.filter(slug=slug).first()
                        if m:
                            mid = m.pk
                    except Exception:
                        mid = None
        set_tenant_merchant_id(mid)
        request.tenant_merchant_id = mid

    def process_response(self, request, response):
        set_tenant_merchant_id(None)
        return response


class IdempotencyMiddleware(MiddlewareMixin):
    MUTATING = {"POST", "PUT", "PATCH", "DELETE"}

    def process_request(self, request):
        if request.method not in self.MUTATING:
            return None
        key = request.META.get("HTTP_IDEMPOTENCY_KEY") or request.META.get("HTTP_IDEMPOTENCY-KEY")
        if not key:
            return None
        endpoint = request.path
        body = request.body or b""
        req_hash = hashlib.sha256(body).hexdigest()
        from apps.common.models import IdempotencyKey

        try:
            existing = IdempotencyKey.objects.filter(key=key, endpoint=endpoint).first()
        except Exception:
            return None
        if existing is None:
            request._idempotency_key = key
            request._idempotency_endpoint = endpoint
            request._idempotency_hash = req_hash
            return None
        if existing.request_hash != req_hash:
            return JsonResponse(
                {"error": {"code": "IDEMPOTENCY_KEY_REUSED", "message": "Idempotency-Key already used with different payload"}},
                status=409,
            )
        cached = existing.response_snapshot or {}
        body_cached = cached.get("body")
        status = existing.status_code or 200
        content_type = cached.get("content_type", "application/json")
        if isinstance(body_cached, (dict, list)):
            resp = JsonResponse(body_cached, status=status)
            resp["Idempotency-Replayed"] = "true"
            return resp
        if isinstance(body_cached, str):
            resp = HttpResponse(body_cached, status=status, content_type=content_type)
            resp["Idempotency-Replayed"] = "true"
            return resp
        resp = JsonResponse(cached, status=status)
        resp["Idempotency-Replayed"] = "true"
        return resp

    def process_response(self, request, response):
        key = getattr(request, "_idempotency_key", None)
        if not key:
            return response
        endpoint = getattr(request, "_idempotency_endpoint", request.path)
        req_hash = getattr(request, "_idempotency_hash", "")
        from apps.common.models import IdempotencyKey

        try:
            body = response.content.decode() if hasattr(response, "content") else ""
            try:
                parsed = json.loads(body) if body else {}
            except Exception:
                parsed = {"raw": body}
            snapshot = {"body": parsed, "content_type": response.get("Content-Type", "application/json")}
            mid = getattr(request, "tenant_merchant_id", None)
            if mid is None:
                mid = tenant_merchant_id.get()
            IdempotencyKey.objects.get_or_create(
                key=key,
                endpoint=endpoint,
                defaults={
                    "merchant_id": mid,
                    "request_hash": req_hash,
                    "response_snapshot": snapshot,
                    "status_code": response.status_code,
                },
            )
        except Exception:
            pass
        return response
