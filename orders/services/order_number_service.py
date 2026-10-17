"""
============================================================
DMX Digital Solutions
Orders - Order Number Service

Motto:
    Building Intelligent Digital Solutions
============================================================
"""

from django.db import transaction

from orders.models import Order, OrderNumberCounter


class OrderNumberService:
    """
    Generates unique order references.

    Format: DMX-ORD-000001
    """

    PREFIX = "DMX-ORD-"
    NUMBER_WIDTH = 6
    COUNTER_NAME = "ORDER"

    @classmethod
    @transaction.atomic
    def generate(cls):
        """
        Allocate the next order number.

        Initialize the counter from existing order references
        if the counter does not yet exist.
        """

        counter, created = OrderNumberCounter.objects.get_or_create(
            name=cls.COUNTER_NAME,
            defaults={"next_number": 1},
        )

        if created:
            highest_number = 0

            existing_numbers = Order.objects.filter(
                order_number__startswith=cls.PREFIX
            ).values_list("order_number", flat=True)

            for order_number in existing_numbers:
                suffix = order_number[len(cls.PREFIX):]

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