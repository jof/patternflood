# Driving the Panels: Colorlight 5A-75B + Raspberry Pi 5

> 🔁 **2026-10-21: the Pi Zero 2 W + USB gigabit adapter became a Raspberry Pi 5**, which has gigabit
> Ethernet on board. The Zero's reasoning is kept below where it still explains a choice.

Decided 2026-10-11/12. This replaces the Adafruit Matrix Portal S3 as the
desktop build's controller, and with it the 2 × 1 landscape layout. The display
is now a **2 × 2 array of Waveshare P2 64 × 64 GOB panels**: 128 × 128 px,
256 mm square.

The reasoning for the Pi + Colorlight split was laid out long before it was
taken, in the wall project's [`compute-options.md`](../wall/compute-options.md)
(option D). What tipped it here was that the P2 panels are physically small, so
more of them is the point. That made panel count, and a driver that scales, the
pressure — not compute.

---

## 1. What this gives up

Said plainly, because [`compute-options.md`](../wall/compute-options.md) §3
spells out the cost: this build **no longer runs upstream Patternflow
firmware**. The `.pfm` loader, the frozen ABI, the web console and the compiled
community pattern library are all ESP32 binaries. A Pi host renders its own
frames. The patterns' JavaScript source form is the bridge back to that
library, if one is wanted (§5).

[`firmware-delta.md`](firmware-delta.md) describes the abandoned ESP32 fork and
is kept for history.

---

## 2. The panels are the easy kind

Chip markings read off one panel, 2026-10-11:

| Marking | Part | Meaning for the driver |
|---|---|---|
| `6124HJ C003173` | FM6124-family column driver | Plain shift-register driver, **no init sequence** — not an FM6126A-style "needs a config write" chip, and not S-PWM |
| `RUC7258G PAE45012` | Ruichips RUC7258 | 8-channel row driver with an internal 3-to-8 decoder and anti-ghost blanking; two cascade for 16 rows, so plain **A–E binary addressing** at 1/32 scan |
| `MW245BC` | MW74HC245 | Signal buffer, no effect |

Every HUB75 driver handles this combination. **Expect an hour of LEDVision
"smart settings"** at bring-up anyway: a user with a 64 × 32 RUC7258 panel
reported only a garbled top half on a 5A-75B
([ESP32-HUB75 discussion #501](https://github.com/mrcodetastic/ESP32-HUB75-MatrixPanel-DMA/discussions/501)),
which is the classic symptom of a wrong scan or data-group setting, not of a
chip that cannot be driven.

---

## 3. Parts and topology

```
   mains ─► IEC (right wall) ─► LRS-50-5 ─┬─ 5 V ─► 4 × panel power (star)
                                          ├─ 5 V ─► Colorlight 5A-75B
                                          └─ 5 V ─► Pi 5 (own leads, USB-C pigtail)

   Pi 5 ─ on-board gigabit Ethernet ─ Cat6 ─► 5A-75B
                                              HUB75 ×4 (J1–J4)
                                                one panel each
   Pi 5 ─ I²C (STEMMA QT) ─► 4 × Adafruit 4991 encoders
   Pi 5 ─ Wi-Fi ─► your network
```

- **Colorlight 5A-75B** — Lattice ECP5, two gigabit PHYs, eight HUB75 outputs.
  **One panel per output**, J1–J4: no chain mapping, short equal ribbons, and
  J5–J8 left for the two spare panels.
- **Raspberry Pi 5** — gigabit Ethernet on board, which the 5A-75B needs, and
  the headroom to render 16 384 px a frame in JavaScript without budgeting.
  It replaced a Pi Zero 2 W, which needed a USB gigabit adapter because the
  5A-75B **will not link at 100 Mbit**
  ([FPP forum](https://falconchristmas.com/forum/index.php?topic=6871.0)), so
  the common 100 Mbit dongles fail. A gigabit adapter on the Zero's USB 2.0
  links at 1000 and moves ~300 Mbit, against the ~24 Mbit/s that 16 384 px at
  60 fps needs. A Zero 2 W driving a 192 × 128 matrix (1.5 × this one) through a
  5A-75B is reported working
  ([FPP forum](https://falconchristmas.com/forum/index.php?topic=15657.0)).
- **Cooling:** fit the Pi 5 **Active Cooler**. The box is closed, and the
  cooler's top is ~5 mm from the back cover (`Bay obstructions` carries an
  envelope for it). Vent slots in the cover over the Pi are an open item.

---

## 4. Power: one LRS-50-5, capped

| Load | Draw |
|---|---|
| LRS-50-5 rating | 10 A; plan on **8 A continuous** |
| Colorlight 5A-75B | ~0.8 A (the two PHYs are the hungry part) |
| Raspberry Pi 5 + Active Cooler | plan **1.6 A** (~0.6 A idle, bursts toward 2 A rendering; no USB devices) |
| **Left for the panels** | **~5.6 A ≈ 1.4 A per panel** (was 1.65 with the Zero) |
| Panel at full white | 2.4 A measured (upstream, on an ESP32 driver); 3 A Waveshare supply rating |
| Typical generative pattern | ~0.8 A per panel |

So the panels need a cap, but it rarely engages:

- **Cap per frame in the renderer, not with a global brightness ceiling.**
  Estimate each frame's current from the post-gamma values actually sent, and
  scale that frame down only when it exceeds the budget. Upstream's firmware
  is adding the same total-power clamp. The PSU's overload hiccup stays as
  the backstop.
- **Calibrate on the real driver first.** The 2.4 A figure is from an ESP32
  DMA driver; the Colorlight may run a higher output duty. Measure one panel at
  full white, and full red, green and blue separately for per-channel weights.

The Pi takes its 5 V from its own pair off the PSU terminals, not through a
panel's harness — the same arrangement as Adafruit's RGB matrix bonnet, which
back-powers the Pi from the panel supply. Set the LRS trim to ~5.15 V so the Pi
sees ≥ 5.0 V under load. The Pi 5 is fed through a **5 V → USB-C pigtail**, which
does no USB-PD, so it assumes a 3 A supply and warns. The LRS can deliver more,
so set `PSU_MAX_CURRENT=5000` in the bootloader config (`rpi-eeprom-config -e`).

---

## 5. Software path

> 🔁 **2026-10-21: no LEDVision.** The stock gateware was replaced by the open
> [receiver75](https://github.com/dgym/receiver75) gateware, loaded over JTAG
> with a Glasgow, and it drives all four panels correctly. Steps 1–2 below are
> superseded; bring-up notes and tools are in
> [`firmware/colorlight/`](../../firmware/colorlight/README.md). The card is a
> **v8.2**, and the stock flash is backed up.
>
> The panels use **J1, J4, J5 and J8**, not J1–J4. receiver75 takes UDP at
> 192.168.75.39 and has 16 slots, two per connector; each connector Jn shows
> slot 2n−1. Upper-left J5 is slot 9, upper-right J8 is 15, lower-left J4 is 7,
> and lower-right J1 is 1, all upright. `r75_frame.py` maps a 128 × 128 frame
> onto them.

1. **Bring-up:** LEDVision (Windows-only; a VM with a bridged NIC works) to
   configure the card for these panels — 64 × 64, 1/32 scan, FM6124, 138-type
   decoding — and *save to receiver* on both the screen-parameter and mapping
   tabs.
2. **First pixels from the Pi:** Falcon Player (FPP) supports Colorlight
   receivers over Ethernet on a Pi. That proves the Pi + card chain before
   anything is written.
3. **The instrument:** a renderer on the Pi that reads the four encoders over
   I²C, runs patterns, applies the per-frame cap, and streams frames to the card
   — through FPP, or directly once the protocol is in hand. With receiver75,
   that's UDP framebuffer writes, as `firmware/colorlight/r75_frame.py` does. Whether the Live
   Editor's **JavaScript** patterns can run here (QuickJS) is the question that
   decides how much of the community library comes along. (On the Zero this
   needed careful budgeting; on the Pi 5 it should not.)
4. **Read-only rootfs** before the box is closed — it will be switched off at
   the wall.

---

## 6. Where it lives in the box

The electronics live on a removable **electronics tray**: two 3 mm ply sheets,
286 × 94, screwed to the back of the middle panel brace, every board on its rear
face with the component side facing **back** (enclosure model: `Enclosure
shell` for the tray, the brace sheets and the spacer rings; `Bay obstructions`
for the boards). Nothing is fastened to the back cover and no cable runs to it.

| | Centre (x, y) | Model | Mounting |
|---|---|---|---|
| 5A-75B | (55.3, 0), long axis **horizontal**, RJ45 end toward −x | **measured** — see below | 4 × M3 x 8 into nuts in the tray |
| Raspberry Pi 5 | (−108, 0), **on end**: USB/Ethernet edge down, USB-C edge toward the card | official drawing, 85 × 56, holes 58 × 49; ports and Active Cooler as envelopes | **4 × M2.5 x 8** into M2.5 nuts in the tray (`#piScrewDia`, `#piNutAF`) — its holes are 2.7 mm |
| Tray | — | 2 sheets, 279.3 × 94 (rev 2; rev 1 285.6), y ±47 | 4 × M3 x 16 into nuts in the middle brace |

**Every nut is a three-layer sandwich** — clearance / hex / clearance — the same
as the back-cover rails, so no nut is ever just sitting in a pocket, and nothing
is glued. Tightening pulls the nut toward the screw head, onto the clearance
layer on that side; the layer on the far side stops it falling out when the
screw is out:

| Joint | Clearance (far side) | Hex — the nut | Clearance (pulled against) |
|---|---|---|---|
| Back cover → rails | rail C | rail B | rail A |
| Tray → middle brace | brace front sheet (against the panels) | brace middle sheet | brace rear sheet |
| Board → tray | tray front sheet | tray rear sheet | a 3 mm ply ring under the board |

```
   panel │ brace front │ brace mid │ brace rear │ring│ tray front │ tray rear │ring│ board
         │   clear     │  HEX nut  │   clear    │    │   clear    │  HEX nut  │    │
              tray screw  M3 x 16 ◄───────────────────────────── (from behind)
                                                      board screw  M3 x 8 ◄──── (from the board side)
```

**How it goes together:**

1. **Brace:** fit the middle brace's front and middle sheets, drop the four tray
   nuts into the middle sheet's hex pockets, then fit the rear sheet — the nuts
   are now trapped. All three sheets are tenoned into the side walls, and the
   panel screws clamp them together.
2. **Panels on**, as before (the middle brace's panel screws are 6 mm longer).
3. **On the bench**, tray face down: board nuts into the rear sheet's hex
   pockets, a ring over each, the board on top, M3 x 8 down through the
   Colorlight and M2.5 x 8 through the Pi (its rings are bored for M2.5). The
   front sheet under the pockets keeps the nuts from falling through. Plug the
   four HUB75 ribbons into the card.
4. **Tray in from the back:** plug each ribbon into its panel's IN, then four
   M3 x 16 through the tray and a ring into the brace's nuts. (M3 x 16 takes the
   full nut and stops 2 mm short of the panel; M3 x 18 would touch it.)
5. Power wiring, then the back cover — which carries nothing.

**To take a panel off:** back cover, then the tray (four screws, unplug), and
the panel screws are exposed. The tray is the only thing that covers them.

Layout: the card sits right of centre, RJ45 face at x −20. The Pi 5 stands on
end at the left: lying flat, its Ethernet jack would face the card's only ~30 mm
away, with no room for two plugs. On end, its jack points **down** past the
tray's bottom edge, and a short (~20 cm) flat patch cable loops round to the
card. Its USB-C power plug points into the gap toward the card (~31 mm to the
tray screw). The tray stops at
|y| 47, 2 mm clear of the panels' 5 V plugs, and the HUB75 ribbons wrap round
its top and bottom edges to the panels' IN ports (each panel's **IN is on the
left seen from behind**). Depth: brace 9, ring 3, tray 6, ring 3, then the
boards — the deepest part, the Pi 5's stacked USB, ends **3.2 mm** short of the
back cover (the card's terminal block, 5 mm).

### The 5A-75B, measured

From 600 dpi scans of both faces, 2026-10-12 — outline and holes off the back,
which lay flat; component outlines off the front, registered through the holes.

![5A-75B, back](img/colorlight-5a-75b-back.jpg)

| | Component side up, origin lower-left, RJ45 edge at top (mm) |
|---|---|
| PCB | **91.76 × 143.67** |
| Mounting holes | Ø4.23 plated, at (5.11, 139.08), (86.51, 139.35), (16.07, 3.81), (76.44, 3.96) — the bottom pair is inset ~16 mm |
| HUB75 J1–J8 | 2 × 8 shrouded, in two columns at x ≈ 11.9 and 80.3, rows at y ≈ 98.6, 71.8, 44.4, 17.1; **angled ±25° off vertical**, mirrored |
| RJ45 | dual, ganged, x 29.5–63.5, overhangs the top edge by ~3.5 |
| 5 V in | 2-way barrier terminal, x 66–86.5 at the top edge (silk: D5V / GND); also a 4-pin header, right edge (GND GND D5V D5V) |

Heights, calipered 2026-10-12: PCB **1.7**; above it RJ45 **13.8**, HUB75
shrouds **9**, terminal block **14.8** (the tallest), big JST **10.6**, small
JST **6.38**. The Pi 5's PCB is taken as 1.6 mm, unmeasured; its port heights are the
drawing's, as one envelope over the whole USB/Ethernet edge.

Because the boards face back, each HUB75 ribbon makes a short U: out of the
card's header toward the cover, round the card's and the tray's edge, and
forward into the panel's IN.
