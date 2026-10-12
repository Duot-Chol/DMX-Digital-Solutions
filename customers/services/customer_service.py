from django.core.exceptions import ValidationError
from django.db import transaction

from customers.models import Customer
from customers.services.customer_number_service import (
    CustomerNumberService,
)
from leads.models import Lead


class CustomerService:
    """
    Handles customer creation and qualified-lead conversion
    for DMX Digital Solutions.
    """

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        customer_type=Customer.CustomerType.ORGANIZATION,
        name,
        email="",
        phone="",
        address="",
        country="",
        website="",
        notes="",
    ):
        """
        Create a customer and automatically assign a customer number.

        General customer creation does not require an originating lead.
        """
        normalized_name = name.strip() if name else ""

        if not normalized_name:
            raise ValidationError("A customer name is required.")

        if customer_type not in Customer.CustomerType.values:
            raise ValidationError("The specified customer type is invalid.")

        return Customer.objects.create(
            customer_number=CustomerNumberService.generate(),
            customer_type=customer_type,
            name=normalized_name,
            email=email,
            phone=phone,
            address=address,
            country=country,
            website=website,
            notes=notes,
        )

    @classmethod
    @transaction.atomic
    def convert_qualified_lead(cls, lead_id):
        """
        Convert a qualified lead into a customer.

        The originating lead is linked to the new customer, and the
        lead status changes to CONVERTED within the same transaction.
        """
        try:
            lead = Lead.objects.select_for_update().get(pk=lead_id)
        except Lead.DoesNotExist:
            raise ValidationError("The specified lead does not exist.")

        if lead.status != Lead.Status.QUALIFIED:
            raise ValidationError(
                "Only qualified leads can be converted into customers."
            )

        if Customer.objects.filter(originating_lead=lead).exists():
            raise ValidationError(
                "This lead has already been converted into a customer."
            )

        organization = (
            lead.organization.strip() if lead.organization else ""
        )

        customer_name = (
            organization if organization else lead.full_name.strip()
        )

        if not customer_name:
            raise ValidationError(
                "A customer name is required to convert this lead."
            )

        customer = Customer.objects.create(
            customer_number=CustomerNumberService.generate(),
            customer_type=(
                Customer.CustomerType.ORGANIZATION
                if organization
                else Customer.CustomerType.INDIVIDUAL
            ),
            name=customer_name,
            email=lead.email,
            phone=lead.phone,
            originating_lead=lead,
        )

        lead.status = Lead.Status.CONVERTED
        lead.save(update_fields=["status", "updated_at"])

        return customer