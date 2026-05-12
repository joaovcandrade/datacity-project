from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, RegisterForm

logger = logging.getLogger(__name__)

USER_TYPE_LABELS: dict[str, str] = {
    "ADMIN": "Administrador",
    "MANAGER": "Gestor",
    "COMMON": "Usuário Comum",
}


@require_http_methods(["GET", "POST"])
def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("menu")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cadastro realizado com sucesso!")
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "authentication/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("menu")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                auth_login(request, user)
                tipo = USER_TYPE_LABELS.get(user.user_type, "Usuário")
                messages.success(request, f"Bem-vindo, {user.username}! (Nível: {tipo})")
                return redirect(request.GET.get("next", "menu"))
            messages.error(request, "E-mail ou senha inválidos.")
    else:
        form = LoginForm()

    return render(request, "authentication/login.html", {"form": form})


@require_http_methods(["POST"])
def logout(request: HttpRequest) -> HttpResponse:
    auth_logout(request)
    messages.success(request, "Logout realizado com sucesso!")
    return redirect("login")
