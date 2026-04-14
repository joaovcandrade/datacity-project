from django.urls import path
from . import views

urlpatterns = [
    # Rotas públicas
    # path('register/', views.register, name='register'),  # Rota de cadastro desabilitada
    path('login/', views.login, name='login'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('verify-code/', views.verify_and_change_password, name='verify_code'),
    path('primeiro-acesso/', views.first_access, name='first_access'),
    path('', views.landing, name='landing'),
    path('saiba-mais/', views.saiba_mais, name='saiba_mais'),

    # Rotas protegidas (requerem login)
    path('dashboard/', views.menu, name='index'),
    path('dashboard/menu/', views.menu, name='menu'),
    path('dashboard/dimensoes/', views.dimensoes, name='dimensoes'),

    path('dashboard/plataformas/', views.plataformas, name='plataformas'),
    path('dashboard/plataformas/csc/', views.csc, name='csc'),
    path('dashboard/plataformas/inteligente/', views.inteligente, name='inteligente'),
    path('dashboard/normas/iso37120/', views.iso37120, name='iso37120'),
    path('dashboard/indicadores/', views.indicadores, name='indicadores'),
    path('dashboard/indicadores/<str:dimensao_id>/', views.indicadores, name='indicadores_dimensao'),
    path('logout/', views.logout, name='logout'),




    # Admin - Gerenciamento de Usuários (apenas para administradores)
    path('dashboard/admin/', views.admin_menu, name='admin_menu'),
    path('dashboard/admin/users/', views.list_users, name='list_users'),
    path('dashboard/admin/users/add/', views.add_user, name='add_user'),
    path('dashboard/admin/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('dashboard/admin/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('dashboard/admin/users/<int:user_id>/change-role/', views.change_user_role, name='change_user_role'),

    # Admin - Gerenciamento de Anos (apenas para administradores)
    path('dashboard/admin/years/', views.list_years, name='list_years'),
    path('dashboard/admin/years/add/', views.add_year, name='add_year'),
    path('dashboard/admin/years/<int:year_id>/change-status/', views.change_year_status, name='change_year_status'),

    #APIs para buscar municipios e estados
    path('dashboard/api/estados/', views.list_states, name='list_states'),
    path('dashboard/api/municipios/', views.list_municipalities, name='list_municipalities'),





    
    # APIs para dimensões
    path('dashboard/api/dimensoes/', views.api_dimensoes, name='api_dimensoes'),
    path('dashboard/api/dimensoes/criar/', views.criar_dimensao, name='criar_dimensao'),
    path('dashboard/api/dimensoes/<str:dimensao_id>/editar/', views.editar_dimensao, name='editar_dimensao'),
    path('dashboard/api/dimensoes/<str:dimensao_id>/remover/', views.remover_dimensao, name='remover_dimensao'),
    
    # APIs para indicadores
    path('dashboard/api/indicadores/<str:dimensao_id>/', views.api_indicadores, name='api_indicadores'),
    path('dashboard/api/indicadores/<str:dimensao_id>/adicionar/', views.adicionar_indicador, name='adicionar_indicador'),
    path('dashboard/api/indicadores/<str:dimensao_id>/<str:indicador_id>/editar/', views.editar_indicador, name='editar_indicador'),
    path('dashboard/api/indicadores/<str:dimensao_id>/<str:indicador_id>/excluir/', views.excluir_indicador, name='excluir_indicador'),
    
    # API para relatórios
    path('dashboard/api/relatorio/<str:dimensao_id>/', views.gerar_relatorio, name='gerar_relatorio'),
    
    # Arquivos estáticos
    path('static/<path:path>', views.serve_static, name='serve_static'),

    # Outras rotas protegidas
    path('dashboard/indicador/<str:dimensao_id>/<int:indicador_id>/', views.indicador_detalhes, name='indicador_detalhes'),

    # Modais
    path('dashboard/modals/dimensoes/', views.modal_dimensoes, name='modal-dimensoes'),
    path('dashboard/modals/indicadores/', views.modal_indicadores, name='modal-indicadores'),

    # APIs para plataformas
    path('dashboard/plataformas/adicionar/', views.adicionar_plataforma, name='adicionar_plataforma'),
    path('dashboard/plataformas/editar/<int:platform_id>/', views.editar_plataforma, name='editar_plataforma'),
    path('dashboard/plataformas/remover/<int:platform_id>/', views.remover_plataforma, name='remover_plataforma'),
    path('dashboard/plataformas/listar/', views.listar_plataformas, name='listar_plataformas'),


    # APIs para ISO37120
    path('dashboard/api/iso37120/save/', views.save_iso37120_data, name='save_iso37120_data'),
    path('dashboard/api/iso37120/get/', views.get_iso37120_data, name='get_iso37120_data'),
    path('dashboard/api/iso37120/update_field/', views.update_iso37120_field, name='update_iso37120_field'),
    path('dashboard/api/iso37120/upload_anexo/', views.upload_iso37120_anexo, name='upload_iso37120_anexo'),
    path('dashboard/api/iso37120/delete_anexo/', views.delete_iso37120_anexo, name='delete_iso37120_anexo'),

    
]
