"""Grove: trees growing and swaying through the seasons, in silhouette, dithered.

After Lee's 0601, its stepped columns of colour. Each tree is a branching
fractal: a trunk that forks, and forks again, seven times, each fork turned a
little at random and a little shorter. They grow from saplings a level at a
time. Wind sways every branch, more towards the tips, since each sways on top
of the swaying of the branch it grows from. The year turns: blossom in
spring, green in summer, orange in autumn with leaves falling and blowing,
bare in winter. The trees are black against a dusk sky; their leaves are spot
inks printed over the dither.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

DEPTH = 7
GROUND = 116
SEASONS = [("spring", (1.0, 0.62, 0.78), 0.7), ("summer", (0.22, 0.62, 0.2), 1.0),
           ("autumn", (1.0, 0.48, 0.08), 0.75), ("winter", None, 0.0)]       # leaf ink, how leafy
YEAR = 64.0                     # seconds round the seasons


class Grove(Inked):
    name = "Grove"
    blurb = "Trees growing and swaying through the seasons, in silhouette (after Lee's 0601). k0 wind, k1 season, k2 screen, k3 inks. Click k0 a gust, k1 grow a new grove, k2 chunky."
    palette, screen_kind = "dusk", "bayer8"

    def __init__(self, rt):
        super().__init__(rt)
        self.seed = 5
        self.wind, self.gust = 1.0, 0.0
        self.year = 10.0
        self.leaves = np.zeros((0, 4), np.float32)        # falling: x, y, vx, vy
        self.t = 0.0
        self.plant()

    def plant(self):
        rng = self.rng = np.random.default_rng(self.seed % 100000)
        self.trees = []
        for x in sorted(rng.uniform(14, 114, 3)):
            levels = []
            for lv in range(DEPTH + 1):
                n = 2 ** lv
                spread = 0.42 + 0.1 * rng.random()
                rel = np.where(np.arange(n) % 2, spread, -spread) + rng.normal(0, 0.18, n) if lv else np.zeros(1)
                shrink = rng.uniform(0.66, 0.8, n) if lv else np.ones(1)
                levels.append((rel.astype(np.float32), shrink.astype(np.float32), rng.uniform(0, 6.28, n).astype(np.float32)))
            self.trees.append((float(x), float(rng.uniform(15, 21)), levels))
        self.grow = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.wind = max(0.0, min(4.0, self.wind + d * 0.15))
        elif k == 1:
            self.year = (self.year + d * YEAR / 16) % YEAR
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.gust = 1.0
        elif k == 1:
            self.seed += 1
            self.plant()
        elif k == 2:
            self.chunky()

    def season(self):
        s = (self.year / YEAR) * 4
        return int(s) % 4, s % 1

    def step(self, dt):
        self.hear(dt)
        dt = min(dt, 1 / 20)
        self.t += dt
        self.year = (self.year + dt * (1 + 2 * self.sound[1])) % YEAR
        self.grow = min(DEPTH + 1.0, self.grow + dt * 0.8)
        self.gust *= math.exp(-dt / 2.0)
        if self.on_beat and self.rt.audio.kick > 0.6:
            self.gust = max(self.gust, 0.5)
        if self.on_phrase:
            self.gust = 1.0
        si, _ = self.season()
        blow = self.wind * (0.5 + 0.5 * math.sin(self.t * 0.4)) + 3 * self.gust
        if SEASONS[si][0] == "autumn" and self.rng.random() < dt * (2 + 4 * blow):     # leaves let go
            tips = self.tips()
            if len(tips):
                i = int(self.rng.integers(len(tips)))
                self.leaves = np.vstack([self.leaves, [[tips[i, 0], tips[i, 1], 0, 0]]]).astype(np.float32)[-120:]
        lv = self.leaves
        if len(lv):
            lv[:, 2] += (blow * 8 - lv[:, 2]) * dt + self.rng.normal(0, 20, len(lv)) * dt
            lv[:, 3] = 9 + 4 * np.sin(self.t * 3 + lv[:, 0])
            lv[:, :2] += lv[:, 2:] * dt
            self.leaves = lv[(lv[:, 1] < GROUND) & (lv[:, 0] > -5) & (lv[:, 0] < N + 5)]

    def skeleton(self):
        """Every branch as (x0, y0, x1, y1, level), swaying in the wind, at its current growth."""
        segs = []
        blow = self.wind * (0.5 + 0.5 * math.sin(self.t * 0.4)) + 3 * self.gust
        for x, trunk, levels in self.trees:
            px, py = np.array([x], np.float32), np.array([GROUND], np.float32)
            ang = np.array([-math.pi / 2], np.float32)
            length = np.array([trunk], np.float32)
            for lv, (rel, shrink, ph) in enumerate(levels):
                if lv:
                    px, py = np.repeat(px, 2), np.repeat(py, 2)
                    ang, length = np.repeat(ang, 2), np.repeat(length, 2)
                sway = blow * 0.025 * (lv + 1) * np.sin(self.t * (1.3 + 0.2 * lv) + ph) + blow * 0.02 * lv
                ang = ang + rel + sway
                length = length * shrink
                g = float(np.clip(self.grow - lv, 0, 1))
                if g <= 0:
                    break
                ex, ey = px + np.cos(ang) * length * g, py + np.sin(ang) * length * g
                segs.append((px, py, ex, ey, lv))
                px, py = ex, ey
        return segs

    def tips(self):
        segs = self.skeleton()
        ends = [np.column_stack([s[2], s[3]]) for s in segs if s[4] == DEPTH]
        return np.concatenate(ends) if ends else np.zeros((0, 2), np.float32)

    def render(self):
        si, frac = self.season()
        name, ink_c, leafy = SEASONS[si]
        sky = 0.15 + 0.55 * np.clip((Y - 10) / 110, 0, 1) ** 1.3
        sky = sky + 0.2 * np.exp(-((X - 96) ** 2 + (Y - 104) ** 2) / 300)     # the low sun
        tone = sky.astype(np.float32)
        tree = np.zeros((N, N), bool)
        tips = []
        for x0, y0, x1, y1, lv in self.skeleton():
            n = max(2, int(np.max(np.hypot(x1 - x0, y1 - y0))) + 1)
            k = np.linspace(0, 1, n, dtype=np.float32)[:, None]
            xs, ys = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
            width = max(0, 3 - lv)                                          # trunks thick, twigs a pixel
            for ox in range(-(width // 2), width - width // 2 + (1 if width == 0 else 0)):
                xi, yi = np.rint(xs + ox).astype(int).ravel(), np.rint(ys).astype(int).ravel()
                ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
                tree[yi[ok], xi[ok]] = True
            if lv == DEPTH:
                tips.append(np.column_stack([x1, y1]))
        tone[tree] = 0.0
        tone[Y >= GROUND] = 0.03
        img = self.print(np.clip(tone, 0, 1))
        # leaves in their season's ink: clusters round the twig tips, thinning as the season turns
        if ink_c is not None and tips and self.grow > DEPTH:
            t = np.concatenate(tips)
            keep = leafy * (1 - (0.6 * frac if name == "autumn" else 0))
            rng = np.random.default_rng(self.seed)
            for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1, -1), (-1, 1)):
                sel = rng.random(len(t)) < keep
                xi, yi = np.rint(t[sel, 0] + dx).astype(int), np.rint(t[sel, 1] + dy).astype(int)
                ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
                img[yi[ok], xi[ok]] = ink_c
        if len(self.leaves) and ink_c is not None:
            xi, yi = self.leaves[:, 0].astype(int), self.leaves[:, 1].astype(int)
            ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
            img[yi[ok], xi[ok]] = ink_c
        return img

    def lights(self):
        si, _ = self.season()
        c = SEASONS[si][1] or (0.6, 0.6, 0.7)
        return [self.glow(0, 0.55, 0.2 + 0.15 * self.wind), tuple(0.6 * v for v in c)] + self.ink_lights()
