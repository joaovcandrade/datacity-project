from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuário customizado com autenticação por e-mail e tipos de acesso."""

    class UserType(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        MANAGER = "MANAGER", "Gestor"
        COMMON = "COMMON", "Usuário Comum"

    # AbstractUser já tem username, first_name, last_name, email, is_staff, etc.
    # Adicionamos campos específicos do domínio.
    nome = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)  # obrigatório — usado como USERNAME_FIELD
    cpf = models.CharField(max_length=14, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.COMMON,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    # Evita conflito com related_name do auth.User padrão
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",
        blank=True,
        verbose_name="groups",
        help_text="The groups this user belongs to.",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_set",
        blank=True,
        verbose_name="user permissions",
        help_text="Specific permissions for this user.",
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


# ---------------------------------------------------------------------------
# Platform
# ---------------------------------------------------------------------------

class Platform(models.Model):
    """Plataforma externa de dados urbanos."""

    # Mantém o nome da coluna original para compatibilidade com o banco existente.
    # TODO (Fase 4): renomear para `nome` e `url` após migração completa.
    Nome = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    Direcionamento = models.URLField(verbose_name="URL")

    class Meta:
        db_table = "plataforma"
        ordering = ["Nome"]
        verbose_name = "Plataforma"
        verbose_name_plural = "Plataformas"

    def __str__(self) -> str:
        return self.Nome


# ---------------------------------------------------------------------------
# Norm
# ---------------------------------------------------------------------------

class Norm(models.Model):
    """Norma ou padrão referenciado pelo sistema."""

    Nome = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    Direcionamento = models.URLField(verbose_name="URL")

    class Meta:
        db_table = "norma"
        ordering = ["Nome"]
        verbose_name = "Norma"
        verbose_name_plural = "Normas"

    def __str__(self) -> str:
        return self.Nome


# ---------------------------------------------------------------------------
# ISO Indicators — modelo unificado
# ---------------------------------------------------------------------------

class ISOStandard(models.TextChoices):
    ISO37120 = "iso37120", "ISO 37120"
    ISO37122 = "iso37122", "ISO 37122"
    ISO37123 = "iso37123", "ISO 37123"
    ISO37125 = "iso37125", "ISO 37125"


class IndicatorType(models.TextChoices):
    CORE = "core", "Principal"
    SUPPORTING = "supporting", "Apoio"
    PROFILE = "profile", "Perfil"


class ISOIndicator(models.Model):
    """
    Indicador de um padrão ISO de cidade inteligente.

    Unifica os 4 modelos anteriores (ISO37120Indicator, ISO37122Indicator,
    ISO37123Indicator, ISO37125Indicator) em um único modelo normalizado.
    O campo `standard` discrimina a qual norma o indicador pertence.
    """

    standard = models.CharField(
        max_length=10,
        choices=ISOStandard.choices,
        verbose_name="Padrão ISO",
    )
    categoria = models.CharField(max_length=100, verbose_name="Categoria")
    nome_indicador = models.CharField(max_length=255, verbose_name="Nome do Indicador")
    tipo = models.CharField(
        max_length=20,
        choices=IndicatorType.choices,
        verbose_name="Tipo",
    )
    ods = models.CharField(max_length=10, verbose_name="ODS")
    unidade = models.CharField(max_length=50, verbose_name="Unidade")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    estado = models.CharField(max_length=50, verbose_name="Estado")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "iso_indicators"
        unique_together = [["standard", "nome_indicador", "cidade", "estado"]]
        ordering = ["categoria", "nome_indicador"]
        indexes = [
            models.Index(fields=["standard", "cidade", "estado"]),
            models.Index(fields=["cidade", "estado"]),
        ]
        verbose_name = "Indicador ISO"
        verbose_name_plural = "Indicadores ISO"

    def __str__(self) -> str:
        return f"[{self.standard.upper()}] {self.nome_indicador} — {self.cidade}/{self.estado}"


class ISOIndicatorData(models.Model):
    """Dado anual de um indicador ISO (dado, fonte e anexo PDF por ano)."""

    indicator = models.ForeignKey(
        ISOIndicator,
        on_delete=models.CASCADE,
        related_name="data",
        verbose_name="Indicador",
    )
    year = models.PositiveSmallIntegerField(verbose_name="Ano")
    dado = models.CharField(max_length=100, null=True, blank=True, verbose_name="Dado")
    fonte = models.CharField(max_length=500, null=True, blank=True, verbose_name="Fonte")
    anexo = models.FileField(
        upload_to="iso_indicators/anexos/%Y/",
        null=True,
        blank=True,
        verbose_name="Anexo PDF",
    )

    class Meta:
        db_table = "iso_indicator_data"
        unique_together = [["indicator", "year"]]
        ordering = ["year"]
        verbose_name = "Dado do Indicador"
        verbose_name_plural = "Dados dos Indicadores"

    def __str__(self) -> str:
        return f"{self.indicator} — {self.year}"


# ---------------------------------------------------------------------------
# Legacy models — mantidos para compatibilidade durante a migração
# Serão removidos após a data migration ser executada (Fase 3.2 do plano).
# ---------------------------------------------------------------------------

class _LegacyISOIndicatorBase(models.Model):
    """Base abstrata compartilhada pelos 4 modelos legados."""

    categoria = models.CharField(max_length=100)
    nome_indicador = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=IndicatorType.choices)
    ods = models.CharField(max_length=10)
    unidade = models.CharField(max_length=50)

    dado_2022 = models.CharField(max_length=100, null=True, blank=True)
    dado_2023 = models.CharField(max_length=100, null=True, blank=True)
    dado_2024 = models.CharField(max_length=100, null=True, blank=True)
    dado_2025 = models.CharField(max_length=100, null=True, blank=True)

    fonte_2022 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2023 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2024 = models.CharField(max_length=500, null=True, blank=True)
    fonte_2025 = models.CharField(max_length=500, null=True, blank=True)

    cidade = models.CharField(max_length=100, default="Londrina")
    estado = models.CharField(max_length=50, default="PR")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        unique_together = [["nome_indicador", "cidade", "estado"]]
        ordering = ["categoria", "nome_indicador"]


class ISO37120Indicator(_LegacyISOIndicatorBase):
    anexo_2022 = models.FileField(upload_to="iso37120/anexos/", null=True, blank=True)
    anexo_2023 = models.FileField(upload_to="iso37120/anexos/", null=True, blank=True)
    anexo_2024 = models.FileField(upload_to="iso37120/anexos/", null=True, blank=True)
    anexo_2025 = models.FileField(upload_to="iso37120/anexos/", null=True, blank=True)

    class Meta(_LegacyISOIndicatorBase.Meta):
        db_table = "iso37120_indicators"

    def __str__(self) -> str:
        return f"{self.nome_indicador} — {self.cidade}/{self.estado}"


class ISO37122Indicator(_LegacyISOIndicatorBase):
    anexo_2022 = models.FileField(upload_to="iso37122/anexos/", null=True, blank=True)
    anexo_2023 = models.FileField(upload_to="iso37122/anexos/", null=True, blank=True)
    anexo_2024 = models.FileField(upload_to="iso37122/anexos/", null=True, blank=True)
    anexo_2025 = models.FileField(upload_to="iso37122/anexos/", null=True, blank=True)

    class Meta(_LegacyISOIndicatorBase.Meta):
        db_table = "iso37122_indicators"

    def __str__(self) -> str:
        return f"{self.nome_indicador} — {self.cidade}/{self.estado}"


class ISO37123Indicator(_LegacyISOIndicatorBase):
    anexo_2022 = models.FileField(upload_to="iso37123/anexos/", null=True, blank=True)
    anexo_2023 = models.FileField(upload_to="iso37123/anexos/", null=True, blank=True)
    anexo_2024 = models.FileField(upload_to="iso37123/anexos/", null=True, blank=True)
    anexo_2025 = models.FileField(upload_to="iso37123/anexos/", null=True, blank=True)

    class Meta(_LegacyISOIndicatorBase.Meta):
        db_table = "iso37123_indicators"

    def __str__(self) -> str:
        return f"{self.nome_indicador} — {self.cidade}/{self.estado}"


class ISO37125Indicator(_LegacyISOIndicatorBase):
    anexo_2022 = models.FileField(upload_to="iso37125/anexos/", null=True, blank=True)
    anexo_2023 = models.FileField(upload_to="iso37125/anexos/", null=True, blank=True)
    anexo_2024 = models.FileField(upload_to="iso37125/anexos/", null=True, blank=True)
    anexo_2025 = models.FileField(upload_to="iso37125/anexos/", null=True, blank=True)

    class Meta(_LegacyISOIndicatorBase.Meta):
        db_table = "iso37125_indicators"

    def __str__(self) -> str:
        return f"{self.nome_indicador} — {self.cidade}/{self.estado}"
