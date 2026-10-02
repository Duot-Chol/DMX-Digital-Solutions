"""
URL configuration for the Core application.

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from django.urls import path

from .views import SiteSettingsAPIView


urlpatterns = [
    path(
        "site/",
        SiteSettingsAPIView.as_view(),
        name="site-settings",
    ),
]