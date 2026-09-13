# Modelling & Rendering in Onshape

How to get the hardware into Onshape and design the enclosure around it.
Companion to [`enclosure-lasercut.md`](enclosure-lasercut.md), which has the
design itself.

---

## 1. What you need to model, and what you don't

For a laser-cut enclosure you need **envelopes and mounting features**, not
detail. A photorealistic Matrix Portal doesn't make the box fit better; knowing
that its HUB75 socket sits X mm off the panel face does.

| Part | Source | Fidelity needed |
|---|---|---|
| **Matrix Portal S3** | ✅ vendor STEP, in repo | as-supplied |
| **4991 encoder breakout** | ✅ vendor STEP, in repo | as-supplied |
| **Waveshare P2 64×64 GOB** | ✋ model it | box + rear post positions |
| **EC11 encoder (PID 377)** | ✋ model it | bushing Ø/thread, shaft, body |
| **Knobs (5528 / 2056)** | ✋ model it | Ø and height only |
| STEMMA QT cables | ✋ skip | route by eye, leave slack |

Two-thirds of this is proxies you draw in ten minutes. That's the right call —
proxies are lighter, they rebuild faster, and you control the dimensions that
matter.

## 2. Vendor models, already downloaded

```
hardware/cad/vendor/
  adafruit-5778-matrix-portal-s3.step      3.9 MB
  adafruit-4991-qt-rotary-encoder.step     1.8 MB
```

From [adafruit/Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts)
(MIT). That repo has 472 parts indexed by product ID — worth remembering for
future projects.

**Not in the repo:** PID 377 encoder, both knobs, the STEMMA cables. Model those
yourself per §4. Note the 4991 STEP may already include an encoder body on it —
check before drawing your own.

To import: **Insert → Import** in a Part Studio, or drag the `.step` into the
document. Onshape reads STEP natively; each import lands as its own tab.

---

## 3. Document structure

Set this up before drawing anything — it's what makes the design changeable
later.

```
📄 Patternflow Desktop
├── 🔢 Variables            ← thickness, kerf, knob pitch, aperture
├── 🧩 Hardware (imported)  ← the two vendor STEPs
├── 🧩 Proxies              ← panel, encoder, knobs
├── 🧩 Enclosure            ← the box; where Box Panelise + Laser Joint run
├── 🧩 Doublers             ← laminations, separate parts
└── 🅰️ Assembly             ← everything mated; in-context source
```

### Variable Studio first

This is the highest-leverage thing in the whole document. Create a **Variable
Studio** and put the numbers that repeat in it:

| Variable | Start value | Notes |
|---|---|---|
| `#thickness` | **measured** | NOT 3 mm — see below |
| `#kerf` | measured | from a test cut |
| `#knobPitch` | 45 mm | clears the 4991 outline |
| `#apertureW` | measured | butted two-panel width, −0.5 mm |
| `#apertureH` | 128 mm − 0.5 | |
| `#bayDepth` | 18 mm | electronics behind the panels |

Then every sketch references `#thickness` rather than a typed 3. When your
actual stock measures 2.83, you change one number and the whole box follows —
finger joints, doubler offsets, bore depths, all of it.

> **Measure the sheet you will actually cut.** This is the single most common
> way a laser-cut box comes out loose everywhere. It was the sharper risk on
> basswood, which runs 2.7–3.2 mm and varies within one sheet; 3 mm Baltic birch
> holds 3.0 much better, which is part of why the stock changed
> ([`enclosure-lasercut.md`](enclosure-lasercut.md) §13).

---

## 4. The proxies

**LED panel** — the important one. It has a `Detailed` switch:

| Off | On |
|---|---|
| a plain 128 × 128 × 14.5 envelope | the stack the panel really is |
| what every clearance check in these docs was written against | for renders, and for seeing what the bay is actually full of |

![Panel proxy, rear](img/proxy-panel-rear.png)

Detail on gives: the GOB resin module, the **lit area as its own body** so a
render can make it emissive, the PCB, the rear frame ring, driver ICs, the two
shrouded HUB75 headers, the power terminals, and four M3 mounting posts.

> ⚠️ **Everything behind the PCB is representative, not measured.** The rear of
> these panels is the one part of this build with no published drawing and no
> consistency between batches — [`enclosure-lasercut.md`](enclosure-lasercut.md)
> §11. The **post positions are the exception**: they are driven from
> `#postXOffset` / `#braceYOffset`, so the proxy agrees with the braces that are
> supposed to bolt to it. Agreeing with the model is not agreeing with the part.

The pair butted gives your aperture; both instances are modelled so the assembly
shows the real seam.

**PSU (Mean Well LRS-50-5)** — same switch, same reasoning:

![PSU proxy](img/proxy-psu.png)

Vents are cut as 0.8 mm recesses rather than through-slots on purpose: a hollow
proxy makes every bounding-box check noisier for no gain. The one feature here
that is **not** cosmetic is the terminal block — its screws face +x, which is
why `#psuX` is pushed left. The screwdriver needs a straight run at them, and
that run is 90 mm of empty bay.

**EC11 encoder** — revolve a profile:

```
        ┌─┐  shaft Ø6, flatted
        │ │  length above bushing ~15 mm  ⚠ measure
     ┌──┴─┴──┐
     │       │  bushing Ø7, thread ~7 mm  ⚠ measure — caps panel thickness
   ┌─┴───────┴─┐
   │  body     │  ~12 × 12 × 7 mm
   └───────────┘
```

The **bushing thread length** is measurement #1 in
[`build-prep.md`](build-prep.md) §B, and it decides whether a 6 mm doubled front
is viable. Model it from calipers, not the datasheet.

**Knobs** — a revolve each, Ø20 and Ø25.4. You only need them to check finger
clearance at `#knobPitch` and to see the front in the render.

---

## 5. Designing the box

Once the hardware is in an assembly, use **in-context design** so the enclosure
references real part positions rather than numbers you retyped:

1. In the **Assembly**, mate the panels, board and encoders into position.
2. Create an in-context Part Studio for the enclosure.
3. Model the box as a **solid** at external dimensions, referencing the assembly
   geometry for the aperture and bore positions.
4. **Box Panelise** → decomposes to overlapping flat panels. Feed it
   `#thickness`.
5. **Laser Joint (AUTO)** → generates the fingers. Allowance = your kerf
   compensation.
6. **Doublers** as separate parts, inset ≥ `#thickness` from any jointed edge
   (§1 of the enclosure doc explains why).
7. **Export DXF** per face.

Both FeatureScripts are community features — search the FeatureScript list for
"Laser Joint" and "Box Panelise". There's also a Board Corner Joint feature if
you want lapped or hidden joints.

### Check these in the assembly before cutting

- Encoder shaft protrudes far enough past 6 mm of wood **plus** the nut to seat
  a knob.
- 4991 breakout bodies don't collide at `#knobPitch` — they're wider than the
  encoders.
- Matrix Portal clears the back cover once it's on the panel's HUB75 header.
- Panel rear posts line up with the cross-brace slots.
- Barrel jack, vents and wall-mount features don't land on a finger joint.

---

## 6. Rendering

**Render Studio** is built into Onshape (NVIDIA Iray, runs in the browser, no
local GPU) and is **included with Professional and Enterprise plans**. If you're
on a free/Standard plan it won't be there — export STEP or glTF to Blender
instead, which is free and you'll get better control of the emissive display
anyway.

Whichever you use, the one thing worth effort:

> **Make the LED panel emissive, not lit.** The whole object reads as a light
> source. A grey rectangle with a texture map looks dead; an emissive surface at
> a plausible brightness, throwing colour onto the basswood around the aperture,
> is what sells it.

Render a pattern screenshot as the emissive texture — the Live Editor at
[patternflow.work/pattern](https://patternflow.work/pattern) will give you a
128 × 64 frame, and Pattern Lab's Capture panel exports PNG at print size.

Materials worth setting: basswood (light, warm, low gloss), anodized aluminium
or black for the knobs, matte black for the panel face between pixels.

---

## 7. Suggested order

```
  1. Variable Studio            ← before anything else
  2. Import the two STEPs
  3. Panel proxy                ← measure first; everything references it
  4. Encoder + knob proxies
  5. Assembly, mate it all
  6. Enclosure in-context
  7. Box Panelise + Laser Joint
  8. Check the list in §5
  9. DXF export → test comb → front face → rest
```

Steps 1–5 are worth doing **before** the caliper session in
[`build-prep.md`](build-prep.md) §B, because the model tells you exactly which
dimensions you need to measure, and you can drop them straight into the Variable
Studio while the parts are still in your hand.

---

## 8. The live document

**Free-tier documents are public.**

| | |
|---|---|
| Document | [`8cfb8d4f799392c05f62f6ad`](https://cad.onshape.com/documents/8cfb8d4f799392c05f62f6ad/w/b5dfed0b24d2121a79e8b1a8) |
| Workspace | `b5dfed0b24d2121a79e8b1a8` |
| Variables | `ecb5fd1eaa5c82ce2840db45` — 17 variables |
| Patternflow FS | `3c1a0a201f41714feba73536` — from [`../../hardware/cad/featurescript/enclosure.fs`](../../hardware/cad/featurescript/enclosure.fs) |
| Part Studio 1 | `06ba580a80083894ed24609b` — panel proxy + bezel |
| Concept B FS | `08032ce8ab6f26772845e4dd` — from [`../../hardware/cad/featurescript/concept-b-corner-post.fs`](../../hardware/cad/featurescript/concept-b-corner-post.fs) |
| Concept B PS | `22bf9277c43f3b54c05038c8` — glueless corner post study, [`fastener-concepts.md`](fastener-concepts.md) §3B |
| Proxies PS | `d1c871ec149418978f2eb283` — panel and PSU proxies alone, for looking at. No enclosure, so nothing hides them |
| LRS-50 (vendor) | `e474d54d0ff1822f6f0a417d` — Mean Well's own STEP, imported. The reference the PSU proxy is checked against |
| Waveshare P2.5 (vendor) | `a70c6a06b8d205902705ee0c` — ⚠ 160 × 160, **not** the P2 this build uses. Layout evidence only |

**The repo is the source of truth**, not the document. `enclosure.fs` is authored
here and uploaded; the document is only where it gets instantiated.

### Verified state — 2026-09-12

**Body count is now 61, not 24** — the panel and PSU proxies went from plain
envelopes to detailed ones (§4). The enclosure itself is unchanged.

> ⚠️ **Turn `Detailed` OFF before running the fragment check.** It counts bodies
> under 500 mm³, and a detailed panel legitimately has twelve driver ICs at
> 130 mm³ and four mounting posts at ~340 mm³. With detail on, the check reports
> sixteen "fragments" per panel that are all supposed to be there. With it off
> the proxies collapse back to one box each and the count means what it used to.

```
bodies=24   fragments=0   bbox 359.5 x 279 x 60 mm    ← Detailed OFF, at P2.5
  (247.5 in y = 244 box + 3.5 mm IEC flange proud of the bottom wall)

  panels     2 x 128 x 128 x 14.5    x -127.5..127.5  y -63.5..63.5  z -14.5..0
  PSU        99.24 x 82 x 30         x  -44.6..54.6   y -152..-70    z -38..-8
  Matrix P.  77.47 x 53.5 x 19.1     x   21.2..98.8   y  23.3..76.8  z -37.6..-18.5
  IEC body   46.75 x 37.45 x 27.25   x   76.6..123.4  y -160..-122.5 z -43.6..-16.4
  IEC flange 59.25 x 3.5 x 48.75     x   70.4..129.6  y -163.5..-160 z -54.4..-5.6
```

Two checks worth re-running after any change, both as one FeatureScript eval:

- **Fragment count** — bodies under 500 mm³. Catches orphaned finger stubs,
  which is how the front-edge joint phase bug showed up (four 3×3×3 fragments).
- **Bounding-box overlap against one body.** `evCollision` is useless as a gate
  here — it reports ~53 pairs on a clean model because every finger joint
  carries deliberate kerf interference. Overlapping *bounding boxes* against a
  single body of interest is the check that actually reads: the IEC inlet should
  overlap exactly one body, the wall it passes through, by exactly its cutout.

## 9. Gotchas found the hard way

**FeatureScript version.** `FeatureScript 2600;` fails to compile **silently** —
`featurespecs` returns an empty list with `libraryVersion: 0` and no error text.
The current library is **3070**, which any eval response reports back. Check this
first when a Feature Studio appears to do nothing.

**Custom-feature namespace** is `e<elementId>::m<microversionId>`, and the
`featurespecs` response hands it to you — don't construct it. It pins a
**microversion**, so editing the Feature Studio leaves existing instances on the
old one. Re-adding the feature (or updating its namespace) is required after every
source change.

**Variable references resolve against the committed table, not your payload.**
So a table with derived variables cannot be created in one POST — it takes one
POST per dependency level: base literals, then first-order derived, then anything
referencing those. `#` is mandatory; bare names are rejected.

**POST to `/variables` REPLACES the whole table.** Anything absent is deleted.

**Part Studios see Variable Studio variables automatically** — no explicit
reference needed, despite the `variablestudioreferences` endpoint existing.

