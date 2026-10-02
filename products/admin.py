"""
Django Admin configuration for the Products application.

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from django.contrib import admin

from .models import Product, ProductCategory, ProductFeature


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for product categories.
    """

    list_display = (
        "name",
        "slug",
        "is_active",
        "display_order",
        "updated_at",
    )

    list_filter = (
        "is_active",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
        "slug",
        "description",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    ordering = (
        "display_order",
        "name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


class ProductFeatureInline(admin.TabularInline):
    """
    Inline interface for managing product features
    directly from the Product admin page.
    """

    model = ProductFeature
    extra = 1

    fields = (
        "name",
        "description",
        "display_order",
        "is_active",
    )

    ordering = (
        "display_order",
        "name",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for commercial DMX products.
    """

    list_display = (
        "name",
        "category",
        "status",
        "is_featured",
        "display_order",
        "updated_at",
    )

    list_filter = (
        "status",
        "is_featured",
        "category",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
        "slug",
        "short_description",
        "description",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    autocomplete_fields = (
        "category",
    )

    ordering = (
        "display_order",
        "name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Product Identity",
            {
                "fields": (
                    "name",
                    "slug",
                    "category",
                    "logo",
                )
            },
        ),
        (
            "Product Description",
            {
                "fields": (
                    "short_description",
                    "description",
                )
            },
        ),
        (
            "Product Status",
            {
                "fields": (
                    "status",
                    "is_featured",
                    "display_order",
                )
            },
        ),
        (
            "Product Links",
            {
                "fields": (
                    "product_url",
                    "demo_url",
                    "documentation_url",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    inlines = (
        ProductFeatureInline,
    )


@admin.register(ProductFeature)
class ProductFeatureAdmin(admin.ModelAdmin):
    """
    Standalone admin interface for product features.
    """

    list_display = (
        "name",
        "product",
        "display_order",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "is_active",
        "product",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
        "description",
        "product__name",
    )

    ordering = (
        "product",
        "display_order",
        "name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )