import os
import time

import psycopg2
from psycopg2.extras import RealDictCursor


def _env(key: str, default: str) -> str:
    val = os.getenv(key)
    return val if val is not None and val != "" else default


DB_HOST = _env("DB_HOST", "localhost")
DB_NAME = _env("DB_NAME", "eventsphere")
DB_USER = _env("DB_USER", "postgres")
DB_PASSWORD = _env("DB_PASSWORD", "2020")
DB_PORT = int(_env("DB_PORT", "5432"))


def get_conn(retries: int = 20, wait_seconds: int = 2):
    last_error = None
    for _ in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                cursor_factory=RealDictCursor,
            )
            return conn
        except Exception as e:
            last_error = e
            time.sleep(wait_seconds)
    raise last_error

