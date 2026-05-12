from __future__ import annotations

from rest_framework import serializers

from .models import Norm


class NormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Norm
        fields = ["id", "nome", "url"]
        read_only_fields = ["id"]
