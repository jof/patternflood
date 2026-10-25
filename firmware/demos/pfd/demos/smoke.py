"""Smoke: incense smoke curling up through still air, dithered.

After SeungHun's Vector Field Flow. Dye rises from a source near the bottom and is
carried by a flow with no divergence (the curl of a few drifting waves of
"stream function"), so it swirls without bunching up or thinning out. The
swirl grows with height: the plume leaves the source as a smooth ribbon and
breaks into curls as it climbs, as real smoke does. Each frame the dye is
advected (traced back along the flow and sampled), fades slowly, and goes
through a blue-noise screen onto the inks.
"""
import math

import numpy as np

from .. import ink
from ..draw import N, X, Y
from .original import Original

NWAVES = 7
SOURCE_Y = 112.0


def _pal(name):
    return next(i for i, (n, _) in enumerate(ink.PALETTES) if n == name)


def _advect(f, sx, sy):
    """f sampled at (sx, sy) with bilinear weights; zero beyond the edges."""
    x0, y0 = np.floor(sx), np.floor(sy)
    fx, fy = sx - x0, sy - y0
    x0, y0 = x0.astype(np.int32), y0.astype(np.int32)
    pad = np.pad(f, 1)
    xi, yi = np.clip(x0 + 1, 0, N + 1), np.clip(y0 + 1, 0, N + 1)
    xj, yj = np.clip(x0 + 2, 0, N + 1), np.clip(y0 + 2, 0, N + 1)
    return ((pad[yi, xi] * (1 - fx) + pad[yi, xj] * fx) * (1 - fy)
            + (pad[yj, xi] * (1 - fx) + pad[yj, xj] * fx) * fy)


class Smoke(Original):
    name = "Smoke"
    blurb = "Incense smoke curling up, dithered (after SeungHun's Vector Field Flow). k0 turbulence, k1 moves the source, k2 screen, k3 inks. Click k0 gust, k1 puff, k2 chunky, k3 second source."

    def __init__(self, rt):
        super().__init__(rt)
        rng = np.random.default_rng(4)
        ang = rng.uniform(0, 2 * math.pi, NWAVES)
        mag = np.geomspace(0.035, 0.16, NWAVES) * rng.uniform(0.8, 1.2, NWAVES)
        self.k = np.stack([np.cos(ang) * mag, np.sin(ang) * mag], -1).astype(np.float32)
        self.amp = (1.1 / mag).astype(np.float32)               # the same speed at every scale
        self.omega = rng.uniform(0.15, 0.5, NWAVES).astype(np.float32)
        self.phase = rng.uniform(0, 2 * math.pi, NWAVES).astype(np.float32)
        self.dye = np.zeros((N, N), np.float32)
        self.turb = 1.4
        self.src_x = 64.0
        self.two = False
        self.gust = 0.0
        self.t = 0.0
        self.pal_i, self.screen_i, self.scale = _pal("synth"), ink.SCREENS.index("blue"), 1
        self._screen()
        # swirl grows with height: none at the source, full by the top third
        self.lift = np.clip((SOURCE_Y - Y) / 70, 0, 1) ** 1.5

    def _screen(self):
        self.thresh = ink.screen(ink.SCREENS[self.screen_i], self.scale, angle=0.5, pitch=3.0 * self.scale)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.turb = max(0.0, min(3.0, self.turb + d * 0.1))
        elif k == 1:
            self.src_x = max(10.0, min(118.0, self.src_x + self.rt.accel(1, d) * 1.5))
        elif k == 2:
            self.screen_i = (self.screen_i + (1 if d > 0 else -1)) % len(ink.SCREENS)
            self._screen()
        elif k == 3:
            self.pal_i = (self.pal_i + (1 if d > 0 else -1)) % len(ink.PALETTES)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.gust = 25.0 * (1 if self.rt.t % 2 < 1 else -1)
        elif k == 1:
            self.puff(self.src_x, 6.0)
        elif k == 2:
            self.scale = 3 - self.scale
            self._screen()
        elif k == 3:
            self.two = not self.two

    def puff(self, x, size):
        self.dye += 2.5 * np.exp(-((X - x) ** 2 + (Y - SOURCE_Y + 4) ** 2) / (2 * size * size))

    def sources(self):
        xs = [self.src_x]
        if self.two:
            xs.append(N - self.src_x if abs(N - 2 * self.src_x) > 20 else self.src_x + 40)
        return xs

    def step(self, dt):
        self.hear(dt)
        dt = min(dt, 1 / 30)
        self.t += dt
        if self.rt.t - min(self.t_touch) > 25:          # left alone, the source wanders and puffs
            self.src_x = 64 + 34 * math.sin(self.rt.t * 0.05)
            if not self.listening and int(self.rt.t / 7) != int((self.rt.t - dt) / 7):
                self.puff(self.src_x, 4.0 + 2 * math.sin(self.rt.t))
        # the flow: the curl of a sum of drifting plane waves of stream function
        arg = (X[..., None] * self.k[:, 0] + Y[..., None] * self.k[:, 1]
               + self.omega * self.t + self.phase)
        c = np.cos(arg) * self.amp
        swirl = self.turb * (1 + self.sound[0]) * self.lift
        vx = (c @ self.k[:, 1]) * swirl * 9 + self.gust
        vy = -(c @ self.k[:, 0]) * swirl * 9 - 14.0 * (1 + 0.5 * self.sound[2])      # and it rises
        self.gust *= math.exp(-dt / 1.2)
        self.dye = _advect(self.dye, X - vx * dt, Y - vy * dt)
        # a touch of diffusion, and a slow fade
        d = self.dye
        d = 0.92 * d + 0.02 * (np.roll(d, 1, 0) + np.roll(d, -1, 0) + np.roll(d, 1, 1) + np.roll(d, -1, 1))
        self.dye = d * math.exp(-dt / 7.0)
        flicker = 0.8 + 0.2 * math.sin(self.t * 7.3) * math.sin(self.t * 2.9)
        rate = (1.4 + 3 * self.sound[2]) * flicker * dt * 60
        for x in self.sources():
            self.dye += rate * 0.08 * np.exp(-((X - x) ** 2 + (Y - SOURCE_Y) ** 2) / 8.0)
        if self.on_beat and self.rt.audio.kick > 0.5:
            for x in self.sources():
                self.puff(x, 3.0 + 3 * self.sound[2])
        if self.on_phrase:
            self.gust = 30.0 * (1 if self.rt.audio.counts.get("phrase", 0) % 2 else -1)

    def render(self):
        tone = 1 - np.exp(-self.dye * 1.6)
        tone[int(SOURCE_Y) + 3:int(SOURCE_Y) + 5, :] *= 0             # a sharp floor under the sticks
        img = ink.dither(tone, ink.PALETTES[self.pal_i][1], self.thresh, self.scale)
        glow = ink.PALETTES[self.pal_i][1][-1]
        for x in self.sources():                                     # the glowing tips
            img[int(SOURCE_Y), int(x)] = glow
        return img

    def lights(self):
        inks = ink.PALETTES[self.pal_i][1]
        return [self.glow(0, 0.6, 0.2 + 0.2 * self.turb), self.glow(1, 0.08),
                self.glow(2, self.screen_i / len(ink.SCREENS)), tuple(float(c) for c in inks[-1])]
