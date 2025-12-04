from django.urls import path
from . import views

urlpatterns = [
    # Rotas públicas
    # path('register/', views.register, name='register'),  # Rota de cadastro desabilitada
    path('login/', views.login, name='login'),
    path('', views.landing, name='landing'),
    path('saiba-mais/', views.saiba_mais, name='saiba_mais'),

    # Rotas protegidas (requerem login)
    path('dashboard/', views.menu, name='index'),
    path('dashboard/menu/', views.menu, name='menu'),
    path('dashboard/dimensoes/', views.dimensoes, name='dimensoes'),
    path('dashboard/normas/', views.normas, name='normas'),
    path('dashboard/plataformas/', views.plataformas, name='plataformas'),
    path('dashboard/plataformas/csc/', views.csc, name='csc'),
    path('dashboard/plataformas/inteligente/', views.inteligente, name='inteligente'),
    path('dashboard/normas/iso37120/', views.iso37120, name='iso37120'),
    path('dashboard/normas/iso37122/', views.iso37122, name='iso37122'),
    path('dashboard/normas/iso37123/', views.iso37123, name='iso37123'),
    path('dashboard/normas/iso37125/', views.iso37125, name='iso37125'),
    path('dashboard/indicadores/', views.indicadores, name='indicadores'),
    path('dashboard/indicadores/<str:dimensao_id>/', views.indicadores, name='indicadores_dimensao'),
    
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
    path('logout/', views.logout, name='logout'),

    # Admin - Gerenciamento de Usuários (apenas para administradores)
    path('dashboard/admin/', views.admin_menu, name='admin_menu'),
    path('dashboard/admin/users/', views.list_users, name='list_users'),
    path('dashboard/admin/users/add/', views.add_user, name='add_user'),
    path('dashboard/admin/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('dashboard/admin/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('dashboard/admin/users/<int:user_id>/change-role/', views.change_user_role, name='change_user_role'),

    # Modais
    path('dashboard/modals/dimensoes/', views.modal_dimensoes, name='modal-dimensoes'),
    path('dashboard/modals/indicadores/', views.modal_indicadores, name='modal-indicadores'),

    # APIs para plataformas
    path('dashboard/plataformas/adicionar/', views.adicionar_plataforma, name='adicionar_plataforma'),
    path('dashboard/plataformas/editar/<int:platform_id>/', views.editar_plataforma, name='editar_plataforma'),
    path('dashboard/plataformas/remover/<int:platform_id>/', views.remover_plataforma, name='remover_plataforma'),
    path('dashboard/plataformas/listar/', views.listar_plataformas, name='listar_plataformas'),

    # APIs para normas
    path('dashboard/normas/adicionar_norma/', views.adicionar_norma, name='adicionar_norma'),
    path('dashboard/normas/editar_norma/<int:norm_id>/', views.editar_norma, name='editar_norma'),
    path('dashboard/normas/remover_norma/<int:norm_id>/', views.remover_norma, name='remover_norma'),
    path('dashboard/normas/listar_normas/', views.listar_normas, name='listar_normas'),

    # APIs para ISO37120
    path('dashboard/api/iso37120/save/', views.save_iso37120_data, name='save_iso37120_data'),
    path('dashboard/api/iso37120/get/', views.get_iso37120_data, name='get_iso37120_data'),
    path('dashboard/api/iso37120/update_field/', views.update_iso37120_field, name='update_iso37120_field'),
    path('dashboard/api/iso37120/upload_anexo/', views.upload_iso37120_anexo, name='upload_iso37120_anexo'),
    path('dashboard/api/iso37120/delete_anexo/', views.delete_iso37120_anexo, name='delete_iso37120_anexo'),

    # APIs para ISO37122
    path('dashboard/api/iso37122/save/', views.save_iso37122_data, name='save_iso37122_data'),
    path('dashboard/api/iso37122/get/', views.get_iso37122_data, name='get_iso37122_data'),
    path('dashboard/api/iso37122/update_field/', views.update_iso37122_field, name='update_iso37122_field'),
    path('dashboard/api/iso37122/upload_anexo/', views.upload_iso37122_anexo, name='upload_iso37122_anexo'),
    path('dashboard/api/iso37122/delete_anexo/', views.delete_iso37122_anexo, name='delete_iso37122_anexo'),

    # APIs para ISO37123
    path('dashboard/api/iso37123/save/', views.save_iso37123_data, name='save_iso37123_data'),
    path('dashboard/api/iso37123/get/', views.get_iso37123_data, name='get_iso37123_data'),
    path('dashboard/api/iso37123/update_field/', views.update_iso37123_field, name='update_iso37123_field'),
    path('dashboard/api/iso37123/upload_anexo/', views.upload_iso37123_anexo, name='upload_iso37123_anexo'),
    path('dashboard/api/iso37123/delete_anexo/', views.delete_iso37123_anexo, name='delete_iso37123_anexo'),

    # APIs para ISO37125
    path('dashboard/api/iso37125/save/', views.save_iso37125_data, name='save_iso37125_data'),
    path('dashboard/api/iso37125/get/', views.get_iso37125_data, name='get_iso37125_data'),
    path('dashboard/api/iso37125/update_field/', views.update_iso37125_field, name='update_iso37125_field'),
    path('dashboard/api/iso37125/upload_anexo/', views.upload_iso37125_anexo, name='upload_iso37125_anexo'),
    path('dashboard/api/iso37125/delete_anexo/', views.delete_iso37125_anexo, name='delete_iso37125_anexo'),
]
