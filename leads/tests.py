from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from products.models import Product, ProductCategory
from services.models import Service
from .models import Lead


class LeadCreateAPITests(TestCase):
    """
    Automated tests for the public Lead submission API.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/leads/"

        self.category = ProductCategory.objects.create(
            name="Test Category",
            slug="test-category",
            is_active=True,
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            slug="test-product",
            short_description="A product for testing.",
            description="Test product description.",
            status="ACTIVE",
        )

        self.service = Service.objects.create(
            name="Test Service",
            slug="test-service",
            short_description="A service for testing.",
            description="Test service description.",
            is_active=True,
        )

        self.valid_payload = {
            "full_name": "Test API Customer",
            "email": "customer@example.com",
            "phone": "+211900000000",
            "organization": "Test Organization",
            "product": self.product.id,
            "subject": "Product Inquiry",
            "message": "I would like more information.",
            "source": "PRODUCT_PAGE",
        }

    def test_valid_submission_creates_lead(self):
        response = self.client.post(
            self.url,
            self.valid_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(
            Lead.objects.get().status,
            Lead.Status.NEW,
        )
        self.assertEqual(
            Lead.objects.get().priority,
            Lead.Priority.MEDIUM,
        )

    def test_invalid_email_is_rejected(self):
        payload = self.valid_payload.copy()
        payload["email"] = "not-an-email"

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Lead.objects.count(), 0)

    def test_inactive_service_is_rejected(self):
        inactive_service = Service.objects.create(
            name="Inactive Test Service",
            slug="inactive-test-service",
            short_description="An inactive service.",
            description="This service is unavailable.",
            is_active=False,
        )

        payload = self.valid_payload.copy()
        payload.pop("product")
        payload["service"] = inactive_service.id

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Lead.objects.count(), 0)

    def test_both_product_and_service_are_rejected(self):
        payload = self.valid_payload.copy()
        payload["service"] = self.service.id

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Lead.objects.count(), 0)

    def test_public_endpoint_does_not_allow_get(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_public_submission_cannot_set_internal_fields(self):
        """
        Public users must not submit internal lead-management
        fields such as status, priority, or notes.
        """
        payload = {
            **self.valid_payload,
            "status": "CONVERTED",
            "priority": "URGENT",
            "notes": "Attempt to modify internal fields.",
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(Lead.objects.count(), 0)

    def test_draft_product_is_rejected(self):
        draft_product = Product.objects.create(
            category=self.category,
            name="Draft Test Product",
            slug="draft-test-product",
            short_description="A draft product.",
            description="Not publicly available.",
            status="DRAFT",
        )

        payload = self.valid_payload.copy()
        payload["product"] = draft_product.id

        response = self.client.post(
            self.url, payload, format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Lead.objects.count(), 0)

    def test_archived_product_is_rejected(self):
        archived_product = Product.objects.create(
            category=self.category,
            name="Archived Test Product",
            slug="archived-test-product",
            short_description="An archived product.",
            description="No longer publicly available.",
            status="ARCHIVED",
        )

        payload = self.valid_payload.copy()
        payload["product"] = archived_product.id

        response = self.client.post(
            self.url, payload, format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Lead.objects.count(), 0)

    def test_coming_soon_product_is_accepted(self):
        coming_soon_product = Product.objects.create(
            category=self.category,
            name="Coming Soon Test Product",
            slug="coming-soon-test-product",
            short_description="An upcoming product.",
            description="Not launched yet.",
            status="COMING_SOON",
        )

        payload = self.valid_payload.copy()
        payload["product"] = coming_soon_product.id

        response = self.client.post(
            self.url, payload, format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(Lead.objects.count(), 1)

    def test_unexpected_field_is_rejected(self):
        """
        Public submissions must reject fields that are not
        explicitly supported by the API.
        """
        payload = {
            **self.valid_payload,
            "unexpected_field": "not allowed",
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(Lead.objects.count(), 0)