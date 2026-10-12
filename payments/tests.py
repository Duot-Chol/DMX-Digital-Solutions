import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APITestCase

from customers.models import Customer
from payments.models import Payment, PaymentNumberCounter
from payments.services.payment_number_service import PaymentNumberService
from payments.services.payment_service import PaymentService
from products.models import Product
from subscriptions.models import Subscription, SubscriptionPlan
from subscriptions.services.subscription_service import SubscriptionService


class PaymentTestDataMixin:
    """Shared test data helpers for the Payments module."""

    def create_customer(self, suffix="1"):
        return Customer.objects.create(
            customer_number=f"CUS-TEST-{suffix}",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name=f"Test customer {suffix}",
        )

    def create_product(self, suffix="1"):
        return Product.objects.create(
            name=f"Test product {suffix}",
            slug=f"test-product-{suffix}",
            short_description="Product for payment tests",
            description="Test product description",
            status=Product.Status.ACTIVE,
        )

    def create_subscription(self, customer, suffix="1"):
        product = self.create_product(suffix)

        plan = SubscriptionPlan.objects.create(
            product=product,
            name=f"Test plan {suffix}",
            price=Decimal("100.00"),
            currency="USD",
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
        )

        return SubscriptionService.create(customer, plan)

    def create_payment(self, reference):
        customer = self.create_customer(
            suffix=reference.replace("-", "")
        )

        return Payment.objects.create(
            payment_reference=reference,
            customer=customer,
            amount=Decimal("10.00"),
            currency="USD",
            payment_method=Payment.PaymentMethod.BANK_TRANSFER,
        )


class PaymentNumberServiceTests(PaymentTestDataMixin, TestCase):

    def test_first_payment_reference(self):
        reference = PaymentNumberService.generate()

        self.assertEqual(reference, "DMX-PAY-000001")

    def test_next_reference_increments(self):
        self.create_payment("DMX-PAY-000001")

        reference = PaymentNumberService.generate()

        self.assertEqual(reference, "DMX-PAY-000002")

    def test_reference_uses_expected_prefix_and_width(self):
        reference = PaymentNumberService.generate()

        self.assertTrue(reference.startswith("DMX-PAY-"))
        self.assertEqual(len(reference), len("DMX-PAY-000001"))

    def test_malformed_reference_is_ignored(self):
        self.create_payment("DMX-PAY-ABC")

        reference = PaymentNumberService.generate()

        self.assertEqual(reference, "DMX-PAY-000001")

    def test_highest_reference_is_used_when_sequence_has_a_gap(self):
        self.create_payment("DMX-PAY-000001")
        self.create_payment("DMX-PAY-000003")

        reference = PaymentNumberService.generate()

        self.assertEqual(reference, "DMX-PAY-000004")

    def test_malformed_reference_does_not_override_highest_number(self):
        self.create_payment("DMX-PAY-000002")
        self.create_payment("DMX-PAY-INVALID")

        reference = PaymentNumberService.generate()

        self.assertEqual(reference, "DMX-PAY-000003")


class PaymentNumberCounterTests(PaymentTestDataMixin, TestCase):

    def test_counter_is_created_on_first_allocation(self):
        reference = PaymentNumberService.generate()

        self.assertEqual(reference, "DMX-PAY-000001")

        counter = PaymentNumberCounter.objects.get(
            name=PaymentNumberService.COUNTER_NAME
        )
        self.assertEqual(counter.next_number, 2)

    def test_repeated_allocations_increment_counter(self):
        first = PaymentNumberService.generate()
        second = PaymentNumberService.generate()
        third = PaymentNumberService.generate()

        self.assertEqual(first, "DMX-PAY-000001")
        self.assertEqual(second, "DMX-PAY-000002")
        self.assertEqual(third, "DMX-PAY-000003")

    def test_existing_payments_initialize_counter(self):
        self.create_payment("DMX-PAY-000004")
        self.create_payment("DMX-PAY-INVALID")

        reference = PaymentNumberService.generate()

        self.assertEqual(reference, "DMX-PAY-000005")


class PaymentServiceTests(PaymentTestDataMixin, TestCase):

    def setUp(self):
        self.customer = self.create_customer("SERVICE-1")

    def create_service_payment(self, **overrides):
        data = {
            "customer": self.customer,
            "amount": "25.50",
            "payment_method": Payment.PaymentMethod.BANK_TRANSFER,
        }
        data.update(overrides)

        return PaymentService.create(**data)

    def test_creates_pending_payment_with_generated_reference(self):
        payment = self.create_service_payment()

        self.assertEqual(payment.payment_reference, "DMX-PAY-000001")
        self.assertEqual(payment.customer, self.customer)
        self.assertEqual(payment.amount, Decimal("25.50"))
        self.assertEqual(payment.currency, "USD")
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertIsNone(payment.paid_at)

    def test_accepts_customer_primary_key(self):
        payment = self.create_service_payment(
            customer=self.customer.pk
        )

        self.assertEqual(payment.customer, self.customer)

    def test_normalizes_currency_and_trims_text(self):
        payment = self.create_service_payment(
            currency=" usd ",
            description="  Annual subscription  ",
            external_transaction_reference="  BANK-123  ",
        )

        self.assertEqual(payment.currency, "USD")
        self.assertEqual(payment.description, "Annual subscription")
        self.assertEqual(
            payment.external_transaction_reference,
            "BANK-123",
        )

    def test_creates_payment_without_subscription(self):
        payment = self.create_service_payment()

        self.assertIsNone(payment.subscription)

    def test_accepts_subscription_instance(self):
        subscription = self.create_subscription(
            self.customer,
            "SUB-INSTANCE",
        )

        payment = self.create_service_payment(
            subscription=subscription
        )

        self.assertEqual(payment.subscription, subscription)

    def test_accepts_subscription_primary_key(self):
        subscription = self.create_subscription(
            self.customer,
            "SUB-PK",
        )

        payment = self.create_service_payment(
            subscription=subscription.pk
        )

        self.assertEqual(payment.subscription, subscription)

    def test_rejects_subscription_owned_by_another_customer(self):
        other_customer = self.create_customer("OTHER")
        subscription = self.create_subscription(
            other_customer,
            "SUB-OTHER",
        )

        with self.assertRaises(ValidationError):
            self.create_service_payment(subscription=subscription)

        self.assertEqual(Payment.objects.count(), 0)

    def test_rejects_nonexistent_customer(self):
        with self.assertRaises(ValidationError):
            self.create_service_payment(
                customer=uuid.uuid4()
            )

        self.assertEqual(Payment.objects.count(), 0)

    def test_rejects_nonexistent_subscription(self):
        with self.assertRaises(ValidationError):
            self.create_service_payment(
                subscription=uuid.uuid4()
            )

        self.assertEqual(Payment.objects.count(), 0)

    def test_rejects_invalid_amounts(self):
        invalid_amounts = [
            "0",
            "-1",
            "NaN",
            "Infinity",
            "-Infinity",
            "not-a-number",
            None,
            "1.234",
            "10000000000.00",
        ]

        for amount in invalid_amounts:
            with self.subTest(amount=amount):
                with self.assertRaises(ValidationError):
                    self.create_service_payment(amount=amount)

        self.assertEqual(Payment.objects.count(), 0)

    def test_rejects_invalid_payment_method(self):
        with self.assertRaises(ValidationError):
            self.create_service_payment(
                payment_method="CRYPTO"
            )

        self.assertEqual(Payment.objects.count(), 0)

    def test_rejects_invalid_currency_formats(self):
        invalid_currencies = [
            "",
            "US",
            "USDD",
            "12D",
            "€UR",
            "U$D",
            None,
            123,
        ]

        for currency in invalid_currencies:
            with self.subTest(currency=currency):
                with self.assertRaises(ValidationError):
                    self.create_service_payment(currency=currency)

        self.assertEqual(Payment.objects.count(), 0)

    def test_rejects_non_text_description(self):
        with self.assertRaises(ValidationError):
            self.create_service_payment(description=123)

        self.assertEqual(Payment.objects.count(), 0)

    def test_rejects_non_text_external_reference(self):
        with self.assertRaises(ValidationError):
            self.create_service_payment(
                external_transaction_reference=123
            )

        self.assertEqual(Payment.objects.count(), 0)


class PaymentAPITests(PaymentTestDataMixin, APITestCase):
    """API tests for payment permissions and operations."""

    def setUp(self):
        self.customer = self.create_customer("API-1")
        self.list_url = "/api/v1/payments/"

        user_model = get_user_model()

        self.staff_user = user_model.objects.create_user(
            username="payments-staff",
            password="test-password",
            is_staff=True,
        )

        self.regular_user = user_model.objects.create_user(
            username="payments-regular",
            password="test-password",
            is_staff=False,
        )

    def authenticate_staff(self):
        self.client.force_authenticate(user=self.staff_user)

    def test_unauthenticated_user_cannot_list_payments(self):
        response = self.client.get(self.list_url)

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

    def test_regular_user_cannot_list_payments(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_user_can_list_payments(self):
        self.authenticate_staff()

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_staff_user_can_create_pending_payment(self):
        self.authenticate_staff()

        response = self.client.post(
            self.list_url,
            {
                "customer": str(self.customer.pk),
                "amount": "125.50",
                "currency": "USD",
                "payment_method": Payment.PaymentMethod.BANK_TRANSFER,
                "description": "API payment test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payment = Payment.objects.get()

        self.assertEqual(
            payment.payment_reference,
            "DMX-PAY-000001",
        )
        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )
        self.assertEqual(
            payment.amount,
            Decimal("125.50"),
        )

    def test_unauthenticated_user_cannot_create_payment(self):
        response = self.client.post(
            self.list_url,
            {
                "customer": str(self.customer.pk),
                "amount": "25.00",
                "payment_method": Payment.PaymentMethod.CASH,
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

        self.assertEqual(Payment.objects.count(), 0)

    def test_client_cannot_set_successful_status(self):
        self.authenticate_staff()

        response = self.client.post(
            self.list_url,
            {
                "customer": str(self.customer.pk),
                "amount": "25.00",
                "payment_method": Payment.PaymentMethod.CASH,
                "status": Payment.Status.SUCCESSFUL,
                "paid_at": "2026-10-12T10:00:00Z",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payment = Payment.objects.get()

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )
        self.assertIsNone(payment.paid_at)

    def test_staff_can_retrieve_payment(self):
        payment = Payment.objects.create(
            payment_reference="DMX-PAY-API-0001",
            customer=self.customer,
            amount=Decimal("40.00"),
            currency="USD",
            payment_method=Payment.PaymentMethod.CASH,
        )

        self.authenticate_staff()

        response = self.client.get(
            f"{self.list_url}{payment.pk}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["payment_reference"],
            payment.payment_reference,
        )

    def test_regular_user_cannot_retrieve_payment(self):
        payment = Payment.objects.create(
            payment_reference="DMX-PAY-API-0002",
            customer=self.customer,
            amount=Decimal("40.00"),
            currency="USD",
            payment_method=Payment.PaymentMethod.CASH,
        )

        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(
            f"{self.list_url}{payment.pk}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_payment_detail_does_not_allow_modification_or_deletion(self):
        payment = Payment.objects.create(
            payment_reference="DMX-PAY-API-0003",
            customer=self.customer,
            amount=Decimal("40.00"),
            currency="USD",
            payment_method=Payment.PaymentMethod.CASH,
        )

        self.authenticate_staff()

        url = f"{self.list_url}{payment.pk}/"

        for method in ("put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    url,
                    {"description": "Attempted modification"},
                    format="json",
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_405_METHOD_NOT_ALLOWED,
                )

        payment.refresh_from_db()

        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.amount, Decimal("40.00"))