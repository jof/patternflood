"""Sea: open water at night, a moon's glitter path across it, dithered.

After SeungHun's Midsummer Sea. The water is eight deep-water waves (each travels
at the speed its length gives it, so long swells outrun the chop), seen from a
boat that rides them. Each screen column is raycast: the sea is sampled at
depths from the bow to the horizon, and every row shows the nearest sample
that reaches up to it, so crests hide the troughs behind them. Each sample
reflects the sky by Fresnel's law, and the moon's sharp reflection breaks into
a path of glitter that follows the waves. All of it goes through a dither
screen onto the inks.
"""
import math

import numpy as np

from .. import ink
from ..draw import N, X, Y
from .original import Original

NWAVES = 8
NZ = 128
HORIZON = 46.0
FOCAL = 64.0
EYE_H = 1.5
ZS = np.geomspace(0.6, 90, NZ).astype(np.float32)[:, None]           # depth of each sample row
COLS = ((np.arange(N, dtype=np.float32) - 63.5) / 64)[None, :]
ROWS = np.arange(N, dtype=np.float32)[None, :, None]
G = 9.8


def _pal(name):
    return next(i for i, (n, _) in enumerate(ink.PALETTES) if n == name)


class Sea(Original):
    name = "Sea"
    blurb = "Open water at night, the moon's glitter on it, dithered (after SeungHun's Midsummer Sea). k0 swell, k1 moves the moon, k2 screen, k3 inks. Click k0 storm, k1 sunset, k2 chunky."

    def __init__(self, rt):
        super().__init__(rt)
        rng = np.random.default_rng(8)
        ang = rng.normal(0, 0.55, NWAVES)                       # mostly rolling towards us, from ahead
        lam = np.geomspace(14, 1.2, NWAVES) * rng.uniform(0.85, 1.15, NWAVES)
        k = 2 * math.pi / lam
        self.kx = (np.sin(ang) * k).astype(np.float32)
        self.kz = (-np.cos(ang) * k).astype(np.float32)
        self.omega = np.sqrt(G * k).astype(np.float32)
        self.amp0 = (0.18 * lam ** 0.8 / 6).astype(np.float32)   # steepness falls off for the long ones
        self.phase = rng.uniform(0, 2 * math.pi, NWAVES).astype(np.float32)
        self.stars = np.column_stack([rng.integers(0, N, 70), rng.integers(0, int(HORIZON) - 4, 70),
                                      rng.random(70)]).astype(np.float32)
        self.swell, self.storm = 1.0, False
        self.moon_az = 0.15
        self.sunset = False
        self.t = 0.0
        self.travel = 0.0
        self.flash = 0.0
        self.scale = 1
        self._mode()

    def _mode(self):
        self.pal_i = _pal("ember" if self.sunset else "ice")
        self.screen_i = ink.SCREENS.index("bayer8")
        self._screen()

    def _screen(self):
        self.thresh = ink.screen(ink.SCREENS[self.screen_i], self.scale, angle=0.2, pitch=3.0 * self.scale)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.swell = max(0.1, min(3.0, self.swell * 1.07 ** d))
        elif k == 1:
            self.moon_az = max(-0.7, min(0.7, self.moon_az + d * 0.03))
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
            self.storm = not self.storm
        elif k == 1:
            self.sunset = not self.sunset
            self._mode()
        elif k == 2:
            self.scale = 3 - self.scale
            self._screen()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        self.travel += dt * 1.2
        if self.rt.t - self.t_touch[1] > 30:                      # left alone, the moon wanders
            self.moon_az = 0.45 * math.sin(self.rt.t * 0.02)
        self.flash *= math.exp(-dt / 0.12)
        if self.on_phrase or (self.storm and np.random.random() < dt / 6):
            self.flash = 1.0

    def waves(self, x, z):
        """Height and slopes (d/dx, d/dz) of the sea at world points (x, z)."""
        amp = self.amp0 * self.swell * (2.2 if self.storm else 1.0) * (1 + 0.8 * self.sound[2])
        arg = x[..., None] * self.kx + (z[..., None] + self.travel) * self.kz - self.omega * self.t + self.phase
        s, c = np.sin(arg), np.cos(arg)
        return (s @ amp), (c @ (amp * self.kx)), (c @ (amp * self.kz))

    def sky(self, elev, az):
        """Sky tone along directions (elevation, azimuth), moon included."""
        low = np.exp(-np.maximum(elev, 0) * (5 if self.sunset else 9))
        tone = (0.42 if self.sunset else 0.2) * low + 0.03 + 0.5 * self.flash * np.clip(elev + 0.2, 0, 1)
        mel = self.moon_el()
        d2 = (elev - mel) ** 2 + (az - self.moon_az) ** 2
        tone = tone + 0.6 * np.exp(-d2 / 0.03) * (1.0 if self.sunset else 0.5)       # halo
        return tone + np.where(d2 < (0.05 if self.sunset else 0.035) ** 2, 1.0, 0.0)  # the disc

    def moon_el(self):
        return 0.09 if self.sunset else 0.2

    def glitter(self, elev, az):
        """The moon's (or sun's) reflection off a facet, spread wide: water is never a mirror."""
        d2 = (elev - self.moon_el()) ** 2 + (az - self.moon_az) ** 2
        return np.exp(-d2 / 0.1 ** 2)

    def render(self):
        # the boat rides the swell
        h0, _, _ = self.waves(np.zeros(1, np.float32), np.full(1, 2.0, np.float32))
        eye = EYE_H + 0.6 * float(h0[0])
        roll = 0.04 * math.sin(self.t * 0.7) * self.swell
        z = ZS * np.ones_like(COLS)
        x = COLS * z
        h, hx, hz = self.waves(x, z)
        # ripples too small to see but not to catch the moon: they only tilt the normals
        rip = 0.22 * (1 + self.sound[3]) * (1.6 if self.storm else 1)
        hx = hx + rip * np.sin(x * 23.1 + z * 7.3 - self.t * 4.1) * np.sin(x * 5.7 - z * 17.9 + self.t * 2.3)
        hz = hz + rip * np.sin(x * 13.3 - z * 21.7 + self.t * 3.7) * np.sin(x * 19.1 + z * 3.1 - self.t * 1.9)
        horizon = HORIZON + 6 * math.sin(self.t * 0.5) * min(1.0, self.swell) * (1.6 if self.storm else 1)
        ys = horizon + (eye - h) / z * FOCAL + roll * (COLS * 64)
        # the nearest sample that reaches each row: running minimum of the projected heights
        reach = np.minimum.accumulate(ys, axis=0)
        idx = (reach[:, None, :] > ROWS).sum(0)                     # (rows, cols): samples that fall short
        # shade each sample: Fresnel mix of the reflected sky and the dark water beneath
        nrm = np.stack([-hx, np.ones_like(h), -hz], -1)
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        v = np.stack([x, h - eye, z], -1)
        v /= np.linalg.norm(v, axis=-1, keepdims=True)
        vn = (v * nrm).sum(-1, keepdims=True)
        r = v - 2 * vn * nrm
        fres = 0.03 + 0.97 * (1 - np.abs(vn[..., 0])) ** 5
        elev = np.arcsin(np.clip(r[..., 1], -1, 1))
        az = np.arctan2(r[..., 0], r[..., 2])
        sea = fres * self.sky(elev, az) + (1 - fres) * 0.025
        sea = sea + 2.0 * self.glitter(elev, az) * (0.25 + fres) * (1 + 1.2 * self.beat)
        fog = np.clip((z - 25) / 65, 0, 1)
        sea = sea * (1 - fog) + fog * self.sky(np.zeros_like(z), COLS) * 0.9
        # the sky behind
        sky = self.sky((horizon - Y) / FOCAL, (X - 63.5) / 64)
        sx, sy, sb = self.stars.T
        stars = np.zeros((N, N), np.float32)
        stars[sy.astype(int), sx.astype(int)] = sb * (0.6 + 0.4 * np.sin(self.rt.t * 2 + sb * 20)) * (0 if self.sunset else 1)
        sky = sky + stars * (Y < horizon - 2)
        cols = np.broadcast_to(np.arange(N), idx.shape)
        tone = np.where(idx < NZ, sea[np.minimum(idx, NZ - 1), cols], sky)
        return ink.dither(tone, ink.PALETTES[self.pal_i][1], self.thresh, self.scale)

    def lights(self):
        inks = ink.PALETTES[self.pal_i][1]
        return [self.glow(0, 0.55, 0.2 + 0.2 * self.swell), self.glow(1, 0.15),
                self.glow(2, self.screen_i / len(ink.SCREENS)), tuple(float(c) for c in inks[-1])]
