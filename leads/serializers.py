from rest_framework import serializers

from products.models import Product
from services.models import Service

from .models import Lead


class LeadCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for public commercial inquiries.

    Only explicitly permitted fields may be submitted.
    Internal lead-management fields are not accepted.
    """

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(
            status__in=["ACTIVE", "COMING_SOON"]
        ),
        required=False,
        allow_null=True,
    )

    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Lead
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "organization",
            "product",
            "service",
            "subject",
            "message",
            "source",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

    def to_internal_value(self, data):
        """
        Reject unknown fields, including internal fields such
        as status, priority, and notes.
        """
        if hasattr(data, "keys"):
            allowed_fields = set(self.fields.keys())
            submitted_fields = set(data.keys())
            unexpected_fields = submitted_fields - allowed_fields

            if unexpected_fields:
                raise serializers.ValidationError({
                    field: ["This field is not permitted."]
                    for field in sorted(unexpected_fields)
                })

        return super().to_internal_value(data)

    def validate(self, attrs):
        """
        An inquiry may reference a product or a service,
        but not both.
        """
        product = attrs.get("product")
        service = attrs.get("service")

        if product and service:
            raise serializers.ValidationError(
                "Please select either a product or a service, not both."
            )

        return attrs