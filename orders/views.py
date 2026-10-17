
"""
============================================================
DMX Digital Solutions
Orders - API Views

Motto:
    Building Intelligent Digital Solutions
============================================================
"""

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from orders.models import Order
from orders.serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
)
from orders.services.order_lifecycle_service import (
    OrderLifecycleService,
)


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Staff-only API for managing commercial orders.

    Supported operations:
    - List orders
    - Retrieve an order
    - Create a draft order
    - Confirm an order
    - Approve a zero-value order
    - Start order processing
    - Fulfil an order
    - Cancel an order

    Order deletion and direct status modification are not supported.
    """

    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return (
            Order.objects
            .select_related(
                "customer",
                "free_order_approved_by",
            )
            .prefetch_related("items")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer

        return OrderDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        response_serializer = OrderDetailSerializer(
            order,
            context=self.get_serializer_context(),
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def _lifecycle_response(self, order):
        serializer = OrderDetailSerializer(
            order,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        order = self.get_object()
        order = OrderLifecycleService.confirm(order)
        return self._lifecycle_response(order)

    @action(
        detail=True,
        methods=["post"],
        url_path="approve-free",
    )
    def approve_free(self, request, pk=None):
        order = self.get_object()
        order = OrderLifecycleService.approve_free_order(
            order,
            approved_by=request.user,
        )
        return self._lifecycle_response(order)

    @action(
        detail=True,
        methods=["post"],
        url_path="start-processing",
    )
    def start_processing(self, request, pk=None):
        order = self.get_object()
        order = OrderLifecycleService.start_processing(order)
        return self._lifecycle_response(order)

    @action(detail=True, methods=["post"])
    def fulfil(self, request, pk=None):
        order = self.get_object()
        order = OrderLifecycleService.fulfil(order)
        return self._lifecycle_response(order)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order = OrderLifecycleService.cancel(order)
        return self._lifecycle_response(order)
