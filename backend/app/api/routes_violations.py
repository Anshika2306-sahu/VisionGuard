"""Violation review routes (confirm -> challan, dismiss)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.base import get_db
from app.db.models import AuditLog, Camera, Violation
from app.schemas import ViolationOut
from app.services import enforcement

router = APIRouter(prefix="/violations", tags=["violations"])


@router.get("", response_model=list[ViolationOut])
def list_violations(
    type: str | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "officer")),
):
    stmt = select(Violation).order_by(Violation.created_at.desc())
    if type:
        stmt = stmt.where(Violation.type == type)
    if status:
        stmt = stmt.where(Violation.status == status)
    if camera_id:
        stmt = stmt.where(Violation.camera_id == camera_id)
    stmt = stmt.limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


@router.post("/{violation_id}/confirm", response_model=ViolationOut)
def confirm(violation_id: str, db: Session = Depends(get_db),
            user: dict = Depends(require_role("admin", "officer"))):
    v = db.get(Violation, violation_id)
    if not v:
        raise HTTPException(404, "violation not found")
    if v.severity != "finable":
        raise HTTPException(400, "safety alerts are not finable")
    v.status = "auto_issued"
    if not v.challan:
        camera = db.get(Camera, v.camera_id) if v.camera_id else None
        enforcement.create_challan(db, v, camera)
    db.add(AuditLog(user_email=user["email"], action="confirm_violation",
                    meta={"violation_id": v.id}))
    db.commit()
    db.refresh(v)
    return v


@router.post("/{violation_id}/dismiss", response_model=ViolationOut)
def dismiss(violation_id: str, reason: str = "", db: Session = Depends(get_db),
            user: dict = Depends(require_role("admin", "officer"))):
    v = db.get(Violation, violation_id)
    if not v:
        raise HTTPException(404, "violation not found")
    v.status = "dismissed"
    db.add(AuditLog(user_email=user["email"], action="dismiss_violation",
                    meta={"violation_id": v.id, "reason": reason}))
    db.commit()
    db.refresh(v)
    return v
