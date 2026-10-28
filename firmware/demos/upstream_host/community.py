#!/usr/bin/env python3
"""Build Patternflow's community patterns (community.patternflow.work) into host libraries.

The community wall's patterns are JavaScript, and most also carry a firmware header:
the author's own, or a port someone verified on hardware. Where there's a header, that's
what we run. Each is compiled, unchanged but for a few mechanical fixups, into its own
small shared library with build.py's C API (pfd/upstream.py drives both), against our
shim and the portable cores of upstream's main branch, which the community builds
against. The JavaScript-only ones run under node, in upstream's own harness, sandboxed
with no network (jsrun.mjs, node_argv()).

    ./community.py sync              # the wall's public patterns, headers and scripts; upstream's cores and harness
    ./community.py build             # compile what's new, in parallel (the controller does this on start)
    ./community.py check             # on ash: run each through a scripted player -> src/checks.json
    ./community.py sheet /tmp/cs     # contact sheets of the check's frames, to judge the canvas by eye
    ./community.py strip /tmp/cs --only ID   # one pattern's versions over time, to judge a port
    ./community.py twin /tmp/tw      # our originals: the script and its header side by side, and how far apart

One library per pattern: names collide between authors, a header that doesn't compile
costs only itself, and a re-sync compiles only what changed. They're built with hidden
visibility and no GNU-unique symbols, so each keeps its own canvas in one process.

Canvas: each pattern runs at the size it was written for, centred in the square. One
that calls PFCanvas::setFrame (all of them portrait, 64 x 128) is built for 128 x 128,
and the shim centres its frame. The rest were written for upstream's 128 x 64, and are
built at that size and letterboxed.

The patterns are CC BY-SA 4.0, their authors'. They're fetched into build/ and aren't
copied into this repository. Our 128 x 128 ports (community_ports/) are derivatives, each
crediting its original and CC BY-SA 4.0 too; community_review.json is ours.

Our own patterns for the wall are in originals/: each a script for Pattern Lab and a header
written as its twin (the device runs the header), CC BY-SA 4.0. They're built as the wall's are,
as written and at 128 x 128, and lead both community shelves. `twin` checks the pair still agree.
"""
import argparse
import fcntl
import functools
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build import c_str, host_api      # noqa: E402

API = "https://community.patternflow.work/api/community"
GITHUB = "engmung/patternflow"
CORES = ["src/core_math.h", "src/core_color.h", "src/core_noise.h", "src/core_tables.h", "src/core_mem.h",
         "src/core_params.h", "abi/pf_params.h"]
WEB = ["shared/constants", "pattern/controls", "pattern/knobs", "pattern/matrix", "pattern/harness", "pattern/ramp",
       "community/knobs"]           # web/src/lib/<module>.ts, as jsrun.mjs bundles them
CACHE = HERE / "build" / "community"
SRC, LIB, CHECK = CACHE / "src", CACHE / "lib", CACHE / "check"
SHIMS = [HERE / "community_shim", HERE / "shim"]
FLAGS = ["-std=c++17", "-w", "-fvisibility=hidden", "-fvisibility-inlines-hidden", "-fno-gnu-unique"]
SQUARE, WIDE = (128, 128), (128, 64)
CHECK_FRAMES = 660
# The frames each check keeps: idle at 0.5 s and 1.5 s (the sheet's), then with the knobs at work.
SHOTS = (30, 90, 200, 330, 450, 600)
SHEET_SHOT = 1
PORTS = HERE / "community_ports"            # our enlarged ports: CC BY-SA, each crediting its original
REVIEW = HERE / "community_review.json"     # by eye: what the COMMUNITY shelf shows of each pattern
ORIGINALS = HERE / "originals"              # ours, for the wall: <name>.js and its twin <name>.h
ORIG_LIB = CACHE / "originals"
# Portrait games and scenes drawn on their side in 128 x 64 (up along +x, as upstream's canvas
# maps a 64 x 128 frame). pfd turns them a quarter anticlockwise to stand upright; by eye, 2026-10-27.
TURN = {"4dbf3bb506814fc3": "Breakout Arcade", "77de31bae37940c7": "Tetris", "6ada5c800c734f5c": "Space Invaders",
        "879b8d05250448ed": "Midsummer Sea", "d027a48e3eaf4995": "Firefly Hollow",
        "df7ca71df5c04d20": "RocketFlightPattern", "618c344307ae4593": "elephant_breath"}
# Of those, the ones whose 128 x 128 version lies on its side too (it fills the square, then turns).
BIG_TURN = {"879b8d05250448ed": "Midsummer Sea", "d027a48e3eaf4995": "Firefly Hollow"}
FRAME_CONST = re.compile(r"(constexpr\s+int\s+FRAME_[WH]\s*=\s*)\d+")

# Anyone can post to the wall, and a pattern runs as native code in the demo process. So a
# built library may import only what drawing needs: maths, memory, strings, and the C++
# runtime's own plumbing. Nothing that opens a file or a socket or starts a process gets
# through, however the source spells it. With no syscall instruction of its own, either,
# that's all a library can reach.
ALLOWED = re.compile(
    r"(a?(sin|cos|tan)h?|sincos|atan2|exp2?|expm1|log(2|10|1p)?|pow|sqrt|cbrt|hypot|fmod|remainder|floor|ceil|"
    r"l?l?round|l?l?rint|nearbyint|trunc|fabs|fmin|fmax|fdim|fma|copysign|ldexp|frexp|modf|erfc?|[lt]gamma)[fl]?"
    r"|(__)?(mem(set|cpy|move|cmp)|strn?(len|cmp|cpy|cat)|strchr|strstr|v?sn?printf)(_chk)?"
    r"|malloc|calloc|realloc|free|aligned_alloc|posix_memalign|rand|srand"
    r"|_Zn[wa]m|_Zd[la]Pv(m)?|_ZSt\d+__throw_\w+|__cxa_\w+|__gxx_personality_v0|_Unwind_Resume"
    r"|__stack_chk_fail|__gmon_start__|_ITM_\w+|__aarch64_\w+")
SYSCALL = re.compile(r"\t(syscall|sysenter|int\s+\$0x80|svc|hvc|smc)\b")


def fetch(url, tries=4):
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "patternflood"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception:
            if n == tries - 1:
                raise
            time.sleep(2 ** n)


def sync():
    """The public wall -> SRC: index.json, h/<id>.h, and upstream main's cores."""
    cards, offset = [], 0
    while True:
        page = json.loads(fetch(f"{API}/patterns?sort=old&size=44&offset={offset}"))
        cards += page["items"]
        offset += len(page["items"])
        if not page["items"] or offset >= page["total"]:
            break
    sha = json.loads(fetch(f"https://api.github.com/repos/{GITHUB}/commits/main"))["sha"]

    new = SRC.with_name("src.new")
    shutil.rmtree(new, ignore_errors=True)
    (new / "h").mkdir(parents=True)
    for rel in CORES:
        (new / "cores" / rel).parent.mkdir(parents=True, exist_ok=True)
        (new / "cores" / rel).write_bytes(fetch(f"https://raw.githubusercontent.com/{GITHUB}/{sha}/firmware/patternflow/{rel}"))
    for mod in WEB:                     # the Pattern Lab's harness, for the JavaScript-only patterns
        (new / "web" / f"{mod}.ts").parent.mkdir(parents=True, exist_ok=True)
        (new / "web" / f"{mod}.ts").write_bytes(fetch(f"https://raw.githubusercontent.com/{GITHUB}/{sha}/web/src/lib/{mod}.ts"))
    (new / "js").mkdir()
    patterns, js_only = [], []
    for c in cards:
        entry = {"id": c["id"], "title": c["title"].strip(), "author": c.get("displayUsername") or c.get("username") or "",
                 "likes": c.get("likeCount", 0), "created": c.get("createdAt")}
        if not c.get("hasCpp"):
            (new / "js" / f"{c['id']}.js").write_text(c["code"])
            js_only.append(entry)
            continue
        header = json.loads(fetch(f"{API}/patterns/{c['id']}/header"))
        (new / "h" / f"{c['id']}.h").write_text(header["codeCpp"])
        entry["ported_by"] = header.get("portedBy")
        patterns.append(entry)
        time.sleep(0.1)                 # a courtesy to the community's server
    if (SRC / "checks.json").exists():  # the last check still applies to headers that haven't changed
        shutil.copy(SRC / "checks.json", new / "checks.json")
    (new / "index.json").write_text(json.dumps({"synced": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                                "upstream": sha, "patterns": patterns, "js_only": js_only}, indent=1))
    r = subprocess.run(["node", str(HERE / "jsrun.mjs"), "bundle", str(new)], capture_output=True, text=True) \
        if shutil.which("node") else None
    if not r or r.returncode:           # it needs node >= 22.6 (to strip the TypeScript); the Pi's node runs the result
        print("no JavaScript-only patterns: couldn't bundle the harness" + (f"\n{r.stderr[-1000:]}" if r else " (no node)"))
    shutil.rmtree(SRC, ignore_errors=True)
    new.rename(SRC)
    print(f"{len(patterns)} patterns with headers, {len(js_only)} JavaScript only; upstream at {sha[:8]} -> {SRC}")


def fixup(text):
    """Mechanical repairs, so a header builds here as on the firmware -> (text, namespace) or (text, None)."""
    text = text.replace('"../src/', '"src/').replace('"../config.h"', '"config.h"').replace('"../abi/', '"abi/')
    m = re.search(r"^[ \t]*namespace[ \t]+([^{\n]+?)[ \t]*\{", text, re.M)
    if not m:
        return text, None
    ns = re.sub(r"\W+", "_", m.group(1)).strip("_")
    return text[:m.start(1)] + ns + text[m.end(1):], ns


# Ours, beyond upstream's API: hooks a header may define, which the firmware never calls.
# Each with its name, a quick test first: the patterns, starting \b, are tried at every character.
HOOKS = [("knobLights", re.compile(r"\bvoid\s+knobLights\s*\(\s*float\b"),       # knob light colours, 4 x RGB
          'extern "C" void pf_lights(float* out) {{ {ns}::knobLights(reinterpret_cast<float (*)[3]>(out)); }}'),
         ("hostAudio", re.compile(r"\bvoid\s+hostAudio\s*\(\s*const\s+float\b"),  # the beat tracker's view of the music
          'extern "C" void pf_audio(const float* in) {{ {ns}::hostAudio(in); }}')]


def unit(ns, author, text=""):
    """The translation unit around one header (included as pattern.h): build.py's C API over one entry,
    and the C side of any HOOKS the header's TEXT defines (pf_lights, pf_audio)."""
    lines = ["// Generated by community.py. Do not edit.",
             '#include "Arduino.h"',
             '#include "pf_module.h"',
             '#include "pattern.h"',
             "struct PFHostEntry {",
             "  const char* name; const char* author; const char* const* labels;",
             "  void (*setup)(); void (*update)(float, const InputFrame&); void (*draw)();",
             "};",
             "static const PFHostEntry ENTRIES[] = {",
             f"  {{{ns}::NAME, {c_str(author)}, {ns}::KNOB_LABELS, {ns}::setup, {ns}::update, {ns}::draw}},",
             "};",
             "#pragma GCC visibility push(default)"]
    lines += host_api()
    lines += [c.format(ns=ns) for name, pat, c in HOOKS if name in text and pat.search(text)]
    lines += ["#pragma GCC visibility pop", "", CHECK_MAIN]
    return "\n".join(lines) + "\n"


# A scripted player for the check: idle (the sheet's frame), then out to the knobs' extremes
# and back, fast spins, clicks, push-and-turn, and the audio edition, 60 frames each.
CHECK_MAIN = r"""#ifdef PF_HOST_CHECK
int main(int argc, char** argv) {
  int frames = atoi(argv[1]);
  char* shots = argv[2];               // "30,90,...": the frames to write out, in order
  int d[4]; uint8_t pressed[4], held[4], aon[4]; float aval[4];
  uint32_t seed = 1;
  pf_setup(0);
  for (int f = 0; f < frames; f++) {
    int phase = f < 120 ? 0 : 1 + (f - 120) / 60, t = (f - 120) % 60;
    for (int k = 0; k < 4; k++) {
      seed = seed * 1664525u + 1013904223u;
      d[k] = 0; pressed[k] = held[k] = aon[k] = 0; aval[k] = 0;
      switch (phase) {
        case 1: d[k] = 1; break;
        case 2: d[k] = 8; break;
        case 3: d[k] = -16; break;
        case 4: d[k] = -1; break;
        case 5: d[k] = (int)(seed >> 29) - 3; break;
        case 6: pressed[k] = (t % 15 == 0) && (t / 15 == k); held[k] = (t / 15 == k); break;
        case 7: held[k] = 1; pressed[k] = t == 0; d[k] = (t & 1) ? 2 : -1; break;
        case 8: aon[k] = 1; aval[k] = (seed >> 8) / 16777216.0f; break;
      }
    }
    const uint8_t* buf = pf_frame(0, 1 / 60.0f, d, pressed, held, f * 17u, aon, aval);
    if (*shots && f == atoi(shots)) {
      fwrite(buf, 1, (size_t)PANEL_RES_W * PANEL_RES_H * 3, stdout);
      while (*shots && *shots != ',') shots++;
      if (*shots) shots++;
    }
  }
  return 0;
}
#endif"""


def load_index(src=SRC):
    idx = json.loads((src / "index.json").read_text())
    checks = json.loads((src / "checks.json").read_text()) if (src / "checks.json").exists() else {}
    return idx, checks


def review():
    """{id: "auto" | "port" | "native"}: what the COMMUNITY shelf shows of each. Unreviewed is native."""
    data = json.loads(REVIEW.read_text()) if REVIEW.exists() else {}
    return {i: r["big"] for i, r in data.items()}


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def header_variants(entry, src=SRC):
    """A compiled pattern's versions -> {"native": spec, "big": spec or None}, a spec being
    {text, ns, size, sha[, port]}; or None if the header has no namespace to build."""
    raw = (src / "h" / f"{entry['id']}.h").read_text(encoding="utf-8", errors="replace")
    return _versions(raw, PORTS / f"{entry['id']}.h")


def _versions(raw, port):
    """header_variants for a header's text, and where a port of it would be."""
    text, ns = fixup(raw)
    if not ns:
        return None
    native = {"text": text, "ns": ns, "size": SQUARE if "setFrame" in text else WIDE, "sha": _sha(raw)}
    big = None
    if port.exists():                   # ours, enlarged by hand
        ptext, pns = fixup(port.read_text())
        big = {"text": ptext, "ns": pns, "size": SQUARE, "sha": _sha(ptext), "port": True}
    else:
        # The same code at 128 x 128, and a frame it declares grows to the square with the panel.
        btext = FRAME_CONST.sub(lambda m: m.group(1) + "128", text)
        big = {"text": btext, "ns": ns, "size": SQUARE, "sha": _sha(btext + "@128x128")}
    return {"native": native, "big": big}


def script_variants(entry, src=SRC):
    """A JavaScript-only pattern's versions -> {"native": spec, "big": spec}, a spec being {file, matrix, sha[, port]}."""
    file = src / "js" / f"{entry['id']}.js"
    code = file.read_text(errors="replace")
    port = PORTS / f"{entry['id']}.js"
    native = {"file": file, "matrix": None, "sha": _sha(code)}
    if port.exists():
        big = {"file": port, "matrix": None, "sha": _sha(port.read_text()), "port": True}
    else:                               # the same script, handed a 128 x 128 display
        big = {"file": file, "matrix": SQUARE, "sha": _sha(code + "@128x128")}
    return {"native": native, "big": big}


def original_entries():
    """Our originals -> [(entry, versions)], from originals/<name>.h: an entry as the index has them."""
    out = []
    for h in sorted(ORIGINALS.glob("*.h")):
        raw = h.read_text()
        title = re.search(r'\bNAME\s*=\s*"([^"]*)"', raw)
        e = {"id": h.stem, "title": title.group(1) if title else h.stem, "author": "Jonathan Lassoff", "likes": 0,
             "ported_by": None}
        vs = _versions(raw, ORIGINALS / "no-port")
        if vs and "hostAudio" in vs["big"]["text"]:
            # The Audio shelf's copy at 128 x 128: a library of its own, so it keeps its own state.
            atext = vs["big"]["text"] + "\n// The Audio shelf's copy.\n"
            vs["audio"] = dict(vs["big"], text=atext, sha=_sha(atext))
        if vs:
            out.append((e, vs))
    return out


def originals(lib=ORIG_LIB, log=print):
    """Build our originals, as written and at 128 x 128 -> [(entry, {"native": path, "big": path})]."""
    lib.mkdir(parents=True, exist_ok=True)
    out = []
    for e, vs in original_entries():
        paths = {}
        for name, spec in vs.items():
            path, why = release(e, spec, SRC, lib)
            if why:
                log(f"originals: {e['title']} ({name}) {why}")
            else:
                paths[name] = path
        if paths:
            out.append((e, paths))
    keep = {n for _, paths in out for p in paths.values() for n in (p.name, p.name + ".vetted")}
    for f in lib.iterdir():             # libraries of versions since edited, as build() prunes the wall's
        if f.name not in keep:
            shutil.rmtree(f) if f.is_dir() else f.unlink()
    return out


def runnable(entry, name, spec, checks):
    """False only if the last check of this very version found it unsafe or broken."""
    c = checks.get(entry["id"], {}).get(name)
    return not c or c.get("sha") != spec["sha"] or c.get("verdict") == "ok"


def _inputs_hash(text, tu, size, extra, src):
    h = hashlib.sha256()
    for part in (text, tu, repr((size, FLAGS, extra))):
        h.update(part.encode())
    for root in SHIMS + [src / "cores"]:
        for f in sorted(root.rglob("*.h")):
            h.update(f.read_bytes())
    return h.hexdigest()[:12]


def compile_one(entry, text, ns, size, out_dir, extra, src=SRC, exe=False):
    """Compile one pattern -> (path, None) or (None, error text). Cached by the hash of every input."""
    tu = unit(ns, entry["author"], text)
    w, h = size
    out = out_dir / f"{entry['id']}-{w}x{h}-{_inputs_hash(text, tu, size, extra, src)}{'' if exe else '.so'}"
    if out.exists():
        return out, None
    work = out_dir / f".{out.name}.d"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    (work / "pattern.h").write_text(text)
    (work / "unit.cpp").write_text(tu)
    incs = [a for d in [work, *SHIMS, src / "cores"] for a in ("-I", str(d))]
    cmd = ["g++", *FLAGS, *extra, f"-DPANEL_RES_W={w}", f"-DPANEL_RES_H={h}", *incs,
           "-o", str(work / "out"), str(work / "unit.cpp")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        shutil.rmtree(work, ignore_errors=True)
        return None, r.stderr
    _fsync(work / "out")                # else a power cut soon after can leave `out` named but empty
    (work / "out").rename(out)
    shutil.rmtree(work, ignore_errors=True)
    return out, None


def _fsync(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def vet(lib_path):
    """None if this library reaches no further than ALLOWED, else why not. A pass is remembered beside it."""
    ok = lib_path.with_name(lib_path.name + ".vetted")
    if ok.exists():
        return None
    nm = subprocess.run(["nm", "-D", "--undefined-only", str(lib_path)], capture_output=True, text=True)
    dis = subprocess.run(["objdump", "-d", str(lib_path)], capture_output=True, text=True)
    if nm.returncode or dis.returncode:
        return "can't inspect it: " + (nm.stderr or dis.stderr).strip()
    imports = {line.split()[-1].split("@")[0] for line in nm.stdout.splitlines() if line.strip()}
    bad = sorted(s for s in imports if not ALLOWED.fullmatch(s))
    if bad:
        return "imports " + ", ".join(bad[:6])
    if SYSCALL.search(dis.stdout):
        return "makes system calls of its own"
    ok.touch()
    return None


def release(entry, spec, src=SRC, lib=LIB):
    """A version's runnable library -> (path, None), or (None, why it won't run)."""
    path, err = compile_one(entry, spec["text"], spec["ns"], spec["size"], lib,
                            ["-O2", "-fPIC", "-shared", "-Wl,-Bsymbolic"], src)
    if err:
        return None, "doesn't build: " + _first_error(err)
    why = vet(path)
    return (path, None) if not why else (None, why)


def build(jobs=None, src=SRC, lib=LIB, log=print):
    """Compile every version that will run -> [(entry, {"native": path, "big": path})], in index order.
    A big version is built only where the review puts it on the COMMUNITY shelf."""
    idx, checks = load_index(src)
    chosen = review()
    lib.mkdir(parents=True, exist_ok=True)
    todo = []
    for e in idx["patterns"]:
        vs = header_variants(e, src)
        if not vs:
            log(f"community: skipping {e['title']} ({e['id']}): no namespace")
            continue
        for name, spec in vs.items():
            if not spec or (name == "big" and chosen.get(e["id"], "native") == "native"):
                continue
            if runnable(e, name, spec, checks):
                todo.append((e, name, spec))
            else:
                log(f"community: skipping {e['title']} ({e['id']}, {name}): the check found it unsafe")
    t0 = time.monotonic()

    def one(job):
        e, name, spec = job
        path, why = release(e, spec, src, lib)
        if why:
            log(f"community: {e['title']} ({e['id']}, {name}) {why}")
        return e, name, path

    built = list(ThreadPoolExecutor(jobs or os.cpu_count()).map(one, todo))
    keep = {n for _, _, p in built if p for n in (p.name, p.name + ".vetted")}
    for f in lib.iterdir():             # libraries of headers since replaced or removed, and refused ones
        if f.name not in keep:
            shutil.rmtree(f) if f.is_dir() else f.unlink()
    out = {}
    for e, name, path in built:
        if path:
            out.setdefault(e["id"], (e, {}))[1][name] = path
    n_big = sum("big" in paths for _, paths in out.values())
    log(f"community: {len(out)} of {len(idx['patterns'])} patterns ready, {n_big} of them at 128 x 128 too "
        f"({time.monotonic() - t0:.0f} s)")
    return list(out.values())


def _first_error(err):
    m = re.search(r"error: (.*)", err)
    return m.group(1) if m else err.strip().splitlines()[-1] if err.strip() else "?"


def check(jobs=None, only=None):
    """Every version of every pattern (or ONLY these, by id prefix) through a scripted player: the
    compiled ones under AddressSanitizer, the scripts in node's sandbox. Each leaves its SHOTS in
    CHECK for `sheet` and `strip`. Results merge into checks.json, so checks may run side by side."""
    idx, _ = load_index()
    if only:
        keep = lambda e: any(e["id"].startswith(o) for o in only)      # noqa: E731
        idx = dict(idx, patterns=[e for e in idx["patterns"] if keep(e)], js_only=[e for e in idx["js_only"] if keep(e)])
    CHECK.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0:abort_on_error=0")

    def header(job):
        e, name, spec = job
        _, why = release(e, spec)       # vetted before anything of it runs here
        if why:
            return e, name, spec, {"verdict": why}
        exe, err = compile_one(e, spec["text"], spec["ns"], spec["size"], CHECK,
                               ["-O1", "-g", "-fsanitize=address", "-fno-omit-frame-pointer", "-DPF_HOST_CHECK"], exe=True)
        if err:
            return e, name, spec, {"verdict": "build: " + _first_error(err)}
        try:
            r = subprocess.run([str(exe), str(CHECK_FRAMES), ",".join(map(str, SHOTS))], capture_output=True, env=env,
                               timeout=120)
        except subprocess.TimeoutExpired:
            return e, name, spec, {"verdict": "timeout"}
        (CHECK / f"{e['id']}-{name}.rgb").write_bytes(r.stdout)
        verdict = "ok"
        if r.returncode:
            m = re.search(rb"ERROR: AddressSanitizer: ([\w-]+)", r.stderr)
            verdict = "asan: " + m.group(1).decode() if m else f"exit {r.returncode}"
        return e, name, spec, {"verdict": verdict, "w": spec["size"][0], "h": spec["size"][1]}

    def script(job):
        e, name, spec = job
        args = ["check", SRC, e["id"], spec["file"], name, CHECK_FRAMES, ",".join(map(str, SHOTS)), CHECK]
        if spec["matrix"]:
            args.append("%dx%d" % spec["matrix"])
        # Its own session, so a timeout kills node too, not just the bwrap around it.
        p = subprocess.Popen(node_argv(args, write=[CHECK]), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, start_new_session=True)
        try:
            out, err = p.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.communicate()
            return e, name, spec, {"verdict": "timeout"}
        res = json.loads(out) if out.strip() else {"verdict": "exit: " + err[-300:]}
        return e, name, spec, res

    work = [(header, (e, name, spec)) for e in idx["patterns"] for name, spec in (header_variants(e) or {}).items() if spec]
    if idx["js_only"] and not (SRC / "web" / "harness.js").exists():
        print("JavaScript-only patterns not checked: no harness (sync with node >= 22.6)")
    elif idx["js_only"] and not node_argv([]):
        print("JavaScript-only patterns not checked: needs node with its permission model, and unshare or bwrap")
    elif idx["js_only"]:
        work += [(script, (e, name, spec)) for e in idx["js_only"] for name, spec in script_variants(e).items()]

    fresh = {}
    for e, name, spec, res in ThreadPoolExecutor(jobs or os.cpu_count()).map(lambda w: w[0](w[1]), work):
        res.pop("id", None)
        fresh.setdefault(e["id"], {"title": e["title"]})[name] = {"sha": spec["sha"], **res}
        if res["verdict"] != "ok":
            print(f"{e['title']} ({e['id']}, {name}): {res['verdict']}")
    with open(SRC / "checks.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        checks = json.loads((SRC / "checks.json").read_text()) if only and (SRC / "checks.json").exists() else {}
        for i, c in fresh.items():
            checks.setdefault(i, {}).update(c)
        (SRC / "checks.json").write_text(json.dumps(checks, indent=1, ensure_ascii=False))
    runs = [v for c in fresh.values() for k, v in c.items() if k != "title"]
    print(f"checked {len(fresh)} patterns, {len(runs)} versions ({sum(r['verdict'] != 'ok' for r in runs)} not ok) "
          f"-> {SRC / 'checks.json'}")


@functools.lru_cache(maxsize=None)
def _sandbox():
    """(node's permission flag, a network-namespace prefix taking extra writable paths), or None if either is missing."""
    if not shutil.which("node"):
        return None
    ok = lambda argv: subprocess.run(argv, capture_output=True).returncode == 0      # noqa: E731
    flag = next((f for f in ("--permission", "--experimental-permission") if ok(["node", f, "-e", "0"])), None)
    if not flag:
        return None
    if ok(["unshare", "-rn", "true"]):                  # the Pi
        return flag, lambda writable: ["unshare", "-rn"]
    bwrap = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--unshare-net", "--die-with-parent"]
    if shutil.which("bwrap") and ok(bwrap + ["true"]):  # ash: Ubuntu lets bwrap have a user namespace, not unshare
        return flag, lambda writable: bwrap + [a for w in writable for a in ("--bind", str(w), str(w))]
    return None


def node_argv(args, write=()):
    """jsrun.mjs ARGS under node's permission model (reads in upstream_host only, writes only in WRITE),
    with no network: the only way a JavaScript pattern runs. None where that can't be arranged."""
    box = _sandbox()
    if not box:
        return None
    flag, netns = box
    return [*netns(write), "node", "--no-warnings", flag, f"--allow-fs-read={HERE}",
            *(f"--allow-fs-write={w}" for w in write),
            "--max-old-space-size=512", str(HERE / "jsrun.mjs"), *map(str, args)]


def js_patterns(src=SRC):
    """The JavaScript-only patterns that can run -> [(entry, {"native": spec, "big": spec})], in index order.
    "big" is there only where the review puts it on the COMMUNITY shelf and its check passed."""
    idx, checks = load_index(src)
    if not (src / "web" / "harness.js").exists():
        return []
    chosen = review()
    out = []
    for e in idx["js_only"]:
        vs = script_variants(e, src)
        if not runnable(e, "native", vs["native"], checks):
            continue
        keep = {"native": vs["native"]}
        if chosen.get(e["id"], "native") != "native" and runnable(e, "big", vs["big"], checks):
            keep["big"] = vs["big"]
        out.append((e, keep))
    return out


def sheet(out, only=None):
    """Contact sheets of the check's frames, for the review: each pattern as published (centred, and
    turned if it's in TURN) beside its 128 x 128 version, with the review's choice under the pair."""
    from PIL import Image, ImageDraw
    idx, checks = load_index()
    chosen = review()
    pairs = []
    for e in idx["patterns"] + idx["js_only"]:
        if only and not any(e["id"].startswith(o) for o in only):
            continue
        cells = []
        for name in ("native", "big"):
            c = checks.get(e["id"], {}).get(name, {})
            f = CHECK / f"{e['id']}-{name}.rgb"
            img = _shot(c, f, SHEET_SHOT)
            if img:
                if e["id"] in (TURN if name == "native" else BIG_TURN):
                    img = img.rotate(90, expand=True)       # anticlockwise, as pfd turns it
            cells.append((img, c.get("verdict", "-")))
        pairs.append((e, cells))
    out.mkdir(parents=True, exist_ok=True)
    per_row, rows, cw, ch = 3, 5, 136, 152
    for page in range(0, len(pairs), per_row * rows):
        img = Image.new("RGB", (per_row * 2 * cw, rows * ch), (40, 40, 40))
        d = ImageDraw.Draw(img)
        for n, (e, cells) in enumerate(pairs[page:page + per_row * rows]):
            x0, y0 = (n % per_row) * 2 * cw, (n // per_row) * ch
            for k, (frame, verdict) in enumerate(cells):
                sq = Image.new("RGB", SQUARE, (0, 0, 0) if frame else (90, 0, 0))
                if frame:
                    sq.paste(frame, ((128 - frame.width) // 2, (128 - frame.height) // 2))
                img.paste(sq, (x0 + k * cw + 4, y0 + 2))
                if verdict != "ok":
                    d.text((x0 + k * cw + 6, y0 + 4), "!", fill=(255, 80, 80))
            d.text((x0 + 4, y0 + 131), f"{e['id'][:6]} [{chosen.get(e['id'], '-')}]", fill=(255, 200, 80))
            d.text((x0 + 4, y0 + 141), e["title"][:40], fill=(170, 170, 170))
        p = out / f"sheet{page // (per_row * rows):02d}.png"
        img.save(p)
        print(p)


def _shot(c, f, k):
    """Frame k of SHOTS from a check's file, as a PIL image, or None."""
    from PIL import Image
    n = c.get("w", 0) * c.get("h", 0) * 3
    if not n or not f.exists() or f.stat().st_size < n * (k + 1):
        return None
    with open(f, "rb") as fh:
        fh.seek(n * k)
        return Image.frombytes("RGB", (c["w"], c["h"]), fh.read(n))


def strip(out, only):
    """For each pattern (ONLY these, by id prefix): its versions over time, a row each, every frame
    of SHOTS as the panel shows it (centred, turned). For judging a port: motion and the knobs' ends."""
    from PIL import Image, ImageDraw
    idx, checks = load_index()
    out.mkdir(parents=True, exist_ok=True)
    for e in idx["patterns"] + idx["js_only"]:
        if only and not any(e["id"].startswith(o) for o in only):
            continue
        img = Image.new("RGB", (len(SHOTS) * 132 + 4, 2 * 144 + 4), (40, 40, 40))
        d = ImageDraw.Draw(img)
        for row, name in enumerate(("native", "big")):
            c = checks.get(e["id"], {}).get(name, {})
            for k, frame_no in enumerate(SHOTS):
                frame = _shot(c, CHECK / f"{e['id']}-{name}.rgb", k)
                sq = Image.new("RGB", SQUARE, (0, 0, 0) if frame else (90, 0, 0))
                if frame:
                    if e["id"] in (TURN if name == "native" else BIG_TURN):
                        frame = frame.rotate(90, expand=True)
                    sq.paste(frame, ((128 - frame.width) // 2, (128 - frame.height) // 2))
                img.paste(sq, (4 + k * 132, 4 + row * 144))
                label = f"{name} {frame_no / 60:.1f}s" + (f"  {c.get('verdict', '-')[:14]}" if k == 0 else "")
                d.text((6 + k * 132, 134 + row * 144), label, fill=(200, 200, 200))
        p = out / f"{e['id']}.png"
        img.save(p)
        print(p, e["title"])


def twin(out, only=None):
    """Each original's script and header (ONLY these, by name) through the check's scripted player, as
    written and at 128 x 128: how far apart their frames are, and a strip of both (script above, header
    below) per version. The knob turns and clicks are the same for both; the audio phase is the header's alone."""
    import numpy as np
    from PIL import Image
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0:abort_on_error=0")
    for e, vs in original_entries():
        if only and e["id"] not in only:
            continue
        js = ORIGINALS / f"{e['id']}.js"
        for name, spec in vs.items():
            if name == "audio":         # the big one again, listening: the script has nothing to hear
                continue
            w, h = spec["size"]
            exe, err = compile_one(e, spec["text"], spec["ns"], spec["size"], out,
                                   ["-O1", "-g", "-fsanitize=address", "-fno-omit-frame-pointer", "-DPF_HOST_CHECK"],
                                   exe=True)
            if err:
                print(f"{e['title']} ({name}): header doesn't build: {_first_error(err)}")
                continue
            r = subprocess.run([str(exe), str(CHECK_FRAMES), ",".join(map(str, SHOTS))], capture_output=True, env=env)
            if r.returncode:
                print(f"{e['title']} ({name}): header failed ({r.returncode})\n{r.stderr.decode()[-1500:]}")
                continue
            cpp = np.frombuffer(r.stdout, np.uint8).reshape(len(SHOTS), h, w, 3)
            fw, fh = re.search(r"FRAME_W\s*=\s*(\d+)", spec["text"]), re.search(r"FRAME_H\s*=\s*(\d+)", spec["text"])
            fw, fh = (int(fw.group(1)), int(fh.group(1))) if fw and fh else (w, h)
            argv = node_argv(["check", SRC, e["id"], js, name, CHECK_FRAMES, ",".join(map(str, SHOTS)), out,
                              f"{fw}x{fh}"], write=[out])
            if not argv:
                print("no script to compare: needs node with its permission model, and unshare or bwrap")
                return
            res = subprocess.run(argv, capture_output=True, text=True)
            verdict = json.loads(res.stdout).get("verdict") if res.stdout.strip() else res.stderr[-500:]
            if verdict != "ok":
                print(f"{e['title']} ({name}): script {verdict}")
                continue
            script = np.fromfile(out / f"{e['id']}-{name}.rgb", np.uint8).reshape(len(SHOTS), fh, fw, 3)
            # The header's frame is the frame centred in the panel; the script's is the frame alone.
            oy, ox = (h - fh) // 2, (w - fw) // 2
            cpp = cpp[:, oy:oy + fh, ox:ox + fw]
            diffs = []
            for k, f in enumerate(SHOTS):
                d = np.abs(cpp[k].astype(int) - script[k].astype(int)).max(axis=2)
                diffs.append(f"{f / 60:.1f}s {d.mean():.2f} ({(d > 24).mean() * 100:.1f}%)")
            print(f"{e['title']} ({name}, {fw} x {fh}): mean |script - header|, and pixels off by more than 24:")
            print("   " + ", ".join(diffs))
            img = np.full((2 * fh + 6, len(SHOTS) * (fw + 4) + 2, 3), 40, np.uint8)
            for k in range(len(SHOTS)):
                x = 2 + k * (fw + 4)
                img[2:2 + fh, x:x + fw] = script[k]
                img[4 + fh:4 + 2 * fh, x:x + fw] = cpp[k]
            p = out / f"{e['id']}-{name}.png"
            Image.fromarray(img).resize((img.shape[1] * 3, img.shape[0] * 3), Image.NEAREST).save(p)
            print("  ", p)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("cmd", choices=["sync", "build", "check", "sheet", "strip", "twin"])
    p.add_argument("out", nargs="?", type=Path, help="sheet: a directory for the PNGs")
    p.add_argument("--only", default="", help="check, sheet, strip: these patterns only, by id or id prefix, "
                                              "comma-separated; twin: these originals, by name")
    p.add_argument("-j", "--jobs", type=int, default=None)
    args = p.parse_args()
    if args.cmd == "sync":
        sync()
    elif args.cmd == "build":
        build(args.jobs)
    elif args.cmd == "check":
        check(args.jobs, [o for o in args.only.split(",") if o])
    elif args.cmd == "twin":
        twin(args.out or Path("/tmp/originals-twin"), [o for o in args.only.split(",") if o])
    elif args.cmd == "strip":
        strip(args.out or Path("/tmp/community-strips"), [o for o in args.only.split(",") if o])
    else:
        sheet(args.out or Path("/tmp/community-sheets"), [o for o in args.only.split(",") if o])


if __name__ == "__main__":
    main()
