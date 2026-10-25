"""Wallpaper: a moving colour field folded through the wallpaper groups.

After SeungHun's 0619, its repeating patterned lines. A plane can be tiled
symmetrically in exactly seventeen ways (the wallpaper groups); here are five.
Each folds every point back into one small fundamental region, by mirrors
and turns, before reading a flowing colour field there, so whatever the field
does is repeated with that group's symmetry everywhere at once:
    p4m   square mirrors and diagonals (a kaleidoscope of squares)
    p6m   hexagonal mirrors (snowflake order)
    p4    quarter turns without mirrors (pinwheels)
    pmm   rectangular mirrors only
    p3    third turns round hexagon centres (triskeles)
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic

GROUPS = ["p4m", "p6m", "p4", "pmm", "p3"]
SQRT3 = math.sqrt(3)


def _hex_centre(x, y, size):
    """The nearest centre of a hexagonal lattice (pointy-top), for every point."""
    q = (SQRT3 / 3 * x - y / 3) / size
    r = (2 / 3 * y) / size
    s = -q - r
    rq, rr, rs = np.rint(q), np.rint(r), np.rint(s)
    dq, dr, ds = np.abs(rq - q), np.abs(rr - r), np.abs(rs - s)
    fix_q = (dq > dr) & (dq > ds)
    fix_r = ~fix_q & (dr > ds)
    rq = np.where(fix_q, -rr - rs, rq)
    rr = np.where(fix_r, -rq - rs, rr)
    return size * SQRT3 * (rq + rr / 2), size * 1.5 * rr


class Wallpaper(Chromatic):
    name = "Wallpaper"
    blurb = "A moving colour field folded through the wallpaper groups (after SeungHun's 0619). k0 tile size, k1 group, k2 field speed, k3 colour. Click k1 hold still, k3 next palette."
    palette = 2

    def __init__(self, rt):
        super().__init__(rt)
        self.size, self.group, self.speed = 22.0, 0, 1.0
        self.still = False
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.size = max(10.0, min(60.0, self.size * 1.05 ** d))
        elif k == 1:
            self.group = (self.group + (1 if d > 0 else -1)) % len(GROUPS)
        elif k == 2:
            self.speed = max(0.0, min(4.0, self.speed + d * 0.1))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 1:
            self.still = not self.still
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        if not self.still:
            self.t += dt * self.speed * (1 + self.sound[1])
        if self.on_phrase:
            self.group = (self.group + 1) % len(GROUPS)

    def fold(self):
        """Every pixel's place in the group's fundamental region, as (u, v) in tile units."""
        s = self.size * (1 - 0.08 * self.beat)
        x, y = X - 63.5, Y - 63.5
        g = GROUPS[self.group]
        if g in ("p4m", "pmm", "p4"):
            u, v = x / s, y / s
            if g == "p4":                                    # quarter-turn the cell's quadrants into one
                cu, cv = np.floor(u) + 0.5, np.floor(v) + 0.5
                du, dv = u - cu, v - cv
                quad = (du < 0).astype(int) * 2 + (dv < 0).astype(int)
                for q, (a, b, c, d) in enumerate([(1, 0, 0, 1), (0, -1, 1, 0), (0, 1, -1, 0), (-1, 0, 0, -1)]):
                    m = quad == q
                    du[m], dv[m] = a * du[m] + b * dv[m], c * du[m] + d * dv[m]
                return du, dv
            u = np.abs((u % 2) - 1)                          # mirror across every cell edge
            v = np.abs((v % 2) - 1) * (0.6 if g == "pmm" else 1)
            if g == "p4m":                                   # and the diagonal
                u, v = np.maximum(u, v), np.minimum(u, v)
            return u, v
        cx, cy = _hex_centre(x, y, s)
        dx, dy = (x - cx) / s, (y - cy) / s
        r, a = np.hypot(dx, dy), np.arctan2(dy, dx)
        if g == "p6m":
            w = math.pi / 6
            a = np.abs((a % (2 * w)) - w)                    # twelve mirrored wedges
        else:
            a = a % (2 * math.pi / 3)                        # three turns, no mirror
        return r * np.cos(a), r * np.sin(a)

    def render(self):
        u, v = self.fold()
        t = self.t
        f = (np.sin(u * 5 + t) + np.sin(v * 6 - t * 0.8) + np.sin((u + v) * 4 + t * 0.6)
             + np.sin(np.hypot(u - 0.3, v - 0.2) * 9 - t * 1.3)) / 4
        img = self.colour(f * 0.7 + t * 0.02)
        ridge = 0.5 + 0.5 * np.cos(f * math.pi * 6)
        img = img * (0.55 + 0.45 * ridge)[..., None]
        return np.clip(img * (1 + 0.2 * self.beat), 0, 1)

    def lights(self):
        return [self.glow(0, 0.6, 0.1 + 0.01 * self.size), self.glow(1, self.group / len(GROUPS)),
                self.glow(2, 0.3, 0.2 + 0.15 * self.speed), self.hue_light()]
