from django.urls import path
from . import views

urlpatterns = [
    path('jobs/', views.create_scraping_job, name='create_job'),
    path('jobs/<int:job_id>/status/', views.get_job_status, name='job_status'),
    path('jobs/<int:job_id>/data/', views.get_scraped_data, name='scraped_data'),
    path('jobs/<int:job_id>/execute/', views.execute_job, name='execute_job'),
] 