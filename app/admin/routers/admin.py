from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.admin.schemas import AdminSetUserStatusIn
from app.database import get_db
from app.models import (
    Event,
    EventAddonSelection,
    EventOrder,
    OrganizerInfo,
    ServiceListing,
    UserMain,
    UserStatus,
)

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/admin/templates")


@router.get("/listings")
def listings(db: Session = Depends(get_db)):
    rows = (
        db.query(ServiceListing, OrganizerInfo.company_name)
        .outerjoin(OrganizerInfo, ServiceListing.org_id == OrganizerInfo.org_id)
        .order_by(ServiceListing.id)
        .all()
    )
    out = []
    for sl, company_name in rows:
        out.append(
            {
                "id": sl.id,
                "org_id": sl.org_id,
                "company_name": company_name,
                "category": sl.category,
                "title": sl.title,
                "base_price": float(sl.base_price),
                "is_deleted": bool(sl.is_deleted) if sl.is_deleted is not None else False,
            }
        )
    return out


@router.delete("/listings/{listing_id}")
def delete_listing(listing_id: str, db: Session = Depends(get_db)):
    listing = db.query(ServiceListing).filter(ServiceListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.is_deleted = True
    db.commit()
    return {"message": "Listing deleted"}


@router.get("/orders")
def orders(db: Session = Depends(get_db)):
    base_rows = (
        db.query(EventOrder)
        .options(
            joinedload(EventOrder.event).joinedload(Event.customer),
            joinedload(EventOrder.event).joinedload(Event.organizer),
            joinedload(EventOrder.listing),
            joinedload(EventOrder.selections).joinedload(EventAddonSelection.addon),
        )
        .order_by(EventOrder.id)
        .all()
    )

    out = []
    for eo in base_rows:
        ev = eo.event
        sl = eo.listing
        oi = ev.organizer if ev else None
        ci = ev.customer if ev else None
        addons = []
        for sel in eo.selections or []:
            ad = sel.addon
            addons.append(
                {
                    "addon_id": sel.addon_id,
                    "addon_name": ad.addon_name if ad else None,
                    "unit_price": float(sel.unit_price),
                }
            )
        addons_total = sum(a["unit_price"] for a in addons)
        base_price = float(eo.base_price_at_booking)
        out.append(
            {
                "order_id": eo.id,
                "event_id": eo.event_id,
                "listing_id": eo.listing_id,
                "listing_title": sl.title if sl else None,
                "org_id": ev.org_id if ev else None,
                "organizer_name": oi.company_name if oi else None,
                "customer_id": ev.customer_id if ev else None,
                "customer_name": ci.full_name if ci else None,
                "event_date": str(ev.event_date) if ev and ev.event_date else None,
                "event_status": ev.status if ev else None,
                "payment_status": eo.payment_status,
                "base_price_at_booking": base_price,
                "addons": addons,
                "addons_total": addons_total,
                "total_price_calculated": base_price + addons_total,
            }
        )
    return out


@router.get("/users")
def users(db: Session = Depends(get_db)):
    rows = (
        db.query(UserMain, UserStatus)
        .outerjoin(UserStatus, UserMain.id == UserStatus.user_id)
        .order_by(UserMain.id)
        .all()
    )
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "status": s.status if s else "Active",
        }
        for u, s in rows
    ]


@router.patch("/users/{user_id}/status")
def set_status(user_id: str, body: AdminSetUserStatusIn, db: Session = Depends(get_db)):
    user = db.query(UserMain).filter(UserMain.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    row = db.query(UserStatus).filter(UserStatus.user_id == user_id).first()
    if row:
        row.status = body.status
        row.reason = body.reason
    else:
        db.add(UserStatus(user_id=user_id, status=body.status, reason=body.reason))
    db.commit()
    return {"message": "User status updated"}


@router.get("/ui", response_class=HTMLResponse)
def admin_ui(request: Request, db: Session = Depends(get_db)):
    listings = (
        db.query(ServiceListing, OrganizerInfo.company_name)
        .outerjoin(OrganizerInfo, ServiceListing.org_id == OrganizerInfo.org_id)
        .order_by(ServiceListing.id)
        .all()
    )

    orders = (
        db.query(EventOrder)
        .options(
            joinedload(EventOrder.event).joinedload(Event.customer),
            joinedload(EventOrder.event).joinedload(Event.organizer),
            joinedload(EventOrder.listing),
            joinedload(EventOrder.selections).joinedload(EventAddonSelection.addon),
        )
        .order_by(EventOrder.id)
        .all()
    )

    users = (
        db.query(UserMain, UserStatus)
        .outerjoin(UserStatus, UserMain.id == UserStatus.user_id)
        .order_by(UserMain.id)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "admin/admin.html",
        {"listings": listings, "orders": orders, "users": users},
    )


@router.post("/ui/listings/{listing_id}/delete")
def admin_ui_delete_listing(listing_id: str, db: Session = Depends(get_db)):
    listing = db.query(ServiceListing).filter(ServiceListing.id == listing_id).first()
    if listing:
        listing.is_deleted = True
        db.commit()
    return RedirectResponse(url="/admin/ui", status_code=303)


@router.post("/ui/users/{user_id}/status")
def admin_ui_set_user_status(
    user_id: str,
    status: str = Form(...),
    reason: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    user = db.query(UserMain).filter(UserMain.id == user_id).first()
    if user:
        row = db.query(UserStatus).filter(UserStatus.user_id == user_id).first()
        if row:
            row.status = status
            row.reason = reason
        else:
            db.add(UserStatus(user_id=user_id, status=status, reason=reason))
        db.commit()
    return RedirectResponse(url="/admin/ui", status_code=303)
