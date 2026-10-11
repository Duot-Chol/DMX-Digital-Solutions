from rest_framework.routers import DefaultRouter

from .views import SubscriptionPlanViewSet, SubscriptionViewSet


router = DefaultRouter()

router.register(
    r"plans",
    SubscriptionPlanViewSet,
    basename="subscription-plan",
)

router.register(
    r"subscriptions",
    SubscriptionViewSet,
    basename="subscription",
)

urlpatterns = router.urls