import sys
from pathlib import Path

# Running `uvicorn main:app` from inside `app/` loads this file as top-level `main`;
# ensure the project root (parent of `app/`) is on sys.path so `import app.*` works.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

# On Render, secrets come from the service environment only (RENDER=true).
if str(os.getenv("RENDER", "")).lower() not in ("1", "true", "yes"):
    load_dotenv(_PROJECT_ROOT / ".env")
    load_dotenv(Path(__file__).resolve().parent / ".env")

from app import models as core_models
from app.paths import APP_DIR
from app.admin.routers import admin
from app.customer.database import Base as customer_base, engine as customer_engine
from app.customer.routes import router as customer_router
from app.database import SessionLocal, engine as core_engine
from app.organizer import models as organizer_models
from app.organizer.database import engine as organizer_engine
from app.organizer.routers import auth, customers, user
from app.reports.routers import reports
from app.search.routers import search
from app.tasks.routers import tasks

import app.customer.models  # noqa: F401

core_models.Base.metadata.create_all(bind=core_engine)
organizer_models.Base.metadata.create_all(bind=organizer_engine)
customer_base.metadata.create_all(bind=customer_engine)

app = FastAPI(title="EventSphere API")


@app.on_event("startup")
def _ensure_schema():
    with SessionLocal() as db:
        db.execute(
            text(
                "ALTER TABLE service_listings ADD COLUMN IF NOT EXISTS is_deleted boolean DEFAULT false"
            )
        )
        db.commit()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory=str(APP_DIR / "static_shared")), name="assets")
app.mount("/static", StaticFiles(directory=str(APP_DIR / "organizer" / "static")), name="static")

app.include_router(admin.router)
app.include_router(customer_router)
app.include_router(reports.router)
app.include_router(search.router)
app.include_router(tasks.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(customers.router)


@app.get("/")
def root():
    return {
        "message": "EventSphere API running",
        "admin_ui": "/admin/ui",
        "search_ui": "/ui/search",
        "organizer_ui": "/organizer/dashboard",
        "customer_api": "/api",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
