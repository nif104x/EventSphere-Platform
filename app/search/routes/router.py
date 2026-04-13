from fastapi import APIRouter, Query

from app.search.services.services import search_listings

router = APIRouter()


@router.get("/search")
def search(
    query: str | None = Query(default=None),
    category: str | None = Query(default=None),
    min_price: float | None = Query(default=None),
    max_price: float | None = Query(default=None),
):
    return search_listings(
        query=query,
        category=category,
        min_price=min_price,
        max_price=max_price,
    )

