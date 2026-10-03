"""
==========================================================
DMX Digital Solutions
Demo Requests - Models

Motto:
    Building Intelligent Digital Solutions
==========================================================
"""

from django.db import models
from django.core.exceptions import ValidationError


class DemoRequest(models.Model):
    """
    Stores product demonstration requests submitted by
    prospective customers.
    """

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        CONTACTED = "CONTACTED", "Contacted"
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        CONVERTED = "CONVERTED", "Converted to Customer"
        SPAM = "SPAM", "Spam"

    # Requester's contact information
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    organization = models.CharField(max_length=200, blank=True)

    # Product being demonstrated
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demo_requests",
    )

    # Preferred demonstration schedule
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)

    # Additional information from the requester
    message = models.TextField(blank=True)

    # Internal management fields
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes for authorized staff. Not public.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Demo Request"
        verbose_name_plural = "Demo Requests"

    def clean(self):
        super().clean()

        # A request cannot select an unpublished product.
        if self.product_id:
            from products.models import Product

            if self.product.status not in {
                Product.Status.ACTIVE,
                Product.Status.COMING_SOON,
            }:
                raise ValidationError({
                    "product": (
                        "Demo requests can only be associated with "
                        "active or coming-soon products."
                    )
                })

    def __str__(self):
        return f"{self.full_name} - Demo Request"
