from django.db import transaction

from subscriptions.models import Subscription, SubscriptionNumberCounter


class SubscriptionNumberService:
    """
    Generates subscription references for DMX Digital Solutions.

    Format: DMX-SUB-000001
    """

    PREFIX = "DMX-SUB-"
    NUMBER_WIDTH = 6
    COUNTER_NAME = "SUBSCRIPTION"

    @classmethod
    @transaction.atomic
    def generate(cls):
        """
        Reserve and return the next subscription number.

        The counter is initialized from existing valid subscription
        references so that previously allocated numbers are not reused.
        """
        counter, created = SubscriptionNumberCounter.objects.get_or_create(
            name=cls.COUNTER_NAME,
            defaults={"next_number": 1},
        )

        if created:
            highest_number = 0

            existing_numbers = Subscription.objects.filter(
                subscription_number__startswith=cls.PREFIX
            ).values_list("subscription_number", flat=True)

            for subscription_number in existing_numbers:
                suffix = subscription_number[len(cls.PREFIX):]

                if suffix.isdigit():
                    highest_number = max(
                        highest_number,
                        int(suffix),
                    )

            counter.next_number = highest_number + 1

        allocated_number = counter.next_number

        counter.next_number = allocated_number + 1
        counter.save(
            update_fields=[
                "next_number",
                "updated_at",
            ]
        )

        return (
            f"{cls.PREFIX}"
            f"{allocated_number:0{cls.NUMBER_WIDTH}d}"
        )