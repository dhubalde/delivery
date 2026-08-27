import uuid
from decimal import Decimal


class GatewayError(Exception):
    pass


class MercadoPagoMockGateway:
    @staticmethod
    def process(method, amount, order_id=None):
        if method not in ("BILLETERA", "TARJETA"):
            raise GatewayError(f"Gateway does not support method {method}")
        if amount <= Decimal("0"):
            return {"status": "REJECTED", "gateway_ref": None, "reason": "invalid amount"}
        ref = f"MP-MOCK-{uuid.uuid4().hex[:12].upper()}"
        return {"status": "CONFIRMED", "gateway_ref": ref}

    @staticmethod
    def reject(method, amount):
        return {"status": "REJECTED", "gateway_ref": None, "reason": "mock rejection"}
