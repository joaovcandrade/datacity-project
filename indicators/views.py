from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from accounts.models import Indicator, YearReference, NormISO, IndicatorValueYear, Category, EvidencePDF, User, Municipality, Certification
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
def list_norms(request):
    """Listar todos as normas ISO cadastrados do sistema"""

    norms_list = NormISO.objects.all().order_by('codigo_norma')
    years = YearReference.objects.all().filter(ativo=True)

    context = {
        'years':years,
        'norms_list': norms_list,
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin/list_norms.html', context)


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
     return render(request, 'admin/add_norm.html', context)


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
    return render(request, 'admin/edit_norm.html', context)


@login_required
@admin_required
def delete_norm(request, norm_id):
    """Excluir norma"""
    if request.method == 'POST':
        try:

            norm_to_delete = get_object_or_404(NormISO, id=norm_id)
            norm = norm_to_delete.codigo_norma
            categories = Category.objects.filter(norma_iso=norm_id)
            indicators = Indicator.objects.filter(categoria__in=categories)
            values_indicators = IndicatorValueYear.objects.filter(indicador__in=indicators)

            values_indicators.delete()
            indicators.delete()
            categories.delete()
            
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
    exists_indicators = Indicator.objects.filter(categoria__norma_iso_id=norm_id).exists()
    exists_indicator_values = IndicatorValueYear.objects.filter(indicador__categoria__norma_iso=norm_id).exists()
    return JsonResponse({
        'has_categories': exists_categories,
        'has_indicators': exists_indicators,
        'exists_indicator_values': exists_indicator_values
    })





@login_required
@admin_required
def list_indicators(request, norm_id):
    """Listar todos os indicadores, da norma ISO selecionada, cadastrados do sistema"""

    norm = get_object_or_404(NormISO, id=norm_id)
    categories = Category.objects.filter(norma_iso=norm).order_by('nome')
    indicators = Indicator.objects.filter(categoria__in=categories).order_by('nome')     

    context = {
        'categories':categories,
        'indicators':indicators,
        'norm': norm,
        'username': request.user.username,
        'user_type': request.user.user_type,
    }
    return render(request, 'admin/list_indicators.html', context)


@login_required
@admin_required
def add_indicator(request, norm_id):
    if request.method == 'POST':
        try:
            nome = request.POST.get('nome')
            tipo = request.POST.get('tipo_indicador')
            ods = request.POST.get('ods_indicador')
            unidade_medida = request.POST.get('unidade_medida')
            opcoes_json = request.POST.get('opcoes_predefinidas')
            categoria_id = request.POST.get('categoria_id')
            direcao_melhoria = request.POST.get('direcao_melhoria')

            categoria = get_object_or_404(Category, id=categoria_id)

            lista_limpa_ods = [item.strip() for item in ods.split(',') if item.strip()]

            if not (all([nome, tipo, direcao_melhoria]) and lista_limpa_ods and lista_limpa_ods != '[]'):
                messages.error(request, 'Todos os campos são obrigatórios')
                return redirect('add_indicator', norm_id=norm_id)

            if not (unidade_medida or (opcoes_json and opcoes_json != '[]')):
                messages.error(request, "Defina uma Unidade de Medida ou Adicione Opções Predefinidas.")
                return redirect('add_indicator', norm_id=norm_id)

            if Indicator.objects.filter(nome=nome, categoria=categoria_id).exists():
                messages.error(request, 'Já existe um indicador com esse nome nessa norma.')
                return redirect('add_indicator', norm_id=norm_id)

            Indicator.objects.create(
                nome=nome,
                tipo=tipo,
                ods=lista_limpa_ods,
                unidade_medida=unidade_medida,
                opcoes_predefinidas=opcoes_json,
                categoria=categoria,
                direcao_melhoria=direcao_melhoria
            )

            messages.success(request, f'Indicador {nome} criado com sucesso!')
            return redirect('list_indicators', norm_id=norm_id)

        except Exception as e:
            messages.error(request, f'Erro ao criar indicador: {str(e)}')
            return redirect('add_indicator', norm_id=norm_id)
        
    selected_norm = get_object_or_404(NormISO, id=norm_id)
    categories = Category.objects.filter(norma_iso=selected_norm)
        
    context = {
        'selected_norm': selected_norm,
        'categories': categories,
    }
    return render(request, 'admin/add_indicator.html', context)


@login_required
@admin_required
def edit_indicator(request, indicator_id):
    indicator_to_edit = get_object_or_404(Indicator, id=indicator_id)

    if request.method == 'POST':
        try:
            nome = request.POST.get('nome')
            tipo = request.POST.get('tipo_indicador')
            ods = request.POST.get('ods_indicador')
            unidade_medida = request.POST.get('unidade_medida')
            opcoes_predefinidas = request.POST.get('opcoes_predefinidas')
            categoria_id = request.POST.get('categoria_id')
            categoria = get_object_or_404(Category, id=categoria_id)
            direcao_melhoria = request.POST.get('direcao_melhoria')

            lista_limpa_ods = [item.strip() for item in ods.split(',') if item.strip()]

            if not (all([nome, tipo, direcao_melhoria]) and lista_limpa_ods and lista_limpa_ods != '[]'):
                messages.error(request, 'Todos os campos são obrigatórios')
                return redirect('edit_indicator', indicator_id=indicator_id)

            if not (unidade_medida or (opcoes_predefinidas and opcoes_predefinidas != '[]')):
                messages.error(request, "Defina uma Unidade de Medida ou Adicione Opções Predefinidas.")
                return redirect('edit_indicator', indicator_id=indicator_id)

            if Indicator.objects.filter(nome=nome, categoria=categoria_id).exclude(id=indicator_to_edit.id).exists():
                messages.error(request, 'Já existe um indicador com esse nome nessa categoria.')
                return redirect('edit_indicator', indicator_id=indicator_id)


            indicator_to_edit.nome = nome
            indicator_to_edit.tipo = tipo
            indicator_to_edit.ods = lista_limpa_ods
            indicator_to_edit.categoria = categoria
            indicator_to_edit.direcao_melhoria = direcao_melhoria
            
            if request.POST.get('usar_predefinidos'):
                indicator_to_edit.opcoes_predefinidas = opcoes_predefinidas
                indicator_to_edit.unidade_medida = None
            else:
                indicator_to_edit.unidade_medida = unidade_medida
                indicator_to_edit.opcoes_predefinidas = None

            indicator_to_edit.save()
            messages.success(request, 'Indicador atualizado!')
            return redirect('list_indicators', norm_id=Category.objects.get(id=categoria_id).norma_iso.id)

        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
            return redirect('edit_indicator', indicator_id=indicator_to_edit.id)

    categories = Category.objects.filter(norma_iso=Category.objects.get(id=indicator_to_edit.categoria.id).norma_iso)
    selected_norm = Category.objects.get(id=indicator_to_edit.categoria.id).norma_iso

    context = {
        'selected_norm' : selected_norm,
        'indicator_to_edit': indicator_to_edit,
        'categories': categories,
    }
    return render(request, 'admin/edit_indicator.html', context)


@login_required
@admin_required
def delete_indicator(request, indicator_id):
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
def get_categories(request, norma_id):
    categories = Category.objects.filter(norma_iso_id=norma_id).values('id', 'nome', 'descricao')
    return JsonResponse(list(categories), safe=False)


@login_required
@admin_required
@require_POST
def save_category(request):
    cat_id = request.POST.get('category_id')
    norma_id = request.POST.get('norma_iso_id')
    nome = request.POST.get('nome')
    desc = request.POST.get('descricao')

    if cat_id: # Editar
        cat = Category.objects.get(id=cat_id)
        cat.nome, cat.descricao = nome, desc
        cat.save()
    else: # Criar
        Category.objects.create(nome=nome, descricao=desc, norma_iso_id=norma_id)
    
    return JsonResponse({'status': 'ok'})


@login_required
@admin_required
@require_POST
def delete_category(request, cat_id):
    if request.method == 'POST':
        try:
            category_to_delete = Category.objects.filter(id=cat_id)
            category_to_delete.delete()

            return JsonResponse({
                    'success': True,
                    'message': f'Categoria {category_to_delete.nome} excluída com sucesso'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao excluir categoria: {str(e)}'
            })
    return JsonResponse({'success': False, 'message': 'Método não permitido'})



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
    categories = Category.objects.filter(norma_iso=norm).order_by('nome')
    indicators = Indicator.objects.filter(categoria__in=categories)

    indicators_dict = {}
    for cat in categories:
        cat_indicators = indicators.filter(categoria=cat)
        indicators_dict[str(cat.id)] = {
            "key": str(cat.id),
            "name": cat.nome,
            "description": cat.descricao or "",
            "indicators": [
                {
                    "id": i.id,
                    "name": i.nome or "",
                    "description": i.descricao or "",
                    "type": i.tipo,
                    "ods": list(i.ods or []),
                    "unit": i.unidade_medida or "",
                    "options": i.opcoes_predefinidas,
                    "improvement_direction": i.direcao_melhoria,
                }
                for i in cat_indicators
            ]
        }

    num_main_indicators = indicators.filter(tipo='PRINCIPAL').count()
    num_support_indicators = indicators.filter(tipo='APOIO').count()
    num_profile_indicators = indicators.filter(tipo='PERFIL').count()

    ods_list = indicators.values_list('ods', flat=True)
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
        'num_categories': categories.count(),
        'num_ods': len(lista_ods),
        'indicators_json': json.dumps(indicators_dict),
        'username': request.user.username,
        'user_type': request.user.user_type,
        'user_municipality_id': _get_user_municipality_id(request.user),
        'norms_json': json.dumps([
            {
                'id': item.id,
                'year': item.ano_referencia.ano,
                'code': item.codigo_norma,
            }
            for item in norms
        ]),
        'current_norm_year': norm.ano_referencia.ano,
    }
    return render(request, 'normas/iso_view.html', context)


@login_required
def municipality_norm_data(request, norm_id, municipio_id):
    norm = get_object_or_404(NormISO, id=norm_id)
    municipality = get_object_or_404(Municipality, id=municipio_id)

    categories = Category.objects.filter(norma_iso=norm).order_by('nome')
    indicators_qs = (
        Indicator.objects
        .filter(categoria__in=categories)
        .select_related('categoria')
        .order_by('categoria__nome', 'nome')
    )
    indicators = list(indicators_qs)

    values = (
        IndicatorValueYear.objects
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

                evidences = EvidencePDF.objects.filter(
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
                "name": indicator.nome or "",
                "description": indicator.descricao or "",
                "type": indicator.tipo,
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
        "norm": {
            "id": norm.id,
            "code": norm.codigo_norma,
            "year": norm.ano_referencia.ano,
        },
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




@login_required
@require_http_methods(["POST"])
@csrf_exempt
def save_municipality_indicator_value(request, norm_id, municipio_id, indicator_id):
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
def upload_municipality_indicator_attachment(request, norm_id, municipio_id, indicator_id):
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
def delete_municipality_indicator_attachment(request, norm_id, municipio_id, indicator_id, attachment_id):
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
