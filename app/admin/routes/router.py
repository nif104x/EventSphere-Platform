from fastapi import APIRouter, HTTPException

from app.admin.schemas.schemas import (
    AdminOrderOut,
    AdminUserOut,
    ListingOut,
    SetUserStatusIn,
)
from app.admin.services.services import (
    ban_or_unban_user,
    delete_listing_soft,
    get_orders_for_admin,
    get_users_for_admin,
    list_listings_for_admin,
)

router = APIRouter()


@router.get("/listings", response_model=list[ListingOut])
def admin_listings():
    return list_listings_for_admin()


@router.delete("/listings/{listing_id}")
def admin_delete_listing(listing_id: str):
    ok = delete_listing_soft(listing_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"message": "Listing deleted (soft delete)"}


@router.get("/orders", response_model=list[AdminOrderOut])
def admin_orders():
    return get_orders_for_admin()


@router.get("/users", response_model=list[AdminUserOut])
def admin_users():
    return get_users_for_admin()


@router.patch("/users/{user_id}/status")
def admin_set_user_status(user_id: str, body: SetUserStatusIn):
    ok = ban_or_unban_user(user_id=user_id, status=body.status, reason=body.reason)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User status updated"}

