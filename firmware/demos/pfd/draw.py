"""Drawing helpers on float RGB images, (128, 128, 3), 0..1 in perceptual (pre-gamma) units."""
import math

import numpy as np

from knob_renderer import hsv  # noqa: F401  (re-exported for demos)

N = 128
Y, X = np.mgrid[0:N, 0:N].astype(np.float32)


def blank():
    return np.zeros((N, N, 3), np.float32)


def hsv1(h, s=1.0, v=1.0):
    """One HSV colour as an (r, g, b) float tuple."""
    return tuple(float(c) for c in hsv(np.array(h), np.array(s), np.array(v)))


def disc(img, x, y, r, rgb, soft=1.0, op="max"):
    """A filled disc with a soft edge, drawn into img in place. op is "max", "add" or "over" (paint)."""
    h, w = img.shape[:2]
    x0, x1 = max(0, int(x - r - soft - 1)), min(w, int(x + r + soft + 2))
    y0, y1 = max(0, int(y - r - soft - 1)), min(h, int(y + r + soft + 2))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.ogrid[y0:y1, x0:x1]
    d = np.hypot(xx - x, yy - y)
    a = np.clip((r + soft - d) / (2 * soft) + 0.5, 0, 1)[..., None] if soft else (d <= r)[..., None]
    patch = a * np.asarray(rgb, np.float32)
    if op == "add":
        img[y0:y1, x0:x1] += patch
    elif op == "over":
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + patch
    else:
        np.maximum(img[y0:y1, x0:x1], patch, out=img[y0:y1, x0:x1])


def ring(img, x, y, r, rgb, width=0.8):
    """An antialiased circle outline, drawn with max."""
    x0, x1 = max(0, int(x - r - 2)), min(N, int(x + r + 3))
    y0, y1 = max(0, int(y - r - 2)), min(N, int(y + r + 3))
    if x0 >= x1 or y0 >= y1:
        return
    d = np.hypot(X[y0:y1, x0:x1] - x, Y[y0:y1, x0:x1] - y)
    a = np.clip(1 - np.abs(d - r) / width, 0, 1)[..., None]
    np.maximum(img[y0:y1, x0:x1], a * np.asarray(rgb, np.float32), out=img[y0:y1, x0:x1])


def poly(img, pts, rgb, mask_out=None):
    """Fill a polygon (even-odd rule, pixel centres) with a flat colour.
    If mask_out is given, OR the coverage into it as well."""
    pts = np.asarray(pts, np.float32)
    h, w = img.shape[:2]
    x0, y0 = max(0, int(np.floor(pts[:, 0].min()))), max(0, int(np.floor(pts[:, 1].min())))
    x1, y1 = min(w, int(np.ceil(pts[:, 0].max())) + 1), min(h, int(np.ceil(pts[:, 1].max())) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    py, px = np.ogrid[y0:y1, x0:x1]
    px, py = np.broadcast_arrays(px + 0.5, py + 0.5)
    inside = np.zeros(px.shape, bool)
    xa, ya = pts[:, 0], pts[:, 1]
    xb, yb = np.roll(xa, -1), np.roll(ya, -1)
    for i in range(len(pts)):
        if ya[i] == yb[i]:
            continue
        cross = (ya[i] > py) != (yb[i] > py)
        xint = xa[i] + (py - ya[i]) * (xb[i] - xa[i]) / (yb[i] - ya[i])
        inside ^= cross & (px < xint)
    img[y0:y1, x0:x1][inside] = rgb
    if mask_out is not None:
        mask_out[y0:y1, x0:x1] |= inside


def segment(x0, y0, x1, y1, step=0.5):
    """Points along a line segment, at most `step` apart (including both ends)."""
    n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
    s = np.linspace(0, 1, n + 1)
    return x0 + (x1 - x0) * s, y0 + (y1 - y0) * s


def plot(img, xs, ys, rgb, op="add"):
    """Single pixels at rounded (xs, ys); rgb is one colour or one per point. Off-screen points are skipped."""
    xi, yi = np.rint(xs).astype(np.int32), np.rint(ys).astype(np.int32)
    ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
    rgb = np.broadcast_to(np.asarray(rgb, np.float32), (len(xi), 3))[ok]
    if op == "add":
        np.add.at(img, (yi[ok], xi[ok]), rgb)
    else:
        img[yi[ok], xi[ok]] = np.maximum(img[yi[ok], xi[ok]], rgb)


# ---------------------------------------------------------------- text

_font = None
_glyphs = {}


def _mask(s):
    global _font
    if s not in _glyphs:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:             # no Pillow: text is a nicety, not a requirement
            _glyphs[s] = np.zeros((1, 1), np.float32)
            return _glyphs[s]
        if _font is None:
            _font = ImageFont.load_default_imagefont() if hasattr(ImageFont, "load_default_imagefont") \
                else ImageFont.load_default()
        x0, y0, x1, y1 = _font.getbbox(s)
        im = Image.new("L", (max(1, x1), max(1, y1)))
        ImageDraw.Draw(im).text((0, 0), s, fill=255, font=_font)
        _glyphs[s] = np.asarray(im, np.float32)[y0:] / 255.0
    return _glyphs[s]


def text_width(s, scale=1):
    return _mask(s).shape[1] * scale


def text(img, s, x, y, rgb, center=False, scale=1):
    """Draw s with its top-left at (x, y), or centred on x; scale blows the bitmap font up."""
    m = _mask(s)
    if scale > 1:
        m = np.kron(m, np.ones((scale, scale), np.float32))
    h, w = m.shape
    x = int(round(x - w / 2)) if center else int(x)
    y = int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    dx0, dy0 = max(0, x), max(0, y)
    w2, h2 = min(w - sx0, N - dx0), min(h - sy0, N - dy0)
    if w2 <= 0 or h2 <= 0:
        return
    a = m[sy0:sy0 + h2, sx0:sx0 + w2, None]
    region = img[dy0:dy0 + h2, dx0:dx0 + w2]
    region[:] = region * (1 - a) + a * np.asarray(rgb, np.float32)
