"""Onshape REST transport shared by push.py, export_dxf.py and decals.py.

Calls go through curl, with the Onshape API keys in ~/.netrc. Responses come
back as text, which is all these tools need (JSON).
"""
import json
import os
import subprocess
import sys
import tempfile

HINT = {
    401: "the API keys in ~/.netrc were rejected",
}


def request(method, url, body=None, form=None):
    """Send one call; returns (status, response bytes).

    body is sent as JSON. form maps field -> value in curl -F syntax, so a file
    is "@path;type=image/png". A 401 stops the run: no call after it would
    succeed either.
    """
    status, out = _curl(method, url, body, form)
    if status in HINT:
        sys.exit(f"onshape: HTTP {status} on {method} {url}\n  {HINT[status]}")
    return status, out


def _curl(method, url, body, form):
    cmd = ["curl", "-s", "--netrc", "-X", method, "-w", "\n%{http_code}"]
    path = None
    if body is not None:
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(body, f)
        cmd += ["-H", "Content-Type: application/json", "--data-binary", "@" + path]
    for k, v in (form or {}).items():
        cmd += ["-F", f"{k}={v}"]
    try:
        out = subprocess.run(cmd + [url], capture_output=True).stdout
    finally:
        if path:
            os.remove(path)
    out, _, code = out.rpartition(b"\n")
    return int(code or 0), out
