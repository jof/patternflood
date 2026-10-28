// ===== Patternflow pattern =====
// Title:    Floaters
// Author:   @rubyfocus
// Based on: "LavaLamp" by @WollyMeister — https://patternflow.work/community/p/acbfdd1510e844bb
// Source:   https://community.patternflow.work/community/p/a0de133274a24074
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the original is a Pattern Lab layer
// stack whose wrapper fixes the canvas at 64 x 128; its top layer (the lava lamp, recoloured by
// luminance through the iridescent ramp) covers the bottom one completely, so here that one
// layer is drawn straight onto the square with the same ramp. The lamp is now 2 units wide
// instead of 1, at the same 64 px per unit, so the blobs keep their size, speed and goo in pixels
// and twice as many of them share the twice-as-wide lamp: Blobs runs 6..24 (15 by default,
// the original's 3..12 and 8), sizes go as sqrt(10 / n) instead of sqrt(5 / n), and 24 home
// columns are spread across the width. The pool keeps its wavelength, so it carries about two
// gentle waves instead of one. The output gamma of 2 is a square, not a Math.pow.

// @matrix 128x128
// @knobs Speed=0.1..2, Blobs=6..24, Goo=0..1, Palette=0..1

// Knob 1 (Speed):   How fast the wax moves (1 = relaxed lamp pace)
// Knob 2 (Blobs):   Number of blobs; fewer blobs are bigger
// Knob 3 (Goo):     How readily blobs melt into each other
// Knob 4 (Palette): Classic, Lagoon, Sunset, Emerald, Twilight, Moonlight —
//                   each knob position settles on one, gliding between them

const MAX_BLOBS    = 24;    // the original: 12 in a lamp half as wide
const BLOB_NORM    = 10;    // size = sqrt(BLOB_NORM / n); the original: 5

// Blob cycle (vertical units: the panel spans y = -1 (top) .. +1 (bottom))
const RISE_MIN   = 0.13, RISE_MAX = 0.26;   // rising speed range
const SINK_MIN   = 0.07, SINK_MAX = 0.14;   // sinking is slower, like cooling wax
const TURN_TOP_MIN = -0.82, TURN_TOP_MAX = -0.05;  // where a rising blob turns back
const REST_Y     = 0.96;   // blobs rest here, sunk into the pool
const REST_MIN   = 1.0,  REST_MAX = 9.0;    // seconds spent warming at the bottom
const ACCEL      = 0.55;   // how gently blobs change speed (lower = floatier)
const STRETCH    = 2.2;    // moving blobs elongate vertically (per unit of speed)
const STRETCH_MAX = 0.40;

// Shape: every blob wobbles through its own slowly turning lobes (2- and
// 3-fold ripples of its outline), has its own resting proportions, and
// trails a teardrop tail behind it while it moves.
const LOBE2_MIN  = 0.06, LOBE2_MAX = 0.24;  // oval / peanut-ness
const LOBE3_MIN  = 0.00, LOBE3_MAX = 0.14;  // three-cornered lumpiness
const LOBE_TURN  = 0.16;   // max turning speed of the lobes (radians/s)
const ASPECT_VAR = 0.18;   // resting proportions: up to this much taller or wider
const TAIL       = 2.0;    // teardrop tail per unit of speed
const TAIL_MAX   = 0.45;
const DRIFT      = 0.0875; // horizontal wandering, units (the original's 0.35 * 0.5 on a half-unit lamp)
const BREATHE    = 0.08;   // how much each blob's radius swells and shrinks
const BLOB_R     = 0.19;   // base blob radius (64 px per unit)
const SPREAD     = 0.90;   // how much of the width the blobs' home columns use

// Shape and light
const AA         = 0.035;  // edge softness (~1 LED)
const POOL_Y     = 0.84;   // wax pool along the bottom edge
const POOL_WAVE  = 0.05;
const POOL_FREQ  = 6.8;    // radians per unit: the original's wavelength
const GLOW_FALL  = 5.0;    // how quickly the halo fades into the liquid
const GLOW_AMT   = 0.55;
const CORE_DEPTH = 0.22;   // how far inside the wax the bright core is reached
const LIQ_BREATHE = 0.10;  // slow brightness breathing of the lit liquid

// Each palette: wax edge, wax core (hot centre), liquid top, liquid bottom
// (the lit end), and the halo colour the wax casts.
const PALETTES = [
  { // Classic: orange wax in purple liquid
    edge: [0.88, 0.16, 0.04], core: [1.00, 0.70, 0.16],
    top:  [0.05, 0.01, 0.09], bot:  [0.40, 0.06, 0.32], halo: [0.95, 0.30, 0.10],
  },
  { // Lagoon: aqua wax in deep blue
    edge: [0.02, 0.52, 0.62], core: [0.55, 1.00, 0.88],
    top:  [0.01, 0.02, 0.10], bot:  [0.10, 0.12, 0.45], halo: [0.10, 0.70, 0.80],
  },
  { // Sunset: rose and amber in indigo
    edge: [0.92, 0.20, 0.42], core: [1.00, 0.80, 0.40],
    top:  [0.04, 0.02, 0.14], bot:  [0.50, 0.14, 0.18], halo: [1.00, 0.40, 0.30],
  },
  { // Emerald: lime wax in dark sea-green
    edge: [0.08, 0.58, 0.18], core: [0.82, 1.00, 0.40],
    top:  [0.00, 0.04, 0.05], bot:  [0.04, 0.26, 0.28], halo: [0.40, 0.90, 0.30],
  },
  { // Twilight: lavender wax over a teal glow
    edge: [0.52, 0.18, 0.90], core: [0.96, 0.80, 1.00],
    top:  [0.02, 0.01, 0.10], bot:  [0.04, 0.30, 0.38], halo: [0.60, 0.40, 1.00],
  },
  { // Moonlight: pale silver-blue wax in near-black
    edge: [0.34, 0.46, 0.76], core: [0.94, 0.97, 1.00],
    top:  [0.00, 0.00, 0.03], bot:  [0.08, 0.10, 0.20], halo: [0.60, 0.70, 1.00],
  },
];
const NUM_PAL = PALETTES.length;

// The layer's recolour ramp: luminance of the lamp -> RGB.
const RAMP = [
  127,14,62,125,20,71,123,25,80,120,30,88,117,34,95,113,38,102,110,42,109,106,46,114,102,50,119,98,54,124,
  93,57,128,88,61,131,83,65,133,78,68,135,73,71,136,68,75,137,63,78,137,57,81,136,52,84,135,47,87,133,
  42,89,131,38,92,129,35,94,126,33,96,123,32,98,120,33,99,117,36,101,114,39,102,110,43,103,107,48,104,104,
  53,104,101,58,105,99,63,105,96,69,105,94,73,106,92,78,106,91,83,106,90,87,106,90,91,106,90,94,106,91,
  97,106,91,100,106,93,102,106,94,105,106,96,106,107,99,106,106,99,104,105,97,101,103,95,99,102,93,96,100,92,
  93,99,90,91,97,89,88,96,87,85,95,86,82,93,85,80,92,84,77,90,83,74,89,82,71,87,82,69,86,81,
  66,84,81,63,82,80,61,81,80,58,79,79,56,77,79,54,76,79,52,74,78,50,72,78,49,70,78,47,68,77,
  46,66,77,45,64,76,44,62,76,44,60,75,43,58,74,43,56,73,43,54,72,43,52,71,43,49,70,43,47,68,
  43,45,67,43,43,65,44,41,63,44,38,61,47,39,64,51,41,67,54,42,69,58,44,72,62,45,75,66,46,77,
  70,48,79,75,49,81,79,50,83,83,52,85,88,53,87,92,54,88,97,56,90,102,57,91,107,58,92,111,60,92,
  116,61,93,121,62,93,126,64,93,130,65,93,135,66,92,140,68,92,145,69,91,149,71,90,154,73,89,159,75,87,
  163,76,85,168,78,83,172,81,81,176,83,79,180,85,76,184,88,73,188,90,70,192,93,66,196,96,62,199,99,57,
  202,102,52,205,106,47,208,109,40,211,113,32,213,117,21,215,121,3,215,126,0,215,131,0,216,136,0,216,141,0,
  216,146,0,216,151,0,215,155,0,215,160,0,215,165,0,214,170,0,214,175,0,213,180,0,211,185,0,210,190,0,
  208,195,0,206,200,0,203,205,0,200,211,0,196,216,0,191,222,0,184,228,0,177,234,22,170,239,45,156,245,69,
  97,251,123,0,252,169,0,247,205,0,243,230,0,239,251,114,228,255,146,220,255,163,214,255,176,209,255,186,203,255,
  197,198,255,210,191,255,226,181,255,252,164,255,255,166,227,255,169,205,255,170,186,255,170,169,255,171,150,255,171,128,
  255,172,103,255,170,107,255,168,110,255,166,114,255,164,117,255,162,120,255,160,123,255,158,125,255,157,129,254,155,132,
  253,154,135,252,152,139,251,151,142,249,150,146,248,149,149,246,148,152,245,147,156,243,146,159,241,145,162,239,144,165,
  237,144,168,234,143,171,232,143,174,229,142,177,227,142,180,224,141,182,221,141,185,218,141,187,215,141,189,212,141,192,
  209,140,194,206,140,196,203,140,198,200,140,199,196,140,201,193,141,202,189,141,204,186,141,205,182,141,206,179,141,207,
  175,141,207,171,142,208,168,142,209,164,142,209,160,142,209,156,142,209,153,143,209,149,143,209,145,143,208,141,143,208,
  137,144,207,134,144,206,130,144,205,126,144,204,122,144,203,119,144,201,115,145,200,111,145,198,108,145,196,104,145,195,
  101,145,193,98,145,191,94,145,188,91,145,186,88,145,184,85,145,181,83,144,179,80,144,176,78,144,173,75,144,171,
  73,143,168,72,143,165,70,143,162,69,142,159,68,142,156,67,141,153,66,141,150,66,140,147,66,140,144,66,139,141,
  66,138,138,66,137,135,67,137,132,68,136,129,69,135,126,70,134,123,
];

function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }
function mix(a, b, t) { return a + (b - a) * t; }
function smoothstep(e0, e1, x) {
  const t = clamp((x - e0) / (e1 - e0), 0, 1);
  return t * t * (3 - 2 * t);
}
function mix3(a, b, t, out) {
  out[0] = mix(a[0], b[0], t); out[1] = mix(a[1], b[1], t); out[2] = mix(a[2], b[2], t);
}

// Small deterministic PRNG so every run starts alike.
function makeRng(seed) {
  let s = seed >>> 0;
  return function () {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function setup(params) {
  params.t        = 0.0;
  params.speed    = 1.0;
  params.nBlobs   = 10;
  params.goo      = 0.5;
  params.palette  = 0.0;
  params.palS     = 0.0;   // smoothed palette position
  params.sizeS    = 1.0;   // smoothed size scale

  const rnd = makeRng(20260925);
  params.rnd = rnd;
  params.blobs = [];
  for (let i = 0; i < MAX_BLOBS; i++) {
    const rising = rnd() < 0.5;
    params.blobs.push({
      baseX: ((((i * 7) % MAX_BLOBS) + 0.5) / MAX_BLOBS * 2 - 1) * SPREAD, // shuffled columns
      y:     mix(-0.7, REST_Y, ((i * 5) % MAX_BLOBS + rnd()) / MAX_BLOBS),
      vy:    0,
      mode:  rising ? 1 : 2,          // 0 = resting, 1 = rising, 2 = sinking
      timer: 0,
      vRise: mix(RISE_MIN, RISE_MAX, rnd()),
      vSink: mix(SINK_MIN, SINK_MAX, rnd()),
      turn:  mix(TURN_TOP_MIN, TURN_TOP_MAX, rnd()),
      size:  mix(0.75, 1.25, rnd()),
      phX:   rnd() * 6.2832,
      frX:   mix(0.05, 0.11, rnd()),
      phR:   rnd() * 6.2832,
      frR:   mix(0.20, 0.40, rnd()),
      vis:   i < 10 ? 1 : 0,
      a2:    mix(LOBE2_MIN, LOBE2_MAX, rnd()),
      a3:    mix(LOBE3_MIN, LOBE3_MAX, rnd()),
      ph2:   rnd() * 6.2832,
      ph3:   rnd() * 6.2832,
      w2:    mix(-LOBE_TURN, LOBE_TURN, rnd()),
      w3:    mix(-LOBE_TURN, LOBE_TURN, rnd()),
      phA:   rnd() * 6.2832,
      frA:   mix(0.04, 0.10, rnd()),
      asp:   1 + mix(-ASPECT_VAR, ASPECT_VAR, rnd()),
      x: 0, r: 0, sx: 1, sy: 1,
      c2: 1, s2: 0, c3: 1, s3: 0, amp: 1, tail: 0, tdir: 1,
    });
  }
  params.cols = { edge: [0,0,0], core: [0,0,0], top: [0,0,0], bot: [0,0,0], halo: [0,0,0] };
}

function update(dt, input, params) {
  if (input && input.knobValues) {
    params.speed   = input.knobValues[0];
    params.nBlobs  = Math.round(input.knobValues[1]);
    params.goo     = input.knobValues[2];
    params.palette = input.knobValues[3];
  }
  const sdt = Math.min(dt, 0.1) * params.speed;   // simulation time step
  params.t += sdt;

  // Ease the palette position and the blob size, so knob turns glide.
  const ease = 1 - Math.exp(-3.0 * dt);
  const palTarget = Math.round(clamp(params.palette, 0, 1) * (NUM_PAL - 1)) / (NUM_PAL - 1);
  const palEase = 1 - Math.exp(-1.2 * dt);   // slow, dreamy crossfade
  params.palS += (palTarget - params.palS) * palEase;
  const n = clamp(params.nBlobs, 6, MAX_BLOBS);
  const targetSize = Math.sqrt(BLOB_NORM / n);    // fewer blobs -> bigger blobs
  params.sizeS += (targetSize - params.sizeS) * ease;

  const fade = 1 - Math.exp(-1.5 * dt);
  for (let i = 0; i < MAX_BLOBS; i++) {
    const b = params.blobs[i];
    b.vis += ((i < n ? 1 : 0) - b.vis) * fade;

    // The lamp cycle: rest (warming) -> rise -> turn -> sink -> rest ...
    const rnd = params.rnd;
    let target;
    if (b.mode === 0) {
      target = (REST_Y - b.y) * 0.8;               // settle into the pool
      b.timer -= sdt;
      if (b.timer <= 0) {
        b.mode = 1;
        b.vRise = mix(RISE_MIN, RISE_MAX, rnd());
        b.turn  = mix(TURN_TOP_MIN, TURN_TOP_MAX, rnd());
      }
    } else if (b.mode === 1) {
      target = -b.vRise;                            // up (negative y)
      if (b.y < b.turn) { b.mode = 2; b.vSink = mix(SINK_MIN, SINK_MAX, rnd()); }
    } else {
      target = b.vSink;                             // down
      if (b.y > REST_Y) { b.mode = 0; b.timer = mix(REST_MIN, REST_MAX, rnd()); }
    }
    b.vy += (target - b.vy) * (1 - Math.exp(-ACCEL * sdt));
    b.y  += b.vy * sdt;

    // Elongate while moving; the vertical radius grows, the horizontal shrinks a bit.
    const st = Math.min(STRETCH_MAX, Math.abs(b.vy) * STRETCH);
    b.sy = 1 / ((1 + st) * b.asp);   // smaller = taller
    b.sx = (1 + st * 0.35) * b.asp;  // larger = narrower

    // Slowly turning lobes, whose strength itself ebbs and flows.
    const a2 = b.ph2 + params.t * b.w2, a3 = b.ph3 + params.t * b.w3;
    b.c2 = Math.cos(a2); b.s2 = Math.sin(a2);
    b.c3 = Math.cos(a3); b.s3 = Math.sin(a3);
    b.amp = 0.6 + 0.4 * Math.sin(params.t * b.frA * 6.2832 + b.phA);

    // Teardrop tail trailing behind the direction of travel (y points down).
    b.tail = Math.min(TAIL_MAX, Math.abs(b.vy) * TAIL);
    b.tdir = b.vy < 0 ? 1 : -1;
    b.x = b.baseX + DRIFT * Math.sin(params.t * b.frX * 6.2832 + b.phX);
    b.r = BLOB_R * b.size * params.sizeS * b.vis *
          (1 + BREATHE * Math.sin(params.t * b.frR * 6.2832 + b.phR));
  }
}

function draw(display, params, time) {
  const w = display.width, h = display.height;
  const aspect = w / Math.max(1, h);
  const t = params.t;

  // Crossfade the palette once per frame.
  const pf = clamp(params.palS, 0, 1) * (NUM_PAL - 1);
  const p0 = Math.floor(pf), p1 = Math.min(NUM_PAL - 1, p0 + 1), pt = pf - p0;
  const A = PALETTES[p0], B = PALETTES[p1], C = params.cols;
  mix3(A.edge, B.edge, pt, C.edge); mix3(A.core, B.core, pt, C.core);
  mix3(A.top,  B.top,  pt, C.top);  mix3(A.bot,  B.bot,  pt, C.bot);
  mix3(A.halo, B.halo, pt, C.halo);
  const er = C.edge[0], eg = C.edge[1], eb = C.edge[2];
  const kr = C.core[0] - er, kg = C.core[1] - eg, kb = C.core[2] - eb;
  const hr = C.halo[0], hg = C.halo[1], hb = C.halo[2];

  const k = mix(0.03, 0.26, clamp(params.goo, 0, 1));   // smooth-union size
  const breathe = 1 + LIQ_BREATHE * Math.sin(t * 0.35);

  // Only blobs that are at least a little visible take part, flattened for the pixel loop.
  const blobs = params.blobs;
  const act = [];
  for (let i = 0; i < MAX_BLOBS; i++) if (blobs[i].r > 0.005) act.push(blobs[i]);
  const na = act.length;
  const BX = new Float64Array(na), BY = new Float64Array(na), SX = new Float64Array(na);
  const SY = new Float64Array(na), R = new Float64Array(na), A2 = new Float64Array(na);
  const S2 = new Float64Array(na), A3 = new Float64Array(na), S3 = new Float64Array(na);
  const C2 = new Float64Array(na), C3 = new Float64Array(na), TL = new Float64Array(na);
  const TD = new Float64Array(na), RM = new Float64Array(na);
  for (let i = 0; i < na; i++) {
    const b = act[i];
    BX[i] = b.x; BY[i] = b.y; SX[i] = b.sx; SY[i] = b.sy; R[i] = b.r;
    A2[i] = b.amp * b.a2 * b.c2; S2[i] = b.amp * b.a2 * b.s2;
    A3[i] = b.amp * b.a3 * b.c3; S3[i] = b.amp * b.a3 * b.s3;
    TL[i] = b.tail; TD[i] = b.tdir;
    // The farthest its outline reaches (in its own stretched frame): past this, smin can't change d.
    RM[i] = b.r * (1 + Math.hypot(A2[i], S2[i]) + Math.hypot(A3[i], S3[i]) + b.tail);
  }
  const order = new Int32Array(na), key = new Float64Array(na);

  // The pool surface per column.
  const pool = params.pool && params.pool.length === w ? params.pool : (params.pool = new Float64Array(w));
  for (let x = 0; x < w; x++) {
    const nx = ((x + 0.5) / w - 0.5) * 2.0 * aspect;
    pool[x] = POOL_Y + POOL_WAVE * Math.sin(nx * POOL_FREQ + t * 0.30);
  }
  const kInv = k > 1e-5 ? 0.5 / k : 0;

  for (let y = 0; y < h; y++) {
    const ny = ((y + 0.5) / h - 0.5) * 2.0;
    // Liquid: dark at the top, lit from below.
    const lit = smoothstep(-1.0, 1.0, ny);
    const lit2 = lit * lit * breathe;
    const lr = mix(C.top[0], C.bot[0], lit2);
    const lg = mix(C.top[1], C.bot[1], lit2);
    const lb = mix(C.top[2], C.bot[2], lit2);
    const hl = 0.4 + 0.6 * lit;

    // Blobs nearest this row first, so d drops early and the far ones can be skipped exactly.
    for (let i = 0; i < na; i++) {
      const v = Math.abs(ny - BY[i]) * SY[i];
      let j = i;
      while (j > 0 && key[j - 1] > v) { key[j] = key[j - 1]; order[j] = order[j - 1]; j--; }
      key[j] = v; order[j] = i;
    }

    for (let x = 0; x < w; x++) {
      const nx = ((x + 0.5) / w - 0.5) * 2.0 * aspect;

      // Wax pool along the bottom (distance is negative inside the wax).
      let d = pool[x] - ny;

      for (let q = 0; q < na; q++) {
        const i = order[q];
        const dx = (nx - BX[i]) * SX[i], dy = (ny - BY[i]) * SY[i];
        const dd2 = dx * dx + dy * dy, reach = d + k + RM[i];
        if (reach <= 0 || dd2 >= reach * reach) continue;   // di >= d + k: smin leaves d as it is
        const dist = Math.sqrt(dd2);
        let def = 0;
        if (dist > 1e-4) {
          // Direction from the blob centre and its 2x / 3x multiples (angle addition).
          const inv = 1 / dist, c = dx * inv, sn = dy * inv;
          const c2 = c * c - sn * sn, s2 = 2 * c * sn;
          const c3 = c * c2 - sn * s2, s3 = sn * c2 + c * s2;
          def = c2 * A2[i] + s2 * S2[i] + c3 * A3[i] + s3 * S3[i];
          const ts = sn * TD[i];
          if (ts > 0) def += TL[i] * ts * ts;
        }
        const di = dist - R[i] * (1 + def);
        // Polynomial smooth-min with a rounded neck of size k.
        if (kInv === 0) { if (di < d) d = di; }
        else {
          const hh = 0.5 + (di - d) * kInv;            // smin(d, di, k)
          if (hh <= 0) d = di;
          else if (hh < 1) d = di + (d - di) * hh - k * hh * (1 - hh);
        }
      }

      // Wax body: soft edge, hot bright core deeper inside.
      const wax   = smoothstep(AA, -AA, d);
      let depth = -d / CORE_DEPTH; depth = depth < 0 ? 0 : depth > 1 ? 1 : depth;
      const cw    = depth * (2 - depth);   // ease-out into the core
      // Halo the wax casts into the liquid.
      const fall = 1 / (1 + (d > 0 ? d : 0) * GLOW_FALL);
      const glow = GLOW_AMT * fall * fall * hl;
      const br = lr + hr * glow, bg = lg + hg * glow, bb = lb + hb * glow;

      let r = br + (er + kr * cw - br) * wax;
      let g = bg + (eg + kg * cw - bg) * wax;
      let bl = bb + (eb + kb * cw - bb) * wax;
      r = r < 0 ? 0 : r > 1 ? 1 : r; g = g < 0 ? 0 : g > 1 ? 1 : g; bl = bl < 0 ? 0 : bl > 1 ? 1 : bl;

      // LED gamma 2, then the layer's recolour by luminance.
      const lum = Math.round(0.2126 * Math.floor(r * r * 255) + 0.7152 * Math.floor(g * g * 255) +
                             0.0722 * Math.floor(bl * bl * 255)) * 3;
      display.setPixel(x, y, RAMP[lum], RAMP[lum + 1], RAMP[lum + 2]);
    }
  }
}
