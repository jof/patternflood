"""Plankton: a dark sea full of bioluminescence that lights where it's stirred.

After Lee's 0526, its glowing vortex. Three
thousand plankton drift on a slow current. Each is dark until something
disturbs it, then flares blue and fades over a second or two. A hand trails
through the water (k0 and k1 steer it, as on an Etch A Sketch; left alone it
wanders), leaving a glowing wake that the current then carries and swirls
away. A click splashes, lighting a ring that spreads. With music, each kick
splashes somewhere. Dithered into deep blues.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

COUNT = 6000


class Plankton(Inked):
    name = "Plankton"
    blurb = "A dark sea of bioluminescence that lights where you stir it (after Lee's 0526). k0/k1 steer your hand, k2 screen, k3 inks. Click k0 splash, k1 a wave over all of it, k2 chunky."
    palette, screen_kind = "ice", "blue"

    def __init__(self, rt):
        super().__init__(rt)
        rng = self.rng = np.random.default_rng()
        self.p = rng.uniform(0, N, (COUNT, 2)).astype(np.float32)
        self.glow_ = np.zeros(COUNT, np.float32)
        self.hand = np.array([64.0, 64.0], np.float32)
        self.last = self.hand.copy()
        self.splashes = []                    # (x, y, t0)
        self.t = 0.0
        self.t_steer = -100.0

    def turn(self, k, d):
        self.touch(k)
        if k in (0, 1):
            self.hand[k] = float(np.clip(self.hand[k] + self.rt.accel(k, d) * (1 if k == 0 else -1) * 1.5, 0, N - 1))
            self.t_steer = self.rt.t
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.splashes.append((float(self.hand[0]), float(self.hand[1]), self.t))
        elif k == 1:
            self.glow_ = np.maximum(self.glow_, self.rng.uniform(0.4, 1.0, COUNT).astype(np.float32))
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        dt = min(dt, 1 / 20)
        self.t += dt
        t = self.t
        if self.rt.t - self.t_steer > 8:      # left alone, the hand wanders through the water
            self.hand = np.array([64 + 44 * math.sin(t * 0.23), 64 + 40 * math.sin(t * 0.31 + 1)], np.float32)
        # the current: a slow curl of a few waves, plus a drift
        x, y = self.p[:, 0], self.p[:, 1]
        vx = 3 * np.cos(y * 0.05 + t * 0.2) + 2 * np.sin(x * 0.03 - t * 0.1) + 2
        vy = 3 * np.sin(x * 0.05 - t * 0.15) + 2 * np.cos(y * 0.04 + t * 0.12)
        # the hand pushes water aside as it moves, and lights what it touches
        move = self.hand - self.last
        self.last = self.hand.copy()
        speed = float(np.hypot(*move)) / max(dt, 1e-3)
        steps = max(1, int(np.hypot(*move) / 2) + 1)        # light all along the path since last frame
        for f in np.linspace(0, 1, steps):
            at = self.last - move * (1 - f)
            near = ((self.p - at) ** 2).sum(1) < 9 ** 2
            self.glow_[near] = np.maximum(self.glow_[near], min(1.0, 0.55 + speed / 50))
        d = self.p - self.hand
        dist = np.sqrt((d ** 2).sum(1)) + 1e-3
        push = np.clip(1 - dist / 9, 0, 1)[:, None] * (move[None, :] * 0.3 + d / dist[:, None] * 0.08)   # a gentle stir: the wake keeps its glow
        self.p += np.column_stack([vx, vy]) * dt + push
        self.p %= N
        for sx, sy, t0 in self.splashes:      # a splash: a spreading ring that lights as it passes
            ring = np.abs(np.hypot(self.p[:, 0] - sx, self.p[:, 1] - sy) - 40 * (t - t0)) < 2.5
            self.glow_[ring] = np.maximum(self.glow_[ring], 0.9 * math.exp(-(t - t0)))
        self.splashes = [s for s in self.splashes if t - s[2] < 2.0]
        if self.on_beat and self.rt.audio.kick > 0.6:
            self.splashes.append((float(self.rng.uniform(15, 113)), float(self.rng.uniform(15, 113)), t))
        if self.on_phrase:
            self.glow_ = np.maximum(self.glow_, self.rng.uniform(0.3, 0.9, COUNT).astype(np.float32))
        self.glow_ *= math.exp(-dt / 2.2)

    def render(self):
        xi, yi = self.p[:, 0].astype(int) % N, self.p[:, 1].astype(int) % N
        img = np.zeros((N, N), np.float32)
        np.maximum.at(img, (yi, xi), self.glow_)
        halo = (img + np.roll(img, 1, 0) + np.roll(img, -1, 0) + np.roll(img, 1, 1) + np.roll(img, -1, 1)) / 5
        dark = np.zeros((N, N), np.float32)
        np.maximum.at(dark, (yi, xi), 0.06)                       # unlit plankton, barely there
        tone = np.maximum.reduce([img, halo * 1.3, dark]) + 0.025 * (1 + np.sin(X * 0.05 + Y * 0.03 + self.t * 0.3))
        return self.print(np.clip(tone * (1 + 0.3 * self.beat), 0, 1))

    def lights(self):
        return [self.glow(0, 0.55), self.glow(1, 0.55)] + self.ink_lights()
