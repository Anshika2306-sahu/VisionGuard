"""Evidence annotation: draw detections + violations onto the frame and return JPEG bytes."""

from __future__ import annotations

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

_DET_COLOR = (0, 200, 0)        # green for detections
_FINABLE_COLOR = (0, 0, 255)    # red for finable violations
_ALERT_COLOR = (0, 165, 255)    # orange for safety alerts


def _put_label(img, text, x, y, color):
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(img, (x, y - th - 6), (x + tw + 4, y), color, -1)
    cv2.putText(img, text, (x + 2, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)


def annotate(image: np.ndarray, detections, violations) -> np.ndarray:
    """Return an annotated copy (BGR). `detections`/`violations` are lists of objects/dicts
    exposing `.cls`/`.bbox` and `.type`/`.severity`/`.bbox`/`.confidence`."""
    if cv2 is None:
        return image
    img = image.copy()

    for d in detections:
        cls = getattr(d, "cls", None) or (d.get("cls") if isinstance(d, dict) else "?")
        bbox = getattr(d, "bbox", None) or (d.get("bbox") if isinstance(d, dict) else None)
        if not bbox:
            continue
        x1, y1, x2, y2 = bbox
        cv2.rectangle(img, (x1, y1), (x2, y2), _DET_COLOR, 1)

    for v in violations:
        vtype = getattr(v, "type", None) or (v.get("type") if isinstance(v, dict) else "violation")
        sev = getattr(v, "severity", None) or (v.get("severity") if isinstance(v, dict) else "finable")
        conf = getattr(v, "confidence", None)
        if conf is None and isinstance(v, dict):
            conf = v.get("confidence")
        bbox = getattr(v, "bbox", None) or (v.get("bbox") if isinstance(v, dict) else None)
        color = _ALERT_COLOR if sev == "safety_alert" else _FINABLE_COLOR
        label = f"{vtype}" + (f" {conf:.2f}" if isinstance(conf, (int, float)) else "")
        if bbox:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            _put_label(img, label, x1, max(20, y1), color)
        else:
            _put_label(img, label, 10, 30, color)

    return img


def to_jpeg_bytes(image: np.ndarray, quality: int = 85) -> bytes:
    if cv2 is None:
        return b""
    ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes() if ok else b""
