FeatureScript 3070;
import(path : "onshape/std/geometry.fs", version : "3070.0");

/**
 * Patternflow desktop enclosure — parametric features.
 *
 * Laser-cut 3 mm basswood finger-joint box, 2 x Waveshare P2 64x64 GOB panels,
 * Matrix Portal S3, 4 x Adafruit 4991 seesaw encoders.
 *
 * DATUM CONVENTION — every part depends on this:
 *   z = 0          the LED panel FRONT face
 *   z < 0          into the enclosure (panels, electronics, back cover)
 *   z > 0          out of the enclosure (the bezel laminations)
 *   x = 0, y = 0   centre of the display area
 *
 * The bezel sits flush on the panel face: GOB panels are resin-filled and
 * already diffuse, so there is no air gap and no separate diffuser.
 *
 * Drive every parameter from the Variables studio. Placeholders that MUST be
 * measured before cutting: #thickness, #kerf, #panelDepth. The EC11 bushing
 * thread length caps #frontThickness — measure it first.
 *
 * Source of truth for this file is the repo, not the Onshape document:
 *   hardware/cad/featurescript/enclosure.fs
 */

// ────────────────────────────────────────────────────────────────────────
// Panel proxy
// ────────────────────────────────────────────────────────────────────────
// Two levels of fidelity, switched by "Detailed":
//
//   OFF  a plain 128 x 128 x 14.5 envelope. What the enclosure actually
//        needs, and what every clearance check in the doc was written
//        against. Leave it off when checking geometry.
//   ON   the stack a GOB panel really is, so renders and interference
//        checks read honestly:
//
//        z=0     ┬──────────────────────────────┬  emissive area, its own
//        -0.3    ┼──┤ 0.5mm reveal all round ├──┼  body so a render can
//                │      GOB resin module        │  make it a light source
//        -3.0    ┼──────────────────────────────┼
//                │            PCB               │  driver ICs on the back
//        -4.6    ┼──┬────────────────────────┬──┼
//                │  │  cavity: connectors,   │  │  rear frame, a ring
//                │  │  posts, ICs            │  │
//        -14.5   ┴──┴────────────────────────┴──┴
//
// ⚠ EVERYTHING BEHIND THE PCB IS REPRESENTATIVE, NOT MEASURED. The rear of
// these panels is the one part of this build with no published drawing and
// no consistency between batches — see enclosure-lasercut.md §11. The post
// positions are driven from #postXOffset / #braceYOffset so the proxy at
// least agrees with the braces it is supposed to bolt to, but agreeing
// with the model is not the same as agreeing with the part in your hand.
// The header block sizes are typical shrouded HUB75, not measured.

annotation { "Feature Type Name" : "Panel proxy" }
export const panelProxy = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Panel width" }
        isLength(definition.panelW, LENGTH_BOUNDS);

        annotation { "Name" : "Panel height" }
        isLength(definition.panelH, LENGTH_BOUNDS);

        annotation { "Name" : "Panel depth" }
        isLength(definition.panelDepth, LENGTH_BOUNDS);

        annotation { "Name" : "Panel count" }
        isInteger(definition.count, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel body (undersize)" }
        isLength(definition.panelBody, LENGTH_BOUNDS);

        annotation { "Name" : "Detailed" }
        definition.detail is boolean;

        annotation { "Name" : "GOB module thickness" }
        isLength(definition.gobT, LENGTH_BOUNDS);

        annotation { "Name" : "PCB thickness" }
        isLength(definition.pcbT, LENGTH_BOUNDS);

        annotation { "Name" : "Rear frame rail width" }
        isLength(definition.frameW, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 header width" }
        isLength(definition.hdrW, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 header depth" }
        isLength(definition.hdrH, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 header projection" }
        isLength(definition.hdrProj, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 header spacing" }
        isLength(definition.hdrPitch, LENGTH_BOUNDS);

        annotation { "Name" : "Mounting post diameter" }
        isLength(definition.postDia, LENGTH_BOUNDS);

        annotation { "Name" : "Post x from panel centre" }
        isLength(definition.postXOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Post y from panel centre" }
        isLength(definition.postYOffset, LENGTH_BOUNDS);
    }
    {
        // panelW/panelH are the TILING PITCH; panelBody is the physical part,
        // which is smaller. The difference is the inter-panel gap, and that
        // gap is REQUIRED, not slop: each panel carries a half-gap border
        // between its edge pixel centre and its edge, so
        //     border + gap + border = one pixel pitch
        // keeps the pixel grid continuous across the seam. Butting the bodies
        // tight would put a whole gap's worth of error in the grid at every
        // seam. Measured on a Waveshare P3 64x64: body 190, pitch 192, gap 2,
        // and 189mm of pixel span — which is exactly 0.5mm of border per edge.
        const n = definition.count;
        const B = definition.panelBody;
        const D = definition.panelDepth;
        const gap = definition.panelW - B;
        const bodySpan = n * B + (n - 1) * gap;

        const reveal = 0.3 * millimeter;
        const border = gap / 2;                 // the half-gap derived above
        const zPcbF  = 0 * millimeter - definition.gobT;
        const zPcbB  = zPcbF - definition.pcbT;

        for (var i = 0; i < n; i += 1)
        {
            const x0  = -bodySpan / 2 + i * definition.panelW;
            const x1  = x0 + B;
            const xc  = x0 + B / 2;
            const pid = id + ("p" ~ i);

            if (!definition.detail)
            {
                fCuboid(context, pid + "box", {
                        "corner1" : vector(x0, -B / 2, -D),
                        "corner2" : vector(x1,  B / 2, 0 * millimeter) });
                continue;
            }

            // GOB resin module, and the lit area as a SEPARATE body so a
            // render can give it an emissive appearance. The 0.5mm reveal
            // around it is the same half-gap border the pixel arithmetic
            // above derives — it is the real edge of the pixel field.
            fCuboid(context, pid + "face", {
                    "corner1" : vector(x0, -B / 2, zPcbF),
                    "corner2" : vector(x1,  B / 2, -reveal) });
            fCuboid(context, pid + "lit", {
                    "corner1" : vector(x0 + border, -B / 2 + border, -reveal),
                    "corner2" : vector(x1 - border,  B / 2 - border, 0 * millimeter) });

            fCuboid(context, pid + "pcb", {
                    "corner1" : vector(x0, -B / 2, zPcbB),
                    "corner2" : vector(x1,  B / 2, zPcbF) });

            // Rear frame: a ring, open in the middle where everything lives.
            fCuboid(context, pid + "frame", {
                    "corner1" : vector(x0, -B / 2, -D),
                    "corner2" : vector(x1,  B / 2, zPcbB) });
            fCuboid(context, pid + "cav", {
                    "corner1" : vector(x0 + definition.frameW,
                                       -B / 2 + definition.frameW, -D - 1 * millimeter),
                    "corner2" : vector(x1 - definition.frameW,
                                        B / 2 - definition.frameW, zPcbB + 1 * millimeter) });
            opBoolean(context, pid + "frCut", {
                    "tools"         : qCreatedBy(pid + "cav", EntityType.BODY),
                    "targets"       : qCreatedBy(pid + "frame", EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });

            // Threaded mounting posts. These are the ONLY rear feature whose
            // position matters to the enclosure — the braces bolt to them —
            // so they are driven from the same variables the braces are.
            for (var sx = -1; sx <= 1; sx += 2)
            {
                for (var sy = -1; sy <= 1; sy += 2)
                {
                    const k  = "" ~ (sx + 1) ~ (sy + 1);
                    const px = xc + sx * definition.postXOffset;
                    const py = sy * definition.postYOffset;
                    fCylinder(context, pid + ("post" ~ k), {
                            "topCenter"    : vector(px, py, zPcbB),
                            "bottomCenter" : vector(px, py, -D),
                            "radius"       : definition.postDia / 2 });
                    fCylinder(context, pid + ("bore" ~ k), {
                            "topCenter"    : vector(px, py, zPcbB - 6 * millimeter),
                            "bottomCenter" : vector(px, py, -D - 1 * millimeter),
                            "radius"       : 1.5 * millimeter });
                    opBoolean(context, pid + ("boreCut" ~ k), {
                            "tools"         : qCreatedBy(pid + ("bore" ~ k), EntityType.BODY),
                            "targets"       : qCreatedBy(pid + ("post" ~ k), EntityType.BODY),
                            "operationType" : BooleanOperationType.SUBTRACTION });
                }
            }

            // Row/column driver ICs on the back of the PCB. Pure cosmetics —
            // they sit well inside every keep-out and touch nothing.
            for (var a = 0; a < 4; a += 1)
            {
                for (var b = 0; b < 2; b += 1)
                {
                    const cxi = xc + (a - 1.5) * 22 * millimeter;
                    const cyi = (b - 0.5) * 30 * millimeter;
                    fCuboid(context, pid + ("ic" ~ a ~ b), {
                            "corner1" : vector(cxi - 9 * millimeter, cyi - 3 * millimeter,
                                               zPcbB - 1.2 * millimeter),
                            "corner2" : vector(cxi + 9 * millimeter, cyi + 3 * millimeter, zPcbB) });
                }
            }

            // HUB75 in and out, plus the power terminals. These are what
            // #keepoutW/H/Proj abstract, so they live inside that envelope.
            for (var h = 0; h < 2; h += 1)
            {
                const hx = xc + (2 * h - 1) * definition.hdrPitch / 2;
                fCuboid(context, pid + ("hdr" ~ h), {
                        "corner1" : vector(hx - definition.hdrW / 2, -definition.hdrH / 2,
                                           zPcbB - definition.hdrProj),
                        "corner2" : vector(hx + definition.hdrW / 2,  definition.hdrH / 2, zPcbB) });
            }

            fCuboid(context, pid + "pwr", {
                    "corner1" : vector(xc - 11 * millimeter, -B / 2 + 14 * millimeter,
                                       zPcbB - 7 * millimeter),
                    "corner2" : vector(xc + 11 * millimeter, -B / 2 + 24 * millimeter, zPcbB) });
        }
    });

// ────────────────────────────────────────────────────────────────────────
// PSU proxy
// ────────────────────────────────────────────────────────────────────────
// Mean Well LRS-50-5 — 99 x 82 x 30 mm, 210 g, 5V 10A. An envelope only.
//
// It hangs from the divider shelf's underside on its own side-face M3 holes,
// inside the mains compartment. Laid with its 82mm dimension along y, which
// is why that compartment exists at all: 82mm fits no clear band in the bay
// behind the panels, because the panel connector keep-outs occupy the middle
// of it.
//
// (The Voltaic V50 bank proxy this replaces is in git history — the design
// went mains on 2026-09-08.)

annotation { "Feature Type Name" : "PSU proxy" }
export const psuProxy = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Length (x)" }
        isLength(definition.psuL, LENGTH_BOUNDS);

        annotation { "Name" : "Width (y)" }
        isLength(definition.psuW, LENGTH_BOUNDS);

        annotation { "Name" : "Thickness (z)" }
        isLength(definition.psuT, LENGTH_BOUNDS);

        annotation { "Name" : "Centre x" }
        isLength(definition.psuX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Top face y" }
        isLength(definition.psuYTop, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Front face z" }
        isLength(definition.psuZFront, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Hole A x from terminal end" }
        isLength(definition.psuHoleAX, LENGTH_BOUNDS);

        annotation { "Name" : "Hole B x from terminal end" }
        isLength(definition.psuHoleBX, LENGTH_BOUNDS);

        annotation { "Name" : "Hole height from front face" }
        isLength(definition.psuHoleZ, LENGTH_BOUNDS);

        annotation { "Name" : "Thread nominal diameter" }
        isLength(definition.threadDia, LENGTH_BOUNDS);

        annotation { "Name" : "Max screw penetration" }
        isLength(definition.threadDepth, LENGTH_BOUNDS);

        annotation { "Name" : "Detailed" }
        definition.detail is boolean;

        annotation { "Name" : "Vent slot width" }
        isLength(definition.ventW, LENGTH_BOUNDS);

        annotation { "Name" : "Vent slot pitch" }
        isLength(definition.ventPitch, LENGTH_BOUNDS);

        annotation { "Name" : "Terminal block depth" }
        isLength(definition.termDepth, LENGTH_BOUNDS);

        annotation { "Name" : "Terminal pitch" }
        isLength(definition.termPitch, LENGTH_BOUNDS);

        annotation { "Name" : "Terminal count" }
        isInteger(definition.termCount, POSITIVE_COUNT_BOUNDS);
    }
    {
        fCuboid(context, id + "psu", {
                "corner1" : vector(definition.psuX - definition.psuL / 2,
                                   definition.psuYTop - definition.psuW,
                                   definition.psuZFront - definition.psuT),
                "corner2" : vector(definition.psuX + definition.psuL / 2,
                                   definition.psuYTop,
                                   definition.psuZFront) });

        // The threaded M3 side holes, blind into the low-y face — the one
        // that faces the bottom panel. Same datums the shell uses: x from
        // the TERMINAL (high-x) end, height down from the front face. The
        // point of putting them on the proxy is that the screw run is now
        // visible end to end: 3mm of wood, then psuStandoff of air, then
        // these threads. That sets the screw length, and it is the only
        // place the model can show the standoff being spanned rather than
        // bridged by nothing.
        //
        // Nominal Ø3, not a clearance hole — these are threaded, so the
        // proxy shows the thread envelope and the wall carries the 4.5mm
        // clearance. The opposite (high-y) face carries a matching pair;
        // it is not modelled because nothing bolts to it in this build.
        //
        // The depth is the spec sheet's L = 5mm MAXIMUM PENETRATION, not a
        // thread depth to aim for. Modelling it as a blind pocket makes the
        // limit visible: 3mm wood + 5mm standoff + 5mm penetration = 13mm,
        // so M3 x 12 is the longest screw that cannot reach the internals.
        const psuYLo = definition.psuYTop - definition.psuW;
        const psuXHi = definition.psuX + definition.psuL / 2;
        const holeZ = definition.psuZFront - definition.psuHoleZ;
        var tools = [];
        for (var i = 0; i < 2; i += 1)
        {
            var hx = psuXHi - definition.psuHoleAX;
            if (i == 1)
            {
                hx = psuXHi - definition.psuHoleBX;
            }
            fCylinder(context, id + ("th" ~ i), {
                    "topCenter"    : vector(hx, psuYLo + definition.threadDepth, holeZ),
                    "bottomCenter" : vector(hx, psuYLo - 1 * millimeter, holeZ),
                    "radius"       : definition.threadDia / 2 });
            tools = append(tools, qCreatedBy(id + ("th" ~ i), EntityType.BODY));
        }
        opBoolean(context, id + "threadDrill", {
                "tools"         : qUnion(tools),
                "targets"       : qCreatedBy(id + "psu", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        if (!definition.detail)
        {
            return;
        }

        // ── Everything below is appearance, not clearance ──────────────
        // The envelope above is what the box is designed around; this makes
        // the proxy read as the part instead of as a brick. Vents are cut as
        // 0.8mm recesses rather than through-slots deliberately: a hollow
        // proxy would make every bounding-box check noisier for no gain.
        //
        // The one thing here that is NOT cosmetic is the terminal block. Its
        // screws face +x, which is why #psuX is pushed left: the screwdriver
        // needs a straight run at them, and that run is 90mm of empty bay.
        const vD   = 0.8 * millimeter;
        const zHi  = definition.psuZFront;
        const zLo  = zHi - definition.psuT;
        const xLo  = definition.psuX - definition.psuL / 2;
        const yHi  = definition.psuYTop;
        const yMid = (psuYLo + yHi) / 2;
        const zMid = (zLo + zHi) / 2;

        var vents = [];
        var vk = 0;

        // Top face: slots running across the short axis.
        const topN = floor((definition.psuL - 42 * millimeter) / definition.ventPitch);
        for (var i = 0; i < topN; i += 1)
        {
            const vx = xLo + 12 * millimeter + i * definition.ventPitch;
            fCuboid(context, id + ("vt" ~ vk), {
                    "corner1" : vector(vx, psuYLo + 18 * millimeter, zHi - vD),
                    "corner2" : vector(vx + definition.ventW, yHi - 18 * millimeter,
                                       zHi + 1 * millimeter) });
            vents = append(vents, qCreatedBy(id + ("vt" ~ vk), EntityType.BODY));
            vk += 1;
        }

        // Both long side faces, in a band across the middle. Slots that would
        // land on a mounting hole are skipped rather than merged into it.
        const hA = psuXHi - definition.psuHoleAX;
        const hB = psuXHi - definition.psuHoleBX;
        const sideN = floor((definition.psuL - 30 * millimeter) / definition.ventPitch);
        for (var i = 0; i < sideN; i += 1)
        {
            const vx = xLo + 10 * millimeter + i * definition.ventPitch;
            const cx = vx + definition.ventW / 2;
            if (abs(cx - hA) < 6 * millimeter || abs(cx - hB) < 6 * millimeter)
            {
                continue;
            }
            for (var sgn = 0; sgn < 2; sgn += 1)
            {
                var y0 = psuYLo - 1 * millimeter;
                var y1 = psuYLo + vD;
                if (sgn == 1)
                {
                    y0 = yHi - vD;
                    y1 = yHi + 1 * millimeter;
                }
                fCuboid(context, id + ("vt" ~ vk), {
                        "corner1" : vector(vx, y0, zMid - 8 * millimeter),
                        "corner2" : vector(vx + definition.ventW, y1, zMid + 8 * millimeter) });
                vents = append(vents, qCreatedBy(id + ("vt" ~ vk), EntityType.BODY));
                vk += 1;
            }
        }

        // Terminal block, in a step recessed into the PSU's TOP COVER at the
        // terminal end. Measured off Mean Well's own STEP (see
        // hardware/cad/vendor/meanwell-lrs-50-5.step): five ways — L, N, FG,
        // -V, +V — at 9.3mm pitch, Ø6.5 screw heads sunk ~10mm below the
        // cover plane, and the screws face OUT OF THE COVER.
        //
        // ⚠ THAT DIRECTION IS A DESIGN CONSTRAINT, not decoration. The screws
        // are the only way mains gets connected, so the cover has to face
        // something openable. Here it faces -z, the back cover. Rotate this
        // part 180 degrees about its long axis and the terminals point at the
        // bezel, which is glued shut — see power-plan.md.
        const zTop = zLo;                       // cover face, toward the back
        fCuboid(context, id + "termPk", {
                "corner1" : vector(psuXHi - definition.termDepth, psuYLo + 4 * millimeter,
                                   zTop - 1 * millimeter),
                "corner2" : vector(psuXHi + 1 * millimeter, yHi - 4 * millimeter,
                                   zTop + 10 * millimeter) });
        vents = append(vents, qCreatedBy(id + "termPk", EntityType.BODY));

        opBoolean(context, id + "ventCut", {
                "tools"         : qUnion(vents),
                "targets"       : qCreatedBy(id + "psu", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // Vadj trimmer, on the cover near the DC end.
        fCylinder(context, id + "vadj", {
                "topCenter"    : vector(psuXHi - 30 * millimeter, psuYLo + 16 * millimeter,
                                        zHi - 1.6 * millimeter),
                "bottomCenter" : vector(psuXHi - 30 * millimeter, psuYLo + 16 * millimeter,
                                        zHi + 2 * millimeter),
                "radius"       : 3.5 * millimeter });
        opBoolean(context, id + "vadjCut", {
                "tools"         : qCreatedBy(id + "vadj", EntityType.BODY),
                "targets"       : qCreatedBy(id + "psu", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        fCuboid(context, id + "term", {
                "corner1" : vector(psuXHi - definition.termDepth, psuYLo + 4 * millimeter,
                                   zTop + 1 * millimeter),
                "corner2" : vector(psuXHi, yHi - 4 * millimeter, zTop + 10 * millimeter) });
        var screws = [qCreatedBy(id + "term", EntityType.BODY)];
        for (var i = 0; i < definition.termCount; i += 1)
        {
            const ty = yMid + (i - (definition.termCount - 1) / 2) * definition.termPitch;
            fCylinder(context, id + ("ts" ~ i), {
                    "topCenter"    : vector(psuXHi - definition.termDepth / 2, ty,
                                            zTop + 0.8 * millimeter),
                    "bottomCenter" : vector(psuXHi - definition.termDepth / 2, ty,
                                            zTop + 4 * millimeter),
                    "radius"       : 3.25 * millimeter });
            screws = append(screws, qCreatedBy(id + ("ts" ~ i), EntityType.BODY));
        }
        opBoolean(context, id + "termJoin", {
                "tools"         : qUnion(screws),
                "operationType" : BooleanOperationType.UNION });
    });

// ────────────────────────────────────────────────────────────────────────
// IEC inlet proxy
// ────────────────────────────────────────────────────────────────────────
// IEC320 C14 + rocker switch + 5x20mm fuse, all measured 2026-09-09.
//
// The flange is NOT a plain rectangle. It overhangs 6.25mm beyond the
// cutout on the short sides, but on the long sides it is a shallow
// triangular lobe peaking 10.75mm out at the middle and tapering to meet
// the short-side flange — with the screw hole sitting in that lobe.
//
// Modelling it settles the screw-spacing contradiction. The screws are on
// the SHORT axis, not the long one: cutH/2 + tip/2 from centre, so about
// 38mm apart. A 40mm spacing (as the listings claimed) puts the hole
// 6.38mm out of a 10.75mm lobe, which is also plausible — hence the
// derived variable and the note to measure hole centre to hole centre.
//
// It also shows why this module cannot go in a side wall: the flange's
// short extent is cutH + 2*tip = 48.75mm against a 44.5mm deep case. That
// is what drove bayDepth to 60mm, which is now what lets the flange live
// in ANY wall — the 48.75mm short extent fits a 60mm depth with 5.6mm
// each side, whichever wall it goes in.
//
// It sits in the BOTTOM (low-y) wall, not the right-hand one. The reason
// is the portrait orientation: stood on end the box rests on a +/-x wall,
// so an inlet there is underneath the case and the cord jacks it off the
// table. The bottom wall is a vertical SIDE in portrait, so the cord
// exits horizontally and no feet are needed. The cost is that landscape
// then rests on the inlet instead — the +y top wall is the only one that
// is a side in both, and it routes mains diagonally across the box past
// the Matrix Portal, which is worse than giving up landscape.
//
// x = 100mm is not free either. The body needs 37.45mm of depth behind
// the wall, and the PSU occupies x -44.6..54.6 there, so the inlet has to
// clear it: 100 - cutW/2 = 76.6 leaves 22mm. Going the other way (x
// negative) would clear the PSU too but put the inlet at the far end from
// the PSU terminals, which face +x.

annotation { "Feature Type Name" : "IEC inlet proxy" }
export const iecProxy = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Outer face y" }
        isLength(definition.faceY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Centre x" }
        isLength(definition.cx, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Centre z" }
        isLength(definition.cz, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Cutout long (x)" }
        isLength(definition.cutW, LENGTH_BOUNDS);

        annotation { "Name" : "Cutout short (z)" }
        isLength(definition.cutH, LENGTH_BOUNDS);

        annotation { "Name" : "Body depth" }
        isLength(definition.depth, LENGTH_BOUNDS);

        annotation { "Name" : "Flange end overhang" }
        isLength(definition.flEnd, LENGTH_BOUNDS);

        annotation { "Name" : "Flange lobe tip" }
        isLength(definition.flTip, LENGTH_BOUNDS);

        annotation { "Name" : "Flange thickness" }
        isLength(definition.flThk, LENGTH_BOUNDS);

        annotation { "Name" : "Screw spacing (short axis)" }
        isLength(definition.screwSpacing, LENGTH_BOUNDS);

        annotation { "Name" : "Screw hole diameter" }
        isLength(definition.screwDia, LENGTH_BOUNDS);
    }
    {
        // body, reaching INWARD (+y) from the outer face of the bottom wall
        fCuboid(context, id + "body", {
                "corner1" : vector(definition.cx - definition.cutW / 2,
                                   definition.faceY,
                                   definition.cz - definition.cutH / 2),
                "corner2" : vector(definition.cx + definition.cutW / 2,
                                   definition.faceY + definition.depth,
                                   definition.cz + definition.cutH / 2) });

        // flange: hexagonal outline, sketched on the wall face
        const hl = definition.cutW / 2 + definition.flEnd;   // half long extent
        const hs = definition.cutH / 2;                      // half short extent
        const tp = hs + definition.flTip;                    // lobe apex

        // Sketch on the wall's OUTER face, normal pointing out of the box
        // (-y). With xDirection = global +x the sketch's own y axis comes
        // out as global +z, so the polyline below is unchanged: u is the
        // long extent, v the lobed short one.
        var sk = newSketchOnPlane(context, id + "flSk", {
                "sketchPlane" : plane(vector(definition.cx, definition.faceY, definition.cz),
                                      vector(0, -1, 0),
                                      vector(1, 0, 0)) });

        skPolyline(sk, "outline", {
                "points" : [
                    vector(-hl, -hs),
                    vector(0 * meter, -tp),
                    vector( hl, -hs),
                    vector( hl,  hs),
                    vector(0 * meter,  tp),
                    vector(-hl,  hs),
                    vector(-hl, -hs)
                ] });
        skSolve(sk);

        opExtrude(context, id + "flEx", {
                "entities"  : qSketchRegion(id + "flSk"),
                "direction" : vector(0, -1, 0),
                "endBound"  : BoundingType.BLIND,
                "endDepth"  : definition.flThk });

        // Drill the flange too. The wall had these holes but the flange did
        // not, so the model showed screws passing through solid material —
        // which is exactly the sort of thing a proxy is meant to catch.
        var holes = [];
        for (var i = 0; i < 2; i += 1)
        {
            var hz = definition.cz - definition.screwSpacing / 2;
            if (i == 1)
            {
                hz = definition.cz + definition.screwSpacing / 2;
            }
            fCylinder(context, id + ("fh" ~ i), {
                    "topCenter"    : vector(definition.cx,
                                            definition.faceY - definition.flThk - 1 * millimeter, hz),
                    "bottomCenter" : vector(definition.cx,
                                            definition.faceY + 1 * millimeter, hz),
                    "radius"       : definition.screwDia / 2 });
            holes = append(holes, qCreatedBy(id + ("fh" ~ i), EntityType.BODY));
        }
        opBoolean(context, id + "flDrill", {
                "tools"         : qUnion(holes),
                "targets"       : qCreatedBy(id + "flEx", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });
    });

// ────────────────────────────────────────────────────────────────────────
// Bay obstructions
// ────────────────────────────────────────────────────────────────────────
// Proxies for everything that already occupies the bay, so anything added
// there can be checked against them instead of assumed to fit.
//
// Per panel, one connector KEEP-OUT covering the HUB75 IN and OUT headers
// and the JST power connector. Positions are not published and vary, so
// this is one generous envelope rather than individual bosses — measure it
// off a real panel and shrink it.
//
// Plus the Matrix Portal itself, which is the big one: it does not sit
// against the panel, it rides ON the HUB75 header, so it reaches roughly
// 20mm back even though the board's own span is 19.1mm. Footprint measured
// from the vendored Adafruit STEP.

annotation { "Feature Type Name" : "Bay obstructions" }
export const bayObstructions = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Panel width" }
        isLength(definition.panelW, LENGTH_BOUNDS);

        annotation { "Name" : "Panel count" }
        isInteger(definition.panelCount, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel depth" }
        isLength(definition.panelDepth, LENGTH_BOUNDS);

        annotation { "Name" : "Keep-out width" }
        isLength(definition.keepoutW, LENGTH_BOUNDS);

        annotation { "Name" : "Keep-out height" }
        isLength(definition.keepoutH, LENGTH_BOUNDS);

        annotation { "Name" : "Keep-out projection" }
        isLength(definition.keepoutProj, LENGTH_BOUNDS);

        annotation { "Name" : "Keep-out offset x" }
        isLength(definition.keepoutX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Keep-out offset y" }
        isLength(definition.keepoutY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Board width" }
        isLength(definition.mpW, LENGTH_BOUNDS);

        annotation { "Name" : "Board height" }
        isLength(definition.mpH, LENGTH_BOUNDS);

        annotation { "Name" : "Board thickness" }
        isLength(definition.mpProj, LENGTH_BOUNDS);

        annotation { "Name" : "Board front face z" }
        isLength(definition.mpZFront, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Board centre x" }
        isLength(definition.mpX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Board centre y" }
        isLength(definition.mpY, ANY_LENGTH_BOUNDS);


    }
    {
        const back = -definition.panelDepth;
        const span = definition.panelCount * definition.panelW;

        for (var i = 0; i < definition.panelCount; i += 1)
        {
            const pc = -span / 2 + (i + 0.5) * definition.panelW + definition.keepoutX;

            fCuboid(context, id + ("keepout" ~ i), {
                    "corner1" : vector(pc - definition.keepoutW / 2,
                                       definition.keepoutY - definition.keepoutH / 2,
                                       back - definition.keepoutProj),
                    "corner2" : vector(pc + definition.keepoutW / 2,
                                       definition.keepoutY + definition.keepoutH / 2,
                                       back) });
        }

        // The Matrix Portal is now mounted to the CASE, not plugged onto the
        // panel, so its depth is set by where it is bolted rather than by the
        // header height. A HUB75 ribbon reaches the panel instead — which is
        // why the keep-out above got deeper, not shallower: a ribbon needs
        // room to turn behind the connector where a board did not.
        // (The IEC envelope used to be duplicated here. It is modelled
        // properly in iecProxy, flange included, so this copy is gone.)

        fCuboid(context, id + "board", {
                "corner1" : vector(definition.mpX - definition.mpW / 2,
                                   definition.mpY - definition.mpH / 2,
                                   definition.mpZFront - definition.mpProj),
                "corner2" : vector(definition.mpX + definition.mpW / 2,
                                   definition.mpY + definition.mpH / 2,
                                   definition.mpZFront) });
    });

// ────────────────────────────────────────────────────────────────────────
// Finger joints
// ────────────────────────────────────────────────────────────────────────
// Two perpendicular plates meeting at an edge overlap in a rectangular
// prism. Slice that prism along the joint and give alternating slices to
// each plate: cut the even slices out of one and the odd slices out of the
// other, and they interlock with no interference anywhere.
//
// KERF. A laser removes material either side of the cut line, so a slot
// comes out `kerf` wider than modelled and a tab `kerf` narrower — 2 x kerf
// of slop, which is why an uncompensated box rattles. Every removed slice
// is therefore shrunk by kerf/2 at each end that is an INTERIOR cut. Ends
// that coincide with the plate's own outer edge are not cuts and get no
// compensation. After cutting, both tabs and slots land on nominal, giving
// a zero-clearance press fit.
//
// Compensation is applied along the finger axis only — the dimension that
// governs the fit. Notch DEPTH is left nominal, so a joint may sit up to
// kerf/2 proud; in basswood that sands flush. Cut a test comb first.

const ANY_LENGTH_BOUNDS = { (millimeter) : [-2000, 0, 2000] } as LengthBoundSpec;
const KERF_BOUNDS       = { (millimeter) : [0, 0.2, 5] } as LengthBoundSpec;

function fingerCount(extent is ValueWithUnits, target is ValueWithUnits) returns number
{
    var n = floor(extent / target);
    if (n < 3)
    {
        n = 3;
    }
    if (n % 2 == 0)
    {
        n += 1;                 // odd, so each plate keeps a tab at both ends
    }
    return n;
}

function cutFingers(context is Context, id is Id, target is Query,
                    ranges is array, axis is number, n is number,
                    phase is number, kerf is ValueWithUnits)
{
    const lo = ranges[axis][0];
    const hi = ranges[axis][1];
    const step = (hi - lo) / n;

    var tools = [];
    var k = 0;

    for (var i = 0; i < n; i += 1)
    {
        if (i % 2 != phase)
        {
            continue;
        }

        var a = lo + i * step;
        var b = lo + (i + 1) * step;

        if (i > 0)      { a = a + kerf / 2; }   // interior cut
        if (i < n - 1)  { b = b - kerf / 2; }   // interior cut

        var r = ranges;
        r[axis] = [a, b];

        fCuboid(context, id + ("f" ~ k), {
                "corner1" : vector(r[0][0], r[1][0], r[2][0]),
                "corner2" : vector(r[0][1], r[1][1], r[2][1])
        });
        tools = append(tools, qCreatedBy(id + ("f" ~ k), EntityType.BODY));
        k += 1;
    }

    if (size(tools) > 0)
    {
        opBoolean(context, id + "b", {
                "tools"         : qUnion(tools),
                "targets"       : target,
                "operationType" : BooleanOperationType.SUBTRACTION
        });
    }
}

// ────────────────────────────────────────────────────────────────────────
// Hex pocket
// ────────────────────────────────────────────────────────────────────────
// A hexagon is the intersection of three slabs at 60 degrees to each other,
// each as wide as the nut's across-flats. Cheaper and more robust than
// sketching a polygon, and it verifies easily: the result must be an
// 8-faced prism.

function hexPrism(context is Context, id is Id, cx is ValueWithUnits, cy is ValueWithUnits,
                  acrossFlats is ValueWithUnits, z0 is ValueWithUnits, z1 is ValueWithUnits) returns Query
{
    const reach = acrossFlats * 1.5;
    var slabs = [];

    for (var i = 0; i < 3; i += 1)
    {
        fCuboid(context, id + ("slab" ~ i), {
                "corner1" : vector(cx - reach, cy - acrossFlats / 2, z0),
                "corner2" : vector(cx + reach, cy + acrossFlats / 2, z1) });

        if (i > 0)
        {
            opTransform(context, id + ("rot" ~ i), {
                    "bodies"    : qCreatedBy(id + ("slab" ~ i), EntityType.BODY),
                    "transform" : rotationAround(line(vector(cx, cy, z0), vector(0, 0, 1)),
                                                 i * 60 * degree) });
        }
        slabs = append(slabs, qCreatedBy(id + ("slab" ~ i), EntityType.BODY));
    }

    opBoolean(context, id + "hex", {
            "tools"         : qUnion(slabs),
            "operationType" : BooleanOperationType.INTERSECTION });

    return qCreatedBy(id, EntityType.BODY);
}

// ────────────────────────────────────────────────────────────────────────
// Part naming
// ────────────────────────────────────────────────────────────────────────
// A body created by fCuboid has no name, and Onshape will happily call it
// "Part 12". That is invisible until a DXF export or a BOM needs to say
// WHICH part, so every body that survives to the end gets named here.

function nameBody(context is Context, id is Id, bodyId is Id, name is string)
{
    setProperty(context, {
            "entities"     : qCreatedBy(bodyId, EntityType.BODY),
            "propertyType" : PropertyType.NAME,
            "value"        : name });
}

// ────────────────────────────────────────────────────────────────────────
// Enclosure shell  (named enclosureShell — a bare `shell` collides with std)
// ────────────────────────────────────────────────────────────────────────
// Bezel laminations plus the four walls, in ONE feature — the finger joints
// couple them, so splitting them into two features would mean two places
// independently deriving the same finger layout and silently disagreeing.
//
// Construction, front to back:
//
//   z = 0    ┬─────────────────────────────┬  outer lamination: FULL footprint,
//            │  ┌───────────────────────┐  │  finger-jointed to the wall front
//   z = t    ┼──┤ inner lamination(s)   ├──┼  edges. Inner laminations are
//            │  │ INSET by t, drop      │  │  inset by t so they drop inside
//   z = 0    ┤  │ inside the tube       │  ├  the tube and self-locate the
//            │  └───────────────────────┘  │  bezel on the panel face.
//            │        panels, bay          │
//   z =-depth┴─────────────────────────────┴  walls: a tube along z
//
// Three joint families:
//   1. four VERTICAL corners, fingers along z, over the full wall height
//   2. four FRONT edges, outer lamination to wall, fingers along the edge,
//      restricted to between the corners so nothing triple-overlaps
//   3. the corner squares in the outer-lamination band are removed from the
//      horizontal walls, so the bezel owns its own corners
//
// (3) is deterministic because the finger count is forced odd: the last
// finger index is always even, so phase 0 — the vertical walls — always
// gives it up, and the horizontal walls are always the ones still holding
// corner material in that band.

annotation { "Feature Type Name" : "Enclosure shell" }
export const enclosureShell = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Aperture width" }
        isLength(definition.apertureW, LENGTH_BOUNDS);

        annotation { "Name" : "Aperture height" }
        isLength(definition.apertureH, LENGTH_BOUNDS);

        annotation { "Name" : "Side margin" }
        isLength(definition.marginSide, LENGTH_BOUNDS);

        annotation { "Name" : "Top margin" }
        isLength(definition.marginTop, LENGTH_BOUNDS);

        annotation { "Name" : "Control band height" }
        isLength(definition.controlH, LENGTH_BOUNDS);

        annotation { "Name" : "Knob pitch" }
        isLength(definition.knobPitch, LENGTH_BOUNDS);

        annotation { "Name" : "Knob count" }
        isInteger(definition.knobCount, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Bore diameter" }
        isLength(definition.boreDia, LENGTH_BOUNDS);

        annotation { "Name" : "Sheet thickness" }
        isLength(definition.thickness, LENGTH_BOUNDS);

        annotation { "Name" : "Bezel laminations" }
        isInteger(definition.layers, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Internal depth" }
        isLength(definition.depth, LENGTH_BOUNDS);

        annotation { "Name" : "Target finger length" }
        isLength(definition.fingerLen, LENGTH_BOUNDS);

        annotation { "Name" : "Kerf" }
        isLength(definition.kerf, KERF_BOUNDS);

        annotation { "Name" : "Panel width" }
        isLength(definition.panelW, LENGTH_BOUNDS);

        annotation { "Name" : "Panel count" }
        isInteger(definition.panelCount, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel depth" }
        isLength(definition.panelDepth, LENGTH_BOUNDS);

        annotation { "Name" : "Brace y offset" }
        isLength(definition.braceYOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Brace width" }
        isLength(definition.braceW, LENGTH_BOUNDS);

        annotation { "Name" : "Panel post x offset" }
        isLength(definition.postXOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Screw diameter" }
        isLength(definition.screwDia, LENGTH_BOUNDS);

        annotation { "Name" : "Screw slot length" }
        isLength(definition.slotLen, LENGTH_BOUNDS);

        annotation { "Name" : "Screw slot width" }
        isLength(definition.slotW, LENGTH_BOUNDS);

        annotation { "Name" : "Rear rail width" }
        isLength(definition.railW, LENGTH_BOUNDS);

        annotation { "Name" : "Rear rail inset from top/bottom walls" }
        isLength(definition.railInset, LENGTH_BOUNDS);

        annotation { "Name" : "Nut across flats" }
        isLength(definition.nutAcrossFlats, LENGTH_BOUNDS);

        annotation { "Name" : "Screw x span" }
        isLength(definition.screwXSpan, LENGTH_BOUNDS);

        annotation { "Name" : "Screws per rail" }
        isInteger(definition.screwsPerRail, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Back cover clearance" }
        isLength(definition.backClearance, KERF_BOUNDS);

        annotation { "Name" : "Knob cluster centre x" }
        isLength(definition.knobXCentre, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Knob grid columns" }
        isInteger(definition.knobCols, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Knob cluster centre y" }
        isLength(definition.knobYCentre, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "PSU standoff from bottom wall" }
        isLength(definition.psuStandoff, LENGTH_BOUNDS);

        annotation { "Name" : "Stiffening web depth" }
        isLength(definition.webDepth, LENGTH_BOUNDS);

        annotation { "Name" : "PSU length (x)" }
        isLength(definition.psuL, LENGTH_BOUNDS);

        annotation { "Name" : "PSU centre x" }
        isLength(definition.psuX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "PSU front face z" }
        isLength(definition.psuZFront, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "PSU hole A from low-x end" }
        isLength(definition.psuHoleAX, LENGTH_BOUNDS);

        annotation { "Name" : "PSU hole B from low-x end" }
        isLength(definition.psuHoleBX, LENGTH_BOUNDS);

        annotation { "Name" : "PSU hole height from base" }
        isLength(definition.psuHoleZ, LENGTH_BOUNDS);

        annotation { "Name" : "PSU hole clearance dia" }
        isLength(definition.psuHoleDia, LENGTH_BOUNDS);

        annotation { "Name" : "IEC cutout width" }
        isLength(definition.iecCutW, LENGTH_BOUNDS);

        annotation { "Name" : "IEC cutout height" }
        isLength(definition.iecCutH, LENGTH_BOUNDS);

        annotation { "Name" : "IEC screw spacing" }
        isLength(definition.iecScrewSpacing, LENGTH_BOUNDS);

        annotation { "Name" : "IEC screw diameter" }
        isLength(definition.iecScrewDia, LENGTH_BOUNDS);

        annotation { "Name" : "IEC position x" }
        isLength(definition.iecX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "IEC position z" }
        isLength(definition.iecZ, ANY_LENGTH_BOUNDS);
    }
    {
        const t    = definition.thickness;
        const nl   = definition.layers;
        const kerf = definition.kerf;
        const over = 1 * millimeter;

        const left   = -(definition.apertureW / 2 + definition.marginSide);
        const right  =   definition.apertureW / 2 + definition.marginSide;
        // The PSU shares the control band rather than having a compartment of
        // its own — the knobs are clustered to one end and the supply takes
        // the other. That is what keeps the box 43mm shorter than a separate
        // compartment below would.
        const bottom = -(definition.apertureH / 2 + definition.controlH);
        const top    =   definition.apertureH / 2 + definition.marginTop;

        // DATUM: z = 0 is the front plane — the bezel's outer face AND the
        // LED surface, coplanar. The bezel therefore hangs BACK from z = 0
        // and the panel passes through its aperture to finish flush.
        const zBack  = -definition.depth;
        const zFront = 0 * meter;               // outer face of the bezel
        const zOut0  = -t;                      // outer lamination band
        const zOut1  = 0 * meter;
        const zBezB  = -nl * t;                 // rearmost bezel lamination

        // ── walls ───────────────────────────────────────────────────────
        // Left/right span the full height, top/bottom the full width; they
        // overlap at the corners, which family (1) then resolves.
        fCuboid(context, id + "wallL", {
                "corner1" : vector(left,      bottom, zBack),
                "corner2" : vector(left + t,  top,    zFront) });
        fCuboid(context, id + "wallR", {
                "corner1" : vector(right - t, bottom, zBack),
                "corner2" : vector(right,     top,    zFront) });
        fCuboid(context, id + "wallB", {
                "corner1" : vector(left,  bottom,     zBack),
                "corner2" : vector(right, bottom + t, zFront) });
        fCuboid(context, id + "wallT", {
                "corner1" : vector(left,  top - t, zBack),
                "corner2" : vector(right, top,     zFront) });

        // ── family 1: vertical corner joints, fingers along z ───────────
        const nz = fingerCount(zFront - zBack, definition.fingerLen);

        const corners = [
            { "vert" : "wallL", "horz" : "wallB", "x" : [left, left + t],   "y" : [bottom, bottom + t] },
            { "vert" : "wallR", "horz" : "wallB", "x" : [right - t, right], "y" : [bottom, bottom + t] },
            { "vert" : "wallL", "horz" : "wallT", "x" : [left, left + t],   "y" : [top - t, top] },
            { "vert" : "wallR", "horz" : "wallT", "x" : [right - t, right], "y" : [top - t, top] }
        ];

        for (var ci = 0; ci < size(corners); ci += 1)
        {
            const c = corners[ci];
            const ranges = [c.x, c.y, [zBack, zFront]];
            cutFingers(context, id + ("cv" ~ ci), qCreatedBy(id + c.vert, EntityType.BODY),
                       ranges, 2, nz, 0, kerf);
            cutFingers(context, id + ("ch" ~ ci), qCreatedBy(id + c.horz, EntityType.BODY),
                       ranges, 2, nz, 1, kerf);
        }

        // ── family 3: hand the bezel its own corners ────────────────────
        // The horizontal walls are the ones still holding corner material in
        // the outer-lamination band (see the note above), so cut it from them.
        for (var ci = 0; ci < size(corners); ci += 1)
        {
            const c = corners[ci];
            fCuboid(context, id + ("csq" ~ ci), {
                    "corner1" : vector(c.x[0], c.y[0], zOut0 - kerf / 2),
                    "corner2" : vector(c.x[1], c.y[1], zOut1 + over) });
            opBoolean(context, id + ("csqCut" ~ ci), {
                    "tools"         : qCreatedBy(id + ("csq" ~ ci), EntityType.BODY),
                    "targets"       : qCreatedBy(id + c.horz, EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
        }

        // ── bezel laminations ───────────────────────────────────────────
        // Every lamination but the outermost is inset by t, so it drops
        // inside the tube. The outermost is full footprint and joints to
        // the walls.
        var plates = [];
        for (var i = 0; i < nl; i += 1)
        {
            // Every lamination but the outermost is inset.
            var in0 = t;
            if (i == nl - 1)
            {
                in0 = 0 * meter;
            }

            // i = 0 is the rearmost lamination; i = nl-1 is the outer face.
            fCuboid(context, id + ("layer" ~ i), {
                    "corner1" : vector(left + in0,  bottom + in0, -(nl - i) * t),
                    "corner2" : vector(right - in0, top - in0,    -(nl - i - 1) * t) });
            plates = append(plates, qCreatedBy(id + ("layer" ~ i), EntityType.BODY));
        }
        const outerPlate = qCreatedBy(id + ("layer" ~ (nl - 1)), EntityType.BODY);

        // ── family 2: front-edge joints ─────────────────────────────────
        // Restricted to between the corners so family 1 and family 3 stay
        // untouched.
        //
        // The bezel takes phase 1 and the walls phase 0, and that way round
        // matters: the finger count is forced odd, so phase 1 keeps the
        // fingers at BOTH ends of every edge. Give the bezel phase 0 instead
        // and it drops the first finger of both edges meeting at a corner,
        // which cuts the corner square free as a loose 3 x 3 x 3 fragment.
        const edges = [
            { "wall" : "wallL", "x" : [left, left + t],       "y" : [bottom + t, top - t], "axis" : 1 },
            { "wall" : "wallR", "x" : [right - t, right],     "y" : [bottom + t, top - t], "axis" : 1 },
            { "wall" : "wallB", "x" : [left + t, right - t],  "y" : [bottom, bottom + t],  "axis" : 0 },
            { "wall" : "wallT", "x" : [left + t, right - t],  "y" : [top - t, top],        "axis" : 0 }
        ];

        for (var ei = 0; ei < size(edges); ei += 1)
        {
            const e = edges[ei];
            const ranges = [e.x, e.y, [zOut0, zOut1]];
            const ne = fingerCount(ranges[e.axis][1] - ranges[e.axis][0], definition.fingerLen);

            cutFingers(context, id + ("fe" ~ ei), outerPlate,
                       ranges, e.axis, ne, 1, kerf);
            cutFingers(context, id + ("fw" ~ ei), qCreatedBy(id + e.wall, EntityType.BODY),
                       ranges, e.axis, ne, 0, kerf);
        }

        // ── panel cross-braces ──────────────────────────────────────────
        // The panels hang from these, not from the bezel. Each brace lies
        // flat against the panel backs and carries M3 screws driven from
        // BEHIND, forward into the panels' own rear threaded posts — so the
        // panel weight goes brace -> through-tenon -> wall, and the bezel
        // stays purely cosmetic.
        //
        // The screw holes are OBROUND, running in x. Panel post positions
        // shift between production runs and the datasheets do not give them,
        // so the slot absorbs the error; #postXOffset and #braceYOffset are
        // placeholders until measured off the actual panels.
        //
        // Each brace is a through-tenon: it spans the full box width, so its
        // ends sit inside the walls, and subtracting it from the walls cuts
        // an exactly matching mortise. Kerf goes the opposite way from the
        // finger joints here — the tenon is GROWN by kerf/2 per side and the
        // mortise SHRUNK by kerf/2, so both land on nominal after cutting.

        const zBraceF = -definition.panelDepth;         // against the panel backs
        const zBraceB = zBraceF - t;
        const panelSpan = definition.panelCount * definition.panelW;

        for (var s = 0; s < 2; s += 1)
        {
            var yc = definition.braceYOffset;
            if (s == 1)
            {
                yc = -definition.braceYOffset;
            }

            const tenonHalf = (definition.braceW + kerf) / 2;

            fCuboid(context, id + ("brace" ~ s), {
                    "corner1" : vector(left,  yc - tenonHalf, zBraceB),
                    "corner2" : vector(right, yc + tenonHalf, zBraceF) });

            // Mortise both side walls. Shrunk by kerf/2 in the wall's own
            // plane (y and z); x overshoots, which is harmless because only
            // the wall is a target.
            const mY0 = yc - definition.braceW / 2 + kerf / 2;
            const mY1 = yc + definition.braceW / 2 - kerf / 2;
            const mZ0 = zBraceB + kerf / 2;
            const mZ1 = zBraceF - kerf / 2;

            const sideWalls = ["wallL", "wallR"];
            for (var w = 0; w < 2; w += 1)
            {
                fCuboid(context, id + ("mort" ~ s ~ w), {
                        "corner1" : vector(left - over,  mY0, mZ0),
                        "corner2" : vector(right + over, mY1, mZ1) });
                opBoolean(context, id + ("mortCut" ~ s ~ w), {
                        "tools"         : qCreatedBy(id + ("mort" ~ s ~ w), EntityType.BODY),
                        "targets"       : qCreatedBy(id + sideWalls[w], EntityType.BODY),
                        "operationType" : BooleanOperationType.SUBTRACTION });
            }

            // Obround screw slots, two per panel. Deliberately oversize in
            // BOTH axes: slotLen absorbs x variation between production runs,
            // and slotW absorbs the fact that a panel's hole row is not
            // collinear — measured 8mm edge inset for the end holes and 9mm
            // for the centre hole on a P3, so a straight brace needs ~1mm of
            // perpendicular give too. Use washers under the screw heads.
            const r = definition.slotW / 2 - kerf / 2;
            var slots = [];
            for (var pi = 0; pi < definition.panelCount; pi += 1)
            {
                const pc = -panelSpan / 2 + (pi + 0.5) * definition.panelW;
                for (var k = 0; k < 2; k += 1)
                {
                    var px = pc + definition.postXOffset;
                    if (k == 1)
                    {
                        px = pc - definition.postXOffset;
                    }
                    const a = px - definition.slotLen / 2;
                    const b = px + definition.slotLen / 2;
                    const tag = "" ~ s ~ pi ~ k;

                    fCylinder(context, id + ("sa" ~ tag), {
                            "topCenter"    : vector(a, yc, zBraceF + over),
                            "bottomCenter" : vector(a, yc, zBraceB - over),
                            "radius"       : r });
                    fCylinder(context, id + ("sb" ~ tag), {
                            "topCenter"    : vector(b, yc, zBraceF + over),
                            "bottomCenter" : vector(b, yc, zBraceB - over),
                            "radius"       : r });
                    fCuboid(context, id + ("sm" ~ tag), {
                            "corner1" : vector(a, yc - r, zBraceB - over),
                            "corner2" : vector(b, yc + r, zBraceF + over) });

                    slots = append(slots, qCreatedBy(id + ("sa" ~ tag), EntityType.BODY));
                    slots = append(slots, qCreatedBy(id + ("sb" ~ tag), EntityType.BODY));
                    slots = append(slots, qCreatedBy(id + ("sm" ~ tag), EntityType.BODY));
                }
            }

            opBoolean(context, id + ("slotCut" ~ s), {
                    "tools"         : qUnion(slots),
                    "targets"       : qCreatedBy(id + ("brace" ~ s), EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
        }

        // ── rear rails and the removable back cover ─────────────────────
        // The finger joints get glued. The back does not, so it needs a
        // fastening that survives being opened indefinitely — wood screws in
        // 3mm basswood would strip after a few cycles.
        //
        // Tightening pulls the nut TOWARD the screw head, so the nut must
        // bear against material on that side, with only a clearance hole
        // through it. That is a counterbore, and one laser-cut sheet cannot
        // make one — so the rail is three laminations:
        //
        //     z:  -D      -D+t    -D+2t    -D+3t    -D+4t
        //         ├────────┼────────┼────────┼────────┤
        //         │ back   │ rail A │ rail B │ rail C │
        //         │ cover  │ Ø clr  │  hex   │ Ø clr  │
        //         │ Ø clr  │        │  nut   │        │
        //         └────────┴────────┴────────┴────────┘
        //          screw ───────────►  ↑
        //                    nut pulls back against rail A
        //
        // Rail A takes the nut's load — it bears on A's front face, and the
        // screw head clamps the cover against A's rear face.
        //
        // Rail B holds the nut laterally. Rail C stops it escaping into the
        // box when the screw is out — its hole is smaller than the nut's
        // across-flats, so the nut cannot pass, but any screw length can.
        //
        // THE TENON IS ON C, NOT A. A is the obvious choice — it is the one
        // the nut bears on — but A sits one thickness from the rear edge, so
        // its mortise leaves a 3mm sliver of side wall between the slot and
        // the edge, and that sliver lands exactly on the roots of the
        // bottom-wall finger notches. Any notch under it opens into the
        // slot: not thin, absent. Tenoning C instead puts the mortise 3t
        // from the rear edge with 9mm of wall behind it.
        //
        // The cost is that the nut's load reaches the wall through the two
        // glue lines of the lamination stack rather than directly. That is
        // not the weak link, and the numbers are not close:
        //
        //     tenon in shear   3 x 18 x 2 sides = 108mm^2 @ ~6MPa  ->  650N
        //     glue line        18 x 290         = 5220mm^2 @ ~2MPa -> 10kN
        //
        // The tenon is 15x weaker either way, so moving which lamination
        // carries it changes nothing that matters.
        //
        // The rails are also INSET from the top and bottom walls by
        // railInset, for the same reason in the other axis — flush against
        // the wall put the mortise hard against those same finger notches.
        //
        // The back cover is INSET into the wall opening rather than lapped
        // over it, so its outer face finishes flush with the wall rear edges
        // and the fixings are all that shows from behind.

        const zBc0 = zBack;                 // back cover, flush with wall rear
        const zBc1 = zBack + t;
        const railZ = [zBc1, zBc1 + t, zBc1 + 2 * t, zBc1 + 3 * t];

        const bcl = definition.backClearance;
        const railW = definition.railW;
        const clrR = definition.screwDia / 2 + 0.25 * millimeter;

        fCuboid(context, id + "backCover", {
                "corner1" : vector(left + t + bcl,  bottom + t + bcl, zBc0),
                "corner2" : vector(right - t - bcl, top - t - bcl,    zBc1) });

        const rIns = definition.railInset;
        const railY0 = [bottom + t + rIns, top - t - rIns - railW];
        var coverHoles = [];

        for (var ri = 0; ri < 2; ri += 1)
        {
            const y0 = railY0[ri];
            const y1 = y0 + railW;
            const yMid = (y0 + y1) / 2;

            // Rails A and B — inner width, glued to C, so no joints needed.
            fCuboid(context, id + ("railA" ~ ri), {
                    "corner1" : vector(left + t,  y0, railZ[0]),
                    "corner2" : vector(right - t, y1, railZ[1]) });
            fCuboid(context, id + ("railB" ~ ri), {
                    "corner1" : vector(left + t,  y0, railZ[1]),
                    "corner2" : vector(right - t, y1, railZ[2]) });

            // Rail C — through-tenoned into the side walls, 3t from the rear
            // edge so the mortise has wall material all the way round it.
            fCuboid(context, id + ("railC" ~ ri), {
                    "corner1" : vector(left,  y0 - kerf / 2, railZ[2]),
                    "corner2" : vector(right, y1 + kerf / 2, railZ[3]) });

            const rSide = ["wallL", "wallR"];
            for (var w = 0; w < 2; w += 1)
            {
                fCuboid(context, id + ("rmort" ~ ri ~ w), {
                        "corner1" : vector(left - over,  y0 + kerf / 2, railZ[2] + kerf / 2),
                        "corner2" : vector(right + over, y1 - kerf / 2, railZ[3] - kerf / 2) });
                opBoolean(context, id + ("rmortCut" ~ ri ~ w), {
                        "tools"         : qCreatedBy(id + ("rmort" ~ ri ~ w), EntityType.BODY),
                        "targets"       : qCreatedBy(id + rSide[w], EntityType.BODY),
                        "operationType" : BooleanOperationType.SUBTRACTION });
            }

            var clrA = [];
            var pockets = [];
            var clrC = [];

            for (var k = 0; k < definition.screwsPerRail; k += 1)
            {
                var sx = 0 * meter;
                if (definition.screwsPerRail > 1)
                {
                    sx = -definition.screwXSpan
                       + k * (2 * definition.screwXSpan / (definition.screwsPerRail - 1));
                }
                const tag = "" ~ ri ~ k;

                // clearance through the back cover
                fCylinder(context, id + ("bch" ~ tag), {
                        "topCenter"    : vector(sx, yMid, zBc1 + over),
                        "bottomCenter" : vector(sx, yMid, zBc0 - over),
                        "radius"       : definition.screwDia / 2 - kerf / 2 });
                coverHoles = append(coverHoles, qCreatedBy(id + ("bch" ~ tag), EntityType.BODY));

                // clearance through rail A — the nut bears on the ring around it
                fCylinder(context, id + ("cah" ~ tag), {
                        "topCenter"    : vector(sx, yMid, railZ[1] + over),
                        "bottomCenter" : vector(sx, yMid, railZ[0] - over),
                        "radius"       : clrR });
                clrA = append(clrA, qCreatedBy(id + ("cah" ~ tag), EntityType.BODY));

                // hex pocket through rail B — the nut itself
                pockets = append(pockets,
                    hexPrism(context, id + ("hexp" ~ tag), sx, yMid,
                             definition.nutAcrossFlats - kerf, railZ[1] - over, railZ[2] + over));

                // clearance through rail C — retains the nut, passes any screw
                fCylinder(context, id + ("cch" ~ tag), {
                        "topCenter"    : vector(sx, yMid, railZ[3] + over),
                        "bottomCenter" : vector(sx, yMid, railZ[2] - over),
                        "radius"       : clrR });
                clrC = append(clrC, qCreatedBy(id + ("cch" ~ tag), EntityType.BODY));
            }

            opBoolean(context, id + ("clrACut" ~ ri), {
                    "tools"         : qUnion(clrA),
                    "targets"       : qCreatedBy(id + ("railA" ~ ri), EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
            opBoolean(context, id + ("pocketCut" ~ ri), {
                    "tools"         : qUnion(pockets),
                    "targets"       : qCreatedBy(id + ("railB" ~ ri), EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
            opBoolean(context, id + ("clrCCut" ~ ri), {
                    "tools"         : qUnion(clrC),
                    "targets"       : qCreatedBy(id + ("railC" ~ ri), EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
        }

        // ── stiffening: one horizontal brace ────────────────────────────
        // Horizontal, and that orientation is the whole point. The
        // back-cover rail stacks run HORIZONTALLY along the top and bottom
        // edges, so a vertical brace has to cross both of them — no position
        // avoids it, only notching, which is what made the earlier vertical
        // web fight them. This brace is parallel to the rails and sits
        // between them, so it cannot clash at any depth.
        //
        // Placed just under the display aperture, which is the one y band
        // clear of everything: 3mm above the PSU, 0.5mm below the panels,
        // clear of the knob cluster, and nowhere near either rail stack.
        //
        // 18mm deep at the rear, leaving ~33mm at the front for the I2C run
        // from the knob cluster up to the Matrix Portal, which sits above the
        // display centreline.

        const braceTopY = -definition.apertureH / 2 - 0.5 * millimeter;
        const braceBotY = braceTopY - t;
        // Starts at the same depth as rail C's mortise, and for the same
        // reason: at zBack + t its own mortise left a 3mm sliver at the rear
        // edge of each side wall.
        const stiffZ0 = railZ[2];
        const stiffZ1 = stiffZ0 + definition.webDepth;

        fCuboid(context, id + "stiff", {
                "corner1" : vector(left,  braceBotY - kerf / 2, stiffZ0),
                "corner2" : vector(right, braceTopY + kerf / 2, stiffZ1) });

        const stiffSides = ["wallL", "wallR"];
        for (var w = 0; w < 2; w += 1)
        {
            fCuboid(context, id + ("stmort" ~ w), {
                    "corner1" : vector(left - over,  braceBotY + kerf / 2, stiffZ0 + kerf / 2),
                    "corner2" : vector(right + over, braceTopY - kerf / 2, stiffZ1 - kerf / 2) });
            opBoolean(context, id + ("stmortCut" ~ w), {
                    "tools"         : qCreatedBy(id + ("stmort" ~ w), EntityType.BODY),
                    "targets"       : qCreatedBy(id + stiffSides[w], EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
        }

        // PSU mounting clearance through the BOTTOM wall. Its side-face holes
        // are 10 and 84 from one end of a 99.24mm case — 2.5mm off centre, so
        // these are not symmetric either. Screw path is 3mm wall + a
        // psuStandoff spacer + up to 5mm of thread, i.e. M3x12.
        // Datum is the TERMINAL end. Both views on the spec sheet dimension
        // from it, and the terminals have to face +x toward the IEC inlet or
        // the mains run crosses the whole box — so these come off the HIGH-x
        // end. That matters because the pair is centred 2.62mm off the case
        // centre; referencing the wrong end puts them 5.24mm out.
        var psuHoles = [];
        const psuXHi = definition.psuX + definition.psuL / 2;
        const psuHoleXs = [psuXHi - definition.psuHoleBX, psuXHi - definition.psuHoleAX];
        // The two side holes ARE collinear — confirmed on the part — and they
        // are threaded M3, so ordinary M3 hardware bolts straight in and no
        // slot or insert is needed. One shared height.
        for (var ph = 0; ph < 2; ph += 1)
        {
            fCylinder(context, id + ("psuh" ~ ph), {
                    "topCenter"    : vector(psuHoleXs[ph], bottom + t + over, definition.psuZFront - definition.psuHoleZ),
                    "bottomCenter" : vector(psuHoleXs[ph], bottom - over,     definition.psuZFront - definition.psuHoleZ),
                    "radius"       : definition.psuHoleDia / 2 - kerf / 2 });
            psuHoles = append(psuHoles, qCreatedBy(id + ("psuh" ~ ph), EntityType.BODY));
        }
        opBoolean(context, id + "psuHoleCut", {
                "tools"         : qUnion(psuHoles),
                "targets"       : qCreatedBy(id + "wallB", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // ── IEC inlet, bottom wall ──────────────────────────────────────
        // In the bottom wall, at the +x end so it lands beside the PSU's
        // terminals and the mains run stays short — which matters more now
        // that a barrier is not doing the containing.
        //
        // The bottom wall rather than the right-hand one because portrait
        // is the orientation this lives in, and portrait rests on a +/-x
        // wall. See the iecProxy header for the full argument.

        var iecTools = [];

        fCuboid(context, id + "iecCut", {
                "corner1" : vector(definition.iecX - definition.iecCutW / 2 + kerf / 2,
                                   bottom - over,
                                   definition.iecZ - definition.iecCutH / 2 + kerf / 2),
                "corner2" : vector(definition.iecX + definition.iecCutW / 2 - kerf / 2,
                                   bottom + t + over,
                                   definition.iecZ + definition.iecCutH / 2 - kerf / 2) });
        iecTools = append(iecTools, qCreatedBy(id + "iecCut", EntityType.BODY));

        // Flange screws, on the SHORT axis. That is what made the listing's
        // 40mm look impossible: 40mm cannot straddle the 46.75mm cutout, but
        // it straddles the 27.25mm one comfortably. The hole sits in the
        // triangular lobe, so the spacing is cutH + tip if it is at the
        // lobe's mid-height. Confirm by measuring hole centre to hole centre;
        // it is one variable either way.
        for (var us = 0; us < 2; us += 1)
        {
            var uz = definition.iecZ - definition.iecScrewSpacing / 2;
            if (us == 1)
            {
                uz = definition.iecZ + definition.iecScrewSpacing / 2;
            }
            fCylinder(context, id + ("iecScrew" ~ us), {
                    "topCenter"    : vector(definition.iecX, bottom - over,     uz),
                    "bottomCenter" : vector(definition.iecX, bottom + t + over, uz),
                    "radius"       : definition.iecScrewDia / 2 - kerf / 2 });
            iecTools = append(iecTools, qCreatedBy(id + ("iecScrew" ~ us), EntityType.BODY));
        }

        opBoolean(context, id + "iecCutOp", {
                "tools"         : qUnion(iecTools),
                "targets"       : qCreatedBy(id + "wallB", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        opBoolean(context, id + "coverCut", {
                "tools"         : qUnion(coverHoles),
                "targets"       : qCreatedBy(id + "backCover", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // ── display aperture and knob bores, through every lamination ───
        var tools = [];

        fCuboid(context, id + "apTool", {
                "corner1" : vector(-definition.apertureW / 2, -definition.apertureH / 2, zBezB - over),
                "corner2" : vector( definition.apertureW / 2,  definition.apertureH / 2, over) });
        tools = append(tools, qCreatedBy(id + "apTool", EntityType.BODY));

        // A 2-D cluster, not a row. Four knobs in a 2x2 block occupy 70mm of
        // band width against 160mm for a 1x4 — and that 90mm is exactly what
        // the IEC module needs, because it protrudes ~30mm behind its panel
        // and a full-width knob row left only 10mm beside the PSU.
        //
        // Index order is reading order: K1 top-left, K2 top-right, K3
        // bottom-left, K4 bottom-right. Upstream assigns fixed functions to
        // K1..K4 (brightness, network, knob values, pattern list), so write
        // this down next to the I2C addresses or the front panel will not
        // match its own documentation.
        const kCols = definition.knobCols;
        const kRows = floor((definition.knobCount + kCols - 1) / kCols);

        for (var i = 0; i < definition.knobCount; i += 1)
        {
            const kc = i % kCols;
            const kr = floor(i / kCols);
            const knobX = definition.knobXCentre
                        + (kc - (kCols - 1) / 2) * definition.knobPitch;
            const knobY = definition.knobYCentre
                        - (kr - (kRows - 1) / 2) * definition.knobPitch;
            fCylinder(context, id + ("bore" ~ i), {
                    "topCenter"    : vector(knobX, knobY, over),
                    "bottomCenter" : vector(knobX, knobY, zBezB - over),
                    "radius"       : definition.boreDia / 2 });
            tools = append(tools, qCreatedBy(id + ("bore" ~ i), EntityType.BODY));
        }

        opBoolean(context, id + "cut", {
                "tools"         : qUnion(tools),
                "targets"       : qUnion(plates),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // ── Part identity ──────────────────────────────────────────────
        // Until now every body was anonymous, which was fine while the only
        // consumer was a bounding-box query. It stops being fine the moment
        // anything downstream needs to refer to ONE part: an assembly
        // instance list, a BOM line, or a DXF file name. Naming here rather
        // than in the document keeps the repo the source of truth — rename a
        // body in Onshape and the next push silently reverts it.
        nameBody(context, id + "n01", id + "layer0",  "Bezel outer");
        nameBody(context, id + "n02", id + "layer1",  "Bezel inner");
        nameBody(context, id + "n03", id + "wallL",   "Wall left");
        nameBody(context, id + "n04", id + "wallR",   "Wall right");
        nameBody(context, id + "n05", id + "wallB",   "Wall bottom (IEC)");
        nameBody(context, id + "n06", id + "wallT",   "Wall top");
        nameBody(context, id + "n07", id + "backCover", "Back cover");
        nameBody(context, id + "n08", id + "stiff",   "Stiffener web");
        nameBody(context, id + "n09", id + "brace0",  "Panel brace lower");
        nameBody(context, id + "n10", id + "brace1",  "Panel brace upper");
        for (var ri = 0; ri < 2; ri += 1)
        {
            var where = "lower";
            if (ri == 1) { where = "upper"; }
            nameBody(context, id + ("nrA" ~ ri), id + ("railA" ~ ri),
                     "Rail A " ~ where ~ " (screw clearance)");
            nameBody(context, id + ("nrB" ~ ri), id + ("railB" ~ ri),
                     "Rail B " ~ where ~ " (hex pocket)");
            nameBody(context, id + ("nrC" ~ ri), id + ("railC" ~ ri),
                     "Rail C " ~ where ~ " (tenoned)");
        }

        // ── Mate connectors ────────────────────────────────────────────
        // Published so the ASSEMBLY can position real vendor parts against
        // the enclosure without re-deriving a single coordinate. Both sides
        // then read the same Variable Studio, which is what keeps "the box
        // follows the insides" true without in-context references.
        opMateConnector(context, id + "mcOrigin", {
                "coordSystem" : coordSystem(vector(0, 0, 0) * millimeter,
                                            vector(1, 0, 0), vector(0, 0, 1)),
                "owner"       : qCreatedBy(id + "layer0", EntityType.BODY) });

        for (var i = 0; i < definition.panelCount; i += 1)
        {
            const pcx = (i - (definition.panelCount - 1) / 2) * definition.panelW;
            opMateConnector(context, id + ("mcPanel" ~ i), {
                    "coordSystem" : coordSystem(vector(pcx, 0 * millimeter, 0 * millimeter),
                                                vector(1, 0, 0), vector(0, 0, 1)),
                    "owner"       : qCreatedBy(id + "layer0", EntityType.BODY) });
        }

        // PSU datum. Mean Well's STEP has its origin at the corner where the
        // TERMINAL end, the MOUNTING-HOLE face and the BASE meet, so this
        // connector maps that corner into our frame:
        //
        //   ours = (psuXHi - X,  psuYLo + Y,  psuZFront - Z)
        //
        // The z flip is the part that matters — it is what puts the cover,
        // and therefore the terminal screws, toward the removable back cover
        // rather than the glued bezel. Fasten the vendor part to this and the
        // orientation cannot be got wrong by hand.
        opMateConnector(context, id + "mcPsu", {
                "coordSystem" : coordSystem(vector(definition.psuX + definition.psuL / 2,
                                                   bottom + t + definition.psuStandoff,
                                                   definition.psuZFront),
                                            vector(-1, 0, 0), vector(0, 0, -1)),
                "owner"       : qCreatedBy(id + "wallB", EntityType.BODY) });

        opMateConnector(context, id + "mcIec", {
                "coordSystem" : coordSystem(vector(definition.iecX, bottom, definition.iecZ),
                                            vector(1, 0, 0), vector(0, -1, 0)),
                "owner"       : qCreatedBy(id + "wallB", EntityType.BODY) });
    });
