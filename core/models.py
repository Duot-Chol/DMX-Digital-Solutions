"""
Core models for the DMX Digital Solutions Commercial Platform.

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from django.core.exceptions import ValidationError
from django.db import models


class SiteSettings(models.Model):
    """
    Global settings and company information for the DMX Digital Solutions
    commercial website.

    The platform is designed to use one active site configuration.
    """

    company_name = models.CharField(
        max_length=150,
        default="DMX Digital Solutions",
    )

    motto = models.CharField(
        max_length=255,
        default="Building Intelligent Digital Solutions",
    )

    description = models.TextField(
        blank=True,
        help_text="Short description of DMX Digital Solutions.",
    )

    logo = models.ImageField(
        upload_to="site/branding/",
        blank=True,
        null=True,
    )

    favicon = models.ImageField(
        upload_to="site/branding/",
        blank=True,
        null=True,
    )

    email = models.EmailField(
        blank=True,
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
    )

    address = models.CharField(
        max_length=255,
        blank=True,
    )

    website = models.URLField(
        blank=True,
    )

    # Social media / external company links
    facebook_url = models.URLField(
        blank=True,
    )

    instagram_url = models.URLField(
        blank=True,
    )

    linkedin_url = models.URLField(
        blank=True,
    )

    youtube_url = models.URLField(
        blank=True,
    )

    x_url = models.URLField(
        blank=True,
        verbose_name="X URL",
    )

    # Default SEO information
    seo_title = models.CharField(
        max_length=255,
        blank=True,
    )

    seo_description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.company_name

    def clean(self):
        """
        Ensure that only one active site configuration exists.
        """

        if self.is_active:
            existing_active = (
                SiteSettings.objects
                .filter(is_active=True)
                .exclude(pk=self.pk)
                .exists()
            )

            if existing_active:
                raise ValidationError(
                    "Only one active Site Settings configuration is allowed."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)