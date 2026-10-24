// Host stand-in for upstream's PFCanvas: the same frame mapping into a plain
// RGB888 buffer, which the host reads after draw(). No gamma, white balance or
// saturation here: the Python side owns output processing.
// License: MIT
#pragma once
#include <Arduino.h>
#include "config.h"

namespace PFCanvas {

constexpr int W = PANEL_RES_W;
constexpr int H = PANEL_RES_H;
constexpr size_t BUFFER_BYTES = (size_t)W * H * 3;

inline uint8_t buffer[BUFFER_BYTES];

inline int frameW = W, frameH = H, frameOffX = 0, frameOffY = 0;
inline bool frameRotate = false, frameDirect = true;

inline void clear() { memset(buffer, 0, BUFFER_BYTES); }

inline void resetFrame() {
  frameW = W; frameH = H; frameOffX = frameOffY = 0;
  frameRotate = false; frameDirect = true;
}

// As upstream: same grid = straight through, swapped = quarter turn, else centred.
inline void setFrame(int w, int h) {
  if (w <= 0 || h <= 0 || (w == W && h == H)) { resetFrame(); return; }
  frameW = w; frameH = h;
  frameDirect = false;
  frameRotate = (w == H && h == W);
  frameOffX = frameRotate ? 0 : (W - w) / 2;
  frameOffY = frameRotate ? 0 : (H - h) / 2;
  clear();
}

inline void setPixel(int x, int y, uint8_t r, uint8_t g, uint8_t b) {
  int px = x, py = y;
  if (!frameDirect) {
    if ((unsigned)x >= (unsigned)frameW || (unsigned)y >= (unsigned)frameH) return;
    if (frameRotate) { px = W - 1 - y; py = x; }
    else { px = x + frameOffX; py = y + frameOffY; }
  }
  if ((unsigned)px >= (unsigned)W || (unsigned)py >= (unsigned)H) return;
  size_t i = ((size_t)py * W + px) * 3;
  buffer[i] = r; buffer[i + 1] = g; buffer[i + 2] = b;
}

inline void present() { resetFrame(); }

}  // namespace PFCanvas
