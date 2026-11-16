#!/usr/bin/env python3
"""Набор «Сладости» для платформера × 16/32-bit «тропа» (#137), зеркало `space_trail16.py` и
`pixel_trail16.py`: те же ключи, размеры холстов, число кадров и точки опоры. Вместо джунглей и
грибов роща сахарной ваты в карамельной стране: фон без неба в три слоя (мятная дымка с облаками
ваты, горами из шариков мороженого под сиропом и дальними леденцами; большие стволы на прежних
местах: карамельная трость, бисквитная палочка в шоколаде, витой зефирный жгут и вафельная
трубочка, каждый в шапке взбитых сливок у земли, наверху сплошной полосой розовая вата, с неё
на нитках свисают конфеты и леденцы; у земли мятные кусты, леденцы на палочках, трости и вата
на рожках над мятным лугом) и тёмная вата с конфетами на нитках над кадром спереди; земля это
срез вафельного торта (вафля, крем, шоколад с орехами) под розовой глазурью с потёками; арка из
витой карамели в малиновую и мятную полоску.

Свойства слотов, на которые рассчитана демка: ленты фона 512 пикселей стыкуются по краям, у
дали и поросли низ сплошной, у больших стволов прозрачно между ними, у ваты спереди прозрачный
низ; грунт 64×64 стыкуется в обе стороны, кромка 32×18 по кругу с поверхностью на строке 4 и
прозрачным низом, грань арки 32×32 по кругу; украшения стоят на нижней строке холста, у травы
и кочки по два кадра качания.

У фона и переднего плана свои палитры по 16 цветов (`SWEETS_BG`, `SWEETS_FG`); драже-жук и
зефир с крылышками в палитре спрайтов `sweets16.PALETTE`, их рисует основа, здесь они получают
красную обводку опасности. Ленты героя рисует `sweets16.py`. Случайность с постоянным зерном:
картинка одна и та же.

    python3 tools/sweets_trail16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweets16  # noqa: E402
from sweets16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, GOLD, BRASS, METAL, DARK, RED,  # noqa: E402,F401
                      VIOLET, PLUM)

TAU = math.pi * 2.0

# Палитра фона: мятная дымка дали, розовая вата, вафля и бисквит стволов, шоколад, карамель.
HZ0, HZ1, HZ2, HZ3, L0, L1, L2, L3, L4, T0, T1, T2, DK, FL1, FL2, MO = range(16)
SWEETS_BG = [
    (0xE6, 0xFB, 0xEC),  # HZ0  облака ваты в дали, блик
    (0xC2, 0xEF, 0xD8),  # HZ1  воздух дали
    (0x9A, 0xDF, 0xC6),  # HZ2  горы мороженого
    (0x72, 0xC6, 0xB2),  # HZ3  сироп на горах, дальние леденцы, свет мяты
    (0xFF, 0xF2, 0xF4),  # L0   блик ваты, сливки, белая карамель
    (0xFF, 0xC2, 0xD8),  # L1   вата, свет
    (0xF6, 0x92, 0xBA),  # L2   вата
    (0xD2, 0x60, 0x9A),  # L3   вата, тень
    (0x98, 0x3E, 0x7A),  # L4   глубокая тень ваты
    (0xFF, 0xEA, 0xB6),  # T0   вафля и бисквит, свет
    (0xEC, 0xBC, 0x74),  # T1   вафля, бисквит
    (0xBC, 0x80, 0x48),  # T2   тень вафли, нитки
    (0x4E, 0x2A, 0x2A),  # DK   тёмный шоколад
    (0xFF, 0xDE, 0x64),  # FL1  лимонная карамель, посыпка
    (0x3A, 0xA6, 0x9A),  # FL2  мята: кусты и луг
    (0xE6, 0x38, 0x4A),  # MO   красная карамель, ягоды
]

# Палитра переднего плана: глазурь, вафля, шоколад, сахар, мята, карамель.
FK, G0, G1, G2, G3, S0, S1, S2, S3, S4, ST0, ST1, W0, W1, W2, PINK = range(16)
SWEETS_FG = [
    (0x2B, 0x16, 0x1E),  # FK   обводка
    (0xFF, 0xE8, 0xF0),  # G0   блик глазури
    (0xFF, 0xA8, 0xC8),  # G1   розовая глазурь
    (0xEE, 0x70, 0xA4),  # G2   глазурь, тень
    (0xB4, 0x38, 0x70),  # G3   малина: глубокая тень, полоски карамели
    (0xFA, 0xDC, 0x92),  # S0   вафля, рёбра
    (0xE4, 0xB0, 0x5E),  # S1   вафля
    (0xBA, 0x7C, 0x3E),  # S2   тень вафли, орехи
    (0x7C, 0x48, 0x38),  # S3   молочный шоколад
    (0x4A, 0x28, 0x26),  # S4   тёмный шоколад
    (0xFF, 0xF7, 0xEC),  # ST0  сахар, крем
    (0xD6, 0xBF, 0xCC),  # ST1  тень сахара
    (0xC8, 0xF6, 0xDE),  # W0   мята, свет
    (0x6A, 0xD0, 0xB0),  # W1   мята
    (0x2C, 0x8C, 0x84),  # W2   тень мяты
    (0xF8, 0xCF, 0x6A),  # PINK карамель, посыпка, серединки цветов
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


def _ball(c, cx, cy, r, cols, y_max=None):
    """Шар со светом сверху слева на ленте по кругу. `cols` от светлого к тёмному: блик, свет,
    тело, тень; на границе тела и тени шахматный переход. `y_max` срезает низ."""
    hi, light, body, shade = cols
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        if y_max is not None and y > y_max:
            break
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy > r * r:
                continue
            t = (-dx * 0.55 - dy * 0.83) / max(r, 0.5)
            if t > 0.74:
                col = hi
            elif t > 0.22:
                col = light
            elif t > -0.38:
                col = body
            elif t > -0.5:
                col = body if (x + y) % 2 == 0 else shade
            else:
                col = shade
            _wset(c, x, y, col)


def _puff(c, rng, cx, cy, r, cols, y_max=None):
    """Ком сахарной ваты: большой шар и бугры по краю, у каждого свой свет; нижние бугры поверх
    верхних. Поверх кома пара светлых волокон дугой."""
    _ball(c, cx, cy, r, cols, y_max)
    lobes = []
    n = max(5, int(r / 3))
    for i in range(n):
        a = TAU * (i + rng.uniform(-0.3, 0.3)) / n
        lobes.append((cy + math.sin(a) * r * 0.72, cx + math.cos(a) * r * 0.72, r * rng.uniform(0.36, 0.5)))
    for ly, lx, lr in sorted(lobes):
        _ball(c, lx, ly, lr, cols, y_max)
    if r >= 12:
        for _ in range(2):
            a0 = rng.uniform(3.4, 4.6)
            rr = r * rng.uniform(0.35, 0.6)
            for k in range(int(rr * 1.2)):
                a = a0 + k / max(rr, 1.0)
                y = cy + math.sin(a) * rr
                if y_max is None or y <= y_max:
                    _wset(c, cx + math.cos(a) * rr, int(y), cols[0])


def _spiral(c, cx, cy, r, a, b, turns=1.6, rim=None, wrap=True):
    """Диск леденца спиралью из двух цветов; `rim` темнит кромку справа снизу."""
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            v = (d / max(r, 0.5) * turns + math.atan2(dy, dx) / TAU) % 1.0
            col = a if v < 0.5 else b
            if rim is not None and d > r - 1.2 and dx + dy > r * 0.5:
                col = rim
            if wrap:
                _wset(c, x, y, col)
            else:
                c.set(x, y, col)


def _wrapped(c, x, y, body, twist):
    """Конфета в фантике на нитке: овал и два хвостика."""
    _wellipse(c, x, y, 4, 2.6, body)
    _wset(c, x - 2, y - 1, L0)
    _wset(c, x - 1, y - 2, L0)
    for sign in (-1, 1):
        _wset(c, x + sign * 5, y, twist)
        for dy in (-1, 0, 1):
            _wset(c, x + sign * 6, y + dy, twist)
        for dy in (-2, -1, 1, 2):
            _wset(c, x + sign * 7, y + dy, twist)


def _lolly(c, x, base, h, r, a, b):
    """Леденец на палочке от земли `base`: палочка в два пикселя, диск спиралью, блик."""
    for y in range(int(base - h), int(base) + 1):
        _wset(c, x, y, T0)
        _wset(c, x + 1, y, T2)
    _spiral(c, x + 0.5, base - h, r, a, b, rim=L4 if b != FL2 else FL2)
    _wset(c, x - r * 0.45, int(base - h - r * 0.5), L0)
    _wset(c, x - r * 0.45 + 1, int(base - h - r * 0.5), L0)


def _cane(c, x, base, h, side, a=L0, b=MO):
    """Карамельная трость от земли: ствол и крюк в сторону `side`, полоски вдоль пути."""
    path = [(x, base - j) for j in range(int(h))]
    rr = 4.0
    for k in range(13):
        ang = math.pi * k / 12.0
        path.append((x + side * (rr - rr * math.cos(ang)), base - h - rr * math.sin(ang)))
    path.append((x + side * rr * 2, base - h + 2))
    s = 0.0
    prev = path[0]
    for p in path:
        s += math.hypot(p[0] - prev[0], p[1] - prev[1])
        prev = p
        col = b if int(s / 3.0) % 2 else a
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if abs(dx) + abs(dy) < 2:
                    shade = dx > 0 or dy > 0
                    _wset(c, p[0] + dx, int(round(p[1] + dy)), (L4 if col == MO else L1) if shade and col == a else col)


def _cotton_stick(c, rng, x, base, h, r):
    """Сахарная вата на бумажном рожке: рожок сужается к земле, сверху розовый ком."""
    for j in range(int(h)):
        half = 0.6 + 2.2 * j / max(h, 1.0)
        for dx in range(int(-half), int(half) + 1):
            _wset(c, x + dx, int(base - j), T0 if dx <= 0 else T1)
        if j % 4 == 0:
            _wset(c, x + int(half), int(base - j), T2)
    _puff(c, rng, x, base - h - r * 0.6, r, (L0, L1, L2, L3))


def _mint_bush(c, rng, x, base, r):
    """Мятный куст: бугристый шар в три тона, листики галочкой, красные ягоды-драже."""
    _puff(c, rng, x, base - r * 0.7, r, (HZ0, HZ3, FL2, FL2), y_max=base)
    for _ in range(int(r * 0.7)):
        lx = x + rng.uniform(-r * 0.7, r * 0.7)
        ly = base - rng.uniform(1, r * 1.3)
        if c.get(int(lx) % c.w, int(ly)) == FL2:
            _wset(c, lx, int(ly), HZ3)
            _wset(c, lx + 1, int(ly) - 1, HZ3)
    for _ in range(max(2, int(r / 4))):
        bx = x + rng.uniform(-r * 0.7, r * 0.7)
        by = base - rng.uniform(2, r * 1.2)
        if c.get(int(bx) % c.w, int(by)) is not None:
            _wellipse(c, bx, by, 1.5, 1.5, MO)
            _wset(c, bx - 1, int(by) - 1, L1)


# --- Фон ---------------------------------------------------------------------------------------

def _sundae(c, rng, x, base, r):
    """Гора из шариков мороженого пирамидой: три внизу, два над ними, один на вершине, на нём
    шапка сиропа с потёками и вафля торчком."""
    rows = ((0, (-1.55, 0.0, 1.55)), (1, (-0.8, 0.8)), (2, (0.0,)))
    top = None
    for level, offs in rows:
        cy = base - r * (0.8 + level * 1.25)
        for o in offs:
            cx = x + o * r
            _wellipse(c, cx, cy, r, r, HZ2)
            # Тень серпом справа снизу, блик штрихом слева сверху.
            for yy in range(int(cy - r), int(cy + r) + 1):
                for xx in range(int(cx - r), int(cx + r) + 1):
                    dx, dy = xx - cx, yy - cy
                    if dx * dx + dy * dy <= r * r and (dx + r * 0.3) ** 2 + (dy + r * 0.3) ** 2 > (r * 1.05) ** 2:
                        _wset(c, xx, yy, HZ3)
            for k in range(int(r * 0.5)):
                a = 3.6 + k / max(r * 0.7, 1.0)
                _wset(c, cx + math.cos(a) * r * 0.7, int(cy + math.sin(a) * r * 0.7), HZ0)
            top = (cx, cy)
    cx, cy = top
    # Вафля торчком и шапка сиропа.
    for j in range(int(r * 1.3)):
        for dx in range(3):
            _wset(c, cx + r * 0.35 + j * 0.4 + dx, int(cy - r * 0.6 - j), HZ3 if dx else HZ2)
    for xx in range(int(cx - r), int(cx + r) + 1):
        dx = xx - cx
        edge = cy - math.sqrt(max(0.0, r * r - dx * dx))
        drop = cy - r * 0.42 + math.sin(dx * 0.5) * r * 0.08
        # Три потёка разной длины с круглыми концами.
        for off, length in ((-0.55, 0.45), (-0.05, 0.75), (0.5, 0.35)):
            d = abs(dx - off * r)
            if d <= 2.0:
                drop = max(drop, cy - r * 0.42 + r * length - (1.5 if d > 1.0 else 0.0))
        for yy in range(int(edge), int(drop) + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                _wset(c, xx, yy, HZ3)
    _wellipse(c, cx - r * 0.3, cy - r * 0.72, r * 0.3, 1.2, HZ2)


def par3_back():
    """Даль на весь экран, 512×277: мятная дымка, облака ваты, горы из шариков мороженого под
    сиропом, у земли дальние леденцы и рожки; низ сплошной."""
    rng = random.Random(341)
    c = Canvas(512, 277)
    c.rect(0, 0, 511, 276, HZ1)
    # Облака ваты: гроздья светлых кругов с плоским низом.
    for x in range(0, 512, 64):
        cx = x + rng.uniform(-14, 14)
        cy = rng.uniform(26, 120)
        s = rng.uniform(10, 17)
        for ox, oy, k in ((-1.5, 0.2, 0.75), (-0.6, -0.45, 1.0), (0.5, -0.25, 0.9), (1.4, 0.2, 0.7), (0.0, 0.3, 0.9)):
            _wellipse(c, cx + ox * s, cy + oy * s, s * k, s * k * 0.8, HZ0)
        for xx in range(int(cx - s * 2.3), int(cx + s * 2.2)):
            for yy in range(int(cy + s * 0.55), int(cy + s * 1.2)):
                if c.get(xx % 512, yy) == HZ0:
                    _wset(c, xx, yy, HZ1)
    # Горы мороженого.
    for x, r in ((34, 26), (150, 19), (238, 30), (352, 22), (446, 27)):
        _sundae(c, rng, x + rng.uniform(-6, 6), 236, r)
    # Дальние леденцы на палочках и рожки с шариком.
    for i in range(26):
        x = i * 512 / 26.0 + rng.uniform(-6, 6)
        if i % 3 == 2:
            top = rng.uniform(196, 214)
            for j in range(int(238 - top)):
                half = 5.0 * (1.0 - j / (238 - top))
                for dx in range(int(-half), int(half) + 1):
                    _wset(c, x + dx, int(top + j), HZ3 if (dx + j) % 3 else HZ2)
            _wellipse(c, x, top - 3, 6, 6, HZ2)
            _wellipse(c, x - 2, top - 5, 2, 1.5, HZ0)
        else:
            top = rng.uniform(170, 212)
            r = rng.uniform(6, 10)
            for y in range(int(top), 240):
                _wset(c, x, y, HZ3)
            _spiral(c, x, top, r, HZ3, HZ0 if i % 2 else HZ2, 1.4)
    # Холмы и сплошной низ.
    for x in range(512):
        h = 233 + 4.0 * math.sin(x * TAU / 128.0) + 2.0 * math.sin(x * TAU / 64.0 + 1.0)
        for y in range(int(h), 277):
            _wset(c, x, y, HZ3)
        if x % 9 == 0:
            _wellipse(c, x, h, 4, 3, HZ3)
    c.rect(0, 242, 511, 276, HZ3)
    return c


def _dollop(c, cx, w):
    """Шапка взбитых сливок у подножия ствола: полукруг с витыми бороздами, свет слева."""
    rx = w / 2.0 + 13
    # Два яруса: широкая розетка у земли и завиток поменьше над ней.
    for tier_rx, y_top, y_bot in ((rx, 253, 262), (rx * 0.66, 246, 255)):
        for y in range(y_top, y_bot + 1):
            k = (y_bot - y) / float(y_bot - y_top + 1)
            half = tier_rx * math.sqrt(max(0.0, 1.0 - k * k))
            for x in range(int(cx - half), int(cx + half) + 1):
                u = (x - cx) / tier_rx
                groove = (x - int(cx) + (y_bot - y) * 2) % 7 == 0
                if u > 0.45:
                    col = L2 if groove else L1
                else:
                    col = L1 if groove else L0
                if y == y_bot and tier_rx < rx:
                    col = L2 if u > 0.0 else L1
                if 0 <= x < c.w:
                    c.set(x, y, col)
    for x in range(int(cx - rx) + 2, int(cx + rx) - 1):
        if 0 <= x < c.w:
            c.set(x, 262, L2)


def _trunk_cane(c, x0, x1, y0, y1):
    """Карамельная трость: косые красные и белые полосы, блик столбцом, тень справа."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = (x - x0) / float(x1 - x0)
            red = (y - (x - x0) * 0.8) % 26 < 11
            thin = 15 <= (y - (x - x0) * 0.8) % 26 < 18
            if red or thin:
                col = L4 if k > 0.72 else (L2 if 0.16 < k < 0.26 else MO)
            else:
                col = L1 if k > 0.72 else (L0 if k > 0.08 else T0)
            c.set(x, y, col)


def _trunk_pocky(c, x0, x1, y0, y1, rng):
    """Бисквитная палочка: верх в шоколаде с потёками и посыпкой, низ пористый бисквит."""
    w = x1 - x0
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = (x - x0) / float(w)
            c.set(x, y, T0 if k < 0.22 else (T1 if k < 0.72 else T2))
    for _ in range(70):
        x = rng.randint(x0 + 1, x1 - 2)
        y = rng.randint(y0, y1 - 1)
        c.set(x, y, T2 if x < x0 + w * 0.7 else T1)
    for x in range(x0 - 1, x1 + 1):
        drip = 150 + int(10 * math.sin((x - x0) * 0.9) + (14 if (x - x0) % 8 in (2, 3) else 0))
        for y in range(y0, drip):
            k = (x - x0) / float(w)
            c.set(x, y, T2 if 0.18 < k < 0.27 and y % 23 < 17 else DK)
        c.set(x, drip, DK if (x - x0) % 8 in (2, 3) else T2)
    for _ in range(26):
        x = rng.randint(x0 + 1, x1 - 3)
        y = rng.randint(y0 + 30, 146)
        col = rng.choice((FL1, L1, HZ0, MO))
        if rng.random() < 0.5:
            c.rect(x, y, x + 1, y, col)
        else:
            c.rect(x, y, x, y + 1, col)


def _trunk_marsh(c, x0, x1, y0, y1):
    """Витой зефирный жгут: белые и розовые пряди выгнуты дугой, между витками бороздка."""
    w = x1 - x0
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = (x - x0) / float(w)
            v = (y + 13.0 * math.sin(k * math.pi)) % 24
            pink = v >= 12
            seam = v < 1 or 12 <= v < 13
            if seam:
                col = L3 if k > 0.5 else L2
            elif pink:
                col = L3 if k > 0.84 else (L2 if k > 0.55 else L1)
            else:
                col = L2 if k > 0.84 else (L1 if k > 0.62 else L0)
            c.set(x, y, col)
    # Витки выпирают за край: по бугорку на каждый.
    for y in range(y0, y1):
        if y % 24 in (5, 6, 7, 17, 18, 19):
            c.set(x0 - 1, y, L0 if y % 24 < 12 else L1)
            c.set(x1, y, L2 if y % 24 < 12 else L3)


def _trunk_wafer(c, x0, x1, y0, y1):
    """Вафельная трубочка: клетка рёбер, свет слева, тень справа, шов спиралью."""
    w = x1 - x0
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = (x - x0) / float(w)
            rib = (x - x0) % 6 == 2 or y % 6 == 0
            if k > 0.76:
                col = T2
            elif rib:
                col = T2 if k > 0.3 else T1
            else:
                col = T0 if k < 0.3 else T1
            if (y + (x - x0) * 2) % 58 < 2:
                col = DK if k > 0.76 else T2
            c.set(x, y, col)
        if y % 6 == 3:
            c.set(x1 - 2, y, T1)


def par3_trees():
    """Большие стволы, 512×277, прозрачно между ними: трость, палочка в шоколаде, зефирный жгут и
    вафельная трубочка стоят в шапках сливок, наверху сплошной полосой розовая вата, с неё на
    нитках свисают конфеты в фантиках и леденцы."""
    rng = random.Random(342)
    c = Canvas(512, 277)
    _trunk_cane(c, 40, 70, 40, 262)
    _trunk_pocky(c, 196, 218, 40, 262, rng)
    _trunk_marsh(c, 300, 338, 40, 262)
    _trunk_wafer(c, 452, 478, 40, 262)
    for x, w in ((40, 30), (196, 22), (300, 38), (452, 26)):
        _dollop(c, x + w / 2.0, w)
    # Нитки с конфетами и леденцами в просветах между стволами.
    for i, x in enumerate((14, 96, 122, 150, 176, 240, 268, 286, 362, 390, 418, 436, 496)):
        length = rng.uniform(34, 100)
        end = int(44 + length)
        for y in range(40, end):
            _wset(c, x + math.sin(y * 0.07 + i) * 1.5, y, T2)
        ex = x + math.sin(end * 0.07 + i) * 1.5
        if i % 3 == 0:
            _spiral(c, ex, end + 4, 5, L0, MO, 1.3, rim=L4)
            _wset(c, ex - 2, end + 2, L0)
        elif i % 3 == 1:
            _wrapped(c, ex, end + 2, FL1, T0)
        else:
            _wrapped(c, ex, end + 2, FL2, HZ0)
    # Вата: сплошной верх, три ряда комьев, нижний светлее.
    c.rect(0, 0, 511, 26, L4)
    for x in range(0, 512, 30):
        _puff(c, rng, x + rng.uniform(-5, 5), rng.uniform(2, 9), rng.uniform(19, 24), (L2, L3, L4, L4))
    for x in range(0, 512, 26):
        _puff(c, rng, x + rng.uniform(-5, 5), rng.uniform(17, 27), rng.uniform(20, 25), (L1, L2, L3, L4))
    for x in range(0, 512, 34):
        _puff(c, rng, x + rng.uniform(-6, 6), rng.uniform(36, 48), rng.uniform(21, 27), (L0, L1, L2, L3))
    return c


def par3_bushes():
    """Яркая поросль у земли, 512×120, прозрачный верх: мятные кусты, леденцы на палочках,
    карамельные трости и вата на рожках над мятным лугом с мармеладками; низ сплошной."""
    rng = random.Random(343)
    c = Canvas(512, 120)
    kinds = "lmcwmlwmclmwlmcmwlmlcmwmlwcmlmwlmcwmlmw"
    for i, x in enumerate(range(0, 512, 13)):
        cx = x + rng.uniform(-3, 3)
        kind = kinds[i % len(kinds)]
        if kind == "l":
            a, b = rng.choice(((L0, MO), (FL1, L2), (L0, FL2), (L1, L4)))
            _lolly(c, cx, 97, rng.uniform(26, 56), rng.uniform(6, 9), a, b)
        elif kind == "c":
            _cane(c, cx, 97, rng.uniform(22, 40), rng.choice((-1, 1)), L0, rng.choice((MO, FL2)))
        elif kind == "w":
            _cotton_stick(c, rng, cx, 97, rng.uniform(16, 28), rng.uniform(9, 13))
        else:
            _mint_bush(c, rng, cx, 97, rng.uniform(10, 16))
    # Луг: сплошная полоса, по кромке мятные бугорки и мармеладки.
    c.rect(0, 92, 511, 119, FL2)
    for x in range(0, 512, 7):
        _ball(c, x + rng.uniform(-2, 2), rng.uniform(93, 97), rng.uniform(4, 7), (HZ0, HZ3, FL2, FL2))
    for x in range(10, 512, 41):
        gx = x + rng.uniform(-8, 8)
        body, dark = rng.choice(((MO, L4), (FL1, T2), (L2, L3)))
        for j in range(7):
            half = 4.5 * (1.0 - (j / 7.0) ** 2.4) ** 0.6
            for dx in range(int(-half), int(half) + 1):
                _wset(c, gx + dx, 100 - j, dark if dx > half * 0.45 else body)
        _wset(c, gx - 2, 96, L0)
        _wset(c, gx - 1, 95, L0)
    for _ in range(240):
        x = rng.uniform(0, 512)
        y = int(rng.uniform(101, 119))
        if c.get(int(x) % 512, y) == FL2:
            _wset(c, x, y, HZ3 if rng.random() < 0.75 else rng.choice((L1, FL1, L0)))
    return c


def canopy_front():
    """Вата над кадром спереди, 256×56, прозрачный низ: тёмные комья и конфеты на нитках."""
    rng = random.Random(344)
    c = Canvas(256, 56)
    for i in range(12):
        x = i * 256 / 12.0 + rng.uniform(-5, 5)
        n = rng.randint(24, 47)
        for y in range(10, n):
            _wset(c, x + math.sin(y * 0.2 + i) * 1.3, y, L4 if y % 5 else L3)
        ex = x + math.sin(n * 0.2 + i) * 1.3
        _wellipse(c, ex, n + 2, 2.2, 2.2, (MO, FL1, FL2)[i % 3])
        _wset(c, ex - 1, n + 1, L0)
    c.rect(0, 0, 255, 8, L4)
    for x in range(0, 256, 30):
        _puff(c, rng, x + rng.uniform(-4, 4), rng.uniform(-6, 0), rng.uniform(15, 19), (L3, L4, L4, L4))
    for x in range(0, 256, 22):
        _puff(c, rng, x + rng.uniform(-4, 4), rng.uniform(5, 13), rng.uniform(14, 19), (L2, L3, L4, L4))
    return c


# --- Передний план -----------------------------------------------------------------------------

def trail_soil():
    """Срез вафельного торта, 64×64 по кругу в обе стороны: два вафельных листа в клетку с
    рёбрами и тенью в ячейках, между ними полоски крема и слои шоколада с орехами и крошкой."""
    rng = random.Random(351)
    n = 64
    c = Canvas(n, n)

    def wafer(y0, shift):
        for y in range(y0, y0 + 20):
            j = y - y0
            for x in range(n):
                u = (x + shift) % 8
                v = (j + 2) % 8
                if j == 0 or j == 19:
                    col = S2
                elif u == 0 or v == 0:
                    col = S0
                elif u == 1 or v == 1:
                    col = S2
                elif u == 7 or v == 7:
                    col = S0 if (u + v) % 2 else S1
                else:
                    col = S1
                c.set(x, y % n, col)
        for _ in range(9):
            x, y = rng.randrange(n), y0 + rng.randrange(2, 18)
            c.set(x, y % n, S2)
            c.set((x + 1) % n, y % n, S2)

    def cream(y0):
        for x in range(n):
            c.set(x, y0 % n, ST0)
            c.set(x, (y0 + 1) % n, ST1 if (x // 3) % 4 else ST0)

    def choco(y0, nuts):
        for y in range(y0, y0 + 8):
            for x in range(n):
                wave = math.sin(x * TAU / 32.0 + y0) * 1.2
                c.set(x, y % n, S3 if (y - y0) < 3.2 + wave else S4)
        for _ in range(nuts):
            x, y = rng.randrange(n), y0 + rng.randrange(1, 6)
            for dx in range(3):
                c.set((x + dx) % n, y % n, S1 if dx < 2 else S2)
                c.set((x + dx) % n, (y + 1) % n, S2)
            c.set(x, y % n, S0)
        for _ in range(14):
            c.set(rng.randrange(n), (y0 + rng.randrange(0, 8)) % n, S3 if rng.random() < 0.5 else S2)

    wafer(0, 0)
    cream(20)
    choco(22, 5)
    cream(30)
    wafer(32, 4)
    cream(52)
    choco(54, 3)
    cream(62)
    return c


def trail_edge():
    """Кромка глазури, 32×18 по кругу: поверхность на строке 4, над ней завитки крема с ягодой и
    бусины посыпки, вниз глазурь стекает потёками разной длины; ниже прозрачно, там грунт."""
    c = Canvas(32, 18)
    top = 4
    drips = ((2, 1, 3), (8, 2, 7), (14, 1, 2), (19, 1, 5), (25, 2, 8), (30, 1, 3))
    hang = []
    for x in range(32):
        h = top + 3
        for cx, half, extra in drips:
            d = min((x - cx) % 32, (cx - x) % 32)
            if d <= half:
                h = max(h, top + 3 + extra - (1 if d == half and half > 1 else 0))
            elif d == half + 1:
                h = max(h, top + 4)
        hang.append(h)
    for x in range(32):
        h = hang[x]
        c.rect(x, top, x, h, G1)
        c.set(x, top, G0)
        if x % 5 in (1, 2):
            c.set(x, top + 1, G0)
        c.set(x, h, G2)
        c.set(x, h + 1, G3)
        # Правый бок потёка в тени, левый с бликом.
        if hang[(x + 1) % 32] < h - 1:
            c.rect(x, hang[(x + 1) % 32] + 1, x, h, G2)
        if hang[(x - 1) % 32] < h - 1 and h > top + 5:
            c.rect(x, hang[(x - 1) % 32] + 2, x, h - 2, G0)
    for x, col in ((4, PINK), (11, W1), (16, ST0), (22, PINK), (27, W1), (0, ST0)):
        c.set(x, top + 2, col)
        c.set(x + 1, top + 2 if col == ST0 else top + 3, col)
    # Над поверхностью: два завитка крема с ягодой и бусины.
    for x in (5, 21):
        c.rect(x - 2, top - 1, x + 2, top - 1, ST0)
        c.set(x + 2, top - 1, ST1)
        c.rect(x - 1, top - 2, x + 1, top - 2, ST0)
        c.set(x + 1, top - 2, ST1)
        c.set(x, top - 3, G3)
    for x, col in ((12, W1), (15, PINK), (28, G0), (31, W1)):
        c.set(x, top - 1, col)
    return c


def arch_bark():
    """Грань арки из витой карамели, 32×32 по кругу: косые полосы белая, малиновая, белая,
    мятная; у каждой блик вдоль и тень по краю, россыпь сахара."""
    rng = random.Random(353)
    c = Canvas(32, 32)
    for y in range(32):
        for x in range(32):
            v = (x + y) % 32
            if v < 9:
                col = ST0 if v < 7 else ST1
            elif v < 19:
                col = G1 if v in (11, 12) else (G2 if v in (9, 17, 18) else G3)
                if v == 10:
                    col = G2
            elif v < 26:
                col = ST0 if v < 24 else ST1
            else:
                col = W0 if v == 27 else (W2 if v >= 30 else W1)
            c.set(x, y, col)
    for _ in range(10):
        x, y = rng.randrange(32), rng.randrange(32)
        if c.get(x, y) in (G3, W1):
            c.set(x, y, G0 if c.get(x, y) == G3 else W0)
    for _ in range(5):
        x, y = rng.randrange(32), rng.randrange(32)
        if c.get(x, y) == ST0:
            c.set(x, y, ST1)
            c.set((x + 1) % 32, (y - 1) % 32, ST1)
    return c


def _blade(c, x, h, bend, col, side):
    """Мятный лист-травинка от нижней строки: внизу в два пикселя, кончик загнут."""
    for j in range(int(h)):
        k = j / h
        c.set(x + bend * k * k, c.h - 1 - j, col)
        if k < 0.6:
            c.set(x + bend * k * k + 1, c.h - 1 - j, side)


def _bead(c, x, y, body, dark):
    """Бусина-драже три на три с бликом и обводкой."""
    for dx, dy in ((0, -2), (-1, -2), (1, -2), (0, 2), (-1, 2), (1, 2), (-2, 0), (-2, -1), (-2, 1), (2, 0), (2, -1),
                   (2, 1)):
        c.set(x + dx, y + dy, FK)
    c.rect(x - 1, y - 1, x + 1, y + 1, body)
    c.set(x + 1, y + 1, dark)
    c.set(x + 1, y, dark)
    c.set(x - 1, y - 1, G0)


def dec_grass(i):
    """Высокая мятная трава перед героем, 32×24, два кадра качания: листья и три стебля с
    бусинами драже на концах."""
    rng = random.Random(361)
    c = Canvas(32, 24)
    sway = 1.5 if i else -0.5
    for _ in range(13):
        x = rng.uniform(2, 30)
        col = rng.choice((W1, W2, W1, W0))
        _blade(c, x, rng.uniform(8, 17), rng.uniform(-3, 3) + sway, col, W2)
    for x, h, body, dark in ((7, 19, G1, G2), (17, 21, PINK, S2), (25, 16, ST0, ST1)):
        tx = x + (1 if i else 0)
        for j in range(h):
            c.set(x + (j / float(h)) ** 2 * (1 if i else 0), 23 - j, W2)
        _bead(c, tx, 23 - h, body, dark)
    return c


def dec_tuft(i):
    """Кочка мятных листьев, 32×14, два кадра: короткие широкие листья, крупинки посыпки."""
    rng = random.Random(362)
    c = Canvas(32, 14)
    for _ in range(15):
        x = rng.uniform(2, 28)
        h = rng.uniform(5, 12)
        bend = rng.uniform(-2, 2) + (1 if i else 0)
        col = rng.choice((W0, W1, W1))
        # Лист в три пикселя у земли: тёмный край, тело, сужение к кончику.
        for j in range(int(h)):
            k = j / h
            bx = x + bend * k * k
            c.set(bx, 13 - j, col)
            if k < 0.7:
                c.set(bx + 1, 13 - j, W1 if col == W0 else W2)
            if k < 0.4:
                c.set(bx + 2, 13 - j, W2)
    for x, col in ((5, PINK), (14, G1), (23, ST0), (28, PINK)):
        c.set(x, 12, col)
        c.set(x + 1, 13, col)
    return c


def _lolly_fg(x, y, r, a, b, rim, ang, length):
    """Леденец на своём холсте 48×32: палочка от (24, 31) под углом, диск спиралью, обводка."""
    c = Canvas(48, 32)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for j in range(int(length)):
        c.set(24 + ca * j, 31 + sa * j, ST0)
        c.set(24 + ca * j + 1, 31 + sa * j, ST1)
    _spiral(c, x, y, r, a, b, 1.7, rim=rim, wrap=False)
    c.set(x - r * 0.45, y - r * 0.5, ST0)
    c.set(x - r * 0.45 + 1, y - r * 0.5 - 1, ST0)
    c.outline(FK)
    return c


def dec_fern():
    """Три леденца на палочках веером за героем, 48×32: мятный, малиновый и карамельный диски
    спиралью, палочки сходятся в горке глазури."""
    c = Canvas(48, 32)
    c.paste(_lolly_fg(12.5, 18.5, 6, ST0, W1, W2, -124, 17), 0, 0)
    c.paste(_lolly_fg(36.5, 17.5, 6.5, PINK, G2, S2, -50, 18), 0, 0)
    c.paste(_lolly_fg(24.5, 9.5, 8, ST0, G3, G2, -90, 20), 0, 0)
    mound = Canvas(48, 32)
    mound.ellipse(24.5, 31, 7, 3, G1)
    mound.rect(20, 28, 25, 28, G0)
    mound.rect(27, 30, 30, 31, G2)
    mound.set(22, 30, PINK)
    mound.set(26, 29, W1)
    mound.outline(FK)
    c.paste(mound, 0, 0)
    return c


def dec_bush():
    """Мятный куст за героем, 64×36: пять бугров в три тона, листики галочкой, малиновые
    ягоды-драже, у земли тень."""
    rng = random.Random(364)
    c = Canvas(64, 36)
    for cx, cy, r in ((23, 15, 9), (42, 14, 9), (32, 18, 14), (15, 25, 10), (49, 24, 11), (32, 28, 9)):
        for y in range(int(cy - r - 1), 36):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                dx, dy = x - cx, y - cy
                if dx * dx + dy * dy > r * r:
                    continue
                t = (-dx * 0.55 - dy * 0.83) / r
                if t > 0.5:
                    col = W0
                elif t > -0.3:
                    col = W1
                elif t > -0.42:
                    col = W1 if (x + y) % 2 else W2
                else:
                    col = W2
                c.set(x, y, col)
    for _ in range(26):
        x = rng.randint(8, 56)
        y = rng.randint(8, 32)
        col = c.get(x, y)
        if col == W1:
            c.set(x, y, W2)
            c.set(x + 1, y - 1, W2)
            c.set(x - 1, y - 1, W2)
        elif col == W2:
            c.set(x, y, W1)
            c.set(x + 1, y - 1, W1)
    for x, y in ((20, 13), (37, 9), (46, 21), (28, 24), (12, 26), (54, 29), (36, 30)):
        c.ellipse(x, y, 2, 2, G3)
        c.rect(x - 1, y - 1, x, y, G2)
        c.set(x - 1, y - 1, G0)
    c.rect(6, 35, 58, 35, W2)
    c.outline(FK)
    return c


def _cube(pts_top, pts_left, pts_right, rng):
    """Кусок сахара на своём холсте 32×20: верх белый, левая грань мятная, правая в тени."""
    c = Canvas(32, 20)
    c.poly(pts_left, W0)
    c.poly(pts_right, ST1)
    c.poly(pts_top, ST0)
    for _ in range(8):
        x, y = rng.randrange(32), rng.randrange(20)
        col = c.get(x, y)
        if col == W0:
            c.set(x, y, ST0)
        elif col == ST1:
            c.set(x, y, ST0 if rng.random() < 0.5 else W0)
        elif col == ST0:
            c.set(x, y, ST1)
    c.outline(FK)
    return c


def dec_rock():
    """Два куска сахара, 32×20: большой куб углом к зрителю и малый перед ним, крупинки у
    подножия."""
    rng = random.Random(365)
    c = Canvas(32, 20)
    c.paste(_cube([(3, 7), (12, 2), (23, 5), (14, 10)], [(3, 7), (14, 10), (14, 19), (3, 16)],
                  [(14, 10), (23, 5), (23, 14), (14, 19)], rng), 0, 0)
    c.paste(_cube([(19, 13), (24, 11), (30, 13), (25, 15)], [(19, 13), (25, 15), (25, 19), (19, 18)],
                  [(25, 15), (30, 13), (30, 18), (25, 19)], rng), 0, 0)
    for x in (1, 16, 17):
        c.set(x, 19, ST0)
    return c


def dec_flowers():
    """Мармеладные цветы среди мятных листьев, 32×20: четыре цветка в пять лепестков с
    карамельной серединкой на стебельках."""
    rng = random.Random(366)
    c = Canvas(32, 20)
    for _ in range(9):
        _blade(c, rng.uniform(2, 29), rng.uniform(4, 8), rng.uniform(-2, 2), rng.choice((W1, W2)), W2)
    for x, y, petal, dark in ((5, 8, G1, G2), (13, 4, ST0, ST1), (21, 9, G2, G3), (27, 5, G1, G2)):
        c.line(x, y + 3, x, 19, W2, 1)
        c.set(x + 1, y + 6, W1)
        c.set(x + 2, y + 5, W1)
        for dx, dy in ((0, -2), (-2, 0), (2, 0), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1), (-2, -1), (2, -1), (-1, -2),
                       (1, -2)):
            c.set(x + dx, y + dy, dark if dy > 0 or (dx > 1 and dy == 0) else petal)
        c.set(x, y - 1, petal)
        c.set(x - 1, y, petal)
        c.set(x + 1, y, petal)
        c.set(x, y + 1, dark)
        c.set(x, y, PINK)
    return c


def _gumdrop(cx, r, h, body, dark, light):
    """Мармеладка на своём холсте 32×16: купол с плоским низом, блик, крупинки сахара."""
    c = Canvas(32, 16)
    for j in range(h):
        half = r * (1.0 - (j / float(h)) ** 2.4) ** 0.6
        for dx in range(int(round(-half)), int(round(half)) + 1):
            u = dx / max(half, 0.5)
            c.set(cx + dx, 15 - j, dark if u > 0.45 or j == 0 else body)
    c.rect(cx - r * 0.5, 15 - h + 2, cx - r * 0.5, 15 - h + 4, light)
    c.set(cx - r * 0.5 + 1, 15 - h + 2, light)
    for k in range(h // 2):
        c.set(cx - r + 2 + (k * 5) % (2 * r - 3), 14 - (k * 3) % (h - 2), ST0)
    c.outline(FK)
    return c


def dec_mush():
    """Три мармеладки в сахаре, 32×16: розовая, высокая мятная и малая карамельная."""
    c = Canvas(32, 16)
    c.paste(_gumdrop(8, 5, 9, G1, G2, G0), 0, 0)
    c.paste(_gumdrop(26, 4, 7, PINK, S2, ST0), 0, 0)
    c.paste(_gumdrop(18, 6, 12, W1, W2, W0), 0, 0)
    return c


# --- Враги (палитра спрайтов) ------------------------------------------------------------------

def _danger(c):
    """Враг тропы: внешняя шоколадная обводка основы становится красной: опасен, убить нельзя."""
    src = [row[:] for row in c.px]
    for y in range(c.h):
        for x in range(c.w):
            if src[y][x] != K:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < c.w and 0 <= ny < c.h) or src[ny][nx] is None:
                    c.px[y][x] = RED
                    break
    return c


def crab(i):
    """Ползун тропы: драже-жук из основы, четыре кадра, ножки переступают по очереди."""
    return _danger(sweets16.bug(i))


def drone(i):
    """Летун тропы: зефир с крылышками из основы, четыре кадра взмаха, тело по центру кадра."""
    return _danger(sweets16.zefir(i))


def sprites():
    """Ленты этой демки в палитре спрайтов (ленты героя в `sweets16.sprites`)."""
    return {
        "crab_walk": strip([crab(i) for i in range(4)]),
        "parrot_fly": strip([drone(i) for i in range(4)]),
    }


def backdrop():
    """Слои фона и вата над кадром в палитре фона `SWEETS_BG`."""
    return {"par3_back": par3_back(), "par3_trees": par3_trees(), "par3_bushes": par3_bushes(),
            "canopy_front": canopy_front()}


def foreground():
    """Земля, арка, украшения в палитре переднего плана `SWEETS_FG`."""
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
    items = sweets16.shaded(sprites())
    for key, canvas in foreground().items():
        items[key] = (canvas, SWEETS_FG)
    for key, canvas in backdrop().items():
        items[key] = (canvas, SWEETS_BG)
    sweets16.save_sheet(path, items, scale=2)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
