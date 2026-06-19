"""ANPR: plate detection + OCR.

Strategy: if a plate bbox is supplied (from the detector's 'plate' class or a dedicated
plate model) we OCR that crop; otherwise we OCR the lower region of a vehicle crop as a
fallback. OCR engine is EasyOCR by default (lazy-loaded, cached). Output is normalized to
the Indian plate format; unreadable plates return text 'UNREADABLE' (mirrors MLFF's
"unidentified vehicle" flag) instead of failing.
"""

from __future__ import annotations

import os
import re

import numpy as np

from ml.pipeline.types import BBox, PlateResult

# KA01AB1234 / KA1A1234 etc. Loose Indian plate pattern after cleanup.
_PLATE_RE = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{1,4}$")
_CLEAN_RE = re.compile(r"[^A-Z0-9]")

_OCR_ENGINE = os.getenv("OCR_ENGINE", "easyocr").lower()
_reader = None  # cached OCR reader


def _get_reader():
    global _reader
    if _reader is not None:
        return _reader
    try:
        if _OCR_ENGINE == "paddleocr":
            from paddleocr import PaddleOCR

            _reader = ("paddle", PaddleOCR(use_angle_cls=True, lang="en", show_log=False))
        else:
            import easyocr

            _reader = ("easy", easyocr.Reader(["en"], gpu=False))
    except Exception:
        _reader = ("none", None)
    return _reader


def normalize_plate(text: str) -> str:
    cleaned = _CLEAN_RE.sub("", text.upper())
    return cleaned


def _ocr(crop: np.ndarray) -> tuple[str, float]:
    engine, reader = _get_reader()
    if reader is None or crop is None or crop.size == 0:
        return "", 0.0
    try:
        if engine == "easy":
            results = reader.readtext(crop)
            if not results:
                return "", 0.0
            # join tokens, weight by confidence
            text = "".join(r[1] for r in results)
            conf = float(np.mean([r[2] for r in results]))
            return normalize_plate(text), conf
        if engine == "paddle":
            results = reader.ocr(crop, cls=True)
            if not results or not results[0]:
                return "", 0.0
            line = results[0]
            text = "".join(item[1][0] for item in line)
            conf = float(np.mean([item[1][1] for item in line]))
            return normalize_plate(text), conf
    except Exception:
        return "", 0.0
    return "", 0.0


def read_plate(image: np.ndarray, plate_bbox: BBox | None = None) -> PlateResult:
    """OCR a plate. `image` may be a full frame (with plate_bbox) or a vehicle crop."""
    crop = image
    if plate_bbox is not None:
        x1, y1, x2, y2 = plate_bbox
        crop = image[max(0, y1):y2, max(0, x1):x2]

    text, conf = _ocr(crop)

    # Fallback: if a vehicle crop was passed without a plate box, try the lower 40%.
    if (not text) and plate_bbox is None and image is not None and image.size:
        h = image.shape[0]
        text, conf = _ocr(image[int(h * 0.6):, :])

    if not text or not _PLATE_RE.match(text):
        # keep partial text as a hint but flag unreadable
        return PlateResult(text=text or "UNREADABLE", conf=conf, bbox=plate_bbox)
    return PlateResult(text=text, conf=conf, bbox=plate_bbox)
