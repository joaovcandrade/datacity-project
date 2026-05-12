from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import NormViewSet

router = DefaultRouter()
router.register(r"norms", NormViewSet, basename="norm")

urlpatterns = router.urls
