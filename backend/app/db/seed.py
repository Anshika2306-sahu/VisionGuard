"""Idempotent demo seed: users + real Bengaluru junction cameras (+ some ROIs)."""

from __future__ import annotations

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import SessionLocal
from app.db.models import ROI, Camera, User

DEMO_USERS = [
    {"email": "admin@visionguard.in", "role": "admin", "pw": "admin123"},
    {"email": "officer@visionguard.in", "role": "officer", "pw": "officer123"},
    {"email": "citizen@visionguard.in", "role": "citizen", "pw": "citizen123", "plate": "KA01AB1234"},
]

# Real Bengaluru junctions (lat, lng) — known congestion/Safe-City hotspots
DEMO_CAMERAS = [
    {"name": "Silk Board Junction", "code": "BLR-SBJ-01", "lat": 12.9170, "lng": 77.6228,
     "zone": "South", "config": {"jam_threshold": 12}},
    {"name": "Hebbal Flyover", "code": "BLR-HBL-02", "lat": 13.0358, "lng": 77.5970,
     "zone": "North", "config": {"jam_threshold": 14}},
    {"name": "KR Puram Hanging Bridge", "code": "BLR-KRP-03", "lat": 13.0078, "lng": 77.6960,
     "zone": "East", "config": {"jam_threshold": 12, "signal_state": "red"}},
    {"name": "Marathahalli Bridge", "code": "BLR-MTH-04", "lat": 12.9560, "lng": 77.7010,
     "zone": "East", "config": {"jam_threshold": 12}},
    {"name": "Trinity Circle (MG Road)", "code": "BLR-TRN-05", "lat": 12.9726, "lng": 77.6203,
     "zone": "Central", "config": {"jam_threshold": 10}},
    {"name": "Tin Factory", "code": "BLR-TIN-06", "lat": 13.0110, "lng": 77.6660,
     "zone": "East", "config": {"jam_threshold": 13}},
]


def seed() -> None:
    db = SessionLocal()
    try:
        if db.scalar(select(User).limit(1)) is None:
            for u in DEMO_USERS:
                db.add(User(email=u["email"], role=u["role"],
                            hashed_pw=hash_password(u["pw"]), plate_text=u.get("plate")))

        existing = {c.code for c in db.scalars(select(Camera)).all()}
        for c in DEMO_CAMERAS:
            if c["code"] in existing:
                continue
            cam = Camera(name=c["name"], code=c["code"], lat=c["lat"], lng=c["lng"],
                         zone=c["zone"], config=c["config"])
            db.add(cam)
            db.flush()
            # give a couple of cameras example ROIs so geometry violations can fire
            if c["code"] == "BLR-KRP-03":
                db.add(ROI(camera_id=cam.id, kind="stop_line",
                           geometry={"points": [[0.15, 0.62], [0.85, 0.62]]}, meta={}))
            if c["code"] == "BLR-TRN-05":
                db.add(ROI(camera_id=cam.id, kind="no_parking",
                           geometry={"points": [[0.05, 0.70], [0.35, 0.70],
                                                [0.35, 0.96], [0.05, 0.96]]}, meta={}))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    from app.db.base import init_db

    init_db()
    seed()
    print("seeded demo users + Bengaluru cameras")
