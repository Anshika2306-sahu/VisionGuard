"""Smoke-test the full CV pipeline on a single image.

Usage:
    python scripts/try_pipeline.py data/samples/your_image.jpg
    python scripts/try_pipeline.py data/samples/your_image.jpg --weights ml/weights/uvh26/yolo11s.pt

If no weights are given (or they don't exist) a COCO YOLO model is auto-downloaded so the
pipeline still runs end-to-end.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# allow `import ml...` when run from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2  # noqa: E402

from ml.pipeline.detector import load_detector  # noqa: E402
from ml.pipeline.helmet import load_helmet_model  # noqa: E402
from ml.pipeline.runner import analyze  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", help="path to an image")
    ap.add_argument("--weights", default=os.getenv("MODEL_DETECTOR"), help="detector weights")
    ap.add_argument("--helmet", default=os.getenv("MODEL_HELMET"), help="helmet weights (optional)")
    ap.add_argument("--out", default="data/evidence/try_annotated.jpg")
    ap.add_argument("--no-anpr", action="store_true", help="skip OCR (faster)")
    args = ap.parse_args()

    img = cv2.imread(args.image)
    if img is None:
        raise SystemExit(f"could not read image: {args.image}")

    print("loading detector...", flush=True)
    detector = load_detector(args.weights)
    if getattr(detector, "using_fallback", False):
        print("  (using COCO fallback weights — download UVH-26 for Bengaluru accuracy)")
    helmet = load_helmet_model(args.helmet)

    print("analyzing...", flush=True)
    result = analyze(img, detector, helmet, run_anpr=not args.no_anpr)

    jpeg = result.pop("annotated_jpeg")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    if jpeg:
        with open(args.out, "wb") as f:
            f.write(jpeg)
        print(f"annotated evidence -> {args.out}")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
