"""Patternflow's community patterns (community.patternflow.work), on their own shelf.

upstream_host/community.py fetches the wall's firmware headers (`sync`, on ash) and
compiles each into its own library; this builds whatever is missing, then runs each
as an upstream preset runs (pfd/upstream.py), at its own canvas, centred. Most liked
first. With nothing synced, the shelf isn't there.
"""
import importlib.util

from .io import log
from .upstream import BUILD, Upstream, knobs_blurb, open_lib


def _builder():
    spec = importlib.util.spec_from_file_location("pf_community_build", BUILD / "community.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def demos():
    """One Demo class per community pattern that builds, or [] if none have been synced."""
    cm = _builder()
    if not (cm.SRC / "index.json").exists():
        return []
    try:
        built = cm.build(log=log)
    except Exception as e:              # a broken cache costs the shelf, not the box
        log(f"community: {e!r}; running without community patterns")
        return []
    out = []
    for e, path in sorted(built, key=lambda b: -b[0]["likes"]):
        try:
            lib = open_lib(path)
        except OSError as err:
            log(f"community: {e['title']}: {err}")
            continue
        by = f" by @{e['author']}" if e["author"] else ""
        port = f", ported by @{e['ported_by']}" if e.get("ported_by") else ""
        blurb = f"Community pattern{by}{port}." + knobs_blurb(lib, 0)
        out.append(type(f"PFC_{e['id']}", (Upstream,), {"name": e["title"], "blurb": blurb, "lib": lib,
                                                        "index": 0, "group": "community"}))
    return out
