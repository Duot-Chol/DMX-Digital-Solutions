from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "organization",
        "subject",
        "product",
        "service",
        "source",
        "status",
        "priority",
        "created_at",
    )

    list_filter = (
        "status",
        "priority",
        "source",
        "product",
        "service",
        "created_at",
    )

    search_fields = (
        "full_name",
        "email",
        "phone",
        "organization",
        "subject",
        "message",
    )

    list_editable = (
        "status",
        "priority",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "product",
        "service",
    )

    fieldsets = (
        (
            "Contact Information",
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
            "Inquiry",
            {
                "fields": (
                    "subject",
                    "message",
                    "product",
                    "service",
                    "source",
                )
            },
        ),
        (
            "Lead Management",
            {
                "fields": (
                    "status",
                    "priority",
                    "notes",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    ordering = ("-created_at",)