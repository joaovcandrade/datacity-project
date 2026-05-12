from __future__ import annotations

from rest_framework import serializers

from .models import Platform


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ["id", "nome", "url"]
        read_only_fields = ["id"]
