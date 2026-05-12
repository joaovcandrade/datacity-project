from __future__ import annotations

from rest_framework import serializers

from .models import ISOIndicator, ISOIndicatorData


class ISOIndicatorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISOIndicatorData
        fields = ["id", "year", "dado", "fonte", "anexo"]
        read_only_fields = ["id"]


class ISOIndicatorSerializer(serializers.ModelSerializer):
    data = ISOIndicatorDataSerializer(many=True, read_only=True)
    standard_display = serializers.CharField(source="get_standard_display", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = ISOIndicator
        fields = [
            "id",
            "standard",
            "standard_display",
            "categoria",
            "nome_indicador",
            "tipo",
            "tipo_display",
            "ods",
            "unidade",
            "cidade",
            "estado",
            "data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ISOIndicatorWriteSerializer(serializers.ModelSerializer):
    """Serializer para criação/edição sem dados anuais embutidos."""

    class Meta:
        model = ISOIndicator
        fields = [
            "standard",
            "categoria",
            "nome_indicador",
            "tipo",
            "ods",
            "unidade",
            "cidade",
            "estado",
        ]
