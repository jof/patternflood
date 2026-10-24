"""Falling sand in a box you tilt with a knob.

Gravity can point any way: each step falls along one of the two nearest
cardinal directions, picked at random in proportion, so the pile flows at the
angle you set. Turning k0 clockwise turns the box clockwise, so gravity swings
the other way round the screen.
"""
import math

import numpy as np

from .. import draw
from ..draw import N, hsv, hsv1
from ..runtime import Demo

WALL = 255
ROT = [0, -1, 2, 1]         # np.rot90 k that makes gravity down/right/up/left point down the rows
LAYOUTS = ["empty", "pegs", "funnel", "shelves"]


def _palette():
    v = np.arange(256)
    hue = ((v - 1) // 4) / 63.0
    shade = 0.62 + 0.12 * ((v - 1) % 4)
    pal = hsv(hue, np.full(256, 0.9), shade).astype(np.float32)
    pal[0] = 0
    pal[WALL] = (0.22, 0.22, 0.26)
    return pal


PAL = _palette()


class Sand(Demo):
    name = "Sand"
    blurb = "k0 tilts the box. k1 moves the spout, hold k1 to pour. k2 colour, click for rainbow. Hold k3 to drain; click k3 for obstacles. Click k0 to shake."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.theta = 0.0                 # gravity angle, 0 = down the screen, + = towards the right
        self.spout = 0.5
        self.hue = 0.08
        self.width = 3.0
        self.rainbow = False
        self.layout = 0
        self.shake = 0.0
        self.t_tilt = -10.0
        self.grid = np.zeros((N, N), np.uint8)
        self._build()
        # start with a heap of sand so the first tilt does something
        y, x = np.mgrid[0:N, 0:N]
        heap = (y > 96 + 10 * np.cos((x - 64) / 20.0)) & (self.grid == 0)
        self.grid[heap] = 1 + ((((x[heap] // 16) * 9) % 63) * 4 + self.rng.integers(0, 4, heap.sum())).astype(np.uint8)

    def _build(self):
        g = self.grid
        g[g == WALL] = 0
        name = LAYOUTS[self.layout]
        y, x = np.mgrid[0:N, 0:N]
        if name == "pegs":
            for cy in (40, 64, 88):
                for cx in range(16 if cy == 64 else 28, N, 24):
                    g[(x - cx) ** 2 + (y - cy) ** 2 <= 5] = WALL
        elif name == "funnel":
            g[(np.abs(np.abs(x - 63.5) - (y - 30) * 0.9) < 1.2) & (y > 30) & (y < 80) & (np.abs(x - 63.5) > 4)] = WALL
        elif name == "shelves":
            for i, cy in enumerate((36, 60, 84, 108)):
                x0 = 8 if i % 2 == 0 else 48
                g[cy:cy + 2, x0:x0 + 72] = WALL

    def turn(self, k, d):
        if k == 0:
            self.theta = (self.theta + d * math.pi / 16) % (2 * math.pi)
            self.t_tilt = self.rt.t
        elif k == 1:
            self.spout = min(1.0, max(0.0, self.spout + self.rt.accel(1, d) * 0.02))
        elif k == 2:
            self.hue = (self.hue + d / 48.0) % 1.0
        elif k == 3:
            self.width = min(10.0, max(1.0, self.width + d * 0.5))

    def release(self, k, click):
        if not click:
            return
        if k == 0:
            self.shake = 0.5
        elif k == 2:
            self.rainbow = not self.rainbow
        elif k == 3:
            self.layout = (self.layout + 1) % len(LAYOUTS)
            self._build()

    def _gvec(self):
        return math.sin(self.theta), math.cos(self.theta)

    def _spout_xy(self):
        gx, gy = self._gvec()
        # the spout rides the wall opposite gravity; k1 slides it along that wall
        px, py = -gy, gx
        cx, cy = 63.5 - gx * 58, 63.5 - gy * 58
        s = (self.spout - 0.5) * 110
        return min(N - 3.0, max(2.0, cx + px * s)), min(N - 3.0, max(2.0, cy + py * s))

    def _pour(self, dt):
        x, y = self._spout_xy()
        r = self.width / 2
        n = int(self.rng.poisson(self.width * 80 * dt)) + 1
        xs = np.rint(x + self.rng.uniform(-r, r, n)).astype(int).clip(0, N - 1)
        ys = np.rint(y + self.rng.uniform(-1.5, 1.5, n)).astype(int).clip(0, N - 1)
        empty = self.grid[ys, xs] == 0
        if self.rainbow:
            self.hue = (self.hue + dt * 0.15) % 1.0
        h6 = int(self.hue * 63) % 63
        self.grid[ys[empty], xs[empty]] = (1 + h6 * 4 + self.rng.integers(0, 4, empty.sum())).astype(np.uint8)

    def _fall(self, rot, drain):
        v = np.rot90(self.grid, ROT[rot]).copy()
        occ = v > 0
        mob = occ & (v != WALL)
        # straight down
        mv = mob[:-1] & ~occ[1:]
        v[1:][mv] = v[:-1][mv]
        v[:-1][mv] = 0
        # then slide off the side of whatever is underneath, one side at a time
        sides = (1, -1) if self.rng.random() < 0.5 else (-1, 1)
        for side in sides:
            occ = v > 0
            mob = occ & (v != WALL)
            rnd = self.rng.random((N - 1, N - 1)) < 0.6
            if side == 1:
                mv = mob[:-1, :-1] & occ[1:, :-1] & ~occ[1:, 1:] & ~occ[:-1, 1:] & rnd
                v[1:, 1:][mv] = v[:-1, :-1][mv]
                v[:-1, :-1][mv] = 0
            else:
                mv = mob[:-1, 1:] & occ[1:, 1:] & ~occ[1:, :-1] & ~occ[:-1, :-1] & rnd
                v[1:, :-1][mv] = v[:-1, 1:][mv]
                v[:-1, 1:][mv] = 0
        if drain:
            v[-1][v[-1] != WALL] = 0
        self.grid[:] = np.rot90(v, -ROT[rot])

    def step(self, dt):
        steps = max(1, min(12, int(round(150 * dt))))
        q = self.theta / (math.pi / 2)
        base, frac = int(math.floor(q)) % 4, q - math.floor(q)
        for _ in range(steps):
            if self.rt.held(1):
                self._pour(dt / steps)
            if self.shake > 0:
                rot = int(self.rng.integers(0, 4))
            else:
                rot = (base + 1) % 4 if self.rng.random() < frac else base
            self._fall(rot, self.rt.held(3) and rot == round(q) % 4)
        self.shake = max(0.0, self.shake - dt)

    def render(self):
        img = PAL[self.grid].copy()
        gx, gy = self._gvec()
        # where "down" is: a soft glow on that stretch of wall, bright just after a tilt
        a = 0.12 + 0.6 * max(0.0, 1 - (self.rt.t - self.t_tilt) / 1.0)
        ex, ey = 63.5 + gx * 90, 63.5 + gy * 90
        d = np.hypot(draw.X - ex, draw.Y - ey)
        edge = (draw.X < 1) | (draw.X > N - 2) | (draw.Y < 1) | (draw.Y > N - 2)
        glow = np.clip(1 - (d - 25) / 30, 0, 1) * edge * a
        drain = self.rt.held(3)
        img += glow[..., None] * (np.array((1, .15, .1)) if drain else np.array((.4, .5, .7)))
        # the spout
        sx, sy = self._spout_xy()
        c = hsv1(self.hue)
        draw.disc(img, sx, sy, self.width / 2 + 0.6, c if self.rt.held(1) else tuple(v * 0.35 for v in c), soft=0.5)
        return img

    def lights(self):
        gx, gy = self._gvec()
        c = hsv1(self.hue)
        return [(0.3 + 0.3 * gx, 0.3, 0.3 + 0.3 * gy) if self.shake <= 0 else (1, 1, 1),
                c if self.rt.held(1) else tuple(v * 0.25 for v in c),
                hsv1(self.rt.t * 0.4) if self.rainbow else c,
                (1, 0.1, 0.05) if self.rt.held(3) else (0.2, 0.2, 0.25)]
