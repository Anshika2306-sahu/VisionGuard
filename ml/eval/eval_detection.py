"""Detection mAP via Ultralytics' validator.

Needs a YOLO-format data.yaml pointing at a labelled val split (e.g. a UVH-26/BMD-45 slice
exported to YOLO). Produces mAP@50 and mAP@50:95 (overall + per class).

Run:  python ml/eval/eval_detection.py --weights ml/weights/uvh26/<model>.pt --data path/to/data.yaml
"""

from __future__ import annotations

import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--data", required=True, help="YOLO data.yaml with a val split + labels")
    args = ap.parse_args()

    if not os.path.exists(args.data):
        print(f"data.yaml not found: {args.data}")
        print("Export a UVH-26/BMD-45 val slice to YOLO format, then point --data at it.")
        return 1

    from ultralytics import YOLO

    model = YOLO(args.weights)
    metrics = model.val(data=args.data, verbose=True)
    result = {
        "detection": {
            "mAP50": float(metrics.box.map50),
            "mAP50_95": float(metrics.box.map),
            "precision": float(metrics.box.mp),
            "recall": float(metrics.box.mr),
        }
    }
    mpath = os.path.join(REPO, "ml", "eval", "metrics.json")
    existing = json.load(open(mpath)) if os.path.exists(mpath) else {}
    existing.update(result)
    json.dump(existing, open(mpath, "w"), indent=2)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
