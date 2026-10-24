"""Riso: a moving colour field, printed as halftone in three inks that never quite register.

Lee's dithers are 1-bit; this is the print shop's version of the same idea.
Each ink is a grid of dots at its own screen angle, every dot sized by the
field's value at that cell's centre (area-true, so tones stay honest). The
grids turn slowly against each other, so the rosettes and moiré between them
churn. A little misregistration drifts each plate, so colours fringe where they
overlap, as a riso print does.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Original

# Inks: three plates plus the paper. On LEDs ink is light, so plates add, except on "paper",
# where they multiply out of a lit sheet as on a real print.
INKS = [
    ("riso", [(1.0, 0.12, 0.5), (0.0, 0.55, 1.0), (1.0, 0.85, 0.0)], None),
    ("light", [(1, 0, 0), (0, 1, 0), (0, 0, 1)], None),
    ("sunset", [(1.0, 0.25, 0.0), (0.7, 0.0, 0.9), (1.0, 0.75, 0.1)], None),
    ("mint", [(0.0, 0.95, 0.6), (0.2, 0.3, 1.0), (1.0, 0.3, 0.7)], None),
    ("paper", [(0.0, 0.7, 0.85), (0.9, 0.0, 0.55), (0.95, 0.85, 0.0)], (0.55, 0.52, 0.45)),
]
ANGLES = (math.radians(15), math.radians(75), math.radians(45))
SOURCES = ["plasma", "orbs", "rings"]


class Riso(Original):
    name = "Riso"
    blurb = "A colour field printed as three halftone plates that churn into moiré. k0 dot size, k1 screen turn, k2 misprint, k3 inks. Click k0 next picture, k1 square the screens."

    def __init__(self, rt):
        super().__init__(rt)
        self.pitch = 6.0
        self.turn_rate = 0.03
        self.spin = 0.0
        self.misreg = 1.2
        self.ink_i = 0
        self.src = 0
        self.t = 0.0
        self.offs = np.zeros((3, 2), np.float32)
        self.orbs = np.random.default_rng(3).random((7, 5)).astype(np.float32)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.pitch = max(3.0, min(16.0, self.pitch * 1.06 ** d))
        elif k == 1:
            self.turn_rate = max(-0.6, min(0.6, self.turn_rate + d * 0.01))
        elif k == 2:
            self.misreg = max(0.0, min(8.0, self.misreg + d * 0.25))
        elif k == 3:
            self.ink_i = (self.ink_i + (1 if d > 0 else -1)) % len(INKS)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.src = (self.src + 1) % len(SOURCES)
        elif k == 1:
            self.spin, self.turn_rate = 0.0, 0.0

    def step(self, dt):
        self.hear(dt)
        self.t += dt * (1 + 1.5 * self.sound[1])
        self.spin += (self.turn_rate + 0.15 * self.sound[3]) * dt
        if self.rt.t - self.t_touch[0] > 30 and int(self.rt.t / 30) != int((self.rt.t - dt) / 30):
            self.src = (self.src + 1) % len(SOURCES)     # left alone, a new picture every half minute
        if self.on_phrase:
            self.src = (self.src + 1) % len(SOURCES)
        mis = self.misreg + 4 * self.sound[2] + 3 * self.beat
        for p in range(3):
            ph = self.rt.t * (0.21 + 0.07 * p) + 2.1 * p
            self.offs[p] = (mis * math.sin(ph), mis * math.cos(ph * 1.3))

    def field(self, x, y, plate):
        """The picture: plate p's value 0..1 at screen points (x, y)."""
        t = self.t
        u, v = x / N, y / N
        if SOURCES[self.src] == "plasma":
            a = (np.sin(u * 6.1 + t * 0.7 + plate * 2.1) + np.sin(v * 5.3 - t * 0.5 + plate)
                 + np.sin((u + v) * 4.3 + t * 0.4 + plate * 1.3) + np.sin(np.hypot(u - 0.5, v - 0.5) * 11 - t))
            return np.clip(0.45 + 0.3 * a, 0, 1) ** 2.2
        if SOURCES[self.src] == "orbs":
            acc = np.zeros_like(x)
            for i, (px, py, sp, r, c) in enumerate(self.orbs):
                if int(c * 3) % 3 != plate and i % 3 != plate:
                    continue
                cx = 0.5 + 0.4 * math.sin(t * (0.2 + sp * 0.3) + px * 6)
                cy = 0.5 + 0.4 * math.cos(t * (0.17 + sp * 0.25) + py * 6)
                acc += np.exp(-((u - cx) ** 2 + (v - cy) ** 2) / (0.02 + 0.05 * r))
            return np.clip(acc, 0, 1) ** 1.5 * 0.9
        cx = 0.5 + 0.25 * math.sin(t * 0.3 + plate * 2.1)
        cy = 0.5 + 0.25 * math.cos(t * 0.23 + plate * 1.7)
        return np.clip(0.5 + 0.5 * np.sin(np.hypot(u - cx, v - cy) * 26 - t * 2 + plate), 0, 1) ** 1.8

    def plate(self, p):
        """Coverage 0..1 of plate p's dots: an antialiased disc per screen cell, its area the
        picture's value at the cell's centre."""
        pitch = self.pitch * (1 - 0.15 * self.beat)
        a = ANGLES[p] + self.spin * (1 + 0.6 * p)
        c, s = math.cos(a), math.sin(a)
        x = X - 63.5 - self.offs[p, 0]
        y = Y - 63.5 - self.offs[p, 1]
        gu, gv = (x * c + y * s) / pitch, (-x * s + y * c) / pitch
        cu, cv = np.floor(gu) + 0.5, np.floor(gv) + 0.5
        d = np.hypot(gu - cu, gv - cv) * pitch
        # the cell centre, back in screen coordinates, to sample the picture there
        sx = (cu * c - cv * s) * pitch + 63.5 + self.offs[p, 0]
        sy = (cu * s + cv * c) * pitch + 63.5 + self.offs[p, 1]
        r = pitch * np.sqrt(self.field(sx, sy, p) / math.pi) * 1.08
        return np.clip(r - d + 0.5, 0, 1)

    def render(self):
        name, inks, paper = INKS[self.ink_i]
        if paper is None:
            img = np.zeros((N, N, 3), np.float32)
            for p in range(3):
                img += self.plate(p)[..., None] * np.asarray(inks[p], np.float32)
            return np.clip(img, 0, 1)
        img = np.ones((N, N, 3), np.float32) * np.asarray(paper, np.float32)
        for p in range(3):                          # ink takes away what it doesn't reflect
            img *= 1 - self.plate(p)[..., None] * (1 - np.asarray(inks[p], np.float32))
        return img

    def lights(self):
        inks = INKS[self.ink_i][1]
        return [self.glow(0, self.src / 3), self.glow(1, 0.55), self.glow(2, 0.9),
                tuple(float(c) * 0.7 for c in inks[0])]
