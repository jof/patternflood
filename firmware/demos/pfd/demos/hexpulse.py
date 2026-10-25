"""Hex Pulse: a honeycomb of tiles that ripples with waves of colour.

After SeungHun's 0528, its dots in a grid. The screen is tiled with hexagons; each
takes one colour, read from a wave field at its centre, so the waves move
across the honeycomb tile by tile. The field is rings spreading from points
that wander, or plane waves crossing, or a turning spiral. Each tile is
bevelled (lit along its upper edges, shadowed along its lower) and set
slightly apart from its neighbours, so the grid reads as tiles. Click k1 to
drop a ripple; with music, every kick drops one.
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic
from .wallpaper import SQRT3, _hex_centre

FIELDS = ["rings", "planes", "spiral"]


class HexPulse(Chromatic):
    name = "Hex Pulse"
    blurb = "A honeycomb rippling with waves of colour (after SeungHun's 0528). k0 tile size, k1 wave speed, k2 wave kind, k3 colour. Click k0 gaps, k1 drop a ripple, k3 next palette."
    palette = 3

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.size, self.speed, self.field_i = 6.0, 1.0, 0
        self.gaps = True
        self.drops = []                      # (x, y, t0)
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.size = max(3.0, min(16.0, self.size + d * 0.25))
        elif k == 1:
            self.speed = max(0.0, min(4.0, self.speed + d * 0.1))
        elif k == 2:
            self.field_i = (self.field_i + (1 if d > 0 else -1)) % len(FIELDS)
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.gaps = not self.gaps
        elif k == 1:
            self.drop()
        elif k == 3:
            self.next_palette()

    def drop(self):
        self.drops = self.drops[-5:] + [(float(self.rng.uniform(-50, 50)), float(self.rng.uniform(-50, 50)), self.t)]

    def step(self, dt):
        self.hear(dt)
        self.t += dt * self.speed * (1 + self.sound[1])
        if self.on_beat and self.rt.audio.kick > 0.6:
            self.drop()
        if self.on_phrase:
            self.field_i = (self.field_i + 1) % len(FIELDS)

    def field(self, x, y):
        t = self.t
        kind = FIELDS[self.field_i]
        if kind == "rings":
            f = np.zeros_like(x)
            for i in range(3):
                cx, cy = 40 * math.sin(t * (0.21 + 0.07 * i) + i * 2), 40 * math.cos(t * (0.17 + 0.05 * i) + i)
                f += np.sin(np.hypot(x - cx, y - cy) * 0.07 - t * 1.6)     # waves several tiles long
            f /= 3
        elif kind == "planes":
            f = (np.sin(x * 0.06 + y * 0.03 - t * 1.4) + np.sin(-x * 0.025 + y * 0.065 + t * 1.0)) / 2
        else:
            f = np.sin(np.arctan2(y, x) * 2 + np.hypot(x, y) * 0.06 - t * 1.6)
        for dx, dy, t0 in self.drops:         # dropped ripples, spreading and fading
            age = t - t0
            ring = np.exp(-((np.hypot(x - dx, y - dy) - 40 * age) / 6) ** 2) * math.exp(-age * 0.7)
            f = f + 1.6 * ring
        return f

    def render(self):
        s = self.size
        x, y = X - 63.5, Y - 63.5
        cx, cy = _hex_centre(x, y, s)
        f = self.field(cx, cy)                      # one value per tile: read at its centre
        img = self.colour(f * 0.35 + self.t * 0.03)
        # bevel and gap, from where the pixel sits within its tile
        dx, dy = (x - cx) / s, (y - cy) / s
        a = np.arctan2(dy, dx)
        r = np.hypot(dx, dy)
        edge_r = (SQRT3 / 2) / np.cos(((a - math.pi / 6) % (math.pi / 3)) - math.pi / 6)   # the hexagon's own edge
        inner = r / edge_r                          # 0 at the centre, 1 at the edge
        bevel = np.where(inner > 0.72, 1 - 0.55 * np.clip(dy / (r + 1e-6), -1, 1), 1.0)
        img = img * (bevel * (0.85 + 0.25 * (0.5 + 0.5 * f)))[..., None]
        if self.gaps:
            img[inner > 0.9] *= 0.15
        return np.clip(img, 0, 1)

    def lights(self):
        return [self.glow(0, 0.55, 0.1 + 0.04 * self.size), self.glow(1, 0.3, 0.2 + 0.15 * self.speed),
                self.glow(2, self.field_i / 3), self.hue_light()]
