from django.db import transaction

from payments.models import Payment, PaymentNumberCounter


class PaymentNumberService:
    """Generate sequential DMX payment references."""

    PREFIX = "DMX-PAY-"
    NUMBER_WIDTH = 6
    COUNTER_NAME = "PAYMENT"

    @classmethod
    @transaction.atomic
    def generate(cls):
        counter, created = PaymentNumberCounter.objects.get_or_create(
            name=cls.COUNTER_NAME,
            defaults={"next_number": 1},
        )

        if created:
            highest_number = 0

            references = Payment.objects.filter(
                payment_reference__startswith=cls.PREFIX
            ).values_list("payment_reference", flat=True)

            for reference in references:
                suffix = reference[len(cls.PREFIX):]

                if suffix.isdigit():
                    highest_number = max(
                        highest_number,
                        int(suffix),
                    )

            counter.next_number = highest_number + 1

        allocated_number = counter.next_number
        counter.next_number = allocated_number + 1
        counter.save(update_fields=["next_number", "updated_at"])

        return (
            f"{cls.PREFIX}"
            f"{allocated_number:0{cls.NUMBER_WIDTH}d}"
        )