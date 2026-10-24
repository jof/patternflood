"""Fireworks: shells launched over a town, bursting into peonies, willows, rings and crackle.

After Lee's a big hit. Rockets climb on a sparking trail and burst at the top
into a shell of stars, thrown out evenly over a sphere and seen flat, so the
burst is a disc that's denser at its rim. Each kind moves its own way:
peonies fall and fade quickly, willows hang and droop with long trails,
rings burst flat and tilted, crackle shells pop into twinkling sparks. The
sky keeps faint trails (the canvas fades, it isn't wiped), each burst lights
up the town's skyline for a moment, and smoke drifts. With the music on,
shells go up on the kicks, and each phrase brings a finale.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

KINDS = ["peony", "willow", "ring", "crackle"]
MAXP = 3000
G = 22.0


class Fireworks(Inked):
    name = "Fireworks"
    blurb = "Shells bursting over a town: peonies, willows, rings and crackle, dithered (after Lee's a big hit). k0 launch rate, k1 shell size, k2 screen, k3 inks. Click k0 a volley, k1 the finale, k2 chunky."
    palette, screen_kind = "synth", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.p = np.zeros((0, 8), np.float32)     # x, y, vx, vy, life, max life, kind, drag
        self.rockets = []                         # [x, y, vy, burst_y, kind]
        self.canvas = np.zeros((N, N), np.float32)
        self.rate, self.size = 1.0, 1.0
        self.flash = 0.0
        self.finale = 0.0
        self.t = 0.0
        sky = np.full(N, 128.0)
        x = 0
        rng = np.random.default_rng(3)
        while x < N:                              # a skyline of blocks
            w = int(rng.integers(5, 13))
            sky[x:x + w] = 128 - rng.integers(6, 20)
            x += w
        self.skyline = sky

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.rate = max(0.2, min(4.0, self.rate * 1.1 ** d))
        elif k == 1:
            self.size = max(0.4, min(1.8, self.size * 1.05 ** d))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            for _ in range(4):
                self.launch()
        elif k == 1:
            self.finale = 3.0
        elif k == 2:
            self.chunky()

    def launch(self):
        r = self.rng
        self.rockets.append([r.uniform(20, 108), 128.0, -r.uniform(75, 95), r.uniform(18, 50),
                             KINDS[int(r.integers(len(KINDS)))]])

    def burst(self, x, y, kind):
        r = self.rng
        n = int({"peony": 140, "willow": 110, "ring": 70, "crackle": 90}[kind] * self.size)
        v = r.normal(size=(n, 3))
        v /= np.linalg.norm(v, axis=1, keepdims=True)
        speed = {"peony": 38, "willow": 30, "ring": 40, "crackle": 34}[kind] * self.size * r.uniform(0.85, 1.15)
        if kind == "ring":                        # a flat ring, tilted towards us
            a = r.uniform(0, 2 * math.pi, n)
            tilt = r.uniform(0.3, 0.9)
            v = np.column_stack([np.cos(a), np.sin(a) * tilt, np.zeros(n)])
        life = {"peony": 1.6, "willow": 3.4, "ring": 1.8, "crackle": 1.3}[kind]
        drag = {"peony": 1.6, "willow": 2.6, "ring": 1.5, "crackle": 1.8}[kind]
        k = KINDS.index(kind)
        new = np.column_stack([np.full(n, x), np.full(n, y), v[:, 0] * speed, v[:, 1] * speed,
                               np.full(n, life) * r.uniform(0.7, 1.0, n), np.full(n, life), np.full(n, k), np.full(n, drag)])
        self.p = np.vstack([self.p, new.astype(np.float32)])[-MAXP:]
        self.flash = min(1.0, self.flash + 0.5 * self.size)

    def step(self, dt):
        self.hear(dt)
        dt = min(dt, 1 / 20)
        self.t += dt
        r = self.rng
        if self.listening:
            if self.on_beat and self.rt.audio.kick > 0.5:
                self.launch()
            if self.on_phrase:
                self.finale = 3.0
        elif r.random() < dt * self.rate * 0.9:
            self.launch()
        if self.finale > 0:
            self.finale -= dt
            if r.random() < dt * 9:
                self.launch()
        # rockets climb, sparking, and burst
        alive = []
        for rk in self.rockets:
            rk[1] += rk[2] * dt
            rk[2] += G * dt
            spark = np.array([[rk[0] + r.normal(0, 0.5), rk[1] + 2, r.normal(0, 3), r.uniform(5, 15), 0.35, 0.35, -1, 2.0]], np.float32)
            self.p = np.vstack([self.p, spark])
            if rk[1] <= rk[3] or rk[2] > -10:
                self.burst(rk[0], rk[1], rk[4])
            else:
                alive.append(rk)
        self.rockets = alive
        p = self.p
        if len(p):
            p[:, 2] *= np.exp(-p[:, 7] * dt)
            p[:, 3] *= np.exp(-p[:, 7] * dt)
            p[:, 3] += G * dt * np.where(p[:, 6] == 1, 0.55, 1.0)     # willows hang
            p[:, 0] += p[:, 2] * dt
            p[:, 1] += p[:, 3] * dt
            p[:, 4] -= dt
            self.p = p[(p[:, 4] > 0) & (p[:, 1] < N + 5)]
        self.flash *= math.exp(-dt / 0.2)
        # the sky keeps a ghost of every trail; willows' linger longest
        self.canvas *= math.exp(-dt / 0.35)

    def render(self):
        p = self.p
        if len(p):
            frac = np.clip(p[:, 4] / p[:, 5], 0, 1)
            b = 0.25 + 0.75 * frac
            crackle = p[:, 6] == 3
            b = np.where(crackle & (frac < 0.5), (self.rng.random(len(p)) < 0.5) * 1.0, b)    # popping sparks
            b = np.where(p[:, 6] == 1, 0.4 + 0.6 * frac ** 0.5, b)                            # willows glow gold, slowly
            xi, yi = np.rint(p[:, 0]).astype(int), np.rint(p[:, 1]).astype(int)
            ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
            np.maximum.at(self.canvas, (yi[ok], xi[ok]), b[ok] * np.where(p[ok, 6] == 1, 0.7, 0.45))
            now = np.zeros((N, N), np.float32)
            np.maximum.at(now, (yi[ok], xi[ok]), b[ok])
        else:
            now = np.zeros((N, N), np.float32)
        tone = np.maximum(self.canvas, now) + 0.012 + 0.14 * self.flash * np.clip(1 - Y / 128, 0, 1)
        town = Y >= self.skyline[None, :]
        lit = 0.05 + 0.3 * self.flash
        tone[town] = lit * (0.4 + 0.6 * ((X[town] % 4 < 2) & (Y[town] % 5 < 2) & ((X[town] * 7 + Y[town] * 3) % 11 < 4)))
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.9, 0.2 + 0.15 * self.rate), self.glow(1, 0.1, 0.2 + 0.3 * self.size)] + self.ink_lights()
