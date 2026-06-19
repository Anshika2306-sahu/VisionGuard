"""Object detector wrapper.

`UltralyticsDetector` loads the UVH-26 (Bengaluru Safe City) YOLO weights if present,
otherwise transparently falls back to a COCO YOLO model (auto-downloaded) so the demo
never hard-fails. Any class implementing the `Detector` protocol can be swapped in
(e.g. a Triton-served model at scale) without touching the rest of the system.
"""

from __future__ import annotations

import glob
import os
from typing import Protocol

import numpy as np

from ml.configs.classes import CONF_FLOOR, normalize_model_name
from ml.pipeline.types import Detection

_COCO_FALLBACK = "yolo11n.pt"  # ultralytics auto-downloads on first use


class Detector(Protocol):
    def predict(self, image: np.ndarray) -> list[Detection]: ...


def resolve_weights(weights_path: str | None) -> tuple[str, bool]:
    """Return (path, using_fallback). If the exact path is missing, search recursively for
    any .pt under its directory (so whatever filename/structure HF ships still gets used);
    else COCO fallback."""
    if weights_path and os.path.exists(weights_path):
        return weights_path, False
    if weights_path:
        root = os.path.dirname(weights_path) or "."
        cands = sorted(glob.glob(os.path.join(root, "**", "*.pt"), recursive=True))
        # prefer small/nano variants for CPU
        cands.sort(key=lambda p: (0 if any(t in p.lower() for t in ("-s.pt", "s.pt", "n.pt", "small", "nano")) else 1))
        if cands:
            return cands[0], False
    return _COCO_FALLBACK, True


class UltralyticsDetector:
    def __init__(self, weights_path: str | None = None, conf: float = CONF_FLOOR):
        from ultralytics import YOLO  # imported lazily so importing this module is cheap

        path, self.using_fallback = resolve_weights(weights_path)
        self.model = YOLO(path)
        self.conf = conf
        self.names: dict[int, str] = dict(self.model.names)

    def predict(self, image: np.ndarray) -> list[Detection]:
        res = self.model(image, conf=self.conf, verbose=False)[0]
        dets: list[Detection] = []
        for box in res.boxes:
            cls_idx = int(box.cls[0])
            raw = self.names.get(cls_idx, str(cls_idx))
            canonical = normalize_model_name(raw)
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            dets.append(
                Detection(
                    cls=canonical,
                    conf=float(box.conf[0]),
                    bbox=(x1, y1, x2, y2),
                    attrs={"raw_cls": raw},
                )
            )
        return dets


class CompositeDetector:
    """Combine a vehicle detector (e.g. UVH-26, vehicles only) with an auxiliary COCO model
    that supplies the classes the primary lacks (notably `person`, needed for helmet /
    triple-riding / occupied-vehicle reasoning). Vehicles come from the primary to keep the
    Bengaluru-tuned accuracy; persons come from COCO."""

    def __init__(self, primary: UltralyticsDetector, aux: UltralyticsDetector, aux_classes: set[str]):
        self.primary = primary
        self.aux = aux
        self.aux_classes = aux_classes
        self.using_fallback = primary.using_fallback

    def predict(self, image: np.ndarray) -> list[Detection]:
        dets = self.primary.predict(image)
        for d in self.aux.predict(image):
            if d.cls in self.aux_classes:
                dets.append(d)
        return dets


def load_detector(weights_path: str | None = None, conf: float = CONF_FLOOR) -> Detector:
    """Factory used by the backend orchestrator.

    If the primary model has no `person` class (UVH-26/BMD-45 are vehicle-only), augment it
    with a COCO model so road users are still detected.
    """
    primary = UltralyticsDetector(weights_path=weights_path, conf=conf)
    has_person = any(normalize_model_name(n) == "person" for n in primary.names.values())
    if has_person or primary.using_fallback:
        return primary  # COCO already has person; nothing to augment
    aux = UltralyticsDetector(weights_path=None, conf=conf)  # COCO fallback
    return CompositeDetector(primary, aux, aux_classes={"person"})
