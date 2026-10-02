from django.db import models

from products.models import Product
from services.models import Service


class Lead(models.Model):
    """
    Represents a potential customer or commercial inquiry
    received by DMX Digital Solutions.
    """

    class Source(models.TextChoices):
        WEBSITE = "WEBSITE", "Website"
        PRODUCT_PAGE = "PRODUCT_PAGE", "Product Page"
        SERVICE_PAGE = "SERVICE_PAGE", "Service Page"
        LIVE_DEMO = "LIVE_DEMO", "Live Demo"
        REFERRAL = "REFERRAL", "Referral"
        SOCIAL_MEDIA = "SOCIAL_MEDIA", "Social Media"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        CONTACTED = "CONTACTED", "Contacted"
        QUALIFIED = "QUALIFIED", "Qualified"
        CONVERTED = "CONVERTED", "Converted"
        LOST = "LOST", "Lost"
        SPAM = "SPAM", "Spam"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    full_name = models.CharField(
        max_length=200,
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=50,
        blank=True,
    )

    organization = models.CharField(
        max_length=200,
        blank=True,
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )

    subject = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    source = models.CharField(
        max_length=30,
        choices=Source.choices,
        default=Source.WEBSITE,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.subject}"