"""Single Postgres URL for the whole app — always from DB_* (defaults match local dev)."""

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


def resolve_database_url() -> str:
    """
    All SQLAlchemy engines use this URL.
    Defaults: localhost:5432, database eventsphere, user postgres, password 2020.
    """
    host = _env("DB_HOST", "localhost")
    port = _env("DB_PORT", "5432")
    name = _env("DB_NAME", "eventsphere")
    user = _env("DB_USER", "postgres")
    password = _env("DB_PASSWORD", "2020")
    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )
