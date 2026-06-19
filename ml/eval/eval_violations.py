"""Violation-level Precision / Recall / F1 + confusion matrix on a labelled mini-set.

Provide a CSV with columns:  image_path,gt_type   (gt_type in VIOLATION_TYPES or 'none')
The script runs the full pipeline per image, takes the highest-confidence violation as the
prediction, and compares to ground truth.

Run:  python ml/eval/eval_violations.py --labels path/to/labels.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True, help="CSV: image_path,gt_type")
    ap.add_argument("--weights", default="ml/weights/uvh26/yolo11s.pt")
    args = ap.parse_args()

    if not os.path.exists(args.labels):
        print(f"labels CSV not found: {args.labels}")
        print("Format: image_path,gt_type  (gt_type in VIOLATION_TYPES or 'none')")
        return 1

    import cv2
    from sklearn.metrics import classification_report, confusion_matrix

    from ml.pipeline.detector import load_detector
    from ml.pipeline.helmet import load_helmet_model
    from ml.pipeline.runner import analyze

    detector = load_detector(os.path.join(REPO, args.weights))
    helmet = load_helmet_model()

    y_true, y_pred = [], []
    with open(args.labels) as f:
        for row in csv.DictReader(f):
            img = cv2.imread(row["image_path"])
            if img is None:
                continue
            res = analyze(img, detector, helmet, run_anpr=False)
            vios = sorted(res["violations"], key=lambda v: -v["confidence"])
            pred = vios[0]["type"] if vios else "none"
            y_true.append(row["gt_type"].strip() or "none")
            y_pred.append(pred)

    if not y_true:
        print("no rows evaluated")
        return 1

    labels = sorted(set(y_true) | set(y_pred))
    report = classification_report(y_true, y_pred, labels=labels, zero_division=0, output_dict=True)
    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()
    print(classification_report(y_true, y_pred, labels=labels, zero_division=0))

    result = {"violations": {"report": report, "labels": labels, "confusion_matrix": cm,
                             "n": len(y_true)}}
    mpath = os.path.join(REPO, "ml", "eval", "metrics.json")
    existing = json.load(open(mpath)) if os.path.exists(mpath) else {}
    existing.update(result)
    json.dump(existing, open(mpath, "w"), indent=2)
    print("wrote", mpath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
