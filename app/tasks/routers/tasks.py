import os

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.tasks.services.reminders import send_customer_due_reminders


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/send-customer-reminders")
def send_customer_reminders(
    x_task_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    token = os.getenv("TASK_TOKEN", "")
    if token and x_task_token != token:
        raise HTTPException(status_code=401, detail="Invalid task token")
    return send_customer_due_reminders(db)

