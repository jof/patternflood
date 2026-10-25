"""Droplets on a pool: a wave-equation surface refracting a tiled floor.

After SeungHun's 0524-2 (droplet ripple refraction) and 0530 (liquid water
surface), made playable: four droppers, one per knob. Turn to slide a dropper
along its lane, click to drip, hold to rain. Ripples from different droppers
cross and interfere.
"""
import math
import random

import numpy as np

from .. import draw
from ..draw import N
from .squash import COLOURS
from ..runtime import Demo

C2 = 0.24               # wave speed^2 (stable below 0.5)
DAMP = 0.993
LANES = [22, 50, 78, 106]
RAIN_S = 0.11


def _floor():
    """Pool tiles: 16 px squares with grout, a little variation per tile."""
    y, x = np.mgrid[0:N, 0:N]
    tile = ((x // 16) * 7 + (y // 16) * 13) % 5
    base = np.stack([0.05 + 0.02 * tile, 0.30 + 0.04 * tile, 0.45 + 0.05 * tile], axis=-1)
    grout = ((x % 16) < 1) | ((y % 16) < 1)
    base[grout] = (0.55, 0.75, 0.8)
    # a mosaic stripe, as pools have, so refraction has something to bend
    stripe = (np.abs(y - 64) < 3) & ((x // 4 + y // 4) % 2 == 0)
    base[stripe] = (0.9, 0.55, 0.2)
    return base.astype(np.float32)


FLOOR = _floor()


class Droplet(Demo):
    name = "Droplet"
    blurb = "A pool, after SeungHun's 0524-2. Each knob owns a dropper: turn to slide it, click to drip, hold to rain."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.u = np.zeros((N, N), np.float32)
        self.prev = np.zeros((N, N), np.float32)
        self.x = [32.0, 56.0, 72.0, 96.0]
        self.t_drop = [-10.0] * 4
        self.t_rain = [0.0] * 4

    def turn(self, k, d):
        self.x[k] = min(N - 4.0, max(3.0, self.x[k] + self.rt.accel(k, d) * 1.5))

    def press(self, k):
        self.drop(k, 1.0)

    def drop(self, k, size):
        x, y = self.x[k], LANES[k]
        r = 3.0 * size
        x0, x1, y0, y1 = int(x - 5), int(x + 6), int(y - 5), int(y + 6)
        d2 = (draw.X[y0:y1, x0:x1] - x) ** 2 + (draw.Y[y0:y1, x0:x1] - y) ** 2
        self.u[y0:y1, x0:x1] -= 6.0 * size * np.exp(-d2 / (r * r))
        self.t_drop[k] = self.rt.t

    def step(self, dt):
        t = self.rt.t
        for k in range(4):
            if self.rt.held_for(k) > 0.3 and t - self.t_rain[k] > RAIN_S:
                self.t_rain[k] = t
                saved = self.x[k]
                self.x[k] = min(N - 4.0, max(3.0, saved + self.rng.uniform(-6, 6)))
                self.drop(k, self.rng.uniform(0.35, 0.6))
                self.x[k] = saved
        for _ in range(max(1, min(4, int(round(dt * 120))))):
            u = self.u
            lap = (np.roll(u, 1, 0) + np.roll(u, -1, 0) + np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4 * u)
            new = (2 * u - self.prev + C2 * lap) * DAMP
            new[0, :] = new[-1, :] = new[:, 0] = new[:, -1] = 0      # the pool's walls
            self.prev, self.u = u, new

    def render(self):
        u = self.u
        gx = (np.roll(u, -1, 1) - np.roll(u, 1, 1)) * 0.5
        gy = (np.roll(u, -1, 0) - np.roll(u, 1, 0)) * 0.5
        # refraction: look at the floor through the slope of the surface
        sx = np.clip(np.rint(draw.X + gx * 6), 0, N - 1).astype(np.int32)
        sy = np.clip(np.rint(draw.Y + gy * 6), 0, N - 1).astype(np.int32)
        img = FLOOR[sy, sx]
        lap = (np.roll(u, 1, 0) + np.roll(u, -1, 0) + np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4 * u)
        caustic = np.clip(-lap * 0.5, -0.15, 0.6)                   # converging light brightens the floor
        spec = np.clip((gx - gy) * 0.35, 0, 1) ** 2                  # glints facing the light, top-left
        img = img * (1 + caustic[..., None]) + spec[..., None] * 0.9
        for k in range(4):
            flash = max(0.0, 1 - (self.rt.t - self.t_drop[k]) / 0.3)
            c = np.array(COLOURS[k], np.float32)
            draw.ring(img, self.x[k], LANES[k], 2.2, c * (0.6 + 0.4 * flash))
        return img

    def lights(self):
        out = []
        for k in range(4):
            flash = max(0.0, 1 - (self.rt.t - self.t_drop[k]) / 0.25)
            out.append(tuple(v * (0.25 + 0.75 * flash) for v in COLOURS[k]))
        return out
