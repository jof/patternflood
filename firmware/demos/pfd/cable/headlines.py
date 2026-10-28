"""Today's headlines from The Onion, for ONN and the news crawls.

Fetched in the background when the Cable demo first comes up, then every few hours, and
cached on disk ($CACHE_DIRECTORY, which systemd's CacheDirectory= gives the Pi's
service, else ~/.cache/patternflood), so the panel keeps yesterday's news when it's offline and our own when it
has never been online. PF_HEADLINES=off leaves the network alone.
"""
import json
import os
import threading
import time
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from ..io import log

FEED = "https://theonion.com/feed/"
CACHE = Path(os.environ.get("CACHE_DIRECTORY") or os.path.expanduser("~/.cache/patternflood")) / "headlines.json"
EVERY_S = 3 * 3600
FALLBACK = ["AREA MAN UNSURE WHICH DIMENSION HE PARKED IN", "SCIENTISTS DISCOVER SECOND, WORSE MOON",
            "NATION'S CLOCKS AGREE TO DISAGREE", "LOCAL DOG ELECTED TO MORE DOGS",
            "REPORT: MOST OF SKY STILL UP THERE", "SOUP RECALLED FOR BEING TOO SOUP",
            "MAN WHO WENT BACK IN TIME TO STOP HIMSELF STOPPED", "TUESDAY POSTPONED INDEFINITELY"]

_lock = threading.Lock()
_items = []
_started = False


def _clean(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("—", " - ").replace("–", "-").replace("…", "...")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def _fetch():
    req = urllib.request.Request(FEED, headers={"User-Agent": "patternflood-cable/1"})
    with urllib.request.urlopen(req, timeout=15) as r:
        root = ET.fromstring(r.read())
    out = [_clean(it.findtext("title") or "") for it in root.iter("item")]
    return [s for s in dict.fromkeys(out) if 8 <= len(s) <= 110]


def _set(items):
    global _items
    with _lock:
        _items = items


def _loop():
    while True:
        try:
            fresh = time.time() - CACHE.stat().st_mtime < EVERY_S
        except OSError:
            fresh = False
        if not fresh:
            try:
                items = _fetch()
            except Exception as e:      # noqa: BLE001 (offline, or the feed moved: keep what we have)
                log(f"cable: headlines: {e}")
                items = []
            if items:
                _set(items)
                log(f"cable: {len(items)} headlines from The Onion")
                try:
                    CACHE.parent.mkdir(parents=True, exist_ok=True)
                    CACHE.write_text(json.dumps(items))
                except OSError as e:
                    log(f"cable: headlines not cached: {e}")
        time.sleep(EVERY_S)


def start():
    """Load the cache and start fetching, once."""
    global _started
    if _started:
        return
    _started = True
    try:
        _set([s for s in json.loads(CACHE.read_text()) if isinstance(s, str)])
    except (OSError, ValueError):
        pass
    if os.environ.get("PF_HEADLINES", "").lower() not in ("off", "0", "no"):
        threading.Thread(target=_loop, daemon=True).start()


def get():
    with _lock:
        return list(_items) or list(FALLBACK)
