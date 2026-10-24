#!/usr/bin/env python3
"""Run the Patternflood demos.

Bench (ash renders; the FeatherS3 knobs are on ash's USB; durian is only a pipe to the card):
    ./run.py --knobs serial:/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_XX:XX:XX:XX:XX:XX-if00 \\
             --out pipe:durian

Pi 5 (knobs on I2C, card on the Pi's own Ethernet):
    ./run.py --knobs i2c:1 --out udp:192.168.75.39

Preview without hardware (writes a GIF; --knobs auto plays by itself):
    ./run.py --demo etch --knobs auto --out preview:/tmp/etch.gif --seconds 8

Audio (what ash is playing, by default; previews take --audio file:PATH):
    ./run.py --demo tempo                  # the calibration demo: tap tempo, mark the one, A/V delay
    ./run.py --audio file:~/Music/set.mp4@600 --out preview:/tmp/viz.gif --demo spectrum

Hold k0 and k3 together for a second for the menu: k0 picks the demo, k3 sets brightness,
k2 lets the music turn the upstream patterns' knobs.
"""
import argparse
import os
import signal
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "colorlight"))     # r75_frame, seesaw, knob_renderer

from pfd.demos import ALL                   # noqa: E402
from pfd.audio import audio_source          # noqa: E402
from pfd.io import frame_sink, knob_source  # noqa: E402
from pfd.runtime import Runtime             # noqa: E402

BRIDGE = "/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_XX:XX:XX:XX:XX:XX-if00"


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("--knobs", default=f"serial:{BRIDGE}", help="serial:PORT | i2c[:BUS] | auto[:SEED] | script:SPEC | none")
    p.add_argument("--out", default="auto:durian",
                   help="auto[:HOST] (udp if the card is on our link, else pipe) | pipe:HOST[:IP] | udp[:IP] | preview:FILE.gif")
    p.add_argument("--demo", default="0", help="start demo, by name or index")
    p.add_argument("--fps", type=float, default=None, help="default 60, or 20 for previews")
    p.add_argument("--audio", default=None,
                   help="pulse[:SOURCE] | alsa[:DEVICE] | file:PATH[@SECONDS] | none (default: pulse on the bench, none for previews)")
    p.add_argument("--audio-delay", type=float, default=None,
                   help="seconds to hold audio back so beats land when heard (default 0.15 for Bluetooth output, else 0)")
    p.add_argument("--bright", type=float, default=None, help="0..1, default 0.3 (1.0 for previews)")
    p.add_argument("--seconds", type=float, default=None, help="stop after this long (previews default to 8)")
    p.add_argument("--list", action="store_true", help="list the demos and exit")
    args = p.parse_args()

    if args.list:
        for i, d in enumerate(ALL):
            print(f"{i}  {d.name:10s} {d.blurb}")
        return

    names = [d.name.lower() for d in ALL]
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
    Runtime(ALL, knobs, out, fps=fps, bright=bright, start=start, duration=seconds, audio=audio).run()


if __name__ == "__main__":
    main()
