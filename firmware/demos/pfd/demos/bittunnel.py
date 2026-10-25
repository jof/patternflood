"""Bit Tunnel: a flight down a tunnel papered with bitwise texture.

After SeungHun's bitwise patterns (0521's XOR masks, 0522's quad-fold gate). The
demoscene XOR texture, (u ^ v), is wrapped round a tunnel. Its cross-section
morphs from round to square to diamond to petals, and its mouth wanders. Depth
fades it into the dark through a dither screen, and a mask on the texture's
bits (as 0521's threshold knob) cuts it into blocks, stripes and lattices.
"""
import math

import numpy as np

from .. import ink
from ..draw import X, Y
from .original import Original

OPS = ["xor", "xor mask", "and", "or", "checker", "xor mod"]
SHAPES = ["round", "square", "diamond", "petals"]


class BitTunnel(Original):
    name = "Bit Tunnel"
    blurb = "Down a tunnel of XOR texture (after SeungHun's 0521 bit masks). k0 speed (and reverse), k1 roll, k2 bit pattern, k3 inks. Click k0 stop, k1 shape, k2 chunky, k3 screen."

    def __init__(self, rt):
        super().__init__(rt)
        self.speed, self.go = 1.0, True
        self.roll = 0.0
        self.roll_rate = 0.15
        self.op = 0
        self.mask = 3
        self.shape = self.shape_to = 0.0
        self.pal_i, self.screen_i, self.scale = 3, 0, 1
        self.z = self.a = self.t = 0.0
        self.thresh = ink.screen(ink.SCREENS[0])

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.speed = max(-4.0, min(6.0, self.speed + d * 0.15))
        elif k == 1:
            self.roll_rate = max(-1.5, min(1.5, self.roll_rate + d * 0.05))
        elif k == 2:                                    # through each op's masks, then the next op
            self.mask += 1 if d > 0 else -1
            if self.mask > 5:
                self.mask, self.op = 1, (self.op + 1) % len(OPS)
            elif self.mask < 1:
                self.mask, self.op = 5, (self.op - 1) % len(OPS)
        elif k == 3:
            self.pal_i = (self.pal_i + (1 if d > 0 else -1)) % len(ink.PALETTES)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.go = not self.go
        elif k == 1:
            self.shape_to = math.floor(self.shape_to) + 1
        elif k == 2:
            self.scale = 3 - self.scale
            self._screen()
        elif k == 3:
            self.screen_i = (self.screen_i + 1) % len(ink.SCREENS)
            self._screen()

    def _screen(self):
        self.thresh = ink.screen(ink.SCREENS[self.screen_i], self.scale, angle=0.6, pitch=4.0 * self.scale)

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        v = self.speed * (1 + 1.5 * self.sound[2] + 2 * self.beat) if self.go else 0.0
        self.z += v * dt * 40
        self.roll += (self.roll_rate + 0.6 * self.sound[0]) * dt
        if self.rt.t - self.t_touch[1] > 25:            # left alone, the cross-section morphs on
            self.shape_to += dt / 20
        if self.on_phrase:
            self.shape_to = math.floor(self.shape_to) + 1
        if self.on_bar:
            self.mask = self.mask % 5 + 1
        self.shape += (self.shape_to - self.shape) * (1 - math.exp(-dt / 0.8))

    def _radius(self, dx, dy, ang):
        """Distance in the tunnel's own metric, blending between cross-sections."""
        def metric(i):
            s = SHAPES[i % len(SHAPES)]
            if s == "round":
                return np.hypot(dx, dy)
            if s == "square":
                return np.maximum(np.abs(dx), np.abs(dy))
            if s == "diamond":
                return (np.abs(dx) + np.abs(dy)) * 0.72
            return np.hypot(dx, dy) * (1 + 0.22 * np.cos(5 * ang + self.t * 0.7))
        i, f = int(math.floor(self.shape)), self.shape % 1
        f = f * f * (3 - 2 * f)
        r = metric(i)
        return r if f < 1e-3 else r * (1 - f) + metric(i + 1) * f

    def render(self):
        t = self.t
        cx = 63.5 + 20 * math.sin(t * 0.31) + 6 * math.sin(t * 0.83)
        cy = 63.5 + 16 * math.sin(t * 0.23 + 1.2) + 5 * math.cos(t * 0.71)
        dx, dy = X - cx, Y - cy
        ang = np.arctan2(dy, dx)
        r = self._radius(dx, dy, ang) + 0.5
        depth = 1400.0 / r
        u = ((ang / (2 * math.pi) + self.roll) * 128 + depth * 0.12 * math.sin(t * 0.2)).astype(np.int32) & 63
        v = (depth + self.z).astype(np.int32) & 63
        tex = self._texture(u, v)
        fog = np.clip(r / 70, 0, 1) ** 0.8
        core = np.exp(-r / 6) * (0.7 + 0.6 * self.sound[1])         # the light at the end
        tone = tex * fog * (1.05 + 0.3 * self.beat) + core
        inks = ink.PALETTES[self.pal_i][1]
        return ink.dither(tone, inks, self.thresh, self.scale)

    def _texture(self, u, v):
        # u, v are 6-bit texel coordinates; m (1..5) is how many of the high bits a pattern looks at
        op, m = OPS[self.op], min(self.mask, 5)
        if op == "xor":
            return (u ^ v) / 63.0
        if op == "xor mask":                     # 0521's gate: lit where the masked bits of u ^ v all clear
            bits = ((1 << m) - 1) << (6 - m)
            return np.where((u ^ v) & bits == 0, 1.0, 0.18 + 0.2 * ((u ^ v) & 7) / 7.0)
        if op == "and":
            return np.where((u & v) >> (6 - m) == 0, 0.95, 0.15)
        if op == "or":
            return ((u | v) >> (6 - m)) / float((1 << m) - 1)
        if op == "checker":
            return (((u >> (6 - m)) ^ (v >> (6 - m))) & 1) * 0.85 + 0.1
        return ((u ^ v) % (m * 5 + 3)) / float(m * 5 + 2)

    def lights(self):
        inks = ink.PALETTES[self.pal_i][1]
        return [self.glow(0, 0.3 if self.go else 0.0), self.glow(1, (self.shape / len(SHAPES)) % 1),
                self.glow(2, self.op / len(OPS)), tuple(float(c) for c in inks[-1])]
