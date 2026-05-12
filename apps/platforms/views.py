from __future__ import annotations

import logging

from rest_framework import filters, viewsets

from .models import Platform
from .permissions import IsManagerOrReadOnly
from .serializers import PlatformSerializer

logger = logging.getLogger(__name__)


class PlatformViewSet(viewsets.ModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [IsManagerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "url"]
    ordering_fields = ["nome"]
    ordering = ["nome"]
