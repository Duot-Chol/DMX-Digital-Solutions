from django.core.exceptions import ValidationError
from django.test import TestCase

from customers.models import Customer, CustomerNumberCounter
from customers.services.customer_number_service import CustomerNumberService
from customers.services.customer_service import CustomerService
from leads.models import Lead


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