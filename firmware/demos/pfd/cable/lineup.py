"""Every channel, for the Cable demo: shows.py's, and each themed batch's."""
from .shows import CHANNELS as _SHOWS

CHANNELS = list(_SHOWS)
_nums = [c.num for c in CHANNELS]
assert len(_nums) == len(set(_nums)), "two channels share a number"
