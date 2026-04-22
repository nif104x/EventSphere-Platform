import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple

from app.customer.database import get_db
from app.organizer import ouath2

router = APIRouter(prefix="/api", tags=["api"])

_bearer = HTTPBearer(auto_error=False)

# Same .env locations as app/main.py so STRIPE_SECRET_KEY is visible to this module
_APP_DIR = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _APP_DIR.parent


def _refresh_payment_env() -> None:
    """Reload env files (uvicorn cwd may differ from where .env lives)."""
    load_dotenv(_PROJECT_ROOT / ".env", override=False)
    load_dotenv(_APP_DIR / ".env", override=True)


def _normalize_stripe_secret_key() -> str:
    """Read secret from env; strip quotes and all whitespace (fixes spaces after '=' or in pasted value)."""
    _refresh_payment_env()
    key = (os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY_TEST") or "").strip()
    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
        key = key[1:-1].strip()
    key = "".join(key.split())
    return key


def _stripe_secret_key_format_error(key: str) -> Optional[str]:
    """Detect common mistake: putting test card 4242… in .env instead of the API Secret key."""
    if not key:
        return None
    if not key.startswith(("sk_test_", "sk_live_")):
        return (
            "STRIPE_SECRET_KEY must start with sk_test_ or sk_live_. "
            "Copy the Secret key from Stripe Dashboard → Developers → API keys."
        )
    # Real Stripe secrets are long (~100+ chars). Card-shaped values are much shorter.
    if len(key) < 80:
        return (
            "STRIPE_SECRET_KEY is not a valid Stripe secret (too short). "
            "In https://dashboard.stripe.com/test/apikeys reveal and copy the full Secret key (sk_test_…). "
            "Do not put 4242 4242 4242 4242 in .env — that is a test card number you type only on the Stripe checkout page."
        )
    return None


def _require_stripe_secret_key() -> str:
    key = _normalize_stripe_secret_key()
    if not key:
        raise HTTPException(
            status_code=503,
            detail="Add STRIPE_SECRET_KEY to app/.env (your Stripe Secret key) and restart the API.",
        )
    fmt = _stripe_secret_key_format_error(key)
    if fmt:
        raise HTTPException(status_code=503, detail=fmt)
    return key


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
    cid = dict(row._mapping)["customer_id"]
    return str(cid).strip()


def _norm_uid(val: Optional[str]) -> str:
    return str(val or "").strip().casefold()


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
    """customer_id is optional; when sent it must match the JWT (legacy clients)."""
    customer_id: Optional[str] = None
    org_id: str
    event_date: str  # YYYY-MM-DD


class OrderCreate(BaseModel):
    event_id: str
    listing_id: str
    base_price: float
    addons_cost: float = 0.0
    total_price: float


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
        expires_delta=timedelta(minutes=ouath2.CUSTOMER_ACCESS_TOKEN_EXPIRE_MINUTES),
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
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    authed_customer_id: str = Depends(get_current_customer_id),
):
    """Creates a row in shared Postgres `events` (same DB/URL as organizer). Organizers list it by `org_id`."""
    body_cid = (event.customer_id or "").strip()
    if body_cid and _norm_uid(body_cid) != _norm_uid(authed_customer_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="customer_id must match the signed-in customer",
        )
    event_id = _next_seq(db, "events", "id", "EVT")
    try:
        db.execute(
            text(
                """
            INSERT INTO events (id, customer_id, org_id, event_date, status)
            VALUES (:id, :customer_id, :org_id, :event_date, 'Pending')
        """
            ),
            {
                "id": event_id,
                "customer_id": authed_customer_id,
                "org_id": event.org_id,
                "event_date": event.event_date,
            },
        )
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not create the event. Check that the organizer and date are valid "
                "and your account is linked in the database."
            ),
        ) from e
    return {"event_id": event_id}


@router.post("/orders")
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    authed_customer_id: str = Depends(get_current_customer_id),
):
    """Order is tied to `events.id`; organizer dashboards read the same `event_orders` rows."""
    owner = db.execute(
        text("SELECT customer_id FROM events WHERE id = :eid LIMIT 1"),
        {"eid": order.event_id},
    ).first()
    if owner is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if _norm_uid(dict(owner._mapping).get("customer_id")) != _norm_uid(authed_customer_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot attach an order to another customer's event",
        )
    order_id = _next_seq(db, "event_orders", "id", "ORD")
    try:
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
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not create the order. The selected service may not exist for this organizer, "
                "or the event reference is invalid."
            ),
        ) from e
    return {"order_id": order_id}


def _payment_redirect_allowed(url: str) -> bool:
    u = (url or "").strip()
    if not u.startswith(("http://", "https://")):
        return False
    raw = os.getenv(
        "PAYMENT_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    bases = [x.strip().rstrip("/") for x in raw.split(",") if x.strip()]
    try:
        origin = f"{urlparse(u).scheme}://{urlparse(u).netloc}".rstrip("/")
    except Exception:
        return False
    for b in bases:
        br = b.rstrip("/")
        if origin == br or u.startswith(br + "/") or u.startswith(br + "?"):
            return True
    return False


def _orders_owned_by_customer(db: Session, customer_id: str, order_ids: List[str]) -> List[dict]:
    ids = sorted({str(x).strip() for x in order_ids if str(x).strip()})
    if not ids:
        raise HTTPException(status_code=400, detail="order_ids required")
    ph = ", ".join(f":id{i}" for i in range(len(ids)))
    params: dict = {f"id{i}": ids[i] for i in range(len(ids))}
    rows = db.execute(
        text(
            f"""
            SELECT eo.id AS id, eo.final_total_price AS final_total_price,
                   eo.payment_status::text AS payment_status, ev.customer_id AS customer_id
            FROM event_orders eo
            JOIN events ev ON ev.id = eo.event_id
            WHERE eo.id IN ({ph})
            """
        ),
        params,
    ).fetchall()
    if len(rows) != len(ids):
        raise HTTPException(status_code=404, detail="One or more orders were not found")
    out: List[dict] = []
    for r in rows:
        m = dict(r._mapping)
        if _norm_uid(m.get("customer_id")) != _norm_uid(customer_id):
            raise HTTPException(
                status_code=403,
                detail="This order is not linked to your account.",
            )
        out.append(m)
    return out


def _assert_customer_orders_unpaid(
    db: Session, customer_id: str, order_ids: List[str]
) -> Tuple[List[dict], float]:
    out = _orders_owned_by_customer(db, customer_id, order_ids)
    total = 0.0
    for m in out:
        st = (m.get("payment_status") or "").strip().lower()
        if st == "paid":
            raise HTTPException(status_code=400, detail=f"Order {m['id']} is already paid")
        total += float(m.get("final_total_price") or 0)
    return out, total


def _mark_orders_paid(db: Session, order_ids: List[str]) -> int:
    ids = [str(x).strip() for x in order_ids if str(x).strip()]
    if not ids:
        return 0
    ph = ", ".join(f":p{i}" for i in range(len(ids)))
    params = {f"p{i}": ids[i] for i in range(len(ids))}
    # Use plain 'Paid' so Postgres can assign to either enum or varchar column (no ::payment_status cast).
    r = db.execute(
        text(
            f"""
            UPDATE event_orders
            SET payment_status = 'Paid'
            WHERE id IN ({ph})
              AND COALESCE(payment_status::text, '') NOT ILIKE 'paid'
            """
        ),
        params,
    )
    db.commit()
    rc = getattr(r, "rowcount", None)
    return int(rc) if rc is not None and rc >= 0 else 0


def _coerce_stripe_metadata_value(v) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    return str(v).strip()


def _stripe_object_metadata_to_dict(md) -> dict:
    """Normalize Stripe SDK metadata (dict or StripeObject) to plain str -> str."""
    if md is None:
        return {}
    if isinstance(md, dict):
        raw = md
    else:
        to_dict = getattr(md, "to_dict", None)
        if callable(to_dict):
            try:
                raw = to_dict()
            except Exception:
                raw = {}
        else:
            try:
                raw = dict(md)
            except Exception:
                raw = {}
    out: dict = {}
    for k, v in (raw or {}).items():
        if v is None:
            continue
        out[str(k)] = _coerce_stripe_metadata_value(v)
    return out


def _stripe_metadata_dict(session) -> dict:
    """Session metadata plus PaymentIntent metadata when expanded (Stripe may surface either)."""
    combined: dict = {}
    combined.update(_stripe_object_metadata_to_dict(getattr(session, "metadata", None)))
    pi = getattr(session, "payment_intent", None)
    if pi is not None and not isinstance(pi, str):
        combined.update(_stripe_object_metadata_to_dict(getattr(pi, "metadata", None)))
    return combined


def _meta_ci_get(meta: dict, key: str) -> str:
    lk = key.casefold()
    for k, v in meta.items():
        if str(k).casefold() == lk:
            return _coerce_stripe_metadata_value(v)
    return ""


def _parse_ids_from_event_sphere_json(data: dict) -> List[str]:
    """Read ids from compact checkout JSON; tolerate string / CSV / alternate keys."""
    raw = data.get("ids")
    raw_list: list = []
    if isinstance(raw, str):
        s = raw.strip()
        if s.startswith("["):
            try:
                parsed = json.loads(s)
                raw_list = parsed if isinstance(parsed, list) else []
            except Exception:
                raw_list = [x.strip() for x in s.split(",") if x.strip()]
        elif s:
            raw_list = [x.strip() for x in s.split(",") if x.strip()]
    elif isinstance(raw, list):
        raw_list = raw
    out = [str(x).strip() for x in raw_list if str(x).strip()]
    if out:
        return out
    alt = data.get("order_ids")
    if isinstance(alt, str):
        return [x.strip() for x in alt.split(",") if x.strip()]
    if isinstance(alt, list):
        return [str(x).strip() for x in alt if str(x).strip()]
    return []


def _checkout_session_is_paid(session) -> bool:
    """Stripe SDK may return strings or enums; Checkout success is paid and/or status complete."""
    ps = getattr(session, "payment_status", None)
    ps_s = (
        ps
        if isinstance(ps, str)
        else (getattr(ps, "value", None) or getattr(ps, "name", None) or str(ps or ""))
    )
    if str(ps_s).lower() == "paid":
        return True
    st = getattr(session, "status", None)
    st_s = (
        st
        if isinstance(st, str)
        else (getattr(st, "value", None) or getattr(st, "name", None) or str(st or ""))
    )
    return str(st_s).lower() == "complete"


def _order_ids_from_checkout_metadata(
    session, customer_id: str, db: Session
) -> List[str]:
    """Read order ids from Stripe session metadata; confirm orders belong to this customer (DB is source of truth)."""
    meta = _stripe_metadata_dict(session)
    blob = _meta_ci_get(meta, "event_sphere_pay")
    ids: List[str] = []
    if blob:
        try:
            parsed = json.loads(blob)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Could not read payment session payload: {e!s}",
            ) from e
        if not isinstance(parsed, dict):
            parsed = {}
        ids = _parse_ids_from_event_sphere_json(parsed)

    if not ids:
        csv = _meta_ci_get(meta, "order_ids")
        ids = [x.strip() for x in csv.split(",") if x.strip()]

    if not ids:
        raise HTTPException(
            status_code=400,
            detail=(
                "Payment session is missing order references. "
                "If this payment was started before the latest app update, start a new checkout from Book."
            ),
        )

    try:
        _orders_owned_by_customer(db, customer_id, ids)
    except HTTPException as e:
        if e.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Sign in as the same customer who started checkout, then open this payment link again."
                ),
            ) from e
        raise
    return ids


class PaymentCheckoutBody(BaseModel):
    order_ids: List[str] = Field(..., min_length=1)
    success_url: str = Field(..., min_length=8)
    cancel_url: str = Field(..., min_length=8)


class PaymentSessionBody(BaseModel):
    session_id: str = Field(..., min_length=8)


@router.post("/payment/stripe-checkout")
def create_stripe_checkout_session(
    body: PaymentCheckoutBody,
    db: Session = Depends(get_db),
    customer_id: str = Depends(get_current_customer_id),
):
    """Creates a Stripe Checkout Session (requires STRIPE_SECRET_KEY in app/.env or project .env)."""
    if not _payment_redirect_allowed(body.success_url) or not _payment_redirect_allowed(body.cancel_url):
        raise HTTPException(
            status_code=400,
            detail="success_url and cancel_url must start with an origin listed in PAYMENT_ALLOWED_ORIGINS",
        )
    if "{CHECKOUT_SESSION_ID}" not in body.success_url:
        raise HTTPException(
            status_code=400,
            detail="success_url must include the literal {CHECKOUT_SESSION_ID} for Stripe Checkout",
        )
    orders, total = _assert_customer_orders_unpaid(db, customer_id, body.order_ids)
    key = _require_stripe_secret_key()
    try:
        import stripe
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Stripe SDK not installed. Run: pip install stripe",
        )
    stripe.api_key = key
    amount_cents = max(int(round(total * 100)), 50)
    cid = str(customer_id).strip()
    id_list = [str(o["id"]) for o in orders]
    pay_meta = json.dumps({"c": cid, "ids": id_list})
    if len(pay_meta) > 500:
        raise HTTPException(
            status_code=400,
            detail="Too many orders for one Stripe payment (metadata limit). Pay in smaller groups.",
        )
    # Redundant CSV survives if JSON blob is unreadable in Stripe responses (each metadata value ≤500 chars).
    order_ids_csv = ",".join(id_list)
    if len(order_ids_csv) > 500:
        raise HTTPException(
            status_code=400,
            detail="Too many orders for one Stripe payment (metadata limit). Pay in smaller groups.",
        )
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": f"EventSphere booking ({len(orders)} order(s))",
                        },
                    },
                    "quantity": 1,
                }
            ],
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            metadata={
                "event_sphere_pay": pay_meta,
                "customer_id": cid,
                "order_ids": order_ids_csv,
            },
        )
    except Exception as e:
        msg = str(e)
        if "Invalid API Key" in msg or "No API key provided" in msg:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Stripe rejected the secret key. Use the Secret key from "
                    "https://dashboard.stripe.com/test/apikeys (long sk_test_…), not the 4242 card number."
                ),
            ) from e
        raise HTTPException(status_code=502, detail=f"Stripe error: {msg}") from e
    return {
        "url": session.url,
        "session_id": session.id,
        "order_count": len(orders),
        "total": round(total, 2),
    }


@router.post("/payment/complete-session")
def complete_stripe_checkout_session(
    body: PaymentSessionBody,
    db: Session = Depends(get_db),
    customer_id: str = Depends(get_current_customer_id),
):
    """After Stripe redirects back with session_id, mark linked orders Paid."""
    try:
        key = _require_stripe_secret_key()
        try:
            import stripe
        except ImportError:
            raise HTTPException(status_code=500, detail="Stripe SDK not installed")
        stripe.api_key = key
        try:
            session = stripe.checkout.Session.retrieve(
                body.session_id,
                expand=["payment_intent"],
            )
        except Exception as e:
            msg = str(e)
            if "Invalid API Key" in msg:
                raise HTTPException(
                    status_code=502,
                    detail="Stripe rejected the secret key. Update STRIPE_SECRET_KEY in app/.env with your Dashboard Secret key.",
                ) from e
            raise HTTPException(status_code=400, detail=f"Invalid session: {msg}") from e

        if not _checkout_session_is_paid(session):
            ps = getattr(session, "payment_status", None)
            st = getattr(session, "status", None)
            raise HTTPException(
                status_code=400,
                detail=f"Checkout is not paid yet (payment_status={ps!r}, status={st!r}).",
            )

        order_ids = _order_ids_from_checkout_metadata(session, customer_id, db)
        if not order_ids:
            raise HTTPException(status_code=400, detail="Session is missing order data")

        rows = _orders_owned_by_customer(db, customer_id, order_ids)
        if all((str(r.get("payment_status") or "").strip().lower() == "paid") for r in rows):
            return {"ok": True, "updated": 0, "order_ids": order_ids, "already_completed": True}
        _assert_customer_orders_unpaid(db, customer_id, order_ids)
        updated = _mark_orders_paid(db, order_ids)
        return {"ok": True, "updated": updated, "order_ids": order_ids}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not finalize payment: {e!s}",
        ) from e


@router.patch("/events/{event_id}/complete")
def mark_event_complete(
    event_id: str,
    db: Session = Depends(get_db),
    customer_id: str = Depends(get_current_customer_id),
):
    """Customer marks their own event completed (Confirmed → Completed) so they can rate."""
    eid = (event_id or "").strip()
    cid = (customer_id or "").strip()
    if not eid:
        raise HTTPException(status_code=400, detail="event_id is required")
    check = db.execute(
        text(
            """
        SELECT status::text AS status FROM events
        WHERE id = :event_id AND customer_id = :cid
        LIMIT 1
        """
        ),
        {"event_id": eid, "cid": cid},
    ).first()
    if check is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found for this account (check you are signed in as the booking owner)",
        )
    st = (dict(check._mapping).get("status") or "").strip()
    if st.casefold() != "confirmed":
        raise HTTPException(
            status_code=400,
            detail=f"Only confirmed events can be marked complete (current status: {st})",
        )
    r = db.execute(
        text(
            """
        UPDATE events SET status = 'Completed'::event_status
        WHERE id = :event_id AND customer_id = :cid
              AND LOWER(TRIM(BOTH FROM status::text)) = 'confirmed'
        RETURNING id
        """
        ),
        {"event_id": eid, "cid": cid},
    )
    if r.first() is None:
        raise HTTPException(
            status_code=409,
            detail="Event status changed; refresh the page and try again",
        )
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
def get_dashboard(
    customer_id: str,
    db: Session = Depends(get_db),
    authed_customer_id: str = Depends(get_current_customer_id),
):
    """Bearer must match URL customer_id (same rule as mark-complete and ratings)."""
    if (customer_id or "").strip() != (authed_customer_id or "").strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot load another customer's dashboard",
        )
    events_result = db.execute(
        text(
            """
        SELECT e.id AS id, e.event_date AS event_date, e.status AS status,
               o.company_name AS company_name, e.org_id AS org_id,
               (SELECT vr.rating FROM vendor_reviews vr WHERE vr.event_id = e.id LIMIT 1) AS my_rating,
               CASE
                 WHEN LOWER(TRIM(BOTH FROM e.status::text)) = 'confirmed' THEN true
                 ELSE false
               END AS can_mark_complete,
               CASE
                 WHEN LOWER(TRIM(BOTH FROM e.status::text)) = 'completed'
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


@router.get("/customer/{customer_id}/event-history")
def get_event_history(
    customer_id: str,
    db: Session = Depends(get_db),
    authed_customer_id: str = Depends(get_current_customer_id),
):
    """Past events with vendor info and ratings (Bearer must match customer_id)."""
    if customer_id != authed_customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view another customer's history",
        )
    result = db.execute(
        text(
            """
        SELECT e.id AS id, e.event_date AS event_date, e.status::text AS status,
               e.org_id AS org_id, o.company_name AS company_name,
               vr.rating AS rating, vr.comment AS review_comment, vr.id AS review_id,
               CASE
                 WHEN LOWER(TRIM(BOTH FROM e.status::text)) = 'confirmed' THEN true
                 ELSE false
               END AS can_mark_complete,
               CASE
                 WHEN LOWER(TRIM(BOTH FROM e.status::text)) = 'completed'
                      AND NOT EXISTS (SELECT 1 FROM vendor_reviews r2 WHERE r2.event_id = e.id)
                 THEN true
                 ELSE false
               END AS can_rate,
               (
                 SELECT sl.title
                 FROM event_orders eo
                 JOIN service_listings sl ON sl.id = eo.listing_id
                 WHERE eo.event_id = e.id
                 ORDER BY eo.id DESC
                 LIMIT 1
               ) AS service_title
        FROM events e
        JOIN organizer_info o ON e.org_id = o.org_id
        LEFT JOIN vendor_reviews vr ON vr.event_id = e.id
        WHERE e.customer_id = :customer_id
        ORDER BY e.event_date DESC NULLS LAST, e.id DESC
        """
        ),
        {"customer_id": customer_id},
    )
    rows = []
    for row in result.fetchall():
        m = dict(row._mapping)
        if m.get("rating") is not None:
            m["rating"] = int(m["rating"])
        rows.append(m)
    return {"events": rows}


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
