"""
Serializers for the Core application.

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from rest_framework import serializers

from .models import SiteSettings


class SiteSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for the global DMX Digital Solutions
    website settings.
    """

    class Meta:
        model = SiteSettings
        fields = [
            "id",
            "company_name",
            "motto",
            "description",
            "logo",
            "favicon",
            "email",
            "phone",
            "address",
            "website",
            "facebook_url",
            "instagram_url",
            "linkedin_url",
            "youtube_url",
            "x_url",
            "seo_title",
            "seo_description",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]