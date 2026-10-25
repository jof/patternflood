"""Spiro: a spirograph drawing on a page that slowly fades.

After SeungHun's Lissajous Weave. A wheel of r teeth rolls round inside a ring of
R teeth, and a pen in one of its holes traces a hypotrochoid: a rosette that
closes after r / gcd(R, r) trips round the ring. The pen draws quickly onto
a page that fades, so fresh ink is bright and the trace ages down through
the inks (white, then cyan, magenta, violet with the default set). The wheel
and the pen's hole drift on their own, so each new figure lays itself over
the ghost of the last. The ring and the wheel show faintly as they turn.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

RING = 96                       # teeth on the ring
SCALE = 0.6                     # pixels per tooth of radius
STEPS = 520                     # pen samples per frame


class Spiro(Inked):
    name = "Spiro"
    blurb = "A spirograph drawing onto a fading page (after SeungHun's Lissajous Weave). k0 pen speed, k1 wheel size (teeth), k2 screen, k3 inks. Click k0 clear the page, k1 a new figure, k2 chunky."
    palette, screen_kind = "synth", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.wheel, self.hole = 63, 0.75
        self.wheel_f = float(self.wheel)
        self.speed = 1.0
        self.a = 0.0                    # the wheel's angle round the ring
        self.page = np.zeros((N, N), np.float32)
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.speed = max(0.1, min(5.0, self.speed * 1.08 ** d))
        elif k == 1:
            self.wheel = max(12, min(RING - 8, self.wheel + (1 if d > 0 else -1)))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.page[:] = 0
        elif k == 1:
            self.new_figure()
        elif k == 2:
            self.chunky()

    def new_figure(self):
        self.wheel = int(self.rng.integers(18, RING - 10))
        self.hole = float(self.rng.uniform(0.45, 0.95))

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        if self.on_phrase or (min(self.rt.t - t for t in self.t_touch) > 25
                              and int(self.rt.t / 20) != int((self.rt.t - dt) / 20)):
            self.new_figure()
        self.wheel_f += (self.wheel - self.wheel_f) * (1 - math.exp(-dt / 1.5))   # the wheel eases between sizes
        self.hole += 0.02 * math.sin(self.t * 0.3) * dt
        sweep = dt * self.speed * 9 * (1 + 1.5 * self.sound[1])                  # radians of travel round the ring
        a = self.a + np.linspace(0, sweep, STEPS, endpoint=False)
        self.a += sweep
        x, y = self.pen(a)
        xi, yi = np.rint(x).astype(int), np.rint(y).astype(int)
        ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
        self.page *= math.exp(-dt / 7.0)
        np.maximum.at(self.page, (yi[ok], xi[ok]), 1.0)

    def pen(self, a):
        R = RING * SCALE
        r = self.wheel_f * SCALE
        d = self.hole * r
        return (63.5 + (R - r) * np.cos(a) + d * np.cos((R - r) / r * a),
                63.5 + (R - r) * np.sin(a) - d * np.sin((R - r) / r * a))

    def render(self):
        R, r = RING * SCALE, self.wheel_f * SCALE
        # the page: fresh ink bright, ageing down through the inks
        tone = self.page ** 0.7
        # the ring and the wheel, faint, and the pen's spot
        rr = np.hypot(X - 63.5, Y - 63.5)
        tone = np.maximum(tone, 0.12 * (np.abs(rr - R) < 0.7))
        wx, wy = 63.5 + (R - r) * math.cos(self.a), 63.5 + (R - r) * math.sin(self.a)
        tone = np.maximum(tone, 0.1 * (np.abs(np.hypot(X - wx, Y - wy) - r) < 0.7))
        px, py = self.pen(np.array([self.a]))
        tone = np.maximum(tone, np.exp(-((X - px[0]) ** 2 + (Y - py[0]) ** 2) / 3) * (1 + 0.5 * self.beat))
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.85, 0.2 + 0.1 * self.speed), self.glow(1, self.wheel / RING)] + self.ink_lights()
