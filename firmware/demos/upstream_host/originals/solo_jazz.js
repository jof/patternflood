// ===== Patternflow pattern =====
// Title:    Solo Jazz
// Author:   Jonathan Lassoff
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================

// @knobs Pace=60..180, Jive=0..1, Zoom=0..1, Spin=-1..1
// @matrix 64x128

// Solo Jazz: the 1990s paper-cup swash, improvised live by a quartet, for playing like an
// instrument. Each voice's teal dry brush lays down a chord (one bar, its pressure on an
// attack/release envelope, each bristle running out of ink at its own rate), and its purple
// pen plays a zigzag solo over it: a walk on scale degrees in swung eighths, triplets or
// sixteenths that mostly turns back on itself. Both are crayon on toothy paper: ink is rub
// pressure, showing only where it beats the grain, so strokes are rough when fresh and wear
// into streaks as they fade. The paper is two screens each way, wrapping round like the cup:
// the soloist always plays in view, the other three anywhere, each landing where the paper is
// emptiest, so zooming out shows the whole band at work.
// Written for any frame size: everything scales with the short side.
// It keeps its own time and hears nothing.
// Knob 1 Pace: how fast the band plays, in beats a minute. Push: a break, fresh phrases on
//   clean paper.
// Knob 2 Jive: how wild the solos are, and how hard the purple dances: a zigzag warp that
//   kicks on every beat, zig and zag trading places. Push: freeze the painting (the view
//   still moves), and again to let it go.
// Knob 3 Zoom: middle as painted; down to a half, the whole paper; up to 3x, a crayon
//   close-up. Pumps a little on the beat. Push: mirror off, mirror, kaleidoscope.
// Knob 4 Spin: middle still; either way, up to a turn every two bars. Back near the middle
//   it eases upright. Push: night (the start) or cream paper.

const BRUSH_BEATS = 4, PEN_DELAY = 1.5, PEN_BEATS = 4;
const VOICES = 4, ROOM = 2;           // a quartet, on paper two screens each way
const MAX_LANES = 96, MAX_NOTES = 24;
const T_MAX = 1.45, P_MAX = 1.4;      // ink over 1 shows as solid: fading starts late
const SWING = 0.64;
const NIB_C = 0.7071, NIB_S = -0.7071; // the pen's nib, at 45 degrees
const PREROLL_BEATS = 7;
// Crayon on paper: ink is rub pressure, and a pixel takes colour only where the pressure
// beats its paper tooth (fixed grain), so light strokes and fading ones break into specks.
const TOOTH_SEED = 0x1b873593, TOOTH_SEED2 = 0xcc9e2d51;
const TEAL_FLOOR = 0.45, TEAL_TOOTH = 0.9, PURPLE_FLOOR = 0.4, PURPLE_TOOTH = 0.9, GRIP = 0.5;
const PAPER_HI = [242, 228, 198], PAPER_LEVEL = 0.8;
const TEAL_LIGHT = [64, 198, 204], TEAL_DARK = [10, 112, 148];
const PURPLE = [96, 26, 176], PURPLE_NIGHT = [132, 48, 222];   // lifted on black, where it runs dim
const SPIN_DEAD = 0.06;               // about a detent either side of the middle: still

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

function wrap(n, m) {
  n %= m;
  return n < 0 ? n + m : n;
}

// -1 at whole numbers, +1 halfway: a zigzag
function tri(x) {
  return 1 - 4 * Math.abs(x - Math.floor(x) - 0.5);
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
  params.pace = 120; params.jive = 0.5; params.zoom = 0.5; params.spin = 0;
  params.w = 0; params.h = 0;
  params.dt = 0;
  params.press = [false, false, false, false];
}

export function update(dt, input, params) {
  if (input && input.knobValues) {
    params.pace = input.knobValues[0];
    params.jive = input.knobValues[1];
    params.zoom = input.knobValues[2];
    params.spin = input.knobValues[3];
  }
  if (input && input.btnPressed) {
    for (let i = 0; i < 4; i++) if (input.btnPressed[i]) params.press[i] = true;
  }
  params.dt = dt > 0.1 ? 0.1 : dt;
}

function init(p, w, h) {
  p.w = w; p.h = h;
  p.cw = w * ROOM; p.ch = h * ROOM;
  p.S = Math.min(w, h) / 64;
  const n = p.cw * p.ch;
  p.T = new Float32Array(n);          // teal ink
  p.Sh = new Float32Array(n);         // its shade, light 0 .. dark 1
  p.P = new Float32Array(n);          // purple ink
  p.tooth = new Float32Array(n);      // the paper's grain: per pixel, and in streaks along the strokes
  for (let y = 0; y < p.ch; y++) {
    for (let x = 0; x < p.cw; x++) {
      const i = y * p.cw + x;
      p.tooth[i] = 0.35 * h01(TOOTH_SEED, i) + 0.65 * vnoise2(TOOTH_SEED2, x * 0.35, y * 1.1);
    }
  }
  p.fadeBeats = 2.4 * (8 + 6 * h / (64 * p.S));   // slow: a stroke spends its life wearing into the grain
  p.rng = 0x2468ace1;
  p.tempoS = p.pace; p.jiveS = p.jive; p.zoomS = p.zoom; p.spinS = p.spin;
  p.paperOn = false; p.paperS = 0;    // night: mostly-white frames fight the power limit
  p.mirror = 0;
  p.frozen = false;
  p.angle = 0;
  p.beatF = 0; p.beatN = 0;
  p.noteFlash = 0;
  p.wash = 0;
  p.voices = [];
  for (let k = 0; k < VOICES; k++) {
    const v = { lastX: -1e4, lastY: -1e4, lanes: [], notes: [] };
    for (let j = 0; j < MAX_LANES; j++) v.lanes.push({ load: 0, dep: 0, seed: 0, shade: 0, t0: 0, t1: 1 });
    for (let j = 0; j < MAX_NOTES; j++) v.notes.push({ t: 0, deg: 0, acc: 0, rest: false });
    p.voices.push(v);
  }
  for (let k = 0; k < VOICES; k++) {
    const v = p.voices[k];
    newPhrase(p, v, k);
    v.hasBrush = v.hasPen = true;     // open with the whole figure
    v.pb = -1.75 * k;                 // and come in one after another
  }
  for (let b = 0; b < PREROLL_BEATS; b += p.tempoS / 60 / 30) step(p, 1 / 30);
}

// Where the paper is emptiest, of six tries, and off this voice's last phrase. The soloist
// (voice 0) plays in the middle screen, the one in view at 1x; the others anywhere.
function pickSpot(p, v, k, hw, len) {
  let bx = p.cw * 0.5, by = p.ch * 0.5, bestScore = 1e30;
  for (let c = 0; c < 6; c++) {
    let x, y;
    if (k === 0) {
      x = p.cw * 0.5 + p.w * (rnd(p) - 0.5) * 0.4;
      y = p.ch * 0.5 + p.h * (rnd(p) * 0.8 - 0.4);
    } else {
      x = p.cw * rnd(p);
      y = p.ch * rnd(p);
    }
    let score = Math.abs(y - v.lastY) < hw * 1.5 && Math.abs(x - v.lastX) < len * 0.5 ? 1e6 : 0;
    const y0 = Math.floor(y - hw), y1 = Math.floor(y + hw);
    const x0 = Math.floor(x - len * 0.5), x1 = Math.floor(x + len * 0.5);
    for (let yy = y0; yy <= y1; yy += 2) {
      const row = wrap(yy, p.ch) * p.cw;
      for (let xx = x0; xx <= x1; xx += 2) score += p.T[row + wrap(xx, p.cw)] + p.P[row + wrap(xx, p.cw)];
    }
    if (score < bestScore) { bestScore = score; bx = x; by = y; }
  }
  v.cx = bx; v.cy = by;
  v.lastX = bx; v.lastY = by;
}

function newPhrase(p, v, k) {
  const S = p.S, W = p.w;
  v.pb = 0;
  const r = rnd(p);
  v.hasBrush = r >= 0.1;                  // one in ten: the pen alone, a solo break
  v.hasPen = r < 0.1 || r >= 0.16;        // and one in sixteen: the brush alone
  const rest = [0.5, 1, 1, 2][Math.floor(rnd(p) * 4)];
  v.phraseLen = PEN_DELAY + PEN_BEATS + rest + (k === 0 ? 0 : 2);   // the band lays out more than the soloist
  v.dry = 0.15 + 0.7 * rnd(p);

  const th = (rnd(p) * 2 - 1) * 0.38;
  const dir = rnd(p) < 0.8 ? 1 : -1;
  v.hw = S * (6.0 + rnd(p) * 3.0);
  v.L = W * (0.75 + rnd(p) * 0.3) / Math.cos(th);
  pickSpot(p, v, k, v.hw, v.L);
  v.bend = (rnd(p) * 2 - 1) * 0.1 * v.L;
  v.wobA = S * (0.6 + rnd(p) * 1.2);
  v.wobF = 0.8 + rnd(p) * 1.4;
  v.wobP = rnd(p);
  v.dx = Math.cos(th) * dir; v.dy = Math.sin(th) * dir;
  v.nx = -v.dy; v.ny = v.dx;

  v.seed = nextU32(p);
  v.nLanes = Math.min(MAX_LANES, Math.floor(2 * v.hw / 0.55) + 1);
  const sf = 1.2 + rnd(p) * 1.6, sp = rnd(p) * 6.2832;
  const hatchSign = rnd(p) < 0.5 ? -1 : 1;
  v.hatchK = hatchSign * (0.6 + 0.6 * rnd(p));       // scribble: pressure in diagonal bands
  v.hatchP = S * (2.6 + 1.4 * rnd(p));
  v.penSeed = nextU32(p);
  for (let j = 0; j < v.nLanes; j++) {
    const lane = v.lanes[j];
    const u = -1 + 2 * j / (v.nLanes - 1);
    lane.load = 0.82 + 0.18 * rnd(p);
    lane.dep = 0.45 + 0.55 * rnd(p);
    lane.seed = nextU32(p);
    const jitter = rnd(p) - 0.5;
    lane.shade = clamp01(0.5 + 0.22 * Math.sin(u * 3.1416 * sf + sp) + jitter * 0.2);
    lane.t0 = (0.05 + 0.03 * rnd(p)) * u * u;          // outer bristles touch down later
    lane.t1 = 1 - (0.06 + 0.06 * rnd(p)) * u * u;      // and lift sooner: a round start, a pointed tail
  }

  // The solo: a zigzag walk on scale degrees -6..6, one beat at a time.
  const jive = p.jiveS;
  v.bias = (rnd(p) * 2 - 1) * 0.3 * v.hw;
  v.amp = v.hw * (1.4 + 1.2 * jive) / 6;
  let deg = Math.floor((rnd(p) * 2 - 1) * 2 + 0.5);
  let up = rnd(p) < 0.5;
  let n = 0;
  for (let b = 0; b < PEN_BEATS; b++) {
    const rs = rnd(p);
    const sub = rs < 0.25 + 0.6 * jive ? 4 : rs < 0.45 + 0.5 * jive ? 3 : 2;
    for (let s = 0; s < sub; s++) {
      const note = v.notes[n++];
      note.t = (b + (sub === 2 ? (s === 0 ? 0 : SWING) : s / sub)) / PEN_BEATS;
      note.deg = deg;
      note.acc = s === 0 ? (b % 2 === 0 ? 1 : 0.6) : 0;
      note.rest = n > 1 && b < PEN_BEATS - 1 && rnd(p) < 0.04;
      let size;
      if (rnd(p) < 0.15 + 0.35 * jive) size = 4 + Math.floor(rnd(p) * 3);
      else size = rnd(p) < 0.5 ? 3 : 2;
      if (rnd(p) < 0.88) up = !up;        // a zigzag: it nearly always turns back
      deg += up ? size : -size;
      if (deg > 6) deg = 12 - deg;
      if (deg < -6) deg = -12 - deg;
      if (deg > 6) deg = 6;
      if (deg < -6) deg = -6;
    }
  }
  const last = v.notes[n++];
  last.t = 1; last.deg = deg; last.acc = 0; last.rest = false;
  v.nNotes = n;
  v.lastNote = -1;
  v.penX = v.penY = -1e9;
}

function pathOff(v, t) {
  const s = t - 0.5;
  return v.bend * (1 - 4 * s * s) + v.wobA * Math.sin(6.2832 * (v.wobF * t + v.wobP));
}

function splat(p, x, y, a, shade) {
  const ix = Math.floor(x), iy = Math.floor(y);
  const fx = x - ix, fy = y - iy;
  for (let k = 0; k < 4; k++) {
    const px = wrap(ix + (k & 1), p.cw), py = wrap(iy + (k >> 1), p.ch);
    const wgt = ((k & 1) ? fx : 1 - fx) * ((k >> 1) ? fy : 1 - fy);
    const aa = a * wgt;
    const i = py * p.cw + px;
    const t = p.T[i] + aa;
    p.T[i] = t > T_MAX ? T_MAX : t;
    const m = aa * 2;
    p.Sh[i] += (shade - p.Sh[i]) * (m > 1 ? 1 : m);
    const q = p.P[i] - aa * 1.2;      // fresh teal covers old purple
    p.P[i] = q > 0 ? q : 0;
  }
}

function paintBrush(p, v, t0, t1) {
  const S = p.S, dry = v.dry;
  const along = (t1 - t0) * v.L;
  const n = Math.max(1, Math.ceil(along / 0.45));
  const stepAlong = along / n;
  for (let i = 1; i <= n; i++) {
    const t = t0 + (t1 - t0) * i / n;
    const s = t - 0.5, off0 = pathOff(v, t);
    const x = v.cx + v.dx * s * v.L + v.nx * off0, y = v.cy + v.dy * s * v.L + v.ny * off0;
    const att = t < 0.1 ? smooth(t / 0.1) : 1;
    const rel = t > 0.78 ? smooth((1 - t) / 0.22) : 1;
    const width = (0.4 + 0.6 * att) * (0.3 + 0.7 * rel);
    const press = (0.75 + 0.25 * att) * (0.6 + 0.4 * rel);
    const spacing = 2 * v.hw * width / (v.nLanes - 1);
    const gain = 1.7 * stepAlong * spacing;
    const tn = t * v.L / (4.5 * S), tc = t * v.L / (9 * S), te = t * v.L / (6 * S), ts = t * v.L / (14 * S);
    const cu = v.hw / (1.4 * S);         // bristle clumps about 1.4 px wide
    for (let j = 0; j < v.nLanes; j++) {
      const lane = v.lanes[j];
      if (t < lane.t0 || t > lane.t1) continue;
      const u = -1 + 2 * j / (v.nLanes - 1);
      const hatch = 0.78 + 0.22 * Math.sin(6.2832 * (t * v.L + u * v.hw * v.hatchK) / v.hatchP);
      let ink = lane.load * press * hatch - dry * lane.dep * t * 0.9
        + (vnoise2(v.seed, (u + 1) * cu, tc) - 0.5) * (0.2 + 1.5 * dry)
        + (vnoise(lane.seed, tn) - 0.5) * 0.15;
      const edge = Math.abs(u);
      if (edge > 0.7) ink -= (edge - 0.7) / 0.3 * (0.2 + 1.0 * vnoise2(v.seed ^ 0x5bd1e995, (u + 1) * cu, te));
      if (ink < 0.12) continue;           // a dry bristle skips: paper shows through
      ink = 0.45 + ink;
      if (ink > 1) ink = 1;
      const off = u * v.hw * width;
      const shade = clamp01(lane.shade + (vnoise2(v.seed ^ 0x27d4eb2f, (u + 1) * cu * 0.6, ts) - 0.5) * 0.9);
      splat(p, x + v.nx * off, y + v.ny * off, ink * gain, shade);
    }
  }
}

function disc(p, x, y, r, press) {
  const x0 = Math.floor(x - r - 1), x1 = Math.ceil(x + r + 1);
  const y0 = Math.floor(y - r - 1), y1 = Math.ceil(y + r + 1);
  for (let py = y0; py <= y1; py++) {
    for (let px = x0; px <= x1; px++) {
      const ddx = px - x, ddy = py - y;
      const c = r + 0.5 - Math.sqrt(ddx * ddx + ddy * ddy);
      if (c <= 0) continue;
      const val = (c > 1 ? 1 : c) * P_MAX * press;
      const i = wrap(py, p.ch) * p.cw + wrap(px, p.cw);
      if (val > p.P[i]) p.P[i] = val;
    }
  }
}

function paintPen(p, v, k, tp0, tp1) {
  const along = (tp1 - tp0) * 1.08 * v.L;
  const n = Math.max(1, Math.ceil(along / 0.12));
  const glide = 0.55 + 0.45 * p.jiveS;  // 0: notes joined by cosine glides, 1: straight, sharp corners
  for (let i = 1; i <= n; i++) {
    const tp = tp0 + (tp1 - tp0) * i / n;
    let q = 0;
    while (q < v.nNotes - 2 && v.notes[q + 1].t <= tp) q++;
    const a = v.notes[q], b = v.notes[q + 1];
    if (q !== v.lastNote) {
      v.lastNote = q;
      if (k === 0 && !a.rest) p.noteFlash = 0.6 + 0.4 * a.acc;   // the soloist's notes light k1
    }
    const f = clamp01((tp - a.t) / (b.t - a.t));
    const cs = (1 - Math.cos(3.1416 * f)) * 0.5;
    const sm = cs + (f - cs) * glide;
    const m = a.deg + (b.deg - a.deg) * sm;
    const accent = a.acc * Math.exp(-(tp - a.t) * PEN_BEATS * 6);
    const t = -0.04 + 1.08 * tp;
    const s = t - 0.5, off0 = pathOff(v, t);
    const off = v.bias + m * v.amp;
    const x = v.cx + v.dx * s * v.L + v.nx * off0 + v.nx * off;
    const y = v.cy + v.dy * s * v.L + v.ny * off0 + v.ny * off;
    const mx = x - v.penX, my = y - v.penY;
    const len = Math.sqrt(mx * mx + my * my);
    if (v.penX > -1e8 && len > 1e-4) v.nib = 0.6 + 0.6 * Math.abs((my * NIB_C - mx * NIB_S) / len);
    else if (v.penX <= -1e8) v.nib = 1;
    v.penX = x; v.penY = y;
    if (a.rest) continue;
    const taper = 0.35 + 0.65 * smooth(tp / 0.05) * smooth((1 - tp) / 0.05);
    const press = 0.8 + 0.4 * vnoise(v.penSeed, tp * 1.08 * v.L / (2.5 * p.S));   // the crayon skips
    disc(p, x, y, p.S * 1.1 * v.nib * (1 + 0.45 * accent) * taper, press);
  }
}

function step(p, dt) {
  // The clicks: a break, freeze, the mirror, the paper.
  if (p.press[0]) {
    p.frozen = false;
    p.wash = 1;
    for (let k = 0; k < VOICES; k++) newPhrase(p, p.voices[k], k);
  }
  if (p.press[1]) p.frozen = !p.frozen;
  if (p.press[2]) p.mirror = (p.mirror + 1) % 3;
  if (p.press[3]) p.paperOn = !p.paperOn;
  for (let i = 0; i < 4; i++) p.press[i] = false;

  const kk = dt * 3 > 1 ? 1 : dt * 3;
  p.tempoS += (p.pace - p.tempoS) * kk;
  p.jiveS += (p.jive - p.jiveS) * kk;
  p.zoomS += (p.zoom - p.zoomS) * kk;
  p.spinS += (p.spin - p.spinS) * kk;
  p.paperS += ((p.paperOn ? 1 : 0) - p.paperS) * (dt * 2 > 1 ? 1 : dt * 2);
  p.noteFlash *= Math.exp(-dt * 8);

  const bps = p.tempoS / 60;
  p.beatF += dt * bps;
  if (p.beatF >= 1) { p.beatF -= 1; p.beatN = (p.beatN + 1) & 3; }

  if (Math.abs(p.spinS) < SPIN_DEAD) {     // let go of the spin: ease back upright
    const target = Math.floor(p.angle / 3.1416 + 0.5) * 3.1416;
    p.angle += (target - p.angle) * (dt * 2.5 > 1 ? 1 : dt * 2.5);
  } else {
    p.angle += p.spinS * Math.abs(p.spinS) * (6.2832 / 8) * bps * dt;
  }
  if (p.angle > 3.1416) p.angle -= 6.2832;
  if (p.angle < -3.1416) p.angle += 6.2832;

  if (p.frozen) return;                // held: the paper keeps, and the band waits
  const rate = bps / p.fadeBeats + (p.wash > 0 ? 3 : 0);
  if (p.wash > 0) p.wash -= dt;
  const fade = Math.exp(-dt * rate);
  const N = p.cw * p.ch;
  for (let i = 0; i < N; i++) { p.T[i] *= fade; p.P[i] *= fade; }

  for (let k = 0; k < VOICES; k++) {
    const v = p.voices[k];
    const pb0 = v.pb;
    v.pb += dt * bps;
    if (v.hasBrush) {
      const t0 = clamp01(pb0 / BRUSH_BEATS), t1 = clamp01(v.pb / BRUSH_BEATS);
      if (t1 > t0) paintBrush(p, v, t0, t1);
    }
    if (v.hasPen) {
      const t0 = clamp01((pb0 - PEN_DELAY) / PEN_BEATS), t1 = clamp01((v.pb - PEN_DELAY) / PEN_BEATS);
      if (t1 > t0) paintPen(p, v, k, t0, t1);
    }
    if (v.pb >= v.phraseLen) newPhrase(p, v, k);
  }
}

export function draw(display, params, time) {
  const p = params, W = display.width, H = display.height;
  if (p.w !== W || p.h !== H) init(p, W, H);
  step(p, p.dt);

  const pa = PAPER_LEVEL * p.paperS;
  const purple = [0, 1, 2].map((c) => PURPLE_NIGHT[c] + (PURPLE[c] - PURPLE_NIGHT[c]) * p.paperS);
  const kick = Math.exp(-p.beatF * 5);
  // A half (the whole paper) at the bottom of the knob, 1x in the middle, 3x at the top.
  const zl = p.zoomS < 0.5 ? (p.zoomS - 0.5) * 2 : (p.zoomS - 0.5) * 2 * 1.585;
  const zoom = Math.exp(zl * 0.693147) * (1 + 0.06 * p.jiveS * kick);
  const ca = Math.cos(p.angle) / zoom, sa = Math.sin(p.angle) / zoom;
  const jiveA = p.S * 3.2 * p.jiveS * (0.35 + 0.65 * kick);   // the purple dances on the beat
  const jiveL = 6 * p.S, jiveShift = (p.beatN & 1) * 0.5;
  const cw = p.cw, ch = p.ch;
  for (let y = 0; y < H; y++) {
    let sy = y + 0.5 - H * 0.5;
    if (p.mirror === 2) sy = Math.abs(sy);
    for (let x = 0; x < W; x++) {
      let sx = x + 0.5 - W * 0.5;
      if (p.mirror >= 1) sx = Math.abs(sx);
      const u = ca * sx + sa * sy + cw * 0.5, v = -sa * sx + ca * sy + ch * 0.5;
      const iu = wrap(Math.floor(u), cw);
      const i = wrap(Math.floor(v), ch) * cw + iu;
      const j = wrap(Math.floor(v + jiveA * tri(u / jiveL + jiveShift)), ch) * cw + iu;
      const tc = clamp01((p.T[i] - TEAL_FLOOR - p.tooth[i] * TEAL_TOOTH) / GRIP);
      const pc = clamp01((p.P[j] - PURPLE_FLOOR - p.tooth[j] * PURPLE_TOOTH) / GRIP), sh = p.Sh[i];
      const grain = (h01(911, y * W + x) - 0.5) * 10 * pa;
      let r = PAPER_HI[0] * pa + grain, g = PAPER_HI[1] * pa + grain, b = PAPER_HI[2] * pa + grain;
      r += (TEAL_LIGHT[0] + (TEAL_DARK[0] - TEAL_LIGHT[0]) * sh - r) * tc;
      g += (TEAL_LIGHT[1] + (TEAL_DARK[1] - TEAL_LIGHT[1]) * sh - g) * tc;
      b += (TEAL_LIGHT[2] + (TEAL_DARK[2] - TEAL_LIGHT[2]) * sh - b) * tc;
      r += (purple[0] - r) * pc;
      g += (purple[1] - g) * pc;
      b += (purple[2] - b) * pc;
      display.setPixel(x, y, r < 0 ? 0 : r | 0, g < 0 ? 0 : g | 0, b < 0 ? 0 : b | 0);
    }
  }
}
