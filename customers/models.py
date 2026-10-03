from django.db import models


class Customer(models.Model):
    """
    Represents an individual or organization that has an
    established commercial relationship with DMX Digital Solutions.
    """

    class CustomerType(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual"
        ORGANIZATION = "ORGANIZATION", "Organization"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"

    customer_number = models.CharField(
        max_length=30,
        unique=True,
        help_text="Unique customer reference assigned by DMX Digital Solutions.",
    )

    customer_type = models.CharField(
        max_length=20,
        choices=CustomerType.choices,
        default=CustomerType.ORGANIZATION,
    )

    name = models.CharField(max_length=200)

    email = models.EmailField(blank=True)

    phone = models.CharField(
        max_length=50,
        blank=True,
    )

    address = models.TextField(blank=True)

    country = models.CharField(
        max_length=100,
        blank=True,
    )

    website = models.URLField(blank=True)

    originating_lead = models.OneToOneField(
        "leads.Lead",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer",
        help_text="Optional lead from which this customer was converted.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    notes = models.TextField(
        blank=True,
        help_text="Internal notes for authorized staff.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ["name", "customer_number"]

    def __str__(self):
        return f"{self.customer_number} - {self.name}"


class CustomerNumberCounter(models.Model):
    """
    Stores the next customer number to allocate for a sequence.
    """

    name = models.CharField(
        max_length=50,
        unique=True,
    )

    next_number = models.PositiveBigIntegerField(default=1)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Number Counter"
        verbose_name_plural = "Customer Number Counters"

    def __str__(self):
        return f"{self.name}: next number {self.next_number}"