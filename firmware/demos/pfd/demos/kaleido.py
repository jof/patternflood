"""A kaleidoscope you twist: k0 turns the barrel, and the beads inside tumble.

After SeungHun's mirror-fold patterns (0522 quad-fold, 0526 kaleidoscopic vortex,
0622 mirror grid). Here the source isn't a formula. It is a cell of beads
under gravity, and turning k0 turns the cell, so they fall and roll as in the
real toy. The mirrors stay put.
"""
import math
import random

import numpy as np

from .. import draw
from ..draw import N, hsv
from ..runtime import DETENTS_PER_REV, Demo

S = 64                      # the object cell, rendered at S x S
NBEADS = 48


class Kaleido(Demo):
    name = "Kaleido"
    blurb = "After SeungHun's mirror folds. Twist k0 like the barrel and the beads tumble. k1 zoom, k2 mirrors, k3 colours. Click k0 shake, k2 new beads, k3 oil."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.barrel = 0.0
        self.zoom = 1.0
        self.folds = 6
        self.hue = 0.0
        self.oil = False
        self.beads()
        self._map()

    def beads(self):
        r = self.rng
        self.p = np.array([[r.uniform(-.6, .6), r.uniform(-.6, .6)] for _ in range(NBEADS)], np.float32)
        self.v = np.zeros_like(self.p)
        self.size = np.array([r.choice((0.06, 0.08, 0.1, 0.13)) for _ in range(NBEADS)], np.float32)
        self.bh = np.array([r.random() for _ in range(NBEADS)], np.float32)
        self.shape = [r.choice(("disc", "ring", "shard")) for _ in range(NBEADS)]

    def _map(self):
        """Screen pixel -> radius and angle within one mirrored wedge (depends on zoom and folds)."""
        dx, dy = draw.X - 63.5, draw.Y - 63.5
        self.r = np.hypot(dx, dy) / 64.0 / self.zoom
        wedge = math.pi / self.folds
        self.a = np.abs((np.arctan2(dy, dx) % (2 * wedge)) - wedge) - wedge / 2
        self.outside = self.r > 1.0

    def _look(self):
        """The mirrors are fixed in the world and the cell turns inside them, so the wedge
        always looks where gravity pulls the beads: world-down, in the cell's frame."""
        a = self.a + math.pi / 2 + self.barrel
        sx = 0.5 + 0.5 * self.r * np.cos(a)
        sy = 0.5 + 0.5 * self.r * np.sin(a)
        return (np.clip((sy * (S - 1)).astype(np.int32), 0, S - 1),
                np.clip((sx * (S - 1)).astype(np.int32), 0, S - 1))

    def turn(self, k, d):
        if k == 0:
            self.barrel += d * 2 * math.pi / DETENTS_PER_REV
        elif k == 1:
            self.zoom = min(2.5, max(0.4, self.zoom * 1.08 ** d))
            self._map()
        elif k == 2:
            self.folds = min(12, max(2, self.folds + (1 if d > 0 else -1)))
            self._map()
        elif k == 3:
            self.hue = (self.hue + d / 48.0) % 1.0

    def release(self, k, click):
        if not click:
            return
        if k == 0:
            self.v += np.array([[self.rng.uniform(-3, 3), self.rng.uniform(-3, 3)] for _ in range(NBEADS)], np.float32)
        elif k == 2:
            self.beads()
        elif k == 3:
            self.oil = not self.oil

    def step(self, dt):
        # gravity in the cell's frame: the cell turns with the barrel
        g = 3.0 * np.array([math.sin(-self.barrel), math.cos(-self.barrel)], np.float32)
        drag = 4.0 if self.oil else 0.6
        for _ in range(3):
            h = dt / 3
            self.v += g * h
            # beads push each other apart
            d = self.p[:, None, :] - self.p[None, :, :]
            dist = np.sqrt((d ** 2).sum(-1)) + 1e-6
            minsep = (self.size[:, None] + self.size[None, :]) * 0.8
            push = np.clip(minsep - dist, 0, None) / dist
            np.fill_diagonal(push, 0)
            self.v += (d * push[..., None]).sum(1) * 40 * h
            self.v *= math.exp(-drag * h)
            self.p += self.v * h
            # the cell's round wall
            r = np.sqrt((self.p ** 2).sum(-1))
            lim = 0.95 - self.size
            out = r > lim
            if out.any():
                n = self.p[out] / r[out, None]
                self.p[out] = n * lim[out, None]
                vn = (self.v[out] * n).sum(-1, keepdims=True)
                self.v[out] -= 1.4 * np.maximum(vn, 0) * n     # bounce off the wall, a little dead
                self.v[out] *= 0.85

    def render(self):
        cell = np.zeros((S, S, 3), np.float32)
        Y, X = np.mgrid[0:S, 0:S].astype(np.float32)
        u = (X / (S - 1)) * 2 - 1
        v = (Y / (S - 1)) * 2 - 1
        cols = hsv(self.hue + self.bh, np.full(NBEADS, 0.85), np.ones(NBEADS))
        for i in range(NBEADS):
            d = np.hypot(u - self.p[i, 0], v - self.p[i, 1])
            s = self.size[i]
            if self.shape[i] == "ring":
                a = np.clip(1 - np.abs(d - s * 0.75) / (s * 0.3), 0, 1)
            elif self.shape[i] == "shard":
                a = np.clip((s - (np.abs(u - self.p[i, 0]) + np.abs(v - self.p[i, 1]) * 2)) / 0.03, 0, 1)
            else:
                a = np.clip((s - d) / 0.03, 0, 1)
            cell = np.maximum(cell, a[..., None] * cols[i] * 0.9)
        glass = hsv(np.array(self.hue + 0.5), np.array(0.5), np.array(0.14))
        cell = np.where(cell.max(-1, keepdims=True) > 0.05, cell, glass)   # frosted glass behind the beads
        my, mx = self._look()
        img = cell[my, mx]
        img[self.outside] = 0
        return img

    def lights(self):
        c = tuple(float(x) for x in hsv(np.array(self.hue + self.barrel / (2 * math.pi)), np.array(0.8), np.array(0.8)))
        return [c, (.3 * self.zoom / 2.5,) * 3, (self.folds / 12, .3, .6), (1, .7, .2) if self.oil else (.2, .2, .2)]
