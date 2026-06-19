"""Celery worker (scale path). With PROCESS_MODE=celery, ingestion enqueues here.

Run:  celery -A app.worker.celery_app worker --loglevel=info
Falls back to inline BackgroundTasks automatically if the broker is unavailable.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import settings
from app.services.orchestrator import process_job

celery_app = Celery("visionguard", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.task_default_queue = "visionguard"


@celery_app.task(name="process_job")
def process_job_task(job_id: str) -> str:
    process_job(job_id)
    return job_id
