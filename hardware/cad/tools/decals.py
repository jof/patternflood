#!/usr/bin/env python3
"""Show the etched art in Onshape, as decals on the parts' outer faces.

    hardware/cad/tools/decals.py

art.py renders each etched part's art as a transparent PNG covering exactly
that part's DXF frame (art/<stem>.decal.png). This
  1. uploads each one, or replaces it, as an image element "Art — <stem>.png"
     in the document;
  2. rewrites the image imports in enclosure.fs (between the ART IMPORTS
     markers) to point at those elements' current microversions;
  3. runs push.py.
The Enclosure shell feature then lays each image on its part's outer face
with the standard library's decal functions, framed by the part's art datum,
so it lands where the laser will etch. Visual only: no geometry changes.

Re-run after art.py.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://cad.onshape.com/api/v10"
DID, WID = "8cfb8d4f799392c05f62f6ad", "b5dfed0b24d2121a79e8b1a8"
LASER = os.path.join(HERE, "..", "..", "laser")
FS = os.path.join(HERE, "..", "featurescript", "enclosure.fs")

# art file stem -> FeatureScript namespace for its image
STEMS = {"bezel-outer": "ArtBezelOuter", "wall-left": "ArtWallLeft", "wall-right-iec": "ArtWallRight",
         "wall-top": "ArtWallTop", "back-cover": "ArtBackCover"}


def curl(method, url, form=None):
    cmd = ["curl", "-s", "--netrc", "-X", method, "-w", "\n%{http_code}"]
    for k, v in (form or {}).items():
        cmd += ["-F", f"{k}={v}"]
    out = subprocess.run(cmd + [url], capture_output=True).stdout.decode()
    b, code = out.rsplit("\n", 1)
    try:
        return (json.loads(b) if b.strip() else {}), code
    except json.JSONDecodeError:
        return {"raw": b[:300]}, code


def elements():
    return curl("GET", f"{API}/documents/d/{DID}/w/{WID}/elements")[0]


def upload(stem):
    path = os.path.join(LASER, "art", stem + ".decal.png")
    name = f"Art — {stem}.png"
    have = [e for e in elements() if e.get("name") == name]
    form = {"file": f"@{path};type=image/png", "encodedFilename": name}
    if have:
        _, code = curl("POST", f"{API}/blobelements/d/{DID}/w/{WID}/e/{have[0]['id']}", form=form)
        eid = have[0]["id"]
    else:
        r, code = curl("POST", f"{API}/blobelements/d/{DID}/w/{WID}", form=form)
        eid = r.get("id")
    mv = [e for e in elements() if e.get("id") == eid][0].get("microversionId")
    return eid, mv, code


def main():
    lines = []
    for stem, ns in STEMS.items():
        eid, mv, code = upload(stem)
        print(f"{stem:16s} -> {eid} @ {mv} ({code})")
        lines.append(f'{ns}::import(path : "{eid}", version : "{mv}");')
    src = open(FS).read()
    block = "// ART IMPORTS BEGIN — written by tools/decals.py\n" + "\n".join(lines) + "\n// ART IMPORTS END"
    src, n = re.subn(r"// ART IMPORTS BEGIN.*?// ART IMPORTS END", block, src, flags=re.S)
    if n != 1:
        sys.exit("enclosure.fs has no ART IMPORTS block")
    open(FS, "w").write(src)
    sys.exit(subprocess.run([sys.executable, os.path.join(HERE, "push.py")]).returncode)


if __name__ == "__main__":
    main()
