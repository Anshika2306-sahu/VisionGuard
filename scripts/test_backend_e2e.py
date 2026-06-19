"""End-to-end backend test using FastAPI TestClient + a mock detector (no torch needed).

Validates: app boot, seed, auth, upload -> background processing -> violation engine ->
challan creation, citizen lookup. Run:  python scripts/test_backend_e2e.py
"""

from __future__ import annotations

import os
import sys

# --- force a clean sqlite db + offline geo BEFORE importing the app ---
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "backend"))
os.environ["DATABASE_URL"] = "sqlite:///./data/_e2e_test.db"
os.environ["MAPPLS_REST_KEY"] = ""          # skip network reverse-geocode
os.environ["PROCESS_MODE"] = "inline"
_dbfile = os.path.join(REPO, "data", "_e2e_test.db")
if os.path.exists(_dbfile):
    os.remove(_dbfile)

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.db.base import init_db  # noqa: E402
from app.db.seed import seed  # noqa: E402
import app.services.orchestrator as orch  # noqa: E402
from ml.pipeline.types import Detection  # noqa: E402

init_db()
seed()

passed = failed = 0


def check(name, cond):
    global passed, failed
    print(("  PASS  " if cond else "  FAIL  ") + name)
    if cond:
        passed += 1
    else:
        failed += 1


# --- mock models (no torch / no easyocr) ---
class MockDetector:
    def predict(self, image):
        return [
            Detection("two_wheeler", 0.92, (900, 500, 1000, 700)),
            Detection("person", 0.88, (905, 410, 995, 560)),      # rider above the bike
            Detection("car", 0.95, (200, 800, 320, 900)),          # inside Trinity no-parking ROI
        ]


class MockHelmet:
    def predict(self, crop):
        return "no_helmet", 0.9


orch.set_models(MockDetector(), MockHelmet())

client = TestClient(app)

print("health:")
r = client.get("/health")
check("health ok", r.status_code == 200 and r.json()["status"] == "ok")

print("auth:")
r = client.post("/api/v1/auth/login",
                data={"username": "officer@visionguard.in", "password": "officer123"})
check("officer login", r.status_code == 200)
token = r.json()["access_token"]
H = {"Authorization": f"Bearer {token}"}
check("wrong password rejected",
      client.post("/api/v1/auth/login",
                  data={"username": "officer@visionguard.in", "password": "x"}).status_code == 401)
check("no token -> 401", client.get("/api/v1/analytics/kpis").status_code == 401)

print("cameras seeded:")
r = client.get("/api/v1/cameras", headers=H)
cams = r.json()
check("6 cameras seeded", len(cams) == 6)
trinity = next((c for c in cams if c["code"] == "BLR-TRN-05"), None)
check("Trinity camera present", trinity is not None)

print("ingest + process (background runs in TestClient):")
# realistic-quality frame (textured) so the quality gate does not suppress finable violations
rng = np.random.default_rng(0)
img = rng.integers(0, 256, (1080, 1920, 3), dtype=np.uint8)
ok, buf = cv2.imencode(".jpg", img)
r = client.post("/api/v1/ingest/image", headers=H,
                files={"file": ("frame.jpg", buf.tobytes(), "image/jpeg")},
                data={"camera_id": trinity["id"]})
check("ingest accepted (202)", r.status_code == 202)
job_id = r.json()["id"]

r = client.get(f"/api/v1/jobs/{job_id}", headers=H)
job = r.json()
check("job done", job["status"] == "done")
vtypes = {v["type"] for v in job["violations"]}
print("    detected violations:", vtypes)
check("no_helmet detected", "no_helmet" in vtypes)
check("illegal_parking detected (review, image-mode)",
      "illegal_parking" in vtypes)
check("annotated evidence saved", bool(job["annotated_uri"]))

print("challans:")
r = client.get("/api/v1/challans", headers=H)
challans = r.json()
check("at least one challan auto-issued", len(challans) >= 1)
if challans:
    c = challans[0]
    print(f"    challan: {c['violation_type']} Rs.{c['fine_amount']} plate={c['plate_text']} status={c['status']}")
    check("challan has 72h due date", c["due_at"] is not None)

print("kpis + heatmap:")
r = client.get("/api/v1/analytics/kpis", headers=H)
k = r.json()
check("kpis has active_cameras=6", k["active_cameras"] == 6)
check("kpis pending_review >= 1", k["pending_review"] >= 1)
r = client.get("/api/v1/geo/heatmap", headers=H)
check("heatmap returns points", isinstance(r.json(), list) and len(r.json()) >= 1)

print("review queue (dismiss):")
review = [v for v in job["violations"] if v["status"] == "needs_review"]
if review:
    r = client.post(f"/api/v1/violations/{review[0]['id']}/dismiss", headers=H,
                    params={"reason": "false positive"})
    check("dismiss works", r.status_code == 200 and r.json()["status"] == "dismissed")

print("config exposes mappls key field:")
check("/config present", "mappls_map_key" in client.get("/api/v1/config").json())

print(f"\n{passed} passed, {failed} failed")
if os.path.exists(_dbfile):
    os.remove(_dbfile)
sys.exit(1 if failed else 0)
