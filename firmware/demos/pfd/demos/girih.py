"""Girih: an eight-pointed star tiling with strapwork, in flowing colour.

After SeungHun's 0514, its crosses in a grid, and the zellij of Moroccan tilework.
Every square cell holds an eight-pointed star whose tips touch its
neighbours', leaving cross-shaped spaces between. Each point is folded into
one sixteenth of its cell (mirrors across the axes and the diagonals), where
the star is just a single edge: whether a point lies inside the star, and
how near its outline, is one line test. The outlines are drawn as strapwork
bands; the stars, the rosettes inside them and the crosses take colours of
the palette that flow across the tiling in a slow diagonal wave.
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic


class Girih(Chromatic):
    name = "Girih"
    blurb = "An eight-pointed star tiling with strapwork, in flowing colour (after SeungHun's 0514). k0 tile size, k1 star depth, k2 strap width, k3 colour. Click k1 inner rosettes, k3 next palette."
    palette = 1

    def __init__(self, rt):
        super().__init__(rt)
        self.size, self.depth, self.strap = 40.0, 3, 0.035
        self.rosettes = True
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.size = max(20.0, min(90.0, self.size * 1.05 ** d))
        elif k == 1:
            self.depth = 2 if self.depth == 3 else 3
        elif k == 2:
            self.strap = max(0.01, min(0.08, self.strap + d * 0.003))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 1:
            self.rosettes = not self.rosettes
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        self.t += dt * (1 + self.sound[1])
        if self.on_phrase:
            self.rosettes = not self.rosettes

    def star_edge(self, u, v, radius):
        """Signed distance-ish from the star {8/depth} of this radius (negative inside), for points
        already folded into the octant 0 <= v <= u (angle 0 to 22.5 degrees)."""
        a = (radius, 0.0)
        b_ang = self.depth * math.pi / 4                     # the edge from the tip at 0 to the tip `depth` steps round
        b = (radius * math.cos(b_ang), radius * math.sin(b_ang))
        ex, ey = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(ex, ey)
        nx, ny = ey / ln, -ex / ln                           # the normal pointing away from the centre
        if nx * (-a[0]) + ny * (-a[1]) > 0:
            nx, ny = -nx, -ny
        return (u - a[0]) * nx + (v - a[1]) * ny

    def render(self):
        s = self.size * (1 + 0.04 * self.beat)
        x, y = (X - 63.5) / s, (Y - 63.5) / s
        ci, cj = np.floor(x + 0.5), np.floor(y + 0.5)
        u, v = np.abs(x - ci), np.abs(y - cj)                # fold: mirrors across the cell's axes...
        u, v = np.maximum(u, v), np.minimum(u, v)            # ...and its diagonals...
        c8, s8 = math.cos(math.pi / 8), math.sin(math.pi / 8)
        over = v * c8 - u * s8 > 0                           # ...and the line at 22.5 degrees: a sixteenth
        ru = u * math.cos(math.pi / 4) + v * math.sin(math.pi / 4)
        rv = u * math.sin(math.pi / 4) - v * math.cos(math.pi / 4)
        u, v = np.where(over, ru, u), np.where(over, rv, v)
        star = self.star_edge(u, v, 0.5)
        rosette = self.star_edge(u, v, 0.27)
        wave = (ci + cj) * 0.08 - self.t * 0.07             # a slow diagonal wave of colour over the tiles
        img = np.where((star < 0)[..., None], self.colour(wave + 0.0), self.colour(wave + 0.5) * 0.8)
        if self.rosettes:
            img = np.where((rosette < 0)[..., None], self.colour(wave + 0.25), img)
            img = img * np.where(np.abs(rosette) < self.strap * 0.7, 0.3, 1.0)[..., None]
        strap = np.abs(star) < self.strap
        edge = np.abs(np.abs(star) - self.strap) < 0.008
        img = np.where(strap[..., None], np.array([0.95, 0.92, 0.85], np.float32), img)
        img = img * np.where(edge, 0.25, 1.0)[..., None]
        return np.clip(img, 0, 1)

    def lights(self):
        return [self.glow(0, 0.1, 0.1 + 0.008 * self.size), self.glow(1, 0.15 * self.depth),
                self.glow(2, 0.0, 0.1 + 8 * self.strap), self.hue_light()]
