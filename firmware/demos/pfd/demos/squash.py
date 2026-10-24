"""Four-player Pong on a square: one paddle per wall, one knob per paddle.

Seats match the knob row: k0 the left wall, k3 the right, k1 the floor, k2 the
ceiling, in the knob_bridge's index colours. Turning a knob takes over that
paddle from the computer; leave it alone for a while and the computer takes it back.
"""
import math
import random

import numpy as np

from .. import draw
from ..draw import N
from ..runtime import Demo

COLOURS = [(1, .1, .05), (.1, 1, .2), (.15, .35, 1), (1, .85, .1)]
LEFT, BOTTOM, TOP, RIGHT = 0, 1, 2, 3       # seat = knob index
PAD = 26.0                  # paddle length, px
EDGE = 2.0                  # paddles sit on the 2 px nearest each wall
R_BALL = 1.8
IDLE_S = 20.0               # a human who stops turning hands back to the computer
SMASH_S = 0.3               # click this close before the hit to smash


class Squash(Demo):
    name = "Squash"
    blurb = "One paddle per wall: k0 left, k3 right, k1 floor, k2 ceiling. Turn to join. Click just before a hit to smash."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.pad = [N / 2] * 4
        self.human = [False] * 4
        self.t_touch = [-99.0] * 4
        self.t_smash = [-99.0] * 4
        self.t_flash = [-99.0] * 4      # paddle hit
        self.t_miss = [-99.0] * 4
        self.misses = [0] * 4
        self.rally, self.best = 0, 0
        self.trail = []
        self.sparks = []                # [x, y, vx, vy, life, colour]
        self.serve()

    def serve(self, delay=0.8):
        self.bx = self.by = N / 2 - 0.5
        a = self.rng.choice([1, 3, 5, 7]) * math.pi / 4 + self.rng.uniform(-0.35, 0.35)
        self.speed = 55.0
        self.vx, self.vy = math.cos(a), math.sin(a)
        self.t_serve = self.rt.t + delay
        self.hot = 0.0
        self.trail = []

    def turn(self, k, d):
        self.human[k] = True
        self.t_touch[k] = self.rt.t
        step = self.rt.accel(k, d) * 1.5
        if k in (LEFT, RIGHT):
            step = -step                    # clockwise moves a side paddle up
        self.pad[k] = min(N - PAD / 2, max(PAD / 2, self.pad[k] + step))

    def release(self, k, click):
        if click:
            self.human[k] = True
            self.t_touch[k] = self.rt.t
            self.t_smash[k] = self.rt.t

    def _ai(self, k, dt):
        # follow the ball's coordinate along this wall, lazily, a bit behind
        target = self.by if k in (LEFT, RIGHT) else self.bx
        incoming = {LEFT: self.vx < 0, RIGHT: self.vx > 0, TOP: self.vy < 0, BOTTOM: self.vy > 0}[k]
        if not incoming:
            target = N / 2
        err = 6 * math.sin(self.rt.t * 1.3 + k * 2)
        diff = target + err - self.pad[k]
        self.pad[k] += max(-1, min(1, diff / 6)) * 70 * dt
        self.pad[k] = min(N - PAD / 2, max(PAD / 2, self.pad[k]))

    def _bounce(self, k, along):
        """The ball reached wall k at coordinate `along`: hit or miss."""
        off = (along - self.pad[k]) / (PAD / 2 + R_BALL)
        if abs(off) <= 1:
            smash = self.rt.t - self.t_smash[k] < SMASH_S
            self.speed = min(170.0, self.speed * (1.35 if smash else 1.05))
            if smash:
                self.hot = 1.0
            # the hit point steers the ball, as in Pong
            normal = {LEFT: (1, 0), RIGHT: (-1, 0), TOP: (0, 1), BOTTOM: (0, -1)}[k]
            tang = (0, 1) if k in (LEFT, RIGHT) else (1, 0)
            a = off * 1.0
            self.vx = normal[0] * math.cos(a) + tang[0] * math.sin(a)
            self.vy = normal[1] * math.cos(a) + tang[1] * math.sin(a)
            self.rally += 1
            self.best = max(self.best, self.rally)
            self.t_flash[k] = self.rt.t
            self._burst(self.bx, self.by, COLOURS[k], 14 if smash else 6)
            return True
        self.misses[k] += 1
        self.t_miss[k] = self.rt.t
        self._burst(self.bx, self.by, COLOURS[k], 30)
        self.rally = 0
        self.serve()
        return False

    def _burst(self, x, y, c, n):
        for _ in range(n):
            a, s = self.rng.uniform(0, 2 * math.pi), self.rng.uniform(15, 60)
            self.sparks.append([x, y, s * math.cos(a), s * math.sin(a), self.rng.uniform(0.3, 0.8), c])

    def step(self, dt):
        t = self.rt.t
        for k in range(4):
            if self.human[k] and t - self.t_touch[k] > IDLE_S:
                self.human[k] = False
            if not self.human[k]:
                self._ai(k, dt)

        for s in self.sparks:
            s[0] += s[2] * dt
            s[1] += s[3] * dt
            s[4] -= dt
        self.sparks = [s for s in self.sparks if s[4] > 0]
        self.hot = max(0.0, self.hot - dt)

        if t < self.t_serve:
            return
        dist = self.speed * dt
        n = max(1, int(dist / 0.7))
        lo, hi = EDGE + R_BALL, N - 1 - EDGE - R_BALL
        for _ in range(n):
            self.bx += self.vx * dist / n
            self.by += self.vy * dist / n
            if self.bx < lo and self.vx < 0:
                if not self._bounce(LEFT, self.by):
                    return
            elif self.bx > hi and self.vx > 0:
                if not self._bounce(RIGHT, self.by):
                    return
            elif self.by < lo and self.vy < 0:
                if not self._bounce(TOP, self.bx):
                    return
            elif self.by > hi and self.vy > 0:
                if not self._bounce(BOTTOM, self.bx):
                    return
        self.trail.append((self.bx, self.by))
        self.trail = self.trail[-14:]

    def render(self):
        img = draw.blank()
        t = self.rt.t
        # faint court, and each wall in its owner's colour, flaring on a miss
        for k, c in enumerate(COLOURS):
            miss = max(0.0, 1 - (t - self.t_miss[k]) / 0.8)
            a = 0.06 + 0.8 * miss
            sl = {LEFT: np.s_[:, 0], RIGHT: np.s_[:, N - 1], TOP: np.s_[0, :], BOTTOM: np.s_[N - 1, :]}[k]
            img[sl] = np.maximum(img[sl], np.array(c, np.float32) * a)
        img[N // 2 - 1:N // 2 + 1, N // 2 - 1:N // 2 + 1] = 0.08

        # rally count, big and dim in the middle
        if self.rally >= 2:
            draw.text(img, str(self.rally), 64, 58, (.18, .18, .18), center=True)

        # paddles
        for k, c in enumerate(COLOURS):
            flash = max(0.0, 1 - (t - self.t_flash[k]) / 0.25)
            lvl = (1.0 if self.human[k] else 0.35) + flash
            col = np.minimum(1, np.array(c) * lvl + flash * 0.5)
            p0, p1 = int(round(self.pad[k] - PAD / 2)), int(round(self.pad[k] + PAD / 2))
            e = int(EDGE)
            if k == LEFT:
                img[p0:p1, 1:1 + e] = col
            elif k == RIGHT:
                img[p0:p1, N - 1 - e:N - 1] = col
            elif k == TOP:
                img[1:1 + e, p0:p1] = col
            else:
                img[N - 1 - e:N - 1, p0:p1] = col
            # misses as pips along the wall, near the corner
            for i in range(min(self.misses[k], 12)):
                q = 4 + 3 * i
                pos = {LEFT: (q, 4), RIGHT: (N - 1 - q, N - 5), TOP: (4, N - 1 - q), BOTTOM: (N - 5, q)}[k]
                img[pos] = np.array(c) * 0.5

        # ball and its trail
        if t >= self.t_serve or int(t * 8) % 2:
            for i, (x, y) in enumerate(self.trail):
                a = (i + 1) / len(self.trail)
                draw.disc(img, x, y, R_BALL * a, (a * .4, a * .4, a * .5), soft=0.5)
            hotc = (1, .6 + .4 * (1 - self.hot), 1 - self.hot)
            draw.disc(img, self.bx, self.by, R_BALL, hotc, soft=0.6)

        for x, y, _, _, life, c in self.sparks:
            draw.plot(img, [x], [y], np.array(c) * min(1, life * 2))
        return img

    def lights(self):
        t = self.rt.t
        out = []
        for k, c in enumerate(COLOURS):
            flash = max(0.0, 1 - (t - self.t_flash[k]) / 0.25)
            miss = max(0.0, 1 - (t - self.t_miss[k]) / 0.6)
            if miss and int(t * 12) % 2:
                out.append((0, 0, 0))
                continue
            lvl = (0.8 if self.human[k] else 0.15) + flash
            out.append(tuple(min(1, v * lvl + flash * .3) for v in c))
        return out
