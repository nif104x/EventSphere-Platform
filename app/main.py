from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app import models as core_models
from app.admin.routers import admin
from app.database import SessionLocal, engine as core_engine
from app.organizer import models as organizer_models
from app.organizer.database import engine as organizer_engine
from app.organizer.routers import auth, customers, user
from app.reports.routers import reports
from app.search.routers import search
from app.tasks.routers import tasks

core_models.Base.metadata.create_all(bind=core_engine)
organizer_models.Base.metadata.create_all(bind=organizer_engine)

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="app/static_shared"), name="assets")
app.mount("/static", StaticFiles(directory="app/organizer/static"), name="static")

app.include_router(admin.router)
app.include_router(reports.router)
app.include_router(search.router)
app.include_router(tasks.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(customers.router)


@app.get("/")
def home_page():
    return {
        "message": "EventSphere API running",
        "admin_ui": "/admin/ui",
        "search_ui": "/ui/search",
        "organizer_ui": "/organizer/dashboard",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"ok": True}
