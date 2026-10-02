from rest_framework import generics
from rest_framework.permissions import AllowAny

from .serializers import LeadCreateSerializer


class LeadCreateAPIView(generics.CreateAPIView):
    """
    Public endpoint for submitting commercial inquiries.

    Visitors can create a lead, but they cannot retrieve,
    modify, or delete existing leads through this endpoint.
    """

    serializer_class = LeadCreateSerializer
    permission_classes = [AllowAny]