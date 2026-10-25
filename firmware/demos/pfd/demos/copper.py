"""Copper: Amiga copper bars bouncing over a plasma, with a sine scroller.

After Lee's Retro Digital Tapestry, in the demoscene's own idiom. Horizontal
bars, each a vertical gradient bright in the middle and dark at the edges (as
the Amiga's copper chip changed the colour register line by line), swing up
and down on sine paths with staggered phases. The ones in front pass over the
ones behind, so the column of bars seems to roll. Behind them a dim plasma
cycles; across the bottom a message scrolls along a sine wave in a rainbow.
"""
import math

import numpy as np

from .. import draw
from ..draw import N, X, Y
from .original import Chromatic

MESSAGE = "    PATTERNFLOOD  *  GREETINGS TO SEUNGHUN LEE AND PATTERNFLOW  *  COPPER BARS FOREVER  *  "


class Copper(Chromatic):
    name = "Copper"
    blurb = "Amiga copper bars bouncing over a plasma, with a sine scroller (after Lee's Retro Digital Tapestry). k0 bars, k1 bounce speed, k2 scroll speed, k3 colour. Click k0 plasma, k2 scroller, k3 next palette."

    def __init__(self, rt):
        super().__init__(rt)
        self.bars, self.speed, self.scroll = 7, 1.0, 1.0
        self.plasma, self.scroller = True, True
        self.t, self.x = 0.0, 0.0
        m = draw._mask(MESSAGE)                         # the message as a bitmap, twice the font's size
        self.text = np.kron(m, np.ones((2, 2), np.float32))

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.bars = max(2, min(14, self.bars + (1 if d > 0 else -1)))
        elif k == 1:
            self.speed = max(0.0, min(4.0, self.speed + d * 0.1))
        elif k == 2:
            self.scroll = max(0.0, min(4.0, self.scroll + d * 0.1))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.plasma = not self.plasma
        elif k == 2:
            self.scroller = not self.scroller
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        self.t += dt * self.speed * (1 + self.sound[1])
        self.x += dt * 40 * self.scroll

    def render(self):
        t = self.t
        if self.plasma:
            p = (np.sin(X * 0.05 + t) + np.sin(Y * 0.07 - t * 0.7) + np.sin((X + Y) * 0.04 + t * 0.5)) / 3
            img = self.colour(p * 0.5 + t * 0.05) * 0.22
        else:
            img = np.zeros((N, N, 3), np.float32)
        # the bars: drawn back to front, so the column seems to roll
        n = self.bars
        phases = [i * 2 * math.pi / n * 0.35 + t * 1.6 for i in range(n)]
        order = sorted(range(n), key=lambda i: math.cos(phases[i]))
        height = 9 * (1 + 0.3 * self.beat)
        rows = np.arange(N, dtype=np.float32)
        for i in order:
            y0 = 50 + 34 * math.sin(phases[i])
            d = np.abs(rows - y0) / height
            band = np.clip(1 - d, 0, 1)
            if not band.any():
                continue
            col = self.colour(i / n)                                          # (3,)
            shade = (band ** 0.6) * (0.5 + 0.5 * math.cos(phases[i]) * 0.4 + 0.3)
            on = band > 0
            img[on] = (col[None, :] * shade[on, None])[:, None, :]
        if self.scroller:                               # the message, waving, in a rainbow
            th, tw = self.text.shape
            cols = (np.arange(N) + int(self.x)) % tw
            base = 100 + 6 * np.sin(np.arange(N) * 0.1 + self.t * 3)
            for xi in range(N):
                column = self.text[:, cols[xi]]
                if not column.any():
                    continue
                y = int(base[xi])
                ys = y + np.nonzero(column > 0.5)[0]
                ys = ys[(ys >= 0) & (ys < N)]
                img[ys, xi] = self.colour(xi / N + self.t * 0.2)
        return np.clip(img, 0, 1)

    def lights(self):
        return [self.glow(0, 0.08, 0.1 + 0.05 * self.bars), self.glow(1, 0.3, 0.2 + 0.15 * self.speed),
                self.glow(2, 0.6, 0.2 + 0.15 * self.scroll), self.hue_light()]
