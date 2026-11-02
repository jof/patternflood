#!/usr/bin/env python3
"""Check the rev 3 audio parts (AUD_* in enclosure.fs) against every other body.

    hardware/cad/tools/audio_fit.py w/<workspace id>     (or v/<version id>)

Read-only: one FeatureScript eval over REST (onshape_http.py, like push.py).
For the exciter, the mic jack and its screws, and the line out and its nut, it
lists every body within 10 mm and the distance to it, leaving out the wall each
mounts in and the bezel the exciter is glued to. Then it checks the cuts are
there: the inner bezel open at the exciter, the doubler notched at the line out
and holed at the mic jack. Anything under 0.05 mm is flagged as a clash.
"""
import json, sys
import onshape_http

API = "https://cad.onshape.com/api/v10"
DID, PS = "8cfb8d4f799392c05f62f6ad", "06ba580a80083894ed24609b"
WVM = sys.argv[1]

FS = r'''
function(context is Context, queries)
{
    const mm = millimeter;
    const audio = ["Exciter.*", "Mic jack.*", "Line out.*", "Nut — line out.*", "Screw M3 x 10 — mic jack.*"];
    // what each one is meant to touch: the wall it mounts in, the bezel it is glued to
    const ok = ["Wall right.*", "Bezel.*"];
    var all = evaluateQuery(context, qBodyType(qEverything(EntityType.BODY), BodyType.SOLID));
    var names = [];
    for (var b in all)
    {
        var nm = getProperty(context, { "entity" : b, "propertyType" : PropertyType.NAME });
        names = append(names, nm == undefined ? "?" : nm);
    }
    const isAny = function(nm, pats) returns boolean
        {
            for (var p in pats) { if (match(nm, p).hasMatch) { return true; } }
            return false;
        };
    var out = [];
    for (var i = 0; i < size(all); i += 1)
    {
        if (!isAny(names[i], audio)) { continue; }
        const bb = evBox3d(context, { "topology" : all[i] });
        var near = [];
        for (var j = 0; j < size(all); j += 1)
        {
            if (j == i || isAny(names[j], audio) || isAny(names[j], ok)) { continue; }
            const d = evDistance(context, { "side0" : all[i], "side1" : all[j] }).distance / mm;
            if (d < 10) { near = append(near, [d, names[j]]); }
        }
        out = append(out, [names[i], [bb.minCorner[0] / mm, bb.minCorner[1] / mm, bb.minCorner[2] / mm],
                           [bb.maxCorner[0] / mm, bb.maxCorner[1] / mm, bb.maxCorner[2] / mm], near]);
    }
    // the pocket: is the inner bezel open at the exciter? (a point in the inner sheet's band)
    const p = vector(88, -150, -4.8) * mm;
    var inner = undefined;
    for (var i = 0; i < size(all); i += 1) { if (names[i] == "Bezel inner") { inner = all[i]; } }
    const dIn = evDistance(context, { "side0" : inner, "side1" : p }).distance / mm;
    // the doubler notch behind the line out, and the mic hole through the doubler
    var dbl = undefined;
    for (var i = 0; i < size(all); i += 1) { if (match(names[i], "Wall right doubler.*").hasMatch) { dbl = all[i]; } }
    const dNotch = evDistance(context, { "side0" : dbl, "side1" : vector(141.7, -105, -36) * mm }).distance / mm;
    const dMic = evDistance(context, { "side0" : dbl, "side1" : vector(141.7, -70, -33) * mm }).distance / mm;
    return [out, dIn, dNotch, dMic];
}
'''


def plain(v):
    t = v.get("btType", "")
    if t.endswith("BTFSValueArray"):
        return [plain(x) for x in v["value"]]
    if t.endswith("BTFSValueMap"):
        return {plain(e["key"]): plain(e["value"]) for e in v["value"]}
    return v.get("value")


s, b = onshape_http.request("POST", f"{API}/partstudios/d/{DID}/{WVM}/e/{PS}/featurescript",
                            {"script": FS, "queries": {}})
d = json.loads(b)
if d.get("notices") or "result" not in d:
    sys.exit(json.dumps(d.get("notices", d), indent=1)[:3000])
out, dIn, dNotch, dMic = plain(d["result"])
for nm, lo, hi, near in out:
    print(f"{nm}\n    x {lo[0]:.1f}..{hi[0]:.1f}  y {lo[1]:.1f}..{hi[1]:.1f}  z {lo[2]:.1f}..{hi[2]:.1f}")
    for dist, other in sorted(near)[:5]:
        print(f"    {dist:6.2f} mm  {other}" + ("   <-- CLASH" if dist < 0.05 else ""))
    if not near:
        print("    nothing within 10 mm")
print(f"pocket: inner bezel is {dIn:.2f} mm from a point in its band at the exciter (> 0 means cut away)")
print(f"line-out notch: doubler is {dNotch:.2f} mm from the jack's axis inside it (> 0 means notched)")
print(f"mic hole: doubler is {dMic:.2f} mm from the jack's axis inside it (~11.9 means the hole is there)")
