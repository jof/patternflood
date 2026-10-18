# Project B — Patternflow Desktop

**Status: enclosure modelled; driver bring-up next.** Redesigned 2026-10-12.

A Patternflow-inspired instrument: four knobs and a **2 × 2 array of P2 GOB
panels**, driven by a **Colorlight 5A-75B** with a **Raspberry Pi Zero 2 W**
rendering the frames. That trades upstream compatibility for panel count — the
ESP32 `.pfm` patterns do not run here as binaries
([`driver-colorlight.md`](driver-colorlight.md) §1).

| | |
|---|---|
| Panels | **4 × Waveshare RGB-Matrix-P2-64x64-B (GOB), 2 × 2** → 128 × 128 px, 256 × 256 mm, **measured** and modelled — see [`mechanical-plan.md`](mechanical-plan.md) §2.1. Six owned, two spare |
| Controller | **Colorlight 5A-75B** (one panel per HUB75 output) + **Pi Zero 2 W** via a **USB gigabit adapter** — [`driver-colorlight.md`](driver-colorlight.md) |
| Input | **4 × Adafruit 4991 seesaw encoders** on the Pi's I²C |
| Power | **IEC mains → Mean Well LRS-50-5**, panel load capped per frame — [`driver-colorlight.md`](driver-colorlight.md) §4 |
| Software | A Pi-side renderer streaming to the card; FPP for first pixels |
| Enclosure | **Laser-cut 3 mm Baltic birch ply**, finger-jointed, 293 × 373 × 60.7 mm, stands upright; cut on an xTool P2 from 12 × 24" sheets |

## Plans

| Doc | Covers |
|---|---|
| [**`driver-colorlight.md`**](driver-colorlight.md) | **The controller: Colorlight + Pi, panel chips, power cap, bring-up — start here** |
| [`build-prep.md`](build-prep.md) | Ordered build plan (written for the Matrix Portal; caliper and hardware items still apply) |
| [`mechanical-plan.md`](mechanical-plan.md) | Geometry, stackup, front panel, clearances |
| [**`../../hardware/laser/test-cuts/`**](../../hardware/laser/test-cuts/README.md) | **Cut these first:** kerf, nut-pocket, hole, panel-fit, board-template and IEC test pieces on one 12 × 12" sheet — regenerate with `hardware/cad/tools/test_cuts.py` |
| [**`../../hardware/laser/`**](../../hardware/laser/MANIFEST.md) | **Cut files: one DXF per part, quantities, preview** — regenerate with `hardware/cad/tools/export_dxf.py` |
| [`enclosure-lasercut.md`](enclosure-lasercut.md) | Finger-joint box in 3 mm sheet — the design, and §13 the material choice |
| [`fastener-concepts.md`](fastener-concepts.md) | **Concepts for review** — assembling it with M3 hardware and no glue |
| [`onshape-workflow.md`](onshape-workflow.md) | Modelling it: vendor CAD, proxies, variables, rendering |
| [`power-plan.md`](power-plan.md) | *Superseded* — USB-C, PD trigger, buck, optional bank |
| [`firmware-delta.md`](firmware-delta.md) | *Superseded* — the ESP32 fork's pinout diff and memory port |

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
