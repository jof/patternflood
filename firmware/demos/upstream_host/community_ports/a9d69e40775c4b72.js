// ===== Patternflow pattern =====
// Title:    Chromatic Plasma Core
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/a9d69e40775c4b72
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same spiral beams through the
// same ramp, with the core 1.8 times as large (Range now reaches 108 px, so the default disc
// fills the square as the original filled its 64-wide frame). The glow's falloff scales with
// the core; the twist and the radial ripple keep their pixel pitch, so the bigger core carries
// 1.8 times as many rings of the same fine coloured dashes instead of fatter ones. Distance and
// angle are tabled once, and pow(w, 30) is a few multiplies.

// @ramp hsvLong recolor 0:#000000 0.173:#00fcff 0.091:#8df900 0:#00fcff
// @matrix 128x128
// @knobs Twist=0..5, Spin=0.1..5, Detail=1..10, Range=10..60
const S = 1.8;            // core scale against the original's 64-wide frame
let W = 0, H = 0, D = null, A = null;

export function setup(params) {
  params.k = [0, 0, 0, 0];
}

export function update(dt, input, params) {
  params.k = input.knobValues;
}

function tables(w, h) {
  W = w; H = h;
  D = new Float32Array(w * h);
  A = new Float32Array(w * h);
  const cx = w / 2, cy = h / 2;
  for (let y = 0, i = 0; y < h; y++) {
    for (let x = 0; x < w; x++, i++) {
      const dx = x - cx, dy = y - cy;
      D[i] = Math.sqrt(dx * dx + dy * dy);
      A[i] = Math.atan2(dy, dx);
    }
  }
}

export function draw(display, params, time) {
  const w = display.width, h = display.height;
  if (w !== W || h !== H) tables(w, h);
  const twist = params.k[0] * 0.1;         // per pixel, as the original: the same line pitch
  const t = time * params.k[1];
  const detail = params.k[2];
  const range = params.k[3] * S;
  const fall = 0.05 / S;
  for (let y = 0, i = 0; y < h; y++) {
    for (let x = 0; x < w; x++, i++) {
      const d = D[i];
      if (d >= range) continue;           // the frame is already black
      const a = A[i] + d * twist;
      const wave = Math.sin(a * detail + d * 0.5 - t);
      if (wave <= 0.6) continue;          // 0.6^30 < 1e-6: nothing a byte can show
      const w2 = wave * wave, w4 = w2 * w2, w8 = w4 * w4, w16 = w8 * w8;
      const bri = w16 * w8 * w4 * w2 * Math.exp(-d * fall) * 255;
      display.setPixel(x, y, Math.floor(bri * 0.8), Math.floor(bri * 0.4), Math.floor(bri));
    }
  }
}

// ── Made with Patternflow Community · https://patternflow.work/community ──
// Shared under CC-BY-SA-4.0. Attribution is part of this licence —
// please keep this notice and the author credit above when you reuse,
// remix, or redistribute this pattern. Do not delete it.
