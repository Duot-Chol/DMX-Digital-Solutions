"""
============================================================
DMX Digital Solutions
Payments - Django Admin
============================================================

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from django.contrib import admin

from payments.models import Payment, PaymentNumberCounter


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for payment records."""

    list_display = (
        "payment_reference",
        "customer",
        "amount",
        "currency",
        "payment_method",
        "status",
        "paid_at",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_method",
        "currency",
        "created_at",
    )

    search_fields = (
        "payment_reference",
        "customer__name",
        "external_transaction_reference",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "id",
        "payment_reference",
        "customer",
        "subscription",
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
    )

    list_select_related = ("customer", "subscription")

    def has_add_permission(self, request):
        """Prevent manual payment creation through Django Admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing payment transaction records."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Preserve payment transaction history."""
        return False


@admin.register(PaymentNumberCounter)
class PaymentNumberCounterAdmin(admin.ModelAdmin):
    """Admin configuration for payment numbering."""

    list_display = (
        "name",
        "next_number",
        "updated_at",
    )

    readonly_fields = (
        "name",
        "next_number",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False