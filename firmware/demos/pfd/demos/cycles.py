"""Light cycles: one detent is one 90-degree turn. Up to four riders, the rest are computer.

Riders start at the same walls as Squash's paddles (k0 left, k3 right, k1
floor, k2 ceiling). Clockwise turns right, anticlockwise left. A click is a
short boost, which recharges.
"""
import math
import random

import numpy as np

from .. import draw
from .squash import COLOURS
from ..runtime import Demo

G = 64                      # arena cells; each is 2 x 2 pixels
DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]   # right, down, left, up (screen); +1 index = turn right
STARTS = [((4, G // 2), 0), ((G // 2, G - 5), 3), ((G // 2 - 1, 4), 1), ((G - 5, G // 2 - 1), 2)]
IDLE_S = 30.0


class Rider:
    def __init__(self, k):
        (self.x, self.y), self.dir = STARTS[k]
        self.alive = True
        self.turns = []
        self.acc = 0.0
        self.boost = 0.0            # seconds of boost left
        self.charge = 1.0           # 0..1; a boost needs a full charge
        self.t_dead = None


class Cycles(Demo):
    name = "Cycles"
    blurb = "Light cycles. Each knob steers a rider: one click of the knob is one turn. Turn to join; click to boost."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.human = [False] * 4
        self.t_touch = [-99.0] * 4
        self.wins = [0] * 4
        self.new_round()

    def new_round(self):
        self.grid = np.zeros((G, G), np.int8)       # 0 empty, k+1 trail of rider k
        self.riders = [Rider(k) for k in range(4)]
        for k, r in enumerate(self.riders):
            self.grid[r.y, r.x] = k + 1
        self.speed = 11.0                           # cells per second
        self.t_round = self.rt.t
        self.t_over = None
        self.winner = None
        self.booms = []                             # (x, y, t, colour)

    def turn(self, k, d):
        self.human[k] = True
        self.t_touch[k] = self.rt.t
        r = self.riders[k]
        for _ in range(min(abs(d), 2)):
            if len(r.turns) < 2:
                r.turns.append(1 if d > 0 else -1)

    def release(self, k, click):
        if not click:
            return
        self.human[k] = True
        self.t_touch[k] = self.rt.t
        r = self.riders[k]
        if r.alive and r.charge >= 1.0:
            r.boost, r.charge = 0.8, 0.0

    def _free(self, x, y):
        return 0 <= x < G and 0 <= y < G and self.grid[y, x] == 0

    def _reach(self, x, y, d, limit=12):
        n = 0
        dx, dy = DIRS[d]
        while n < limit and self._free(x + dx * (n + 1), y + dy * (n + 1)):
            n += 1
        return n

    def _ai(self, r):
        ahead = self._reach(r.x, r.y, r.dir)
        if ahead > 3 and self.rng.random() > 0.04:
            return
        left, right = (r.dir - 1) % 4, (r.dir + 1) % 4
        options = [(self._reach(r.x, r.y, d, 30) + self.rng.random(), d) for d in (r.dir, left, right)]
        r.dir = max(options)[1]

    def step(self, dt):
        t = self.rt.t
        for k in range(4):
            if self.human[k] and t - self.t_touch[k] > IDLE_S:
                self.human[k] = False
        if self.t_over is not None:
            if t - self.t_over > 2.5:
                self.new_round()
            return
        if t - self.t_round < 1.2:                  # get ready
            return
        self.speed = min(22.0, 11.0 + (t - self.t_round - 1.2) * 0.35)

        moving = []
        for k, r in enumerate(self.riders):
            if not r.alive:
                continue
            r.charge = min(1.0, r.charge + dt / 4.0)
            r.boost = max(0.0, r.boost - dt)
            r.acc += self.speed * (1.8 if r.boost else 1.0) * dt
            moving.append(k)

        # advance one cell at a time so riders that cross paths really meet
        while True:
            due = [k for k in moving if self.riders[k].alive and self.riders[k].acc >= 1.0]
            if not due:
                break
            targets = {}
            for k in due:
                r = self.riders[k]
                r.acc -= 1.0
                if self.human[k]:
                    if r.turns:
                        r.dir = (r.dir + r.turns.pop(0)) % 4
                else:
                    self._ai(r)
                dx, dy = DIRS[r.dir]
                targets[k] = (r.x + dx, r.y + dy)
            for k, (x, y) in targets.items():
                r = self.riders[k]
                head_on = [j for j, p in targets.items() if j != k and p == (x, y)]
                if not self._free(x, y) or head_on:
                    self._crash(k)
                else:
                    r.x, r.y = x, y
            for k in targets:
                r = self.riders[k]
                if r.alive:
                    self.grid[r.y, r.x] = k + 1

        alive = [k for k, r in enumerate(self.riders) if r.alive]
        humans = [k for k in range(4) if self.human[k]]
        if len(alive) <= 1 or (humans and not any(k in alive for k in humans)):
            self.t_over = t
            if len(alive) == 1:
                self.winner = alive[0]
                self.wins[alive[0]] += 1

    def _crash(self, k):
        r = self.riders[k]
        r.alive = False
        r.t_dead = self.rt.t
        self.booms.append((r.x, r.y, self.rt.t, COLOURS[k]))

    def render(self):
        t = self.rt.t
        small = np.zeros((G, G, 3), np.float32)
        for k, r in enumerate(self.riders):
            fade = 1.0 if r.alive else max(0.0, 1 - (t - r.t_dead) / 1.0)
            small[self.grid == k + 1] = np.array(COLOURS[k]) * 0.45 * fade
            if r.alive:
                blink = 1.0 if t - self.t_round > 1.2 or int(t * 6) % 2 else 0.3
                small[r.y, r.x] = np.minimum(1, np.array(COLOURS[k]) * 0.5 + 0.6) * blink
        img = small.repeat(2, 0).repeat(2, 1)
        img[0, :] = img[-1, :] = img[:, 0] = img[:, -1] = np.maximum(img[0, 0], 0.05)

        for x, y, t0, c in self.booms:
            age = t - t0
            if age < 0.8:
                draw.ring(img, x * 2 + 0.5, y * 2 + 0.5, 2 + age * 30, np.array(c) * (1 - age / 0.8), width=1.5)

        if self.t_over is not None and self.winner is not None and int(t * 4) % 2:
            img = img * 0.4 + np.array(COLOURS[self.winner], np.float32) * 0.25
        for k in range(4):                          # round wins as pips in each start corner
            for i in range(min(self.wins[k], 10)):
                x, y = STARTS[k][0]
                img[min(125, max(2, y * 2 + 6)), min(125, max(2, x * 2 - 9 + 2 * i))] = np.array(COLOURS[k]) * 0.6
        return img

    def lights(self):
        out = []
        for k, r in enumerate(self.riders):
            c = np.array(COLOURS[k])
            if not r.alive:
                out.append((0.05, 0.05, 0.05))
            elif not self.human[k]:
                out.append(tuple(c * 0.12))
            elif r.boost:
                out.append((1, 1, 1))
            else:
                out.append(tuple(c * (0.25 + 0.75 * r.charge)))    # brightens as the boost recharges
        return out
