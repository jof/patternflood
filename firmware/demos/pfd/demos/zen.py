"""Zen: a raked sand garden, slowly raked again, dithered.

After SeungHun's 0619, its patterned lines. Grooves run straight across the
gravel, and near each stone they bend into rings around it, as a karesansui
garden is raked. The grooves are a height field lit by a low sun, so each
ridge has a bright face and a shadowed one. A rake crosses the garden top to
bottom, laying down a new pattern (a new angle and spacing) behind it, its
tines dragging through the old one. Now and then a petal drifts down and
settles. The stones are dark and mossy.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

PETAL_INK = (1.0, 0.68, 0.78)


class Zen(Inked):
    name = "Zen"
    blurb = "A raked sand garden, slowly raked anew (after SeungHun's 0619). k0 rake speed, k1 groove spacing for the next raking, k2 screen, k3 inks. Click k0 rake now, k1 move the stones, k2 chunky."
    palette, screen_kind = "sand", "bayer8"     # the sand inks sit close, so ridges are a fine grain

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng(3)
        self.place_stones()
        self.old = (0.0, 5.0)                 # (angle, spacing) of the pattern already there
        self.new = (0.5, 6.0)
        self.rake_y = -10.0                   # the rake's position; past the bottom it's resting
        self.speed, self.spacing = 1.0, 6.0
        self.petals = []                      # [x, y, vx, vy, settled]
        self.t = 0.0
        self.rest = 0.0

    def place_stones(self):
        r = self.rng
        self.stones = []
        while len(self.stones) < 3:           # well apart, so each gets its own rings
            s = (float(r.uniform(22, 106)), float(r.uniform(24, 104)), float(r.uniform(6, 11)))
            if all(math.hypot(s[0] - x, s[1] - y) > s[2] + rr + 26 for x, y, rr in self.stones):
                self.stones.append(s)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.speed = max(0.2, min(4.0, self.speed * 1.08 ** d))
        elif k == 1:
            self.spacing = max(3.5, min(10.0, self.spacing + d * 0.25))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.start_raking()
        elif k == 1:
            self.place_stones()
        elif k == 2:
            self.chunky()

    def start_raking(self):
        self.old = self.new if self.rake_y > N else self.old
        self.new = (float(self.rng.uniform(-0.6, 0.6)), self.spacing)
        self.rake_y = -6.0

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        if self.rake_y <= N + 6:
            self.rake_y += dt * 7 * self.speed * (1 + self.sound[1])
        else:
            self.rest += dt
            if self.rest > 12 or self.on_phrase:
                self.rest = 0.0
                self.start_raking()
        if self.rng.random() < dt / 3 or (self.on_beat and self.rng.random() < 0.2):
            self.petals.append([float(self.rng.uniform(0, N)), -2.0, float(self.rng.normal(4, 3)), 9.0, 0.0])
        for p in self.petals:
            if not p[4]:
                p[0] += (p[2] + 6 * math.sin(self.t * 2 + p[1] * 0.1)) * dt
                p[1] += p[3] * dt
                if p[1] > self.rng.uniform(20, 126) and self.rng.random() < dt * 2:
                    p[4] = 1.0
        self.petals = [p for p in self.petals if p[1] < N + 2][-40:]

    def height(self, angle, spacing):
        """The raked surface for one pattern: lines at an angle, bending into rings near stones."""
        lines = X * math.sin(angle) + Y * math.cos(angle)
        p = lines
        for sx, sy, sr in self.stones:
            d = np.hypot(X - sx, Y - sy)
            zone = sr + 3 * spacing
            w = np.clip((zone - d) / (spacing * 1.2), 0, 1)
            w = w * w * (3 - 2 * w)
            p = p * (1 - w) + (d - sr) * w           # inside the zone, grooves follow the stone
        return np.cos(2 * math.pi * p / spacing)

    def render(self):
        old = self.height(*self.old)
        new = self.height(*self.new)
        raked = np.clip((self.rake_y - Y) / 2, 0, 1)
        h = old * (1 - raked) + new * raked
        gx = np.roll(h, -1, 1) - np.roll(h, 1, 1)
        gy = np.roll(h, -1, 0) - np.roll(h, 1, 0)
        shade = 0.78 + 0.06 * gx + 0.09 * gy                 # a low sun from the lower right: gentle ridges
        tone = np.clip(shade, 0.15, 0.95)
        for sx, sy, sr in self.stones:                       # stones: dark, rounded, lit on one side
            d = np.hypot(X - sx, Y - sy)
            q = np.clip(1 - (d / sr) ** 2, 0, 1)
            nz = np.sqrt(q)                                   # a rounded rock: its normal, lit from the low sun
            lit = np.clip(0.06 + 0.5 * np.clip(((X - sx) + (Y - sy)) / sr * 0.55 + nz * 0.6, 0, 1), 0.04, 0.6)
            shadow = (d >= sr) & (np.hypot(X - sx + 2.5, Y - sy + 2.5) < sr)    # cast away from the low sun
            tone = np.where(shadow, tone * 0.55, tone)
            tone = np.where(d < sr, lit * (0.85 + 0.15 * np.sin(X * 1.3 + Y * 0.9)), tone)
        if 0 <= self.rake_y < N:                             # the rake: a beam with tines
            ry = int(self.rake_y)
            tone[max(0, ry - 2):ry, :] = 0.08
            tone[ry:ry + 2, ::3] = 0.08
        img = self.print(np.clip(tone, 0, 1))
        for x, y, *_ in self.petals:
            xi, yi = int(x), int(y)
            if 0 <= xi < N - 1 and 0 <= yi < N:
                img[yi, xi:xi + 2] = PETAL_INK
        return img

    def lights(self):
        return [self.glow(0, 0.12, 0.2 + 0.15 * self.speed), self.glow(1, 0.1, 0.1 + 0.06 * self.spacing)] + self.ink_lights()
