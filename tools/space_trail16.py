#!/usr/bin/env python3
"""Набор «Космос» для платформера × 16/32-bit «тропа» (#136), зеркало `pixel_trail16.py`: те же
ключи, размеры холстов, число кадров и точки опоры. Вместо леса заросли светящихся грибов и
кристаллов чужой планеты: фон без неба в три слоя (тёмная даль с силуэтами, большие грибы со
шляпками сплошной полосой наверху, яркая поросль у земли) и шляпки над кадром спереди; земля из
реголита и базальта с фиолетовым мхом по кромке; арка кристальная.

У фона и переднего плана свои палитры по 16 цветов (`SPACE_BG`, `SPACE_FG`); краб-ползун и
дрон-глаз в палитре спрайтов `space16.PALETTE`. Ленты героя рисует `space16.py`.

    python3 tools/space_trail16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import space16  # noqa: E402
from space16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, GOLD, BRASS, METAL, DARK, RED,  # noqa: E402
                     VIOLET, PLUM)

# Палитра фона: тёмная даль, свечение шляпок, ножки, кристаллы, споры.
HZ0, HZ1, HZ2, HZ3, L0, L1, L2, L3, L4, T0, T1, T2, DK, FL1, FL2, MO = range(16)
SPACE_BG = [
    (0x54, 0x44, 0x92),  # HZ0  просвет в дали, кромка дальних шляпок
    (0x40, 0x34, 0x7C),  # HZ1  дальние шляпки
    (0x30, 0x28, 0x66),  # HZ2  дальние ножки
    (0x22, 0x1C, 0x50),  # HZ3  глубина дали
    (0xC0, 0xF8, 0xF0),  # L0   блик шляпки, свечение
    (0x62, 0xDC, 0xD8),  # L1   шляпка, свет
    (0x30, 0xA8, 0xBC),  # L2   шляпка
    (0x28, 0x70, 0x9E),  # L3   шляпка, тень
    (0x24, 0x42, 0x78),  # L4   глубокая тень шляпки
    (0xCC, 0xB8, 0xEC),  # T0   ножка, свет
    (0x90, 0x76, 0xC2),  # T1   ножка
    (0x5C, 0x46, 0x92),  # T2   ножка, тень
    (0x12, 0x0E, 0x2A),  # DK   самая тёмная тень
    (0xF6, 0xE2, 0x7C),  # FL1  споры, огоньки
    (0xF0, 0x6C, 0xC2),  # FL2  розовые пятна
    (0xA4, 0x60, 0xE4),  # MO   фиолетовые кристаллы, усики
]

# Палитра переднего плана: мох, реголит, базальт, кристалл, огоньки.
FK, G0, G1, G2, G3, S0, S1, S2, S3, S4, ST0, ST1, W0, W1, W2, PINK = range(16)
SPACE_FG = [
    (0x14, 0x10, 0x22),  # FK   обводка
    (0xEA, 0xBC, 0xFC),  # G0   кромка мха
    (0xBC, 0x7C, 0xEE),  # G1   мох
    (0x86, 0x4E, 0xCA),  # G2
    (0x54, 0x30, 0x90),  # G3   тень мха
    (0x8E, 0x94, 0xAE),  # S0   камень реголита, свет
    (0x68, 0x6E, 0x8C),  # S1   камень
    (0x4A, 0x4E, 0x6C),  # S2   грунт
    (0x32, 0x34, 0x50),  # S3   тень грунта
    (0x1E, 0x1E, 0x34),  # S4   щели
    (0xC6, 0xCE, 0xDE),  # ST0  метеорит
    (0x82, 0x8A, 0xA6),  # ST1  тень метеорита
    (0xAC, 0xF2, 0xF0),  # W0   кристалл, свет
    (0x4E, 0xBA, 0xCA),  # W1   кристалл
    (0x2C, 0x72, 0x9A),  # W2   тень кристалла
    (0xF6, 0xE2, 0x7C),  # PINK огоньки, споры
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


def _cap(c, rng, cx, cy, r, cols, spots=None, flat=0.55):
    """Шляпка гриба куполом: низ ровный на строке `cy`, свет сверху слева, тёмный испод с
    пластинками, пятна. `cols` от светлого к тёмному: блик, свет, тело, тень."""
    hi, light, body, shade = cols
    h = r * flat
    for y in range(int(cy - h - 1), int(cy) + 1):
        k = (cy - y) / max(h, 0.5)
        if k > 1.0:
            continue
        half = r * math.sqrt(max(0.0, 1.0 - k * k))
        for x in range(int(cx - half), int(cx + half) + 1):
            u = (x - cx) / max(r, 0.5)
            if k > 0.72 and u < 0.25:
                col = hi if k > 0.86 and -0.45 < u < 0.05 else light
            elif u < -0.55 or k > 0.45 and u < 0.45:
                col = light
            elif u > 0.6 or k < 0.18:
                col = shade
            else:
                col = body
            _wset(c, x, y, col)
    # Испод: тёмная полоса с пластинками.
    for x in range(int(cx - r * 0.86), int(cx + r * 0.86) + 1):
        _wset(c, x, int(cy) + 1, shade)
        if r > 9 and (x + int(cx)) % 3 == 0:
            _wset(c, x, int(cy) + 2, shade)
    if spots is not None:
        for _ in range(int(r * 0.5)):
            a = rng.uniform(-r * 0.7, r * 0.7)
            b = rng.uniform(0.2, 0.8) * h
            if abs(a) < r * math.sqrt(max(0.0, 1.0 - (b / h) ** 2)) - 1:
                _wset(c, cx + a, int(cy - b), spots)
                if r > 12:
                    _wset(c, cx + a + 1, int(cy - b), spots)


def _stalk(c, x0, x1, y0, y1, cols, rng, rings=True):
    """Ножка гриба: светлый край слева, волокна вдоль, кольца и светящиеся поры."""
    light, body, shade = cols
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            k = (x - x0) / max(x1 - x0, 1)
            _wset(c, x, y, light if k < 0.2 else (body if k < 0.7 else shade))
    for gx in range(int(x0) + 4, int(x1) - 2, 6):
        ph = rng.uniform(0, 6)
        for y in range(int(y0), int(y1)):
            wob = int(round(math.sin(y * 0.11 + ph) * 1.2))
            if (y + gx) % 13 < 9:
                _wset(c, gx + wob, y, shade)
    if rings:
        for _ in range(int((y1 - y0) / 48) + 1):
            ry = int(rng.uniform(y0 + 14, y1 - 20))
            for x in range(int(x0) - 1, int(x1) + 1):
                _wset(c, x, ry, light if x < x0 + (x1 - x0) * 0.4 else body)
                _wset(c, x, ry + 1, shade)
        for _ in range(int((y1 - y0) / 30) + 1):
            px = rng.uniform(x0 + 3, x1 - 4)
            py = int(rng.uniform(y0 + 8, y1 - 8))
            _wset(c, px, py, L1)
            _wset(c, px, py + 1, L2)


def _crystal(c, x, base, h, w, cols, lean=0.0):
    """Кристалл-шпиль от земли `base` вверх на `h`: светлая грань слева, тёмная справа."""
    light, body, shade = cols
    for j in range(int(h)):
        k = j / max(h, 1.0)
        half = w * (1.0 - k) * 0.5 if k > 0.3 else w * 0.5 * (0.75 + k * 0.85)
        cx = x + lean * j
        for dx in range(int(-half), int(half) + 1):
            u = dx / max(half, 0.5)
            _wset(c, cx + dx, int(base - j), light if u < -0.25 else (body if u < 0.4 else shade))


# --- Фон ---------------------------------------------------------------------------------------

def par3_back():
    """Даль на весь экран, 512×277: тёмная глубина, силуэты высоких грибов и шпилей, редкие огни
    спор; низ сплошной."""
    rng = random.Random(141)
    c = Canvas(512, 277)
    c.rect(0, 0, 511, 276, HZ3)
    # Пятна света в глубине, как просветы.
    for x in range(0, 512, 11):
        _wellipse(c, x, rng.uniform(120, 190), rng.uniform(16, 30), rng.uniform(30, 52), HZ2)
    for x in range(0, 512, 37):
        _wellipse(c, x + rng.uniform(-8, 8), rng.uniform(140, 180), rng.uniform(10, 16), rng.uniform(22, 34), HZ1, HZ2)
    # Дальние грибы: тонкая ножка и купол.
    for _ in range(30):
        x = rng.uniform(0, 512)
        top = rng.uniform(30, 150)
        w = rng.uniform(3, 6)
        for y in range(int(top), 277):
            for dx in range(int(w)):
                _wset(c, x + dx, y, HZ1 if dx < w * 0.4 else HZ2)
        r = rng.uniform(12, 26)
        _cap(c, rng, x + w / 2, top, r, (HZ0, HZ0, HZ1, HZ2), flat=0.5)
    # Шпили кристаллов между ними.
    for _ in range(18):
        _crystal(c, rng.uniform(0, 512), 240, rng.uniform(30, 90), rng.uniform(6, 12), (HZ0, HZ1, HZ2),
                 rng.uniform(-0.12, 0.12))
    for _ in range(70):
        _wset(c, rng.uniform(0, 512), int(rng.uniform(10, 230)), HZ0)
    # Поросль у земли и сплошной низ.
    for x in range(0, 512, 10):
        _cap(c, rng, x + rng.uniform(-3, 3), rng.uniform(224, 240), rng.uniform(8, 14), (HZ0, HZ1, HZ1, HZ2))
    c.rect(0, 238, 511, 276, HZ3)
    return c


def par3_trees():
    """Большие грибы, 512×277, прозрачно между ними: ножки с волокнами и кольцами расходятся к
    земле, шляпки наверху сплошной полосой, с испода свисают светящиеся усики."""
    rng = random.Random(142)
    c = Canvas(512, 277)
    for x, w in ((40, 30), (196, 22), (300, 38), (452, 26)):
        _stalk(c, x, x + w, 40, 262, (T0, T1, T2), rng)
        # Основание расходится к земле.
        for side in (-1, 1):
            for i in range(14):
                yy = 248 + i
                spread = int(i * 0.9)
                if side < 0:
                    c.rect(max(x - spread, 0), yy, x + 3, yy, T1)
                else:
                    c.rect(x + w - 3, yy, min(x + w + spread, 511), yy, T2)
    # Шляпки: нижний ряд крупных куполов над ножками и между ними, верхний ряд темнее.
    for x in range(0, 512, 34):
        _cap(c, rng, x + rng.uniform(-6, 6), rng.uniform(44, 62), rng.uniform(26, 36), (L0, L1, L2, L3), FL2, 0.6)
    for x in range(0, 512, 26):
        _cap(c, rng, x + rng.uniform(-6, 6), rng.uniform(16, 30), rng.uniform(22, 30), (L1, L2, L3, L4), None, 0.65)
    for x in range(0, 512, 30):
        _cap(c, rng, x + rng.uniform(-6, 6), rng.uniform(2, 10), rng.uniform(20, 28), (L2, L3, L4, DK), None, 0.7)
    # Усики с огоньками на концах.
    for _ in range(11):
        x = rng.uniform(0, 512)
        length = rng.uniform(36, 104)
        for y in range(46, int(46 + length)):
            _wset(c, x + math.sin(y * 0.08) * 2, y, MO if y % 7 else L2)
        ex = x + math.sin((46 + length) * 0.08) * 2
        _wellipse(c, ex, 46 + length, 1.5, 1.5, L1)
        _wset(c, ex, int(46 + length), L0)
    return c


def par3_bushes():
    """Яркая поросль у земли, 512×120, прозрачный верх: грибы и кристаллы вперемешку; низ
    сплошной."""
    rng = random.Random(143)
    c = Canvas(512, 120)
    for x in range(0, 512, 13):
        cx = x + rng.uniform(-4, 4)
        if rng.random() < 0.3:
            _crystal(c, cx, 96, rng.uniform(26, 50), rng.uniform(7, 12), (L0, MO, T2), rng.uniform(-0.15, 0.15))
            continue
        top = rng.uniform(46, 80)
        w = rng.uniform(4, 7)
        for y in range(int(top), 96):
            for dx in range(int(w)):
                _wset(c, cx - w / 2 + dx, y, T0 if dx < w * 0.35 else (T1 if dx < w * 0.75 else T2))
        _cap(c, rng, cx, top, rng.uniform(11, 19), (L0, L1, L2, L3), FL2 if rng.random() < 0.6 else L0)
    c.rect(0, 92, 511, 119, L4)
    for x in range(0, 512, 7):
        _cap(c, rng, x + rng.uniform(-2, 2), rng.uniform(92, 98), rng.uniform(5, 9), (L1, L2, L3, L4))
    for _ in range(260):
        x = rng.uniform(0, 512)
        y = rng.uniform(99, 119)
        _wset(c, x, int(y), L3 if rng.random() < 0.6 else DK)
    for _ in range(46):
        x = rng.uniform(0, 512)
        y = rng.uniform(30, 104)
        if c.get(int(x) % 512, int(y)) is None:
            _wset(c, x, int(y), FL1)
    return c


def canopy_front():
    """Шляпки над кадром спереди, 256×56, прозрачный низ: тёмные исподы и свисающие усики."""
    rng = random.Random(144)
    c = Canvas(256, 56)
    for x in range(0, 256, 22):
        _cap(c, rng, x + rng.uniform(-4, 4), rng.uniform(10, 20), rng.uniform(18, 26), (L2, L3, L4, DK), None, 0.9)
    for x in range(0, 256, 30):
        _cap(c, rng, x + rng.uniform(-4, 4), rng.uniform(0, 6), rng.uniform(16, 22), (L3, L4, DK, DK), None, 0.9)
    for _ in range(14):
        x = rng.uniform(0, 256)
        n = rng.randint(22, 46)
        for y in range(12, n):
            _wset(c, x + math.sin(y * 0.2) * 1.5, y, L4 if y % 5 else L3)
        _wset(c, x + math.sin(n * 0.2) * 1.5, n, L1)
    return c


# --- Передний план -----------------------------------------------------------------------------

def trail_soil():
    """Реголит, 64×64 по кругу в обе стороны: угловатые камни разного размера рядами, свет сверху
    слева, тёмные щели, редкие вкрапления кристалла."""
    rng = random.Random(151)
    n = 64
    c = Canvas(n, n)
    c.rect(0, 0, n - 1, n - 1, S4)

    def stone(cx, cy, rx, ry):
        cut = rng.uniform(0.2, 0.45)
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                u = abs(x - cx) / rx
                v = abs(y - cy) / ry
                # Гранёный камень: срезанные углы вместо овала.
                if u > 1.0 or v > 1.0 or u + v > 1.0 + cut:
                    continue
                lit = (x - cx) < -rx * 0.15 and (y - cy) < -ry * 0.1
                col = S0 if lit else (S3 if y > cy + ry * 0.5 else (S2 if (x - cx) > rx * 0.45 else S1))
                c.set(x % n, y % n, col)

    y = 0.0
    while y < n:
        h = rng.uniform(3.0, 5.2)
        x = rng.uniform(0, 8)
        while x < n:
            w = rng.uniform(3.5, 8.5)
            # Камни в ряду разной высоты и чуть выше или ниже строки: не кладка.
            hh = h * rng.uniform(0.65, 1.0)
            stone(x + w, y + h + rng.uniform(-0.8, 0.8), w - 0.6, hh - 0.4)
            x += 2 * w + rng.uniform(0.5, 2.5)
        y += 2 * h + rng.uniform(0.3, 1.0)
    for _ in range(36):
        c.set(rng.randrange(n), rng.randrange(n), S3)
    for _ in range(5):
        x, y = rng.randrange(n), rng.randrange(n)
        c.set(x, y, W1)
        c.set((x + 1) % n, y, W2)
    return c


def trail_edge():
    """Кромка мха, 32×18 по кругу: поверхность на строке 4, ростки над ней, мох свисает бахромой
    в грунт; ниже прозрачно, там грунт."""
    rng = random.Random(152)
    c = Canvas(32, 18)
    top = 4
    for x in range(32):
        hang = top + 4 + int(1.5 + 1.5 * math.sin(x * 0.9) + rng.uniform(0, 2.5))
        c.rect(x, top, x, hang, G1)
        c.rect(x, top, x, top, G0)
        if x % 3 == 0:
            c.set(x, top + 1, G0)
        c.set(x, hang, G2)
        c.set(x, hang + 1, G3)
        if rng.random() < 0.45:
            h = rng.randint(1, 3)
            c.rect(x, top - h, x, top - 1, G1 if rng.random() < 0.5 else G0)
            if h == 3 and rng.random() < 0.5:
                c.set(x, top - h, PINK)
    return c


def arch_bark():
    """Грань кристальной арки, 32×32 по кругу: косые грани, светлые рёбра, тёмные трещины."""
    rng = random.Random(153)
    c = Canvas(32, 32)
    for y in range(32):
        for x in range(32):
            band = ((x + y * 2) // 8) % 4
            c.set(x, y, (W1, W2, W1, W0)[band])
    for y in range(32):
        for x in range(32):
            if (x + y * 2) % 8 == 0:
                c.set(x, y, W0 if ((x + y * 2) // 8) % 2 == 0 else FK)
    for _ in range(5):
        x = rng.randint(0, 31)
        y = rng.randint(0, 31)
        for k in range(rng.randint(3, 6)):
            c.set((x + k) % 32, (y + k // 2) % 32, W2)
    for _ in range(4):
        x = rng.randint(0, 31)
        y = rng.randint(0, 31)
        for dx in range(-2, 3):
            for dy in range(-1, 2):
                if rng.random() < 0.7:
                    c.set((x + dx) % 32, (y + dy) % 32, G2 if dy < 1 else G3)
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
    """Высокие усики мха перед героем, 32×24, два кадра качания; у части огонёк на конце."""
    rng = random.Random(161)
    c = Canvas(32, 24)
    for _ in range(16):
        x = rng.uniform(2, 30)
        col = rng.choice((G1, G2, G1, G0))
        tip = PINK if rng.random() < 0.35 else None
        _blade(c, x, rng.uniform(9, 22), rng.uniform(-3, 3) + (1.5 if i else -0.5), col, G3 if col == G2 else G2, tip)
    return c


def dec_tuft(i):
    rng = random.Random(162)
    c = Canvas(32, 14)
    for _ in range(10):
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 11), rng.uniform(-2, 2) + (1 if i else 0), rng.choice((G0, G1, G2)), G3)
    return c


def dec_fern():
    """Друза кристаллов за героем, 48×32: веер шпилей из одной точки."""
    rng = random.Random(163)
    c = Canvas(48, 32)
    for ang, length, w in ((-160, 15, 5), (-128, 21, 6), (-98, 28, 8), (-72, 23, 7), (-44, 18, 6), (-20, 13, 5)):
        a = math.radians(ang + rng.uniform(-4, 4))
        for j in range(int(length)):
            k = j / length
            half = w * 0.5 * (1.0 - k) if k > 0.35 else w * 0.5 * (0.7 + k * 0.85)
            cx = 24 + math.cos(a) * j
            cy = 31 + math.sin(a) * j
            for d in range(int(-half), int(half) + 1):
                u = d / max(half, 0.5)
                c.set(cx - math.sin(a) * d, cy + math.cos(a) * d, W0 if u < -0.2 else (W1 if u < 0.45 else W2))
    c.rect(14, 29, 34, 31, S2)
    c.rect(16, 28, 31, 28, S1)
    c.outline(FK)
    return c


def dec_bush():
    """Семейка грибов за героем, 64×36: пять шляпок разной высоты, пятна, у земли тень."""
    rng = random.Random(164)
    c = Canvas(64, 36)
    for cx, top, r in ((30, 12, 15), (13, 20, 11), (49, 18, 12), (22, 27, 8), (41, 28, 8)):
        c.rect(cx - 2, top, cx + 2, 33, ST0)
        c.rect(cx + 1, top, cx + 2, 33, ST1)
        h = r * 0.62
        for y in range(int(top - h - 1), top + 1):
            k = (top - y) / h
            if k > 1.0:
                continue
            half = r * math.sqrt(max(0.0, 1.0 - k * k))
            for x in range(int(cx - half), int(cx + half) + 1):
                u = (x - cx) / r
                c.set(x, y, W0 if k > 0.6 and u < 0.2 else (W2 if u > 0.55 or k < 0.2 else W1))
        c.rect(int(cx - r * 0.8), top + 1, int(cx + r * 0.8), top + 1, W2)
        for _ in range(int(r * 0.45)):
            sx = cx + rng.uniform(-r * 0.6, r * 0.5)
            sy = top - rng.uniform(0.25, 0.75) * h
            c.set(sx, sy, PINK)
    c.rect(4, 32, 58, 35, G3)
    for x in range(4, 59):
        if rng.random() < 0.5:
            c.set(x, 31, G2)
        if rng.random() < 0.25:
            c.set(x, 32, G1)
    c.outline(FK)
    return c


def dec_rock():
    """Метеорит, 32×20: гранёный камень с кратером, мох у подножия."""
    c = Canvas(32, 20)
    c.poly([(3, 19), (2, 12), (8, 6), (16, 4), (24, 7), (29, 13), (29, 19)], ST1)
    c.poly([(5, 12), (9, 7), (16, 5), (22, 7), (16, 11), (9, 13)], ST0)
    c.ellipse(21, 12, 2.5, 1.5, S2)
    c.set(20, 11, S3)
    c.line(13, 14, 17, 18, FK, 1)
    c.rect(0, 18, 31, 19, None)
    c.poly([(1, 19), (6, 15), (10, 19)], G2)
    c.poly([(22, 19), (27, 14), (31, 19)], G1)
    c.outline(FK)
    return c


def dec_flowers():
    """Светящиеся бутоны на стебельках среди мха, 32×20."""
    rng = random.Random(165)
    c = Canvas(32, 20)
    for _ in range(9):
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 9), rng.uniform(-2, 2), rng.choice((G1, G2)), G3)
    for x, y in ((6, 9), (14, 6), (22, 10), (27, 7)):
        c.line(x, y + 2, x, 19, G2, 1)
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            c.set(x + dx, y + dy, W1)
        c.set(x, y, W0)
        c.set(x, y - 2, PINK)
    return c


def dec_mush():
    """Мелкие кристаллы у ножек, 32×16: три шпиля и осколки."""
    c = Canvas(32, 16)
    for x, h, w in ((8, 9, 5), (17, 13, 6), (25, 7, 4)):
        for j in range(h):
            k = j / h
            half = w * 0.5 * (1.0 - k) if k > 0.4 else w * 0.5
            for d in range(int(-half), int(half) + 1):
                c.set(x + d, 15 - j, W0 if d < 0 else (W1 if d < half * 0.6 else W2))
    c.set(12, 15, W1)
    c.set(21, 15, W1)
    c.set(21, 14, W0)
    c.outline(FK)
    return c


# --- Враги (палитра спрайтов) ------------------------------------------------------------------

def _danger(c):
    """Враг: тень как у всех, но обводка оранжевая, а не чёрная: опасен, убить нельзя."""
    c.shade()
    c.outline(RED)
    return c


def crab(i):
    """Лунный краб-ползун, четыре кадра: ноги по очереди, клешни щёлкают, глаза на стебельках
    светятся. Панцирь фиолетовый с металлическим гребнем, чтобы оранжевая обводка читалась."""
    c = Canvas()
    for k in range(3):
        for sign in (-1, 1):
            lift = 1 if (k + i) % 2 == 0 else 0
            x = 16 + sign * (6 + k * 3)
            c.line(16 + sign * (3 + k * 2), 24, x, 29 - lift, PLUM, 2)
    c.ellipse(16, 23, 10, 5.5, VIOLET)
    c.ellipse(15, 21.5, 6.5, 2.5, GREY)
    for x in (11, 15, 19):
        c.set(x, 21, METAL)
    for sign in (-1, 1):
        open_ = 1 + (i % 2)
        cx = 16 + sign * 10
        c.line(16 + sign * 7, 22, cx, 16, VIOLET, 2)
        c.ellipse(cx, 14, 3, 3, VIOLET)
        c.rect(cx - 1, 10 - open_, cx + 1, 12 - open_, VIOLET)
        c.rect(cx + sign * 2, 10 - open_, cx + sign * 2, 12, VIOLET)
    for sign in (-1, 1):
        c.line(16 + sign * 3, 19, 16 + sign * 3, 15, PLUM, 1)
        c.ellipse(16 + sign * 3, 14, 1.5, 1.5, AQUA)
    _danger(c)
    c.set(13, 14, SKY)
    c.set(19, 14, SKY)
    return c


def drone(i):
    """Дрон-глаз летит вправо: металлический шар, большая бирюзовая линза с зрачком спереди,
    два плавника-крыла машут (вверх, середина, вниз, середина), сзади сопло с выхлопом. Тело по
    центру кадра, чтобы при развороте не прыгало."""
    c = Canvas()
    wing = (-8, -2, 6, -2)[i]
    # Сопло и выхлоп сзади.
    c.rect(6, 15, 9, 19, DARK)
    c.poly([(3, 17), (6, 16 + (i % 2)), (6, 18 - (i % 2))], AQUA)
    # Корпус шаром.
    c.ellipse(16, 17, 7.5, 7.5, METAL)
    c.ellipse(14, 13.5, 4.5, 2.5, GREY)
    c.rect(10, 22, 20, 22, DARK)
    # Линза: большой глаз спереди.
    c.ellipse(20, 17, 5.5, 5.5, DARK)
    c.ellipse(20.5, 17, 4.5, 4.5, AQUA)
    c.ellipse(22, 17, 2.2, 2.2, NAVY)
    # Антенна.
    c.line(14, 9, 12, 5, DARK, 1)
    c.set(12, 4, GOLD)
    # Плавник.
    c.poly([(9, 16), (16, 16), (14, 16 + wing), (8, 16 + wing)], VIOLET)
    c.line(10, 16, 9, 16 + wing * 0.7, PLUM, 2)
    _danger(c)
    c.set(19, 15, SKY)
    c.set(20, 14, SKY)
    c.set(22, 17, RED)
    return c


def sprites():
    """Ленты этой демки в палитре спрайтов (ленты героя в `space16.sprites`)."""
    return {
        "crab_walk": strip([crab(i) for i in range(4)]),
        "parrot_fly": strip([drone(i) for i in range(4)]),
    }


def backdrop():
    """Слои фона и шляпки над кадром в палитре фона `SPACE_BG`."""
    return {"par3_back": par3_back(), "par3_trees": par3_trees(), "par3_bushes": par3_bushes(),
            "canopy_front": canopy_front()}


def foreground():
    """Земля, арка, украшения в палитре переднего плана `SPACE_FG`."""
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


def preview(path):
    items = space16.shaded(sprites())
    for key, canvas in foreground().items():
        items[key] = (canvas, SPACE_FG)
    for key, canvas in backdrop().items():
        items[key] = (canvas, SPACE_BG)
    space16.save_sheet(path, items, scale=2)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
