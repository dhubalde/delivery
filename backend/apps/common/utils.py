from datetime import timedelta

from django.utils import timezone


def get_business_date():
    now = timezone.localtime(timezone.now())
    cutoff = now.replace(hour=3, minute=0, second=0, microsecond=0)
    return cutoff.date() if now >= cutoff else (cutoff - timedelta(days=1)).date()
