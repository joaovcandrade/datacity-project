from django.urls import path
from . import views

urlpatterns = [
    # Rotas públicas
    path('login/', views.login, name='login'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('verify-code/', views.verify_and_change_password, name='verify_code'),
    path('primeiro-acesso/', views.first_access, name='first_access'),
    path('', views.landing, name='landing'),
    path('saiba-mais/', views.saiba_mais, name='saiba_mais'),
    path('logout/', views.logout, name='logout'),

    # Rotas protegidas (requerem login)
    path('dashboard/', views.menu, name='index'),
    path('dashboard/menu/', views.menu, name='menu'),

    #Serão removidas ou modificadas após refatoração da tela da plataforma Inteli.gente
    path('dashboard/dimensoes/', views.dimensoes, name='dimensoes'),   
    path('dashboard/plataformas/inteligente/', views.inteligente, name='inteligente'),
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
    



    # Rotas plataformas
    path('dashboard/plataformas/', views.plataformas, name='plataformas'),
    #CSC
    path("csc/", views.csc_dashboard, name="csc_dashboard"),
    path("dashboard/api/estados/", views.api_estados, name="api_estados"),
    path("dashboard/api/municipios/", views.api_municipios, name="api_municipios"),
    path("api/dados-municipio/<int:municipio_id>/", views.get_municipio_data, name="get_municipio_data"),
    path("api/ranking/", views.get_ranking_data, name="get_ranking_data"),
    path("api/resumo-csc/", views.get_csc_summary, name="get_csc_summary"),




    # Admin - Gerenciamento de Usuários (apenas para administradores)
    path('dashboard/admin/', views.admin_menu, name='admin_menu'),
    path('dashboard/admin/users/', views.list_users, name='list_users'),
    path('dashboard/admin/users/add/', views.add_user, name='add_user'),
    path('dashboard/admin/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('dashboard/admin/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('dashboard/admin/users/<int:user_id>/change-role/', views.change_user_role, name='change_user_role'),

    #APIs para buscar municipios e estados
    path('dashboard/api/estados/', views.list_states, name='list_states'),
    path('dashboard/api/municipios/', views.list_municipalities, name='list_municipalities'),


    # Arquivos estáticos
    path('static/<path:path>', views.serve_static, name='serve_static'),

    # Outras rotas protegidas
    path('dashboard/indicador/<str:dimensao_id>/<int:indicador_id>/', views.indicador_detalhes, name='indicador_detalhes'),

    # APIs para plataformas
    path('dashboard/plataformas/adicionar/', views.adicionar_plataforma, name='adicionar_plataforma'),
    path('dashboard/plataformas/editar/<int:platform_id>/', views.editar_plataforma, name='editar_plataforma'),
    path('dashboard/plataformas/remover/<int:platform_id>/', views.remover_plataforma, name='remover_plataforma'),
    path('dashboard/plataformas/listar/', views.listar_plataformas, name='listar_plataformas'),





    # Logs
    path("dashboard/logs/", views.logs_auditoria, name="logs"),
    path("dashboard/logs/<int:log_id>/", views.detalhe_log_auditoria, name="detalhe_log"),

    # Recuperação
    path("dashboard/recuperacao/", views.recuperacao_auditoria, name="recuperacao"),
    path("dashboard/recuperacao/<int:log_id>/recuperar/", views.recuperar_auditoria, name="recuperar"),

    # Anexos / evidências
    path("dashboard/evidencias/<int:evidencia_id>/apagar/", views.apagar_anexo_auditoria, name="apagar_anexo"),

    # Valores dos indicadores
    path("dashboard/valores-indicadores/<int:valor_id>/alterar/", views.alterar_valor_indicador_auditoria, name="alterar_valor_indicador"),

    # Indicadores
    path("dashboard/indicadores/<int:indicador_id>/editar/", views.editar_indicador_auditoria, name="editar_indicador"),
    path("dashboard/indicadores/<int:indicador_id>/deletar/", views.deletar_indicador_auditoria, name="deletar_indicador"),



    # Designações de preenchimento
    path("dashboard/designacoes/", views.listar_designacoes, name="designacoes"),
    path("dashboard/designacoes/criar/", views.criar_designacao, name="criar_designacao"),
    path("dashboard/designacoes/<int:designacao_id>/", views.detalhe_designacao, name="detalhe_designacao"),
    path("dashboard/designacoes/<int:designacao_id>/cancelar/", views.cancelar_designacao, name="cancelar_designacao"),
    path("dashboard/designacoes/indicador/<int:item_id>/preencher/", views.preencher_indicador_designado, name="preencher_indicador_designado"),

]
