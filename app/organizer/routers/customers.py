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




from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

@router.get("/chatbot", response_class=HTMLResponse)
def chat(request: Request, db: Session=Depends(get_db)):
        past_chats = db.query(models.ChatbotInteraction).filter(models.ChatbotInteraction.customer_id=="CUST-01").order_by(models.ChatbotInteraction.timestamp.asc()).all()

        clean_history = []
        for chat in past_chats:
            if isinstance(chat.ai_response, dict):
                ai_text = chat.ai_response.get("reply", "Error: No reply text found.")
            else:
                ai_text = str(chat.ai_response)
            
            clean_history.append({
                 "query_text": chat.query_text,
                 "ai_text": chat.ai_response,
                 "time": chat.timestamp.strftime('%I:%M %p') if chat.timestamp else ""
            })

        return templates.TemplateResponse(
            request,
            "organizer/chatbot.html",
            {
                "request": request,
                "history": clean_history 
            }
        )

# current_user: models.CustomerInfo = Depends(ouath2.get_current_user)
"""
in js:
const response = await fetch('/chatbot/ask', { 
    method: 'POST',
    credentials: 'include', // <--- ADD THIS LINE so it sends your login cookie!
    body: formData
});
"""
@router.post("/chatbot")
def chat_res(request:Request,
             query_text= Form(...), 
             db:Session=Depends(get_db)):
    
    services = get_service_listings_dict(db)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful event gigs recommendation chatbot."},
            {"role": "user", "content": f"User query: {query_text}\n\nProduct data: {services}\n\n Direction: If the user is not asking about event services, respond naturally as a casual EventSphere assistant; if they do request services, provide the most relevant and complete answer including required details like organization ID, company name, and any other necessary information to help the customer clearly understand the next steps."}
        ],
        temperature=0.7
    )

    ai_text = response.choices[0].message.content

    ai_json = {
        "reply": ai_text
    }

    chat_entry = models.ChatbotInteraction(
        id=str(uuid.uuid4()),
        customer_id="CUST-01",
        query_text=query_text,
        ai_response=ai_json
    )
    db.add(chat_entry)
    db.commit()
    db.refresh(chat_entry)

    return {
        "reply": ai_text
    }



#############################
def get_service_listings_dict(db: Session):
    listings = db.query(models.ServiceListing).all()
    
    listings_dict = {}
    
    for gig in listings:
        addon_data = [
            {
                "id": addon.id,
                "addon_name": addon.addon_name,
                "price": float(addon.price)
            }
            for addon in gig.addons
        ]
        
        listings_dict[gig.id] = {
            "id": gig.id,
            "org_id": gig.org_id,
            "category": gig.category,
            "title": gig.title,
            "base_price": float(gig.base_price),
            "addons": addon_data
        }
        
    return listings_dict