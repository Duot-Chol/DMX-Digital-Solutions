from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser

from subscriptions.models import Subscription, SubscriptionPlan
from subscriptions.serializers import (
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
)


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only API for active subscription plans.

    Only active plans are exposed through the public API.
    """

    queryset = (
        SubscriptionPlan.objects
        .filter(is_active=True)
        .select_related("product")
    )
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]


class SubscriptionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Authenticated API for subscription records.

    Supported operations:
        - List subscriptions
        - Retrieve a subscription
        - Create a subscription

    Subscription lifecycle operations such as activation,
    pausing, cancellation, expiration, and renewal will be
    handled through dedicated business services later.
    """

    queryset = (
        Subscription.objects
        .select_related(
            "customer",
            "plan",
            "plan__product",
        )
    )
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAdminUser]