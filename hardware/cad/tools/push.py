#!/usr/bin/env python3
"""Upload enclosure.fs and UPDATE the five features in place.

The old shell version deleted every feature and re-added it. That works, but
it briefly destroys every part in the studio, and any assembly instance
referencing those parts comes back with partId:"" - a dead instance that
still shows its old name and renders nothing. Updating in place keeps part
identity, so the assembly survives a push.
"""
import json,subprocess,sys,time
DID="8cfb8d4f799392c05f62f6ad"; WID="b5dfed0b24d2121a79e8b1a8"
PS="06ba580a80083894ed24609b"; FSEID="3c1a0a201f41714feba73536"
API="https://cad.onshape.com/api/v10"
F="/home/jof/src/patternflow/hardware/cad/featurescript/enclosure.fs"
S="/home/jof/.claude/jobs/5315265f/tmp"

def curl(method,url,body=None,out=None):
    cmd=["curl","-s","--netrc","-X",method]
    if body is not None:
        open(f"{S}/_p.json","w").write(json.dumps(body))
        cmd+=["-H","Content-Type: application/json","--data-binary",f"@{S}/_p.json"]
    cmd.append(url)
    r=subprocess.run(cmd,capture_output=True).stdout
    return r

src=open(F).read()
for i in range(5):
    curl("POST",f"{API}/featurestudios/d/{DID}/w/{WID}/e/{FSEID}",{"contents":src})
    if json.loads(curl("GET",f"{API}/featurestudios/d/{DID}/w/{WID}/e/{FSEID}"))["contents"]==src:
        print("studio matches local"); break
    time.sleep(6)
else:
    sys.exit("STUDIO DOES NOT MATCH LOCAL")

specs=json.loads(curl("GET",f"{API}/featurestudios/d/{DID}/w/{WID}/e/{FSEID}/featurespecs")).get("featureSpecs",[])
print("specs:",len(specs))
assert len(specs)==5, "COMPILE FAILED"
NS=specs[0]["namespace"]

WANT=json.load(open(f"{S}/featuredefs.json"))
base=f"{API}/partstudios/d/{DID}/w/{WID}/e/{PS}/features"
have={f["featureType"]:f["featureId"] for f in json.loads(curl("GET",base)).get("features",[])}

for ft,(nm,params) in WANT.items():
    feat={"btType":"BTMFeature-134","featureType":ft,"name":nm,"namespace":NS,
          "parameters":[{"btType":"BTMParameterQuantity-147","parameterId":k,"expression":v}
                        if isinstance(v,str) else
                        {"btType":"BTMParameterBoolean-144","parameterId":k,"value":v}
                        for k,v in params]}
    if ft in have:
        feat["featureId"]=have[ft]
        r=curl("POST",f"{base}/featureid/{have[ft]}",{"feature":feat}); verb="update"
    else:
        r=curl("POST",base,{"feature":feat}); verb="add"
    d=json.loads(r); st=(d.get("featureState") or {}).get("featureStatus")
    print(f"  {verb:6} {nm:20} -> {st or ('ERR: '+str(d.get('message'))[:160])}")
