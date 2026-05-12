from __future__ import annotations

from django.contrib import admin

from .models import Platform


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ["nome", "url"]
    search_fields = ["nome"]
