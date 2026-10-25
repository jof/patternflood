"""Strange: a Clifford attractor, drawn by a cloud of points, that the knobs bend.

    x' = sin(a y) + c cos(a x)
    y' = sin(b x) + d cos(b y)

A cloud of points is stepped through the map every frame and each landing is
counted, so the picture is the attractor's density, glowing and coloured by the
direction each point jumped. The counts fade quickly, so when a knob moves a, b,
c or d the shape visibly bends into its next form instead of smearing.
After SeungHun's flow-field and Lissajous patterns; here the field is chaos.
"""
import math

import numpy as np

from ..draw import N
from .original import Original

PRESETS = [(-1.4, 1.6, 1.0, 0.7), (1.7, 1.7, 0.6, 1.2), (-1.7, 1.3, -0.1, -1.2), (1.5, -1.8, 1.6, 0.9),
           (-1.8, -2.0, -0.5, -0.9), (-1.24, -1.25, -1.81, -1.91), (1.5, -1.8, 1.6, 2.0),
           (2.01, -2.53, 1.61, -0.33), (-1.9, -1.9, -1.9, -1.0)]
POINTS = 30000
ITERS = 4
# colour by direction of jump: one ink for leftward jumps, the other for rightward
INKS = [((0.1, 0.85, 1.0), (1.0, 0.15, 0.6)), ((1.0, 0.45, 0.05), (0.55, 0.1, 1.0)),
        ((0.2, 1.0, 0.45), (0.1, 0.35, 1.0)), ((1.0, 0.85, 0.2), (1.0, 0.1, 0.15))]
FADE_S = 0.35


class Strange(Original):
    name = "Strange"
    blurb = "A Clifford attractor's glow, which the knobs bend: k0..k3 are its a, b, c, d. Click k0 next form, k1 colours, k2 freeze the drift, k3 long glow."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.p = self.rng.uniform(-1, 1, (POINTS, 2)).astype(np.float32)
        self.preset = 0
        self.base = np.array(PRESETS[0], np.float32)
        self.target = self.base.copy()
        self.nudge = np.zeros(4, np.float32)
        self.drift = True
        self.long = False
        self.hue_i = 0
        self.fade, self.pending = 1.0, None
        self.kick = 0.0
        self.h = np.zeros((N, N, 2), np.float32)
        self.view = np.array([0.0, 0.0, 2.6, 2.6], np.float32)      # centre x, y and half-sizes
        self.peak = None
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        self.nudge[k] += self.rt.accel(k, d) * 0.01

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.next_form()
        elif k == 1:
            self.hue_i = (self.hue_i + 1) % len(INKS)
        elif k == 2:
            self.drift = not self.drift
        elif k == 3:
            self.long = not self.long

    def next_form(self):
        """Fade out, jump, fade in: gliding between forms passes through dull periodic orbits."""
        self.preset = (self.preset + 1) % len(PRESETS)
        self.pending = np.array(PRESETS[self.preset], np.float32)

    def params(self):
        t = self.t
        wob = 0.06 * np.array([math.sin(t * 0.13), math.sin(t * 0.11 + 1), math.sin(t * 0.07 + 2),
                               math.sin(t * 0.09 + 3)], np.float32) if self.drift else 0
        s = np.array(self.sound, np.float32)
        return self.base + self.nudge + wob + (0.12 * s[[2, 0, 3, 1]] + self.kick) * np.array([1, -1, 1, -1], np.float32)

    def step(self, dt):
        self.hear(dt)
        if self.drift:
            self.t += dt
        if self.drift and min(self.rt.t - tt for tt in self.t_touch) > 40 and \
                int(self.rt.t / 40) != int((self.rt.t - dt) / 40):
            self.next_form()                    # left alone, a new form every 40 s
        if self.pending is not None:
            self.fade -= dt / FADE_S
            if self.fade <= 0:
                self.base = self.target = self.pending
                self.pending, self.nudge[:] = None, 0
                self.p = self.rng.uniform(-1, 1, (POINTS, 2)).astype(np.float32)
                self._iterate(*self.params(), burn=24)
                self.h[:] = 0
                self.peak = None
                self._frame(1.0)
        else:
            self.fade = min(1.0, self.fade + dt / FADE_S)
        if self.on_phrase:
            self.next_form()
        if self.on_beat:                        # each beat kicks the parameters; they ease back
            self.kick = 0.08 + 0.06 * self.sound[2]
        self.kick *= math.exp(-dt / 0.12)
        self.base += (self.target - self.base) * (1 - math.exp(-dt / 2.0))
        hist = self._iterate(*self.params())
        # a few points are reborn each frame next to others, so the cloud never thins to a cycle
        n = POINTS // 50
        self.p[self.rng.integers(0, POINTS, n)] = self.p[self.rng.integers(0, POINTS, n)] \
            + self.rng.normal(0, 0.01, (n, 2)).astype(np.float32)
        keep = math.exp(-dt / (1.2 if self.long else 0.12))
        self.h = self.h * keep + hist * (1 - keep)
        self._frame(1 - math.exp(-dt / 0.8))

    def _frame(self, k):
        """Frame the cloud as it is (square, with a margin), from a sample of its points."""
        q = self.p[::16]
        lo, hi = np.percentile(q, 0.5, axis=0), np.percentile(q, 99.5, axis=0)
        half = float(max(hi - lo)) * 0.55 + 0.05
        want = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, half, half], np.float32)
        self.view += (want - self.view) * k

    def _iterate(self, a, b, c, d, burn=0):
        """Step every point through the map ITERS times (after `burn` uncounted steps); returns
        the landings counted per pixel, split by the jump's direction."""
        a, b, c, d = float(a), float(b), float(c), float(d)
        x, y = self.p[:, 0], self.p[:, 1]
        for _ in range(burn):
            x, y = np.sin(a * y) + c * np.cos(a * x), np.sin(b * x) + d * np.cos(b * y)
        hist = np.zeros((N * N, 2), np.float32)
        cx, cy, sx, sy = self.view
        for _ in range(ITERS):
            nx = np.sin(a * y) + c * np.cos(a * x)
            ny = np.sin(b * x) + d * np.cos(b * y)
            right = nx > x
            x, y = nx, ny
            px = ((x - cx) / sx * 0.5 + 0.5) * (N - 1)
            py = ((y - cy) / sy * 0.5 + 0.5) * (N - 1)
            ok = (px >= 0) & (px < N - 0.5) & (py >= 0) & (py < N - 0.5)
            cell = np.rint(py[ok]).astype(np.int32) * N + np.rint(px[ok]).astype(np.int32)
            hist[:, 0] += np.bincount(cell, weights=right[ok], minlength=N * N)
            hist[:, 1] += np.bincount(cell, minlength=N * N)
        self.p = np.stack([x, y], -1)
        hist[:, 1] -= hist[:, 0]
        return hist.reshape(N, N, 2)

    def render(self):
        total = self.h.sum(-1)
        top = float(np.percentile(total[total > 0], 99.5)) if (total > 0).any() else 1.0
        self.peak = top if self.peak is None else self.peak + (top - self.peak) * 0.1
        v = np.log1p(total * (6 / max(self.peak, 1e-6))) / math.log1p(6)
        mix = (self.h[..., 0] / (total + 1e-9))[..., None]
        a, b = (np.asarray(c, np.float32) for c in INKS[self.hue_i])
        col = a * mix + b * (1 - mix)
        col = col + (1 - col) * (v ** 3)[..., None] * 0.7          # the densest threads burn white
        return np.clip(col * v[..., None] * self.fade * (1 + 0.7 * self.beat), 0, 1)

    def lights(self):
        a, b = INKS[self.hue_i]
        return [tuple(0.6 * x for x in (a if k % 2 else b)) for k in range(4)]
