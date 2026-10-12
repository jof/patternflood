#!/usr/bin/env python3
"""Upload enclosure.fs and UPDATE the five features in place.

Also refreshes the standalone proxy instances (panel, PSU, IEC) in the proxy
Part Studios, which would otherwise keep the old parameter list and quietly
fall back to defaults for anything new — or, when a parameter is renamed,
fail outright.

The old shell version deleted every feature and re-added it. That works, but
it briefly destroys every part in the studio, and any assembly instance
referencing those parts comes back with partId:"" - a dead instance that
still shows its old name and renders nothing. Updating in place keeps part
identity, so the assembly survives a push.
"""
import json,os,re,subprocess,sys,tempfile,time
DID="8cfb8d4f799392c05f62f6ad"; WID="b5dfed0b24d2121a79e8b1a8"
PS="06ba580a80083894ed24609b"; FSEID="3c1a0a201f41714feba73536"
API="https://cad.onshape.com/api/v10"
HERE=os.path.dirname(os.path.abspath(__file__))
F=os.path.join(HERE,"..","featurescript","enclosure.fs")
DEFS=os.path.join(HERE,"featuredefs.json")
S=tempfile.mkdtemp(prefix="pfpush-")
# Proxy studios that instance the same features standalone. Every feature in
# them whose type is pushed here is refreshed with the same parameters; panel
# proxies are forced to a single 1 x 1 panel.
PROXY_STUDIOS={"9aacde0e7a6103be9fff46fd":"Panel P2 (proxy)",
               "d1c871ec149418978f2eb283":"Proxies (view only)",
               "f9604c88ee037028910ba08a":"IEC AC-14-F16A (proxy)"}

def curl(method,url,body=None,out=None):
    cmd=["curl","-s","--netrc","-X",method]
    if body is not None:
        open(f"{S}/_p.json","w").write(json.dumps(body))
        cmd+=["-H","Content-Type: application/json","--data-binary",f"@{S}/_p.json"]
    cmd.append(url)
    r=subprocess.run(cmd,capture_output=True).stdout
    return r

# Onshape re-pins document imports (`NS::import(path : "<element>", version :
# "<microversion>")`) to the target's latest microversion on save, so compare
# with those versions masked, then adopt the server's pin locally.
IMPORT_PIN=re.compile(r'(::import\(path : "[0-9a-f]{24}", version : ")([0-9a-f]{24})(")')
def unpinned(t): return IMPORT_PIN.sub(r"\1-\3",t)

src=open(F).read()
for i in range(5):
    curl("POST",f"{API}/featurestudios/d/{DID}/w/{WID}/e/{FSEID}",{"contents":src})
    remote=json.loads(curl("GET",f"{API}/featurestudios/d/{DID}/w/{WID}/e/{FSEID}"))["contents"]
    if unpinned(remote)==unpinned(src):
        if remote!=src:
            open(F,"w").write(remote)
            print("studio matches local (import re-pinned by Onshape; local updated)")
        else:
            print("studio matches local")
        break
    time.sleep(6)
else:
    sys.exit("STUDIO DOES NOT MATCH LOCAL")

specs=json.loads(curl("GET",f"{API}/featurestudios/d/{DID}/w/{WID}/e/{FSEID}/featurespecs")).get("featureSpecs",[])
print("specs:",len(specs))
assert len(specs)==5, "COMPILE FAILED"
NS=specs[0]["namespace"]

WANT=json.load(open(DEFS))
base=f"{API}/partstudios/d/{DID}/w/{WID}/e/{PS}/features"
have={f["featureType"]:f["featureId"] for f in json.loads(curl("GET",base)).get("features",[])}

def mkfeat(ft,nm,params):
    return {"btType":"BTMFeature-134","featureType":ft,"name":nm,"namespace":NS,
            "parameters":[{"btType":"BTMParameterQuantity-147","parameterId":k,"expression":v}
                          if isinstance(v,str) else
                          {"btType":"BTMParameterBoolean-144","parameterId":k,"value":v}
                          for k,v in params]}

def report(verb,nm,r):
    d=json.loads(r); st=(d.get("featureState") or {}).get("featureStatus")
    print(f"  {verb:6} {nm:20} -> {st or ('ERR: '+str(d.get('message'))[:160])}")

for ft,(nm,params) in WANT.items():
    feat=mkfeat(ft,nm,params)
    if ft in have:
        feat["featureId"]=have[ft]
        r=curl("POST",f"{base}/featureid/{have[ft]}",{"feature":feat}); verb="update"
    else:
        r=curl("POST",base,{"feature":feat}); verb="add"
    report(verb,nm,r)

for eid,label in PROXY_STUDIOS.items():
    pbase=f"{API}/partstudios/d/{DID}/w/{WID}/e/{eid}/features"
    for f in json.loads(curl("GET",pbase)).get("features",[]):
        ft=f.get("featureType")
        if ft not in WANT: continue
        params=WANT[ft][1]
        if ft=="panelProxy":
            params=[(k,"1" if k in ("cols","rows") else v) for k,v in params]
        feat=mkfeat(ft,f["name"],params); feat["featureId"]=f["featureId"]
        report("update",f"{label[:12]}/{f['name']}"[:20],
               curl("POST",f"{pbase}/featureid/{f['featureId']}",{"feature":feat}))
