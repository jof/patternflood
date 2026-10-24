"""Resort: an endless city-pop coastline in the manner of Hiroshi Nagai's illustrations.

Flat, hard-edged colour and no texture: cobalt skies fading to a pale horizon,
big flat-bottomed cumulus, turquoise pools with white coping, palms, white
modernist blocks with crisp blue shadow faces, a coupe on the coast road, the
sun going down in flat bands. The coast is generated lot by lot from its
position, so it goes on forever and the same stretch always looks the same.
Nothing is copied from a real picture.

    k0  time of day: noon, golden hour, sunset, dusk, night. Click: let the day pass
    k1  pan along the coast (clouds drift by slower, the sun stays put). Click: cruise
    k2  horizon height. Click: mirror
    k3  colour story, continuously: cobalt, Miami, coral, citrus, lagoon. Click: album frame
"""
import functools
import math
import random

import numpy as np

from .. import draw
from ..draw import N
from ..runtime import Demo

TILE = 128                  # world px per lot
MARGIN = 48                 # palms reach this far past their lot
ROAD = N - 27               # the coast road's top edge, the same everywhere so it joins up
CLOUD_PARALLAX = 0.35
STAR_PARALLAX = 0.05
CRUISE = 14.0               # px/s when cruising

# Time of day: keyed lighting, blended between keys.
#   top/hor  sky at the zenith and at the horizon
#   tint     multiplies every lit surface (white walls go gold, then rose)
#   shadow   the colour of shade
#   sil      how far foreground objects go to silhouette
#   bands    how much the sky posterises into flat bands
KEYS = [
    (0.00, dict(top=(.04, .20, .62), hor=(.55, .82, .95), sea=(.02, .26, .62), tint=(1.0, 1.0, 1.0),
                shadow=(.45, .58, .82), sun=(1.0, 1.0, .9), sil=0.0, night=0.0, bands=0.0)),
    (0.35, dict(top=(.06, .24, .66), hor=(.72, .88, .96), sea=(.03, .30, .60), tint=(1.0, .97, .9),
                shadow=(.40, .50, .78), sun=(1.0, .95, .7), sil=0.0, night=0.0, bands=0.0)),
    (0.60, dict(top=(.14, .24, .60), hor=(1.0, .76, .46), sea=(.10, .26, .52), tint=(1.0, .83, .62),
                shadow=(.38, .34, .62), sun=(1.0, .78, .3), sil=0.25, night=0.0, bands=0.5)),
    (0.78, dict(top=(.24, .14, .46), hor=(1.0, .46, .34), sea=(.20, .15, .40), tint=(.92, .56, .5),
                shadow=(.26, .15, .36), sun=(1.0, .52, .2), sil=0.8, night=0.0, bands=1.0)),
    (0.90, dict(top=(.05, .05, .25), hor=(.55, .26, .50), sea=(.05, .06, .22), tint=(.42, .36, .56),
                shadow=(.10, .08, .26), sun=(1.0, .4, .3), sil=1.0, night=0.5, bands=0.7)),
    (1.00, dict(top=(.00, .02, .10), hor=(.08, .12, .30), sea=(.00, .03, .13), tint=(.26, .30, .46),
                shadow=(.05, .05, .16), sun=(1.0, .4, .3), sil=1.0, night=1.0, bands=0.0)),
]

# Colour stories, blended continuously round a loop. Each turns the hue of the sky,
# sea, sun and pool (degrees, in YIQ, so brightness holds) and adds saturation; sand,
# palms and white walls keep their own colours. A positive turn takes a noon sky
# towards teal and a sunset towards pink; a negative one, violet skies and gold.
GRADES = [("cobalt", 0, 1.08), ("lagoon", 30, 1.16), ("vivid", 0, 1.3), ("violet", -32, 1.16)]
_TO_YIQ = np.array([[.299, .587, .114], [.596, -.274, -.322], [.211, -.523, .312]], np.float32)
_FROM_YIQ = np.linalg.inv(_TO_YIQ).astype(np.float32)

CAR_COLOURS = [(.86, .10, .16), (.95, .95, .92), (.98, .80, .10), (.20, .75, .75)]
WALLS = [(.97, .97, .95), (1.0, .86, .86), (.98, .94, .84), (.86, .93, 1.0)]
WORDS_A = ["SUMMER", "BLUE", "SEASIDE", "POOLSIDE", "SUNSET", "WEEKEND", "PACIFIC", "HOLIDAY",
           "CRUISE", "MIDNIGHT", "SURF", "PALM", "COAST", "TROPIC"]
WORDS_B = ["BREEZE", "DRIVE", "PARADISE", "CITY", "LOUNGE", "DREAMS", "SIDE", "HOTEL", "CLUB",
           "ROMANCE", "LIGHTS", "MOTEL", "AVENUE", "RESORT"]


def light(t):
    """The lighting at time t (0 noon .. 1 night), blended between KEYS."""
    for (t0, a), (t1, b) in zip(KEYS, KEYS[1:]):
        if t <= t1:
            f = (t - t0) / (t1 - t0)
            return {k: (np.array(a[k], np.float32) * (1 - f) + np.array(b[k], np.float32) * f)
                    if isinstance(a[k], tuple) else a[k] * (1 - f) + b[k] * f for k in a}
    return {k: np.array(v, np.float32) if isinstance(v, tuple) else v for k, v in KEYS[-1][1].items()}


def grade_params(g):
    """(hue turn in degrees, saturation) at g in [0, 1), blended round the loop of GRADES."""
    n = len(GRADES)
    x = (g % 1.0) * n
    i = int(x)
    f = x - i
    f = f * f * (3 - 2 * f)                     # ease through each story
    a, b = GRADES[i % n], GRADES[(i + 1) % n]
    return a[1] * (1 - f) + b[1] * f, a[2] * (1 - f) + b[2] * f


def regrade(rgb, rot, sat):
    """Turn hue by rot degrees and scale saturation, keeping brightness (YIQ)."""
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    m = _FROM_YIQ @ np.array([[1, 0, 0], [0, c * sat, -s * sat], [0, s * sat, c * sat]], np.float32) @ _TO_YIQ
    return np.clip(np.asarray(rgb, np.float32) @ m.T, 0, 1)


def mix(a, b, f):
    return np.asarray(a, np.float32) * (1 - f) + np.asarray(b, np.float32) * f


def _rng(*key):
    return random.Random(":".join(str(k) for k in key))


def _cloud_sprite(w, seed):
    """A flat-bottomed cumulus: (alpha mask, shadow mask), a bump of puffs, tallest in the middle."""
    r = random.Random(seed)
    k = r.randint(4, 6)
    puffs = []
    for i in range(k):
        rad = w / k * 0.75 * (1 + 0.8 * math.sin(math.pi * (i + 0.5) / k)) * r.uniform(0.85, 1.1)
        puffs.append(((i + 0.5) * w / k + r.uniform(-2, 2), rad))
    big = max(rad for _, rad in puffs)
    pad = big * 1.2 + 2                         # room for the end puffs, so no edge gets cut off
    h = int(big * 1.6) + 3
    W = int(w + 2 * pad)
    yy, xx = np.mgrid[0:h, 0:W].astype(np.float32)
    base = h - 1
    m = np.zeros((h, W), bool)
    for cx, rad in puffs:
        m |= ((xx - cx - pad) / (rad * 1.15)) ** 2 + ((yy - (base - rad * 0.55)) / rad) ** 2 <= 1
    m &= yy <= base
    cols = np.nonzero(m.any(0))[0]
    m = m[:, cols[0]:cols[-1] + 1]
    # one flat band of shade along the underside, its top edge scalloped like the puffs
    yy = yy[:, :m.shape[1]]
    top = m.argmax(0)
    depth = (base - top) * 0.42 + 1.5 * np.sin(np.arange(m.shape[1]) * (k * math.pi / w) + r.uniform(0, 6))
    return m, m & (yy > base - depth[None, :])


class World:
    """The coast, lot by lot: everything is a function of (seed, lot index)."""

    def __init__(self, seed):
        self.seed = seed

    @functools.lru_cache(maxsize=4096)
    def kind(self, i):
        # Lots come in runs of two, so a stretch of pools or beach goes on for a while,
        # and every three runs hold one of each kind, in a shuffled order.
        run = i // 2
        order = ["pool", "beach", "drive"]
        _rng(self.seed, "order", run // 3).shuffle(order)
        return order[run % 3]

    @functools.lru_cache(maxsize=4096)
    def sea_depth(self, i):
        lo, hi = {"pool": (8, 14), "beach": (18, 26), "drive": (10, 16)}[self.kind(i)]
        return _rng(self.seed, "depth", i).uniform(lo, hi)

    @functools.lru_cache(maxsize=256)
    def depth_profile(self, i):
        """Sea depth for each column of lot i, eased between lot centres so the shore flows."""
        c = (i * TILE + np.arange(TILE) + 0.5) / TILE - 0.5      # in lot-centre units
        j = np.floor(c).astype(int)
        f = c - j
        f = f * f * (3 - 2 * f)
        d0 = np.array([self.sea_depth(k) for k in j], np.float32)
        d1 = np.array([self.sea_depth(k + 1) for k in j], np.float32)
        return d0 * (1 - f) + d1 * f

    @functools.lru_cache(maxsize=256)
    def lot(self, i):
        r = _rng(self.seed, "lot", i)
        kind = self.kind(i)
        s = dict(kind=kind)
        s["building"] = None
        if kind != "beach" and r.random() < 0.7:
            w = r.uniform(30, 50)
            sw = r.uniform(5, 9)
            s["building"] = dict(x=r.uniform(sw + 4, TILE - w - sw - 4), w=w, h=r.uniform(26, 58), side_w=sw,
                                 style=r.choice(["bands", "grid"]), wall=r.choice(WALLS))
        s["palms"] = [dict(x=r.uniform(4, TILE - 4), dy=r.uniform(3, 10), h=r.uniform(46, 74),
                           lean=r.uniform(-0.35, 0.35), n=r.randint(7, 9), size=r.uniform(15, 22),
                           phase=r.uniform(0, 6.3), seed=r.random())
                      for _ in range(r.choice([0, 1, 1, 2, 2, 3]))]
        if kind == "pool" and r.random() < 0.35:
            kind = s["kind"] = "deck"                       # a sun deck: no pool, umbrellas instead
        if kind == "pool":
            s["pool"] = dict(cx=r.uniform(56, 72), tw=r.uniform(46, 70), bw=r.uniform(84, 108), top=r.uniform(8, 14),
                             ladder=r.choice([-1, 1]))
        if kind in ("beach", "deck"):
            s["umbrellas"] = [dict(x=x, colour=r.choice([(.9, .15, .2), (.15, .35, .85), (1, .6, .1)]), dy=r.uniform(3, 12))
                              for x in sorted(r.sample(range(16, TILE - 16, 14), r.randint(1, 3)))]
        if kind == "drive":
            s["car"] = dict(x=r.uniform(8, TILE - 48), colour=r.choice(CAR_COLOURS), flip=r.random() < 0.5) \
                if r.random() < 0.7 else None
        s["title"] = f"{r.choice(WORDS_A)} {r.choice(WORDS_B)}"
        return s


class Resort(Demo):
    name = "Resort"
    blurb = "An endless city-pop coast after Hiroshi Nagai. k0 time of day (click: let it pass), k1 pan (click: cruise), k2 horizon (click: mirror), k3 colour story (click: album frame)."

    def __init__(self, rt):
        super().__init__(rt)
        self.world = World(1)
        self.t = 0.2
        self.horizon = 60
        self.grade = 0.0
        self.pan = self.pan_target = 0.0
        self.mirror = False
        self.frame = False
        self.auto_day = False
        self.cruise = False
        self.t_grade = -10.0
        self.lots = {}              # (i, look) -> rendered lot
        self.palm_shapes = {}       # (i, horizon) -> palm part maps
        self.cloud_sprites = {}
        self.sun_x = 38.0
        self.look = None

    # ---- controls

    def turn(self, k, d):
        if k == 0:
            self.t = min(1.0, max(0.0, self.t + self.rt.accel(0, d, top=3) / 48))
            self.auto_day = False
        elif k == 1:
            self.pan_target += self.rt.accel(1, d, top=8) * 3
        elif k == 2:
            self.horizon = min(84, max(36, self.horizon - 2 * d))
        elif k == 3:
            self.grade = (self.grade + self.rt.accel(3, d, top=3) / 60) % 1.0
            self.t_grade = self.rt.t

    def release(self, k, click):
        if not click:
            return
        if k == 0:
            self.auto_day = not self.auto_day
        elif k == 1:
            self.cruise = not self.cruise
        elif k == 2:
            self.mirror = not self.mirror
        elif k == 3:
            self.frame = not self.frame

    def step(self, dt):
        if self.auto_day:                           # a day in about a minute, then morning again
            self.t += dt / 50
            if self.t > 1.0:
                self.t = 0.0
        if self.cruise:
            self.pan_target += CRUISE * dt
        self.pan += (self.pan_target - self.pan) * (1 - math.exp(-10 * dt))

    # ---- the look: lighting and colour story, quantised so caches can key on it

    def _lighting(self):
        look = (round(self.t * 200), self.horizon, round(self.grade * 120) % 120)
        if self.look != look:
            self.look = look
            L = light(self.t)
            rot, sat = grade_params(self.grade)
            for k in ("top", "hor", "sea", "sun", "shadow"):
                L[k] = regrade(L[k], rot, sat)
            self.L, self.rot, self.sat = L, rot, sat
            self.lots = {k: v for k, v in self.lots.items() if k[1] == look}
        return self.L

    # ---- one lot's static picture: sea, ground, building, pool, umbrellas, road, car

    def _lot(self, i):
        key = (i, self.look)
        if key in self.lots:
            return self.lots[key]
        w, L, H = self.world, self.L, self.horizon
        s = w.lot(i)
        kind = s["kind"]
        ground_kind = w.kind(i)                             # a deck is a pool lot without the pool
        D = (H + w.depth_profile(i)).astype(int)            # the shore, per column
        tint, shadow, sil = L["tint"], L["shadow"], L["sil"]
        sil_col = L["top"] * 0.3 + L["shadow"] * 0.2
        rows = np.arange(N)[:, None]
        cols = np.arange(TILE)
        wx = i * TILE + cols                                # world x, for patterns that must join up

        front = np.zeros((N, TILE, 3), np.float32)
        occ = np.zeros((N, TILE), bool)
        # sea, lighter towards the shore, and the horizon line
        f = np.clip((rows - H) / np.maximum(1, D - H)[None, :], 0, 1)
        front[:] = mix(L["sea"], L["sea"] * 1.25 + 0.03, f[..., None])
        front[H] = mix(L["sea"], L["hor"], 0.45)

        # ground: this lot's kind, except left of a diagonal path edge where the
        # previous lot's kind carries on, so the two meet along a curb
        def ground(kd, mask):
            if kd == "pool":
                g = np.broadcast_to((.93, .90, .82) * tint, (N, TILE, 3)).copy()
                g[:, wx % 8 == 0] *= 0.93                   # tile joints, continuous in world x
                g[(rows[:, 0] - H) % 6 == 3] *= 0.93
            elif kd == "beach":
                g = np.broadcast_to((.95, .82, .60) * tint, (N, TILE, 3)).copy()
            else:
                g = np.broadcast_to((.24, .52, .26) * tint, (N, TILE, 3)).copy()
                g[ROAD:ROAD + 16] = (.34, .36, .42) * tint
                g[ROAD] = g[ROAD + 15] = (.9, .9, .88) * tint
                g[ROAD + 7:ROAD + 9, (wx % 12) < 6] = (.95, .9, .6) * tint
            front[mask] = g[mask]

        land = rows >= D[None, :]
        prev = w.kind(i - 1)
        edge = (rows - D[None, :]) * 0.35 + 2               # the path edge leans across the first columns
        left = land & (cols[None, :] < edge)
        if prev != ground_kind:
            ground(ground_kind, land & ~left)
            ground(prev, left)
            front[land & (np.abs(cols[None, :] - edge) < 1.2)] = (.96, .96, .93) * tint
        else:
            ground(ground_kind, land)
        foam = mix((.97, .97, .95) * tint, L["sea"], 0.15)
        for c in range(TILE):                               # foam along a sandy shore
            if (prev if c < 2 else ground_kind) == "beach":
                y = D[c] + int(1.2 * math.sin(wx[c] * 0.21))
                front[y:y + 2, c] = foam

        b = s["building"]
        if b:
            x0, x1 = int(b["x"]), int(b["x"] + b["w"])
            base = int(D[x0:x1].min())
            top = int(base - b["h"])
            wall = mix(np.array(b["wall"]) * tint, sil_col, sil * 0.7)
            face = mix(shadow, sil_col, sil * 0.7)
            sw = b["side_w"]
            # the sun stays on the left, so every block shows its shaded right face
            draw.poly(front, [(x1, top), (x1 + sw, top - sw * 0.45), (x1 + sw, base - sw * 0.45), (x1, base)],
                      face, mask_out=occ)
            front[top:base, x0:x1] = wall
            occ[top:base, x0:x1] = True
            front[top, x0:x1] = mix(wall, (1, 1, 1), 0.3)                 # the roof's edge
            glass = mix(mix(L["hor"], L["top"], 0.55) * 0.8, sil_col, sil * 0.5)
            windows = []
            if b["style"] == "bands":
                for wy in range(top + 5, base - 5, 7):
                    front[wy:wy + 3, x0 + 3:x1 - 3] = glass
                    front[wy + 3, x0 + 2:x1 - 2] = wall * 1.05                # balcony lip
                    windows += [(wy, c) for c in range(x0 + 3, x1 - 6, 6)]
            else:
                for wy in range(top + 4, base - 5, 7):
                    for c in range(x0 + 3, x1 - 5, 6):
                        front[wy:wy + 4, c:c + 4] = glass
                        windows.append((wy, c))
            if L["night"] > 0:
                r = _rng(w.seed, "windows", i)
                for wy, c in windows:
                    if r.random() < 0.45:
                        front[wy:wy + 3, c:c + 4] = mix(front[wy:wy + 3, c:c + 4], (1, .82, .4), L["night"])

        pool_mask = np.zeros((N, TILE), bool)
        if kind == "pool":
            p = s["pool"]
            cx, tw, bw = p["cx"], p["tw"], p["bw"]
            py = int(D[int(cx)] + p["top"])
            coping = [(cx - tw / 2 - 2, py - 2), (cx + tw / 2 + 2, py - 2), (cx + bw / 2 + 3, N + 8), (cx - bw / 2 - 3, N + 8)]
            draw.poly(front, coping, mix((.98, .98, .96) * tint, sil_col, sil * 0.3))
            water = [(cx - tw / 2, py), (cx + tw / 2, py), (cx + bw / 2, N + 8), (cx - bw / 2, N + 8)]
            draw.poly(np.zeros((N, TILE, 3), np.float32), water, (0, 0, 0), mask_out=pool_mask)
            g = np.clip((rows - py) / max(1, N - py), 0, 1)[..., None]
            day = mix((.04, .55, .72), (.25, .86, .86), g) * mix(tint, (1, 1, 1), 0.5)
            night = mix((.10, .55, .85), (.35, .95, 1.0), g)
            # pools follow the colour story only a third of the way: a full turn takes turquoise to green
            pool = np.broadcast_to(regrade(mix(day, night, L["night"]), self.rot * 0.35, self.sat), (N, TILE, 3))
            front[pool_mask] = pool[pool_mask]
            chrome = mix((.85, .87, .9) * tint, sil_col, sil * 0.5)
            lx = cx + p["ladder"] * (tw / 2 - 8)
            for rail in (lx - 2, lx + 2):
                front[py - 6:py + 7, int(rail)] = chrome
            for ry in (py - 1, py + 3):
                front[ry, int(lx - 2):int(lx + 3)] = chrome

        if kind in ("beach", "deck"):
            for u in s["umbrellas"]:
                ux = u["x"]
                top = int(D[int(ux)] + u["dy"])
                front[top:top + 18, int(ux)] = mix((.9, .9, .88) * tint, sil_col, sil * 0.5)
                can = (((cols[None, :] - ux) / 13) ** 2 + ((rows - top) / 7) ** 2 <= 1) & (rows <= top)
                stripe = np.broadcast_to(np.floor((cols[None, :] - ux + 13) / 4.3) % 2 == 0, can.shape)
                front[can & stripe] = mix(np.array(u["colour"]) * tint, sil_col, sil * 0.6)
                front[can & ~stripe] = mix((.97, .97, .95) * tint, sil_col, sil * 0.6)
                occ |= can

        if kind == "drive" and s["car"]:
            self._car(front, s["car"], L, sil_col)

        lot = dict(front=front, fm=(rows >= H) | occ, sea_vis=(rows > H) & ~land & ~occ,
                   pool=pool_mask, D=D, title=s["title"])
        self.lots[key] = lot
        return lot

    def _car(self, front, c, L, sil_col):
        """A coupe in profile, facing right unless flipped: long hood, raked windshield, short tail."""
        tint, sil = L["tint"], L["sil"]
        base = ROAD + 12
        # (x, y) from the rear bumper, y up as negative: tail, rear deck, near-upright back
        # window, roof, raked windshield down to the hood, nose
        pts = [(0, -2), (1, -6), (10, -7), (13, -7), (15, -11.5), (24, -11.5), (29, -7.5), (38, -6.5),
               (40, -4), (40, 0), (0, 0)]
        flip = c["flip"]

        def X(px):
            return c["x"] + (40 - px if flip else px)
        body = mix(np.array(c["colour"]) * tint, sil_col, sil * 0.6)
        draw.poly(front, [(X(px), base + py) for px, py in pts], body)
        glass = mix(L["hor"] * 0.9, sil_col, sil * 0.5)
        draw.poly(front, [(X(px), base + py) for px, py in [(16, -10.5), (23, -10.5), (27, -7.5), (15.5, -7.5)]], glass)
        chrome = mix((.9, .92, .95) * tint, sil_col, sil * 0.5)
        x0, x1 = sorted((X(1), X(39)))
        front[base - 4, int(x0):int(x1)] = chrome
        for wx in (8, 32):
            draw.disc(front, X(wx), base, 3.6, (.06, .06, .08), soft=0.3, op="over")
            draw.disc(front, X(wx), base, 1.4, chrome, soft=0.3, op="over")
        if L["night"] > 0.2:                        # headlights reach down the road; tail lights glow
            nose, tail, ahead = X(40), X(0), (-1 if flip else 1)
            beam = [(nose, base - 6), (nose + ahead * 34, base - 9), (nose + ahead * 34, base + 2), (nose, base - 4)]
            glow = np.zeros(front.shape[:2], bool)
            draw.poly(np.zeros_like(front), beam, (0, 0, 0), mask_out=glow)
            front[glow] = mix(front[glow], (1, .95, .7), 0.45 * L["night"])
            hx = int(nose) - (0 if flip else 1)
            front[base - 6:base - 4, max(0, hx):hx + 2] = (1, .97, .8)
            tx = int(tail) - (1 if flip else 0)
            front[base - 6:base - 4, max(0, tx):tx + 2] = (1, .1, .1)

    # ---- palms: drawn once per lot and look as sprites; the sway is a shear, every frame

    POSES = 3                   # sway poses either side of rest: 7 in all

    def _palms_of(self, i):
        """The palms of lot i, placed on its shore; their sway poses are drawn on demand.
        Shapes don't change with the light, so this is cached on the horizon alone."""
        key = (i, self.horizon)
        if key in self.palm_shapes:
            return self.palm_shapes[key]
        if len(self.palm_shapes) > 32:
            self.palm_shapes.clear()
        D = (self.horizon + self.world.depth_profile(i)).astype(int)
        palms = []
        for p in sorted(self.world.lot(i)["palms"], key=lambda p: p["dy"]):
            by = D[int(min(TILE - 1, p["x"]))] + p["dy"]
            palms.append(dict(p=p, lot=i, by=by, h=min(p["h"], by - 6), poses={}))
        self.palm_shapes[key] = palms
        return palms

    def _palm_pose(self, palm, pose):
        """One sway pose of a palm, as a map of parts: -1 none, 0 trunk shade, 1 trunk lit,
        2-4 greens, 5 coconut. A pose bends the whole tree: the trunk leans a little further,
        the crown follows it and the fronds turn and lift with the wind."""
        if pose in palm["poses"]:
            return palm["poses"][pose]
        p, by, h = palm["p"], palm["by"], palm["h"]
        W = TILE + 2 * MARGIN
        part = np.full((N, W), -1, np.int8)
        bx = p["x"] + MARGIN
        lean = p["lean"] + pose * 0.017                    # about a pixel at the crown per pose
        cx, cy = bx + lean * h, by - h + abs(pose) * 0.15
        ss = np.linspace(0, 1, 12)
        ctrl = (bx + lean * h * 0.15, by - h * 0.6)
        px = (1 - ss) ** 2 * bx + 2 * (1 - ss) * ss * ctrl[0] + ss ** 2 * cx
        py = (1 - ss) ** 2 * by + 2 * (1 - ss) * ss * ctrl[1] + ss ** 2 * cy
        wdt = 2.2 - 1.0 * ss
        draw.poly(part, list(zip(px - wdt, py)) + list(zip(px + wdt, py))[::-1], 0)
        draw.poly(part, list(zip(px - wdt * 0.9, py)) + list(zip(px, py))[::-1], 1)   # sunlit side
        r = random.Random(p["seed"])
        n = p["n"]
        for k in range(n):
            th = math.radians(-18 + 216 * k / (n - 1) + r.uniform(-8, 8)) - pose * 0.045
            dx, dy = math.cos(th), -math.sin(th)
            ln = p["size"] * r.uniform(0.85, 1.1)
            # fronds on the downwind side stream out flatter; upwind ones droop more
            droop = (0.75 if abs(dx) > 0.5 else 0.35) * (1 - 0.06 * pose * (1 if dx > 0 else -1))
            s_ = np.linspace(0, 1, 11)
            fx = cx + dx * ln * s_
            fy = cy + dy * ln * s_ + droop * ln * s_ ** 2
            nx, ny = -(dy + 2 * droop * s_), np.full_like(s_, dx)
            nl = np.hypot(nx, ny) + 1e-6
            nx, ny = nx / nl, ny / nl
            wd = p["size"] * 0.17 * np.sin(np.pi * s_) ** 0.7 * (0.7 + 0.3 * (np.arange(11) % 2))
            draw.poly(part, list(zip(fx + nx * wd, fy + ny * wd)) + list(zip(fx - nx * wd, fy - ny * wd))[::-1],
                      2 + (k + (1 if dy < -0.3 else 0)) % 3)
        yy, xx = np.ogrid[0:N, 0:W]
        for k in range(3):
            part[(xx - (cx + (k - 1) * 1.8)) ** 2 + (yy - (cy + 1.5)) ** 2 <= 1.6] = 5
        ys, xs = np.nonzero(part >= 0)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        out = dict(part=part[y0:y1, x0:x1].copy(), x=palm["lot"] * TILE - MARGIN + x0, y=int(y0))
        palm["poses"][pose] = out
        return out

    def _palm_colours(self):
        """The palette for palm parts under the current light (indexed by part)."""
        L = self.L
        sil_col = L["top"] * 0.3 + L["shadow"] * 0.2
        sil = L["sil"]
        cols = [(.45, .32, .22), (.72, .55, .36), (.06, .32, .16), (.12, .48, .22), (.20, .58, .26)]
        pal = [mix(np.array(c) * L["tint"], sil_col, sil) for c in cols] + [mix((.35, .22, .1), sil_col, sil)]
        return np.array(pal, np.float32)

    def _draw_palms(self, img, pan, i0):
        t = self.rt.t
        pal = self._palm_colours()
        for i in range(i0 - 1, i0 + 3):
            for palm in self._palms_of(i):
                if not -MARGIN - TILE < i * TILE - pan < N + MARGIN:
                    continue
                # a slow sway with a gentler gust on top, stepped through whole poses
                ph = palm["p"]["phase"]
                wind = 0.75 * math.sin(t * 0.9 + ph) + 0.25 * math.sin(t * 2.3 + ph * 1.7)
                sp = self._palm_pose(palm, int(round(wind * self.POSES)))
                h, w = sp["part"].shape
                sx = sp["x"] - pan
                a, b = max(0, -sx), min(w, N - sx)
                if a >= b:
                    continue
                part = sp["part"][:, a:b]
                m = part >= 0
                region = img[sp["y"]:sp["y"] + h, sx + a:sx + b]
                region[m] = pal[part[m]]

    # ---- per frame

    def render(self):
        L = self._lighting()
        t = self.rt.t
        H = self.horizon
        pan = int(round(self.pan))

        # sky: a vertical gradient that posterises into bands towards sunset
        f = np.clip(np.arange(N, dtype=np.float32) / max(1, H), 0, 1) ** 0.85
        f = f * (1 - L["bands"]) + np.floor(f * 9) / 9 * L["bands"]
        img = np.repeat(mix(L["top"], L["hor"], f[:, None])[:, None, :], N, axis=1)
        if L["night"] > 0:
            r = _rng(self.world.seed, "stars")
            for _ in range(60):
                x, fy, b = r.uniform(0, 4 * N), r.random(), r.random()
                xx = int(x - pan * STAR_PARALLAX) % (4 * N)
                if xx < N:
                    yy = int(fy * (H - 6))
                    img[yy, xx] = np.maximum(img[yy, xx], L["night"] * (0.4 + 0.6 * b))
        # the sun is far away: it stays put while we pan
        e = 1 - self.t / 0.8
        rad = 6 + 7 * (1 - max(0.0, e))
        sy = H - e * H * 1.15 + rad * 0.2
        sx = self.sun_x
        if sy + rad > 0 and self.t < 0.9:
            d = np.hypot(draw.X - sx, draw.Y - sy)
            glow = np.clip(1 - d / (rad * 3.2), 0, 1) ** 2 * 0.35
            img = img * (1 - glow[..., None]) + L["sun"] * glow[..., None]
            img[d <= rad] = L["sun"]
        # clouds, at a third of the pan speed, drifting
        lit = mix(mix((.98, .98, .97) * L["tint"], L["sun"], 0.15 * L["bands"]), L["top"] * 0.6, L["night"] * 0.8)
        shade = mix(mix(L["shadow"], L["hor"], 0.25), L["top"] * 0.4, L["night"] * 0.8)
        cx0 = pan * CLOUD_PARALLAX + t * 1.2
        span = 170
        for j in range(int(cx0 // span) - 1, int((cx0 + N) // span) + 1):
            r = _rng(self.world.seed, "clouds", j)
            for c in range(r.choice([0, 1, 1, 2])):
                w, up, off, sd = r.uniform(26, 56), r.uniform(4, 22), r.uniform(0, span), r.random()
                if (j, c) not in self.cloud_sprites:
                    if len(self.cloud_sprites) > 40:
                        self.cloud_sprites.clear()
                    self.cloud_sprites[(j, c)] = _cloud_sprite(w, sd)
                m, sh = self.cloud_sprites[(j, c)]
                x = int(j * span + off - cx0)
                yb = int(H - up - m.shape[0])
                for mask, col in ((m & ~sh, lit), (sh, shade)):
                    yy, xx = np.nonzero(mask)
                    yy, xx = yy + yb, xx + x
                    ok = (xx >= 0) & (xx < N) & (yy >= 0) & (yy < H)
                    img[yy[ok], xx[ok]] = col

        # the ground and everything on it, from the two lots in view
        i0, off = pan // TILE, pan % TILE
        parts = [(self._lot(i0), off, TILE), (self._lot(i0 + 1), 0, off)]

        def view(key):
            return np.concatenate([p[key][:, a:b] if p[key].ndim > 1 else p[key][a:b] for p, a, b in parts], axis=1
                                  if parts[0][0][key].ndim > 1 else 0)
        front, fm, sea_vis, pool, D_view = view("front"), view("fm"), view("sea_vis"), view("pool"), view("D")
        img[fm] = front[fm]

        # glints on the sea, and the sun's path across it near sunset
        r = np.random.default_rng(int(t * 6))
        shore = int(D_view.max())
        gx, gy = r.integers(0, N, 30), r.integers(H + 1, max(H + 2, shore), 30)
        for x, yy in zip(gx, gy):
            if sea_vis[yy, x]:
                img[yy, x:min(N, x + 3)] = mix(L["sea"], L["hor"] + 0.15, 0.7)
        if 0.45 < self.t < 0.9:
            for yy in range(H + 1, shore):
                wob = int(2 * math.sin(yy * 1.7 + t * 5))
                half = int(rad * (0.4 + 0.6 * (yy - H) / max(1, shore - H)))
                x0, x1 = max(0, int(sx) - half + wob), min(N, int(sx) + half + wob)
                if (yy + int(t * 8)) % 2 and x1 > x0:
                    row = sea_vis[yy, x0:x1]
                    img[yy, x0:x1][row] = mix(img[yy, x0:x1][row], L["sun"], 0.8)
        # caustics on the pool floor, in world x so they slide with the pool
        if pool.any():
            y0 = int(np.argmax(pool.any(1)))
            X, Y, pm = draw.X[y0:] + pan, draw.Y[y0:], pool[y0:]
            c = (np.abs(np.sin(X * 0.33 + 1.8 * np.sin(Y * 0.22 + t * 1.3))
                        + np.sin(Y * 0.41 - t * 1.1 + np.sin(X * 0.17))) < 0.22) & pm
            sub = img[y0:]
            sub[c] = mix(sub[c], (.85, 1.0, 1.0), 0.45 + 0.3 * L["night"])

        # palms, from the lots in view and their neighbours (fronds reach across)
        self._draw_palms(img, pan, i0)

        img = np.clip(img, 0, 1)
        if self.mirror:
            img = img[:, ::-1]
        if self.frame:
            img = self._album(img, parts[0][0]["title"])
        elif self.rt.t - self.t_grade < 1.2:
            name = GRADES[int(round((self.grade % 1.0) * len(GRADES))) % len(GRADES)][0]
            draw.text(img, name, N - 2 - draw.text_width(name), 1, (1, 1, 1))
        return img

    def _album(self, img, title):
        out = np.empty_like(img)
        out[:] = (.97, .96, .93)
        out[5:104, 5:123] = img[5:104, 5:123]
        draw.text(out, title, 6, 106, (.08, .12, .35))
        draw.text(out, "PATTERNFLOOD", 6, 116, (.45, .45, .5))
        return out

    def lights(self):
        L = self.L if self.look else light(self.t)
        return [tuple(float(v) for v in L["hor"]),
                (1, .9, .5) if self.cruise else (.3, .3, .3),
                tuple(float(v) for v in L["sea"] * 1.4),
                tuple(float(v) for v in L["top"] * 1.5)]
