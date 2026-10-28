"""Every channel, for the Cable demo: shows.py's, and each themed batch's.

    2-99     shows.py         the first 25, with ONN (6) and dead air (404)
    101-199  batch_ads        commercials and infomercials
    201-299  batch_formats    TV formats gone wrong
    301-399  batch_slapstick  silent slapstick and cartoon physics
    501-599  batch_docs       kids' TV, nature docs, science, PSAs
    601-699  batch_strange    stop motion, toy figures, trailers, pure strangeness
    700-     tapes            video files from ~/cable (pfd/demos/cable.py)
"""
from . import batch_ads, batch_docs, batch_formats, batch_slapstick, batch_strange
from .shows import CHANNELS as _SHOWS

CHANNELS = (list(_SHOWS) + batch_ads.CHANNELS + batch_formats.CHANNELS + batch_slapstick.CHANNELS
            + batch_docs.CHANNELS + batch_strange.CHANNELS)
_nums = [c.num for c in CHANNELS]
assert len(_nums) == len(set(_nums)), "two channels share a number"
