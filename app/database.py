from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

_pkg_dir = Path(__file__).resolve().parent
_project_dir = _pkg_dir.parent
load_dotenv(_pkg_dir / ".env")
load_dotenv(_project_dir / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://appuser:12345@localhost:5432/eventdb")
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

