"""Feedback visuals in the manner of MilkDrop, Winamp's.

Every frame the last one is resampled through a zoom, a turn and a sine warp,
dimmed a little, and the waveform is drawn on top: so whatever was drawn flows
away along the warp and leaves trails. Bass pushes the zoom, the mids the turn,
the treble the warp; the kick flashes the wave. Presets blend into one another
over a bar at each phrase boundary, and a drop jumps to a random one.

    k0  preset (turn), random preset (click)
    k1  hue
    k2  trails
    k3  sensitivity
"""
import math
import random

import numpy as np

from .. import draw
from ..draw import N, hsv1
from ..runtime import Demo

# zoom/turn/warp are per second; drift moves the picture; mirror folds it
PRESETS = [
    dict(name="bloom", zoom=1.35, zoom_bass=1.2, rot=0.15, rot_mid=0.6, warp=0.02, freq=3.0, speed=1.0,
         decay=0.93, wave="circle", size=0.35, hue_speed=0.05, mirror="none", drift=(0.0, 0.0)),
    dict(name="vortex", zoom=1.1, zoom_bass=0.6, rot=0.9, rot_mid=1.5, warp=0.01, freq=5.0, speed=2.0,
         decay=0.95, wave="spiral", size=0.3, hue_speed=0.08, mirror="none", drift=(0.0, 0.0)),
    dict(name="ripple", zoom=1.05, zoom_bass=0.4, rot=0.0, rot_mid=0.2, warp=0.06, freq=6.0, speed=3.0,
         decay=0.94, wave="line", size=0.4, hue_speed=0.03, mirror="x", drift=(0.0, -0.08)),
    dict(name="mandala", zoom=1.2, zoom_bass=0.9, rot=-0.4, rot_mid=0.8, warp=0.03, freq=4.0, speed=1.5,
         decay=0.92, wave="circle", size=0.25, hue_speed=0.1, mirror="quad", drift=(0.0, 0.0)),
    dict(name="nebula", zoom=0.97, zoom_bass=0.5, rot=0.25, rot_mid=0.4, warp=0.05, freq=2.0, speed=0.7,
         decay=0.965, wave="dots", size=0.45, hue_speed=0.02, mirror="none", drift=(0.05, 0.0)),
]
NUMERIC = ["zoom", "zoom_bass", "rot", "rot_mid", "warp", "freq", "speed", "decay", "size", "hue_speed"]


class Milk(Demo):
    name = "Milk"
    group = "audio"
    blurb = "Feedback visuals after MilkDrop: the last frame flows through a warp under the waveform. Presets blend each phrase. k0 preset, k1 hue, k2 trails, k3 sensitivity."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.buf = draw.blank()
        self.cur = dict(PRESETS[0])
        self.frm = dict(PRESETS[0])
        self.to = dict(PRESETS[0])
        self.blend = 1.0
        self.pi = 0
        self.hue = 0.6
        self.trail_adj = 0.0
        self.sens = 1.0
        self.t = 0.0
        self.flash = 0.0
        self.t_name = rt.t
        c = (np.arange(N, dtype=np.float32) - 63.5) / 64
        self.V, self.U = np.meshgrid(c, c, indexing="ij")

    def _go(self, i):
        self.pi = i % len(PRESETS)
        self.frm, self.to, self.blend = dict(self.cur), dict(PRESETS[self.pi]), 0.0
        self.t_name = self.rt.t

    def turn(self, k, d):
        if k == 0:
            self._go(self.pi + (1 if d > 0 else -1))
        elif k == 1:
            self.hue = (self.hue + d / 48) % 1.0
        elif k == 2:
            self.trail_adj = max(-0.1, min(0.03, self.trail_adj + d * 0.005))
        elif k == 3:
            self.sens = max(0.2, min(3.0, self.sens * 1.1 ** d))

    def release(self, k, click):
        if click and k == 0:
            self._go(self.rng.randrange(len(PRESETS)))

    def step(self, dt):
        a = self.rt.audio
        self.t += dt
        if a.phrase:
            self._go(self.pi + 1)
        if a.drop:
            self._go(self.rng.randrange(len(PRESETS)))
            self.flash = 1.0
        # blend presets over a bar
        bar = 4 * 60.0 / max(60.0, a.bpm or 120.0)
        self.blend = min(1.0, self.blend + dt / bar)
        f = self.blend * self.blend * (3 - 2 * self.blend)
        for key in NUMERIC:
            self.cur[key] = self.frm[key] * (1 - f) + self.to[key] * f
        for key in ("wave", "mirror", "drift", "name"):
            self.cur[key] = self.to[key] if f > 0.5 else self.frm[key]
        p, s = self.cur, self.sens
        bass, mid, treble = a.bass * s, a.mid * s, a.treble * s

        # where each pixel samples the last frame from: back through the zoom, turn and warp
        zoom = (p["zoom"] + p["zoom_bass"] * bass) ** dt
        th = (p["rot"] + p["rot_mid"] * (mid - 0.2)) * dt
        c, sn = math.cos(th), math.sin(th)
        u, v = self.U / zoom, self.V / zoom
        u, v = c * u + sn * v, -sn * u + c * v
        w = p["warp"] * (0.5 + treble) * dt * 60
        u = u + w * np.sin(v * p["freq"] + self.t * p["speed"])
        v = v + w * np.cos(u * p["freq"] * 1.1 - self.t * p["speed"] * 0.9)
        u, v = u - p["drift"][0] * dt, v - p["drift"][1] * dt
        x = (u * 64 + 63.5)
        y = (v * 64 + 63.5)
        x0, y0 = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32)
        fx, fy = (x - x0)[..., None], (y - y0)[..., None]
        inside = ((x0 >= 0) & (x0 < N - 1) & (y0 >= 0) & (y0 < N - 1))[..., None]
        x0, y0 = np.clip(x0, 0, N - 2), np.clip(y0, 0, N - 2)
        b = self.buf
        out = (b[y0, x0] * (1 - fx) * (1 - fy) + b[y0, x0 + 1] * fx * (1 - fy)
               + b[y0 + 1, x0] * (1 - fx) * fy + b[y0 + 1, x0 + 1] * fx * fy) * inside
        out *= (min(0.99, p["decay"] + self.trail_adj)) ** (dt * 60)
        if p["mirror"] == "x":
            out[:, N // 2:] = out[:, :N // 2][:, ::-1]
        elif p["mirror"] == "quad":
            out[:, N // 2:] = out[:, :N // 2][:, ::-1]
            out[N // 2:] = out[:N // 2][::-1]

        # the waveform, on top
        wave = np.asarray(a.wave, np.float32).mean(1)[::4]
        pk = max(0.05, float(np.abs(wave).max()))
        wave = wave / pk
        n = len(wave)
        i = np.arange(n) / n
        hue = self.hue + self.t * p["hue_speed"] + 0.2 * treble
        col = np.array(hsv1(hue, 0.75, 0.5 + 0.5 * min(1.0, a.level * s)), np.float32)
        kick = math.exp(-a.phase * 6) * min(1.0, a.kick + 0.3)
        col = col * (0.6 + 0.8 * kick)
        size = p["size"]
        if p["wave"] == "circle":
            th = i * 2 * np.pi
            r = size * (1 + 0.25 * wave * (0.5 + bass))
            xs, ys = r * np.cos(th), r * np.sin(th)
        elif p["wave"] == "spiral":
            th = i * 6 * np.pi + self.t
            r = size * i * (1 + 0.3 * wave)
            xs, ys = r * np.cos(th), r * np.sin(th)
        elif p["wave"] == "line":
            xs, ys = (i - 0.5) * 1.8, wave * size * 0.5
        else:
            xs, ys = (np.cos(i * 37.0 + self.t) * size * (1 + wave * 0.3), np.sin(i * 23.0 - self.t) * size * (1 + wave * 0.3))
        px, py = xs * 64 + 63.5, ys * 64 + 63.5
        draw.plot(out, px, py, col, op="max")
        draw.plot(out, px + 1, py, col * 0.6, op="max")
        if self.flash > 0:
            out += self.flash * 0.25
            self.flash = max(0.0, self.flash - dt * 2)
        self.buf = np.clip(out, 0, 1.5)

    def render(self):
        img = np.clip(self.buf, 0, 1)
        if self.rt.t - self.t_name < 1.2:
            draw.text(img, self.cur["name"], 64, 2, (.85, .85, .85), center=True)
        return img

    def lights(self):
        a = self.rt.audio
        c = hsv1(self.hue + self.t * self.cur["hue_speed"])
        b = math.exp(-a.phase * 5)
        return [tuple(v * (.2 + .8 * self.blend) for v in c), hsv1(self.hue), (.3,) * 3, tuple(v * b for v in c)]
