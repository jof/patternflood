"""Laser-scored text: IBM Plex Mono Medium for anything 1.3 mm tall or more,
Hershey Sans 1-stroke below that.

Each glyph's outline (fonts/, SIL OFL) is flattened and filled with horizontal
score lines FILL apart, a little closer than the beam is wide, so it burns in
solid like the QR codes, with one pass round its edge for a crisp outline. The
fill is inset half a beam so the burn lands on the drawn outline. Strokes too
thin to survive that inset (small text) are filled without it, both ways, so
they burn a touch bold rather than vanish.

Under STROKE_BELOW a filled face is only a few scan lines tall and breaks up, so
small text (the silkscreen designators, the hidden words) is set the way a real
PCB's silkscreen is: in a single-stroke plotter font, one beam pass per stroke
(Hershey Sans 1-stroke, fonts/HersheySans1.svg, its acknowledgements in the
file). Legible down to ~0.8 mm.

Same interface as before: text() returns score segments [("L", p, q)], width()
the advance. To try another face, point FONT at any TTF/OTF (a variable font
takes AXES); the layout follows its metrics.
"""
import functools
import os
import re

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "IBMPlexMono-Medium.ttf")
AXES = {}                # e.g. {"wght": 450, "wdth": 100} for a variable font
STROKE = os.path.join(HERE, "fonts", "HersheySans1.svg")
STROKE_BELOW = 1.3       # mm cap height: smaller text is set in the stroke font
BEAM = 0.15              # what one scored line burns (art.py's BEAM)
FILL = 0.12              # fill pitch: under the beam, so it burns in solid


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


@functools.lru_cache(maxsize=None)
def _glyph(ch, h):
    """Score segments for one character at cap height h, origin at its baseline-left."""
    gs, cmap, cap, _ = _font()
    name = cmap.get(ord(ch)) or cmap.get(ord("?"))
    pen = _Flatten(gs)
    gs[name].draw(pen)
    k = h / cap
    shape = Polygon()
    for ring in pen.rings:            # nonzero/even-odd alike for these fonts: XOR the contours
        shape = shape.symmetric_difference(Polygon([(x * k, y * k) for x, y in ring]).buffer(0))
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


class _Lines(_Flatten):
    """A stroke glyph's path -> open polylines (font units)."""

    def _closePath(self):
        if len(self.cur) > 1:
            self.rings.append(self.cur)
        self.cur = []

    _endPath = _closePath

    def _moveTo(self, p):
        self._closePath()
        self.cur = [p]


@functools.lru_cache(maxsize=None)
def _stroke_font():
    """{char: (polylines in font units, advance)}, and the cap height (the H's top)."""
    from fontTools.svgLib.path import parse_path
    src = open(STROKE).read()
    ents = {"&amp;": "&", "&quot;": '"', "&lt;": "<", "&gt;": ">", "&apos;": "'"}
    glyphs = {}
    for m in re.finditer(r"<glyph\b([^>]*)>", src):
        a = m.group(1)
        u = re.search(r'unicode="([^"]*)"', a)
        if not u:
            continue
        ch = ents.get(u.group(1), u.group(1))
        if len(ch) != 1:
            continue
        d = re.search(r'\bd="([^"]*)"', a)
        pen = _Lines(None, steps=6)
        if d:
            parse_path(d.group(1), pen)
            pen._closePath()
        lines = pen.rings
        if ch in ".,:;":      # Hershey's sit 94.5 up, reading as a middle dot: drop them onto the baseline
            lines = [[(px, py - 94.5) for px, py in line] for line in lines]
        glyphs[ch] = (lines, float(re.search(r'horiz-adv-x="([\d.]+)"', a).group(1)))
    cap = max(p[1] for line in glyphs["H"][0] for p in line)
    return glyphs, cap


def _stroked(s, x, y, h):
    glyphs, cap = _stroke_font()
    k = h / cap
    out = []
    for ch in s:
        lines, adv = glyphs.get(ch, glyphs["?"])
        for line in lines:
            pts = [(x + px * k, y + py * k) for px, py in line]
            out += [("L", a, b) for a, b in zip(pts, pts[1:])]
        x += adv * k
    return out


def advance(h):
    """Distance from one character to the next at cap height h (the filled, monospaced face)."""
    _, _, cap, adv = _font()
    return adv * h / cap


def width(s, h):
    """Rendered width of s at cap height h (no trailing space)."""
    if h < STROKE_BELOW:
        glyphs, cap = _stroke_font()
        return sum(glyphs.get(ch, glyphs["?"])[1] for ch in s) * h / cap
    return max(0.0, (len(s) - 0.15) * advance(h))


def text(s, x, y, h, anchor="left"):
    """Score segments [("L", p, q)] for s, baseline-left at (x, y) unless anchored 'center'."""
    if anchor == "center":
        x -= width(s, h) / 2
        y -= h / 2
    if h < STROKE_BELOW:
        return _stroked(s, x, y, h)
    a = advance(h)
    out = []
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        ox = x + i * a
        out += [("L", (ox + p[0], y + p[1]), (ox + q[0], y + q[1])) for p, q in _glyph(ch, round(h, 4))]
    return out
