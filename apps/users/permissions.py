from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdminOrSelf(BasePermission):
    """Admin pode tudo. Usuário comum pode ler/editar apenas seu próprio perfil."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if request.user.is_admin():
            return True
        if request.method in SAFE_METHODS:
            return obj == request.user
        return obj == request.user
