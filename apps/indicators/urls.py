from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import ISOIndicatorViewSet

router = DefaultRouter()
router.register(r"indicators", ISOIndicatorViewSet, basename="indicator")

urlpatterns = router.urls
