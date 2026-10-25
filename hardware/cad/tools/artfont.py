"""Laser-scored text in two faces, by size.

Under BIG (1.3 mm cap height), a tiny single-stroke font on a 4 x 6 grid
(y up; each glyph a list of polylines; characters advance 6 units, 4 wide + 2
space, so text of height h is h per char). Scored, a stroke is one pass of the
beam: legible down to ~0.8 mm on birch, where any filled face breaks up. The
silkscreen designators, chip names and hidden words are this size.

From BIG up, JetBrains Mono Medium (fonts/, SIL OFL): each glyph's outline is
flattened and filled with horizontal score lines FILL apart, a little closer
than the beam is wide, so it burns in solid like the QR codes, with one pass
round its edge. The fill is inset half a beam so the burn lands on the drawn
outline; strokes too thin for that inset are filled without it, both ways. The
title block and the credits plate are this size.

text() returns score segments [("L", p, q)], width() the rendered width. To try
another face, point FONT at any TTF/OTF (a variable font takes AXES).
"""
import functools
import os

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "JetBrainsMono.ttf")
AXES = {"wght": 500}     # Medium
BIG = 1.3                # mm cap height: from here up, text is set in FONT
BEAM = 0.15              # what one scored line burns (art.py's BEAM)
FILL = 0.12              # fill pitch: under the beam, so it burns in solid

G = {
    "0": [[(0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0), (0, 1)], [(0, 1), (4, 5)]],
    "1": [[(1, 5), (2, 6), (2, 0)], [(1, 0), (3, 0)]],
    "2": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (0, 0), (4, 0)]],
    "3": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (1, 3)],
          [(3, 3), (4, 2), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "4": [[(3, 0), (3, 6), (0, 2), (4, 2)]],
    "5": [[(4, 6), (0, 6), (0, 3), (3, 3), (4, 2), (4, 1), (3, 0), (0, 0)]],
    "6": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "7": [[(0, 6), (4, 6), (1, 0)]],
    "8": [[(1, 3), (0, 4), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (1, 3), (0, 2), (0, 1), (1, 0),
           (3, 0), (4, 1), (4, 2), (3, 3)]],
    "9": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3), (4, 3)]],
    "A": [[(0, 0), (0, 4), (2, 6), (4, 4), (4, 0)], [(0, 3), (4, 3)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(3, 3), (4, 2), (4, 1), (3, 0), (0, 0)]],
    "C": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1)]],
    "D": [[(0, 0), (0, 6), (2, 6), (4, 4), (4, 2), (2, 0), (0, 0)]],
    "E": [[(4, 6), (0, 6), (0, 0), (4, 0)], [(0, 3), (3, 3)]],
    "F": [[(4, 6), (0, 6), (0, 0)], [(0, 3), (3, 3)]],
    "G": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1), (4, 3), (2, 3)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(1, 6), (3, 6)], [(2, 6), (2, 0)], [(1, 0), (3, 0)]],
    "J": [[(4, 6), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "K": [[(0, 0), (0, 6)], [(4, 6), (0, 2)], [(1, 3), (4, 0)]],
    "L": [[(0, 6), (0, 0), (4, 0)]],
    "M": [[(0, 0), (0, 6), (2, 3), (4, 6), (4, 0)]],
    "N": [[(0, 0), (0, 6), (4, 0), (4, 6)]],
    "O": [[(1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0)]],
    "P": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]],
    "Q": [[(1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0)], [(2, 2), (4, 0)]],
    "R": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(2, 3), (4, 0)]],
    "S": [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3), (3, 3), (4, 2), (4, 1), (3, 0), (1, 0), (0, 1)]],
    "T": [[(0, 6), (4, 6)], [(2, 6), (2, 0)]],
    "U": [[(0, 6), (0, 1), (1, 0), (3, 0), (4, 1), (4, 6)]],
    "V": [[(0, 6), (2, 0), (4, 6)]],
    "W": [[(0, 6), (1, 0), (2, 3), (3, 0), (4, 6)]],
    "X": [[(0, 0), (4, 6)], [(0, 6), (4, 0)]],
    "Y": [[(0, 6), (2, 3), (4, 6)], [(2, 3), (2, 0)]],
    "Z": [[(0, 6), (4, 6), (0, 0), (4, 0)]],
    "-": [[(1, 3), (3, 3)]],
    ".": [[(1.6, 0), (2.4, 0), (2.4, 0.8), (1.6, 0.8), (1.6, 0)]],
    "/": [[(0, 0), (4, 6)]],
    ":": [[(1.6, 1), (2.4, 1), (2.4, 1.8), (1.6, 1.8), (1.6, 1)], [(1.6, 4), (2.4, 4), (2.4, 4.8), (1.6, 4.8), (1.6, 4)]],
    "#": [[(1, 0), (1, 6)], [(3, 0), (3, 6)], [(0, 2), (4, 2)], [(0, 4), (4, 4)]],
    "+": [[(2, 1), (2, 5)], [(0, 3), (4, 3)]],
    "_": [[(0, 0), (4, 0)]],
    "=": [[(0, 2), (4, 2)], [(0, 4), (4, 4)]],
    ">": [[(0, 6), (4, 3), (0, 0)]],
    "<": [[(4, 6), (0, 3), (4, 0)]],
    "[": [[(3, 6), (1, 6), (1, 0), (3, 0)]],
    "]": [[(1, 6), (3, 6), (3, 0), (1, 0)]],
    "*": [[(2, 1), (2, 5)], [(0, 2), (4, 4)], [(0, 4), (4, 2)]],
    "'": [[(2, 6), (2, 4.5)]],
    "@": [[(3, 2), (3, 4), (1.5, 4), (1, 3.5), (1, 2.5), (1.5, 2), (3, 2), (4, 2.5), (4, 5), (3, 6), (1, 6),
           (0, 5), (0, 1), (1, 0), (4, 0)]],
    " ": [],
}


class _Flatten(BasePen):
    """Glyph outline -> closed polylines (font units)."""

    def __init__(self, glyphset, steps=8):
        super().__init__(glyphset)
        self.rings, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, a, b, c):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append(tuple(u ** 3 * p0[j] + 3 * u * u * t * a[j] + 3 * u * t * t * b[j] + t ** 3 * c[j]
                                  for j in (0, 1)))

    def _qCurveToOne(self, a, b):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append(tuple(u * u * p0[j] + 2 * u * t * a[j] + t * t * b[j] for j in (0, 1)))

    def _closePath(self):
        if len(self.cur) > 2:
            self.rings.append(self.cur)
        self.cur = []

    _endPath = _closePath


@functools.lru_cache(maxsize=None)
def _font():
    f = TTFont(FONT)
    if "fvar" in f:
        from fontTools.varLib import instancer
        f = instancer.instantiateVariableFont(f, AXES)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    adv = gs[cmap[ord("0")]].width
    return gs, cmap, f["OS/2"].sCapHeight, adv


def _hatch(region, vertical=False):
    out = []
    if region.is_empty:
        return out
    x0, y0, x1, y1 = region.bounds
    lo, hi = (x0, x1) if vertical else (y0, y1)
    v = lo + FILL / 2
    while v < hi:
        cut = LineString([(v, y0 - 1), (v, y1 + 1)] if vertical else [(x0 - 1, v), (x1 + 1, v)])
        clip = region.intersection(cut)
        for g in getattr(clip, "geoms", [clip]):
            if g.geom_type == "LineString" and g.length > 0.02:
                cs = list(g.coords)
                out.append((cs[0], cs[-1]))
        v += FILL
    return out


def _winding(p, ring):
    """Winding number of closed ring round point p."""
    w = 0
    x, y = p
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        if y0 <= y < y1 and (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0) > 0:
            w += 1
        elif y1 <= y < y0 and (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0) < 0:
            w -= 1
    return w


def _nonzero(rings):
    """The area a set of contours fills under the nonzero rule, as TrueType does.

    A variable font keeps overlapping and even self-intersecting contours (its
    8 is two of them), so node every edge into faces and keep each face whose
    winding number is not zero."""
    if not rings:
        return Polygon()
    edges = unary_union([LineString(r + r[:1]) for r in rings])
    keep = [f for f in polygonize(edges) if sum(_winding(f.representative_point().coords[0], r) for r in rings)]
    return unary_union(keep) if keep else Polygon()


@functools.lru_cache(maxsize=None)
def _glyph(ch, h):
    """Score segments for one character at cap height h, origin at its baseline-left."""
    gs, cmap, cap, _ = _font()
    name = cmap.get(ord(ch)) or cmap.get(ord("?"))
    pen = _Flatten(gs)
    gs[name].draw(pen)
    k = h / cap
    rings = [[(x * k, y * k) for x, y in ring] for ring in pen.rings]
    shape = _nonzero(rings)
    if shape.is_empty:
        return ()
    core = shape.buffer(-BEAM / 2)
    thin = shape.difference(core.buffer(BEAM / 2 + 0.01)) if not core.is_empty else shape
    segs = []
    for g in getattr(core, "geoms", [core]):
        if g.is_empty:
            continue
        for ring in [g.exterior] + list(g.interiors):
            cs = list(ring.simplify(0.01).coords)
            segs += list(zip(cs, cs[1:]))
    segs += _hatch(core)
    if thin.area > 1e-4:
        segs += _hatch(thin) + _hatch(thin, vertical=True)
    return tuple(segs)


def _grid_text(s, x, y, h):
    k = h / 6
    out = []
    for i, ch in enumerate(s.upper()):
        for stroke in G.get(ch, G["*"]):
            pts = [(x + (6 * i + px) * k, y + py * k) for px, py in stroke]
            out += [("L", a, b) for a, b in zip(pts, pts[1:])]
    return out


def advance(h):
    """Distance from one character to the next at cap height h."""
    if h < BIG:
        return h
    _, _, cap, adv = _font()
    return adv * h / cap


def width(s, h):
    """Rendered width of s at cap height h (no trailing space)."""
    if h < BIG:
        return max(0.0, (6 * len(s) - 2) * h / 6)
    return max(0.0, (len(s) - 0.15) * advance(h))


def text(s, x, y, h, anchor="left"):
    """Score segments [("L", p, q)] for s, baseline-left at (x, y) unless anchored 'center'."""
    if anchor == "center":
        x -= width(s, h) / 2
        y -= h / 2
    if h < BIG:
        return _grid_text(s, x, y, h)
    a = advance(h)
    out = []
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        ox = x + i * a
        out += [("L", (ox + p[0], y + p[1]), (ox + q[0], y + q[1])) for p, q in _glyph(ch, round(h, 4))]
    return out
