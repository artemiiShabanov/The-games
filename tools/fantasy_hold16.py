#!/usr/bin/env python3
"""Набор «Фэнтези» для шутера × 16/32-bit «до выхода» (#137), зеркало `space_hold16.py` и
`pixel_hold16.py`: те же ключи, размеры холстов, число и порядок кадров и точки опоры (ноги
врагов на 61-62 строке по центру кадра, палочка вверх по оси 64, текстуры 64×64 со швом по краю).

Тема: гоблинские норы в корнях великого дерева, дорога к порталу. Стены: кора с гирляндой лиан
и мхом, пещера с кристаллами, живой ствол с рунными обручами, каменная арка портала (выход),
библиотека чародея, дупло-окно с летающим островом, кладовая из плетёных коробов. Полы: земля
в корнях, рунные плиты, ковёр со звёздами. Враги: гоблин-шаман в пончо и перьях, с посохом и
черепом на нём (`skel_*`), и гоблин с шипастой дубинкой (`cut_*`). Волшебная палочка в руке
мага, огненный шар героя, сгусток порчи шамана, ключ и зелье из основы, лицо мага в шляпе.

    python3 tools/fantasy_hold16.py --preview out.png [--scale=N] [--keys=a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fantasy16  # noqa: E402
from fantasy16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                       DARK, RED, VIOLET, PLUM)

T = 64

# Руны 3×5: общий алфавит резьбы на камне, обручах и плитах.
RUNES = ("X..XX.X.XXX.X..", ".X.XXX.X..X..X.", "X.XX.X.X..X..X.", "XXX..X.X.X..XXX", ".X.X.XX.XX.X.X.",
         "X.X.X.X.X.X.X.X", "XX.X.XXX.X..X..", "..X.XXX.XXX.X..")


def _rune(c, x, y, i, col):
    """Руна номер `i` левым верхним углом в (x, y), координаты заворачиваются по плитке."""
    bits = RUNES[i % len(RUNES)]
    for k, ch in enumerate(bits):
        if ch == "X":
            c.set((x + k % 3) % T, (y + k // 3) % T, col)


def _cells(seed, grid, jitter=0.7, wrap_y=True):
    """Ячейки Вороного на плитке: точки по сетке `grid`×`grid` с разбросом. На пиксель отдаёт
    (номер ячейки, зазор до границы, смещение от точки по x и y); по x шов замкнут всегда."""
    rng = random.Random(seed)
    step = T / grid
    pts = []
    for gy in range(grid):
        for gx in range(grid):
            pts.append(((gx + 0.5 + rng.uniform(-jitter, jitter) / 2) * step,
                        (gy + 0.5 + rng.uniform(-jitter, jitter) / 2) * step))
    out = []
    for y in range(T):
        row = []
        for x in range(T):
            best = []
            for i, (px, py) in enumerate(pts):
                dx = (x - px + T / 2) % T - T / 2
                dy = y - py
                if wrap_y:
                    dy = (dy + T / 2) % T - T / 2
                best.append((dx * dx + dy * dy, i, dx, dy))
            best.sort()
            row.append((best[0][1], math.sqrt(best[1][0]) - math.sqrt(best[0][0]), best[0][2], best[0][3]))
        out.append(row)
    return out


def _bark(c, seed, base=METAL, light=BRASS, dark=DARK):
    """Кора: вертикальные пластины с извилистыми трещинами (свет справа от трещины), короткие
    поперечные надломы и штрихи волокон. По горизонтали замкнута."""
    rng = random.Random(seed)
    cracks = []
    x = 0
    while x < T - 5:
        cracks.append((x, rng.uniform(1.0, 2.4), rng.random() * math.tau, rng.choice((1, 2, 3))))
        x += rng.randint(7, 12)
    for y in range(T):
        for x in range(T):
            col = base
            for x0, amp, ph, k in cracks:
                xc = x0 + amp * math.sin(y * math.tau / T * k + ph)
                d = (x - xc) % T
                if d < 1.0:
                    col = dark
                elif d < 2.0:
                    col = light
            c.set(x, y, col)
    for _ in range(26):
        x, y = rng.randrange(T), rng.randrange(T - 6)
        n = rng.randint(3, 7)
        for k in range(n):
            if c.get(x, y + k) == base:
                c.set(x, y + k, dark)
    for _ in range(12):
        x, y = rng.randrange(T), rng.randrange(T)
        for k in range(rng.randint(2, 4)):
            if c.get((x + k) % T, y) == base:
                c.set((x + k) % T, y, dark)


def _knot(c, cx, cy, rx, ry):
    """Сучок: тёмное кольцо, светлая сердцевина с точкой."""
    c.ellipse(cx, cy, rx, ry, DARK)
    c.ellipse(cx, cy, rx - 1, ry - 1, METAL)
    c.ellipse(cx, cy, rx - 2, ry - 2, BRASS)
    c.set(cx, cy, DARK)


def _mushroom(c, x, y, big=False):
    """Светящийся грибок: ножка от строки `y` вверх, бирюзовая шляпка с бликом."""
    h = 4 if big else 2
    c.rect(x, y - h, x + (1 if big else 0), y, WHITE)
    r = 3 if big else 2
    c.rect(x - r + 1, y - h - 1, x + r, y - h - 1, AQUA)
    c.rect(x - r + 2, y - h - 2, x + r - 1, y - h - 2, AQUA)
    c.rect(x - r, y - h, x + r + 1, y - h, SEA)
    c.set(x, y - h - 2, SKY)


# --- Текстуры ----------------------------------------------------------------------------------

def tex_panels():
    """Основная стена: кора великого дерева, два сучка, под потолком гирляндой висит лиана с
    сиреневыми листьями, внизу мох и светящиеся грибки."""
    c = Canvas(T, T)
    _bark(c, 401)
    _knot(c, 15, 34, 5, 4)
    _knot(c, 47, 27, 4, 5)
    # Лиана: провисает между колышками на 0 и 32 столбцах.
    for x in range(T):
        y = 5 + 7 * abs(math.sin(x * math.pi / 32.0))
        c.set(x, y + 2, DARK)
        c.set(x, y, TAN)
        c.set(x, y + 1, TAN)
        if x % 6 == 3:
            yy = int(round(y)) + 2
            c.rect(x - 1, yy, x + 1, yy + 1, VIOLET)
            c.set(x, yy + 2, VIOLET)
            c.set(x + 1, yy + 2, PLUM)
            c.set(x - 1, yy, WHITE if x % 12 == 3 else VIOLET)
    for x in (0, 32):
        c.rect(x - 1, 3, x + 1, 6, DARK)
        c.set(x, 4, BRASS)
        c.set(T - 1, 4, DARK)
    for x in (16, 48):
        c.rect(x - 1, 14, x, 15, GOLD)
        c.set(x, 16, BRASS)
    # Мох по низу: неровная кромка, тень над ней, цветы.
    for x in range(T):
        top = 56 + int(round(1.6 * math.sin(x * math.tau / 16.0) + 1.2 * math.sin(x * math.tau / 64.0 * 5 + 1.0)))
        c.set(x, top - 1, DARK)
        for y in range(top, T):
            col = TAN
            if (x * 7 + y * 5) % 11 == 0:
                col = DARK
            elif y == top and x % 3 == 0:
                col = GOLD
            c.set(x, y, col)
        if y and x % 13 == 6:
            c.set(x, top + 2, VIOLET)
    c.rect(0, T - 1, T - 1, T - 1, DARK)
    _mushroom(c, 9, 57, True)
    _mushroom(c, 14, 58)
    _mushroom(c, 41, 58)
    _mushroom(c, 54, 57, True)
    return c


def _shard(c, bx, by, ang, length, half):
    """Кристалл-осколок: от основания (bx, by) под углом `ang` градусов, свет слева, тень справа."""
    a = math.radians(ang)
    ux, uy = math.cos(a), -math.sin(a)
    nx, ny = -uy, ux
    tip = (bx + ux * length, by + uy * length)
    sh = (bx + ux * length * 0.72, by + uy * length * 0.72)
    left = (bx - nx * half, by - ny * half)
    right = (bx + nx * half, by + ny * half)
    sl = (sh[0] - nx * half, sh[1] - ny * half)
    sr = (sh[0] + nx * half, sh[1] + ny * half)
    c.poly([left, sl, tip, sr, right], K)
    c.poly([(left[0] + ux, left[1] + uy), sl, (tip[0] - ux, tip[1] - uy), sr, (right[0] + ux, right[1] + uy)], AQUA)
    c.poly([(bx, by), sh, (tip[0] - ux, tip[1] - uy), sr, right], SEA)
    c.line(left[0] + nx + ux, left[1] + ny + uy, sl[0] + nx, sl[1] + ny, SKY, 1)
    c.set(sh[0] - nx * 0.5, sh[1] - ny * 0.5, WHITE)


def tex_growth():
    """Пещера с кристаллами: тёмный сиреневый камень глыбами, из трещин растут бирюзовые друзы,
    вокруг них отсвет."""
    c = Canvas(T, T)
    cells = _cells(402, 4, 0.9, wrap_y=False)
    for y in range(T):
        for x in range(T):
            i, gap, dx, dy = cells[y][x]
            col = (PLUM, NAVY, PLUM, PLUM, NAVY)[i % 5]
            if gap < 1.3:
                col = K
            elif gap < 3.0 and dx + dy < -2:
                col = VIOLET
            elif (x * 3 + y * 7 + i) % 17 == 0:
                col = NAVY if col == PLUM else PLUM
            c.set(x, y, col)
    # Отсвет друз на камне.
    for gx, gy, r in ((16, 50, 11), (47, 36, 10), (28, 15, 9), (55, 9, 6)):
        for y in range(T):
            for x in range(T):
                d = math.hypot(x - gx, y - gy)
                if d < r and c.get(x, y) in (PLUM, NAVY) and (x + y) % 2 == 0 and d > r * 0.3:
                    c.set(x, y, SEA if d < r * 0.75 else c.get(x, y))
    _shard(c, 11, 54, 118, 13, 2.5)
    _shard(c, 20, 55, 62, 10, 2.2)
    _shard(c, 16, 56, 92, 19, 3.4)
    _shard(c, 43, 41, 125, 9, 2.0)
    _shard(c, 51, 41, 55, 12, 2.4)
    _shard(c, 47, 42, 86, 16, 3.0)
    _shard(c, 25, 19, 110, 8, 2.0)
    _shard(c, 30, 20, 70, 12, 2.6)
    _shard(c, 55, 13, 95, 9, 2.2)
    for x, y in ((6, 30), (36, 52), (58, 26), (38, 6), (8, 8), (26, 38), (60, 52)):
        c.set(x, y, AQUA)
        c.set(x + 1, y, SEA)
    return c


def tex_pillar():
    """Колонна: живой ствол с глубокими бороздами, свет слева, два золотых обруча с рунами,
    поперёк вьётся лиана с листьями и ягодами."""
    c = Canvas(T, T)
    for y in range(T):
        sway = int(round(1.2 * math.sin(y * math.tau / 32.0)))
        for x in range(T):
            px = (x + sway) % 8
            col = METAL
            if px == 0:
                col = DARK
            elif px == 1:
                col = BRASS
            elif px == 7:
                col = DARK if (y // 3) % 3 else METAL
            if x < 5 or x > 58:
                col = K if col == DARK else DARK
            elif 14 <= x <= 28 and col == METAL and (x + 2 * y) % 4 == 0:
                col = BRASS
            elif x > 44 and col == BRASS:
                col = METAL
            c.set(x, y, col)
    for n, y in enumerate((8, 47)):
        c.rect(0, y - 1, T - 1, y - 1, K)
        c.rect(0, y, T - 1, y + 7, GOLD)
        c.rect(0, y, T - 1, y, WHITE)
        c.rect(0, y + 7, T - 1, y + 7, BRASS)
        c.rect(0, y + 8, T - 1, y + 9, K)
        for i, x in enumerate(range(3, T, 8)):
            _rune(c, x, y + 2, i + n * 3, DARK)
            c.set(x + 5, y + 4, BRASS)
        c.rect(0, y + 1, 4, y + 6, BRASS)
        c.rect(59, y + 1, T - 1, y + 6, BRASS)
    for x in range(T):
        y = 31 + 8 * math.sin(x * math.tau / T)
        c.set(x, y + 2, K)
        c.rect(x, int(round(y)), x, int(round(y)) + 1, TAN)
        if x % 8 == 2:
            up = (x // 8) % 2 == 0
            yy = int(round(y)) + (-4 if up else 3)
            c.rect(x - 1, yy, x + 2, yy + 2, VIOLET)
            c.set(x - 1, yy + (0 if up else 2), None)
            c.set(x + 2, yy + (2 if up else 0), PLUM)
            c.set(x, yy + 1, WHITE if x % 16 == 2 else VIOLET)
        if x % 16 == 11:
            c.rect(x, int(round(y)) + 3, x + 1, int(round(y)) + 4, AQUA)
            c.set(x, int(round(y)) + 3, SKY)
    # Дырки от сброшенных пикселей листьев закрываем корой.
    for y in range(T):
        for x in range(T):
            if c.get(x, y) is None:
                c.set(x, y, METAL)
    return c


def tex_exit():
    """Выход: каменная арка с золотыми рунами и замковым камнем, в ней бирюзовый водоворот
    портала с белым ядром; вокруг кора, у порога ступень."""
    c = Canvas(T, T)
    _bark(c, 404, DARK, METAL, K)
    ax, ay = 31.5, 30.0
    for y in range(T):
        for x in range(T):
            d = math.hypot(x - ax, y - ay)
            deg = math.degrees(math.atan2(ay - y, x - ax))
            portal = (12 <= x <= 51 and 30 <= y <= 58) or (d <= 20 and y < 30)
            ring = y < 30 and 20 < d <= 27.5
            post = y >= 30 and (4 <= x <= 11 or 52 <= x <= 59) and y <= 58
            if portal:
                dx, dy = x - ax, y - 36.0
                r = math.hypot(dx, dy)
                v = (math.atan2(dy, dx) / math.tau * 3 + r / 9.0) % 1.0
                col = SEA if v < 0.3 else (AQUA if v < 0.58 else (SKY if v < 0.68 else NAVY))
                if r < 3:
                    col = WHITE
                elif r < 5.5:
                    col = SKY
                edge = (y < 30 and d > 18.6) or (y >= 30 and (x < 14 or x > 49))
                if edge and (x + y) % 2 == 0:
                    col = SKY
                c.set(x, y, col)
            elif ring:
                col = GREY
                if deg % 22.5 < 2.4:
                    col = DARK
                elif d > 26.4:
                    col = WHITE
                elif d < 21.2:
                    col = PLUM
                if 79 < deg < 101:
                    col = GOLD if 80.5 < deg < 99.5 else K
                    if d > 26.4:
                        col = WHITE
                    elif d < 21.2:
                        col = BRASS
                c.set(x, y, col)
            elif post:
                px = x - (4 if x < 32 else 52)
                col = GREY
                if (y - 30) % 10 == 9:
                    col = DARK
                elif px == 0 or (y - 30) % 10 == 0:
                    col = WHITE
                elif px == 7:
                    col = PLUM
                c.set(x, y, col)
            elif (y < 30 and 27.5 < d <= 28.6) or (y >= 30 and y <= 58 and x in (3, 60)):
                c.set(x, y, K)
    # Руны на клиньях арки и на столбах.
    for k in range(8):
        if k in (3, 4):
            continue
        a = math.radians(k * 22.5 + 12.5)
        rx, ry = ax + math.cos(a) * 23.8, ay - math.sin(a) * 23.8
        c.rect(rx - 0.5, ry - 0.5, rx + 0.5, ry + 0.5, GOLD)
        c.set(rx + 1, ry + 1, BRASS)
    for i in range(3):
        _rune(c, 6, 33 + i * 10, i, GOLD)
        _rune(c, 55, 33 + i * 10, i + 3, GOLD)
    # Замковый камень с бирюзовым самоцветом.
    c.rect(30, 4, 33, 8, K)
    c.rect(31, 4, 32, 7, AQUA)
    c.set(31, 5, SKY)
    # Порог: ступень, по ней ложится отсвет портала.
    c.rect(0, 59, T - 1, T - 1, GREY)
    c.rect(0, 59, T - 1, 59, WHITE)
    c.rect(0, T - 1, T - 1, T - 1, DARK)
    for x in range(8, T, 16):
        c.rect(x, 60, x, 62, DARK)
    for x in range(14, 50):
        for y in (60, 61):
            if (x + y) % 2 == 0:
                c.set(x, y, AQUA)
    # Искры вокруг арки.
    for x, y in ((5, 6), (58, 9), (2, 22), (61, 24)):
        c.set(x, y, SKY)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.set(x + dx, y + dy, AQUA)
    return c


def tex_cabin():
    """Библиотека чародея: три полки книг с золотым тиснением, между книгами колба, свеча и
    череп, внизу резная панель."""
    rng = random.Random(405)
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, DARK)
    shelves = ((3, 19), (23, 38), (42, 54))
    props = {0: (38, 49), 1: (10, 21), 2: (30, 42)}
    for n, (top, bottom) in enumerate(shelves):
        x = 2
        while x < 61:
            if props[n][0] <= x < props[n][1]:
                x = props[n][1]
                continue
            w = rng.randint(3, 5)
            w = min(w, 61 - x, (props[n][0] - x) if x < props[n][0] else 99)
            if w < 2:
                x += w + 1
                continue
            col = rng.choice((RED, SEA, VIOLET, TAN, PLUM, NAVY, SEA, RED, BRASS))
            y0 = top + rng.randint(0, 4)
            c.rect(x, y0, x + w - 1, bottom, col)
            c.rect(x, y0, x + w - 1, y0, WHITE if col in (NAVY, PLUM) else K)
            band = GOLD if col != BRASS else DARK
            c.rect(x, y0 + 3, x + w - 1, y0 + 3, band)
            c.rect(x, bottom - 2, x + w - 1, bottom - 2, band)
            if w >= 4:
                c.set(x + 1, (y0 + bottom) // 2, band)
                c.set(x + 2, (y0 + bottom) // 2 + 1, band)
            c.rect(x + w, y0 + 1, x + w, bottom, K)
            x += w + 1
    # Колба с зельем и свеча на верхней полке.
    c.ellipse(42, 15, 3.5, 3.5, GREY)
    c.ellipse(42, 16, 2.5, 2.5, AQUA)
    c.rect(41, 8, 43, 12, GREY)
    c.rect(41, 7, 43, 7, METAL)
    c.set(41, 14, WHITE)
    c.rect(46, 12, 47, 19, WHITE)
    c.set(47, 14, GREY)
    c.rect(46, 9, 47, 11, GOLD)
    c.set(46, 8, RED)
    c.set(47, 10, WHITE)
    # Череп на средней полке.
    c.ellipse(15, 32, 4.5, 4, WHITE)
    c.rect(13, 35, 17, 38, WHITE)
    c.rect(13, 31, 14, 33, K)
    c.rect(16, 31, 17, 33, K)
    c.set(15, 35, K)
    for x in (13, 15, 17):
        c.set(x, 38, GREY)
    # Свиток и кристалл на нижней.
    c.rect(31, 50, 40, 53, WHITE)
    c.rect(31, 50, 31, 53, GREY)
    c.rect(40, 50, 40, 53, GREY)
    c.rect(34, 51, 37, 52, RED)
    c.rect(30, 54, 41, 54, K)
    # Доски полок и стойки.
    for y in (0, 20, 39, 55):
        c.rect(0, y, T - 1, y, BRASS)
        c.rect(0, y + 1, T - 1, y + 1, METAL)
        c.rect(0, y + 2, T - 1, y + 2, K)
    for y in range(T):
        c.set(0, y, BRASS)
        c.set(1, y, METAL)
        c.set(T - 2, y, METAL)
        c.set(T - 1, y, DARK)
    # Резная панель: ромбы.
    c.rect(0, 58, T - 1, T - 1, METAL)
    c.rect(0, 58, T - 1, 58, BRASS)
    c.rect(0, T - 1, T - 1, T - 1, DARK)
    for x0 in range(0, T, 16):
        for y in range(59, 63):
            for x in range(16):
                d = abs(x - 7.5) + abs(y - 60.5) * 2
                if 4 < d <= 6:
                    c.set(x0 + x, y, DARK)
                elif d <= 2:
                    c.set(x0 + x, y, GOLD)
    return c


def tex_hull():
    """Дупло-окно: та же кора, в кольце из свитых корней сумеречное небо, месяц и летающий
    остров с водопадом."""
    c = tex_panels()
    wx, wy = 32, 29
    sky = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            d = math.hypot(x - wx, y - wy)
            if d <= 18.5:
                c.set(x, y, K)
            if d <= 17.5:
                deg = math.degrees(math.atan2(wy - y, x - wx)) % 360
                col = METAL
                if (deg + d * 6) % 30 < 5:
                    col = DARK
                elif d > 16.2 and 45 < deg < 200:
                    col = BRASS
                elif d < 14.6 and (deg < 20 or deg > 220):
                    col = BRASS
                c.set(x, y, col)
            if d <= 13.5:
                c.set(x, y, K)
            if d <= 12.5:
                col = NAVY if y < wy - 5 else (PLUM if y < wy + 3 else VIOLET)
                if y in (wy - 5, wy + 3) and x % 2 == 0:
                    col = NAVY if y == wy - 5 else PLUM
                if y == wy - 6 and x % 2 == 1:
                    col = PLUM
                if y == wy + 2 and x % 2 == 1:
                    col = VIOLET
                c.set(x, y, col)
                sky.set(x, y, 1)
    # Месяц и звёзды.
    for y in range(T):
        for x in range(T):
            if sky.get(x, y) and math.hypot(x - 25, y - 23) <= 3.6 and math.hypot(x - 26.8, y - 22) > 3.0:
                c.set(x, y, WHITE)
    for x, y in ((31, 19), (37, 21), (40, 26), (28, 28), (34, 24)):
        c.set(x, y, SKY)
    # Остров: мшистая шапка, каменное брюхо клином, дерево и нитка водопада.
    for y in range(31, 41):
        half = int(round(7 * (1 - (y - 31) / 9.0) ** 1.5))
        for x in range(37 - half, 38 + half):
            if sky.get(x, y):
                c.set(x, y, METAL if (x + y) % 3 else DARK)
    for x in range(30, 45):
        for y in (30, 31):
            if sky.get(x, y):
                c.set(x, y, TAN)
    c.ellipse(39, 27, 2.6, 2.6, VIOLET)
    c.set(38, 26, WHITE)
    c.set(39, 30, DARK)
    for y in range(32, 41):
        if sky.get(33, y):
            c.set(33, y, AQUA if y % 3 else SKY)
    # Листья на раме.
    for x, y in ((17, 40), (20, 44), (46, 14)):
        c.rect(x, y, x + 2, y + 1, TAN)
        c.set(x + 3, y, TAN)
        c.set(x + 1, y + 2, DARK)
    return c


def tex_cargo():
    """Кладовая гоблинов: плетёные короба 32×32 со сдвигом ряда, обод, крышка с петлёй, красная
    тряпка-метка; из одного короба светят грибы."""
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, K)
    for by in (0, 32):
        for n, bx in enumerate((0, 32)):
            x0 = (bx + (16 if by else 0)) % T
            for y in range(32):
                for x in range(32):
                    col = None
                    if 7 <= y <= 30 and 1 <= x <= 30:
                        # Плетение: прутья через один поверх стоек.
                        over = ((x - 1) // 4 + (y - 7) // 3) % 2 == 0
                        col = BRASS if over else METAL
                        if (y - 7) % 3 == 2:
                            col = DARK if not over else METAL
                        if (x - 1) % 4 == 3 and not over:
                            col = DARK
                        if x in (1, 2):
                            col = BRASS if col != DARK else METAL
                        if x in (29, 30):
                            col = DARK if col != BRASS else METAL
                    elif y in (5, 6) and 0 <= x <= 31:
                        col = GOLD if y == 5 else DARK
                        if y == 5 and x % 4 == 2:
                            col = BRASS
                    elif 1 <= y <= 4:
                        inset = (4 - y) * 2 + 1
                        if inset <= x <= 31 - inset:
                            col = BRASS if (x + y) % 3 else METAL
                            if y == 1:
                                col = GOLD
                    if col is not None:
                        c.set((x0 + x) % T, by + y, col)
            # Верёвочная петля на крышке.
            for x in range(13, 19):
                c.set((x0 + x) % T, by + 1, GREY)
            c.set((x0 + 13) % T, by + 2, GREY)
            c.set((x0 + 18) % T, by + 2, GREY)
            # Метка: красная тряпка с гоблинским знаком.
            for y in range(13, 21):
                for x in range(20, 27):
                    if y < 19 or x % 2 == 0:
                        c.set((x0 + x) % T, by + y, RED)
            for x, y in ((22, 14), (24, 14), (23, 15), (22, 16), (24, 16), (23, 17)):
                c.set((x0 + x) % T, by + y, K)
            if by == 0 and n == 1:
                # Крышка приоткрыта: грибы наружу.
                for x in range(6, 14):
                    for y in (3, 4):
                        c.set((x0 + x) % T, by + y, K)
                for x, col in ((7, AQUA), (8, SKY), (9, AQUA), (11, AQUA), (12, SKY)):
                    c.set((x0 + x) % T, by + 3, col)
                    c.set((x0 + x) % T, by + 4, SEA if col == AQUA else WHITE)
    return c


def tex_floor():
    """Пол нор: тёмная земля, по ней вьются корни со светлым верхом, в просветах кочки мха."""
    rng = random.Random(407)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = DARK
            if (x * 5 + y * 3) % 13 == 0:
                col = PLUM
            elif (x * 11 + y * 7) % 23 == 0:
                col = K
            c.set(x, y, col)
    # Мох: кочки с цветком.
    for _ in range(9):
        mx, my = rng.randrange(T), rng.randrange(T)
        for dy in range(-2, 3):
            for dx in range(-3, 4):
                if dx * dx / 9.0 + dy * dy / 4.0 <= 1.0 and (dx + dy * 3) % 4:
                    c.set((mx + dx) % T, (my + dy) % T, TAN)
        c.set(mx % T, (my - 1) % T, GOLD)

    def root(horizontal, base, amp, k, ph, thick):
        for t in range(T):
            p = base + amp * math.sin(t * math.tau / T * k + ph)
            for d in range(thick + 1):
                col = BRASS if d == 0 else (K if d == thick else METAL)
                q = int(round(p)) + d
                if horizontal:
                    c.set(t, q % T, col)
                else:
                    c.set(q % T, t, col)
            if t % 9 == 4 and thick > 3:
                q = int(round(p)) + 2
                if horizontal:
                    c.set(t, q % T, DARK)
                else:
                    c.set(q % T, t, DARK)

    root(False, 44, 5, 1, 0.5, 4)
    root(True, 12, 4, 2, 1.0, 4)
    root(False, 14, 3, 2, 2.6, 3)
    root(True, 43, 5, 1, 4.0, 5)
    root(True, 28, 2, 3, 0.2, 2)
    return c


def tex_floor_grate():
    """Рунные плиты: сиреневый камень неровными плитами, мох в швах, на трёх плитах светятся
    руны, остальные с вытертой резьбой."""
    c = Canvas(T, T)
    cells = _cells(408, 3, 0.8)
    seen = {}
    for y in range(T):
        for x in range(T):
            i, gap, dx, dy = cells[y][x]
            seen.setdefault(i, (x - dx, y - dy))
            col = GREY
            if gap < 1.4:
                col = DARK
                if (x * 7 + y * 13) % 5 == 0:
                    col = TAN
            elif gap < 2.4:
                # Фаска: свет сверху слева узкой кромкой, тень снизу справа, бока в тон камня.
                col = WHITE if dx + dy < -5 else (PLUM if dx + dy > 3 else GREY)
            elif (x * 5 + y * 11 + i * 3) % 31 == 0:
                col = VIOLET
            elif (x * 3 + y * 5) % 43 == 0:
                col = WHITE
            c.set(x, y, col)
    for i, (px, py) in seen.items():
        x, y = int(round(px)) - 1, int(round(py)) - 2
        if i % 3 == 0:
            for k, ch in enumerate(RUNES[i % len(RUNES)]):
                if ch == "X":
                    for sx in range(2):
                        for sy in range(2):
                            c.set((x - 1 + (k % 3) * 2 + sx) % T, (y - 2 + (k // 3) * 2 + sy) % T, AQUA)
                            c.set((x + (k % 3) * 2) % T, (y - 2 + (k // 3) * 2) % T, SKY)
        else:
            _rune(c, x, y, i + 2, VIOLET)
            _rune(c, x + 1, y + 1, i + 2, WHITE)
            _rune(c, x, y, i + 2, VIOLET)
    return c


def tex_floor_tiles():
    """Ковёр библиотеки: фиолетовый, золотая ромбическая сетка, в ромбах звёзды и месяцы."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 32, y % 32
            d = abs(px - 15.5) + abs(py - 15.5)
            col = PLUM
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                col = VIOLET if d < 13 else PLUM
            if 14 <= d <= 15:
                col = BRASS
            elif d > 28:
                col = RED
            elif d > 15 and (x + y) % 2 == 0:
                col = NAVY
            c.set(x, y, col)
    for bx in (0, 32):
        for by in (0, 32):
            cx, cy = bx + 15, by + 15
            for dy in range(-7, 9):
                for dx in range(-7, 9):
                    if abs(dx - 0.5) + abs(dy - 0.5) <= 6:
                        c.set(cx + dx, cy + dy, PLUM)
            if (bx + by) % 64 == 0:
                # Звезда в четыре луча.
                for k in range(-5, 7):
                    c.set(cx + k, cy, GOLD)
                    c.set(cx + k, cy + 1, GOLD)
                    c.set(cx, cy + k, GOLD)
                    c.set(cx + 1, cy + k, GOLD)
                c.rect(cx - 1, cy - 1, cx + 2, cy + 2, GOLD)
                c.rect(cx, cy, cx + 1, cy + 1, WHITE)
                for dx, dy in ((-3, -3), (4, -3), (-3, 4), (4, 4)):
                    c.set(cx + dx, cy + dy, BRASS)
            else:
                for dy in range(-6, 7):
                    for dx in range(-6, 7):
                        if math.hypot(dx, dy) <= 5.2 and math.hypot(dx - 2.5, dy - 1) > 4.2:
                            c.set(cx + dx, cy + dy, GOLD)
                c.set(cx + 3, cy - 3, WHITE)
                c.set(cx + 4, cy + 2, BRASS)
    return c


def tex_ceiling():
    """Потолок: тёмный свод в переплетении корней, редкие светлячки точками (без ярких полос,
    иначе в перспективе они расходятся лучами)."""
    rng = random.Random(409)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = NAVY if (x * 7 + y * 3) % 11 else K
            if (x * 3 + y * 13) % 17 == 0:
                col = PLUM
            c.set(x, y, col)
    for horizontal, base, amp, k, ph in ((True, 8, 4, 1, 0.0), (False, 20, 5, 2, 1.5), (True, 38, 3, 2, 3.0),
                                         (False, 50, 4, 1, 4.4), (True, 54, 2, 3, 2.0)):
        for t in range(T):
            p = int(round(base + amp * math.sin(t * math.tau / T * k + ph)))
            for d in range(4):
                col = METAL if d == 0 and t % 3 else (K if d == 3 else DARK)
                if horizontal:
                    c.set(t, (p + d) % T, col)
                else:
                    c.set((p + d) % T, t, col)
    for _ in range(14):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == NAVY:
            c.set(x, y, PLUM)
    for x, y in ((12, 26), (44, 18), (30, 46), (58, 60)):
        c.rect(x, y, x + 1, y + 1, GOLD)
        c.set(x, y, WHITE)
    return c


# --- Гоблины -----------------------------------------------------------------------------------
# Облик из основы (`fantasy16.goblin_*`): зелёная кожа, огромные острые уши, длинный нос, жёлтые
# глаза, клыки снизу. Дубинщик (`rod`) в бурой рубахе с поясом; шаман в сиреневом пончо, с
# перьями на голове и посохом с черепом. Силуэты разведены ушами (торчком и вислые), перьями
# и оружием.

def _club(c, hx, hy, tx, ty):
    """Дубинка от кулака (hx, hy) к концу (tx, ty): рукоять, толстая голова, обруч, шипы."""
    n = math.hypot(tx - hx, ty - hy)
    ux, uy = (tx - hx) / n, (ty - hy) / n
    nx, ny = -uy, ux

    def at(k, side=0.0):
        return hx + (tx - hx) * k + nx * side, hy + (ty - hy) * k + ny * side

    for k, side in ((0.62, 5.5), (0.62, -5.5), (0.9, 5.5), (0.9, -5.5)):
        b = at(k)
        p = at(k, side)
        c.poly([(b[0] - ux * 2, b[1] - uy * 2), (b[0] + ux * 2, b[1] + uy * 2), p], GREY)
        c.line(b[0], b[1], p[0], p[1], GREY, 2)
    p = (tx + ux * 4.5, ty + uy * 4.5)
    c.line(tx, ty, p[0], p[1], GREY, 2)
    c.line(hx - ux * 4, hy - uy * 4, at(0.5)[0], at(0.5)[1], METAL, 3)
    c.line(at(0.42)[0], at(0.42)[1], at(0.55)[0], at(0.55)[1], METAL, 5)
    c.line(at(0.55)[0], at(0.55)[1], tx, ty, METAL, 8)
    a, b = at(0.5, -2.6), at(0.5, 2.6)
    c.line(a[0], a[1], b[0], b[1], DARK, 2)
    a, b = at(0.62, -2.0), at(0.95, -2.0)
    c.line(a[0], a[1], b[0], b[1], BRASS, 1)
    a = at(0.78, 1.0)
    c.set(a[0], a[1], DARK)


def _skull(c, sx, sy, r=4.0, glow=TAN):
    """Череп на посохе: свод, челюсть, глазницы с огоньком, зубы."""
    c.ellipse(sx, sy, r, r * 0.9, WHITE)
    j = max(2, int(round(r * 0.55)))
    c.rect(sx - j, sy + r * 0.6, sx + j, sy + r * 1.3, WHITE)
    e = r * 0.45
    c.ellipse(sx - e, sy, r * 0.28, r * 0.33, K)
    c.ellipse(sx + e, sy, r * 0.28, r * 0.33, K)
    if r > 5:
        c.set(sx - e, sy, glow)
        c.set(sx + e, sy, glow)
        c.rect(sx, sy + 2, sx, sy + 3, K)
        for x in range(-j + 1, j, 2):
            c.set(sx + x, sy + r * 1.3, K)
    else:
        c.set(sx, sy + r * 1.3, K)


def _staff(c, bx, by, tx, ty):
    """Посох шамана от пяты к вершине: кривое древко, красная кисть, череп над вершиной."""
    n = math.hypot(tx - bx, ty - by)
    ux, uy = (tx - bx) / n, (ty - by) / n
    c.line(bx, by, tx, ty, METAL, 3)
    c.line(tx, ty, tx - 3, ty + 5, RED, 2)
    c.set(tx - 3, ty + 6, GOLD)
    c.rect(tx - 2, ty + 1, tx + 2, ty + 2, DARK)
    _skull(c, tx + ux * 4, ty + uy * 4)


def _fist(c, x, y):
    c.ellipse(x, y, 2.6, 2.6, TAN)


def _fallen(k, rod):
    """Гоблин падает: 1 оседает на колени, уши обвисли, язык наружу; 2 лежит на спине ногами
    влево, оружие рядом."""
    c = Canvas(T, T)
    cx = 32
    cloth = METAL if rod else VIOLET
    if k == 1:
        # Оружие валится вбок.
        if rod:
            _club(c, cx + 15, 58, cx + 25, 38)
        else:
            _staff(c, cx + 14, 61, cx + 23, 36)
        # Колени и ступни.
        for sign in (-1, 1):
            c.ellipse(cx + sign * 8, 56, 5, 4, DARK)
            c.rect(cx + sign * 8 - 4, 59, cx + sign * 8 + 4, 62, TAN)
        c.ellipse(cx, 47, 11, 9, cloth)
        c.rect(cx - 10, 50, cx + 10, 55, cloth)
        if rod:
            c.rect(cx - 10, 51, cx + 10, 52, DARK)
            c.rect(cx - 1, 51, cx + 1, 52, GOLD)
        else:
            c.rect(cx - 11, 49, cx + 11, 50, PLUM)
            for x in range(cx - 9, cx + 10, 4):
                c.set(x, 49, GOLD)
        # Руки обвисли.
        c.line(cx - 10, 42, cx - 15, 54, TAN, 4)
        c.line(cx + 10, 42, cx + 14, 54, TAN, 4)
        hx, hy = cx + 2, 31
        c.poly([(hx - 7, hy - 2), (hx - 21, hy + 5), (hx - 16, hy + 8), (hx - 8, hy + 5)], TAN)
        c.poly([(hx + 7, hy - 2), (hx + 21, hy + 5), (hx + 16, hy + 8), (hx + 8, hy + 5)], TAN)
        c.ellipse(hx, hy, 10, 8, TAN)
        c.rect(hx - 7, hy + 2, hx + 7, hy + 9, TAN)
        c.line(hx - 17, hy + 5, hx - 10, hy + 3, PLUM, 1)
        c.line(hx + 17, hy + 5, hx + 10, hy + 3, PLUM, 1)
        for e in (-5, 5):
            c.line(hx + e - 2, hy - 3, hx + e + 2, hy + 1, K, 1)
            c.line(hx + e - 2, hy + 1, hx + e + 2, hy - 3, K, 1)
        c.rect(hx - 4, hy + 5, hx + 4, hy + 7, K)
        c.rect(hx - 1, hy + 6, hx + 2, hy + 10, RED)
        c.set(hx - 4, hy + 5, WHITE)
        c.set(hx + 4, hy + 5, WHITE)
        if not rod:
            c.rect(hx - 7, hy - 7, hx + 7, hy - 6, DARK)
            c.poly([(hx - 3, hy - 7), (hx - 9, hy - 16), (hx + 1, hy - 7)], RED)
            c.poly([(hx + 9, hy - 22), (hx + 14, hy - 27), (hx + 13, hy - 20)], GOLD)
        return c.finish()
    # Лежит: ноги слева носками вверх, тело, голова справа, ухо торчит.
    if rod:
        _club(c, cx - 4, 50, cx - 24, 46)
    else:
        c.line(cx - 26, 50, cx + 4, 47, METAL, 3)
        _skull(c, cx + 27, 43, 3.6)
    for x in (cx - 21, cx - 15):
        c.line(cx - 10, 57, x, 57, DARK, 5)
        c.rect(x - 2, 52, x + 1, 60, TAN)
    c.ellipse(cx - 1, 56, 13, 5.5, cloth)
    c.rect(cx - 12, 57, cx + 10, 61, cloth)
    if rod:
        c.rect(cx - 5, 51, cx - 4, 61, DARK)
        c.rect(cx - 5, 53, cx - 4, 54, GOLD)
    else:
        c.rect(cx - 6, 51, cx - 5, 61, PLUM)
        for y in range(52, 61, 3):
            c.set(cx - 6, y, GOLD)
    c.line(cx + 4, 55, cx + 2, 61, TAN, 4)
    hx, hy = cx + 17, 55
    c.poly([(hx - 3, hy - 4), (hx + 1, hy - 17), (hx + 6, hy - 4)], TAN)
    c.ellipse(hx, hy, 8, 6.5, TAN)
    c.rect(hx - 5, hy + 2, hx + 7, hy + 6, TAN)
    c.poly([(hx + 6, hy - 3), (hx + 12, hy - 7), (hx + 9, hy + 1)], TAN)
    c.line(hx + 1, hy - 13, hx + 2, hy - 6, PLUM, 1)
    c.line(hx - 4, hy - 2, hx, hy - 2, K, 1)
    c.line(hx + 3, hy - 2, hx + 6, hy - 2, K, 1)
    c.rect(hx - 1, hy + 3, hx + 5, hy + 3, K)
    c.set(hx, hy + 2, WHITE)
    c.set(hx + 4, hy + 2, WHITE)
    c.rect(hx + 5, hy + 4, hx + 7, hy + 5, RED)
    if not rod:
        c.rect(hx - 7, hy - 5, hx - 6, hy + 1, DARK)
        c.poly([(hx - 7, hy - 3), (hx - 15, hy - 8), (hx - 7, hy)], RED)
    for x in range(64):
        for y in (62, 63):
            c.set(x, y, None)
    return c.finish()


def alien(angle, phase, mode="walk", rod=False):
    """Гоблин 64×64 в ракурсе `angle` (0 спереди … 4 со спины, лицом вправо на 1-3), шаг `phase`
    0/1. `mode`: walk, aim, fire, slash, die0..die2, hurt. `rod` дубинщик: уши торчком и шипастая
    дубинка; без него шаман: перья, пончо, посох с черепом, из черепа летит порча. Ступни на
    61-62 строке, ось по центру кадра, как у скелета пиратов. Имя функции как у зеркала."""
    if mode.startswith("die"):
        k = int(mode[-1])
        if k == 0:
            return alien(0, 0, "hurt", rod)
        return _fallen(k, rod)
    c = Canvas(T, T)
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    bob = 1 if phase else 0
    cloth = METAL if rod else VIOLET
    w = 7 if side else (9 if diag else 10)
    top = 25 - bob
    turn = 1 if angle in (1, 2) else (-1 if angle == 3 else 0)
    # Дальняя рука висит, кулак у бедра.
    if side:
        c.line(cx - 2, top + 4, cx - 5 - (2 if phase else -2), 40 - bob, TAN, 4)
    else:
        c.line(cx - w, top + 4, cx - w - 4, 39 - bob, TAN, 4)
        _fist(c, cx - w - 4, 41 - bob)
    # Ноги: короткие, кривые, в рваных тёмных штанах, босые ступни.
    for sign in (-1, 1):
        swing = (sign * 3 if phase else -sign * 3) if mode == "walk" else 0
        hip = (cx + sign * (2 if side else 5), 44 - bob)
        fx = cx + sign * (2 if side else 7) + swing * (1.4 if side else 0.3)
        lift = 2 if (swing > 0 and not side) else 0
        knee = ((hip[0] + fx) / 2 + (2 if side else sign * 2), 53 - lift)
        c.line(hip[0], hip[1], knee[0], knee[1], DARK, 6)
        c.line(knee[0], knee[1], fx, 59 - lift, TAN, 4)
        if side:
            c.rect(fx - 2, 60 - lift, fx + 6, 62 - lift, TAN)
        elif back:
            c.rect(fx - 3, 60 - lift, fx + 3, 62 - lift, TAN)
        else:
            c.rect(fx - 3 + turn, 60 - lift, fx + 4 + turn, 62 - lift, TAN)
            c.set(fx - 1 + turn, 62 - lift, DARK)
            c.set(fx + 2 + turn, 62 - lift, DARK)
    # Корпус: сутулые плечи бочонком, рваный подол.
    c.ellipse(cx, top + 4, w + 1, 5.5, cloth)
    c.poly([(cx - w, top + 3), (cx + w, top + 3), (cx + w + 2, 45 - bob), (cx - w - 2, 45 - bob)], cloth)
    for x in range(cx - w - 2, cx + w + 1, 4):
        c.poly([(x, 45 - bob), (x + 3, 45 - bob), (x + 1.5, 48 - bob)], cloth)
    if rod:
        c.rect(cx - w - 1, 39 - bob, cx + w + 1, 40 - bob, DARK)
        if back:
            # Ремень через спину и заплата.
            c.line(cx - w + 1, top + 4, cx + w - 1, 38 - bob, DARK, 2)
            c.rect(cx - 5, 33 - bob, cx - 1, 36 - bob, BRASS)
            c.set(cx - 5, 33 - bob, DARK)
            c.set(cx - 1, 36 - bob, DARK)
        else:
            c.rect(cx - 1 + turn * 3, 38 - bob, cx + 2 + turn * 3, 41 - bob, GOLD)
            c.set(cx + turn * 3, 39 - bob, DARK)
            c.rect(cx - 6 + turn * 2, 31 - bob, cx - 3 + turn * 2, 34 - bob, BRASS)
            c.set(cx - 6 + turn * 2, 31 - bob, DARK)
            c.set(cx - 3 + turn * 2, 34 - bob, DARK)
            c.set(cx + 4 + turn * 2, 43 - bob, DARK)
    else:
        # Пончо шамана: кайма с золотыми точками, зубчатый узор, на груди ожерелье из клыков.
        c.rect(cx - w - 1, 39 - bob, cx + w + 1, 41 - bob, PLUM)
        for x in range(cx - w, cx + w + 1, 3):
            c.set(x, 40 - bob, GOLD)
        for x in range(cx - w + 1, cx + w, 4):
            c.set(x, 35 - bob, PLUM)
            c.set(x + 1, 34 - bob, PLUM)
            c.set(x + 2, 35 - bob, PLUM)
        if back:
            c.rect(cx, top + 3, cx, 38 - bob, PLUM)
        else:
            for i in range(-2, 3):
                c.set(cx + turn * 2 + i * 3, 30 - bob - abs(i), WHITE)
                c.set(cx + turn * 2 + i * 3, 31 - bob - abs(i), WHITE)
    # Голова: уши, череп, тяжёлая челюсть.
    off = 0 if angle in (0, 4) else (4 if side else 2)
    hx = cx + off
    hy = 15 - bob
    if rod:
        big = [(-8, -4), (-21, -11), (-17, -2), (-9, 3)]
        small = [(6, -5), (13, -11), (10, -2)]
        side_ear = [(-4, -4), (-18, -12), (-14, -3), (-7, 3)]
    else:
        big = [(-8, -3), (-21, -1), (-18, 3), (-9, 4)]
        small = [(7, -3), (14, -2), (9, 2)]
        side_ear = [(-4, -3), (-19, -3), (-15, 2), (-7, 4)]
    ear_lines = []
    if side:
        c.poly([(hx + x, hy + y) for x, y in side_ear], TAN)
        ear_lines.append((hx + side_ear[1][0] + 4, hy + side_ear[1][1] + 3, hx - 7, hy))
    elif diag:
        m = 1 if angle == 1 else -1
        hx_ = hx if angle == 1 else cx - 2
        hx = hx_
        c.poly([(hx + m * (x + 2), hy + y) for x, y in big], TAN)
        c.poly([(hx + m * x, hy + y) for x, y in small], TAN)
        ear_lines.append((hx + m * (big[1][0] + 6), hy + big[1][1] + 3, hx + m * -8, hy))
    else:
        for m in (-1, 1):
            c.poly([(hx - m * x, hy + y) for x, y in big], TAN)
            ear_lines.append((hx - m * (big[1][0] + 4), hy + big[1][1] + 3, hx + m * 10, hy))
    if side:
        c.ellipse(hx - 1, hy, 9, 8, TAN)
        c.rect(hx - 4, hy + 2, hx + 7, hy + 9, TAN)
        c.poly([(hx + 6, hy - 3), (hx + 13, hy + 2), (hx + 12, hy + 4), (hx + 6, hy + 4)], TAN)
    elif diag:
        m = 1 if angle == 1 else -1
        c.ellipse(hx, hy, 9.5, 8, TAN)
        c.rect(hx - 6, hy + 2, hx + 6, hy + 9, TAN)
        if angle == 1:
            c.poly([(hx + 6, hy - 2), (hx + 12, hy + 2), (hx + 11, hy + 4), (hx + 6, hy + 5)], TAN)
        else:
            c.poly([(hx - 7, hy), (hx - 11, hy + 3), (hx - 7, hy + 5)], TAN)
    else:
        c.ellipse(hx, hy, 10, 8, TAN)
        c.rect(hx - 7, hy + 2, hx + 7, hy + 9, TAN)
    for x0, y0, x1, y1 in ear_lines:
        c.line(x0, y0, x1, y1, PLUM, 1)
    roar = mode in ("slash", "fire")
    if not back:
        if side:
            c.rect(hx + 3, hy - 2, hx + 5, hy - 1, GOLD)
            c.set(hx + 5, hy - 1, K)
            c.line(hx + 1, hy - 5, hx + 6, hy - 3, K, 1)
            c.rect(hx + 9, hy + 4, hx + 10, hy + 4, DARK)
            c.rect(hx + 2, hy + 6, hx + 7, hy + 6, K)
            c.set(hx + 6, hy + 5, WHITE)
            c.set(hx + 3, hy + 5, WHITE)
        else:
            sh = 2 if diag else 0
            for e in (-5, 5):
                ex = hx + e + sh
                c.rect(ex - 2, hy - 2, ex + 1, hy - 1, GOLD)
                c.set(ex - (1 if e > 0 else 0) + (1 if diag else 0), hy - 1, K if mode != "fire" else RED)
                c.set(ex - (1 if e > 0 else 0) + (1 if diag else 0), hy - 2, K if mode != "fire" else RED)
                c.line(ex - (3 if e < 0 else -2), hy - 5, ex + (2 if e < 0 else -3), hy - 3, K, 1)
            # Нос картошкой: тень снизу и по бокам.
            nx = hx + sh * 2
            c.rect(nx - 1, hy + 3, nx + 1, hy + 3, DARK)
            c.set(nx - 2, hy + 2, DARK)
            c.set(nx + 2, hy + 2, DARK)
            mx = hx + sh
            if roar:
                c.rect(mx - 5, hy + 5, mx + 5, hy + 8, K)
                c.rect(mx - 2, hy + 7, mx + 2, hy + 8, RED)
                for x in (-5, -2, 2, 5):
                    c.set(mx + x, hy + 5, WHITE)
                c.set(mx - 4, hy + 8, WHITE)
                c.set(mx + 4, hy + 8, WHITE)
            else:
                c.rect(mx - 6, hy + 6, mx + 6, hy + 6, K)
                for x in (-5, 5):
                    c.rect(mx + x, hy + 4, mx + x, hy + 5, WHITE)
                c.set(mx - 2, hy + 7, WHITE)
                c.set(mx + 2, hy + 7, WHITE)
            if not rod:
                # Боевая раскраска шамана.
                c.rect(hx - 8 + sh, hy + 1, hx - 6 + sh, hy + 1, WHITE)
                c.rect(hx + 6 + sh, hy + 1, hx + 8 + sh, hy + 1, WHITE)
    else:
        # Затылок: складки и редкая щетина.
        c.line(hx - 5, hy + 1, hx + 5, hy + 1, PLUM, 1)
        c.line(hx - 4, hy + 5, hx + 4, hy + 5, PLUM, 1)
        if rod:
            for x in (-2, 0, 2):
                c.set(hx + x, hy - 6, DARK)
    if rod:
        # Золотая серьга в ухе.
        if side:
            c.rect(hx - 13, hy - 4, hx - 12, hy - 2, GOLD)
        elif not diag:
            c.rect(hx + 14, hy - 3, hx + 15, hy - 1, GOLD)
        else:
            m = 1 if angle == 1 else -1
            c.rect(hx - m * 13 - 1, hy - 3, hx - m * 13, hy - 1, GOLD)
    else:
        # Повязка и три пера.
        lean = -4 if side else (-2 * turn if diag else 0)
        hw = 6 if side else 7
        c.rect(hx - hw - (1 if side else 0), hy - 6, hx + hw - (1 if side else 0), hy - 5, DARK)
        if not back:
            c.set(hx + (4 if side else turn * 2), hy - 5, WHITE)
        c.poly([(hx - 7, hy - 6), (hx - 9 + lean, hy - 12), (hx - 3, hy - 6)], GOLD)
        c.poly([(hx + 3, hy - 6), (hx + 9 + lean, hy - 12), (hx + 7, hy - 6)], GOLD)
        c.poly([(hx - 3, hy - 6), (hx + lean, hy - 14), (hx + 3, hy - 6)], RED)
        c.set(hx + lean, hy - 14, WHITE)
        c.set(hx + lean, hy - 13, WHITE)
    # Ближняя рука и оружие.
    if rod:
        if side:
            hand = (cx + 11, 35 - bob)
            c.line(cx + 1, top + 4, hand[0], hand[1], TAN, 4)
            _club(c, hand[0], hand[1], cx + 25, 18 - bob)
        elif mode == "slash":
            hand = (cx + w + 4, 19 - bob)
            c.line(cx + w, top + 3, hand[0], hand[1], TAN, 5)
            _club(c, hand[0], hand[1], cx + w + 11, 4)
        else:
            hand = (cx + w + 4, 37 - bob)
            c.line(cx + w, top + 4, hand[0], hand[1], TAN, 4)
            _club(c, hand[0], hand[1], cx + w + 15, 22 - bob)
        _fist(c, hand[0], hand[1])
    elif mode in ("aim", "fire"):
        # Посох черепом в камеру: обе руки вперёд.
        c.line(cx - w, top + 4, cx - 7, 37 - bob, TAN, 4)
        c.line(cx + w, top + 4, cx + 7, 37 - bob, TAN, 4)
        c.line(cx, 40 - bob, cx - 1, 48 - bob, METAL, 3)
        _skull(c, cx, 33 - bob, 6.5, TAN if mode == "aim" else RED)
        _fist(c, cx - 7, 38 - bob)
        _fist(c, cx + 7, 38 - bob)
    elif side:
        hand = (cx + 11, 38 - bob)
        c.line(cx + 1, top + 4, hand[0], hand[1], TAN, 4)
        _staff(c, cx + 6, 61, cx + 18, 34 - bob)
        hand = (cx + 6 + 12 * (61 - hand[1]) / (27.0 + bob), hand[1])
        _fist(c, hand[0], hand[1])
    else:
        hand = (cx + w + 9, 39 - bob)
        c.line(cx + w, top + 4, hand[0], hand[1], TAN, 4)
        _staff(c, hand[0], 61, hand[0], 33 - bob)
        _fist(c, hand[0], hand[1])
    c.finish()
    if mode == "fire":
        fx, fy = cx, 32 - bob
        for k in range(8):
            a = k * math.tau / 8 + 0.4
            c.line(fx, fy, fx + math.cos(a) * 10, fy + math.sin(a) * 9, TAN, 1)
        c.ellipse(fx, fy, 7, 6, PLUM)
        c.ellipse(fx, fy, 5.5, 4.6, TAN)
        c.ellipse(fx, fy, 2.6, 2.2, WHITE)
    if mode == "hurt":
        for x in range(T):
            for y in range(T):
                if c.get(x, y) == TAN and (x + y) % 3 == 0:
                    c.set(x, y, RED)
    return c


def alien_strips():
    out = {}
    for name, rod in (("skel", False), ("cut", True)):
        walk = []
        for a in range(5):
            for ph in range(2):
                walk.append(alien(a, ph, "walk", rod))
        out[name + "_walk"] = strip(walk)
        out[name + "_die"] = strip([alien(0, 0, "die%d" % k, rod) for k in range(3)])
    out["skel_fire"] = strip([alien(0, 0, "aim"), alien(0, 0, "fire")])
    out["cut_slash"] = strip([alien(0, 0, "walk", True), alien(0, 0, "slash", True)])
    return out


# --- Предметы, оружие, лицо --------------------------------------------------------------------

def shot():
    """Выстрел шамана: зелёный сгусток порчи в фиолетовой кромке, чтобы не путать с огненным
    шаром героя; в ядре глазницы черепа."""
    c = Canvas(16, 16)
    c.ellipse(8, 8, 6, 6, PLUM)
    c.ellipse(8, 8, 4.6, 4.6, TAN)
    c.ellipse(7, 7, 2.2, 2.2, WHITE)
    c.set(6, 7, K)
    c.set(8, 7, K)
    for x, y in ((2, 3), (13, 4), (3, 13), (13, 12)):
        c.set(x, y, VIOLET)
    return c


def bullet():
    """Огненный шар героя: красное пламя с золотым телом, белое ядро, хвост книзу."""
    c = Canvas(16, 16)
    c.ellipse(8, 7, 3.6, 3.6, RED)
    c.poly([(5, 9), (11, 9), (8, 14)], RED)
    c.finish()
    c.ellipse(8, 7, 2.2, 2.2, GOLD)
    c.set(8, 11, GOLD)
    c.ellipse(7.5, 6.5, 1.0, 1.0, WHITE)
    return c


def decor(kind):
    """Ориентир зала 64×64, низ на 62-63 строке: 0 гигантские грибы, 1 сундук-мимик, 2
    фонарь-цветок, 3 кристалл на треноге, 4 котёл с зельем, 5 рунный камень."""
    c = Canvas(T, T)
    if kind == 0:
        # Три гриба: ножка с юбкой, сиреневая шляпка в светлых пятнах, бирюзовые пластинки.
        for bx, top, r, sw in ((14, 38, 11, 3), (50, 44, 9, 2), (31, 10, 17, 4)):
            c.poly([(bx - sw, top + 6), (bx + sw, top + 6), (bx + sw + 2, 62), (bx - sw - 2, 62)], WHITE)
            c.rect(bx - sw - 1, top + 12, bx + sw + 1, top + 13, GREY)
            c.rect(bx - r + 2, top + 5, bx + r - 2, top + 7, AQUA)
            for x in range(bx - r + 3, bx + r - 2, 3):
                c.rect(x, top + 5, x, top + 7, SEA)
            for y in range(top - int(r * 0.55), top + 6):
                k = (y - (top - r * 0.55)) / (r * 0.55 + 5)
                half = r * math.sqrt(max(0.0, 1 - (1 - k) ** 2))
                c.rect(bx - half, y, bx + half, y, VIOLET)
            c.rect(bx - r, top + 4, bx + r, top + 5, PLUM)
            for dx, dy, rr in ((-0.45, 0.2, 0.2), (0.3, -0.15, 0.16), (0.55, 0.3, 0.12), (-0.1, -0.3, 0.12)):
                c.ellipse(bx + dx * r, top + dy * r * 0.6, max(1.0, rr * r), max(0.8, rr * r * 0.7), SKY)
        for x in (4, 24, 42, 58):
            c.rect(x, 60, x + 1, 62, TAN)
            c.set(x + 2, 61, TAN)
    elif kind == 1:
        # Сундук-мимик: крышка откинута, зубы в два ряда, язык наружу, глаз под крышкой.
        c.rect(10, 40, 53, 62, METAL)
        c.rect(10, 40, 53, 41, K)
        for x in (10, 30, 50):
            c.rect(x, 42, x + 3, 62, GOLD)
            c.set(x + 1, 46, BRASS)
            c.set(x + 1, 56, BRASS)
        for y in (48, 55):
            c.rect(14, y, 49, y, DARK)
        c.rect(10, 61, 53, 62, DARK)
        # Пасть: тёмная глотка между крышкой и ящиком.
        c.poly([(10, 40), (53, 40), (55, 24), (8, 24)], DARK)
        c.poly([(13, 38), (50, 38), (51, 27), (12, 27)], K)
        # Крышка горбом.
        c.poly([(6, 24), (57, 24), (55, 12), (46, 6), (17, 6), (8, 12)], METAL)
        c.rect(6, 22, 57, 24, GOLD)
        for x in (10, 30, 50):
            c.rect(x, 7 if x == 30 else 11, x + 3, 22, GOLD)
        c.line(14, 14, 28, 9, BRASS, 1)
        c.line(35, 9, 48, 14, BRASS, 1)
        for x in range(13, 50, 6):
            c.poly([(x, 27), (x + 4, 27), (x + 2, 32)], WHITE)
            c.poly([(x + 3, 38), (x + 7, 38), (x + 5, 33)], WHITE)
        # Язык и глаз.
        c.poly([(26, 38), (38, 38), (40, 50), (34, 56), (27, 52)], RED)
        c.line(32, 39, 33, 52, PLUM, 1)
        c.ellipse(41, 16, 4.5, 3.5, GOLD)
        c.ellipse(42, 16, 1.5, 2.5, K)
        c.line(36, 11, 46, 13, K, 1)
    elif kind == 2:
        # Фонарь-цветок: изогнутый стебель, колокол бутона вниз, в нём огонь; листья у земли.
        pts = [(34, 62), (35, 48), (33, 34), (28, 20), (30, 10), (38, 6), (45, 10)]
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1], b[0], b[1], TAN, 4)
        c.poly([(34, 60), (14, 50), (10, 56), (30, 62)], TAN)
        c.poly([(35, 60), (54, 52), (57, 58), (38, 62)], TAN)
        c.poly([(33, 40), (20, 32), (22, 39)], TAN)
        c.poly([(34, 30), (44, 26), (41, 32)], TAN)
        # Бутон: чашечка, лепестки раструбом, свет изнутри.
        c.rect(42, 9, 49, 12, TAN)
        c.poly([(40, 12), (51, 12), (56, 30), (51, 27), (46, 32), (41, 27), (36, 30)], VIOLET)
        c.poly([(43, 16), (48, 16), (50, 26), (46, 29), (42, 26)], GOLD)
        c.ellipse(46, 23, 2.0, 3.0, WHITE)
        c.line(40, 14, 38, 27, PLUM, 1)
        c.line(51, 14, 54, 27, PLUM, 1)
        c.line(14, 53, 30, 60, DARK, 1)
        c.line(54, 55, 38, 60, DARK, 1)
        for x, y in ((40, 36), (52, 37), (46, 40), (36, 42), (55, 44)):
            c.set(x, y, GOLD)
    elif kind == 3:
        # Кристалл на треноге: три ноги, золотая чаша-оправа, гранёный кристалл с бликом.
        c.line(32, 40, 13, 62, METAL, 4)
        c.line(32, 40, 51, 62, METAL, 4)
        c.line(32, 40, 32, 62, DARK, 4)
        c.line(20, 54, 44, 54, DARK, 2)
        c.poly([(18, 34), (46, 34), (40, 43), (24, 43)], GOLD)
        c.rect(18, 33, 46, 35, BRASS)
        for x in range(21, 45, 6):
            c.set(x, 38, RED)
        c.poly([(32, 1), (42, 14), (39, 34), (25, 34), (22, 14)], AQUA)
        c.poly([(32, 1), (42, 14), (39, 34), (32, 34), (32, 14)], SEA)
        c.poly([(32, 1), (22, 14), (32, 14)], SKY)
        c.line(32, 14, 32, 33, SKY, 1)
        c.line(24, 16, 26, 31, WHITE, 1)
        c.line(22, 14, 42, 14, SKY, 1)
        c.set(36, 20, AQUA)
        c.set(37, 26, AQUA)
        for x, y in ((12, 10), (52, 8), (50, 24), (14, 26)):
            c.set(x, y, SKY)
            c.set(x + 1, y, AQUA)
            c.set(x, y + 1, AQUA)
    elif kind == 4:
        # Котёл: пузатый, на трёх лапах над костром, зелёное варево с пузырями и пар.
        for x0, x1 in ((16, 26), (48, 38)):
            c.line(x0, 60, x1, 55, METAL, 3)
        c.poly([(24, 62), (28, 50), (32, 62)], RED)
        c.poly([(31, 62), (36, 48), (41, 62)], RED)
        c.poly([(27, 62), (30, 55), (33, 62)], GOLD)
        c.poly([(33, 62), (36, 54), (39, 62)], GOLD)
        c.ellipse(32, 40, 21, 16, DARK)
        for x in (15, 49):
            c.rect(x - 2, 52, x + 2, 59, DARK)
        c.rect(10, 24, 54, 29, GREY)
        c.rect(10, 24, 54, 24, WHITE)
        c.ellipse(32, 26, 19, 3.2, TAN)
        c.ellipse(26, 25, 3, 1.5, WHITE)
        c.ellipse(40, 27, 2, 1, WHITE)
        c.ellipse(22, 20, 3, 3, TAN)
        c.ellipse(41, 16, 2.2, 2.2, TAN)
        c.ellipse(33, 11, 1.6, 1.6, TAN)
        c.set(21, 19, WHITE)
        c.set(40, 15, WHITE)
        # Блик на боку и клёпки, ручка-кольцо.
        c.line(17, 36, 20, 47, GREY, 1)
        c.line(19, 35, 21, 41, GREY, 1)
        for x in range(16, 50, 8):
            c.set(x, 32, GREY)
        c.ellipse(53, 38, 3.5, 4.5, GREY)
        c.ellipse(53, 38, 1.8, 2.8, DARK)
    else:
        # Рунный камень: наклонный менгир, светящиеся руны столбцом, трещины, мох и камни внизу.
        c.poly([(20, 62), (22, 20), (27, 7), (36, 3), (43, 9), (46, 26), (47, 62)], GREY)
        c.poly([(40, 8), (43, 9), (46, 26), (47, 62), (42, 62), (41, 26)], VIOLET)
        c.line(23, 20, 27, 8, WHITE, 1)
        c.line(22, 22, 21, 52, WHITE, 1)
        # Руны: спираль, стрела, вилка.
        c.ellipse(32, 17, 5, 5, AQUA)
        c.ellipse(32, 17, 3.4, 3.4, GREY)
        c.ellipse(32.5, 17.5, 1.6, 1.6, AQUA)
        c.rect(32, 12, 37, 13, GREY)
        c.set(35, 15, AQUA)
        c.line(32, 27, 32, 39, AQUA, 2)
        c.line(32, 27, 27, 32, AQUA, 2)
        c.line(33, 27, 37, 32, AQUA, 2)
        c.line(28, 44, 32, 49, AQUA, 2)
        c.line(37, 44, 33, 49, AQUA, 2)
        c.line(32, 49, 32, 55, AQUA, 2)
        c.set(32, 28, SKY)
        c.set(32, 50, SKY)
        c.set(30, 14, SKY)
        c.line(39, 20, 37, 24, DARK, 1)
        c.line(37, 24, 39, 29, DARK, 1)
        c.line(24, 40, 26, 44, DARK, 1)
        # Мох у подножия, обломки.
        c.ellipse(22, 60, 7, 3, TAN)
        c.ellipse(45, 61, 6, 2.2, TAN)
        c.rect(15, 60, 52, 62, TAN)
        c.ellipse(11, 59, 4, 3.5, GREY)
        c.ellipse(54, 60, 3.5, 2.5, GREY)
        c.set(10, 57, WHITE)
        c.set(25, 58, GOLD)
        c.set(44, 60, VIOLET)
    return c.finish()


def key():
    """Ключ из основы набора: золотой, головка ромбом с бирюзовым камнем."""
    return fantasy16.key()


def medkit():
    """Лечит зелье из основы набора: круглая колба с пробкой и золотой звездой."""
    return fantasy16.potion()


def pistol(frame):
    """Волшебная палочка в руке снизу по центру, 128×96: раструб синего рукава мантии с золотой
    каймой, кулак, палочка остриём вглубь (ось x=64, кристалл у верхнего края); кадр 1 со
    вспышкой огня."""
    c = Canvas(128, 96)
    # Рукав: колокол, складки тенью, золотые звёзды.
    for y in range(64, 96):
        w = 19 + (y - 64) * 2 // 3
        for x in range(64 - w, 64 + w + 1):
            col = SEA
            k = (x - 64) / float(w)
            if abs(k) > 0.86:
                col = NAVY
            elif abs(abs(k) - 0.42) < 0.035 or abs(k + 0.08) < 0.03:
                col = NAVY
            c.set(x, y, col)
    for sx, sy in ((50, 82), (77, 78), (62, 90), (88, 92), (40, 93)):
        c.rect(sx - 1, sy, sx + 1, sy, GOLD)
        c.rect(sx, sy - 1, sx, sy + 1, GOLD)
    # Кайма раструба: золото с тёмным узором, под ней тень подкладки.
    c.poly([(43, 60), (85, 60), (86, 67), (42, 67)], GOLD)
    c.rect(43, 60, 85, 60, WHITE)
    c.rect(42, 66, 86, 67, BRASS)
    for x in range(46, 84, 6):
        c.rect(x, 62, x + 2, 64, BRASS)
        c.set(x + 1, 63, RED)
    c.rect(49, 56, 79, 59, NAVY)
    # Кулак со спины ладони: запястье, четыре пальца обхватывают рукоять, большой сбоку.
    c.rect(53, 50, 75, 58, SKIN)
    c.ellipse(64, 47, 13, 8, SKIN)
    for k in range(4):
        x0 = 52 + k * 6
        c.rect(x0, 40, x0 + 5, 47, SKIN)
        c.rect(x0 + 1, 39, x0 + 4, 39, SKIN)
        if k:
            c.rect(x0 - 1 + 1, 41, x0, 49, BRASS)
        c.rect(x0 + 1, 44, x0 + 4, 44, BRASS)
    c.poly([(76, 44), (80, 46), (79, 54), (74, 56)], SKIN)
    c.rect(54, 53, 74, 53, BRASS)
    # Палочка: тёмная рукоять с навершием под кулаком не видна, выше золотое кольцо, резное
    # древко с витком, оправа-коготки и кристалл.
    c.rect(61, 30, 67, 40, DARK)
    c.rect(60, 34, 68, 37, GOLD)
    c.rect(60, 34, 68, 34, WHITE)
    c.rect(60, 37, 68, 37, BRASS)
    for y in range(14, 34):
        half = 2 if y > 22 else 1.5
        c.rect(64 - half, y, 64 + half, y, METAL)
    c.rect(62, 22, 62, 33, BRASS)
    c.rect(63, 14, 63, 22, BRASS)
    for y in range(16, 33, 4):
        c.line(62, y + 1, 66, y - 1, DARK, 1)
    c.poly([(59, 15), (69, 15), (67, 11), (61, 11)], GOLD)
    c.rect(58, 9, 59, 14, GOLD)
    c.rect(69, 9, 70, 14, GOLD)
    c.rect(59, 15, 69, 15, BRASS)
    # Кристалл: ромб с гранями.
    c.poly([(64, 0), (69, 6), (67, 12), (61, 12), (59, 6)], AQUA)
    c.poly([(64, 0), (69, 6), (67, 12), (64, 12), (64, 6)], SEA)
    c.poly([(64, 1), (60, 6), (64, 6)], SKY)
    c.line(61, 7, 62, 11, WHITE, 1)
    c.finish()
    # Искры у кристалла.
    for x, y in ((54, 4), (74, 3), (76, 12), (52, 13)):
        c.set(x, y, SKY)
    if frame:
        for k in range(10):
            a = k * math.tau / 10 + 0.2
            c.line(64, 3, 64 + math.cos(a) * 24, 3 + math.sin(a) * 15, RED, 2)
        c.ellipse(64, 2, 17, 10, RED)
        c.ellipse(64, 1, 13, 8, GOLD)
        c.ellipse(64, 0, 8, 5, WHITE)
    return c


def face(mode):
    """Лицо мага для HUD, 32×32: остроконечная шляпа с загнутым кончиком и золотой лентой,
    каштановые волосы; 0 прямо, 1 глянул влево, 2 вправо, 3 больно (шляпа набекрень, звёзды из
    глаз), 4 ухмылка."""
    c = Canvas(32, 32)
    tilt = 2 if mode == 3 else 0
    # Воротник мантии с застёжкой.
    c.poly([(7, 31), (10, 26), (22, 26), (25, 31)], SEA)
    c.rect(15, 28, 17, 30, GOLD)
    # Волосы и лицо.
    c.ellipse(16, 19, 9.5, 8.5, METAL)
    c.ellipse(16, 20, 7.8, 7.6, SKIN)
    c.rect(8, 13, 24, 15, METAL)
    c.rect(7, 16, 8, 23, METAL)
    c.rect(24, 16, 25, 23, METAL)
    # Шляпа: тулья клонится вправо, кончик загнут, поля шире лица.
    c.poly([(9, 12 + tilt), (23, 12 - tilt), (22, 3), (18, 1), (14, 4)], SEA)
    c.poly([(18, 1), (22, 3), (27, 2), (29, 5), (25, 5), (22, 5)], SEA)
    c.poly([(8, 9 + tilt), (24, 9 - tilt), (24, 11 - tilt), (8, 11 + tilt)], GOLD)
    c.poly([(1, 12 + tilt * 2), (30, 12 - tilt * 2), (29, 14 - tilt * 2), (2, 14 + tilt * 2)], SEA)
    c.set(16, 10, RED)
    c.finish()
    c.line(13, 5, 12, 8, NAVY, 1)
    look = {0: 0, 1: -1, 2: 1, 3: 0, 4: 0}[mode]
    for e in (-4, 4):
        ex = 16 + e
        if mode == 3:
            c.line(ex - 2, 18, ex + 1, 21, K, 1)
            c.line(ex - 2, 21, ex + 1, 18, K, 1)
        else:
            c.rect(ex - 2, 18, ex + 1, 21, WHITE)
            c.rect(ex - 1 + look, 19, ex + look, 21, K)
            c.rect(ex - 2, 17, ex + 1, 17, METAL)
            if mode == 4:
                c.rect(ex - 2, 21, ex + 1, 21, SKIN)
    c.rect(15, 22, 16, 23, BRASS)
    if mode == 4:
        c.rect(12, 25, 20, 26, WHITE)
        c.rect(12, 24, 20, 24, K)
        c.set(11, 24, K)
        c.set(21, 24, K)
        c.set(11, 23, K)
        c.set(21, 23, K)
    elif mode == 3:
        c.ellipse(16, 26, 2.6, 1.6, K)
        c.set(16, 26, RED)
        c.rect(8, 22, 10, 23, RED)
        c.set(28, 17, GOLD)
        c.set(27, 18, GOLD)
        c.set(29, 18, GOLD)
        c.set(28, 19, GOLD)
        c.set(3, 20, GOLD)
    else:
        c.rect(13, 25, 19, 25, K)
        c.set(12 if mode != 2 else 20, 24, K)
    # Румянец.
    if mode != 3:
        c.set(9, 23, RED)
        c.set(23, 23, RED)
    return c


def textures():
    return {"wall_planks": tex_panels(), "wall_stone": tex_growth(), "wall_pillar": tex_pillar(),
            "wall_exit": tex_exit(), "wall_cabin": tex_cabin(), "wall_hull": tex_hull(), "wall_cargo": tex_cargo(),
            "floor_planks": tex_floor(), "floor_stone": tex_floor_grate(), "floor_carpet": tex_floor_tiles(),
            "ceiling_beams": tex_ceiling()}


def sprites():
    out = {"shot": shot(), "bullet": bullet(), "key": key(), "medkit": medkit(),
           "hold_decor": strip([decor(k) for k in range(6)]),
           "pistol": strip([pistol(0), pistol(1)]),
           "face": strip([face(i) for i in range(5)])}
    out.update(alien_strips())
    out.update(textures())
    return out


if __name__ == "__main__":
    if "--preview" in sys.argv:
        scale_ = 3
        keys_ = None
        for arg in sys.argv:
            if arg.startswith("--scale="):
                scale_ = int(arg.split("=", 1)[1])
            if arg.startswith("--keys="):
                keys_ = arg.split("=", 1)[1].split(",")
        items_ = sprites()
        if keys_:
            items_ = {k: items_[k] for k in keys_ if k in items_}
        fantasy16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], fantasy16.shaded(items_), scale=scale_)
