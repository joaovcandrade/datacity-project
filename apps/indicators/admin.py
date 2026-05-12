from __future__ import annotations

from django.contrib import admin

from .models import ISOIndicator, ISOIndicatorData


class ISOIndicatorDataInline(admin.TabularInline):
    model = ISOIndicatorData
    extra = 0
    fields = ["year", "dado", "fonte", "anexo"]


@admin.register(ISOIndicator)
class ISOIndicatorAdmin(admin.ModelAdmin):
    list_display = ["standard", "categoria", "nome_indicador", "tipo", "cidade", "estado"]
    list_filter = ["standard", "tipo", "cidade", "estado"]
    search_fields = ["nome_indicador", "categoria"]
    inlines = [ISOIndicatorDataInline]
    readonly_fields = ["created_at", "updated_at"]
