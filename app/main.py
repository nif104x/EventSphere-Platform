from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin.routes.router import router as admin_router
from app.search.routes.router import router as search_router

app = FastAPI(title="EventSphere API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(search_router, tags=["search"])


@app.get("/")
def home_page():
    return {"message": "EventSphere API running"}


