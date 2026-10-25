"""Caustics: sunlight through moving water, gathering into bright nets on a pool floor.

After SeungHun's 0530, whose glowing net looks like them. The water's surface is a
few crossing waves plus the rings from dropped pebbles. Light through each
point of the surface bends by the surface's slope and lands on the floor
somewhere else; counting where it all lands (each point's light spread over
the four nearest floor pixels) gives the caustics. Where the surface focuses
light, the floor blazes; where it spreads it, the floor goes dim. The tiles
seen through the water wobble by the same refraction. Dithered into inks.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

NWAVES = 6


class Caustics(Inked):
    name = "Caustics"
    blurb = "Sunlight through water, netting a pool floor; dithered (after SeungHun's 0530). k0 chop, k1 depth (focus), k2 screen, k3 inks. Click k0 drop a pebble, k1 tiles, k2 chunky."
    palette, screen_kind = "pool", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        rng = np.random.default_rng(6)
        ang = rng.uniform(0, 2 * math.pi, NWAVES)
        k = 2 * math.pi / np.geomspace(70, 18, NWAVES)
        self.kx, self.ky = (np.cos(ang) * k).astype(np.float32), (np.sin(ang) * k).astype(np.float32)
        self.omega = (np.sqrt(k) * 4.0).astype(np.float32)
        self.amp = (1.0 / k * 0.35).astype(np.float32)
        self.phase = rng.uniform(0, 2 * math.pi, NWAVES).astype(np.float32)
        self.chop, self.depth = 1.0, 0.4
        self.tiles = True
        self.drops = []                     # (x, y, t0)
        self.rng = rng
        self.t = 0.0
        self.level = None

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.chop = max(0.2, min(1.6, self.chop * 1.07 ** d))
        elif k == 1:
            self.depth = max(0.12, min(1.4, self.depth * 1.05 ** d))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.drop()
        elif k == 1:
            self.tiles = not self.tiles
        elif k == 2:
            self.chunky()

    def drop(self, x=None, y=None):
        x = self.rng.uniform(20, 108) if x is None else x
        y = self.rng.uniform(20, 108) if y is None else y
        self.drops = [d for d in self.drops if self.t - d[2] < 6][-5:] + [(x, y, self.t)]

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        if self.on_beat and self.rt.audio.kick > 0.6:
            self.drop()
        elif not self.listening and self.rng.random() < dt / 5:     # now and then, a pebble
            self.drop()

    def surface_slope(self):
        """The water's slope (d/dx, d/dy) at every pixel: waves plus spreading rings."""
        a = self.amp * self.chop * (1 + 0.8 * self.sound[2])
        arg = X[..., None] * self.kx + Y[..., None] * self.ky - self.omega * self.t + self.phase
        c = np.cos(arg) * a
        sx, sy = c @ self.kx, c @ self.ky
        for x0, y0, t0 in self.drops:
            age = self.t - t0
            dx, dy = X - x0, Y - y0
            r = np.sqrt(dx * dx + dy * dy) + 1e-3
            front = 30 * age                                     # the ring spreads at 30 px/s
            env = np.exp(-((r - front) / 10) ** 2) * math.exp(-age / 1.8) * 1.4
            g = env * np.cos(0.6 * (r - front))                  # radial slope of the ring
            sx, sy = sx + g * dx / r, sy + g * dy / r
        return sx, sy

    def render(self):
        sx, sy = self.surface_slope()
        reach = 22.0 * self.depth                                # how far a slope throws the light
        fx, fy = X - sx * reach, Y - sy * reach
        # light lands on the floor: splat each pixel's share over the four floor pixels around it
        x0, y0 = np.floor(fx), np.floor(fy)
        ax, ay = fx - x0, fy - y0
        x0, y0 = x0.astype(np.int64) % N, y0.astype(np.int64) % N
        x1, y1 = (x0 + 1) % N, (y0 + 1) % N
        light = np.zeros(N * N, np.float32)
        for yy, xx, w in ((y0, x0, (1 - ax) * (1 - ay)), (y0, x1, ax * (1 - ay)),
                          (y1, x0, (1 - ax) * ay), (y1, x1, ax * ay)):
            light += np.bincount((yy * N + xx).ravel(), weights=w.ravel(), minlength=N * N)
        light = light.reshape(N, N)
        light = (light + np.roll(light, 1, 0) + np.roll(light, 1, 1) + np.roll(light, (1, 1), (0, 1))) / 4
        # the floor, seen through the same water: tile grout wobbles
        floor = np.full((N, N), 0.55, np.float32)
        if self.tiles:
            gx, gy = (X + sx * reach * 0.3) % 16, (Y + sy * reach * 0.3) % 16
            floor = np.where((gx < 1.2) | (gy < 1.2), 0.25, floor)
        caust = np.clip(light - 0.6, 0, None) ** 1.3
        level = float(np.percentile(caust, 99.5)) + 1e-3
        self.level = level if self.level is None else self.level + (level - self.level) * 0.05
        tone = floor * (0.25 + 0.3 * light) + 0.55 * caust / self.level * (1 + 0.5 * self.beat)
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.5, 0.2 + 0.2 * self.chop), self.glow(1, 0.55, 0.2 + 0.2 * self.depth)] + self.ink_lights()
