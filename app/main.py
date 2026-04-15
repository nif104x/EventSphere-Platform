"""FastAPI entrypoint. Run either:
  - from EventSphere-Platform:  uvicorn app.main:app --reload
  - from app/:                  uvicorn main:app --reload
"""
import sys
from pathlib import Path

# Running `uvicorn main:app` from inside `app/` loads this file as top-level `main`;
# ensure the project root (parent of `app/`) is on sys.path so `import app.*` works.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base
from app.routes import router
import app.models  # noqa: F401 — register all models on metadata

app = FastAPI(title="EventSphere API")

# CORS
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

# Create tables (if needed, but schema exists)
Base.metadata.create_all(bind=engine)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "EventSphere API - Ready for bookings!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
