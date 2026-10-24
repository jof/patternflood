"""Moon: a world turning in the dark, lit through its phases, printed in inks.

Three worlds: a cratered moon, an Earth with drifting clouds, and a banded giant
with rings. The sphere is drawn analytically: every pixel on the disc knows
its normal, which turns into the world's own latitude and longitude for its
surface. The crater rims are bump-mapped, and the rings take the planet's
shadow and cast their own on it. The light circles slowly, so the terminator
sweeps from full to new. It all goes through a dither screen onto a palette of
inks, over a field of twinkling one-pixel stars. After Lee's Poincaré Sphere.
"""
import math

import numpy as np

from .. import ink
from ..draw import N, X, Y
from ..runtime import DETENTS_PER_REV
from .original import Original

# world, its inks and its screen when chosen (k3 and k2 change them after)
WORLDS = [("moon", "silver", "bayer8"), ("earth", "ice", "blue"), ("giant", "ember", "hatch")]
NCRATERS = 46
RING_IN, RING_OUT = 1.3, 2.15


def _pal(name):
    return next(i for i, (n, _) in enumerate(ink.PALETTES) if n == name)


def _rot(spin, tilt, incline):
    """World -> view: turn about the world's axis, lean it towards us, tilt it in the picture."""
    cs, ss = math.cos(spin), math.sin(spin)
    ci, si = math.cos(incline), math.sin(incline)
    ct, st = math.cos(tilt), math.sin(tilt)
    ry = np.array([[cs, 0, ss], [0, 1, 0], [-ss, 0, cs]], np.float32)
    rx = np.array([[1, 0, 0], [0, ci, -si], [0, si, ci]], np.float32)
    rz = np.array([[ct, -st, 0], [st, ct, 0], [0, 0, 1]], np.float32)
    return rz @ rx @ ry


def _noise(q, dirs, freqs, phases):
    """A smooth pattern on the sphere: a few plane waves through it, about -1..1."""
    return np.sin((q @ dirs.T) * freqs + phases).sum(-1) / math.sqrt(len(freqs))


class Moon(Original):
    name = "Moon"
    blurb = "A world in the dark, lit through its phases, dithered into inks (after Lee's Poincaré Sphere). k0 turns it, k1 moves the sun, k2 screen, k3 inks. Click k0 next world, k1 auto phase, k2 chunky."

    def __init__(self, rt):
        super().__init__(rt)
        rng = np.random.default_rng(11)
        c = rng.normal(size=(NCRATERS, 3)).astype(np.float32)
        self.crater = c / np.linalg.norm(c, axis=1, keepdims=True)
        self.crater_r = (0.05 + 0.22 * rng.random(NCRATERS) ** 2.5).astype(np.float32)
        self.crater_d = (0.6 + 0.6 * rng.random(NCRATERS)).astype(np.float32)
        d = rng.normal(size=(7, 3)).astype(np.float32)
        self.wave_dirs = d / np.linalg.norm(d, axis=1, keepdims=True)
        self.wave_f = (np.array([1.3, 1.9, 2.6, 3.7, 5.1, 7.3, 9.8], np.float32))
        self.wave_ph = (rng.random(7) * 6.28).astype(np.float32)
        self.stars = np.column_stack([rng.integers(0, N, 110), rng.integers(0, N, 110),
                                      rng.random(110), rng.random(110) * 6.28]).astype(np.float32)
        self.spin, self.spin_rate = 0.0, 0.12
        self.phase, self.auto_phase = 0.9, True
        self.t_phase = 0.0
        self.world = 0
        self.scale = 1
        self.t = 0.0
        self._choose(0)

    def _choose(self, w):
        self.world = w
        _, pal, scr = WORLDS[w]
        self.pal_i, self.screen_i = _pal(pal), ink.SCREENS.index(scr)
        self._screen()

    def _screen(self):
        self.thresh = ink.screen(ink.SCREENS[self.screen_i], self.scale, angle=0.3, pitch=3.0 * self.scale)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.spin += d * 2 * math.pi / DETENTS_PER_REV
        elif k == 1:
            self.phase += d * 2 * math.pi / 48
            self.auto_phase = False
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
            self._choose((self.world + 1) % len(WORLDS))
        elif k == 1:
            self.auto_phase = not self.auto_phase
        elif k == 2:
            self.scale = 3 - self.scale
            self._screen()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        self.spin += (self.spin_rate + 0.5 * self.sound[0]) * dt
        if self.auto_phase:                 # swings from crescent to full and back, never quite new
            self.t_phase += dt
            self.phase = 1.9 * math.sin(self.t_phase * 2 * math.pi / 50)
        if self.on_phrase or (min(self.rt.t - tt for tt in self.t_touch) > 45
                              and int(self.rt.t / 45) != int((self.rt.t - dt) / 45)):
            self._choose((self.world + 1) % len(WORLDS))

    def render(self):
        world = WORLDS[self.world][0]
        ringed = world == "giant"
        rad = (27.0 if ringed else 45.0) * (1 + 0.04 * self.beat)
        cx, cy = 63.5, 63.5
        sx, sy = (X - cx) / rad, (cy - Y) / rad
        r2 = sx * sx + sy * sy
        m = _rot(self.spin, -0.35 if ringed else 0.25, 0.28 if ringed else 0.15)
        light = np.array([math.sin(self.phase), 0.3, math.cos(self.phase)], np.float32)
        light /= np.linalg.norm(light)
        tone = self._sky()

        disc = r2 < 1
        n = np.stack([sx[disc], sy[disc], np.sqrt(1 - r2[disc])], -1)
        q = n @ m                                           # view -> the world's own frame
        if world == "moon":
            q2 = self._craters(q)
            nv = q2 @ m.T
            alb = 0.82 - 0.32 * np.clip(_noise(q, self.wave_dirs[:4], self.wave_f[:4] * 1.4, self.wave_ph[:4]) * 1.5 - 0.2, 0, 1)
            lit = np.clip(nv @ light, 0, 1) * alb + 0.025
        elif world == "earth":
            lat = q[:, 1]
            hgt = _noise(q, self.wave_dirs, self.wave_f, self.wave_ph)
            land = hgt > -0.05
            alb = np.where(land, 0.55 + 0.3 * np.clip(hgt, 0, 1), 0.24)
            alb = np.where(np.abs(lat) > 0.86, 0.95, alb)
            cq = q @ _rot(self.t * 0.05, 0, 0)               # clouds drift on their own
            cloud = np.clip(_noise(cq * 1.7, self.wave_dirs[2:], self.wave_f[2:], self.wave_ph[2:] + 2) * 1.6 - 0.5, 0, 1)
            alb = alb * (1 - cloud) + 0.95 * cloud
            ndl = n @ light
            refl = 2 * ndl[:, None] * n - light
            glint = np.where(land | (cloud > 0.3), 0, np.clip(refl[:, 2], 0, 1) ** 30)
            lit = np.clip(ndl, 0, 1) * alb + 0.8 * glint + 0.02
            lit += 0.35 * (1 - n[:, 2]) ** 3 * np.clip(ndl + 0.3, 0, 1)        # the atmosphere's rim
        else:
            lat = np.arcsin(np.clip(q[:, 1], -1, 1))
            lon = np.arctan2(q[:, 0], q[:, 2])
            band = np.sin(lat * 9 + 0.7 * np.sin(lat * 23) + 0.35 * np.sin(lon * 2 + lat * 14 + self.t * 0.4))
            alb = 0.55 + 0.3 * band
            spot = ((lon - 1.0) / 0.45) ** 2 + ((lat + 0.35) / 0.17) ** 2
            alb = np.where(spot < 1, 0.95 - 0.25 * spot, alb)
            ndl = n @ light
            lit = np.clip(ndl, 0, 1) * alb + 0.02
            lit *= 1 - 0.85 * self._ring_shadow(n, light, m)
        tone[disc] = lit

        if ringed:
            self._rings(tone, sx, sy, r2, light, m)
        img = ink.dither(tone, ink.PALETTES[self.pal_i][1], self.thresh, self.scale)
        return img

    def _sky(self):
        tone = np.zeros((N, N), np.float32)
        x, y, b, ph = self.stars.T
        tw = b * (0.55 + 0.45 * np.sin(self.rt.t * (1 + 2 * b) + ph)) * (1 + 0.6 * self.sound[3])
        tone[y.astype(int), x.astype(int)] = np.clip(0.25 + 0.75 * tw, 0, 1)
        return tone

    def _craters(self, q):
        """The surface normal (world frame) bent by every crater's bowl and rim."""
        dots = np.clip(q @ self.crater.T, -1, 1)               # (pixels, craters)
        d = np.arccos(dots)
        u = d / self.crater_r
        # height profile h(u): a bowl inside (u^2 - 1), a raised rim out to u = 1.5; its slope:
        slope = np.where(u < 1, 2 * u, np.where(u < 1.5, 0.35 * math.pi / 0.5 * np.cos(math.pi * (u - 1) / 0.5), 0))
        w = slope / self.crater_r * self.crater_d * 0.11 / np.maximum(np.sin(d), 1e-3)
        # the gradient points away from each centre; the normal leans the other way
        bent = q + (w @ self.crater - (w * dots).sum(1, keepdims=True) * q)
        return bent / np.linalg.norm(bent, axis=1, keepdims=True)

    def _ring_band(self, r):
        """Ring opacity by radius (in planet radii): banded, with a dark gap."""
        inside = (r > RING_IN) & (r < RING_OUT)
        dens = 0.55 + 0.3 * np.sin(r * 31) + 0.15 * np.sin(r * 73)
        gap = np.abs(r - 1.78) < 0.05
        return np.where(inside & ~gap, np.clip(dens, 0.1, 1), 0)

    def _ring_shadow(self, n, light, m):
        """How much the rings shade each point on the disc, along its line to the sun."""
        axis = m[:, 1]
        la = float(light @ axis)
        if abs(la) < 1e-3:
            return np.zeros(len(n), np.float32)
        t = -(n @ axis) / la
        p = n + t[:, None] * light
        return np.where(t > 0, self._ring_band(np.linalg.norm(p, axis=1)), 0)

    def _rings(self, tone, sx, sy, r2, light, m):
        axis = m[:, 1]
        if abs(axis[2]) < 0.03:
            return
        z = -(sx * axis[0] + sy * axis[1]) / axis[2]            # where each pixel's sightline meets the ring plane
        r = np.sqrt(sx * sx + sy * sy + z * z)
        opacity = self._ring_band(r)
        front = (r2 >= 1) | (z > np.sqrt(np.clip(1 - r2, 0, 1)))
        show = (opacity > 0) & front
        if not show.any():
            return
        p = np.stack([sx[show], sy[show], z[show]], -1)
        b = p @ light                                           # the planet's shadow across the rings
        c = (p * p).sum(1) - 1
        shadowed = (b * b - c > 0) & (b < 0)
        lit = (0.25 + 0.75 * abs(float(light @ axis))) * np.where(shadowed, 0.08, 1.0)
        tone[show] = tone[show] * (1 - opacity[show]) + opacity[show] * 0.85 * lit

    def lights(self):
        inks = ink.PALETTES[self.pal_i][1]
        return [self.glow(0, self.world / 3), self.glow(1, 0.12, 0.3 + 0.4 * (1 + math.cos(self.phase)) / 2),
                self.glow(2, self.screen_i / len(ink.SCREENS)), tuple(float(c) for c in inks[-1])]
