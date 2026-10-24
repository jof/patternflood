"""Asteroids, where the knob is the ship: one turn of k0 is one turn of the ship.

No acceleration and no rate: the heading is the knob's position, a detent at a
time (DETENTS_PER_REV to a revolution). Hold k1 to thrust, click k2 to fire
(hold it for autofire), hold k3 for the shield, which drains and recharges.
"""
import math
import random

import numpy as np

from .. import draw
from ..draw import N
from ..runtime import DETENTS_PER_REV, Demo

SHIP = [(5, 0), (-4, 3.2), (-2, 0), (-4, -3.2)]
SIZES = {3: 11.0, 2: 6.5, 1: 3.5}
SPEED = {3: 14.0, 2: 24.0, 1: 34.0}
SHOT_SPEED, SHOT_LIFE = 95.0, 0.9
AUTOFIRE_S = 0.18


def _wrap(v):
    return v % N


class Rock:
    def __init__(self, rng, size, x=None, y=None):
        self.size = size
        self.x = rng.uniform(0, N) if x is None else x
        self.y = rng.uniform(0, N) if y is None else y
        a = rng.uniform(0, 2 * math.pi)
        s = SPEED[size] * rng.uniform(0.7, 1.3)
        self.vx, self.vy = s * math.cos(a), s * math.sin(a)
        self.spin = rng.uniform(-1.5, 1.5)
        self.rot = rng.uniform(0, 2 * math.pi)
        n = 9
        self.shape = [(2 * math.pi * i / n, SIZES[size] * rng.uniform(0.7, 1.15)) for i in range(n)]


class Rotor(Demo):
    name = "Rotor"
    blurb = "Asteroids. k0 IS the ship's heading, one detent at a time. Hold k1 thrust, click k2 fire (hold for auto), hold k3 shield."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.heading = -math.pi / 2         # pointing up the screen
        self.score, self.best, self.wave = 0, 0, 0
        self.lives = 3
        self.energy = 1.0
        self.particles = []                 # [x, y, vx, vy, life, (r, g, b)]
        self.t_fire = -10.0
        self.t_flash_fire = -10.0
        self.respawn()
        self.rocks = []
        self.next_wave()

    def respawn(self):
        self.x = self.y = N / 2
        self.vx = self.vy = 0.0
        self.shots = getattr(self, "shots", [])
        self.t_spawn = self.rt.t
        self.dead_until = None

    def next_wave(self):
        self.wave += 1
        self.rocks = []
        for _ in range(2 + self.wave):
            while True:                     # not on top of the ship
                r = Rock(self.rng, 3)
                if math.hypot(r.x - self.x, r.y - self.y) > 35:
                    break
            self.rocks.append(r)

    def turn(self, k, d):
        if k == 0:
            self.heading += d * 2 * math.pi / DETENTS_PER_REV

    def press(self, k):
        if k == 2:
            self.fire()

    def release(self, k, click):
        if k == 0 and click and self.dead_until is None and self.lives <= 0:
            self.__init__(self.rt)          # game over: click k0 to start again

    def fire(self):
        if self.dead_until is not None or len(self.shots) > 6:
            return
        c, s = math.cos(self.heading), math.sin(self.heading)
        self.shots.append([self.x + 5 * c, self.y + 5 * s, self.vx + SHOT_SPEED * c, self.vy + SHOT_SPEED * s, SHOT_LIFE])
        self.t_fire = self.t_flash_fire = self.rt.t

    def _burst(self, x, y, n, colour, speed=30):
        for _ in range(n):
            a, v = self.rng.uniform(0, 2 * math.pi), self.rng.uniform(0.3, 1) * speed
            self.particles.append([x, y, v * math.cos(a), v * math.sin(a), self.rng.uniform(0.3, 0.9), colour])

    def step(self, dt):
        t = self.rt.t
        alive = self.dead_until is None and self.lives > 0
        shield = alive and self.rt.held(3) and self.energy > 0.02
        self.energy = max(0.0, min(1.0, self.energy + (-0.5 if shield else 0.12) * dt))
        self.shield = shield

        if alive:
            if self.rt.held(1):
                self.vx += math.cos(self.heading) * 70 * dt
                self.vy += math.sin(self.heading) * 70 * dt
                if self.rng.random() < 0.7:
                    c, s = math.cos(self.heading + math.pi), math.sin(self.heading + math.pi)
                    self.particles.append([self.x + 3 * c, self.y + 3 * s, 30 * c + self.rng.uniform(-8, 8),
                                           30 * s + self.rng.uniform(-8, 8), 0.25, (1, .5, .1)])
            if self.rt.held(2) and t - self.t_fire > AUTOFIRE_S:
                self.fire()
            drag = math.exp(-0.5 * dt)
            self.vx *= drag
            self.vy *= drag
            self.x, self.y = _wrap(self.x + self.vx * dt), _wrap(self.y + self.vy * dt)
        elif self.dead_until is not None and t > self.dead_until and self.lives > 0:
            self.respawn()

        for sh in self.shots:
            sh[0], sh[1] = _wrap(sh[0] + sh[2] * dt), _wrap(sh[1] + sh[3] * dt)
            sh[4] -= dt
        self.shots = [sh for sh in self.shots if sh[4] > 0]

        for r in self.rocks:
            r.x, r.y = _wrap(r.x + r.vx * dt), _wrap(r.y + r.vy * dt)
            r.rot += r.spin * dt

        # shots against rocks
        for sh in list(self.shots):
            for r in list(self.rocks):
                if self._dist(sh[0], sh[1], r.x, r.y) < SIZES[r.size]:
                    self.shots.remove(sh)
                    self.rocks.remove(r)
                    self.score += {3: 20, 2: 50, 1: 100}[r.size]
                    self.best = max(self.best, self.score)
                    self._burst(r.x, r.y, 6 + 4 * r.size, (.8, .7, .5))
                    if r.size > 1:
                        self.rocks += [Rock(self.rng, r.size - 1, r.x, r.y) for _ in range(2)]
                    break

        # rocks against the ship (not while it blinks in after a respawn)
        if alive and t - self.t_spawn > 2.0:
            for r in self.rocks:
                if self._dist(self.x, self.y, r.x, r.y) < SIZES[r.size] + 3:
                    if shield:
                        nx, ny = self.x - r.x, self.y - r.y
                        n = math.hypot(nx, ny) or 1
                        r.vx, r.vy = -abs(r.vx) * nx / n * 1.2 - nx / n * 20, -abs(r.vy) * ny / n * 1.2 - ny / n * 20
                        continue
                    self.lives -= 1
                    self.dead_until = t + 2.0
                    self._burst(self.x, self.y, 40, (1, .8, .3), speed=45)
                    break

        if not self.rocks:
            self.next_wave()

        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]

    @staticmethod
    def _dist(x0, y0, x1, y1):
        dx = (x0 - x1 + N / 2) % N - N / 2      # across the wrap
        dy = (y0 - y1 + N / 2) % N - N / 2
        return math.hypot(dx, dy)

    def _poly(self, img, pts, rgb):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            xs, ys = draw.segment(x0, y0, x1, y1, step=0.6)
            draw.plot(img, xs % N, ys % N, rgb, op="max")

    def render(self):
        img = draw.blank()
        t = self.rt.t
        for r in self.rocks:
            pts = [(r.x + rad * math.cos(a + r.rot), r.y + rad * math.sin(a + r.rot)) for a, rad in r.shape]
            self._poly(img, pts, (.75, .7, .6))
        for sh in self.shots:
            draw.plot(img, [sh[0]], [sh[1]], (1, 1, .7), op="max")
        for x, y, _, _, life, c in self.particles:
            draw.plot(img, [x % N], [y % N], np.array(c) * min(1.0, life * 2), op="max")

        alive = self.dead_until is None and self.lives > 0
        if alive and (t - self.t_spawn > 2.0 or int(t * 8) % 2):
            c, s = math.cos(self.heading), math.sin(self.heading)
            pts = [(self.x + px * c - py * s, self.y + px * s + py * c) for px, py in SHIP]
            self._poly(img, pts, (.6, .9, 1))
            if self.shield:
                draw.ring(img, self.x, self.y, 7.5, (.2, .5, 1))

        draw.text(img, str(self.score), 2, 1, (.5, .5, .5))
        for i in range(max(0, self.lives)):
            img[3:6, N - 4 - 5 * i:N - 2 - 5 * i] = (.3, .6, .8)
        img[N - 1, :int(N * self.energy)] = (.1, .25, .6)
        if self.lives <= 0:
            draw.text(img, "GAME OVER", 64, 52, (1, .3, .2), center=True)
            draw.text(img, f"best {self.best}", 64, 66, (.6, .6, .6), center=True)
            draw.text(img, "click k0", 64, 80, (.4, .4, .4), center=True)
        return img

    def lights(self):
        fire = max(0.0, 1 - (self.rt.t - self.t_flash_fire) / 0.15)
        return [(.3, .6, .8),
                (1, .5, .1) if self.rt.held(1) else (.15, .08, .02),
                (1, .9 * fire + .1, .3 * fire) if fire else (.15, .05, .02),
                (.2, .5, 1) if getattr(self, "shield", False) else (.03, .08, .1 + .3 * self.energy)]
