from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app import models
from app.admin.routers import admin
from app.database import SessionLocal, engine
from app.reports.routers import reports
from app.search.routers import search
from app.tasks.routers import tasks

load_dotenv()

models.Base.metadata.create_all(bind=engine)

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

app.include_router(admin.router)
app.include_router(reports.router)
app.include_router(search.router)
app.include_router(tasks.router)


@app.get("/")
def home_page():
    return {"message": "EventSphere API running", "admin_ui": "/admin/ui", "search_ui": "/ui/search"}


@app.get("/health")
def health():
    return {"ok": True}
