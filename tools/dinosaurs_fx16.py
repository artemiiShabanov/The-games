#!/usr/bin/env python3
"""Мелкие эффекты «Динозавров» для 16/32 (#144): те же ленты, что у пиратов (`pixel_fx16.py`) и
космоса (`space_fx16.py`), рисунок свой: клубы красной глины с камешками из-под ног, завиток
аммонита на подобранной монете, оскал костяных клыков на ударе, всплеск лавы с каплями на
выстреле, вулканическая струя с углями вместо нитро.

Ключи, кадры и опорные точки как у пиратов, их читает `scripts/demos/fx16.gd`:
`fx16_dust` 5 кадров 24×12 (облако лежит на нижней трети кадра и расходится в стороны),
`fx16_spark` и `fx16_star` по 4 кадра 24×24 с центром в (12, 12), `fx16_flash` 3 кадра 32×32 с
центром в (16, 16), `fx16_fire` 4 кадра 40×64: корень пламени узкий вверху по центру (20, 2),
вниз к зрителю оно расширяется и рвётся на языки. Палитра та же по составу: обводка и четыре
рампы по четыре тона (`white`, `gold`, `dust`, `fire`), цвета взяты от `dinosaurs16.PALETTE`.

    python3 tools/dinosaurs_fx16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites16 import Canvas, strip  # noqa: E402
from pixel_brawl16 import Pal, ellipse, poly, capsule  # noqa: E402


def fx_pal():
    p = Pal(0x181010)
    # Кость: лавовый камень в тени, тень кости, кость, блик скорлупы.
    p.add("white", [0x7C686E, 0xBCB09A, 0xF4EEDA, 0xFFFFFF])
    # «gold» и «fire» это роли в рисунках пиратов: искры подбора и огонь; здесь янтарь аммонита
    # и лава.
    p.add("gold", [0x8A4A1C, 0xBC822C, 0xF4CC52, 0xFFF6C0])
    # Красная глина: тёмная, сырая, сухая, пыль на свету.
    p.add("dust", [0x522F28, 0x8E4C34, 0xC4805A, 0xEAC096])
    # Лава: остывшая корка, оранжевая шкура, жар, белое ядро.
    p.add("fire", [0x7A2014, 0xEC5E24, 0xF4B03A, 0xFFF4B6])
    return p


def _fill(c, pts, col):
    for (x, y) in pts:
        c.set(x, y, col)


def _clear(c, pts):
    for (x, y) in pts:
        if 0 <= x < c.w and 0 <= y < c.h:
            c.px[y][x] = None


def _at(cx, cy, a, r):
    return (cx + math.cos(a) * r, cy + math.sin(a) * r)


# --- Пыль --------------------------------------------------------------------------------------

def dust(p):
    """Глина из-под ног и лап: два низких клуба расходятся в стороны от следа, между ними
    невысокий горб; вверх летят камешки и осколок кости. К концу клубы редеют шашечкой."""
    frames = []
    d = p["dust"]
    rng = random.Random(7)
    stones = [(rng.uniform(-1.2, 1.2), rng.uniform(1.0, 1.6)) for _ in range(4)]
    for i in range(5):
        c = Canvas(24, 12)
        off = 3.6 + i * 1.3
        for k, (dx, r) in enumerate(((-off, 3.2), (off, 3.5), (0.0, 2.6))):
            rr = r + i * (0.5 if k < 2 else 0.15)
            ry = rr * (0.8 if k < 2 else 0.62)
            # Клуб лежит на земле: низ на предпоследней строке кадра.
            cy = 10.4 - ry
            S = ellipse(12 + dx, cy, rr, ry)
            _fill(c, S, d[1])
            # Светлая шапка смещена наружу от следа: клубы катятся в стороны.
            side = -0.8 if dx < 0 else 0.8 if dx > 0 else 0.0
            _fill(c, ellipse(12 + dx + side, cy - ry * 0.35, rr * 0.7, ry * 0.58) & S, d[2])
            if i < 3:
                c.set(12 + dx + side, cy - ry * 0.55, d[3])
                c.set(12 + dx + side + (1 if side >= 0 else -1), cy - ry * 0.55, d[3])
        # Тёмная подошва облака на земле.
        for x in range(24):
            for y in range(11, 5, -1):
                if c.get(x, y) is not None:
                    if c.get(x, y + 1) is None:
                        c.px[y][x] = d[0]
                    break
        # Камешки и осколок кости летят по дуге.
        for k, (vx, vy) in enumerate(stones):
            t = i + 0.7
            x = 12 + vx * t * 2.4 + (k - 1.5) * 1.6
            y = 7.0 - vy * t * 1.8 + 0.40 * t * t
            if y > 10.5 or y < 0 or i == 4:
                continue
            if k == 1:
                c.set(x, y, p["white"][2])
                c.set(x + (1 if vx > 0 else -1), y, p["white"][1])
            else:
                c.set(x, y, d[0])
        if i >= 3:
            for y in range(12):
                for x in range(24):
                    if c.get(x, y) is not None and ((x + y) % 2 or (i == 4 and x % 3 == 0)):
                        c.px[y][x] = None
        frames.append(c)
    return strip(frames)


# --- Искры монеты ------------------------------------------------------------------------------

def _swirl(c, p, turn, r_in, r_out, sweep, width, arms=3):
    """Янтарные рукава завитка аммонита: дуги раскручиваются из центра, к хвосту тоньше и темнее."""
    g = p["gold"]
    for k in range(arms):
        a0 = turn + k * 2 * math.pi / arms
        steps = 14
        prev = None
        for s in range(steps + 1):
            t = s / steps
            pt = _at(12, 12, a0 + sweep * t, r_in + (r_out - r_in) * t)
            if prev is not None:
                w = width * (1.0 - 0.75 * t)
                _fill(c, capsule(prev, pt, w, w), g[2] if t < 0.7 else g[1])
            prev = pt
        # Светлая жилка по голове рукава.
        for s in range(6):
            t = s / steps
            c.set(*_at(12, 12, a0 + sweep * t, r_in + (r_out - r_in) * t), g[3])


def spark(p):
    """Искры монеты: янтарный завиток аммонита раскручивается из ядра, рукава отрываются и
    тают блёстками по кругу."""
    frames = []
    g = p["gold"]
    for i in range(4):
        c = Canvas(24, 24)
        if i == 0:
            _swirl(c, p, 0.3, 1.5, 6.0, 1.9, 1.5)
            _fill(c, ellipse(12, 12, 2.6, 2.6), g[3])
            _fill(c, ellipse(11.6, 11.6, 1.2, 1.2), p["white"][3])
        elif i == 1:
            _swirl(c, p, 0.9, 3.0, 9.0, 1.8, 1.4)
            _fill(c, ellipse(12, 12, 1.8, 1.8), g[3])
        elif i == 2:
            # Рукава оторвались: короткие дуги на окружности и блёстки между ними.
            _swirl(c, p, 1.6, 7.0, 10.0, 1.0, 1.0)
            for k in range(3):
                c.set(*_at(12, 12, 0.6 + k * 2 * math.pi / 3, 4.5), g[3])
        else:
            for k in range(6):
                a = 2.3 + k * math.pi / 3
                x, y = _at(12, 12, a, 10.0 if k % 2 == 0 else 7.0)
                c.set(x, y, g[3])
                if k % 2 == 0:
                    c.set(x + 1, y, g[2])
                    c.set(x, y + 1, g[2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Удар --------------------------------------------------------------------------------------

def _fang(cx, cy, a, r0, r1, w):
    """Клык: широкое основание на `r0`, острие на `r1`, слегка загнут по часовой."""
    b = _at(cx, cy, a, r0)
    side = (-math.sin(a) * w, math.cos(a) * w)
    mid = _at(cx, cy, a + 0.10, r0 + (r1 - r0) * 0.6)
    tip = _at(cx, cy, a + 0.22, r1)
    return poly([(b[0] + side[0], b[1] + side[1]), (mid[0] + side[0] * 0.45, mid[1] + side[1] * 0.45), tip,
                 (mid[0] - side[0] * 0.5, mid[1] - side[1] * 0.5), (b[0] - side[0], b[1] - side[1])])


def star(p):
    """Звезда удара: укус. Вокруг жаркого ядра кольцо костяных клыков остриями наружу, длинные
    чередуются с короткими; ядро гаснет, клыки разлетаются осколками и тают крошкой."""
    frames = []
    w, g, f = p["white"], p["gold"], p["fire"]
    n = 8
    for i in range(4):
        c = Canvas(24, 24)
        if i < 2:
            r0 = (2.0, 4.0)[i]
            # Жар под клыками: рыжие клинья между ними.
            for k in range(n):
                a = (k + 0.5) * 2 * math.pi / n
                _fill(c, _fang(12, 12, a, r0, (6.5, 8.5)[i], 1.3), f[1])
            for k in range(n):
                a = k * 2 * math.pi / n
                r1 = ((10.0, 11.3)[i]) if k % 2 == 0 else ((7.5, 9.0)[i])
                F = _fang(12, 12, a, r0, r1, 1.7)
                _fill(c, F, w[2])
                # Тень клыка с нижней стороны и белая грань по хребту.
                for (x, y) in F:
                    if (x, y + 1) not in F and y > 12:
                        c.set(x, y, w[1])
                _fill(c, capsule(_at(12, 12, a + 0.05, r0 + 0.5), _at(12, 12, a + 0.12, r0 + (r1 - r0) * 0.5),
                                 0.3, 0.2), w[3])
            if i == 0:
                _fill(c, ellipse(12, 12, 3.6, 3.6), g[2])
                _fill(c, ellipse(12, 12, 2.4, 2.4), w[3])
            else:
                _fill(c, ellipse(12, 12, 4.8, 4.8) - ellipse(12, 12, 3.2, 3.2), g[2])
                _clear(c, ellipse(12, 12, 2.4, 2.4))
        elif i == 2:
            # Разлёт: осколки клыков на окружности и рыжая крошка между ними.
            for k in range(n):
                a = k * 2 * math.pi / n + 0.12
                r1 = 10.6 if k % 2 == 0 else 9.0
                _fill(c, _fang(12, 12, a, r1 - 3.2, r1, 1.0), w[2])
                c.set(*_at(12, 12, a + 0.4, 6.5), g[2 if k % 2 else 1])
        else:
            for k in range(n):
                a = k * 2 * math.pi / n + 0.25
                c.set(*_at(12, 12, a, 10.5 if k % 2 == 0 else 8.0), w[2] if k % 2 == 0 else g[2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Вспышка -----------------------------------------------------------------------------------

def _drop(cx, cy, a, r0, r1, w):
    """Капля лавы: тонкая шейка у центра, круглая голова на `r1`."""
    head = _at(cx, cy, a, r1 - w)
    return capsule(_at(cx, cy, a, r0), head, w * 0.35, w * 0.8) | ellipse(head[0], head[1], w, w)


def flash(p):
    """Вспышка выстрела: всплеск лавы. Круглое ядро выбрасывает семь капель на шейках, шейки
    рвутся, капли летят сами, под конец остаётся рваное кольцо корки и остывающие брызги."""
    frames = []
    f = p["fire"]
    n = 7
    for i in range(3):
        c = Canvas(32, 32)
        turn = 0.35 + i * 0.2
        for j in range(n):
            a = turn + j * 2 * math.pi / n
            far = j % 2 == 0
            r1 = ((10.0, 13.0, 14.2)[i]) * (1.0 if far else 0.82)
            w = ((2.6, 2.4, 1.7)[i]) * (1.0 if far else 0.85)
            r0 = (2.0, 5.0, r1 - 2.0 * w)[i] if i < 2 else r1 - 2.2 * w
            if i == 1 and not far:
                r0 = r1 - 2.6 * w      # короткие капли уже оторвались
            hx, hy = _at(16, 16, a, r1 - w)
            D = _drop(16, 16, a, r0, r1, w) if i < 2 else ellipse(hx, hy, w, w)
            _fill(c, D, f[1] if i < 2 else f[0])
            _fill(c, ellipse(hx, hy, w * 0.68, w * 0.68), f[2] if i < 2 else f[1])
            if i < 2:
                c.set(hx - 0.6, hy - 0.6, f[3])
            elif far:
                c.set(hx, hy, f[2])
        if i == 0:
            _fill(c, ellipse(16, 16, 6.2, 6.2), f[1])
            _fill(c, ellipse(16, 16, 5.0, 5.0), f[2])
            _fill(c, ellipse(15.6, 15.6, 3.4, 3.4), f[3])
            _fill(c, ellipse(15.2, 15.2, 1.6, 1.6), p["white"][3])
        elif i == 1:
            _fill(c, ellipse(16, 16, 7.4, 7.4), f[1])
            _fill(c, ellipse(16, 16, 6.0, 6.0), f[2])
            _fill(c, ellipse(16, 16, 4.4, 4.4), f[3])
            _clear(c, ellipse(16, 16, 2.4, 2.4))
        else:
            # Рваное кольцо остывающей корки.
            ring = ellipse(16, 16, 6.6, 6.6) - ellipse(16, 16, 5.0, 5.0)
            for (x, y) in ring:
                ang = math.atan2(y - 16, x - 16)
                if math.sin(ang * 5 + 0.8) > -0.35:
                    c.set(x, y, f[1] if math.sin(ang * 5 + 0.8) > 0.4 else f[0])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Пламя -------------------------------------------------------------------------------------

def fire(p):
    """Пламя нитро: вулканическая струя. Корень у трубы вверху узкий (20, 2), вниз к зрителю
    струя идёт клубами: три яруса круглых комьев огня, каждый шире прежнего и качается в свою
    сторону, низ рвётся на отдельные языки. Слои от остывшей корки по краю к белому ядру у
    корня; из струи летят угли и камни. 4 кадра 40×64."""
    W, H = 40, 64
    frames = []
    f = p["fire"]
    layers = [(1.0, 0), (0.80, 1), (0.58, 2), (0.34, 3)]
    for i in range(4):
        c = Canvas(W, H)
        rng = random.Random(50 + i)
        sway = [math.sin(i * 1.6 + k * 1.9) for k in range(4)]
        for li, (k, tone) in enumerate(layers):
            S = set()
            # Горло у корня: узкий клин.
            S |= poly([(20 - 3.2 * k - 0.6, 2), (20 + 3.2 * k + 0.6, 2),
                       (20 + 6.0 * k + sway[0], 16), (20 - 6.0 * k + sway[0], 16)])
            # Ярусы комьев: шире книзу, внутренние слои короче.
            reach = 0.55 + 0.45 * k
            for t, (cy, rx, ry) in enumerate(((15, 7.5, 7.0), (27, 11.0, 9.5), (39, 14.0, 10.0))):
                y = 2 + (cy - 2) * reach
                S |= ellipse(20 + sway[t] * (1.2 + t * 0.8), y, rx * k + 0.6, ry * k + 0.6)
            # Языки внизу: разной длины, дрожат по кадрам.
            base_y = 2 + 40 * reach
            for t in range(5):
                tx = 20 + (t - 2) * 6.0 * k + sway[(t + 1) % 4] * 1.4
                ln = (10.5 + 8.5 * math.sin(t * 2.3 + i * 1.9 + 1.0)) * (0.45 + 0.55 * k)
                S |= capsule((tx, base_y), (tx + (t - 2) * 0.9, base_y + ln), 3.0 * k + 0.4, 0.4)
            _fill(c, S, f[tone])
        # Белое ядро у корня.
        _fill(c, capsule((20, 3), (20 + sway[0] * 0.5, 12), 1.0, 1.6), p["white"][3])
        # Завитки корки внутри комьев: тёмные серпы по правому краю ярусов.
        for t, (cy, rx) in enumerate(((16, 6.0), (28, 9.5))):
            x0 = 20 + sway[t] * (1.2 + t * 0.8)
            for s in range(7):
                a = -0.5 + s * 0.22
                x, y = x0 + math.cos(a) * rx * (1 if (t + i) % 2 == 0 else -1), cy + math.sin(a) * rx * 0.8
                if c.get(int(round(x)), int(round(y))) is not None:
                    c.set(x, y, f[0])
        # Оторвавшиеся комья, камни и угли у кончиков.
        for k in range(3):
            tx = 20 + rng.uniform(-11, 11)
            ty = H - 12 + rng.uniform(0, 7)
            _fill(c, ellipse(tx, ty, 1.8, 2.2), f[1])
            c.set(tx, ty, f[2])
        for k in range(3):
            tx = rng.randint(5, 34)
            ty = rng.randint(30, H - 6)
            if c.get(tx, ty) is None:
                # Камень: тёмный с горячим краем.
                c.set(tx, ty, p["white"][0])
                c.set(tx + 1, ty, p["white"][0])
                c.set(tx, ty + 1, f[1])
        for _ in range(5):
            c.set(rng.randint(5, 35), rng.randint(H - 16, H - 3), f[3])
        c.outline(0)
        frames.append(c)
    return strip(frames)


def sprites_own():
    p = fx_pal()
    return {
        "fx16_dust": (dust(p), p.colors),
        "fx16_spark": (spark(p), p.colors),
        "fx16_star": (star(p), p.colors),
        "fx16_flash": (flash(p), p.colors),
        "fx16_fire": (fire(p), p.colors),
    }


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import dinosaurs16
        dinosaurs16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own())
