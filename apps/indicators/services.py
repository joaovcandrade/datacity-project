from __future__ import annotations

import logging
from typing import Any

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from .constants import ALLOWED_UPDATE_FIELDS, MAX_ATTACHMENT_SIZE, VALID_YEARS
from .models import ISOIndicator, ISOIndicatorData, ISOStandard

logger = logging.getLogger(__name__)


class AttachmentValidationError(ValueError):
    """Levantada quando o arquivo enviado não passa nas validações."""


class ISOIndicatorService:
    """
    Camada de serviço para o domínio de indicadores ISO.
    Toda lógica de negócio fica aqui — views apenas orquestram.
    """

    @staticmethod
    def get_or_create_indicator(
        standard: str,
        nome_indicador: str,
        cidade: str,
        estado: str,
        defaults: dict[str, Any] | None = None,
    ) -> tuple[ISOIndicator, bool]:
        return ISOIndicator.objects.get_or_create(
            standard=standard,
            nome_indicador=nome_indicador,
            cidade=cidade,
            estado=estado,
            defaults=defaults or {},
        )

    @staticmethod
    @transaction.atomic
    def save_indicator_data(
        standard: str,
        nome_indicador: str,
        cidade: str,
        estado: str,
        fields: dict[str, Any],
    ) -> ISOIndicator:
        """Cria ou atualiza um indicador e seus dados anuais."""
        base_fields = {
            k: v for k, v in fields.items()
            if not k.startswith(("dado_", "fonte_"))
        }
        indicator, created = ISOIndicator.objects.update_or_create(
            standard=standard,
            nome_indicador=nome_indicador,
            cidade=cidade,
            estado=estado,
            defaults=base_fields,
        )

        for year in VALID_YEARS:
            dado = fields.get(f"dado_{year}")
            fonte = fields.get(f"fonte_{year}")
            if dado is not None or fonte is not None:
                ISOIndicatorData.objects.update_or_create(
                    indicator=indicator,
                    year=year,
                    defaults={k: v for k, v in {"dado": dado, "fonte": fonte}.items() if v is not None},
                )

        return indicator

    @staticmethod
    def update_field(indicator_id: int, field_name: str, field_value: Any) -> ISOIndicator:
        """Atualiza um campo permitido de um indicador com whitelist estrita."""
        if field_name not in ALLOWED_UPDATE_FIELDS:
            raise ValueError(f"Campo '{field_name}' não é permitido para atualização direta.")

        indicator = ISOIndicator.objects.get(id=indicator_id)

        # Os campos dado_/fonte_ agora estão em ISOIndicatorData
        # Mantemos compatibilidade enquanto os models legados existem
        prefix, year_str = field_name.rsplit("_", 1)
        year = int(year_str)
        data_entry, _ = ISOIndicatorData.objects.get_or_create(
            indicator=indicator, year=year
        )
        field_map = {"dado": "dado", "fonte": "fonte"}
        data_field = field_map.get(prefix)
        if data_field:
            setattr(data_entry, data_field, field_value)
            data_entry.save(update_fields=[data_field])

        return indicator

    @staticmethod
    @transaction.atomic
    def upload_attachment(indicator_id: int, year: int, file: UploadedFile) -> str:
        """Valida e persiste um anexo PDF para um ano específico."""
        if year not in VALID_YEARS:
            raise AttachmentValidationError(f"Ano inválido: {year}.")

        if not file.name.lower().endswith(".pdf"):
            raise AttachmentValidationError("Apenas arquivos PDF são permitidos.")

        if file.size > MAX_ATTACHMENT_SIZE:
            raise AttachmentValidationError("Arquivo maior que 10 MB.")

        indicator = ISOIndicator.objects.get(id=indicator_id)
        data_entry, _ = ISOIndicatorData.objects.get_or_create(
            indicator=indicator, year=year
        )

        if data_entry.anexo:
            data_entry.anexo.delete(save=False)

        data_entry.anexo = file
        data_entry.save(update_fields=["anexo"])

        return data_entry.anexo.url

    @staticmethod
    @transaction.atomic
    def delete_attachment(indicator_id: int, year: int) -> None:
        """Remove o anexo de um indicador para o ano informado."""
        if year not in VALID_YEARS:
            raise AttachmentValidationError(f"Ano inválido: {year}.")

        try:
            data_entry = ISOIndicatorData.objects.get(
                indicator_id=indicator_id, year=year
            )
        except ISOIndicatorData.DoesNotExist as exc:
            raise ISOIndicatorData.DoesNotExist("Dado não encontrado para este indicador/ano.") from exc

        if not data_entry.anexo:
            raise FileNotFoundError("Nenhum anexo encontrado para este indicador/ano.")

        data_entry.anexo.delete(save=False)
        data_entry.anexo = None
        data_entry.save(update_fields=["anexo"])
