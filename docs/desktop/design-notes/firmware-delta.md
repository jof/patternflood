# Firmware Delta

> **Design history:** the ESP32 / Matrix Portal fork of upstream firmware, abandoned on 2026-10-12 for the Colorlight + Pi controller ([`../driver-colorlight.md`](../driver-colorlight.md)).

> 🔁 **2026-10-12: superseded.** The desktop build no longer runs upstream
> Patternflow on an ESP32: a Raspberry Pi Zero 2 W renders frames and a
> Colorlight 5A-75B drives the panels — [`driver-colorlight.md`](../driver-colorlight.md).
> This document describes the Matrix Portal S3 fork that was planned instead,
> and is kept for that history.

What has to change in `upstream/firmware/patternflow/` to run on this hardware.
Not a work plan — a record of what the mechanical and power decisions imply, so
nothing here is a surprise later.

Referenced from [`mechanical-plan.md`](mechanical-plan.md) and
[`power-plan.md`](power-plan.md). For the order to do it in, and how to keep the
delta against upstream tidy, see [`build-prep.md`](build-prep.md).

---

## 1. The good news: the HUB75 pinout is four lines apart

Upstream's `config.h` pinout and the Matrix Portal S3's fixed HUB75 wiring are
**almost the same board**. Comparing `upstream/firmware/patternflow/config.h`
against Adafruit's CircuitPython board definition:

| Signal | Upstream | Matrix Portal S3 | |
|---|---|---|---|
| R1 | 42 | 42 | ✅ |
| G1 | 41 | 41 | ✅ |
| B1 | 40 | 40 | ✅ |
| R2 | 38 | 38 | ✅ |
| G2 | 39 | 39 | ✅ |
| **B2** | **13** | **37** | ❌ |
| **A** | **46** | **45** | ❌ |
| **B** | **11** | **36** | ❌ |
| C | 48 | 48 | ✅ |
| **D** | **12** | **35** | ❌ |
| E | 21 | 21 | ✅ |
| LAT | 47 | 47 | ✅ |
| OE | 14 | 14 | ✅ |
| CLK | 2 | 2 | ✅ |

Ten of fourteen already match — upstream evidently took the Matrix Portal as
its pinout reference. **Four `#define`s in `config.h`** and the display works.

That is genuinely the whole display change:

```c
#define PANEL_RES_W 128   // unchanged
#define PANEL_RES_H 64    // unchanged
#define PANEL_CHAIN 1     // unchanged — see below
```

**The panel config needs no change at all.** Two 64×64 shift-register panels
chained are electrically indistinguishable from one 128×64 panel — the data just
shifts straight through — so upstream's stock values are already correct.

`PANEL_CHAIN 2` would be **wrong**, and it's worth understanding why, because the
trap is subtle. `core_display.h` passes `PANEL_RES_W` to the driver as the
*module* width:

```c
HUB75_I2S_CFG mxconfig(PANEL_RES_W, PANEL_RES_H, PANEL_CHAIN, _pins);
```

and the library's physical width is `mx_width × chain_length`. But `PANEL_RES_W`
is **simultaneously** the canvas width everywhere else — `core_canvas.h`,
`core_tables.h`, `pf_module.h`, the module ABI's array bounds. Those two uses
only agree when `PANEL_CHAIN` is 1. Setting it to 2 gives a 256-px-wide physical
display driven by a 128-px-wide canvas.

In practice `PANEL_CHAIN` is effectively pinned at 1 in this codebase. Change
`PANEL_RES_W` to describe the whole chain, not the module.

**Portrait is free too, if the panels go in the right way round.** The box
stands on end. Upstream maps a pattern that declares a 64 × 128 grid onto the
128 × 64 panel itself (`core_canvas.h`: logical `(x, y)` → panel `(127 − y, x)`),
so the hardware must be exactly a 128 × 64 panel turned so its x = 127 end is up:
both panels upright in the landscape model, chain left → right, box resting on
its −x wall. Then there is still no config change. Stack the panels any other
way and portrait needs a remap patch — see
[`mechanical-plan.md`](mechanical-plan.md) §2.1.

`config.h` explicitly documents this as the supported path: *"Running a panel
other than the stock 128x64? Change these to match your hardware and reflash —
that is the whole change."* Because we land on 128×64 anyway, even that is
mostly a no-op. Start with `PANEL_PROFILE PANEL_STANDARD`; only change it if
the panels stay completely dark.

---

## 2. The real blocker: memory and partitions

This is the one genuinely awkward part of the port.

| | Upstream target | Matrix Portal S3 |
|---|---|---|
| Flash | 16 MB | **8 MB** |
| PSRAM | 8 MB **octal** | **2 MB quad** |

`upstream/firmware/patternflow/platformio.ini` is built around the larger part:

```ini
board_build.arduino.memory_type = qio_opi
board_build.psram_type          = opi
board_upload.flash_size         = 16MB
board_upload.maximum_size       = 16777216
board_build.partitions          = partitions/app3M_fat9M_16MB.csv
```

Every one of those needs changing: `qio_qspi` / `qspi`, 8 MB, and a **new
partition table** — `app3M_fat9M_16MB.csv` describes 12 MB of regions that do
not exist on this board. Roughly 3 MB app + ~4 MB FAT fits.

The 2 MB quad PSRAM is the tighter constraint of the two, and it is not just a
number in a config file. `platformio.ini` explains that the firmware
deliberately pushes its own allocations into PSRAM so that internal DRAM stays
free for loadable pattern modules — with a quarter of the PSRAM, that
budget shrinks. The 128-module cap (136 bytes of PSRAM per slot) is fine; the
concern is per-pattern working memory and HUB75 double-buffering competing for
what's left.

**Expect to run a lower colour depth than stock.** Practical starting point:
build at reduced bit depth, confirm the panels are stable, then raise it until
allocation fails. This is a tuning exercise on first boot, not a design flaw —
but budget an evening for it rather than expecting a clean first flash.

---

## 3. Encoders move from GPIO to I²C — and had to

Upstream reads four EC11s directly:

```c
#define ENC1_A 4   #define ENC1_B 8    #define ENC1_SW 9
#define ENC2_A 5   #define ENC2_B 10   #define ENC2_SW 15
#define ENC3_A 6   #define ENC3_B 16   #define ENC3_SW 17
#define ENC4_A 7   #define ENC4_B 18   #define ENC4_SW 1
```

On a Matrix Portal S3 that is **impossible**, not merely inconvenient. Those
GPIOs are already spoken for:

- **16 / 17** → STEMMA QT SDA / SCL
- **8 / 18** → UART RX / TX
- **4** → status NeoPixel
- **6 / 7** → onboard UP / DOWN buttons

Nine of the twelve encoder pins collide. The BOM's four **Adafruit 4991 seesaw
breakouts** sidestep this entirely: all four encoders arrive on the two I²C
pins that are actually free. That was the right call, and it's worth noting it
was forced rather than optional.

**Consequences:**

- A new I²C encoder driver replaces upstream's GPIO/interrupt path. Upstream's
  debounce constants (`ENC_BOUNCE_US 500`, `INVERT_ENCODER`) become properties
  of the seesaw firmware instead, and the polling cadence has to be fast enough
  that the knobs still feel immediate — the encoder feel *is* the instrument, so
  this deserves more care than a typical driver swap.
- **Set four distinct I²C addresses.** The 4991 defaults to `0x36`, with
  address jumpers covering `0x36`–`0x3D`. Cut/bridge the jumpers to give each
  encoder its own address, and **write down which is which** — physical knob
  order K1–K4 needs to map to a stable address order, or the front panel
  controls will be scrambled relative to upstream's documented behaviour
  (encoder 1 = brightness, 2 = network, 3 = knob values, 4 = pattern list).
- Each 4991 has a NeoPixel. Upstream has no concept of per-knob lighting — it's
  a free addition, and it doubles as the trickle load that keeps a power bank
  from auto-shutting-off during sleep mode (see [`power-plan.md`](power-plan.md) §3).

The four STEMMA QT cables are 100 mm. Four daisy-chained encoders plus the ToF
sensor is a long bus by I²C standards — if it's flaky, that's bus capacitance,
and the fix is stronger pull-ups or a shorter chain, not a faster MCU.

---

## 4. New sensors — no upstream equivalent

Both are additive; neither has any hook in upstream firmware.

- **LD2450** (UART, `RX`=8 / `TX`=18): ASCII trajectory output, up to 3 tracked
  targets with X/Y coordinates, ~6 m range. The interesting mapping is presence
  and position → pattern parameters, i.e. the room plays the instrument. This is
  the most novel thing in the whole build and the furthest from upstream.
- **VL53L9CX** (I²C, shares the encoder bus): a **2268-zone 3D dToF lidar**, not
  a proximity sensor. This is the largest piece of new work in the fork and it
  has its own document — **[`lidar-plan.md`](../../wall/lidar-plan.md)**. The headline:
  upstream's `paramAbsolute` tier already provides a way for a non-knob source
  to drive pattern parameters, so gesture control needs **no ABI change** and
  works with every existing community pattern. Bus speed, binning and the ULD
  port are covered there.

Both should sit behind a feature flag, via upstream's `features/` mechanism —
`config.h` includes `features/overrides.h` if present, and `features_local.h`
does the same for the feature list. That keeps *new* functionality out of the
core files.

> ⚠️ **But `overrides.h` cannot carry this port.** `config.h` claims every
> tunable is `#ifndef`-guarded; only 12 symbols actually are (sleep, gamma,
> white balance). The pins, `PANEL_RES_*`, `PANEL_CHAIN` and the encoder
> defines are all **bare** — so §1 and §2 must patch `config.h` and
> `platformio.ini` directly. Keep that delta as a patch series:
> [`build-prep.md`](build-prep.md) §A2. Making the pin block guarded is a good
> upstream contribution and would remove the need — §D there.

---

## 5. Power clamp

`upstream/README.md` notes a total-pixel-power clamp is planned but not yet
shipped, and that a full-white pattern pulls ~4.8 A at 5 V. Given this build
runs off a bank through a buck converter, **implement the clamp** — sum the
pixel values per frame and scale global brightness to hold a configured current
ceiling. It protects the converter, the bank, and the connectors, and it makes
the option-C fallback in [`power-plan.md`](power-plan.md) available if the PD
chain ever gets swapped for a plain 5 V supply.

---

## 6. Order of work

1. Flash stock firmware with the four pin edits, on **USB power, one panel,
   low brightness** (`PANEL_RES_W 64` for the single-panel test). Confirm
   pixels before anything else.
2. Fix `platformio.ini` for 8 MB / quad PSRAM + new partition table. Tune colour
   depth until stable.
3. Second panel, confirm the chain and the seam.
4. I²C encoder driver, addresses assigned and labelled.
5. Power chain (PD trigger → buck), then the clamp.
6. Sensors, behind feature flags.

Steps 1–3 are the ones that prove the build is viable. Everything after is
additive.
