from decimal import Decimal

import factory

from apps.catalog.tests.factories import MerchantFactory
from apps.delivery.models import DeliveryConfig, Zone


class DeliveryConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeliveryConfig

    merchant = factory.SubFactory(MerchantFactory)
    modo = DeliveryConfig.Modo.PROPIO
    cobro = DeliveryConfig.Cobro.EN_PEDIDO
    calculo = DeliveryConfig.Calculo.FIJO
    flat_amount = Decimal("1500.00")
    free_threshold = None
    third_party_fixed_amount = None


class ZoneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Zone

    merchant = factory.SubFactory(MerchantFactory)
    name = factory.Sequence(lambda n: f"Zone {n}")
    base_fee = Decimal("800.00")
