from __future__ import annotations

from django.db import models

from .constants import DEFAULT_CITY, DEFAULT_STATE


class ISOStandard(models.TextChoices):
    ISO37120 = "iso37120", "ISO 37120"
    ISO37122 = "iso37122", "ISO 37122"
    ISO37123 = "iso37123", "ISO 37123"
    ISO37125 = "iso37125", "ISO 37125"


class IndicatorType(models.TextChoices):
    CORE = "core", "Principal"
    SUPPORTING = "supporting", "Apoio"
    PROFILE = "profile", "Perfil"


class ISOIndicatorQuerySet(models.QuerySet):
    def for_location(self, cidade: str, estado: str) -> ISOIndicatorQuerySet:
        return self.filter(cidade=cidade, estado=estado)

    def for_standard(self, standard: str) -> ISOIndicatorQuerySet:
        return self.filter(standard=standard)

    def with_data(self) -> ISOIndicatorQuerySet:
        return self.prefetch_related("data")


class ISOIndicatorManager(models.Manager):
    def get_queryset(self) -> ISOIndicatorQuerySet:
        return ISOIndicatorQuerySet(self.model, using=self._db)

    def for_location(self, cidade: str, estado: str) -> ISOIndicatorQuerySet:
        return self.get_queryset().for_location(cidade, estado)


class ISOIndicator(models.Model):
    """
    Indicador de cidade inteligente conforme padrões ISO 37120/37122/37123/37125.
    Substitui os 4 modelos legados com um design normalizado.
    """

    standard = models.CharField(
        max_length=10,
        choices=ISOStandard.choices,
        verbose_name="Padrão ISO",
        db_index=True,
    )
    categoria = models.CharField(max_length=100, verbose_name="Categoria")
    nome_indicador = models.CharField(max_length=255, verbose_name="Nome do Indicador")
    tipo = models.CharField(max_length=20, choices=IndicatorType.choices, verbose_name="Tipo")
    ods = models.CharField(max_length=10, verbose_name="ODS", blank=True)
    unidade = models.CharField(max_length=50, verbose_name="Unidade", blank=True)
    cidade = models.CharField(max_length=100, default=DEFAULT_CITY, verbose_name="Cidade")
    estado = models.CharField(max_length=50, default=DEFAULT_STATE, verbose_name="Estado")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ISOIndicatorManager()

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
        return f"[{self.get_standard_display()}] {self.nome_indicador} — {self.cidade}/{self.estado}"


class ISOIndicatorData(models.Model):
    """Dado anual de um indicador ISO (dado numérico, fonte e anexo PDF)."""

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
