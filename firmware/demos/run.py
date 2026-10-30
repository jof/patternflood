#!/usr/bin/env python3
"""Run the Patternflood demos.

Bench (a PC renders; the FeatherS3 knob bridge is on its USB, found by itself; the card is on
its Ethernet, or on HOST's, which only forwards the frames):
    ./run.py                               # or: --knobs serial:PORT --out pipe:HOST

Pi 5 (knobs on I2C, card on the Pi's own Ethernet):
    ./run.py --knobs i2c:1 --out udp:192.168.75.39

Preview without hardware (writes a GIF; --knobs auto plays by itself):
    ./run.py --demo etch --knobs auto --out preview:/tmp/etch.gif --seconds 8

Audio (what this machine is playing, by default; previews take --audio file:PATH):
    ./run.py --demo tempo                  # the calibration demo: tap tempo, mark the one, A/V delay
    ./run.py --audio file:~/Music/set.mp4@600 --out preview:/tmp/viz.gif --demo spectrum

Hold k0 and k3 together for a second for the menu: k0 picks the demo, k3 sets brightness,
k2 lets the music turn the upstream patterns' knobs.
"""
import argparse
import glob
import os
import signal
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "colorlight"))     # r75_frame, seesaw, knob_renderer

from pfd.demos import ALL                   # noqa: E402
from pfd.audio import audio_source          # noqa: E402
from pfd.io import frame_sink, knob_source  # noqa: E402
from pfd.runtime import Runtime             # noqa: E402
from pfd.upstream import Upstream           # noqa: E402



def default_knobs():
    """$PF_KNOBS, else a FeatherS3 knob bridge if one is plugged in, else the random player."""
    if os.environ.get("PF_KNOBS"):
        return os.environ["PF_KNOBS"]
    bridges = sorted(glob.glob("/dev/serial/by-id/usb-Espressif_*"))
    return f"serial:{bridges[0]}" if bridges else "auto"


def pick(demos, only):
    """--only: shelves by name, or "upstream" (SeungHun's presets, which are native code: fast on a Pi Zero)."""
    keys = {k.strip().lower() for k in only.split(",") if k.strip()}
    if not keys:
        return demos
    picked = [d for d in demos if d.group in keys
              or ("upstream" in keys and issubclass(d, Upstream) and d.group == "patternflow")]
    if not picked:
        raise SystemExit(f"--only {only!r} matches no demos (shelves: {sorted({d.group for d in demos})}, or upstream)")
    return picked


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("--knobs", default=default_knobs(),
                   help="serial:PORT | i2c[:BUS] | auto[:SEED] | script:SPEC | none (default: $PF_KNOBS, a knob bridge, or auto)")
    p.add_argument("--out", default=os.environ.get("PF_OUT", "auto"),
                   help="auto[:HOST] (udp if the card is on our link, else pipe via HOST) | pipe:HOST[:IP] | udp[:IP] | "
                        "preview:FILE.gif (default: $PF_OUT, or auto)")
    p.add_argument("--demo", default="0", help="start demo, by name or index")
    p.add_argument("--only", default="",
                   help="limit the demos: shelves, comma-separated (play,audio,cable,patternflow,community,community-1to1), or 'upstream' for "
                        "SeungHun's presets alone (default: all)")
    p.add_argument("--fps", type=float, default=None, help="default 60, or 20 for previews")
    p.add_argument("--audio", default=None,
                   help="pulse[:SOURCE] | alsa[:DEVICE] | file:PATH[@SECONDS] | none (default: pulse on the bench, none for previews)")
    p.add_argument("--audio-delay", type=float, default=None,
                   help="seconds to hold audio back so beats land when heard (default 0.15 for Bluetooth output, else 0)")
    p.add_argument("--bright", type=float, default=None, help="0..1, default 0.3 (1.0 for previews)")
    p.add_argument("--seconds", type=float, default=None, help="stop after this long (previews default to 8)")
    p.add_argument("--list", action="store_true", help="list the demos and exit")
    args = p.parse_args()

    demos = pick(ALL, args.only)
    if args.list:
        for i, d in enumerate(demos):
            print(f"{i}  {d.name:10s} {d.blurb}")
        return

    names = [d.name.lower() for d in demos]
    start = int(args.demo) if args.demo.isdigit() else names.index(args.demo.lower())
    preview = args.out.startswith("preview")
    fps = args.fps or (20.0 if preview else 60.0)
    bright = args.bright if args.bright is not None else (1.0 if preview else 0.3)
    seconds = args.seconds if args.seconds is not None else (8.0 if preview else None)

    def on_term(*_):
        raise KeyboardInterrupt         # systemd stop: blank the display on the way out
    signal.signal(signal.SIGTERM, on_term)

    out = frame_sink(args.out, preview_fps=fps)
    knobs = knob_source(args.knobs)
    spec = args.audio or ("none" if preview else "pulse")
    audio = audio_source(spec, delay=args.audio_delay, preview=preview)
    Runtime(demos, knobs, out, fps=fps, bright=bright, start=start, duration=seconds, audio=audio).run()


if __name__ == "__main__":
    main()
