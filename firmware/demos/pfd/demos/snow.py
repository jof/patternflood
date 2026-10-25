"""Snow: a village at night in falling snow, dithered.

After SeungHun's 0515-3, its soft glow. Snow falls in three layers: far flakes
small, slow and dim; near ones bigger, faster, swaying more. Under it a row of
houses, roofs and chimneys in silhouette, windows lit warm (now and then one
goes dark, or comes on). Smoke curls from the chimneys and drifts with the
wind. The snow settles: drifts on the ground and the roofs build up slowly
where flakes land, until a click of k0 clears them. A moon behind thin cloud.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

LAYERS = [(160, 0.5, 9.0, 0.35), (110, 1.0, 16.0, 0.6), (50, 1.6, 28.0, 0.95)]   # count, size, speed, brightness
GROUND = 116


class Snow(Inked):
    name = "Snow"
    blurb = "A village at night in falling snow, dithered (after SeungHun's 0515-3). k0 snowfall, k1 wind, k2 screen, k3 inks. Click k0 clear the drifts, k1 lights on or off, k2 chunky."
    palette, screen_kind = "ice", "bayer4"
    WINDOW_INK = (1.0, 0.62, 0.22)              # a spot ink, printed over whatever the palette is

    def __init__(self, rt):
        super().__init__(rt)
        rng = self.rng = np.random.default_rng(14)
        self.flakes = [np.column_stack([rng.uniform(0, N, n), rng.uniform(0, N, n), rng.uniform(0, 6.28, n)]).astype(np.float32)
                       for n, _, _, _ in LAYERS]
        self.fall, self.wind = 1.0, 0.0
        self.houses = self._village()
        self.depth = np.zeros(N, np.float32)          # snow piled on each column's top surface
        self.windows_on = rng.random(len(self.windows)) < 0.7
        self.smoke = np.zeros((N, N), np.float32)
        self.t = 0.0

    def _village(self):
        """The houses as a skyline mask, their roof line, the windows and the chimneys."""
        rng = self.rng
        sky = np.full(N, GROUND, np.float32)          # the highest solid pixel in each column
        mask = Y >= GROUND
        self.windows, self.chimneys = [], []
        x = -4
        while x < N:
            w = int(rng.integers(14, 24))
            wall = int(rng.integers(12, 20))
            top = GROUND - wall
            roof = int(rng.integers(6, 11))
            for xx in range(max(0, x), min(N, x + w)):
                frac = abs((xx - x) - w / 2) / (w / 2)
                peak = top - roof * (1 - frac)
                mask[int(peak):, xx] = True
                sky[xx] = min(sky[xx], peak)
            for wx in range(x + 3, x + w - 3, 6):
                for wy in range(top + 3, GROUND - 4, 7):
                    if 0 <= wx < N - 2:
                        self.windows.append((wx, wy))
            cx = x + int(w * rng.uniform(0.2, 0.4))
            if 0 <= cx < N - 2:
                ctop = int(top - roof * 0.8)
                mask[ctop:top, cx:cx + 3] = True
                sky[cx:cx + 3] = np.minimum(sky[cx:cx + 3], ctop)
                self.chimneys.append((cx + 1, ctop))
            x += w + int(rng.integers(2, 7))
        self.mask = mask
        return sky

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.fall = max(0.1, min(3.0, self.fall * 1.07 ** d))
        elif k == 1:
            self.wind = max(-20.0, min(20.0, self.wind + d))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.depth[:] = 0
        elif k == 1:
            on = not self.windows_on.any()
            self.windows_on[:] = on
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        gust = self.wind + 6 * math.sin(self.t * 0.13) + 10 * self.sound[0]
        for (n, size, speed, b), f in zip(LAYERS, self.flakes):
            f[:, 1] += speed * self.fall * dt * (1 + 0.5 * self.beat)
            f[:, 0] += (gust * speed / 20 + 4 * size * np.sin(self.t * 1.3 + f[:, 2])) * dt
            f[:, 0] %= N
            if size >= 1.0:                           # near flakes settle where they meet the town
                xi = f[:, 0].astype(int) % N
                landed = f[:, 1] >= self.houses[xi] - self.depth[xi]
                np.add.at(self.depth, xi[landed], 0.06 * size)
                f[landed, 1] = -2
                f[landed, 0] = self.rng.uniform(0, N, landed.sum())
            else:
                f[f[:, 1] > GROUND, 1] -= GROUND + 4
        self.depth = np.minimum(self.depth, 9)
        self.depth = 0.9 * self.depth + 0.05 * (np.roll(self.depth, 1) + np.roll(self.depth, -1))   # it slumps
        if self.rng.random() < dt / 4:                # someone turns a light on, or off
            i = self.rng.integers(len(self.windows))
            self.windows_on[i] = not self.windows_on[i]
        # chimney smoke: puffs added at each chimney, drifting up and downwind, fading
        sm = np.roll(self.smoke, -1, 0) * 0.97
        shift = int(round(gust * dt * 3 + self.rng.normal(0, 0.6)))
        self.smoke = np.roll(sm, shift, 1) * 0.5 + self.smoke * 0.5 * 0.985
        for cx, cy in self.chimneys:
            self.smoke[max(0, cy - 2):cy, max(0, cx - 1):cx + 2] += 0.35

    def render(self):
        tone = (0.05 + 0.07 * np.clip((Y - 20) / 96, 0, 1)).astype(np.float32)           # sky, lighter low down
        mx, my = 100, 22
        d = np.hypot(X - mx, Y - my)
        tone += 0.9 * (d < 7) + 0.18 * np.exp(-d / 16)                                   # the moon, haloed
        tone += np.clip(self.smoke, 0, 0.5) * 0.4
        tone[self.mask] = 0.02                                                           # the houses, dark
        # snow on the roofs and ground: a pale band above each column's surface
        top = self.houses - self.depth
        band = (Y >= top[None, :]) & (Y < self.houses[None, :] + 1.5)
        tone[band] = 0.55
        ground = Y >= GROUND + np.minimum(self.depth, 3)[None, :]
        tone[ground] = np.maximum(tone[ground], 0.62 - 0.003 * (Y[ground] - GROUND))
        for (n, size, speed, b), f in zip(LAYERS, self.flakes):
            xi, yi = f[:, 0].astype(int) % N, f[:, 1].astype(int)
            ok = (yi >= 0) & (yi < N)
            np.maximum.at(tone, (yi[ok], xi[ok]), b)
            if size > 1.2:                                                               # near flakes are 2 px
                ok2 = ok & (yi + 1 < N)
                np.maximum.at(tone, (yi[ok2] + 1, xi[ok2]), b * 0.8)
                np.maximum.at(tone, (yi[ok2], (xi[ok2] + 1) % N), b * 0.8)
        img = self.print(np.clip(tone, 0, 1))
        for (wx, wy), on in zip(self.windows, self.windows_on):    # the windows, in their own warm ink
            if on:
                img[wy:wy + 3, wx:wx + 2] = self.WINDOW_INK
        return img

    def lights(self):
        return [self.glow(0, 0.6, 0.2 + 0.2 * self.fall), self.glow(1, 0.55, 0.2 + 0.03 * abs(self.wind))] + self.ink_lights()
