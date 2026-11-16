from django.contrib import admin

from apps.tenancy.models import Merchant, PlatformUser


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "seat_limit", "has_branches", "print_tickets")
    list_filter = ("is_active", "has_branches", "print_tickets")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "slug", "vertical", "is_active", "logo", "logo_url", "seat_limit", "has_branches", "print_tickets")}),
        (
            "Mercado Pago",
            {"fields": ("mp_access_token", "mp_webhook_secret"), "classes": ("collapse",)},
        ),
    )


@admin.register(PlatformUser)
class PlatformUserAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "merchant", "must_change_password")
    list_filter = ("role",)
    search_fields = ("user__username",)
