// ===== Patternflow pattern =====
// Title:    Strawberry Rush
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/bb3c80ebdfe04652
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the frame is as tall as the
// original's, so the strawberries keep their size and the doubled width gets twice the
// traffic: up to twelve rockets instead of six (Quantity spans 1..12), launching from six
// lanes across the square rather than three, and fifty-two stars instead of twenty-six. The
// flight paths keep the original's sideways reach in pixels (they would otherwise lean twice
// as far over), and the opening flight is spread over the width instead of one column.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"
#include "src/core_color.h"
#include "src/core_noise.h"

namespace StrawberryRush {

constexpr int FRAME_W = 128;
constexpr int MAX_ROCKETS = 12;   // the original: 6
constexpr int STARS = 52;         // the original: 26 (of 30)
constexpr float REACH = 64.0f;    // the original's frame width: paths bend as far as there
constexpr int FRAME_H = 128;

const char* NAME = "Strawberry Rush";
const char* const KNOB_LABELS[4] = {"PowerBoost", "TakeoffCurve", "Quantity", "StarSize"};
constexpr bool ABSOLUTE_READY = true;

// Knob parameter states initialized with calibrated values
static float kPowerBoost = 1.0f;       // Knob 1: PowerBoost (0.0 to 1.0)
static float kTakeoffCurve = 117.95f;   // Knob 2: TakeoffCurve (0.0 to 120.0)
static float kQuantity = 9.0f;          // Knob 3: Quantity (1.0 to 9.0 -> maps to active rockets)
static float kStarSize = 6.537f;        // Knob 4: StarSize (0.0 to 10.0)

static float timeAcc = 0.0f;
static float glintTimeAcc = 0.0f;

// 17x19 Tilted Pixel-Art Strawberry Sprite Color Index Map
static const uint8_t SPRITE[19 * 17] = {
    0,0,0,0,0,0,0,0,0,1,1,0,1,1,0,0,0,
    0,0,0,0,0,0,0,0,1,3,2,1,3,2,1,0,0,
    0,0,0,0,0,0,0,1,3,3,2,3,3,2,1,1,0,
    0,0,0,0,0,0,1,1,2,3,3,2,3,3,2,1,1,
    0,0,0,1,1,1,1,3,3,2,2,3,3,2,1,1,0,
    0,0,1,4,4,4,1,1,1,1,1,1,1,1,1,0,0,
    0,1,4,7,6,4,4,1,4,4,4,4,4,4,1,0,0,
    1,4,7,6,6,4,8,5,4,8,5,4,4,4,5,1,0,
    1,4,6,6,4,5,5,4,5,5,4,8,5,4,5,1,0,
    1,4,4,4,8,5,4,8,5,4,5,5,4,5,5,1,0,
    1,4,8,5,5,4,5,5,4,8,5,4,5,5,5,1,0,
    1,4,5,5,4,8,5,4,5,5,4,8,5,5,5,1,0,
    0,1,4,4,5,5,4,8,5,4,5,5,5,5,1,0,0,
    0,1,4,8,5,4,5,5,4,8,5,5,5,1,0,0,0,
    0,0,1,4,5,5,4,8,5,5,5,5,1,0,0,0,0,
    0,0,0,1,4,8,5,5,5,5,5,1,0,0,0,0,0,
    0,0,0,0,1,4,5,5,5,5,1,0,0,0,0,0,0,
    0,0,0,0,0,1,1,4,5,1,0,0,0,0,0,0,0,
    0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0
};

static const uint8_t PALETTE[9 * 3] = {
    0, 0, 0,        // 0: Transparent
    20, 10, 15,     // 1: Dark Outline
    60, 175, 35,    // 2: Leaf Green
    135, 225, 55,   // 3: Leaf Highlight
    235, 15, 35,    // 4: Red Body
    160, 10, 25,    // 5: Dark Red Shadow
    255, 180, 200,  // 6: Specular Pink
    255, 255, 255,  // 7: Pure White
    255, 230, 40    // 8: Seed Yellow
};

struct Star {
    float u;
    float v;
    float baseSize;
    float speed;
    float phase;
};

static Star stars[STARS];

struct Rocket {
    float progress;
    float duration;
    float flightTime;
    float x0, x1, x2, x3;
    float currX, currY;
    float scale;
    float seed;
    float trailWidth;
};

static Rocket rockets[MAX_ROCKETS];

// Cubic Bezier evaluation helper
static inline float evalCubicX(float p, float x0, float x1, float x2, float x3) {
    float invP = 1.0f - p;
    return (invP * invP * invP * x0) +
           (3.0f * invP * invP * p * x1) +
           (3.0f * invP * p * p * x2) +
           (p * p * p * x3);
}

static void resetRocket(Rocket& r, float seedVal, float w, float bendKnobNorm) {
    r.seed = seedVal;
    r.flightTime = 0.0f;
    r.duration = 3.2f + PFNoise::cellHash((int)(seedVal * 13.0f), 0) * 2.8f;
    r.progress = 0.0f;

    // Six lanes, the original's three in each half of the square.
    int zone = (int)(PFNoise::cellHash((int)(seedVal * 21.0f), 1) * 6.0f);
    if (zone >= 6) zone = 5;
    const float half = (zone >= 3) ? 0.5f * w : 0.0f;
    const int lane = zone % 3;
    const float hw = 0.5f * w;

    if (lane == 0) {
        r.x0 = half + 0.05f * hw + PFNoise::cellHash((int)(seedVal * 31.0f), 2) * 0.20f * hw;
    } else if (lane == 1) {
        r.x0 = half + 0.40f * hw + PFNoise::cellHash((int)(seedVal * 31.0f), 3) * 0.20f * hw;
    } else {
        r.x0 = half + 0.75f * hw + PFNoise::cellHash((int)(seedVal * 31.0f), 4) * 0.20f * hw;
    }

    // Lands within the original's reach of its lane (its 10..90 % of 64), kept on the square.
    r.x3 = r.x0 + (PFNoise::cellHash((int)(seedVal * 43.0f), 5) - 0.5f) * 0.80f * REACH;
    r.x3 = fminf(fmaxf(r.x3, 0.10f * w), 0.90f * w);

    float curveWildness = 0.2f + bendKnobNorm * 2.2f;
    float bend1 = (PFNoise::cellHash((int)(seedVal * 57.0f), 6) - 0.5f) * REACH * 1.5f * curveWildness;
    float bend2 = (PFNoise::cellHash((int)(seedVal * 69.0f), 7) - 0.5f) * REACH * 1.5f * curveWildness;

    r.x1 = r.x0 + bend1;
    r.x2 = r.x3 + bend2;
    r.trailWidth = 5.5f + PFNoise::cellHash((int)(seedVal * 72.0f), 8) * 3.5f;
}

void setup() {
    PFMath::buildSinLUT();

    for (int i = 0; i < STARS; i++) {
        stars[i].u = PFNoise::cellHash(i * 3, 17);
        stars[i].v = PFNoise::cellHash(i * 7, 43);
        stars[i].baseSize = 1.2f + PFNoise::cellHash(i * 11, 2) * 2.0f;
        stars[i].speed = 1.5f + PFNoise::cellHash(i * 13, 7) * 2.5f;
        stars[i].phase = PFNoise::cellHash(i * 17, 9) * TWO_PI;
    }

    // The original starts all six on one path (a column of strawberries); here each starts on a
    // lane of its own, staggered in time as there.
    const float bendInit = kTakeoffCurve / 120.0f;
    for (int i = 0; i < MAX_ROCKETS; i++) {
        resetRocket(rockets[i], (float)i * 2.37f, (float)FRAME_W, bendInit);
        rockets[i].flightTime = (float)(i % 6) * 0.6f + (float)(i / 6) * 0.3f;
        rockets[i].currX = rockets[i].x0;
        rockets[i].currY = (float)FRAME_H + 35.0f;
        rockets[i].scale = 2.0f;
    }
}

void update(float dt, const InputFrame& input) {
    PFParams::apply(input, 0, &kPowerBoost, 0.0f, 1.0f, 0.021f);
    PFParams::apply(input, 1, &kTakeoffCurve, 0.0f, 120.0f, 2.5f);
    PFParams::apply(input, 2, &kQuantity, 1.0f, 9.0f, 0.167f);
    PFParams::apply(input, 3, &kStarSize, 0.0f, 10.0f, 0.208f);

    float powerBoost = kPowerBoost;
    float speedMult = 0.25f + powerBoost * 1.5f;

    timeAcc += dt * speedMult;
    if (timeAcc > TWO_PI * 100.0f) {
        timeAcc -= TWO_PI * 100.0f;
    }

    glintTimeAcc += dt * 12.0f;
    if (glintTimeAcc > 10000.0f) {
        glintTimeAcc -= 10000.0f;
    }

    float w = (float)FRAME_W;
    float h = (float)FRAME_H;
    float bendKnobNorm = kTakeoffCurve / 120.0f;
    bendKnobNorm = fminf(1.0f, fmaxf(0.0f, bendKnobNorm));

    for (int i = 0; i < MAX_ROCKETS; i++) {
        Rocket& r = rockets[i];
        r.flightTime += dt * speedMult;

        float normTime = r.flightTime / r.duration;
        if (normTime > 1.0f) normTime = 1.0f;

        r.progress = normTime * normTime;
        r.scale = 2.0f - r.progress * 1.50f;

        float p = r.progress;
        r.currX = evalCubicX(p, r.x0, r.x1, r.x2, r.x3);
        r.currY = (1.0f - p) * (h + 35.0f) + p * (-45.0f);

        if (r.progress >= 1.0f) {
            resetRocket(r, r.seed + timeAcc + 1.1f, w, bendKnobNorm);
        }
    }
}

// Structs for row-level spatial filtering
struct RowStar {
    float sx;
    float dy;
    float effSize;
    float invEffSize;
    float maxDx;
    float twinkle;
};

struct RowTrail {
    float tx;
    float tw;
    float invTw;
    float fadeBase;
    float hueBase;
    float coreGlowBase;
    float nozzleGlowBase;
    bool hasNozzle;
};

struct RowSprite {
    int rx;
    int renderW;
    int syOffset;
    float invSc;
    int rowHashBase;
    float shimmerBase;
};

void draw() {
    PFCanvas::setFrame(FRAME_W, FRAME_H);

    float t = timeAcc;
    float k4Norm = kStarSize / 10.0f;
    k4Norm = fminf(1.0f, fmaxf(0.0f, k4Norm));

    float k3Norm = (kQuantity - 1.0f) / 8.0f;
    k3Norm = fminf(1.0f, fmaxf(0.0f, k3Norm));
    int activeRockets = (int)(k3Norm * (float)(MAX_ROCKETS - 1) + 1.0f);
    if (activeRockets < 1) activeRockets = 1;
    if (activeRockets > MAX_ROCKETS) activeRockets = MAX_ROCKETS;

    float powerBoost = kPowerBoost;
    float baseTrailLen = 45.0f + powerBoost * 45.0f;
    float starSizeMult = 0.8f + k4Norm * 3.5f;

    int glintFrame = (int)glintTimeAcc;

    // Precalculate column wave terms
    float wave1_x[FRAME_W];
    for (int x = 0; x < FRAME_W; x++) {
        wave1_x[x] = PFMath::fastSin((float)x * 0.06f + t * 0.5f);
    }

    // Precalculate per-star frame parameters
    float star_sx[STARS];
    float star_sy[STARS];
    float star_effSize[STARS];
    float star_invEffSize[STARS];
    float star_maxDy[STARS];
    float star_twinkle[STARS];

    for (int s = 0; s < STARS; s++) {
        star_sx[s] = stars[s].u * (float)FRAME_W;
        star_sy[s] = stars[s].v * (float)FRAME_H;
        float eff = stars[s].baseSize * starSizeMult;
        star_effSize[s] = eff;
        star_invEffSize[s] = (eff > 0.0001f) ? (1.0f / eff) : 0.0f;
        star_maxDy[s] = eff * 2.2f;
        float twinkleSin = PFMath::fastSin(t * stars[s].speed + stars[s].phase);
        star_twinkle[s] = 0.2f + 0.8f * fmaxf(0.0f, twinkleSin);
    }

    RowStar rowStars[STARS];
    RowTrail rowTrails[MAX_ROCKETS];
    RowSprite rowSprites[MAX_ROCKETS];

    uint8_t rowR[FRAME_W];
    uint8_t rowG[FRAME_W];
    uint8_t rowB[FRAME_W];
    float starGlow[FRAME_W];

    for (int y = 0; y < FRAME_H; y++) {
        float fy = (float)y;

        // Background row terms
        float bgVal = 0.88f + 0.12f * PFMath::fastCos(fy * 0.05f - t);
        float y_wave2_phase = fy * 0.04f - t * 0.3f;
        float fy_003 = fy * 0.03f;

        // 1. Filter stars intersecting row y
        int numRowStars = 0;
        for (int s = 0; s < STARS; s++) {
            float dy = fabsf(fy - star_sy[s]);
            if (dy < star_maxDy[s]) {
                rowStars[numRowStars++] = {
                    star_sx[s], dy, star_effSize[s], star_invEffSize[s], star_maxDy[s], star_twinkle[s]
                };
            }
        }

        // 2. Filter rocket trails intersecting row y
        int numRowTrails = 0;
        for (int i = 0; i < activeRockets; i++) {
            const Rocket& rk = rockets[i];
            float sc = rk.scale;
            float attachY = rk.currY + 16.0f * sc;
            float trailLen = baseTrailLen * (0.5f + sc * 0.5f);
            float dy = fy - attachY;

            if (dy >= 0.0f && dy < trailLen) {
                float pTrail = rk.progress - (dy / ((float)FRAME_H + 60.0f));
                if (pTrail < 0.0f) pTrail = 0.0f;

                float tx = evalCubicX(pTrail, rk.x0, rk.x1, rk.x2, rk.x3);

                float flameFlicker = PFMath::fastSin(t * (14.0f + powerBoost * 10.0f) - dy * 0.3f + rk.seed) * 0.18f +
                                     PFMath::fastCos(t * 20.0f + dy * 0.5f) * 0.12f;

                float tRatio = dy / trailLen;
                float tw = ((rk.trailWidth * sc) + flameFlicker) * (1.0f - tRatio * 0.35f);

                if (dy < 8.0f * sc && sc > 0.001f) {
                    tw = 3.5f * sc + (dy / (8.0f * sc)) * (rk.trailWidth * sc - 3.5f * sc);
                }

                if (tw > 0.001f) {
                    float hueBase = t * (0.25f + powerBoost * 0.35f) + dy * 0.02f + rk.seed * 0.2f;
                    float coreGlowBase = (0.6f + 0.4f * PFMath::fastSin(t * 12.0f - dy * 0.2f));
                    bool hasNozzle = (dy < 10.0f * sc && sc > 0.001f);
                    float nozzleGlowBase = hasNozzle ? ((1.0f - dy / (10.0f * sc)) * (0.8f + powerBoost * 0.4f)) : 0.0f;

                    rowTrails[numRowTrails++] = {
                        tx, tw, 1.0f / tw, (1.0f - tRatio), hueBase, coreGlowBase, nozzleGlowBase, hasNozzle
                    };
                }
            }
        }

        // 3. Filter rocket sprites intersecting row y
        int numRowSprites = 0;
        for (int i = 0; i < activeRockets; i++) {
            const Rocket& rk = rockets[i];
            float sc = rk.scale;
            if (sc < 0.001f) continue;

            int renderW = (int)ceilf(17.0f * sc);
            int renderH = (int)ceilf(19.0f * sc);
            int ry = (int)floorf(rk.currY);

            if (y >= ry && y < ry + renderH) {
                int sy = (int)floorf((float)(y - ry) / sc);
                if (sy >= 0 && sy < 19) {
                    int rx = (int)floorf(rk.currX - ((float)renderW * 0.5f));
                    float shimmerBase = t * 10.0f - (float)sy * 0.6f + rk.seed * 2.0f;
                    int rowHashBase = sy * 37 + (int)(rk.seed * 11.0f);
                    rowSprites[numRowSprites++] = {
                        rx, renderW, sy * 17, 1.0f / sc, rowHashBase, shimmerBase
                    };
                }
            }
        }

        // Base Layer: Soft Pastel Iridescent Gradient Background
        for (int x = 0; x < FRAME_W; x++) {
            float fx = (float)x;
            float wave1 = wave1_x[x];
            float wave2 = PFMath::fastCos(y_wave2_phase + fx * 0.02f);
            float bgHue = PFMath::fract(0.42f + 0.28f * wave1 + 0.14f * wave2 + k4Norm * 0.2f);
            float bgSat = 0.38f + 0.18f * PFMath::fastSin(fx * 0.03f + fy_003);

            PFColor::hsvToRgb(bgHue, bgSat, bgVal, rowR[x], rowG[x], rowB[x]);
        }

        // Star Layer: 1D Active Bounding Span Rasterization with Zero-Cost Bypass
        if (numRowStars > 0) {
            int boundMinX = FRAME_W;
            int boundMaxX = -1;

            for (int x = 0; x < FRAME_W; x++) {
                starGlow[x] = 0.0f;
            }

            for (int s = 0; s < numRowStars; s++) {
                const RowStar& st = rowStars[s];
                int minX = (int)floorf(st.sx - st.maxDx);
                int maxX = (int)ceilf(st.sx + st.maxDx);
                if (minX < 0) minX = 0;
                if (maxX >= FRAME_W) maxX = FRAME_W - 1;

                if (minX < boundMinX) boundMinX = minX;
                if (maxX > boundMaxX) boundMaxX = maxX;

                for (int x = minX; x <= maxX; x++) {
                    float dx = fabsf((float)x - st.sx);
                    if (dx < st.maxDx) {
                        float cross1 = fmaxf(0.0f, 1.0f - (dx + st.dy * 2.2f) * st.invEffSize);
                        float cross2 = fmaxf(0.0f, 1.0f - (dx * 2.2f + st.dy) * st.invEffSize);
                        float glow = (cross1 + cross2) * st.twinkle;
                        if (glow > starGlow[x]) starGlow[x] = glow;
                    }
                }
            }

            for (int x = boundMinX; x <= boundMaxX; x++) {
                if (starGlow[x] > 0.05f) {
                    float sg = fminf(1.0f, starGlow[x] * 1.1f);
                    uint32_t a8 = (uint32_t)(sg * 256.0f);
                    uint32_t invA8 = 256 - a8;
                    rowR[x] = (uint8_t)((rowR[x] * invA8 + 255 * a8) >> 8);
                    rowG[x] = (uint8_t)((rowG[x] * invA8 + 255 * a8) >> 8);
                    rowB[x] = (uint8_t)((rowB[x] * invA8 + 255 * a8) >> 8);
                }
            }
        }

        // Flame Plume Layer: DDA Stepping + Fast Fixed-Point Blending
        for (int i = 0; i < numRowTrails; i++) {
            const RowTrail& rt = rowTrails[i];
            int minX = (int)ceilf(rt.tx - rt.tw);
            int maxX = (int)floorf(rt.tx + rt.tw);
            if (minX < 0) minX = 0;
            if (maxX >= FRAME_W) maxX = FRAME_W - 1;
            if (minX > maxX) continue;

            float uAcross = ((float)minX - rt.tx) * rt.invTw;
            float uAcrossStep = rt.invTw;

            for (int x = minX; x <= maxX; x++) {
                float absU = fabsf(uAcross);
                float hueTrail = PFMath::fract(uAcross * 0.38f + rt.hueBase);
                float fade = rt.fadeBase * (1.0f - absU * 0.25f);

                uint8_t trR = 0, trG = 0, trB = 0;
                PFColor::hsvToRgb(hueTrail, 0.95f, 1.0f, trR, trG, trB);

                float u2 = uAcross * uAcross;
                // Degree-3 Horner polynomial for exp(-3.2 * u2)
                float expTerm = ((-1.2692f * u2 + 3.1410f) * u2 - 2.8260f) * u2 + 0.9831f;
                if (expTerm < 0.0f) expTerm = 0.0f;
                float coreGlow = expTerm * rt.coreGlowBase;

                if (rt.hasNozzle) {
                    float nozzleGlow = rt.nozzleGlowBase * (1.0f - absU);
                    if (nozzleGlow > coreGlow) coreGlow = nozzleGlow;
                }

                if (coreGlow > 0.1f) {
                    float cg = fminf(1.0f, coreGlow);
                    uint32_t cg8 = (uint32_t)(cg * 256.0f);
                    uint32_t invCg8 = 256 - cg8;
                    trR = (uint8_t)((trR * invCg8 + 255 * cg8) >> 8);
                    trG = (uint8_t)((trG * invCg8 + 255 * cg8) >> 8);
                    uint32_t targetB = 200 + (uint32_t)(powerBoost * 55.0f);
                    trB = (uint8_t)((trB * invCg8 + targetB * cg8) >> 8);
                    fade = fminf(1.0f, fade + cg * 0.4f);
                }

                uint32_t f8 = (uint32_t)(fade * 256.0f);
                uint32_t invF8 = 256 - f8;
                rowR[x] = (uint8_t)((rowR[x] * invF8 + trR * f8) >> 8);
                rowG[x] = (uint8_t)((rowG[x] * invF8 + trG * f8) >> 8);
                rowB[x] = (uint8_t)((rowB[x] * invF8 + trB * f8) >> 8);

                uAcross += uAcrossStep;
            }
        }

        // Sprite Layer: DDA Texture Stepping Direct Blit
        for (int i = 0; i < numRowSprites; i++) {
            const RowSprite& rsp = rowSprites[i];
            int minX = rsp.rx;
            int maxX = rsp.rx + rsp.renderW - 1;
            if (minX < 0) minX = 0;
            if (maxX >= FRAME_W) maxX = FRAME_W - 1;
            if (minX > maxX) continue;

            float sx_f = (float)(minX - rsp.rx) * rsp.invSc;
            float sx_step = rsp.invSc;

            for (int x = minX; x <= maxX; x++) {
                int sx = (int)sx_f;

                if (sx >= 0 && sx < 17) {
                    uint8_t colorIdx = SPRITE[rsp.syOffset + sx];

                    if (colorIdx > 0) {
                        int pIdx = colorIdx * 3;
                        uint8_t sr = PALETTE[pIdx];
                        uint8_t sg = PALETTE[pIdx + 1];
                        uint8_t sb = PALETTE[pIdx + 2];

                        float shimmerWave = PFMath::fastSin(rsp.shimmerBase - (float)sx * 0.4f);
                        if (shimmerWave > 0.3f) {
                            if (colorIdx == 6 || colorIdx == 7) {
                                sr = 255; sg = 255; sb = 255;
                            } else if (colorIdx == 8) {
                                sr = 255; sg = 255; sb = 180;
                            } else if (colorIdx == 4 && shimmerWave > 0.8f) {
                                uint32_t r32 = (uint32_t)sr + 70;
                                uint32_t g32 = (uint32_t)sg + 50;
                                uint32_t b32 = (uint32_t)sb + 90;
                                sr = (uint8_t)(r32 > 255 ? 255 : r32);
                                sg = (uint8_t)(g32 > 255 ? 255 : g32);
                                sb = (uint8_t)(b32 > 255 ? 255 : b32);
                            }
                        }

                        float glintHash = PFNoise::cellHash(sx * 17 + rsp.rowHashBase, glintFrame);
                        if (glintHash > 0.88f && colorIdx > 1) {
                            sr = 255; sg = 255; sb = 255;
                        }

                        rowR[x] = sr;
                        rowG[x] = sg;
                        rowB[x] = sb;
                    }
                }

                sx_f += sx_step;
            }
        }

        // Flush scanline directly to Canvas
        for (int x = 0; x < FRAME_W; x++) {
            PFCanvas::setPixel(x, y, rowR[x], rowG[x], rowB[x]);
        }
    }

    PFCanvas::present();
}

} // namespace StrawberryRush