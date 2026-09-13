# Glueless Assembly — Fastener Concepts

**Status: concepts for review. Nothing here is in the model yet.**

The enclosure as designed in [`enclosure-lasercut.md`](enclosure-lasercut.md) is a
glued finger-jointed box with one demountable part (the back cover, on captive
M3 nuts). This doc asks the other question: **can the whole box be held together
with nothing but laser-cut 3 mm basswood and M3 hardware?**

Constraint set, as stated:

- Laser-cut parts only — no machining, no counterbores, no threaded inserts.
- M3 bolts, washers, lock washers, nuts.
- No glue anywhere, including the laminations.
- Must stay demountable, indefinitely.

Short answer: **yes, and the box is already most of the way there** — but not by
the route that looks obvious, and two pieces of arithmetic below rule out about
half of the standard laser-cut joinery vocabulary in 3 mm stock.

---

## 1. Two numbers that kill the obvious answers

### 1.1 You cannot put an M3 cross-hole through 3 mm stock

The canonical glueless laser-cut joint is the **T-slot** (a.k.a. tab-and-captive-nut):
a tab on panel A passes through a slot in panel B, a cross-hole through the tab
takes the bolt, and a T-shaped pocket in B's face traps the nut.

```
   panel B  ──┬────────────────┬──
              │   ▄▄▄▄▄▄▄▄▄    │      T pocket, nut drops in
      tab ════╪═══[O]══════════╪══    bolt through the TAB
              │                │
```

M3 clearance is **3.2 mm**. The tab is **3.0 mm** thick. The hole is wider than
the material it goes through. There is no version of this that works at this
thickness — the tab has to be ≥ 6 mm, i.e. laminated, and a laminated tab cannot
finger-joint into single-thickness panels ([`enclosure-lasercut.md`](enclosure-lasercut.md) §1).

**Consequence: every bolt axis must be normal to a panel face, never into an
edge, and every nut must live inside a lamination stack rather than an edge
pocket.** That is exactly the back cover's rail A/B/C pattern, and it is the only
nut-retention geometry available in 3 mm.

### 1.2 You cannot develop preload against basswood

Basswood crushes perpendicular to the grain at roughly **2.4 MPa** at the
proportional limit. Bearing area under an M3 washer:

| Washer | OD | Bearing area | Embeds above |
|---|---|---|---|
| DIN 125 (standard M3) | 7 mm | 29 mm² | **~70 N** |
| DIN 9021 (fender M3) | 9 mm | 55 mm² | ~130 N |
| Ø12 penny washer | 12 mm | 104 mm² | ~250 N |
| Ø16 penny washer | 16 mm | 190 mm² | ~460 N |

An M3 bolt nipped up by hand with a short driver reaches **400–600 N** without
feeling tight. A torque wrench at 1 Nm gives ~1.5 kN. **Every one of those
crushes the wood**, and then the wood creeps and the preload decays anyway.

So: a bolted basswood joint has **no usable friction capacity**, and any design
whose stiffness depends on clamp force is designing on sand.

---

## 2. The reframing that makes this work

> **Glue makes a monolith. Bolts make a retained assembly. Don't try to replace
> the glue's clamp force — replace its *job*.**

Break down what the glue in a finger-jointed box actually does:

| Glue's job | Carried by | Needs hardware? |
|---|---|---|
| Resist racking (shear in the joint plane) | The finger interlock itself | **No** |
| Locate the panels | The finger interlock itself | **No** |
| Stop fingers walking out (tension normal to the joint) | *glue only* | **Yes** |
| Hold laminations together in shear | *glue only* | **Yes** |
| Resist torsion of the whole box | Front + back **diaphragms** | **No — already built** |

Only two rows need hardware, and the loads in both are small. The box is ~1.5 kg
of wood plus ~0.9 kg of panels and PSU; nothing inside it pulls a corner apart.
**The bolt is a retainer, not a clamp.** Torque it snug, use a nyloc so it stays
snug, and stop worrying about preload — §1.2 stops being a problem the moment
you stop asking the joint for friction.

### The two diaphragms are the real structure

This is the argument that glueless is viable *here specifically*:

```
    z=0                                              z=-60
     ║                                                 ║
     ║  front face, 2 laminations, 296 x 244           ║  back cover
     ║  minus a 257 x 129 aperture                     ║  289 x 237, 6 bolts
     ║                                                 ║
     ╚══ side / top / bottom walls, dry finger joints ═╝
```

A box with a stiff plate bolted across each end is torsionally stiff regardless
of how its corners are joined — the plates take the torque as in-plane shear, and
in-plane shear is what a 3 mm sheet is best at. The back cover is **already** a
6-bolt diaphragm. The front is already doubled and full-perimeter. So the
torsion case, which is the one a dry box normally loses, is the one case this
design had already solved for other reasons.

Caveat: the front face is not a *full* diaphragm — it has a 257 × 129 hole in it,
leaving 20 mm rails top and sides and a 96 mm control band below. A 20 mm rail in
3 mm basswood is a weak shear path. **This is the thing to test, not to assume.**

---

## 3. The concepts

Four schemes, cheapest-change first. They are not exclusive — C is a supplement
to any of them.

### Concept A — Dry press fit, diaphragms only

**Change to the model: none.** Cut what is already drawn, skip the glue bottle.

The finger joints are drawn for a **zero-clearance press fit** (kerf compensated
both ways, `enclosure.fs` §"Finger joints"). Press-fit basswood fingers hold
genuinely well dry — enough to carry the box around. The front face and back
cover bolt on and provide the torsion path.

| | |
|---|---|
| Hardware | 6 × M3 (back cover, already in the model) + 4 encoder nuts |
| New parts | none |
| Demountable | yes, but the corners will loosen with repeated cycles |
| Risk | **humidity.** A press fit that is perfect in winter is loose in summer, and basswood moves ~3 % across the grain over the seasonal humidity range — that is 0.1 mm on a 3 mm finger, i.e. half the kerf budget |

**Verdict: the honest baseline, not the answer.** Worth cutting first because it
costs nothing and tells you how tight the joints actually are. If it feels solid
dry, every other scheme gets easier.

### Concept B — Internal corner cleats with captive nuts ★ recommended

Add a wooden angle bracket inside each corner, made the only way 3 mm allows:
as a **lamination stack** with the nut trapped between layers, exactly like rails
A/B/C.

```
   plan view, one corner              section through one bolt
   ┌──────────────────────┐
   │▓▓▓▓▓│  side wall     │            side wall  ███ 3 mm
   │▓▓▓▓▓│                │       bolt ──────────►███
   │▓▓▓▓▓│  cleat stack   │                       ▓▓▓  L1  clearance Ø3.2
   ├─────┼────────────────┤                       ▓▓▓  L2  hex pocket 5.5 AF
   │     │ top wall       │                       ▓▓▓  L3  blind — nut can't escape
   └─────┴────────────────┘                       └── cleat, 9 mm of laminations
```

Each cleat is an L (or two separate strips) that bolts to both panels meeting at
that corner: 2 bolts into the side wall, 2 into the top/bottom wall, per corner.
The fingers still locate everything; the cleat supplies only the normal
restraint, which is the one thing §2 says is missing.

| | |
|---|---|
| Hardware | 16 × M3 × 10 button head + nyloc, + 6 back cover |
| New parts | 4 cleats × 3 laminations = 12, all small |
| Nut pocket | proven pattern — identical to rails A/B/C |
| Bolt loading | pure tension, no friction required |
| Demountable | yes, indefinitely — nuts are captive, nothing threads into wood |

**Clearance check against the existing model** (interior `x −145…145`,
`y −157…81`):

| Corner | Nearest obstruction | Room for a cleat |
|---|---|---|
| bottom-left `(−145, −157)` | PSU starts at x = −44.6 | 100 mm — free |
| bottom-right `(145, −157)` | IEC flange ends at x = 129.6 | **15.4 mm** — tight |
| top-left `(−145, 81)` | nothing | free |
| top-right `(145, 81)` | Matrix Portal ends at x = 98.8 | 46 mm — free |

The bottom-right corner is the one to draw first. A 12 mm cleat fits with 3 mm to
spare; anything wider collides with the IEC flange and the cleat has to become an
L that runs up the side wall only.

**Verdict: this is the one to model.** Smallest conceptual leap from what exists,
reuses a pattern already verified in the part studio, and the load path is
wood-in-bearing with the bolt only in tension.

### Concept C — Bolt the laminations (required by every scheme)

Easy to forget: **"no glue" also outlaws the doublers.** The design currently
face-glues laminations in four places, and each needs a mechanical answer:

| Lamination | Layers | Mechanical fix | Free? |
|---|---|---|---|
| Front face | 2 | **4 encoder bushing nuts already clamp it** at the knob cluster, plus 4 × M3 in the bezel margin | mostly |
| Panel cross-braces | 2 | **the panel mounting bolts already clamp it** — they pass through both layers into the panel posts | **yes, free** |
| Rear rails A/B/C | 3 | **the back cover bolts already clamp them** — that is what they are for | **yes, free** |
| Corner cleats (Concept B) | 3 | the cleat's own bolts clamp it | yes |

Three of the four are already paid for by hardware the design needs anyway.
Only the front face needs bolts added, and only in the 20 mm bezel margin.

> ⚠️ **A bolted cross-grain lamination is not plywood.** The cross-grain trick in
> [`enclosure-lasercut.md`](enclosure-lasercut.md) §1 works because glue makes the
> two layers act as one section. Bolted at intervals, the layers can slip between
> bolts, and the narrow rails above and below the aperture — the exact place the
> cross-grain trick was protecting — get the least of the benefit. **Bolt spacing
> on the front face wants to be ~60 mm, not ~150.**

### Concept D — Front-to-back tension rods

Four long M3 bolts running the full depth at the corners, through the back cover
and into captive nuts in the front face's inner lamination, putting the whole
stack of walls into compression.

```
        front (2 layers)          back cover
            ║                          ║
   nut ▓▓───╫──────────────────────────╫───[bolt head + washer]
       ↑    ║   side wall in           ║
   captive  ║   compression, 60 mm     ║
```

Very few parts, very quick to assemble, and the visible hardware is 4 heads on
the back cover. But:

- §1.2 says the compression is worth ~250 N at best before the washer embeds,
  over a 60 mm column of end grain that will creep. **It will go slack.**
- The rods land in the corners, which is where the finger joints are.
- The front nut pocket needs 3 laminations; the front is 2, so `#frontLayers`
  goes to 3 and the EC11 bushing thread length (~7 mm) no longer clears 9 mm of
  wood plus a nut. **This breaks the encoders.**

**Verdict: rejected.** The last bullet is fatal on its own.

### Concept E — Wedged through-tenons, zero hardware

The traditional answer, and it needs no M3 anything: the tenon passes through the
wall and out the far side, a tapered slot in the protruding tenon takes a wooden
wedge, and driving the wedge pulls the joint tight.

**Rejected for this box**, for one reason: the wedge is loaded across a 3 mm
section in a soft, straight-grained wood, and basswood wedges at that scale snap.
It is also a lot of small loose parts on a desktop object. Worth remembering for
the [wall project's](../wall/) frame, where the stock will be thicker.

---

## 4. Hardware recommendations

Assuming Concept B.

| Item | Spec | Why |
|---|---|---|
| Bolts | **M3 × 10 button head**, socket drive | 3 mm wall + 9 mm cleat means the thread lands in the middle lamination's nut; button heads sit flat on soft wood and there is no counterbore to hide a cap head in |
| Washer, under the head | **Ø9 DIN 9021 minimum, Ø12 preferred** | §1.2 — a standard Ø7 M3 washer embeds at 70 N, which is less than finger-tight |
| Washer, under the nut | **none needed** | the nut is captive between laminations and bears on wood over its full 5.5 mm hex, not a point |
| Nut | **M3 nyloc (DIN 985)**, or plain DIN 934 + thread locker | **not a split lock washer** — see below |
| Back cover | unchanged, 6 × M3 into the existing rails | already modelled |

### Why not lock washers

The user's list included them, and they are the wrong part here. A split lock
washer works by storing elastic energy in the split ring — it maintains preload
as the joint relaxes. That assumes the *joint* relaxes by a few microns of
thread settling. A basswood joint relaxes by **tenths of a millimetre** of
crushing and creep, which is far past the washer's travel; it flattens out and
contributes nothing. Worse, its sharp cut ends dig into the basswood and start
the crushing.

**Prevailing-torque locking (nyloc) is independent of preload**, which is exactly
the property you want when §2 says there is no preload to speak of. Serrated
flange nuts also lock without preload, but they bite into the wood and chew it on
removal — fine if nothing ever comes apart, wrong for a box whose whole premise
is demountability.

---

## 5. What to cut to decide this

One test coupon settles it, and it is small:

```
   ┌──────────────┐
   │              │  two 80 x 80 panels, finger-jointed
   │      A       │  one 3-lamination corner cleat
   │              │  4 x M3 x 10 + nyloc + Ø12 washers
   └───┬──────────┘
       │  B
       │
```

Cut it three ways and try to rack each by hand:

1. **Dry fingers only** — Concept A's baseline. How much does it move?
2. **Dry fingers + cleat + 4 bolts** — Concept B. Does the movement stop?
3. **Glued fingers** — the control. How much better is glue, really?

If (2) is close to (3), the whole box goes glueless. If (2) is much closer to
(1), the diaphragm argument in §2 is doing more work than the corners are, and
the front face's 20 mm bezel rails become the thing to reinforce instead.

**Also worth measuring on the coupon:** how much a Ø12 washer embeds at "snug",
and whether the 5.5 mm hex pocket holds an M3 nut against a driver without
spinning. Both are numbers that this doc currently *derives* rather than knows.

---

## 6. Open questions

1. **How much does the front aperture cost the diaphragm?** §2 assumes the front
   face is a shear panel; a 257 × 129 hole in a 296 × 244 plate makes it a frame,
   not a plate. The 96 mm control band below the aperture is solid and probably
   carries most of it, which would make the box stiff at the bottom and floppy at
   the top. Worth a quick FEA or the coupon test.
2. **Does the back cover need more than 6 bolts** once it is the primary torsion
   path rather than a lid? `#screwsPerRail` is 3; going to 4 is a one-variable
   change, and the back cover split (still pending) may force a rethink anyway.
3. **Seasonal movement.** Concept A's risk applies to B as well, just less: the
   cleat bolts hold the corner closed but nothing stops a finger joint gapping
   as the wood shrinks. Slotted holes in the cleat, in the grain direction,
   would let it move. Probably over-thinking a desktop object in a heated room.
4. **Is a hybrid allowed?** Gluing only the laminations (which never need to come
   apart) while bolting all the corners gets most of §1's stiffness back for none
   of the demountability cost. That may be the actual answer, and it is worth
   deciding whether "no glue" is a hard constraint or a design exercise.
