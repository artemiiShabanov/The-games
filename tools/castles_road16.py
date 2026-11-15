#!/usr/bin/env python3
"""Набор «Замки» для гонки × 16/32-bit «псевдо-3D» (#136), зеркало `space_road16.py` (а оно
`pixel_road16.py`): те же ключи, размеры холстов и порядок кадров, чтобы `racing_bit16.gd` брала
их без правок. Герой едет на боевой повозке с копьями и вымпелом (вид сзади), за рулём рыцарь с
красным плюмажем; соперники на чёрных повозках чужих гербов с частоколом и стражником в чёрном
шлеме. У дороги дуб и ель вместо пальм (дуб с кустом роз), замшелый валун, стог сена, указатели
в виде стрел-досок, сторожка с двумя башнями вместо хижины. На горизонте дневное небо с облаками
и солнцем, зелёные холмы с замком, луг вместо моря. Дорога из брусчатки, обочина трава.

Повозки и пропы в палитре `castles16.PALETTE`, горизонт в своей (`CASTLES_SKY`), цвета дороги
лентой `road_colors` по местам `ROAD_COLORS`. Ленты те же, что у космоса: повозки по 6 кадров
160×104 (три крена по два кадра, колёса бегут по фазе), деревья 120×240, валун 96×64, стог
48×64, указатели 96×112, сторожка 192×160, небо 512×128, холмы 512×40, луг 512×24.

    python3 tools/castles_road16.py --preview out.png   # лист режется на out.png, out_b.png...
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import castles16  # noqa: E402
from castles16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS,  # noqa: E402
                       METAL, DARK, RED, VIOLET, PLUM)

# Палитра горизонта: небо, облака, луг, холмы и замок. Места те же по смыслу, что у пиратов.
S0, S1, S2, S3, C0, C1, C2, M0, M1, M2, M3, I0, I1, I2, I3, SUN = range(16)
CASTLES_SKY = [
    (0x3E, 0x86, 0xD8),  # S0  небо наверху
    (0x5C, 0xA2, 0xE8),  # S1
    (0x86, 0xC2, 0xF0),  # S2
    (0xBE, 0xE2, 0xF6),  # S3  небо у горизонта
    (0xA8, 0xBE, 0xDC),  # C0  тень облака
    (0xE2, 0xEC, 0xF8),  # C1  облако
    (0xFF, 0xFF, 0xFF),  # C2  свет облака, солнце
    (0x3C, 0x8C, 0x44),  # M0  луг вдали
    (0x4E, 0xA4, 0x4C),  # M1  луг
    (0x6C, 0xC0, 0x58),  # M2  луг у дороги
    (0x2C, 0x6C, 0x38),  # M3  тень травы, бойницы
    (0x78, 0x94, 0xAC),  # I0  холмы в дымке, тень камня
    (0x4A, 0x8C, 0x58),  # I1  зелёный холм
    (0xB4, 0xB8, 0xC4),  # I2  камень замка
    (0xC8, 0x3C, 0x3C),  # I3  крыши и вымпелы
    (0xB8, 0xDC, 0x6A),  # SUN сухая трава у кромки дороги
]

# Цвета дороги по местам ленты `road_colors` (демка берёт их по индексу).
ROAD_COLORS = [
    (0xA0, 0x98, 0x8C),  # 0 брусчатка светлая
    (0x8E, 0x86, 0x7C),  # 1 брусчатка тёмная
    (0xD0, 0x34, 0x38),  # 2 бордюр красный
    (0xEC, 0xE8, 0xDC),  # 3 бордюр белый
    (0xF4, 0xE6, 0xA8),  # 4 разметка
    (0x7C, 0xC8, 0x58),  # 5 трава светлая
    (0x5E, 0xAC, 0x48),  # 6 трава тёмная
    (0xBE, 0xE2, 0xF6),  # 7 дымка вдали
]


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wellipse(c, cx, cy, rx, ry, col):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                _wset(c, x, y, col)


# --- Горизонт ----------------------------------------------------------------------------------

def sky():
    """Небо, 512×128, стыкуется по краям: синева наверху, светлая дымка у горизонта, пухлые
    облака с серой подбивкой, солнце с ореолом и пара птиц."""
    rng = random.Random(171)
    c = Canvas(512, 128)
    bands = [(0, S0), (40, S1), (78, S2), (106, S3)]
    for y in range(128):
        col = S0
        for start, b in bands:
            if y >= start:
                col = b
        for x in range(512):
            for start, b in bands[1:]:
                if start <= y < start + 3 and (x + y) % 2 == 0:
                    col = bands[bands.index((start, b)) - 1][1]
            c.set(x, y, col)
    # Солнце: ореол шахматкой, белый диск.
    sx, sy = 392, 34
    for y in range(sy - 26, sy + 27):
        for x in range(sx - 26, sx + 27):
            d = math.hypot(x - sx, y - sy)
            if 15 < d <= 26 and (x + y) % 2 == 0:
                _wset(c, x, y, S3)
            elif 15 < d <= 20 and (x + y) % 2 == 1:
                _wset(c, x, y, S3)
    _wellipse(c, sx, sy, 15, 15, S3)
    _wellipse(c, sx, sy, 11, 11, C2)
    # Облака: основа, тень снизу, белая шапка сверху слева.
    for cx, cy, w in ((60, 38, 40), (170, 70, 52), (300, 22, 34), (448, 82, 44), (236, 100, 28)):
        for dx, dy, rx, ry in ((-0.6, 0.12, 0.34, 0.34), (-0.3, -0.12, 0.34, 0.5), (0.05, -0.2, 0.36, 0.56),
                               (0.4, 0.0, 0.34, 0.42), (0.7, 0.14, 0.26, 0.3), (0.0, 0.25, 0.85, 0.3)):
            _wellipse(c, cx + dx * w, cy + dy * w * 0.5, rx * w, ry * w * 0.5, C1)
        for dx in range(int(-w * 0.8), int(w * 0.8) + 1):
            _wset(c, cx + dx, cy + w * 0.5 * 0.5 + 1, C0)
            _wset(c, cx + dx, cy + w * 0.5 * 0.5, C0 if abs(dx) < w * 0.5 else C1)
        _wellipse(c, cx - 0.2 * w, cy - 0.22 * w * 0.5, 0.3 * w, 0.2 * w * 0.5, C2)
    # Птицы: галочки крыльями.
    for bx, by in ((120, 22), (136, 28), (332, 56), (348, 52), (92, 84)):
        for i in range(-3, 1):
            _wset(c, bx + i, by + (i + 3) // 2 * -1 + 1, I0)
        for i in range(0, 4):
            _wset(c, bx + i, by - (3 - i) // 2 + 1, I0)
    # Мелкие облачка дымкой у горизонта.
    for _ in range(14):
        x = rng.randint(0, 511)
        y = rng.randint(104, 116)
        for i in range(rng.randint(5, 12)):
            _wset(c, x + i, y, C1 if y < 112 else S3)
    return c


def islands():
    """Холмы и замок на горизонте, 512×40, прозрачный верх: дальние холмы в дымке, ближний
    зелёный холм с замком (стена с зубцами, донжон и две башни с красными крышами и вымпелами),
    по склонам тёмные ели, вдали сторожевые башни."""
    c = Canvas(512, 40)
    hills = ((60, 70, 12, False), (190, 46, 8, False), (300, 110, 16, True), (430, 64, 11, False))
    tops = {}
    for cx, w, h, near in hills:
        for x in range(int(cx - w), int(cx + w) + 1):
            k = (x - cx) / w
            jag = (abs((x * 7) % 13 - 6) * 0.5 if near else abs((x * 5) % 9 - 4) * 0.3)
            top = 39 - int(h * max(0.0, 1.0 - k * k) ** 0.7 + jag)
            for y in range(top, 40):
                _wset(c, x, y, I0 if not near else (M2 if y < top + 1 else I1))
            tops[x % 512] = min(tops.get(x % 512, 99), top)
    # Ели по склонам.
    for tx in (232, 240, 248, 262, 350, 358, 366, 372, 380, 76, 84, 440, 446):
        by = tops.get(tx, 36) + 2
        for k in range(3):
            w = 1 + k
            for yy in range(by - 7 + k * 2, by - 5 + k * 2 + 1):
                for xx in range(tx - w, tx + w + 1):
                    _wset(c, xx, yy, M3)
        _wset(c, tx, by - 8, M3)
    # Замок на вершине: стена, донжон, две башни.
    gx = 300
    base = tops[gx] + 2

    def tower(x, w, h, roof_h, flag=True):
        for yy in range(base - h, base + 1):
            for xx in range(x - w // 2, x + w // 2 + 1):
                _wset(c, xx, yy, I2 if xx > x - w // 2 else C1)
        for yy in range(base - h, base + 1):
            _wset(c, x + w // 2, yy, I0)
        for yy in range(roof_h):
            half = int((w // 2 + 2) * (1.0 - yy / float(roof_h)))
            for xx in range(x - half, x + half + 1):
                _wset(c, xx, base - h - 1 - yy, I3)
        if flag:
            for yy in range(5):
                _wset(c, x, base - h - roof_h - yy, I0)
            for i in range(4):
                _wset(c, x + 1 + i, base - h - roof_h - 4 + i // 2, I3)
                _wset(c, x + 1 + i, base - h - roof_h - 3 + i // 2, I3)
        for yy in (base - h + 4, base - h + 9):
            _wset(c, x, yy, M3)
            _wset(c, x, yy + 1, M3)

    for yy in range(base - 8, base + 1):
        for xx in range(gx - 26, gx + 27):
            _wset(c, xx, yy, I2)
    for xx in range(gx - 26, gx + 27, 3):
        _wset(c, xx, base - 10, I2)
        _wset(c, xx + 1, base - 10, I2)
        _wset(c, xx, base - 9, I2)
        _wset(c, xx + 1, base - 9, I2)
    for xx in range(gx - 26, gx + 27):
        _wset(c, xx, base, I0)
    tower(gx, 10, 15, 7)
    tower(gx - 25, 7, 12, 5)
    tower(gx + 25, 7, 11, 5, False)
    for yy in range(base - 5, base + 1):
        for xx in range(gx - 12, gx - 6):
            _wset(c, xx, yy, M3)
    for yy in range(base - 5, base + 1):
        for xx in range(gx + 6, gx + 12):
            _wset(c, xx, yy, M3)
    # Дальние сторожевые башни без крыши.
    for tx, th in ((62, 8), (432, 7), (190, 6)):
        by = tops.get(tx, 36) + 1
        for yy in range(by - th, by + 1):
            for xx in range(tx - 2, tx + 3):
                _wset(c, xx, yy, I2)
        for xx in (tx - 2, tx, tx + 2):
            _wset(c, xx, by - th - 1, I2)
    return c


def sea():
    """Луг от горизонта, 512×24: тёмная трава вдали, светлее у дороги, полосы скоса, у нижней
    кромки полоса сухой травы, кустики и цветы (красные, белые, жёлтые)."""
    rng = random.Random(173)
    c = Canvas(512, 24)
    for y in range(24):
        col = M0 if y < 5 else (M1 if y < 15 else M2)
        c.rect(0, y, 511, y, col)
        if y in (5, 15):
            for x in range(0, 512, 2):
                c.set(x + (y % 2), y, M0 if y == 5 else M1)
    # Полосы скоса: светлые длинные полосы с резкими краями.
    for x0 in range(0, 512, 64):
        for y in range(5, 22):
            half = 4 + y // 3
            for x in range(x0 + 30 - half, x0 + 30 + half):
                if c.get(x % 512, y) in (M1, M2):
                    _wset(c, x, y, M2 if c.get(x % 512, y) == M1 else SUN)
    c.rect(0, 22, 511, 23, SUN)
    # Кустики: тёмная метёлка с светлым пятном.
    for _ in range(40):
        y = rng.randint(2, 20)
        x = rng.uniform(0, 512)
        w = rng.randint(1, 2) + y // 8
        for i in range(-w, w + 1):
            _wset(c, x + i, y, M3)
        _wset(c, x, y - 1, M3)
        _wset(c, x - w // 2, y + 1, M1 if y < 15 else M2)
    # Цветы.
    for _ in range(70):
        y = rng.randint(1, 21)
        _wset(c, rng.uniform(0, 512), y, rng.choice((C2, I3, SUN, C2)))
    return c


# --- Повозки, деревья и пропы (палитра спрайтов) -----------------------------------------------

def _wheel(c, cx, cy, r, phase, spiked=False):
    """Колесо повозки сзади: широкий обод с железными кромками, деревянные звенья, шляпки гвоздей
    бегут вниз (`phase` 0..1). Колпак ступицы с внешней стороны, у вражеских с шипом."""
    w = 8
    c.rect(cx - w, cy - r + 3, cx + w, cy + r - 3, K)
    c.rect(cx - w + 2, cy - r, cx + w - 2, cy + r, K)
    c.rect(cx - w + 2, cy - r + 3, cx + w - 2, cy + r - 3, TAN)
    c.rect(cx - w + 2, cy - r + 3, cx - w + 3, cy + r - 3, DARK)
    c.rect(cx + w - 3, cy - r + 3, cx + w - 2, cy + r - 3, DARK)
    c.rect(cx - w + 3, cy - r + 3, cx - w + 3, cy + r - 3, METAL)
    c.rect(cx - w + 4, cy - r + 3, cx - w + 4, cy + r - 3, SKIN)
    step = 8
    off = int(phase * step)
    for y in range(int(cy - r + 4) + off, int(cy + r - 3), step):
        c.rect(cx - w + 4, y, cx + w - 4, y, DARK)
        c.set(cx - 3, y + 3, METAL)
        c.set(cx + 2, y + 3, METAL)
    out = -1 if cx < 80 else 1
    ox = cx + out * (w + 1)
    c.rect(min(ox, ox + out * 2), cy - 3, max(ox, ox + out * 2), cy + 3, METAL)
    if spiked:
        c.poly([(ox, cy - 5), (ox + out * 8, cy), (ox, cy + 5)], METAL)
        c.set(ox + out * 2, cy - 1, WHITE)


def _shield(c, cx, top, accent, sh=0.0):
    """Геральдический щит на заднем борту: стальной кант, поле цвета `accent`, белый шеврон."""
    pts = [(cx - 17, top), (cx + 17, top), (cx + 17, top + 17), (cx, top + 31), (cx - 17, top + 17)]
    c.poly(pts, GREY)
    c.poly([(cx - 15, top + 2), (cx + 15, top + 2), (cx + 15, top + 16), (cx, top + 28), (cx - 15, top + 16)], accent)
    c.rect(cx - 17, top, cx + 17, top, WHITE)
    c.line(cx - 10, top + 9, cx, top + 17, WHITE, 3)
    c.line(cx, top + 17, cx + 10, top + 9, WHITE, 3)
    c.rect(cx - 15, top + 2, cx - 15, top + 15, SKIN if accent != GOLD else WHITE)


def _body_box(c, sh, dark):
    """Короб повозки: доски, железные полосы с заклёпками и поручень. `dark` чернёная повозка."""
    poly = [(30 + sh, 46), (130 + sh, 46), (128 + sh * 0.6, 90), (32 + sh * 0.6, 90)]
    c.poly(poly, DARK if dark else TAN)
    seam = METAL if dark else DARK
    for x in range(44, 130, 14):
        c.line(x + sh * 0.9, 47, x + sh * 0.6, 89, seam, 1)
    if not dark:
        for x in range(45, 130, 14):
            c.line(x + sh * 0.9, 48, x + sh * 0.6, 88, SKIN, 1)
    for y in (58, 80):
        c.rect(31 + sh * 0.8, y, 129 + sh * 0.8, y + 2, METAL if not dark else GREY)
        c.rect(31 + sh * 0.8, y, 129 + sh * 0.8, y, WHITE if not dark else METAL)
        for x in range(38, 126, 16):
            c.set(x + sh * 0.8, y + 1, DARK)
    c.rect(28 + sh, 44, 132 + sh, 48, DARK)
    c.rect(28 + sh, 44, 132 + sh, 44, METAL)
    c.rect(30 + sh, 45, 130 + sh, 45, METAL if dark else SKIN)


def _lanterns(c, sh, accent, glow):
    """Фонари на задних углах: железная рама, огонёк (красный, у красной повозки золотой)."""
    for x in (36, 124):
        c.rect(x + sh - 4, 52, x + sh + 4, 62, DARK)
        c.rect(x + sh - 3, 54, x + sh + 3, 60, RED if accent != RED else GOLD)
        c.rect(x + sh - 1, 55, x + sh + 1, 57, GOLD if glow else SKIN)
        c.rect(x + sh - 5, 51, x + sh + 5, 51, METAL)


def _hitch(c, sh):
    """Под бортом два железных кольца подвеса."""
    for x in (50, 110):
        cx = x + sh * 0.6
        c.ellipse(cx, 85, 5, 4, METAL)
        c.ellipse(cx, 85, 2.5, 2, DARK)


def _rider_back(c, x0, plume):
    """Рыцарь со спины: стальные наплечники, красный табард с золотым поясом, шлем с плюмажем."""
    c.rect(x0 - 1, 24, x0 + 17, 42, GREY)
    c.rect(x0 + 2, 26, x0 + 14, 42, RED)
    c.rect(x0 + 7, 26, x0 + 9, 42, PLUM)
    c.rect(x0 + 2, 36, x0 + 14, 37, GOLD)
    c.rect(x0 - 1, 24, x0 + 17, 24, WHITE)
    for side in (-1, 1):
        sx = x0 + (0 if side < 0 else 16)
        c.ellipse(sx, 27, 4, 4, GREY)
        c.rect(sx - 3, 24, sx + 3, 24, WHITE)
        c.line(sx, 28, sx + side * 5, 35, GREY, 5)
        c.line(sx + side * 5, 35, sx + side * 3, 41, METAL, 4)
        c.ellipse(sx + side * 2.5, 42, 3, 2.5, DARK)
    # Шлем: сталь, шов на затылке, шея металлом, красный гребень вдоль макушки.
    c.ellipse(x0 + 8, 15, 8.5, 9, GREY)
    c.rect(x0 + 2, 11, x0 + 14, 11, METAL)
    c.rect(x0 + 3, 7, x0 + 13, 7, WHITE)
    c.rect(x0 + 4, 21, x0 + 12, 22, METAL)
    c.rect(x0 + 7, 7, x0 + 9, 22, METAL)
    c.rect(x0 + 6, plume, x0 + 10, 14, RED)
    c.rect(x0 + 7, plume - 2, x0 + 9, plume, RED)
    c.rect(x0 + 7, 15, x0 + 9, 19, RED)


def _guard_back(c, x0):
    """Стражник со спины: чёрный шлем с наносником-гребнем, кольчужный капюшон, багровая туника."""
    c.rect(x0 - 1, 24, x0 + 17, 42, DARK)
    c.rect(x0 + 2, 26, x0 + 14, 42, VIOLET)
    c.rect(x0 + 2, 26, x0 + 4, 42, PLUM)
    c.rect(x0 + 2, 36, x0 + 14, 37, DARK)
    for side in (-1, 1):
        sx = x0 + (0 if side < 0 else 16)
        c.ellipse(sx, 27, 4, 4, DARK)
        c.line(sx, 28, sx + side * 5, 35, DARK, 5)
        c.line(sx + side * 5, 35, sx + side * 3, 41, METAL, 4)
        c.ellipse(sx + side * 2.5, 42, 3, 2.5, K)
    for y in range(22, 27):
        for x in range(int(x0) + 1, int(x0) + 16):
            if (x + y) % 2 == 0:
                c.set(x, y, METAL)
    c.ellipse(x0 + 8, 15, 8.5, 9, DARK)
    c.rect(x0 + 2, 18, x0 + 14, 22, METAL)
    c.rect(x0 + 3, 7, x0 + 13, 7, METAL)
    c.rect(x0 + 7, 5, x0 + 9, 20, METAL)
    for dx in range(3, 14, 2):
        c.set(x0 + dx, 19 + (dx % 4) // 2, DARK)


def cart(lean, phase, accent):
    """Боевая повозка героя со спины, 160×104: два деревянных колеса, дубовый короб с железными
    полосами и щитом цвета `accent` на заднем борту, фонари по углам, копья в стойке, круглый
    щит на шесте, у правого угла копьё-мачта с вымпелом; за рулём рыцарь. `lean` −1..1 крен."""
    c = Canvas(160, 104)
    sh = lean * 6
    _wheel(c, 22 + sh * 0.3, 78, 24, phase)
    _wheel(c, 138 + sh * 0.3, 78, 24, phase)
    # Ось и подбой днища.
    c.rect(24, 84, 136, 88, DARK)
    c.rect(34, 88, 126, 92, TAN)
    c.rect(34, 91, 126, 92, DARK)
    _body_box(c, sh, False)
    _shield(c, 80 + sh * 0.8, 52, accent)
    _lanterns(c, sh, accent, phase < 0.5)
    _hitch(c, sh)
    # Вымпел на копье-мачте: древко, стальной наконечник, ласточкин хвост цвета `accent`.
    mx = 122 + sh * 1.4
    c.rect(mx, 6, mx + 2, 46, TAN)
    c.rect(mx, 6, mx, 44, SKIN)
    flap = 3 * math.sin(phase * math.pi * 2)
    c.poly([(mx + 3, 8), (mx + 27, 12 + flap), (mx + 19, 16 + flap * 0.8), (mx + 27, 21 + flap),
            (mx + 3, 24)], accent)
    c.poly([(mx + 1, 0), (mx + 4, 5), (mx + 1, 8), (mx - 2, 5)], WHITE)
    c.rect(mx - 1, 8, mx + 3, 9, GOLD)
    # Круглый щит на шесте слева.
    c.line(44 + sh, 44, 40 + sh * 1.2, 30, TAN, 2)
    sx = 39 + sh * 1.2
    c.ellipse(sx, 25, 10, 10, DARK)
    c.ellipse(sx, 25, 8, 8, TAN)
    c.line(sx - 8, 25, sx + 8, 25, DARK, 1)
    c.line(sx, 17, sx, 33, DARK, 1)
    c.ellipse(sx, 25, 3, 3, GOLD)
    c.set(sx - 1, 24, WHITE)
    # Копья в стойке справа: три древка с наконечниками.
    for dx, top in ((0, 24), (6, 18), (12, 26)):
        x = 100 + dx + sh
        c.rect(x, top + 6, x + 1, 44, TAN)
        c.poly([(x + 0.5, top - 2), (x + 3, top + 6), (x - 2, top + 6)], WHITE)
    c.rect(98 + sh, 38, 116 + sh, 40, DARK)
    # Мешок зерна слева от рыцаря.
    c.ellipse(58 + sh, 38, 8, 7, SKIN)
    c.rect(54 + sh, 30, 62 + sh, 32, SKIN)
    c.rect(54 + sh, 32, 62 + sh, 33, DARK)
    c.line(52 + sh, 40, 64 + sh, 38, BRASS, 1)
    _rider_back(c, 72 + sh * 1.2, 3)
    c.finish()
    return c


def black_cart(lean, phase, accent):
    """Чёрная повозка чужого герба со спины, 160×104: колёса с шипами на ступицах, железный короб с
    щитом цвета `accent`, поверх борта частокол остриями, фонари на столбах, стяг на перекладине
    справа; за рулём стражник в чёрном шлеме и багровой тунике."""
    c = Canvas(160, 104)
    sh = lean * 6
    _wheel(c, 22 + sh * 0.3, 78, 24, phase, spiked=True)
    _wheel(c, 138 + sh * 0.3, 78, 24, phase, spiked=True)
    c.rect(24, 84, 136, 88, DARK)
    c.rect(34, 88, 126, 92, METAL)
    c.rect(34, 91, 126, 92, DARK)
    _body_box(c, sh, True)
    _shield(c, 80 + sh * 0.8, 52, accent)
    _hitch(c, sh)
    # Стражник за частоколом.
    _guard_back(c, 72 + sh * 1.2)
    # Частокол по заднему борту: заострённые колья на всю ширину, ниже плеч стражника.
    for x in range(34, 128, 8):
        px = x + sh * (1.0 - (46 - 34) / 60.0)
        c.rect(px, 36, px + 5, 46, DARK)
        c.poly([(px, 36), (px + 5, 36), (px + 2.5, 29)], DARK)
        c.line(px + 1, 38, px + 1, 45, METAL, 1)
        c.set(px + 2, 31, METAL)
    # Столбы с фонарями по углам.
    for x in (30, 126):
        px = x + sh
        c.rect(px - 1, 14, px + 2, 46, DARK)
        c.rect(px - 1, 14, px - 1, 45, METAL)
        c.rect(px - 4, 8, px + 5, 18, DARK)
        c.rect(px - 3, 10, px + 4, 16, RED if phase < 0.5 else GOLD)
        c.rect(px - 1, 11, px + 2, 13, SKIN)
        c.poly([(px - 5, 8), (px + 6, 8), (px + 0.5, 3)], METAL)
    # Стяг: высокое древко с остриём, перекладина и полотнище с зубцами понизу.
    mx = 142 + sh * 1.4
    c.rect(mx - 1, 10, mx + 1, 46, DARK)
    c.rect(mx - 1, 10, mx - 1, 45, METAL)
    c.poly([(mx, 3), (mx + 3, 10), (mx - 3, 10)], METAL)
    flap = 2 * math.sin(phase * math.pi * 2)
    c.rect(mx - 12, 16, mx + 12, 17, METAL)
    c.poly([(mx - 10, 18), (mx + 10, 18), (mx + 10, 32 + flap), (mx + 5, 29 + flap), (mx, 33 + flap),
            (mx - 5, 29 + flap), (mx - 10, 32 + flap)], accent)
    c.rect(mx - 1, 21, mx + 1, 27, WHITE)
    c.finish()
    return c


def carts_strip(accent, enemy):
    """Три крена (влево, прямо, вправо) по два кадра: лента 6 кадров по 160, порядок как у пиратов."""
    frames = []
    for lean in (-1.0, 0.0, 1.0):
        for ph in (0.0, 0.5):
            frames.append(black_cart(lean, ph, accent) if enemy else cart(lean, ph, accent))
    return strip(frames)


def oak():
    """Старый дуб у обочины, 120×240 (место пальмы): толстый ствол с корнями и дуплом, пышная
    крона из шести шапок листвы с бликами, внизу куст роз."""
    rng = random.Random(181)
    c = Canvas(120, 240)
    # Ствол: расширяется к корням, кора с бороздами, две ветви уходят в крону.
    for y in range(100, 240):
        k = (y - 100) / 139.0
        w = 11 + 5 * k + (8 * max(0.0, (y - 218) / 21.0) ** 1.5)
        lean = 2 * math.sin(k * 2.0)
        for x in range(int(60 + lean - w), int(60 + lean + w) + 1):
            c.set(x, y, TAN)
    for y in range(102, 238):
        k = (y - 100) / 139.0
        w = 11 + 5 * k
        lean = 2 * math.sin(k * 2.0)
        c.set(60 + lean - w + 3, y, SKIN)
        c.set(60 + lean - w + 4, y, SKIN)
        for fx in (-4, 1, 6):
            if (y // 11 + fx) % 3:
                c.set(60 + lean + fx, y, DARK)
    c.ellipse(55, 182, 5, 9, K)
    c.ellipse(55, 188, 3, 4, DARK)
    c.line(50, 112, 28, 84, TAN, 6)
    c.line(70, 112, 92, 84, TAN, 6)
    # Крона: мелкие шапки листвы по овалам, снизу тёмные, сверху слева светлые.
    cl = []
    for cx, cy, rx, ry in ((60, 112, 52, 26), (32, 82, 30, 24), (90, 84, 30, 24), (60, 56, 42, 34),
                           (30, 50, 22, 18), (90, 52, 22, 18), (60, 24, 26, 18)):
        n = int(rx * 0.55)
        for i in range(n):
            a = i * 2 * math.pi / n
            cl.append((cx + math.cos(a) * rx * 0.85, cy + math.sin(a) * ry * 0.85, 9 + (i % 3)))
        cl.append((cx, cy, min(rx, ry) * 0.9))
    cl += [(38, 106, 14), (82, 106, 14), (60, 102, 22), (22, 98, 12), (98, 100, 12)]
    for x, y, r in cl:
        c.ellipse(x + 2, y + 4, r, r * 0.9, NAVY)
    for x, y, r in cl:
        c.ellipse(x, y, r, r * 0.9, SEA)
    for x, y, r in sorted(cl, key=lambda t: t[1]):
        if x < 70 and y < 108:
            c.ellipse(x - r * 0.25, y - r * 0.3, r * 0.6, r * 0.5, AQUA)
    for _ in range(190):
        x = rng.uniform(6, 114)
        y = rng.uniform(6, 134)
        col = c.get(int(x), int(y))
        if col in (SEA, AQUA):
            c.set(x, y, NAVY if col == SEA else SEA)
            c.set(x + 1, y, NAVY if col == SEA else SEA)
    # Куст роз у корней слева.
    for bx, by, r in ((20, 232, 14), (40, 235, 10)):
        c.ellipse(bx, by, r, r * 0.7, NAVY)
        c.ellipse(bx - 1, by - 2, r - 2, r * 0.6, SEA)
        c.ellipse(bx - 3, by - 4, r * 0.4, r * 0.25, AQUA)
    for rx, ry in ((14, 228), (24, 226), (30, 233), (40, 230), (18, 236)):
        c.ellipse(rx, ry, 2, 2, RED)
        c.set(rx, ry, GOLD)
    c.finish()
    return c


def pine():
    """Высокая ель у обочины, 120×240 (место второй пальмы): восемь ярусов лап с бахромой книзу,
    светлые лапы слева и тёмные справа, короткий ствол, шишки и пучок травы."""
    c = Canvas(120, 240)
    c.rect(56, 216, 63, 239, TAN)
    c.rect(56, 216, 57, 239, SKIN)
    c.rect(60, 216, 63, 239, DARK)
    for i in range(7, -1, -1):
        apex = 6 + i * 24
        bot = apex + 48
        w = 14 + i * 5
        pts = [(60, apex)]
        # Бахрома: правая сторона вниз зубцами, затем влево.
        n = 6
        right = [(60 + w * (1 - (j % 2) * 0.12), apex + (bot - apex) * (0.35 + 0.65 * j / n)) for j in range(n + 1)]
        left = [(60 - w * (1 - (j % 2) * 0.12), apex + (bot - apex) * (0.35 + 0.65 * j / n)) for j in range(n + 1)]
        pts += right + left[::-1]
        c.poly([(60, apex), (60 + w, bot - 8), (60 + w * 0.7, bot), (60, bot - 4), (60 - w * 0.7, bot),
                (60 - w, bot - 8)], NAVY)
        c.poly([(60, apex), (60 - w, bot - 8), (60 - w * 0.7, bot), (60, bot - 4)], SEA)
        # Зубцы бахромы.
        for j in range(1, 5):
            t = j / 5.0
            yy = apex + (bot - 8 - apex) * t
            c.line(60 - w * t, yy, 60 - w * t + 3, yy + 6, NAVY, 1)
            c.line(60 + w * t, yy, 60 + w * t - 3, yy + 6, NAVY, 1)
        c.poly([(60, bot - 6), (60 - w * 0.7, bot), (60 - w + 2, bot - 8), (60, bot - 11)], NAVY)
        # Блик на левой кромке.
        c.line(60 - 2, apex + 4, 60 - w * 0.8, bot - 10, AQUA, 1)
        c.line(60 - w * 0.5, apex + (bot - apex) * 0.5, 60 - w * 0.9, bot - 6, AQUA, 1)
    # Шишки и трава.
    for cx, cy in ((44, 150), (78, 120), (52, 84)):
        c.ellipse(cx, cy, 2, 3, TAN)
    for gx in (36, 44, 76, 86):
        c.line(gx, 239, gx - 2, 232, SEA, 1)
        c.line(gx, 239, gx + 2, 233, AQUA, 1)
    c.finish()
    return c


def boulder():
    """Замшелый валун у дороги, 96×64: круглая серая глыба, малый камень рядом, шапка мха,
    трещины и пучки травы у подошвы."""
    c = Canvas(96, 64)
    c.poly([(4, 63), (0, 44), (10, 24), (30, 10), (56, 8), (80, 20), (92, 42), (95, 63)], METAL)
    c.poly([(12, 40), (18, 26), (34, 15), (52, 13), (44, 26), (28, 40)], GREY)
    c.poly([(64, 63), (68, 48), (80, 42), (95, 50), (95, 63)], METAL)
    c.poly([(70, 50), (80, 44), (90, 49), (80, 52)], GREY)
    # Мох сверху, свисает пятнами.
    c.poly([(14, 26), (30, 12), (56, 10), (72, 18), (62, 22), (52, 19), (44, 25), (34, 22), (26, 31)], SEA)
    for x, y in ((24, 15), (38, 13), (52, 12), (66, 18), (30, 22), (46, 21)):
        c.set(x, y, AQUA)
        c.set(x + 1, y, AQUA)
    c.line(22, 30, 22, 36, SEA, 2)
    c.line(48, 24, 49, 30, SEA, 2)
    # Трещины.
    c.line(48, 34, 56, 46, DARK, 1)
    c.line(56, 46, 52, 58, DARK, 1)
    c.line(56, 46, 66, 50, DARK, 1)
    c.line(26, 46, 30, 56, DARK, 1)
    # Трава у подошвы.
    for gx in (6, 14, 40, 60, 90):
        c.line(gx, 63, gx - 2, 56, SEA, 1)
        c.line(gx + 1, 63, gx + 3, 55, AQUA, 1)
    return c.finish()


def haystack():
    """Стог сена, 48×64: конус из золотой соломы с тёмными штрихами, две перевязи верёвкой,
    жердь торчит из макушки, у основания пучки соломы."""
    rng = random.Random(191)
    c = Canvas(48, 64)
    for y in range(9, 61):
        t = (y - 9) / 51.0
        half = 3 + 19 * t ** 0.85 + 2.2 * math.sin(t * math.pi)
        for x in range(int(24 - half), int(24 + half) + 1):
            c.set(x, y, GOLD)
    c.ellipse(24, 58, 22, 4, GOLD)
    # Светлая левая сторона и тёмные штрихи соломы.
    for y in range(10, 60):
        t = (y - 9) / 51.0
        half = 3 + 19 * t ** 0.85 + 2.2 * math.sin(t * math.pi)
        c.set(24 - half + 2, y, SKIN)
        c.set(24 - half + 3, y, SKIN)
    for _ in range(60):
        y = rng.randint(14, 58)
        t = (y - 9) / 51.0
        half = (3 + 19 * t ** 0.85) * 0.85
        x = 24 + rng.uniform(-half, half)
        c.line(x, y, x + 2, y + 3, BRASS, 1)
    for _ in range(18):
        y = rng.randint(14, 56)
        t = (y - 9) / 51.0
        half = (3 + 19 * t ** 0.85) * 0.8
        x = 24 + rng.uniform(-half, half * 0.5)
        c.line(x, y, x + 2, y + 2, SKIN, 1)
    # Перевязи и жердь.
    for y in (28, 44):
        t = (y - 9) / 51.0
        half = 3 + 19 * t ** 0.85 + 2.2 * math.sin(t * math.pi)
        c.rect(24 - half, y, 24 + half, y + 1, TAN)
        c.rect(24 - half, y + 2, 24 + half, y + 2, DARK)
    c.rect(23, 0, 25, 12, TAN)
    c.rect(23, 0, 23, 11, SKIN)
    # Пучки у основания.
    for x, dy in ((4, 0), (10, 2), (36, 2), (43, 0)):
        c.line(x, 60 + dy, x + 2, 57 + dy, GOLD, 1)
        c.line(x + 2, 60 + dy, x + 4, 58 + dy, BRASS, 1)
    return c.finish()


def sign(right):
    """Указатель поворота, 96×112: деревянная стойка и доска-стрела в сторону поворота, красное
    поле в золотой кайме, три золотых шеврона, заклёпки."""
    c = Canvas(96, 112)
    d = 1 if right else -1

    def x(v):
        return 48 + d * (v - 48)

    # Стойка и каменный фундамент.
    c.rect(44, 50, 51, 111, TAN)
    c.rect(44, 50, 45, 111, SKIN)
    c.rect(48, 50, 51, 111, TAN)
    c.rect(50, 50, 51, 111, DARK)
    c.ellipse(48, 108, 14, 4, METAL)
    c.rect(34, 108, 61, 111, METAL)
    c.rect(34, 108, 61, 108, GREY)
    for sx in (40, 48, 56):
        c.rect(sx, 108, sx, 111, DARK)
    # Доска-стрела: золотая кайма, красное поле.
    outer = [(6, 16), (62, 16), (62, 4), (91, 30), (62, 56), (62, 44), (6, 44)]
    inner = [(10, 20), (66, 20), (66, 14), (82, 30), (66, 46), (66, 40), (10, 40)]
    c.poly([(x(px), py) for px, py in outer], GOLD)
    c.poly([(x(px), py) for px, py in inner], RED)
    c.line(x(7), 17, x(61), 17, WHITE, 1)
    # Шевроны в сторону поворота.
    for k in range(3):
        cx = 22 + k * 15
        c.poly([(x(cx), 23), (x(cx + 8), 30), (x(cx), 37), (x(cx + 4), 30)], GOLD)
    # Заклёпки на кайме.
    for px, py in ((12, 18), (12, 42), (58, 18), (58, 42)):
        c.set(x(px), py, WHITE)
    return c.finish()


def gatehouse():
    """Сторожка у дороги, 192×160 (место хижины): две каменные башни с красными коническими
    крышами и вымпелами, между ними стена с зубцами и аркой ворот с решёткой, над воротами
    знамя с гербом; кладка рядами с бликом, бойницы."""
    c = Canvas(192, 160)

    def stone(x0, y0, x1, y1):
        c.rect(x0, y0, x1, y1, METAL)
        for r, y in enumerate(range(y0, y1 + 1, 8)):
            c.rect(x0, y, x1, y, GREY)
            sh = 0 if r % 2 == 0 else 7
            for x in range(x0 + sh, x1, 14):
                c.rect(x, y + 1, x, min(y + 7, y1), DARK)
        c.rect(x0, y0, x0 + 1, y1, GREY)
        c.rect(x1 - 1, y0, x1, y1, DARK)

    # Стена между башнями и зубцы.
    stone(60, 84, 132, 159)
    for x in range(60, 132, 12):
        c.rect(x, 76, x + 7, 84, METAL)
        c.rect(x, 76, x + 7, 77, GREY)
    # Ворота: арка, решётка, брусчатка у порога.
    c.rect(80, 118, 112, 159, DARK)
    c.ellipse(96, 118, 16, 16, DARK)
    for x in range(84, 112, 6):
        c.rect(x, 104, x, 159, METAL)
    for y in range(110, 159, 10):
        c.rect(81, y, 111, y, METAL)
    c.rect(78, 117, 80, 159, GREY)
    c.rect(112, 117, 114, 159, GREY)
    for dx in range(-17, 18, 4):
        yy = 118 - int(math.sqrt(max(0.0, 17 * 17 - dx * dx)))
        c.rect(96 + dx, yy - 2, 96 + dx + 2, yy, GREY)
    # Знамя над воротами.
    c.rect(88, 84, 104, 86, TAN)
    c.poly([(89, 86), (103, 86), (103, 104), (96, 99), (89, 104)], RED)
    c.rect(95, 88, 97, 98, GOLD)
    c.rect(92, 91, 100, 92, GOLD)

    def tower(x0, x1, top, roof_top, pole):
        stone(x0, top, x1, 159)
        c.rect(x0 - 3, top - 2, x1 + 3, top + 3, DARK)
        c.rect(x0 - 3, top - 2, x1 + 3, top - 2, METAL)
        mid = (x0 + x1) // 2
        # Коническая крыша со швами и бликом.
        c.poly([(mid, roof_top), (x1 + 5, top - 2), (x0 - 5, top - 2)], RED)
        c.poly([(mid, roof_top), (x0 - 5, top - 2), (mid - 6, top - 2)], VIOLET)
        for k in range(1, 6):
            yy = roof_top + (top - 2 - roof_top) * k // 6
            half = (x1 - x0) // 2 + 5
            h = half * k // 6
            c.rect(mid - h, yy, mid + h, yy, PLUM)
        c.rect(mid, roof_top - pole, mid, roof_top, DARK)
        c.poly([(mid + 1, roof_top - pole), (mid + 14, roof_top - pole + 3), (mid + 1, roof_top - pole + 7)], RED)
        c.ellipse(mid, roof_top - pole, 2, 2, GOLD)
        # Бойницы.
        for yy in (top + 14, top + 52):
            c.rect(mid - 1, yy, mid + 1, yy + 12, K)
            c.rect(mid - 3, yy + 5, mid + 3, yy + 6, K)
        c.rect(x0, 148, x1, 159, DARK)
        c.rect(x0, 148, x1, 148, GREY)

    tower(10, 62, 58, 12, 12)
    tower(130, 182, 70, 26, 10)
    # Трава у подошвы.
    for gx in range(6, 188, 9):
        if 70 < gx < 124:
            continue
        c.line(gx, 159, gx - 1, 154, SEA, 1)
        c.line(gx + 3, 159, gx + 4, 153, AQUA, 1)
    c.finish()
    return c


def road_colors():
    """Лента цветов дороги 8×1: индекс это место в `ROAD_COLORS`."""
    c = Canvas(8, 1)
    for i in range(8):
        c.set(i, 0, i)
    return c


def sprites():
    """Ленты гонки в палитре спрайтов, ключи как у пиратов."""
    out = {
        "cart_hero": carts_strip(RED, False),
        "palm": oak(),
        "palm_b": pine(),
        "road_rock": boulder(),
        "road_barrel": haystack(),
        "sign_left": sign(False),
        "sign_right": sign(True),
        "road_hut": gatehouse(),
    }
    for i, accent in enumerate((SEA, GOLD, RED, AQUA)):
        out["cart_%d" % i] = carts_strip(accent, True)
    return out


def horizon():
    """Горизонт в своей палитре `CASTLES_SKY`."""
    return {"road_sky": sky(), "road_islands": islands(), "road_sea": sea()}


def road_palette():
    return {"road_colors": road_colors()}


def sheet_items():
    items = castles16.shaded(sprites())
    for key, canvas in horizon().items():
        items[key] = (canvas, CASTLES_SKY)
    for key, canvas in road_palette().items():
        items[key] = (canvas, ROAD_COLORS)
    return items


def preview(path, limit=1500, scale=2, pad=6, back=(0x6E, 0x9C, 0xC0, 255)):
    """Лист набора. Повозки режутся по три кадра в строку (480 пикселей), остальное по 512. Если
    лист выше `limit` пикселей, он режется на файлы `path`, `_b`, `_c`... Фон голубой, как небо
    за кадром игры: на тёмном не видно, держит ли обводка."""
    items = sheet_items()
    groups = [({}, 512)]
    height = 0
    for key, (canvas, pal) in items.items():
        mw = 480 if key.startswith("cart_") else 512
        h = (-(-canvas.w // mw) * (canvas.h + pad) + pad) * scale
        if groups[-1][0] and (height + h > limit or groups[-1][1] != mw):
            groups.append(({}, mw))
            height = 0
        groups[-1] = (groups[-1][0], mw)
        groups[-1][0][key] = (canvas, pal)
        height += h
    base, ext = os.path.splitext(path)
    for i, (grp, mw) in enumerate(groups):
        castles16.save_sheet(path if i == 0 else "%s_%s%s" % (base, "bcdefghij"[i - 1], ext), grp,
                             scale=scale, max_w=mw, back=back)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
