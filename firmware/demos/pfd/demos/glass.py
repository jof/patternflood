"""Stained Glass: panes of coloured glass in lead, lit from behind by a moving sun.

After SeungHun's 0601, its blocks of colour. The panes are the cells of a Voronoi
pattern: every point belongs to its nearest seed, and where two seeds are
nearly equally near, a lead line runs. The seeds drift slowly, so panes grow,
shrink and trade neighbours. Each pane has its own colour from the palette,
and the light behind the window wanders, so panes brighten as it passes behind
them. The glass is rippled, so the light catches unevenly within each pane.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Chromatic


class Glass(Chromatic):
    name = "Stained Glass"
    blurb = "Panes of coloured glass in lead, lit by a moving sun behind (after SeungHun's 0601). k0 panes, k1 drift, k2 lead width, k3 colour. Click k0 a new window, k1 hold still, k3 next palette."
    palette = 2

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.count, self.drift, self.lead = 26, 1.0, 1.4
        self.still = False
        self.t = 0.0
        self.new_window()

    def new_window(self):
        r = self.rng
        n = self.count
        self.seeds = r.uniform(-4, N + 4, (n, 2)).astype(np.float32)
        self.vel = r.normal(0, 1, (n, 2)).astype(np.float32)
        self.hue = r.random(n).astype(np.float32)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.count = max(6, min(70, self.count + (2 if d > 0 else -2)))
            self.new_window()
        elif k == 1:
            self.drift = max(0.0, min(5.0, self.drift + d * 0.15))
        elif k == 2:
            self.lead = max(0.4, min(4.0, self.lead + d * 0.1))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.new_window()
        elif k == 1:
            self.still = not self.still
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        if not self.still:
            v = self.vel + 0.6 * np.column_stack([np.sin(self.t * 0.3 + self.hue * 9), np.cos(self.t * 0.27 + self.hue * 7)])
            self.seeds += v * dt * 3 * self.drift * (1 + self.sound[1])
            self.seeds = (self.seeds + 8) % (N + 16) - 8
        if self.on_phrase:
            self.hue = self.rng.random(len(self.hue)).astype(np.float32)

    def render(self):
        s = self.seeds
        d = (X[..., None] - s[:, 0]) ** 2 + (Y[..., None] - s[:, 1]) ** 2       # (N, N, seeds)
        two = np.partition(d, 1, axis=-1)[..., :2]
        nearest = np.argmin(d, axis=-1)
        d1, d2 = np.sqrt(two[..., 0]), np.sqrt(two[..., 1])
        lead = (d2 - d1) < self.lead * (1 + 0.4 * self.beat)
        glass = self.colour(self.hue[nearest])
        # the light behind: a soft sun wandering across the window
        lx, ly = 64 + 44 * math.sin(self.t * 0.13), 64 + 38 * math.sin(self.t * 0.17 + 1)
        sun = np.exp(-((X - lx) ** 2 + (Y - ly) ** 2) / 1800)
        ripple = 0.88 + 0.12 * np.sin(X * 0.7 + np.sin(Y * 0.31) * 3) * np.sin(Y * 0.55 + np.sin(X * 0.23) * 3)
        light = (0.62 + 0.7 * sun) * ripple * (1 + 0.5 * self.sound[2])
        # each pane a touch darker at its edge, as thick glass is
        edge = np.clip((d2 - d1) / 10, 0, 1)
        img = glass * (light * (0.6 + 0.4 * edge))[..., None]
        img[lead] = (0.05, 0.05, 0.06)
        return np.clip(img, 0, 1)

    def lights(self):
        return [self.glow(0, 0.15, 0.1 + 0.01 * self.count), self.glow(1, 0.55, 0.2 + 0.15 * self.drift),
                self.glow(2, 0.0, 0.1 + 0.15 * self.lead), self.hue_light()]
