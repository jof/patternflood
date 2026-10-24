"""Fireworks: aim, hold to charge, let go to launch.

k0 aims (a dotted arc shows the path), hold k1 to charge the shell and release
to fire (longer hold, higher burst), k2 picks colour, k3 the burst. Click k0
for a salvo; click k3 for an automatic show.
"""
import math
import random

import numpy as np

from .. import draw
from ..draw import N, hsv, hsv1
from ..runtime import Demo

G = 100.0                   # px/s^2, downwards
CHARGE_S = 1.2
BURSTS = ["peony", "ring", "willow", "palm", "double"]


class Rocket(Demo):
    name = "Rocket"
    blurb = "Fireworks. k0 aims; hold k1 to charge, let go to launch. k2 colour, k3 burst type. Click k0 for a salvo, k3 for an automatic show."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.aim = 0.0              # radians from vertical, + to the right
        self.hue = 0.08
        self.burst = 0
        self.auto = False
        self.t_auto = 0.0
        self.t_type = -10.0
        self.shells = []            # [x, y, vx, vy, hue, burst]
        self.trail = draw.blank()
        # particles in parallel arrays
        self.p = np.zeros((0, 2), np.float32)
        self.v = np.zeros((0, 2), np.float32)
        self.life = np.zeros(0, np.float32)
        self.life0 = np.zeros(0, np.float32)
        self.col = np.zeros((0, 3), np.float32)
        self.drag = np.zeros(0, np.float32)

    def turn(self, k, d):
        if k == 0:
            self.aim = max(-0.9, min(0.9, self.aim + d * 0.06))
        elif k == 2:
            self.hue = (self.hue + d / 36.0) % 1.0
        elif k == 3:
            self.burst = (self.burst + (1 if d > 0 else -1)) % len(BURSTS)
            self.t_type = self.rt.t

    def release(self, k, click):
        if k == 1:
            power = min(1.0, (self.rt.t - self.rt.k[1].t_down) / CHARGE_S)
            self.launch(self.aim, 0.25 + 0.75 * power, self.hue, BURSTS[self.burst])
        elif k == 0 and click:
            for i in range(5):
                self.launch(-0.5 + 0.25 * i, self.rng.uniform(0.5, 1.0), self.rng.random(), self.rng.choice(BURSTS))
        elif k == 3 and click:
            self.auto = not self.auto

    def _v0(self, power):
        return 62 + 95 * power

    def launch(self, aim, power, hue, burst):
        v = self._v0(power)
        self.shells.append([64.0, N - 2.0, v * math.sin(aim), -v * math.cos(aim), hue, burst])

    def _explode(self, x, y, hue, burst):
        r = self.rng
        if burst == "ring":
            n = 48
            a = np.linspace(0, 2 * np.pi, n, endpoint=False) + r.uniform(0, 1)
            sp = np.full(n, 38.0)
        elif burst == "palm":
            n = 8 * 10
            a = np.repeat(np.linspace(0, 2 * np.pi, 8, endpoint=False), 10) + r.uniform(0, 1)
            sp = np.tile(np.linspace(14, 40, 10), 8)
        else:
            n = 140 if burst != "willow" else 110
            a = np.array([r.uniform(0, 2 * math.pi) for _ in range(n)])
            sp = np.sqrt(np.array([r.random() for _ in range(n)])) * (45 if burst != "willow" else 30)
        vel = np.stack([np.cos(a) * sp, np.sin(a) * sp], axis=1).astype(np.float32)
        life = np.array([r.uniform(1.0, 1.8) if burst != "willow" else r.uniform(2.2, 3.2) for _ in range(n)], np.float32)
        if burst == "willow":
            col = np.tile(np.array([[1, .7, .25]], np.float32), (n, 1))
        else:
            hues = np.full(n, hue) + np.array([r.uniform(-0.03, 0.03) for _ in range(n)])
            if burst == "double":
                hues[n // 2:] += 0.5
                vel[n // 2:] *= 0.55
            col = hsv(hues, np.full(n, 0.85), np.ones(n)).astype(np.float32)
        drag = np.full(n, 1.6 if burst != "willow" else 2.6, np.float32)
        self.p = np.concatenate([self.p, np.tile(np.array([[x, y]], np.float32), (n, 1))])
        self.v = np.concatenate([self.v, vel])
        self.life = np.concatenate([self.life, life])
        self.life0 = np.concatenate([self.life0, life])
        self.col = np.concatenate([self.col, col])
        self.drag = np.concatenate([self.drag, drag])

    def step(self, dt):
        t = self.rt.t
        if self.auto and t - self.t_auto > 0.7:
            self.t_auto = t + self.rng.uniform(0, 0.8)
            self.launch(self.rng.uniform(-0.5, 0.5), self.rng.uniform(0.5, 1.0), self.rng.random(), self.rng.choice(BURSTS))

        self.trail *= math.exp(-6.0 * dt)
        for s in list(self.shells):
            x0, y0 = s[0], s[1]
            s[3] += G * dt
            s[0] += s[2] * dt
            s[1] += s[3] * dt
            xs, ys = draw.segment(x0, y0, s[0], s[1], step=0.7)
            draw.plot(self.trail, xs, ys, (.6, .45, .3), op="max")
            if s[3] >= -5 or s[1] < 4:      # apex: burst
                self.shells.remove(s)
                self._explode(s[0], s[1], s[4], s[5])

        if len(self.life):
            k = np.exp(-self.drag * dt)[:, None]
            self.v *= k
            self.v[:, 1] += G * 0.35 * dt
            self.p += self.v * dt
            self.life -= dt
            keep = (self.life > 0) & (self.p[:, 1] < N + 2)
            self.p, self.v, self.life, self.life0, self.col, self.drag = (
                self.p[keep], self.v[keep], self.life[keep], self.life0[keep], self.col[keep], self.drag[keep])
            a = np.clip(self.life / self.life0, 0, 1) ** 1.5
            # a crackle of sparkle late in life
            sparkle = (a < 0.35) & (np.random.random(len(a)) < 0.5)
            draw.plot(self.trail, self.p[:, 0], self.p[:, 1], self.col * (a[:, None] * 0.9 + sparkle[:, None] * 0.4), op="max")

    def _arc(self, img):
        """The predicted path at the current aim and charge, as dots."""
        held = self.rt.held(1)
        power = min(1.0, self.rt.held_for(1) / CHARGE_S) if held else 0.6
        v = self._v0(0.25 + 0.75 * power)
        vx, vy = v * math.sin(self.aim), -v * math.cos(self.aim)
        apex_t = -vy / G
        for i in range(1, 16):
            tt = apex_t * i / 15
            x, y = 64 + vx * tt, N - 2 + vy * tt + 0.5 * G * tt * tt
            if 0 <= x < N and 0 <= y < N and i % 2 == 0:
                a = 0.5 if held else 0.18
                img[int(y), int(x)] = np.maximum(img[int(y), int(x)], (a, a, a * 0.8))

    def render(self):
        img = self.trail.copy()
        self._arc(img)
        for s in self.shells:
            draw.disc(img, s[0], s[1], 0.8, (1, .9, .7), soft=0.5)
        # launcher
        img[N - 3:, 62:67] = (.3, .3, .3)
        if self.rt.held(1):
            charge = min(1.0, self.rt.held_for(1) / CHARGE_S)
            img[N - 2 - int(40 * charge):N - 2, N - 3:N - 1] = (1, .6 + .4 * charge, .2 + .8 * charge)
        if self.rt.t - self.t_type < 1.2:
            draw.text(img, BURSTS[self.burst], 64, 2, hsv1(self.hue, 0.5), center=True)
        return img

    def lights(self):
        charge = min(1.0, self.rt.held_for(1) / CHARGE_S) if self.rt.held(1) else 0.0
        return [(.25, .25, .2),
                (0.2 + 0.8 * charge, 0.1 + 0.8 * charge * charge, 0.05 + 0.5 * charge ** 3),
                hsv1(self.hue),
                hsv1(self.rt.t * 0.6) if self.auto else (.2, .15, .3)]
