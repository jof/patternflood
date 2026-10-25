"""Marbling: ink dropped on water, pushed into rings and combed into feathers.

After SeungHun's 0520, its soft blobs, and the paper marbler's tray (ebru,
suminagashi). Every drop of ink spreads as a disc and pushes all the ink
already on the water outward, keeping its area, so earlier drops become
rings round later ones. A comb dragged across draws everything along with
it, most strongly near its tines, into feathered chevrons. All of it is
exact (Jaffer and Lu's mathematical marbling): the tray keeps the list of
drops and strokes, and each pixel is traced backwards through them to find
which drop's ink it holds.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Chromatic

MAX_OPS = 48


class Marbling(Chromatic):
    name = "Marbling"
    blurb = "Ink dropped on water, pushed into rings and combed into feathers (after SeungHun's 0520). k0 drop size, k1 drop rate, k2 comb spacing, k3 colour. Click k0 fresh tray, k1 a big drop, k2 comb it, k3 next palette."
    palette = 3

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.size, self.rate, self.spacing = 1.0, 1.0, 16.0
        self.ops = []                       # ("drop", cx, cy, r, hue) or ("comb", angle, spacing, z, z_to, phase)
        self.n = 0
        self.t = 0.0
        self.next_drop = 0.0
        for _ in range(10):
            self.drop()

    def drop(self, big=False):
        r = self.rng
        cx, cy = r.uniform(10, 118), r.uniform(10, 118)
        rad = (r.uniform(9, 20) * self.size) * (2.0 if big else 1.0)
        self.n += 1
        self.ops.append(("drop", cx, cy, rad, (self.n * 0.137) % 1))
        self.trim()

    def comb(self):
        a = self.rng.choice([0.0, math.pi / 2, math.pi / 4, -math.pi / 4])
        self.ops.append(["comb", float(a), self.spacing, 0.0, float(self.rng.uniform(10, 22)), float(self.rng.uniform(0, 1))])
        self.trim()

    def trim(self):
        while len(self.ops) > MAX_OPS:      # the oldest ink is by now thin rings at the edges
            self.ops.pop(0)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.size = max(0.4, min(2.5, self.size * 1.06 ** d))
        elif k == 1:
            self.rate = max(0.1, min(5.0, self.rate * 1.1 ** d))
        elif k == 2:
            self.spacing = max(6.0, min(40.0, self.spacing + d))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.ops = []
            for _ in range(4):
                self.drop()
        elif k == 1:
            self.drop(big=True)
        elif k == 2:
            self.comb()
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        self.next_drop -= dt * self.rate * (1 + self.sound[2])
        if self.next_drop <= 0:
            self.next_drop = self.rng.uniform(0.6, 1.6)
            if self.rng.random() < 0.12:
                self.comb()
            else:
                self.drop()
        if self.on_beat and self.rt.audio.kick > 0.7:
            self.drop()
        if self.on_phrase:
            self.comb()
        for op in self.ops:                 # strokes are dragged through over a second or so
            if op[0] == "comb" and op[3] < op[4]:
                op[3] = min(op[4], op[3] + dt * 14)

    def render(self):
        px, py = X.astype(np.float32).copy(), Y.astype(np.float32).copy()
        hue = np.full((N, N), -1.0, np.float32)
        for op in reversed(self.ops):       # trace each pixel back through the tray's history
            if op[0] == "drop":
                _, cx, cy, r, h = op
                dx, dy = px - cx, py - cy
                d2 = dx * dx + dy * dy
                inside = (d2 < r * r) & (hue < 0)
                hue[inside] = h
                scale = np.sqrt(np.clip(1 - r * r / np.maximum(d2, 1e-6), 0, 1))
                px, py = cx + dx * scale, cy + dy * scale
            else:
                _, a, lam, z, _, ph = op
                mx, my = math.cos(a), math.sin(a)            # the comb moves along m; its tines are lines along m
                nx, ny = -my, mx
                dist = (px * nx + py * ny) / lam + ph
                d = np.abs(dist - np.floor(dist) - 0.5) * lam    # distance to the nearest tine
                shift = z * 0.5 ** (d / 3.0)
                px, py = px - shift * mx, py - shift * my
        paper = hue < 0
        img = self.colour(np.where(paper, 0.0, hue))
        img[paper] = (0.9, 0.88, 0.8)
        return np.clip(img * (1 + 0.15 * self.beat), 0, 1)

    def lights(self):
        return [self.glow(0, 0.6, 0.1 + 0.25 * self.size), self.glow(1, 0.3, 0.1 + 0.15 * self.rate),
                self.glow(2, 0.85, 0.1 + 0.02 * self.spacing), self.hue_light()]
