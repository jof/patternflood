"""Clock: the real time, on an engraved dial, dithered.

After Lee's 0515-4, its tick marks round a grid. A wall clock showing the
local time: twelve hour bars (heavier at the quarters) and sixty minute ticks
on a dial lit from the upper left, with a bevelled rim and a curve of light
on the glass. The hands are tapered blades with drop shadows; the second
hand is a thin red spot ink that ticks with a little overshoot and settles,
as a quartz clock's does (or sweeps, if you prefer). With the music on, it
ticks on the beat instead of the second, just for fun, and corrects itself
when the music stops.
"""
import math
import time

import numpy as np

from .. import draw
from ..draw import N, X, Y
from .original import Inked

SECOND_INK = (0.95, 0.12, 0.08)
R = 58.0
FACES = ["bars", "dots", "minimal"]


class Clock(Inked):
    name = "Clock"
    blurb = "The real time on an engraved dial (after Lee's 0515-4). k0 face, k1 tick or sweep, k2 screen, k3 inks. Click k1 tick on the beat (with music), k2 chunky."
    palette, screen_kind = "obra", "hatch"

    def __init__(self, rt):
        super().__init__(rt)
        self.face = 0
        self.sweep = False
        self.beat_ticks = True
        self.beat_sec = 0.0             # seconds counted by beats, while the music runs the hand
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.face = (self.face + (1 if d > 0 else -1)) % len(FACES)
        elif k == 1:
            self.sweep = d > 0
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 1:
            self.beat_ticks = not self.beat_ticks
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        if self.listening and self.beat_ticks and self.on_beat:
            self.beat_sec += 1

    def hand(self, img, mask, angle, length, width, tail, value):
        """A tapered blade from the centre (with a short tail) at angle (0 = twelve, clockwise)."""
        s, c = math.sin(angle), -math.cos(angle)
        px, py = -c, s                                         # across the blade
        tip = (63.5 + s * length, 63.5 + c * length)
        back = (63.5 - s * tail, 63.5 - c * tail)
        pts = [(back[0] + px * width, back[1] + py * width), (tip[0] + px * width * 0.25, tip[1] + py * width * 0.25),
               (tip[0] - px * width * 0.25, tip[1] - py * width * 0.25), (back[0] - px * width, back[1] - py * width)]
        shadow = [(x + 2, y + 2.5) for x, y in pts]
        sm = np.zeros((N, N), bool)
        draw.poly(np.zeros((N, N, 1), np.float32), shadow, 1.0, mask_out=sm)
        img[sm & (img > 0.12)] *= 0.55
        hm = np.zeros((N, N), bool)
        draw.poly(np.zeros((N, N, 1), np.float32), pts, 1.0, mask_out=hm)
        img[hm] = value
        mask |= hm

    def render(self):
        now = time.time()
        lt = time.localtime(now)
        frac = now % 1
        sec = lt.tm_sec + (frac if self.sweep else 0)
        if not self.sweep:                                     # a quartz tick: jump, overshoot a hair, settle
            sec += 0.12 * math.exp(-frac * 14) * math.sin(frac * 40)
        if self.listening and self.beat_ticks:
            sec = self.beat_sec % 60 + 0.12 * (1 - self.rt.audio.phase) ** 6
        minute = lt.tm_min + lt.tm_sec / 60
        hour = lt.tm_hour % 12 + minute / 60
        r = np.hypot(X - 63.5, Y - 63.5)
        ang = np.arctan2(X - 63.5, -(Y - 63.5)) % (2 * math.pi)  # 0 at twelve, clockwise
        tone = np.where(r < R, 0.62 + 0.18 * (1 - r / R) - 0.12 * ((X - 30) + (Y - 30)) / 128, 0.04)
        rim = (r >= R) & (r < R + 4)
        tone = np.where(rim, 0.3 + 0.35 * np.clip(-((X - 63.5) + (Y - 63.5)) / (r + 1e-3), 0, 1), tone)
        face = FACES[self.face]
        a12 = (ang * 60 / (2 * math.pi)) % 1
        minute_tick = (np.minimum(a12, 1 - a12) < 0.08) & (r > R - 6) & (r < R - 2)
        a_h = (ang * 12 / (2 * math.pi)) % 1
        near_hour = np.minimum(a_h, 1 - a_h)
        a_q = (ang * 4 / (2 * math.pi)) % 1
        quarter = np.minimum(a_q, 1 - a_q) < 0.02                 # the quarter hours get heavier bars
        if face == "bars":
            hour_mark = (near_hour < 0.012) & (r > R - 14) & (r < R - 2)
            hour_mark |= quarter & (r > R - 16) & (r < R - 2)
        elif face == "dots":
            hour_mark = np.zeros((N, N), bool)
            for h in range(12):
                a = h * math.pi / 6
                hx, hy = 63.5 + math.sin(a) * (R - 8), 63.5 - math.cos(a) * (R - 8)
                hour_mark |= np.hypot(X - hx, Y - hy) < (3.2 if h % 3 == 0 else 2.0)
        else:
            hour_mark = quarter & (r > R - 10) & (r < R - 2)
        if face != "minimal":
            tone = np.where(minute_tick, 0.12, tone)
        tone = np.where(hour_mark, 0.05, tone)
        # the glass: a curve of light near the top left
        tone = tone + 0.18 * np.exp(-((r - R * 0.8) / 3) ** 2) * np.clip(-((X - 63.5) + (Y - 63.5)) / (r + 1e-3) - 0.5, 0, 1)
        tone = tone.astype(np.float32)
        mask = np.zeros((N, N), bool)
        self.hand(tone, mask, hour * math.pi / 6, R * 0.55, 3.2, 8, 0.03)
        self.hand(tone, mask, minute * math.pi / 30, R * 0.82, 2.4, 10, 0.03)
        img = self.print(np.clip(tone, 0, 1))
        # the second hand, in its own red ink, and the centre cap
        a = sec * math.pi / 30
        s, c = math.sin(a), -math.cos(a)
        xs, ys = draw.segment(63.5 - s * 14, 63.5 - c * 14, 63.5 + s * R * 0.9, 63.5 + c * R * 0.9, 0.5)
        xi, yi = np.rint(xs).astype(int), np.rint(ys).astype(int)
        ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
        img[yi[ok], xi[ok]] = SECOND_INK
        cap = np.hypot(X - 63.5, Y - 63.5) < 3
        img[cap] = SECOND_INK
        return img

    def lights(self):
        return [self.glow(0, self.face / 3), tuple(0.5 * v for v in SECOND_INK)] + self.ink_lights()
