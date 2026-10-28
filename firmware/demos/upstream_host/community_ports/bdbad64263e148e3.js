// ===== Patternflow pattern =====
// Title:    Fractured Grid Fluid Cells
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/bdbad64263e148e3
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the original is a Pattern Lab layer
// stack (Fractured Fluid Cells, with Cyber-Grid Gravity Well screened over it) flattened onto
// a fixed 64 x 128 canvas, so on a wider display it drew only its first 64 columns. Here both
// layers are drawn and composited in one pass at the display's size: the fluid keeps its
// pixel scale, so the square holds twice the cells and a full wave of the flow across it,
// and the gravity well, scaled to the height as before, is seen whole, a round funnel
// instead of a tall slice of one. Knob wiring, clocks, colours and the CRT scanlines are the
// original's; distances and angles are tabled once.

// @matrix 128x128
// @knobs Glitch=0..1, Speed=0.05..5.037, Freq=10..120, Quantize=2..10

let W = 0, H = 0, DIST = null, ANG = null, LOGD = null;

export function setup(params) {
  params.t1 = 0;     // the fluid layer's clock
  params.t2 = 0;     // the gravity well's
  params.k = [0.5, 2.54, 65, 6];
}

export function update(dt, input, params) {
  params.k = input.knobValues;
  params.t1 += dt * params.k[1];
  params.t2 += dt * params.k[1] * 0.5;
}

function tables(w, h) {
  W = w; H = h;
  DIST = new Float32Array(w * h); ANG = new Float32Array(w * h); LOGD = new Float32Array(w * h);
  for (let y = 0, i = 0; y < h; y++) {
    for (let x = 0; x < w; x++, i++) {
      const nx = (x - w / 2) / (h / 2), ny = (y - h / 2) / (h / 2);
      const d = Math.sqrt(nx * nx + ny * ny);
      DIST[i] = d;
      ANG[i] = Math.atan2(ny, nx) + Math.PI;
      LOGD[i] = d > 0 ? Math.log(d) : -Infinity;
    }
  }
}

// a layer's byte, as its Uint8ClampedArray kept it
function q(v) { return v <= 0 ? 0 : v >= 255 ? 255 : Math.round(v); }

export function draw(display, params) {
  const w = display.width, h = display.height;
  if (w !== W || h !== H) tables(w, h);
  const k = params.k;

  // Fractured Fluid Cells
  const t = params.t1 * 0.5;
  const cellSize = 4 + Math.floor(k[0] * 28);
  const jitterAmt = k[2] * 10;
  const colorShift = k[3];
  const gMid = Math.floor(100 + 155 * Math.abs(Math.cos(t)));
  const bLow = Math.floor(150 + 105 * Math.sin(t * 0.5));
  const nCells = Math.ceil(Math.max(w, h) / cellSize) + 1;
  const offX = new Float32Array(nCells), gHigh = new Float32Array(nCells);
  const offY = new Float32Array(nCells);
  for (let c = 0; c < nCells; c++) {
    offX[c] = Math.sin(c * 0.5 + t) * jitterAmt;
    offY[c] = Math.cos(c * 0.5 - t) * jitterAmt;
    gHigh[c] = Math.floor(128 + 127 * Math.sin(t + c));
  }

  // Cyber-Grid Gravity Well
  const t2 = params.t2;
  const radialCount = 4 + Math.floor(k[0] * 24);
  const ringSpacing = 0.05 + (1.0 - k[3]) * 0.2;
  const warpExp = 1.0 / (1.0 + k[2] * 2.0);
  const ringShift = t2 * 0.2;

  for (let y = 0, i = 0; y < h; y++) {
    const cellY = Math.floor(y / cellSize);
    const yEdge = y % cellSize === 0;
    const scan = (y % 2 === 0) ? 1.0 : 0.7;
    const cy = Math.cos((y + offY[cellY]) * 0.08 - t);
    for (let x = 0; x < w; x++, i++) {
      const cellX = Math.floor(x / cellSize);
      const val = Math.sin((x + offX[cellX]) * 0.05 + t) + cy;
      const ring = Math.sin(val * 4.0 + (cellX + cellY) * colorShift);
      let r, g, b;
      if (ring > 0.5) { r = 255; g = gHigh[cellX]; b = 50; }
      else if (ring > -0.2) { r = 0; g = gMid; b = 200; }
      else { r = 100; g = 0; b = bLow; }
      if (yEdge || x % cellSize === 0) {
        r = Math.min(255, r + 100); g = Math.min(255, g + 100); b = Math.min(255, b + 100);
      }
      r = q(r); g = q(g); b = q(b);

      const dist = DIST[i];
      const warped = Math.exp(LOGD[i] * warpExp);
      const isRadial = Math.abs(Math.sin(ANG[i] * radialCount)) > 0.95;
      const isRing = Math.abs((warped - ringShift) % ringSpacing) < 0.015;
      const glow = Math.exp(-dist * 4.0);
      let sr = 0, sg = 0, sb = 0;
      if (isRadial || isRing) { sr = 20; sg = 100 + warped * 155; sb = 255; }
      sr = q(Math.min(255, sr + glow * 255) * scan);
      sg = q(Math.min(255, sg + glow * 150) * scan);
      sb = q(Math.min(255, sb + glow * 50) * scan);

      display.setPixel(x, y,
        255 - (255 - r) * (255 - sr) / 255,
        255 - (255 - g) * (255 - sg) / 255,
        255 - (255 - b) * (255 - sb) / 255);
    }
  }
}

// ── Made with Patternflow Community · https://patternflow.work/community ──
// Shared under CC-BY-SA-4.0. Attribution is part of this licence —
// please keep this notice and the author credit above when you reuse,
// remix, or redistribute this pattern. Do not delete it.
