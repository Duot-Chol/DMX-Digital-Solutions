"""
Product models for the DMX Digital Solutions Commercial Platform.

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from django.db import models


class ProductCategory(models.Model):
    """
    Category used to organize DMX Digital Solutions products.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    display_order = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    A commercial software product offered by DMX Digital Solutions.

    The model is intentionally product-agnostic so that SmartSchool ERP,
    E-Voting Management System, and future DMX products can all use it.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        COMING_SOON = "COMING_SOON", "Coming Soon"
        ARCHIVED = "ARCHIVED", "Archived"

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )

    name = models.CharField(
        max_length=150,
        unique=True,
    )

    slug = models.SlugField(
        max_length=180,
        unique=True,
    )

    short_description = models.CharField(
        max_length=300,
    )

    description = models.TextField()

    logo = models.ImageField(
        upload_to="products/logos/",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    is_featured = models.BooleanField(
        default=False,
    )

    display_order = models.PositiveIntegerField(
        default=0,
    )

    # Public product links
    product_url = models.URLField(
        blank=True,
        help_text="Public URL for the actual product, if available.",
    )

    demo_url = models.URLField(
        blank=True,
        help_text="Live demonstration URL, if available.",
    )

    documentation_url = models.URLField(
        blank=True,
        help_text="Public documentation URL, if available.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class ProductFeature(models.Model):
    """
    A feature belonging to a commercial DMX product.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="features",
    )

    name = models.CharField(
        max_length=150,
    )

    description = models.TextField(
        blank=True,
    )

    display_order = models.PositiveIntegerField(
        default=0,
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
        verbose_name = "Product Feature"
        verbose_name_plural = "Product Features"
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.product.name} - {self.name}"