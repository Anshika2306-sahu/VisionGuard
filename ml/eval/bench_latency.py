"""Measure end-to-end pipeline latency + throughput on the current machine (real model).

Run:  python ml/eval/bench_latency.py [--weights ml/weights/uvh26/yolo11s.pt] [--anpr]
Writes ml/eval/metrics.json (system section).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

import cv2  # noqa: E402

from ml.pipeline.detector import load_detector  # noqa: E402
from ml.pipeline.helmet import load_helmet_model  # noqa: E402
from ml.pipeline.runner import analyze  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default="ml/weights/uvh26/yolo11s.pt")
    ap.add_argument("--samples", default="data/samples")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--anpr", action="store_true")
    args = ap.parse_args()

    imgs = [p for p in glob.glob(os.path.join(args.samples, "**", "*"), recursive=True)
            if p.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not imgs:
        print("no sample images found in", args.samples)
        return 1
    print(f"benchmarking on {len(imgs)} images x{args.repeats} repeats (anpr={args.anpr})")

    detector = load_detector(os.path.join(REPO, args.weights))
    helmet = load_helmet_model()
    fallback = getattr(detector, "using_fallback", False)

    # warmup
    warm = cv2.imread(imgs[0])
    analyze(warm, detector, helmet, run_anpr=False)

    times = []
    total_dets = 0
    for _ in range(args.repeats):
        for p in imgs:
            img = cv2.imread(p)
            if img is None:
                continue
            t0 = time.perf_counter()
            res = analyze(img, detector, helmet, run_anpr=args.anpr)
            times.append(time.perf_counter() - t0)
            total_dets += len(res["detections"])

    n = len(times)
    avg_ms = 1000 * sum(times) / n
    ips = n / sum(times)
    out = {
        "system": {
            "model": "COCO-fallback" if fallback else os.path.basename(args.weights),
            "device": "cpu",
            "images_benchmarked": n,
            "ms_per_image_cpu": round(avg_ms, 1),
            "images_per_sec_cpu": round(ips, 2),
            "anpr_enabled": args.anpr,
            "avg_detections_per_image": round(total_dets / n, 1),
        }
    }
    os.makedirs(os.path.join(REPO, "ml", "eval"), exist_ok=True)
    mpath = os.path.join(REPO, "ml", "eval", "metrics.json")
    existing = {}
    if os.path.exists(mpath):
        existing = json.load(open(mpath))
    existing.update(out)
    json.dump(existing, open(mpath, "w"), indent=2)
    print(json.dumps(out, indent=2))
    print("wrote", mpath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
