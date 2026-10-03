from django.core.exceptions import ValidationError
from django.db import transaction

from customers.models import Customer
from customers.services.customer_number_service import CustomerNumberService
from leads.models import Lead


class CustomerService:
    """
    Handles customer creation and qualified-lead conversion
    for DMX Digital Solutions.
    """

    @classmethod
    @transaction.atomic
    def convert_qualified_lead(cls, lead_id):
        """
        Convert a qualified lead into a customer.

        Customer creation and the lead status update are atomic:
        if either operation fails, the transaction is rolled back.
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

        customer_name = (
            lead.organization.strip()
            if lead.organization and lead.organization.strip()
            else lead.full_name.strip()
        )

        if not customer_name:
            raise ValidationError(
                "A customer name is required to convert this lead."
            )

        customer = Customer.objects.create(
            customer_number=CustomerNumberService.generate(),
            customer_type=Customer.CustomerType.ORGANIZATION
            if lead.organization.strip()
            else Customer.CustomerType.INDIVIDUAL,
            name=customer_name,
            email=lead.email,
            phone=lead.phone,
            originating_lead=lead,
        )

        lead.status = Lead.Status.CONVERTED
        lead.save(update_fields=["status", "updated_at"])

        return customer