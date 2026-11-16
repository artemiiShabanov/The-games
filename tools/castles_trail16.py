#!/usr/bin/env python3
"""Набор «Замки» для платформера × 16/32-bit «тропа» (#137), зеркало `space_trail16.py` и
`pixel_trail16.py`: те же ключи, размеры холстов, число кадров и точки опоры. Вместо джунглей и
грибов королевская дубрава под стенами замка: фон без неба в три слоя (голубая дымка с башнями
и зубцами замка и силуэтами елей, большие дубы с бороздчатой корой и кроной сплошной полосой
наверху, с кроны свисают турнирные стяги, у земли живая изгородь из роз и ёлочки) и дубовая
листва с гирляндой флажков над кадром спереди; земля из тёсаной кладки с травяной кромкой; арка
из светлого известняка с плющом.

Свойства слотов, на которые рассчитана демка: ленты фона 512 пикселей стыкуются по краям, у
дали и кустов низ сплошной, у больших деревьев стволы на тех же местах и прозрачно между ними,
у листвы спереди прозрачный низ; грунт 64×64 стыкуется в обе стороны, кромка 32×18 с
поверхностью на строке 4, грань арки 32×32 по кругу; украшения стоят на нижней строке холста.

У фона и переднего плана свои палитры по 16 цветов (`CASTLES_BG`, `CASTLES_FG`); кабан и
летучая мышь в палитре спрайтов `castles16.PALETTE`, их рисует основа. Ленты героя рисует
`castles16.py`. Случайность с постоянным зерном: картинка одна и та же.

    python3 tools/castles_trail16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import castles16  # noqa: E402
from castles16 import Canvas, strip  # noqa: E402

# Палитра фона: голубая дымка дали, дубовая листва, кора, тени, золото и красное стягов, ели.
HZ0, HZ1, HZ2, HZ3, L0, L1, L2, L3, L4, T0, T1, T2, DK, FL1, FL2, MO = range(16)
CASTLES_BG = [
    (0xD8, 0xE8, 0xEE),  # HZ0  дымка, просвет в дали
    (0xB2, 0xCA, 0xDA),  # HZ1  стены и башни замка
    (0x86, 0xA8, 0xBE),  # HZ2  дальние ели, крыши башен
    (0x5E, 0x86, 0x9A),  # HZ3  ближняя кромка дали
    (0xE2, 0xEE, 0x7E),  # L0   блик листа
    (0xAA, 0xD0, 0x50),  # L1   лист, свет
    (0x6C, 0xA8, 0x3E),  # L2   лист
    (0x3E, 0x7C, 0x38),  # L3   лист, тень
    (0x22, 0x52, 0x34),  # L4   глубокая тень листвы
    (0xB4, 0x98, 0x7C),  # T0   кора дуба, свет
    (0x80, 0x64, 0x52),  # T1   кора
    (0x52, 0x3E, 0x3A),  # T2   кора, тень
    (0x18, 0x22, 0x26),  # DK   самая тёмная тень
    (0xF4, 0xC8, 0x4A),  # FL1  золото: кайма стягов, жёлуди
    (0xD2, 0x30, 0x2C),  # FL2  красное: стяги, розы
    (0x2C, 0x72, 0x62),  # MO   хвоя, плющ, мох
]

# Палитра переднего плана: трава, серая кладка, известняк, дерево, красное роз и оперения.
FK, G0, G1, G2, G3, S0, S1, S2, S3, S4, ST0, ST1, W0, W1, W2, PINK = range(16)
CASTLES_FG = [
    (0x15, 0x13, 0x1A),  # FK   обводка
    (0xD6, 0xEE, 0x74),  # G0   кромка травы
    (0x92, 0xD0, 0x50),  # G1   трава
    (0x5C, 0xAE, 0x4A),  # G2
    (0x2A, 0x6A, 0x3E),  # G3   тень травы
    (0xB6, 0xB2, 0xAC),  # S0   тёсаный камень, свет
    (0x92, 0x8E, 0x8A),  # S1   камень кладки
    (0x70, 0x6C, 0x6E),  # S2   камень в тени
    (0x4E, 0x4C, 0x58),  # S3   тень блока
    (0x2C, 0x2C, 0x3A),  # S4   швы
    (0xE4, 0xDE, 0xCA),  # ST0  известняк
    (0xAA, 0xA2, 0x92),  # ST1  тень известняка
    (0xDA, 0xAE, 0x6C),  # W0   дерево, свет, колос, сердцевина ромашки
    (0x9C, 0x64, 0x2C),  # W1   дерево
    (0x5E, 0x3C, 0x26),  # W2   тень дерева
    (0xD2, 0x30, 0x2C),  # PINK красное: розы, маки, оперение стрел
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


def _foliage(c, rng, cx, cy, r, cols, leaf=1.0):
    """Ком дубовой листвы: волнистый край из мелких кругов, тень снизу справа, свет сверху
    слева, поверх штрихи листьев дугами. `cols` от светлого к тёмному: блик, свет, тело, тень."""
    hi, light, body, shade = cols
    _wellipse(c, cx + r * 0.1, cy + r * 0.14, r, r * 0.8, shade)
    # Лопасти по краю: дубовый лист волной, а не гладкий овал.
    n = max(7, int(r * 0.7))
    for i in range(n):
        a = math.tau * i / n + rng.uniform(-0.2, 0.2)
        rr = r * rng.uniform(0.2, 0.3)
        col = shade if math.sin(a) > 0.25 or math.cos(a) > 0.6 else body
        _wellipse(c, cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.7, rr, rr * 0.9, col)
    _wellipse(c, cx, cy, r * 0.9, r * 0.7, body)
    _wellipse(c, cx - r * 0.22, cy - r * 0.24, r * 0.6, r * 0.42, light)
    _wellipse(c, cx - r * 0.34, cy - r * 0.36, r * 0.26, r * 0.16, hi)
    for _ in range(int(r * r * 0.09 * leaf)):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0.0, 0.85)
        x = cx + math.cos(a) * r * d
        y = cy + math.sin(a) * r * 0.72 * d
        here = c.get(int(math.floor(x)) % c.w, int(round(y)))
        if here == body:
            col = light if rng.random() < 0.45 else shade
        elif here == light:
            col = body
        elif here == shade:
            col = body if rng.random() < 0.35 else None
        else:
            col = None
        if col is not None:
            _wset(c, x, int(round(y)), col)
            _wset(c, x + 1, int(round(y)) + 1, col)


def _bark(c, x0, x1, y0, y1, cols, rng):
    """Ствол дуба: светлый край слева, глубокие извилистые борозды, дупла-сучки, мох снизу."""
    light, body, shade = cols
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            k = (x - x0) / max(x1 - x0, 1)
            _wset(c, x, y, light if k < 0.18 else (body if k < 0.68 else shade))
    # Борозды: длинные извилистые, рядом светлая грань гребня.
    for gx in range(int(x0) + 3, int(x1) - 2, 5):
        ph = rng.uniform(0, 6)
        gap = rng.randint(17, 29)
        for y in range(int(y0), int(y1)):
            if (y + gx * 3) % gap < 4:
                continue
            wob = int(round(math.sin(y * 0.07 + ph) * 1.6 + math.sin(y * 0.23 + ph) * 0.6))
            k = (gx + wob - x0) / max(x1 - x0, 1)
            _wset(c, gx + wob, y, shade if k < 0.68 else DK)
            if k < 0.6 and (y + gx) % 3:
                _wset(c, gx + wob + 1, y, light)
    # Сучки: тёмное дупло в светлом ободе.
    for _ in range(int((y1 - y0) / 70) + 1):
        kx = rng.uniform(x0 + 6, x1 - 7)
        ky = rng.uniform(y0 + 30, y1 - 40)
        _wellipse(c, kx, ky, 4, 5, light)
        _wellipse(c, kx + 0.5, ky + 0.5, 3, 4, shade)
        _wellipse(c, kx + 0.5, ky + 1, 1.5, 2.5, DK)
    # Мох у земли с наветренной стороны.
    for _ in range(int((x1 - x0) * 1.6)):
        mx = rng.uniform(x0, x0 + (x1 - x0) * 0.55)
        my = rng.uniform(y1 - 46, y1 - 2)
        if rng.random() < (my - (y1 - 46)) / 46.0:
            _wset(c, mx, int(my), MO)
            _wset(c, mx + 1, int(my), L3)


def _fir(c, x, base, h, cols, w=None):
    """Ель ярусами от земли `base` вверх на `h`: лапы зубцами, свет слева."""
    light, body, shade = cols
    w = h * 0.46 if w is None else w
    tiers = max(3, int(h / 9))
    for j in range(int(h)):
        k = j / max(h, 1.0)
        # Пила ярусов: каждый ярус шире к низу и обрывается.
        t = (k * tiers) % 1.0
        half = w * 0.5 * (1.0 - k) * (0.55 + 0.45 * (1.0 - t)) + 0.6
        for dx in range(int(-half), int(half) + 1):
            u = dx / max(half, 0.5)
            col = light if u < -0.35 else (body if u < 0.3 else shade)
            if t > 0.86:
                col = shade
            _wset(c, x + dx, int(base - j), col)


def _banner(c, x, y0, length, w=9):
    """Турнирный стяг на шнуре: красное полотнище с золотой каймой и полосой, низ ласточкиным
    хвостом."""
    for y in range(int(y0) - 14, int(y0)):
        _wset(c, x + w // 2, y, T2)
    c_top = int(y0)
    for dx in range(-1, w + 1):
        _wset(c, x + dx, c_top, T0)
        _wset(c, x + dx, c_top + 1, T2)
    for j in range(int(length)):
        y = c_top + 2 + j
        cut = 0
        if j > length - 6:
            cut = j - (length - 6)
        for dx in range(w):
            mid = abs(dx - (w - 1) / 2.0)
            if mid < cut * 0.75:
                continue
            col = FL2
            if dx == 0 or dx == w - 1:
                col = FL1
            elif dx == w - 2:
                col = T2
            _wset(c, x + dx, y, col)
        if j in (3, 4):
            for dx in range(1, w - 1):
                _wset(c, x + dx, y, FL1)
    # Герб: золотой ромб посередине.
    cy = c_top + 2 + int(length * 0.5)
    for dy in range(-2, 3):
        for dx in range(-2 + abs(dy), 3 - abs(dy)):
            _wset(c, x + w // 2 + dx, cy + dy, FL1)


# --- Фон ---------------------------------------------------------------------------------------

def _castle_tower(c, x0, w, top, roof):
    """Башня замка в дымке: зубцы или шатёр с флажком, бойницы, тень справа."""
    for y in range(int(top), 240):
        for dx in range(w):
            _wset(c, x0 + dx, y, HZ2 if dx >= w - 3 else HZ1)
    if roof:
        # Свес и шатёр.
        for dx in range(-2, w + 2):
            _wset(c, x0 + dx, int(top), HZ2)
            _wset(c, x0 + dx, int(top) - 1, HZ2)
        h = int(w * 1.3)
        for j in range(h):
            half = (w / 2.0 + 2) * (1.0 - j / float(h))
            for dx in range(int(-half), int(half) + 1):
                _wset(c, x0 + w / 2.0 + dx, int(top) - 2 - j, HZ2)
        px = x0 + w / 2.0
        for j in range(9):
            _wset(c, px, int(top) - 2 - h - j, HZ2)
        for j in range(4):
            for dx in range(1, 7 - j):
                _wset(c, px + dx, int(top) - 10 - h + j, HZ2)
    else:
        # Выступ с зубцами.
        for dx in range(-2, w + 2):
            for y in range(int(top), int(top) + 5):
                _wset(c, x0 + dx, y, HZ2 if dx >= w - 1 else HZ1)
            if (dx + 2) % 6 < 3:
                for y in range(int(top) - 4, int(top)):
                    _wset(c, x0 + dx, y, HZ1)
        for dx in range(-2, w + 2):
            _wset(c, x0 + dx, int(top) + 5, HZ2)
    # Бойницы и окна.
    for k, wy in enumerate(range(int(top) + 14, 200, 26)):
        wx = x0 + w * (0.35 if k % 2 == 0 else 0.6)
        for dy in range(6):
            _wset(c, wx, wy + dy, HZ3 if dy else HZ2)
            _wset(c, wx + 1, wy + dy, HZ2)
    # Швы кладки намёком.
    for y in range(int(top) + 9, 236, 9):
        for dx in range(1, w - 4, 7):
            if (y + dx) % 3:
                _wset(c, x0 + dx + (y % 2) * 3, y, HZ0)
                _wset(c, x0 + dx + (y % 2) * 3 + 1, y, HZ0)


def par3_back():
    """Даль на весь экран, 512×277: голубая дымка, за ней стена замка с зубцами, башни с
    шатрами и флажками, перед стеной силуэты елей и дубов; низ сплошной."""
    rng = random.Random(241)
    c = Canvas(512, 277)
    c.rect(0, 0, 511, 276, HZ0)
    # Куртина с зубцами волной по холму.
    for x in range(512):
        top = 150 + int(round(10 * math.sin(x * math.tau / 512.0) + 5 * math.sin(x * math.tau / 256.0 + 1.0)))
        if x % 8 < 4:
            top -= 4
        c.rect(x, top, x, 240, HZ1)
        c.set(x, top + 9, HZ2)
        if x % 14 == 0:
            c.rect(x, top + 16, x, top + 20, HZ2)
    for x0, w, top, roof in ((34, 26, 84, True), (138, 20, 118, False), (232, 34, 58, True), (276, 18, 104, False),
                             (368, 22, 126, False), (446, 28, 92, True)):
        _castle_tower(c, x0, w, top, roof)
    # Ворота в куртине.
    for y in range(188, 240):
        for x in range(186, 210):
            if y > 200 or (x - 198) ** 2 + (y - 200) ** 2 <= 144:
                c.set(x, y, HZ2)
    for x in range(188, 210, 4):
        c.rect(x, 192, x, 239, HZ3)
    # Дальние дубы комьями и ели перед стеной.
    for x in range(0, 512, 23):
        _wellipse(c, x + rng.uniform(-6, 6), rng.uniform(204, 222), rng.uniform(14, 22), rng.uniform(12, 18), HZ2)
    for _ in range(26):
        _fir(c, rng.uniform(0, 512), 240, rng.uniform(34, 84), (HZ2, HZ2, HZ3))
    for x in range(0, 512, 12):
        cx = x + rng.uniform(-4, 4)
        _wellipse(c, cx, rng.uniform(226, 238), rng.uniform(9, 15), rng.uniform(7, 11), HZ3)
    # Птицы над башнями.
    for _ in range(9):
        x = rng.uniform(0, 512)
        y = int(rng.uniform(24, 110))
        if c.get(int(x), y) == HZ0:
            for dx, dy in ((-2, -1), (-1, 0), (0, 1), (1, 0), (2, -1)):
                _wset(c, x + dx, y + dy, HZ2)
    c.rect(0, 232, 511, 276, HZ3)
    return c


def par3_trees():
    """Большие дубы, 512×277, прозрачно между ними: бороздчатая кора с дуплами, корни
    расходятся к земле, по стволу плющ; кроны наверху сплошной полосой, с них свисают стяги."""
    rng = random.Random(242)
    c = Canvas(512, 277)
    for x, w in ((40, 30), (196, 22), (300, 38), (452, 26)):
        # Корни расходятся к земле (сначала, ствол ложится поверх без щели).
        for side in (-1, 1):
            for i in range(18):
                yy = 244 + i
                spread = int(i * i * 0.07 + i * 0.3)
                if side < 0:
                    for xx in range(max(x - spread, 0), x + 4):
                        c.set(xx, yy, T0 if xx == max(x - spread, 0) else T1)
                else:
                    for xx in range(x + w - 4, min(x + w + spread, 511) + 1):
                        c.set(xx, yy, T2)
        _bark(c, x, x + w, 40, 262, (T0, T1, T2), rng)
        # Плющ вьётся по стволу.
        ph = rng.uniform(0, 6)
        for y in range(70, 250):
            vx = x + w * 0.5 + math.sin(y * 0.05 + ph) * w * 0.38
            _wset(c, vx, y, L4)
            if y % 6 == 0:
                side = 1 if (y // 6) % 2 else -1
                _wset(c, vx + side, y, L2)
                _wset(c, vx + side * 2, y, L2)
                _wset(c, vx + side * 2, y - 1, L1)
                _wset(c, vx + side, y + 1, L3)
    # Стяги висят с кроны (рисуются до листвы: шнур уходит в неё).
    for x, length in ((92, 62), (128, 44), (246, 70), (372, 52), (408, 74)):
        _banner(c, x, 60, length)
    # Крона: сверху тёмные ряды, поверх них нижний ряд крупных светлых комьев над стволами.
    for x in range(0, 512, 24):
        _foliage(c, rng, x + rng.uniform(-6, 6), rng.uniform(-2, 8), rng.uniform(18, 26), (L2, L3, L4, DK), 0.6)
    for x in range(0, 512, 22):
        _foliage(c, rng, x + rng.uniform(-6, 6), rng.uniform(16, 28), rng.uniform(20, 28), (L1, L2, L3, L4), 0.8)
    for x in range(0, 512, 26):
        _foliage(c, rng, x + rng.uniform(-6, 6), rng.uniform(40, 56), rng.uniform(24, 32), (L0, L1, L2, L3), 1.0)
    # Жёлуди под нижней кромкой кроны.
    for _ in range(26):
        x = rng.uniform(0, 512)
        for y in range(40, 84):
            if c.get(int(x) % 512, y) is None and c.get(int(x) % 512, y - 1) in (L2, L3):
                _wset(c, x, y, T2)
                _wset(c, x, y + 1, FL1)
                _wset(c, x, y + 2, FL1)
                break
    return c


def _rose(c, x, y, big=True):
    """Роза: красный венчик, тёмная сердцевина завитком, золотая искра."""
    for dx, dy in ((0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)):
        _wset(c, x + dx, y + dy, FL2)
    if big:
        _wset(c, x + 1, y - 1, FL2)
        _wset(c, x - 1, y + 1, FL2)
        _wset(c, x, y, T2)
        _wset(c, x - 1, y - 1, FL1)


def par3_bushes():
    """Живая изгородь у земли, 512×120, прозрачный верх: кусты роз в красных цветах и ёлочки
    между ними; низ сплошной."""
    rng = random.Random(243)
    c = Canvas(512, 120)
    for x in range(0, 512, 16):
        cx = x + rng.uniform(-5, 5)
        if rng.random() < 0.28:
            _fir(c, cx, 98, rng.uniform(44, 70), (L3, MO, L4), rng.uniform(22, 30))
            continue
        cy = rng.uniform(56, 82)
        r = rng.uniform(16, 25)
        _foliage(c, rng, cx, cy, r, (L0, L1, L2, L3), 1.2)
        for _ in range(int(r * 0.45)):
            a = rng.uniform(0, math.tau)
            d = rng.uniform(0.1, 0.8)
            _rose(c, cx + math.cos(a) * r * d, int(cy + math.sin(a) * r * 0.66 * d), rng.random() < 0.6)
    c.rect(0, 92, 511, 119, L4)
    for x in range(0, 512, 9):
        _foliage(c, rng, x + rng.uniform(-3, 3), rng.uniform(92, 99), rng.uniform(8, 12), (L1, L2, L3, L4), 0.8)
    for _ in range(280):
        x = rng.uniform(0, 512)
        y = rng.uniform(102, 119)
        _wset(c, x, int(y), L3 if rng.random() < 0.6 else DK)
    for _ in range(22):
        _rose(c, rng.uniform(0, 512), int(rng.uniform(90, 104)), False)
    # Опавшие лепестки и бабочки в просветах.
    for _ in range(30):
        x = rng.uniform(0, 512)
        y = rng.uniform(26, 90)
        if c.get(int(x) % 512, int(y)) is None:
            _wset(c, x, int(y), FL1 if rng.random() < 0.6 else FL2)
    return c


def canopy_front():
    """Дубовая листва над кадром спереди, 256×56, прозрачный низ: тёмные ветви и под ними
    гирлянда турнирных флажков на шнуре, красные через один с золотыми."""
    rng = random.Random(244)
    c = Canvas(256, 56)

    def rope(x):
        return 27 + 13 * math.sin(math.pi * (x % 128) / 128.0)

    for x in range(256):
        c.set(x, int(round(rope(x))), T2)
    for k, x0 in enumerate(range(6, 256, 12)):
        col = FL2 if k % 2 == 0 else FL1
        for j in range(9):
            half = 4.0 * (1.0 - j / 9.0)
            for dx in range(int(-half), int(half) + 1):
                y = int(round(rope(x0 + dx))) + 1 + j
                edge = dx >= half - 1 and j < 7
                c.set(x0 + dx, y, (T2 if col == FL2 else T0) if edge else col)
    for x in range(0, 256, 21):
        _foliage(c, rng, x + rng.uniform(-4, 4), rng.uniform(-5, 1), rng.uniform(13, 17), (L3, L4, DK, DK), 0.5)
    for x in range(0, 256, 15):
        _foliage(c, rng, x + rng.uniform(-4, 4), rng.uniform(5, 12), rng.uniform(12, 17), (L2, L3, L4, DK), 0.9)
    # Жёлуди висят с листвы.
    for _ in range(12):
        x = int(rng.uniform(0, 256))
        for y in range(8, 40):
            if c.get(x, y) is None and c.get(x, y - 1) in (L3, L4, DK):
                c.set(x, y, T2)
                c.set(x, y + 1, FL1)
                c.set(x, y + 2, FL1)
                break
    return c


# --- Передний план -----------------------------------------------------------------------------

def trail_soil():
    """Тёсаная кладка, 64×64 по кругу в обе стороны: ряды блоков разной длины вперевязку, свет
    на верхней и левой грани, тень снизу справа, тёмные швы, сколы, трещины и редкий мох."""
    rng = random.Random(251)
    n = 64
    c = Canvas(n, n)
    c.rect(0, 0, n - 1, n - 1, S4)
    row_h = 8
    for r in range(n // row_h):
        y0 = r * row_h
        widths = []
        left = n
        while left > 20:
            w = rng.randint(9, 15)
            widths.append(w)
            left -= w
        if left > 15:
            widths += [left // 2, left - left // 2]
        else:
            widths.append(left)
        x = rng.randint(0, 7) + (r % 2) * 5
        for w in widths:
            tone = rng.random()
            body = S1 if tone < 0.62 else (S2 if tone < 0.88 else S0)
            lit = S0 if body != S0 else ST1
            dark = S3 if body != S2 else S3
            for dy in range(row_h - 1):
                for dx in range(w - 1):
                    col = body
                    if dy == 0 or dx == 0:
                        col = lit
                    if dy == row_h - 2 or dx == w - 2:
                        col = dark
                    if (dy == 0 and dx == w - 2) or (dx == 0 and dy == row_h - 2):
                        col = body
                    c.set((x + dx) % n, y0 + dy, col)
            # Насечка зубилом и щербины.
            for _ in range(w // 3):
                px = x + rng.randint(2, w - 4)
                py = y0 + rng.randint(2, row_h - 4)
                c.set(px % n, py, S2 if body != S2 else S3)
                if rng.random() < 0.5:
                    c.set((px + 1) % n, py, lit)
            # Трещина наискось.
            if rng.random() < 0.22 and w > 10:
                px = x + rng.randint(3, w - 6)
                for k in range(row_h - 3):
                    c.set((px + k // 2) % n, y0 + 1 + k, S3)
            # Сколотый угол.
            if rng.random() < 0.3:
                c.set((x + w - 2) % n, y0, S4)
                c.set((x + w - 3) % n, y0, dark)
            x += w
    # Мох в швах.
    for _ in range(9):
        x = rng.randrange(n)
        y = rng.randrange(n // row_h) * row_h + row_h - 1
        for dx in range(rng.randint(2, 5)):
            c.set((x + dx) % n, y, G3)
            if rng.random() < 0.4:
                c.set((x + dx) % n, (y + 1) % n, G2)
    return c


def trail_edge():
    """Травяная кромка, 32×18 по кругу: поверхность на строке 4, травинки над ней, дёрн
    свисает бахромой на кладку; ниже прозрачно, там грунт."""
    rng = random.Random(252)
    c = Canvas(32, 18)
    top = 4
    for x in range(32):
        hang = top + 3 + int(1.5 + 1.5 * math.sin(x * math.tau / 8.0) + rng.uniform(0, 2.2))
        c.rect(x, top, x, hang, G2)
        c.rect(x, top, x, top + 1, G1)
        c.rect(x, top, x, top, G0)
        if x % 4 == 1:
            c.set(x, top + 2, G1)
        if x % 5 == 3:
            c.set(x, top + 3, G3)
        c.set(x, hang, G3)
        c.set(x, hang + 1, FK)
        if rng.random() < 0.5:
            h = rng.randint(1, 3)
            c.rect(x, top - h, x, top - 1, G1 if rng.random() < 0.5 else G0)
    # Ромашка и мак на кромке.
    c.set(9, 1, ST0)
    c.set(9, 2, G2)
    c.set(23, 0, PINK)
    c.set(23, 1, G2)
    c.set(23, 2, G2)
    return c


def arch_bark():
    """Грань каменной арки, 32×32 по кругу: блоки светлого известняка 16×8 вперевязку, фаска
    светом сверху, выбоины, по камню плющ."""
    rng = random.Random(253)
    c = Canvas(32, 32)
    for y in range(32):
        row = y // 8
        for x in range(32):
            bx = (x + (8 if row % 2 else 0)) % 16
            by = y % 8
            if by == 7 or bx == 15:
                col = S3
            elif by == 0 or bx == 0:
                col = ST0
            elif by == 6 or bx == 14:
                col = S1
            else:
                col = ST0 if ((x + (8 if row % 2 else 0)) // 16 + row) % 3 == 0 else ST1
            c.set(x, y, col)
    # Блоки с более светлым телом получают тёплую середину, чтобы не сливались с фаской.
    for y in range(32):
        row = y // 8
        for x in range(32):
            bx = (x + (8 if row % 2 else 0)) % 16
            by = y % 8
            if 1 <= by <= 5 and 1 <= bx <= 13 and c.get(x, y) == ST0 and (x * 7 + y * 3) % 5 == 0:
                c.set(x, y, ST1)
    for _ in range(14):
        x = rng.randint(0, 31)
        y = rng.randint(0, 31)
        if y % 8 in (2, 3, 4):
            c.set(x, y, S1)
            c.set((x + 1) % 32, y, S2)
    # Плющ: две плети с листьями.
    for x0, ph in ((6, 0.0), (22, 2.0)):
        for y in range(32):
            vx = x0 + math.sin(y * math.tau / 32.0 + ph) * 3
            c.set(int(round(vx)) % 32, y, G3)
            if y % 4 == 0:
                side = 1 if (y // 4) % 2 else -1
                c.set(int(round(vx + side)) % 32, y, G2)
                c.set(int(round(vx + side * 2)) % 32, y, G1)
                c.set(int(round(vx + side * 2)) % 32, (y + 1) % 32, G2)
    return c


def _blade(c, x, h, bend, col, side, tip=None):
    for j in range(int(h)):
        k = j / h
        c.set(x + bend * k * k, c.h - 1 - j, col)
        if k < 0.55:
            c.set(x + bend * k * k + 1, c.h - 1 - j, side)
    if tip is not None:
        # Колос: три зерна вдоль стебля.
        for j in range(3):
            c.set(x + bend, c.h - int(h) + j, tip)
        c.set(x + bend + 1, c.h - int(h) + 1, tip)


def dec_grass(i):
    """Высокая луговая трава перед героем, 32×24, два кадра качания; у части стеблей колос."""
    rng = random.Random(261)
    c = Canvas(32, 24)
    for _ in range(16):
        x = rng.uniform(2, 29)
        col = rng.choice((G1, G2, G1, G0))
        tip = W0 if rng.random() < 0.35 else None
        _blade(c, x, rng.uniform(9, 21), rng.uniform(-3, 3) + (1.5 if i else -0.5), col, G3 if col == G2 else G2, tip)
    return c


def dec_tuft(i):
    """Кочка короткой травы, 32×14, два кадра качания."""
    rng = random.Random(262)
    c = Canvas(32, 14)
    for _ in range(11):
        _blade(c, rng.uniform(2, 29), rng.uniform(4, 11), rng.uniform(-2, 2) + (1 if i else 0), rng.choice((G0, G1, G2)), G3)
    return c


def _fg_fir(c, x, base, h, w):
    """Ёлочка переднего плана: ярусы лап зубцами, свет слева, снег не нужен: лето."""
    tiers = max(3, int(h / 7))
    for j in range(int(h)):
        k = j / float(h)
        t = (k * tiers) % 1.0
        half = w * 0.5 * (1.0 - k) * (0.5 + 0.5 * (1.0 - t)) + 0.7
        for dx in range(int(-half), int(half) + 1):
            u = dx / max(half, 0.5)
            col = G1 if u < -0.4 else (G2 if u < 0.25 else G3)
            if t > 0.84 and u > -0.5:
                col = G3
            c.set(x + dx, base - j, col)


def dec_fern():
    """Две молодые ели за героем, 48×32: большая и малая, ярусы лап, короткие стволики."""
    c = Canvas(48, 32)
    c.rect(18, 28, 20, 31, W1)
    c.rect(20, 28, 20, 31, W2)
    c.rect(36, 29, 37, 31, W1)
    _fg_fir(c, 19, 28, 28, 25)
    _fg_fir(c, 36, 29, 17, 15)
    # Шишки.
    for x, y in ((15, 21), (23, 16), (20, 24), (35, 24)):
        c.set(x, y, W1)
        c.set(x, y + 1, W2)
    c.outline(FK)
    return c


def dec_bush():
    """Куст роз за героем, 64×36: три кома листвы, крупные красные розы и бутоны, у земли
    тень."""
    rng = random.Random(264)
    c = Canvas(64, 36)
    for cx, cy, r in ((16, 22, 11), (47, 21, 12), (31, 16, 14)):
        c.ellipse(cx + 1, cy + 2, r, r * 0.82, G3)
        c.ellipse(cx, cy, r * 0.94, r * 0.76, G2)
        c.ellipse(cx - r * 0.25, cy - r * 0.26, r * 0.6, r * 0.42, G1)
        for _ in range(int(r * 2.2)):
            a = rng.uniform(0, math.tau)
            d = rng.uniform(0.1, 0.88)
            x = int(round(cx + math.cos(a) * r * d))
            y = int(round(cy + math.sin(a) * r * 0.76 * d))
            here = c.get(x, y)
            if here == G2:
                c.set(x, y, G1 if rng.random() < 0.5 else G3)
            elif here == G1:
                c.set(x, y, G0 if rng.random() < 0.4 else G2)
    for x, y in ((11, 18), (21, 25), (26, 10), (36, 14), (31, 21), (43, 15), (52, 23), (45, 26), (17, 28)):
        for dx, dy in ((0, -1), (-1, 0), (0, 0), (1, 0), (0, 1), (1, -1), (-1, 1), (-1, -1)):
            c.set(x + dx, y + dy, PINK)
        c.set(x, y, W2)
        c.set(x - 1, y - 1, ST0)
        c.set(x + 1, y + 1, W2)
        c.set(x + 2, y + 1, G3)
    for x, y in ((6, 24), (38, 6), (57, 17), (25, 27)):
        c.set(x, y, PINK)
        c.set(x, y + 1, G3)
    c.rect(5, 32, 58, 35, G3)
    for x in range(5, 59):
        if rng.random() < 0.5:
            c.set(x, 31, G2)
        if rng.random() < 0.25:
            c.set(x, 32, G1)
    c.outline(FK)
    return c


def dec_rock():
    """Обломок стены, 32×20: два тёсаных блока известняка, верхний съехал набок, швы, скол,
    мох и трава у подножия."""
    c = Canvas(32, 20)
    # Нижний блок лежит ровно.
    c.rect(4, 11, 26, 19, ST1)
    c.rect(4, 11, 24, 17, ST0)
    c.rect(4, 11, 26, 11, ST0)
    c.rect(25, 12, 26, 19, S1)
    c.rect(5, 18, 26, 19, S1)
    c.rect(14, 12, 14, 19, S2)
    # Верхний съехал и накренился.
    c.poly([(8, 10), (9, 4), (22, 2), (23, 10)], ST1)
    c.poly([(9, 9), (10, 5), (20, 3), (21, 8)], ST0)
    c.line(21, 4, 22, 10, S1, 1)
    c.line(8, 10, 23, 10, S2, 1)
    # Выбоины, трещина и сколотый угол.
    c.set(12, 6, ST1)
    c.set(17, 5, ST1)
    c.set(8, 14, ST1)
    c.set(19, 15, ST1)
    c.line(20, 12, 22, 16, S2, 1)
    c.set(4, 11, None)
    c.set(5, 11, None)
    c.set(4, 12, None)
    # Мох на камне и трава у подножия.
    c.rect(10, 4, 13, 4, G2)
    c.set(11, 5, G3)
    c.rect(16, 11, 19, 11, G2)
    c.poly([(0, 19), (4, 15), (7, 19)], G2)
    c.poly([(24, 19), (28, 14), (31, 19)], G1)
    c.set(3, 16, G1)
    c.outline(FK)
    return c


def dec_flowers():
    """Ромашки и маки в траве, 32×20: белые венчики с жёлтой сердцевиной, красные маки."""
    rng = random.Random(265)
    c = Canvas(32, 20)
    for _ in range(9):
        _blade(c, rng.uniform(2, 29), rng.uniform(4, 9), rng.uniform(-2, 2), rng.choice((G1, G2)), G3)
    for k, (x, y) in enumerate(((6, 8), (14, 5), (22, 9), (27, 6))):
        c.line(x, y + 2, x, 19, G2, 1)
        c.set(x + 1, y + 5, G1)
        if k % 2 == 0:
            for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
                c.set(x + dx, y + dy, ST0)
            c.set(x, y, W0)
        else:
            for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1), (-1, -1), (1, -1)):
                c.set(x + dx, y + dy, PINK)
            c.set(x, y, FK)
    return c


def dec_mush():
    """Стрелы, воткнутые в землю, 32×16: три древка под разным углом с красно-белым оперением."""
    c = Canvas(32, 16)
    for (x0, y0, x1, y1) in ((9, 15, 4, 2), (17, 15, 18, 0), (23, 15, 29, 3)):
        c.line(x0, y0, x1, y1, W1, 1)
        n = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / n, (y1 - y0) / n
        # Оперение: перья по сторонам от древка ниже хвостовика, сам хвостовик тонкий.
        for k in (2, 3, 4, 5):
            px = x1 - ux * k
            py = y1 - uy * k
            col = ST0 if k == 3 else PINK
            wide = 1.3 if k < 5 else 1.0
            c.set(px - uy * wide, py + ux * wide, col)
            c.set(px + uy * wide, py - ux * wide, col)
        c.set(x1, y1, W0)
        c.set(x1 - ux, y1 - uy, W0)
    c.outline(FK)
    return c


# --- Враги (палитра спрайтов) ------------------------------------------------------------------

def crab(i):
    """Ползун тропы: кабан из основы, четыре кадра шага, красная обводка опасности."""
    return castles16.boar(i)


def drone(i):
    """Летун тропы: летучая мышь из основы, четыре кадра взмаха, тело по центру кадра."""
    return castles16.bat(i)


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


def preview(path):
    items = castles16.shaded(sprites())
    for key, canvas in foreground().items():
        items[key] = (canvas, CASTLES_FG)
    for key, canvas in backdrop().items():
        items[key] = (canvas, CASTLES_BG)
    castles16.save_sheet(path, items, scale=2)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
