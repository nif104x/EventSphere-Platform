"""Postgres URL for the app: prefer DATABASE_URL (Render, etc.), else DB_* pieces."""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

_root = Path(__file__).resolve().parent.parent
_app = Path(__file__).resolve().parent


def _on_render_host() -> bool:
    return str(os.getenv("RENDER", "")).lower() in ("1", "true", "yes")


# On Render, use only the dashboard environment — never a repo .env that might set localhost DB_*.
if not _on_render_host():
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
    1. DATABASE_URL — Render (linked Postgres), other hosts, or local override.
    2. DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD — local dev only.

    On Render (RENDER=true), DATABASE_URL must be set; localhost fallbacks are rejected.
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

    if _on_render_host() and host in ("localhost", "127.0.0.1", "::1"):
        raise RuntimeError(
            "DATABASE_URL is missing or empty on Render, so the app fell back to DB_HOST=localhost, "
            "which does not exist on the web service.\n"
            "Fix: In the Render dashboard open this Web Service → Environment → add variable "
            "DATABASE_URL with your Postgres External Connection String, or use "
            "'Add from existing' / link the PostgreSQL instance so Render injects DATABASE_URL."
        )

    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )
