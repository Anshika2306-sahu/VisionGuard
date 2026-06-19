"""FastAPI app factory: routers, CORS, static evidence, startup (tables + seed)."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import (
    routes_analytics,
    routes_auth,
    routes_cameras,
    routes_challans,
    routes_citizen,
    routes_ingest,
    routes_violations,
)
from app.core.config import settings

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(
        title="VisionGuard AI",
        version="0.1.0",
        description="Automated traffic-violation detection on Bengaluru Safe City cameras.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for r in (
        routes_auth.router,
        routes_ingest.router,
        routes_violations.router,
        routes_challans.router,
        routes_cameras.router,
        routes_analytics.router,
        routes_citizen.router,
    ):
        app.include_router(r, prefix=API_PREFIX)

    # serve evidence images / e-notices
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    app.mount("/evidence", StaticFiles(directory=settings.STORAGE_DIR), name="evidence")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "visionguard", "process_mode": settings.PROCESS_MODE}

    @app.get("/")
    def root():
        return {"name": "VisionGuard AI", "docs": "/docs", "health": "/health"}

    @app.on_event("startup")
    def _startup():
        from app.db.base import init_db
        from app.db.seed import seed

        init_db()
        seed()

    return app


app = create_app()
