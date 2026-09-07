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

Tiling LED panels have **no bezel margin**: P2 at 64 px is 128 mm of pixels in a
128 mm module, edge to edge, because they're designed to butt seamlessly. So
there is no border to grab, and **the panels cannot be retained from the front**
the way a picture frame holds glass.

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
