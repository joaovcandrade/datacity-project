from django.urls import path
from . import views

urlpatterns = [
    # Admin - Gerenciamento de Normas ISO (apenas para administradores)
    path('dashboard/admin/norms/', views.list_norms, name='list_norms'),
    path('dashboard/admin/norms/add/', views.add_norm, name='add_norm'),
    path('dashboard/admin/norms/<int:norm_id>/edit/', views.edit_norm, name='edit_norm'),
    path('dashboard/admin/norms/<int:norm_id>/delete/', views.delete_norm, name='delete_norm'),
    path('dashboard/admin/norms/<int:norm_id>/check-related-records/', views.check_related_records, name='check_related_records'),


    # Admin - Gerenciamento de Indicadores (apenas para administradores)
    path('dashboard/admin/indicators/<int:norm_id>/', views.list_indicators, name='list_indicators'),
    path('dashboard/admin/indicators/add/<int:norm_id>/', views.add_indicator, name='add_indicator'),
    path('dashboard/admin/indicators/<int:indicator_id>/edit/', views.edit_indicator, name='edit_indicator'),
    path('dashboard/admin/indicators/<int:indicator_id>/delete/', views.delete_indicator, name='delete_indicator'),

    # Admin - Gerenciamento de Categorias da Norma selecionada (apenas para administradores)
    path('dashboard/admin/categories/get/<int:norma_id>/', views.get_categories, name='get_categories'),
    path('dashboard/admin/categories/save/', views.save_category, name='save_category'),
    path('dashboard/admin/categories/delete/<int:cat_id>/', views.delete_category, name='delete_category'),

    # Admin - Gerenciamento de Certificações da Norma selecionada (apenas para administradores)
    path('dashboard/admin/certifications/get/<int:norma_id>/', views.get_certifications, name='get_certifications'),
    path('dashboard/admin/certifications/save/', views.save_certification, name='save_certification'),
    path('dashboard/admin/certifications/delete/<int:cert_id>/', views.delete_certification, name='delete_certification'),

    # Rotas protegidas (requerem login)
    path('dashboard/normas/', views.normas, name='normas'),
    path('dashboard/normas/<int:norm_id>/<str:codigo_norma>/', views.iso_view, name='iso_view'),

    #APIs para buscar municipios e estados
    path('dashboard/api/estados/', views.list_states, name='list_states'),
    path('dashboard/api/municipios/', views.list_municipalities, name='list_municipalities'),
    

    #APIs para Normas
    path('dashboard/api/normas/<int:norm_id>/municipios/<int:municipio_id>/', views.municipality_norm_data, name='municipality_norm_data'),
    path('dashboard/api/normas/<int:norm_id>/municipios/<int:municipio_id>/indicadores/<int:indicator_id>/save/', views.save_municipality_indicator_value, name='save_municipality_indicator_value'),
    path('dashboard/api/normas/<int:norm_id>/municipios/<int:municipio_id>/indicadores/<int:indicator_id>/upload-anexo/',
    views.upload_municipality_indicator_attachment,name='upload_municipality_indicator_attachment'),
    path('dashboard/api/normas/<int:norm_id>/municipios/<int:municipio_id>/indicadores/<int:indicator_id>/anexos/<int:attachment_id>/delete/',
    views.delete_municipality_indicator_attachment,name='delete_municipality_indicator_attachment'),

]
