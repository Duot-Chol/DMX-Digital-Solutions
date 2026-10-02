"""
Tests for the Core application.

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import SiteSettings


class SiteSettingsAPITests(TestCase):
    """
    Test the public, read-only Site Settings API.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/core/site/"

    def test_public_user_can_retrieve_active_settings(self):
        """
        Public visitors can retrieve active site settings.
        """
        settings = SiteSettings.objects.create(
            company_name="DMX Digital Solutions",
            motto="Building Intelligent Digital Solutions",
            is_active=True,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["company_name"],
            settings.company_name,
        )
        self.assertEqual(
            response.data["motto"],
            settings.motto,
        )

    def test_returns_404_when_no_active_settings_exist(self):
        """
        Return 404 if no active configuration exists.
        """
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_inactive_settings_are_not_returned(self):
        """
        Inactive settings must not be exposed as active settings.
        """
        SiteSettings.objects.create(
            company_name="Inactive Configuration",
            is_active=False,
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_post_cannot_create_settings_through_public_api(self):
        """
        Public visitors cannot create site settings.
        """
        response = self.client.post(
            self.url,
            {
                "company_name": "Unauthorized Company",
                "motto": "Unauthorized Motto",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(SiteSettings.objects.count(), 0)

    def test_put_cannot_replace_existing_settings(self):
        """
        Public visitors cannot replace existing settings.
        """
        settings = SiteSettings.objects.create(
            company_name="DMX Digital Solutions",
            motto="Building Intelligent Digital Solutions",
        )

        response = self.client.put(
            self.url,
            {
                "company_name": "Unauthorized Replacement",
                "motto": "Changed Motto",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

        settings.refresh_from_db()
        self.assertEqual(
            settings.company_name,
            "DMX Digital Solutions",
        )
        self.assertEqual(
            settings.motto,
            "Building Intelligent Digital Solutions",
        )

    def test_patch_cannot_modify_existing_settings(self):
        """
        Public visitors cannot partially update settings.
        """
        settings = SiteSettings.objects.create(
            company_name="DMX Digital Solutions",
        )

        response = self.client.patch(
            self.url,
            {"company_name": "Unauthorized Change"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

        settings.refresh_from_db()
        self.assertEqual(
            settings.company_name,
            "DMX Digital Solutions",
        )

    def test_delete_cannot_remove_existing_settings(self):
        """
        Public visitors cannot delete site settings.
        """
        settings = SiteSettings.objects.create(
            company_name="DMX Digital Solutions",
        )

        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertTrue(
            SiteSettings.objects.filter(pk=settings.pk).exists()
        )