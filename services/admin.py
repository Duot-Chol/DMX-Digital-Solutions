from django.contrib import admin

from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_featured",
        "is_active",
        "display_order",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_featured",
        "is_active",
    )

    search_fields = (
        "name",
        "short_description",
        "description",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    list_editable = (
        "is_featured",
        "is_active",
        "display_order",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Service Information",
            {
                "fields": (
                    "name",
                    "slug",
                    "short_description",
                    "description",
                    "icon",
                ),
            },
        ),
        (
            "Commercial Settings",
            {
                "fields": (
                    "service_url",
                    "is_featured",
                    "is_active",
                    "display_order",
                ),
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )