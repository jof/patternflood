"""Audio in, and what it means: level, spectrum, onsets, tempo, beats, bars, phrases.

Sources (run.py --audio):
    pulse[:SOURCE]        a PulseAudio/PipeWire source; by default the monitor of the
                          default output, i.e. whatever this machine is playing (ash)
    alsa[:DEVICE]         an ALSA capture device via arecord (the Pi 5's line-in or mic)
    file:PATH[@SECONDS]   a track decoded by ffmpeg, paced in real time, or stepped with
                          the frames in a preview; silent, nothing is played
    none

The analyzer runs on audio held back by --audio-delay seconds, so what it sees lines
up with what you hear. Bluetooth output is ~0.2 s behind its own monitor.

Analysis, at 48 kHz in hops of 512 samples (93.75 a second), on a 2048-point FFT:
  level, 24 log-spaced bands      RMS and band energies, each against its own slow peak
  onsets                          spectral flux on log band energies; kick (lows),
                                  snare (mids), hat (highs) flux kept separately
  tempo                           autocorrelation of the last 8 s of onset strength,
                                  scored with its 2x and 4x lags (bars repeat too) under a
                                  broad prior around 125 BPM, refined to a quarter frame,
                                  and changed only when a new tempo persists
  beats                           a phase-locked clock: each tempo update aligns it to
                                  a pulse train cross-correlated with the onsets
  downbeats                       which of the four beats carries the most low-end onset
                                  and spectral change, accumulated over many bars
  phrases                         8-bar phrases: bar-by-bar novelty (how different the
                                  last four bars are from the four before) accumulated by
                                  position mod 8, so boundaries are predicted, not just
                                  noticed after the fact; plus drops (a bar that starts
                                  much louder and bassier than the last four) and builds
                                  (rising highs and onset density over falling bass)
"""
import collections
import math
import os
import shutil
import subprocess
import sys
import threading
import time

import numpy as np

SR = 48000
HOP = 512
WIN = 2048
FPS = SR / HOP                  # analysis frames a second
NBANDS = 24
HIST_S = 8.0                    # onset history used for tempo
KICK_LAG = 8                    # hops (85 ms) to see whether a low onset decayed like a kick
TEMPO_EVERY = 24                # hops between tempo/phase updates (~0.25 s)
BPM_MIN, BPM_MAX, BPM_PRIOR = 70.0, 190.0, 125.0
PHRASE_BARS = 8


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def _bands():
    """Triangular log-spaced bands from 30 Hz to 16 kHz, as a (bins, bands) matrix."""
    freqs = np.fft.rfftfreq(WIN, 1 / SR)
    edges = np.geomspace(30, 16000, NBANDS + 2)
    m = np.zeros((len(freqs), NBANDS), np.float32)
    for b in range(NBANDS):
        lo, mid, hi = edges[b], edges[b + 1], edges[b + 2]
        up = (freqs - lo) / (mid - lo)
        down = (hi - freqs) / (hi - mid)
        m[:, b] = np.clip(np.minimum(up, down), 0, None)
    m /= np.maximum(m.sum(0, keepdims=True), 1e-9)
    centres = edges[1:-1]
    return m, centres


class Analyzer:
    def __init__(self):
        self.B, self.centres = _bands()
        self.low = self.centres < 150
        self.mid = (self.centres >= 150) & (self.centres < 2500)
        self.high = self.centres >= 5000
        self.window = np.hanning(WIN).astype(np.float32)
        self.buf = np.zeros(WIN, np.float32)
        self.pending = np.zeros(0, np.float32)
        self.wave = np.zeros((1024, 2), np.float32)          # the latest samples, for scopes
        self.prev = np.zeros(NBANDS, np.float32)
        self.peak_bands = np.full(NBANDS, 1e-3, np.float32)
        self.peak_rms = 1e-3
        self.peak_flux = 1e-3
        n = int(HIST_S * FPS)
        self.onset = collections.deque([0.0] * n, maxlen=n)           # all onsets, for display and events
        self.beat_onset = collections.deque([0.0] * n, maxlen=n)      # kick-weighted, KICK_LAG hops behind
        q = KICK_LAG + 2                                             # one hop before the onset, too
        self.low_e = collections.deque([0.0] * q, maxlen=q)
        self.low_flux_q = collections.deque([0.0] * q, maxlen=q)
        self.body_flux_q = collections.deque([0.0] * q, maxlen=q)
        self.lowflux = collections.deque([0.0] * 8, maxlen=8)
        self.frames = 0
        self.t = 0.0
        self.lock = threading.Lock()
        # features for the current frame
        self.rms = 0.0
        self.level = 0.0
        self.bands = np.zeros(NBANDS, np.float32)
        self.flux = 0.0
        self.kick = self.snare = self.hat = 0.0
        self.counts = dict(beat=0, bar=0, phrase=0, drop=0, kick=0, snare=0, hat=0, onset=0)
        # tempo and beat clock
        self.bpm = 0.0
        self.conf = 0.0
        self.candidate, self.cand_hits = 0.0, 0
        self.period = FPS * 60 / 120.0
        self.phase = 0.0                                     # 0..1 through the current beat
        self.locked = False
        # bars and phrases
        self.down_acc = np.zeros(4, np.float32)
        self.downbeat = 0                                    # which beat count mod 4 is the one
        self.iv_e, self.iv_rms, self.iv_low, self.iv_n = np.zeros(NBANDS, np.float32), 0.0, 0.0, 0
        self.beats = collections.deque(maxlen=64)            # per beat: spectrum, loudness, low onset
        self.bars = collections.deque(maxlen=64)             # (bar index, bands + rms + low onset)
        self.last_drop = -999
        self.big_errs = []
        self.kick_hist = collections.deque(maxlen=int(2 * FPS))   # (hop, kick strength), lagged
        self.iv_start = 0
        self.iv_lowlin = 0.0
        self.phrase_acc = np.zeros(PHRASE_BARS, np.float32)
        self.phrase_off = 0
        self.bar_in_phrase = 0
        self.build = 0.0
        self.intensity = 0.0
        self.bar_rms_hist = collections.deque(maxlen=256)
        self.taps = collections.deque(maxlen=8)
        self.manual_until = 0.0
        self.onset_gate = collections.deque([0.0] * 32, maxlen=32)
        # impact: how sharply the last ~0.4 s contrasts with the ~6 s before it
        self.imp_low = collections.deque(maxlen=int(6.5 * FPS))     # linear low-end energy per hop
        self.imp_rms = collections.deque(maxlen=int(6.5 * FPS))
        self.imp_vec = collections.deque(maxlen=int(6.5 * FPS))     # log band energies per hop
        self.impact = 0.0              # an envelope: jumps on a big change, fades over about a bar
        self.impact_score = 0.0        # the contrast right now
        self.last_impact = -1e9
        self.impact_armed = True
        self.counts["impact"] = 0

    # ---- input

    def feed(self, stereo):
        """stereo: float32 (n, 2) in -1..1."""
        if not len(stereo):
            return
        k = min(len(stereo), len(self.wave))
        self.wave = np.concatenate([self.wave[k:], stereo[-k:]])
        self.pending = np.concatenate([self.pending, stereo.mean(1)])
        while len(self.pending) >= HOP:
            hop, self.pending = self.pending[:HOP], self.pending[HOP:]
            self._hop(hop)

    # ---- one analysis frame

    def _hop(self, hop):
        self.buf = np.concatenate([self.buf[HOP:], hop])
        mag = np.abs(np.fft.rfft(self.buf * self.window))
        e = np.log1p(mag @ self.B * 4.0)
        diff = np.maximum(e - self.prev, 0)
        self.prev = e
        flux = float(diff.sum())
        kick, snare, hat = float(diff[self.low].sum()), float(diff[self.mid].sum()), float(diff[self.high].sum())
        rms = float(np.sqrt(np.mean(hop * hop)))

        decay = 0.9993                                       # peaks halve in ~10 s
        self.peak_bands = np.maximum(e, self.peak_bands * decay)
        self.peak_rms = max(rms, self.peak_rms * decay, 1e-4)
        self.peak_flux = max(flux, self.peak_flux * decay, 1e-4)

        with self.lock:
            self.frames += 1
            self.t = self.frames / FPS
            self.rms = rms
            self.level = min(1.0, rms / self.peak_rms)
            self.bands = np.clip(e / np.maximum(self.peak_bands, 0.3), 0, 1)
            self.flux = min(1.0, flux / self.peak_flux)
            self.onset.append(flux)
            self.lowflux.append(kick)
            # Kicks mark the beat, but off-beat bass lands in the same bands. A kick's low end
            # is gone within ~80 ms and a bass note sustains, so weight each low onset by how
            # much of the energy it *added* has gone again KICK_LAG hops later. (Total energy
            # won't do: a kick on top of a held bass note never falls far.) Hats, often on the
            # off-beat, are left out.
            low_lin = float(np.expm1(e[self.low]).sum())
            self.low_e.append(low_lin)
            self.low_flux_q.append(kick)
            self.body_flux_q.append(flux - hat)
            before, peak, after = self.low_e[0], max(self.low_e[1], self.low_e[2]), self.low_e[-1]
            rise = peak - before
            decayed = float(np.clip((peak - after) / rise, 0, 1)) if rise > 1e-6 else 0.0
            kickness = self.low_flux_q[1] * decayed
            self.beat_onset.append(3.0 * kickness + 0.3 * self.body_flux_q[1])
            self.kick_hist.append((self.frames - KICK_LAG - 1, kickness))
            self._events(flux, kick, snare, hat)
            self._beat_clock(e, rms)
            self._impact(e, rms)
            if self.frames % TEMPO_EVERY == 0 and self.frames > 3 * FPS:
                self._tempo()

    def _events(self, flux, kick, snare, hat):
        """Onset events: a peak well above the recent median, per range."""
        self.onset_gate.append(flux)
        med = float(np.median(self.onset_gate))
        if flux > med * 1.8 + 0.05 * self.peak_flux and flux >= max(list(self.onset_gate)[-3:]):
            self.counts["onset"] += 1
        tot = kick + snare + hat + 1e-9
        for name, v in (("kick", kick), ("snare", snare), ("hat", hat)):
            prev = getattr(self, name)
            if v > 0.25 * self.peak_flux and v / tot > 0.35 and v > prev * 1.5:
                self.counts[name] += 1
            setattr(self, name, 0.6 * prev + 0.4 * v)

    # ---- impact: the big changes, whatever their loudness

    def _impact(self, e, rms):
        """A big change in the music: the low end arriving (a warm bass drop needn't be loud),
        the sound turning into something new, or the level jumping. "New" is the point: the
        last ~0.4 s is compared with the *strongest* and *most similar* moments of the ~6 s
        before it, not their average, so a stab that recurs every couple of bars, already
        heard, isn't news, while a drop that outdoes everything recent is."""
        self.imp_low.append(float(np.expm1(e[self.low]).sum()))
        self.imp_rms.append(rms)
        self.imp_vec.append(e)
        W, gap = int(0.4 * FPS), int(0.6 * FPS)
        n = len(self.imp_low)
        if n < W + gap + int(5 * FPS):                           # a fair memory first: at the start everything is new
            return
        if self.frames % 2:                                       # every other hop is plenty
            self.impact *= math.exp(-1 / (FPS * 0.8))
            return

        def windows(a):
            cs = np.concatenate([np.zeros((1,) + a.shape[1:], np.float64), np.cumsum(a, 0, dtype=np.float64)])
            return (cs[W:] - cs[:-W]) / W                          # the mean of every W-hop window

        low = windows(np.fromiter(self.imp_low, np.float32))
        lvl = windows(np.fromiter(self.imp_rms, np.float32))
        vec = windows(np.array(self.imp_vec, np.float32))
        past = slice(0, len(low) - gap)
        s_low, s_rms, sv = low[-1], lvl[-1], vec[-1]
        bass_in = math.log2((s_low + 1e-6) / (low[past].max() + 1e-6))
        louder = math.log2((s_rms + 1e-6) / (lvl[past].max() + 1e-6))
        pv = vec[past][::4]
        cos = pv @ sv / (np.linalg.norm(pv, axis=1) * np.linalg.norm(sv) + 1e-9)
        change = 1 - float(cos.max())                             # unlike even the nearest recent moment
        score = max(np.clip((bass_in - 0.2) / 1.2, 0, 1),         # past the biggest recent low end
                    np.clip((change - 0.01) * 25, 0, 1),           # a sound not heard in the last 6 s
                    np.clip((louder - 0.25) / 0.8, 0, 1))          # past the loudest recent moment
        if s_rms < 0.004:                                          # silence isn't an event
            score = 0.0
        self.impact_score = float(score)
        # One hit per change: once it fires, it re-arms only after the contrast has settled.
        if score < 0.3:
            self.impact_armed = True
        if score > 0.55 and self.impact_armed and self.frames - self.last_impact > 2 * FPS:
            self.counts["impact"] += 1
            self.last_impact = self.frames
            self.impact_armed = False
            self.impact = max(self.impact, float(score))
        self.impact *= math.exp(-2 / (FPS * 0.8))

    # ---- tempo: autocorrelation of onset strength

    def _tempo(self):
        o = np.array(self.beat_onset, np.float32)
        o = o - np.convolve(o, np.ones(16) / 16, mode="same")   # take away the slow swell
        o = np.maximum(o, 0)
        if o.std() < 1e-6:
            self.conf = 0.0
            return
        n = len(o)
        f = np.fft.rfft(o, 2 * n)
        acf = np.fft.irfft(f * np.conj(f))[:n]
        acf /= acf[0] + 1e-9

        def at(lag):
            i = int(lag)
            fr = lag - i
            if i + 1 >= n:
                return 0.0
            return acf[i] * (1 - fr) + acf[i + 1] * fr

        lags = np.arange(FPS * 60 / BPM_MAX, FPS * 60 / BPM_MIN, 0.25)
        # The beat repeats, and so do the bar (4x) and two bars (8x); the half lag is the
        # off-beat. Scoring the multiples is what rejects the 3:2 alias that breakbeats
        # invite (174 heard as 116: kick, kick-on-the-and, every 1.5 beats), which has no
        # two-bar repeat to match.
        scores = np.array([at(l) + 0.5 * at(2 * l) + 0.35 * at(4 * l) + 0.35 * at(8 * l) + 0.3 * at(l / 2)
                           for l in lags])
        bpms = FPS * 60 / lags
        prior = np.exp(-0.5 * (np.log2(bpms / BPM_PRIOR) / 1.3) ** 2)
        s = scores * prior
        k = int(np.argmax(s))
        cand = float(bpms[k])
        self.conf = float(np.clip((s[k] - np.median(s)) / (np.std(s) + 1e-9) / 4, 0, 1))

        if time.monotonic() < self.manual_until:
            pass                                             # a tapped tempo holds for a while
        elif self.bpm == 0 or abs(cand - self.bpm) / self.bpm < 0.04:
            self.bpm = cand if self.bpm == 0 else 0.8 * self.bpm + 0.2 * cand
            self.cand_hits = 0
        else:
            # A new tempo has to persist before it's believed: ~2 s for an unrelated one, and
            # ~6 s for one metrically related to ours (3:2, 2:3, 3x, 1/3), which is usually a
            # pattern fooling the autocorrelation rather than the music changing.
            # An exact octave (2x, 1/2) is the same groove: never switch to it, the display
            # would only jump.
            ratio = cand / self.bpm
            octave = min(abs(ratio - r) / r for r in (2, 0.5)) < 0.04
            related = min(abs(ratio - r) / r for r in (1.5, 2 / 3, 3, 1 / 3)) < 0.04
            if self.candidate and abs(cand - self.candidate) / self.candidate < 0.04:
                self.cand_hits += 1
            else:
                self.candidate, self.cand_hits = cand, 1
            if not octave and self.cand_hits >= (24 if related else 8):
                self.bpm, self.cand_hits = cand, 0
        self.period = FPS * 60 / self.bpm
        self._align_phase(o)

    def _align_phase(self, o):
        """Pull the beat clock towards the pulse train that best fits the last 4 s of onsets."""
        P = self.period
        recent = o[-int(4 * FPS):]
        n = len(recent)
        offs = np.arange(0, P, 0.5)
        vals = np.zeros(len(offs))
        for i, off in enumerate(offs):
            idx = n - 1 - off - np.arange(0, n - 1 - off, P)
            idx = idx[idx >= 0]
            w = np.exp(-np.arange(len(idx)) * 0.15)          # recent beats count more
            vals[i] = float((np.interp(idx, np.arange(n), recent) * w).sum())
        k = int(np.argmax(vals))
        best_off = offs[k]
        # How decisively one phase wins: high in a steady groove, low in rolls and risers,
        # where every offset scores about the same. Corrections scale with it, so the clock
        # coasts through fills instead of creeping off the beat.
        contrast = float((vals[k] - np.median(vals)) / (vals[k] + 1e-9))
        gain = 0.35 * float(np.clip((contrast - 0.15) / 0.35, 0, 1))
        want = ((best_off + KICK_LAG) / P) % 1.0             # best_off frames before the lagged end
        err = (want - self.phase + 0.5) % 1.0 - 0.5
        if abs(err) <= 0.12:
            self.phase = (self.phase + gain * err) % 1.0
            self.big_errs = []
        else:
            # A big jump has to show up three updates running and agree with itself: fills,
            # rolls and risers pull the onsets around for a bar or two, and the clock should
            # coast through them.
            self.big_errs.append(err)
            recent = self.big_errs[-3:]
            if len(recent) == 3 and np.std(recent) < 0.08 and gain > 0.1:
                self.phase = (self.phase + float(np.mean(recent))) % 1.0
                self.big_errs = []
        self.locked = abs(err) < 0.1 and self.conf > 0.3

    # ---- beats, bars, phrases

    def _beat_clock(self, e, rms):
        # statistics of the beat interval in progress: its mean spectrum, loudness, and the
        # biggest low-end onset in its first ~60 ms (where a kick on the beat would land)
        self.iv_e += e
        self.iv_rms += rms
        self.iv_lowlin += float(np.expm1(e[self.low]).sum())
        if self.iv_n < 6:
            self.iv_low = max(self.iv_low, float(self.lowflux[-1]))
        self.iv_n += 1
        if self.bpm == 0:
            return
        self.phase += 1.0 / self.period
        if self.phase < 1.0:
            return
        self.phase -= 1.0
        self.counts["beat"] += 1
        k = self.counts["beat"]                              # the beat starting now
        n = max(1, self.iv_n)
        kick = max([v for h, v in self.kick_hist if self.iv_start - 2 <= h <= self.iv_start + 6] or [0.0])
        done = dict(vec=self.iv_e / n, rms=self.iv_rms / n, low=self.iv_low / self.peak_flux, kick=kick,
                    lowlin=self.iv_lowlin / n)
        self.iv_e, self.iv_rms, self.iv_low, self.iv_n = np.zeros(NBANDS, np.float32), 0.0, 0.0, 0
        self.iv_lowlin = 0.0
        self.iv_start = self.frames
        self.beats.append(done)                              # stats of beat k-1
        j = k - 1
        # downbeat evidence for beat j: its low-end onset, and how much the music changed into it
        if len(self.beats) >= 2:
            change = float(np.abs(done["vec"] - self.beats[-2]["vec"]).mean())
            self.down_acc *= 0.98
            self.down_acc[j % 4] += 0.5 * done["low"] + 4.0 * change
            best = int(np.argmax(self.down_acc))
            if best != self.downbeat and self.down_acc[best] > 1.1 * self.down_acc[self.downbeat]:
                self.downbeat = best
        # a drop: the bar that began at beat j came in much louder and bassier than before
        # (in linear energy: logs flatten a 5-10x jump in the low end into a ratio under 2)
        if (j - self.downbeat) % 4 == 0 and len(self.beats) >= 17:
            before = list(self.beats)[-17:-1]
            low = done["lowlin"] / (np.mean([b["lowlin"] for b in before]) + 1e-9)
            loud = done["rms"] / (np.mean([b["rms"] for b in before]) + 1e-9)
            if low > 6.0 and loud > 1.2 and self.counts["beat"] - self.last_drop > 16:
                self.counts["drop"] += 1
                self.last_drop = self.counts["beat"]
                self.phrase_acc[self.bar_index(j) % PHRASE_BARS] += 3.0    # drops land on phrase boundaries
        if (k - self.downbeat) % 4 == 0:
            self._bar()

    def bar_index(self, beat):
        return (beat - self.downbeat) // 4

    def _bar(self):
        """A bar starts now, at beat k: close the bar before it and update the phrase grid."""
        self.counts["bar"] += 1
        k = self.counts["beat"]
        m = self.bar_index(k)                                # the bar starting now
        last4 = list(self.beats)[-4:]
        v = np.concatenate([np.mean([b["vec"] for b in last4], 0), [np.mean([b["rms"] for b in last4])],
                            [np.mean([b["low"] for b in last4])]])
        self.bars.append((m - 1, v))
        self.bar_rms_hist.append(v[NBANDS])
        recent = [vv for idx, vv in self.bars if m - 8 <= idx <= m - 1]
        if len(recent) == 8:
            # novelty four bars late: bars m-8..m-5 against m-4..m-1; the boundary was bar m-4
            a, b = np.mean(recent[:4], 0), np.mean(recent[4:], 0)
            na, nb_ = a[:NBANDS], b[:NBANDS]
            cos = float(na @ nb_ / (np.linalg.norm(na) * np.linalg.norm(nb_) + 1e-9))
            energy = abs(math.log((b[NBANDS] + 1e-6) / (a[NBANDS] + 1e-6)))
            self.phrase_acc *= 0.93
            self.phrase_acc[(m - 4) % PHRASE_BARS] += (1 - cos) * 20 + energy
            best = int(np.argmax(self.phrase_acc))
            if self.phrase_acc[best] > 1.2 * self.phrase_acc[self.phrase_off]:
                self.phrase_off = best
        self.bar_in_phrase = (m - self.phrase_off) % PHRASE_BARS
        if self.bar_in_phrase == 0:
            self.counts["phrase"] += 1
        # a build: highs and onset density rising across eight bars while the bass thins
        if len(recent) == 8:
            x = np.arange(8)
            hi = [bb[:NBANDS][self.high].mean() for bb in recent]
            lo = [bb[:NBANDS][self.low].mean() for bb in recent]
            slope = lambda y: float(np.polyfit(x, y, 1)[0] / (np.mean(np.abs(y)) + 1e-6))
            self.build = float(np.clip((slope(hi) - slope(lo)) * 4, 0, 1))
        h = np.array(self.bar_rms_hist)
        self.intensity = float((h < h[-1]).mean()) if len(h) > 4 else 0.5

    # ---- people can help: tap the tempo, mark the one

    def tap(self):
        now = time.monotonic()
        self.taps.append(now)
        if len(self.taps) >= 3:
            gaps = np.diff(self.taps)
            gaps = gaps[gaps < 1.5]
            if len(gaps) >= 2:
                with self.lock:
                    self.bpm = 60.0 / float(np.median(gaps))
                    self.period = FPS * 60 / self.bpm
                    self.phase = 0.0
                    self.manual_until = now + 8.0
        else:
            with self.lock:
                self.phase = 0.0

    def mark_downbeat(self):
        with self.lock:
            # the beat that just went by (or is about to) is beat one
            beat = self.counts["beat"] + (1 if self.phase > 0.5 else 0)
            self.downbeat = beat % 4
            self.down_acc[:] = 0
            self.down_acc[self.downbeat] = 5.0

    def shift_phrase(self, bars):
        with self.lock:
            self.phrase_off = (self.phrase_off + bars) % PHRASE_BARS
            self.phrase_acc[:] = 0
            self.phrase_acc[self.phrase_off] = 5.0
            m = self.bar_index(self.counts["beat"])
            self.bar_in_phrase = (m - self.phrase_off) % PHRASE_BARS

    def snapshot(self):
        with self.lock:
            return dict(t=self.t, level=self.level, rms=self.rms, bands=self.bands.copy(), flux=self.flux,
                        kick=min(1.0, self.kick / self.peak_flux * 2), snare=min(1.0, self.snare / self.peak_flux * 2),
                        hat=min(1.0, self.hat / self.peak_flux * 3), counts=dict(self.counts), bpm=self.bpm,
                        conf=self.conf, phase=self.phase, locked=self.locked,
                        beat_in_bar=(self.counts["beat"] - self.downbeat) % 4,
                        bar_in_phrase=self.bar_in_phrase, build=self.build, intensity=self.intensity,
                        manual=time.monotonic() < self.manual_until, impact=self.impact,
                        impact_score=self.impact_score,
                        wave=self.wave.copy(), onset_hist=np.array(list(self.onset)[-256:], np.float32) / self.peak_flux)


# ---------------------------------------------------------------- sources

class _Delayed:
    """Feeds the analyzer from a reader thread, held back by `delay` seconds."""

    def __init__(self, analyzer, delay):
        self.an, self.delay = analyzer, delay
        self.queue = collections.deque()

    def push(self, chunk):
        now = time.monotonic()
        self.queue.append((now, chunk))
        while self.queue and self.queue[0][0] <= now - self.delay:
            self.an.feed(self.queue.popleft()[1])


class _ProcessSource:
    """Raw s16le stereo 48 kHz from a subprocess (parec, arecord or ffmpeg)."""
    realtime = True

    def __init__(self, cmd, analyzer, delay, pace=False):
        self.cmd, self.an, self.pace = cmd, analyzer, pace
        self.feed = _Delayed(analyzer, delay)
        self.proc = None
        self.alive = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        chunk = HOP * 4                                      # bytes: 512 frames of 2 x s16
        while self.alive:
            try:
                self.proc = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                t0, got = time.monotonic(), 0
                while self.alive:
                    b = self.proc.stdout.read(chunk)
                    if not b:
                        break
                    a = np.frombuffer(b[: len(b) // 4 * 4], np.int16).reshape(-1, 2).astype(np.float32) / 32768
                    if self.pace:                            # a file: hand it over in real time
                        got += len(a)
                        ahead = got / SR - (time.monotonic() - t0)
                        if ahead > 0:
                            time.sleep(ahead)
                    self.feed.push(a)
            except OSError as e:
                log(f"audio: {e}")
            if self.alive:
                log("audio: source ended; restarting in 2 s")
                time.sleep(2)

    def pump(self, dt):
        pass

    def close(self):
        self.alive = False
        if self.proc:
            self.proc.kill()


class _FileSteps:
    """A decoded track, stepped with the frames: for previews, where time isn't real."""
    realtime = False

    def __init__(self, path, start, analyzer):
        self.an = analyzer
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-i", path, "-f", "s16le",
                              "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
        self.pcm = np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float32) / 32768
        self.pos = 0.0

    def pump(self, dt):
        n = int(self.pos + dt * SR) - int(self.pos)
        a = self.pcm[int(self.pos):int(self.pos) + n]
        self.pos += dt * SR
        self.an.feed(a)

    def close(self):
        pass


def default_delay():
    """How far to hold the analysis back. Bluetooth (A2DP, SBC) plays ~0.2 s behind its
    monitor; the panel itself shows a frame ~30-50 ms after the analysis sees it (render,
    transport, the card's bank flip), so the hold-back is the difference. Wired output
    is about as quick as the panel, so nothing."""
    try:
        sink = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=2).stdout
        return 0.15 if sink.startswith("bluez") else 0.0
    except (OSError, subprocess.TimeoutExpired):
        return 0.03


def audio_source(spec, delay=None, preview=False):
    """An Audio for run.py's --audio spec, or None."""
    kind, _, arg = spec.partition(":")
    if kind == "none" or not kind:
        return None
    an = Analyzer()
    if kind == "pulse":
        if not shutil.which("parec"):
            log("audio: no parec; running without audio")
            return None
        src = arg or subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True).stdout.strip() + ".monitor"
        delay = default_delay() if delay is None else delay
        cmd = ["parec", "-d", src, "--format=s16le", f"--rate={SR}", "--channels=2", "--raw",
               "--latency-msec=10", "--process-time-msec=5"]
        log(f"audio: {src}, delay {delay * 1000:.0f} ms")
        return Audio(an, _ProcessSource(cmd, an, delay))
    if kind == "alsa":
        cmd = ["arecord", "-q", "-D", arg or "default", "-f", "S16_LE", "-r", str(SR), "-c", "2", "-t", "raw",
               "--buffer-time=20000"]
        return Audio(an, _ProcessSource(cmd, an, delay or 0.0))
    if kind == "file":
        path, _, start = arg.partition("@")
        path = os.path.expanduser(path)
        if preview:
            return Audio(an, _FileSteps(path, float(start or 0), an))
        cmd = ["ffmpeg", "-v", "error", "-ss", str(float(start or 0)), "-i", path, "-f", "s16le", "-ac", "2",
               "-ar", str(SR), "-"]
        return Audio(an, _ProcessSource(cmd, an, delay or 0.0, pace=True))
    raise SystemExit(f"unknown audio source {spec!r}")


# ---------------------------------------------------------------- what demos see

class AudioState:
    """One render frame's view of the music. Events are true for the frame they happen in."""

    def __init__(self, snap, prev_counts, t_frame):
        self.__dict__.update(snap)
        c = snap["counts"]
        p = prev_counts or c
        self.beat = c["beat"] > p["beat"]
        self.bar = c["bar"] > p["bar"] and self.beat_in_bar == 0
        self.phrase = c["phrase"] > p["phrase"]
        self.drop = c["drop"] > p["drop"]
        self.impact_hit = c["impact"] > p.get("impact", c["impact"])
        self.kick_hit = c["kick"] > p["kick"]
        self.snare_hit = c["snare"] > p["snare"]
        self.hat_hit = c["hat"] > p["hat"]
        self.onset = c["onset"] > p["onset"]
        self.bar_phase = (self.beat_in_bar + self.phase) / 4
        self.phrase_phase = (self.bar_in_phrase + self.bar_phase) / PHRASE_BARS
        self.bass = float(self.bands[:5].mean())
        self.mid = float(self.bands[5:15].mean())
        self.treble = float(self.bands[15:].mean())
        self.live = True


class Audio:
    def __init__(self, analyzer, source):
        self.an, self.src = analyzer, source
        self.prev = None

    @property
    def realtime(self):
        return self.src.realtime

    def frame(self, dt):
        """Advance (for stepped sources) and return this frame's AudioState."""
        self.src.pump(dt)
        snap = self.an.snapshot()
        st = AudioState(snap, self.prev, time.monotonic())
        self.prev = snap["counts"]
        return st

    def tap(self):
        self.an.tap()

    def mark_downbeat(self):
        self.an.mark_downbeat()

    def shift_phrase(self, bars):
        self.an.shift_phrase(bars)

    @property
    def delay(self):
        return getattr(getattr(self.src, "feed", None), "delay", 0.0)

    @delay.setter
    def delay(self, d):
        if hasattr(self.src, "feed"):
            self.src.feed.delay = min(1.0, max(0.0, d))

    def close(self):
        self.src.close()


class SilentState:
    """What demos see with no audio: a steady 120 BPM, quiet, so visualizers still move."""

    def __init__(self, t, prev_beat):
        self.live = False
        beats = t * 2.0
        self.phase = beats % 1.0
        nb = int(beats)
        self.beat = nb > prev_beat
        self.counts = dict(beat=nb)
        self.beat_in_bar = nb % 4
        self.bar = self.beat and self.beat_in_bar == 0
        self.bar_in_phrase = (nb // 4) % PHRASE_BARS
        self.phrase = self.bar and self.bar_in_phrase == 0
        self.bar_phase = (self.beat_in_bar + self.phase) / 4
        self.phrase_phase = (self.bar_in_phrase + self.bar_phase) / PHRASE_BARS
        self.bpm, self.conf, self.locked = 120.0, 0.0, False
        pulse = math.exp(-self.phase * 6)
        self.level = self.flux = 0.15 + 0.2 * pulse
        self.bands = np.full(NBANDS, 0.15, np.float32) + 0.2 * pulse * np.linspace(1, 0.3, NBANDS)
        self.bass, self.mid, self.treble = 0.3 * pulse + 0.1, 0.15, 0.1
        self.kick, self.snare, self.hat = pulse, 0.0, 0.0
        self.kick_hit = self.beat
        self.snare_hit = self.hat_hit = self.drop = False
        self.onset = self.beat
        self.build, self.intensity = 0.0, 0.5
        self.manual = False
        self.impact = self.impact_score = 0.0
        self.impact_hit = False
        self.wave = np.zeros((1024, 2), np.float32)
        self.onset_hist = np.zeros(256, np.float32)
        self.rms = 0.0
