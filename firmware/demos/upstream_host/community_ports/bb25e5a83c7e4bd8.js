// ===== Patternflow pattern =====
// Title:    CALM TURING
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/bb25e5a83c7e4bd8
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the original is a Pattern Lab layer
// stack whose wrapper fixes the canvas at 64 x 128: two copies of the same panel composition,
// each with its own random layout, the first drawn as is and the second recoloured through a
// rainbow ramp and added. Here both run on the full square. The strips keep their heights (the
// square is as tall as the original), and each strip is split into up to five tiles instead of
// three (29 tiles in all instead of 19), so panels stay about the size they were and there are
// half again as many sliding, swapping, cross-fading ones; the split points glide around their
// own homes as before, and a two-tile strip can still wipe one tile away. The Turing mazes and
// spot arrays, the scanlines, streaks and dust all keep their scale in pixels, so twice the area
// shows twice the structure. All the photosensitivity limits are untouched.
// Cost: the two layers share one pair of reaction-diffusion fields (128 x 128) instead of
// simulating two pairs each (64 x 128), which keeps the simulation's cost per frame where the
// original's was; the second layer reads them shifted by about half the square (they wrap), so
// its mazes and spots still fall between the first layer's, as two separate fields did. The warm-up starts from 120 seeds per field and runs 500 steps instead of
// 40 and 800, which comes out about as mature in a bit over half the time. The second layer's
// palette and ramp are folded into one table.

// @matrix 128x128
// @knobs Speed=0.1..0.6, Glow=0.4..1, Mix=0..1, Warp=0..1

// =============================================================================
//  CALM TURING
//  (Originally a vertical 64x128 canvas; here 128x128.) Glowing cyan / deep-blue dots on pitch black.
//
//  Look    Modular rectangular panels and thin horizontal strips that slide,
//          wipe and re-assign themselves. Inside them live real Gray-Scott
//          Turing mazes, hex-spaced spot arrays, deep-blue data streaks, soft
//          scanlines and sparse dim dots.
//
//  Safety  Every "glitch" gesture of the reference is re-expressed as slow,
//          eased motion for photosensitive viewers:
//    - every oscillator and the beat clock live inside 0.1-0.6 Hz
//      (HZ_MIN / HZ_MAX). The Speed knob is hard-clamped to that band, no
//      matter how its range fields are edited.
//    - no strobing: sine / smoothstep easing only. Panel edges are feathered
//      (softer the faster they move) and texture swaps cross-fade for >= 1.6 s.
//    - two low-pass stages plus a per-pixel slew limiter (SLEW) mean no pixel's
//      brightness can swing 0 -> 1 -> 0 faster than 0.6 Hz, whatever a texture does.
//    - soft spatial detail: scanlines sit 4 px apart with a gaussian profile,
//      the maze / spot fields are band-limited, dust is dim and static.
//    - organic motion: reaction-diffusion morphing, drifting streaks, gently
//      warped lines.
//
//  Controls
//    Knob 1  Speed  0.1-0.6 Hz   master cycle rate
//    Knob 2  Glow   0.4-1        brightness and bloom
//    Knob 3  Mix    0-1          0 = mostly Turing mazes ... 1 = more grids, streaks, dust
//    Knob 4  Warp   0-1          how much the textures bend and morph
//    Push 1  seed new Turing growth      (one-shot pushes are limited to 0.6 Hz)
//    Push 2  next beat now
//    Push 3  hold = ease to a gentle stop, release = ease back
//    Push 4  re-roll every panel texture (cross-faded)
// =============================================================================


const TAU = 6.283185307179586;

// ---- safety envelope (single source of truth) -------------------------------
const HZ_MIN = 0.1;            // slowest oscillation used anywhere
const HZ_MAX = 0.6;            // fastest oscillation used anywhere (hazard zone starts at 3 Hz)
const MIN_BEAT = 1 / HZ_MAX;   // user-triggered beats can never exceed the max cadence
const SLEW = 1.2;              // max value change per second per pixel: 0 -> 1 takes 0.83 s
const TAU_LP = 0.16;           // two cascaded low-pass stages of this time constant (seconds)
const VMAX = 2.6;              // fastest panel edge, px/s
const FW_MIN = 1.2, FW_MAX = 3.6, FW_K = 0.9;  // edge feather px: crisp at rest, softer in motion
const FADE_MIN = 1.6;          // shortest texture cross-fade, seconds
const SEAM = 0.45;             // depth of the thin dark seam between panels (0 = none)
const SEAM_K = 0.89;           // 1 / (2 * sigma^2), sigma = 0.75 px

// ---- layout recipe: horizontal strips, each split into up to 3 tiles ---------
// 128 px wide: each strip has about twice the tiles the 64-wide original had (29 instead of 19).
const NB = 9, MC = 5, MC1 = MC + 1;
const BAND_H  = [0.17, 0.045, 0.13, 0.07, 0.20, 0.05, 0.14, 0.065, 0.13];  // fraction of height
const BAND_NC = [3, 2, 5, 3, 4, 1, 5, 3, 3];                                // tiles per strip
const BAND_X  = [[0.31, 0.66], [0.55], [0.16, 0.36, 0.58, 0.80], [0.27, 0.63], [0.22, 0.47, 0.74], [],
                 [0.18, 0.37, 0.53, 0.79], [0.30, 0.69], [0.26, 0.62]];
const BAND_T  = [[0, 1, 2], [3, 2], [1, 5, 0, 2, 1], [2, 4, 3], [0, 2, 1, 0], [3], [4, 1, 2, 0, 5],
                 [2, 3, 4], [0, 1, 0]];
const THIN    = [0, 1, 0, 1, 0, 1, 0, 1, 0];
const MAX_VOIDS = 5;           // the original: 3 of 19 tiles
const MINH = 4, MINW = 9;      // min strip height / tile width in px

const T_MAZE = 0, T_SPOT = 1, T_BAND = 2, T_LINE = 3, T_NOISE = 4, T_VOID = 5, NT = 6;

// ---- reaction-diffusion (Gray-Scott, 9-point isotropic stencil, toroidal) ----
const RD_DT = 2.0;
const RD_BURN = 500;                    // warm-up steps so the first frame is already mature
const RD_SEEDS = 120;                   // warm-up seeds per field (the original: 40 on half the area, 800 steps)
const RD_RATE0 = 45, RD_RATE1 = 140;    // sim steps per second at Speed min / max
const RD_MAXSTEPS = 6;
const WK_X = [0.13, -0.09, 0.05], WK_Y = [0.05, 0.11, -0.13];   // feed-wave vectors (rad/px)
const WLO = [0.10, 0.12, 0.10], WHI = [0.22, 0.32, 0.18];       // each wave: Hz at Speed min / max
const WPH = [0.4, 2.2, 4.1];

// ---- palette measured from the reference: navy -> azure -> electric cyan ----
const PAL_V = [0, 0.10, 0.25, 0.40, 0.55, 0.70, 0.85, 0.95, 1.0];
const PAL_R = [0, 1, 3, 7, 15, 26, 38, 64, 96];
const PAL_G = [0, 8, 24, 49, 80, 124, 190, 224, 232];
const PAL_B = [0, 25, 58, 98, 138, 186, 242, 255, 255];
const CHEM_LO = 0.06, CHEM_SPAN = 0.28, CHEM_PEAK = 0.95, CHEM_GAMMA = 1.35;

// ---- small helpers ----------------------------------------------------------
function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
function sstep(a, b, x) {
  let t = (x - a) / (b - a);
  t = t < 0 ? 0 : t > 1 ? 1 : t;
  return t * t * (3 - 2 * t);
}
function hash2(ix, iy) {
  let h = (Math.imul(ix, 374761393) + Math.imul(iy, 668265263)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
function vnoise(u, v) {
  const iu = Math.floor(u), iv = Math.floor(v);
  let fu = u - iu, fv = v - iv;
  fu = fu * fu * (3 - 2 * fu);
  fv = fv * fv * (3 - 2 * fv);
  const a = hash2(iu, iv), b = hash2(iu + 1, iv), c = hash2(iu, iv + 1), d = hash2(iu + 1, iv + 1);
  return a + (b - a) * fu + (c - a) * fv + (a - b - c + d) * fu * fv;
}
function vnoise1(u, s) {
  const i = Math.floor(u);
  let f = u - i;
  f = f * f * (3 - 2 * f);
  const a = hash2(i, s), b = hash2(i + 1, s);
  return a + (b - a) * f;
}

// ---- reaction-diffusion -------------------------------------------------------
function rdAlloc(N) {
  return { u: new Float32Array(N), v: new Float32Array(N), u2: new Float32Array(N), v2: new Float32Array(N) };
}

function rdSeed(f, W, H, blobs, reset) {
  const N = W * H;
  if (reset) {
    f.u.fill(1);
    f.v.fill(0);
    for (let i = 0; i < N; i++) {
      f.u[i] += (Math.random() - 0.5) * 0.02;
      f.v[i] += Math.random() * 0.02;
    }
  }
  for (let b = 0; b < blobs; b++) {
    const cx = (Math.random() * W) | 0, cy = (Math.random() * H) | 0;
    for (let dy = -2; dy <= 2; dy++) {
      for (let dx = -2; dx <= 2; dx++) {
        const c = ((cy + dy + H) % H) * W + ((cx + dx + W) % W);
        f.u[c] = 0.5;
        f.v[c] = 0.25;
      }
    }
  }
}

function rdStep(f, wm, W, H, Du, Dv, F0, dF, k, dt) {
  const u = f.u, v = f.v, u2 = f.u2, v2 = f.v2;
  for (let y = 0; y < H; y++) {
    const yU = (y === 0 ? H - 1 : y - 1) * W, yC = y * W, yD = (y === H - 1 ? 0 : y + 1) * W;
    for (let x = 0; x < W; x++) {
      const xl = x === 0 ? W - 1 : x - 1, xr = x === W - 1 ? 0 : x + 1;
      const c = yC + x, uc = u[c], vc = v[c];
      const lu = 0.2 * (u[yU + x] + u[yD + x] + u[yC + xl] + u[yC + xr]) +
                 0.05 * (u[yU + xl] + u[yU + xr] + u[yD + xl] + u[yD + xr]) - uc;
      const lv = 0.2 * (v[yU + x] + v[yD + x] + v[yC + xl] + v[yC + xr]) +
                 0.05 * (v[yU + xl] + v[yU + xr] + v[yD + xl] + v[yD + xr]) - vc;
      const F = F0 + dF * wm[c];
      const uvv = uc * vc * vc;
      const nu = uc + dt * (Du * lu - uvv + F * (1 - uc));
      const nv = vc + dt * (Dv * lv + uvv - (F + k) * vc);
      u2[c] = nu < 0 ? 0 : nu > 1 ? 1 : nu;
      v2[c] = nv < 0 ? 0 : nv > 1 ? 1 : nv;
    }
  }
  f.u = u2; f.v = v2; f.u2 = u; f.v2 = v;
}

// Slow travelling waves that nudge the feed rate, so the mazes keep writhing
// and branching. Each wave oscillates inside 0.1-0.6 Hz.
function computeWaves(P) {
  const W = P.W, H = P.H, wm = P.wm;
  for (let q = 0; q < 3; q++) {
    const ph = TAU * (WLO[q] * P.T + (WHI[q] - WLO[q]) * P.S) + WPH[q];
    for (let x = 0; x < W; x++) {
      const a = WK_X[q] * x + ph;
      P.wsx[q * W + x] = Math.sin(a);
      P.wcx[q * W + x] = Math.cos(a);
    }
    for (let y = 0; y < H; y++) {
      const b = WK_Y[q] * y;
      P.wsy[q * H + y] = Math.sin(b);
      P.wcy[q * H + y] = Math.cos(b);
    }
  }
  const sx = P.wsx, cx = P.wcx, sy = P.wsy, cy = P.wcy;
  for (let y = 0; y < H; y++) {
    const s0 = sy[y], c0 = cy[y], s1 = sy[H + y], c1 = cy[H + y], s2 = sy[2 * H + y], c2 = cy[2 * H + y];
    const r = y * W;
    for (let x = 0; x < W; x++) {
      wm[r + x] = (sx[x] * c0 + cx[x] * s0 +
                   sx[W + x] * c1 + cx[W + x] * s1 +
                   sx[2 * W + x] * c2 + cx[2 * W + x] * s2) * 0.3333;
    }
  }
}

// ---- allocation / (re)initialisation ------------------------------------------
function ensure(P, W, H) {
  if (P.ready && P.W === W && P.H === H) return;
  const N = W * H;
  P.W = W; P.H = H; P.N = N;

  // static per-pixel randomness: thresholds, brightness, twinkle, sparkle
  P.hs = new Float32Array(N);
  P.tbr = new Float32Array(N);
  P.tlo = new Float32Array(N);
  P.tdd = new Float32Array(N);
  P.tph = new Float32Array(N);
  P.gain = new Float32Array(N);
  const dl = [];
  for (let p = 0; p < N; p++) {
    P.hs[p] = Math.random();
    P.tbr[p] = 0.22 + 0.63 * Math.random();
    P.tlo[p] = HZ_MIN + 0.10 * Math.random();                    // 0.10-0.20 Hz at Speed min
    P.tdd[p] = (0.30 + 0.30 * Math.random()) - P.tlo[p];         // up to 0.30-0.60 Hz at Speed max
    P.tph[p] = TAU * Math.random();
    P.gain[p] = 0.90 + 0.20 * Math.random();
    if (Math.random() < 0.04) dl.push(p);                        // ~4% of pixels carry faint dust
  }
  P.dustN = dl.length;
  P.dustIdx = new Int32Array(P.dustN);
  P.dustAmp = new Float32Array(P.dustN);
  for (let q = 0; q < P.dustN; q++) { P.dustIdx[q] = dl[q]; P.dustAmp[q] = 0.05 + 0.11 * Math.random(); }
  P.dust = new Float32Array(N);

  // frame buffers
  P.tgt = new Float32Array(N);
  P.disp = new Float32Array(N);
  P.lp1 = new Float32Array(N);
  P.tmp = new Float32Array(N);
  P.out = new Uint8Array(N);       // palette index per pixel, for the compositor

  // palette lookup
  P.lutR = new Uint8Array(256); P.lutG = new Uint8Array(256); P.lutB = new Uint8Array(256);
  for (let i = 0; i < 256; i++) {
    const v = i / 255;
    let k = 1;
    while (k < PAL_V.length - 1 && v > PAL_V[k]) k++;
    const t = (v - PAL_V[k - 1]) / (PAL_V[k] - PAL_V[k - 1]);
    P.lutR[i] = (PAL_R[k - 1] + (PAL_R[k] - PAL_R[k - 1]) * t + 0.5) | 0;
    P.lutG[i] = (PAL_G[k - 1] + (PAL_G[k] - PAL_G[k - 1]) * t + 0.5) | 0;
    P.lutB[i] = (PAL_B[k - 1] + (PAL_B[k] - PAL_B[k - 1]) * t + 0.5) | 0;
  }
  // chemistry v (0..0.4) -> brightness: gamma curve, only the very cores reach cyan, edges stay deep blue
  P.chem = new Float32Array(258);
  for (let i = 0; i < 258; i++) {
    const t = clamp((i / 640 - CHEM_LO) / CHEM_SPAN, 0, 1);
    P.chem[i] = CHEM_PEAK * Math.pow(t, CHEM_GAMMA);
  }
  // static per-row grain for the streak bands
  P.rowG = new Float32Array(H);
  for (let y = 0; y < H; y++) P.rowG[y] = 0.62 + 0.38 * hash2(y, 5);

  // per-frame texture constants
  P.fc = { bw1: 1, bw2: 0, bnrm: 1, shPh: 0, shAmp: 0, lnPh: 0, lnAmp: 0, lw1: 1, lw2: 0, lnrm: 1,
           dw1: 1, dw2: 0, dnrm: 1, gain: 1 };

  // layout state
  P.ybBase = new Float32Array(NB + 1);
  P.yb0 = new Float32Array(NB + 1); P.yb1 = new Float32Array(NB + 1); P.ybG = new Float32Array(NB + 1);
  P.yst = new Float32Array(NB + 1); P.yb = new Float32Array(NB + 1); P.fwY = new Float32Array(NB + 1);
  P.xb0 = new Float32Array(NB * MC1); P.xb1 = new Float32Array(NB * MC1); P.xbG = new Float32Array(NB * MC1);
  P.xst = new Float32Array(NB * MC1); P.xb = new Float32Array(NB * MC1); P.fwX = new Float32Array(NB * MC1);
  let acc = 0;
  for (let k = 0; k <= NB; k++) {
    P.ybBase[k] = acc * H;
    if (k < NB) acc += BAND_H[k];
  }
  P.ybBase[NB] = H;
  for (let k = 0; k <= NB; k++) {
    P.yb0[k] = P.yb1[k] = P.ybG[k] = P.yb[k] = P.ybBase[k];
    P.fwY[k] = FW_MIN;
  }
  for (let i = 0; i < NB; i++) {
    const bx = i * MC1, nc = BAND_NC[i];
    P.xb0[bx] = P.xb1[bx] = P.xbG[bx] = P.xb[bx] = 0;
    P.xb0[bx + nc] = P.xb1[bx + nc] = P.xbG[bx + nc] = P.xb[bx + nc] = W;
    for (let j = 1; j < nc; j++) {
      const x = BAND_X[i][j - 1] * W;
      P.xb0[bx + j] = P.xb1[bx + j] = P.xbG[bx + j] = P.xb[bx + j] = x;
    }
    for (let j = 0; j <= MC; j++) P.fwX[bx + j] = FW_MIN;
  }
  P.tA = new Uint8Array(NB * MC); P.tB = new Uint8Array(NB * MC); P.tm = new Float32Array(NB * MC);
  P.wts = new Float32Array(NT);
  for (let i = 0; i < NB; i++) {
    for (let j = 0; j < MC; j++) {
      const t = j < BAND_NC[i] ? BAND_T[i][j] : T_VOID;
      P.tA[i * MC + j] = t; P.tB[i * MC + j] = t; P.tm[i * MC + j] = 1;
    }
  }
  P.rowB = new Int8Array(H); P.rowO = new Int8Array(H); P.rowW = new Float32Array(H); P.seamY = new Float32Array(H);
  P.colJ = new Int8Array(NB * W); P.colO = new Int8Array(NB * W);
  P.colW = new Float32Array(NB * W); P.seamX = new Float32Array(NB * W);

  P.beat = 0; P.sinceBeat = 0; P.sinceShuf = 99; P.sinceSeed = 99; P.rdAcc = 0; P.frame = 0;
  P.ready = true;
}

// ---- layout: beats pick new targets, positions glide there with easing --------
function pickType(P, thin, cur) {
  const m = P.mix, w = P.wts;
  w[T_MAZE] = thin ? 0 : 4.0 - 3.2 * m;
  w[T_SPOT] = thin ? 0 : 2.6 - 1.6 * m;
  w[T_BAND] = 0.8 + 1.4 * m;
  w[T_LINE] = 0.4 + 1.2 * m;
  w[T_NOISE] = 0.4 + 1.1 * m;
  w[T_VOID] = 0.3 + 0.4 * m;
  let voids = 0;
  for (let i = 0; i < NB; i++) for (let j = 0; j < BAND_NC[i]; j++) if (P.tB[i * MC + j] === T_VOID) voids++;
  if (voids >= MAX_VOIDS) w[T_VOID] = 0;
  w[cur] = 0;
  let sum = 0;
  for (let t = 0; t < NT; t++) sum += w[t];
  let r = Math.random() * sum;
  for (let t = 0; t < NT; t++) {
    r -= w[t];
    if (r <= 0 && w[t] > 0) return t;
  }
  return T_BAND;
}

function swapTile(P, delay) {
  for (let tries = 0; tries < 8; tries++) {
    const i = (Math.random() * NB) | 0;
    const j = (Math.random() * BAND_NC[i]) | 0;
    const idx = i * MC + j;
    if (P.tm[idx] < 1) continue;
    P.tB[idx] = pickType(P, THIN[i], P.tA[idx]);
    P.tm[idx] = -delay * Math.random();
    return;
  }
}

function pickX(P, i, nc, j) {
  const W = P.W, X = BAND_X[i];
  if (nc === 2) {
    if (Math.random() < 0.14) return Math.random() < 0.5 ? -6 : W + 6;   // let a tile wipe away
    return W * (0.25 + 0.5 * Math.random());
  }
  // around its home, by up to 45% of the narrower neighbouring tile
  const home = X[j - 1], lo = j === 1 ? 0 : X[j - 2], hi = j === nc - 1 ? 1 : X[j];
  return W * (home + (Math.random() * 2 - 1) * 0.45 * Math.min(home - lo, hi - home));
}

function newBeat(P) {
  const W = P.W, H = P.H;
  const dmax = 0.47 * VMAX / P.F;      // px an edge may travel per beat: peak speed <= VMAX
  const yb0 = P.yb0, yb1 = P.yb1;
  for (let k = 1; k < NB; k++) yb0[k] = P.yb[k];
  for (let k = 1; k < NB; k++) {
    if (Math.abs(P.ybG[k] - yb0[k]) < 0.8) {
      const span = 0.6 * Math.min(BAND_H[k - 1], BAND_H[k]) * H;
      P.ybG[k] = P.ybBase[k] + (Math.random() * 2 - 1) * span;
    }
    yb1[k] = yb0[k] + clamp(P.ybG[k] - yb0[k], -dmax, dmax);
    P.yst[k] = Math.random() * 0.3;
  }
  for (let k = 1; k < NB; k++) if (yb1[k] < yb1[k - 1] + MINH) yb1[k] = yb1[k - 1] + MINH;
  for (let k = NB - 1; k >= 1; k--) if (yb1[k] > yb1[k + 1] - MINH) yb1[k] = yb1[k + 1] - MINH;

  for (let i = 0; i < NB; i++) {
    const nc = BAND_NC[i];
    if (nc < 2) continue;
    const bx = i * MC1;
    for (let j = 1; j < nc; j++) P.xb0[bx + j] = P.xb[bx + j];
    for (let j = 1; j < nc; j++) {
      if (Math.abs(P.xbG[bx + j] - P.xb0[bx + j]) < 0.8) P.xbG[bx + j] = pickX(P, i, nc, j);
      P.xb1[bx + j] = P.xb0[bx + j] + clamp(P.xbG[bx + j] - P.xb0[bx + j], -dmax, dmax);
      P.xst[bx + j] = Math.random() * 0.3;
    }
    if (nc >= 3) {
      for (let j = 1; j < nc; j++) {
        const lo = j === 1 ? MINW : P.xb1[bx + j - 1] + MINW;
        P.xb1[bx + j] = clamp(P.xb1[bx + j], lo, W - (nc - j) * MINW);
      }
    }
  }
  swapTile(P, 0);
  if (Math.random() < 0.5) swapTile(P, 0);
}

function shuffleAll(P) {
  for (let i = 0; i < NB; i++) {
    for (let j = 0; j < BAND_NC[i]; j++) {
      const idx = i * MC + j;
      if (P.tm[idx] < 1) continue;
      P.tB[idx] = pickType(P, THIN[i], P.tA[idx]);
      P.tm[idx] = -0.8 * Math.random();      // staggered start, then a slow cross-fade
    }
  }
}

// ---- per-frame geometry: soft panel edges, seams, tile weights ----------------
function computeLayout(P) {
  const W = P.W, H = P.H, b = P.beat, fb = P.F * P.z;
  const yb = P.yb, fwY = P.fwY;
  yb[0] = 0; yb[NB] = H; fwY[0] = FW_MIN; fwY[NB] = FW_MIN;
  for (let k = 1; k < NB; k++) {
    const t = clamp((b - P.yst[k]) / 0.7, 0, 1);
    const d = P.yb1[k] - P.yb0[k];
    yb[k] = P.yb0[k] + d * t * t * (3 - 2 * t);
    fwY[k] = Math.min(FW_MAX, FW_MIN + FW_K * Math.abs(d) * 6 * t * (1 - t) * fb / 0.7);
  }
  let i = 0;
  for (let y = 0; y < H; y++) {
    const yc = y + 0.5;
    while (i < NB - 1 && yc >= yb[i + 1]) i++;
    const dT = yc - yb[i], dB = yb[i + 1] - yc;
    let o = -1, w = 0;
    if (i > 0) {
      const h = 0.5 * fwY[i];
      if (dT < h) { o = i - 1; w = 1 - sstep(-h, h, dT); }
    }
    if (o < 0 && i < NB - 1) {
      const h = 0.5 * fwY[i + 1];
      if (dB < h) { o = i + 1; w = 1 - sstep(-h, h, dB); }
    }
    P.rowB[y] = i; P.rowO[y] = o; P.rowW[y] = w;
    let dm = 1e9;
    if (i > 0) dm = dT;
    if (i < NB - 1 && dB < dm) dm = dB;
    P.seamY[y] = 1 - SEAM * Math.exp(-dm * dm * SEAM_K);
  }
  for (let bi = 0; bi < NB; bi++) {
    const nc = BAND_NC[bi], bx = bi * MC1, xb = P.xb, fwX = P.fwX;
    xb[bx] = 0; xb[bx + nc] = W; fwX[bx] = FW_MIN; fwX[bx + nc] = FW_MIN;
    for (let j = 1; j < nc; j++) {
      const t = clamp((b - P.xst[bx + j]) / 0.7, 0, 1);
      const d = P.xb1[bx + j] - P.xb0[bx + j];
      xb[bx + j] = P.xb0[bx + j] + d * t * t * (3 - 2 * t);
      fwX[bx + j] = Math.min(FW_MAX, FW_MIN + FW_K * Math.abs(d) * 6 * t * (1 - t) * fb / 0.7);
    }
    let j = 0;
    const o0 = bi * W;
    for (let x = 0; x < W; x++) {
      const xc = x + 0.5;
      while (j < nc - 1 && xc >= xb[bx + j + 1]) j++;
      const dL = xc - xb[bx + j], dR = xb[bx + j + 1] - xc;
      let o = -1, w = 0;
      if (j > 0) {
        const h = 0.5 * fwX[bx + j];
        if (dL < h) { o = j - 1; w = 1 - sstep(-h, h, dL); }
      }
      if (o < 0 && j < nc - 1) {
        const h = 0.5 * fwX[bx + j + 1];
        if (dR < h) { o = j + 1; w = 1 - sstep(-h, h, dR); }
      }
      if (o >= 0) w *= sstep(0, FW_MAX, xb[bx + o + 1] - xb[bx + o]);   // no ghost slivers from collapsed tiles
      P.colJ[o0 + x] = j; P.colO[o0 + x] = o; P.colW[o0 + x] = w;
      let dm = 1e9;
      if (j > 0) dm = dL;
      if (j < nc - 1 && dR < dm) dm = dR;
      P.seamX[o0 + x] = 1 - SEAM * Math.exp(-dm * dm * SEAM_K);
    }
  }
}

// ---- textures: every one returns brightness 0..1 -------------------------------
function texBand(P, x, y) {
  // deep-blue horizontal streaks: stretched noise, rows slide gently against each other
  const c = P.fc;
  const sh = c.shAmp * Math.sin(y * 0.09 + c.shPh);
  const u = (x + 0.5 + sh) * 0.062, v = (y + 0.5) * 0.46;
  const n = 0.5 + ((vnoise(u, v) - 0.5) * c.bw1 + (vnoise(u + 17.3, v + 9.1) - 0.5) * c.bw2) * c.bnrm;
  const r = sstep(0.50, 0.82, n);
  return r * (0.22 + 0.58 * r) * P.rowG[y];
}

function texLine(P, x, y) {
  // parallel scanlines, 4 px apart, soft gaussian profile, gently warped, dashed
  const c = P.fc;
  const r = y + c.lnAmp * Math.sin(x * 0.11 + c.lnPh);
  const k = Math.floor((r + 2) * 0.25);
  const d = r - k * 4;
  const prof = Math.exp(-d * d * 0.62);
  if (prof < 0.01) return 0;
  const u = (x + 0.5) * 0.05;
  const n = 0.5 + ((vnoise1(u, k) - 0.5) * c.lw1 + (vnoise1(u + 5.7, k + 41) - 0.5) * c.lw2) * c.lnrm;
  return prof * (0.16 + 0.50 * sstep(0.30, 0.66, n));
}

function texNoise(P, x, y, p) {
  // low-density dot field: each dot fades in and out as a slow density field passes it
  const c = P.fc;
  const a0 = x * 0.06, b0 = y * 0.06;
  const n = 0.5 + ((vnoise(a0, b0) - 0.5) * c.dw1 + (vnoise(a0 + 23.1, b0 + 7.7) - 0.5) * c.dw2) * c.dnrm;
  const d = 0.30 * sstep(0.38, 0.80, n);
  let a = (d - P.hs[p]) * 9;
  if (a <= 0) return 0;
  if (a > 1) a = 1;
  const tw = 0.62 + 0.38 * Math.sin(TAU * (P.tlo[p] * P.T + P.tdd[p] * P.S) + P.tph[p]);
  return a * P.tbr[p] * tw;
}

function tex(P, t, x, y, p) {
  switch (t) {
    case T_MAZE: return P.mA[p];
    case T_SPOT: return P.mB[p];
    case T_BAND: return texBand(P, x, y);
    case T_LINE: return texLine(P, x, y);
    case T_NOISE: return texNoise(P, x, y, p);
    default: return 0;
  }
}

function tileVal(P, idx, x, y, p) {
  const m = P.tm[idx];
  const a = tex(P, P.tA[idx], x, y, p);
  if (m <= 0 || m >= 1) return a;
  const e = m * m * (3 - 2 * m);
  return a + (tex(P, P.tB[idx], x, y, p) - a) * e;
}

function bandVal(P, i, x, y, p) {
  const o = i * P.W + x;
  let v = tileVal(P, i * MC + P.colJ[o], x, y, p);
  const jo = P.colO[o];
  if (jo >= 0) {
    const w = P.colW[o];
    if (w > 0.001) v += (tileVal(P, i * MC + jo, x, y, p) - v) * w;
  }
  return v;
}

// ---- per-frame texture constants (all oscillators sit inside 0.1-0.6 Hz) ------
function ph(P, lo, hi) { return TAU * (lo * P.T + (hi - lo) * P.S); }

function frameConsts(P, time) {
  const c = P.fc, w = P.warpS;
  let m = 0.5 + 0.5 * Math.sin(ph(P, 0.10, 0.20));
  c.bw1 = 1 - m; c.bw2 = m; c.bnrm = 1 / Math.sqrt(c.bw1 * c.bw1 + c.bw2 * c.bw2);
  c.shPh = ph(P, 0.10, 0.22) + 1.3;
  c.shAmp = 3.0 * (0.25 + 0.75 * w);
  c.lnPh = ph(P, 0.10, 0.20) + 0.7;
  c.lnAmp = 1.3 * (0.20 + 0.80 * w);
  m = 0.5 + 0.5 * Math.sin(ph(P, 0.12, 0.25) + 2.1);
  c.lw1 = 1 - m; c.lw2 = m; c.lnrm = 1 / Math.sqrt(c.lw1 * c.lw1 + c.lw2 * c.lw2);
  m = 0.5 + 0.5 * Math.sin(ph(P, 0.10, 0.18) + 4.0);
  c.dw1 = 1 - m; c.dw2 = m; c.dnrm = 1 / Math.sqrt(c.dw1 * c.dw1 + c.dw2 * c.dw2);
  const breathe = 1 + 0.05 * Math.sin(ph(P, 0.12, 0.30) + 0.4);
  const intro = sstep(0, 3, time);                       // gentle fade-in from black
  c.gain = (0.72 + 0.28 * (P.glowS - 0.4) / 0.6) * breathe * intro;
}

// ---- lifecycle -----------------------------------------------------------------
function layerSetup(params) {
  const P = params;
  P.ready = false; P.W = 0; P.H = 0;
  P.T = 0; P.S = 0; P.z = 1;
  P.F = 0.3; P.s = 0.4; P.glowS = 0.8; P.mix = 0.4; P.warpS = 0.5; P.dt = 1 / 60;
  P.beat = 0; P.sinceBeat = 0; P.sinceShuf = 99; P.sinceSeed = 99; P.fadeDur = 3;
  P.rdAcc = 0; P.frame = 0;
}

function layerUpdate(dt, input, params) {
  const P = params;
  if (P.T === undefined) layerSetup(P);
  if (!P.ready) return;                      // buffers are sized on the first draw
  dt = dt > 0.1 ? 0.1 : dt > 0 ? dt : 0;     // survive stalls without jumping
  P.dt = dt;
  const kv = input && input.knobValues, bp = input && input.btnPressed, bh = input && input.btnHeld;

  // knobs: hard-clamped, then eased so a fast twist never causes a sudden change
  const fk = clamp(kv && kv[0] > 0 ? kv[0] : 0.3, HZ_MIN, HZ_MAX);
  const gk = clamp(kv && kv[1] > 0 ? kv[1] : 0.8, 0.4, 1);
  const mk = clamp(kv && kv[2] >= 0 ? kv[2] : 0.4, 0, 1);
  const wk = clamp(kv && kv[3] >= 0 ? kv[3] : 0.5, 0, 1);
  P.F += (fk - P.F) * (1 - Math.exp(-dt / 1.2));
  P.F = clamp(P.F, HZ_MIN, HZ_MAX);
  P.s = (P.F - HZ_MIN) / (HZ_MAX - HZ_MIN);
  P.glowS += (gk - P.glowS) * (1 - Math.exp(-dt / 0.5));
  P.warpS += (wk - P.warpS) * (1 - Math.exp(-dt / 0.8));
  P.mix = mk;

  // hold: ease the whole animation to a stop (and back), never an instant freeze
  const hold = bh && bh[2];
  P.z += ((hold ? 0 : 1) - P.z) * (1 - Math.exp(-dt / 0.6));
  const dz = dt * P.z;
  P.T += dz;
  P.S += dz * P.s;

  // cadence: one soft "beat" per cycle, at most HZ_MAX per second
  P.sinceBeat += dt;
  P.sinceShuf += dt;
  P.sinceSeed += dt;
  P.beat += P.F * dz;
  if (bp && bp[1] && P.sinceBeat >= MIN_BEAT) P.beat = 1;
  if (P.beat >= 1) {
    P.beat -= 1;
    if (P.beat >= 1) P.beat = 0;
    newBeat(P);
    P.sinceBeat = 0;
  }
  if (bp && bp[3] && P.sinceShuf >= MIN_BEAT) { shuffleAll(P); P.sinceShuf = 0; }

  // texture cross-fades
  P.fadeDur = Math.max(FADE_MIN, 0.7 / P.F);
  for (let i = 0; i < NB * MC; i++) {
    const m = P.tm[i];
    if (m < 1) {
      const n = m + dz / P.fadeDur;
      if (n >= 1) { P.tm[i] = 1; P.tA[i] = P.tB[i]; } else P.tm[i] = n;
    }
  }
}

function layerDraw(P, R, W, H, time, second) {
  if (P.T === undefined) layerSetup(P);
  ensure(P, W, H);
  const tm = time > 0 ? time : 0;
  const N = P.N;

  frameConsts(P, tm);
  computeLayout(P);
  updateDust(P);

  // the shared chemistry, already mapped to brightness (the second layer reads it shifted)
  if (second) { P.mA = R.mA2; P.mB = R.mB2; } else { P.mA = R.mA; P.mB = R.mB; }

  // compose panels -> target brightness
  const tgt = P.tgt, dust = P.dust, gain = P.gain, g = P.fc.gain;
  const rowB = P.rowB, rowO = P.rowO, rowW = P.rowW, seamY = P.seamY, seamX = P.seamX;
  for (let y = 0; y < H; y++) {
    const bi = rowB[y], bo = rowO[y], bw = rowW[y], sy = seamY[y], r0 = y * W;
    for (let x = 0; x < W; x++) {
      const p = r0 + x;
      let v = bandVal(P, bi, x, y, p);
      let sx = seamX[bi * W + x];
      if (bo >= 0) {
        v += (bandVal(P, bo, x, y, p) - v) * bw;
        sx += (seamX[bo * W + x] - sx) * bw;
      }
      v *= sy * sx;
      const d = dust[p];
      if (d > v) v = d;
      tgt[p] = v * gain[p] * g;
    }
  }

  // temporal safety net: two low-pass stages + a slew limit, so no pixel can ever strobe
  const disp = P.disp, lp1 = P.lp1, dtr = P.dt;
  const a = 1 - Math.exp(-dtr / TAU_LP), mx = SLEW * dtr;
  for (let p = 0; p < N; p++) {
    let t = tgt[p];
    t = t > 1 ? 1 : t < 0 ? 0 : t;
    const s1 = lp1[p] + (t - lp1[p]) * a;
    lp1[p] = s1;
    let d = (s1 - disp[p]) * a;
    if (d > mx) d = mx; else if (d < -mx) d = -mx;
    disp[p] += d;
  }

  // soft bloom (deep-blue halo around the cyan cores), then palette
  const tmp = P.tmp, bloom = 0.10 + 0.25 * (P.glowS - 0.4) / 0.6;
  for (let y = 0; y < H; y++) {
    const r = y * W;
    for (let x = 0; x < W; x++) {
      const xl = x === 0 ? 0 : x - 1, xr = x === W - 1 ? W - 1 : x + 1;
      tmp[r + x] = 0.25 * disp[r + xl] + 0.5 * disp[r + x] + 0.25 * disp[r + xr];
    }
  }
  const out = P.out;
  for (let y = 0; y < H; y++) {
    const r = y * W, ru = (y === 0 ? 0 : y - 1) * W, rd = (y === H - 1 ? H - 1 : y + 1) * W;
    for (let x = 0; x < W; x++) {
      const d = disp[r + x];
      const bl = 0.25 * tmp[ru + x] + 0.5 * tmp[r + x] + 0.25 * tmp[rd + x];
      let o = d + bloom * bl * (1 - d);
      o = o > 1 ? 1 : o;
      const k = (o * 255 + 0.5) | 0;
      out[r + x] = k;
    }
  }
}

function updateDust(P) {
  const idx = P.dustIdx, amp = P.dustAmp, out = P.dust, n = P.dustN;
  for (let q = 0; q < n; q++) {
    const p = idx[q];
    out[p] = amp[q] * (0.55 + 0.45 * Math.sin(TAU * (P.tlo[p] * P.T + P.tdd[p] * P.S) + P.tph[p]));
  }
}

// ---- shared reaction-diffusion -------------------------------------------------
// Both layers read the same two fields; their layouts (and so what shows where) differ.
function rdEnsure(R, W, H) {
  if (R.ready && R.W === W && R.H === H) return;
  const N = W * H;
  R.W = W; R.H = H; R.N = N;
  R.wm = new Float32Array(N);
  R.wsx = new Float32Array(3 * W); R.wcx = new Float32Array(3 * W);
  R.wsy = new Float32Array(3 * H); R.wcy = new Float32Array(3 * H);
  R.mA = new Float32Array(N); R.mB = new Float32Array(N);
  R.mA2 = new Float32Array(N); R.mB2 = new Float32Array(N);
  R.A = rdAlloc(N); R.B = rdAlloc(N);
  rdSeed(R.A, W, H, RD_SEEDS, true);
  rdSeed(R.B, W, H, RD_SEEDS, true);
  for (let s = 0; s < RD_BURN; s++) {
    rdStep(R.A, R.wm, W, H, 0.28, 0.14, 0.029, 0, 0.057, RD_DT);
    rdStep(R.B, R.wm, W, H, 0.34, 0.17, 0.030, 0, 0.062, RD_DT);
  }
  // chemistry v (0..0.4) -> brightness, as each layer's ensure() builds it
  R.chem = new Float32Array(258);
  for (let i = 0; i < 258; i++) {
    const t = clamp((i / 640 - CHEM_LO) / CHEM_SPAN, 0, 1);
    R.chem[i] = CHEM_PEAK * Math.pow(t, CHEM_GAMMA);
  }
  R.rdAcc = 0; R.frame = 0; R.sinceSeed = 99;
  R.ready = true;
}

// One layer's clocks drive it (both layers see the same knobs, so their clocks agree).
function rdUpdate(R, P, input) {
  if (!R.ready || !P.ready) return;
  const dt = P.dt, dz = dt * P.z, bp = input && input.btnPressed;
  R.sinceSeed += dt;
  if (bp && bp[0] && R.sinceSeed >= MIN_BEAT) {
    rdSeed(R.A, R.W, R.H, 10, false);
    rdSeed(R.B, R.W, R.H, 10, false);
    R.sinceSeed = 0;
  }
  const warpAmt = 0.35 + 0.65 * P.warpS;
  R.rdAcc += (RD_RATE0 + (RD_RATE1 - RD_RATE0) * P.s) * dz;
  let n = Math.floor(R.rdAcc);
  R.rdAcc -= n;
  if (n > RD_MAXSTEPS) n = RD_MAXSTEPS;
  if (n > 0) {
    R.T = P.T; R.S = P.S;
    computeWaves(R);
    for (let i = 0; i < n; i++) {
      rdStep(R.A, R.wm, R.W, R.H, 0.28, 0.14, 0.029, 0.0050 * warpAmt, 0.057, RD_DT);
      rdStep(R.B, R.wm, R.W, R.H, 0.34, 0.17, 0.030, 0.0040 * warpAmt, 0.062, RD_DT);
    }
  }
  // watchdog: if a field ever dies out, plant a few seeds so it regrows
  R.frame++;
  if (R.frame % 45 === 0) {
    let sa = 0, sb = 0, cnt = 0;
    for (let p = 0; p < R.N; p += 11) { sa += R.A.v[p]; sb += R.B.v[p]; cnt++; }
    if (!(sa / cnt > 0.02)) rdSeed(R.A, R.W, R.H, 12, sa !== sa);
    if (!(sb / cnt > 0.015)) rdSeed(R.B, R.W, R.H, 12, sb !== sb);
  }
}

// map reaction-diffusion chemistry to brightness, once for both layers
function rdBrightness(R) {
  const av = R.A.v, bv = R.B.v, ma = R.mA, mb = R.mB, chem = R.chem, N = R.N;
  for (let p = 0; p < N; p++) {
    let f = av[p] * 640; if (f > 256) f = 256;
    let i = f | 0, r = f - i;
    ma[p] = chem[i] + (chem[i + 1] - chem[i]) * r;
    f = bv[p] * 640; if (f > 256) f = 256;
    i = f | 0; r = f - i;
    mb[p] = chem[i] + (chem[i + 1] - chem[i]) * r;
  }
  // The original's second layer grew its own fields, so its mazes and spots never sat on the
  // first layer's. The fields wrap around, so reading them shifted by about half the square
  // gives the second layer an unrelated-looking stretch of the same chemistry.
  const W = R.W, H = R.H, ox = (W >> 1) + 19, oy = (H >> 1) + 41, ma2 = R.mA2, mb2 = R.mB2;
  for (let y = 0; y < H; y++) {
    const src = ((y + oy) % H) * W, dst = y * W, split = W - (ox % W);
    ma2.set(ma.subarray(src + (ox % W), src + W), dst); ma2.set(ma.subarray(src, src + (ox % W)), dst + split);
    mb2.set(mb.subarray(src + (ox % W), src + W), dst); mb2.set(mb.subarray(src, src + (ox % W)), dst + split);
  }
}

// ---- the two layers ------------------------------------------------------------
// The second layer's recolour ramp (luminance of its navy -> cyan palette -> RGB), added on top.
const RAMP2 = [
  3,3,3,5,5,5,8,8,8,10,10,10,12,12,12,14,15,14,17,17,16,19,19,18,21,22,21,23,24,23,
  25,27,25,27,29,26,29,31,28,30,34,30,32,36,32,34,38,35,36,41,37,37,43,39,39,45,41,41,48,43,
  42,50,46,44,52,48,46,55,51,47,57,53,49,60,56,50,62,59,52,64,62,53,67,65,54,69,68,56,71,71,
  57,73,74,58,74,76,59,75,78,60,76,81,62,77,83,63,78,85,64,78,88,65,79,90,66,79,92,67,79,95,
  68,78,97,69,78,100,69,77,102,70,76,104,71,75,107,72,74,109,72,73,111,75,73,114,79,74,116,82,74,118,
  86,75,121,89,75,123,93,76,125,98,76,128,102,77,130,107,77,133,112,77,135,117,78,137,122,78,140,128,78,142,
  133,79,144,139,79,147,146,79,149,151,79,150,154,79,148,156,79,146,158,79,143,161,79,140,163,79,137,165,79,133,
  168,79,129,170,78,125,173,78,120,175,78,115,177,78,110,180,77,105,182,77,99,184,76,92,187,76,86,189,76,79,
  191,79,75,194,85,74,196,92,74,198,100,73,201,107,73,203,115,72,206,124,71,208,132,70,210,141,70,213,151,69,
  215,161,68,217,171,67,220,181,66,222,192,65,224,203,64,227,215,63,229,227,62,223,231,61,215,234,60,206,236,58,
  197,238,57,191,239,57,186,238,57,182,238,57,177,237,58,172,237,58,168,237,58,163,236,58,159,236,58,154,235,58,
  149,235,58,145,234,59,140,234,59,136,234,59,132,233,59,127,233,59,123,232,59,119,232,59,114,232,60,110,231,60,
  106,231,60,101,230,60,97,230,60,93,229,60,89,229,60,85,229,61,81,228,61,77,228,61,73,227,61,69,227,61,
  65,226,61,61,226,62,61,226,66,62,225,70,62,225,75,62,224,79,62,224,83,62,223,87,62,223,91,62,223,95,
  62,222,99,63,222,103,63,221,107,63,221,110,63,221,114,63,220,118,63,220,122,63,219,126,63,219,130,63,218,133,
  64,218,137,64,218,141,64,217,144,64,217,148,64,216,151,64,216,155,64,215,159,64,215,162,64,215,166,65,214,169,
  65,214,172,65,213,176,65,213,179,65,213,183,65,212,186,65,212,189,65,211,192,65,211,196,65,210,199,65,210,202,
  66,210,205,66,209,208,66,206,209,66,202,208,66,198,208,66,194,207,66,190,207,66,186,207,66,183,206,66,179,206,
  66,175,205,67,171,205,67,168,205,67,164,204,67,160,204,67,157,203,67,153,203,67,149,202,67,146,202,67,142,202,
  67,139,201,67,135,201,67,132,200,67,128,200,68,125,199,68,122,199,68,118,199,68,115,198,68,111,198,68,108,197,
  68,105,197,68,102,197,68,98,196,68,95,196,68,92,195,68,89,195,68,86,194,68,83,194,68,79,194,68,76,193,
  69,73,193,69,70,192,70,69,192,73,69,191,76,69,191,79,69,191,82,69,190,85,69,190,88,69,189,91,69,189,
  94,69,188,97,69,188,100,69,188,103,69,187,105,69,187,108,69,186,111,69,186,114,69,186,117,69,185,119,69,185,
  122,69,184,125,69,184,127,70,183,130,70,183,132,70,183,135,70,182,138,70,182,140,70,181,143,70,181,145,70,180,
  147,70,180,150,70,180,152,70,179,155,70,179,157,70,178,159,70,178,162,70,178,164,70,177,166,70,177,169,70,176,
  142,67,180,58,75,191,48,189,202,36,212,88,122,223,23,234,169,8,
];

let RD = { ready: false }, LAYERS = [{}, {}], OUT2 = null;

function setup(params) {
  RD = { ready: false };
  LAYERS = [{}, {}];
  for (const P of LAYERS) layerSetup(P);
}

function update(dt, input, params) {
  for (const P of LAYERS) layerUpdate(dt, input, P);
  rdUpdate(RD, LAYERS[0], input);
}

function draw(display, params, time) {
  const W = display.width, H = display.height;
  rdEnsure(RD, W, H);
  rdBrightness(RD);
  layerDraw(LAYERS[0], RD, W, H, time, false);
  layerDraw(LAYERS[1], RD, W, H, time, true);
  const P0 = LAYERS[0];
  if (!OUT2) {
    // palette index -> the second layer's colour after its recolour, as one table
    OUT2 = new Uint8Array(768);
    for (let k = 0; k < 256; k++) {
      const l = Math.round(0.2126 * P0.lutR[k] + 0.7152 * P0.lutG[k] + 0.0722 * P0.lutB[k]) * 3;
      OUT2[k * 3] = RAMP2[l]; OUT2[k * 3 + 1] = RAMP2[l + 1]; OUT2[k * 3 + 2] = RAMP2[l + 2];
    }
  }
  const lr = P0.lutR, lg = P0.lutG, lb = P0.lutB, a = P0.out, b = LAYERS[1].out;
  for (let y = 0, p = 0; y < H; y++) {
    for (let x = 0; x < W; x++, p++) {
      const k = a[p], j = b[p] * 3;
      display.setPixel(x, y, lr[k] + OUT2[j], lg[k] + OUT2[j + 1], lb[k] + OUT2[j + 2]);
    }
  }
}
