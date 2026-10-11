from django.core.exceptions import ValidationError
from django.db import transaction

from customers.models import Customer
from subscriptions.models import Subscription, SubscriptionPlan
from subscriptions.services.subscription_number_service import (
    SubscriptionNumberService,
)


class SubscriptionService:
    """
    Handles subscription creation for DMX Digital Solutions.
    """

    @classmethod
    @transaction.atomic
    def create(
        cls,
        customer,
        plan,
        *,
        status=Subscription.Status.PENDING,
        start_date=None,
        end_date=None,
        auto_renew=False,
    ):
        """
        Create a subscription for a customer.

        The subscription number is generated automatically, while the
        plan's current price and currency are captured as a snapshot.
        """

        if not isinstance(customer, Customer):
            try:
                customer = Customer.objects.get(pk=customer)
            except (Customer.DoesNotExist, ValueError, TypeError):
                raise ValidationError(
                    "The specified customer does not exist."
                )

        if not isinstance(plan, SubscriptionPlan):
            try:
                plan = SubscriptionPlan.objects.get(pk=plan)
            except (SubscriptionPlan.DoesNotExist, ValueError, TypeError):
                raise ValidationError(
                    "The specified subscription plan does not exist."
                )

        if not plan.is_active:
            raise ValidationError(
                "The selected subscription plan is inactive."
            )

        if start_date and end_date and end_date < start_date:
            raise ValidationError(
                "The subscription end date cannot be earlier than "
                "the start date."
            )

        return Subscription.objects.create(
            subscription_number=SubscriptionNumberService.generate(),
            customer=customer,
            plan=plan,
            agreed_price=plan.price,
            currency=plan.currency,
            status=status,
            start_date=start_date,
            end_date=end_date,
            auto_renew=auto_renew,
        )