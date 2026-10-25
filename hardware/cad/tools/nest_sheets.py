#!/usr/bin/env python3
"""Nest the enclosure's part DXFs onto 12 x 24" sheets for the xTool P2.

    hardware/cad/tools/nest_sheets.py            (reads and writes hardware/laser/)

Reads the per-part DXFs that export_dxf.py wrote, and the quantities in its
MANIFEST.md, and lays every part out on five sheets, one DXF per sheet in
hardware/laser/sheets/, with a preview PNG each and a README cut list.

The layout is written down by hand below rather than searched for: it is
small, it changes rarely, and a person loading the laser wants the same part
in the same place every time. What the script does guarantee, and refuses to
write otherwise:

  * every part in MANIFEST.md is placed exactly as many times as its quantity;
  * every part lies inside the P2's 600 x 305 mm cut area with MARGIN to spare,
    and inside the 304.8 mm width of a real 12" sheet;
  * no two parts' bounding boxes come closer than GAP;
  * a part nested INSIDE another's hole (the ribs, in the inner bezel's
    display aperture, which is waste anyway) sits at least GAP inside that
    hole. Those need the laser to cut inner shapes first, xTool Creative
    Space's default; the README says so.

The sheet DXFs hold cut paths only — no sheet outline, no labels — because
the laser cuts every path it is given. The labels are in the PNGs and README.

If art.py has written etch art for a part (art/<part>.etch.dxf), it rides
along with that part, turned and moved exactly as the part is, into
sheet-N.svg: cut paths red, score lines blue, engraved dots filled black —
one file, so the art cannot drift off its part. The DXFs stay cut-only. For
software that wants the cuts and the art as separate imports, the same sheet is
also split into sheet-N-cut.svg and sheet-N-score.svg, each with identical
registration marks at the corners of the cut area (reg_marks).

Re-run after export_dxf.py whenever the model changes. If a part has grown and
no longer fits, this fails loudly; fix the layout below.
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LASER = os.path.join(HERE, "..", "..", "laser")
OUT = os.path.join(LASER, "sheets")

CUT_L, CUT_W = 600.0, 305.0      # xTool P2 cut area, mm
SHEET_L, SHEET_W = 609.6, 304.8  # 12 x 24" sheet; only 600 of its length is cuttable
MARGIN = 3.0                     # from the cut-area edge
GAP = 3.0                        # between parts
USE_W = min(CUT_W, SHEET_W)


# ── DXF in ────────────────────────────────────────────────────────────────
def read_dxf(path):
    toks = open(path).read().split("\n")
    ents, cur = [], None
    for c, v in zip(toks[0::2], toks[1::2]):
        c, v = c.strip(), v.strip()
        if c == "0":
            if cur:
                ents.append(cur)
            cur = {"type": v} if v in ("LINE", "ARC", "CIRCLE") else None
        elif cur is not None and c in ("10", "20", "11", "21", "40", "50", "51"):
            cur[c] = float(v)
    out = []
    for e in ents:
        if e["type"] == "LINE":
            out.append(("L", (e["10"], e["20"]), (e["11"], e["21"])))
        elif e["type"] == "CIRCLE":
            out.append(("C", (e["10"], e["20"]), e["40"]))
        else:
            out.append(("A", (e["10"], e["20"]), e["40"], e["50"], e["51"]))
    return out


def manifest():
    """{file: qty} from the table export_dxf.py writes."""
    q = {}
    for line in open(os.path.join(LASER, "MANIFEST.md")):
        m = re.match(r"\|\s*`([^`]+\.dxf)`\s*\|\s*(\d+)\s*\|", line)
        if m:
            q[m.group(1)] = int(m.group(2))
    return q


# ── geometry ──────────────────────────────────────────────────────────────
def rot90(ents):
    """Quarter turn anticlockwise about the origin."""
    R = lambda p: (-p[1], p[0])
    out = []
    for e in ents:
        if e[0] == "L":
            out.append(("L", R(e[1]), R(e[2])))
        elif e[0] == "C":
            out.append(("C", R(e[1]), e[2]))
        else:
            out.append(("A", R(e[1]), e[2], (e[3] + 90) % 360, (e[4] + 90) % 360))
    return out


def move(ents, dx, dy):
    T = lambda p: (p[0] + dx, p[1] + dy)
    return [(e[0], T(e[1]), T(e[2])) if e[0] == "L" else (e[0], T(e[1]), *e[2:]) for e in ents]


def bbox(ents):
    xs, ys = [], []
    for e in ents:
        if e[0] == "L":
            xs += [e[1][0], e[2][0]]
            ys += [e[1][1], e[2][1]]
            continue
        (cx, cy), r = e[1], e[2]
        if e[0] == "C":
            angs = [0, 90, 180, 270]
        else:
            a0, a1 = e[3] % 360, e[4] % 360
            sweep = (a1 - a0) % 360 or 360
            angs = [a0, a1] + [a for a in (0, 90, 180, 270) if (a - a0) % 360 <= sweep]
        for a in angs:
            xs.append(cx + r * math.cos(math.radians(a)))
            ys.append(cy + r * math.sin(math.radians(a)))
    return min(xs), min(ys), max(xs), max(ys)


def ends(e):
    if e[0] == "L":
        return [e[1], e[2]]
    if e[0] == "C":
        return []
    (cx, cy), r = e[1], e[2]
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in (e[3], e[4])]


def holes(ents):
    """Bounding boxes of a part's closed loops other than its outline, largest first."""
    par = list(range(len(ents)))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    seen = {}
    for i, e in enumerate(ents):
        for q in ends(e):
            k = (round(q[0], 3), round(q[1], 3))
            if k in seen:
                par[f(i)] = f(seen[k])
            else:
                seen[k] = i
    loops = {}
    for i, e in enumerate(ents):
        loops.setdefault(f(i), []).append(e)
    boxes = sorted((bbox(l) for l in loops.values()), key=lambda b: -(b[2] - b[0]) * (b[3] - b[1]))
    return boxes[1:]


# Parts nested in another part's hole, per sheet title: {index: (host index, hole box)}
INSIDE = {}


# ── layout ────────────────────────────────────────────────────────────────
# Sheet x runs along the 600 mm cut length, y across the 305 mm axis.
# "across" parts are turned so their long side runs across the sheet; they
# are stacked along x and centred in y. Every long part is <= 293 mm, which is
# what makes this the only orientation that works for most of them.
LAYOUT = [
    {"title": "Sheet 1 — bezel",
     "along": [("bezel-outer.dxf", True),
               ("electronics-tray-rear-sheet-board-nuts.dxf", True),
               ("panel-brace-middle.dxf", True),
               ("rail-c-tenoned.dxf", True)]},
    {"title": "Sheet 2 — back cover",
     "along": [("back-cover.dxf", True),
               ("electronics-tray-front-sheet.dxf", True),
               ("panel-brace-middle-middle-sheet-tray-nuts.dxf", True),
               ("panel-brace-upper.dxf", True)]},
    {"title": "Sheet 3 — walls",
     # the two 373 mm side walls and their doublers lie along the sheet...
     "walls": ["wall-left.dxf", "wall-right-iec.dxf",
               "wall-left-doubler.dxf", "wall-right-doubler-iec.dxf"],
     # ...with the short strips stacked beside them, also lying along...
     "beside": ["panel-brace-lower.dxf", "rail-c-tenoned.dxf"],
     # ...the spacer rings in the corner the shorter strips leave free...
     "rings": ["spacer-ring-tray-to-brace.dxf"] * 4 + ["spacer-ring-colorlight.dxf"] * 4
              + ["spacer-ring-pi-m2.5.dxf"] * 4,
     # plus spares: the 7 mm board ring is only 1.8 mm of wood round its hole
     "spares": ["spacer-ring-tray-to-brace.dxf"] * 2 + ["spacer-ring-colorlight.dxf"] * 2
               + ["spacer-ring-pi-m2.5.dxf"] * 2,
     # ...and the rest across the far end.
     "along_after_walls": [("panel-brace-middle.dxf", True),
                           ("wall-top.dxf", True),
                           ("wall-bottom.dxf", True)]},
    {"title": "Sheet 4 — inner bezel and doublers",
     "along": [("bezel-inner.dxf", True),
               ("wall-top-doubler.dxf", True),
               ("wall-bottom-doubler-psu.dxf", True),
               ("rail-a-screw-clearance.dxf", True),
               ("rail-a-screw-clearance.dxf", True),
               ("rail-b-lower-hex-pocket.dxf", True),
               ("rail-b-upper-hex-pocket.dxf", True),
               ("stiffener-shelf.dxf", True)],
     # the knob ribs, in the inner bezel's display aperture
     "inside": [("knob-rib-1.dxf", False), ("knob-rib-2.dxf", False)]},
    # 286 x 310: nothing else of that size has room left on sheets 1-4
    {"title": "Sheet 5 — back cover doubler",
     "along": [("back-cover-doubler.dxf", True)]},
]


ART_DIR = os.path.join(LASER, "art")
ART_OF = {}        # id(part entities as loaded) -> its art, in the same frame
SHEET_ART = {}     # sheet title -> {placed index: art in sheet coordinates}


def read_art(path):
    """Etch entities with their layer: ("L", p, q, layer) / ("C", c, r, layer)."""
    if not os.path.exists(path):
        return []
    toks = open(path).read().split("\n")
    ents, cur = [], None
    for c, v in zip(toks[0::2], toks[1::2]):
        c, v = c.strip(), v.strip()
        if c == "0":
            if cur:
                ents.append(cur)
            cur = {"type": v} if v in ("LINE", "CIRCLE") else None
        elif cur is not None:
            cur[c] = v if c == "8" else float(v) if c in ("10", "20", "11", "21", "40") else v
    out = []
    for e in ents:
        if e["type"] == "LINE":
            out.append(("L", (e["10"], e["20"]), (e["11"], e["21"]), e["8"]))
        else:
            out.append(("C", (e["10"], e["20"]), e["40"], e["8"]))
    return out


def art_xform(art, fn):
    """Apply a point transform to art entities, keeping radius and layer."""
    return [("L", fn(e[1]), fn(e[2]), e[3]) if e[0] == "L" else ("C", fn(e[1]), e[2], e[3]) for e in art]


def load(name, turn):
    ents = read_dxf(os.path.join(LASER, name))
    art = read_art(os.path.join(ART_DIR, name[:-4] + ".etch.dxf"))
    if turn:
        ents = rot90(ents)
        art = art_xform(art, lambda q: (-q[1], q[0]))
    x0, y0, _, _ = bbox(ents)
    moved = move(ents, -x0, -y0)
    if art:
        # keep the list itself too: it pins the id, and put() checks it is the same object
        ART_OF[id(moved)] = (moved, art_xform(art, lambda q: (q[0] - x0, q[1] - y0)))
    return moved


def size(ents):
    x0, y0, x1, y1 = bbox(ents)
    return x1 - x0, y1 - y0


def build(spec):
    placed = []                       # (name, ents) in sheet coordinates
    SHEET_ART[spec["title"]] = {}

    def put(name, ents, x, y):
        placed.append((name, move(ents, x, y)))
        own, art = ART_OF.get(id(ents), (None, None))
        if own is ents and art:
            SHEET_ART[spec["title"]][len(placed) - 1] = art_xform(art, lambda q: (q[0] + x, q[1] + y))

    x = MARGIN
    if "along" in spec:
        for name, turn in spec["along"]:
            e = load(name, turn)
            w, h = size(e)
            put(name, e, x, (USE_W - h) / 2)
            x += w + GAP
        if "inside" in spec:
            ap = holes(placed[0][1])[0]          # the host's biggest hole
            INSIDE[spec["title"]] = {}
            ix, iy, rowh = ap[0] + GAP, ap[1] + GAP, 0
            for name, turn in spec["inside"]:
                e = load(name, turn)
                w, h = size(e)
                if ix + w > ap[2] - GAP:
                    ix, iy, rowh = ap[0] + GAP, iy + rowh + GAP, 0
                INSIDE[spec["title"]][len(placed)] = (0, ap)
                put(name, e, ix, iy)
                ix += w + GAP
                rowh = max(rowh, h)
        return placed

    # Sheet 3
    y = MARGIN
    wall_len = 0
    for name in spec["walls"]:
        e = load(name, True)
        w, h = size(e)
        put(name, e, x, y)
        y += h + GAP
        wall_len = max(wall_len, w)
    strip_len = 0
    for name in spec["beside"]:
        e = load(name, False)
        w, h = size(e)
        put(name, e, x, y)
        y += h + GAP
        strip_len = max(strip_len, w)
    # rings: a grid in the corner past the strips' ends, above the walls
    walls_top = MARGIN + sum(size(load(n, True))[1] + GAP for n in spec["walls"])
    rx0, rx1 = MARGIN + strip_len + GAP, MARGIN + wall_len
    rx, ry, rowh = rx0, walls_top, 0
    for name in spec["rings"] + spec.get("spares", []):
        e = load(name, False)
        w, h = size(e)
        if rx + w > rx1:
            rx, ry, rowh = rx0, ry + rowh + GAP, 0
        put(name, e, rx, ry)
        rx += w + GAP
        rowh = max(rowh, h)
    x = MARGIN + wall_len + GAP
    for name, turn in spec["along_after_walls"]:
        e = load(name, turn)
        w, h = size(e)
        put(name, e, x, (USE_W - h) / 2)
        x += w + GAP
    return placed


# ── checks ────────────────────────────────────────────────────────────────
def check(sheets, qty):
    errs = []
    spare = {}
    for s in LAYOUT:
        for n in s.get("spares", []):
            spare[n] = spare.get(n, 0) + 1
    used = {}
    for si, placed in enumerate(sheets, 1):
        nested = INSIDE.get(LAYOUT[si - 1]["title"], {})
        for i, (host, ap) in nested.items():
            b = bbox(placed[i][1])
            if b[0] < ap[0] + GAP - 1e-6 or b[1] < ap[1] + GAP - 1e-6 or b[2] > ap[2] - GAP + 1e-6 or b[3] > ap[3] - GAP + 1e-6:
                errs.append(f"sheet {si}: {placed[i][0]} not {GAP} mm inside the hole in {placed[host][0]}")
        boxes = []
        for name, ents in placed:
            used[name] = used.get(name, 0) + 1
            b = bbox(ents)
            boxes.append((name, b))
            if b[0] < MARGIN - 1e-6 or b[1] < MARGIN - 1e-6 or b[2] > CUT_L - MARGIN + 1e-6 or b[3] > USE_W - MARGIN + 1e-6:
                errs.append(f"sheet {si}: {name} outside the cut area: {[round(v, 1) for v in b]}")
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if nested.get(j, (None,))[0] == i or nested.get(i, (None,))[0] == j:
                    continue                     # nested in the other's hole; checked above
                a, b = boxes[i][1], boxes[j][1]
                sep = max(b[0] - a[2], a[0] - b[2], b[1] - a[3], a[1] - b[3])
                if sep < GAP - 1e-6:
                    errs.append(f"sheet {si}: {boxes[i][0]} and {boxes[j][0]} {sep:.2f} mm apart")
    for name, n in qty.items():
        if used.get(name, 0) != n + spare.get(name, 0):
            errs.append(f"{name}: placed {used.get(name, 0)}, manifest says {n} + {spare.get(name, 0)} spare")
    for name in used:
        if name not in qty:
            errs.append(f"{name}: placed but not in MANIFEST.md")
    return errs


# ── out ───────────────────────────────────────────────────────────────────
def write_dxf(path, ents):
    L = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "0", "ENDSEC",
         "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", "1",
         "0", "LAYER", "2", "CUT", "70", "0", "62", "1", "6", "CONTINUOUS",
         "0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    f = lambda v: f"{v:.4f}"
    for e in ents:
        if e[0] == "L":
            L += ["0", "LINE", "8", "CUT", "10", f(e[1][0]), "20", f(e[1][1]), "30", "0.0",
                  "11", f(e[2][0]), "21", f(e[2][1]), "31", "0.0"]
        elif e[0] == "C":
            L += ["0", "CIRCLE", "8", "CUT", "10", f(e[1][0]), "20", f(e[1][1]), "30", "0.0", "40", f(e[2])]
        else:
            L += ["0", "ARC", "8", "CUT", "10", f(e[1][0]), "20", f(e[1][1]), "30", "0.0", "40", f(e[2]),
                  "50", f(e[3]), "51", f(e[4])]
    L += ["0", "ENDSEC", "0", "EOF"]
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


REG = 2.0           # mm, arm of each registration mark
REG_COLOUR = "#00a000"


def reg_marks(W, H):
    """An L at each corner of the W x H working area, pointing in: the same in a
    sheet's cut file and its score file, so both have the same bounding box and
    line up exactly when aligned in the laser software. Inside the margin every
    part keeps from the edge, so they touch nothing."""
    out = []
    for cx, cy, sx, sy in ((0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1), (W, H, -1, -1)):
        for dx, dy in ((REG * sx, 0), (0, REG * sy)):
            out.append(f'<line x1="{cx:.3f}" y1="{cy:.3f}" x2="{cx + dx:.3f}" y2="{cy + dy:.3f}" '
                       f'stroke="{REG_COLOUR}" stroke-width="0.1" fill="none"/>')
    return out


def write_split_svgs(stem, page, area, cut, score, engrave):
    """stem-cut.svg and stem-score.svg: the cuts alone and the art alone, on the
    same page, each with the same registration marks round `area` (W, H)."""
    from art import svg_body, write_svg       # art.py imports this module; import late
    write_svg(stem + "-cut.svg", *page, svg_body(cut, [], []) + reg_marks(*area))
    write_svg(stem + "-score.svg", *page, svg_body([], score, engrave) + reg_marks(*area))


def write_sheet_svg(path, ents, arts):
    from art import svg_body, write_svg       # art.py imports this module; import late
    score = [e[:3] for a in arts for e in a if e[3] == "SCORE"]
    engrave = [e[:3] for a in arts for e in a if e[3] == "ENGRAVE"]
    write_svg(path, SHEET_L, SHEET_W, svg_body(ents, score, engrave))
    if score or engrave:
        write_split_svgs(path[:-4], (SHEET_L, SHEET_W), (CUT_L, USE_W), ents, score, engrave)


def preview(path, title, placed, labels, arts=None):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return
    k, pad = 2.0, 20
    W, H = int(SHEET_L * k) + 2 * pad, int(SHEET_W * k) + 2 * pad + 24
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    T = lambda p: (pad + p[0] * k, 24 + pad + (SHEET_W - p[1]) * k)
    d.rectangle([T((0, SHEET_W)), T((SHEET_L, 0))], outline=(190, 190, 190))       # the sheet
    d.rectangle([T((0, CUT_W)), T((CUT_L, 0))], outline=(120, 170, 255))           # the cut area
    d.text((pad, 4), title.replace("—", "-") + "   (grey: 12 x 24 sheet, blue: P2 cut area 600 x 305)", fill=(0, 0, 0))
    for a in (arts or {}).values():
        for e in a:
            if e[0] == "L":
                d.line([T(e[1]), T(e[2])], fill=(150, 110, 60))
            elif e[3] == "ENGRAVE":
                c, r = e[1], max(e[2], 0.5)
                d.ellipse([T((c[0] - r, c[1] + r)), T((c[0] + r, c[1] - r))], fill=(150, 110, 60))
            else:
                c, r = e[1], e[2]
                d.ellipse([T((c[0] - r, c[1] + r)), T((c[0] + r, c[1] - r))], outline=(150, 110, 60))
    for (name, ents), lab in zip(placed, labels):
        for e in ents:
            if e[0] == "L":
                d.line([T(e[1]), T(e[2])], fill="black")
            else:
                c, r = e[1], e[2]
                box = [T((c[0] - r, c[1] + r)), T((c[0] + r, c[1] - r))]
                if e[0] == "C":
                    d.ellipse(box, outline="red")
                else:
                    d.arc(box, -e[4], -e[3], fill="red")
        if lab:
            x0, y0, x1, y1 = bbox(ents)
            d.text(T(((x0 + x1) / 2 - 3, (y0 + y1) / 2 + 2)), lab, fill=(0, 0, 200))
    im.save(path)


PART = {  # file -> what to call it on the cut sheet
    "bezel.dxf": "Bezel",
    "bezel-outer.dxf": "Bezel, outer (front face)",
    "bezel-inner.dxf": "Bezel, inner (glued behind the outer; knob pockets)",
    "wall-left-doubler.dxf": "Wall left doubler (glued inside)",
    "wall-right-doubler-iec.dxf": "Wall right doubler, IEC cutout (glued inside)",
    "wall-bottom-doubler-psu.dxf": "Wall bottom doubler, PSU holes (glued inside)",
    "wall-top-doubler.dxf": "Wall top doubler (glued inside)",
    "back-cover.dxf": "Back cover",
    "back-cover-doubler.dxf": "Back cover doubler (glued inside the cover, between the rails)",
    "electronics-tray-front-sheet.dxf": "Electronics tray, front sheet",
    "electronics-tray-rear-sheet-board-nuts.dxf": "Electronics tray, rear sheet (board nuts)",
    "panel-brace-middle.dxf": "Panel brace middle (front or rear sheet; identical)",
    "panel-brace-middle-middle-sheet-tray-nuts.dxf": "Panel brace middle, middle sheet (tray nuts)",
    "panel-brace-upper.dxf": "Panel brace upper",
    "panel-brace-lower.dxf": "Panel brace lower",
    "wall-left.dxf": "Wall left",
    "wall-right-iec.dxf": "Wall right (IEC cutout)",
    "wall-top.dxf": "Wall top",
    "wall-bottom.dxf": "Wall bottom",
    "rail-c-tenoned.dxf": "Rail C, tenoned (upper or lower; identical)",
    "rail-a-screw-clearance.dxf": "Rail A, screw clearance (upper or lower; identical)",
    "rail-b-lower-hex-pocket.dxf": "Rail B lower, hex pockets",
    "rail-b-upper-hex-pocket.dxf": "Rail B upper, hex pockets",
    "stiffener-web.dxf": "Stiffener web",
    "stiffener-shelf.dxf": "Stiffener shelf (props the knob band under the aperture)",
    "knob-rib-1.dxf": "Knob rib 1, between the knob columns (cable holes)",
    "knob-rib-2.dxf": "Knob rib 2, between the knobs and the PSU",
    "spacer-ring-tray-to-brace.dxf": "Spacer ring, tray to brace (8 mm)",
    "spacer-ring-board.dxf": "Spacer ring, board (7 mm)",
    "spacer-ring-colorlight.dxf": "Spacer ring, Colorlight (7 mm, M3 bore)",
    "spacer-ring-pi-m2.5.dxf": "Spacer ring, Pi 5 (7 mm, M2.5 bore)",
}


def main():
    qty = manifest()
    sheets = [build(s) for s in LAYOUT]
    errs = check(sheets, qty)
    if errs:
        print("\n".join(errs))
        sys.exit("layout does not fit — nothing written")
    os.makedirs(OUT, exist_ok=True)
    md = [f"# Cut sheets — the enclosure on {len(LAYOUT)} 12 × 24\" sheets", "",
          "Generated by `hardware/cad/tools/nest_sheets.py` from the part DXFs one level up — "
          "do not edit by hand; re-run `export_dxf.py` and then this after any model change.", "",
          f"- **Material:** 3 mm Baltic birch, B/BB, 12 × 24\" (304.8 × 609.6 mm). Caliper it: the "
          f"model is cut for `#thickness` 3.18 and `#kerf` 0.15, as set from the test cuts.",
          f"- **Placement:** the P2 cuts {CUT_L:.0f} × {CUT_W:.0f} mm, so a 24\" sheet overhangs the "
          f"cut area by {SHEET_L - CUT_L:.1f} mm at one end. Every part is at least {MARGIN:.0f} mm inside "
          f"the cut area and {GAP:.0f} mm from its neighbours. Each DXF's origin is the corner of the "
          "cut area; put the sheet's corner there.",
          "- **Inner shapes first.** The knob ribs are nested inside the inner bezel's display "
          "aperture on sheet 4. xTool Creative Space cuts inner shapes before outer ones by default; "
          "keep it that way, or the aperture drops out with the ribs still in it.",
          "- **Cut paths only.** No sheet outline or labels in the DXFs — the laser would cut them. "
          "Use the pictures below to tell the parts apart as they come off.",
          "- **Etched art (sheets 1–3).** The outer faces — bezel, side walls, top wall, back cover — "
          "carry a circuit-board pattern from `art.py`. To etch, load **`sheet-N.svg`** instead of the "
          "DXF: one file, so the art stays on its part. In xTool Creative Space assign processing **by "
          "colour**: **red = Cut**, **blue = Score** — all of the art, dots included (they are tight "
          "concentric circles that burn in solid: a raster engrave of thousands of dots would run "
          "line by line over the whole part). Make sure the score runs **before** the cut, so nothing "
          "has moved when the art goes on: each colour imports as its own layer, so drag the blue "
          "layer above the red one and set the processing order to **by layer**. XCS does not keep "
          "settings with a colour, only with the objects, so set both layers up once per sheet and "
          "save that as a project (.xcs) to reopen, rather than re-importing. **Or import the cuts and "
          "the art separately**, `sheet-N-cut.svg` and `sheet-N-score.svg`: both carry the same green "
          "L-marks at the corners of the cut area, so the two imports are the same size — select both, "
          "**align left** and **align bottom**, and they are registered; then delete the green marks "
          "(they sit in the 3 mm border, clear of every part, so nothing is lost if one is left in). "
          "It is a lot of "
          "line: ~101 m on the back cover, ~23 m on the bezel, ~10–12 m per wall — budget roughly "
          "20–30 min for sheet 2 and 5–15 for sheets 1 and 3 at a typical score speed. Set the score "
          "settings on test piece 16 first (`../test-cuts/since-rev-1/`): you want a fine, even, light "
          "line and a QR code that scans. The art faces up on the bed, which "
          "is the outside face. Skip it by loading the DXF instead: same cuts.",
          "- **Cut the test sheet first** ([`../test-cuts/`](../test-cuts/README.md), a 12 × 12) if you "
          "haven't, or after any change of stock.",
          "- **Good face up, and don't mirror anything.** Every part is drawn as seen from outside the "
          "box, so the face that is up on the bed becomes the outside: the bezel's front, each wall's "
          "outer face, the back of the back cover. Mask that face (transfer tape) against smoke marks; "
          "the face against the honeycomb, with its flash-back marks, ends up inside.",
          f"- **Buy {len(LAYOUT) + 2}:** {len(LAYOUT)} for the box, one 12 × 12 for the test cuts, "
          "one spare for a recut.",
          "- **Rev 2:** the bezel, every wall and (rev 2.3) the back cover are two sheets, the second glued on (PVA, clamped flat) "
          "before the box goes together — `docs/desktop/enclosure-lasercut.md` §2.", ""]
    for si, (spec, placed) in enumerate(zip(LAYOUT, sheets), 1):
        all_ents = [e for _, ents in placed for e in ents]
        dxf = f"sheet-{si}.dxf"
        write_dxf(os.path.join(OUT, dxf), all_ents)
        arts = SHEET_ART.get(spec["title"], {})
        write_sheet_svg(os.path.join(OUT, f"sheet-{si}.svg"), all_ents, list(arts.values()))
        counts, order = {}, []
        for name, _ in placed:
            if name not in counts:
                order.append(name)
            counts[name] = counts.get(name, 0) + 1
        num = {n: i + 1 for i, n in enumerate(x for x in order if not x.startswith("spacer-ring"))}
        labels = [str(num[n]) if not n.startswith("spacer-ring") else "" for n, _ in placed]
        png = f"sheet-{si}.png"
        preview(os.path.join(OUT, png), spec["title"], placed, labels, arts)
        x1 = max(bbox(e)[2] for _, e in placed)
        y0 = min(bbox(e)[1] for _, e in placed)
        y1 = max(bbox(e)[3] for _, e in placed)
        md += [f"## {spec['title']} — `{dxf}`", "",
               f"Parts span {x1 - MARGIN:.1f} × {y1 - y0:.1f} mm.", "",
               f"![{spec['title']}]({png})", "", "| # | Part | Qty | From |", "|---|---|---|---|"]
        for n in order:
            md.append(f"| {num[n] if not n.startswith('spacer-ring') else '—'} | {PART.get(n, n)} | "
                      f"{counts[n]} | `{n}` |")
        md.append("")
        print(f"{dxf}: {len(placed)} parts, {len(all_ents)} entities, span {x1:.1f} x {y1 - y0:.1f}")
    md += ["## Totals", "", "| Part | Qty | Sheet |", "|---|---|---|"]
    where = {}
    for si, placed in enumerate(sheets, 1):
        for name, _ in placed:
            where.setdefault(name, [])
            if si not in where[name]:
                where[name].append(si)
    for name, n in qty.items():
        md.append(f"| {PART.get(name, name)} | {n} | {', '.join(map(str, where[name]))} |")
    nsp = sum(len(s.get("spares", [])) for s in LAYOUT)
    md += ["", f"**{sum(qty.values())} parts on {len(LAYOUT)} sheets**, plus {nsp} spare spacer rings on sheet 3 "
           "(the 7 mm board ring is only 1.8 mm of wood round its hole).", ""]
    with open(os.path.join(OUT, "README.md"), "w") as fh:
        fh.write("\n".join(md))


if __name__ == "__main__":
    main()
