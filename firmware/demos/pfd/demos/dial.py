"""Dial: concentric rings of coloured segments, turning like a combination lock.

After Lee's 0614, its rings. Eight rings, each cut into its own number of
segments in a run of palette colours, turn at their own speeds, some each
way, so the segments slide past each other in shifting patterns. Every so
often (click k0, or each phrase of the music) the lock "opens": every ring
eases round until all their segment boundaries line up on one radius, holds
there for a moment with a flash, then lets go and drifts apart again.
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic

RINGS = 8


class Dial(Chromatic):
    name = "Dial"
    blurb = "Concentric rings of coloured segments turning like a combination lock (after Lee's 0614). k0 speed, k1 segments, k2 rings, k3 colour. Click k0 open the lock, k3 next palette."
    palette = 4

    def __init__(self, rt):
        super().__init__(rt)
        rng = np.random.default_rng(13)
        self.base_segs = rng.integers(3, 9, RINGS)
        self.omega = rng.uniform(0.2, 0.7, RINGS) * np.where(np.arange(RINGS) % 2, 1, -1)
        self.angle = rng.uniform(0, 2 * math.pi, RINGS)
        self.speed, self.seg_mul, self.rings = 1.0, 1.0, RINGS
        self.lock, self.hold, self.flash = 0.0, 0.0, 0.0
        self.r = np.hypot(X - 63.5, Y - 63.5)
        self.theta = np.arctan2(Y - 63.5, X - 63.5) % (2 * math.pi)

    def segs(self):
        return np.maximum(2, np.round(self.base_segs * self.seg_mul)).astype(int)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.speed = max(0.0, min(4.0, self.speed + d * 0.1))
        elif k == 1:
            self.seg_mul = max(0.5, min(3.0, self.seg_mul + d * 0.1))
        elif k == 2:
            self.rings = max(3, min(RINGS, self.rings + (1 if d > 0 else -1)))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.lock = 1.0
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        if self.on_phrase or (self.rt.t - self.t_touch[0] > 20 and int(self.rt.t / 18) != int((self.rt.t - dt) / 18)):
            self.lock = 1.0
        if self.lock > 0:                         # ease every ring to its nearest boundary on the zero radius
            segs = self.segs()
            step = 2 * math.pi / segs
            target = np.round(self.angle / step) * step
            self.angle += (target - self.angle) * (1 - math.exp(-dt / 0.25))
            if np.all(np.abs(target - self.angle) < 0.01):
                self.hold += dt
                if self.hold > 0.2 and self.flash == 0:
                    self.flash = 1.0
                if self.hold > 1.2:
                    self.lock, self.hold = 0.0, 0.0
        else:
            self.angle += self.omega * dt * self.speed * (1 + self.sound[1])
        self.flash = max(0.0, self.flash - dt * 1.5)

    def render(self):
        n = self.rings
        r0, r1 = 8.0, 62.0
        width = (r1 - r0) / n
        ring = np.floor((self.r - r0) / width).astype(int)
        inside = (ring >= 0) & (ring < n)
        ring_c = np.clip(ring, 0, n - 1)
        segs = self.segs()[ring_c]
        a = (self.theta - self.angle[ring_c]) % (2 * math.pi)
        seg = np.floor(a / (2 * math.pi) * segs)
        frac = a / (2 * math.pi) * segs - seg
        img = self.colour(seg / segs * 0.6 + ring_c * 0.11)
        # bevels: dark seams between segments and rings, a little light on each segment's face
        within = (self.r - r0) / width - ring
        seam = (np.minimum(frac, 1 - frac) * (self.r * 2 * math.pi / segs) < 0.9) | (np.minimum(within, 1 - within) < 0.12)
        face = 0.75 + 0.25 * np.sin(math.pi * within)
        img = img * face[..., None]
        img[seam] *= 0.15
        img[~inside] = 0.04
        hub = self.r < r0 - 1
        img[hub] = self.colour(0.0)[None, :] * (0.4 + 0.6 * self.flash)
        img = img + self.flash * 0.4 * inside[..., None]
        return np.clip(img * (1 + 0.2 * self.beat), 0, 1)

    def lights(self):
        return [self.glow(0, 0.3, 0.2 + 0.15 * self.speed), self.glow(1, 0.6, 0.2 + 0.2 * self.seg_mul),
                self.glow(2, self.rings / RINGS), self.hue_light()]
