#!/usr/bin/env python3
"""Набор «Замки» для шутера × 16/32-bit «до выхода» (#136), зеркало `space_hold16.py`, которое
само зеркалит `pixel_hold16.py`: те же ключи, размеры холстов, число и порядок кадров и точки
опоры (ноги врагов на 61-62 строке по центру кадра, ствол оружия вверх по оси 64, текстуры
64×64 со швом по краю). Меняется рисунок, не геометрия кадров. Палитра и светотень у основы
`castles16.py` (K обводка, NAVY хвоя, SEA зелень, AQUA трава, SKY блики, WHITE светлая сталь,
GREY тень стали, SKIN и TAN кожа и дерево, GOLD и BRASS золото, METAL камень, DARK чёрное железо,
RED герб и плюмаж, VIOLET и PLUM багрянец стражи).

Тема: двор и залы замка, взятого чужой стражей. Стены: кладка, увитая плющом стена с розами,
колонна с обручами, ворота-выход с гербовым знаменем, тронный зал с гобеленом и факелами, окно
с видом на холмы, склад с тюками сена. Полы: доски подъёмного моста, брусчатка с травой в
швах, красный ковёр. Враги: стражник вражеского замка с арбалетом (`skel_*`: чёрная кольчуга,
багровая туника, шлем-котелок) и наёмник с боевым молотом (`cut_*`: кожаный жилет, железная
шапка, борода). Арбалет в стальной перчатке, зажигательный болт врага, болт героя, железный
ключ, лекарская сумка, лицо рыцаря с плюмажем.

    python3 tools/castles_hold16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import castles16  # noqa: E402
from castles16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                       DARK, RED, VIOLET, PLUM)

T = 64


# --- Текстуры ----------------------------------------------------------------------------------

def _courses(c, rng, y_end, dark=False):
    """Кладка из тёсаных блоков 32×16, ряды сдвинуты на половину (период 32 делит 64): шов,
    светлая кромка сверху и слева, тень снизу и справа, редкие крапинки."""
    for y in range(y_end):
        row, py = divmod(y, 16)
        off = 16 if row % 2 else 0
        for x in range(T):
            px = (x + off) % 32
            if py == 0 or px == 0:
                col = DARK
            elif py == 1 or px == 1:
                col = GREY if dark else WHITE
            elif py == 15 or px == 31:
                col = DARK if dark else METAL
            else:
                col = METAL if dark else GREY
            c.set(x, y, col)
    for _ in range(40):
        x, y = rng.randrange(T), rng.randrange(y_end)
        if c.get(x, y) == (METAL if dark else GREY):
            c.set(x, y, DARK if dark else METAL)


def tex_blocks():
    """Основная стена: светлая кладка, под ней цоколь из крупных плит, на нижних рядах мох и
    трещины."""
    rng = random.Random(301)
    c = Canvas(T, T)
    _courses(c, rng, 56)
    for y in range(56, T):
        py = y - 56
        for x in range(T):
            col = METAL
            if py == 0 or x % 32 == 0:
                col = DARK
            elif py == 1:
                col = GREY
            elif py >= 6:
                col = DARK
            c.set(x, y, col)
    # Мох: пятна и свисающие пряди по нижним рядам.
    for _ in range(26):
        x, y = rng.randrange(T), rng.randrange(40, 56)
        if c.get(x, y) in (GREY, METAL):
            c.set(x, y, SEA)
            if rng.random() < 0.5 and c.get(x, y + 1) in (GREY, METAL):
                c.set(x, y + 1, NAVY)
            if rng.random() < 0.4:
                c.set(x + 1, y, AQUA)
    for x0, y0 in ((9, 6), (44, 22)):
        for k in range(6):
            c.set(x0 + (k % 2) + k // 3, y0 + k * 2, DARK)
            c.set(x0 + (k % 2) + k // 3, y0 + k * 2 + 1, DARK)
    return c


def tex_ivy():
    """Стена, увитая плющом: тёмная кладка, четыре вертикальные лозы (период 32 по высоте, шов
    замкнут), листья и алые розы."""
    rng = random.Random(302)
    c = Canvas(T, T)
    _courses(c, rng, T, dark=True)
    for i, x0 in enumerate((6, 22, 40, 55)):
        ph = rng.random() * math.tau
        for y in range(T):
            x = x0 + 2.5 * math.sin(y * math.tau / 32.0 + ph)
            c.set(x, y, SEA)
            c.set(x + 1, y, NAVY)
            if (y + i * 3) % 6 == 0:
                side = 1 if (y // 6 + i) % 2 else -1
                c.ellipse(x + side * 3, y, 2.2, 1.4, AQUA)
                c.ellipse(x + side * 3.5, y + 0.5, 1.2, 0.8, SEA)
            if (y + i * 3 + 3) % 6 == 0:
                c.ellipse(x - 2 * (1 if (y // 6 + i) % 2 else -1), y, 1.6, 1.1, SEA)
    for x, y in ((12, 14), (30, 40), (47, 9), (58, 47), (18, 56)):
        c.ellipse(x, y, 2.2, 2.2, RED)
        c.set(x, y, PLUM)
        c.set(x - 1, y - 1, GOLD if (x + y) % 2 else RED)
        c.set(x + 1, y + 2, NAVY)
    return c


def tex_columns():
    """Колонна: каннелюры шириной 16 с бликом и тенью, два каменных обруча с золотыми болтами."""
    c = Canvas(T, T)
    flute = [DARK, METAL, GREY, WHITE, WHITE, GREY, GREY, GREY, GREY, METAL, METAL, METAL, METAL, DARK, DARK, DARK]
    for x in range(T):
        c.rect(x, 0, x, T - 1, flute[x % 16])
    for y0 in (10, 46):
        c.rect(0, y0, T - 1, y0, DARK)
        c.rect(0, y0 + 1, T - 1, y0 + 1, WHITE)
        c.rect(0, y0 + 2, T - 1, y0 + 4, GREY)
        c.rect(0, y0 + 5, T - 1, y0 + 5, METAL)
        c.rect(0, y0 + 6, T - 1, y0 + 6, DARK)
        for x in range(8, T, 16):
            c.rect(x - 1, y0 + 2, x, y0 + 3, GOLD)
            c.set(x - 1, y0 + 3, BRASS)
            c.set(x, y0 + 3, BRASS)
    for x, y in ((6, 26), (7, 27), (8, 28), (41, 30), (42, 31)):
        c.set(x, y, DARK)
    return c


def tex_gate():
    """Ворота-выход: каменная рама из блоков, под гербовым знаменем двустворчатые дубовые
    двери с железными полосами, кольцами и золотым замком посередине."""
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, DARK)
    # Рама: блоки по 8 пикселей в высоту, светлая кромка снаружи.
    for y in range(T):
        for x in range(T):
            if x < 6 or x > 57 or y > 59 or y < 12:
                col = GREY
                if (x < 6 or x > 57) and y % 8 == 0:
                    col = DARK
                elif y > 59 and x % 16 == 0:
                    col = DARK
                elif y < 12 and (x + (y // 6) * 8) % 16 == 0:
                    col = DARK
                elif x in (0, 6) and 12 <= y <= 59 or y == 0:
                    col = WHITE
                elif x in (5, 57) or y == 59:
                    col = METAL
                c.set(x, y, col)
    # Створки: вертикальные доски по 4 пикселя, шов между створками.
    for y in range(12, 60):
        for x in range(6, 58):
            px = (x - 6) % 4
            col = (DARK, SKIN, TAN, TAN)[px]
            if px == 3 and (x + y) % 5 == 0:
                col = BRASS
            c.set(x, y, col)
    c.rect(31, 12, 32, 59, K)
    c.rect(30, 12, 30, 59, DARK)
    c.rect(33, 12, 33, 59, DARK)
    # Дверь с закруглёнными верхними углами.
    for y in range(12, 18):
        inset = (5, 3, 2, 1, 1, 0)[y - 12]
        for x in range(6, 6 + inset):
            c.set(x, y, GREY)
            c.set(63 - x, y, GREY)
    # Железные полосы с заклёпками.
    for y0 in (19, 47):
        c.rect(6, y0, 57, y0 + 3, DARK)
        c.rect(6, y0, 57, y0, METAL)
        c.rect(30, y0, 33, y0 + 3, K)
        for x in range(10, 56, 8):
            if x not in (30, 31, 32, 33):
                c.rect(x, y0 + 1, x + 1, y0 + 2, WHITE)
    # Кольца и замок.
    for x in (24, 39):
        c.ellipse(x, 38, 3, 3, METAL)
        c.ellipse(x, 38, 1.6, 1.6, TAN)
    c.rect(28, 30, 35, 41, BRASS)
    c.rect(29, 31, 34, 40, GOLD)
    c.rect(29, 31, 34, 31, WHITE)
    c.rect(31, 34, 32, 38, DARK)
    c.rect(30, 34, 33, 35, DARK)
    # Знамя над дверью: красное полотно, золотая корона, зубчатый низ.
    c.rect(14, 3, 49, 11, K)
    c.rect(15, 4, 48, 10, RED)
    c.rect(15, 4, 48, 4, GOLD)
    for x in range(15, 49, 4):
        c.rect(x, 10, x + 1, 10, PLUM)
    c.rect(27, 7, 36, 9, GOLD)
    for x in (27, 30, 33, 36):
        c.rect(x - (1 if x == 36 else 0), 5, x, 6, GOLD)
    c.rect(28, 8, 35, 8, BRASS)
    c.set(31, 6, RED)
    c.set(32, 6, RED)
    return c


def tex_hall():
    """Тронный зал: кладка, красный гобелен с золотой короной и мечом на карнизе, факелы по
    краям, внизу дубовая панель с рейкой."""
    c = tex_blocks()
    c.rect(0, 40, T - 1, T - 1, TAN)
    for x in range(T):
        col = DARK if x % 8 == 0 else (SKIN if x % 8 == 1 else TAN)
        c.rect(x, 44, x, 61, col)
    c.rect(0, 40, T - 1, 40, DARK)
    c.rect(0, 41, T - 1, 41, SKIN)
    c.rect(0, 42, T - 1, 42, TAN)
    c.rect(0, 43, T - 1, 43, DARK)
    c.rect(0, 62, T - 1, T - 1, DARK)
    for x in range(4, T, 8):
        c.set(x, 47, BRASS)
        c.set(x, 58, BRASS)
    # Гобелен на карнизе.
    c.rect(12, 3, 51, 4, DARK)
    c.rect(12, 3, 51, 3, BRASS)
    c.rect(10, 2, 11, 5, GOLD)
    c.rect(52, 2, 53, 5, GOLD)
    c.rect(16, 5, 47, 28, PLUM)
    c.rect(17, 6, 46, 27, RED)
    c.rect(17, 6, 46, 6, GOLD)
    c.rect(17, 6, 17, 27, GOLD)
    c.rect(46, 6, 46, 27, GOLD)
    c.rect(18, 26, 45, 26, GOLD)
    for x in range(17, 47, 2):
        c.set(x, 28, GOLD)
    # Корона и меч.
    c.rect(27, 10, 36, 13, GOLD)
    for x in (27, 30, 33, 36):
        c.rect(x - (1 if x == 36 else 0), 8, x, 9, GOLD)
    c.rect(27, 13, 36, 13, BRASS)
    c.set(31, 11, RED)
    c.set(32, 11, RED)
    c.rect(31, 15, 32, 24, WHITE)
    c.rect(32, 15, 32, 24, GREY)
    c.rect(28, 21, 35, 22, GOLD)
    c.rect(31, 23, 32, 25, BRASS)
    # Факелы.
    for x in (5, 58):
        c.rect(x - 1, 24, x + 1, 30, DARK)
        c.rect(x, 23, x, 30, TAN)
        c.ellipse(x, 18, 2.6, 4.5, RED)
        c.ellipse(x, 19, 1.5, 3, GOLD)
        c.set(x, 20, WHITE)
    return c


def tex_window():
    """Окно в кладке: стрельчатая арка с каменной рамой, за решёткой холмы, башня с флажком и
    облако."""
    c = tex_blocks()

    def inside(x, y, half, bot):
        if y >= 24:
            return abs(x - 31.5) <= half and y <= bot
        return (x - 31.5) ** 2 + (y - 24) ** 2 <= half ** 2

    for half, col, bot in ((14, DARK, 49), (13, METAL, 48), (12, GREY, 48), (10.5, SKY, 47)):
        for y in range(8, 56):
            for x in range(T):
                if inside(x, y, half, bot):
                    c.set(x, y, col)
    # Блик рамы по левому краю.
    for y in range(24, 48):
        c.set(20, y, WHITE)
    for y in range(8, 56):
        for x in range(T):
            if not inside(x, y, 10.5, 47) or c.get(x, y) != SKY:
                continue
            if y >= 37 + int(2.5 * math.sin(x * 0.35)):
                c.set(x, y, NAVY)
            if y >= 41 + int(2 * math.sin(x * 0.28 + 1)):
                c.set(x, y, SEA)
            if y >= 45:
                c.set(x, y, AQUA)
    # Башня на дальнем холме.
    for y in range(31, 40):
        for x in range(34, 39):
            if inside(x, y, 10.5, 47):
                c.set(x, y, METAL if x != 34 else GREY)
    for x in (34, 36, 38):
        c.set(x, 30, METAL)
    c.rect(36, 26, 36, 29, DARK)
    c.rect(37, 26, 38, 27, RED)
    # Облако.
    for x, y in ((24, 18), (25, 18), (26, 18), (25, 17), (28, 20), (29, 20), (30, 20)):
        c.set(x, y, WHITE)
    # Решётка: две стойки и прут.
    for x in (27, 36):
        c.rect(x, 16, x, 47, DARK)
    c.rect(18, 31, 45, 31, DARK)
    # Подоконник.
    c.rect(15, 50, 48, 53, GREY)
    c.rect(15, 50, 48, 50, WHITE)
    c.rect(15, 53, 48, 53, DARK)
    return c


def tex_hay():
    """Склад: стопка тюков сена 32×32 со сдвигом второго ряда, соломенная штриховка, две
    бечёвки и красная печать на каждом."""
    rng = random.Random(307)
    c = Canvas(T, T)
    for by in (0, 32):
        off = 16 if by == 32 else 0
        for bx in (0, 32):
            x0 = (bx + off) % T
            body, hi, stroke = (GOLD, SKIN, BRASS) if (bx // 32 + by // 32) % 2 == 0 else (GOLD, SKIN, TAN)
            for ly in range(32):
                for x in range(32):
                    edge = x in (0, 31) or ly in (0, 31)
                    col = DARK if edge else (hi if ly == 1 else body)
                    c.set((x0 + x) % T, by + ly, col)
            for _ in range(60):
                px, py = rng.randint(2, 29), rng.randint(3, 26)
                for k in range(rng.randint(2, 4)):
                    c.set((x0 + px) % T, by + py + k, stroke)
            for _ in range(24):
                px, py = rng.randint(2, 29), rng.randint(3, 27)
                c.set((x0 + px) % T, by + py, hi)
            for x in (9, 10, 21, 22):
                for ly in range(1, 31):
                    c.set((x0 + x) % T, by + ly, DARK)
                c.set((x0 + x) % T, by + 2, METAL if x in (9, 21) else DARK)
            c.rect(x0 + 14 if x0 + 14 < T else x0 + 14 - T, by + 14, x0 + 17 if x0 + 17 < T else x0 + 17 - T, by + 17, RED)
            c.set((x0 + 14) % T, by + 14, PLUM)
    return c


def tex_bridge():
    """Доски подъёмного моста: полосы по 8 пикселей, швы торцов у каждой на своей высоте (период
    32), гвозди, волокна."""
    rng = random.Random(308)
    c = Canvas(T, T)
    for x in range(T):
        pl, px = divmod(x, 8)
        for y in range(T):
            ys = (y + 13 * pl) % 32
            col = TAN
            if px == 0 or ys == 0:
                col = DARK
            elif px == 1 or ys == 1:
                col = SKIN if px == 1 and ys != 1 else BRASS
            elif px == 7:
                col = BRASS
            c.set(x, y, col)
    for _ in range(90):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == TAN and c.get(x, (y + 1) % T) == TAN:
            c.set(x, y, BRASS)
            c.set(x, (y + 1) % T, BRASS)
    for pl in range(8):
        for ny in (4, 20):
            y = (ny - 13 * pl) % 32
            for yy in (y, y + 32):
                c.set(pl * 8 + 3, yy, METAL)
                c.set(pl * 8 + 4, yy, DARK)
    return c


def tex_cobble():
    """Брусчатка: булыжники 16×16 со сдвигом рядов, закруглённые углы, на швах пробивается
    трава."""
    rng = random.Random(309)
    c = Canvas(T, T)
    for y in range(T):
        row, py = divmod(y, 16)
        off = 8 if row % 2 else 0
        for x in range(T):
            px = (x + off) % 16
            cell = ((x + off) // 16 * 7 + row * 3) % 5
            base = METAL if cell == 2 else GREY
            col = base
            corner = (px in (0, 15) and py in (0, 15)) or (px in (1, 14) and py in (1, 14) and False)
            if px == 0 or py == 0 or corner:
                col = DARK
            elif px == 1 or py == 1:
                col = WHITE if base == GREY else GREY
            elif px == 15 or py == 15:
                col = METAL if base == GREY else DARK
            elif (px, py) in ((2, 2), (13, 2), (2, 14), (14, 14)):
                col = DARK
            c.set(x, y, col)
    for _ in range(26):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == DARK:
            c.set(x, y, SEA if rng.random() < 0.6 else AQUA)
            if rng.random() < 0.5:
                c.set(x, (y - 1) % T, AQUA)
    return c


def tex_carpet():
    """Ковёр: красное поле, золотая кайма и ромбы в клетках 32×32, багровые крапинки."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 32, y % 32
            d = abs(px - 16) + abs(py - 16)
            col = RED
            if px in (0, 31) or py in (0, 31):
                col = GOLD
            elif px in (1, 30) or py in (1, 30):
                col = PLUM
            elif d == 11:
                col = GOLD
            elif d == 10:
                col = PLUM
            elif d <= 2:
                col = GOLD
            elif d == 6:
                col = BRASS
            elif (px + py) % 4 == 0 and d > 11:
                col = VIOLET
            c.set(x, y, col)
    return c


def tex_rafters():
    """Потолок: тёмные доски со швами, через 32 пикселя балка с бликом, на балках лампады-точки
    (без ярких полос, иначе в перспективе они расходятся лучами)."""
    rng = random.Random(311)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = DARK
            if x % 16 == 0:
                col = K
            if y % 32 < 6:
                col = (K, BRASS, TAN, TAN, DARK, K)[y % 32]
            c.set(x, y, col)
    for _ in range(26):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == DARK:
            c.set(x, y, K)
    for y in (2, 34):
        for x in (8, 40):
            c.rect(x, y, x + 1, y + 1, GOLD)
    return c


# --- Люди --------------------------------------------------------------------------------------

def _mail(c, x0, y0, x1, y1):
    """Кольчуга: на тёмном железе шахматка из звеньев."""
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            if (x + y) % 2 == 0 and c.get(x, y) == DARK:
                c.set(x, y, METAL)


def _head(c, hx, hy, side, back, diag, brute, mode):
    """Голова. `hy` центр шлема. Стражник: шлем-котелок с полями и носовым выступом, бритое
    лицо. Наёмник: железная шапка с красной повязкой и рыжая борода."""
    face_y = hy + 4
    # Шея и лицо.
    c.rect(hx - 2, hy + 7, hx + 2, hy + 10, TAN)
    if back:
        pass
    elif side:
        c.ellipse(hx + 1, face_y, 4.2, 5, SKIN)
        c.set(hx + 5, face_y, SKIN)
        c.set(hx + 5, face_y + 1, SKIN)
    else:
        c.ellipse(hx + (1 if diag else 0), face_y, 4.6, 5, SKIN)
    if brute and not back:
        # Борода: нижняя половина лица и подбородок.
        if side:
            c.ellipse(hx + 1.5, face_y + 3, 4, 3, DARK)
            c.rect(hx + 3, face_y + 1, hx + 5, face_y + 2, DARK)
        else:
            c.ellipse(hx + (1 if diag else 0), face_y + 3, 4.8, 3.2, DARK)
            c.rect(hx - 1 + (1 if diag else 0), face_y + 2, hx + 1 + (1 if diag else 0), face_y + 2, SKIN)
    # Глаза, нос.
    if not back:
        if side:
            ey = face_y - 1
            if mode == "hurt":
                c.line(hx + 3, ey - 1, hx + 5, ey + 1, K, 1)
            else:
                c.rect(hx + 3, ey, hx + 4, ey, K)
                c.set(hx + 4, ey - 1, K)
            c.set(hx + 6, face_y, TAN)
            c.set(hx + 5, face_y + 1, TAN)
        else:
            sh = 1 if diag else 0
            for e in (-2, 2):
                if mode == "hurt":
                    c.line(hx + e - 1 + sh, face_y - 2, hx + e + 1 + sh, face_y, K, 1)
                else:
                    c.rect(hx + e + sh, face_y - 1, hx + e + sh, face_y, K)
            c.rect(hx + sh, face_y, hx + sh, face_y + 1, TAN)
            if not brute:
                c.rect(hx - 1 + sh, face_y + 3, hx + 1 + sh, face_y + 3, TAN)
    # Головной убор.
    if brute:
        c.ellipse(hx, hy - 1, 5.6, 4.2, METAL)
        c.rect(hx - 5, hy, hx + 5, hy + 1, RED)
        c.rect(hx - 5, hy + 1, hx + 5, hy + 1, PLUM)
        c.rect(hx - 3, hy - 4, hx, hy - 4, GREY)
        c.set(hx - 4, hy - 2, GREY)
        if side:
            c.rect(hx - 6, hy + 3, hx - 4, hy + 7, PLUM)
        elif back:
            c.rect(hx - 5, hy + 4, hx + 5, hy + 6, TAN)
    else:
        c.ellipse(hx, hy - 0.5, 5.4, 4.6, GREY)
        c.rect(hx - 4, hy - 2, hx - 2, hy - 2, WHITE)
        c.set(hx - 3, hy - 3, WHITE)
        c.set(hx - 4, hy - 1, WHITE)
        c.line(hx - 5, hy + 1, hx + 5, hy + 1, METAL, 1)
        if side:
            c.ellipse(hx - 0.5, hy + 2, 8.2, 1.7, METAL)
            c.rect(hx + 2, hy + 3, hx + 7, hy + 3, METAL)
            c.rect(hx + 2, hy + 2, hx + 6, hy + 2, GREY)
            c.rect(hx + 5, hy + 3, hx + 5, hy + 6, GREY)
        else:
            c.ellipse(hx, hy + 2, 8.6, 1.7, METAL)
            c.rect(hx - 7, hy + 2, hx + 7, hy + 2, GREY)
        if not back and not side:
            # Носовая пластина и ремешок под подбородок.
            c.rect(hx + (1 if diag else 0), hy + 3, hx + (1 if diag else 0), hy + 6, GREY)
            c.rect(hx - 4, hy + 5, hx - 4, hy + 9, DARK)
            c.rect(hx + 4, hy + 5, hx + 4, hy + 9, DARK)
        elif back:
            c.rect(hx - 4, hy + 4, hx + 4, hy + 6, DARK)
            _mail(c, hx - 4, hy + 4, hx + 4, hy + 6)


def man(angle, phase, mode="walk", brute=False):
    """Страж 64×64 в ракурсе `angle` (0 спереди … 4 со спины, лицом вправо на 1-3), шаг `phase`
    0/1. `mode`: walk, aim, fire, slash, die0..die2, hurt. `brute` наёмник: боевой молот вместо
    арбалета. Ступни на 61-62 строке, ось по центру кадра, как у пришельца космоса."""
    c = Canvas(T, T)
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    if mode.startswith("die"):
        return _fallen(int(mode[-1]), brute)
    bob = 1 if phase else 0
    leg_a, leg_b = (DARK, METAL) if brute else (PLUM, VIOLET)
    # Ноги: штаны, колено, сапог с носком вперёд.
    for sign in (-1, 1):
        swing = (sign * 3 if phase else -sign * 3) if mode == "walk" else 0
        col = leg_a if sign < 0 else leg_b
        hip = (cx + sign * (1 if side else 3), 38 - bob)
        foot = (cx + sign * (1 if side else 4) + swing * (1 if side else 0.3), 59)
        knee = ((hip[0] + foot[0]) / 2 + (1 if side else sign * 0.6), 49)
        c.line(hip[0], hip[1], knee[0], knee[1], col, 5)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 4)
        c.rect(foot[0] - 2, 56, foot[0] + 1, 58, DARK)
        c.rect(foot[0] - (2 if not side else 1), 59, foot[0] + (3 if side else 2) + (1 if not side else 0), 62, DARK)
        c.rect(foot[0] - (2 if not side else 1), 59, foot[0] + (3 if side else 2) + (1 if not side else 0), 59, METAL)
    # Корпус.
    w = (6 if side else (8 if diag else 9)) if brute else (5 if side else (7 if diag else 8))
    top = 17 - bob
    if brute:
        c.poly([(cx - w, top), (cx + w, top), (cx + w - 1, 40 - bob), (cx - w + 1, 40 - bob)], TAN)
        if not back:
            c.line(cx - w + 1, top + 1, cx + w - 2, 36 - bob, DARK, 1)
            c.line(cx + w - 1, top + 1, cx - w + 2, 36 - bob, DARK, 1)
            if not side:
                c.rect(cx - 2, top, cx + 2, top + 3, SKIN)
        else:
            c.rect(cx - w + 2, top + 4, cx + w - 2, top + 15, SKIN)
            c.rect(cx - w + 2, top + 4, cx - w + 2, top + 15, DARK)
            c.rect(cx - w + 1, top, cx + w - 1, top + 3, RED)
            c.rect(cx - w + 1, top + 3, cx + w - 1, top + 3, PLUM)
            c.rect(cx - 1, top + 4, cx, top + 15, DARK)
        c.rect(cx - w, 38 - bob, cx + w, 40 - bob, DARK)
        c.rect(cx - 1 + (2 if side or diag else 0), 38 - bob, cx + 1 + (2 if side or diag else 0), 40 - bob, GOLD)
        c.rect(cx - w + 1, 41 - bob, cx + w - 1, 43 - bob, DARK)
        for x in range(cx - w + 1, cx + w):
            c.set(x, 43 - bob, TAN if x % 2 else DARK)
    else:
        c.poly([(cx - w, top), (cx + w, top), (cx + w - 1, 40 - bob), (cx - w + 1, 40 - bob)], VIOLET)
        c.rect(cx - w, top, cx + w, top + 5, DARK)
        _mail(c, cx - w, top, cx + w, top + 5)
        if not back:
            c.rect(cx - 1 + (2 if side or diag else 0), top + 8, cx + 1 + (2 if side or diag else 0), top + 10, GOLD)
            c.set(cx + (2 if side or diag else 0), top + 9, RED)
        else:
            # Колчан с болтами за спиной.
            c.rect(cx - 3, top + 4, cx + 3, top + 15, TAN)
            c.rect(cx - 3, top + 4, cx + 3, top + 5, DARK)
            for x in (cx - 2, cx, cx + 2):
                c.rect(x, top + 1, x, top + 4, WHITE)
        c.rect(cx - w, 36 - bob, cx + w, 37 - bob, DARK)
        c.set(cx + (2 if side or diag else 0), 36 - bob, GOLD)
        c.poly([(cx - w + 1, 38 - bob), (cx + w - 1, 38 - bob), (cx + w + 1, 44 - bob), (cx - w - 1, 44 - bob)], VIOLET)
        c.rect(cx - w - 1, 44 - bob, cx + w + 1, 44 - bob, PLUM)
        if side or diag:
            c.rect(cx - w, 40 - bob, cx - w, 43 - bob, PLUM)
    # Руки и оружие.
    sleeve = SKIN if brute else DARK
    hand = SKIN
    if brute:
        up = mode == "slash"
        hx_ = cx + (9 if side or diag else 9)
        hy_ = (26 if not up else 14) - bob
        c.line(cx + w - 2, top + 3, hx_, hy_, sleeve, 5)
        c.ellipse(hx_, hy_, 2.4, 2.4, hand)
        tip = (hx_ + (9 if side or diag else 8), (13 if not up else 6) - bob)
        tail = (hx_ - (4 if side or diag else 2), hy_ + 8)
        c.line(tail[0], tail[1], tip[0], tip[1], TAN, 3)
        # Головка молота: боёк и клюв.
        c.rect(tip[0] - 5, tip[1] - 3, tip[0] + 5, tip[1] + 3, METAL)
        c.rect(tip[0] - 5, tip[1] - 3, tip[0] + 5, tip[1] - 3, WHITE)
        c.rect(tip[0] - 5, tip[1] + 3, tip[0] + 5, tip[1] + 3, DARK)
        c.rect(tip[0] - 5, tip[1] - 3, tip[0] - 5, tip[1] + 3, DARK)
        c.rect(tip[0] + 5, tip[1] - 3, tip[0] + 5, tip[1] + 3, DARK)
        c.poly([(tip[0] - 5, tip[1] - 1), (tip[0] - 9, tip[1]), (tip[0] - 5, tip[1] + 1)], METAL)
        c.rect(tip[0] - 1, tip[1] - 3, tip[0], tip[1] + 3, GREY)
        c.line(cx - w + 1, top + 4, cx - w - 1, 33 - bob, sleeve, 4)
        c.ellipse(cx - w - 1, 34 - bob, 2.2, 2.2, hand)
    elif mode in ("aim", "fire") or not back:
        if side or diag:
            c.line(cx + 2, top + 5, cx + 11, 27 - bob, sleeve, 4)
            _mail(c, cx, top + 3, cx + 12, 29 - bob)
            # Арбалет: ложе, дуга впереди, тетива.
            c.rect(cx + 4, 26 - bob, cx + 23, 28 - bob, TAN)
            c.rect(cx + 4, 26 - bob, cx + 23, 26 - bob, SKIN)
            c.rect(cx + 3, 28 - bob, cx + 7, 31 - bob, DARK)
            c.line(cx + 22, 18 - bob, cx + 25, 27 - bob, METAL, 2)
            c.line(cx + 25, 27 - bob, cx + 22, 36 - bob, METAL, 2)
            c.set(cx + 22, 18 - bob, WHITE)
            if mode == "fire":
                c.line(cx + 22, 18 - bob, cx + 22, 36 - bob, WHITE, 1)
            else:
                c.line(cx + 22, 18 - bob, cx + 13, 27 - bob, WHITE, 1)
                c.line(cx + 13, 27 - bob, cx + 22, 36 - bob, WHITE, 1)
                c.rect(cx + 12, 25 - bob, cx + 27, 25 - bob, WHITE)
                c.rect(cx + 28, 24 - bob, cx + 29, 26 - bob, GREY)
            c.ellipse(cx + 11, 28 - bob, 2, 2, hand)
        else:
            c.line(cx - w, top + 3, cx - 5, 31 - bob, sleeve, 4)
            c.line(cx + w, top + 3, cx + 4, 31 - bob, sleeve, 4)
            if mode in ("aim", "fire"):
                # Арбалет смотрит в камеру: дуга поперёк, ложе короткой полосой, наконечник болта.
                c.line(cx - 11, 26 - bob, cx - 4, 30 - bob, METAL, 2)
                c.line(cx - 4, 30 - bob, cx + 4, 30 - bob, METAL, 2)
                c.line(cx + 4, 30 - bob, cx + 11, 26 - bob, METAL, 2)
                c.rect(cx - 2, 29 - bob, cx + 2, 35 - bob, TAN)
                c.rect(cx - 2, 29 - bob, cx - 2, 35 - bob, SKIN)
                if mode == "fire":
                    c.line(cx - 11, 26 - bob, cx + 11, 26 - bob, WHITE, 1)
                else:
                    c.line(cx - 11, 26 - bob, cx, 33 - bob, WHITE, 1)
                    c.line(cx, 33 - bob, cx + 11, 26 - bob, WHITE, 1)
                    c.rect(cx - 1, 27 - bob, cx + 1, 30 - bob, WHITE)
                    c.rect(cx, 26 - bob, cx, 26 - bob, GREY)
                c.ellipse(cx - 5, 32 - bob, 2, 2, hand)
                c.ellipse(cx + 4, 32 - bob, 2, 2, hand)
            else:
                # Несёт арбалет наискосок.
                c.line(cx - 9, 36 - bob, cx + 10, 24 - bob, TAN, 3)
                c.line(cx + 6, 20 - bob, cx + 13, 28 - bob, METAL, 2)
                c.ellipse(cx - 5, 33 - bob, 2, 2, hand)
    else:
        c.line(cx - w, top + 3, cx - w - 1, 31 - bob, sleeve, 4)
        c.line(cx + w, top + 3, cx + w + 1, 31 - bob, sleeve, 4)
        _mail(c, cx - w - 2, top + 3, cx + w + 2, 31 - bob)
        c.line(cx - 9, 37 - bob, cx + 10, 25 - bob, TAN, 3)
        c.line(cx + 6, 21 - bob, cx + 13, 29 - bob, METAL, 2)
    _head(c, cx + (2 if side else (1 if diag else 0)), 8 - bob, side, back, diag, brute, mode)
    c.finish()
    if mode == "fire":
        fx, fy = (cx + 31, 26 - bob) if side or diag else (cx, 30 - bob)
        c.ellipse(fx, fy, 5, 4, GOLD)
        c.ellipse(fx, fy, 2.5, 2, WHITE)
        if not (side or diag):
            c.set(fx - 6, fy - 1, GOLD)
            c.set(fx + 6, fy - 1, GOLD)
    if mode == "hurt":
        for x in range(T):
            for y in range(T):
                if c.get(x, y) in (VIOLET, PLUM, TAN, SKIN, METAL, GREY) and (x + y) % 3 == 0:
                    c.set(x, y, WHITE)
    return c


def _fallen(k, brute):
    """Падение: k=1 оседает на колени, k=2 лежит лицом вверх, рядом выпавшее оружие."""
    if k == 0:
        return man(0, 0, "hurt", brute)
    c = Canvas(T, T)
    cx = 32
    base = 62
    tunic = TAN if brute else VIOLET
    hose = DARK if brute else PLUM
    if k == 1:
        # На коленях: бёдра на земле, корпус валится вперёд, руки плетьми.
        c.rect(cx - 12, base - 6, cx + 4, base - 2, hose)
        c.rect(cx - 15, base - 3, cx - 8, base, DARK)
        c.rect(cx - 2, base - 3, cx + 6, base, DARK)
        c.poly([(cx - 8, base - 8), (cx + 6, base - 8), (cx + 12, base - 25), (cx - 2, base - 27)], tunic)
        if not brute:
            c.rect(cx - 2, base - 27, cx + 12, base - 22, DARK)
            _mail(c, cx - 2, base - 27, cx + 12, base - 22)
        c.rect(cx - 8, base - 12, cx + 7, base - 10, DARK)
        c.line(cx + 9, base - 22, cx + 14, base - 8, DARK if not brute else TAN, 4)
        c.ellipse(cx + 14, base - 6, 2.2, 2.2, SKIN)
        hx, hy = cx + 12, base - 31
        c.ellipse(hx, hy + 3, 4.5, 5, SKIN)
        if brute:
            c.ellipse(hx + 1, hy + 6, 4.4, 3, TAN)
            c.ellipse(hx, hy, 5.6, 4.6, METAL)
            c.rect(hx - 5, hy + 1, hx + 5, hy + 2, RED)
        else:
            c.ellipse(hx, hy, 5.4, 4.4, GREY)
            c.ellipse(hx + 1, hy + 2, 8.4, 1.6, METAL)
        c.line(hx - 1, hy + 4, hx + 2, hy + 4, K, 1)
        c.line(hx + 2, hy + 4, hx + 4, hy + 5, K, 1)
        c.set(hx + 2, hy + 6, K)
        wx = cx - 22
    else:
        c.ellipse(cx, base, 26, 2.2, PLUM)
        c.rect(cx - 27, base - 5, cx - 11, base - 1, hose)
        c.rect(cx - 31, base - 4, cx - 25, base, DARK)
        c.poly([(cx - 12, base - 10), (cx + 8, base - 10), (cx + 9, base - 1), (cx - 12, base - 1)], tunic)
        if not brute:
            c.rect(cx + 3, base - 10, cx + 9, base - 1, DARK)
            _mail(c, cx + 3, base - 10, cx + 9, base - 1)
        c.rect(cx - 12, base - 6, cx - 8, base - 3, DARK)
        c.line(cx - 2, base - 9, cx + 10, base - 1, DARK if not brute else TAN, 3)
        hx, hy = cx + 16, base - 5
        c.ellipse(hx, hy, 6, 5, SKIN)
        if brute:
            c.ellipse(hx + 2, hy + 1, 4, 3.4, TAN)
            c.ellipse(hx - 1, hy - 1, 5, 4, METAL)
            c.rect(hx - 4, hy, hx + 1, hy + 1, RED)
        else:
            c.ellipse(hx - 1, hy - 1, 5, 4, GREY)
            c.rect(hx + 3, hy - 5, hx + 9, hy - 4, METAL)
        c.line(hx + 1, hy, hx + 4, hy, K, 1)
        c.set(hx + 3, hy + 2, K)
        wx = cx - 26
    # Выпавшее оружие.
    if brute:
        c.line(wx, base - 2, wx + 22, base - 5, TAN, 2)
        c.rect(wx - 3, base - 8, wx + 1, base - 2, METAL)
        c.rect(wx - 3, base - 8, wx + 1, base - 8, WHITE)
    else:
        c.rect(wx, base - 3, wx + 12, base - 2, TAN)
        c.line(wx + 1, base - 9, wx + 4, base - 2, METAL, 2)
        c.line(wx + 4, base - 2, wx + 1, base + 0, METAL, 2)
    return c.finish()


def man_strips():
    out = {}
    for name, brute in (("skel", False), ("cut", True)):
        walk = []
        for a in range(5):
            for ph in range(2):
                walk.append(man(a, ph, "walk", brute))
        out[name + "_walk"] = strip(walk)
        out[name + "_die"] = strip([man(0, 0, "die%d" % k, brute) for k in range(3)])
    out["skel_fire"] = strip([man(0, 0, "aim"), man(0, 0, "fire")])
    out["cut_slash"] = strip([man(0, 0, "walk", True), man(0, 0, "slash", True)])
    return out


# --- Предметы, оружие, лицо --------------------------------------------------------------------

def shot():
    """Выстрел стража: зажигательный болт летит в лицо, пламя с тёмным железным остриём
    посередине; красно-золотой, чтобы не путать с болтом героя."""
    c = Canvas(16, 16)
    c.ellipse(8, 8, 6, 6, RED)
    c.ellipse(8, 8, 4.5, 4.5, GOLD)
    c.ellipse(8, 8.5, 2.2, 2.2, DARK)
    c.set(6, 6, WHITE)
    c.set(5, 7, WHITE)
    for x, y in ((8, 1), (3, 3), (13, 4)):
        c.set(x, y, RED)
    return c


def bullet():
    """Болт героя: стальное остриё, древко и красное оперение, хвост вниз."""
    c = Canvas(16, 16)
    c.poly([(8, 1), (11, 6), (5, 6)], WHITE)
    c.poly([(8, 1), (11, 6), (8, 6)], GREY)
    c.rect(7, 6, 8, 12, TAN)
    c.poly([(8, 10), (4, 15), (8, 13), (12, 15)], RED)
    c.finish()
    c.set(7, 3, SKY)
    c.set(7, 4, SKY)
    return c


def decor(kind):
    """Ориентир зала 64×64, низ на 62-63 строке: 0 стойка с копьями, 1 тюки сена и мешок, 2 факел
    на подставке, 3 баллиста, 4 окованный ларь, 5 колокол на раме."""
    c = Canvas(T, T)
    if kind == 0:
        # Стойка: две перекладины, пять копий с наконечниками, два вымпела.
        c.rect(6, 56, 58, 59, TAN)
        c.rect(6, 56, 58, 56, SKIN)
        c.rect(6, 39, 58, 42, TAN)
        c.rect(6, 39, 58, 39, SKIN)
        c.rect(8, 59, 13, 62, DARK)
        c.rect(50, 59, 55, 62, DARK)
        for i, x in enumerate((12, 22, 32, 42, 52)):
            c.rect(x - 1, 14, x, 60, TAN)
            c.rect(x - 1, 14, x - 1, 60, SKIN)
            c.poly([(x - 3, 15), (x - 0.5, 3), (x + 2, 15)], WHITE)
            c.poly([(x - 0.5, 3), (x + 2, 15), (x - 0.5, 15)], GREY)
            c.rect(x - 3, 15, x + 2, 16, METAL)
            if i in (1, 3):
                c.poly([(x + 1, 19), (x + 9, 22), (x + 1, 26)], RED)
                c.rect(x + 1, 22, x + 5, 22, GOLD)
    elif kind == 1:
        for x0, y0, x1, col, hi in ((3, 40, 30, GOLD, SKIN), (32, 44, 59, GOLD, SKIN), (13, 20, 41, GOLD, SKIN)):
            c.rect(x0, y0, x1, y0 + 22 if y0 != 20 else y0 + 20, col)
            h = 22 if y0 != 20 else 20
            c.rect(x0, y0, x1, y0 + 1, hi)
            for x in (x0 + 7, x1 - 7):
                c.rect(x, y0 + 1, x + 1, y0 + h - 1, DARK)
            for k in range(14):
                sx, sy = x0 + 3 + (k * 7) % (x1 - x0 - 5), y0 + 3 + (k * 5) % (h - 6)
                c.rect(sx, sy, sx, sy + 2, BRASS if col == GOLD else GOLD)
            c.rect(x0 + 12, y0 + 9, x0 + 14, y0 + 11, RED)
        # Мешок с зерном на тюке справа.
        c.ellipse(51, 38, 7, 8, TAN)
        c.rect(48, 28, 54, 31, TAN)
        c.rect(47, 31, 55, 32, DARK)
        c.line(46, 38, 48, 44, TAN, 1)
        c.ellipse(49, 36, 2, 3, SKIN)
        c.rect(50, 28, 52, 29, RED)
    elif kind == 2:
        c.rect(30, 28, 33, 63, TAN)
        c.rect(30, 28, 30, 63, SKIN)
        c.rect(28, 40, 35, 42, DARK)
        c.rect(26, 58, 37, 63, DARK)
        c.rect(24, 54, 39, 57, METAL)
        c.poly([(18, 18), (45, 18), (39, 29), (24, 29)], DARK)
        c.rect(17, 16, 46, 18, METAL)
        c.rect(17, 16, 46, 16, WHITE)
        c.poly([(31.5, 0), (40, 13), (23, 13)], RED)
        c.ellipse(31.5, 10, 8, 6, RED)
        c.ellipse(31.5, 11, 5, 5, GOLD)
        c.ellipse(31.5, 12, 2.5, 3, WHITE)
    elif kind == 3:
        # Баллиста: треножник, ложе с жёлобом, лук поперёк, тетива, болт и лебёдка.
        c.line(32, 44, 14, 62, TAN, 3)
        c.line(32, 44, 50, 62, TAN, 3)
        c.rect(30, 44, 34, 62, DARK)
        c.rect(8, 36, 54, 40, TAN)
        c.rect(8, 36, 54, 36, SKIN)
        c.rect(12, 40, 52, 41, DARK)
        c.line(46, 17, 53, 38, METAL, 3)
        c.line(53, 38, 46, 59, METAL, 3)
        c.rect(50, 34, 55, 42, DARK)
        c.line(46, 17, 22, 38, WHITE, 1)
        c.line(22, 38, 46, 59, WHITE, 1)
        c.line(14, 34, 60, 34, SKIN, 1)
        c.poly([(63, 34), (56, 31), (56, 37)], WHITE)
        c.rect(12, 32, 15, 36, RED)
        c.ellipse(9, 38, 5, 5, DARK)
        c.ellipse(9, 38, 3, 3, TAN)
        c.line(5, 38, 13, 38, DARK, 1)
        c.line(9, 34, 9, 42, DARK, 1)
        c.set(9, 38, GOLD)
    elif kind == 4:
        c.rect(8, 56, 14, 62, DARK)
        c.rect(50, 56, 56, 62, DARK)
        c.rect(10, 34, 54, 58, TAN)
        c.ellipse(32, 34, 22, 10, TAN)
        c.rect(10, 34, 54, 35, SKIN)
        c.rect(10, 34, 54, 34, WHITE)
        for x in (22, 32, 42):
            c.rect(x, 24, x, 58, DARK)
        for x in (12, 49):
            c.rect(x, 26, x + 3, 58, DARK)
            c.rect(x, 26, x, 58, METAL)
            for y in (30, 40, 50):
                c.set(x + 2, y, WHITE)
        c.rect(10, 44, 54, 45, DARK)
        c.rect(28, 38, 36, 49, BRASS)
        c.rect(29, 39, 35, 48, GOLD)
        c.rect(29, 39, 35, 39, WHITE)
        c.rect(31, 42, 33, 45, DARK)
        c.rect(31, 45, 32, 47, DARK)
    else:
        # Колокол на раме: стойки, перекладина, красная крыша, золотой колокол и верёвка.
        c.rect(14, 26, 19, 63, TAN)
        c.rect(14, 26, 14, 63, SKIN)
        c.rect(44, 26, 49, 63, TAN)
        c.rect(44, 26, 44, 63, SKIN)
        c.rect(12, 22, 51, 27, DARK)
        c.rect(12, 22, 51, 23, TAN)
        c.poly([(7, 24), (32, 3), (57, 24)], RED)
        c.poly([(7, 24), (32, 3), (32, 24)], VIOLET)
        c.rect(7, 24, 57, 24, PLUM)
        c.line(32, 5, 32, 22, DARK, 2)
        c.poly([(28, 29), (36, 29), (42, 50), (22, 50)], GOLD)
        c.rect(30, 29, 30, 49, SKY)
        c.rect(38, 33, 40, 49, BRASS)
        c.ellipse(32, 50, 10.5, 2.6, BRASS)
        c.rect(22, 51, 42, 51, GOLD)
        c.ellipse(32, 54, 2.5, 2.5, DARK)
        c.line(32, 56, 32, 62, TAN, 1)
        c.rect(28, 26, 36, 29, DARK)
    return c.finish()


def key():
    """Железный ключ: кольцо-трилистник, золотая муфта, красный шнурок, борода из двух зубцов."""
    c = Canvas(32, 32)
    for x, y in ((16, 5), (11, 10), (21, 10), (16, 10)):
        c.ellipse(x, y, 3.6, 3.6, METAL)
    c.ellipse(16, 8, 2, 2, None)
    c.rect(15, 14, 17, 29, METAL)
    c.rect(15, 14, 15, 29, WHITE)
    c.rect(18, 22, 23, 24, METAL)
    c.rect(18, 26, 21, 28, METAL)
    c.rect(13, 14, 19, 16, GOLD)
    c.rect(13, 14, 19, 14, WHITE)
    c.rect(13, 16, 19, 16, BRASS)
    c.line(19, 17, 25, 18, RED, 2)
    c.line(25, 18, 27, 24, RED, 2)
    c.set(27, 26, RED)
    c.set(26, 27, PLUM)
    return c.finish()


def medkit():
    """Лекарская сумка: кожаный мешок с клапаном, ремень-ручка, золотая пряжка и красный
    крест на белой нашивке."""
    c = Canvas(32, 32)
    c.line(9, 11, 12, 5, DARK, 2)
    c.line(12, 5, 19, 5, DARK, 2)
    c.line(19, 5, 22, 11, DARK, 2)
    c.rect(4, 11, 27, 29, TAN)
    c.rect(4, 11, 27, 18, SKIN)
    c.rect(4, 18, 27, 19, DARK)
    c.rect(4, 11, 27, 11, WHITE)
    c.rect(14, 15, 17, 21, BRASS)
    c.rect(15, 16, 16, 20, GOLD)
    c.rect(9, 22, 22, 28, WHITE)
    c.rect(15, 22, 16, 28, RED)
    c.rect(12, 24, 19, 26, RED)
    c.rect(4, 11, 4, 29, DARK)
    return c.finish()


def pistol(frame):
    """Арбалет в руке снизу по центру, 128×96: красный рукав с наручем, стальная перчатка,
    арбалет ложем вглубь (ось x=64, остриё болта у верхнего края); кадр 1: тетива спущена,
    болта нет, вспышка."""
    c = Canvas(128, 96)
    # Рукав: красный, слегка расширяется книзу, складки; выше наруч из стали.
    for y in range(66, 96):
        w = 17 + (y - 66) // 4
        for x in range(64 - w, 64 + w):
            fold = (x - 64 + w) % 9 == 4
            c.set(x, y, PLUM if fold else RED)
        c.set(64 - w, y, PLUM)
    for y in range(66, 70):
        c.rect(64 - 18, y, 64 + 17, y, GOLD if y == 66 else BRASS)
    for y in range(60, 66):
        w = 16
        col = WHITE if y < 62 else GREY
        c.rect(64 - w, y, 64 + w, y, col if y != 65 else METAL)
    for x in range(48, 81, 8):
        c.set(x, 63, DARK)
    # Ложе: дерево с бликом, жёлоб сверху, спусковой рычаг.
    c.rect(58, 18, 70, 60, TAN)
    c.rect(58, 18, 59, 60, SKIN)
    c.rect(69, 18, 70, 60, DARK)
    c.rect(62, 6, 66, 44, DARK)
    c.rect(63, 10, 65, 44, BRASS)
    c.rect(60, 44, 68, 47, DARK)
    # Лук-дуга поперёк: стальные плечи, стремя спереди.
    flex = 4 if frame else 0
    pts = [(14, 10), (30, 14 - flex // 2), (48, 17 - flex), (64, 18 - flex), (80, 17 - flex), (98, 14 - flex // 2), (114, 10)]
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], METAL, 4)
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1] - 2, b[0], b[1] - 2, WHITE, 1)
        c.line(a[0], a[1] + 2, b[0], b[1] + 2, DARK, 1)
    c.ellipse(64, 11, 8, 5, METAL)
    c.ellipse(64, 11, 5.5, 3, None)
    # Тетива и болт.
    if frame:
        c.line(14, 10, 114, 10, WHITE, 1)
    else:
        c.line(14, 10, 64, 36, WHITE, 1)
        c.line(64, 36, 114, 10, WHITE, 1)
        c.rect(63, 8, 65, 34, SKIN)
        c.poly([(64, 1), (68, 9), (60, 9)], WHITE)
        c.poly([(64, 1), (68, 9), (64, 9)], GREY)
        c.rect(62, 33, 66, 37, RED)
    c.rect(60, 36, 68, 37, METAL)
    # Перчатка: ладонь и четыре пальца, швы между пальцами, костяшки.
    c.ellipse(64, 55, 15, 10, GREY)
    c.rect(51, 48, 77, 58, GREY)
    for k in range(4):
        x0 = 51 + k * 7
        c.rect(x0, 42, x0 + 5, 50, WHITE)
        c.rect(x0, 42, x0 + 5, 42, SKY)
        c.rect(x0 + 1, 50, x0 + 4, 51, METAL)
        c.rect(x0, 46, x0 + 5, 46, GREY)
        if k:
            c.rect(x0 - 1, 43, x0 - 1, 54, DARK)
    c.rect(51, 56, 77, 57, METAL)
    c.rect(46, 60, 82, 61, WHITE)
    c.finish()
    if frame:
        c.ellipse(64, 0, 18, 10, GOLD)
        c.ellipse(64, 0, 10, 6, WHITE)
    return c


def face(mode):
    """Лицо рыцаря для HUD, 32×32: шлем с поднятым забралом и красным плюмажем, 0 прямо, 1 глянул
    влево, 2 вправо, 3 больно (вмятина на шлеме, кровь на брови), 4 ухмылка."""
    c = Canvas(32, 32)
    c.ellipse(16, 17, 14, 13, GREY)
    c.ellipse(14.5, 15, 11, 10, WHITE)
    # Плюмаж над шлемом.
    c.ellipse(16, 4, 7, 3.4, RED)
    c.rect(9, 3, 23, 6, RED)
    c.line(23, 5, 27, 9, RED, 2)
    c.rect(9, 6, 23, 6, PLUM)
    # Открытое лицо и носовая планка.
    c.ellipse(16, 19, 8.5, 9, DARK)
    c.ellipse(16, 20, 7.5, 8.2, SKIN)
    c.rect(15, 11, 16, 21, GREY)
    c.rect(15, 11, 15, 21, WHITE)
    c.rect(8, 27, 24, 30, DARK)
    _mail(c, 8, 27, 24, 30)
    look = {0: 0, 1: -2, 2: 2, 3: 0, 4: 0}[mode]
    for e in (-4, 4):
        if mode == 3:
            c.line(16 + e - 2, 16, 16 + e + 2, 18, K, 1)
            c.line(16 + e - 2, 18, 16 + e + 2, 16, K, 1)
        else:
            c.rect(16 + e - 2, 16, 16 + e + 2, 18, WHITE)
            c.rect(16 + e + look - 1, 17, 16 + e + look, 18, K)
            c.rect(16 + e - 2, 15, 16 + e + 2, 15, TAN)
    c.rect(16, 19, 16, 21, TAN)
    if mode == 4:
        c.rect(11, 24, 21, 26, WHITE)
        c.rect(11, 24, 21, 24, K)
        c.set(10, 23, K)
        c.set(22, 23, K)
    elif mode == 3:
        c.ellipse(16, 25, 3.5, 2, K)
        c.line(7, 10, 11, 14, DARK, 1)
        c.line(11, 14, 9, 17, DARK, 1)
        c.line(19, 11, 21, 14, RED, 1)
        c.set(21, 15, RED)
        c.set(21, 16, RED)
    else:
        c.rect(12, 25, 20, 25, K)
    return c.finish()


def textures():
    return {"wall_planks": tex_blocks(), "wall_stone": tex_ivy(), "wall_pillar": tex_columns(),
            "wall_exit": tex_gate(), "wall_cabin": tex_hall(), "wall_hull": tex_window(), "wall_cargo": tex_hay(),
            "floor_planks": tex_bridge(), "floor_stone": tex_cobble(), "floor_carpet": tex_carpet(),
            "ceiling_beams": tex_rafters()}


def sprites():
    out = {"shot": shot(), "bullet": bullet(), "key": key(), "medkit": medkit(),
           "hold_decor": strip([decor(k) for k in range(6)]),
           "pistol": strip([pistol(0), pistol(1)]),
           "face": strip([face(i) for i in range(5)])}
    out.update(man_strips())
    out.update(textures())
    return out


if __name__ == "__main__":
    if "--preview" in sys.argv:
        castles16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], castles16.shaded(sprites()))
