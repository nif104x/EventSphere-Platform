import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


def _env(key: str, default: str) -> str:
    v = os.getenv(key)
    return v if v else default


DB_HOST = _env("DB_HOST", "localhost")
DB_PORT = _env("DB_PORT", "5432")
DB_NAME = _env("DB_NAME", "eventsphere")
DB_USER = _env("DB_USER", "postgres")
DB_PASSWORD = _env("DB_PASSWORD", "2020")

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

