"""Ingestion + job routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import require_role
from app.core.storage import storage
from app.db.base import get_db
from app.db.models import Detection, Job, Violation
from app.schemas import JobDetail, JobOut
from app.services.orchestrator import process_job

router = APIRouter(tags=["ingest"])


def _enqueue(job_id: str, background: BackgroundTasks):
    if settings.PROCESS_MODE == "celery":
        try:
            from app.worker import process_job_task

            process_job_task.delay(job_id)
            return
        except Exception:
            pass  # fall back to inline if broker unavailable
    background.add_task(process_job, job_id)


@router.post("/ingest/image", response_model=JobOut, status_code=202)
def ingest_image(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    camera_id: str | None = Form(None),
    captured_at: str | None = Form(None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "officer")),
):
    data = file.file.read()
    if not data:
        raise HTTPException(400, "empty file")

    job = Job(camera_id=camera_id, source="upload", image_uri="pending", status="queued")
    if captured_at:
        try:
            job.captured_at = datetime.fromisoformat(captured_at)
        except ValueError:
            pass
    db.add(job)
    db.flush()  # get job.id

    key = f"uploads/{job.id}.jpg"
    storage.save(key, data)
    job.image_uri = key
    db.commit()
    db.refresh(job)

    _enqueue(job.id, background)
    return job


@router.post("/ingest/batch", response_model=list[JobOut], status_code=202)
def ingest_batch(
    background: BackgroundTasks,
    files: list[UploadFile] = File(...),
    camera_id: str | None = Form(None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "officer")),
):
    jobs = []
    for f in files:
        data = f.file.read()
        if not data:
            continue
        job = Job(camera_id=camera_id, source="batch", image_uri="pending", status="queued")
        db.add(job)
        db.flush()
        key = f"uploads/{job.id}.jpg"
        storage.save(key, data)
        job.image_uri = key
        jobs.append(job)
    db.commit()
    for j in jobs:
        db.refresh(j)
        _enqueue(j.id, background)
    return jobs


@router.get("/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: str, db: Session = Depends(get_db),
            user: dict = Depends(require_role("admin", "officer"))):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    # JobDetail (from_attributes) reads job.detections / job.violations relationships
    return JobDetail.model_validate(job)


@router.post("/jobs/{job_id}/reprocess", response_model=JobOut, status_code=202)
def reprocess(job_id: str, background: BackgroundTasks, db: Session = Depends(get_db),
              user: dict = Depends(require_role("admin", "officer"))):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    db.query(Detection).filter(Detection.job_id == job_id).delete()
    db.query(Violation).filter(Violation.job_id == job_id).delete()
    job.status = "queued"
    job.error = None
    db.commit()
    db.refresh(job)
    _enqueue(job.id, background)
    return job
