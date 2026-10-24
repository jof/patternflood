"""Point shapes made of the music, in the manner of AVS superscopes (Winamp's
Advanced Visualization Studio).

Each frame a few hundred points are computed from the spectrum and waveform,
projected, and drawn with glowing trails:

    ring     the spectrum wrapped round a circle, turning with the bar
    tunnel   a ring of the waveform launched on each beat, flying at you
    knot     a torus knot whose radius breathes with the bass
    sphere   points on a sphere pushed out by the band at their latitude

The shape changes at each phrase.

    k0  shape
    k1  hue
    k2  trails
    k3  spin
"""
import math

import numpy as np

from .. import draw
from ..draw import N, hsv
from ..runtime import Demo

SHAPES = ["ring", "tunnel", "knot", "sphere"]


def _fib_sphere(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.cos(phi), np.sin(th) * np.sin(phi)], 1), phi / np.pi


class Superscope(Demo):
    name = "Superscope"
    group = "audio"
    blurb = "Point shapes made of the music, after Winamp's AVS: spectrum ring, waveform tunnel, torus knot, spectrum sphere. k0 shape, k1 hue, k2 trails, k3 spin."

    def __init__(self, rt):
        super().__init__(rt)
        self.shape = 0
        self.hue = 0.55
        self.trail = 0.78
        self.spin_k = 1.0
        self.buf = draw.blank()
        self.rings = []                    # tunnel: [z, waveform points]
        self.yaw = self.pitch = 0.0
        self.sphere, self.lat = _fib_sphere(420)
        self.t_shape = rt.t

    def turn(self, k, d):
        if k == 0:
            self.shape = (self.shape + (1 if d > 0 else -1)) % len(SHAPES)
            self.t_shape = self.rt.t
        elif k == 1:
            self.hue = (self.hue + d / 48) % 1.0
        elif k == 2:
            self.trail = min(0.95, max(0.4, self.trail + d * 0.02))
        elif k == 3:
            self.spin_k = min(4.0, max(0.0, self.spin_k + d * 0.1))

    def _project(self, p):
        """Turn by yaw and pitch, then perspective onto the panel."""
        cy, sy, cp, sp = math.cos(self.yaw), math.sin(self.yaw), math.cos(self.pitch), math.sin(self.pitch)
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        x, z = cy * x + sy * z, -sy * x + cy * z
        y, z = cp * y - sp * z, sp * y + cp * z
        s = 1.6 / (z + 2.6)
        return 63.5 + x * s * 64, 63.5 + y * s * 64, s

    def step(self, dt):
        a = self.rt.audio
        if a.phrase:
            self.shape = (self.shape + 1) % len(SHAPES)
            self.t_shape = self.rt.t
        bar = 4 * 60.0 / max(60.0, a.bpm or 120.0)
        self.yaw += dt * self.spin_k * (2 * math.pi / (2 * bar))
        self.pitch = 0.35 * math.sin(self.rt.t * 0.3)
        self.buf *= self.trail ** (dt * 60)
        bands = np.asarray(a.bands, np.float32)
        wave = np.asarray(a.wave, np.float32).mean(1)
        wave = wave / max(0.05, float(np.abs(wave).max()))
        shape = SHAPES[self.shape]
        kick = math.exp(-a.phase * 5)

        if shape == "ring":
            n = 360
            th = np.linspace(0, 2 * np.pi, n, endpoint=False) + a.bar_phase * np.pi / 2
            bi = np.abs(((th / np.pi) % 2) - 1) * 23                     # the bands, mirrored round the ring
            v = np.interp(bi, np.arange(24), bands)
            r = 0.45 + 0.45 * v + 0.05 * kick
            pts = np.stack([np.cos(th) * r, np.sin(th) * r, np.zeros(n)], 1)
            hues = self.hue + v * 0.3
        elif shape == "tunnel":
            if a.beat or not self.rings:
                seg = wave[::4][:256]
                self.rings.append([3.0, seg.copy(), a.beat_in_bar == 0])
            speed = (a.bpm or 120) / 60 * 0.8
            for r in self.rings:
                r[0] -= dt * speed
            self.rings = [r for r in self.rings if r[0] > -1.5][-16:]
            pts, hues = [], []
            for z, seg, one in self.rings:
                th = np.linspace(0, 2 * np.pi, len(seg), endpoint=False)
                rad = 0.7 + 0.25 * seg
                pts.append(np.stack([np.cos(th) * rad, np.sin(th) * rad, np.full(len(seg), z)], 1))
                hues.append(np.full(len(seg), self.hue + (0.5 if one else 0) + z * 0.05))
            pts, hues = np.concatenate(pts), np.concatenate(hues)
        elif shape == "knot":
            n = 500
            t = np.linspace(0, 2 * np.pi, n)
            p, q = 2, 3
            r = 0.55 + 0.25 * np.cos(q * t) * (0.6 + 0.8 * a.bass) + 0.05 * kick
            pts = np.stack([r * np.cos(p * t), r * np.sin(p * t), 0.35 * np.sin(q * t)], 1)
            hues = self.hue + t / (2 * np.pi) * 0.4
        else:
            v = np.interp(self.lat * 23, np.arange(24), bands)
            pts = self.sphere * (0.55 + 0.4 * v + 0.05 * kick)[:, None]
            hues = self.hue + self.lat * 0.4

        xs, ys, s = self._project(pts)
        cols = hsv(np.asarray(hues), np.full(len(xs), 0.75), np.clip(0.4 + 0.6 * s * a.level + 0.3 * kick, 0, 1))
        draw.plot(self.buf, xs, ys, cols.astype(np.float32) * 0.8, op="add")

    def render(self):
        b = np.clip(self.buf, 0, 1)
        glow = (np.roll(b, 1, 0) + np.roll(b, -1, 0) + np.roll(b, 1, 1) + np.roll(b, -1, 1)) * 0.1
        img = b + glow
        if self.rt.t - self.t_shape < 1.2:
            draw.text(img, SHAPES[self.shape], 64, 2, (.8, .8, .8), center=True)
        return img

    def lights(self):
        a = self.rt.audio
        b = math.exp(-a.phase * 5)
        return [(.3 + .7 * b,) * 3, tuple(float(x) for x in hsv(np.array(self.hue), np.array(.7), np.array(.8))),
                (self.trail * .5,) * 3, (min(1, self.spin_k / 3),) * 3]
