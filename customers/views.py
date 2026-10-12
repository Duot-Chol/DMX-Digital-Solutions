from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser

from customers.models import Customer
from customers.serializers import CustomerSerializer


class CustomerViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Staff-only API for managing DMX Digital Solutions customers.

    Supported operations:
    - List customers
    - Retrieve a customer
    - Create a customer
    - Update a customer profile

    Customer deletion is intentionally not supported.
    """

    queryset = Customer.objects.all().order_by(
        "name",
        "customer_number",
    )
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]
