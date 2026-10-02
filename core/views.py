"""
API views for the Core application.

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SiteSettings
from .serializers import SiteSettingsSerializer


class SiteSettingsAPIView(APIView):
    """
    Public, read-only API endpoint for active website settings.

    GET:
        Returns the active site settings.

    All write operations:
        Rejected. Site settings must be managed through
        the trusted Django Admin interface.
    """

    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        """
        Return the active site configuration.
        """
        site_settings = SiteSettings.objects.filter(
            is_active=True
        ).first()

        if not site_settings:
            return Response(
                {
                    "detail": (
                        "Site settings have not been configured yet."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SiteSettingsSerializer(site_settings)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )