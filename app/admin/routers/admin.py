from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.admin.schemas import AdminSetUserStatusIn


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/listings")
def listings(db: Session = Depends(get_db)):
    db.execute(
        text(
            "ALTER TABLE service_listings ADD COLUMN IF NOT EXISTS is_deleted boolean DEFAULT false"
        )
    )
    db.commit()
    rows = db.execute(
        text(
            """
            SELECT sl.id, sl.org_id, oi.company_name, sl.category, sl.title, sl.base_price,
                   COALESCE(sl.is_deleted, false) AS is_deleted
            FROM service_listings sl
            LEFT JOIN organizer_info oi ON oi.org_id = sl.org_id
            ORDER BY sl.id
            """
        )
    ).mappings().all()
    return [dict(r) for r in rows]


@router.delete("/listings/{listing_id}")
def delete_listing(listing_id: str, db: Session = Depends(get_db)):
    db.execute(
        text(
            "ALTER TABLE service_listings ADD COLUMN IF NOT EXISTS is_deleted boolean DEFAULT false"
        )
    )
    db.commit()
    res = db.execute(
        text("UPDATE service_listings SET is_deleted = true WHERE id = :id"),
        {"id": listing_id},
    )
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"message": "Listing deleted"}


@router.get("/orders")
def orders(db: Session = Depends(get_db)):
    base_rows = db.execute(
        text(
            """
            SELECT
              eo.id AS order_id,
              eo.event_id,
              eo.listing_id,
              sl.title AS listing_title,
              e.org_id,
              oi.company_name AS organizer_name,
              e.customer_id,
              ci.full_name AS customer_name,
              e.event_date,
              e.status AS event_status,
              eo.payment_status,
              eo.base_price_at_booking
            FROM event_orders eo
            LEFT JOIN events e ON e.id = eo.event_id
            LEFT JOIN service_listings sl ON sl.id = eo.listing_id
            LEFT JOIN organizer_info oi ON oi.org_id = e.org_id
            LEFT JOIN customer_info ci ON ci.customer_id = e.customer_id
            ORDER BY eo.id
            """
        )
    ).mappings().all()

    out = []
    for r in base_rows:
        addons = db.execute(
            text(
                """
                SELECT sel.addon_id, sa.addon_name, sel.unit_price
                FROM event_addon_selections sel
                LEFT JOIN service_addons sa ON sa.id = sel.addon_id
                WHERE sel.order_id = :oid
                ORDER BY sel.id
                """
            ),
            {"oid": r["order_id"]},
        ).mappings().all()
        addons_total = sum([float(a["unit_price"]) for a in addons]) if addons else 0.0
        base_price = float(r["base_price_at_booking"])
        d = dict(r)
        d["event_date"] = str(d["event_date"]) if d.get("event_date") else None
        d["addons"] = [dict(a) for a in addons]
        d["addons_total"] = addons_total
        d["total_price_calculated"] = base_price + addons_total
        out.append(d)
    return out


@router.get("/users")
def users(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT um.id, um.username, um.role, COALESCE(us.status, 'Active') AS status
            FROM user_main um
            LEFT JOIN user_status us ON us.user_id = um.id
            ORDER BY um.id
            """
        )
    ).mappings().all()
    return [dict(r) for r in rows]


@router.patch("/users/{user_id}/status")
def set_status(user_id: str, body: AdminSetUserStatusIn, db: Session = Depends(get_db)):
    exists = db.execute(
        text("SELECT id FROM user_main WHERE id = :id"), {"id": user_id}
    ).first()
    if not exists:
        raise HTTPException(status_code=404, detail="User not found")

    db.execute(
        text(
            """
            INSERT INTO user_status (user_id, status, reason)
            VALUES (:uid, :st::account_status, :rs)
            ON CONFLICT (user_id)
            DO UPDATE SET status = EXCLUDED.status, reason = EXCLUDED.reason, updated_at = CURRENT_TIMESTAMP
            """
        ),
        {"uid": user_id, "st": body.status, "rs": body.reason},
    )
    db.commit()
    return {"message": "User status updated"}

