from app.admin.services.services import _ensure_service_listings_soft_delete_column
from app.db import get_conn


def search_listings(
    query: str | None,
    category: str | None,
    min_price: float | None,
    max_price: float | None,
):
    _ensure_service_listings_soft_delete_column()

    where = ["COALESCE(sl.is_deleted, false) = false"]
    params: list[object] = []

    if query:
        where.append("(sl.title ILIKE %s OR oi.company_name ILIKE %s OR sl.category ILIKE %s)")
        q = f"%{query}%"
        params.extend([q, q, q])

    if category:
        where.append("sl.category = %s")
        params.append(category)

    if min_price is not None:
        where.append("sl.base_price >= %s")
        params.append(min_price)

    if max_price is not None:
        where.append("sl.base_price <= %s")
        params.append(max_price)

    where_sql = " AND ".join(where) if where else "TRUE"

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
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
            ORDER BY sl.base_price ASC;
            """,
            tuple(params),
        )
        listings = cur.fetchall()

        # Attach addons for display
        for l in listings:
            cur.execute(
                """
                SELECT id, addon_name, price
                FROM service_addons
                WHERE listing_id = %s
                ORDER BY id;
                """,
                (l["id"],),
            )
            l["addons"] = cur.fetchall()

        return listings
    finally:
        conn.close()

