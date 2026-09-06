# Power Plan

Companion to [`mechanical-plan.md`](mechanical-plan.md).

Goal, as stated: **USB-C in, charge an internal bank, run from the bank, and
pass through when plugged in and full.** Start with a sealed COTS bank rather
than building a charger.

That instinct is right, and this plan backs it — with one hard constraint that
has to shape the choice of bank, and four failure modes that bite people who
do this naively.

---

## 1. Load budget

| Load | Typical | Worst case |
|---|---|---|
| 2× Waveshare P2 64×64 | ~1.5–2 A | **6 A** (2 × 3 A spec, 30 W) |
| Matrix Portal S3 | ~0.15 A | 0.25 A |
| LD2450 radar | ~0.07 A | 0.1 A |
| VL53L9CX lidar | ~0.15 A | 0.3 A ⚠ estimate |
| 4× seesaw encoder + NeoPixel | ~0.05 A | 0.15 A |
| **Total @ 5 V** | **~2.1 A (11 W)** | **~6.8 A (34 W)** |

> ⚠️ The lidar figure is an **estimate**, not a datasheet value. The VL53L9CX
> drives two VCSELs for 9 m flood illumination, so it draws materially more than
> the milliamp-class ToF parts it's easy to mistake it for — and it draws in
> pulses synchronised to ranging. Measure it during the standalone bring-up in
> [`lidar-plan.md`](lidar-plan.md) §6, and give it local decoupling rather than
> hanging it off the end of a 400 mm STEMMA QT chain.

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
