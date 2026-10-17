"""
============================================================
DMX Digital Solutions
Orders - Tests
============================================================

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from customers.models import Customer
from orders.models import Order
from orders.services.order_lifecycle_service import (
    OrderLifecycleService,
)
from orders.services.order_service import OrderService
from payments.models import Payment
from payments.services.payment_service import PaymentService
from products.models import Product
from subscriptions.models import SubscriptionPlan


class OrderTestDataMixin:
    """Shared test data helpers for the Orders module."""

    def create_customer(self, suffix="1", status=None):
        data = {
            "customer_number": f"CUS-ORD-TEST-{suffix}",
            "customer_type": Customer.CustomerType.ORGANIZATION,
            "name": f"Orders Test Customer {suffix}",
        }

        if status is not None:
            data["status"] = status

        return Customer.objects.create(**data)

    def create_product(self, suffix="1", status=None):
        data = {
            "name": f"Orders Test Product {suffix}",
            "slug": f"orders-test-product-{suffix}",
            "short_description": "Product for order tests",
            "description": "Test product description",
            "status": status or Product.Status.ACTIVE,
        }

        return Product.objects.create(**data)

    def create_plan(
        self,
        product,
        suffix="1",
        price=Decimal("100.00"),
        currency="USD",
        is_active=True,
    ):
        return SubscriptionPlan.objects.create(
            product=product,
            name=f"Orders Test Plan {suffix}",
            description="Subscription plan for order tests",
            price=price,
            currency=currency,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            is_active=is_active,
        )

    def create_order(
        self,
        customer=None,
        product=None,
        suffix="1",
        unit_price=Decimal("100.00"),
        quantity=1,
        currency="USD",
    ):
        customer = customer or self.create_customer(suffix)
        product = product or self.create_product(suffix)

        return OrderService.create(
            customer=customer,
            items=[
                {
                    "product": product,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "currency": currency,
                }
            ],
            notes="Orders test",
        )

    def create_free_order(self, customer=None, suffix="free"):
        """Create a zero-total order using a zero-priced subscription plan."""
        customer = customer or self.create_customer(suffix)
        product = self.create_product(suffix)
        plan = self.create_plan(
            product,
            suffix=suffix,
            price=Decimal("0.00"),
        )
        return OrderService.create(
            customer=customer,
            items=[{"subscription_plan": plan}],
            notes="Free order test",
        )

    def create_staff_user(self, suffix="1"):
        User = get_user_model()

        return User.objects.create_user(
            username=f"orders_staff_{suffix}",
            password="test-password-not-for-production",
            is_staff=True,
            is_active=True,
        )


class OrderServiceTests(OrderTestDataMixin, TestCase):
    """Tests for order creation and item snapshots."""

    def test_creates_order_with_generated_number(self):
        order = self.create_order()

        self.assertTrue(order.order_number.startswith("DMX-ORD-"))
        self.assertEqual(order.status, Order.Status.DRAFT)
        self.assertEqual(order.payment_status, Order.PaymentStatus.UNPAID)
        self.assertEqual(order.subtotal, Decimal("100.00"))

    def test_snapshots_product_price_and_description(self):
        product = self.create_product()
        original_name = product.name

        order = self.create_order(
            product=product,
            unit_price=Decimal("125.50"),
            quantity=2,
        )

        item = order.items.get()

        self.assertEqual(item.unit_price, Decimal("125.50"))
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.line_total, Decimal("251.00"))
        self.assertIn(original_name, item.item_description)
        self.assertEqual(order.subtotal, Decimal("251.00"))

        product.name = "Renamed Product"
        product.save()

        item.refresh_from_db()

        self.assertIn(original_name, item.item_description)
        self.assertEqual(item.unit_price, Decimal("125.50"))

    def test_creates_order_from_subscription_plan(self):
        customer = self.create_customer()
        product = self.create_product()
        plan = self.create_plan(
            product,
            price=Decimal("75.00"),
            currency="USD",
        )

        order = OrderService.create(
            customer=customer,
            items=[{"subscription_plan": plan}],
        )

        item = order.items.get()

        self.assertEqual(item.product_id, None)
        self.assertEqual(item.subscription_plan_id, plan.pk)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.unit_price, Decimal("75.00"))
        self.assertEqual(item.line_total, Decimal("75.00"))
        self.assertEqual(order.currency, "USD")

    def test_plan_price_is_snapshotted(self):
        customer = self.create_customer()
        product = self.create_product()
        plan = self.create_plan(product, price=Decimal("75.00"))

        order = OrderService.create(
            customer=customer,
            items=[{"subscription_plan": plan}],
        )

        plan.price = Decimal("90.00")
        plan.save()

        item = order.items.get()

        self.assertEqual(item.unit_price, Decimal("75.00"))
        self.assertEqual(item.line_total, Decimal("75.00"))
        self.assertEqual(order.subtotal, Decimal("75.00"))

    def test_rejects_inactive_customer(self):
        customer = self.create_customer(
            status=Customer.Status.INACTIVE,
        )
        product = self.create_product()

        with self.assertRaises(ValidationError):
            OrderService.create(
                customer=customer,
                items=[
                    {
                        "product": product,
                        "quantity": 1,
                        "unit_price": Decimal("10.00"),
                    }
                ],
            )

    def test_rejects_inactive_product(self):
        customer = self.create_customer()
        product = self.create_product(
            status=Product.Status.DRAFT,
        )

        with self.assertRaises(ValidationError):
            OrderService.create(
                customer=customer,
                items=[
                    {
                        "product": product,
                        "quantity": 1,
                        "unit_price": Decimal("10.00"),
                    }
                ],
            )

    def test_rejects_inactive_subscription_plan(self):
        customer = self.create_customer()
        product = self.create_product()
        plan = self.create_plan(product, is_active=False)

        with self.assertRaises(ValidationError):
            OrderService.create(
                customer=customer,
                items=[{"subscription_plan": plan}],
            )

    def test_rejects_empty_order(self):
        customer = self.create_customer()

        with self.assertRaises(ValidationError):
            OrderService.create(
                customer=customer,
                items=[],
            )

    def test_rejects_mixed_currency_items(self):
        customer = self.create_customer()
        product_a = self.create_product("currency-a")
        product_b = self.create_product("currency-b")

        with self.assertRaises(ValidationError):
            OrderService.create(
                customer=customer,
                items=[
                    {
                        "product": product_a,
                        "quantity": 1,
                        "unit_price": Decimal("10.00"),
                        "currency": "USD",
                    },
                    {
                        "product": product_b,
                        "quantity": 1,
                        "unit_price": Decimal("10.00"),
                        "currency": "EUR",
                    },
                ],
            )


class OrderLifecycleServiceTests(OrderTestDataMixin, TestCase):
    """Tests for order status transitions and free-order approval."""

    def test_confirms_order_with_items(self):
        order = self.create_order()

        confirmed = OrderLifecycleService.confirm(order)

        self.assertEqual(confirmed.status, Order.Status.CONFIRMED)

    def test_draft_order_cannot_be_processed(self):
        order = self.create_order()

        with self.assertRaises(ValidationError):
            OrderLifecycleService.start_processing(order)

    def test_unpaid_order_cannot_be_processed(self):
        order = self.create_order()

        OrderLifecycleService.confirm(order)

        with self.assertRaises(ValidationError):
            OrderLifecycleService.start_processing(order)

    def test_free_order_requires_explicit_staff_approval(self):
        order = self.create_free_order()

        self.assertEqual(order.subtotal, Decimal("0.00"))
        self.assertEqual(order.payment_status, Order.PaymentStatus.UNPAID)

        with self.assertRaises(ValidationError):
            OrderLifecycleService.confirm(order)

    def test_approves_free_order_and_records_audit_fields(self):
        staff_user = self.create_staff_user()
        order = self.create_free_order()

        approved = OrderLifecycleService.approve_free_order(
            order,
            approved_by=staff_user,
        )

        self.assertEqual(approved.status, Order.Status.CONFIRMED)
        self.assertEqual(approved.free_order_approved_by_id, staff_user.pk)
        self.assertIsNotNone(approved.free_order_approved_at)
        self.assertEqual(approved.payment_status, Order.PaymentStatus.PAID)

    def test_rejects_free_order_approval_by_non_staff_user(self):
        User = get_user_model()

        regular_user = User.objects.create_user(
            username="orders_regular_user",
            password="test-password-not-for-production",
            is_staff=False,
            is_active=True,
        )

        order = self.create_free_order()

        with self.assertRaises(ValidationError):
            OrderLifecycleService.approve_free_order(
                order,
                approved_by=regular_user,
            )

    def test_cancels_confirmed_order(self):
        order = self.create_order()
        OrderLifecycleService.confirm(order)

        cancelled = OrderLifecycleService.cancel(order)

        self.assertEqual(cancelled.status, Order.Status.CANCELLED)

    def test_cannot_cancel_fulfilled_order(self):
        order = self.create_order()
        OrderLifecycleService.confirm(order)

        payment = Payment.objects.create(
            payment_reference="DMX-PAY-ORD-FULFILLED",
            customer=order.customer,
            order=order,
            amount=order.subtotal,
            currency=order.currency,
            payment_method=Payment.PaymentMethod.BANK_TRANSFER,
            status=Payment.Status.SUCCESSFUL,
        )

        self.assertIsNotNone(payment.pk)

        OrderLifecycleService.start_processing(order)
        fulfilled = OrderLifecycleService.fulfil(order)

        self.assertEqual(fulfilled.status, Order.Status.FULFILLED)

        with self.assertRaises(ValidationError):
            OrderLifecycleService.cancel(fulfilled)


class OrderPaymentIntegrationTests(OrderTestDataMixin, TestCase):
    """Tests for order-linked payments and outstanding balances."""

    def setUp(self):
        self.customer = self.create_customer()
        self.product = self.create_product()
        self.order = self.create_order(
            customer=self.customer,
            product=self.product,
            unit_price=Decimal("100.00"),
        )
        OrderLifecycleService.confirm(self.order)

    def create_order_payment(self, amount, currency=None):
        return PaymentService.create(
            customer=self.customer,
            order=self.order,
            amount=amount,
            payment_method=Payment.PaymentMethod.BANK_TRANSFER,
            currency=currency,
            description="Orders payment test",
        )

    def test_creates_pending_payment_linked_to_order(self):
        payment = self.create_order_payment(Decimal("40.00"))

        self.assertEqual(payment.order_id, self.order.pk)
        self.assertEqual(payment.customer_id, self.customer.pk)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.currency, self.order.currency)

    def test_pending_payment_does_not_count_as_paid(self):
        self.create_order_payment(Decimal("40.00"))

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.payment_status,
            Order.PaymentStatus.UNPAID,
        )

    def test_successful_partial_payment_is_reported_correctly(self):
        payment = self.create_order_payment(Decimal("40.00"))

        payment.status = Payment.Status.SUCCESSFUL
        payment.save(update_fields=["status"])

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.payment_status,
            Order.PaymentStatus.PARTIALLY_PAID,
        )

    def test_successful_full_payment_marks_order_paid(self):
        payment = self.create_order_payment(Decimal("100.00"))

        payment.status = Payment.Status.SUCCESSFUL
        payment.save(update_fields=["status"])

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.payment_status,
            Order.PaymentStatus.PAID,
        )

    def test_supports_multiple_partial_payments(self):
        first_payment = self.create_order_payment(Decimal("40.00"))

        first_payment.status = Payment.Status.SUCCESSFUL
        first_payment.save(update_fields=["status"])

        second_payment = self.create_order_payment(Decimal("60.00"))

        second_payment.status = Payment.Status.SUCCESSFUL
        second_payment.save(update_fields=["status"])

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.payment_status,
            Order.PaymentStatus.PAID,
        )

    def test_rejects_payment_for_another_customer(self):
        other_customer = self.create_customer("another")

        with self.assertRaises(ValidationError):
            PaymentService.create(
                customer=other_customer,
                order=self.order,
                amount=Decimal("10.00"),
                payment_method=Payment.PaymentMethod.BANK_TRANSFER,
            )

    def test_rejects_payment_currency_mismatch(self):
        with self.assertRaises(ValidationError):
            self.create_order_payment(
                Decimal("10.00"),
                currency="EUR",
            )

    def test_rejects_payment_above_outstanding_balance(self):
        with self.assertRaises(ValidationError):
            self.create_order_payment(Decimal("100.01"))

    def test_pending_payments_reserve_outstanding_balance(self):
        self.create_order_payment(Decimal("60.00"))

        with self.assertRaises(ValidationError):
            self.create_order_payment(Decimal("50.00"))

    def test_rejects_payment_for_draft_order(self):
        draft_order = self.create_order(
            customer=self.create_customer("draft"),
            product=self.create_product("draft"),
        )

        with self.assertRaises(ValidationError):
            PaymentService.create(
                customer=draft_order.customer,
                order=draft_order,
                amount=Decimal("10.00"),
                payment_method=Payment.PaymentMethod.BANK_TRANSFER,
            )

    def test_rejects_payment_for_zero_total_order(self):
        customer = self.create_customer("free-payment")
        free_order = self.create_free_order(
            customer=customer,
            suffix="free-payment",
        )

        OrderLifecycleService.approve_free_order(
            free_order,
            approved_by=self.create_staff_user("free-payment"),
        )

        with self.assertRaises(ValidationError):
            PaymentService.create(
                customer=customer,
                order=free_order,
                amount=Decimal("1.00"),
                payment_method=Payment.PaymentMethod.BANK_TRANSFER,
            )


class OrderAPITests(OrderTestDataMixin, TestCase):
    """Tests for staff access and Orders API behaviour."""

    def setUp(self):
        self.client = APIClient()
        self.staff_user = self.create_staff_user("api")
        self.customer = self.create_customer("api")
        self.product = self.create_product("api")

    def test_anonymous_user_cannot_list_orders(self):
        response = self.client.get("/api/v1/orders/")

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_user_can_list_orders(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get("/api/v1/orders/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_user_can_create_product_order(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.pk),
                "notes": "API order test",
                "items": [
                    {
                        "product": str(self.product.pk),
                        "quantity": 2,
                        "unit_price": "25.00",
                        "currency": "USD",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )
        self.assertEqual(response.data["status"], Order.Status.DRAFT)
        self.assertEqual(response.data["subtotal"], "50.00")
        self.assertEqual(len(response.data["items"]), 1)

    def test_staff_cannot_create_order_with_both_item_types(self):
        plan = self.create_plan(self.product, suffix="api")

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.pk),
                "items": [
                    {
                        "product": str(self.product.pk),
                        "subscription_plan": str(plan.pk),
                        "quantity": 1,
                        "unit_price": "25.00",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_client_cannot_set_order_status_during_creation(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            "/api/v1/orders/",
            {
                "customer": str(self.customer.pk),
                "status": "FULFILLED",
                "items": [
                    {
                        "product": str(self.product.pk),
                        "quantity": 1,
                        "unit_price": "25.00",
                        "currency": "USD",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )
        self.assertEqual(response.data["status"], Order.Status.DRAFT)

    def test_staff_can_confirm_order_through_lifecycle_action(self):
        order = self.create_order(
            customer=self.customer,
            product=self.product,
            suffix="api-confirm",
        )
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            f"/api/v1/orders/{order.pk}/confirm/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )
        self.assertEqual(response.data["status"], Order.Status.CONFIRMED)

    def test_client_cannot_delete_order(self):
        order = self.create_order(
            customer=self.customer,
            product=self.product,
            suffix="api-delete",
        )
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.delete(
            f"/api/v1/orders/{order.pk}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )