"""Warp: a starfield at cruise, and the jump to hyperspace, dithered.

After Lee's 0510's scattered points. Stars sit in a 3D box ahead and stream
past the ship. Each is drawn as a streak from where it is now to where it
was a moment ago, so at cruise they're points and at speed they stretch into
lines. A jump (click k0, or a big hit in the music) winds the speed up until
the streaks fill a tunnel of light, holds there with the tunnel glowing
blue, then drops out with a flash among new stars. Turning k1 steers: the
vanishing point slides and the whole field swings.
"""
import math

import numpy as np

from ..draw import N
from .original import Inked

NSTARS = 900
DEPTH = 60.0
FOCAL = 60.0
SAMPLES = 10                    # points along each streak


class Warp(Inked):
    name = "Warp"
    blurb = "Stars streaming past, and the jump to hyperspace, dithered (after Lee's 0510). k0 throttle, k1 steer, k2 screen, k3 inks. Click k0 jump, k2 chunky."
    palette, screen_kind = "ice", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.s = self._new(NSTARS, spread=True)
        self.throttle, self.speed = 1.0, 1.0
        self.steer, self.yaw = 0.0, 0.0
        self.jump = -1.0                # time into a jump, or < 0
        self.flash = 0.0
        self.t = 0.0

    def _new(self, n, spread=False):
        r = self.rng
        z = r.uniform(0.5, DEPTH, n) if spread else r.uniform(DEPTH * 0.8, DEPTH, n)
        return np.column_stack([r.uniform(-20, 20, n), r.uniform(-20, 20, n), z, r.uniform(0.4, 1, n)]).astype(np.float32)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.throttle = max(0.0, min(8.0, self.throttle + d * 0.2))
        elif k == 1:
            self.steer = max(-1.0, min(1.0, self.steer + d * 0.04))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0 and self.jump < 0:
            self.jump = 0.0
        elif k == 2:
            self.chunky()

    def warp_speed(self):
        """Speed through a jump: wind up (2 s), hold in hyperspace (4 s), drop out."""
        j = self.jump
        if j < 0:
            return 0.0
        if j < 2:
            return (j / 2) ** 3 * 120
        if j < 6:
            return 120.0
        return 0.0

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        if self.jump >= 0:
            self.jump += dt
            if self.jump >= 6:                  # drop out: a flash, and a fresh sky
                self.jump, self.flash = -1.0, 1.0
                self.s = self._new(NSTARS, spread=True)
        elif self.listening and self.rt.audio.impact_hit:
            self.jump = 0.0
        if not self.listening and self.jump < 0 and min(self.rt.t - t for t in self.t_touch) > 30 \
                and int(self.rt.t / 40) != int((self.rt.t - dt) / 40):
            self.jump = 0.0                     # left alone, a jump every 40 s
        self.flash *= math.exp(-dt / 0.25)
        cruise = self.throttle * 2.5 * (1 + 2 * self.sound[2] + 1.5 * self.beat)
        self.speed = cruise + self.warp_speed()
        self.yaw += (self.steer - self.yaw) * (1 - math.exp(-dt / 0.6))
        s = self.s
        s[:, 2] -= self.speed * dt
        s[:, 0] -= self.yaw * 8 * dt * (1 + self.speed * 0.05)
        gone = (s[:, 2] < 0.3) | (np.abs(s[:, 0]) > 30)
        s[gone] = self._new(gone.sum())

    def render(self):
        s = self.s
        cx = 63.5 - self.yaw * 30
        trail = min(DEPTH * 0.5, 0.03 + self.speed * 0.045)            # how far back the streak reaches
        k = np.linspace(0, 1, SAMPLES, dtype=np.float32)[None, :]
        z = s[:, 2:3] + trail * k
        px = cx + s[:, 0:1] / z * FOCAL
        py = 63.5 + s[:, 1:2] / z * FOCAL
        near = np.clip(1.5 - s[:, 2:3] / DEPTH * 1.4, 0.1, 1.0)
        b = (s[:, 3:4] * near * (1 - 0.6 * k)).ravel()
        xi, yi = np.rint(px).astype(np.int32).ravel(), np.rint(py).astype(np.int32).ravel()
        ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
        tone = np.zeros((N, N), np.float32)
        np.maximum.at(tone, (yi[ok], xi[ok]), b[ok])
        hyper = self.warp_speed() / 120
        if hyper > 0:                                                # the tunnel's glow
            yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
            r = np.hypot(xx - cx, yy - 63.5)
            tone = np.maximum(tone, hyper * (0.3 * np.exp(-((r - 50) / 25) ** 2) + 0.5 * np.exp(-r / 8)))
        return self.print(np.clip(tone + self.flash * 0.9, 0, 1))

    def lights(self):
        return [self.glow(0, 0.6, 0.2 + 0.1 * self.throttle), self.glow(1, 0.55, 0.2 + 0.3 * abs(self.steer))] + self.ink_lights()
