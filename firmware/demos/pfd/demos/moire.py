"""Moiré: fine coloured gratings turning against each other.

After Lee's Retro Digital Tapestry and 0515-4. Two or three layers of thin
lines (or rings, or dots), each in its own colour of the palette, lie over
one another and turn at slightly different speeds. Where their lines nearly
agree, broad fringes appear that are in none of the layers. They sweep and
swirl far faster than the gratings themselves turn, and where layers overlap
the colours add, the way light does.
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic

KINDS = ["lines", "rings", "dots"]


class Moire(Chromatic):
    name = "Moiré"
    blurb = "Fine coloured gratings turning against each other into sweeping fringes (after Lee's Retro Digital Tapestry). k0 pitch, k1 turn speed, k2 pattern, k3 colour. Click k0 thick lines, k1 a third layer, k3 next palette."

    def __init__(self, rt):
        super().__init__(rt)
        self.pitch, self.speed, self.kind = 6.0, 1.0, 0
        self.thick, self.three = False, True
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.pitch = max(4.0, min(14.0, self.pitch + d * 0.2))
        elif k == 1:
            self.speed = max(-3.0, min(3.0, self.speed + d * 0.1))
        elif k == 2:
            self.kind = (self.kind + (1 if d > 0 else -1)) % len(KINDS)
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.thick = not self.thick
        elif k == 1:
            self.three = not self.three
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        self.t += dt * self.speed * (1 + self.sound[1])
        if self.on_phrase:
            self.kind = (self.kind + 1) % len(KINDS)

    def layer(self, i):
        t = self.t
        # the set turns as a whole, and the layers' small angles apart breathe: that's what sweeps the fringes
        a = t * 0.12 + i * (0.07 + 0.05 * math.sin(t * 0.11)) + 0.03 * math.sin(t * 0.13 + i * 2.1)
        cx = 63.5 + 18 * math.sin(t * 0.07 + i * 1.9)
        cy = 63.5 + 18 * math.cos(t * 0.06 + i * 1.3)
        x, y = X - cx, Y - cy
        c, s = math.cos(a), math.sin(a)
        u, v = x * c + y * s, -x * s + y * c
        p = self.pitch * (1 + 0.012 * i) * (1 - 0.05 * self.beat)
        kind = KINDS[self.kind]
        if kind == "lines":
            w = 0.5 + 0.5 * np.cos(2 * math.pi * u / p)
        elif kind == "rings":
            w = 0.5 + 0.5 * np.cos(2 * math.pi * np.hypot(u, v) / p)
        else:
            w = (0.5 + 0.5 * np.cos(2 * math.pi * u / p)) * (0.5 + 0.5 * np.cos(2 * math.pi * v / p))
        return w ** (2 if self.thick else 4)

    def render(self):
        n = 3 if self.three else 2
        img = np.zeros((128, 128, 3), np.float32)
        for i in range(n):
            img += self.colour(i / n)[None, None, :] * self.layer(i)[..., None]
        return np.clip(img * (1.1 if self.thick else 1.6), 0, 1)

    def lights(self):
        return [self.glow(0, 0.6, 0.1 + 0.08 * self.pitch), self.glow(1, 0.3, 0.2 + 0.15 * abs(self.speed)),
                self.glow(2, self.kind / 3), self.hue_light()]
