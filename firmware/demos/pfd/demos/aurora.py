"""Aurora: the northern lights over mountains and a still lake, dithered.

After SeungHun's 0602, its bands of colour rippling. Two or three curtains hang in
the sky, each a ribbon whose hem folds slowly from side to side. A curtain is
brightest at its hem and fades upward, and it's made of fine vertical rays
that flicker and travel along it. Now and then a substorm (click k0, or a new
phrase in the music) brightens everything, and the folds quicken and grow. Stars
behind, a ridge of mountains in front, and a lake that mirrors it all with a
slow ripple. The inks shade from deep teal through green to a pale pink top.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

HORIZON = 98                    # the lake's shore line
NCURTAINS = 3


class Aurora(Inked):
    name = "Aurora"
    blurb = "The northern lights over mountains and a lake, dithered (after SeungHun's 0602). k0 activity, k1 curtain height, k2 screen, k3 inks. Click k0 substorm, k1 the lake, k2 chunky."
    palette, screen_kind = "aurora", "bayer8"

    def __init__(self, rt):
        super().__init__(rt)
        rng = np.random.default_rng(9)
        self.stars = np.column_stack([rng.integers(0, N, 120), rng.integers(0, HORIZON, 120), rng.random(120)]).astype(np.float32)
        self.ridge = (89 + 4 * np.sin(np.arange(N) * 0.05 + 1) + 3 * np.sin(np.arange(N) * 0.13 + 2)
                      + 1.5 * np.sin(np.arange(N) * 0.37) + 0.8 * np.sin(np.arange(N) * 0.9)).astype(np.float32)
        self.ridge = np.minimum(self.ridge, HORIZON - 1)
        self.phases = rng.uniform(0, 6.28, (NCURTAINS, 4)).astype(np.float32)
        self.activity, self.height = 1.0, 1.0
        self.lake = True
        self.storm = 0.0
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.activity = max(0.2, min(3.0, self.activity * 1.07 ** d))
        elif k == 1:
            self.height = max(0.4, min(2.0, self.height * 1.05 ** d))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.storm = 1.0
        elif k == 1:
            self.lake = not self.lake
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        self.t += dt * self.activity * (1 + 2 * self.storm + self.sound[1])
        self.storm *= math.exp(-dt / 6)
        if self.on_phrase or (not self.listening and np.random.random() < dt / 90):
            self.storm = 1.0

    def sky(self):
        """The aurora (and stars) over the whole frame, before the land goes in front."""
        t = self.t
        x = np.arange(N, dtype=np.float32)
        tone = np.zeros((N, N), np.float32)
        for c in range(NCURTAINS):
            p = self.phases[c]
            fold = 1 + 1.5 * self.storm
            hem = (66 + 8 * c - 10 * self.storm + 9 * fold * np.sin(x * 0.035 + t * 0.21 + p[0])
                   + 5 * fold * np.sin(x * 0.09 - t * 0.33 + p[1]) + 2 * np.sin(x * 0.23 + t * 0.7 + p[2]))
            # rays: fine vertical streaks that travel along the curtain and flicker
            rays = (0.55 + 0.25 * np.sin(x * 0.9 + t * 2.3 + p[3]) + 0.2 * np.sin(x * 2.3 - t * 3.1 + c)
                    + 0.15 * np.sin(x * 5.1 + t * 7 + 2 * c)) * (0.5 + 0.5 * np.sin(x * 0.05 + t * 0.4 + p[2]) ** 2)
            h = (30 + 8 * c) * self.height * (1 + 0.4 * self.storm)
            above = hem[None, :] - Y                                       # pixels above the hem
            veil = np.where(above >= 0, np.exp(-above / h), np.exp(above / 1.8))
            tone += veil * rays[None, :] * (0.55 - 0.1 * c) * (1 + 0.8 * self.storm + 0.4 * self.sound[2])
        tone = 1 - np.exp(-tone * 1.4)                                     # overlapping curtains saturate softly
        tone += 0.05 + 0.09 * np.clip((Y - 30) / (HORIZON - 30), 0, 1) ** 2     # airglow, brightest low down
        sx, sy, sb = self.stars.T
        twinkle = sb * (0.6 + 0.4 * np.sin(self.rt.t * (2 + sb * 3) + sb * 30))
        tone[sy.astype(int), sx.astype(int)] = np.maximum(tone[sy.astype(int), sx.astype(int)], 0.35 * twinkle)
        return tone

    def render(self):
        tone = self.sky()
        if self.lake:                       # the lake: the sky mirrored about the shore, rippling
            rows = np.arange(HORIZON, N)
            src = 2 * HORIZON - rows - 1
            wob = (1.5 * np.sin(rows[:, None] * 0.7 + self.rt.t * 1.3 + X[0][None, :] * 0.05)).astype(int)
            cols = np.clip(np.arange(N)[None, :] + wob, 0, N - 1)
            tone[HORIZON:] = tone[np.clip(src, 0, N - 1)[:, None], cols] * 0.55
        else:
            tone[HORIZON:] = 0.02
        land = Y >= self.ridge[None, :]
        tone[land & (Y < HORIZON)] = 0.0                                   # the mountains, black
        if self.lake:                                                      # and their reflection
            mirror = (Y >= HORIZON) & (2 * HORIZON - Y - 1 >= self.ridge[None, :])
            tone[mirror] = 0.0
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.38, 0.2 + 0.3 * self.activity), self.glow(1, 0.85, 0.2 + 0.3 * self.height)] + self.ink_lights()
