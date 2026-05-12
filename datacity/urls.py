from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", health_check),
    path("admin/", admin.site.urls),

    # Legacy app — mantida durante migração
    path("", include("accounts.urls")),
    path("api/scraping/", include("scraping.urls")),

    # New apps — REST API
    path("api/", include("apps.indicators.urls")),
    path("api/", include("apps.platforms.urls")),
    path("api/", include("apps.norms.urls")),
    path("api/", include("apps.users.urls")),

    # New apps — views
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
