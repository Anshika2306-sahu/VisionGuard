#!/bin/sh
# Container entrypoint: ensure a vehicle model exists, then serve API + UI on $PORT.
set -e

# If the UVH-26 vehicle model wasn't baked into the image, download it (uses HF token if set).
if ! python -c "import glob,sys; sys.exit(0 if glob.glob('ml/weights/uvh26/**/*.pt', recursive=True) else 1)"; then
  echo "vehicle model not found — downloading UVH-26..."
  python scripts/fetch_models.py || echo "download failed; will use COCO fallback"
fi

exec uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port "${PORT:-7860}"
