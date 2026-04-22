from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models import Event, EventAddonSelection, EventOrder


def get_orders_report_rows(
    db: Session,
    from_date: date | None = None,
    to_date: date | None = None,
    payment_status: str | None = None,
):
    q = (
        db.query(EventOrder)
        .options(
            joinedload(EventOrder.event).joinedload(Event.customer),
            joinedload(EventOrder.event).joinedload(Event.organizer),
            joinedload(EventOrder.listing),
            joinedload(EventOrder.selections).joinedload(EventAddonSelection.addon),
        )
        .order_by(EventOrder.id)
    )

    if payment_status:
        q = q.filter(EventOrder.payment_status == payment_status)

    if from_date is not None:
        q = q.join(Event, Event.id == EventOrder.event_id).filter(Event.event_date >= from_date)

    if to_date is not None:
        q = q.join(Event, Event.id == EventOrder.event_id).filter(Event.event_date <= to_date)

    orders = q.all()

    out = []
    for eo in orders:
        ev = eo.event
        sl = eo.listing
        oi = ev.organizer if ev else None
        ci = ev.customer if ev else None

        addons_total = 0.0
        for sel in eo.selections or []:
            addons_total += float(sel.unit_price)

        base_price = float(eo.base_price_at_booking)
        out.append(
            {
                "order_id": eo.id,
                "event_id": eo.event_id,
                "event_date": ev.event_date.isoformat() if ev and ev.event_date else "",
                "event_status": ev.status if ev else "",
                "customer_id": ev.customer_id if ev else "",
                "customer_name": ci.full_name if ci else "",
                "customer_email": ci.email if ci else "",
                "organizer_id": ev.org_id if ev else "",
                "organizer_name": oi.company_name if oi else "",
                "listing_id": eo.listing_id,
                "listing_title": sl.title if sl else "",
                "payment_status": eo.payment_status or "",
                "base_price": base_price,
                "addons_total": addons_total,
                "total_calculated": base_price + addons_total,
            }
        )

    return out

