"""The channels: short, very weird TV from other dimensions.

A show draws itself whole at t seconds since you tuned in, from a fixed script: change
channel and come back, and it starts over. `length` is how long it runs before the surf
moves on (or loops, if you stay); `reception` 0..1 is how much snow the TV puts over it.
"""
import math

import numpy as np

from .. import draw
from ..draw import N, X, Y
from . import headlines
from .kit import (BLACK, LEG, LINE, SKINS, WHITE, bee, body, caption, chatter, cue, ellipse, face, grey, hand, line,
                  person, poly, rays, rect, star, stick, ticker, toon, typed, vgrad, words, wrap)


class Show:
    num = 0
    title = ""
    net = ""                # the network's bug, in the corner
    length = 10.0
    reception = 0.0

    def tune(self):
        """Just tuned in: a chance to pick something new."""

    def draw(self, img, t):
        pass


def _bowl(img, x, y, r, soup=(.9, .5, .15)):
    ellipse(img, x, y, r, r * 0.65, (.92, .92, .86), half="bottom")
    ellipse(img, x, y, r * 0.95, r * 0.16, soup)


def _steam(img, x, y, t, n=3, h=14):
    for k in range(n):
        px = x + (k - (n - 1) / 2) * 6
        pts = [(px + 2 * math.sin(t * 5 + k + j * 0.9), y - j * h / 5) for j in range(6)]
        for (a, b), (c, d) in zip(pts, pts[1:]):
            line(img, a, b, c, d, (.85, .85, .85), w=1, a=0.6)


class SoupHat(Show):
    num, title, net, length = 2, "SOUP HAT", "SHOP-Z", 11.0

    def draw(self, img, t):
        i, _, lt = cue(t, [(0, 0), (3.6, 1), (7.4, 2)])
        if i == 0:                                  # the sad, grey "before"
            vgrad(img, (.4, .35, .35), (.12, .1, .1))
            slosh = 4 * math.sin(t * 6)
            person(img, 64, 46, 15, SKINS[0], (.3, .4, .8), t, mood=-1, look=(slosh / 4, 1), seed=1)
            _bowl(img, 64 + slosh, 88, 22)
            for k in range(6):
                ellipse(img, 48 + k * 6 + slosh, 96 + (t * 50 + k * 13) % 34, 1.4, 2.2, (.9, .5, .15))
            grey(img, 0.85)
            caption(img, "TIRED OF HOLDING SOUP?", 4)
            if lt > 1.8:
                caption(img, "THERE'S A BETTER WAY.")
        elif i == 1:                                # the bright "after"
            rays(img, 64, 50, (1, .75, .1), (1, .55, .05), rot=t * 0.6)
            person(img, 64, 54, 15, SKINS[0], (.3, .4, .8), t, mood=1, seed=1)
            _bowl(img, 64, 34, 17)
            _steam(img, 64, 32, t)
            star(img, 106, 20, 17 + math.sin(t * 12), (.95, .1, .2), rot=t)
            draw.text(img, "NEW!", 106, 15, WHITE, center=True)
            words(img, "SOUP HAT!", 98 + 3 * abs(math.sin(lt * 5)), (.95, .1, .2), scale=2, shadow=WHITE)
        else:                                       # the pitch
            vgrad(img, (.1, .1, .45), (.35, .05, .4))
            words(img, "ONLY 3 PAYMENTS OF", 8, (1, 1, .6))
            hue = (1, .9, .1) if int(lt * 4) % 2 else (1, .3, .6)
            words(img, "$SOUP", 34, hue, scale=3)
            _bowl(img, 64, 84, 14)
            _steam(img, 64, 82, t)
            ticker(img, "CALL 1-800-SOUP-HAT NOW * OPERATORS ARE SOUP * ", 105, lt, 40)


class IsItAHat(Show):
    num, title, net, length = 3, "IS IT A HAT?", "PUB-ACCESS", 12.0
    ITEMS = [("cat", "NOT A HAT", (.9, .15, .1)), ("fish", "HAT!", (.15, .85, .2)), ("house", "...MAYBE", (.9, .8, .1))]

    def __init__(self):
        self.bg = np.zeros((N, N, 3), np.float32)
        wrinkle = 0.06 * np.sin(X * 0.25 + 3 * np.sin(Y * 0.07)) + 0.04 * np.sin(Y * 0.4 + X * 0.05)
        self.bg[:] = (np.array((.45, .55, .75), np.float32) + wrinkle[..., None])

    def draw(self, img, t):
        img[:] = self.bg
        i, (item, verdict, col), lt = cue(t, [(0, self.ITEMS[0]), (4, self.ITEMS[1]), (8, self.ITEMS[2])])
        hx, hy = 64, 66
        person(img, hx, hy, 14, SKINS[1], (.55, .2, .2), t, talk=chatter(t) if lt < 1.8 else 0,
               mood=1 if verdict == "HAT!" else -1 if lt > 1.8 else 0, look=(0, -1) if lt < 1 else (0, 0), seed=3)
        top = hy - 16
        if item == "cat":
            ellipse(img, hx, top - 4, 16, 7, (.95, .55, .15))
            for s in (-1, 1):
                poly(img, [(hx + s * 10, top - 9), (hx + s * 15, top - 18), (hx + s * 16, top - 7)], (.95, .55, .15))
            line(img, hx + 15, top - 4, hx + 22 + 3 * math.sin(t * 6), top - 14, (.95, .55, .15), w=3)
            for s in (-1, 1):
                ellipse(img, hx + s * 6, top - 6, 1.6, 1.2 if not (t % 2.3 < 0.15) else 0.3, (.1, .4, .1))
        elif item == "fish":
            ellipse(img, hx, top - 5, 17, 6, (.6, .75, .85))
            poly(img, [(hx + 15, top - 5), (hx + 24, top - 12 + math.sin(t * 9)), (hx + 24, top + 2 + math.sin(t * 9))],
                 (.5, .65, .8))
            ellipse(img, hx - 10, top - 6, 1.6, 1.6, BLACK)
        else:
            rect(img, hx - 10, top - 14, hx + 10, top, (.85, .8, .7))
            poly(img, [(hx - 14, top - 13), (hx, top - 25), (hx + 14, top - 13)], (.7, .2, .15))
            rect(img, hx - 3, top - 8, hx + 2, top, (.4, .25, .1))
            rect(img, hx + 4, top - 11, hx + 8, top - 7, (1, .9, .4))
        rect(img, 0, 0, N, 13, (.35, .1, .45))
        words(img, "IS IT A HAT?", 1, (1, .9, .2))
        if lt < 1.8:
            caption(img, ["OK. NEXT ITEM.", "THIS ONE'S TRICKY.", "FINAL ITEM. FOLKS."][i])
        else:
            s = 1 + (lt < 2.0)
            w = draw.text_width(verdict, 2) + 8
            rect(img, 64 - w / 2, 92, 64 + w / 2, 118, col)
            rect(img, 64 - w / 2 + 2, 94, 64 + w / 2 - 2, 116, (.1, .1, .1))
            words(img, verdict, 94 + (s - 1) * 2, col, scale=2, shadow=None)


class News(Show):
    num, title, net, length = 4, "NEWS AT NEVER", "ZNN", 12.0
    STORIES = [(0, "THE MOON HAS LEFT. IT TOOK NOTHING."),
               (4, "LOCAL MAN BECOMES A HALLWAY"),
               (8, "TUESDAY CANCELLED DUE TO FOG")]

    GAGS = ["STOCKS: SCREAMING", "GRAVITY DOWN 2%", "SOUP UP", "DOGS NOW TWO DOGS", "SKY REPORTED 'MOSTLY FINE'"]

    def __init__(self):
        self.crawl = " * ".join(self.GAGS) + " * "

    def tune(self):
        """The crawl mixes our news with a few of this dimension's headlines."""
        rng = np.random.default_rng()
        news = headlines.get()
        mix = list(self.GAGS) + list(rng.choice(news, min(3, len(news)), replace=False))
        rng.shuffle(mix)
        self.crawl = " * ".join(mix) + " * "

    def _picture(self, img, i, lt):
        x0, y0, x1, y1 = 72, 10, 122, 46
        rect(img, x0 - 1, y0 - 1, x1 + 1, y1 + 1, WHITE)
        rect(img, x0, y0, x1, y1, (.02, .02, .1))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if i == 0:
            d = min(1.0, lt / 3.5)
            ellipse(img, cx + 18 * d, cy - 8 * d, 12 * (1 - 0.7 * d), 12 * (1 - 0.7 * d), (.85, .85, .75))
            face(img, cx + 18 * d, cy - 8 * d, 7 * (1 - 0.7 * d), (.85, .85, .75), lt, mood=1, look=(1, -1), seed=5)
        elif i == 1:
            for k in range(5):
                f = 0.5 ** k
                rect(img, cx - 25 * f, cy - 18 * f, cx + 25 * f, cy + 18 * f, (.35 + .1 * k, .3, .2 + .08 * k))
            for sx in (-1, 1):
                for sy in (-1, 1):
                    line(img, cx + sx * 25, cy + sy * 18, cx + sx * 1.6, cy + sy * 1.1, (.15, .1, .05), w=1)
            face(img, cx, cy, 3, SKINS[0], lt, seed=6)
        else:
            rect(img, cx - 13, cy - 14, cx + 13, cy + 14, (.95, .95, .9))
            rect(img, cx - 13, cy - 14, cx + 13, cy - 7, (.8, .1, .1))
            draw.text(img, "TUE", cx, cy - 4, BLACK, center=True)
            if lt > 1:
                line(img, cx - 11, cy - 12, cx + 11, cy + 12, (.9, 0, 0), w=2)
                line(img, cx + 11, cy - 12, cx - 11, cy + 12, (.9, 0, 0), w=2)

    def draw(self, img, t):
        vgrad(img, (.05, .1, .3), (.02, .02, .1))
        for k in range(8):
            rect(img, k * 16 + 4, 0, k * 16 + 6, 70, (.08, .14, .38))
        i, story, lt = cue(t, self.STORIES)
        body(img, 40, 40, 11, (.12, .12, .16))
        rect(img, 37, 58, 43, 70, (.7, .1, .1))
        for k, hx in enumerate((29, 51)):          # two heads, taking turns
            talking = (math.sin(t * 1.3) > 0) == (k == 0)
            face(img, hx, 38, 9, SKINS[k * 2], t, talk=chatter(t, k) if talking else 0,
                 look=(1 if k == 0 else -1, 0) if not talking else (0, 0), seed=k * 4)
        rect(img, 0, 70, N, 92, (.3, .3, .38))
        rect(img, 0, 72, N, 74, (.8, .1, .1))
        self._picture(img, i, lt)
        rect(img, 0, 78, 46, 89, (.8, .05, .05))
        draw.text(img, "BREAKING", 2, 78, WHITE)
        caption(img, typed(story, lt, 30), 89, (1, 1, 1), (.05, .05, .2), a=0.9)
        ticker(img, self.crawl, N - LINE - 1, t, 32, (1, 1, .7), (.1, .1, .3))


class Weather(Show):
    num, title, net, length = 7, "WEATHER-ISH", "KBLRG", 12.0

    def __init__(self):
        f = np.sin(X * 0.07) + np.sin(Y * 0.09 + 1) + np.sin((X + Y) * 0.05 + 2) + 0.4 * np.sin(X * 0.2 + Y * 0.15)
        land = f > 0.5
        coast = (f > 0.35) & ~land
        self.map = np.empty((N, N, 3), np.float32)
        self.map[:] = (.08, .25, .6)
        self.map[land] = (.2, .55, .2)
        self.map[coast] = (.3, .45, .7)
        rng = np.random.default_rng(7)
        self.bees = rng.random((24, 4))

    def draw(self, img, t):
        img[:] = self.map
        i, _, lt = cue(t, [(0, 0), (4, 1), (8, 2)])
        if i == 0:
            for dx in (-12, 0, 12, 6, -6):
                ellipse(img, 82 + dx, 32 - abs(dx) * 0.4, 11, 8, (.75, .75, .8))
            for k in range(10):
                x = 68 + (k * 37) % 30
                y = 40 + (t * 30 + k * 11) % 50
                rect(img, x, y, x + 3, y + 4, (1, 1, .95))
                rect(img, x + 1, y + 3, x + 2, y + 4, (.6, .3, .3))
            words(img, "TODAY: TEETH", 2, (1, 1, .3))
        elif i == 1:
            rect(img, 40, 30, 126, 84, (.05, .05, .2), a=0.8)
            words(img, "HIGH", 34, (1, .5, .3), x=83)
            words(img, "4000", 44, (1, .5, .3), scale=2, x=83)
            words(img, "LOW:", 66, (.5, .7, 1), x=83)
            words(img, "EMOTIONALLY", 74, (.5, .7, 1), x=83)
        else:
            words(img, "90% CHANCE", 2, (1, .9, .2), scale=2)
            words(img, "OF BEES", 24, (1, .9, .2), scale=2)
            for k, (a, b, c, d) in enumerate(self.bees):
                x = 50 + 70 * a + 10 * math.sin(t * (3 + 3 * c) + k)
                y = 50 + 40 * b + 8 * math.sin(t * (4 + 2 * d) + 2 * k)
                bee(img, x, y, t + k, 2.2)
        # the weatherman, pointing at it
        person(img, 20, 86, 9, SKINS[2], (.6, .1, .5), t, talk=chatter(t, 2), look=(1, 0), seed=2)
        line(img, 33, 101, 46 + 4 * math.sin(t * 2), 82, SKINS[2], w=3)


class Square(Show):
    num, title, net, length = 9, "PLANET SQUARE", "NAT-GEOMETRIC", 13.0
    LINES = [(0, "THE SQUARE HAS NO KNEES."), (3, "AND YET... IT MIGRATES."), (6, "NOBODY KNOWS WHERE."),
             (8.5, "THE TRIANGLE WAITS."), (11, "NOT EVEN THE SQUARE.")]

    def __init__(self):
        rng = np.random.default_rng(9)
        self.herd = [(rng.random() * 180, 4 + rng.random() * 5, 60 + rng.random() * 14, rng.random() * 6) for _ in range(9)]
        self.grass = rng.random(64)

    def draw(self, img, t):
        vgrad(img, (.95, .55, .2), (.6, .15, .3), 0, 72)
        vgrad(img, (.35, .15, .1), (.12, .05, .05), 72, N)
        ellipse(img, 86, 60, 16, 16, (1, .85, .4))
        rect(img, 0, 72, N, N, (.3, .12, .08))
        for s, size, y, ph in sorted(self.herd, key=lambda h: h[2]):
            x = (s + t * size * 2.4) % 180 - 26
            hop = abs(math.sin(t * 5 + ph)) * 2.5
            rect(img, x, y + 14 - size * 2 - hop, x + size * 2, y + 14 - hop, (.15, .05, .05))
        x = 30 + t * 3
        hop = abs(math.sin(t * 4)) * 4
        rect(img, x, 100 - 22 - hop, x + 22, 100 - hop, (.08, .03, .03))
        ellipse(img, x + 17, 100 - 16 - hop, 2, 2, WHITE)
        if t > 8.5:                                 # in the grass
            rise = min(1.0, (t - 8.5) / 1.2) * 20
            poly(img, [(100, 104 - rise), (90, 106), (110, 106)], (.1, .03, .03))
            for dx in (-2, 2):
                ellipse(img, 100 + dx, 100 - rise * 0.6, 1, 1, (1, .9, .2))
        for k, g in enumerate(self.grass):
            gx = k * 2
            line(img, gx, 106, gx + 2 * math.sin(t * 2 + k), 106 - 4 - 6 * g, (.06, .02, .02), w=1)
        rect(img, 0, 106, N, N, (.06, .02, .02))
        caption(img, cue(t, self.LINES)[1], None, (1, 1, .85), BLACK, a=0.0)


class Standing(Show):
    num, title, net, length = 11, "PRO STANDING", "ESPN-9", 11.0

    def __init__(self):
        rng = np.random.default_rng(11)
        self.field = np.empty((N, N, 3), np.float32)
        self.field[:] = np.where(((X // 16) % 2 == 0)[..., None], (.15, .5, .15), (.12, .42, .12))
        self.crowd = (rng.random((10, N, 3)) * 0.8 + 0.1).astype(np.float32)

    def draw(self, img, t):
        img[:] = self.field
        flash = 1.0 if 7 < t < 8.5 else 0.45
        on = np.random.default_rng(int(t * 6)).random((10, N, 1)) < 0.6
        img[14:24] = self.crowd * np.where(on, flash, 0.25)
        rect(img, 0, 24, N, 26, (.9, .9, .9))
        rect(img, 0, 0, N, 13, (.05, .05, .05))
        yeen = "-0.5" if t > 7 else "0.0"
        draw.text(img, f"GLORB 0.0  YEEN {yeen}", 64, 1, (1, .8, .2), center=True)
        rect(img, 0, 26, N, 30, (.08, .3, .08))
        stick(img, 42, 100, 44, (.95, .95, .95), t)
        stick(img, 86, 100, 44, (1, .55, .15), t, wobble=4 if 6.6 < t < 7.4 else 0)
        draw.text(img, "Q4  " + f"{9.99 - t * 0.0009:.4f}", 64, 32, (1, 1, 1), center=True)
        caption(img, cue(t, [(0, "AND HE'S... STANDING."), (3, "INCREDIBLE POSTURE FROM YEEN TODAY."),
                             (6.6, "OH! A WOBBLE!"), (8.5, "THAT'LL COST HIM.")])[1])


class Doors(Show):
    num, title, net, length = 13, "DOOR WORLD", "SHOP-Z", 11.0
    WALLS = [(.85, .75, .55), (.5, .7, .55), (.7, .5, .6), (.45, .55, .75)]

    def draw(self, img, t):
        z = (t * 0.55) % 1.0
        lvl = int(t * 0.55)
        cx, cy = 64, 70
        h = 110 * 2 ** z
        img[:] = self.WALLS[lvl % 4]
        k = 0
        while h > 2:
            w = h * 0.5
            x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
            rect(img, x0 - h * 0.05, y0 - h * 0.05, x1 + h * 0.05, y1, (.35, .2, .1))
            rect(img, x0, y0, x1, y1, self.WALLS[(lvl + k + 1) % 4])
            sw = w * 0.32
            poly(img, [(x0, y0), (x0 + sw, y0 + h * 0.07), (x0 + sw, y1 - h * 0.07), (x0, y1)], (.55, .32, .15))
            ellipse(img, x0 + sw * 0.75, cy, max(0.6, h * 0.02), max(0.6, h * 0.02), (1, .8, .2))
            h *= 0.5
            cy = y1 - h / 2 - (h * 0.02)
            k += 1
        i, s, lt = cue(t, [(0, "DOOR WORLD!"), (2.5, "DOORS THAT OPEN ONTO MORE DOORS."), (5.5, "NO ROOMS. NO WALLS. NO WAY BACK."),
                           (8.2, "BUY ONE GET ONE GET ONE GET ONE GET ONE GET ONE")])
        caption(img, typed(s, lt, 22) if i == 3 else s, 2, (1, 1, .6))
        star(img, 108, 108, 16, (.95, .1, .2), rot=t)
        draw.text(img, "$9", 108, 98, WHITE, center=True)
        draw.text(img, "DOOR", 108, 107, WHITE, center=True)


class Mouth(Show):
    num, title, net, length = 18, "MR. MOUTH", "KIDZ+", 12.0
    SONG = [(0, ["COUNT", "WITH", "MR.", "MOUTH!"]), (3, ["ONE,", "TWO,", "BLUE!"]),
            (6, ["SEVEN,", "EIGHT,", "SOUP!"]), (9, ["NINE,", "TEN,", "FOREVER!"])]

    def draw(self, img, t):
        vgrad(img, (.55, .8, 1), (1, .75, .85))
        for k, c in enumerate([(1, .3, .3), (1, .7, .2), (1, 1, .3), (.3, .9, .4), (.3, .6, 1)]):
            r = 80 - k * 5
            ring = np.abs(np.hypot(X - 64, Y - 128) - r) < 2.5
            img[ring] = img[ring] * 0.4 + np.asarray(c, np.float32) * 0.6
        sr = 11 + math.sin(t * 2)
        for k in range(10):
            a = k * math.pi / 5 + t
            line(img, 18 + sr * math.cos(a), 18 + sr * math.sin(a), 18 + (sr + 6) * math.cos(a),
                 18 + (sr + 6) * math.sin(a), (1, .85, .1), w=2)
        face(img, 18, 18, 10, (1, .85, .1), t, mood=1, seed=8)
        i, song, lt = cue(t, self.SONG)
        per = 3 / len(song)
        w = min(len(song) - 1, int(lt / per))
        sing = abs(math.sin(lt / per * math.pi))
        my = 56 + 3 * math.sin(t * 2 * math.pi)
        ellipse(img, 70, my, 34, 10 + 14 * sing, (.85, .05, .2))
        ellipse(img, 70, my, 28, 5 + 12 * sing, (.25, 0, .05))
        rect(img, 50, my - 4 - 12 * sing, 90, my - 1 - 12 * sing, WHITE)
        ellipse(img, 70, my + 2 + 8 * sing, 12, 3 * sing + 0.5, (.9, .4, .5))
        for k in range(3):                         # notes, rising
            ny = 100 - ((t * 18 + k * 30) % 90)
            nx = 104 + 10 * math.sin(t * 2 + k * 2) - k * 6
            ellipse(img, nx, ny, 2.5, 2, (.3, .2, .6), rot=-0.4)
            line(img, nx + 2, ny, nx + 2, ny - 8, (.3, .2, .6), w=1)
        text = " ".join(song)
        x = 64 - draw.text_width(text) / 2
        rect(img, 0, 104, N, 118, (.2, .1, .4), a=0.7)
        for k, wd in enumerate(song):
            draw.text(img, wd, x, 106, (1, 1, .2) if k == w else WHITE)
            if k == w:
                bx = x + draw.text_width(wd) / 2
                ellipse(img, bx, 101 - 6 * abs(math.sin((lt / per) * math.pi)), 2.5, 2.5, (1, .3, .3))
            x += draw.text_width(wd + " ")


class Wheel(Show):
    num, title, net, length = 23, "WHEEL OF REGRET", "GZN", 11.0
    SEGS = [("BEES", (.95, .75, .1)), ("TAX", (.2, .5, .9)), ("DAD", (.85, .2, .3)), ("AGAIN", (.5, .2, .8)),
            ("SOUP", (.95, .5, .1)), ("YES", (.2, .75, .35)), ("LEGS", (.9, .4, .7)), ("AGAIN", (.1, .7, .8))]
    CX, CY, R = 64, 66, 42
    SPIN = 5.0

    def __init__(self):
        dx, dy = X + 0.5 - self.CX, Y + 0.5 - self.CY
        self.r = np.hypot(dx, dy)
        self.ang = np.arctan2(dy, dx)
        self.cols = np.array([c for _, c in self.SEGS], np.float32)
        n = len(self.SEGS)
        self.final = -math.pi / 2 - 3.5 * 2 * math.pi / n + 2 * math.pi * 6     # lands on AGAIN

    def _rot(self, t):
        if t > 8.4:                                 # and around we go again
            u = t - 8.4
            return self.final + u * u * 2
        u = min(1.0, t / self.SPIN)
        return self.final * (1 - (1 - u) ** 3)

    def draw(self, img, t):
        vgrad(img, (.15, .02, .25), (.02, .0, .05))
        for k, x in enumerate((20, 108)):            # spotlights
            cone = np.clip(1 - np.abs(X - x - (Y - 0) * 0.25 * (1 if k else -1)) / (6 + Y * 0.2), 0, 1)
            img += cone[..., None] * np.array((.25, .2, .1), np.float32) * (0.6 + 0.4 * math.sin(t * 3 + k))
        rot = self._rot(t)
        n = len(self.SEGS)
        seg = (np.floor(((self.ang - rot) % (2 * math.pi)) / (2 * math.pi / n))).astype(np.int32) % n
        inside = self.r < self.R
        img[inside] = self.cols[seg[inside]]
        rim = (self.r >= self.R) & (self.r < self.R + 3)
        img[rim] = (.95, .85, .4)
        for k in range(16):
            a = k * 2 * math.pi / 16
            on = (k + int(t * 8)) % 2
            ellipse(img, self.CX + (self.R + 1.5) * math.cos(a), self.CY + (self.R + 1.5) * math.sin(a), 1.5, 1.5,
                    (1, 1, .7) if on else (.4, .3, .1))
        for j, (label, _) in enumerate(self.SEGS):
            a = rot + (j + 0.5) * 2 * math.pi / n
            draw.text(img, label, self.CX + 27 * math.cos(a), self.CY + 27 * math.sin(a) - 5, WHITE, center=True)
        ellipse(img, self.CX, self.CY, 5, 5, (.95, .85, .4))
        poly(img, [(self.CX - 5, self.CY - self.R - 8), (self.CX + 5, self.CY - self.R - 8), (self.CX, self.CY - self.R + 2)],
             (1, 1, 1))
        if 5.0 < t < 8.4:
            if int(t * 6) % 2:
                img *= 1.25
            words(img, "AGAIN!", 92 - 4 * abs(math.sin(t * 6)), (1, 1, .3), scale=3)
        caption(img, cue(t, [(0, "SPIN THE WHEEL OF REGRET!"), (5, ""), (8.4, "SPIN AGAIN. FOREVER.")])[1], 0)


class Glorpax(Show):
    num, title, net, length = 27, "GLORPAX", "KBLRG", 13.0
    EFFECTS = ["SIDE EFFECTS", "MAY INCLUDE:", "", "BECOMING TWO PEOPLE,", "KNOWING THE SUN'S", "BIRTHDAY, MILD SOUP,",
               "HEARING BEIGE, A", "SECOND, SMALLER YOU,", "TEETH IN THE WRONG", "ORDER, AND GLORPAX.", "",
               "DO NOT TAKE GLORPAX", "IF YOU ARE GLORPAX."]

    def __init__(self):
        self.hill = (Y > 92 + 6 * np.sin(X * 0.05 + 1))[..., None]

    def draw(self, img, t):
        vgrad(img, (.55, .75, .95), (.9, .9, .95))
        img[:] = np.where(self.hill, np.array((.4, .7, .35), np.float32), img)
        split = min(1.0, max(0.0, (t - 7.5) / 3)) * 16
        walk = t * 3
        for k, (dx, skin, shirt) in enumerate(((0, SKINS[0], (.9, .5, .5)), (16, SKINS[2], (.5, .6, .9)))):
            for ghost in ((0, 1.0), (split, 0.55)) if split > 0.5 else ((0, 1.0),):
                x = 34 + dx + walk + ghost[0]
                body(img, x, 74, 6, shirt, a=ghost[1])
                face(img, x, 74, 6, skin, t, mood=1, seed=k, a=ghost[1])
        bx, by = 90 + 10 * math.sin(t * 0.9), 40 + 6 * math.sin(t * 1.7)
        flap = abs(math.sin(t * 9))
        for s in (-1, 1):
            ellipse(img, bx + s * 3 * flap, by, 3 * flap + 0.5, 3, (.9, .4, .9))
        i, _, lt = cue(t, [(0, 0), (3.5, 1), (7.5, 2)])
        if i == 0:
            words(img, "LIFE CAN BE...", 10, (.2, .2, .45), shadow=None)
            if lt > 1.2:
                words(img, "BLURRY.", 22, (.2, .2, .45), shadow=None)
        elif i == 1:
            ellipse(img, 52, 26, 12, 7, (.6, .3, .85), rot=0.3)
            ellipse(img, 72, 20, 12, 7, (.95, .95, .95), rot=0.3)
            words(img, "GLORPAX", 34, (.5, .2, .75), scale=2, shadow=WHITE)
            words(img, "ASK YOUR DOCTOR", 102, (.2, .2, .45), shadow=None)
        else:
            rect(img, 0, 0, N, N, (.05, .05, .15), a=0.55)
            y = 116 - lt * 26
            for k, s in enumerate(self.EFFECTS):
                draw.text(img, s, 64, y + k * LINE, WHITE, center=True)


class Cooking(Show):
    num, title, net, length = 31, "COOKING WITH A HAND", "FOOD-ISH", 12.0

    def __init__(self):
        chk = (((X // 8) + (Y // 8)) % 2)[..., None]
        self.bg = np.where(chk > 0, np.array((.55, .7, .75), np.float32), np.array((.75, .85, .85), np.float32))
        self.bg[88:] = (.5, .3, .15)
        self.bg[88:90] = (.35, .2, .1)

    def draw(self, img, t):
        img[:] = self.bg
        i, s, lt = cue(t, [(0, "STEP 1: APOLOGISE TO THE EGG."), (4, "STEP 2: THE EGG FORGIVES YOU."),
                           (8, "STEP 3: SERVE COLD, IN A SHOE.")])
        _steam(img, 90, 66, t, n=4)
        ellipse(img, 90, 78, 22, 15, (.25, .25, .28), half="bottom")
        ellipse(img, 90, 78, 22, 4, (.35, .35, .4))
        ellipse(img, 90, 78, 19, 2.5, (.9, .8, .3))
        a = t * 4
        hx, hy = 90 + 8 * math.cos(a), 56 + 2 * math.sin(a)
        rect(img, hx - 6, 0, hx + 6, hy, SKINS[3])
        ellipse(img, hx, hy, 10, 8, SKINS[3])
        for f in range(4):
            line(img, hx - 7 + f * 4.5, hy + 4, hx - 7 + f * 4.5, hy + 10, SKINS[3], w=3)
        line(img, hx, hy + 6, 90 + 4 * math.cos(a), 80, (.6, .4, .2), w=2)
        ex, ey = 32, 76
        if i == 2:
            poly(img, [(14, 88), (16, 74), (30, 76), (52, 82), (54, 88)], (.45, .2, .08))
            ex, ey = 26, 68
        ellipse(img, ex, ey, 10, 13, (.97, .95, .88))
        mood = -1 if i == 0 else 1
        for dx in (-3.5, 3.5):
            ellipse(img, ex + dx, ey - 2, 1.4, 1.6 if not (i == 0 and lt % 1.2 < 0.1) else 0.3, BLACK)
        line(img, ex - 3, ey + 4 - mood, ex, ey + 4 + mood, BLACK, w=1)
        line(img, ex, ey + 4 + mood, ex + 3, ey + 4 - mood, BLACK, w=1)
        if i == 0:
            ellipse(img, ex + 4, ey + 1 + (lt * 12) % 10, 1, 1.5, (.4, .7, 1))
        elif i == 1:
            hy2 = ey - 18 - (lt * 8) % 12
            for dx in (-1.6, 1.6):
                ellipse(img, ex + dx, hy2, 2, 2, (.95, .2, .4))
            poly(img, [(ex - 3.4, hy2 + 0.5), (ex + 3.4, hy2 + 0.5), (ex, hy2 + 5)], (.95, .2, .4))
        caption(img, s)
        draw.text(img, "COOKING WITH A HAND", 64, 1, (.2, .2, .3), center=True)


class Cube(Show):
    num, title, net, length = 38, "THE 2087 CUBE", "AUTO-Z", 11.0
    V = np.array([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], np.float32)
    FACES = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]

    def __init__(self):
        rng = np.random.default_rng(38)
        self.stars = rng.random((40, 3))

    def draw(self, img, t):
        vgrad(img, (.0, .0, .08), (.15, .05, .25), 0, 70)
        vgrad(img, (.08, .08, .1), (.02, .02, .03), 70, N)
        for sx, sy, sb in self.stars:
            img[int(sy * 66), int(sx * 127)] = 0.3 + 0.6 * sb * (0.5 + 0.5 * math.sin(t * 3 + sx * 40))
        poly(img, [(56, 70), (72, 70), (128, 128), (0, 128)], (.18, .18, .2))
        for k in range(6):
            u = ((t * 0.8 + k / 6) % 1) ** 2
            y0, y1 = 70 + 58 * u, 70 + 58 * min(1, u + 0.06)
            line(img, 64, y0, 64, y1, (.9, .8, .3), w=1 + 3 * u)
        a, tilt = t * 0.9, 0.45
        ca, sa, ct, st = math.cos(a), math.sin(a), math.cos(tilt), math.sin(tilt)
        v = self.V.copy()
        v[:, 0], v[:, 2] = ca * self.V[:, 0] + sa * self.V[:, 2], -sa * self.V[:, 0] + ca * self.V[:, 2]
        v[:, 1], v[:, 2] = ct * v[:, 1] - st * v[:, 2], st * v[:, 1] + ct * v[:, 2]
        bob = 2 * math.sin(t * 2)
        pts = np.stack([64 + v[:, 0] * 17, 54 + v[:, 1] * 17 + bob], 1)
        light = np.array((-0.4, -0.7, -0.6), np.float32)
        light /= np.linalg.norm(light)
        drawn = []
        for f in self.FACES:
            n = np.cross(v[f[1]] - v[f[0]], v[f[2]] - v[f[0]])
            if n[2] < 0:
                n = n / np.linalg.norm(n)
                drawn.append((v[list(f), 2].mean(), f, 0.3 + 0.7 * max(0.0, float(n @ light))))
        for _, f, shade in sorted(drawn, key=lambda d: -d[0]):
            poly(img, pts[list(f)], (0.9 * shade + 0.05, 0.08 * shade, 0.15 * shade))
        gx, gy = pts[int(t * 1.5) % 8]
        g = abs(math.sin(t * 5))
        line(img, gx - 6 * g, gy, gx + 6 * g, gy, WHITE, w=1)
        line(img, gx, gy - 6 * g, gx, gy + 6 * g, WHITE, w=1)
        s = cue(t, [(0, "THE ALL-NEW 2087 CUBE."), (2.8, "NO WHEELS. NO DOORS. NO EXIT."), (5.6, "0-60: NEVER."),
                    (7.8, "LEASE ONE FOR 3 TEETH A MONTH.")])[1]
        words(img, s, 88, WHITE)


class StandBy(Show):
    num, title, net, length = 42, "PLEASE STAND BY", "", 9.0
    BARS = [(.75, .75, .75), (.75, .75, 0), (0, .75, .75), (0, .75, 0), (.75, 0, .75), (.75, 0, 0), (0, 0, .75)]
    LOW = [(0, 0, .75), (0, 0, 0), (.75, 0, .75), (0, 0, 0), (0, .75, .75), (0, 0, 0), (.75, .75, .75)]

    def __init__(self):
        self.bg = np.zeros((N, N, 3), np.float32)
        for k in range(7):
            x0, x1 = round(k * N / 7), round((k + 1) * N / 7)
            self.bg[:84, x0:x1] = self.BARS[k]
            self.bg[84:94, x0:x1] = self.LOW[k]
        for k, c in enumerate([(0, .1, .3), (.9, .9, .9), (.2, 0, .4), (0, 0, 0)]):
            self.bg[94:, k * 32:(k + 1) * 32] = c
        rng = np.random.default_rng(42)
        self.looks = rng.uniform(-1, 1, (32, 2))

    def draw(self, img, t):
        img[:] = self.bg
        stare = t > 6
        look = (0, 0) if stare else self.looks[int(t * 1.4) % 32]
        open_ = 0.1 if t % 2.7 < 0.15 else 1.0
        ellipse(img, 64, 44, 26, 15, (.1, .0, .0))
        ellipse(img, 64, 44, 24, 13 * open_, (.96, .94, .9))
        if open_ > 0.5:
            ix, iy = 64 + look[0] * 10, 44 + look[1] * 4
            ellipse(img, ix, iy, 9, 9, (.2, .55, .3))
            ellipse(img, ix, iy, 4 + 2 * stare, 4 + 2 * stare, BLACK)
            ellipse(img, ix - 2, iy - 3, 1.5, 1.5, WHITE)
        s = cue(t, [(0, "PLEASE STAND BY"), (3, "THIS DIMENSION IS EXPERIENCING DIFFICULTIES"), (6, "WE CAN SEE YOU.")])[1]
        caption(img, s, 96, WHITE, BLACK, a=1.0)


class Snake(Show):
    num, title, net, length = 47, "ARM DAY FOR SNAKES", "FIT-TV", 11.0

    def draw(self, img, t):
        vgrad(img, (.1, .0, .25), (.9, .2, .5), 0, 70)
        sun = np.hypot(X - 64, Y - 60) < 26
        stripes = ((Y.astype(np.int32) // 3) % 2 == 0) & (Y > 52)
        img[sun & ~stripes & (Y < 70)] = (1, .7, .2)
        img[70:] = (.04, 0, .08)
        for k in range(8):                          # the grid, rushing at us
            u = ((t * 0.7 + k / 8) % 1) ** 2.2
            y = int(70 + 58 * u)
            img[y, :] = (.1, .9, 1)
        for k in range(-8, 9):
            line(img, 64 + k * 4, 70, 64 + k * 24, 128, (.1, .9, 1), w=1, a=0.8)
        lift = 14 * max(0.0, math.sin(t * 3.2))
        n = 16
        for j in range(n):
            u = j / (n - 1)
            x = 24 + u * 70
            y = 100 + 3 * math.sin(u * 8 - t * 4) - lift * u * u
            ellipse(img, x, y, 5, 5, (.2, .8 - .2 * (j % 2), .3))
        hx, hy = 98, 100 - lift - 4
        ellipse(img, hx, hy, 8, 7, (.2, .75, .3))
        line(img, hx - 7, hy - 4, hx + 7, hy - 4, (.95, .1, .2), w=2)
        for dx in (-2, 3):
            ellipse(img, hx + dx, hy - 1, 1.6, 1.8, (1, 1, .6))
        if int(t * 3) % 3 == 0:
            line(img, hx + 7, hy + 2, hx + 12, hy + 2, (.9, .1, .2), w=1)
        draw.text(img, "REPS: 0", 124 - draw.text_width("REPS: 0"), 2, (1, 1, 1))
        s = cue(t, [(0, "AND PUSH!"), (2.5, "YOU DON'T HAVE ARMS!"), (5, "PUSH ANYWAY!"), (7.8, "GOOD. NOW THE OTHER ARM.")])[1]
        words(img, s, 14, (1, 1, .4), shadow=(.5, 0, .4))


class Zorb(Show):
    num, title, net, length = 52, "MADAME ZORB", "PSY-NET", 11.0

    def __init__(self):
        self.ang = np.arctan2(Y - 60, X - 64)
        self.r = np.hypot(X - 64, Y - 60)

    def draw(self, img, t):
        v = (np.sin(self.ang * 3 + self.r * 0.15 - t * 2) * 0.5 + 0.5)[..., None]
        img[:] = np.array((.12, .02, .2), np.float32) + v * np.array((.35, .05, .45), np.float32)
        poly(img, [(46, 98), (82, 98), (74, 84), (54, 84)], (.6, .45, .1))
        ellipse(img, 64, 60, 26, 26, (.35, .55, .85))
        ellipse(img, 64, 60, 23, 23, (.55, .75, 1))
        ghost = 0.35 + 0.25 * math.sin(t * 1.5)
        face(img, 64, 62, 13, (.9, .95, 1), t, talk=chatter(t, 1) * 0.7, eyes=3, look=(0, 0), seed=7, a=ghost)
        ellipse(img, 54, 48, 5, 3, WHITE, a=0.6, rot=-0.6)
        for s in (-1, 1):
            hx = 64 + s * (36 + 3 * math.sin(t * 2 + s))
            ellipse(img, hx, 66 + 2 * math.sin(t * 2.3 + s), 8, 11, SKINS[4])
            ellipse(img, hx, 70, 2, 2, (.2, 1, .5))
        s = cue(t, [(0, "MADAME ZORB SEES ALL."), (2.8, "SHE SEES YOU. ON YOUR COUCH."), (5.6, "CALL 1-900-BEHIND-YOU"),
                    (8.4, "SHE KNOWS YOU WON'T.")])[1]
        caption(img, s, None, (1, .9, .4), (.1, 0, .15))


def _raccoon(img, x, y, r, t, seed=0.0):
    for s in (-1, 1):
        ellipse(img, x + s * r * 0.7, y - r * 0.8, r * 0.35, r * 0.4, (.35, .35, .38))
    ellipse(img, x, y, r, r * 0.85, (.55, .55, .58))
    ellipse(img, x, y - r * 0.15, r * 0.9, r * 0.28, (.08, .08, .1))
    for s in (-1, 1):
        ellipse(img, x + s * r * 0.4, y - r * 0.15, r * 0.16, r * 0.16, WHITE)
    ellipse(img, x, y + r * 0.35, r * 0.2, r * 0.14, BLACK)


class Soap(Show):
    num, title, net, length = 66, "AS THE WORM TURNS", "WB-Q", 13.0

    def _coat(self, img, x, y, r):
        ellipse(img, x, y + r * 2.8, r * 1.9, r * 1.9, (.7, .55, .3))
        poly(img, [(x - r * 0.9, y + r), (x, y + r * 2.3), (x + r * 0.9, y + r)], (.55, .4, .2))
        line(img, x, y + r * 2.3, x, N, (.4, .28, .12), w=1)

    def draw(self, img, t):
        vgrad(img, (.55, .25, .45), (.2, .05, .2))
        glow = np.exp(-((X - 40) ** 2 + (Y - 30) ** 2) / 1800)[..., None]
        img += glow * np.array((.3, .15, .2), np.float32)
        i, s, lt = cue(t, [(0, "GREGORIO... I KNOW YOUR SECRET."), (3.5, "YOU ARE THREE RACCOONS IN A TRENCH COAT."),
                           (7, "..."), (9.6, "WE ALWAYS HAVE BEEN.")])
        if i < 2:
            ellipse(img, 36, 52, 19, 24, (.25, .1, .05))
            person(img, 36, 52, 14, SKINS[0], (.6, .1, .3), t, talk=chatter(t), look=(1, 0), seed=1)
            self._coat(img, 96, 50, 13)
            face(img, 96, 50, 13, SKINS[1], t, mood=-1 if i else 0, look=(-1, 0), seed=2)
        elif i == 2:
            z = 14 + lt * 8
            self._coat(img, 64, 54, z)
            face(img, 64, 54, z, SKINS[1], t, look=(0, 0), seed=2)
            if int(lt * 10) % 7 == 0:
                img *= 1.6
        else:
            self._coat(img, 64, 60, 16)
            for k, (dx, dy) in enumerate(((-12, 44), (12, 44), (0, 30))):
                _raccoon(img, 64 + dx, dy + 2 * math.sin(t * 6 + k * 2), 10, t, k)
        caption(img, s, None, (1, .85, .9), BLACK, a=0.6)


class Whale(Show):
    num, title, net, length = 73, "HOUSE HUNTERS: WHALE", "HGTV-9", 12.0

    def __init__(self):
        rng = np.random.default_rng(73)
        self.bubbles = rng.random((14, 3))
        self.rays = (0.5 + 0.5 * np.sin((X - Y * 0.5) * 0.12))[..., None] * np.clip(1 - Y / 100, 0, 1)[..., None]

    def draw(self, img, t):
        vgrad(img, (.1, .45, .6), (.0, .05, .18))
        img += self.rays * np.array((.08, .15, .15), np.float32)
        x = 70 + 12 * math.sin(t * 0.5)
        y = 58 + 4 * math.sin(t * 0.8)
        tail = 6 * math.sin(t * 2)
        poly(img, [(x - 42, y), (x - 60, y - 14 + tail), (x - 56, y + tail), (x - 60, y + 14 + tail)], (.2, .3, .5))
        ellipse(img, x, y, 46, 20, (.25, .35, .55))
        ellipse(img, x + 4, y + 8, 38, 10, (.55, .65, .75), half="bottom")
        ellipse(img, x + 30, y - 4, 2, 2, BLACK)
        for k in range(4):                          # somebody's home
            wx = x - 28 + k * 12
            rect(img, wx, y - 6, wx + 5, y + 1, (1, .85, .4) if (k + int(t)) % 5 else (.3, .3, .2))
        rect(img, x - 6, y - 26, x - 1, y - 18, (.4, .2, .15))
        for k in range(3):
            ellipse(img, x - 3 + k * 2 + math.sin(t * 2 + k), y - 30 - k * 4 - (t * 6) % 4, 1.5 + k, 1.2 + k, (.6, .6, .6), a=0.5)
        for bx, by, bs in self.bubbles:
            yy = 128 - ((t * (10 + 20 * bs) + by * 128) % 140)
            ellipse(img, bx * 128 + 2 * math.sin(t * 3 + by * 9), yy, 1 + 1.5 * bs, 1 + 1.5 * bs, (.7, .9, 1), a=0.5)
        s = cue(t, [(0, "PLOOB AND JENNIX WANT TO LIVE INSIDE A WHALE."), (3.5, "BUDGET: FOUR SHELLS."),
                    (6.5, "'IT HAS GOOD BONES.'"), (9.2, "'IS THE HOUSE MOVING?'")])[1]
        caption(img, s, None, WHITE, (.05, .1, .25), a=0.8)


class Bees(Show):
    num, title, net, length = 99, "EMERGENCY BEE SYSTEM", "EBS", 11.0

    def __init__(self):
        self.hazard = ((((X + Y) // 8) % 2) > 0)[..., None]

    def draw(self, img, t):
        img[:] = (.25 + .15 * math.sin(t * 6), 0, 0)
        for y0, y1 in ((0, 12), (116, 128)):
            band = np.roll(self.hazard, int(t * 12), 1)[y0:y1]
            img[y0:y1] = np.where(band, np.array((1, .8, 0), np.float32), np.array((0, 0, 0), np.float32))
        i, s, lt = cue(t, [(0, "THIS IS A TEST OF THE EMERGENCY BEE SYSTEM."),
                           (3.5, "IF THIS HAD BEEN AN ACTUAL BEE, YOU WOULD HAVE BEEN INFORMED BY THE BEE."),
                           (7, ""), (9.2, "THAT WAS AN ACTUAL BEE.")])
        words(img, s, 22, WHITE)
        if i == 2:
            bx = -10 + lt * 70
            bee(img, bx, 64 + 18 * math.sin(lt * 9) * math.cos(lt * 3), t, 6)
        draw.text(img, "EBS", 64, 102, (1, .8, 0), center=True)


class NoSignal(Show):
    num, title, net, length = 404, "", "", 7.0
    reception = 1.0

    def draw(self, img, t):
        img[:] = 0.05
        w, h = 66, 15
        x = abs((t * 23) % (2 * (N - w)) - (N - w))
        y = abs((t * 17) % (2 * (N - h)) - (N - h))
        hue = int(t * 23 // (N - w) + t * 17 // (N - h)) % 5
        col = [(1, .3, .3), (.3, 1, .4), (.4, .6, 1), (1, .9, .3), (1, .4, 1)][hue]
        rect(img, x, y, x + w, y + h, (0, 0, 0))
        draw.text(img, "NO SIGNAL", x + w / 2, y + 2, col, center=True)
        if 3 < t < 5.5:
            face(img, 64, 60, 30, (.6, .6, .6), t, talk=chatter(t), a=0.25, seed=4)
            caption(img, "...IS ANYONE WATCHING?", None, (.7, .7, .7), BLACK, a=0.0)


class Onn(Show):
    """An anchor desk for this dimension's real headlines, from The Onion (headlines.py)."""
    num, title, net, length = 6, "ONN", "ONN", 14.0

    def __init__(self):
        lat, lon = [], []
        for la in range(-60, 61, 30):
            lat += [la] * 90
            lon += list(range(0, 360, 4))
        for lo in range(0, 360, 30):
            lat += list(range(-88, 89, 4))
            lon += [lo] * 45
        self.lat, self.lon = np.radians(lat).astype(np.float32), np.radians(lon).astype(np.float32)
        self.tune()

    def tune(self):
        news = headlines.get()
        rng = np.random.default_rng()
        self.pick = list(rng.choice(news, min(2, len(news)), replace=False))
        rest = [h for h in news if h not in self.pick] or self.pick
        self.crawl = " * ".join(rng.choice(rest, min(6, len(rest)), replace=False)) + " * "

    def draw(self, img, t):
        vgrad(img, (.02, .06, .22), (0, 0, .05))
        lon = self.lon + t * 0.4
        x, y, z = np.cos(self.lat) * np.sin(lon), -np.sin(self.lat), np.cos(self.lat) * np.cos(lon)
        front = z > -0.2
        col = (0.15 + 0.5 * np.clip(z[front], 0, 1))[:, None] * np.array((.3, .55, 1), np.float32)
        draw.plot(img, 96 + 30 * x[front], 36 + 30 * y[front], col, op="max")
        body(img, 40, 40, 12, (.08, .1, .2))
        poly(img, [(37, 54), (43, 54), (40, 66)], (.75, .05, .1))
        ellipse(img, 40, 33, 13, 10, (.3, .2, .1))
        face(img, 40, 42, 12, SKINS[0], t, talk=chatter(t, 3), seed=9)
        rect(img, 0, 66, N, 72, (.25, .25, .3))
        rect(img, 2, 2, 30, 14, (.75, .05, .1))
        draw.text(img, "ONN", 16, 3, WHITE, center=True)
        half = self.length / 2
        k, lt = int(t // half) % len(self.pick), t % half
        lines = wrap(self.pick[k])
        pages = [lines[i:i + 3] for i in range(0, len(lines), 3)]
        page = pages[min(len(pages) - 1, int(lt / (half / len(pages))))]
        rect(img, 0, 72, N, 83, (.75, .05, .1))
        draw.text(img, "BREAKING NEWS", 4, 72, WHITE)
        if int(t * 2) % 2:
            ellipse(img, 121, 77, 2.5, 2.5, WHITE)
        rect(img, 0, 83, N, 117, (.82, .82, .85))
        shown = typed(" ".join(page), lt - (half / len(pages)) * pages.index(page), 40)
        y, used = 85, 0
        for ln in page:
            part = shown[used:used + len(ln)]
            used += len(ln) + 1
            draw.text(img, part, 64 - draw.text_width(ln) / 2, y, (.05, .08, .25))
            y += LINE
        ticker(img, self.crawl, N - LINE, t, 30, (1, .9, .3), (0, 0, 0))


class Pull(Show):
    """Silent: a man, a door, a sign."""
    num, title, net, length = 5, "PULL", "LOL-TV", 11.5
    G, H = 104, 46

    def _door(self, img, phi):
        c, s = math.cos(phi), math.sin(phi)

        def at(dx, dy):                             # tips about its bottom-left corner, leftwards
            return 84 + dx * c + dy * s, self.G - dx * s + dy * c

        poly(img, [at(0, -70), at(30, -70), at(30, 0), at(0, 0)], (.55, .32, .15))
        poly(img, [at(4, -64), at(26, -64), at(26, -42), at(4, -42)], (.47, .26, .12))
        poly(img, [at(3, -36), at(27, -36), at(27, -26), at(3, -26)], (.92, .9, .8))
        ellipse(img, *at(25, -18), 1.8, 1.8, (1, .8, .2))
        if phi < 0.08:
            draw.text(img, "PULL", 99, self.G - 37, (.7, .05, .05), center=True)

    def _man(self, t):
        base = self.G - LEG * self.H
        m = dict(x=66.0, y=base, rot=0.0, arms=(0.3, 0.3), walk=0.0, look=(1, 0), mood=0, stars=False)
        if t < 1.5:
            m.update(x=-10 + 76 * t / 1.5, walk=1)
        elif t < 5.1:
            u = (t - 1.5) % 1.8
            if u < 0.6:
                m.update(x=66 + 0.8 * math.sin(u * 60), rot=0.15, arms=(-1.4, 1.4), mood=-1)
            elif u < 0.9:
                m.update(x=66 - 14 * (u - 0.6) / 0.3, rot=-0.35, mood=-1)
            elif u < 1.4:
                m.update(x=52, stars=True, look=(0, 0))
            else:
                m.update(x=52 + 14 * (u - 1.4) / 0.4, walk=1)
        elif t < 5.5:
            m.update(x=66 - 36 * (t - 5.1) / 0.4, walk=1, look=(-1, 0))
        elif t < 6.0:
            m.update(x=30 + 36 * (t - 5.5) / 0.5, walk=1.6, rot=0.2, mood=-1)
        elif t < 6.5:
            u = (t - 6.0) / 0.5
            m.update(x=66 - 30 * u, rot=-1.45 * u, y=base + (self.G - 4 - base) * u * u, arms=(2.5, 2.5))
        elif t < 7.4:
            m.update(x=36, rot=-1.45, y=self.G - 4, stars=True, look=(0, 0))
        elif t < 7.9:
            u = (t - 7.4) / 0.5
            m.update(x=36, rot=-1.45 * (1 - u), y=self.G - 4 + (base - self.G + 4) * u)
        elif t < 8.4:
            m.update(x=36 + 30 * (t - 7.9) / 0.5, walk=1)
        elif t < 9.0:
            m.update(look=(1, -1), mood=-1)
        else:
            m.update(rot=-0.15, arms=(-1.2, 1.2), x=64)
        return m

    def draw(self, img, t):
        vgrad(img, (.8, .75, .6), (.6, .55, .42), 0, self.G)
        rect(img, 0, self.G, N, N, (.32, .22, .16))
        rect(img, 81, 31, 117, self.G, (.3, .17, .08))
        for row in range(0, 70, 7):                 # behind the door: a brick wall
            off = 4 if (row // 7) % 2 else 0
            for bx in range(84 - 8 + off, 116, 8):
                rect(img, max(84, bx), 34 + row, min(114, bx + 7), 34 + row + 6, (.6, .25, .18))
        phi = 0.0
        if t > 9.0:
            phi = 0.04 * math.sin(t * 30) if t < 9.4 else (math.pi / 2) * min(1.0, ((t - 9.4) / 0.5) ** 2)
        if t < 9.8:
            m = self._man(t)
            hx, hy, r = toon(img, m["x"], m["y"], self.H, SKINS[0], (.2, .5, .3), t, walk=m["walk"], rot=m["rot"],
                             arms=m["arms"], look=m["look"], mood=m["mood"], seed=2)
            if m["stars"]:
                for k in range(3):
                    a = t * 6 + k * 2.1
                    star(img, hx + 9 * math.cos(a), hy - r - 3 + 3 * math.sin(a), 2.5, (1, .9, .2), n=5, inner=0.45)
        self._door(img, phi)
        if t > 9.9:
            for k in range(3):
                a = t * 5 + k * 2.1
                star(img, 50 + 12 * math.cos(a), 68 + 3 * math.sin(a), 2.5, (1, .9, .2), n=5, inner=0.45)
            wave = 2 * math.sin(t * 8)
            line(img, 50, 74, 50 + wave, 66, (.2, .5, .3), w=3)
            ellipse(img, 50 + wave, 65, 2.5, 2.5, SKINS[0])


class Piano(Show):
    """Silent: a nice day for a walk."""
    num, title, net, length = 14, "LOOK UP", "LOL-TV", 10.5
    G, H = 106, 40

    def draw(self, img, t):
        vgrad(img, (.45, .7, .95), (.8, .88, .95), 0, 92)
        rect(img, 92, 0, N, 92, (.6, .3, .25))
        for wy in range(6, 86, 16):
            for wx in (98, 114):
                rect(img, wx, wy, wx + 9, wy + 10, (.25, .35, .5) if (wx, wy) != (98, 6) else (.05, .05, .08))
        rect(img, 0, 92, N, N, (.55, .55, .55))
        rect(img, 0, 92, N, 94, (.75, .75, .75))
        base = self.G - LEG * self.H
        if 3.0 < t < 5.15:                          # its shadow, growing
            u = min(1.0, (t - 3.0) / 1.9)
            ellipse(img, 61, self.G + 1, 3 + 22 * u, 1.5 + 2.5 * u, (.25, .25, .25), a=0.6)
        if t < 5.15:
            x = -10 + 70 * min(1.0, t / 3)
            look = (1, 0) if t < 3.3 else (0, 1) if t < 4.2 else (0, -1)
            hx, hy, r = toon(img, x, base, self.H, SKINS[1], (.85, .3, .2), t, walk=1 if t < 3 else 0, look=look,
                             talk=1.0 if t > 4.4 else 0, seed=3)
            if t < 3:
                ny = hy - ((t * 20) % 16)
                ellipse(img, hx + 8, ny, 1.8, 1.4, (.2, .2, .4))
                line(img, hx + 9.5, ny, hx + 9.5, ny - 5, (.2, .2, .4), w=1)
        bottom = -10 + (self.G + 12) * min(1.0, max(0.0, (t - 4.6) / 0.55)) ** 2 if t > 4.6 else -40
        if bottom > -40:
            x0, x1 = 38, 84
            rect(img, x0, bottom - 34, x1, bottom - 6, (.1, .06, .06))
            rect(img, x0 - 2, bottom - 18, x1 + 2, bottom - 13, WHITE)
            for k in range(x0 + 2, x1, 5):
                rect(img, k, bottom - 18, k + 2, bottom - 15, BLACK)
            for lx in (x0 + 2, x1 - 6):
                rect(img, lx, bottom - 6, lx + 4, bottom, (.1, .06, .06))
        if t > 7.0:
            flat = 0.34 + 0.08 * math.sin(t * 12)
            toon(img, 86 + (t - 7) * 12, self.G - LEG * self.H * flat, self.H, SKINS[1], (.85, .3, .2), t, walk=1,
                 flat=flat, mood=-1, look=(1, 0), seed=3)
        if 5.15 < t < 6.4:                          # dust and loose notes
            u = t - 5.15
            for k in range(6):
                s = -1 if k % 2 else 1
                ellipse(img, 61 + s * (26 + u * 30 * (1 + k // 2) / 2), self.G - 2 - k // 2 * 4, 4 + 6 * u, 3 + 4 * u,
                        (.7, .7, .65), a=max(0.0, 0.8 - u * 0.6))
            for k in range(4):
                nx, ny = 61 + (k - 1.5) * 18 * u * 2, self.G - 40 - 50 * u + 40 * u * u
                ellipse(img, nx, ny, 2, 1.5, BLACK)
                line(img, nx + 1.5, ny, nx + 1.5, ny - 6, BLACK, w=1)
            shake = int(4 * math.sin(u * 50) * math.exp(-u * 5))
            img[:] = np.roll(img, (shake, -shake // 2), (0, 1))


def _peel(img, x, y, rot=0.0):
    for k in (-1, 0, 1):
        ellipse(img, x + 4 * math.sin(rot + k * 0.9), y + 4 * math.cos(rot + k * 0.9) * 0.5, 4, 1.6, (1, .85, .15),
                rot=rot + k * 0.9)
    ellipse(img, x, y, 2, 2, (.95, .8, .1))


class Banana(Show):
    """Silent: three bananas."""
    num, title, net, length = 16, "BANANA", "LOL-TV", 11.0
    G, H = 104, 40

    def draw(self, img, t):
        vgrad(img, (.4, .7, 1), (.8, .9, 1), 0, self.G)
        for cx, cy in ((24, 18), (96, 28)):
            for dx in (-7, 0, 7):
                ellipse(img, cx + dx + t * 2, cy - (dx == 0) * 3, 8, 5, (.97, .97, 1))
        rect(img, 0, self.G, N, N, (.3, .65, .25))
        base = self.G - LEG * self.H
        x, y, rot, arms, mood, walk, stars = 0.0, base, 0.0, (0.3, 0.3), 0, 0.0, False

        def fall(u):
            return -math.pi / 2 * min(1.0, u * 1.4), base - 18 * math.sin(math.pi * min(u, 1)) + (self.G - 5 - base) * u

        if t < 2.7:
            x, walk = -10 + 25 * t, 1.0
        elif t < 3.4:
            u = (t - 2.7) / 0.7
            x = 57.5 + 6 * u
            rot, y = fall(u)
            arms = (2.5 + math.sin(t * 30), 2.5 - math.sin(t * 30))
        elif t < 4.6:
            x, rot, y, stars = 63.5, -math.pi / 2, self.G - 5, True
        elif t < 5.0:
            u = (t - 4.6) / 0.4
            x, rot, y = 63.5, -math.pi / 2 * (1 - u), self.G - 5 + (base - self.G + 5) * u
        elif t < 6.1:
            x, walk = 63.5 + 25 * (t - 5.0), 1.0
        elif t < 7.1:
            u = (t - 6.1) / 1.0
            x, rot, y, arms = 91 + 4 * u, -2 * math.pi * u, base - 34 * math.sin(math.pi * u), (2.0, 2.0)
        elif t < 9.0:
            x, arms, mood = 95, (2.7, 2.7), 1
        elif t < 9.6:
            u = (t - 9.0) / 0.6
            x = 95
            rot, y = fall(u)
        else:
            x, rot, y, stars = 95, -math.pi / 2, self.G - 5, True
        if t < 2.7:
            _peel(img, 58, self.G)
        elif t < 4:
            u = t - 2.7
            _peel(img, 58 + 50 * u, self.G - 70 * u + 30 * u * u, rot=u * 12)
        if t < 6.1:
            _peel(img, 92, self.G)
        hx, hy, r = toon(img, x, y, self.H, SKINS[2], (.3, .4, .9), t, walk=walk, rot=rot, arms=arms, mood=mood,
                         look=(1, 0) if walk else (0, 0), seed=4)
        if t > 8.4:                                 # the third one
            u = min(1.0, (t - 8.4) / 0.5)
            px = 95 + (hx - 95) * (t > 8.9)
            py = -10 + (hy - r - 1 + 10) * u * u if t < 8.9 else hy - r * 1.1 * math.cos(rot)
            _peel(img, px if t < 8.9 else hx + r * 1.1 * math.sin(rot), py, rot=rot)
        if stars:
            for k in range(3):
                a = t * 6 + k * 2.1
                star(img, hx + 9 * math.cos(a), hy - 8 + 3 * math.sin(a), 2.5, (1, .9, .2), n=5, inner=0.45)


class Pies(Show):
    """Silent: a gentlemen's disagreement."""
    num, title, net, length = 21, "PIE OFF", "LOL-TV", 9.5
    G, H, A, B = 116, 50, 28, 100
    FLY = 0.45
    CREAM = (.95, .9, .78)

    def __init__(self):
        self.curtain = (np.array((.55, .05, .08), np.float32) * (0.7 + 0.3 * np.sin(X * 0.45))[..., None])
        x = np.arange(N, dtype=np.float32)
        self.drip = 75 + 22 * np.sin(x * 0.21) + 14 * np.sin(x * 0.53 + 1)        # it slides off unevenly
        self.edge = 5 + 4 * np.sin(x * 0.37 + 2) + 3 * np.sin(x * 0.9)

    def _pie(self, img, x, y, r=4.0):
        ellipse(img, x, y + r * 0.3, r, r * 0.55, (.75, .55, .3))
        ellipse(img, x, y, r * 0.9, r * 0.45, self.CREAM)

    def _splat(self, img, hx, hy, r):
        ellipse(img, hx, hy - r * 0.2, r * 1.15, r * 0.9, self.CREAM)
        for k in (-1, 0, 1):
            ellipse(img, hx + k * r * 0.6, hy + r * 0.7, r * 0.22, r * 0.5, self.CREAM)

    def draw(self, img, t):
        img[:] = self.curtain
        rect(img, 0, self.G - 12, N, N, (.45, .28, .12))
        base = self.G - LEG * self.H
        throws = {self.A: [0.6, 3.8, 5.6], self.B: [2.2, 3.8]}
        heads = {}
        for x, skin, shirt, d in ((self.A, SKINS[0], (.3, .3, .7), 1), (self.B, SKINS[1], (.6, .5, .2), -1)):
            arm = 0.3
            for t0 in throws[x]:
                if t0 - 0.45 < t < t0:
                    arm = 2.9                       # wind up
                elif t0 <= t < t0 + 0.25:
                    arm = 1.4
            hit = (x == self.B and t > 0.6 + self.FLY) or (x == self.A and t > 2.2 + self.FLY)
            mood = 1 if (x == self.A and t > 7) else -1 if hit else 0
            arms = (0.3, arm) if d > 0 else (arm, 0.3)
            heads[x] = toon(img, x, base, self.H, skin, shirt, t, arms=arms, look=(0, 0) if t > 5 else (d, 0), mood=mood,
                            talk=chatter(t * 2) if (x == self.A and t > 7) else 0, seed=x)
            if hit:
                self._splat(img, *heads[x])
        for t0, frm, to in ((0.6, self.A, self.B), (2.2, self.B, self.A)):
            u = (t - t0) / self.FLY
            if 0 <= u < 1:
                hx, hy, _ = heads[to]
                sx, sy = hand(frm, base, self.H, 2.9, 1 if frm == self.A else -1)
                self._pie(img, sx + (hx - sx) * u, sy + (hy - sy) * u - 20 * math.sin(math.pi * u))
        u = (t - 3.8) / self.FLY
        if 0 <= u < 0.5:                            # both at once: they meet in the middle
            for frm, to in ((self.A, 64), (self.B, 64)):
                self._pie(img, frm + (to - frm) * u * 2, 50 - 14 * math.sin(math.pi * u))
        elif 0.5 <= u < 3:
            v = (u - 0.5) * self.FLY
            for k in range(10):
                a = k * 0.63
                ellipse(img, 64 + math.cos(a) * 60 * v, 36 - math.sin(a) * 50 * v + 120 * v * v, 3, 2.5, self.CREAM)
        u = (t - 5.6) / 0.5                         # and one for you
        if 0 <= u < 1:
            r = 4 + 80 * u ** 2.5
            self._pie(img, self.A + (64 - self.A) * u, 50 + 14 * u, r)
        elif u >= 1:
            top = np.clip((t - 6.4) * self.drip, 0, None) - self.edge
            cover = (Y >= top[None, :])[..., None]
            img[:] = np.where(cover, np.array(self.CREAM, np.float32) * (0.92 + 0.08 * np.sin(X * 0.15) * np.sin(Y * 0.11))[..., None], img)


class Cave(Show):
    """Silent, in stop motion: a lesson."""
    num, title, net, length = 33, "CAVE SCHOOL", "CLAY-TV", 11.0
    G, H, P, C = 108, 52, 32, 98
    ROCK = (.62, .6, .58)

    def __init__(self):
        rng = np.random.default_rng(33)
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.32, .2, .12), (.14, .08, .05))
        for _ in range(26):
            x, y = rng.uniform(0, N), rng.uniform(0, 70)
            ellipse(self.bg, x, y, rng.uniform(4, 12), rng.uniform(3, 8), (.22, .14, .08), a=0.7)
        self.bg[self.G - 6:] = (.24, .16, .1)

    def _wheel(self, img, x, y, a, r=9):
        ellipse(img, x, y, r, r, self.ROCK)
        ellipse(img, x, y, r * 0.3, r * 0.3, (.35, .33, .3))
        for k in range(3):
            b = a + k * math.pi / 3
            line(img, x - r * 0.85 * math.cos(b), y - r * 0.85 * math.sin(b), x + r * 0.85 * math.cos(b),
                 y + r * 0.85 * math.sin(b), (.45, .43, .4), w=1)

    def draw(self, img, t):
        t = math.floor(t * 8) / 8                   # claymation: eight poses a second
        if t < 1.6:
            img[:] = (.35, .22, .1)
            rect(img, 6, 10, 122, 112, (.1, .25, .15))
            words(img, "LESSON 12:", 24, (.9, .9, .85), shadow=None)
            words(img, "THE WHEEL", 40, (.9, .9, .85), scale=2, shadow=None)
            draw.ring(img, 64, 84, 12, (.85, .85, .8))
            draw.ring(img, 64, 84, 3, (.85, .85, .8))
            return
        img[:] = self.bg
        for k in range(4):                          # the fire
            f = 0.6 + 0.4 * math.sin(t * 17 + k * 2)
            ellipse(img, 12 + (k - 1.5) * 3, self.G - 8 - 6 * f, 3, 7 * f, (1, .5 + .1 * k, .1))
        line(img, 4, self.G - 2, 20, self.G - 5, (.35, .2, .1), w=3)
        base = self.G - LEG * self.H
        pa, ca, cmood, look = (0.3, 0.3), (0.3, 0.6), 0, (-1, 0)
        wheel = None
        if t < 3.6:
            u = (t - 1.6) / 2
            wx = 44 + 34 * u
            wheel = (wx, self.G - 9, wx / 9)
            pa = (0.3, 1.0)
        elif t < 4.6:
            wheel, look, ca = (78, self.G - 9, 0), (-1, 1), (2.9, 0.6)
        if t >= 7.6:
            pa, ca, cmood = (0.3, -2.7), (0.3, 2.8), 1
        elif t >= 6.6:
            ca = (0.3, 2.8 if t < 7.1 else 0.9)
        hx, hy, r = toon(img, self.C, base, self.H, (.72, .5, .32), (.75, .45, .15), t, arms=ca, mood=cmood, look=look,
                         talk=chatter(t * 1.5) if t >= 7.6 else (1.0 if 5.6 <= t < 6.6 and int(t * 4) % 2 else 0),
                         pants=(.6, .35, .12), seed=5)
        line(img, hx - r * 0.7, hy - r * 0.45, hx + r * 0.7, hy - r * 0.45, (.15, .08, .05), w=2)
        cx, cy = hand(self.C, base, self.H, ca[1], 1)
        a = ca[1]
        ex, ey = cx + math.sin(a) * 14, cy + math.cos(a) * 14
        line(img, cx, cy, ex, ey, (.4, .22, .1), w=3)
        ellipse(img, ex, ey, 4, 4, (.4, .22, .1))
        if 4.6 <= t < 5.6:
            u = min(1.0, (t - 4.6) / 0.4)
            wheel = (78 + (hx - 78) * u, self.G - 9 + (hy - r - 5 - self.G + 9) * u, 0)
        elif 5.6 <= t < 6.6:
            wheel = (hx - 2, hy + r * 0.8, 0)
        elif 6.6 <= t < 7.2:
            wheel = (84, self.G - 9, 0)
        if wheel:
            self._wheel(img, *wheel)
            if 6.0 <= t < 7.2:
                ellipse(img, wheel[0] - 7, wheel[1] - 5, 3.5, 3.5, self.bg[int(wheel[1]) - 5, int(wheel[0]) - 7])
        if t >= 7.2:                                # in pieces
            v = min(1.0, t - 7.2)
            for k in range(5):
                ang = -0.3 - k * 0.6
                ellipse(img, 84 + math.cos(ang) * 50 * v, min(self.G - 3, self.G - 9 + math.sin(ang) * 50 * v + 60 * v * v),
                        3, 2.5, self.ROCK)
        toon(img, self.P, base, self.H, (.55, .9, .5), (.5, .25, .7), t, arms=pa, look=(1, 1) if t >= 7.6 else (1, 0),
             mood=-1 if t >= 7.6 else 1, headr=self.H * 0.2, pants=(.5, .25, .7), seed=6)
        if t >= 8.2:
            rect(img, hx - 34, hy - 30, hx - 8, hy - 18, WHITE)
            poly(img, [(hx - 16, hy - 18), (hx - 10, hy - 18), (hx - 6, hy - 12)], WHITE)
            draw.text(img, "OOG!", hx - 21, hy - 30, BLACK, center=True)


CHANNELS = [SoupHat, IsItAHat, News, Pull, Onn, Weather, Square, Standing, Doors, Piano, Banana, Mouth, Pies, Wheel,
            Glorpax, Cooking, Cave, Cube, StandBy, Snake, Zorb, Soap, Whale, Bees, NoSignal]
