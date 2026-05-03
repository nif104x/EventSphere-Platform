import csv
import io
import os
from datetime import date

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.paths import APP_DIR
from app.database import get_db
from app.reports.services.orders import get_orders_report_rows

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory=str(APP_DIR / "reports" / "templates"))


@router.get("/orders.csv")
def export_orders_csv(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    payment_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    rows = get_orders_report_rows(
        db, from_date=from_date, to_date=to_date, payment_status=payment_status
    )

    def _iter():
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            [
                "order_id",
                "event_id",
                "event_date",
                "event_status",
                "customer_id",
                "customer_name",
                "customer_email",
                "organizer_id",
                "organizer_name",
                "listing_id",
                "listing_title",
                "payment_status",
                "base_price",
                "addons_total",
                "total_calculated",
            ]
        )
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)

        for r in rows:
            w.writerow(
                [
                    r["order_id"],
                    r["event_id"],
                    r["event_date"],
                    r["event_status"],
                    r["customer_id"],
                    r["customer_name"],
                    r["customer_email"],
                    r["organizer_id"],
                    r["organizer_name"],
                    r["listing_id"],
                    r["listing_title"],
                    r["payment_status"],
                    f'{r["base_price"]:.2f}',
                    f'{r["addons_total"]:.2f}',
                    f'{r["total_calculated"]:.2f}',
                ]
            )
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    name = "orders_export.csv"
    headers = {"Content-Disposition": f'attachment; filename="{name}"'}
    return StreamingResponse(_iter(), media_type="text/csv", headers=headers)


@router.get("/orders.pdf")
def export_orders_pdf(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    payment_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    api_key = os.getenv("PDFSHIFT_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing PDFSHIFT_API_KEY")

    rows = get_orders_report_rows(
        db, from_date=from_date, to_date=to_date, payment_status=payment_status
    )
    html = templates.get_template("orders.html").render(
        {
            "generated_at": date.today().isoformat(),
            "filters": {
                "from_date": from_date.isoformat() if from_date else "",
                "to_date": to_date.isoformat() if to_date else "",
                "payment_status": payment_status or "",
            },
            "rows": rows,
        }
    )

    try:
        r = requests.post(
            "https://api.pdfshift.io/v3/convert/pdf",
            headers={"X-API-Key": api_key},
            json={"source": html},
            timeout=45,
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=str(e))

    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"PDFShift error {r.status_code}: {r.text}")

    name = "orders_report.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{name}"'}
    return Response(content=r.content, media_type="application/pdf", headers=headers)

