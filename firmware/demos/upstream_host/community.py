#!/usr/bin/env python3
"""Build Patternflow's community patterns (community.patternflow.work) into host libraries.

The community wall's patterns are JavaScript, and most also carry a firmware header:
the author's own, or a port someone verified on hardware. The headers are what we run.
Each is compiled, unchanged but for a few mechanical fixups, into its own small shared
library with build.py's C API (pfd/upstream.py drives both), against our shim and the
portable cores of upstream's main branch, which the community builds against.

    ./community.py sync              # the wall's public patterns, their headers, and upstream's cores
    ./community.py build             # compile what's new, in parallel (the controller does this on start)
    ./community.py check             # on ash: run each under AddressSanitizer -> src/checks.json
    ./community.py sheet /tmp/cs     # contact sheets of the check's frames, to judge the canvas by eye

One library per pattern: names collide between authors, a header that doesn't compile
costs only itself, and a re-sync compiles only what changed. They're built with hidden
visibility and no GNU-unique symbols, so each keeps its own canvas in one process.

Canvas: each pattern runs at the size it was written for, centred in the square. One
that calls PFCanvas::setFrame (all of them portrait, 64 x 128) is built for 128 x 128,
and the shim centres its frame. The rest were written for upstream's 128 x 64, and are
built at that size and letterboxed.

The patterns are CC BY-SA 4.0, their authors'. They're fetched into build/ and aren't
copied into this repository.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
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
CACHE = HERE / "build" / "community"
SRC, LIB, CHECK = CACHE / "src", CACHE / "lib", CACHE / "check"
SHIMS = [HERE / "community_shim", HERE / "shim"]
FLAGS = ["-std=c++17", "-w", "-fvisibility=hidden", "-fvisibility-inlines-hidden", "-fno-gnu-unique"]
SQUARE, WIDE = (128, 128), (128, 64)
CHECK_FRAMES, SHEET_FRAME = 660, 90


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
    patterns, js_only = [], []
    for c in cards:
        entry = {"id": c["id"], "title": c["title"].strip(), "author": c.get("displayUsername") or c.get("username") or "",
                 "likes": c.get("likeCount", 0), "created": c.get("createdAt")}
        if not c.get("hasCpp"):
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
    shutil.rmtree(SRC, ignore_errors=True)
    new.rename(SRC)
    print(f"{len(patterns)} patterns with headers, {len(js_only)} JavaScript only; upstream cores at {sha[:8]} -> {SRC}")


def fixup(text):
    """Mechanical repairs, so a header builds here as on the firmware -> (text, namespace) or (text, None)."""
    text = text.replace('"../src/', '"src/').replace('"../config.h"', '"config.h"').replace('"../abi/', '"abi/')
    m = re.search(r"^[ \t]*namespace[ \t]+([^{\n]+?)[ \t]*\{", text, re.M)
    if not m:
        return text, None
    ns = re.sub(r"\W+", "_", m.group(1)).strip("_")
    return text[:m.start(1)] + ns + text[m.end(1):], ns


def unit(ns, author):
    """The translation unit around one header (included as pattern.h): build.py's C API over one entry."""
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
    lines += ["#pragma GCC visibility pop", "", CHECK_MAIN]
    return "\n".join(lines) + "\n"


# A scripted player for the check: idle (the sheet's frame), then out to the knobs' extremes
# and back, fast spins, clicks, push-and-turn, and the audio edition, 60 frames each.
CHECK_MAIN = r"""#ifdef PF_HOST_CHECK
int main(int argc, char** argv) {
  int frames = atoi(argv[1]), shot = atoi(argv[2]);
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
    if (f == shot) fwrite(buf, 1, (size_t)PANEL_RES_W * PANEL_RES_H * 3, stdout);
  }
  return 0;
}
#endif"""


def load_index(src=SRC):
    idx = json.loads((src / "index.json").read_text())
    checks = json.loads((src / "checks.json").read_text()) if (src / "checks.json").exists() else {}
    return idx, checks


def prepare(entry, src=SRC):
    """-> (fixed header text, namespace or None, header sha)."""
    raw = (src / "h" / f"{entry['id']}.h").read_text(encoding="utf-8", errors="replace")
    text, ns = fixup(raw)
    return text, ns, hashlib.sha256(raw.encode()).hexdigest()[:16]


def canvas(text):
    """setFrame's patterns centre their own frame in 128 x 128; the rest are 128 x 64."""
    return SQUARE if "setFrame" in text else WIDE


def runnable(entry, sha, size, checks):
    """False only if the last check of this very header found it unsafe."""
    c = checks.get(entry["id"])
    return not c or c.get("sha") != sha or c.get(f"{size[0]}x{size[1]}") == "ok"


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
    tu = unit(ns, entry["author"])
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
    (work / "out").rename(out)
    shutil.rmtree(work, ignore_errors=True)
    return out, None


def build(jobs=None, src=SRC, lib=LIB, log=print):
    """Compile every pattern that will run -> [(entry, library path)], in index order."""
    idx, checks = load_index(src)
    lib.mkdir(parents=True, exist_ok=True)
    todo = []
    for e in idx["patterns"]:
        text, ns, sha = prepare(e, src)
        if ns and runnable(e, sha, canvas(text), checks):
            todo.append((e, text, ns))
        else:
            log(f"community: skipping {e['title']} ({e['id']}): " + ("the check found it unsafe" if ns else "no namespace"))
    t0 = time.monotonic()

    def one(job):
        e, text, ns = job
        path, err = compile_one(e, text, ns, canvas(text), lib, ["-O2", "-fPIC", "-shared", "-Wl,-Bsymbolic"], src)
        if err:
            log(f"community: {e['title']} ({e['id']}) doesn't build: {_first_error(err)}")
        return e, path

    built = list(ThreadPoolExecutor(jobs or os.cpu_count()).map(one, todo))
    keep = {p.name for _, p in built if p}
    for f in lib.iterdir():             # libraries of headers since replaced or removed
        if f.name not in keep:
            shutil.rmtree(f) if f.is_dir() else f.unlink()
    ok = [b for b in built if b[1]]
    log(f"community: {len(ok)} of {len(idx['patterns'])} patterns ready ({time.monotonic() - t0:.0f} s)")
    return ok


def _first_error(err):
    m = re.search(r"error: (.*)", err)
    return m.group(1) if m else err.strip().splitlines()[-1] if err.strip() else "?"


def check(jobs=None):
    """Each pattern under AddressSanitizer, through a scripted player, at the size it runs at."""
    idx, _ = load_index()
    CHECK.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0:abort_on_error=0")
    jobs_list = []
    for e in idx["patterns"]:
        text, ns, sha = prepare(e)
        if ns:
            jobs_list.append((e, text, ns, sha, canvas(text)))

    def one(job):
        e, text, ns, sha, size = job
        exe, err = compile_one(e, text, ns, size, CHECK,
                               ["-O1", "-g", "-fsanitize=address", "-fno-omit-frame-pointer", "-DPF_HOST_CHECK"], exe=True)
        if err:
            return e, sha, size, "build: " + _first_error(err)
        try:
            r = subprocess.run([str(exe), str(CHECK_FRAMES), str(SHEET_FRAME)], capture_output=True, env=env, timeout=120)
        except subprocess.TimeoutExpired:
            return e, sha, size, "timeout"
        frame = CHECK / f"{e['id']}-{size[0]}x{size[1]}.rgb"
        frame.write_bytes(r.stdout)
        if r.returncode:
            m = re.search(rb"ERROR: AddressSanitizer: ([\w-]+)", r.stderr)
            return e, sha, size, "asan: " + m.group(1).decode() if m else f"exit {r.returncode}"
        return e, sha, size, "ok"

    checks = {}
    for e, sha, size, verdict in ThreadPoolExecutor(jobs or os.cpu_count()).map(one, jobs_list):
        checks.setdefault(e["id"], {"sha": sha, "title": e["title"]})[f"{size[0]}x{size[1]}"] = verdict
        if verdict != "ok":
            print(f"{e['title']} ({e['id']}) at {size[0]}x{size[1]}: {verdict}")
    (SRC / "checks.json").write_text(json.dumps(checks, indent=1, ensure_ascii=False))
    bad = sum(1 for c in checks.values() for k, v in c.items() if "x" in k and v != "ok")
    print(f"checked {len(checks)} patterns ({bad} not ok) -> {SRC / 'checks.json'}")


def sheet(out):
    """Contact sheets from the check's frames, each centred in the square as on the panel."""
    from PIL import Image, ImageDraw
    idx, checks = load_index()
    cells = []
    for e in idx["patterns"]:
        size = canvas(prepare(e)[0])
        f = CHECK / f"{e['id']}-{size[0]}x{size[1]}.rgb"
        if f.exists() and f.stat().st_size == size[0] * size[1] * 3:
            img = Image.frombytes("RGB", size, f.read_bytes())
            verdict = checks.get(e["id"], {}).get(f"{size[0]}x{size[1]}", "?")
            cells.append((e, size, img, verdict))
    out.mkdir(parents=True, exist_ok=True)
    cols, rows, cw, ch = 6, 5, 136, 150
    for page in range(0, len(cells), cols * rows):
        sheet_img = Image.new("RGB", (cols * cw, rows * ch), (40, 40, 40))
        d = ImageDraw.Draw(sheet_img)
        for i, (e, size, img, verdict) in enumerate(cells[page:page + cols * rows]):
            x, y = (i % cols) * cw + 4, (i // cols) * ch + 2
            sq = Image.new("RGB", SQUARE)
            sq.paste(img, ((128 - size[0]) // 2, (128 - size[1]) // 2))
            sheet_img.paste(sq, (x, y))
            label = f"{e['id'][:6]} {size[0]}x{size[1]}{'' if verdict == 'ok' else ' !'}"
            d.text((x, y + 129), label, fill=(255, 200, 80) if verdict != "ok" else (200, 200, 200))
            d.text((x, y + 139), e["title"][:22], fill=(150, 150, 150))
        p = out / f"sheet{page // (cols * rows):02d}.png"
        sheet_img.save(p)
        print(p)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("cmd", choices=["sync", "build", "check", "sheet"])
    p.add_argument("out", nargs="?", type=Path, help="sheet: a directory for the PNGs")
    p.add_argument("-j", "--jobs", type=int, default=None)
    args = p.parse_args()
    if args.cmd == "sync":
        sync()
    elif args.cmd == "build":
        build(args.jobs)
    elif args.cmd == "check":
        check(args.jobs)
    else:
        sheet(args.out or Path("/tmp/community-sheets"))


if __name__ == "__main__":
    main()
