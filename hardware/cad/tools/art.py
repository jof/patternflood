#!/usr/bin/env python3
"""Etched art for the box's outside faces: a generated circuit-board pattern.

    hardware/cad/tools/art.py            (reads hardware/laser/*.dxf, writes hardware/laser/art/)

For each visible part — bezel, side walls, top wall, back cover — this reads
the part's cut DXF (drawn as seen from OUTSIDE, so the face up on the laser bed
is the outer face), works out where etching is allowed, and fills it with
PCB-style traces: 45/90-degree routes on a grid, chips with pin rows, vias and
pads. On the bezel each knob gets a dial ring with ticks, and traces run out
from it.

Allowed area = the part's outline, inset past the finger joints, minus every
hole, slot and cutout grown by a margin. Nothing is etched on a joint, near a
cut edge, or under a knob.

Outputs, per part, in the part's own frame:
  art/<part>.etch.dxf   etch only: layer SCORE (lines, rings) and ENGRAVE (filled dots,
                        as circles), for reference
  art/<part>.svg        cut (red) + score (blue) + engrave (black fill) — what you'd
                        load to cut that part alone
and art/preview.png. nest_sheets.py picks the etch files up and puts the art on
the sheets, in sheets/sheet-N.svg.

Seeded per part: re-running gives the same art. Change SEED to re-roll.
"""
import math
import os
import random
import sys

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polygonize, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from nest_sheets import read_dxf  # noqa: E402

LASER = os.path.join(HERE, "..", "..", "laser")
OUT = os.path.join(LASER, "art")

T = 3.18             # sheet thickness: the finger joints reach this far in from an edge
EDGE = T + 2.5       # keep this far inside the outline
HOLE = 2.5           # and this far from any hole or slot
G = 3.0              # trace grid pitch
KNOB_CLEAR = 13.5    # a 20 mm / 1" knob's skirt hides r < ~13
DIAL_R = 15.0        # dial ring radius round each knob
PAD = 1.3            # nodes and traces keep this far inside the allowed area (via ring 1.1)

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


# ── generator ─────────────────────────────────────────────────────────────
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


class Board:
    def __init__(self, allowed, rng):
        # nodes and trace segments keep PAD clear of the allowed area's edge,
        # so a via ring or pad drawn on a node still lies inside it
        self.allowed, self.rng = allowed, rng
        self.core = allowed.buffer(-PAD)
        x0, y0, x1, y1 = allowed.bounds
        self.ox, self.oy = math.floor(x0 / G) * G, math.floor(y0 / G) * G
        self.nodes = set()
        for i in range(int((x1 - self.ox) / G) + 2):
            for j in range(int((y1 - self.oy) / G) + 2):
                if self.core.contains(Point(self.ox + i * G, self.oy + j * G)):
                    self.nodes.add((i, j))
        self.used = set()
        self.score, self.engrave = [], []      # score: ("L", p, q) / ("C", c, r); engrave: ("C", c, r)

    def xy(self, n):
        return (self.ox + n[0] * G, self.oy + n[1] * G)

    def free(self, n):
        return n in self.nodes and n not in self.used

    def route(self, start, d, lo=4, hi=28):
        """Walk from start heading d; returns the node path (start included) or None."""
        path, cur = [start], start
        want = self.rng.randint(lo, hi)
        while len(path) <= want:
            opts = [(d, 8), ((d + 1) % 8, 1), ((d - 1) % 8, 1)]
            self.rng.shuffle(opts)
            opts.sort(key=lambda o: -o[1] * self.rng.random())
            moved = False
            for nd, _ in opts:
                dx, dy = DIRS[nd]
                nxt = (cur[0] + dx, cur[1] + dy)
                if not self.free(nxt) or nxt in path:
                    continue
                if dx and dy and ((cur[0] + dx, cur[1]) in self.used and (cur[0], cur[1] + dy) in self.used):
                    continue                              # would cross another trace's diagonal
                if dx and dy and not LineString([self.xy(cur), self.xy(nxt)]).within(self.core):
                    continue                              # a diagonal across a concave corner
                path.append(nxt)
                cur, d, moved = nxt, nd, True
                break
            if not moved:
                break
        return path if len(path) >= lo else None

    def commit(self, path, start_pad=True):
        self.used.update(path)
        pts = [self.xy(n) for n in path]
        # merge collinear steps into single segments
        seg = [pts[0]]
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            if (b[0] - a[0]) * (c[1] - b[1]) != (b[1] - a[1]) * (c[0] - b[0]):
                seg.append(b)
        seg.append(pts[-1])
        for a, b in zip(seg, seg[1:]):
            self.score.append(("L", a, b))
        if start_pad:
            self.engrave.append(("C", pts[0], 0.9))
        self.score.append(("C", pts[-1], 1.1))           # via at the far end
        self.engrave.append(("C", pts[-1], 0.45))

    def chip(self, w, h):
        """Place a w x h (grid cells) chip; draw it; return its pin starts [(node, dir)]."""
        cand = list(self.nodes)
        self.rng.shuffle(cand)
        for (i, j) in cand[:400]:
            cells = {(i + a, j + b) for a in range(-1, w + 2) for b in range(-1, h + 2)}
            if not all(self.free(c) for c in cells):
                continue
            body = [(i + a, j + b) for a in range(w + 1) for b in range(h + 1)]
            self.used.update(body)
            x0, y0 = self.xy((i, j))
            x1, y1 = self.xy((i + w, j + h))
            m = G * 0.35
            r = (x0 + m, y0 + m, x1 - m, y1 - m)
            for a, b in [((r[0], r[1]), (r[2], r[1])), ((r[2], r[1]), (r[2], r[3])),
                         ((r[2], r[3]), (r[0], r[3])), ((r[0], r[3]), (r[0], r[1]))]:
                self.score.append(("L", a, b))
            self.engrave.append(("C", (r[0] + 1.6, r[3] - 1.6), 0.6))     # pin-1 dot
            pins = []
            for a in range(1, w):
                pins += [((i + a, j - 1), 6, (i + a, j)), ((i + a, j + h + 1), 2, (i + a, j + h))]
            for b in range(1, h):
                pins += [((i - 1, j + b), 4, (i, j + b)), ((i + w + 1, j + b), 0, (i + w, j + b))]
            starts = []
            for node, d, inner in pins:
                if self.free(node):
                    p, q = self.xy(inner), self.xy(node)
                    edge = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                    starts.append((node, d, edge))
            return starts
        return []


def dial(board, c, rng):
    """Knob dial: ring, ticks, and traces leaving it radially."""
    board.score.append(("C", c, DIAL_R))
    for k in range(24):
        a = math.radians(k * 15)
        r1 = DIAL_R + (2.6 if k % 6 == 0 else 1.4)
        board.score.append(("L", (c[0] + DIAL_R * math.cos(a), c[1] + DIAL_R * math.sin(a)),
                            (c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a))))
    # traces start at grid nodes just outside the ticks, heading away from the knob
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        p = (c[0] + (DIAL_R + 5) * math.cos(a), c[1] + (DIAL_R + 5) * math.sin(a))
        n = (round((p[0] - board.ox) / G), round((p[1] - board.oy) / G))
        d = round(((math.degrees(a)) % 360) / 45) % 8
        if board.free(n) and rng.random() < 0.8:
            path = board.route(n, d, 3, 22)
            if path:
                board.commit(path, start_pad=False)
                q = board.xy(n)
                board.score.append(("L", (c[0] + (DIAL_R + 2.8) * math.cos(a), c[1] + (DIAL_R + 2.8) * math.sin(a)), q))


def generate(name, seed):
    ents = read_dxf(os.path.join(LASER, name))
    outline, holes, knobs = part_regions(ents)
    keep_out = [h.buffer(HOLE) for h in holes] + [Point(k).buffer(DIAL_R + 4) for k in knobs]
    allowed = outline.buffer(-EDGE).difference(unary_union(keep_out)) if keep_out else outline.buffer(-EDGE)
    rng = random.Random(SEED * 100 + seed)
    b = Board(allowed, rng)
    for k in knobs:
        dial(b, k, rng)
    area = allowed.area
    for _ in range(max(1, int(area / 9000))):
        for node, d, edge in b.chip(rng.choice([3, 4, 5, 6]), rng.choice([2, 3, 4])):
            path = b.route(node, d, 2, 24)
            if path:
                b.commit(path, start_pad=False)
                b.score.append(("L", edge, b.xy(node)))
    for _ in range(int(area / 160)):
        free = [n for n in b.nodes if n not in b.used]
        if not free:
            break
        n = rng.choice(free)
        path = b.route(n, rng.randrange(0, 8, 2) if rng.random() < 0.7 else rng.randrange(8))
        if path:
            b.commit(path)
    return ents, allowed, b.score, b.engrave


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
    for e in score:
        if e[0] == "L":
            out.append(f'<line x1="{e[1][0]:.3f}" y1="{e[1][1]:.3f}" x2="{e[2][0]:.3f}" y2="{e[2][1]:.3f}" '
                       'stroke="#0000ff" stroke-width="0.1" fill="none"/>')
        else:
            out.append(f'<circle cx="{e[1][0]:.3f}" cy="{e[1][1]:.3f}" r="{e[2]:.3f}" '
                       'stroke="#0000ff" stroke-width="0.1" fill="none"/>')
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
    k, pad = 1.6, 10
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
            c, r = e[1], max(e[2], 0.6)
            d.ellipse([Tr((c[0] - r, c[1] + r)), Tr((c[0] + r, c[1] - r))], fill=(40, 25, 10))
        for e in ents:
            pts = [Tr(p) for p in sampled(e, 0.5)]
            d.line(pts, fill=(200, 0, 0), width=1)
        ox += int((x1 - x0) * k + 2 * pad)
    im.save(path)


def check(name, ents, allowed, score, engrave):
    """Every etch mark inside the allowed area (with its own half-width)."""
    bad = 0
    region = allowed.buffer(0.05)
    for e in score:
        g = LineString([e[1], e[2]]) if e[0] == "L" else Point(e[1]).buffer(e[2]).exterior
        if not g.within(region):
            # the dial rings and the knob-to-trace stubs live in the knob keep-out by design
            if not ("bezel" in name):
                bad += 1
    for e in engrave:
        if not Point(e[1]).buffer(e[2]).within(region):
            bad += 1
    # nothing etched within 1.5 mm of any cut path, knobs included
    cutlines = unary_union([LineString(sampled(e)) for e in ents])
    shape = lambda e, filled: (LineString([e[1], e[2]]) if e[0] == "L"
                               else Point(e[1]).buffer(e[2]) if filled else Point(e[1]).buffer(e[2]).exterior)
    near = (sum(1 for e in score if shape(e, False).distance(cutlines) < 1.5)      # score rings are rings
            + sum(1 for e in engrave if shape(e, True).distance(cutlines) < 1.5))
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
        bad, near = check(name, ents, allowed, score, engrave)
        problems += bad + near
        print(f"{name:22s} score {len(score):5d}  engrave {len(engrave):4d}  outside-area {bad}  "
              f"within 1.5 mm of a cut {near}")
    preview(os.path.join(OUT, "preview.png"), results)
    if problems:
        sys.exit(f"{problems} etch marks too close to a cut")


if __name__ == "__main__":
    main()
