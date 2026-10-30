# Build Prep — Desktop

> **Design history:** the ordered plan for the abandoned Matrix Portal S3 build. The build as it stands is in [`../BUILD.md`](../BUILD.md).

> 🔁 **2026-10-12: the controller changed.** The Matrix Portal S3 steps below
> (first light on its pins, the `desktop` firmware branch) no longer apply.
> First light is now one panel on a Colorlight 5A-75B configured in LEDVision,
> then the Pi Zero 2 W + USB gigabit adapter in front of it —
> [`driver-colorlight.md`](../driver-colorlight.md) §4. The enclosure is a 2 × 2
> array — [`mechanical-plan.md`](mechanical-plan.md). The caliper items and the
> mechanical hardware below still apply.

Ordered so that **nothing blocks on a delivery**. Section A needs only what's
already on your bench; B is a caliper session; C is the shopping list, and it's
shorter than the earlier power plan implied.

---

## 0. Two corrections to earlier plans

**① `features/overrides.h` cannot do this port.** `config.h` states that "every
tunable in this file and in `net_config.h` is `#ifndef`-guarded", and that isn't
true of the parts we need. Only **12** symbols are guarded — the sleep settings
and the gamma / white-balance / saturation constants:

```
PF_SLEEP_ENABLED  PF_SLEEP_STOP_DMA  PF_SLEEP_CPU_MHZ  PF_AWAKE_CPU_MHZ
LED_GAMMA_R/G/B   LED_WB_R/G/B       LED_SAT_BOOST
```

Everything this build changes — `R1_PIN`, `PIN_A`, `PIN_B`, `PIN_D`, `B2_PIN`,
`PANEL_RES_W/H`, `PANEL_CHAIN`, the encoder pins, `DEFAULT_BRIGHTNESS` — is a
**bare `#define`**. So the fork has to patch `config.h` directly. See §A2 for
how to keep that tidy, and §D for the small upstream contribution that would
fix it for everyone.

**② If you build mains-first, you don't need the PD trigger or the buck.**
The PD-trigger → buck chain in [`power-plan.md`](power-plan.md) §2 exists to get
past USB's 5 V/3 A ceiling *when the source is a battery bank*. From the wall, a
**5 V 8–10 A PSU straight into the screw terminals** does the same job with two
fewer parts, no conversion losses, and no inrush negotiation.

I said earlier that the chain was "identical either way". That was imprecise —
the **device side** is identical (screw terminals, bulk cap, wiring gauge), and
only the supply upstream of it changes. Adding a bank later means adding the
trigger and buck then, not preserving them from now.

---

## A. Bench work — start today, needs nothing new

### A1. Toolchain

PlatformIO (the repo is a PlatformIO project, not Arduino IDE):

```bash
pipx install platformio        # or: pip install --user platformio
pio --version
```

### A2. Fork structure

`upstream/` is a pristine clone and stays that way. Since the port needs real
edits to `config.h` and `platformio.ini`, keep the delta as an explicit patch
series rather than a vendored copy — small repo, visible diff, and rebasing onto
a new upstream is one command.

```bash
git -C upstream checkout -b desktop
# ... make the edits from firmware-delta.md ...
git -C upstream commit -am "Matrix Portal S3: pinout, 2-panel chain, 8MB/quad"
mkdir -p firmware/patches
git -C upstream format-patch main --output-directory ../firmware/patches
```

Rebasing later is `git -C upstream rebase <new-tag>` and re-exporting. If a
patch conflicts, that's exactly the signal you want — upstream changed something
you depend on.

### A3. First light — one panel, USB power only

**This needs no PSU.** One P2 64×64 at low brightness plus the board is well
under what USB-C will give you, and it's the safest possible first test.

1. Matrix Portal S3 plugs directly onto the panel's HUB75 input header.
2. Apply the pinout patch (`firmware/patches/0001-*`, already on the `desktop`
   branch) and set `config.h` for **one** panel:
   ```c
   #define PANEL_RES_W 64      // one panel for now
   #define PANEL_RES_H 64
   #define PANEL_CHAIN 1
   #define DEFAULT_BRIGHTNESS 40   // ~15%, keep the current down
   ```
3. Leave `PANEL_PROFILE PANEL_STANDARD`. Only change it if the panel stays
   *completely* dark — see the long note in `config.h`, most panels need no init.
4. Build and flash. You should get Origin, upstream's built-in failsafe pattern.

> ⚠️ **Don't power the screw terminals and USB-C simultaneously** until you've
> checked how the Matrix Portal ties them together — they're both on the board's
> 5 V rail. For first light, USB-C alone. Once the PSU arrives, power from the
> terminals and flash over USB only after confirming that's safe on this board.

### A4. Second panel

Short HUB75 ribbon from panel A's **OUT** to panel B's **IN**, then put
`PANEL_RES_W` back to its stock value:

```c
#define PANEL_RES_W 128   // stock
#define PANEL_CHAIN 1     // stock — NOT 2, see firmware-delta.md §1
```

Two chained shift-register panels are electrically one 128-wide panel, so this
is upstream's untouched configuration. Still on USB, still dim. Confirm the
image is continuous across the seam and that column 64 isn't duplicated or
dropped.

### A5. `platformio.ini` and the partition table

Per [`firmware-delta.md`](firmware-delta.md) §2 — 8 MB flash, quad PSRAM, and a
new partition CSV, because `app3M_fat9M_16MB.csv` describes 12 MB that doesn't
exist. Expect to tune colour depth down. Do this *after* first light so you're
debugging one thing at a time.

### A6. Encoders, standalone

Independent of everything above — do it while waiting on parts.

1. Mount each PID 377 encoder to its 4991 breakout.
2. **Assign four distinct I²C addresses** via the jumpers (`0x36`–`0x3D`) and
   **write down which knob is which**. Getting this wrong scrambles the front
   panel relative to upstream's documented behaviour (K1 brightness, K2 network,
   K3 knob values, K4 pattern list).
3. Chain them with the STEMMA QT cables and run Adafruit's seesaw example to
   confirm all four enumerate and count cleanly.
4. Then write the I²C encoder driver that replaces upstream's GPIO path.

This is the largest piece of actual code in the desktop build.

---

## B. Measure — one caliper session

Ordered by how expensive each is to get wrong:

| # | Measure | Decides |
|---|---|---|
| 1 | **EC11 bushing thread length** (PID 377) | max bezel thickness — blocks stock choice |
| 2 | ~~Two panels butted, actual overall width~~ | ✅ 256 × 128, zero seam |
| 3 | ~~Panel depth incl. rear connectors~~ | ✅ 14.5 (17.8 over the pins) |
| 4 | **4991 breakout outline** | confirms 45 mm knob pitch doesn't collide |

Details and why each matters: [`mechanical-plan.md`](mechanical-plan.md) §4.
#2 and #3 done 2026-10-03, along with the insert and pin positions — the model is
now at P2 ([`mechanical-plan.md`](mechanical-plan.md) §2.1). #1 and #4 remain.

---

## C. Order

### Power (mains-first)

| Item | Spec | Note |
|---|---|---|
| **5 V PSU** | 5 V, 8–10 A (40–50 W) | Meanwell GST60A05 class. Covers the ~6.5 A worst case with margin |
| Barrel jack | panel-mount + pigtail | matched to the PSU |
| **Bulk capacitor** | 1000 µF, 16 V electrolytic | at the panel end — upstream fits one for the same reason |
| Wire | 18 AWG min, 16 AWG preferred | red/black, short runs |
| Inline fuse | holder + 8 A fuse | between PSU and board |
| Power switch | optional | rated for 8 A DC |

**Not needed unless you add a bank later:** PD trigger board, buck converter.

### Mechanical

| Item | Note |
|---|---|
| M3 screws + standoffs | panel mounting to the carrier plate |
| Short HUB75 ribbon | panel A→B. Check whether your panels shipped with one |
| Bezel stock | **buy after measurement #1** — thread length sets thickness |
| Carrier plate | 3 mm aluminium / acrylic, or printed with a metal spine |
| Filament | white body, black knobs, per upstream's scheme |

### Already on the bench

Matrix Portal S3 · 2 × P2 64×64 GOB · 4 × 4991 breakouts · 4 × PID 377
encoders · 4 × STEMMA QT 100 mm · both knob sets · LD2450 (optional here)

---

## D. Worth sending upstream

The pin block being bare while `config.h` claims everything is guarded is a
small, well-scoped bug, and fixing it directly serves this fork: wrap the HUB75
and encoder pin defines in `#ifndef`, and **any** variant — Matrix Portal
included — becomes an `overrides.h` file with **zero patches**.

Upstream explicitly wants this kind of contribution. The
[core-and-variants RFC](../../../upstream/docs/rfc-core-and-variants.md) exists
precisely so that variants don't have to fork the tree, and `overrides.h` is
described as the mechanism for exactly this. The pins were simply missed.

It would also delete §A2 of this document, which is the sign of a good patch.

---

## Suggested order of operations

```
  today            A1 toolchain ─► A2 fork structure ─► A3 first light (1 panel)
                                                              │
  parts arrive     C order ──────────────────────────────┐    ▼
                                                         │  A4 two panels
  bench session    B measure ──► bezel stock ──────────┐ │    │
                                                       │ │    ▼
                                                       │ └─► A5 platformio/partitions
                                                       │      │
                   A6 encoders (any time) ─────────────┼──────┤
                                                       ▼      ▼
                                                      enclosure + assembly
```

A3 is the milestone that proves the whole approach. It needs nothing you don't
already have, and if the four pin edits are right it should take an evening.
