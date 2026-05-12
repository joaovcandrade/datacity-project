from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from accounts.models import ISOIndicator, ISOStandard

logger = logging.getLogger(__name__)

VALID_YEARS: frozenset[int] = frozenset({2022, 2023, 2024, 2025})

_STANDARD_LABELS: dict[str, str] = {
    ISOStandard.ISO37120: "ISO 37120",
    ISOStandard.ISO37122: "ISO 37122",
    ISOStandard.ISO37123: "ISO 37123",
    ISOStandard.ISO37125: "ISO 37125",
}

_ISO_STANDARDS_LIST: list[tuple[str, str]] = list(_STANDARD_LABELS.items())
_VALID_YEARS_SORTED: list[int] = sorted(VALID_YEARS)


def _base_context() -> dict[str, Any]:
    return {"iso_standards": _ISO_STANDARDS_LIST, "valid_years": _VALID_YEARS_SORTED}


@login_required
def menu(request: HttpRequest) -> HttpResponse:
    return render(request, "dashboard/menu.html", _base_context())


@login_required
def indicators_dashboard(request: HttpRequest, standard_slug: str) -> HttpResponse:
    if standard_slug not in _STANDARD_LABELS:
        raise Http404(f"Padrão '{standard_slug}' não encontrado.")

    cidade = getattr(request.user, "cidade", None) or "Londrina"
    indicators = (
        ISOIndicator.objects
        .filter(standard=standard_slug, cidade=cidade, estado="PR")
        .prefetch_related("data")
    )

    context: dict[str, Any] = {
        **_base_context(),
        "standard_slug": standard_slug,
        "standard_label": _STANDARD_LABELS[standard_slug],
        "indicators": indicators,
    }
    return render(request, "dashboard/indicators.html", context)
