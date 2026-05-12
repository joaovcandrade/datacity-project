from __future__ import annotations

from django.db import models


class Norm(models.Model):
    """Norma ou padrão referenciado pelo sistema."""

    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    url = models.URLField(verbose_name="URL")

    class Meta:
        db_table = "norma"
        ordering = ["nome"]
        verbose_name = "Norma"
        verbose_name_plural = "Normas"

    def __str__(self) -> str:
        return self.nome
