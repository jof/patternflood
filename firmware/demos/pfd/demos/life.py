"""Life: Conway's Game of Life, with the ghosts of the dead, dithered.

After Lee's TileWaves, its grid of lit squares. The rules are Conway's: a
cell with three neighbours is born, one with two or three lives on, and the
rest die. The grid wraps at the edges. Newborn cells blaze, and the long-lived
dim to a steady glow. Dead cells leave ghosts that fade through the dither,
so gliders trail comets and oscillators shimmer. When the board settles into
still lifes and blinkers, it's reseeded: a random soup, a glider fleet, or an
R-pentomino growing from one spot. With the music on, a generation passes on
every beat.
"""
import math

import numpy as np

from ..draw import N
from .original import Inked

SEEDS = ["soup", "gliders", "r-pentomino", "acorn"]


class Life(Inked):
    name = "Life"
    blurb = "Conway's Life with fading ghosts, dithered (after Lee's TileWaves). k0 speed, k1 ghost length, k2 screen, k3 inks. Click k0 pause, k1 reseed, k2 big cells."
    palette, screen_kind = "gameboy", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.rate, self.ghost = 12.0, 0.8
        self.paused = False
        self.cell = 1                               # pixels per cell: 1, or 2 when chunky
        self.acc = 0.0
        self.seed_i = 0
        self.history = []
        self.reseed()

    def chunky(self):
        self.cell = 3 - self.cell
        self.reseed()

    def reseed(self):
        n = N // self.cell
        g = np.zeros((n, n), np.uint8)
        kind = SEEDS[self.seed_i % len(SEEDS)]
        self.seed_i += 1
        if kind == "soup":
            g[:] = self.rng.random((n, n)) < 0.3
        elif kind == "gliders":
            glider = np.array([[0, 1, 0], [0, 0, 1], [1, 1, 1]], np.uint8)
            for _ in range(n // 6):
                y, x = self.rng.integers(0, n - 3, 2)
                g[y:y + 3, x:x + 3] = np.rot90(glider, self.rng.integers(0, 4))
        else:
            shape = np.array([[0, 1, 1], [1, 1, 0], [0, 1, 0]], np.uint8) if kind == "r-pentomino" else \
                np.array([[0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0], [1, 1, 0, 0, 1, 1, 1]], np.uint8)
            h, w = shape.shape
            g[n // 2 - h // 2:n // 2 - h // 2 + h, n // 2 - w // 2:n // 2 - w // 2 + w] = shape
        self.g = g
        self.age = g.astype(np.float32)
        self.ghosts = np.zeros((n, n), np.float32)
        self.history = []

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.rate = max(1.0, min(60.0, self.rate * 1.1 ** d))
        elif k == 1:
            self.ghost = max(0.0, min(0.97, self.ghost + d * 0.02))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.paused = not self.paused
        elif k == 1:
            self.reseed()
        elif k == 2:
            self.chunky()

    def generation(self):
        g = self.g
        nb = sum(np.roll(np.roll(g, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
        new = ((nb == 3) | ((g == 1) & (nb == 2))).astype(np.uint8)
        died = (g == 1) & (new == 0)
        self.ghosts[died] = 1.0
        self.age = np.where(new == 1, self.age + 1, 0)
        self.g = new
        # settled into still lifes and blinkers (the same board as one or two generations ago)? reseed
        key = hash(new.tobytes())
        self.history = (self.history + [key])[-6:]
        if self.history.count(key) >= 3 or new.sum() < 3:
            self.reseed()

    def step(self, dt):
        self.hear(dt)
        if self.listening:                          # a generation a beat (two, when the music's busy)
            if self.on_beat or (self.sound[1] > 0.5 and self.rt.audio.phase > 0.5 > self.rt.audio.phase - dt * 4):
                self.generation()
        elif not self.paused:
            self.acc += dt * self.rate
            while self.acc >= 1:
                self.acc -= 1
                self.generation()
        self.ghosts *= math.exp(-dt / (0.05 + 1.5 * self.ghost))
        if self.on_phrase:
            self.reseed()

    def render(self):
        live = self.g == 1
        fresh = np.exp(-self.age / 8)                # newborns blaze; the long-lived settle to a glow
        tone = np.where(live, 0.62 + 0.38 * fresh, self.ghosts * 0.5)
        if self.cell > 1:
            tone = tone.repeat(self.cell, 0).repeat(self.cell, 1)
        return self.print(np.clip(tone * (1 + 0.2 * self.beat), 0, 1))

    def lights(self):
        return [self.glow(0, 0.3, 0.1 if self.paused else 0.2 + 0.01 * self.rate),
                self.glow(1, 0.35, 0.2 + 0.4 * self.ghost)] + self.ink_lights()
