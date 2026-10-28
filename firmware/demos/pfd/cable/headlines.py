"""Today's headlines from The Onion, for ONN and the news crawls.

A personal feed reader, and a gentle one:
- robots.txt is read under our own user-agent (at most once a day) and obeyed;
- the feed is read at most once every 6 hours, plus up to half an hour of jitter, and when
  the next read is due is remembered on disk, so restarts (update_pi.py, the watchdog, a
  power cut) never cause an extra one;
- reads are conditional (ETag, Last-Modified): an unchanged feed costs a 304 and no body;
- gzip, a 15 s timeout, and at most 2 MB;
- a failure backs off, doubling from half an hour up to a day, and a Retry-After is honoured;
- only the items' titles are used, and the screen credits The Onion.

The state is cached on disk ($CACHE_DIRECTORY, which systemd's CacheDirectory= gives the Pi's
service, else ~/.cache/patternflood), so the panel keeps the last headlines when it's
offline, and shows our own when it has never been online. PF_HEADLINES=off leaves the
network alone.
"""
import email.utils
import gzip
import json
import os
import random
import threading
import time
import unicodedata
import urllib.error
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from pathlib import Path

from ..io import log

FEED = "https://theonion.com/feed/"
ROBOTS = "https://theonion.com/robots.txt"
AGENT = "patternflood-cable"
UA = f"{AGENT}/1.1 (a personal LED-panel TV; reads this feed a few times a day)"
CACHE = Path(os.environ.get("CACHE_DIRECTORY") or os.path.expanduser("~/.cache/patternflood")) / "headlines.json"
EVERY_S = 6 * 3600
JITTER_S = 1800
BACKOFF_S = (1800, 24 * 3600)
ROBOTS_EVERY_S = 24 * 3600
MAX_BYTES = 2_000_000
TIMEOUT_S = 15
CREDIT = "HEADLINES VIA THE ONION"
FALLBACK = ["AREA MAN UNSURE WHICH DIMENSION HE PARKED IN", "SCIENTISTS DISCOVER SECOND, WORSE MOON",
            "NATION'S CLOCKS AGREE TO DISAGREE", "LOCAL DOG ELECTED TO MORE DOGS",
            "REPORT: MOST OF SKY STILL UP THERE", "SOUP RECALLED FOR BEING TOO SOUP",
            "MAN WHO WENT BACK IN TIME TO STOP HIMSELF STOPPED", "TUESDAY POSTPONED INDEFINITELY"]

_lock = threading.Lock()
_state = {}
_started = False


def _clean(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("—", " - ").replace("–", "-").replace("…", "...")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def _get(url, headers=()):
    """(body, response headers); raises urllib.error.HTTPError for a 304 or a failure."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip", **dict(headers)})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        body = r.read(MAX_BYTES + 1)
        if r.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        if len(body) > MAX_BYTES:
            raise ValueError(f"{url}: over {MAX_BYTES} bytes")
        return body, r.headers


def _robots_allow():
    try:
        body, _ = _get(ROBOTS)
    except urllib.error.HTTPError as e:
        if 400 <= e.code < 500:
            return True                 # no robots.txt: no rules
        raise
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(body.decode("utf-8", "replace").splitlines())
    return rp.can_fetch(AGENT, FEED)


def _retry_after(e):
    v = e.headers.get("Retry-After") if e.headers else None
    if not v:
        return 0
    if v.strip().isdigit():
        return int(v)
    try:
        return max(0, email.utils.parsedate_to_datetime(v).timestamp() - time.time())
    except (TypeError, ValueError):
        return 0


def _attempt(st):
    now = time.time()
    if now - st.get("robots_at", 0) > ROBOTS_EVERY_S:
        st["robots_ok"], st["robots_at"] = _robots_allow(), now
    if not st.get("robots_ok", True):
        log("cable: robots.txt asks us not to read the feed; showing our own headlines")
        st["items"], st["next"] = [], now + ROBOTS_EVERY_S
        return
    cond = {k: v for k, v in (("If-None-Match", st.get("etag")), ("If-Modified-Since", st.get("modified"))) if v}
    try:
        body, headers = _get(FEED, cond)
    except urllib.error.HTTPError as e:
        if e.code != 304:
            raise
        log("cable: headlines unchanged")
    else:
        root = ET.fromstring(body)
        items = [s for s in dict.fromkeys(_clean(it.findtext("title") or "") for it in root.iter("item"))
                 if 8 <= len(s) <= 110]
        if items:
            st.update(items=items, etag=headers.get("ETag"), modified=headers.get("Last-Modified"))
            log(f"cable: {len(items)} headlines from The Onion")
    st["fails"], st["next"] = 0, now + EVERY_S + random.uniform(0, JITTER_S)


def _save(st):
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE.with_suffix(".tmp")
        tmp.write_text(json.dumps(st))
        tmp.replace(CACHE)
    except OSError as e:
        log(f"cable: headlines not cached: {e}")


def _loop():
    while True:
        with _lock:
            st = dict(_state)
        wait = st.get("next", 0) - time.time()
        if wait > 0:
            time.sleep(min(wait, 3600))
            continue
        try:
            _attempt(st)
        except Exception as e:          # noqa: BLE001 (offline, or the feed moved: keep what we have)
            st["fails"] = st.get("fails", 0) + 1
            delay = min(BACKOFF_S[1], BACKOFF_S[0] * 2 ** (st["fails"] - 1))
            if isinstance(e, urllib.error.HTTPError):
                delay = max(delay, _retry_after(e))
            st["next"] = time.time() + delay + random.uniform(0, 60)
            log(f"cable: headlines: {e} (next try in {delay / 3600:.1f} h)")
        with _lock:
            _state.clear()
            _state.update(st)
        _save(st)


def start():
    """Load the cache and start the reader, once."""
    global _started
    if _started:
        return
    _started = True
    try:
        st = json.loads(CACHE.read_text())
        st = {"items": st} if isinstance(st, list) else st         # the first version cached the list alone
        if isinstance(st, dict) and all(isinstance(s, str) for s in st.get("items", [])):
            _state.update(st)
    except (OSError, ValueError):
        pass
    if os.environ.get("PF_HEADLINES", "").lower() not in ("off", "0", "no"):
        threading.Thread(target=_loop, daemon=True).start()


def real():
    """The Onion's headlines, if we have any."""
    with _lock:
        return list(_state.get("items", []))


def get():
    return real() or list(FALLBACK)
