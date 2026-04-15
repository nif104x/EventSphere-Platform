from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.notifications import send_email_resend


def send_customer_due_reminders(db: Session):
    tomorrow = date.today() + timedelta(days=1)

    events = db.execute(
        text(
            """
            SELECT e.id AS event_id, e.event_date, e.customer_id, ci.full_name, ci.email
            FROM events e
            JOIN customer_info ci ON ci.customer_id = e.customer_id
            WHERE e.event_date = :tomorrow
            """
        ),
        {"tomorrow": tomorrow},
    ).mappings().all()

    sent = []
    skipped = []
    failed = []

    for ev in events:
        orders = db.execute(
            text(
                """
                SELECT eo.id AS order_id
                FROM event_orders eo
                WHERE eo.event_id = :eid
                ORDER BY eo.id
                """
            ),
            {"eid": ev["event_id"]},
        ).mappings().all()

        for o in orders:
            milestones = db.execute(
                text(
                    """
                    SELECT id, amount, due_date, status
                    FROM payment_milestones
                    WHERE order_id = :oid AND status <> 'Paid'
                    ORDER BY due_date
                    """
                ),
                {"oid": o["order_id"]},
            ).mappings().all()

            if not milestones:
                skipped.append(
                    {
                        "event_id": ev["event_id"],
                        "order_id": o["order_id"],
                        "reason": "no unpaid milestones",
                    }
                )
                continue

            total_due = 0.0
            lines = []
            for m in milestones:
                amt = float(m["amount"])
                total_due += amt
                lines.append(
                    f"- {m['id']}: amount {amt:.2f}, due {m['due_date']} ({m['status']})"
                )

            subject = "EventSphere reminder: payment due before your event"
            msg = (
                f"Hello {ev['full_name']},\n\n"
                f"Your event is tomorrow ({ev['event_date']}).\n"
                f"Total due: {total_due:.2f}\n\n"
                f"Milestones:\n" + "\n".join(lines) + "\n\n"
                "Please complete your payment.\n"
            )

            try:
                send_email_resend(to_email=ev["email"], subject=subject, text=msg)
                sent.append(
                    {
                        "event_id": ev["event_id"],
                        "order_id": o["order_id"],
                        "to": ev["email"],
                        "total_due": total_due,
                    }
                )
            except Exception as e:
                failed.append(
                    {
                        "event_id": ev["event_id"],
                        "order_id": o["order_id"],
                        "to": ev["email"],
                        "error": str(e),
                    }
                )

    return {"tomorrow": str(tomorrow), "sent": sent, "skipped": skipped, "failed": failed}

