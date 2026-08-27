from decimal import Decimal

import pytest

from apps.catalog.tests.factories import MerchantFactory
from apps.delivery.models import DeliveryConfig
from apps.delivery.services import ConfigImmutableError, DeliveryConfigService, DeliveryFeeCalculator, DeliveryFeeError
from apps.delivery.tests.factories import DeliveryConfigFactory, ZoneFactory
from apps.orders.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db


class TestBrDel01Modo:
    def test_br_del_01_modo_propio_and_tercerizado(self):
        cfg_propio = DeliveryConfigFactory(modo=DeliveryConfig.Modo.PROPIO)
        cfg_tercero = DeliveryConfigFactory(modo=DeliveryConfig.Modo.TERCERIZADO)
        assert cfg_propio.modo == "PROPIO"
        assert cfg_tercero.modo == "TERCERIZADO"

    def test_br_del_01_modo_per_merchant_onetoone(self):
        merchant = MerchantFactory()
        cfg = DeliveryConfigFactory(merchant=merchant, modo=DeliveryConfig.Modo.PROPIO)
        assert cfg.merchant_id == merchant.pk
        with pytest.raises(Exception):
            DeliveryConfigFactory(merchant=merchant)


class TestBrDel02Cobro:
    def test_br_del_02_cobro_en_pedido_and_en_entrega(self):
        cfg_pedido = DeliveryConfigFactory(cobro=DeliveryConfig.Cobro.EN_PEDIDO)
        cfg_entrega = DeliveryConfigFactory(cobro=DeliveryConfig.Cobro.EN_ENTREGA)
        assert cfg_pedido.cobro == "EN_PEDIDO"
        assert cfg_entrega.cobro == "EN_ENTREGA"


class TestBrDel03Calculo:
    def test_br_del_03_fijo_returns_flat_amount(self):
        cfg = DeliveryConfigFactory(calculo=DeliveryConfig.Calculo.FIJO, flat_amount=Decimal("1500.00"))
        assert DeliveryFeeCalculator.calc(cfg) == Decimal("1500.00")

    def test_br_del_03_por_zona_returns_zone_base_fee(self):
        merchant = MerchantFactory()
        cfg = DeliveryConfigFactory(merchant=merchant, calculo=DeliveryConfig.Calculo.POR_ZONA)
        zone = ZoneFactory(merchant=merchant, base_fee=Decimal("900.00"))
        assert DeliveryFeeCalculator.calc(cfg, zone=zone) == Decimal("900.00")

    def test_br_del_03_por_zona_without_zone_raises(self):
        cfg = DeliveryConfigFactory(calculo=DeliveryConfig.Calculo.POR_ZONA)
        with pytest.raises(DeliveryFeeError, match="Zone required"):
            DeliveryFeeCalculator.calc(cfg, zone=None)

    def test_br_del_03_gratis_monto_below_threshold_pays(self):
        cfg = DeliveryConfigFactory(calculo=DeliveryConfig.Calculo.GRATIS_MONTO, flat_amount=Decimal("1200.00"), free_threshold=Decimal("10000.00"))
        assert DeliveryFeeCalculator.calc(cfg, items_total=Decimal("9000.00")) == Decimal("1200.00")

    def test_br_del_03_gratis_monto_above_threshold_free(self):
        cfg = DeliveryConfigFactory(calculo=DeliveryConfig.Calculo.GRATIS_MONTO, flat_amount=Decimal("1200.00"), free_threshold=Decimal("10000.00"))
        assert DeliveryFeeCalculator.calc(cfg, items_total=Decimal("15000.00")) == Decimal("0.00")

    def test_br_del_03_gratis_monto_exact_threshold_free(self):
        cfg = DeliveryConfigFactory(calculo=DeliveryConfig.Calculo.GRATIS_MONTO, flat_amount=Decimal("1200.00"), free_threshold=Decimal("10000.00"))
        assert DeliveryFeeCalculator.calc(cfg, items_total=Decimal("10000.00")) == Decimal("0.00")

    def test_br_del_03_por_distancia_calc(self):
        cfg = DeliveryConfigFactory(calculo=DeliveryConfig.Calculo.POR_DISTANCIA, flat_amount=Decimal("500.00"))
        assert DeliveryFeeCalculator.calc(cfg, distance_km=Decimal("3")) == Decimal("1500.00")
        assert DeliveryFeeCalculator.calc(cfg, distance_km=4) == Decimal("2000.00")

    def test_br_del_03_por_distancia_without_distance_raises(self):
        cfg = DeliveryConfigFactory(calculo=DeliveryConfig.Calculo.POR_DISTANCIA, flat_amount=Decimal("500.00"))
        with pytest.raises(DeliveryFeeError, match="distance_km"):
            DeliveryFeeCalculator.calc(cfg, distance_km=None)


class TestBrDel04Passthrough:
    def test_br_del_04_is_passthrough_true_tercero_en_pedido(self):
        cfg = DeliveryConfigFactory(modo=DeliveryConfig.Modo.TERCERIZADO, cobro=DeliveryConfig.Cobro.EN_PEDIDO)
        assert DeliveryFeeCalculator.is_passthrough(cfg) is True

    def test_br_del_04_is_passthrough_false_propio_en_pedido(self):
        cfg = DeliveryConfigFactory(modo=DeliveryConfig.Modo.PROPIO, cobro=DeliveryConfig.Cobro.EN_PEDIDO)
        assert DeliveryFeeCalculator.is_passthrough(cfg) is False

    def test_br_del_04_is_passthrough_false_tercero_en_entrega(self):
        cfg = DeliveryConfigFactory(modo=DeliveryConfig.Modo.TERCERIZADO, cobro=DeliveryConfig.Cobro.EN_ENTREGA)
        assert DeliveryFeeCalculator.is_passthrough(cfg) is False

    def test_br_del_04_is_passthrough_false_propio_en_entrega(self):
        cfg = DeliveryConfigFactory(modo=DeliveryConfig.Modo.PROPIO, cobro=DeliveryConfig.Cobro.EN_ENTREGA)
        assert DeliveryFeeCalculator.is_passthrough(cfg) is False

    def test_br_del_04_merchant_revenue_zero_when_passthrough(self):
        cfg = DeliveryConfigFactory(modo=DeliveryConfig.Modo.TERCERIZADO, cobro=DeliveryConfig.Cobro.EN_PEDIDO)
        assert DeliveryFeeCalculator.merchant_revenue(Decimal("1500.00"), cfg) == Decimal("0.00")

    def test_br_del_04_merchant_revenue_equals_fee_when_not_passthrough(self):
        cfg = DeliveryConfigFactory(modo=DeliveryConfig.Modo.PROPIO, cobro=DeliveryConfig.Cobro.EN_PEDIDO)
        assert DeliveryFeeCalculator.merchant_revenue(Decimal("1500.00"), cfg) == Decimal("1500.00")


class TestBrDel05TicketAndImmutability:
    def test_br_del_05_ticket_payload_separates_passthrough_fee(self):
        cfg = DeliveryConfigFactory(modo=DeliveryConfig.Modo.TERCERIZADO, cobro=DeliveryConfig.Cobro.EN_PEDIDO, calculo=DeliveryConfig.Calculo.FIJO, flat_amount=Decimal("1200.00"))
        fee = DeliveryFeeCalculator.calc(cfg)
        payload = DeliveryFeeCalculator.ticket_payload(Decimal("8000.00"), fee, cfg)
        assert payload["subtotal"] == Decimal("8000.00")
        assert payload["delivery_fee"] == Decimal("1200.00")
        assert payload["is_passthrough"] is True
        assert payload["passthrough_fee"] == Decimal("1200.00")
        assert payload["merchant_revenue_delivery"] == Decimal("0.00")
        assert payload["customer_total"] == Decimal("9200.00")

    def test_br_del_05_ticket_payload_no_passthrough_not_separated(self):
        cfg = DeliveryConfigFactory(modo=DeliveryConfig.Modo.PROPIO, cobro=DeliveryConfig.Cobro.EN_PEDIDO, calculo=DeliveryConfig.Calculo.FIJO, flat_amount=Decimal("800.00"))
        fee = DeliveryFeeCalculator.calc(cfg)
        payload = DeliveryFeeCalculator.ticket_payload(Decimal("5000.00"), fee, cfg)
        assert payload["is_passthrough"] is False
        assert payload["passthrough_fee"] == Decimal("0.00")
        assert payload["merchant_revenue_delivery"] == Decimal("800.00")
        assert payload["subtotal"] == Decimal("5000.00")
        assert payload["customer_total"] == Decimal("5800.00")

    def test_br_del_05_config_modo_immutable_when_orders_exist(self):
        merchant = MerchantFactory()
        cfg = DeliveryConfigFactory(merchant=merchant, modo=DeliveryConfig.Modo.PROPIO)
        OrderFactory(merchant=merchant)
        with pytest.raises(ConfigImmutableError, match="BR-DEL-05"):
            DeliveryConfigService.update_config(merchant, modo=DeliveryConfig.Modo.TERCERIZADO)

    def test_br_del_05_config_modo_change_allowed_when_no_orders(self):
        merchant = MerchantFactory()
        cfg = DeliveryConfigFactory(merchant=merchant, modo=DeliveryConfig.Modo.PROPIO)
        updated = DeliveryConfigService.update_config(merchant, modo=DeliveryConfig.Modo.TERCERIZADO)
        assert updated.modo == DeliveryConfig.Modo.TERCERIZADO

    def test_br_del_05_other_field_change_allowed_even_with_orders(self):
        merchant = MerchantFactory()
        cfg = DeliveryConfigFactory(merchant=merchant, modo=DeliveryConfig.Modo.PROPIO, flat_amount=Decimal("1000.00"))
        OrderFactory(merchant=merchant)
        updated = DeliveryConfigService.update_config(merchant, flat_amount=Decimal("2000.00"))
        assert updated.flat_amount == Decimal("2000.00")
