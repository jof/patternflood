// ===== Patternflow pattern =====
// Title:    Multicore Phyllotaxis
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/e8316f656eb14bd8
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the original stacks SpiralCount
// sunflower cores in one column down its 64 x 128 frame; here they tile the square as a
// SpiralCount x SpiralCount grid (1, 4, 9 at the default, 16 or 25 cores), each core the size
// and seed density of the original's at that count, and neighbours counter-rotate like
// meshed gears (the original alternated down its column). Each core's colours step on along
// the grid as they stepped down the column; the divergence, morph, speed and white hearts are
// the original's.

// @matrix 128x128
// @knobs Divergence=0.1..1, SpiralCount=1..5, Speed=0..5, Morph=0..1
export function setup(params) {
  params.t = 0;
  params.k = [0.3819, 1, 1, 0];
}

export function update(dt, input, params) {
  params.k = input.knobValues;
  params.t += dt * params.k[2];
}

export function draw(display, params, time) {
  const w = display.width;
  const h = display.height;
  const count = Math.max(1, Math.floor(params.k[1]));
  const divergence = params.k[0] * Math.PI * 2;
  const morph = params.k[3];
  const t = params.t;

  // The original's cell: h / count tall, seeds spaced (cell / 2) / 10, 400 / count of them.
  const cellW = w / count, cellH = h / count;
  const cell = Math.min(cellW, cellH);
  const baseScale = (cell / 2) / 10;
  const seeds = Math.floor(400 / count);

  for (let row = 0; row < count; row++) {
    for (let col = 0; col < count; col++) {
      const s = row * count + col;
      const cx = cellW / 2 + col * cellW;
      const cy = cellH / 2 + row * cellH;
      const dir = ((row + col) % 2 === 0) ? 1 : -1;
      const rot = t * dir;
      const hue0 = t * 0.3 + s * 1.5;
      for (let i = 1; i < seeds; i++) {
        const angle = i * divergence + rot;
        const radius = baseScale * Math.sqrt(i);
        if (radius > cell) break;
        const x = Math.floor(cx + Math.cos(angle) * radius);
        const y = Math.floor(cy + Math.sin(angle) * radius);
        if (x < 0 || x >= w || y < 0 || y >= h) continue;
        if (i < 5) { display.setPixel(x, y, 255, 255, 255); continue; }
        const hue = i * 0.05 + hue0;
        display.setPixel(x, y,
          Math.floor(127 + 127 * Math.sin(hue)),
          Math.floor(127 + 127 * Math.sin(hue + 2 + morph * 4)),
          Math.floor(127 + 127 * Math.sin(hue + 4)));
      }
    }
  }
}

// ── Made with Patternflow Community · https://patternflow.work/community ──
// Shared under CC-BY-SA-4.0. Attribution is part of this licence —
// please keep this notice and the author credit above when you reuse,
// remix, or redistribute this pattern. Do not delete it.
