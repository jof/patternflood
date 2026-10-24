"""Truchet: a maze of arc tiles whose paths reroute as tiles spin.

After Lee's 0513, its grid of tile motifs. Each square holds two quarter
circles joining the midpoints of its edges, one of two ways round, so across
the grid the arcs join into endless winding paths. The regions between the
paths take two colours that alternate in a way that stays continuous across
every tile, so the whole field reads as one interlocking maze. The paths are
shaded ribbons carrying a rainbow that flows diagonally over everything.
Tiles spin a quarter turn now and then (and in waves, with the music), and
every spin reroutes the paths around it.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Chromatic


class Truchet(Chromatic):
    name = "Truchet"
    blurb = "A maze of arc tiles whose paths reroute as tiles spin (after Lee's 0513). k0 tile size, k1 spin rate, k2 ribbon width, k3 colour. Click k0 a wave of spins, k1 hold still, k2 fills, k3 next palette."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.size, self.rate, self.width = 16, 1.0, 0.16
        self.still, self.fills = False, True
        self.flow = 0.0
        self.t = 0.0
        self._grid()

    def _grid(self):
        n = N // self.size + 2
        self.turns = self.rng.integers(0, 2, (n, n)).astype(np.float32)   # quarter turns, target
        self.angle = self.turns.copy()                                       # quarter turns, shown (eases)
        self.pending_on = None                                               # a wave in progress was for the old grid

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.size = int(max(8, min(32, self.size + (2 if d > 0 else -2))))
            self._grid()
        elif k == 1:
            self.rate = max(0.0, min(8.0, self.rate * 1.12 ** d if self.rate else 0.2))
        elif k == 2:
            self.width = max(0.05, min(0.35, self.width + d * 0.01))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.wave()
        elif k == 1:
            self.still = not self.still
        elif k == 2:
            self.fills = not self.fills
        elif k == 3:
            self.next_palette()

    def wave(self):
        """A diagonal wave of spins, sweeping across the grid."""
        n = self.turns.shape[0]
        i, j = np.mgrid[0:n, 0:n]
        self.pending = (i + j).astype(np.float32) * 0.06            # seconds until each tile spins
        self.pending_on = np.ones((n, n), bool)

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        self.flow += dt * (0.12 + 0.5 * self.sound[1])
        if not self.still:
            n = self.turns.shape[0]
            spins = self.rng.random((n, n)) < dt * self.rate * 0.08
            self.turns[spins] += 1
        if self.pending_on is not None:
            self.pending -= dt
            go = self.pending_on & (self.pending <= 0)
            self.turns[go] += 1
            self.pending_on &= ~go
            if not self.pending_on.any():
                self.pending_on = None
        if self.on_bar or self.on_phrase:
            self.wave()
        self.angle += (self.turns - self.angle) * (1 - math.exp(-dt / 0.12))

    def render(self):
        s = self.size
        i, j = (X // s).astype(int), (Y // s).astype(int)
        u, v = X / s - i - 0.5, Y / s - j - 0.5
        theta = self.angle[j, i] * (math.pi / 2)
        c, sn = np.cos(theta), np.sin(theta)
        ru, rv = u * c + v * sn, -u * sn + v * c                       # into the tile's own frame
        d1 = np.hypot(ru + 0.5, rv + 0.5)
        d2 = np.hypot(ru - 0.5, rv - 0.5)
        dist = np.minimum(np.abs(d1 - 0.5), np.abs(d2 - 0.5))
        corner = (d1 < 0.5) | (d2 < 0.5)
        # two-colouring that stays continuous across tiles: flip with the tile's checker and turn
        parity = corner ^ (((i + j) % 2) == 1) ^ ((np.rint(self.angle[j, i]).astype(int) % 2) == 1)
        w = self.width * (1 + 0.4 * self.beat)
        ribbon = np.clip(1 - dist / w, 0, 1)
        rainbow = self.colour((X + Y) / 180 - self.flow)
        tube = (0.45 + 0.55 * np.sqrt(ribbon))[..., None]               # rounded: bright down the middle
        if self.fills:
            fill = np.where(parity[..., None], self.colour(0.5 - self.flow * 0.3), self.colour(0.0 - self.flow * 0.3))
            fill = fill * 0.38
        else:
            fill = np.zeros((N, N, 3), np.float32)
        edge = np.clip(1 - np.abs(dist - w) / 0.03, 0, 1)[..., None] * (dist > w * 0.5)[..., None]
        img = np.where((ribbon > 0)[..., None], rainbow * tube, fill)
        return np.clip(img * (1 - 0.8 * edge), 0, 1)

    def lights(self):
        return [self.glow(0, 0.6, 0.1 + 0.015 * self.size), self.glow(1, 0.3, 0.2 + 0.1 * self.rate),
                self.glow(2, 0.9, 0.2 + 2 * self.width), self.hue_light()]
