"""Radar: a phosphor radar scope sweeping a coastline, rain and air traffic.

After Lee's 0614, its rings. The beam turns once every few seconds and paints
what it sees as it passes: a coastline and islands (fixed returns, with
speckle), rain cells that drift and change, and aircraft, each a bright blip
that moves a little between sweeps and leaves a trail of older echoes. The
phosphor glows where the beam has just been and fades over the turn, so
everything shows brightest just behind the sweep. Range rings and bearing
ticks are etched on the glass. Dithered into phosphor greens.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

R_SCOPE = 60.0
NPLANES = 7


class Radar(Inked):
    name = "Radar"
    blurb = "A phosphor radar scope: coastline, rain and aircraft, painted by the sweep (after Lee's 0614). k0 sweep speed, k1 range, k2 screen, k3 inks. Click k0 new traffic, k1 rain, k2 chunky."
    palette, screen_kind = "phosphor", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        rng = self.rng = np.random.default_rng(41)
        self.grid = rng.random((48, 48)).astype(np.float32)
        self.dx, self.dy = X - 63.5, Y - 63.5
        self.r = np.hypot(self.dx, self.dy)
        self.theta = np.arctan2(self.dy, self.dx) % (2 * math.pi)
        self.inside = self.r < R_SCOPE
        self.phos = np.zeros((N, N), np.float32)
        self.angle = 0.0
        self.rate, self.zoom = 1.6, 1.0
        self.rain = True
        self.planes = self._planes()
        self.t = 0.0

    def _planes(self):
        r = self.rng
        a = r.uniform(0, 2 * math.pi, NPLANES)
        d = r.uniform(10, 55, NPLANES)
        h = r.uniform(0, 2 * math.pi, NPLANES)
        return np.column_stack([np.cos(a) * d, np.sin(a) * d, np.cos(h) * r.uniform(2, 5, NPLANES),
                                np.sin(h) * r.uniform(2, 5, NPLANES)]).astype(np.float32)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.rate = max(0.3, min(6.0, self.rate * 1.08 ** d))
        elif k == 1:
            self.zoom = max(0.5, min(2.5, self.zoom * 1.05 ** d))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.planes = self._planes()
        elif k == 1:
            self.rain = not self.rain
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

    def returns(self, sel):
        """Echo strength at the selected pixels, in world units scaled by the range knob."""
        wx, wy = self.dx[sel] * self.zoom, self.dy[sel] * self.zoom
        land = self._noise(wx * 0.05 + 3, wy * 0.05 + 7) + 0.5 * self._noise(wx * 0.12, wy * 0.12)
        coast = np.clip((land - 0.95) * 6, 0, 1) * (0.55 + 0.45 * self.rng.random(len(wx)))
        echo = coast
        if self.rain:
            cells = self._noise(wx * 0.07 - self.t * 0.15, wy * 0.07 + self.t * 0.05 + 20)
            echo = np.maximum(echo, np.clip((cells - 0.62) * 3, 0, 1) * self.rng.random(len(wx)) * 0.8)
        for x, y, vx, vy in self.planes:
            d = np.hypot(wx - x, wy - y)
            echo = np.maximum(echo, np.where(d < 1.6 * self.zoom, 1.0, 0.0))
        return echo

    def step(self, dt):
        self.hear(dt)
        dt = min(dt, 1 / 20)
        self.t += dt
        self.planes[:, 0] += self.planes[:, 2] * dt
        self.planes[:, 1] += self.planes[:, 3] * dt
        far = np.hypot(self.planes[:, 0], self.planes[:, 1]) > 70
        if far.any():
            fresh = self._planes()
            self.planes[far] = fresh[far]
        if self.on_phrase:
            self.planes = self._planes()
        sweep = self.rate * dt * (1 + 0.5 * self.sound[0])
        a0 = self.angle
        self.angle = (self.angle + sweep) % (2 * math.pi)
        wedge = self.inside & (((self.theta - a0) % (2 * math.pi)) < sweep)
        self.phos *= math.exp(-dt * self.rate / 4.5)              # it fades over most of a turn
        if wedge.any():
            self.phos[wedge] = np.maximum(self.phos[wedge], self.returns(wedge))

    def render(self):
        tone = self.phos * 0.9
        # the beam, and a soft trailing glow behind it
        behind = (self.angle - self.theta) % (2 * math.pi)
        tone = np.maximum(tone, self.inside * (0.35 * np.exp(-behind / 0.35) + 0.6 * (behind < 0.04)) * (1 + 0.5 * self.beat))
        # the glass: range rings, bearing ticks, the bezel
        rings = np.zeros((N, N), bool)
        for rr in (15, 30, 45):
            rings |= (np.abs(self.r - rr) < 0.5) & ((self.theta * rr) % 3 < 1.2)
        ticks = (np.abs(((self.theta / (2 * math.pi) * 36) % 1) - 0.5) > 0.47) & (self.r > R_SCOPE - 4) & self.inside
        tone = np.maximum(tone, 0.28 * (rings | ticks))
        tone[np.abs(self.r - R_SCOPE - 1) < 1.2] = 0.4
        tone[self.r > R_SCOPE + 2.5] = 0.0
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.33, 0.2 + 0.1 * self.rate), self.glow(1, 0.33, 0.2 + 0.2 * self.zoom)] + self.ink_lights()
