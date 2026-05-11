from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from accounts.models import YearReference, User, Municipality
import json
import os
from django.conf import settings
from django.utils import timezone
from accounts.decorators import admin_required, manager_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from django.utils import timezone
import os


@login_required
@admin_required
def list_indicators_csc(request):
    """Listar todos os indicadores cadastrados do sistema"""
    years = YearReference.objects.filter(ativo=True)
    categories = CategoryCSC.objects.filter().order_by('nome')
    indicators = FutureIndicatorCSC.objects.filter(categoria__in=categories).order_by('nome_indicador')     

    context = {
        'years': years,
        'categories':categories,
        'indicators':indicators,
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin/list_indicators_csc.html', context)


@login_required
@admin_required
def add_indicator_csc(request):
    selected_year = request.GET.get('ano')
    if request.method == 'POST':
        try:
            nome_indicador = request.POST.get('nome')
            descricao = request.POST.get('composicao')
            ods = request.POST.get('ods_indicador')
            unidade_medida = request.POST.get('unidade_medida')
            opcoes_json = request.POST.get('opcoes_predefinidas')
            categoria_id = request.POST.get('categoria_id')
            ano = YearReference.objects.get(ano=request.POST.get('ano_referencia'))

            categoria = get_object_or_404(CategoryCSC, id=categoria_id)

            lista_limpa_ods = [item.strip() for item in ods.split(',') if item.strip()]

            if not (all([nome_indicador, descricao]) and lista_limpa_ods and lista_limpa_ods != '[]'):
                messages.error(request, 'Todos os campos são obrigatórios')
                return redirect('add_indicator_csc')

            if not (unidade_medida or (opcoes_json and opcoes_json != '[]')):
                messages.error(request, "Defina uma Unidade de Medida ou Adicione Opções Predefinidas.")
                return redirect('add_indicator_csc')

            if FutureIndicatorCSC.objects.filter(nome_indicador=nome_indicador, categoria=categoria_id).exists():
                messages.error(request, 'Já existe um indicador com esse nome.')
                return redirect('add_indicator_csc')

            FutureIndicatorCSC.objects.create(
                nome_indicador=nome_indicador,
                descricao=descricao,
                ods=lista_limpa_ods,
                unidade_medida=unidade_medida,
                opcoes_predefinidas=opcoes_json,
                categoria=categoria,
                ano_referencia=ano
            )

            messages.success(request, f'Indicador {nome_indicador} criado com sucesso!')
            return redirect('list_indicators_csc')

        except Exception as e:
            messages.error(request, f'Erro ao criar indicador: {str(e)}')
            return redirect('add_indicator_csc')
        
    categories = CategoryCSC.objects.all()
        
    context = {
        'selected_year': selected_year,
        'categories': categories,
    }
    return render(request, 'admin/add_indicator_csc.html', context)


@login_required
@admin_required
def edit_indicator_csc(request, indicator_id):
    indicator_to_edit = get_object_or_404(FutureIndicatorCSC, id=indicator_id)

    if request.method == 'POST':
        try:
            nome_indicador = request.POST.get('nome')
            descricao = request.POST.get('composicao')
            ods = request.POST.get('ods_indicador')
            unidade_medida = request.POST.get('unidade_medida')
            opcoes_predefinidas = request.POST.get('opcoes_predefinidas')
            categoria_id = request.POST.get('categoria_id')
            categoria = get_object_or_404(CategoryCSC, id=categoria_id)

            lista_limpa_ods = [item.strip() for item in ods.split(',') if item.strip()]

            if not (all([nome_indicador, descricao]) and lista_limpa_ods and lista_limpa_ods != '[]'):
                messages.error(request, 'Todos os campos são obrigatórios')
                return redirect('edit_indicator', indicator_id=indicator_id)

            if not (unidade_medida or (opcoes_predefinidas and opcoes_predefinidas != '[]')):
                messages.error(request, "Defina uma Unidade de Medida ou Adicione Opções Predefinidas.")
                return redirect('edit_indicator', indicator_id=indicator_id)

            if  FutureIndicatorCSC.objects.filter(nome_indicador=nome_indicador, categoria=categoria_id).exclude(id=indicator_to_edit.id).exists():
                messages.error(request, 'Já existe um indicador com esse nome nessa categoria.')
                return redirect('edit_indicator', indicator_id=indicator_id)


            indicator_to_edit.nome_indicador = nome_indicador
            indicator_to_edit.descricao = descricao
            indicator_to_edit.ods = lista_limpa_ods
            indicator_to_edit.categoria = categoria
            
            if request.POST.get('usar_predefinidos'):
                indicator_to_edit.opcoes_predefinidas = opcoes_predefinidas
                indicator_to_edit.unidade_medida = None
            else:
                indicator_to_edit.unidade_medida = unidade_medida
                indicator_to_edit.opcoes_predefinidas = None

            indicator_to_edit.save()
            messages.success(request, 'Indicador atualizado!')
            return redirect('list_indicators_csc')

        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
            return redirect('edit_indicator_csc', indicator_id=indicator_to_edit.id)

    categories = CategoryCSC.objects.filter(ano_referencia=indicator_to_edit.categoria.ano_referencia)

    context = {
        'indicator_to_edit': indicator_to_edit,
        'categories': categories,
    }
    return render(request, 'admin/edit_indicator_csc.html', context)


@login_required
@admin_required
def delete_indicator_csc(request, indicator_id):
    """Excluir indicador"""
    if request.method == 'POST':
        try:
            indicator_to_delete = get_object_or_404(Indicator, id=indicator_id)
            indicator = indicator_to_delete.nome

            indicator_to_delete.delete()

            return JsonResponse({
                'success': True,
                'message': f'Norma {indicator} excluído com sucesso'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao excluir indicador: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método não permitido'})



@login_required
@admin_required
def get_categories_csc(request, ano):
    categories = CategoryCSC.objects.filter(
        ano_referencia__ano=ano
    ).values('id', 'nome')
    
    return JsonResponse(list(categories), safe=False)


@login_required
@admin_required
@require_POST
def save_category_csc(request, ano_referencia):
    cat_id = request.POST.get('category_id')
    nome = request.POST.get('nome')

    ano_obj = get_object_or_404(YearReference, ano=ano_referencia)
    
    if cat_id:
        # Editar
        cat = get_object_or_404(CategoryCSC, id=cat_id)
        cat.nome = nome
        cat.ano_referencia = ano_obj
        cat.save()
    else:
        # Criar
        CategoryCSC.objects.create(nome=nome, ano_referencia=ano_obj)
        
    return JsonResponse({'status': 'ok'})

@login_required
@admin_required
@require_POST
def delete_category_csc(request, cat_id):
    try:
        category_to_delete = get_object_or_404(CategoryCSC, id=cat_id)
        nome_categoria = category_to_delete.nome
        category_to_delete.delete()
        return JsonResponse({
            'success': True, 
            'message': f'Categoria {nome_categoria} excluída com sucesso'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})






def _get_user_municipality_id(user):
    possible_attrs = [
        'municipio_id', 'municipality_id', 'fk_municipio_id', 'cidade_id',
    ]
    for attr in possible_attrs:
        value = getattr(user, attr, None)
        if value:
            return value

    possible_rel_attrs = [
        'municipio', 'municipality', 'fk_municipio', 'cidade',
    ]
    for attr in possible_rel_attrs:
        value = getattr(user, attr, None)
        if value is not None:
            rel_id = getattr(value, 'id', None)
            if rel_id:
                return rel_id
    return None


def _can_edit_municipality(user, municipality_id):
    user_type = getattr(user, 'user_type', '')
    if user_type == 'ADMIN':
        return True
    if user_type == 'MANAGER':
        return _get_user_municipality_id(user) == municipality_id
    return False



@login_required
def csc_survey_view(request):
    categories = CategoryCSC.objects.filter().order_by('nome')
    indicators = FutureIndicatorCSC.objects.filter(categoria__in=categories)

    indicators_dict = {}
    for cat in categories:
        cat_indicators = indicators.filter(categoria=cat)
        indicators_dict[str(cat.id)] = {
            "key": str(cat.id),
            "name": cat.nome,
            "indicators": [
                {
                    "id": i.id,
                    "name": i.nome_indicador or "",
                    "description": i.descricao or "",
                    "ods": list(i.ods or []),
                    "unit": i.unidade_medida or "",
                    "options": i.opcoes_predefinidas,
                }
                for i in cat_indicators
            ]
        }

    ods_list = indicators.values_list('ods', flat=True)
    lista_ods = set()
    for item in ods_list:
        if item:
            lista_ods.update(item)

    context = {
        'num_categories': categories.count(),
        'num_ods': len(lista_ods),
        'indicators_json': json.dumps(indicators_dict),
        'username': request.user.username,
        'user_type': request.user.user_type,
        'user_municipality_id': _get_user_municipality_id(request.user),
    }
    return render(request, 'csc_survey_view.html', context)


@login_required
def municipality_csc_survey_data(request, municipio_id):
    municipality = get_object_or_404(Municipality, id=municipio_id)

    categories = CategoryCSC.objects.all().order_by('nome')
    indicators_qs = (
        FutureIndicatorCSC.objects
        .filter(categoria__in=categories)
        .select_related('categoria')
        .order_by('categoria__nome', 'nome')
    )
    indicators = list(indicators_qs)

    values = (
        FutureIndicatorValueCSC.objects
        .filter(indicador__in=indicators, municipio=municipality)
        .select_related('indicador', 'indicador__categoria')
    )

    values_by_indicator_id = {value.indicador_id: value for value in values}

    profile_indicators = []
    categories_progress = []
    indicators_payload = []

    principal_total = principal_filled = 0
    apoio_total = apoio_filled = 0

    for category in categories:
        category_indicators = [ind for ind in indicators if ind.categoria_id == category.id]
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

                evidences = EvidencePDFCSC.objects.filter(
                    valor_indicador_ano=value_obj
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
                "name": indicator.nome_indicador or "",
                "description": indicator.descricao or "",
                "ods": list(indicator.ods or []),
                "unit": indicator.unidade_medida or "",
                "value": str(value) if value is not None else "",
                "source": source,
                "attachments": attachments,
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
        })

    return JsonResponse({
        "success": True,
        "municipality": {
            "id": municipality.id,
            "name": municipality.nome,
            "state": municipality.estado,
        },
        "permissions": {
            "user_type": getattr(request.user, 'user_type', ''),
            "user_municipality_id": _get_user_municipality_id(request.user),
            "can_edit": _can_edit_municipality(request.user, municipality.id),
        },
        "indicators": indicators_payload,
        "categories_progress": categories_progress,
    })




@login_required
@require_http_methods(["POST"])
@csrf_exempt
def save_municipality_csc_survey_indicator_value(request, norm_id, municipio_id, indicator_id):
    municipality = get_object_or_404(Municipality, id=municipio_id)
    indicator = get_object_or_404(Indicator, id=indicator_id, categoria__norma_iso_id=norm_id)

    if not _can_edit_municipality(request.user, municipality.id):
        return JsonResponse({
            'success': False,
            'message': 'Você não tem permissão para preencher indicadores deste município.'
        }, status=403)

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        payload = {}

    value = payload.get('value', '')
    source = payload.get('source', '')

    defaults = {
        'fonte': source or None,
        'valor_texto': None,
        'valor_numerico': None,
    }

    if value not in [None, '']:
        value_str = str(value).strip()
        try:
            defaults['valor_numerico'] = value_str
        except Exception:
            defaults['valor_texto'] = value_str

    IndicatorValueYear.objects.update_or_create(
        indicador=indicator,
        municipio=municipality,
        defaults=defaults
    )

    return JsonResponse({
        'success': True,
        'message': 'Indicador salvo com sucesso.'
    })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def upload_municipality_csc_survey_indicator_attachment(request, norm_id, municipio_id, indicator_id):
    municipality = get_object_or_404(Municipality, id=municipio_id)
    indicator = get_object_or_404(
        Indicator,
        id=indicator_id,
        categoria__norma_iso_id=norm_id
    )

    if not _can_edit_municipality(request.user, municipality.id):
        return JsonResponse(
            {'success': False, 'message': 'Sem permissão.'},
            status=403
        )

    files = request.FILES.getlist('anexos')
    if not files:
        single_file = request.FILES.get('anexo')
        if single_file:
            files = [single_file]

    if not files:
        return JsonResponse(
            {'success': False, 'message': 'Nenhum arquivo enviado.'},
            status=400
        )

    indicator_value, _ = IndicatorValueYear.objects.get_or_create(
        indicador=indicator,
        municipio=municipality
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
            caminho_arquivo=file_url
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
@csrf_exempt
def delete_municipality_csc_survey_indicator_attachment(request, norm_id, municipio_id, indicator_id, attachment_id):
    municipality = get_object_or_404(Municipality, id=municipio_id)
    indicator = get_object_or_404(
        Indicator,
        id=indicator_id,
        categoria__norma_iso_id=norm_id
    )

    if not _can_edit_municipality(request.user, municipality.id):
        return JsonResponse(
            {'success': False, 'message': 'Sem permissão.'},
            status=403
        )

    indicator_value = get_object_or_404(
        IndicatorValueYear,
        indicador=indicator,
        municipio=municipality
    )

    evidence = get_object_or_404(
        EvidencePDF,
        id=attachment_id,
        valor_indicador_ano=indicator_value
    )

    file_path = evidence.caminho_arquivo.replace('/media/', '', 1) if evidence.caminho_arquivo else None
    if file_path and default_storage.exists(file_path):
        default_storage.delete(file_path)

    evidence.delete()

    return JsonResponse({
        'success': True,
        'message': 'Anexo removido com sucesso.'
    })



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
