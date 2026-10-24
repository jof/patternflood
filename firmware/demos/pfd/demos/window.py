"""Window: rain on the glass, a city's lights out of focus behind it, dithered.

After Lee's 0609, its soft blob seen through a screen. The city is bokeh:
discs of light, out of focus, some twinkling, all drifting very slowly as if
we're on a bus. On the glass, drops: a mist of tiny ones, and larger ones
that are lenses, each showing the city behind it small and upside down, with
a dark rim and a glint. When a large drop grows heavy enough it slides,
swallowing the small ones in its path and leaving a trail of droplets. The
wiper (click k0) clears the glass.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

NLIGHTS = 46
MAX_DROPS = 40


class Window(Inked):
    name = "Window"
    blurb = "Rain on the glass, a city's lights blurred behind it, dithered (after Lee's 0609). k0 rain, k1 focus, k2 screen, k3 inks. Click k0 wiper, k1 lightning, k2 chunky."
    palette, screen_kind = "night", "bayer8"

    def __init__(self, rt):
        super().__init__(rt)
        rng = self.rng = np.random.default_rng()
        self.lights_xy = np.column_stack([rng.uniform(-10, 138, NLIGHTS), rng.uniform(30, 125, NLIGHTS),
                                          rng.uniform(4, 12, NLIGHTS), rng.uniform(0.25, 1.0, NLIGHTS),
                                          rng.uniform(0, 6.28, NLIGHTS)]).astype(np.float32)
        self.rain, self.focus = 1.0, 1.0
        self.drops = np.zeros((0, 4), np.float32)       # x, y, r, vy
        self.mist = np.zeros((N, N), np.float32)        # the tiny droplets, as a coverage map
        self.wipe = -1.0                                # the wiper's angle, while it sweeps
        self.flash = 0.0
        self.t, self.pan = 0.0, 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.rain = max(0.0, min(3.0, self.rain + d * 0.1))
        elif k == 1:
            self.focus = max(0.4, min(2.0, self.focus * 1.05 ** d))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.wipe = 0.0
        elif k == 1:
            self.flash = 1.0
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        self.pan += dt * 2.0
        self.flash *= math.exp(-dt / 0.15)
        if self.on_phrase:
            self.flash = 1.0
        rng = self.rng
        # new drops land; the big ones are lenses, the rest join the mist
        n_new = rng.poisson(self.rain * (3 + 6 * self.sound[3]) * dt * 10)
        for _ in range(n_new):
            x, y = rng.uniform(0, N), rng.uniform(0, N)
            if rng.random() < 0.18 and len(self.drops) < MAX_DROPS:
                self.drops = np.vstack([self.drops, [x, y, rng.uniform(2.5, 4.5), 0.0]]).astype(np.float32)
            else:
                xi, yi = int(x), int(y)
                self.mist[max(0, yi - 1):yi + 1, max(0, xi - 1):xi + 1] = 1.0
        self.mist *= math.exp(-dt / 40)                 # it evaporates, slowly
        d = self.drops
        if len(d):
            d[:, 2] += dt * 0.15 * self.rain            # drops grow as the rain feeds them
            heavy = d[:, 2] > 4.2
            d[:, 3] = np.where(heavy, np.minimum(d[:, 3] + 60 * dt, 30 + 10 * d[:, 2]), 0)
            d[:, 1] += d[:, 3] * dt
            d[:, 0] += np.where(heavy, np.sin(self.t * 3 + d[:, 1] * 0.2) * 6 * dt, 0)
            for x, y, r, vy in d[heavy]:                # sliding: clear a path, leave droplets
                y0, y1 = max(0, int(y - r * 2)), min(N, int(y + r))
                x0, x1 = max(0, int(x - r)), min(N, int(x + r) + 1)
                self.mist[y0:y1, x0:x1] = 0
                if rng.random() < dt * 8:
                    self.mist[min(N - 1, max(0, int(y - r * 2.5))), min(N - 1, max(0, int(x)))] = 1.0
            d[heavy, 2] -= dt * 0.25                    # and they lose water as they go
            self.drops = d[(d[:, 1] < N + 10) & (d[:, 2] > 1.5)]
        if self.wipe >= 0:                              # the wiper sweeps an arc and clears it
            self.wipe += dt * 2.5
            a = math.pi * min(1.0, self.wipe)
            ang = np.arctan2(64 - Y, X - 64) % (2 * math.pi)
            swept = (ang <= a + 0.05) & (Y <= 64 + 10)
            self.mist[swept] = 0
            if len(self.drops):
                da = np.arctan2(64 - self.drops[:, 1], self.drops[:, 0] - 64) % (2 * math.pi)
                self.drops = self.drops[~((da <= a) & (self.drops[:, 1] <= 74))]
            if self.wipe >= 1.2:
                self.wipe = -1.0

    def city(self):
        """The blurred city, (N, N): each light a soft-edged disc, brighter at its rim."""
        tone = 0.03 + 0.1 * np.clip((Y - 20) / 100, 0, 1) + 0.5 * self.flash
        for lx, ly, r, b, ph in self.lights_xy:
            lx = (lx - self.pan) % 148 - 10
            rr = r * self.focus
            x0, x1 = max(0, int(lx - rr - 2)), min(N, int(lx + rr) + 3)
            y0, y1 = max(0, int(ly - rr - 2)), min(N, int(ly + rr) + 3)
            if x0 >= x1 or y0 >= y1:
                continue
            tw = b * (0.8 + 0.2 * math.sin(self.t * (1 + ph) + ph))
            dist = np.hypot(X[y0:y1, x0:x1] - lx, Y[y0:y1, x0:x1] - ly)
            tone[y0:y1, x0:x1] += tw * 0.7 * np.clip((rr - dist) / 1.5 + 0.5, 0, 1) * (0.7 + 0.3 * np.clip(dist / rr, 0, 1))
        return tone

    def render(self):
        city = self.city()
        tone = city.copy()
        # the mist scatters what's behind it a little
        tone = tone * (1 - 0.35 * self.mist) + 0.12 * self.mist
        for x, y, r, vy in self.drops:                  # each lens shows the city small, upside down
            x0, x1 = max(0, int(x - r - 1)), min(N, int(x + r) + 2)
            y0, y1 = max(0, int(y - r - 1)), min(N, int(y + r) + 2)
            if x0 >= x1 or y0 >= y1:
                continue
            px, py = X[y0:y1, x0:x1], Y[y0:y1, x0:x1]
            dx, dy = px - x, py - y
            dist = np.hypot(dx, dy)
            inside = dist < r
            sx = np.clip(np.rint(x - dx * 5), 0, N - 1).astype(np.int32)    # through the lens: flipped and shrunk
            sy = np.clip(np.rint(y - dy * 5), 0, N - 1).astype(np.int32)
            seen = city[sy, sx]
            rim = np.clip(1 - np.abs(dist - r + 0.5), 0, 1)
            patch = np.where(inside, seen * 0.9, tone[y0:y1, x0:x1])
            patch = patch * (1 - 0.7 * rim * (dist < r + 0.5))
            glint = (np.abs(dx + r * 0.4) < 0.8) & (np.abs(dy + r * 0.4) < 0.8)
            tone[y0:y1, x0:x1] = np.where(glint, 1.0, patch)
        if self.wipe >= 0:                              # the wiper blade itself
            a = math.pi * min(1.0, self.wipe)
            u = np.cos(a) * (X - 64) - np.sin(a) * (64 - Y)
            w = np.sin(a) * (X - 64) + np.cos(a) * (64 - Y)
            tone = np.where((np.abs(w) < 1.5) & (u > 0) & (u < 90), 0.0, tone)
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.58, 0.2 + 0.2 * self.rain), self.glow(1, 0.1, 0.2 + 0.2 * self.focus)] + self.ink_lights()
