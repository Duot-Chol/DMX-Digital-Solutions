from django.urls import path

from .views import LeadCreateAPIView


urlpatterns = [
    path("", LeadCreateAPIView.as_view(), name="lead-create"),
]