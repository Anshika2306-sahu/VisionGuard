"""Download a helmet (and/or number-plate) dataset from Roboflow Universe.

Reads ROBOFLOW_API_KEY from .env. Tries a list of known public helmet projects; you can also
pass an exact --workspace/--project/--version (copy these from Roboflow's "Download Dataset
-> Show download code"). Saves YOLO-format data into data/raw/helmet/.

Run:  python scripts/download_roboflow.py
      python scripts/download_roboflow.py --workspace WS --project PROJ --version 3
"""

from __future__ import annotations

import argparse
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "raw", "helmet")

# Known public helmet/number-plate projects on Roboflow Universe (best-effort).
KNOWN = [
    ("helmet-and-number-plate-detection-project",
     "helmet-and-number-plate-detection-for-motorbike-safety-iityz"),
    ("school-fkfkz", "helmet-detection-project"),
    ("objectdetection-2cqkv", "helmet-detection-2-vamco"),
]


def read_env(key: str) -> str | None:
    path = os.path.join(REPO, ".env")
    if not os.path.exists(path):
        return None
    for line in open(path):
        line = line.strip()
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].split("#")[0].strip()
    return None


def try_download(rf, ws, proj, fmt, versions):
    for v in versions:
        try:
            project = rf.workspace(ws).project(proj)
            ds = project.version(v).download(fmt, location=OUT, overwrite=True)
            print(f"SUCCESS: {ws}/{proj} v{v} -> {ds.location}")
            return True
        except Exception as e:
            print(f"  {ws}/{proj} v{v}: {str(e)[:120]}")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--project")
    ap.add_argument("--version", type=int)
    ap.add_argument("--format", default="yolov8")
    args = ap.parse_args()

    api_key = read_env("ROBOFLOW_API_KEY")
    if not api_key:
        print("ROBOFLOW_API_KEY not set in .env")
        return 1

    from roboflow import Roboflow

    rf = Roboflow(api_key=api_key)
    os.makedirs(OUT, exist_ok=True)

    if args.workspace and args.project:
        versions = [args.version] if args.version else list(range(1, 8))
        ok = try_download(rf, args.workspace, args.project, args.format, versions)
        return 0 if ok else 1

    print("Trying known public helmet projects...")
    for ws, proj in KNOWN:
        if try_download(rf, ws, proj, args.format, list(range(1, 8))):
            return 0

    print("\nCould not auto-download. Open your chosen helmet project on Roboflow Universe,")
    print("click Download Dataset -> Show download code, and run e.g.:")
    print("  python scripts/download_roboflow.py --workspace <WS> --project <PROJ> --version <N>")
    return 1


if __name__ == "__main__":
    sys.exit(main())
