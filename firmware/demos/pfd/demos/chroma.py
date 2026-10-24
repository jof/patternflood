"""Chroma Waves: a ripple tank in colour, rings from a few drifting sources interfering.

After Lee's Retro Digital Tapestry, its rings crossing. Each source sends out
circular waves in its own colour from the palette, and the sources drift on
slow Lissajous paths. Where waves add, colours mix the way light does, so the
crossing rings make a moiré that shimmers through every hue; where crests meet
troughs, it goes dark. The waves are sharpened into bright rings rather than
soft sines, so the interference reads as lines.
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic


class Chroma(Chromatic):
    name = "Chroma Waves"
    blurb = "A ripple tank in colour: rings from drifting sources interfering (after Lee's Retro Digital Tapestry). k0 wavelength, k1 drift, k2 sources, k3 colour. Click k0 sharp or soft, k1 hold still, k3 next palette."

    def __init__(self, rt):
        super().__init__(rt)
        self.wavelength, self.drift, self.sources = 9.0, 1.0, 3
        self.sharp, self.still = True, False
        self.t = 0.0
        self.wt = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.wavelength = max(3.0, min(24.0, self.wavelength * 1.05 ** d))
        elif k == 1:
            self.drift = max(0.0, min(4.0, self.drift + d * 0.1))
        elif k == 2:
            self.sources = max(2, min(7, self.sources + (1 if d > 0 else -1)))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.sharp = not self.sharp
        elif k == 1:
            self.still = not self.still
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        if not self.still:
            self.t += dt * self.drift
        self.wt += dt * (2.5 + 4 * self.sound[2])                    # the waves keep running outward

    def render(self):
        n = self.sources
        img = np.zeros((128, 128, 3), np.float32)
        lam = self.wavelength * (1 - 0.15 * self.beat)
        for i in range(n):
            ph = i * 2 * math.pi / n
            sx = 64 + 42 * math.sin(self.t * (0.21 + 0.03 * i) + ph)
            sy = 64 + 42 * math.cos(self.t * (0.17 + 0.04 * i) + ph * 1.3)
            r = np.hypot(X - sx, Y - sy)
            w = 0.5 + 0.5 * np.cos(2 * math.pi * r / lam - self.wt)
            if self.sharp:
                w = w ** 6                                            # thin bright rings
            fall = 1 / (1 + r / 90)
            img += self.colour(i / n)[None, None, :] * (w * fall)[..., None]
        # soft waves carry about twice the light of sharp rings on average (0.5 against 924/4^6), so
        # they're scaled down to match
        img *= 2.4 / n ** 0.6 * (1.0 if self.sharp else 0.45)
        return np.clip(img, 0, 1)

    def lights(self):
        return [self.glow(0, 0.6, 0.1 + 0.03 * self.wavelength), self.glow(1, 0.3, 0.2 + 0.15 * self.drift),
                self.glow(2, 0.8, 0.1 + 0.1 * self.sources), self.hue_light()]
