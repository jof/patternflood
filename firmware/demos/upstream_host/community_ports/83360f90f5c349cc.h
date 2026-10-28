// ===== Patternflow pattern =====
// Title:    Moonwell
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/83360f90f5c349cc
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-28): the cave is widened, not scaled.
// The shaft, the sword, its spell ring, the pedestal and the waterline are the original's,
// pixel for pixel, re-centred on x = 64, and the wall faces either side of the shaft keep
// their exact shapes. The walls' outer, receding layers are drawn out from 16 columns a side
// to 48 (their shading falls off over the same span), and five columns of faceted crags a
// side fill them instead of two; the near and far columns keep the original's seeds, the
// three new ones get their own. The small cracks and facets are repeated further out, and the
// dark notches behind the walls' tops stay their own size at the frame's edges. The pool
// opens across the cave (about x = 17..113 at its widest, 35..93 at the foot, against the
// original's 8..57 and 22..45), between bigger shores with four crags a corner, and gains two
// small stones; it reflects the whole width. The original 23 surface ripples stay by the
// pedestal with 23 more across the pool, the dust in the shaft is joined by a sparser drift
// across the cave, and the pool's pulse ring spreads twice as wide. Palette, motion, timing,
// knobs and buttons are unchanged.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"
#include "src/core_mem.h"

namespace MoonwellPattern {

    const char* NAME = "Moonwell";
    const char* const KNOB_LABELS[4] = {"Moonlight", "Water", "Aperture", "Awakening"};
    constexpr bool ABSOLUTE_READY = true;

    constexpr int FRAME_W = 128;
    constexpr int FRAME_H = 128;
    constexpr int CX = 64;              // the shaft's axis (the original's 32)

    // Knob parameters
    static float kMoonlight = 0.260f;
    static float kWater     = 1.525f;
    static float kAperture  = 1.0f;
    static float kAwakening = 1.0f;

    // Animation & button state
    static float timeAcc = 0.0f;
    static float waterFlow = 0.0f;
    static float shift = 0.0f;
    static float drop = 0.0f;
    static float burst = 0.0f;
    static bool breathe = false;

    // Framebuffer-scale buffers (allocated via PFMem)
    static uint8_t* stoneMap = nullptr;
    static uint8_t* frameBuf = nullptr;

    // Fixed precomputed tables
    static uint8_t radialMap[42 * FRAME_W]; // y = 86..127
    static float wx[FRAME_W];
    static float wy[FRAME_H];
    static float ringLUT[180];
    static float shadeCol[FRAME_W];

    // Static color references
    static const uint8_t rockColors[8][3] = {
        {2, 5, 9}, {5, 11, 18}, {11, 23, 34}, {21, 38, 51},
        {33, 55, 70}, {48, 77, 90}, {72, 111, 121}, {119, 164, 161}
    };

    static const uint8_t lights[6][3] = {
        {55, 225, 255}, {197, 65, 255}, {255, 59, 24},
        {255, 205, 58}, {77, 255, 117}, {55, 225, 255}
    };

    static const uint8_t gemColors[8][3] = {
        {0, 0, 0}, {5, 12, 19}, {13, 28, 37}, {25, 47, 58},
        {42, 70, 80}, {67, 107, 115}, {104, 146, 140}, {170, 197, 139}
    };

    static const char* const pedestal[16] = {
        "............77777..............",
        "..........776566777.............",
        ".........76554555667............",
        ".......776545334555667..........",
        "......76554322334456667.........",
        "....776544332223344455667.......",
        "...76543211332233444555667......",
        "..7654321112332233445554467.....",
        ".654321111122332233444433467....",
        "65432111111122332233443333467...",
        "543211122111122332223332223456..",
        "4321123442111122332222332223456.",
        "3211235543211112233222233222345.",
        "211234443221111122333223322234..",
        ".1234433221111112223333222233...",
        "..22332211111111122223332222...."
    };

    static inline float hashN(uint32_t n) {
        n = (n ^ 0x9e3779b9u) * 0x85ebca6bu;
        n ^= (n >> 13);
        return (float)n * (1.0f / 4294967296.0f);
    }

    static inline void putPixel(int x, int y, float r, float g, float b) {
        if (x < 0 || x >= FRAME_W || y < 0 || y >= FRAME_H) return;
        int idx = (y * FRAME_W + x) * 3;
        frameBuf[idx + 0] = (uint8_t)PFMath::clamp(r, 0.0f, 255.0f);
        frameBuf[idx + 1] = (uint8_t)PFMath::clamp(g, 0.0f, 255.0f);
        frameBuf[idx + 2] = (uint8_t)PFMath::clamp(b, 0.0f, 255.0f);
    }

    static inline void rectFill(int x, int y, int w, int h, float r, float g, float b) {
        int x0 = x < 0 ? 0 : x;
        int x1 = (x + w) > FRAME_W ? FRAME_W : (x + w);
        int y0 = y < 0 ? 0 : y;
        int y1 = (y + h) > FRAME_H ? FRAME_H : (y + h);
        if (x0 >= x1 || y0 >= y1) return;

        uint8_t ur = (uint8_t)PFMath::clamp(r, 0.0f, 255.0f);
        uint8_t ug = (uint8_t)PFMath::clamp(g, 0.0f, 255.0f);
        uint8_t ub = (uint8_t)PFMath::clamp(b, 0.0f, 255.0f);

        for (int yy = y0; yy < y1; ++yy) {
            int rowIdx = (yy * FRAME_W + x0) * 3;
            for (int xx = x0; xx < x1; ++xx) {
                frameBuf[rowIdx + 0] = ur;
                frameBuf[rowIdx + 1] = ug;
                frameBuf[rowIdx + 2] = ub;
                rowIdx += 3;
            }
        }
    }

    struct Pt {
        int x, y;
    };

    // The original's 64-wide geometry onto the square: the middle 32 columns (the shaft and the
    // wall faces either side of it) keep their size, re-centred on x = 64; the outer 16 columns
    // a side, the receding wall, are drawn out to 48, where more crags fill them.
    static int wideX(int x) {
        int d = x - 32;
        int ad = d < 0 ? -d : d;
        int ad2 = ad <= 16 ? ad : 16 + (ad - 16) * 3;
        return CX + (d < 0 ? -ad2 : ad2);
    }
    // ...and back, as a fractional original distance from the axis (for the wall's shading).
    static float origDist(int x) {
        float ad = fabsf((float)x + 0.5f - (float)CX) - 0.5f;
        if (ad < 0.0f) ad = 0.0f;
        return ad <= 16.0f ? ad : 16.0f + (ad - 16.0f) * (1.0f / 3.0f);
    }

    static void polygonFill(const Pt* points, int count, uint8_t c) {
        int lo = FRAME_H, hi = 0;
        for (int i = 0; i < count; ++i) {
            if (points[i].y < lo) lo = points[i].y;
            if (points[i].y > hi) hi = points[i].y;
        }
        int y0 = lo < 0 ? 0 : lo;
        int y1 = hi > FRAME_H ? FRAME_H : hi;

        for (int y = y0; y < y1; ++y) {
            float xs[16];
            int xCount = 0;
            for (int i = 0; i < count; ++i) {
                Pt a = points[i];
                Pt b = points[(i + 1) % count];
                if ((a.y <= y && b.y > y) || (b.y <= y && a.y > y)) {
                    float xIntersect = (float)a.x + (float)(y - a.y) * (float)(b.x - a.x) / (float)(b.y - a.y);
                    if (xCount < 16) {
                        xs[xCount++] = xIntersect;
                    }
                }
            }
            // Sort intersection x coordinates
            for (int i = 0; i < xCount - 1; ++i) {
                for (int j = i + 1; j < xCount; ++j) {
                    if (xs[i] > xs[j]) {
                        float tmp = xs[i];
                        xs[i] = xs[j];
                        xs[j] = tmp;
                    }
                }
            }
            for (int i = 0; i + 1 < xCount; i += 2) {
                int startX = (int)ceilf(xs[i]);
                int endX = (int)ceilf(xs[i + 1]);
                if (startX < 0) startX = 0;
                if (endX > FRAME_W) endX = FRAME_W;
                for (int x = startX; x < endX; ++x) {
                    stoneMap[y * FRAME_W + x] = c;
                }
            }
        }
    }

    static void seamDraw(const Pt* points, int count, uint8_t c) {
        for (int i = 0; i < count - 1; ++i) {
            Pt a = points[i];
            Pt b = points[i + 1];
            int n = abs(b.x - a.x) > abs(b.y - a.y) ? abs(b.x - a.x) : abs(b.y - a.y);
            if (n == 0) n = 1;
            for (int s = 0; s <= n; ++s) {
                int x = (int)roundf((float)a.x + (float)(b.x - a.x) * (float)s / (float)n);
                int y = (int)roundf((float)a.y + (float)(b.y - a.y) * (float)s / (float)n);
                if (x >= 0 && x < FRAME_W && y >= 0 && y < FRAME_H) {
                    stoneMap[y * FRAME_W + x] = c;
                }
            }
        }
    }

    // A wall layer or long seam from the original, every vertex drawn out with wideX.
    static void fillWide(const Pt* p, int n, uint8_t c) {
        Pt q[16];
        for (int i = 0; i < n; ++i) q[i] = Pt{wideX(p[i].x), p[i].y};
        polygonFill(q, n, c);
    }
    static void seamWide(const Pt* p, int n, uint8_t c) {
        Pt q[16];
        for (int i = 0; i < n; ++i) q[i] = Pt{wideX(p[i].x), p[i].y};
        seamDraw(q, n, c);
    }
    // A small facet or crack from the original, kept its size and moved to where wideX puts it;
    // `more` shifts it further along the wall (its copies in the widened part).
    static void fillMoved(const Pt* p, int n, uint8_t c, int more) {
        Pt q[16];
        int dx = wideX(p[0].x) - p[0].x + more;
        for (int i = 0; i < n; ++i) q[i] = Pt{p[i].x + dx, p[i].y};
        polygonFill(q, n, c);
    }
    static void seamMoved(const Pt* p, int n, uint8_t c, int more) {
        Pt q[16];
        int dx = wideX(p[0].x) - p[0].x + more;
        for (int i = 0; i < n; ++i) q[i] = Pt{p[i].x + dx, p[i].y};
        seamDraw(q, n, c);
    }

    static void cragDraw(float cx, float cy, float w, float h, float flip) {
        float shear = hashN((uint32_t)roundf(cx * 7.0f + cy * 13.0f)) * 0.8f - 0.4f;
        auto P = [cx, cy, w, h, flip, shear](float px, float py) -> Pt {
            return Pt{
                (int)roundf(cx + (px + py * shear) * w * flip),
                (int)roundf(cy + py * h)
            };
        };

        Pt poly1[6] = { P(-0.5f, -0.35f), P(-0.18f, -0.55f), P(0.35f, -0.43f), P(0.51f, 0.03f), P(0.19f, 0.5f), P(-0.34f, 0.42f) };
        polygonFill(poly1, 6, 2);

        Pt poly2[5] = { P(-0.5f, -0.35f), P(-0.18f, -0.55f), P(0.13f, -0.20f), P(-0.16f, 0.12f), P(-0.34f, 0.42f) };
        polygonFill(poly2, 5, 5);

        Pt poly3[3] = { P(-0.18f, -0.55f), P(0.35f, -0.43f), P(0.13f, -0.20f) };
        polygonFill(poly3, 3, 7);

        Pt poly4[5] = { P(0.13f, -0.20f), P(0.35f, -0.43f), P(0.51f, 0.03f), P(0.19f, 0.5f), P(-0.16f, 0.12f) };
        polygonFill(poly4, 5, 3);

        Pt poly5[4] = { P(0.13f, -0.20f), P(0.37f, 0.03f), P(0.19f, 0.5f), P(-0.03f, 0.21f) };
        polygonFill(poly5, 4, 4);

        Pt seam1[3] = { P(-0.48f, -0.32f), P(-0.18f, -0.49f), P(0.12f, -0.23f) };
        seamDraw(seam1, 3, 6);

        Pt seam2[4] = { P(-0.28f, 0.41f), P(-0.08f, 0.18f), P(0.11f, 0.16f), P(0.22f, 0.01f) };
        seamDraw(seam2, 4, 1);
    }

    void setup() {
        PFMath::buildSinLUT();

        if (!stoneMap) {
            float* mem = PFMem::allocFloats((FRAME_W * FRAME_H + sizeof(float) - 1) / sizeof(float));
            stoneMap = reinterpret_cast<uint8_t*>(mem);
        }
        if (!frameBuf) {
            float* mem = PFMem::allocFloats((FRAME_W * FRAME_H * 3 + sizeof(float) - 1) / sizeof(float));
            frameBuf = reinterpret_cast<uint8_t*>(mem);
        }

        if (stoneMap) {
            memset(stoneMap, 0, FRAME_W * FRAME_H);

            // The wall's layers, as the original drew them, drawn out across the wider cave
            const Pt p1[10] = {{0,0},{29,0},{21,14},{20,26},{17,34},{19,43},{17,62},{21,73},{23,87},{0,99}};
            fillWide(p1, 10, 3);
            const Pt p2[10] = {{64,0},{39,0},{43,12},{44,25},{48,35},{46,46},{48,61},{45,74},{44,91},{64,101}};
            fillWide(p2, 10, 3);
            const Pt p3[10] = {{0,0},{23,0},{18,15},{19,23},{13,35},{15,47},{12,58},{17,70},{15,89},{0,102}};
            fillWide(p3, 10, 2);
            const Pt p4[9]  = {{64,0},{44,0},{49,18},{48,29},{53,41},{49,52},{53,64},{50,83},{64,101}};
            fillWide(p4, 9, 2);
            const Pt p5[11] = {{0,0},{17,0},{12,13},{13,23},{8,32},{10,44},{6,55},{11,69},{8,80},{11,94},{0,110}};
            fillWide(p5, 11, 1);
            const Pt p6[10] = {{64,0},{51,0},{52,11},{57,23},{55,35},{60,46},{55,61},{57,76},{54,90},{64,107}};
            fillWide(p6, 10, 1);
            // The dark notches behind the walls' tops stay their own size, at the frame's edges
            const Pt p7[7]  = {{0,0},{11,0},{7,15},{8,27},{3,38},{5,49},{0,59}};
            polygonFill(p7, 7, 0);
            const Pt p8[6]  = {{128,0},{123,0},{122,17},{127,30},{124,44},{128,56}};
            polygonFill(p8, 6, 0);

            const Pt s1[5] = {{23,0},{18,15},{19,23},{13,35},{15,47}};
            seamWide(s1, 5, 4);
            const Pt s2[5] = {{8,45},{6,55},{11,69},{8,80},{11,94}};
            seamWide(s2, 5, 4);
            const Pt s3[3] = {{13,57},{17,70},{15,82}};
            seamWide(s3, 3, 5);
            const Pt s4[4] = {{43,12},{44,25},{48,35},{46,46}};
            seamWide(s4, 4, 4);
            const Pt s5[5] = {{53,52},{50,59},{53,64},{50,83},{54,91}};
            seamWide(s5, 5, 5);

            // Short cracks and small facets: the original's, then their kin further out
            for (int k = 0; k < 2; ++k) {
                int L = k ? -21 : 0, R = k ? 21 : 0;
                int o = k ? 9 : 0;          // the copies sit a little lower
                const Pt s6[3] = {{5,5+o},{3,18+o},{5,22+o}}; seamMoved(s6, 3, 2, 0);
                const Pt s7[3] = {{56,6+o},{58,16+o},{56,22+o}}; seamMoved(s7, 3, 3, k ? -12 : 0);
                const Pt s8[3] = {{15,3+o},{12,13+o},{13,19+o}}; seamMoved(s8, 3, 3, L);
                const Pt s9[3] = {{61,37+o},{59,45+o},{61,50+o}}; seamMoved(s9, 3, 3, k ? -14 : 0);
                const Pt s10[3] = {{2,72-o},{7,73-o},{9,83-o}}; seamMoved(s10, 3, 5, k ? 14 : 0);
                const Pt s11[3] = {{61,76-o},{57,77-o},{53,88-o}}; seamMoved(s11, 3, 6, k ? -10 : 0);
                const Pt s12[3] = {{18,66+o},{20,73+o},{22,82+o}}; seamMoved(s12, 3, 4, L);

                const Pt p9[5]  = {{16,32+o},{19,25+o},{18,41+o},{16,47+o},{16,39+o}}; fillMoved(p9, 5, 3, L);
                const Pt p10[5] = {{12,51-o},{14,47-o},{16,60-o},{15,67-o},{14,57-o}}; fillMoved(p10, 5, 3, L);
                const Pt p11[4] = {{8,17+o},{10,9+o},{9,29+o},{7,34+o}}; fillMoved(p11, 4, 2, k ? 12 : 0);
                const Pt p12[4] = {{46,39+o},{49,32+o},{48,47+o},{45,57+o}}; fillMoved(p12, 4, 4, R);
                const Pt p13[5] = {{54,64-o},{56,57-o},{55,76-o},{51,87-o},{52,77-o}}; fillMoved(p13, 5, 3, R);
                const Pt p14[4] = {{11,76},{14,79},{18,91},{15,90}}; fillMoved(p14, 4, 4, k ? -16 : 0);
            }

            for (int y = 11; y < 83; y += 7) {
                for (int x = 4; x < FRAME_W - 4; ++x) {
                    uint8_t s = stoneMap[y * FRAME_W + x];
                    int hx = x >= 32 && x < 96 ? x - 32 : x + 64;
                    if (s >= 2 && s <= 4 && hashN((uint32_t)((hx / 3) * 91 + y * 3)) > 0.77f) {
                        stoneMap[y * FRAME_W + x] = s - 1;
                    }
                }
            }

            // The shores, drawn round a pool that opens across the cave
            const Pt sh1[7] = {{0,94},{14,99},{18,106},{27,109},{33,118},{35,128},{0,128}};
            polygonFill(sh1, 7, 1);
            const Pt sh2[7] = {{128,96},{114,99},{110,109},{100,114},{94,121},{93,128},{128,128}};
            polygonFill(sh2, 7, 1);
            seamDraw(sh1, 6, 4);
            seamDraw(sh2, 5, 3);

            // Copy silhouette to mask out crags later
            static uint8_t silhouette[FRAME_W * FRAME_H];
            memcpy(silhouette, stoneMap, FRAME_W * FRAME_H);

            // The original's two columns of crags a side, at their places, and three more
            // between and beyond them; the near column and the far one keep the original's seeds
            for (int side = 0; side < 2; ++side) {
                float flip = side ? -1.0f : 1.0f;
                for (int row = 0; row < 7; ++row) {
                    float yy = 3.0f + (float)row * 14.0f + hashN((uint32_t)(row * 51 + side * 87)) * 9.0f;
                    for (int col = 0; col < 5; ++col) {
                        float d = 19.0f + (float)col * 10.0f;
                        float x = side ? (float)CX + d : (float)CX - d;
                        if (col == 0) {
                            cragDraw(x + (hashN((uint32_t)(row * 7 + side)) * 6.0f - 3.0f) * flip, yy,
                                     7.0f + hashN((uint32_t)(row * 37 + side)) * 9.0f,
                                     15.0f + hashN((uint32_t)(row * 53 + side)) * 18.0f, flip);
                        } else if (col == 3) {
                            cragDraw(x, yy + 7.0f,
                                     8.0f + hashN((uint32_t)(row * 13 + side)) * 7.0f,
                                     17.0f + hashN((uint32_t)(row * 9 + side)) * 12.0f, flip);
                        } else {
                            uint32_t k = (uint32_t)(col * 1009 + row * 131 + side * 17);
                            float jit = hashN(k + 5) * 6.0f - 3.0f;
                            float yj = (col & 1) ? 7.0f : hashN(k + 7) * 4.0f - 2.0f;
                            cragDraw(x + jit * flip, yy + yj,
                                     7.0f + hashN(k + 11) * 9.0f,
                                     15.0f + hashN(k + 13) * 17.0f, flip);
                        }
                    }
                }
                float sx = side ? 1.0f : 0.0f;
                auto X = [sx](float x) { return sx > 0.5f ? 128.0f - x : x; };
                cragDraw(X(24.0f), 106.0f, 17.0f, 22.0f, flip);
                cragDraw(X(8.0f), 102.0f, 15.0f, 20.0f, flip);
                cragDraw(X(12.0f), 124.0f, 22.0f, 25.0f, flip);
                cragDraw(X(31.0f), 126.0f, 24.0f, 27.0f, flip);
            }

            for (int i = 0; i < FRAME_W * FRAME_H; ++i) {
                if (!silhouette[i]) stoneMap[i] = 0;
            }
        }

        for (int y = 86; y < FRAME_H; ++y) {
            for (int x = 0; x < FRAME_W; ++x) {
                float dx = (float)(x - CX);
                float dy = (float)(y - 87);
                int r = (int)roundf(sqrtf(dx * dx * 0.7f + dy * dy * 4.0f));
                radialMap[(y - 86) * FRAME_W + x] = (uint8_t)(r > 179 ? 179 : r);
            }
        }

        // The wall darkens away from the light as the original's did across its 64 columns
        for (int x = 0; x < FRAME_W; ++x) {
            shadeCol[x] = 0.3f + PFMath::clamp01(1.0f - origDist(x) * (1.0f / 32.0f)) * 0.7f;
        }
    }

    void update(float dt, const InputFrame& input) {
        if (!stoneMap || !frameBuf) return;

        dt = PFMath::clamp(dt, 0.0f, 0.05f);

        PFParams::applyUnit(input, 0, &kMoonlight, 0.021f);
        PFParams::apply(input, 1, &kWater, 0.0f, 4.0f, 0.083f);
        PFParams::apply(input, 2, &kAperture, 0.0f, 1.0f, 0.021f);
        PFParams::apply(input, 3, &kAwakening, 0.0f, 1.0f, 0.021f);

        timeAcc += dt;
        if (timeAcc > 720.0f * PI) {
            timeAcc -= 720.0f * PI;
        }

        waterFlow += dt * kWater;
        if (waterFlow > 10000.0f) {
            waterFlow = PFMath::jsMod(waterFlow, 720.0f * PI);
        }

        drop = PFMath::clamp01(drop - dt * 0.55f);
        burst = PFMath::clamp01(burst - dt * 0.45f);

        if (input.btnPressed[0] && !input.paramAbsoluteActive[0] && !input.knobAudioActive[0]) {
            shift = PFMath::fract(shift + 0.2f);
        }
        if (input.btnPressed[1] && !input.paramAbsoluteActive[1] && !input.knobAudioActive[1]) {
            drop = 1.0f;
        }
        if (input.btnPressed[2] && !input.paramAbsoluteActive[2] && !input.knobAudioActive[2]) {
            breathe = !breathe;
        }
        if (input.btnPressed[3] && !input.paramAbsoluteActive[3] && !input.knobAudioActive[3]) {
            burst = 1.0f;
        }
    }

    void draw() {
        PFCanvas::setFrame(FRAME_W, FRAME_H);

        if (!stoneMap || !frameBuf) {
            PFCanvas::present();
            return;
        }

        float t = timeAcc;
        float flow = waterFlow;
        float awake = PFMath::clamp01(kAwakening + burst);

        // Light color interpolation
        float hue = PFMath::fract(kMoonlight + shift) * 5.0f;
        int si = PFMath::ifloor(hue);
        if (si > 4) si = 4;
        float mix = hue - (float)si;

        const uint8_t* lA = lights[si];
        const uint8_t* lB = lights[si + 1];
        float lr = (float)lA[0] + ((float)lB[0] - (float)lA[0]) * mix;
        float lg = (float)lA[1] + ((float)lB[1] - (float)lA[1]) * mix;
        float lb = (float)lA[2] + ((float)lB[2] - (float)lA[2]) * mix;

        float opening = kAperture * kAperture;
        float breath = breathe ? (0.80f + PFMath::fastSin(t * 0.85f) * 0.20f) : 1.0f;
        float sway = PFMath::fastSin(t * 0.23f) * 0.7f;
        float sinT055 = PFMath::fastSin(t * 0.55f);
        float tint = 0.18f + opening * 0.8f + awake * 0.25f;
        float kr = (lr / 190.0f) * (1.0f + tint) + 0.3f;
        float kg = (lg / 230.0f) * (1.0f + tint) + 0.3f;
        float kb = (lb / 255.0f) * (1.0f + tint) + 0.3f;

        // 1. Upper cavern & illuminated rock face (y = 0..87)
        for (int y = 0; y < 88; ++y) {
            float yNorm = (float)y * (1.0f / 88.0f);
            float center = (float)CX + sway * yNorm + sinT055 * opening * 7.0f * yNorm;
            float halfW = 1.5f + opening * 13.0f + (float)y * (0.018f + opening * 0.29f);
            float invHalfW = 1.0f / halfW;
            float vertical = PFMath::clamp(1.0f - (float)y * 0.0068f, 0.20f, 1.0f) * breath;

            float streakA = (float)(CX - 3) + PFMath::fastSin(t * 0.37f + (float)y * 0.035f) * 2.0f;
            float streakB = (float)(CX + 3) + PFMath::fastSin(t * 0.29f + (float)y * 0.025f);

            int rowOffset = y * FRAME_W;
            for (int x = 0; x < FRAME_W; ++x) {
                uint8_t st = stoneMap[rowOffset + x];
                const uint8_t* c = rockColors[st];

                float d = fabsf((float)x - center);
                float cone = 1.0f - d * invHalfW;
                if (cone < 0.0f) cone = 0.0f;

                float ripple = (fabsf((float)x - streakA) < 1.5f ? 0.09f : 0.0f) +
                               (fabsf((float)x - streakB) < 1.0f ? 0.06f : 0.0f);

                float v = (cone * cone * (0.30f + opening) + cone * 0.12f + ripple * cone) * vertical;
                if (st > 0) v *= (0.22f + opening * 0.8f);

                // Skylight aperture cap
                if (y < 16 && st == 0) {
                    float capLimit = (y < 5) ? ((float)y * 0.9f) : (7.0f - (float)(y - 5) * 0.43f);
                    if (d < capLimit) {
                        putPixel(x, y, 192.0f + lr * 0.23f, 192.0f + lg * 0.23f, 192.0f + lb * 0.23f);
                        continue;
                    }
                }

                float rim = (st >= 4) ? (0.05f * vertical) : 0.0f;
                float shade = st ? shadeCol[x] : 1.0f;

                float pr = (float)c[0] * shade * kr + lr * (v + rim);
                float pg = (float)c[1] * shade * kg + lg * (v + rim);
                float pb = (float)c[2] * shade * kb + lb * (v + rim);

                putPixel(x, y, pr, pg, pb);
            }
        }

        // 2. Floating dust motes inside shaft
        int dustCount = 10 + PFMath::ifloor(awake * 45.0f);
        for (int i = 0; i < dustCount; ++i) {
            float yF = 17.0f + PFMath::jsMod(
                PFMath::jsMod(hashN((uint32_t)(i * 19 + 3)) * 67.0f - t * (0.55f + hashN((uint32_t)i) * 1.1f), 67.0f) + 67.0f,
                67.0f
            );
            int y = PFMath::ifloor(yF);
            int x = PFMath::ifloor((float)(CX - 9) + hashN((uint32_t)(i * 71)) * 19.0f + PFMath::fastSin(t * 0.4f + (float)i) * 1.1f);
            float v = (i % 5 == 0) ? 0.85f : 0.35f;

            putPixel(x, y, lr * v, lg * v, lb * v);
            if ((i % 8 == 0) && (awake > 0.6f)) {
                putPixel(x - 1, y, lr * 0.3f, lg * 0.3f, lb * 0.3f);
                putPixel(x, y - 1, 150.0f, 225.0f, 239.0f);
            }
        }
        // ...and more of it adrift across the wider cave, in front of the walls
        int driftCount = 8 + PFMath::ifloor(awake * 34.0f);
        for (int i = 0; i < driftCount; ++i) {
            uint32_t k = (uint32_t)(i + 400);
            float yF = 8.0f + PFMath::jsMod(
                PFMath::jsMod(hashN(k * 19 + 3) * 78.0f - t * (0.45f + hashN(k) * 0.9f), 78.0f) + 78.0f,
                78.0f
            );
            int y = PFMath::ifloor(yF);
            int x = PFMath::ifloor(6.0f + hashN(k * 71) * 116.0f + PFMath::fastSin(t * 0.4f + (float)i) * 1.1f);
            float v = (i % 5 == 0) ? 0.70f : 0.28f;

            putPixel(x, y, lr * v, lg * v, lb * v);
            if ((i % 8 == 0) && (awake > 0.6f)) {
                putPixel(x - 1, y, lr * 0.3f, lg * 0.3f, lb * 0.3f);
                putPixel(x, y - 1, 150.0f, 225.0f, 239.0f);
            }
        }

        // 3. Floating blade & hilt
        int lift = (int)roundf(awake * 30.0f + PFMath::fastSin(t * 2.0f) * awake * 3.0f);
        int sy = 80 - lift;
        constexpr int O = CX - 32;      // the sword, pedestal and stones move with the axis

        rectFill(O + 30, sy - 10, 5, 12, lr * 0.2f, lg * 0.2f, lb * 0.2f);
        rectFill(O + 31, sy - 10, 3, 12, lr * 0.64f, lg * 0.84f, lb * 0.84f);
        rectFill(O + 31, sy - 10, 1, 12, 210.0f, 255.0f, 255.0f);
        rectFill(O + 32, sy - 10, 1, 12, 241.0f, 255.0f, 243.0f);
        putPixel(O + 32, sy + 2, 195.0f, 250.0f, 255.0f);

        rectFill(O + 27, sy - 12, 11, 1, 255.0f, 227.0f, 137.0f);
        rectFill(O + 28, sy - 11, 9, 1, 133.0f, 99.0f, 45.0f);
        putPixel(O + 27, sy - 11, 241.0f, 229.0f, 166.0f);
        putPixel(O + 37, sy - 11, 241.0f, 229.0f, 166.0f);

        rectFill(O + 31, sy - 17, 3, 5, 13.0f, 24.0f, 30.0f);
        rectFill(O + 32, sy - 17, 1, 5, 154.0f, 154.0f, 109.0f);
        putPixel(O + 32, sy - 16, 28.0f, 37.0f, 36.0f);
        putPixel(O + 32, sy - 14, 28.0f, 37.0f, 36.0f);
        putPixel(O + 31, sy - 15, 99.0f, 154.0f, 158.0f);
        putPixel(O + 31, sy - 13, 99.0f, 154.0f, 158.0f);

        rectFill(O + 31, sy - 19, 3, 2, 255.0f, 230.0f, 147.0f);
        putPixel(O + 32, sy - 19, 248.0f, 255.0f, 228.0f);
        putPixel(O + 32, sy - 12, 23.0f, 107.0f, 165.0f);
        putPixel(O + 32, sy - 11, 173.0f, 241.0f, 255.0f);

        // Spell ring & blade energy
        if (awake > 0.15f) {
            float radX = 6.0f + awake * 15.0f;
            float radY = 3.0f + awake * 13.0f;
            for (int i = 0; i < 32; ++i) {
                float angle = t * (0.5f + awake * 2.0f) + (float)i * (PI / 16.0f);
                int xx = PFMath::ifloor((float)CX + PFMath::fastCos(angle) * radX + 0.5f);
                int yy = PFMath::ifloor((float)(sy - 5) + PFMath::fastSin(angle) * radY + 0.5f);
                if (((float)i * (1.0f / 32.0f)) > awake) continue;

                putPixel(xx, yy, lr, lg, lb);
                if (i % 4 == 0) {
                    putPixel(xx + 1, yy, 200.0f, 250.0f, 255.0f);
                    putPixel(xx, yy + 1, lr * 0.6f, lg * 0.6f, lb * 0.6f);
                }
            }

            if (awake > 0.4f) {
                for (int y = sy + 3; y < 82; ++y) {
                    int x = CX + (int)roundf(PFMath::fastSin((float)y * 0.63f - t * 6.0f) * awake * 4.0f);
                    putPixel(x, y, lr * 0.6f, lg * 0.6f, lb * 0.6f);
                    if (y % 3 == 0) {
                        putPixel(x + 1, y, 190.0f, 250.0f, 255.0f);
                    }
                }
            }
        }

        // 4. Wave displacements for reflection calculation
        for (int x = 0; x < FRAME_W; ++x) {
            float xo = (float)(x - O);  // the original's phases, about the axis
            wx[x] = PFMath::fastSin(xo * 0.33f + flow * 0.7f) +
                    PFMath::fastSin(xo * 0.71f - flow * 0.9f) * 0.45f;
        }
        for (int y = 86; y < FRAME_H; ++y) {
            wy[y] = PFMath::fastSin((float)y * 0.64f - flow * 2.0f) +
                    PFMath::fastSin((float)y * 0.27f + flow * 1.6f) * 0.6f;
        }
        for (int i = 0; i < 180; ++i) {
            ringLUT[i] = PFMath::fastSin((float)i * 0.56f - flow * 2.7f);
        }

        // 5. Water reflections (y = 88..127)
        float amplitude = kWater * kWater * 0.55f;
        for (int y = 88; y < FRAME_H; ++y) {
            float depth = (float)(y - 88) * (1.0f / 40.0f);
            float shiftScale = 0.1f + amplitude * (0.5f + depth);
            float baseSrcY = 85.0f - (float)(y - 88) * 0.7f;
            float invCenterDiv = 1.0f / (10.0f + depth * 7.0f);
            float invRibbonDiv = 1.0f / (1.6f + depth * 2.7f);

            int rowOffset = y * FRAME_W;
            int radRowOffset = (y - 86) * FRAME_W;

            for (int x = 0; x < FRAME_W; ++x) {
                uint8_t st = stoneMap[rowOffset + x];
                if (st) {
                    const uint8_t* c = rockColors[st];
                    putPixel(x, y,
                             (float)c[0] * (0.25f + lr * (1.0f / 900.0f)),
                             (float)c[1] * (0.25f + lg * (1.0f / 900.0f)),
                             (float)c[2] * (0.25f + lb * (1.0f / 900.0f)));
                    continue;
                }

                uint8_t rIdx = radialMap[radRowOffset + x];
                float wave = wy[y] + wx[x] * 0.6f + ringLUT[rIdx] * 0.6f;
                int shift = (int)roundf(wave * shiftScale);

                int srcY = (int)roundf(baseSrcY + wx[x] * amplitude * 0.3f);
                if (srcY < 0) srcY = 0;
                if (srcY > 87) srcY = 87;

                bool glint = (wave > 0.65f && wave < 1.17f);
                int sx = x + shift;
                if (sx < 0) sx = 0;
                if (sx >= FRAME_W) sx = FRAME_W - 1;

                int si = (srcY * FRAME_W + sx) * 3;
                float rr = (float)frameBuf[si + 0];
                float gg = (float)frameBuf[si + 1];
                float bb = (float)frameBuf[si + 2];

                float distCenter = fabsf((float)(x - CX - shift));
                float center = PFMath::clamp01(1.0f - distCenter * invCenterDiv);
                float ribbon = PFMath::clamp01(1.0f - distCenter * invRibbonDiv);

                float mod = glint ? 0.88f : 0.30f;
                float sheen = (glint ? 0.17f : 0.03f) * center + ribbon * (glint ? 0.60f : 0.07f);
                float foam = (wave > 0.87f && wave < 1.08f) ? (PFMath::clamp(kWater - 1.5f, 0.0f, 4.0f) * center * 0.20f) : 0.0f;
                float body = 0.014f + 0.012f * wx[x] * wy[y];

                float outR = 4.0f + rr * mod + lr * (sheen + body) + foam * 160.0f;
                float outG = 13.0f + gg * mod + lg * (sheen + body) + foam * 210.0f;
                float outB = 20.0f + bb * mod + lb * (sheen + body) + foam * 220.0f;

                putPixel(x, y, outR, outG, outB);
            }
        }

        // 6. Surface ripples: the original's 23 by the pedestal, and 23 more across the pool
        for (int i = 0; i < 46; ++i) {
            int y, x;
            if (i < 23) {
                y = 86 + PFMath::ifloor(hashN((uint32_t)(i * 31 + 8)) * 41.0f);
                x = O + 9 + PFMath::ifloor(hashN((uint32_t)(i * 59 + 7)) * 46.0f);
            } else {
                y = 88 + PFMath::ifloor(hashN((uint32_t)(i * 31 + 8)) * 30.0f);
                x = 8 + PFMath::ifloor(hashN((uint32_t)(i * 59 + 7)) * 108.0f);
            }
            int len = 2 + PFMath::ifloor(hashN((uint32_t)(i * 11)) * 7.0f);
            float v = 0.07f + 0.1f * (0.5f + 0.5f * PFMath::fastSin(flow * 1.1f + (float)i * 2.0f));

            for (int q = 0; q < len; ++q) {
                if ((x + q < FRAME_W) && !stoneMap[y * FRAME_W + x + q]) {
                    putPixel(x + q, y, lr * v, lg * v, lb * v);
                }
            }
        }

        // 7. Hand-composed pedestal facets
        for (int row = 0; row < 16; ++row) {
            const char* pLine = pedestal[row];
            for (int x = 0; pLine[x] != '\0'; ++x) {
                char ch = pLine[x];
                if (ch < '1' || ch > '7') continue;
                int sVal = ch - '0';
                int cIdx = sVal;
                if (sVal == 7 && row > 3) {
                    cIdx = (row % 3 == 0) ? 6 : 5;
                }
                const uint8_t* c = gemColors[cIdx];
                float v = awake * 0.18f + opening * 0.14f;
                putPixel(O + x + 17, 80 + row, (float)c[0] + lr * v, (float)c[1] + lg * v, (float)c[2] + lb * v);
            }
        }

        // 8. Satellite stones & waterline
        rectFill(O + 17, 89, 5, 3, 5.0f, 13.0f, 21.0f);
        rectFill(O + 18, 88, 3, 1, 86.0f, 139.0f, 145.0f);
        putPixel(O + 20, 89, 137.0f, 189.0f, 184.0f);

        rectFill(O + 43, 89, 5, 3, 6.0f, 17.0f, 26.0f);
        rectFill(O + 44, 88, 2, 1, 76.0f, 125.0f, 135.0f);

        // two more, smaller, out in the wider pool
        rectFill(26, 99, 4, 2, 5.0f, 13.0f, 21.0f);
        rectFill(27, 98, 2, 1, 76.0f, 125.0f, 135.0f);
        rectFill(98, 100, 5, 2, 6.0f, 17.0f, 26.0f);
        rectFill(99, 99, 3, 1, 86.0f, 139.0f, 145.0f);
        putPixel(101, 99, 137.0f, 189.0f, 184.0f);

        for (int x = 18; x < 48; ++x) {
            if (x < 24 || x > 40 || (x % 4 == 0)) {
                putPixel(O + x, 92, lr * 0.45f, lg * 0.60f, lb * 0.60f);
            }
        }

        // 9. Interactive water ripple pulse, out across the wider pool
        if (drop > 0.0f || burst > 0.0f) {
            float life = drop > burst ? drop : burst;
            float radius = (1.0f - life) * 25.0f + 3.0f;
            for (int i = 0; i < 96; ++i) {
                float angle = (float)i * (PI / 48.0f);
                int rx = (int)roundf((float)CX + PFMath::fastCos(angle) * radius * 2.0f);
                int ry = (int)roundf(94.0f + PFMath::fastSin(angle) * radius * 0.24f);
                putPixel(rx, ry, lr * life, lg * life, lb * life);
            }
        }

        // Output final framebuffer to panel canvas
        for (int y = 0; y < FRAME_H; ++y) {
            int rowIdx = y * FRAME_W * 3;
            for (int x = 0; x < FRAME_W; ++x) {
                PFCanvas::setPixel(x, y,
                                   frameBuf[rowIdx + 0],
                                   frameBuf[rowIdx + 1],
                                   frameBuf[rowIdx + 2]);
                rowIdx += 3;
            }
        }

        PFCanvas::present();
    }

} // namespace MoonwellPattern
