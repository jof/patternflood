# Patternflow — personal fork, and what grew out of it

Two projects with one shared inspiration: [Patternflow](https://github.com/engmung/patternflow),
an open-source LED synthesizer you play with four knobs.

They started as one build. They're separate because they want opposite things.

| | [**Desktop**](docs/desktop/) | [**Wall**](docs/wall/) |
|---|---|---|
| | Patternflow fork, four knobs | Room-interactive LED wall |
| Display | 128 × 64 px, 256 × 128 mm | 192 × 192 px, 576 × 576 mm |
| Input | four seesaw encoders | VL53L9CX lidar, contactless |
| Compute | Matrix Portal S3 | Pi + RP2350 front-end |
| Power | mains 5 V 8 A, ~10 W | mains, ~200 W peak |
| Enclosure | laser-cut basswood box | frame + wall mount |
| Code | **tracks upstream** | new codebase |
| Status | **ready to build** | concept — lidar on order |

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
