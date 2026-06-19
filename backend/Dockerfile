# VisionGuard backend (API + worker share this image).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:/app/backend

# OpenCV runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt backend-req.txt
COPY ml/requirements.txt ml-req.txt
# CPU torch is fine for the prototype
RUN pip install --upgrade pip && pip install -r backend-req.txt -r ml-req.txt

COPY backend ./backend
COPY ml ./ml

WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
