from datetime import date, timedelta

from sqlalchemy.orm import Session, joinedload

from app.models import Event, EventOrder
from app.notifications import send_email_resend


def send_customer_due_reminders(db: Session):
    tomorrow = date.today() + timedelta(days=1)

    events = (
        db.query(Event)
        .options(
            joinedload(Event.customer),
            joinedload(Event.orders).joinedload(EventOrder.milestones),
        )
        .filter(Event.event_date == tomorrow)
        .all()
    )

    sent = []
    skipped = []
    failed = []

    for ev in events:
        if not ev.customer:
            continue
        for o in ev.orders or []:
            milestones = [m for m in (o.milestones or []) if m.status != "Paid"]

            if not milestones:
                skipped.append(
                    {
                        "event_id": ev.id,
                        "order_id": o.id,
                        "reason": "no unpaid milestones",
                    }
                )
                continue

            total_due = 0.0
            lines = []
            for m in milestones:
                amt = float(m.amount)
                total_due += amt
                lines.append(
                    f"- {m.id}: amount {amt:.2f}, due {m.due_date} ({m.status})"
                )

            cust = ev.customer
            subject = "EventSphere reminder: payment due before your event"
            msg = (
                f"Hello {cust.full_name},\n\n"
                f"Your event is tomorrow ({ev.event_date}).\n"
                f"Total due: {total_due:.2f}\n\n"
                f"Milestones:\n" + "\n".join(lines) + "\n\n"
                "Please complete your payment.\n"
            )

            try:
                send_email_resend(to_email=cust.email, subject=subject, text=msg)
                sent.append(
                    {
                        "event_id": ev.id,
                        "order_id": o.id,
                        "to": cust.email,
                        "total_due": total_due,
                    }
                )
            except Exception as e:
                failed.append(
                    {
                        "event_id": ev.id,
                        "order_id": o.id,
                        "to": cust.email,
                        "error": str(e),
                    }
                )

    return {"tomorrow": str(tomorrow), "sent": sent, "skipped": skipped, "failed": failed}
