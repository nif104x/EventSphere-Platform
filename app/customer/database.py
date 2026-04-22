from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

_app_dir = Path(__file__).resolve().parent.parent
_project_dir = _app_dir.parent
load_dotenv(_project_dir / ".env")
load_dotenv(_app_dir / ".env")


def _database_url() -> str:
    # Prefer the shared DB_* settings used by the rest of the backend.
    if any(os.getenv(key) for key in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")):
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "eventsphere")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "2020")
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    return os.getenv("DATABASE_URL", "postgresql://appuser:12345@localhost:5432/eventdb")


DATABASE_URL = _database_url()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

