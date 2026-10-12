# Patternflow — personal fork, and what grew out of it

Two projects with one shared inspiration: [Patternflow](https://github.com/engmung/patternflow),
an open-source LED synthesizer you play with four knobs.

They started as one build. They're separate because they want opposite things.

| | [**Desktop**](docs/desktop/) | [**Wall**](docs/wall/) |
|---|---|---|
| | Patternflow-inspired, four knobs | Room-interactive LED wall |
| Display | 128 × 128 px, 256 × 256 mm (2 × 2 P2) | 192 × 192 px, 576 × 576 mm |
| Input | four seesaw encoders | VL53L9CX lidar, contactless |
| Compute | Pi Zero 2 W + Colorlight 5A-75B | Pi + RP2350 front-end |
| Power | mains, LRS-50-5, panel load capped | mains, ~200 W peak |
| Enclosure | laser-cut birch ply box | frame + wall mount |
| Code | Pi renderer (left upstream 2026-10-12) | new codebase |
| Status | **enclosure modelled; driver bring-up next** | concept — lidar on order |

## Why two

The single combined build had to compromise on every axis at once. Battery
versus 200 W; instant-on versus a Linux boot; knobs versus a depth camera;
tracking upstream versus diverging from it. The
[power plan kept fighting the lidar plan](docs/wall/lidar-plan.md), which was
the signal.

The clean split: **the desktop build stays a Patternflow** and inherits
everything upstream has — the `.pfm` pattern loader, the frozen ABI, the web
console, 100+ community patterns. **The wall build is a new thing** that only
borrows the idea.

*2026-10-12:* the desktop build has since left upstream too. The P2 panels are
small enough that four of them make the instrument, and four panels want a
Colorlight 5A-75B and a Pi rather than an ESP32 —
[`docs/desktop/driver-colorlight.md`](docs/desktop/driver-colorlight.md).

## Layout

```
docs/desktop/    Project B — the Patternflow fork
docs/wall/       Project A — the room-interactive wall
firmware/        patch series against upstream (desktop build)
hardware/cad/    vendor STEP models (MIT, from Adafruit_CAD_Parts)
upstream/        clone @ 87700bd (v3.9.5), gitignored; `desktop` branch holds the fork
```

## The findings that shaped both

Four things came out of reading the upstream tree that decided most of the rest:

- **The HUB75 pinout is four `#define`s apart.** Upstream's `config.h` matches
  the Matrix Portal S3 on 10 of 14 pins — they used it as their reference.
  ([desktop/firmware-delta §1](docs/desktop/firmware-delta.md))
- **The I²C encoders were forced, not chosen.** Nine of upstream's twelve
  encoder GPIOs collide with fixed Matrix Portal functions.
  ([desktop/firmware-delta §3](docs/desktop/firmware-delta.md))
- **Upstream already has a hook for non-knob input.** `pf_params.h` has an
  absolute-param tier, added for audio, which lets an outside source drive
  pattern parameters with **no ABI change** — so sensor input works with every
  existing community pattern. ([wall/lidar-plan §2](docs/wall/lidar-plan.md))
- **I³C, not I²C, is what makes the lidar a camera.** 2268 zones at ~27 fps
  instead of ~3. The ESP32-S3 has no I³C, which is what removed it from the
  wall project. ([wall/README §2](docs/wall/README.md))

## Licensing

Upstream is dual-licensed: MIT for code, CC BY-SA 4.0 for hardware. Enclosure
work derived from `upstream/hardware/` inherits **CC BY-SA 4.0** and must be
shared alike. The wall project derives from none of it.
