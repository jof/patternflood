"""Galaxy: a spiral galaxy turning, its arms made of stars that flow through them.

After SeungHun's Chromatic Vortex. The arms are a density wave, as in real spirals:
every star rides its own closed orbit, slightly out of round, and the orbits'
shapes twist a little with radius. Where neighbouring orbits crowd together,
stars pile up, and the crowding makes the arms. The pattern turns slowly while
the stars sweep through it at their own (faster) speeds, so the arms persist
without winding up. Dust rides just inside each arm and dims what's behind it.
It's tilted in three dimensions, counted into a density map, and dithered.
"""
import math

import numpy as np

from ..draw import N
from .original import Inked

STARS = 40000
DUST = 9000
R_CORE = 0.05


class Galaxy(Inked):
    name = "Galaxy"
    blurb = "A spiral galaxy whose arms are a density wave, dithered (after SeungHun's Chromatic Vortex). k0 arm twist, k1 tilt, k2 screen, k3 inks. Click k0 arm count, k1 bar, k2 chunky."
    palette, screen_kind = "nebula", "blue"

    def __init__(self, rt):
        super().__init__(rt)
        rng = np.random.default_rng(12)
        a = rng.exponential(0.28, STARS * 2)
        self.a = (a[a < 0.95][:STARS] + 0.04).astype(np.float32)     # drawn again past the edge, not piled on it
        self.m0 = rng.uniform(0, 2 * math.pi, len(self.a)).astype(np.float32)
        self.z = (rng.normal(0, 0.025, len(self.a)) * (1 + 2 * np.exp(-self.a / 0.1))).astype(np.float32)
        self.da = (rng.uniform(0.15, 1.0, DUST)).astype(np.float32)
        self.dm0 = rng.uniform(0, 2 * math.pi, DUST).astype(np.float32)
        self.twist, self.tilt = 2.6, 0.55
        self.arms, self.bar = 2, False
        self.t, self.roll = 0.0, 0.0
        self.peak = None

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.twist = max(0.0, min(6.0, self.twist + d * 0.1))
        elif k == 1:
            self.tilt = max(0.0, min(1.45, self.tilt + d * 0.04))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.arms = self.arms % 4 + 1 if self.arms < 4 else 2
        elif k == 1:
            self.bar = not self.bar
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        self.t += dt * (1 + 1.5 * self.sound[0])
        self.roll += dt * 0.02
        if self.on_phrase:
            self.arms = self.arms % 4 + 1 if self.arms < 4 else 2

    def orbit(self, a, m0, lag=0.0):
        """Positions (x, y) on each orbit now: angle advancing at the orbit's own speed, radius
        swelling m times a turn, with the swell's phase twisting with radius (the arms)."""
        omega = 1.2 / (a + 0.12)                                # a flat rotation curve, roughly
        theta = m0 + omega * self.t * 0.25
        pattern = self.t * 0.08 + lag                           # the arms' own, slower turn
        phi = self.twist * np.log(a + 0.05) + pattern
        ecc = 0.16 if not self.bar else np.where(a < 0.3, 0.45, 0.16)
        r = a * (1 + ecc * np.cos(self.arms * (theta - phi)))
        if self.bar:                                            # a bar: inner orbits drawn out along one axis
            bar = np.exp(-(a / 0.22) ** 2)
            return r * np.cos(theta) * (1 + 0.8 * bar), r * np.sin(theta) * (1 - 0.5 * bar)
        return r * np.cos(theta), r * np.sin(theta)

    def project(self, x, y, z):
        """Tilt the disc away from us, turn it in the picture, to pixel coordinates."""
        ct, st = math.cos(self.tilt), math.sin(self.tilt)
        y, z = y * ct - z * st, y * st + z * ct
        cr, sr = math.cos(self.roll + 0.4), math.sin(self.roll + 0.4)
        x, y = x * cr - y * sr, x * sr + y * cr
        return x * 56 + 63.5, y * 56 + 63.5, z

    def density(self, px, py, w=None):
        ok = (px >= 0) & (px < N - 1) & (py >= 0) & (py < N - 1)
        cell = py[ok].astype(np.int32) * N + px[ok].astype(np.int32)
        return np.bincount(cell, weights=None if w is None else w[ok], minlength=N * N).reshape(N, N)

    def render(self):
        x, y = self.orbit(self.a, self.m0)
        px, py, _ = self.project(x, y, self.z)
        stars = _soften(_soften(self.density(px, py)))
        # dust trails the arms a little (it's compressed first), and dims what's behind it
        dx, dy = self.orbit(self.da, self.dm0, lag=-0.18)
        qx, qy, _ = self.project(dx, dy, np.zeros_like(dx))
        dust = self.density(qx, qy)
        dust = (dust + np.roll(dust, 1, 0) + np.roll(dust, -1, 0) + np.roll(dust, 1, 1) + np.roll(dust, -1, 1)) / 5
        # brightness set by the arms, not the core: the 90th percentile of what's lit
        top = float(np.percentile(stars[stars > 0.05], 90)) if (stars > 0.05).any() else 1.0
        self.peak = top if self.peak is None else self.peak + (top - self.peak) * 0.05
        tone = np.log1p(stars / self.peak * 3) / math.log1p(3) * 0.7
        # the bulge: a soft glow at the centre, flattened by the tilt
        cx, cy, _ = self.project(np.zeros(1), np.zeros(1), np.zeros(1))
        yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
        u, v = (xx - cx[0]) / 56, (yy - cy[0]) / 56
        bulge = np.exp(-(u * u + v * v / max(0.2, math.cos(self.tilt)) ** 2) / (2 * R_CORE ** 2))
        tone = tone * np.exp(-dust * 0.35) + 0.8 * bulge * (1 + 0.3 * self.beat)
        return self.print(np.clip(tone * (1 + 0.25 * self.sound[1]), 0, 1))

    def lights(self):
        return [self.glow(0, 0.75, 0.2 + 0.05 * self.twist), self.glow(1, 0.6, 0.2 + 0.3 * self.tilt)] + self.ink_lights()


def _soften(a):
    """A [1 2 1] blur each way: stars become a glow."""
    a = (np.roll(a, 1, 0) + 2 * a + np.roll(a, -1, 0)) / 4
    return (np.roll(a, 1, 1) + 2 * a + np.roll(a, -1, 1)) / 4
