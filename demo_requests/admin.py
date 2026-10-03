"""
==========================================================
DMX Digital Solutions
Demo Requests - Admin Configuration
==========================================================
"""

from django.contrib import admin

from .models import DemoRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "organization",
        "product",
        "preferred_date",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "preferred_date",
        "created_at",
    )

    search_fields = (
        "full_name",
        "email",
        "phone",
        "organization",
        "product__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Requester Information",
            {
                "fields": (
                    "full_name",
                    "email",
                    "phone",
                    "organization",
                )
            },
        ),
        (
            "Demonstration Details",
            {
                "fields": (
                    "product",
                    "preferred_date",
                    "preferred_time",
                    "message",
                )
            },
        ),
        (
            "Request Management",
            {
                "fields": (
                    "status",
                    "notes",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    ordering = ("-created_at",)
    list_per_page = 25
    date_hierarchy = "created_at"