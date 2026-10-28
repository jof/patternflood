// ===== Patternflow pattern =====
// Title:    Biolum Helix
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/49e2592863db4ace
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the original is a Pattern Lab layer
// stack whose wrapper fixes the canvas at 64 x 128 (and its scale is 0.4 x the width, which a
// wider canvas would blow up past the top and bottom). Here the two layers are kept as two
// particle buffers on the full square: the first recoloured through the same warm ramp (so the
// water is the same dark brown, now edge to edge), the second's raw pink / cyan added on top, each
// with its own random rungs as before. The helix is drawn at 33 px per unit instead of 25.6, so
// it stands 119 px tall instead of 92 and swings through the whole square when the Rot knobs
// turn it, and it is built from 1800 particles instead of 1200 so the strands stay as solid and
// the rungs as speckled at the larger size. The rotation is one matrix per frame instead of
// three per particle.

// @matrix 128x128
// @knobs Rot_X=0..6.28, Rot_Y=0..6.28, Rot_Z=0..6.28, Twist=0..12

const N_PARTICLES = 1800;      // the original: 1200 at 25.6 px per unit
const SCALE = 33;              // px per unit: the helix is 3.6 units tall

// The first layer's ramp: luminance -> RGB (black water comes out dark brown).
const LUT = [
  26,9,6,28,10,7,30,11,8,32,12,9,34,13,10,36,14,11,38,15,12,40,16,13,42,17,15,44,18,16,
  46,19,17,48,20,19,50,21,20,53,22,21,55,23,23,57,24,24,59,25,26,61,26,27,63,27,29,65,28,31,
  68,29,32,70,30,34,72,31,36,74,32,37,76,34,39,78,35,41,81,36,43,83,37,45,85,38,47,87,39,49,
  89,40,51,92,41,53,94,43,55,96,44,57,98,45,59,100,46,61,103,47,63,105,48,65,107,50,68,109,51,70,
  111,52,72,114,53,74,116,55,77,118,56,79,120,57,82,122,58,84,124,60,87,126,61,89,129,62,92,131,63,94,
  133,65,97,135,66,100,137,67,102,139,69,105,141,70,108,143,72,110,145,73,113,147,74,116,149,76,119,151,77,122,
  153,79,125,155,80,128,157,82,131,159,83,134,161,85,137,163,86,140,165,88,143,167,89,146,169,91,149,171,92,152,
  172,94,155,174,95,159,177,96,160,180,97,159,184,98,158,187,98,158,190,99,157,193,100,156,196,101,155,200,101,154,
  203,102,153,206,103,151,209,104,150,212,105,149,215,106,147,218,106,146,221,107,144,224,109,142,227,110,141,230,111,139,
  232,112,137,235,113,135,238,114,133,240,116,131,243,117,129,245,118,126,248,120,124,250,121,122,252,123,119,255,125,117,
  255,128,115,255,131,115,255,135,114,255,138,114,255,141,113,255,144,113,255,147,113,255,150,113,255,153,113,255,156,113,
  255,159,114,255,162,114,255,165,114,255,167,115,255,170,116,255,173,116,255,176,117,255,178,118,255,181,118,255,184,119,
  255,186,120,255,189,121,255,191,122,255,194,123,255,196,124,255,199,125,255,202,126,255,204,127,255,207,127,255,209,128,
  255,212,129,255,214,130,255,217,130,255,219,130,255,222,130,255,224,130,255,227,129,255,229,128,255,232,126,255,234,123,
  255,237,118,255,240,110,255,243,98,255,246,75,255,250,0,255,247,79,255,242,117,255,237,132,255,233,140,255,229,144,
  255,225,145,255,221,146,255,217,146,255,214,146,255,210,145,255,206,144,255,202,143,255,198,142,255,195,141,255,191,140,
  255,187,140,255,183,139,255,179,138,255,175,138,255,170,138,255,166,138,255,162,138,255,157,139,255,153,139,255,148,141,
  255,143,142,255,138,144,255,133,146,255,127,149,253,123,152,249,121,157,244,120,161,239,118,165,234,117,168,229,116,172,
  223,115,175,218,114,178,212,113,181,206,112,183,200,112,185,194,111,187,188,110,189,182,110,190,176,109,191,170,109,192,
  171,111,193,173,114,194,174,116,195,175,118,196,177,120,197,178,122,198,179,125,199,180,127,200,182,129,201,183,131,202,
  184,133,203,186,136,204,187,138,205,188,140,206,190,142,207,191,144,208,192,147,209,193,149,210,195,151,211,196,153,212,
  197,155,213,199,157,214,200,160,215,201,162,216,202,164,217,204,166,218,205,168,219,206,171,220,208,173,221,209,175,222,
  210,177,223,212,179,224,213,182,225,214,184,226,215,186,227,217,188,228,218,190,228,219,193,229,221,195,230,222,197,231,
  223,199,232,224,201,233,226,204,234,227,206,235,228,208,236,229,210,237,231,212,238,232,215,239,233,217,240,235,219,241,
  236,221,241,237,224,242,238,226,243,240,228,244,241,230,245,242,233,246,244,235,247,245,237,248,246,239,249,247,241,250,
  249,244,251,250,246,251,251,248,252,252,250,253,254,253,254,255,255,255,
];

function makeParticles() {
  const ps = [];
  for (let i = 0; i < N_PARTICLES; i++) {
    ps.push({ v: (i / N_PARTICLES) * 2 - 1, type: i % 3, rand: Math.random() });
  }
  return ps;
}

function setup(params) {
  params.t = 0;
  params.k = [3.14, 3.14, 3.14, 6];
  params.layers = [makeParticles(), makeParticles()];   // each layer rolled its own rungs
  params.bufA = null;
  params.bufB = null;
}

function update(dt, input, params) {
  params.k = input.knobValues;
  params.t += dt * 0.6;
}

function drawLayer(buf, ps, w, h, M, t, twist) {
  const cx = w / 2, cy = h / 2;
  const [m00, m01, m02, m10, m11, m12, m20, m21, m22] = M;
  for (let i = 0; i < ps.length; i++) {
    const p = ps[i];
    const angle = p.v * twist + t;
    const ca = Math.cos(angle), sa = Math.sin(angle);
    let px, pz;
    if (p.type === 0) { px = 0.6 * ca; pz = 0.6 * sa; }
    else if (p.type === 1) { px = -0.6 * ca; pz = -0.6 * sa; }
    else { const l = p.rand * 2 - 1; px = 0.6 * ca * l; pz = 0.6 * sa * l; }
    const py = p.v * 1.8;

    // Fresnel rim from the backbone normal (px, 0, pz) normalised, rotated, against the view.
    const nl = Math.sqrt(px * px + pz * pz) || 1;
    let fr = 1.0 - Math.abs(-(m20 * px + m22 * pz) / nl);
    fr = fr * fr * fr;

    const rx = m00 * px + m01 * py + m02 * pz;
    const ry = m10 * px + m11 * py + m12 * pz;
    const rz = m20 * px + m21 * py + m22 * pz;
    const sx = Math.floor(cx + rx * SCALE), sy = Math.floor(cy + ry * SCALE);
    if (sx < 0 || sx >= w || sy < 0 || sy >= h) continue;

    let r, g, b;
    if (p.type < 2) { r = 255; g = 100 + fr * 155; b = 180 + fr * 75; }
    else { r = 50 + fr * 100; g = 200 + fr * 55; b = 255; }
    let o = (sy * w + sx) * 3;
    buf[o] = r; buf[o + 1] = g; buf[o + 2] = b;
    if (rz > 0.2 && fr > 0.7 && sx + 1 < w) {           // depth hint: a faint pixel beside it
      o += 3;
      buf[o] = r * 0.4; buf[o + 1] = g * 0.4; buf[o + 2] = b * 0.4;
    }
  }
}

function draw(display, params, time) {
  const w = display.width, h = display.height, n = w * h * 3;
  if (!params.bufA || params.bufA.length !== n) {
    params.bufA = new Uint8ClampedArray(n);
    params.bufB = new Uint8ClampedArray(n);
  }
  const A = params.bufA, B = params.bufB;
  A.fill(0); B.fill(0);
  const [ax, ay, az, twist] = params.k;

  // rotatePoint(): about X, then Y, then Z, as one matrix Rz * Ry * Rx.
  const cX = Math.cos(ax), sX = Math.sin(ax), cY = Math.cos(ay), sY = Math.sin(ay);
  const cZ = Math.cos(az), sZ = Math.sin(az);
  const r00 = cY, r01 = sY * sX, r02 = sY * cX;            // Ry * Rx
  const r10 = 0, r11 = cX, r12 = -sX;
  const r20 = -sY, r21 = cY * sX, r22 = cY * cX;
  const M = [cZ * r00 - sZ * r10, cZ * r01 - sZ * r11, cZ * r02 - sZ * r12,
             sZ * r00 + cZ * r10, sZ * r01 + cZ * r11, sZ * r02 + cZ * r12,
             r20, r21, r22];

  drawLayer(A, params.layers[0], w, h, M, params.t, twist);
  drawLayer(B, params.layers[1], w, h, M, params.t, twist);

  // Layer 1 through its ramp (normal), layer 2 added raw.
  for (let y = 0, o = 0; y < h; y++) {
    for (let x = 0; x < w; x++, o += 3) {
      const l = Math.round(0.2126 * A[o] + 0.7152 * A[o + 1] + 0.0722 * A[o + 2]) * 3;
      display.setPixel(x, y, LUT[l] + B[o], LUT[l + 1] + B[o + 1], LUT[l + 2] + B[o + 2]);
    }
  }
}
