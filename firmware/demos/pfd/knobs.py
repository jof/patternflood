"""Knobs that turn a value smoothly along a range with ends, instead of stepping and wrapping.

The encoders click in detents (24 a turn), and the demos began by adding a fixed step per
detent, then clamping it or wrapping it round with %. Wrapped, the top of a range jumps
straight back to the bottom; stepped, every detent shows as a jump. These replace that:

A Dial holds the knob's position along its range (0 at one end, 1 at the other), and its value is
a curve of that position, chosen for what the knob turns:
    lin   evenly spaced
    log   equal ratios per detent, for rates, sizes, zooms, anything you'd double
    bi    a signed value that reverses (a speed): finer near zero, which it catches on going
          through (a turn that would cross it stops there), so stopping dead is easy to find
The value glides to where the knob points, a few hundredths of a second behind, so detents
don't show as jumps. Spun fast, a detent goes further (rt.accel). At the ends it stops: further
turns do nothing, and the knob's light blinks to say so.

A Choice is a knob over a list (pictures, screens, inks). It stops at the ends too, rather than
coming round, and when it changes it dissolves from the last item to the next (`fade`), so a
demo can draw both and mix them (`dissolve`).

Both are moved on in step(dt) (Original.hear calls it for those made with self.dial / self.choice),
so a session's replay lands them where they were.
"""
import math

import numpy as np

from .runtime import DETENTS_PER_REV

GLIDE_S = 0.08          # the value's lag behind the knob
FADE_S = 0.35           # a Choice's dissolve from one item to the next
STOP_S = 0.45           # how long the light blinks at an end


class Dial:
    def __init__(self, rt, k, lo, hi, value, curve="lin", turns=1.5, top=3.0, bend=1.6):
        """lo..hi over `turns` revolutions at a slow turn; `top` is the most a fast spin multiplies a
        detent by; `bend` how much finer a bi Dial is near zero (1: not at all)."""
        assert curve in ("lin", "log", "bi"), curve
        assert curve != "log" or 0 < lo < hi, "log needs 0 < lo < hi"
        assert curve != "bi" or lo < 0 < hi, "bi needs lo < 0 < hi"
        self.rt, self.k, self.lo, self.hi, self.curve, self.top, self.bend = rt, k, lo, hi, curve, top, bend
        self.per_detent = 1.0 / (turns * DETENTS_PER_REV)
        self.target = self.pos = self.u_of(value)
        self.t_stop = -10.0

    # position <-> value

    def value_of(self, u):
        if self.curve == "lin":
            return self.lo + (self.hi - self.lo) * u
        if self.curve == "log":
            return self.lo * (self.hi / self.lo) ** u
        s = 2 * u - 1                                       # -1..1, zero in the middle
        return (self.hi if s > 0 else -self.lo) * math.copysign(abs(s) ** self.bend, s)

    def u_of(self, v):
        v = min(self.hi, max(self.lo, v))
        if self.curve == "lin":
            return (v - self.lo) / (self.hi - self.lo)
        if self.curve == "log":
            return math.log(v / self.lo) / math.log(self.hi / self.lo)
        if v == 0:
            return 0.5
        a = (v / self.hi if v > 0 else v / self.lo) ** (1 / self.bend)
        return (math.copysign(a, v) + 1) / 2

    @property
    def v(self):
        """The value now, gliding."""
        return self.value_of(self.pos)

    @property
    def to(self):
        """Where it's gliding to."""
        return self.value_of(self.target)

    @property
    def u(self):
        """The position now, 0..1 (for lights)."""
        return self.pos

    # moving it

    def turn(self, d):
        """d detents (+ clockwise, as the runtime gives them). False if it was at its end already."""
        u = self.target + self.rt.accel(self.k, d, top=self.top) * self.per_detent
        if (u > 1 and self.target >= 1) or (u < 0 and self.target <= 0):
            self.t_stop = self.rt.t
            return False
        if self.curve == "bi" and (self.target - 0.5) * (u - 0.5) < 0:
            u = 0.5                                         # going through zero: stop on it first
        self.target = min(1.0, max(0.0, u))
        return True

    def set(self, value, glide=True):
        self.target = self.u_of(value)
        if not glide:
            self.pos = self.target

    def step(self, dt):
        self.pos += (self.target - self.pos) * (1 - math.exp(-dt / GLIDE_S))
        if abs(self.target - self.pos) < 1e-5:
            self.pos = self.target

    @property
    def stopped(self):
        """0..1 while the light should blink: the knob was turned against an end just now."""
        a = self.rt.t - self.t_stop
        return 0.0 if a > STOP_S else float(int(a / 0.075) % 2 == 0)


class Choice:
    def __init__(self, rt, n, index=0):
        self.rt, self.n = rt, n
        self.i = self.was = index
        self.fade = 1.0                 # 0 just changed (all `was`) .. 1 settled (all `i`)
        self.t_stop = -10.0

    def turn(self, d):
        """One item along per turn event, either way. False at an end."""
        j = self.i + (1 if d > 0 else -1)
        if not 0 <= j < self.n:
            self.t_stop = self.rt.t
            return False
        self.go(j)
        return True

    def go(self, j, fade=True):
        """To item j (any of them: an automatic change may come round from the last to the first)."""
        j %= self.n
        if j == self.i:
            return
        if self.fade >= 0.5:            # the dissolve carries on from whichever item is showing more
            self.was = self.i
        self.i = j
        self.fade = 0.0 if fade else 1.0
        if not fade:
            self.was = j

    def step(self, dt):
        self.fade = min(1.0, self.fade + dt / FADE_S)

    @property
    def mixing(self):
        return self.fade < 1.0 and self.was != self.i

    @property
    def stopped(self):
        a = self.rt.t - self.t_stop
        return 0.0 if a > STOP_S else float(int(a / 0.075) % 2 == 0)


_MASK = None


def dissolve_mask():
    """A (128, 128) map of thresholds in [0, 1) for dissolves: white noise, a pixel at a time, so it
    lines up with none of the screens (and costs nothing to make, unlike blue noise's 0.1 s).
    A pixel shows the new item once fade passes its value."""
    global _MASK
    if _MASK is None:
        _MASK = np.random.default_rng(5).random((128, 128), dtype=np.float32)
    return _MASK


def dissolve(choice, a, b):
    """Mix two (128, 128[, 3]) pictures by a Choice's fade: a is the old item's, b the new's."""
    m = dissolve_mask() < choice.fade
    return np.where(m[..., None] if np.ndim(a) == 3 else m, b, a)
