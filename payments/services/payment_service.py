"""
============================================================
DMX Digital Solutions
Payments - Payment Service

Motto:
    Building Intelligent Digital Solutions
============================================================
"""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import models, transaction

from customers.models import Customer
from orders.models import Order
from payments.models import Payment
from payments.services.payment_number_service import (
    PaymentNumberService,
)
from subscriptions.models import Subscription


# Distinguishes an omitted currency argument from currency=None.
_CURRENCY_UNSET = object()


class PaymentService:
    """
    Handles payment creation and business validation.

    Payments may be associated with an order or a subscription.
    Order-linked payments must match the order's customer and
    currency and cannot exceed its remaining available balance.

    Creating a payment never marks it as successful.
    """

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        customer,
        amount,
        payment_method,
        currency=_CURRENCY_UNSET,
        subscription=None,
        order=None,
        description="",
        external_transaction_reference="",
    ):
        """
        Create a pending payment.

        Order-linked payments reserve available balance while
        pending or processing. Only successful payments count
        toward the order's paid total.

        If currency is omitted, ordinary payments default to USD
        and order-linked payments use the order's currency.
        Explicit currency=None is invalid for ordinary payments.
        For order-linked payments, None means use the order currency.

        Payment success must be confirmed separately through
        a controlled verification process.
        """

        customer = cls._resolve_customer(customer)
        subscription = cls._resolve_subscription(subscription)

        # Lock the order during validation and payment creation
        # to reduce the risk of concurrent overpayment.
        order = cls._resolve_order(order, lock=True)

        if order is not None and subscription is not None:
            raise ValidationError(
                "A payment cannot be linked to both an order "
                "and a subscription."
            )

        if (
            subscription is not None
            and subscription.customer_id != customer.pk
        ):
            raise ValidationError(
                "The subscription does not belong to the specified customer."
            )

        if order is not None:
            if order.customer_id != customer.pk:
                raise ValidationError(
                    "The order does not belong to the specified customer."
                )

            if order.status not in (
                Order.Status.CONFIRMED,
                Order.Status.PROCESSING,
            ):
                raise ValidationError(
                    "Payments can only be created for confirmed "
                    "or processing orders."
                )

            if order.subtotal <= Decimal("0.00"):
                raise ValidationError(
                    "Zero-total orders do not require a payment."
                )

            if currency is _CURRENCY_UNSET or currency is None:
                currency = order.currency

        else:
            if currency is _CURRENCY_UNSET:
                currency = "USD"
            elif currency is None:
                raise ValidationError(
                    "The currency must be a three-letter code."
                )

        amount = cls._resolve_amount(amount)

        if payment_method not in Payment.PaymentMethod.values:
            raise ValidationError(
                "The specified payment method is invalid."
            )

        currency = cls._resolve_currency(currency)

        if not isinstance(description, str):
            raise ValidationError(
                "The description must be text."
            )

        if not isinstance(external_transaction_reference, str):
            raise ValidationError(
                "The external transaction reference must be text."
            )

        if order is not None:
            if currency != order.currency:
                raise ValidationError(
                    "The payment currency must match the order currency."
                )

            cls._validate_order_balance(
                order=order,
                amount=amount,
                currency=currency,
            )

        return Payment.objects.create(
            payment_reference=PaymentNumberService.generate(),
            customer=customer,
            order=order,
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
    def _validate_order_balance(*, order, amount, currency):
        """
        Ensure the new payment does not exceed the unreserved
        order balance.

        Successful payments count toward the paid total.
        Pending and processing payments reserve balance.
        Failed, cancelled, and refunded payments do not reserve
        balance.
        """

        reserved_statuses = (
            Payment.Status.PENDING,
            Payment.Status.PROCESSING,
            Payment.Status.SUCCESSFUL,
        )

        reserved_total = (
            Payment.objects.filter(
                order=order,
                currency=currency,
                status__in=reserved_statuses,
            ).aggregate(
                total=models.Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        available_balance = order.subtotal - reserved_total

        if available_balance <= Decimal("0.00"):
            raise ValidationError(
                "This order has no remaining balance available for payment."
            )

        if amount > available_balance:
            raise ValidationError(
                "The payment amount exceeds the order's remaining "
                "available balance."
            )

    @staticmethod
    def _resolve_amount(amount):
        """
        Validate and normalize a monetary amount.
        """

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

        if len(amount.as_tuple().digits) > 12:
            raise ValidationError(
                "The payment amount exceeds the maximum permitted precision."
            )

        return amount

    @staticmethod
    def _resolve_currency(currency):
        """
        Validate and normalize a three-letter currency code.
        """

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

        return currency

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

    @staticmethod
    def _resolve_order(order, *, lock=False):
        if order is None:
            return None

        queryset = Order.objects

        if lock:
            queryset = queryset.select_for_update()

        try:
            if isinstance(order, Order):
                return queryset.get(pk=order.pk)

            return queryset.get(pk=order)
        except (
            Order.DoesNotExist,
            ValueError,
            TypeError,
        ):
            raise ValidationError(
                "The specified order does not exist."
            )
