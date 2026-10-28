#!/usr/bin/env python3
"""Tapes for Cable: short trims of public-domain silent comedy, cartoons and old ads.

    ./tools/cable_trims.py fetch              # download the sources once, gently, into the cache
    ./tools/cable_trims.py scan one-week      # a timestamped contact sheet of a source, to find gags
    ./tools/cable_trims.py scan one-week --start 920 --length 80 --every 1    # then closer
    ./tools/cable_trims.py cut [DIR]          # cut the trims to 128 x 128 clips in DIR (default ~/cable)

The trims are listed in cable_trims.json, next to this file. Every source is on the Internet
Archive and in the public domain (US films before 1930, or marked public domain there), and
only its small 512 kb/s (or similar) copy is fetched: once, one file at a time, at most
1.5 MB/s, a pause between files, our own user-agent, and checked against the archive's MD5.
Nothing downloaded goes in the repo. Then copy DIR's clips to the Pi's
/var/lib/patternflood/cable.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "cable_trims.json"
CACHE = Path(os.path.expanduser("~/.cache/patternflood/cable-sources"))
UA = "patternflood-cable-trims/1.0 (personal LED-panel TV; fetches a few public-domain films once)"
RATE = 1.5e6            # bytes a second, at most
PAUSE_S = 5             # between files
N = 128
FPS = 24


def _get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30)


def fetch(manifest):
    CACHE.mkdir(parents=True, exist_ok=True)
    for key, src in manifest["sources"].items():
        dst = CACHE / src["file"]
        if dst.exists():
            print(f"{key}: have it")
            continue
        with _get(f"https://archive.org/metadata/{src['item']}") as r:
            files = {f["name"]: f for f in json.load(r).get("files", [])}
        info = files[src["file"]]
        url = f"https://archive.org/download/{src['item']}/{urllib.request.quote(src['file'])}"
        print(f"{key}: {int(info['size']) / 1e6:.0f} MB from {url}")
        part = dst.with_suffix(dst.suffix + ".part")
        md5, t0, n = hashlib.md5(), time.monotonic(), 0
        with _get(url) as r, open(part, "wb") as f:
            while chunk := r.read(256 * 1024):
                f.write(chunk)
                md5.update(chunk)
                n += len(chunk)
                ahead = n / RATE - (time.monotonic() - t0)
                if ahead > 0:
                    time.sleep(ahead)
        if info.get("md5") and md5.hexdigest() != info["md5"]:
            part.unlink()
            sys.exit(f"{key}: MD5 mismatch; deleted, try again later")
        part.rename(dst)
        time.sleep(PAUSE_S)


def scan(manifest, key, every, out, start=0.0, length=None):
    src = CACHE / manifest["sources"][key]["file"]
    vf = (f"fps=1/{every},scale=160:-2,drawtext=text='%{{pts\\:hms\\:{start}}}':x=4:y=4:fontsize=14:"
          f"fontcolor=yellow:box=1:boxcolor=black@0.6,tile=10x8")
    span = ["-t", str(length)] if length else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", str(src), *span, "-vf", vf,
                    "-frames:v", "99", "-start_number", "0", str(out)], check=True)
    print(f"{key}: sheets of {every} s steps in {out}")


def cut(manifest, out):
    out.mkdir(parents=True, exist_ok=True)
    for tr in manifest["trims"]:
        src = CACHE / manifest["sources"][tr["src"]]["file"]
        dst = out / (tr["title"].lower().replace(" ", "_") + ".mp4")
        x = tr.get("x", 0.5)
        vf = (f"crop='min(iw,ih)':'min(iw,ih)':'(iw-min(iw,ih))*{x}':'(ih-min(iw,ih))/2',"
              f"scale={N}:{N}:flags=area,fps={FPS}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(tr["at"]), "-i", str(src), "-t", str(tr["dur"]),
                        "-an", "-vf", vf, "-c:v", "libx264", "-crf", "20", "-preset", "slow", "-pix_fmt", "yuv420p",
                        str(dst)], check=True)
        print(f"{dst.name}  {tr['src']} @ {tr['at']} s, {tr['dur']} s")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0], epilog=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["fetch", "scan", "cut"])
    p.add_argument("arg", nargs="?")
    p.add_argument("--every", type=float, default=5.0, help="scan: seconds between frames")
    p.add_argument("--out", default="/tmp/cable-scan-%02d.png", help="scan: where the sheets go")
    p.add_argument("--start", type=float, default=0.0, help="scan: from this many seconds in")
    p.add_argument("--length", type=float, default=None, help="scan: for this many seconds")
    a = p.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    if a.cmd == "fetch":
        fetch(manifest)
    elif a.cmd == "scan":
        scan(manifest, a.arg, a.every, a.out, a.start, a.length)
    else:
        cut(manifest, Path(os.path.expanduser(a.arg or "~/cable")))


if __name__ == "__main__":
    main()
