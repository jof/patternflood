#!/usr/bin/env python3
"""Export every laser-cut part of the enclosure as a DXF, straight from Onshape.

    hardware/cad/tools/export_dxf.py [out_dir]      (default hardware/laser/)

Every sheet part in this box is a through-cut of one 3 mm sheet, so one planar
face of each part carries its whole cut path: outline, holes, slots, finger
notches, hex pockets. A FeatureScript eval (over REST, with ~/.netrc, like
push.py) walks that face's edges; this script projects them onto the part's
own plane, moves the part to the origin and writes true LINE / ARC / CIRCLE
entities in millimetres, DXF R12 for the widest importer support.

Geometrically identical parts (the two rail stacks, the spacer rings) are
written once, with the quantity in MANIFEST.md. A preview.png of every part
is written alongside for a quick look before anything goes near the laser.

The outlines are KERF-COMPENSATED for whatever #kerf the Variable Studio holds,
and finger depths follow #thickness. Measure the real sheet and cut the test
comb, set both variables, then re-run this — never edit the DXFs by hand.
"""
import json
import math
import os
import re
import subprocess
import sys
import tempfile

DID, WID, PS = "8cfb8d4f799392c05f62f6ad", "b5dfed0b24d2121a79e8b1a8", "06ba580a80083894ed24609b"
API = "https://cad.onshape.com/api/v10"
VARS_EID = "ecb5fd1eaa5c82ce2840db45"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "laser")

# Parts that are cut from sheet. Everything else in the studio is a proxy.
PATTERN = r"^(Bezel.*|Wall.*|Back cover|Rail.*|Stiffener web|Panel brace.*|Electronics tray.*|Spacer ring.*)$"

SCRIPT = r'''
function(context is Context, queries)
{
    const pat = "%s";
    const mm = millimeter;
    var parts = [];
    for (var b in evaluateQuery(context, qAllModifiableSolidBodies()))
    {
        const nm = getProperty(context, { "entity" : b, "propertyType" : PropertyType.NAME });
        if (nm == undefined || !match(nm, pat).hasMatch) { continue; }
        const bb = evBox3d(context, { "topology" : b });
        const ext = bb.maxCorner - bb.minCorner;
        var ax = 0;
        if (ext[1] < ext[ax]) { ax = 1; }
        if (ext[2] < ext[ax]) { ax = 2; }
        var best = undefined;
        var bestC = -1e9 * meter;
        for (var f in evaluateQuery(context, qGeometry(qOwnedByBody(b, EntityType.FACE), GeometryType.PLANE)))
        {
            const pl = evPlane(context, { "face" : f });
            if (abs(pl.normal[ax]) > 0.999 && pl.origin[ax] > bestC) { bestC = pl.origin[ax]; best = f; }
        }
        var edges = [];
        for (var e in evaluateQuery(context, qAdjacent(best, AdjacencyType.EDGE, EntityType.EDGE)))
        {
            const c = evCurveDefinition(context, { "edge" : e });
            const tl = evEdgeTangentLines(context, { "edge" : e, "parameters" : [0, 0.5, 1] });
            var pts = [];
            for (var t in tl) { pts = append(pts, [t.origin[0] / mm, t.origin[1] / mm, t.origin[2] / mm]); }
            if (c is Circle)
            {
                const o = c.coordSystem.origin;
                edges = append(edges, ["C", [o[0] / mm, o[1] / mm, o[2] / mm], c.radius / mm, pts]);
            }
            else if (c is Line) { edges = append(edges, ["L", pts]); }
            else
            {
                var many = [];
                for (var t in evEdgeTangentLines(context, { "edge" : e, "parameters" : range(0, 1, 0.05) }))
                {
                    many = append(many, [t.origin[0] / mm, t.origin[1] / mm, t.origin[2] / mm]);
                }
                edges = append(edges, ["P", many]);
            }
        }
        parts = append(parts, [nm, ax, ext[ax] / mm, edges]);
    }
    return parts;
}
''' % PATTERN.replace("\\", "\\\\")

# 2D frame per thin axis: walls stand their long edge vertical
FRAME = {0: (2, 1), 1: (0, 2), 2: (0, 1)}


def curl(method, url, body=None):
    cmd = ["curl", "-s", "--netrc", "-X", method]
    if body is not None:
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(body, f)
        cmd += ["-H", "Content-Type: application/json", "--data-binary", "@" + path]
    return json.loads(subprocess.run(cmd + [url], capture_output=True).stdout)


def plain(v):
    t = v.get("btType", "")
    if t.endswith("BTFSValueArray"):
        return [plain(x) for x in v["value"]]
    if t.endswith("BTFSValueMap"):
        return {plain(e["key"]): plain(e["value"]) for e in v["value"]}
    return v.get("value")


# The parts whose outer face is on show.
SKIN = r"^(Bezel.*|Wall.*|Back cover)$"

# Which way each 2-D frame looks at its part: the frame's normal (u x v), along
# the thin axis. (z, y) and (x, z) look from the negative side; (x, y) from +z.
FRAME_NORMAL = {0: -1, 1: -1, 2: 1}


def box_centre(parts):
    """Centre of everything exported, from the cut-face edge points."""
    lo, hi = [1e9] * 3, [-1e9] * 3
    for _, _, _, edges in parts:
        for e in edges:
            for q in (e[3] if e[0] == "C" else e[1]):
                for k in range(3):
                    lo[k], hi[k] = min(lo[k], q[k]), max(hi[k], q[k])
    return [(a + b) / 2 for a, b in zip(lo, hi)]


def project(part, centre):
    """-> (name, thickness, entities) with entities in part-local 2D mm, min corner at 0,0.

    Every part is drawn as seen from OUTSIDE the box (from the side of it that
    faces away from the box's centre), so the face that is up on the laser bed
    is the face that ends up on the outside: the bezel's front, each wall's
    outer face, the back of the back cover. A through-cut part is the same part
    either way up, so this changes which face is seen, never the fit; but cut
    as drawn and nothing shows its bed-marked side. Where FRAME looks from the
    inside, u is mirrored. Only the box's skin (SKIN) is turned: inner parts
    keep FRAME's view, so the sheets of one stack (the tray, a brace) are all
    drawn from the same side and visibly line up on paper.
    """
    name, ax, thick, edges = part
    ax = int(ax)
    i, j = FRAME[ax]
    pts0 = [q for e in edges for q in (e[3] if e[0] == "C" else e[1])]
    face = sum(q[ax] for q in pts0) / len(pts0)
    outward = 1 if face >= centre[ax] else -1
    su = 1 if FRAME_NORMAL[ax] == outward or not re.match(SKIN, name) else -1
    P = lambda q: (su * q[i], q[j])
    ents = []
    for e in edges:
        if e[0] == "L":
            a, b = e[1][0], e[1][2]
            ents.append(["L", P(a), P(b)])
        elif e[0] == "C":
            c, r, pts = e[1], e[2], e[3]
            cc = P(c)
            s, m, t = [P(p) for p in pts]
            if math.dist(s, t) < 1e-6:
                ents.append(["CIRCLE", cc, r])
            else:
                ang = [math.degrees(math.atan2(p[1] - cc[1], p[0] - cc[0])) % 360 for p in (s, m, t)]
                ccw = (ang[1] - ang[0]) % 360 < (ang[2] - ang[0]) % 360
                ents.append(["ARC", cc, r, ang[0], ang[2]] if ccw else ["ARC", cc, r, ang[2], ang[0]])
        else:
            pts = [P(p) for p in e[1]]
            for a, b in zip(pts, pts[1:]):
                ents.append(["L", a, b])
    xs, ys = [], []
    for e in ents:
        if e[0] == "L":
            xs += [e[1][0], e[2][0]]; ys += [e[1][1], e[2][1]]
        else:
            xs += [e[1][0] - e[2], e[1][0] + e[2]]; ys += [e[1][1] - e[2], e[1][1] + e[2]]
    ox, oy = min(xs), min(ys)
    out = []
    for e in ents:
        if e[0] == "L":
            out.append(["L", (e[1][0] - ox, e[1][1] - oy), (e[2][0] - ox, e[2][1] - oy)])
        else:
            out.append([e[0], (e[1][0] - ox, e[1][1] - oy)] + list(e[2:]))
    return name, thick, out, (max(xs) - ox, max(ys) - oy)


def signature(ents):
    def r(v): return round(v, 2)
    keys = []
    for e in ents:
        if e[0] == "L":
            a, b = sorted([(r(e[1][0]), r(e[1][1])), (r(e[2][0]), r(e[2][1]))])
            keys.append(("L", a, b))
        else:
            keys.append((e[0], r(e[1][0]), r(e[1][1]), r(e[2]), *[r(x) for x in e[3:]]))
    return tuple(sorted(keys))


def write_dxf(path, ents):
    L = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "0", "ENDSEC",
         "0", "SECTION", "2", "TABLES",
         "0", "TABLE", "2", "LAYER", "70", "1",
         "0", "LAYER", "2", "CUT", "70", "0", "62", "1", "6", "CONTINUOUS",
         "0", "ENDTAB", "0", "ENDSEC",
         "0", "SECTION", "2", "ENTITIES"]
    f = lambda v: f"{v:.4f}"
    for e in ents:
        if e[0] == "L":
            L += ["0", "LINE", "8", "CUT", "10", f(e[1][0]), "20", f(e[1][1]), "30", "0.0",
                  "11", f(e[2][0]), "21", f(e[2][1]), "31", "0.0"]
        elif e[0] == "CIRCLE":
            L += ["0", "CIRCLE", "8", "CUT", "10", f(e[1][0]), "20", f(e[1][1]), "30", "0.0", "40", f(e[2])]
        else:
            L += ["0", "ARC", "8", "CUT", "10", f(e[1][0]), "20", f(e[1][1]), "30", "0.0", "40", f(e[2]),
                  "50", f(e[3]), "51", f(e[4])]
    L += ["0", "ENDSEC", "0", "EOF"]
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


def slug(name):
    s = name.lower()
    for a, b in (("—", "-"), (",", ""), ("(", ""), (")", ""), ("/", "-")):
        s = s.replace(a, b)
    return "-".join(s.split())


def preview(path, groups):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return
    k, pad = 2.0, 12
    cells = []
    for g in groups:
        w, h = g["size"]
        cells.append((int(w * k) + 2 * pad, int(h * k) + 2 * pad + 14))
    W = 1800
    x = y = rowh = 0
    pos = []
    for cw, ch in cells:
        if x + cw > W:
            x, y, rowh = 0, y + rowh, 0
        pos.append((x, y))
        x += cw
        rowh = max(rowh, ch)
    im = Image.new("RGB", (W, y + rowh), "white")
    d = ImageDraw.Draw(im)
    for g, (px, py), (cw, ch) in zip(groups, pos, cells):
        h = g["size"][1]
        T = lambda p: (px + pad + p[0] * k, py + 14 + pad + (h - p[1]) * k)
        d.text((px + 4, py + 2), f'{g["file"]}  x{g["qty"]}', fill=(0, 0, 160))
        for e in g["ents"]:
            if e[0] == "L":
                d.line([T(e[1]), T(e[2])], fill="black")
            else:
                c, r = e[1], e[2]
                box = [T((c[0] - r, c[1] + r)), T((c[0] + r, c[1] - r))]
                if e[0] == "CIRCLE":
                    d.ellipse(box, outline="red")
                else:  # PIL arcs run clockwise in screen space: flip the angles
                    d.arc(box, -e[4], -e[3], fill="red")
    im.save(path)


def main():
    d = curl("POST", f"{API}/partstudios/d/{DID}/w/{WID}/e/{PS}/featurescript", {"script": SCRIPT, "queries": {}})
    if d.get("notices"):
        sys.exit(json.dumps(d["notices"], indent=1)[:3000])
    raw = plain(d["result"])
    centre = box_centre(raw)
    parts = [project(p, centre) for p in raw]

    groups = {}
    for name, thick, ents, size in parts:
        g = groups.setdefault(signature(ents), {"names": [], "ents": ents, "size": size, "thick": thick})
        g["names"].append(name)
    groups = sorted(groups.values(), key=lambda g: -g["size"][0] * g["size"][1])

    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".dxf"):
            os.remove(os.path.join(OUT, f))
    for g in groups:
        base = slug(g["names"][0])
        if len(g["names"]) > 1 and g["names"][0].startswith("Spacer ring"):
            base = "spacer-ring-" + ("tray-to-brace" if "tray to brace" in g["names"][0] else "board")
        elif len(g["names"]) > 1:
            base = base.replace("-lower", "").replace("-upper", "")
        g["file"] = base + ".dxf"
        g["qty"] = len(g["names"])
        write_dxf(os.path.join(OUT, g["file"]), g["ents"])

    v = {x["name"]: x["expression"] for x in curl("GET", f"{API}/variables/d/{DID}/w/{WID}/e/{VARS_EID}/variables")[0]["variables"]}
    total = sum(g["qty"] for g in groups)
    lines = [
        "# Laser-cut parts",
        "",
        "Generated by `hardware/cad/tools/export_dxf.py` from the Onshape enclosure studio —",
        "do not edit by hand; change the model and re-run.",
        "",
        f"- **{total} parts, {len(groups)} files.** DXF R12, millimetres, one closed cut path per",
        "  outline/hole on layer `CUT`. Every part is a through-cut of one sheet.",
        f"- Cut with **#thickness = {v.get('thickness')}** and **#kerf = {v.get('kerf')}** baked in: tabs and",
        "  holes are already compensated. Both come from the test cuts; re-measure for new stock,",
        "  set them, then re-run this export.",
        "- **Drawn as seen from outside the box.** Cut each part as drawn and the face that",
        "  was up on the bed is its outside face — the bezel's front, the walls' outer faces.",
        "- **To cut the whole box, use [`sheets/`](sheets/README.md)**: every part nested on",
        "  three 12 × 24\" sheets (`nest_sheets.py`).",
        "- **Cut [`test-cuts/`](test-cuts/README.md) first** — kerf, nut pockets, hole sizes, the",
        "  panel jig and the board templates, all on one 12 × 12\" sheet.",
        "- Material: 3 mm Baltic birch, B/BB (enclosure-lasercut.md §13). Everything fits",
        "  across the xTool P2's 305 mm axis.",
        "",
        "| File | Qty | Size (mm) | Parts |",
        "|---|---|---|---|",
    ]
    for g in groups:
        lines.append(f'| `{g["file"]}` | {g["qty"]} | {g["size"][0]:.1f} × {g["size"][1]:.1f} | '
                     + "; ".join(sorted(set(g["names"]))) + " |")
    lines += ["", "![All parts](preview.png)", ""]
    with open(os.path.join(OUT, "MANIFEST.md"), "w") as fh:
        fh.write("\n".join(lines))
    preview(os.path.join(OUT, "preview.png"), groups)
    for g in groups:
        print(f'{g["file"]:58s} x{g["qty"]:<2d} {g["size"][0]:7.1f} x {g["size"][1]:6.1f}  ents {len(g["ents"])}')


if __name__ == "__main__":
    main()
