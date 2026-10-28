// ===== Patternflow pattern =====
// Title:    Velvet Steps
// Author:   @mikdnom
// Source:   https://community.patternflow.work/community/p/f90f84ad04b840d6
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same cat on the same glass,
// drawn sharper and seen whole. The cat is now rendered into its sprite at two samples per
// design unit (VS_SS) instead of one, so the fur, the frosted edge and the jelly pads keep
// their detail at the size the panel shows them (the original magnified one sample to 1.8
// px by default, and the automatic 128 x 128 version to 3.7, which washed it out). The view
// keeps the original's scale, so the default frame shows what it showed top to bottom
// (front and back paws) and the glass beside the cat that the 64-wide frame cut off.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"
#include "src/core_noise.h"
#include "src/core_mem.h"

namespace VelvetSteps {

const char* NAME = "Velvet Steps";
const char* const KNOB_LABELS[4] = {"Walk", "Direction", "Zoom", "Frost"};
constexpr bool ABSOLUTE_READY = true;

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;

// ---------------------------------------------------------------------------
// Sprite ("cat texture") geometry, in the pattern's own design units.
// The cat is rendered once per frame into a sprite, then resampled
// (rotated / zoomed) onto the frame. Only the columns [VS_CX0, VS_CX1) and rows
// [VS_CY0, VS_CY1) can ever hold cat pixels, so the sprite buffer is cropped to
// those columns; everything outside is plain background.
// ---------------------------------------------------------------------------
// Patternflood: the sprite holds VS_SS samples per design unit. Design coordinates (the
// original's sprite pixels) stay as they were; sprite-pixel arrays are VS_SS times larger.
constexpr int   VS_SS = 2;
constexpr float VS_INV_SS = 1.0f / VS_SS;
constexpr int   VS_DES_W = 128;                      // the sprite in design units
constexpr int   VS_DES_H = 160;
constexpr int   VS_SPR_W = VS_DES_W * VS_SS;         // ... and in sprite pixels
constexpr int   VS_SPR_H = VS_DES_H * VS_SS;
constexpr int   VS_CX0 = 24 * VS_SS;
constexpr int   VS_CX1 = 104 * VS_SS;
constexpr int   VS_CW  = VS_CX1 - VS_CX0;
constexpr int   VS_CY0 = 8 * VS_SS;
constexpr int   VS_CY1 = 156 * VS_SS;
constexpr float VS_ORG_X = VS_DES_W * 0.5f;          // body origin, design units
constexpr float VS_ORG_Y = VS_DES_H * 0.5f;
constexpr float VS_U0 = (VS_SPR_W - 1) * 0.5f;       // sprite sampling origin, sprite px
constexpr float VS_V0 = (VS_SPR_H - 1) * 0.5f;
constexpr float VS_BASE = 1.0f;                      // the original's scale: its 64 x 128 view, widened to the square

constexpr float VS_BG_R = 235.0f;
constexpr float VS_BG_G = 236.0f;
constexpr float VS_BG_B = 233.0f;
constexpr float VS_BG_SUM = 704.0f;

constexpr float VS_STEP[4] = {0.021f, 0.021f, 0.021f, 0.021f};
constexpr float VS_WALK_PERIOD = 50.0f;   // common period of every walk-driven phase

// Lookup-table geometry
constexpr int   VS_GN = 256;              // exp(-s), s in [0, VS_GSMAX]
constexpr float VS_GSMAX = 8.0f;
constexpr float VS_GSCALE = VS_GN / VS_GSMAX;
constexpr int   VS_P25N = 160;            // x^2.5, x in [0, 2.5]
constexpr float VS_P25MAX = 2.5f;
constexpr float VS_P25SCALE = VS_P25N / VS_P25MAX;
constexpr int   VS_P04N = 256;            // x^0.4, x in [0, 12]
constexpr float VS_P04MAX = 12.0f;
constexpr float VS_P04SCALE = VS_P04N / VS_P04MAX;
constexpr int   VS_VN = 128;              // sqrt(1 - t^2), t in [0, 1]

constexpr int   VS_NSEG = 17;             // 2 ears + 7 tail + 8 leg segments

// Paw colours (JS: tint 0.72)
constexpr float VS_JR = 83.0f + 144.0f * 0.72f;
constexpr float VS_JG = 74.0f + 69.0f * 0.72f;
constexpr float VS_JB = 79.0f + 83.0f * 0.72f;

constexpr float VS_SIDE[4]  = {-1.0f, 1.0f, -1.0f, 1.0f};
constexpr float VS_PHASE[4] = {0.0f, 0.5f, 0.75f, 0.25f};

constexpr float VS_TOE_TX[4] = {-5.0f, -1.9f, 1.9f, 5.0f};
constexpr float VS_TOE_TY[4] = {-4.7f, -7.0f, -7.0f, -4.7f};
constexpr float VS_CPX[5] = {-1.55f, 1.55f, -2.05f, 0.0f, 2.05f};
constexpr float VS_CPY[5] = {1.25f, 1.25f, 3.8f, 3.8f, 3.8f};
constexpr float VS_CIX[5] = {1.0f / 2.55f, 1.0f / 2.55f, 1.0f / 2.05f, 1.0f / 2.05f, 1.0f / 2.05f};
constexpr float VS_CIY[5] = {1.0f / 2.55f, 1.0f / 2.55f, 1.0f / 1.95f, 1.0f / 1.95f, 1.0f / 1.95f};

struct VsSeg  { float ax, ay, dx, dy, inv, r0, dr, x0, x1, y0, y1; };
struct VsFoot { float x, y, lift, scale, contact; };

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
static float walkK = 0.0f, dirK = 1.0f, zoomK = 1.0f, frostK = 1.0f;   // raw knobs
static float kWalk = 0.30f, kZoom = 0.42f, kFrost = 0.25f;              // smoothed
static float angle = 0.0f;
static float catX = 0.0f, catY = 0.0f;
static float walkT = 0.0f;
static float pressPulse = 0.0f;

static float* buf = nullptr;              // cropped RGB float sprite (PSRAM)

static float gaussLUT[VS_GN + 1];
static float pow25LUT[VS_P25N + 1];
static float pow04LUT[VS_P04N + 1];
static float volLUT[VS_VN + 1];
static float colS28[VS_CW], colC28[VS_CW], colS35[VS_CW], colC35[VS_CW];
static float rowSBelly[VS_SPR_H], rowSChest[VS_SPR_H], rowSChin[VS_SPR_H];
static float rowSMuz[VS_SPR_H], rowSMouth[VS_SPR_H];
static int16_t dirtyLo[VS_SPR_H], dirtyHi[VS_SPR_H];
static int16_t inkLo[VS_SPR_H], inkHi[VS_SPR_H];
static float pawCos[4], pawSin[4], toeCos[4], toeSin[4];
static VsSeg segs[VS_NSEG];
static VsFoot feet[4];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
static inline float vsSmooth(float v) {
  v = PFMath::clamp01(v);
  return v * v * (3.0f - 2.0f * v);
}

static inline float lutInterp(const float* tab, int n, float scale, float x) {
  float f = x * scale;
  if (f >= (float)n) return tab[n];
  int i = (int)f;
  float fr = f - (float)i;
  return tab[i] + (tab[i + 1] - tab[i]) * fr;
}

static inline float vsGauss(float s) {       // exp(-s), s >= 0
  if (s >= VS_GSMAX) return 0.0f;
  return lutInterp(gaussLUT, VS_GN, VS_GSCALE, s);
}

static inline float vsExpDecay(float x) {    // exp(-x) for small x >= 0
  return PFMath::fastPow(2.7182818f, -x);
}

static inline float sprGrain(int x, int y) {
  return PFNoise::cellHash(x, y, 1) - 0.5f;
}

static inline uint8_t vsByte(float v) {
  if (v <= 0.0f) return 0;
  if (v >= 255.0f) return 255;
  return (uint8_t)v;
}

static inline int vsCol(float X) {
  return PFMath::ifloor((X + VS_ORG_X) * VS_SS - 0.5f);
}

static inline float desX(int x) { return ((float)x + 0.5f) * VS_INV_SS - VS_ORG_X; }
static inline float desY(int y) { return ((float)y + 0.5f) * VS_INV_SS - VS_ORG_Y; }

static inline void markDirty(int y, int xa, int xb) {
  if (xa < dirtyLo[y]) dirtyLo[y] = (int16_t)xa;
  if (xb > dirtyHi[y]) dirtyHi[y] = (int16_t)xb;
}

static inline void markInk(int x, int y) {
  if (x < inkLo[y]) inkLo[y] = (int16_t)x;
  if (x > inkHi[y]) inkHi[y] = (int16_t)x;
}

static void setSeg(VsSeg& s, float ax, float ay, float bx, float by,
                   float r0, float r1, float pad) {
  s.ax = ax;
  s.ay = ay;
  s.dx = bx - ax;
  s.dy = by - ay;
  float l2 = s.dx * s.dx + s.dy * s.dy;
  s.inv = (l2 > 1e-6f) ? 1.0f / l2 : 0.0f;
  s.r0 = r0;
  s.dr = r1 - r0;
  float rm = (r0 > r1 ? r0 : r1) + pad;
  s.x0 = (ax < bx ? ax : bx) - rm;
  s.x1 = (ax > bx ? ax : bx) + rm;
  s.y0 = (ay < by ? ay : by) - rm;
  s.y1 = (ay > by ? ay : by) + rm;
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
void setup() {
  PFMath::buildSinLUT();
  if (!buf) buf = PFMem::allocFloats(VS_CW * VS_SPR_H * 3);

  // exp(-s) table by repeated multiplication
  {
    const float r = 0.96923323f;   // exp(-1/32)
    float v = 1.0f;
    for (int i = 0; i <= VS_GN; ++i) {
      gaussLUT[i] = v;
      v *= r;
    }
  }
  for (int i = 0; i <= VS_P25N; ++i) {
    float x = (float)i / VS_P25SCALE;
    pow25LUT[i] = PFMath::fastPow(x, 2.5f);
  }
  for (int i = 0; i <= VS_P04N; ++i) {
    float x = (float)i / VS_P04SCALE;
    pow04LUT[i] = PFMath::fastPow(x, 0.4f);
  }
  for (int i = 0; i <= VS_VN; ++i) {
    float t = (float)i / (float)VS_VN;
    float v = 1.0f - t * t;
    volLUT[i] = v > 0.0f ? sqrtf(v) : 0.0f;
  }
  for (int ci = 0; ci < VS_CW; ++ci) {
    float X = desX(VS_CX0 + ci);
    colS28[ci] = PFMath::fastSin(X * 2.8f);
    colC28[ci] = PFMath::fastCos(X * 2.8f);
    colS35[ci] = PFMath::fastSin(X * 0.35f);
    colC35[ci] = PFMath::fastCos(X * 0.35f);
  }
  for (int y = 0; y < VS_SPR_H; ++y) {
    float Y = desY(y);
    float t;
    t = (Y - 2.0f) * (1.0f / 36.0f);   rowSBelly[y] = t * t;
    t = (Y + 29.0f) * (1.0f / 14.0f);  rowSChest[y] = t * t;
    t = (Y + 45.0f) * (1.0f / 6.0f);   rowSChin[y]  = t * t;
    t = (Y + 50.0f) * (1.0f / 2.8f);   rowSMuz[y]   = t * t;
    t = (Y + 50.6f) * (1.0f / 1.5f);   rowSMouth[y] = t * t;
  }
  for (int j = 0; j < 4; ++j) {
    float a = VS_SIDE[j] * (j < 2 ? 0.13f : 0.26f);
    pawCos[j] = PFMath::fastCos(a);
    pawSin[j] = PFMath::fastSin(a);
    float rot = ((float)j - 1.5f) * 0.19f;
    toeCos[j] = PFMath::fastCos(rot);
    toeSin[j] = PFMath::fastSin(rot);
  }

  // state
  walkK = 0.0f; dirK = 1.0f; zoomK = 1.0f; frostK = 1.0f;
  kWalk = 0.30f; kZoom = 0.42f; kFrost = 0.25f;
  angle = 0.0f;
  catX = 0.0f; catY = 0.0f;
  walkT = 0.0f;
  pressPulse = 0.0f;

  for (int y = 0; y < VS_SPR_H; ++y) {
    dirtyLo[y] = VS_CX1; dirtyHi[y] = VS_CX0 - 1;
    inkLo[y] = VS_CX1;   inkHi[y] = VS_CX0 - 1;
  }
  if (buf) {
    float* o = buf;
    for (int i = 0; i < VS_CW * VS_SPR_H; ++i) {
      o[0] = VS_BG_R; o[1] = VS_BG_G; o[2] = VS_BG_B;
      o += 3;
    }
  }
}

// ---------------------------------------------------------------------------
// Update
// ---------------------------------------------------------------------------
void update(float dt, const InputFrame& input) {
  if (!(dt > 0.0f)) dt = 0.0f;
  if (dt > 0.1f) dt = 0.1f;

  PFParams::apply(input, 0, &walkK,  0.0f, 1.0f, VS_STEP[0]);
  PFParams::apply(input, 1, &dirK,   0.0f, 1.0f, VS_STEP[1]);
  PFParams::apply(input, 2, &zoomK,  0.0f, 1.0f, VS_STEP[2]);
  PFParams::apply(input, 3, &frostK, 0.0f, 1.0f, VS_STEP[3]);

  const float a = 1.0f - vsExpDecay(dt / 0.32f);
  kWalk  += (walkK  - kWalk)  * a;
  kZoom  += (zoomK  - kZoom)  * a;
  kFrost += (frostK - kFrost) * a;

  const float twoPi = (float)TWO_PI;
  const float piF = (float)PI;

  const float turn = dirK * twoPi;
  const float da = turn - angle;
  const float delta = PFMath::fastAtan2(PFMath::fastSin(da), PFMath::fastCos(da));
  angle += delta * a;
  if (angle > piF) angle -= twoPi;
  else if (angle < -piF) angle += twoPi;

  const float speed = 0.4f + 2.4f * kWalk;
  walkT += dt * speed * 1.15f;
  if (walkT >= VS_WALK_PERIOD) walkT -= VS_WALK_PERIOD;

  catX += PFMath::fastSin(angle) * dt * speed * 9.0f;
  catY -= PFMath::fastCos(angle) * dt * speed * 9.0f;

  pressPulse *= vsExpDecay(dt * 3.5f);
  if (input.btnPressed[0] || input.btnPressed[1] || input.btnPressed[2] || input.btnPressed[3]) {
    pressPulse = 1.0f;
  }
}

// ---------------------------------------------------------------------------
// Sprite rendering
// ---------------------------------------------------------------------------
static void clearDirty() {
  for (int y = 0; y < VS_SPR_H; ++y) {
    int lo = dirtyLo[y];
    int hi = dirtyHi[y];
    if (hi >= lo) {
      float* o = buf + (y * VS_CW + (lo - VS_CX0)) * 3;
      for (int x = lo; x <= hi; ++x) {
        o[0] = VS_BG_R; o[1] = VS_BG_G; o[2] = VS_BG_B;
        o += 3;
      }
    }
    dirtyLo[y] = VS_CX1; dirtyHi[y] = VS_CX0 - 1;
    inkLo[y] = VS_CX1;   inkHi[y] = VS_CX0 - 1;
  }
}

static void computePoses() {
  const float piF = (float)PI;
  for (int j = 0; j < 4; ++j) {
    const float side = VS_SIDE[j];
    const float u = PFMath::fract(walkT + VS_PHASE[j]);
    float lift = 0.0f;
    float travel;
    if (u < 0.65f) {
      travel = -5.0f + 10.0f * u / 0.65f;
    } else {
      const float ph = (u - 0.65f) / 0.35f;
      lift = PFMath::fastSin(piF * ph);
      travel = 5.0f - 10.0f * vsSmooth(ph);
    }
    const float weight = 1.0f - lift;
    const bool front = j < 2;
    VsFoot& f = feet[j];
    f.x = VS_ORG_X + side * (front ? 13.0f : 16.0f) + lift * side;
    f.y = VS_ORG_Y + (front ? -26.0f : 27.0f) + travel;
    f.lift = lift;
    f.scale = 1.0f + 0.65f * 0.24f * weight - lift * 0.19f + pressPulse * 0.10f * weight;
    f.contact = weight;
  }
}

static void buildSegments(float blur, float tailPhase) {
  setSeg(segs[0], -7.0f, -49.0f, -10.0f, -61.0f, 4.0f, 0.3f, blur);
  setSeg(segs[1],  5.0f, -49.0f,   8.0f, -59.0f, 4.0f, 0.3f, blur);

  float tx[8];
  for (int n = 0; n <= 7; ++n) {
    const float a = (float)n / 7.0f;
    tx[n] = 2.0f + PFMath::fastSin(a * 2.8f + tailPhase) * 17.0f * a;
  }
  for (int n = 0; n < 7; ++n) {
    const float a = (float)n / 7.0f;
    const float b = (float)(n + 1) / 7.0f;
    setSeg(segs[2 + n], tx[n], 34.0f + a * 34.0f, tx[n + 1], 34.0f + b * 34.0f,
           7.0f - a * 5.3f, 7.0f - b * 5.3f, blur);
  }
  for (int j = 0; j < 4; ++j) {
    const float side = VS_SIDE[j];
    const float ax = side * 7.0f;
    const float ay = (j < 2) ? -22.0f : 24.0f;
    const float ex = feet[j].x - VS_ORG_X;
    const float ey = feet[j].y - VS_ORG_Y;
    const float mx = ax * 0.4f + ex * 0.6f + side * 2.0f;
    const float my = ay * 0.6f + ey * 0.4f + 4.0f;
    setSeg(segs[9 + 2 * j],  ax, ay, mx, my, 6.8f, 4.3f, blur);
    setSeg(segs[10 + 2 * j], mx, my, ex, ey, 4.3f, 3.8f, blur);
  }
}

static void renderBody(float bendPhase, float blur) {
  const float frost = kFrost;
  const float invTwoBlur = 1.0f / (2.0f * blur);
  const float aMax = 0.98f - frost * 0.25f;
  const float texScale = 1.0f - frost * 0.75f;
  const float noseScale = 1.0f - frost * 0.7f;
  const float headLim0 = 1.0f + blur / 12.0f;
  uint8_t act[VS_NSEG];

  for (int y = VS_CY0; y < VS_CY1; ++y) {
    const float Y = desY(y);

    // --- row setup -------------------------------------------------------
    int xl = VS_CX1;
    int xh = VS_CX0 - 1;

    int na = 0;
    for (int i = 0; i < VS_NSEG; ++i) {
      if (Y >= segs[i].y0 && Y <= segs[i].y1) {
        act[na++] = (uint8_t)i;
        int xa = vsCol(segs[i].x0);
        int xb = vsCol(segs[i].x1) + 1;
        if (xa < xl) xl = xa;
        if (xb > xh) xh = xb;
      }
    }

    const float bend = 2.4f * PFMath::fastSin(Y * 0.043f + bendPhase) +
                       1.1f * PFMath::fastSin(Y * 0.11f);
    float t1 = (Y + 21.0f) * (1.0f / 18.0f);
    float t2 = (Y - 23.0f) * (1.0f / 17.0f);
    const float width = 14.3f + 5.4f * vsGauss(t1 * t1) + 5.8f * vsGauss(t2 * t2);
    const float invW = 1.0f / width;

    const bool boxRow = fabsf(Y) < 38.0f + blur;
    if (boxRow) {
      const float hw = width + blur + 1.0f;
      int xa = vsCol(bend - hw);
      int xb = vsCol(bend + hw) + 1;
      if (xa < xl) xl = xa;
      if (xb > xh) xh = xb;
    }

    const float hy = (Y + 44.0f) * (1.0f / 13.0f);
    const float hy2 = hy * hy;
    const bool headRow = hy2 < headLim0 * headLim0;
    const float hOff = 2.0f + Y * 0.025f;
    if (headRow) {
      const float m = sqrtf(headLim0 * headLim0 - hy2);
      int xa = vsCol(-hOff - 12.5f * m);
      int xb = vsCol(-hOff + 12.5f * m) + 1;
      if (xa < xl) xl = xa;
      if (xb > xh) xh = xb;
    }

    if (xl < VS_CX0) xl = VS_CX0;
    if (xh > VS_CX1 - 1) xh = VS_CX1 - 1;
    if (xl > xh) continue;
    markDirty(y, xl, xh);

    const float Ar = PFMath::fastSin(Y * 0.22f) * 2.0f + Y * 0.4f;
    const float sAr = PFMath::fastSin(Ar);
    const float cAr = PFMath::fastCos(Ar);
    const float Br = Y * 1.6f;
    const float sBr = PFMath::fastSin(Br);
    const float cBr = PFMath::fastCos(Br);
    const float sBelly = rowSBelly[y];
    const float sChest = rowSChest[y];
    const float sChin = rowSChin[y];
    const float sMuz = rowSMuz[y];
    const float sMouth = rowSMouth[y];
    const bool noseRow = fabsf(Y + 53.0f) < 1.5f;
    const float ny = (Y + 53.0f) * (1.0f / 1.3f);
    const float ny2 = ny * ny;
    const float absY = fabsf(Y);
    float* rowp = buf + y * VS_CW * 3;

    // --- pixels ----------------------------------------------------------
    for (int x = xl; x <= xh; ++x) {
      const float X = desX(x);
      float d = blur;   // capped: anything >= blur contributes no coverage

      if (boxRow) {
        const float ex = fabsf(X - bend) - width;
        if (ex <= blur + 0.7f) {
          float rough = 0.0f;
          if (ex > -8.0f) {
            rough = 0.45f * PFMath::fastSin(Y * 0.61f + X * 0.08f) +
                    0.22f * PFMath::fastSin(Y * 1.37f + X * 0.23f);
          }
          const float qx = ex - rough + 7.0f;
          const float qy = absY - 31.0f;
          const float pxp = qx > 0.0f ? qx : 0.0f;
          const float pyp = qy > 0.0f ? qy : 0.0f;
          const float len = (pxp > 0.0f && pyp > 0.0f) ? sqrtf(pxp * pxp + pyp * pyp) : (pxp + pyp);
          float mm = qx > qy ? qx : qy;
          if (mm > 0.0f) mm = 0.0f;
          const float db = len + mm - 7.0f;
          if (db < d) d = db;
        }
      }

      if (headRow) {
        const float hx = (X + hOff) * 0.08f;
        const float q2 = hx * hx + hy2;
        const float lim = 1.0f + d * (1.0f / 12.0f);
        if (lim > 0.0f && q2 < lim * lim) d = (sqrtf(q2) - 1.0f) * 12.0f;
      }

      for (int k = 0; k < na; ++k) {
        const VsSeg& s = segs[act[k]];
        if (X < s.x0 || X > s.x1) continue;
        const float px = X - s.ax;
        const float py = Y - s.ay;
        float t = (px * s.dx + py * s.dy) * s.inv;
        t = t < 0.0f ? 0.0f : (t > 1.0f ? 1.0f : t);
        const float ex = px - t * s.dx;
        const float ey = py - t * s.dy;
        const float rad = s.r0 + s.dr * t;
        const float lim = rad + d;
        if (lim > 0.0f) {
          const float q2 = ex * ex + ey * ey;
          if (q2 < lim * lim) d = sqrtf(q2) - rad;
        }
      }

      if (d >= blur) continue;
      const float cov = (1.0f - vsSmooth((d + blur) * invTwoBlur)) * aMax;
      if (cov <= 0.0f) continue;

      // --- shading ------------------------------------------------------
      const float xb = X - bend;
      float lat = xb * invW;
      lat = lat < -1.0f ? -1.0f : (lat > 1.0f ? 1.0f : lat);
      const float alat = fabsf(lat);
      const float volume = lutInterp(volLUT, VS_VN, (float)VS_VN, alat);

      const float bx = xb * (1.0f / 11.0f);
      const float belly = vsGauss(bx * bx + sBelly);
      const float cx1 = (X + 1.0f) * (1.0f / 11.0f);
      const float chest = vsGauss(cx1 * cx1 + sChest);
      const float cx2 = (X + 1.0f) * (1.0f / 8.0f);
      const float chin = vsGauss(cx2 * cx2 + sChin);

      float coat = 88.0f + 32.0f * volume - 12.0f * lat +
                   belly * 42.0f + chest * 27.0f + chin * 45.0f;

      const float sideMask = vsSmooth((alat - 0.35f) * (1.0f / 0.6f));
      if (sideMask > 0.0f) {
        const float sv = 0.5f + 0.5f * PFMath::fastSin(Y * 0.48f + fabsf(xb) * 0.29f);
        const float sv2 = sv * sv;
        const float sv4 = sv2 * sv2;
        coat -= sv4 * sv2 * sv * sideMask * 25.0f;
      }

      const int ci = x - VS_CX0;
      const float fwA = colS28[ci] * cAr + colC28[ci] * sAr;   // sin(X*2.8 + Ar)
      const float fwB = colS35[ci] * cBr + colC35[ci] * sBr;   // sin(X*0.35 + Y*1.6)
      const float gr = sprGrain(x, y);
      coat += (fwA * fwB * 6.0f + gr * 8.0f) * texScale;

      if (sMuz < VS_GSMAX) {
        const float m1x = (X + 3.2f) * (1.0f / 3.6f);
        const float m2x = (X - 2.6f) * (1.0f / 3.6f);
        const float m1 = vsGauss(m1x * m1x + sMuz);
        const float m2 = vsGauss(m2x * m2x + sMuz);
        coat += (m1 > m2 ? m1 : m2) * 25.0f;
      }

      float nose = 0.0f;
      if (noseRow && fabsf(X) < 2.3f) {
        const float nx = X * 0.5f;
        const float q2 = nx * nx + ny2;
        if (q2 < 1.21f) nose = (1.0f - vsSmooth((sqrtf(q2) - 0.6f) * 2.0f)) * noseScale;
      }

      float r = coat + 5.0f;
      float g = coat + 3.0f;
      float b = coat;
      r += (126.0f - r) * nose;
      g += (91.0f - g) * nose;
      b += (94.0f - b) * nose;

      const float mouth = vsGauss(2.0f * X * X + sMouth) * 0.35f;
      const float mk = 1.0f - mouth;
      r *= mk; g *= mk; b *= mk;

      float* o = rowp + ci * 3;
      o[0] = VS_BG_R + (r - VS_BG_R) * cov;
      o[1] = VS_BG_G + (g - VS_BG_G) * cov;
      o[2] = VS_BG_B + (b - VS_BG_B) * cov;

      const float ink = cov * (VS_BG_SUM - r - g - b);
      if (ink >= 3.0f) markInk(x, y);
    }
  }
}

static void drawPaw(int j) {
  const VsFoot& ft = feet[j];
  const float lift = ft.lift;
  const float scale = ft.scale;
  const float invS = 1.0f / scale;
  const float c = pawCos[j];
  const float s = pawSin[j];
  const float contact = ft.contact;
  const float opacity = 1.0f - lift * (0.28f + kFrost * 0.32f);
  const float extent = 16.0f * scale;
  const float softness = 1.15f + lift * 1.8f;
  const float invSoft2 = 1.0f / (2.0f * softness);
  const float edgeGain = (5.5f - lift * 3.5f) * scale;
  const float tuftPh = (float)j * 1.7f;
  const float strandPh = (float)j;
  const float shineR = 22.0f + contact * 19.0f;
  const float shineG = 24.0f + contact * 22.0f;
  const float shineB = 26.0f + contact * 23.0f;
  const float rimGain = contact * 16.0f;

  int x0 = PFMath::ifloor((ft.x - extent) * VS_SS);
  int x1 = PFMath::ifloor((ft.x + extent) * VS_SS) + 1;
  int y0 = PFMath::ifloor((ft.y - extent) * VS_SS);
  int y1 = PFMath::ifloor((ft.y + extent) * VS_SS) + 1;
  if (x0 < VS_CX0) x0 = VS_CX0;
  if (x1 > VS_CX1 - 1) x1 = VS_CX1 - 1;
  if (y0 < VS_CY0) y0 = VS_CY0;
  if (y1 > VS_CY1 - 1) y1 = VS_CY1 - 1;
  if (x0 > x1 || y0 > y1) return;

  for (int y = y0; y <= y1; ++y) {
    markDirty(y, x0, x1);
    const float dy = ((float)y + 0.5f) * VS_INV_SS - ft.y;
    const float dx0 = ((float)x0 + 0.5f) * VS_INV_SS - ft.x;
    float u = (dx0 * c + dy * s) * invS;
    float v = (-dx0 * s + dy * c) * invS;
    const float du = c * invS * VS_INV_SS;
    const float dv = -s * invS * VS_INV_SS;

    for (int x = x0; x <= x1; ++x, u += du, v += dv) {
      if (u < -12.0f || u > 12.0f || v < -16.0f || v > 13.0f) continue;

      float* o = buf + (y * VS_CW + (x - VS_CX0)) * 3;
      bool touched = false;
      float gr = 0.0f;
      bool haveGr = false;

      // ---- fur silhouette ------------------------------------------------
      const float pu = fabsf((u + 0.25f) * (1.0f / 7.4f));
      const float pv = fabsf((v - 1.2f) * (1.0f / 7.8f));
      const float palm = lutInterp(pow25LUT, VS_P25N, VS_P25SCALE, pu) +
                         lutInterp(pow25LUT, VS_P25N, VS_P25SCALE, pv);
      float furD = (lutInterp(pow04LUT, VS_P04N, VS_P04SCALE, palm) - 1.0f) * 7.4f;

      for (int t = 0; t < 4; ++t) {
        const float ta = (u - VS_TOE_TX[t]) * (1.0f / 3.0f);
        const float tb = (v - VS_TOE_TY[t]) * 0.25f;
        const float q2 = ta * ta + tb * tb;
        const float lim = 1.0f + (furD + 1.25f) * (1.0f / 3.0f);
        if (lim > 0.0f && q2 < lim * lim) {
          const float toeD = (sqrtf(q2) - 1.0f) * 3.0f;
          float diff = furD - toeD;
          if (diff < 0.0f) diff = -diff;
          float bl = 1.25f - diff;
          if (bl < 0.0f) bl = 0.0f;
          bl *= 0.8f;
          const float mn = furD < toeD ? furD : toeD;
          furD = mn - bl * bl * 0.3125f;
        }
      }

      if (furD < softness + 0.34f) {
        const float theta = PFMath::fastAtan2(v + 1.0f, u);
        const float tufts = 0.22f * PFMath::fastSin(theta * 5.0f + tuftPh) +
                            0.12f * PFMath::fastSin(theta * 8.0f + 1.2f);
        const float fd = furD - tufts;
        const float fur = (1.0f - vsSmooth((fd + softness) * invSoft2)) * opacity;
        if (fur > 0.0f) {
          gr = sprGrain(x, y);
          haveGr = true;
          float strands = 0.0f;
          const float sw = vsSmooth((fd + 2.5f) * (1.0f / 3.5f));
          if (sw > 0.0f) {
            strands = PFMath::fastSin(theta * 37.0f + sqrtf(u * u + v * v) * 1.1f + strandPh) * 1.5f * sw;
          }
          const float grey = 89.0f + gr * 9.0f + lift * 24.0f + strands;
          o[0] += (grey - o[0]) * fur;
          o[1] += (grey + 3.0f - o[1]) * fur;
          o[2] += (grey + 6.0f - o[2]) * fur;
          touched = true;
        }
      }

      // ---- jelly pads ----------------------------------------------------
      if (u >= -7.6f && u <= 7.6f && v >= -10.2f && v <= 6.2f) {
        float best = 99.0f;
        float bu = 0.0f;
        float bv = 0.0f;
        for (int t = 0; t < 4; ++t) {
          const float ex = u - VS_TOE_TX[t];
          const float ey = v - VS_TOE_TY[t];
          const float ja = (ex * toeCos[t] + ey * toeSin[t]) * (1.0f / 2.05f);
          const float jb = (-ex * toeSin[t] + ey * toeCos[t]) * (1.0f / 2.8f);
          const float q = ja * ja + jb * jb;
          if (q < best) { best = q; bu = ja; bv = jb; }
        }
        float central = 99.0f;
        for (int l = 0; l < 5; ++l) {
          const float ja = (u - VS_CPX[l]) * VS_CIX[l];
          const float jb = (v - VS_CPY[l]) * VS_CIY[l];
          const float q = ja * ja + jb * jb;
          if (q < central) central = q;
        }
        if (central < best) {
          best = central;
          bu = u * (1.0f / 4.5f);
          bv = (v - 2.3f) * (1.0f / 3.6f);
        }

        if (best < 1.0f) {
          float edge = (1.0f - best) * edgeGain;
          edge = edge < 0.0f ? 0.0f : (edge > 1.0f ? 1.0f : edge);
          edge *= opacity;

          const float dome = sqrtf(1.0f - best);
          const float sbu = bu + 0.32f;
          const float sbv = bv + 0.4f;
          const float shine = vsGauss(sbu * sbu * 12.0f + sbv * sbv * 15.0f);
          const float shade = 0.66f + 0.31f * dome - 0.07f * bv;
          const float b2 = best * best;
          const float rim = b2 * b2 * rimGain;
          if (!haveGr) gr = sprGrain(x, y);
          const float g2 = gr * 2.0f;

          const float rr = VS_JR * shade + shine * shineR + rim + g2;
          const float gg = VS_JG * shade + shine * shineG + rim + g2;
          const float bb = VS_JB * shade + shine * shineB + rim + g2;
          o[0] += (rr - o[0]) * edge;
          o[1] += (gg - o[1]) * edge;
          o[2] += (bb - o[2]) * edge;
          touched = true;
        }
      }

      if (touched && (VS_BG_SUM - (o[0] + o[1] + o[2])) >= 3.0f) markInk(x, y);
    }
  }
}

// ---------------------------------------------------------------------------
// Draw
// ---------------------------------------------------------------------------
void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);
  if (!buf) { PFCanvas::present(); return; }

  const float twoPi = (float)TWO_PI;
  const float piF = (float)PI;

  // ---- render the cat into the sprite -----------------------------------
  clearDirty();
  computePoses();

  const float blur = 1.0f + kFrost * 4.5f;
  const float bendPhase = PFMath::jsMod(walkT, 2.0f) * piF;
  const float tailPhase = PFMath::jsMod(walkT, 25.0f / 3.0f) * twoPi * 0.12f;
  buildSegments(blur, tailPhase);
  renderBody(bendPhase, blur);

  for (int j = 0; j < 4; ++j) {
    if (feet[j].lift > 0.05f) drawPaw(j);
  }
  for (int j = 0; j < 4; ++j) {
    if (feet[j].lift <= 0.05f) drawPaw(j);
  }

  // ---- view transform ---------------------------------------------------
  const float base = VS_BASE;
  const float z = base * (0.48f + kZoom * 1.35f);     // screen px per design unit
  const float zs = z * VS_INV_SS;                       // ... per sprite px
  const float invZ = 1.0f / zs;
  const float ca = PFMath::fastCos(angle);
  const float sa = PFMath::fastSin(angle);
  const float halfW = FRAME_W * 0.5f;
  const float halfH = FRAME_H * 0.5f;

  // extents of the cat silhouette in screen space (row end-points are enough)
  float minX = 1e30f, maxX = -1e30f, minY = 1e30f, maxY = -1e30f;
  bool anyInk = false;
  for (int y = VS_CY0; y < VS_CY1; ++y) {
    if (inkHi[y] < inkLo[y]) continue;
    anyInk = true;
    const float ly = ((float)y - VS_V0) * zs;
    for (int e = 0; e < 2; ++e) {
      const float sx = (float)(e == 0 ? inkLo[y] : inkHi[y]);
      const float lx = (sx - VS_U0) * zs;
      const float xx = lx * ca - ly * sa;
      const float yy = lx * sa + ly * ca;
      if (xx < minX) minX = xx;
      if (xx > maxX) maxX = xx;
      if (yy < minY) minY = yy;
      if (yy > maxY) maxY = yy;
    }
  }

  // re-enter from the opposite side only once the whole cat has left
  if (anyInk) {
    const float cx = catX * base;
    const float cy = catY * base;
    const bool outside = cx + maxX < -halfW - 1.0f ||
                         cx + minX > halfW + 1.0f ||
                         cy + maxY < -halfH - 1.0f ||
                         cy + minY > halfH + 1.0f;
    if (outside) {
      const float vx = sa;
      const float vy = -ca;
      const float avx = fabsf(vx);
      const float avy = fabsf(vy);
      const float tx = avx < 0.0001f ? 1e30f : (halfW + (vx > 0.0f ? maxX : -minX)) / avx;
      const float ty = avy < 0.0001f ? 1e30f : (halfH + (vy > 0.0f ? maxY : -minY)) / avy;
      float dist = (tx < ty ? tx : ty) - 1.0f;
      if (dist < 0.0f) dist = 0.0f;
      catX = -vx * dist / base;
      catY = -vy * dist / base;
    }
  }

  // ---- resample the sprite onto the frame --------------------------------
  const float offX = catX * base;
  const float offY = catY * base;
  const float grainAmt = 1.0f + kFrost * 2.0f;
  const float invW = 1.0f / (float)FRAME_W;
  const float invH = 1.0f / (float)FRAME_H;
  const float du = ca * invZ;
  const float dv = -sa * invZ;

  for (int y = 0; y < FRAME_H; ++y) {
    const float dy = (float)y + 0.5f - halfH - offY;
    const float dx0 = 0.5f - halfW - offX;
    float u = (dx0 * ca + dy * sa) * invZ + VS_U0;
    float v = (-dx0 * sa + dy * ca) * invZ + VS_V0;
    const float lightY = 3.0f * (float)y * invH;

    for (int x = 0; x < FRAME_W; ++x, u += du, v += dv) {
      float r = VS_BG_R;
      float g = VS_BG_G;
      float b = VS_BG_B;

      const int ix = PFMath::ifloor(u);
      const int iy = PFMath::ifloor(v);
      if (ix >= VS_CX0 && ix < VS_CX1 - 1 && iy >= 0 && iy < VS_SPR_H - 1) {
        const float fx = u - (float)ix;
        const float fy = v - (float)iy;
        const float* p0 = buf + (iy * VS_CW + (ix - VS_CX0)) * 3;
        const float* p1 = p0 + VS_CW * 3;
        const float wA = (1.0f - fx) * (1.0f - fy);
        const float wB = fx * (1.0f - fy);
        const float wC = (1.0f - fx) * fy;
        const float wD = fx * fy;
        r = p0[0] * wA + p0[3] * wB + p1[0] * wC + p1[3] * wD;
        g = p0[1] * wA + p0[4] * wB + p1[1] * wC + p1[4] * wD;
        b = p0[2] * wA + p0[5] * wB + p1[2] * wC + p1[5] * wD;
      }

      const float grain = (PFNoise::cellHash(x, y, 2) - 0.5f) * grainAmt;
      const float light = 4.0f * (float)x * invW + lightY;
      const float off = grain - light;

      PFCanvas::setPixel(x, y, vsByte(r + off), vsByte(g + off), vsByte(b + off));
    }
  }

  PFCanvas::present();
}

} // namespace VelvetSteps