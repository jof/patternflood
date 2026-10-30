// ===== Patternflow pattern =====
// Title:    Starlight Jester Ribbon
// Author:   @martinnlopez (ported by @engmung)
// Source:   https://community.patternflow.work/community/p/b2683ba1d9fc4647
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-30): the frame is 128 wide, so the hood,
// dots and ribbon spread across the square, and the ribbon's baked pixel list holds 6000
// instead of 4000. At 128 wide the ribbon covers 5403 pixels; the list fills top down, so with
// room for 4000 it stopped at row 100 and cut off the ribbon's tail. Knobs as the original.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_math.h"
#include "src/core_mem.h"

namespace StarlightJesterRibbon {

    const char* NAME = "Starlight Jester Ribbon";
    const char* const KNOB_LABELS[4] = {"Speed", "Twinkle", "DiaWidth", "DiaHeight"};

    constexpr int FRAME_W = 128;
    constexpr int FRAME_H = 128;

    constexpr uint8_t PINK[3] = {241, 147, 189};
    constexpr uint8_t BLUE[3] = {43, 98, 174};

    struct Star {
        float u, v;
        float outerR;
        float angle;
        float rotSpeed;
        float twinklePhase;
        float twinkleMul;
    };

    struct Dot {
        float u, v, r;
        float phase;
        float speedMul;
    };

    struct Segment {
        float ax, ay;
        float bx, by;
        float dx, dy;
        float len;
        float invLenSq;
        float sA;
        int minX, maxX;
        int minY, maxY;
    };

    struct RibbonPixel {
        uint8_t x;
        uint8_t y;
        float along;
        float across;
        float dist;
    };

    constexpr int NUM_STARS = 22;
    constexpr int NUM_DOTS = 12;
    constexpr int MAX_SEGS = 160;
    constexpr int MAX_RIBBON_PIXELS = 6000;

    static Star stars[NUM_STARS];
    static Dot dots[NUM_DOTS];
    static Segment segments[MAX_SEGS];
    static int numSegments = 0;

    static RibbonPixel* ribbonPixels = nullptr;
    static int ribbonPixelCount = 0;
    static uint8_t hoodMaxX[FRAME_H];

    static float timeAcc = 0.0f;
    static float paramSpeed = 1.0f;
    static float paramTwinkle = 2.0f;
    static float paramDiaWidth = 10.0f;
    static float paramDiaHeight = 1.0f;

    static inline float floatMod(float n, float m) {
        return fmodf(fmodf(n, m) + m, m);
    }

    static inline float hoodEdgeAt(float v) {
        constexpr float topEdge = 0.10f;
        constexpr float bottomEdge = 0.58f;
        if (v < topEdge) return 1.0f;
        if (v > bottomEdge) return 0.0f;
        return 1.0f - (v - topEdge) / (bottomEdge - topEdge);
    }

    static inline bool starMask(float dx, float dy, float outerR, float innerR) {
        float rSq = dx * dx + dy * dy;
        if (rSq > outerR * outerR) return false;
        float r = sqrtf(rSq);
        float theta = PFMath::fastAtan2(dy, dx);
        if (theta < 0.0f) theta += TWO_PI;
        constexpr float seg = TWO_PI / 5.0f;
        constexpr float invHalfSeg = 2.0f / seg;
        float a = fmodf(theta, seg);
        if (a < 0.0f) a += seg;
        if (a > seg * 0.5f) a = seg - a;
        float tpt = a * invHalfSeg;
        float boundaryR = outerR + (innerR - outerR) * tpt;
        return r <= boundaryR;
    }

    static void buildRibbonPath(int W, int H) {
        constexpr float halfWidth = 8.0f;
        struct PointUV { float u, v; };
        constexpr PointUV controlPts[14] = {
            { 0.00f, 0.65f }, { 0.04f, 0.72f }, { 0.12f, 0.78f }, { 0.22f, 0.55f },
            { 0.32f, 0.28f }, { 0.50f, 0.10f }, { 0.70f, 0.12f }, { 0.88f, 0.28f },
            { 0.94f, 0.50f }, { 0.82f, 0.72f }, { 0.55f, 0.82f }, { 0.30f, 0.90f },
            { 0.12f, 0.98f }, { 0.05f, 1.05f }
        };

        struct PointXY { float x, y; };
        constexpr int stepsPerSeg = 12;
        constexpr int maxWaypoints = (14 - 3) * stepsPerSeg + 1;
        PointXY waypoints[maxWaypoints];
        int numWaypoints = 0;

        for (int i = 1; i < 14 - 2; i++) {
            PointUV p0 = controlPts[i - 1];
            PointUV p1 = controlPts[i];
            PointUV p2 = controlPts[i + 1];
            PointUV p3 = controlPts[i + 2];

            for (int s = 0; s < stepsPerSeg; s++) {
                float t = (float)s / (float)stepsPerSeg;
                float t2 = t * t;
                float t3 = t2 * t;

                float x = 0.5f * (
                    (2.0f * p1.u) +
                    (-p0.u + p2.u) * t +
                    (2.0f * p0.u - 5.0f * p1.u + 4.0f * p2.u - p3.u) * t2 +
                    (-p0.u + 3.0f * p1.u - 3.0f * p2.u + p3.u) * t3
                ) * (float)W;

                float y = 0.5f * (
                    (2.0f * p1.v) +
                    (-p0.v + p2.v) * t +
                    (2.0f * p0.v - 5.0f * p1.v + 4.0f * p2.v - p3.v) * t2 +
                    (-p0.v + 3.0f * p1.v - 3.0f * p2.v + p3.v) * t3
                ) * (float)H;

                waypoints[numWaypoints++] = { x, y };
            }
        }

        PointUV last = controlPts[14 - 2];
        waypoints[numWaypoints++] = { last.u * (float)W, last.v * (float)H };

        numSegments = 0;
        float accumLen = 0.0f;
        constexpr float pad = halfWidth + 2.0f;

        for (int i = 0; i < numWaypoints - 1; i++) {
            float ax = waypoints[i].x;
            float ay = waypoints[i].y;
            float bx = waypoints[i + 1].x;
            float by = waypoints[i + 1].y;

            float dx = bx - ax;
            float dy = by - ay;
            float lenSq = dx * dx + dy * dy;
            if (lenSq < 1e-5f) continue;

            float len = sqrtf(lenSq);

            segments[numSegments++] = {
                ax, ay,
                bx, by,
                dx, dy,
                len,
                1.0f / lenSq,
                accumLen,
                (int)floorf(fminf(ax, bx) - pad),
                (int)ceilf(fmaxf(ax, bx) + pad),
                (int)floorf(fminf(ay, by) - pad),
                (int)ceilf(fmaxf(ay, by) + pad)
            };
            accumLen += len;
        }
    }

    void setup() {
        PFMath::buildSinLUT();

        timeAcc = 0.0f;
        paramSpeed = 1.0f;
        paramTwinkle = 2.0f;
        paramDiaWidth = 10.0f;
        paramDiaHeight = 1.0f;

        // 1. 후드 경계선 1D LUT 베이킹
        for (int y = 0; y < FRAME_H; y++) {
            float v = (float)y / (float)FRAME_H;
            hoodMaxX[y] = (uint8_t)fminf((float)FRAME_W, fmaxf(0.0f, hoodEdgeAt(v) * (float)FRAME_W));
        }

        // 2. 별/도트 초기화
        for (int i = 0; i < NUM_STARS; i++) {
            float vy = 0.02f + (float)rand() / (float)RAND_MAX * 0.48f;
            float maxU = fmaxf(hoodEdgeAt(vy) - 0.05f, 0.06f);
            float u = 0.02f + (float)rand() / (float)RAND_MAX * maxU;
            stars[i].u = u;
            stars[i].v = vy;
            stars[i].outerR = 3.0f + (float)rand() / (float)RAND_MAX * 3.5f;
            stars[i].angle = (float)rand() / (float)RAND_MAX * TWO_PI;
            stars[i].rotSpeed = (0.3f + (float)rand() / (float)RAND_MAX * 0.6f) * (((rand() % 2) == 0) ? -1.0f : 1.0f);
            stars[i].twinklePhase = (float)rand() / (float)RAND_MAX * TWO_PI;
            stars[i].twinkleMul = 0.7f + (float)rand() / (float)RAND_MAX * 0.8f;
        }

        constexpr struct { float u, v, r; } dotSpecs[NUM_DOTS] = {
            { 0.62f, 0.32f, 7.0f }, { 0.80f, 0.44f, 6.0f }, { 0.90f, 0.20f, 4.0f },
            { 0.25f, 0.55f, 4.0f }, { 0.18f, 0.72f, 3.5f }, { 0.50f, 0.62f, 4.0f },
            { 0.72f, 0.58f, 4.5f }, { 0.85f, 0.68f, 4.0f }, { 0.35f, 0.80f, 4.0f },
            { 0.60f, 0.88f, 4.5f }, { 0.15f, 0.92f, 3.5f }, { 0.82f, 0.90f, 4.0f }
        };

        for (int i = 0; i < NUM_DOTS; i++) {
            dots[i].u = dotSpecs[i].u;
            dots[i].v = dotSpecs[i].v;
            dots[i].r = dotSpecs[i].r;
            dots[i].phase = (float)i * 0.9f;
            dots[i].speedMul = 0.7f + (float)(i % 3) * 0.25f;
        }

        buildRibbonPath(FRAME_W, FRAME_H);

        // 3. 리본 픽셀 Sparse LUT 메모리 할당 (PSRAM) 및 사전 베이킹
        if (!ribbonPixels) {
            ribbonPixels = (RibbonPixel*)PFMem::allocFloats((sizeof(RibbonPixel) * MAX_RIBBON_PIXELS + sizeof(float) - 1) / sizeof(float));
        }

        if (ribbonPixels) {
            ribbonPixelCount = 0;
            constexpr float halfWidth = 8.0f;

            for (int y = 0; y < FRAME_H; y++) {
                for (int x = 0; x < FRAME_W; x++) {
                    float minDistSq = 1e9f;
                    float bestDist = 0.0f;
                    float bestAlong = 0.0f;
                    float bestAcross = 0.0f;
                    bool hit = false;

                    for (int i = 0; i < numSegments; i++) {
                        const Segment& seg = segments[i];
                        if (x < seg.minX || x > seg.maxX || y < seg.minY || y > seg.maxY) continue;

                        float px = (float)x - seg.ax;
                        float py = (float)y - seg.ay;
                        float proj = (px * seg.dx + py * seg.dy) * seg.invLenSq;
                        if (proj < 0.0f) proj = 0.0f;
                        else if (proj > 1.0f) proj = 1.0f;

                        float cx = seg.ax + proj * seg.dx;
                        float cy = seg.ay + proj * seg.dy;
                        float distSq = ((float)x - cx) * ((float)x - cx) + ((float)y - cy) * ((float)y - cy);

                        if (distSq < minDistSq) {
                            minDistSq = distSq;
                            bestDist = sqrtf(distSq);
                            bestAlong = seg.sA + proj * seg.len;
                            bestAcross = (px * seg.dy - py * seg.dx) / seg.len;
                            hit = true;
                        }
                    }

                    if (hit && bestDist <= halfWidth && ribbonPixelCount < MAX_RIBBON_PIXELS) {
                        ribbonPixels[ribbonPixelCount++] = {
                            (uint8_t)x, (uint8_t)y,
                            bestAlong, bestAcross, bestDist
                        };
                    }
                }
            }
        }
    }

    void update(float dt, const InputFrame& input) {
        paramSpeed += input.knobDeltas[0] * 0.083f;
        paramSpeed = fminf(fmaxf(paramSpeed, 1.0f), 5.0f);

        paramTwinkle += input.knobDeltas[1] * 0.206f;
        paramTwinkle = fminf(fmaxf(paramTwinkle, 0.1f), 10.0f);

        paramDiaWidth += input.knobDeltas[2] * 0.167f;
        paramDiaWidth = fminf(fmaxf(paramDiaWidth, 2.0f), 10.0f);

        paramDiaHeight += input.knobDeltas[3] * 0.021f;
        paramDiaHeight = fminf(fmaxf(paramDiaHeight, 0.0f), 1.0f);

        if (input.btnPressed[0]) {
            timeAcc = 0.0f;
        }
        if (!input.btnHeld[1]) {
            timeAcc += dt;
            constexpr float WRAP_PERIOD = 2000.0f * TWO_PI;
            if (timeAcc >= WRAP_PERIOD) {
                timeAcc = fmodf(timeAcc, WRAP_PERIOD);
            }
        }
    }

    void draw() {
        PFCanvas::setFrame(FRAME_W, FRAME_H);

        if (!ribbonPixels) {
            PFCanvas::present();
            return;
        }

        const float t = timeAcc;
        const float speed = paramSpeed;
        const float twinkleSpeed = paramTwinkle;
        const float mappedDiaW = 3.0f + paramDiaWidth * 2.8f;
        const float mappedDiaH = 4.0f + paramDiaHeight * 16.0f;
        const float diaW = fmaxf(2.0f, mappedDiaW);
        const float diaH = fmaxf(2.0f, mappedDiaH);

        // --- Pass 1: 배경 렌더링 (1D LUT 스캔라인) ---
        for (int y = 0; y < FRAME_H; y++) {
            int hx = hoodMaxX[y];
            for (int x = 0; x < hx; x++) {
                PFCanvas::setPixel(x, y, 0, 0, 0);
            }
            for (int x = hx; x < FRAME_W; x++) {
                PFCanvas::setPixel(x, y, 255, 255, 255);
            }
        }

        // --- Pass 1.5: 바운싱 도트 (바운딩 박스 스탬핑) ---
        for (int i = 0; i < NUM_DOTS; i++) {
            float cx = dots[i].u * (float)FRAME_W;
            float cy = dots[i].v * (float)FRAME_H + PFMath::fastSin(t * twinkleSpeed * 1.5f + dots[i].phase) * 2.5f * dots[i].speedMul;
            float r = dots[i].r;
            float rSq = r * r;

            int minX = (int)fmaxf(0.0f, floorf(cx - r));
            int maxX = (int)fminf((float)(FRAME_W - 1), ceilf(cx + r));
            int minY = (int)fmaxf(0.0f, floorf(cy - r));
            int maxY = (int)fminf((float)(FRAME_H - 1), ceilf(cy + r));

            for (int y = minY; y <= maxY; y++) {
                int hx = hoodMaxX[y];
                for (int x = minX; x <= maxX; x++) {
                    if (x >= hx) {
                        float ddx = (float)x - cx;
                        float ddy = (float)y - cy;
                        if (ddx * ddx + ddy * ddy <= rSq) {
                            PFCanvas::setPixel(x, y, 0, 0, 0);
                        }
                    }
                }
            }
        }

        // --- Pass 2: 별 (바운딩 박스 스탬핑) ---
        for (int i = 0; i < NUM_STARS; i++) {
            const Star& s = stars[i];
            float sx = s.u * (float)FRAME_W;
            float sy = s.v * (float)FRAME_H;
            float angle = s.angle + t * speed * s.rotSpeed * 2.0f;
            float twinkle = 0.35f + 0.65f * (0.5f + 0.5f * PFMath::fastSin(t * twinkleSpeed * s.twinkleMul * 2.0f + s.twinklePhase));
            float outerR = s.outerR;
            float innerR = outerR * 0.42f;
            float cosA = PFMath::fastCos(-angle);
            float sinA = PFMath::fastSin(-angle);

            int minX = (int)fmaxf(0.0f, floorf(sx - outerR));
            int maxX = (int)fminf((float)(FRAME_W - 1), ceilf(sx + outerR));
            int minY = (int)fmaxf(0.0f, floorf(sy - outerR));
            int maxY = (int)fminf((float)(FRAME_H - 1), ceilf(sy + outerR));

            uint8_t val = (uint8_t)fminf(255.0f, fmaxf(0.0f, 255.0f * twinkle + 0.5f));

            for (int y = minY; y <= maxY; y++) {
                for (int x = minX; x <= maxX; x++) {
                    float dx = (float)x - sx;
                    float dyy = (float)y - sy;
                    float rdx = dx * cosA - dyy * sinA;
                    float rdy = dx * sinA + dyy * cosA;
                    if (starMask(rdx, rdy, outerR, innerR)) {
                        PFCanvas::setPixel(x, y, val, val, val);
                    }
                }
            }
        }

        // --- Pass 3: 리본 (사전 계산된 LUT 다이렉트 렌더링) ---
        constexpr float halfWidth = 8.0f;
        const float snakeShift = t * speed * 4.0f;
        const float scale = diaW * diaH;
        const float invScale = 1.0f / scale;
        const float edgeThreshold = scale * 0.09f;

        for (int i = 0; i < ribbonPixelCount; i++) {
            const RibbonPixel& p = ribbonPixels[i];

            if (p.dist > halfWidth - 1.2f) {
                PFCanvas::setPixel(p.x, p.y, 0, 0, 0);
                continue;
            }

            float along = p.along + snakeShift;
            float across = p.across;

            float d1 = floatMod(along * diaW + across * diaH, scale);
            float d2 = floatMod(along * diaW - across * diaH, scale);

            if (d1 < edgeThreshold || d1 > scale - edgeThreshold ||
                d2 < edgeThreshold || d2 > scale - edgeThreshold) {
                PFCanvas::setPixel(p.x, p.y, 0, 0, 0);
            } else {
                int c1 = (int)floorf((along * diaW + across * diaH) * invScale);
                int c2 = (int)floorf((along * diaW - across * diaH) * invScale);

                if (((c1 + c2) % 2 + 2) % 2 == 0) {
                    PFCanvas::setPixel(p.x, p.y, PINK[0], PINK[1], PINK[2]);
                } else {
                    PFCanvas::setPixel(p.x, p.y, BLUE[0], BLUE[1], BLUE[2]);
                }
            }
        }

        PFCanvas::present();
    }

} // namespace StarlightJesterRibbon