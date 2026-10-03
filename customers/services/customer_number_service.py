from django.db import transaction

from customers.models import Customer, CustomerNumberCounter


class CustomerNumberService:
    """
    Generates customer references for DMX Digital Solutions.

    Format: DMX-CUS-000001
    """

    PREFIX = "DMX-CUS-"
    NUMBER_WIDTH = 6
    COUNTER_NAME = "CUSTOMER"

    @classmethod
    @transaction.atomic
    def generate(cls):
        """
        Reserve and return the next customer number.

        The counter is initialized from existing valid customer references
        so that previously allocated numbers are not reused.
        """
        counter, created = CustomerNumberCounter.objects.get_or_create(
            name=cls.COUNTER_NAME,
            defaults={"next_number": 1},
        )

        if created:
            highest_number = 0

            existing_numbers = Customer.objects.filter(
                customer_number__startswith=cls.PREFIX
            ).values_list("customer_number", flat=True)

            for customer_number in existing_numbers:
                suffix = customer_number[len(cls.PREFIX):]

                if suffix.isdigit():
                    highest_number = max(highest_number, int(suffix))

            counter.next_number = highest_number + 1

        allocated_number = counter.next_number
        counter.next_number = allocated_number + 1
        counter.save(update_fields=["next_number", "updated_at"])

        return (
            f"{cls.PREFIX}"
            f"{allocated_number:0{cls.NUMBER_WIDTH}d}"
        )