"""Cumulus: clouds drifting across a low sun, rays fanning through the gaps, dithered.

After Lee's 0517, its slow purple haze. The clouds are fractal noise (four
octaves, each drifting at its own speed, so they billow and change shape as
they go), cut off softly below a cover level. Each point is shaded by how much
cloud lies between it and the sun, sampled a few steps sunward, so the sun's
side of each cloud is bright and the far side dark. Crepuscular rays come
from smearing the light that gets through the gaps outward from the sun (a
radial blur), so beams fan across the sky wherever the clouds part.
"""
import numpy as np

from ..draw import N, X, Y
from .original import Inked

RAY_STEPS = 14


class Cumulus(Inked):
    name = "Cumulus"
    blurb = "Clouds drifting across a low sun, rays fanning through the gaps, dithered (after Lee's 0517). k0 wind, k1 cloud cover, k2 screen, k3 inks. Click k0 time-lapse, k1 move the sun, k2 chunky."
    palette, screen_kind = "dusk", "bayer8"

    def __init__(self, rt):
        super().__init__(rt)
        rng = np.random.default_rng(23)
        self.grid = rng.random((64, 64)).astype(np.float32)
        self.wind, self.cover = 1.0, 0.45
        self.fast = False
        self.sun = np.array([96.0, 38.0], np.float32)
        self.sun_i = 0
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.wind = max(0.0, min(4.0, self.wind + d * 0.1))
        elif k == 1:
            self.cover = max(0.15, min(0.85, self.cover + d * 0.02))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.fast = not self.fast
        elif k == 1:
            self.sun_i = (self.sun_i + 1) % 3
            self.sun = np.array([(96.0, 38.0), (64.0, 24.0), (30.0, 46.0)][self.sun_i], np.float32)
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        self.t += dt * self.wind * (6 if self.fast else 1) * (1 + self.sound[1])

    def _noise(self, u, v):
        g, n = self.grid, self.grid.shape[0]
        x0, y0 = np.floor(u), np.floor(v)
        fx, fy = u - x0, v - y0
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        x0, y0 = x0.astype(int) % n, y0.astype(int) % n
        x1, y1 = (x0 + 1) % n, (y0 + 1) % n
        return (g[y0, x0] * (1 - fx) + g[y0, x1] * fx) * (1 - fy) + (g[y1, x0] * (1 - fx) + g[y1, x1] * fx) * fy

    def density(self, x, y):
        t = self.t
        f = np.zeros_like(x)
        amp, s = 0.5, 0.022
        for o in range(4):                  # each octave drifts at its own speed: billowing
            f += amp * self._noise(x * s - t * (0.2 + 0.1 * o) + o * 9.1, y * s * 1.7 + t * 0.03 * o + o * 4.7)
            amp, s = amp * 0.5, s * 2
        f /= 0.9375
        # clouds thin out towards the horizon, where we look through more sky
        return np.clip((f - (1 - self.cover) + 0.15 * (1 - y / 100)) / 0.08, 0, 1)

    def render(self):
        sx, sy = float(self.sun[0]), float(self.sun[1])
        # cloud and its self-shadow on a half-size grid (clouds are soft; this is a quarter the work)
        h = N // 2
        gy, gx = np.mgrid[0:h, 0:h].astype(np.float32) * 2 + 0.5
        d = self.density(gx, gy)
        dx, dy = sx - gx, sy - gy
        dist = np.hypot(dx, dy) + 1e-3
        ux, uy = dx / dist, dy / dist
        shadow = np.zeros_like(d)
        for k in (2, 4, 7):                 # cloud lying sunward of each point shades it
            px = np.clip(((gx + ux * k * 2) / 2).astype(int), 0, h - 1)
            py = np.clip(((gy + uy * k * 2) / 2).astype(int), 0, h - 1)
            shadow += d[py, px]
        shadow /= 3
        lit = 0.32 + 0.66 * (1 - shadow) * (0.55 + 0.45 * np.exp(-dist / 70))
        d = d.repeat(2, 0).repeat(2, 1)
        lit = lit.repeat(2, 0).repeat(2, 1)
        dist = np.hypot(sx - X, sy - Y)
        sky = 0.18 + 0.32 * np.clip(Y / 128, 0, 1) ** 1.5 + 0.45 * np.exp(-dist / 22)
        sun_disc = np.where(dist < 6, 1.0, 0.0)
        # light through the gaps, smeared outward from the sun: crepuscular rays
        through = (sun_disc + 0.5 * np.exp(-dist / 30)) * (1 - d)
        rays = np.zeros_like(through)
        for k in range(RAY_STEPS):
            f = 1 - k / RAY_STEPS * 0.85
            px = np.clip(sx + (X - sx) * f, 0, N - 1).astype(int)
            py = np.clip(sy + (Y - sy) * f, 0, N - 1).astype(int)
            rays += through[py, px]
        rays /= RAY_STEPS
        rim = d * (1 - d) * 4 * np.exp(-dist / 35) * 0.6            # silver linings near the sun
        tone = sky * (1 - d) + d * lit + rim + 0.4 * rays * (1 - d * 0.7) + sun_disc * (1 - d)
        return self.print(np.clip(tone * (1 + 0.15 * self.beat), 0, 1))

    def lights(self):
        return [self.glow(0, 0.55, 0.2 + 0.15 * self.wind), self.glow(1, 0.6, 0.2 + 0.5 * self.cover)] + self.ink_lights()
