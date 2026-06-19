"""Camera + ROI configuration routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.base import get_db
from app.db.models import ROI, Camera
from app.schemas import CameraIn, CameraOut, ROIIn, ROIOut
from app.services import geo

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("", response_model=list[CameraOut])
def list_cameras(db: Session = Depends(get_db),
                 user: dict = Depends(require_role("admin", "officer"))):
    return list(db.scalars(select(Camera)).all())


@router.post("", response_model=CameraOut)
def create_camera(body: CameraIn, db: Session = Depends(get_db),
                  user: dict = Depends(require_role("admin"))):
    cam = Camera(**body.model_dump())
    db.add(cam)
    db.commit()
    db.refresh(cam)
    geo.ensure_camera_address(db, cam)
    db.refresh(cam)
    return cam


@router.get("/{camera_id}", response_model=CameraOut)
def get_camera(camera_id: str, db: Session = Depends(get_db),
               user: dict = Depends(require_role("admin", "officer"))):
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "camera not found")
    return cam


@router.get("/{camera_id}/roi", response_model=list[ROIOut])
def list_roi(camera_id: str, db: Session = Depends(get_db),
             user: dict = Depends(require_role("admin", "officer"))):
    return list(db.scalars(select(ROI).where(ROI.camera_id == camera_id)).all())


@router.post("/{camera_id}/roi", response_model=ROIOut)
def add_roi(camera_id: str, body: ROIIn, db: Session = Depends(get_db),
            user: dict = Depends(require_role("admin"))):
    if not db.get(Camera, camera_id):
        raise HTTPException(404, "camera not found")
    roi = ROI(camera_id=camera_id, kind=body.kind, geometry=body.geometry, meta=body.meta)
    db.add(roi)
    db.commit()
    db.refresh(roi)
    return roi


@router.delete("/{camera_id}/roi/{roi_id}")
def delete_roi(camera_id: str, roi_id: str, db: Session = Depends(get_db),
               user: dict = Depends(require_role("admin"))):
    roi = db.get(ROI, roi_id)
    if not roi or roi.camera_id != camera_id:
        raise HTTPException(404, "roi not found")
    db.delete(roi)
    db.commit()
    return {"ok": True}
