"""ORM models (see docs/04_LLD.md section 2). Portable across SQLite and Postgres."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default="citizen")  # admin|officer|citizen
    hashed_pw: Mapped[str] = mapped_column(String(255))
    plate_text: Mapped[str | None] = mapped_column(String(20), nullable=True)  # citizen's vehicle
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Camera(Base):
    __tablename__ = "cameras"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(64), index=True)  # Safe City cam id
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    zone: Mapped[str | None] = mapped_column(String(128), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    rois: Mapped[list["ROI"]] = relationship(back_populates="camera", cascade="all, delete-orphan")


class ROI(Base):
    __tablename__ = "rois"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    camera_id: Mapped[str] = mapped_column(ForeignKey("cameras.id"))
    kind: Mapped[str] = mapped_column(String(32))  # stop_line|no_parking|lane_dir|signal_lamp
    geometry: Mapped[dict] = mapped_column(JSON)    # normalized 0..1 points
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    camera: Mapped["Camera"] = relationship(back_populates="rois")


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    camera_id: Mapped[str | None] = mapped_column(ForeignKey("cameras.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="upload")  # upload|rtsp|batch
    image_uri: Mapped[str] = mapped_column(String(512))
    annotated_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued|processing|done|failed|unusable
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    detections: Mapped[list["Detection"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    violations: Mapped[list["Violation"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detections"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    cls: Mapped[str] = mapped_column(String(40))
    conf: Mapped[float] = mapped_column(Float)
    bbox: Mapped[list] = mapped_column(JSON)
    attrs: Mapped[dict] = mapped_column(JSON, default=dict)

    job: Mapped["Job"] = relationship(back_populates="detections")


class Violation(Base):
    __tablename__ = "violations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    camera_id: Mapped[str | None] = mapped_column(ForeignKey("cameras.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(40), index=True)
    severity: Mapped[str] = mapped_column(String(20))  # finable|safety_alert
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20))  # auto_issued|needs_review|dismissed|alert
    bbox: Mapped[list | None] = mapped_column(JSON, nullable=True)
    plate_text: Mapped[str | None] = mapped_column(String(20), nullable=True)
    evidence_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    rationale: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    job: Mapped["Job"] = relationship(back_populates="violations")
    challan: Mapped["Challan | None"] = relationship(back_populates="violation", uselist=False)


class Challan(Base):
    __tablename__ = "challans"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    violation_id: Mapped[str] = mapped_column(ForeignKey("violations.id"))
    camera_id: Mapped[str | None] = mapped_column(ForeignKey("cameras.id"), nullable=True)
    plate_text: Mapped[str] = mapped_column(String(20), index=True)
    violation_type: Mapped[str] = mapped_column(String(40))
    fine_amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="issued")  # issued|notified|paid|contested|expired
    evidence_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    enotice_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    violation: Mapped["Violation"] = relationship(back_populates="challan")


class Vehicle(Base):
    __tablename__ = "vehicles"
    plate_text: Mapped[str] = mapped_column(String(20), primary_key=True)
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vehicle_class: Mapped[str | None] = mapped_column(String(40), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(128))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    at: Mapped[datetime] = mapped_column(DateTime, default=_now)
