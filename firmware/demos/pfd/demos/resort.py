"""Resort: city-pop scenery in the manner of Hiroshi Nagai's illustrations.

Flat, hard-edged colour and no texture: cobalt skies fading to a pale horizon,
big flat-bottomed cumulus, a turquoise pool with white coping, palms, white
modernist blocks with crisp blue shadow faces, a convertible on the coast
road, the sun going down in flat bands. Every scene is generated from a seed;
nothing is copied from a real picture.

    k0  time of day: noon, golden hour, sunset, dusk, night. Click: let the day pass
    k1  a new scene each detent; turn back to return to one. Click: a random scene
    k2  horizon height. Click: mirror the composition
    k3  palette: classic, pastel, tropical, blue print. Click: album-cover frame
"""
import math
import random

import numpy as np

from .. import draw
from ..draw import N
from ..runtime import Demo

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
PALETTES = ["classic", "pastel", "tropical", "print"]
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


def mix(a, b, f):
    return np.asarray(a, np.float32) * (1 - f) + np.asarray(b, np.float32) * f


def compose(seed):
    """A scene: what's in it and where, independent of time, horizon and mirroring."""
    r = random.Random(seed)
    kind = r.choices(["pool", "beach", "drive"], [0.5, 0.25, 0.25])[0]
    s = dict(kind=kind, seed=seed)
    s["sea_depth"] = {"pool": r.randint(8, 14), "beach": r.randint(20, 30), "drive": r.randint(10, 16)}[kind]
    s["sun_x"] = r.choice([r.uniform(18, 44), r.uniform(84, 110)])
    s["clouds"] = [dict(x=r.uniform(-10, 130), up=r.uniform(4, 22), w=r.uniform(26, 56), seed=r.random())
                   for _ in range(r.choice([0, 1, 1, 2, 2, 3]))]
    side = r.choice([-1, 1])                       # which side the building and palms favour
    s["building"] = None
    if kind != "beach" and r.random() < 0.75:
        w = r.uniform(30, 52)
        x = r.uniform(4, 30) if side < 0 else r.uniform(N - 34 - w, N - 4 - w)
        s["building"] = dict(x=x, w=w, h=r.uniform(26, 58), side_w=r.uniform(5, 10),
                             style=r.choice(["bands", "grid"]), wall=r.choice(WALLS), lit=r.random())
    palms = []
    for i in range(r.choice([1, 2, 2, 3])):
        x = r.uniform(8, 50) if (i % 2 == 0) == (side > 0) else r.uniform(78, 120)
        palms.append(dict(x=x, dy=r.uniform(3, 10), h=r.uniform(46, 74), lean=r.uniform(-0.35, 0.35),
                          n=r.randint(7, 9), size=r.uniform(15, 22), phase=r.uniform(0, 6.3), seed=r.random()))
    s["palms"] = palms
    if kind == "pool":
        s["pool"] = dict(cx=r.uniform(44, 84), tw=r.uniform(50, 80), bw=r.uniform(90, 130), top=r.uniform(8, 16),
                         ladder=r.choice([-1, 1]))
    elif kind == "beach":
        s["umbrella"] = dict(x=r.uniform(30, 98), colour=r.choice([(.9, .15, .2), (.15, .35, .85), (1, .6, .1)]))
    else:
        s["road"] = r.uniform(96, 108)
        s["car"] = dict(x=r.uniform(20, 70), colour=r.choice(CAR_COLOURS), flip=r.random() < 0.5)
    s["stars"] = [(r.uniform(0, N), r.uniform(0, 1), r.random()) for _ in range(40)]
    s["title"] = f"{r.choice(WORDS_A)} {r.choice(WORDS_B)}"
    return s


def _cloud_sprite(w, seed):
    """A flat-bottomed cumulus: (alpha mask, shadow mask), a bump of puffs, tallest in the middle."""
    r = random.Random(seed)
    k = r.randint(4, 6)
    h = int(w * 0.55) + 2
    W = int(w) + 4
    yy, xx = np.mgrid[0:h, 0:W].astype(np.float32)
    base = h - 1
    m = np.zeros((h, W), bool)
    for i in range(k):
        cx = 2 + (i + 0.5) * w / k + r.uniform(-2, 2)
        rad = w / k * 0.75 * (1 + 0.8 * math.sin(math.pi * (i + 0.5) / k)) * r.uniform(0.85, 1.1)
        cy = base - rad * 0.55
        m |= ((xx - cx) / (rad * 1.15)) ** 2 + ((yy - cy) / rad) ** 2 <= 1
    m &= yy <= base
    # one flat band of shade along the underside, its top edge scalloped like the puffs
    top = m.argmax(0)                               # first cloud row per column
    depth = (base - top) * 0.42 + 1.5 * np.sin(np.arange(W) * (k * math.pi / w) + r.uniform(0, 6))
    shade = m & (yy > base - depth[None, :])
    return m, shade


class Resort(Demo):
    name = "Resort"
    blurb = "City-pop scenery after Hiroshi Nagai. k0 time of day (click: let it pass), k1 new scene, k2 horizon (click: mirror), k3 palette (click: album frame)."

    def __init__(self, rt):
        super().__init__(rt)
        self.seed = 1
        self.t = 0.2
        self.horizon = 60
        self.palette = 0
        self.mirror = False
        self.frame = False
        self.auto = False
        self.t_seed = -10.0
        self.key = None
        self._scene(self.seed)

    # ---- controls

    def _scene(self, seed):
        self.seed = seed
        self.scene = compose(seed)
        self.clouds = [(c, *_cloud_sprite(c["w"], c["seed"])) for c in self.scene["clouds"]]
        self.key = None
        self.t_seed = self.rt.t

    def turn(self, k, d):
        if k == 0:
            self.t = min(1.0, max(0.0, self.t + self.rt.accel(0, d, top=3) / 48))
            self.auto = False
        elif k == 1:
            self._scene(max(1, self.seed + (1 if d > 0 else -1)))
        elif k == 2:
            self.horizon = min(84, max(36, self.horizon - 2 * d))
        elif k == 3:
            self.palette = (self.palette + (1 if d > 0 else -1)) % len(PALETTES)

    def release(self, k, click):
        if not click:
            return
        if k == 0:
            self.auto = not self.auto
        elif k == 1:
            self._scene(random.randint(1, 99999))
        elif k == 2:
            self.mirror = not self.mirror
        elif k == 3:
            self.frame = not self.frame

    def step(self, dt):
        if self.auto:                               # a day in about a minute, then morning again
            self.t += dt / 50
            if self.t > 1.0:
                self.t = 0.0

    # ---- the static picture, rebuilt only when time, scene or horizon change

    def _base(self):
        key = (self.seed, round(self.t * 200), self.horizon)
        if key == self.key:
            return
        self.key = key
        s, L, H = self.scene, light(self.t), self.horizon
        D = H + s["sea_depth"]
        sil_col = L["top"] * 0.3 + L["shadow"] * 0.2
        self.L, self.D = L, D

        # back layer: sky, stars, sun
        y = np.arange(N, dtype=np.float32)
        f = np.clip(y / max(1, H), 0, 1) ** 0.85
        nb = 9
        f = f * (1 - L["bands"]) + np.floor(f * nb) / nb * L["bands"]
        back = mix(L["top"], L["hor"], f[:, None])[:, None, :].repeat(N, 1)
        if L["night"] > 0:
            for x, fy, b in s["stars"]:
                yy = int(fy * (H - 6))
                back[yy, int(x) % N] = np.maximum(back[yy, int(x) % N], L["night"] * (0.4 + 0.6 * b))
        e = 1 - self.t / 0.8
        rad = 6 + 7 * (1 - max(0.0, e))
        sy = H - e * H * 1.15 + rad * 0.2
        self.sun = (s["sun_x"], sy, rad)
        if sy + rad > 0 and self.t < 0.9:
            d = np.hypot(draw.X - s["sun_x"], draw.Y - sy)
            glow = np.clip(1 - d / (rad * 3.2), 0, 1) ** 2 * 0.35
            back = back * (1 - glow[..., None]) + L["sun"] * glow[..., None]
            back[d <= rad] = L["sun"]
        self.back = back.astype(np.float32)

        # front layer: sea, ground, building, pool, umbrella, road, car
        front = np.zeros((N, N, 3), np.float32)
        fm = np.zeros((N, N), bool)
        fm[H:] = True
        sea_rows = np.arange(H, D)
        front[H:D] = mix(L["sea"], L["sea"] * 1.25 + 0.03, ((sea_rows - H) / max(1, D - H))[:, None])[:, None, :]
        front[H] = mix(L["sea"], L["hor"], 0.45)                     # the horizon line
        tint, shadow = L["tint"], L["shadow"]
        if s["kind"] == "pool":
            deck = (.93, .90, .82) * tint
            front[D:] = deck
            front[D:, ::8] = deck * 0.93                            # tile joints
            front[D + 3::6] = deck * 0.93
        elif s["kind"] == "beach":
            front[D:] = (.95, .82, .60) * tint
            foam = D + (1.2 * np.sin(np.arange(N) * 0.21 + s["seed"] * 7)).astype(int)
            for x in range(N):
                front[foam[x]:foam[x] + 2, x] = mix((.97, .97, .95) * tint, L["sea"], 0.15)
        else:
            ry = int(s["road"])
            front[D:ry] = (.24, .52, .26) * tint
            front[ry:ry + 16] = (.34, .36, .42) * tint
            front[ry, :] = (.9, .9, .88) * tint
            front[ry + 15, :] = (.9, .9, .88) * tint
            front[ry + 7:ry + 9, (np.arange(N) % 12) < 6] = (.95, .9, .6) * tint
            front[ry + 16:] = (.24, .52, .26) * tint
        sil = L["sil"]
        occ = np.zeros((N, N), bool)                # things standing in front of the sea

        b = s["building"]
        self.windows = []
        if b:
            x0, x1, top = int(b["x"]), int(b["x"] + b["w"]), int(D - b["h"])
            light_from_left = s["sun_x"] < 64
            wall = mix(np.array(b["wall"]) * tint, sil_col, sil * 0.7)
            face = mix(shadow, sil_col, sil * 0.7)
            sw = b["side_w"]
            if light_from_left:
                pts = [(x1, top), (x1 + sw, top - sw * 0.45), (x1 + sw, D - sw * 0.45), (x1, D)]
            else:
                pts = [(x0, top), (x0 - sw, top - sw * 0.45), (x0 - sw, D - sw * 0.45), (x0, D)]
            draw.poly(front, pts, face, mask_out=occ)
            front[top:D, x0:x1] = wall
            occ[top:D, x0:x1] = True
            front[top:top + 1, x0:x1] = mix(wall, (1, 1, 1), 0.3)           # the roof's edge
            glass = mix(mix(L["hor"], L["top"], 0.55) * 0.8, sil_col, sil * 0.5)
            rng = random.Random(s["seed"] * 31 + 7)
            if b["style"] == "bands":
                for wy in range(top + 5, D - 5, 7):
                    front[wy:wy + 3, x0 + 3:x1 - 3] = glass
                    front[wy + 3, x0 + 2:x1 - 2] = wall * 1.05                # balcony lip
                    self.windows += [(wy, wx) for wx in range(x0 + 3, x1 - 6, 6)]
            else:
                for wy in range(top + 4, D - 5, 7):
                    for wx in range(x0 + 3, x1 - 5, 6):
                        front[wy:wy + 4, wx:wx + 4] = glass
                        self.windows.append((wy, wx))
            if L["night"] > 0:
                for wy, wx in self.windows:
                    if rng.random() < 0.45:
                        a = L["night"]
                        front[wy:wy + 3, wx:wx + 4] = mix(front[wy:wy + 3, wx:wx + 4], (1, .82, .4), a)

        self.pool_mask = np.zeros((N, N), bool)
        if s["kind"] == "pool":
            p = s["pool"]
            py = D + p["top"]
            cx, tw, bw = p["cx"], p["tw"], p["bw"]
            coping = [(cx - tw / 2 - 2, py - 2), (cx + tw / 2 + 2, py - 2), (cx + bw / 2 + 3, N + 8), (cx - bw / 2 - 3, N + 8)]
            draw.poly(front, coping, mix((.98, .98, .96) * tint, sil_col, sil * 0.3))
            water = [(cx - tw / 2, py), (cx + tw / 2, py), (cx + bw / 2, N + 8), (cx - bw / 2, N + 8)]
            tmp = np.zeros((N, N, 3), np.float32)
            draw.poly(tmp, water, (1, 1, 1), mask_out=self.pool_mask)
            g = np.clip((np.arange(N) - py) / max(1, N - py), 0, 1)[:, None, None]
            day = mix((.04, .55, .72), (.25, .86, .86), g) * mix(tint, (1, 1, 1), 0.5)
            night = mix((.10, .55, .85), (.35, .95, 1.0), g)
            pool = mix(day, night, L["night"]) * np.ones((1, N, 1), np.float32)
            front[self.pool_mask] = pool[self.pool_mask]
            lx = cx + p["ladder"] * (tw / 2 - 8)
            for rail in (lx - 2, lx + 2):
                front[int(py - 6):int(py + 7), int(rail)] = mix((.85, .87, .9) * tint, sil_col, sil * 0.5)
            for ry_ in (py - 1, py + 3):
                front[int(ry_), int(lx - 2):int(lx + 3)] = mix((.85, .87, .9) * tint, sil_col, sil * 0.5)

        if s["kind"] == "beach":
            u = s["umbrella"]
            ux, top = u["x"], D + 4
            front[int(top):int(top + 18), int(ux)] = mix((.9, .9, .88) * tint, sil_col, sil * 0.5)
            yy, xx = draw.Y, draw.X
            can = (((xx - ux) / 13) ** 2 + ((yy - top) / 7) ** 2 <= 1) & (yy <= top)
            stripe = (np.floor((xx - ux + 13) / 4.3) % 2 == 0)
            c1 = mix(np.array(u["colour"]) * tint, sil_col, sil * 0.6)
            c2 = mix((.97, .97, .95) * tint, sil_col, sil * 0.6)
            front[can & stripe] = c1
            front[can & ~stripe] = c2
            occ |= can

        if s["kind"] == "drive":
            c = s["car"]
            ry = int(s["road"])
            base = ry + 12
            pts = [(0, -3), (2, -7), (14, -8), (18, -12), (25, -12), (28, -8), (38, -7), (40, -4), (40, 0), (0, 0)]
            if c["flip"]:
                pts = [(40 - px, py_) for px, py_ in pts]
            body = mix(np.array(c["colour"]) * tint, sil_col, sil * 0.6)
            draw.poly(front, [(c["x"] + px, base + py_) for px, py_ in pts], body)
            chrome = mix((.9, .92, .95) * tint, sil_col, sil * 0.5)
            front[base - 4, int(c["x"]) + 1:int(c["x"]) + 40] = chrome
            front[base - 11:base - 8, int(c["x"]) + 17:int(c["x"]) + 23] = mix(L["hor"] * 0.9, sil_col, sil * 0.5)
            for wx in (8, 32):
                draw.disc(front, c["x"] + wx, base, 3.6, (.06, .06, .08), soft=0.3)
                draw.disc(front, c["x"] + wx, base, 1.4, chrome, soft=0.3)
            if L["night"] > 0.2:                    # headlights reach down the road; tail lights glow
                nose, tail = (c["x"] + 40, c["x"]) if not c["flip"] else (c["x"], c["x"] + 40)
                ahead = 1 if not c["flip"] else -1
                beam = [(nose, base - 6), (nose + ahead * 34, base - 9), (nose + ahead * 34, base + 2), (nose, base - 4)]
                glow = np.zeros((N, N), bool)
                draw.poly(np.zeros((N, N, 3), np.float32), beam, (0, 0, 0), mask_out=glow)
                front[glow] = mix(front[glow], (1, .95, .7), 0.45 * L["night"])
                front[base - 6:base - 4, int(nose) - 1:int(nose) + 1] = (1, .97, .8)
                front[base - 6:base - 4, int(tail):int(tail) + 2] = (1, .1, .1)
        fm |= occ
        self.sea_vis = np.zeros((N, N), bool)
        self.sea_vis[H + 1:D] = True
        self.sea_vis &= ~occ
        self.front, self.fmask = front, fm

    # ---- per frame

    def _palms(self, img):
        s, L = self.scene, self.L
        sil_col = L["top"] * 0.3 + L["shadow"] * 0.2
        sil = L["sil"]
        light_from_left = s["sun_x"] < 64
        trunk_lit = mix(np.array((.72, .55, .36)) * L["tint"], sil_col, sil)
        trunk_dark = mix(np.array((.45, .32, .22)) * L["tint"], sil_col, sil)
        greens = [mix(np.array(c) * L["tint"], sil_col, sil) for c in ((.06, .32, .16), (.12, .48, .22), (.20, .58, .26))]
        t = self.rt.t
        for p in sorted(s["palms"], key=lambda p: p["dy"]):
            bx, by = p["x"], self.D + p["dy"]
            h = min(p["h"], by - 6)
            sway = 0.035 * math.sin(t * 0.9 + p["phase"])
            lean = p["lean"] + sway
            cx, cy = bx + lean * h, by - h
            # the trunk: a quadratic curve, tapering, lit on the sun's side
            ss = np.linspace(0, 1, 14)
            ctrl = (bx + lean * h * 0.15, by - h * 0.6)
            px = (1 - ss) ** 2 * bx + 2 * (1 - ss) * ss * ctrl[0] + ss ** 2 * cx
            py = (1 - ss) ** 2 * by + 2 * (1 - ss) * ss * ctrl[1] + ss ** 2 * cy
            wdt = 2.2 - 1.0 * ss
            left = list(zip(px - wdt, py))
            right = list(zip(px + wdt, py))
            draw.poly(img, left + right[::-1], trunk_dark)
            lit_side = [(x - (w * 0.9 if light_from_left else -w * 0.9), y) for (x, y), w in zip(zip(px, py), wdt)]
            mid = list(zip(px, py))
            draw.poly(img, (lit_side + mid[::-1]), trunk_lit)
            # fronds: drooping, serrated leaves fanned over the top
            r = random.Random(p["seed"])
            n = p["n"]
            for i in range(n):
                th = math.radians(-18 + 216 * i / (n - 1) + r.uniform(-8, 8)) + sway * 2
                dx, dy = math.cos(th), -math.sin(th)
                L_ = p["size"] * r.uniform(0.85, 1.1)
                droop = 0.75 if abs(dx) > 0.5 else 0.35
                s_ = np.linspace(0, 1, 11)
                fx = cx + dx * L_ * s_
                fy = cy + dy * L_ * s_ + droop * L_ * s_ ** 2
                nx, ny = -(dy + 2 * droop * s_), np.full_like(s_, dx)
                nl = np.hypot(nx, ny) + 1e-6
                nx, ny = nx / nl, ny / nl
                w = p["size"] * 0.17 * np.sin(np.pi * s_) ** 0.7 * (0.7 + 0.3 * (np.arange(11) % 2))
                a = list(zip(fx + nx * w, fy + ny * w))
                b = list(zip(fx - nx * w, fy - ny * w))
                draw.poly(img, a + b[::-1], greens[(i + (1 if dy < -0.3 else 0)) % 3])
            for k in range(3):
                draw.disc(img, cx + (k - 1) * 1.8, cy + 1.5, 1.2, mix((.35, .22, .1), sil_col, sil), soft=0.3)

    def render(self):
        self._base()
        L, t = self.L, self.rt.t
        img = self.back.copy()
        # clouds drift across the sky, behind everything in front
        lit = mix(mix((.98, .98, .97) * L["tint"], L["sun"], 0.15 * L["bands"]), L["top"] * 0.6, L["night"] * 0.8)
        shade = mix(mix(L["shadow"], L["hor"], 0.25), L["top"] * 0.4, L["night"] * 0.8)
        for c, m, sh in self.clouds:
            h, w = m.shape
            x = int((c["x"] + t * 1.2) % (N + w + 20)) - w
            y = int(self.horizon - c["up"] - h)
            for (yy, xx), val in ((np.nonzero(m & ~sh), lit), (np.nonzero(sh), shade)):
                yy, xx = yy + y, xx + x
                ok = (xx >= 0) & (xx < N) & (yy >= 0) & (yy < self.horizon)
                img[yy[ok], xx[ok]] = val
        img[self.fmask] = self.front[self.fmask]
        # glints on the sea, and the sun's path across it near sunset
        H, D = self.horizon, self.D
        r = np.random.default_rng(int(t * 6))
        n = 26
        gx, gy = r.integers(0, N, n), r.integers(H + 1, max(H + 2, D), n)
        for x, y in zip(gx, gy):
            if self.sea_vis[y, x]:
                img[y, x:min(N, x + 3)] = mix(L["sea"], L["hor"] + 0.15, 0.7)
        sx, sy, rad = self.sun
        if 0.45 < self.t < 0.9:
            for y in range(H + 1, D):
                wob = int(2 * math.sin(y * 1.7 + t * 5))
                half = int(rad * (0.4 + 0.6 * (y - H) / max(1, D - H)))
                x0, x1 = max(0, int(sx) - half + wob), min(N, int(sx) + half + wob)
                if (y + int(t * 8)) % 2 and x1 > x0:
                    row = self.sea_vis[y, x0:x1]
                    img[y, x0:x1][row] = mix(img[y, x0:x1][row], L["sun"], 0.8)
        # caustics on the pool floor
        if self.pool_mask.any():
            y0 = int(np.argmax(self.pool_mask.any(1)))           # only the pool's rows
            X, Y, pm = draw.X[y0:], draw.Y[y0:], self.pool_mask[y0:]
            c = (np.abs(np.sin(X * 0.33 + 1.8 * np.sin(Y * 0.22 + t * 1.3))
                        + np.sin(Y * 0.41 - t * 1.1 + np.sin(X * 0.17))) < 0.22) & pm
            sub_ = img[y0:]
            sub_[c] = mix(sub_[c], (.85, 1.0, 1.0), 0.45 + 0.3 * L["night"])
        # palms sway slowly: redraw them ~15 times a second, composite the cached layer between
        if self.key != getattr(self, "palm_key", None) or t - getattr(self, "t_palms", -1) > 1 / 15:
            layer = np.full((N, N, 3), -1.0, np.float32)
            self._palms(layer)
            self.palm_layer, self.palm_mask = layer, layer[..., 0] >= 0
            self.palm_key, self.t_palms = self.key, t
        img[self.palm_mask] = self.palm_layer[self.palm_mask]
        img = self._grade(img)
        if self.mirror:
            img = img[:, ::-1]
        if self.frame:
            img = self._album(img)
        if self.rt.t - self.t_seed < 1.0 and not self.frame:
            draw.text(img, f"#{self.seed}", N - 2 - draw.text_width(f"#{self.seed}"), 1, (1, 1, 1))
        return img

    def _grade(self, img):
        name = PALETTES[self.palette]
        if name == "pastel":
            y = img @ np.array([.3, .59, .11], np.float32)
            img = (y[..., None] * 0.25 + img * 0.75) * 0.72 + 0.28
        elif name == "tropical":
            y = img @ np.array([.3, .59, .11], np.float32)
            img = y[..., None] + (img - y[..., None]) * 1.45
            img[..., 1] *= 1.05
        elif name == "print":
            y = np.clip(img @ np.array([.3, .59, .11], np.float32), 0, 1) ** 0.9
            img = mix((.02, .11, .42), (.95, .97, 1.0), y[..., None])
        return np.clip(img, 0, 1)

    def _album(self, img):
        out = np.empty_like(img)
        out[:] = (.97, .96, .93)
        out[5:104, 5:123] = img[5:104, 5:123]
        draw.text(out, self.scene["title"], 6, 106, (.08, .12, .35))
        draw.text(out, "PATTERNFLOOD", 6, 116, (.45, .45, .5))
        return out

    def lights(self):
        L = self.L if hasattr(self, "L") else light(self.t)
        return [tuple(float(v) for v in L["hor"]),
                (.15, .7, .75) if self.scene["kind"] == "pool" else tuple(float(v) for v in L["sea"] * 1.6),
                tuple(float(v) for v in L["sea"] * 1.4),
                (.9, .88, .8) if self.frame else (.2, .2, .2)]
