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
| Firmware | **Forked Patternflow** — `desktop` branch, patches in [`../../firmware/`](../../firmware/) |
| Enclosure | **Laser-cut 3 mm basswood**, finger-jointed, selectively doubled |

## Plans

| Doc | Covers |
|---|---|
| [**`build-prep.md`**](build-prep.md) | **What to do and order, in sequence — start here** |
| [`mechanical-plan.md`](mechanical-plan.md) | Geometry, stackup, front panel, clearances |
| [`enclosure-lasercut.md`](enclosure-lasercut.md) | Finger-joint box in 3 mm basswood, Onshape workflow |
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

**[`build-prep.md`](build-prep.md) is the ordered plan.** In short:

1. **First light** — one panel, USB power only, four pin edits. Needs nothing
   you don't already have, and proves the whole approach in an evening.
2. **Caliper session** — four measurements that stop the enclosure being
   provisional. [`mechanical-plan.md`](mechanical-plan.md) §4.
3. **Order** — a 5 V 8–10 A PSU and mechanical hardware. Shorter than the
   power plan originally implied; no PD trigger or buck unless a bank is added.
