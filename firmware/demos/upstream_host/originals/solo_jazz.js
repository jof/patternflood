// ===== Patternflow pattern =====
// Title:    Solo Jazz
// Author:   Jonathan Lassoff
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================

// @knobs Tempo=60..180, Solo=0..1, Dry=0..1, Paper=0..1
// @matrix 64x128

// Solo Jazz: the 1990s paper-cup swash, improvised live. A teal dry brush lays down
// the chord (one bar, its pressure on an attack/release envelope, each bristle running
// out of ink at its own rate), and a purple pen plays a solo over it: a random walk on
// scale degrees in swung eighths, triplets or sixteenths, gliding between notes, with a
// calligraphic nib. Each phrase lands where the paper is emptiest; old ones fade.
// Written for any frame size: everything scales with the short side.
// Knob 1 Tempo: beats per minute, how fast the brush and pen move.
// Knob 2 Solo: 0 a lazy wave in swung eighths, 1 a bebop zigzag of sixteenths and leaps.
// Knob 3 Dry: 0 a wet, solid swash; 1 a dry brush, streaky and breaking up.
// Knob 4 Paper: 0 black (the inks glow), 1 cream cup paper.
// Push any knob: wash the paper and start a new phrase.

const BRUSH_BEATS = 4, PEN_DELAY = 1.5, PEN_BEATS = 4;
const MAX_LANES = 96, MAX_NOTES = 24;
const T_MAX = 1.45, P_MAX = 1.4;      // ink over 1 shows as solid: fading starts late
const SWING = 0.64;
const NIB_C = 0.7071, NIB_S = -0.7071; // the pen's nib, at 45 degrees
const PREROLL_BEATS = 7;
const PAPER_HI = [242, 228, 198];
const TEAL_LIGHT = [64, 198, 204], TEAL_DARK = [10, 112, 148];
const PURPLE = [96, 26, 176];

function hash32(x) {
  x = (x ^ (x >>> 16)) >>> 0;
  x = Math.imul(x, 0x7feb352d) >>> 0;
  x = (x ^ (x >>> 15)) >>> 0;
  x = Math.imul(x, 0x846ca68b) >>> 0;
  return (x ^ (x >>> 16)) >>> 0;
}

function h01(seed, i) {
  return hash32((seed + Math.imul(i, 0x9e3779b9)) >>> 0) / 4294967296;
}

function vnoise(seed, t) {
  const i = Math.floor(t), f = t - i;
  const a = h01(seed, i), b = h01(seed, i + 1);
  return a + (b - a) * f * f * (3 - 2 * f);
}

function h2(seed, ix, iy) {
  return hash32((seed + Math.imul(ix, 0x9e3779b9) + Math.imul(iy, 0x85ebca6b)) >>> 0) / 4294967296;
}

// 2D value noise: across the brush (bristle clumps) by along the stroke.
function vnoise2(seed, x, y) {
  const ix = Math.floor(x), iy = Math.floor(y);
  let fx = x - ix, fy = y - iy;
  fx = fx * fx * (3 - 2 * fx);
  fy = fy * fy * (3 - 2 * fy);
  const a = h2(seed, ix, iy), b = h2(seed, ix + 1, iy);
  const c = h2(seed, ix, iy + 1), d = h2(seed, ix + 1, iy + 1);
  return a + (b - a) * fx + (c - a + (d - c - b + a) * fx) * fy;
}

function smooth(x) {
  return x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x);
}

function clamp01(x) {
  return x < 0 ? 0 : x > 1 ? 1 : x;
}

function nextU32(p) {
  let x = p.rng;
  x = (x ^ (x << 13)) >>> 0;
  x = (x ^ (x >>> 17)) >>> 0;
  x = (x ^ (x << 5)) >>> 0;
  p.rng = x;
  return x;
}

function rnd(p) {
  return (nextU32(p) >>> 8) / 16777216;
}

export function setup(params) {
  params.tempo = 120; params.solo = 0.5; params.dry = 0.5; params.paper = 0.5;
  params.w = 0; params.h = 0;
  params.dt = 0;
  params.washReq = false;
}

export function update(dt, input, params) {
  if (input && input.knobValues) {
    params.tempo = input.knobValues[0];
    params.solo = input.knobValues[1];
    params.dry = input.knobValues[2];
    params.paper = input.knobValues[3];
  }
  if (input && input.btnPressed) {
    for (let i = 0; i < 4; i++) if (input.btnPressed[i]) params.washReq = true;
  }
  params.dt = dt > 0.1 ? 0.1 : dt;
}

function init(p, w, h) {
  p.w = w; p.h = h;
  p.S = Math.min(w, h) / 64;
  p.T = new Float32Array(w * h);      // teal ink
  p.Sh = new Float32Array(w * h);     // its shade, light 0 .. dark 1
  p.P = new Float32Array(w * h);      // purple ink
  p.fadeBeats = 8 + 6 * h / (64 * p.S);
  p.rng = 0x2468ace1;
  p.tempoS = p.tempo; p.soloS = p.solo; p.dryS = p.dry; p.paperS = p.paper;
  p.wash = 0;
  p.lastY = -1000;
  p.lanes = [];
  for (let j = 0; j < MAX_LANES; j++) p.lanes.push({ load: 0, dep: 0, seed: 0, shade: 0, t0: 0, t1: 1 });
  p.notes = [];
  for (let k = 0; k < MAX_NOTES; k++) p.notes.push({ t: 0, deg: 0, acc: 0, rest: false });
  newPhrase(p);
  p.hasBrush = p.hasPen = true;       // open with the whole figure
  for (let b = 0; b < PREROLL_BEATS; b += p.tempoS / 60 / 30) step(p, 1 / 30);
}

// Where the paper is emptiest, of six tries, and not on top of the last phrase.
function pickY(p, hw) {
  let best = p.h * 0.5, bestScore = 1e30;
  for (let k = 0; k < 6; k++) {
    const y = p.h * (0.1 + 0.8 * rnd(p));
    let score = Math.abs(y - p.lastY) < hw * 1.5 ? 1e6 : 0;
    const y0 = Math.max(0, Math.floor(y - hw)), y1 = Math.min(p.h - 1, Math.floor(y + hw));
    for (let yy = y0; yy <= y1; yy += 2) {
      for (let x = 0; x < p.w; x += 2) score += p.T[yy * p.w + x] + p.P[yy * p.w + x];
    }
    if (score < bestScore) { bestScore = score; best = y; }
  }
  return best;
}

function newPhrase(p) {
  const S = p.S, W = p.w;
  p.pb = 0;
  const r = rnd(p);
  p.hasBrush = r >= 0.1;                  // one in ten: the pen alone, a solo break
  p.hasPen = r < 0.1 || r >= 0.16;        // and one in sixteen: the brush alone
  const rest = [0.5, 1, 1, 2][Math.floor(rnd(p) * 4)];
  p.phraseLen = PEN_DELAY + PEN_BEATS + rest;

  const th = (rnd(p) * 2 - 1) * 0.38;
  const dir = rnd(p) < 0.8 ? 1 : -1;
  p.hw = S * (6.0 + rnd(p) * 3.0);
  p.L = W * (0.85 + rnd(p) * 0.45) / Math.cos(th);
  p.cx = W * (0.3 + rnd(p) * 0.4);
  p.cy = pickY(p, p.hw);
  p.lastY = p.cy;
  p.bend = (rnd(p) * 2 - 1) * 0.1 * p.L;
  p.wobA = S * (0.6 + rnd(p) * 1.2);
  p.wobF = 0.8 + rnd(p) * 1.4;
  p.wobP = rnd(p);
  p.dx = Math.cos(th) * dir; p.dy = Math.sin(th) * dir;
  p.nx = -p.dy; p.ny = p.dx;

  p.seed = nextU32(p);
  p.nLanes = Math.min(MAX_LANES, Math.floor(2 * p.hw / 0.55) + 1);
  const sf = 1.2 + rnd(p) * 1.6, sp = rnd(p) * 6.2832;
  for (let j = 0; j < p.nLanes; j++) {
    const lane = p.lanes[j];
    const u = -1 + 2 * j / (p.nLanes - 1);
    lane.load = 0.82 + 0.18 * rnd(p);
    lane.dep = 0.45 + 0.55 * rnd(p);
    lane.seed = nextU32(p);
    const jitter = rnd(p) - 0.5;
    lane.shade = clamp01(0.5 + 0.22 * Math.sin(u * 3.1416 * sf + sp) + jitter * 0.2);
    lane.t0 = (0.05 + 0.03 * rnd(p)) * u * u;          // outer bristles touch down later
    lane.t1 = 1 - (0.06 + 0.06 * rnd(p)) * u * u;      // and lift sooner: a round start, a pointed tail
  }

  // The solo: a walk on scale degrees -5..5, one beat at a time.
  const solo = p.soloS;
  p.bias = (rnd(p) * 2 - 1) * 0.3 * p.hw;
  p.amp = p.hw * (1.0 + 0.8 * solo) / 5;
  let deg = Math.round((rnd(p) * 2 - 1) * 2);
  let up = rnd(p) < 0.5;
  let n = 0;
  for (let b = 0; b < PEN_BEATS; b++) {
    const rs = rnd(p);
    const sub = rs < solo * 0.75 ? 4 : rs < solo ? 3 : 2;
    for (let s = 0; s < sub; s++) {
      const note = p.notes[n++];
      note.t = (b + (sub === 2 ? (s === 0 ? 0 : SWING) : s / sub)) / PEN_BEATS;
      note.deg = deg;
      note.acc = s === 0 ? (b % 2 === 0 ? 1 : 0.6) : 0;
      note.rest = n > 1 && b < PEN_BEATS - 1 && rnd(p) < 0.04;
      let size;
      if (rnd(p) < 0.08 + 0.25 * solo) size = 3 + Math.floor(rnd(p) * 3);
      else size = rnd(p) < 0.4 ? 2 : 1;
      if (rnd(p) < 0.7) up = !up;         // a squiggle mostly turns back
      deg += up ? size : -size;
      if (deg > 5) deg = 10 - deg;
      if (deg < -5) deg = -10 - deg;
    }
  }
  const last = p.notes[n++];
  last.t = 1; last.deg = deg; last.acc = 0; last.rest = false;
  p.nNotes = n;
  p.penX = p.penY = -1e9;
}

function pathX(p, t) {
  const s = t - 0.5;
  const off = p.bend * (1 - 4 * s * s) + p.wobA * Math.sin(6.2832 * (p.wobF * t + p.wobP));
  return p.cx + p.dx * s * p.L + p.nx * off;
}

function pathY(p, t) {
  const s = t - 0.5;
  const off = p.bend * (1 - 4 * s * s) + p.wobA * Math.sin(6.2832 * (p.wobF * t + p.wobP));
  return p.cy + p.dy * s * p.L + p.ny * off;
}

function splat(p, x, y, a, shade) {
  const ix = Math.floor(x), iy = Math.floor(y);
  const fx = x - ix, fy = y - iy;
  for (let k = 0; k < 4; k++) {
    const px = ix + (k & 1), py = iy + (k >> 1);
    if (px < 0 || py < 0 || px >= p.w || py >= p.h) continue;
    const wgt = ((k & 1) ? fx : 1 - fx) * ((k >> 1) ? fy : 1 - fy);
    const aa = a * wgt;
    const i = py * p.w + px;
    const t = p.T[i] + aa;
    p.T[i] = t > T_MAX ? T_MAX : t;
    const m = aa * 2;
    p.Sh[i] += (shade - p.Sh[i]) * (m > 1 ? 1 : m);
    const q = p.P[i] - aa * 1.2;      // fresh teal covers old purple
    p.P[i] = q > 0 ? q : 0;
  }
}

function paintBrush(p, t0, t1) {
  const S = p.S, dry = p.dryS;
  const along = (t1 - t0) * p.L;
  const n = Math.max(1, Math.ceil(along / 0.45));
  const stepAlong = along / n;
  for (let i = 1; i <= n; i++) {
    const t = t0 + (t1 - t0) * i / n;
    const x = pathX(p, t), y = pathY(p, t);
    const att = t < 0.1 ? smooth(t / 0.1) : 1;
    const rel = t > 0.78 ? smooth((1 - t) / 0.22) : 1;
    const width = (0.4 + 0.6 * att) * (0.3 + 0.7 * rel);
    const press = (0.75 + 0.25 * att) * (0.6 + 0.4 * rel);
    const spacing = 2 * p.hw * width / (p.nLanes - 1);
    const gain = 1.3 * stepAlong * spacing;
    const tn = t * p.L / (4.5 * S), tc = t * p.L / (9 * S), te = t * p.L / (6 * S), ts = t * p.L / (14 * S);
    const cu = p.hw / (1.4 * S);         // bristle clumps about 1.4 px wide
    for (let j = 0; j < p.nLanes; j++) {
      const lane = p.lanes[j];
      if (t < lane.t0 || t > lane.t1) continue;
      const u = -1 + 2 * j / (p.nLanes - 1);
      let ink = lane.load * press - dry * lane.dep * t * 0.9
        + (vnoise2(p.seed, (u + 1) * cu, tc) - 0.5) * (0.2 + 1.5 * dry)
        + (vnoise(lane.seed, tn) - 0.5) * 0.15;
      const edge = Math.abs(u);
      if (edge > 0.7) ink -= (edge - 0.7) / 0.3 * (0.2 + 1.0 * vnoise2(p.seed ^ 0x5bd1e995, (u + 1) * cu, te));
      if (ink < 0.12) continue;           // a dry bristle skips: paper shows through
      ink = 0.45 + ink;
      if (ink > 1) ink = 1;
      const off = u * p.hw * width;
      const shade = clamp01(lane.shade + (vnoise2(p.seed ^ 0x27d4eb2f, (u + 1) * cu * 0.6, ts) - 0.5) * 0.9);
      splat(p, x + p.nx * off, y + p.ny * off, ink * gain, shade);
    }
  }
}

function disc(p, x, y, r) {
  const x0 = Math.max(0, Math.floor(x - r - 1)), x1 = Math.min(p.w - 1, Math.ceil(x + r + 1));
  const y0 = Math.max(0, Math.floor(y - r - 1)), y1 = Math.min(p.h - 1, Math.ceil(y + r + 1));
  for (let py = y0; py <= y1; py++) {
    for (let px = x0; px <= x1; px++) {
      const ddx = px - x, ddy = py - y;
      const c = r + 0.5 - Math.sqrt(ddx * ddx + ddy * ddy);
      if (c <= 0) continue;
      const v = (c > 1 ? 1 : c) * P_MAX;
      const i = py * p.w + px;
      if (v > p.P[i]) p.P[i] = v;
    }
  }
}

function paintPen(p, tp0, tp1) {
  const along = (tp1 - tp0) * 1.08 * p.L;
  const n = Math.max(1, Math.ceil(along / 0.12));
  const bend = 0.85 * p.soloS * p.soloS;  // 0: notes joined by cosine glides, 1: nearly straight
  for (let i = 1; i <= n; i++) {
    const tp = tp0 + (tp1 - tp0) * i / n;
    let k = 0;
    while (k < p.nNotes - 2 && p.notes[k + 1].t <= tp) k++;
    const a = p.notes[k], b = p.notes[k + 1];
    const f = clamp01((tp - a.t) / (b.t - a.t));
    const cs = (1 - Math.cos(3.1416 * f)) * 0.5;
    const s = cs + (f - cs) * bend;
    const m = a.deg + (b.deg - a.deg) * s;
    const accent = a.acc * Math.exp(-(tp - a.t) * PEN_BEATS * 6);
    const t = -0.04 + 1.08 * tp;
    const off = p.bias + m * p.amp;
    const x = pathX(p, t) + p.nx * off, y = pathY(p, t) + p.ny * off;
    const mx = x - p.penX, my = y - p.penY;
    const len = Math.sqrt(mx * mx + my * my);
    if (p.penX > -1e8 && len > 1e-4) p.nib = 0.6 + 0.6 * Math.abs((my * NIB_C - mx * NIB_S) / len);
    else if (p.penX <= -1e8) p.nib = 1;
    p.penX = x; p.penY = y;
    if (a.rest) continue;
    const taper = 0.35 + 0.65 * smooth(tp / 0.05) * smooth((1 - tp) / 0.05);
    disc(p, x, y, p.S * 0.85 * p.nib * (1 + 0.45 * accent) * taper);
  }
}

function step(p, dt) {
  const kk = dt * 3 > 1 ? 1 : dt * 3;
  p.tempoS += (p.tempo - p.tempoS) * kk;
  p.soloS += (p.solo - p.soloS) * kk;
  p.dryS += (p.dry - p.dryS) * kk;
  p.paperS += (p.paper - p.paperS) * (kk * 0.5);
  if (p.washReq) { p.washReq = false; p.wash = 1; newPhrase(p); }

  const bps = p.tempoS / 60;
  const rate = bps / p.fadeBeats + (p.wash > 0 ? 3 : 0);
  if (p.wash > 0) p.wash -= dt;
  const fade = Math.exp(-dt * rate);
  const N = p.w * p.h;
  for (let i = 0; i < N; i++) { p.T[i] *= fade; p.P[i] *= fade; }

  const pb0 = p.pb;
  p.pb += dt * bps;
  if (p.hasBrush) {
    const t0 = clamp01(pb0 / BRUSH_BEATS), t1 = clamp01(p.pb / BRUSH_BEATS);
    if (t1 > t0) paintBrush(p, t0, t1);
  }
  if (p.hasPen) {
    const t0 = clamp01((pb0 - PEN_DELAY) / PEN_BEATS), t1 = clamp01((p.pb - PEN_DELAY) / PEN_BEATS);
    if (t1 > t0) paintPen(p, t0, t1);
  }
  if (p.pb >= p.phraseLen) newPhrase(p);
}

export function draw(display, params, time) {
  const p = params, W = display.width, H = display.height;
  if (p.w !== W || p.h !== H) init(p, W, H);
  step(p, p.dt);

  const pa = 1 - (1 - p.paperS) * (1 - p.paperS);   // mid-knob is already cream, not grey
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const i = y * W + x;
      const grain = (h01(911, i) - 0.5) * 10 * pa;
      const tc = p.T[i] > 1 ? 1 : p.T[i], pc = p.P[i] > 1 ? 1 : p.P[i], sh = p.Sh[i];
      let r = PAPER_HI[0] * pa + grain, g = PAPER_HI[1] * pa + grain, b = PAPER_HI[2] * pa + grain;
      r += (TEAL_LIGHT[0] + (TEAL_DARK[0] - TEAL_LIGHT[0]) * sh - r) * tc;
      g += (TEAL_LIGHT[1] + (TEAL_DARK[1] - TEAL_LIGHT[1]) * sh - g) * tc;
      b += (TEAL_LIGHT[2] + (TEAL_DARK[2] - TEAL_LIGHT[2]) * sh - b) * tc;
      r += (PURPLE[0] - r) * pc;
      g += (PURPLE[1] - g) * pc;
      b += (PURPLE[2] - b) * pc;
      display.setPixel(x, y, r < 0 ? 0 : r | 0, g < 0 ? 0 : g | 0, b < 0 ? 0 : b | 0);
    }
  }
}
