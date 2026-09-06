# LiDAR Plan — VL53L9CX

The one genuinely new feature in this build. Everything else is a port; this is
an addition upstream has no concept of.

Companion to [`mechanical-plan.md`](../desktop/mechanical-plan.md),
[`power-plan.md`](../desktop/power-plan.md), [`firmware-delta.md`](../desktop/firmware-delta.md).

---

## 1. What the part actually is

I under-described this in the first pass as a "ToF sensor". It isn't. The
VL53L9CX is a **3D dToF lidar camera**:

| | |
|---|---|
| Zones | **2268** (54 × 42 raw at full resolution) |
| Range | **5 cm – 9 m** |
| Field of view | 55° × 42° (71° diagonal) |
| Frame rate | up to 100 Hz *(sensor-side; see §3 — the bus, not the sensor, is the limit)* |
| Illumination | 2× VCSEL, 940 nm invisible flood |
| Host interface | **I²C @ 1 MHz** or I³C @ 12.5 MHz |
| Binning modes | 2, 4, 6, 8, 12, 24 → 54×42 down to 4×4 |

That is a depth camera, not a rangefinder. It's also **new** — announced around
June 2026 — which is the source of most of the risk in §6.

The practical framing: upstream Patternflow takes **four scalars** from four
knobs. This part offers a **depth image of the room at video rate**. The gap
between those two things is the whole opportunity here.

---

## 2. The key finding: upstream already has the hook

Reading `upstream/firmware/patternflow/abi/pf_params.h`, the param bus has a
**three-tier priority per channel**:

```
  1. paramAbsoluteActive[i] → lerp(min, max, v/1000)    ← absolute, 0..1000
  2. knobAudioActive[i]     → lerp(min, max, 0..1)      ← audio / Weather
  3. knobDeltas[i]          → integrate with step       ← the physical encoder
```

Tier 2 exists because audio already needed to drive a knob channel from
something that isn't a knob. **That is exactly the lidar's problem, already
solved.** Any pattern written against `PFParams::apply()` — which is the
standard way patterns read knobs — will accept an external absolute value with
**no change to the pattern at all**.

The consequence is worth stating plainly:

> Feed derived gesture values into `paramAbsolute[0..3]` and **the entire
> community pattern library becomes gesture-controlled for free.** All 100+
> published patterns, the 33-pattern Basics pack, everything in the Live
> Editor. No pattern edits, no ABI change, no recompile of anything.

This matters because the ABI is a **frozen contract** — `pf_params.h` says so in
its first line, `abi.sums` records it, and `check_abi_freeze.py` fails CI on
drift. Append-at-tail-only, bump `PF_ABI_MODULE_VERSION`. Going through the
existing absolute tier sidesteps all of that.

### Two tiers of integration

**Tier 1 — gesture → knob channels. No ABI change.**
Reduce the depth frame to four scalars and publish them on the absolute param
bus. Candidate mappings:

| Channel | Derived from |
|---|---|
| K1 | nearest-target distance (hand proximity) |
| K2 | horizontal centroid of the nearest cluster |
| K3 | vertical centroid |
| K4 | occupied-zone count (hand vs. body vs. crowd), or approach velocity |

This is the whole feature for most purposes, and it should ship first.

**Tier 2 — depth field → patterns. ABI change, opt-in.**
Expose the binned depth map so a pattern can *sample* it — the room's silhouette
becomes a term in the pixel loop. This needs a genuine ABI extension: append to
the input frame at the tail, bump `PF_ABI_MODULE_VERSION` to 3, refresh
`abi.sums`.

The header documents the precedent for doing this cleanly: when the absolute
tier was added, modules built for an older host **compile the new tier out** and
still run. Follow that pattern exactly and Tier 2 doesn't fork the catalogue —
lidar-native patterns stay installable on stock Patternflows, just without the
depth term.

---

## 3. Bandwidth is the real design constraint

The sensor will do 100 Hz. The bus will not. From the binning table:

| Binning | Raw grid | Zones | Frame bytes | @400 kHz | @1 MHz |
|---|---|---|---|---|---|
| 2 | 54 × 42 | 2268 | 14,842 | ~2.7 fps | ~6.7 fps |
| 4 | ~27 × 21 | ~567 | ~3,800 | ~10 fps | ~26 fps |
| **6** | **~18 × 14** | **~252** | **~1,700** | **~23 fps** | **~58 fps** |
| **8** | **~13 × 10** | **~130** | **~900** | **~44 fps** | **~100 fps** |
| 24 | 4 × 4 | 16 | 204 | fast | fast |

*(400 kHz ≈ 40 KB/s and 1 MHz ≈ 100 KB/s usable after protocol overhead.)*

**Full resolution is not a live-performance mode.** At 2268 zones you get single-
digit frame rates — fine for a one-shot room scan, useless for an instrument
that has to feel instant.

**Binning 6–8 is the sweet spot: ~130–250 zones at 25–60 fps.** That is still
far more spatial information than four knobs, and it comfortably outruns the
panel's own refresh.

> Treat "we bought a 2268-zone sensor so we should use 2268 zones" as the trap
> it is. The instrument wants *latency*, not resolution. 130 zones at 44 fps
> beats 2268 zones at 3 fps for every purpose in this build.

### The bus conflict

**The lidar wants 1 MHz. The seesaw encoders do not.** Adafruit's seesaw is
reliable at 100–400 kHz and is not specified for 1 MHz. On this build they
share the STEMMA QT bus, along with the four daisy-chained 100 mm cables from
[`mechanical-plan.md`](../desktop/mechanical-plan.md) §2.3.

Two ways out:

- **A. One bus at 400 kHz, binning 8 → ~44 fps.** ✅ **Recommended.** Simplest,
  no extra wiring, and 44 fps is past the point where anyone can feel the
  difference. Take this unless measurement says otherwise.
- **B. Second I²C bus for the lidar at 1 MHz.** The ESP32-S3 has two I²C
  peripherals, and the Matrix Portal S3 has spare analog pins (A1–A4) to put the
  second one on. Buys binning 6 at ~58 fps. Costs a wiring run and a mux of
  complexity. Hold in reserve.

### Boot cost

ST's ULD architecture uploads a **firmware blob to the sensor over the bus at
every init** — ~84 KB on the VL53L5CX, and the L9CX is unlikely to be smaller.
At 400 kHz that is **2–3 seconds of boot time**, plus ~84 KB out of the 3 MB app
partition (which is already tight — see [`firmware-delta.md`](../desktop/firmware-delta.md) §2).

Do the upload **before** HUB75 init, or on a separate task. A multi-second
blocking I²C transfer while the I2S DMA is driving the panel is a good way to
get a glitching display.

---

## 4. Division of labour with the radar

The LD2450 and the VL53L9CX overlap more than the BOM suggests — both see people
in front of the instrument. They're good at genuinely different things:

| | LD2450 (24 GHz radar) | VL53L9CX (lidar) |
|---|---|---|
| Sees through the enclosure | **Yes** — no aperture needed | No — needs an open hole |
| Works in darkness / through clothing | Yes | Yes (940 nm, but optical) |
| Coverage | ~6 m, ±60° — room scale | 9 m, 55°×42° — narrower cone |
| Output | up to 3 targets, X/Y trajectory | **depth image**, ~130–2268 zones |
| Data rate | trivial (UART ASCII) | the design constraint (§3) |
| Good for | *is anyone there, and where* | *what shape is in front of me* |

**Suggested two-tier attention model:**

```
   nobody in the room          radar quiet
        │                           │
        ▼                           ▼
   ┌─────────┐  radar sees    ┌──────────┐  lidar sees   ┌──────────┐
   │  SLEEP  │ ──a person──►  │  AMBIENT │ ──a hand──►   │  PLAYED  │
   │ panel   │                │ pattern  │  <80 cm       │ gesture  │
   │ dark    │  ◄──timeout──  │ runs     │  ◄──timeout── │ drives   │
   └─────────┘                └──────────┘               │ K1–K4    │
                                                         └──────────┘
```

Each sensor does what it's actually good for: the radar is the wide, always-on,
zero-aperture net that decides *whether to wake*; the lidar is the precise,
power-hungry, aperture-needing instrument that only matters once someone is
close enough to play it.

This also solves a power problem for free. [`power-plan.md`](../desktop/power-plan.md) §3
flags that sealed banks auto-shut-off under low draw during sleep — but a device
that wakes on radar doesn't need to sleep as deeply or as often, and the
AMBIENT tier keeps a real load on the bank.

And it's the most faithful thing in this build to upstream's stated origin —
the README's Nam June Paik *Participation TV*, where standing in front of the
work is what makes it move. Upstream requires you to touch a knob. This
version notices you walk up.

---

## 5. Mechanical requirements

These are stricter than the radar's and they constrain the front panel. From
[`mechanical-plan.md`](../desktop/mechanical-plan.md) §2.4, expanded:

**Use an open aperture. Not a window.**
Cover-glass crosstalk is *the* classic failure mode for ST multizone ToF parts —
light from the VCSEL reflecting off the inside of the cover directly into the
receiver, which raises the noise floor and destroys near-field accuracy. ST
publishes cover-glass design guidance precisely because getting it wrong is so
easy. Ordinary acrylic, and anything printed "clear", will do this.

If the aperture must be covered, it needs a proper IR-transmissive window with
an **air gap** and an **opaque separator between emitter and receiver**. Simpler
to leave it open.

**Give it a light-tight collar.** The emitter must not see the receiver through
the housing wall. A short printed shroud between the two optical paths, matte
black.

**Aim it as a gesture volume, not at the player's chest.**
55° × 42° at 9 m means a front-facing sensor sees the whole room and, at playing
distance, mostly torso. Two options:

```
   (a) top edge, angled forward/up        (b) front face, near-field gated
   ┌──────────────┐ ◄── lidar             ┌──────────────┐
   │              │╲   gesture            │         ◎────┼─► sees everything
   │   DISPLAY    │ ╲  volume             │   DISPLAY    │   incl. torso
   │              │  ╲                    │              │
   ├──────────────┤   hands enter         ├──────────────┤   gate 5–80 cm
   │ ◉ ◉ ◉ ◉      │   deliberately        │ ◉ ◉ ◉ ◉   ◎  │   in software
   └──────────────┘                       └──────────────┘
```

**(a) is better.** A hand has to be raised into the volume on purpose, so the
instrument doesn't react to the player's body while they're using the knobs —
which would make the knobs feel possessed. (b) works but pushes the whole
problem into software gating, and gating by distance alone can't tell a hand
from a chest at the same range.

**Keep it away from the buck converter** for the same reason as the radar, and
**don't let it look across the panel face** — a grazing view of the LED panel's
own surface will return spurious near-field zones.

---

## 6. Risk — this is the riskiest item in the build

Stated plainly, because it's easy to miss behind an impressive spec sheet:

- **The part is new** (~June 2026). The driver ecosystem has not caught up.
- **There is no known ESP32 driver.** The one Arduino effort I found
  ([earlynerd/VL53L9-Arduino](https://github.com/earlynerd/VL53L9-Arduino)) is
  explicitly *"active bring-up code, not a finished Arduino library"*, targets
  the **RP2350**, and uses **I³C** rather than I²C. It is useful as a reference
  for register sequences and the binning table — **not** as a library to drop in.
- **The realistic path is porting ST's ULD**, which is portable C with a thin
  platform layer (I²C read/write + delay) you implement. People have done this
  for the VL53L5CX and L8CX on ESP32; the L9CX is the same architecture. This is
  real work — days, not hours — and it is the long pole of the whole project.
- **The ESP32-S3 has no I³C peripheral.** If the I²C path turns out to be
  limited or buggy on this part, there is no cheap fallback on this MCU. That
  would be the point to reconsider the controller.

**De-risk it in this order:**

1. Bring the lidar up **standalone** — bare Matrix Portal S3, ULD ported, no
   panel, no encoders, print depth frames to serial. Prove it before it is
   anywhere near an enclosure.
2. Confirm the **binning mode and achievable frame rate** on a real bus at
   400 kHz. Everything in §3 is calculated, not measured.
3. Only then commit the **aperture position** in the front panel, which is the
   one mechanical decision that can't be undone.

Steps 1 and 2 need no enclosure and no panels. **Do them first, in parallel with
waiting on the power bank** — they gate more of this build than anything else,
and if the lidar turns out to be impractical on this MCU, everything else in the
project still works and you've lost nothing but bench time.

---

## 7. Sequence

| # | Step | Blocks |
|---|---|---|
| 1 | ULD port, standalone, serial output | everything below |
| 2 | Binning / frame-rate characterisation @ 400 kHz | aperture placement |
| 3 | Coexistence test: lidar + 4 seesaw encoders on one bus | bus architecture (§3) |
| 4 | Tier 1 — gesture → `paramAbsolute[0..3]` | — *ships the feature* |
| 5 | Radar + attention state machine (§4) | — |
| 6 | Tier 2 — depth field in ABI, `PF_ABI_MODULE_VERSION` 3 | lidar-native patterns |

Step 4 is the point where the feature is real and every existing pattern
responds to gesture. Steps 5 and 6 are the interesting part, but 4 is the one
that justifies the sensor.
