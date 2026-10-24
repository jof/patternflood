"""Op Art: black and white lines bent until they seem to move by themselves.

After Lee's Warped Wave, and Bridget Riley's paintings. Five fields, each a
signed wave sharpened into hard black and white, with a pixel of dithered
grey where the edges fall between pixels:
    current   wavy lines whose spacing breathes across the frame
    squares   a checkerboard whose columns crowd towards a drifting fold
    bulge     a grid swelling under a lens that roams over it
    rings     two sets of rings whose crossings make a third pattern
    twist     a sunburst whose rays twist with the radius
"""
import math

import numpy as np

from .. import ink
from ..draw import X, Y
from .original import Inked

MODES = ["current", "squares", "bulge", "rings", "twist"]


class OpArt(Inked):
    name = "Op Art"
    blurb = "Black and white lines bent until they seem to move (after Lee's Warped Wave and Bridget Riley). k0 line spacing, k1 warp, k2 picture, k3 inks. Click k0 invert, k1 hold still, k2 screen, k3 chunky."
    palette, screen_kind = "mac", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        self.spacing, self.warp = 7.0, 1.0
        self.mode = 0
        self.invert, self.still = False, False
        self.t = 0.0
        self.kick = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.spacing = max(3.0, min(16.0, self.spacing * 1.04 ** d))
        elif k == 1:
            self.warp = max(0.0, min(3.0, self.warp + d * 0.05))
        elif k == 2:
            self.mode = (self.mode + (1 if d > 0 else -1)) % len(MODES)
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.invert = not self.invert
        elif k == 1:
            self.still = not self.still
        elif k == 2:
            self.screen_i = (self.screen_i + 1) % len(ink.SCREENS)
            self.set_screen()
        elif k == 3:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        if not self.still:
            self.t += dt * (1 + self.sound[0])
        if self.on_beat:
            self.kick = 1.0
        self.kick *= math.exp(-dt / 0.15)
        if self.on_phrase or (self.rt.t - self.t_touch[2] > 30 and int(self.rt.t / 30) != int((self.rt.t - dt) / 30)):
            self.mode = (self.mode + 1) % len(MODES)

    def field(self):
        """The signed wave, about -1..1, for the current picture."""
        t, lam = self.t, self.spacing
        w = self.warp * (1 + 0.6 * self.kick + 0.5 * self.sound[2])
        mode = MODES[self.mode]
        if mode == "current":
            bend = w * 10 * np.sin(X * 0.045 + t * 0.7) * np.sin(Y * 0.02 - t * 0.3)
            breathe = lam * (1 + 0.45 * np.sin(X * 0.03 - t * 0.5))
            return np.sin(2 * math.pi * (Y + bend) / breathe)
        if mode == "squares":
            x0 = 64 + 40 * math.sin(t * 0.21)
            u = X - 0.85 * w * 18 * np.tanh((X - x0) / 18)          # columns crowd into the fold at x0
            v = Y + w * 4 * np.sin(X * 0.05 + t)
            return np.sin(math.pi * u / lam) * np.sin(math.pi * v / lam) * 3
        if mode == "bulge":
            cx, cy = 64 + 34 * math.sin(t * 0.33), 64 + 30 * math.sin(t * 0.27 + 1)
            dx, dy = X - cx, Y - cy
            lens = 1 - 0.75 * min(1.0, w) * np.exp(-(dx * dx + dy * dy) / (2 * (24 + 8 * w) ** 2))
            u, v = cx + dx * lens, cy + dy * lens
            return np.sin(math.pi * u / lam) * np.sin(math.pi * v / lam) * 3
        if mode == "rings":
            r1 = np.hypot(X - 64 - 22 * math.sin(t * 0.4), Y - 64 - 14 * math.cos(t * 0.3))
            r2 = np.hypot(X - 64 + 22 * math.sin(t * 0.33), Y - 64 + 18 * math.cos(t * 0.25))
            return np.sin(2 * math.pi * r1 / lam) * np.sin(2 * math.pi * r2 / lam) * 3
        dx, dy = X - 63.5, Y - 63.5
        r = np.hypot(dx, dy)
        n = max(6, int(round(160 / lam)))
        return np.sin(n * np.arctan2(dy, dx) + w * r * 0.12 * np.sin(t * 0.4) + t * 0.6 - 0.04 * r)

    def render(self):
        s = self.field()
        tone = np.clip(0.5 + 2.2 * s, 0, 1)            # sharp: black, white, and a sliver of grey between
        if self.invert:
            tone = 1 - tone
        return self.print(tone)

    def lights(self):
        return [self.glow(0, 0.0, 0.2 + 0.03 * self.spacing), self.glow(1, 0.12, 0.2 + 0.2 * self.warp),
                self.glow(2, self.mode / len(MODES)), tuple(float(c) for c in self.inks[-1])]
