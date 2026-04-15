from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Optional
from .database import get_db

router = APIRouter(prefix="/api", tags=["api"])


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
        text(
            """
        SELECT 1 FROM vendor_reviews WHERE event_id = :event_id AND customer_id = :cid
    """
        ),
        {"event_id": event_id, "cid": body.customer_id},
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Already rated this event")

    rev_id = _next_seq(db, "vendor_reviews", "id", "REV")
    try:
        db.execute(
            text(
                """
            INSERT INTO vendor_reviews (id, event_id, vendor_id, customer_id, rating, comment)
            VALUES (:id, :event_id, :vendor_id, :customer_id, :rating, :comment)
        """
            ),
            {
                "id": rev_id,
                "event_id": event_id,
                "vendor_id": m["org_id"],
                "customer_id": body.customer_id,
                "rating": body.rating,
                "comment": body.comment,
            },
        )
        db.commit()
    except Exception as e:
        db.rollback()
        err = str(e.orig) if hasattr(e, "orig") else str(e)
        if "customer_id" in err or "column" in err.lower():
            raise HTTPException(
                status_code=500,
                detail="Database missing customer_id on vendor_reviews; run Database/migrations/001_vendor_reviews_customer_id.sql",
            )
        raise HTTPException(status_code=500, detail="Could not save rating")

    return {"review_id": rev_id}


@router.get("/customer/{customer_id}/dashboard")
def get_dashboard(customer_id: str, db: Session = Depends(get_db)):
    events_result = db.execute(
        text(
            """
        SELECT e.id AS id, e.event_date AS event_date, e.status AS status,
               o.company_name AS company_name, e.org_id AS org_id,
               vr.rating AS my_rating,
               CASE
                 WHEN e.status::text = 'Completed' AND vr.id IS NULL THEN true
                 ELSE false
               END AS can_rate
        FROM events e
        JOIN organizer_info o ON e.org_id = o.org_id
        LEFT JOIN vendor_reviews vr ON vr.event_id = e.id AND vr.customer_id = :customer_id
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
          COALESCE(SUM(eo.final_total_price), 0) AS gross_booking_value
        FROM events e
        INNER JOIN event_orders eo ON eo.event_id = e.id
        WHERE e.org_id = :org_id
    """
        ),
        {"org_id": org_id},
    ).first()
    if row is None:
        return {
            "events_served": 0,
            "total_earnings": 0,
            "total_bookings": 0,
            "gross_booking_value": 0,
        }
    m = dict(row._mapping)
    for k in ("total_earnings", "gross_booking_value"):
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
               eo.final_total_price AS order_total, eo.payment_status AS payment_status
        FROM events e
        LEFT JOIN customer_info ci ON ci.customer_id = e.customer_id
        LEFT JOIN event_orders eo ON eo.event_id = e.id
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
