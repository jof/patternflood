"""Ribbons: saturated colour stripes warped by travelling waves.

After SeungHun's Wave Saw, its bending stripes, and Bridget Riley's colour stripe
paintings. A repeating run of stripes in a few palette colours is bent by
sine waves whose phase slides along them, so the curves travel down the
ribbons and the colours seem to shimmer where they crowd. Stripes can run up
and down, across, or round in rings.
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic

LAYOUTS = ["vertical", "horizontal", "rings"]


class Ribbons(Chromatic):
    name = "Ribbons"
    blurb = "Saturated colour stripes warped by travelling waves (after SeungHun's Wave Saw). k0 stripe width, k1 wave height, k2 wave length, k3 colour. Click k1 up, across or rings, k2 hold still, k3 next palette."
    palette = 2

    def __init__(self, rt):
        super().__init__(rt)
        self.width, self.amp, self.length = 4.5, 1.0, 1.0
        self.layout, self.still = 0, False
        self.colours = 5
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.width = max(2.0, min(12.0, self.width + d * 0.2))
        elif k == 1:
            self.amp = max(0.0, min(3.0, self.amp + d * 0.08))
        elif k == 2:
            self.length = max(0.3, min(3.0, self.length * 1.05 ** d))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 1:
            self.layout = (self.layout + 1) % len(LAYOUTS)
        elif k == 2:
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
        t = self.t
        lay = LAYOUTS[self.layout]
        k = 0.06 / self.length
        if lay == "rings":                      # round the rings, a whole number of lobes per turn (no seam)
            across, theta = np.hypot(X - 63.5, Y - 63.5), np.arctan2(Y - 63.5, X - 63.5)
            m = max(1, round(5 / self.length))
            a1, a2 = theta * m, theta * (m + 2)
        else:
            across, along = (X, Y) if lay == "vertical" else (Y, X)
            a1, a2 = along * k, along * k * 2.3
        amp = self.amp * (1 + 0.8 * self.sound[2] + 0.6 * self.beat)
        # the bend: two waves whose phase drifts across the stripes, so the curves travel
        bend = amp * (9 * np.sin(a1 + across * 0.035 - t * 1.4) + 4 * np.sin(a2 - across * 0.02 + t * 0.9))
        s = (across + bend) / self.width
        idx = np.floor(s)
        frac = s - idx
        img = self.colour((idx % self.colours) / self.colours)
        # each stripe a little rounded, darker at its edges
        img = img * (0.7 + 0.3 * np.sin(math.pi * frac))[..., None]
        return np.clip(img, 0, 1)

    def lights(self):
        return [self.glow(0, 0.1, 0.1 + 0.05 * self.width), self.glow(1, 0.6, 0.2 + 0.2 * self.amp),
                self.glow(2, 0.85, 0.2 + 0.2 * self.length), self.hue_light()]
