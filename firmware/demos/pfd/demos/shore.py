"""Shore: waves rolling onto a beach, seen from straight above, dithered.

After SeungHun's Midsummer Sea, from the air. Swells come in from the top, their
crests bending to follow the seabed, steepening and breaking into white as
they reach the shallows. Each breaker's water runs up the sand as a sheet
(the swash) with a lacy foam edge, slows, and slides back, leaving a dark
band of wet sand that dries slowly. Foam is a drifting noise texture that
rides with the water. Now and then a set of bigger waves arrives (click k0
to call one).
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

PERIOD = 6.5                    # seconds between waves


class Shore(Inked):
    name = "Shore"
    blurb = "Waves rolling onto a beach, seen from above, dithered (after SeungHun's Midsummer Sea). k0 swell, k1 tide, k2 screen, k3 inks. Click k0 a set of big waves, k2 chunky."
    palette, screen_kind = "beach", "blue"

    def __init__(self, rt):
        super().__init__(rt)
        rng = np.random.default_rng(31)
        self.grid = rng.random((40, 40)).astype(np.float32)
        self.swell, self.tide = 1.0, 0.0
        self.set_left = 0.0
        self.t = 0.0
        self.edge = np.full(N, 80.0, np.float32)        # where the swash has reached, per column
        self.wet = np.zeros((N, N), np.float32)
        self.vel = np.zeros(N, np.float32)
        self.last_wave = -1
        # the beach: the shoreline wanders, so waves refract and run up unevenly
        x = np.arange(N, dtype=np.float32)
        self.shore = (78 + 6 * np.sin(x * 0.04 + 1) + 3 * np.sin(x * 0.11)).astype(np.float32)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.swell = max(0.2, min(2.5, self.swell * 1.07 ** d))
        elif k == 1:
            self.tide = max(-15.0, min(15.0, self.tide + d * 0.5))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.set_left = 3.0
        elif k == 2:
            self.chunky()

    def _noise(self, u, v):
        g, n = self.grid, self.grid.shape[0]
        x0, y0 = np.floor(u), np.floor(v)
        fx, fy = u - x0, v - y0
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        x0, y0 = x0.astype(int) % n, y0.astype(int) % n
        x1, y1 = (x0 + 1) % n, (y0 + 1) % n
        return (g[y0, x0] * (1 - fx) + g[y0, x1] * fx) * (1 - fy) + (g[y1, x0] * (1 - fx) + g[y1, x1] * fx) * fy

    def step(self, dt):
        self.hear(dt)
        dt = min(dt, 1 / 20)
        self.t += dt * (1 + 0.5 * self.sound[2])
        wave = int(self.t / PERIOD)
        if wave != self.last_wave:                   # a breaker arrives: the swash surges up the sand
            self.last_wave = wave
            big = 1.6 if self.set_left > 0 else 1.0
            self.set_left -= 1
            self.vel[:] = (26 + 8 * np.sin(np.arange(N) * 0.07 + wave)) * self.swell * big
        if self.on_phrase:
            self.set_left = 3.0
        shore = self.shore + self.tide
        # the swash: driven up, slowed by friction and the slope, then it slides back to the shore
        self.vel -= (16 + 2 * np.maximum(self.edge - shore, 0)) * dt
        self.edge += self.vel * dt
        back = self.edge < shore
        self.edge[back] = shore[back]
        self.vel[back] = 0
        self.edge = np.minimum(self.edge, N + 4)
        # wherever the water is, the sand is wet; it dries slowly
        under = Y < self.edge[None, :]
        self.wet = np.where(under, 1.0, self.wet * math.exp(-dt / 9))

    def render(self):
        t = self.t
        shore = self.shore + self.tide
        depth = np.clip((shore[None, :] - Y) / 60, 0, 1)                 # 0 at the shore, 1 far out
        # crests: lines travelling towards the shore, bending to follow it
        phase = (Y - shore[None, :] * 0.6) / 22 - t / PERIOD * (78 / 22) * 0.6
        crest = np.cos(2 * math.pi * phase) * 0.5 + 0.5
        breaking = np.clip(1 - depth * 3, 0, 1)                           # near the shore, crests turn white
        water = 0.08 + 0.22 * (1 - depth) + 0.12 * crest ** 3 * (0.4 + self.swell * 0.6)
        foam_tex = self._noise(X * 0.22 + t * 0.4, Y * 0.22 - t * 1.5)
        foam = np.clip((crest ** 4) * breaking * 2.2 - foam_tex * 0.9, 0, 1)
        tone = water + foam * 0.7
        # the swash sheet and its lacy edge, up on the sand
        on_sand = Y >= shore[None, :]
        sheet = on_sand & (Y < self.edge[None, :])
        lace = np.abs(Y - self.edge[None, :]) < 1.6 + 1.5 * self._noise(X * 0.3, Y * 0.1 + t)
        sand = 0.667 - 0.17 * self.wet + 0.012 * self._noise(X * 0.6, Y * 0.6)     # dry sand sits right on its ink
        tone = np.where(on_sand, sand, tone)
        tone = np.where(sheet, 0.33 + 0.1 * foam_tex, tone)
        tone = np.where(on_sand & lace & (self.vel[None, :] > -6), 0.95, tone)
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.5, 0.2 + 0.25 * self.swell), self.glow(1, 0.12, 0.3 + 0.02 * self.tide)] + self.ink_lights()
