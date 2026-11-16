#!/usr/bin/env python3
"""Набор «Замки» для гонки × 16/32-bit «псевдо-3D» (#137), зеркало `space_road16.py` и
`pixel_road16.py`: те же ключи, размеры холстов и порядок кадров, чтобы `racing_bit16.gd` брала
их без правок. Герой едет на боевой повозке (вид сзади): дощатый борт с окованными зубцами по
углам, щит с гербом, связка копий и раздвоенный вымпел, на облучке рыцарь в ведёрном шлеме с
красным плюмажем. Соперники на повозках чужих гербов: тёмный окованный короб под полосатым
шатром, в проёме стражник в железной шляпе, сбоку алебарда и хоругвь. У дороги дуб и ель вместо
пальм, сторожевая башня с воротами вместо хижины, замшелый валун, стог сена с вилами,
указатели-стрелки на столбе. На горизонте дневное небо с кучевыми облаками, синие горы и
зелёные холмы с замком, мельницей и дозорной башней, луга с изгородями и рекой вместо моря.
Дорога из брусчатки, обочина трава.

Повозки и пропы в палитре `castles16.PALETTE`, горизонт в своей (`CASTLES_SKY`), цвета дороги
лентой `road_colors` по местам `ROAD_COLORS`.

    python3 tools/castles_road16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import castles16  # noqa: E402
from castles16 import (Canvas, strip, K, SEA, WHITE, GREY, TAN, GOLD, BRASS, METAL, DARK, RED,  # noqa: E402
                       VIOLET, PLUM)

# Палитра горизонта: небо, облака, луга, горы и холмы с замком. Места те же по смыслу, что у
# пиратов и космоса.
S0, S1, S2, S3, C0, C1, C2, M0, M1, M2, M3, I0, I1, I2, I3, SUN = range(16)
CASTLES_SKY = [
    (0x38, 0x66, 0xBC),  # S0  небо наверху
    (0x56, 0x88, 0xD2),  # S1
    (0x86, 0xB4, 0xE6),  # S2  небо, вода реки
    (0xC6, 0xE2, 0xF2),  # S3  небо у горизонта
    (0xAE, 0xBC, 0xD8),  # C0  тень облака, тень камня
    (0xE2, 0xE8, 0xF2),  # C1  облако
    (0xFF, 0xFD, 0xF2),  # C2  свет облака, солнце, снег
    (0x4C, 0x8C, 0x5C),  # M0  луг вдали
    (0x56, 0xA0, 0x4C),  # M1  луг
    (0x64, 0xAE, 0x4A),  # M2  луг у дороги
    (0x2C, 0x68, 0x40),  # M3  изгороди, ельник
    (0x7C, 0x9E, 0xCE),  # I0  горы в дымке
    (0x3C, 0x7C, 0x56),  # I1  холмы
    (0xCC, 0xCE, 0xD6),  # I2  камень замка
    (0xC8, 0x3A, 0x32),  # I3  шатры башен, флаги
    (0x74, 0xBE, 0x50),  # SUN трава у кромки дороги
]

# Цвета дороги по местам ленты `road_colors` (демка берёт их по индексу).
ROAD_COLORS = [
    (0xA8, 0x9C, 0x8A),  # 0 брусчатка светлая
    (0x9A, 0x8E, 0x7E),  # 1 брусчатка тёмная
    (0x34, 0x58, 0xB0),  # 2 бордюр синий (турнирная ограда)
    (0xF2, 0xEE, 0xE0),  # 3 бордюр белый
    (0xEC, 0xE2, 0xC4),  # 4 разметка: светлый камень
    (0x74, 0xBE, 0x50),  # 5 трава светлая
    (0x66, 0xB0, 0x46),  # 6 трава тёмная
    (0xC6, 0xE2, 0xF2),  # 7 дымка вдали
]


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wellipse(c, cx, cy, rx, ry, col):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                _wset(c, x, y, col)


# --- Горизонт ----------------------------------------------------------------------------------

def _cloud(c, cx, base, lumps):
    """Кучевое облако с плоским низом: `lumps` это (сдвиг, радиус) шапок; свет сверху слева,
    тень полосой по низу."""
    for dx, r in lumps:
        for y in range(base - r, base + 1):
            half = math.sqrt(max(0.0, r * r - (base - y) ** 2)) * 1.35
            for x in range(int(cx + dx - half), int(cx + dx + half) + 1):
                _wset(c, x, y, C1)
    for dx, r in lumps:
        for y in range(base - r, base - int(r * 0.45)):
            half = math.sqrt(max(0.0, r * r - (base - y) ** 2)) * 1.35
            for x in range(int(cx + dx - half), int(cx + dx + half * 0.5)):
                _wset(c, x, y, C2)
    lo = min(dx - r * 1.35 for dx, r in lumps)
    hi = max(dx + r * 1.35 for dx, r in lumps)
    for x in range(int(cx + lo), int(cx + hi) + 1):
        for y in (base - 1, base):
            if c.px[y][x % c.w] in (C1, C2):
                _wset(c, x, y, C0)
        if c.px[base - 2][x % c.w] == C1 and x % 2 == 0:
            _wset(c, x, base - 2, C0)


def sky():
    """Небо, 512×128, стыкуется по краям: синева наверху, светлая дымка у горизонта, солнце с
    ореолом, кучевые облака с плоским низом, стая птиц."""
    rng = random.Random(271)
    c = Canvas(512, 128)
    bands = [(0, S0), (36, S1), (70, S2), (100, S3)]
    for y in range(128):
        col = S0
        for start, b in bands:
            if y >= start:
                col = b
        for x in range(512):
            px = col
            for i, (start, b) in enumerate(bands[1:]):
                if start <= y < start + 3 and (x + y) % 2 == 0:
                    px = bands[i][1]
            c.set(x, y, px)
    # Солнце: диск и ореол через пиксель.
    sx, sy = 420, 30
    for y in range(sy - 18, sy + 19):
        for x in range(sx - 18, sx + 19):
            d = math.hypot(x - sx, y - sy)
            if d <= 10:
                c.set(x, y, C2)
            elif d <= 13 and (x + y) % 2 == 0:
                c.set(x, y, C2)
            elif d <= 17 and (x + y) % 2 == 0 and (x - y) % 4 == 0:
                c.set(x, y, S2)
    # Облака: три больших, остальные мелкие и ближе к горизонту.
    _cloud(c, 92, 58, ((-26, 10), (-8, 17), (14, 13), (32, 8)))
    _cloud(c, 262, 40, ((-20, 9), (0, 14), (20, 10)))
    _cloud(c, 486, 76, ((-22, 8), (-4, 13), (16, 10), (34, 6)))
    _cloud(c, 338, 88, ((-12, 5), (2, 8), (16, 5)))
    _cloud(c, 176, 96, ((-10, 4), (2, 6), (14, 4)))
    _cloud(c, 20, 104, ((-8, 3), (2, 5), (12, 3)))
    for _ in range(9):
        x = rng.randint(0, 511)
        y = rng.randint(104, 122)
        for i in range(rng.randint(8, 22)):
            _wset(c, x + i, y, C1)
    # Стая птиц галочками.
    for bx, by in ((196, 84), (207, 79), (216, 88), (227, 82), (187, 92)):
        for i in range(3):
            _wset(c, bx - i, by - i if i < 2 else by - 1, S0)
            _wset(c, bx + i, by - i if i < 2 else by - 1, S0)
    return c


def _ridge(x):
    """Высота синих гор, период 512."""
    a = x * math.pi * 2 / 512.0
    return 15 + 7 * math.sin(a * 3 + 1.0) + 4 * math.sin(a * 7 + 2.0) + 4 * abs(math.sin(a * 13 + 0.4))


def _down(x):
    """Высота зелёных холмов, период 512: главный холм под замком у x = 300."""
    a = x * math.pi * 2 / 512.0
    return 7 + 3 * math.sin(a * 2 + 0.5) + 2 * math.sin(a * 5 + 1.7) + 7 * math.exp(-((x - 300) / 46.0) ** 2)


def _far_tower(c, x0, x1, top, bottom, roof):
    """Башня замка на горизонте: свет слева, тень справа, шатёр или зубцы, бойница."""
    for y in range(top, bottom + 1):
        for x in range(x0, x1 + 1):
            _wset(c, x, y, I2)
        _wset(c, x0, y, C2)
        _wset(c, x1, y, C0)
        if x1 - x0 >= 5:
            _wset(c, x1 - 1, y, C0)
    mid = (x0 + x1) // 2
    if roof:
        for i in range(roof):
            half = (x1 - x0) / 2.0 + 1 - (i * ((x1 - x0) / 2.0 + 1) / roof)
            for x in range(int(mid - half + 0.5), int(mid + half + 0.5) + 1):
                _wset(c, x, top - 1 - i, I3)
        _wset(c, mid, top - roof - 1, I3)
    else:
        for x in range(x0, x1 + 1, 2):
            _wset(c, x, top - 1, I2)
    _wset(c, mid, top + 2, M3)
    _wset(c, mid, top + 3, M3)


def islands():
    """Горы и холмы на горизонте, 512×40, прозрачный верх: синие горы в дымке со снегом,
    зелёные холмы с ельником, на главном холме замок с шатрами башен и флагом, на соседних
    дозорная башня и мельница."""
    c = Canvas(512, 40)
    for x in range(512):
        h = _ridge(x)
        top = 39 - int(h)
        for y in range(top, 40):
            c.set(x, y, I0)
        if _ridge(x + 1) > h:
            c.set(x, top, C0)
            c.set(x, top + 1, C0)
        if h > 23:
            c.set(x, top, C2)
            if h > 25:
                c.set(x, top + 1, C2)
    # Замок рисуется до холма: холм закрывает подошву стен.
    b = 39 - int(_down(300))
    for y in range(b - 6, b + 5):
        for x in range(272, 329):
            c.set(x, y, I2 if y > b - 6 else C2)
    for x in range(272, 329, 3):
        c.set(x, b - 7, I2)
        c.set(x + 1, b - 7, I2)
    for x in range(276, 326, 6):
        c.set(x, b - 3, C0)
        c.set(x + 3, b - 1, C0)
    for y in range(b - 3, b + 5):
        for x in (299, 300, 301):
            c.set(x, y, M3)
    c.set(300, b - 4, M3)
    _far_tower(c, 292, 308, b - 14, b - 7, 6)
    _far_tower(c, 266, 273, b - 12, b + 4, 5)
    _far_tower(c, 327, 334, b - 11, b + 4, 5)
    _far_tower(c, 283, 287, b - 9, b - 6, 0)
    _far_tower(c, 313, 317, b - 9, b - 6, 0)
    for y in range(b - 25, b - 20):
        c.set(300, y, M3)
    for x in (301, 302, 303):
        c.set(x, b - 25, I3)
        c.set(x, b - 24, I3)
    # Дозорная башня и мельница на соседних холмах.
    b2 = 39 - int(_down(96))
    _far_tower(c, 93, 98, b2 - 9, b2 + 4, 4)
    b3 = 39 - int(_down(438))
    for y in range(b3 - 7, b3 + 4):
        for x in range(436, 441):
            c.set(x, y, I2)
        c.set(440, y, C0)
    for i in range(3):
        for x in range(436 + i, 441 - i):
            c.set(x, b3 - 8 - i, I3)
    for i in range(-6, 7):
        c.set(438 + i, b3 - 7 + i, C2)
        c.set(438 + i, b3 - 7 - i, C2)
    # Холмы: светлая кромка, тень склона через пиксель, ельник по гребням.
    for x in range(512):
        h = _down(x)
        top = 39 - int(h)
        for y in range(top, 40):
            c.set(x, y, I1)
        c.set(x, top, M1)
        if _down(x + 1) > h or (x * 7) % 5 == 0:
            c.set(x, top + 1, M1)
        for y in range(top + 3, 40):
            if (x + y) % 2 == 0 and (y > top + 6 or _down(x + 1) < h):
                c.set(x, y, M3)
    for x in (14, 20, 27, 52, 60, 118, 126, 133, 160, 168, 204, 212, 220, 236, 352, 360, 367, 392, 400, 470, 478,
              486, 502):
        top = 39 - int(_down(x))
        for r in range(6):
            for dx in range(-(r // 2), r // 2 + 1):
                _wset(c, x + dx, top - 5 + r, M3)
    return c


def sea():
    """Луга от горизонта, 512×24: тёмные вдали, светлее у дороги; изгороди полосами, река
    петлёй с бликами, домики под красными крышами и овцы точками, у нижней кромки полоса травы
    обочины."""
    rng = random.Random(273)
    c = Canvas(512, 24)
    for y in range(24):
        col = M0 if y < 5 else (M1 if y < 15 else M2)
        c.rect(0, y, 511, y, col)
        if y in (5, 15):
            for x in range(0, 512, 2):
                c.set(x + (y % 2), y, M0 if y == 5 else M1)
    c.rect(0, 22, 511, 23, SUN)
    # Изгороди: чем ближе, тем длиннее; под ближними светлая полоска скошенного луга.
    for _ in range(40):
        y = rng.randint(1, 20)
        x = rng.uniform(0, 512)
        w = rng.randint(5, 9) + y * 2
        for i in range(w):
            _wset(c, x + i, y, M3)
        if y > 8:
            for i in range(2, w - 2):
                _wset(c, x + i, y + 1, SUN if y > 14 else M2)
    # Река: от горизонта к дороге, шире к низу.
    for y in range(2, 22):
        x = 196 + 46 * math.sin(y / 4.2) + y * 1.5
        w = 1 + y // 3
        for i in range(-w, w + 1):
            _wset(c, x + i, y, S1 if i == w or y < 4 else S2)
        if y % 3 == 0:
            _wset(c, x - w // 2, y, C2)
            _wset(c, x - w // 2 + 1, y, C2)
    # Домики, рощицы и овцы.
    for x, y in ((40, 6), (120, 9), (330, 7), (452, 10), (270, 12)):
        c.rect(x, y, x + 3, y + 1, I2)
        c.rect(x - 1, y - 1, x + 4, y - 1, I3)
        c.rect(x, y - 2, x + 3, y - 2, I3)
        c.set(x + 3, y + 1, C0)
    for _ in range(22):
        x = rng.uniform(0, 512)
        y = rng.randint(3, 19)
        _wset(c, x, y, M3)
        _wset(c, x + 1, y, M3)
        _wset(c, x, y - 1, M3)
    for _ in range(14):
        x = rng.uniform(0, 512)
        y = rng.randint(12, 20)
        _wset(c, x, y, C2)
        _wset(c, x + 1, y, C1)
    return c


# --- Повозки (палитра спрайтов) ------------------------------------------------------------------

def _wheel(c, cx, cy, r, phase, side, rim, tyre, band):
    """Колесо сзади: узкий высокий обод со скруглёнными концами, по середине шина, поперёк
    скобы, которые бегут вниз (`phase` 0..1); наружу торчит ступица (`side` −1 влево, 1 вправо)."""
    cx = int(round(cx))
    c.rect(cx - 5, cy - r + 3, cx + 5, cy + r - 3, rim)
    c.rect(cx - 3, cy - r, cx + 3, cy + r, rim)
    c.rect(cx - 2, cy - r, cx + 2, cy + r, tyre)
    c.rect(cx - 2, cy - r + 1, cx - 2, cy + r - 1, band)
    step = 8
    off = int(phase * step)
    for y in range(cy - r + 3 + off, cy + r - 4, step):
        c.rect(cx - 5, y, cx + 5, y + 1, band)
        c.set(cx - 4, y, GOLD)
        c.set(cx + 4, y, GOLD)
    c.rect(cx + min(side * 6, side * 9), cy - 4, cx + max(side * 6, side * 9), cy + 4, tyre)
    c.rect(cx + min(side * 10, side * 11), cy - 2, cx + max(side * 10, side * 11), cy + 2, band)


def _knight_back(c, x0, phase):
    """Рыцарь со спины по пояс: ведёрный шлем с плоским верхом, красный гребень и хвост
    плюмажа по затылку, стальные наплечники и руки, красный табард с золотым крестом и поясом.
    `x0` левый край корпуса (ширина 16)."""
    # Корпус и ворот.
    c.rect(x0, 23, x0 + 16, 47, RED)
    c.rect(x0 + 2, 21, x0 + 14, 23, GREY)
    c.rect(x0 + 7, 27, x0 + 9, 36, GOLD)
    c.rect(x0 + 4, 30, x0 + 12, 32, GOLD)
    c.rect(x0, 39, x0 + 16, 40, GOLD)
    # Руки в латах разведены к вожжам, наплечники шарами.
    for side in (-1, 1):
        sx = x0 + (-1 if side < 0 else 17)
        c.line(sx, 27, sx + side * 7, 35, GREY, 5)
        c.line(sx + side * 7, 35, sx + side * 4, 44, METAL, 4)
        c.ellipse(sx, 26, 4.5, 4, GREY)
        c.rect(sx - 2, 23, sx + 1, 23, WHITE)
    # Шлем: коробка, обод и шов тёмной сталью, блик слева.
    c.rect(x0 + 1, 6, x0 + 15, 20, GREY)
    c.rect(x0 + 2, 5, x0 + 14, 5, GREY)
    c.rect(x0 + 2, 7, x0 + 3, 16, WHITE)
    c.rect(x0 + 1, 18, x0 + 15, 20, METAL)
    c.rect(x0 + 13, 7, x0 + 14, 17, METAL)
    for y in (9, 13):
        c.set(x0 + 5, y, METAL)
        c.set(x0 + 11, y, METAL)
    # Плюмаж: гребень над шлемом и узкий хвост по затылку, конец качается.
    sway = 1 if phase >= 0.5 else -1
    c.rect(x0 + 5, 2, x0 + 11, 4, RED)
    c.rect(x0 + 7, 1, x0 + 9, 1, RED)
    c.rect(x0 + 7, 5, x0 + 9, 10, RED)
    c.rect(x0 + 7 + sway, 11, x0 + 9 + sway, 14, RED)


def wagon(lean, phase, accent):
    """Боевая повозка со спины, 160×104: два высоких деревянных колеса с железной шиной, дощатый
    задний борт с окованными поясами и щитом цвета `accent`, по углам высокие зубцы с бойницей,
    слева связка копий, справа древко с раздвоенным вымпелом; на облучке рыцарь. `lean` −1..1
    крен на повороте."""
    c = Canvas(160, 104)
    sh = lean * 6
    _wheel(c, 22 + sh * 0.3, 76, 26, phase, -1, BRASS, DARK, METAL)
    _wheel(c, 138 + sh * 0.3, 76, 26, phase, 1, BRASS, DARK, METAL)
    # Ось и подвеска под днищем.
    c.rect(27, 79, 133, 83, BRASS)
    c.rect(27, 84, 133, 85, DARK)
    c.rect(40, 86, 120, 92, DARK)
    c.rect(46, 88, 114, 89, METAL)
    # Груз за бортом: мешок слева, круглый щит справа.
    c.ellipse(58 + sh, 36, 8, 9, WHITE)
    c.rect(55 + sh, 25, 61 + sh, 28, WHITE)
    c.rect(54 + sh, 28, 62 + sh, 29, BRASS)
    c.line(53 + sh, 34, 57 + sh, 42, GREY, 1)
    c.ellipse(105 + sh, 34, 10, 11, GREY)
    c.ellipse(105 + sh, 34, 8, 9, SEA)
    c.rect(104 + sh, 26, 106 + sh, 42, WHITE)
    c.ellipse(105 + sh, 34, 2.5, 2.5, GOLD)
    # Связка копий у левого зубца.
    for x_b, x_t, top in ((33, 28, 12), (39, 42, 8), (36, 35, 5)):
        tx = x_t + sh * 1.4
        c.line(x_b + sh, 36, tx, top, BRASS, 2)
        c.poly([(tx - 2.5, top + 1), (tx + 2.5, top + 1), (tx, top - 5)], GREY)
    # Рыцарь: его низ закрыт бортом.
    _knight_back(c, int(round(72 + sh * 1.2)), phase)
    # Задний борт: доски, два железных пояса с заклёпками, перила по верху.
    c.poly([(28 + sh, 44), (132 + sh, 44), (128 + sh * 0.6, 88), (32 + sh * 0.6, 88)], BRASS)
    for x in range(41, 130, 13):
        xb = 80 + (x - 80) * 48.0 / 52.0
        c.line(x + sh, 47, xb + sh * 0.6, 87, DARK, 1)
    for y0 in (49, 80):
        for y in range(y0, y0 + 4):
            k = (y - 44) / 44.0
            c.rect(28 + sh + (4 - sh * 0.4) * k, y, 132 + sh + (-4 - sh * 0.4) * k, y, METAL)
        for x in range(34, 130, 12):
            k = (y0 + 1 - 44) / 44.0
            xr = 80 + (x - 80) * (1 - k * 4.0 / 52.0) + sh * (1 - 0.4 * k)
            c.rect(xr, y0 + 1, xr + 1, y0 + 2, GOLD)
    c.rect(28 + sh, 42, 132 + sh, 44, BRASS)
    c.rect(28 + sh, 42, 132 + sh, 42, METAL)
    # Угловые зубцы с железной шапкой и бойницей.
    for x0, x1 in ((27, 44), (116, 133)):
        c.rect(x0 + sh, 30, x1 + sh, 46, BRASS)
        c.rect(x0 + sh, 30, x1 + sh, 32, METAL)
        c.rect(x0 + sh - 1, 28, x0 + sh + 5, 30, METAL)
        c.rect(x1 + sh - 5, 28, x1 + sh + 1, 30, METAL)
        mid = (x0 + x1) // 2 + sh
        c.rect(mid, 35, mid + 1, 43, DARK)
        c.rect(mid - 2, 38, mid + 3, 39, DARK)
    # Щит с гербом посередине борта: стальная кромка, поле цвета экипажа, золотой крест.
    cx = 80 + sh * 0.8
    c.poly([(cx - 14, 55), (cx + 14, 55), (cx + 14, 67), (cx, 79), (cx - 14, 67)], GREY)
    c.poly([(cx - 12, 57), (cx + 12, 57), (cx + 12, 66), (cx, 76), (cx - 12, 66)], accent)
    c.rect(cx - 1, 58, cx + 1, 73, GOLD)
    c.rect(cx - 10, 61, cx + 10, 63, GOLD)
    # Древко с раздвоенным вымпелом у правого зубца.
    px = 126 + sh * 1.4
    c.rect(px - 1, 5, px, 30, BRASS)
    c.ellipse(px - 0.5, 3, 2, 2, GOLD)
    flap = 3 * math.sin(phase * math.pi * 2 + 0.6)
    c.poly([(px + 1, 6), (px + 22, 8 + flap), (px + 14, 13 + flap), (px + 22, 18 + flap), (px + 1, 20)], accent)
    c.line(px + 2, 13, px + 12, 13 + flap * 0.6, GOLD, 1)
    c.finish()
    return c


def rival_wagon(lean, phase, accent):
    """Повозка чужого герба со спины, 160×104: тёмный окованный короб со щитами по борту, над
    ним полосатый шатёр цвета `accent` с флажком на шпиле, в проёме стражник в железной шляпе и
    багровой тунике, слева алебарда, справа хоругвь. Ширина по колёсам та же, что у героя."""
    c = Canvas(160, 104)
    sh = lean * 6
    _wheel(c, 22 + sh * 0.3, 80, 22, phase, -1, METAL, DARK, GREY)
    _wheel(c, 138 + sh * 0.3, 80, 22, phase, 1, METAL, DARK, GREY)
    c.rect(27, 84, 133, 88, DARK)
    c.rect(27, 84, 133, 84, METAL)
    # Алебарда слева: древко, топор и остриё.
    hx = 32 + sh * 1.3
    c.line(37 + sh * 0.8, 64, hx, 8, BRASS, 2)
    c.poly([(hx - 1, 11), (hx - 9, 9), (hx - 12, 17), (hx - 9, 25), (hx - 1, 22)], GREY)
    c.poly([(hx - 2, 10), (hx + 3, 10), (hx, 1)], GREY)
    c.poly([(hx + 1, 14), (hx + 7, 16), (hx + 1, 19)], METAL)
    # Хоругвь справа: древко с перекладиной, полотнище с ласточкиным хвостом.
    bx = 127 + sh * 1.3
    c.line(124 + sh * 0.8, 64, bx, 9, DARK, 2)
    c.rect(bx - 9, 11, bx + 9, 12, DARK)
    swing = 1 if phase >= 0.5 else 0
    c.poly([(bx - 8, 13), (bx + 8, 13), (bx + 8 + swing, 40), (bx + swing, 34), (bx - 8 + swing, 40)], accent)
    c.poly([(bx - 5, 17), (bx, 22), (bx + 5, 17), (bx + 5, 21), (bx, 26), (bx - 5, 21)], WHITE if accent != GOLD else RED)
    c.ellipse(bx, 8, 2, 2, GOLD)
    # Шатёр: конус полосами от шпиля, под ним подзор с зубчиками.
    for y in range(16, 51):
        k = (y - 16) / 34.0
        cxr = 80 + sh * (1.3 - 0.3 * k)
        half = 3 + 49 * k
        for x in range(int(round(cxr - half)), int(round(cxr + half)) + 1):
            idx = min(6, max(0, int((x - cxr + half) / (2 * half + 0.001) * 7)))
            c.set(x, y, accent if idx % 2 == 0 else WHITE)
    for i, x in enumerate(range(28, 132, 13)):
        col = accent if i % 2 == 0 else WHITE
        c.rect(x + sh, 51, x + 12 + sh, 59, col)
        c.poly([(x + sh, 60), (x + 12 + sh, 60), (x + 6 + sh, 65)], col)
    c.rect(28 + sh, 51, 131 + sh, 51, GOLD)
    # Проём: стражник со спины в тени шатра.
    gx = int(round(80 + sh * 1.1))
    c.ellipse(gx, 41, 14, 12, K)
    c.rect(gx - 14, 41, gx + 14, 63, K)
    c.rect(gx - 8, 46, gx + 8, 63, TAN)
    c.rect(gx - 8, 56, gx + 8, 57, GOLD)
    c.rect(gx - 11, 47, gx - 9, 60, DARK)
    c.rect(gx + 9, 47, gx + 11, 60, DARK)
    c.rect(gx - 3, 42, gx + 3, 46, DARK)
    c.ellipse(gx, 37, 6, 5, METAL)
    c.rect(gx - 9, 40, gx + 9, 42, METAL)
    c.rect(gx - 8, 40, gx + 3, 40, GREY)
    c.rect(gx - 3, 33, gx - 2, 36, GREY)
    # Шпиль и флажок.
    ax = int(round(80 + sh * 1.3))
    c.rect(ax, 5, ax + 1, 16, DARK)
    c.ellipse(ax + 0.5, 15, 2.5, 2.5, GOLD)
    flap = 2 * math.sin(phase * math.pi * 2)
    c.poly([(ax + 2, 4), (ax + 17, 7 + flap), (ax + 2, 11)], accent)
    # Короб: тёмные доски, железные полосы с шипами, полоса герба, три щита.
    c.poly([(24 + sh * 0.6, 64), (136 + sh * 0.6, 64), (131 + sh * 0.4, 93), (29 + sh * 0.4, 93)], DARK)
    for x in (38, 66, 93, 121):
        c.rect(x + sh * 0.5, 64, x + 2 + sh * 0.5, 93, METAL)
        for y in (67, 89):
            c.rect(x + sh * 0.5, y, x + 2 + sh * 0.5, y + 1, GREY)
    c.rect(26 + sh * 0.6, 69, 134 + sh * 0.6, 71, accent)
    for x in (52, 80, 108):
        c.ellipse(x + sh * 0.5, 81, 8, 8, GREY)
        c.ellipse(x + sh * 0.5, 81, 6, 6, accent)
        c.rect(x + sh * 0.5 - 5, 80, x + sh * 0.5 + 5, 81, WHITE if accent != GOLD else RED)
        c.ellipse(x + sh * 0.5, 81, 2, 2, GOLD)
    c.finish()
    return c


def carts_strip(accent, alien):
    """Три крена (влево, прямо, вправо) по два кадра: лента 6 кадров по 160, порядок как у
    пиратов и космоса. `alien`: повозка чужого герба вместо повозки героя."""
    frames = []
    for lean in (-1.0, 0.0, 1.0):
        for ph in (0.0, 0.5):
            frames.append(rival_wagon(lean, ph, accent) if alien else wagon(lean, ph, accent))
    return strip(frames)


# --- Пропы у дороги ------------------------------------------------------------------------------

def oak():
    """Дуб у обочины, 120×240 (место пальмы): толстый ствол с корнями и дуплом, три сука,
    широкая крона из шапок листвы с тенью снизу, жёлуди; у корней куст роз."""
    rng = random.Random(281)
    c = Canvas(120, 240)
    # Ствол: расширяется к корням, чуть изогнут; борозды коры.
    for y in range(104, 240):
        k = (y - 104) / 135.0
        cx = 60 + 4 * math.sin(k * math.pi)
        half = 7 + 3 * k + 9 * max(0.0, k - 0.86) / 0.14
        c.rect(cx - half, y, cx + half, y, BRASS)
        for g in (-0.55, 0.05, 0.6):
            if (y + int(g * 20)) % 23 > 3:
                c.set(cx + half * g + math.sin(y / 9.0 + g * 7), y, DARK)
    c.ellipse(62, 176, 4, 6, DARK)
    c.ellipse(62, 177, 2, 4, K)
    # Сучья.
    for x1, y1, t in ((28, 86, 7), (60, 70, 8), (94, 90, 7), (44, 60, 5), (80, 58, 5)):
        c.line(60, 126, x1, y1, BRASS, t)
    # Крона: шапки от дальних к ближним, у каждой тёмный низ и светлый верх.
    blobs = ((44, 30, 28, 20), (80, 28, 27, 19), (60, 50, 44, 34), (24, 78, 22, 20), (96, 76, 22, 21),
             (60, 90, 34, 18), (40, 100, 16, 9), (84, 102, 15, 8))
    crown = Canvas(120, 240)
    for bx, by, rx, ry in blobs:
        crown.ellipse(bx, by, rx, ry, PLUM)
        crown.ellipse(bx - 4, by - 5, rx * 0.8, ry * 0.72, VIOLET)
    # Листва: тёмные дужки на свету, светлые точки в тени, редкие жёлуди.
    for _ in range(260):
        x = rng.randint(2, 117)
        y = rng.randint(8, 112)
        v = crown.get(x, y)
        if v == VIOLET and crown.get(x + 3, y) == VIOLET and crown.get(x, y - 2) == VIOLET:
            crown.set(x, y, PLUM)
            crown.set(x + 1, y + 1, PLUM)
            crown.set(x + 2, y, PLUM)
        elif v == PLUM and rng.random() < 0.35 and crown.get(x, y + 2) == PLUM:
            crown.set(x, y, VIOLET)
    for _ in range(12):
        x = rng.randint(14, 106)
        y = rng.randint(60, 104)
        if crown.get(x, y) is not None and crown.get(x + 2, y + 2) is not None:
            crown.rect(x, y, x + 1, y + 1, GOLD)
            crown.set(x, y - 1, BRASS)
            crown.set(x + 1, y - 1, BRASS)
    c.paste(crown, 0, 0)
    # Куст роз у корней и трава.
    c.ellipse(92, 228, 17, 11, PLUM)
    c.ellipse(90, 225, 14, 8, VIOLET)
    for x, y in ((82, 222), (92, 219), (100, 226), (88, 230), (104, 233), (78, 231)):
        c.rect(x, y, x + 2, y + 2, RED)
        c.set(x + 1, y + 1, TAN)
    for x in (22, 30, 38):
        c.poly([(x - 4, 239), (x, 228 + (x % 5)), (x + 4, 239)], VIOLET)
    c.finish()
    return c


def fir():
    """Ель у обочины, 120×240 (место второй пальмы): шесть ярусов лапника с провисшими концами,
    свет слева, шишки, короткий ствол; рядом ёлочка поменьше."""
    rng = random.Random(283)
    c = Canvas(120, 240)
    c.rect(56, 214, 64, 239, BRASS)
    c.rect(59, 216, 59, 239, DARK)
    c.rect(63, 214, 64, 239, DARK)

    def tree(cx, top, bottom, tiers, w0, w1, canvas):
        step = (bottom - top) / (tiers + 0.8)
        for i in range(tiers - 1, -1, -1):
            yt = top + i * step
            yb = yt + step * 1.8
            w = w0 + (w1 - w0) * i / max(1, tiers - 1)
            canvas.poly([(cx, yt), (cx + w, yb), (cx - w, yb)], PLUM)
            # Провисшие концы лап зубцами по нижней кромке.
            n = max(3, int(w / 6))
            for j in range(n):
                x0 = cx - w + j * (2 * w / n)
                x1 = x0 + 2 * w / n
                drop = 5 + (j * 7 + i * 3) % 4
                canvas.poly([(x0, yb), (x1, yb), ((x0 + x1) / 2 - 2, yb + drop)], PLUM)
            # Свет слева: грань от вершины яруса, ниже тени верхнего яруса.
            canvas.poly([(cx - 1, yt + step * 0.62), (cx - w * 0.86, yb - 1), (cx - w * 0.18, yb - 1)], VIOLET)
            for j in range(int(w * 0.6)):
                x = int(cx - rng.uniform(w * 0.15, w * 0.8))
                y = int(rng.uniform(yt + step * 0.8, yb - 2))
                if canvas.get(x, y) == VIOLET and canvas.get(x + 2, y + 1) == VIOLET:
                    canvas.set(x, y, PLUM)
                    canvas.set(x + 1, y + 1, PLUM)
            for j in range(max(1, int(w / 14))):
                x = int(cx + rng.uniform(w * 0.1, w * 0.7))
                y = int(rng.uniform(yt + step * 1.0, yb - 3))
                if canvas.get(x, y) == PLUM and canvas.get(x, y + 5) == PLUM:
                    canvas.rect(x, y, x + 1, y + 3, BRASS)

    tree(60, 6, 222, 6, 15, 55, c)
    # Ёлочка поменьше у левого края.
    c.rect(19, 228, 22, 239, BRASS)
    small = Canvas(120, 240)
    tree(20, 168, 232, 3, 9, 17, small)
    c.paste(small, 0, 0)
    for x in (88, 96, 104):
        c.poly([(x - 4, 239), (x, 230 + (x % 4)), (x + 4, 239)], VIOLET)
    c.finish()
    return c


def boulder():
    """Валун у дороги, 96×64: округлая глыба с трещинами и шапкой мха, рядом камень поменьше,
    у подошвы трава и цветы."""
    c = Canvas(96, 64)
    body = Canvas(96, 64)
    body.ellipse(42, 42, 37, 29, METAL)
    body.ellipse(36, 34, 27, 17, GREY)
    body.ellipse(28, 26, 11, 5, WHITE)
    c.paste(body, 0, 0)
    # Трещины и щербины.
    c.line(52, 20, 60, 36, DARK, 2)
    c.line(60, 36, 54, 50, DARK, 1)
    c.line(60, 36, 72, 44, DARK, 1)
    c.line(20, 42, 30, 54, DARK, 1)
    for x, y in ((40, 44), (66, 54), (14, 50), (46, 56)):
        c.rect(x, y, x + 2, y, DARK)
    # Мох шапкой с подтёками.
    c.ellipse(44, 15, 22, 4, VIOLET)
    for x, d in ((26, 5), (34, 8), (44, 4), (54, 9), (62, 5)):
        c.rect(x, 15, x + 3, 15 + d, VIOLET)
        c.rect(x + 3, 16, x + 3, 15 + d, PLUM)
    c.rect(28, 13, 58, 13, PLUM)
    # Камень поменьше справа.
    c.ellipse(80, 53, 14, 11, METAL)
    c.ellipse(77, 49, 9, 5, GREY)
    c.line(84, 50, 88, 60, DARK, 1)
    # Трава и цветы у подошвы.
    for x in (4, 12, 58, 66, 90):
        c.poly([(x - 4, 63), (x, 54 + (x % 3)), (x + 4, 63)], VIOLET)
    c.rect(8, 55, 9, 56, GOLD)
    c.rect(62, 53, 63, 54, WHITE)
    return c.finish()


def haystack():
    """Стог сена, 48×64 (место бочки): золотой улей с рядами соломы, шест с пучком наверху,
    перевязь, сбоку воткнуты вилы."""
    rng = random.Random(285)
    c = Canvas(48, 64)

    def half(y):
        return 21.0 * (1.0 - (max(0.0, 63 - y) / 52.0) ** 2.3)

    # Вилы за стогом: черенок и три зубца.
    c.line(41, 62, 43, 18, BRASS, 2)
    c.rect(40, 14, 46, 15, GREY)
    for x in (40, 43, 46):
        c.rect(x, 5, x, 14, GREY)
    for y in range(12, 64):
        h = half(y)
        c.rect(21 - h, y, 21 + h, y, GOLD)
    # Ряды соломы: зубчатые тёмные кромки и штрихи вдоль склона.
    for y0 in (24, 35, 46, 57):
        h = half(y0)
        for x in range(int(21 - h) + 1, int(21 + h)):
            c.set(x, y0 + (1 if (x // 2) % 2 == 0 else 0), BRASS)
    for _ in range(46):
        y = rng.randint(15, 60)
        h = half(y) - 2
        if h < 2:
            continue
        x = 21 + rng.uniform(-h, h)
        slope = (x - 21) / 18.0
        c.line(x, y, x + slope * 2, y + 3, BRASS, 1)
    for x in range(8, 36, 3):
        if abs(x - 21) < half(18) - 1:
            c.set(x, 19, WHITE)
    # Шест с пучком и перевязь.
    c.rect(20, 3, 21, 14, BRASS)
    c.poly([(16, 6), (21, 0), (26, 6), (21, 9)], GOLD)
    c.rect(int(21 - half(41)) + 1, 41, int(21 + half(41)) - 1, 41, DARK)
    # Клочки соломы у подошвы.
    for x in (1, 5, 38, 42):
        c.rect(x, 62, x + 2, 63, GOLD)
    return c.finish()


def sign(right):
    """Указатель поворота, 96×112: белёная доска-стрелка остриём в сторону поворота на
    деревянном столбе, красные шевроны, заклёпки, под доской щиток с гербом, у подошвы камни."""
    c = Canvas(96, 112)

    def mx(x):
        return x if right else 95 - x

    def poly(points, col):
        c.poly([(mx(x), y) for x, y in points], col)

    # Столб с навершием и камни у подошвы.
    c.rect(45, 8, 50, 111, BRASS)
    c.rect(49, 8, 50, 111, DARK)
    c.ellipse(47.5, 5, 3.5, 3.5, GOLD)
    c.ellipse(39, 107, 7, 5, METAL)
    c.ellipse(56, 108, 8, 4, GREY)
    c.ellipse(46, 109, 5, 3, GREY)
    # Доска-стрелка: деревянная рама, белёное поле.
    poly([(4, 12), (68, 12), (92, 33), (68, 54), (4, 54)], BRASS)
    poly([(7, 15), (67, 15), (87, 33), (67, 51), (7, 51)], WHITE)
    d = 1 if right else -1
    for k in range(3):
        cx = 48 + d * (k * 21 - 24)
        c.poly([(cx - d * 7, 18), (cx + d * 8, 33), (cx - d * 7, 48), (cx - d * 1, 33)], RED)
    for x, y in ((9, 17), (9, 49), (64, 17), (64, 49)):
        c.rect(mx(x) - 1, y - 1, mx(x), y, DARK)
    # Щиток с гербом на цепочках под доской.
    for x in (42, 53):
        c.rect(x, 55, x, 60, DARK)
    c.poly([(39, 61), (56, 61), (56, 72), (47.5, 82), (39, 72)], GREY)
    c.poly([(41, 63), (54, 63), (54, 71), (47.5, 79), (41, 71)], RED)
    c.rect(47, 64, 48, 76, GOLD)
    c.rect(42, 67, 53, 68, GOLD)
    return c.finish()


def _masonry(c, x0, y0, x1, y1, stone, joint, row=9, brick=16, shift=0):
    """Кладка: ряды камней со швами вперевязку."""
    c.rect(x0, y0, x1, y1, stone)
    for j, y in enumerate(range(y0, y1 + 1, row)):
        if y > y0:
            c.rect(x0, y - 1, x1, y - 1, joint)
        off = ((j + shift) % 2) * (brick // 2)
        for x in range(x0 + off + brick - 1, x1 - 2, brick):
            c.rect(x, y, x, min(y + row - 2, y1), joint)


def tower():
    """Сторожевая башня у дороги, 192×160 (место хижины): каменная башня с навесным ярусом и
    зубцами, красный шатёр с флажком, окованные ворота под аркой, бойница крестом, щит с гербом;
    по бокам стены с зубцами, на левой плющ, на правой знамя, у подошвы куст роз."""
    rng = random.Random(291)
    c = Canvas(192, 160)
    # Шатёр за зубцами: свет слева, тень справа, ряды черепицы.
    c.poly([(60, 42), (132, 42), (96, 8)], RED)
    c.poly([(97, 9), (132, 42), (102, 42)], TAN)
    for y in range(16, 42, 6):
        half = (y - 8) * 36 / 34.0
        for x in range(int(96 - half) + 2, 100):
            if (x + y) % 4 < 2:
                c.set(x, y, TAN)
        for x in range(104, int(96 + half) - 1):
            if (x + y) % 4 < 2:
                c.set(x, y, DARK)
    c.rect(96, 1, 96, 9, DARK)
    c.poly([(98, 1), (112, 4), (98, 8)], GOLD)
    # Боковые стены с зубцами.
    for x0, x1, shade in ((6, 60, False), (132, 186, True)):
        _masonry(c, x0, 100, x1, 159, GREY, METAL)
        for m in range(x0, x1 - 8, 18):
            c.rect(m, 89, m + 11, 100, GREY)
            c.rect(m, 89, m + 11, 89, WHITE)
            c.rect(m + 11, 90, m + 11, 100, METAL)
        c.rect(x0, 100, x1, 100, WHITE)
    # Башня: светлая кладка, справа теневая грань.
    _masonry(c, 60, 56, 114, 159, GREY, METAL, shift=1)
    _masonry(c, 115, 56, 132, 159, METAL, DARK, brick=12)
    c.rect(60, 56, 61, 159, WHITE)
    # Навесной ярус на кронштейнах и зубцы.
    _masonry(c, 54, 42, 138, 55, GREY, METAL, row=7, brick=14)
    c.rect(120, 42, 138, 55, METAL)
    c.rect(54, 42, 138, 42, WHITE)
    for x in range(56, 136, 10):
        c.rect(x, 56, x + 5, 60, METAL)
        c.rect(x + 1, 61, x + 4, 62, DARK)
    for m in range(54, 130, 18):
        c.rect(m, 30, m + 12, 42, GREY if m < 110 else METAL)
        c.rect(m, 30, m + 12, 30, WHITE)
        c.rect(m + 12, 31, m + 12, 42, METAL if m < 110 else DARK)
    # Бойница крестом и узкие окна.
    c.rect(86, 70, 88, 88, K)
    c.rect(82, 77, 92, 79, K)
    for x in (70, 104):
        c.rect(x, 74, x + 2, 84, K)
        c.rect(x - 1, 72, x + 3, 73, WHITE)
    # Ворота: арка из клиньев, дощатые створки, железные полосы и кольцо.
    c.ellipse(87, 128, 20, 20, WHITE)
    c.rect(67, 128, 107, 159, WHITE)
    for a in range(-80, 81, 20):
        ra = math.radians(a - 90)
        c.line(87 + math.cos(ra) * 15, 128 + math.sin(ra) * 15, 87 + math.cos(ra) * 20, 128 + math.sin(ra) * 20,
               METAL, 1)
    for y in (138, 148, 158):
        c.rect(67, y, 71, y, METAL)
        c.rect(103, y, 107, y, METAL)
    c.ellipse(87, 128, 15, 15, BRASS)
    c.rect(72, 128, 102, 159, BRASS)
    for x in range(77, 102, 5):
        c.rect(x, 115, x, 159, DARK)
    c.rect(87, 113, 87, 159, K)
    for y in (132, 150):
        c.rect(72, y, 102, y + 2, METAL)
        for x in range(74, 102, 6):
            c.set(x, y + 1, GOLD)
    c.ellipse(92, 142, 2.5, 2.5, GOLD)
    c.set(92, 142, BRASS)
    # Щит с гербом над воротами и факелы по бокам.
    c.poly([(79, 92), (95, 92), (95, 100), (87, 107), (79, 100)], GOLD)
    c.poly([(81, 94), (93, 94), (93, 99), (87, 104), (81, 99)], RED)
    c.rect(86, 94, 87, 102, GOLD)
    for x in (63, 110):
        c.rect(x, 118, x + 1, 126, DARK)
        c.poly([(x - 2, 118), (x + 3, 118), (x + 0.5, 110)], GOLD)
        c.rect(x, 114, x + 1, 117, RED)
    # Знамя на правой стене.
    c.rect(148, 104, 172, 105, DARK)
    c.poly([(150, 106), (170, 106), (170, 140), (160, 133), (150, 140)], RED)
    c.rect(159, 110, 161, 128, GOLD)
    c.rect(153, 115, 167, 117, GOLD)
    # Плющ по левой стене.
    for _ in range(70):
        k = rng.random() ** 1.6
        y = 157 - 52 * k
        x = 8 + rng.uniform(0, 30 * (1 - k * 0.75)) + rng.uniform(-2, 2)
        c.rect(x, y, x + 3, y + 2, PLUM)
        c.rect(x, y, x + 2, y + 1, VIOLET)
        c.set(x + 1, y - 1, VIOLET)
    # Куст роз и трава у подошвы.
    c.ellipse(160, 151, 20, 9, PLUM)
    c.ellipse(158, 148, 16, 6, VIOLET)
    for x, y in ((146, 147), (156, 144), (166, 149), (174, 152), (152, 153)):
        c.rect(x, y, x + 2, y + 2, RED)
        c.set(x + 1, y + 1, TAN)
    for x in (4, 46, 54, 112, 122, 186):
        c.poly([(x - 4, 159), (x, 150 + (x % 4)), (x + 4, 159)], VIOLET)
    return c.finish()


def road_colors():
    """Лента цветов дороги 8×1: индекс это место в `ROAD_COLORS`."""
    c = Canvas(8, 1)
    for i in range(8):
        c.set(i, 0, i)
    return c


def sprites():
    """Ленты гонки в палитре спрайтов, ключи как у пиратов и космоса."""
    out = {
        "cart_hero": carts_strip(RED, False),
        "palm": oak(),
        "palm_b": fir(),
        "road_rock": boulder(),
        "road_barrel": haystack(),
        "sign_left": sign(False),
        "sign_right": sign(True),
        "road_hut": tower(),
    }
    # Гербы соперников: синий, золотой, зелёный, багровый.
    for i, accent in enumerate((SEA, GOLD, VIOLET, TAN)):
        out["cart_%d" % i] = carts_strip(accent, True)
    return out


def horizon():
    """Горизонт в своей палитре `CASTLES_SKY`."""
    return {"road_sky": sky(), "road_islands": islands(), "road_sea": sea()}


def road_palette():
    return {"road_colors": road_colors()}


def preview(path):
    """Лист набора; выше 1500 пикселей делится на файлы с суффиксами _b, _c."""
    items = castles16.shaded(sprites())
    for key, canvas in horizon().items():
        items[key] = (canvas, CASTLES_SKY)
    for key, canvas in road_palette().items():
        items[key] = (canvas, ROAD_COLORS)
    scale, pad, max_w, limit = 2, 6, 512, 1500
    pages = [{}]
    height = pad * scale
    for key, item in items.items():
        rows = -(-item[0].w // max_w) * (item[0].h + pad) * scale
        if pages[-1] and height + rows > limit:
            pages.append({})
            height = pad * scale
        pages[-1][key] = item
        height += rows
    root, ext = os.path.splitext(path)
    for i, page in enumerate(pages):
        castles16.save_sheet(path if i == 0 else "%s_%s%s" % (root, chr(ord("a") + i), ext), page, scale=scale,
                             max_w=max_w)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
