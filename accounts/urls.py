from django.urls import path

from . import views

urlpatterns = [
    # ── Públicas ────────────────────────────────────────────────────────────
    path("", views.landing, name="landing"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("saiba-mais/", views.saiba_mais, name="saiba_mais"),

    # ── Dashboard ───────────────────────────────────────────────────────────
    path("dashboard/", views.menu, name="menu"),
    path("dashboard/menu/", views.menu, name="index"),
    path("dashboard/dimensoes/", views.dimensoes, name="dimensoes"),
    path("dashboard/indicadores/", views.indicadores, name="indicadores"),
    path("dashboard/indicadores/<str:dimensao_id>/", views.indicadores, name="indicadores_dimensao"),
    path("dashboard/normas/", views.normas, name="normas"),
    path("dashboard/plataformas/", views.plataformas, name="plataformas"),

    # ── Páginas de plataformas ───────────────────────────────────────────────
    path("dashboard/plataformas/csc/", views.csc, name="csc"),
    path("dashboard/plataformas/inteligente/", views.inteligente, name="inteligente"),

    # ── Páginas de normas ISO ────────────────────────────────────────────────
    path("dashboard/normas/iso37120/", views.iso37120, name="iso37120"),
    path("dashboard/normas/iso37122/", views.iso37122, name="iso37122"),
    path("dashboard/normas/iso37123/", views.iso37123, name="iso37123"),
    path("dashboard/normas/iso37125/", views.iso37125, name="iso37125"),

    # ── API genérica ISO (4 padrões numa rota só) ────────────────────────────
    path("dashboard/api/<str:standard_slug>/get/", views.get_iso_data, name="get_iso_data"),
    path("dashboard/api/<str:standard_slug>/save/", views.save_iso_data, name="save_iso_data"),
    path("dashboard/api/<str:standard_slug>/update_field/", views.update_iso_field, name="update_iso_field"),
    path("dashboard/api/<str:standard_slug>/upload_anexo/", views.upload_iso_anexo, name="upload_iso_anexo"),
    path("dashboard/api/<str:standard_slug>/delete_anexo/", views.delete_iso_anexo, name="delete_iso_anexo"),

    # ── Plataformas CRUD ─────────────────────────────────────────────────────
    path("dashboard/plataformas/listar/", views.listar_plataformas, name="listar_plataformas"),
    path("dashboard/plataformas/adicionar/", views.adicionar_plataforma, name="adicionar_plataforma"),
    path("dashboard/plataformas/editar/<int:platform_id>/", views.editar_plataforma, name="editar_plataforma"),
    path("dashboard/plataformas/remover/<int:platform_id>/", views.remover_plataforma, name="remover_plataforma"),

    # ── Normas CRUD ──────────────────────────────────────────────────────────
    path("dashboard/normas/listar/", views.listar_normas, name="listar_normas"),
    path("dashboard/normas/adicionar/", views.adicionar_norma, name="adicionar_norma"),
    path("dashboard/normas/editar/<int:norm_id>/", views.editar_norma, name="editar_norma"),
    path("dashboard/normas/remover/<int:norm_id>/", views.remover_norma, name="remover_norma"),

    # ── Admin de usuários ────────────────────────────────────────────────────
    path("dashboard/admin/", views.admin_menu, name="admin_menu"),
    path("dashboard/admin/users/", views.list_users, name="list_users"),
    path("dashboard/admin/users/add/", views.add_user, name="add_user"),
    path("dashboard/admin/users/<int:user_id>/edit/", views.edit_user, name="edit_user"),
    path("dashboard/admin/users/<int:user_id>/delete/", views.delete_user, name="delete_user"),
    path("dashboard/admin/users/<int:user_id>/change-role/", views.change_user_role, name="change_user_role"),

    # ── Modais ───────────────────────────────────────────────────────────────
    path("dashboard/modals/dimensoes/", views.modal_dimensoes, name="modal-dimensoes"),
    path("dashboard/modals/indicadores/", views.modal_indicadores, name="modal-indicadores"),

    # ── Static (apenas dev — em prod usar Nginx) ─────────────────────────────
    path("static/<path:path>", views.serve_static, name="serve_static"),
]
