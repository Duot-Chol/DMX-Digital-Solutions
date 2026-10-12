"""
============================================================
DMX Digital Solutions
Payments - URL Configuration
============================================================
"""

from django.urls import path

from payments.views import (
    PaymentDetailAPIView,
    PaymentListCreateAPIView,
)

app_name = "payments"

urlpatterns = [
    path(
        "",
        PaymentListCreateAPIView.as_view(),
        name="payment-list-create",
    ),
    path(
        "<uuid:pk>/",
        PaymentDetailAPIView.as_view(),
        name="payment-detail",
    ),
]