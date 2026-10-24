"""Feedback visuals in the manner of MilkDrop, Winamp's: an engine, and families of presets.

Every frame the last one is resampled through a motion field, dimmed a little, and
waveforms and shapes are drawn on top: whatever was drawn flows away along the field
and leaves trails. Like MilkDrop, the field is per pixel:

    zoom      per second, pushed by the bass; zoom_rad makes it grow towards the
              edges (a tunnel) or the centre
    rot       per second, pushed by the mids; rot_rad twists the middle more (a whirlpool)
    warp      a sine wobble, pushed by the treble
    cx, cy    the centre of zoom and turn, which can wander with the bass
    dx, dy    a drift; sx, sy a stretch; wrap: edges wrap round instead of going black

then waves (circle, spiral, line, double line, dots, spectrum, stereo xy) and shapes:
polygons, solid or *textured*, filled with a shrunken copy of the screen, which is
MilkDrop's signature look. On the way out, never into the buffer: video echo (an
overlay of the frame zoomed and flipped onto itself), a kaleidoscope fold, a colour
map of brightness, and on a drop a flash of inversion.

On top of each preset runs a rhythm layer, from the beat tracker, so the motion is locked
to the music rather than just following its loudness:

    beat     a zoom punch that decays through the beat; the wave swells on the kick;
             the hue steps on; the warp's wobble cycles in beat time
    bar      the turn swings one way for a bar and back the next; the downbeat stamps a
             bright ring that then flows out through the field (tunnels fly one per bar)
    phrase   zoom and warp ramp up across the eight bars, then let go at the boundary,
             where the next preset cuts in over half a bar with a flash
    build    pushes the warp; a drop punches the zoom, flashes and inverts

Each demo is a family of presets; a drop jumps to a random one. k3 scales both the
sound's push and the rhythm layer.

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

DEFAULTS = dict(zoom=1.0, zoom_bass=0.0, zoom_rad=0.0, rot=0.0, rot_mid=0.0, rot_rad=0.0, warp=0.0, freq=3.0,
                speed=1.0, cx=0.0, cy=0.0, wander=0.0, dx=0.0, dy=0.0, sx=1.0, sy=1.0, decay=0.94, size=0.35,
                wave_y=0.0, hue_speed=0.05, echo=0.0, echo_zoom=1.0, gamma=1.0,
                wave="circle", wrap=False, mirror="none", echo_orient="none", cmap=None, fold=0, shapes=())
NUMERIC = ["zoom", "zoom_bass", "zoom_rad", "rot", "rot_mid", "rot_rad", "warp", "freq", "speed", "cx", "cy",
           "wander", "dx", "dy", "sx", "sy", "decay", "size", "wave_y", "hue_speed", "echo", "echo_zoom", "gamma"]

# Colour maps for brightness-mapped presets: stops from black up
CMAPS = {
    "heat": [(0, 0, 0), (0.45, 0.02, 0.0), (0.9, 0.25, 0.0), (1.0, 0.7, 0.1), (1.0, 1.0, 0.8)],
    "gas": [(0, 0, 0), (0.0, 0.05, 0.35), (0.1, 0.35, 1.0), (0.6, 0.85, 1.0), (1, 1, 1)],
    "aurora": [(0, 0, 0.02), (0.0, 0.25, 0.15), (0.1, 0.8, 0.4), (0.6, 0.4, 0.9), (1.0, 0.9, 1.0)],
}


def P(name, **kw):
    p = dict(DEFAULTS)
    p.update(kw, name=name)
    return p


def _lut(stops):
    stops = np.array(stops, np.float32)
    x = np.linspace(0, 1, len(stops))
    v = np.linspace(0, 1, 256)
    return np.stack([np.interp(v, x, stops[:, c]) for c in range(3)], 1).astype(np.float32)


LUTS = {k: _lut(v) for k, v in CMAPS.items()}


class MilkEngine(Demo):
    group = "audio"
    PRESETS = []

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.buf = draw.blank()
        self.cur = dict(self.PRESETS[0])
        self.frm = dict(self.PRESETS[0])
        self.to = dict(self.PRESETS[0])
        self.blend = 1.0
        self.pi = 0
        self.hue = 0.6
        self.trail_adj = 0.0
        self.sens = 1.0
        self.t = 0.0
        self.flash = 0.0
        self.invert = 0.0
        self.t_name = rt.t
        self.shape_rot = 0.0
        c = (np.arange(N, dtype=np.float32) - 63.5) / 64
        self.V, self.U = np.meshgrid(c, c, indexing="ij")
        self.fold_cache = {}

    # ---- presets

    def _go(self, i):
        self.pi = i % len(self.PRESETS)
        self.frm, self.to, self.blend = dict(self.cur), dict(self.PRESETS[self.pi]), 0.0
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
            self._go(self.rng.randrange(len(self.PRESETS)))

    # ---- the frame

    def _sample(self, b, x, y, wrap):
        """Bilinear sample of b at pixel coordinates x, y (arrays)."""
        if wrap:
            x, y = x % N, y % N
        x0, y0 = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32)
        fx, fy = (x - x0)[..., None], (y - y0)[..., None]
        if wrap:
            x0, y0 = x0 % N, y0 % N
            x1, y1 = (x0 + 1) % N, (y0 + 1) % N
            inside = 1.0
        else:
            inside = ((x0 >= 0) & (x0 < N - 1) & (y0 >= 0) & (y0 < N - 1))[..., None]
            x0, y0 = np.clip(x0, 0, N - 2), np.clip(y0, 0, N - 2)
            x1, y1 = x0 + 1, y0 + 1
        return (b[y0, x0] * (1 - fx) * (1 - fy) + b[y0, x1] * fx * (1 - fy)
                + b[y1, x0] * (1 - fx) * fy + b[y1, x1] * fx * fy) * inside

    def step(self, dt):
        a = self.rt.audio
        self.t += dt
        if a.phrase:
            self._go(self.pi + 1)
            self.flash = max(self.flash, 0.6)
        if a.drop:
            self._go(self.rng.randrange(len(self.PRESETS)))
            self.flash, self.invert, self.punch = 1.0, 1.0, 1.0
        bar = 4 * 60.0 / max(60.0, a.bpm or 120.0)
        self.blend = min(1.0, self.blend + dt / (bar / 2))     # the next preset cuts in over half a bar
        f = self.blend * self.blend * (3 - 2 * self.blend)
        for key in NUMERIC:
            self.cur[key] = self.frm[key] * (1 - f) + self.to[key] * f
        for key in ("wave", "mirror", "wrap", "echo_orient", "cmap", "fold", "shapes", "name"):
            self.cur[key] = self.to[key] if f > 0.5 else self.frm[key]
        p, s = self.cur, self.sens
        bass, mid, treble = a.bass * s, a.mid * s, a.treble * s

        # the rhythm layer
        R = min(2.0, s)
        beats = a.counts["beat"] + a.phase                      # time, in beats
        env = math.exp(-a.phase * 5) * (0.6 + 0.4 * min(1.0, a.kick + 0.3))
        ramp = a.phrase_phase ** 2                              # tension across the phrase
        swing = math.sin(math.pi * (a.counts.get("bar", 0) + a.bar_phase))   # one way a bar, back the next
        self.punch = getattr(self, "punch", 0.0) * math.exp(-dt * 3)
        if a.bar and a.live:
            self.stamp = 1.0

        # where each pixel samples the last frame from: back through the motion field
        cx = p["cx"] + p["wander"] * math.sin(beats * 0.35) * (0.4 + bass)
        cy = p["cy"] + p["wander"] * math.cos(beats * 0.27) * (0.4 + bass)
        x, y = self.U - cx, self.V - cy
        rad = np.sqrt(x * x + y * y)
        zbase = p["zoom"] + p["zoom_bass"] * bass + R * (0.45 * env + 0.35 * ramp + 1.2 * self.punch + 0.3 * a.build)
        zoom = zbase ** (dt * (1 + p["zoom_rad"] * (rad - 0.5)))
        x, y = x / zoom / p["sx"] ** dt, y / zoom / p["sy"] ** dt
        th = (p["rot"] + p["rot_mid"] * (mid - 0.2) + R * 0.7 * swing
              + p["rot_rad"] * np.clip(1 - rad, 0, 1)) * dt
        c, sn = np.cos(th), np.sin(th)
        x, y = c * x + sn * y, -sn * x + c * y
        w = (p["warp"] * (0.5 + treble) + R * 0.012 * (ramp + a.build)) * dt * 60
        tb = beats * math.pi * 0.5                              # the wobble cycles every four beats
        x = x + w * np.sin(y * p["freq"] + tb * p["speed"])
        y = y + w * np.cos(x * p["freq"] * 1.1 - tb * p["speed"] * 0.9)
        x, y = x + cx - p["dx"] * dt, y + cy - p["dy"] * dt
        out = self._sample(self.buf, x * 64 + 63.5, y * 64 + 63.5, p["wrap"])
        out *= (min(0.99, p["decay"] + self.trail_adj)) ** (dt * 60)
        if p["mirror"] == "x":
            out[:, N // 2:] = out[:, :N // 2][:, ::-1]
        elif p["mirror"] == "quad":
            out[:, N // 2:] = out[:, :N // 2][:, ::-1]
            out[N // 2:] = out[:N // 2][::-1]

        hue = self.hue + self.t * p["hue_speed"] + 0.2 * treble + math.floor(beats) / 24   # a step each beat
        kick = math.exp(-a.phase * 6) * min(1.0, a.kick + 0.3)
        self.wave_boost = 1 + 0.5 * R * env
        if getattr(self, "stamp", 0.0) > 0:
            # the downbeat stamps a ring, which the field then carries away
            col = np.array(hsv1(hue + 0.5, 0.5, 1.0), np.float32) * self.stamp
            draw.ring(out, 63.5 + (p["cx"]) * 64, 63.5 + p["cy"] * 64, 6 + 4 * bass, col, width=1.6)
            self.stamp = 0.0
        self._shapes(out, p, a, bass, hue, dt)
        self._wave(out, p, a, bass, hue, kick, s)
        if self.flash > 0:
            out += self.flash * 0.25
            self.flash = max(0.0, self.flash - dt * 2)
        self.buf = np.clip(out, 0, 1.5)

    def _shapes(self, out, p, a, bass, hue, dt):
        self.shape_rot += dt * (0.5 + a.mid)
        for sh in p["shapes"]:
            sides, r, sx_, sy_ = sh.get("sides", 4), sh.get("r", 0.3), sh.get("x", 0.0), sh.get("y", 0.0)
            r = r * (1 + sh.get("pulse", 0.3) * math.exp(-a.phase * 5) * min(1.0, a.kick + 0.2))
            rot = self.shape_rot * sh.get("spin", 1.0)
            pts = [((sx_ + r * math.cos(rot + 2 * math.pi * i / sides)) * 64 + 63.5,
                    (sy_ + r * math.sin(rot + 2 * math.pi * i / sides)) * 64 + 63.5) for i in range(sides)]
            if sh.get("textured", False):
                # fill the shape with the whole screen, shrunk into it: MilkDrop's textured shapes
                mask = np.zeros((N, N), bool)
                draw.poly(np.zeros((N, N), np.float32), pts, 1.0, mask_out=mask)
                if mask.any():
                    yy, xx = np.nonzero(mask)
                    k = sh.get("tex_zoom", 2.2) / max(0.1, r * 2)
                    srcx = ((xx - (sx_ * 64 + 63.5)) * k + 63.5)
                    srcy = ((yy - (sy_ * 64 + 63.5)) * k + 63.5)
                    cos_, sin_ = math.cos(-rot * 0.5), math.sin(-rot * 0.5)
                    rx, ry = srcx - 63.5, srcy - 63.5
                    srcx, srcy = cos_ * rx - sin_ * ry + 63.5, sin_ * rx + cos_ * ry + 63.5
                    tex = self._sample(self.buf, srcx, srcy, True)
                    out[yy, xx] = out[yy, xx] * 0.3 + tex * 0.85
            else:
                col = np.array(hsv1(hue + sh.get("hue", 0.0), 0.7, 0.8), np.float32)
                draw.poly(out, pts, col * (0.5 + 0.5 * a.level))
            if sh.get("border", True):
                bc = np.array(hsv1(hue + 0.5, 0.4, 1.0), np.float32)
                for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                    xs, ys = draw.segment(x0, y0, x1, y1, step=0.7)
                    draw.plot(out, xs, ys, bc * 0.8, op="max")

    def _wave(self, out, p, a, bass, hue, kick, s):
        stereo = np.asarray(a.wave, np.float32)
        wave = stereo.mean(1)[::4]
        pk = max(0.05, float(np.abs(wave).max()))
        wave = wave / pk
        n = len(wave)
        i = np.arange(n) / n
        col = np.array(hsv1(hue, 0.75, 0.5 + 0.5 * min(1.0, a.level * s)), np.float32) * (0.6 + 0.8 * kick)
        size = p["size"] * getattr(self, "wave_boost", 1.0)
        kind = p["wave"]
        if kind == "circle":
            th = i * 2 * np.pi
            r = size * (1 + 0.25 * wave * (0.5 + bass))
            xs, ys = r * np.cos(th), r * np.sin(th)
        elif kind == "spiral":
            th = i * 6 * np.pi + self.t
            r = size * i * (1 + 0.3 * wave)
            xs, ys = r * np.cos(th), r * np.sin(th)
        elif kind in ("line", "double"):
            xs, ys = (i - 0.5) * 1.8, wave * size * 0.5 + p["wave_y"]
            if kind == "double":
                xs = np.concatenate([xs, xs])
                ys = np.concatenate([ys - 0.25, -wave * size * 0.5 + p["wave_y"] + 0.25])
        elif kind == "spectrum":
            bands = np.interp(np.linspace(0, 23, 128), np.arange(24), np.asarray(a.bands, np.float32))
            xs = np.linspace(-0.9, 0.9, 128)
            ys = p["wave_y"] - bands * size
        elif kind == "xy":
            st = stereo[::2] / max(0.05, float(np.abs(stereo).max()))
            xs, ys = (st[:, 0] - st[:, 1]) * size, -(st[:, 0] + st[:, 1]) * size
        elif kind == "none":
            return
        else:
            xs = np.cos(i * 37.0 + self.t) * size * (1 + wave * 0.3)
            ys = np.sin(i * 23.0 - self.t) * size * (1 + wave * 0.3)
        px, py = xs * 64 + 63.5, ys * 64 + 63.5
        draw.plot(out, px, py, col, op="max")
        draw.plot(out, px + 1, py, col * 0.6, op="max")

    # ---- out: echo, fold, colour map, inversion

    def _fold_map(self, n):
        if n not in self.fold_cache:
            ang = np.arctan2(self.V, self.U)
            rad = np.hypot(self.U, self.V)
            wedge = math.pi / n
            a = np.abs((ang % (2 * wedge)) - wedge)
            x = rad * np.cos(a) * 64 + 63.5
            y = rad * np.sin(a) * 64 + 63.5
            self.fold_cache[n] = (np.clip(np.rint(y), 0, N - 1).astype(int), np.clip(np.rint(x), 0, N - 1).astype(int))
        return self.fold_cache[n]

    def render(self):
        p = self.cur
        img = np.clip(self.buf, 0, 1)
        if p["echo"] > 0.01:
            # video echo: the frame again, zoomed about the centre and flipped, laid over itself
            z = p["echo_zoom"]
            ex, ey = self.U / z, self.V / z
            if p["echo_orient"] in ("x", "xy"):
                ex = -ex
            if p["echo_orient"] in ("y", "xy"):
                ey = -ey
            echo = self._sample(img, ex * 64 + 63.5, ey * 64 + 63.5, True)
            img = np.maximum(img * (1 - p["echo"] * 0.4), echo * p["echo"])
        if p["fold"]:
            my, mx = self._fold_map(int(p["fold"]))
            img = img[my, mx]
        if p["cmap"]:
            lum = np.clip(img.max(-1), 0, 1)
            img = LUTS[p["cmap"]][(lum * 255).astype(np.int32)]
        if p["gamma"] != 1.0:
            img = img ** (1 / p["gamma"])
        if self.invert > 0:
            img = img * (1 - self.invert) + (1 - img) * self.invert * 0.6
            self.invert = max(0.0, self.invert - 0.05)
        if self.rt.t - self.t_name < 1.2:
            draw.text(img, p["name"], 64, 2, (.85, .85, .85), center=True)
        return img

    def lights(self):
        a = self.rt.audio
        c = hsv1(self.hue + self.t * self.cur["hue_speed"])
        b = math.exp(-a.phase * 5)
        return [tuple(v * (.2 + .8 * self.blend) for v in c), hsv1(self.hue), (.3,) * 3, tuple(v * b for v in c)]


class Milk(MilkEngine):
    name = "Milk"
    blurb = "Feedback visuals after MilkDrop: the last frame flows through a warp under the waveform. Presets blend each phrase. k0 preset, k1 hue, k2 trails, k3 sensitivity."
    PRESETS = [
        P("bloom", zoom=1.35, zoom_bass=1.2, rot=0.15, rot_mid=0.6, warp=0.02, freq=3.0, speed=1.0, decay=0.93,
          wave="circle", size=0.35, hue_speed=0.05),
        P("vortex", zoom=1.1, zoom_bass=0.6, rot=0.9, rot_mid=1.5, warp=0.01, freq=5.0, speed=2.0, decay=0.95,
          wave="spiral", size=0.3, hue_speed=0.08),
        P("ripple", zoom=1.05, zoom_bass=0.4, rot_mid=0.2, warp=0.06, freq=6.0, speed=3.0, decay=0.94,
          wave="line", size=0.4, hue_speed=0.03, mirror="x", dy=-0.08),
        P("mandala", zoom=1.2, zoom_bass=0.9, rot=-0.4, rot_mid=0.8, warp=0.03, freq=4.0, speed=1.5, decay=0.92,
          wave="circle", size=0.25, hue_speed=0.1, mirror="quad"),
        P("nebula", zoom=0.97, zoom_bass=0.5, rot=0.25, rot_mid=0.4, warp=0.05, freq=2.0, speed=0.7, decay=0.965,
          wave="dots", size=0.45, hue_speed=0.02, dx=0.05),
    ]


class MilkTunnel(MilkEngine):
    name = "Milk Tunnel"
    blurb = "MilkDrop tunnels: zoom that grows towards the edges and twists the middle, a centre that wanders with the bass. Wormhole, hyperspace, twister."
    PRESETS = [
        P("wormhole", zoom=1.3, zoom_bass=1.0, zoom_rad=1.6, rot=0.3, rot_rad=1.6, rot_mid=0.6, wander=0.25,
          decay=0.955, wave="spiral", size=0.35, hue_speed=0.06, gamma=1.4),
        P("hyperspace", zoom=1.9, zoom_bass=1.5, zoom_rad=2.2, decay=0.935, wave="dots", size=0.32, hue_speed=0.03,
          wander=0.1, warp=0.005, gamma=1.5),
        P("twister", zoom=1.12, zoom_bass=0.5, zoom_rad=0.6, rot=0.4, rot_rad=4.0, rot_mid=1.0, decay=0.96,
          wave="circle", size=0.3, hue_speed=0.08, gamma=1.3),
        P("spectrum tunnel", zoom=1.45, zoom_bass=0.8, zoom_rad=1.0, rot=-0.2, rot_rad=1.0, decay=0.95,
          wave="spectrum", size=0.35, wave_y=0.2, hue_speed=0.05, wander=0.15, gamma=1.3),
    ]


class MilkFlame(MilkEngine):
    name = "Milk Flame"
    blurb = "MilkDrop fire: the frame drifts upward through a wobble and turns to flame through a colour map. Bonfire, blue gas, aurora."
    PRESETS = [
        P("bonfire", zoom=1.02, dy=0.55, warp=0.035, freq=7.0, speed=2.5, decay=0.95, wave="line", size=0.35,
          wave_y=0.78, cmap="heat", gamma=1.1, hue_speed=0.0, sx=1.02),
        P("blue gas", zoom=1.0, dy=0.4, warp=0.05, freq=5.0, speed=3.5, decay=0.955, wave="double", size=0.3,
          wave_y=0.6, cmap="gas", hue_speed=0.0),
        P("aurora", zoom=1.0, dy=0.25, dx=0.05, warp=0.02, freq=3.0, speed=1.0, decay=0.965, sx=1.04, sy=0.98,
          wave="spectrum", size=0.35, wave_y=0.85, cmap="aurora", hue_speed=0.0),
        P("embers", zoom=1.05, zoom_bass=0.4, dy=0.7, warp=0.06, freq=9.0, speed=4.0, decay=0.93, wave="dots",
          size=0.5, wave_y=0.4, cmap="heat", hue_speed=0.0),
    ]


class MilkMirror(MilkEngine):
    name = "Milk Mirror"
    blurb = "MilkDrop kaleidoscopes: mirror folds over spinning shapes filled with a shrunken copy of the screen."
    PRESETS = [
        P("hexes", zoom=1.08, rot=0.2, rot_mid=0.5, decay=0.95, wave="circle", size=0.3, fold=6, hue_speed=0.06,
          shapes=({"sides": 6, "r": 0.28, "textured": True, "spin": 0.6},)),
        P("quad bloom", zoom=1.25, zoom_bass=0.9, rot=-0.3, decay=0.93, wave="spiral", size=0.35, mirror="quad",
          hue_speed=0.08, shapes=({"sides": 4, "r": 0.2, "x": 0.35, "y": 0.35, "spin": 1.5, "pulse": 0.5},)),
        P("triad", zoom=1.15, rot=0.5, rot_rad=1.0, decay=0.94, wave="xy", size=0.4, fold=3, hue_speed=0.05,
          shapes=({"sides": 3, "r": 0.35, "textured": True, "spin": -0.8, "tex_zoom": 1.6},)),
        P("rose window", zoom=1.0, rot=0.1, warp=0.02, decay=0.96, wave="dots", size=0.4, fold=8, hue_speed=0.04,
          shapes=({"sides": 8, "r": 0.18, "textured": True, "spin": 1.0},
                  {"sides": 5, "r": 0.1, "x": 0.5, "spin": -2.0, "hue": 0.3, "border": False})),
    ]


class MilkEcho(MilkEngine):
    name = "Milk Echo"
    blurb = "MilkDrop video echo: the frame laid over itself zoomed and flipped, with wrapping edges. Halls of mirrors."
    PRESETS = [
        P("hall of mirrors", zoom=1.1, rot=0.2, decay=0.94, wave="dots", size=0.4, echo=0.7, echo_zoom=1.6,
          echo_orient="x", wrap=True, hue_speed=0.05),
        P("double vision", zoom=1.03, warp=0.03, freq=4.0, decay=0.95, wave="double", size=0.35, echo=0.6,
          echo_zoom=0.7, echo_orient="xy", hue_speed=0.07),
        P("tiles", zoom=0.92, zoom_bass=0.3, rot=0.15, decay=0.96, wave="circle", size=0.3, wrap=True, echo=0.5,
          echo_zoom=2.0, echo_orient="y", hue_speed=0.03),
        P("ghosts", zoom=1.18, zoom_bass=0.8, rot=-0.5, rot_mid=0.8, decay=0.92, wave="spiral", size=0.3,
          echo=0.8, echo_zoom=1.3, echo_orient="xy", hue_speed=0.1),
    ]
