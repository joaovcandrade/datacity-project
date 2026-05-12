from __future__ import annotations

DEFAULT_CITY: str = "Londrina"
DEFAULT_STATE: str = "PR"

MAX_ATTACHMENT_SIZE: int = 10 * 1024 * 1024  # 10 MB

VALID_YEARS: frozenset[int] = frozenset({2022, 2023, 2024, 2025})

ALLOWED_UPDATE_FIELDS: frozenset[str] = frozenset(
    {f"{prefix}_{year}" for prefix in ("dado", "fonte") for year in VALID_YEARS}
)
