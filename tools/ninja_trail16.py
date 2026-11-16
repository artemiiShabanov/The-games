#!/usr/bin/env python3
"""Набор «Ниндзя» для платформера × 16/32-bit «тропа» (#137), зеркало `space_trail16.py` и
`pixel_trail16.py`: те же ключи, размеры холстов, число кадров и точки опоры. Вместо леса
кленовая роща на закате: фон без неба в три слоя (закатная дымка с силуэтами бамбука и пагоды,
большие клёны и бамбук с красной кроной сплошной полосой наверху и бумажными фонарями на
нитях, стриженые азалии с каменными фонарями у земли) и тёмная кленовая листва над кадром
спереди; земля из каменной кладки замка (исигаки) с подушками мха по кромке; арка из красного
лакового бруса с кованой полосой.

У фона и переднего плана свои палитры по 16 цветов (`NINJA_BG`, `NINJA_FG`); жаба-ползун и
ворон-тэнгу в палитре спрайтов `ninja16.PALETTE`, рисунок их утверждён в основе `ninja16.py`.
Ленты героя рисует `ninja16.py`. Ленты фона 512 пикселей шириной стыкуются по краям.
Случайность с постоянным зерном: картинка одна и та же.

    python3 tools/ninja_trail16.py --preview out.png

Лист выше 1500 пикселей пишется несколькими файлами: out.png, out_b.png, out_c.png.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ninja16  # noqa: E402
from ninja16 import Canvas, strip  # noqa: E402

# Палитра фона: закатная дымка, кленовая листва, бамбук, тени, огни.
HZ0, HZ1, HZ2, HZ3, L0, L1, L2, L3, L4, T0, T1, T2, DK, FL1, FL2, MO = range(16)
NINJA_BG = [
    (0xF8, 0xDA, 0xA6),  # HZ0  просвет заката в дали
    (0xEC, 0xAE, 0x88),  # HZ1  дымка
    (0xBE, 0x7C, 0x86),  # HZ2  дальние стволы и кроны
    (0x80, 0x52, 0x7A),  # HZ3  глубина дали, свет на коре
    (0xFA, 0xD2, 0x68),  # L0   блик кленового листа
    (0xF2, 0x8C, 0x38),  # L1   лист, свет
    (0xD8, 0x46, 0x2E),  # L2   лист
    (0x9E, 0x28, 0x32),  # L3   лист, тень
    (0x58, 0x1C, 0x30),  # L4   глубокая тень листвы, кора
    (0xC8, 0xD4, 0x7C),  # T0   бамбук, свет
    (0x82, 0xA8, 0x4E),  # T1   бамбук
    (0x44, 0x70, 0x40),  # T2   бамбук, тень
    (0x1C, 0x12, 0x22),  # DK   самая тёмная тень
    (0xFC, 0xEC, 0x9A),  # FL1  огонь фонаря, светлячки
    (0xF6, 0xA8, 0xBC),  # FL2  цветы азалии, лепестки
    (0x28, 0x4C, 0x3C),  # MO   мох, тень зелени
]

# Палитра переднего плана: мох, кладка, камень, красный лак, цветы.
FK, G0, G1, G2, G3, S0, S1, S2, S3, S4, ST0, ST1, W0, W1, W2, PINK = range(16)
NINJA_FG = [
    (0x16, 0x10, 0x1E),  # FK   обводка
    (0xCC, 0xE0, 0x70),  # G0   кромка мха
    (0x8A, 0xBA, 0x48),  # G1   мох
    (0x4E, 0x8C, 0x40),  # G2
    (0x2A, 0x5A, 0x3C),  # G3   тень мха
    (0xB4, 0xA2, 0x92),  # S0   камень кладки, закатный свет
    (0x88, 0x7A, 0x7A),  # S1   камень
    (0x60, 0x56, 0x66),  # S2   тень камня
    (0x40, 0x3A, 0x52),  # S3   глубокая тень
    (0x24, 0x20, 0x38),  # S4   швы
    (0xCE, 0xCA, 0xCE),  # ST0  светлый камень, метёлки травы
    (0x8A, 0x86, 0x9C),  # ST1  тень светлого камня
    (0xF4, 0x78, 0x4C),  # W0   красный лак, свет; кленовый лист
    (0xD2, 0x3C, 0x30),  # W1   красный лак
    (0x8A, 0x22, 0x32),  # W2   тень лака
    (0xF8, 0xB0, 0xC4),  # PINK азалия, лепестки
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


def _wline(c, x0, y0, x1, y1, col, t=1):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        y = y0 + (y1 - y0) * i / n
        for d in range(t):
            _wset(c, x + d, int(round(y)), col)


def _leaf(c, x, y, col, vein=None):
    """Кленовый лист звёздочкой в пять пикселей, черешок вниз."""
    y = int(y)
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (-1, -1), (1, -1)):
        _wset(c, x + dx, y + dy, col)
    _wset(c, x - 2, y - 1, col)
    _wset(c, x + 2, y - 1, col)
    _wset(c, x, y - 2, col)
    _wset(c, x, y + 1, vein if vein is not None else col)


def _maple(c, rng, cx, cy, r, cols, flat=0.8, leaves=True):
    """Охапка кленовой листвы: пятно с зубчатым краем, свет сверху слева, поверх россыпь
    листьев светлее и темнее. `cols` от светлого к тёмному: блик, свет, тело, тень."""
    hi, light, body, shade = cols
    ph = rng.uniform(0, 6.28)
    ry = r * flat
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - r - 2), int(cx + r + 3)):
            dx = (x - cx) / r
            dy = (y - cy) / ry
            a = math.atan2(dy, dx)
            edge = 0.84 + 0.1 * math.cos(a * 9 + ph) + 0.06 * math.cos(a * 17 - ph)
            if dx * dx + dy * dy > edge * edge:
                continue
            k = -dx * 0.55 - dy * 0.85
            _wset(c, x, y, light if k > 0.42 else (body if k > -0.25 else shade))
    if not leaves:
        return
    for _ in range(int(r * r * 0.05)):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(0, 0.72)
        x = cx + math.cos(a) * d * r
        y = cy + math.sin(a) * d * ry
        k = -(x - cx) / r * 0.55 - (y - cy) / ry * 0.85
        if k > 0.3:
            _leaf(c, x, y, hi if rng.random() < 0.6 else body, light)
        elif k > -0.2:
            _leaf(c, x, y, light if rng.random() < 0.55 else shade, body)
        else:
            _leaf(c, x, y, body if rng.random() < 0.35 else shade, shade)


def _bamboo(c, rng, x, w, y0, y1, cols, twigs=True):
    """Ствол бамбука от `y0` вниз до `y1`: светлый край слева, колена кольцами, у части колен
    веточка с узкими листьями."""
    light, body, shade, deep = cols
    for y in range(int(y0), int(y1)):
        for dx in range(int(w)):
            k = dx / max(w - 1.0, 1.0)
            col = light if k < 0.22 else (body if k < 0.7 else shade)
            if w >= 6 and dx == 1:
                col = body
            _wset(c, x + dx, y, col)
    y = y0 + rng.uniform(6, 20)
    side = 1
    while y < y1 - 4:
        yy = int(y)
        for dx in range(-1, int(w) + 1):
            _wset(c, x + dx, yy, light if dx < w * 0.5 else body)
            _wset(c, x + dx, yy + 1, deep)
        if twigs and rng.random() < 0.55:
            side = -side
            bx = x + (w if side > 0 else -1)
            ln = rng.uniform(7, 13)
            _wline(c, bx, yy, bx + side * ln, yy - ln * 0.35, shade)
            for k in range(3):
                lx = bx + side * ln * (0.45 + 0.27 * k)
                ly = yy - ln * 0.35 * (0.45 + 0.27 * k)
                n = rng.randint(6, 9)
                for j in range(n):
                    _wset(c, lx + side * j * 0.75, int(ly + j * 0.8), light if j < n - 2 and k != 1 else body)
                    if 1 <= j < n - 2:
                        _wset(c, lx + side * j * 0.75, int(ly + j * 0.8) + 1, shade)
        y += rng.uniform(20, 30) * (0.7 + w * 0.05)


def _lantern(c, x, y, small=False):
    """Бумажный фонарь тётин на нити: (x, y) верх фонаря. Светится изнутри, рёбра кольцами."""
    rx, ry = (3, 4) if small else (4, 6)
    cy = y + ry + 1
    for yy in range(cy - ry, cy + ry + 1):
        k = (yy - cy) / float(ry)
        half = int(round(rx * math.sqrt(max(0.0, 1.0 - k * k * 0.8))))
        for xx in range(-half, half + 1):
            edge = abs(xx) >= half
            col = L1 if edge else (FL1 if xx <= 0 else L0)
            if (yy - cy) % 3 == 0 and not edge and xx != -1:
                col = L0 if xx <= 0 else L1
            _wset(c, x + xx, yy, col)
    c.rect(x - rx + 1, cy - ry - 1, x + rx - 1, cy - ry, DK)
    c.rect(x - rx + 1, cy + ry, x + rx - 1, cy + ry + 1, DK)
    # Знак на боку и кисть внизу.
    c.rect(x, cy - 1, x, cy + 1, L3)
    c.set(x + 1, cy - 1, L3)
    c.rect(x, cy + ry + 2, x, cy + ry + (3 if small else 5), L2)


def _pagoda(c, x, base, col, dark, glow):
    """Силуэт пятиярусной пагоды в дымке: (x, base) середина основания."""
    y = base
    for k in range(5):
        hw = 15 - k * 2
        hh = 15 - k
        c.rect(x - hw, y - hh, x + hw, y, col)
        for wx in (-hw + 3, 0, hw - 3):
            c.rect(x + wx - 1, y - hh + 5, x + wx, y - hh + 8, glow if (k + wx) % 3 == 0 else dark)
        y -= hh
        rw = hw + 11
        for j in range(5):
            # Крыша: скат с загнутыми углами.
            half = rw - j * 3
            c.rect(x - half, y - j, x + half, y - j, dark if j < 2 else col)
        c.set(x - rw - 1, y - 1, dark)
        c.set(x + rw + 1, y - 1, dark)
        c.rect(x - rw - 2, y - 3, x - rw - 2, y - 2, dark)
        c.rect(x + rw + 2, y - 3, x + rw + 2, y - 2, dark)
        y -= 5
    c.rect(x, y - 22, x, y, dark)
    for j in (4, 8, 12, 16):
        c.rect(x - 2, y - j, x + 2, y - j, dark)


# --- Фон ---------------------------------------------------------------------------------------

def par3_back():
    """Даль на весь экран, 512×277: закатная дымка между стволами, силуэты бамбука и дальних
    кленовых крон, пагода в просвете; низ сплошной."""
    rng = random.Random(341)
    c = Canvas(512, 277)
    c.rect(0, 0, 511, 276, HZ1)
    # Просветы заката в глубине рощи.
    for x in range(0, 512, 13):
        if rng.random() < 0.62:
            _wellipse(c, x, rng.uniform(125, 185), rng.uniform(14, 30), rng.uniform(30, 58), HZ0)
    # Пагода в самом светлом просвете.
    _wellipse(c, 338, 150, 70, 80, HZ0)
    _pagoda(c, 338, 240, HZ2, HZ3, HZ0)
    # Дальние кроны: тёмная полоса наверху с зубчатым низом.
    c.rect(0, 0, 511, 38, HZ2)
    for x in range(0, 512, 19):
        _maple(c, rng, x + rng.uniform(-5, 5), rng.uniform(34, 56), rng.uniform(16, 26), (HZ1, HZ1, HZ2, HZ2), 0.75, False)
    c.rect(0, 0, 511, 12, HZ3)
    for x in range(0, 512, 23):
        _maple(c, rng, x + rng.uniform(-5, 5), rng.uniform(10, 24), rng.uniform(16, 24), (HZ2, HZ2, HZ3, HZ3), 0.7, False)
    # Дальний бамбук: тонкие стволы с коленами, часть наклонена.
    for i in range(46):
        x = rng.uniform(0, 512)
        w = rng.choice((2, 2, 3, 3, 4))
        near = rng.random() < 0.35
        lean = rng.uniform(-0.05, 0.05)
        top = rng.uniform(0, 30)
        step = rng.randint(13, 19)
        for y in range(int(top), 277):
            px = x + lean * (277 - y)
            for dx in range(w):
                col = HZ3 if near and dx >= w - 2 else HZ2
                _wset(c, px + dx, y, col)
            if (y + i * 5) % step == 0:
                for dx in range(-1, w + 1):
                    _wset(c, px + dx, y, HZ3)
                if not near:
                    _wset(c, px, y - 1, HZ1)
    # Листья в воздухе.
    for _ in range(60):
        x = rng.uniform(0, 512)
        y = int(rng.uniform(60, 226))
        col = HZ3 if rng.random() < 0.5 else HZ2
        _wset(c, x, y, col)
        _wset(c, x + 1, y + 1, col)
    # Поросль у земли и сплошной низ.
    for x in range(0, 512, 11):
        _maple(c, rng, x + rng.uniform(-3, 3), rng.uniform(228, 240), rng.uniform(9, 15), (HZ2, HZ2, HZ3, HZ3), 0.7, False)
    c.rect(0, 238, 511, 276, HZ3)
    return c


def _trunk_x(x, k, lean):
    """Середина ствола клёна на доле высоты `k` (0 наверху, 1 у земли): ствол гнётся коленом."""
    return x + math.sin(k * 4.2 + lean * 2) * 9 * (1 - k) ** 0.7 + lean * 10 * (1 - k)


def _bough(c, x0, y0, x1, y1, t, sag):
    """Сук от ствола в крону: дугой, к концу тоньше, свет сверху."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        k = i / float(n)
        x = x0 + (x1 - x0) * k
        y = y0 + (y1 - y0) * k + math.sin(k * math.pi) * sag
        w = max(2, int(round(t * (1 - k * 0.55))))
        for d in range(w):
            _wset(c, x, int(round(y)) + d, HZ3 if d == 0 else (L4 if d < w - 1 else DK))


def _maple_trunk(c, rng, x, w, y0, y1, lean):
    """Ствол старого клёна: гнётся, кора бороздами, мох у корней, корни расходятся к земле."""
    span = float(y1 - y0)
    for y in range(int(y0), int(y1)):
        k = (y - y0) / span
        cx = _trunk_x(x, k, lean)
        half = w * (0.36 + 0.14 * k) + (max(0.0, k - 0.9) * 10) ** 1.6
        for dx in range(int(-half), int(half) + 1):
            u = dx / max(half, 1.0)
            col = HZ3 if u < -0.55 else (L4 if u < 0.35 else DK)
            _wset(c, cx + dx, y, col)
        # Борозды коры: тёмные извилистые штрихи и редкие светлые.
        for g in range(-2, 3):
            gx = cx + g * half * 0.36 + math.sin(y * 0.09 + g * 1.7) * 1.6
            if (y + g * 7) % 17 < 11 and abs(gx - cx) < half - 1:
                _wset(c, gx, y, DK if g > -2 else L4)
            if g < 0 and (y + g * 5) % 23 < 4:
                _wset(c, gx + 1, y, HZ3)
    # Дупло и наплыв.
    ky = int(y0 + span * 0.55)
    kx = _trunk_x(x, 0.55, lean)
    _wellipse(c, kx + 1, ky, 3.5, 5, DK)
    _wellipse(c, kx - 3, ky, 1.2, 5, HZ3)
    # Мох у корней.
    for _ in range(60):
        mx = x + rng.uniform(-w * 0.75, w * 0.4)
        my = rng.uniform(y1 - 34, y1 - 1)
        if c.get(int(mx) % c.w, int(my)) in (HZ3, L4):
            _wset(c, mx, int(my), T2 if rng.random() < 0.6 else MO)
            _wset(c, mx + 1, int(my), MO)


def _rope(c, x, w, y):
    """Соломенный канат симэнава на стволе с бумажными молниями сидэ."""
    for dx in range(int(-w), int(w) + 1):
        sag = int(round(2.5 * (1 - (dx / float(w)) ** 2)))
        _wset(c, x + dx, y + sag, FL1 if dx % 3 else L1)
        _wset(c, x + dx, y + sag + 1, HZ0 if dx % 3 else L1)
        _wset(c, x + dx, y + sag + 2, HZ2)
    for dx in (-w * 0.55, 0, w * 0.55):
        sx = int(x + dx)
        sy = y + int(round(2.5 * (1 - (dx / float(w)) ** 2))) + 3
        for j in range(9):
            off = (0, 0, 0, 2, 2, 2, 0, 0, 0)[j]
            c.rect(sx + off, sy + j, sx + off + 2, sy + j, HZ0 if j % 3 else FL1)


def par3_trees():
    """Большие деревья, 512×277, прозрачно между ними: два старых клёна (на одном канат
    симэнава) и два куста бамбука, стволы расходятся к земле, красная крона наверху сплошной
    полосой, из-под неё свисают бумажные фонари."""
    rng = random.Random(342)
    c = Canvas(512, 277)
    # Бамбук позади клёнов.
    for x, w, top in ((176, 9, 30), (192, 6, 30), (206, 7, 30), (430, 6, 30), (444, 10, 30), (464, 7, 30), (118, 5, 30)):
        _bamboo(c, rng, x, w, top, 264, (T0, T1, T2, MO))
        # Молодой побег у подножия.
        c.rect(x - 1, 258, x + w, 263, T2)
    # Клёны.
    _maple_trunk(c, rng, 56, 30, 30, 264, 0.6)
    _maple_trunk(c, rng, 318, 38, 30, 264, -0.5)
    _rope(c, 318, 16, 168)
    # Сучья уходят в крону.
    for tx, lean, k, dx, top, t, sag in ((56, 0.6, 0.36, 46, 60, 7, 9), (56, 0.6, 0.27, -40, 58, 6, 7),
                                         (318, -0.5, 0.4, 52, 62, 8, 10), (318, -0.5, 0.3, -44, 58, 7, 8)):
        x0 = _trunk_x(tx, k, lean)
        _bough(c, x0, 30 + 234 * k, x0 + dx, top, t, sag)
    # Крона: сверху тёмная, ниже ярче; нижний ряд висит впереди.
    c.rect(0, 0, 511, 22, L4)
    for x in range(0, 512, 27):
        _maple(c, rng, x + rng.uniform(-6, 6), rng.uniform(4, 12), rng.uniform(22, 28), (L2, L3, L4, DK), 0.75)
    for x in range(0, 512, 25):
        _maple(c, rng, x + rng.uniform(-6, 6), rng.uniform(22, 34), rng.uniform(21, 28), (L1, L2, L3, L4), 0.75)
    for x in range(0, 512, 31):
        _maple(c, rng, x + rng.uniform(-6, 6), rng.uniform(42, 56), rng.uniform(19, 27), (L0, L1, L2, L3), 0.72)
    # Фонари на нитях.
    for x, length, small in ((30, 52, False), (108, 30, True), (150, 66, False), (246, 44, False), (280, 24, True),
                             (392, 58, False), (410, 34, True), (492, 46, False)):
        top = 60
        c.rect(x, top, x, top + length, DK)
        _lantern(c, x, top + length, small)
    # Листья падают.
    for _ in range(26):
        x = rng.uniform(0, 512)
        y = rng.uniform(86, 250)
        if all(c.get(int(x + dx) % 512, int(y + dy)) is None for dx in (-3, 0, 3) for dy in (-3, 0, 2)):
            _leaf(c, x, y, L1 if rng.random() < 0.5 else L2, L3)
    return c


def _stone_lantern(c, x, base):
    """Каменный фонарь исидоро в сумерках: (x, base) середина подножия. В окошке огонь."""
    c.rect(x - 6, base - 3, x + 6, base, HZ3)
    c.rect(x - 4, base - 5, x + 4, base - 4, HZ2)
    c.rect(x - 2, base - 17, x + 2, base - 6, HZ2)
    c.rect(x - 2, base - 17, x - 2, base - 6, HZ1)
    c.rect(x + 2, base - 17, x + 2, base - 6, HZ3)
    c.rect(x - 6, base - 20, x + 6, base - 18, HZ2)
    c.rect(x - 6, base - 20, x + 6, base - 20, HZ1)
    c.rect(x - 5, base - 28, x + 5, base - 21, HZ2)
    c.rect(x + 4, base - 28, x + 5, base - 21, HZ3)
    c.rect(x - 2, base - 27, x + 2, base - 22, FL1)
    c.rect(x, base - 27, x, base - 22, L1)
    c.rect(x - 2, base - 25, x + 2, base - 25, L1)
    # Крыша с загнутыми углами и навершие.
    for j, half in enumerate((10, 8, 6, 4)):
        c.rect(x - half, base - 29 - j, x + half, base - 29 - j, HZ3 if j == 0 else HZ2)
        c.set(x - half, base - 29 - j, HZ1)
    c.set(x - 11, base - 30, HZ3)
    c.set(x + 11, base - 30, HZ3)
    c.rect(x - 1, base - 36, x + 1, base - 33, HZ2)
    c.set(x - 1, base - 36, HZ1)
    # Мох на крыше.
    for dx in (-7, -3, 2, 5):
        c.set(x + dx, base - 30 - (1 if abs(dx) < 6 else 0), T2)


def _azalea(c, rng, cx, cy, r):
    """Стриженая азалия подушкой с цветами."""
    ry = r * 0.72
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx = (x - cx) / r
            dy = (y - cy) / ry
            if dx * dx + dy * dy > 1.0:
                continue
            k = -dx * 0.5 - dy * 0.9
            _wset(c, x, y, T0 if k > 0.72 else (T1 if k > 0.2 else (T2 if k > -0.45 else MO)))
    for _ in range(int(r * r * 0.1)):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(0, 0.85)
        x = cx + math.cos(a) * d * r
        y = cy + math.sin(a) * d * ry
        k = -(x - cx) / r * 0.5 - (y - cy) / ry * 0.9
        _wset(c, x, int(y), T0 if k > 0.3 else (T2 if k > -0.2 else MO))
        _wset(c, x + 1, int(y), T1 if k > 0.3 else MO)
    for _ in range(int(r * 0.9)):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(0, 0.75)
        x = cx + math.cos(a) * d * r
        y = int(cy + math.sin(a) * d * ry - ry * 0.12)
        _wset(c, x, y, FL2)
        _wset(c, x + 1, y, FL2)
        _wset(c, x, y - 1, FL2)
        _wset(c, x + 1, y - 1, FL1)


def par3_bushes():
    """Яркая поросль у земли, 512×120, прозрачный верх: стриженые азалии в цвету, побеги
    бамбука, молодые клёны и два каменных фонаря с огнём; низ сплошной."""
    rng = random.Random(343)
    c = Canvas(512, 120)
    lanterns = (92, 366)
    for x in range(0, 512, 15):
        cx = x + rng.uniform(-4, 4)
        if any(abs(cx - lx) < 20 for lx in lanterns):
            continue
        kind = rng.random()
        if kind < 0.24:
            # Побеги бамбука пучком.
            for j in range(rng.randint(2, 3)):
                bx = cx + j * 5 - 5
                top = rng.uniform(36, 64)
                _bamboo(c, rng, bx, 3, top, 96, (T0, T1, T2, MO), twigs=False)
                for s in (-1, 1):
                    for k in range(2):
                        ly = top + 3 + k * 9 + (2 if s > 0 else 0)
                        for i in range(8):
                            _wset(c, bx + 1 + s * i, int(ly + i * 0.7), T0 if i < 5 else T1)
                            if 1 < i < 6:
                                _wset(c, bx + 1 + s * i, int(ly + i * 0.7) + 1, T2)
        elif kind < 0.44:
            # Молодой клён: тонкий ствол и красная шапка.
            top = rng.uniform(52, 68)
            c.rect(int(cx), int(top), int(cx) + 1, 96, L4)
            c.rect(int(cx), int(top), int(cx), 96, HZ3)
            _maple(c, rng, cx, top, rng.uniform(11, 15), (L0, L1, L2, L3), 0.75)
        else:
            _azalea(c, rng, cx, rng.uniform(80, 88), rng.uniform(12, 19))
    for lx in lanterns:
        _stone_lantern(c, lx, 95)
    # Сплошной низ: стриженая изгородь.
    c.rect(0, 92, 511, 119, MO)
    for x in range(0, 512, 9):
        _azalea(c, rng, x + rng.uniform(-2, 2), rng.uniform(96, 101), rng.uniform(7, 11))
    c.rect(0, 108, 511, 119, MO)
    for _ in range(240):
        x = rng.uniform(0, 512)
        y = rng.uniform(104, 119)
        _wset(c, x, int(y), T2 if rng.random() < 0.6 else DK)
    for _ in range(30):
        x = rng.uniform(0, 512)
        y = int(rng.uniform(102, 118))
        _wset(c, x, y, L2)
        _wset(c, x + 1, y, L1)
    # Светлячки.
    for _ in range(40):
        x = rng.uniform(0, 512)
        y = rng.uniform(24, 90)
        if all(c.get(int(x + dx) % 512, int(y + dy)) is None for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            _wset(c, x, int(y), FL1)
    return c


def canopy_front():
    """Кленовая листва над кадром спереди, 256×56, прозрачный низ: тёмные охапки и свисающие
    веточки с листьями."""
    rng = random.Random(344)
    c = Canvas(256, 56)
    c.rect(0, 0, 255, 8, L4)
    for x in range(0, 256, 21):
        _maple(c, rng, x + rng.uniform(-4, 4), rng.uniform(10, 16), rng.uniform(13, 17), (L1, L2, L3, L4), 0.78)
    for x in range(0, 256, 24):
        _maple(c, rng, x + rng.uniform(-4, 4), rng.uniform(0, 4), rng.uniform(14, 18), (L3, L3, L4, DK), 0.8)
    for _ in range(11):
        x = rng.uniform(0, 256)
        n = rng.randint(26, 46)
        for y in range(14, n):
            _wset(c, x + math.sin(y * 0.16) * 1.6, y, DK)
            if y > 22 and y % 7 == 0:
                s = 1 if (y // 7) % 2 else -1
                _leaf(c, x + math.sin(y * 0.16) * 1.6 + s * 3, y, L3 if y % 2 else L2, L4)
        _leaf(c, x + math.sin(n * 0.16) * 1.6, n + 2, L2, L4)
    return c


# --- Передний план -----------------------------------------------------------------------------

def trail_soil():
    """Кладка исигаки, 64×64 по кругу в обе стороны: крупные камни неправильной формы подогнаны
    вплотную, свет сверху слева, тёмные швы, в швах мох."""
    rng = random.Random(351)
    n = 64
    c = Canvas(n, n)
    seeds = []
    for gy in range(4):
        for gx in range(4):
            seeds.append((gx * 16 + 8 + rng.uniform(-5, 5) + (gy % 2) * 6, gy * 16 + 8 + rng.uniform(-4.5, 4.5),
                          rng.uniform(0.62, 0.8)))
    for _ in range(5):
        seeds.append((rng.uniform(0, n), rng.uniform(0, n), rng.uniform(1.15, 1.5)))

    def dist(x, y, s):
        dx = (x - s[0] + n / 2.0) % n - n / 2.0
        dy = (y - s[1] + n / 2.0) % n - n / 2.0
        return math.hypot(dx * s[2], dy) * (1.0 if s[2] < 1 else 1.25), dx, dy

    for y in range(n):
        for x in range(n):
            near = sorted((dist(x, y, s) + (i,) for i, s in enumerate(seeds)))
            d1, dx, dy, i1 = near[0]
            gap = near[1][0] - d1
            if gap < 1.25:
                c.set(x, y, S4)
                continue
            k = -dx * 0.45 - dy * 0.9
            col = S0 if k > 2.2 else (S1 if k > -1.6 else (S2 if k > -4.5 else S3))
            if gap < 2.9:
                # Фаска у шва: сверху и слева светлая, снизу и справа тёмная.
                col = S0 if k > 0.6 else S3
            c.set(x, y, col)
    # Щербины, сколы и мох в швах.
    for _ in range(46):
        x, y = rng.randrange(n), rng.randrange(n)
        cur = c.get(x, y)
        if cur == S1:
            c.set(x, y, S2)
            c.set((x + 1) % n, y, S2)
        elif cur == S0:
            c.set(x, y, S1)
    for _ in range(9):
        x, y = rng.randrange(n), rng.randrange(n)
        for k in range(rng.randint(3, 5)):
            if c.get((x + k) % n, (y + k // 2) % n) in (S0, S1, S2):
                c.set((x + k) % n, (y + k // 2) % n, S3)
    for y in range(n):
        for x in range(n):
            if c.get(x, y) == S4 and rng.random() < 0.09:
                c.set(x, y, G3)
                if rng.random() < 0.5:
                    c.set(x, (y - 1) % n, G2)
    return c


def trail_edge():
    """Кромка мха, 32×18 по кругу: поверхность на строке 4, над ней травинки и опавшие кленовые
    листья, мох подушками свисает на кладку; ниже прозрачно, там грунт."""
    rng = random.Random(352)
    c = Canvas(32, 18)
    top = 4
    for x in range(32):
        # Подушки шириной 8: край фестонами.
        u = (x % 8 - 3.5) / 4.0
        hang = top + 4 + int(round(3.2 * math.sqrt(max(0.0, 1.0 - u * u)) + rng.uniform(0, 1.2)))
        c.rect(x, top, x, hang, G1)
        c.set(x, top, G0)
        if (x * 3) % 5 < 2:
            c.set(x, top + 1, G0)
        if (x + 1) % 4 == 0:
            c.set(x, top + 3, G2)
        c.set(x, hang - 1, G2)
        c.set(x, hang, G3)
        c.set(x, hang + 1, FK if x % 8 in (0, 7) else G3)
        if rng.random() < 0.4:
            h = rng.randint(1, 3)
            c.rect(x, top - h, x, top - 1, G1 if rng.random() < 0.5 else G0)
    # Опавшие листья лежат на мху, лепесток рядом.
    for x, col in ((5, W1), (17, W0), (26, W1)):
        c.set(x, top - 1, col)
        c.set(x + 1, top - 1, col)
        c.set(x + 1, top, W2)
        c.set(x + 2, top, col)
    c.set(11, top, PINK)
    c.set(22, top + 1, PINK)
    return c


def arch_bark():
    """Брус арки, 32×32 по кругу: красный лаковый брус в четыре доски, волокна и потёртости,
    поперёк кованая полоса с заклёпками."""
    rng = random.Random(353)
    c = Canvas(32, 32)
    for y in range(32):
        for x in range(32):
            k = x % 8
            c.set(x, y, W2 if k == 0 else (W0 if k == 1 else (W2 if k == 7 and y % 5 else W1)))
    # Волокна и потёртости лака.
    for _ in range(26):
        x = rng.randrange(32)
        if x % 8 in (0, 1):
            continue
        y = rng.randrange(32)
        for k in range(rng.randint(3, 8)):
            c.set(x, (y + k) % 32, W2)
    for _ in range(12):
        x = rng.randrange(32)
        if x % 8 in (0, 7):
            continue
        y = rng.randrange(32)
        for k in range(rng.randint(2, 4)):
            c.set(x, (y + k) % 32, W0)
    # Кованая полоса.
    for x in range(32):
        c.set(x, 12, ST1)
        c.rect(x, 13, x, 17, S3)
        c.set(x, 18, FK)
        c.set(x, 19, W2)
        if x % 8 == 4:
            c.rect(x - 1, 14, x, 15, ST0)
            c.set(x, 16, ST1)
            c.set(x + 1, 15, ST1)
    return c


def _blade(c, x, h, bend, col, side, tip=None):
    for j in range(int(h)):
        k = j / h
        c.set(x + bend * k * k, c.h - 1 - j, col)
        if k < 0.55:
            c.set(x + bend * k * k + 1, c.h - 1 - j, side)
    if tip is not None:
        # Метёлка сусуки: клонится по ветру.
        s = 1 if bend >= 0 else -1
        ty = c.h - int(h)
        for k in range(5):
            c.set(x + bend + s * k, ty + k // 2 - 1, tip)
            if k in (1, 2, 3):
                c.set(x + bend + s * k, ty + k // 2, tip if k < 3 else ST1)


def dec_grass(i):
    """Высокая трава сусуки перед героем, 32×24, два кадра качания; у части стеблей светлая
    метёлка."""
    rng = random.Random(361)
    c = Canvas(32, 24)
    for _ in range(15):
        x = rng.uniform(4, 28)
        col = rng.choice((G1, G2, G1, G0))
        tip = ST0 if rng.random() < 0.4 else None
        h = rng.uniform(9, 21)
        _blade(c, x, h, rng.uniform(-3, 3) + (1.5 if i else -0.5), col, G3 if col == G2 else G2, tip)
    return c


def dec_tuft(i):
    """Кочка травы, 32×14, два кадра качания; у корней лежат кленовые листья."""
    rng = random.Random(362)
    c = Canvas(32, 14)
    for _ in range(10):
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 11), rng.uniform(-2, 2) + (1 if i else 0), rng.choice((G0, G1, G2)), G3)
    for x, col in ((8, W1), (21, W0)):
        c.set(x, 13, col)
        c.set(x + 1, 13, col)
        c.set(x + 1, 12, col)
        c.set(x + 2, 13, W2)
    return c


def dec_fern():
    """Куст низкого бамбука саса за героем, 48×32: широкие острые листья веером из одной точки,
    светлая жилка посередине, крайние клонятся к земле."""
    c = Canvas(48, 32)
    for ang, length, w, droop in ((-170, 16, 3.0, 0.045), (-18, 18, 3.2, -0.05), (-142, 23, 3.8, 0.028),
                                  (-48, 25, 4.0, -0.03), (-112, 27, 4.2, 0.012), (-76, 22, 3.8, -0.012)):
        a = math.radians(ang)
        px, py = 24.0, 30.0
        for j in range(length):
            k = j / float(length)
            a -= droop
            px += math.cos(a)
            py += math.sin(a)
            # Лист: узкий у черешка, шире всего на трети, остриё на конце.
            half = w * (math.sin(min(1.0, k / 0.38) * math.pi / 2) if k < 0.38 else (1.0 - (k - 0.38) / 0.62) ** 0.8)
            half = max(half, 0.35)
            nx, ny = -math.sin(a), math.cos(a)
            for d in range(int(-half * 2), int(half * 2) + 1):
                u = d / 2.0
                # Сторона к свету (верх и лево) светлая, другая в тени.
                lit = (nx * u * -0.5 + ny * u * -0.9) > 0
                c.set(px + nx * u, py + ny * u, G1 if lit else G2)
            c.set(px, py, G0 if k < 0.85 else G1)
            if j % 5 == 4 and half > 1.4:
                c.set(px + nx * half * 0.6, py + ny * half * 0.6, G3 if ny * half > 0 or nx > 0 else G2)
    c.rect(19, 30, 29, 31, G3)
    c.rect(21, 29, 27, 29, G2)
    c.outline(FK)
    return c


def dec_bush():
    """Стриженые азалии за героем, 64×36: четыре подушки разной высоты в цвету, у земли тень."""
    rng = random.Random(364)
    c = Canvas(64, 36)
    for cx, cy, r in ((9, 27, 8), (53, 25, 10), (22, 21, 13), (39, 18, 15)):
        ry = r * 0.85
        for y in range(int(cy - ry - 1), 34):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                dx = (x - cx) / r
                dy = min(0.0, (y - cy) / ry)
                if dx * dx + dy * dy > 1.0:
                    continue
                k = -dx * 0.5 - (y - cy) / ry * 0.9
                c.set(x, y, G0 if k > 0.78 else (G1 if k > 0.25 else (G2 if k > -0.5 else G3)))
        # Листва крапом, чтобы подушка не была гладкой.
        for _ in range(int(r * r * 0.12)):
            x = int(cx + rng.uniform(-r * 0.8, r * 0.8))
            y = int(cy + rng.uniform(-ry * 0.75, 6))
            cur = c.get(x, y)
            if cur == G1:
                c.set(x, y, G0 if rng.random() < 0.5 else G2)
            elif cur == G2:
                c.set(x, y, G3 if rng.random() < 0.6 else G1)
        # Цветы горстями.
        for _ in range(int(r * 0.7)):
            a = rng.uniform(3.3, 6.1)
            d = rng.uniform(0.15, 0.8)
            x = int(cx + math.cos(a) * d * r)
            y = int(cy + math.sin(a) * d * ry)
            c.set(x, y, PINK)
            c.set(x + 1, y, PINK)
            c.set(x, y + 1, W0)
            c.set(x + 1, y - 1, PINK if rng.random() < 0.5 else ST0)
    c.rect(2, 33, 61, 35, G3)
    for x in range(2, 62):
        if rng.random() < 0.3:
            c.set(x, 34, G2)
    c.outline(FK)
    return c


def dec_rock():
    """Садовый валун под шапкой мха и пирамидка из плоских камней рядом, 32×20."""
    c = Canvas(32, 20)
    c.poly([(2, 19), (1, 13), (5, 7), (11, 4), (17, 6), (20, 12), (20, 19)], ST1)
    c.poly([(3, 13), (6, 8), (11, 6), (14, 8), (11, 12), (6, 14)], ST0)
    c.line(13, 12, 16, 17, S2, 1)
    c.line(7, 16, 10, 17, S2, 1)
    c.rect(15, 17, 19, 19, S2)
    # Мох шапкой сверху.
    c.poly([(5, 7), (11, 4), (17, 6), (18, 8), (13, 7), (8, 8)], G1)
    c.rect(8, 5, 12, 5, G0)
    c.set(15, 8, G2)
    c.set(17, 9, G2)
    c.set(6, 9, G2)
    # Пирамидка: три плоских камня.
    c.ellipse(26, 17.5, 4.4, 1.9, ST1)
    c.rect(23, 16, 27, 16, ST0)
    c.ellipse(26, 13.5, 3.2, 1.6, S1)
    c.rect(24, 12, 26, 12, S0)
    c.ellipse(26, 10, 2.2, 1.4, ST1)
    c.rect(25, 9, 26, 9, ST0)
    c.outline(FK)
    # Обводка между камнями пирамидки.
    c.rect(23, 15, 28, 15, FK)
    c.rect(24, 11, 28, 11, FK)
    c.rect(22, 19, 30, 19, G3)
    c.set(1, 19, G2)
    return c


def dec_flowers():
    """Паучьи лилии хиганбана среди травы, 32×20: красные цветы с загнутыми тычинками на голых
    стеблях."""
    rng = random.Random(365)
    c = Canvas(32, 20)
    for _ in range(9):
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 8), rng.uniform(-2, 2), rng.choice((G1, G2)), G3)
    for x, y in ((6, 8), (14, 5), (22, 9), (27, 5)):
        c.line(x, y + 1, x, 19, G2, 1)
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (-2, -1), (2, -1), (-1, 1), (1, 1)):
            c.set(x + dx, y + dy, W1)
        for dx, dy in ((-3, -2), (3, -2), (-1, -2), (1, -2), (-3, 0), (3, 0)):
            c.set(x + dx, y + dy, W0)
        c.set(x, y - 3, PINK)
        c.set(x - 4, y - 3, PINK)
        c.set(x + 4, y - 3, PINK)
        c.set(x, y, W0)
    return c


def dec_mush():
    """Два придорожных каменных дзидзо в красных нагрудниках, 32×16: большой и малый, у ног
    мох."""
    c = Canvas(32, 16)
    for x, top, r, w in ((11, 1, 3, 4), (23, 6, 2, 3)):
        hy = top + r
        # Тело столбиком со скруглёнными плечами.
        c.rect(x - w, hy + r + 1, x + w, 15, ST1)
        c.rect(x - w + 1, hy + r, x + w - 1, hy + r, ST1)
        c.rect(x - w, hy + r + 1, x - w + 1, 15, ST0)
        c.rect(x + w, hy + r + 3, x + w, 15, S1)
        # Голова.
        c.ellipse(x, hy, r, r, ST0)
        c.rect(x + r - 1, hy, x + r, hy + 1, ST1)
        # Нагрудник.
        c.rect(x - w + 1, hy + r, x + w - 1, hy + r + 2, W1)
        c.rect(x - w + 2, hy + r + 3, x + w - 2, hy + r + 3, W1)
        c.rect(x - w + 1, hy + r, x - w + 2, hy + r, W0)
        c.set(x, hy + r + 3, W2)
    c.rect(4, 15, 17, 15, G2)
    c.rect(19, 15, 28, 15, G2)
    c.set(6, 14, G1)
    c.set(16, 14, G1)
    c.set(27, 14, G1)
    c.outline(FK)
    # Лица: закрытые глаза чёрточками.
    c.set(10, 4, FK)
    c.set(12, 4, FK)
    c.set(11, 6, S2)
    c.set(22, 8, FK)
    c.set(24, 8, FK)
    return c


# --- Враги (палитра спрайтов) ------------------------------------------------------------------

def crab(i):
    """Ползун тропы: жаба анфас, четыре кадра (приседает, горло раздувается, лапы переступают).
    Рисунок из основы сеттинга, обводка красная: опасна, убить нельзя."""
    return ninja16.toad(i)


def drone(i):
    """Летун тропы: ворон-тэнгу с длинным красным клювом летит вправо, крылья машут (вверх,
    середина, вниз, середина), тело по центру кадра. Рисунок из основы сеттинга."""
    return ninja16.raven(i)


def sprites():
    """Ленты этой демки в палитре спрайтов (ленты героя в `ninja16.sprites`)."""
    return {
        "crab_walk": strip([crab(i) for i in range(4)]),
        "parrot_fly": strip([drone(i) for i in range(4)]),
    }


def backdrop():
    """Слои фона и листва над кадром в палитре фона `NINJA_BG`."""
    return {"par3_back": par3_back(), "par3_trees": par3_trees(), "par3_bushes": par3_bushes(),
            "canopy_front": canopy_front()}


def foreground():
    """Земля, арка, украшения в палитре переднего плана `NINJA_FG`."""
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


def preview(path, scale=2, limit=1500):
    """Лист набора; выше `limit` пикселей делится на файлы с суффиксами _b, _c."""
    items = ninja16.shaded(sprites())
    for key, canvas in foreground().items():
        items[key] = (canvas, NINJA_FG)
    for key, canvas in backdrop().items():
        items[key] = (canvas, NINJA_BG)
    pad = 6
    pages = [{}]
    height = pad * scale
    for key, item in items.items():
        h = (item[0].h + pad) * scale
        if pages[-1] and height + h > limit:
            pages.append({})
            height = pad * scale
        pages[-1][key] = item
        height += h
    stem, ext = os.path.splitext(path)
    for i, page in enumerate(pages):
        ninja16.save_sheet(path if i == 0 else "%s_%s%s" % (stem, "bcdefgh"[i - 1], ext), page, scale=scale, pad=pad)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
