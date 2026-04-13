from pydantic import BaseModel


class ListingOut(BaseModel):
    id: str
    org_id: str | None = None
    company_name: str | None = None
    category: str
    title: str
    base_price: float
    is_deleted: bool = False


class AdminOrderAddonOut(BaseModel):
    addon_id: str
    addon_name: str | None = None
    unit_price: float


class AdminOrderOut(BaseModel):
    order_id: str
    event_id: str | None = None
    listing_id: str | None = None
    listing_title: str | None = None
    org_id: str | None = None
    organizer_name: str | None = None
    customer_id: str | None = None
    customer_name: str | None = None
    event_date: str | None = None 
    event_status: str | None = None
    payment_status: str | None = None
    base_price_at_booking: float
    addons: list[AdminOrderAddonOut] = []
    addons_total: float
    total_price_calculated: float


class AdminUserOut(BaseModel):
    id: str
    username: str
    role: str
    status: str


class SetUserStatusIn(BaseModel):
    status: str 
    reason: str | None = None

