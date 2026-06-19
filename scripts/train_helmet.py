"""Fine-tune a YOLO helmet/plate model on the Roboflow helmet dataset.

Writes a corrected data.yaml (Roboflow's relative paths often break), trains yolov8n, and
copies the best weights to ml/weights/helmet/best.pt (the path the backend expects).

Quick CPU demo:   python scripts/train_helmet.py --epochs 8 --fraction 0.06 --imgsz 416
Full (GPU):       python scripts/train_helmet.py --epochs 60 --fraction 1.0 --imgsz 640 --device 0
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "data", "raw", "helmet")


def write_fixed_yaml() -> str:
    import yaml

    src = os.path.join(DATA_DIR, "data.yaml")
    cfg = yaml.safe_load(open(src))
    fixed = {
        "path": DATA_DIR,
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "names": cfg["names"],
        "nc": cfg["nc"],
    }
    out = os.path.join(DATA_DIR, "data_fixed.yaml")
    yaml.safe_dump(fixed, open(out, "w"))
    print("classes:", cfg["names"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--imgsz", type=int, default=416)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--fraction", type=float, default=0.06)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--base", default="yolov8n.pt",
                    help="base weights to start from (e.g. ml/weights/helmet/best.pt to continue)")
    ap.add_argument("--copy-each-epoch", action="store_true",
                    help="copy best.pt to the live model path after every epoch")
    args = ap.parse_args()

    if not os.path.exists(os.path.join(DATA_DIR, "data.yaml")):
        print("helmet dataset missing — run scripts/download_roboflow.py first")
        return 1

    from ultralytics import YOLO

    data_yaml = write_fixed_yaml()
    base = args.base if os.path.exists(args.base) else "yolov8n.pt"
    print(f"starting from base weights: {base}")
    model = YOLO(base)

    src = os.path.join(REPO, "ml", "weights", "helmet_train", "run", "weights", "best.pt")
    dst_dir = os.path.join(REPO, "ml", "weights", "helmet")
    os.makedirs(dst_dir, exist_ok=True)

    if args.copy_each_epoch:
        # publish the improving model to the live path after every epoch
        def _on_epoch_end(trainer):
            if os.path.exists(src):
                shutil.copy(src, os.path.join(dst_dir, "best.pt"))
        model.add_callback("on_fit_epoch_end", _on_epoch_end)

    model.train(
        data=data_yaml, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
        fraction=args.fraction, device=args.device,
        project=os.path.join(REPO, "ml", "weights", "helmet_train"), name="run",
        exist_ok=True, verbose=True, plots=False,
    )
    shutil.copy(src, os.path.join(dst_dir, "best.pt"))
    print("HELMET_MODEL_READY", os.path.join(dst_dir, "best.pt"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
