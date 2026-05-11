from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from accounts.models import Indicator, IndicatorCategory, Platform, YearReference, NormISO, IndicatorValueYear, Category, EvidencePDF, User, Municipality, Certification, RankingISOCategoriaView, MunicipalityRanking, AuditLog, PlatformGoalReference
import json
import ast
import os
from decimal import Decimal
from collections import defaultdict
from django.db import connection
from django.db.models import F, Q
from django.db.utils import DatabaseError
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from accounts.decorators import admin_required, manager_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from django.utils import timezone
import os


@login_required
@admin_required
def list_norms(request):
    """Listar todos as normas ISO cadastrados do sistema"""

    norms_list = NormISO.objects.all().order_by('codigo_norma')
    years = YearReference.objects.all().filter(ativo=True).order_by('ano')

    context = {
        'years':years,
        'norms_list': norms_list,
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin/norms/list_norms.html', context)


@login_required
@admin_required
def add_norm(request):
     """Adicionar nova norma"""
     
     if request.method == 'POST':
        try:
            # Pegar dados do formulário
            ano = YearReference.objects.get(ano=request.POST.get('ano_referencia'))
            codigo_norma = request.POST.get('codigo_norma')
            descricao = request.POST.get('descricao')
            ano_referencia = ano
            

            # Validar campos obrigatórios
            if not all([codigo_norma, descricao, ano_referencia]):
                messages.error(request, 'Todos os campos são obrigatórios')
                return redirect('add_norm')
            
            # Verificar se uma norma já existe nesse ano
            if NormISO.objects.filter(codigo_norma=codigo_norma, ano_referencia=ano_referencia).exists():
                messages.error(request, 'Já existe uma norma com esse codigo nesse ano.')
                return redirect('add_norm')

            # Criar novo usuário (user_type será igual a categoria)
            norm = NormISO.objects.create(
                codigo_norma=codigo_norma,
                descricao=descricao,
                ano_referencia=ano_referencia
            )

            messages.success(request, f'Norma {codigo_norma} criado com sucesso!')
            return redirect('list_norms')

        except Exception as e:
            messages.error(request, f'Erro ao criar norma: {str(e)}')
            return redirect('add_norm')
        
     ano_pre_selecionado = request.GET.get('ano')
        
     context = {
        'username': request.user.username,
        'user_type': request.user.user_type,
        'ano_pre_selecionado': ano_pre_selecionado,
     }
     return render(request, 'admin/norms/add_norm.html', context)


@login_required
@admin_required
def edit_norm(request, norm_id):
    """Editar usuário existente"""
    norm_to_edit = get_object_or_404(NormISO, id=norm_id)

    if request.method == 'POST':
        try:
            # Pegar dados do formulário
            codigo_norma = request.POST.get('codigo_norma')
            descricao = request.POST.get('descricao')
            ano_referencia = norm_to_edit.ano_referencia

            # Validar campos obrigatórios
            if not all([codigo_norma, descricao, ano_referencia]):
                messages.error(request, 'Todos os campos são obrigatórios')
                return redirect('edit_norm', norm_id=norm_id)
            
            # Valida se existe outra norma com id diferente e mesmo codigo
            if NormISO.objects.filter(codigo_norma=codigo_norma).exclude(id=norm_to_edit.id).exists():
                messages.error(request, 'Já existe uma norma com esse código.')
                return redirect('edit_norm', norm_id=norm_id)

            # Atualizar dados do usuário (user_type será igual a categoria)
            norm_to_edit.codigo_norma = codigo_norma
            norm_to_edit.descricao = descricao
            norm_to_edit.ano_referencia = ano_referencia

            norm_to_edit.save()

            messages.success(request, f'Norma {codigo_norma} atualizada com sucesso!')
            return redirect('list_norms')

        except Exception as e:
            messages.error(request, f'Erro ao atualizar norma: {str(e)}')
            return redirect('edit_norm', norm_id=norm_id)

    context = {
        'norm_to_edit': norm_to_edit,
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin/norms/edit_norm.html', context)


@login_required
@admin_required
def delete_norm(request, norm_id):
    """Excluir norma"""
    if request.method == 'POST':
        try:

            norm_to_delete = get_object_or_404(NormISO, id=norm_id)
            norm = norm_to_delete.codigo_norma
            certifications = Certification.objects.filter(norma_iso=norm_to_delete)
            categories = Category.objects.filter(norma_iso=norm_to_delete)
            indicators = Indicator.objects.filter(categorias__in=categories)
            values_indicators = IndicatorValueYear.objects.filter(indicador__in=indicators)

            values_indicators.delete()
            indicators.delete()
            categories.delete()
            certifications.delete()
            
            norm_to_delete.delete()

            return JsonResponse({
                'success': True,
                'message': f'Norma {norm} excluída com sucesso'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao excluir norma: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método não permitido'})


def check_related_records(request, norm_id):
    exists_categories = Category.objects.filter(norma_iso=norm_id).exists()
    exists_indicators = Indicator.objects.filter(categorias__norma_iso_id=norm_id).exists()
    exists_indicator_values = IndicatorValueYear.objects.filter(indicador__categorias__norma_iso=norm_id).exists()
    return JsonResponse({
        'has_categories': exists_categories,
        'has_indicators': exists_indicators,
        'exists_indicator_values': exists_indicator_values
    })


@login_required
@admin_required
def list_platforms(request):
    """Listar todos as plataformas cadastrados do sistema"""

    platforms_list = Platform.objects.all().order_by('nome')
    years = YearReference.objects.all().filter(ativo=True).order_by('ano')

    context = {
        'years':years,
        'platforms_list': platforms_list,
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin/platforms/list_platforms.html', context)


@login_required
@admin_required
def add_platform(request):
    """Adicionar nova plataforma"""
    if request.method == 'POST':
        try:
            # Pegar dados do formulário
            nome = request.POST.get('nome')     
            ano_referencia = request.POST.get('ano_referencia')   

            ano = get_object_or_404(YearReference, ano=ano_referencia)    

            # Validar campos obrigatórios
            if not all([nome, ano_referencia]):
                messages.error(request, 'Todos os campos são obrigatórios')
                return redirect('add_platform')
            
            # Verificar se uma plataforma já existe com esse nome
            if Platform.objects.filter(nome=nome).exists():
                messages.error(request, 'Já existe uma plataforma com esse nome.')
                return redirect('add_platform')

            # Criar nova plataforma
            Platform.objects.create(
                nome=nome,
                ano_referencia=ano,
            )

            messages.success(request, f'Plataforma {nome} criada com sucesso!')
            return redirect('list_platforms')

        except Exception as e:
            messages.error(request, f'Erro ao criar plataforma: {str(e)}')
            return redirect('add_platform')
        
    ano_pre_selecionado = request.GET.get('ano')
        
    context = {
        'username': request.user.username,
        'user_type': request.user.user_type,
        'ano_pre_selecionado': ano_pre_selecionado,
     }
    return render(request, 'admin/platforms/add_platform.html', context)


@login_required
@admin_required
def edit_platform(request, plataform_id):
    """Editar plataforma existente"""
    platform_to_edit = get_object_or_404(Platform, id=plataform_id)

    if request.method == 'POST':
        try:
            # Pegar dados do formulário
            nome = request.POST.get('nome')

            # Validar campos obrigatórios
            if not all([nome]):
                messages.error(request, 'Todos os campos são obrigatórios')
                return redirect('edit_platform', plataform_id=plataform_id)
            
            # Valida se existe outra plataforma com id diferente e mesmo nome
            if Platform.objects.filter(nome=nome).exclude(id=platform_to_edit.id).exists():
                messages.error(request, 'Já existe uma plataforma com esse nome.')
                return redirect('edit_platform', plataform_id=plataform_id)

            # Atualizar dados da plataforma
            platform_to_edit.nome = nome

            platform_to_edit.save()

            messages.success(request, f'Plataforma {nome} atualizada com sucesso!')
            return redirect('list_platforms')

        except Exception as e:
            messages.error(request, f'Erro ao atualizar plataforma: {str(e)}')
            return redirect('edit_platform', plataform_id=plataform_id)

    context = {
        'platform_to_edit': platform_to_edit,
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin/platforms/edit_platform.html', context)


@login_required
@admin_required
def delete_platform(request, plataform_id):
    """Excluir plataforma"""
    if request.method == 'POST':
        try:
            platform_to_delete = get_object_or_404(Platform, id=plataform_id)
            platform_name = platform_to_delete.nome

            platform_to_delete.delete()

            return JsonResponse({
                'success': True,
                'message': f'Plataforma {platform_name} excluída com sucesso'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao excluir plataforma: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método não permitido'})

def check_related_records_platform(request, plataform_id):
    exists_categories = Category.objects.filter(plataform_id=plataform_id).exists()
    exists_indicators = Indicator.objects.filter(categorias__plataform_id=plataform_id).exists()
    exists_indicator_values = IndicatorValueYear.objects.filter(indicador__categorias__plataform_id=plataform_id).exists()
    return JsonResponse({
        'has_categories': exists_categories,
        'has_indicators': exists_indicators,
        'exists_indicator_values': exists_indicator_values
    })






@login_required
@admin_required
def list_indicators(request, norm_id=None):
    """
    Lista indicadores com filtros por norma OU plataforma, categoria, tipo e busca.
    """
    years = YearReference.objects.filter(ativo=True).order_by('-ano')
    norms = NormISO.objects.select_related('ano_referencia').order_by('-ano_referencia__ano', 'codigo_norma')
    platforms = Platform.objects.select_related('ano_referencia').order_by('-ano_referencia__ano', 'nome')

    contexto_tipo = request.GET.get('contexto_tipo') or 'norma'
    norma_id = request.GET.get('norma_id') or norm_id
    plataforma_id = request.GET.get('plataforma_id')
    categoria_id = request.GET.get('categoria_id')
    tipo = request.GET.get('tipo')
    busca = request.GET.get('busca')

    selected_norm = None
    selected_platform = None

    if contexto_tipo == 'plataforma':
        if plataforma_id:
            selected_platform = get_object_or_404(Platform, id=plataforma_id)
        else:
            selected_platform = platforms.first()
        categories = Category.objects.filter(plataforma=selected_platform).order_by('nome') if selected_platform else Category.objects.none()
    else:
        contexto_tipo = 'norma'
        if norma_id:
            selected_norm = get_object_or_404(NormISO, id=norma_id)
        else:
            selected_norm = norms.first()
        categories = Category.objects.filter(norma_iso=selected_norm).order_by('nome') if selected_norm else Category.objects.none()

    indicators = (
        Indicator.objects
        .filter(categorias__in=categories, deletado=False)
        .prefetch_related('categorias', 'categorias__norma_iso', 'categorias__plataforma')
        .distinct()
        .order_by('nome')
    )

    if categoria_id:
        indicators = indicators.filter(categorias__id=categoria_id).distinct()

    if tipo:
        indicators = indicators.filter(tipo=tipo)

    if busca:
        indicators = indicators.filter(
            Q(nome__icontains=busca) |
            Q(descricao__icontains=busca) |
            Q(categorias__nome__icontains=busca)
        ).distinct()

    context = {
        'categories': categories,
        'indicators': indicators,
        'years': years,
        'norms': norms,
        'platforms': platforms,
        'selected_norm': selected_norm,
        'selected_platform': selected_platform,
        'contexto_tipo': contexto_tipo,
        'categoria_id': str(categoria_id or ''),
        'tipo_filtro': tipo or '',
        'busca': busca or '',
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin/indicators/list_indicators.html', context)


@login_required
@admin_required
def indicator_categories_by_context(request):
    """API simples para carregar categorias após selecionar Norma ou Plataforma."""
    contexto_tipo = request.GET.get('contexto_tipo')
    contexto_id = request.GET.get('contexto_id')

    categories = Category.objects.none()

    if contexto_tipo == 'norma' and contexto_id:
        categories = Category.objects.filter(norma_iso_id=contexto_id).order_by('nome')
    elif contexto_tipo == 'plataforma' and contexto_id:
        categories = Category.objects.filter(plataforma_id=contexto_id).order_by('nome')

    return JsonResponse({
        'success': True,
        'categories': [
            {
                'id': category.id,
                'nome': category.nome,
                'descricao': category.descricao or '',
            }
            for category in categories
        ]
    })


def _get_categoria_from_context(contexto_tipo, contexto_id, categoria_id):
    if contexto_tipo == 'plataforma':
        return get_object_or_404(Category, id=categoria_id, plataforma_id=contexto_id)
    return get_object_or_404(Category, id=categoria_id, norma_iso_id=contexto_id)


def _redirect_list_indicators_from_category(categoria):
    if categoria.plataforma_id:
        return redirect(f"{reverse('list_indicators')}?contexto_tipo=plataforma&plataforma_id={categoria.plataforma_id}")
    return redirect(f"{reverse('list_indicators')}?contexto_tipo=norma&norma_id={categoria.norma_iso_id}")


def _decimal_or_none(value):
    if value in [None, '']:
        return None
    try:
        return Decimal(str(value).replace(',', '.'))
    except Exception:
        return None


def _category_ids_from_indicator_form(request):
    """
    Lê vínculos do formulário de indicador:
    - uma norma ISO opcional, com sua categoria própria;
    - zero, uma ou várias plataformas, cada uma com sua categoria própria.
    """
    ids = []
    norm_category_id = request.POST.get('norm_category_id')
    if norm_category_id:
        ids.append(norm_category_id)

    for platform_id in request.POST.getlist('platform_ids'):
        # Cada plataforma pode vincular uma ou várias categorias ao mesmo indicador.
        # Aceita tanto o nome antigo (platform_category_<id>) quanto um alias plural.
        category_values = request.POST.getlist(f'platform_category_{platform_id}')
        category_values += request.POST.getlist(f'platform_categories_{platform_id}')
        for category_id in category_values:
            if category_id:
                ids.append(category_id)

    # Mantém compatibilidade com o formulário antigo.
    legacy_category_id = request.POST.get('categoria_id')
    if not ids and legacy_category_id:
        ids.append(legacy_category_id)

    unique_ids = []
    for item in ids:
        if item and item not in unique_ids:
            unique_ids.append(item)
    return unique_ids


def _selected_contexts_for_indicator(indicator=None):
    """Monta dados usados nos templates de adição/edição."""
    norm_category = None
    platform_category_map = {}
    if indicator:
        for category in indicator.categorias.select_related('norma_iso', 'plataforma').all():
            if category.norma_iso_id and not norm_category:
                norm_category = category
            if category.plataforma_id:
                platform_category_map.setdefault(str(category.plataforma_id), []).append(category.id)
    return norm_category, platform_category_map





def _coerce_predefined_label(value):
    """Retorna apenas o label de opções predefinidas, mesmo se veio como dict/string de dict."""
    if value in [None, '']:
        return ''
    if isinstance(value, dict):
        return str(value.get('label') or value.get('nome') or value.get('value') or value.get('valor') or '').strip()
    text = str(value).strip()
    if not text:
        return ''
    if (text.startswith('{') and text.endswith('}')) or (text.startswith('[') and text.endswith(']')):
        parsed = None
        try:
            parsed = json.loads(text)
        except Exception:
            try:
                parsed = ast.literal_eval(text)
            except Exception:
                parsed = None
        if isinstance(parsed, dict):
            return _coerce_predefined_label(parsed)
        if isinstance(parsed, list) and parsed:
            return _coerce_predefined_label(parsed[0])
    return text

def _normalize_predefined_options(options):
    """Normaliza opções antigas e novas para [{'label': str, 'score': str}]."""
    normalized = []
    if not options:
        return normalized
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except Exception:
            options = [options]
    for option in options:
        if isinstance(option, dict):
            label = _coerce_predefined_label(option)
            score = option.get('score') if option.get('score') is not None else option.get('pontuacao')
        else:
            label = _coerce_predefined_label(option)
            score = None
        if not label:
            continue
        normalized.append({
            'label': label,
            'score': _format_number_clean(score) if score not in [None, ''] else '',
        })
    return normalized


def _predefined_option_score(indicator, selected_label):
    selected_label = _coerce_predefined_label(selected_label)
    if not selected_label:
        return Decimal('0')
    for option in _normalize_predefined_options(getattr(indicator, 'opcoes_predefinidas', None)):
        if option['label'] == selected_label:
            try:
                return Decimal(str(option.get('score') or 0).replace(',', '.'))
            except Exception:
                return Decimal('0')
    return Decimal('0')


def _normalize_options_json_for_form(options):
    return json.dumps(_normalize_predefined_options(options), ensure_ascii=False)


def _clean_predefined_options_from_json(opcoes_json):
    try:
        raw_options = json.loads(opcoes_json or '[]')
    except Exception:
        raise ValueError('JSON de opções predefinidas inválido.')
    options = _normalize_predefined_options(raw_options)
    if not options:
        raise ValueError('Adicione pelo menos uma opção predefinida.')
    labels = set()
    cleaned = []
    for option in options:
        label = option.get('label', '').strip()
        score = option.get('score', '')
        if not label:
            raise ValueError('Todas as opções precisam de um nome.')
        if label in labels:
            raise ValueError(f'A opção "{label}" foi adicionada mais de uma vez.')
        labels.add(label)
        if score in [None, '']:
            raise ValueError(f'Informe a pontuação da opção "{label}".')
        try:
            score_decimal = Decimal(str(score).replace(',', '.'))
        except Exception:
            raise ValueError(f'A pontuação da opção "{label}" precisa ser numérica.')
        if score_decimal < 0 or score_decimal > 100:
            raise ValueError(f'A pontuação da opção "{label}" deve estar entre 0 e 100.')
        cleaned.append({'label': label, 'score': _format_number_clean(score_decimal)})
    return cleaned

def _indicator_numeric_value(value_obj):
    if not value_obj:
        return None
    if value_obj.valor_numerico is not None:
        return Decimal(value_obj.valor_numerico)
    if value_obj.valor_texto not in [None, '']:
        try:
            return Decimal(str(value_obj.valor_texto).replace(',', '.'))
        except Exception:
            return None
    return None



def _format_number_clean(value):
    """Exibe números sem zeros decimais desnecessários."""
    if value is None or value == '':
        return ''
    try:
        decimal_value = Decimal(str(value))
        if decimal_value == decimal_value.to_integral():
            return str(decimal_value.quantize(Decimal('1')))
        return format(decimal_value.normalize(), 'f').rstrip('0').rstrip('.')
    except Exception:
        return str(value)


def _to_float(value, default=0.0):
    """Converte Decimal/int/str formatada em número para cálculos e round()."""
    if value is None or value == '':
        return default
    try:
        if isinstance(value, str):
            value = value.strip().replace('.', '').replace(',', '.') if ',' in value else value.strip()
        return float(value)
    except Exception:
        return default

def calcular_nota_indicador(indicator, value_obj):
    """
    Calcula a nota 0-100 no padrão CSC simplificado.
    Indicadores categóricos usam a pontuação da opção selecionada.
    Indicadores numéricos usam mínimo, máximo e direção de melhoria.
    """
    if getattr(indicator, 'opcoes_predefinidas', None):
        selected = _coerce_predefined_label(getattr(value_obj, 'valor_texto', None) if value_obj else None)
        nota_opcao = _predefined_option_score(indicator, selected)
        if nota_opcao < 0:
            return Decimal('0')
        if nota_opcao > 100:
            return Decimal('100')
        return nota_opcao.quantize(Decimal('0.01'))

    valor = _indicator_numeric_value(value_obj)
    minimo = indicator.valor_referencia_minimo
    maximo = indicator.valor_referencia_maximo
    if valor is None or minimo is None or maximo is None or maximo == minimo:
        return Decimal('0')

    minimo = Decimal(minimo)
    maximo = Decimal(maximo)
    if indicator.direcao_melhoria == -1:
        nota = ((maximo - valor) / (maximo - minimo)) * Decimal('100')
    else:
        nota = ((valor - minimo) / (maximo - minimo)) * Decimal('100')

    if nota < 0:
        return Decimal('0')
    if nota > 100:
        return Decimal('100')
    return nota.quantize(Decimal('0.01'))


@login_required
@admin_required
def add_indicator(request, norm_id=None):
    """
    Adiciona um indicador que pode estar vinculado a:
    - uma norma ISO opcional, com categoria da própria norma;
    - nenhuma, uma ou várias plataformas, cada uma com sua própria categoria.
    """
    norms = NormISO.objects.select_related('ano_referencia').order_by('-ano_referencia__ano', 'codigo_norma')
    platforms = Platform.objects.select_related('ano_referencia').order_by('-ano_referencia__ano', 'nome')

    selected_norm_id = request.POST.get('norm_id') or request.GET.get('norm_id') or norm_id or ''
    selected_platform_ids = request.POST.getlist('platform_ids') or request.GET.getlist('platform_ids')

    norm_categories = Category.objects.filter(norma_iso_id=selected_norm_id).order_by('nome') if selected_norm_id else Category.objects.none()
    platform_categories_by_id = {
        str(platform.id): list(Category.objects.filter(plataforma=platform).order_by('nome'))
        for platform in platforms
    }

    if request.method == 'POST':
        try:
            nome = request.POST.get('nome')
            descricao = request.POST.get('descricao')
            tipo = (request.POST.get('tipo_indicador') or '').lower()
            ods = request.POST.get('ods_indicador') or ''
            unidade_medida = request.POST.get('unidade_medida')
            opcoes_json = request.POST.get('opcoes_predefinidas')
            direcao_melhoria = request.POST.get('direcao_melhoria')
            usar_predefinidos = bool(request.POST.get('usar_predefinidos'))
            valor_referencia_minimo = _decimal_or_none(request.POST.get('valor_referencia_minimo'))
            valor_referencia_maximo = _decimal_or_none(request.POST.get('valor_referencia_maximo'))
            fonte_valor_referencia = request.POST.get('fonte_valor_referencia') or None

            category_ids = _category_ids_from_indicator_form(request)
            if not category_ids:
                messages.error(request, 'Selecione pelo menos uma categoria de norma ou plataforma.')
                return redirect('add_indicator')

            categorias = list(Category.objects.filter(id__in=category_ids).select_related('norma_iso', 'plataforma'))
            if len(categorias) != len(category_ids):
                messages.error(request, 'Uma ou mais categorias selecionadas são inválidas.')
                return redirect('add_indicator')

            lista_limpa_ods = [int(item.strip()) for item in ods.split(',') if item.strip().isdigit()]

            if not nome or not tipo or not direcao_melhoria:
                messages.error(request, 'Nome, tipo e direção de melhoria são obrigatórios.')
                return redirect('add_indicator')

            if valor_referencia_minimo is None or valor_referencia_maximo is None:
                messages.error(request, 'Informe o valor mínimo e máximo de referência para calcular a nota.')
                return redirect('add_indicator')
            if valor_referencia_minimo == valor_referencia_maximo:
                messages.error(request, 'O valor mínimo e o máximo não podem ser iguais.')
                return redirect('add_indicator')

            if usar_predefinidos:
                if not opcoes_json or opcoes_json == '[]':
                    messages.error(request, 'Adicione pelo menos uma opção predefinida.')
                    return redirect('add_indicator')
                unidade_medida = None
                opcoes_final = _clean_predefined_options_from_json(opcoes_json)
            else:
                if not unidade_medida:
                    messages.error(request, 'Informe a unidade de medida.')
                    return redirect('add_indicator')
                opcoes_final = None

            for categoria in categorias:
                if Indicator.objects.filter(nome=nome, categorias=categoria, deletado=False).exists():
                    messages.error(request, f'Já existe um indicador com esse nome na categoria {categoria.nome}.')
                    return redirect('add_indicator')

            indicator = Indicator.objects.create(
                nome=nome,
                descricao=descricao or None,
                tipo=tipo,
                ods=lista_limpa_ods,
                unidade_medida=unidade_medida,
                opcoes_predefinidas=opcoes_final,
                direcao_melhoria=int(direcao_melhoria),
                valor_referencia_minimo=valor_referencia_minimo,
                valor_referencia_maximo=valor_referencia_maximo,
                fonte_valor_referencia=fonte_valor_referencia,
                ativo=True,
                deletado=False,
            )
            for categoria in categorias:
                IndicatorCategory.objects.create(indicador=indicator, categoria=categoria)

            messages.success(request, f'Indicador {nome} criado com sucesso!')
            return _redirect_list_indicators_from_category(categorias[0])

        except Exception as e:
            messages.error(request, f'Erro ao criar indicador: {str(e)}')
            return redirect('add_indicator')

    return render(request, 'admin/indicators/add_indicator.html', {
        'norms': norms,
        'platforms': platforms,
        'norm_categories': norm_categories,
        'platform_categories_by_id': platform_categories_by_id,
        'platform_categories_json': json.dumps({str(k): [{'id': c.id, 'nome': c.nome} for c in v] for k, v in platform_categories_by_id.items()}),
        'norm_categories_json': json.dumps([{'id': c.id, 'nome': c.nome} for c in norm_categories]),
        'selected_norm_id': str(selected_norm_id or ''),
        'selected_platform_ids': [str(x) for x in selected_platform_ids],
    })


@login_required
@admin_required
def edit_indicator(request, indicator_id):
    indicator_to_edit = get_object_or_404(
        Indicator.objects.prefetch_related('categorias', 'categorias__norma_iso', 'categorias__plataforma'),
        id=indicator_id,
        deletado=False,
    )

    norms = NormISO.objects.select_related('ano_referencia').order_by('-ano_referencia__ano', 'codigo_norma')
    platforms = Platform.objects.select_related('ano_referencia').order_by('-ano_referencia__ano', 'nome')
    norm_category_current, platform_category_map = _selected_contexts_for_indicator(indicator_to_edit)

    selected_norm_id = request.POST.get('norm_id') or (str(norm_category_current.norma_iso_id) if norm_category_current else '')
    selected_platform_ids = request.POST.getlist('platform_ids') or list(platform_category_map.keys())

    norm_categories = Category.objects.filter(norma_iso_id=selected_norm_id).order_by('nome') if selected_norm_id else Category.objects.none()
    platform_categories_by_id = {
        str(platform.id): list(Category.objects.filter(plataforma=platform).order_by('nome'))
        for platform in platforms
    }

    if request.method == 'POST':
        try:
            categorias_anteriores = [c.id for c in indicator_to_edit.categorias.all()]
            dados_anteriores = {
                'campos': {
                    'nome': indicator_to_edit.nome,
                    'descricao': indicator_to_edit.descricao,
                    'tipo': indicator_to_edit.tipo,
                    'ods': indicator_to_edit.ods,
                    'unidade_medida': indicator_to_edit.unidade_medida,
                    'opcoes_predefinidas': indicator_to_edit.opcoes_predefinidas,
                    'direcao_melhoria': indicator_to_edit.direcao_melhoria,
                    'valor_referencia_minimo': str(indicator_to_edit.valor_referencia_minimo) if indicator_to_edit.valor_referencia_minimo is not None else None,
                    'valor_referencia_maximo': str(indicator_to_edit.valor_referencia_maximo) if indicator_to_edit.valor_referencia_maximo is not None else None,
                    'fonte_valor_referencia': indicator_to_edit.fonte_valor_referencia,
                    'categorias_ids': categorias_anteriores,
                }
            }

            nome = request.POST.get('nome')
            descricao = request.POST.get('descricao')
            tipo = (request.POST.get('tipo_indicador') or '').lower()
            ods = request.POST.get('ods_indicador') or ''
            unidade_medida = request.POST.get('unidade_medida')
            opcoes_predefinidas = request.POST.get('opcoes_predefinidas')
            direcao_melhoria = request.POST.get('direcao_melhoria')
            usar_predefinidos = bool(request.POST.get('usar_predefinidos'))
            valor_referencia_minimo = _decimal_or_none(request.POST.get('valor_referencia_minimo'))
            valor_referencia_maximo = _decimal_or_none(request.POST.get('valor_referencia_maximo'))
            fonte_valor_referencia = request.POST.get('fonte_valor_referencia') or None

            category_ids = _category_ids_from_indicator_form(request)
            if not category_ids:
                messages.error(request, 'Selecione pelo menos uma categoria de norma ou plataforma.')
                return redirect('edit_indicator', indicator_id=indicator_id)

            categorias = list(Category.objects.filter(id__in=category_ids).select_related('norma_iso', 'plataforma'))
            if len(categorias) != len(category_ids):
                messages.error(request, 'Uma ou mais categorias selecionadas são inválidas.')
                return redirect('edit_indicator', indicator_id=indicator_id)

            lista_limpa_ods = [int(item.strip()) for item in ods.split(',') if item.strip().isdigit()]

            if not nome or not tipo or not direcao_melhoria:
                messages.error(request, 'Nome, tipo e direção de melhoria são obrigatórios.')
                return redirect('edit_indicator', indicator_id=indicator_id)
            if valor_referencia_minimo is None or valor_referencia_maximo is None:
                messages.error(request, 'Informe o valor mínimo e máximo de referência para calcular a nota.')
                return redirect('edit_indicator', indicator_id=indicator_id)
            if valor_referencia_minimo == valor_referencia_maximo:
                messages.error(request, 'O valor mínimo e o máximo não podem ser iguais.')
                return redirect('edit_indicator', indicator_id=indicator_id)

            if usar_predefinidos:
                if not opcoes_predefinidas or opcoes_predefinidas == '[]':
                    messages.error(request, 'Adicione pelo menos uma opção predefinida.')
                    return redirect('edit_indicator', indicator_id=indicator_id)
                unidade_medida = None
                opcoes_final = _clean_predefined_options_from_json(opcoes_predefinidas)
            else:
                if not unidade_medida:
                    messages.error(request, 'Informe a unidade de medida.')
                    return redirect('edit_indicator', indicator_id=indicator_id)
                opcoes_final = None

            for categoria in categorias:
                if Indicator.objects.filter(nome=nome, categorias=categoria, deletado=False).exclude(id=indicator_to_edit.id).exists():
                    messages.error(request, f'Já existe um indicador com esse nome na categoria {categoria.nome}.')
                    return redirect('edit_indicator', indicator_id=indicator_id)

            indicator_to_edit.nome = nome
            indicator_to_edit.descricao = descricao or None
            indicator_to_edit.tipo = tipo
            indicator_to_edit.ods = lista_limpa_ods
            indicator_to_edit.unidade_medida = unidade_medida
            indicator_to_edit.opcoes_predefinidas = opcoes_final
            indicator_to_edit.direcao_melhoria = int(direcao_melhoria)
            indicator_to_edit.valor_referencia_minimo = valor_referencia_minimo
            indicator_to_edit.valor_referencia_maximo = valor_referencia_maximo
            indicator_to_edit.fonte_valor_referencia = fonte_valor_referencia
            indicator_to_edit.save()

            IndicatorCategory.objects.filter(indicador=indicator_to_edit).delete()
            for categoria in categorias:
                IndicatorCategory.objects.create(indicador=indicator_to_edit, categoria=categoria)

            AuditLog.objects.create(
                usuario=request.user,
                acao=AuditLog.AcaoChoices.INDICADOR_EDITADO,
                objeto_tipo='Indicator',
                objeto_id=indicator_to_edit.id,
                descricao=f'Indicador editado: {indicator_to_edit.nome}',
                dados_anteriores=dados_anteriores,
                dados_novos={
                    'campos': {
                        'nome': indicator_to_edit.nome,
                        'descricao': indicator_to_edit.descricao,
                        'tipo': indicator_to_edit.tipo,
                        'ods': indicator_to_edit.ods,
                        'unidade_medida': indicator_to_edit.unidade_medida,
                        'opcoes_predefinidas': indicator_to_edit.opcoes_predefinidas,
                        'direcao_melhoria': indicator_to_edit.direcao_melhoria,
                        'valor_referencia_minimo': str(indicator_to_edit.valor_referencia_minimo),
                        'valor_referencia_maximo': str(indicator_to_edit.valor_referencia_maximo),
                        'fonte_valor_referencia': indicator_to_edit.fonte_valor_referencia,
                        'categorias_ids': [c.id for c in categorias],
                    }
                },
                recuperavel=True,
            )

            messages.success(request, 'Indicador atualizado com sucesso!')
            return _redirect_list_indicators_from_category(categorias[0])

        except Exception as e:
            messages.error(request, f'Erro ao atualizar indicador: {str(e)}')
            return redirect('edit_indicator', indicator_id=indicator_to_edit.id)

    return render(request, 'admin/indicators/edit_indicator.html', {
        'norms': norms,
        'platforms': platforms,
        'indicator_to_edit': indicator_to_edit,
        'norm_categories': norm_categories,
        'platform_categories_by_id': platform_categories_by_id,
        'platform_categories_json': json.dumps({str(k): [{'id': c.id, 'nome': c.nome} for c in v] for k, v in platform_categories_by_id.items()}),
        'norm_categories_json': json.dumps([{'id': c.id, 'nome': c.nome} for c in norm_categories]),
        'selected_norm_id': str(selected_norm_id or ''),
        'selected_platform_ids': [str(x) for x in selected_platform_ids],
        'norm_category_current': norm_category_current.id if norm_category_current else '',
        'platform_category_map': json.dumps(platform_category_map),
        'opcoes_predefinidas_json': _normalize_options_json_for_form(indicator_to_edit.opcoes_predefinidas),
        'valor_referencia_minimo_formatado': _format_number_clean(indicator_to_edit.valor_referencia_minimo),
        'valor_referencia_maximo_formatado': _format_number_clean(indicator_to_edit.valor_referencia_maximo),
    })


@login_required
@admin_required
def delete_indicator(request, indicator_id):
    """Exclui indicador de forma lógica e registra log recuperável."""
    if request.method == 'POST':
        try:
            indicator_to_delete = get_object_or_404(Indicator, id=indicator_id, deletado=False)
            categoria_atual = indicator_to_delete.categorias.first()

            dados_anteriores = {
                'campos': {
                    'nome': indicator_to_delete.nome,
                    'tipo': indicator_to_delete.tipo,
                    'ods': indicator_to_delete.ods,
                    'unidade_medida': indicator_to_delete.unidade_medida,
                    'opcoes_predefinidas': indicator_to_delete.opcoes_predefinidas,
                    'direcao_melhoria': indicator_to_delete.direcao_melhoria,
                    'valor_referencia_minimo': str(indicator_to_delete.valor_referencia_minimo) if indicator_to_delete.valor_referencia_minimo is not None else None,
                    'valor_referencia_maximo': str(indicator_to_delete.valor_referencia_maximo) if indicator_to_delete.valor_referencia_maximo is not None else None,
                    'fonte_valor_referencia': indicator_to_delete.fonte_valor_referencia,
                    'ativo': indicator_to_delete.ativo,
                    'deletado': indicator_to_delete.deletado,
                    'categorias_ids': list(indicator_to_delete.categorias.values_list('id', flat=True)),
                }
            }

            indicator_to_delete.deletado = True
            indicator_to_delete.ativo = False
            indicator_to_delete.deletado_por = request.user
            indicator_to_delete.deletado_em = timezone.now()
            indicator_to_delete.save()

            AuditLog.objects.create(
                usuario=request.user,
                acao=AuditLog.AcaoChoices.INDICADOR_DELETADO,
                objeto_tipo='Indicator',
                objeto_id=indicator_to_delete.id,
                descricao=f'Indicador deletado: {indicator_to_delete.nome}',
                dados_anteriores=dados_anteriores,
                dados_novos={'campos': {'ativo': False, 'deletado': True}},
                recuperavel=True,
            )

            return JsonResponse({
                'success': True,
                'message': f'Indicador {indicator_to_delete.nome} excluído com sucesso.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao excluir indicador: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método não permitido'})


@login_required
@admin_required
def get_categories(request,ano):
    categories = Category.objects.filter(
        Q(norma_iso__ano_referencia__ano=ano) | 
        Q(plataforma__ano_referencia__ano=ano)
    ).values('id', 'nome', 'descricao', 'norma_iso__id','plataforma__id')
    data = {
        'categories': list(categories),
    }
    return JsonResponse(data, safe=False)


@login_required
@admin_required
def get_norms_and_platforms(request, ano):
    norms = NormISO.objects.filter(ano_referencia__ano=ano).values('id', 'codigo_norma')
    platforms = Platform.objects.filter(ano_referencia__ano=ano).values('id', 'nome')
    return JsonResponse({
        'norms': list(norms),
        'platforms': list(platforms),
    }, safe=False)



@login_required
@admin_required
@require_POST
def save_category(request):
    """
    Cria ou edita categoria da norma/plataforma selecionada na tela de indicadores.
    Aceita tanto o formato antigo (norma_iso_id) quanto o novo:
    contexto_tipo=norma|plataforma e contexto_id=<id>.
    """
    cat_id = request.POST.get('category_id')
    nome = (request.POST.get('nome') or '').strip()
    desc = (request.POST.get('descricao') or '').strip()

    contexto_tipo = request.POST.get('contexto_tipo')
    contexto_id = request.POST.get('contexto_id')

    norma_id = request.POST.get('norma_iso_id')
    plataforma_id = request.POST.get('plataforma_id')

    if contexto_tipo == 'norma' and contexto_id:
        norma_id = contexto_id
        plataforma_id = None
    elif contexto_tipo == 'plataforma' and contexto_id:
        plataforma_id = contexto_id
        norma_id = None

    if not nome:
        return JsonResponse({'success': False, 'message': 'Informe o nome da categoria.'}, status=400)

    if not norma_id and not plataforma_id:
        return JsonResponse({'success': False, 'message': 'Selecione uma norma ou plataforma.'}, status=400)

    try:
        if cat_id:
            cat = get_object_or_404(Category, id=cat_id)

            # Impede editar uma categoria fora do contexto selecionado pela tela.
            if norma_id and cat.norma_iso_id != int(norma_id):
                return JsonResponse({'success': False, 'message': 'Categoria não pertence à norma selecionada.'}, status=403)
            if plataforma_id and cat.plataforma_id != int(plataforma_id):
                return JsonResponse({'success': False, 'message': 'Categoria não pertence à plataforma selecionada.'}, status=403)

            exists = Category.objects.filter(
                nome__iexact=nome,
                norma_iso_id=cat.norma_iso_id,
                plataforma_id=cat.plataforma_id,
            ).exclude(id=cat.id).exists()

            if exists:
                return JsonResponse({'success': False, 'message': 'Já existe uma categoria com esse nome neste contexto.'}, status=400)

            cat.nome = nome
            cat.descricao = desc
            cat.save()
            message = 'Categoria atualizada com sucesso.'
        else:
            exists = Category.objects.filter(
                nome__iexact=nome,
                norma_iso_id=norma_id if norma_id else None,
                plataforma_id=plataforma_id if plataforma_id else None,
            ).exists()

            if exists:
                return JsonResponse({'success': False, 'message': 'Já existe uma categoria com esse nome neste contexto.'}, status=400)

            cat = Category.objects.create(
                nome=nome,
                descricao=desc,
                norma_iso_id=norma_id if norma_id else None,
                plataforma_id=plataforma_id if plataforma_id else None,
            )
            message = 'Categoria criada com sucesso.'

        return JsonResponse({
            'success': True,
            'status': 'ok',
            'message': message,
            'category': {
                'id': cat.id,
                'nome': cat.nome,
                'descricao': cat.descricao or '',
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao salvar categoria: {str(e)}'}, status=400)


@login_required
@admin_required
@require_POST
def delete_category(request, cat_id):
    try:
        category_to_delete = get_object_or_404(Category, id=cat_id)
        category_name = category_to_delete.nome

        category_to_delete.delete()

        return JsonResponse({
            'success': True,
            'message': f'Categoria {category_name} excluída com sucesso.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir categoria: {str(e)}'
        }, status=400)



@login_required
@admin_required
def get_certifications(request, norma_id):
    norm = NormISO.objects.get(id=norma_id)
    certifications = Certification.objects.filter(norma_iso=norm).values('id', 'nivel', 'requisitos')
    return JsonResponse(list(certifications), safe=False)


@login_required
@admin_required
@require_POST
def save_certification(request):
    cert_id = request.POST.get('certification_id')
    norma_id = request.POST.get('norma_iso_id')
    nivel = request.POST.get('nivel')
    requisitos = request.POST.get('requisitos')

    try:
        if cert_id: # Editar
            cert = get_object_or_404(Certification, id=cert_id)
            cert.nivel = nivel
            cert.requisitos = requisitos
            cert.save()
            msg = "Certificação atualizada!"
        else: # Criar
            norm = get_object_or_404(NormISO, id=norma_id)
            Certification.objects.create(
                nivel=nivel, 
                requisitos=requisitos, 
                norma_iso=norm
            )
            msg = "Certificação criada!"
        
        return JsonResponse({'success': True, 'message': msg})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@admin_required
@require_POST
def delete_certification(request, cert_id):
    if request.method == 'POST':
        try:
            certification_to_delete = Certification.objects.filter(id=cert_id)
            certification_to_delete.delete()

            return JsonResponse({
                    'success': True,
                    'message': f'Certificação excluída com sucesso'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao excluir certificação: {str(e)}'
            })
    return JsonResponse({'success': False, 'message': 'Método não permitido'})



def _get_user_municipality_data(user):
    """Retorna um dicionário com id, nome e estado do município do usuário"""
    possible_attrs = [
        'municipio_id', 'municipality_id', 'fk_municipio_id', 'cidade_id',
    ]
    for attr in possible_attrs:
        value = getattr(user, attr, None)
        if value:
            try:
                municipality = Municipality.objects.get(id=value)
                result = {
                    'id': municipality.id,
                    'nome': municipality.nome,
                    'estado': municipality.estado
                }
                return result
            except Municipality.DoesNotExist:
                print(f"Erro Município com ID {value} não encontrado")
                pass

    possible_rel_attrs = [
        'municipio', 'municipality', 'fk_municipio', 'cidade',
    ]
    for attr in possible_rel_attrs:
        value = getattr(user, attr, None)
        if value is not None:
            rel_id = getattr(value, 'id', None)
            if rel_id:
                result = {
                    'id': rel_id,
                    'nome': getattr(value, 'nome', ''),
                    'estado': getattr(value, 'estado', '')
                }
                return result
    
    print(f"Erro Nenhum município encontrado para {user.username}")
    return None


def _get_user_municipality_id(user):
    """Retorna apenas o ID do município do usuário (compatibilidade com código existente)"""
    data = _get_user_municipality_data(user)
    return data['id'] if data else None


def _can_edit_municipality(user, municipality_id):
    user_type = getattr(user, 'user_type', '')
    if user_type == 'ADMIN':
        return True
    if user_type == 'MANAGER':
        return _get_user_municipality_id(user) == municipality_id
    return False




@login_required
def normas(request):
    norms = NormISO.objects.all().order_by('codigo_norma', '-ano_referencia').distinct('codigo_norma')
         
    context = {
        'norms': norms,
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'normas/normas.html', context)


@login_required
def iso_view(request, norm_id, codigo_norma):
    norm = get_object_or_404(NormISO, id=norm_id)
    certifications = Certification.objects.filter(norma_iso=norm)
    norms = NormISO.objects.filter(codigo_norma=norm.codigo_norma).order_by('-ano_referencia__ano')
    categories = Category.objects.filter(norma_iso__in=norms).order_by('nome')
    indicators = Indicator.objects.filter(categorias__in=categories, deletado=False).distinct()

    indicators_dict = {}
    actual_categoty_year = None
    for cat in categories:
        cat_indicators = indicators.filter(categorias=cat)
        actual_categoty_year = cat.norma_iso.ano_referencia.ano
        indicators_dict[str(cat.id)] = {
            "key": str(cat.id),
            "name": cat.nome,
            "description": cat.descricao or "",
            "reference_year": actual_categoty_year,
            "indicators": [
                {
                    "id": i.id,
                    "name": i.nome or "",
                    "description": i.descricao or "",
                    "type": i.tipo,
                    "ods": list(i.ods or []),
                    "unit": i.unidade_medida or "",
                    "options": _normalize_predefined_options(i.opcoes_predefinidas),
                    "improvement_direction": i.direcao_melhoria,
                }
                for i in cat_indicators
            ]
        }

    # Resumo da tela: deve considerar apenas a última versão ativa da norma,
    # e não a soma de indicadores de todos os anos cadastrados para o mesmo código.
    latest_active_year = YearReference.objects.filter(ativo=True).order_by('-ano').first()
    summary_norm = None

    if latest_active_year:
        summary_norm = NormISO.objects.filter(
            codigo_norma=norm.codigo_norma,
            ano_referencia=latest_active_year,
        ).first()

    # Caso não exista norma para o último ano ativo, usa a própria norma aberta
    # para evitar zerar o resumo.
    if not summary_norm:
        summary_norm = norm

    summary_categories = Category.objects.filter(norma_iso=summary_norm).order_by('nome')
    summary_indicators = Indicator.objects.filter(
        categorias__in=summary_categories,
        deletado=False,
        ativo=True,
    ).distinct()

    num_main_indicators = summary_indicators.filter(tipo='principal').count()
    num_support_indicators = summary_indicators.filter(tipo='apoio').count()
    num_profile_indicators = summary_indicators.filter(tipo='perfil').count()
    num_categories = summary_categories.distinct('nome').count()

    ods_list = summary_indicators.values_list('ods', flat=True)
    lista_ods = set()
    for item in ods_list:
        if item:
            lista_ods.update(item)

    certifications_json = [
        {
            'id': cert.id,
            'nivel': cert.nivel,
            'requisitos': cert.requisitos or {}
        }
        for cert in certifications
    ]

    context = {
        'norm': norm,
        'certifications': certifications,
        'certifications_json': json.dumps(certifications_json),
        'norms': norms,
        'num_principal_indicators': num_main_indicators + num_support_indicators,
        'num_indicators': num_main_indicators + num_support_indicators + num_profile_indicators,
        'num_main_indicators': num_main_indicators,
        'num_support_indicators': num_support_indicators,
        'num_profile_indicators': num_profile_indicators,
        'num_categories': num_categories,
        'num_ods': len(lista_ods),
        'indicators_json': json.dumps(indicators_dict),
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    
    user_mun_data = _get_user_municipality_data(request.user)
    context['user_municipality_data'] = json.dumps(user_mun_data)
    
    context.update({
        'norms_json': json.dumps([
            {
                'id': item.id,
                'year': item.ano_referencia.ano,
                'code': item.codigo_norma,
            }
            for item in norms
        ]),
        'current_norm_year': norms.first().ano_referencia.ano,
    })
    return render(request, 'normas/iso_view.html', context)


@login_required
def municipality_norm_data(request, norm_id, municipio_id):
    norm = get_object_or_404(NormISO, id=norm_id)
    norms = NormISO.objects.filter(codigo_norma=norm.codigo_norma).order_by('-ano_referencia__ano')
    municipality = get_object_or_404(Municipality, id=municipio_id)

    categories = Category.objects.filter(norma_iso__in=norms).order_by('nome')
    indicators_qs = (
        Indicator.objects
        .filter(categorias__in=categories, deletado=False)
        .prefetch_related('categorias')
        .distinct()
        .order_by('nome')
    )
    indicators = list(indicators_qs)

    values = (
        IndicatorValueYear.objects
        .filter(indicador__in=indicators, municipio=municipality)
        .select_related('indicador')
    )

    values_by_indicator_id = {value.indicador_id: value for value in values}

    profile_indicators = []
    categories_progress = []
    indicators_payload = []

    principal_total = principal_filled = 0
    apoio_total = apoio_filled = 0

    for category in categories:
        category_indicators = [ind for ind in indicators if category in ind.categorias.all()]
        filled_in_category = 0
        total_in_category = len(category_indicators)

        for indicator in category_indicators:
            value_obj = values_by_indicator_id.get(indicator.id)

            value = None
            source = ""
            attachments = []

            if value_obj:
                value = (
                    value_obj.valor_numerico
                    if value_obj.valor_numerico is not None
                    else value_obj.valor_texto
                )
                source = value_obj.fonte or ""

                evidences = EvidencePDF.objects.filter(
                    valor_indicador_ano=value_obj,
                    apagado=False
                ).order_by('-data_upload')

                attachments = [
                    {
                        "id": evidence.id,
                        "descricao": evidence.descricao or f"PDF {idx + 1}",
                        "url": evidence.caminho_arquivo,
                    }
                    for idx, evidence in enumerate(evidences)
                ]

            has_value = value not in (None, "", [])

            indicator_payload = {
                "id": indicator.id,
                "category_id": category.id,
                "category_name": category.nome,
                "name": indicator.nome or "",
                "description": indicator.descricao or "",
                "type": indicator.tipo,
                "ods": list(indicator.ods or []),
                "unit": indicator.unidade_medida or "",
                "options": _normalize_predefined_options(indicator.opcoes_predefinidas),
                "improvement_direction": indicator.direcao_melhoria,
                "value": str(value) if value is not None else "",
                "source": source,
                "attachments": attachments,
                "reference_year": category.norma_iso.ano_referencia.ano,
            }

            indicators_payload.append(indicator_payload)

            if has_value:
                filled_in_category += 1

            tipo_normalizado = str(indicator.tipo).strip().lower()

            if tipo_normalizado == 'perfil':
                profile_indicators.append(indicator_payload)
            elif tipo_normalizado == 'principal':
                principal_total += 1
                if has_value:
                    principal_filled += 1
            elif tipo_normalizado == 'apoio':
                apoio_total += 1
                if has_value:
                    apoio_filled += 1

        categories_progress.append({
            "id": category.id,
            "name": category.nome,
            "percentage": round((filled_in_category / total_in_category) * 100, 1) if total_in_category else 0,
            "filled": filled_in_category,
            "total": total_in_category,
            "reference_year": category.norma_iso.ano_referencia.ano,
        })

    return JsonResponse({
        "success": True,
        "municipality": {
            "id": municipality.id,
            "name": municipality.nome,
            "state": municipality.estado,
        },
        "norms": [
            {
                "id": item.id,
                "code": item.codigo_norma,
                "year": item.ano_referencia.ano,
            }
            for item in norms
        ],
        "permissions": {
            "user_type": getattr(request.user, 'user_type', ''),
            "user_municipality_id": _get_user_municipality_id(request.user),
            "can_edit": _can_edit_municipality(request.user, municipality.id),
        },
        "profile_indicators": profile_indicators,
        "indicators": indicators_payload,
        "categories_progress": categories_progress,
        "summary": {
            "principal_total": principal_total,
            "principal_filled": principal_filled,
            "apoio_total": apoio_total,
            "apoio_filled": apoio_filled,
        }
    })





def _indicator_value_has_content(value_obj):
    return bool(value_obj and (value_obj.valor_numerico is not None or value_obj.valor_texto not in (None, '')))


def recalcular_ranking_municipio_categoria(municipality, indicator):
    """Recalcula a pontuação das categorias ISO do indicador para o município, usando a nota normalizada."""
    categorias = indicator.categorias.filter(norma_iso__isnull=False)

    for categoria in categorias:
        indicadores_categoria = (
            Indicator.objects
            .filter(categorias=categoria, deletado=False, ativo=True)
            .exclude(tipo='perfil')
            .distinct()
        )
        total = indicadores_categoria.count()
        valores = IndicatorValueYear.objects.filter(
            municipio=municipality,
            indicador__in=indicadores_categoria,
        )
        valores_por_indicador = {valor.indicador_id: valor for valor in valores}

        preenchidos = 0
        soma_notas = Decimal('0')
        for ind in indicadores_categoria:
            valor_obj = valores_por_indicador.get(ind.id)
            if _indicator_value_has_content(valor_obj):
                preenchidos += 1
            soma_notas += calcular_nota_indicador(ind, valor_obj)

        pontuacao = Decimal('0')
        if total:
            pontuacao = (soma_notas / Decimal(total)).quantize(Decimal('0.01'))
        classificacao, css = classificar_nota(pontuacao)
        MunicipalityRanking.objects.update_or_create(
            municipio=municipality,
            categoria=categoria,
            defaults={
                'pontuacao_total_categoria': pontuacao,
                'indicadores_preenchidos': preenchidos,
                'indicadores_totais': total,
                'cor_classificacao': css,
            }
        )


@login_required
@require_http_methods(["POST"])
@manager_required
@csrf_exempt
def save_municipality_indicator_value(request, norm_id, municipio_id, indicator_id):
    municipality = get_object_or_404(Municipality, id=municipio_id)
    indicator = get_object_or_404(
        Indicator.objects.prefetch_related('categorias'),
        id=indicator_id,
        categorias__norma_iso_id=norm_id,
        deletado=False,
    )

    if not _can_edit_municipality(request.user, municipality.id):
        return JsonResponse({
            'success': False,
            'message': 'Você não tem permissão para preencher indicadores deste município.'
        }, status=403)

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido.'}, status=400)

    value = payload.get('value', '')
    source = payload.get('source', '')

    indicator_value, created = IndicatorValueYear.objects.get_or_create(
        indicador=indicator,
        municipio=municipality,
        defaults={'fonte': None, 'valor_texto': None, 'valor_numerico': None, 'atualizado_por': request.user}
    )

    dados_anteriores = {
        'campos': {
            'valor_numerico': indicator_value.valor_numerico,
            'valor_texto': indicator_value.valor_texto,
            'fonte': indicator_value.fonte,
        }
    }

    indicator_value.fonte = source or None
    indicator_value.valor_texto = None
    indicator_value.valor_numerico = None

    if value not in [None, '']:
        value_str = str(value).strip()
        if indicator.opcoes_predefinidas:
            indicator_value.valor_texto = value_str
        else:
            try:
                numero = Decimal(value_str.replace(',', '.'))
                indicator_value.valor_numerico = numero
            except Exception:
                indicator_value.valor_texto = value_str

    indicator_value.atualizado_por = request.user
    indicator_value.save()

    AuditLog.objects.create(
        usuario=request.user,
        acao=AuditLog.AcaoChoices.VALOR_ALTERADO,
        objeto_tipo='IndicatorValueYear',
        objeto_id=indicator_value.id,
        descricao=f'Valor alterado: {indicator.nome} - {municipality.nome}/{municipality.estado}',
        dados_anteriores=dados_anteriores,
        dados_novos={
            'campos': {
                'valor_numerico': indicator_value.valor_numerico,
                'valor_texto': indicator_value.valor_texto,
                'fonte': indicator_value.fonte,
            }
        },
        recuperavel=True,
    )

    recalcular_ranking_municipio_categoria(municipality, indicator)
    refresh_iso_ranking_materialized_view()

    return JsonResponse({
        'success': True,
        'message': 'Indicador salvo com sucesso.',
        'value_id': indicator_value.id,
    })


@login_required
@require_http_methods(["POST"])
@manager_required
@csrf_exempt
def upload_municipality_indicator_attachment(request, norm_id, municipio_id, indicator_id):
    municipality = get_object_or_404(Municipality, id=municipio_id)
    indicator = get_object_or_404(
        Indicator,
        id=indicator_id,
        categorias__norma_iso_id=norm_id,
        deletado=False,
    )

    if not _can_edit_municipality(request.user, municipality.id):
        return JsonResponse({'success': False, 'message': 'Sem permissão.'}, status=403)

    files = request.FILES.getlist('anexos') or ([request.FILES.get('anexo')] if request.FILES.get('anexo') else [])
    files = [file for file in files if file]

    for file in files:
        if file.size > 15728640:
            return JsonResponse({'success': False, 'message': f'O arquivo {file.name} excede o limite de 15MB.'}, status=400)

    if not files:
        return JsonResponse({'success': False, 'message': 'Nenhum arquivo enviado.'}, status=400)

    indicator_value, _ = IndicatorValueYear.objects.get_or_create(
        indicador=indicator,
        municipio=municipality,
        defaults={'atualizado_por': request.user}
    )

    created_files = []

    for file in files:
        original_name = file.name or 'arquivo.pdf'
        safe_original_name = get_valid_filename(original_name)
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S%f")
        filename = f"norm_{norm_id}_mun_{municipio_id}_ind_{indicator_id}_{timestamp}_{safe_original_name}"
        relative_path = os.path.join('iso_anexos', filename)

        saved_path = default_storage.save(relative_path, ContentFile(file.read()))
        file_url = default_storage.url(saved_path)

        evidence = EvidencePDF.objects.create(
            valor_indicador_ano=indicator_value,
            descricao=original_name,
            caminho_arquivo=file_url,
            apagado=False,
        )

        AuditLog.objects.create(
            usuario=request.user,
            acao=AuditLog.AcaoChoices.ANEXO_ENVIADO,
            objeto_tipo='EvidencePDF',
            objeto_id=evidence.id,
            descricao=f'Anexo enviado: {original_name}',
            dados_novos={'campos': {'descricao': original_name, 'caminho_arquivo': file_url}},
            recuperavel=False,
        )

        created_files.append({
            'id': evidence.id,
            'descricao': evidence.descricao,
            'url': evidence.caminho_arquivo,
        })

    return JsonResponse({
        'success': True,
        'message': 'Anexo(s) enviado(s) com sucesso.',
        'attachments': created_files
    })


@login_required
@require_http_methods(["POST"])
@manager_required
@csrf_exempt
def delete_municipality_indicator_attachment(request, norm_id, municipio_id, indicator_id, attachment_id):
    municipality = get_object_or_404(Municipality, id=municipio_id)
    indicator = get_object_or_404(
        Indicator,
        id=indicator_id,
        categorias__norma_iso_id=norm_id,
        deletado=False,
    )

    if not _can_edit_municipality(request.user, municipality.id):
        return JsonResponse({'success': False, 'message': 'Sem permissão.'}, status=403)

    indicator_value = get_object_or_404(IndicatorValueYear, indicador=indicator, municipio=municipality)
    evidence = get_object_or_404(EvidencePDF, id=attachment_id, valor_indicador_ano=indicator_value, apagado=False)

    dados_anteriores = {
        'campos': {
            'descricao': evidence.descricao,
            'caminho_arquivo': evidence.caminho_arquivo,
            'apagado': False,
            'valor_indicador_ano_id': indicator_value.id,
        }
    }

    evidence.apagado = True
    evidence.apagado_por = request.user
    evidence.apagado_em = timezone.now()
    evidence.save()

    AuditLog.objects.create(
        usuario=request.user,
        acao=AuditLog.AcaoChoices.ANEXO_APAGADO,
        objeto_tipo='EvidencePDF',
        objeto_id=evidence.id,
        descricao=f'Anexo apagado: {evidence.descricao or evidence.caminho_arquivo}',
        dados_anteriores=dados_anteriores,
        dados_novos={'campos': {'apagado': True, 'apagado_por_id': request.user.id}},
        recuperavel=True,
    )

    return JsonResponse({'success': True, 'message': 'Anexo removido com sucesso.'})


@login_required
def list_states(request):
    try:
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
    





# -----------------------------------------------------------------------------
# Pontuações / Metas / Consulta de Cidades por Plataforma
# -----------------------------------------------------------------------------

def _display_indicator_value(value_obj):
    if not value_obj:
        return ""
    if value_obj.valor_numerico is not None:
        return value_obj.valor_numerico
    return _coerce_predefined_label(value_obj.valor_texto) or ""


def _rating_label(score):
    try:
        score = float(score or 0)
    except Exception:
        score = 0
    if score >= 70:
        return "Bom"
    if score >= 40:
        return "Médio"
    return "Ruim"


def _platform_scope(platform_id=None):
    if platform_id:
        return get_object_or_404(Platform.objects.select_related('ano_referencia'), id=platform_id)
    return Platform.objects.select_related('ano_referencia').order_by('-ano_referencia__ano', 'nome').first()


def _platform_categories(platform):
    if not platform:
        return Category.objects.none()
    return Category.objects.filter(plataforma=platform).order_by('nome')


def _platform_indicators(platform, user=None):
    categories = _platform_categories(platform)
    qs = (
        Indicator.objects
        .filter(categorias__in=categories, deletado=False, ativo=True)
        .prefetch_related('categorias', 'categorias__plataforma')
        .distinct()
        .order_by('nome')
    )

    return qs


def _compute_category_score(municipality, category):
    ranking = MunicipalityRanking.objects.filter(municipio=municipality, categoria=category).first()
    if ranking:
        return {
            'score': _to_float(ranking.pontuacao_total_categoria or 0),
            'filled': ranking.indicadores_preenchidos,
            'total': ranking.indicadores_totais,
        }

    indicators = Indicator.objects.filter(categorias=category, deletado=False, ativo=True).exclude(tipo='perfil').distinct()
    total = indicators.count()
    values = IndicatorValueYear.objects.filter(municipio=municipality, indicador__in=indicators)
    values_by_indicator = {item.indicador_id: item for item in values}
    filled = 0
    total_score = Decimal('0')
    for ind in indicators:
        value_obj = values_by_indicator.get(ind.id)
        if _indicator_value_has_content(value_obj):
            filled += 1
        # Padrão CSC: indicador ausente entra como zero na média do eixo.
        total_score += calcular_nota_indicador(ind, value_obj)
    score = (total_score / Decimal(total)) if total else Decimal('0')
    return {'score': round(float(score), 2), 'filled': filled, 'total': total}


def _rank_position_for_category(municipality, category, score=None):
    rankings = list(
        MunicipalityRanking.objects
        .filter(categoria=category)
        .select_related('municipio')
        .order_by('-pontuacao_total_categoria', 'municipio__nome')
    )
    if rankings:
        for idx, item in enumerate(rankings, start=1):
            if item.municipio_id == municipality.id:
                return idx
        return len(rankings) + 1

    if score is None:
        score = _compute_category_score(municipality, category)['score']
    return 1 if score else '-'


def _best_city_for_category(category):
    ranking = (
        MunicipalityRanking.objects
        .filter(categoria=category)
        .select_related('municipio')
        .order_by('-pontuacao_total_categoria', 'municipio__nome')
        .first()
    )
    if ranking:
        return {
            'city': ranking.municipio.nome,
            'uf': ranking.municipio.estado,
            'score': _format_number_clean(ranking.pontuacao_total_categoria or 0),
        }
    return None


def _best_city_for_indicator(indicator):
    values = (
        IndicatorValueYear.objects
        .filter(indicador=indicator)
        .exclude(valor_numerico__isnull=True)
        .select_related('municipio')
    )
    if not values.exists():
        return None
    if indicator.direcao_melhoria == -1:
        value = values.order_by('valor_numerico', 'municipio__nome').first()
    else:
        value = values.order_by('-valor_numerico', 'municipio__nome').first()
    if not value:
        return None
    return {
        'city': value.municipio.nome,
        'uf': value.municipio.estado,
        'value': _format_number_clean(value.valor_numerico),
        'unit': indicator.unidade_medida or '',
    }


def _build_platform_dashboard_data(platform, municipality, user=None):
    categories = list(_platform_categories(platform))
    indicators = list(_platform_indicators(platform, user=user))
    values = IndicatorValueYear.objects.filter(municipio=municipality, indicador__in=indicators).select_related('indicador') if municipality else IndicatorValueYear.objects.none()
    values_by_indicator = {item.indicador_id: item for item in values}

    evidences_by_value = {}
    evidence_counts = {}
    value_ids = [v.id for v in values]
    if value_ids:
        evidences = EvidencePDF.objects.filter(
            valor_indicador_ano_id__in=value_ids,
            apagado=False,
        ).order_by('-data_upload')
        for evidence in evidences:
            evidences_by_value.setdefault(evidence.valor_indicador_ano_id, []).append(evidence)
            evidence_counts[evidence.valor_indicador_ano_id] = evidence_counts.get(evidence.valor_indicador_ano_id, 0) + 1

    category_rows = []
    radar_labels = []
    radar_values = []
    for category in categories:
        score_data = _compute_category_score(municipality, category) if municipality else {'score': 0, 'filled': 0, 'total': 0}
        score_value = _to_float(score_data.get('score', 0))
        best = _best_city_for_category(category)
        position = _rank_position_for_category(municipality, category, score_value) if municipality else '-'
        category_rows.append({
            'id': category.id,
            'name': category.nome,
            'score': _format_number_clean(round(score_value, 2)),
            'label': _rating_label(score_value),
            'position': position,
            'best': best,
            'filled': score_data['filled'],
            'total': score_data['total'],
        })
        radar_labels.append(category.nome)
        radar_values.append(round(score_value, 2))

    indicator_rows = []
    for indicator in indicators:
        categories_for_indicator = [c for c in indicator.categorias.all() if c.plataforma_id == platform.id]
        category = categories_for_indicator[0] if categories_for_indicator else None
        value_obj = values_by_indicator.get(indicator.id)
        best_value = _best_city_for_indicator(indicator)
        attachments = evidences_by_value.get(value_obj.id, []) if value_obj else []
        attachments_count = evidence_counts.get(value_obj.id, 0) if value_obj else 0
        indicator_rows.append({
            'id': indicator.id,
            'name': indicator.nome,
            'description': indicator.descricao or '',
            'category': category.nome if category else 'Sem eixo',
            'category_id': category.id if category else '',
            'value': _format_number_clean(_display_indicator_value(value_obj)),
            'raw_value': _format_number_clean(_display_indicator_value(value_obj)),
            'unit': indicator.unidade_medida or '',
            'source': value_obj.fonte if value_obj else '',
            'attachments_count': attachments_count,
            'attachments': attachments,
            'filled': _indicator_value_has_content(value_obj),
            'score': _format_number_clean(calcular_nota_indicador(indicator, value_obj)),
            'reference_min': _format_number_clean(indicator.valor_referencia_minimo),
            'reference_max': _format_number_clean(indicator.valor_referencia_maximo),
            'best_value': best_value,
            'options': _normalize_predefined_options(indicator.opcoes_predefinidas),
        })

    return {
        'category_rows': category_rows,
        'indicator_rows': indicator_rows,
        'radar_labels': radar_labels,
        'radar_values': radar_values,
        'filled_count': sum(1 for item in indicator_rows if item['filled']),
        'unfilled_count': sum(1 for item in indicator_rows if not item['filled']),
        'total_indicators': len(indicator_rows),
    }


def _recalcular_ranking_municipio_categoria_unica(municipality, category):
    """Recalcula a pontuação de uma categoria/eixo com a metodologia CSC simplificada."""
    indicadores_categoria = (
        Indicator.objects
        .filter(categorias=category, deletado=False, ativo=True)
        .exclude(tipo='perfil')
        .distinct()
    )
    total = indicadores_categoria.count()
    valores = IndicatorValueYear.objects.filter(
        municipio=municipality,
        indicador__in=indicadores_categoria,
    )
    valores_por_indicador = {valor.indicador_id: valor for valor in valores}

    preenchidos = 0
    soma_notas = Decimal('0')
    for indicador in indicadores_categoria:
        valor_obj = valores_por_indicador.get(indicador.id)
        if _indicator_value_has_content(valor_obj):
            preenchidos += 1
        # Indicador vazio conta como zero, conforme a lógica CSC descrita no manual.
        soma_notas += calcular_nota_indicador(indicador, valor_obj)

    pontuacao = Decimal('0')
    if total:
        pontuacao = (soma_notas / Decimal(total)).quantize(Decimal('0.01'))

    classificacao, css = classificar_nota(pontuacao)
    MunicipalityRanking.objects.update_or_create(
        municipio=municipality,
        categoria=category,
        defaults={
            'pontuacao_total_categoria': pontuacao,
            'indicadores_preenchidos': preenchidos,
            'indicadores_totais': total,
            'cor_classificacao': css,
        }
    )


def recalcular_ranking_municipio_plataforma(municipality, indicator, platform):
    """Recalcula os eixos de uma plataforma após preenchimento ou anexo."""
    for category in indicator.categorias.filter(plataforma=platform):
        _recalcular_ranking_municipio_categoria_unica(municipality, category)


@login_required
def completions_goals_home(request):
    platform = _platform_scope()
    if not platform:
        messages.error(request, 'Nenhuma plataforma cadastrada.')
        return redirect('normas')
    return redirect('completions_goals_platform', platform_id=platform.id)


@login_required
def completions_goals_platform(request, platform_id):
    platform = _platform_scope(platform_id)
    platforms = Platform.objects.select_related('ano_referencia').order_by('-ano_referencia__ano', 'nome')
    tab = request.GET.get('tab', 'scores')
    if tab not in ['scores', 'cities', 'indicators']:
        tab = 'scores'

    selected_state = request.GET.get('estado') or ''
    selected_city_id = request.GET.get('municipio') or ''

    user_municipality = getattr(request.user, 'municipio', None)
    selected_municipality = user_municipality

    if selected_city_id:
        selected_municipality = Municipality.objects.filter(id=selected_city_id).first() or user_municipality

    goal_ref = None
    if platform and selected_municipality:
        # A cidade meta é compartilhada por todos os gestores do município atual,
        # não é uma preferência individual do usuário.
        goal_ref = (
            PlatformGoalReference.objects
            .filter(platform=platform, municipio=selected_municipality)
            .select_related('municipio', 'municipio_referencia', 'gestor')
            .first()
        )

    data = _build_platform_dashboard_data(platform, selected_municipality, user=request.user) if platform and selected_municipality else {
        'category_rows': [], 'indicator_rows': [], 'radar_labels': [], 'radar_values': [],
        'filled_count': 0, 'unfilled_count': 0, 'total_indicators': 0,
    }

    goal_data = None
    if platform and goal_ref and goal_ref.municipio_referencia:
        goal_data = _build_platform_dashboard_data(
            platform,
            goal_ref.municipio_referencia,
            user=request.user,
        )

    categories = _platform_categories(platform)
    states = Municipality.objects.exclude(estado__isnull=True).exclude(estado='').values_list('estado', flat=True).distinct().order_by('estado')
    municipalities = Municipality.objects.all().order_by('estado', 'nome')
    if selected_state:
        municipalities = municipalities.filter(estado=selected_state)

    context = {
        'platform': platform,
        'platforms': platforms,
        'active_tab': tab,
        'municipality': selected_municipality,
        'user_municipality': user_municipality,
        'goal_reference': goal_ref,
        'categories': categories,
        'states': states,
        'municipalities': municipalities,
        'selected_state': selected_state,
        'selected_city_id': int(selected_city_id) if str(selected_city_id).isdigit() else '',
        **data,
        'radar_labels_json': json.dumps(data['radar_labels']),
        'radar_values_json': json.dumps(data['radar_values']),
        'goal_radar_values_json': json.dumps(goal_data['radar_values'] if goal_data else []),
        'radar_city_label': selected_municipality.nome if selected_municipality else 'Cidade do gestor',
        'goal_radar_city_label': goal_ref.municipio_referencia.nome if goal_ref and goal_ref.municipio_referencia else '',
    }
    return render(request, 'completionsAndGoals/dashboard.html', context)


@login_required
@require_POST
def save_platform_indicator_completion(request, platform_id, indicator_id):
    platform = get_object_or_404(Platform, id=platform_id)
    # Um mesmo indicador pode estar vinculado a mais de uma categoria da mesma plataforma.
    # Por isso, filtrar por categorias__plataforma_id pode gerar linhas duplicadas no JOIN.
    # O distinct() garante que o get_object_or_404 receba apenas um Indicator.
    indicator = get_object_or_404(
        Indicator.objects.filter(
            id=indicator_id,
            categorias__plataforma_id=platform_id,
            deletado=False,
            ativo=True,
        ).prefetch_related('categorias').distinct()
    )
    municipality = getattr(request.user, 'municipio', None)
    wants_json = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in (request.content_type or '')

    def fail(message, status=400):
        if wants_json:
            return JsonResponse({'success': False, 'message': message}, status=status)
        messages.error(request, message)
        return redirect(f"{reverse('completions_goals_platform', kwargs={'platform_id': platform.id})}?tab=indicators")

    if not municipality:
        return fail('Seu usuário não possui município vinculado para preencher indicadores.', 403)

    if not _can_edit_municipality(request.user, municipality.id):
        return fail('Você não tem permissão para preencher indicadores deste município.', 403)

    if wants_json:
        try:
            payload = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return fail('JSON inválido.', 400)
        value = payload.get('value', '')
        source = payload.get('source', '')
    else:
        value = request.POST.get('value', '')
        source = request.POST.get('source', '')

    # Validação de consistência semelhante à tela ISO: valor inválido não é salvo.
    value_str = _coerce_predefined_label(value) if value not in [None, ''] else ''
    parsed_number = None
    parsed_text = None

    if value_str:
        if indicator.opcoes_predefinidas:
            valid_options = [option['label'] for option in _normalize_predefined_options(indicator.opcoes_predefinidas)]
            if value_str not in valid_options:
                return fail('Valor inconsistente: selecione uma das opções cadastradas para este indicador.', 400)
            parsed_text = value_str
        else:
            try:
                parsed_number = Decimal(value_str.replace(',', '.'))
            except Exception:
                return fail('Valor inconsistente: informe um número válido para este indicador.', 400)

    indicator_value, _ = IndicatorValueYear.objects.get_or_create(
        indicador=indicator,
        municipio=municipality,
        defaults={'fonte': None, 'valor_texto': None, 'valor_numerico': None, 'atualizado_por': request.user}
    )

    dados_anteriores = {
        'campos': {
            'valor_numerico': str(indicator_value.valor_numerico) if indicator_value.valor_numerico is not None else None,
            'valor_texto': indicator_value.valor_texto,
            'fonte': indicator_value.fonte,
        }
    }

    indicator_value.fonte = source or None
    indicator_value.valor_texto = parsed_text
    indicator_value.valor_numerico = parsed_number
    indicator_value.atualizado_por = request.user
    indicator_value.save()

    AuditLog.objects.create(
        usuario=request.user,
        acao=AuditLog.AcaoChoices.PREENCHIMENTO_DESIGNADO if hasattr(AuditLog.AcaoChoices, 'PREENCHIMENTO_DESIGNADO') else AuditLog.AcaoChoices.VALOR_ALTERADO,
        objeto_tipo='IndicatorValueYear',
        objeto_id=indicator_value.id,
        descricao=f'Preenchimento na área de metas: {indicator.nome} - {municipality.nome}/{municipality.estado}',
        dados_anteriores=dados_anteriores,
        dados_novos={
            'campos': {
                'valor_numerico': str(indicator_value.valor_numerico) if indicator_value.valor_numerico is not None else None,
                'valor_texto': indicator_value.valor_texto,
                'fonte': indicator_value.fonte,
                'platform_id': platform.id,
            }
        },
        recuperavel=True,
    )

    files = [] if wants_json else (request.FILES.getlist('anexos') or ([request.FILES.get('anexo')] if request.FILES.get('anexo') else []))
    files = [file for file in files if file]
    for file in files:
        if file.size > 15728640:
            return fail(f'O arquivo {file.name} excede o limite de 15MB.', 400)
        original_name = file.name or 'arquivo.pdf'
        safe_original_name = get_valid_filename(original_name)
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S%f')
        filename = f'platform_{platform_id}_mun_{municipality.id}_ind_{indicator_id}_{timestamp}_{safe_original_name}'
        relative_path = os.path.join('iso_anexos', filename)
        saved_path = default_storage.save(relative_path, ContentFile(file.read()))
        file_url = default_storage.url(saved_path)
        evidence = EvidencePDF.objects.create(
            valor_indicador_ano=indicator_value,
            descricao=original_name,
            caminho_arquivo=file_url,
            apagado=False,
        )
        AuditLog.objects.create(
            usuario=request.user,
            acao=AuditLog.AcaoChoices.ANEXO_ENVIADO,
            objeto_tipo='EvidencePDF',
            objeto_id=evidence.id,
            descricao=f'Anexo enviado na área de metas: {original_name}',
            dados_novos={'campos': {'descricao': original_name, 'caminho_arquivo': file_url, 'platform_id': platform.id}},
            recuperavel=False,
        )

    recalcular_ranking_municipio_plataforma(municipality, indicator, platform)
    score = calcular_nota_indicador(indicator, indicator_value)

    if wants_json:
        return JsonResponse({
            'success': True,
            'message': 'Indicador salvo com sucesso.',
            'score': _format_number_clean(score),
            'value': _format_number_clean(indicator_value.valor_numerico) if indicator_value.valor_numerico is not None else (_coerce_predefined_label(indicator_value.valor_texto) or ''),
            'source': indicator_value.fonte or '',
        })

    messages.success(request, 'Indicador salvo com sucesso.')
    return redirect(f"{reverse('completions_goals_platform', kwargs={'platform_id': platform.id})}?tab=indicators")


@login_required
@require_POST
def delete_platform_indicator_attachment(request, platform_id, indicator_id, attachment_id):
    platform = get_object_or_404(Platform, id=platform_id)
    # O distinct() evita MultipleObjectsReturned quando o indicador tem múltiplas
    # categorias dentro da mesma plataforma.
    indicator = get_object_or_404(
        Indicator.objects.filter(
            id=indicator_id,
            categorias__plataforma_id=platform_id,
            deletado=False,
            ativo=True,
        ).distinct()
    )
    municipality = getattr(request.user, 'municipio', None)
    if not municipality or not _can_edit_municipality(request.user, municipality.id):
        messages.error(request, 'Você não tem permissão para remover anexos deste município.')
        return redirect(f"{reverse('completions_goals_platform', kwargs={'platform_id': platform.id})}?tab=indicators")

    indicator_value = get_object_or_404(
        IndicatorValueYear,
        indicador=indicator,
        municipio=municipality,
    )
    evidence = get_object_or_404(
        EvidencePDF,
        id=attachment_id,
        valor_indicador_ano=indicator_value,
        apagado=False,
    )

    dados_anteriores = {
        'campos': {
            'descricao': evidence.descricao,
            'caminho_arquivo': evidence.caminho_arquivo,
            'apagado': False,
            'valor_indicador_ano_id': indicator_value.id,
        }
    }
    evidence.apagado = True
    evidence.apagado_por = request.user
    evidence.apagado_em = timezone.now()
    evidence.save()

    AuditLog.objects.create(
        usuario=request.user,
        acao=AuditLog.AcaoChoices.ANEXO_APAGADO,
        objeto_tipo='EvidencePDF',
        objeto_id=evidence.id,
        descricao=f'Anexo apagado na área de metas: {evidence.descricao or evidence.caminho_arquivo}',
        dados_anteriores=dados_anteriores,
        dados_novos={'campos': {'apagado': True, 'apagado_por_id': request.user.id, 'apagado_em': evidence.apagado_em.isoformat()}},
        recuperavel=True,
    )
    messages.success(request, 'Anexo removido da lista e registrado na auditoria.')
    return redirect(f"{reverse('completions_goals_platform', kwargs={'platform_id': platform.id})}?tab=indicators")


@login_required
@require_POST
def save_platform_goal_reference(request, platform_id):
    platform = get_object_or_404(Platform, id=platform_id)
    municipio_usuario = getattr(request.user, 'municipio', None)

    if not municipio_usuario:
        messages.error(request, 'Seu usuário não possui município vinculado para definir uma meta.')
        return redirect(request.POST.get('next') or reverse('completions_goals_platform', kwargs={'platform_id': platform.id}))

    municipio_id = request.POST.get('municipio_referencia')
    municipio_referencia = get_object_or_404(Municipality, id=municipio_id)

    # A meta é definida por município: todos os gestores do mesmo município
    # verão a mesma cidade referência nessa plataforma.
    PlatformGoalReference.objects.update_or_create(
        platform=platform,
        municipio=municipio_usuario,
        defaults={
            'municipio_referencia': municipio_referencia,
            'gestor': request.user,
        },
    )
    messages.success(
        request,
        f'Cidade referência definida como {municipio_referencia.nome}/{municipio_referencia.estado} para todos os gestores de {municipio_usuario.nome}/{municipio_usuario.estado}.'
    )
    return redirect(f"{request.POST.get('next') or reverse('completions_goals_platform', kwargs={'platform_id': platform.id})}")


def classificar_nota(nota):
    if nota is None:
        return None, None

    nota = float(nota)

    if nota >= 90:
        return "Platina", "platinum"
    elif nota >= 80:
        return "Ouro", "gold"
    elif nota >= 70:
        return "Prata", "silver"
    return "Bronze", "bronze"


def montar_resultado_norma(nota):
    if nota is None:
        return {
            "nota": None,
            "classificacao": None,
            "css": None,
        }

    classificacao, css = classificar_nota(nota)

    return {
        "nota": round(float(nota), 2),
        "classificacao": classificacao,
        "css": css,
    }



@login_required
def ranking_iso_view(request):
    ano = request.GET.get("ano")
    estado = request.GET.get("estado")
    norma = request.GET.get("norma")
    categoria = request.GET.get("categoria")
    busca = request.GET.get("busca")

    ano_mais_recente = YearReference.objects.filter(ativo=True).order_by("-ano").first()

    try:
        qs = RankingISOCategoriaView.objects.all()
        if ano:
            qs = qs.filter(ano=ano)
        elif ano_mais_recente:
            qs = qs.filter(ano=ano_mais_recente.ano)
        qs_exists = qs.exists()
    except DatabaseError:
        qs = None
        qs_exists = False

    if qs is None or not qs_exists:
        qs = (
            MunicipalityRanking.objects
            .filter(categoria__norma_iso__isnull=False)
            .select_related('municipio', 'categoria', 'categoria__norma_iso', 'categoria__norma_iso__ano_referencia')
            .annotate(
                municipio_id_annot=F('municipio__id'),
                municipio_nome=F('municipio__nome'),
                uf=F('municipio__estado'),
                ano_annot=F('categoria__norma_iso__ano_referencia__ano'),
                norma_id_annot=F('categoria__norma_iso__id'),
                codigo_norma_annot=F('categoria__norma_iso__codigo_norma'),
                categoria_id_annot=F('categoria__id'),
                categoria_nome=F('categoria__nome'),
            )
        )
        if ano:
            qs = qs.filter(categoria__norma_iso__ano_referencia__ano=ano)
        elif ano_mais_recente:
            qs = qs.filter(categoria__norma_iso__ano_referencia__ano=ano_mais_recente.ano)

    if estado:
        qs = qs.filter(uf=estado) if isinstance(qs.model, type) and qs.model is RankingISOCategoriaView else qs.filter(municipio__estado=estado)

    if norma:
        if qs.model is RankingISOCategoriaView:
            qs = qs.filter(codigo_norma=norma)
        else:
            qs = qs.filter(categoria__norma_iso__codigo_norma=norma)

    if categoria:
        if qs.model is RankingISOCategoriaView:
            qs = qs.filter(categoria_id=categoria)
        else:
            qs = qs.filter(categoria_id=categoria)

    if busca:
        if qs.model is RankingISOCategoriaView:
            qs = qs.filter(municipio__icontains=busca)
        else:
            qs = qs.filter(municipio__nome__icontains=busca)

    ranking_por_municipio = defaultdict(lambda: {
        "municipio_id": None,
        "municipio": "",
        "uf": "",
        "iso37120": None,
        "iso37122": None,
        "iso37123": None,
        "iso37125": None,
        "notas": [],
    })

    for item in qs:
        if isinstance(item, RankingISOCategoriaView):
            municipio_id = item.municipio_id
            municipio_nome = item.municipio
            uf = item.uf
            codigo_norma = item.codigo_norma
            nota = item.pontuacao_categoria
        else:
            municipio_id = item.municipio_id
            municipio_nome = item.municipio.nome
            uf = item.municipio.estado
            codigo_norma = item.categoria.norma_iso.codigo_norma if item.categoria and item.categoria.norma_iso else ''
            nota = item.pontuacao_total_categoria

        row = ranking_por_municipio[municipio_id]
        row["municipio_id"] = municipio_id
        row["municipio"] = municipio_nome
        row["uf"] = uf
        if nota is not None:
            row["notas"].append(Decimal(nota))

        codigo = str(codigo_norma).replace(" ", "").upper()
        resultado = montar_resultado_norma(nota)
        if "37120" in codigo:
            row["iso37120"] = resultado
        elif "37122" in codigo:
            row["iso37122"] = resultado
        elif "37123" in codigo:
            row["iso37123"] = resultado
        elif "37125" in codigo:
            row["iso37125"] = resultado

    ranking = []
    municipios_cache = Municipality.objects.in_bulk([key for key in ranking_por_municipio.keys() if key])

    for dados in ranking_por_municipio.values():
        notas = dados["notas"]
        nota_geral = sum(notas) / Decimal(len(notas)) if notas else None
        municipio_obj = municipios_cache.get(dados["municipio_id"])

        nota_geral_resultado = montar_resultado_norma(nota_geral)
        ranking.append({
            "municipio_id": dados["municipio_id"],
            "municipio": dados["municipio"],
            "uf": dados["uf"],
            "iso37120": dados["iso37120"] or montar_resultado_norma(None),
            "iso37122": dados["iso37122"] or montar_resultado_norma(None),
            "iso37123": dados["iso37123"] or montar_resultado_norma(None),
            "iso37125": dados["iso37125"] or montar_resultado_norma(None),
            "nota_geral": nota_geral_resultado["nota"],
            "nota_geral_classificacao": nota_geral_resultado["classificacao"],
            "nota_geral_css": nota_geral_resultado["css"],
            "porte": getattr(municipio_obj, "porte", "-") if municipio_obj else "-",
            "regiao": getattr(municipio_obj, "regiao", "-") if municipio_obj else "-",
        })

    ranking.sort(key=lambda item: item["nota_geral"] if item["nota_geral"] is not None else -1, reverse=True)
    for posicao, item in enumerate(ranking, start=1):
        item["posicao"] = posicao

    context = {
        "rankings": ranking,
        "anos": YearReference.objects.filter(ativo=True).order_by("-ano"),
        "estados": Municipality.objects.exclude(estado__isnull=True).exclude(estado="").values_list("estado", flat=True).distinct().order_by("estado"),
        "normas": NormISO.objects.values_list("codigo_norma", flat=True).distinct().order_by("codigo_norma"),
        "categorias": Category.objects.filter(norma_iso__isnull=False).select_related("norma_iso", "norma_iso__ano_referencia").order_by("norma_iso__codigo_norma", "nome"),
        "user_is_admin": request.user.is_admin() if hasattr(request.user, "is_admin") else request.user.is_superuser,
        "filtros": {
            "ano": ano,
            "estado": estado,
            "norma": norma,
            "categoria": categoria,
            "busca": busca,
        },
    }
    return render(request, "normas/ranking_iso.html", context)


@login_required
def consulta_cidade_view(request, uf, municipio_id):
    cidade = get_object_or_404(
        Municipality,
        id=municipio_id,
        estado=uf,
    )

    valores = (
        IndicatorValueYear.objects
        .filter(municipio=cidade)
        .select_related("indicador")
        .prefetch_related(
            "indicador__categorias",
            "indicador__categorias__norma_iso",
            "indicador__categorias__plataforma",
        )
        .order_by("indicador__nome")
    )

    rankings = (
        MunicipalityRanking.objects
        .filter(municipio=cidade)
        .select_related(
            "categoria",
            "categoria__norma_iso",
            "categoria__plataforma",
        )
        .order_by("categoria__nome")
    )

    context = {
        "cidade": cidade,
        "valores": valores,
        "rankings": rankings,
    }

    return render(request, "consulta_cidade.html", context)


def refresh_iso_ranking_materialized_view():
    try:
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW vw_ranking_iso_categoria;")
    except DatabaseError:
        # Se a view materializada não existir ou houver problema de banco, não interrompe o salvamento.
        pass


@login_required
def atualizar_ranking_iso_view(request):
    if not request.user.is_admin():
        messages.error(request, "Você não tem permissão para atualizar o ranking.")
        return redirect("ranking_iso")

    refresh_iso_ranking_materialized_view()

    messages.success(request, "Ranking ISO atualizado com sucesso.")
    return redirect("ranking_iso")
