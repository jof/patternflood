#!/usr/bin/env python3
"""Pictures of every demo for the web remote's shelves, made here rather than waiting for the box.

The box keeps a picture of each demo it shows (pfd/web.py), so its shelves fill in as it's
played. This renders them all at once, off-screen, with nobody at the knobs: each demo runs for
--seconds and its last frame is kept. Then copy them to the box:

    tools/thumbs.py                                  # into ~/.cache/patternflood/thumbs
    tools/thumbs.py --only patternflood --seconds 8 --out /tmp/thumbs
    rsync -a ~/.cache/patternflood/thumbs/ patternflood.local:/tmp/thumbs/ && \\
        ssh patternflood.local 'sudo install -o patternflood -g patternflood -m 644 /tmp/thumbs/*.png /var/cache/patternflood/thumbs/'

Cable is left out (it would go looking for the day's headlines). A demo that fails gets no picture.
"""
import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(HERE), str(HERE.parent / "colorlight")]

import numpy as np                              # noqa: E402

from pfd.io import NoKnobs                      # noqa: E402
from pfd.runtime import Runtime                 # noqa: E402
from pfd.web import default_thumbs, png, thumb_name  # noqa: E402


class _Offscreen:
    realtime = False

    def show(self, frame, lights=None):
        pass

    def stats(self):
        return ""

    def close(self):
        pass


class _Snap(Runtime):
    """Keeps each frame as the eye sees it, with no banner over it."""
    snap = None

    def _overlay(self, rgb):
        self.snap = rgb.copy()         # the runtime scales rgb in place for its gamma table next
        return rgb


def _render(args):
    i, seconds, out = args
    from pfd.demos import ALL
    cls = ALL[i]
    key = f"{cls.group}/{cls.__name__}"
    t0 = time.monotonic()
    try:
        devnull = open(os.devnull, "w")
        stderr, sys.stderr = sys.stderr, devnull      # the runtime's log lines, a few per demo
        try:
            rt = _Snap([cls], NoKnobs(), _Offscreen(), fps=20, bright=1.0, duration=seconds)
            rt.run()
        finally:
            sys.stderr = stderr
        if rt.snap is None:
            return key, "no frame"
        u8 = (np.clip(rt.snap, 0, 1) * 255 + 0.5).astype(np.uint8)
        (Path(out) / thumb_name(key)).write_bytes(png(u8))
        return key, f"{time.monotonic() - t0:.1f} s"
    except Exception as e:
        return key, f"failed: {e!r}"


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("--out", type=Path, default=default_thumbs(), help="default ~/.cache/patternflood/thumbs")
    p.add_argument("--seconds", type=float, default=6.0, help="how long each demo runs first (default 6)")
    p.add_argument("--only", default="", help="shelves, comma-separated (default: all but cable)")
    p.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    args = p.parse_args()

    from pfd.demos import ALL
    shelves = {s.strip() for s in args.only.split(",") if s.strip()}
    picked = [i for i, d in enumerate(ALL) if d.group != "cable" and (not shelves or d.group in shelves)]
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"{len(picked)} demos, {args.seconds:g} s each, {args.jobs} at a time, into {args.out}")
    failed = 0
    with ProcessPoolExecutor(args.jobs) as pool:
        for n, (key, how) in enumerate(pool.map(_render, [(i, args.seconds, str(args.out)) for i in picked]), 1):
            if not how.endswith(" s"):
                failed += 1
                print(f"  {key}: {how}")
            if n % 50 == 0:
                print(f"  {n} done")
    print(f"done: {len(picked) - failed} pictures, {failed} without")


if __name__ == "__main__":
    main()
