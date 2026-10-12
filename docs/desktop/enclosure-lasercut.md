# Enclosure — Laser-Cut Finger-Joint Box

Supersedes the fabrication section of [`mechanical-plan.md`](mechanical-plan.md) §3.
Geometry, stackup and clearances there still hold; this is the how.

**Material:** 3 mm Baltic birch ply, finger-jointed, doubled selectively.
*(Switched from basswood 2026-09-12 — the reasoning is in §13.)*
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

> ✅ **Superseded by the material change — see §13.3.** Plywood is already
> cross-plied, so there is no grain direction to cross and no orientation to
> get right. Kept because it is the reasoning that made the switch worth
> making: this workaround existing at all was evidence the stock was wrong.

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
>
> ✅ **And refined 2026-10-03 by the P2 itself:** its front face is 128.0 on a
> 128 pitch — **no gap at all**. The edge pixel sits a full half-pitch in
> instead. What generalises is *border + gap + border = one pitch*; the P3 splits
> it 0.5 + 2 + 0.5 and the P2 splits it 1 + 0 + 1. The variables already
> handled it — `#panelGap` is derived and is simply zero now.

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

**The P2-B's registration pins do the locating.** Each panel has two Ø2.83–2.87 pins
standing 3.3 mm proud of its back, near the top edge at (±55.75, +29). The
upper brace is widened to 40 mm so it reaches them, and carries a hole for each:

| Hole | Width (y) | Travel (x) | Job |
|---|---|---|---|
| Pin | **3.0** — 0.13–0.17 over the pin | 1.5 mm | **locates**: rows line up across the seam |
| Screw, ×4 per panel | 5.2 | 10 mm | **clamps** only |

y is the axis the seam shows — a row that jogs by a fraction of a pixel is
visible from across the room — and x is set by butting the panels together, so
the pins are exact in y and free in x. The screw slots stay oversize in both
axes on purpose: a screw that also located would fight the pins. Brace edge to
pin hole is 3.5 mm of birch.

---

## 6. Depth

Mains-first (no battery bay), from [`mechanical-plan.md`](mechanical-plan.md) §2.2:

| Layer | Depth |
|---|---|
| Front face, doubled | 6 mm |
| Panel bodies | 14.5 mm ✅ measured |
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

- **Actual sheet thickness.** This is the main practical reason §13 switched
  stock: "3 mm" basswood runs 2.7–3.2 mm and varies within one sheet, where 3 mm
  Baltic birch holds 3.0 fairly honestly. **Measure it anyway** and put that
  number in the FeatureScript — fingers cut for 3.0 into 2.7 stock are loose
  everywhere.
- **Kerf.** Was 0.15–0.25 mm on basswood; birch is denser and its glue lines cut
  differently, so **the old figure does not carry over**. Cut a test comb — a
  strip of fingers at ±0.05 mm — before committing a full sheet.

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

| Path | Area | Basswood | Baltic birch | Fails at |
|---|---|---|---|---|
| Tenon in shear | 3 × 18 × 2 sides = 108 mm² | ~6 MPa | ~12 MPa | 650 N → **1 300 N** |
| Glue line in tension | 18 × 290 = 5 220 mm² | ~2 MPa | ~2 MPa | ~10 kN |

The tenon is 15× weaker either way — 8× on birch — so which lamination carries
it changes nothing that matters. (The glue-line row assumes the rails stay
glued; [`fastener-concepts.md`](fastener-concepts.md) §3C bolts them instead,
and the back-cover screws already clamp that stack for free.) Face-glued laminations loaded normal to the glue line are
how plywood works.

---

## 8. Material specifics

- **Char.** Both basswood and birch char, and it transfers to hands and to
  light-coloured knobs. Birch glue lines char darker than the wood either side,
  which shows on every exposed edge. Mask the show face, or plan to sand and
  finish.
- **Soft = screws strip.** Still true on birch, just 2.3× less so (§13.2).
  Anywhere something threads into wood, use through-bolts with washers, captive
  nuts, or threaded inserts. Not wood screws into 3 mm.
- **Voids.** A plywood problem basswood did not have: a void under the cut line
  is an uncut spot and a weak finger. Buy on the edge, not the label — §13.5.
- **Ventilation is free.** The PSU and panels both make heat; cut slots in the
  back cover and low on the side walls. Pattern them — it's a laser, the vents
  can be the decoration.
- **Glue.** Ordinary PVA on the doublers, clamped flat. Cross-graining no
  longer matters (§13.3), so orientation is free. Watch for cupping on a
  300 mm face — clamp between something rigid while it dries. *(Whether there is
  any glue at all is an open question — see
  [`fastener-concepts.md`](fastener-concepts.md), which asks whether the box can
  be held together with M3 hardware alone.)*
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

### Measured: Waveshare P2 64×64-B — the panel actually in the box

Calipers, 2026-10-03. Back face 127 × 127 (front 128), positions from its
centre:

| | |
|---|---|
| Body | **128 × 128 × 14.5 mm** front face; 127 × 127 at the back |
| Inserts | **6 × M3**: (±57, ±44) down the sides, (0, ±57) mid top and bottom |
| Inset | **6.5 mm** for every insert |
| Registration pins | **2 × Ø2.83–2.87** (nominal Ø3 hole), 3.3 proud, at (±55.75, +29) |

So the fourth data point is a sixth pattern: not one-per-corner at all. The
braces use the four side inserts, which share a y (`#braceYOffset` = 44) and so
suit a horizontal brace; the mid-edge pair is modelled and left free. The
§11 caution below still stands for any *other* batch — but this one is
measured, and the 50 mm extrapolation in the table is retired.

#### Flatbed cross-check, 2026-10-11

The back face was scanned at 600 dpi on the Epson
([`p2-rear-scan-600dpi.jpg`](img/p2-rear-scan-600dpi.jpg), back view, pins up).
White paper was draped over the panel so the rim reads dark on light. A second
hand-measured sheet was scanned the same day ([`p2-dims-sheet.png`](img/p2-dims-sheet.png)).

**The datum is the rear outer edge**, because the panel has no feature at its
centre. The scan rests on its pins and tilts, so only two edges sit on the glass:
- **Top and left:** in focus. Line fits to them are good to about 20 µm.
- **Bottom and right:** lifted and blurred, so they are not used.

Distances to the right and bottom edges therefore assume the back is 127. Hole
centres come from the brass rings and from circle fits to the pin tips.

| From the rear edge | Calipers 10-03 | Sheet 10-11 | Scan |
|---|---|---|---|
| Side inserts, down from top | 19.5 | 20 | **19.47** (19.45 / 19.49) |
| Side inserts, up from bottom | 19.5 | not dimensioned | 19.8 (127 − 107.18) |
| Mid inserts, in from top / bottom | 6.5 | 6.5 | **6.70** / 7.07 (127 − 119.93) |
| Side inserts, in from left | 6.5 | 6.5 | **6.52** (6.69 top, 6.34 bottom) |
| Side inserts, in from right | 6.5 | 7 | 6.67 (127 − 120.33) |
| Pins, down from top | 34.5 | 34 | **34.58** (34.54 / 34.62) |
| Pins, in from left / right | 7.75 | in line with the side inserts | **7.70** / 7.45 (127 − 119.55) |
| Insert pattern centreline, from left | 63.5 | 63.5 | **63.43** |

Bold is measured from an edge that was on the glass. Those figures agree with
10-03 to 0.2 mm, so the model stays as it is. Where the sheet differs (the 7,
the 20 and the 34), the scan sides with 10-03.

Two things limit the scan:
- **Squareness:** the insert column runs 0.35 mm out of parallel with the left
  edge over its length. That is either the moulding or the scanner's axes, and
  a scan cannot tell which.
- **Scale:** it is not calibrated. Mid-to-mid inserts read 113.2 against 114
  by calipers, which may mean the scan's top-to-bottom axis is ~0.7 % short.
  A steel rule laid on the glass in the next scan would settle it.

**Pins: Ø2.83–2.87 by calipers on the shank** (re-measured 10-11), so they are
made for a nominal Ø3 hole, which is what the brace has. The flatbed sees only
the tip face that touches the glass (Ø2.2–2.7 across the two scans), so the tips
are chamfered.

### Measured: Waveshare P2.5 64×64 — a real Waveshare rear at last

A vendor CAD model is now in [`hardware/cad/vendor/`](../../hardware/cad/vendor/)
— 121 bodies, measured rather than guessed:

| | |
|---|---|
| Body | **160 × 160 × 16.5 mm** |
| Posts | **4 × M3 at (±63.5, ±63.5)** from the panel centre |
| Inset | **16.5 mm**, and **equal in both axes** |

That makes three measured panels, and the spread got *worse*, not better:

| Panel | Size | Inset | From centre |
|---|---|---|---|
| Adafruit 5036 (P2.5 64×32) | 160 × 80 | 15.75 / 12.5 mm | 24.25 mm |
| Waveshare P3 64×64 | 190 × 190 | **8 mm** | 87 mm |
| Waveshare P2.5 64×64 | 160 × 160 | **16.5 mm** | 63.5 mm |
| **Waveshare P2 64×64-B** *(measured)* | 128 × 128 | **6.5 mm** | 57 / 44 mm, 6 inserts |

Two Waveshare 64×64 panels, 8 mm and 16.5 mm. **There is no convention.** The one
thing this model does add is that on a *square* panel the insets are equal in
both axes — which is more than could be assumed before, and it is the axis
(`braceYOffset`, in y) that has no forgiveness.

> ✅ **Superseded 2026-10-03 — the design is now built at the measured P2.**
> It was built at P2.5 in the meantime — see
> [`mechanical-plan.md`](mechanical-plan.md) §2.1 for the decision and the list
> of variables to flip when the panels arrive. The note below is kept because it
> is the arithmetic that makes the two interchangeable on paper and very much
> not interchangeable in wood.

> ⚠️ **This model is a P2.5; the P2 (SKU 33838) is the other candidate.** Both are
> *64 × 64 pixels* — that is the number on the box, and it is not a size. The
> size is pitch × pixels: **2 mm × 64 = 128 mm** for ours, **2.5 mm × 64 =
> 160 mm** for the model. So it is 160 × 160 × 16.5 against our 128 × 128 × 14.5.
> Pointing `#panelBody` at it would not be a proxy swap, it would be a 64 mm
> wider box — aperture 256 → 320, `#boxW` → 360, and upstream's pixel geometry
> broken for nothing, since the pixel count is identical either way.

**What the model is and is not good for.** Checked body by body, it is a
**160 × 160 × 1.6 PCB plus a handful of connectors** — 121 bodies, but the LEDs
are not modelled at all. So:

| | Trust it? | |
|---|---|---|
| Mounting holes at (±63.5, ±63.5) | **yes** | deliberate features, and `#postXOffset` / `#braceYOffset` now use them |
| PCB outline 160 × 160 | **no** | exactly the pitch, which would mean a zero seam gap — see §4. `#panelBody` uses 158.5 from the border arithmetic instead |
| Overall depth 16.5 | **no** | that is PCB + HUB75 shroud, not the panel module. `#panelDepth` stays a flagged placeholder |
| Rear layout | as shape only | topology, not positions |

That is the useful discipline with a found model: it upgraded one guess to a
measurement and left two others exactly as uncertain as they were.

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
> or shy. Now measured at **14.5** (17.8 over the pins, which pass through the
> brace and so do not count). Still expect to shim the braces on first assembly, and
> if that tolerance turns out to be unwinnable, `#apertureGap` negative is the
> forgiving fallback: a lip locates the panel positively at the cost of a small
> recess.

External depth drops to **40 mm** as a side effect, since the bezel no longer
adds to the stack.

---

## 13. Material — and why the 30 W laser is not the constraint

Basswood was picked in [`mechanical-plan.md`](mechanical-plan.md) §3 without much
argument, and three things have happened since that make it worth revisiting:
§1's cross-grain lamination trick exists only to work around basswood's grain,
§7b's mortise rules exist because it splits, and the whole of
[`fastener-concepts.md`](fastener-concepts.md) §1.2 — "you cannot develop preload
against basswood" — is a material property, not a geometry one.

### 13.1 The laser barely narrows the field

**At 3 mm, a 30 W CO₂ cuts every candidate here.** Denser stock needs a slower
feed or a second pass, but nothing in the list below is out of reach:

| Stock | 30 W, 3 mm | Notes |
|---|---|---|
| Basswood | 1 pass, fast | the easy baseline |
| Poplar / "craft" ply | 1 pass | voids are the problem, not power |
| **Baltic birch ply** | **1 pass, slower — or 2** | glue lines cut slower than the wood |
| Cherry, walnut | 1–2 passes | best-looking char |
| Hard maple | 2 passes | slow, and it chars dark |
| Bamboo ply | 2–3 passes, heavy char | **marginal — skip it** |
| **Any 6 mm** | **3+ passes, taper, heavy char** | **this is where 30 W actually runs out** |

So the constraint bites at **thickness, not species.** The design never asks the
laser for 6 mm — the 6 mm at the knob bores is two 3 mm laminations (§3) — so the
laser is not choosing the material. Properties are.

### 13.2 What the properties actually buy

Handbook values at 12 % MC, run through the two numbers this design is sensitive
to. "Ø12 washer" is the load at which a Ø12 penny washer starts embedding
(§1.2 of the fastener doc); "tusk key" is the shear-out load on the corner post's
key (Concept B).

| Stock | ρ kg/m³ | Ø12 washer | Tusk key | Whole box |
|---|---|---|---|---|
| **Basswood** *(current)* | 400 | **270 N** | **300 N** | 480 g |
| Poplar | 420 | 354 N | 364 N | 500 g |
| Paper birch | 550 | 426 N | 369 N | 660 g |
| **Baltic birch ply** | 680 | **624 N** | **533 N** | 815 g |
| Cherry | 500 | 499 N | 519 N | 600 g |
| Walnut | 550 | 728 N | 417 N | 660 g |
| **Hard maple** | 705 | **1050 N** | **715 N** | 845 g |

Two things to read off that:

- **A hand-snug M3 is 400–600 N.** Basswood embeds well below that; Baltic birch
  is at the top of the range; hard maple is clear of it. Maple is the only entry
  that makes §1.2's conclusion stop being true — on maple you *can* torque a bolt
  and have it stay clamped.
- **The box roughly doubles in weight**, 480 g → ~820 g. On a desktop object that
  is a feature, not a cost: it stops the thing sliding when you turn a knob.

### 13.3 The argument that actually decides it

Not strength — **plywood is already cross-plied, and that deletes the one place
glue was still earning its keep.**

[`fastener-concepts.md`](fastener-concepts.md) §6.5 concluded that the front
face's two laminations should stay glued, because bolted at 60 mm centres they
are not plywood between the bolts, and the narrow bezel rails around the aperture
are exactly where the cross-grain trick was protecting the part. **On plywood
stock that argument evaporates**: every sheet is already balanced and
cross-grained, the doubler needs no grain-crossing, and the front face can be
bolted like everything else.

> **Switching to ply is what makes a fully glueless box reachable.** It is worth
> more than the 2.3× bearing strength.

It also quietly retires three other workarounds:

| Existing workaround | On ply |
|---|---|
| §1 "laminate the doublers cross-grain" | **moot** — sheet is already cross-plied |
| §8 "soft = screws strip" | still true, but 2.3× less so |
| Concept A's humidity risk — 3 % seasonal movement across grain | **~0.2 %** — ply barely moves |

And it fixes the most annoying practical thing in the whole build: **3 mm Baltic
birch is genuinely 3.0 mm**, where "3 mm" basswood runs 2.7–3.2 and varies within
one sheet (§7). Finger joints care about that more than they care about strength.

### 13.4 What it costs

- **The edge.** Ply shows its layer lines, and the most visible edge in the build
  is the one running all the way around a 257 × 129 aperture. Solid hardwood cuts
  a clean edge; ply does not. This is the real trade, and it is a taste question,
  not an engineering one.
- **Glue lines cut slower than the wood**, so kerf is slightly inconsistent
  through the thickness and the char is darker at each line.
- **Voids.** A void under the cut line is an uncut spot and a weak finger.

### 13.5 Recommendation

**3 mm Baltic birch ply, B/BB grade or better**, with hard maple as the
alternative if the aperture edge matters more than going fully glueless.

Sourcing caveat, because this is where it goes wrong: **"Baltic birch" is now
often a grade description rather than an origin.** Check the *edge*, not the
label — real stock shows uniform, void-free birch plies of equal thickness all
the way through. A poplar or mixed-hardwood core is a different material with
different numbers and worse voids. Model-shop "aircraft ply" is the same product
sold honestly, and it is worth the premium for a one-box build.

> ⚠️ **Do not mix stock.** §1's rule is absolute: fingers only mesh if every
> mating panel is the same thickness, so a maple front face on a ply box does not
> work — nominal 3 mm ply is 3.0 and nominal ⅛" hardwood is 3.18. Pick one
> material for everything that carries a finger joint.

**Never laser:** MDF (fastener bearing crumbles, and the bores would wallow worse
than basswood), hardboard, and anything with PVC or vinyl content.

### 13.6 What changes in the model

Nothing structural — which is the point of having driven everything from the
variable table:

| | |
|---|---|
| `#thickness` | **re-measure.** Expect ~3.0, not 2.7–3.2 |
| `#kerf` | **re-cut the comb.** Denser stock and glue lines both move it |
| §1 cross-grain doublers | delete the requirement |
| `fastener-concepts.md` §6.5 | resolved — the front face no longer needs glue |
| Everything else | unchanged |

The test comb in §9 step 2 was already the gate. It just needs cutting in the new
stock instead.
