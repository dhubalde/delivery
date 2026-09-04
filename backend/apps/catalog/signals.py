import django.db.models as models
from django.db.models import signals as django_signals
from django.dispatch import receiver

from apps.orders.models import Order
from apps.catalog.models import CatalogStat


@receiver(django_signals.post_save, sender=Order)
def _on_order_saved(sender, instance, created, **kwargs):
    """Increment buyer_count in CatalogStat when an order reaches ENTREGADO state."""
    mid = instance.merchant_id
    if mid is None:
        return
    stat, _ = CatalogStat.objects.get_or_create(merchant_id=mid)
    if instance.state == Order.State.ENTREGADO:
        stat.buyer_count += 1
        stat.save(update_fields=["buyer_count"])