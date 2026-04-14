from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .forms import RegisterForm, LoginForm
from .models import User, Platform, Norm, ISO37120Indicator, ISO37122Indicator, ISO37123Indicator, ISO37125Indicator, Municipality, YearReference
import json
import os
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
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                # 1. Autentica primeiro para garantir que a senha (mesmo temporária) está correta
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    # 2. Se a senha for temporária, não loga ainda. Manda para a troca.
                    if user.senha_temporaria_ativa:
                        request.session['temp_user_id'] = user.id
                        return redirect('first_access') 

                    # 3. Se não for temporária, segue o login normal
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
                # CORREÇÃO AQUI: Endereço correto do Gmail
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(email_user, email_pass)
                    smtp.send_message(msg)
                return True
            except Exception as e:
                print(f"Erro ao enviar: {e}")
                return False

        if _send_email_token(email_usuario, codigo_gerado):
            messages.success(request, "Código enviado para o seu e-mail!")
            # CORREÇÃO AQUI: Nome da URL definido no path()
            return redirect('verify_code') 
        else:
            messages.error(request, "Erro ao enviar e-mail. Tente novamente.")

    return render(request, 'accounts/reset-password.html')


@require_http_methods(["GET", "POST"])
def verify_and_change_password(request):
    # Recupera os dados que guardamos na sessão na função anterior
    username = request.session.get('reset_username')
    codigo_correto = request.session.get('reset_code')
    email_alvo = request.session.get('reset_email')

    if request.method == "POST":
        codigo_digitado = request.POST.get('codigo')
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        # 1. Validações básicas
        if codigo_digitado != codigo_correto:
            messages.error(request, "Código de verificação incorreto!")
        elif nova_senha != confirmar_senha:
            messages.error(request, "As senhas não coincidem!")
        else:
            # 2. Se tudo OK, busca o usuário e altera a senha
            try:
                user = User.objects.get(email=email_alvo, username = username)
                user.set_password(nova_senha)
                user.save()
                
                # 3. Limpa a sessão para segurança
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
    norms = Norm.objects.all()
    return render(request, 'accounts/normas.html', {'norms': norms})

@login_required
def plataformas(request):
    platforms = Platform.objects.all()
    return render(request, 'accounts/plataformas.html', {'platforms': platforms})

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

@login_required
@require_http_methods(["GET"])
def csc(request):
    context = {
        'dimensoes': MOCK_DATA['dimensoes'],
        'username': request.user.username
    }
    return render(request, 'accounts/plataformas/csc.html', context)

@login_required
@require_http_methods(["GET"])
def inteligente(request):
    context = {
        'dimensoes': MOCK_DATA['dimensoes'],
        'username': request.user.username
    }
    return render(request, 'accounts/plataformas/inteligente.html', context)

@login_required
@require_http_methods(["GET"])
def iso37120(request):
    context = {
        'dimensoes': MOCK_DATA['dimensoes'],
        'username': request.user.username
    }
    return render(request, 'accounts/normas/iso37120.html', context)

# API to save/update ISO37120 indicator data
@csrf_exempt
@login_required
@manager_required
def save_iso37120_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            categoria = data.get('categoria')
            nome_indicador = data.get('nome_indicador')
            tipo = data.get('tipo')
            ods = data.get('ods')
            unidade = data.get('unidade')
            cidade = data.get('cidade', 'Londrina')
            estado = data.get('estado', 'PR')

            # Data fields
            dado_2022 = data.get('dado_2022')
            dado_2023 = data.get('dado_2023')
            dado_2024 = data.get('dado_2024')
            dado_2025 = data.get('dado_2025')

            # Source fields
            fonte_2022 = data.get('fonte_2022')
            fonte_2023 = data.get('fonte_2023')
            fonte_2024 = data.get('fonte_2024')
            fonte_2025 = data.get('fonte_2025')

            # Create or update indicator
            indicator, created = ISO37120Indicator.objects.get_or_create(
                nome_indicador=nome_indicador,
                cidade=cidade,
                estado=estado,
                defaults={
                    'categoria': categoria,
                    'tipo': tipo,
                    'ods': ods,
                    'unidade': unidade,
                    'dado_2022': dado_2022,
                    'dado_2023': dado_2023,
                    'dado_2024': dado_2024,
                    'dado_2025': dado_2025,
                    'fonte_2022': fonte_2022,
                    'fonte_2023': fonte_2023,
                    'fonte_2024': fonte_2024,
                    'fonte_2025': fonte_2025,
                }
            )

            if not created:
                # Update existing indicator - only update provided fields
                indicator.categoria = categoria
                indicator.tipo = tipo
                indicator.ods = ods
                indicator.unidade = unidade

                # Only update data fields if they are provided (not None)
                if dado_2022 is not None:
                    indicator.dado_2022 = dado_2022
                if dado_2023 is not None:
                    indicator.dado_2023 = dado_2023
                if dado_2024 is not None:
                    indicator.dado_2024 = dado_2024
                if dado_2025 is not None:
                    indicator.dado_2025 = dado_2025

                # Only update source fields if they are provided (not None)
                if fonte_2022 is not None:
                    indicator.fonte_2022 = fonte_2022
                if fonte_2023 is not None:
                    indicator.fonte_2023 = fonte_2023
                if fonte_2024 is not None:
                    indicator.fonte_2024 = fonte_2024
                if fonte_2025 is not None:
                    indicator.fonte_2025 = fonte_2025

                indicator.save()

            return JsonResponse({
                'success': True,
                'message': 'Dados salvos com sucesso',
                'id': indicator.id
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método não permitido'})

# API to get ISO37120 indicator data
@login_required
def get_iso37120_data(request):
    try:
        cidade = request.GET.get('cidade', 'Londrina')
        estado = request.GET.get('estado', 'PR')

        indicators = ISO37120Indicator.objects.filter(
            cidade=cidade,
            estado=estado
        )

        # Build response with anexo URLs
        data = []
        for indicator in indicators:
            indicator_data = {
                'id': indicator.id,
                'categoria': indicator.categoria,
                'nome_indicador': indicator.nome_indicador,
                'tipo': indicator.tipo,
                'ods': indicator.ods,
                'unidade': indicator.unidade,
                'dado_2022': indicator.dado_2022,
                'dado_2023': indicator.dado_2023,
                'dado_2024': indicator.dado_2024,
                'dado_2025': indicator.dado_2025,
                'fonte_2022': indicator.fonte_2022,
                'fonte_2023': indicator.fonte_2023,
                'fonte_2024': indicator.fonte_2024,
                'fonte_2025': indicator.fonte_2025,
                'anexo_2022': indicator.anexo_2022.url if indicator.anexo_2022 else None,
                'anexo_2023': indicator.anexo_2023.url if indicator.anexo_2023 else None,
                'anexo_2024': indicator.anexo_2024.url if indicator.anexo_2024 else None,
                'anexo_2025': indicator.anexo_2025.url if indicator.anexo_2025 else None,
                'cidade': indicator.cidade,
                'estado': indicator.estado,
                'created_at': indicator.created_at.isoformat() if indicator.created_at else None,
                'updated_at': indicator.updated_at.isoformat() if indicator.updated_at else None,
            }
            data.append(indicator_data)

        return JsonResponse({
            'success': True,
            'data': data
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# API to update specific field (for edit functionality)
@csrf_exempt
@login_required
@manager_required
def update_iso37120_field(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            indicator_id = data.get('indicator_id')
            field_name = data.get('field_name')
            field_value = data.get('field_value')

            indicator = ISO37120Indicator.objects.get(id=indicator_id)
            setattr(indicator, field_name, field_value)
            indicator.save()

            return JsonResponse({
                'success': True,
                'message': 'Campo atualizado com sucesso'
            })

        except ISO37120Indicator.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Indicador não encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método não permitido'})

# API to upload PDF attachment for ISO37120 indicator
@csrf_exempt
@login_required
@manager_required
def upload_iso37120_anexo(request):
    if request.method == 'POST':
        try:
            nome_indicador = request.POST.get('nome_indicador') or request.POST.get('indicator_id')
            year = request.POST.get('year')
            anexo_file = request.FILES.get('anexo')
            categoria = request.POST.get('categoria', '')
            tipo = request.POST.get('tipo', 'core')
            ods = request.POST.get('ods', '')
            unidade = request.POST.get('unidade', '')
            cidade = request.POST.get('cidade', 'Londrina')
            estado = request.POST.get('estado', 'PR')

            if not nome_indicador or not year or not anexo_file:
                return JsonResponse({'success': False, 'message': 'Parâmetros obrigatórios ausentes'})

            # Validate file type
            if not anexo_file.name.lower().endswith('.pdf'):
                return JsonResponse({'success': False, 'message': 'Apenas arquivos PDF são permitidos'})

            # Validate file size (max 10MB)
            if anexo_file.size > 10 * 1024 * 1024:
                return JsonResponse({'success': False, 'message': 'Arquivo muito grande. Máximo permitido: 10MB'})

            # Get or create indicator by name
            indicator, created = ISO37120Indicator.objects.get_or_create(
                nome_indicador=nome_indicador,
                cidade=cidade,
                estado=estado,
                defaults={
                    'categoria': categoria,
                    'tipo': tipo,
                    'ods': ods,
                    'unidade': unidade,
                }
            )

            # Get the appropriate field name based on year
            anexo_field = f'anexo_{year}'

            # Delete old file if exists
            old_file = getattr(indicator, anexo_field)
            if old_file:
                old_file.delete(save=False)

            # Save new file
            setattr(indicator, anexo_field, anexo_file)
            indicator.save()

            return JsonResponse({
                'success': True,
                'message': 'Anexo enviado com sucesso',
                'anexo_url': getattr(indicator, anexo_field).url if getattr(indicator, anexo_field) else None
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método não permitido'})

# API to delete PDF attachment for ISO37120 indicator
@csrf_exempt
@login_required
@manager_required
def delete_iso37120_anexo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nome_indicador = data.get('nome_indicador') or data.get('indicator_id')
            year = data.get('year')
            cidade = data.get('cidade', 'Londrina')
            estado = data.get('estado', 'PR')

            if not nome_indicador or not year:
                return JsonResponse({'success': False, 'message': 'Parâmetros obrigatórios ausentes'})

            indicator = ISO37120Indicator.objects.get(
                nome_indicador=nome_indicador,
                cidade=cidade,
                estado=estado
            )

            # Get the appropriate field name based on year
            anexo_field = f'anexo_{year}'

            # Delete file if exists
            old_file = getattr(indicator, anexo_field)
            if old_file:
                old_file.delete(save=False)
                setattr(indicator, anexo_field, None)
                indicator.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Anexo removido com sucesso'
                })
            else:
                return JsonResponse({'success': False, 'message': 'Nenhum anexo encontrado'})

        except ISO37120Indicator.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Indicador não encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método não permitido'})





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

# API to generate a report (simulated)
@require_http_methods(["GET"])
def gerar_relatorio(request, dimensao_id):
    # Check if user is logged in via API
    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Não autorizado'}, status=401)
    
    # Check if dimension exists
    if dimensao_id not in MOCK_DATA['indicadores']:
        return JsonResponse({'error': 'Dimensão não encontrada'}, status=404)
    
    # In a real scenario, you would generate a PDF or other report format
    # For now, we just return the data in a different format
    
    dimensao = next((d for d in MOCK_DATA['dimensoes'] if d['id'] == dimensao_id), None)
    indicadores = MOCK_DATA['indicadores'][dimensao_id]
    
    relatorio = {
        'titulo': f'Relatório de {dimensao["nome"]}',
        'data_geracao': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
        'dimensao': dimensao,
        'indicadores': indicadores,
        'total_indicadores': len(indicadores),
        'usuario': request.session.get('username', '')
    }
    
    return JsonResponse(relatorio)

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
    

    # Em accounts/views.py
def modal_dimensoes(request):
    return render(request, 'screens/modals-dimensoes.html')

def modal_indicadores(request):
    return render(request, 'screens/modals-indicadores.html')














# Admin User Management Views
@login_required
@admin_required
def admin_menu(request):
    """Menu de administração - apenas para administradores"""
    context = {
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'accounts/admin/menu.html', context)


@login_required
@admin_required
def list_years(request):
    """Listar todos os anos cadastrados do sistema"""
    years_list = YearReference.objects.all().order_by('-ano')
    
    context = {
        'years': years_list,
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'accounts/admin/list_years.html', context)


@login_required
@admin_required
def add_year(request):
    if request.method == 'POST':
        try:
            last_year_obj = YearReference.objects.order_by('-ano').first()
            novo_ano = (last_year_obj.ano + 1) if last_year_obj else 2022

            YearReference.objects.create(
                ano=novo_ano,
                ativo=True
            )
            
            messages.success(request, f"Ano {novo_ano} adicionado com sucesso!")
            return redirect('list_years')
            
        except Exception as e:
            messages.error(request, f"Erro ao criar ano: {str(e)}")
            return redirect('add_year')

    return render(request, 'accounts/admin/add_year.html')


@login_required
@admin_required
def change_year_status(request, year_id):
    if request.method == 'POST':
        try:
            year_to_change = get_object_or_404(YearReference, id=year_id)
            
            new_status_raw = request.POST.get('ativo')

            if new_status_raw not in ['True', 'False']:
                return JsonResponse({'success': False, 'message': 'Status inválido'})

            is_active = new_status_raw == 'True'
            
            year_to_change.ativo = is_active
            year_to_change.save()

            status_text = 'Ativo' if is_active else 'Desativado'

            return JsonResponse({
                'success': True,
                'message': f'Status do ano {year_to_change.ano} alterado para {status_text}'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)


@login_required
@admin_required
def list_users(request):
    """Listar todos os usuários do sistema"""
    users = User.objects.all().order_by('-created_at')
    context = {
        'users': users,
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'accounts/admin/list_users.html', context)


@login_required
@admin_required
def add_user(request):
    """Adicionar novo usuário"""

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

            # Validar campos obrigatórios
            if not all([nome, username, email, cpf, cidade, categoria]):
                messages.error(request, 'Todos os campos são obrigatórios')
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
                user_type=categoria
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
    }
    return render(request, 'accounts/admin/add_user.html', context)


@login_required
@admin_required
def edit_user(request, user_id):
    """Editar usuário existente"""
    user_to_edit = get_object_or_404(User, id=user_id)

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
            cidade = Municipality.objects.get(id=request.POST.get('cidade'))
            categoria = request.POST.get('categoria')

            # Validar campos obrigatórios
            if not all([nome, username, email, cpf, cidade, categoria]):
                messages.error(request, 'Todos os campos são obrigatórios')
                return redirect('edit_user', user_id=user_id)

            # Verificar se o email já existe (exceto para o usuário atual)
            if User.objects.filter(email=email).exclude(id=user_id).exists():
                messages.error(request, 'Já existe um usuário com este email')
                return redirect('edit_user', user_id=user_id)
            
            if User.objects.filter(cpf=cpf).exists():
                messages.error(request, 'Já existe um usuário com este CPF')
                return redirect('add_user')
            
            if not _cpf_valido(cpf):
                messages.error(request, 'O CPF informado é inválido.')
                return redirect('add_user')

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
    }
    return render(request, 'accounts/admin/edit_user.html', context)


@login_required
@admin_required
def delete_user(request, user_id):
    """Excluir usuário"""
    if request.method == 'POST':
        try:
            user_to_delete = get_object_or_404(User, id=user_id)

            # Não permitir que o admin delete a si mesmo
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
@admin_required
def change_user_role(request, user_id):
    """Modificar privilégios do usuário"""
    if request.method == 'POST':
        try:
            user_to_change = get_object_or_404(User, id=user_id)
            new_role = request.POST.get('user_type')

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

