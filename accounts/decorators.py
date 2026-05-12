from __future__ import annotations

from functools import wraps
from typing import Callable

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect


def admin_required(view_func: Callable) -> Callable:
    """Restringe acesso a usuários com user_type=ADMIN."""
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated or not request.user.is_admin():
            messages.error(request, "Você não tem permissão para acessar esta página.")
            return redirect("menu")
        return view_func(request, *args, **kwargs)
    return _wrapped


def manager_required(view_func: Callable) -> Callable:
    """Restringe acesso a ADMIN e MANAGER."""
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated or not (
            request.user.is_admin() or request.user.is_manager()
        ):
            messages.error(request, "Você não tem permissão para acessar esta página.")
            return redirect("menu")
        return view_func(request, *args, **kwargs)
    return _wrapped


def user_required(view_func: Callable) -> Callable:
    """Restringe acesso a qualquer usuário autenticado."""
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            messages.error(request, "Você precisa estar logado para acessar esta página.")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return _wrapped
