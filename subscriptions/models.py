"""
============================================================
DMX Digital Solutions
Subscriptions - Models
============================================================

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from customers.models import Customer
from products.models import Product


class SubscriptionPlan(models.Model):
    """
    Defines a commercial subscription plan offered for a product.
    """

    class BillingCycle(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        SEMI_ANNUALLY = "SEMI_ANNUALLY", "Semi-Annually"
        YEARLY = "YEARLY", "Yearly"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="subscription_plans",
    )

    name = models.CharField(
        max_length=150,
    )

    description = models.TextField(
        blank=True,
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    currency = models.CharField(
        max_length=3,
        default="USD",
    )

    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("product", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("product", "name"),
                name="unique_subscription_plan_per_product",
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class Subscription(models.Model):
    """
    Represents a customer's subscription to a subscription plan.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    subscription_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    agreed_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    currency = models.CharField(
        max_length=3,
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
    )

    start_date = models.DateField(
        null=True,
        blank=True,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    auto_renew = models.BooleanField(
        default=False,
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.subscription_number


class SubscriptionNumberCounter(models.Model):
    """
    Stores the next subscription number to allocate.
    """

    name = models.CharField(
        max_length=50,
        unique=True,
    )

    next_number = models.PositiveBigIntegerField(
        default=1,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Subscription Number Counter"
        verbose_name_plural = "Subscription Number Counters"

    def __str__(self):
        return f"{self.name}: next number {self.next_number}"