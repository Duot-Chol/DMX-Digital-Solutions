from django.db import models


class Service(models.Model):
    """
    Represents a professional service offered by DMX Digital Solutions.
    """

    name = models.CharField(
        max_length=200,
        unique=True,
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
    )

    short_description = models.CharField(
        max_length=500,
    )

    description = models.TextField()

    icon = models.CharField(
        max_length=100,
        blank=True,
        help_text="Icon identifier used by the frontend.",
    )

    is_featured = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    display_order = models.PositiveIntegerField(
        default=0,
    )

    service_url = models.URLField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name