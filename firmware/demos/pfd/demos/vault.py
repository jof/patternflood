"""Safecracker: four tumblers, one per knob, found by the warmth of each knob's light.

Each knob rolls its tumbler through 0..39. The knob's light warms as its number
nears the hidden one, but it looks the same within a step either side, so you
click to try. Right, and it locks green. Wrong, and it buzzes and costs time.
Open all four, and the next vault's warm zone is narrower.
"""
import math
import random

import numpy as np

from .. import draw
from ..draw import N
from ..runtime import Demo

DIAL = 40
PENALTY_S = 5.0


class Vault(Demo):
    name = "Vault"
    blurb = "Safecracker. Each knob rolls a tumbler; its light warms as you near the number. Click to try it. Open all four."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.level = 0
        self.best = None
        self.new_vault()

    def new_vault(self):
        self.level += 1
        self.target = [self.rng.randrange(DIAL) for _ in range(4)]
        self.val = [self.rng.randrange(DIAL) for _ in range(4)]
        self.shown = [float(v) for v in self.val]      # animated roll
        self.locked = [False] * 4
        self.t_buzz = [-10.0] * 4
        self.t_lock = [-10.0] * 4
        self.t_start = self.rt.t
        self.penalty = 0.0
        self.t_open = None
        self.warm = max(3, 10 - 2 * self.level)         # how far out the light starts to warm

    def _dist(self, k):
        d = abs(self.val[k] - self.target[k]) % DIAL
        return min(d, DIAL - d)

    def turn(self, k, d):
        if self.locked[k] or self.t_open is not None:
            return
        self.val[k] = (self.val[k] + d) % DIAL

    def release(self, k, click):
        if not click:
            return
        if self.t_open is not None:
            if self.rt.t - self.t_open > 1.5:
                self.new_vault()
            return
        if self.locked[k]:
            return
        if self._dist(k) == 0:
            self.locked[k] = True
            self.t_lock[k] = self.rt.t
            if all(self.locked):
                self.t_open = self.rt.t
                took = self.t_open - self.t_start + self.penalty
                self.took = took
                self.best = took if self.best is None else min(self.best, took)
        else:
            self.t_buzz[k] = self.rt.t
            self.penalty += PENALTY_S

    def step(self, dt):
        for k in range(4):
            # roll the shown value towards the real one, the short way round
            diff = (self.val[k] - self.shown[k] + DIAL / 2) % DIAL - DIAL / 2
            self.shown[k] = (self.shown[k] + diff * min(1.0, 18 * dt)) % DIAL

    def _heat(self, k):
        """0 cold .. 1 hot, flat across the last step so it can't give the exact number away."""
        d = self._dist(k)
        if d <= 1:
            return 1.0
        return max(0.0, 1 - (d - 1) / self.warm)

    def _heat_rgb(self, h):
        return (0.1 + 0.9 * h, 0.05 + 0.35 * h * h, 0.6 * (1 - h) + 0.05)

    def render(self):
        img = draw.blank()
        t = self.rt.t
        for k in range(4):
            x0, cx = k * 32, k * 32 + 16
            buzz = max(0.0, 1 - (t - self.t_buzz[k]) / 0.4)
            lock = max(0.0, 1 - (t - self.t_lock[k]) / 0.6)
            frame = (.1, .5, .15) if self.locked[k] else (.12, .12, .14)
            if buzz:
                frame = (buzz, .05, .05)
            img[18:110, x0 + 2:x0 + 30] = np.array(frame, np.float32) * 0.35
            img[18:110, x0 + 2] = img[18:110, x0 + 29] = frame
            # the rolling strip: the number in the window, neighbours fading above and below
            base = math.floor(self.shown[k])
            frac = self.shown[k] - base
            for j in range(-2, 3):
                v = (base + j) % DIAL
                y = 58 + (j - frac) * 20
                a = max(0.0, 1 - abs(j - frac) / 2.4)
                col = (.3, 1, .4) if self.locked[k] else (1, 1, .9)
                col = tuple(c * a * (1 if abs(j - frac) < 0.5 else 0.45) for c in col)
                draw.text(img, f"{v:02d}", cx, y - 6, col, center=True, scale=2 if abs(j - frac) < 0.5 else 1)
            img[46:47, x0 + 4:x0 + 28] = img[73:74, x0 + 4:x0 + 28] = (.25, .25, .25)
            if lock:
                draw.ring(img, cx, 60, 6 + 20 * (1 - lock), (lock * .3, lock, lock * .4), width=1.5)

        elapsed = (self.t_open if self.t_open is not None else t) - self.t_start + self.penalty
        draw.text(img, f"vault {self.level}", 2, 1, (.5, .5, .5))
        tm = f"{elapsed:4.1f}s"
        draw.text(img, tm, N - 2 - draw.text_width(tm), 1, (1, .4, .3) if self.penalty else (.5, .5, .5))
        if self.t_open is not None:
            a = min(1.0, (t - self.t_open) / 0.6)
            img *= 1 - 0.6 * a
            draw.ring(img, 64, 64, 10 + 50 * a, (.3 * a, a, .4 * a), width=2)
            draw.text(img, "OPEN", 64, 52, (a, a, a), center=True, scale=2)
            draw.text(img, f"{self.took:.1f}s  best {self.best:.1f}s", 64, 72, (.7 * a,) * 3, center=True)
            if t - self.t_open > 1.5:
                draw.text(img, "click for the next", 64, 112, (.4, .4, .4), center=True)
        return img

    def lights(self):
        t = self.rt.t
        out = []
        for k in range(4):
            if t - self.t_buzz[k] < 0.4:
                out.append((1, 0, 0) if int(t * 20) % 2 else (0, 0, 0))
            elif self.locked[k]:
                out.append((.1, .8, .2))
            else:
                h = self._heat(k)
                pulse = 0.85 + 0.15 * math.sin(t * (2 + 6 * h))    # a quicker pulse when hot
                out.append(tuple(c * pulse for c in self._heat_rgb(h)))
        return out
