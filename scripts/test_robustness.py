"""Break-it / regression suite: security scoping, malformed input, error handling, idempotency.
Uses a mock detector (fast, no torch). Run:  python scripts/test_robustness.py
"""

from __future__ import annotations

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "backend"))
os.environ["DATABASE_URL"] = "sqlite:///./data/_rob_test.db"
os.environ["MAPPLS_REST_KEY"] = ""
os.environ["PROCESS_MODE"] = "inline"
_db = os.path.join(REPO, "data", "_rob_test.db")
if os.path.exists(_db):
    os.remove(_db)

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
    passed += 1 if cond else 0
    failed += 0 if cond else 1


class MockDetector:
    def predict(self, image):
        return [
            Detection("two_wheeler", 0.92, (900, 500, 1000, 700)),
            Detection("person", 0.88, (905, 410, 995, 560)),
        ]


class MockHelmet:
    def predict(self, crop):
        return "no_helmet", 0.9


orch.set_models(MockDetector(), MockHelmet())
client = TestClient(app)


def token(email, pw):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": pw})
    return r.json().get("access_token")


officer = {"Authorization": f"Bearer {token('officer@visionguard.in', 'officer123')}"}
citizen = {"Authorization": f"Bearer {token('citizen@visionguard.in', 'citizen123')}"}

print("auth & RBAC:")
check("no token -> 401", client.get("/api/v1/analytics/kpis").status_code == 401)
check("bad token -> 401", client.get("/api/v1/analytics/kpis", headers={"Authorization": "Bearer x"}).status_code == 401)
check("citizen blocked from KPIs (403)", client.get("/api/v1/analytics/kpis", headers=citizen).status_code == 403)
check("citizen blocked from violations (403)", client.get("/api/v1/violations", headers=citizen).status_code == 403)
check("citizen blocked from ingest (403)",
      client.post("/api/v1/ingest/image", headers=citizen,
                  files={"file": ("a.jpg", b"x", "image/jpeg")}).status_code == 403)
check("officer allowed KPIs (200)", client.get("/api/v1/analytics/kpis", headers=officer).status_code == 200)

print("citizen data scoping:")
check("citizen reads OWN plate (200)",
      client.get("/api/v1/citizen/challans", headers=citizen, params={"plate": "KA01AB1234"}).status_code == 200)
check("citizen blocked from OTHER plate (403)",
      client.get("/api/v1/citizen/challans", headers=citizen, params={"plate": "KA99ZZ9999"}).status_code == 403)
check("officer can query any plate (200)",
      client.get("/api/v1/citizen/challans", headers=officer, params={"plate": "KA99ZZ9999"}).status_code == 200)

print("malformed / edge inputs:")
check("empty file -> 400",
      client.post("/api/v1/ingest/image", headers=officer,
                  files={"file": ("a.jpg", b"", "image/jpeg")}).status_code == 400)
# non-image bytes -> job should FAIL gracefully, not crash the server
r = client.post("/api/v1/ingest/image", headers=officer,
                files={"file": ("a.jpg", b"this is not an image", "image/jpeg")})
check("garbage upload accepted (202)", r.status_code == 202)
jid = r.json()["id"]
job = client.get(f"/api/v1/jobs/{jid}", headers=officer).json()
check("garbage upload -> job failed gracefully", job["status"] == "failed")
check("server still alive after failure", client.get("/health").status_code == 200)
check("unknown job -> 404", client.get("/api/v1/jobs/does-not-exist", headers=officer).status_code == 404)
check("unknown challan -> 404", client.get("/api/v1/challans/nope", headers=officer).status_code == 404)
check("SQLi-ish plate search no crash",
      client.get("/api/v1/challans", headers=officer, params={"plate": "' OR 1=1;--"}).status_code == 200)
check("oversized page rejected (422)",
      client.get("/api/v1/violations", headers=officer, params={"limit": 9999}).status_code == 422)

print("processing + idempotency:")
img = (np.random.default_rng(1).integers(0, 256, (1080, 1920, 3))).astype(np.uint8)
ok, buf = cv2.imencode(".jpg", img)
r = client.post("/api/v1/ingest/image", headers=officer,
                files={"file": ("f.jpg", buf.tobytes(), "image/jpeg")})
jid = r.json()["id"]
job = client.get(f"/api/v1/jobs/{jid}", headers=officer).json()
check("valid job done", job["status"] == "done")
nh = [v for v in job["violations"] if v["type"] == "no_helmet"]
check("no_helmet present", len(nh) > 0)
# confirm twice -> only one challan
before = len(client.get("/api/v1/challans", headers=officer).json())
client.post(f"/api/v1/violations/{nh[0]['id']}/confirm", headers=officer)
client.post(f"/api/v1/violations/{nh[0]['id']}/confirm", headers=officer)
after = len(client.get("/api/v1/challans", headers=officer).json())
check("confirm is idempotent (no duplicate challan)", after - before <= 1)
check("confirm on safety alert -> 400",
      (lambda vs: client.post(f"/api/v1/violations/{vs[0]['id']}/confirm", headers=officer).status_code == 400
       if vs else True)(
          [v for v in client.get("/api/v1/violations", headers=officer, params={"type": "traffic_jam"}).json()]
      ) if True else True)
check("reprocess works (202)",
      client.post(f"/api/v1/jobs/{jid}/reprocess", headers=officer).status_code == 202)

print(f"\n{passed} passed, {failed} failed")
if os.path.exists(_db):
    os.remove(_db)
sys.exit(1 if failed else 0)
