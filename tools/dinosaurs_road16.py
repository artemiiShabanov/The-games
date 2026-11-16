#!/usr/bin/env python3
"""Набор «Динозавры» для гонки × 16/32-bit «псевдо-3D» (#144), зеркало `space_road16.py` и
`pixel_road16.py`: те же ключи, размеры холстов и порядок кадров, чтобы `racing_bit16.gd` брала их
без правок. Герой едет на каменной тележке с колёсами-валунами (вид сзади), соперники-рапторы на
тележках из костей; у дороги древовидный папоротник и хвощи вместо пальм, шалаш из бивней и шкур
вместо хижины, глыба лавы, плетёная корзина с яйцами, указатели из шкуры на костях. На горизонте
бирюзовое небо с тёплой дымкой, солнцем и птеродактилями, вулканы с лавой и шеи зауроподов,
джунгли с лавовыми ручьями вместо моря. Дорога из красной глины, обочина лесная подстилка.

Транспорт без паруса и мачты: на месте флага короткая кость с лоскутом шкуры ниже головы
водителя, у костяной тележки пара низких рогов по углам кормы.

Тележки и пропы в палитре `dinosaurs16.PALETTE`, горизонт в своей (`DINOSAURS_SKY`), цвета
дороги лентой `road_colors` по местам `ROAD_COLORS`.

    python3 tools/dinosaurs_road16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dinosaurs16  # noqa: E402
from dinosaurs16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS,  # noqa: E402,F401
                         METAL, DARK, RED, VIOLET, PLUM)

# Палитра горизонта: небо, облака, джунгли, вулканы. Места те же по смыслу, что у пиратов.
S0, S1, S2, S3, C0, C1, C2, M0, M1, M2, M3, I0, I1, I2, I3, SUN = range(16)
DINOSAURS_SKY = [
    (0x22, 0x6E, 0x86),  # S0  небо наверху
    (0x44, 0x9C, 0x9E),  # S1
    (0x86, 0xC8, 0xB0),  # S2
    (0xF2, 0xE2, 0xAA),  # S3  тёплая дымка у горизонта
    (0xDC, 0x9A, 0x6C),  # C0  тень облака, пепел
    (0xF4, 0xCC, 0x92),  # C1  облако, солнце
    (0xFE, 0xF6, 0xDC),  # C2  свет облака, диск солнца
    (0x1E, 0x58, 0x54),  # M0  джунгли вдали
    (0x2E, 0x7A, 0x4C),  # M1  джунгли
    (0x58, 0x98, 0x44),  # M2  подстилка у дороги
    (0xF0, 0x74, 0x28),  # M3  лавовый ручей
    (0x74, 0x9A, 0x9E),  # I0  вулкан в дымке
    (0x46, 0x52, 0x66),  # I1  вулкан, птеродактиль
    (0x2C, 0x62, 0x62),  # I2  зауропод
    (0xFA, 0xB0, 0x38),  # I3  жар лавы
    (0x76, 0xA4, 0x4C),  # SUN подстилка у кромки дороги
]

# Цвета дороги по местам ленты `road_colors` (демка берёт их по индексу).
ROAD_COLORS = [
    (0xC2, 0x6E, 0x46),  # 0 глина светлая
    (0xB4, 0x62, 0x3E),  # 1 глина тёмная
    (0x5A, 0x36, 0x30),  # 2 бордюр лавовый камень
    (0xF4, 0xEE, 0xDA),  # 3 бордюр кость
    (0xF4, 0xDC, 0x9A),  # 4 разметка охрой
    (0x76, 0xA4, 0x4C),  # 5 подстилка светлая
    (0x68, 0x96, 0x44),  # 6 подстилка тёмная
    (0x2C, 0x80, 0x84),  # 7 дымка вдали
]


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wellipse(c, cx, cy, rx, ry, col):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                _wset(c, x, y, col)


def _curve(c, p0, p1, p2, w0, w1, col, steps=60):
    """Кривая Безье по трём точкам кружками: толщина от `w0` к `w1` (рог, бивень, хвост)."""
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * p1[1] + t * t * p2[1]
        r = (w0 + (w1 - w0) * t) / 2.0
        c.ellipse(x, y, r, r, col)


# --- Горизонт ----------------------------------------------------------------------------------

def sky():
    """Небо, 512×128, стыкуется по краям: бирюза наверху, тёплая дымка у горизонта, низкое солнце
    с ореолом, вытянутые облака пепла и клин птеродактилей."""
    rng = random.Random(471)
    c = Canvas(512, 128)
    bands = [(0, S0), (36, S1), (72, S2), (102, S3)]
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
    # Солнце: ореол шашкой, диск, полосы дымки поперёк низа.
    sx, sy = 372, 84
    for y in range(sy - 30, sy + 31):
        for x in range(sx - 30, sx + 31):
            d = math.hypot(x - sx, y - sy)
            if d <= 30 and (d <= 24 or (x + y) % 2 == 0) and y < 128:
                c.set(x, y, S3 if d > 24 or (d > 20 and (x + y) % 2 == 0) else C1)
    _wellipse(c, sx, sy, 16, 16, C2)
    for y, half in ((90, 20), (95, 15)):
        c.rect(sx - half, y, sx + half, y, C1)
    # Облака пепла: длинные плоские гряды, свет сверху, тень снизу.
    for _ in range(9):
        x = rng.uniform(0, 512)
        y = rng.randint(20, 96)
        w = rng.randint(22, 54)
        for k in range(3):
            ox = rng.uniform(-w * 0.4, w * 0.4)
            ww = w * rng.uniform(0.4, 0.8)
            _wellipse(c, x + ox, y + k * 2 + 1, ww, 3.2, C0)
            _wellipse(c, x + ox, y + k * 2, ww, 2.6, C1)
        _wellipse(c, x - w * 0.15, y - 1, w * 0.45, 1.6, C2)
    # Птеродактили: клин галочек с гребнем, ближний крупнее.
    for px, py, s in ((96, 40, 7), (120, 30, 4), (138, 48, 4), (250, 22, 3), (464, 54, 5)):
        for i in range(s + 1):
            _wset(c, px - i, py - int(i * 0.5) + (i * i) // (s + 2), I1)
            _wset(c, px + i, py - int(i * 0.5) + (i * i) // (s + 2), I1)
            if i < s - 1:
                _wset(c, px - i, py - int(i * 0.5) + (i * i) // (s + 2) + 1, I1)
                _wset(c, px + i, py - int(i * 0.5) + (i * i) // (s + 2) + 1, I1)
        _wset(c, px, py + 1, I1)
        _wset(c, px + 1, py - 1, I1)
        _wset(c, px + 2, py - 2, I1)
    return c


def islands():
    """Вулканы и зауроподы на горизонте, 512×40, прозрачный верх: дальние конусы в дымке,
    ближний вулкан с кратером, жаром и потёками лавы, перед ними шеи зауроподов."""
    c = Canvas(512, 40)
    # Конусы: (центр, полуширина основания, высота, ближний).
    for cx, w, h, near in ((70, 60, 20, False), (200, 44, 14, False), (310, 86, 34, True), (446, 56, 18, False)):
        crater = max(4, w // 9)
        for x in range(int(cx - w), int(cx + w) + 1):
            k = abs(x - cx) / w
            # Вогнутый склон, срезанная вершина с выемкой кратера.
            top = 39 - h * (1.0 - k) ** 1.5 * 1.25
            lip = 39 - h + (0 if abs(x - cx) > crater * 0.5 else 2)
            top = int(max(top, lip) + abs((x * 7) % 5 - 2) * 0.3)
            for y in range(top, 40):
                col = I0 if not near else I1
                if near and (x - cx) < -4 and y < top + 2:
                    col = I0
                _wset(c, x, y, col)
        if near:
            # Жар в кратере и два потёка лавы по склону.
            for x in range(cx - crater // 2, cx + crater // 2 + 1):
                _wset(c, x, 39 - h + 2, I3)
                _wset(c, x, 39 - h + 1, M3)
            for x0, dx, n in ((cx - 2, -0.55, 22), (cx + 3, 0.7, 16)):
                x = float(x0)
                for i in range(n):
                    y = 39 - h + 3 + i
                    _wset(c, x, y, I3 if i < 6 else M3)
                    if i % 5 == 2:
                        _wset(c, x + 1, y, M3)
                    x += dx + 0.3 * math.sin(i * 0.9)
            # Клуб пепла над кратером.
            for ox, oy, r in ((2, -1, 3), (6, -3, 3), (11, -4, 2)):
                _wellipse(c, cx + ox, 39 - h + oy, r, 1.6, I0)
        else:
            _wset(c, cx, 39 - h + 1, I3)
            _wset(c, cx - 1, 39 - h + 1, I3)
    # Зауроподы: горб спины, длинная шея дугой, маленькая голова, хвост.
    for bx, s, face in ((150, 1.0, 1), (236, 0.7, -1), (404, 0.85, 1), (20, 0.6, 1)):
        _wellipse(c, bx, 40, 17 * s, 11 * s, I2)
        n = int(30 * s)
        hx = hy = 0
        for i in range(n + 1):
            t = i / n
            hx = bx + face * (11 * s + t * 13 * s + math.sin(t * math.pi) * 4 * s)
            hy = 34 - 3 * s - t * 23 * s
            r = (3.4 - 2.2 * t) * s
            _wellipse(c, hx, hy, max(0.9, r), max(0.9, r), I2)
        _wellipse(c, hx + face * 2.5 * s, hy, 3.2 * s, 1.6 * s, I2)
        for i in range(int(22 * s)):
            t = i / (22 * s)
            x = bx - face * (13 * s + i)
            for k in range(int(round((1 - t) * 4 * s)) + 1):
                _wset(c, x, 39 - k - int(t * 3 * s), I2)
    return c


def sea():
    """Джунгли от горизонта, 512×24: тёмный полог вдали, светлее у дороги, кроны кочками,
    лавовые ручьи светящимися штрихами, у нижней кромки полоса подстилки."""
    rng = random.Random(473)
    c = Canvas(512, 24)
    for y in range(24):
        col = M0 if y < 5 else (M1 if y < 15 else M2)
        c.rect(0, y, 511, y, col)
        if y in (5, 15):
            for x in range(0, 512, 2):
                c.set(x + (y % 2), y, M0 if y == 5 else M1)
    c.rect(0, 22, 511, 23, SUN)
    # Кроны: тёмная дуга снизу, светлая макушка.
    for _ in range(70):
        y = rng.randint(3, 20)
        x = rng.uniform(0, 512)
        w = rng.randint(2, 3) + y // 5
        for i in range(-w, w + 1):
            _wset(c, x + i, y + 1, M0 if y < 15 else M1)
        for i in range(-w + 1, w):
            _wset(c, x + i, y, M1 if y < 8 else (M2 if y < 15 else SUN))
    # Лавовые ручьи: короткие горизонтальные штрихи с ярким ядром.
    for _ in range(14):
        y = rng.randint(2, 19)
        x = rng.uniform(0, 512)
        w = rng.randint(3, 6) + y // 3
        for i in range(-w, w + 1):
            _wset(c, x + i + (1 if i > 0 else 0) * (y % 2), y, M3)
        for i in range(-w // 2, w // 2 + 1):
            _wset(c, x + i, y, I3)
    return c


# --- Тележки и пропы (палитра спрайтов) ---------------------------------------------------------

def _boulder_wheel(c, cx, cy, r, phase):
    """Колесо-валун сзади: толстый каменный жернов со сколами, трещины бегут вниз (`phase` 0..1)."""
    w = 10
    c.rect(cx - w, cy - r + 5, cx + w, cy + r - 5, METAL)
    c.rect(cx - w + 1, cy - r + 2, cx + w - 1, cy + r - 2, METAL)
    c.rect(cx - w + 4, cy - r, cx + w - 4, cy + r, METAL)
    c.rect(cx - w + 2, cy - r + 5, cx - w + 3, cy + r - 6, GREY)
    step = 8
    off = int(phase * step)
    for i, y in enumerate(range(int(cy - r + 3) + off, int(cy + r - 5), step)):
        d = 1 if i % 2 == 0 else -1
        c.line(cx - w + 5, y + d, cx - 1, y + 2 - d, DARK, 1)
        c.line(cx - 1, y + 2 - d, cx + w - 2, y + 1, DARK, 1)
        c.rect(cx - 3 + d * 3, y + 4, cx - 2 + d * 3, y + 4, GREY)
    # Скол на кромке: камень, а не шина.
    c.rect(cx + w - 1, cy - 6 + off, cx + w, cy - 3 + off, DARK)


def _bone_wheel(c, cx, cy, r, phase):
    """Колесо костяной тележки сзади: каток из позвонков, отростки бегут вниз (`phase` 0..1)."""
    w = 6
    c.rect(cx - w, cy - r + 3, cx + w, cy + r - 3, WHITE)
    c.rect(cx - w + 2, cy - r, cx + w - 2, cy + r, WHITE)
    c.rect(cx + w - 2, cy - r + 3, cx + w, cy + r - 3, GREY)
    step = 8
    off = int(phase * step)
    for y in range(int(cy - r + 2) + off, int(cy + r - 3), step):
        c.rect(cx - w - 3, y, cx + w + 3, y + 2, WHITE)
        c.rect(cx - w - 3, y + 2, cx + w + 3, y + 2, GREY)
        c.rect(cx - w + 1, y + 4, cx + w - 1, y + 4, GREY)
        c.rect(cx - 1, y + 5, cx, y + 6, METAL)


def _ammonite(c, x, y, r):
    """Аммонит: золотой завиток, вместо фонаря."""
    c.ellipse(x, y, r, r, GOLD)
    c.ellipse(x + 1, y + 1, r - 2, r - 2, BRASS)
    c.ellipse(x, y, r - 3.2, r - 3.2, GOLD)
    c.set(x + 1, y + 1, BRASS)


def stonecart(lean, phase, accent):
    """Каменная тележка со спины, 160×104: два колеса-валуна на бревне-оси, кузов из тёсаных
    плит с трещинами и мхом, по борту полоса охры цвета `accent` зубцами, по углам аммониты, над
    колёсами дуги из рёбер; на борту череп, яйцо, охапка папоротника и короткая кость с лоскутом
    шкуры цвета `accent` (всё ниже головы, без мачты); правит пещерный человек. `lean` −1..1 крен."""
    c = Canvas(160, 104)
    sh = lean * 6
    _boulder_wheel(c, 22 + sh * 0.3, 78, 24, phase)
    _boulder_wheel(c, 138 + sh * 0.3, 78, 24, phase)
    # Ось бревном с кольцами коры и полоз под кузовом.
    c.rect(30, 83, 130, 88, BRASS)
    for x in range(36, 128, 9):
        c.rect(x, 84, x, 88, DARK)
    c.rect(36, 89, 124, 92, DARK)
    # Кузов: каменная ванна, кладка плит в два ряда со сдвигом, трещины.
    c.poly([(30 + sh, 46), (130 + sh, 46), (127 + sh * 0.6, 88), (33 + sh * 0.6, 88)], METAL)
    c.line(32 + sh * 0.8, 68, 128 + sh * 0.8, 68, DARK, 1)
    for x in (62, 100):
        c.line(x + sh, 49, x + sh * 0.8, 67, DARK, 1)
    for x in (47, 82, 114):
        c.line(x + sh * 0.8, 69, x + sh * 0.6, 87, DARK, 1)
    for x, y in ((35, 50), (64, 50), (102, 50), (36, 70), (49, 70), (84, 70), (116, 70)):
        c.rect(x + sh * 0.8, y, x + sh * 0.8 + 6, y, GREY)
        c.rect(x + sh * 0.8, y + 1, x + sh * 0.8, y + 4, GREY)
    c.line(72 + sh * 0.7, 76, 76 + sh * 0.7, 81, DARK, 1)
    c.line(76 + sh * 0.7, 81, 73 + sh * 0.7, 86, DARK, 1)
    c.line(110 + sh * 0.9, 52, 106 + sh * 0.9, 58, DARK, 1)
    # Мох в нижних углах.
    for x, w in ((36, 9), (112, 11)):
        c.rect(x + sh * 0.6, 85, x + sh * 0.6 + w, 87, VIOLET)
        c.rect(x + sh * 0.6 + 2, 83, x + sh * 0.6 + w - 3, 84, VIOLET)
        c.rect(x + sh * 0.6 + 1, 87, x + sh * 0.6 + w - 1, 87, PLUM)
    # Верхняя кромка: светлая тёсаная плита с зазубринами.
    c.rect(28 + sh, 44, 132 + sh, 48, GREY)
    c.rect(28 + sh, 48, 132 + sh, 48, DARK)
    for x in (41, 73, 90, 119):
        c.rect(x + sh, 44, x + sh + 1, 45, METAL)
    # Полоса охры цвета экипажа зубцами посередине борта.
    c.rect(50 + sh * 0.9, 54, 110 + sh * 0.9, 62, DARK)
    c.rect(51 + sh * 0.9, 55, 109 + sh * 0.9, 61, accent)
    for x in range(54, 108, 8):
        c.poly([(x + sh * 0.9, 61), (x + sh * 0.9 + 3, 56), (x + sh * 0.9 + 6, 61)], DARK)
    # Аммониты по углам на месте фонарей.
    for x in (40, 120):
        _ammonite(c, x + sh * 0.9, 57, 5)
    # Дуги из рёбер над колёсами: крылья.
    for wx in (22, 138):
        x = wx + sh * 0.5
        c.rect(x - 12, 49, x + 12, 52, WHITE)
        c.rect(x - 12, 52, x + 12, 52, GREY)
        c.ellipse(x - 12, 51, 2.5, 3, WHITE)
        c.ellipse(x + 12, 51, 2.5, 3, WHITE)
    # Череп ящера на борту слева: низкий трофей.
    c.ellipse(41 + sh, 38, 9, 6, WHITE)
    c.rect(34 + sh, 40, 48 + sh, 43, WHITE)
    c.rect(37 + sh, 37, 39 + sh, 39, DARK)
    c.rect(44 + sh, 37, 46 + sh, 39, DARK)
    for x in (36, 40, 44):
        c.rect(x + sh, 42, x + sh, 43, GREY)
    # Яйцо в крапинку рядом.
    c.ellipse(59 + sh, 38, 5.5, 7, WHITE)
    for dx, dy in ((-2, -2), (2, 0), (-1, 3), (3, -4)):
        c.set(59 + sh + dx, 38 + dy, BRASS)
    # Охапка папоротника справа: лежит на борту, жилки тёмные.
    c.poly([(94 + sh * 1.1, 37), (110 + sh * 1.1, 33), (127 + sh * 1.1, 36), (131 + sh, 45), (93 + sh, 45)], VIOLET)
    for x in (100, 108, 116, 124):
        c.line(x + sh * 1.1, 36, x - 2 + sh, 44, PLUM, 1)
    c.line(96 + sh * 1.05, 41, 128 + sh * 1.05, 40, PLUM, 1)
    c.rect(102 + sh * 1.05, 39, 121 + sh * 1.05, 39, BRASS)
    # Короткая кость с лоскутом шкуры цвета экипажа у заднего угла: ниже головы водителя.
    flap = 2 * math.sin(phase * math.pi * 2)
    c.rect(134 + sh * 1.2, 31, 135 + sh * 1.2, 46, WHITE)
    c.ellipse(134.5 + sh * 1.2, 30, 2, 1.6, WHITE)
    c.poly([(136 + sh * 1.2, 31), (147 + sh * 1.2, 32 + flap), (143 + sh * 1.2, 35 + flap),
            (146 + sh * 1.2, 38 + flap), (136 + sh * 1.2, 38)], accent)
    # Пещерный человек со спины: голая спина, шкура через плечо, руки на поводьях-лианах.
    x0 = 72 + sh * 1.2
    c.rect(x0, 23, x0 + 16, 43, SKIN)
    c.rect(x0 + 13, 24, x0 + 16, 43, TAN)
    c.poly([(x0, 23), (x0 + 5, 23), (x0 + 16, 33), (x0 + 16, 43), (x0, 43)], RED)
    for dx, dy in ((2, 28), (6, 33), (3, 38), (10, 37), (13, 40), (8, 30)):
        c.rect(x0 + dx, dy, x0 + dx + 1, dy + 1, DARK)
    for side in (-1, 1):
        sx = x0 + (0 if side < 0 else 16)
        c.ellipse(sx, 26, 4, 4, SKIN)
        c.line(sx, 26, sx + side * 6, 34, SKIN, 6)
        c.line(sx + side * 6, 34, sx + side * 3, 41, TAN, 5)
        c.ellipse(sx + side * 2.5, 42, 3, 2.5, SKIN)
    # Голова: уши, лохматая копна шире головы, пряди на плечи.
    c.ellipse(x0 + 8, 15, 8.5, 8, SKIN)
    c.ellipse(x0 + 8, 13, 10, 8.5, DARK)
    for dx, n in ((-1, 3), (1, 6), (4, 4), (7, 7), (10, 4), (13, 6), (16, 3)):
        c.rect(x0 + dx, 19, x0 + dx + 1, 21 + n, DARK)
    for dx in (2, 8, 13):
        c.rect(x0 + dx, 3, x0 + dx + 1, 5, DARK)
    c.finish()
    # Кость поперёк копны поверх обводки: белая на тёмном, концы шире.
    c.line(x0 + 1, 13, x0 + 15, 9, WHITE, 2)
    for dx, dy in ((-1, 12), (0, 15), (15, 7), (16, 10)):
        c.rect(x0 + dx, dy, x0 + dx + 1, dy + 1, WHITE)
    return c


def bonecart(lean, phase, accent):
    """Тележка из костей со спины, 160×104: катки из позвонков на оси-бедренной кости, кузов из
    шкуры на рёбрах под хребтом, поперёк рёбер полоса шкуры цвета `accent` со следами когтей,
    по углам кормы пара низких рогов; правит раптор: полосатая спина, хвост через борт (качается
    по `phase`), хохол из перьев цвета `accent`. Без киля и мачт."""
    c = Canvas(160, 104)
    sh = lean * 6
    sway = 3 if phase < 0.25 else -2
    _bone_wheel(c, 20 + sh * 0.3, 78, 24, phase)
    _bone_wheel(c, 140 + sh * 0.3, 78, 24, phase)
    # Ось: бедренная кость с суставами у катков.
    c.rect(24, 83, 136, 87, WHITE)
    c.rect(24, 87, 136, 87, GREY)
    for x in (33, 127):
        c.ellipse(x, 83, 3.5, 3, WHITE)
        c.ellipse(x, 88, 3.5, 3, WHITE)
    # Кузов: шкура, натянутая на рёбра, швы жилами.
    c.poly([(32 + sh, 48), (128 + sh, 48), (122 + sh * 0.6, 86), (38 + sh * 0.6, 86)], TAN)
    c.poly([(36 + sh * 0.9, 76), (124 + sh * 0.9, 76), (122 + sh * 0.6, 86), (38 + sh * 0.6, 86)], DARK)
    for i in range(8):
        x = 38 + i * 12
        bow = (i - 3.5) * 1.2
        _curve(c, (x + sh, 49), (x + sh * 0.9 + bow * 2.2, 68), (x + sh * 0.6 - bow * 0.4, 88), 4.5, 2.5, WHITE, 30)
        _curve(c, (x + 1.5 + sh, 52), (x + 1.5 + sh * 0.9 + bow * 2.2, 68), (x + 1.5 + sh * 0.6 - bow * 0.4, 86),
               1.0, 1.0, GREY, 30)
    # Полоса шкуры цвета экипажа поперёк рёбер, три следа когтей.
    c.rect(44 + sh * 0.85, 59, 116 + sh * 0.85, 69, DARK)
    c.rect(45 + sh * 0.85, 60, 115 + sh * 0.85, 68, accent)
    for x in (52, 57, 62):
        c.line(x + sh * 0.85, 61, x - 3 + sh * 0.85, 67, WHITE if accent != GOLD else DARK, 1)
    for x in range(46, 116, 6):
        c.rect(x + sh * 0.85, 69, x + sh * 0.85 + 2, 71, accent)
    # Хребет по верхней кромке: позвонки буграми.
    c.rect(28 + sh, 45, 132 + sh, 49, WHITE)
    c.rect(28 + sh, 49, 132 + sh, 49, GREY)
    for x in range(32, 132, 9):
        if 62 < x < 98:
            continue
        c.ellipse(x + sh, 44, 3, 3.2, WHITE)
        c.set(x + sh + 1, 46, GREY)
    # Пара низких рогов по углам кормы: вместо спойлера, ниже головы раптора.
    for side in (-1, 1):
        bx = 80 + side * 50 + sh
        _curve(c, (bx, 47), (bx + side * 13, 46), (bx + side * 12 + sh * 0.2, 30), 7, 1.5, WHITE, 40)
        _curve(c, (bx + side * 3, 47), (bx + side * 11, 44), (bx + side * 12 + sh * 0.2, 36), 1.5, 1, GREY, 30)
        c.rect(bx + side * 2 - 2, 43, bx + side * 2 + 2, 44, accent)
    # Раптор со спины: узкая спина с полосами, длинная шея, вытянутая голова с хохлом.
    cx = 80 + sh * 1.2
    # Хвост через борт: толстый у крестца, кончик качается.
    _curve(c, (cx, 42), (cx + 6, 60), (cx + 30 + sway, 56 - sway), 11, 2.5, VIOLET, 50)
    _curve(c, (cx + 2, 46), (cx + 8, 60), (cx + 26 + sway, 57 - sway), 2, 1, PLUM, 40)
    for t in (0.25, 0.45, 0.65, 0.8):
        x = (1 - t) ** 2 * cx + 2 * t * (1 - t) * (cx + 6) + t * t * (cx + 30 + sway)
        y = (1 - t) ** 2 * 42 + 2 * t * (1 - t) * 60 + t * t * (56 - sway)
        c.rect(x - 1, y - 4 + t * 3, x, y - 1, PLUM)
    c.ellipse(cx, 37, 13, 11, VIOLET)
    c.ellipse(cx + 4, 39, 9, 8, PLUM)
    c.ellipse(cx - 1, 36, 10, 9, VIOLET)
    for y, half in ((30, 6), (34, 9), (38, 9), (42, 7)):
        c.rect(cx - half, y, cx + half - 3, y, PLUM)
    c.rect(cx - 4, 16, cx + 4, 30, VIOLET)
    c.rect(cx + 2, 18, cx + 4, 30, PLUM)
    # Лапы: локти в стороны, белые когти на хребте.
    for side in (-1, 1):
        c.line(cx + side * 10, 32, cx + side * 19, 38, VIOLET, 5)
        c.line(cx + side * 19, 38, cx + side * 17, 44, PLUM, 4)
        for k in (-2, 0, 2):
            c.rect(cx + side * 17 + k, 45, cx + side * 17 + k, 47, WHITE)
    # Голова вполоборота: раптор косится вбок, длинная морда с зубами, жёлтый глаз.
    c.ellipse(cx, 12, 7, 6.5, VIOLET)
    c.ellipse(cx + 9, 13, 9, 4.5, VIOLET)
    c.rect(cx + 3, 15, cx + 17, 16, GOLD)
    c.rect(cx + 4, 17, cx + 15, 17, PLUM)
    for dx in (6, 9, 12, 15):
        c.set(cx + dx, 16, WHITE)
    c.rect(cx + 15, 10, cx + 16, 10, PLUM)
    c.rect(cx + 1, 8, cx + 5, 8, PLUM)
    c.rect(cx + 2, 9, cx + 4, 11, GOLD)
    c.rect(cx + 3, 9, cx + 3, 11, K)
    c.rect(cx - 5, 9, cx - 3, 9, PLUM)
    c.rect(cx - 6, 12, cx - 3, 12, PLUM)
    # Хохол из перьев цвета экипажа на затылке: торчит назад и вверх.
    for (ex, ey) in ((-12, 1), (-14, 7), (-12, 14), (-5, 0)):
        c.poly([(cx - 5, 8), (cx - 3, 12), (cx + ex, ey + 1), (cx + ex, ey)], accent)
    c.finish()
    return c


def carts_strip(accent, raptor):
    """Три крена (влево, прямо, вправо) по два кадра: лента 6 кадров по 160, порядок как у пиратов."""
    frames = []
    for lean in (-1.0, 0.0, 1.0):
        for ph in (0.0, 0.5):
            frames.append(bonecart(lean, ph, accent) if raptor else stonecart(lean, ph, accent))
    return strip(frames)


def _frond(c, x0, y0, ang, length, droop, flip=False):
    """Вайя папоротника: стержень дугой вниз, по обе стороны листочки, к концу короче."""
    n = int(length)
    prev = (x0, y0)
    for i in range(n + 1):
        t = i / n
        x = x0 + math.cos(ang) * length * t
        y = y0 - math.sin(ang) * length * t + droop * t * t
        # Касательная к стержню, листочки поперёк.
        tx = math.cos(ang) * length
        ty = -math.sin(ang) * length + 2 * droop * t
        d = math.hypot(tx, ty)
        nx, ny = -ty / d, tx / d
        if i % 3 == 0 and i > 3:
            ll = 3 + 9 * math.sin(min(1.0, t * 1.15) * math.pi) ** 0.7
            col = VIOLET if (i // 3) % 2 == 0 or flip else PLUM
            c.line(x, y, x + nx * ll + tx / d * 3, y + ny * ll + ty / d * 3, PLUM if ny > 0 else col, 2)
            c.line(x, y, x - nx * ll + tx / d * 3, y - ny * ll + ty / d * 3, col if ny > 0 else PLUM, 2)
        c.line(prev[0], prev[1], x, y, PLUM, 2)
        prev = (x, y)


def treefern():
    """Древовидный папоротник у обочины, 120×240 (место пальмы): чешуйчатый ствол с лёгким
    изгибом, крона из перистых вай дугами, в середине молодые побеги улитками, у корня кустики."""
    c = Canvas(120, 240)
    bend = 12
    pts = []
    for i in range(170):
        k = i / 169
        pts.append((56 + bend * math.sin(k * math.pi * 0.9), 239 - i))
    for i, (x, y) in enumerate(pts):
        w = 9 - i / 45
        c.rect(x - w, y, x + w, y, BRASS)
        # Чешуя от старых черешков: ромбами в шахмат.
        row = i // 6
        for k in range(-2, 3):
            sx = x + k * 6 + (3 if row % 2 else 0)
            if abs(sx - x) < w - 1 and i % 6 in (0, 1):
                c.rect(sx, y, sx + 2, y, DARK)
        c.set(x + w, y, DARK)
        c.set(x + w - 1, y, DARK)
        c.set(x - w + 1, y, GOLD)
    tx, ty = pts[-1]
    # Крона: задние вайи темнее и ниже, передние поверх.
    for deg, ln, droop in ((-8, 46, 46), (188, 50, 46), (22, 54, 44), (158, 56, 44), (48, 54, 30), (132, 56, 30),
                           (74, 52, 16), (106, 54, 16)):
        _frond(c, tx, ty + 2, math.radians(deg), ln, droop)
    c.ellipse(tx, ty + 3, 9, 7, PLUM)
    # Молодые побеги улитками.
    for dx in (-5, 5):
        c.line(tx + dx * 0.4, ty + 2, tx + dx, ty - 12, VIOLET, 2)
        c.ellipse(tx + dx + (2 if dx > 0 else -2), ty - 14, 3.5, 3.5, VIOLET)
        c.set(tx + dx + (2 if dx > 0 else -2), ty - 14, PLUM)
    # Кустики папоротника у корня.
    for bx in (22, 96):
        for deg in (35, 75, 110, 150):
            _frond(c, bx, 238, math.radians(deg), 26, 12, True)
    c.finish()
    return c


def _horsetail(c, x, base, h, w, cone):
    """Стебель хвоща: членики с тёмными зубчатыми узлами, мутовки тонких веток вверх и в стороны."""
    joints = max(3, h // 20)
    top = base - h
    for j in range(joints):
        yj = base - int(h * (j + 0.6) / joints)
        k = j / max(1, joints - 1)
        ll = (10 + 22 * math.sin(min(1.0, k * 1.1 + 0.15) * math.pi)) * (h / 220.0) ** 0.5
        for side in (-1, 1):
            for rise, mul in ((0.25, 1.0), (0.75, 0.8)):
                ex = x + side * ll * mul
                ey = yj - ll * mul * rise
                c.line(x, yj, ex, ey, VIOLET, 2)
                c.line(x + side * ll * mul * 0.6, yj - ll * mul * rise * 0.6 + 1, ex, ey + 1, PLUM, 1)
                c.line(ex, ey, ex + side * 3, ey - 4, VIOLET, 1)
    for y in range(top, base + 1):
        ww = max(1.5, w * (0.45 + 0.55 * (y - top) / h))
        c.rect(x - ww, y, x + ww, y, VIOLET)
        c.set(x + ww, y, PLUM)
        c.set(x + ww - 1, y, PLUM)
    for j in range(joints):
        yj = base - int(h * (j + 0.6) / joints)
        ww = max(1.5, w * (0.45 + 0.55 * (yj - top) / h)) + 1
        c.rect(x - ww, yj, x + ww, yj + 1, DARK)
        for dx in range(int(-ww), int(ww) + 1, 2):
            c.set(x + dx, yj - 1, DARK)
        c.rect(x - ww, yj + 2, x + ww, yj + 2, GOLD)
    if cone:
        # Колосок со спорами на макушке.
        c.ellipse(x, top - 7, 4.5, 9, BRASS)
        for dy in range(-13, 0, 3):
            c.set(x - 2, top + dy, DARK)
            c.set(x + 1, top + dy + 1, DARK)
        c.set(x - 1, top - 13, GOLD)


def horsetails():
    """Хвощи у обочины, 120×240 (место второй пальмы): высокий стебель с колоском и два пониже,
    членики, мутовки веток ёршиком, у корня камни."""
    c = Canvas(120, 240)
    _horsetail(c, 26, 239, 128, 4, False)
    _horsetail(c, 96, 239, 96, 4, True)
    _horsetail(c, 60, 239, 212, 6, True)
    c.poly([(2, 239), (10, 226), (24, 228), (36, 239)], METAL)
    c.poly([(72, 239), (84, 228), (104, 231), (114, 239)], METAL)
    c.rect(11, 228, 22, 229, GREY)
    c.rect(85, 230, 100, 231, GREY)
    c.finish()
    return c


def lava_rock():
    """Глыба лавы у дороги, 96×64: тёмные наплывы подушками, раскалённые щели между ними, у
    подножия лужа жара."""
    c = Canvas(96, 64)
    c.ellipse(48, 60, 46, 5, RED)
    c.ellipse(44, 60, 30, 2.5, GOLD)
    # Наплывы: от задних к передним.
    lobes = ((30, 30, 24, 20), (64, 28, 26, 22), (48, 16, 20, 14), (20, 46, 18, 14), (76, 46, 18, 14), (48, 44, 22, 16))
    for cx, cy, rx, ry in lobes:
        c.ellipse(cx, cy + 1, rx, ry, RED)
        c.ellipse(cx, cy, rx - 1.5, ry - 1.5, DARK)
        c.ellipse(cx - 1, cy - 1, rx - 3, ry - 3, METAL)
        c.ellipse(cx - rx * 0.3, cy - ry * 0.4, rx * 0.4, ry * 0.25, GREY)
    # Яркое ядро щелей и потёк.
    c.line(40, 32, 44, 28, GOLD, 1)
    c.line(57, 32, 52, 29, GOLD, 1)
    c.line(30, 50, 37, 58, GOLD, 2)
    c.line(66, 50, 60, 59, GOLD, 2)
    for x, y in ((24, 24), (70, 20), (52, 48), (82, 44), (14, 44), (46, 12)):
        c.rect(x, y, x + 1, y, DARK)
    for y in range(61, 64):
        for x in range(96):
            c.px[y][x] = None
    return c.finish()


def basket():
    """Плетёная корзина, 48×64: прутья в шахмат, обод жгутом, две ручки-петли, сверху яйца в
    крапинку и лист."""
    c = Canvas(48, 64)
    # Яйца горкой над ободом.
    c.ellipse(15, 13, 7, 9, WHITE)
    c.ellipse(33, 14, 7, 9, WHITE)
    c.ellipse(24, 10, 8, 10, METAL)
    c.ellipse(24, 9, 7, 9, WHITE)
    for x, y in ((21, 5), (26, 9), (23, 13), (12, 10), (16, 15), (34, 10), (30, 16), (36, 15)):
        c.rect(x, y, x + 1, y, BRASS)
    c.rect(27, 3, 28, 7, GREY)
    c.poly([(34, 20), (46, 10), (44, 22)], VIOLET)
    c.line(36, 20, 44, 13, PLUM, 1)
    # Корзина: бока бочонком, плетение.
    for y in range(22, 62):
        k = (y - 22) / 39.0
        half = 17 + 5 * math.sin(k * math.pi) - 3 * k
        c.rect(24 - half, y, 24 + half, y, GOLD)
        row = (y - 22) // 4
        for x in range(int(24 - half), int(24 + half) + 1):
            col_ = (x + (3 if row % 2 else 0)) // 6
            if (y - 22) % 4 == 3 or (x + (3 if row % 2 else 0)) % 6 == 5:
                c.set(x, y, BRASS)
            elif col_ % 2 == 0 and (y - 22) % 4 == 0:
                c.set(x, y, SKY)
        c.set(24 + half, y, DARK)
        c.set(24 + half - 1, y, BRASS)
    # Обод жгутом и донце.
    c.rect(4, 19, 44, 24, BRASS)
    for x in range(5, 44, 5):
        c.line(x, 24, x + 3, 19, DARK, 1)
    c.rect(4, 19, 44, 19, GOLD)
    c.rect(9, 60, 39, 63, DARK)
    # Ручки-петли по бокам.
    for side in (-1, 1):
        x = 24 + side * 21
        c.rect(x - 1, 26, x + 1, 38, BRASS)
        c.rect(x - 1 - side, 26, x + 1 - side, 28, BRASS)
        c.rect(x - 1 - side, 36, x + 1 - side, 38, BRASS)
    return c.finish()


def sign(right):
    """Указатель поворота, 96×112: шкура, растянутая на раме из костей, тёмные шевроны углём в
    сторону поворота, ремни по углам, стойка бедренной костью в камнях."""
    c = Canvas(96, 112)
    # Стойка: кость с суставами, камни у подножия.
    c.rect(44, 52, 51, 106, WHITE)
    c.rect(49, 52, 51, 106, GREY)
    c.ellipse(44, 104, 5, 4, WHITE)
    c.ellipse(52, 104, 5, 4, WHITE)
    c.ellipse(38, 108, 9, 4, METAL)
    c.ellipse(58, 109, 9, 3.5, METAL)
    c.rect(33, 106, 40, 106, GREY)
    # Рама: четыре кости с шишками на концах.
    for y in (6, 54):
        c.rect(4, y - 2, 91, y + 2, WHITE)
        c.rect(4, y + 2, 91, y + 2, GREY)
    for x in (6, 89):
        c.rect(x - 2, 4, x + 2, 56, WHITE)
        c.rect(x + 2, 6, x + 2, 54, GREY)
    for x in (4, 91):
        for y in (4, 56):
            c.ellipse(x + (1 if x < 48 else -1), y + (1 if y < 30 else -1), 4, 4, WHITE)
    # Шкура: края втянуты между ремнями.
    c.poly([(10, 9), (48, 12), (85, 9), (82, 30), (85, 51), (48, 48), (10, 51), (13, 30)], SKY)
    c.poly([(13, 46), (48, 44), (82, 46), (85, 51), (48, 48), (10, 51)], GOLD)
    for x, y in ((10, 9), (85, 9), (10, 51), (85, 51), (48, 11), (48, 49)):
        c.rect(x - 1, y - 1, x + 1, y + 1, BRASS)
    for x, y in ((18, 14), (76, 40), (70, 15), (22, 42)):
        c.rect(x, y, x + 2, y, GOLD)
    d = 1 if right else -1
    for k in range(3):
        cx = 48 + d * (k * 20 - 20)
        c.poly([(cx - d * 8, 15), (cx + d * 9, 30), (cx - d * 8, 45), (cx - d * 2, 30)], K)
        c.line(cx - d * 8, 15, cx + d * 9, 30, RED, 1)
    return c.finish()


def hut():
    """Шалаш из бивней и шкур у дороги, 192×160 (место хижины): купол из сшитых шкур на кольце
    камней, два больших бивня крест-накрест над макушкой, вход с черепом над ним и пологом,
    дымок из макушки, сбоку сушится шкура."""
    c = Canvas(192, 160)
    cx, base = 96, 150
    # Дымок из макушки: ниже рисуется первым, бивни лягут поверх.
    for ox, oy, r in ((98, 40, 7), (104, 28, 8), (98, 16, 7), (106, 7, 5)):
        c.ellipse(ox, oy, r, r * 0.8, GREY)
        c.ellipse(ox - 1, oy - 1, r * 0.6, r * 0.45, WHITE)
    # Купол из шкур.
    rx, ry = 84, 98
    for y in range(base - ry, base + 1):
        half = int(rx * math.sqrt(max(0.0, 1.0 - ((base - y) / ry) ** 2)))
        c.rect(cx - half, y, cx + half, y, TAN)
    # Лоскуты: светлые шкуры и одна пятнистая, швы жилами.
    c.poly([(40, 150), (34, 108), (56, 82), (72, 96), (66, 150)], SKIN)
    c.poly([(124, 150), (120, 92), (140, 78), (162, 110), (158, 150)], SKIN)
    c.poly([(74, 62), (96, 54), (120, 62), (116, 84), (78, 86)], RED)
    for x, y in ((84, 64), (96, 70), (106, 62), (90, 78), (110, 76), (100, 80)):
        c.ellipse(x, y, 2.5, 2, DARK)
    for pts in (((40, 150), (34, 108), (56, 82), (72, 96), (66, 150)),
                ((124, 150), (120, 92), (140, 78), (162, 110), (158, 150)),
                ((74, 62), (78, 86), (116, 84), (120, 62))):
        for a, b in zip(pts, pts[1:]):
            n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 5)
            for i in range(n + 1):
                t = i / max(1, n)
                x = a[0] + (b[0] - a[0]) * t
                y = a[1] + (b[1] - a[1]) * t
                c.rect(x, y, x + 1, y + 1, DARK)
    # Рёбра каркаса проступают дугами.
    for m in (-0.55, 0.55):
        prev = None
        for y in range(base - ry + 6, base - 4, 3):
            half = rx * math.sqrt(max(0.0, 1.0 - ((base - y) / ry) ** 2))
            p = (cx + half * m, y)
            if prev is not None and y > 90:
                c.line(prev[0], prev[1], p[0], p[1], DARK, 1)
            prev = p
    # Два больших бивня крест-накрест: от земли по бокам через макушку.
    _curve(c, (12, 150), (16, 44), (118, 30), 11, 2.5, WHITE, 160)
    _curve(c, (180, 150), (176, 44), (74, 30), 11, 2.5, WHITE, 160)
    _curve(c, (17, 146), (22, 52), (108, 36), 2, 1, GREY, 120)
    _curve(c, (175, 146), (170, 52), (84, 36), 2, 1, GREY, 120)
    for y in (132, 112):
        c.rect(8, y, 20, y + 2, BRASS)
        c.rect(172, y, 184, y + 2, BRASS)
    # Вход: тёмный проём аркой, рама из малых бивней, полог откинут.
    for y in range(96, base + 1):
        half = int(24 * math.sqrt(max(0.0, 1.0 - ((base - y) / 54.0) ** 2)))
        c.rect(cx - half, y, cx + half, y, K)
    _curve(c, (70, 150), (70, 98), (94, 94), 7, 2.5, WHITE, 70)
    _curve(c, (122, 150), (122, 98), (98, 94), 7, 2.5, WHITE, 70)
    c.poly([(104, 104), (118, 112), (117, 150), (108, 150), (112, 126)], RED)
    for x, y in ((112, 116), (114, 130), (111, 142)):
        c.rect(x, y, x + 1, y + 1, DARK)
    # Череп с рогами над входом.
    c.ellipse(96, 88, 10, 8, WHITE)
    c.rect(91, 92, 101, 99, WHITE)
    c.rect(90, 86, 93, 89, DARK)
    c.rect(99, 86, 102, 89, DARK)
    c.rect(95, 92, 97, 94, DARK)
    for x in (92, 95, 98):
        c.rect(x, 98, x, 99, GREY)
    _curve(c, (87, 84), (78, 82), (76, 72), 4, 1.5, WHITE, 24)
    _curve(c, (105, 84), (114, 82), (116, 72), 4, 1.5, WHITE, 24)
    # Кольцо камней у основания.
    for x, r in ((14, 10), (34, 8), (52, 9), (140, 9), (158, 8), (178, 10)):
        c.ellipse(x, 153, r, 6, METAL)
        c.rect(x - r * 0.5, 149, x, 149, GREY)
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
        "palm": treefern(),
        "palm_b": horsetails(),
        "road_rock": lava_rock(),
        "road_barrel": basket(),
        "sign_left": sign(False),
        "sign_right": sign(True),
        "road_hut": hut(),
    }
    for i, accent in enumerate((SEA, GOLD, RED, AQUA)):
        out["cart_%d" % i] = carts_strip(accent, True)
    return out


def horizon():
    """Горизонт в своей палитре `DINOSAURS_SKY`."""
    return {"road_sky": sky(), "road_islands": islands(), "road_sea": sea()}


def road_palette():
    return {"road_colors": road_colors()}


def preview(path):
    items = dinosaurs16.shaded(sprites())
    for key, canvas in horizon().items():
        items[key] = (canvas, DINOSAURS_SKY)
    for key, canvas in road_palette().items():
        items[key] = (canvas, ROAD_COLORS)
    dinosaurs16.save_sheet(path, items, scale=2, max_w=512)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
