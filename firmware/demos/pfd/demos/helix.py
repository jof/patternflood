"""Helix: a DNA double helix, turning and rising forever, dithered.

After SeungHun's 0512, its flower of lines turning on a centre. Two backbones
wind round a common axis, joined by base pairs. Every atom is a shaded
sphere drawn as an impostor (each pixel of its disc knows its own normal and
depth), and a depth buffer sorts them, so the strands pass behind and in front
of each other properly. The helix rises and turns; the camera looks a little
across it. Unzip it (click k0) and the base pairs part from the top down, the
two strands swinging apart like a replication fork, then zip back up.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

STEP = 5.0                      # pixels between base pairs along the axis
TURN = 2 * math.pi / 10.5       # radians per base pair (B-DNA: 10.5 pairs a turn)
RADIUS = 25.0


class Helix(Inked):
    name = "Helix"
    blurb = "A DNA double helix turning and rising, dithered (after SeungHun's 0512). k0 spin, k1 tilt, k2 screen, k3 inks. Click k0 unzip, k2 chunky."
    palette, screen_kind = "ember", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        self.spin, self.rate = 0.0, 0.6
        self.tilt = 0.12
        self.rise = 0.0
        self.unzip, self.unzip_to = 0.0, 0.0
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.rate = max(-3.0, min(3.0, self.rate + d * 0.1))
        elif k == 1:
            self.tilt = max(-1.0, min(1.0, self.tilt + d * 0.04))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.unzip_to = 0.0 if self.unzip_to else 1.0
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        self.spin += self.rate * dt * (1 + self.sound[0])
        self.rise += dt * 6 * (1 + self.sound[2])
        if self.on_phrase:
            self.unzip_to = 0.0 if self.unzip_to else 1.0
        if self.rt.t - self.t_touch[0] > 30 and int(self.rt.t / 25) != int((self.rt.t - dt) / 25):
            self.unzip_to = 0.0 if self.unzip_to else 1.0   # left alone, it unzips and zips now and then
        self.unzip += (self.unzip_to - self.unzip) * (1 - math.exp(-dt / 2.5))

    def atoms(self):
        """Every sphere: (x, y, z, radius, tone), in screen pixels, z towards the viewer."""
        first = math.floor(-self.rise / STEP) - 4
        idx = np.arange(first, first + int(N / STEP) + 10)
        y = idx * STEP + self.rise                      # the axis runs down the screen, rising
        a = idx * TURN + self.spin
        # unzipping: from the top of the screen down, the strands swing out apart
        open_ = np.clip(self.unzip * 1.6 - (y + 10) / (N + 20), 0, 1)
        spread = 1 + 0.55 * open_
        out = []
        for strand, (off, tone) in enumerate(((0.0, 0.92), (math.pi * 0.78, 0.7))):     # the minor groove
            ang = a + off + (open_ * 0.8 if strand else -open_ * 0.8)
            x = np.cos(ang) * RADIUS * spread + (open_ * 8 * (1 if strand else -1))
            z = np.sin(ang) * RADIUS * spread
            out.append(np.column_stack([x, y, z, np.full_like(x, 4.4), np.full_like(x, tone)]))
            # the phosphate between this nucleotide and the next, a smaller sphere
            a2 = ang + TURN / 2
            x2 = np.cos(a2) * RADIUS * spread + (open_ * 8 * (1 if strand else -1))
            out.append(np.column_stack([x2, y + STEP / 2, np.sin(a2) * RADIUS * spread, np.full_like(x, 2.9), np.full_like(x, tone * 0.85)]))
        # base pairs: a short row of small spheres across, where the strands haven't parted
        s0, s1 = out[0], out[2]
        for f in (0.22, 0.4, 0.6, 0.78):
            p = s0[:, :3] * (1 - f) + s1[:, :3] * f
            keep = open_ < 0.25
            tone = np.where(np.arange(len(p)) % 4 < 2, 0.5, 0.38)
            out.append(np.column_stack([p[keep], np.full(keep.sum(), 2.6), tone[keep]]))
        return np.concatenate(out)

    def render(self):
        at = self.atoms()
        # tilt the axis towards us (about screen x) and centre it
        ct, st = math.cos(self.tilt), math.sin(self.tilt)
        y0 = at[:, 1] - 64
        sy = y0 * ct - at[:, 2] * st + 64
        sz = y0 * st + at[:, 2] * ct
        sx = at[:, 0] + 63.5
        tone = np.zeros((N, N), np.float32)
        depth = np.full((N, N), -1e9, np.float32)
        light = np.array([-0.5, -0.6, 0.62], np.float32)
        light /= np.linalg.norm(light)
        persp = 1 + sz / 260                            # nearer is a little bigger
        for x, y, z, r, tn, pz in zip(sx, sy, sz, at[:, 3], at[:, 4], persp):
            r = r * pz * (1 + 0.15 * self.beat)
            x0, x1 = max(0, int(x - r - 1)), min(N, int(x + r) + 2)
            y0_, y1 = max(0, int(y - r - 1)), min(N, int(y + r) + 2)
            if x0 >= x1 or y0_ >= y1:
                continue
            u = (X[y0_:y1, x0:x1] - x) / r
            v = (Y[y0_:y1, x0:x1] - y) / r
            q = 1 - u * u - v * v
            inside = q > 0
            w = np.sqrt(np.clip(q, 0, 1))
            zz = z + w * r
            front = inside & (zz > depth[y0_:y1, x0:x1])
            shade = np.clip(u * light[0] + v * light[1] + w * light[2], 0, 1)
            spec = shade ** 12
            val = tn * (0.18 + 0.75 * shade) + 0.35 * spec
            fog = np.clip(0.75 + z / 80, 0.35, 1)       # the far side dimmer
            tone[y0_:y1, x0:x1] = np.where(front, val * fog, tone[y0_:y1, x0:x1])
            depth[y0_:y1, x0:x1] = np.where(front, zz, depth[y0_:y1, x0:x1])
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.9, 0.2 + 0.2 * abs(self.rate)), self.glow(1, 0.55, 0.2 + 0.3 * abs(self.tilt))] + self.ink_lights()
