from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from accounts.models import YearReference, NormISO, Certification, Category, Indicator, IndicatorCategory, IndicatorValueYear
import os
from django.conf import settings
from django.utils import timezone
import mimetypes
from pathlib import Path
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from accounts.decorators import admin_required, manager_required
from django.db import transaction

# Create your views here.
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
    return render(request, 'admin/list_years.html', context)


@login_required
@admin_required
def add_year(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                last_year_obj = YearReference.objects.order_by('-ano').first()
                new_year_val = (last_year_obj.ano + 1) if last_year_obj else 2022
                
                new_year = YearReference.objects.create(ano=new_year_val, ativo=True)
                
                if last_year_obj:
                    norm_map = {}
                    cat_map = {}

                    # Clonar Normas ISO
                    norms = NormISO.objects.filter(ano_referencia=last_year_obj)
                    for norm in norms:
                        old_id = norm.pk
                        norm.pk = None
                        norm.ano_referencia = new_year
                        norm.save()
                        norm_map[old_id] = norm

                    # Clonar Certificações vinculadas à nova norma
                    for old_id, new_norm in norm_map.items():
                        certs = Certification.objects.filter(norma_iso_id=old_id)
                        for cert in certs:
                            cert.pk = None
                            cert.norma_iso = new_norm
                            cert.save()

                    # Clonar Categorias
                    categories = Category.objects.filter(norma_iso_id__in=norm_map.keys())
                    for cat in categories:
                        old_cat_id = cat.pk
                        old_norm_id = cat.norma_iso_id
                        cat.pk = None
                        cat.norma_iso = norm_map[old_norm_id]
                        cat.save()
                        cat_map[old_cat_id] = cat

                    # Clonar Indicadores
                    indicators = Indicator.objects.filter(categorias__in=cat_map.keys())
                    for ind in indicators:
                        old_cat_id = ind.categoria_id
                        ind.pk = None
                        ind.categoria = cat_map[old_cat_id]
                        ind.save()

            messages.success(request, f"Ano {new_year} adicionado com sucesso!")
            return redirect('list_years')
            
        except Exception as e:
            messages.error(request, f"Erro ao criar ano: {str(e)}")
            return redirect('list_years')

    return render(request, 'admin/list_years.html')


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
