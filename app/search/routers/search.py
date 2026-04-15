from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db


router = APIRouter(tags=["search"])


@router.get("/search")
def search(
    query: str | None = Query(default=None),
    category: str | None = Query(default=None),
    min_price: float | None = Query(default=None),
    max_price: float | None = Query(default=None),
    db: Session = Depends(get_db),
):
    db.execute(
        text(
            "ALTER TABLE service_listings ADD COLUMN IF NOT EXISTS is_deleted boolean DEFAULT false"
        )
    )
    db.commit()

    where = ["COALESCE(sl.is_deleted, false) = false"]
    params = {}

    if query:
        where.append(
            "(sl.title ILIKE :q OR oi.company_name ILIKE :q OR sl.category ILIKE :q)"
        )
        params["q"] = f"%{query}%"

    if category:
        where.append("sl.category = :cat")
        params["cat"] = category

    if min_price is not None:
        where.append("sl.base_price >= :minp")
        params["minp"] = min_price

    if max_price is not None:
        where.append("sl.base_price <= :maxp")
        params["maxp"] = max_price

    where_sql = " AND ".join(where)

    rows = db.execute(
        text(
            f"""
            SELECT
              sl.id, sl.org_id, oi.company_name, sl.category, sl.title, sl.base_price,
              (
                SELECT li.image_url
                FROM listing_images li
                WHERE li.listing_id = sl.id
                ORDER BY li.id
                LIMIT 1
              ) AS image_url
            FROM service_listings sl
            LEFT JOIN organizer_info oi ON oi.org_id = sl.org_id
            WHERE {where_sql}
            ORDER BY sl.base_price ASC
            """
        ),
        params,
    ).mappings().all()

    out = []
    for r in rows:
        addons = db.execute(
            text(
                """
                SELECT id, addon_name, price
                FROM service_addons
                WHERE listing_id = :lid
                ORDER BY id
                """
            ),
            {"lid": r["id"]},
        ).mappings().all()
        d = dict(r)
        d["addons"] = [dict(a) for a in addons]
        out.append(d)
    return out

