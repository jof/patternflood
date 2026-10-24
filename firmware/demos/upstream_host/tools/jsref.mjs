// Run an upstream web preset (web/src/lib/presets/pattern-*.ts) headless, as the
// Pattern Lab harness does, and write its last frame as raw RGB888 to stdout.
//
//   node jsref.mjs pattern-0516.ts W H FRAMES k0 k1 k2 k3
//
// knobValues are held at k0..k3 from the first frame (the web's absolute knobs);
// knobNormalized is derived from the default ranges. dt is 1/30 s.
// License: MIT
import { readFileSync } from "node:fs";

const [file, W, H, FRAMES, ...k] = process.argv.slice(2);
const src = readFileSync(file, "utf8");
const m = src.match(/code:\s*`([\s\S]*?)`,\s*\n\s*(?:[a-zA-Z]+:|\};)/);
if (!m) throw new Error("no code: `...` in " + file);
const code = m[1].replace(/\\`/g, "`").replace(/\\\$/g, "$").replace(/^\s*export\s+/gm, "");
const mod = new Function(`${code}\nreturn { setup, update, draw };`)();

const RANGES = [[0, 1], [0.1, 10], [0, 4.9], [0, 1]];
const w = +W, h = +H;
const buf = Buffer.alloc(w * h * 3);
const display = {
  width: w, height: h,
  setPixel(x, y, r, g, b) {
    x = Math.floor(x); y = Math.floor(y);
    if (x < 0 || y < 0 || x >= w || y >= h) return;
    const i = (y * w + x) * 3;
    const c = (v) => Math.max(0, Math.min(255, Math.round(v || 0)));
    buf[i] = c(r); buf[i + 1] = c(g); buf[i + 2] = c(b);
  },
};
const knobValues = k.map(Number);
const knobNormalized = knobValues.map((v, i) => (v - RANGES[i][0]) / (RANGES[i][1] - RANGES[i][0]));
const params = {};
mod.setup(params);
let time = 0;
for (let f = 0; f < +FRAMES; f++) {
  const dt = 1 / 30;
  time += dt;
  const input = { knobDeltas: [0, 0, 0, 0], knobValues, knobNormalized,
                  btnPressed: [false, false, false, false], btnHeld: [false, false, false, false] };
  mod.update(dt, input, params);
  mod.draw(display, params, time);
}
process.stdout.write(buf);
