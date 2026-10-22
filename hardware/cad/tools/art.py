#!/usr/bin/env python3
"""Etched art for the box's outside faces: a generated circuit-board pattern.

    hardware/cad/tools/art.py            (reads hardware/laser/*.dxf, writes hardware/laser/art/)

For each visible part — bezel, side walls, top wall, back cover — this reads
the part's cut DXF (drawn as seen from OUTSIDE, so the face up on the laser bed
is the outer face), works out where etching is allowed, and fills it with
a dense, generated circuit board meant to be looked at for a long time: on a
1.27 mm grid, QFP / BGA / SOIC chips with their fan-out, passives, headers,
crystals, test points, fiducials, spiral inductors, Hilbert meanders,
length-matched serpentines, wide power traces, parallel buses, silkscreen
designators in a single-stroke font (artfont.py), and the leftover space
filled with hatch, cross-hatch, topographic contours or stipple — or left empty
on purpose. Hidden in it: a real QR code per part (it scans; see QR_MESSAGES), a space
invader, a Lissajous figure, and tiny words in some of the empty spaces. On the
bezel each knob gets a real dial: a 270-degree scale 0-10 with fine ticks,
numerals, and the knob's name.

Allowed area = the part's outline, inset past the finger joints, minus every
hole, slot and cutout grown by a margin. Nothing is etched on a joint, near a
cut edge, or under a knob.

Outputs, per part, in the part's own frame:
  art/<part>.etch.dxf   etch only, layer SCORE (lines and circles; the dots are tight
                        concentric circles that burn in solid — see vector_dots), for reference
  art/<part>.svg        cut (red) + score (blue) + engrave (black fill) — what you'd
                        load to cut that part alone
  art/<part>.decal.png  the art alone, transparent, over exactly the part's DXF frame —
                        tools/decals.py uploads these, and the Enclosure shell shows them
                        as decals on the outer faces in Onshape
and art/preview.png. nest_sheets.py picks the etch files up and puts the art on
the sheets, in sheets/sheet-N.svg.

Seeded per part: re-running gives the same art. Change SEED to re-roll.
Needs shapely, Pillow and segno (QR encoding); zxing-cpp, if installed, checks
that every QR code decodes from the score lines actually drawn.
"""
import math
import os
import random
import sys

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polygonize, unary_union
from shapely.prepared import prep

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from nest_sheets import read_dxf  # noqa: E402
import artfont  # noqa: E402

LASER = os.path.join(HERE, "..", "..", "laser")
OUT = os.path.join(LASER, "art")

T = 3.18             # sheet thickness: the finger joints reach this far in from an edge
EDGE = T + 2.5       # keep this far inside the outline
HOLE = 2.0           # and this far from any hole or slot
G = 1.27             # trace grid pitch: real PCB pitch (0.05")
DIAL_R = 15.0        # dial scale radius round each knob (a 20 mm / 1" knob hides r < ~13)
DIAL_KEEP = 22.5     # the dial, its numerals and name own r < this round each knob
PAD = 0.9            # nodes and traces keep this far inside the allowed area (via ring 0.55)

# part file -> seed. The bottom wall is the base: never seen, not etched.
PARTS = {"bezel-outer.dxf": 11, "wall-left.dxf": 12, "wall-right-iec.dxf": 13,
         "wall-top.dxf": 14, "back-cover.dxf": 15}
SEED = 2026


# ── part geometry ─────────────────────────────────────────────────────────
def sampled(e, step=0.5):
    if e[0] == "L":
        return [e[1], e[2]]
    (cx, cy), r = e[1], e[2]
    a0, a1 = (0.0, 360.0) if e[0] == "C" else (e[3], e[4])
    sw = (a1 - a0) % 360 or 360
    n = max(8, int(math.radians(sw) * r / step))
    return [(cx + r * math.cos(math.radians(a0 + sw * k / n)), cy + r * math.sin(math.radians(a0 + sw * k / n)))
            for k in range(n + 1)]


def part_regions(ents):
    """(outline polygon, [hole polygons], [knob centres])."""
    lines = [LineString(sampled(e)) for e in ents]
    rings = sorted((Polygon(p.exterior) for p in polygonize(unary_union(lines))), key=lambda p: -p.area)
    outline = rings[0]
    holes = [h for h in rings[1:] if h.within(outline.buffer(0.01))]
    knobs = [e[1] for e in ents if e[0] == "C" and 3.0 < e[2] < 4.0]   # the 7 mm knob bores
    return outline, holes, knobs


# ── generator (v2: dense) ─────────────────────────────────────────────────
# Composition, in order, on a 1.27 mm grid (real PCB pitch):
#   dials (bezel) -> title block (back cover) -> components (QFP, BGA, SOIC,
#   headers, passives, crystals, test points, fiducials, inductors, Hilbert
#   meanders, serpentines, a data matrix that really encodes a message) ->
#   their escape routing -> parallel buses -> free traces -> "pours" in the
#   leftover space (hatch, cross-hatch, topographic contours, stipple, or left
#   empty on purpose) -> tiny hidden text in some of the empty ones.
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
KNOB_NAMES = ["BRIGHT", "NETWORK", "VALUES", "PATTERN"]        # K1..K4, reading order
EGGS = ["LOOK CLOSER", "HELLO FROM INSIDE", "MADE OF LIGHT", "PATTERNFLOW", "NO USER SERVICEABLE PARTS",
        "128 X 128", "IN LOW OUT HIGH", "KERF 0.15", "FM6124", "RUC7258", "5A-75B", "WAS HERE",
        "TURN ME", "SEE YOU IN THE GRID", "GND IS A STATE OF MIND"]


def hilbert(order):
    """Points of a Hilbert curve on an n x n grid, n = 2**order."""
    n = 2 ** order
    pts = []
    for d in range(n * n):
        rx = ry = 0
        x = y = 0
        t = d
        s = 1
        while s < n:
            rx = 1 & (t // 2)
            ry = 1 & (t ^ rx)
            if ry == 0:
                if rx == 1:
                    x, y = s - 1 - x, s - 1 - y
                x, y = y, x
            x += s * rx
            y += s * ry
            t //= 4
            s *= 2
        pts.append((x, y))
    return pts


class Board:
    def __init__(self, allowed, rng):
        self.allowed, self.rng = allowed, rng
        self.core = allowed.buffer(-PAD)
        self.pcore = prep(self.core)
        x0, y0, x1, y1 = allowed.bounds
        self.ox, self.oy = math.floor(x0 / G) * G, math.floor(y0 / G) * G
        self.nodes = set()
        for i in range(int((x1 - self.ox) / G) + 2):
            for j in range(int((y1 - self.oy) / G) + 2):
                if self.pcore.contains(Point(self.ox + i * G, self.oy + j * G)):
                    self.nodes.add((i, j))
        self.used = set()
        self.score, self.engrave = [], []
        self.geoms = []                       # what the pours must keep clear of
        self.refs = {}
        self.qrs = []                         # (message, box) of each QR code, to verify

    # ── primitives ──
    def xy(self, n):
        return (self.ox + n[0] * G, self.oy + n[1] * G)

    def node_at(self, p):
        return (round((p[0] - self.ox) / G), round((p[1] - self.oy) / G))

    def free(self, n):
        return n in self.nodes and n not in self.used

    def ref(self, prefix):
        self.refs[prefix] = self.refs.get(prefix, 0) + 1
        return f"{prefix}{self.refs[prefix]}"

    def seg(self, a, b):
        self.score.append(("L", a, b))
        self.geoms.append(LineString([a, b]))

    def poly(self, pts, closed=False):
        if closed:
            pts = list(pts) + [pts[0]]
        for a, b in zip(pts, pts[1:]):
            self.score.append(("L", a, b))
        self.geoms.append(LineString(pts))

    def ring(self, c, r):
        self.score.append(("C", c, r))
        self.geoms.append(Point(c).buffer(r))

    def dot(self, c, r):
        self.engrave.append(("C", c, r))
        self.geoms.append(Point(c).buffer(r))

    def rect(self, x0, y0, x1, y1):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], closed=True)

    def label(self, s, x, y, h=1.0, anchor="left"):
        segs = artfont.text(s, x, y, h, anchor)
        if not segs:
            return
        self.score += segs
        xs = [p[0] for e in segs for p in (e[1], e[2])]
        ys = [p[1] for e in segs for p in (e[1], e[2])]
        self.geoms.append(box(min(xs), min(ys), max(xs), max(ys)))

    def label_fits(self, s, x, y, h):
        w = artfont.width(s, h)
        return self.pcore.contains(box(x, y, x + w, y + h))

    # ── cells ──
    def cells_free(self, i0, j0, i1, j1):
        return all(self.free((i, j)) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1))

    def reserve(self, i0, j0, i1, j1):
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                self.used.add((i, j))

    def spot(self, w, h, margin=1, tries=700):
        cand = list(self.nodes - self.used)
        if not cand:
            return None
        for _ in range(tries):
            i, j = self.rng.choice(cand)
            if self.cells_free(i - margin, j - margin, i + w + margin, j + h + margin):
                return (i, j)
        return None

    # ── routing ──
    def step_ok(self, cur, nd, taken):
        dx, dy = DIRS[nd]
        nxt = (cur[0] + dx, cur[1] + dy)
        if not self.free(nxt) or nxt in taken:
            return None
        if dx and dy:
            if (cur[0] + dx, cur[1]) in self.used and (cur[0], cur[1] + dy) in self.used:
                return None
            if not self.pcore.contains(LineString([self.xy(cur), self.xy(nxt)])):
                return None
        return nxt

    def route(self, start, d, lo=3, hi=30, straight=10):
        if not self.free(start):
            return None
        path, cur = [start], start
        want = self.rng.randint(lo, hi)
        taken = {start}
        while len(path) <= want:
            opts = [(d, straight), ((d + 1) % 8, 1), ((d - 1) % 8, 1)]
            weights = [w * self.rng.random() for _, w in opts]
            for (nd, _), _w in sorted(zip(opts, weights), key=lambda o: -o[1]):
                nxt = self.step_ok(cur, nd, taken)
                if nxt:
                    path.append(nxt)
                    taken.add(nxt)
                    cur, d = nxt, nd
                    break
            else:
                break
        return path if len(path) >= lo else None

    def commit(self, path, start="pad", end="via", power=False):
        self.used.update(path)
        pts = [self.xy(n) for n in path]
        keep = [pts[0]]
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9:
                keep.append(b)
        keep.append(pts[-1])
        if power and len(keep) >= 2:
            # a wide trace, drawn as its outline
            outline = LineString(keep).buffer(0.42, cap_style=1, join_style=2, mitre_limit=2).exterior
            self.poly(list(outline.simplify(0.02).coords))
            for n in path:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        self.used.add((n[0] + dx, n[1] + dy))
        else:
            self.poly(keep)
        for at, kind in ((pts[0], start), (pts[-1], end)):
            if kind == "via":
                self.ring(at, 0.55)
                self.dot(at, 0.2)
            elif kind == "pad":
                self.dot(at, 0.42)
            elif kind == "ring":
                self.ring(at, 0.45)

    def fan_out(self, pins, lo=2, hi=26, power=0.08, end_kinds=("via", "via", "pad", "ring")):
        for node, d, stub in pins:
            path = self.route(node, d, lo, hi)
            if path:
                self.commit(path, start="none", end=self.rng.choice(end_kinds), power=self.rng.random() < power)
                if stub:
                    self.seg(stub, self.xy(node))

    def bus(self, lanes_n):
        """k parallel traces moving in lockstep."""
        d = self.rng.choice([0, 2, 4, 6])
        px, py = DIRS[(d + 2) % 8]
        for _ in range(60):
            s = self.rng.choice(list(self.nodes - self.used))
            lanes = [(s[0] + k * px, s[1] + k * py) for k in range(lanes_n)]
            if all(self.free(n) for n in lanes):
                break
        else:
            return
        paths = [[n] for n in lanes]
        taken = set(lanes)
        want = self.rng.randint(10, 60)
        cur_d = d
        for _ in range(want):
            nd = cur_d if self.rng.random() < 0.88 else (cur_d + self.rng.choice([1, -1])) % 8
            if nd % 2 == 1 and cur_d % 2 == 1:
                nd = cur_d                      # no diagonal-to-diagonal swing
            nxts = [self.step_ok(p[-1], nd, taken) for p in paths]
            if not all(nxts):
                nxts = [self.step_ok(p[-1], cur_d, taken) for p in paths]
                nd = cur_d
                if not all(nxts):
                    break
            for p, n in zip(paths, nxts):
                p.append(n)
                taken.add(n)
            cur_d = nd
        if len(paths[0]) >= 6:
            for k, p in enumerate(paths):
                self.commit(p, start="via", end="via" if k % 2 else "pad")

    # ── components ──
    def qfp(self, n):
        at = self.spot(n, n, margin=2)
        if not at:
            return
        i, j = at
        self.reserve(i, j, i + n, j + n)
        x0, y0 = self.xy((i, j))
        x1, y1 = self.xy((i + n, j + n))
        m = G * 0.4
        self.rect(x0 + m, y0 + m, x1 - m, y1 - m)
        q = (n * G) * 0.28
        self.rect(x0 + q, y0 + q, x1 - q, y1 - q)                   # the die
        self.dot((x0 + m + 0.9, y1 - m - 0.9), 0.35)
        pins = []
        for a in range(1, n):
            pins += [((i + a, j - 1), 6, (self.xy((i + a, j))[0], y0 + m)),
                     ((i + a, j + n + 1), 2, (self.xy((i + a, j))[0], y1 - m)),
                     ((i - 1, j + a), 4, (x0 + m, self.xy((i, j + a))[1])),
                     ((i + n + 1, j + a), 0, (x1 - m, self.xy((i, j + a))[1]))]
        self.rng.shuffle(pins)
        self.fan_out([p for p in pins[: int(len(pins) * 0.8)]])
        r = self.ref("U")
        if self.label_fits(r, x0, y1 + 1.6, 1.2):
            self.label(r, x0, y1 + 1.6, 1.2)
        name = self.rng.choice(["MCU", "FPGA", "ECP5", "RP3A0", "DSP", "PHY", "SERDES", "GPU", "NPU"])
        self.label(name, (x0 + x1) / 2, (y0 + y1) / 2, min(1.6, (x1 - x0) * 0.08), anchor="center")

    def bga(self, n):
        at = self.spot(n + 1, n + 1, margin=2)
        if not at:
            return
        i, j = at
        self.reserve(i, j, i + n + 1, j + n + 1)
        x0, y0 = self.xy((i, j))
        x1, y1 = self.xy((i + n + 1, j + n + 1))
        self.poly([(x0 + 1.4, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0 + 1.4), (x0 + 1.4, y0)])
        for a in range(1, n + 1):
            for b in range(1, n + 1):
                self.dot(self.xy((i + a, j + b)), 0.26)
        pins = []
        for a in range(1, n + 1, 2):
            pins += [((i + a, j - 1), 6, None), ((i + a, j + n + 2), 2, None),
                     ((i - 1, j + a), 4, None), ((i + n + 2, j + a), 0, None)]
        self.fan_out(pins, end_kinds=("via",))
        r = self.ref("U")
        if self.label_fits(r, x0, y1 + 1.4, 1.1):
            self.label(r, x0, y1 + 1.4, 1.1)

    def soic(self, n):
        horiz = self.rng.random() < 0.5
        w, h = (n, 3) if horiz else (3, n)
        at = self.spot(w, h, margin=2)
        if not at:
            return
        i, j = at
        self.reserve(i, j, i + w, j + h)
        x0, y0 = self.xy((i, j))
        x1, y1 = self.xy((i + w, j + h))
        m = G * 0.45
        self.rect(x0 + m, y0 + m, x1 - m, y1 - m)
        self.dot((x0 + m + 0.7, y0 + m + 0.7), 0.25)
        pins = []
        if horiz:
            for a in range(1, w):
                pins += [((i + a, j - 1), 6, (self.xy((i + a, j))[0], y0 + m)),
                         ((i + a, j + h + 1), 2, (self.xy((i + a, j))[0], y1 - m))]
        else:
            for b in range(1, h):
                pins += [((i - 1, j + b), 4, (x0 + m, self.xy((i, j + b))[1])),
                         ((i + w + 1, j + b), 0, (x1 - m, self.xy((i, j + b))[1]))]
        self.fan_out(pins)
        r = self.ref("U")
        if self.label_fits(r, x1 + 0.8, y0, 1.0):
            self.label(r, x1 + 0.8, y0, 1.0)

    def passive(self):
        horiz = self.rng.random() < 0.5
        w, h = (2, 0) if horiz else (0, 2)
        at = self.spot(w, h, margin=1)
        if not at:
            return
        i, j = at
        self.reserve(i - 1, j - 1, i + w + 1, j + h + 1)
        a, b = self.xy((i, j)), self.xy((i + w, j + h))
        s = 0.45
        for p in (a, b):
            self.rect(p[0] - s, p[1] - s, p[0] + s, p[1] + s)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if horiz:
            self.rect(mid[0] - 0.5, mid[1] - 0.3, mid[0] + 0.5, mid[1] + 0.3)
            pins = [((i - 2, j), 4, (a[0] - s, a[1])), ((i + w + 2, j), 0, (b[0] + s, b[1]))]
        else:
            self.rect(mid[0] - 0.3, mid[1] - 0.5, mid[0] + 0.3, mid[1] + 0.5)
            pins = [((i, j - 2), 6, (a[0], a[1] - s)), ((i, j + h + 2), 2, (b[0], b[1] + s))]
        for node, d, stub in pins:
            if self.free(node):
                path = self.route(node, d, 2, 20)
                if path:
                    self.commit(path, start="none", end=self.rng.choice(["via", "pad"]))
                    self.seg(stub, self.xy(node))
        r = self.ref(self.rng.choice(["R", "R", "C", "C", "L", "D", "FB"]))
        lx, ly = (a[0] - 0.4, a[1] + 1.0) if horiz else (a[0] + 1.0, a[1] - 0.4)
        if self.label_fits(r, lx, ly, 0.8):
            self.label(r, lx, ly, 0.8)

    def header(self, m):
        horiz = self.rng.random() < 0.5
        w, h = (m - 1, 0) if horiz else (0, m - 1)
        at = self.spot(w + 1, h + 1, margin=2)
        if not at:
            return
        i, j = at
        self.reserve(i - 1, j - 1, i + w + 1, j + h + 1)
        pins = []
        for k in range(m):
            n = (i + k, j) if horiz else (i, j + k)
            c = self.xy(n)
            if k == 0:
                self.rect(c[0] - 0.5, c[1] - 0.5, c[0] + 0.5, c[1] + 0.5)
            else:
                self.ring(c, 0.5)
            self.dot(c, 0.2)
            pins.append(((n[0], n[1] - 2) if horiz else (n[0] - 2, n[1]), 6 if horiz else 4, None))
        x0, y0 = self.xy((i, j))
        x1, y1 = self.xy((i + w, j + h))
        self.rect(x0 - 0.9, y0 - 0.9, x1 + 0.9, y1 + 0.9)
        self.fan_out(pins, lo=2, hi=18)
        r = self.ref("J")
        if self.label_fits(r, x0, y1 + 1.4, 1.0):
            self.label(r, x0, y1 + 1.4, 1.0)

    def crystal(self):
        at = self.spot(4, 2, margin=1)
        if not at:
            return
        i, j = at
        self.reserve(i, j, i + 4, j + 2)
        x0, y0 = self.xy((i, j))
        x1, y1 = self.xy((i + 4, j + 2))
        r = 1.0
        pts = []
        for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            pts += [(cx + r * math.cos(math.radians(a0 + t * 15)), cy + r * math.sin(math.radians(a0 + t * 15)))
                    for t in range(7)]
        self.poly(pts, closed=True)
        for n in ((i + 1, j + 1), (i + 3, j + 1)):
            self.dot(self.xy(n), 0.35)
        self.fan_out([((i - 1, j + 1), 4, None), ((i + 5, j + 1), 0, None)], lo=2, hi=12)
        ref = self.ref("Y")
        if self.label_fits(ref, x0, y1 + 1.0, 0.8):
            self.label(ref, x0, y1 + 1.0, 0.8)

    def test_point(self):
        at = self.spot(0, 0, margin=1)
        if not at:
            return
        self.reserve(at[0] - 1, at[1] - 1, at[0] + 1, at[1] + 1)
        c = self.xy(at)
        self.ring(c, 0.7)
        self.dot(c, 0.3)
        r = self.ref("TP")
        if self.label_fits(r, c[0] + 1.0, c[1] + 0.6, 0.8):
            self.label(r, c[0] + 1.0, c[1] + 0.6, 0.8)
        self.fan_out([((at[0] + 1, at[1] - 1), 7, None)], lo=2, hi=14)

    def fiducial(self):
        at = self.spot(2, 2, margin=1)
        if not at:
            return
        self.reserve(at[0], at[1], at[0] + 2, at[1] + 2)
        c = self.xy((at[0] + 1, at[1] + 1))
        self.ring(c, 1.15)
        self.dot(c, 0.45)

    def inductor(self, k):
        at = self.spot(k, k, margin=1)
        if not at:
            return
        i, j = at
        self.reserve(i, j, i + k, j + k)
        x0, y0 = self.xy((i, j))
        s = k * G
        sp = 0.55
        pts, lo, hi = [], 0.0, s
        while hi - lo > 2 * sp:
            pts += [(x0 + lo, y0 + lo), (x0 + hi, y0 + lo), (x0 + hi, y0 + hi), (x0 + lo + sp, y0 + hi)]
            lo += sp
            hi -= sp
            pts.append((x0 + lo, y0 + hi))
        self.poly(pts)
        r = self.ref("L")
        if self.label_fits(r, x0, y0 + s + 0.9, 0.9):
            self.label(r, x0, y0 + s + 0.9, 0.9)

    def meander(self, order):
        k = 2 ** order
        cells = math.ceil(k * 0.5)
        at = self.spot(cells, cells, margin=1)
        if not at:
            return
        i, j = at
        self.reserve(i, j, i + cells, j + cells)
        x0, y0 = self.xy((i, j))
        step = cells * G / k
        pts = [(x0 + (px + 0.5) * step, y0 + (py + 0.5) * step) for px, py in hilbert(order)]
        self.poly(pts)

    def serpentine(self):
        n = self.rng.randint(5, 12)
        horiz = self.rng.random() < 0.5
        w, h = (2 * n + 2, 3) if horiz else (3, 2 * n + 2)
        at = self.spot(w, h, margin=1)
        if not at:
            return
        i, j = at
        self.reserve(i, j, i + w, j + h)
        x0, y0 = self.xy((i, j))
        pts = []
        amp = 3 * G
        for k in range(n + 1):
            u = (1 + 2 * k) * G
            v0, v1 = (0.0, amp) if k % 2 == 0 else (amp, 0.0)
            pts += [(u, v0), (u, v1)] if k < n else [(u, v0)]
            if k < n:
                pts.append((u + 2 * G, v1))
        pts = [(x0 + u, y0 + v) for u, v in pts] if horiz else [(x0 + v, y0 + u) for u, v in pts]
        self.poly(pts)
        for p in (pts[0], pts[-1]):
            self.ring(p, 0.5)
        r = self.ref("DIFF")
        lx, ly = pts[0][0], pts[0][1] - 1.6
        if self.label_fits(r, lx, ly, 0.8):
            self.label(r, lx, ly, 0.8)

    def qr(self, message, module=0.8, quiet=4):
        """A real, scannable QR code (segno, error correction M). Dark modules
        are filled solid with horizontal score lines a little closer than the
        beam is wide; the quiet zone round it is kept clear of every other mark."""
        import segno
        mat = [list(row) for row in segno.make(message, error="m", micro=False).matrix]
        n = len(mat)
        side = (n + 2 * quiet) * module
        cells = math.ceil(side / G) + 1
        at = self.spot(cells, cells, margin=1, tries=4000)
        if not at:
            print(f"  (no room for the QR code '{message[:24]}...')")
            return
        i, j = at
        self.reserve(i - 1, j - 1, i + cells + 1, j + cells + 1)
        x0, y0 = self.xy((i, j))
        self.geoms.append(box(x0, y0, x0 + side, y0 + side))       # quiet zone: pours keep out
        ox, oy = x0 + quiet * module, y0 + quiet * module
        pitch = QR_FILL
        lines_per = max(1, round(module / pitch))
        inset = BEAM / 2
        for r, row in enumerate(mat):
            top = oy + (n - r) * module
            c = 0
            while c < n:
                if not row[c]:
                    c += 1
                    continue
                c1 = c
                while c1 + 1 < n and row[c1 + 1]:
                    c1 += 1
                xa, xb = ox + c * module + inset, ox + (c1 + 1) * module - inset
                for k in range(lines_per):
                    y = top - inset - k * (module - 2 * inset) / max(1, lines_per - 1)
                    self.score.append(("L", (xa, y), (xb, y)))
                c = c1 + 1
        self.qrs.append((message, (x0, y0, x0 + side, y0 + side)))

    def invader(self):
        sprite = ["..X.....X..", "...X...X...", "..XXXXXXX..", ".XX.XXX.XX.", "XXXXXXXXXXX",
                  "X.XXXXXXX.X", "X.X.....X.X", "...XX.XX..."]
        p = 0.6
        cells = math.ceil(11 * p / G) + 1
        at = self.spot(cells, cells, margin=2)
        if not at:
            return
        i, j = at
        self.reserve(i, j, i + cells, j + cells)
        x0, y0 = self.xy((i, j))
        for r, row in enumerate(sprite):
            for c, ch in enumerate(row):
                if ch == "X":
                    self.dot((x0 + c * p, y0 + (7 - r) * p), 0.24)

    def lissajous(self, size, a=3, b=2):
        cells = math.ceil(size / G)
        at = self.spot(cells, cells, margin=2)
        if not at:
            return
        i, j = at
        self.reserve(i, j, i + cells, j + cells)
        c = self.xy((i + cells / 2, j + cells / 2))
        r = size / 2 * 0.92
        pts = [(c[0] + r * math.sin(a * t + math.pi / 2), c[1] + r * math.sin(b * t))
               for t in [k * 2 * math.pi / 400 for k in range(401)]]
        self.poly(pts)

    def title_block(self, lines):
        h = 1.6
        w = max(artfont.width(s, h) for s in lines) + 4
        rows = len(lines)
        cw, ch = math.ceil(w / G) + 1, math.ceil((rows * 2.6 + 3 + 8) / G) + 1
        at = self.spot(cw, ch, margin=2, tries=3000)
        if not at:
            return
        i, j = at
        self.reserve(i, j, i + cw, j + ch)
        x0, y0 = self.xy((i, j))
        x1, y1 = self.xy((i + cw, j + ch))
        self.rect(x0, y0, x1, y1)
        self.rect(x0 + 0.6, y0 + 0.6, x1 - 0.6, y1 - 0.6)
        y = y1 - 2.4 - h
        for s in lines:
            self.label(s, x0 + 2, y, h)
            self.seg((x0 + 0.6, y - 0.6), (x1 - 0.6, y - 0.6))
            y -= 2.6
        # a barcode under the text
        bx = x0 + 2
        while bx < x1 - 2:
            wbar = self.rng.choice([0.2, 0.2, 0.4, 0.6])
            for t in range(int(wbar / 0.2)):
                self.seg((bx + t * 0.2, y0 + 1.6), (bx + t * 0.2, y0 + 6.0))
            bx += wbar + self.rng.choice([0.3, 0.5, 0.7])


def dial(board, c, name):
    """A knob's dial: rings and a 270-degree scale with fine ticks. Unlabelled on
    purpose — no numerals, no names (`name` is kept for the caller's sake)."""
    board.ring(c, DIAL_R)
    board.ring(c, DIAL_R - 1.0)
    a_lo, a_hi = 225.0, -45.0                     # clockwise from lower-left to lower-right
    for k in range(101):
        a = math.radians(a_lo + (a_hi - a_lo) * k / 100)
        ln = 2.6 if k % 10 == 0 else 1.6 if k % 5 == 0 else 0.9
        p = (c[0] + DIAL_R * math.cos(a), c[1] + DIAL_R * math.sin(a))
        q = (c[0] + (DIAL_R + ln) * math.cos(a), c[1] + (DIAL_R + ln) * math.sin(a))
        board.seg(p, q)
    # an arc of fine dots just inside, like a gauge
    for k in range(0, 61):
        a = math.radians(a_lo + (a_hi - a_lo) * k / 60)
        board.dot((c[0] + (DIAL_R - 2.2) * math.cos(a), c[1] + (DIAL_R - 2.2) * math.sin(a)), 0.16)
    # traces leaving the dial, from just outside its numerals
    for k in range(10):
        a = math.radians(k * 36 + 18)
        p = (c[0] + (DIAL_KEEP + 1.5) * math.cos(a), c[1] + (DIAL_KEEP + 1.5) * math.sin(a))
        n = board.node_at(p)
        d = round((math.degrees(a) % 360) / 45) % 8
        if board.free(n):
            path = board.route(n, d, 3, 30)
            if path:
                board.commit(path, start="ring", end=board.rng.choice(["via", "pad"]))


def pours(b, eggs):
    """Fill the leftover space: hatch, cross-hatch, contours, stipple — or nothing."""
    occupied = unary_union([g.buffer(0.55) for g in b.geoms]) if b.geoms else Polygon()
    free = b.allowed.buffer(-0.7).difference(occupied)
    polys = [p for p in getattr(free, "geoms", [free]) if p.area > 25]
    polys.sort(key=lambda p: -p.area)
    empty = []
    for p in polys:
        style = b.rng.choices(["hatch", "cross", "contour", "stipple", "empty"], [30, 14, 26, 10, 20])[0]
        inner = p.buffer(-0.35)
        if inner.is_empty:
            continue
        if style in ("hatch", "cross"):
            sp = 0.8 if style == "hatch" else 1.15
            angs = [45] if style == "hatch" else [45, -45]
            if b.rng.random() < 0.3 and style == "hatch":
                angs = [-45]
            x0, y0, x1, y1 = inner.bounds
            L = (x1 - x0) + (y1 - y0)
            for ang in angs:
                ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                n = int(L / sp) + 2
                for k in range(-n, n + 1):
                    off = k * sp
                    a = (cx - sa * off - ca * L, cy + ca * off - sa * L)
                    q = (cx - sa * off + ca * L, cy + ca * off + sa * L)
                    clip = inner.intersection(LineString([a, q]))
                    for g in getattr(clip, "geoms", [clip]):
                        if g.geom_type == "LineString" and g.length > 0.3:
                            cs = list(g.coords)
                            b.score.append(("L", cs[0], cs[-1]))
        elif style == "contour":
            d = 0.7
            for k in range(1, 40):
                ring_poly = p.buffer(-d * k)
                if ring_poly.is_empty:
                    break
                for g in getattr(ring_poly, "geoms", [ring_poly]):
                    for ring in [g.exterior] + list(g.interiors):
                        cs = list(ring.simplify(0.04).coords)
                        b.score += [("L", u, v) for u, v in zip(cs, cs[1:])]
        elif style == "stipple":
            if p.area > 1500:
                empty.append(p)
                continue
            sp = 1.0
            x0, y0, x1, y1 = inner.bounds
            pin = prep(inner.buffer(-0.2))
            row = 0
            y = y0
            while y < y1:
                x = x0 + (sp / 2 if row % 2 else 0)
                while x < x1:
                    if pin.contains(Point(x, y)):
                        b.engrave.append(("C", (x, y), 0.17))
                    x += sp
                y += sp * 0.866
                row += 1
        else:
            empty.append(p)
    # hidden words, tiny, in some of the empty spaces
    b.rng.shuffle(eggs)
    for p in empty:
        if not eggs:
            break
        s = eggs[0]
        h = 0.9
        w = artfont.width(s, h)
        c = p.representative_point()
        bx = box(c.x - w / 2, c.y - h / 2, c.x + w / 2, c.y + h / 2)
        if p.buffer(-0.4).contains(bx):
            b.score += artfont.text(s, c.x, c.y, h, anchor="center")
            eggs.pop(0)


def generate(name, seed):
    ents = read_dxf(os.path.join(LASER, name))
    outline, holes, knobs = part_regions(ents)
    keep_out = [h.buffer(HOLE) for h in holes] + [Point(k).buffer(DIAL_KEEP) for k in knobs]
    allowed = outline.buffer(-EDGE).difference(unary_union(keep_out)) if keep_out else outline.buffer(-EDGE)
    rng = random.Random(SEED * 100 + seed)
    b = Board(allowed, rng)
    knobs = sorted(knobs, key=lambda c: (-round(c[1]), c[0]))        # reading order: K1..K4
    for k, c in enumerate(knobs):
        dial(b, c, KNOB_NAMES[k] if k < len(KNOB_NAMES) else f"K{k + 1}")
    A = allowed.area
    if name.startswith("back-cover"):
        b.title_block(["PATTERNFLOW / DESKTOP", "REV 2  2026-10", "128 X 128  P2 GOB X4", "PI 5 + 5A-75B",
                       "LRS-50-5  5V 10A", "BIRCH 3.18  KERF 0.15"])
    if name.startswith("bezel"):
        b.lissajous(11)
    msg, mod = QR_MESSAGES.get(name, ("PATTERNFLOW", 0.8))
    b.qr(msg, module=mod)
    big = A > 20000
    for _ in range(max(1 if big else 0, int(A / 16000))):
        b.qfp(rng.randint(9, 15))
    for _ in range(int(A / 24000)):
        b.bga(rng.randint(5, 8))
    for _ in range(max(1, int(A / 5000))):
        b.soic(rng.randint(5, 9))
    for _ in range(int(A / 12000)):
        b.header(rng.randint(4, 10))
    for _ in range(int(A / 9000)):
        b.crystal()
    for _ in range(int(A / 14000)):
        b.inductor(rng.randint(5, 8))
    for _ in range(max(1, int(A / 20000))):
        b.meander(rng.choice([3, 4]))
    for _ in range(int(A / 9000)):
        b.serpentine()
    if rng.random() < 0.7 or name.startswith("back"):
        b.invader()
    for _ in range(3):
        b.fiducial()
    for _ in range(int(A / 1600)):
        b.test_point()
    for _ in range(int(A / 420)):
        b.passive()
    for _ in range(int(A / 6000)):
        b.bus(rng.randint(3, 8))
    for _ in range(int(A / 30)):
        free = list(b.nodes - b.used)
        if len(free) < 4:
            break
        n = rng.choice(free)
        path = b.route(n, rng.randrange(0, 8, 2) if rng.random() < 0.75 else rng.randrange(8), 3, 34)
        if path:
            b.commit(path, start=rng.choice(["pad", "via", "ring"]), end=rng.choice(["via", "pad"]),
                     power=rng.random() < 0.05)
    pours(b, list(EGGS))
    QR_FOUND[name] = b.qrs
    return ents, allowed, b.score + vector_dots(b.engrave), []


BEAM = 0.15          # what one scored line burns, roughly
QR_FILL = 0.12       # QR dark-module fill pitch: a little under BEAM, so it burns in solid
QR_FOUND = {}        # part -> [(message, box)], filled by generate(), checked by verify_qr()
# one real QR code per part: (text, module size mm). Phone cameras read 0.8 mm modules fine.
QR_MESSAGES = {
    "back-cover.dxf": ("PATTERNFLOW DESKTOP / REV 2 / 2026 - 128x128 P2 GOB - RASPBERRY PI 5 + COLORLIGHT 5A-75B "
                       "- LRS-50-5 - BALTIC BIRCH 3.18 - IF YOU CAN READ THIS, YOU LOOKED CLOSE ENOUGH", 1.0),
    "bezel-outer.dxf": ("TURN THE KNOBS", 0.8),
    "wall-left.dxf": ("LOOK CLOSER", 0.8),
    "wall-right-iec.dxf": ("IN LOW, OUT HIGH", 0.8),
    "wall-top.dxf": ("SEE YOU IN THE GRID", 0.8),
}


def verify_qr(name, score):
    """Render each QR code from its actual score lines and decode it. -> [(want, got)]."""
    try:
        import zxingcpp
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    out = []
    for msg, (x0, y0, x1, y1) in QR_FOUND.get(name, []):
        k = 20.0                                        # px per mm
        im = Image.new("L", (round((x1 - x0) * k), round((y1 - y0) * k)), 235)
        d = ImageDraw.Draw(im)
        for e in score:
            if e[0] == "L" and x0 <= e[1][0] <= x1 and y0 <= e[1][1] <= y1:
                d.line([((e[1][0] - x0) * k, (y1 - e[1][1]) * k), ((e[2][0] - x0) * k, (y1 - e[2][1]) * k)],
                       fill=60, width=max(1, round(BEAM * k)))
        got = [r.text for r in zxingcpp.read_barcodes(im)]
        out.append((msg, got[0] if got else None))
    return out


def vector_dots(dots):
    """Filled dots as concentric scored circles, BEAM apart, which burn in solid.

    A raster ENGRAVE of thousands of dots spread over a whole part runs as long
    as the part is tall, line by line; scored circles are vector and quick. So
    everything the art draws is one process: Score."""
    out = []
    for e in dots:
        r = e[2]
        while r > BEAM / 2:
            out.append(("C", e[1], round(r, 3)))
            r -= BEAM
        if not out or out[-1][1] != e[1]:
            out.append(("C", e[1], BEAM / 2))
    return out


# ── output ────────────────────────────────────────────────────────────────
def write_etch_dxf(path, score, engrave):
    L = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "0", "ENDSEC",
         "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", "2",
         "0", "LAYER", "2", "SCORE", "70", "0", "62", "5", "6", "CONTINUOUS",
         "0", "LAYER", "2", "ENGRAVE", "70", "0", "62", "7", "6", "CONTINUOUS",
         "0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    f = lambda v: f"{v:.4f}"
    for layer, ents in (("SCORE", score), ("ENGRAVE", engrave)):
        for e in ents:
            if e[0] == "L":
                L += ["0", "LINE", "8", layer, "10", f(e[1][0]), "20", f(e[1][1]), "30", "0.0",
                      "11", f(e[2][0]), "21", f(e[2][1]), "31", "0.0"]
            else:
                L += ["0", "CIRCLE", "8", layer, "10", f(e[1][0]), "20", f(e[1][1]), "30", "0.0", "40", f(e[2])]
    L += ["0", "ENDSEC", "0", "EOF"]
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


def svg_body(cut, score, engrave):
    """SVG elements in a y-up frame (the caller flips it)."""
    out = []
    for e in cut:
        if e[0] == "L":
            out.append(f'<line x1="{e[1][0]:.3f}" y1="{e[1][1]:.3f}" x2="{e[2][0]:.3f}" y2="{e[2][1]:.3f}" '
                       'stroke="#ff0000" stroke-width="0.1" fill="none"/>')
        elif e[0] == "C":
            out.append(f'<circle cx="{e[1][0]:.3f}" cy="{e[1][1]:.3f}" r="{e[2]:.3f}" '
                       'stroke="#ff0000" stroke-width="0.1" fill="none"/>')
        else:
            pts = sampled(e, 0.2)
            out.append('<polyline points="' + " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
                       + '" stroke="#ff0000" stroke-width="0.1" fill="none"/>')
    # chain end-to-start segments into polylines: one move per trace, not one per step
    chain = []

    def flush():
        if chain:
            out.append('<polyline points="' + " ".join(f"{x:.3f},{y:.3f}" for x, y in chain)
                       + '" stroke="#0000ff" stroke-width="0.1" fill="none"/>')
            chain.clear()
    for e in score:
        if e[0] == "L":
            if chain and abs(chain[-1][0] - e[1][0]) < 1e-6 and abs(chain[-1][1] - e[1][1]) < 1e-6:
                chain.append(e[2])
            else:
                flush()
                chain.extend([e[1], e[2]])
        else:
            flush()
            out.append(f'<circle cx="{e[1][0]:.3f}" cy="{e[1][1]:.3f}" r="{e[2]:.3f}" '
                       'stroke="#0000ff" stroke-width="0.1" fill="none"/>')
    flush()
    for e in engrave:
        out.append(f'<circle cx="{e[1][0]:.3f}" cy="{e[1][1]:.3f}" r="{e[2]:.3f}" fill="#000000" stroke="none"/>')
    return out


def write_svg(path, W, H, body):
    with open(path, "w") as fh:
        fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.3f}mm" height="{H:.3f}mm" '
                 f'viewBox="0 0 {W:.3f} {H:.3f}">\n<g transform="matrix(1 0 0 -1 0 {H:.3f})">\n')
        fh.write("\n".join(body))
        fh.write("\n</g>\n</svg>\n")


def preview(path, results):
    from PIL import Image, ImageDraw
    k, pad = 4.0, 16
    cells = []
    for name, (ents, allowed, score, engrave) in results.items():
        x0, y0, x1, y1 = Polygon(sampled(("C", (0, 0), 1))).bounds if not ents else (0, 0, 0, 0)
        xs = [p[0] for e in ents for p in sampled(e)]
        ys = [p[1] for e in ents for p in sampled(e)]
        cells.append((name, min(xs), min(ys), max(xs), max(ys), ents, score, engrave))
    W = int(sum((c[3] - c[1]) * k + 2 * pad for c in cells))
    H = int(max((c[4] - c[2]) * k for c in cells) + 2 * pad + 16)
    im = Image.new("RGB", (W, H), (236, 222, 196))
    d = ImageDraw.Draw(im)
    ox = 0
    for name, x0, y0, x1, y1, ents, score, engrave in cells:
        Tr = lambda p: (ox + pad + (p[0] - x0) * k, 16 + pad + (y1 - p[1]) * k)
        d.text((ox + pad, 2), name, fill=(0, 0, 0))
        for e in score:
            if e[0] == "L":
                d.line([Tr(e[1]), Tr(e[2])], fill=(70, 45, 20), width=1)
            else:
                c, r = e[1], e[2]
                d.ellipse([Tr((c[0] - r, c[1] + r)), Tr((c[0] + r, c[1] - r))], outline=(70, 45, 20))
        for e in engrave:
            c, r = e[1], e[2]
            d.ellipse([Tr((c[0] - r, c[1] + r)), Tr((c[0] + r, c[1] - r))], fill=(40, 25, 10))
        for e in ents:
            pts = [Tr(p) for p in sampled(e, 0.5)]
            d.line(pts, fill=(200, 0, 0), width=1)
        ox += int((x1 - x0) * k + 2 * pad)
    im.save(path)


DECAL_MAX = 4096                    # Onshape's decal image limit, px a side
BURN = (52, 32, 14, 235)            # what a laser score/engrave on birch looks like, roughly


def decal_png(path, ents, score, engrave):
    """The art alone, transparent, covering exactly the part's DXF frame
    (0..W, 0..H), for an Onshape Decal anchored at the face centre."""
    from PIL import Image, ImageDraw
    xs = [p[0] for e in ents for p in sampled(e)]
    ys = [p[1] for e in ents for p in sampled(e)]
    W, H = max(xs), max(ys)
    k = min(12.0, (DECAL_MAX - 2) / max(W, H))      # as fine as the decal limit allows
    im = Image.new("RGBA", (round(W * k), round(H * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    Tr = lambda p: (p[0] * k, (H - p[1]) * k)
    lw = max(1, round(0.16 * k))
    for e in score:
        if e[0] == "L":
            d.line([Tr(e[1]), Tr(e[2])], fill=BURN, width=lw)
        else:
            c, r = e[1], e[2]
            d.ellipse([Tr((c[0] - r, c[1] + r)), Tr((c[0] + r, c[1] - r))], outline=BURN, width=lw)
    # (score lines are drawn ~0.16 mm wide: about what one pass of the beam leaves)
    for e in engrave:
        c, r = e[1], e[2]
        d.ellipse([Tr((c[0] - r, c[1] + r)), Tr((c[0] + r, c[1] - r))], fill=BURN)
    im.save(path, optimize=True)
    return W, H


def check(name, ents, allowed, score, engrave):
    """(marks outside the allowed area, marks within 1.5 mm of any cut path)."""
    region = prep(allowed.buffer(0.05))
    outline, holes, knobs = part_regions(ents)
    dials = prep(unary_union([Point(k).buffer(DIAL_KEEP + 0.05) for k in knobs])) if knobs else None
    shape = lambda e, filled: (LineString([e[1], e[2]]) if e[0] == "L"
                               else Point(e[1]).buffer(e[2], 8) if filled else Point(e[1]).buffer(e[2], 8).exterior)
    bad = 0
    for e, filled in [(e, False) for e in score] + [(e, True) for e in engrave]:
        g = shape(e, filled)
        # the dials live in the knob keep-out by design
        if not region.contains(g) and not (dials and dials.contains(g)):
            bad += 1
    cutzone = prep(unary_union([LineString(sampled(e)) for e in ents]).buffer(1.5))
    near = sum(1 for e in score if cutzone.intersects(shape(e, False))) + \
        sum(1 for e in engrave if cutzone.intersects(shape(e, True)))
    return bad, near


def main():
    os.makedirs(OUT, exist_ok=True)
    results = {}
    problems = 0
    for name, seed in PARTS.items():
        ents, allowed, score, engrave = generate(name, seed)
        results[name] = (ents, allowed, score, engrave)
        stem = name[:-4]
        write_etch_dxf(os.path.join(OUT, stem + ".etch.dxf"), score, engrave)
        xs = [p[0] for e in ents for p in sampled(e)]
        ys = [p[1] for e in ents for p in sampled(e)]
        write_svg(os.path.join(OUT, stem + ".svg"), max(xs), max(ys), svg_body(ents, score, engrave))
        decal_png(os.path.join(OUT, stem + ".decal.png"), ents, score, engrave)
        bad, near = check(name, ents, allowed, score, engrave)
        problems += bad + near
        length = sum(math.dist(e[1], e[2]) if e[0] == "L" else 2 * math.pi * e[2] for e in score) / 1000
        qr = verify_qr(name, score)
        if qr is None:
            print("  (QR not verified: pip install zxing-cpp to check it decodes)")
        else:
            for want, got in qr:
                ok = got == want
                problems += 0 if ok else 1
                print(f"  QR {'decodes OK' if ok else 'FAILED'}: {want[:40]!r}" + ("" if ok else f" -> {got!r}"))
        print(f"{name:22s} score {len(score):6d} marks, {length:6.1f} m  outside-area {bad}  "
              f"within 1.5 mm of a cut {near}")
    preview(os.path.join(OUT, "preview.png"), results)
    if problems:
        sys.exit(f"{problems} etch marks too close to a cut")


if __name__ == "__main__":
    main()
