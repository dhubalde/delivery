from rest_framework import authentication, exceptions
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


def get_tokens_for_customer(customer):
    """Issue SimpleJWT pair with claims mid (merchant id) and cid (customer id).

    Distinct from WorkZoneToken (Bearer) — this token is sent as
    Authorization: Customer <jwt>. Validated without DB session table.
    """
    refresh = RefreshToken()
    refresh["mid"] = customer.merchant_id
    refresh["cid"] = customer.pk
    access = refresh.access_token
    access["mid"] = customer.merchant_id
    access["cid"] = customer.pk
    return {"refresh": str(refresh), "access": str(access)}


class CustomerJWTAuthentication(authentication.BaseAuthentication):
    """Authenticate via `Authorization: Customer <jwt>` with mid/cid claims.

    Distinct prefix prevents collision with PlatformUser Bearer tokens.
    Middleware does not parse Customer prefix, so this class is authoritative.
    """

    keyword = "Customer"

    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header:
            return None
        if not header.startswith(f"{self.keyword} "):
            return None
        token_str = header.split(" ", 1)[1].strip()
        if not token_str:
            raise exceptions.AuthenticationFailed("Invalid Customer token.", code="invalid_token")
        try:
            token = AccessToken(token_str)
        except Exception as exc:
            raise exceptions.AuthenticationFailed(f"Invalid Customer token: {exc}", code="invalid_token")
        mid = token.get("mid")
        cid = token.get("cid")
        if mid is None or cid is None:
            raise exceptions.AuthenticationFailed("Customer token missing mid/cid.", code="invalid_token")
        # Return a lightweight user-like object with merchant/customer ids
        try:
            mid = int(mid)
            cid = int(cid)
        except (TypeError, ValueError):
            raise exceptions.AuthenticationFailed("Invalid mid/cid type.", code="invalid_token")
        # Lazy import to avoid circular
        from apps.customers.models import Customer

        try:
            customer = Customer.objects.get(pk=cid, merchant_id=mid)
        except Customer.DoesNotExist:
            raise exceptions.AuthenticationFailed("Customer not found.", code="invalid_token")
        # Attach ids to request for views to inspect without re-decoding
        request.customer = customer
        request.customer_merchant_id = mid
        request.customer_id = cid
        # DRF expects (user, token)
        return (customer, token)

    def authenticate_header(self, request):
        return self.keyword
