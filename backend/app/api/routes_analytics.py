"""Analytics, geo heatmap, and public config routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import require_role
from app.db.base import get_db
from app.schemas import HeatPoint, KPIResponse, TrendPoint
from app.services import analytics, geo

router = APIRouter(tags=["analytics"])


@router.get("/analytics/kpis", response_model=KPIResponse)
def get_kpis(db: Session = Depends(get_db),
             user: dict = Depends(require_role("admin", "officer"))):
    return analytics.kpis(db)


@router.get("/analytics/trends", response_model=list[TrendPoint])
def get_trends(groupby: str = "type", db: Session = Depends(get_db),
               user: dict = Depends(require_role("admin", "officer"))):
    return analytics.trends(db, groupby)


@router.get("/geo/heatmap", response_model=list[HeatPoint])
def get_heatmap(type: str | None = None, db: Session = Depends(get_db),
                user: dict = Depends(require_role("admin", "officer"))):
    return geo.heatmap(db, type)


@router.get("/config")
def public_config():
    """Non-secret config the frontend needs (Mappls map SDK key is a client-side key)."""
    return {"mappls_map_key": settings.MAPPLS_MAP_SDK_KEY}
