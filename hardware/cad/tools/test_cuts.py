#!/usr/bin/env python3
"""Generate the pre-project test cuts: small pieces that validate every critical
dimension of the enclosure before a full sheet is committed.

    hardware/cad/tools/test_cuts.py [out_dir]      (default hardware/laser/test-cuts/)

Values come live from the Onshape Variable Studio (evaluated, so derived
expressions resolve), and the board hole patterns from the constants in
enclosure.fs — the same sources the model uses — and every kerf rule here is the
model's own:

    finger slots   shrunk kerf/2 at each interior end          (cutFingers)
    tenons         grown kerf/2 per side; mortises shrunk      (braces, rail C)
    hex pockets    across-flats - kerf                          (hexPrism calls)
    round holes    diameter - kerf, except the rail/brace clearance (screwDia + 0.5)
                   and the knob bores (boreDia), which are drawn uncompensated

Where a test sweeps a value, each variant is engraved with it (layer SCORE,
blue); the cut paths are on layer CUT (red). Nothing but holes, outlines and
those labels is drawn, so every path is safe to cut even where the laser
software ignores layers — closed label digits just drop out as small holes.
One DXF per piece, plus
all-test-cuts.dxf with everything laid out on one 12 x 12" sheet, plus a
preview and a README saying what each piece is for and which variable it sets.
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import export_dxf as X  # noqa: E402  (curl, plain, ids)

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "laser", "test-cuts")
FS = os.path.join(HERE, "..", "featurescript", "enclosure.fs")
SHEET = 300.0          # usable square on a 12" (304.8) sheet
GAP = 3.0

VARS = ["kerf", "thickness", "screwDia", "nutAcrossFlats", "boreDia", "pinHoleDia", "pinSlotLen",
        "pinXOffset", "pinYOffset", "postXOffset", "braceYOffset", "midPostYOffset", "slotW", "slotLen",
        "psuHoleDia", "psuHoleAX", "psuHoleBX", "iecCutW", "iecCutH", "iecScrewSpacing", "iecScrewDia",
        "iecFlangeEnd", "iecFlangeTip", "fingerLen", "railW", "pinDia"]


def fetch_vars():
    names = ", ".join('"%s"' % n for n in VARS)
    script = ('function(context is Context, queries) { var out = {}; for (var n in [%s]) '
              '{ out[n] = getVariable(context, n) / millimeter; } return out; }' % names)
    d = X.curl("POST", f"{X.API}/partstudios/d/{X.DID}/w/{X.WID}/e/{X.PS}/featurescript",
               {"script": script, "queries": {}})
    return {k: round(v, 6) for k, v in X.plain(d["result"]).items()}


def fs_const(src, name):
    m = re.search(r"const %s\s*=\s*([^;]+);" % name, src)
    return json.loads(re.sub(r"//[^\n]*", "", m.group(1)))


# ── geometry: entities are tuples ending in a layer name ──────────────────
CUT, SCORE = "CUT", "SCORE"


def line(a, b, layer=CUT):
    return [("L", a, b, layer)]


def poly(pts, layer=CUT):
    return [("L", pts[i], pts[(i + 1) % len(pts)], layer) for i in range(len(pts))]


def rect(x0, y0, x1, y1, layer=CUT):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer)


def circle(cx, cy, d, layer=CUT):
    return [("C", (cx, cy), d / 2, layer)]


def obround(cx, cy, r, travel, layer=CUT):
    a, b = cx - travel / 2, cx + travel / 2
    return [("A", (b, cy), r, -90.0, 90.0, layer), ("A", (a, cy), r, 90.0, 270.0, layer),
            ("L", (a, cy + r), (b, cy + r), layer), ("L", (a, cy - r), (b, cy - r), layer)]


def hexagon(cx, cy, af, layer=CUT):
    R = af / math.sqrt(3)       # corners on +-x, flats parallel to x, as hexPrism
    return poly([(cx + R * math.cos(math.radians(60 * i)), cy + R * math.sin(math.radians(60 * i)))
                 for i in range(6)], layer)


def rotated_rect(cx, cy, L, W, ang, layer):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    pts = [(-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2)]
    return poly([(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts], layer)


# 7-segment stroke font, cell 0..1 wide, 0..2 tall: a top, b upper right,
# c lower right, d bottom, e lower left, f upper left, g middle
SEG = {"a": ((0, 2), (1, 2)), "b": ((1, 2), (1, 1)), "c": ((1, 1), (1, 0)), "d": ((0, 0), (1, 0)),
       "e": ((0, 0), (0, 1)), "f": ((0, 1), (0, 2)), "g": ((0, 1), (1, 1))}
GLYPH = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
         "7": "abc", "8": "abcdefg", "9": "abcdfg", "-": "g", "A": "abcefg", "B": "cdefg", "C": "adef",
         "P": "abefg"}


def text(s, x, y, h=3.0, layer=SCORE, centre=True):
    w, adv = h / 2 * 0.6, h / 2 * 0.95
    width = sum(adv * (0.45 if ch == "." else 1) for ch in s)
    x0 = x - width / 2 if centre else x
    out = []
    for ch in s:
        if ch == ".":
            out += line((x0 + 0.05 * h, y), (x0 + 0.15 * h, y), layer)
            x0 += adv * 0.45
            continue
        for sg in GLYPH.get(ch, ""):
            (ax, ay), (bx, by) = SEG[sg]
            out += line((x0 + ax * w, y + ay * h / 2), (x0 + bx * w, y + by * h / 2), layer)
        x0 += adv
    return out


def fmt(v):
    return ("%.2f" % v).rstrip("0").rstrip(".") if abs(v - round(v)) > 1e-9 else "%d" % round(v)


def shift(ents, dx, dy):
    out = []
    for e in ents:
        if e[0] == "L":
            out.append(("L", (e[1][0] + dx, e[1][1] + dy), (e[2][0] + dx, e[2][1] + dy), e[3]))
        else:
            out.append((e[0], (e[1][0] + dx, e[1][1] + dy)) + tuple(e[2:]))
    return out


def bbox(ents):
    xs, ys = [], []
    for e in ents:
        if e[0] == "L":
            xs += [e[1][0], e[2][0]]; ys += [e[1][1], e[2][1]]
        else:
            xs += [e[1][0] - e[2], e[1][0] + e[2]]; ys += [e[1][1] - e[2], e[1][1] + e[2]]
    return min(xs), min(ys), max(xs), max(ys)


def normalise(ents):
    x0, y0, x1, y1 = bbox(ents)
    return shift(ents, -x0, -y0), (x1 - x0, y1 - y0)


# ── the pieces ────────────────────────────────────────────────────────────
def finger_plate(W, H, t, n, k, phase, edge_top):
    """One side of a corner joint, exactly as cutFingers makes it."""
    step = W / n
    gone = []
    for i in range(n):
        if i % 2 != phase:
            continue
        a = i * step + (k / 2 if i > 0 else 0)
        b = (i + 1) * step - (k / 2 if i < n - 1 else 0)
        gone.append((a, b))
    # walk the joint edge left to right as (x, depth)
    prof, x = [], 0.0
    for a, b in gone:
        if a > x:
            prof += [(x, 0), (a, 0)]
        prof += [(a, t), (b, t)]
        x = b
    if x < W:
        prof += [(x, 0), (W, 0)]
    if edge_top:
        edge = [(px, H - d) for px, d in prof]
        pts = [(0, 0), (W, 0)] + edge[::-1]
    else:
        edge = [(px, d) for px, d in prof]
        pts = edge + [(W, H), (0, H)]
    # drop repeated points
    clean = []
    for p in pts:
        if not clean or math.dist(clean[-1], p) > 1e-9:
            clean.append(p)
    if math.dist(clean[0], clean[-1]) < 1e-9:
        clean.pop()
    return poly(clean)


def piece_comb(v, ks):
    t, n, W, H = v["thickness"], 5, 5 * v["fingerLen"], 22.0
    ents, x = [], 0.0
    for k in ks:
        a = finger_plate(W, H, t, n, k, 0, True)                  # tabs up
        b = shift(finger_plate(W, H, t, n, k, 1, False), 0, H + 4)  # tabs down, cut apart
        lab = fmt(k)
        ents += shift(a + text(lab, W / 2, 7) + b + text(lab, W / 2, H + 4 + 12), x, 0)
        x += W + 5
    return ents


def piece_tenon(v, ks):
    t, w = v["thickness"], v["railW"]
    ents = []
    pitch = w + 7
    plate_w = len(ks) * pitch + 4
    ents += rect(0, 0, plate_w, 24)
    for i, k in enumerate(ks):
        cx = 4 + i * pitch + w / 2
        ents += rect(cx - (w - k) / 2, 14 - (t - k) / 2, cx + (w - k) / 2, 14 + (t - k) / 2)   # mortise
        ents += text(fmt(k), cx, 3.5)
    y = 28
    for i, k in enumerate(ks):
        cx = 4 + i * pitch + w / 2
        ents += rect(cx - (w + k) / 2, y, cx + (w + k) / 2, y + 26)                          # tenon strip
        ents += text(fmt(k), cx, y + 11)
    return ents


def piece_hex(v, afs):
    pitch = 11.0
    W = len(afs) * pitch + 4
    ents = rect(0, 0, W, 21)
    for i, af in enumerate(afs):
        cx = 2 + pitch / 2 + i * pitch
        ents += hexagon(cx, 13.5, af)
        ents += text(fmt(af), cx, 2.5, h=2.6)
    return ents


def piece_sandwich(v):
    clr = v["screwDia"] + 0.5                   # clrR in the model: screwDia/2 + 0.25, uncompensated
    af = v["nutAcrossFlats"] - v["kerf"]
    ents = []
    for i, (kind, lab) in enumerate((("clr", "1"), ("hex", "2"), ("clr", "3"))):
        x = i * 19
        ents += rect(x, 0, x + 16, 16)
        ents += hexagon(x + 8, 9.5, af) if kind == "hex" else circle(x + 8, 9.5, clr)
        ents += text(lab, x + 8, 1.5, h=2.6)
    return ents


def piece_holes(v, rows):
    pitch, rowh = 14.0, 16.0
    cols = max(len(r[1]) for r in rows)
    W, H = 12 + cols * pitch, len(rows) * rowh + 2
    ents = rect(0, 0, W, H)
    for ri, (lab, ds) in enumerate(rows):
        y = H - (ri + 1) * rowh + 1
        ents += text(lab, 5, y + 7, h=3.2)
        for ci, d in enumerate(ds):
            cx = 12 + pitch / 2 + ci * pitch
            ents += circle(cx, y + 9.5, d)
            ents += text(fmt(d), cx, y + 1.5, h=2.4)
    return ents


def piece_panel_jig(v):
    """The upper brace's footprint on ONE panel, 127 wide = the panel's rear face.
    Panel-local, front view; symmetric in x, so it reads the same from behind."""
    k = v["kerf"]
    y0, y1 = 20.0, 63.5                      # top edge flush with the panel's rear top edge
    ents = rect(-63.5, y0, 63.5, y1)
    pr = v["pinHoleDia"] / 2 - k / 2
    sr = v["slotW"] / 2 - k / 2
    for sx in (-1, 1):
        ents += obround(sx * v["pinXOffset"], v["pinYOffset"], pr, v["pinSlotLen"])
        # the brace's screw slots run on into the next panel's; on a one-panel
        # jig a round hole of the slot's width checks the insert just as well
        ents += circle(sx * v["postXOffset"], v["braceYOffset"], 2 * sr)
    ents += circle(0, v["midPostYOffset"], 3.5)                   # mid-edge insert, a sight hole
    ents += poly([(-40, y1 - 7), (-32, y1 - 7), (-36, y1 - 3)])         # points at the pin (top) edge
    ents += text("6", 0, y0 + 3)
    return ents


def piece_board(W, H, holes, d, label, lab_at, lab_h):
    """Board footprint + 4 mm, its mounting holes, its number. Nothing else:
    the holes alone locate the board, and anything more would be cut."""
    m = 4.0
    ents = rect(-m, -m, W + m, H + m)
    for hx, hy in holes:
        ents += circle(hx, hy, d)
    return ents + text(label, lab_at[0], lab_at[1], h=lab_h)


def piece_iec(v):
    k = v["kerf"]
    w, h = v["iecCutW"], v["iecCutH"]
    hl, hs, tp = w / 2 + v["iecFlangeEnd"], h / 2, h / 2 + v["iecFlangeTip"]
    W, H = 2 * hl + 12, 2 * tp + 12
    cx, cy = W / 2, H / 2
    ents = rect(0, 0, W, H)
    ents += rect(cx - (w - k) / 2, cy - (h - k) / 2, cx + (w - k) / 2, cy + (h - k) / 2)
    for s in (-1, 1):
        ents += circle(cx, cy + s * v["iecScrewSpacing"] / 2, v["iecScrewDia"] - k)
    ents += text("9", 5, 2)
    return ents


def piece_psu(v):
    d = v["psuHoleDia"] - v["kerf"]
    ents = rect(0, 0, 100, 16)
    for hx in (v["psuHoleAX"], v["psuHoleBX"]):
        ents += circle(hx, 8, d)
    ents += poly([(2.5, 8), (6, 5.5), (6, 10.5)])                    # points at the terminal end
    ents += text("10", 50, 5)
    return ents


# ── output ────────────────────────────────────────────────────────────────
def write_dxf(path, ents):
    L = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "0", "ENDSEC",
         "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", "2",
         "0", "LAYER", "2", CUT, "70", "0", "62", "1", "6", "CONTINUOUS",
         "0", "LAYER", "2", SCORE, "70", "0", "62", "5", "6", "CONTINUOUS",
         "0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    f = lambda q: f"{q:.4f}"
    for e in ents:
        lay = e[-1]
        if e[0] == "L":
            L += ["0", "LINE", "8", lay, "10", f(e[1][0]), "20", f(e[1][1]), "30", "0.0",
                  "11", f(e[2][0]), "21", f(e[2][1]), "31", "0.0"]
        elif e[0] == "C":
            L += ["0", "CIRCLE", "8", lay, "10", f(e[1][0]), "20", f(e[1][1]), "30", "0.0", "40", f(e[2])]
        else:
            L += ["0", "ARC", "8", lay, "10", f(e[1][0]), "20", f(e[1][1]), "30", "0.0", "40", f(e[2]),
                  "50", f(e[3] % 360), "51", f(e[4] % 360)]
    L += ["0", "ENDSEC", "0", "EOF"]
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


def render(path, ents, size, k=3.0):
    from PIL import Image, ImageDraw
    W, H = size
    im = Image.new("RGB", (int(W * k) + 20, int(H * k) + 20), "white")
    d = ImageDraw.Draw(im)
    T = lambda p: (10 + p[0] * k, 10 + (H - p[1]) * k)
    for e in ents:
        col = (200, 0, 0) if e[-1] == CUT else (0, 80, 220)
        if e[0] == "L":
            d.line([T(e[1]), T(e[2])], fill=col)
        else:
            c, r = e[1], e[2]
            box = [T((c[0] - r, c[1] + r)), T((c[0] + r, c[1] - r))]
            if e[0] == "C":
                d.ellipse(box, outline=col)
            else:
                d.arc(box, -e[4], -e[3], fill=col)
    im.save(path)


def rotate90(ents):
    out = []
    for e in ents:
        if e[0] == "L":
            out.append(("L", (-e[1][1], e[1][0]), (-e[2][1], e[2][0]), e[3]))
        elif e[0] == "C":
            out.append(("C", (-e[1][1], e[1][0]), e[2], e[3]))
        else:
            out.append(("A", (-e[1][1], e[1][0]), e[2], e[3] + 90, e[4] + 90, e[5]))
    return normalise(out)


def pack(pieces):
    """Bottom-left skyline packing onto a SHEET-wide strip, largest first, each
    piece tried both ways round. Returns {i: (x, y, rotated)} and the height used."""
    sky = [(0.0, SHEET, 0.0)]                 # (x0, x1, height) segments
    placed = {}

    def fit(w):
        best = None
        for si in range(len(sky)):
            x0 = sky[si][0]
            if x0 + w > SHEET + 1e-9:
                break
            top, x1 = 0.0, x0 + w
            for sx0, sx1, sh in sky:
                if sx1 > x0 + 1e-9 and sx0 < x1 - 1e-9:
                    top = max(top, sh)
            if best is None or top < best[1] - 1e-9:
                best = (x0, top)
        return best

    order = sorted(range(len(pieces)), key=lambda i: -pieces[i]["size"][0] * pieces[i]["size"][1])
    for i in order:
        w, h = pieces[i]["size"]
        cands = []
        for rot, (pw, ph) in ((False, (w, h)), (True, (h, w))):
            f = fit(pw + GAP)
            if f:
                cands.append((f[1] + ph, f[0], f[1], rot, pw, ph))
        _, x, y, rot, pw, ph = min(cands)
        placed[i] = (x, y, rot)
        top, x1 = y + ph + GAP, x + pw + GAP
        new = []
        for sx0, sx1, sh in sky:
            if sx1 <= x or sx0 >= x1:
                new.append((sx0, sx1, sh))
            else:
                if sx0 < x:
                    new.append((sx0, x, sh))
                if sx1 > x1:
                    new.append((x1, sx1, sh))
        new.append((x, x1, top))
        sky = sorted(new)
    used = max(placed[i][1] + (pieces[i]["size"][0] if placed[i][2] else pieces[i]["size"][1])
               for i in placed)
    return placed, used


def main():
    v = fetch_vars()
    src = open(FS).read()
    C = {n: fs_const(src, n) for n in ("CL_W", "CL_H", "CL_HOLES", "CL_HUBS", "CL_HUB_L", "CL_HUB_W",
                                         "CL_RJ45", "PI_W", "PI_H", "PI_HOLES", "PI_EDGE_PARTS")}
    k = v["kerf"]
    kerfs = [0.0, 0.1, 0.15, 0.2, 0.25, 0.3]
    afs = [5.1, 5.2, 5.3, 5.4, 5.5, 5.6]
    board_hole = v["screwDia"] + 0.5 - k        # trayClrR*2 - kerf: the tray's board holes


    pieces = [
        dict(id=1, file="01-kerf-finger-comb.dxf", ents=piece_comb(v, kerfs),
             title="Kerf: finger-joint pairs",
             test="Six pairs of finger plates, compensated exactly as the box corners are, one pair per kerf value "
                  f"({', '.join(fmt(q) for q in kerfs)} mm, engraved on both plates). Push each pair's finger "
                  "edges together, in plane and then at 90° like a box corner.",
             read="The pair that goes together with a firm hand press and holds without glue is your kerf. "
                  "Loose → the kerf is bigger than that label; won't go in → smaller. The finger depth is "
                  f"#thickness ({fmt(v['thickness'])}): at 90° the tabs should finish flush — proud or "
                  "short means the sheet isn't that thickness.",
             var="#kerf (and #thickness)"),
        dict(id=2, file="02-kerf-tenon-mortise.dxf", ents=piece_tenon(v, kerfs),
             title="Kerf: through-tenon and mortise",
             test=f"A wall coupon with six mortises and six {fmt(v['railW'])} mm tenon strips, one per kerf value, "
                  "compensated as the braces and rail C are (tenon +kerf, mortise −kerf, in both directions).",
             read="Push each strip into the mortise with the same label. It should agree with test 1; this "
                  "one also checks the sheet thickness against the mortise's short side.",
             var="#kerf"),
        dict(id=3, file="03-hex-nut-pockets.dxf", ents=piece_hex(v, afs),
             title="Captive nut: hex pocket sweep",
             test="Six hex pockets drawn at " + ", ".join(fmt(a) for a in afs) + " mm across flats. The model "
                  f"cuts {fmt(v['nutAcrossFlats'] - k)} (#nutAcrossFlats {fmt(v['nutAcrossFlats'])} − kerf).",
             read="Drop an M3 nut into each. You want the smallest pocket it still drops into by hand and in "
                  "which it can't turn. Set #nutAcrossFlats so that #nutAcrossFlats − #kerf equals that "
                  "label.",
             var="#nutAcrossFlats"),
        dict(id=4, file="04-captive-nut-sandwich.dxf", ents=piece_sandwich(v),
             title="Captive nut: the three-layer sandwich",
             test=f"Three 16 mm squares: 1 clearance Ø{fmt(v['screwDia'] + 0.5)}, 2 hex "
                  f"{fmt(v['nutAcrossFlats'] - k)} AF, 3 clearance — the stack every nut in the box sits in "
                  "(rails, middle brace, tray).",
             read="Stack 1-2-3 with a nut in 2, drive an M3 x 8 through 3. The nut should not spin, should pull "
                  "up tight against 1, and should stay put when the screw is backed out.",
             var="#nutAcrossFlats, #screwDia"),
        dict(id=5, file="05-hole-gauge.dxf",
             ents=piece_holes(v, [("1", [3.0, 3.2, 3.4, 3.6, 3.8]), ("2", [2.7, 2.8, 2.9, 3.0, 3.1]),
                                  ("3", [6.8, 7.0, 7.2, 7.4, 7.6]), ("4", [4.1, 4.3, 4.5, 4.7])]),
             title="Hole gauge (labels are the DRAWN diameter)",
             test="Row 1: M3 clearance. Row 2: panel registration pin (Ø2.83–2.87). Row 3: EC11 encoder bushing "
                  "(the knob bore). Row 4: PSU side-screw clearance. Each hole is engraved with the diameter "
                  "drawn; the cut comes out about one kerf bigger.",
             read=f"Row 1: the smallest an M3 passes freely — the model draws {fmt(v['screwDia'] - k)} for the "
                  f"back cover and {fmt(v['screwDia'] + 0.5)} in the rails and braces. Row 2: the one the pin "
                  f"drops into with no play — the model draws {fmt(v['pinHoleDia'] - k)}. Row 3: the encoder "
                  f"bushing should pass and not wobble — the model draws {fmt(v['boreDia'])}. Row 4: the model "
                  f"draws {fmt(v['psuHoleDia'] - k)}, deliberately loose (±0.75 mm for the PSU's hole "
                  "tolerance).",
             var="#screwDia, #pinHoleDia, #boreDia, #psuHoleDia"),
        dict(id=6, file="06-panel-fit-jig.dxf", ents=piece_panel_jig(v),
             title="Panel fit jig",
             test="The upper brace's footprint on one panel: 127 wide, the panel's rear width. Registration pin "
                  f"holes at (±{fmt(v['pinXOffset'])}, {fmt(v['pinYOffset'])}), screw slots at "
                  f"(±{fmt(v['postXOffset'])}, {fmt(v['braceYOffset'])}), and a sight hole over the mid-edge "
                  f"insert at (0, {fmt(v['midPostYOffset'])}). The triangle points at the pin (top) edge.",
             read="Lay it on a panel's back, flush with the rear top and side edges. Both pins should drop into "
                  "their holes with no rocking, both inserts should sit inside their slots (M3 screws go in "
                  "square), and the insert should be centred in the sight hole.",
             var="#pinXOffset, #pinYOffset, #postXOffset, #braceYOffset, #midPostYOffset"),
        dict(id=7, file="07-colorlight-template.dxf",
             ents=piece_board(C["CL_W"], C["CL_H"], C["CL_HOLES"], board_hole, "7", (C["CL_W"] / 2, 60), 6),
             title="Colorlight 5A-75B template",
             test="The card's footprint plus 4 mm, with its four mounting holes at the positions measured off "
                  "the scans, at the tray's hole size. The RJ45 end is the end with the two holes 5 mm in from "
                  "the corners.",
             read="Set the card on it component side up. All four M3 screws should go through card and template "
                  "together. If one doesn't, the scan is off at that hole — measure it and correct CL_HOLES in "
                  "enclosure.fs.",
             var="CL_HOLES (enclosure.fs)"),
        dict(id=8, file="08-pi-zero-template.dxf",
             ents=piece_board(C["PI_W"], C["PI_H"], C["PI_HOLES"], board_hole, "8", (C["PI_W"] / 2, 14), 3),
             title="Pi Zero 2 W template",
             test="The board's footprint plus 4 mm, with the four 58 × 23 mounting holes at the tray's hole size.",
             read="With the Pi's holes opened to 3.2, an M3 should go through all four. (Or check the pattern with "
                  "M2.5 before drilling.)",
             var="PI_HOLES (enclosure.fs)"),
        dict(id=9, file="09-iec-cutout.dxf", ents=piece_iec(v),
             title="IEC inlet cutout",
             test=f"The {fmt(v['iecCutW'])} × {fmt(v['iecCutH'])} cutout and its two flange screw holes "
                  f"{fmt(v['iecScrewSpacing'])} apart, as cut in the right wall.",
             read="The inlet body should pass with a slight drag and the flange sit flat around it; "
                  "M3 screws through both lobes. Mains part — do not skip this one.",
             var="#iecCutW, #iecCutH, #iecScrewSpacing, #iecScrewDia"),
        dict(id=10, file="10-psu-side-holes.dxf", ents=piece_psu(v),
             title="PSU side-screw holes",
             test=f"A strip with the two holes {fmt(v['psuHoleBX'] - v['psuHoleAX'])} apart, at "
                  f"{fmt(v['psuHoleAX'])} and {fmt(v['psuHoleBX'])} from the end the triangle points at — the "
                  "PSU's terminal end.",
             read="Hold it on the PSU's threaded side face, that end flush with the terminal end: two M3 x 12 "
                  "should thread in square.",
             var="#psuHoleAX, #psuHoleBX, #psuHoleDia"),
    ]

    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".dxf") or f.endswith(".png"):
            os.remove(os.path.join(OUT, f))
    for p in pieces:
        p["ents"], p["size"] = normalise(p["ents"])
        write_dxf(os.path.join(OUT, p["file"]), p["ents"])

    placed, used = pack(pieces)
    sheet = []
    for i, p in enumerate(pieces):
        x, y, rot = placed[i]
        ents = rotate90(p["ents"])[0] if rot else p["ents"]
        sheet += shift(ents, x, y)
    write_dxf(os.path.join(OUT, "all-test-cuts.dxf"), sheet)
    render(os.path.join(OUT, "preview.png"), shift(sheet, 1.5, 1.5), (SHEET + 3, used + 3))

    md = ["# Test cuts — validate before the full sheet", "",
          "Generated by `hardware/cad/tools/test_cuts.py` from the live Variable Studio and the board data "
          "in `enclosure.fs`; re-run after changing either.", "",
          f"Everything below fits one 12 × 12\" sheet (`all-test-cuts.dxf`, {fmt(SHEET)} × {fmt(used)} mm), "
          "or cut the pieces singly. Every path is safe to cut: outlines and holes on layer **CUT** (red), the "
          "engraved numbers on layer **SCORE** (blue) — set blue to a light engrave if your laser software maps "
          "by colour; if it cuts everything, the digits just come out as small slots and holes. Cut them in the "
          "same 3 mm Baltic birch as the box, with the same laser settings you'll use for the real parts, or "
          "the numbers mean nothing.", "",
          "**Order:** caliper the sheet's thickness first, then tests 1–2 to settle **#kerf** (everything "
          "else is compensated by it), set the variables, re-run this script, and cut the rest.", "",
          "Values used for this cut: " + ", ".join(f"`#{n}` {fmt(v[n])}" for n in
                                                   ("kerf", "thickness", "screwDia", "nutAcrossFlats", "boreDia",
                                                    "pinHoleDia", "psuHoleDia")) + ".", "",
          "![Test sheet](preview.png)", ""]
    for p in pieces:
        md += [f"## {p['id']}. {p['title']} — `{p['file']}`", "",
               f"**Cut:** {p['test']}", "", f"**Read:** {p['read']}", "", f"**Sets:** {p['var']}", ""]
    md += ["## Not cuttable — measure", "",
           "- **Sheet thickness** — calipers, several places on the sheet you'll cut. Finger depth and every "
           "mortise follow `#thickness`.",
           "- **EC11 bushing thread length** — measured 5.5 mm (2026-10-18): it clamps one sheet, so the "
           "bezel is one sheet.", ""]
    with open(os.path.join(OUT, "README.md"), "w") as fh:
        fh.write("\n".join(md))
    for p in pieces:
        print(f"{p['file']:30s} {p['size'][0]:6.1f} x {p['size'][1]:6.1f}  ents {len(p['ents'])}")
    print(f"sheet: {fmt(SHEET)} x {fmt(used)} mm" + ("  ** OVERFLOWS 12in **" if used > SHEET else ""))


if __name__ == "__main__":
    main()
