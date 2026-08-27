import datetime

import pytest
from django.utils import timezone

from apps.catalog.tests.factories import MerchantFactory
from apps.tenancy.models import Schedule, SpecialDate, TimeRange
from apps.tenancy.services.hours import is_open, next_open_at

pytestmark = pytest.mark.django_db


def _make_schedule(merchant, weekday, ranges):
    sched = Schedule.objects.create(merchant=merchant, weekday=weekday)
    for opens, closes in ranges:
        TimeRange.objects.create(schedule=sched, opens_at=opens, closes_at=closes)
    return sched


class TestBrHrs02OrderingBlockedOutsideRanges:
    def test_br_hrs_02_inside_range_is_open(self):
        merchant = MerchantFactory()
        _make_schedule(merchant, 0, [(datetime.time(9, 0), datetime.time(18, 0))])
        dt = timezone.make_aware(datetime.datetime(2026, 8, 24, 10, 0))
        assert is_open(merchant, dt) is True

    def test_br_hrs_02_outside_range_is_closed(self):
        merchant = MerchantFactory()
        _make_schedule(merchant, 0, [(datetime.time(9, 0), datetime.time(18, 0))])
        dt = timezone.make_aware(datetime.datetime(2026, 8, 24, 19, 0))
        assert is_open(merchant, dt) is False

    def test_br_hrs_02_multiple_ranges_gap_is_closed(self):
        merchant = MerchantFactory()
        _make_schedule(
            merchant, 0, [(datetime.time(9, 0), datetime.time(12, 0)), (datetime.time(16, 0), datetime.time(20, 0))]
        )
        gap = timezone.make_aware(datetime.datetime(2026, 8, 24, 14, 0))
        assert is_open(merchant, gap) is False
        second = timezone.make_aware(datetime.datetime(2026, 8, 24, 17, 0))
        assert is_open(merchant, second) is True

    def test_br_hrs_02_boundary_closes_at_is_closed(self):
        merchant = MerchantFactory()
        _make_schedule(merchant, 0, [(datetime.time(9, 0), datetime.time(18, 0))])
        dt = timezone.make_aware(datetime.datetime(2026, 8, 24, 18, 0))
        assert is_open(merchant, dt) is False

    def test_br_hrs_02_no_schedule_means_closed(self):
        merchant = MerchantFactory()
        dt = timezone.make_aware(datetime.datetime(2026, 8, 24, 12, 0))
        assert is_open(merchant, dt) is False

    def test_br_hrs_04_special_date_closed_overrides_schedule(self):
        merchant = MerchantFactory()
        _make_schedule(merchant, 0, [(datetime.time(9, 0), datetime.time(18, 0))])
        SpecialDate.objects.create(merchant=merchant, date=datetime.date(2026, 8, 24), is_closed=True)
        dt = timezone.make_aware(datetime.datetime(2026, 8, 24, 10, 0))
        assert is_open(merchant, dt) is False

    def test_next_open_at_returns_next_slot(self):
        merchant = MerchantFactory()
        _make_schedule(merchant, 0, [(datetime.time(9, 0), datetime.time(12, 0))])
        _make_schedule(merchant, 1, [(datetime.time(9, 0), datetime.time(12, 0))])
        dt = timezone.make_aware(datetime.datetime(2026, 8, 24, 13, 0))
        result = next_open_at(merchant, dt)
        assert result is not None
        assert result.date() == datetime.date(2026, 8, 25)
        assert result.time() == datetime.time(9, 0)
