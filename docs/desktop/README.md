# Project B — Patternflow Desktop

**Status: ready to build.** Nothing is blocked.

A Patternflow fork at roughly upstream's scale, on different parts. Four knobs,
a 128 × 64 panel, USB-C. Keeps upstream's exact pixel geometry, so **every
community pattern runs unmodified**, and stays close enough to upstream's tree
to keep tracking it.

| | |
|---|---|
| Panels | **2 × Waveshare P2 64×64 GOB** → 128 × 64 px, 256 × 128 mm |
| Controller | **Adafruit Matrix Portal S3** (no custom PCB) |
| Input | **4 × Adafruit 4991 seesaw encoders** on I²C |
| Power | **USB-C**, optionally a bank — see [`power-plan.md`](power-plan.md) |
| Firmware | **Forked Patternflow**, tracking upstream |

## Plans

| Doc | Covers |
|---|---|
| [`mechanical-plan.md`](mechanical-plan.md) | Geometry, stackup, front panel, fabrication |
| [`power-plan.md`](power-plan.md) | USB-C, PD trigger, buck, optional bank |
| [`firmware-delta.md`](firmware-delta.md) | Pinout diff, memory port, I²C encoders |

## What the split changed

The lidar moved to the [wall project](../wall/). That removes the two things
that were making this build complicated:

- **The compute pressure is gone.** The ESP32-S3's 2 MB quad PSRAM was tight
  mainly because a depth camera wanted to share it. Without that, the port is
  a pinout change and a partition table — see [`firmware-delta.md`](firmware-delta.md).
- **The power budget dropped.** No lidar means ~1.9 A typical rather than 2.1 A,
  and more importantly no pulsed VCSEL load fighting the panel supply.

**The LD2450 radar can still live here** if you want the "notices you walk up"
behaviour. It's cheap, needs no aperture (it sees through the enclosure wall),
and its data rate is trivial. Upstream's `paramAbsolute` tier means it can drive
pattern parameters with no ABI change — see [`firmware-delta.md`](firmware-delta.md) §4.

## Where it stands

1. **Calipers on the parts** — EC11 bushing thread length, butted two-panel
   width, panel depth, 4991 outline. [`mechanical-plan.md`](mechanical-plan.md) §4.
2. **Decide: battery or not.** The split may have made it unnecessary — see
   [`power-plan.md`](power-plan.md) §0.
3. **First light** — four pin edits and `PANEL_CHAIN 2`, on USB power, one
   panel, low brightness. [`firmware-delta.md`](firmware-delta.md) §6.

Steps 1 and 3 need nothing that isn't already on the bench.
