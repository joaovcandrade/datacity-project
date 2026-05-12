from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import PlatformViewSet

router = DefaultRouter()
router.register(r"platforms", PlatformViewSet, basename="platform")

urlpatterns = router.urls
