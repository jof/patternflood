"""Sculpt a landscape, then flood it. Topographic contours after Lee's 0519-1 and 0529.

k0 and k1 move the brush, as in Etch. k2 moves earth: clockwise piles it up
under the brush, anticlockwise digs. k3 is sea level, the reveal: turn it to
watch the water find the valleys you dug.
"""
import math

import numpy as np

from .. import draw
from ..draw import N
from ..runtime import Demo

BRUSHES = [5.0, 9.0, 15.0]
LINE_STEP = 0.08            # height between contour lines

# hypsometric tint, by height above sea level: (height, rgb)
TINT = [(-1.0, (0.0, 0.03, 0.15)), (-0.25, (0.0, 0.15, 0.45)), (-0.02, (0.05, 0.45, 0.65)),
        (0.0, (0.85, 0.8, 0.5)), (0.05, (0.25, 0.6, 0.2)), (0.3, (0.15, 0.4, 0.12)),
        (0.55, (0.45, 0.35, 0.2)), (0.8, (0.6, 0.6, 0.6)), (1.0, (1.0, 1.0, 1.0))]


def _tint(h):
    xs = np.array([p for p, _ in TINT], np.float32)
    cs = np.array([c for _, c in TINT], np.float32)
    h = np.clip(h, xs[0], xs[-1])
    return np.stack([np.interp(h, xs, cs[:, i]) for i in range(3)], axis=-1)


class Terrain(Demo):
    name = "Terrain"
    blurb = "After Lee's contour maps. k0/k1 move the brush, k2 piles earth (anticlockwise digs), k3 sea level. Click k0 smooth, k1 new land, k2 brush size."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.x = self.y = N / 2
        self.brush = 1
        self.sea = 0.0
        self.t_move = -10.0
        self.t_sea = -10.0
        self.new_land()

    def new_land(self):
        h = np.zeros((N, N), np.float32)
        for octave in range(4):
            f = 2 ** octave
            for _ in range(3):
                kx, ky = self.rng.uniform(0.5, 1.5, 2) * f * 2 * math.pi / N
                ph = self.rng.uniform(0, 2 * math.pi)
                h += np.sin(draw.X * kx + draw.Y * ky + ph) * 0.35 / f
        self.h = h * 0.6

    def turn(self, k, d):
        if k == 0:
            self.x = min(N - 1.0, max(0.0, self.x + self.rt.accel(0, d)))
            self.t_move = self.rt.t
        elif k == 1:
            self.y = min(N - 1.0, max(0.0, self.y - self.rt.accel(1, d)))
            self.t_move = self.rt.t
        elif k == 2:
            r = BRUSHES[self.brush]
            bump = np.exp(-((draw.X - self.x) ** 2 + (draw.Y - self.y) ** 2) / (r * r))
            self.h += bump * 0.04 * d
            np.clip(self.h, -1, 1, out=self.h)
        elif k == 3:
            self.sea = min(0.9, max(-0.9, self.sea + d * 0.02))
            self.t_sea = self.rt.t

    def release(self, k, click):
        if not click:
            return
        if k == 0:
            for _ in range(3):              # erode a little: a few passes of a soft blur
                self.h = (self.h * 4 + np.roll(self.h, 1, 0) + np.roll(self.h, -1, 0)
                          + np.roll(self.h, 1, 1) + np.roll(self.h, -1, 1)) / 8
        elif k == 1:
            self.new_land()
        elif k == 2:
            self.brush = (self.brush + 1) % len(BRUSHES)

    def render(self):
        rel = self.h - self.sea
        img = _tint(rel).astype(np.float32)
        # hill shade from the light in the top-left (land only)
        gx = np.roll(self.h, -1, 1) - np.roll(self.h, 1, 1)
        gy = np.roll(self.h, -1, 0) - np.roll(self.h, 1, 0)
        shade = np.clip(1 - (gx + gy) * 6, 0.55, 1.35)
        land = rel > 0
        img[land] *= shade[land, None]
        # contour lines where the height crosses a multiple of LINE_STEP
        band = np.floor(self.h / LINE_STEP)
        edge = (band != np.roll(band, 1, 0)) | (band != np.roll(band, 1, 1))
        img[edge & land] *= 0.45
        img[edge & ~land] += 0.06
        coast = land != np.roll(land, 1, 0)
        img[coast | (land != np.roll(land, 1, 1))] = (0.9, 0.95, 1.0)
        # the brush
        a = 1.0 if self.rt.t - self.t_move < 1.5 or self.rt.held(2) else 0.4
        draw.ring(img, self.x, self.y, BRUSHES[self.brush], (a, a, a * 0.6), width=0.7)
        if self.rt.t - self.t_sea < 1.2:
            draw.text(img, f"sea {self.sea:+.2f}", 64, 2, (.8, .9, 1), center=True)
        return img

    def lights(self):
        return [(.5, .5, .4), (.5, .5, .4),
                (.3, .7, .2) if self.rt.k[2].rate > 0 and self.rt.t - self.rt.k[2].t_turn < 0.3 else (.25, .2, .1),
                (0.0, 0.2 + 0.5 * (self.sea + 0.9) / 1.8, 0.6)]
