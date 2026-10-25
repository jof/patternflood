"""Pixel Sort: a glowing landscape, melted by sorting runs of its pixels by brightness.

The glitch artist's trick, after SeungHun's 0519-2 RGB stripes and 0521 tear. Along
each column (or row), every run of pixels brighter than a threshold is sorted by
brightness, so light pours downhill in streaks while the dark parts stay sharp.
The threshold sweeps on its own (or with the music), and the picture under it
drifts, so the streaks grow, retract and shimmer.
"""
import math

import numpy as np

from .. import ink
from ..draw import N, X, Y
from .original import Original

DIRS = ["down", "right", "up", "left"]
SCENES = ["sunset", "aurora", "orbs"]


class PixelSort(Original):
    name = "Pixel Sort"
    blurb = "A landscape melted by sorting its bright runs (after SeungHun's 0519-2 and 0521 glitches). k0 threshold, k1 direction, k2 drift speed, k3 colours. Click k0 auto sweep, k1 next scene, k2 reverse sort."

    def __init__(self, rt):
        super().__init__(rt)
        self.thr, self.sweep = 0.45, True
        self.dir = 0
        self.speed = 1.0
        self.hue = 0.0
        self.scene = 0
        self.reverse = True
        self.t = 0.0
        rng = np.random.default_rng(5)
        self.jit = rng.random(N).astype(np.float32)            # per-line threshold jitter: ragged edges
        self.stars = rng.random((40, 3)).astype(np.float32)
        # runs also break at intervals along each line, which drift: the streaks crawl like drips
        self.span = rng.integers(10, 64, N).astype(np.float32)
        self.off = (rng.random(N) * 64).astype(np.float32)
        self.crawl = (0.4 + rng.random(N)).astype(np.float32)
        self.grain = rng.random((N, N)).astype(np.float32) - 0.5

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.thr = max(0.02, min(0.98, self.thr + d * 0.02))
            self.sweep = False
        elif k == 1:
            self.dir = (self.dir + (1 if d > 0 else -1)) % 4
        elif k == 2:
            self.speed = max(-4.0, min(4.0, self.speed + d * 0.1))
        elif k == 3:
            self.hue = (self.hue + d / 36) % 1.0

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.sweep = not self.sweep
        elif k == 1:
            self.scene = (self.scene + 1) % len(SCENES)
        elif k == 2:
            self.reverse = not self.reverse

    def step(self, dt):
        self.hear(dt)
        self.t += dt * self.speed * (1 + self.sound[1])
        self.off += self.crawl * dt * 12 * (1 + 2 * self.sound[0] + 3 * self.beat)
        if self.sweep:
            self.thr = 0.5 + 0.32 * math.sin(self.rt.t * 0.35) - 0.25 * self.beat - 0.2 * self.sound[2]
        if self.rt.t - min(self.t_touch) > 30 and int(self.rt.t / 30) != int((self.rt.t - dt) / 30):
            self.scene = (self.scene + 1) % len(SCENES)         # left alone, a new scene every half minute
            self.dir = (self.dir + 1) % 4 if self.scene == 0 else self.dir
        if self.on_phrase:
            self.scene = (self.scene + 1) % len(SCENES)
        if self.on_bar and self.rt.audio.bar_in_phrase % 4 == 0:
            self.dir = (self.dir + 2) % 4               # every fourth bar the melt flips over

    def picture(self):
        """The unsorted scene, (N, N, 3)."""
        t = self.t
        u, v = X / N, Y / N
        scene = SCENES[self.scene]
        if scene == "sunset":
            sky = ink.palette_lerp([(0.05, 0.0, 0.15), (0.45, 0.05, 0.45), (1.0, 0.3, 0.3), (1.0, 0.8, 0.35)],
                                   np.clip(v * 1.4 - 0.15 + 0.05 * np.sin(u * 9 + t * 0.4), 0, 1))
            sx, sy = 0.5 + 0.12 * math.sin(t * 0.13), 0.55
            sun = (np.hypot(u - sx, v - sy) < 0.17) & ((v < sy) | (np.sin(v * 70 - t) > -0.2))
            img = np.where(sun[..., None], np.array([1.0, 0.95, 0.6], np.float32), sky)
            hills = 0.72 + 0.06 * np.sin(u * 7 + t * 0.3) + 0.04 * np.sin(u * 17 - t * 0.5)
            img[v > hills] *= 0.08
        elif scene == "aurora":
            img = np.zeros((N, N, 3), np.float32)
            for i, c in enumerate(((0.1, 1.0, 0.5), (0.2, 0.5, 1.0), (0.9, 0.2, 1.0))):
                y0 = 0.3 + 0.12 * i + 0.08 * np.sin(u * (4 + i) + t * (0.5 + 0.2 * i) + i)
                band = np.exp(-((v - y0) / (0.05 + 0.03 * np.sin(u * 13 + t + i))) ** 2)
                img += band[..., None] * np.asarray(c, np.float32) * (0.6 + 0.4 * np.sin(u * 23 - t * 1.3 + i))[..., None]
            for x, y, b in self.stars:
                xi, yi = int(x * N), int(y * N * 0.6)
                img[yi, xi] += 0.4 + 0.6 * b
        else:                                   # orbs: glowing balls drifting over a dim floor of light
            img = ink.palette_lerp([(0.02, 0, 0.08), (0.12, 0.02, 0.3), (0.45, 0.1, 0.45)], v)
            for i, (x, y, b) in enumerate(self.stars[:7]):
                cx = 0.5 + 0.38 * math.sin(t * (0.21 + 0.1 * b) + 6 * x)
                cy = 0.5 + 0.38 * math.cos(t * (0.17 + 0.08 * x) + 6 * y)
                g = np.clip(1 - np.hypot(u - cx, v - cy) / (0.2 + 0.14 * b), 0, 1) ** 1.2
                col = np.asarray(ink.PALETTES[3][1][1 + i % 4], np.float32)
                img = np.maximum(img, g[..., None] * col)
        img = img * (1 + 0.18 * self.grain[..., None])
        if self.hue:
            img = _hue_rotate(img, self.hue)
        return np.clip(img, 0, 1)

    def render(self):
        img = self.picture()
        d = DIRS[self.dir]
        # bring the sort direction to "along rows, left to right", sort, and turn back
        k = {"right": 0, "down": 1, "left": 2, "up": 3}[d]
        a = np.rot90(img, k)
        lum = a @ np.array([0.3, 0.55, 0.15], np.float32)
        thr = np.clip(self.thr + 0.06 * (self.jit[:, None] - 0.5), 0, 1)
        inrun = lum > thr
        # a new group starts at every pixel outside a run, at each row's start, and at the drifting
        # breaks; the pixel that opens a group keys lowest and stays put
        j = np.arange(N, dtype=np.float32)[None, :]
        brk = ((j + self.off[:, None]) % self.span[:, None]) < 1
        inrun &= ~brk
        start = ~inrun
        start[:, 0] = True
        group = np.cumsum(start.ravel())
        key = np.where(inrun, -lum if self.reverse else lum, -2.0).ravel()
        order = np.lexsort((key, group))
        out = a.reshape(-1, 3)[order].reshape(a.shape)
        return np.ascontiguousarray(np.rot90(out, -k))

    def lights(self):
        return [self.glow(0, 0.1, 0.3 + 0.5 * self.thr), self.glow(1, self.dir / 4),
                self.glow(2, 0.6), self.glow(3, self.hue)]


def _hue_rotate(img, h):
    """Rotate hues by h turns (a rotation about the grey axis)."""
    a = 2 * math.pi * h
    c, s = math.cos(a), math.sin(a)
    k = 1 / 3
    q = math.sqrt(k)
    m = np.array([[c + (1 - c) * k, k * (1 - c) - q * s, k * (1 - c) + q * s],
                  [k * (1 - c) + q * s, c + (1 - c) * k, k * (1 - c) - q * s],
                  [k * (1 - c) - q * s, k * (1 - c) + q * s, c + (1 - c) * k]], np.float32)
    return img @ m.T
