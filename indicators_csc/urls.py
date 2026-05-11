from django.urls import path
from . import views

urlpatterns = [
    # Admin - Gerenciamento de Indicadores futuros CSC (apenas para administradores)
    path('dashboard/admin/levantamento-csc/indicators/', views.list_indicators_csc, name='list_indicators_csc'),
    path('dashboard/admin/levantamento-csc/indicators/add/', views.add_indicator_csc, name='add_indicator_csc'),
    path('dashboard/admin/levantamento-csc/indicators/<int:indicator_id>/edit/', views.edit_indicator_csc, name='edit_indicator_csc'),
    path('dashboard/admin/levantamento-csc/indicators/<int:indicator_id>/delete/', views.delete_indicator_csc, name='delete_indicator_csc'),

    # Admin - Gerenciamento de Categorias dos Indicadores Futuros CSC (apenas para administradores)
    path('dashboard/admin/levantamento-csc/categories/get/<int:ano>/', views.get_categories_csc, name='get_categories_csc'),
    path('dashboard/admin/levantamento-csc/categories/save/<int:ano_referencia>/', views.save_category_csc, name='save_category_csc'),
    path('dashboard/admin/levantamento-csc/categories/delete/<int:cat_id>/', views.delete_category_csc, name='delete_category_csc'),

    # Rotas protegidas (requerem login)
    path('dashboard/levantamento-csc/', views.csc_survey_view, name='csc_survey_view'),

    #APIs para buscar municipios e estados
    path('dashboard/api/estados/', views.list_states, name='list_states'),
    path('dashboard/api/municipios/', views.list_municipalities, name='list_municipalities'),

    #APIs
    path('dashboard/api/levantamento-csc/<int:ano_referencia>/municipios/<int:municipio_id>/', 
    views.municipality_csc_survey_data, name='municipality_csc_survey_data'),
    path('dashboard/api/levantamento-csc/<int:ano_referencia>/municipios/<int:municipio_id>/indicadores/<int:indicator_id>/save/', 
    views.save_municipality_csc_survey_indicator_value, name='save_municipality_csc_survey_indicator_value'),
    path('dashboard/api/levantamento-csc/<int:ano_referencia>/municipios/<int:municipio_id>/indicadores/<int:indicator_id>/upload-anexo/',
    views.upload_municipality_csc_survey_indicator_attachment,name='upload_municipality_csc_survey_indicator_attachment'),
    path('dashboard/api/levantamento-csc/<int:ano_referencia>/municipios/<int:municipio_id>/indicadores/<int:indicator_id>/anexos/<int:attachment_id>/delete/',
    views.delete_municipality_csc_survey_indicator_attachment,name='delete_municipality_csc_survey_indicator_attachment'),

]
