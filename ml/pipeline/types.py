"""Shared dataclasses for the CV pipeline (kept dependency-free)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


BBox = tuple[int, int, int, int]  # x1, y1, x2, y2


@dataclass
class Detection:
    cls: str                       # canonical class (see ml/configs/classes.py)
    conf: float
    bbox: BBox
    attrs: dict = field(default_factory=dict)  # helmet, riders, plate_text, etc.

    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def area(self) -> float:
        x1, y1, x2, y2 = self.bbox
        return max(0, x2 - x1) * max(0, y2 - y1)


@dataclass
class PlateResult:
    text: str
    conf: float
    bbox: Optional[BBox] = None


def iou(a: BBox, b: BBox) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    if inter == 0:
        return 0.0
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return inter / float(area_a + area_b - inter)


def contains_point(box: BBox, pt: tuple[float, float], pad: float = 0.0) -> bool:
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    px, py = pt
    return (x1 - pad * w) <= px <= (x2 + pad * w) and (y1 - pad * h) <= py <= (y2 + pad * h)
