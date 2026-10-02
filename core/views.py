"""
API views for the Core application.

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SiteSettings
from .serializers import SiteSettingsSerializer


class SiteSettingsAPIView(APIView):
    """
    Public API endpoint for the active DMX Digital Solutions
    website configuration.

    GET:
        Returns the active site settings.

    POST:
        Creates the site settings if no active configuration exists.

    PUT:
        Updates the existing active site settings.

    PATCH:
        Partially updates the existing active site settings.
    """

    def get_active_settings(self):
        """
        Return the active SiteSettings instance, if one exists.
        """
        return SiteSettings.objects.filter(is_active=True).first()

    def get(self, request):
        """
        Return the active site configuration.
        """

        site_settings = self.get_active_settings()

        if not site_settings:
            return Response(
                {
                    "detail": "Site settings have not been configured yet."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SiteSettingsSerializer(site_settings)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        Create the initial site configuration.

        Only one active configuration is allowed.
        """

        existing_settings = self.get_active_settings()

        if existing_settings:
            return Response(
                {
                    "detail": (
                        "Active site settings already exist. "
                        "Use PUT or PATCH to update them."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SiteSettingsSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def put(self, request):
        """
        Replace the active site configuration.
        """

        site_settings = self.get_active_settings()

        if not site_settings:
            return Response(
                {
                    "detail": (
                        "Site settings do not exist yet. "
                        "Create them first."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SiteSettingsSerializer(
            site_settings,
            data=request.data,
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request):
        """
        Partially update the active site configuration.
        """

        site_settings = self.get_active_settings()

        if not site_settings:
            return Response(
                {
                    "detail": (
                        "Site settings do not exist yet. "
                        "Create them first."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SiteSettingsSerializer(
            site_settings,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )