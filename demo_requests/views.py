"""
==========================================================
DMX Digital Solutions
Demo Requests - API Views
==========================================================
"""

from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from .models import DemoRequest
from .serializers import DemoRequestSerializer


class DemoRequestCreateAPIView(CreateAPIView):
    """
    Public endpoint for submitting product demo requests.

    Only POST is supported by this view.
    """

    queryset = DemoRequest.objects.all()
    serializer_class = DemoRequestSerializer
    permission_classes = [AllowAny]
    http_method_names = ["post", "options"]
    id="s1a8cc"
