#!/usr/bin/env python3
"""Набор «Замки» для платформера × 16/32-bit «тропа» (#137), зеркало `space_trail16.py` (а оно
`pixel_trail16.py`): те же ключи, размеры холстов, число кадров и точки опоры. Вместо зарослей
чужой планеты дневной сказочный лес и дорога к замку: фон без неба в три слоя (светлая дымчатая
даль с холмами, силуэтами замков и елей; большие дубы со шляпой листвы сплошной полосой наверху и
свисающим плющом и вымпелами; яркая поросль у земли с розами и древками вымпелов) и листва над
кадром спереди; земля из булыжника с мхом по кромке, дерн с цветами по краю; арка из тёсаного
камня.

У фона и переднего плана свои палитры по 16 цветов (`CASTLES_BG`, `CASTLES_FG`); кабан-секач и
летучая мышь в палитре спрайтов `castles16.PALETTE` (слоты `crab_walk` и `parrot_fly`). Ленты
героя рисует `castles16.py`.

Свойства слотов те же, что у зеркала: фон без неба и стыкуется по краям; низ дали, кустов и
булыжника сплошной; у `par3_trees` между дубами прозрачно, листва сплошной полосой наверху; у
`par3_bushes` прозрачен верх, у `canopy_front` низ; кромка дёрна лежит на строке 4; враги
с красной обводкой опасности вместо чёрной, тело по центру кадра.

    python3 tools/castles_trail16.py --preview out.png [--scale=2] [--keys=par3_back,dec_bush]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import castles16  # noqa: E402
from castles16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, GOLD, BRASS, METAL, DARK,  # noqa: E402
                       RED, VIOLET, PLUM, SKIN, TAN)

# Палитра фона: светлая дымка дали, листва, стволы, герб.
HZ0, HZ1, HZ2, HZ3, L0, L1, L2, L3, L4, T0, T1, T2, DK, FL1, FL2, MO = range(16)
CASTLES_BG = [
    (0xE2, 0xF2, 0xEE),  # HZ0  просвет, блик дали
    (0xBC, 0xDC, 0xE0),  # HZ1  дымка
    (0x92, 0xBC, 0xC6),  # HZ2  дальние холмы
    (0x68, 0x96, 0xAE),  # HZ3  дальние замки и ели, глубина
    (0xDC, 0xF4, 0x84),  # L0   блик листвы
    (0x92, 0xD2, 0x5A),  # L1   листва, свет
    (0x4C, 0xA2, 0x4E),  # L2   листва
    (0x2C, 0x76, 0x46),  # L3   листва, тень
    (0x1C, 0x4A, 0x3C),  # L4   глубокая тень листвы
    (0xD2, 0xA4, 0x6A),  # T0   ствол, свет
    (0x9C, 0x6C, 0x40),  # T1   ствол
    (0x62, 0x40, 0x30),  # T2   ствол, тень
    (0x16, 0x1A, 0x20),  # DK   самая тёмная тень
    (0xF4, 0xD3, 0x5E),  # FL1  золото, цветы
    (0xD0, 0x34, 0x38),  # FL2  красные вымпелы, розы
    (0x6E, 0x9A, 0x3A),  # MO   плющ, лозы
]

# Палитра переднего плана: дёрн, булыжник, тёсаный камень, дерево и солома, розы.
FK, G0, G1, G2, G3, S0, S1, S2, S3, S4, ST0, ST1, W0, W1, W2, PINK = range(16)
CASTLES_FG = [
    (0x15, 0x10, 0x16),  # FK   обводка
    (0xDE, 0xF6, 0x8C),  # G0   кромка травы
    (0x8F, 0xCF, 0x58),  # G1   трава
    (0x3C, 0x92, 0x4C),  # G2
    (0x1E, 0x52, 0x3E),  # G3   тень травы
    (0xCE, 0xC2, 0xA8),  # S0   булыжник, свет
    (0x9E, 0x94, 0x88),  # S1   булыжник
    (0x74, 0x6A, 0x68),  # S2   грунт между камнями
    (0x4C, 0x46, 0x4C),  # S3   тень
    (0x28, 0x24, 0x2A),  # S4   щели
    (0xC4, 0xCC, 0xD8),  # ST0  сталь, светлый валун
    (0x80, 0x88, 0x9A),  # ST1  тень стали и валуна
    (0xF6, 0xDC, 0x70),  # W0   солома, свет
    (0xC8, 0x90, 0x3A),  # W1   солома, дерево
    (0x7C, 0x4E, 0x2C),  # W2   дерево, тень
    (0xE0, 0x40, 0x58),  # PINK розы, вымпелы
]


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wellipse(c, cx, cy, rx, ry, col, keep=None):
    """Эллипс на ленте, которая стыкуется по краям; `keep` красит только поверх этого цвета."""
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                if keep is None or c.get(int(x) % c.w, y) == keep:
                    _wset(c, x, y, col)


def _wpoly(c, pts, col):
    """Многоугольник на ленте, которая стыкуется по краям."""
    for k in (-c.w, 0, c.w):
        c.poly([(x + k, y) for x, y in pts], col)


def _foliage(c, rng, cx, cy, r, cols, spots=None, flat=0.55):
    """Шапка листвы: купол с волнистым краем, низ рваный на строке `cy`, свет сверху слева,
    тёмный испод, листовая крапинка. `cols` от светлого к тёмному: блик, свет, тело, тень."""
    hi, light, body, shade = cols
    h = r * flat
    ph = rng.uniform(0, 6)
    for y in range(int(cy - h * 1.2 - 2), int(cy) + 4):
        k = (cy - y) / max(h, 0.5)
        for x in range(int(cx - r * 1.15), int(cx + r * 1.15) + 1):
            u = (x - cx) / max(r, 0.5)
            if y <= cy:
                ang = math.atan2(max(k, 0.0), u)
                lim = 1.0 + 0.09 * math.sin(6 * ang + ph)
                if u * u + k * k > lim * lim:
                    continue
            else:
                bottom = cy + 1 + 1.4 + 1.4 * math.sin(x * 0.85 + ph)
                if y > bottom or abs(u) > 0.97:
                    continue
            if y > cy:
                col = shade
            elif k > 0.6 and u < 0.2:
                col = hi if k > 0.8 and -0.5 < u < 0.05 else light
            elif u < -0.5 or (k > 0.4 and u < 0.4):
                col = light
            elif u > 0.55 or k < 0.15:
                col = shade
            else:
                col = body
            roll = rng.random()
            if roll < 0.12 and col == body:
                col = light
            elif roll < 0.08 and col == light:
                col = body
            elif roll < 0.07 and col == shade and y <= cy:
                col = body
            _wset(c, x, y, col)
    if spots is not None:
        for _ in range(int(r * 0.45)):
            a = rng.uniform(-r * 0.7, r * 0.7)
            b = rng.uniform(0.15, 0.7) * h
            if abs(a) < r * math.sqrt(max(0.0, 1.0 - (b / h) ** 2)) - 1:
                _wset(c, cx + a, int(cy - b), spots)


def _trunk(c, x0, x1, y0, y1, cols, rng):
    """Ствол дуба: светлый край слева, борозды коры вдоль, сучковые глазки."""
    light, body, shade = cols
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            k = (x - x0) / max(x1 - x0, 1)
            _wset(c, x, y, light if k < 0.2 else (body if k < 0.7 else shade))
    for gx in range(int(x0) + 3, int(x1) - 2, 5):
        ph = rng.uniform(0, 6)
        for y in range(int(y0), int(y1)):
            wob = int(round(math.sin(y * 0.09 + ph) * 1.4))
            if (y + gx) % 11 < 8:
                _wset(c, gx + wob, y, shade)
    for _ in range(int((y1 - y0) / 55) + 1):
        kx = rng.uniform(x0 + 5, x1 - 6)
        ky = int(rng.uniform(y0 + 24, y1 - 30))
        _wellipse(c, kx, ky, 2.2, 3.2, T2)
        _wellipse(c, kx + 0.5, ky + 0.5, 1.0, 1.8, DK)
        _wset(c, kx - 2, ky - 3, T0)


def _crown_branch(c, x, y, side, col):
    """Толстый сук от ствола в сторону, на котором висит лоза."""
    for i in range(9):
        _wset(c, x + side * i, y - i // 3, col)
        _wset(c, x + side * i, y - i // 3 + 1, col)


def _ivy(c, x, y0, length, rng, col=MO, leaf=L2, tip=L1):
    """Плющ: волнистая плеть вниз, парами листьев по бокам, на конце светлый лист."""
    for y in range(int(y0), int(y0 + length)):
        _wset(c, x + math.sin(y * 0.08) * 2, y, col)
    for y in range(int(y0) + 4, int(y0 + length) - 2, 6):
        sx = x + math.sin(y * 0.08) * 2
        _wset(c, sx - 1, y, leaf)
        _wset(c, sx + 1, y + 1, leaf)
    ex = x + math.sin((y0 + length) * 0.08) * 2
    _wellipse(c, ex, y0 + length, 1.6, 1.3, tip)


def _pennant(c, x, y0, h, col=FL2, trim=FL1, pole=T2):
    """Вымпел на древке: древко вниз от `y0`, красный язык с двумя хвостами, золотая кайма."""
    for y in range(int(y0), int(y0 + h + 6)):
        _wset(c, x, y, pole)
    for j in range(h):
        w = 7 if j < h - 5 else 7 - (j - (h - 6)) * 1
        w = max(w, 1)
        for i in range(1, w + 1):
            # Вырез ласточкина хвоста у нижнего края.
            if j >= h - 5 and abs(i - 4) < (j - (h - 6)) * 0.7:
                continue
            _wset(c, x + i, y0 + 2 + j, col if j else trim)
    _wset(c, x, int(y0) - 1, trim)


def _castle_sil(c, x, base, s, body, hi, glint):
    """Силуэт замка вдали: стена с зубцами, донжон с конической крышей, две башни, бойницы."""
    c.rect(x - 20 * s, base - 14 * s, x + 20 * s, base, body)
    for dx in range(-20 * s, 20 * s + 1, 3 * s):
        c.rect(x + dx, base - 17 * s, x + dx + s, base - 14 * s, body)
    for tx, w, h, roof in ((x, 14, 42, True), (x - 21 * s, 9, 28, True), (x + 21 * s, 9, 24, False)):
        w *= s
        h *= s
        c.rect(tx - w // 2, base - h, tx + w // 2, base, body)
        c.rect(tx - w // 2, base - h, tx - w // 2 + 1, base, hi)
        if roof:
            c.poly([(tx, base - h - int(w * 1.3)), (tx + w // 2 + 2, base - h), (tx - w // 2 - 2, base - h)], body)
            c.line(tx, base - h - int(w * 1.3), tx, base - h - int(w * 1.3) - 5 * s, body, 1)
            c.rect(tx + 1, base - h - int(w * 1.3) - 5 * s, tx + 4 * s, base - h - int(w * 1.3) - 4 * s + s, body)
        else:
            for dx in range(-(w // 2), w // 2 + 1, 3):
                c.rect(tx + dx, base - h - 3, tx + dx + 1, base - h, body)
        c.rect(tx, base - h + 8 * s, tx, base - h + 11 * s, glint)
    c.rect(x - 3 * s, base - 8 * s, x + 3 * s, base, glint)
    c.ellipse(x, base - 8 * s, 3 * s, 3 * s, glint)


def _fir(c, x, base, h, col):
    """Дальняя ель острыми ярусами."""
    for k in range(4):
        top = base - h + k * h // 4
        w = 2 + k * 2
        _wpoly(c, [(x, top), (x + w, top + h // 3), (x - w, top + h // 3)], col)
    _wpoly(c, [(x - 1, base - 3), (x + 1, base - 3), (x + 1, base), (x - 1, base)], col)


# --- Фон ---------------------------------------------------------------------------------------

def par3_back():
    """Даль на весь экран, 512×277: светлая дымка, пятна света, два ряда холмов, замки с башнями и
    ели силуэтами; низ сплошной."""
    rng = random.Random(241)
    c = Canvas(512, 277)
    c.rect(0, 0, 511, 276, HZ1)
    # Пятна света в дымке.
    for x in range(0, 512, 13):
        _wellipse(c, x, rng.uniform(40, 170), rng.uniform(16, 32), rng.uniform(20, 44), HZ0, HZ1)
    for x in range(0, 512, 41):
        _wellipse(c, x + rng.uniform(-8, 8), rng.uniform(70, 130), rng.uniform(10, 18), rng.uniform(26, 40), HZ0)

    def ridge1(x):
        return 150 + 14 * math.sin(x * math.pi * 2 / 512 * 3 + 1.0) + 8 * math.sin(x * math.pi * 2 / 512 * 8)

    def ridge2(x):
        return 204 + 10 * math.sin(x * math.pi * 2 / 512 * 4 + 2.0) + 5 * math.sin(x * math.pi * 2 / 512 * 9)

    for x in range(512):
        c.rect(x, int(ridge1(x)), x, 276, HZ2)
    # Замки на дальней гряде, холм под ними ровный.
    for gx, s in ((118, 2), (392, 2)):
        base = int(ridge1(gx)) + 3
        c.rect(gx - 26 * s, base - 3, gx + 26 * s, base + 40, HZ2)
        _castle_sil(c, gx, base, s, HZ3, HZ2, HZ1)
    # Ели на гряде.
    for _ in range(46):
        x = rng.uniform(4, 508)
        if min(abs(x - 118), abs(x - 392)) < 60:
            continue
        _fir(c, int(x), int(ridge1(x)) + 4, rng.randint(22, 40), HZ3)
    for x in range(512):
        c.rect(x, int(ridge2(x)), x, 276, HZ3)
    for x in range(0, 512, 9):
        _wellipse(c, x + rng.uniform(-3, 3), rng.uniform(218, 234), rng.uniform(8, 14), rng.uniform(5, 9), HZ3)
    c.rect(0, 238, 511, 276, HZ3)
    for _ in range(60):
        _wset(c, rng.uniform(0, 512), int(rng.uniform(8, 120)), HZ0)
    return c


def par3_trees():
    """Большие дубы, 512×277, прозрачно между ними: стволы с корой и сучками расходятся корнями к
    земле, шляпа листвы наверху сплошной полосой, с неё свисают плющ и вымпелы."""
    rng = random.Random(242)
    c = Canvas(512, 277)
    for x, w in ((40, 30), (196, 22), (300, 38), (452, 26)):
        _trunk(c, x, x + w, 54, 262, (T0, T1, T2), rng)
        # Корни расходятся к земле.
        for side in (-1, 1):
            for i in range(14):
                yy = 248 + i
                spread = int(i * 0.9)
                if side < 0:
                    c.rect(max(x - spread, 0), yy, x + 3, yy, T1)
                else:
                    c.rect(x + w - 3, yy, min(x + w + spread, 511), yy, T2)
        _crown_branch(c, x - 1, 66, -1, T1)
        _crown_branch(c, x + w, 80, 1, T2)
    # Листва тремя рядами: нижний светлый над стволами, выше темнее.
    for x in range(0, 512, 34):
        _foliage(c, rng, x + rng.uniform(-6, 6), rng.uniform(44, 62), rng.uniform(26, 36), (L0, L1, L2, L3), FL2, 0.6)
    for x in range(0, 512, 26):
        _foliage(c, rng, x + rng.uniform(-6, 6), rng.uniform(16, 30), rng.uniform(22, 30), (L1, L2, L3, L4), None, 0.65)
    for x in range(0, 512, 30):
        _foliage(c, rng, x + rng.uniform(-6, 6), rng.uniform(2, 10), rng.uniform(20, 28), (L2, L3, L4, DK), None, 0.7)
    # Плющ с листьями и три вымпела на суках.
    for _ in range(11):
        _ivy(c, rng.uniform(0, 512), 46, rng.uniform(36, 104), rng)
    for px in (118, 250, 372):
        _pennant(c, px, 50, rng.randint(15, 20))
    return c


def par3_bushes():
    """Яркая поросль у земли, 512×120, прозрачный верх: кусты роз, высокие травы и древки с
    вымпелами; низ сплошной."""
    rng = random.Random(243)
    c = Canvas(512, 120)
    for x in range(0, 512, 13):
        cx = x + rng.uniform(-4, 4)
        roll = rng.random()
        if roll < 0.22:
            top = rng.uniform(40, 70)
            for y in range(int(top), 96):
                _wset(c, cx, y, T2)
                _wset(c, cx - 1, y, T1)
            _pennant(c, cx + 1, top - 1, rng.randint(10, 14))
            continue
        if roll < 0.4:
            # Высокая трава с колосьями.
            for _ in range(5):
                bx = cx + rng.uniform(-5, 5)
                bh = rng.uniform(28, 50)
                bend = rng.uniform(-3, 3)
                for j in range(int(bh)):
                    k = j / bh
                    _wset(c, bx + bend * k * k, 95 - j, L2 if j % 5 else L1)
                _wellipse(c, bx + bend, 95 - bh, 1.2, 3.0, FL1)
            continue
        top = rng.uniform(52, 82)
        r = rng.uniform(11, 19)
        _foliage(c, rng, cx, 96, r, (L0, L1, L2, L3), None, rng.uniform(0.9, 1.3) * (96 - top) / r)
    c.rect(0, 92, 511, 119, L4)
    for x in range(0, 512, 7):
        _foliage(c, rng, x + rng.uniform(-2, 2), rng.uniform(92, 98), rng.uniform(5, 9), (L1, L2, L3, L4))
    for _ in range(260):
        _wset(c, rng.uniform(0, 512), int(rng.uniform(99, 119)), L3 if rng.random() < 0.6 else DK)
    # Розы и цветы по зелени.
    for _ in range(54):
        x = rng.uniform(0, 512)
        y = int(rng.uniform(52, 100))
        if c.get(int(x) % 512, y) in (L1, L2, L3, L0):
            col = FL2 if rng.random() < 0.7 else FL1
            _wset(c, x, y, col)
            _wset(c, x + 1, y, col)
            _wset(c, x, y + 1, col)
    return c


def canopy_front():
    """Листва над кадром спереди, 256×56, прозрачный низ: тёмные кроны и свисающий плющ."""
    rng = random.Random(244)
    c = Canvas(256, 56)
    for x in range(0, 256, 22):
        _foliage(c, rng, x + rng.uniform(-4, 4), rng.uniform(10, 20), rng.uniform(18, 26), (L2, L3, L4, DK), None, 0.9)
    for x in range(0, 256, 30):
        _foliage(c, rng, x + rng.uniform(-4, 4), rng.uniform(0, 6), rng.uniform(16, 22), (L3, L4, DK, DK), None, 0.9)
    for _ in range(14):
        x = rng.uniform(0, 256)
        n = rng.randint(22, 46)
        for y in range(12, n):
            _wset(c, x + math.sin(y * 0.2) * 1.5, y, L4 if y % 5 else L3)
        for y in range(16, n - 2, 7):
            _wset(c, x + math.sin(y * 0.2) * 1.5 - 1, y, L3)
        _wset(c, x + math.sin(n * 0.2) * 1.5, n, L1)
    return c


# --- Передний план -----------------------------------------------------------------------------

def trail_soil():
    """Булыжник, 64×64 по кругу в обе стороны: округлые камни разного размера рядами, свет сверху
    слева, тёмные щели, редкие пятна мха."""
    rng = random.Random(251)
    n = 64
    c = Canvas(n, n)
    c.rect(0, 0, n - 1, n - 1, S4)

    def cobble(cx, cy, rx, ry):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                u = abs(x - cx) / rx
                v = abs(y - cy) / ry
                # Скруглённый квадрат: булыжник, не овал и не гранёный осколок.
                if u ** 2.6 + v ** 2.6 > 1.0:
                    continue
                lit = (x - cx) < -rx * 0.1 and (y - cy) < -ry * 0.05
                if lit and (x - cx) < -rx * 0.35 and (y - cy) < -ry * 0.3:
                    col = S0
                elif lit:
                    col = S0 if rng.random() < 0.5 else S1
                elif y > cy + ry * 0.55 or (x - cx) > rx * 0.6:
                    col = S3 if y > cy + ry * 0.7 else S2
                else:
                    col = S1
                c.set(x % n, y % n, col)

    y = 0.0
    while y < n:
        h = rng.uniform(3.4, 5.0)
        x = rng.uniform(0, 8)
        while x < n:
            w = rng.uniform(4.0, 8.0)
            cobble(x + w, y + h + rng.uniform(-0.6, 0.6), w - 0.5, h * rng.uniform(0.75, 1.0) - 0.3)
            x += 2 * w + rng.uniform(0.4, 1.8)
        y += 2 * h + rng.uniform(0.2, 0.8)
    for _ in range(30):
        c.set(rng.randrange(n), rng.randrange(n), S3)
    for _ in range(6):
        x, y = rng.randrange(n), rng.randrange(n)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0)):
            c.set((x + dx) % n, (y + dy) % n, G2 if (dx + dy) % 2 == 0 else G3)
        c.set(x, (y - 1) % n, G1)
    return c


def trail_edge():
    """Кромка дёрна, 32×18 по кругу: поверхность на строке 4, трава и цветы над ней, дёрн
    свисает бахромой с корешками в грунт; ниже прозрачно, там грунт."""
    rng = random.Random(252)
    c = Canvas(32, 18)
    top = 4
    for x in range(32):
        hang = top + 4 + int(1.5 + 1.5 * math.sin(x * 0.9) + rng.uniform(0, 2.5))
        c.rect(x, top, x, hang, G1)
        c.rect(x, top, x, top, G0)
        if x % 4 == 1:
            c.set(x, top + 1, G0)
        c.set(x, hang, G2)
        c.set(x, hang + 1, G3)
        if (x * 5) % 9 == 0:
            c.set(x, hang + 2, W2)
        if rng.random() < 0.5:
            h = rng.randint(1, 3)
            c.rect(x, top - h, x, top - 1, G1 if rng.random() < 0.6 else G0)
            if h == 3 and rng.random() < 0.5:
                c.set(x, top - h, PINK if rng.random() < 0.6 else W0)
    return c


def arch_bark():
    """Грань каменной арки, 32×32 по кругу: тёсаные блоки по 16×8 вразбежку, светлые верхние
    грани, швы раствором, трещины и пятна мха."""
    rng = random.Random(253)
    c = Canvas(32, 32)
    for row in range(4):
        y0 = row * 8
        shift = 0 if row % 2 == 0 else 8
        for bi in range(2):
            x0 = shift + bi * 16
            tone = rng.choice((S1, S1, S0, S2))
            for y in range(y0, y0 + 8):
                for x in range(x0, x0 + 16):
                    if y == y0 + 7:
                        col = S4
                    elif y == y0:
                        col = S0
                    elif x == x0 + 15:
                        col = S4
                    elif x == x0:
                        col = S0
                    elif y == y0 + 6 or x == x0 + 14:
                        col = S3
                    else:
                        col = tone
                    c.set(x % 32, y, col)
            for _ in range(6):
                c.set((x0 + rng.randrange(2, 14)) % 32, y0 + rng.randrange(2, 6), S2 if tone != S2 else S1)
    for _ in range(4):
        x = rng.randint(0, 31)
        y = rng.randint(0, 31)
        for k in range(rng.randint(3, 5)):
            c.set((x + k // 2) % 32, (y + k) % 32, S4)
    for _ in range(3):
        x = rng.randint(0, 31)
        y = rng.randint(0, 31)
        for dx in range(-2, 3):
            for dy in range(0, 2):
                if rng.random() < 0.75:
                    c.set((x + dx) % 32, (y + dy) % 32, G2 if dy == 0 else G3)
    return c


def _blade(c, x, h, bend, col, side, tip=None):
    for j in range(int(h)):
        k = j / h
        c.set(x + bend * k * k, c.h - 1 - j, col)
        if k < 0.55:
            c.set(x + bend * k * k + 1, c.h - 1 - j, side)
    if tip is not None:
        c.set(x + bend, c.h - int(h), tip)


def dec_grass(i):
    """Высокая трава перед героем, 32×24, два кадра качания; у части стеблей золотой колос."""
    rng = random.Random(261)
    c = Canvas(32, 24)
    for _ in range(16):
        x = rng.uniform(2, 30)
        col = rng.choice((G1, G2, G1, G0))
        h = rng.uniform(9, 22)
        bend = rng.uniform(-3, 3) + (1.5 if i else -0.5)
        ear = rng.random() < 0.35
        _blade(c, x, h, bend, col, G3 if col == G2 else G2, None)
        if ear:
            c.set(x + bend, c.h - int(h) - 1, W0)
            c.set(x + bend, c.h - int(h), W1)
            c.set(x + bend + 1, c.h - int(h) + 1, W0)
    return c


def dec_tuft(i):
    rng = random.Random(262)
    c = Canvas(32, 14)
    for _ in range(10):
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 11), rng.uniform(-2, 2) + (1 if i else 0), rng.choice((G0, G1, G2)), G3)
    return c


def dec_fern():
    """Пучок копий за героем, 48×32: деревянная стойка и веер из шести копий с вымпелами и
    стальными наконечниками."""
    rng = random.Random(263)
    c = Canvas(48, 32)
    for ang, length, flag in ((-158, 20, False), (-126, 26, True), (-98, 30, False), (-72, 27, True),
                              (-46, 23, False), (-20, 17, False)):
        a = math.radians(ang + rng.uniform(-2, 2))
        for j in range(int(length)):
            c.set(24 + math.cos(a) * j, 31 + math.sin(a) * j, W1 if j % 3 else W2)
            c.set(24 + math.cos(a) * j + 1, 31 + math.sin(a) * j, W2)
        tx = 24 + math.cos(a) * length
        ty = 31 + math.sin(a) * length
        px, py = -math.sin(a), math.cos(a)
        fx, fy = math.cos(a), math.sin(a)
        # Наконечник листом.
        c.poly([(tx + fx * 4, ty + fy * 4), (tx + px * 1.6, ty + py * 1.6), (tx - px * 1.6, ty - py * 1.6)], ST0)
        c.set(tx - fx, ty - fy, ST1)
        if flag:
            bx, by = tx - fx * 3, ty - fy * 3
            c.poly([(bx, by), (bx + 6, by + 1), (bx + 4, by + 3), (bx + 6, by + 5), (bx, by + 4)], PINK)
    # Стойка с поперечиной.
    c.rect(15, 28, 33, 31, W2)
    c.rect(15, 28, 33, 28, W1)
    c.rect(22, 26, 26, 28, W2)
    c.outline(FK)
    return c


def dec_bush():
    """Куст роз за героем, 64×36: пять холмиков листвы разной высоты, красные розы, шипастые
    плети; у земли тень."""
    rng = random.Random(264)
    c = Canvas(64, 36)
    for cx, cy, rx, ry in ((30, 20, 15, 11), (13, 25, 11, 8), (50, 24, 12, 9), (22, 30, 9, 6), (41, 31, 9, 6)):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                u = (x - cx) / rx
                v = (y - cy) / ry
                if u * u + v * v > 1.0:
                    continue
                if v < -0.35 and u < 0.1:
                    col = G0 if rng.random() < 0.3 else G1
                elif u > 0.5 or v > 0.45:
                    col = G3
                else:
                    col = G2 if rng.random() < 0.8 else G1
                c.set(x, y, col)
    # Розы: красный цветок с тёмной серединой и светлым бликом.
    for rxp, ryp in ((26, 11), (35, 14), (12, 21), (19, 16), (47, 19), (54, 24), (30, 22), (41, 25), (22, 28)):
        c.rect(rxp, ryp, rxp + 2, ryp + 2, PINK)
        c.set(rxp + 1, ryp + 1, FK)
        c.set(rxp, ryp, W0)
    for x, y in ((5, 29), (58, 30), (33, 8), (17, 12)):
        c.set(x, y, W0)
    c.rect(4, 32, 58, 35, G3)
    for x in range(4, 59):
        if rng.random() < 0.5:
            c.set(x, 31, G2)
        if rng.random() < 0.25:
            c.set(x, 32, G1)
    c.outline(FK)
    return c


def dec_rock():
    """Замшелый валун, 32×20: круглая серая глыба с трещиной, шапка травы и мха сверху."""
    c = Canvas(32, 20)
    c.ellipse(16, 12, 14, 8, ST1)
    c.rect(2, 12, 29, 19, ST1)
    c.ellipse(13, 9, 9, 4.5, ST0)
    c.ellipse(24, 15, 4, 3, S3)
    c.rect(0, 19, 31, 19, None)
    c.line(19, 11, 21, 17, FK, 1)
    c.line(21, 17, 18, 19, FK, 1)
    # Мох шапкой и пучки травы у подножия.
    c.poly([(4, 10), (8, 5), (15, 3), (22, 5), (26, 9), (21, 8), (15, 7), (9, 9)], G2)
    c.poly([(8, 5), (15, 3), (20, 5), (14, 6)], G1)
    c.set(13, 3, G0)
    c.poly([(1, 19), (3, 15), (6, 19)], G2)
    c.poly([(24, 19), (28, 14), (31, 19)], G1)
    c.outline(FK)
    return c


def dec_flowers():
    """Маки и лютики на стебельках среди травы, 32×20."""
    rng = random.Random(265)
    c = Canvas(32, 20)
    for _ in range(9):
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 9), rng.uniform(-2, 2), rng.choice((G1, G2)), G3)
    for x, y, petal in ((6, 9, PINK), (14, 6, W0), (22, 10, PINK), (27, 7, W0)):
        c.line(x, y + 2, x, 19, G2, 1)
        c.set(x - 1, y + 7, G1)
        c.set(x + 1, y + 9, G1)
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1), (-1, -1), (1, -1)):
            c.set(x + dx, y + dy, petal)
        c.set(x, y, W1 if petal == W0 else FK)
    return c


def dec_mush():
    """Стожки сена у ножек деревьев, 32×16: два конусом и один низкий, соломенные полосы."""
    c = Canvas(32, 16)
    for cx, h, w in ((9, 12, 7), (21, 14, 8), (28, 7, 4)):
        for j in range(h):
            k = j / h
            half = w * (1.0 - 0.7 * k) + 0.5
            for d in range(int(-half), int(half) + 1):
                u = d / max(half, 0.5)
                col = W0 if u < -0.2 else (W1 if u < 0.45 else W2)
                if (j + d) % 4 == 0 and col != W2:
                    col = W2 if col == W1 else W1
                c.set(cx + d, 15 - j, col)
    c.set(21, 0, W1)
    c.line(21, 0, 21, 2, W2, 1)
    c.outline(FK)
    return c


# --- Враги (палитра спрайтов) ------------------------------------------------------------------

def _danger(c):
    """Враг: тень как у всех, но обводка красная, а не чёрная: опасен, убить нельзя."""
    c.shade()
    c.outline(RED)
    return c


def crab(i):
    """Кабан-секач (слот краба-ползуна), четыре кадра: ноги по очереди, щетина гребнем вдоль
    хребта, железный ошейник с шипами, белые клыки. Шкура бурая с тёмной щетиной, чтобы красная
    обводка читалась. Тело по центру кадра, ноги до строки 29."""
    c = Canvas()
    for k, dx in enumerate((-9, -6, 5, 8)):
        lift = 1 if (k + i) % 2 == 0 else 0
        c.rect(16 + dx - 1, 25, 16 + dx, 29 - lift, DARK)
        c.rect(16 + dx - 1, 28 - lift, 16 + dx, 29 - lift, K)
    # Тело, хвост-закорючка и гребень щетины.
    c.ellipse(15, 21, 11, 6, TAN)
    c.line(4, 19, 2, 16 - (i % 2), DARK, 1)
    for x in range(8, 21, 2):
        c.line(x, 16, x + 1, 13 + (x + i) % 2, DARK, 1)
    # Голова с пятачком, ухом, клыками и ошейником.
    c.ellipse(25, 20.5, 5, 4.5, TAN)
    c.poly([(27, 21), (31, 22), (30, 25), (26, 25)], SKIN)
    c.poly([(21, 16), (22, 12), (25, 16)], DARK)
    c.rect(20, 17, 21, 24, METAL)
    c.set(19, 17, GREY)
    c.set(19, 20, GREY)
    c.set(19, 23, GREY)
    _danger(c)
    c.set(26, 19, WHITE)
    c.set(27, 19, K)
    c.set(28, 25, WHITE)
    c.set(29, 24, WHITE)
    c.set(29, 23, WHITE)
    return c


def drone(i):
    """Летучая мышь (слот дрона-глаза) летит вправо: тёмное тело по центру кадра, большие уши,
    красные глаза и клыки; перепончатые крылья с тремя костными пальцами машут (вверх, середина,
    вниз, середина), край перепонки зубцами. Тело не прыгает при развороте."""
    c = Canvas()
    wing = (-8, -2, 6, -2)[i]
    # Дальнее крыло позади тела, ближнее поверх.
    for dx, col in ((-3, PLUM), (1, VIOLET)):
        pts = [(14 + dx, 17), (19 + dx, 17), (22 + dx, 17 + wing * 1.4), (19 + dx, 16 + wing * 1.0),
               (16 + dx, 17 + wing * 1.3), (13 + dx, 16 + wing * 0.9), (10 + dx, 17 + wing * 1.4),
               (7 + dx, 16 + wing * 1.0), (5 + dx, 17 + wing * 1.5)]
        c.poly(pts, col)
        # Перепонка провисает книзу даже в плоских кадрах взмаха.
        c.poly([(14 + dx, 17), (19 + dx, 17), (19 + dx, 20 + wing * 0.5), (15 + dx, 21 + wing * 0.4),
                (10 + dx, 20 + wing * 0.8)], col)
        for tx, ty in ((22, 1.4), (13, 0.9 + 0.4), (5, 1.5)):
            c.line(15 + dx, 17, tx + dx, 17 + wing * ty, DARK, 1)
    # Тело, голова, уши.
    c.ellipse(15.5, 18.5, 4.5, 4.2, DARK)
    c.ellipse(21.5, 15.5, 3.4, 3.1, DARK)
    c.poly([(19, 14), (19, 9), (22, 13)], DARK)
    c.poly([(23, 13), (25, 9), (26, 14)], DARK)
    c.ellipse(15.5, 19.5, 2.4, 2.2, METAL)
    # Мордочка.
    c.poly([(23, 15), (27, 16), (24, 18)], DARK)
    _danger(c)
    c.set(22, 14, RED)
    c.set(24, 14, GOLD)
    c.set(23, 18, WHITE)
    c.set(25, 17, WHITE)
    return c


def sprites():
    """Ленты этой демки в палитре спрайтов (ленты героя в `castles16.sprites`)."""
    return {
        "crab_walk": strip([crab(i) for i in range(4)]),
        "parrot_fly": strip([drone(i) for i in range(4)]),
    }


def backdrop():
    """Слои фона и листва над кадром в палитре фона `CASTLES_BG`."""
    return {"par3_back": par3_back(), "par3_trees": par3_trees(), "par3_bushes": par3_bushes(),
            "canopy_front": canopy_front()}


def foreground():
    """Земля, арка, украшения в палитре переднего плана `CASTLES_FG`."""
    return {
        "trail_soil": trail_soil(),
        "trail_edge": trail_edge(),
        "arch_bark": arch_bark(),
        "dec_grass": strip([dec_grass(i) for i in range(2)]),
        "dec_tuft": strip([dec_tuft(i) for i in range(2)]),
        "dec_fern": dec_fern(),
        "dec_bush": dec_bush(),
        "dec_rock": dec_rock(),
        "dec_flowers": dec_flowers(),
        "dec_mush": dec_mush(),
    }


def preview(path, scale=2, keys=None):
    items = castles16.shaded(sprites())
    for key, canvas in foreground().items():
        items[key] = (canvas, CASTLES_FG)
    for key, canvas in backdrop().items():
        items[key] = (canvas, CASTLES_BG)
    if keys:
        items = {k: v for k, v in items.items() if k in keys}
    castles16.save_sheet(path, items, scale=scale)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        scale = 2
        keys = None
        for a in sys.argv:
            if a.startswith("--scale="):
                scale = int(a.split("=", 1)[1])
            if a.startswith("--keys="):
                keys = a.split("=", 1)[1].split(",")
        preview(sys.argv[sys.argv.index("--preview") + 1], scale, keys)
