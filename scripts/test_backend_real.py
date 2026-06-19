"""REAL end-to-end backend test: real UVH-26 detector + COCO persons + EasyOCR ANPR,
driven through the actual FastAPI app on a real Bengaluru CCTV image (no mocks).

Run:  python scripts/test_backend_real.py
"""

from __future__ import annotations

import glob
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "backend"))
os.environ["DATABASE_URL"] = "sqlite:///./data/_real_test.db"
os.environ["MAPPLS_REST_KEY"] = ""
os.environ["PROCESS_MODE"] = "inline"
os.environ.setdefault("MODEL_DETECTOR", "ml/weights/uvh26/yolo11s.pt")
_db = os.path.join(REPO, "data", "_real_test.db")
if os.path.exists(_db):
    os.remove(_db)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.db.base import init_db  # noqa: E402
from app.db.seed import seed  # noqa: E402

init_db()
seed()

passed = failed = 0


def check(name, cond):
    global passed, failed
    print(("  PASS  " if cond else "  FAIL  ") + name)
    passed += 1 if cond else 0
    failed += 0 if cond else 1


# pick a real Bengaluru sample image
imgs = [p for p in glob.glob(os.path.join(REPO, "data", "samples", "**", "*"), recursive=True)
        if p.lower().endswith((".png", ".jpg", ".jpeg")) and "annotated" not in p]
assert imgs, "no sample images; run the dataset download first"
img_path = sorted(imgs)[0]
print("using image:", os.path.relpath(img_path, REPO))

client = TestClient(app)
tok = client.post("/api/v1/auth/login",
                  data={"username": "officer@visionguard.in", "password": "officer123"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

# use KR Puram (has a stop_line ROI + signal red) so geometry rules can engage
cams = client.get("/api/v1/cameras", headers=H).json()
cam = next((c for c in cams if c["code"] == "BLR-KRP-03"), cams[0])

with open(img_path, "rb") as f:
    data = f.read()
r = client.post("/api/v1/ingest/image", headers=H,
                files={"file": ("blr.png", data, "image/png")}, data={"camera_id": cam["id"]})
check("ingest accepted", r.status_code == 202)
job_id = r.json()["id"]

job = client.get(f"/api/v1/jobs/{job_id}", headers=H).json()
print(f"    status={job['status']} quality={job['quality_score']} detections={len(job['detections'])} violations={len(job['violations'])}")
classes = {}
for d in job["detections"]:
    classes[d["cls"]] = classes.get(d["cls"], 0) + 1
print("    detected classes:", classes)
print("    violations:", [(v["type"], v["status"], round(v["confidence"], 2), v.get("plate_text")) for v in job["violations"]])

check("job processed (done)", job["status"] == "done")
check("real model detected vehicles", len(job["detections"]) >= 3)
check("India-specific classes present", any(c in classes for c in ["two_wheeler", "auto_rickshaw", "car", "truck"]))
check("annotated evidence produced", bool(job["annotated_uri"]))
check("at least one violation/alert raised", len(job["violations"]) >= 1)

# ANPR path executed (plate_text present on any finable violation, even if UNREADABLE)
fin = [v for v in job["violations"] if v["severity"] == "finable"]
if fin:
    check("ANPR ran on finable violation (plate field set)", fin[0]["plate_text"] is not None)

print(f"\n{passed} passed, {failed} failed")
if os.path.exists(_db):
    os.remove(_db)
sys.exit(1 if failed else 0)
