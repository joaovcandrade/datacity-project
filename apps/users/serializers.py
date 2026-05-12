from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    user_type_display = serializers.CharField(source="get_user_type_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nome",
            "cpf",
            "cidade",
            "user_type",
            "user_type_display",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class UserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "nome", "cpf", "cidade", "user_type", "password"]

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance: User, validated_data: dict) -> User:
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
