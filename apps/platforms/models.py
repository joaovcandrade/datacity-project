from __future__ import annotations

from django.db import models


class Platform(models.Model):
    """Plataforma externa de dados urbanos."""

    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    url = models.URLField(verbose_name="URL")

    class Meta:
        db_table = "plataforma"
        ordering = ["nome"]
        verbose_name = "Plataforma"
        verbose_name_plural = "Plataformas"

    def __str__(self) -> str:
        return self.nome
