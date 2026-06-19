"""Analytics: KPI summary, trends, and search helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Camera, Challan, Violation


def kpis(db: Session) -> dict:
    today = datetime.now(timezone.utc).date()
    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)

    challans_total = db.scalar(select(func.count(Challan.id))) or 0
    challans_today = db.scalar(
        select(func.count(Challan.id)).where(Challan.issued_at >= today_start)
    ) or 0
    active_cameras = db.scalar(select(func.count(Camera.id))) or 0
    accident_alerts = db.scalar(
        select(func.count(Violation.id)).where(Violation.type == "accident")
    ) or 0
    jam_zones = db.scalar(
        select(func.count(Violation.id)).where(Violation.type == "traffic_jam")
    ) or 0
    pending_review = db.scalar(
        select(func.count(Violation.id)).where(Violation.status == "needs_review")
    ) or 0
    fine_collected = db.scalar(
        select(func.coalesce(func.sum(Challan.fine_amount), 0)).where(Challan.status == "paid")
    ) or 0
    fine_outstanding = db.scalar(
        select(func.coalesce(func.sum(Challan.fine_amount), 0)).where(
            Challan.status.in_(["issued", "notified", "contested", "expired"])
        )
    ) or 0

    return {
        "challans_total": challans_total,
        "challans_today": challans_today,
        "active_cameras": active_cameras,
        "accident_alerts": accident_alerts,
        "jam_zones": jam_zones,
        "pending_review": pending_review,
        "fine_collected": int(fine_collected),
        "fine_outstanding": int(fine_outstanding),
    }


def trends(db: Session, groupby: str = "type") -> list[dict]:
    if groupby == "type":
        rows = db.execute(
            select(Violation.type, func.count(Violation.id)).group_by(Violation.type)
        ).all()
        return [{"key": k, "count": c} for k, c in rows]
    if groupby == "day":
        # last 14 days
        since = datetime.now(timezone.utc) - timedelta(days=14)
        rows = db.execute(
            select(func.date(Violation.created_at), func.count(Violation.id))
            .where(Violation.created_at >= since)
            .group_by(func.date(Violation.created_at))
        ).all()
        return [{"key": str(k), "count": c} for k, c in rows]
    if groupby == "zone":
        rows = db.execute(
            select(Camera.zone, func.count(Violation.id))
            .join(Camera, Violation.camera_id == Camera.id)
            .group_by(Camera.zone)
        ).all()
        return [{"key": k or "Unknown", "count": c} for k, c in rows]
    return []
