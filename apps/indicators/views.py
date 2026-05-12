from __future__ import annotations

import logging
from typing import Any

from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from .constants import VALID_YEARS
from .models import ISOIndicator, ISOIndicatorData
from .permissions import IsManagerOrReadOnly
from .serializers import (
    ISOIndicatorDataSerializer,
    ISOIndicatorSerializer,
    ISOIndicatorWriteSerializer,
)
from .services import AttachmentValidationError, ISOIndicatorService

logger = logging.getLogger(__name__)


class ISOIndicatorViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para ISOIndicator com filtros e ações de anexo.

    list:   GET  /api/indicators/
    create: POST /api/indicators/
    retrieve: GET  /api/indicators/{id}/
    update: PUT  /api/indicators/{id}/
    partial_update: PATCH /api/indicators/{id}/
    destroy: DELETE /api/indicators/{id}/
    upload_attachment: POST /api/indicators/{id}/data/{year}/attachment/
    delete_attachment: DELETE /api/indicators/{id}/data/{year}/attachment/
    """

    permission_classes = [IsManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["standard", "cidade", "estado", "tipo", "categoria"]
    search_fields = ["nome_indicador", "categoria"]
    ordering_fields = ["categoria", "nome_indicador", "standard", "created_at"]
    ordering = ["categoria", "nome_indicador"]

    def get_queryset(self) -> models.QuerySet[ISOIndicator]:
        return ISOIndicator.objects.with_data().select_related()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ISOIndicatorWriteSerializer
        return ISOIndicatorSerializer

    def perform_create(self, serializer) -> None:
        indicator = serializer.save()
        logger.info("Indicador criado: id=%s por user=%s", indicator.id, self.request.user.id)

    def perform_update(self, serializer) -> None:
        indicator = serializer.save()
        logger.info("Indicador atualizado: id=%s por user=%s", indicator.id, self.request.user.id)

    def perform_destroy(self, instance: ISOIndicator) -> None:
        logger.info("Indicador removido: id=%s por user=%s", instance.id, self.request.user.id)
        instance.delete()

    # ------------------------------------------------------------------
    # Ações de dado anual
    # ------------------------------------------------------------------

    @action(
        detail=True,
        methods=["post"],
        url_path=r"data/(?P<year>\d{4})/attachment",
        parser_classes=[MultiPartParser],
        permission_classes=[IsManagerOrReadOnly],
    )
    def upload_attachment(self, request: Request, pk: Any, year: str) -> Response:
        year_int = int(year)
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "Nenhum arquivo enviado."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            url = ISOIndicatorService.upload_attachment(int(pk), year_int, file)
        except AttachmentValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ISOIndicator.DoesNotExist:
            return Response({"detail": "Indicador não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"url": url}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"data/(?P<year>\d{4})/attachment",
        permission_classes=[IsManagerOrReadOnly],
    )
    def delete_attachment(self, request: Request, pk: Any, year: str) -> Response:
        year_int = int(year)
        if year_int not in VALID_YEARS:
            return Response({"detail": f"Ano inválido: {year}."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ISOIndicatorService.delete_attachment(int(pk), year_int)
        except AttachmentValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except (ISOIndicator.DoesNotExist, ISOIndicatorData.DoesNotExist):
            return Response({"detail": "Recurso não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except FileNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="data")
    def list_data(self, request: Request, pk: Any) -> Response:
        indicator = self.get_object()
        data = ISOIndicatorData.objects.filter(indicator=indicator).order_by("year")
        serializer = ISOIndicatorDataSerializer(data, many=True)
        return Response(serializer.data)
