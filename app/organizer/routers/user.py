from fastapi import FastAPI, HTTPException, status, Response, Depends, APIRouter
from sqlalchemy.orm import Session 

from app.organizer.database import get_db
from app.organizer import models, schemas, utils, ouath2

import uuid

# For jinja2 templates
from fastapi import Request
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="app/organizer/templates")


router = APIRouter(
    prefix="/organizer",
    tags = ["organizer"]
)



# @router.get("/", response_model=list[schemas.OrganizerInfoSchema])
# def homePage(db: Session=Depends(get_db), current_user: models.OrganizerInfo = Depends(ouath2.get_current_user)):
#     users = db.query(models.OrganizerInfo).all()
#     return users

@router.get("/dashboard", name="dashboard", include_in_schema=False)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "organizer/dashboard.html", {'data':1})

@router.get("/creategig", name="creategig", include_in_schema=False)
def creategig(request: Request):
    return templates.TemplateResponse(request, "organizer/creategig.html", {'data':1})

@router.get("/message", name="message", include_in_schema=False)
def message(request: Request):
    return templates.TemplateResponse(request, "organizer/message.html", {'data':1})



@router.post("/registration", status_code=status.HTTP_201_CREATED)
def user_registration(data:schemas.OrganizerRegisterSchema, db : Session=Depends(get_db)):
    new_user_id = f"ORG-{uuid.uuid4().hex[:6].upper()}"
    hashed_password = utils.hash_password(data.password)
    if db.query(models.OrganizerInfo).filter(models.OrganizerInfo.email==data.email).first():
        raise HTTPException(400, "Email already exist")
    # insert into user_main
    user = models.UserMain(
        id = new_user_id,
        username = data.username,
        password = hashed_password,
        role = data.role
    )
    db.add(user)

    # insert into organizer_info
    organizer = models.OrganizerInfo(
            org_id = new_user_id,
            email = data.email,
            company_name = data.company_name,
            primary_category = data.primary_category,
            is_verified = data.is_verified,      
    )
    db.add(organizer)
    db.commit()
    return{"message": "Organizer created successfully"}





