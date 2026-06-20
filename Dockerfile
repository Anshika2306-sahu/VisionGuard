# All-in-one image for Hugging Face Spaces: builds the React UI and serves it
# together with the FastAPI backend (+ CV models) from a single container on :7860.

# ---- stage 1: build the frontend ----
FROM node:20-slim AS fe
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm install
COPY frontend ./
RUN npm run build

# ---- stage 2: python app ----
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend \
    HF_HUB_DISABLE_XET=1 \
    HOME=/app/data \
    YOLO_CONFIG_DIR=/app/data/ultralytics \
    STATIC_DIR=/app/frontend_dist \
    DATABASE_URL=sqlite:///./data/visionguard.db \
    PROCESS_MODE=inline \
    MODEL_DETECTOR=ml/weights/uvh26/yolo11s.pt \
    MODEL_HELMET=ml/weights/helmet/best.pt \
    OCR_ENGINE=easyocr \
    PORT=7860

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /app/data && chmod -R 777 /app/data
COPY deploy/requirements-space.txt req.txt
RUN pip install --no-cache-dir -r req.txt

COPY backend ./backend
COPY ml ./ml
COPY scripts ./scripts
COPY --from=fe /fe/dist ./frontend_dist

# Bake the runtime-downloaded models so the first request is instant and needs no write
# perms at runtime (non-fatal: falls back to runtime download if a build-time fetch fails).
RUN python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')" || true
RUN python -c "import easyocr; easyocr.Reader(['en'], gpu=False)" || true

# writable dirs for sqlite, evidence, caches
RUN mkdir -p /app/ml/weights/uvh26 && chmod -R 777 /app/data /app/ml/weights /app/yolo11n.pt 2>/dev/null; \
    chmod -R 777 /app/data /app/ml/weights || true

EXPOSE 7860
CMD ["sh", "scripts/start.sh"]
