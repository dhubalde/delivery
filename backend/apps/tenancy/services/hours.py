from datetime import datetime, timedelta

from django.utils import timezone

from apps.tenancy.models import Schedule, SpecialDate


def is_open(merchant, dt=None):
    if dt is None:
        dt = timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    local_date = dt.date()
    local_time = dt.time()

    special = SpecialDate.objects.filter(merchant=merchant, date=local_date).first()
    if special is not None:
        if special.is_closed:
            return False
        return True

    weekday = local_date.weekday()
    try:
        schedule = Schedule.objects.get(merchant=merchant, weekday=weekday)
    except Schedule.DoesNotExist:
        return False

    for tr in schedule.time_ranges.all():
        if tr.opens_at <= local_time < tr.closes_at:
            return True
    return False


def next_open_at(merchant, dt=None):
    if dt is None:
        dt = timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)

    for offset in range(14):
        check_date = (dt + timedelta(days=offset)).date()
        check_time = dt.time() if offset == 0 else None

        special = SpecialDate.objects.filter(merchant=merchant, date=check_date).first()
        if special is not None and special.is_closed:
            continue
        if special is not None and not special.is_closed:
            weekday = check_date.weekday()
            try:
                schedule = Schedule.objects.get(merchant=merchant, weekday=weekday)
            except Schedule.DoesNotExist:
                continue
            ranges = list(schedule.time_ranges.order_by("opens_at"))
            if not ranges:
                continue
            first = ranges[0]
            candidate = datetime.combine(check_date, first.opens_at)
            candidate = timezone.make_aware(candidate) if timezone.is_naive(candidate) else candidate
            if offset == 0 and check_time is not None and check_time >= first.closes_at:
                continue
            if offset == 0 and check_time is not None:
                for tr in ranges:
                    cand = datetime.combine(check_date, tr.opens_at)
                    cand = timezone.make_aware(cand) if timezone.is_naive(cand) else cand
                    if check_time < tr.opens_at:
                        return cand
                    if tr.opens_at <= check_time < tr.closes_at:
                        return dt
                continue
            return candidate

        weekday = check_date.weekday()
        try:
            schedule = Schedule.objects.get(merchant=merchant, weekday=weekday)
        except Schedule.DoesNotExist:
            continue
        ranges = list(schedule.time_ranges.order_by("opens_at"))
        if not ranges:
            continue
        if offset == 0 and check_time is not None:
            for tr in ranges:
                if tr.opens_at <= check_time < tr.closes_at:
                    return dt
                if check_time < tr.opens_at:
                    candidate = datetime.combine(check_date, tr.opens_at)
                    candidate = timezone.make_aware(candidate) if timezone.is_naive(candidate) else candidate
                    return candidate
            continue
        candidate = datetime.combine(check_date, ranges[0].opens_at)
        candidate = timezone.make_aware(candidate) if timezone.is_naive(candidate) else candidate
        return candidate
    return None
