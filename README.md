# Patternflow — personal fork

A [Patternflow](https://github.com/engmung/patternflow) built from different
parts: a Matrix Portal S3 instead of the custom PCB, I²C encoders instead of
GPIO ones, an internal battery, and two sensors upstream doesn't have.

Same 128 × 64 pixel grid as stock, so **every upstream pattern runs unmodified.**

## Layout

```
upstream/    pristine clone of engmung/patternflow @ 87700bd (v3.9.5)
             reference only — never edit
docs/        this fork's plans
```

## Plans

| Doc | Covers |
|---|---|
| [`docs/mechanical-plan.md`](docs/mechanical-plan.md) | Geometry, stackup, front panel, sensor apertures, fabrication |
| [`docs/power-plan.md`](docs/power-plan.md) | USB-C in → sealed bank → PD trigger → buck → 5 V |
| [`docs/lidar-plan.md`](docs/lidar-plan.md) | **The VL53L9CX — the one new feature.** Integration, bandwidth, risk |
| [`docs/firmware-delta.md`](docs/firmware-delta.md) | Pinout diff, memory/partition port, I²C encoders, sensors |
| [`docs/architecture-options.md`](docs/architecture-options.md) | Matrix Portal vs. Pi vs. Pi + Colorlight 5A-75B |

## Hardware

| | Upstream v3.9 | This build |
|---|---|---|
| Controller | ESP32-S3 DevKit N16R8 + custom PCB | Adafruit Matrix Portal S3 (no PCB) |
| Panel | 1× 128×64 P2.5, 320×160 mm | 2× Waveshare P2 64×64 GOB, 256×128 mm |
| Resolution | 128 × 64 px | **128 × 64 px — identical** |
| Encoders | 4× EC11 on GPIO | 4× Adafruit 4991 seesaw on I²C |
| Power | USB power bank → screw terminal | USB-C → internal sealed bank |
| Sensing | — | LD2450 radar + **VL53L9CX 3D lidar** |

Two spare 64×64 panels and a spare knob set are held back; not every BOM line
lands in v1.

## Where it stands

Planning. Nothing built, nothing flashed.

The three things that unblock everything else:

1. **Calipers on the parts** — EC11 bushing thread length, butted two-panel
   width, panel depth, 4991 outline. See mechanical plan §4.
2. **Buy the power bank** — its dimensions set the enclosure depth, and
   pass-through charging is the one spec that must be verified before purchase.
   See power plan §6.
3. **First light** — four pin edits and `PANEL_CHAIN 2`, on USB power, one
   panel, low brightness. See firmware delta §6.

Running in parallel, and gating more than anything else: **bring the lidar up
standalone.** It needs no enclosure, no panels and no power decision, and it is
the highest-risk item in the build. See lidar plan §6.

## Licensing

Upstream is dual-licensed: MIT for code, CC BY-SA 4.0 for hardware. Enclosure
work derived from `upstream/hardware/` inherits **CC BY-SA 4.0** and must be
shared alike.
