"""Droste: a spiral of colour bands, zooming in for ever.

After SeungHun's Chromatic Vortex. In log-polar coordinates (the logarithm of the
distance from the centre, and the angle) a zoom is just a slide and a spiral
is just a sloping line, so bands that slope across that plane become
logarithmic spirals, and sliding them makes an endless zoom: each band grows
out of the centre and swells past the edge while the next follows it. A
second family of spirals winding the other way crosses the first into a
checker of curved tiles, as in Escher's spiral prints.
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic


class Droste(Chromatic):
    name = "Droste"
    blurb = "Spiral bands of colour zooming in for ever (after SeungHun's Chromatic Vortex). k0 zoom speed (and reverse), k1 arms, k2 twist, k3 colour. Click k0 stop, k1 checker, k3 next palette."
    palette = 4

    def __init__(self, rt):
        super().__init__(rt)
        self.speed, self.arms, self.twist = 1.0, 3, 1.0
        self.checker, self.go = True, True
        self.z = 0.0
        r = np.hypot(X - 63.5, Y - 63.5) + 0.5
        self.rho = np.log(r)
        self.theta = np.arctan2(Y - 63.5, X - 63.5)
        self.r = r

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.speed = max(-4.0, min(4.0, self.speed + d * 0.1))
        elif k == 1:
            self.arms = max(1, min(12, self.arms + (1 if d > 0 else -1)))
        elif k == 2:
            self.twist = max(-3.0, min(3.0, self.twist + d * 0.1))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.go = not self.go
        elif k == 1:
            self.checker = not self.checker
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        if self.go:
            self.z += dt * self.speed * 0.6 * (1 + 1.5 * self.sound[2] + 2 * self.beat)
        if self.on_phrase:
            self.arms = self.arms % 6 + 2

    def render(self):
        rho = self.rho - self.z
        # one family: arms spirals, the band index climbing as rho climbs (outward) and round the turn
        s1 = (rho * 2.2 * self.twist + self.theta * self.arms / (2 * math.pi) * (1 if self.twist >= 0 else -1))
        img = self.colour(s1 / self.arms)                     # whole palette cycles per turn: no seam at the wrap
        if self.checker:                              # a second family the other way: a checker of tiles
            s2 = rho * 2.2 - self.theta * (self.arms + 2) / (2 * math.pi)     # arms + 2: the checker's parity survives the wrap
            tile = (np.floor(s1) + np.floor(s2)) % 2
            shade = 0.55 + 0.45 * tile
            img = img * shade[..., None]
        edge = np.minimum(s1 % 1, 1 - s1 % 1) < 0.06
        img[edge] *= 0.4
        img *= np.clip(self.r / 6, 0, 1)[..., None]   # the centre, where everything converges, fades out
        return np.clip(img, 0, 1)

    def lights(self):
        return [self.glow(0, 0.6, 0.1 + 0.15 * abs(self.speed)), self.glow(1, self.arms / 12),
                self.glow(2, 0.9, 0.2 + 0.2 * abs(self.twist)), self.hue_light()]
