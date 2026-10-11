from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from customers.models import Customer
from products.models import Product
from subscriptions.models import (
    Subscription,
    SubscriptionNumberCounter,
    SubscriptionPlan,
)
from subscriptions.serializers import (
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
)
from subscriptions.services.subscription_number_service import (
    SubscriptionNumberService,
)
from subscriptions.services.subscription_service import SubscriptionService


class SubscriptionNumberServiceTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_number="DMX-CUS-000001",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Example Organization",
        )

        self.product = Product.objects.create(
            name="DMX SmartSchool ERP",
        )

        self.plan = self.product.subscription_plans.create(
            name="Standard",
            price=Decimal("100.00"),
            currency="USD",
            billing_cycle="MONTHLY",
        )

    def create_subscription(self, subscription_number):
        return Subscription.objects.create(
            subscription_number=subscription_number,
            customer=self.customer,
            plan=self.plan,
            agreed_price=self.plan.price,
            currency=self.plan.currency,
        )

    def test_first_subscription_number(self):
        number = SubscriptionNumberService.generate()

        self.assertEqual(
            number,
            "DMX-SUB-000001",
        )

    def test_next_number_increments(self):
        self.create_subscription(
            "DMX-SUB-000001",
        )

        number = SubscriptionNumberService.generate()

        self.assertEqual(
            number,
            "DMX-SUB-000002",
        )

    def test_number_uses_expected_prefix_and_width(self):
        number = SubscriptionNumberService.generate()

        self.assertTrue(
            number.startswith("DMX-SUB-"),
        )

        self.assertEqual(
            len(number),
            len("DMX-SUB-000001"),
        )

    def test_malformed_reference_is_ignored(self):
        self.create_subscription(
            "DMX-SUB-ABC",
        )

        number = SubscriptionNumberService.generate()

        self.assertEqual(
            number,
            "DMX-SUB-000001",
        )

    def test_highest_number_is_used_when_sequence_has_a_gap(self):
        self.create_subscription(
            "DMX-SUB-000001",
        )
        self.create_subscription(
            "DMX-SUB-000003",
        )

        number = SubscriptionNumberService.generate()

        self.assertEqual(
            number,
            "DMX-SUB-000004",
        )

    def test_malformed_reference_does_not_override_highest_number(self):
        self.create_subscription(
            "DMX-SUB-000002",
        )
        self.create_subscription(
            "DMX-SUB-INVALID",
        )

        number = SubscriptionNumberService.generate()

        self.assertEqual(
            number,
            "DMX-SUB-000003",
        )


class SubscriptionNumberCounterTests(TestCase):
    def test_counter_is_created_on_first_allocation(self):
        number = SubscriptionNumberService.generate()

        self.assertEqual(
            number,
            "DMX-SUB-000001",
        )

        counter = SubscriptionNumberCounter.objects.get(
            name=SubscriptionNumberService.COUNTER_NAME,
        )

        self.assertEqual(
            counter.next_number,
            2,
        )

    def test_repeated_allocations_increment_counter(self):
        first = SubscriptionNumberService.generate()
        second = SubscriptionNumberService.generate()
        third = SubscriptionNumberService.generate()

        self.assertEqual(
            first,
            "DMX-SUB-000001",
        )
        self.assertEqual(
            second,
            "DMX-SUB-000002",
        )
        self.assertEqual(
            third,
            "DMX-SUB-000003",
        )

        counter = SubscriptionNumberCounter.objects.get(
            name=SubscriptionNumberService.COUNTER_NAME,
        )

        self.assertEqual(
            counter.next_number,
            4,
        )

    def test_existing_subscriptions_initialize_counter(self):
        customer = Customer.objects.create(
            customer_number="DMX-CUS-000001",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Existing Organization",
        )

        product = Product.objects.create(
            name="DMX SmartSchool ERP",
        )

        plan = product.subscription_plans.create(
            name="Existing Plan",
            price=Decimal("100.00"),
            currency="USD",
            billing_cycle="MONTHLY",
        )

        Subscription.objects.create(
            subscription_number="DMX-SUB-000004",
            customer=customer,
            plan=plan,
            agreed_price=plan.price,
            currency=plan.currency,
        )

        Subscription.objects.create(
            subscription_number="DMX-SUB-INVALID",
            customer=customer,
            plan=plan,
            agreed_price=plan.price,
            currency=plan.currency,
        )

        number = SubscriptionNumberService.generate()

        self.assertEqual(
            number,
            "DMX-SUB-000005",
        )


class SubscriptionServiceTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_number="DMX-CUS-000001",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Example Organization",
        )

        self.product = Product.objects.create(
            name="DMX SmartSchool ERP",
        )

        self.plan = self.product.subscription_plans.create(
            name="Standard",
            price=Decimal("100.00"),
            currency="USD",
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
        )

    def test_create_subscription(self):
        subscription = SubscriptionService.create(
            customer=self.customer,
            plan=self.plan,
        )

        self.assertEqual(
            subscription.subscription_number,
            "DMX-SUB-000001",
        )
        self.assertEqual(
            subscription.customer,
            self.customer,
        )
        self.assertEqual(
            subscription.plan,
            self.plan,
        )
        self.assertEqual(
            subscription.agreed_price,
            Decimal("100.00"),
        )
        self.assertEqual(
            subscription.currency,
            "USD",
        )
        self.assertEqual(
            subscription.status,
            Subscription.Status.PENDING,
        )
        self.assertFalse(subscription.auto_renew)

    def test_create_subscription_accepts_primary_keys(self):
        subscription = SubscriptionService.create(
            customer=self.customer.pk,
            plan=self.plan.pk,
        )

        self.assertEqual(
            subscription.customer_id,
            self.customer.pk,
        )
        self.assertEqual(
            subscription.plan_id,
            self.plan.pk,
        )

    def test_plan_price_is_snapshotted(self):
        subscription = SubscriptionService.create(
            customer=self.customer,
            plan=self.plan,
        )

        self.plan.price = Decimal("250.00")
        self.plan.save(update_fields=["price", "updated_at"])

        subscription.refresh_from_db()

        self.assertEqual(
            subscription.agreed_price,
            Decimal("100.00"),
        )

    def test_plan_currency_is_snapshotted(self):
        subscription = SubscriptionService.create(
            customer=self.customer,
            plan=self.plan,
        )

        self.plan.currency = "SSP"
        self.plan.save(update_fields=["currency", "updated_at"])

        subscription.refresh_from_db()

        self.assertEqual(
            subscription.currency,
            "USD",
        )

    def test_inactive_plan_cannot_create_subscription(self):
        self.plan.is_active = False
        self.plan.save(update_fields=["is_active", "updated_at"])

        with self.assertRaises(ValidationError):
            SubscriptionService.create(
                customer=self.customer,
                plan=self.plan,
            )

        self.assertEqual(
            Subscription.objects.count(),
            0,
        )

    def test_invalid_customer_is_rejected(self):
        with self.assertRaises(ValidationError):
            SubscriptionService.create(
                customer=999999,
                plan=self.plan,
            )

        self.assertEqual(
            Subscription.objects.count(),
            0,
        )

    def test_invalid_plan_is_rejected(self):
        with self.assertRaises(ValidationError):
            SubscriptionService.create(
                customer=self.customer,
                plan=999999,
            )

        self.assertEqual(
            Subscription.objects.count(),
            0,
        )

    def test_end_date_cannot_be_before_start_date(self):
        with self.assertRaises(ValidationError):
            SubscriptionService.create(
                customer=self.customer,
                plan=self.plan,
                start_date=date(2026, 10, 10),
                end_date=date(2026, 10, 9),
            )

        self.assertEqual(
            Subscription.objects.count(),
            0,
        )

    def test_subscription_dates_and_auto_renew_are_saved(self):
        subscription = SubscriptionService.create(
            customer=self.customer,
            plan=self.plan,
            status=Subscription.Status.ACTIVE,
            start_date=date(2026, 10, 8),
            end_date=date(2027, 10, 7),
            auto_renew=True,
        )

        self.assertEqual(
            subscription.status,
            Subscription.Status.ACTIVE,
        )
        self.assertEqual(
            subscription.start_date,
            date(2026, 10, 8),
        )
        self.assertEqual(
            subscription.end_date,
            date(2027, 10, 7),
        )
        self.assertTrue(subscription.auto_renew)


class SubscriptionSerializerTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_number="DMX-CUS-000001",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Example Organization",
        )

        self.product = Product.objects.create(
            name="DMX SmartSchool ERP",
        )

        self.plan = self.product.subscription_plans.create(
            name="Standard",
            price=Decimal("100.00"),
            currency="USD",
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
        )

    def test_subscription_plan_serializer_contains_expected_fields(self):
        serializer = SubscriptionPlanSerializer(
            instance=self.plan,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "product",
                "name",
                "description",
                "price",
                "currency",
                "billing_cycle",
                "is_active",
                "created_at",
                "updated_at",
            },
        )

    def test_subscription_serializer_contains_expected_fields(self):
        subscription = SubscriptionService.create(
            customer=self.customer,
            plan=self.plan,
        )

        serializer = SubscriptionSerializer(
            instance=subscription,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "subscription_number",
                "customer",
                "plan",
                "agreed_price",
                "currency",
                "status",
                "start_date",
                "end_date",
                "auto_renew",
                "cancelled_at",
                "created_at",
                "updated_at",
            },
        )

    def test_subscription_generated_fields_are_read_only(self):
        serializer = SubscriptionSerializer()

        self.assertTrue(
            serializer.fields["subscription_number"].read_only
        )
        self.assertTrue(
            serializer.fields["agreed_price"].read_only
        )
        self.assertTrue(
            serializer.fields["currency"].read_only
        )
        self.assertTrue(
            serializer.fields["cancelled_at"].read_only
        )

    def test_subscription_plan_system_fields_are_read_only(self):
        serializer = SubscriptionPlanSerializer()

        self.assertTrue(
            serializer.fields["id"].read_only
        )
        self.assertTrue(
            serializer.fields["created_at"].read_only
        )
        self.assertTrue(
            serializer.fields["updated_at"].read_only
        )


class SubscriptionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer = Customer.objects.create(
            customer_number="DMX-CUS-000001",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Example Organization",
        )

        self.product = Product.objects.create(
            name="DMX SmartSchool ERP",
        )

        self.active_plan = self.product.subscription_plans.create(
            name="Standard",
            price=Decimal("100.00"),
            currency="USD",
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            is_active=True,
        )

        self.inactive_plan = self.product.subscription_plans.create(
            name="Legacy",
            price=Decimal("50.00"),
            currency="USD",
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            is_active=False,
        )

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="subscription_test_user",
            password="test-password-for-automated-tests",
            is_staff=False,
        )

        self.staff_user = user_model.objects.create_user(
            username="subscription_staff_test_user",
            password="test-password-for-automated-tests",
            is_staff=True,
        )

        self.plans_url = "/api/v1/subscriptions/plans/"
        self.subscriptions_url = "/api/v1/subscriptions/subscriptions/"

    def test_active_plans_are_publicly_accessible(self):
        response = self.client.get(self.plans_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Standard")

    def test_inactive_plans_are_not_publicly_visible(self):
        response = self.client.get(self.plans_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        plan_names = [plan["name"] for plan in response.data]
        self.assertNotIn("Legacy", plan_names)

    def test_unauthenticated_subscription_list_is_rejected(self):
        response = self.client.get(self.subscriptions_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unauthenticated_subscription_creation_is_rejected(self):
        response = self.client.post(
            self.subscriptions_url,
            {
                "customer": self.customer.pk,
                "plan": self.active_plan.pk,
                "status": Subscription.Status.PENDING,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(Subscription.objects.count(), 0)

    def test_ordinary_authenticated_user_cannot_list_subscriptions(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.subscriptions_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_user_can_list_subscriptions(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(self.subscriptions_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_ordinary_authenticated_user_cannot_create_subscription(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.subscriptions_url,
            {
                "customer": self.customer.pk,
                "plan": self.active_plan.pk,
                "status": Subscription.Status.PENDING,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(Subscription.objects.count(), 0)

    @patch(
        "subscriptions.serializers.SubscriptionService.create",
        wraps=SubscriptionService.create,
    )
    def test_creation_uses_subscription_service(self, mocked_create):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            self.subscriptions_url,
            {
                "customer": self.customer.pk,
                "plan": self.active_plan.pk,
                "status": Subscription.Status.PENDING,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_create.assert_called_once()
        self.assertEqual(Subscription.objects.count(), 1)

    def test_inactive_plan_submission_returns_bad_request(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            self.subscriptions_url,
            {
                "customer": self.customer.pk,
                "plan": self.inactive_plan.pk,
                "status": Subscription.Status.PENDING,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Subscription.objects.count(), 0)