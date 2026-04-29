from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ListingImage, OrganizerInfo, ServiceAddon, ServiceListing

router = APIRouter(tags=["search"])
templates = Jinja2Templates(directory="app/search/templates")


def _not_deleted():
    return or_(ServiceListing.is_deleted.is_(False), ServiceListing.is_deleted.is_(None))


def _clean_str(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip()
    return v or None


def _parse_optional_float(value: str | None) -> float | None:
    v = _clean_str(value)
    if v is None:
        return None
    try:
        return float(v)
    except ValueError:
        return None


@router.get("/search")
def search(
    query: str | None = Query(default=None),
    category: str | None = Query(default=None),
    min_price: str | None = Query(default=None),
    max_price: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = _clean_str(query)
    category = _clean_str(category)
    min_price_f = _parse_optional_float(min_price)
    max_price_f = _parse_optional_float(max_price)

    q = (
        db.query(ServiceListing, OrganizerInfo)
        .outerjoin(OrganizerInfo, ServiceListing.org_id == OrganizerInfo.org_id)
        .filter(_not_deleted())
    )

    if query:
        term = f"%{query}%"
        q = q.filter(
            or_(
                ServiceListing.title.ilike(term),
                OrganizerInfo.company_name.ilike(term),
                ServiceListing.category.ilike(term),
            )
        )

    if category:
        q = q.filter(ServiceListing.category.ilike(category))

    if min_price_f is not None:
        q = q.filter(ServiceListing.base_price >= min_price_f)

    if max_price_f is not None:
        q = q.filter(ServiceListing.base_price <= max_price_f)

    rows = q.order_by(ServiceListing.base_price.asc()).all()

    listing_ids = [sl.id for sl, _ in rows]
    img_map: dict[str, str | None] = {}
    if listing_ids:
        imgs = (
            db.query(ListingImage)
            .filter(ListingImage.listing_id.in_(listing_ids))
            .order_by(ListingImage.listing_id, ListingImage.id)
            .all()
        )
        for im in imgs:
            if im.listing_id not in img_map:
                img_map[im.listing_id] = im.image_url

    out = []
    for sl, oi in rows:
        addons = (
            db.query(ServiceAddon)
            .filter(ServiceAddon.listing_id == sl.id)
            .order_by(ServiceAddon.id)
            .all()
        )
        d = {
            "id": sl.id,
            "org_id": sl.org_id,
            "company_name": oi.company_name if oi else None,
            "category": sl.category,
            "title": sl.title,
            "base_price": float(sl.base_price),
            "image_url": img_map.get(sl.id),
            "addons": [
                {"id": a.id, "addon_name": a.addon_name, "price": float(a.price)} for a in addons
            ],
        }
        out.append(d)
    return out


@router.get("/ui/search", response_class=HTMLResponse)
def search_ui(
    request: Request,
    query: str | None = Query(default=None),
    category: str | None = Query(default=None),
    min_price: str | None = Query(default=None),
    max_price: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = _clean_str(query)
    category = _clean_str(category)
    min_price_f = _parse_optional_float(min_price)
    max_price_f = _parse_optional_float(max_price)

    q = (
        db.query(ServiceListing, OrganizerInfo)
        .outerjoin(OrganizerInfo, ServiceListing.org_id == OrganizerInfo.org_id)
        .filter(_not_deleted())
    )

    if query:
        term = f"%{query}%"
        q = q.filter(
            or_(
                ServiceListing.title.ilike(term),
                OrganizerInfo.company_name.ilike(term),
                ServiceListing.category.ilike(term),
            )
        )

    if category:
        q = q.filter(ServiceListing.category.ilike(category))

    if min_price_f is not None:
        q = q.filter(ServiceListing.base_price >= min_price_f)

    if max_price_f is not None:
        q = q.filter(ServiceListing.base_price <= max_price_f)

    rows = q.order_by(ServiceListing.base_price.asc()).all()

    listing_ids = [sl.id for sl, _ in rows]
    img_map: dict[str, str | None] = {}
    if listing_ids:
        imgs = (
            db.query(ListingImage)
            .filter(ListingImage.listing_id.in_(listing_ids))
            .order_by(ListingImage.listing_id, ListingImage.id)
            .all()
        )
        for im in imgs:
            if im.listing_id not in img_map:
                img_map[im.listing_id] = im.image_url

    addon_map: dict[str, list[dict]] = {}
    if listing_ids:
        addons = (
            db.query(ServiceAddon)
            .filter(ServiceAddon.listing_id.in_(listing_ids))
            .order_by(ServiceAddon.listing_id, ServiceAddon.id)
            .all()
        )
        for a in addons:
            addon_map.setdefault(a.listing_id, []).append(
                {"id": a.id, "addon_name": a.addon_name, "price": float(a.price)}
            )

    return templates.TemplateResponse(
        request,
        "search/search.html",
        {
            "rows": rows,
            "img_map": img_map,
            "addon_map": addon_map,
            "filters": {
                "query": query or "",
                "category": category or "",
                "min_price": "" if min_price_f is None else str(min_price_f),
                "max_price": "" if max_price_f is None else str(max_price_f),
            },
            "nav_active": "search",
            "role_badge": "Search",
        },
    )
