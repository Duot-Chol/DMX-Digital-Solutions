"""
============================================================
DMX Digital Solutions
Payments - API Views
============================================================

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from payments.models import Payment
from payments.serializers import PaymentSerializer


class PaymentListCreateAPIView(generics.ListCreateAPIView):
    """
    Staff-only endpoint for listing and creating payments.

    New payments are created with PENDING status through
    PaymentService, which is called by PaymentSerializer.
    """

    serializer_class = PaymentSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return (
            Payment.objects
            .select_related("customer", "subscription")
            .order_by("-created_at")
        )


class PaymentDetailAPIView(generics.RetrieveAPIView):
    """
    Staff-only endpoint for retrieving an individual payment.

    Payment modification and deletion are not exposed.
    """

    serializer_class = PaymentSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "pk"

    def get_queryset(self):
        return Payment.objects.select_related(
            "customer",
            "subscription",
        )