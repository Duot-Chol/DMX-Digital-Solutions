"""
==========================================================
DMX Digital Solutions
Demo Requests - URL Configuration
==========================================================
"""

from django.urls import path

from .views import DemoRequestCreateAPIView


urlpatterns = [
    path("", DemoRequestCreateAPIView.as_view(), name="demo-request-create"),
]