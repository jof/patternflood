"""A wave pool of isometric pillars, after Lee's 0624 (isometric pillars waving
in 3D). Each knob drives a wave paddle on one side, in the same seats as
Squash (k0 left, k3 right, k1 near, k2 far). Every detent is a push, so spinning
faster makes bigger waves: the rate of turn is the input.
"""
import math

import numpy as np

from ..draw import N, hsv
from .squash import COLOURS
from ..runtime import Demo

G = 14                      # pool cells a side
TW, TH = 8, 4               # tile width/height on screen
LIFT = 11.0                 # px of pillar per unit of water
BASE = 10.0                 # px of pillar at rest
CX, CY = 64, 34             # screen position of the far corner's top


class Pool(Demo):
    name = "Pool"
    blurb = "Wave pool, after Lee's 0624. Each knob is a paddle on one side; spin faster for bigger waves. Click a knob for one big push."

    def __init__(self, rt):
        super().__init__(rt)
        self.u = np.zeros((G, G), np.float32)
        self.prev = np.zeros((G, G), np.float32)
        self.t_push = [-10.0] * 4
        # half-widths of a tile's top face per column offset, for drawing
        self.dxs = np.arange(-TW // 2, TW // 2)
        self.rh = (TH / 2) * (1 - np.abs(self.dxs + 0.5) / (TW / 2))

    def _edge(self, k):
        """The row of cells a paddle pushes: k0 left (i=0), k3 right, k1 near (j=G-1), k2 far."""
        return {0: np.s_[:, 0], 3: np.s_[:, G - 1], 1: np.s_[G - 1, :], 2: np.s_[0, :]}[k]

    def push(self, k, amount):
        sl = self._edge(k)
        self.u[sl] += amount
        self.t_push[k] = self.rt.t

    def turn(self, k, d):
        self.push(k, 0.07 * abs(d))

    def release(self, k, click):
        if click:
            self.push(k, 0.6)

    def step(self, dt):
        for _ in range(max(1, int(round(dt * 90)))):
            u = self.u
            p = np.pad(u, 1, mode="edge")                 # reflecting walls
            lap = p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] - 4 * u
            new = (2 * u - self.prev + 0.2 * lap) * 0.995
            new -= new.mean()                             # paddles move water about; they don't add any
            self.prev, self.u = u, new

    def render(self):
        h = np.clip(self.u, -0.7, 1.2)
        # one colour per pillar face: [top, left side, right side], plus the background at 0
        c = hsv(0.55 - 0.08 * h, np.maximum(0.0, 0.8 - 0.5 * np.maximum(0.0, h - 0.6)),
                np.minimum(1.0, 0.45 + 0.35 * h)).reshape(G * G, 3).astype(np.float32)
        palette = np.concatenate([[(0.01, 0.01, 0.03)], np.stack([c, c * 0.55, c * 0.75], 1).reshape(-1, 3)])
        face_of = np.where(self.dxs < 0, 2, 3)                    # palette offset of each column's side face
        idx = np.zeros((N, N), np.int32)                          # which face each pixel shows
        # Back to front, a diagonal (i + j = s) at a time. Pillars on one diagonal sit
        # exactly a tile apart, so they never overlap and can be drawn in one pass.
        for s in range(2 * G - 1):
            j = np.arange(max(0, s - G + 1), min(G, s + 1))
            i = s - j
            sx = CX + (i - j) * (TW // 2)
            sy = CY + (i + j) * (TH // 2)
            top = sy - (BASE + h[j, i] * LIFT).astype(int)
            cols = (sx[:, None] + self.dxs[None, :]).ravel()
            ok = (cols >= 0) & (cols < N)
            cols = cols[ok]
            t0 = np.rint(top[:, None] - self.rh[None, :]).astype(int).ravel()[ok]
            t1 = np.rint(top[:, None] + self.rh[None, :]).astype(int).ravel()[ok]
            ground = np.repeat(sy + 26, TW)[ok]
            base = np.repeat((j * G + i) * 3, TW)[ok]
            side_id = base + np.tile(face_of, len(j))[ok]
            r0, r1 = max(0, int(t0.min())), min(N, int(ground.max()))
            if r0 >= r1:
                continue
            rows = np.arange(r0, r1)[:, None]
            sub = idx[r0:r1, cols]
            sub = np.where((rows >= t1) & (rows < ground), side_id, sub)
            sub = np.where((rows >= t0) & (rows <= t1), base + 1, sub)
            idx[r0:r1, cols] = sub
        return palette[idx]

    def lights(self):
        out = []
        for k in range(4):
            a = max(0.0, 1 - (self.rt.t - self.t_push[k]) / 0.4)
            out.append(tuple(v * (0.2 + 0.8 * a) for v in COLOURS[k]))
        return out
