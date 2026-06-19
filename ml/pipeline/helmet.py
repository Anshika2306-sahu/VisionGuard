"""Helmet attribute model.

If a helmet model (`MODEL_HELMET`) is available it is used (treated as a small YOLO
detector with helmet / no-helmet classes run on the rider crop). Otherwise returns
('unknown', 0.0) so the violation engine simply won't raise a helmet violation —
the pipeline keeps working without it.
"""

from __future__ import annotations

import os
from typing import Protocol

import numpy as np

_NO_HELMET_HINTS = ("no_helmet", "no-helmet", "without", "nohelmet", "head")
_HELMET_HINTS = ("helmet", "with_helmet")


class HelmetModel(Protocol):
    def predict(self, rider_crop: np.ndarray) -> tuple[str, float]: ...


class YoloHelmetModel:
    def __init__(self, weights_path: str, conf: float = 0.25):
        from ultralytics import YOLO

        self.model = YOLO(weights_path)
        self.conf = conf
        self.names = {i: n.lower() for i, n in self.model.names.items()}

    def _classify(self, name: str) -> str | None:
        if any(h in name for h in _NO_HELMET_HINTS):  # check no-helmet first ('no-helmet' contains 'helmet')
            return "no_helmet"
        if "plate" in name or "number" in name:
            return "plate"
        if "motor" in name or "cycle" in name:
            return "motorcycle"
        if any(h in name for h in _HELMET_HINTS):
            return "helmet"
        return None

    def predict(self, rider_crop: np.ndarray) -> tuple[str, float]:
        if rider_crop is None or rider_crop.size == 0:
            return "unknown", 0.0
        res = self.model(rider_crop, conf=self.conf, verbose=False)[0]
        best_label, best_conf = "unknown", 0.0
        for box in res.boxes:
            label = self._classify(self.names.get(int(box.cls[0]), ""))
            if label not in ("helmet", "no_helmet"):
                continue
            conf = float(box.conf[0])
            if conf > best_conf or (label == "no_helmet" and best_label != "no_helmet"):
                best_label, best_conf = label, conf
        return best_label, best_conf

    def detect(self, image: np.ndarray) -> list[tuple[str, float, tuple[int, int, int, int]]]:
        """Full-frame detection -> [(label, conf, bbox)] for no_helmet/helmet/plate/motorcycle.
        Lets the engine raise helmet violations directly, independent of the vehicle detector."""
        if image is None or image.size == 0:
            return []
        res = self.model(image, conf=self.conf, verbose=False)[0]
        out = []
        for box in res.boxes:
            label = self._classify(self.names.get(int(box.cls[0]), ""))
            if label is None:
                continue
            xy = tuple(int(v) for v in box.xyxy[0].tolist())
            out.append((label, float(box.conf[0]), xy))
        return out


class StubHelmetModel:
    def predict(self, rider_crop: np.ndarray) -> tuple[str, float]:
        return "unknown", 0.0

    def detect(self, image: np.ndarray):
        return []


def load_helmet_model(weights_path: str | None = None) -> HelmetModel:
    if weights_path and os.path.exists(weights_path):
        try:
            return YoloHelmetModel(weights_path)
        except Exception:
            return StubHelmetModel()
    return StubHelmetModel()
