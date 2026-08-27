from decimal import Decimal

from django.db import transaction


class DeliveryFeeError(Exception):
    pass


class ConfigImmutableError(DeliveryFeeError):
    pass


class DeliveryFeeCalculator:
    @staticmethod
    def is_passthrough(config):
        return (
            config.modo == config.Modo.TERCERIZADO
            and config.cobro == config.Cobro.EN_PEDIDO
        )

    @staticmethod
    def calc(config, items_total=None, zone=None, distance_km=None):
        calculo = config.calculo
        if calculo == config.Calculo.POR_ZONA:
            if zone is None:
                raise DeliveryFeeError("Zone required for POR_ZONA (BR-DEL-03)")
            if zone.merchant_id != config.merchant_id:
                raise DeliveryFeeError("Zone merchant mismatch")
            return Decimal(zone.base_fee)
        if calculo == config.Calculo.FIJO:
            if config.flat_amount is None:
                raise DeliveryFeeError("flat_amount required for FIJO (BR-DEL-03)")
            return Decimal(config.flat_amount)
        if calculo == config.Calculo.GRATIS_MONTO:
            if config.flat_amount is None or config.free_threshold is None:
                raise DeliveryFeeError("flat_amount and free_threshold required for GRATIS_MONTO (BR-DEL-03)")
            if items_total is None:
                raise DeliveryFeeError("items_total required for GRATIS_MONTO")
            if Decimal(str(items_total)) >= Decimal(str(config.free_threshold)):
                return Decimal("0.00")
            return Decimal(config.flat_amount)
        if calculo == config.Calculo.POR_DISTANCIA:
            if config.flat_amount is None:
                raise DeliveryFeeError("flat_amount (rate per km) required for POR_DISTANCIA")
            if distance_km is None:
                raise DeliveryFeeError("distance_km required for POR_DISTANCIA")
            return (Decimal(str(config.flat_amount)) * Decimal(str(distance_km))).quantize(Decimal("0.01"))
        raise DeliveryFeeError(f"Unknown calculo {calculo}")

    @staticmethod
    def merchant_revenue(delivery_fee, config):
        if DeliveryFeeCalculator.is_passthrough(config):
            return Decimal("0.00")
        return Decimal(str(delivery_fee))

    @staticmethod
    def ticket_payload(items_total, delivery_fee, config):
        is_pt = DeliveryFeeCalculator.is_passthrough(config)
        fee = Decimal(str(delivery_fee))
        subtotal = Decimal(str(items_total))
        return {
            "subtotal": subtotal,
            "delivery_fee": fee,
            "is_passthrough": is_pt,
            "passthrough_fee": fee if is_pt else Decimal("0.00"),
            "merchant_revenue_delivery": Decimal("0.00") if is_pt else fee,
            "customer_total": subtotal + fee,
        }


class DeliveryConfigService:
    @staticmethod
    @transaction.atomic
    def get_or_create(merchant):
        from apps.delivery.models import DeliveryConfig

        config, _ = DeliveryConfig.objects.get_or_create(merchant=merchant)
        return config

    @staticmethod
    @transaction.atomic
    def update_config(merchant, **fields):
        from apps.delivery.models import DeliveryConfig
        from apps.orders.models import Order

        try:
            config = DeliveryConfig.objects.select_for_update().get(merchant=merchant)
        except DeliveryConfig.DoesNotExist:
            raise DeliveryFeeError("DeliveryConfig does not exist for merchant")
        if "modo" in fields and fields["modo"] != config.modo:
            if Order.objects.filter(merchant=merchant).exists():
                raise ConfigImmutableError(
                    "Delivery config modo immutable once orders exist (BR-DEL-05)"
                )
        for key, value in fields.items():
            setattr(config, key, value)
        config.full_clean()
        config.save()
        return config
