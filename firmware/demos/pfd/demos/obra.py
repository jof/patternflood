"""Obra: a solid lit object, printed in two to five inks through a dither screen.

After the 1-bit dithering of Lee's 0521 and 0522, and Obra Dinn's look. Here the
thing being dithered is a real 3D object: a raymarched signed-distance shape
that turns, morphs from one form to the next, and is lit by a light that circles it.
Its tone goes through an ordered or blue-noise screen (or prints as halftone
dots or engraving lines) onto a palette of inks, with a hard ink outline.
"""
import math
import time

import numpy as np

from .. import ink
from ..draw import N, X, Y
from ..io import log
from ..runtime import DETENTS_PER_REV
from .original import Original

R_BOUND = 1.42              # every shape fits in this sphere (at size 1)
STEPS = 32
HIT = 4e-3
FOV = 1.9
EYE = 3.0
SLOW_S = 0.012             # if a frame's render takes longer than this (a slower machine), march at half resolution


def _rays(res):
    """One ray per res x res block of pixels, through the block's centre, unit length."""
    c = np.arange(N // res, dtype=np.float32) * res + (res - 1) / 2
    u, v = np.meshgrid((c - 63.5) / 64, (63.5 - c) / 64)
    rd = np.stack([u.ravel(), v.ravel(), np.full(u.size, -FOV, np.float32)], -1)
    return rd / np.linalg.norm(rd, axis=-1, keepdims=True)


RAYS = {1: _rays(1), 2: _rays(2)}


def bound(rd, r):
    """The rays that meet the bounding sphere of radius r (the eye is on +z looking down -z),
    and where they enter and leave it."""
    b = -EYE * rd[:, 2]
    disc = b * b - (EYE * EYE - r * r)
    idx = np.flatnonzero(disc > 0)
    root = np.sqrt(disc[idx])
    return idx, (b[idx] - root).astype(np.float32), (b[idx] + root).astype(np.float32)


def _backdrop():
    """A dim floor glow under the object, with its shadow, so the screen shows in the dark too."""
    fy = np.clip((Y - 92) / 36, 0, 1)
    r = np.hypot((X - 64) / 48, (Y - 116) / 9)
    shadow = np.clip(1.3 - r, 0, 1)
    return (0.2 * fy * (1 - 0.95 * shadow)).astype(np.float32)


BACKDROP = _backdrop()


def _len(*c):
    return np.sqrt(sum(x * x for x in c))


def torus(p, t):
    q = _len(p[:, 0], p[:, 2]) - 0.82
    return _len(q, p[:, 1]) - 0.36


def gyroid(p, t):
    s = 3.4
    g = (np.sin(p[:, 0] * s + t) * np.cos(p[:, 1] * s) + np.sin(p[:, 1] * s) * np.cos(p[:, 2] * s)
         + np.sin(p[:, 2] * s) * np.cos(p[:, 0] * s))
    return np.maximum(_len(p[:, 0], p[:, 1], p[:, 2]) - 1.15, (np.abs(g) / s - 0.07) * 0.7)


def twisted(p, t):
    a = p[:, 1] * (1.3 + 0.5 * math.sin(t * 0.7))
    c, s = np.cos(a), np.sin(a)
    x, z = c * p[:, 0] - s * p[:, 2], s * p[:, 0] + c * p[:, 2]
    qx, qy, qz = np.abs(x) - 0.5, np.abs(p[:, 1]) - 0.95, np.abs(z) - 0.5
    out = _len(np.maximum(qx, 0), np.maximum(qy, 0), np.maximum(qz, 0))
    return (out + np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0) - 0.08) * 0.75


def blobs(p, t):
    d = None
    k = 0.45
    for i in range(4):
        ph = t * (0.6 + 0.17 * i) + i * 1.7
        c = (0.6 * math.sin(ph), 0.55 * math.cos(ph * 1.3 + i), 0.5 * math.sin(ph * 0.7 + 2 * i))
        di = _len(p[:, 0] - c[0], p[:, 1] - c[1], p[:, 2] - c[2]) - (0.42 + 0.06 * i)
        if d is None:
            d = di
        else:                                   # polynomial smooth min
            h = np.clip(0.5 + 0.5 * (di - d) / k, 0, 1)
            d = di + (d - di) * h - k * h * (1 - h)
    return d


def octa(p, t):
    return (np.abs(p[:, 0]) + np.abs(p[:, 1]) + np.abs(p[:, 2]) - 1.15) * 0.577


def rings(p, t):
    d = None
    for i, (a, b) in enumerate(((0, 1), (1, 2), (2, 0))):
        r = 1.0 - 0.18 * i
        q = _len(p[:, a], p[:, b]) - r
        di = _len(q, p[:, 3 - a - b]) - 0.1
        d = di if d is None else np.minimum(d, di)
    return d


SHAPES = [torus, blobs, twisted, gyroid, octa, rings]


def _rot(yaw, pitch):
    cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], np.float32)
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], np.float32)
    return ry @ rx


class Obra(Original):
    name = "Obra"
    blurb = "A lit solid, dithered into inks (after Lee's 0521/0522 dither). k0 turns it, k1 morphs the form, k2 screen, k3 inks. Click k0 spin, k2 chunky, k3 outline."

    def __init__(self, rt):
        super().__init__(rt)
        self.yaw, self.spin = 0.4, 0.35
        self.morph = self.morph_to = 0.0
        self.screen_i, self.pal_i = 0, 0
        self.scale, self.outline = 1, True
        self.t = 0.0
        self.light = 0.0
        self.thresh = ink.screen(ink.SCREENS[0])
        self.res, self.cost = 1, 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.yaw += d * 2 * math.pi / DETENTS_PER_REV
        elif k == 1:
            self.morph_to += d / 6
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
            self.spin = 0.0 if self.spin else 0.35
        elif k == 2:
            self.scale = 3 - self.scale
            self._screen()
        elif k == 3:
            self.outline = not self.outline

    def _screen(self):
        kind = ink.SCREENS[self.screen_i]
        self.thresh = ink.screen(kind, self.scale, angle=0.6, pitch=4.0 * self.scale)

    def sdf(self, p):
        n = len(SHAPES)
        m = self.morph % n
        i, f = int(m), m - int(m)
        f = f * f * (3 - 2 * f)
        a = SHAPES[i](p, self.t)
        if f < 1e-3:
            return a
        return a * (1 - f) + SHAPES[(i + 1) % n](p, self.t) * f

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        self.yaw += self.spin * dt * (1 + 2 * self.sound[0])
        self.morph += (self.morph_to - self.morph) * (1 - math.exp(-dt / 0.6))
        if self.rt.t - self.t_touch[1] > 20:          # left alone, it wanders through its forms
            self.morph_to += dt / 14
        self.morph_to += 0.12 * self.sound[3] * dt
        if self.on_phrase:
            self.morph_to = math.floor(self.morph_to) + 1
        self.light += dt * (0.5 + 2 * self.sound[0])

    def render(self):
        t0 = time.perf_counter()
        rot = _rot(self.yaw, 0.55 + 0.3 * math.sin(self.t * 0.23))
        size = 1 + 0.18 * self.sound[2] + 0.06 * self.beat
        eye = np.array([0, 0, EYE], np.float32)
        res = self.res
        RD = RAYS[res]
        idx, t, far = bound(RD, R_BOUND * size)
        # march in the object's own space: rays turned and scaled once, then only the live ones kept
        eye_o = eye @ rot / size
        rd_o = RD[idx] @ rot / size
        hit_t = np.full(len(RD), np.inf, np.float32)
        for _ in range(STEPS):
            d = self.sdf(eye_o + rd_o * t[:, None]) * size
            t += d
            hit = d < HIT
            hit_t[idx[hit]] = t[hit]
            keep = ~hit & (t < far)
            if not keep.all():
                idx, t, far, rd_o = idx[keep], t[keep], far[keep], rd_o[keep]
                if not len(idx):
                    break
        hits = np.flatnonzero(np.isfinite(hit_t))
        tone = np.zeros(len(RD), np.float32)
        if len(hits):
            rdh = RD[hits]
            ph = (eye + rdh * hit_t[hits, None]) @ rot / size
            e = 3e-3
            nrm = np.stack([self.sdf(ph + o) for o in
                            (np.array(v, np.float32) * e for v in ((1, -1, -1), (-1, -1, 1), (-1, 1, -1), (1, 1, 1)))], -1)
            nrm = nrm @ np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], np.float32)
            nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-9
            nrm = nrm @ rot.T                               # object space -> world
            la = self.light
            ld = np.array([math.cos(la) * 0.8, 0.6 + 0.2 * math.sin(la * 0.7), math.sin(la) * 0.8 + 0.4], np.float32)
            ld /= np.linalg.norm(ld)
            diff = (0.5 + 0.5 * (nrm @ ld)) ** 2      # wrapped: the shadow side still reads
            refl = ld - 2 * (nrm @ ld)[:, None] * nrm
            spec = np.clip((refl * rdh).sum(-1), 0, 1) ** 18
            rim = (1 - np.clip(-(nrm * rdh).sum(-1), 0, 1)) ** 3
            tone[hits] = 0.04 + 0.8 * diff + 0.5 * spec + 0.2 * rim + 0.25 * self.beat
        n = N // res
        m = np.isfinite(hit_t).reshape(n, n)
        tone = tone.reshape(n, n)
        if res > 1:
            m, tone = (a.repeat(res, 0).repeat(res, 1) for a in (m, tone))
        tone = np.where(m, tone, BACKDROP)
        inks = ink.PALETTES[self.pal_i][1]
        img = ink.dither(tone, inks, self.thresh, self.scale if ink.SCREENS[self.screen_i] != "dots" else 1)
        self.cost += (time.perf_counter() - t0 - self.cost) * 0.05
        if self.cost > SLOW_S and self.res == 1 and self.rt.t > 2:     # past the warm-up
            self.res = 2
            log(f"obra: {self.cost * 1000:.1f} ms a frame, marching at half resolution")
        if self.outline and len(hits):
            edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
            img[edge] = inks[-1] if len(inks) > 2 else inks[1]
        return img

    def lights(self):
        hue = (self.yaw / (2 * math.pi)) % 1
        inks = ink.PALETTES[self.pal_i][1]
        top = tuple(float(c) for c in inks[-1])
        return [self.glow(0, hue), self.glow(1, (self.morph / len(SHAPES)) % 1),
                self.glow(2, self.screen_i / len(ink.SCREENS)), top]
