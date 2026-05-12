from __future__ import annotations

from .base import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

DEBUG = True

SECRET_KEY = os.environ.get(  # noqa: F405
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-key-never-use-in-production",
)

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]

# ---------------------------------------------------------------------------
# Banco de dados (PostgreSQL local)
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "datacity"),  # noqa: F405
        "USER": os.environ.get("DATABASE_USER", "datacity_user"),  # noqa: F405
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),  # noqa: F405
        "HOST": os.environ.get("DATABASE_HOST", "localhost"),  # noqa: F405
        "PORT": os.environ.get("DATABASE_PORT", "5432"),  # noqa: F405
    }
}

# ---------------------------------------------------------------------------
# Email (console em desenvolvimento)
# ---------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# CORS (permissivo em dev)
# ---------------------------------------------------------------------------

CORS_ALLOW_ALL_ORIGINS = True
