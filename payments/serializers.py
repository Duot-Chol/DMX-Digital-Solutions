"""
============================================================
DMX Digital Solutions
Payments - Serializers
============================================================

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from rest_framework import serializers

from payments.models import Payment
from payments.services.payment_service import PaymentService


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializes payment records.

    Payment references, status, payment confirmation timestamps,
    and failure details are controlled by the server.
    """

    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True,
    )

    subscription_number = serializers.CharField(
        source="subscription.subscription_number",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "payment_reference",
            "customer",
            "customer_name",
            "subscription",
            "subscription_number",
            "amount",
            "currency",
            "payment_method",
            "status",
            "external_transaction_reference",
            "description",
            "failure_reason",
            "paid_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "payment_reference",
            "customer_name",
            "subscription_number",
            "status",
            "failure_reason",
            "paid_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """
        Delegate payment creation to the payment service.
        """

        return PaymentService.create(**validated_data)