from __future__ import annotations

import logging

from rest_framework import filters, viewsets

from .models import Norm
from .permissions import IsManagerOrReadOnly
from .serializers import NormSerializer

logger = logging.getLogger(__name__)


class NormViewSet(viewsets.ModelViewSet):
    queryset = Norm.objects.all()
    serializer_class = NormSerializer
    permission_classes = [IsManagerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "url"]
    ordering_fields = ["nome"]
    ordering = ["nome"]
