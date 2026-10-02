"""
URL configuration for the DMX Digital Solutions Commercial Platform.

Company:
    DMX Digital Solutions

Motto:
    Building Intelligent Digital Solutions
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    # Django Administration
    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/core/", include("core.urls")),
    path("api/v1/products/", include("products.urls")),
    path("api/v1/services/", include("services.urls")),
    path("api/v1/leads/", include("leads.urls")),
]


# Serve uploaded media files during development.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )