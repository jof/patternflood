"""Neon: a neon sign buzzing on a brick wall at night, dithered in three glowing inks.

After Lee's 0622, its bright outlines on black. Each sign is a few glass tubes
(polylines) in pink, cyan or amber. Every colour is its own plate, as in Riso:
the tubes' cores and their soft glow are dithered onto that plate separately,
and the plates add up where they overlap. The glow lights the bricks nearby.
The tubes hum (a faint steady flicker), and now and then one fails for a
moment: it stutters, drops out and catches again. Four signs: OPEN, a cocktail
bar, a palm under a setting sun, and a heart with an arrow.
"""
import math

import numpy as np

from .. import ink
from ..draw import N, X, Y
from .original import Inked

INKS = [(1.0, 0.18, 0.62), (0.15, 0.85, 1.0), (1.0, 0.62, 0.12)]       # pink, cyan, amber


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def _arc(cx, cy, r, a0, a1, n=24, ry=None):
    a = np.linspace(a0, a1, n)
    return list(zip(cx + r * np.cos(a), cy + (ry or r) * np.sin(a)))


def _signs():
    """Each sign: a list of (ink index, polyline)."""
    open_ = [(1, _rect(8, 34, 120, 94))]
    open_ += [(0, _arc(28, 64, 10, 0, 2 * math.pi, 28, 16))]                                   # O
    open_ += [(0, [(46, 80), (46, 48), (58, 48)] + _arc(58, 56, 8, -math.pi / 2, math.pi / 2, 12) + [(46, 64)])]  # P
    open_ += [(0, [(84, 48), (70, 48), (70, 80), (84, 80)]), (0, [(70, 64), (81, 64)])]       # E
    open_ += [(0, [(92, 80), (92, 48), (108, 80), (108, 48)])]                                # N
    bar = [(1, [(24, 22), (64, 62), (104, 22), (24, 22)]), (1, [(64, 62), (64, 92)]), (1, [(46, 96), (82, 96)])]
    bar += [(0, _arc(76, 34, 5, 0, 2 * math.pi, 16)), (0, [(76, 34), (92, 14)])]
    bar += [(2, [(30, 124), (30, 108), (34, 108)] + _arc(34, 112, 4, -math.pi / 2, math.pi / 2, 8) + [(30, 116), (35, 116)]
             + _arc(35, 120, 4, -math.pi / 2, math.pi / 2, 8) + [(30, 124)]),
            (2, [(46, 124), (54, 108), (62, 124)]), (2, [(49, 118), (59, 118)]),
            (2, [(70, 124), (70, 108), (78, 108)] + _arc(78, 112, 4, -math.pi / 2, math.pi / 2, 8) + [(70, 116), (80, 124)])]
    palm = [(2, _arc(84, 46, 22, math.pi, 2 * math.pi, 24) + [(62, 46)])]                     # the sun, half set
    palm += [(2, [(66, 54), (102, 54)]), (2, [(72, 62), (96, 62)])]
    palm += [(1, [(40, 112), (42, 90), (46, 70), (52, 50)])]                                  # trunk
    for a, l in ((-2.6, 26), (-2.0, 22), (-1.2, 24), (-0.5, 26), (0.1, 20)):                  # fronds
        pts = [(52 + l * k / 6 * math.cos(a + 0.25 * k / 6), 50 + l * k / 6 * math.sin(a + 0.25 * k / 6) + 4 * (k / 6) ** 2) for k in range(7)]
        palm.append((1, pts))
    palm += [(0, [(8, 116), (120, 116)])]
    heart = [(0, _arc(48, 50, 16, math.pi * 0.8, math.pi * 2.0, 20) + _arc(80, 50, 16, math.pi, math.pi * 2.2, 20) + [(64, 100)] + [(36, 60)])]
    heart += [(2, [(16, 96), (110, 30)]), (2, [(110, 30), (98, 31)]), (2, [(110, 30), (106, 41)])]
    heart += [(1, [(16, 96), (10, 92)]), (1, [(16, 96), (12, 102)])]
    return [open_, bar, palm, heart]


def _blur(a, passes=3):
    for _ in range(passes):
        a = (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1) + a) / 5
    return a


class Neon(Inked):
    name = "Neon"
    blurb = "A neon sign buzzing on a brick wall, each colour its own dithered plate (after Lee's 0622). k0 glow, k1 sign, k2 screen, k3 wall inks. Click k0 a failing tube, k1 lights out, k2 chunky."
    palette, screen_kind = "silver", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.signs = _signs()
        self.sign = 0
        self.glow_amt = 1.0
        self.on = True
        self.failing, self.fail_left = -1, 0.0
        self.t = 0.0
        self._paths()
        # the wall: bricks in courses, each offset half a brick from the last
        course = (Y // 6).astype(int)
        bx = (X + 7 * (course % 2)) % 14
        mortar = ((Y % 6) < 1) | (bx < 1)
        rng = np.random.default_rng(2)
        shade = rng.uniform(0.75, 1.0, (N // 6 + 2, N // 14 + 3))[course, ((X + 7 * (course % 2)) // 14).astype(int)]
        self.wall = np.where(mortar, 0.05, 0.13 * shade).astype(np.float32)

    def _paths(self):
        """Rasterize the current sign's tubes into one mask per tube."""
        self.tubes = []
        for c, pts in self.signs[self.sign]:
            m = np.zeros((N, N), np.float32)
            for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
                n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 2
                xs, ys = np.linspace(x0, x1, n), np.linspace(y0, y1, n)
                for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):          # tubes two pixels thick
                    xi, yi = np.clip((xs + ox).astype(int), 0, N - 1), np.clip((ys + oy).astype(int), 0, N - 1)
                    m[yi, xi] = 1.0
            self.tubes.append((c, m))
        self.offsets = [ink.screen(ink.SCREENS[self.screen_i], self.scale, angle=0.3 + 0.5 * p, pitch=3.0) for p in range(3)]

    def set_screen(self):
        super().set_screen()
        if hasattr(self, "tubes"):
            self._paths()

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.glow_amt = max(0.2, min(2.0, self.glow_amt + d * 0.05))
        elif k == 1:
            self.sign = (self.sign + (1 if d > 0 else -1)) % len(self.signs)
            self._paths()
        elif k == 3:
            self.turn_ink(k, d)
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.failing, self.fail_left = int(self.rng.integers(len(self.tubes))), 2.5
        elif k == 1:
            self.on = not self.on
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        self.fail_left -= dt
        if self.fail_left <= 0 and self.rng.random() < dt / 9:
            self.failing, self.fail_left = int(self.rng.integers(len(self.tubes))), self.rng.uniform(0.8, 2.5)
        if self.on_phrase or (min(self.rt.t - t for t in self.t_touch) > 30
                              and int(self.rt.t / 25) != int((self.rt.t - dt) / 25)):
            self.sign = (self.sign + 1) % len(self.signs)
            self._paths()

    def render(self):
        plates = np.zeros((3, N, N), np.float32)
        for i, (c, m) in enumerate(self.tubes):
            level = 0.93 + 0.07 * math.sin(self.t * 120 + i)                  # the hum
            if i == self.failing and self.fail_left > 0:                     # a tube on its way out
                level *= float(self.rng.random() < 0.45) * self.rng.uniform(0.3, 1.0)
            if not self.on:
                level = 0.0
            level *= 1 + 0.4 * self.beat
            plates[c] = np.maximum(plates[c], m * level)
        glows = np.stack([_blur(p, 7) for p in plates]) * 4.0 * self.glow_amt
        # the wall, lit by the glow, through the palette
        lit = glows.sum(0)
        img = self.print(np.clip(self.wall * (1 + 3.5 * lit) + 0.05 * lit, 0, 1))
        # each colour's plate: the core solid, its glow dithered at half strength
        for c in range(3):
            core = plates[c] > 0.5
            haze = np.clip(glows[c], 0, 1) > self.offsets[c] * 0.9 + 0.05
            col = np.asarray(INKS[c], np.float32)
            img = np.where(haze[..., None], np.maximum(img, col * 0.45), img)
            img = np.where(core[..., None], np.clip(img + col * plates[c][..., None], 0, 1), img)
        return img

    def lights(self):
        return [tuple(0.5 * v for v in INKS[self.sign % 3]), self.glow(1, self.sign / 4)] + self.ink_lights()
