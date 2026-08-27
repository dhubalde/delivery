import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.catalog.tests.factories import MerchantFactory
from apps.tenancy.models import Schedule, SpecialDate, TimeRange

pytestmark = pytest.mark.django_db


class TestBrHrs01SchedulePerDay:
    def test_br_hrs_01_schedule_unique_per_weekday(self):
        merchant = MerchantFactory()
        Schedule.objects.create(merchant=merchant, weekday=0)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Schedule.objects.create(merchant=merchant, weekday=0)

    def test_br_hrs_01_schedule_weekday_range_valid(self):
        merchant = MerchantFactory()
        for wd in range(7):
            s = Schedule(merchant=merchant, weekday=wd)
            s.full_clean()

    def test_br_hrs_01_weekday_out_of_range_rejected(self):
        merchant = MerchantFactory()
        with pytest.raises(ValidationError):
            Schedule(merchant=merchant, weekday=7).full_clean()

    def test_br_hrs_01_multiple_ranges_per_day(self):
        merchant = MerchantFactory()
        schedule = Schedule.objects.create(merchant=merchant, weekday=1)
        TimeRange.objects.create(schedule=schedule, opens_at=datetime.time(9, 0), closes_at=datetime.time(12, 0))
        TimeRange.objects.create(schedule=schedule, opens_at=datetime.time(16, 0), closes_at=datetime.time(20, 0))
        assert schedule.time_ranges.count() == 2

    def test_br_hrs_01_overlapping_ranges_rejected(self):
        merchant = MerchantFactory()
        schedule = Schedule.objects.create(merchant=merchant, weekday=2)
        TimeRange.objects.create(schedule=schedule, opens_at=datetime.time(9, 0), closes_at=datetime.time(12, 0))
        overlapping = TimeRange(schedule=schedule, opens_at=datetime.time(11, 0), closes_at=datetime.time(13, 0))
        with pytest.raises(ValidationError) as exc:
            overlapping.full_clean()
        assert "opens_at" in exc.value.message_dict

    def test_br_hrs_01_closes_must_be_after_opens(self):
        merchant = MerchantFactory()
        schedule = Schedule.objects.create(merchant=merchant, weekday=3)
        bad = TimeRange(schedule=schedule, opens_at=datetime.time(14, 0), closes_at=datetime.time(14, 0))
        with pytest.raises(ValidationError):
            bad.full_clean()

    def test_br_hrs_04_special_date_unique_per_merchant(self):
        merchant = MerchantFactory()
        SpecialDate.objects.create(merchant=merchant, date=datetime.date(2026, 12, 25), is_closed=True)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SpecialDate.objects.create(merchant=merchant, date=datetime.date(2026, 12, 25), is_closed=False)
