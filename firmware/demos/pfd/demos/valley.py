"""Valley: low flight over mountains at dawn, dithered.

After Lee's 0624, the isometric landscape. The land is a ridged fractal
heightmap that tiles, so the flight never ends. It's drawn the way Comanche
drew it: each screen column is a ray across the map, sampled from near to far,
and each row shows the nearest sample that rises to it. The land is shaded by
the sun (slopes facing it lit, valleys holding shadow), lakes fill the
hollows and mirror the sky, and distance fades into haze. The plane banks
into its turns and holds its height above the ground.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

M = 256                                 # heightmap size (it tiles)
TEX = 0.25                              # heightmap texels per unit of distance
NZ = 150
ZS = np.geomspace(0.5, 420, NZ).astype(np.float32)[:, None]
COLS = ((np.arange(N, dtype=np.float32) - 63.5) / 64)[None, :]
ROWS = np.arange(N, dtype=np.float32)[None, :, None]
FOCAL = 70.0
HORIZON = 44.0
WATER = 0.22
HSCALE = 110.0                          # heightmap 0..1 -> units of distance
SUNS = [("dawn", 0.12, -0.7), ("night", 0.3, 0.6), ("dusk", 0.06, 2.4)]     # name, elevation, azimuth (night: the moon)


def _terrain(seed):
    """A tiling ridged-fractal heightmap, 0..1."""
    rng = np.random.default_rng(seed)
    f = np.fft.fftfreq(M)[:, None] ** 2 + np.fft.fftfreq(M)[None, :] ** 2
    spec = (rng.normal(size=(M, M)) + 1j * rng.normal(size=(M, M))) / np.maximum(f, 1 / M ** 2) ** 1.05
    spec[0, 0] = 0
    h = np.real(np.fft.ifft2(spec))
    h = (h - h.mean()) / h.std()
    ridged = 1 - np.abs(np.tanh(h * 0.9))           # sharp crests where the field crosses zero
    smooth = 0.5 + 0.5 * np.tanh(h * 0.6)
    h = 0.55 * ridged ** 1.5 + 0.45 * smooth
    return ((h - h.min()) / (h.max() - h.min())).astype(np.float32)


class Valley(Inked):
    name = "Valley"
    blurb = "Low flight over mountains at dawn, dusk or night, dithered (after Lee's 0624). k0 steers, k1 altitude, k2 screen, k3 inks. Click k0 autopilot, k1 time of day, k2 chunky, k3 new land."
    palette, screen_kind = "dusk", "bayer8"

    def __init__(self, rt):
        super().__init__(rt)
        self.seed = 3
        self.sun_i = 0
        self._land()
        self.x, self.y = 0.0, 0.0
        self.heading, self.turn_rate = 0.0, 0.0
        self.alt = 0.35
        self.cam_h = None
        self.auto = True
        self.t = 0.0
        rng = np.random.default_rng(2)
        self.stars = np.column_stack([rng.uniform(-math.pi, math.pi, 260), rng.uniform(0.02, 0.75, 260),
                                      rng.uniform(0.3, 1.0, 260)]).astype(np.float32)

    def _land(self):
        self.h = _terrain(self.seed)
        self._shade()

    def _shade(self):
        """Sun shading for the whole map: slope towards the sun, and a little ambient light."""
        _, el, az = SUNS[self.sun_i]
        gx = (np.roll(self.h, -1, 1) - np.roll(self.h, 1, 1)) * 40
        gy = (np.roll(self.h, -1, 0) - np.roll(self.h, 1, 0)) * 40
        n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        sun = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)], np.float32)
        lit = np.clip(n @ sun, 0, 1)
        snow = np.clip((self.h - 0.78) * 8, 0, 1)
        dim = 0.6 if SUNS[self.sun_i][0] == "night" else 1.0
        self.shade = (dim * (0.08 + (0.55 + 0.4 * snow) * lit) + 0.08 * self.h).astype(np.float32)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.turn_rate = max(-0.8, min(0.8, self.turn_rate + d * 0.05))
            self.auto = False
        elif k == 1:
            self.alt = max(0.12, min(1.0, self.alt + d * 0.02))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.auto = not self.auto
        elif k == 1:
            self.sun_i = (self.sun_i + 1) % len(SUNS)
            self._shade()
        elif k == 2:
            self.chunky()
        elif k == 3:
            self.seed += 1
            self._land()

    def ground(self, x, y):
        return float(_bilinear(self.h, np.float32(x * TEX), np.float32(y * TEX)))

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        if self.auto:                   # gentle wandering turns, steering away from the high ground ahead
            look = [self.ground(self.x + 40 * math.cos(self.heading + a), self.y + 40 * math.sin(self.heading + a))
                    for a in (-0.5, 0.5)]
            want = 0.25 * math.sin(self.t * 0.07) + 2.0 * (look[0] - look[1])
            self.turn_rate += (max(-0.5, min(0.5, want)) - self.turn_rate) * (1 - math.exp(-dt / 1.5))
        self.heading += self.turn_rate * dt
        speed = 30 * (1 + 0.8 * self.sound[2])
        self.x += math.cos(self.heading) * speed * dt
        self.y += math.sin(self.heading) * speed * dt
        # hold height above the highest ground just ahead, smoothly
        ahead = max(self.ground(self.x + d * math.cos(self.heading), self.y + d * math.sin(self.heading))
                    for d in (0, 15, 30, 45))
        want = max(ahead, WATER) * HSCALE + 8 + self.alt * 60
        self.cam_h = want if self.cam_h is None else self.cam_h + (want - self.cam_h) * (1 - math.exp(-dt / 1.2))
        if self.on_phrase:
            self.sun_i = (self.sun_i + 1) % len(SUNS)
            self._shade()

    def sky(self, rows, cols):
        name, el, az = SUNS[self.sun_i]
        up = (HORIZON - rows) / FOCAL
        night = name == "night"
        glow = 0.25 if night else (0.55 if name == "dawn" else 0.6)
        tone = (0.06 if night else 0.12) + glow * np.exp(-np.maximum(up, 0) * 5)
        # the sun, where its bearing falls on screen
        rel = (az - self.heading + math.pi) % (2 * math.pi) - math.pi
        sx = 63.5 + math.tan(max(-1.3, min(1.3, rel))) * 64 if abs(rel) < 1.2 else -100
        sy = HORIZON - math.tan(el) * FOCAL
        d = np.hypot(cols - sx, rows - sy)
        return tone + np.where(d < (3 if night else 5), 1.0, 0.0) + (0.2 if night else 0.45) * np.exp(-d / 14)

    def render(self):
        bank = -self.turn_rate * 0.35
        ch, sh = math.cos(self.heading), math.sin(self.heading)
        z = ZS * np.ones_like(COLS)
        side = COLS * z
        wx = self.x + ch * z - sh * side
        wy = self.y + sh * z + ch * side
        tx, ty = wx * TEX, wy * TEX
        hraw = _bilinear(self.h, tx, ty)
        h = np.maximum(hraw, WATER)
        ys = HORIZON + (self.cam_h - h * HSCALE) / z * FOCAL + bank * COLS * 64
        reach = np.minimum.accumulate(ys, axis=0)
        idx = (reach[:, None, :] > ROWS).sum(0)
        land = _bilinear(self.shade, tx, ty)
        water = hraw < WATER
        sky_ref = self.sky(np.full_like(z, HORIZON + 6.0), np.broadcast_to(np.arange(N, dtype=np.float32), z.shape))
        shimmer = 0.75 + 0.25 * np.sin((wx * sh - wy * ch) * 0.05 + (wx * ch + wy * sh) * 0.6 + self.t * 2)
        land = np.where(water, 0.06 + 0.6 * sky_ref * shimmer, land)
        haze = np.clip(z / 420, 0, 1) ** 1.2
        land = land * (1 - haze) + haze * self.sky(np.full_like(z, HORIZON), np.broadcast_to(np.arange(N, dtype=np.float32), z.shape)) * 0.8
        sky = self.sky(Y - bank * (X - 63.5), X)
        if SUNS[self.sun_i][0] == "night":           # stars, fixed in the world, wheeling past as we turn
            az, el, b = self.stars.T
            rel = (az - self.heading + math.pi) % (2 * math.pi) - math.pi
            on = np.abs(rel) < 1.0
            sx = (63.5 + np.tan(rel[on]) * 64).astype(int)
            sy = (HORIZON - np.tan(el[on]) * FOCAL + bank * (sx - 63.5)).astype(int)
            ok = (sx >= 0) & (sx < N) & (sy >= 0) & (sy < N)
            sky[sy[ok], sx[ok]] += b[on][ok] * (0.6 + 0.4 * np.sin(self.t * 3 + b[on][ok] * 40))
        cols = np.broadcast_to(np.arange(N), idx.shape)
        tone = np.where(idx < NZ, land[np.minimum(idx, NZ - 1), cols], sky)
        return self.print(np.clip(tone * (1 + 0.2 * self.beat), 0, 1))

    def lights(self):
        return [self.glow(0, 0.3 if self.auto else 0.08), self.glow(1, 0.6, 0.2 + 0.5 * self.alt)] + self.ink_lights()


def _bilinear(a, x, y):
    """a (M, M), tiled, sampled at float texel coordinates (x, y)."""
    x0, y0 = np.floor(x), np.floor(y)
    fx, fy = x - x0, y - y0
    x0, y0 = x0.astype(np.int64) % M, y0.astype(np.int64) % M
    x1, y1 = (x0 + 1) % M, (y0 + 1) % M
    return (a[y0, x0] * (1 - fx) + a[y0, x1] * fx) * (1 - fy) + (a[y1, x0] * (1 - fx) + a[y1, x1] * fx) * fy
