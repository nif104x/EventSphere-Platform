from fastapi import FastAPI, HTTPException, status, Response, Depends, APIRouter
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text

from app.paths import APP_DIR
from app.organizer.database import get_db
from app.organizer import models, schemas, utils, ouath2, database
from app.organizer.routers import auth

import uuid

# For jinja2 templates
from fastapi import Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse


templates = Jinja2Templates(directory=str(APP_DIR / "organizer" / "templates"))


router = APIRouter(
    prefix="/organizer",
    tags = ["organizer"]
)



# @router.get("/", response_model=list[schemas.OrganizerInfoSchema])
# def homePage(db: Session=Depends(get_db), current_user: models.OrganizerInfo = Depends(ouath2.get_current_user)):
#     users = db.query(models.OrganizerInfo).all()
#     return users

@router.get("/dashboard", name="dashboard", include_in_schema=False)
def dashboard_page(request: Request, current_user: models.OrganizerInfo = Depends(ouath2.get_current_user), db: Session=Depends(get_db)):
    analytics = db.query(models.VendorAnalytics).filter(models.VendorAnalytics.org_id==current_user.org_id).first()
    
    orders_pending = (
        db.query(models.Event)
        .options(
            joinedload(models.Event.customer),
            joinedload(models.Event.order).joinedload(models.EventOrder.listing),
        )
        .filter(
            models.Event.org_id == current_user.org_id,
            models.Event.status == models.EventStatusEnum.Pending,
        )
        .all()
    )

    gigs = db.query(models.ServiceListing).options(
        joinedload(models.ServiceListing.images)
    ).filter(
        models.ServiceListing.org_id == current_user.org_id
    ).all()

    average_rating = db.query(func.avg(models.VendorReview.rating)).filter(
        models.VendorReview.vendor_id == current_user.org_id
        ).scalar()
    
    display_rating = round(average_rating, 1) if average_rating else "0.0"

    completed = (
        db.query(models.Event)
        .options(
            joinedload(models.Event.order),
            joinedload(models.Event.customer),
        )
        .filter(
            models.Event.org_id == current_user.org_id,
            models.Event.status == models.EventStatusEnum.Completed,
        )
        .all()
    )

    review_rows = (
        db.query(
            models.VendorReview,
            models.Event.event_date,
            models.CustomerInfo.full_name,
            models.Event.customer_id,
            models.CustomerInfo.email,
            models.CustomerInfo.phone,
        )
        .join(models.Event, models.Event.id == models.VendorReview.event_id)
        .outerjoin(models.CustomerInfo, models.CustomerInfo.customer_id == models.Event.customer_id)
        .filter(models.VendorReview.vendor_id == current_user.org_id)
        .order_by(models.Event.event_date.desc().nullslast(), models.VendorReview.id.desc())
        .limit(25)
        .all()
    )
    recent_reviews = [
        {
            "rating": int(vr.rating or 0),
            "comment": (vr.comment or "").strip(),
            "event_date": ev_dt,
            "customer_name": (fn or cid or "Customer"),
            "event_id": vr.event_id,
            "customer_email": em,
            "customer_phone": ph,
        }
        for vr, ev_dt, fn, cid, em, ph in review_rows
    ]

    return templates.TemplateResponse(
        request=request, 
        name="organizer/dashboard.html", 
        context={
            "request": request, 
            "user": current_user, 
            "gigs": gigs,             
            "analytics": analytics, 
            "pending": orders_pending,
            "rating": display_rating,
            "completed": completed,
            "recent_reviews": recent_reviews,
        }
    )


@router.post(
    "/pending-event-action",
    name="organizer_pending_event_action",
    include_in_schema=False,
)
def organizer_pending_event_action(
    request: Request,
    event_id: str = Form(...),
    action: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.OrganizerInfo = Depends(ouath2.get_current_user),
):
    """Confirm or decline a pending event for the signed-in organizer (Jinja cookie session)."""
    aid = (action or "").strip().lower()
    if aid not in ("confirm", "decline"):
        raise HTTPException(status_code=400, detail="action must be confirm or decline")
    eid = (event_id or "").strip()
    if not eid:
        raise HTTPException(status_code=400, detail="event_id required")
    row = db.execute(
        text(
            """
        SELECT id, status::text AS status FROM events
        WHERE id = :event_id AND org_id = :org_id
    """
        ),
        {"event_id": eid, "org_id": current_user.org_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found for this organizer")
    m = dict(row._mapping)
    if m.get("status") != "Pending":
        raise HTTPException(
            status_code=400, detail="Only pending events can be confirmed or declined"
        )
    if aid == "confirm":
        db.execute(
            text(
                """
            UPDATE events SET status = 'Confirmed'::event_status
            WHERE id = :event_id AND org_id = :org_id
        """
            ),
            {"event_id": eid, "org_id": current_user.org_id},
        )
    else:
        db.execute(
            text(
                """
            UPDATE events SET status = 'Cancelled'::event_status
            WHERE id = :event_id AND org_id = :org_id
        """
            ),
            {"event_id": eid, "org_id": current_user.org_id},
        )
    db.commit()
    return RedirectResponse(url=request.url_for("dashboard"), status_code=303)







@router.get("/creategig", name="creategig", include_in_schema=False)
def creategig(request: Request):
    return templates.TemplateResponse(request, "organizer/creategig.html", {'data':1})


@router.post("/creategig", name="handle_create_gig", include_in_schema=False)
def handle_create_gig(
    request: Request,
    form:schemas.GigCreateRequest = Depends(),
    db:Session=Depends(get_db),
    current_user: models.OrganizerInfo = Depends(ouath2.get_current_user)
):
    listing_id = f"LIST-{uuid.uuid4().hex[:6].upper()}"
    new_gig = models.ServiceListing(
        id=listing_id,
        org_id=current_user.org_id,
        title = form.title,
        category=form.category,
        base_price = form.base_price,
        is_deleted=False,
    )
    db.add(new_gig)
    image_id = f"IMG-{uuid.uuid4().hex[:6].upper()}"
    new_image = models.ListingImage(
        id=image_id,
        listing_id=listing_id,
        image_url=form.image_url
    )
    db.add(new_image)

    for name, price in zip(form.addon_names, form.addon_prices):
        if name.strip():  
            addon_id = f"ADD-{str(uuid.uuid4())[:8]}"
            new_addon = models.ServiceAddon(
                id=addon_id,
                listing_id=listing_id,
                addon_name=name,
                price=price
            )
            db.add(new_addon)

    db.commit()

    return RedirectResponse(
        url=request.url_for("dashboard"), 
        status_code=303
    )



@router.get("/message", name="message", include_in_schema=False)
def message(request: Request,
            db: Session=Depends(get_db),
            current_user: models.OrganizerInfo=Depends(ouath2.get_current_user)
):
    rooms = (
        db.query(models.ChatRoom)
        .options(joinedload(models.ChatRoom.customer))
        .filter(models.ChatRoom.org_id == current_user.org_id)
        .all()
    )

    return templates.TemplateResponse(
        request, 
        "organizer/message.html", 
        {"rooms": rooms}
    )



@router.get("/messages/{room_id}", include_in_schema=False)
def get_room_messages(
    room_id: str, 
    db: Session = Depends(get_db),
    current_user: models.OrganizerInfo = Depends(ouath2.get_current_user)
):
    room = (
        db.query(models.ChatRoom)
        .filter(
            models.ChatRoom.id == room_id,
            models.ChatRoom.org_id == current_user.org_id,
        )
        .first()
    )
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    messages = db.query(models.Message).filter(
        models.Message.room_id == room_id
    ).order_by(models.Message.timestamp.asc()).all()

    # Format them for JavaScript
    msg_list = []
    for m in messages:
        msg_list.append({
            "text": m.message_text,
            # We need to know who sent it to style it left (received) or right (sent)
            "is_mine": m.sender_id == current_user.org_id, 
            "time": m.timestamp.strftime("%I:%M %p") 
        })

    return {"messages": msg_list}

from app.chat.chat import save_chat_message
@router.post("/message")
def organizer_send_message(
    room_id: str = Form(...),
    text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.OrganizerInfo = Depends(ouath2.get_current_user)
):
    room = (
        db.query(models.ChatRoom)
        .filter(
            models.ChatRoom.id == room_id,
            models.ChatRoom.org_id == current_user.org_id,
        )
        .first()
    )
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    # Pass the organizer's ID as the sender
    saved_msg = save_chat_message(
        db=db, 
        room_id=room_id, 
        sender_id=current_user.org_id, 
        text=text
    )
    return {"status": "success", "msg_id": saved_msg.id}


## Registration ##
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




# LOG IN HANDLING:
@router.get("/login", name="login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request,"organizer/login.html", {"request": request})

# @router.post("/login", name="login_post")
# def login(request:Request, username:str=Form(...), password: str = Form(...), db: Session=Depends(database.get_db)):
#     user_credentials = schemas.userLoginSchema(username=username, password=password)
#     auth_data = auth.login(user_credentials=user_credentials, db=db)

#     token = auth_data["access_token"]

#     redirect = RedirectResponse(url= request.url_for("dashboard"), status_code=status.HTTP_303_SEE_OTHER)
#     redirect.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True, path="/")

#     return redirect

from datetime import timedelta

@router.post("/login", name="login_post")
def login(request:Request, username:str=Form(...), password: str = Form(...), db: Session=Depends(database.get_db)):
    username = (username or "").strip()
    password = (password or "").strip()
    user = db.query(models.UserMain).filter(models.UserMain.username==username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid credential")
    
    if not utils.password_matches_stored(password, user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid credential")

    access_token = ouath2.create_access_token(
        data = {"user_id": user.id},
        expires_delta=timedelta(minutes=ouath2.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    redirect = RedirectResponse(url= request.url_for("dashboard"), status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, path="/")

    return redirect


# @router.get("/chatbot", response_class=HTMLResponse)
# def dashboard_page(request: Request, current_user: models.OrganizerInfo = Depends(ouath2.get_current_user), db: Session=Depends(get_db)):
#         past_chats = db.query(models.ChatbotInteraction).filter(models.ChatbotInteraction.customer_id==current_user.org_id).order_by(models.ChatbotInteraction.timestamp.asc()).all()

#         clean_history = []
#         for chat in past_chats:
#             if isinstance(chat.ai_response, dict):
#                 ai_text = chat.ai_response.get("reply", "Error: No reply text found.")
#             else:
#                 ai_text = str(chat.ai_response)
            
#             clean_history.append({
#                  "query_text": chat.query_text,
#                  "ai_text": chat.ai_text,
#                  "time": chat.timestamp.strftime('%I:%M %p') if chat.timestamp else ""
#             })

#         return templates.TemplateResponse(
#             request,
#             "organizer/chatbot.html",
#             {
#                 "request": request,
#                 "history": clean_history 
#             }
#         )