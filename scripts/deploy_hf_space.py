"""Deploy VisionGuard as a single Hugging Face Space (Docker): API + UI in one container.

Reads HUGGINGFACE_TOKEN + Mappls keys from .env, creates the Space, uploads the project
(with the helmet + UVH-26 models baked in), and sets runtime secrets.

Usage:  python scripts/deploy_hf_space.py [space_name]
"""

from __future__ import annotations

import os
import secrets
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPACE_README = """---
title: VisionGuard
emoji: \U0001F6A6
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
---

# VisionGuard
Automated traffic-violation detection on Bengaluru Safe City cameras (UVH-26) with MapMyIndia maps.
Single-container deploy: FastAPI API + React dashboard.

**Demo logins** — officer@visionguard.in / officer123 · citizen@visionguard.in / citizen123
"""

IGNORE = [
    ".git", ".git/**", ".venv/**", "**/node_modules/**", "frontend/dist/**",
    ".hf_cache/**", "data/raw/**", "data/processed/**", "data/evidence/**",
    "data/samples/**", "**/__pycache__/**", "*.db", "**/*.db",
    "ml/weights/helmet_train/**", "docs/09_*", "docs/10_*", "docs/12_*", "docs/13_*",
    "VisionGuard_Design_Thoughts.md", "*.zip", ".env", "README.md",
    "yolo11n.pt", "yolov8n.pt",
    # NEVER upload .gitignore: HF honors it and would then ignore our model .pt files
    ".gitignore",
]


def read_env(key: str) -> str:
    path = os.path.join(REPO, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].split("#")[0].strip()
    return ""


def main() -> int:
    from huggingface_hub import HfApi

    token = read_env("HUGGINGFACE_TOKEN")
    if not token or token.startswith("__") or token.startswith("hf_PASTE"):
        print("HUGGINGFACE_TOKEN missing in .env"); return 1

    api = HfApi()
    user = api.whoami(token=token)["name"]
    name = sys.argv[1] if len(sys.argv) > 1 else "visionguard"
    repo_id = f"{user}/{name}"
    print(f"deploying to Space: {repo_id}")

    api.create_repo(repo_id, repo_type="space", space_sdk="docker", exist_ok=True, token=token)

    print("uploading project (this includes the baked-in models)...")
    api.upload_folder(
        folder_path=REPO, repo_id=repo_id, repo_type="space", token=token,
        ignore_patterns=IGNORE, commit_message="Deploy VisionGuard (API + UI)",
    )

    # Model weights are gitignored locally, so upload them explicitly (baked into the image
    # for instant first-use). upload_folder would skip them; upload_file forces them in.
    import glob as _glob
    weights = ["ml/weights/helmet/best.pt"] + _glob.glob(
        os.path.join(REPO, "ml/weights/uvh26/**/*.pt"), recursive=True)
    for w in weights:
        rel = os.path.relpath(w, REPO) if os.path.isabs(w) else w
        if os.path.exists(os.path.join(REPO, rel)):
            print("uploading model:", rel)
            api.upload_file(path_or_fileobj=os.path.join(REPO, rel), path_in_repo=rel,
                            repo_id=repo_id, repo_type="space", token=token)

    # Space config README (sdk/app_port) — uploaded last so it isn't overwritten
    api.upload_file(
        path_or_fileobj=SPACE_README.encode(), path_in_repo="README.md",
        repo_id=repo_id, repo_type="space", token=token,
    )

    # runtime secrets
    sec = {
        "HUGGINGFACE_TOKEN": token,
        "MAPPLS_REST_KEY": read_env("MAPPLS_REST_KEY"),
        "MAPPLS_MAP_SDK_KEY": read_env("MAPPLS_MAP_SDK_KEY"),
        "JWT_SECRET": secrets.token_hex(24),
    }
    for k, v in sec.items():
        if v:
            api.add_space_secret(repo_id=repo_id, key=k, value=v, token=token)
    print("secrets set:", [k for k, v in sec.items() if v])

    try:
        rt = api.get_space_runtime(repo_id, token=token)
        print("build stage:", getattr(rt, "stage", "?"))
    except Exception:
        pass

    print("\nSPACE_URL: https://huggingface.co/spaces/" + repo_id)
    print("It will build for ~10-15 min. Watch logs at the URL above (App / Logs tab).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
