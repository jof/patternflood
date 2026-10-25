"""Koi: carp circling a dark pond under lily pads, dithered.

After SeungHun's 0614-2, its spotted tiles. Each koi is a spine of linked
segments: the head steers towards a target that wanders round the pond, and
every segment after it is pulled along at a fixed distance, so the body
bends through each turn and the tail sweeps. The body is drawn as discs
along the spine, thick behind the head and tapering to a fanned tail, in
patches of orange, white and black. Lily pads (a green spot ink) drift on
top, and the fish pass under them. Drop food (click k1) and they all come.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

NFISH = 6
SEGS = 14
SEG_LEN = 2.3
PAD_INK = (0.12, 0.42, 0.14)
PAD_VEIN = (0.06, 0.26, 0.08)


class Koi(Inked):
    name = "Koi"
    blurb = "Koi circling a dark pond under lily pads, dithered (after SeungHun's 0614-2). k0 swim speed, k1 food (click), k2 screen, k3 inks. Click k1 drop food, k2 chunky."
    palette, screen_kind = "koi", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        rng = self.rng = np.random.default_rng(17)
        self.spine = np.zeros((NFISH, SEGS, 2), np.float32)
        for f in range(NFISH):
            x, y, a = rng.uniform(20, 108), rng.uniform(20, 108), rng.uniform(0, 2 * math.pi)
            self.spine[f] = np.column_stack([x - np.cos(a) * SEG_LEN * np.arange(SEGS), y - np.sin(a) * SEG_LEN * np.arange(SEGS)])
        self.heading = rng.uniform(0, 2 * math.pi, NFISH).astype(np.float32)
        self.size = rng.uniform(0.8, 1.25, NFISH).astype(np.float32)
        # each fish's pattern: a tone per segment (0 black, 0.66 orange, 1 white)
        self.pattern = rng.choice([0.66, 1.0, 0.66, 0.0], size=(NFISH, SEGS)).astype(np.float32)
        for f in range(NFISH):                       # patches, not speckle: smooth along the body
            self.pattern[f] = np.repeat(rng.choice([0.66, 1.0, 0.0], size=SEGS // 3 + 1, p=[0.5, 0.35, 0.15]), 3)[:SEGS]
            self.pattern[f, 0] = rng.choice([0.66, 1.0])
        self.target = rng.uniform(20, 108, (NFISH, 2)).astype(np.float32)
        self.pads = np.column_stack([rng.uniform(0, N, 7), rng.uniform(0, N, 7), rng.uniform(7, 13, 7),
                                     rng.uniform(0, 2 * math.pi, 7)]).astype(np.float32)
        self.food = None
        self.speed = 1.0
        self.rings = []                              # (x, y, t0): ripples where they mouth the surface
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.speed = max(0.2, min(3.0, self.speed * 1.07 ** d))
        elif k == 1:
            pass
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 1:
            self.food = [float(self.rng.uniform(25, 103)), float(self.rng.uniform(25, 103)), 6.0]
            self.rings.append((self.food[0], self.food[1], self.t))
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        dt = min(dt, 1 / 20)
        self.t += dt
        rng = self.rng
        head = self.spine[:, 0]
        if self.on_phrase:
            self.food = [float(rng.uniform(25, 103)), float(rng.uniform(25, 103)), 6.0]
        for f in range(NFISH):
            tgt = self.target[f]
            if self.food is not None:
                tgt = np.array(self.food[:2], np.float32) + np.array([math.cos(f * 1.1), math.sin(f * 1.1)], np.float32) * 4
            elif np.hypot(*(tgt - head[f])) < 10:
                self.target[f] = rng.uniform(15, 113, 2)
            want = math.atan2(tgt[1] - head[f, 1], tgt[0] - head[f, 0])
            turn = (want - self.heading[f] + math.pi) % (2 * math.pi) - math.pi
            self.heading[f] += max(-2.0, min(2.0, turn * 2.2)) * dt
        sp = 16 * self.speed * (1 + 0.8 * self.sound[1]) * self.size * (1.6 if self.food else 1)
        # a swimming wiggle: the head sways across its heading as the tail beats
        sway = 0.35 * np.sin(self.t * 7 * self.speed + np.arange(NFISH))
        step = np.column_stack([np.cos(self.heading + sway), np.sin(self.heading + sway)]) * sp[:, None] * dt
        self.spine[:, 0] += step
        for i in range(1, SEGS):                     # each segment follows at a fixed distance
            d = self.spine[:, i] - self.spine[:, i - 1]
            dist = np.sqrt((d ** 2).sum(1, keepdims=True)) + 1e-6
            self.spine[:, i] = self.spine[:, i - 1] + d / dist * SEG_LEN * self.size[:, None]
        if self.food is not None:
            self.food[2] -= dt
            if self.food[2] <= 0:
                self.food = None
        self.pads[:, 0] += np.sin(self.t * 0.05 + self.pads[:, 3]) * 0.6 * dt
        self.pads[:, 1] += np.cos(self.t * 0.04 + self.pads[:, 3]) * 0.6 * dt
        self.pads[:, 3] += 0.02 * dt
        if rng.random() < dt * 0.4:                  # someone mouths the surface
            f = int(rng.integers(NFISH))
            self.rings.append((float(head[f, 0]), float(head[f, 1]), self.t))
        self.rings = [r for r in self.rings if self.t - r[2] < 3]

    def render(self):
        t = self.t
        # the water: dark, with a slow shimmer of light across it
        tone = 0.1 + 0.06 * np.sin(X * 0.13 + t * 0.6) * np.sin(Y * 0.11 - t * 0.5) + 0.04 * np.sin((X + Y) * 0.07 + t)
        tone = tone.astype(np.float32)
        for x, y, t0 in self.rings:
            age = t - t0
            d = np.hypot(X - x, Y - y)
            tone += 0.25 * np.exp(-((d - 14 * age) / 1.2) ** 2) * math.exp(-age)
        # the fish, deepest drawn first: body discs along the spine, tapering, then the tail fan
        for f in np.argsort(self.size):
            sp = self.spine[f]
            for i in range(SEGS - 1, -1, -1):
                frac = i / (SEGS - 1)
                r = (2.9 * math.sin(math.pi * min(1.0, (frac + 0.12) * 1.05)) + 0.6) * self.size[f]
                x, y = sp[i]
                x0, x1 = max(0, int(x - r - 1)), min(N, int(x + r) + 2)
                y0, y1 = max(0, int(y - r - 1)), min(N, int(y + r) + 2)
                if x0 >= x1 or y0 >= y1:
                    continue
                inside = (X[y0:y1, x0:x1] - x) ** 2 + (Y[y0:y1, x0:x1] - y) ** 2 < r * r
                tone[y0:y1, x0:x1][inside] = self.pattern[f, i]
            # the tail: a fan off the last segment, swinging
            tx, ty = sp[-1]
            back = sp[-1] - sp[-2]
            ang = math.atan2(back[1], back[0]) + 0.5 * math.sin(self.t * 7 * self.speed + f)
            for s in (-0.45, 0.45):
                for k in range(1, 6):
                    px, py = tx + math.cos(ang + s) * k * self.size[f], ty + math.sin(ang + s) * k * self.size[f]
                    if 0 <= px < N and 0 <= py < N:
                        tone[int(py), int(px)] = 0.8
        if self.food is not None:                    # the pellets, floating
            fx, fy = int(self.food[0]), int(self.food[1])
            for k in range(6):
                px, py = fx + int(3 * math.cos(k * 2.1)), fy + int(3 * math.sin(k * 1.7))
                if 0 <= px < N and 0 <= py < N:
                    tone[py, px] = 0.66
        img = self.print(np.clip(tone, 0, 1))
        # lily pads, over everything, in their own green ink: a disc with a notch and a vein
        for x, y, r, a in self.pads:
            d = np.hypot(X - x, Y - y)
            ang = (np.arctan2(Y - y, X - x) - a + math.pi) % (2 * math.pi) - math.pi
            pad = (d < r) & (np.abs(ang) > 0.25)
            img[pad] = PAD_INK
            vein = pad & ((np.abs(ang - 1.6) < 0.04) | (np.abs(ang + 1.6) < 0.04) | (np.abs(np.abs(ang) - math.pi) < 0.04))
            img[vein] = PAD_VEIN
        return img

    def lights(self):
        return [self.glow(0, 0.08, 0.2 + 0.2 * self.speed), self.glow(1, 0.1, 0.8 if self.food else 0.2)] + self.ink_lights()
