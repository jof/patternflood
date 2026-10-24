"""A clock you can glitch, after Lee's glitch work (0519-2 glitch typography,
0511 sliding rows, 0602 colour separation, 0521 bitwise cascades).

Each knob is one unmistakable effect, and each springs back like a whammy bar:
turning injects glitch, which relaxes over a couple of seconds. Hold a knob to
pin its effect where it is. Click k0 to change what's shown.
"""
import datetime
import math
import random

import numpy as np

from .. import draw
from ..draw import N, hsv1
from ..runtime import Demo

RELAX_S = 1.6
SHOWS = ["clock", "PATTERN", "FLOOD", "date"]


class Glitch(Demo):
    name = "Glitch"
    blurb = "A clock, after Lee's glitch type. k0 tears, k1 splits colour, k2 smears, k3 crushes; each springs back. Hold to pin. Click k0 to change the text."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.amt = [0.0] * 4
        self.show = 0
        self.hue = 0.55
        self.minute = None
        self.t_shift = 0.0
        self.offsets = np.zeros(N, np.int32)
        self.blocks = np.zeros((16, 16), bool)

    def turn(self, k, d):
        self.amt[k] = min(1.0, max(0.0, self.amt[k] + abs(d) * 0.12))
        if k == 1:
            self.hue = (self.hue + d / 96.0) % 1.0

    def release(self, k, click):
        if click and k == 0:
            self.show = (self.show + 1) % len(SHOWS)
            self.amt[0] = max(self.amt[0], 0.8)          # change the text through a tear

    def _text(self):
        now = datetime.datetime.now()
        s = SHOWS[self.show]
        if s == "clock":
            return now.strftime("%H:%M"), now
        if s == "date":
            return now.strftime("%d.%m"), now
        return s, now

    def step(self, dt):
        t = self.rt.t
        _, now = self._text()
        if self.minute is not None and now.minute != self.minute:
            self.amt = [max(a, 0.9) for a in self.amt]   # the minute turns over with a jolt
        self.minute = now.minute
        for k in range(4):
            if not self.rt.held(k):
                self.amt[k] *= math.exp(-dt / RELAX_S * 3)
        if t - self.t_shift > 0.07:                       # re-roll the tears ~14 times a second
            self.t_shift = t
            a = self.amt[0]
            rows = np.zeros(N, np.int32)
            y = 0
            while y < N:
                h = self.rng.randint(2, 14)
                if self.rng.random() < a:
                    rows[y:y + h] = self.rng.randint(-int(40 * a) - 1, int(40 * a) + 1)
                y += h
            self.offsets = rows
            self.blocks = np.array([[self.rng.random() < self.amt[3] * 0.25 for _ in range(16)] for _ in range(16)])

    def render(self):
        t = self.rt.t
        s, now = self._text()
        img = draw.blank()
        img[::2] = 0.02                                   # scanlines
        scale = 4 if len(s) <= 5 else 3
        col = hsv1(self.hue, 0.25, 1.0)
        draw.text(img, s, 64, 64 - 6 * scale, col, center=True, scale=scale)
        # seconds, as a bar
        img[100:102, 14:14 + int(100 * now.second / 59)] = (.25, .25, .3)

        # k0: tear rows sideways
        if self.amt[0] > 0.02:
            ys = np.arange(N)
            xs = (np.arange(N)[None, :] - self.offsets[:, None]) % N
            img = img[ys[:, None], xs]
        # k1: split the colour channels apart
        a = self.amt[1]
        if a > 0.02:
            sh = int(round(10 * a))
            img = img.copy()
            img[..., 0] = np.roll(img[..., 0], -sh, 1)
            img[..., 2] = np.roll(np.roll(img[..., 2], sh, 1), int(3 * a * math.sin(t * 40)), 0)
        # k2: smear bright pixels to the right, like a pixel sort
        a = self.amt[2]
        if a > 0.02:
            keep = 1 - 0.15 / (a + 0.05)
            sm = img.copy()
            for x in range(1, N):
                np.maximum(sm[:, x], sm[:, x - 1] * keep, out=sm[:, x])
            img = img * (1 - a) + sm * a
        # k3: crush to blocks, with corrupted blocks of data
        a = self.amt[3]
        if a > 0.02:
            b = 1 + int(a * 7)
            img = img[::b, ::b].repeat(b, 0).repeat(b, 1)[:N, :N]
            levels = max(2, int(8 - 6 * a))
            img = np.round(img * levels) / levels
            bm = self.blocks.repeat(8, 0).repeat(8, 1)
            noise = np.random.random((N, N, 1)) > 0.5
            img = np.where(bm[..., None], noise * np.array(hsv1(self.hue + 0.5)), img)
        return img

    def lights(self):
        cs = [(1, .2, .6), (.2, .9, 1), (1, .9, .2), (.6, .3, 1)]
        return [tuple(c * (0.12 + 0.88 * self.amt[k]) for c in cs[k]) for k in range(4)]
