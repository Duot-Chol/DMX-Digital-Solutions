from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from customers.models import Customer
from customers.services.customer_service import CustomerService


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializes customer information for the DMX Digital Solutions API.
    """

    class Meta:
        model = Customer
        fields = [
            "id",
            "customer_number",
            "customer_type",
            "name",
            "email",
            "phone",
            "address",
            "country",
            "website",
            "originating_lead",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "customer_number",
            "originating_lead",
            "status",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """
        Delegate customer creation to the service layer.
        """

        try:
            return CustomerService.create(**validated_data)
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise serializers.ValidationError(exc.message_dict) from exc

            raise serializers.ValidationError(
                {"detail": exc.messages}
            ) from exc