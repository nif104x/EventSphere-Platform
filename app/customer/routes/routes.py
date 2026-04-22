import uuid
from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Optional

from app.customer.database import get_db
from app.organizer import ouath2

router = APIRouter(prefix="/api", tags=["api"])

_bearer = HTTPBearer(auto_error=False)


def _fmt_msg_time(ts) -> str:
    if ts is None:
        return ""
    if isinstance(ts, datetime):
        return ts.strftime("%I:%M %p")
    return str(ts)[:8]


def get_current_customer_id(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> str:
    """JWT from customer login (same secret as organizer); must be a Customer profile."""
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    raw_token = (creds.credentials or "").strip()
    if not raw_token or raw_token.lower() in ("undefined", "null"):
        raise credentials_exception
    try:
        payload = jwt.decode(
            raw_token,
            ouath2.SECRET_KEY,
            algorithms=[ouath2.ALGORITHM],
            leeway=timedelta(seconds=120),
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except PyJWTError:
        raise credentials_exception from None
    uid = payload.get("user_id")
    if uid is None:
        raise credentials_exception
    user_id = str(uid)
    row = db.execute(
        text(
            """
            SELECT c.customer_id AS customer_id
            FROM customer_info c
            WHERE c.customer_id = :uid
            """
        ),
        {"uid": user_id},
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a customer session",
        )
    return dict(row._mapping)["customer_id"]


_ALLOWED_TABLES = frozenset({"events", "event_orders", "vendor_reviews"})


def _next_seq(db: Session, table: str, id_column: str, prefix: str) -> str:
    """Next id like EVT-004 / ORD-004 / REV-003 using trailing digits."""
    if table not in _ALLOWED_TABLES or id_column != "id":
        raise ValueError("Invalid id sequence target")
    result = db.execute(
        text(
            f"""
        SELECT COALESCE(MAX(CAST((regexp_match({id_column}, :pat))[1] AS INTEGER)), 0) + 1
        FROM {table}
        """
        ),
        {"pat": f"^{prefix}-(\\d+)$"},
    )
    n = result.scalar()
    return f"{prefix}-{n:03d}"


class EventCreate(BaseModel):
    customer_id: str
    org_id: str
    event_date: str  # YYYY-MM-DD


class OrderCreate(BaseModel):
    event_id: str
    listing_id: str
    base_price: float
    addons_cost: float = 0.0
    total_price: float


class EventCompleteBody(BaseModel):
    org_id: str


class RatingCreate(BaseModel):
    customer_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class OrganizerEventRespond(BaseModel):
    org_id: str
    action: str  # "confirm" | "decline"


class CustomerLoginIn(BaseModel):
    username: str
    password: str


@router.post("/customer/login")
def customer_login(body: CustomerLoginIn, db: Session = Depends(get_db)):
    """Same credential rules as organizer Jinja login: user_main row + plaintext password + Customer role."""
    row = db.execute(
        text(
            """
        SELECT u.id AS id, u.password AS password, u.role::text AS role, c.full_name AS full_name
        FROM user_main u
        INNER JOIN customer_info c ON c.customer_id = u.id
        WHERE u.username = :username
        LIMIT 1
        """
        ),
        {"username": body.username.strip()},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Invalid credential")
    m = dict(row._mapping)
    if m.get("password") != body.password:
        raise HTTPException(status_code=404, detail="Invalid credential")
    role = (m.get("role") or "").strip()
    if role != "Customer" and not role.endswith(".Customer"):
        raise HTTPException(status_code=403, detail="Not a customer account")

    access_token = ouath2.create_access_token(
        data={"user_id": m["id"]},
        expires_delta=timedelta(minutes=ouath2.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "customer_id": m["id"],
        "full_name": m["full_name"],
        "username": body.username.strip(),
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/organizers")
def get_organizers(db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
        SELECT o.org_id AS org_id, o.company_name AS company_name, o.email AS email,
               o.primary_category AS primary_category, o.is_verified AS is_verified,
               COALESCE((
                 SELECT ROUND(AVG(v.rating::numeric), 2)
                 FROM vendor_reviews v WHERE v.vendor_id = o.org_id
               ), 0) AS avg_rating,
               COALESCE((
                 SELECT COUNT(*)::int FROM vendor_reviews v WHERE v.vendor_id = o.org_id
               ), 0) AS review_count
        FROM organizer_info o
        ORDER BY o.company_name
    """
        )
    )
    rows = [dict(row._mapping) for row in result.fetchall()]
    for r in rows:
        if r.get("avg_rating") is not None:
            r["avg_rating"] = float(r["avg_rating"])
    return rows


@router.get("/services/{org_id}")
def get_services(org_id: str, db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
        SELECT id AS id, category AS category, title AS title, base_price AS base_price
        FROM service_listings
        WHERE org_id = :org_id
    """
        ),
        {"org_id": org_id},
    )
    return [dict(row._mapping) for row in result.fetchall()]


@router.get("/addons/{listing_id}")
def get_addons(listing_id: str, db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
        SELECT id AS id, addon_name AS name, price AS price
        FROM service_addons
        WHERE listing_id = :listing_id
    """
        ),
        {"listing_id": listing_id},
    )
    return [dict(row._mapping) for row in result.fetchall()]


@router.post("/events")
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    event_id = _next_seq(db, "events", "id", "EVT")
    db.execute(
        text(
            """
        INSERT INTO events (id, customer_id, org_id, event_date, status)
        VALUES (:id, :customer_id, :org_id, :event_date, 'Pending')
    """
        ),
        {
            "id": event_id,
            "customer_id": event.customer_id,
            "org_id": event.org_id,
            "event_date": event.event_date,
        },
    )
    db.commit()
    return {"event_id": event_id}


@router.post("/orders")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    order_id = _next_seq(db, "event_orders", "id", "ORD")
    db.execute(
        text(
            """
        INSERT INTO event_orders (id, event_id, listing_id, base_price_at_booking, total_addons_cost, final_total_price, payment_status)
        VALUES (:id, :event_id, :listing_id, :base_price, :addons_cost, :total_price, 'Unpaid')
    """
        ),
        {
            "id": order_id,
            "event_id": order.event_id,
            "listing_id": order.listing_id,
            "base_price": order.base_price,
            "addons_cost": order.addons_cost,
            "total_price": order.total_price,
        },
    )
    db.commit()
    return {"order_id": order_id}


@router.patch("/events/{event_id}/complete")
def mark_event_complete(
    event_id: str, body: EventCompleteBody, db: Session = Depends(get_db)
):
    """Organizer marks an event completed (required before customers may rate)."""
    r = db.execute(
        text(
            """
        UPDATE events SET status = 'Completed'
        WHERE id = :event_id AND org_id = :org_id
        RETURNING id
    """
        ),
        {"event_id": event_id, "org_id": body.org_id},
    )
    if r.first() is None:
        raise HTTPException(status_code=404, detail="Event not found for this organizer")
    db.commit()
    return {"ok": True, "event_id": event_id, "status": "Completed"}


@router.post("/events/{event_id}/rating")
def submit_rating(
    event_id: str, body: RatingCreate, db: Session = Depends(get_db)
):
    """Customer rates vendor after the event is completed."""
    row = db.execute(
        text(
            """
        SELECT e.customer_id AS customer_id, e.org_id AS org_id, e.status AS status
        FROM events e WHERE e.id = :event_id
    """
        ),
        {"event_id": event_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    m = dict(row._mapping)
    if m["customer_id"] != body.customer_id:
        raise HTTPException(status_code=403, detail="Not your event")
    if str(m["status"]) != "Completed":
        raise HTTPException(
            status_code=400, detail="You can only rate after the event is completed"
        )
    exists = db.execute(
        text("SELECT 1 FROM vendor_reviews WHERE event_id = :event_id LIMIT 1"),
        {"event_id": event_id},
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Already rated this event")

    rev_id = _next_seq(db, "vendor_reviews", "id", "REV")
    comment = body.comment if body.comment else None
    db.execute(
        text(
            """
        INSERT INTO vendor_reviews (id, event_id, vendor_id, rating, comment)
        VALUES (:id, :event_id, :vendor_id, :rating, :comment)
    """
        ),
        {
            "id": rev_id,
            "event_id": event_id,
            "vendor_id": m["org_id"],
            "rating": body.rating,
            "comment": comment,
        },
    )
    db.commit()

    return {"review_id": rev_id}


@router.patch("/events/{event_id}/organizer-response")
def organizer_respond_to_event(
    event_id: str, body: OrganizerEventRespond, db: Session = Depends(get_db)
):
    """Confirm (Pending→Confirmed) or decline (Pending→Cancelled) an event for this organizer."""
    if body.action not in ("confirm", "decline"):
        raise HTTPException(status_code=400, detail="action must be confirm or decline")
    row = db.execute(
        text(
            """
        SELECT id, status::text AS status FROM events
        WHERE id = :event_id AND org_id = :org_id
    """
        ),
        {"event_id": event_id, "org_id": body.org_id},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found for this organizer")
    m = dict(row._mapping)
    if m.get("status") != "Pending":
        raise HTTPException(status_code=400, detail="Only pending events can be confirmed or declined")
    if body.action == "confirm":
        db.execute(
            text(
                """
            UPDATE events SET status = 'Confirmed'::event_status
            WHERE id = :event_id AND org_id = :org_id
        """
            ),
            {"event_id": event_id, "org_id": body.org_id},
        )
        out_status = "Confirmed"
    else:
        db.execute(
            text(
                """
            UPDATE events SET status = 'Cancelled'::event_status
            WHERE id = :event_id AND org_id = :org_id
        """
            ),
            {"event_id": event_id, "org_id": body.org_id},
        )
        out_status = "Cancelled"
    db.commit()
    return {"ok": True, "event_id": event_id, "status": out_status}


@router.get("/organizer/{org_id}/reviews")
def organizer_reviews(org_id: str, db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
        SELECT vr.id AS id, vr.rating AS rating, vr.comment AS comment, vr.event_id AS event_id,
               e.event_date AS event_date,
               COALESCE(ci.full_name, e.customer_id) AS customer_name
        FROM vendor_reviews vr
        JOIN events e ON e.id = vr.event_id AND e.org_id = :org_id
        LEFT JOIN customer_info ci ON ci.customer_id = e.customer_id
        WHERE vr.vendor_id = :org_id
        ORDER BY e.event_date DESC NULLS LAST, vr.id DESC
        LIMIT 25
    """
        ),
        {"org_id": org_id},
    )
    rows = [dict(row._mapping) for row in result.fetchall()]
    return rows


@router.get("/organizer/{org_id}/listings")
def organizer_listings(org_id: str, db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
        SELECT sl.id AS id, sl.title AS title, sl.category AS category, sl.base_price AS base_price,
               (SELECT li.image_url FROM listing_images li WHERE li.listing_id = sl.id LIMIT 1) AS image_url
        FROM service_listings sl
        WHERE sl.org_id = :org_id
        ORDER BY sl.title
    """
        ),
        {"org_id": org_id},
    )
    rows = [dict(row._mapping) for row in result.fetchall()]
    for r in rows:
        if r.get("base_price") is not None:
            r["base_price"] = float(r["base_price"])
    return rows


@router.get("/customer/{customer_id}/dashboard")
def get_dashboard(customer_id: str, db: Session = Depends(get_db)):
    events_result = db.execute(
        text(
            """
        SELECT e.id AS id, e.event_date AS event_date, e.status AS status,
               o.company_name AS company_name, e.org_id AS org_id,
               (SELECT vr.rating FROM vendor_reviews vr WHERE vr.event_id = e.id LIMIT 1) AS my_rating,
               CASE
                 WHEN e.status::text = 'Completed'
                      AND NOT EXISTS (SELECT 1 FROM vendor_reviews r2 WHERE r2.event_id = e.id)
                 THEN true
                 ELSE false
               END AS can_rate
        FROM events e
        JOIN organizer_info o ON e.org_id = o.org_id
        WHERE e.customer_id = :customer_id
        ORDER BY e.event_date DESC
    """
        ),
        {"customer_id": customer_id},
    )

    orders_result = db.execute(
        text(
            """
        SELECT eo.id AS id, eo.event_id AS event_id, eo.final_total_price AS final_total_price,
               eo.payment_status AS payment_status, sl.title AS title, o.company_name AS company_name
        FROM event_orders eo
        JOIN service_listings sl ON eo.listing_id = sl.id
        JOIN events ev ON ev.id = eo.event_id
        JOIN organizer_info o ON ev.org_id = o.org_id
        WHERE ev.customer_id = :customer_id
        ORDER BY eo.id DESC
    """
        ),
        {"customer_id": customer_id},
    )

    return {
        "events": [dict(row._mapping) for row in events_result.fetchall()],
        "orders": [dict(row._mapping) for row in orders_result.fetchall()],
    }


@router.get("/organizer/{org_id}/analytics")
def organizer_analytics(org_id: str, db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
        SELECT
          COUNT(*) FILTER (WHERE e.status::text = 'Completed')::int AS events_served,
          COALESCE(SUM(eo.final_total_price) FILTER (WHERE e.status::text = 'Completed'), 0) AS total_earnings,
          COUNT(*)::int AS total_bookings,
          COALESCE(SUM(eo.final_total_price), 0) AS gross_booking_value,
          COALESCE((
            SELECT ROUND(AVG(v.rating::numeric), 2)
            FROM vendor_reviews v WHERE v.vendor_id = :org_id
          ), 0) AS avg_rating
        FROM events e
        INNER JOIN event_orders eo ON eo.event_id = e.id
        WHERE e.org_id = :org_id
    """
        ),
        {"org_id": org_id},
    ).first()
    if row is None:
        ar = db.execute(
            text(
                """
            SELECT COALESCE(ROUND(AVG(rating::numeric), 2), 0) AS a
            FROM vendor_reviews WHERE vendor_id = :org_id
        """
            ),
            {"org_id": org_id},
        ).scalar()
        return {
            "events_served": 0,
            "total_earnings": 0,
            "total_bookings": 0,
            "gross_booking_value": 0,
            "avg_rating": float(ar or 0),
        }
    m = dict(row._mapping)
    for k in ("total_earnings", "gross_booking_value", "avg_rating"):
        if m.get(k) is not None:
            m[k] = float(m[k])
    return m


@router.get("/organizer/{org_id}/events")
def organizer_events(org_id: str, db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
        SELECT e.id AS id, e.event_date AS event_date, e.status AS status,
               e.customer_id AS customer_id, ci.full_name AS customer_name,
               eo.final_total_price AS order_total, eo.payment_status AS payment_status,
               sl.title AS service_title
        FROM events e
        LEFT JOIN customer_info ci ON ci.customer_id = e.customer_id
        LEFT JOIN event_orders eo ON eo.event_id = e.id
        LEFT JOIN service_listings sl ON sl.id = eo.listing_id
        WHERE e.org_id = :org_id
        ORDER BY e.event_date DESC
    """
        ),
        {"org_id": org_id},
    )
    rows = [dict(row._mapping) for row in result.fetchall()]
    for r in rows:
        if r.get("order_total") is not None:
            r["order_total"] = float(r["order_total"])
    return rows


# --- Customer ↔ organizer chat (same `chat_rooms` / `messages` tables as organizer UI) ---


class ChatSendBody(BaseModel):
    room_id: str
    text: str = Field(..., min_length=1, max_length=8000)


class ChatOpenBody(BaseModel):
    event_id: str


@router.get("/customer/chat/rooms")
def customer_chat_rooms(
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
):
    result = db.execute(
        text(
            """
            SELECT cr.id AS room_id, cr.org_id AS org_id, cr.event_id AS event_id,
                   o.company_name AS company_name
            FROM chat_rooms cr
            INNER JOIN organizer_info o ON o.org_id = cr.org_id
            WHERE cr.customer_id = :cid
            ORDER BY cr.id DESC
            """
        ),
        {"cid": customer_id},
    )
    return [dict(row._mapping) for row in result.fetchall()]


@router.post("/customer/chat/rooms/open")
def customer_chat_open_room(
    body: ChatOpenBody,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
):
    """Return existing chat room for this event or create one (customer must own the event)."""
    ev = db.execute(
        text(
            """
            SELECT id AS id, org_id AS org_id, customer_id AS customer_id
            FROM events
            WHERE id = :eid
            LIMIT 1
            """
        ),
        {"eid": body.event_id.strip()},
    ).first()
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")
    em = dict(ev._mapping)
    if em.get("customer_id") != customer_id:
        raise HTTPException(status_code=403, detail="Not your event")
    existing = db.execute(
        text(
            """
            SELECT id AS id
            FROM chat_rooms
            WHERE event_id = :eid AND customer_id = :cid
            LIMIT 1
            """
        ),
        {"eid": body.event_id.strip(), "cid": customer_id},
    ).first()
    if existing:
        return {"room_id": dict(existing._mapping)["id"]}
    rid = f"ROOM-{uuid.uuid4().hex[:6].upper()}"
    db.execute(
        text(
            """
            INSERT INTO chat_rooms (id, customer_id, org_id, event_id)
            VALUES (:id, :cid, :oid, :eid)
            """
        ),
        {
            "id": rid,
            "cid": customer_id,
            "oid": em["org_id"],
            "eid": body.event_id.strip(),
        },
    )
    db.commit()
    return {"room_id": rid}


@router.get("/customer/chat/rooms/{room_id}/messages")
def customer_chat_messages(
    room_id: str,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
):
    ok = db.execute(
        text(
            """
            SELECT 1 AS ok
            FROM chat_rooms
            WHERE id = :rid AND customer_id = :cid
            LIMIT 1
            """
        ),
        {"rid": room_id, "cid": customer_id},
    ).first()
    if ok is None:
        raise HTTPException(status_code=404, detail="Room not found")
    rows = db.execute(
        text(
            """
            SELECT m.id AS id, m.message_text AS message_text, m.sender_id AS sender_id,
                   m.timestamp AS timestamp
            FROM messages m
            WHERE m.room_id = :rid
            ORDER BY m.timestamp ASC NULLS LAST, m.id ASC
            """
        ),
        {"rid": room_id},
    ).fetchall()
    msg_list = []
    for row in rows:
        m = dict(row._mapping)
        msg_list.append(
            {
                "id": m.get("id"),
                "text": m.get("message_text"),
                "is_mine": m.get("sender_id") == customer_id,
                "time": _fmt_msg_time(m.get("timestamp")),
            }
        )
    return {"messages": msg_list}


@router.post("/customer/chat/messages")
def customer_chat_send(
    body: ChatSendBody,
    customer_id: str = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
):
    ok = db.execute(
        text(
            """
            SELECT 1 AS ok
            FROM chat_rooms
            WHERE id = :rid AND customer_id = :cid
            LIMIT 1
            """
        ),
        {"rid": body.room_id.strip(), "cid": customer_id},
    ).first()
    if ok is None:
        raise HTTPException(status_code=404, detail="Room not found")
    msg_id = f"MSG-{uuid.uuid4().hex[:8]}"
    db.execute(
        text(
            """
            INSERT INTO messages (id, room_id, sender_id, message_text)
            VALUES (:id, :room_id, :sender_id, :text)
            """
        ),
        {
            "id": msg_id,
            "room_id": body.room_id.strip(),
            "sender_id": customer_id,
            "text": body.text.strip(),
        },
    )
    db.commit()
    return {"status": "success", "msg_id": msg_id}
