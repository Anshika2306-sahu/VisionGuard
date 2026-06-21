# VisionGuard AI

**Automated traffic-violation detection and classification using computer vision.**

VisionGuard is an end-to-end system that ingests CCTV footage and automatically detects, classifies, and evidences traffic violations — no-helmet riding, signal jumping, illegal parking — using a YOLOv11-based detection pipeline with ANPR for license-plate recognition. Detected violations flow through a FastAPI backend into automated challan generation, with a React + Mappls dashboard for live tracking and a citizen-facing portal for lookup.

Rather than building enforcement infrastructure from scratch, VisionGuard reuses India's already-proven smart-traffic stack — the same ANPR + multi-angle-evidence + auto-challan pattern used in highway MLFF/FASTag tolling — and extends it from tolling to full city traffic enforcement. It runs on Bengaluru's existing **2,800+ Safe City CCTV cameras** (the same cameras behind the open **UVH-26 / BMD-45** datasets) and plots everything on **MapMyIndia / Mappls** maps.

---

## Results

| Metric | Value |
|---|---|
| Inference latency | **~98 ms/image (~10 img/s) on CPU** |
| Violation engine tests | **23/23** passing |
| Backend API e2e tests | **18/18** passing |
| Security/robustness tests | **22/22** passing |
| **Total automated tests** | **63/63 passing** |
| Real-model verification | `no_helmet` and `red_light` challans generated end-to-end on real Bengaluru CCTV frames |
| Helmet detection confidence | 0.77–0.93 (quick CPU-trained demo model) |

---

## Why this approach is credible

| Asset reused | What it is | Why it matters |
|---|---|---|
| **Bengaluru Safe City CCTV** | 2,800–3,600 existing police cameras | Zero new hardware needed to go live city-wide |
| **UVH-26 / BMD-45 datasets** | 26K–45K labelled images from those exact cameras, free (CC BY 4.0) | India-specific, Bengaluru-specific, pre-trained models included |
| **MLFF / FASTag / ANPR pattern** | Nationally deployed tolling enforcement loop | A proven, already-accepted enforcement workflow we mirror |
| **MapMyIndia / Mappls** | India's mapping backbone, free dev tier | Camera geolocation, heatmaps, citizen navigation alerts |

---

## Architecture

```
VisionGuard/
├── backend/    ← FastAPI service (ingestion, inference, challan, analytics)
├── ml/         ← CV pipeline (preprocess, detect, ANPR, violation engine, eval)
├── frontend/   ← React + Mappls dashboard (Command Center + Citizen Portal)
├── infra/      ← Docker Compose, deployment configs
├── data/       ← datasets, sample images, generated evidence
├── scripts/    ← dataset download, model fetch, demo seeding
└── docs/       ← full design docs (HLD, LLD, workflow, roadmap, tech stack, eval)
```

<details>
<summary><strong>Full documentation index</strong> (click to expand)</summary>

| Doc | Covers |
|---|---|
| `01_PROBLEM_AND_VISION.md` | Problem statement, reuse-existing-tech narrative |
| `02_DATASETS.md` | Every dataset used, how to download |
| `03_HLD.md` | High-Level Design — architecture, components, diagrams |
| `04_LLD.md` | Low-Level Design — schemas, APIs, model contracts, rules |
| `05_WORKFLOW.md` | End-to-end data flow + sequence diagrams |
| `06_CHAIN_OF_THOUGHT.md` | Design decisions and rationale |
| `07_SCALABILITY_ROADMAP.md` | Prototype → whole-city scale (HLD + LLD) |
| `08_TECH_STACK.md` | Every tool used, free at every stage |
| `11_PERFORMANCE_EVALUATION.md` | Accuracy / Precision / Recall / F1 / mAP + latency |

</details>

---

## Tech Stack

- **ML / CV:** YOLOv11, ANPR (OCR), PyTorch
- **Backend:** FastAPI, PostgreSQL, Redis
- **Frontend:** React, Mappls/MapMyIndia
- **Infra:** Docker Compose

---

## Setup

### Run with Docker

```bash
cd VisionGuard
docker compose -f infra/docker-compose.yml up --build
```

- Command Center: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

### Run locally (no Docker)

```bash
# backend (terminal 1)
cd VisionGuard && source .venv/bin/activate
DATABASE_URL="sqlite:///./data/visionguard.db" PROCESS_MODE=inline \
  uvicorn app.main:app --app-dir backend --port 8000

# frontend (terminal 2)
cd VisionGuard/frontend && npm run dev    # http://localhost:5173

# or both at once:
bash scripts/run_local.sh
```

Login: `officer@visionguard.in` / `officer123` (Command Center) · `citizen@visionguard.in` / `citizen123` (Citizen Portal)

> For local development without Docker, see [`TESTING.md`](TESTING.md).

---

## Testing

```bash
.venv/bin/python scripts/test_violation_engine.py    # 23/23 engine logic
.venv/bin/python scripts/test_backend_e2e.py         # 18/18 API e2e
.venv/bin/python scripts/test_robustness.py          # 22/22 security/break tests
.venv/bin/python ml/eval/bench_latency.py            # real latency/throughput
```

---

## Roadmap

- **Full-quality helmet model** (optional, free GPU): open `ml/notebooks/train_helmet_colab.ipynb` in Google Colab (T4 GPU) → Run all → download `best.pt` → place at `ml/weights/helmet/best.pt`
- **Scale-up:** see `docs/07_SCALABILITY_ROADMAP.md` for the path from prototype to whole-city deployment

---

*VisionGuard AI — reuse what works, extend what's missing.*
