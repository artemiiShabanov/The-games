#!/usr/bin/env python3
"""Мелкие эффекты «Фэнтези» для 16/32 (#137): те же ленты, что у пиратов (`pixel_fx16.py`) и
космоса (`space_fx16.py`), рисунок свой: сиреневая пыльца мха с завитками и золотыми спорами,
шестилучевой знак золотой руны, бирюзовый вихрь чар при ударе, шар огня с кольцом язычков от
волшебной палочки, витое чародейское пламя из-под кристалла вагонетки.

Ключи, кадры и опорные точки как у пиратов, их читает `scripts/demos/fx16.gd`:
`fx16_dust` 5 кадров 24×12 (облако лежит на нижней трети кадра и расходится в стороны),
`fx16_spark` и `fx16_star` по 4 кадра 24×24 с центром в (12, 12), `fx16_flash` 3 кадра 32×32 с
центром в (16, 16), `fx16_fire` 4 кадра 40×64: корень пламени узкий вверху по центру (20, 2),
вниз к зрителю оно расширяется и рвётся на языки. Палитра та же по составу: обводка и четыре
рампы по четыре тона (`white`, `gold`, `dust`, `fire`), цвета взяты от `fantasy16.PALETTE`.

    python3 tools/fantasy_fx16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites16 import Canvas, strip  # noqa: E402
from pixel_brawl16 import Pal, ellipse, poly, capsule  # noqa: E402


def fx_pal():
    p = Pal(0x15101E)
    # «white» здесь свечение кристалла посоха: синий мантии, бирюза, блик, белое ядро.
    p.add("white", [0x3A5ACC, 0x3AD4C2, 0xC8F8EC, 0xFFFFFF])
    # Золото руны и каймы мантии.
    p.add("gold", [0x8A5A24, 0xC2862C, 0xF6D058, 0xFFF6C0])
    # Пыльца и споры мха в сумерках: от сливовой тени к сиреневому камню и бледному блику.
    p.add("dust", [0x52468A, 0x8E86BC, 0xBEB6D8, 0xECE8F8])
    # Чародейский огонь: фиолетовый край, красный шар, золото, бледное ядро.
    p.add("fire", [0x522E8E, 0xDC465A, 0xF6A848, 0xFFF0B0])
    return p


def _fill(c, pts, col):
    for (x, y) in pts:
        c.set(x, y, col)


def _cut(c, pts):
    for (x, y) in pts:
        if 0 <= x < c.w and 0 <= y < c.h:
            c.px[y][x] = None


def _diamond(cx, cy, rx, ry):
    return poly([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)])


def _ring(cx, cy, r1, r0):
    return ellipse(cx, cy, r1, r1) - ellipse(cx, cy, r0, r0)


def _tri(cx, cy, r, a):
    return poly([(cx + math.cos(a + k * 2 * math.pi / 3) * r, cy + math.sin(a + k * 2 * math.pi / 3) * r)
                 for k in range(3)])


def _hexagram(cx, cy, r):
    """Шестилучевой знак: два треугольника остриём вверх и вниз."""
    return _tri(cx, cy, r, -math.pi / 2) | _tri(cx, cy, r, math.pi / 2)


def _swirl(cx, cy, a0, r0, r1, turn, w0, w1, steps=12):
    """Изогнутый луч вихря: цепочка кружков по спирали, от толстого корня к тонкому острию."""
    pts = set()
    for s in range(steps + 1):
        t = s / steps
        a = a0 + turn * t
        r = r0 + (r1 - r0) * t
        w = w0 + (w1 - w0) * t
        pts |= ellipse(cx + math.cos(a) * r, cy + math.sin(a) * r, w, w)
    return pts


# --- Пыльца ------------------------------------------------------------------------------------

def dust(p):
    """Пыльца из-под башмаков и колёс: два завитка мха катятся от центра в стороны, между ними
    растёт просвет, вверх летят золотые споры и бирюзовая искра; к концу завитки редеют."""
    frames = []
    d, g = p["dust"], p["gold"]
    spores = [(-0.9, 1.25), (0.5, 1.5), (1.1, 1.0)]
    for i in range(5):
        c = Canvas(24, 12)
        for side in (-1, 1):
            # Завиток: большой клуб впереди, два меньших тянутся хвостом к центру.
            lead = 3.0 + i * 1.05
            r = 2.8 + i * 0.3
            parts = [(lead, r), (lead - r * 0.95, r * 0.74), (lead - r * 1.75, r * 0.5)]
            for k, (dx, rr) in enumerate(parts):
                if dx < 0.4 and k:
                    continue
                ry = rr * 0.82
                cx, cy = 11.5 + side * dx, 10.4 - ry
                S = ellipse(cx, cy, rr, ry)
                _fill(c, S, d[1])
                _fill(c, ellipse(cx - 0.6, cy - ry * 0.32, rr * 0.7, ry * 0.58) & S, d[2])
                if k == 0:
                    # Улитка завитка: тёмная запятая внутри переднего клуба и блик на макушке.
                    if i < 4:
                        c.set(cx + side * 0.4, cy + 0.4, d[0])
                        c.set(cx + side * 1.3, cy + 0.9, d[0])
                    c.set(cx - 1, cy - ry * 0.55, d[3])
        # Тёмный низ там, где пыльца лежит на мху.
        for x in range(24):
            for y in range(11, 4, -1):
                if c.get(x, y) is not None:
                    if c.get(x, y + 1) is None:
                        c.px[y][x] = d[0]
                    break
        # Споры поднимаются и гаснут, не падая: пыльца легче воздуха.
        if i < 4:
            for k, (vx, vy) in enumerate(spores):
                t = i + 0.7
                x = 11.5 + vx * t * 1.9
                y = 6.6 - vy * t * 1.05
                if y < 0.5 or c.get(int(round(x)), int(round(y))) is not None:
                    continue
                c.set(x, y, p["white"][2] if k == 1 else g[2 + (i == 0)])
        if i >= 3:
            for y in range(12):
                for x in range(24):
                    if c.get(x, y) is not None and ((x + y) % 2 or (i == 4 and y % 3 == 0)):
                        c.px[y][x] = None
        frames.append(c)
    return strip(frames)


# --- Знак руны ---------------------------------------------------------------------------------

def spark(p):
    """Искры подобранной руны: шестилучевой золотой знак вспыхивает, растёт, пустеет до контура
    с огоньками на вершинах и рассыпается на шесть ромбиков."""
    frames = []
    g = p["gold"]
    for i in range(4):
        c = Canvas(24, 24)
        if i == 0:
            _fill(c, _hexagram(12, 12, 6.0), g[2])
            _fill(c, ellipse(12, 12, 2.6, 2.6), g[3])
            _fill(c, ellipse(12, 12, 1.4, 1.4), p["white"][3])
        elif i == 1:
            _fill(c, _hexagram(12, 12, 9.6), g[1])
            _fill(c, _hexagram(12, 12, 7.4), g[2])
            _fill(c, ellipse(12, 12, 3.6, 3.6), g[3])
            _fill(c, _diamond(12, 12, 1.2, 5.6) | _diamond(12, 12, 5.6, 1.2), p["white"][3])
        elif i == 2:
            # Контур знака: середина прозрачная, на вершинах огоньки.
            _fill(c, _hexagram(12, 12, 10.4), g[2])
            _cut(c, _hexagram(12, 12, 6.6) | ellipse(12, 12, 4.4, 4.4))
            for k in range(6):
                a = -math.pi / 2 + k * math.pi / 3
                c.set(12 + math.cos(a) * 9.2, 12 + math.sin(a) * 9.2, g[3])
            c.set(12, 12, g[3])
        else:
            for k in range(6):
                a = -math.pi / 2 + k * math.pi / 3
                x, y = 12 + math.cos(a) * 9.4, 12 + math.sin(a) * 9.4
                _fill(c, _diamond(int(round(x)), int(round(y)), 1, 1), g[2])
                c.set(int(round(x)), int(round(y)), g[3])
                b = a + math.pi / 6
                c.set(12 + math.cos(b) * 5.0, 12 + math.sin(b) * 5.0, g[1 + k % 2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Удар --------------------------------------------------------------------------------------

def star(p):
    """Звезда удара: вихрь чар. Белое ядро в золотом ободке, от него закручены пять бирюзовых
    лучей; дальше ядро раскрывается кольцом, лучи отрываются и докручиваются, под конец точки."""
    frames = []
    w, g = p["white"], p["gold"]
    n = 5
    for i in range(4):
        c = Canvas(24, 24)
        rot = -1.2 + i * 0.5
        if i < 2:
            r0, r1 = ((1.5, 9.2), (4.6, 10.0))[i]
            for k in range(n):
                a = rot + k * 2 * math.pi / n
                _fill(c, _swirl(12, 12, a, r0, r1, 1.0, 1.9 - i * 0.3, 0.3), w[0])
                _fill(c, _swirl(12, 12, a + 0.08, r0, r1 - 0.8, 0.95, 1.2 - i * 0.2, 0.2), w[1])
                _fill(c, _swirl(12, 12, a + 0.12, r0, r0 + (r1 - r0) * 0.5, 0.5, 0.5, 0.2), w[2])
                # Золотые брызги между лучами.
                b = a + 1.25
                c.set(12 + math.cos(b) * (6.5 + i * 3), 12 + math.sin(b) * (6.5 + i * 3), g[2])
            if i == 0:
                _fill(c, ellipse(12, 12, 4.0, 4.0), g[2])
                _fill(c, ellipse(12, 12, 3.0, 3.0), w[3])
                c.set(11, 11, w[2])
            else:
                _fill(c, _ring(12, 12, 4.4, 2.9), w[3])
                _fill(c, _ring(12, 12, 5.2, 4.4), g[2])
                _fill(c, ellipse(12, 12, 2.9, 2.9), w[2])
                _fill(c, ellipse(12, 12, 1.4, 1.4), w[1])
        elif i == 2:
            for k in range(n):
                a = rot + k * 2 * math.pi / n
                _fill(c, _swirl(12, 12, a + 0.5, 7.6, 10.4, 0.6, 1.0, 0.3, 8), w[1])
                _fill(c, _swirl(12, 12, a + 0.55, 7.8, 9.4, 0.4, 0.4, 0.2, 6), w[2])
                b = a - 0.25
                c.set(12 + math.cos(b) * 5.6, 12 + math.sin(b) * 5.6, g[2])
        else:
            for k in range(n):
                a = rot + k * 2 * math.pi / n + 0.9
                c.set(12 + math.cos(a) * 10.2, 12 + math.sin(a) * 10.2, w[2])
                c.set(12 + math.cos(a - 0.3) * 8.6, 12 + math.sin(a - 0.3) * 8.6, w[1])
                c.set(12 + math.cos(a + 0.7) * 6.0, 12 + math.sin(a + 0.7) * 6.0, g[2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Вспышка -----------------------------------------------------------------------------------

def flash(p):
    """Вспышка выстрела: рождение огненного шара у палочки. Круглый шар в слоях от фиолетового
    края к бледному ядру с венцом загнутых язычков; затем шар раскрывается в кольцо огня с
    угольком в середине; под конец кольцо рвётся на дуги и искры."""
    frames = []
    f = p["fire"]
    n = 8
    for i in range(3):
        c = Canvas(32, 32)
        rot = 0.2 + i * 0.35
        if i == 0:
            for tone, k in ((0, 1.0), (1, 0.8), (2, 0.55)):
                for j in range(n):
                    a = rot + j * 2 * math.pi / n
                    ln = 12.0 if j % 2 == 0 else 10.2
                    _fill(c, _swirl(16, 16, a, 5.0, 5.0 + (ln - 5.0) * k, 0.55 * k, 2.6 * k, 0.4), f[tone])
            _fill(c, ellipse(16, 16, 7.6, 7.6), f[0])
            _fill(c, ellipse(16, 16, 6.6, 6.6), f[1])
            _fill(c, ellipse(15.6, 15.6, 5.0, 5.0), f[2])
            _fill(c, ellipse(15.2, 15.2, 3.2, 3.2), f[3])
            _fill(c, ellipse(14.8, 14.8, 1.5, 1.5), p["white"][3])
        elif i == 1:
            for tone, k in ((0, 1.0), (1, 0.72)):
                for j in range(n):
                    a = rot + j * 2 * math.pi / n
                    ln = 14.2 if j % 2 == 0 else 12.6
                    _fill(c, _swirl(16, 16, a, 9.0, 9.0 + (ln - 9.0) * k, 0.4 * k, 2.2 * k, 0.4), f[tone])
            _fill(c, _ring(16, 16, 11.4, 5.6), f[0])
            _fill(c, _ring(16, 16, 10.6, 6.4), f[1])
            _fill(c, _ring(16, 16, 9.6, 7.2), f[2])
            _fill(c, _ring(16, 16, 8.8, 8.0), f[3])
            _fill(c, ellipse(16, 16, 3.0, 3.0), f[2])
            _fill(c, ellipse(16, 16, 1.8, 1.8), f[3])
        else:
            # Рваное кольцо: четыре дуги с просветами, между ними искры.
            ring = _ring(16, 16, 13.6, 10.4)
            core = _ring(16, 16, 12.8, 11.4)
            for (x, y) in ring:
                a = (math.atan2(y - 16, x - 16) - rot) % (math.pi / 2)
                if a < 1.0:
                    c.set(x, y, f[2] if (x, y) in core else f[1])
            for j in range(4):
                a = rot + 1.28 + j * math.pi / 2
                c.set(16 + math.cos(a) * 12.0, 16 + math.sin(a) * 12.0, f[3])
                c.set(16 + math.cos(a) * 7.0, 16 + math.sin(a) * 7.0, f[2])
                c.set(16 + math.cos(a - 0.8) * 5.0, 16 + math.sin(a - 0.8) * 5.0, f[3])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Пламя -------------------------------------------------------------------------------------

def _strand(root, length, amp, phase, sign, r_mid, wave=0.115):
    """Прядь витого пламени: от узкого корня вниз, качается синусом вокруг оси и сходит в
    остриё; `sign` разводит две пряди в противофазе, чтобы они переплетались."""
    pts = set()
    steps = int(length)
    for s in range(steps + 1):
        t = s / steps
        y = root[1] + length * t
        grow = min(t / 0.3, 1.0)
        x = root[0] + sign * math.sin(s * wave + phase) * amp * grow
        r = r_mid * (0.3 + 0.7 * math.sin(grow * math.pi / 2)) if t < 0.3 \
            else r_mid * (1.0 - ((t - 0.3) / 0.7) ** 1.6) + 0.5
        pts |= ellipse(x, y, r, r * 1.2)
    return pts


def _glint(c, x, y, ramp, big):
    """Четырёхлучевая искорка кристалла."""
    if c.get(x, y) is not None:
        return
    if big:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if c.get(x + dx, y + dy) is None:
                c.set(x + dx, y + dy, ramp[1])
    c.set(x, y, ramp[2])


def fire(p):
    """Пламя нитро: чародейский огонь из-под кристалла вагонетки. Корень узкий вверху по
    центру, вниз к зрителю две пряди огня расходятся и переплетаются косой, между ними короткий
    третий язык; пряди бегут волной по кадрам. Слои от фиолетового края через красный и золото к
    бледной сердцевине, у корня бирюзовое ядро кристалла, вокруг кончиков бирюзовые искорки.
    4 кадра 40×64."""
    W, H = 40, 64
    frames = []
    f, w = p["fire"], p["white"]
    layers = [(1.0, 0), (0.76, 1), (0.50, 2), (0.24, 3)]
    for i in range(4):
        c = Canvas(W, H)
        rng = random.Random(70 + i)
        ph = -i * math.pi / 2
        for k, tone in layers:
            S = set()
            # Две длинные пряди в противофазе и короткий язык по оси.
            S |= _strand((20, 2), 56.0 * (0.52 + 0.48 * k), 8.5, ph, 1, 6.6 * k + 0.5)
            S |= _strand((20, 2), 49.0 * (0.52 + 0.48 * k), 8.5, ph + 0.5, -1, 6.0 * k + 0.5)
            S |= _strand((20, 2), 30.0 * (0.52 + 0.48 * k), 2.0, ph + 1.2, 1, 5.2 * k + 0.5, 0.2)
            # Горловина у кристалла: общий корень не уже трёх пикселей.
            S |= ellipse(20, 4, 1.8 + 2.4 * k, 3.0)
            # Строка 0 остаётся под обводку корня.
            _fill(c, {q for q in S if q[1] >= 1}, f[tone])
        # Ядро кристалла у корня: бирюза с белой серединой.
        _fill(c, ellipse(20, 6, 2.4, 4.4), w[2])
        _fill(c, ellipse(20, 6, 1.2, 3.0), w[3])
        c.set(20, 11, w[1])
        c.set(20, 12, w[1])
        # Оторвавшиеся капли огня под кончиками прядей.
        for k in range(2):
            tx = 20 + (k * 2 - 1) * rng.uniform(4, 9)
            ty = H - 8 + rng.uniform(-2, 3)
            if c.get(int(tx), int(ty)) is None and c.get(int(tx), int(ty) - 4) is None:
                _fill(c, ellipse(tx, ty, 1.3, 2.1), f[1])
                c.set(tx, ty - 1, f[2])
        # Искорки кристалла по краям, крупные и точками.
        for k in range(6):
            x, y = rng.randint(4, 35), rng.randint(20, H - 4)
            _glint(c, x, y, w, k < 2)
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
        import fantasy16
        fantasy16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own())
