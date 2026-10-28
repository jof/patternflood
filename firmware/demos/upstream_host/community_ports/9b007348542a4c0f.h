// ===== Patternflow pattern =====
// Title:    Midnight Clocktower
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/9b007348542a4c0f
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-28): the tower already spans the full
// height, so it keeps its size and moves to the centre, and the world widens around it. The
// far town has 29 houses instead of 15, with two distant church spires in its greys; the
// foreground has ten rooftops instead of five and a second smoking chimney on the right;
// the sky has twice the stars, twelve clouds instead of six (each looping a wider sky), eight
// bats instead of four, and the moon sits a little further out, upper left. Zoom ends at
// seven times the scale, not 3.5, so the close-up clock face fills the square as it filled
// the narrow frame; the detail steps (ticks, numerals, second hand, pendulum, shingles)
// still come in at the same knob positions. Palette, motion, knobs and buttons are the
// original's.
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

namespace MidnightClocktower {

    const char* NAME = "Midnight Clocktower";
    const char* const KNOB_LABELS[4] = {"Zoom", "ClockSpeed", "Wind", "Light"};
    constexpr bool ABSOLUTE_READY = true;

    constexpr int FRAME_W = 128;
    constexpr int FRAME_H = 128;

    // Knob parameters & State
    static float rawZoom       = 1.0f;
    static float rawClockSpeed = 0.448f;
    static float rawWind       = 1.149f;
    static float rawLight      = 1.0f;

    static float prevRawZoom = 1.0f;
    static float zoom        = 1.0f;
    static float view        = 1.0f;   // the camera's scale: 1 at Zoom's floor, 7 at its top
    static float clockSpeed  = 0.448f;
    static float wind        = 1.149f;
    static float light       = 1.0f;

    static float hours     = 10.0f + 1.0f / 6.0f;
    static bool  autoClock = true;
    static bool  zoomHome  = false;
    static float gust      = 0.0f;
    static float beacon    = 0.0f;
    static float drift     = 0.0f;
    static float flow      = 0.18f;
    static float t         = 0.0f;
    static float cameraY   = 64.0f;

    struct Bird {
        float x;
        float y;
        float baseSpeed;
        float waveFreq;
        float waveAmp;
        float flapSpeed;
    };
    static Bird birds[8];

    // Color definitions
    struct ColorRGB {
        uint8_t r, g, b;
        constexpr ColorRGB(uint8_t r_, uint8_t g_, uint8_t b_) : r(r_), g(g_), b(b_) {}
    };

    static constexpr ColorRGB INK(0, 0, 0);
    static constexpr ColorRGB STONE(9, 9, 9);
    static constexpr ColorRGB SHADE(23, 23, 23);
    static constexpr ColorRGB EDGE(83, 83, 83);
    static constexpr ColorRGB SILVER(173, 173, 173);
    static constexpr ColorRGB WHITE(229, 229, 222);
    static constexpr ColorRGB GOLD(242, 146, 29);
    static constexpr ColorRGB WARM(255, 204, 76);

    inline ColorRGB grey(int n) {
        uint8_t val = (uint8_t)(n < 0 ? 0 : (n > 255 ? 255 : n));
        return ColorRGB(val, val, val);
    }

    // Framebuffer pointer (PSRAM-first)
    static uint8_t* rgbBuf = nullptr;

    inline void project(float x, float y, float depth, float& outX, float& outY) {
        float z  = 1.0f + (view - 1.0f) * depth;
        float cy = 64.0f + (cameraY - 64.0f) * depth;
        outX = 64.0f + (x - 32.0f) * z;
        outY = 64.0f + (y - cy) * z;
    }

    inline void setPixelRgb(int x, int y, ColorRGB c) {
        if (x < 0 || y < 0 || x >= FRAME_W || y >= FRAME_H) return;
        int idx = (y * FRAME_W + x) * 3;
        rgbBuf[idx]     = c.r;
        rgbBuf[idx + 1] = c.g;
        rgbBuf[idx + 2] = c.b;
    }

    void drawRect(float x, float y, float w, float h, ColorRGB c, float depth = 1.0f) {
        float ax, ay, bx, by;
        project(x, y, depth, ax, ay);
        project(x + w, y + h, depth, bx, by);
        int x0 = (int)fmaxf(0.0f, roundf(ax));
        int x1 = (int)fminf((float)FRAME_W, roundf(bx));
        int y0 = (int)fmaxf(0.0f, roundf(ay));
        int y1 = (int)fminf((float)FRAME_H, roundf(by));
        if (x0 > x1) { int tmp = x0; x0 = x1; x1 = tmp; }
        if (y0 > y1) { int tmp = y0; y0 = y1; y1 = tmp; }
        for (int yy = y0; yy < y1; ++yy) {
            for (int xx = x0; xx < x1; ++xx) {
                setPixelRgb(xx, yy, c);
            }
        }
    }

    void drawPoly(const float points[][2], int numPts, ColorRGB c, float depth = 1.0f) {
        if (numPts <= 0) return;
        float projPts[24][2];
        float minY = 9999.0f;
        float maxY = -9999.0f;
        for (int i = 0; i < numPts; ++i) {
            project(points[i][0], points[i][1], depth, projPts[i][0], projPts[i][1]);
            if (projPts[i][1] < minY) minY = projPts[i][1];
            if (projPts[i][1] > maxY) maxY = projPts[i][1];
        }

        int ymin = (int)fmaxf(0.0f, floorf(minY));
        int ymax = (int)fminf((float)FRAME_H, ceilf(maxY));

        for (int y = ymin; y < ymax; ++y) {
            float cy = (float)y + 0.5f;
            float hits[24];
            int hitCount = 0;

            for (int i = 0, j = numPts - 1; i < numPts; j = i++) {
                const float* a = projPts[i];
                const float* b = projPts[j];
                if ((a[1] > cy) != (b[1] > cy)) {
                    if (fabsf(b[1] - a[1]) > 1e-6f) {
                        float hx = a[0] + (cy - a[1]) * (b[0] - a[0]) / (b[1] - a[1]);
                        if (hitCount < 24) {
                            hits[hitCount++] = hx;
                        }
                    }
                }
            }

            for (int i = 1; i < hitCount; ++i) {
                float key = hits[i];
                int k = i - 1;
                while (k >= 0 && hits[k] > key) {
                    hits[k + 1] = hits[k];
                    k--;
                }
                hits[k + 1] = key;
            }

            for (int i = 0; i + 1 < hitCount; i += 2) {
                int xStart = (int)fmaxf(0.0f, ceilf(hits[i] - 0.5f));
                int xEnd   = (int)fminf((float)FRAME_W, ceilf(hits[i + 1] - 0.5f));
                for (int x = xStart; x < xEnd; ++x) {
                    setPixelRgb(x, y, c);
                }
            }
        }
    }

    void drawStroke(float x1, float y1, float x2, float y2, ColorRGB c, float width = 0.55f, float depth = 1.0f) {
        float ax, ay, bx, by;
        project(x1, y1, depth, ax, ay);
        project(x2, y2, depth, bx, by);
        float z = 1.0f + (view - 1.0f) * depth;
        int size = (int)fmaxf(1.0f, roundf(width * z));
        float ddx = bx - ax;
        float ddy = by - ay;
        int n = (int)fmaxf(1.0f, ceilf(sqrtf(ddx * ddx + ddy * ddy)));
        float invN = 1.0f / (float)n;
        int halfSize = size >> 1;

        for (int i = 0; i <= n; ++i) {
            float frac = (float)i * invN;
            int x = (int)roundf(ax + ddx * frac);
            int y = (int)roundf(ay + ddy * frac);
            for (int dy = 0; dy < size; ++dy) {
                for (int dx = 0; dx < size; ++dx) {
                    setPixelRgb(x + dx - halfSize, y + dy - halfSize, c);
                }
            }
        }
    }

    void drawEllipse(float x, float y, float rx, float ry, ColorRGB c, float depth = 1.0f) {
        float ax, ay;
        project(x, y, depth, ax, ay);
        float z = 1.0f + (view - 1.0f) * depth;
        rx *= z;
        ry *= z;
        if (rx <= 0.001f || ry <= 0.001f) return;

        int y0 = (int)fmaxf(0.0f, ceilf(ay - ry));
        int y1 = (int)fminf((float)(FRAME_H - 1), floorf(ay + ry));
        float invRy = 1.0f / ry;

        for (int yy = y0; yy <= y1; ++yy) {
            float v = ((float)yy - ay) * invRy;
            float v2 = v * v;
            if (v2 > 1.0f) continue;
            float span = rx * sqrtf(1.0f - v2);
            int x0 = (int)fmaxf(0.0f, ceilf(ax - span));
            int x1 = (int)fminf((float)(FRAME_W - 1), floorf(ax + span));
            for (int xx = x0; xx <= x1; ++xx) {
                setPixelRgb(xx, yy, c);
            }
        }
    }

    void drawArch(float x, float y, float w, float h, ColorRGB c, float depth = 1.0f) {
        float pts[7][2] = {
            {x,             y + h},
            {x,             y + w * 0.45f},
            {x + w * 0.23f, y + w * 0.14f},
            {x + w * 0.5f,  y},
            {x + w * 0.77f, y + w * 0.14f},
            {x + w,         y + w * 0.45f},
            {x + w,         y + h}
        };
        drawPoly(pts, 7, c, depth);
    }

    inline bool isLit(int id) {
        float threshold;
        if (id == 1 || id == 3 || id == 4) {
            threshold = 0.12f + (float)id * 0.025f;
        } else {
            threshold = PFNoise::cellHash(id + 41, 0) * 0.88f + 0.04f;
        }
        return (light > threshold) || (beacon > 1.0f);
    }

    void drawWindow(float x, float y, float w, float h, int id, float depth = 1.0f) {
        drawArch(x - 0.45f, y - 0.6f, w + 0.9f, h + 0.9f, EDGE, depth);
        drawArch(x, y, w, h, INK, depth);
        if (isLit(id)) {
            drawArch(x + 0.5f, y + 0.65f, w - 1.0f, h - 1.0f, GOLD, depth);
            drawRect(x + w * 0.52f, y + 1.3f, w * 0.19f, h - 1.8f, WARM, depth);
        } else if (zoom > 1.5f) {
            drawStroke(x + 0.5f, y + 1.2f, x + 0.5f, y + h - 1.0f, SHADE, 0.3f, depth);
        }
        drawStroke(x + w * 0.5f, y + 0.5f, x + w * 0.5f, y + h, INK, 0.42f, depth);
        drawStroke(x + 0.2f, y + h * 0.58f, x + w - 0.2f, y + h * 0.58f, INK, 0.45f, depth);
        drawRect(x - 0.6f, y + h, w + 1.2f, 0.55f, SILVER, depth);
    }

    void drawCloud(float x, float y, float size, int lightVal, float depth = 0.28f) {
        static const float outline[20][2] = {
            {-17,2},{-13,1},{-11,-1},{-8,0},{-7,-3},{-4,-2},{-3,-5},{0,-4},{2,-1},{5,-2},
            {7,0},{10,0},{12,2},{18,3},{11,4},{7,5},{1,4},{-3,6},{-8,5},{-12,3}
        };
        float pts[20][2];
        for (int i = 0; i < 20; ++i) {
            pts[i][0] = x + outline[i][0] * size;
            pts[i][1] = y + outline[i][1] * size;
        }
        drawPoly(pts, 20, grey(lightVal), depth);

        static const float ridge[9][2] = {
            {-15,2},{-10,1},{-8,-1},{-6,0},{-3,-3},{0,-2},{2,0},{6,0},{9,2}
        };
        for (int i = 1; i < 9; ++i) {
            drawStroke(x + ridge[i - 1][0] * size, y + ridge[i - 1][1] * size,
                       x + ridge[i][0]     * size, y + ridge[i][1]     * size,
                       grey(lightVal + 19), 0.45f, depth);
        }
    }

    struct Glyph {
        int width;
        uint8_t rows[5];
    };

    inline Glyph getGlyph(char ch) {
        if (ch == 'I') return {1, {1, 1, 1, 1, 1}};
        if (ch == 'V') return {3, {5, 5, 5, 5, 2}};
        if (ch == 'X') return {3, {5, 5, 2, 5, 5}};
        return {0, {0, 0, 0, 0, 0}};
    }

    void drawRoman(const char* text, float x, float y, float h, ColorRGB c) {
        int unit = (int)fmaxf(1.0f, roundf(h * view * 0.2f));
        int sumLen = -1;
        for (int idx = 0; text[idx] != '\0'; ++idx) {
            sumLen += getGlyph(text[idx]).width + 1;
        }
        float total = (float)(sumLen * unit);

        float atX, atY;
        project(x, y + h * 0.5f, 1.0f, atX, atY);
        int left = (int)roundf(atX - total * 0.5f);
        int top  = (int)roundf(atY - 2.5f * (float)unit);

        for (int idx = 0; text[idx] != '\0'; ++idx) {
            Glyph g = getGlyph(text[idx]);
            for (int r = 0; r < 5; ++r) {
                for (int col = 0; col < g.width; ++col) {
                    if ((g.rows[r] >> (g.width - 1 - col)) & 1) {
                        for (int yy = 0; yy < unit; ++yy) {
                            for (int xx = 0; xx < unit; ++xx) {
                                setPixelRgb(left + col * unit + xx, top + r * unit + yy, c);
                            }
                        }
                    }
                }
            }
            left += (g.width + 1) * unit;
        }
    }

    void drawHand(float a, float length, float width, ColorRGB c) {
        float dx = PFMath::fastCos(a);
        float dy = PFMath::fastSin(a);
        float nx = -dy * width;
        float ny =  dx * width;
        float pts[3][2] = {
            {32.0f - dx * 0.8f + nx, 53.0f - dy * 0.8f + ny},
            {32.0f + dx * length,    53.0f + dy * length},
            {32.0f - dx * 0.8f - nx, 53.0f - dy * 0.8f - ny}
        };
        drawPoly(pts, 3, c, 1.0f);
        drawStroke(32.0f, 53.0f, 32.0f + dx * length, 53.0f + dy * length, c, 0.4f, 1.0f);
    }

    constexpr float MOON_X = -4.0f;

    // A far church in the town's own greys, for the wider skyline: nave, steeple, lit slits.
    void drawSpire(float x, float top, float base, int id) {
        const float d = 0.42f;
        drawRect(x - 2.4f, top + 11.0f, 4.8f, base - top - 11.0f, grey(20), d);
        float pts[3][2] = {{x - 3.0f, top + 11.0f}, {x, top}, {x + 3.0f, top + 11.0f}};
        drawPoly(pts, 3, grey(35), d);
        drawStroke(x - 3.0f, top + 11.0f, x, top, EDGE, 0.35f, d);
        drawRect(x - 3.2f, top + 11.0f, 6.4f, 0.6f, grey(35), d);
        drawStroke(x, top, x, top - 4.0f, EDGE, 0.35f, d);
        drawStroke(x - 1.0f, top - 2.8f, x + 1.0f, top - 2.8f, EDGE, 0.35f, d);
        if (isLit(id)) drawRect(x - 0.4f, top + 13.5f, 0.8f, 2.6f, GOLD, d);
        if (isLit(id + 1)) drawRect(x - 0.4f, top + 20.0f, 0.8f, 2.0f, GOLD, d);
    }

    void drawSky() {
        float starDriftX = PFMath::jsMod(drift * 0.15f, 128.0f);
        float starDriftY = PFMath::fastSin(t * 0.1f) * 0.8f;

        for (int i = 0; i < 66; ++i) {
            float hx = PFNoise::cellHash(i * 7, 1);
            float hy = PFNoise::cellHash(i * 7 + 1, 2);
            float x = PFMath::jsMod(2.0f + hx * 124.0f + starDriftX, 128.0f) - 32.0f;
            float y = 2.0f + hy * 94.0f + starDriftY;
            if (fabsf(x - 32.0f) < 10.0f && y > 22.0f) continue;

            int baseB = (i % 8 == 0) ? 172 : 48;
            float bVal = (float)baseB * (0.8f + 0.2f * PFMath::fastSin(t * 0.35f + (float)i));
            drawRect(x, y, 0.65f, 0.65f, grey((int)roundf(bVal)), 0.16f);
        }

        const float moonX = MOON_X;
        const float moonY = 18.0f;
        drawEllipse(moonX, moonY, 6.8f, 6.8f, WHITE, 0.18f);

        float rotAngle = t * 0.12f;
        float cosA = PFMath::fastCos(rotAngle);
        float sinA = PFMath::fastSin(rotAngle);

        static const float craters[5][3] = {
            {-3.0f, -3.0f, 2.0f},
            {-1.0f,  0.0f, 1.6f},
            { 2.0f, -4.0f, 1.5f},
            { 3.0f,  2.0f, 2.1f},
            {-2.0f,  4.0f, 1.4f}
        };

        for (int i = 0; i < 5; ++i) {
            float mx = craters[i][0];
            float my = craters[i][1];
            float r  = craters[i][2];
            float rx = mx * cosA - my * sinA;
            float ry = mx * sinA + my * cosA;
            drawEllipse(moonX + rx, moonY + ry, r, r * 0.8f, grey(48), 0.18f);
        }

        float shadowX = -3.0f * cosA;
        float shadowY = -3.0f * sinA;
        drawEllipse(moonX + shadowX, moonY + shadowY, 0.9f, 1.4f, INK, 0.18f);

        // The original six, then six more for the wider sky; each loops over 244 px, not 180.
        static const float clouds[12][4] = {
            { 1.0f, 16.0f, 0.90f, 24.0f},
            {59.0f, 12.0f, 0.85f, 21.0f},
            {-5.0f, 28.0f, 1.10f, 18.0f},
            {66.0f, 35.0f, 1.25f, 22.0f},
            { 8.0f, 42.0f, 1.25f, 19.0f},
            {52.0f, 48.0f, 1.40f, 25.0f},
            {-34.0f, 8.0f, 0.95f, 22.0f},
            {92.0f, 22.0f, 1.00f, 20.0f},
            {-28.0f, 40.0f, 1.20f, 23.0f},
            {96.0f, 46.0f, 1.15f, 18.0f},
            {-52.0f, 55.0f, 1.30f, 21.0f},
            {28.0f,  4.0f, 0.80f, 19.0f}
        };

        for (int i = 0; i < 12; ++i) {
            float cDrift = PFMath::jsMod((drift * 3.0f) * (0.48f + (float)(i % 6) * 0.05f) + (float)i * 3.0f + 122.0f, 244.0f) - 122.0f - (float)i * 3.0f;
            drawCloud(clouds[i][0] + cDrift, clouds[i][1] + PFMath::fastSin(t * 0.08f + (float)i) * 0.6f, clouds[i][2], (int)clouds[i][3], 0.28f);
        }

        for (int i = 0; i < 8; ++i) {
            const Bird& b = birds[i];
            float renderY = b.y + PFMath::fastSin(t * b.waveFreq + (float)i) * b.waveAmp;
            float flap    = PFMath::fastSin(t * b.flapSpeed + (float)i) * 0.8f;
            drawStroke(b.x - 1.5f, renderY - 0.3f - flap, b.x, renderY + 0.5f, SILVER, 0.35f, 0.45f);
            drawStroke(b.x, renderY + 0.5f, b.x + 1.6f, renderY - 0.5f - flap, SILVER, 0.35f, 0.45f);
        }

        drawSpire(-19.0f, 71.0f, 110.0f, 90);
        drawSpire( 85.0f, 77.0f, 110.0f, 92);

        for (int i = -7; i < 22; ++i) {     // the original's 15 houses, and seven more each side
            float x = (float)i * 4.8f - 2.0f;
            float h = 7.0f + PFNoise::cellHash(i + 19, 3) * 12.0f;
            float y = 111.0f - h;
            drawRect(x, y, 3.8f, h, grey(((i % 3) + 3) % 3 == 0 ? 26 : 14), 0.42f);

            float pts[3][2] = {
                {x - 0.3f, y},
                {x + 1.9f, y - 3.0f - PFNoise::cellHash(i, 4) * 4.0f},
                {x + 4.1f, y}
            };
            drawPoly(pts, 3, grey(35), 0.42f);

            if (((i % 3) + 3) % 3 == 0) drawStroke(x + 1.9f, y - 4.0f, x + 1.9f, y - 7.0f, EDGE, 0.35f, 0.42f);
            if (isLit(i + 70)) drawRect(x + 1.2f, y + 3.0f, 0.7f, 1.3f, GOLD, 0.42f);
        }

        for (int i = 0; i < 27; ++i) {
            float y = 110.0f + (float)i * 0.48f;
            float shift = PFMath::fastSin(y * 1.8f + drift * 0.8f) * (0.7f + fabsf(flow));
            ColorRGB c = (i % 4 == 0) ? EDGE : SHADE;
            float h0 = PFNoise::cellHash(i, 5);
            float h1 = PFNoise::cellHash(i + 1, 6);
            drawStroke(45.0f + h0 * 4.0f + shift, y, 49.0f + h1 * 11.0f + shift, y, c, 0.3f, 0.5f);
            if (i % 3 == 0 && light > 0.2f) {
                drawStroke(54.0f + shift, y, 55.2f + shift + h0 * 1.4f, y, GOLD, 0.3f, 0.5f);
            }
        }
    }

    void drawTurret(float x, float y, float base) {
        drawRect(x - 1.0f, y, 2.0f, base - y, STONE);
        drawStroke(x - 1.0f, y, x - 1.0f, base, SILVER, 0.5f);
        drawStroke(x + 1.0f, y, x + 1.0f, base, EDGE, 0.4f);

        float pts[3][2] = {
            {x - 2.0f, y},
            {x,        y - 7.0f},
            {x + 2.0f, y}
        };
        drawPoly(pts, 3, INK);

        drawStroke(x - 2.0f, y, x, y - 7.0f, SILVER, 0.5f);
        drawStroke(x, y - 7.0f, x + 2.0f, y, EDGE, 0.4f);
        drawStroke(x, y - 7.0f, x, y - 9.0f, EDGE, 0.35f);
        drawRect(x - 2.3f, y, 4.6f, 0.65f, SILVER);
        if (isLit((int)floorf(x))) {
            drawRect(x - 0.4f, y + 1.5f, 0.8f, 3.3f, GOLD);
        }
        drawRect(x - 2.0f, base, 4.0f, 0.7f, EDGE);
    }

    void drawTower() {
        drawRect(24.0f, 39.0f, 16.0f, 74.0f, STONE);
        drawRect(23.0f, 65.0f, 2.0f, 47.0f, SHADE);
        drawRect(39.0f, 65.0f, 1.7f, 47.0f, SHADE);
        drawRect(25.5f, 67.0f, 13.0f, 43.0f, INK);

        float beaconSin = PFMath::fastSin(beacon / 4.0f * PI);
        ColorRGB edgeLight = (beacon > 0.0f) ? grey((int)roundf(173.0f + beaconSin * 69.0f)) : SILVER;

        drawStroke(23.5f, 44.0f, 23.5f, 113.0f, edgeLight, 0.75f);
        drawStroke(40.5f, 43.0f, 40.5f, 112.0f, EDGE, 0.55f);
        drawStroke(25.2f, 67.0f, 25.2f, 111.0f, EDGE, 0.50f);
        drawStroke(38.5f, 67.0f, 38.5f, 111.0f, SHADE, 0.55f);

        float pButtressL[5][2] = {
            {22.8f, 69.0f}, {24.5f, 69.0f}, {24.0f, 104.0f}, {22.8f, 114.0f}, {21.6f, 115.0f}
        };
        drawPoly(pButtressL, 5, grey(35));
        drawStroke(22.8f, 69.0f, 21.6f, 115.0f, edgeLight, 0.65f);

        float pButtressR[4][2] = {
            {40.0f, 69.0f}, {41.2f, 69.0f}, {42.1f, 113.0f}, {40.5f, 112.0f}
        };
        drawPoly(pButtressR, 4, grey(18));
        drawStroke(41.2f, 69.0f, 42.1f, 113.0f, EDGE, 0.45f);

        static const float yBands[3] = {67.0f, 88.0f, 103.0f};
        for (int i = 0; i < 3; ++i) {
            drawRect(22.1f, yBands[i], 4.0f, 0.7f, edgeLight);
            drawRect(38.2f, yBands[i], 3.7f, 0.6f, EDGE);
        }

        drawWindow(27.0f, 66.8f, 2.3f, 6.2f, 2);
        drawWindow(30.8f, 66.8f, 2.3f, 6.2f, 5);
        drawWindow(34.6f, 66.8f, 2.3f, 6.2f, 8);
        drawWindow(29.0f, 77.0f, 6.0f, 10.3f, 1);
        drawWindow(29.7f, 93.0f, 4.6f, 9.0f, 4);
        drawWindow(29.8f, 106.0f, 4.4f, 7.5f, 0);

        drawArch(28.2f, 75.1f, 7.6f, 13.3f, EDGE);
        drawArch(28.8f, 75.8f, 6.4f, 11.7f, INK);
        drawWindow(29.8f, 77.4f, 4.4f, 9.8f, 1);

        if (zoom > 1.3f) {
            for (int i = 0; i < 23; ++i) {
                float y = 65.0f + (float)i * 2.1f;
                drawStroke(23.2f, y, 24.6f, y, grey(i % 3 == 0 ? 106 : 45), 0.22f);
                drawStroke(39.4f, y + 0.7f, 40.9f, y + 0.7f, SHADE, 0.25f);
            }
            static const float yDia[3] = {75.3f, 91.4f, 104.7f};
            for (int i = 0; i < 3; ++i) {
                float y = yDia[i];
                float ptsOuter[4][2] = {{32.0f, y - 1.6f}, {33.0f, y}, {32.0f, y + 1.6f}, {31.0f, y}};
                drawPoly(ptsOuter, 4, EDGE);
                float ptsInner[4][2] = {{32.0f, y - 1.0f}, {32.6f, y}, {32.0f, y + 1.0f}, {31.4f, y}};
                drawPoly(ptsInner, 4, INK);
            }
            float swing = PFMath::fastSin(t * 2.3f) * 1.3f;
            drawStroke(32.0f, 68.0f, 32.0f + swing, 73.0f, SILVER, 0.3f);
            drawEllipse(32.0f + swing, 73.0f, 0.85f, 1.05f, WARM);
            drawEllipse(32.0f + swing, 73.0f, 0.60f, 0.80f, GOLD);
        }

        drawRect(23.0f, 44.0f, 18.0f, 19.0f, STONE);
        drawRect(24.5f, 45.4f, 15.0f, 16.8f, INK);
        drawRect(23.0f, 44.0f, 18.0f, 1.0f, EDGE);
        drawRect(22.5f, 63.0f, 19.0f, 1.0f, SILVER);
        drawRect(24.0f, 64.5f, 16.0f, 0.6f, EDGE);

        static const float xCols[2] = {22.5f, 40.8f};
        for (int i = 0; i < 2; ++i) {
            float x = xCols[i];
            drawStroke(x, 45.0f, x, 62.0f, SILVER, 0.55f);
            drawRect(x - 0.65f, 45.0f, 1.8f, 1.3f, EDGE);
            drawRect(x - 0.80f, 61.5f, 2.1f, 1.2f, SILVER);
        }

        drawRect(26.0f, 32.0f, 12.0f, 11.0f, STONE);

        float pBelfry1[3][2] = {{25.0f, 32.0f}, {32.0f, 13.0f}, {39.0f, 32.0f}};
        drawPoly(pBelfry1, 3, INK);

        float pBelfry2[3][2] = {{25.0f, 32.0f}, {32.0f, 13.0f}, {29.8f, 30.0f}};
        drawPoly(pBelfry2, 3, grey(35));

        drawStroke(25.0f, 32.0f, 32.0f, 13.0f, SILVER, 0.70f);
        drawStroke(32.0f, 13.0f, 39.0f, 32.0f, EDGE, 0.40f);
        drawStroke(27.5f, 31.0f, 32.0f, 15.0f, EDGE, 0.45f);

        if (zoom > 1.4f) {
            for (int i = 0; i < 10; ++i) {
                float y = 18.0f + (float)i * 1.3f;
                float x = 32.0f - (y - 13.0f) * 0.37f;
                drawStroke(x, y, x + 0.9f, y, SHADE, 0.3f);
            }
        }

        drawTurret(25.0f, 32.0f, 41.0f);
        drawTurret(39.0f, 32.0f, 41.0f);
        drawTurret(22.0f, 41.0f, 46.0f);
        drawTurret(42.0f, 41.0f, 46.0f);

        float pPediment[5][2] = {
            {28.0f, 39.0f}, {28.0f, 32.0f}, {32.0f, 27.5f}, {36.0f, 32.0f}, {36.0f, 39.0f}
        };
        drawPoly(pPediment, 5, INK);

        drawStroke(28.0f, 32.0f, 32.0f, 27.5f, SILVER, 0.60f);
        drawStroke(32.0f, 27.5f, 36.0f, 32.0f, EDGE, 0.50f);
        drawWindow(30.0f, 30.3f, 4.0f, 8.5f, 3);
        drawRect(25.0f, 40.0f, 14.0f, 0.80f, SILVER);
        drawRect(26.0f, 42.0f, 12.0f, 0.65f, EDGE);

        for (float x = 27.0f; x <= 36.0f; x += 2.7f) {
            drawRect(x, 40.9f, 1.0f, 1.0f, INK);
        }

        drawStroke(32.0f, 13.0f, 32.0f, 8.4f, SILVER, 0.45f);
        drawStroke(30.9f, 10.2f, 33.1f, 10.2f, (light > 0.15f) ? GOLD : SILVER, 0.50f);
        if (light > 0.15f) {
            drawRect(31.8f, 8.3f, 0.5f, 1.7f, WARM);
        }
    }

    void drawClockFace() {
        drawEllipse(32.0f, 53.0f, 8.70f, 8.70f, EDGE);
        drawEllipse(32.0f, 53.0f, 8.10f, 8.10f, INK);
        drawEllipse(32.0f, 53.0f, 7.55f, 7.55f, WHITE);

        bool fine = (zoom >= 1.7f);
        if (fine) {
            for (int i = 0; i < 60; ++i) {
                float a = (float)i * (TWO_PI / 60.0f) - HALF_PI;
                float r = (i % 5 == 0) ? 6.65f : 7.0f;
                drawStroke(32.0f + PFMath::fastCos(a) * r,    53.0f + PFMath::fastSin(a) * r,
                           32.0f + PFMath::fastCos(a) * 7.2f, 53.0f + PFMath::fastSin(a) * 7.2f,
                           INK, 0.22f);
            }
        }

        for (int i = 0; i < 12; ++i) {
            float a = (float)i * (TWO_PI / 12.0f) - HALF_PI;
            if (!fine) {
                float pos[2];
                project(32.0f + PFMath::fastCos(a) * 6.6f, 53.0f + PFMath::fastSin(a) * 6.6f, 1.0f, pos[0], pos[1]);
                setPixelRgb((int)roundf(pos[0]), (int)roundf(pos[1]), INK);
            }
        }

        if (fine) {
            drawRoman("XII", 32.0f, 46.9f, 1.4f, INK);
            drawRoman("III", 37.2f, 52.3f, 1.4f, INK);
            drawRoman("VI",  32.0f, 57.6f, 1.4f, INK);
            drawRoman("IX",  26.8f, 52.3f, 1.4f, INK);

            if (zoom > 2.7f) {
                static const struct { int n; const char* str; } nums[8] = {
                    {1, "I"}, {2, "II"}, {4, "IV"}, {5, "V"},
                    {7, "VII"}, {8, "VIII"}, {10, "X"}, {11, "XI"}
                };
                for (int i = 0; i < 8; ++i) {
                    float a = (float)nums[i].n * (TWO_PI / 12.0f) - HALF_PI;
                    drawRoman(nums[i].str, 32.0f + PFMath::fastCos(a) * 5.45f, 53.0f + PFMath::fastSin(a) * 5.45f - 0.6f, 1.15f, INK);
                }
            }
        }

        float hourA = (fmodf(hours, 12.0f) / 12.0f) * TWO_PI - HALF_PI;
        float minA  = PFMath::fract(hours) * TWO_PI - HALF_PI;

        drawHand(hourA, 4.2f, 0.70f, INK);
        drawHand(minA,  6.1f, 0.42f, INK);

        drawEllipse(32.0f, 53.0f, 0.85f, 0.85f, INK);
        drawEllipse(32.0f, 53.0f, 0.30f, 0.30f, (light > 0.10f) ? GOLD : WHITE);

        if (zoom > 2.0f) {
            float secA = PFMath::fract(hours * 60.0f) * TWO_PI - HALF_PI;
            drawStroke(32.0f, 53.0f, 32.0f + PFMath::fastCos(secA) * 6.0f, 53.0f + PFMath::fastSin(secA) * 6.0f, GOLD, 0.17f);
            drawEllipse(32.0f, 53.0f, 0.33f, 0.33f, INK);
        }
    }

    void drawRoof(float x, float y, float w, float h, float depth, int id) {
        drawRect(x, y, w, 128.0f - y, STONE, depth);

        float pRoof[3][2] = {
            {x - 2.0f, y}, {x + w * 0.5f, y - h}, {x + w + 2.0f, y}
        };
        drawPoly(pRoof, 3, INK, depth);

        drawStroke(x - 2.0f, y, x + w * 0.5f, y - h, EDGE, 0.65f, depth);
        drawStroke(x + w * 0.5f, y - h, x + w + 2.0f, y, SHADE, 0.40f, depth);
        drawStroke(x - 1.0f, y, x + w + 1.0f, y, EDGE, 0.55f, depth);

        if (w > 15.0f) {
            for (int i = 1; i < 5; ++i) {
                float fi = (float)i;
                drawStroke(x + w * 0.5f - fi * 1.4f, y - h + fi * 1.6f,
                           x + w * 0.5f + fi * 1.8f, y - h + fi * 1.6f,
                           grey(25), 0.3f, depth);
            }
        }

        if (w > 8.0f) {
            drawWindow(x + w * 0.5f - 1.6f, y + 3.0f, 3.2f, 5.0f, id, depth);
        }

        drawRect(x + w * 0.24f,         y - h * 0.75f - 3.0f, 1.7f, 5.0f, INK, depth);
        drawRect(x + w * 0.24f - 0.6f,  y - h * 0.75f - 3.0f, 2.9f, 0.65f, EDGE, depth);
    }

    void drawForeground() {
        for (int i = 0; i < 10; ++i) {
            float phase = PFMath::jsMod(t * 0.22f + (float)i * 0.16f, 1.6f);
            float x = 7.0f + phase * flow * 3.0f + PFMath::fastSin(phase * 5.0f + t * 0.15f) * 0.8f;
            float y = 105.0f - phase * 12.0f;
            drawEllipse(x, y, 0.5f + phase * 0.6f, 0.9f, grey((int)roundf(28.0f * (1.0f - phase / 1.6f))), 0.90f);
        }
        for (int i = 0; i < 10; ++i) {      // a second stack on the right, out of step with the first
            float phase = PFMath::jsMod(t * 0.22f + (float)i * 0.16f + 0.7f, 1.6f);
            float x = 90.0f + phase * flow * 3.0f + PFMath::fastSin(phase * 5.0f + t * 0.15f + 2.0f) * 0.8f;
            float y = 103.0f - phase * 12.0f;
            drawEllipse(x, y, 0.5f + phase * 0.6f, 0.9f, grey((int)roundf(28.0f * (1.0f - phase / 1.6f))), 0.90f);
        }

        drawRoof(-36.0f, 118.0f, 15.0f, 8.0f, 1.14f, 95);
        drawRoof(-22.0f, 124.0f, 12.0f, 7.0f, 1.18f, 96);
        drawRoof(-13.0f, 119.0f, 9.0f, 6.0f, 1.15f, 97);
        drawRoof(-3.0f, 113.0f, 16.0f, 7.0f, 1.12f, 20);
        drawRoof( 9.0f, 122.0f, 14.0f, 8.0f, 1.16f, 21);
        drawRoof(19.0f, 116.0f, 22.0f, 8.0f, 1.13f, 22);
        drawRoof(37.0f, 126.0f, 14.0f, 9.0f, 1.20f, 23);
        drawRoof(55.0f, 120.0f, 14.0f, 8.0f, 1.15f, 24);
        drawRoof(71.0f, 114.0f, 17.0f, 7.0f, 1.13f, 98);
        drawRoof(86.0f, 123.0f, 14.0f, 8.0f, 1.17f, 99);

        drawRect(4.0f, 105.0f, 4.0f, 10.0f, INK, 1.1f);
        drawRect(3.3f, 104.5f, 5.4f, 1.0f, EDGE, 1.1f);
        drawRect(4.0f, 101.0f, 1.2f, 4.0f, INK, 1.1f);
        drawRect(6.4f, 101.0f, 1.2f, 4.0f, INK, 1.1f);

        drawRect(87.0f, 103.0f, 4.0f, 11.0f, INK, 1.1f);
        drawRect(86.3f, 102.5f, 5.4f, 1.0f, EDGE, 1.1f);
        drawRect(87.0f,  99.0f, 1.2f, 4.0f, INK, 1.1f);
        drawRect(89.4f,  99.0f, 1.2f, 4.0f, INK, 1.1f);
    }

    void setup() {
        PFMath::buildSinLUT();

        if (!rgbBuf) {
            rgbBuf = reinterpret_cast<uint8_t*>(PFMem::allocFloats((FRAME_W * FRAME_H * 3 + 3) / 4));
        }

        t = 0.0f;
        zoom = 1.0f;
        rawZoom = 1.0f;
        prevRawZoom = 1.0f;
        hours = 10.0f + 1.0f / 6.0f;
        clockSpeed = 0.448f;
        rawClockSpeed = 0.448f;
        wind = 1.149f;
        rawWind = 1.149f;
        light = 1.0f;
        rawLight = 1.0f;
        autoClock = true;
        zoomHome = false;
        gust = 0.0f;
        beacon = 0.0f;
        drift = 0.0f;
        flow = 0.18f;

        birds[0] = {-10.0f, 25.0f, 7.0f, 1.2f, 2.0f, 8.5f};
        birds[1] = { 15.0f, 42.0f, 9.0f, 0.9f, 1.5f, 9.2f};
        birds[2] = { 45.0f, 58.0f, 6.0f, 1.5f, 2.8f, 7.8f};
        birds[3] = { 70.0f, 73.0f, 8.0f, 1.1f, 1.8f, 8.8f};
        birds[4] = {-40.0f, 33.0f, 7.5f, 1.0f, 2.2f, 8.2f};
        birds[5] = {100.0f, 50.0f, 6.5f, 1.3f, 1.6f, 9.0f};
        birds[6] = {-25.0f, 66.0f, 8.5f, 0.8f, 2.4f, 8.0f};
        birds[7] = { 88.0f, 18.0f, 7.0f, 1.4f, 1.9f, 9.4f};
    }

    void update(float dt, const InputFrame& input) {
        if (!rgbBuf) return;

        float dtClamped = fmaxf(0.0f, fminf(0.05f, dt));

        PFParams::apply(input, 0, &rawZoom,       1.0f,   3.5f,  0.052f);
        PFParams::apply(input, 1, &rawClockSpeed, -3.0f,  5.0f,  0.167f);
        PFParams::apply(input, 2, &rawWind,       -10.0f, 10.0f, 0.417f);
        PFParams::apply(input, 3, &rawLight,      0.0f,   1.0f,  0.021f);

        if (fabsf(rawZoom - prevRawZoom) > 0.001f) {
            zoomHome = false;
        }
        prevRawZoom = rawZoom;

        if (input.btnPressed[0] && !input.paramAbsoluteActive[0] && !input.knobAudioActive[0]) {
            zoomHome = true;
        }
        if (input.btnPressed[1] && !input.paramAbsoluteActive[1] && !input.knobAudioActive[1]) {
            autoClock = !autoClock;
        }
        if (input.btnPressed[2] && !input.paramAbsoluteActive[2] && !input.knobAudioActive[2]) {
            gust = 3.8f;
        }
        if (input.btnPressed[3] && !input.paramAbsoluteActive[3] && !input.knobAudioActive[3]) {
            beacon = 4.0f;
        }

        float ease = 1.0f - expf(-dtClamped * 5.0f);
        float targetZoom = zoomHome ? 1.0f : rawZoom;
        zoom       += (targetZoom - zoom) * ease;
        clockSpeed += (rawClockSpeed - clockSpeed) * ease;
        wind       += (rawWind - wind) * ease;
        light      += (rawLight - light) * ease;

        t += dtClamped;
        if (t >= 628.3185307f) t -= 628.3185307f;

        if (autoClock) {
            hours += (dtClamped / 120.0f) * clockSpeed;
            hours = fmodf(hours, 24.0f);
            if (hours < 0.0f) hours += 24.0f;
        }

        gust   = fmaxf(0.0f, gust - dtClamped);
        beacon = fmaxf(0.0f, beacon - dtClamped);

        flow = wind + (wind < 0.0f ? -1.0f : 1.0f) * PFMath::fastSin(gust / 3.8f * PI) * 0.9f;
        drift += dtClamped * flow;
        if (drift >= 5760.0f) drift -= 5760.0f;
        else if (drift <= -5760.0f) drift += 5760.0f;

        for (int i = 0; i < 8; ++i) {
            Bird& b = birds[i];
            float currentSpeed = b.baseSpeed + flow * 10.0f;
            b.x += currentSpeed * dtClamped;
            if (currentSpeed >= 0.0f && b.x > 116.0f) {
                b.x = -52.0f;
            } else if (currentSpeed < 0.0f && b.x < -52.0f) {
                b.x = 116.0f;
            }
        }
    }

    void draw() {
        PFCanvas::setFrame(FRAME_W, FRAME_H);

        if (!rgbBuf) {
            PFCanvas::present();
            return;
        }

        memset(rgbBuf, 0, FRAME_W * FRAME_H * 3);

        view = 1.0f + (zoom - 1.0f) * 2.4f;
        float approach = fmaxf(0.0f, fminf(1.0f, (zoom - 1.0f) / 1.8f));
        cameraY = 64.0f + (53.0f - 64.0f) * (approach * approach * (3.0f - 2.0f * approach));

        drawSky();
        drawTower();
        drawClockFace();
        drawForeground();

        for (int y = 0; y < FRAME_H; ++y) {
            int row = y * FRAME_W * 3;
            for (int x = 0; x < FRAME_W; ++x) {
                int i = row + x * 3;
                PFCanvas::setPixel(x, y, rgbBuf[i], rgbBuf[i + 1], rgbBuf[i + 2]);
            }
        }

        PFCanvas::present();
    }

} // namespace MidnightClocktower