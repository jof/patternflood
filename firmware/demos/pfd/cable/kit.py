"""A kit for TV from other dimensions: shapes, faces, captions and tickers.

Everything draws in place on draw's float RGB images, (128, 128, 3), 0..1. Shapes are
antialiased, and take an alpha `a` so ghosts and fades come free.
"""
import math

import numpy as np

from .. import draw
from ..draw import N, X, Y

BLACK, WHITE = (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)
SKINS = [(.95, .75, .6), (.75, .52, .38), (.5, .33, .22), (.6, .85, .55), (.7, .6, .95), (.55, .8, .9)]
LINE = 11               # the bitmap font's line height


def _box(x0, y0, x1, y1):
    return max(0, int(x0)), max(0, int(y0)), min(N, int(math.ceil(x1))), min(N, int(math.ceil(y1)))


def _paint(img, x0, y0, x1, y1, cov, rgb):
    region = img[y0:y1, x0:x1]
    region += (np.asarray(rgb, np.float32) - region) * cov[..., None]


def vgrad(img, top, bottom, y0=0, y1=N):
    """A vertical gradient from top to bottom over rows y0..y1."""
    s = np.linspace(0, 1, y1 - y0, dtype=np.float32)[:, None, None]
    img[y0:y1] = np.asarray(top, np.float32) * (1 - s) + np.asarray(bottom, np.float32) * s


def rect(img, x0, y0, x1, y1, rgb, a=1.0):
    x0, y0, x1, y1 = _box(round(x0), round(y0), round(x1), round(y1))
    if x0 < x1 and y0 < y1:
        if a >= 1:
            img[y0:y1, x0:x1] = rgb
            return
        region = img[y0:y1, x0:x1]
        region += (np.asarray(rgb, np.float32) - region) * a


def ellipse(img, x, y, rx, ry, rgb, a=1.0, rot=0.0, half=None):
    """A filled ellipse, rotated by rot radians; half="top" or "bottom" keeps just that half."""
    r = max(rx, ry) + 1.5
    x0, y0, x1, y1 = _box(x - r, y - r, x + r, y + r)
    if half == "bottom":
        y0 = max(y0, int(y))
    elif half == "top":
        y1 = min(y1, int(math.ceil(y)))
    if x0 >= x1 or y0 >= y1:
        return
    dx, dy = X[y0:y1, x0:x1] + 0.5 - x, Y[y0:y1, x0:x1] + 0.5 - y
    if rot:
        c, s = math.cos(rot), math.sin(rot)
        dx, dy = c * dx + s * dy, -s * dx + c * dy
    d = np.sqrt((dx / max(rx, 0.3)) ** 2 + (dy / max(ry, 0.3)) ** 2)
    cov = np.clip((1 - d) * min(rx, ry) + 0.5, 0, 1) * a
    _paint(img, x0, y0, x1, y1, cov, rgb)


def line(img, x0, y0, x1, y1, rgb, w=1.0, a=1.0):
    """A thick antialiased line segment with round ends."""
    pad = w + 1.5
    bx0, by0, bx1, by1 = _box(min(x0, x1) - pad, min(y0, y1) - pad, max(x0, x1) + pad, max(y0, y1) + pad)
    if bx0 >= bx1 or by0 >= by1:
        return
    px, py = X[by0:by1, bx0:bx1] + 0.5, Y[by0:by1, bx0:bx1] + 0.5
    vx, vy = x1 - x0, y1 - y0
    s = np.clip(((px - x0) * vx + (py - y0) * vy) / max(vx * vx + vy * vy, 1e-6), 0, 1)
    d = np.hypot(px - x0 - s * vx, py - y0 - s * vy)
    _paint(img, bx0, by0, bx1, by1, np.clip(w / 2 + 0.5 - d, 0, 1) * a, rgb)


def poly(img, pts, rgb):
    draw.poly(img, pts, np.asarray(rgb, np.float32))


def star(img, x, y, r, rgb, n=12, inner=0.62, rot=0.0):
    """A price-sticker starburst."""
    a = rot + np.arange(2 * n) * math.pi / n
    rr = np.where(np.arange(2 * n) % 2 == 0, r, r * inner)
    poly(img, np.stack([x + rr * np.cos(a), y + rr * np.sin(a)], 1), rgb)


def rays(img, x, y, c0, c1, n=12, rot=0.0):
    """The whole screen in alternating sunburst wedges about (x, y)."""
    ang = np.arctan2(Y + 0.5 - y, X + 0.5 - x) + rot
    m = (np.floor(ang * n / (2 * math.pi)) % 2)[..., None]
    img[:] = np.asarray(c0, np.float32) * (1 - m) + np.asarray(c1, np.float32) * m


def grey(img, k=1.0):
    """Drain the colour, as in an infomercial's sad 'before'."""
    g = img.mean(-1, keepdims=True)
    img += (g - img) * k


# ---------------------------------------------------------------- people

def chatter(t, seed=0.0):
    """How far open a talking mouth is: syllables, with pauses."""
    v = math.sin(t * 15 + seed) * 0.6 + math.sin(t * 9.3 + 2 * seed) * 0.4
    gate = math.sin(t * 1.7 + seed * 3) > -0.5
    return max(0.0, v) if gate else 0.0


def blinking(t, seed=0.0):
    return (t * 0.37 + seed * 0.13) % 1.0 < 0.04


def face(img, x, y, r, skin, t=0.0, talk=0.0, look=(0.0, 0.0), mood=0, seed=0.0, eyes=2, a=1.0, rot=0.0, flat=1.0):
    """A head: r is its half-width. talk 0..1 opens the mouth; mood -1 sad, 0, 1 happy.
    rot tips it (radians, clockwise); flat squashes it top to bottom."""
    c, s = math.cos(rot), math.sin(rot)

    def at(dx, dy):
        dy *= flat
        return x + dx * c - dy * s, y + dx * s + dy * c

    ellipse(img, x, y, r, r * 1.12 * flat, skin, a=a, rot=rot)
    xs = [0.0] if eyes == 1 else [r * (i / (eyes - 1) - 0.5) * 0.85 for i in range(eyes)]
    er = r * (0.26 if eyes == 1 else 0.21)
    for ex in xs:
        if blinking(t, seed):
            line(img, *at(ex - er, -r * 0.18), *at(ex + er, -r * 0.18), (.1, .05, .05), w=max(1, r * 0.08), a=a)
        else:
            ellipse(img, *at(ex, -r * 0.18), er, er * 1.1 * flat, WHITE, a=a, rot=rot)
            ellipse(img, *at(ex + look[0] * er * 0.45, -r * 0.18 + look[1] * er * 0.45), er * 0.5, er * 0.55 * flat,
                    (.05, .05, .1), a=a, rot=rot)
    mw = r * 0.42
    if talk > 0.05:
        ellipse(img, *at(0, r * 0.5), mw * (0.8 + 0.2 * talk), r * (0.06 + 0.26 * talk) * flat, (.35, .05, .08), a=a, rot=rot)
    else:
        bend = mood * r * 0.12
        ends = [at(-mw, r * 0.5 - bend), at(0, r * 0.5 + bend), at(mw, r * 0.5 - bend)]
        for p, q in zip(ends, ends[1:]):
            line(img, *p, *q, (.35, .08, .08), w=max(1, r * 0.09), a=a)


def body(img, x, y, r, shirt, a=1.0):
    """Shoulders under a head of half-width r centred at (x, y)."""
    ellipse(img, x, y + r * 2.6, r * 1.7, r * 1.6, shirt, a=a)


def person(img, x, y, r, skin, shirt, t=0.0, talk=0.0, look=(0.0, 0.0), mood=0, seed=0.0, eyes=2):
    body(img, x, y, r, shirt)
    face(img, x, y, r, skin, t, talk, look, mood, seed, eyes)


LEG = 0.42      # a toon's legs, as a fraction of its height: its hips are this far above its feet


def toon(img, x, y, h, skin, shirt, t=0.0, walk=0.0, rot=0.0, arms=(0.3, 0.3), flat=1.0, look=(0.0, 0.0), mood=0,
         talk=0.0, seed=0.0, pants=(.2, .2, .35), headr=None):
    """A cartoon person with its hips at (x, y), h tall standing. walk swings the legs; rot tips the
    whole figure about the hips (radians, clockwise); arms are each arm's angle from hanging down,
    outwards positive (pi/2 straight out, pi straight up); flat squashes it (a piano's work).
    Returns where the head went, (x, y, r)."""
    c, s = math.cos(rot), math.sin(rot)

    def at(dx, dy):
        dy *= flat
        return x + dx * c - dy * s, y + dx * s + dy * c

    w = max(1.5, h * 0.09)
    for k in (-1, 1):
        a = walk * 0.55 * math.sin(t * 10) * k
        line(img, *at(k * h * 0.05, 0), *at(k * h * 0.05 + LEG * h * math.sin(a), LEG * h * math.cos(a)), pants, w)
    sx, sy = 0, -h * 0.3
    for k, a in zip((-1, 1), arms):
        line(img, *at(k * h * 0.12, sy), *at(k * h * 0.12 + k * math.sin(a) * h * 0.28, sy + math.cos(a) * h * 0.28),
             shirt, w * 0.85)
        ellipse(img, *at(k * h * 0.12 + k * math.sin(a) * h * 0.3, sy + math.cos(a) * h * 0.3), w * 0.7, w * 0.7, skin)
    ellipse(img, *at(0, -h * 0.17), h * 0.15 / max(0.5, flat) ** 0.5, h * 0.2 * flat, shirt, rot=rot)
    r = headr or h * 0.14
    hx, hy = at(0, -h * 0.34 - r * 1.05)
    face(img, hx, hy, r, skin, t, talk, look, mood, seed, rot=rot, flat=flat)
    return hx, hy, r


def hand(x, y, h, a, k=1, rot=0.0):
    """Where a toon's hand is: hips at (x, y), arm k (-1 left, 1 right) at angle a, as toon() draws it."""
    dx, dy = k * h * 0.12 + k * math.sin(a) * h * 0.3, -h * 0.3 + math.cos(a) * h * 0.3
    c, s = math.cos(rot), math.sin(rot)
    return x + dx * c - dy * s, y + dx * s + dy * c


def stick(img, x, y, h, rgb, t=0.0, wobble=0.0, arms=0.0):
    """A stick figure, feet at (x, y), h tall; wobble leans it, arms raises them (0 down, 1 up)."""
    lean = wobble * math.sin(t * 9)
    hip = (x + lean * 0.3, y - h * 0.45)
    neck = (x + lean, y - h * 0.8)
    w = max(1.0, h / 14)
    line(img, x - h * 0.15, y, *hip, rgb, w)
    line(img, x + h * 0.15, y, *hip, rgb, w)
    line(img, *hip, *neck, rgb, w)
    for s in (-1, 1):
        ay = neck[1] + h * 0.25 - arms * h * 0.5
        line(img, *neck, neck[0] + s * h * 0.22, ay, rgb, w)
    ellipse(img, neck[0], neck[1] - h * 0.1, h * 0.1, h * 0.11, rgb)


def bee(img, x, y, t, r=2.5):
    ellipse(img, x, y, r * 1.3, r, (1, .8, .1))
    line(img, x - r * 0.3, y - r, x - r * 0.3, y + r, BLACK, w=max(1, r * 0.45))
    ellipse(img, x + r * 0.2, y - r * 1.1, r * 0.7, r * (0.35 + 0.3 * abs(math.sin(t * 60))), (.85, .9, 1), a=0.8)


# ---------------------------------------------------------------- words

def wrap(s, width=124, scale=1):
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and draw.text_width(trial, scale) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur] if cur else lines


def typed(s, t, cps=20.0):
    """s as typed so far, t seconds after it started."""
    return s[:max(0, int(t * cps))]


def words(img, s, y, rgb=WHITE, scale=1, shadow=BLACK, width=124, x=64):
    """Centred, wrapped text from row y down, with a drop shadow. Returns the row below it."""
    for ln in wrap(s, width, scale):
        if shadow is not None:
            draw.text(img, ln, x + scale, y + scale, shadow, center=True, scale=scale)
        draw.text(img, ln, x, y, rgb, center=True, scale=scale)
        y += LINE * scale
    return y


def caption(img, s, y=None, rgb=WHITE, bg=BLACK, a=0.75):
    """Subtitles on a dark band, at the bottom unless y is given."""
    lines = wrap(s)
    if not lines:
        return
    h = LINE * len(lines) + 2
    y = N - h if y is None else y
    rect(img, 0, y, N, y + h, bg, a)
    for i, ln in enumerate(lines):
        draw.text(img, ln, 64, y + 1 + LINE * i, rgb, center=True)


def ticker(img, s, y, t, speed=30.0, rgb=WHITE, bg=(.6, 0, 0)):
    """A crawl across a band at row y."""
    rect(img, 0, y, N, y + LINE + 1, bg)
    w = draw.text_width(s)
    x = N - (t * speed) % (w + N)
    draw.text(img, s, x, y + 1, rgb)
    if x + w < 0:
        draw.text(img, s, x + w + N, y + 1, rgb)


def cue(t, cues):
    """The cue playing at time t, from [(start, value), ...] in order: (index, value, time into it)."""
    i = 0
    while i + 1 < len(cues) and t >= cues[i + 1][0]:
        i += 1
    return i, cues[i][1], t - cues[i][0]
