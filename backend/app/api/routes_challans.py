"""Challan routes (list, detail, pay stub)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.base import get_db
from app.db.models import AuditLog, Challan
from app.schemas import ChallanOut

router = APIRouter(prefix="/challans", tags=["challans"])


@router.get("", response_model=list[ChallanOut])
def list_challans(
    plate: str | None = None,
    status: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "officer")),
):
    stmt = select(Challan).order_by(Challan.issued_at.desc())
    if plate:
        stmt = stmt.where(Challan.plate_text.ilike(f"%{plate}%"))
    if status:
        stmt = stmt.where(Challan.status == status)
    return list(db.scalars(stmt.limit(limit).offset(offset)).all())


@router.get("/{challan_id}", response_model=ChallanOut)
def get_challan(challan_id: str, db: Session = Depends(get_db),
                user: dict = Depends(require_role("admin", "officer"))):
    c = db.get(Challan, challan_id)
    if not c:
        raise HTTPException(404, "challan not found")
    return c


@router.post("/{challan_id}/pay", response_model=ChallanOut)
def pay(challan_id: str, db: Session = Depends(get_db),
        user: dict = Depends(require_role("admin", "officer"))):
    c = db.get(Challan, challan_id)
    if not c:
        raise HTTPException(404, "challan not found")
    c.status = "paid"  # real gateway integration is a scale upgrade
    db.add(AuditLog(user_email=user["email"], action="pay_challan", meta={"challan_id": c.id}))
    db.commit()
    db.refresh(c)
    return c
