"""Moon: a world turning in the dark, lit through its phases, printed in inks.

Eight worlds: a cratered moon; an Earth with drifting clouds and its cities lit
on the night side; Mars, with its ice caps, Olympus Mons and the Tharsis
volcanoes, and the long rift of Valles Marineris; a banded giant with rings;
Europa, its ice scored with cracks; a molten world whose crust splits into
glowing seams; a tipped-over ice giant with thin rings and a little moon that
throws its shadow across it; and Pluto, with its heart and its blue haze.

The sphere is drawn analytically: every pixel on the disc knows its normal,
which turns into the world's own latitude and longitude for its surface. Craters,
volcanoes and rifts bend the normals; rings take the planet's shadow and cast
their own on it. It all goes through a dither screen onto a palette of inks,
over a field of twinkling one-pixel stars. After SeungHun's Poincaré Sphere.

Two ways to watch (k1's click). Drift: the world spins by itself and its axis
slowly precesses; k1 sets how fast, through zero and into reverse. Hold: the
world stops, fixed to you, and k1 carries you round it instead. The sun and the
stars stay fixed to the world, so going round brings the night side into view
and wheels the sky past. Back in Drift, the view eases home.
"""
import math

import numpy as np

from .. import ink
from ..draw import N, X, Y
from .original import Original

# name, inks, screen, radius in pixels, tilt in the picture, lean towards us
WORLDS = [
    ("moon", "silver", "bayer8", 45, 0.25, 0.15),
    ("earth", "ice", "blue", 45, 0.25, 0.25),
    ("mars", "dusk", "dots", 43, 0.2, 0.2),
    ("giant", "ember", "hatch", 27, -0.35, 0.28),
    ("europa", "koi", "bayer4", 44, 0.1, 0.1),
    ("lava", "ember", "blue", 44, 0.3, 0.2),
    ("ice giant", "pool", "bayer8", 25, 0.45, 1.15),
    ("pluto", "obra", "blue", 40, -0.2, 0.3),
]
RING_IN, RING_OUT = 1.3, 2.15
# the ice giant's rings: (radius, width, opacity), narrow, the outermost the broadest
THIN_RINGS = [(1.6, 0.035, 0.6), (1.67, 0.03, 0.5), (1.74, 0.035, 0.65), (1.8, 0.03, 0.5), (1.93, 0.08, 0.95)]
MOONLET_ORBIT, MOONLET_R = 2.45, 0.14
HOLD_AXIS = np.array([math.sin(0.5), math.cos(0.5), 0.0])     # Hold turns you round this (view frame)
PRECESS = 0.3, 0.2              # the axis's precession: its rate against the spin, and its cone (radians)
STAR_F = 110.0                  # the sky's focal length in pixels: about 60 degrees across


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


# quaternions (w, x, y, z), for the view offset that Hold builds up and Drift lets go of
def _q_axis(axis, angle):
    return np.concatenate([[math.cos(angle / 2)], np.asarray(axis, float) * math.sin(angle / 2)])


def _q_mul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2])


def _q_pow(q, f):
    """The same turn, scaled by f (f < 1 eases it towards none)."""
    q = q if q[0] >= 0 else -q
    s = float(np.linalg.norm(q[1:]))
    if s < 1e-9:
        return np.array([1.0, 0, 0, 0])
    return _q_axis(q[1:] / s, 2 * math.atan2(s, q[0]) * f)


def _q_mat(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]], np.float32)


def _unit(v):
    v = np.asarray(v, np.float32)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _at(lon, lat):
    """A point on the world (world frame) by longitude and latitude."""
    return np.array([math.sin(lon) * math.cos(lat), math.sin(lat), math.cos(lon) * math.cos(lat)], np.float32)


def _noise(q, dirs, freqs, phases):
    """A smooth pattern on the sphere: a few plane waves through it, about -1..1."""
    return np.sin((q @ dirs.T) * freqs + phases).sum(-1) / math.sqrt(len(freqs))


def _radial_grad(q, centres, dh):
    """The surface gradient of heights that hang on each centre by angular distance: dh(d) is dh/dd,
    (pixels, centres). The normal is q minus this."""
    dots = np.clip(q @ centres.T, -1, 1)
    d = np.arccos(dots)
    w = dh(d) / np.maximum(np.sin(d), 1e-3)
    return -(w @ centres - (w * dots).sum(1, keepdims=True) * q)


def _bend(q, grad):
    return _unit(q - grad)


class Moon(Original):
    name = "Moon"
    blurb = ("Eight worlds in the dark, lit through their phases, dithered into inks (after SeungHun's "
             "Poincaré Sphere). k0 moves the sun; k1 spin speed (Drift) or carries you round the world "
             "(Hold); k2 screen; k3 inks. Click k0 next world, k1 Drift/Hold, k2 chunky.")

    def __init__(self, rt):
        super().__init__(rt)
        rng = np.random.default_rng(11)
        c = rng.normal(size=(46, 3)).astype(np.float32)
        self.crater = _unit(c)
        self.crater_r = (0.05 + 0.22 * rng.random(46) ** 2.5).astype(np.float32)
        self.crater_d = (0.6 + 0.6 * rng.random(46)).astype(np.float32)
        d = rng.normal(size=(7, 3)).astype(np.float32)
        self.wave_dirs = _unit(d)
        self.wave_f = (np.array([1.3, 1.9, 2.6, 3.7, 5.1, 7.3, 9.8], np.float32))
        self.wave_ph = (rng.random(7) * 6.28).astype(np.float32)
        self._worlds_setup(np.random.default_rng(23))
        # stars on the celestial sphere, fixed to the world's frame, so Hold wheels them past
        s = _unit(rng.normal(size=(1400, 3)))
        self.stars = s
        self.star_b = (rng.random(1400) ** 1.8).astype(np.float32)
        self.star_ph = (rng.random(1400) * 6.28).astype(np.float32)

        self.spin, self.precess = 0.0, 0.0
        self.rate, self.spin_v = 0.12, 0.12          # the spin Drift asks for, and the one it has
        self.hold = False
        self.view = np.array([1.0, 0, 0, 0])         # quaternion: where Hold has carried you
        self.look_due = 0.0                          # k1's turns in Hold, not yet eased in
        self.phase, self.auto_phase = 0.9, True
        self.t_phase = 0.0
        self.moonlet = 0.0
        self.world = 0
        self.scale = 1
        self.t = 0.0
        self._choose(0)

    def _worlds_setup(self, rng):
        # Mars: smaller, shallower craters than the moon's
        self.mars_crater = _unit(rng.normal(size=(30, 3)))
        self.mars_crater_r = (0.04 + 0.12 * rng.random(30) ** 2.5).astype(np.float32)
        # Olympus Mons and the three Tharsis volcanoes in a line beside it: (centre, spread, height)
        self.volcanoes = np.stack([_at(-1.0, 0.32), _at(-0.62, 0.0), _at(-0.52, 0.16), _at(-0.42, 0.32)])
        self.volcano_s = np.array([0.2, 0.09, 0.09, 0.09], np.float32)
        self.volcano_h = np.array([0.09, 0.04, 0.04, 0.04], np.float32)
        # Valles Marineris: along the great circle at right angles to g, either side of p
        p = _at(-0.1, -0.12)
        east = _unit(np.cross([0, 1, 0], p))
        self.rift_p, self.rift_g = p, _unit(np.cross(p, east) + 0.25 * east)
        # Europa: cracks along great circles, each one an arc
        g = _unit(rng.normal(size=(26, 3)))
        a = _unit(np.cross(g, rng.normal(size=(26, 3))))
        self.lin_g, self.lin_p = g, a
        self.lin_cos = np.cos(0.4 + 1.1 * rng.random(26)).astype(np.float32)
        self.lin_w = (0.01 + 0.025 * rng.random(26) ** 2).astype(np.float32)
        # the molten world: plates, and a few lava lakes
        self.plates = _unit(rng.normal(size=(60, 3)))
        self.lakes = _unit(rng.normal(size=(7, 3)))
        self.lake_r = (0.06 + 0.07 * rng.random(7)).astype(np.float32)
        # Pluto: its heart and the dark belt beside it
        self.heart_c = _at(0.25, 0.22)
        e = _unit(np.cross([0, 1, 0], self.heart_c))
        self.heart_e, self.heart_n = e, np.cross(self.heart_c, e)
        self.pluto_crater = self.mars_crater[:12]
        self.pluto_crater_r = self.mars_crater_r[:12] * 1.5

    def _choose(self, w):
        self.world = w
        _, pal, scr = WORLDS[w][:3]
        self.pal_i, self.screen_i = _pal(pal), ink.SCREENS.index(scr)
        self.auto_phase = True
        self._screen()

    def _screen(self):
        self.thresh = ink.screen(ink.SCREENS[self.screen_i], self.scale, angle=0.3, pitch=3.0 * self.scale)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.phase += d * 2 * math.pi / 48
            self.auto_phase = False
        elif k == 1:
            if self.hold:
                self.look_due += d * 2 * math.pi / 48
            else:                           # finer near standing still, coarser when it's flying round
                self.rate = max(-2.0, min(2.0, self.rate + d * (0.015 + 0.08 * abs(self.rate))))
                if abs(self.rate) < 0.008:
                    self.rate = 0.0
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
            self.hold = not self.hold
            self.look_due = 0.0
        elif k == 2:
            self.scale = 3 - self.scale
            self._screen()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        want = 0.0 if self.hold else self.rate + 0.5 * self.sound[0]
        self.spin_v += (want - self.spin_v) * (1 - math.exp(-dt / 0.5))
        self.spin += self.spin_v * dt
        self.precess += PRECESS[0] * self.spin_v * dt
        self.moonlet += 0.3 * dt
        if self.hold:
            a = self.look_due * (1 - math.exp(-dt / 0.15))
            self.look_due -= a
            self.view = _q_mul(_q_axis(HOLD_AXIS, a), self.view)
        else:
            self.view = _q_pow(self.view, math.exp(-dt / 1.5))
            if self.auto_phase:             # swings from crescent to full and back, never quite new
                self.t_phase += dt
                self.phase = 1.9 * math.sin(self.t_phase * 2 * math.pi / 50)
        if self.on_phrase or (min(self.rt.t - tt for tt in self.t_touch) > 45
                              and int(self.rt.t / 45) != int((self.rt.t - dt) / 45)):
            self._choose((self.world + 1) % len(WORLDS))

    def render(self):
        world, _, _, rad, tilt, incline = WORLDS[self.world]
        rad = rad * (1 + 0.04 * self.beat)
        cx, cy = 63.5, 63.5
        sx, sy = (X - cx) / rad, (cy - Y) / rad
        r2 = sx * sx + sy * sy
        o = _q_mat(self.view)
        tilt += PRECESS[1] * math.cos(self.precess)
        incline += PRECESS[1] * math.sin(self.precess)
        frame = o @ _rot(0.0, tilt, incline)            # the world's axis, before its spin
        m = frame @ _rot(self.spin, 0, 0)
        light = o @ _unit([math.sin(self.phase), 0.3, math.cos(self.phase)])
        tone = self._sky(o)

        disc = r2 < 1
        n = np.stack([sx[disc], sy[disc], np.sqrt(1 - r2[disc])], -1)
        q = n @ m                                       # view -> the world's own frame
        lit = getattr(self, "_" + world.replace(" ", "_"))(n, q, light, m)
        if world in ("giant", "ice giant"):
            band = self._ring_band if world == "giant" else self._thin_rings
            lit *= 1 - 0.85 * self._ring_shadow(n, light, m, band)
        moonlet = None
        if world == "ice giant":
            moonlet = frame @ (MOONLET_ORBIT * np.array([math.cos(self.moonlet), 0, math.sin(self.moonlet)], np.float32))
            lit *= 1 - 0.9 * self._moonlet_shadow(n, light, moonlet)
        tone[disc] = lit

        if world in ("earth", "pluto"):
            self._haze(tone, sx, sy, r2, light, 0.03 if world == "earth" else 0.05)
        if moonlet is not None and moonlet[2] < 0:
            self._draw_moonlet(tone, sx, sy, r2, light, moonlet)
        if world == "giant":
            self._rings(tone, sx, sy, r2, light, m, self._ring_band)
        elif world == "ice giant":
            self._rings(tone, sx, sy, r2, light, m, self._thin_rings)
        if moonlet is not None and moonlet[2] >= 0:
            self._draw_moonlet(tone, sx, sy, r2, light, moonlet)
        return ink.dither(tone, ink.PALETTES[self.pal_i][1], self.thresh, self.scale)

    # the sky
    def _sky(self, o):
        tone = np.zeros((N, N), np.float32)
        v = self.stars @ o.T
        ahead = v[:, 2] < -0.3                          # behind the world, from where we look
        v = v[ahead]
        px = (63.5 + STAR_F * v[:, 0] / -v[:, 2]).astype(int)
        py = (63.5 - STAR_F * v[:, 1] / -v[:, 2]).astype(int)
        b, ph = self.star_b[ahead], self.star_ph[ahead]
        tw = b * (0.55 + 0.45 * np.sin(self.rt.t * (1 + 2 * b) + ph)) * (1 + 0.6 * self.sound[3])
        on = (px >= 0) & (px < N) & (py >= 0) & (py < N) & (b > 0.08)
        tone[py[on], px[on]] = np.clip(0.2 + 0.8 * tw[on], 0, 1)
        return tone

    # the worlds: each takes the disc's normals (view frame) and points (world frame) and gives its tone
    def _moon(self, n, q, light, m):
        q2 = self._craters(q)
        nv = q2 @ m.T
        alb = 0.82 - 0.32 * np.clip(_noise(q, self.wave_dirs[:4], self.wave_f[:4] * 1.4, self.wave_ph[:4]) * 1.5 - 0.2, 0, 1)
        return np.clip(nv @ light, 0, 1) * alb + 0.025

    def _earth(self, n, q, light, m):
        lat = q[:, 1]
        hgt = _noise(q, self.wave_dirs, self.wave_f, self.wave_ph)
        land = hgt > -0.05
        alb = np.where(land, 0.55 + 0.3 * np.clip(hgt, 0, 1), 0.24)
        ice = np.abs(lat) > 0.86
        alb = np.where(ice, 0.95, alb)
        cq = q @ _rot(self.t * 0.05, 0, 0)              # clouds drift on their own
        cloud = np.clip(_noise(cq * 1.7, self.wave_dirs[2:], self.wave_f[2:], self.wave_ph[2:] + 2) * 1.6 - 0.5, 0, 1)
        alb = alb * (1 - cloud) + 0.95 * cloud
        ndl = n @ light
        refl = 2 * ndl[:, None] * n - light
        glint = np.where(land | (cloud > 0.3), 0, np.clip(refl[:, 2], 0, 1) ** 30)
        lit = np.clip(ndl, 0, 1) * alb + 0.8 * glint + 0.02
        lit += 0.35 * (1 - n[:, 2]) ** 3 * np.clip(ndl + 0.3, 0, 1)        # the atmosphere's rim
        # cities: near the coasts, out where it's night, dimmed by cloud
        towns = _noise(q, self.wave_dirs, self.wave_f * 7.1, self.wave_ph * 3.1)
        coast = np.clip(1 - (hgt + 0.05) / 0.35, 0, 1)
        city = land & ~ice & (towns > 1.15 - 0.45 * coast)
        night = np.clip(-ndl * 5, 0, 1)
        lit += np.where(city, 0.55 * night * (1 - cloud), 0)
        return lit

    def _mars(self, n, q, light, m):
        lat = q[:, 1]
        dark = np.clip(_noise(q, self.wave_dirs[:5], self.wave_f[:5] * 1.1, self.wave_ph[:5] + 1.3) * 1.4 - 0.15, 0, 1)
        alb = 0.72 - 0.3 * dark
        cap = np.clip((lat - 0.9) / 0.03, 0, 1) + np.clip((-lat - 0.94) / 0.02, 0, 1)
        r, dep = self.mars_crater_r, 0.05
        grad = _radial_grad(q, self.mars_crater, lambda d: self._crater_slope(d / r) / r * dep)
        s, h = self.volcano_s, self.volcano_h
        grad += _radial_grad(q, self.volcanoes, lambda d: -2 * h * d / (s * s) * np.exp(-(d / s) ** 2))
        grad += _radial_grad(q, self.volcanoes[:1], lambda d: 2 * 0.015 * d / 0.03 ** 2 * np.exp(-(d / 0.03) ** 2))
        # the rift: a trench across the great circle, faded in along its length
        sg = q @ self.rift_g
        win = np.clip((q @ self.rift_p - math.cos(0.65)) / 0.08, 0, 1)
        trench = np.exp(-(sg / 0.035) ** 2) * win
        grad += (2 * 0.05 * sg / 0.035 ** 2 * trench)[:, None] * (self.rift_g - sg[:, None] * q)
        alb = alb * (1 - 0.35 * trench)
        alb = alb * (1 - cap) + 0.97 * np.clip(cap, 0, 1)
        nv = _bend(q, grad) @ m.T
        ndl = nv @ light
        lit = np.clip(ndl, 0, 1) * alb + 0.02
        return lit + 0.15 * (1 - n[:, 2]) ** 3 * np.clip(n @ light + 0.2, 0, 1)     # dust in the air

    def _giant(self, n, q, light, m):
        lat = np.arcsin(np.clip(q[:, 1], -1, 1))
        lon = np.arctan2(q[:, 0], q[:, 2])
        band = np.sin(lat * 9 + 0.7 * np.sin(lat * 23) + 0.35 * np.sin(lon * 2 + lat * 14 + self.t * 0.4))
        alb = 0.55 + 0.3 * band
        spot = ((lon - 1.0) / 0.45) ** 2 + ((lat + 0.35) / 0.17) ** 2
        alb = np.where(spot < 1, 0.95 - 0.25 * spot, alb)
        return np.clip(n @ light, 0, 1) * alb + 0.02

    def _europa(self, n, q, light, m):
        mott = _noise(q, self.wave_dirs[1:6], self.wave_f[1:6] * 1.6, self.wave_ph[1:6])
        alb = 0.86 - 0.08 * mott
        s = np.abs(q @ self.lin_g.T)
        arc = np.clip((q @ self.lin_p.T - self.lin_cos) / 0.15, 0, 1)
        line = (np.clip(1.5 - s / self.lin_w, 0, 1) * arc).max(1)
        alb = alb * (1 - 0.5 * np.clip(line, 0, 1))
        chaos = np.clip(_noise(q, self.wave_dirs[3:], self.wave_f[3:] * 2.2, self.wave_ph[3:] + 4) * 2 - 1.1, 0, 1)
        alb = alb * (1 - 0.35 * chaos)
        ndl = n @ light
        refl = 2 * ndl[:, None] * n - light
        sheen = 0.25 * np.clip(refl[:, 2], 0, 1) ** 12
        return np.clip(ndl, 0, 1) * alb + sheen + 0.02

    def _lava(self, n, q, light, m):
        dots = q @ self.plates.T
        top = -np.partition(-dots, 1, axis=1)[:, :2]
        seam = np.abs(top[:, 0] - top[:, 1])            # zero along the seams between plates
        flick = 0.75 + 0.25 * np.sin((q @ self.wave_dirs[4]) * 9 + self.t * 1.7) * np.sin((q @ self.wave_dirs[5]) * 6 - self.t)
        glow = np.exp(-(seam / 0.012) ** 2) * flick
        d = np.arccos(np.clip(q @ self.lakes.T, -1, 1)) / self.lake_r
        lake = np.clip((1.0 - d) / 0.2, 0, 1).max(1)
        crust = 0.3 + 0.1 * _noise(q, self.wave_dirs, self.wave_f * 1.8, self.wave_ph)
        ndl = n @ light
        hot = np.maximum(glow, 0.9 * lake)
        lit = np.clip(ndl, 0, 1) * crust * (1 - hot) + 0.015
        return lit + hot * (0.8 + 0.3 * self.beat)

    def _ice_giant(self, n, q, light, m):
        lat = q[:, 1]
        alb = 0.7 + 0.04 * np.sin(lat * 11 + 0.3 * np.sin(self.t * 0.2)) + 0.14 * np.clip(lat - 0.55, 0, 1) / 0.45
        cq = q @ _rot(self.t * 0.12, 0, 0)
        storm = np.clip(_noise(cq, self.wave_dirs[3:], self.wave_f[3:] * 2.5, self.wave_ph[3:]) * 2 - 1.3, 0, 1)
        alb = np.minimum(alb + 0.3 * storm * (np.abs(lat - 0.25) < 0.15), 1)
        ndl = n @ light
        return np.clip(ndl, 0, 1) ** 0.9 * alb * (0.6 + 0.4 * n[:, 2]) + 0.02

    def _pluto(self, n, q, light, m):
        alb = 0.55 + 0.13 * _noise(q, self.wave_dirs[2:6], self.wave_f[2:6] * 1.4, self.wave_ph[2:6] + 0.7)
        x = (q @ self.heart_e) / 0.36
        y = (q @ self.heart_n) / 0.36 + 0.2
        heart = (q @ self.heart_c > 0) & ((x * x + y * y - 1) ** 3 - x * x * y ** 3 < 0)
        lat = np.arcsin(np.clip(q[:, 1], -1, 1))
        lon = np.arctan2(q[:, 0], q[:, 2])
        edge = 0.08 * _noise(q, self.wave_dirs[4:], self.wave_f[4:] * 2, self.wave_ph[4:])
        belt = (np.abs(lat + 0.12 + edge) < 0.22) & (np.abs(lon + 1.5 + edge) < 0.95)
        alb = np.where(heart, 0.96, np.where(belt, 0.2, alb))
        r = self.pluto_crater_r
        grad = _radial_grad(q, self.pluto_crater, lambda d: self._crater_slope(d / r) / r * 0.04)
        nv = _bend(q, grad) @ m.T
        return np.clip(nv @ light, 0, 1) * alb + 0.02

    # relief
    @staticmethod
    def _crater_slope(u):
        """A crater's height profile h(u), u its distance in radii: a bowl inside (u^2 - 1), a raised
        rim out to u = 1.5. This is its slope."""
        return np.where(u < 1, 2 * u, np.where(u < 1.5, 0.35 * math.pi / 0.5 * np.cos(math.pi * (u - 1) / 0.5), 0))

    def _craters(self, q):
        """The moon's surface normal (world frame), bent by every crater's bowl and rim."""
        r, dep = self.crater_r, self.crater_d * 0.11
        return _bend(q, _radial_grad(q, self.crater, lambda d: self._crater_slope(d / r) / r * dep))

    # air, rings and moons
    def _haze(self, tone, sx, sy, r2, light, thick):
        """A thin atmosphere past the limb, bright where the sun is, and all round when it's behind."""
        r = np.sqrt(r2)
        rim = (r >= 1) & (r < 1 + 4 * thick)
        rr = r[rim]
        toward = (sx[rim] * light[0] + sy[rim] * light[1]) / rr
        ill = np.clip(toward + 0.3, 0, 1) + 0.9 * max(0.0, -float(light[2])) ** 2
        tone[rim] = np.maximum(tone[rim], 0.55 * np.exp(-(rr - 1) / thick) * ill)

    def _ring_band(self, r):
        """The giant's ring opacity by radius (in planet radii): banded, with a dark gap."""
        inside = (r > RING_IN) & (r < RING_OUT)
        dens = 0.55 + 0.3 * np.sin(r * 31) + 0.15 * np.sin(r * 73)
        gap = np.abs(r - 1.78) < 0.05
        return np.where(inside & ~gap, np.clip(dens, 0.1, 1), 0)

    def _thin_rings(self, r):
        out = np.zeros_like(r)
        for rad, w, o in THIN_RINGS:
            out = np.maximum(out, o * np.clip(1.5 - np.abs(r - rad) / (w / 2), 0, 1))
        return out

    def _ring_shadow(self, n, light, m, band):
        """How much the rings shade each point on the disc, along its line to the sun."""
        axis = m[:, 1]
        la = float(light @ axis)
        if abs(la) < 1e-3:
            return np.zeros(len(n), np.float32)
        t = -(n @ axis) / la
        p = n + t[:, None] * light
        return np.where(t > 0, band(np.linalg.norm(p, axis=1)), 0)

    def _rings(self, tone, sx, sy, r2, light, m, band):
        axis = m[:, 1]
        if abs(axis[2]) < 0.03:
            return
        z = -(sx * axis[0] + sy * axis[1]) / axis[2]            # where each pixel's sightline meets the ring plane
        r = np.sqrt(sx * sx + sy * sy + z * z)
        opacity = band(r)
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

    def _moonlet_shadow(self, n, light, p):
        """The little moon's shadow on the disc: where the line to the sun passes within its radius."""
        v = p - n
        t = v @ light
        d2 = (v * v).sum(1) - t * t
        return np.where(t > 0, np.clip((MOONLET_R ** 2 - d2) / (0.4 * MOONLET_R ** 2), 0, 1), 0)

    def _draw_moonlet(self, tone, sx, sy, r2, light, p):
        dx, dy = sx - p[0], sy - p[1]
        d2 = dx * dx + dy * dy
        on = d2 < MOONLET_R ** 2
        if not on.any():
            return
        nz = np.sqrt(MOONLET_R ** 2 - d2[on])
        z = p[2] + nz
        clear = (r2[on] >= 1) | (z > np.sqrt(np.clip(1 - r2[on], 0, 1)))       # not behind the planet
        nrm = np.stack([dx[on], dy[on], nz], -1) / MOONLET_R
        b, c = float(p @ light), float(p @ p) - 1                               # in the planet's shadow?
        dark = 0.06 if (b < 0 and b * b - c > 0) else 1.0
        lit = np.clip(nrm @ light, 0, 1) * 0.75 * dark + 0.02
        idx = np.flatnonzero(on)[clear]
        tone.flat[idx] = lit[clear]

    def lights(self):
        inks = ink.PALETTES[self.pal_i][1]
        k1 = self.glow(1, 0.08, 0.6) if self.hold else self.glow(1, 0.55, 0.2 + 0.4 * min(1.0, abs(self.rate) / 1.0))
        return [self.glow(0, self.world / len(WORLDS), 0.3 + 0.4 * (1 + math.cos(self.phase)) / 2), k1,
                self.glow(2, self.screen_i / len(ink.SCREENS)), tuple(float(c) for c in inks[-1])]
