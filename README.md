# VisionGuard AI

**Automated Photo Identification & Classification of Traffic Violations using Computer Vision**

> Built for the Bengaluru Traffic Police (ASTraM) + MapMyIndia hackathon.
> We do not reinvent enforcement — we **reuse India's already-proven smart-traffic stack**
> (MLFF tolling, FASTag/RFID, ANPR cameras, multi-angle evidence capture, automated e-notice)
> and **extend it from tolling to full traffic-violation enforcement**, powered by Bengaluru's
> existing **Safe City CCTV network** and **MapMyIndia / Mappls** location intelligence.

---

## 30-second pitch

Indian highways already run **Multi-Lane Free-Flow (MLFF)** tolling: you drive through at 100 km/h,
an RFID reader scans your FASTag, an **ANPR camera reads your plate as a fallback**, LIDAR/radar build a
3D profile + measure speed, high-speed cameras grab **multi-angle photographic evidence**, and the system
**auto-flags violators and issues an e-notice payable in 72 hours**.

**VisionGuard takes that exact, battle-tested enforcement pattern and points it at city traffic.**
Instead of "did you pay the toll?", we ask "did you wear a helmet, stop at the line, park legally, ride
double-only?" — using the **same ANPR + multi-angle-evidence + auto-challan + e-notice loop**, running on the
**2,800+ Bengaluru Safe City cameras** that already exist (the very cameras behind the open **UVH-26 / BMD-45**
datasets), and plotting everything on **MapMyIndia/Mappls** maps.

## Why this is credible (not just a hackathon toy)

| Asset we reuse | What it is | Why it matters |
|---|---|---|
| **Bengaluru Safe City CCTV** | 2,800–3,600 existing police cameras | Zero new hardware to "go live" city-wide |
| **UVH-26 / BMD-45 datasets** | 26K–45K labelled images from *those exact cameras*, free (CC BY 4.0) | India-specific, Bengaluru-specific, pre-trained models included |
| **MLFF / FASTag / ANPR pattern** | Nationally deployed tolling enforcement loop | A proven, accepted enforcement workflow we mirror |
| **MapMyIndia / Mappls** | India's mapping backbone, free dev tier | Camera geolocation, heatmaps, citizen navigation alerts |

## What's in this repo

```
VisionGuard/
├── README.md                     ← you are here
├── docs/                         ← design set (read these in order)
│   ├── 00_INDEX.md               ← start here: how to read the docs
│   ├── 01_PROBLEM_AND_VISION.md  ← problem, reuse-existing-tech narrative, sponsor alignment
│   ├── 02_DATASETS.md            ← every free dataset, Bengaluru-first, how to download
│   ├── 03_HLD.md                 ← High-Level Design (architecture, components, diagrams)
│   ├── 04_LLD.md                 ← Low-Level Design (schemas, APIs, model contracts, rules)
│   ├── 05_WORKFLOW.md            ← end-to-end data flow + sequence diagrams
│   ├── 06_CHAIN_OF_THOUGHT.md    ← every design decision and *why*
│   ├── 07_SCALABILITY_ROADMAP.md ← prototype → whole-city scale (HLD + LLD of scaled system)
│   ├── 08_TECH_STACK.md          ← every tool, free at every stage
│   └── 11_PERFORMANCE_EVALUATION.md  ← Accuracy/Precision/Recall/F1/mAP + latency/throughput
├── backend/                      ← FastAPI service (ingestion, inference, challan, analytics)
├── ml/                           ← CV pipeline (preprocess, detect, ANPR, violation engine, eval)
├── frontend/                     ← React + Mappls dashboard (Command Center + Citizen Portal)
├── infra/                        ← Docker Compose, deployment configs
├── data/                         ← datasets, sample images, generated evidence
└── scripts/                      ← dataset download, model fetch, demo seeding
```

## Quick start (after the build phase)

```bash
# 1. clone + enter
cd VisionGuard

# 2. spin everything up (Postgres + Redis + API + worker + frontend)
docker compose -f infra/docker-compose.yml up --build

# 3. open the dashboard
#    Command Center : http://localhost:5173
#    API docs       : http://localhost:8000/docs
```

> Detailed, copy-paste, step-by-step instructions live in
> [`docs/09_STEP_BY_STEP_BUILD_GUIDE.md`](docs/09_STEP_BY_STEP_BUILD_GUIDE.md).

## Status — built & verified ✅

| Layer | State | Verification |
|---|---|---|
| Design docs (HLD/LLD/workflow/roadmap/master-prompt) | done | `docs/` (12 files) |
| ML pipeline (preprocess, detect, helmet, ANPR, annotate) | done | runs on real images |
| Violation Reasoning Engine | done | **23/23** unit tests |
| Real Bengaluru model (UVH-26 YOLOv11-S) | downloaded + running | detects India classes on real CCTV |
| Helmet model (trained on Roboflow set) | trained (quick CPU demo) | no-helmet 0.77–0.93; Colab notebook for full quality |
| FastAPI backend (auth/RBAC, ingest, challan, geo, analytics, citizen) | done | **18/18** e2e tests |
| Security / break testing | done | **22/22** robustness tests |
| Frontend (React + Mappls, Command Center + Citizen Portal) | done | `npm run build` passes |
| Docker Compose (db+redis+api+worker+frontend) | done | `infra/docker-compose.yml` |
| Eval harness (latency/mAP/P-R-F1) | done | **~98 ms/img, ~10 img/s on CPU** |

**63 automated tests passing**, plus real-model end-to-end verified (real `no_helmet` and `red_light`
challans created through the API on real Bengaluru frames).

### Run it locally (no Docker)

```bash
# one-time: models are already downloaded into ml/weights/ ; deps into .venv/
# backend (terminal 1)
cd VisionGuard && source .venv/bin/activate
DATABASE_URL="sqlite:///./data/visionguard.db" PROCESS_MODE=inline \
  uvicorn app.main:app --app-dir backend --port 8000
# frontend (terminal 2)
cd VisionGuard/frontend && npm run dev    # http://localhost:5173

# or both at once:
bash scripts/run_local.sh
```
Login: `officer@visionguard.in` / `officer123` (Command Center) · `citizen@visionguard.in` /
`citizen123` (Citizen Portal).

### Re-run the tests
```bash
.venv/bin/python scripts/test_violation_engine.py    # 23/23 engine logic
.venv/bin/python scripts/test_backend_e2e.py         # 18/18 API e2e
.venv/bin/python scripts/test_robustness.py          # 22/22 security/break tests
.venv/bin/python ml/eval/bench_latency.py            # real latency/throughput
```

### Full-quality helmet model (optional, free GPU)
Open `ml/notebooks/train_helmet_colab.ipynb` in Google Colab (T4 GPU) → Run all → download
`best.pt` → place at `ml/weights/helmet/best.pt`.

---

*VisionGuard AI — reuse what works, extend what's missing.*
