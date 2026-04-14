import os
from datetime import date, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware

from app.admin.services.services import (
    ban_or_unban_user,
    delete_listing_soft,
    get_orders_for_admin,
    get_users_for_admin,
    list_listings_for_admin,
)
from app.search.services.services import search_listings
from app.db import get_conn
from app.notifications import send_email_resend

load_dotenv()

app = FastAPI(title="EventSphere API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home_page():
    return {"message": "EventSphere API running"}


@app.get("/admin/listings")
def admin_listings():
    return list_listings_for_admin()


@app.delete("/admin/listings/{listing_id}")
def admin_delete_listing(listing_id: str):
    ok = delete_listing_soft(listing_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"message": "Listing deleted (soft delete)"}


@app.get("/admin/orders")
def admin_orders():
    return get_orders_for_admin()


@app.get("/admin/users")
def admin_users():
    return get_users_for_admin()


@app.patch("/admin/users/{user_id}/status")
def admin_set_user_status(user_id: str, body: dict):
    status = body.get("status")
    reason = body.get("reason")
    if not status:
        raise HTTPException(status_code=400, detail="status is required")

    ok = ban_or_unban_user(user_id=user_id, status=status, reason=reason)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User status updated"}


@app.get("/search")
def search(
    query: str | None = Query(default=None),
    category: str | None = Query(default=None),
    min_price: float | None = Query(default=None),
    max_price: float | None = Query(default=None),
):
    return search_listings(
        query=query,
        category=category,
        min_price=min_price,
        max_price=max_price,
    )


@app.post("/tasks/send-customer-reminders")
def send_customer_reminders(x_task_token: str | None = Header(default=None)):
    token = os.getenv("TASK_TOKEN", "")
    if token and x_task_token != token:
        raise HTTPException(status_code=401, detail="Invalid task token")

    tomorrow = date.today() + timedelta(days=1)

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
              e.id AS event_id,
              e.event_date,
              e.customer_id,
              ci.full_name,
              ci.email
            FROM events e
            JOIN customer_info ci ON ci.customer_id = e.customer_id
            WHERE e.event_date = %s;
            """,
            (tomorrow,),
        )
        events = cur.fetchall()

        sent = []
        skipped = []
        failed = []

        for ev in events:
            cur.execute(
                """
                SELECT eo.id AS order_id
                FROM event_orders eo
                WHERE eo.event_id = %s
                ORDER BY eo.id;
                """,
                (ev["event_id"],),
            )
            orders = cur.fetchall()

            for o in orders:
                cur.execute(
                    """
                    SELECT id, amount, due_date, status
                    FROM payment_milestones
                    WHERE order_id = %s AND status <> 'Paid'
                    ORDER BY due_date;
                    """,
                    (o["order_id"],),
                )
                milestones = cur.fetchall()
                if not milestones:
                    skipped.append(
                        {
                            "event_id": ev["event_id"],
                            "order_id": o["order_id"],
                            "reason": "no unpaid milestones",
                        }
                    )
                    continue

                lines = []
                total_due = 0.0
                for m in milestones:
                    amt = float(m["amount"])
                    total_due += amt
                    lines.append(f"- {m['id']}: amount {amt:.2f}, due {m['due_date']} ({m['status']})")

                subject = "EventSphere reminder: payment due before your event"
                text = (
                    f"Hello {ev['full_name']},\n\n"
                    f"Your event is tomorrow ({ev['event_date']}).\n"
                    f"Total due: {total_due:.2f}\n\n"
                    f"Milestones:\n" + "\n".join(lines) + "\n\n"
                    "Please complete your payment.\n"
                )

                try:
                    send_email_resend(to_email=ev["email"], subject=subject, text=text)
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
    finally:
        conn.close()


