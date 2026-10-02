from rest_framework import serializers

from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for public DMX Digital Solutions services.
    """

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "description",
            "icon",
            "is_featured",
            "is_active",
            "display_order",
            "service_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]