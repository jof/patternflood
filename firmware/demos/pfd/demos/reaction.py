"""Gray-Scott reaction-diffusion: two knobs walk the feed/kill map, the patterns follow slowly.

The interest is in the lag: a turn now shows up seconds later, as spots
splitting, worms, coral or mazes. Presets jump to known regions of the map.
"""
import numpy as np

from .. import draw
from ..draw import N, hsv
from ..runtime import Demo

PRESETS = [("coral", 0.0545, 0.062), ("mitosis", 0.0367, 0.0649), ("worms", 0.078, 0.061),
           ("spots", 0.030, 0.062), ("maze", 0.029, 0.057), ("chaos", 0.018, 0.051), ("bubbles", 0.098, 0.0555)]
DA, DB = 1.0, 0.5


def _lap(a):
    return (0.2 * (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1))
            + 0.05 * (np.roll(np.roll(a, 1, 0), 1, 1) + np.roll(np.roll(a, 1, 0), -1, 1)
                      + np.roll(np.roll(a, -1, 0), 1, 1) + np.roll(np.roll(a, -1, 0), -1, 1)) - a)


class Reaction(Demo):
    name = "Reaction"
    blurb = "Reaction-diffusion. k0 feed, k1 kill: walk the map and wait. Click k0 to seed, k1 next preset. k2 speed, k3 colour; click k3 to wipe."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.preset = 0
        _, self.f, self.k = PRESETS[0]
        self.iters = 10
        self.hue = 0.55
        self.t_param = -10.0
        self.t_seed = -10.0
        self.a = np.ones((N, N), np.float32)
        self.b = np.zeros((N, N), np.float32)
        self.seed(12)

    def seed(self, n=5):
        for _ in range(n):
            y, x = self.rng.integers(8, N - 8, 2)
            r = int(self.rng.integers(2, 5))
            self.b[y - r:y + r, x - r:x + r] = 1.0
            self.a[y - r:y + r, x - r:x + r] = 0.5
        self.t_seed = self.rt.t

    def turn(self, k, d):
        if k == 0:
            self.f = min(0.11, max(0.005, self.f + d * 0.0007))
            self.t_param = self.rt.t
        elif k == 1:
            self.k = min(0.072, max(0.04, self.k + d * 0.0003))
            self.t_param = self.rt.t
        elif k == 2:
            self.iters = min(30, max(0, self.iters + d))
        elif k == 3:
            self.hue = (self.hue + d / 48.0) % 1.0

    def release(self, k, click):
        if not click:
            return
        if k == 0:
            self.seed()
        elif k == 1:
            self.preset = (self.preset + 1) % len(PRESETS)
            _, self.f, self.k = PRESETS[self.preset]
            self.t_param = self.rt.t
            self.wipe()             # a grown field often collapses under new parameters
        elif k == 3:
            self.wipe()

    def wipe(self):
        self.a[:] = 1
        self.b[:] = 0
        self.seed(12)

    def step(self, dt):
        a, b = self.a, self.b
        n = int(round(self.iters * min(3.0, dt * 60)))
        for _ in range(n):
            abb = a * b * b
            a += DA * _lap(a) - abb + self.f * (1 - a)
            b += DB * _lap(b) + abb - (self.k + self.f) * b
        np.clip(a, 0, 1, out=a)
        np.clip(b, 0, 1, out=b)
        # never leave the panel dark: a field that has died out gets reseeded
        if b.max() < 0.05:
            self.t_dead = getattr(self, "t_dead", None) or self.rt.t
            if self.rt.t - self.t_dead > 1.0:
                self.seed(8)
                self.t_dead = None
        else:
            self.t_dead = None

    def render(self):
        v = np.clip((self.b - 0.08) * 3.2, 0, 1)
        img = hsv(self.hue + 0.25 * v, 1 - 0.55 * v, v ** 0.9).astype(np.float32)
        if self.rt.t - self.t_param < 1.5:
            name = next((nm for nm, f, k in PRESETS if abs(f - self.f) < 1e-4 and abs(k - self.k) < 1e-4), None)
            label = name or f"F {self.f:.4f}  k {self.k:.4f}"
            img[:13] *= 0.3
            draw.text(img, label, 64, 1, (.9, .9, .9), center=True)
            # where we are on the map: a small inset, F up, k across
            img[100:126, 2:28] *= 0.2
            mx = 2 + (self.k - 0.04) / 0.032 * 25
            my = 125 - (self.f - 0.005) / 0.105 * 25
            for nm, f, k in PRESETS:
                draw.plot(img, [2 + (k - 0.04) / 0.032 * 25], [125 - (f - 0.005) / 0.105 * 25], (.4, .4, .4), op="max")
            draw.disc(img, mx, my, 1.0, (1, 1, 1), soft=0.4)
        return img

    def lights(self):
        c = tuple(float(x) for x in hsv(np.array(self.hue), np.array(1.0), np.array(0.6)))
        seed = max(0.0, 1 - (self.rt.t - self.t_seed) / 0.5)
        fk = 0.3 + 0.7 * max(0.0, 1 - (self.rt.t - self.t_param) / 1.0)
        return [(fk, fk * 0.6, 0.1 + seed), (0.1, fk * 0.6, fk), (0.05, 0.05 + self.iters / 40, 0.05), c]
