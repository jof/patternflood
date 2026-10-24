"""Game of Life with a time knob: scrub back through history, change the past, watch a new future.

k0 is a jog wheel over generations, k1 the play speed, and it goes through zero
into reverse. Dropping a pattern while scrubbed back discards the old future.
The bar along the bottom is the stored history, with the playhead in it.
"""
import numpy as np

from .. import draw
from ..draw import N
from ..runtime import Demo

G = 64
HISTORY = 2000
SPEEDS = [-30, -15, -8, -4, -2, -1, 0, 1, 2, 4, 8, 15, 30]   # generations per second
STAMPS = {
    "glider": [".#.", "..#", "###"],
    "r-pentomino": [".##", "##.", ".#."],
    "acorn": [".#.....", "...#...", "##..###"],
    "lwss": [".#..#", "#....", "#...#", "####."],
    "diehard": ["......#.", "##......", ".#...###"],
    "pulsar-seed": ["###.###", "#.....#", "###.###"],
}
GHOSTS = 10


def _life(b):
    n = sum(np.roll(np.roll(b, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    return (n == 3) | (b & (n == 2))


class Rewind(Demo):
    name = "Rewind"
    blurb = "Life with a time knob. k0 scrubs generations, k1 play speed (through zero into reverse). Click k2 to drop a pattern, turn k2 to pick it. Click k3 new soup."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.speed_i = SPEEDS.index(8)
        self.paused_i = None
        self.stamp = 0
        self.t_stamp_pick = -10.0
        self.t_edge = -10.0          # hit the start of history
        self.t_drop = -10.0
        self.drop_at = (32, 32)
        self.acc = 0.0
        self.soup()

    def soup(self):
        b = self.rng.random((G, G)) < 0.32
        b[:, :] &= np.pad(np.ones((G - 16, G - 16), bool), 8)   # a square of soup in open space
        self.hist = [b]
        self.now = 0

    # ---- history

    def _go(self, n):
        """Move the playhead n generations, computing new ones past the end of history."""
        target = self.now + n
        if target < 0:
            target = 0
            self.t_edge = self.rt.t
        while target >= len(self.hist):
            self.hist.append(_life(self.hist[-1]))
            if len(self.hist) > HISTORY:
                self.hist.pop(0)
                target -= 1
        self.now = target

    def turn(self, k, d):
        if k == 0:
            self._go(int(round(self.rt.accel(0, d, top=8))))
            self.acc = 0.0
        elif k == 1:
            self.speed_i = min(len(SPEEDS) - 1, max(0, self.speed_i + (1 if d > 0 else -1)))
            self.paused_i = None
        elif k == 2:
            self.stamp = (self.stamp + (1 if d > 0 else -1)) % len(STAMPS)
            self.t_stamp_pick = self.rt.t

    def release(self, k, click):
        if not click:
            return
        if k == 1:
            if SPEEDS[self.speed_i] == 0 and self.paused_i is not None:
                self.speed_i, self.paused_i = self.paused_i, None
            elif SPEEDS[self.speed_i] != 0:
                self.paused_i, self.speed_i = self.speed_i, SPEEDS.index(0)
        elif k == 2:
            self.drop()
        elif k == 3:
            self.soup()

    def drop(self):
        rows = STAMPS[list(STAMPS)[self.stamp]]
        pat = np.array([[c == "#" for c in r] for r in rows])
        for _ in range(self.rng.integers(0, 4)):
            pat = np.rot90(pat)
        y, x = (int(v) for v in self.rng.integers(0, G, 2))
        b = self.hist[self.now].copy()
        for dy, dx in zip(*np.nonzero(pat)):
            b[(y + dy) % G, (x + dx) % G] = True
        del self.hist[self.now + 1:]             # the old future is gone
        self.hist[self.now] = b
        self.drop_at = (x + pat.shape[1] / 2, y + pat.shape[0] / 2)
        self.t_drop = self.rt.t

    def step(self, dt):
        sp = SPEEDS[self.speed_i]
        if self.rt.held(0) or sp == 0:
            return
        self.acc += sp * dt
        n = int(self.acc)
        if n:
            self.acc -= n
            self._go(n)

    def render(self):
        now = self.hist[self.now]
        # age: how many generations each live cell has been alive (up to 6)
        age = np.zeros((G, G), np.float32)
        run = now.copy()
        for j in range(1, 7):
            if self.now - j < 0:
                break
            run &= self.hist[self.now - j]
            age += run
        ghost = np.zeros((G, G), np.float32)
        for j in range(1, GHOSTS + 1):
            if self.now - j < 0:
                break
            ghost = np.maximum(ghost, self.hist[self.now - j] * (1 - j / (GHOSTS + 1)))
        ghost[now] = 0

        rev = SPEEDS[self.speed_i] < 0
        small = np.zeros((G, G, 3), np.float32)
        gc = np.array((.25, .05, .3) if rev else (.03, .15, .25), np.float32)
        small += ghost[..., None] * gc
        a = age[now] / 6.0
        small[now] = np.stack([1 - 0.7 * a, 0.9 - 0.3 * a, 0.4 + 0.6 * a], axis=-1)
        img = small.repeat(2, 0).repeat(2, 1)

        drop = max(0.0, 1 - (self.rt.t - self.t_drop) / 0.7)
        if drop:
            draw.ring(img, self.drop_at[0] * 2, self.drop_at[1] * 2, 4 + 20 * (1 - drop), (drop, drop, drop * 0.5), width=1.2)

        # history bar: stored span, and the playhead
        img[N - 2:] *= 0.3
        filled = int(N * len(self.hist) / HISTORY)
        img[N - 1, :filled] = (.12, .12, .12)
        head = int((N - 1) * self.now / max(1, HISTORY - 1))
        edge = max(0.0, 1 - (self.rt.t - self.t_edge) / 0.4)
        img[N - 2:, max(0, head - 1):head + 1] = (1, .3 * (1 - edge) + .1, .1) if edge else (1, 1, .6)

        if self.rt.t - self.t_stamp_pick < 1.2:
            name = list(STAMPS)[self.stamp]
            draw.text(img, name, 64, 2, (.9, .9, .5), center=True)
        return img

    def lights(self):
        sp = SPEEDS[self.speed_i]
        edge = max(0.0, 1 - (self.rt.t - self.t_edge) / 0.4)
        drop = max(0.0, 1 - (self.rt.t - self.t_drop) / 0.5)
        mag = abs(sp) / 30
        return [(1, 0.1, 0.1) if edge else ((0.9, 0.9, 0.6) if self.rt.held(0) else (0.3, 0.3, 0.2)),
                (0.5, 0.5, 0.5) if sp == 0 else ((0.5 + 0.5 * mag, 0.0, 0.6) if sp < 0 else (0.0, 0.4 + 0.6 * mag, 0.5)),
                (0.5 + 0.5 * drop, 0.5 + 0.5 * drop, 0.2 + 0.5 * drop),
                (0.15, 0.15, 0.15)]
