"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


# ---- auth ----
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


# ---- cameras / roi ----
class CameraIn(BaseModel):
    name: str
    code: str
    lat: float
    lng: float
    zone: Optional[str] = None
    config: dict = {}


class CameraOut(CameraIn):
    id: str
    address: Optional[str] = None

    class Config:
        from_attributes = True


class ROIIn(BaseModel):
    kind: str               # stop_line|no_parking|lane_dir|signal_lamp
    geometry: dict          # {"points": [[x,y],...]} normalized 0..1
    meta: dict = {}


class ROIOut(ROIIn):
    id: str
    camera_id: str

    class Config:
        from_attributes = True


# ---- jobs / detections / violations ----
class DetectionOut(BaseModel):
    cls: str
    conf: float
    bbox: list[int]
    attrs: dict = {}

    class Config:
        from_attributes = True


class ViolationOut(BaseModel):
    id: str
    job_id: str
    type: str
    severity: str
    confidence: float
    status: str
    bbox: Optional[list[int]] = None
    plate_text: Optional[str] = None
    evidence_uri: Optional[str] = None
    rationale: dict = {}
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobOut(BaseModel):
    id: str
    camera_id: Optional[str] = None
    source: str
    status: str
    quality_score: Optional[float] = None
    image_uri: str
    annotated_uri: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobDetail(JobOut):
    detections: list[DetectionOut] = []
    violations: list[ViolationOut] = []


# ---- challans ----
class ChallanOut(BaseModel):
    id: str
    plate_text: str
    violation_type: str
    fine_amount: int
    status: str
    evidence_uri: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---- analytics ----
class KPIResponse(BaseModel):
    challans_total: int
    challans_today: int
    active_cameras: int
    accident_alerts: int
    jam_zones: int
    pending_review: int
    fine_collected: int
    fine_outstanding: int


class HeatPoint(BaseModel):
    lat: float
    lng: float
    weight: float
    type: str
    severity: str


class TrendPoint(BaseModel):
    key: str
    count: int


class GenericResponse(BaseModel):
    ok: bool = True
    detail: Any = None
