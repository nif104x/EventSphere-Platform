from fastapi import FastAPI
from app.organizer.routers import user, auth
from app.organizer import models
from app.organizer.database import engine
from fastapi.staticfiles import StaticFiles

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/organizer/static"), name="static")


app.include_router(user.router)
app.include_router(auth.router)                   


