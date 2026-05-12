from __future__ import annotations

from django.contrib import admin

from .models import Norm


@admin.register(Norm)
class NormAdmin(admin.ModelAdmin):
    list_display = ["nome", "url"]
    search_fields = ["nome"]
