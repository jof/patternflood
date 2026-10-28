// ===== Patternflow pattern =====
// Title:    Spectral Mosaic Rings
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/e56ee5868c084141
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the original is a Pattern Lab layer
// stack whose wrapper fixes the canvas at 64 x 128, so here the two layers (the same ring mosaic,
// once recoloured through a fading-in ramp, once multiplied through a spectrum ramp) are folded
// into one luminance -> colour table and drawn straight onto the 128 x 128 square. Cells keep
// their size in pixels (CellSize 4..12, 8 by default), so the mosaic is 16 x 16 cells instead of
// 8 x 16 and the colour field, the diagonal on/off bands and their drift play out over twice as
// many rings; the grid is centred, so sizes that do not divide 128 leave even margins. Each
// cell's colour is worked out once per cell and each ring's falloff once per cell size, instead
// of per pixel.

// @matrix 128x128
// @knobs CellSize=4..12, Speed=0.1..5, RingThick=0.305..1.001, HueShift=0..1

// Luminance -> RGB of the original's two layers composited (normal with the first ramp's alpha,
// then multiply by the second ramp); everything below LUT_FROM is black.
const LUT_FROM = 81;
const LUT = [
  1,1,1,2,2,2,3,2,2,4,4,3,6,5,5,7,6,6,8,8,7,9,10,9,11,12,10,12,14,12,
  13,16,14,15,18,16,17,21,19,18,24,21,20,27,24,21,30,27,23,33,30,25,37,33,27,41,37,29,44,41,
  31,49,45,33,52,49,35,56,53,38,61,58,40,66,63,42,71,68,45,76,73,48,81,79,50,86,84,53,92,90,
  55,97,97,58,103,103,61,109,110,64,116,117,68,122,124,71,128,132,74,136,140,77,142,148,80,149,155,84,156,164,
  88,164,173,91,169,180,95,175,188,99,181,195,103,187,202,107,192,210,111,196,217,115,203,224,119,208,232,123,214,240,
  128,219,248,132,224,255,133,221,255,134,218,255,135,216,255,136,213,255,137,211,255,138,209,255,139,206,255,140,204,255,
  141,202,255,142,200,255,143,197,255,144,195,255,145,193,255,146,191,255,147,189,255,148,187,255,149,186,255,150,184,255,
  151,182,255,152,180,255,153,179,255,154,177,255,155,175,255,156,174,255,157,172,255,158,171,255,159,170,255,160,168,255,
  161,167,255,162,166,255,163,164,255,165,164,255,168,165,255,171,166,255,174,167,255,177,168,255,180,169,255,183,170,255,
  185,171,255,188,172,255,191,173,255,194,174,255,196,175,255,199,176,255,201,177,255,204,178,255,206,179,255,209,180,255,
  211,181,255,213,182,255,216,183,255,218,184,255,220,185,255,222,186,255,224,187,255,226,188,255,228,189,255,230,190,255,
  232,191,255,234,192,255,236,193,255,238,194,255,239,195,255,241,196,255,242,197,255,244,198,255,246,199,255,247,200,255,
  248,201,255,250,202,255,251,203,255,252,204,255,254,205,255,255,206,255,255,207,254,255,208,253,255,209,252,255,210,251,
  255,211,250,255,212,249,255,213,248,255,214,247,255,215,247,255,216,246,255,217,245,255,218,245,255,219,244,255,220,244,
  255,221,243,255,222,243,255,223,242,255,224,242,255,225,242,255,226,241,255,227,241,255,228,241,255,229,241,255,230,241,
  255,231,241,255,232,241,255,233,241,255,234,241,255,235,241,255,236,242,255,237,242,255,238,242,255,239,243,255,240,243,
  255,241,244,255,242,244,255,243,245,255,244,245,255,245,246,255,246,247,255,247,247,255,248,248,255,249,249,255,250,250,
  255,251,251,255,252,252,255,253,253,255,254,254,255,255,255,
];

function setup(params) {
  params.timeAcc = 0;
  params.k = [8, 2.55, 0.653, 0.5];
  params.edge = new Float32Array(144);    // ring falloff per in-cell position (0 = off the ring)
  params.edgeKey = "";
  params.cr = new Uint8Array(1024);       // per-cell colour (32 x 32 cells at the smallest size)
  params.cg = new Uint8Array(1024);
  params.cb = new Uint8Array(1024);
  params.on = new Uint8Array(1024);
}

function update(dt, input, params) {
  params.k = input.knobValues;
  params.timeAcc += dt * params.k[1];
}

function draw(display, params, time) {
  const w = display.width, h = display.height;
  const cellSize = Math.floor(params.k[0]);
  const thick = params.k[2];
  const t = params.timeAcc;
  const globalHue = params.k[3] * 6.28;

  // The ring's profile inside one cell: the same for every cell, so worked out once per size.
  const innerRad = cellSize * 0.2, outerRad = cellSize * (0.2 + thick);
  const key = cellSize + ":" + thick;
  const E = params.edge;
  if (params.edgeKey !== key) {
    params.edgeKey = key;
    for (let ly = 0; ly < cellSize; ly++) {
      const dy = ly - cellSize / 2;
      for (let lx = 0; lx < cellSize; lx++) {
        const dx = lx - cellSize / 2;
        const dist = Math.sqrt(dx * dx + dy * dy);
        E[ly * cellSize + lx] = dist >= innerRad && dist <= outerRad
          ? 1.0 - Math.abs((innerRad + outerRad) / 2 - dist) / (thick * cellSize) : 0;
      }
    }
  }

  // Centre the grid: a size that does not divide the square leaves even part-cells at the edges.
  const nx = Math.ceil(w / cellSize), ny = Math.ceil(h / cellSize);
  const offX = Math.floor((nx * cellSize - w) / 2), offY = Math.floor((ny * cellSize - h) / 2);

  // Each cell's single colour, from the fluid field sampled at the cell (as the original does).
  const cr = params.cr, cg = params.cg, cb = params.cb, on = params.on;
  for (let cy = 0; cy < ny; cy++) {
    for (let cx = 0; cx < nx; cx++) {
      const c = cy * nx + cx;
      const intensity = Math.sin(cx * 0.5 + cy * 0.3 + t) * 0.5 + 0.5;
      on[c] = intensity > 0.3 ? 1 : 0;
      if (!on[c]) continue;
      const sig = Math.sin(cx * 0.2 + t) * Math.cos(cy * 0.2 - t * 0.5) + Math.sin(cx * 0.1 - t);
      const hue = sig * 3.0 + cx * 0.1 + cy * 0.1 + globalHue;
      cr[c] = Math.floor(127 + 127 * Math.sin(hue));
      cg[c] = Math.floor(127 + 127 * Math.sin(hue + 2.1));
      cb[c] = Math.floor(127 + 127 * Math.sin(hue + 4.2));
    }
  }

  for (let y = 0; y < h; y++) {
    const yy = y + offY, cy = Math.floor(yy / cellSize), ly = yy - cy * cellSize;
    for (let x = 0; x < w; x++) {
      const xx = x + offX, cx = Math.floor(xx / cellSize);
      const c = cy * nx + cx;
      if (!on[c]) continue;
      const e = E[ly * cellSize + xx - cx * cellSize];
      if (e <= 0) continue;
      const lum = Math.round(0.2126 * Math.floor(cr[c] * e) + 0.7152 * Math.floor(cg[c] * e) +
                             0.0722 * Math.floor(cb[c] * e));
      if (lum < LUT_FROM) continue;
      const i = (lum - LUT_FROM) * 3;
      display.setPixel(x, y, LUT[i], LUT[i + 1], LUT[i + 2]);
    }
  }
}
