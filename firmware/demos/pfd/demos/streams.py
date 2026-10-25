"""Streams: thousands of coloured particles tracing silky trails through a flow.

After Lee's Vector Field Flow. The flow is the curl of a slowly changing sum
of waves (so it swirls without sources or sinks), and eighteen hundred particles
ride it, each leaving a trail on a canvas that fades. Each particle carries a
colour from the palette, by where it was born or by which way it's heading,
so the streams braid into ribbons of colour. Particles live a few seconds and
are reborn somewhere new, so the field keeps being redrawn.
"""
import math

import numpy as np

from ..draw import N
from .original import Chromatic

COUNT = 1800
NWAVES = 5


class Streams(Chromatic):
    name = "Streams"
    blurb = "Thousands of coloured particles tracing silky trails through a flow (after Lee's Vector Field Flow). k0 speed, k1 swirl size, k2 trail length, k3 colour. Click k0 a new flow, k1 colour by heading or birthplace, k3 next palette."
    palette = 0

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.speed, self.scale, self.trail = 1.0, 1.0, 1.0
        self.by_heading = False
        self.canvas = np.zeros((N, N, 3), np.float32)
        self.t = 0.0
        self.new_flow()
        self.p = self.rng.uniform(0, N, (COUNT, 2)).astype(np.float32)
        self.life = self.rng.uniform(0, 5, COUNT).astype(np.float32)
        self.hue = (self.p[:, 0] + self.p[:, 1]) / (2 * N)

    def new_flow(self):
        r = self.rng
        ang = r.uniform(0, 2 * math.pi, NWAVES)
        mag = r.uniform(0.02, 0.06, NWAVES)
        self.k = np.stack([np.cos(ang) * mag, np.sin(ang) * mag], -1).astype(np.float32)
        self.ph = r.uniform(0, 2 * math.pi, NWAVES).astype(np.float32)
        self.om = r.uniform(0.05, 0.2, NWAVES).astype(np.float32)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.speed = max(0.1, min(4.0, self.speed * 1.08 ** d))
        elif k == 1:
            self.scale = max(0.4, min(3.0, self.scale * 1.05 ** d))
        elif k == 2:
            self.trail = max(0.1, min(4.0, self.trail * 1.08 ** d))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.new_flow()
        elif k == 1:
            self.by_heading = not self.by_heading
        elif k == 3:
            self.next_palette()

    def velocity(self, p):
        k = self.k / self.scale
        arg = p @ k.T + self.ph + self.om * self.t
        c = np.cos(arg) / np.sqrt((k ** 2).sum(1))           # each wave's swirl the same speed, whatever its size
        return np.stack([c @ k[:, 1], -(c @ k[:, 0])], -1) * 9

    def step(self, dt):
        self.hear(dt)
        dt = min(dt, 1 / 20)
        self.t += dt
        v = self.velocity(self.p) * self.speed * (1 + 1.5 * self.sound[2] + self.beat)
        old = self.p.copy()
        self.p += v * dt
        self.life -= dt
        dead = (self.life <= 0) | (self.p[:, 0] < 0) | (self.p[:, 0] >= N) | (self.p[:, 1] < 0) | (self.p[:, 1] >= N)
        n = int(dead.sum())
        if n:
            self.p[dead] = self.rng.uniform(0, N, (n, 2))
            self.life[dead] = self.rng.uniform(2, 6, n)
            self.hue[dead] = (self.p[dead, 0] + self.p[dead, 1]) / (2 * N)
            old[dead] = self.p[dead]
        if self.on_phrase:
            self.new_flow()
        self.canvas *= math.exp(-dt / (0.45 * self.trail))
        # draw each particle's step as a short segment (two points), so fast ones don't dot
        hue = np.arctan2(v[:, 1], v[:, 0]) / (2 * math.pi) if self.by_heading else self.hue
        col = self.colour(hue)
        for f in (0.0, 0.5):
            q = old + (self.p - old) * f
            xi, yi = q[:, 0].astype(int), q[:, 1].astype(int)
            ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
            np.maximum.at(self.canvas, (yi[ok], xi[ok]), col[ok])

    def render(self):
        return np.clip(self.canvas * (1 + 0.3 * self.beat), 0, 1)

    def lights(self):
        return [self.glow(0, 0.3, 0.2 + 0.15 * self.speed), self.glow(1, 0.6, 0.2 + 0.2 * self.scale),
                self.glow(2, 0.85, 0.1 + 0.2 * self.trail), self.hue_light()]
