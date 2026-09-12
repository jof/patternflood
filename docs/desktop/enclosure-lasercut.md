# Enclosure — Laser-Cut Finger-Joint Box

Supersedes the fabrication section of [`mechanical-plan.md`](mechanical-plan.md) §3.
Geometry, stackup and clearances there still hold; this is the how.

**Material:** 3 mm basswood, finger-jointed, doubled selectively.
**CAD:** Onshape. **Cut:** CO₂ laser.

---

## 1. The one structural idea

Mixing thicknesses in a finger-jointed box breaks the joints — fingers only mesh
if every mating panel is the same thickness. So:

> **The structural box is 3 mm everywhere and finger-jointed. Doublers are
> separate 3 mm layers glued to the inside face, clear of the joints.**

Model the doublers as their own parts, inset from the panel outline by at least
the finger depth (3 mm) on any jointed edge. That way Onshape's Laser Joint
feature sees a uniform 3 mm box and the doublers are just laminations.

### Laminate the doublers cross-grain

Basswood sheet is usually **solid wood, not ply** — it has a grain direction and
it will split along it. That matters most in the narrow rails above and below a
256 mm aperture, which is exactly where the front face is weakest.

Gluing the doubler with its **grain at 90° to the base layer** makes plywood
locally, right where you need it. This is the single highest-value trick in the
whole design and it costs nothing but sheet orientation.

*(If your stock is basswood **ply**, this is moot — check which you have.)*

---

## 2. Where doubling is actually needed

| Location | Doubled? | Why |
|---|---|---|
| **Front face** | ✅ full, cross-grain | Narrow rails around the aperture; encoder bore strength; stops the face racking |
| **Panel cross-braces** | ✅ cross-grain | Carries ~0.8 kg of panel into the side walls |
| **Wall-mount points** | ✅ local pads | Soft wood strips out under a keyhole |
| Side walls | ❌ single | Finger joints work fine in 3 mm shear |
| Back cover | ❌ single | Removable, carries nothing |
| Top / bottom | ❌ single | Unless the top carries a handle |

Doubling the front is the important one and it pays twice: it gets you to
**6 mm at the knob positions**, which is the right thickness for an EC11.

---

## 3. Encoder bores — the reason 6 mm is right

Soft basswood plus knob torque will wallow a 3 mm bore out over time. The
doubled front fixes it, and 6 mm happens to suit the part:

```
   knob (20 mm or 1")
        ▼
   ┌─────────┐
   │  ╭───╮  │   ← set screw
   ═══╡███╞═══   nut + washer
   ▓▓▓│███│▓▓▓   ← L0 outer  3 mm ─┐
   ▓▓▓│███│▓▓▓   ← L1 doubler 3 mm ─┴ 6 mm total, grain crossed
      │███│      ← EC11 bushing, thread ~7 mm  ⚠ MEASURE
      └─┬─┘
    ┌───┴────┐
    │  4991  │  breakout hangs off the encoder body
    └────────┘
```

- **Bore Ø7 mm** through both layers. Cut both layers in the same operation if
  you can, or cut them together after lamination — concentricity matters more
  than either hole's absolute position.
- **Washer under the nut.** Spreads the clamp load; without it the nut crushes
  a ring into the basswood and goes loose.
- **Anti-rotation nub.** Many EC11s have a small locating boss beside the
  bushing. Check the PID 377 and add the relief hole if it's there — otherwise
  the body rotates and the wiring twists.
- **Bushing thread length caps total panel thickness.** ~7 mm is typical, which
  leaves 6 mm of wood plus a nut comfortably. **Measure before committing** —
  this is measurement #1 in [`build-prep.md`](build-prep.md) §B, and it's the
  one that decides whether 6 mm is viable at all.

---

## 4. Aperture — and why there's no front lip

> ⚠️ **Corrected 2026-09-08 from measured panels.** This section previously said
> tiling panels are "128 mm of pixels in a 128 mm module, edge to edge". They are
> not. The panel body is **undersize** and the gap between panels is **required**
> for pixel continuity — measured on a P3: body 190, pitch 192, gap 2, with
> 189 mm of pixel span, i.e. 0.5 mm of border per edge. The model now separates
> `#panelW` (tiling pitch) from `#panelBody` (the physical part), and the
> aperture is derived from `#panelBodySpan`. Full measurements and the arithmetic
> are in [`../wall/README.md`](../wall/README.md) §8.

Tiling LED panels have a **negligible** bezel margin — half a pixel pitch, so
0.5 mm on P2. That is far too little to retain a panel from the front, so **the
panels still cannot be held from the front** the way a picture frame holds glass,
and everything below stands.

Consequences:

- **Retention is from behind**, via the panels' rear threaded posts onto the
  cross-braces (§5). The front face is purely cosmetic and locating.
- **Aperture ≈ 256 × 128 mm**, or **minus ~0.5 mm** for a crisp edge that hides
  the module seam. Half a millimetre clips the outer ~0.25 px, which is
  invisible; going further starts eating real pixels.
- Use the **measured** butted width, not 256 nominal — measurement #2.
- The face sits **flush on the GOB panel front**. No air gap, no diffuser: the
  epoxy fill already diffuses. See [`mechanical-plan.md`](mechanical-plan.md) §2.2.

---

## 5. Panel mounting

Don't hang 800 g of panel off the front face. Two horizontal **cross-braces**,
doubled and cross-grained, finger-jointed into both side walls:

```
      ┌───────────────────────────────────┐
      │  ╔═══════════════════════════════╗│  ← top wall
      │  ║                               ║│
      │══╬═══════════════════════════════╬│  ← brace 1, panels bolt here
      │  ║    2 × 64×64 panels, rear     ║│
      │  ║                               ║│
      │══╬═══════════════════════════════╬│  ← brace 2
      │  ║                               ║│
      │  ╚═══════════════════════════════╝│
      └───────────────────────────────────┘
```

Slot the braces so bolt positions can slide — panel post locations vary between
production runs, and a slot costs nothing on a laser. Load goes brace → finger
joint → side wall → box, not into the front face.

---

## 6. Depth

Mains-first (no battery bay), from [`mechanical-plan.md`](mechanical-plan.md) §2.2:

| Layer | Depth |
|---|---|
| Front face, doubled | 6 mm |
| Panel bodies | ~13–16 mm ⚠ measure #3 |
| Electronics bay — Matrix Portal on the HUB75 header, encoders, wiring | 15–20 mm |
| Back cover | 3 mm |
| **Internal** | **~40 mm** |
| **External** | **~46 mm** |

That's a comfortable, shallow desktop object — the battery was most of the depth,
and it left with the lidar.

---

## 7. Onshape workflow

> Full version, including where the vendor CAD is and how to set up the
> document: [`onshape-workflow.md`](onshape-workflow.md). Summary:

1. **Model the box as a solid** at external dimensions (~300 × 190 × 46 mm).
2. **Box Panelise** — decomposes it into overlapping flat panels. Set thickness
   to your **measured** stock, not 3.00 nominal.
3. **Laser Joint (AUTO)** on all panels — generates the finger joints. Set the
   allowance to your machine's kerf compensation.
4. **Sketch the apertures and bores** on the relevant faces: display aperture,
   4 × Ø7 encoder bores at 45 mm pitch, barrel jack, vent slots, wall-mount
   keyholes.
5. **Doublers as separate parts**, inset ≥3 mm from any jointed edge.
6. **Export DXF per face.**

Community FeatureScripts cover steps 2–3 — the Laser Joint feature is the
well-travelled one, and there's a Board Corner Joint alternative if you want
lapped or hidden variants. Worth a look before hand-drawing tabs.

### Two numbers to get right

- **Actual sheet thickness.** "3 mm" basswood runs 2.7–3.2 mm and varies between
  sheets, sometimes within one. Measure the sheet you'll cut and put that number
  in the FeatureScript. Fingers cut for 3.0 into 2.7 stock are loose everywhere.
- **Kerf.** Typically 0.15–0.25 mm on basswood, but it's yours to measure. Cut a
  test comb — a strip of fingers at ±0.05 mm — before committing a full sheet.
  You've done this before; do it again for this stock.

---

## 7b. The back cover, and where a mortise may not go

The finger joints get glued. The back does not — it has to open indefinitely —
so it is through-bolted into captive nuts. One laser-cut sheet cannot make a
counterbore, so the nut pocket is three laminations:

```
  z:  -60      -57      -54      -51      -48
      ├────────┼────────┼────────┼────────┤
      │ back   │ rail A │ rail B │ rail C │
      │ cover  │ Ø clr  │  hex   │ Ø clr  │──┐ through-tenon
      └────────┴────────┴────────┴────────┘  │ into both side walls
       screw ───────────►  ↑                 │
                 nut pulls back against A    └─ 9 mm of wall behind it
```

Rail A takes the nut's load; B holds the nut laterally; C stops it escaping
into the box when the screw is out — its hole is smaller than the nut's
across-flats, so the nut cannot pass but any screw length can.

### Two mortise rules, both learned by drawing one that could not be cut

**A mortise may not sit within one thickness of an edge.** Tenoning rail A — the
obvious choice, since it is the one the nut bears on — puts the slot 3 mm from
the wall's rear edge, leaving a 3 mm sliver of basswood along an 18 mm slot.

**And it may not sit on the roots of a finger notch.** This is the one that
actually bites. The rails were flush against the top and bottom walls, so the
mortise's near edge landed exactly at y = −157 — which is also where the
notches for the top/bottom wall fingers bottom out:

```
   side wall, y-z plane                        z=-60 rear edge
      ...  ┌──────────────────────────┐          │
   y=-139  │   rail A mortise 18x3    │ ◄─ 3mm ──┤   sliver
   y=-157  └──────────────────────────┘          │
   y=-160  ╥─╨─╥─╨─╥  finger notches, 3mm deep, roots AT y=-157
```

Any notch landing under the slot opens straight into it. Not thin — **absent**.

**The fix is one variable per axis.** `#railInset` = 10 mm holds the rails off
the top and bottom walls; the tenon moved from rail A to **rail C**, 3t from the
rear edge. Margins are now 9.9 mm to the notch roots and 9.0 mm to the rear
edge. The same 3 mm sliver existed on the stiffener mortise and got the same
treatment.

### What moving the tenon costs

The nut's load now reaches the wall through the lamination stack's two glue
lines rather than bearing directly on a tenoned rail. That sounds like a
downgrade and isn't, because the tenon was never the strong part:

| Path | Area | Basswood | Fails at |
|---|---|---|---|
| Tenon in shear | 3 × 18 × 2 sides = 108 mm² | ~6 MPa | **650 N** |
| Glue line in tension | 18 × 290 = 5 220 mm² | ~2 MPa | ~10 kN |

The tenon is 15× weaker either way, so which lamination carries it changes
nothing that matters. Face-glued laminations loaded normal to the glue line are
how plywood works.

---

## 8. Basswood specifics

- **Char.** Basswood chars readily and it transfers to hands and to light-coloured
  knobs. Mask the show face, or plan to sand and finish.
- **Soft = screws strip.** Anywhere something threads into wood, use through-bolts
  with washers, captive nuts, or threaded inserts. Not wood screws into 3 mm.
- **Ventilation is free.** The PSU and panels both make heat; cut slots in the
  back cover and low on the side walls. Pattern them — it's a laser, the vents
  can be the decoration.
- **Glue.** Ordinary PVA on the doublers, clamped flat. Watch for cupping on a
  300 mm face — clamp between something rigid while it dries.
- **Finish before assembly.** Much easier flat.

---

## 9. Order of operations

1. **Measure** — stock thickness, kerf, and items #1–#4 from
   [`build-prep.md`](build-prep.md) §B.
2. **Cut a test comb + one encoder bore** in scrap. Confirm the joint fit and
   that a nut clamps 6 mm of doubled basswood without crushing it.
3. **Cut the front face first**, doubled, and dry-fit the panels and encoders
   against it before cutting anything else. It carries every critical dimension.
4. Cut the rest, dry-assemble unglued, check the panel and board fit.
5. Finish flat, then glue.

Step 3 is the cheap insurance: one sheet tells you whether the aperture, the
bore pitch and the 6 mm stack are all right, and it's the only part that has to
be exact.

---

## 10. Open questions

- **Does the LD2450 stay?** It sees through basswood happily — no aperture — so
  it's nearly free to include. Its footprint just needs reserving now if you
  want the option later.
- **Wall-mount or desk stand?** Upstream's case has keyhole hangers. A laser-cut
  angled stand is easy and suits a desktop object; keyholes need doubled pads.
- **Grain direction as decoration.** If the doublers are cross-grained anyway,
  the exposed edges will show it. Worth deciding whether that's a feature.

---

## 11. Panel mounting: there is no standard

Researched because the braces need to hit the panels' rear threaded posts, and
those positions decide whether the braces work at all.

**Waveshare publishes no mechanical drawing.** Neither the wiki nor the docs
platform gives hole positions, count, thread size or even panel thickness. The
Adafruit forum thread on exactly this question concludes that panel makers don't
publish mounting drawings and that positions **vary batch to batch**, because
these are secondary-market industrial modules.

Upstream Patternflow hit the same wall independently. Its BOM tells you to buy
one specific listing because *"its mounting-screw positions are known to match
the case"*, and `hardware/case/bed_256mm/for_other_panels/` exists solely because
*"panel suppliers drill them in different places"* — with the warning that
*"adjustable ≠ universal"*.

So there is nothing reliable to clone. But there is one real data point.

### Measured: Adafruit 5036 (P2.5 64×32)

Extracted from the Ø3.0 mm circles in its published STEP
(`hardware/cad/vendor/` sources, Adafruit_CAD_Parts):

| | |
|---|---|
| Panel | 160 × 80 × **17.5** mm |
| Posts | **4 × M3**, one per corner |
| x inset | 12.45 / 12.50 mm (spacing 135.05) |
| y inset | 15.75 / 15.75 mm (spacing 48.50) |
| Thread depth | ~11.5 mm |

**The convention that generalises:** four M3 holes, one near each corner, inset
**12–16 mm** from each edge. Nothing else does — the insets aren't equal between
axes, so there's no single rule to apply.

Extrapolated to a 128 × 128 P2 64×64, that puts the posts about `64 − 14 = 50 mm`
from the panel's own centre, which is what `postXOffset` and `braceYOffset` are
now set to. Both were previously guesses (54 and 59) with nothing behind them.

**Still measure them.** The obround slots absorb error in x; **y has no such
forgiveness**, and if the posts aren't at ±`braceYOffset` the braces miss
entirely. One variable fixes it, but only once you know the number.

Also note the 17.5 mm thickness against our 15 mm `panelDepth` placeholder — see
§12, because that number now does more work than it used to.

---

## 12. Flush LEDs, and what it costs

The display surface now finishes **coplanar with the bezel's outer face**: both
sit on `z = 0`. Previously the bezel stood 6 mm proud and the LEDs sat in a
shadowbox recess.

How it works: the bezel hangs back from the front plane (`z = -6 … 0`) and the
aperture is cut **larger** than the panel, so the panel passes through it and
its own front face forms part of the front surface. `#apertureGap` is signed:

| `#apertureGap` | Result |
|---|---|
| **+0.5 mm** *(current)* | aperture clears the panel → **flush**, hairline gap all round |
| −0.25 mm | aperture laps over the panel edge → LEDs recess by the bezel thickness |

> ⚠️ **Flush means there is no front stop, and that is unavoidable.** A stop has
> to sit in front of the thing it stops, so any lip that locates the panel in z
> necessarily also covers it and pushes the LEDs back. Nothing can hold the
> panel forward except what is behind it.
>
> So **`#panelDepth` alone decides how flush the result is.** The braces sit at
> `-panelDepth`, and any error there shows directly as the panel sitting proud
> or shy. Measure it properly, expect to shim the braces on first assembly, and
> if that tolerance turns out to be unwinnable, `#apertureGap` negative is the
> forgiving fallback: a lip locates the panel positively at the cost of a small
> recess.

External depth drops to **40 mm** as a side effect, since the bezel no longer
adds to the stack.
