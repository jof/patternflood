"""Guilloche: banknote rosettes, fine lines woven in colour, turning.

After Lee's Poincaré Sphere, its petals of lines. Each ring of the rosette is
a family of curves r = R(theta) + A sin(n theta + phi), one for each of K
evenly spaced phases phi, so they cross and recross into the woven band seen
on banknotes and certificates. Rather than drawing the K curves one by one,
each pixel works out which phases pass through it (phi = asin((r - R) / A) - n
theta, and its mirror) and lights if one is close to a line: one pass per
ring, however many lines. Three rings in three colours of the palette turn
against each other, and the base radius of each wobbles in a second rhythm.
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic

# each ring: base radius R, amplitude A, lobes n, curves K, wobble B and its lobes m. A ring
# crosses itself 2 n K times round, so n K stays near 20-40 to keep lines ~5 px apart here
LAYOUTS = [
    [(20, 10, 5, 3, 2.0, 3), (39, 12, 7, 4, 3.0, 4), (56, 7, 9, 4, 2.0, 6)],
    [(24, 16, 6, 4, 3.0, 2), (50, 12, 9, 4, 2.5, 5)],
    [(16, 9, 4, 3, 1.5, 2), (31, 9, 6, 3, 2.0, 3), (45, 9, 8, 4, 2.0, 4), (58, 5, 10, 4, 1.5, 8)],
]


class Guilloche(Chromatic):
    name = "Guilloche"
    blurb = "Banknote rosettes: fine lines woven in colour, turning (after Lee's Poincaré Sphere). k0 lobes, k1 lines, k2 amplitude, k3 colour. Click k0 next rosette, k1 hold still, k3 next palette."
    palette = 3

    def __init__(self, rt):
        super().__init__(rt)
        self.layout = 0
        self.lobes, self.lines, self.amp = 1.0, 1.0, 1.0
        self.still = False
        self.t = 0.0
        self.r = np.hypot(X - 63.5, Y - 63.5)
        self.theta = np.arctan2(Y - 63.5, X - 63.5)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.lobes = max(0.5, min(2.0, self.lobes + d * 0.05))
        elif k == 1:
            self.lines = max(0.4, min(2.5, self.lines + d * 0.05))
        elif k == 2:
            self.amp = max(0.2, min(1.8, self.amp + d * 0.05))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.layout = (self.layout + 1) % len(LAYOUTS)
        elif k == 1:
            self.still = not self.still
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        if not self.still:
            self.t += dt * (1 + self.sound[1])
        if self.on_phrase:
            self.layout = (self.layout + 1) % len(LAYOUTS)

    def render(self):
        img = np.zeros((128, 128, 3), np.float32)
        rings = LAYOUTS[self.layout]
        for i, (R, A, n, K, B, m) in enumerate(rings):
            n = max(1, round(n * self.lobes))
            K = max(3, round(K * self.lines))
            A = A * self.amp * (1 + 0.25 * self.beat)
            spin = self.t * (0.25 if i % 2 else -0.18) * (1 + 0.2 * i)
            base = R + B * np.sin(m * self.theta - self.t * 0.4 * (1 if i % 2 else -1))
            s = (self.r - base) / A
            inside = np.abs(s) < 1
            a = np.arcsin(np.clip(s, -1, 1))
            th = self.theta * n + spin
            # the two branches of asin give the two crossing sets of curves
            line = np.maximum((0.5 + 0.5 * np.cos(K * (a - th))) ** 10,
                              (0.5 + 0.5 * np.cos(K * (math.pi - a - th))) ** 10)
            fade = np.clip((1 - np.abs(s)) * 6, 0, 1) * inside
            img += self.colour(i / len(rings))[None, None, :] * (line * fade)[..., None]
        return np.clip(img * 1.3, 0, 1)

    def lights(self):
        return [self.glow(0, 0.1, 0.2 + 0.3 * self.lobes), self.glow(1, 0.4, 0.2 + 0.2 * self.lines),
                self.glow(2, 0.7, 0.2 + 0.3 * self.amp), self.hue_light()]
