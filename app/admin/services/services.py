from app.db import get_conn


def _ensure_service_listings_soft_delete_column():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            ALTER TABLE service_listings
            ADD COLUMN IF NOT EXISTS is_deleted boolean DEFAULT false;
            """
        )
        conn.commit()
    finally:
        conn.close()


def list_listings_for_admin():
    _ensure_service_listings_soft_delete_column()
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT sl.id, sl.org_id, oi.company_name, sl.category, sl.title, sl.base_price, sl.is_deleted
            FROM service_listings sl
            LEFT JOIN organizer_info oi ON oi.org_id = sl.org_id
            ORDER BY sl.id;
            """
        )
        return cur.fetchall()
    finally:
        conn.close()


def delete_listing_soft(listing_id: str) -> bool:
    _ensure_service_listings_soft_delete_column()
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE service_listings
            SET is_deleted = true
            WHERE id = %s;
            """,
            (listing_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_orders_for_admin():
    conn = get_conn()
    try:
        cur = conn.cursor()

        cur.execute(
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
            ORDER BY eo.id;
            """
        )
        orders = cur.fetchall()

        # attach addons + calculate totals
        for o in orders:
            cur.execute(
                """
                SELECT sel.addon_id, sa.addon_name, sel.unit_price
                FROM event_addon_selections sel
                LEFT JOIN service_addons sa ON sa.id = sel.addon_id
                WHERE sel.order_id = %s
                ORDER BY sel.id;
                """,
                (o["order_id"],),
            )
            addons = cur.fetchall()
            addons_total = (
                float(sum([a["unit_price"] for a in addons])) if addons else 0.0
            )
            base = float(o["base_price_at_booking"])
            o["addons"] = addons
            o["addons_total"] = addons_total
            o["total_price_calculated"] = base + addons_total
            if o.get("event_date") is not None:
                o["event_date"] = str(o["event_date"])

        return orders
    finally:
        conn.close()


def get_users_for_admin():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
              um.id,
              um.username,
              um.role,
              COALESCE(us.status, 'Active') AS status
            FROM user_main um
            LEFT JOIN user_status us ON us.user_id = um.id
            ORDER BY um.id;
            """
        )
        return cur.fetchall()
    finally:
        conn.close()


def ban_or_unban_user(user_id: str, status: str, reason: str | None) -> bool:
    conn = get_conn()
    try:
        cur = conn.cursor()

        cur.execute("SELECT id FROM user_main WHERE id = %s;", (user_id,))
        exists = cur.fetchone()
        if not exists:
            return False

        cur.execute(
            """
            INSERT INTO user_status (user_id, status, reason)
            VALUES (%s, %s::account_status, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET status = EXCLUDED.status, reason = EXCLUDED.reason, updated_at = CURRENT_TIMESTAMP;
            """,
            (user_id, status, reason),
        )
        conn.commit()
        return True
    finally:
        conn.close()
