"""Canonical classes, violation taxonomy, fine schedule and thresholds.

Single source of truth shared by the ML pipeline and the backend violation engine.
Vehicle taxonomy follows the UVH-26 / BMD-45 (IISc, Bengaluru Safe City) 14-class scheme,
collapsed to coarse parents that are practical for enforcement.
"""

from __future__ import annotations

# --- Canonical detection classes -------------------------------------------------
VEHICLE_CLASSES = [
    "bicycle",
    "two_wheeler",        # motorbike / scooter
    "auto_rickshaw",      # three-wheeler
    "car",                # hatchback / sedan / SUV / MUV
    "bus",                # bus / mini-bus
    "van",
    "commercial_vehicle", # LCV / tempo-traveller
    "truck",
    "other",
]
ROAD_USER_CLASSES = ["person", "plate"]
ALL_CLASSES = VEHICLE_CLASSES + ROAD_USER_CLASSES

# Two-wheeler-like classes used by rider/helmet/triple-riding logic
TWO_WHEELER_LIKE = {"two_wheeler", "bicycle"}

# --- Maps from raw model class names -> canonical --------------------------------
# COCO (yolo*.pt fallback) names:
COCO_TO_CANONICAL = {
    "person": "person",
    "bicycle": "bicycle",
    "motorcycle": "two_wheeler",
    "motorbike": "two_wheeler",
    "car": "car",
    "bus": "bus",
    "truck": "truck",
    "van": "van",
    "auto rickshaw": "auto_rickshaw",
}

# UVH-26 / BMD-45 style names (lowercased, punctuation stripped) -> canonical.
# We match loosely (substring) at load time, but list explicit hints here.
UVH_HINTS = {
    "bicycle": "bicycle",
    "two": "two_wheeler",          # "two-wheeler", "two wheeler"
    "motorbike": "two_wheeler",
    "motorcycle": "two_wheeler",
    "three": "auto_rickshaw",      # "three-wheeler"
    "auto": "auto_rickshaw",
    "rickshaw": "auto_rickshaw",
    "car": "car",
    "hatchback": "car",
    "sedan": "car",
    "suv": "car",
    "muv": "car",
    "bus": "bus",
    "mini": "bus",
    "van": "van",
    "lcv": "commercial_vehicle",
    "commercial": "commercial_vehicle",
    "tempo": "commercial_vehicle",
    "truck": "truck",
    "person": "person",
    "rider": "person",
    "pedestrian": "person",
    "plate": "plate",
    "number": "plate",
    "licence": "plate",
    "license": "plate",
}

# --- Violation taxonomy + Indian fine schedule (INR, tunable) --------------------
VIOLATION_TYPES = {
    "no_helmet":       {"severity": "finable", "fine": 1000, "label": "No Helmet"},
    "seatbelt":        {"severity": "finable", "fine": 1000, "label": "No Seatbelt"},
    "triple_riding":   {"severity": "finable", "fine": 1000, "label": "Triple Riding"},
    "wrong_side":      {"severity": "finable", "fine": 5000, "label": "Wrong-Side Driving"},
    "stop_line":       {"severity": "finable", "fine": 1000, "label": "Stop-Line Violation"},
    "red_light":       {"severity": "finable", "fine": 2000, "label": "Red-Light Violation"},
    "illegal_parking": {"severity": "finable", "fine": 500,  "label": "Illegal Parking"},
    "accident":        {"severity": "safety_alert", "fine": 0, "label": "Accident Alert"},
    "traffic_jam":     {"severity": "safety_alert", "fine": 0, "label": "Traffic Jam / Overcrowding"},
}

FINABLE = {k for k, v in VIOLATION_TYPES.items() if v["severity"] == "finable"}
SAFETY_ALERTS = {k for k, v in VIOLATION_TYPES.items() if v["severity"] == "safety_alert"}

# Per-violation confidence threshold: below -> needs_review (no auto challan).
CONF_THRESHOLDS = {
    "no_helmet": 0.55,
    "triple_riding": 0.60,
    "illegal_parking": 0.65,
    "stop_line": 0.60,
    "red_light": 0.70,
    "wrong_side": 0.70,
    "seatbelt": 0.65,
}

# Global floors
CONF_FLOOR = 0.25       # detector minimum confidence
QUALITY_FLOOR = 0.30    # below this image quality -> no finable violations (alerts ok)
JAM_VEHICLE_COUNT = 12  # default per-frame density for a jam alert (per-camera calibratable)


def normalize_model_name(raw: str) -> str:
    """Map a raw model class name to a canonical class. Falls back to 'other'."""
    key = raw.strip().lower()
    if key in COCO_TO_CANONICAL:
        return COCO_TO_CANONICAL[key]
    if key in ALL_CLASSES:
        return key
    for hint, canon in UVH_HINTS.items():
        if hint in key:
            return canon
    return "other"
