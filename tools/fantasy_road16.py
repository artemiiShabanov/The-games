#!/usr/bin/env python3
"""Набор «Фэнтези» для гонки × 16/32-bit «псевдо-3D» (#137), зеркало `space_road16.py` и
`pixel_road16.py`: те же ключи, размеры холстов и порядок кадров, чтобы `racing_bit16.gd` брала
их без правок. Герой едет на гномьей вагонетке (вид сзади): дощатый кузов трапецией в железных
обручах, узкие железные колёса, в кузове большой бирюзовый кристалл, на шесте вымпел и фонарь,
правит юный маг в синей остроконечной шляпе. Соперники на гоблинских вагонетках: кривой тёмный
короб с костяными шипами и черепом на борту, ушастый гоблин с дубиной, рваный флаг на палке.
У дороги дерево с сиреневой листвой и лианами и гигантский цветок вместо пальм, башня мага
вместо хижины, рунный камень, плетёный короб, указатели-стрелки с фонарём-цветком. На горизонте
сиреневые сумерки с двумя лунами и летающими островами, лесная гряда с великим деревом, море
облаков под островами вместо моря. Дорога из рунных плит, обочина мох.

Вагонетки и пропы в палитре `fantasy16.PALETTE`, горизонт в своей (`FANTASY_SKY`), цвета
дороги лентой `road_colors` по местам `ROAD_COLORS`.

    python3 tools/fantasy_road16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fantasy16  # noqa: E402
from fantasy16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS,  # noqa: E402
                       METAL, DARK, RED, VIOLET, PLUM)

# Палитра горизонта: небо, луны и облака, море облаков, лес и острова. Места те же по смыслу,
# что у пиратов и космоса.
S0, S1, S2, S3, C0, C1, C2, M0, M1, M2, M3, I0, I1, I2, I3, SUN = range(16)
FANTASY_SKY = [
    (0x24, 0x1A, 0x56),  # S0  небо наверху
    (0x40, 0x2A, 0x7E),  # S1
    (0x6E, 0x40, 0xA2),  # S2
    (0xB4, 0x6A, 0xB6),  # S3  небо у горизонта, зарево
    (0x8E, 0x5E, 0xB4),  # C0  тень облака и луны
    (0xEA, 0xA6, 0xC4),  # C1  облако, луна
    (0xFF, 0xF0, 0xDE),  # C2  свет луны, яркие звёзды
    (0x62, 0x48, 0x96),  # M0  море облаков вдали
    (0x94, 0x74, 0xBC),  # M1  облака
    (0xCE, 0xB4, 0xE2),  # M2  облака у дороги
    (0x4C, 0x36, 0x7E),  # M3  тень между валами облаков
    (0x5E, 0x42, 0x94),  # I0  лес и острова в дымке
    (0x32, 0x22, 0x60),  # I1  лес, великое дерево
    (0xA8, 0x7C, 0xDA),  # I2  свет на сиреневой листве
    (0x3A, 0xD4, 0xC2),  # I3  огни, водопады
    (0x62, 0xA4, 0x4A),  # SUN мох у кромки дороги
]

# Цвета дороги по местам ленты `road_colors` (демка берёт их по индексу).
ROAD_COLORS = [
    (0x8A, 0x82, 0xAC),  # 0 рунная плита светлая
    (0x7C, 0x74, 0x9E),  # 1 рунная плита тёмная
    (0x9C, 0x5E, 0xD8),  # 2 бордюр фиолетовый
    (0xF4, 0xEE, 0xE4),  # 3 бордюр белый
    (0xC8, 0xF8, 0xEC),  # 4 разметка: светящаяся руна
    (0x62, 0xA4, 0x4A),  # 5 мох светлый
    (0x54, 0x94, 0x42),  # 6 мох тёмный
    (0x62, 0x48, 0x96),  # 7 дымка вдали
]


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wellipse(c, cx, cy, rx, ry, col):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                _wset(c, x, y, col)


# --- Горизонт ----------------------------------------------------------------------------------

def _sky_island(c, cx, cy, w, fall):
    """Летающий остров в дымке: плоская макушка с кронами, снизу скала клином, водопад нитью."""
    for x in range(int(cx - w), int(cx + w) + 1):
        k = (x - cx) / w
        depth = int((1.0 - abs(k) ** 1.4) * w * 0.75 + abs((x * 5) % 7 - 3) * 0.5)
        for y in range(cy, cy + depth + 1):
            _wset(c, x, y, I0 if y < cy + 2 + depth // 3 else I1)
        crown = int((1.0 - k * k) * 3 + abs((x * 3) % 5 - 2))
        for y in range(cy - crown, cy):
            _wset(c, x, y, I2 if y == cy - crown and x % 2 == 0 else I0)
    if fall:
        fx = cx + w * 0.45
        for y in range(cy + 1, cy + int(w * 1.3)):
            if y % 5 != 4:
                _wset(c, fx, y, I3)
        _wset(c, fx - 1, cy + int(w * 1.3), C2)
        _wset(c, fx + 1, cy + int(w * 1.3), C2)


def sky():
    """Небо, 512×128, стыкуется по краям: густой индиго наверху, сиреневое зарево у горизонта,
    звёзды, большая луна с кратерами и малая серпом, перистые облака, летающие острова."""
    rng = random.Random(311)
    c = Canvas(512, 128)
    bands = [(0, S0), (34, S1), (70, S2), (102, S3)]
    for y in range(128):
        col = S0
        for start, b in bands:
            if y >= start:
                col = b
        for x in range(512):
            px = col
            for i in range(1, len(bands)):
                start = bands[i][0]
                # Переход полос шашечкой в четыре строки.
                if start - 2 <= y < start and (x + y) % 2 == 0:
                    px = bands[i][1]
                elif start <= y < start + 2 and (x + y) % 2 == 0:
                    px = bands[i - 1][1]
            c.set(x, y, px)
    # Звёзды: гуще наверху, яркие крестиком.
    for _ in range(190):
        x = rng.randint(0, 511)
        y = int(rng.random() ** 1.6 * 92)
        c.set(x, y, S2 if rng.random() < 0.55 else C1)
    for _ in range(20):
        x = rng.randint(2, 509)
        y = rng.randint(2, 70)
        c.set(x, y, C2)
        if rng.random() < 0.5:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.set(x + dx, y + dy, C1)
    # Большая луна: диск, тень справа снизу, кратеры, ореол точками.
    px_, py_, pr = 140, 44, 24
    for a in range(0, 360, 6):
        ra = math.radians(a)
        _wset(c, px_ + math.cos(ra) * (pr + 4), int(py_ + math.sin(ra) * (pr + 4)), S2)
    _wellipse(c, px_, py_, pr, pr, C1)
    for y in range(py_ - pr, py_ + pr + 1):
        for x in range(px_ - pr, px_ + pr + 1):
            if math.hypot(x - px_, y - py_) > pr:
                continue
            if math.hypot(x - (px_ - 8), y - (py_ - 8)) > pr * 1.04:
                c.set(x, y, C0)
            elif math.hypot(x - (px_ - 8), y - (py_ - 9)) < 11 and (x + y) % 2 == 0:
                c.set(x, y, C2)
    for cx, cy, r in ((132, 52, 5), (150, 38, 4), (144, 58, 3), (124, 36, 3), (155, 52, 2)):
        _wellipse(c, cx, cy, r, r * 0.8, C0)
        _wellipse(c, cx + 1, cy + 1, r - 1, (r - 1) * 0.8, C1)
    # Малая луна серпом.
    _wellipse(c, 404, 26, 8, 8, C2)
    _wellipse(c, 408, 23, 8, 8, S0)
    # Перистые облака у горизонта: длинные полосы со светлым верхом.
    for cx, cy, w in ((40, 96, 46), (230, 88, 60), (330, 108, 40), (468, 98, 50), (120, 112, 34)):
        for i in range(-w, w + 1):
            k = 1.0 - abs(i) / w
            h = int(k * 3.2 + (1 if (i * 7) % 5 < 2 else 0))
            for d in range(h):
                _wset(c, cx + i, cy - d, C1 if d == h - 1 else C0)
        for i in range(-w // 2, w // 2, 3):
            _wset(c, cx + i + 6, cy + 1, C0)
    # Летающие острова: три в дымке, у двух водопады.
    _sky_island(c, 276, 46, 22, True)
    _sky_island(c, 352, 70, 12, False)
    _sky_island(c, 34, 56, 15, True)
    _sky_island(c, 462, 60, 9, False)
    return c


def islands():
    """Лес на горизонте, 512×40, прозрачный верх: дальняя гряда крон в дымке, ближняя гряда
    тёмная, над ней великое дерево с огнями в стволе, по краям шпили башен магов."""
    c = Canvas(512, 40)
    # Дальняя гряда крон по всей ширине: низкая, буграми.
    for x in range(512):
        a = x / 512.0 * math.pi * 2
        top = 34 - int(3 + 2.5 * math.sin(a * 5) + 1.5 * math.sin(a * 13 + 1) + abs((x % 9) - 4) * 0.6)
        for y in range(top, 40):
            c.set(x, y, I0)
    # Ближние рощи: тёмные купола крон со светом по макушкам.
    for cx, w, h in ((70, 60, 12), (196, 40, 9), (300, 96, 13), (436, 56, 11)):
        for x in range(int(cx - w), int(cx + w) + 1):
            k = (x - cx) / w
            bump = abs(((x * 3) % 14) - 7) * 0.55
            top = 39 - int(h * max(0.0, 1.0 - k * k) ** 0.6 + bump)
            for y in range(top, 40):
                _wset(c, x, y, I2 if y == top and x % 3 != 0 else I1)
    # Великое дерево: ствол с расходящимся комлем, три яруса кроны, огни окон.
    tx = 300
    for y in range(12, 40):
        half = 4 + (y - 12) * 0.12 + max(0, y - 32) * 0.9
        for x in range(int(tx - half), int(tx + half) + 1):
            c.set(x, y, I1)
    # Сучья вилкой от ствола к боковым клубам, чтобы крона не висела шляпкой гриба.
    for (x0, y0), (x1, y1) in (((299, 27), (283, 17)), ((301, 25), (318, 16)), ((300, 22), (296, 10))):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            x = int(round(x0 + (x1 - x0) * i / n))
            y = int(round(y0 + (y1 - y0) * i / n))
            c.rect(x - 1, y, x + 1, y + 1, I1)
    # Крона клубами разной высоты: макушка, плечи, нижние ветви свисают ниже развилки.
    for cx, cy, rx, ry in ((299, 8, 15, 8), (284, 12, 12, 7), (316, 11, 13, 7), (272, 17, 9, 5),
                           (329, 16, 9, 5), (292, 4, 9, 4), (309, 4, 8, 4), (300, 15, 12, 5)):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1.0 and y >= 0:
                    edge = ((x - cx) / rx) ** 2 + ((y - 1 - cy) / ry) ** 2 > 1.0
                    c.set(x, y, I2 if edge and x % 3 != 0 else I1)
    for x, y in ((299, 20), (301, 26), (298, 31), (302, 33)):
        c.set(x, y, I3)
    c.set(300, 26, C2)
    # Башни магов: шпиль с колпаком и светящимся окном.
    for cx, top in ((62, 14), (432, 18), (168, 22)):
        for y in range(top + 6, 36):
            c.rect(cx - 2, y, cx + 2, y, I1)
        for i in range(7):
            c.rect(cx - i * 0.6, top + i, cx + i * 0.6, top + i, I1)
        c.set(cx, top - 1, C2)
        c.set(cx, top + 10, I3)
        c.set(cx, top + 11, I3)
        c.set(cx + 1, top + 16, C1)
    return c


def sea():
    """Море облаков от горизонта, 512×24: три вала клубами, тёмные вдали и светлые у дороги,
    между валами тени; у нижней кромки полоса мха."""
    rng = random.Random(313)
    c = Canvas(512, 24)
    c.rect(0, 0, 511, 23, M0)
    # Вал: волнистая кромка клубами, под кромкой свет, перед следующим валом тень.
    for base, amp, period, col, shade in ((6, 2.0, 46.0, M1, M3), (13, 2.6, 64.0, M2, M0)):
        for x in range(512):
            a = x / 512.0 * math.pi * 2
            puff = abs(math.sin(a * 512.0 / period)) * amp + abs(math.sin(a * 512.0 / (period * 0.37) + 1.3)) * amp * 0.5
            top = int(round(base - puff))
            for y in range(top, 24):
                c.set(x, y, col)
            c.set(x, top - 1, shade)
            if x % 2 == 0:
                c.set(x, top - 2, shade)
    # Блики на ближнем вале и прорехи тени в дальних.
    for _ in range(40):
        x = rng.uniform(0, 512)
        y = rng.randint(15, 20)
        w = rng.randint(2, 5)
        for i in range(w):
            _wset(c, x + i, y, C2)
    for _ in range(34):
        x = rng.uniform(0, 512)
        y = rng.randint(2, 11)
        w = rng.randint(2, 4)
        for i in range(w):
            _wset(c, x + i, y, M3 if y < 7 else M1)
    for _ in range(26):
        x = rng.uniform(0, 512)
        w = rng.randint(3, 7)
        for i in range(w):
            _wset(c, x + i, 20, M1)
    c.rect(0, 22, 511, 23, SUN)
    return c


# --- Вагонетки и пропы (палитра спрайтов) -------------------------------------------------------

def _iron_wheel(c, cx, cy, r, phase):
    """Колесо вагонетки сзади: узкий железный обод с ребордой внутрь, заклёпки бегут вниз
    (`phase` 0..1)."""
    cx = int(round(cx))
    w = 7
    c.rect(cx - w, cy - r + 3, cx + w, cy + r - 3, DARK)
    c.rect(cx - w + 2, cy - r, cx + w - 2, cy + r, DARK)
    c.rect(cx - w + 2, cy - r + 2, cx - w + 4, cy + r - 2, GREY)
    c.rect(cx - w + 2, cy - r + 2, cx - w + 2, cy + r - 2, WHITE)
    step = 6
    off = int(phase * step)
    for y in range(cy - r + 3 + off, cy + r - 3, step):
        c.rect(cx - w + 6, y, cx + w - 2, y + 1, GREY)
        c.rect(cx + w - 3, y, cx + w - 2, y + 1, BRASS)


def _gem(c, cx, tip_y, w, base_y, tilt=0.0):
    """Кристалл гранями: светлая левая грань, тёмная правая, блик по ребру."""
    tip = (cx + tilt, tip_y)
    sh_y = tip_y + w * 1.5
    c.poly([tip, (cx + w, sh_y), (cx + w * 0.7, base_y), (cx - w * 0.7, base_y), (cx - w, sh_y + 2)], AQUA)
    c.poly([tip, (cx + w, sh_y), (cx + w * 0.7, base_y), (cx + 1, base_y), (cx + 1, sh_y + 3)], SEA)
    c.line(tip[0], tip_y + 2, cx, sh_y + 3, SKY, 1)
    c.line(cx, sh_y + 3, cx, base_y, SKY, 1)
    c.line(cx - w + 2, sh_y + 4, cx - w * 0.7 + 2, base_y, SKY, 1)


def cart(lean, phase, accent):
    """Гномья вагонетка со спины, 160×104: два железных колеса, дощатый кузов трапецией в
    обручах с заклёпками, на борту щиток цвета `accent`, в кузове большой кристалл и руда, на
    шесте вымпел цвета `accent` и фонарь; правит маг в остроконечной шляпе. `lean` −1..1 крен."""
    c = Canvas(160, 104)
    sh = lean * 6
    _iron_wheel(c, 22 + sh * 0.3, 78, 24, phase)
    _iron_wheel(c, 138 + sh * 0.3, 78, 24, phase)
    # Ось и сцепка.
    c.rect(26, 80, 134, 85, DARK)
    c.rect(30, 81, 130, 82, GREY)
    c.rect(75, 88, 85, 96, DARK)
    c.ellipse(80, 97, 4, 3, GREY)
    c.ellipse(80, 97, 2, 1, DARK)
    # Груз за спиной возницы: большой кристалл слева, друзы справа, руда вдоль борта.
    _gem(c, 48 + sh * 1.2, 10, 11, 48, -3)
    _gem(c, 62 + sh * 1.1, 28, 6, 48, 2)
    _gem(c, 106 + sh * 1.1, 26, 7, 48, 3)
    _gem(c, 117 + sh * 1.1, 34, 5, 48, -1)
    for x, r in ((34, 6), (70, 5), (96, 6), (126, 5)):
        c.ellipse(x + sh, 43, r, 5, GREY)
        c.ellipse(x + sh - 1, 41, r * 0.5, 2, WHITE)
    # Кузов: доски трапецией, швы досок, древесный рисунок.
    tl, tr = 26 + sh, 134 + sh
    bl, br = 38 + sh * 0.6, 122 + sh * 0.6
    c.poly([(tl, 46), (tr, 46), (br, 90), (bl, 90)], METAL)
    for k in (0.17, 0.34, 0.5, 0.66, 0.83):
        c.line(tl + (tr - tl) * k, 50, bl + (br - bl) * k, 89, DARK, 1)
    for i, k in enumerate((0.08, 0.26, 0.42, 0.58, 0.75, 0.92)):
        y0 = 54 + (i * 11) % 14
        xa = tl + (tr - tl) * k + (bl - tl) * (y0 - 46) / 44.0 * (1 - 2 * k)
        c.line(xa, y0, xa + (0.5 - k) * 3, y0 + 10, BRASS, 1)
    # Обручи: верхняя кромка и пояс, заклёпки.
    c.rect(tl - 2, 44, tr + 2, 49, GREY)
    c.rect(tl - 2, 44, tr + 2, 44, WHITE)
    for x in range(int(tl) + 4, int(tr) - 2, 13):
        c.rect(x, 46, x + 1, 47, DARK)
    ml = tl + (bl - tl) * 0.68
    mr = tr + (br - tr) * 0.68
    c.rect(ml, 75, mr, 78, GREY)
    for x in range(int(ml) + 5, int(mr) - 2, 12):
        c.rect(x, 76, x + 1, 77, DARK)
    # Угловые накладки вдоль скосов.
    c.line(tl + 1, 49, bl + 1, 89, GREY, 3)
    c.line(tr - 1, 49, br - 1, 89, GREY, 3)
    # Щиток цвета экипажа с руной посередине борта.
    px_ = 80 + sh * 0.8
    c.poly([(px_ - 14, 52), (px_ + 14, 52), (px_ + 14, 64), (px_, 73), (px_ - 14, 64)], DARK)
    c.poly([(px_ - 11, 54), (px_ + 11, 54), (px_ + 11, 63), (px_, 70), (px_ - 11, 63)], accent)
    rune = WHITE if accent in (GOLD, AQUA) else GOLD
    c.rect(px_ - 1, 56, px_, 66, rune)
    c.line(px_, 57, px_ + 5, 60, rune, 1)
    c.line(px_ - 1, 61, px_ - 6, 58, rune, 1)
    # Рунные огни по углам борта.
    for x in (42, 118):
        c.rect(x + sh * 0.9 - 4, 54, x + sh * 0.9 + 4, 62, DARK)
        c.rect(x + sh * 0.9 - 2, 56, x + sh * 0.9 + 2, 60, AQUA)
        c.set(x + sh * 0.9 - 1, 57, SKY)
    # Шест у правого заднего угла: вымпел, ниже фонарь на крюке.
    mx = 128 + sh * 1.4
    c.rect(mx - 1, 3, mx + 1, 46, METAL)
    flap = 3 * math.sin(phase * math.pi * 2)
    c.poly([(mx + 2, 4), (mx + 24, 8 + flap), (mx + 14, 11 + flap * 0.6), (mx + 22, 16 + flap), (mx + 2, 17)], accent)
    c.ellipse(mx, 2, 2, 2, GOLD)
    c.line(mx, 24, mx + 9, 24, DARK, 2)
    lx = mx + 9 + flap * 0.4
    c.rect(lx - 3, 26, lx + 3, 27, BRASS)
    c.rect(lx - 4, 28, lx + 4, 36, GOLD)
    c.rect(lx - 1, 30, lx + 1, 34, WHITE)
    c.rect(lx - 3, 37, lx + 3, 38, BRASS)
    # Маг со спины: мантия со складками, широкие рукава к кромке борта, волосы, шляпа.
    x0 = 72 + sh * 1.2
    mid = x0 + 8
    c.poly([(x0 - 2, 25), (x0 + 18, 25), (x0 + 21, 45), (x0 - 5, 45)], SEA)
    c.line(x0 + 4, 30, x0 + 2, 44, NAVY, 1)
    c.line(x0 + 12, 30, x0 + 14, 44, NAVY, 1)
    c.line(mid, 32, mid, 44, NAVY, 1)
    for sx, sy in ((x0 + 6, 35), (x0 + 11, 39), (x0 + 3, 41)):
        c.set(sx, sy, GOLD)
    for side in (-1, 1):
        sx = x0 + (0 if side < 0 else 16)
        c.line(sx, 28, sx + side * 9, 37, SEA, 7)
        c.line(sx + side * 9, 37, sx + side * 11, 41, SEA, 8)
        c.rect(sx + side * 8 - 3, 42, sx + side * 8 + 5 if side > 0 else sx + side * 8 + 3, 43, GOLD)
        c.ellipse(sx + side * 11, 45, 3, 2.5, SKIN)
    c.rect(x0 - 1, 24, x0 + 17, 25, GOLD)
    c.ellipse(mid, 19, 7, 6, METAL)
    c.rect(mid - 5, 22, mid + 5, 24, METAL)
    # Шляпа: поля овалом, тулья конусом с золотой лентой, кончик заломлен вправо и качается.
    c.ellipse(mid, 14, 16, 4, SEA)
    c.poly([(mid - 9, 13), (mid + 9, 13), (mid + 3, 2), (mid - 2, 2)], SEA)
    c.rect(mid - 8, 10, mid + 8, 12, GOLD)
    tipy = 3 + (1 if phase >= 0.5 else 0)
    c.line(mid + 1, 3, mid + 8, tipy, SEA, 3)
    c.line(mid - 4, 9, mid - 1, 3, NAVY, 1)
    c.finish()
    return c


def goblin_cart(lean, phase, accent):
    """Гоблинская вагонетка со спины, 160×104: кривой короб из тёмных досок с заплатами и
    костяными шипами по кромке, деревянные колёса с шипами, на борту череп и полоса цвета
    `accent`; ушастый гоблин машет дубиной (качается по `phase`), слева рваный флаг цвета
    `accent` на палке."""
    c = Canvas(160, 104)
    sh = lean * 6
    bob = 2 if phase >= 0.5 else 0
    # Колёса: дощатые плахи с железными шипами, шипы бегут вниз.
    for gx in (22, 138):
        x = int(round(gx + sh * 0.3))
        c.rect(x - 8, 57, x + 8, 99, DARK)
        c.rect(x - 6, 54, x + 6, 102, DARK)
        c.rect(x - 5, 57, x - 2, 99, METAL)
        c.rect(x + 2, 57, x + 4, 99, METAL)
        off = int(phase * 8)
        for y in range(58 + off, 98, 8):
            c.rect(x - 10, y, x - 8, y + 1, GREY)
            c.rect(x + 8, y, x + 10, y + 1, GREY)
            c.rect(x - 5, y + 3, x + 4, y + 3, DARK)
    # Ось бревном и искры из-под колёс.
    c.rect(26, 80, 134, 86, METAL)
    c.rect(26, 84, 134, 86, DARK)
    if phase < 0.25:
        for x, y in ((12, 100), (9, 96), (150, 100), (152, 95)):
            c.set(x + sh * 0.3, y, GOLD)
    # Флаг на кривой палке слева: рваный, в два зубца.
    fx0, fx1 = 30 + sh, 24 + sh * 1.4
    c.line(fx0, 50, fx1, 5, METAL, 2)
    flap = 3 * math.sin(phase * math.pi * 2)
    c.poly([(fx1 + 2, 6), (fx1 + 24, 9 + flap), (fx1 + 15, 14 + flap * 0.5), (fx1 + 23, 19 + flap),
            (fx1 + 12, 21 + flap * 0.4), (fx1 + 3, 24)], accent)
    c.rect(fx1 + 8, 12, fx1 + 10, 14, DARK)
    c.ellipse(fx1, 4, 2, 2, WHITE)
    # Мешок с добычей слева от возницы.
    c.ellipse(56 + sh, 40, 9, 9, BRASS)
    c.rect(53 + sh, 28, 59 + sh, 32, BRASS)
    c.rect(52 + sh, 32, 60 + sh, 33, DARK)
    c.rect(53 + sh, 38, 58 + sh, 39, METAL)
    # Гоблин со спины: дубина в поднятой руке, жилет, зелёная голова с ушами торчком.
    gx = 82 + sh * 1.2
    hx, hy = gx + 30, 30 - bob
    c.line(hx + 1, hy - 2, hx + 9, hy - 20, METAL, 5)
    c.ellipse(hx + 10, hy - 23, 6, 8, METAL)
    c.line(hx + 7, hy - 26, hx + 12, hy - 18, DARK, 1)
    for dx, dy in ((-7, -5), (7, -3), (-5, 5), (2, -10), (8, 4)):
        c.rect(hx + 10 + dx, hy - 23 + dy, hx + 11 + dx, hy - 22 + dy, WHITE)
    c.line(gx + 11, 34, hx, hy, TAN, 6)
    c.line(gx - 11, 34, gx - 20, 44, TAN, 6)
    c.ellipse(gx, 40, 14, 10, DARK)
    c.rect(gx - 13, 40, gx + 13, 46, DARK)
    c.line(gx - 9, 32, gx + 8, 45, BRASS, 2)
    c.rect(gx - 2, 37, gx + 1, 40, GOLD)
    for side in (-1, 1):
        ear = [(gx + side * 7, 17), (gx + side * 24, 9 + (bob if side > 0 else 0)), (gx + side * 9, 25)]
        c.poly(ear, TAN)
        c.line(gx + side * 10, 19, gx + side * 19, 13 + (bob if side > 0 else 0), DARK, 1)
    c.ellipse(gx, 21, 10, 9, TAN)
    c.rect(gx - 5, 29, gx + 5, 31, TAN)
    c.poly([(gx - 4, 13), (gx, 6), (gx + 2, 12), (gx + 5, 8), (gx + 5, 14)], DARK)
    c.rect(gx - 6, 25, gx - 3, 25, DARK)
    c.rect(gx + 3, 26, gx + 6, 26, DARK)
    # Короб: кривая трапеция из тёмных досок, светлые заплаты наискось.
    tl, tr = 28 + sh, 132 + sh
    bl, br = 36 + sh * 0.6, 124 + sh * 0.6
    c.poly([(tl, 50), (tr, 46), (br, 90), (bl, 90)], DARK)
    for k in (0.2, 0.42, 0.63, 0.82):
        c.line(tl + (tr - tl) * k, 52, bl + (br - bl) * k, 89, K, 1)
    c.poly([(tl + 8, 56), (tl + 30, 53), (tl + 31, 62), (tl + 10, 66)], METAL)
    c.poly([(tr - 34, 74), (tr - 10, 70), (tr - 12, 80), (tr - 33, 84)], METAL)
    c.poly([(tr - 26, 52), (tr - 8, 51), (tr - 9, 60), (tr - 25, 61)], BRASS)
    for x, y in ((tl + 10, 58), (tl + 28, 56), (tr - 32, 76), (tr - 13, 73), (tr - 24, 54), (tr - 11, 58)):
        c.set(x, y, GREY)
    # Костяные шипы по кромке и по углам.
    for i, k in enumerate((0.03, 0.15, 0.27, 0.73, 0.85, 0.97)):
        x = tl + (tr - tl) * k
        y = 50 + (46 - 50) * k
        h = 11 if i in (0, 5) else 8
        c.poly([(x - 3, y + 1), (x + (-2 if k < 0.5 else 2), y - h), (x + 3, y + 1)], WHITE)
    c.line(tl, 50, tr, 46, GREY, 2)
    # Полоса цвета экипажа и череп посередине борта.
    ml, mr = tl + (bl - tl) * 0.62, tr + (br - tr) * 0.62
    c.rect(ml + 1, 76, mr - 1, 79, accent)
    sx = 80 + sh * 0.8
    c.ellipse(sx, 64, 9, 8, WHITE)
    c.rect(sx - 5, 70, sx + 5, 75, WHITE)
    c.rect(sx - 5, 62, sx - 2, 65, K)
    c.rect(sx + 2, 62, sx + 5, 65, K)
    c.rect(sx - 1, 67, sx, 69, K)
    for x in (-3, 0, 3):
        c.rect(sx + x, 73, sx + x, 75, K)
    # Цепь-сцепка под днищем.
    c.rect(77, 90, 83, 95, DARK)
    c.ellipse(80, 97, 3, 3, GREY)
    c.finish()
    return c


def carts_strip(accent, goblin):
    """Три крена (влево, прямо, вправо) по два кадра: лента 6 кадров по 160, порядок как у пиратов."""
    frames = []
    for lean in (-1.0, 0.0, 1.0):
        for ph in (0.0, 0.5):
            frames.append(goblin_cart(lean, ph, accent) if goblin else cart(lean, ph, accent))
    return strip(frames)


def lilac_tree():
    """Дерево с сиреневой листвой у обочины, 120×240 (место пальмы): кривой ствол с корнями и
    светящимся дуплом, крона клубами в три яруса, с кроны свисают лианы с золотыми плодами."""
    rng = random.Random(317)
    c = Canvas(120, 240)
    # Ствол: изгиб буквой S, к корням шире, полосы коры.
    pts = []
    for i in range(160):
        k = i / 159.0
        pts.append((60 + 9 * math.sin(k * math.pi * 1.6) - 4 * k, 239 - i, 6.5 + 5 * (1 - k) + 9 * (1 - k) ** 8))
    for i, (x, y, w) in enumerate(pts):
        c.rect(x - w, y, x + w, y, METAL)
        for n, off in enumerate((-0.55, -0.05, 0.45)):
            if (i + n * 9) % 23 < 15:
                c.set(x + off * w, y, DARK)
        if (i // 5) % 3 != 0:
            c.set(x - w + 1, y, BRASS)
    # Корни: три лапы по земле.
    c.poly([(48, 224), (14, 239), (40, 239), (54, 232)], METAL)
    c.poly([(72, 224), (106, 239), (80, 239), (66, 232)], METAL)
    c.line(30, 236, 48, 228, DARK, 1)
    c.line(90, 236, 72, 228, DARK, 1)
    # Дупло со светом.
    c.ellipse(63, 192, 5, 8, DARK)
    c.ellipse(63, 193, 2, 4, AQUA)
    c.set(63, 191, SKY)
    # Сучья к ярусам кроны.
    top = pts[-1]
    for bx, by in ((24, 78), (96, 74), (60, 52)):
        c.line(top[0], top[1] + 22, bx, by, METAL, 5)
    # Лианы позади кроны: висят с ярусов, на концах плоды, листья парами.
    for x0, y0, length, sway in ((16, 84, 62, 5), (34, 92, 40, -4), (92, 96, 70, 6), (106, 84, 44, -5)):
        for i in range(length):
            x = x0 + sway * math.sin(i / 11.0)
            c.set(x, y0 + i, TAN)
            c.set(x + 1, y0 + i, TAN)
            if i % 12 == 6:
                c.rect(x - 3, y0 + i, x - 1, y0 + i + 1, TAN)
                c.rect(x + 2, y0 + i + 3, x + 4, y0 + i + 4, TAN)
        ex = x0 + sway * math.sin(length / 11.0)
        c.ellipse(ex + 0.5, y0 + length + 2, 3, 3, GOLD)
        c.set(ex, y0 + length + 1, WHITE)
    # Крона: тёмный испод, поверх клубы листвы; низ клубов подчёркнут.
    clumps = ((60, 34, 34, 26), (26, 60, 24, 20), (94, 58, 24, 21), (60, 70, 30, 20), (40, 28, 20, 16),
              (84, 30, 20, 16), (16, 78, 14, 11), (104, 78, 14, 12))
    for cx, cy, rx, ry in clumps:
        c.ellipse(cx, cy + 5, rx, ry, PLUM)
    for cx, cy, rx, ry in clumps:
        c.ellipse(cx, cy, rx, ry - 2, VIOLET)
    # Листва: дуги тени рядами и светлые цветки.
    for cx, cy, rx, ry in clumps:
        for _ in range(int(rx * ry / 14)):
            a = rng.uniform(0, math.pi * 2)
            d = rng.uniform(0.15, 0.85)
            x = cx + math.cos(a) * rx * d
            y = cy + math.sin(a) * (ry - 2) * d
            c.rect(x - 2, y, x - 1, y, PLUM)
            c.set(x, y + 1, PLUM)
            c.rect(x + 1, y, x + 2, y, PLUM)
    for _ in range(26):
        cx, cy, rx, ry = clumps[rng.randint(0, len(clumps) - 1)]
        a = rng.uniform(math.pi, math.pi * 2)
        d = rng.uniform(0.2, 0.8)
        x = int(cx + math.cos(a) * rx * d)
        y = int(cy + math.sin(a) * (ry - 2) * d)
        c.rect(x, y, x + 1, y + 1, SKY)
        c.set(x, y, WHITE)
    c.finish()
    return c


def giant_flower():
    """Гигантский цветок у обочины, 120×240 (место второй пальмы): изогнутый зелёный стебель с
    двумя листьями-лопастями, наверху раскрытый венчик в два ряда лепестков с золотой
    сердцевиной, сбоку бутон."""
    c = Canvas(120, 240)
    # Листья позади стебля: лопасти с жилкой.
    c.poly([(58, 224), (30, 200), (8, 150), (4, 132), (20, 168), (40, 196), (60, 208)], TAN)
    c.line(56, 216, 24, 180, DARK, 1)
    c.line(24, 180, 8, 142, DARK, 1)
    c.poly([(66, 196), (92, 170), (110, 126), (116, 108), (114, 150), (98, 184), (70, 212)], TAN)
    c.line(68, 202, 100, 166, DARK, 1)
    c.line(100, 166, 113, 122, DARK, 1)
    # Бутон на боковом побеге.
    c.line(70, 150, 92, 128, TAN, 3)
    c.ellipse(96, 116, 8, 12, RED)
    c.poly([(88, 124), (92, 110), (96, 124), (100, 110), (104, 124), (96, 130)], TAN)
    # Стебель дугой, с узлами.
    pts = []
    for i in range(172):
        k = i / 171.0
        pts.append((60 + 12 * math.sin(k * math.pi), 239 - i))
    for i, (x, y) in enumerate(pts):
        w = 5.5 - 2.0 * i / 171.0
        c.rect(x - w, y, x + w, y, TAN)
        if i % 34 == 20:
            c.rect(x - w - 1, y, x + w + 1, y + 1, TAN)
            c.rect(x - w, y + 2, x + w, y + 2, DARK)
    c.poly([(40, 239), (50, 228), (72, 228), (82, 239)], TAN)
    # Венчик: чашелистики, задний ряд лепестков сиреневый, передний алый, сердцевина.
    bx, by = 60, 56
    c.poly([(bx - 16, by + 26), (bx - 6, by + 44), (bx + 6, by + 44), (bx + 16, by + 26)], TAN)

    def petal(a, r, col, vein):
        def at(rr, aa):
            return (bx + math.cos(aa) * rr, by + math.sin(aa) * rr * 0.86)
        c.poly([at(r * 0.2, a - 0.6), at(r * 0.72, a - 0.34), at(r, a), at(r * 0.72, a + 0.34), at(r * 0.2, a + 0.6)], col)
        p0 = at(r * 0.3, a)
        p1 = at(r * 0.82, a)
        c.line(p0[0], p0[1], p1[0], p1[1], vein, 1)

    for i in range(8):
        petal(i * math.pi / 4 + math.pi / 8, 52, VIOLET, PLUM)
    for i in range(8):
        petal(i * math.pi / 4, 40, RED, PLUM)
    c.ellipse(bx, by, 14, 12, GOLD)
    c.ellipse(bx, by, 9, 7, BRASS)
    for i in range(10):
        a = i * math.pi / 5
        c.set(bx + math.cos(a) * 11, by + math.sin(a) * 9, WHITE)
    for dx, dy in ((-3, -2), (2, -3), (4, 2), (-2, 3), (0, 0)):
        c.set(bx + dx, by + dy, GOLD)
    c.finish()
    return c


def rune_stone():
    """Рунный камень у дороги, 96×64: наклонный менгир с бирюзовыми рунами, обломок рядом,
    мох на макушке и у подножия."""
    c = Canvas(96, 64)
    # Менгир: светлая левая грань, тёмная правая, скол на макушке.
    c.poly([(16, 63), (20, 34), (30, 12), (42, 2), (56, 6), (68, 28), (74, 63)], GREY)
    c.poly([(22, 36), (31, 14), (42, 4), (48, 6), (44, 30), (40, 62), (20, 62)], WHITE)
    c.line(48, 7, 44, 30, DARK, 1)
    c.line(44, 30, 41, 62, DARK, 1)
    c.line(58, 22, 64, 44, DARK, 1)
    c.line(52, 44, 58, 54, DARK, 1)
    # Руны на светлой грани: вертикаль с ветками, круг с точкой, угол.
    c.rect(32, 16, 33, 28, AQUA)
    c.line(33, 17, 38, 21, AQUA, 1)
    c.line(33, 22, 38, 26, AQUA, 1)
    c.set(32, 16, SKY)
    for a in range(0, 360, 20):
        ra = math.radians(a)
        c.set(32 + math.cos(ra) * 5, 39 + math.sin(ra) * 5, AQUA)
    c.rect(31, 38, 33, 40, SKY)
    c.line(27, 50, 32, 56, AQUA, 2)
    c.line(32, 56, 37, 50, AQUA, 2)
    # Руна на тёмной грани.
    c.line(54, 16, 60, 34, AQUA, 1)
    c.line(57, 25, 51, 30, AQUA, 1)
    # Мох шапкой и у подножия.
    c.poly([(30, 12), (42, 1), (56, 5), (52, 9), (44, 6), (36, 12)], TAN)
    c.set(38, 13, TAN)
    c.set(50, 10, TAN)
    # Обломок справа и камень слева.
    c.poly([(70, 63), (74, 46), (84, 40), (93, 50), (94, 63)], GREY)
    c.poly([(74, 48), (84, 42), (86, 52), (78, 62), (72, 62)], WHITE)
    c.rect(79, 49, 80, 55, AQUA)
    c.poly([(2, 63), (6, 52), (16, 50), (22, 63)], GREY)
    for x in range(1, 95, 5):
        c.rect(x, 61 + (x % 2), x + 2, 63, TAN)
    return c.finish()


def basket():
    """Плетёный короб, 48×64: корзина бочонком из лозы в шашечку, крышка с петлёй, два ремня,
    золотая бирка с руной."""
    c = Canvas(48, 64)
    # Дужка над крышкой.
    for a in range(180, 361, 4):
        ra = math.radians(a)
        c.rect(24 + math.cos(ra) * 11, 12 + math.sin(ra) * 10, 25 + math.cos(ra) * 11, 13 + math.sin(ra) * 10, METAL)
    # Корпус: шире к плечам, плетение в шашечку.
    for y in range(16, 62):
        k = (y - 16) / 45.0
        half = 17 + 4 * math.sin(k * math.pi * 0.9) - 2 * k
        for x in range(int(24 - half), int(24 + half) + 1):
            c.set(x, y, BRASS if ((x + 2) // 4 + (y // 4)) % 2 == 0 else METAL)
        if y % 4 == 3:
            for x in range(int(24 - half), int(24 + half) + 1, 4):
                c.set(x + (y // 4) % 2 * 2, y, DARK)
    # Обод дна и крышка куполом с кромкой.
    c.rect(8, 60, 40, 62, DARK)
    c.ellipse(24, 16, 20, 6, BRASS)
    c.rect(4, 16, 44, 19, METAL)
    c.rect(4, 19, 44, 19, DARK)
    c.rect(10, 12, 38, 12, GOLD)
    # Ремни с пряжками.
    for x in (13, 33):
        c.rect(x - 1, 20, x + 1, 59, DARK)
        c.rect(x - 2, 30, x + 2, 33, GOLD)
    # Бирка с руной.
    c.rect(20, 36, 28, 46, GOLD)
    c.rect(23, 38, 24, 44, PLUM)
    c.set(25, 40, PLUM)
    c.set(26, 41, PLUM)
    c.set(22, 42, PLUM)
    return c.finish()


def sign(right):
    """Указатель поворота, 96×112: дощатая стрела на кривом столбе, остриё в сторону поворота,
    золотые шевроны на тёмной доске в медной раме, с другого края висит фонарь-цветок."""
    c = Canvas(96, 112)
    d = 1 if right else -1
    # Столб с сучком и корнями.
    c.line(48, 111, 47, 52, METAL, 7)
    c.line(47, 80, 47, 104, DARK, 1)
    c.line(49, 60, 49, 74, BRASS, 1)
    c.poly([(40, 111), (44, 102), (52, 102), (57, 111)], METAL)

    def mx(x):
        return 48 + d * (x - 48)

    # Доска стрелой: рама, тёмное поле.
    c.poly([(mx(4), 5), (mx(72), 5), (mx(93), 30), (mx(72), 55), (mx(4), 55)], BRASS)
    c.poly([(mx(8), 9), (mx(70), 9), (mx(87), 30), (mx(70), 51), (mx(8), 51)], DARK)
    c.line(mx(8), 23, mx(80), 23, K, 1)
    c.line(mx(8), 37, mx(80), 37, K, 1)
    # Шевроны в сторону поворота (те же места, что у зеркала).
    for k in range(3):
        cx = 48 + d * (k * 20 - 20)
        c.poly([(cx - d * 8, 14), (cx + d * 10, 30), (cx - d * 8, 46), (cx - d * 2, 30)], GOLD)
    # Гвозди рамы.
    for x, y in ((6, 7), (6, 53), (70, 7), (70, 53)):
        c.rect(mx(x) - 1, y - 1, mx(x), y, GREY)
    # Фонарь-цветок на тупом конце: стебель крюком, колокольчик светится.
    fx = mx(12)
    c.line(fx, 55, fx, 62, TAN, 2)
    c.poly([(fx - 6, 74), (fx - 4, 64), (fx, 61), (fx + 4, 64), (fx + 6, 74), (fx + 3, 71), (fx, 75), (fx - 3, 71)], VIOLET)
    c.rect(fx - 1, 70, fx + 1, 78, AQUA)
    c.set(fx, 79, SKY)
    c.rect(fx - 2, 61, fx + 2, 62, TAN)
    return c.finish()


def mage_tower():
    """Башня мага у дороги, 192×160 (место хижины): круглая каменная башня под кривым сиреневым
    колпаком с кристаллом на шпиле, сбоку навесная башенка, слева пристройка под своим
    колпаком; арочная дверь, окна светятся, по кладке плющ."""
    rng = random.Random(331)
    c = Canvas(192, 160)

    def stone(x0, x1, y0, y1, flare=0.0):
        """Кладка: стена с расширением к низу, швы рядами вразбежку."""
        for y in range(y0, y1 + 1):
            f = flare * max(0.0, (y - (y1 - 30)) / 30.0) ** 2
            c.rect(x0 - f, y, x1 + f, y, GREY)
            # Светлая полоса слева: башня круглая.
            c.rect(x0 - f + 3, y, x0 - f + (x1 - x0) * 0.3, y, WHITE)
        for row, y in enumerate(range(y0 + 6, y1, 9)):
            for x in range(x0 + 4 + (row % 2) * 7, x1 - 4, 14):
                if rng.random() < 0.7:
                    c.rect(x, y, x + 6, y, DARK)
                    c.set(x + (3 if row % 2 else 0), y - 4, DARK)
                    c.set(x + (3 if row % 2 else 0), y - 3, DARK)

    def roof(cx, y_eave, half, tip_x, tip_y):
        """Колпак: конус с загнутым шпилем, ряды черепицы, свес."""
        c.poly([(cx - half, y_eave), (cx + half, y_eave), (tip_x + 2, tip_y), (tip_x - 2, tip_y)], VIOLET)
        n = max(1, y_eave - tip_y)
        for y in range(tip_y + 8, y_eave, 8):
            k = (y - tip_y) / n
            lo = tip_x + (cx - half - tip_x) * k
            hi = tip_x + (cx + half - tip_x) * k
            for x in range(int(lo) + 2, int(hi) - 1):
                if (x + y) % 6 < 4:
                    c.set(x, y, PLUM)
            for x in range(int(lo) + 4 + (y // 8) % 2 * 3, int(hi) - 2, 6):
                c.set(x, y + 1, PLUM)
                c.set(x, y + 2, PLUM)
        c.rect(cx - half - 3, y_eave, cx + half + 3, y_eave + 3, PLUM)
        c.rect(cx - half - 3, y_eave, cx + half + 3, y_eave, VIOLET)

    def window(x, y, w, h):
        c.rect(x - w - 2, y - 2, x + w + 2, y + h + 2, DARK)
        c.ellipse(x, y - 1, w + 2, w + 1, DARK)
        c.rect(x - w, y, x + w, y + h, GOLD)
        c.ellipse(x, y, w, w - 1, GOLD)
        c.rect(x, y - w + 1, x, y + h, DARK)
        c.rect(x - w, y + h // 2, x + w, y + h // 2, DARK)
        c.set(x - w + 1, y + 1, WHITE)

    # Пригорок мха под башней.
    c.ellipse(96, 160, 94, 12, TAN)
    # Пристройка слева.
    stone(26, 66, 104, 156, 2.0)
    roof(46, 102, 24, 40, 62)
    window(46, 122, 5, 10)
    # Навесная башенка справа на подкосах.
    c.poly([(126, 112), (158, 100), (158, 104), (128, 124)], METAL)
    stone(134, 162, 66, 102)
    c.rect(132, 100, 164, 104, DARK)
    roof(148, 64, 17, 152, 34)
    window(148, 78, 4, 8)
    # Главная башня.
    stone(64, 130, 62, 156, 5.0)
    # Балка-пояс и зубчики под свесом.
    c.rect(62, 100, 132, 103, METAL)
    for x in range(64, 130, 8):
        c.rect(x, 104, x + 3, 106, DARK)
    roof(97, 60, 40, 104, 12)
    # Шпиль: загнутый кончик и кристалл.
    c.line(104, 12, 112, 6, VIOLET, 3)
    c.poly([(114, 1), (118, 6), (114, 12), (110, 6)], AQUA)
    c.set(113, 4, SKY)
    c.set(113, 5, SKY)
    # Слуховое окно в колпаке.
    c.poly([(88, 44), (97, 34), (106, 44)], PLUM)
    c.ellipse(97, 44, 4, 4, GOLD)
    c.set(96, 43, WHITE)
    # Окна и круглое окно с бирюзой.
    window(82, 76, 5, 11)
    window(114, 76, 5, 11)
    c.ellipse(97, 116, 8, 8, DARK)
    c.ellipse(97, 116, 6, 6, AQUA)
    c.rect(97, 110, 97, 122, DARK)
    c.rect(91, 116, 103, 116, DARK)
    c.set(94, 113, SKY)
    # Дверь аркой, кованые петли, ступени.
    c.ellipse(97, 138, 12, 10, DARK)
    c.rect(85, 138, 109, 156, DARK)
    c.ellipse(97, 139, 9, 8, METAL)
    c.rect(88, 139, 106, 156, METAL)
    c.rect(97, 132, 97, 156, DARK)
    c.rect(88, 142, 94, 143, GREY)
    c.rect(100, 142, 106, 143, GREY)
    c.rect(88, 151, 94, 152, GREY)
    c.rect(100, 151, 106, 152, GREY)
    c.rect(94, 146, 95, 147, GOLD)
    c.rect(80, 156, 114, 159, GREY)
    c.rect(80, 156, 114, 156, WHITE)
    # Плющ по правому боку главной башни.
    for i in range(52):
        x = 124 + 4 * math.sin(i / 6.0) - i * 0.12
        y = 156 - i
        c.rect(x, y, x + 1, y, TAN)
        if i % 5 == 0:
            c.rect(x - 3, y - 1, x - 1, y, TAN)
        if i % 5 == 2:
            c.rect(x + 2, y - 1, x + 4, y, TAN)
    # Кусты мха у подножия.
    c.ellipse(20, 154, 14, 6, TAN)
    c.ellipse(170, 154, 16, 6, TAN)
    for x, y in ((14, 150), (24, 151), (166, 150), (176, 151)):
        c.rect(x, y, x + 1, y + 1, SKY)
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
        "palm": lilac_tree(),
        "palm_b": giant_flower(),
        "road_rock": rune_stone(),
        "road_barrel": basket(),
        "sign_left": sign(False),
        "sign_right": sign(True),
        "road_hut": mage_tower(),
    }
    for i, accent in enumerate((SEA, GOLD, RED, AQUA)):
        out["cart_%d" % i] = carts_strip(accent, True)
    return out


def horizon():
    """Горизонт в своей палитре `FANTASY_SKY`."""
    return {"road_sky": sky(), "road_islands": islands(), "road_sea": sea()}


def road_palette():
    return {"road_colors": road_colors()}


def preview(path):
    items = fantasy16.shaded(sprites())
    for key, canvas in horizon().items():
        items[key] = (canvas, FANTASY_SKY)
    for key, canvas in road_palette().items():
        items[key] = (canvas, ROAD_COLORS)
    fantasy16.save_sheet(path, items, scale=2, max_w=512)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
