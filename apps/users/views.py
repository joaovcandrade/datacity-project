from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .permissions import IsAdminOrSelf
from .serializers import UserSerializer, UserWriteSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """
    Gerenciamento de usuários.

    Admin: acesso total.
    Usuário comum: apenas leitura/edição do próprio perfil.
    """

    permission_classes = [IsAdminOrSelf]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "nome", "cidade"]
    ordering_fields = ["email", "nome", "created_at"]
    ordering = ["email"]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return User.objects.all()
        return User.objects.filter(pk=user.pk)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return UserWriteSerializer
        return UserSerializer

    @action(detail=False, methods=["get"])
    def me(self, request: Request) -> Response:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request: Request, pk=None) -> Response:
        if not request.user.is_admin():
            return Response({"detail": "Apenas administradores podem desativar usuários."}, status=status.HTTP_403_FORBIDDEN)
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active"])
        logger.info("Usuário desativado: id=%s por admin=%s", user.id, request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
