from __future__ import annotations

import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.staticfiles import finders
from django.http import FileResponse, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .decorators import admin_required, manager_required
from .forms import LoginForm, RegisterForm
from .models import (
    ISO37120Indicator,
    ISO37122Indicator,
    ISO37123Indicator,
    ISO37125Indicator,
    Norm,
    Platform,
    User,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_YEARS: frozenset[str] = frozenset({"2022", "2023", "2024", "2025"})

ALLOWED_UPDATE_FIELDS: frozenset[str] = frozenset(
    {
        "dado_2022", "dado_2023", "dado_2024", "dado_2025",
        "fonte_2022", "fonte_2023", "fonte_2024", "fonte_2025",
    }
)

MAX_ATTACHMENT_SIZE: int = 10 * 1024 * 1024  # 10 MB

# ISO model lookup — evita if/elif repetitivo nas views genéricas
_ISO_MODEL_MAP: dict[str, type] = {
    "iso37120": ISO37120Indicator,
    "iso37122": ISO37122Indicator,
    "iso37123": ISO37123Indicator,
    "iso37125": ISO37125Indicator,
}

# Mapeamento de tipo de usuário para exibição
USER_TYPE_LABELS: dict[str, str] = {
    "ADMIN": "Administrador",
    "MANAGER": "Gestor",
    "COMMON": "Usuário Comum",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_url(url: str) -> str:
    """Garante que uma URL tenha protocolo HTTPS."""
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _get_iso_model(standard_slug: str) -> type | None:
    return _ISO_MODEL_MAP.get(standard_slug)


def _validate_attachment(file: Any) -> str | None:
    """Retorna mensagem de erro se o arquivo for inválido, None se válido."""
    if not file.name.lower().endswith(".pdf"):
        return "Apenas arquivos PDF são permitidos."
    if file.size > MAX_ATTACHMENT_SIZE:
        return "Arquivo muito grande. Máximo permitido: 10 MB."
    return None


def _build_indicator_dict(indicator: Any) -> dict[str, Any]:
    """Serializa um indicador ISO para dict JSON-safe."""
    return {
        "id": indicator.id,
        "categoria": indicator.categoria,
        "nome_indicador": indicator.nome_indicador,
        "tipo": indicator.tipo,
        "ods": indicator.ods,
        "unidade": indicator.unidade,
        "dado_2022": indicator.dado_2022,
        "dado_2023": indicator.dado_2023,
        "dado_2024": indicator.dado_2024,
        "dado_2025": indicator.dado_2025,
        "fonte_2022": indicator.fonte_2022,
        "fonte_2023": indicator.fonte_2023,
        "fonte_2024": indicator.fonte_2024,
        "fonte_2025": indicator.fonte_2025,
        "anexo_2022": indicator.anexo_2022.url if indicator.anexo_2022 else None,
        "anexo_2023": indicator.anexo_2023.url if indicator.anexo_2023 else None,
        "anexo_2024": indicator.anexo_2024.url if indicator.anexo_2024 else None,
        "anexo_2025": indicator.anexo_2025.url if indicator.anexo_2025 else None,
        "cidade": indicator.cidade,
        "estado": indicator.estado,
        "created_at": indicator.created_at.isoformat() if indicator.created_at else None,
        "updated_at": indicator.updated_at.isoformat() if indicator.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def register(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cadastro realizado com sucesso!")
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


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
                return redirect("menu")
            messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["POST"])
def logout(request: HttpRequest) -> HttpResponse:
    auth_logout(request)
    messages.success(request, "Logout realizado com sucesso!")
    return redirect("login")


# ---------------------------------------------------------------------------
# Páginas públicas
# ---------------------------------------------------------------------------

def landing(request: HttpRequest) -> HttpResponse:
    return render(request, "landing.html")


def saiba_mais(request: HttpRequest) -> HttpResponse:
    return render(request, "saiba_mais.html")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@require_http_methods(["GET"])
def menu(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "new-screens/menu.html")


@require_http_methods(["GET"])
def dimensoes(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "screens/dimensoes.html")


@require_http_methods(["GET"])
def indicadores(request: HttpRequest, dimensao_id: str | None = None) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("login")
    if dimensao_id:
        request.session["dimensao_id"] = dimensao_id
    return render(request, "screens/indicadores.html")


@require_http_methods(["GET"])
def normas(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("login")
    norms = Norm.objects.all()
    return render(request, "accounts/normas.html", {"norms": norms})


@require_http_methods(["GET"])
def plataformas(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("login")
    platforms = Platform.objects.all()
    return render(request, "accounts/plataformas.html", {"platforms": platforms})


@require_http_methods(["GET"])
def csc(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "accounts/plataformas/csc.html")


@require_http_methods(["GET"])
def inteligente(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "accounts/plataformas/inteligente.html")


# ---------------------------------------------------------------------------
# Normas ISO — páginas
# ---------------------------------------------------------------------------

@require_http_methods(["GET"])
def iso37120(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "accounts/normas/iso37120.html")


@require_http_methods(["GET"])
def iso37122(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "accounts/normas/iso37122.html")


@require_http_methods(["GET"])
def iso37123(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "accounts/normas/iso37123.html")


@require_http_methods(["GET"])
def iso37125(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "accounts/normas/iso37125.html")


# ---------------------------------------------------------------------------
# API genérica para indicadores ISO (elimina 20 funções duplicadas)
# ---------------------------------------------------------------------------

@require_http_methods(["GET"])
def get_iso_data(request: HttpRequest, standard_slug: str) -> JsonResponse:
    """Retorna todos os indicadores de um padrão ISO para uma cidade/estado."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Não autorizado"}, status=401)

    model = _get_iso_model(standard_slug)
    if model is None:
        return JsonResponse({"error": "Padrão ISO inválido"}, status=404)

    cidade = request.GET.get("cidade", "Londrina")
    estado = request.GET.get("estado", "PR")

    try:
        indicators = model.objects.filter(cidade=cidade, estado=estado)
        return JsonResponse({"success": True, "data": [_build_indicator_dict(i) for i in indicators]})
    except Exception:
        logger.exception("Erro ao buscar dados %s", standard_slug)
        return JsonResponse({"success": False, "message": "Erro interno ao buscar dados."}, status=500)


@require_http_methods(["POST"])
@manager_required
def save_iso_data(request: HttpRequest, standard_slug: str) -> JsonResponse:
    """Cria ou atualiza um indicador ISO."""
    model = _get_iso_model(standard_slug)
    if model is None:
        return JsonResponse({"error": "Padrão ISO inválido"}, status=404)

    try:
        data: dict[str, Any] = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "JSON inválido."}, status=400)

    nome_indicador = data.get("nome_indicador")
    if not nome_indicador:
        return JsonResponse({"success": False, "message": "nome_indicador é obrigatório."}, status=400)

    cidade = data.get("cidade", "Londrina")
    estado = data.get("estado", "PR")

    year_fields = {
        f"dado_{y}": data.get(f"dado_{y}")
        for y in ("2022", "2023", "2024", "2025")
        if data.get(f"dado_{y}") is not None
    }
    source_fields = {
        f"fonte_{y}": data.get(f"fonte_{y}")
        for y in ("2022", "2023", "2024", "2025")
        if data.get(f"fonte_{y}") is not None
    }

    defaults = {
        "categoria": data.get("categoria", ""),
        "tipo": data.get("tipo", "core"),
        "ods": data.get("ods", ""),
        "unidade": data.get("unidade", ""),
        **year_fields,
        **source_fields,
    }

    try:
        indicator, created = model.objects.get_or_create(
            nome_indicador=nome_indicador,
            cidade=cidade,
            estado=estado,
            defaults=defaults,
        )
        if not created:
            for field, value in defaults.items():
                setattr(indicator, field, value)
            indicator.save()

        return JsonResponse({"success": True, "message": "Dados salvos com sucesso.", "id": indicator.id})
    except Exception:
        logger.exception("Erro ao salvar indicador %s", standard_slug)
        return JsonResponse({"success": False, "message": "Erro interno ao salvar dados."}, status=500)


@require_http_methods(["POST"])
@manager_required
def update_iso_field(request: HttpRequest, standard_slug: str) -> JsonResponse:
    """Atualiza um campo específico de um indicador ISO."""
    model = _get_iso_model(standard_slug)
    if model is None:
        return JsonResponse({"error": "Padrão ISO inválido"}, status=404)

    try:
        data: dict[str, Any] = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "JSON inválido."}, status=400)

    field_name: str = data.get("field_name", "")
    if field_name not in ALLOWED_UPDATE_FIELDS:
        logger.warning("Tentativa de atualizar campo não permitido: %s", field_name)
        return JsonResponse({"success": False, "message": "Campo não permitido."}, status=400)

    indicator = get_object_or_404(model, id=data.get("indicator_id"))

    try:
        setattr(indicator, field_name, data.get("field_value"))
        indicator.save(update_fields=[field_name, "updated_at"])
        return JsonResponse({"success": True, "message": "Campo atualizado com sucesso."})
    except Exception:
        logger.exception("Erro ao atualizar campo %s em %s", field_name, standard_slug)
        return JsonResponse({"success": False, "message": "Erro interno ao atualizar campo."}, status=500)


@require_http_methods(["POST"])
@manager_required
def upload_iso_anexo(request: HttpRequest, standard_slug: str) -> JsonResponse:
    """Faz upload de um anexo PDF para um indicador ISO."""
    model = _get_iso_model(standard_slug)
    if model is None:
        return JsonResponse({"error": "Padrão ISO inválido"}, status=404)

    nome_indicador = request.POST.get("nome_indicador") or request.POST.get("indicator_id")
    year = request.POST.get("year", "")
    anexo_file = request.FILES.get("anexo")

    if not nome_indicador or not year or not anexo_file:
        return JsonResponse({"success": False, "message": "Parâmetros obrigatórios ausentes."}, status=400)

    if year not in VALID_YEARS:
        return JsonResponse({"success": False, "message": "Ano inválido."}, status=400)

    error = _validate_attachment(anexo_file)
    if error:
        return JsonResponse({"success": False, "message": error}, status=400)

    cidade = request.POST.get("cidade", "Londrina")
    estado = request.POST.get("estado", "PR")

    try:
        indicator, _ = model.objects.get_or_create(
            nome_indicador=nome_indicador,
            cidade=cidade,
            estado=estado,
            defaults={
                "categoria": request.POST.get("categoria", ""),
                "tipo": request.POST.get("tipo", "core"),
                "ods": request.POST.get("ods", ""),
                "unidade": request.POST.get("unidade", ""),
            },
        )

        anexo_field = f"anexo_{year}"
        old_file = getattr(indicator, anexo_field)
        if old_file:
            old_file.delete(save=False)

        setattr(indicator, anexo_field, anexo_file)
        indicator.save(update_fields=[anexo_field, "updated_at"])

        url = getattr(indicator, anexo_field).url
        return JsonResponse({"success": True, "message": "Anexo enviado com sucesso.", "anexo_url": url})
    except Exception:
        logger.exception("Erro ao fazer upload de anexo em %s", standard_slug)
        return JsonResponse({"success": False, "message": "Erro interno ao enviar anexo."}, status=500)


@require_http_methods(["POST"])
@manager_required
def delete_iso_anexo(request: HttpRequest, standard_slug: str) -> JsonResponse:
    """Remove um anexo PDF de um indicador ISO."""
    model = _get_iso_model(standard_slug)
    if model is None:
        return JsonResponse({"error": "Padrão ISO inválido"}, status=404)

    try:
        data: dict[str, Any] = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "JSON inválido."}, status=400)

    nome_indicador = data.get("nome_indicador") or data.get("indicator_id")
    year = data.get("year", "")

    if not nome_indicador or not year:
        return JsonResponse({"success": False, "message": "Parâmetros obrigatórios ausentes."}, status=400)

    if str(year) not in VALID_YEARS:
        return JsonResponse({"success": False, "message": "Ano inválido."}, status=400)

    indicator = get_object_or_404(
        model,
        nome_indicador=nome_indicador,
        cidade=data.get("cidade", "Londrina"),
        estado=data.get("estado", "PR"),
    )

    anexo_field = f"anexo_{year}"
    old_file = getattr(indicator, anexo_field)

    if not old_file:
        return JsonResponse({"success": False, "message": "Nenhum anexo encontrado."}, status=404)

    try:
        old_file.delete(save=False)
        setattr(indicator, anexo_field, None)
        indicator.save(update_fields=[anexo_field, "updated_at"])
        return JsonResponse({"success": True, "message": "Anexo removido com sucesso."})
    except Exception:
        logger.exception("Erro ao remover anexo em %s", standard_slug)
        return JsonResponse({"success": False, "message": "Erro interno ao remover anexo."}, status=500)


# ---------------------------------------------------------------------------
# Plataformas — CRUD
# ---------------------------------------------------------------------------

@require_http_methods(["GET"])
@admin_required
def listar_plataformas(request: HttpRequest) -> JsonResponse:
    platforms = Platform.objects.values("id_plataforma", "Nome", "Direcionamento")
    return JsonResponse({
        "status": "success",
        "plataformas": [
            {"id": p["id_plataforma"], "name": p["Nome"], "link": p["Direcionamento"]}
            for p in platforms
        ],
    })


@require_http_methods(["POST"])
@admin_required
def adicionar_plataforma(request: HttpRequest) -> JsonResponse:
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        data = request.POST

    name = data.get("name", "").strip()
    link = data.get("link", "").strip()

    if not name or not link:
        return JsonResponse({"success": False, "message": "Nome e link são obrigatórios."}, status=400)

    link = normalize_url(link)

    try:
        Platform.objects.create(Nome=name, Direcionamento=link)
        return JsonResponse({"success": True, "message": "Plataforma adicionada com sucesso."})
    except Exception:
        logger.exception("Erro ao criar plataforma")
        return JsonResponse({"success": False, "message": "Erro ao criar plataforma."}, status=500)


@require_http_methods(["POST"])
@admin_required
def editar_plataforma(request: HttpRequest, platform_id: int) -> JsonResponse:
    platform = get_object_or_404(Platform, id_plataforma=platform_id)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        data = request.POST

    name = data.get("name", "").strip()
    link = data.get("link", "").strip()

    if not name or not link:
        return JsonResponse({"success": False, "message": "Nome e link são obrigatórios."}, status=400)

    platform.Nome = name
    platform.Direcionamento = normalize_url(link)
    platform.save()
    return JsonResponse({"success": True, "message": "Plataforma editada com sucesso."})


@require_http_methods(["DELETE"])
@admin_required
def remover_plataforma(request: HttpRequest, platform_id: int) -> JsonResponse:
    platform = get_object_or_404(Platform, id_plataforma=platform_id)
    platform.delete()
    return JsonResponse({"success": True, "message": "Plataforma removida com sucesso."})


# ---------------------------------------------------------------------------
# Normas — CRUD
# ---------------------------------------------------------------------------

@require_http_methods(["GET"])
def listar_normas(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Não autorizado"}, status=401)

    norms = list(Norm.objects.values("id_norma", "Nome", "Direcionamento"))
    return JsonResponse({"status": "success", "normas": norms})


@require_http_methods(["POST"])
@admin_required
def adicionar_norma(request: HttpRequest) -> JsonResponse:
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        data = request.POST

    name = data.get("name", "").strip()
    link = data.get("link", "").strip()

    if not name or not link:
        return JsonResponse({"success": False, "message": "Nome e link são obrigatórios."}, status=400)

    try:
        Norm.objects.create(Nome=name, Direcionamento=normalize_url(link))
        return JsonResponse({"success": True, "message": "Norma adicionada com sucesso."})
    except Exception:
        logger.exception("Erro ao criar norma")
        return JsonResponse({"success": False, "message": "Erro ao criar norma."}, status=500)


@require_http_methods(["POST"])
@admin_required
def editar_norma(request: HttpRequest, norm_id: int) -> JsonResponse:
    norm = get_object_or_404(Norm, id_norma=norm_id)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        data = request.POST

    name = data.get("name", "").strip()
    link = data.get("link", "").strip()

    if not name or not link:
        return JsonResponse({"success": False, "message": "Nome e link são obrigatórios."}, status=400)

    norm.Nome = name
    norm.Direcionamento = normalize_url(link)
    norm.save()
    return JsonResponse({"success": True, "message": "Norma editada com sucesso."})


@require_http_methods(["DELETE"])
@admin_required
def remover_norma(request: HttpRequest, norm_id: int) -> JsonResponse:
    norm = get_object_or_404(Norm, id_norma=norm_id)
    norm.delete()
    return JsonResponse({"success": True, "message": "Norma removida com sucesso."})


# ---------------------------------------------------------------------------
# Administração de Usuários
# ---------------------------------------------------------------------------

@require_http_methods(["GET"])
@admin_required
def admin_menu(request: HttpRequest) -> HttpResponse:
    return render(request, "accounts/admin/menu.html")


@require_http_methods(["GET"])
@admin_required
def list_users(request: HttpRequest) -> HttpResponse:
    users = User.objects.all().order_by("-created_at")
    return render(request, "accounts/admin/list_users.html", {"users": users})


@require_http_methods(["GET", "POST"])
@admin_required
def add_user(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        cpf = request.POST.get("cpf", "").strip()
        cidade = request.POST.get("cidade", "").strip()
        user_type = request.POST.get("categoria", "COMMON")

        if not all([nome, username, email, password, cpf, cidade, user_type]):
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect("add_user")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Já existe um usuário com este e-mail.")
            return redirect("add_user")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Já existe um usuário com este nome de usuário.")
            return redirect("add_user")

        try:
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                nome=nome,
                cpf=cpf,
                cidade=cidade,
                user_type=user_type,
            )
            messages.success(request, f"Usuário {username} criado com sucesso!")
            return redirect("list_users")
        except Exception:
            logger.exception("Erro ao criar usuário %s", username)
            messages.error(request, "Erro interno ao criar usuário.")
            return redirect("add_user")

    return render(request, "accounts/admin/add_user.html")


@require_http_methods(["GET", "POST"])
@admin_required
def edit_user(request: HttpRequest, user_id: int) -> HttpResponse:
    user_to_edit = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        cpf = request.POST.get("cpf", "").strip()
        cidade = request.POST.get("cidade", "").strip()
        user_type = request.POST.get("categoria", "COMMON")

        if not all([nome, username, email, cpf, cidade, user_type]):
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect("edit_user", user_id=user_id)

        if User.objects.filter(email=email).exclude(id=user_id).exists():
            messages.error(request, "Já existe um usuário com este e-mail.")
            return redirect("edit_user", user_id=user_id)

        if User.objects.filter(username=username).exclude(id=user_id).exists():
            messages.error(request, "Já existe um usuário com este nome de usuário.")
            return redirect("edit_user", user_id=user_id)

        user_to_edit.nome = nome
        user_to_edit.username = username
        user_to_edit.email = email
        user_to_edit.cpf = cpf
        user_to_edit.cidade = cidade
        user_to_edit.user_type = user_type

        if password:
            user_to_edit.set_password(password)

        user_to_edit.save()
        messages.success(request, f"Usuário {username} atualizado com sucesso!")
        return redirect("list_users")

    return render(request, "accounts/admin/edit_user.html", {"user_to_edit": user_to_edit})


@require_http_methods(["POST"])
@admin_required
def delete_user(request: HttpRequest, user_id: int) -> JsonResponse:
    user_to_delete = get_object_or_404(User, id=user_id)

    if user_to_delete.id == request.user.id:
        return JsonResponse({"success": False, "message": "Você não pode excluir sua própria conta."}, status=400)

    username = user_to_delete.username
    user_to_delete.delete()
    return JsonResponse({"success": True, "message": f"Usuário {username} excluído com sucesso."})


@require_http_methods(["POST"])
@admin_required
def change_user_role(request: HttpRequest, user_id: int) -> JsonResponse:
    user_to_change = get_object_or_404(User, id=user_id)

    if user_to_change.id == request.user.id:
        return JsonResponse({"success": False, "message": "Você não pode modificar seus próprios privilégios."}, status=400)

    new_role = request.POST.get("user_type", "")
    if new_role not in User.UserType.values:
        return JsonResponse({"success": False, "message": "Tipo de usuário inválido."}, status=400)

    user_to_change.user_type = new_role
    user_to_change.save(update_fields=["user_type"])

    label = USER_TYPE_LABELS.get(new_role, new_role)
    return JsonResponse({
        "success": True,
        "message": f"Privilégios de {user_to_change.username} alterados para {label}.",
    })


# ---------------------------------------------------------------------------
# Servir arquivos estáticos (apenas em desenvolvimento — usar Nginx em prod)
# ---------------------------------------------------------------------------

def serve_static(request: HttpRequest, path: str) -> HttpResponse:
    static_file = finders.find(path)
    if static_file:
        content_type, _ = mimetypes.guess_type(static_file)
        content_type = content_type or _guess_content_type(path)
        return FileResponse(open(static_file, "rb"), content_type=content_type)

    for base in (settings.BASE_DIR / "static", settings.BASE_DIR / "templates" / "static"):
        candidate = base / path
        if candidate.is_file():
            content_type, _ = mimetypes.guess_type(str(candidate))
            content_type = content_type or _guess_content_type(path)
            return FileResponse(open(candidate, "rb"), content_type=content_type)

    return HttpResponse(f"Arquivo {path} não encontrado.", status=404)


def _guess_content_type(path: str) -> str:
    if path.endswith(".css"):
        return "text/css"
    if path.endswith(".js"):
        return "application/javascript"
    return "application/octet-stream"


# ---------------------------------------------------------------------------
# Modais
# ---------------------------------------------------------------------------

def modal_dimensoes(request: HttpRequest) -> HttpResponse:
    return render(request, "screens/modals-dimensoes.html")


def modal_indicadores(request: HttpRequest) -> HttpResponse:
    return render(request, "screens/modals-indicadores.html")
