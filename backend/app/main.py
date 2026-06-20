"""FastAPI app factory: routers, CORS, static evidence, startup (tables + seed)."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

    # Optionally serve the built frontend from the same container (single-deploy mode,
    # e.g. Hugging Face Spaces). Only active when STATIC_DIR points at a built SPA.
    static_dir = os.getenv("STATIC_DIR", "")
    if static_dir and os.path.isdir(static_dir):
        assets = os.path.join(static_dir, "assets")
        if os.path.isdir(assets):
            app.mount("/assets", StaticFiles(directory=assets), name="assets")
        index_html = os.path.join(static_dir, "index.html")

        @app.get("/{full_path:path}")
        def spa(full_path: str):  # SPA fallback for client-side routes
            return FileResponse(index_html)
    else:
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
