// Patternflood's web remote. The server's side, and the stream's format, are in pfd/web.py.
"use strict";

const N = 128, FRAME = N * N * 3, LIGHTS = 12;
const DETENT_DEG = 15;            // the 4991's encoder: 24 detents a turn
const HOLD_MS = 320;              // a knob held this long without turning is pushed, not clicked
const $ = (id) => document.getElementById(id);

const ui = {
  panel: $("panel"), glow: $("glow"), well: $("well"), lost: $("lost"), wake: $("wake"),
  knobs: $("knobs"), name: $("name"), where: $("where"), mode: $("mode"), blurb: $("blurb"),
  bright: $("bright"), brightOut: $("bright-out"), audioRow: $("audio-row"), audio: $("audio"),
  stats: $("stats"), tabs: $("tabs"), grid: $("grid"), search: $("search"), empty: $("empty"),
};

let catalog = null;               // {shelves, demos, thumbs}
let state = {};
let shelf = null;                 // the shelf shown in the grid
let query = "";
let thumbRev = -1;
let brightDragging = false, tBrightSent = 0;

// ---------------------------------------------------------------- commands

let outbox = [], flushing = false;
function send(cmd) {
  const last = outbox[outbox.length - 1];
  if (cmd.op === "turn" && last && last.op === "turn" && last.k === cmd.k && Math.sign(last.d) === Math.sign(cmd.d)
      && Math.abs(last.d + cmd.d) <= 48) {
    last.d += cmd.d;              // a fast spin: one turn of several detents
  } else {
    outbox.push(cmd);
  }
  if (!flushing) flush();
}
async function flush() {
  flushing = true;
  while (outbox.length) {
    const batch = outbox;
    outbox = [];
    try {
      await fetch("/api/cmd", {method: "POST", headers: {"Content-Type": "application/json"},
                               body: JSON.stringify(batch), keepalive: true});
    } catch (e) { /* the stream's "lost" note says so */ }
  }
  flushing = false;
}

// ---------------------------------------------------------------- the panel

const frameCanvas = document.createElement("canvas");
frameCanvas.width = frameCanvas.height = N;
const frameCtx = frameCanvas.getContext("2d");
const frameImg = frameCtx.createImageData(N, N);
for (let i = 3; i < frameImg.data.length; i += 4) frameImg.data[i] = 255;
const panelCtx = ui.panel.getContext("2d");
const glowCtx = ui.glow.getContext("2d");
let mask = null, maskSize = 0, newFrame = false;

function sizePanel() {
  const css = ui.panel.getBoundingClientRect().width;
  const size = Math.max(N, Math.round(css * (window.devicePixelRatio || 1)));
  if (ui.panel.width !== size) {
    ui.panel.width = ui.panel.height = size;
    makeMask(size);
    newFrame = true;
  }
}
// The P2 panel's look: round LEDs with black between. Only when each LED gets 3 device pixels or more.
function makeMask(size) {
  const cell = size / N;
  mask = null;
  if (cell < 3) return;
  mask = document.createElement("canvas");
  mask.width = mask.height = size;
  const m = mask.getContext("2d");
  m.fillStyle = "#000";
  m.fillRect(0, 0, size, size);
  m.globalCompositeOperation = "destination-out";
  const r = cell * 0.4;
  m.beginPath();
  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      const cx = (x + 0.5) * cell, cy = (y + 0.5) * cell;
      m.moveTo(cx + r, cy);
      m.arc(cx, cy, r, 0, Math.PI * 2);
    }
  }
  m.fill();
}
function drawPanel() {
  if (newFrame) {
    newFrame = false;
    frameCtx.putImageData(frameImg, 0, 0);
    const s = ui.panel.width;
    panelCtx.globalCompositeOperation = "source-over";
    panelCtx.fillStyle = "#1a1612";              // the LEDs, unlit
    panelCtx.fillRect(0, 0, s, s);
    panelCtx.globalCompositeOperation = "lighter";
    panelCtx.imageSmoothingEnabled = false;
    panelCtx.drawImage(frameCanvas, 0, 0, s, s);
    panelCtx.globalCompositeOperation = "source-over";
    if (mask) panelCtx.drawImage(mask, 0, 0);
    glowCtx.drawImage(frameCanvas, 0, 0, ui.glow.width, ui.glow.height);
  }
  requestAnimationFrame(drawPanel);
}
new ResizeObserver(sizePanel).observe(ui.panel);
requestAnimationFrame(drawPanel);

// ---------------------------------------------------------------- the stream

let streamAbort = null, retryMs = 500;

async function stream() {
  if (streamAbort || document.hidden) return;
  const ctl = streamAbort = new AbortController();
  let buf = new Uint8Array(0);
  try {
    const r = await fetch("/api/stream?fps=30", {signal: ctl.signal, cache: "no-store"});
    if (!r.ok || !r.body) throw new Error(r.status);
    const reader = r.body.getReader();
    for (;;) {
      const {value, done} = await reader.read();
      if (done) break;
      ui.lost.hidden = true;
      retryMs = 500;
      const joined = new Uint8Array(buf.length + value.length);
      joined.set(buf);
      joined.set(value, buf.length);
      buf = joined;
      let off = 0;
      for (;;) {
        if (buf.length - off < 4) break;
        const n = buf[off] | buf[off + 1] << 8 | buf[off + 2] << 16 | buf[off + 3] << 24;
        const need = 4 + n + FRAME + LIGHTS;
        if (buf.length - off < need) break;
        if (n) onState(JSON.parse(new TextDecoder().decode(buf.subarray(off + 4, off + 4 + n))));
        onFrame(buf.subarray(off + 4 + n, off + 4 + n + FRAME), buf.subarray(off + 4 + n + FRAME, off + need));
        off += need;
      }
      buf = buf.slice(off);
    }
  } catch (e) {
    if (ctl.signal.aborted) return;
  } finally {
    if (streamAbort === ctl) streamAbort = null;
  }
  if (!document.hidden) {
    ui.lost.hidden = false;
    setTimeout(stream, retryMs);
    retryMs = Math.min(5000, retryMs * 2);
  }
}
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {               // nobody's looking: let the box stop sending
    if (streamAbort) streamAbort.abort();
    streamAbort = null;
  } else {
    stream();
  }
});

function onFrame(rgb, lights) {
  const d = frameImg.data;
  for (let i = 0, j = 0; i < FRAME; i += 3, j += 4) {
    d[j] = rgb[i]; d[j + 1] = rgb[i + 1]; d[j + 2] = rgb[i + 2];
  }
  newFrame = true;
  setLights(lights);
}

// ---------------------------------------------------------------- knobs

const knobs = [];
for (let k = 0; k < 4; k++) {
  const el = document.createElement("div");
  el.className = "knob";
  el.tabIndex = 0;
  el.setAttribute("role", "button");
  el.setAttribute("aria-label", `Knob k${k}`);
  el.title = `k${k}: drag round to turn, tap to click, hold to push`;
  el.innerHTML = `<span class="halo"></span><span class="lit"></span><span class="cap-k"><span class="tick"></span></span><span class="k">k${k}</span>`;
  ui.knobs.appendChild(el);
  const knob = {el, cap: el.querySelector(".cap-k"), angle: 0, light: ""};
  knobs.push(knob);
  wireKnob(knob, k);
}
function turnKnob(k, d) {
  const knob = knobs[k];
  knob.angle += d * DETENT_DEG;
  knob.cap.style.transform = `rotate(${knob.angle}deg)`;
  send({op: "turn", k, d});
}
function wireKnob(knob, k) {
  const el = knob.el;
  let g = null;
  const angleAt = (e) => {
    const r = el.getBoundingClientRect();
    return Math.atan2(e.clientY - (r.top + r.height / 2), e.clientX - (r.left + r.width / 2)) * 180 / Math.PI;
  };
  el.addEventListener("pointerdown", (e) => {
    if (g) return;
    e.preventDefault();
    el.setPointerCapture(e.pointerId);
    el.focus({preventScroll: true});
    g = {id: e.pointerId, a: angleAt(e), acc: 0, x: e.clientX, y: e.clientY, moved: false, pushed: false};
    g.timer = setTimeout(() => {
      if (g && !g.moved) { g.pushed = true; el.classList.add("held"); send({op: "down", k}); }
    }, HOLD_MS);
  });
  el.addEventListener("pointermove", (e) => {
    if (!g || e.pointerId !== g.id) return;
    const a = angleAt(e);
    let da = a - g.a;
    if (da > 180) da -= 360;
    if (da < -180) da += 360;
    g.a = a;
    g.acc += da;                  // from the first touch, so a turn counts all of itself
    if (Math.hypot(e.clientX - g.x, e.clientY - g.y) > 6) g.moved = true;
    if (!g.moved) return;
    while (g.acc >= DETENT_DEG) { g.acc -= DETENT_DEG; turnKnob(k, 1); }
    while (g.acc <= -DETENT_DEG) { g.acc += DETENT_DEG; turnKnob(k, -1); }
  });
  const end = (e) => {
    if (!g || e.pointerId !== g.id) return;
    clearTimeout(g.timer);
    if (g.pushed) {
      send({op: "up", k});
    } else if (!g.moved && e.type === "pointerup") {
      send({op: "down", k});
      send({op: "up", k});
    }
    el.classList.remove("held");
    g = null;
  };
  el.addEventListener("pointerup", end);
  el.addEventListener("pointercancel", end);
  let wheel = 0;
  el.addEventListener("wheel", (e) => {
    e.preventDefault();
    wheel += e.deltaMode === 1 ? e.deltaY * 30 : e.deltaY;
    while (wheel <= -40) { wheel += 40; turnKnob(k, 1); }
    while (wheel >= 40) { wheel -= 40; turnKnob(k, -1); }
  }, {passive: false});
  let keyDown = false;
  el.addEventListener("keydown", (e) => {
    const steps = {ArrowUp: 1, ArrowRight: 1, ArrowDown: -1, ArrowLeft: -1, PageUp: 6, PageDown: -6}[e.key];
    if (steps) { e.preventDefault(); e.stopPropagation(); turnKnob(k, steps); return; }
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      e.stopPropagation();
      if (!keyDown) { keyDown = true; el.classList.add("held"); send({op: "down", k}); }
    }
  });
  el.addEventListener("keyup", (e) => {
    if ((e.key === " " || e.key === "Enter") && keyDown) {
      e.preventDefault();
      e.stopPropagation();
      keyDown = false;
      el.classList.remove("held");
      send({op: "up", k});
    }
  });
  el.addEventListener("blur", () => {
    if (keyDown) { keyDown = false; el.classList.remove("held"); send({op: "up", k}); }
  });
}

let liveColour = "";
function setLights(bytes) {
  let best = null, bestV = 0.08 * 255;
  for (let k = 0; k < 4; k++) {
    const r = bytes[k * 3], g = bytes[k * 3 + 1], b = bytes[k * 3 + 2];
    const c = `rgb(${r},${g},${b})`;
    if (c !== knobs[k].light) {
      knobs[k].light = c;
      knobs[k].el.style.setProperty("--light", c);
    }
    const v = Math.max(r, g, b);
    if (v > bestV) { bestV = v; best = [r, g, b]; }
  }
  // the page's accent follows the brightest knob light, brought up to a readable level
  if (best) {
    const s = 255 / Math.max(...best);
    const c = `rgb(${best.map((x) => Math.round(Math.min(255, x * s * 0.85 + 30))).join(",")})`;
    if (c !== liveColour) {
      liveColour = c;
      document.documentElement.style.setProperty("--live", c);
    }
  }
}

// ---------------------------------------------------------------- buttons

const BUTTON_KEYS = {",": 0, "<": 0, "Enter": 1, ".": 2, ">": 2, "s": 3};
const capDown = new Set();
function buttonDown(b) {
  if (capDown.has(b)) return;
  capDown.add(b);
  document.querySelector(`.cap[data-b="${b}"]`).classList.add("down");
  send({op: "bdown", b});
}
function buttonUp(b) {
  if (!capDown.has(b)) return;
  capDown.delete(b);
  document.querySelector(`.cap[data-b="${b}"]`).classList.remove("down");
  send({op: "bup", b});
}
for (const cap of document.querySelectorAll(".cap")) {
  const b = +cap.dataset.b;
  cap.addEventListener("pointerdown", (e) => { e.preventDefault(); cap.setPointerCapture(e.pointerId); buttonDown(b); });
  cap.addEventListener("pointerup", () => buttonUp(b));
  cap.addEventListener("pointercancel", () => buttonUp(b));
  cap.addEventListener("keydown", (e) => {
    if (e.key === " " || e.key === "Enter") { e.preventDefault(); e.stopPropagation(); if (!e.repeat) buttonDown(b); }
  });
  cap.addEventListener("keyup", (e) => {
    if (e.key === " " || e.key === "Enter") { e.preventDefault(); e.stopPropagation(); buttonUp(b); }
  });
}
function typing(e) {
  // a text field takes every key; a focused button or knob keeps Enter and Space for itself
  const t = e.target;
  if (!t.closest) return false;
  if (t.closest("input[type=search], input[type=text], textarea")) return true;
  return (e.key === "Enter" || e.key === " ") && t.closest("button, input, .knob, a") !== null;
}
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey || typing(e)) return;
  const b = BUTTON_KEYS[e.key];
  if (b === undefined) return;
  e.preventDefault();
  if (!e.repeat) buttonDown(b);
});
document.addEventListener("keyup", (e) => {
  const b = BUTTON_KEYS[e.key];
  if (b !== undefined) buttonUp(b);
});
window.addEventListener("blur", () => { for (const b of [...capDown]) buttonUp(b); });

ui.wake.addEventListener("click", () => send({op: "wake"}));

// ---------------------------------------------------------------- what's on

const nameCtx = ui.name.getContext("2d");
let shownIndex = -1, labelFor = "";

async function drawName(text) {
  labelFor = text;
  let lab = null;
  try {
    lab = await (await fetch(`/api/label?s=${encodeURIComponent(text)}`)).json();
  } catch (e) { /* drawn as plain text below */ }
  if (labelFor !== text) return;
  ui.name.setAttribute("aria-label", text);
  const dpr = window.devicePixelRatio || 1;
  const cssW = ui.name.getBoundingClientRect().width, cssH = 40;
  ui.name.width = Math.round(cssW * dpr);
  ui.name.height = Math.round(cssH * dpr);
  const ctx = nameCtx;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH);
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--burn").trim() || "#43291a";
  if (!lab || lab.w <= 1) {
    ctx.font = `600 22px system-ui, sans-serif`;
    ctx.textBaseline = "middle";
    ctx.fillText(text, 0, cssH / 2, cssW);
    return;
  }
  // the panel's own font, each pixel a square burnt into the birch, on whole device pixels
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const W = ui.name.width, H = ui.name.height;
  const px = Math.max(1, Math.floor(Math.min(H / lab.h, W / lab.w, 5 * dpr)));
  const gap = px >= 4 ? Math.round(px / 5) : 0;
  const y0 = Math.floor((H - lab.h * px) / 2);
  lab.rows.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) {
      if (row[x] === "1") ctx.fillRect(x * px, y0 + y * px, px - gap, px - gap);
    }
  });
}

function onState(s) {
  const prev = state;
  state = s;
  if (!catalog) return;
  const demo = catalog.demos[s.i];
  if (s.i !== shownIndex && demo) {
    shownIndex = s.i;
    drawName(demo.name.toUpperCase());
    ui.blurb.textContent = demo.blurb;
    const members = catalog.demos.filter((d) => d.group === demo.group);
    const sh = catalog.shelves.find((x) => x.group === demo.group);
    ui.where.textContent = `${sh ? sentence(sh.name) : demo.group} shelf, ` +
      `${members.indexOf(demo) + 1} of ${members.length}`;
    document.title = `${demo.name} on Patternflood`;
    if (prev.i !== undefined && shelf === catalog.demos[prev.i]?.group && !query) shelf = demo.group;
    if (shelf === null) shelf = demo.group;
    renderTabs();
    renderGrid(true);
  }
  ui.mode.hidden = !(s.menu || s.asleep);
  ui.mode.textContent = s.asleep ? "Asleep" : s.menu ? "Menu open: k0 picks, k1 changes shelf, k3 sets brightness" : "";
  ui.wake.hidden = !s.asleep;
  if (!brightDragging && performance.now() - tBrightSent > 1500) {
    const v = Math.round(s.bright * 100);
    ui.bright.value = v;
    ui.brightOut.textContent = `${v}%`;
  }
  ui.audioRow.hidden = !s.audio_ok;
  ui.audio.checked = !!s.audio_knobs;
  ui.audio.disabled = !s.audio_live;
  ui.audioRow.classList.toggle("off", !s.audio_live);
  ui.audioRow.title = s.audio_live ? "" : "The box has no music to listen to (PF_AUDIO is none)";
  const bits = [`${s.fps.toFixed(0)} frames a second`, `about ${s.amps.toFixed(1)} A`];
  if (s.cap < 0.995) bits.push(`dimmed to ${Math.round(s.cap * 100)}% to stay in budget`);
  if (s.bpm) bits.push(`${s.bpm} BPM`);
  ui.stats.textContent = bits.join(", ");
  (s.held || []).forEach((h, k) => {
    if (document.activeElement !== knobs[k].el) knobs[k].el.classList.toggle("held", h);
  });
  if (s.thumb_rev !== thumbRev) {
    thumbRev = s.thumb_rev;
    refreshThumbs();
  }
}

ui.bright.addEventListener("input", () => {
  brightDragging = true;
  tBrightSent = performance.now();
  ui.brightOut.textContent = `${ui.bright.value}%`;
  send({op: "bright", v: ui.bright.value / 100});
});
ui.bright.addEventListener("change", () => { brightDragging = false; });
ui.audio.addEventListener("change", () => send({op: "audio_knobs", on: ui.audio.checked}));

// ---------------------------------------------------------------- the shelves

function renderTabs() {
  ui.tabs.innerHTML = "";
  const on = catalog.demos[state.i]?.group;
  for (const sh of catalog.shelves) {
    const b = document.createElement("button");
    b.setAttribute("aria-current", String(!query && sh.group === shelf));
    b.innerHTML = `${esc(sentence(sh.name))}<span class="n">${sh.count}</span>${sh.group === on ? '<span class="on" title="Playing now"></span>' : ""}`;
    b.addEventListener("click", () => {
      shelf = sh.group;
      query = ui.search.value = "";
      renderTabs();
      renderGrid(true);
    });
    ui.tabs.appendChild(b);
  }
}
function sentence(s) {
  // the panel's shelf names, in sentence case: "INTERDIM. CABLE" -> "Interdimensional cable"
  const t = s.toLowerCase().replace(/^interdim\./, "interdimensional");
  return t.charAt(0).toUpperCase() + t.slice(1);
}
function esc(s) {
  return s.replace(/[&<>"]/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
}
function visible() {
  if (query) {
    const q = query.toLowerCase();
    return catalog.demos.filter((d) => d.name.toLowerCase().includes(q) || d.blurb.toLowerCase().includes(q));
  }
  return catalog.demos.filter((d) => d.group === shelf);
}
function thumbURL(i) {
  const t = catalog.thumbs[i];
  return t ? `/thumbs/${i}.png?v=${t}` : null;
}
const tiles = new Map();          // demo index -> li
function renderGrid(scrollToCurrent) {
  const list = visible();
  ui.grid.innerHTML = "";
  tiles.clear();
  ui.empty.hidden = list.length > 0;
  ui.empty.textContent = query ? `Nothing matches "${query}". Try part of a name, or an author's handle.` : "";
  const shelfName = (g) => sentence(catalog.shelves.find((x) => x.group === g)?.name || g);
  const frag = document.createDocumentFragment();
  list.forEach((d, n) => {
    const li = document.createElement("li");
    li.className = "tile" + (d.i === state.i ? " current" : "");
    const url = thumbURL(d.i);
    li.innerHTML = `<button title="${esc(d.blurb)}"><span class="pic">${url ? `<img ${n < 40 ? "" : 'loading="lazy" '}alt="" src="${url}">` : ""}</span>` +
      `<span class="t">${esc(d.name)}</span>${query ? `<span class="s">${esc(shelfName(d.group))}</span>` : ""}</button>`;
    li.querySelector("button").addEventListener("click", () => {
      send({op: "goto", i: d.i});
      setCurrent(d.i);
    });
    tiles.set(d.i, li);
    frag.appendChild(li);
  });
  ui.grid.appendChild(frag);
  if (scrollToCurrent) revealCurrent();
}
function setCurrent(i) {
  for (const [j, li] of tiles) li.classList.toggle("current", j === i);
}
function revealCurrent() {
  const li = tiles.get(state.i);
  if (!li) return;
  // only on the wide layout, where the grid scrolls by itself: a phone's page stays where it is
  if (window.matchMedia("(min-width: 901px)").matches) li.scrollIntoView({block: "nearest"});
}
async function refreshThumbs() {
  if (!catalog) return;
  try {
    const t = await (await fetch("/api/thumbs")).json();
    catalog.thumbs = t.thumbs;
  } catch (e) { return; }
  for (const [i, li] of tiles) {
    const url = thumbURL(i);
    if (!url) continue;
    const pic = li.querySelector(".pic");
    const img = pic.querySelector("img");
    if (img) { if (!img.src.endsWith(url)) img.src = url; }
    else pic.innerHTML = `<img loading="lazy" alt="" src="${url}">`;
  }
}

let searchTimer = 0;
ui.search.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    query = ui.search.value.trim();
    renderTabs();
    renderGrid(false);
  }, 120);
});

$("random").addEventListener("click", () => {
  const list = visible().filter((d) => d.i !== state.i);
  if (!list.length) return;
  const d = list[Math.floor(Math.random() * list.length)];
  send({op: "goto", i: d.i});
  setCurrent(d.i);
});
$("snap").addEventListener("click", () => {
  const name = (catalog?.demos[state.i]?.name || "patternflood").replace(/[^\w.-]+/g, "-");
  ui.panel.toBlob((blob) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `patternflood-${name}.png`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  });
});
const goFull = () => {
  if (document.fullscreenElement) document.exitFullscreen();
  else ui.well.requestFullscreen?.().then(sizePanel, () => {});
};
$("full").addEventListener("click", goFull);
ui.panel.addEventListener("click", goFull);
document.addEventListener("fullscreenchange", () => setTimeout(sizePanel, 50));

// ---------------------------------------------------------------- start

(async function start() {
  for (;;) {
    try {
      catalog = await (await fetch("/api/demos")).json();
      break;
    } catch (e) {
      ui.lost.hidden = false;
      await new Promise((r) => setTimeout(r, 2000));
    }
  }
  try {
    const s = await (await fetch("/api/state")).json();
    if (s && s.i !== undefined) onState(s);
  } catch (e) { /* the stream brings it */ }
  stream();
})();
