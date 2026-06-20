# VisionGuard — Testing & Usage Guide (end to end)

Everything you need to **start, stop, and exercise every feature**. Two ways to use it:
the **live site** (no setup) or **locally** (full control).

- 🌐 **Live:** https://sahuanshika2306-visionguard.hf.space
- 💻 **Local:** instructions below

**Logins**

| Role | Email | Password | Lands on |
|---|---|---|---|
| Officer | `officer@visionguard.in` | `officer123` | Command Center |
| Admin | `admin@visionguard.in` | `admin123` | Command Center |
| Citizen | `citizen@visionguard.in` | `citizen123` | Citizen Portal |

---

## 1. Start / Stop

### A. Local (recommended for the live demo — most reliable)

**Start (one command):**
```bash
cd VisionGuard
bash scripts/run_local.sh
```
- Command Center → http://localhost:5173
- API docs (Swagger) → http://localhost:8000/docs

**Start (manual, two terminals):**
```bash
# terminal 1 — backend
cd VisionGuard && source .venv/bin/activate
DATABASE_URL="sqlite:///./data/visionguard.db" PROCESS_MODE=inline \
  uvicorn app.main:app --app-dir backend --port 8000

# terminal 2 — frontend
cd VisionGuard/frontend && export PATH="/opt/homebrew/bin:$PATH" && npm run dev
```

**Stop:** press `Ctrl-C` in the terminal(s). That's it — local run costs nothing.

**Reset the local data (fresh demo):**
```bash
rm -f VisionGuard/data/visionguard.db   # cameras/users are re-seeded on next start
```

### B. Docker (full stack: Postgres + Redis + worker)
```bash
cd VisionGuard
docker compose -f infra/docker-compose.yml up --build     # start
docker compose -f infra/docker-compose.yml down           # stop
```

### C. Live Space (Hugging Face)
- It's **always on** and **free**. It auto-sleeps after long inactivity and wakes on the next visit.
- **Pause it** (to fully stop): Space page → Settings → "Pause this Space".
- **Restart/rebuild**: Space page → Settings → "Factory reboot" / "Restart".
- **Redeploy after code changes**: `python scripts/deploy_hf_space.py visionguard`

---

## 2. Test images (in `test_images/`)

| File | What it is | Expected result |
|---|---|---|
| `no_helmet_closeup_1.jpg` | Rider without helmet | **`no_helmet` violation → ₹1,000 challan** |
| `no_helmet_closeup_2.jpg` | Rider without helmet | **`no_helmet` violation → challan** |
| `no_helmet_closeup_3.jpg` | Rider without helmet | **`no_helmet` violation** |
| `helmet_ok_1.jpg` | Rider wearing helmet | **No violation** (correctly clean) |
| `helmet_ok_2.jpg` | Rider wearing helmet | No violation (or low-confidence → review) |
| `cctv_bengaluru_traffic_1.png` | Dense Bengaluru CCTV frame | **Many vehicles → `traffic_jam` safety alert** |
| `cctv_bengaluru_traffic_2.png` | Bengaluru CCTV frame | Vehicle detections (auto-rickshaw, car, truck…) |
| `cctv_bengaluru_traffic_3.png` | Bengaluru CCTV frame | Vehicle detections + possible jam alert |

> These are real images from the open **UVH-26** (Bengaluru Safe City CCTV) and **Roboflow
> helmet** datasets (both CC BY 4.0).

### Want more / internet images?
Download your own and drop them into the upload box. Good free sources + search terms:
- **Google Images / Bing** → "Bengaluru traffic signal CCTV", "Indian bike rider no helmet",
  "triple riding India", "wrong side driving India", "no parking violation India".
- **Wikimedia Commons** (free-licensed): search "traffic India", "motorcycle helmet".
- **Pexels / Unsplash** (free): search "indian traffic", "motorbike street".
- The full datasets: `data/raw/helmet/` (helmet) and `data/samples/` (UVH-26 CCTV).
- For best results use clear, well-lit images where riders/plates are reasonably large
  (far-away CCTV plates often read as `UNREADABLE` — that's expected and handled).

---

## 3. Feature-by-feature walkthrough (Command Center)

Log in as **officer**. Then:

1. **KPI cards** (top) — challans today, active cameras, accident alerts, jam zones, pending review,
   fines collected/outstanding. They refresh live.
2. **Safety Heatmap** (Mappls) — Bengaluru map with incident hotspots. (If the map can't load, it
   falls back to a geocoded list — the dashboard never breaks.)
3. **Violations by Type** chart — bar chart that fills as you analyze frames.
4. **Analyze a Frame:**
   - Pick a camera (e.g., *KR Puram Hanging Bridge* — it has a stop-line + red signal configured).
   - Click **Upload image** → choose `test_images/no_helmet_closeup_1.jpg`.
   - Watch: annotated evidence appears with boxes + a **`no_helmet` violation card** (confidence),
     and a **challan (₹1,000, status `notified`, due in 72h)** is auto-created.
   - Try `cctv_bengaluru_traffic_1.png` → a **`traffic_jam` zero-fine alert** + many vehicle boxes.
   - Try `helmet_ok_1.jpg` → **no violation** (proves it doesn't false-fire on helmeted riders).
5. **Review Queue** tab — low-confidence detections wait here. **Confirm** (issues a challan) or
   **Dismiss** (logged in the audit trail). This is the fairness / human-in-the-loop step.
6. **Challans** tab — searchable records (plate, type, fine, status, location). Click "mark paid"
   to move a challan to `paid`.

## 4. Feature walkthrough (Citizen Portal)

Log out → log in as **citizen** → enter plate **`KA01AB1234`** → **Search**:
- See **your own** challans + total outstanding + nearby safety alerts on a local map.
- Try another plate (e.g., `KA05XX1111`) → **blocked** (citizens can only see their own vehicle).

---

## 5. Test the API directly (Swagger / curl)

Swagger UI: http://localhost:8000/docs (local) — click **Authorize**, log in, try any endpoint.

curl example (local):
```bash
# login -> token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=officer@visionguard.in&password=officer123" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# upload an image
curl -s -X POST http://localhost:8000/api/v1/ingest/image \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_images/no_helmet_closeup_1.jpg"

# list challans
curl -s http://localhost:8000/api/v1/challans -H "Authorization: Bearer $TOKEN"
```
(For the live site, replace the base URL with `https://sahuanshika2306-visionguard.hf.space`.)

---

## 6. Run the automated test suites
```bash
cd VisionGuard
.venv/bin/python scripts/test_violation_engine.py    # 23 tests — violation logic
.venv/bin/python scripts/test_backend_e2e.py         # 18 tests — full API flow
.venv/bin/python scripts/test_robustness.py          # 22 tests — security / bad input
.venv/bin/python ml/eval/bench_latency.py            # real latency / throughput
```

---

## 7. Costs & keeping it live (important)

| Service | Used for | Cost | Notes |
|---|---|---|---|
| **Hugging Face Space (CPU)** | hosting the live app | **FREE** | Free CPU tier; auto-sleeps when idle. Do **not** switch to a paid GPU. |
| **Roboflow** | dataset download (one-time) | **FREE / done** | Not called at runtime — zero ongoing cost. |
| **MapMyIndia / Mappls** | maps + geocoding | free dev tier | Only counts when someone **opens the dashboard**; geocodes are cached. Idle = no hits. |
| **Models / OCR** | inference | **FREE** | Run on the Space's CPU; no paid API calls anywhere. |

**Can you keep it live 24/7?** Yes — the free HF Space won't burn money. To be safe:
- Keep the Space on the **free CPU** hardware (never upgrade to paid GPU/persistent storage).
- Don't leave the dashboard open in many browser tabs forever (each open map view uses Mappls quota).
- In your Mappls console, confirm you're on the **free plan** with **no card set for auto-charge**.
- Roboflow: don't re-run dataset downloads.

There are **no paid APIs** in the running app, so normal demo usage costs ₹0.

---

## 8. Troubleshooting
| Symptom | Fix |
|---|---|
| Frontend can't reach API (local) | Start the backend first; check http://localhost:8000/health |
| Map blank | Expected if offline / key limit — falls back to a geocoded list automatically |
| `no_helmet` not firing | Use a clear, close image; far CCTV shots favor vehicle/jam detection |
| Plate `UNREADABLE` | Far/blurred plates can't be OCR'd — expected; close shots read better |
| Live Space slow on first hit | It was asleep; first request wakes it (~30–60s), then it's fast |
