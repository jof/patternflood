"""Girih: star tilings with strapwork that morph from one star to the next.

After SeungHun's 0514, its crosses in a grid, and the zellij of Moroccan
tilework. Each cell of a lattice holds an n-pointed star {n/k}: n tips round
a circle, each joined to the tip k steps along. Every point is folded into one
mirrored wedge of its cell (360 / 2n degrees), where the star's outline is a
single straight edge, so whether a point is inside, and how near the outline,
is one line test. Because k can be any number, not just a whole one, the
star's sharpness turns smoothly from a polygon to a spiky star, and moving
from one star to another blends their outlines, so the tiling morphs. Stars
whose points suit a square lattice (4, 8, 16) sit on one; those that suit a
hexagonal one (6, 12, 10) on that, and a change of lattice dissolves across.
White strapwork traces the outlines; the stars, their inner rosettes and the
spaces between take palette colours that flow across in a diagonal wave.
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic
from .wallpaper import _hex_centre

# (points, lattice) in the order the tiling morphs through
STARS = [(8, "square"), (16, "square"), (4, "square"), (6, "hex"), (12, "hex"), (10, "hex")]
MORPH_S = 2.5
STRAPS = [0.022, 0.035, 0.055]


class Girih(Chromatic):
    name = "Girih"
    blurb = "Star tilings with strapwork that morph from one star to the next (after SeungHun's 0514). k0 tile size, k1 star (morphs), k2 sharpness, k3 colour. Click k0 strap width, k1 auto morph, k2 inner rosettes, k3 next palette."
    palette = 1

    def __init__(self, rt):
        super().__init__(rt)
        self.size, self.sharp = 40.0, 0.65
        self.strap_i, self.rosettes, self.auto = 1, True, True
        self.star, self.prev, self.blend = 0, 0, 1.0       # morphing from prev to star; blend 0..1
        self.t, self.t_star = 0.0, 0.0

    def go_to(self, i):
        i %= len(STARS)
        if i == self.star:
            return
        self.prev, self.star, self.blend = self.star, i, 0.0
        self.t_star = self.t

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.size = max(20.0, min(90.0, self.size * 1.05 ** d))
        elif k == 1:
            self.go_to(self.star + (1 if d > 0 else -1))
        elif k == 2:
            self.sharp = max(0.0, min(1.0, self.sharp + d * 0.02))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.strap_i = (self.strap_i + 1) % len(STRAPS)
        elif k == 1:
            self.auto = not self.auto
        elif k == 2:
            self.rosettes = not self.rosettes
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        self.t += dt * (1 + self.sound[1])
        self.blend = min(1.0, self.blend + dt / MORPH_S)
        idle = self.rt.t - self.t_touch[1] > 15
        if self.on_phrase or (self.auto and idle and self.blend >= 1 and self.t - self.t_star > 12):
            self.go_to(self.star + 1)

    def cell(self, lattice):
        """Each pixel's offset from its cell centre, in units of the centre-to-centre spacing,
        and its cell's index (for the colour wave)."""
        s = self.size * (1 + 0.04 * self.beat)
        x, y = X - 63.5, Y - 63.5
        if lattice == "square":
            ci, cj = np.floor(x / s + 0.5), np.floor(y / s + 0.5)
            return x / s - ci, y / s - cj, ci + cj
        hs = s / math.sqrt(3)                                # hex size whose neighbours are s apart
        cx, cy = _hex_centre(x, y, hs)
        return (x - cx) / s, (y - cy) / s, (cx + cy) / s

    def star_edge(self, u, v, n, radius):
        """Signed distance-ish from the star {n/k} of this radius (negative inside), k set by sharpness."""
        r = np.hypot(u, v)
        w = math.pi / n
        a = np.abs((np.arctan2(v, u) % (2 * w)) - w)        # fold into one mirrored wedge, 0..pi/n from a tip
        a = w - a
        pu, pv = r * np.cos(a), r * np.sin(a)
        k = 1 + self.sharp * (n / 2 - 1.25)                  # 1: a polygon; up towards n/2: a spiky star
        b = 2 * math.pi * k / n
        ax, ay = radius, 0.0
        bx, by = radius * math.cos(b), radius * math.sin(b)
        ex, ey = bx - ax, by - ay
        ln = math.hypot(ex, ey)
        nx, ny = ey / ln, -ex / ln
        if nx * -ax + ny * -ay > 0:                          # point the normal away from the centre
            nx, ny = -nx, -ny
        return (pu - ax) * nx + (pv - ay) * ny

    def shape(self, i):
        """The star, rosette and wave fields for star i on its own lattice."""
        n, lattice = STARS[i]
        u, v, idx = self.cell(lattice)
        return self.star_edge(u, v, n, 0.5), self.star_edge(u, v, n, 0.27), idx

    def paint(self, star, rosette, idx):
        strap = STRAPS[self.strap_i]
        wave = idx * 0.08 - self.t * 0.07
        img = np.where((star < 0)[..., None], self.colour(wave), self.colour(wave + 0.5) * 0.8)
        if self.rosettes:
            img = np.where((rosette < 0)[..., None], self.colour(wave + 0.25), img)
            img = img * np.where(np.abs(rosette) < strap * 0.7, 0.3, 1.0)[..., None]
        img = np.where((np.abs(star) < strap)[..., None], np.array([0.95, 0.92, 0.85], np.float32), img)
        return img * np.where(np.abs(np.abs(star) - strap) < 0.008, 0.25, 1.0)[..., None]

    def render(self):
        f = self.blend * self.blend * (3 - 2 * self.blend)
        if f >= 1:
            return np.clip(self.paint(*self.shape(self.star)), 0, 1)
        a, b = self.shape(self.prev), self.shape(self.star)
        if STARS[self.prev][1] == STARS[self.star][1]:      # same lattice: blend the outlines themselves
            return np.clip(self.paint(*(x * (1 - f) + y * f for x, y in zip(a, b))), 0, 1)
        return np.clip(self.paint(*a) * (1 - f) + self.paint(*b) * f, 0, 1)    # a new lattice: dissolve across

    def lights(self):
        return [self.glow(0, 0.1, 0.1 + 0.008 * self.size), self.glow(1, self.star / len(STARS)),
                self.glow(2, 0.0, 0.2 + 0.6 * self.sharp), self.hue_light()]
