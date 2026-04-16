"""
<form method="POST" action="/send_message">
    <input type="hidden" name="event_id" value="{{ event_id }}">
    <input type="hidden" name="room_id" value="{{ room_id }}">
    
    <input type="text" name="text" placeholder="Type your message..." required>
    <button type="submit">Send</button>
</form>
"""

"""
@router.post("/customer/send_message")
def customer_send_message(
    room_id: str = Form(...),
    text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.CustomerInfo = Depends(oauth2.get_current_user)
):
    # Pass the customer's ID as the sender
    saved_msg = save_chat_message(
        db=db, 
        room_id=room_id, 
        sender_id=current_user.customer_id, 
        text=text
    )
    return {"status": "success", "msg_id": saved_msg.id}
"""


import uuid
from sqlalchemy.orm import Session
from app.organizer import models

def save_chat_message(db: Session, room_id: str, sender_id: str, text: str):

    msg_id = f"MSG-{str(uuid.uuid4())[:8]}"
    
    new_message = models.Message(
        id=msg_id,
        room_id=room_id,
        sender_id=sender_id, 
        message_text=text
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    return new_message