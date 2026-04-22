from fastapi import FastAPI, HTTPException, status, Response, Depends, APIRouter
from sqlalchemy.orm import Session 
from datetime import timedelta

from app.organizer import models, schemas, database, utils, ouath2


router = APIRouter(
    tags = ["Authentication"]
)


# @router.post("/organizerLogin", response_model=schemas.OrganizerInfoSchema)
# @router.post("/organizerLogin", response_model=schemas.Token)

def login(user_credentials: schemas.userLoginSchema, db: Session=Depends(database.get_db)):
    user = db.query(models.UserMain).filter(models.UserMain.username==user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid credential")
    
    if not utils.verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid credential")

    # info = db.query(models.OrganizerInfo).filter(models.OrganizerInfo.org_id==user.id).first()

    access_token = ouath2.create_access_token(
        data = {"user_id": user.id},
        expires_delta=timedelta(minutes=ouath2.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}


