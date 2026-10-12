from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from customers.models import Customer, CustomerNumberCounter
from customers.services.customer_number_service import CustomerNumberService
from customers.services.customer_service import CustomerService
from leads.models import Lead


User = get_user_model()


class CustomerNumberServiceTests(TestCase):
    def test_first_customer_number(self):
        number = CustomerNumberService.generate()

        self.assertEqual(number, "DMX-CUS-000001")

    def test_next_number_increments(self):
        Customer.objects.create(
            customer_number="DMX-CUS-000001",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Example Organization",
        )

        number = CustomerNumberService.generate()

        self.assertEqual(number, "DMX-CUS-000002")

    def test_number_uses_expected_prefix_and_width(self):
        number = CustomerNumberService.generate()

        self.assertTrue(number.startswith("DMX-CUS-"))
        self.assertEqual(len(number), len("DMX-CUS-000001"))

    def test_malformed_reference_is_ignored(self):
        Customer.objects.create(
            customer_number="DMX-CUS-ABC",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Malformed Reference Organization",
        )

        number = CustomerNumberService.generate()

        self.assertEqual(number, "DMX-CUS-000001")

    def test_highest_number_is_used_when_sequence_has_a_gap(self):
        Customer.objects.create(
            customer_number="DMX-CUS-000001",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="First Organization",
        )
        Customer.objects.create(
            customer_number="DMX-CUS-000003",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Third Organization",
        )

        number = CustomerNumberService.generate()

        self.assertEqual(number, "DMX-CUS-000004")

    def test_malformed_reference_does_not_override_highest_number(self):
        Customer.objects.create(
            customer_number="DMX-CUS-000002",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Valid Reference Organization",
        )
        Customer.objects.create(
            customer_number="DMX-CUS-INVALID",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Invalid Reference Organization",
        )

        number = CustomerNumberService.generate()

        self.assertEqual(number, "DMX-CUS-000003")


class CustomerNumberCounterTests(TestCase):
    def test_counter_is_created_on_first_allocation(self):
        number = CustomerNumberService.generate()

        self.assertEqual(number, "DMX-CUS-000001")

        counter = CustomerNumberCounter.objects.get(
            name=CustomerNumberService.COUNTER_NAME
        )
        self.assertEqual(counter.next_number, 2)

    def test_repeated_allocations_increment_counter(self):
        first = CustomerNumberService.generate()
        second = CustomerNumberService.generate()
        third = CustomerNumberService.generate()

        self.assertEqual(first, "DMX-CUS-000001")
        self.assertEqual(second, "DMX-CUS-000002")
        self.assertEqual(third, "DMX-CUS-000003")

    def test_existing_customers_initialize_counter(self):
        Customer.objects.create(
            customer_number="DMX-CUS-000004",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Existing Organization",
        )
        Customer.objects.create(
            customer_number="DMX-CUS-INVALID",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Malformed Reference Organization",
        )

        number = CustomerNumberService.generate()

        self.assertEqual(number, "DMX-CUS-000005")


class CustomerConversionTests(TestCase):
    def setUp(self):
        self.lead = Lead.objects.create(
            full_name="Jane Doe",
            email="jane@example.com",
            phone="+211900000000",
            organization="Example Organization",
            subject="DMX SmartSchool ERP",
            message="Interested in purchasing the system.",
            status=Lead.Status.QUALIFIED,
        )

    def test_qualified_organization_lead_converts_successfully(self):
        customer = CustomerService.convert_qualified_lead(self.lead.pk)

        self.assertEqual(customer.name, "Example Organization")
        self.assertEqual(customer.email, "jane@example.com")
        self.assertEqual(customer.phone, "+211900000000")
        self.assertEqual(
            customer.customer_type,
            Customer.CustomerType.ORGANIZATION,
        )
        self.assertEqual(customer.originating_lead, self.lead)

        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, Lead.Status.CONVERTED)

    def test_individual_lead_uses_full_name(self):
        self.lead.organization = ""
        self.lead.save(update_fields=["organization"])

        customer = CustomerService.convert_qualified_lead(self.lead.pk)

        self.assertEqual(customer.name, "Jane Doe")
        self.assertEqual(
            customer.customer_type,
            Customer.CustomerType.INDIVIDUAL,
        )

    def test_unqualified_lead_cannot_be_converted(self):
        self.lead.status = Lead.Status.NEW
        self.lead.save(update_fields=["status"])

        with self.assertRaises(ValidationError):
            CustomerService.convert_qualified_lead(self.lead.pk)

        self.assertEqual(Customer.objects.count(), 0)

    def test_missing_lead_cannot_be_converted(self):
        with self.assertRaises(ValidationError):
            CustomerService.convert_qualified_lead(999999)

        self.assertEqual(Customer.objects.count(), 0)

    def test_converted_lead_cannot_be_converted_twice(self):
        first_customer = CustomerService.convert_qualified_lead(
            self.lead.pk
        )

        with self.assertRaises(ValidationError):
            CustomerService.convert_qualified_lead(self.lead.pk)

        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(
            Customer.objects.get(pk=first_customer.pk).originating_lead_id,
            self.lead.pk,
        )


class CustomerCreationServiceTests(TestCase):
    def test_general_customer_creation_generates_number(self):
        customer = CustomerService.create(
            name="  Example Organization  ",
            email="contact@example.com",
        )

        self.assertEqual(customer.customer_number, "DMX-CUS-000001")
        self.assertEqual(customer.name, "Example Organization")
        self.assertEqual(customer.email, "contact@example.com")
        self.assertEqual(
            customer.customer_type,
            Customer.CustomerType.ORGANIZATION,
        )
        self.assertEqual(customer.status, Customer.Status.ACTIVE)
        self.assertIsNone(customer.originating_lead)

    def test_general_customer_creation_supports_individuals(self):
        customer = CustomerService.create(
            customer_type=Customer.CustomerType.INDIVIDUAL,
            name="Jane Doe",
        )

        self.assertEqual(
            customer.customer_type,
            Customer.CustomerType.INDIVIDUAL,
        )
        self.assertEqual(customer.name, "Jane Doe")

    def test_general_customer_creation_rejects_blank_name(self):
        with self.assertRaises(ValidationError):
            CustomerService.create(name="   ")

        self.assertEqual(Customer.objects.count(), 0)

    def test_general_customer_creation_rejects_invalid_type(self):
        with self.assertRaises(ValidationError):
            CustomerService.create(
                customer_type="INVALID",
                name="Example Organization",
            )

        self.assertEqual(Customer.objects.count(), 0)


class CustomerAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse("customer-list")

        self.staff_user = User.objects.create_user(
            username="customer_staff",
            password="test-password-123",
            is_staff=True,
        )

        self.ordinary_user = User.objects.create_user(
            username="ordinary_customer_user",
            password="test-password-123",
            is_staff=False,
        )

        self.customer = Customer.objects.create(
            customer_number="DMX-CUS-000010",
            customer_type=Customer.CustomerType.ORGANIZATION,
            name="Existing Organization",
            email="existing@example.com",
            phone="+211900000000",
        )

    def test_anonymous_user_cannot_list_customers(self):
        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_ordinary_user_cannot_list_customers(self):
        self.client.force_authenticate(user=self.ordinary_user)

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_user_can_list_customers(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["customer_number"],
            "DMX-CUS-000010",
        )

    def test_staff_user_can_retrieve_customer(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(
            reverse(
                "customer-detail",
                kwargs={"pk": self.customer.pk},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["name"],
            "Existing Organization",
        )

    def test_staff_user_can_create_customer(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            self.list_url,
            {
                "customer_type": "ORGANIZATION",
                "name": "New Organization",
                "email": "new@example.com",
                "phone": "+211911111111",
                "country": "South Sudan",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(response.data["customer_number"], "DMX-CUS-000011")

        customer = Customer.objects.get(
            customer_number="DMX-CUS-000011"
        )
        self.assertEqual(customer.name, "New Organization")
        self.assertEqual(customer.email, "new@example.com")

    def test_client_cannot_choose_customer_number_or_status(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            self.list_url,
            {
                "customer_number": "CLIENT-CHOSEN-001",
                "customer_type": "ORGANIZATION",
                "name": "Protected Fields Organization",
                "status": "SUSPENDED",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(response.data["customer_number"], "DMX-CUS-000011")
        self.assertEqual(response.data["status"], Customer.Status.ACTIVE)

    def test_blank_customer_name_is_rejected(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            self.list_url,
            {
                "customer_type": "ORGANIZATION",
                "name": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Customer.objects.count(), 1)

    def test_staff_user_can_update_customer_profile(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.patch(
            reverse(
                "customer-detail",
                kwargs={"pk": self.customer.pk},
            ),
            {
                "name": "Updated Organization",
                "email": "updated@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, "Updated Organization")
        self.assertEqual(self.customer.email, "updated@example.com")

    def test_customer_number_status_and_lead_are_read_only(self):
        lead = Lead.objects.create(
            full_name="Lead Contact",
            email="lead@example.com",
            phone="+211922222222",
            organization="Lead Organization",
            subject="ERP",
            message="Interested in the ERP.",
            status=Lead.Status.QUALIFIED,
        )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.patch(
            reverse(
                "customer-detail",
                kwargs={"pk": self.customer.pk},
            ),
            {
                "customer_number": "CHANGED-001",
                "status": "SUSPENDED",
                "originating_lead": lead.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.customer.refresh_from_db()
        self.assertEqual(
            self.customer.customer_number,
            "DMX-CUS-000010",
        )
        self.assertEqual(self.customer.status, Customer.Status.ACTIVE)
        self.assertIsNone(self.customer.originating_lead)

        self.assertFalse(
            Customer.objects.filter(originating_lead=lead).exists()
        )

    def test_customer_deletion_is_not_supported(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.delete(
            reverse(
                "customer-detail",
                kwargs={"pk": self.customer.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertTrue(
            Customer.objects.filter(pk=self.customer.pk).exists()
        )

    def test_ordinary_user_cannot_create_customer(self):
        self.client.force_authenticate(user=self.ordinary_user)

        response = self.client.post(
            self.list_url,
            {
                "customer_type": "ORGANIZATION",
                "name": "Unauthorized Organization",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(Customer.objects.count(), 1)