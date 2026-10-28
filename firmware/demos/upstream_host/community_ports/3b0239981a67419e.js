// ===== Patternflow pattern =====
// Title:    Understory
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/3b0239981a67419e
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the original grows one swaying
// stalk of leaves (three layers of it, back to front) down the middle of its 64 x 128 frame;
// here five stalks grow across the square, each the original's leaf at its pixel size, set
// back to front with the original's three greens and two blended between them, each with its
// own sway, drift and light shafts, so the panel reads as a thicket rather than one column.
// The leaf maths, knobs and reset button are the original's; per-row and per-column terms
// are hoisted out of the pixel loop, each stalk is only evaluated where it can light a pixel,
// and the contrast curve is a table.

// @knobs Folds=3..12, Speed=0.1..10, Zoom=2..17, Contrast=0.1..1
// @matrix 128x128

// Five stalks, back to front: x offset from the centre (fraction of the width), fade, and
// colour ramp (low rgb, high rgb), the original's three with two blends between them.
const STALKS = [
  { x: -0.19, fade: 0.50, rg: [10, 60, 15, 40, 160, 30] },
  { x:  0.20, fade: 0.62, rg: [8, 70, 18, 30, 180, 40] },
  { x: -0.38, fade: 0.75, rg: [5, 80, 20, 20, 200, 50] },
  { x:  0.38, fade: 0.88, rg: [10, 90, 15, 50, 210, 45] },
  { x:  0.01, fade: 1.00, rg: [15, 100, 10, 80, 220, 40] },
];

let W = 0, H = 0, R = null, G = null, B = null, colShaft = null;
const LUT_N = 1024, LUT_MAX = 1.5;
const powLut = new Float32Array(LUT_N + 2);
let lutExp = -1;

export function setup(params) {
  params.t = 0;
  params.folds    = 6;
  params.speed    = 3.0;
  params.zoom     = 8;
  params.contrast = 0.5;
}

export function update(dt, input, params) {
  params.folds    = input.knobValues[0];
  params.speed    = input.knobValues[1];
  params.zoom     = input.knobValues[2];
  params.contrast = input.knobValues[3];

  params.t += dt * params.speed;

  if (input.btnPressed[0]) params.t = 0; // tap knob 1 to reset time
}

export function draw(display, params) {
  const w = display.width, h = display.height;
  if (w !== W || h !== H) {
    W = w; H = h;
    R = new Float32Array(w * h); G = new Float32Array(w * h); B = new Float32Array(w * h);
    colShaft = new Float32Array(w);
  }
  R.fill(0); G.fill(0); B.fill(0);
  const { folds, zoom, contrast, t } = params;
  const p = 1.0 / Math.max(0.1, contrast);
  if (p !== lutExp) {
    lutExp = p;
    for (let i = 0; i <= LUT_N + 1; i++) powLut[i] = Math.pow(i * LUT_MAX / LUT_N, p);
  }
  // A stalk can't light a pixel (< half a level) where leafMask * xMask is below this.
  const mThr = Math.pow(0.5 / (420 * Math.pow(1.32, p)), 1 / (p + 1));
  const iz = 1 / zoom;
  const period = 14.0 / folds, halfP = period * 0.5;
  const mid2 = folds * 2.0, fx8 = folds * 0.8;

  for (let l = 0; l < STALKS.length; l++) {
    const st = STALKS[l], gc = st.rg, fade = st.fade;
    const lt = t + l * 1.7;
    const s = lt * 0.1;
    const xoff = st.x * w + Math.sin(lt * 0.23 + l * 2.1) * 8;
    const yoff = (l - 2) * (h / 3) + Math.cos(lt * 0.17 + l) * 4;
    // light shafts: a column factor times a row factor
    const sp = lt * 0.4 + l * 1.3;
    for (let x = 0; x < w; x++) {
      const v = Math.sin((x - w / 2 + xoff) * iz * 0.5 + sp);
      colShaft[x] = v > 0 ? v : 0;
    }
    const sinA = s, sinB = s * 1.3, sinC = s * 2.1;
    for (let y = 0; y < h; y++) {
      const ly = y - h / 2 + yoff;
      const fy = ly * iz;
      let yOff = (fy * folds * 0.5) % period;
      if (yOff < 0) yOff += period;
      const q = yOff / halfP - 1.0;
      const leafMask = 1.0 - q * q;
      if (leafMask <= mThr) continue;
      const cxMax = Math.sqrt(Math.log(leafMask / mThr) / 0.4);
      const sway = Math.sin(fy * 0.4 + lt * 0.7) * 0.8 + Math.sin(fy * 0.15 + lt * 0.3) * 1.5;
      // x = cx * zoom + sway * zoom - xoff + w / 2
      const x0 = Math.max(0, Math.ceil((sway - cxMax) * zoom - xoff + w / 2));
      const x1 = Math.min(w - 1, Math.floor((sway + cxMax) * zoom - xoff + w / 2));
      if (x1 < x0) continue;
      const Y = fy * 2.0;
      const c1 = Math.cos(Y * 0.9 + s * 0.7);
      const c2 = Math.cos(Y * 2.3 + s * 0.4) * 0.5;
      const c3 = Math.cos(Y * 1.7 + s * 1.1) * 0.25;
      const rs = Math.sin(fy * 0.3 + lt * 0.2);
      const rowShaft = rs > 0 ? rs : 0;
      const lmf = leafMask * fade;
      const xbase = (-w / 2 + xoff) * iz - sway;
      let i = y * w + x0;
      for (let x = x0; x <= x1; x++, i++) {
        const cx = x * iz + xbase;
        const cx2 = cx * cx;
        const xMask = Math.exp(-cx2 * 0.4);
        const midrib = Math.exp(-cx2 * mid2) * 1.2;
        const X = cx * fx8;
        const n = Math.sin(X * 1.3 + sinA) * c1 + Math.sin(X * 2.1 + sinB) * c2
                + Math.sin(X * 0.4 + sinC) * c3;
        const vein = n * 0.5 + 0.5;
        const m = leafMask * xMask;
        let u = (vein * 0.7 + midrib * 0.3) * m;
        if (u <= 0) continue;
        u *= LUT_N / LUT_MAX;
        let k = u | 0;
        let intensity;
        if (k >= LUT_N) intensity = Math.pow(u * (LUT_MAX / LUT_N), p);
        else intensity = powLut[k] + (powLut[k + 1] - powLut[k]) * (u - k);
        const sh = colShaft[x] * rowShaft;
        const shimmer = sh * sh * 0.5;
        const alpha = intensity * xMask * lmf;
        R[i] += (gc[0] + (gc[3] - gc[0]) * intensity + shimmer * 120) * alpha;
        G[i] += (gc[1] + (gc[4] - gc[1]) * intensity + shimmer * 200) * alpha;
        B[i] += (gc[2] + (gc[5] - gc[2]) * intensity + shimmer *  60) * alpha;
      }
    }
  }

  for (let y = 0, i = 0; y < h; y++) {
    for (let x = 0; x < w; x++, i++) {
      const r = R[i] + 5, g = G[i] + 20, b = B[i] + 8;
      display.setPixel(x, y, r < 255 ? r : 255, g < 255 ? g : 255, b < 255 ? b : 255);
    }
  }
}

// ── Made with Patternflow Community · https://patternflow.work/community ──
// Shared under CC-BY-SA-4.0. Attribution is part of this licence —
// please keep this notice and the author credit above when you reuse,
// remix, or redistribute this pattern. Do not delete it.
