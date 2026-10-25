"""Quasicrystal: plane waves at evenly spaced angles, adding into a pattern that never repeats.

After SeungHun's 0515-4, its interlocking marks. n waves of one wavelength, each
pointing a step of 180/n degrees round from the last, are summed. With n = 4
the sum tiles like a carpet; with 5, 7 or more it never repeats, a
quasicrystal, with the rotational order of a Penrose tiling. Every wave's phase
slides with time, so the rosettes breathe, dissolve and reform. The sum is
coloured as flowing bands of the palette, or posterized into flat steps.
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic


class Quasi(Chromatic):
    name = "Quasicrystal"
    blurb = "Plane waves at evenly spaced angles, summing into a pattern that never repeats (after SeungHun's 0515-4). k0 scale, k1 symmetry, k2 phase speed, k3 colour. Click k0 bands or steps, k1 hold still, k3 next palette."

    def __init__(self, rt):
        super().__init__(rt)
        self.scale, self.order, self.speed = 0.32, 7, 1.0
        self.steps, self.still = False, False
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.scale = max(0.08, min(1.0, self.scale * 1.05 ** d))
        elif k == 1:
            self.order = max(3, min(13, self.order + (1 if d > 0 else -1)))
        elif k == 2:
            self.speed = max(-4.0, min(4.0, self.speed + d * 0.1))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.steps = not self.steps
        elif k == 1:
            self.still = not self.still
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        if not self.still:
            self.t += dt * self.speed * (1 + 1.5 * self.sound[1])
        if self.on_phrase:
            self.order = 5 + (self.order - 3) % 7

    def render(self):
        n = self.order
        x, y = (X - 63.5) * self.scale * (1 + 0.1 * self.beat), (Y - 63.5) * self.scale * (1 + 0.1 * self.beat)
        f = np.zeros_like(x)
        for k in range(n):
            a = math.pi * k / n
            f += np.cos(x * math.cos(a) + y * math.sin(a) + self.t * (1 + 0.15 * k))
        f /= n                                                  # -1..1
        if self.steps:
            t = np.floor((f + 1) * 4) / 8
            return np.clip(self.colour(t), 0, 1)
        bands = 0.5 + 0.5 * np.cos(f * math.pi * 3)             # bright where the sum crosses its levels
        img = self.colour(f * 0.8) * (0.5 + 0.5 * bands)[..., None]
        return np.clip(img, 0, 1)

    def lights(self):
        return [self.glow(0, 0.6, 0.15 + self.scale * 0.6), self.glow(1, self.order / 13),
                self.glow(2, 0.3, 0.2 + 0.1 * abs(self.speed)), self.hue_light()]
