# Project A — Room-Interactive LED Wall

**Status: concept.** Blocked on the VL53L9CX breakout, which is on order.

A large LED wall that responds to the people in front of it. The lidar is not
an accessory here — it is the input device, and the reason the project exists.
Nobody touches a knob.

| | |
|---|---|
| Panels | **9 × 64×64 P3** (of 10 on hand) → 192 × 192 px, 576 × 576 mm |
| Input | **VL53L9CX over I³C** — 2268 zones, target ≥25 fps |
| Compute | Linux host + RP2350 lidar front-end — see [`compute-options.md`](compute-options.md) |
| Power | **Mains.** ~200 W peak. No battery, not portable |
| Firmware | **Not Patternflow.** New codebase |

---

## 1. Why this is its own project

Splitting this off the Patternflow build is right, and the clearest argument is
that the two projects want **opposite things**:

| | [Desktop](../desktop/) | Wall (this) |
|---|---|---|
| Power | battery, portable, ~11 W | mains, fixed, ~200 W peak |
| Boot | instant — you switch it on | can take 30 s, it lives on a wall |
| Input | four knobs, hands on | lidar, contactless, across a room |
| Scale | 256 × 128 mm, desk | 576 × 576 mm, wall |
| Compute | as little as possible | as much as needed |
| Codebase | **tracks upstream Patternflow** | **new, diverges permanently** |
| Lidar bus | I²C, gesture-grade | **I³C, camera-grade** |

Every row conflicts. The single build I was planning had to compromise on all of
them at once — which is why the power plan kept fighting the lidar plan, and why
the [compute options](compute-options.md) doc ended up arguing with itself.

Two projects, one shared inspiration. They can still trade patterns and ideas;
they should not share a BOM or a codebase.

---

## 2. The I³C decision

This is the technical reason the ESP32-S3 leaves the design.

The VL53L9CX speaks **I²C at 1 MHz or I³C at 12.5 MHz**, and the gap between
those is the gap between two entirely different products:

| Bus | Throughput | Full 2268 zones | Practical mode |
|---|---|---|---|
| I²C @ 400 kHz | ~40 KB/s | ~2.7 fps | ~130 zones @ 44 fps |
| I²C @ 1 MHz | ~100 KB/s | ~6.7 fps | ~250 zones @ 58 fps |
| **I³C @ 3.2 MHz** | ~400 KB/s | **~27 fps** | full res, usable |
| **I³C @ 12.5 MHz** | ~1.5 MB/s | **~100 fps** (sensor cap) | full res, sensor-limited |

For the desktop toy, I²C gesture-grade is plenty. For "the room is the input",
it isn't — you want the depth *image*, at rate.

**The ESP32-S3 has no I³C peripheral**, and no practical way to synthesise one
while also bit-banging HUB75 through I²S DMA. That single fact is what removes
it from this project. (Worth noting: the **ESP32-P4** does have I³C, if staying
in the Espressif world ever becomes attractive.)

**What does have I³C:**

- **RP2350** — no hardware I³C, but its **PIO** can synthesise it, and this is
  already proven: [earlynerd/VL53L9-Arduino](https://github.com/earlynerd/VL53L9-Arduino)
  is exactly that, running 2.0–3.2 MHz. The driver I dismissed as "wrong
  platform" for the ESP32 build is **exactly right** for this one.
- **STM32 H5 / U5 / MP2** — hardware I³C at full speed. ST's own
  STEVAL-VL53L9 evaluation board is STM32 Nucleo-based, so this is the
  reference path with the best driver support.
- **Raspberry Pi** — no exposed I³C. This matters: the Pi cannot talk to this
  sensor at camera rate on its own.

That last point shapes the architecture: **the Pi needs a front-end.**

---

## 3. Suggested architecture

```
  ┌──────────────┐  I³C @ ~3.2 MHz   ┌─────────────┐
  │  VL53L9CX    │ ─────PIO────────► │  RP2350     │  depth → blobs,
  │  2268 zones  │                   │  (Pico 2)   │  tracking, framing
  └──────────────┘                   └──────┬──────┘
                                            │ USB / UART
                                            ▼
                                     ┌─────────────┐
   9 × P3 64×64 ◄───HUB75 ×3 chains──│  Pi 4 / 5   │  patterns, compositing
   192 × 192 px      active-3 HAT    │  + hzeller  │  GPU shaders
                                     └─────────────┘
                                            ▲
                                     5 V 40 A PSU (mains)
```

**Why this shape:**

- The **RP2350 does one job** — I³C to the sensor, at rate, with deterministic
  timing PIO is uniquely good at. It hands up processed data, not raw frames.
  It's a $5 part and it removes the only hard real-time constraint from the Pi.
- The **Pi does everything else** and is unconstrained: real memory, a GPU for
  shader-based patterns, networking, storage, a normal development loop.
- **9 panels map perfectly onto an active-3 HAT**: three parallel chains of
  three panels, each chain 192 × 64 px, stacked to 192 × 192. hzeller's
  `rpi-rgb-led-matrix` handles this routinely — **no FPGA needed.**

The Colorlight 5A-75B stays in reserve. [`compute-options.md`](compute-options.md)
§5 set the threshold at "panel count grows past ~8", and nine crosses it — but
the active-3 HAT still handles nine comfortably, so the FPGA buys bit depth and
refresh rather than capability. Revisit it if 5–6 bit banding turns out to
matter, or if the wall grows.

---

## 4. Panel layout

Ten panels on hand; **3 × 3 is the recommended build**, keeping one spare:

```
        576 mm  (3 × 192 mm)
   ┌───────┬───────┬───────┐
   │ 64×64 │ 64×64 │ 64×64 │  ◄── chain 1
   ├───────┼───────┼───────┤
   │ 64×64 │ 64×64 │ 64×64 │  ◄── chain 2      576 mm
   ├───────┼───────┼───────┤
   │ 64×64 │ 64×64 │ 64×64 │  ◄── chain 3
   └───────┴───────┴───────┘
        = 192 × 192 px, 36 864 px
```

Square, keeps a spare, and maps one chain per panel row onto the three parallel
outputs. The alternative 5 × 2 (960 × 384 mm, 320 × 128 px) uses all ten but
leaves no spare and is an awkward object to hang.

**36 864 pixels is 4.5× the desktop build.** Worth sitting with — it is a
different kind of object, and patterns composed for 128 × 64 will not simply
scale into it.

---

## 5. Power — mains, and not a small amount

P3 64×64 panels draw roughly 20 W peak each.

| | |
|---|---|
| 9 panels, peak (full white) | **~180 W** → 36 A at 5 V |
| 9 panels, typical pattern | ~60–80 W |
| Pi 4 + RP2350 | ~7 W |
| **PSU to buy** | **5 V, 40 A (200 W)** — Meanwell LRS-200-5 class |

This is the clearest evidence for the split: **there is no battery answer
here.** 180 W peak is roughly eighteen times the desktop build's typical draw,
and a 100 Wh bank would run it for well under an hour even if it could source
36 A, which it can't.

Mains changes the mechanical problem completely — a frame and a wall mount
rather than an enclosure, mains-safe wiring practice, and real thought about
fusing and distribution across three chains. **Do not daisy-chain 36 A through
panel-to-panel power jumpers**; run proper distribution from the PSU.

---

## 6. What to order now

The lidar is the blocker, but nothing else is:

- **Pi 4 or 5** + **active-3 HAT** (Electrodragon or hzeller's own design)
- **RP2350 / Pico 2** — cheap, and it lets the I³C driver work start the day
  the breakout lands
- **5 V 40 A PSU** + fusing + distribution wiring
- Frame material for a 576 mm square + wall mount

**Hold off on the Colorlight** until §3's threshold is actually hit.

---

## 7. Open questions

1. **What does the wall actually do?** The desktop toy inherits Patternflow's
   answer — four knobs, a pattern library. This project has no such inheritance,
   and "room-interactive" is a feeling, not a spec. Worth writing down what a
   person walking up to it should experience before writing any code.
2. **Do patterns transfer at all?** Patternflow patterns are 128 × 64 C++ against
   a frozen ABI. At 192 × 192 on a GPU, the honest answer is probably "as
   inspiration, not as code" — but the Live Editor's **JavaScript** origin form
   is the thing to look at first.
3. **Does the LD2450 radar belong here or on the desktop?** It's cheap, needs no
   aperture, and does room-scale presence well. Arguably both — see
   [`lidar-plan.md`](lidar-plan.md) §4 for the two-tier attention model, which
   was written for the combined build but fits this project better.

---

## 8. Measured panel data (P3 64×64)

Measured off the actual panels, 2026-09-08. **This is the only hard mounting
data for these parts** — Waveshare publishes no drawing, and §7 of the desktop
[`enclosure-lasercut.md`](../desktop/enclosure-lasercut.md) records why nothing
generalises between panel types.

| | |
|---|---|
| Body | **190 × 190 mm** (not 192 — see below) |
| Thread | **M3** |
| Hole row, along the edge | **16 / 95 / 174 mm** from one corner (79 mm pitch, symmetric) |
| Hole row, perpendicular | **8 mm** from the edge for the end holes, **9 mm** for the centre hole |
| Tiling pitch | **192 mm** hole-centre to hole-centre between stacked panels |
| Flatness | slightly **wedge-shaped**; laid together the gap is ~2 mm |

### The 2 mm gap is required, not slop

This is the important part, and it was not obvious:

```
  64 px x 3 mm pitch      -> 189 mm first-to-last pixel centre
  body 190 mm             -> 189 + 0.5 mm border per edge
  continuity across a seam requires  border + gap + border = 3 mm
                                     0.5   + 2.0 + 0.5    = 3.0   ✓
  tiling pitch = 190 + 2 = 192 = 64 x 3 mm                        ✓
```

So the panels are **deliberately undersize** and the gap makes up the pixel
pitch. **Butting them tight would put a 2 mm error into the pixel grid at every
seam** — a visible jog, not a cosmetic gap. The carrier must therefore be built
on a **192 mm hole grid**, not on the panel bodies.

For the 3 × 3 array: bodies span `3 × 190 + 2 × 2 = 574 mm`, pixel area
`3 × 192 = 576 mm`. The wedge shape is also why alignment must come from the
hole grid and not from panels touching each other.

### Two consequences for the frame

1. **The hole row is not collinear.** 8 mm for the end holes, 9 mm for the
   centre one. Any straight rail bolting to all three needs ~1 mm of
   perpendicular give — oversized holes or slots wide in both axes, with
   washers.
2. **Hole inset does not generalise at all.** Third data point now:

   | Panel | Size | Inset | From centre |
   |---|---|---|---|
   | Adafruit 5036 (P2.5 64×32) | 160 × 80 | 15.75 mm | 24.25 mm |
   | Waveshare P3 64×64 | 190 × 190 | **8 mm** | 87 mm |

   Nearly a 2× spread in inset. Measure every panel type; infer nothing.
