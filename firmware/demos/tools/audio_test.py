#!/usr/bin/env python3
"""Score the audio analyzer against music with known beats, bars and phrases.

    tools/audio_test.py synth [--bpm 128] [--wav out.wav]   a generated club track, scored
    tools/audio_test.py file PATH [--start S] [--seconds N]  a real track: tempo over time only

The synthetic track is four-on-the-floor house: a kick on every beat, so the
downbeat can't come from the kick; it has to come from the bass line and the
changes at bar starts. Sections are 8 bars: intro (kick, hats), groove (+ bass,
claps), breakdown (pads, no kick), build (snare roll, rising noise), drop
(everything, a crash on the one). Scores:

    beats      F-measure of beat events within 70 ms of the true beats
    tempo      the analyzer's BPM against the truth, after it settles
    downbeats  share of the analyzer's bar starts that land on true downbeats
    phrases    share of its phrase starts that land on true 8-bar boundaries
    drops      drop events within one bar of the true drops
Scores count from 16 bars in, once the analyzer has had time to listen.
"""
import argparse
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pfd.audio import FPS, SR, Analyzer  # noqa: E402

TOL = 0.07


def synth(bpm=128.0, sections=("intro", "groove", "groove", "breakdown", "build", "drop", "drop", "groove"), seed=1):
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    bars = 8 * len(sections)
    n = int(bars * 4 * beat * SR) + SR
    out = np.zeros(n, np.float32)
    t_beats, t_down, t_phrase, t_drop = [], [], [], []

    def add(at, sig, gain=1.0):
        i = int(at * SR)
        j = min(n, i + len(sig))
        out[i:j] += sig[:j - i] * gain

    def env(dur, decay):
        t = np.arange(int(dur * SR)) / SR
        return t, np.exp(-t * decay)

    t, e = env(0.35, 18)
    kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-t * 30)) * t) * e
    t, e = env(0.2, 30)
    clap = rng.normal(0, 1, len(t)) * e * 0.5
    t, e = env(0.05, 120)
    hat = np.diff(rng.normal(0, 1, len(t) + 1)) * e * 0.25
    t, e = env(1.5, 2.5)
    crash = np.diff(rng.normal(0, 1, len(t) + 1)) * e * 0.4
    roots = [55.0, 55.0 * 2 ** (3 / 12), 55.0 * 2 ** (-2 / 12), 55.0 * 2 ** (5 / 12)]    # a four-bar bass line

    for s, sec in enumerate(sections):
        for b in range(8):
            bar = s * 8 + b
            t0 = bar * 4 * beat
            t_down.append(t0)
            if b == 0:
                t_phrase.append(t0)
            if sec == "drop" and b == 0 and sections[s - 1] == "build":
                t_drop.append(t0)
            root = roots[bar % 4]
            for q in range(4):
                tb = t0 + q * beat
                t_beats.append(tb)
                if sec in ("intro", "groove", "drop"):
                    add(tb, kick, 0.9)
                if sec in ("groove", "drop") and q in (1, 3):
                    add(tb, clap)
                if sec != "breakdown":
                    add(tb + beat / 2, hat)
                if sec == "build":                          # a snare roll that doubles each two bars
                    div = 2 ** (1 + b // 2)
                    for k in range(div):
                        add(tb + k * beat / div, clap, 0.25 + 0.6 * b / 8)
            if sec in ("groove", "drop", "breakdown"):
                # the bass plays on the one and off-beats, a new note each bar
                tt = np.arange(int(4 * beat * SR)) / SR
                gate = ((tt % beat) > beat / 2) | (tt < beat)
                bass = np.sin(2 * np.pi * root * tt) * gate * (0.5 if sec != "breakdown" else 0.0)
                pad = (np.sin(2 * np.pi * root * 4 * tt) + np.sin(2 * np.pi * root * 5 * tt)) * 0.06
                add(t0, bass + (pad if sec in ("breakdown", "drop") else 0))
            if sec == "drop" and b == 0:
                add(t0, crash)
            if sec == "build":
                tt = np.arange(int(4 * beat * SR)) / SR
                riser = np.diff(rng.normal(0, 1, len(tt) + 1)) * (b / 8 + tt / (4 * beat) / 8) * 0.2
                add(t0, riser)
    out /= np.abs(out).max() * 1.1
    stereo = np.stack([out, out], 1)
    return stereo, dict(beats=np.array(t_beats), down=np.array(t_down), phrase=np.array(t_phrase),
                        drop=np.array(t_drop), bpm=bpm, beat=beat)


def run(pcm):
    """Feed the analyzer hop by hop, recording when each kind of event fires and the tempo."""
    an = Analyzer()
    events = {k: [] for k in ("beat", "bar", "phrase", "drop")}
    bpm = []
    prev = dict(an.counts)
    step = 512
    for i in range(0, len(pcm) - step, step):
        an.feed(pcm[i:i + step])
        t = (i + step) / SR
        for k in events:
            if an.counts[k] > prev[k]:
                events[k].append(t)
        prev = dict(an.counts)
        bpm.append((t, an.bpm, an.conf))
    return {k: np.array(v) for k, v in events.items()}, np.array(bpm)


def hits(det, truth, tol):
    if not len(det) or not len(truth):
        return np.zeros(len(det), bool)
    d = np.abs(det[:, None] - truth[None, :]).min(1)
    return d <= tol


def score(ev, bpm, truth, settle):
    out = {}
    b = ev["beat"][ev["beat"] > settle]
    tb = truth["beats"][truth["beats"] > settle]
    # the analyzer reports a beat when its clock wraps: allow for the analysis latency
    lat = np.median([d for d in (b[:, None] - tb[None, :]).ravel() if abs(d) < 0.15]) if len(b) else 0
    p = hits(b - lat, tb, TOL).mean() if len(b) else 0
    r = hits(tb, b - lat, TOL).mean() if len(tb) else 0
    out["beats F"] = 2 * p * r / (p + r + 1e-9)
    out["beat latency ms"] = lat * 1000
    good = bpm[bpm[:, 0] > settle]
    est = np.median(good[:, 1])
    out["tempo"] = f"{est:.2f} (true {truth['bpm']:.2f}, err {100 * (est - truth['bpm']) / truth['bpm']:+.2f} %)"
    bars = ev["bar"][ev["bar"] > settle] - lat
    out["downbeats"] = hits(bars, truth["down"], TOL).mean() if len(bars) else 0
    ph = ev["phrase"][ev["phrase"] > settle] - lat
    out["phrases"] = hits(ph, truth["phrase"], TOL).mean() if len(ph) else 0
    out["phrase events"] = f"{len(ph)} (true {int((truth['phrase'] > settle).sum())})"
    dr = ev["drop"] - lat
    out["drops"] = f"{int(hits(dr, truth['drop'], truth['beat'] * 4).sum())} of {len(truth['drop'])} found, " \
                   f"{int((~hits(dr, truth['drop'], truth['beat'] * 4)).sum())} false"
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("synth")
    s.add_argument("--bpm", type=float, default=128)
    s.add_argument("--wav")
    f = sub.add_parser("file")
    f.add_argument("path")
    f.add_argument("--start", type=float, default=0)
    f.add_argument("--seconds", type=float, default=120)
    a = p.parse_args()
    if a.cmd == "synth":
        pcm, truth = synth(a.bpm)
        if a.wav:
            import wave
            with wave.open(a.wav, "wb") as w:
                w.setnchannels(2), w.setsampwidth(2), w.setframerate(SR)
                w.writeframes((pcm * 32767).astype(np.int16).tobytes())
        ev, bpm = run(pcm)
        settle = 16 * 4 * truth["beat"]
        for k, v in score(ev, bpm, truth, settle).items():
            print(f"  {k:16s} {v:.3f}" if isinstance(v, float) else f"  {k:16s} {v}")
    else:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a.start), "-t", str(a.seconds), "-i",
                              os.path.expanduser(a.path), "-f", "s16le", "-ac", "2", "-ar", str(SR), "-"],
                             capture_output=True, check=True).stdout
        pcm = np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float32) / 32768
        ev, bpm = run(pcm)
        for t0 in range(0, int(a.seconds), 10):
            seg = bpm[(bpm[:, 0] >= t0) & (bpm[:, 0] < t0 + 10)]
            if len(seg):
                print(f"  {t0:4d}-{t0 + 10:<4d}s  bpm {np.median(seg[:, 1]):6.1f}  conf {np.median(seg[:, 2]):.2f}"
                      f"  beats {int(((ev['beat'] >= t0) & (ev['beat'] < t0 + 10)).sum())}"
                      f"  bars {int(((ev['bar'] >= t0) & (ev['bar'] < t0 + 10)).sum())}"
                      f"  phrases {int(((ev['phrase'] >= t0) & (ev['phrase'] < t0 + 10)).sum())}"
                      f"  drops {int(((ev['drop'] >= t0) & (ev['drop'] < t0 + 10)).sum())}")


if __name__ == "__main__":
    main()
