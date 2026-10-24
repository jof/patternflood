"""Bonfire: flames over a pile of logs, sparks going up into the dark, dithered.

After Lee's Firefly Hollow. The flame is a teardrop of heat over the logs,
eaten away by fractal noise that streams upward faster than the flame
itself, so the tongues lick, split and break off at the top; wind leans
the tips. (Doom's row-by-row fire, tried first, smeared into horizontal
streaks at this size.) Over that: sparks, each a mote of light that rises,
wavers and dims, the logs as dark shapes, and the glow the fire throws on
the ground. All of it through a dither screen.
"""
import math

import numpy as np

from .. import draw
from ..draw import N, X, Y
from .original import Inked

BED_Y = 106                     # where the flames start, among the logs
GROUND = 112
NSPARKS = 70


class Bonfire(Inked):
    name = "Bonfire"
    blurb = "Flames over logs, sparks rising into the dark, dithered (after Lee's Firefly Hollow). k0 fire size, k1 wind, k2 screen, k3 inks. Click k0 stoke, k1 calm, k2 chunky."
    palette, screen_kind = "ember", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.grid = self.rng.random((48, 48)).astype(np.float32)
        self.size, self.wind = 1.0, 0.0
        self.t = 0.0
        self.stoke = 0.0
        self.sparks = np.zeros((NSPARKS, 5), np.float32)          # x, y, vx, vy, life
        self.logs = self._logs()

    def _logs(self):
        """Log silhouettes (a mask), and where the embers sit along them."""
        m = np.zeros((N, N), bool)
        for x0, y0, x1, y1, r in ((34, 116, 94, 104, 4.5), (36, 103, 92, 116, 4.5), (50, 110, 80, 110, 4.0)):
            px, py = draw.segment(x0, y0, x1, y1, 1.0)
            for x, y in zip(px, py):
                m |= (X - x) ** 2 + (Y - y) ** 2 < r * r
        return m

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.size = max(0.3, min(1.8, self.size + d * 0.05))
        elif k == 1:
            self.wind = max(-1.5, min(1.5, self.wind + d * 0.06))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.stoked()
        elif k == 1:
            self.wind = 0.0
        elif k == 2:
            self.chunky()

    def stoked(self):
        self.stoke = 1.0
        dead = np.flatnonzero(self.sparks[:, 4] <= 0)[:25]
        self._spawn(dead, burst=True)

    def _spawn(self, idx, burst=False):
        n = len(idx)
        if not n:
            return
        r = self.rng
        self.sparks[idx, 0] = r.uniform(44, 84, n)
        self.sparks[idx, 1] = r.uniform(80, 104, n)
        self.sparks[idx, 2] = r.normal(0, 6 if burst else 3, n)
        self.sparks[idx, 3] = -r.uniform(25, 60 if burst else 40, n)
        self.sparks[idx, 4] = r.uniform(0.8, 2.2, n)

    def _noise(self, u, v):
        """Smooth value noise from a tiled random grid, about 0..1."""
        g = self.grid
        n = g.shape[0]
        x0, y0 = np.floor(u), np.floor(v)
        fx, fy = u - x0, v - y0
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        x0, y0 = x0.astype(np.int64) % n, y0.astype(np.int64) % n
        x1, y1 = (x0 + 1) % n, (y0 + 1) % n
        return (g[y0, x0] * (1 - fx) + g[y0, x1] * fx) * (1 - fy) + (g[y1, x0] * (1 - fx) + g[y1, x1] * fx) * fy

    def flame(self):
        """Heat 0..1 over the whole frame."""
        t = self.t
        height = 70 * self.size * (1 + 0.25 * self.stoke + 0.3 * self.sound[2])
        rise = np.clip((BED_Y - Y) / height, 0, None)                  # 0 at the bed, 1 at the flame's top
        lean = self.wind * 30 * rise ** 2
        dx = X - 64 - lean
        width = 30 * (1 - 0.6 * np.clip(rise, 0, 1)) + 2
        shape = np.exp(-(dx / width) ** 2) * np.clip(1 - rise, 0, 1) ** 0.6
        shape[Y > BED_Y + 2] = 0
        n = np.zeros((N, N), np.float32)
        amp, f = 0.5, 0.06
        for o in range(4):                  # each octave finer and faster, all streaming upward
            n += amp * self._noise(dx * f + o * 7.1, (Y + t * (45 + 25 * o)) * f * 1.4)
            amp, f = amp * 0.5, f * 2
        n /= 0.9375
        return np.clip(1.35 * shape - n * (0.5 + 1.0 * rise), 0, 1) * 1.15

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        self.stoke *= math.exp(-dt / 0.6)
        if self.on_beat and self.rt.audio.kick > 0.5:
            self._spawn(np.flatnonzero(self.sparks[:, 4] <= 0)[:6], burst=True)
        if self.on_phrase:
            self.stoked()
        s = self.sparks
        s[:, 2] += (self.wind * 30 - s[:, 2]) * dt + self.rng.normal(0, 40, NSPARKS) * dt
        s[:, 0] += s[:, 2] * dt
        s[:, 1] += s[:, 3] * dt
        s[:, 3] *= math.exp(-dt / 2.5)
        s[:, 4] -= dt
        dead = np.flatnonzero(s[:, 4] <= 0)
        if len(dead) and self.rng.random() < dt * 8 * self.size:
            self._spawn(dead[:1])

    def render(self):
        heat = self.flame()
        tone = heat ** 1.1
        # the ground catches the glow: brightest under the fire, fading outwards
        glow = 0.6 + 0.3 * self.stoke + 0.1 * math.sin(self.t * 9) * math.sin(self.t * 5.3)
        ground = (Y >= GROUND) * np.exp(-((X - 64) / 40) ** 2) * np.exp(-(Y - GROUND) / 10) * glow
        tone = np.maximum(tone, ground * 0.6)
        tone[self.logs] = 0.04 + 0.35 * np.clip(heat[self.logs] - 0.5, 0, 1)    # logs dark, embers showing through
        live = self.sparks[:, 4] > 0
        sx, sy = self.sparks[live, 0].astype(int), self.sparks[live, 1].astype(int)
        ok = (sx >= 0) & (sx < N) & (sy >= 0) & (sy < N)
        tone[sy[ok], sx[ok]] = np.maximum(tone[sy[ok], sx[ok]], np.clip(self.sparks[live, 4][ok], 0.4, 1))
        return self.print(tone)

    def lights(self):
        return [self.glow(0, 0.06, 0.2 + 0.4 * self.size), self.glow(1, 0.55, 0.2 + 0.3 * abs(self.wind))] + self.ink_lights()
