#!/usr/bin/env python3
"""Набор «Сладости» для гонки × 16/32-bit «псевдо-3D» (#137), зеркало `space_road16.py` и
`pixel_road16.py`: те же ключи, размеры холстов и порядок кадров, чтобы `racing_bit16.gd` брала
их без правок. Герой едет на эклере (вид сзади): две половинки заварного теста, между ними
розетки крема, сверху розовая глазурь с потёками и посыпкой, колёса из печенья-сэндвича ребром,
мачта карамельной тростью с вымпелом, правит пряничный человечек с красным бантом. Соперники на
кексах: гофрированная формочка цвета экипажа, шапка белого крема витками, колёса из печенья с
шоколадной крошкой, в креме сидит мармеладный мишка. У дороги дерево сахарной ваты и гигантский
леденец-спираль вместо пальм, торт со свечой вместо хижины, куски сахара, желе на блюдце,
указатели из печенья на карамельной трости. На горизонте пастельное небо с облаками ваты, горы
из шариков мороженого под шоколадным сиропом, розовый сироп вместо моря. Дорога шоколадная,
бордюр карамельной тростью, обочина бисквит.

Эклер, кексы и пропы в палитре `sweets16.PALETTE`, горизонт в своей (`SWEETS_SKY`), цвета
дороги лентой `road_colors` по местам `ROAD_COLORS`.

    python3 tools/sweets_road16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweets16  # noqa: E402
from sweets16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS,  # noqa: E402
                      METAL, DARK, RED, VIOLET, PLUM)

# Палитра горизонта: небо, облака ваты, сироп, горы мороженого. Места те же по смыслу, что у
# пиратов и космоса.
S0, S1, S2, S3, C0, C1, C2, M0, M1, M2, M3, I0, I1, I2, I3, SUN = range(16)
SWEETS_SKY = [
    (0x5C, 0xAE, 0xCC),  # S0  небо наверху
    (0x86, 0xCC, 0xD4),  # S1
    (0xBA, 0xE8, 0xDA),  # S2  мятный крем
    (0xFF, 0xE8, 0xD8),  # S3  небо у горизонта, сливки
    (0xF6, 0x9C, 0xC0),  # C0  розовый низ облака, тень клубничного шарика
    (0xFF, 0xCC, 0xDE),  # C1  облако ваты, клубничный шарик
    (0xFF, 0xFA, 0xF2),  # C2  свет облака, солнце, сливки
    (0xC2, 0x4A, 0x82),  # M0  сироп вдали
    (0xE2, 0x68, 0x9A),  # M1  сироп
    (0xF6, 0x90, 0xB6),  # M2  сироп у дороги
    (0xFF, 0xDA, 0xE8),  # M3  блик на сиропе
    (0xA4, 0xD8, 0xCC),  # I0  дальние шарики в дымке
    (0x7C, 0x48, 0x38),  # I1  шоколадный сироп на вершинах
    (0xFF, 0xEC, 0xBC),  # I2  ванильный шарик
    (0xE6, 0x35, 0x45),  # I3  вишня
    (0xF2, 0xD0, 0x86),  # SUN бисквит у кромки дороги, вафля
]

# Цвета дороги по местам ленты `road_colors` (демка берёт их по индексу).
ROAD_COLORS = [
    (0x8E, 0x58, 0x44),  # 0 шоколад светлый
    (0x80, 0x4C, 0x3C),  # 1 шоколад тёмный
    (0xE6, 0x35, 0x45),  # 2 бордюр красный, карамельная трость
    (0xFF, 0xF7, 0xEC),  # 3 бордюр белый
    (0xFF, 0xF0, 0xD4),  # 4 разметка глазурью
    (0xF2, 0xD0, 0x86),  # 5 бисквит светлый
    (0xE4, 0xBC, 0x70),  # 6 бисквит тёмный
    (0xFF, 0xE8, 0xD8),  # 7 дымка вдали
]

# Светлый и тёмный тон к цвету экипажа: складки формочки кекса.
_LIGHT = {SEA: AQUA, GOLD: WHITE, RED: VIOLET, AQUA: SKY}
_SHADE = {SEA: NAVY, GOLD: BRASS, RED: PLUM, AQUA: SEA}


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wellipse(c, cx, cy, rx, ry, col):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                _wset(c, x, y, col)


# --- Горизонт ----------------------------------------------------------------------------------

def _wcloud(c, cx, cy, s):
    """Облако сахарной ваты: клубы со светом сверху и розовым плоским низом, стыкуется по краю."""
    puffs = ((-13, 1, 5), (-6, -4, 7), (3, -6, 8), (12, -2, 6), (19, 2, 4))
    cells = set()
    for dx, dy, r in puffs:
        px, py, pr = cx + dx * s, cy + dy * s, r * s
        for y in range(int(py - pr - 1), int(py + pr + 2)):
            for x in range(int(px - pr - 1), int(px + pr + 2)):
                if (x - px) ** 2 + (y - py) ** 2 <= pr * pr and y <= cy + 3 * s:
                    cells.add((x, y))
    for x, y in cells:
        low = (x, y + 1) not in cells or (x, y + 2) not in cells or (x, y + 3) not in cells
        top = (x, y - 1) not in cells or (x - 1, y - 1) not in cells or (x, y - 2) not in cells
        _wset(c, x, y, C0 if low else (C2 if top else C1))


def sky():
    """Небо, 512×128, стыкуется по краям: голубая мята наверху, сливки у горизонта, блёстки
    сахарной пудры, солнце в мягком ореоле, облака сахарной ваты."""
    rng = random.Random(271)
    c = Canvas(512, 128)
    bands = [(0, S0), (34, S1), (66, S2), (98, S3)]
    for y in range(128):
        col = S0
        for start, b in bands:
            if y >= start:
                col = b
        for x in range(512):
            cur = col
            for i, (start, b) in enumerate(bands[1:]):
                if start <= y < start + 4 and (x + y) % 2 == 0:
                    cur = bands[i][1]
            c.set(x, y, cur)
    # Блёстки сахарной пудры: мелкие точки наверху, редкие крестики.
    for _ in range(90):
        c.set(rng.randint(0, 511), rng.randint(0, 60), S2 if rng.random() < 0.6 else C2)
    for _ in range(12):
        x = rng.randint(2, 509)
        y = rng.randint(2, 44)
        c.set(x, y, C2)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.set(x + dx, y + dy, S2)
    # Солнце: диск сливок в ореоле шашечкой.
    sx, sy = 372, 62
    for y in range(sy - 26, sy + 27):
        for x in range(sx - 26, sx + 27):
            d = math.hypot(x - sx, y - sy)
            if d <= 15:
                c.set(x, y, C2)
            elif d <= 19 and (x + y) % 2 == 0:
                c.set(x, y, C2)
            elif d <= 25 and (x + y) % 2 == 0 and (x - y) % 4 == 0:
                c.set(x, y, S3)
    # Облака ваты: крупные пониже, мелкие выше.
    for cx, cy, s in ((70, 84, 2.2), (232, 70, 1.6), (470, 88, 2.4), (150, 40, 1.1), (318, 30, 1.0),
                      (420, 108, 1.4), (20, 26, 0.9), (290, 104, 1.2)):
        _wcloud(c, cx, cy, s)
    return c


def _scoop(c, cx, cy, r, body, shade, light=None):
    """Шарик мороженого на горизонте: купол, ниже центра стенка до низа ленты; тень серпом
    справа снизу, блик слева сверху, по подолу бахрома подтаявшего края."""
    for y in range(int(cy - r), 40):
        half = r * math.sqrt(max(0.0, 1.0 - ((y - cy) / r) ** 2)) if y < cy else r
        for x in range(int(cx - half), int(cx + half) + 1):
            col = body
            if math.hypot(x - (cx - r * 0.28), y - (cy - r * 0.3)) > r * 0.98:
                col = shade
            elif light is not None and math.hypot(x - (cx - r * 0.42), y - (cy - r * 0.45)) < r * 0.2:
                col = light
            _wset(c, x, y, col)


def _syrup_cap(c, cx, cy, r, col):
    """Шапка шоколадного сиропа на макушке шарика с потёками разной длины."""
    for x in range(int(cx - r * 0.72), int(cx + r * 0.72) + 1):
        k = (x - cx) / r
        top = cy - r * math.sqrt(max(0.0, 1.0 - k * k))
        drip = r * (0.34 + 0.22 * math.sin(x * 1.1) + 0.12 * math.sin(x * 2.7 + 1.0))
        for y in range(int(top), int(top + max(2.0, drip)) + 1):
            _wset(c, x, y, col)


def islands():
    """Горы мороженого на горизонте, 512×40, прозрачный верх: дальние шарики в мятной дымке,
    ближние из клубничных и ванильных шариков под шоколадным сиропом, вишни на вершинах,
    вафельные треугольники."""
    c = Canvas(512, 40)
    # Дальняя гряда в дымке.
    for cx, r in ((24, 12), (52, 16), (118, 11), (150, 15), (222, 13), (250, 9), (368, 12), (398, 17),
                  (478, 13), (504, 9)):
        _scoop(c, cx, 40 - r * 0.9, r, I0, I0)
        for a in range(200, 250, 6):
            ra = math.radians(a)
            _wset(c, cx + math.cos(ra) * r * 0.7, 40 - r * 0.9 + math.sin(ra) * r * 0.7, S2)
    # Ближние горы: (центр, верхний шарик, боковые шарики).
    peaks = ((300, 12, (C1, C0, C2), ((-17, 29, 14, I2, SUN, C2), (17, 30, 13, C1, C0, C2), (0, 34, 10, I2, SUN, None))),
             (86, 9, (I2, SUN, C2), ((-12, 33, 10, C1, C0, C2), (12, 32, 11, I2, SUN, C2))),
             (190, 8, (C1, C0, C2), ((10, 34, 9, I2, SUN, C2), (-9, 35, 8, C1, C0, None))),
             (440, 10, (C1, C0, C2), ((-14, 32, 11, I2, SUN, C2), (13, 33, 10, C1, C0, C2))))
    for cx, r, (body, shade, light), sides in peaks:
        top_cy = 39 - r * 2.2
        # Вафельный треугольник торчит из-за вершины.
        for i in range(int(r * 1.5)):
            for dx in range(-i // 3, i // 3 + 1):
                x, y = cx + r * 0.9 + dx - i * 0.3, top_cy - r * 0.9 + i
                _wset(c, x, y, I1 if (int(x) + int(y)) % 3 == 0 else SUN)
        _scoop(c, cx, top_cy, r, body, shade, light)
        _syrup_cap(c, cx, top_cy, r, I1)
        _wellipse(c, cx, top_cy - r - 1.5, 2.2, 2.2, I3)
        _wset(c, cx - 1, top_cy - r - 3, C2)
        _wset(c, cx + 1, top_cy - r - 4, I1)
        _wset(c, cx + 2, top_cy - r - 5, I1)
        for dx, cy, sr, sbody, sshade, slight in sides:
            _scoop(c, cx + dx, cy, sr, sbody, sshade, slight)
            if sbody == I2:
                # Шоколадная крошка на ванильных шариках.
                for k, (ox, oy) in enumerate(((-0.5, -0.1), (0.1, -0.6), (0.35, 0.05), (-0.15, 0.4), (0.6, -0.4))):
                    _wset(c, cx + dx + ox * sr, cy + oy * sr, I1)
    return c


def sea():
    """Розовый сироп от горизонта, 512×24: тёмная малина вдали, светлее у дороги, блики
    штрихами (чем ближе, тем длиннее), плавают зефирки, у нижней кромки полоса бисквита."""
    rng = random.Random(273)
    c = Canvas(512, 24)
    for y in range(24):
        col = M0 if y < 5 else (M1 if y < 14 else M2)
        c.rect(0, y, 511, y, col)
        if y in (5, 14):
            for x in range(0, 512, 2):
                c.set(x + (y % 2), y, M0 if y == 5 else M1)
    for _ in range(70):
        y = rng.randint(1, 20)
        x = rng.uniform(0, 512)
        w = 1 + y // 3 + rng.randint(0, 2)
        for i in range(-w, w + 1):
            _wset(c, x + i, y, M3 if y > 8 or rng.random() < 0.5 else M1)
    # Тягучие волны: тёмные дуги под бликами.
    for _ in range(26):
        y = rng.randint(7, 20)
        x = rng.uniform(0, 512)
        w = 3 + y // 3
        for i in range(-w, w + 1):
            _wset(c, x + i, y + (1 if abs(i) < w - 1 else 0), M1 if y >= 14 else M0)
    # Зефирки на плаву: белый верх, розовая тень в сиропе.
    for x, y in ((40, 12), (132, 17), (214, 9), (296, 18), (388, 13), (462, 16)):
        w = 2 + y // 6
        for i in range(-w, w + 1):
            _wset(c, x + i, y, C2)
            _wset(c, x + i, y + 1, C1 if abs(i) < w else M0)
            _wset(c, x + i, y + 2, M0)
    c.rect(0, 22, 511, 23, SUN)
    return c


# --- Эклер, кексы и пропы (палитра спрайтов) ----------------------------------------------------

def _cane(c, pts, t, period=6, a=RED, b=WHITE):
    """Карамельная трость по ломаной: кружки вдоль пути, цвет чередуется по длине."""
    s = 0.0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) * 2))
        for j in range(n + 1):
            k = j / n
            col = a if int(s + k * n * 0.5) // period % 2 == 0 else b
            c.ellipse(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, t / 2.0, t / 2.0, col)
        s += n * 0.5


def _swirl(c, cx, cy, r, a, b, twist=0.16, arms=8):
    """Диск леденца-спирали: секторы двух цветов закручены по радиусу."""
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            d = math.hypot(x - cx, y - cy)
            if d > r:
                continue
            t = math.atan2(y - cy, x - cx) + d * twist
            c.set(x, y, a if int(math.floor(t / (2 * math.pi / arms))) % 2 == 0 else b)


def _sandwich_wheel(c, cx, cy, r, phase):
    """Колесо эклера сзади: печенье-сэндвич ребром, два шоколадных диска и крем между ними,
    тиснение на дисках бежит вниз (`phase` 0..1)."""
    cx = int(round(cx))
    w = 8
    for y in range(cy - r, cy + r + 1):
        edge = r - abs(y - cy)
        inset = 3 if edge < 1 else (2 if edge < 2 else (1 if edge < 4 else 0))
        c.rect(cx - w + inset, y, cx - 3, y, DARK)
        c.rect(cx + 3, y, cx + w - inset, y, DARK)
        if edge >= 1:
            c.rect(cx - 2, y, cx + 2, y, WHITE)
    step = 6
    off = int(phase * step)
    for y in range(cy - r + 3 + off, cy + r - 3, step):
        c.rect(cx - w + 1, y, cx - 4, y + 1, METAL)
        c.rect(cx + 4, y, cx + w - 1, y + 1, METAL)
        c.rect(cx - 2, y + 3, cx + 2, y + 3, GREY)


def eclair(lean, phase, accent):
    """Эклер со спины, 160×104: два колеса из печенья-сэндвича, заварное тесто в две половинки,
    крем розетками, розовая глазурь с потёками, табличка цвета `accent` и такой же вымпел на
    мачте карамельной тростью; правит пряничный человечек. `lean` −1..1 крен."""
    c = Canvas(160, 104)
    sh = lean * 6
    _sandwich_wheel(c, 22 + sh * 0.3, 78, 24, phase)
    _sandwich_wheel(c, 138 + sh * 0.3, 78, 24, phase)
    # Ось соломкой и вафельное днище.
    c.rect(24, 84, 136, 88, BRASS)
    c.rect(24, 84, 136, 85, GOLD)
    c.rect(34, 88, 126, 94, GOLD)
    for x in range(34, 127, 6):
        c.rect(x, 88, x, 94, BRASS)
    c.rect(34, 91, 126, 91, BRASS)
    # Груз и мачты ставятся раньше корпуса: их низ утоплен в глазурь.
    # Мачта карамельной тростью с вымпелом у правого края, шарик карамели на макушке.
    mx = 123 + sh * 1.4
    _cane(c, [(mx, 4), (mx + (sh * 0.9 - sh * 1.4), 56)], 3.4, 5)
    flap = 3 * math.sin(phase * math.pi * 2)
    c.poly([(mx + 2, 5), (mx + 26, 11 + flap), (mx + 2, 19)], accent)
    c.line(mx + 5, 12, mx + 16, 12 + flap * 0.5, WHITE, 1)
    c.ellipse(mx, 3, 2.5, 2.5, GOLD)
    # Мятный леденец-спираль на палочке слева.
    c.line(46 + sh, 52, 40 + sh * 1.2, 30, WHITE, 2)
    _swirl(c, 39 + sh * 1.2, 24, 9, SEA, WHITE, 0.5, 6)
    # Вишня с черешком и коробка конфет с лентой.
    c.line(58 + sh, 32, 63 + sh, 24, DARK, 1)
    c.ellipse(58 + sh, 38, 7, 7, RED)
    c.rect(55 + sh, 34, 56 + sh, 35, WHITE)
    c.rect(98 + sh, 30, 116 + sh, 48, VIOLET)
    c.rect(98 + sh, 30, 116 + sh, 33, PLUM)
    c.rect(106 + sh, 30, 108 + sh, 48, WHITE)
    c.rect(98 + sh, 38, 116 + sh, 39, WHITE)
    c.ellipse(104 + sh, 28, 3, 2, GOLD)
    c.ellipse(110 + sh, 28, 3, 2, GOLD)
    # Пряничный человечек со спины: тело с зигзагом глазури, руки в стороны с каймой, бант,
    # круглая голова.
    x0 = 72 + sh * 1.2
    for side in (-1, 1):
        sx = x0 + 8 + side * 9
        c.line(sx, 29, sx + side * 9, 38, SKIN, 7)
        px, py = sx + side * 6.5, 35.5
        c.line(px - side * 2.6, py + 2.6, px + side * 2.6, py - 2.6, WHITE, 2)
    c.ellipse(x0 + 8, 35, 11, 12, SKIN)
    for k in range(13):
        c.set(x0 + 2 + k, 34 + (0, 1, 2, 1)[k % 4], WHITE)
    c.rect(x0 + 2, 23, x0 + 14, 26, RED)
    c.poly([(x0 - 5, 20), (x0 + 3, 24), (x0 - 5, 29)], RED)
    c.poly([(x0 + 21, 20), (x0 + 13, 24), (x0 + 21, 29)], RED)
    c.ellipse(x0 + 8, 13, 10, 10, SKIN)
    c.rect(x0 + 2, 9, x0 + 4, 10, GOLD)
    # Нижняя половинка теста: трещинки корочки, табличка экипажа, мармеладки-фонари.
    c.ellipse(80 + sh * 0.6, 76, 54, 15, GOLD)
    for x, y in ((38, 80), (50, 86), (62, 71), (104, 86), (118, 80), (100, 71), (74, 88), (44, 72), (116, 72)):
        c.line(x + sh * 0.6, y, x + sh * 0.6 + 4, y + 2, BRASS, 1)
    c.rect(66 + sh * 0.8, 75, 94 + sh * 0.8, 85, DARK)
    c.rect(68 + sh * 0.8, 77, 92 + sh * 0.8, 83, accent)
    c.rect(70 + sh * 0.8, 78, 78 + sh * 0.8, 78, WHITE)
    for x in (36, 124):
        col = RED if accent != RED else AQUA
        c.ellipse(x + sh * 0.6, 77, 5, 5, col)
        c.rect(x + sh * 0.6 - 2, 74, x + sh * 0.6 - 1, 75, WHITE)
    # Верхняя половинка, между половинками розетки крема.
    c.ellipse(80 + sh, 55, 50, 13, GOLD)
    c.ellipse(80 + sh, 60, 46, 7, BRASS)
    for x in range(34, 127, 8):
        k = sh * 0.8
        c.ellipse(x + k, 65, 5.5, 5, WHITE)
        c.line(x + k - 3, 68, x + k + 3, 68, GREY, 1)
        c.rect(x + k, 63, x + k + 1, 63, GREY)
    # Глазурь шапкой: потёки разной длины, блик, посыпка.
    c.ellipse(80 + sh, 51, 46, 10, VIOLET)
    for x, ln in ((40, 4), (51, 8), (64, 5), (78, 9), (92, 5), (106, 8), (119, 4)):
        c.rect(x + sh - 2, 54, x + sh + 2, 55 + ln, VIOLET)
        c.ellipse(x + sh, 55 + ln, 2.6, 2.6, VIOLET)
    c.line(48 + sh, 47, 66 + sh, 44, WHITE, 1)
    c.line(44 + sh, 50, 47 + sh, 48, WHITE, 1)
    for i, (x, y) in enumerate(((54, 52), (70, 49), (88, 53), (112, 50), (98, 46), (62, 56), (120, 54),
                                (42, 54), (80, 57), (104, 57))):
        col = (WHITE, AQUA, GOLD, RED, SEA)[i % 5]
        c.rect(x + sh, y, x + sh + (2 if i % 2 == 0 else 0), y + (0 if i % 2 == 0 else 2), col)
    c.finish()
    return c


def cupcake(lean, phase, accent):
    """Кекс со спины, 160×104: гофрированная формочка цвета `accent`, шапка белого крема в три
    витка с посыпкой, по бокам колёса из печенья с шоколадной крошкой (на месте колёс эклера,
    силуэт той же ширины), в креме сидит мармеладный мишка, на вафельной трубочке флажок;
    драже по поясу мигают по `phase`."""
    c = Canvas(160, 104)
    sh = lean * 6
    blink = 1 if phase < 0.25 else 0
    # Колёса: печенье в три четверти, крошка бежит вниз.
    for gx, side in ((20, -1), (140, 1)):
        x = gx + sh * 0.4
        c.ellipse(x, 80, 10, 21, BRASS)
        c.ellipse(x + side * 1.5, 80, 8, 19, GOLD)
        for dx, dy in ((-2, -13), (3, -5), (-3, 4), (2, 12), (0, -1)):
            yy = (dy + 16 + (0 if blink else 6)) % 32 - 16
            c.rect(x + side * 1.5 + dx, 80 + yy, x + side * 1.5 + dx + 1, 80 + yy + 1, DARK)
    # Ось: шоколадная палочка.
    c.rect(24, 82, 136, 86, METAL)
    c.rect(24, 82, 136, 82, BRASS)
    # Вафельная трубочка с флажком на корме справа.
    c.line(122 + sh * 1.3, 52, 132 + sh * 1.4, 14, BRASS, 4)
    c.line(121 + sh * 1.3, 52, 131 + sh * 1.4, 14, GOLD, 1)
    c.poly([(133 + sh * 1.4, 12), (149 + sh * 1.4, 19), (135 + sh * 1.4, 27)], accent)
    c.ellipse(132 + sh * 1.4, 12, 2.5, 2.5, GOLD)
    # Формочка: трапеция в складку, зубчатый верх, пояс с драже.
    light, shade = _LIGHT[accent], _SHADE[accent]
    c.poly([(28 + sh, 56), (132 + sh, 56), (118 + sh * 0.5, 97), (42 + sh * 0.5, 97)], accent)
    for i in range(14):
        xt = 28 + i * 8.0 + sh
        xb = 42 + i * 5.85 + sh * 0.5
        c.ellipse(xt + 4, 55, 4, 4, accent)
        if i > 0:
            c.line(xt, 57, xb, 96, shade, 1)
        if i < 13:
            c.line(xt + 3, 60, xb + 2.4, 96, light, 1)
    c.rect(43 + sh * 0.5, 88, 117 + sh * 0.5, 92, DARK)
    for i, x in enumerate(range(47, 116, 9)):
        on = (i + blink) % 2 == 0
        c.rect(x + sh * 0.5, 89, x + sh * 0.5 + 3, 91, GOLD if on else METAL)
    # Румяная шапка кекса над формочкой.
    c.ellipse(80 + sh, 53, 55, 9, BRASS)
    c.ellipse(80 + sh, 51, 53, 8, GOLD)
    # Мишка: плечи ставятся до верхнего витка крема, голова и уши после.
    cx = 80 + sh * 1.2
    c.ellipse(cx, 27, 14, 9, RED)
    # Крем: три витка, у каждого тень по подолу и борозды.
    for cy, rx, ry, k in ((46, 46, 10, 1.0), (37, 34, 8, 1.1), (30, 22, 6, 1.2)):
        c.ellipse(80 + sh * k, cy + 2, rx, ry, GREY)
        c.ellipse(80 + sh * k, cy, rx, ry - 1, WHITE)
        for j in range(-3, 4):
            gx = 80 + sh * k + j * rx * 0.27
            c.line(gx, cy - ry * 0.5, gx + 4, cy + ry * 0.6, GREY, 1)
    for i, (x, y) in enumerate(((46, 46), (62, 50), (84, 49), (104, 47), (118, 45), (58, 38), (76, 40),
                                (100, 38), (70, 31), (92, 31))):
        col = (RED, AQUA, GOLD, VIOLET, SEA)[i % 5]
        c.rect(x + sh, y, x + sh + (2 if i % 2 == 0 else 0), y + (0 if i % 2 == 0 else 2), col)
    c.ellipse(cx - 9, 6, 4.5, 4.5, RED)
    c.ellipse(cx + 9, 6, 4.5, 4.5, RED)
    c.ellipse(cx, 14, 12, 10, RED)
    # Блик мармелада на затылке и плече.
    c.line(cx - 7, 11, cx - 4, 7, WHITE, 1)
    c.rect(cx - 8, 13, cx - 8, 14, WHITE)
    c.line(cx + 5, 19, cx + 8, 16, VIOLET, 1)
    c.rect(cx - 10, 4, cx - 9, 4, VIOLET)
    c.rect(cx + 8, 4, cx + 9, 4, VIOLET)
    c.finish()
    return c


def carts_strip(accent, rival):
    """Три крена (влево, прямо, вправо) по два кадра: лента 6 кадров по 160, порядок как у пиратов."""
    frames = []
    for lean in (-1.0, 0.0, 1.0):
        for ph in (0.0, 0.5):
            frames.append(cupcake(lean, ph, accent) if rival else eclair(lean, ph, accent))
    return strip(frames)


def _puff(c, cx, cy, r, col, shade, light):
    """Ком сахарной ваты: гроздь клубов, тень по подолу, тонкие завитки волокон, блики сверху."""
    blobs = [(cx, cy, r * 0.72)]
    for i in range(7):
        a = i * 2 * math.pi / 7 + 0.4
        blobs.append((cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.52, r * (0.5 + 0.06 * (i % 3))))
    cells = set()
    for bx, by, br in blobs:
        for y in range(int(by - br - 1), int(by + br + 2)):
            for x in range(int(bx - br - 1), int(bx + br + 2)):
                if (x - bx) ** 2 + (y - by) ** 2 <= br * br:
                    cells.add((x, y))
    rim = max(2, int(r / 8))
    for x, y in cells:
        d = math.hypot(x - cx, y - cy)
        a = math.atan2(y - cy, x - cx)
        cur = col
        if any((x, y + k) not in cells for k in range(1, rim + 1)):
            cur = shade
        elif d > r * 0.2 and ((a + d * 0.11) % 0.9) < 0.1:
            cur = shade
        c.set(x, y, cur)
    for bx, by, br in blobs:
        for deg in range(205, 262, 2):
            ra = math.radians(deg)
            x, y = int(bx + math.cos(ra) * br * 0.72), int(by + math.sin(ra) * br * 0.72)
            if (x, y) in cells:
                c.set(x, y, light)


def cotton_tree():
    """Дерево сахарной ваты у обочины, 120×240 (место пальмы): изогнутый ствол витой карамелью,
    две ветки, большой розовый ком ваты наверху и два поменьше на ветках, у ствола мятные кусты."""
    c = Canvas(120, 240)
    bend = -14
    pts = []
    for i in range(180):
        k = i / 179
        pts.append((60 + bend * math.sin(k * math.pi), 239 - i))
    # Ветки под комья ваты.
    c.line(pts[70][0], pts[70][1], 24, 132, BRASS, 4)
    c.line(pts[96][0], pts[96][1], 97, 112, BRASS, 4)
    c.line(pts[70][0], pts[70][1] - 1, 24, 131, GOLD, 1)
    c.line(pts[96][0], pts[96][1] - 1, 97, 111, GOLD, 1)
    # Ствол: витая карамель, полосы наискось.
    for i, (x, y) in enumerate(pts):
        w = 8 - i / 45
        for dx in range(int(-w), int(w) + 1):
            c.set(x + dx, y, GOLD if ((i + dx * 1.3) // 9) % 2 == 0 else BRASS)
        c.set(x - int(w) + 1, y, WHITE if (i // 9) % 2 == 0 else GOLD)
    top = pts[-1]
    _puff(c, top[0] + 2, top[1] - 4, 43, VIOLET, PLUM, WHITE)
    _puff(c, 22, 122, 17, WHITE, GREY, SKY)
    _puff(c, 98, 102, 15, VIOLET, PLUM, WHITE)
    # Мятные кусты у основания: шарики с драже.
    for bx, r in ((30, 15), (92, 12), (76, 8)):
        c.ellipse(bx, 239 - r * 0.6, r, r * 0.8, SEA)
        c.ellipse(bx - 2, 239 - r * 0.7, r * 0.75, r * 0.6, AQUA)
        c.ellipse(bx - r * 0.35, 239 - r * 0.95, r * 0.3, r * 0.2, SKY)
        for k in range(3):
            c.rect(bx - r * 0.5 + k * r * 0.5, 239 - r * 0.5 + (k % 2) * 3, bx - r * 0.5 + k * r * 0.5 + 1,
                   239 - r * 0.5 + (k % 2) * 3 + 1, (WHITE, VIOLET, WHITE)[k])
    c.finish()
    return c


def lolly_tree():
    """Гигантский леденец-спираль у обочины, 120×240 (место второй пальмы): красно-белый диск на
    белой палочке с мятным бантом, у подножия мятный леденец поменьше и карамельная трость."""
    c = Canvas(120, 240)
    # Палочка: белая, тень справа.
    c.rect(56, 100, 63, 239, WHITE)
    c.rect(62, 100, 63, 239, GREY)
    # Трость крюком справа и малый мятный леденец слева.
    hook = [(98, 239), (98, 176)]
    for deg in range(180, 381, 12):
        ra = math.radians(deg)
        hook.append((108 + math.cos(ra) * 10, 176 + math.sin(ra) * 10))
    _cane(c, hook, 8, 7)
    c.rect(22, 200, 25, 239, WHITE)
    c.rect(25, 200, 25, 239, GREY)
    _swirl(c, 24, 186, 17, SEA, WHITE, 0.3, 6)
    for deg in range(200, 260, 3):
        ra = math.radians(deg)
        c.set(24 + math.cos(ra) * 13, 186 + math.sin(ra) * 13, SKY)
    # Большой диск: спираль, тёмный ободок снизу справа, блик дугой слева сверху.
    cx, cy, r = 60, 58, 52
    _swirl(c, cx, cy, r, RED, WHITE, 0.15, 10)
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d = math.hypot(x - cx, y - cy)
            if d > r:
                continue
            a = math.degrees(math.atan2(y - cy, x - cx)) % 360
            cur = c.get(x, y)
            if d > r - 4 and (a < 110 or a > 320):
                c.set(x, y, PLUM if cur == RED else GREY)
            elif r - 13 < d < r - 9 and 195 < a < 255:
                c.set(x, y, VIOLET if cur == RED else SKY)
    c.ellipse(cx, cy, 3, 3, WHITE)
    # Бант под диском: два крыла, узел, хвосты.
    c.poly([(60, 120), (36, 108), (38, 132)], AQUA)
    c.poly([(60, 120), (84, 108), (82, 132)], AQUA)
    c.poly([(60, 120), (44, 114), (44, 126)], SEA)
    c.poly([(60, 120), (76, 114), (76, 126)], SEA)
    c.line(57, 124, 48, 146, AQUA, 4)
    c.line(63, 124, 72, 148, AQUA, 4)
    c.rect(55, 115, 65, 125, SEA)
    c.rect(57, 117, 60, 118, SKY)
    c.finish()
    return c


def _cube(c, rng, x, y, w, h, d):
    """Кусок сахара: белый верх, зернистая передняя грань, боковая в тени, искры."""
    c.poly([(x, y + d), (x + d, y), (x + w + d, y), (x + w, y + d)], WHITE)
    c.rect(x, y + d, x + w, y + d + h, WHITE)
    c.poly([(x + w + 1, y + d), (x + w + d, y + 1), (x + w + d, y + h), (x + w + 1, y + d + h)], GREY)
    c.line(x, y + d, x + w, y + d, GREY, 1)
    c.line(x + 1, y + d + 1, x + w - 1, y + d + 1, SKY, 1)
    for _ in range(int(w * h / 14)):
        gx, gy = rng.randint(x + 1, x + w - 1), rng.randint(y + d + 3, y + d + h - 1)
        c.set(gx, gy, GREY)
        if rng.random() < 0.4:
            c.set(gx + 1, gy, GREY)
    for _ in range(int(w * d / 12)):
        gy = rng.randint(y + 1, y + d - 1)
        gx = rng.randint(x + (d - (gy - y)) + 1, x + (d - (gy - y)) + w - 1)
        c.set(gx, gy, SKY if rng.random() < 0.5 else GREY)
    for _ in range(int(d * h / 16)):
        gx = rng.randint(x + w + 2, x + w + d - 1)
        c.set(gx, rng.randint(y + d, y + h), WHITE)


def sugar_pile():
    """Куски сахара у дороги, 96×64 (место камня): три кубика горкой, зерно на гранях, крошки."""
    rng = random.Random(283)
    c = Canvas(96, 64)
    _cube(c, rng, 3, 26, 40, 28, 9)
    _cube(c, rng, 50, 32, 34, 22, 9)
    # Тень под верхним куском на гранях нижних.
    c.poly([(24, 37), (58, 37), (66, 29), (70, 29), (62, 39), (24, 39)], GREY)
    _cube(c, rng, 24, 3, 34, 24, 9)
    for x, s in ((44, 3), (88, 4), (0, 2), (60, 2)):
        c.rect(x, 63 - s, x + s + 1, 63, WHITE)
        c.rect(x + s, 63 - s + 1, x + s + 1, 63, GREY)
    return c.finish()


def jelly():
    """Желе на блюдце, 48×64 (место бочки): красный купол в рёбрах формы, блик, шапка сливок с
    вишней, белое блюдце."""
    c = Canvas(48, 64)
    c.ellipse(24, 59, 23, 4.5, WHITE)
    c.rect(6, 62, 42, 63, GREY)
    c.rect(2, 58, 6, 58, SKY)
    for y in range(18, 59):
        k = (y - 18) / 40.0
        half = 11 + 6 * k ** 0.8
        c.rect(24 - half, y, 24 + half, y, RED)
    # Рёбра формы расходятся книзу, между ними светлые грани.
    for i in range(-3, 4):
        xt, xb = 24 + i * 3.3, 24 + i * 5.1
        c.line(xt, 20, xb, 57, PLUM, 1)
        if i < 3:
            c.line(xt + 1.6, 24, xb + 2.5, 50, VIOLET if i in (-3, -2) else RED, 1)
    c.ellipse(24, 18, 11, 4, VIOLET)
    c.line(14, 28, 11, 48, WHITE, 2)
    c.rect(16, 24, 17, 26, WHITE)
    # Сливки и вишня.
    c.ellipse(24, 14, 8, 4.5, WHITE)
    c.ellipse(24, 10, 5.5, 3.5, WHITE)
    c.line(19, 15, 29, 15, GREY, 1)
    c.ellipse(24, 4.5, 3.6, 3.6, RED)
    c.set(23, 3, WHITE)
    return c.finish()


def sign(right):
    """Указатель поворота, 96×112: печенье с зубчатым краем на карамельной трости, сверху
    глазурь с потёками, шоколадные шевроны в сторону поворота, драже по углам, внизу мармеладка."""
    c = Canvas(96, 112)
    _cane(c, [(47.5, 52), (47.5, 108)], 8, 6)
    for y, half in enumerate((6, 9, 11, 12, 13, 13)):
        c.rect(48 - half, 106 + y, 47 + half, 106 + y, VIOLET)
    c.rect(40, 108, 42, 108, WHITE)
    c.rect(4, 4, 91, 56, GOLD)
    c.rect(7, 7, 88, 53, GOLD)
    # Зубчатый край печенья: выемки по периметру, ряд проколов внутри.
    for x in range(4, 92):
        if (x - 4) % 8 in (6, 7):
            c.px[4][x] = None
            c.px[56][x] = None
    for y in range(4, 57):
        if (y - 4) % 8 in (6, 7) and y < 52:
            c.px[y][4] = None
            c.px[y][91] = None
    for x in range(10, 88, 6):
        c.set(x, 50, BRASS)
    for y in range(14, 50, 6):
        c.set(8, y, BRASS)
        c.set(87, y, BRASS)
    c.rect(5, 53, 90, 55, BRASS)
    # Глазурь по верху с потёками.
    c.rect(5, 5, 90, 9, WHITE)
    for x in range(8, 88, 9):
        ln = 2 + (x * 7) % 5
        c.rect(x, 10, x + 2, 10 + ln, WHITE)
    d = 1 if right else -1
    for k in range(3):
        cx = 48 + d * (k * 20 - 20)
        c.poly([(cx - d * 8, 17), (cx + d * 10, 32), (cx - d * 8, 47), (cx - d * 2, 32)], DARK)
        c.line(cx - d * 7, 19, cx + d * 7, 31, METAL, 1)
    for i, (x, y) in enumerate(((9, 14), (86, 14), (9, 47), (86, 47))):
        c.rect(x - 1, y - 1, x + 1, y + 1, (RED, AQUA, AQUA, RED)[i])
    return c.finish()


def _tier(c, x0, x1, y0, y1, body, side, layer, icing, icing_shade, seed):
    """Ярус торта: корж с прослойками, тень справа, шапка глазури с потёками, по низу розетки
    крема."""
    c.rect(x0, y0, x1, y1, body)
    c.rect(x1 - 8, y0, x1, y1, side)
    mid = (y0 + y1) // 2
    for y in (mid - 3, mid + 7):
        c.rect(x0, y, x1, y + 2, layer)
    c.rect(x0 - 2, y0 - 2, x1 + 2, y0 + 4, icing)
    for x in range(x0 - 2, x1 + 3):
        ln = 4 + 5 * (0.5 + 0.5 * math.sin(x * 0.42 + seed)) + 2 * math.sin(x * 1.3 + seed)
        c.rect(x, y0 + 4, x, y0 + 4 + max(0, int(ln)), icing)
    c.rect(x1 - 6, y0 - 1, x1 + 2, y0 + 3, icing_shade)
    c.line(x0 + 3, y0, x0 + (x1 - x0) * 0.4, y0, WHITE if icing != WHITE else SKY, 1)
    for x in range(x0 + 3, x1 - 1, 9):
        c.ellipse(x + 1, y1 - 2, 4, 3.5, WHITE)
        c.rect(x, y1, x + 3, y1, GREY)


def cake():
    """Торт со свечой у дороги, 192×160 (место хижины): три яруса на блюде, сливочный, шоколадный
    и бисквитный, глазурь с потёками, вишни на уступах, наверху полосатая свеча с огнём."""
    c = Canvas(192, 160)
    # Блюдо на ножке.
    c.rect(4, 148, 187, 153, WHITE)
    c.rect(4, 152, 187, 153, GREY)
    c.poly([(60, 154), (132, 154), (146, 159), (46, 159)], GREY)
    # Свеча ставится раньше верхнего яруса: низ утоплен в глазурь.
    for y in range(12, 44):
        for x in range(91, 101):
            c.set(x, y, AQUA if ((x + y) // 5) % 2 == 0 else WHITE)
    c.rect(99, 12, 100, 43, SEA)
    c.rect(95, 8, 96, 12, DARK)
    c.ellipse(95.5, 5, 4, 5.5, GOLD)
    c.poly([(92, 4), (95.5, -4), (99, 4)], GOLD)
    c.ellipse(95.5, 6.5, 1.8, 2.6, WHITE)
    # Ярусы снизу вверх.
    _tier(c, 16, 175, 104, 147, WHITE, GREY, GOLD, VIOLET, PLUM, 0.0)
    _tier(c, 42, 149, 66, 101, METAL, DARK, DARK, WHITE, GREY, 1.7)
    _tier(c, 66, 125, 40, 63, GOLD, BRASS, RED, VIOLET, PLUM, 3.1)
    # Гирлянда крема на шоколадном ярусе и драже.
    for i, x in enumerate(range(48, 142, 4)):
        c.rect(x, 86 + int(3 * abs(math.sin(i * 0.52))), x + 1, 87 + int(3 * abs(math.sin(i * 0.52))), WHITE)
    for i, x in enumerate(range(54, 140, 12)):
        c.rect(x, 93, x + 2, 95, (VIOLET, AQUA, GOLD)[i % 3])
    # Сердечки на нижнем ярусе.
    for x in range(30, 160, 22):
        c.ellipse(x - 2, 130, 2.6, 2.6, RED)
        c.ellipse(x + 2, 130, 2.6, 2.6, RED)
        c.poly([(x - 5, 131), (x + 5, 131), (x, 137)], RED)
        c.set(x - 3, 129, WHITE)
    # Вишни на уступах ярусов, с черешками.
    for x, y in ((24, 97), (34, 96), (158, 96), (168, 97), (50, 59), (140, 59)):
        c.line(x, y - 4, x + 3, y - 10, DARK, 1)
        c.ellipse(x, y, 4.5, 4.5, RED)
        c.rect(x - 2, y - 2, x - 1, y - 2, WHITE)
    return c.finish()


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
        "palm": cotton_tree(),
        "palm_b": lolly_tree(),
        "road_rock": sugar_pile(),
        "road_barrel": jelly(),
        "sign_left": sign(False),
        "sign_right": sign(True),
        "road_hut": cake(),
    }
    for i, accent in enumerate((SEA, GOLD, RED, AQUA)):
        out["cart_%d" % i] = carts_strip(accent, True)
    return out


def horizon():
    """Горизонт в своей палитре `SWEETS_SKY`."""
    return {"road_sky": sky(), "road_islands": islands(), "road_sea": sea()}


def road_palette():
    return {"road_colors": road_colors()}


def preview(path):
    items = sweets16.shaded(sprites())
    for key, canvas in horizon().items():
        items[key] = (canvas, SWEETS_SKY)
    for key, canvas in road_palette().items():
        items[key] = (canvas, ROAD_COLORS)
    sweets16.save_sheet(path, items, scale=2, max_w=512)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
