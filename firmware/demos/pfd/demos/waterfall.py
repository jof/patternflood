"""A scrolling spectrogram with the analyzer's beat grid drawn into it.

Low notes on the left, high on the right, the newest row at the top. Beats
leave ticks down the left edge (the one in red), bar lines run faintly across,
phrase boundaries brightly, and a drop leaves a red line: the music's structure,
as the analyzer heard it, scrolling away under the sound.

    k0  scroll speed
    k1  palette
    k2  gain
    k3  click: grid marks on or off
"""
import numpy as np

from .. import draw
from ..draw import N, hsv
from ..runtime import Demo

PALETTES = [((0.02, 0.02, 0.1), (0.1, 0.1, 0.6), (0.9, 0.2, 0.5), (1.0, 0.85, 0.3), (1, 1, 1)),
            ((0, 0, 0), (0.0, 0.25, 0.2), (0.0, 0.7, 0.5), (0.7, 1.0, 0.6), (1, 1, 1)),
            ((0, 0, 0), (0.25, 0.05, 0.0), (0.8, 0.3, 0.0), (1.0, 0.8, 0.2), (1, 1, 0.9))]


class Waterfall(Demo):
    name = "Waterfall"
    blurb = "A scrolling spectrogram with the beat grid drawn in: beats, bars, phrases, drops. k0 speed, k1 palette, k2 gain, click k3 for marks."

    def __init__(self, rt):
        super().__init__(rt)
        self.speed = 1.0
        self.palette = 0
        self.gain = 1.0
        self.marks = True
        self.hist = np.zeros((N, N), np.float32)
        self.mark = np.zeros((N, 3), np.float32)       # a colour per row, for the grid
        self.acc = 0.0
        # 24 bands spread across 128 columns, by linear interpolation
        self.xi = np.linspace(0, 23, N)

    def turn(self, k, d):
        if k == 0:
            self.speed = min(4.0, max(0.25, self.speed * 1.15 ** d))
        elif k == 1:
            self.palette = (self.palette + (1 if d > 0 else -1)) % len(PALETTES)
        elif k == 2:
            self.gain = min(4.0, max(0.25, self.gain * 1.1 ** d))

    def release(self, k, click):
        if click and k == 3:
            self.marks = not self.marks

    def step(self, dt):
        a = self.rt.audio
        row = np.interp(self.xi, np.arange(24), np.asarray(a.bands, np.float32))
        row = np.clip(row * self.gain * 0.85, 0, 1) ** 2.4
        mark = np.zeros(3, np.float32)
        if a.beat:
            mark = np.array((.9, .25, .2) if a.beat_in_bar == 0 else (.4, .4, .45), np.float32)
        if a.phrase:
            mark = np.array((1, .9, .4), np.float32)
        if a.drop:
            mark = np.array((1, .1, .1), np.float32)
        self.acc += self.speed * dt * 60
        n = int(self.acc)
        self.acc -= n
        for _ in range(n):
            self.hist = np.roll(self.hist, 1, 0)
            self.mark = np.roll(self.mark, 1, 0)
            self.hist[0] = row
            self.mark[0] = mark
            mark = np.zeros(3, np.float32)                 # an event marks one row only

    def render(self):
        stops = np.array(PALETTES[self.palette], np.float32)
        x = np.linspace(0, 1, len(stops))
        v = self.hist
        img = np.stack([np.interp(v, x, stops[:, c]) for c in range(3)], -1).astype(np.float32)
        if self.marks:
            m = self.mark.max(1) > 0
            img[m, :4] = self.mark[m][:, None, :]
            # bar and phrase lines run across, faintly; drops boldly
            big = (self.mark[:, 0] > 0.85) & (self.mark[:, 1] < 0.3)
            phr = self.mark[:, 1] > 0.8
            img[phr] = img[phr] * 0.6 + np.array((1, .9, .4)) * 0.4
            img[big] = img[big] * 0.4 + np.array((1, .1, .1)) * 0.6
        return img

    def lights(self):
        a = self.rt.audio
        c = PALETTES[self.palette][3]
        return [tuple(v * (.2 + .8 * a.bass) for v in c), tuple(v * .3 for v in c),
                (min(1, self.gain / 3),) * 3, (.5, .5, .5) if self.marks else (.05, .05, .05)]
