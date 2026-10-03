"""
==========================================================
DMX Digital Solutions
Demo Requests - Serializer
Motto: Building Intelligent Digital Solutions
==========================================================
"""

from rest_framework import serializers

from products.models import Product
from .models import DemoRequest


class DemoRequestSerializer(serializers.ModelSerializer):
    """Accept public demo requests without exposing internal fields."""

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(
            status__in=[
                Product.Status.ACTIVE,
                Product.Status.COMING_SOON,
            ]
        ),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = DemoRequest
        fields = (
            "id",
            "full_name",
            "email",
            "phone",
            "organization",
            "product",
            "preferred_date",
            "preferred_time",
            "message",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def to_internal_value(self, data):
        allowed_fields = set(self.fields.keys())
        submitted_fields = set(data.keys())
        unexpected_fields = submitted_fields - allowed_fields

        if unexpected_fields:
            raise serializers.ValidationError({
                field: "This field is not accepted by the public API."
                for field in sorted(unexpected_fields)
            })

        return super().to_internal_value(data)
        id="s1a8cb"