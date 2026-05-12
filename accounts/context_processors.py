from __future__ import annotations

from typing import Any

from django.http import HttpRequest


def user_context(request: HttpRequest) -> dict[str, Any]:
    """Injeta dados do usuário autenticado em todos os templates."""
    if not request.user.is_authenticated:
        return {}
    return {
        "current_user": request.user,
        "user_type": request.user.user_type,
        "user_type_display": request.user.get_user_type_display(),
    }
