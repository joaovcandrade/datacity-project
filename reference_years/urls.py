from django.urls import path
from . import views

urlpatterns = [
    # Admin - Gerenciamento de Anos (apenas para administradores)
    path('dashboard/admin/years/', views.list_years, name='list_years'),
    path('dashboard/admin/years/add/', views.add_year, name='add_year'),
    path('dashboard/admin/years/<int:year_id>/change-status/', views.change_year_status, name='change_year_status'),

] 