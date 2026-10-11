from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from subscriptions.models import Subscription, SubscriptionPlan
from subscriptions.services.subscription_service import SubscriptionService


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "product",
            "name",
            "description",
            "price",
            "currency",
            "billing_cycle",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            "id",
            "subscription_number",
            "customer",
            "plan",
            "agreed_price",
            "currency",
            "status",
            "start_date",
            "end_date",
            "auto_renew",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "subscription_number",
            "agreed_price",
            "currency",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        try:
            return SubscriptionService.create(**validated_data)
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                detail = exc.message_dict
            else:
                detail = exc.messages

            raise serializers.ValidationError(detail) from exc