from django.urls import path
from . import views

urlpatterns = [
    # Admin - Gerenciamento de Normas ISO (apenas para administradores)
    path('dashboard/admin/norms/', views.list_norms, name='list_norms'),
    path('dashboard/admin/norms/add/', views.add_norm, name='add_norm'),
    path('dashboard/admin/norms/<int:norm_id>/edit/', views.edit_norm, name='edit_norm'),
    path('dashboard/admin/norms/<int:norm_id>/delete/', views.delete_norm, name='delete_norm'),
    path('dashboard/admin/norms/<int:norm_id>/check-related-records/', views.check_related_records, name='check_related_records'),

    #Admin - Gerenciamento de Plataformas (apenas para administradores)
    path('dashboard/admin/plataforms/', views.list_platforms, name='list_platforms'),
    path('dashboard/admin/plataforms/add/', views.add_platform, name='add_platform'),
    path('dashboard/admin/plataforms/<int:plataform_id>/edit/', views.edit_platform, name='edit_platform'),
    path('dashboard/admin/plataforms/<int:plataform_id>/delete/', views.delete_platform, name='delete_platform'),
    path('dashboard/admin/plataforms/<int:plataform_id>/check-related-records/', views.check_related_records_platform, name='check_related_records_platform'),

    # Admin - Gerenciamento de Indicadores (apenas para administradores)
    path('dashboard/admin/indicators/', views.list_indicators, name='list_indicators'),
    path('dashboard/admin/indicators/norma/<int:norm_id>/', views.list_indicators, name='list_indicators_by_norm'),
    path('dashboard/admin/indicators/add/', views.add_indicator, name='add_indicator'),
    path('dashboard/admin/indicators/norma/<int:norm_id>/add/', views.add_indicator, name='add_indicator_by_norm'),
    path('dashboard/admin/indicators/categories-by-context/', views.indicator_categories_by_context, name='indicator_categories_by_context'),
    path('dashboard/admin/indicators/<int:indicator_id>/edit/', views.edit_indicator, name='edit_indicator'),
    path('dashboard/admin/indicators/<int:indicator_id>/delete/', views.delete_indicator, name='delete_indicator'),
    
    # Admin - Gerenciamento de Categorias da Norma selecionada (apenas para administradores)
    path('dashboard/admin/categories/get/<int:ano>/', views.get_categories, name='get_categories'),
    path('dashboard/admin/categories/save/', views.save_category, name='save_category'),
    path('dashboard/admin/categories/delete/<int:cat_id>/', views.delete_category, name='delete_category'),
    path('dashboard/admin/categories/get-norms-platforms/<int:ano>/', views.get_norms_and_platforms, name='get_norms_and_platforms'),

    # Admin - Gerenciamento de Certificações da Norma selecionada (apenas para administradores)
    path('dashboard/admin/certifications/get/<int:norma_id>/', views.get_certifications, name='get_certifications'),
    path('dashboard/admin/certifications/save/', views.save_certification, name='save_certification'),
    path('dashboard/admin/certifications/delete/<int:cert_id>/', views.delete_certification, name='delete_certification'),

    # Rotas protegidas (requerem login)
    path('dashboard/normas/', views.normas, name='normas'),
    path('dashboard/normas/<int:norm_id>/<str:codigo_norma>/', views.iso_view, name='iso_view'),

    #APIs para buscar municipios e estados
    path('dashboard/dashboard/api/estados/', views.list_states, name='list_states'),
    path('dashboard/dashboard/api/municipios/', views.list_municipalities, name='list_municipalities'),
    

    #APIs para Normas
    path('dashboard/api/normas/<int:norm_id>/municipios/<int:municipio_id>/', views.municipality_norm_data, name='municipality_norm_data'),
    path('dashboard/api/normas/<int:norm_id>/municipios/<int:municipio_id>/indicadores/<int:indicator_id>/save/', views.save_municipality_indicator_value, name='save_municipality_indicator_value'),
    path('dashboard/api/normas/<int:norm_id>/municipios/<int:municipio_id>/indicadores/<int:indicator_id>/upload-anexo/',
    views.upload_municipality_indicator_attachment,name='upload_municipality_indicator_attachment'),
    path('dashboard/api/normas/<int:norm_id>/municipios/<int:municipio_id>/indicadores/<int:indicator_id>/anexos/<int:attachment_id>/delete/',
    views.delete_municipality_indicator_attachment,name='delete_municipality_indicator_attachment'),

    # Pontuações, metas e consulta de cidades por plataforma
    path('dashboard/completions-goals/', views.completions_goals_home, name='completions_goals_home'),
    path('dashboard/completions-goals/platform/<int:platform_id>/', views.completions_goals_platform, name='completions_goals_platform'),
    path('dashboard/completions-goals/platform/<int:platform_id>/goal-reference/', views.save_platform_goal_reference, name='save_platform_goal_reference'),
    path('dashboard/completions-goals/platform/<int:platform_id>/indicator/<int:indicator_id>/save/', views.save_platform_indicator_completion, name='save_platform_indicator_completion'),
    path('dashboard/completions-goals/platform/<int:platform_id>/indicator/<int:indicator_id>/attachment/<int:attachment_id>/delete/', views.delete_platform_indicator_attachment, name='delete_platform_indicator_attachment'),



    path("ranking-iso/", views.ranking_iso_view, name="ranking_iso"),
    path("consulta-cidade/<str:uf>/<int:municipio_id>/", views.consulta_cidade_view, name="consulta_cidade"),
    path("ranking-iso/atualizar/", views.atualizar_ranking_iso_view, name="atualizar_ranking_iso"),
]
