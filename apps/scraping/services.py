from __future__ import annotations

# Re-exporta o serviço da app legada scraping/ durante o período de transição.
# TODO (Fase 4.2): mover scraping/services.py para cá e atualizar INSTALLED_APPS.
from scraping.services import ScrapingService  # noqa: F401
