from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Product, ProductCategory
from .serializers import ProductCategorySerializer, ProductSerializer


class ProductCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only API for product categories.
    """

    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only API for commercial products.

    Only active and coming-soon products are exposed publicly.
    """

    queryset = (
        Product.objects
        .filter(status__in=["ACTIVE", "COMING_SOON"])
        .select_related("category")
        .prefetch_related("features")
    )
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]