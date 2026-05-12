from __future__ import annotations

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.menu, name="menu"),
    path("<str:standard_slug>/", views.indicators_dashboard, name="indicators"),
]
