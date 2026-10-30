# Firmware and software

| Directory | What it is |
|---|---|
| [`demos/`](demos/README.md) | The demos and the renderer that runs them: knobs in, 128 × 128 frames out. Python and numpy, plus upstream Patternflow's and the community's patterns compiled natively. Runs on the Pi 5 in the box, or on a PC on the bench |
| [`pi-controller/`](pi-controller/README.md) | The Raspberry Pi appliance: provisions a stock Raspberry Pi OS Lite card to boot straight into the demos, with a boot splash, a watchdog and a power-cut-safe setup |
| [`colorlight/`](colorlight/README.md) | The Colorlight 5A-75B card: JTAG tools for a Glasgow, the receiver75 gateware with our boot-splash patches, and the UDP frame protocol (`r75_frame.py`) |
| [`knob_bridge/`](knob_bridge/) | A bench tool: a FeatherS3 on the STEMMA QT chain reads the four encoders and streams them to a PC over USB serial, as JSON lines (protocol in `src/main.cpp`). Lets the demos run on a PC with real knobs |
| [`patches/`](patches/) | The abandoned ESP32 fork (below) |

## How the pieces fit

```
  4 × 4991 encoders ─I²C─► Pi 5: demos/run.py ─UDP, gigabit─► 5A-75B: receiver75 ─HUB75─► 4 panels
                                 (renders,                     (framebuffer,
                                  power cap)                    1/32 scan)
```

On the bench the same `run.py` runs on a PC, with the knobs from the knob
bridge (`--knobs serial:PORT`) and frames sent to the card over the PC's own
Ethernet (`--out udp`), or written to a GIF with no hardware at all
(`--out preview:FILE.gif`).

## The abandoned ESP32 fork

Until 2026-10-12 the desktop build was a fork of upstream Patternflow's
firmware for an Adafruit Matrix Portal S3. The delta is kept in `patches/`, as a
patch series against upstream at `87700bd` (v3.9.5):

```bash
git clone https://github.com/engmung/patternflow upstream
git -C upstream checkout -b desktop 87700bd
git -C upstream am ../firmware/patches/*.patch
```

Why it was needed and why it was left:
[`docs/desktop/design-notes/firmware-delta.md`](../docs/desktop/design-notes/firmware-delta.md)
and [`docs/desktop/driver-colorlight.md`](../docs/desktop/driver-colorlight.md) §1.
