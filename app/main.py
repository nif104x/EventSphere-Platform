from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from sqlalchemy import text
from app import models
from app.admin.routers import admin
from app.database import SessionLocal, engine
from app.search.routers import search
from app.tasks.routers import tasks

load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="EventSphere API")
templates = Jinja2Templates(directory="app/templates")


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

app.mount(
    "/admin/static", StaticFiles(directory="app/admin/static"), name="admin_static"
)
app.mount(
    "/search/static", StaticFiles(directory="app/search/static"), name="search_static"
)

app.include_router(admin.router)
app.include_router(search.router)
app.include_router(tasks.router)


@app.get("/")
def home_page():
    return {"message": "EventSphere API running", "ui": "/ui/"}


@app.get("/ui", response_class=HTMLResponse)
def ui_home(request: Request):
    return templates.TemplateResponse(request, "home.html", {})


@app.get("/health")
def health():
    return {"ok": True}
