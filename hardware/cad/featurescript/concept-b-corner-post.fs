FeatureScript 3070;
import(path : "onshape/std/geometry.fs", version : "3070.0");

/**
 * CONCEPT B — laminated corner post, glueless.
 *
 * A study model, not part of the enclosure. It draws ONE corner of the
 * desktop box at full scale, on the same datum as enclosure.fs, so the
 * dimensions can be read straight across:
 *
 *   z = 0        LED panel front face      x = 0, y = 0   display centre
 *   side wall    x  145 .. 148             bottom wall    y -160 .. -157
 *
 * WHY THIS SHAPE — three rules, each forced by 3 mm sheet:
 *
 *  1. A laser only drills along a sheet's normal, so a bolt joining two
 *     parts must be normal to BOTH: you can only ever bolt PARALLEL plates.
 *     A corner between perpendicular walls therefore needs an intermediary
 *     that is parallel to one of them. That intermediary is the post.
 *
 *  2. The post is parallel to the side wall, so the side wall bolts to it.
 *     The bottom wall is perpendicular to it and can never be bolted to it,
 *     so that end is a through-tenon locked with a tusk key — an interlock,
 *     not a fastener.
 *
 *  3. The post's laminations are through-bolted with plain nuts on the
 *     inboard face rather than captive nuts in pockets. A captive nut needs
 *     its 5.5 mm across-flats to lie IN the sheet plane, which costs a whole
 *     lamination per nut and only ties the plates either side of it. One
 *     long bolt ties every lamination at once and needs no pocket.
 *
 * Source of truth is the repo:
 *   hardware/cad/featurescript/concept-b-corner-post.fs
 */

const ANY_LENGTH_BOUNDS = { (millimeter) : [-2000, 0, 2000] } as LengthBoundSpec;

// Hex prism with its axis along X — the enclosure's hexPrism() is Z-axis.
function hexPrismX(context is Context, id is Id, cy is ValueWithUnits, cz is ValueWithUnits,
                   af is ValueWithUnits, x0 is ValueWithUnits, x1 is ValueWithUnits) returns Query
{
    const reach = af * 1.5;
    var slabs = [];

    for (var i = 0; i < 3; i += 1)
    {
        fCuboid(context, id + ("slab" ~ i), {
                "corner1" : vector(x0, cy - af / 2, cz - reach),
                "corner2" : vector(x1, cy + af / 2, cz + reach) });

        if (i > 0)
        {
            opTransform(context, id + ("rot" ~ i), {
                    "bodies"    : qCreatedBy(id + ("slab" ~ i), EntityType.BODY),
                    "transform" : rotationAround(line(vector(x0, cy, cz), vector(1, 0, 0)),
                                                 i * 60 * degree) });
        }
        slabs = append(slabs, qCreatedBy(id + ("slab" ~ i), EntityType.BODY));
    }

    opBoolean(context, id + "hex", {
            "tools"         : qUnion(slabs),
            "operationType" : BooleanOperationType.INTERSECTION });

    return qCreatedBy(id, EntityType.BODY);
}

annotation { "Feature Type Name" : "Corner post concept" }
export const cornerPostDemo = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Sheet thickness" }
        isLength(definition.t, LENGTH_BOUNDS);

        annotation { "Name" : "Post laminations" }
        isInteger(definition.postLayers, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Tenon laminations" }
        isInteger(definition.tenonLayers, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Post width (z)" }
        isLength(definition.postW, LENGTH_BOUNDS);

        annotation { "Name" : "Tenon width (z)" }
        isLength(definition.tenonW, LENGTH_BOUNDS);

        annotation { "Name" : "Tenon protrusion" }
        isLength(definition.tenonOut, LENGTH_BOUNDS);

        annotation { "Name" : "Key thickness" }
        isLength(definition.keyT, LENGTH_BOUNDS);

        annotation { "Name" : "Key height" }
        isLength(definition.keyH, LENGTH_BOUNDS);

        annotation { "Name" : "Key draw" }
        isLength(definition.keyDraw, LENGTH_BOUNDS);

        annotation { "Name" : "Bolt clearance dia" }
        isLength(definition.boltDia, LENGTH_BOUNDS);

        annotation { "Name" : "Bolts in the fragment" }
        isInteger(definition.boltCount, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Nut across flats" }
        isLength(definition.nutAF, LENGTH_BOUNDS);

        annotation { "Name" : "Washer diameter" }
        isLength(definition.washerDia, LENGTH_BOUNDS);

        annotation { "Name" : "Side wall inner face x" }
        isLength(definition.xIn, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Bottom wall inner face y" }
        isLength(definition.yIn, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Post front z" }
        isLength(definition.zF, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Wall fragment span" }
        isLength(definition.frag, LENGTH_BOUNDS);

        annotation { "Name" : "Wall front z" }
        isLength(definition.zWallF, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Wall back z" }
        isLength(definition.zWallB, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Corner fingers" }
        isInteger(definition.fingers, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Show hardware" }
        definition.showHW is boolean;
    }
    {
        const t    = definition.t;
        const over = 1 * millimeter;

        const xIn  = definition.xIn;                             // side wall inner face
        const xOut = xIn + t;                                    // side wall outer face
        const yIn  = definition.yIn;                             // bottom wall inner face
        const yOut = yIn - t;                                    // bottom wall outer face

        const xP0  = xIn - definition.postLayers * t;            // post inboard face
        const xT1  = xP0 + definition.tenonLayers * t;           // tenon outboard face

        const zF   = definition.zF;
        const zB   = zF - definition.postW;
        const zTF  = zF - (definition.postW - definition.tenonW) / 2;
        const zTB  = zTF - definition.tenonW;

        const yTop = yIn + definition.frag;                      // fragment cut line
        const xLo  = xIn - definition.frag;
        const yTen = yOut - definition.tenonOut;                 // tenon tip

        // ── walls ──────────────────────────────────────────────────────
        fCuboid(context, id + "wallS", {
                "corner1" : vector(xIn,  yOut, definition.zWallB),
                "corner2" : vector(xOut, yTop, definition.zWallF) });

        fCuboid(context, id + "wallB", {
                "corner1" : vector(xLo,  yOut, definition.zWallB),
                "corner2" : vector(xOut, yIn,  definition.zWallF) });

        // Corner finger joint, fingers running along z through the prism
        // where the two walls overlap. Even slices leave the side wall,
        // odd slices leave the bottom wall.
        const n    = definition.fingers;
        const step = (definition.zWallF - definition.zWallB) / n;
        for (var i = 0; i < n; i += 1)
        {
            const za = definition.zWallB + i * step;
            fCuboid(context, id + ("fg" ~ i), {
                    "corner1" : vector(xIn - over, yOut - over, za),
                    "corner2" : vector(xOut + over, yIn + over, za + step) });

            var victim = id + "wallS";
            if (i % 2 == 1) { victim = id + "wallB"; }

            opBoolean(context, id + ("fgCut" ~ i), {
                    "tools"         : qCreatedBy(id + ("fg" ~ i), EntityType.BODY),
                    "targets"       : qCreatedBy(victim, EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
        }

        // ── post laminations ───────────────────────────────────────────
        // Plate 0 is the inboard one. The tenon is made from the INBOARD
        // plates so its mortise lands 3t from the bottom wall's own edge —
        // enclosure-lasercut.md §7b, the rule that moved the rear rails.
        var plates = [];
        for (var i = 0; i < definition.postLayers; i += 1)
        {
            const xa = xP0 + i * t;
            fCuboid(context, id + ("pl" ~ i), {
                    "corner1" : vector(xa,     yIn,  zB),
                    "corner2" : vector(xa + t, yTop, zF) });

            if (i < definition.tenonLayers)
            {
                fCuboid(context, id + ("tn" ~ i), {
                        "corner1" : vector(xa,     yTen, zTB),
                        "corner2" : vector(xa + t, yIn,  zTF) });
                opBoolean(context, id + ("tnJoin" ~ i), {
                        "tools"         : qUnion([qCreatedBy(id + ("pl" ~ i), EntityType.BODY),
                                                  qCreatedBy(id + ("tn" ~ i), EntityType.BODY)]),
                        "operationType" : BooleanOperationType.UNION });
            }
            plates = append(plates, qCreatedBy(id + ("pl" ~ i), EntityType.BODY));
        }

        // ── mortise through the bottom wall ────────────────────────────
        fCuboid(context, id + "mort", {
                "corner1" : vector(xP0, yOut - over, zTB),
                "corner2" : vector(xT1, yIn + over,  zTF) });
        opBoolean(context, id + "mortCut", {
                "tools"         : qCreatedBy(id + "mort", EntityType.BODY),
                "targets"       : qCreatedBy(id + "wallB", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // ── tusk key slot ──────────────────────────────────────────────
        // The slot's upper edge sits keyDraw BELOW the wall's outer face, so
        // the key wedges between the wall and the slot's lower edge and pulls
        // the post's shoulder up tight. That is the whole mechanism.
        const zKeyC = (zTF + zTB) / 2;
        const ySlotHi = yOut - definition.keyDraw;
        const ySlotLo = ySlotHi - definition.keyH;

        fCuboid(context, id + "keySlot", {
                "corner1" : vector(xP0 - over, ySlotLo, zKeyC - definition.keyT / 2),
                "corner2" : vector(xT1 + over, ySlotHi, zKeyC + definition.keyT / 2) });
        opBoolean(context, id + "keySlotCut", {
                "tools"         : qCreatedBy(id + "keySlot", EntityType.BODY),
                "targets"       : qUnion(plates),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // ── the key itself: a trapezoid, thin end leading ──────────────
        const xK0 = xP0 - 10 * millimeter;          // leading (thin) end, inboard
        const xK1 = xIn;                            // trailing (thick) end
        var sk = newSketchOnPlane(context, id + "keySk", {
                "sketchPlane" : plane(vector(0 * millimeter, 0 * millimeter,
                                             zKeyC - definition.keyT / 2),
                                      vector(0, 0, 1), vector(1, 0, 0)) });
        skPolyline(sk, "kp", {
                "points" : [vector(xK0, yOut),
                            vector(xK1, yOut),
                            vector(xK1, yOut - definition.keyH - 2 * definition.keyDraw),
                            vector(xK0, yOut - definition.keyH),
                            vector(xK0, yOut)] });
        skSolve(sk);
        opExtrude(context, id + "keyEx", {
                "entities"  : qSketchRegion(id + "keySk", false),
                "direction" : vector(0, 0, 1),
                "endBound"  : BoundingType.BLIND,
                "endDepth"  : definition.keyT });

        // ── through-bolts, side wall into the post ─────────────────────
        // Plain nut on the inboard face, not a captive nut: one bolt then
        // clamps every lamination, and no lamination is spent on a pocket.
        const zBolt = (zF + zB) / 2;
        var hw = [];
        for (var j = 0; j < definition.boltCount; j += 1)
        {
            const yb = yIn + definition.frag * (j + 1) / (definition.boltCount + 1);

            fCylinder(context, id + ("bh" ~ j), {
                    "topCenter"    : vector(xOut + over, yb, zBolt),
                    "bottomCenter" : vector(xP0 - over,  yb, zBolt),
                    "radius"       : definition.boltDia / 2 });
            opBoolean(context, id + ("bhCut" ~ j), {
                    "tools"         : qCreatedBy(id + ("bh" ~ j), EntityType.BODY),
                    "targets"       : qUnion(concatenateArrays([plates,
                                             [qCreatedBy(id + "wallS", EntityType.BODY)]])),
                    "operationType" : BooleanOperationType.SUBTRACTION });

            if (definition.showHW)
            {
                fCylinder(context, id + ("head" ~ j), {          // button head
                        "topCenter"    : vector(xOut + 1.6 * millimeter, yb, zBolt),
                        "bottomCenter" : vector(xOut, yb, zBolt),
                        "radius"       : 2.75 * millimeter });
                fCylinder(context, id + ("shank" ~ j), {
                        "topCenter"    : vector(xOut, yb, zBolt),
                        "bottomCenter" : vector(xP0 - 4.2 * millimeter, yb, zBolt),
                        "radius"       : 1.5 * millimeter });
                fCylinder(context, id + ("wash" ~ j), {
                        "topCenter"    : vector(xP0, yb, zBolt),
                        "bottomCenter" : vector(xP0 - 0.8 * millimeter, yb, zBolt),
                        "radius"       : definition.washerDia / 2 });
                hexPrismX(context, id + ("nut" ~ j),
                          yb, zBolt, definition.nutAF,
                          xP0 - 3.2 * millimeter, xP0 - 0.8 * millimeter);

                fCylinder(context, id + ("washHole" ~ j), {
                        "topCenter"    : vector(xP0 + over, yb, zBolt),
                        "bottomCenter" : vector(xP0 - 0.8 * millimeter - over, yb, zBolt),
                        "radius"       : 1.7 * millimeter });
                opBoolean(context, id + ("washDrill" ~ j), {
                        "tools"         : qCreatedBy(id + ("washHole" ~ j), EntityType.BODY),
                        "targets"       : qCreatedBy(id + ("wash" ~ j), EntityType.BODY),
                        "operationType" : BooleanOperationType.SUBTRACTION });
            }
        }
    });
