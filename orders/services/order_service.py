"""
============================================================
DMX Digital Solutions
Orders - Order Service

Motto:
    Building Intelligent Digital Solutions
============================================================
"""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from customers.models import Customer
from orders.models import Order, OrderItem
from orders.services.order_number_service import OrderNumberService
from products.models import Product
from subscriptions.models import SubscriptionPlan


class OrderService:
    """
    Handles order creation and purchase-item validation.

    One-time product prices are entered by authorized staff.
    Subscription items use the selected plan's current price.
    """

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        customer,
        items,
        notes="",
    ):
        """
        Create a draft order and its items.

        Expected item formats:

        One-time product:
            {
                "product": product_or_id,
                "quantity": 1,
                "unit_price": "100.00",
                "currency": "USD",
            }

        Subscription plan:
            {
                "subscription_plan": plan_or_id,
            }

        Subscription plans always use their current price,
        currency, name, and description.
        """

        customer = cls._resolve_customer(customer)

        if customer.status != Customer.Status.ACTIVE:
            raise ValidationError(
                "Orders can only be created for active customers."
            )

        if not isinstance(items, (list, tuple)) or not items:
            raise ValidationError(
                "An order must contain at least one item."
            )

        if not isinstance(notes, str):
            raise ValidationError("Order notes must be text.")

        prepared_items = []
        order_currency = None
        subtotal = Decimal("0.00")

        for item_data in items:
            if not isinstance(item_data, dict):
                raise ValidationError(
                    "Each order item must be an object."
                )

            product_value = item_data.get("product")
            plan_value = item_data.get("subscription_plan")

            if (product_value is None) == (plan_value is None):
                raise ValidationError(
                    "Each item must specify exactly one product "
                    "or subscription plan."
                )

            if plan_value is not None:
                if "quantity" in item_data:
                    quantity = cls._resolve_quantity(
                        item_data["quantity"]
                    )

                    if quantity != 1:
                        raise ValidationError(
                            "Subscription plan quantity must be one."
                        )

                plan = cls._resolve_plan(plan_value)

                if not plan.is_active:
                    raise ValidationError(
                        "The selected subscription plan is inactive."
                    )

                if plan.product.status != Product.Status.ACTIVE:
                    raise ValidationError(
                        "The product associated with this plan "
                        "is not available for purchase."
                    )

                quantity = 1
                unit_price = plan.price
                currency = cls._resolve_currency(plan.currency)

                description = (
                    f"{plan.product.name} - {plan.name}"
                )

                if plan.description.strip():
                    description = (
                        f"{description}: {plan.description.strip()}"
                    )

                prepared_items.append(
                    {
                        "product": None,
                        "subscription_plan": plan,
                        "item_description": description[:255],
                        "quantity": quantity,
                        "unit_price": unit_price,
                    }
                )

            else:
                product = cls._resolve_product(product_value)

                if product.status != Product.Status.ACTIVE:
                    raise ValidationError(
                        "Only active products can be ordered."
                    )

                if "unit_price" not in item_data:
                    raise ValidationError(
                        "A negotiated unit price is required "
                        "for a one-time product purchase."
                    )

                unit_price = cls._resolve_price(
                    item_data["unit_price"]
                )

                if unit_price <= Decimal("0.00"):
                    raise ValidationError(
                        "One-time product prices must be greater "
                        "than zero."
                    )

                quantity = cls._resolve_quantity(
                    item_data.get("quantity", 1)
                )

                currency = cls._resolve_currency(
                    item_data.get("currency", "USD")
                )

                description = (
                    f"{product.name}: {product.short_description}"
                )

                prepared_items.append(
                    {
                        "product": product,
                        "subscription_plan": None,
                        "item_description": description[:255],
                        "quantity": quantity,
                        "unit_price": unit_price,
                    }
                )

            if order_currency is None:
                order_currency = currency
            elif order_currency != currency:
                raise ValidationError(
                    "All items in an order must use the same currency."
                )

            line_total = unit_price * quantity

            cls._validate_money(line_total)

            prepared_items[-1]["line_total"] = line_total
            subtotal += line_total

            cls._validate_money(subtotal)

        order = Order.objects.create(
            order_number=OrderNumberService.generate(),
            customer=customer,
            status=Order.Status.DRAFT,
            currency=order_currency,
            subtotal=subtotal,
            notes=notes.strip(),
        )

        for item_data in prepared_items:
            OrderItem.objects.create(
                order=order,
                **item_data,
            )

        return order

    @staticmethod
    def _resolve_customer(customer):
        if isinstance(customer, Customer):
            return customer

        try:
            return Customer.objects.get(pk=customer)
        except (Customer.DoesNotExist, ValueError, TypeError):
            raise ValidationError(
                "The specified customer does not exist."
            )

    @staticmethod
    def _resolve_product(product):
        if isinstance(product, Product):
            return product

        try:
            return Product.objects.get(pk=product)
        except (Product.DoesNotExist, ValueError, TypeError):
            raise ValidationError(
                "The specified product does not exist."
            )

    @staticmethod
    def _resolve_plan(plan):
        if isinstance(plan, SubscriptionPlan):
            return plan

        try:
            return SubscriptionPlan.objects.select_related(
                "product"
            ).get(pk=plan)
        except (
            SubscriptionPlan.DoesNotExist,
            ValueError,
            TypeError,
        ):
            raise ValidationError(
                "The specified subscription plan does not exist."
            )

    @staticmethod
    def _resolve_quantity(value):
        if isinstance(value, bool):
            raise ValidationError(
                "Quantity must be a positive whole number."
            )

        try:
            quantity = int(value)
        except (TypeError, ValueError, OverflowError):
            raise ValidationError(
                "Quantity must be a positive whole number."
            )

        if str(value).strip() != str(quantity) or quantity < 1:
            raise ValidationError(
                "Quantity must be a positive whole number."
            )

        return quantity

    @staticmethod
    def _resolve_price(value):
        try:
            price = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError(
                "The unit price must be a valid number."
            )

        OrderService._validate_money(price)

        return price

    @staticmethod
    def _validate_money(amount):
        if not amount.is_finite() or amount < Decimal("0.00"):
            raise ValidationError(
                "Monetary amounts must be finite and non-negative."
            )

        if amount.as_tuple().exponent < -2:
            raise ValidationError(
                "Monetary amounts cannot have more than "
                "two decimal places."
            )

        if amount.adjusted() > 9 or len(amount.as_tuple().digits) > 12:
            raise ValidationError(
                "The monetary amount exceeds the permitted precision."
            )

    @staticmethod
    def _resolve_currency(currency):
        if not isinstance(currency, str):
            raise ValidationError(
                "Currency must be a three-letter code."
            )

        currency = currency.strip().upper()

        if (
            len(currency) != 3
            or not currency.isascii()
            or not currency.isalpha()
        ):
            raise ValidationError(
                "Currency must be a three-letter alphabetic code."
            )

        return currency