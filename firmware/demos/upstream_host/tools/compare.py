#!/usr/bin/env python3
"""Check a C++ port of an upstream web preset against the JavaScript original.

    compare.py pattern-0516.ts ../web_ports/preset_0516.h [--size 128x64] [--frames 90] [--png out.png]

Runs both for the same number of 1/30 s frames at two knob settings and compares
the last frames:
  default  the web's default knob values (0, 2, 0, 0.06), which the port starts at
  turned   k0..k3 at 0.5, 3.0, 2.0, 0.56, reached in the port by 10/10/40/10 detents
           (the steps upstream's ports use: 0.05, 0.1, 0.05, 0.05)
It prints the mean absolute difference (0..255) and the share of pixels off by
more than 48 in any channel. Small differences are expected (the C++ sin LUT,
float vs double); a wrong port shows as a large share. Patterns that use
Math.random can't match pixel for pixel: compare those by eye in the PNG.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build  # noqa: E402

CASES = {"default": ([0, 2, 0, 0.06], [0, 0, 0, 0]),
         "turned": ([0.5, 3.0, 2.0, 0.56], [10, 10, 40, 10])}

HARNESS = r'''
#include "Arduino.h"
#include "presets/%(header)s"
int main(int argc, char** argv) {
  int frames = atoi(argv[1]);
  int d[4] = {atoi(argv[2]), atoi(argv[3]), atoi(argv[4]), atoi(argv[5])};
  %(ns)s::setup();
  for (int f = 0; f < frames; f++) {
    InputFrame in; memset(&in, 0, sizeof in);
    for (int k = 0; k < 4; k++) in.knobDeltas[k] = f == 0 ? d[k] : 0;
    in.now = pf_host_now_ms = (uint32_t)((f + 1) * 1000 / 30);   // JS draw() gets time = (f + 1) / 30
    %(ns)s::update(1.0f / 30.0f, in);
    %(ns)s::draw();
  }
  fwrite(PFCanvas::buffer, 1, PFCanvas::BUFFER_BYTES, stdout);
}
'''


def run_cpp(header, w, h, frames, deltas, tmp):
    tree = tmp / "tree"
    if not tree.exists():
        build.write_tree(build.default_upstream(), tree)
        shutil.copy(header, tree / "presets" / header.name)
        ns = re.search(r"^namespace\s+(\w+)\s*\{", header.read_text(), re.M).group(1)
        (tmp / "h.cpp").write_text(HARNESS % {"header": header.name, "ns": ns})
        subprocess.run(["g++", "-std=c++17", "-O2", "-w", f"-DPANEL_RES_W={w}", f"-DPANEL_RES_H={h}",
                        "-I", str(tree), "-o", str(tmp / "h"), str(tmp / "h.cpp")], check=True)
    out = subprocess.run([str(tmp / "h"), str(frames), *map(str, deltas)], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.uint8).reshape(h, w, 3)


def run_js(ts, w, h, frames, values):
    out = subprocess.run(["node", str(HERE / "jsref.mjs"), str(ts), str(w), str(h), str(frames), *map(str, values)],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, np.uint8).reshape(h, w, 3)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("ts", type=Path)
    p.add_argument("header", type=Path)
    p.add_argument("--size", default="128x64")
    p.add_argument("--frames", type=int, default=90)
    p.add_argument("--png", type=Path)
    a = p.parse_args()
    w, h = (int(v) for v in a.size.split("x"))
    rows = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for name, (values, deltas) in CASES.items():
            js = run_js(a.ts.resolve(), w, h, a.frames, values)
            cpp = run_cpp(a.header.resolve(), w, h, a.frames, deltas, tmp)
            diff = np.abs(js.astype(int) - cpp.astype(int))
            mad = diff.mean()
            bad = (diff.max(axis=2) > 48).mean()
            lit = (js.max(axis=2) > 0).mean()
            print(f"{name:8s} mean |diff| {mad:6.2f}   pixels off >48: {100 * bad:5.1f}%   (js lit {100 * lit:5.1f}%)")
            rows.append(np.concatenate([js, np.full((h, 4, 3), 60, np.uint8), cpp], axis=1))
    if a.png:
        from PIL import Image
        img = np.concatenate([np.concatenate([r, np.full((4, r.shape[1], 3), 60, np.uint8)]) for r in rows])
        Image.fromarray(img).resize((img.shape[1] * 3, img.shape[0] * 3), Image.NEAREST).save(a.png)
        print(f"wrote {a.png} (rows: default, turned; left JS, right C++)")


if __name__ == "__main__":
    main()
