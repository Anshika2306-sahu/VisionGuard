"""Violation Reasoning Engine — pure functions: (detections + ROI + context) -> violations.

This is intentionally free of any web/DB dependency so it can be unit-tested in isolation
(the most important test surface in the project). The backend wraps it, supplying ROI from
the DB and persisting the results.

Design notes:
- Detectors produce *facts* (boxes, classes, attrs). This engine produces *violations*
  (explainable, each with a `rationale`).
- Geometry violations (stop_line, red_light, wrong_side, illegal_parking) need per-camera ROI.
  Without ROI, only attribute violations (helmet, triple-riding) + safety alerts are produced.
- False-positive controls applied last: occupied-vehicle heuristic, confidence gating,
  quality gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ml.configs.classes import (
    CONF_THRESHOLDS,
    FINABLE,
    JAM_VEHICLE_COUNT,
    QUALITY_FLOOR,
    TWO_WHEELER_LIKE,
    VEHICLE_CLASSES,
    VIOLATION_TYPES,
)
from ml.pipeline.types import BBox, Detection, contains_point, iou


@dataclass
class Violation:
    type: str
    severity: str
    confidence: float
    bbox: BBox | None
    status: str                       # auto_issued | needs_review | alert
    rationale: dict = field(default_factory=dict)
    plate_text: str | None = None


# ----------------------------- geometry helpers --------------------------------------
def _denorm_point(pt, w: int, h: int) -> tuple[float, float]:
    return (pt[0] * w, pt[1] * h)


def _point_in_polygon(pt, poly) -> bool:
    """Ray-casting. poly = list of (x,y) in pixel coords."""
    x, y = pt
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def _ccw(a, b, c) -> bool:
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def _segments_intersect(a, b, c, d) -> bool:
    return _ccw(a, c, d) != _ccw(b, c, d) and _ccw(a, b, c) != _ccw(a, b, d)


def _segment_intersects_bbox(a, b, bbox: BBox) -> bool:
    """True if the line segment a-b passes through / touches the bbox rectangle."""
    x1, y1, x2, y2 = bbox
    # either endpoint inside the box?
    if (x1 <= a[0] <= x2 and y1 <= a[1] <= y2) or (x1 <= b[0] <= x2 and y1 <= b[1] <= y2):
        return True
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    edges = [
        (corners[0], corners[1]), (corners[1], corners[2]),
        (corners[2], corners[3]), (corners[3], corners[0]),
    ]
    return any(_segments_intersect(a, b, c, d) for c, d in edges)


# ----------------------------- per-rule logic ----------------------------------------
def _is_vehicle(d: Detection) -> bool:
    return d.cls in VEHICLE_CLASSES


def _rule_no_helmet(dets, results):
    for d in dets:
        # fires for a two-wheeler whose rider was classified no-helmet (association path),
        # or a direct 'rider' detection from the helmet detector (works even if the bike
        # itself was not detected by the CCTV-tuned vehicle model)
        if (d.cls in TWO_WHEELER_LIKE or d.cls == "rider") and d.attrs.get("helmet") == "no_helmet":
            hc = float(d.attrs.get("helmet_conf", 0.0))
            conf = round(0.5 * hc + 0.5 * d.conf, 4)
            results.append(Violation(
                type="no_helmet", severity="finable", confidence=conf, bbox=d.bbox,
                status="pending",
                rationale={"rule": "no_helmet", "helmet_conf": hc, "det_conf": d.conf},
                plate_text=d.attrs.get("plate_text"),
            ))


def _rule_triple_riding(dets, results):
    for d in dets:
        if d.cls in TWO_WHEELER_LIKE:
            riders = int(d.attrs.get("rider_count", 0))
            if riders >= 3:
                conf = round(min(1.0, 0.5 + 0.15 * (riders - 2)) * d.conf, 4)
                results.append(Violation(
                    type="triple_riding", severity="finable", confidence=conf, bbox=d.bbox,
                    status="pending",
                    rationale={"rule": "triple_riding", "rider_count": riders, "det_conf": d.conf},
                    plate_text=d.attrs.get("plate_text"),
                ))


def _rule_illegal_parking(dets, roi, w, h, mode, results):
    polys = [r for r in roi.get("no_parking", [])]
    if not polys:
        return
    persons = [d for d in dets if d.cls == "person"]
    for d in dets:
        if not _is_vehicle(d):
            continue
        center = d.center()
        in_zone = any(
            _point_in_polygon(center, [_denorm_point(p, w, h) for p in poly])
            for poly in polys
        )
        if not in_zone:
            continue
        # occupied-vehicle heuristic: suppress if a person overlaps / is near the vehicle
        occupied = any(iou(d.bbox, p.bbox) > 0.02 or contains_point(d.bbox, p.center(), pad=0.25)
                       for p in persons)
        if occupied:
            continue
        # in image mode we cannot measure dwell; lower confidence accordingly
        base = 0.6 if mode == "image" else 0.8
        conf = round(base * d.conf, 4)
        results.append(Violation(
            type="illegal_parking", severity="finable", confidence=conf, bbox=d.bbox,
            status="pending",
            rationale={"rule": "illegal_parking", "mode": mode, "occupied": False, "det_conf": d.conf},
            plate_text=d.attrs.get("plate_text"),
        ))


def _rule_stop_line(dets, roi, w, h, results, signal_state=None):
    lines = roi.get("stop_line", [])
    if not lines:
        return
    for line in lines:
        if len(line) < 2:
            continue
        a = _denorm_point(line[0], w, h)
        b = _denorm_point(line[1], w, h)
        for d in dets:
            if not _is_vehicle(d):
                continue
            # crossing test: the stop-line segment passes through the vehicle bbox
            # (vehicle is sitting on / has moved onto the line)
            crossed = _segment_intersects_bbox(a, b, d.bbox)
            if not crossed:
                continue
            # red_light if signal is red, else plain stop_line
            if signal_state == "red":
                results.append(Violation(
                    type="red_light", severity="finable",
                    confidence=round(0.85 * d.conf, 4), bbox=d.bbox, status="pending",
                    rationale={"rule": "red_light", "signal": "red", "det_conf": d.conf},
                    plate_text=d.attrs.get("plate_text"),
                ))
            else:
                results.append(Violation(
                    type="stop_line", severity="finable",
                    confidence=round(0.7 * d.conf, 4), bbox=d.bbox, status="pending",
                    rationale={"rule": "stop_line", "signal": signal_state, "det_conf": d.conf},
                    plate_text=d.attrs.get("plate_text"),
                ))


def _rule_wrong_side(dets, roi, results, headings=None):
    """headings: optional {det_index: (dx, dy)} from clip motion. Image mode -> skipped."""
    lane_dirs = roi.get("lane_dir", [])  # list of {"dir": [dx,dy]} (allowed direction)
    if not lane_dirs or not headings:
        return
    allowed = lane_dirs[0].get("dir", [0, -1])
    for i, d in enumerate(dets):
        if not _is_vehicle(d) or i not in headings:
            continue
        dx, dy = headings[i]
        dot = dx * allowed[0] + dy * allowed[1]
        if dot < 0:  # moving opposite to allowed direction
            results.append(Violation(
                type="wrong_side", severity="finable",
                confidence=round(0.7 * d.conf, 4), bbox=d.bbox, status="pending",
                rationale={"rule": "wrong_side", "dot": round(dot, 3), "det_conf": d.conf},
                plate_text=d.attrs.get("plate_text"),
            ))


def _alert_traffic_jam(dets, roi, results):
    threshold = roi.get("jam_threshold", JAM_VEHICLE_COUNT)
    vehicles = [d for d in dets if _is_vehicle(d)]
    if len(vehicles) >= threshold:
        sev_conf = round(min(1.0, len(vehicles) / (threshold * 2.0)), 4)
        results.append(Violation(
            type="traffic_jam", severity="safety_alert", confidence=sev_conf, bbox=None,
            status="alert",
            rationale={"rule": "traffic_jam", "vehicle_count": len(vehicles), "threshold": threshold},
        ))


def _alert_accident(dets, results):
    """Conservative heuristic: two vehicles with very high overlap AND a person on the road
    very close to them -> possible accident. Requiring the person sharply reduces false
    positives from ordinary dense-traffic occlusion (overlapping boxes are normal in jams)."""
    vehicles = [d for d in dets if _is_vehicle(d)]
    persons = [d for d in dets if d.cls == "person"]
    for i in range(len(vehicles)):
        for j in range(i + 1, len(vehicles)):
            ov = iou(vehicles[i].bbox, vehicles[j].bbox)
            if ov <= 0.70:
                continue
            # a person must be genuinely overlapping the collision region (on the road, fallen)
            near_person = any(iou(vehicles[i].bbox, p.bbox) > 0.12 for p in persons)
            if not near_person:
                continue
            results.append(Violation(
                type="accident", severity="safety_alert", confidence=round(0.6, 4),
                bbox=vehicles[i].bbox, status="alert",
                rationale={"rule": "accident_heuristic", "overlap": round(ov, 3),
                           "person_near": True},
            ))
            return  # one accident flag per frame is enough


# ----------------------------- public entrypoint -------------------------------------
def evaluate(
    detections: list[Detection],
    image_size: tuple[int, int],
    roi: dict | None = None,
    quality: float = 1.0,
    mode: str = "image",
    signal_state: str | None = None,
    headings: dict | None = None,
) -> list[Violation]:
    """Run all rules and apply false-positive controls.

    image_size = (width, height). roi = per-camera config dict. quality = 0..1.
    """
    roi = roi or {}
    w, h = image_size
    results: list[Violation] = []

    # attribute rules (work without ROI)
    _rule_no_helmet(detections, results)
    _rule_triple_riding(detections, results)

    # geometry rules (need ROI)
    _rule_illegal_parking(detections, roi, w, h, mode, results)
    _rule_stop_line(detections, roi, w, h, results, signal_state=signal_state)
    _rule_wrong_side(detections, roi, results, headings=headings)

    # safety alerts (zero fine)
    _alert_traffic_jam(detections, roi, results)
    _alert_accident(detections, results)

    # ---- false-positive controls ----
    final: list[Violation] = []
    for v in results:
        # quality gate: poor image -> drop finable, keep safety alerts
        if v.severity == "finable" and quality < QUALITY_FLOOR:
            continue
        # confidence gating
        if v.severity == "finable":
            thr = CONF_THRESHOLDS.get(v.type, 0.5)
            v.status = "auto_issued" if v.confidence >= thr else "needs_review"
        else:
            v.status = "alert"
        final.append(v)
    return final
