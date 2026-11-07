from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from apps.catalog.models import Category, Flavor, Product, CatalogStat
from apps.catalog.serializers import CategorySerializer, FlavorSerializer, ProductSerializer
from apps.tenancy.models import Merchant, Schedule, SpecialDate


def _get_merchant_by_slug(slug):
    merchant = Merchant.all_objects.filter(slug=slug).first()
    if merchant is None or merchant.deleted_at is not None or not merchant.is_active:
        from django.http import Http404

        raise Http404(f"No Merchant matches slug={slug}")
    return merchant


class PublicCatalogAggregateView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def get(self, request, slug):
        merchant = _get_merchant_by_slug(slug)
        categories = Category.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("position", "name")
        products = Product.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("name")
        flavors = Flavor.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("name")
        try:
            stat_obj, _created = CatalogStat.objects.get_or_create(merchant_id=merchant.pk)
            stats = {"visit_count": stat_obj.visit_count, "buyer_count": stat_obj.buyer_count}
        except Exception:
            stats = {"visit_count": 0, "buyer_count": 0}
        cat_data = CategorySerializer(categories, many=True).data
        prod_data = ProductSerializer(products, many=True, context={"request": request}).data
        flav_data = FlavorSerializer(flavors, many=True).data
        merchant_data = {
            "id": merchant.pk,
            "slug": merchant.slug,
            "name": merchant.name,
            "is_active": merchant.is_active,
            "logo_url": getattr(merchant, "resolved_logo_url", "") or "",
        }
        return Response(
            {
                "merchant": merchant_data,
                "categories": cat_data,
                "products": prod_data,
                "flavors": flav_data,
                "stats": stats,
            }
        )


class PublicCategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        merchant = _get_merchant_by_slug(self.kwargs["slug"])
        return Category.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("position", "name")


class PublicProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        merchant = _get_merchant_by_slug(self.kwargs["slug"])
        qs = Product.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("name")
        category_id = self.request.query_params.get("category")
        if category_id is not None:
            try:
                qs = qs.filter(category_id=int(category_id))
            except ValueError:
                pass
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__istartswith=search)
        return qs


class PublicFlavorListView(generics.ListAPIView):
    serializer_class = FlavorSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        merchant = _get_merchant_by_slug(self.kwargs["slug"])
        qs = Flavor.objects.filter(merchant_id=merchant.pk, is_active=True).order_by("name")
        category_id = self.request.query_params.get("category")
        if category_id is not None:
            try:
                qs = qs.filter(category_id=int(category_id))
            except ValueError:
                pass
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__istartswith=search)
        return qs


class CatalogStatPublicView(generics.GenericAPIView):
    """Public endpoint: GET returns stats, POST increments visit count."""

    permission_classes = [permissions.AllowAny]

    def _get_merchant(self):
        return _get_merchant_by_slug(self.kwargs["slug"])

    def post(self, request, slug):
        merchant = self._get_merchant()
        obj, created = CatalogStat.objects.get_or_create(merchant_id=merchant.pk)
        obj.visit_count += 1
        obj.save()
        return Response({"visit_count": obj.visit_count, "buyer_count": obj.buyer_count})

    def get(self, request, slug):
        merchant = self._get_merchant()
        obj, created = CatalogStat.objects.get_or_create(merchant_id=merchant.pk)
        return Response({"visit_count": obj.visit_count, "buyer_count": obj.buyer_count})


def _compute_menu_status(merchant):
    """Compute open/closed status from schedules + special dates.

    Defaults to open when the merchant has no schedule data at all,
    so the storefront never blocks customers of unconfigured stores.
    """
    import datetime

    now = timezone.localtime(timezone.now())
    today = now.date()
    current_time = now.time()

    special_dates = {
        sd.date: sd
        for sd in SpecialDate.objects.filter(merchant_id=merchant.pk)
    }

    def _aware(d, t):
        naive = datetime.datetime.combine(d, t)
        try:
            return timezone.make_aware(naive)
        except Exception:
            return naive

    def _find_next_open(from_date, from_time=None):
        for offset in range(0, 8):
            day = from_date + datetime.timedelta(days=offset)
            special = special_dates.get(day)
            if special is not None and special.is_closed:
                continue
            if special is not None and not special.is_closed:
                # Explicitly open day: if it is today, open now.
                if offset == 0:
                    return None
                schedule = (
                    Schedule.objects.filter(merchant_id=merchant.pk, weekday=day.weekday())
                    .prefetch_related("time_ranges")
                    .first()
                )
                if schedule is not None:
                    first_range = schedule.time_ranges.order_by("opens_at").first()
                    if first_range is not None:
                        return _aware(day, first_range.opens_at).isoformat()
                # No hours configured for that open day: open at midnight.
                return _aware(day, datetime.time.min).isoformat()
            schedule = (
                Schedule.objects.filter(merchant_id=merchant.pk, weekday=day.weekday())
                .prefetch_related("time_ranges")
                .first()
            )
            if schedule is None:
                continue
            ranges = list(schedule.time_ranges.order_by("opens_at"))
            if not ranges:
                continue
            if offset == 0 and from_time is not None:
                for r in ranges:
                    if r.opens_at > from_time:
                        return _aware(day, r.opens_at).isoformat()
                continue
            return _aware(day, ranges[0].opens_at).isoformat()
        return None

    today_special = special_dates.get(today)
    if today_special is not None:
        if today_special.is_closed:
            return False, _find_next_open(today, current_time)
        return True, None

    has_any_schedule = Schedule.objects.filter(merchant_id=merchant.pk).exists()
    if not has_any_schedule:
        return True, None

    today_schedule = (
        Schedule.objects.filter(merchant_id=merchant.pk, weekday=today.weekday())
        .prefetch_related("time_ranges")
        .first()
    )
    if today_schedule is not None:
        for r in today_schedule.time_ranges.order_by("opens_at"):
            if r.opens_at <= current_time < r.closes_at:
                return True, None
    return False, _find_next_open(today, current_time)


class PublicMenuView(generics.GenericAPIView):
    """Public storefront status: GET /api/public/<slug>/menu."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def get(self, request, slug):
        merchant = _get_merchant_by_slug(slug)
        is_open, next_open_at = _compute_menu_status(merchant)
        return Response(
            {
                "is_open": is_open,
                "isOpen": is_open,
                "closed": not is_open,
                "next_open_at": next_open_at,
            }
        )
