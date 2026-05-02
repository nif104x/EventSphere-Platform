"""Postgres URL for the app: prefer DATABASE_URL (Render, etc.), else DB_* pieces."""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

_root = Path(__file__).resolve().parent.parent
_app = Path(__file__).resolve().parent
load_dotenv(_root / ".env")
load_dotenv(_app / ".env")


def _env(key: str, default: str) -> str:
    """Treat unset or blank env as missing (so empty DB_HOST does not break URL)."""
    v = os.getenv(key)
    if v is None:
        return default
    v = str(v).strip()
    return v if v else default


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and (
        (value.startswith('"') and value.endswith('"'))
        or (value.startswith("'") and value.endswith("'"))
    ):
        return value[1:-1].strip()
    return value


def _normalize_postgres_scheme(url: str) -> str:
    """SQLAlchemy / psycopg2 expect postgresql://, not postgres://."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


def _ensure_sslmode_for_render(url: str) -> str:
    """Render external Postgres often requires TLS; append if host looks like Render and DSN omits sslmode."""
    lower = url.lower()
    if "sslmode=" in lower:
        return url
    if "render.com" not in lower and "dpg-" not in lower:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}sslmode=require"


def resolve_database_url() -> str:
    """
    Single URL for all SQLAlchemy engines (and scripts that import this module).

    Order:
    1. DATABASE_URL — use on Render or when pointing local app at a remote DB.
    2. DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD — local dev defaults.
    """
    composite = _env("DATABASE_URL", "")
    if composite:
        url = _strip_wrapping_quotes(composite)
        url = _normalize_postgres_scheme(url)
        return _ensure_sslmode_for_render(url)

    host = _env("DB_HOST", "localhost")
    port = _env("DB_PORT", "5432")
    name = _env("DB_NAME", "eventsphere")
    user = _env("DB_USER", "postgres")
    password = _env("DB_PASSWORD", "2020")
    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )
