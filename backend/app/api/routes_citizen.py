"""Citizen Portal routes: read-only, scoped to own plate + nearby safety alerts."""

from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import HTTPException
from sqlalchemy import select as _select

from app.core.security import get_current_user
from app.db.base import get_db
from app.db.models import Camera, Challan, User, Violation
from app.schemas import ChallanOut

router = APIRouter(prefix="/citizen", tags=["citizen"])


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.get("/challans", response_model=list[ChallanOut])
def my_challans(plate: str = Query(...), db: Session = Depends(get_db),
                user: dict = Depends(get_current_user)):
    plate = plate.upper().strip()
    # citizens may only query their OWN registered plate; officers/admins may query any
    if user["role"] == "citizen":
        u = db.scalar(_select(User).where(User.email == user["email"]))
        if not u or not u.plate_text or u.plate_text.upper() != plate:
            raise HTTPException(403, "citizens can only view their own vehicle's challans")
    stmt = select(Challan).where(Challan.plate_text == plate).order_by(Challan.issued_at.desc())
    return list(db.scalars(stmt).all())


@router.get("/alerts")
def nearby_alerts(lat: float, lng: float, radius: float = 3.0,
                  db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Return nearby zero-fine safety alerts (accidents, jams) within `radius` km."""
    rows = db.execute(
        select(Violation, Camera)
        .join(Camera, Violation.camera_id == Camera.id)
        .where(Violation.severity == "safety_alert")
    ).all()
    out = []
    for v, cam in rows:
        d = _haversine_km(lat, lng, cam.lat, cam.lng)
        if d <= radius:
            out.append({
                "type": v.type, "lat": cam.lat, "lng": cam.lng,
                "distance_km": round(d, 2), "confidence": v.confidence,
                "address": cam.address or cam.name,
            })
    out.sort(key=lambda x: x["distance_km"])
    return out
