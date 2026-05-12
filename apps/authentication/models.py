from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuário do sistema com autenticação por e-mail."""

    class UserType(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        MANAGER = "MANAGER", "Gestor"
        COMMON = "COMMON", "Usuário Comum"

    nome = models.CharField(max_length=100, blank=True, verbose_name="Nome completo")
    email = models.EmailField(unique=True, verbose_name="E-mail")
    cpf = models.CharField(max_length=14, blank=True, verbose_name="CPF")
    cidade = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.COMMON,
        verbose_name="Tipo de usuário",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",
        blank=True,
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_set",
        blank=True,
        verbose_name="user permissions",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self) -> str:
        return self.email or self.username

    def is_admin(self) -> bool:
        return self.user_type == self.UserType.ADMIN

    def is_manager(self) -> bool:
        return self.user_type == self.UserType.MANAGER

    def is_common_user(self) -> bool:
        return self.user_type == self.UserType.COMMON
