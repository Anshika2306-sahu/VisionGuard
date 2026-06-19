"""Storage abstraction. LocalFS now; the same interface backs MinIO/S3 at scale
(swap the class, nothing else changes)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from app.core.config import settings


class StorageBackend(Protocol):
    def save(self, key: str, data: bytes) -> str: ...
    def load(self, key: str) -> bytes: ...
    def url(self, key: str) -> str: ...


class LocalFSStorage:
    def __init__(self, base_dir: str):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = self.base / key
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def save(self, key: str, data: bytes) -> str:
        with open(self._path(key), "wb") as f:
            f.write(data)
        return key

    def load(self, key: str) -> bytes:
        with open(self._path(key), "rb") as f:
            return f.read()

    def url(self, key: str) -> str:
        # served by the API at /evidence/{key}
        return f"/evidence/{key}"


def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND == "s3":  # pragma: no cover - scale path
        raise NotImplementedError("S3 backend is the scale upgrade; implement S3Storage here.")
    return LocalFSStorage(settings.STORAGE_DIR)


storage = get_storage()
