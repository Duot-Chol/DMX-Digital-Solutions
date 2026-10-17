"""
============================================================
DMX Digital Solutions
Orders - Serializers

Motto:
    Building Intelligent Digital Solutions
============================================================
"""

from rest_framework import serializers

from customers.models import Customer
from orders.models import Order, OrderItem
from orders.services.order_service import OrderService
from products.models import Product
from subscriptions.models import SubscriptionPlan


class OrderItemReadSerializer(serializers.ModelSerializer):
    """Read-only representation of a purchased order item."""

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
        allow_null=True,
    )
    subscription_plan_name = serializers.CharField(
        source="subscription_plan.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "subscription_plan",
            "subscription_plan_name",
            "item_description",
            "quantity",
            "unit_price",
            "line_total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OrderDetailSerializer(serializers.ModelSerializer):
    """Read-only representation of an order and its items."""

    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True,
    )
    items = OrderItemReadSerializer(many=True, read_only=True)
    free_order_approved_by_username = serializers.CharField(
        source="free_order_approved_by.username",
        read_only=True,
        allow_null=True,
    )
    payment_status = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer",
            "customer_name",
            "status",
            "payment_status",
            "currency",
            "subtotal",
            "notes",
            "free_order_approved_by",
            "free_order_approved_by_username",
            "free_order_approved_at",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OrderItemCreateSerializer(serializers.Serializer):
    """Validate one product or subscription-plan purchase."""

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        required=False,
    )
    subscription_plan = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.all(),
        required=False,
    )
    quantity = serializers.IntegerField(
        min_value=1,
        required=False,
        default=1,
    )
    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
    )
    currency = serializers.CharField(
        max_length=3,
        required=False,
    )

    def validate(self, attrs):
        has_product = attrs.get("product") is not None
        has_plan = attrs.get("subscription_plan") is not None

        if has_product == has_plan:
            raise serializers.ValidationError(
                "Specify exactly one of product or subscription_plan."
            )

        if has_plan and "unit_price" in attrs:
            raise serializers.ValidationError(
                "Subscription-plan prices are taken from the plan. "
                "Do not supply unit_price for a plan purchase."
            )

        return attrs


class OrderCreateSerializer(serializers.Serializer):
    """Validate order creation and delegate business rules to the service."""

    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
    )
    items = OrderItemCreateSerializer(
        many=True,
        allow_empty=False,
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    def create(self, validated_data):
        """
        Delegate order creation to the service and return
        business-rule errors as proper API validation errors.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        try:
            return OrderService.create(**validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                getattr(exc, "message_dict", None)
                or getattr(exc, "messages", [str(exc)])
            ) from exc