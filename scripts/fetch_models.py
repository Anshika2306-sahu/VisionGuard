"""Download the UVH-26 (Bengaluru Safe City) pretrained YOLO detector from Hugging Face.

Reads HUGGINGFACE_TOKEN from .env. Discovers a YOLO .pt across iisc-aim repos and saves it
into ml/weights/uvh26/. If nothing is found, the pipeline still works via the COCO fallback.

Usage:  python scripts/fetch_models.py
"""

from __future__ import annotations

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "ml", "weights", "uvh26")


def read_env(key: str) -> str | None:
    path = os.path.join(REPO, ".env")
    if not os.path.exists(path):
        return None
    for line in open(path):
        line = line.strip()
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].split("#")[0].strip()
    return None


def main() -> int:
    from huggingface_hub import HfApi, hf_hub_download, login

    token = read_env("HUGGINGFACE_TOKEN")
    if token and not token.startswith("hf_PASTE"):
        try:
            login(token=token)
            print("HF login ok")
        except Exception as e:
            print(f"HF login failed ({e}); trying anonymous")

    api = HfApi()
    os.makedirs(OUT, exist_ok=True)

    # gather .pt candidates across iisc-aim model repos
    candidates: list[tuple[str, str]] = []  # (repo_id, filename)
    try:
        models = list(api.list_models(author="iisc-aim"))
    except Exception as e:
        print(f"could not list models: {e}")
        models = []
    print(f"found {len(models)} iisc-aim model repos")
    for m in models:
        try:
            files = api.list_repo_files(m.id)
        except Exception:
            continue
        for f in files:
            if f.endswith(".pt"):
                candidates.append((m.id, f))

    if not candidates:
        print("No .pt found in iisc-aim model repos. The detector will use the COCO fallback.")
        print("You can still download manually later; the system remains fully functional.")
        return 0

    def score(c):
        name = c[1].lower()
        s = 0
        if "yolov11" in name or "yolo11" in name:
            s -= 4
        if "yolov8" in name or "yolo8" in name:
            s -= 2
        if name.endswith("s.pt") or "small" in name:
            s -= 2
        if name.endswith("n.pt") or "nano" in name:
            s -= 1
        return s

    candidates.sort(key=score)
    print("top candidates:")
    for c in candidates[:5]:
        print("  ", c)

    repo_id, filename = candidates[0]
    print(f"downloading {repo_id} :: {filename}")
    local = hf_hub_download(repo_id=repo_id, filename=filename, local_dir=OUT)
    print(f"saved -> {local}")
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
