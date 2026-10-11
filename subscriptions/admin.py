"""
============================================================
DMX Digital Solutions
Subscriptions - Django Admin
============================================================

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from django.contrib import admin

from .models import Subscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "product",
        "billing_cycle",
        "price",
        "currency",
        "is_active",
        "created_at",
    )

    list_filter = (
        "billing_cycle",
        "currency",
        "is_active",
        "product",
    )

    search_fields = (
        "name",
        "description",
        "product__name",
    )

    ordering = (
        "product",
        "name",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    list_per_page = 25


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "subscription_number",
        "customer",
        "plan",
        "status",
        "agreed_price",
        "currency",
        "start_date",
        "end_date",
        "auto_renew",
    )

    list_filter = (
        "status",
        "auto_renew",
        "currency",
        "plan",
    )

    search_fields = (
        "subscription_number",
        "customer__name",
        "plan__name",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "id",
        "subscription_number",
        "created_at",
        "updated_at",
    )

    list_per_page = 25

    date_hierarchy = "created_at"