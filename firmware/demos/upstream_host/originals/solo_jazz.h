#pragma once
#include <Arduino.h>
#include <math.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_mem.h"

// Solo Jazz: the 1990s paper-cup swash, improvised live. A teal dry brush lays down
// the chord (one bar, its pressure on an attack/release envelope, each bristle running
// out of ink at its own rate), and a purple pen plays a solo over it: a random walk on
// scale degrees in swung eighths, triplets or sixteenths, gliding between notes, with a
// calligraphic nib. Each phrase lands where the paper is emptiest; old ones fade.
// Knobs: Tempo (BPM), Solo (lazy wave .. bebop zigzag), Dry (wet .. dry brush),
// Paper (black .. cream). Push any knob: wash the paper and start a new phrase.
//
// A line-for-line twin of solo_jazz.js: the same generator, hash and draws in the same
// order, so the device paints what Pattern Lab previews. Everything scales with the
// short side, so FRAME_W / FRAME_H may be any size (64 x 128 as shared, 128 x 128 too).
//
// By Jonathan Lassoff. CC BY-SA 4.0.

namespace SoloJazz {

const char* NAME = "Solo Jazz";
const char* const KNOB_LABELS[4] = {"Tempo", "Solo", "Dry", "Paper"};
constexpr bool ABSOLUTE_READY = true;

constexpr int FRAME_W = 64;
constexpr int FRAME_H = 128;
constexpr int SJ_N = FRAME_W * FRAME_H;

constexpr float SJ_BRUSH_BEATS = 4.0f, SJ_PEN_DELAY = 1.5f;
constexpr int SJ_PEN_BEATS = 4;
constexpr int SJ_MAX_LANES = 96, SJ_MAX_NOTES = 24;
constexpr float SJ_T_MAX = 1.45f, SJ_P_MAX = 1.4f;     // ink over 1 shows as solid: fading starts late
constexpr float SJ_SWING = 0.64f;
constexpr float SJ_NIB_C = 0.7071f, SJ_NIB_S = -0.7071f;  // the pen's nib, at 45 degrees
constexpr float SJ_PREROLL_BEATS = 7.0f;
constexpr float SJ_PAPER[3] = {242, 228, 198};
constexpr float SJ_TEAL_LIGHT[3] = {64, 198, 204}, SJ_TEAL_DARK[3] = {10, 112, 148};
constexpr float SJ_PURPLE[3] = {96, 26, 176};

// knobs, at the cards' start: mid-range
static float tempo = 120.0f, solo = 0.5f, dry = 0.5f, paper = 0.5f;
static float tempoS, soloS, dryS, paperS;
static bool washReq = false;
static float wash = 0.0f;

static float* T = nullptr;    // teal ink
static float* Sh = nullptr;   // its shade, light 0 .. dark 1
static float* P = nullptr;    // purple ink

static uint32_t rng = 0x2468ace1u;
static float S = 1.0f, fadeBeats = 20.0f, lastY = -1000.0f;

// the phrase
static float pb = 0.0f, phraseLen = 7.0f;
static bool hasBrush = true, hasPen = true;
static float hw, L, cx, cy, bend, wobA, wobF, wobP, dx, dy, nx, ny, bias, amp;
static uint32_t seed = 0;
static int nLanes = 0, nNotes = 0;
static float penX = -1e9f, penY = -1e9f, nib = 1.0f;

struct Lane { float load, dep, shade, t0, t1; uint32_t seed; };
struct Note { float t; int deg; float acc; bool rest; };
static Lane lanes[SJ_MAX_LANES];
static Note notes[SJ_MAX_NOTES];

static inline uint32_t hash32(uint32_t x) {
  x ^= x >> 16;
  x *= 0x7feb352du;
  x ^= x >> 15;
  x *= 0x846ca68bu;
  return x ^ (x >> 16);
}

static inline float h01(uint32_t s, int i) {
  return (float)hash32(s + (uint32_t)i * 0x9e3779b9u) * (1.0f / 4294967296.0f);
}

static inline float vnoise(uint32_t s, float t) {
  const float fi = floorf(t), f = t - fi;
  const int i = (int)fi;
  const float a = h01(s, i), b = h01(s, i + 1);
  return a + (b - a) * f * f * (3.0f - 2.0f * f);
}

static inline float h2(uint32_t s, int ix, int iy) {
  return (float)hash32(s + (uint32_t)ix * 0x9e3779b9u + (uint32_t)iy * 0x85ebca6bu) * (1.0f / 4294967296.0f);
}

// 2D value noise: across the brush (bristle clumps) by along the stroke.
static float vnoise2(uint32_t s, float x, float y) {
  const float fx0 = floorf(x), fy0 = floorf(y);
  const int ix = (int)fx0, iy = (int)fy0;
  float fx = x - fx0, fy = y - fy0;
  fx = fx * fx * (3.0f - 2.0f * fx);
  fy = fy * fy * (3.0f - 2.0f * fy);
  const float a = h2(s, ix, iy), b = h2(s, ix + 1, iy);
  const float c = h2(s, ix, iy + 1), d = h2(s, ix + 1, iy + 1);
  return a + (b - a) * fx + (c - a + (d - c - b + a) * fx) * fy;
}

static inline float smooth(float x) {
  return x <= 0.0f ? 0.0f : x >= 1.0f ? 1.0f : x * x * (3.0f - 2.0f * x);
}

static inline float clamp01(float x) {
  return x < 0.0f ? 0.0f : x > 1.0f ? 1.0f : x;
}

static inline uint32_t nextU32() {
  uint32_t x = rng;
  x ^= x << 13;
  x ^= x >> 17;
  x ^= x << 5;
  rng = x;
  return x;
}

static inline float rnd() {
  return (float)(nextU32() >> 8) * (1.0f / 16777216.0f);
}

// Where the paper is emptiest, of six tries, and not on top of the last phrase.
static float pickY(float w) {
  float best = FRAME_H * 0.5f, bestScore = 1e30f;
  for (int k = 0; k < 6; k++) {
    const float y = FRAME_H * (0.1f + 0.8f * rnd());
    float score = fabsf(y - lastY) < w * 1.5f ? 1e6f : 0.0f;
    int y0 = (int)floorf(y - w), y1 = (int)floorf(y + w);
    if (y0 < 0) y0 = 0;
    if (y1 > FRAME_H - 1) y1 = FRAME_H - 1;
    for (int yy = y0; yy <= y1; yy += 2) {
      for (int x = 0; x < FRAME_W; x += 2) score += T[yy * FRAME_W + x] + P[yy * FRAME_W + x];
    }
    if (score < bestScore) { bestScore = score; best = y; }
  }
  return best;
}

static void newPhrase() {
  static const float RESTS[4] = {0.5f, 1.0f, 1.0f, 2.0f};
  pb = 0.0f;
  const float r = rnd();
  hasBrush = r >= 0.1f;                   // one in ten: the pen alone, a solo break
  hasPen = r < 0.1f || r >= 0.16f;        // and one in sixteen: the brush alone
  phraseLen = SJ_PEN_DELAY + SJ_PEN_BEATS + RESTS[(int)floorf(rnd() * 4.0f)];

  const float th = (rnd() * 2.0f - 1.0f) * 0.38f;
  const float dir = rnd() < 0.8f ? 1.0f : -1.0f;
  hw = S * (6.0f + rnd() * 3.0f);
  L = FRAME_W * (0.85f + rnd() * 0.45f) / cosf(th);
  cx = FRAME_W * (0.3f + rnd() * 0.4f);
  cy = pickY(hw);
  lastY = cy;
  bend = (rnd() * 2.0f - 1.0f) * 0.1f * L;
  wobA = S * (0.6f + rnd() * 1.2f);
  wobF = 0.8f + rnd() * 1.4f;
  wobP = rnd();
  dx = cosf(th) * dir; dy = sinf(th) * dir;
  nx = -dy; ny = dx;

  seed = nextU32();
  nLanes = (int)floorf(2.0f * hw / 0.55f) + 1;
  if (nLanes > SJ_MAX_LANES) nLanes = SJ_MAX_LANES;
  const float sf = 1.2f + rnd() * 1.6f;
  const float sp = rnd() * 6.2832f;
  for (int j = 0; j < nLanes; j++) {
    Lane& lane = lanes[j];
    const float u = -1.0f + 2.0f * j / (nLanes - 1);
    lane.load = 0.82f + 0.18f * rnd();
    lane.dep = 0.45f + 0.55f * rnd();
    lane.seed = nextU32();
    const float jitter = rnd() - 0.5f;
    lane.shade = clamp01(0.5f + 0.22f * sinf(u * 3.1416f * sf + sp) + jitter * 0.2f);
    lane.t0 = (0.05f + 0.03f * rnd()) * u * u;           // outer bristles touch down later
    lane.t1 = 1.0f - (0.06f + 0.06f * rnd()) * u * u;    // and lift sooner: a round start, a pointed tail
  }

  // The solo: a walk on scale degrees -5..5, one beat at a time.
  const float so = soloS;
  bias = (rnd() * 2.0f - 1.0f) * 0.3f * hw;
  amp = hw * (1.0f + 0.8f * so) / 5.0f;
  int deg = (int)floorf((rnd() * 2.0f - 1.0f) * 2.0f + 0.5f);
  bool up = rnd() < 0.5f;
  int n = 0;
  for (int b = 0; b < SJ_PEN_BEATS; b++) {
    const float rs = rnd();
    const int sub = rs < so * 0.75f ? 4 : rs < so ? 3 : 2;
    for (int s = 0; s < sub; s++) {
      Note& note = notes[n++];
      note.t = (b + (sub == 2 ? (s == 0 ? 0.0f : SJ_SWING) : (float)s / sub)) / SJ_PEN_BEATS;
      note.deg = deg;
      note.acc = s == 0 ? (b % 2 == 0 ? 1.0f : 0.6f) : 0.0f;
      note.rest = n > 1 && b < SJ_PEN_BEATS - 1 && rnd() < 0.04f;
      int size;
      if (rnd() < 0.08f + 0.25f * so) size = 3 + (int)floorf(rnd() * 3.0f);
      else size = rnd() < 0.4f ? 2 : 1;
      if (rnd() < 0.7f) up = !up;          // a squiggle mostly turns back
      deg += up ? size : -size;
      if (deg > 5) deg = 10 - deg;
      if (deg < -5) deg = -10 - deg;
    }
  }
  Note& last = notes[n++];
  last.t = 1.0f; last.deg = deg; last.acc = 0.0f; last.rest = false;
  nNotes = n;
  penX = penY = -1e9f;
}

static inline float pathOff(float t) {
  const float s = t - 0.5f;
  return bend * (1.0f - 4.0f * s * s) + wobA * sinf(6.2832f * (wobF * t + wobP));
}

static void splat(float x, float y, float a, float shade) {
  const float fx0 = floorf(x), fy0 = floorf(y);
  const int ix = (int)fx0, iy = (int)fy0;
  const float fx = x - fx0, fy = y - fy0;
  for (int k = 0; k < 4; k++) {
    const int px = ix + (k & 1), py = iy + (k >> 1);
    if (px < 0 || py < 0 || px >= FRAME_W || py >= FRAME_H) continue;
    const float wgt = ((k & 1) ? fx : 1.0f - fx) * ((k >> 1) ? fy : 1.0f - fy);
    const float aa = a * wgt;
    const int i = py * FRAME_W + px;
    const float t = T[i] + aa;
    T[i] = t > SJ_T_MAX ? SJ_T_MAX : t;
    const float m = aa * 2.0f;
    Sh[i] += (shade - Sh[i]) * (m > 1.0f ? 1.0f : m);
    const float q = P[i] - aa * 1.2f;     // fresh teal covers old purple
    P[i] = q > 0.0f ? q : 0.0f;
  }
}

static void paintBrush(float t0, float t1) {
  const float along = (t1 - t0) * L;
  int n = (int)ceilf(along / 0.45f);
  if (n < 1) n = 1;
  const float stepAlong = along / n;
  for (int i = 1; i <= n; i++) {
    const float t = t0 + (t1 - t0) * i / n;
    const float s = t - 0.5f, off0 = pathOff(t);
    const float x = cx + dx * s * L + nx * off0, y = cy + dy * s * L + ny * off0;
    const float att = t < 0.1f ? smooth(t / 0.1f) : 1.0f;
    const float rel = t > 0.78f ? smooth((1.0f - t) / 0.22f) : 1.0f;
    const float width = (0.4f + 0.6f * att) * (0.3f + 0.7f * rel);
    const float press = (0.75f + 0.25f * att) * (0.6f + 0.4f * rel);
    const float spacing = 2.0f * hw * width / (nLanes - 1);
    const float gain = 1.3f * stepAlong * spacing;
    const float tn = t * L / (4.5f * S), tc = t * L / (9.0f * S), te = t * L / (6.0f * S), ts = t * L / (14.0f * S);
    const float cu = hw / (1.4f * S);      // bristle clumps about 1.4 px wide
    for (int j = 0; j < nLanes; j++) {
      const Lane& lane = lanes[j];
      if (t < lane.t0 || t > lane.t1) continue;
      const float u = -1.0f + 2.0f * j / (nLanes - 1);
      float ink = lane.load * press - dryS * lane.dep * t * 0.9f
        + (vnoise2(seed, (u + 1.0f) * cu, tc) - 0.5f) * (0.2f + 1.5f * dryS)
        + (vnoise(lane.seed, tn) - 0.5f) * 0.15f;
      const float edge = fabsf(u);
      if (edge > 0.7f) ink -= (edge - 0.7f) / 0.3f * (0.2f + 1.0f * vnoise2(seed ^ 0x5bd1e995u, (u + 1.0f) * cu, te));
      if (ink < 0.12f) continue;            // a dry bristle skips: paper shows through
      ink = 0.45f + ink;
      if (ink > 1.0f) ink = 1.0f;
      const float off = u * hw * width;
      const float shade = clamp01(lane.shade + (vnoise2(seed ^ 0x27d4eb2fu, (u + 1.0f) * cu * 0.6f, ts) - 0.5f) * 0.9f);
      splat(x + nx * off, y + ny * off, ink * gain, shade);
    }
  }
}

static void disc(float x, float y, float r) {
  int x0 = (int)floorf(x - r - 1.0f), x1 = (int)ceilf(x + r + 1.0f);
  int y0 = (int)floorf(y - r - 1.0f), y1 = (int)ceilf(y + r + 1.0f);
  if (x0 < 0) x0 = 0;
  if (y0 < 0) y0 = 0;
  if (x1 > FRAME_W - 1) x1 = FRAME_W - 1;
  if (y1 > FRAME_H - 1) y1 = FRAME_H - 1;
  for (int py = y0; py <= y1; py++) {
    for (int px = x0; px <= x1; px++) {
      const float ddx = px - x, ddy = py - y;
      const float c = r + 0.5f - sqrtf(ddx * ddx + ddy * ddy);
      if (c <= 0.0f) continue;
      const float v = (c > 1.0f ? 1.0f : c) * SJ_P_MAX;
      const int i = py * FRAME_W + px;
      if (v > P[i]) P[i] = v;
    }
  }
}

static void paintPen(float tp0, float tp1) {
  const float along = (tp1 - tp0) * 1.08f * L;
  int n = (int)ceilf(along / 0.12f);
  if (n < 1) n = 1;
  const float glide = 0.85f * soloS * soloS;   // 0: notes joined by cosine glides, 1: nearly straight
  for (int i = 1; i <= n; i++) {
    const float tp = tp0 + (tp1 - tp0) * i / n;
    int k = 0;
    while (k < nNotes - 2 && notes[k + 1].t <= tp) k++;
    const Note& a = notes[k];
    const Note& b = notes[k + 1];
    const float f = clamp01((tp - a.t) / (b.t - a.t));
    const float cs = (1.0f - cosf(3.1416f * f)) * 0.5f;
    const float sm = cs + (f - cs) * glide;
    const float m = a.deg + (b.deg - a.deg) * sm;
    const float accent = a.acc * expf(-(tp - a.t) * SJ_PEN_BEATS * 6.0f);
    const float t = -0.04f + 1.08f * tp;
    const float s = t - 0.5f, off0 = pathOff(t);
    const float off = bias + m * amp;
    const float x = cx + dx * s * L + nx * off0 + nx * off;
    const float y = cy + dy * s * L + ny * off0 + ny * off;
    const float mx = x - penX, my = y - penY;
    const float len = sqrtf(mx * mx + my * my);
    if (penX > -1e8f && len > 1e-4f) nib = 0.6f + 0.6f * fabsf((my * SJ_NIB_C - mx * SJ_NIB_S) / len);
    else if (penX <= -1e8f) nib = 1.0f;
    penX = x; penY = y;
    if (a.rest) continue;
    const float taper = 0.35f + 0.65f * smooth(tp / 0.05f) * smooth((1.0f - tp) / 0.05f);
    disc(x, y, S * 0.85f * nib * (1.0f + 0.45f * accent) * taper);
  }
}

static void step(float dt) {
  const float kk = dt * 3.0f > 1.0f ? 1.0f : dt * 3.0f;
  tempoS += (tempo - tempoS) * kk;
  soloS += (solo - soloS) * kk;
  dryS += (dry - dryS) * kk;
  paperS += (paper - paperS) * (kk * 0.5f);
  if (washReq) { washReq = false; wash = 1.0f; newPhrase(); }

  const float bps = tempoS / 60.0f;
  const float rate = bps / fadeBeats + (wash > 0.0f ? 3.0f : 0.0f);
  if (wash > 0.0f) wash -= dt;
  const float fade = expf(-dt * rate);
  for (int i = 0; i < SJ_N; i++) { T[i] *= fade; P[i] *= fade; }

  const float pb0 = pb;
  pb += dt * bps;
  if (hasBrush) {
    const float t0 = clamp01(pb0 / SJ_BRUSH_BEATS), t1 = clamp01(pb / SJ_BRUSH_BEATS);
    if (t1 > t0) paintBrush(t0, t1);
  }
  if (hasPen) {
    const float t0 = clamp01((pb0 - SJ_PEN_DELAY) / SJ_PEN_BEATS), t1 = clamp01((pb - SJ_PEN_DELAY) / SJ_PEN_BEATS);
    if (t1 > t0) paintPen(t0, t1);
  }
  if (pb >= phraseLen) newPhrase();
}

static bool buffersOk() { return T && Sh && P; }

void setup() {
  if (!T) T = PFMem::allocFloats(SJ_N);
  if (!Sh) Sh = PFMem::allocFloats(SJ_N);
  if (!P) P = PFMem::allocFloats(SJ_N);
  tempo = 120.0f; solo = 0.5f; dry = 0.5f; paper = 0.5f;
  tempoS = tempo; soloS = solo; dryS = dry; paperS = paper;
  washReq = false;
  wash = 0.0f;
  rng = 0x2468ace1u;
  S = (FRAME_W < FRAME_H ? FRAME_W : FRAME_H) / 64.0f;
  fadeBeats = 8.0f + 6.0f * FRAME_H / (64.0f * S);
  lastY = -1000.0f;
  if (!buffersOk()) return;
  for (int i = 0; i < SJ_N; i++) T[i] = Sh[i] = P[i] = 0.0f;
  newPhrase();
  hasBrush = hasPen = true;               // open with the whole figure
  for (float b = 0.0f; b < SJ_PREROLL_BEATS; b += tempoS / 60.0f / 30.0f) step(1.0f / 30.0f);
}

void update(float dt, const InputFrame& input) {
  PFParams::apply(input, 0, &tempo, 60.0f, 180.0f, 2.5f);
  PFParams::apply(input, 1, &solo, 0.0f, 1.0f, 0.020833f);
  PFParams::apply(input, 2, &dry, 0.0f, 1.0f, 0.020833f);
  PFParams::apply(input, 3, &paper, 0.0f, 1.0f, 0.020833f);
  for (int i = 0; i < 4; i++) {
    if (input.btnPressed[i] && !input.paramAbsoluteActive[i] && !input.knobAudioActive[i]) washReq = true;
  }
  if (!buffersOk()) return;
  step(dt > 0.1f ? 0.1f : dt);
}

void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);
  if (!buffersOk()) { PFCanvas::present(); return; }
  const float pa = 1.0f - (1.0f - paperS) * (1.0f - paperS);   // mid-knob is already cream, not grey
  for (int y = 0; y < FRAME_H; y++) {
    for (int x = 0; x < FRAME_W; x++) {
      const int i = y * FRAME_W + x;
      const float grain = (h01(911u, i) - 0.5f) * 10.0f * pa;
      const float tc = T[i] > 1.0f ? 1.0f : T[i], pc = P[i] > 1.0f ? 1.0f : P[i], sh = Sh[i];
      float c[3];
      for (int ch = 0; ch < 3; ch++) {
        float v = SJ_PAPER[ch] * pa + grain;
        v += (SJ_TEAL_LIGHT[ch] + (SJ_TEAL_DARK[ch] - SJ_TEAL_LIGHT[ch]) * sh - v) * tc;
        v += (SJ_PURPLE[ch] - v) * pc;
        c[ch] = v < 0.0f ? 0.0f : v;
      }
      PFCanvas::setPixel(x, y, (uint8_t)(int)c[0], (uint8_t)(int)c[1], (uint8_t)(int)c[2]);
    }
  }
  PFCanvas::present();
}

}  // namespace SoloJazz
