"""Print-shop rendering for the Patternflow originals: threshold screens and inks.

A screen is a (128, 128) map of thresholds in [0, 1). Comparing a value field
against it turns tone into pattern. Ordered (Bayer), blue-noise and
interleaved-gradient screens dither; the halftone, line and cross-hatch screens print.
`dither` quantizes a tone field onto a palette of inks, stepping between
neighbouring inks so a 4-ink palette gives the PICO-8/Game Boy look.
"""
import math

import numpy as np

from .draw import N, X, Y

# Inks, darkest first, as 0..1 perceptual RGB. Black is the paper: on the panel, ink is light.
PALETTES = [
    ("obra", [(0, 0, 0), (0.18, 0.11, 0.05), (0.62, 0.42, 0.18), (1.0, 0.86, 0.6)]),
    ("riso", [(0, 0, 0), (0.0, 0.25, 0.55), (1.0, 0.28, 0.55), (1.0, 0.86, 0.3)]),
    ("gameboy", [(0.02, 0.06, 0.03), (0.12, 0.3, 0.12), (0.42, 0.66, 0.2), (0.8, 0.95, 0.45)]),
    ("synth", [(0, 0, 0), (0.22, 0.04, 0.45), (0.95, 0.15, 0.6), (0.2, 0.9, 1.0), (1, 1, 1)]),
    ("ember", [(0, 0, 0), (0.35, 0.02, 0.02), (0.95, 0.3, 0.02), (1.0, 0.8, 0.25), (1, 1, 0.9)]),
    ("ice", [(0, 0, 0), (0.02, 0.1, 0.3), (0.1, 0.5, 0.8), (0.75, 0.95, 1.0)]),
    ("pool", [(0, 0.02, 0.05), (0.0, 0.18, 0.3), (0.05, 0.55, 0.65), (0.8, 1.0, 1.0)]),
    ("dusk", [(0, 0, 0), (0.18, 0.04, 0.28), (0.75, 0.2, 0.4), (1.0, 0.6, 0.35), (1.0, 0.95, 0.75)]),
    ("nebula", [(0, 0, 0), (0.05, 0.05, 0.3), (0.45, 0.1, 0.6), (1.0, 0.35, 0.55), (1.0, 0.92, 0.8)]),
    ("night", [(0, 0, 0), (0.02, 0.06, 0.18), (0.1, 0.35, 0.5), (1.0, 0.62, 0.22), (1.0, 0.95, 0.85)]),
    ("aurora", [(0, 0, 0), (0.0, 0.14, 0.18), (0.05, 0.6, 0.35), (0.55, 1.0, 0.6), (0.98, 0.75, 1.0)]),
    ("koi", [(0, 0.02, 0.03), (0.03, 0.17, 0.2), (0.95, 0.38, 0.06), (1.0, 0.95, 0.86)]),
    ("silver", [(0, 0, 0), (0.1, 0.1, 0.12), (0.42, 0.42, 0.46), (1.0, 0.98, 0.92)]),
    ("mac", [(0, 0, 0), (1, 1, 1)]),
    ("hotpink", [(0, 0, 0), (1.0, 0.0, 0.6)]),
]


def palette_index(name):
    return next(i for i, (n, _) in enumerate(PALETTES) if n == name)


def bayer(n):
    """The n x n Bayer matrix (n a power of two), as thresholds in [0, 1)."""
    m = np.zeros((1, 1), np.float32)
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / m.size


def _tile(m, scale=1):
    s = m.shape[0]
    return m[(Y // scale).astype(int) % s, (X // scale).astype(int) % s].astype(np.float32)


def _rank(v):
    """Values to their rank, spread over [0, 1): any field becomes a uniform screen."""
    r = np.empty(v.size, np.float32)
    r[np.argsort(v, axis=None, kind="stable")] = (np.arange(v.size) + 0.5) / v.size
    return r.reshape(v.shape)


_blue = None


def blue_noise(size=64, sigma=1.6):
    """A tileable blue-noise threshold map by void filling: rank each pixel by when it's
    the emptiest place left. About 0.1 s, once."""
    global _blue
    if _blue is None or _blue.shape[0] != size:
        d = np.minimum(np.arange(size), size - np.arange(size))
        k = np.exp(-(d[:, None] ** 2 + d[None, :] ** 2) / (2 * sigma ** 2)).astype(np.float32)
        energy = np.random.default_rng(7).random((size, size)).astype(np.float32) * 1e-3
        rank = np.zeros((size, size), np.float32)
        for i in range(size * size):
            y, x = divmod(int(np.argmin(energy)), size)
            rank[y, x] = (i + 0.5) / (size * size)
            energy += np.roll(np.roll(k, y, 0), x, 1)
            energy[y, x] = np.inf
        _blue = rank
    return _blue


def screen(kind, scale=1, angle=0.0, pitch=6.0):
    """A threshold map. kind: bayer2 bayer4 bayer8 blue ign dots lines hatch."""
    if kind.startswith("bayer"):
        return _tile(bayer(int(kind[5:])), scale)
    if kind == "blue":
        return _tile(blue_noise(), scale)
    if kind == "ign":               # Jimenez's interleaved gradient noise
        x, y = X // scale, Y // scale
        return (52.9829189 * ((0.06711056 * x + 0.00583715 * y) % 1)) % 1
    c, s = math.cos(angle), math.sin(angle)
    u, v = (X * c + Y * s) / pitch, (-X * s + Y * c) / pitch
    if kind == "dots":
        d = np.hypot(u - np.floor(u) - 0.5, v - np.floor(v) - 0.5)
        return _rank(d + 1e-4 * _tile(bayer(8)))
    if kind == "lines":
        return _rank(np.abs(v - np.floor(v) - 0.5) + 1e-4 * _tile(bayer(8)))
    if kind == "hatch":             # an etcher's cross-hatching: line sets come in one by one as tone rises
        p = max(3, int(round(pitch)))       # pixel-exact diagonals and rows, so the lines stay crisp
        sets = []
        for i, w in enumerate(((X + Y) % p, (X - Y) % p, Y % p)):
            d = np.minimum(w, p - w) / (p / 2)              # 0 on a line, 1 midway between lines
            sets.append(0.06 + 0.27 * i + 0.3 * d)
        return np.minimum(np.minimum(sets[0], sets[1]), np.minimum(sets[2], 0.95)).astype(np.float32)
    raise ValueError(kind)


SCREENS = ["bayer8", "bayer4", "blue", "dots", "lines", "hatch", "bayer2", "ign"]


def dither(v, inks, thresh, scale=1):
    """Tone v (128, 128) in 0..1 onto inks (n, 3): each pixel gets one of the two inks its
    tone sits between, chosen by the screen. scale > 1 makes chunky pixels."""
    inks = np.asarray(inks, np.float32)
    if scale > 1:
        v = v[::scale, ::scale].repeat(scale, 0).repeat(scale, 1)[:N, :N]
    f = np.clip(v, 0, 1) * (len(inks) - 1)
    i = np.minimum(f.astype(np.int32) + (f % 1 > thresh), len(inks) - 1)
    return inks[i]


def palette_lerp(inks, v):
    """Smooth (undithered) lookup through the inks: for glows and previews."""
    inks = np.asarray(inks, np.float32)
    f = np.clip(v, 0, 1) * (len(inks) - 1)
    i = np.minimum(f.astype(np.int32), len(inks) - 2)
    a = (f - i)[..., None]
    return inks[i] * (1 - a) + inks[i + 1] * a
