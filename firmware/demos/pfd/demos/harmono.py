"""Harmonograph: two pendulums, x and y. Tune their ratio until the figure locks.

The curve shown is the pen's recent path. At an irrational ratio it crawls;
near a simple ratio (3:2, 5:4, ...) it snaps exactly onto it, the figure
closes and holds still, and the knob lights flash. Finding those locks by feel
is the instrument.
"""
import math
from fractions import Fraction

import numpy as np

from .. import draw
from ..draw import N, hsv
from ..runtime import Demo

LOCK = 0.008                # ratio distance that snaps
BASE_HZ = 0.35
POINTS = 5000
PALETTES = [(0.0, 0.35), (0.55, 0.2), (0.08, 0.08), (0.75, 0.6)]   # (hue, hue spread along the trail)


def _ratios():
    out = set()
    for q in range(1, 7):
        for p in range(1, 9):
            out.add(Fraction(p, q))
    return sorted(out)


RATIOS = _ratios()


class Harmono(Demo):
    name = "Harmono"
    blurb = "k0 and k1 tune the two pendulums. Simple ratios lock and the figure holds still. k2 spins it, k3 trail. Click k0 snap, k2 stop spin, k3 colours."

    def __init__(self, rt):
        super().__init__(rt)
        self.fx, self.fy = 3.0, 2.0
        self.spin = 0.25            # phase drift, rad/s: makes a locked figure turn like a 3D wire
        self.trail = 3.0            # seconds of path shown
        self.palette = 0
        self.phase = 0.0
        self.tp = 0.0               # pen time
        self.t_lock = -10.0
        self.was_locked = None

    def _effective(self):
        r = self.fx / self.fy
        best = min(RATIOS, key=lambda f: abs(float(f) - r))
        if abs(float(best) - r) < LOCK * max(1.0, r):
            return self.fy * float(best), self.fy, best
        return self.fx, self.fy, None

    def turn(self, k, d):
        if k == 0:
            self.fx = min(8.0, max(0.5, self.fx + self.rt.accel(0, d, top=10) * 0.005))
        elif k == 1:
            self.fy = min(8.0, max(0.5, self.fy + self.rt.accel(1, d, top=10) * 0.005))
        elif k == 2:
            self.spin = max(-2.0, min(2.0, self.spin + d * 0.05))
            if abs(self.spin) < 0.026:
                self.spin = 0.0
        elif k == 3:
            self.trail = min(20.0, max(0.3, self.trail * (1.1 ** d)))

    def release(self, k, click):
        if not click:
            return
        if k == 0:
            r = self.fx / self.fy
            self.fx = self.fy * float(min(RATIOS, key=lambda f: abs(float(f) - r)))
        elif k == 2:
            self.spin = 0.0
        elif k == 3:
            self.palette = (self.palette + 1) % len(PALETTES)

    def step(self, dt):
        self.tp += dt
        self.phase += self.spin * dt
        locked = self._effective()[2]
        if locked is not None and locked != self.was_locked:
            self.t_lock = self.rt.t
        self.was_locked = locked

    def render(self):
        ax, ay, locked = self._effective()
        w = 2 * math.pi * BASE_HZ
        s = np.linspace(self.tp - self.trail, self.tp, POINTS)
        # phase drift is applied to the whole figure, so a locked figure turns rigidly
        x = np.sin(ax * w * s + self.phase)
        y = np.sin(ay * w * s)
        age = (self.tp - s) / self.trail                    # 0 at the pen, 1 at the tail
        hue0, spread = PALETTES[self.palette]
        rgb = hsv(hue0 + spread * age, np.full_like(age, 0.85), np.clip(1 - age, 0, 1) ** 1.3)
        dens = max(1.0, POINTS / (self.trail * 250))       # keep brightness steady as the trail grows
        img = draw.blank()
        amp = 58 * getattr(self, "amp", 1.0)
        draw.plot(img, 63.5 + amp * x, 63.5 + amp * y, rgb / dens * 2.2)
        # soft glow: a cheap blur of the line
        glow = (np.roll(img, 1, 0) + np.roll(img, -1, 0) + np.roll(img, 1, 1) + np.roll(img, -1, 1)) * 0.12
        img = img + glow
        draw.disc(img, 63.5 + amp * x[-1], 63.5 + amp * y[-1], 1.3, (1, 1, 1), soft=0.6)

        flash = max(0.0, 1 - (self.rt.t - self.t_lock) / 0.6)
        if locked is not None:
            label = f"{locked.numerator}:{locked.denominator}"
            g = 0.25 + 0.75 * flash
            draw.text(img, label, 125 - draw.text_width(label), 115, (g, g, g))
        return img

    def lights(self):
        locked = self._effective()[2]
        flash = max(0.0, 1 - (self.rt.t - self.t_lock) / 0.6)
        if locked is not None:
            tune = (0.3 + 0.7 * flash, 0.9, 0.3 + 0.7 * flash)        # green, flaring white on the lock
        else:
            tune = (0.5, 0.15, 0.0)
        hue0, _ = PALETTES[self.palette]
        sp = min(1.0, abs(self.spin) / 2)
        return [tune, tune,
                (0.2, 0.2, 0.2) if self.spin == 0 else tuple(hsv(np.array(hue0), np.array(1.0), np.array(0.2 + 0.8 * sp))),
                (0.1 + 0.04 * self.trail,) * 3]
