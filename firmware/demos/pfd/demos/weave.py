"""Weave: cloth coming off the loom, coloured threads over and under.

After Lee's Lissajous Weave and 0511's striped tiles. Warp threads run down,
weft threads across, and the weave structure says which is on top at each
crossing: plain (alternating), twill (stepping into diagonals), basket (in
pairs) or satin (long floats). Both sets of threads are dyed in a repeating
stripe sequence from the palette, so the cloth comes out a plaid. Each thread
is shaded round across its width and dips where it passes under its
neighbour, so the cloth has texture. It scrolls slowly up, as if being woven
at the bottom, and ripples a little.
"""
import math

import numpy as np

from ..draw import X, Y
from .original import Chromatic

STRUCTURES = ["plain", "twill", "basket", "satin"]


class Weave(Chromatic):
    name = "Weave"
    blurb = "Cloth coming off the loom, coloured threads over and under (after Lee's Lissajous Weave). k0 thread size, k1 weave, k2 ripple, k3 colour. Click k1 a new plaid, k2 hold still, k3 next palette."
    palette = 2

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.size, self.structure, self.ripple = 8, 1, 1.0
        self.still = False
        self.roll = 0.0
        self.t = 0.0
        self.plaid()

    def plaid(self):
        """A stripe sequence for warp and weft: runs of a few colours, mirrored like a sett."""
        r = self.rng
        runs = [(float(r.random()), int(r.integers(1, 5))) for _ in range(int(r.integers(3, 6)))]
        seq = [c for c, n in runs for _ in range(n)]
        seq = seq + seq[::-1]                     # a mirrored sett, as tartans are
        self.warp_seq = np.array(seq, np.float32)
        self.weft_seq = np.roll(self.warp_seq, int(r.integers(len(seq))))

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.size = max(3, min(14, self.size + (1 if d > 0 else -1)))
        elif k == 1:
            self.structure = (self.structure + (1 if d > 0 else -1)) % len(STRUCTURES)
        elif k == 2:
            self.ripple = max(0.0, min(3.0, self.ripple + d * 0.1))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 1:
            self.plaid()
        elif k == 2:
            self.still = not self.still
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        if not self.still:
            self.roll += dt * 3 * (1 + self.sound[1])
        if self.on_phrase:
            self.plaid()
        if self.on_bar and self.rt.audio.bar_in_phrase % 4 == 0:
            self.structure = (self.structure + 1) % len(STRUCTURES)

    def over(self, i, j):
        """True where the warp thread (column i) is on top of the weft (row j)."""
        s = STRUCTURES[self.structure]
        if s == "plain":
            return (i + j) % 2 == 0
        if s == "twill":
            return (i + j) % 4 < 2
        if s == "basket":
            return (i // 2 + j // 2) % 2 == 0
        return (i * 2 + j) % 5 != 0               # satin: the warp floats long, the weft shows once in five

    def render(self):
        s = self.size
        amp = self.ripple * (1 + 0.6 * self.sound[2])
        x = X + amp * 1.5 * np.sin(Y * 0.07 + self.t * 0.9)
        y = Y + self.roll + amp * 1.5 * np.sin(X * 0.06 - self.t * 0.7)
        i, j = np.floor(x / s).astype(int), np.floor(y / s).astype(int)
        u, v = x / s - i, y / s - j                                  # position within the crossing
        top = self.over(i, j)
        warp_c = self.colour(self.warp_seq[i % len(self.warp_seq)])
        weft_c = self.colour(self.weft_seq[j % len(self.weft_seq)])
        # round across the thread on top; darker where it dives under at the ends of a float
        across = np.where(top, u, v)
        along = np.where(top, v, u)
        roundness = 0.55 + 0.45 * np.sin(math.pi * np.clip(across, 0, 1))
        dive = 0.75 + 0.25 * np.sin(math.pi * np.clip(along, 0, 1))
        gap = (np.minimum(across, 1 - across) < 0.08)                 # the little gap between threads
        img = np.where(top[..., None], warp_c, weft_c) * (roundness * dive)[..., None]
        img[gap] *= 0.35
        return np.clip(img * (1 + 0.2 * self.beat), 0, 1)

    def lights(self):
        return [self.glow(0, 0.15, 0.1 + 0.05 * self.size), self.glow(1, self.structure / 4),
                self.glow(2, 0.55, 0.2 + 0.2 * self.ripple), self.hue_light()]
