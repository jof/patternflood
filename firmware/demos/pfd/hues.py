"""Colour for the full-colour Patternflow originals: cosine-gradient palettes.

A palette is colour(t) = a + b * cos(2 pi (c t + d)), per channel (Inigo
Quilez's recipe): four vectors give a smooth, endlessly repeating gradient,
and sliding t (or d) cycles it. These are tuned bright and saturated, as the
panels and Lee's patterns like them.
"""
import math

import numpy as np

PRESETS = [
    ("rainbow", (0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (1.0, 1.0, 1.0), (0.0, 0.33, 0.67)),
    ("sunset", (0.85, 0.4, 0.45), (0.15, 0.35, 0.45), (1.0, 1.0, 1.0), (0.0, 0.6, 0.1)),
    ("candy", (0.6, 0.5, 0.6), (0.4, 0.45, 0.4), (1.0, 1.0, 1.0), (0.9, 0.55, 0.3)),
    ("lagoon", (0.35, 0.55, 0.6), (0.35, 0.45, 0.4), (1.0, 1.0, 1.0), (0.6, 0.25, 0.1)),
    ("acid", (0.5, 0.5, 0.4), (0.5, 0.5, 0.5), (2.0, 1.0, 0.0), (0.5, 0.2, 0.25)),
    ("ember", (0.75, 0.38, 0.15), (0.25, 0.32, 0.15), (1.0, 1.0, 1.0), (0.0, 0.1, 0.2)),
]


def cosine(t, preset=0, shift=0.0):
    """Colours for t (any shape), as (..., 3) floats 0..1."""
    _, a, b, c, d = PRESETS[preset % len(PRESETS)]
    t = np.asarray(t, np.float32)[..., None]
    a, b, c, d = (np.asarray(v, np.float32) for v in (a, b, c, d))
    return np.clip(a + b * np.cos(2 * math.pi * (c * t + d + shift)), 0, 1)
