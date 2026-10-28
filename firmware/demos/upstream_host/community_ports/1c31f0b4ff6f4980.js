// ===== Patternflow pattern =====
// Title:    Twisted Perspective Tunnel
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/1c31f0b4ff6f4980
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the original is a Pattern Lab layer
// stack flattened onto a fixed 64 x 128 canvas, so its round tunnel was only ever seen as a
// tall slice. Here the four layers (elastic rings and wobbling rings, screened; the twisted
// tunnel, laid over them; the stepped square frames, added) are composited in one pass at the
// display's size, so the whole tunnel shows: the rings close into circles and the square
// frames turn as complete squares out to the panel's edge. Every layer keeps its scale
// against the height (the wobbling rings' colour fade too, which ran across the original's
// 64-px width), its own clock and its knob wiring. Distances and angles are tabled once.

// @matrix 128x128
// @knobs Count=2..12, Speed=1..5, Strobe=0..4.9, StepSize=0.1..1

let W = 0, H = 0, D = null, A = null, C = null;
const ringCos = new Float32Array(64), ringSin = new Float32Array(64);
const ringFlash = new Float32Array(64);

export function setup(params) {
  params.T = 0;
  params.k = [7, 3, 2.45, 0.55];
}

export function update(dt, input, params) {
  params.k = input.knobValues;
  params.T += dt * params.k[1];     // layers 2 and 5 run at this; 3 at 0.2 x, 4 at 0.4 x
}

function tables(w, h) {
  W = w; H = h;
  D = new Float32Array(w * h); A = new Float32Array(w * h); C = new Float32Array(w * h);
  for (let y = 0, i = 0; y < h; y++) {
    for (let x = 0; x < w; x++, i++) {
      const dx = x - w / 2, dy = y - h / 2;
      D[i] = Math.sqrt(dx * dx + dy * dy);
      A[i] = Math.atan2(dy, dx);
      C[i] = Math.max(Math.abs(dx), Math.abs(dy));
    }
  }
}

// a layer's byte, as its Uint8ClampedArray kept it
function q(v) { return v <= 0 ? 0 : v >= 255 ? 255 : Math.round(v); }

export function draw(display, params) {
  const w = display.width, h = display.height;
  if (w !== W || h !== H) tables(w, h);
  const k = params.k;
  const T = params.T, t3 = T * 0.2, t4 = T * 0.4;

  // layer 2: elastic rings
  const rings = k[0], elastic = k[2], r2 = 1 / (h * 0.6);
  // layer 3: wobbling rings; their colour fade spans half the height (the original's width)
  const thick = k[3] * 5 / 10, pw = 1 / (h / 2), k2 = k[2];
  // layer 4: tunnel
  const fov = k[2], twist = k[0];
  // layer 5: stepped square frames, per ring
  const count = Math.min(63, Math.floor(k[0]));
  const step = k[3] * Math.PI, strobe = k[2], half = h * 0.5;
  for (let ri = 1; ri < count; ri++) {
    const ang = Math.floor((T + ri) / step) * step;
    ringCos[ri] = Math.cos(ang); ringSin[ri] = Math.sin(ang);
    ringFlash[ri] = Math.sin(T * strobe + ri) > 0 ? 255 : 50;
  }

  for (let y = 0, i = 0; y < h; y++) {
    const dy = y - h / 2;
    for (let x = 0; x < w; x++, i++) {
      const d = D[i];
      let r = 0, g = 0, b = 0;

      // layer 2 (screen over black: its own colour)
      const normD = d * r2;
      const phase = normD * rings;
      const motion = Math.sin(T - phase * elastic);
      const ringSignal = Math.sin(phase * 3.14 + motion);
      if (ringSignal > 0.8) {
        const bri = (ringSignal - 0.8) * 5.0;
        r = q(255 * (1 - normD) * bri);
        g = q(150 * Math.abs(motion) * bri);
        b = q(255 * normD * bri);
      }

      // layer 3 (screen)
      const rc = (d + Math.sin(t3 + d * 0.1) * 10) / 10;
      if (rc - Math.floor(rc) < thick) {
        const perc = 1.0 - d * pw;
        const cycle = (t3 + perc * k2) % 2;
        let sr, sg, sb;
        if (cycle < 1) { sr = 255 * perc; sg = 255 * (1 - perc); sb = 255 * Math.sin(t3); }
        else { sr = 125 * perc; sg = 255 * perc; sb = 255 * (1 - perc); }
        sr = q(sr); sg = q(sg); sb = q(sb);
        r = 255 - (255 - r) * (255 - sr) / 255;
        g = 255 - (255 - g) * (255 - sg) / 255;
        b = 255 - (255 - b) * (255 - sb) / 255;
      }

      // layer 4 (normal: replaces what's under it)
      const z = 1.0 / (d / h * fov + 0.1);
      const ang = A[i] + z * twist + t4;
      if (Math.sin(z - t4 * 2) * Math.cos(ang * 2) > 0.5) {
        const depthCol = q(Math.min(255, z * 20));
        if (z > 5) { r = 255; g = depthCol; b = 100; }
        else { r = depthCol; g = 200; b = 255; }
      }

      // layer 5 (add)
      const ri = Math.floor(C[i] / half * count);
      if (ri >= 1 && ri < count) {
        const dx = x - w / 2, cs = ringCos[ri], sn = ringSin[ri];
        const rx = dx * cs - dy * sn, ry = dx * sn + dy * cs;
        const border = Math.max(Math.abs(rx), Math.abs(ry));
        if (Math.abs(border - h * 0.4 * (ri / count)) < 1.5) {
          const flash = ringFlash[ri];
          if (ri > count / 2) r += flash;
          g += q(flash / 2);
          if (ri <= count / 2) b += flash;
        }
      }

      display.setPixel(x, y, r > 255 ? 255 : r, g > 255 ? 255 : g, b > 255 ? 255 : b);
    }
  }
}

// ── Made with Patternflow Community · https://patternflow.work/community ──
// Shared under CC-BY-SA-4.0. Attribution is part of this licence —
// please keep this notice and the author credit above when you reuse,
// remix, or redistribute this pattern. Do not delete it.
