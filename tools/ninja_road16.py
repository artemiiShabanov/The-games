#!/usr/bin/env python3
"""Набор «Ниндзя» для гонки × 16/32-bit «псевдо-3D» (#137), зеркало `space_road16.py` и
`pixel_road16.py`: те же ключи, размеры холстов и порядок кадров, чтобы `racing_bit16.gd` брала
их без правок. Герой едет на двухколёсной повозке-рикше (вид сзади): дощатый кузов трапецией под
красным лаковым поручнем, высокие деревянные колёса в железной шине, на борту белый круг с
солнцем, поперёк спинки сложенный гармошкой верх, из-за него видна бочка сакэ в соломе, на
заднем углу бумажный фонарь на коротком крюке и флажок на хлысте (всё ниже головы возницы, без
шестов, знамён и змеев: паруса только у пиратов); правит ниндзя в тёмно-синем с красным шарфом
и мечом через спину. Соперники на повозках чужих кланов: чёрный лаковый короб с загнутыми вверх
красными углами, гербом и поясом цвета клана, под углами висят бумажные фонари того же цвета,
ниндзя в красном с серпами накрест за спиной. У дороги красный клён и бамбук вместо пальм,
пагода вместо хижины, приземистый каменный фонарь, бочка сакэ в соломе, указатели под двускатной
крышей. На горизонте закат с низким солнцем в полосах облаков, гора со снежной шапкой в дымке,
замок на утёсе и тории, тёмный пруд с бликами заката вместо моря. Дорога каменная, обочина мох.

Повозки и пропы в палитре `ninja16.PALETTE`, горизонт в своей (`NINJA_SKY`), цвета дороги
лентой `road_colors` по местам `ROAD_COLORS`.

    python3 tools/ninja_road16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ninja16  # noqa: E402
from ninja16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS,  # noqa: E402
                     METAL, DARK, RED, VIOLET, PLUM)

# Палитра горизонта: закатное небо, солнце и облака, пруд, горы и замок. Места те же по смыслу,
# что у пиратов и космоса.
S0, S1, S2, S3, C0, C1, C2, M0, M1, M2, M3, I0, I1, I2, I3, SUN = range(16)
NINJA_SKY = [
    (0x1C, 0x17, 0x44),  # S0  небо наверху, индиго
    (0x4C, 0x2B, 0x68),  # S1  лиловый
    (0xB4, 0x4A, 0x62),  # S2  розовый
    (0xF2, 0x94, 0x56),  # S3  небо у горизонта, оранжевый
    (0x7C, 0x36, 0x64),  # C0  тень облака
    (0xF0, 0x6A, 0x4A),  # C1  кромка облака, ободок солнца, тории
    (0xFD, 0xE6, 0xA4),  # C2  солнце, месяц, звёзды
    (0x22, 0x20, 0x4A),  # M0  пруд вдали
    (0x38, 0x32, 0x64),  # M1  пруд
    (0x62, 0x44, 0x76),  # M2  пруд у берега
    (0xF6, 0xA8, 0x6A),  # M3  блик заката
    (0x74, 0x40, 0x70),  # I0  гора в дымке
    (0x2A, 0x1E, 0x46),  # I1  утёс, крыши, сосны
    (0xEC, 0xE0, 0xD2),  # I2  стены замка, снег
    (0xFB, 0xD4, 0x6A),  # I3  окна и огни
    (0x5E, 0x8A, 0x48),  # SUN мох у кромки дороги
]

# Цвета дороги по местам ленты `road_colors` (демка берёт их по индексу).
ROAD_COLORS = [
    (0x90, 0x88, 0x92),  # 0 камень светлый
    (0x84, 0x7C, 0x88),  # 1 камень тёмный
    (0xC8, 0x38, 0x34),  # 2 бордюр красный лак
    (0xEE, 0xE8, 0xDC),  # 3 бордюр белый
    (0xF6, 0xDE, 0x9C),  # 4 разметка
    (0x5E, 0x8A, 0x48),  # 5 мох светлый
    (0x52, 0x7C, 0x42),  # 6 мох тёмный
    (0x74, 0x40, 0x70),  # 7 дымка вдали
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
    """Небо, 512×128, стыкуется по краям: индиго наверху, лиловый, розовый и оранжевый у
    горизонта с переходами в шахматку, низкое солнце в полосах облаков, тонкий месяц, первые
    звёзды и стая ворон."""
    rng = random.Random(271)
    c = Canvas(512, 128)
    bands = [(0, S0), (30, S1), (66, S2), (98, S3)]
    for y in range(128):
        col, prev, start = S0, S0, 0
        for i, (s, b) in enumerate(bands):
            if y >= s:
                col, start = b, s
                prev = bands[i - 1][1] if i else b
        for x in range(512):
            d = y - start
            out = col
            # Три ступени перехода по три строки: четверть, половина, три четверти нового цвета.
            if col != prev and d < 9:
                if d < 3:
                    out = col if (x + 2 * y) % 4 == 0 else prev
                elif d < 6:
                    out = col if (x + y) % 2 == 0 else prev
                else:
                    out = prev if (x + 2 * y) % 4 == 0 else col
            c.set(x, y, out)
    # Первые звёзды в индиго и тонкий месяц.
    for _ in range(46):
        c.set(rng.randint(0, 511), rng.randint(0, 34), S1 if rng.random() < 0.6 else C2)
    _wellipse(c, 96, 22, 8, 8, C2)
    _wellipse(c, 100, 19, 8, 8, S0)
    # Солнце у горизонта: светлый диск в коралловом ободке, низ уходит за край.
    sx, sy, sr = 372, 104, 30
    _wellipse(c, sx, sy, sr, sr, C1)
    _wellipse(c, sx, sy, sr - 3, sr - 3, C2)
    # Полосы облаков как на гравюре: длинные, с коралловой кромкой снизу, часть режет солнце.
    streaks = [(372, 96, 54, 2), (350, 110, 40, 2), (410, 118, 46, 2)]
    for _ in range(15):
        streaks.append((rng.uniform(0, 512), rng.randint(42, 120), rng.randint(22, 60), rng.choice((1, 2, 2, 3))))
    for cx, cy, rx, ry in streaks:
        _wellipse(c, cx, cy + 1, rx, ry, C1 if cy > 60 else S2)
        _wellipse(c, cx - 3, cy, rx * 0.94, ry, C0)
        if ry > 1:
            _wellipse(c, cx + rx * 0.3, cy - ry, rx * 0.5, 1, C0)
    # Вороны галочками.
    for bx, by in ((214, 52), (226, 46), (238, 55), (250, 49), (232, 62), (204, 60)):
        for dx, dy in ((-2, -1), (-1, 0), (0, 1), (1, 0), (2, -1)):
            _wset(c, bx + dx, by + dy, I1)
    return c


def _ridge_top(x, cx, w, h, jag):
    k = (x - cx) / w
    return 39 - int(h * max(0.0, 1.0 - k * k) ** 0.7 + abs((x * 7) % 13 - 6) * jag)


def islands():
    """Горы и замок на горизонте, 512×40, прозрачный верх: гора-конус со снежной шапкой и гряды
    в дымке, тёмный утёс с соснами, на нём замок в три яруса с огнями в окнах, на холме тории;
    понизу полосы тумана."""
    c = Canvas(512, 40)
    # Гора-конус: вогнутые склоны, срезанная вершина, снег зубцами.
    cx, w, h = 128, 104, 37
    for x in range(cx - w, cx + w + 1):
        k = abs(x - cx) / w
        top = 39 - int(h * min(1.0, (1.0 - k) ** 1.7 * 1.12))
        top = max(top, 2)
        for y in range(top, 40):
            snow = y < 11 + (x * 7) % 5 - (2 if (x // 3) % 2 else 0)
            _wset(c, x, y, I2 if snow else I0)
    # Дальние гряды в дымке.
    for gx, gw, gh in ((300, 70, 12), (486, 60, 10), (10, 40, 7)):
        for x in range(gx - gw, gx + gw + 1):
            for y in range(_ridge_top(x, gx, gw, gh, 0.3), 40):
                _wset(c, x, y, I0)
    # Тёмный утёс: плато под замок и скат, сосны по гребню.
    def cliff(x):
        if 386 <= x <= 430:
            return 20 + (x * 5) % 3
        if 366 <= x < 386:
            return 20 + int((386 - x) ** 1.25 * 0.5) + (x * 7) % 3
        if 430 < x <= 452:
            return 20 + int((x - 430) * 0.6) + (x * 5) % 3
        return 99
    for x in range(330, 500):
        top = min(cliff(x), _ridge_top(x, 414, 84, 9, 0.35))
        for y in range(top, 40):
            _wset(c, x, y, I1)
    for px in (340, 352, 372, 444, 458, 472, 486):
        top = min(cliff(px), _ridge_top(px, 414, 84, 9, 0.35))
        for i in range(7):
            for dx in range(-(i // 2 + (i % 2)), i // 2 + (i % 2) + 1):
                _wset(c, px + dx, top - 8 + i, I1)
    # Замок: каменное основание, три яруса белых стен под тёмными крышами с загнутыми углами.
    for x in range(392, 425):
        for y in range(17, 21):
            if x - 392 >= (20 - y) // 2 and 424 - x >= (20 - y) // 2:
                _wset(c, x, y, I0)
    for x0, x1, wall_y0, wall_y1 in ((394, 422, 13, 16), (398, 418, 8, 10), (402, 414, 3, 5)):
        for y in range(wall_y0, wall_y1 + 1):
            for x in range(x0, x1 + 1):
                _wset(c, x, y, I2)
        for x in range(x0 - 3, x1 + 4):
            _wset(c, x, wall_y0 - 1, I1)
        for x in range(x0 - 1, x1 + 2):
            _wset(c, x, wall_y0 - 2, I1)
        _wset(c, x0 - 4, wall_y0 - 2, I1)
        _wset(c, x1 + 4, wall_y0 - 2, I1)
        for x in range(x0 + 2, x1 - 1, 4):
            _wset(c, x, wall_y0 + 1, I3 if (x // 4) % 2 else I1)
    _wset(c, 408, 0, I3)
    # Тории на холме слева от горы: два столба, двойная перекладина.
    for x in range(232, 268):
        for y in range(_ridge_top(x, 250, 18, 5, 0.2), 40):
            _wset(c, x, y, I1)
    for x in (246, 254):
        for y in range(27, 35):
            _wset(c, x, y, C1)
    for x in range(243, 258):
        _wset(c, x, 26, C1)
    for x in range(245, 256):
        _wset(c, x, 29, C1)
    _wset(c, 242, 25, C1)
    _wset(c, 258, 25, C1)
    # Туман: полосы дымки поверх подножий.
    rng = random.Random(277)
    for _ in range(22):
        y = rng.randint(31, 39)
        x = rng.uniform(0, 512)
        n = rng.randint(14, 46)
        for i in range(n):
            if c.get(int(x + i) % 512, y) is not None and (i + y) % 3 != 0:
                _wset(c, x + i, y, I0)
    return c


def sea():
    """Тёмный пруд от горизонта, 512×24: вдали темнее, блики заката штрихами, лодка с огнём,
    у нижней кромки берег камышом и полоса мха в цвет обочины."""
    rng = random.Random(273)
    c = Canvas(512, 24)
    for y in range(24):
        col = M0 if y < 5 else (M1 if y < 13 else M2)
        c.rect(0, y, 511, y, col)
        if y in (5, 13):
            for x in range(0, 512, 2):
                c.set(x + (y % 2), y, M0 if y == 5 else M1)
    # Блики: у горизонта частые и короткие, ближе редкие и длинные.
    for _ in range(70):
        y = rng.randint(0, 17)
        x = rng.uniform(0, 512)
        w = rng.randint(1, 3) + y // 4
        if rng.random() < 0.75 - y * 0.03:
            for i in range(w):
                _wset(c, x + i, y, M3)
        else:
            for i in range(w + 2):
                _wset(c, x + i, y, M0)
    # Лодка рыбака с фонарём.
    for bx in (196, 420):
        for i in range(-6, 7):
            _wset(c, bx + i, 9, I1)
        for i in range(-4, 5):
            _wset(c, bx + i, 10, I1)
        for y in range(4, 9):
            _wset(c, bx + 2, y, I1)
        _wset(c, bx + 3, 5, I3)
        _wset(c, bx - 2, 8, I1)
        _wset(c, bx - 2, 7, I1)
        for i in range(-3, 5, 2):
            _wset(c, bx + i, 12, M3)
    # Берег: камыш зубцами, под ним мох.
    c.rect(0, 21, 511, 23, SUN)
    for x in range(512):
        if (x * 5) % 7 < 4:
            c.set(x, 20, SUN)
        else:
            c.set(x, 20, I1)
        if (x * 3) % 11 < 4:
            c.set(x, 19, I1)
        if (x * 3) % 11 == 1:
            c.set(x, 18, I1)
            c.set(x, 17, I1)
    return c


# --- Повозки и пропы (палитра спрайтов) ---------------------------------------------------------

def _wheel(c, cx, cy, r, phase, rim, tyre, bar):
    """Высокое колесо повозки сзади: обод `rim`, по середине шина `tyre`, поперечины `bar`
    бегут вниз (`phase` 0..1)."""
    w = 7
    c.rect(cx - w, cy - r + 4, cx + w, cy + r - 4, rim)
    c.rect(cx - w + 2, cy - r, cx + w - 2, cy + r, rim)
    c.rect(cx - 3, cy - r, cx + 3, cy + r, tyre)
    step = 6
    off = int(phase * step)
    for y in range(int(cy - r + 3) + off, int(cy + r - 3), step):
        c.rect(cx - w + 1, y, cx + w - 1, y + 1, bar)
        c.rect(cx - 3, y + 2, cx + 3, y + 2, rim)


def _driver(c, x0, phase, cloth, shade, wrap):
    """Возница со спины, руки на вожжах: корпус от x0 до x0+16, плечи y=26, пояс y=42. Голова в
    капюшоне цвета `cloth`, предплечья в обмотках `wrap`."""
    c.rect(x0 - 1, 22, x0 + 17, 42, cloth)
    c.rect(x0 + 7, 25, x0 + 8, 39, shade)
    c.rect(x0 - 1, 40, x0 + 17, 42, DARK)
    for side in (-1, 1):
        sx = x0 + (0 if side < 0 else 16)
        c.ellipse(sx, 26, 4, 4, cloth)
        c.line(sx, 26, sx + side * 6, 34, cloth, 6)
        c.line(sx + side * 6, 34, sx + side * 3, 41, wrap, 5)
        c.ellipse(sx + side * 2.5, 42, 3, 2.5, SKIN)
    c.ellipse(x0 + 8, 13, 9, 9, cloth)
    c.rect(x0 + 8, 5, x0 + 8, 20, shade)
    c.rect(x0 + 3, 18, x0 + 4, 20, shade)
    c.rect(x0 + 12, 18, x0 + 13, 20, shade)


def rickshaw(lean, phase, accent):
    """Повозка-рикша со спины, 160×104: два высоких деревянных колеса в железной шине, дощатый
    кузов под красным поручнем, на борту белый круг с солнцем цвета `accent`, поперёк спинки
    сложенный гармошкой верх на золотых шарнирах, из-за него видна бочка сакэ; справа бумажный
    фонарь на коротком крюке, слева флажок цвета `accent` на хлысте (оба ниже головы возницы,
    без шестов и полотнищ); правит ниндзя в синем с красным шарфом и мечом через спину.
    `lean` −1..1 крен."""
    c = Canvas(160, 104)
    sh = lean * 6
    flap = 2 if phase < 0.25 else -1
    _wheel(c, 22 + sh * 0.3, 78, 24, phase, BRASS, METAL, DARK)
    _wheel(c, 138 + sh * 0.3, 78, 24, phase, BRASS, METAL, DARK)
    # Ось и брус под кузовом.
    c.rect(24, 83, 136, 87, DARK)
    c.rect(38, 88, 122, 92, BRASS)
    c.rect(38, 88, 122, 88, GOLD)
    # Кузов: доски поясами, тёмные швы со светлой фаской, лаковые стойки по углам.
    c.poly([(30 + sh, 50), (130 + sh, 50), (126 + sh * 0.6, 90), (34 + sh * 0.6, 90)], BRASS)
    for i, y in enumerate((60, 70, 80)):
        k = (y - 50) / 40.0
        xa = 31 + sh + (4 - sh * 0.4) * k
        xb = 129 + sh - (4 + sh * 0.4) * k
        c.line(xa, y, xb, y, DARK, 1)
        c.line(xa + 2, y + 1, xb - 2, y + 1, GOLD, 1)
        for x in range(46 + i * 9, 120, 31):
            c.rect(x + sh * (1 - 0.4 * k), y - 6, x + sh * (1 - 0.4 * k), y - 1, DARK)
    c.line(31 + sh, 50, 35 + sh * 0.6, 90, DARK, 3)
    c.line(129 + sh, 50, 125 + sh * 0.6, 90, DARK, 3)
    for x, y in ((33, 54), (127, 54), (36, 86), (124, 86)):
        k = (y - 50) / 40.0
        c.rect(x + sh * (1 - 0.4 * k) - 1, y - 1, x + sh * (1 - 0.4 * k) + 1, y + 1, GOLD)
    # Красный лаковый поручень с золотыми оковками.
    c.rect(26 + sh, 45, 134 + sh, 50, RED)
    c.rect(26 + sh, 49, 134 + sh, 50, TAN)
    for x in (26, 76, 129):
        c.rect(x + sh, 45, x + sh + 5, 50, GOLD)
    # Герб на борту: белый круг с солнцем цвета экипажа.
    mx = 80 + sh * 0.8
    c.ellipse(mx, 70, 12, 12, DARK)
    c.ellipse(mx, 70, 11, 11, WHITE)
    c.ellipse(mx, 70, 7, 7, accent)
    # Груз: бочка сакэ в соломе слева, низ закрыт сложенным верхом.
    bx = 54 + sh
    c.rect(bx - 9, 30, bx + 9, 40, SKY)
    c.ellipse(bx, 30, 9, 4, WHITE)
    c.rect(bx - 9, 35, bx + 9, 36, BRASS)
    c.rect(bx - 2, 31, bx + 2, 33, RED)
    # Свёрток циновки справа: торец спиралью, верёвка.
    rx = 108 + sh
    c.rect(rx - 12, 32, rx + 10, 39, SKY)
    c.ellipse(rx + 10, 35.5, 4, 4, SKY)
    c.ellipse(rx + 10, 35.5, 2, 2, BRASS)
    for x in (-8, 0):
        c.rect(rx + x, 32, rx + x + 1, 39, RED)
    c.rect(rx - 12, 32, rx + 8, 32, WHITE)
    # Сложенный верх рикши поперёк спинки: тёмная гармошка, складки, дуги рёбер, шарниры золотом.
    c.rect(30 + sh, 38, 130 + sh, 45, DARK)
    c.rect(30 + sh, 38, 130 + sh, 38, METAL)
    for x in range(36, 128, 8):
        c.rect(x + sh, 39, x + sh, 44, METAL if (x // 8) % 2 else K)
    c.rect(30 + sh, 42, 130 + sh, 42, K)
    for x in (30, 130):
        c.ellipse(x + sh, 42, 4, 4, DARK)
        c.ellipse(x + sh, 42, 2, 2, GOLD)
    # Бумажный фонарь на коротком крюке у правого угла: висит над колесом, ниже плеч возницы.
    hx = 131 + sh * 1.1
    lx = 141 + sh * 1.15
    c.line(hx, 44, hx + 2, 31, BRASS, 2)
    c.line(hx + 2, 31, lx, 30, BRASS, 2)
    c.rect(lx - 2, 31, lx + 2, 32, DARK)
    c.ellipse(lx, 39, 5, 6, SKY)
    c.ellipse(lx, 39, 3, 4, GOLD)
    for y in (36, 39, 42):
        c.rect(lx - 4, y, lx + 4, y, AQUA)
    c.rect(lx - 2, 45, lx + 2, 46, DARK)
    c.rect(lx, 47, lx, 49, RED)
    # Флажок на коротком хлысте у левого угла: треугольник цвета экипажа, полощется.
    fx = 28 + sh * 1.1
    c.rect(fx, 31, fx + 1, 45, BRASS)
    c.poly([(fx, 31), (fx - 11, 34 + flap), (fx, 38)], accent)
    c.set(fx - 3, 34, WHITE)
    # Ниндзя со спины: концы шарфа на ветру, меч наискось, обмотки на предплечьях.
    x0 = 72 + sh * 1.2
    for j in (0, 1):
        pts = []
        for k in range(15):
            wave = math.sin(k * 0.6 + phase * math.pi * 2 + j * 1.3) * 2.2 * k / 14
            pts.append((x0 + 2 - k * 0.95, 22 + j * 2 + wave + j * k * 0.3))
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1], b[0], b[1], RED, 3)
    _driver(c, x0, phase, SEA, NAVY, WHITE)
    c.line(x0 + 17, 22, x0 + 1, 39, DARK, 3)
    c.rect(x0 - 1, 38, x0 + 1, 40, GOLD)
    c.line(x0 + 19, 19, x0 + 24, 10, DARK, 3)
    c.set(x0 + 21, 16, METAL)
    c.set(x0 + 22, 13, METAL)
    c.ellipse(x0 + 24, 9, 1.5, 1.5, GOLD)
    c.ellipse(x0 + 18, 21, 3, 2, GOLD)
    c.rect(x0 + 1, 20, x0 + 15, 23, RED)
    c.ellipse(x0 + 1, 22, 3, 3, RED)
    c.finish()
    return c


def clan_cart(lean, phase, accent):
    """Повозка чужого клана со спины, 160×104: чёрный лаковый короб с красным поясом и
    загнутыми вверх углами, колёса чёрные с красной шиной, на борту герб и пояс цвета `accent`,
    под загнутыми углами висят бумажные фонари того же цвета (качаются по `phase`), на спинке
    низкая лаковая решётка; правит ниндзя в красном с серпами накрест. Без знамён и шестов."""
    c = Canvas(160, 104)
    sh = lean * 6
    swing = 3 if phase < 0.25 else -2
    _wheel(c, 22 + sh * 0.3, 79, 23, phase, DARK, RED, GREY)
    _wheel(c, 138 + sh * 0.3, 79, 23, phase, DARK, RED, GREY)
    c.rect(24, 84, 136, 88, METAL)
    c.rect(40, 89, 120, 92, DARK)
    mon = RED if accent == WHITE else WHITE
    # Низкая решётка спинки над поясом: лаковые стойки и перекладина, ниже плеч возницы.
    for x in range(40, 124, 10):
        c.rect(x + sh, 40, x + sh + 1, 48, DARK)
    c.rect(36 + sh, 39, 124 + sh, 41, DARK)
    c.rect(36 + sh, 39, 124 + sh, 39, METAL)
    # Короб: чёрный лак, красный пояс поверху с загнутыми углами, золотая кайма, заклёпки.
    c.poly([(28 + sh, 53), (132 + sh, 53), (124 + sh * 0.6, 90), (36 + sh * 0.6, 90)], DARK)
    c.poly([(30 + sh, 56), (62 + sh, 56), (60 + sh * 0.6, 86), (38 + sh * 0.6, 86)], METAL)
    c.poly([(32 + sh, 58), (60 + sh, 58), (58 + sh * 0.6, 84), (40 + sh * 0.6, 84)], DARK)
    c.poly([(98 + sh, 56), (130 + sh, 56), (122 + sh * 0.6, 86), (100 + sh * 0.6, 86)], METAL)
    c.poly([(100 + sh, 58), (128 + sh, 58), (120 + sh * 0.6, 84), (102 + sh * 0.6, 84)], DARK)
    c.rect(22 + sh, 48, 138 + sh, 53, RED)
    c.rect(22 + sh, 52, 138 + sh, 53, TAN)
    c.poly([(22 + sh, 53), (12 + sh, 40), (17 + sh, 39), (30 + sh, 48)], RED)
    c.poly([(138 + sh, 53), (148 + sh, 40), (143 + sh, 39), (130 + sh, 48)], RED)
    c.ellipse(14 + sh, 39, 2.5, 2.5, GOLD)
    c.ellipse(146 + sh, 39, 2.5, 2.5, GOLD)
    for x in range(34, 130, 12):
        c.rect(x + sh, 50, x + sh + 1, 51, GOLD)
    c.rect(36 + sh * 0.6, 87, 124 + sh * 0.6, 88, GOLD)
    # Пояс цвета клана по низу короба и фонари под загнутыми углами: шнур, каркас, кисть.
    c.rect(38 + sh * 0.6, 80, 122 + sh * 0.6, 83, accent)
    c.rect(38 + sh * 0.6, 83, 122 + sh * 0.6, 83, mon if accent == WHITE else DARK)
    for cx0, d in ((14, -1), (146, 1)):
        lx = cx0 + sh + swing * 0.4
        c.line(cx0 + sh, 41, lx, 45, BRASS, 1)
        c.rect(lx - 2, 45, lx + 2, 46, DARK)
        c.ellipse(lx, 52, 5, 6, accent)
        c.rect(lx - 4, 50, lx + 4, 50, mon)
        c.rect(lx - 4, 54, lx + 4, 54, mon)
        c.rect(lx - 2, 58, lx + 2, 59, DARK)
        c.rect(lx, 60, lx, 62, GOLD)
    # Герб клана: золотое кольцо, круг цвета экипажа, три тёмные полосы.
    mx = 80 + sh * 0.8
    c.ellipse(mx, 70, 12, 12, GOLD)
    c.ellipse(mx, 70, 10, 10, accent)
    for y in (66, 70, 74):
        c.rect(mx - 5, y, mx + 5, y, DARK if accent != WHITE else RED)
    # Ниндзя в красном: серпы накрест за спиной, тёмная повязка с концами.
    x0 = 72 + sh * 1.2
    for d in (-1, 1):
        hx = x0 + 8 + d * 12
        c.line(x0 + 8 - d * 7, 40, hx, 19, BRASS, 2)
        c.line(hx, 19, hx + d * 8, 15, GREY, 2)
        c.line(hx + d * 8, 15, hx + d * 12, 21, GREY, 2)
        c.set(hx + d * 12, 23, GREY)
    _driver(c, x0, phase, RED, TAN, DARK)
    c.rect(x0, 10, x0 + 16, 12, DARK)
    for j in (0, 1):
        c.line(x0 + 16, 11, x0 + 23 + j, 12 + j * 4 + (1 if phase < 0.25 else -1), DARK, 2)
    c.finish()
    return c


def carts_strip(accent, rival):
    """Три крена (влево, прямо, вправо) по два кадра: лента 6 кадров по 160, порядок как у пиратов."""
    frames = []
    for lean in (-1.0, 0.0, 1.0):
        for ph in (0.0, 0.5):
            frames.append(clan_cart(lean, ph, accent) if rival else rickshaw(lean, ph, accent))
    return strip(frames)


def maple():
    """Красный клён у обочины, 120×240 (место пальмы): тёмный изогнутый ствол с развилкой,
    крона плоскими ярусами-облаками, листва красная с коралловым светом и терракотовой тенью,
    у корней мох, камень и опавшие листья."""
    rng = random.Random(281)
    c = Canvas(120, 240)
    # Ствол: изгиб буквой S, сужается кверху; светлая кора штрихами слева.
    pts = []
    for i in range(150):
        k = i / 149
        pts.append((56 + 12 * math.sin(k * math.pi * 1.5) + 6 * k, 239 - i))
    for i, (x, y) in enumerate(pts):
        w = 8 - i / 30
        c.rect(x - w, y, x + w, y, DARK)
        if (i // 5) % 3 != 0:
            c.rect(x - w + 1, y, x - w + 2, y, BRASS)
        if (i // 7) % 2 == 0:
            c.set(x + 1, y, METAL)
    fork = pts[104]
    top = pts[-1]
    # Ветви к ярусам кроны.
    for tx, ty, t in ((26, 78, 4), (96, 72, 4), (22, 112, 3), (88, 108, 3)):
        c.line(fork[0], fork[1], tx, ty, DARK, t)
    c.line(top[0], top[1], 60, 44, DARK, 4)
    # Ярусы кроны: тень снизу, красная масса, свет пятнами сверху слева.
    tiers = ((60, 36, 36, 22), (28, 70, 26, 15), (94, 64, 25, 16), (58, 84, 28, 12), (22, 108, 19, 10),
             (90, 102, 22, 11))
    for cx, cy, rx, ry in tiers:
        c.ellipse(cx + 1, cy + 4, rx, ry, TAN)
    for cx, cy, rx, ry in tiers:
        c.ellipse(cx, cy, rx, ry, RED)
        # Зубчатая кромка: листья выступают за овал.
        for a in range(0, 360, 14):
            ra = math.radians(a + rng.uniform(-4, 4))
            ex = cx + math.cos(ra) * rx
            ey = cy + math.sin(ra) * ry
            c.ellipse(ex, ey, 3.2, 2.6, RED if math.sin(ra) < 0.4 else TAN)
    for cx, cy, rx, ry in tiers:
        for _ in range(int(rx * ry * 0.09)):
            a = rng.uniform(0, math.pi * 2)
            r = rng.uniform(0, 0.9)
            x = cx + math.cos(a) * rx * r
            y = cy + math.sin(a) * ry * r
            lit = (x - cx) / rx + (y - cy) / ry < -0.1
            col = (AQUA if rng.random() < 0.8 else GOLD) if lit else TAN
            # Лист звёздочкой.
            c.set(x, y, col)
            c.set(x - 1, y, col)
            c.set(x + 1, y, col)
            c.set(x, y - 1, col)
            if rng.random() < 0.5:
                c.set(x, y + 1, col)
    # Мох, камень и опавшие листья у корней.
    c.poly([(26, 239), (38, 228), (60, 224), (84, 229), (94, 239)], VIOLET)
    c.poly([(40, 239), (52, 231), (70, 232), (80, 239)], PLUM)
    c.rect(48, 226, 66, 239, DARK)
    c.rect(49, 226, 50, 239, BRASS)
    c.poly([(84, 239), (90, 228), (104, 226), (114, 239)], METAL)
    c.poly([(90, 231), (103, 228), (106, 233), (92, 235)], GREY)
    for lx, ly in ((14, 236), (22, 232), (34, 237), (76, 236), (110, 222), (8, 228)):
        c.rect(lx, ly, lx + 2, ly + 1, RED)
        c.set(lx + 1, ly - 1, AQUA)
    for _ in range(7):
        x = rng.uniform(10, 110)
        y = rng.uniform(128, 214)
        c.rect(x, y, x + 1, y + 1, RED)
        c.set(x + 2, y, AQUA)
    c.finish()
    return c


def _leaf(c, x, y, a, length, w, col):
    """Узкий лист бамбука от (x, y) под углом `a` (радианы, 0 вправо, плюс вниз)."""
    ux, uy = math.cos(a), math.sin(a)
    mx, my = x + ux * length * 0.45, y + uy * length * 0.45
    c.poly([(x, y), (mx - uy * w, my + ux * w), (x + ux * length, y + uy * length), (mx + uy * w, my - ux * w)], col)


def bamboo():
    """Бамбук у обочины, 120×240 (место второй пальмы): четыре коленчатых стебля разной высоты
    с наклоном, светлые кольца на узлах, листья веерами к верхушкам, у земли ростки и камень."""
    c = Canvas(120, 240)
    stalks = ((24, 14, 30, 4, -5), (50, 56, 8, 5, 4), (76, 70, 44, 4, -3), (98, 108, 22, 4, 5))
    sprays = []
    for n, (xb, xt, top, w, bend) in enumerate(stalks):
        length = 239 - top
        for i in range(length + 1):
            k = i / length
            x = xb + (xt - xb) * k + bend * math.sin(k * math.pi)
            y = 239 - i
            ww = w - (1 if k > 0.7 else 0)
            c.rect(x - ww, y, x + ww, y, VIOLET)
            c.set(x + ww, y, PLUM)
            c.set(x + ww - 1, y, PLUM)
            c.set(x - ww + 1, y, SKY)
            j = (i + n * 7) % 24
            if j == 0:
                c.rect(x - ww - 1, y, x + ww + 1, y, PLUM)
            elif j == 1:
                c.rect(x - ww, y, x + ww, y, SKY)
                if k > 0.38:
                    sprays.append((x, y, 1 if ((i + n * 7) // 24 + n) % 2 else -1, k))
        sprays.append((xt, top, 1, 1.0))
        sprays.append((xt, top, -1, 1.0))
    # Веера листьев: сначала дальние тёмные, потом ближние.
    for dark in (True, False):
        for x, y, side, k in sprays:
            c.line(x, y, x + side * 9, y - 5, PLUM, 1) if dark else None
            bx, by = x + side * 9, y - 5
            for m, da in enumerate((-0.25, 0.3, 0.85)):
                a = (0.0 if side > 0 else math.pi) + side * da
                if dark == (m == 1):
                    continue
                _leaf(c, bx, by, a, 15 + k * 7 - m * 2, 2.6, PLUM if dark else VIOLET)
    # Ростки и камень у земли.
    for sx, h in ((38, 20), (64, 14), (88, 24)):
        c.poly([(sx - 5, 239), (sx, 239 - h), (sx + 5, 239)], BRASS)
        for y in range(239 - h + 5, 239, 5):
            c.line(sx - 3, y + 2, sx + 3, y - 1, DARK, 1)
        c.set(sx, 239 - h + 1, GOLD)
    c.poly([(0, 239), (4, 228), (16, 226), (22, 239)], METAL)
    c.poly([(4, 231), (15, 228), (17, 233), (6, 235)], GREY)
    c.finish()
    return c


def stone_lantern():
    """Приземистый каменный фонарь у дороги, 96×64: широкая шляпа-крыша с навершием, светильня
    с горящими окошками, плита и три гнутые ноги; на шляпе мох, у ног трава."""
    c = Canvas(96, 64)
    # Ноги: две гнутые по краям, третья в тени сзади.
    c.rect(44, 42, 52, 62, METAL)
    c.rect(46, 42, 52, 62, DARK)
    c.poly([(8, 63), (20, 63), (32, 42), (22, 42), (12, 52)], GREY)
    c.poly([(88, 63), (76, 63), (64, 42), (74, 42), (84, 52)], METAL)
    # Плита и светильня с окошками.
    c.rect(18, 37, 78, 42, GREY)
    c.rect(18, 41, 78, 42, METAL)
    c.rect(28, 21, 68, 37, METAL)
    c.rect(28, 21, 31, 37, GREY)
    for x in (36, 53):
        c.rect(x - 1, 23, x + 9, 35, DARK)
        c.rect(x, 24, x + 8, 34, GOLD)
        c.rect(x + 2, 26, x + 6, 32, SKY)
        c.rect(x + 4, 24, x + 4, 34, DARK)
        c.rect(x, 29, x + 8, 29, DARK)
    # Шляпа: широкий скат с загнутыми краями, тёмный испод, навершие луковкой.
    c.poly([(2, 20), (6, 15), (30, 7), (66, 7), (90, 15), (94, 20), (86, 23), (10, 23)], GREY)
    c.poly([(48, 7), (66, 7), (90, 15), (94, 20), (86, 23), (48, 23)], METAL)
    c.rect(10, 22, 86, 23, DARK)
    for x0, x1 in ((30, 16), (48, 48), (66, 80)):
        c.line(x0, 8, x1, 21, DARK, 1)
    c.rect(42, 4, 54, 7, METAL)
    c.ellipse(48, 3, 4, 2.5, GREY)
    # Мох на шляпе и трещина.
    for mx, my, r in ((16, 15, 5), (26, 11, 5), (38, 9, 4), (72, 12, 4)):
        c.ellipse(mx, my, r, 2.2, VIOLET)
        c.set(mx + 1, my + 1, PLUM)
        c.set(mx - 2, my, PLUM)
    c.line(62, 22, 65, 30, DARK, 1)
    c.line(65, 30, 63, 36, DARK, 1)
    # Трава у ног.
    for gx in (4, 24, 38, 58, 70, 90):
        c.poly([(gx - 4, 63), (gx - 2, 56), (gx, 61), (gx + 2, 54), (gx + 4, 63)], VIOLET)
        c.set(gx + 2, 58, PLUM)
    return c.finish()


def sake_barrel():
    """Бочка сакэ в соломе, 48×64: пузатая, в светлой рогоже с верёвками накрест, на боку знак
    тушью и красная печать, сверху крышка с узлом."""
    c = Canvas(48, 64)
    c.rect(6, 10, 41, 58, SKY)
    c.rect(4, 20, 43, 48, SKY)
    c.ellipse(24, 58, 17.5, 5, SKY)
    c.ellipse(24, 10, 17.5, 6, WHITE)
    c.ellipse(24, 10, 12, 3.5, SKY)
    # Рогожа: штрихи соломы и тень справа.
    for x in range(7, 42, 3):
        for y in range(18 + (x * 5) % 4, 58, 7):
            c.rect(x, y, x, y + 2, BRASS)
    c.rect(39, 18, 43, 56, AQUA)
    # Верёвки: два пояса и сетка ромбами между ними.
    for y in (17, 51):
        c.rect(4, y, 43, y + 2, BRASS)
        for x in range(5, 43, 4):
            c.set(x, y + 1, GOLD)
    for x in (4, 17, 30):
        c.line(x, 20, x + 6, 26, BRASS, 1)
        c.line(x + 13, 20, x + 7, 26, BRASS, 1)
        c.line(x, 50, x + 6, 44, BRASS, 1)
        c.line(x + 13, 50, x + 7, 44, BRASS, 1)
    # Знак тушью и красная печать.
    c.rect(13, 28, 34, 30, K)
    c.rect(22, 24, 25, 36, K)
    c.line(23, 31, 14, 42, K, 3)
    c.line(24, 31, 33, 42, K, 3)
    c.rect(33, 35, 39, 41, RED)
    c.rect(35, 37, 37, 39, WHITE)
    # Узел на крышке.
    c.rect(20, 3, 28, 7, BRASS)
    c.rect(22, 1, 26, 3, GOLD)
    return c.finish()


def sign(right):
    """Указатель поворота, 96×112: белая доска в деревянной раме под двускатной крышей на
    столбе, красные шевроны кистью в сторону поворота, столб в верёвке, у основания камень."""
    c = Canvas(96, 112)
    c.rect(44, 54, 51, 111, BRASS)
    c.rect(49, 54, 51, 111, DARK)
    for y in (64, 68):
        c.rect(43, y, 52, y + 1, WHITE)
    c.poly([(34, 111), (38, 102), (58, 102), (62, 111)], METAL)
    c.rect(40, 103, 54, 104, GREY)
    c.ellipse(36, 109, 4, 2, VIOLET)
    # Доска в раме.
    c.rect(6, 15, 89, 57, BRASS)
    c.rect(9, 19, 86, 53, WHITE)
    c.rect(6, 55, 89, 57, DARK)
    for x, y in ((7, 17), (88, 17), (7, 54), (88, 54)):
        c.rect(x - 1, y - 1, x + 1, y + 1, GOLD)
    d = 1 if right else -1
    for k in range(3):
        cx = 48 + d * (k * 22 - 22)
        c.poly([(cx - d * 8, 22), (cx + d * 9, 36), (cx - d * 8, 50), (cx - d * 1, 36)], RED)
    # Крыша: фронтон и два ската с выносом, конёк золотом.
    c.poly([(6, 15), (48, 5), (89, 15)], BRASS)
    c.poly([(0, 15), (48, 2), (95, 15), (95, 19), (48, 7), (0, 19)], DARK)
    for x in range(8, 92, 8):
        y = 15 - (1.0 - abs(x - 48) / 48.0) * 13
        c.rect(x, y + 2, x, y + 4, METAL)
    c.rect(45, 1, 51, 4, GOLD)
    return c.finish()


def _roof(c, cx, ye, yt, hr, ht):
    """Крыша яруса пагоды: скат от полуширины `ht` на высоте `yt` к свесу `hr` на `ye`, углы
    загнуты вверх; синяя черепица рядами, тёмная кромка, золото на углах."""
    c.poly([(cx - ht, yt), (cx + ht, yt), (cx + hr - 10, ye - 4), (cx + hr, ye - 9), (cx + hr - 1, ye),
            (cx - hr + 1, ye), (cx - hr, ye - 9), (cx - hr + 10, ye - 4)], NAVY)
    for i in range(-8, 9):
        k = i / 8.0
        c.line(cx + ht * k, yt + 1, cx + (hr - 6) * k, ye - 3, SEA, 1)
    c.rect(cx - hr + 2, ye - 2, cx + hr - 2, ye, DARK)
    c.rect(cx - ht, yt, cx + ht, yt + 1, DARK)
    c.ellipse(cx - hr + 1, ye - 9, 2, 2, GOLD)
    c.ellipse(cx + hr - 1, ye - 9, 2, 2, GOLD)


def _tier(c, cx, y0, y1, half, cols):
    """Стена яруса: белая штукатурка, красные столбы и перила, решётчатые окна со светом."""
    c.rect(cx - half, y0, cx + half, y1, WHITE)
    c.rect(cx - half, y1 - 4, cx + half, y1, RED)
    c.rect(cx - half, y1 - 1, cx + half, y1, TAN)
    c.rect(cx - half, y0, cx + half, y0 + 2, GREY)
    for i in range(cols + 1):
        x = cx - half + (2 * half) * i / cols
        c.rect(x - 1, y0, x + 1, y1, RED)
    for i in range(cols):
        xa = cx - half + (2 * half) * i / cols + 4
        xb = cx - half + (2 * half) * (i + 1) / cols - 4
        if xb - xa < 4:
            continue
        c.rect(xa, y0 + 4, xb, y1 - 7, DARK)
        c.rect(xa + 1, y0 + 5, xb - 1, y1 - 8, GOLD)
        mid = int((xa + xb) / 2)
        c.rect(mid, y0 + 5, mid, y1 - 8, DARK)
        c.rect(xa + 1, int((y0 + y1) / 2) - 1, xb - 1, int((y0 + y1) / 2) - 1, DARK)


def pagoda():
    """Пагода у дороги, 192×160 (место хижины): три яруса белых стен с красными столбами под
    синими крышами с загнутыми углами, золотой шпиль с кольцами, каменное основание со
    ступенями, тёмная дверь с фонарями по бокам."""
    c = Canvas(192, 160)
    cx = 96
    # Основание и ступени.
    c.rect(18, 146, 173, 159, METAL)
    c.rect(18, 146, 173, 148, GREY)
    for x in range(26, 172, 22):
        c.rect(x, 149, x, 159, DARK)
    c.rect(18, 153, 173, 153, DARK)
    c.rect(76, 148, 116, 159, GREY)
    for y in (151, 155):
        c.rect(76, y, 116, y, METAL)
    # Шпиль: стержень, кольца, навершие.
    c.rect(cx - 1, 3, cx + 1, 34, GOLD)
    for i, y in enumerate((11, 16, 21, 26)):
        c.ellipse(cx, y, 3 + i, 1.5, BRASS if i % 2 else GOLD)
    c.ellipse(cx, 4, 2.5, 2.5, GOLD)
    # Ярусы снизу вверх: стена, над ней крыша.
    _tier(c, cx, 116, 146, 52, 6)
    _tier(c, cx, 82, 102, 38, 4)
    _tier(c, cx, 50, 68, 26, 3)
    _roof(c, cx, 118, 100, 88, 40)
    _roof(c, cx, 84, 66, 70, 28)
    _roof(c, cx, 52, 30, 54, 3)
    # Дверь с оковкой и бумажные фонари по бокам.
    c.rect(82, 122, 110, 146, DARK)
    c.rect(84, 124, 108, 146, BRASS)
    c.rect(95, 124, 96, 146, DARK)
    for x in (88, 103):
        c.rect(x, 134, x + 1, 135, GOLD)
    for x in (72, 120):
        c.rect(x - 1, 121, x + 1, 123, DARK)
        c.ellipse(x, 129, 5, 6, RED)
        c.rect(x - 4, 129, x + 4, 129, GOLD)
        c.rect(x - 2, 135, x + 2, 136, DARK)
    # Кусты у основания.
    for bx, r in ((12, 12), (180, 12)):
        c.ellipse(bx, 150, r, 10, PLUM)
        c.ellipse(bx - 2, 147, r - 4, 6, VIOLET)
        c.rect(bx - r, 155, bx + r, 159, PLUM)
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
        "palm": maple(),
        "palm_b": bamboo(),
        "road_rock": stone_lantern(),
        "road_barrel": sake_barrel(),
        "sign_left": sign(False),
        "sign_right": sign(True),
        "road_hut": pagoda(),
    }
    for i, accent in enumerate((SEA, GOLD, VIOLET, WHITE)):
        out["cart_%d" % i] = carts_strip(accent, True)
    return out


def horizon():
    """Горизонт в своей палитре `NINJA_SKY`."""
    return {"road_sky": sky(), "road_islands": islands(), "road_sea": sea()}


def road_palette():
    return {"road_colors": road_colors()}


def preview(path):
    items = ninja16.shaded(sprites())
    for key, canvas in horizon().items():
        items[key] = (canvas, NINJA_SKY)
    for key, canvas in road_palette().items():
        items[key] = (canvas, ROAD_COLORS)
    ninja16.save_sheet(path, items, scale=2, max_w=512)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
