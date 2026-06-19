"""Geo service: Mappls reverse-geocoding (cached) + heatmap aggregation."""

from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Camera, Violation

_MAPPLS_REV = "https://apis.mappls.com/advancedmaps/v1/{key}/rev_geocode"


def reverse_geocode(lat: float, lng: float) -> str | None:
    """Return a human-readable address via Mappls, or None on any failure (offline-safe)."""
    if not settings.MAPPLS_REST_KEY or settings.MAPPLS_REST_KEY.startswith("__"):
        return None
    try:
        url = _MAPPLS_REV.format(key=settings.MAPPLS_REST_KEY)
        r = httpx.get(url, params={"lat": lat, "lng": lng}, timeout=5.0)
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        if results:
            return results[0].get("formatted_address")
    except Exception:
        return None
    return None


def ensure_camera_address(db: Session, camera: Camera) -> str | None:
    if camera.address:
        return camera.address
    addr = reverse_geocode(camera.lat, camera.lng)
    if addr:
        camera.address = addr
        db.add(camera)
        db.commit()
    return addr


def heatmap(db: Session, vtype: str | None = None) -> list[dict]:
    """Aggregate violations to weighted geo points for the Mappls heatmap.

    Prototype aggregates in Python; at scale this becomes a PostGIS spatial query.
    """
    stmt = select(Violation, Camera).join(Camera, Violation.camera_id == Camera.id)
    if vtype:
        stmt = stmt.where(Violation.type == vtype)
    rows = db.execute(stmt).all()

    buckets: dict[tuple, dict] = {}
    for v, cam in rows:
        key = (round(cam.lat, 5), round(cam.lng, 5), v.severity)
        b = buckets.setdefault(
            key,
            {"lat": cam.lat, "lng": cam.lng, "weight": 0.0,
             "type": v.type, "severity": v.severity},
        )
        b["weight"] += 1.0
        b["type"] = v.type
    return list(buckets.values())
