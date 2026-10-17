
"""
============================================================
DMX Digital Solutions
Orders - Order Lifecycle Service

Motto:
    Building Intelligent Digital Solutions
============================================================
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from orders.models import Order


class OrderLifecycleService:
    """
    Controls order status transitions.

    Valid workflow:
        DRAFT -> CONFIRMED -> PROCESSING -> FULFILLED

    Free orders require explicit approval by an active staff
    user. The approving user and approval timestamp are stored
    for auditing.

    Cancellation never deletes an order or automatically
    reverses a successful payment.
    """

    @classmethod
    @transaction.atomic
    def confirm(cls, order):
        """
        Confirm a draft order with a positive total.

        Zero-total orders must use approve_free_order().
        """

        order = cls._resolve_order(order, lock=True)

        if order.status != Order.Status.DRAFT:
            raise ValidationError(
                "Only draft orders can be confirmed."
            )

        if not order.items.exists():
            raise ValidationError(
                "An order must contain at least one item."
            )

        if order.subtotal <= Decimal("0.00"):
            raise ValidationError(
                "Zero-total orders require explicit staff approval "
                "through the free-order approval workflow."
            )

        cls._set_status(order, Order.Status.CONFIRMED)

        return order

    @classmethod
    @transaction.atomic
    def approve_free_order(cls, order, *, approved_by):
        """
        Approve and confirm a zero-total order.

        An authenticated, active staff user must be supplied.
        The approval user and timestamp are saved together with
        the confirmation status.
        """

        order = cls._resolve_order(order, lock=True)
        approver = cls._resolve_approver(approved_by)

        if order.status != Order.Status.DRAFT:
            raise ValidationError(
                "Only draft orders can be approved as free orders."
            )

        if not order.items.exists():
            raise ValidationError(
                "An order must contain at least one item."
            )

        if order.subtotal != Decimal("0.00"):
            raise ValidationError(
                "Only zero-total orders qualify for free-order approval."
            )

        order.free_order_approved_by = approver
        order.free_order_approved_at = timezone.now()
        order.status = Order.Status.CONFIRMED

        order.save(
            update_fields=[
                "free_order_approved_by",
                "free_order_approved_at",
                "status",
                "updated_at",
            ]
        )

        return order

    @classmethod
    @transaction.atomic
    def start_processing(cls, order):
        """
        Move a confirmed order into processing.

        Positive-total orders require full verified payment.
        Zero-total orders require recorded staff approval.
        """

        order = cls._resolve_order(order, lock=True)

        if order.status != Order.Status.CONFIRMED:
            raise ValidationError(
                "Only confirmed orders can enter processing."
            )

        if order.subtotal > Decimal("0.00"):
            if order.payment_status != Order.PaymentStatus.PAID:
                raise ValidationError(
                    "Payment must be verified in full before "
                    "processing this order."
                )
        elif not cls._has_free_order_approval(order):
            raise ValidationError(
                "Free-order approval must be recorded before "
                "processing this order."
            )

        cls._set_status(order, Order.Status.PROCESSING)

        return order

    @classmethod
    @transaction.atomic
    def fulfil(cls, order):
        """
        Fulfil an order after its payment or free-order
        approval requirements have been satisfied.
        """

        order = cls._resolve_order(order, lock=True)

        if order.status != Order.Status.PROCESSING:
            raise ValidationError(
                "Only processing orders can be fulfilled."
            )

        if order.subtotal > Decimal("0.00"):
            if order.payment_status != Order.PaymentStatus.PAID:
                raise ValidationError(
                    "Full verified payment is required before fulfilment."
                )
        elif not cls._has_free_order_approval(order):
            raise ValidationError(
                "Free-order approval must be recorded before fulfilment."
            )

        cls._set_status(order, Order.Status.FULFILLED)

        return order

    @classmethod
    @transaction.atomic
    def cancel(cls, order):
        """
        Cancel an order that has not been fulfilled.

        Successful payments, if any, are preserved. Refunds must
        be handled through a separate controlled process.
        """

        order = cls._resolve_order(order, lock=True)

        if order.status in (
            Order.Status.FULFILLED,
            Order.Status.CANCELLED,
        ):
            raise ValidationError(
                "This order cannot be cancelled in its current state."
            )

        cls._set_status(order, Order.Status.CANCELLED)

        return order

    @staticmethod
    def _resolve_approver(approved_by):
        """
        Resolve an active staff user for free-order approval.
        """

        User = get_user_model()

        if approved_by is None:
            raise ValidationError(
                "An authorized staff user must approve a free order."
            )

        if isinstance(approved_by, User):
            user = approved_by
        else:
            try:
                user = User.objects.get(pk=approved_by)
            except (
                User.DoesNotExist,
                ValueError,
                TypeError,
            ):
                raise ValidationError(
                    "The specified approving user does not exist."
                )

        if not user.is_active or not user.is_staff:
            raise ValidationError(
                "Only active staff users can approve free orders."
            )

        return user

    @staticmethod
    def _has_free_order_approval(order):
        """
        Confirm that both required approval audit fields exist.
        """

        return (
            order.free_order_approved_by_id is not None
            and order.free_order_approved_at is not None
        )

    @staticmethod
    def _resolve_order(order, *, lock=False):
        if isinstance(order, Order):
            order_id = order.pk
        else:
            order_id = order

        queryset = Order.objects

        if lock:
            queryset = queryset.select_for_update()

        try:
            return queryset.get(pk=order_id)
        except (
            Order.DoesNotExist,
            ValueError,
            TypeError,
        ):
            raise ValidationError(
                "The specified order does not exist."
            )

    @staticmethod
    def _set_status(order, status):
        order.status = status
        order.save(update_fields=["status", "updated_at"])
