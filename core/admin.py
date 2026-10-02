"""
Django Admin configuration for the Core application.

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for managing global DMX Digital Solutions
    website settings.
    """

    list_display = (
        "company_name",
        "motto",
        "email",
        "phone",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "is_active",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "company_name",
        "motto",
        "email",
        "phone",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Company Identity",
            {
                "fields": (
                    "company_name",
                    "motto",
                    "description",
                    "logo",
                    "favicon",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "email",
                    "phone",
                    "address",
                    "website",
                )
            },
        ),
        (
            "Social Media",
            {
                "fields": (
                    "facebook_url",
                    "instagram_url",
                    "linkedin_url",
                    "youtube_url",
                    "x_url",
                )
            },
        ),
        (
            "SEO",
            {
                "fields": (
                    "seo_title",
                    "seo_description",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_active",
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