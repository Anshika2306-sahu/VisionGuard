"""Image preprocessing: enhancement + quality scoring.

Handles low light (CLAHE), light denoise, and computes a 0..1 quality score from
sharpness + brightness so the violation engine can refuse to fine on unusable frames.
"""

from __future__ import annotations

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


def _laplacian_sharpness(gray: np.ndarray) -> float:
    """Variance of Laplacian, normalized to ~0..1 (higher = sharper)."""
    if cv2 is None:
        return 0.5
    lap = cv2.Laplacian(gray, cv2.CV_64F).var()
    # ~0 (blurry) .. >500 (sharp). Squash to 0..1.
    return float(min(1.0, lap / 300.0))


def _brightness_score(gray: np.ndarray) -> float:
    """Closeness of mean brightness to an ideal mid-range (0..1)."""
    mean = float(gray.mean()) / 255.0
    # ideal around 0.5; penalize very dark / very bright
    return float(max(0.0, 1.0 - abs(mean - 0.5) * 2.0))


def quality_score(image: np.ndarray) -> float:
    if cv2 is None:
        return 0.6
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sharp = _laplacian_sharpness(gray)
    bright = _brightness_score(gray)
    return float(round(0.6 * sharp + 0.4 * bright, 4))


def enhance(image: np.ndarray) -> tuple[np.ndarray, float]:
    """Return (clean_image, quality_score in 0..1).

    Applies CLAHE on the L channel for low-light/low-contrast frames. Designed to be
    cheap (CPU-friendly) for the prototype.
    """
    if cv2 is None:
        return image, 0.6

    out = image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean = float(gray.mean())

    # Low-light / low-contrast -> CLAHE on L channel
    if mean < 110 or gray.std() < 45:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        l = clahe.apply(l)
        out = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

    score = quality_score(out)
    return out, score
