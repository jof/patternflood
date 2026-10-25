#!/usr/bin/env python3
"""Test cuts for what has changed since the last ones were cut.

    hardware/cad/tools/test_cuts_delta.py [out_dir]   (default hardware/laser/test-cuts/since-rev-1/)

The full set (test_cuts.py) was cut and measured on 2026-10-18, and Rev 1 was
built from it on 2026-10-20, which proved everything it had. This is one
small sheet for the fit-critical things added or changed since, so the box can
be cut with confidence without re-cutting what is already known:

  12, 13  a knob, as the bezel cuts it: the outer sheet's bore and light slits
          with its etched dial, and the inner sheet's 35 mm pocket (rev 2 made
          the bezel two sheets; rev 2.1 added the slits) — real geometry,
          cropped out of the bezel DXFs
   8      the Pi 5 template and its M2.5 nut pockets (rev 2)
  17      the Pi's M2.5 spacer rings (rev 2), out of the sheet DXF
  11      the push buttons' keyed holes (rev 2.2)
  10, 14  the PSU screw strip at the new #psuHoleDia, and the matching
          outer-sheet strip with the head recesses, to stack under it (rev 2.3+)
  15      a hole gauge for the new holes: cleat, PSU clamp, head recess
  16      the etch: a crop of the back cover's credits plate, with its QR code
          and plate lettering, to set the Score process on before 100 m of it

Pieces 8, 10 and 11 are test_cuts.py's own. Writes one DXF per piece, the sheet
as a DXF (cut + engraved labels only, safe to cut even if the laser ignores
layers) and as an SVG with the art too (cut red, score blue), a preview, and a
README listing every change since rev 1 and how it is covered. Needs what art.py
needs (it re-runs the back cover's art to find the credits plate).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import art  # noqa: E402
import test_cuts as T  # noqa: E402
from nest_sheets import read_art, read_dxf  # noqa: E402

LASER = os.path.join(HERE, "..", "..", "laser")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(LASER, "test-cuts", "since-rev-1")
CUT, SCORE, ART = T.CUT, T.SCORE, "ART"
BAND = 7.0                     # mm, a label strip under the cropped coupons, clear of their art


def ends(e):
    if e[0] == "L":
        return [e[1], e[2]]
    if e[0] == "A":
        pts = art.sampled(e[:5])
        return [pts[0], pts[-1]]
    return []


def loops_inside(ents, x0, y0, x1, y1):
    """The closed cut paths lying wholly inside the box: entities are joined by
    shared ends, and a path is kept only if every part of it is inside."""
    key = lambda p: (round(p[0], 2), round(p[1], 2))
    parent = list(range(len(ents)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    at = {}
    for i, e in enumerate(ents):
        for p in ends(e):
            j = at.setdefault(key(p), i)
            parent[find(i)] = find(j)
    inside = lambda e: all(x0 < x < x1 and y0 < y < y1 for x, y in art.sampled(e[:5] if e[0] == "A" else e))
    ok = {}
    for i, e in enumerate(ents):
        r = find(i)
        ok[r] = ok.get(r, True) and inside(e)
    return [e for i, e in enumerate(ents) if ok[find(i)]]


def art_inside(etch, x0, y0, x1, y1, m=1.5):
    """Etch marks wholly inside the box inset by m (none near the coupon's cut edge)."""
    out = []
    for e in etch:
        pts = [e[1], e[2]] if e[0] == "L" else [(e[1][0] + dx * e[2], e[1][1] + dy * e[2])
                                                 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        if all(x0 + m < x < x1 - m and y0 + m < y < y1 - m for x, y in pts):
            out.append(e[:3] + (ART,))
    return out


def coupon(part, etch_part, x0, y0, x1, y1, label):
    """A rectangle of a real part: its cut paths inside, its etch, and an
    outline with a label strip below."""
    cut = [e + (CUT,) for e in loops_inside(read_dxf(os.path.join(LASER, part)), x0, y0, x1, y1)]
    etch = art_inside(read_art(os.path.join(LASER, "art", etch_part)), x0, y0, x1, y1) if etch_part else []
    ents = cut + etch + T.rect(x0, y0 - BAND, x1, y1) + T.text(label, (x0 + x1) / 2, y0 - BAND + 1.8)
    return ents


def piece_psu_recess(v, d):
    """Piece 10's strip again, with the outer sheet's head recesses."""
    ents = T.rect(0, 0, 100, 16)
    for hx in (v["psuHoleAX"], v["psuHoleBX"]):
        ents += T.circle(hx, 8, d)
    ents += T.poly([(1.2, 8), (3.6, 6.4), (3.6, 9.6)])           # smaller: the recess comes to x 6.3
    ents += T.text("14", 50, 5)
    return ents


def ring_pair(name):
    e = read_dxf(os.path.join(LASER, name))
    one = [x + (CUT,) for x in e]
    w = T.bbox(one)[2] - T.bbox(one)[0]
    return one + T.shift(one, w + 3, 0)


def main():
    v = T.fetch_vars()
    C = T.board_consts()
    src = open(T.FS).read()
    K = {n: T.fs_const(src, n) for n in ("PSU_HEAD_RECESS", "CLEAT_HOLE", "KNOB_SLITS", "KNOB_SLIT_W")}
    k, t = v["kerf"], v["thickness"]
    base = {p["id"]: p for p in T.all_pieces(v, C)}

    # a knob: K1, the top-left, as the bezel cuts it; the inner sheet is inset by t each side
    outer = read_dxf(os.path.join(LASER, "bezel-outer.dxf"))
    knobs = sorted((e[1] for e in outer if e[0] == "C" and 3.0 < e[2] < 4.0), key=lambda c: (-round(c[1]), c[0]))
    kx, ky = knobs[0]
    h = 27.0
    # the credits plate on the back cover: re-run its art to find the plate that holds the QR code
    art.generate("back-cover.dxf", art.PARTS["back-cover.dxf"])
    qr = [b for m, b in art.QR_FOUND["back-cover.dxf"] if m.startswith("https://patternflow.work")][0]
    plate = [p.bounds for p in art.PLATES_FOUND["back-cover.dxf"]
             if p.bounds[0] <= qr[0] and p.bounds[2] >= qr[2] and p.bounds[1] <= qr[1] and p.bounds[3] >= qr[3]][0]
    px0, py0, px1, py1 = plate[0] - 2.5, plate[1] - 2.5, plate[2] + 2.5, plate[3] + 2.5

    rec = K["PSU_HEAD_RECESS"] - k
    pieces = [
        dict(id=12, file="12-knob-outer-sheet.dxf",
             ents=coupon("bezel-outer.dxf", "bezel-outer.etch.dxf", kx - h, ky - h, kx + h, ky + h, "12"),
             title="Knob, outer bezel sheet (bore, light slits, dial)",
             test=f"A {2 * h:g} mm square of the real outer bezel round knob K1: the Ø{T.fmt(v['boreDia'])} "
                  f"bore and the {K['KNOB_SLITS']} light slits ({T.fmt(K['KNOB_SLIT_W'])} wide as cut, ~1.5 mm "
                  "of wood between them at the inner end), and in the SVG its etched dial.",
             read="The slits should be cut clean through with every web whole and unscorched — if the webs burn "
                  "or break, the slits want a faster/lower-power cut, or KNOB_SLIT_W/KNOB_SLITS changed. Glue 13 "
                  "behind it, fit the encoder and its jam nut, and light the 4991's NeoPixel behind a paper "
                  "diffuser (`../../diffusers/`): you want an even ring.",
             var="KNOB_SLITS, KNOB_SLIT_W (enclosure.fs); cut settings for fine slots"),
        dict(id=13, file="13-knob-inner-sheet.dxf",
             ents=coupon("bezel-inner.dxf", None, kx - t - h, ky - t - h, kx - t + h, ky - t + h, "13"),
             title="Knob, inner bezel sheet (35 mm pocket)",
             test=f"The same square of the inner bezel: the {T.fmt(v['knobPocket'])} mm pocket behind the knob, "
                  "and the knob rib's slots where they fall inside it.",
             read="Glued behind 12, both outer face up, label strips together and edges flush: the EC11's jam nut should pull its face tight against 12 alone "
                  "(5.5 mm of thread, 2.3 mm nut), the 4991 breakout and its STEMMA plugs should sit inside the "
                  "pocket, and a paper diffuser should drop in flat. The rib slot takes a 3.18 tab like piece 2's "
                  "tenons.",
             var="#knobPocket"),
        base[8], base[10],
        dict(id=14, file="14-psu-head-recesses.dxf", ents=piece_psu_recess(v, rec),
             title="PSU screw-head recesses (outer sheet)",
             test=f"Piece 10's strip with the outer sheet's Ø{T.fmt(K['PSU_HEAD_RECESS'])} head recesses "
                  f"(drawn {T.fmt(rec)}) at the same spacing, triangle at the same end.",
             read="Stack 14 under 10, triangles together, and screw two M3 × 8, no washers, up through both "
                  "into the PSU's side face: they should thread in square, and each head should sit inside 14 "
                  "at or just below its face, so the stack lies flat on the bench.",
             var="PSU_HEAD_RECESS (enclosure.fs), #psuHoleDia"),
        base[11],
        dict(id=15, file="15-new-holes-gauge.dxf",
             ents=T.piece_holes(v, [("A", [4.85, 5.05, 5.25]), ("B", [3.75, 3.95, 4.15]),
                                    ("C", [7.1, 7.35, 7.6])]) + T.text("15", 6, 1.5, h=2.4),
             title="Hole gauge for the new holes (labels are the DRAWN diameter)",
             test=f"Row A: French cleat screw clearance (the model draws {T.fmt(K['CLEAT_HOLE'] - k)}). "
                  f"Row B: PSU clamp hole ({T.fmt(v['psuHoleDia'] - k)}). Row C: PSU head recess "
                  f"({T.fmt(rec)}).",
             read="A: a #10 / 5 mm wood screw should pass with no thread bite. B: an M3 passes with a little "
                  "play, and a 5.5 mm head can't pull in. C: the 5.5 mm head drops in with room round it.",
             var="CLEAT_HOLE, PSU_HEAD_RECESS (enclosure.fs), #psuHoleDia"),
        dict(id=16, file="16-etch-sampler.dxf",
             ents=coupon("back-cover.dxf", "back-cover.etch.dxf", px0, py0, px1, py1, "16"),
             title="Etch sampler: the back cover's credits plate",
             test="A crop of the real back cover round its credits plate: the QR code to patternflow.work (dark "
                  f"modules filled with score lines {art.QR_FILL} apart), the plate's lettering in JetBrains Mono "
                  "and the grid font, and the traces, vias and pours round it. The art is in the SVG only.",
             read="Score it with the settings you mean to use for the whole box, then cut. The QR code should "
                  "scan with a phone, its modules solid; the small lettering should read; lines should be fine "
                  "and even, not charred. Tune the Score process here, not on the back cover.",
             var="Score speed/power (laser settings, not the model)"),
        dict(id=17, file="17-pi-spacer-rings.dxf", ents=ring_pair("spacer-ring-pi-m2.5.dxf"),
             title="Pi 5 spacer rings (M2.5)",
             test="Two of the tray's M2.5 spacer rings, 7 mm round, as on sheet 3.",
             read="They should come out whole (1.8 mm of wood round the hole) and an M2.5 screw pass through.",
             var="#piScrewDia"),
    ]

    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith((".dxf", ".png", ".svg")):
            os.remove(os.path.join(OUT, f))
    cut_only = lambda ents: [e for e in ents if e[-1] != ART]
    for p in pieces:
        p["ents"], p["size"] = T.normalise(p["ents"])
        T.write_dxf(os.path.join(OUT, p["file"]), cut_only(p["ents"]))
    placed, used = T.pack(pieces)
    sheet = []
    for i, p in enumerate(pieces):
        x, y, rot = placed[i]
        sheet += T.shift(T.rotate90(p["ents"])[0] if rot else p["ents"], x, y)
    T.write_dxf(os.path.join(OUT, "all-since-rev-1.dxf"), cut_only(sheet))
    cut = [e[:-1] for e in sheet if e[-1] == CUT]
    score = [e[:-1] for e in sheet if e[-1] in (SCORE, ART)]
    art.write_svg(os.path.join(OUT, "all-since-rev-1.svg"), T.SHEET, used, art.svg_body(cut, score, []))
    T.render(os.path.join(OUT, "preview.png"), T.shift(sheet, 1.5, 1.5), (T.SHEET + 3, used + 3), k=4.0)

    changes = [
        ("Bezel two sheets, inner one pocketed 35 mm at each knob (rev 2)", "12 + 13"),
        ("Knob light slits, 36 × 0.7 mm per knob (rev 2.1)", "12"),
        ("Etched art: dials, QR codes, JetBrains Mono plates, score fill (rev 2 – 2.3)", "12 (dial), 16"),
        ("Raspberry Pi 5 holes, M2.5 nut pockets and spacer rings (rev 2)", "8, 17"),
        ("Push buttons, keyed 12 mm holes (rev 2.2)", "11"),
        (f"`#psuHoleDia` {T.fmt(v['psuHoleDia'])} and the head recesses, M3 × 8 no washer (after rev 2.3)",
         "10 + 14, 15"),
        ("French cleat holes Ø5.2 (rev 2.3)", "15"),
        ("Knob rib tabs in blind slots in the inner bezel (rev 2)", "13 (slot); same kerf rule as piece 2"),
        ("Wall doublers and the back cover doubler, glued; mortises through both sheets (rev 2, 2.3)",
         "not cut: the same 2-D fits as pieces 1–2, now through two glued sheets — glue them with a brace "
         "pushed through to register, as REVISIONS.md says"),
        ("Back cover doubler between the rail A strips, 0.5 mm clear; its relief windows (rev 2.3)",
         "not cut: clearances, checked in the model"),
        ("Intake/exhaust vents, shelf wire passthroughs, the top doubler's button notch (rev 2 – 2.2)",
         "not cut: openings, nothing fits in them"),
        ("Paper knob diffusers (rev 2.3)", "paper, not birch: `../../diffusers/`; try one with 12 + 13"),
    ]
    md = ["# Test cuts since rev 1", "",
          "Generated by `hardware/cad/tools/test_cuts_delta.py` from the live variables, `enclosure.fs` and "
          "the part DXFs; re-run after changing any of them.", "",
          "The full set in `../` was cut and measured on 2026-10-18 and Rev 1 was built on it on 2026-10-20, so "
          "kerf, thickness, finger joints, tenons, M3 nut pockets, the panel jig, the Colorlight and IEC holes "
          "are known good. This one sheet covers what is new since then.", "",
          f"**Load `all-since-rev-1.svg`** ({T.fmt(T.SHEET)} × {T.fmt(used)} mm, fits a 12 × 12\" sheet): one "
          "file, so the art stays registered on its coupons. In xTool Creative Space every colour imports as "
          "its own layer — set **red = Cut** and **blue = Score**, put the blue layer above the red one and "
          "process **by layer**, so all the scoring runs before anything is cut loose. XCS keeps those "
          "settings with the objects, not the colour: save the set-up as a project (.xcs) and reuse the "
          "settings you settle on here for the box's sheets. The DXF "
          "(`all-since-rev-1.dxf`) has the cuts and engraved labels only, no art, and is safe to cut even if "
          "the software ignores layers.", "",
          "Same 3 mm Baltic birch and the same settings as the box, or the results mean nothing.", "",
          "![Since rev 1](preview.png)", "",
          "## What changed since rev 1, and what covers it", "",
          "| Change | Test piece |", "|---|---|"]
    md += [f"| {a} | {b} |" for a, b in changes]
    md += [""]
    for p in pieces:
        md += [f"## {p['id']}. {p['title']} — `{p['file']}`", "",
               f"**Cut:** {p['test']}", "", f"**Read:** {p['read']}", "", f"**Sets:** {p['var']}", ""]
    with open(os.path.join(OUT, "README.md"), "w") as fh:
        fh.write("\n".join(md))
    for p in pieces:
        print(f"{p['file']:30s} {p['size'][0]:6.1f} x {p['size'][1]:6.1f}  ents {len(p['ents'])}")
    print(f"sheet: {T.fmt(T.SHEET)} x {T.fmt(used)} mm" + ("  ** OVERFLOWS 12in **" if used > T.SHEET else ""))


if __name__ == "__main__":
    main()
