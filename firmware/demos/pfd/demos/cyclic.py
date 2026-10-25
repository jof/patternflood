"""Cyclic: a cellular automaton that organizes noise into rainbow spirals.

After SeungHun's TileWaves, its grid of coloured cells. Each cell holds one of N
colours, in a cycle. A cell moves on to the next colour when enough of its
neighbours already have it; nothing else ever happens. From random noise this
one rule first makes blotches, then waves, and finally a field of spirals that
wind out for ever, each a full turn of the palette. (David Griffeath's cyclic
cellular automaton.) It reseeds itself if it ever freezes.
"""
import numpy as np

from ..draw import N
from .original import Chromatic

NEIGHBOURHOODS = [
    ("moore", [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]),
    ("cross", [(-1, 0), (1, 0), (0, -1), (0, 1)]),
    ("wide", [(dy, dx) for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2) if (dy or dx) and abs(dy) + abs(dx) <= 3]),
]


class Cyclic(Chromatic):
    name = "Cyclic"
    blurb = "A cellular automaton that grows rainbow spirals out of noise (after SeungHun's TileWaves). k0 speed, k1 colours, k2 neighbourhood, k3 colour. Click k0 reseed, k1 big cells, k2 drop a seed, k3 next palette."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.rate, self.states, self.hood = 20.0, 14, 1
        self.cell = 1
        self.acc = 0.0
        self.reseed(warm=320)

    def threshold(self):
        return {"moore": 1, "cross": 1, "wide": 2}[NEIGHBOURHOODS[self.hood][0]]

    def reseed(self, warm=0):
        n = N // self.cell
        self.g = self.rng.integers(0, self.states, (n, n)).astype(np.int16)
        for _ in range(warm):                       # start somewhere organized, not in raw noise
            self.generation()

    def generation(self):
        g = self.g
        nxt = (g + 1) % self.states
        count = np.zeros(g.shape, np.int16)
        for dy, dx in NEIGHBOURHOODS[self.hood][1]:
            count += np.roll(np.roll(g, dy, 0), dx, 1) == nxt
        move = count >= self.threshold()
        self.changed = int(move.sum())
        self.g = np.where(move, nxt, g)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.rate = max(1.0, min(60.0, self.rate * 1.1 ** d))
        elif k == 1:
            self.states = max(3, min(24, self.states + (1 if d > 0 else -1)))
            self.g %= self.states
        elif k == 2:
            self.hood = (self.hood + (1 if d > 0 else -1)) % len(NEIGHBOURHOODS)
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.reseed()
        elif k == 1:
            self.cell = 3 - self.cell
            self.reseed(warm=200)
        elif k == 2:
            n = self.g.shape[0]
            y, x = self.rng.integers(0, n - 8, 2)
            self.g[y:y + 8, x:x + 8] = self.rng.integers(0, self.states, (8, 8))
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        self.acc += dt * self.rate * (1 + self.sound[1])
        steps = 0
        while self.acc >= 1 and steps < 4:
            self.acc -= 1
            steps += 1
            self.generation()
        self.acc = min(self.acc, 1.0)
        if getattr(self, "changed", 1) == 0:        # frozen: start again
            self.reseed()
        if self.on_phrase:
            self.reseed(warm=200)

    def render(self):
        img = self.colour(self.g / self.states)
        if self.cell > 1:
            img = img.repeat(self.cell, 0).repeat(self.cell, 1)
        return np.clip(img * (1 + 0.2 * self.beat), 0, 1)

    def lights(self):
        return [self.glow(0, 0.3, 0.1 + 0.01 * self.rate), self.glow(1, self.states / 24),
                self.glow(2, self.hood / 3), self.hue_light()]
