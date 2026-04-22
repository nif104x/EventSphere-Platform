from fastapi import FastAPI, HTTPException, status, Response, Depends, APIRouter
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.organizer.database import get_db
from app.organizer import models, schemas, utils, ouath2, database
from app.organizer.routers import auth

import uuid

# For jinja2 templates
from fastapi import Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse


templates = Jinja2Templates(directory="app/organizer/templates")


router = APIRouter(
    prefix="/customer",
    tags = ["customer"]
)

@router.get("/message", name="message", include_in_schema=False)
def message(request: Request,
            db: Session=Depends(get_db),
            current_user: models.CustomerInfo=Depends(ouath2.get_current_user)
):
    
    rooms = db.query(models.ChatRoom).filter(
        models.ChatRoom.customer_id == current_user.customer_id
    ).all()

    return templates.TemplateResponse(
        request, 
        "customer/message.html", 
        {"rooms": rooms}
    )


@router.get("/messages/{room_id}", include_in_schema=False)
def get_room_messages(
    room_id: str, 
    db: Session = Depends(get_db),
    current_user: models.CustomerInfo = Depends(ouath2.get_current_user)
):
    messages = db.query(models.Message).filter(
        models.Message.room_id == room_id
    ).order_by(models.Message.timestamp.asc()).all()


    msg_list = []
    for m in messages:
        msg_list.append({
            "text": m.message_text,
            "is_mine": m.sender_id == current_user.customer_id, 
            "time": m.timestamp.strftime("%I:%M %p") 
        })

    return {"messages": msg_list}


from app.chat.chat import save_chat_message

@router.post("/message")
def customer_send_message(
    room_id: str = Form(...),
    text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.CustomerInfo = Depends(ouath2.get_current_user)
):

    saved_msg = save_chat_message(
        db=db, 
        room_id=room_id, 
        sender_id=current_user.customer_id, 
        text=text
    )
    return {"status": "success", "msg_id": saved_msg.id}
