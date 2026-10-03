"""
==========================================================
DMX Digital Solutions
Demo Requests - API Tests
==========================================================
"""

from datetime import date, time

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Product
from .models import DemoRequest


class DemoRequestAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("demo-request-create")

        self.active_product = Product.objects.create(
            name="DMX SmartSchool ERP",
            slug="dmx-smartschool-erp",
            status=Product.Status.ACTIVE,
        )

        self.coming_soon_product = Product.objects.create(
            name="DMX Future Product",
            slug="dmx-future-product",
            status=Product.Status.COMING_SOON,
        )

        self.draft_product = Product.objects.create(
            name="Draft Product",
            slug="draft-product",
            status=Product.Status.DRAFT,
        )

        self.valid_payload = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+211912345678",
            "organization": "Example School",
            "product": self.active_product.pk,
            "preferred_date": "2026-10-15",
            "preferred_time": "10:30:00",
            "message": "We would like a product demonstration.",
        }

    def test_valid_demo_request_is_created(self):
        response = self.client.post(
            self.url, self.valid_payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DemoRequest.objects.count(), 1)

        demo_request = DemoRequest.objects.get()
        self.assertEqual(demo_request.full_name, "John Doe")
        self.assertEqual(demo_request.status, DemoRequest.Status.NEW)
        self.assertEqual(demo_request.product, self.active_product)
        self.assertEqual(demo_request.notes, "")

        self.assertNotIn("notes", response.data)
        self.assertNotIn("status", response.data)

    def test_request_without_product_is_allowed(self):
        payload = self.valid_payload.copy()
        payload.pop("product")

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(DemoRequest.objects.get().product)

    def test_invalid_email_is_rejected(self):
        payload = self.valid_payload.copy()
        payload["email"] = "not-an-email"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DemoRequest.objects.count(), 0)

    def test_coming_soon_product_is_allowed(self):
        payload = self.valid_payload.copy()
        payload["product"] = self.coming_soon_product.pk

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_draft_product_is_rejected(self):
        payload = self.valid_payload.copy()
        payload["product"] = self.draft_product.pk

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DemoRequest.objects.count(), 0)

    def test_internal_status_is_rejected(self):
        payload = self.valid_payload.copy()
        payload["status"] = DemoRequest.Status.CONVERTED

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DemoRequest.objects.count(), 0)

    def test_internal_notes_are_rejected(self):
        payload = self.valid_payload.copy()
        payload["notes"] = "Unauthorized internal note"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DemoRequest.objects.count(), 0)

    def test_unknown_fields_are_rejected(self):
        payload = self.valid_payload.copy()
        payload["unexpected_field"] = "unexpected value"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DemoRequest.objects.count(), 0)

    def test_get_is_not_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_is_not_allowed(self):
        response = self.client.put(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_is_not_allowed(self):
        response = self.client.patch(self.url, {"message": "Changed"})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_is_not_allowed(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    id="w3f0sp"
