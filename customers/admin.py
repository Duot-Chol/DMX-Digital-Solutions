
from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "customer_number",
        "name",
        "customer_type",
        "email",
        "phone",
        "status",
        "created_at",
    )

    list_filter = (
        "customer_type",
        "status",
        "country",
        "created_at",
    )

    search_fields = (
        "customer_number",
        "name",
        "email",
        "phone",
        "originating_lead__full_name",
        "originating_lead__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Customer Information",
            {
                "fields": (
                    "customer_number",
                    "customer_type",
                    "name",
                    "email",
                    "phone",
                )
            },
        ),
        (
            "Location and Website",
            {
                "fields": (
                    "address",
                    "country",
                    "website",
                )
            },
        ),
        (
            "Business Relationship",
            {
                "fields": (
                    "originating_lead",
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

    ordering = ("name", "customer_number")
    list_per_page = 25
    date_hierarchy = "created_at"