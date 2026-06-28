"""End-to-end single-image pipeline runner.

Chains: enhance -> detect -> (rider association + helmet) -> violation engine ->
ANPR on violators -> annotate. Used by both the backend orchestrator and the CLI smoke test.
ANPR is run only on finable-violation crops (efficient, and mirrors enforcement: we only
need the plate of an actual violator).
"""

from __future__ import annotations

from dataclasses import asdict

import numpy as np

from ml.pipeline import violation_engine as ve
from ml.pipeline.annotate import annotate, to_jpeg_bytes
from ml.pipeline.anpr import read_plate
from ml.pipeline.detector import Detector
from ml.pipeline.helmet import HelmetModel, StubHelmetModel
from ml.pipeline.preprocess import enhance
from ml.pipeline.types import Detection, contains_point
from ml.configs.classes import TWO_WHEELER_LIKE, VEHICLE_CLASSES


def _best_plate_for(vbox, plate_boxes):
    """Pick the plate box whose center lies inside the violation bbox (highest conf wins)."""
    vx1, vy1, vx2, vy2 = vbox
    best = None
    best_conf = -1.0
    for conf, (px1, py1, px2, py2) in plate_boxes:
        cx, cy = (px1 + px2) / 2.0, (py1 + py2) / 2.0
        if vx1 <= cx <= vx2 and vy1 <= cy <= vy2 and conf > best_conf:
            best, best_conf = (px1, py1, px2, py2), conf
    return best


def _associate_riders_and_helmet(clean, dets: list[Detection], helmet: HelmetModel):
    persons = [d for d in dets if d.cls == "person"]
    for bike in dets:
        if bike.cls not in TWO_WHEELER_LIKE:
            continue
        x1, y1, x2, y2 = bike.bbox
        bw, bh = x2 - x1, y2 - y1
        # riders: persons whose centroid sits over/above the bike footprint
        riders = []
        for p in persons:
            pcx, pcy = p.center()
            in_x = (x1 - 0.3 * bw) <= pcx <= (x2 + 0.3 * bw)
            in_y = (y1 - 1.2 * bh) <= pcy <= (y2 + 0.2 * bh)
            if in_x and in_y:
                riders.append(p)
        bike.attrs["rider_count"] = len(riders)
        if riders:
            top = min(riders, key=lambda p: p.bbox[1])  # head of the topmost rider
            rx1, ry1, rx2, ry2 = top.bbox
            crop = clean[max(0, ry1):ry2, max(0, rx1):rx2]
            label, conf = helmet.predict(crop)
            bike.attrs["helmet"] = label
            bike.attrs["helmet_conf"] = conf


def analyze(
    image: np.ndarray,
    detector: Detector,
    helmet: HelmetModel | None = None,
    roi: dict | None = None,
    mode: str = "image",
    signal_state: str | None = None,
    run_anpr: bool = True,
) -> dict:
    helmet = helmet or StubHelmetModel()
    clean, quality = enhance(image)
    h, w = clean.shape[:2]

    dets = detector.predict(clean)
    _associate_riders_and_helmet(clean, dets, helmet)

    # direct helmet-detector pass: extracting plate boxes.
    # We no longer blindly append 'helmet'/'no_helmet' boxes as 'rider' detections,
    # as this was causing pedestrians to be falsely fined. Helmet violations will now
    # exclusively rely on the strict motorcycle association logic above.
    plate_boxes: list = []
    for label, conf, box in (helmet.detect(clean) if hasattr(helmet, "detect") else []):
        if label == "plate":
            plate_boxes.append((conf, box))

    violations = ve.evaluate(
        dets, image_size=(w, h), roi=roi, quality=quality,
        mode=mode, signal_state=signal_state,
    )

    # ANPR on finable violators: prefer an overlapping detected plate box, else OCR the crop.
    if run_anpr:
        for v in violations:
            if v.severity != "finable" or not v.bbox:
                continue
            pbox = _best_plate_for(v.bbox, plate_boxes)
            if pbox is not None:
                plate = read_plate(clean, plate_bbox=pbox)
            else:
                bx1, by1, bx2, by2 = v.bbox
                plate = read_plate(clean[max(0, by1):by2, max(0, bx1):bx2])
            v.plate_text = plate.text
            v.rationale["plate_conf"] = round(plate.conf, 3)

    annotated = annotate(clean, dets, violations)
    return {
        "quality": quality,
        "image_size": (w, h),
        "detections": [
            {"cls": d.cls, "conf": round(d.conf, 4), "bbox": list(d.bbox), "attrs": d.attrs}
            for d in dets
        ],
        "violations": [
            {
                "type": v.type, "severity": v.severity, "confidence": v.confidence,
                "bbox": list(v.bbox) if v.bbox else None, "status": v.status,
                "plate_text": v.plate_text, "rationale": v.rationale,
            }
            for v in violations
        ],
        "annotated_jpeg": to_jpeg_bytes(annotated),
    }
