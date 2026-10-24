"""The three bench patterns from knob_renderer.py, with the same knob map: the baseline.

Steps are larger than knob_renderer's: there, it took several detents to see a
change. Each detent now moves a parameter by a perceptually even step, and
shows a gauge along the bottom edge, so every click visibly does something,
even speed, which can't show in a single frame.
"""
import math

import numpy as np

import knob_renderer as kr
from ..draw import hsv1
from ..runtime import Demo

STEP = 1.15                 # speed, scale and level: x1.15 a detent
SPEED = (0.05, 8.0)
SCALE = (0.25, 4.0)
LEVEL = (0.05, 1.0)
GAUGE_S = 1.2


def _mul(v, d, lo_hi):
    lo, hi = lo_hi
    return min(hi, max(lo, v * STEP ** d))


def _logpos(v, lo_hi):
    lo, hi = lo_hi
    return math.log(v / lo) / math.log(hi / lo)


class Classic(Demo):
    name = "Classic"
    blurb = "Plasma, tunnel, ripples. k0 hue, k1 speed, k2 scale, k3 level. Click k0 next pattern, k1 freeze, k3 blackout."

    def __init__(self, rt):
        super().__init__(rt)
        self.pattern, self.hue, self.speed, self.scale, self.level = 0, 0.0, 1.0, 1.0, 1.0
        self.frozen = self.black = False
        self.t_anim = 0.0
        self.gauge = None               # (knob, time of last turn)

    def turn(self, k, d):
        d = self.rt.accel(k, d, top=4)
        if k == 0:
            self.hue = (self.hue + d / 24.0) % 1.0
        elif k == 1:
            self.speed = _mul(self.speed, d, SPEED)
        elif k == 2:
            self.scale = _mul(self.scale, d, SCALE)
        elif k == 3:
            self.level = _mul(self.level, d, LEVEL)
        self.gauge = (k, self.rt.t)

    def release(self, k, click):
        if not click:
            return
        if k == 0:
            self.pattern = (self.pattern + 1) % len(kr.PATTERNS)
            self.rt.t_banner = self.rt.t
        elif k == 1:
            self.frozen = not self.frozen
        elif k == 2:
            self.__init__(self.rt)
        elif k == 3:
            self.black = not self.black

    def step(self, dt):
        if not self.frozen:
            self.t_anim += dt * self.speed

    def render(self):
        rgb = kr.PATTERNS[self.pattern][1](self.t_anim, self.scale, self.hue)
        rgb = rgb * (0.0 if self.black else self.level)
        if self.gauge and self.rt.t - self.gauge[1] < GAUGE_S:
            k = self.gauge[0]
            a = min(1.0, 3 * (GAUGE_S - (self.rt.t - self.gauge[1])))
            pos = [self.hue, _logpos(self.speed, SPEED), _logpos(self.scale, SCALE), _logpos(self.level, LEVEL)][k]
            colour = np.array([hsv1(self.hue), (0.2, 1, 0.3), (0.3, 0.5, 1), (1, 1, 1)][k], np.float32)
            bar = rgb[122:126, 4:124]
            bar *= 1 - 0.8 * a
            bar += 0.12 * a                                  # the track
            x = int(round(pos * 119))
            if k == 0:                                       # hue wraps: a marker, not a fill
                bar[:, max(0, x - 1):x + 2] = colour * a
            else:
                bar[:, :x + 1] = colour * a
        return rgb

    def lights(self):
        return [hsv1(self.hue),
                (0.7, 0, 0) if self.frozen else (0, 0.3 + 0.7 * _logpos(self.speed, SPEED), 0),
                (0, 0, 0.3 + 0.7 * _logpos(self.scale, SCALE)),
                (0, 0, 0) if self.black else (self.level,) * 3]
