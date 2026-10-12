from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from customers.models import Customer
from payments.models import Payment
from payments.services.payment_number_service import (
    PaymentNumberService,
)
from subscriptions.models import Subscription


class PaymentService:
    """
    Handles payment creation and business validation.
    """

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        customer,
        amount,
        payment_method,
        currency="USD",
        subscription=None,
        description="",
        external_transaction_reference="",
    ):
        """
        Create a pending payment.

        Payment success must be confirmed separately through
        a controlled verification process.
        """

        customer = cls._resolve_customer(customer)
        subscription = cls._resolve_subscription(subscription)

        if (
            subscription is not None
            and subscription.customer_id != customer.pk
        ):
            raise ValidationError(
                "The subscription does not belong to the specified customer."
            )

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError(
                "The payment amount must be a valid number."
            )

        if not amount.is_finite() or amount <= Decimal("0.00"):
            raise ValidationError(
                "The payment amount must be greater than zero."
            )

        if amount.as_tuple().exponent < -2:
            raise ValidationError(
                "The payment amount cannot have more than two decimal places."
            )

        # DecimalField(max_digits=12, decimal_places=2) allows
        # at most 10 digits before the decimal point.
        if amount.adjusted() > 9:
            raise ValidationError(
                "The payment amount exceeds the maximum permitted value."
            )

        if not amount.is_zero() and len(amount.as_tuple().digits) > 12:
            raise ValidationError(
                "The payment amount exceeds the maximum permitted precision."
            )

        if payment_method not in Payment.PaymentMethod.values:
            raise ValidationError(
                "The specified payment method is invalid."
            )

        if not isinstance(currency, str):
            raise ValidationError(
                "The currency must be a three-letter code."
            )

        currency = currency.strip().upper()

        if (
            len(currency) != 3
            or not currency.isascii()
            or not currency.isalpha()
        ):
            raise ValidationError(
                "The currency must be a three-letter alphabetic code."
            )

        if not isinstance(description, str):
            raise ValidationError(
                "The description must be text."
            )

        if not isinstance(external_transaction_reference, str):
            raise ValidationError(
                "The external transaction reference must be text."
            )

        return Payment.objects.create(
            payment_reference=PaymentNumberService.generate(),
            customer=customer,
            subscription=subscription,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            status=Payment.Status.PENDING,
            description=description.strip(),
            external_transaction_reference=(
                external_transaction_reference.strip()
            ),
        )

    @staticmethod
    def _resolve_customer(customer):
        if isinstance(customer, Customer):
            return customer

        try:
            return Customer.objects.get(pk=customer)
        except (
            Customer.DoesNotExist,
            ValueError,
            TypeError,
        ):
            raise ValidationError(
                "The specified customer does not exist."
            )

    @staticmethod
    def _resolve_subscription(subscription):
        if subscription is None:
            return None

        if isinstance(subscription, Subscription):
            return subscription

        try:
            return Subscription.objects.get(pk=subscription)
        except (
            Subscription.DoesNotExist,
            ValueError,
            TypeError,
        ):
            raise ValidationError(
                "The specified subscription does not exist."
            )