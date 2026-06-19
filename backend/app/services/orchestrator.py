"""Job orchestration: load image -> run CV pipeline -> persist detections/violations ->
issue challans -> update geo. Heavy ML imports are lazy so the API boots without torch.

Models are lazy singletons; `set_models()` lets tests inject mocks (no torch needed).
"""

from __future__ import annotations

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.storage import storage
from app.db.base import SessionLocal
from app.db.models import Camera, Detection, Job, Violation
from app.services import enforcement, geo

_detector = None
_helmet = None


def set_models(detector, helmet):
    """Inject models (used by tests with mocks)."""
    global _detector, _helmet
    _detector, _helmet = detector, helmet


def _abs(path: str) -> str:
    """Resolve a possibly-relative model path against the repo root (works in containers)."""
    import os

    return path if os.path.isabs(path) else str(settings.repo_root / path)


def get_models():
    global _detector, _helmet
    if _detector is None:
        from ml.pipeline.detector import load_detector
        from ml.pipeline.helmet import load_helmet_model

        _detector = load_detector(_abs(settings.MODEL_DETECTOR), conf=settings.CONF_FLOOR)
        _helmet = load_helmet_model(_abs(settings.MODEL_HELMET))
    return _detector, _helmet


def _roi_for_camera(camera: Camera | None) -> tuple[dict, str | None]:
    """Build the engine ROI dict from the camera's ROI rows + config."""
    roi: dict = {"no_parking": [], "stop_line": [], "lane_dir": []}
    signal_state = None
    if not camera:
        return roi, signal_state
    cfg = camera.config or {}
    if "jam_threshold" in cfg:
        roi["jam_threshold"] = cfg["jam_threshold"]
    signal_state = cfg.get("signal_state")
    for r in camera.rois:
        pts = (r.geometry or {}).get("points", [])
        if r.kind == "no_parking" and pts:
            roi["no_parking"].append(pts)
        elif r.kind == "stop_line" and pts:
            roi["stop_line"].append(pts)
        elif r.kind == "lane_dir":
            direction = (r.meta or {}).get("dir")
            if direction:
                roi["lane_dir"].append({"dir": direction})
    return roi, signal_state


def _decode_image(image_key: str) -> np.ndarray | None:
    import cv2

    data = storage.load(image_key)
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def process_job(job_id: str) -> None:
    """Entry point used by BackgroundTasks / Celery. Opens its own DB session."""
    db: Session = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            return
        job.status = "processing"
        db.commit()

        from ml.pipeline.runner import analyze  # lazy (needs cv2)

        image = _decode_image(job.image_uri)
        if image is None:
            job.status = "failed"
            job.error = "could not decode image"
            db.commit()
            return

        camera = db.get(Camera, job.camera_id) if job.camera_id else None
        roi, signal_state = _roi_for_camera(camera)
        detector, helmet = get_models()

        result = analyze(image, detector, helmet, roi=roi, mode="image", signal_state=signal_state)

        job.quality_score = result["quality"]

        # store annotated evidence
        annotated_uri = None
        if result.get("annotated_jpeg"):
            key = f"{job.id}/annotated.jpg"
            storage.save(key, result["annotated_jpeg"])
            annotated_uri = storage.url(key)
            job.annotated_uri = annotated_uri

        # persist detections
        for d in result["detections"]:
            db.add(Detection(job_id=job.id, cls=d["cls"], conf=d["conf"],
                             bbox=d["bbox"], attrs=d["attrs"]))

        # persist violations + challans
        if camera:
            geo.ensure_camera_address(db, camera)
        for v in result["violations"]:
            vio = Violation(
                job_id=job.id, camera_id=job.camera_id, type=v["type"],
                severity=v["severity"], confidence=v["confidence"], status=v["status"],
                bbox=v["bbox"], plate_text=v.get("plate_text"),
                evidence_uri=annotated_uri, rationale=v.get("rationale", {}),
            )
            db.add(vio)
            db.flush()
            if v["severity"] == "finable" and v["status"] == "auto_issued":
                enforcement.create_challan(db, vio, camera)

        job.status = "unusable" if result["quality"] < settings.QUALITY_FLOOR and not result["violations"] else "done"
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        job = db.get(Job, job_id)
        if job:
            job.status = "failed"
            job.error = str(e)[:2000]
            db.commit()
    finally:
        db.close()
