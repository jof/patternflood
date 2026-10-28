// ===== Patternflow pattern =====
// Title:    Collatz Kelp
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/523e8c0fd1424e9c
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): a bigger reef of the same kelp.
// The trie now holds the Collatz paths of 1..3200 (6932 nodes; the original stopped at
// 1600), Seeds starts at 800 instead of 300 and runs to 3200, so the default frond carries
// about twice the stalks and the full knob four times the original's most. The fit keeps
// the aspect ratio (the original let x stretch to 1.6 times y to fill its tall frame), so
// curls stay round, and the strokes keep their pixel width, so the denser reef reads as
// finer strands rather than a thicker blur.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"
#include "src/core_mem.h"

namespace CollatzKelp {

const char* NAME = "Collatz Kelp";
const char* const KNOB_LABELS[4] = {"Odd", "Grow", "Even", "Seeds"};
constexpr bool ABSOLUTE_READY = true;

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;

constexpr int CK_MAXN = 3200;
constexpr int CK_CAP = 7168;   // the trie of n = 1..3200 has 6932 nodes
constexpr int CK_HASH = 16384; // value -> node map, only used while building
constexpr int CK_PATH = 1024;
constexpr int CK_DEPS = 256;   // deepest node is 216
constexpr float CK_T_WRAP = 1000.0f * PI;

// Knob state (Pattern Lab current values).
static float ckOddTurn = 0.28f;
static float ckGrow = 2.0f;
static float ckEvenTurn = 0.15f;
static float ckSeeds = 800.0f;

static float ckT = 0.0f;
static float ckReveal = 0.0f;
static float ckRevRate = 0.0f;  // 0 = not measured yet (JS: params.revRate || 20)

static bool ckFitInit = false;
static float ckFitRot = 0.0f, ckFitSx = 1.0f, ckFitSy = 1.0f, ckFitCx = 0.0f, ckFitCy = 0.0f;

// Trie, built once (PSRAM-first).
static uint16_t* ckPar = nullptr;
static uint8_t* ckDep = nullptr;
static uint8_t* ckOdd = nullptr;
static uint16_t* ckUpTo = nullptr;
static uint16_t* ckCnt = nullptr;
static uint8_t* ckTop = nullptr;
static uint8_t* ckPi = nullptr;   // palette index per node (cached per seed count)
static float* ckLc = nullptr;     // log subtree size / log root size (cached per seed count)
static float* ckS = nullptr;      // sin / cos of each node's heading
static float* ckC = nullptr;
static float* ckX = nullptr;
static float* ckY = nullptr;
static float* ckAcc = nullptr;    // RGB accumulator, FRAME_W * FRAME_H * 3
static int ckNodes = 0;
static int ckCachedN = -1;
static int ckCachedMaxDep = 1;
static float ckLogMax = 1.0f;

static float ckPal[64 * 3];
static float ckStep[CK_DEPS];     // 1.3 / (1 + 0.012 d)
static float ckSway[CK_DEPS];
static float ckPulse[CK_DEPS];
static float ckTurnS[CK_DEPS * 2];
static float ckTurnC[CK_DEPS * 2];

static const float CK_STOPS[24] = {
  0.0f, 10, 120, 130,
  0.3f, 20, 200, 130,
  0.55f, 110, 235, 120,
  0.75f, 255, 110, 80,
  0.88f, 255, 80, 130,
  1.0f, 255, 205, 70,
};

// Accurate sin/cos for per-frame / per-depth use (not per pixel). The turtle walk
// chains up to 181 headings, so the sin LUT's 0.35-degree steps would bend long
// stalks; this is a range-reduced polynomial, no libm call.
static inline void ckSinCos(float x, float& s, float& c) {
  int q = PFMath::ifloor(x * 0.63661977f + 0.5f);
  float fq = (float)q;
  float r = ((x - fq * 1.5703125f) - fq * 4.837512969970703125e-4f) - fq * 7.54978995489188216e-8f;
  float r2 = r * r;
  float sn = r * (1.0f + r2 * (-1.0f / 6.0f + r2 * (1.0f / 120.0f + r2 * (-1.0f / 5040.0f + r2 * (1.0f / 362880.0f)))));
  float cs = 1.0f + r2 * (-0.5f + r2 * (1.0f / 24.0f + r2 * (-1.0f / 720.0f + r2 * (1.0f / 40320.0f))));
  switch (q & 3) {
    case 0: s = sn; c = cs; break;
    case 1: s = cs; c = -sn; break;
    case 2: s = -sn; c = -cs; break;
    default: s = -cs; c = sn; break;
  }
}

static inline float ckSin(float x) {
  float s, c;
  ckSinCos(x, s, c);
  return s;
}

static inline uint32_t ckSlot(int32_t v) {
  return ((uint32_t)v * 2654435761u) >> 18;  // 14 bits -> 0..16383
}

static void ckBuild() {
  // The accumulator is scratch space while building: hash keys, hash values, path.
  int32_t* keys = (int32_t*)ckAcc;
  int32_t* vals = keys + CK_HASH;
  int32_t* path = vals + CK_HASH;
  memset(keys, 0, sizeof(int32_t) * CK_HASH);

  auto find = [&](int32_t v) -> int {
    uint32_t h = ckSlot(v);
    while (keys[h] != 0) {
      if (keys[h] == v) return vals[h];
      h = (h + 1) & (CK_HASH - 1);
    }
    return -1;
  };
  auto put = [&](int32_t v, int node) {
    uint32_t h = ckSlot(v);
    while (keys[h] != 0 && keys[h] != v) h = (h + 1) & (CK_HASH - 1);
    keys[h] = v;
    vals[h] = node;
  };

  put(1, 0);
  ckPar[0] = 0; ckDep[0] = 0; ckOdd[0] = 1;
  ckNodes = 1;
  ckUpTo[0] = 1; ckUpTo[1] = 1;
  bool full = false;
  for (int n = 2; n <= CK_MAXN; n++) {
    if (!full) {
      int32_t v = n;
      int len = 0;
      int p = find(v);
      while (p < 0 && len < CK_PATH) {
        path[len++] = v;
        v = (v & 1) ? 3 * v + 1 : v / 2;
        p = find(v);
      }
      if (p < 0 || ckNodes + len > CK_CAP) {
        full = true;
      } else {
        for (int i = len - 1; i >= 0; i--) {
          int32_t c = path[i];
          int k = ckNodes++;
          ckPar[k] = (uint16_t)p;
          int dk = ckDep[p] + 1;
          ckDep[k] = (uint8_t)(dk < CK_DEPS - 1 ? dk : CK_DEPS - 1);
          ckOdd[k] = (uint8_t)(c & 1);
          put(c, k);
          p = k;
        }
      }
    }
    ckUpTo[n] = (uint16_t)ckNodes;
  }
  memset(ckAcc, 0, sizeof(float) * FRAME_W * FRAME_H * 3);
}

static void ckBuildPalette() {
  for (int i = 0; i < 64; i++) {
    float f = i / 63.0f;
    int s = 0;
    while (s < 24 - 8 && f > CK_STOPS[s + 4]) s += 4;
    float a = CK_STOPS[s], b = CK_STOPS[s + 4];
    float u = PFMath::clamp01((f - a) / (b - a));
    for (int c = 0; c < 3; c++) ckPal[i * 3 + c] = CK_STOPS[s + 1 + c] + (CK_STOPS[s + 5 + c] - CK_STOPS[s + 1 + c]) * u;
  }
  for (int d = 0; d < CK_DEPS; d++) ckStep[d] = 1.3f / (1.0f + 0.012f * d);
}

// Subtree sizes, deepest leaves, log weights and palette slots depend only on the seed count.
static void ckCacheTree(int N) {
  int maxDep = 1;
  for (int i = 0; i < N; i++) {
    ckCnt[i] = 1;
    ckTop[i] = ckDep[i];
    if (ckDep[i] > maxDep) maxDep = ckDep[i];
  }
  for (int i = N - 1; i > 0; i--) {
    int p = ckPar[i];
    ckCnt[p] = (uint16_t)(ckCnt[p] + ckCnt[i]);
    if (ckTop[i] > ckTop[p]) ckTop[p] = ckTop[i];
  }
  ckLogMax = logf(1.0f + ckCnt[0]);
  for (int i = 1; i < N; i++) {
    ckLc[i] = logf(1.0f + ckCnt[i]) / ckLogMax;
    int pi = (int)(((float)ckDep[i] / (float)ckTop[i]) * 63.99f);
    ckPi[i] = (uint8_t)(pi < 63 ? pi : 63);
  }
  ckCachedMaxDep = maxDep;
  ckCachedN = N;
}

// Soft round dab of radius r (px) and weight wt into the RGB accumulator.
static inline void ckDab(float x, float y, float r, float wt, float pr, float pg, float pb) {
  float* acc = ckAcc;
  if (r < 0.75f) {
    int x0 = PFMath::ifloor(x - 0.5f), y0 = PFMath::ifloor(y - 0.5f);
    float fx = x - 0.5f - x0, fy = y - 0.5f - y0;
    for (int j = 0; j < 2; j++) {
      int yy = y0 + j;
      if (yy < 0 || yy >= FRAME_H) continue;
      float wy = j ? fy : 1.0f - fy;
      for (int i = 0; i < 2; i++) {
        int xx = x0 + i;
        if (xx < 0 || xx >= FRAME_W) continue;
        float q = wt * wy * (i ? fx : 1.0f - fx);
        float* o = acc + (yy * FRAME_W + xx) * 3;
        o[0] += pr * q; o[1] += pg * q; o[2] += pb * q;
      }
    }
    return;
  }
  int x0 = PFMath::ifloor(x - r), x1 = PFMath::ifloor(x + r);
  int y0 = PFMath::ifloor(y - r), y1 = PFMath::ifloor(y + r);
  if (x0 < 0) x0 = 0;
  if (x1 > FRAME_W - 1) x1 = FRAME_W - 1;
  if (y0 < 0) y0 = 0;
  if (y1 > FRAME_H - 1) y1 = FRAME_H - 1;
  float norm = wt / (0.5f + 0.9f * r);
  float rr = r + 0.5f;
  float inv = 1.0f / rr;
  float lim = rr * rr;
  for (int yy = y0; yy <= y1; yy++) {
    float dy = yy + 0.5f - y;
    for (int xx = x0; xx <= x1; xx++) {
      float dx = xx + 0.5f - x;
      float d2 = dx * dx + dy * dy;
      if (d2 >= lim) continue;
      float q = norm * (1.0f - sqrtf(d2) * inv);
      float* o = acc + (yy * FRAME_W + xx) * 3;
      o[0] += pr * q; o[1] += pg * q; o[2] += pb * q;
    }
  }
}

void setup() {
  if (!ckAcc) ckAcc = PFMem::allocFloats(FRAME_W * FRAME_H * 3);
  if (!ckPar) {
    size_t bytes = (size_t)CK_CAP * (2 + 1 + 1 + 2 + 1 + 1 + 4 * 5) + (CK_MAXN + 1) * 2 + 16;
    uint8_t* blk = (uint8_t*)PFMem::alloc(bytes);
    if (blk) {
      ckS = (float*)blk;
      ckC = ckS + CK_CAP;
      ckX = ckC + CK_CAP;
      ckY = ckX + CK_CAP;
      ckLc = ckY + CK_CAP;
      ckPar = (uint16_t*)(ckLc + CK_CAP);
      ckCnt = ckPar + CK_CAP;
      ckUpTo = ckCnt + CK_CAP;
      ckDep = (uint8_t*)(ckUpTo + CK_MAXN + 1);
      ckOdd = ckDep + CK_CAP;
      ckTop = ckOdd + CK_CAP;
      ckPi = ckTop + CK_CAP;
    }
  }
  if (ckNodes == 0 && ckAcc && ckPar) {
    ckBuildPalette();
    ckBuild();
  }
  ckOddTurn = 0.28f;
  ckGrow = 2.0f;
  ckEvenTurn = 0.15f;
  ckSeeds = 800.0f;
  ckT = 0.0f;
  ckReveal = 0.0f;
  ckRevRate = 0.0f;
  ckFitInit = false;
  ckCachedN = -1;
}

void update(float dt, const InputFrame& input) {
  if (!ckAcc || !ckPar) return;
  PFParams::apply(input, 0, &ckOddTurn, 0.28f, 0.8f, 0.011f);
  PFParams::apply(input, 1, &ckGrow, 0.3f, 5.0f, 0.098f);
  PFParams::apply(input, 2, &ckEvenTurn, 0.15f, 0.45f, 0.006f);
  PFParams::apply(input, 3, &ckSeeds, 300.0f, (float)CK_MAXN, (CK_MAXN - 300.0f) / 48.0f);
  for (int i = 0; i < 4; i++) {
    if (input.btnPressed[i] && !input.paramAbsoluteActive[i] && !input.knobAudioActive[i]) ckReveal = 0.0f;
  }
  ckT += dt * (0.35f + 0.5f * ckGrow);
  if (ckT > CK_T_WRAP) ckT -= CK_T_WRAP;
  if (ckReveal < 400.0f) ckReveal += dt * (0.4f + ckGrow) * (ckRevRate > 0.0f ? ckRevRate : 20.0f);
}

void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);
  if (!ckAcc || !ckPar || ckNodes == 0) { PFCanvas::present(); return; }
  float* acc = ckAcc;
  memset(acc, 0, sizeof(float) * FRAME_W * FRAME_H * 3);

  int seeds = PFMath::ifloor(ckSeeds);
  if (seeds < 2) seeds = 2;
  if (seeds > CK_MAXN) seeds = CK_MAXN;
  const int N = ckUpTo[seeds];
  if (N != ckCachedN) ckCacheTree(N);
  const int maxDep = ckCachedMaxDep;
  const float oddT = ckOddTurn, evenT = ckEvenTurn, t = ckT;
  ckRevRate = maxDep / 9.0f;  // full reef in ~4 s at Grow 2

  // Current: a wave travelling up the stalks; the turn at each depth for odd / even steps.
  const int dLim = maxDep < CK_DEPS - 1 ? maxDep : CK_DEPS - 1;
  for (int d = 0; d <= dLim; d++) {
    float sw = 0.02f * ckSin(t * 0.7f - d * 0.08f) + 0.007f * ckSin(t * 1.3f - d * 0.19f + 1.7f);
    ckSway[d] = sw;
    ckSinCos(evenT + sw, ckTurnS[d * 2], ckTurnC[d * 2]);
    ckSinCos(-oddT + sw, ckTurnS[d * 2 + 1], ckTurnC[d * 2 + 1]);
    float sp = ckSin(d * 0.16f - t * 2.4f);
    if (sp < 0.0f) sp = 0.0f;
    ckPulse[d] = 0.6f + 0.9f * sp * sp;
  }

  // Turtle walk (unrotated): each heading is the parent's turned by the step's angle.
  ckS[0] = 0.0f; ckC[0] = 1.0f; ckX[0] = 0.0f; ckY[0] = 0.0f;
  float sx = 0.0f, sy = 0.0f;
  for (int i = 1; i < N; i++) {
    const int p = ckPar[i], d = ckDep[i];
    const int ti = d * 2 + ckOdd[i];
    const float ts = ckTurnS[ti], tc = ckTurnC[ti];
    const float ps = ckS[p], pc = ckC[p];
    const float s = ps * tc + pc * ts;
    const float c = pc * tc - ps * ts;
    ckS[i] = s; ckC[i] = c;
    const float st = ckStep[d];
    ckX[i] = ckX[p] + st * s;
    ckY[i] = ckY[p] + st * c;
    sx += ckX[i]; sy += ckY[i];
  }

  // Rotate so the frond's mass leans 30 degrees right, toward the square's far corner (the
  // original stood it straight up in its tall frame), easing toward it.
  const float target = PFMath::fastAtan2(sx, sy) - (float)(PI / 6.0);
  if (!ckFitInit) ckFitRot = target;
  float dr = target - ckFitRot;
  dr -= (float)PFMath::ifloor(dr / TWO_PI + 0.5f) * TWO_PI;
  ckFitRot += dr * 0.08f;
  float sr, cr;
  ckSinCos(ckFitRot, sr, cr);
  float minX = 1e9f, maxX = -1e9f, minY = 1e9f, maxY = -1e9f;
  for (int i = 0; i < N; i++) {
    const float x = ckX[i] * cr - ckY[i] * sr;
    const float y = ckX[i] * sr + ckY[i] * cr;
    ckX[i] = x; ckY[i] = y;
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
  }
  const float m = 3.0f;
  // Fit the whole frond, one scale for both axes.
  const float spanX = maxX - minX, spanY = maxY - minY;
  float fsx = (FRAME_W - 2 * m) / (spanX > 1e-3f ? spanX : 1e-3f);
  float fsy = (FRAME_H - 2 * m) / (spanY > 1e-3f ? spanY : 1e-3f);
  if (fsx > fsy) fsx = fsy;
  fsy = fsx;
  const float cx = (minX + maxX) * 0.5f, cy = (minY + maxY) * 0.5f;
  if (!ckFitInit) {
    ckFitSx = fsx; ckFitSy = fsy; ckFitCx = cx; ckFitCy = cy; ckFitInit = true;
  } else {
    ckFitSx += (fsx - ckFitSx) * 0.08f;
    ckFitSy += (fsy - ckFitSy) * 0.08f;
    ckFitCx += (cx - ckFitCx) * 0.08f;
    ckFitCy += (cy - ckFitCy) * 0.08f;
  }
  const float SX = ckFitSx, SY = ckFitSy, S = sqrtf(SX * SY);
  const float ox = FRAME_W * 0.5f - ckFitCx * SX, oy = FRAME_H * 0.5f + ckFitCy * SY;

  // Draw every revealed segment; the growth front is a bright bud.
  const float rev = ckReveal;
  const float thick = S * 0.9f > 0.6f ? S * 0.9f : 0.6f;
  for (int i = 1; i < N; i++) {
    const int d = ckDep[i];
    if (d > rev + 1.0f) continue;
    const int p = ckPar[i];
    const float g = rev + 1.0f - d;
    const float grow = g < 1.0f ? g : 1.0f;
    const float lc = ckLc[i];
    const float* pal = ckPal + ckPi[i] * 3;
    const float pulse = ckPulse[d];
    const float wt = (0.45f + 1.1f * lc) * pulse;
    float r = 0.4f + thick * lc * lc * 1.6f;
    if (r > 1.9f) r = 1.9f;
    const float x0 = ox + ckX[p] * SX, y0 = oy - ckY[p] * SY;
    const float x1 = x0 + (ckX[i] - ckX[p]) * SX * grow, y1 = y0 - (ckY[i] - ckY[p]) * SY * grow;
    const float len = fabsf(x1 - x0) + fabsf(y1 - y0);
    const int steps = 1 + PFMath::ifloor(len * 1.4f);
    const float lw = len + 0.35f;
    const float sw = wt / steps * (lw < 1.4f ? lw : 1.4f);
    const float invSteps = 1.0f / steps;
    for (int k = 1; k <= steps; k++) {
      const float u = k * invSteps;
      ckDab(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, r, sw, pal[0], pal[1], pal[2]);
    }
    if (ckCnt[i] == 1) ckDab(x1, y1, 0.5f, d >= rev ? 1.3f : 0.55f * pulse, 255.0f, 225.0f, 140.0f);
  }

  for (int y = 0; y < FRAME_H; y++) {
    const float* row = acc + y * FRAME_W * 3;
    for (int x = 0; x < FRAME_W; x++) {
      float r = row[x * 3], g = row[x * 3 + 1], b = row[x * 3 + 2];
      float mx = r > g ? r : g;
      if (b > mx) mx = b;
      if (mx > 1.0f) {
        // Soft knee: lift faint stalks, compress the trunk, bleed only the hottest toward white.
        float k = 1.5f / (mx + 128.0f);
        if (mx * k > 1.0f) k = 1.0f / mx;
        float e = 0.0f;
        if (mx > 400.0f) { e = (mx - 400.0f) * (1.0f / 1500.0f); if (e > 0.6f) e = 0.6f; }
        r *= k; g *= k; b *= k;
        r = (r + (1.0f - r) * e) * 255.0f;
        g = (g + (1.0f - g) * e) * 255.0f;
        b = (b + (1.0f - b) * e) * 255.0f;
      }
      int ri = (int)r, gi = (int)g, bi = (int)b;
      if (ri > 255) ri = 255;
      if (gi > 255) gi = 255;
      if (bi > 255) bi = 255;
      if (ri < 0) ri = 0;
      if (gi < 0) gi = 0;
      if (bi < 0) bi = 0;
      PFCanvas::setPixel(x, y, (uint8_t)ri, (uint8_t)gi, (uint8_t)bi);
    }
  }

  PFCanvas::present();
}

}  // namespace CollatzKelp