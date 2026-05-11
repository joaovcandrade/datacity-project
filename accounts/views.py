from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .forms import RegisterForm, LoginForm
from .models import User, Platform, Municipality, Category, Indicator, IndicatorCategory, IndicatorValueYear, EvidencePDF, MunicipalityRanking, AuditLog, DesignacaoIndicador, DesignacaoPreenchimento
import json
import os
from django.db.models import Count, Q
from django.conf import settings
from django.utils import timezone
import mimetypes
from pathlib import Path
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from .decorators import admin_required, manager_required
import smtplib
from email.message import EmailMessage
import random
import string
from django.db import transaction

# Mock data for the application
MOCK_DATA = {
    'dimensoes': [
        {'id': 'mobilidade', 'nome': 'Mobilidade', 'cor': '#FF8C00', 'ods': '9, 11', 'iso': 'ISO 37120'},
        {'id': 'urbanismo', 'nome': 'Urbanismo', 'cor': '#8A2BE2', 'ods': '11', 'iso': 'ISO 37122'},
        {'id': 'educacao', 'nome': 'Educação', 'cor': '#4CAF50', 'ods': '4', 'iso': 'ISO 37120'},
        {'id': 'seguranca', 'nome': 'Segurança', 'cor': '#00CED1', 'ods': '16', 'iso': 'ISO 37120'},
        {'id': 'governanca', 'nome': 'Governança', 'cor': '#FF00FF', 'ods': '16, 17', 'iso': 'ISO 37122'},
        {'id': 'economia', 'nome': 'Economia', 'cor': '#32CD32', 'ods': '8, 9', 'iso': 'ISO 37120'},
        {'id': 'energia', 'nome': 'Energia', 'cor': '#FF0000', 'ods': '7', 'iso': 'ISO 37120'},
        {'id': 'meio-ambiente', 'nome': 'Meio Ambiente', 'cor': '#FFD700', 'ods': '13, 14, 15', 'iso': 'ISO 37120'},
        {'id': 'tecnologia', 'nome': 'Tecnologia e Inovação', 'cor': '#1E90FF', 'ods': '9', 'iso': 'ISO 37122'},
        {'id': 'empreendedorismo', 'nome': 'Empreendedorismo', 'cor': '#FF6347', 'ods': '8', 'iso': 'ISO 37122'},
        {'id': 'saude', 'nome': 'Saúde', 'cor': '#FF6B81', 'ods': '3', 'iso': 'ISO 37120'}
    ],
    'indicadores': {
        'economia': [
            {'id': 1, 'nome': 'PIB per capita', 'ods': '8', 'dado': 'R$ 45.000,00', 'fonte': 'IBGE', 'iso': 'ISO 37120'},
            {'id': 2, 'nome': 'Taxa de desemprego', 'ods': '8', 'dado': '7,5%', 'fonte': 'IBGE', 'iso': 'ISO 37120'},
            {'id': 3, 'nome': 'Crescimento anual', 'ods': '8', 'dado': '2,3%', 'fonte': 'Secretaria de Economia', 'iso': 'ISO 37122'}
        ],
        'educacao': [
            {'id': 1, 'nome': 'Taxa de alfabetização', 'ods': '4', 'dado': '97,2%', 'fonte': 'IBGE', 'iso': 'ISO 37120'},
            {'id': 2, 'nome': 'Escolas com acesso à internet', 'ods': '4, 9', 'dado': '89%', 'fonte': 'Secretaria de Educação', 'iso': 'ISO 37122'}
        ],
        'mobilidade': [
            {'id': 1, 'nome': 'Extensão de ciclovias', 'ods': '11', 'dado': '85 km', 'fonte': 'Secretaria de Mobilidade', 'iso': 'ISO 37120'}
        ]
    }
}

# Landing page view
def landing(request):
    context = {
        'user': request.user if request.user.is_authenticated else None,
        'is_authenticated': request.user.is_authenticated
    }
    return render(request, 'landing.html', context)

# Saiba Mais page view
def saiba_mais(request):
    return render(request, 'saiba_mais.html')




# Helper function to get the next ID for a new indicator
def get_next_indicator_id(dimensao_id):
    indicadores = MOCK_DATA['indicadores'].get(dimensao_id, [])
    if not indicadores:
        return 1
    return max(ind['id'] for ind in indicadores) + 1




# Authentication views
@require_http_methods(["GET", "POST"])
def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    if user.senha_temporaria_ativa:
                        request.session['temp_user_id'] = user.id
                        return redirect('first_access') 

                    auth_login(request, user)
                    tipo_usuario = {
                        'ADMIN': 'Administrador', 'MANAGER': 'Gestor', 'COMMON': 'Usuário'
                    }.get(user.user_type, 'Usuário')
                    
                    messages.success(request, f'Bem-vindo, {user.username}! ({tipo_usuario})')
                    return redirect('menu')
                else:
                    messages.error(request, 'Usuário ou senha inválidos')
            except User.DoesNotExist:
                messages.error(request, 'Usuário não encontrado')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(["GET", "POST"])
def reset_password(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email_usuario = request.POST.get('email')
        codigo_gerado = str(random.randint(1000000, 9999999))

        request.session['reset_username'] = username
        request.session['reset_code'] = codigo_gerado
        request.session['reset_email'] = email_usuario

        def _send_email_token(destinatario, codigo):
            email_user = os.getenv('EMAIL_HOST_USER')
            email_pass = os.getenv('EMAIL_HOST_PASSWORD')
            
            msg = EmailMessage()
            msg.set_content(f'Olá! Seu código de verificação DataCity é: {codigo}')
            msg['Subject'] = 'Código de Recuperação - DataCity'
            msg['From'] = email_user  # Usando a variável do ambiente
            msg['To'] = destinatario
 
            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(email_user, email_pass)
                    smtp.send_message(msg)
                return True
            except Exception as e:
                print(f"Erro ao enviar: {e}")
                return False

        if _send_email_token(email_usuario, codigo_gerado):
            messages.success(request, "Código enviado para o seu e-mail!")
            return redirect('verify_code') 
        else:
            messages.error(request, "Erro ao enviar e-mail. Tente novamente.")

    return render(request, 'accounts/reset-password.html')


@require_http_methods(["GET", "POST"])
def verify_and_change_password(request):
    username = request.session.get('reset_username')
    codigo_correto = request.session.get('reset_code')
    email_alvo = request.session.get('reset_email')

    if request.method == "POST":
        codigo_digitado = request.POST.get('codigo')
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if codigo_digitado != codigo_correto:
            messages.error(request, "Código de verificação incorreto!")
        elif nova_senha != confirmar_senha:
            messages.error(request, "As senhas não coincidem!")
        else:
            try:
                user = User.objects.get(email=email_alvo, username = username)
                user.set_password(nova_senha)
                user.save()

                del request.session['reset_code']
                del request.session['reset_email']
                
                messages.success(request, "Senha alterada com sucesso!")
                return redirect('login') # Redireciona para sua tela de login
            except User.DoesNotExist:
                messages.error(request, "Usuário não encontrado.")

    return render(request, 'accounts/verify-code.html')


@require_http_methods(["GET", "POST"])
def first_access(request):
    # Recupera o ID que salvamos no login
    user_id = request.session.get('temp_user_id')
    if not user_id:
        return redirect('login')

    if request.method == "POST":
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if nova_senha == confirmar_senha:
            user = User.objects.get(id=user_id)
            user.set_password(nova_senha)
            user.senha_temporaria_ativa = False
            user.save()

            # Loga automaticamente
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Limpa a sessão
            del request.session['temp_user_id']
            messages.success(request, "Senha alterada com sucesso!")
            return redirect('menu')
        else:
            messages.error(request, "As senhas não coincidem.")

    return render(request, 'accounts/first-access.html')


def logout(request):
    auth_logout(request)
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('login')

# Main page views
@login_required
def index(request):
    # Pass user information to the template
    context = {
        'username': request.user.username,
        'user_type': request.user.user_type,
        'dimensoes_count': len(MOCK_DATA['dimensoes']),
        'indicadores_count': sum(len(inds) for inds in MOCK_DATA['indicadores'].values())
    }
    return render(request, 'screens/index.html', context)

@login_required
def menu(request):
    # Pass user information to the template
    context = {
        'username': request.user.username,
        'user_type': request.user.user_type,
        'dimensoes_count': len(MOCK_DATA['dimensoes']),
        'indicadores_count': sum(len(inds) for inds in MOCK_DATA['indicadores'].values())
    }
    return render(request, 'new-screens/menu.html', context)





@login_required
@require_http_methods(["GET"])
def dimensoes(request):
    context = {
        'dimensoes': MOCK_DATA['dimensoes'],
        'username': request.user.username,
        'user_type': request.user.user_type
    }
    return render(request, 'screens/dimensoes.html', context)

@login_required
@require_http_methods(["GET"])
def indicadores(request, dimensao_id=None):
    # If no dimension specified, use one from session or default to 'economia'
    if dimensao_id is None:
        dimensao_id = request.session.get('dimensao_id', 'economia')
    
    # Find dimension by ID
    dimensao = next((d for d in MOCK_DATA['dimensoes'] if d['id'] == dimensao_id), None)
    
    if not dimensao:
        messages.error(request, 'Dimensão não encontrada')
        return redirect('dimensoes')
    
    # Store selected dimension in session
    request.session['dimensao_id'] = dimensao_id
    request.session['dimensao_nome'] = dimensao['nome']
    
    # Get indicators for this dimension
    indicadores = MOCK_DATA['indicadores'].get(dimensao_id, [])
    
    context = {
        'dimensao': dimensao,
        'indicadores': indicadores,
        'dimensoes': MOCK_DATA['dimensoes'],  # For navigation menu
        'username': request.user.username,
        'user_type': request.user.user_type
    }
    
    return render(request, 'screens/indicadores.html', context)

@login_required
def normas(request):
    return render(request, 'accounts/normas.html')

@login_required
def plataformas(request):
    return render(request, 'accounts/plataformas.html')

@login_required
def listar_plataformas(request):
    platforms = Platform.objects.all()
    return JsonResponse({
        'status': 'success',
        'plataformas': [
            {
                'id': p.id_plataforma,
                'name': p.Nome,
                'link': p.Direcionamento
            } for p in platforms
        ]
    })

def normalize_url(url):
    """Normaliza URL para garantir que tenha protocolo"""
    if not url:
        return url

    url = url.strip()

    # Se não tem protocolo, adiciona https://
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    return url

@login_required
@admin_required
def adicionar_plataforma(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            name = data.get('name')
            link = data.get('link')
        except (json.JSONDecodeError, AttributeError):
            name = request.POST.get('name')
            link = request.POST.get('link')

        if not name or not link:
            return JsonResponse({'success': False, 'message': 'Nome e link são obrigatórios'})

        # Normalizar URL
        link = normalize_url(link)

        try:
            platform = Platform.objects.create(Nome=name, Direcionamento=link)
            return JsonResponse({'success': True, 'message': 'Plataforma adicionada com sucesso'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
@admin_required
def editar_plataforma(request, platform_id):
    if request.method == 'POST':
        platform = get_object_or_404(Platform, id_plataforma=platform_id)
        
        try:
            import json
            data = json.loads(request.body)
            name = data.get('name')
            link = data.get('link')
        except (json.JSONDecodeError, AttributeError):
            name = request.POST.get('name')
            link = request.POST.get('link')
        
        if not name or not link:
            return JsonResponse({'success': False, 'message': 'Nome e link são obrigatórios'})

        # Normalizar URL
        link = normalize_url(link)

        try:
            platform.Nome = name
            platform.Direcionamento = link
            platform.save()
            return JsonResponse({'success': True, 'message': 'Plataforma editada com sucesso'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
@admin_required
def remover_plataforma(request, platform_id):
    if request.method == 'DELETE':
        platform = get_object_or_404(Platform, id_plataforma=platform_id)
        try:
            platform.delete()
            return JsonResponse({'success': True, 'message': 'Plataforma removida com sucesso'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})






#CSC
@login_required
def csc_dashboard(request):
    return render(request, "accounts/plataformas/csc.html")


def get_csc_platforms(ano=None):
    qs = Platform.objects.select_related("ano_referencia").filter(
        nome__istartswith="CSC"
    )

    if ano:
        qs = qs.filter(ano_referencia__ano=ano)

    return qs


def get_latest_csc_platform():
    return (
        Platform.objects
        .select_related("ano_referencia")
        .filter(nome__istartswith="CSC")
        .order_by("-ano_referencia__ano")
        .first()
    )


def format_value(valor):
    if not valor:
        return None

    if valor.valor_numerico is not None:
        return valor.valor_numerico

    if valor.valor_texto not in [None, ""]:
        return valor.valor_texto

    return None


def uf_from_municipio(municipio):
    estado = municipio.estado or ""
    estado = estado.strip()

    if len(estado) == 2:
        return estado.upper()

    return estado


def regiao_por_uf(uf):
    mapa = {
        "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte",
        "RO": "Norte", "RR": "Norte", "TO": "Norte",
        "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste",
        "MA": "Nordeste", "PB": "Nordeste", "PE": "Nordeste",
        "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
        "DF": "Centro-Oeste", "GO": "Centro-Oeste",
        "MT": "Centro-Oeste", "MS": "Centro-Oeste",
        "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
        "PR": "Sul", "RS": "Sul", "SC": "Sul",
    }
    return mapa.get((uf or "").upper(), "")


@login_required
def api_estados(request):
    estados = (
        Municipality.objects
        .exclude(estado__isnull=True)
        .exclude(estado="")
        .values_list("estado", flat=True)
        .distinct()
        .order_by("estado")
    )

    data = [{"estado": estado} for estado in estados if estado]

    return JsonResponse({"success": True, "data": data})


@login_required
def api_municipios(request):
    estado = request.GET.get("estado", "").strip()

    qs = Municipality.objects.all()

    if estado:
        qs = qs.filter(estado=estado)

    qs = qs.order_by("nome")

    data = [
        {
            "id": m.id,
            "nome": m.nome,
            "estado": m.estado,
            "codigo_ibge": m.codigo_ibge,
        }
        for m in qs
    ]

    return JsonResponse({"success": True, "data": data})


@login_required
def get_municipio_data(request, municipio_id):
    try:
        municipio = Municipality.objects.get(id=municipio_id)

        ano = request.GET.get("ano", "").strip()

        plataformas = get_csc_platforms(ano=ano)

        # Se o usuário pediu 2025, mas só existe 2024, pega a última CSC existente.
        if not plataformas.exists():
            latest = get_latest_csc_platform()
            if latest:
                plataformas = Platform.objects.filter(id=latest.id)

        plataforma_ids = list(plataformas.values_list("id", flat=True))

        categorias = (
            Category.objects
            .filter(
                plataforma_id__in=plataforma_ids,
                norma_iso__isnull=True,
            )
            .select_related("plataforma", "plataforma__ano_referencia")
            .prefetch_related(
                "categoria_indicadores",
                "categoria_indicadores__indicador",
            )
            .order_by("nome")
        )

        indicador_ids = (
            IndicatorCategory.objects
            .filter(categoria__in=categorias)
            .values_list("indicador_id", flat=True)
            .distinct()
        )

        valores = (
            IndicatorValueYear.objects
            .filter(
                municipio=municipio,
                indicador_id__in=indicador_ids,
            )
            .select_related("indicador")
        )

        valores_por_indicador = {}
        for valor in valores:
            valores_por_indicador[valor.indicador_id] = valor

        indicadores_data = {}

        for categoria in categorias:
            ano_ref = categoria.plataforma.ano_referencia.ano
            categoria_nome = categoria.nome

            indicadores_categoria = []

            for vinculo in categoria.categoria_indicadores.all():
                indicador = vinculo.indicador
                valor_obj = valores_por_indicador.get(indicador.id)
                valor_final = format_value(valor_obj)

                item = {
                    "indicador_id": indicador.id,
                    "indicador_nome": indicador.nome,
                    "indicador_descricao": indicador.descricao or "",
                    "eixo": categoria_nome,
                    "categoria_id": categoria.id,
                    "categoria_nome": categoria_nome,
                    "plataforma": categoria.plataforma.nome,
                    "ano_referencia": ano_ref,
                    "valores": {},
                    "valor": valor_final,
                    "ano_coleta": ano_ref if valor_final is not None else None,
                    "unidade": indicador.unidade_medida or "",
                    "fonte": valor_obj.fonte if valor_obj else "",
                }

                if valor_final is not None:
                    item["valores"][str(ano_ref)] = valor_final

                indicadores_categoria.append(item)

            if indicadores_categoria:
                indicadores_data[categoria_nome] = indicadores_categoria

        rankings_qs = (
            MunicipalityRanking.objects
            .filter(
                municipio=municipio,
                categoria__plataforma_id__in=plataforma_ids,
                categoria__norma_iso__isnull=True,
            )
            .select_related(
                "categoria",
                "categoria__plataforma",
                "categoria__plataforma__ano_referencia",
            )
            .order_by("categoria__nome")
        )

        rankings = []

        for r in rankings_qs:
            rankings.append({
                "ano": r.categoria.plataforma.ano_referencia.ano,
                "grupo": r.categoria.nome,
                "categoria_id": r.categoria.id,
                "posicao": r.pontuacao_total_categoria,
                "nota": r.pontuacao_total_categoria or 0,
                "indicadores_preenchidos": r.indicadores_preenchidos,
                "indicadores_totais": r.indicadores_totais,
                "cor_classificacao": r.cor_classificacao or "",
                "plataforma": r.categoria.plataforma.nome,
            })

        return JsonResponse({
            "municipio": {
                "id": municipio.id,
                "nome": municipio.nome,
                "estado": municipio.estado,
                "codigo_ibge": municipio.codigo_ibge,
                "latitude": municipio.latitude,
                "longitude": municipio.longitude,
            },
            "rankings": rankings,
            "indicadores": indicadores_data,
            "debug": {
                "plataformas": list(plataformas.values("id", "nome", "ano_referencia__ano")),
                "categorias_count": categorias.count(),
                "indicadores_count": len(set(indicador_ids)),
                "valores_count": valores.count(),
                "rankings_count": rankings_qs.count(),
            }
        })

    except Municipality.DoesNotExist:
        return JsonResponse({"error": "Município não encontrado"}, status=404)

    except Exception as e:
        import traceback
        return JsonResponse({
            "error": str(e),
            "traceback": traceback.format_exc(),
        }, status=500)


@login_required
def get_ranking_data(request):
    try:
        ano = request.GET.get("ano", "").strip()
        regiao = request.GET.get("regiao", "").strip()
        estado = request.GET.get("estado", "").strip()
        busca = request.GET.get("busca", "").strip()

        plataformas = get_csc_platforms(ano=ano)

        if not plataformas.exists():
            latest = get_latest_csc_platform()
            if latest:
                plataformas = Platform.objects.filter(id=latest.id)

        plataforma_ids = list(plataformas.values_list("id", flat=True))

        rankings = (
            MunicipalityRanking.objects
            .filter(
                categoria__plataforma_id__in=plataforma_ids,
                categoria__norma_iso__isnull=True,
            )
            .select_related(
                "municipio",
                "categoria",
                "categoria__plataforma",
                "categoria__plataforma__ano_referencia",
            )
        )

        if estado:
            rankings = rankings.filter(municipio__estado=estado)

        if busca:
            rankings = rankings.filter(municipio__nome__icontains=busca)

        if regiao:
            ufs = [
                uf for uf in [
                    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
                    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
                    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
                ]
                if regiao_por_uf(uf) == regiao
            ]
            rankings = rankings.filter(municipio__estado__in=ufs)

        # Tenta ranking geral, mas se não existir, mostra todos.
        geral = rankings.filter(
            Q(categoria__nome__iexact="Geral") |
            Q(categoria__nome__icontains="geral")
        )

        if geral.exists():
            rankings = geral

        rankings = rankings.order_by("pontuacao_total_categoria", "municipio__nome")[:100]

        data = []

        for index, r in enumerate(rankings, start=1):
            uf = uf_from_municipio(r.municipio)

            data.append({
                "position": r.pontuacao_total_categoria or index,
                "uf": uf,
                "municipio": r.municipio.nome,
                "codigo_ibge": r.municipio.codigo_ibge,
                "nota": r.pontuacao_total_categoria or 0,
                "porte": getattr(r.municipio, "porte", "") or "",
                "regiao": getattr(r.municipio, "regiao", "") or regiao_por_uf(uf),
                "categoria": r.categoria.nome,
                "categoria_id": r.categoria.id,
                "plataforma": r.categoria.plataforma.nome,
                "ano": r.categoria.plataforma.ano_referencia.ano,
            })

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def get_csc_summary(request):
    try:
        ano = request.GET.get("ano", "").strip()

        plataformas = get_csc_platforms(ano=ano)

        if not plataformas.exists():
            latest = get_latest_csc_platform()
            if latest:
                plataformas = Platform.objects.filter(id=latest.id)

        plataforma_ids = list(plataformas.values_list("id", flat=True))

        categorias = (
            Category.objects
            .filter(
                plataforma_id__in=plataforma_ids,
                norma_iso__isnull=True,
            )
            .annotate(quantidade_indicadores=Count("categoria_indicadores", distinct=True))
            .select_related("plataforma", "plataforma__ano_referencia")
            .order_by("nome")
        )

        total_indicadores = (
            Indicator.objects
            .filter(
                indicador_categorias__categoria__plataforma_id__in=plataforma_ids,
                indicador_categorias__categoria__norma_iso__isnull=True,
            )
            .distinct()
            .count()
        )

        eixos = {}

        for c in categorias:
            eixos[str(c.id)] = {
                "id": c.id,
                "nome": c.nome,
                "descricao": c.descricao or "",
                "plataforma": c.plataforma.nome,
                "ano": c.plataforma.ano_referencia.ano,
                "quantidade": c.quantidade_indicadores,
            }

        return JsonResponse({
            "total_indicadores": total_indicadores,
            "eixos": eixos,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)










@login_required
@require_http_methods(["GET"])
def inteligente(request):
    context = {
        'dimensoes': MOCK_DATA['dimensoes'],
        'username': request.user.username
    }
    return render(request, 'accounts/plataformas/inteligente.html', context)






# API for dimensions
@require_http_methods(["GET"])
def api_dimensoes(request):
    # Check if user is logged in via API
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Não autorizado'}, status=401)
    
    return JsonResponse(MOCK_DATA['dimensoes'], safe=False)

# API for indicators
@require_http_methods(["GET"])
def api_indicadores(request, dimensao_id):
    # Check if user is logged in via API
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Não autorizado'}, status=401)
    
    # Verify if dimension exists
    if dimensao_id not in MOCK_DATA['indicadores']:
        return JsonResponse({'error': 'Dimensão não encontrada'}, status=404)
    
    indicadores = MOCK_DATA['indicadores'].get(dimensao_id, [])
    return JsonResponse(indicadores, safe=False)

# API to create a new dimension
@csrf_exempt
@require_http_methods(["POST"])
def criar_dimensao(request):
    # Check if user is logged in via API
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Não autorizado'}, status=401)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['id', 'nome', 'cor']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Campo obrigatório ausente: {field}'}, status=400)
        
        # Check if ID already exists
        if any(d['id'] == data['id'] for d in MOCK_DATA['dimensoes']):
            return JsonResponse({'error': 'Dimensão com este ID já existe'}, status=400)
        
        # Create new dimension
        nova_dimensao = {
            'id': data['id'],
            'nome': data['nome'],
            'cor': data['cor'],
            'ods': data.get('ods', ''),
            'iso': data.get('iso', '')
        }
        
        MOCK_DATA['dimensoes'].append(nova_dimensao)
        MOCK_DATA['indicadores'][data['id']] = []  # Initialize empty indicators list
        
        return JsonResponse(nova_dimensao, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# API to edit an existing dimension
@csrf_exempt
@require_http_methods(["PUT"])
def editar_dimensao(request, dimensao_id):
    # Check if user is logged in via API
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Não autorizado'}, status=401)
    
    try:
        data = json.loads(request.body)
        
        # Find dimension by ID
        dimensao = next((d for d in MOCK_DATA['dimensoes'] if d['id'] == dimensao_id), None)
        
        if not dimensao:
            return JsonResponse({'error': 'Dimensão não encontrada'}, status=404)
        
        # Update fields
        if 'nome' in data:
            dimensao['nome'] = data['nome']
        if 'cor' in data:
            dimensao['cor'] = data['cor']
        if 'ods' in data:
            dimensao['ods'] = data['ods']
        if 'iso' in data:
            dimensao['iso'] = data['iso']
        
        return JsonResponse(dimensao)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# API to remove a dimension
@csrf_exempt
@require_http_methods(["DELETE"])
def remover_dimensao(request, dimensao_id):
    # Check if user is logged in via API
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Não autorizado'}, status=401)
    
    # Find dimension index
    index = next((i for i, d in enumerate(MOCK_DATA['dimensoes']) if d['id'] == dimensao_id), None)
    
    if index is None:
        return JsonResponse({'error': 'Dimensão não encontrada'}, status=404)
    
    # Remove dimension
    dimensao_removida = MOCK_DATA['dimensoes'].pop(index)
    
    # Remove associated indicators
    if dimensao_id in MOCK_DATA['indicadores']:
        del MOCK_DATA['indicadores'][dimensao_id]
    
    return JsonResponse({'success': True, 'removed': dimensao_removida})

# API to add a new indicator to a dimension
@csrf_exempt
@require_http_methods(["POST"])
def adicionar_indicador(request, dimensao_id):
    # Check if user is logged in via API
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Não autorizado'}, status=401)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['nome', 'dado']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Campo obrigatório ausente: {field}'}, status=400)
        
        # Check if dimension exists
        if dimensao_id not in MOCK_DATA['indicadores']:
            return JsonResponse({'error': 'Dimensão não encontrada'}, status=404)
        
        # Create new indicator
        novo_indicador = {
            'id': get_next_indicator_id(dimensao_id),
            'nome': data['nome'],
            'dado': data['dado'],
            'ods': data.get('ods', ''),
            'fonte': data.get('fonte', ''),
            'iso': data.get('iso', '')
        }
        
        # Add to dimension's indicators list
        MOCK_DATA['indicadores'][dimensao_id].append(novo_indicador)
        
        return JsonResponse(novo_indicador, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# API to edit an existing indicator
@csrf_exempt
@require_http_methods(["PUT"])
def editar_indicador(request, dimensao_id, indicador_id):
    # Check if user is logged in via API
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Não autorizado'}, status=401)
    
    try:
        data = json.loads(request.body)
        indicador_id = int(indicador_id)  # Convert to integer
        
        # Check if dimension exists
        if dimensao_id not in MOCK_DATA['indicadores']:
            return JsonResponse({'error': 'Dimensão não encontrada'}, status=404)
        
        # Find the indicator
        indicador = next((ind for ind in MOCK_DATA['indicadores'][dimensao_id] if ind['id'] == indicador_id), None)
        
        if not indicador:
            return JsonResponse({'error': 'Indicador não encontrado'}, status=404)
        
        # Update fields
        if 'nome' in data:
            indicador['nome'] = data['nome']
        if 'dado' in data:
            indicador['dado'] = data['dado']
        if 'ods' in data:
            indicador['ods'] = data['ods']
        if 'fonte' in data:
            indicador['fonte'] = data['fonte']
        if 'iso' in data:
            indicador['iso'] = data['iso']
        
        return JsonResponse(indicador)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados JSON inválidos'}, status=400)
    except ValueError:
        return JsonResponse({'error': 'ID do indicador inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# API to delete an indicator
@csrf_exempt
@require_http_methods(["DELETE"])
def excluir_indicador(request, dimensao_id, indicador_id):
    # Check if user is logged in via API
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Não autorizado'}, status=401)
    
    try:
        indicador_id = int(indicador_id)  # Convert to integer
        
        # Check if dimension exists
        if dimensao_id not in MOCK_DATA['indicadores']:
            return JsonResponse({'error': 'Dimensão não encontrada'}, status=404)
        
        # Find indicator index
        indicadores = MOCK_DATA['indicadores'][dimensao_id]
        index = next((i for i, ind in enumerate(indicadores) if ind['id'] == indicador_id), None)
        
        if index is None:
            return JsonResponse({'error': 'Indicador não encontrado'}, status=404)
        
        # Remove indicator
        indicador_removido = indicadores.pop(index)
        
        return JsonResponse({'success': True, 'removed': indicador_removido})
    
    except ValueError:
        return JsonResponse({'error': 'ID do indicador inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




def serve_static(request, path):
    """Improved function to serve static files."""
    # Try Django's staticfiles system first
    static_file = finders.find(path)
    if static_file:
        content_type, encoding = mimetypes.guess_type(static_file)
        if content_type is None:
            if path.endswith('.css'):
                content_type = 'text/css'
            elif path.endswith('.js'):
                content_type = 'application/javascript'
            else:
                content_type = 'application/octet-stream'
                
        return FileResponse(open(static_file, 'rb'), content_type=content_type)
    
    # If not found in staticfiles, search through various directories
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'static', path),
        os.path.join(settings.BASE_DIR, 'templates', 'static', path),
    ]
    
    for file_path in possible_paths:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            content_type, encoding = mimetypes.guess_type(file_path)
            if content_type is None:
                if path.endswith('.css'):
                    content_type = 'text/css'
                elif path.endswith('.js'):
                    content_type = 'application/javascript'
                else:
                    content_type = 'application/octet-stream'
            
            return FileResponse(open(file_path, 'rb'), content_type=content_type)
    
    # If file not found
    return HttpResponse(f'Arquivo {path} não encontrado.', status=404)





# Dashboard view
def dashboard(request):
    # Check if user is logged in
    if 'user_id' not in request.session:
        return redirect('login')
    
    # Calculate some statistics for the dashboard
    total_dimensoes = len(MOCK_DATA['dimensoes'])
    total_indicadores = sum(len(inds) for inds in MOCK_DATA['indicadores'].values())
    
    # Get dimensions with most indicators
    dim_with_indicators = [(d['id'], d['nome'], len(MOCK_DATA['indicadores'].get(d['id'], []))) 
                          for d in MOCK_DATA['dimensoes']]
    dim_with_indicators.sort(key=lambda x: x[2], reverse=True)
    top_dimensions = dim_with_indicators[:5]
    
    context = {
        'username': request.session.get('username', ''),
        'total_dimensoes': total_dimensoes,
        'total_indicadores': total_indicadores,
        'top_dimensions': top_dimensions,
        'dimensoes': MOCK_DATA['dimensoes']  # For navigation
    }
    
    return render(request, 'screens/dashboard.html', context)



# View for detailed indicators
def indicador_detalhes(request, dimensao_id, indicador_id):
    # Check if user is logged in
    if 'user_id' not in request.session:
        return redirect('login')
    
    try:
        indicador_id = int(indicador_id)
        
        # Check if dimension exists
        if dimensao_id not in MOCK_DATA['indicadores']:
            messages.error(request, 'Dimensão não encontrada')
            return redirect('dimensoes')
        
        # Find the indicator
        indicador = next((ind for ind in MOCK_DATA['indicadores'][dimensao_id] if ind['id'] == indicador_id), None)
        
        if not indicador:
            messages.error(request, 'Indicador não encontrado')
            return redirect('indicadores', dimensao_id=dimensao_id)
        
        # Find the dimension
        dimensao = next((d for d in MOCK_DATA['dimensoes'] if d['id'] == dimensao_id), None)
        
        context = {
            'username': request.session.get('username', ''),
            'dimensao': dimensao,
            'indicador': indicador,
            'dimensoes': MOCK_DATA['dimensoes']  # For navigation
        }
        
        return render(request, 'screens/indicador_detalhes.html', context)
    
    except ValueError:
        messages.error(request, 'ID do indicador inválido')
        return redirect('indicadores', dimensao_id=dimensao_id)
    
















# Admin User Management Views

def usuario_eh_gestor_lider(user):
    """
    Gestor líder: gestor criado diretamente por um administrador/superuser
    ou gestor com permissão explícita. Esses gestores podem criar e gerenciar
    gestores subordinados do próprio município.
    """
    if not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser or user.is_admin():
        return True
    if not user.is_manager():
        return False
    if user.has_perm('accounts.acesso_total_designacao'):
        return True
    criador = getattr(user, 'criado_por', None)
    return bool(criador and (criador.is_superuser or criador.is_admin()))


def usuario_pode_gerenciar_usuarios(user):
    return user.is_authenticated and (user.is_superuser or user.is_admin() or usuario_eh_gestor_lider(user))


def usuarios_visiveis_para(user):
    """Admin vê todos. Gestor líder vê somente ele e os gestores que criou."""
    qs = User.objects.select_related('municipio', 'criado_por').all()
    if user.is_superuser or user.is_admin():
        return qs
    if usuario_eh_gestor_lider(user):
        return qs.filter(Q(id=user.id) | Q(criado_por=user)).order_by('-created_at')
    return User.objects.none()


def usuario_pode_editar_usuario(user, target):
    if user.is_superuser or user.is_admin():
        return True
    if usuario_eh_gestor_lider(user):
        return target.criado_por_id == user.id
    return False


def gestor_esta_abaixo_de(user, gestor):
    """Verifica se um gestor pode receber designação criada por user."""
    if user.is_superuser or user.is_admin():
        return True
    if usuario_eh_gestor_lider(user):
        return gestor.criado_por_id == user.id or gestor.id == user.id
    return gestor.id == user.id






def admin_menu(request):
    """
    Menu de administração.

    - Administradores veem todas as opções administrativas.
    - Gestores veem apenas as áreas que podem acessar, como logs, auditoria,
      designações e metas.
    - Usuários comuns não acessam esta área.
    """
    user = request.user

    if not (user.is_admin() or user.is_manager() or user.is_superuser):
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('menu')

    is_admin = user.is_superuser or user.is_admin()
    can_view_logs = usuario_pode_acessar_auditoria(user)
    can_recover_logs = usuario_pode_acessar_auditoria(user, precisa_recuperar=True)
    # Todos os gestores podem abrir a área de designações: gestores líderes criam,
    # gestores subordinados visualizam/preenchem as designações recebidas.
    can_manage_designations = is_admin or user.is_manager() or user.has_perm('accounts.acesso_total_designacao')
    can_manage_users = usuario_pode_gerenciar_usuarios(user)

    context = {
        'username': user.username,
        'user_type': user.user_type,
        'is_admin_area': is_admin,
        'is_manager_area': user.is_manager(),
        'can_view_logs': can_view_logs,
        'can_recover_logs': can_recover_logs,
        'can_manage_designations': can_manage_designations,
        'can_access_goals': is_admin or user.is_manager(),
        'can_manage_users': can_manage_users,
    }
    return render(request, 'accounts/admin/menu.html', context)


@login_required




def list_users(request):
    """Listar usuários respeitando a hierarquia."""
    if not usuario_pode_gerenciar_usuarios(request.user):
        messages.error(request, 'Você não tem permissão para gerenciar usuários.')
        return redirect('admin_menu')

    users = usuarios_visiveis_para(request.user).order_by('-created_at')
    context = {
        'users': users,
        'username': request.user.username,
        'user_type': request.user.user_type,
        'can_create_admin': request.user.is_superuser or request.user.is_admin(),
        'is_manager_leader': usuario_eh_gestor_lider(request.user),
    }
    return render(request, 'accounts/admin/list_users.html', context)


@login_required
def add_user(request):
    """Adicionar novo usuário respeitando a hierarquia."""
    if not usuario_pode_gerenciar_usuarios(request.user):
        messages.error(request, 'Você não tem permissão para criar usuários.')
        return redirect('admin_menu')

    def _generate_random_password(tamanho=15):
        caracteres = string.ascii_letters + string.digits
        password = ''.join(random.choice(caracteres) for _ in range(tamanho))
        return password


    def _valid_cpf(cpf):
        cpf = ''.join(filter(str.isdigit, cpf))

        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False

        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito_1 = (soma * 10 % 11) % 10

        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito_2 = (soma * 10 % 11) % 10

        return cpf[-2:] == f"{digito_1}{digito_2}"
    

    def _send_credentials(username, password, email):
        email_user = os.getenv('EMAIL_HOST_USER')
        email_pass = os.getenv('EMAIL_HOST_PASSWORD')
        
        msg = EmailMessage()
        msg.set_content(f'Olá!\nAbaixo estão suas credenciais para logar no sistema.\nUsuário: {username}\nSenha Temporária: {password}')
        msg['Subject'] = 'Credenciais de Login - DataCity'
        msg['From'] = email_user
        msg['To'] = email

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(email_user, email_pass)
                smtp.send_message(msg)
            return True
        except Exception as e:
            print(f"Erro ao enviar: {e}")
            return False


    if request.method == 'POST':
        try:
            # Pegar dados do formulário
            nome = request.POST.get('nome')
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            cpf = request.POST.get('cpf')
            categoria = request.POST.get('categoria')
            cidade = request.POST.get('cidade')

            if usuario_eh_gestor_lider(request.user) and not (request.user.is_superuser or request.user.is_admin()):
                categoria = User.UserType.MANAGER
                cidade = request.user.municipio_id

            # Validar campos obrigatórios
            if not all([nome, username, email, cpf, cidade, categoria]):
                messages.error(request, 'Todos os campos são obrigatórios')
                return redirect('add_user')

            if not (request.user.is_superuser or request.user.is_admin()) and categoria != User.UserType.MANAGER:
                messages.error(request, 'Gestores líderes só podem criar novos usuários gestores.')
                return redirect('add_user')
            
            if not password:
                random_password = _generate_random_password()
                password = random_password

            # Verificar se o email já existe
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Já existe um usuário com este email')
                return redirect('add_user')
            
            if not _valid_cpf(cpf):
                messages.error(request, 'O CPF informado é inválido.')
                return redirect('add_user')
            
            if User.objects.filter(cpf=cpf).exists():
                messages.error(request, 'Já existe um usuário com este CPF')
                return redirect('add_user')

            # Verificar se o username já existe
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Já existe um usuário com este nome de usuário')
                return redirect('add_user')

            # Criar novo usuário (user_type será igual a categoria)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                nome=nome,
                cpf=cpf,
                municipio=Municipality.objects.get(id=cidade),
                categoria=categoria,
                user_type=categoria,
                criado_por=request.user
            )

            messages.success(request, f'Usuário {username} criado com sucesso!')
            _send_credentials(username, password,email)
            return redirect('list_users')

        except Exception as e:
            messages.error(request, f'Erro ao criar usuário: {str(e)}')
            return redirect('add_user')

    context = {
        'username': request.user.username,
        'user_type': request.user.user_type,
        'can_create_admin': request.user.is_superuser or request.user.is_admin(),
        'is_manager_leader': usuario_eh_gestor_lider(request.user),
        'municipio_gestor': getattr(request.user, 'municipio', None),
    }
    return render(request, 'accounts/admin/add_user.html', context)


@login_required
def edit_user(request, user_id):
    """Editar usuário existente respeitando a hierarquia."""
    if not usuario_pode_gerenciar_usuarios(request.user):
        messages.error(request, 'Você não tem permissão para editar usuários.')
        return redirect('admin_menu')

    user_to_edit = get_object_or_404(User, id=user_id)

    if not usuario_pode_editar_usuario(request.user, user_to_edit):
        messages.error(request, 'Você só pode editar usuários criados por você.')
        return redirect('list_users')

    def _cpf_valido(cpf):
        cpf = ''.join(filter(str.isdigit, cpf))

        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False

        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito_1 = (soma * 10 % 11) % 10

        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito_2 = (soma * 10 % 11) % 10

        return cpf[-2:] == f"{digito_1}{digito_2}"

    if request.method == 'POST':
        try:
            # Pegar dados do formulário
            nome = request.POST.get('nome')
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            cpf = request.POST.get('cpf')
            categoria = request.POST.get('categoria')
            cidade_id = request.POST.get('cidade')

            if usuario_eh_gestor_lider(request.user) and not (request.user.is_superuser or request.user.is_admin()):
                categoria = User.UserType.MANAGER
                cidade_id = request.user.municipio_id

            cidade = Municipality.objects.get(id=cidade_id)

            if not (request.user.is_superuser or request.user.is_admin()) and categoria != User.UserType.MANAGER:
                messages.error(request, 'Gestores líderes só podem manter subordinados como gestores.')
                return redirect('edit_user', user_id=user_id)

            # Validar campos obrigatórios
            if not all([nome, username, email, cpf, cidade, categoria]):
                messages.error(request, 'Todos os campos são obrigatórios')
                return redirect('edit_user', user_id=user_id)

            # Verificar se o email já existe (exceto para o usuário atual)
            if User.objects.filter(email=email).exclude(id=user_id).exists():
                messages.error(request, 'Já existe um usuário com este email')
                return redirect('edit_user', user_id=user_id)
            
            if User.objects.filter(cpf=cpf).exclude(id=user_id).exists():
                messages.error(request, 'Já existe um usuário com este CPF')
                return redirect('edit_user', user_id=user_id)
            
            if not _cpf_valido(cpf):
                messages.error(request, 'O CPF informado é inválido.')
                return redirect('edit_user', user_id=user_id)

            # Verificar se o username já existe (exceto para o usuário atual)
            if User.objects.filter(username=username).exclude(id=user_id).exists():
                messages.error(request, 'Já existe um usuário com este nome de usuário')
                return redirect('edit_user', user_id=user_id)

            # Atualizar dados do usuário (user_type será igual a categoria)
            user_to_edit.nome = nome
            user_to_edit.username = username
            user_to_edit.email = email
            user_to_edit.cpf = cpf
            user_to_edit.municipio = cidade
            user_to_edit.categoria = categoria
            user_to_edit.user_type = categoria

            # Atualizar senha apenas se foi fornecida
            if password:
                user_to_edit.set_password(password)

            user_to_edit.save()

            messages.success(request, f'Usuário {username} atualizado com sucesso!')
            return redirect('list_users')

        except Exception as e:
            messages.error(request, f'Erro ao atualizar usuário: {str(e)}')
            return redirect('edit_user', user_id=user_id)

    context = {
        'user_to_edit': user_to_edit,
        'username': request.user.username,
        'user_type': request.user.user_type,
        'can_create_admin': request.user.is_superuser or request.user.is_admin(),
        'is_manager_leader': usuario_eh_gestor_lider(request.user),
        'municipio_gestor': getattr(request.user, 'municipio', None),
    }
    return render(request, 'accounts/admin/edit_user.html', context)


@login_required
def delete_user(request, user_id):
    """Excluir usuário respeitando a hierarquia."""
    if request.method == 'POST':
        try:
            if not usuario_pode_gerenciar_usuarios(request.user):
                return JsonResponse({'success': False, 'message': 'Sem permissão para excluir usuários.'})

            user_to_delete = get_object_or_404(User, id=user_id)

            if not usuario_pode_editar_usuario(request.user, user_to_delete):
                return JsonResponse({'success': False, 'message': 'Você só pode excluir usuários criados por você.'})

            # Não permitir que o usuário delete a si mesmo
            if user_to_delete.id == request.user.id:
                return JsonResponse({
                    'success': False,
                    'message': 'Você não pode excluir sua própria conta'
                })

            username = user_to_delete.username
            user_to_delete.delete()

            return JsonResponse({
                'success': True,
                'message': f'Usuário {username} excluído com sucesso'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao excluir usuário: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })


@login_required
def change_user_role(request, user_id):
    """Modificar privilégios do usuário respeitando a hierarquia."""
    if request.method == 'POST':
        try:
            if not usuario_pode_gerenciar_usuarios(request.user):
                return JsonResponse({'success': False, 'message': 'Sem permissão para modificar usuários.'})

            user_to_change = get_object_or_404(User, id=user_id)
            new_role = request.POST.get('user_type')

            if not usuario_pode_editar_usuario(request.user, user_to_change):
                return JsonResponse({'success': False, 'message': 'Você só pode modificar usuários criados por você.'})

            if usuario_eh_gestor_lider(request.user) and not (request.user.is_superuser or request.user.is_admin()):
                new_role = User.UserType.MANAGER

            if new_role not in ['ADMIN', 'MANAGER', 'COMMON']:
                return JsonResponse({
                    'success': False,
                    'message': 'Tipo de usuário inválido'
                })

            # Não permitir que o admin mude seu próprio privilégio
            if user_to_change.id == request.user.id:
                return JsonResponse({
                    'success': False,
                    'message': 'Você não pode modificar seus próprios privilégios'
                })

            user_to_change.user_type = new_role
            user_to_change.categoria = new_role
            user_to_change.save()

            role_names = {
                'ADMIN': 'Administrador',
                'MANAGER': 'Gestor',
                'COMMON': 'Usuário Comum'
            }

            return JsonResponse({
                'success': True,
                'message': f'Privilégios de {user_to_change.username} alterados para {role_names[new_role]}'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao modificar privilégios: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })


@login_required
def list_states(request):
    try:
        # Busca estados únicos e transforma em lista de dicionários
        states = Municipality.objects.values('estado').distinct().order_by('estado')
        
        return JsonResponse({
            'success': True,
            'data': list(states)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def list_municipalities(request):
    estado_filtrado = request.GET.get('estado')
    
    try:
        query = Municipality.objects.all()
        if estado_filtrado:
            query = query.filter(estado=estado_filtrado)
            
        municipalities = query.values('id', 'nome').order_by('nome')
        
        return JsonResponse({
            'success': True,
            'data': list(municipalities)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})






def usuario_pode_acessar_auditoria(user, precisa_recuperar=False):
    """Permite auditoria para administradores, gestores e usuários com permissão explícita."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_admin() or user.is_manager():
        return True
    if precisa_recuperar:
        return user.has_perm('accounts.change_auditlog')
    return user.has_perm('accounts.view_auditlog')


@login_required
def logs_auditoria(request):
    if not usuario_pode_acessar_auditoria(request.user):
        messages.error(request, "Você não tem permissão para acessar os logs de auditoria.")
        return redirect("admin_menu")

    logs = AuditLog.objects.all().order_by("-criado_em")

    acao = request.GET.get("acao")
    usuario = request.GET.get("usuario")
    recuperavel = request.GET.get("recuperavel")

    if acao:
        logs = logs.filter(acao=acao)

    if usuario:
        logs = logs.filter(usuario__username__icontains=usuario)

    if recuperavel == "sim":
        logs = logs.filter(recuperavel=True, recuperado=False)

    context = {
        "logs": logs,
        "acao": acao,
        "usuario": usuario,
        "recuperavel": recuperavel,
        "acoes": AuditLog.AcaoChoices.choices,
    }

    return render(request, "accounts/audit/logs.html", context)


@login_required
def detalhe_log_auditoria(request, log_id):
    if not usuario_pode_acessar_auditoria(request.user):
        messages.error(request, "Você não tem permissão para acessar este log.")
        return redirect("admin_menu")

    log = get_object_or_404(AuditLog, id=log_id)

    return render(request, "accounts/audit/detalhe_log.html", {
        "log": log,
    })


@login_required
def recuperacao_auditoria(request):
    if not usuario_pode_acessar_auditoria(request.user, precisa_recuperar=True):
        messages.error(request, "Você não tem permissão para acessar a recuperação de dados.")
        return redirect("admin_menu")

    logs_recuperaveis = AuditLog.objects.filter(
        recuperavel=True,
        recuperado=False,
    ).order_by("-criado_em")

    return render(request, "accounts/audit/recuperacao.html", {
        "logs_recuperaveis": logs_recuperaveis,
    })


@login_required
@require_POST
@transaction.atomic
def recuperar_auditoria(request, log_id):
    if not usuario_pode_acessar_auditoria(request.user, precisa_recuperar=True):
        messages.error(request, "Você não tem permissão para recuperar dados.")
        return redirect("recuperacao")

    log = get_object_or_404(
        AuditLog,
        id=log_id,
        recuperavel=True,
        recuperado=False,
    )

    try:
        if log.acao == AuditLog.AcaoChoices.ANEXO_APAGADO:
            recuperar_anexo_apagado(log)

        elif log.acao in [AuditLog.AcaoChoices.VALOR_ALTERADO, AuditLog.AcaoChoices.PREENCHIMENTO_DESIGNADO]:
            recuperar_valor_alterado(log)

        elif log.acao == AuditLog.AcaoChoices.INDICADOR_EDITADO:
            recuperar_indicador_editado(log)

        elif log.acao == AuditLog.AcaoChoices.INDICADOR_DELETADO:
            recuperar_indicador_deletado(log)

        else:
            messages.error(request, "Esse tipo de log não possui recuperação automática.")
            return redirect("recuperacao")

        log.recuperado = True
        log.recuperado_por = request.user
        log.recuperado_em = timezone.now()
        log.save()

        AuditLog.objects.create(
            usuario=request.user,
            acao=AuditLog.AcaoChoices.RECUPERACAO,
            objeto_tipo=log.objeto_tipo,
            objeto_id=log.objeto_id,
            descricao=f"Recuperação realizada a partir do log #{log.id}.",
            dados_anteriores=log.dados_novos,
            dados_novos=log.dados_anteriores,
            recuperavel=False,
            recuperado=True,
            recuperado_por=request.user,
            recuperado_em=timezone.now(),
        )

        messages.success(request, "Recuperação realizada com sucesso.")

    except Exception as erro:
        messages.error(request, f"Erro ao recuperar os dados: {erro}")

    return redirect("recuperacao")


def recuperar_anexo_apagado(log):
    """
    Recupera um anexo apagado logicamente.
    Usa o model EvidencePDF.
    """
    evidencia = get_object_or_404(EvidencePDF, id=log.objeto_id)

    evidencia.apagado = False
    evidencia.apagado_por = None
    evidencia.apagado_em = None
    evidencia.save()


def recuperar_valor_alterado(log):
    """
    Recupera valor anterior de IndicatorValueYear.
    Restaura valor_numerico, valor_texto e fonte.
    """
    valor_indicador = get_object_or_404(IndicatorValueYear, id=log.objeto_id)

    campos_anteriores = log.dados_anteriores.get("campos", {})

    for campo, valor_antigo in campos_anteriores.items():
        setattr(valor_indicador, campo, valor_antigo)

    valor_indicador.save()


def recuperar_indicador_editado(log):
    """
    Recupera dados anteriores de um indicador editado.
    Também restaura todos os vínculos de categoria quando o log tiver categorias_ids.
    """
    indicador = get_object_or_404(Indicator, id=log.objeto_id)

    campos_anteriores = dict(log.dados_anteriores.get("campos", {}))
    categorias_ids = campos_anteriores.pop("categorias_ids", None)
    categoria_id = campos_anteriores.pop("categoria_id", None)
    if categorias_ids is None and categoria_id:
        categorias_ids = [categoria_id]

    for campo, valor_antigo in campos_anteriores.items():
        if hasattr(indicador, campo):
            setattr(indicador, campo, valor_antigo)

    indicador.save()

    if categorias_ids is not None:
        IndicatorCategory.objects.filter(indicador=indicador).delete()
        for categoria in Category.objects.filter(id__in=categorias_ids):
            IndicatorCategory.objects.get_or_create(indicador=indicador, categoria=categoria)


def recuperar_indicador_deletado(log):
    """
    Recupera um indicador deletado logicamente.
    Também restaura todos os vínculos de categoria quando o log tiver categorias_ids.
    """
    indicador = get_object_or_404(Indicator, id=log.objeto_id)

    campos_anteriores = dict(log.dados_anteriores.get("campos", {}))
    categorias_ids = campos_anteriores.pop("categorias_ids", None)
    categoria_id = campos_anteriores.pop("categoria_id", None)
    if categorias_ids is None and categoria_id:
        categorias_ids = [categoria_id]

    for campo, valor_antigo in campos_anteriores.items():
        if hasattr(indicador, campo):
            setattr(indicador, campo, valor_antigo)

    indicador.deletado = False
    indicador.ativo = True
    indicador.deletado_em = None
    indicador.deletado_por = None
    indicador.save()

    if categorias_ids is not None:
        IndicatorCategory.objects.filter(indicador=indicador).delete()
        for categoria in Category.objects.filter(id__in=categorias_ids):
            IndicatorCategory.objects.get_or_create(indicador=indicador, categoria=categoria)


@login_required
@permission_required("accounts.delete_evidencepdf", raise_exception=True)
@require_POST
@transaction.atomic
def apagar_anexo_auditoria(request, evidencia_id):
    """
    Apaga uma evidência PDF de forma lógica.
    Não remove o arquivo físico.
    """
    evidencia = get_object_or_404(
        EvidencePDF,
        id=evidencia_id,
        apagado=False,
    )

    dados_anteriores = {
        "campos": {
            "descricao": evidencia.descricao,
            "caminho_arquivo": evidencia.caminho_arquivo,
            "apagado": False,
            "valor_indicador_ano_id": evidencia.valor_indicador_ano_id,
        }
    }

    evidencia.apagado = True
    evidencia.apagado_por = request.user
    evidencia.apagado_em = timezone.now()
    evidencia.save()

    AuditLog.objects.create(
        usuario=request.user,
        acao=AuditLog.AcaoChoices.ANEXO_APAGADO,
        objeto_tipo="EvidencePDF",
        objeto_id=evidencia.id,
        descricao=f"Anexo apagado: {evidencia.caminho_arquivo}",
        dados_anteriores=dados_anteriores,
        dados_novos={
            "campos": {
                "apagado": True,
                "apagado_por_id": request.user.id,
                "apagado_em": timezone.now().isoformat(),
            }
        },
        recuperavel=True,
    )

    messages.success(request, "Anexo apagado e registrado na auditoria.")
    return redirect("logs")


@login_required
@permission_required("accounts.change_indicatorvalueyear", raise_exception=True)
@require_POST
@transaction.atomic
def alterar_valor_indicador_auditoria(request, valor_id):
    """
    Altera valor de um indicador e registra o valor anterior.
    Model usado: IndicatorValueYear.
    """
    valor_indicador = get_object_or_404(IndicatorValueYear, id=valor_id)

    dados_anteriores = {
        "campos": {
            "valor_numerico": valor_indicador.valor_numerico,
            "valor_texto": valor_indicador.valor_texto,
            "fonte": valor_indicador.fonte,
        }
    }

    valor_numerico = request.POST.get("valor_numerico")
    valor_texto = request.POST.get("valor_texto")
    fonte = request.POST.get("fonte")

    valor_indicador.valor_numerico = valor_numerico or None
    valor_indicador.valor_texto = valor_texto or None
    valor_indicador.fonte = fonte or None

    if hasattr(valor_indicador, "atualizado_por"):
        valor_indicador.atualizado_por = request.user

    valor_indicador.save()

    dados_novos = {
        "campos": {
            "valor_numerico": valor_indicador.valor_numerico,
            "valor_texto": valor_indicador.valor_texto,
            "fonte": valor_indicador.fonte,
        }
    }

    AuditLog.objects.create(
        usuario=request.user,
        acao=AuditLog.AcaoChoices.VALOR_ALTERADO,
        objeto_tipo="IndicatorValueYear",
        objeto_id=valor_indicador.id,
        descricao=f"Valor alterado para o indicador {valor_indicador.indicador.nome} em {valor_indicador.municipio}.",
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        recuperavel=True,
    )

    messages.success(request, "Valor alterado e registrado na auditoria.")
    return redirect("logs")


@login_required
@permission_required("accounts.change_indicator", raise_exception=True)
@require_POST
@transaction.atomic
def editar_indicador_auditoria(request, indicador_id):
    """
    Edita um indicador e registra os dados anteriores.
    Model usado: Indicator.
    """
    indicador = get_object_or_404(
        Indicator,
        id=indicador_id,
        deletado=False,
    )

    dados_anteriores = {
        "campos": {
            "nome": indicador.nome,
            "descricao": indicador.descricao,
            "tipo": indicador.tipo,
            "opcoes_predefinidas": indicador.opcoes_predefinidas,
            "unidade_medida": indicador.unidade_medida,
            "direcao_melhoria": indicador.direcao_melhoria,
            "ods": indicador.ods,
            "ativo": getattr(indicador, "ativo", True),
            "deletado": getattr(indicador, "deletado", False),
        }
    }

    indicador.nome = request.POST.get("nome") or indicador.nome
    indicador.descricao = request.POST.get("descricao") or None
    indicador.tipo = request.POST.get("tipo") or indicador.tipo
    indicador.unidade_medida = request.POST.get("unidade_medida") or None

    direcao_melhoria = request.POST.get("direcao_melhoria")
    indicador.direcao_melhoria = direcao_melhoria or None

    if hasattr(indicador, "ativo"):
        indicador.ativo = request.POST.get("ativo") == "on"

    indicador.save()

    dados_novos = {
        "campos": {
            "nome": indicador.nome,
            "descricao": indicador.descricao,
            "tipo": indicador.tipo,
            "opcoes_predefinidas": indicador.opcoes_predefinidas,
            "unidade_medida": indicador.unidade_medida,
            "direcao_melhoria": indicador.direcao_melhoria,
            "ods": indicador.ods,
            "ativo": getattr(indicador, "ativo", True),
            "deletado": getattr(indicador, "deletado", False),
        }
    }

    AuditLog.objects.create(
        usuario=request.user,
        acao=AuditLog.AcaoChoices.INDICADOR_EDITADO,
        objeto_tipo="Indicator",
        objeto_id=indicador.id,
        descricao=f"Indicador editado: {indicador.nome}",
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        recuperavel=True,
    )

    messages.success(request, "Indicador editado e registrado na auditoria.")
    return redirect("logs")


@login_required
@permission_required("accounts.delete_indicator", raise_exception=True)
@require_POST
@transaction.atomic
def deletar_indicador_auditoria(request, indicador_id):
    """
    Deleta indicador de forma lógica.
    Não remove o registro do banco.
    """
    indicador = get_object_or_404(
        Indicator,
        id=indicador_id,
        deletado=False,
    )

    dados_anteriores = {
        "campos": {
            "nome": indicador.nome,
            "descricao": indicador.descricao,
            "tipo": indicador.tipo,
            "opcoes_predefinidas": indicador.opcoes_predefinidas,
            "unidade_medida": indicador.unidade_medida,
            "direcao_melhoria": indicador.direcao_melhoria,
            "ods": indicador.ods,
            "ativo": getattr(indicador, "ativo", True),
            "deletado": getattr(indicador, "deletado", False),
            "deletado_em": None,
            "deletado_por_id": None,
        }
    }

    indicador.deletado = True
    indicador.ativo = False
    indicador.deletado_em = timezone.now()
    indicador.deletado_por = request.user
    indicador.save()

    dados_novos = {
        "campos": {
            "ativo": False,
            "deletado": True,
            "deletado_em": indicador.deletado_em.isoformat(),
            "deletado_por_id": request.user.id,
        }
    }

    AuditLog.objects.create(
        usuario=request.user,
        acao=AuditLog.AcaoChoices.INDICADOR_DELETADO,
        objeto_tipo="Indicator",
        objeto_id=indicador.id,
        descricao=f"Indicador deletado: {indicador.nome}",
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        recuperavel=True,
    )

    messages.success(request, "Indicador deletado e registrado na auditoria.")
    return redirect("logs")








def usuario_tem_acesso_total_designacao(user):
    return (
        user.is_superuser
        or getattr(user, "user_type", None) == User.UserType.ADMIN
        or usuario_eh_gestor_lider(user)
        or user.has_perm("accounts.acesso_total_designacao")
    )


def _municipio_escopo_designacao(user):
    """
    Município usado para limitar as designações de contas com acesso total.

    Regra:
    - gestor/admin com município cadastrado: só designa e gerencia contas do próprio município;
    - superuser/admin sem município: pode operar em modo global, usando o município do gestor escolhido.
    """
    return getattr(user, "municipio", None)


def _pode_gerenciar_designacao_do_municipio(user, municipio_id):
    if not usuario_tem_acesso_total_designacao(user):
        return False

    municipio_escopo = _municipio_escopo_designacao(user)
    if municipio_escopo:
        return int(municipio_escopo.id) == int(municipio_id)

    return user.is_superuser or getattr(user, "user_type", None) == User.UserType.ADMIN


@login_required
def listar_designacoes(request):
    municipio_escopo = _municipio_escopo_designacao(request.user)

    if usuario_tem_acesso_total_designacao(request.user):
        designacoes = DesignacaoPreenchimento.objects.select_related(
            "gestor_responsavel",
            "criado_por",
            "municipio",
        )

        if municipio_escopo:
            designacoes = designacoes.filter(municipio=municipio_escopo)
    else:
        designacoes = DesignacaoPreenchimento.objects.select_related(
            "gestor_responsavel",
            "criado_por",
            "municipio",
        ).filter(
            gestor_responsavel=request.user,
            ativa=True,
        )

    status = request.GET.get("status")
    if status:
        designacoes = designacoes.filter(status=status)

    return render(request, "accounts/designations/listar.html", {
        "designacoes": designacoes,
        "status": status,
        "status_choices": DesignacaoPreenchimento.StatusChoices.choices,
        "acesso_total": usuario_tem_acesso_total_designacao(request.user),
        "municipio_escopo": municipio_escopo,
    })


@login_required
def criar_designacao(request):
    if not usuario_tem_acesso_total_designacao(request.user):
        messages.error(request, "Você não tem permissão para criar designações.")
        return redirect("designacoes")

    municipio_escopo = _municipio_escopo_designacao(request.user)

    gestores = User.objects.filter(
        ativo=True,
        user_type=User.UserType.MANAGER,
    ).order_by("nome", "username")

    if municipio_escopo:
        gestores = gestores.filter(municipio=municipio_escopo)

    if usuario_eh_gestor_lider(request.user) and not (request.user.is_superuser or getattr(request.user, "user_type", None) == User.UserType.ADMIN):
        gestores = gestores.filter(criado_por=request.user)
    elif not (request.user.is_superuser or getattr(request.user, "user_type", None) == User.UserType.ADMIN):
        messages.error(request, "Sua conta precisa estar vinculada a um município para criar designações.")
        return redirect("designacoes")

    indicadores = (
        Indicator.objects
        .filter(ativo=True, deletado=False)
        .prefetch_related("categorias", "categorias__plataforma", "categorias__norma_iso")
        .order_by("nome")
        .distinct()
    )
    categorias = Category.objects.all().select_related("plataforma", "norma_iso").order_by("nome")
    plataformas = Platform.objects.all().order_by("nome")

    filtro_nome = request.GET.get("nome", "").strip()
    filtro_categoria = request.GET.get("categoria", "").strip()
    filtro_plataforma = request.GET.get("plataforma", "").strip()

    if filtro_nome:
        indicadores = indicadores.filter(nome__icontains=filtro_nome)
    if filtro_categoria:
        indicadores = indicadores.filter(categorias__id=filtro_categoria)
    if filtro_plataforma:
        indicadores = indicadores.filter(categorias__plataforma_id=filtro_plataforma)

    indicadores = indicadores.distinct()

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        descricao = request.POST.get("descricao")
        gestor_id = request.POST.get("gestor_responsavel")
        prazo = request.POST.get("prazo") or None
        indicadores_ids = request.POST.getlist("indicadores")

        if not titulo or not gestor_id or not indicadores_ids:
            messages.error(request, "Preencha título, gestor responsável e pelo menos um indicador.")
            return redirect("criar_designacao")

        gestor = get_object_or_404(User, id=gestor_id, ativo=True, user_type=User.UserType.MANAGER)

        if not gestor_esta_abaixo_de(request.user, gestor):
            messages.error(request, "Você só pode designar preenchimentos aos gestores criados por você.")
            return redirect("criar_designacao")

        if municipio_escopo:
            if gestor.municipio_id != municipio_escopo.id:
                messages.error(request, "Você só pode designar gestores vinculados ao seu município.")
                return redirect("criar_designacao")
            municipio_designacao = municipio_escopo
        else:
            municipio_designacao = gestor.municipio
            if not municipio_designacao:
                messages.error(request, "O gestor escolhido não possui município vinculado.")
                return redirect("criar_designacao")

        with transaction.atomic():
            designacao = DesignacaoPreenchimento.objects.create(
                titulo=titulo,
                descricao=descricao,
                gestor_responsavel=gestor,
                criado_por=request.user,
                municipio=municipio_designacao,
                prazo=prazo,
                status=DesignacaoPreenchimento.StatusChoices.PENDENTE,
                ativa=True,
            )

            indicadores_selecionados = (
                Indicator.objects
                .filter(id__in=indicadores_ids, ativo=True, deletado=False)
                .distinct()
            )

            for indicador in indicadores_selecionados:
                DesignacaoIndicador.objects.create(
                    designacao=designacao,
                    indicador=indicador,
                    obrigatorio=True,
                )

            AuditLog.objects.create(
                usuario=request.user,
                acao=AuditLog.AcaoChoices.DESIGNACAO_CRIADA,
                objeto_tipo="DesignacaoPreenchimento",
                objeto_id=designacao.id,
                descricao=f"Designação de preenchimento criada para {gestor.username} no município {municipio_designacao}.",
                dados_anteriores=None,
                dados_novos={
                    "campos": {
                        "titulo": designacao.titulo,
                        "gestor_responsavel_id": gestor.id,
                        "municipio_id": municipio_designacao.id,
                        "indicadores_ids": list(indicadores_selecionados.values_list("id", flat=True)),
                    }
                },
                recuperavel=False,
            )

        messages.success(request, "Designação criada com sucesso.")
        return redirect("designacoes")

    return render(request, "accounts/designations/criar.html", {
        "gestores": gestores,
        "municipio_escopo": municipio_escopo,
        "indicadores": indicadores,
        "categorias": categorias,
        "plataformas": plataformas,
        "filtros": {
            "nome": filtro_nome,
            "categoria": filtro_categoria,
            "plataforma": filtro_plataforma,
        },
    })


@login_required
def detalhe_designacao(request, designacao_id):
    designacao = get_object_or_404(
        DesignacaoPreenchimento.objects.select_related(
            "gestor_responsavel",
            "criado_por",
            "municipio",
        ),
        id=designacao_id,
    )

    if usuario_tem_acesso_total_designacao(request.user):
        if not _pode_gerenciar_designacao_do_municipio(request.user, designacao.municipio_id):
            messages.error(request, "Você não tem acesso a designações de outro município.")
            return redirect("designacoes")
    elif designacao.gestor_responsavel_id != request.user.id:
        messages.error(request, "Você não tem acesso a esta designação.")
        return redirect("designacoes")

    itens = designacao.itens.select_related("indicador", "valor_indicador").prefetch_related(
        "indicador__categorias",
        "indicador__categorias__plataforma",
    ).all()

    return render(request, "accounts/designations/detalhe.html", {
        "designacao": designacao,
        "itens": itens,
        "acesso_total": usuario_tem_acesso_total_designacao(request.user),
    })


@login_required
@require_POST
@transaction.atomic
def preencher_indicador_designado(request, item_id):
    """
    Gestor designado preenche um indicador específico.
    Acesso total também pode preencher, desde que a designação pertença ao seu município.
    """
    item = get_object_or_404(
        DesignacaoIndicador.objects.select_related(
            "designacao",
            "indicador",
            "designacao__municipio",
            "designacao__gestor_responsavel",
        ),
        id=item_id,
    )

    designacao = item.designacao

    if usuario_tem_acesso_total_designacao(request.user):
        if not _pode_gerenciar_designacao_do_municipio(request.user, designacao.municipio_id):
            messages.error(request, "Você não pode preencher designações de outro município.")
            return redirect("designacoes")
    elif designacao.gestor_responsavel_id != request.user.id:
        messages.error(request, "Você não pode preencher este indicador.")
        return redirect("designacoes")

    if not designacao.ativa or designacao.status == DesignacaoPreenchimento.StatusChoices.CANCELADA:
        messages.error(request, "Esta designação não está ativa.")
        return redirect("detalhe_designacao", designacao.id)

    valor_numerico = request.POST.get("valor_numerico") or None
    valor_texto = request.POST.get("valor_texto") or None
    fonte = request.POST.get("fonte") or None

    valor_indicador, criado = IndicatorValueYear.objects.get_or_create(
        indicador=item.indicador,
        municipio=designacao.municipio,
    )

    dados_anteriores = {
        "campos": {
            "valor_numerico": valor_indicador.valor_numerico,
            "valor_texto": valor_indicador.valor_texto,
            "fonte": valor_indicador.fonte,
        }
    }

    valor_indicador.valor_numerico = valor_numerico
    valor_indicador.valor_texto = valor_texto
    valor_indicador.fonte = fonte

    if hasattr(valor_indicador, "atualizado_por"):
        valor_indicador.atualizado_por = request.user

    valor_indicador.save()

    item.valor_indicador = valor_indicador
    item.preenchido = True
    item.preenchido_por = request.user
    item.preenchido_em = timezone.now()
    item.save()

    designacao.status = DesignacaoPreenchimento.StatusChoices.EM_ANDAMENTO

    total_itens = designacao.itens.count()
    itens_preenchidos = designacao.itens.filter(preenchido=True).count()

    if total_itens > 0 and total_itens == itens_preenchidos:
        designacao.status = DesignacaoPreenchimento.StatusChoices.CONCLUIDA
        designacao.concluida_em = timezone.now()

    designacao.save()

    AuditLog.objects.create(
        usuario=request.user,
        acao=AuditLog.AcaoChoices.PREENCHIMENTO_DESIGNADO,
        objeto_tipo="IndicatorValueYear",
        objeto_id=valor_indicador.id,
        descricao=f"Preenchimento designado: {item.indicador.nome} para {designacao.municipio}.",
        dados_anteriores=dados_anteriores,
        dados_novos={
            "campos": {
                "valor_numerico": valor_indicador.valor_numerico,
                "valor_texto": valor_indicador.valor_texto,
                "fonte": valor_indicador.fonte,
                "designacao_id": designacao.id,
                "item_designacao_id": item.id,
            }
        },
        recuperavel=True,
    )

    try:
        recalcular_ranking_municipio_categoria(designacao.municipio, item.indicador)
    except Exception:
        pass

    messages.success(request, "Indicador preenchido com sucesso.")
    return redirect("detalhe_designacao", designacao.id)


@login_required
@require_POST
def cancelar_designacao(request, designacao_id):
    designacao = get_object_or_404(DesignacaoPreenchimento, id=designacao_id)

    if not _pode_gerenciar_designacao_do_municipio(request.user, designacao.municipio_id):
        messages.error(request, "Você não tem permissão para cancelar esta designação.")
        return redirect("designacoes")

    designacao.status = DesignacaoPreenchimento.StatusChoices.CANCELADA
    designacao.ativa = False
    designacao.save()

    AuditLog.objects.create(
        usuario=request.user,
        acao=AuditLog.AcaoChoices.DESIGNACAO_CANCELADA,
        objeto_tipo="DesignacaoPreenchimento",
        objeto_id=designacao.id,
        descricao=f"Designação cancelada: {designacao.titulo}.",
        recuperavel=False,
    )

    messages.success(request, "Designação cancelada com sucesso.")
    return redirect("designacoes")