import base64
import hashlib
import json

from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from apps.common.context import set_tenant_merchant_id, tenant_merchant_id


def _decode_jwt_merchant_id(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
        mid = payload.get("merchant_id") or payload.get("merchant")
        if mid is not None:
            return int(mid)
    except Exception:
        return None
    return None


class TenantContextMiddleware(MiddlewareMixin):
    def process_request(self, request):
        mid = None
        header_mid = request.META.get("HTTP_X_MERCHANT_ID")
        if header_mid:
            try:
                mid = int(header_mid)
            except ValueError:
                mid = None
        if mid is None:
            mid = _decode_jwt_merchant_id(request)
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
