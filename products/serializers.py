from rest_framework import serializers

from .models import Product, ProductCategory, ProductFeature


class ProductCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for product categories.
    """

    class Meta:
        model = ProductCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "display_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ProductFeatureSerializer(serializers.ModelSerializer):
    """
    Serializer for individual product features.
    """

    class Meta:
        model = ProductFeature
        fields = [
            "id",
            "name",
            "description",
            "display_order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for commercial products.

    Product features are included as nested read-only data.
    """

    category = ProductCategorySerializer(read_only=True)
    features = ProductFeatureSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "slug",
            "short_description",
            "description",
            "logo",
            "status",
            "is_featured",
            "display_order",
            "product_url",
            "demo_url",
            "documentation_url",
            "features",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "features",
        ]