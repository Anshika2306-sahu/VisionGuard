# 08 — Tech Stack (free at every stage)

> Everything here has a **free path**. Paid options are noted only as the eventual scale upgrade.

## 1. At-a-glance

| Layer | Prototype (free) | Scale upgrade |
|---|---|---|
| Language | Python 3.11, TypeScript | same |
| Backend | **FastAPI** + Uvicorn | + Gunicorn workers, k8s |
| Queue | **Redis** + **Celery** | Redis Cluster / **Kafka** |
| DB | **PostgreSQL** (or SQLite for ultra-light) | Postgres + **PostGIS** HA, replicas |
| Object storage | local FS (interface) | **MinIO** → S3 |
| CV detection | **Ultralytics YOLO (v8/v11)** + UVH-26 weights | **ONNX** → **TensorRT** on **Triton** |
| OCR (ANPR) | **PaddleOCR** or **EasyOCR** | fine-tuned OCR + GPU |
| Image processing | **OpenCV**, NumPy, Pillow | same + GPU (cv2.cuda) |
| Frontend | **React + Vite + Tailwind** | static build + CDN |
| Maps | **Mappls / MapMyIndia Web SDK** (free dev tier) | paid tier (higher hits) |
| Auth | JWT (python-jose), passlib | + OAuth/SSO, gateway |
| Containerisation | **Docker + Docker Compose** | **Kubernetes** + Helm |
| Training compute | **Google Colab / Kaggle** free GPU | owned/cloud GPU |
| Hosting demo | local / **HF Spaces / Render / Railway / Fly.io** free | cloud k8s |
| Monitoring | logs + FastAPI metrics | **Prometheus + Grafana**, OTel, Loki |
| Experiment tracking | CSV / TensorBoard | Weights&Biases free / MLflow |

## 2. Backend dependencies (`backend/requirements.txt`)

```
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
psycopg[binary]            # postgres driver (use sqlite fallback if needed)
alembic                    # migrations
celery
redis
python-jose[cryptography]  # JWT
passlib[bcrypt]            # password hashing
python-multipart           # file uploads
httpx                      # Mappls REST calls
pillow
numpy
opencv-python-headless
```

## 3. ML dependencies (`ml/requirements.txt`)

```
ultralytics                # YOLOv8/v11 train+infer+export
torch                      # CPU build fine for prototype
torchvision
opencv-python-headless
numpy
paddleocr                  # OR easyocr (pick one)
paddlepaddle               # CPU
onnx
onnxruntime                # CPU inference (scale: onnxruntime-gpu / TensorRT)
huggingface_hub
datasets
pandas
matplotlib                 # eval plots
scikit-learn               # P/R/F1, confusion matrix
pycocotools                # mAP
```

> **OCR pick:** start with **EasyOCR** (simplest install) or **PaddleOCR** (better accuracy). Keep both
> behind the `read_plate()` interface so you can switch.

## 4. Frontend dependencies (`frontend/package.json` highlights)

```
react, react-dom
vite, @vitejs/plugin-react
tailwindcss, postcss, autoprefixer
react-router-dom            # Command Center vs Citizen routes
@tanstack/react-query       # data fetching/caching
recharts                    # KPI charts/trends
mappls-web-maps (or the Mappls JS SDK script tag)  # maps + heatmap
axios
lucide-react                # icons
```

## 5. Free compute & hosting playbook

| Task | Free resource | Notes |
|---|---|---|
| Fine-tune YOLO | **Kaggle** (30h/wk GPU) or **Colab** | upload UVH-26 subset; train YOLOv11s |
| Try models fast | **HF Spaces** (CPU/limited GPU) | demo deploy |
| Host API+UI demo | **Render / Railway / Fly.io** free | small dynos; or just local Docker |
| Datasets | **Hugging Face**, **Roboflow Universe**, **Kaggle**, **IDD portal** | all free accounts |
| Maps | **Mappls dev console** | free key; cache geocodes |
| Storage (self-host) | **MinIO** (Docker) | S3-compatible, free |

## 6. Versioning & reproducibility

- Pin versions in `requirements.txt` before submission (run `pip freeze` once stable).
- Commit `ml/configs/*.yaml` (class maps, thresholds, model paths).
- Model weights are **gitignored**; `scripts/fetch_models.sh` downloads them reproducibly.
- One `infra/docker-compose.yml` reproduces the whole stack on any machine.

## 7. Why each "headline" tool (1-liners for the deck)

- **FastAPI** — typed, async, auto Swagger docs; tiny but production-grade.
- **YOLO + UVH-26 weights** — best free, Bengaluru-trained detector; export-friendly to ONNX/TensorRT.
- **PaddleOCR/EasyOCR** — strong on noisy real plates; no training needed to start.
- **Postgres(+PostGIS)** — one DB from laptop to city; native geospatial heatmaps.
- **Redis/Celery** — dead-simple queue that scales to many workers.
- **React + Mappls** — fast dashboards on India's own mapping backbone (sponsor-aligned).
- **Docker → k8s** — one-command demo, clean path to autoscale.
