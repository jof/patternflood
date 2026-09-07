# Power Plan — Desktop

Companion to [`mechanical-plan.md`](mechanical-plan.md).

Original goal: **USB-C in, charge an internal bank, run from the bank, and pass
through when plugged in and full**, using a sealed COTS bank rather than
building a charger.

That instinct was right for the *combined* build. Since the lidar moved to the
[wall project](../wall/), it's worth asking whether the battery is still wanted
at all — §0 — before spending money on one.

---

## 0. Do you actually want a battery?

You described this one as a **"USB-C desktop toy"**. If that's the frame, the
battery may have left with the lidar.

**What dropping it removes**, all at once: the pass-through-charging hunt, the
auto-shutoff-during-sleep problem, cell heat inside a closed box, the inrush
fault, ~30 mm of enclosure depth (bay [4] — the single largest contributor), the
weight, and a lithium pack in a wooden box on your desk. That is most of §3
below, deleted.

**What it costs:** the thing is tethered.

| | Mains only | With a bank |
|---|---|---|
| Supply | USB-C PD wall wart, 65 W | + bank, PD trigger stays the same |
| Enclosure depth | **~35–45 mm** | ~60–75 mm |
| Failure modes | none of §3 | all of §3 |
| Cost | ~$25 | ~$25 + $60–120 |

**Recommendation: build it mains-first** — and note that mains-first is
*simpler* than §2, not just cheaper. The PD trigger and buck exist to get past
USB's 5 V/3 A ceiling **when the source is a bank**. From the wall, a **5 V
8–10 A PSU straight into the screw terminals** does the same job with two fewer
parts and no conversion losses.

What carries over is the **device side** — screw terminals, bulk cap, wire
gauge, fusing — which is identical either way. Adding a bank later means adding
the trigger and buck *then*. So leave depth in the back for a bank, buy the
PSU now, and defer §2 until you actually want the thing to be portable.

*(An earlier draft of this said the chain was "identical either way". It isn't;
only the device side is. Corrected in [`build-prep.md`](build-prep.md) §0.)*

### If you do want the bank now

Buy on these four specs, in this order. The first two are the ones that make
banks unsuitable, and neither is on the front of the box:

1. **Pass-through charging** (charge and discharge simultaneously, sometimes
   sold as "UPS mode"). Most banks cut output when a charger is connected.
   **Must be explicitly documented** — treat silence as "no".
2. **Low-current / "small device" mode.** Banks auto-shut-off under light load
   so they don't drain in a bag, which is exactly what Patternflow's sleep mode
   looks like. Without it, the device can't be woken remotely.
3. **≥45 W USB-C PD output.** Not 5 V/3 A — see §2, that ceiling is the whole
   problem. 45 W gives 12 V or 15 V at 3 A with margin. 65 W is better.
4. **20 000 mAh (~74 Wh).** Comfortably under the 100 Wh airline limit, ~6 h
   typical runtime. Bigger mostly buys depth in bay [4].

**Where to look.** Specific SKUs churn faster than this document will, so buy on
the criteria, not on a model number I name today. That said, the category that
actually advertises specs 1 and 2 is **banks sold for always-on embedded and
IoT use** — **Voltaic Systems** (V50, V88) is the clearest example, built
explicitly for pass-through and no auto-shutoff, and priced accordingly.
Consumer brands are hit-and-miss: **INIU** markets a low-current mode, and some
**Anker** models charge while discharging, but both vary by SKU and neither
guarantees it across a range. Check the current spec sheet for the exact model,
and if pass-through isn't stated in writing, assume it isn't there.

**Measure the bank before designing the back half of the case** — its dimensions
set bay [4], per [`mechanical-plan.md`](mechanical-plan.md) §2.2.

---

## 1. Load budget

| Load | Typical | Worst case |
|---|---|---|
| 2× Waveshare P2 64×64 | ~1.5–2 A | **6 A** (2 × 3 A spec, 30 W) |
| Matrix Portal S3 | ~0.15 A | 0.25 A |
| LD2450 radar *(optional)* | ~0.07 A | 0.1 A |
| 4× seesaw encoder + NeoPixel | ~0.05 A | 0.15 A |
| **Total @ 5 V** | **~1.9 A (10 W)** | **~6.5 A (33 W)** |

> The VL53L9CX is **not** in this budget — it moved to the
> [wall project](../wall/). That removes ~0.15 A of average draw and, more
> usefully, a pulsed two-VCSEL load that would have been fighting the panel
> supply on the same 5 V rail.

The worst case is not theoretical. Upstream measured **4.8 A at 5 V** on a
full-white pattern at max brightness across the same 8192 pixels — enough that
they note the connector gets warm and that a total-pixel-power clamp is being
added to the firmware. Our panels are the same pixel count at a finer pitch, so
expect the same order: **~5 A on full white, 6 A+ if you also want headroom.**

Typical generative patterns sit around a third of that.

---

## 2. The constraint that decides everything

**A USB port at 5 V is limited to 3 A — 15 W.** That is the USB spec ceiling
for 5 V without PD negotiation, and it is less than half our worst case.

So a sealed bank's ordinary 5 V USB output **cannot** feed this display at full
brightness. There are exactly three honest ways out:

| Option | How | Verdict |
|---|---|---|
| **A. PD trigger + buck** | Negotiate 12 V @ 3 A (36 W) from a PD bank, step down to 5 V @ ~7 A | ✅ **Recommended.** Full brightness, one cable, standard parts |
| **B. Two 5 V ports** | One USB port per panel, commoned grounds | ⚠️ Works, but relies on undocumented per-port limits and creates a ground-loop/backfeed hazard between ports |
| **C. Clamp brightness** | Firmware power limit to stay under 3 A | ✅ Legitimate, and worth doing *anyway* as a safety net — but as the *only* strategy it permanently costs you the top of the brightness range |

**Do A, and implement C as a backstop.** They're complementary: the clamp
protects the converter and the bank regardless of which supply is attached.

### Recommended chain

```
  USB-C wall charger (PD, ≥45 W)
        │
        ▼
  ┌──────────────────────────────────────┐
  │  Sealed USB-C PD power bank          │   ← the one purchasing decision
  │  • PD in AND PD out                  │      that matters
  │  • pass-through charging  ⚠ VERIFY   │
  │  • ≥36 W out, ≥20 000 mAh            │
  └──────────────────┬───────────────────┘
                     │  USB-C
                     ▼
        ┌────────────────────────┐
        │  PD trigger / decoy     │  fixed 12 V request
        │  board (12 V)           │
        └────────────┬───────────┘
                     │  12 V
                     ▼
        ┌────────────────────────┐
        │  Buck converter         │  12 V → 5.0 V, ≥8 A rated
        │  + bulk cap (1000 µF)   │  synchronous, not a linear reg
        └────────────┬───────────┘
                     │  5 V, thick wire, short run
                     ▼
        Matrix Portal S3 screw terminals ──► panels
```

Notes on this chain:

- **Rate the buck for 8 A, not 6.** Cheap modules are rated optimistically and
  derate hard with temperature — inside a sealed enclosure that matters.
  Synchronous buck, not linear: a linear regulator dropping 12→5 at 5 A would
  dissipate 35 W as heat.
- **Feed the Matrix Portal's screw terminals, not its USB-C port.** This is the
  same rule upstream states emphatically for its `J4` terminal: never run panel
  current through the DevKit's USB port. The Matrix Portal S3 provides +5 V and
  GND M3 screw terminals precisely for this.
- **Keep the 5 V run short and fat.** At 6 A, 300 mm of thin wire is a
  meaningful voltage drop and the panels will show it as a brightness gradient
  across the display. 18 AWG minimum, 16 AWG preferred.
- **Bulk capacitance at the panel end.** Upstream puts 1000 µF/16 V on the
  board for exactly this reason — the panel's row-scan draws in sharp pulses.

---

## 3. The four things that go wrong

These are the failure modes specific to running off a sealed bank, and they are
all worth knowing *before* buying one.

**1. Pass-through charging is rare, and often bad.**
Most banks will not charge and discharge simultaneously; they cut the output
when a charger is connected, which browns out the display. Of those that do,
many implement it poorly (charging the cell *through* the output path, which
runs the cell hot and shortens its life). **This is the single spec to verify
before purchase** — look for explicitly documented "pass-through charging" /
"UPS mode", and treat unmarked banks as not having it.

**2. Auto-shutoff on low draw.**
Banks are designed to turn themselves off when they see a small load, so they
don't drain in a bag. Patternflow's **sleep mode** — panel dark, HUB75 transfer
stopped, board idling on Wi-Fi — is exactly the low-draw condition that triggers
this. You'd lose the ability to wake the device remotely, which is one of the
nicer upstream features. Mitigations: pick a bank with a documented low-current
or "small device" mode, or keep a deliberate trickle load (the encoder NeoPixels
at low brightness will do it) during sleep.

**3. Heat in a sealed box.**
Charging and discharging a 20 000 mAh cell while a buck converter dissipates a
few watts, inside a closed enclosure, with an LED panel radiating in front of
it. Bay [4] in the stackup needs **ventilation**, and the bank should not be
sandwiched directly against the panel backs. Put the buck converter near the
back cover vents, not buried.

**4. Inrush on connect.**
1000 µF plus a panel's input capacitance looks like a short circuit for the
first milliseconds. Some banks and PD sources read that as a fault and refuse to
start. If the display won't come up on first connect but works when the bank is
already running, that's this — and the fix is a soft-start / inrush limiter, not
a bigger bank.

---

## 4. Runtime

At the ~2 A (10 W) typical draw, and taking ~85 % for cell-to-5 V conversion:

| Bank | Nominal energy | Usable | Typical runtime | Full-white runtime |
|---|---|---|---|---|
| 10 000 mAh | ~37 Wh | ~31 Wh | ~3 h | ~1.2 h |
| 20 000 mAh | ~74 Wh | ~63 Wh | ~6 h | ~2.5 h |
| 26 800 mAh | ~99 Wh | ~84 Wh | ~8 h | ~3.3 h |

Consistent with upstream's measured "roughly 4 h per 10 000 mAh at max
brightness". **20 000 mAh is the sweet spot** — 26 800 mAh is the practical
ceiling for air travel (100 Wh limit) and adds depth to bay [4] for runtime
you probably won't use.

---

## 5. Why not build the charger

For the record, since it's the obvious "do it properly" temptation:

A real integrated design is a USB-C PD sink controller, a multi-cell Li-ion
charger IC (BQ25703-class), a 2S or 3S pack with protection, a fuel gauge, and
a 5 V buck — plus the cell-balancing, thermal cutoff and mechanical protection
that make a lithium pack safe in a wooden or plastic box you carry around.

That is a genuinely good project and a completely different one from building a
Patternflow. **The sealed bank is the right v1** and it is not a compromise you
have to undo later: the PD trigger + buck stage stays identical if you ever
swap the bank for a custom pack. Only the thing upstream of the trigger board
changes.

---

## 6. Decisions to make

1. **Buy the bank first.** Its dimensions set bay [4], which dominates total
   enclosure depth — you cannot finalise the back half of the case without it.
   Criteria: ≥36 W PD out, ≥20 000 mAh, **documented pass-through charging**,
   documented low-current mode.
2. **PD trigger voltage: 12 V.** 9 V works and needs less step-down ratio, but
   12 V @ 3 A gives 36 W against 27 W and more margin at the buck input.
3. **Implement the firmware power clamp** regardless of supply — see
   [`firmware-delta.md`](firmware-delta.md).

---

## 7. The bank: Voltaic V50

Selected after checking candidates against §0's four criteria. **Pass-through
plus always-on plus ≥36 W turns out to be an empty set** — nothing found meets
all three, so this is a considered compromise, not a clean win.

| | Voltaic V50 | Voltaic V88 |
|---|---|---|
| Size | **118 × 82 × 26 mm**, 368 g | 218 × 137 × 22 mm |
| Capacity | 13,400 mAh / **48 Wh** | 24,000 mAh / 88.8 Wh |
| Output | USB-C PD 5V/3.6A, 9V/2.2A, 12V/1.6A → **~20 W** | DC **12V/6A = 72 W** |
| Always-on | ✅ documented, ~7 mA idle | ✅ documented |
| Pass-through | ✅ **documented** | ❌ **see below** |

> ⚠️ **The V88 does not do pass-through, whatever the retailers say.** Multiple
> listings advertise it, but the actual usage documentation states: *"Do NOT
> simultaneously charge the Voltaic V88 power bank and use it to power your
> robot."* Charge-while-running is the entire reason for a fixed USB-C inlet, so
> that rules it out despite the far better 72 W output.

### The V50's ceiling, and why it's acceptable

Waveshare rates each P2 64×64 panel at **5 V / 3 A, ≤15 W**, so the pair's rated
maximum is **30 W**. Upstream measured **4.8 A (24 W)** for real full white on the
same 8192 pixels, and about a third of that for a typical generative pattern.

The V50 delivers ~20 W, or ~18 W after the buck:

| | Draw | V50 |
|---|---|---|
| Typical pattern | ~8 W | ✅ comfortable |
| Measured full white | ~25 W | clamp to ~72 % |
| Rated maximum | 30 W | clamp to ~60 % |

So **every realistic pattern runs at full brightness**; only near-full-white
frames get clamped. The firmware power clamp
([`firmware-delta.md`](firmware-delta.md) §5) therefore moves from prudent to
**required** — it is what keeps the bank inside its output limit.

Runtime at ~11 W typical: **48 Wh × ~0.85 ≈ 3.7 h**. Under 100 Wh, so it flies.

### Mounting

The bank straps to the **inside of the removable back cover** with two velcro
straps through obround slots, so lifting the cover takes the bank with it and
there is no separate battery tray. Obround rather than rectangular because a
strap slot is loaded in tension every time it is tightened, and sharp internal
corners are where soft basswood splits.

Modelled at `bankX = -80`, offset left so the Matrix Portal gets the rest of the
bay. Verified clearances: **1 mm** to the brace backs at z −17.5, **1 mm** to the
back cover's inner face at z −45.5, 6.5 mm to the left wall.

`bayDepth` is now **34 mm** — clear bay space is `bayDepth − 6`, independent of
panel depth, so 34 gives the 28 mm the 26 mm bank needs.

### USB-C inlet, not a barrel jack

A **panel-mount USB-C passthrough** in the right wall replaces the DC barrel
jack. One external connector, and it is the same one the bank charges through,
so plugging a charger into the case charges the bank in place.

Cutout and flange screw dimensions are placeholders — **verify against the actual
part**, they vary between panel-mount USB-C extensions. Positioned at
`usbY = 0, usbZ = -30`, clear of the corner fingers and the rail mortises.

### Still to resolve

1. **Bank port orientation.** Its USB-C ports must face the open bay (+x), not
   the left wall 6.5 mm away. Check which edge they're on before finalising
   `bankX`.
2. **The cable to the buck must survive cover removal** — long enough to hinge
   the cover aside, or a connector inline.
3. **Matrix Portal vs bank.** The bank occupies x −139…−21. If the panel's HUB75
   header sits centrally or on the left panel, `bankX` has to move. Another
   thing the caliper session settles.
