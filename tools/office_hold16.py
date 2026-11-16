#!/usr/bin/env python3
"""Набор «Офис» для шутера × 16/32-bit «до выхода» (#138), зеркало `space_hold16.py` и
`pixel_hold16.py`: те же ключи, размеры холстов, число и порядок кадров и точки опоры (ноги
врагов на 61-62 строке по центру кадра, оружие героя вверх по оси 64, текстуры 64×64 со швом по
краю).

Тема: ночной этаж конторы, занятый одинаковыми сотрудниками, выход это лифт. Стены: перегородка
опенспейса со стикерами, архив с папками, колонна с огнетушителем, двери лифта с зелёным табло
EXIT, кабинет директора в дереве с графиком в раме, окно с ночным городом, склад коробок с
бумагой. Полы: ковролин плитками, кафель, ламинат кабинета; потолок из плит со светильниками.
Враги: сотрудник в чёрном костюме с усами и папкой под мышкой, кидает скомканные листы
(`skel_*`), и охранник в фуражке и тёмных очках с дубинкой (`cut_*`). У героя красный степлер в
руке с закатанным рукавом и часами, голубая скрепка-снаряд, ключ с биркой, аптечка, лицо клерка
в очках.

    python3 tools/office_hold16.py --preview out.png
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import office16  # noqa: E402
from office16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                      DARK, RED, VIOLET, PLUM)

T = 64


# --- Текстуры ----------------------------------------------------------------------------------

def _note(c, x, y, w, h, col, lines=DARK):
    """Листок на стене: цветной прямоугольник, тень снизу, строчки и красная кнопка сверху."""
    c.rect(x, y, x + w - 1, y + h - 1, col)
    c.rect(x + 1, y + h, x + w, y + h, NAVY)
    for yy in range(y + 3, y + h - 1, 2):
        c.rect(x + 1, yy, x + w - 2 - (yy % 3), yy, lines)
    c.set(x + w // 2, y, RED)


def tex_partition():
    """Основная стена: перегородка опенспейса. Синяя ткань с переплетением в рамах 32×32,
    сверху алюминиевый профиль, на ткани стикеры и листки на кнопках, короб с розетками, плинтус."""
    rng = random.Random(301)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px = x % 32
            col = SEA
            if (x + y * 2) % 4 == 0 and y % 2 == 0:
                col = NAVY
            if px in (0, 31):
                col = DARK
            elif px == 1:
                col = METAL
            c.set(x, y, col)
    for _ in range(30):
        x, y = rng.randrange(T), rng.randrange(8, 40)
        if c.get(x, y) == SEA:
            c.set(x, y, AQUA if rng.random() < 0.25 else NAVY)
    # Профиль сверху.
    c.rect(0, 0, T - 1, 5, METAL)
    c.rect(0, 1, T - 1, 1, WHITE)
    c.rect(0, 2, T - 1, 2, GREY)
    c.rect(0, 5, T - 1, 5, DARK)
    # Листки: левая рама в жёлтых стикерах, правая с распечаткой и графиком.
    _note(c, 5, 11, 8, 8, GOLD, BRASS)
    _note(c, 16, 9, 11, 14, WHITE, GREY)
    _note(c, 7, 23, 7, 7, AQUA, SEA)
    _note(c, 37, 10, 12, 10, WHITE, GREY)
    c.line(39, 18, 42, 15, RED, 1)
    c.line(42, 15, 44, 16, RED, 1)
    c.line(44, 16, 47, 12, RED, 1)
    _note(c, 52, 13, 7, 7, GOLD, BRASS)
    _note(c, 44, 25, 8, 8, GOLD, BRASS)
    c.rect(54, 25, 58, 31, WHITE)
    c.rect(55, 26, 57, 29, SKIN)
    c.rect(55, 26, 57, 26, DARK)
    c.set(56, 25, RED)
    # Короб с розетками на высоте стола.
    c.rect(0, 41, T - 1, 46, GREY)
    c.rect(0, 41, T - 1, 41, WHITE)
    c.rect(0, 46, T - 1, 46, DARK)
    for x in range(8, T, 16):
        c.rect(x, 42, x + 4, 45, WHITE)
        c.set(x + 1, 43, DARK)
        c.set(x + 3, 43, DARK)
    c.rect(26, 47, 27, 57, DARK)
    # Плинтус.
    c.rect(0, 58, T - 1, T - 1, DARK)
    c.rect(0, 58, T - 1, 58, K)
    c.rect(0, 59, T - 1, 59, METAL)
    return c


def tex_archive():
    """Архив: четыре полки, плотно заставленные папками-регистраторами. Корешки разной ширины и
    высоты, на каждом белая этикетка и кольцо, кое-где папка стоит наискось или её нет."""
    rng = random.Random(302)
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, DARK)
    spines = (GOLD, RED, SEA, WHITE, VIOLET, GREY, BRASS, AQUA)
    for row in range(4):
        y0 = row * 16
        x = 0
        last = None
        while x < T:
            w = min(rng.choice((4, 5, 5, 6, 7)), T - x)
            if T - x - w in (1, 2, 3):
                w = T - x
            col = rng.choice([s for s in spines if s != last])
            last = col
            top = y0 + rng.choice((1, 1, 2, 3))
            if rng.random() < 0.1 and w >= 5:
                # Пустое место с завалившейся папкой.
                c.line(x + 1, y0 + 12, x + w - 2, y0 + 4, col, 2)
                x += w
                continue
            c.rect(x, top, x + w - 1, y0 + 12, col)
            c.rect(x, top, x, y0 + 12, K)
            if w >= 5:
                c.rect(x + 2, top + 2, x + w - 2, top + 5, GREY if col == WHITE else WHITE)
                c.rect(x + 2, top + 3, x + w - 3, top + 3, DARK)
                c.set(x + w // 2, y0 + 10, K)
                c.set(x + w // 2, y0 + 9, METAL)
            else:
                c.rect(x + 2, top + 2, x + 2, top + 6, DARK if col in (WHITE, GOLD, GREY) else WHITE)
            x += w
        # Доска полки с бликом и тенью под ней.
        c.rect(0, y0 + 13, T - 1, y0 + 14, GREY)
        c.rect(0, y0 + 13, T - 1, y0 + 13, WHITE)
        c.rect(0, y0 + 15, T - 1, y0 + 15, K)
        for xx in (0, 32):
            c.rect(xx, y0, xx, y0 + 14, METAL)
    return c


def tex_pillar():
    """Колонна: белёный бетон с металлическими уголками по краям, на ней красный огнетушитель на
    кронштейне и табличка над ним, внизу отбойная полоса."""
    rng = random.Random(303)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = WHITE if (x * 3 + y * 7) % 11 else GREY
            if x < 4 or x > 59:
                col = METAL
            if x in (0, T - 1):
                col = DARK
            if x in (3, 60):
                col = GREY
            if x in (4, 59):
                col = GREY
            c.set(x, y, col)
    for _ in range(40):
        x, y = rng.randrange(6, 58), rng.randrange(T)
        c.set(x, y, GREY)
    for y in range(6, T, 14):
        c.set(1, y, WHITE)
        c.set(62, y, WHITE)
    # Табличка «огнетушитель».
    c.rect(25, 6, 38, 19, RED)
    c.rect(26, 7, 37, 18, WHITE)
    c.rect(27, 8, 36, 17, RED)
    c.poly([(29, 16), (31, 9), (33, 13), (34, 11), (35, 16)], GOLD)
    c.rect(31, 14, 32, 16, WHITE)
    # Огнетушитель: баллон, раструб, шланг, манометр.
    c.rect(22, 30, 41, 31, DARK)
    c.rect(26, 28, 37, 52, RED)
    c.ellipse(31.5, 28, 5.5, 3, RED)
    c.ellipse(31.5, 52, 5.5, 2, RED)
    c.rect(27, 30, 28, 50, WHITE)
    c.rect(36, 29, 37, 52, DARK)
    c.rect(29, 36, 35, 42, WHITE)
    c.rect(30, 38, 34, 38, DARK)
    c.rect(30, 40, 33, 40, DARK)
    c.rect(30, 22, 33, 25, METAL)
    c.rect(27, 21, 36, 22, K)
    c.ellipse(36, 25, 1.5, 1.5, GOLD)
    c.line(27, 24, 23, 28, K, 2)
    c.line(23, 28, 23, 44, K, 2)
    c.poly([(21, 44), (25, 44), (26, 49), (20, 49)], K)
    # Отбойная полоса и плинтус.
    c.rect(0, 56, T - 1, T - 1, METAL)
    c.rect(0, 56, T - 1, 56, DARK)
    c.rect(0, 57, T - 1, 57, GREY)
    for x in range(2, T, 8):
        c.set(x, 60, DARK)
    return c


_FONT = {"E": ("111", "100", "110", "100", "111"), "X": ("101", "101", "010", "101", "101"),
         "I": ("111", "010", "010", "010", "111"), "T": ("111", "010", "010", "010", "010")}


def tex_exit():
    """Выход: двери лифта. Стальные створки со швом посередине и стрелками вверх, над ними
    зелёное табло EXIT, рама с зелёной светящейся кромкой, справа кнопка вызова."""
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, GREY)
    for y in range(T):
        for x in (0, T - 1):
            c.set(x, y, METAL)
    # Створки: шлифованная сталь.
    for y in range(14, 60):
        for x in range(7, 57):
            col = GREY if x % 5 else WHITE
            if x % 5 == 3:
                col = METAL
            c.set(x, y, col)
    c.rect(7, 14, 56, 15, DARK)
    c.rect(31, 16, 32, 59, K)
    c.rect(30, 16, 30, 59, METAL)
    c.rect(33, 16, 33, 59, WHITE)
    for x0 in (10, 36):
        c.rect(x0, 19, x0 + 17, 19, METAL)
        c.rect(x0, 55, x0 + 17, 55, METAL)
        c.rect(x0, 19, x0, 55, METAL)
        c.rect(x0 + 17, 19, x0 + 17, 55, WHITE)
    # Рама: тёмный наличник и зелёная кромка.
    for y in range(12, 60):
        for x in (4, 5, 6, 57, 58, 59):
            c.set(x, y, VIOLET if x in (5, 58) else DARK)
    c.rect(4, 12, 59, 13, DARK)
    # Табло.
    c.rect(13, 0, 50, 12, PLUM)
    c.rect(14, 1, 49, 11, VIOLET)
    x = 17
    for ch in "EXIT":
        for ry, row in enumerate(_FONT[ch]):
            for rx, bit in enumerate(row):
                if bit == "1":
                    c.rect(x + rx * 2, 2 + ry * 2, x + rx * 2 + 1, 3 + ry * 2, WHITE)
        x += 8
    # Стрелки вверх на створках.
    for cx in (19, 45):
        c.poly([(cx - 6, 38), (cx + 6, 38), (cx, 27)], VIOLET)
        c.rect(cx - 2, 38, cx + 2, 48, VIOLET)
        c.rect(cx - 2, 49, cx + 2, 49, PLUM)
        c.set(cx, 29, WHITE)
    # Кнопка вызова и порог.
    c.rect(60, 30, 62, 38, DARK)
    c.set(61, 32, GOLD)
    c.set(61, 35, METAL)
    c.rect(0, 60, T - 1, T - 1, METAL)
    c.rect(0, 60, T - 1, 60, K)
    for x in range(T):
        if x % 4 < 2:
            c.set(x, 62, DARK)
    return c


def tex_cabin():
    """Кабинет директора: стена в деревянных панелях, золотая рейка, ниже филёнки; посередине
    график роста в золотой раме."""
    rng = random.Random(305)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px = x % 16
            col = BRASS
            if px == 0:
                col = DARK
            elif px == 1:
                col = TAN
            elif px == 15:
                col = TAN if y % 5 == 0 else BRASS
            c.set(x, y, col)
    # Волокна дерева.
    for _ in range(46):
        x, y = rng.randrange(T), rng.randrange(T)
        n = rng.randint(3, 7)
        for k in range(n):
            if c.get(x, (y + k) % T) == BRASS:
                c.set(x, (y + k) % T, TAN if rng.random() < 0.3 else DARK)
    # Рейка и филёнки.
    c.rect(0, 38, T - 1, 41, GOLD)
    c.rect(0, 38, T - 1, 38, WHITE)
    c.rect(0, 41, T - 1, 41, DARK)
    for x0 in range(0, T, 32):
        c.rect(x0 + 4, 45, x0 + 27, 45, DARK)
        c.rect(x0 + 4, 45, x0 + 4, 54, DARK)
        c.rect(x0 + 5, 54, x0 + 27, 54, TAN)
        c.rect(x0 + 27, 46, x0 + 27, 54, TAN)
    c.rect(0, 58, T - 1, T - 1, DARK)
    c.rect(0, 58, T - 1, 58, K)
    # Рама с графиком.
    c.rect(15, 5, 48, 31, K)
    c.rect(16, 6, 47, 30, GOLD)
    c.rect(16, 30, 47, 30, BRASS)
    c.rect(47, 6, 47, 30, BRASS)
    c.rect(19, 9, 44, 27, WHITE)
    c.rect(21, 11, 21, 25, DARK)
    c.rect(21, 25, 42, 25, DARK)
    for i, h in enumerate((3, 5, 4, 8, 11)):
        c.rect(24 + i * 4, 24 - h, 25 + i * 4, 24, SEA)
    pts = ((23, 21), (27, 19), (31, 20), (35, 15), (41, 11))
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], RED, 1)
    c.poly([(39, 11), (42, 10), (42, 13)], RED)
    return c


def tex_window():
    """Окно в город: крашеная стена, в раме ночное небо с луной и силуэтами домов в жёлтых
    окнах, сверху приспущенные жалюзи, под подоконником батарея."""
    rng = random.Random(306)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            c.set(x, y, GREY if (x * 5 + y * 3) % 17 else METAL)
    c.rect(0, 0, T - 1, 1, WHITE)
    # Рама и стекло.
    c.rect(6, 4, 57, 46, DARK)
    c.rect(7, 5, 56, 45, METAL)
    c.rect(9, 7, 54, 43, NAVY)
    # Дома: высота столбиками, окна сеткой.
    x = 9
    while x <= 54:
        w = min(rng.randint(5, 9), 55 - x)
        h = rng.randint(8, 24)
        c.rect(x, 43 - h, x + w - 1, 43, DARK)
        c.rect(x, 43 - h, x + w - 1, 43 - h, SEA)
        for wy in range(43 - h + 2, 43, 3):
            for wx in range(x + 1, x + w - 1, 2):
                if rng.random() < 0.55:
                    c.set(wx, wy, GOLD if rng.random() < 0.8 else AQUA)
        x += w
    c.ellipse(46, 13, 3, 3, SKY)
    c.ellipse(47, 12, 2, 2, NAVY)
    for sx, sy in ((14, 17), (25, 16), (36, 18), (30, 21)):
        if c.get(sx, sy) == NAVY:
            c.set(sx, sy, SKY)
    # Жалюзи: ламели и шнур.
    for y in range(7, 16):
        c.rect(9, y, 54, y, WHITE if y % 3 else METAL)
    c.rect(9, 16, 54, 16, DARK)
    c.rect(52, 17, 52, 30, GREY)
    c.set(52, 31, WHITE)
    # Переплёт и подоконник.
    c.rect(31, 7, 32, 43, METAL)
    c.rect(31, 7, 31, 43, GREY)
    c.rect(4, 46, 59, 48, WHITE)
    c.rect(4, 48, 59, 48, METAL)
    c.rect(4, 49, 59, 49, DARK)
    # Батарея.
    c.rect(14, 51, 49, 58, WHITE)
    for x in range(14, 50, 4):
        c.rect(x, 51, x, 58, METAL)
        c.rect(x + 1, 51, x + 1, 58, GREY)
    c.rect(50, 53, 52, 54, METAL)
    c.rect(0, 59, T - 1, T - 1, DARK)
    c.rect(0, 59, T - 1, 59, K)
    c.rect(0, 60, T - 1, 60, METAL)
    return c


def tex_boxes():
    """Склад: штабель картонных коробок с бумагой 32×32 со сдвигом ряда. Скотч по крышке,
    прорезь-ручка, белая наклейка со строчками и красный знак."""
    c = Canvas(T, T)
    for by in (0, 32):
        for bx in (0, 32):
            off = 16 if by == 32 else 0
            x0 = (bx + off) % T
            body = (BRASS, TAN)[(bx // 32 + by // 32) % 2]
            hi = TAN if body == BRASS else SKIN
            for y in range(by, by + 32):
                for x in range(32):
                    edge = x in (0, 31) or y in (by, by + 31)
                    ly = y - by
                    col = body
                    if edge:
                        col = DARK
                    elif ly == 1 or x == 1:
                        col = hi
                    elif ly == 8:
                        col = DARK
                    elif ly == 9:
                        col = hi
                    elif (x * 7 + ly * 3) % 23 == 0:
                        col = hi
                    c.set((x0 + x) % T, y, col)
            # Скотч через крышку.
            for y in range(by + 1, by + 14):
                for x in range(14, 18):
                    c.set((x0 + x) % T, y, GREY if x != 14 else WHITE)
            # Прорезь-ручка.
            for x in range(22, 28):
                c.set((x0 + x) % T, by + 13, K)
                c.set((x0 + x) % T, by + 14, K if x not in (22, 27) else body)
            # Наклейка.
            for x in range(4, 14):
                for y in range(by + 16, by + 27):
                    c.set((x0 + x) % T, y, WHITE)
            for k, yy in enumerate((18, 20, 22, 24)):
                for x in range(5, 12 - k % 2 * 2):
                    c.set((x0 + x) % T, by + yy, DARK if k == 0 else GREY)
            # Красный знак «не кантовать».
            for x in range(21, 27):
                for y in range(by + 19, by + 27):
                    c.set((x0 + x) % T, y, RED)
            for y in range(by + 21, by + 26):
                c.set((x0 + 23) % T, y, WHITE)
                c.set((x0 + 24) % T, y, WHITE)
            c.set((x0 + 22) % T, by + 22, WHITE)
            c.set((x0 + 25) % T, by + 22, WHITE)
    return c


def tex_floor():
    """Ковролин плитками 32×32: ворс через плитку лежит то вдоль, то поперёк, швы темнее."""
    rng = random.Random(307)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 32, y % 32
            along = (x // 32 + y // 32) % 2 == 0
            col = VIOLET
            if px == 0 or py == 0:
                col = PLUM
            elif along and py % 3 == 0 and (px + py) % 5 < 3:
                col = PLUM
            elif not along and px % 3 == 0 and (px + py) % 5 < 3:
                col = PLUM
            c.set(x, y, col)
    for _ in range(40):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == VIOLET:
            c.set(x, y, AQUA if rng.random() < 0.2 else PLUM)
    return c


def tex_floor_tile():
    """Кафель 16×16 в шахматку: светлая и серая плитка, тёмная затирка, блик в углу."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 16, y % 16
            light = (x // 16 + y // 16) % 2 == 0
            col = WHITE if light else GREY
            if px == 0 or py == 0:
                col = DARK
            elif px == 15 or py == 15:
                col = GREY if light else METAL
            elif (px * 3 + py * 5) % 19 == 0:
                col = GREY if light else METAL
            c.set(x, y, col)
    for x in range(0, T, 16):
        for y in range(0, T, 16):
            c.rect(x + 2, y + 2, x + 4, y + 2, WHITE)
    return c


def tex_floor_laminate():
    """Ламинат кабинета: доски по 8 пикселей со стыками вразбежку, волокна и светлая фаска."""
    rng = random.Random(308)
    c = Canvas(T, T)
    for y in range(T):
        row = y // 8
        for x in range(T):
            joint = (x + row * 23) % 32 == 0
            col = BRASS
            if y % 8 == 0 or joint:
                col = DARK
            elif y % 8 == 1:
                col = TAN
            c.set(x, y, col)
    for _ in range(60):
        x, y = rng.randrange(T), rng.randrange(T)
        n = rng.randint(3, 9)
        for k in range(n):
            if c.get((x + k) % T, y) == BRASS:
                c.set((x + k) % T, y, TAN if rng.random() < 0.5 else GOLD)
    return c


def tex_ceiling():
    """Потолок: плиты 16×16 в тёмной решётке, точки перфорации, две квадратные панели света на
    тайл (квадраты, а не полосы: полосы в перспективе расходятся лучами)."""
    rng = random.Random(309)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = METAL
            if x % 16 == 0 or y % 16 == 0:
                col = DARK
            elif (x % 16) % 4 == 2 and (y % 16) % 4 == 2:
                col = DARK
            c.set(x, y, col)
    for _ in range(30):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == METAL:
            c.set(x, y, GREY)
    for x0, y0 in ((17, 1), (49, 33)):
        c.rect(x0, y0, x0 + 14, y0 + 14, GREY)
        c.rect(x0 + 1, y0 + 1, x0 + 13, y0 + 13, SKY)
        c.rect(x0 + 3, y0 + 3, x0 + 11, y0 + 11, WHITE)
        c.rect(x0 + 7, y0 + 1, x0 + 7, y0 + 13, GREY)
    return c


# --- Сотрудники --------------------------------------------------------------------------------
# Рост 58 пикселей при кадре 64: голова 12, корпус 20, ноги 22, человеческие пропорции. Сотрудник
# узнаётся по чёрному пиджаку с белой манишкой, усам шире лица и жёлтой папке под мышкой;
# охранник по фуражке с козырьком, синей рубашке, чёрным очкам и светлой дубинке.

def _paper_ball(c, x, y, r):
    """Скомканный лист: белый ком с серыми заломами."""
    c.ellipse(x, y, r, r, WHITE)
    c.line(x - r * 0.5, y - r * 0.3, x, y + r * 0.2, GREY, 1)
    c.line(x, y + r * 0.2, x + r * 0.6, y - r * 0.4, GREY, 1)
    if r >= 5:
        c.line(x, y + r * 0.2, x - r * 0.2, y + r * 0.8, GREY, 1)
        c.rect(x + 1, y + 2, x + 2, y + 3, RED)


def _sleeve(c, x0, y0, x1, y1, guard, far=False):
    """Рука от плеча до кисти. У костюма рукав до запястья с белой манжетой, у охранника
    короткий рукав и голое предплечье. Тёмная кромка отбивает рукав от корпуса того же цвета."""
    cloth = SEA if guard else DARK
    c.line(x0, y0, x1, y1, NAVY, 5)
    if guard:
        mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        c.line(mx, my, x1, y1, TAN if far else SKIN, 3)
        c.line(x0, y0, mx, my, NAVY if far else cloth, 4)
    else:
        c.line(x0, y0, x1, y1, NAVY if far else cloth, 3)
        c.ellipse(x1, y1, 1.6, 1.6, WHITE)


def _hand(c, x, y):
    c.ellipse(x, y, 2, 2, SKIN)


def _head(c, hx, hy, angle, guard, mode):
    """Голова 11×12 с центром (hx, hy): причёска или фуражка и лицо по ракурсу."""
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    c.rect(hx - 2, hy + 5, hx + 2, hy + 9, TAN)
    c.ellipse(hx, hy, 5.5, 6, SKIN)
    if not side:
        c.rect(hx - 6, hy, hx - 6, hy + 1, SKIN)
        c.rect(hx + 6, hy, hx + 6, hy + 1, SKIN)
    for yy in range(hy - 7, hy + 7):
        for xx in range(hx - 7, hx + 8):
            if c.get(xx, yy) != SKIN or yy > hy + 6:
                continue
            dx, dy = xx - hx, yy - hy
            if angle == 0:
                hair = dy <= -4 or (abs(dx) >= 5 and dy <= -2)
            elif angle == 1:
                hair = dy <= -4 or (dx <= -4 and dy <= 1)
            elif angle == 2:
                hair = dy <= -4 or (dx <= -2 and dy <= 1) or (dx <= -4 and dy <= 3)
            elif angle == 3:
                hair = dy <= 3 and not (dx >= 3 and dy >= -2)
            else:
                hair = dy <= 3
            if hair:
                c.set(xx, yy, DARK)
    off = 2 if angle == 1 else 0
    if guard:
        # Фуражка: тулья шире головы, околыш, кокарда, чёрный козырёк.
        c.ellipse(hx, hy - 6, 7, 3, NAVY)
        c.rect(hx - 6, hy - 6, hx + 6, hy - 4, NAVY)
        c.rect(hx - 6, hy - 4, hx + 6, hy - 4, SEA)
        if angle == 0:
            c.rect(hx - 6, hy - 3, hx + 6, hy - 3, K)
            c.rect(hx - 1, hy - 7, hx, hy - 6, GOLD)
        elif angle == 1:
            c.rect(hx - 3, hy - 3, hx + 8, hy - 3, K)
            c.rect(hx + 2, hy - 7, hx + 3, hy - 6, GOLD)
        elif angle == 2:
            c.rect(hx, hy - 3, hx + 10, hy - 3, K)
            c.rect(hx + 5, hy - 7, hx + 6, hy - 6, GOLD)
    if back:
        if not guard:
            # Зализанный затылок: блик и линия стрижки над шеей.
            c.line(hx - 3, hy - 3, hx + 2, hy - 4, METAL, 1)
        return
    if guard:
        if side:
            c.rect(hx + 1, hy - 1, hx + 5, hy, K)
            c.rect(hx - 3, hy - 1, hx, hy - 1, K)
            c.set(hx + 4, hy - 1, SKY)
            c.set(hx + 6, hy + 1, SKIN)
            c.rect(hx + 3, hy + 3, hx + 5, hy + 3, K)
        else:
            c.rect(hx - 5 + off, hy - 1, hx + 5 + off // 2, hy, K)
            c.set(hx + off, hy, SKIN)
            c.set(hx - 3 + off, hy - 1, SKY)
            c.set(hx + 3 + off, hy - 1, SKY)
            c.rect(hx - 2 + off, hy + 3, hx + 2 + off, hy + 3, K)
            c.set(hx + off, hy + 1, TAN)
        return
    # Сотрудник: брови, глаза, нос, усы шире лица.
    if side:
        c.rect(hx + 2, hy - 2, hx + 4, hy - 2, K)
        c.rect(hx + 3, hy - 1, hx + 3, hy, K)
        c.set(hx + 6, hy + 1, SKIN)
        c.rect(hx + 2, hy + 2, hx + 7, hy + 2, DARK)
        c.rect(hx + 5, hy + 3, hx + 8, hy + 3, DARK)
        c.line(hx - 1, hy - 5, hx + 3, hy - 6, METAL, 1)
    else:
        for e in (-3, 3):
            c.rect(hx + e - 1 + off, hy - 2, hx + e + 1 + off, hy - 2, K)
            c.rect(hx + e + off, hy - 1, hx + e + off, hy, K if mode != "fire" else RED)
        c.rect(hx + off, hy, hx + off, hy + 1, TAN)
        c.rect(hx - 4 + off, hy + 2, hx + 4 + off, hy + 2, DARK)
        c.rect(hx - 6 + off, hy + 3, hx - 2 + off, hy + 3, DARK)
        c.rect(hx + 2 + off, hy + 3, hx + 6 + off, hy + 3, DARK)
        c.set(hx - 6 + off, hy + 4, DARK)
        c.set(hx + 6 + off, hy + 4, DARK)
        if mode in ("fire", "hurt"):
            c.rect(hx - 1 + off, hy + 4, hx + 1 + off, hy + 4, K)
        c.line(hx - 2, hy - 5, hx + 2, hy - 6, METAL, 1)


def _fallen(k, guard):
    """Падение: кадр 1 оседает на колени, раскинув руки; кадр 2 лежит на спине головой вправо.
    У сотрудника разлетаются листы и падает папка, у охранника слетает фуражка и катится дубинка."""
    c = Canvas(T, T)
    cx = 32
    cloth = SEA if guard else DARK
    if k == 1:
        c.rect(cx - 15, 60, cx - 9, 62, K)
        c.rect(cx + 6, 60, cx + 12, 62, K)
        c.ellipse(cx - 1, 57, 11, 5, DARK)
        c.ellipse(cx - 1, 56, 9, 3, NAVY)
        _sleeve(c, cx - 7, 38, cx - 17, 30, guard, True)
        _hand(c, cx - 18, 28)
        _sleeve(c, cx + 7, 37, cx + 18, 31, guard)
        _hand(c, cx + 19, 29)
        c.poly([(cx - 8, 36), (cx + 7, 34), (cx + 9, 54), (cx - 8, 55)], cloth)
        if guard:
            c.rect(cx - 8, 52, cx + 9, 53, K)
            c.rect(cx - 1, 52, cx + 1, 53, GOLD)
            c.rect(cx + 3, 39, cx + 5, 41, GOLD)
            c.line(cx, 36, cx + 1, 51, NAVY, 1)
        else:
            c.poly([(cx - 3, 35), (cx + 4, 34), (cx + 1, 45)], WHITE)
            c.line(cx + 1, 36, cx + 1, 43, K, 2)
            c.set(cx + 1, 48, METAL)
        _head(c, cx + 2, 26, 0, guard, "hurt")
        if guard:
            # Очки на месте, фуражка слетела вверх: заново голова без неё не нужна, тулья
            # улетает отдельно, дубинка падает.
            c.line(cx + 22, 38, cx + 27, 54, METAL, 3)
            c.line(cx + 22, 38, cx + 23, 42, DARK, 3)
        else:
            c.poly([(cx - 27, 40), (cx - 19, 37), (cx - 16, 48), (cx - 24, 51)], GOLD)
            c.line(cx - 25, 42, cx - 19, 40, BRASS, 1)
            for px, py, d in ((cx - 22, 12, 1), (cx + 19, 10, -1), (cx - 9, 6, -1), (cx + 24, 22, 1)):
                c.poly([(px - 4, py - 2 * d), (px + 3, py - 4), (px + 4, py + 2 * d), (px - 3, py + 4)], WHITE)
                c.line(px - 2, py, px + 2, py - 1, GREY, 1)
        return c.finish()
    # Лежит: ботинки носками вверх слева, корпус, голова справа.
    c.rect(cx - 28, 54, cx - 25, 61, K)
    c.line(cx - 23, 58, cx - 6, 58, DARK, 6)
    c.line(cx - 23, 56, cx - 8, 56, NAVY, 1)
    c.poly([(cx - 8, 53), (cx + 8, 52), (cx + 10, 61), (cx - 8, 61)], cloth)
    hx, hy = cx + 17, 56
    c.rect(cx + 9, 55, cx + 12, 59, TAN)
    c.ellipse(hx, hy, 6, 5.5, SKIN)
    if guard:
        c.rect(cx - 2, 53, cx - 1, 61, K)
        c.rect(cx - 2, 56, cx - 1, 57, GOLD)
        c.rect(cx + 3, 54, cx + 5, 56, GOLD)
        for yy in range(hy - 6, hy + 7):
            for xx in range(hx + 4, hx + 8):
                if c.get(xx, yy) == SKIN:
                    c.set(xx, yy, DARK)
        c.rect(hx - 1, hy - 4, hx, hy + 4, K)
        c.set(hx - 1, hy - 2, SKY)
        c.rect(hx - 4, hy - 1, hx - 4, hy + 1, K)
        # Фуражка лежит на животе, дубинка на полу вдоль ног.
        c.ellipse(cx, 49, 6, 3, NAVY)
        c.rect(cx - 6, 50, cx + 6, 51, SEA)
        c.rect(cx - 10, 52, cx - 4, 52, K)
        c.rect(cx - 1, 47, cx, 48, GOLD)
        c.rect(cx - 22, 61, cx - 4, 62, METAL)
        c.rect(cx - 8, 61, cx - 4, 62, DARK)
        _sleeve(c, cx + 5, 56, cx - 5, 60, guard)
        _hand(c, cx - 6, 60)
    else:
        c.poly([(cx + 3, 52), (cx + 8, 52), (cx + 9, 58)], WHITE)
        c.line(cx + 5, 53, cx + 8, 55, K, 2)
        for yy in range(hy - 6, hy + 7):
            for xx in range(hx + 3, hx + 8):
                if c.get(xx, yy) == SKIN:
                    c.set(xx, yy, DARK)
        # Лицо вверх: закрытые глаза и усы поперёк.
        c.rect(hx, hy - 3, hx, hy - 2, K)
        c.rect(hx, hy + 2, hx, hy + 3, K)
        c.rect(hx - 3, hy - 4, hx - 2, hy + 4, DARK)
        c.rect(hx - 4, hy - 5, hx - 4, hy - 3, DARK)
        c.rect(hx - 4, hy + 3, hx - 4, hy + 5, DARK)
        _sleeve(c, cx + 5, 56, cx - 5, 60, guard)
        _hand(c, cx - 6, 60)
        # Папка домиком на ногах, лист в воздухе и лист на полу.
        c.poly([(cx - 21, 55), (cx - 15, 45), (cx - 9, 55)], GOLD)
        c.line(cx - 15, 46, cx - 12, 54, BRASS, 1)
        c.poly([(cx - 2, 34), (cx + 7, 31), (cx + 9, 38), (cx, 41)], WHITE)
        c.line(cx + 1, 36, cx + 6, 34, GREY, 1)
        c.poly([(cx - 22, 24), (cx - 14, 26), (cx - 16, 33), (cx - 24, 31)], WHITE)
        c.line(cx - 21, 28, cx - 17, 29, GREY, 1)
    return c.finish()


def worker(angle, phase, mode="walk", guard=False):
    """Сотрудник 64×64 в ракурсе `angle` (0 спереди … 4 со спины, лицом вправо на 1-3), шаг
    `phase` 0/1. `mode`: walk, aim, fire, slash, die0..die2, hurt. `guard` охранник с дубинкой
    вместо сотрудника с папкой. Ступни на 61-62 строке, ось по центру кадра, как у скелета
    пиратов и пришельца космоса."""
    if mode.startswith("die"):
        k = int(mode[-1])
        if k == 0:
            return worker(0, 0, "hurt", guard)
        return _fallen(k, guard)
    c = Canvas(T, T)
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    bob = 1 if phase else 0
    cloth = SEA if guard else DARK
    sh = 20 - bob
    hip = 40 - bob
    w = (6 if side else (9 if diag else 10)) if guard else (5 if side else (8 if diag else 9))
    walk = mode in ("walk", "slash")
    # Ноги: брюки, ботинки с носком по ходу.
    for sign in (-1, 1):
        if side:
            swing = sign * (6 if phase else -6) if mode == "walk" else sign * 2
            top = (cx, hip - 1)
            foot = (cx + swing, 60)
            knee = ((top[0] + foot[0]) / 2.0 + 1.5, 50)
            col = NAVY if sign < 0 else DARK
            lift = 0
        else:
            lift = 2 if (mode == "walk" and (sign > 0) == bool(phase)) else 0
            top = (cx + sign * 4, hip - 1)
            foot = (cx + sign * 5, 60 - lift)
            knee = ((top[0] + foot[0]) / 2.0, 50 - lift)
            col = DARK
        c.line(top[0], top[1], knee[0], knee[1], col, 6)
        c.line(knee[0], knee[1], foot[0], foot[1], col, 5)
        if side:
            c.rect(foot[0] - 2, 60, foot[0] + 5, 62, K)
        else:
            c.rect(foot[0] - 3, 60 - lift, foot[0] + 3, 62 - lift, K)
            if not back:
                c.rect(foot[0] - 2, 60 - lift, foot[0] + 2, 60 - lift, METAL)
    # Что за корпусом: папка у бока и дальняя рука.
    if not guard:
        if side:
            c.rect(cx + 2, sh + 6, cx + 9, sh + 17, GOLD)
            c.rect(cx + 9, sh + 7, cx + 10, sh + 16, WHITE)
            c.line(cx + 6, sh + 7, cx + 6, sh + 16, BRASS, 1)
        elif back:
            c.rect(cx - w - 5, sh + 5, cx - w + 1, sh + 18, GOLD)
            c.rect(cx - w - 4, sh + 4, cx - w, sh + 4, WHITE)
            c.line(cx - w - 3, sh + 7, cx - w - 3, sh + 17, BRASS, 1)
        else:
            c.rect(cx + w - 1, sh + 5, cx + w + 5, sh + 18, GOLD)
            c.rect(cx + w, sh + 4, cx + w + 4, sh + 4, WHITE)
            c.line(cx + w + 3, sh + 7, cx + w + 3, sh + 17, BRASS, 1)
    elif side:
        _sleeve(c, cx + 1, sh + 3, cx - 3 if phase else cx + 4, sh + 16, guard, True)
        _hand(c, cx - 3 if phase else cx + 4, sh + 18)
    # Корпус.
    c.poly([(cx - w, sh + 1), (cx + w, sh + 1), (cx + w - 1, hip), (cx - w + 1, hip)], cloth)
    c.rect(cx - w + 1, sh, cx + w - 1, sh, cloth)
    off = 2 if angle == 1 else 0
    if guard:
        c.rect(cx - w + 1, hip - 2, cx + w - 1, hip - 1, K)
        c.rect(cx - w + 1, hip, cx + w - 1, hip, DARK)
        if back:
            c.rect(cx - 6, sh + 5, cx + 6, sh + 8, WHITE)
            for x in range(cx - 5, cx + 6, 2):
                c.rect(x, sh + 6, x, sh + 7, DARK)
            c.rect(cx - w + 1, sh, cx + w - 1, sh + 1, NAVY)
        elif side:
            c.rect(cx + 2, hip - 2, cx + 4, hip - 1, GOLD)
            c.rect(cx + 2, sh + 5, cx + 4, sh + 7, GOLD)
            c.rect(cx + 2, sh, cx + 5, sh + 1, WHITE)
        else:
            c.rect(cx - 1 + off, hip - 2, cx + 1 + off, hip - 1, GOLD)
            c.line(cx + off, sh + 2, cx + off, hip - 3, NAVY, 1)
            c.poly([(cx - 3 + off, sh), (cx + 3 + off, sh), (cx + off, sh + 4)], WHITE)
            c.rect(cx + off, sh + 2, cx + off, sh + 7, K)
            c.rect(cx + 3 + off, sh + 5, cx + 6 + off, sh + 8, GOLD)
            c.rect(cx + 4 + off, sh + 6, cx + 5 + off, sh + 7, BRASS)
            c.rect(cx - 7 + off, sh + 6, cx - 3 + off, sh + 6, NAVY)
            c.rect(cx - w, sh, cx - w + 3, sh + 1, NAVY)
            c.rect(cx + w - 3, sh, cx + w, sh + 1, NAVY)
    else:
        if back:
            c.rect(cx - 3, sh - 1, cx + 3, sh, WHITE)
            c.line(cx, sh + 12, cx, hip, NAVY, 1)
            c.line(cx - w + 2, sh + 3, cx - w + 3, sh + 12, NAVY, 1)
            c.line(cx + w - 2, sh + 3, cx + w - 3, sh + 12, NAVY, 1)
        elif side:
            c.rect(cx + 3, sh, cx + 5, sh + 8, WHITE)
            c.rect(cx + 4, sh + 2, cx + 5, sh + 8, K)
            c.line(cx + 2, sh, cx + 3, sh + 10, METAL, 1)
        else:
            c.poly([(cx - 3 + off, sh), (cx + 3 + off, sh), (cx + off, sh + 11)], WHITE)
            c.rect(cx - 1 + off, sh + 1, cx + off, sh + 8, K)
            c.line(cx - 4 + off, sh, cx - 1 + off, sh + 11, METAL, 1)
            c.line(cx + 4 + off, sh, cx + 1 + off, sh + 11, METAL, 1)
            c.set(cx + off, sh + 14, METAL)
            c.set(cx + off, sh + 17, METAL)
            c.rect(cx - 7 + off, sh + 6, cx - 5 + off, sh + 6, WHITE)
    # Руки и то, что в руках.
    flash = None
    if guard:
        up = mode == "slash"
        if side:
            hx_, hy_ = (cx + 9, sh + 12) if not up else (cx + 8, sh - 6)
            _sleeve(c, cx, sh + 3, hx_, hy_, guard)
            tip = (hx_ + 8, hy_ - 20) if not up else (hx_ + 6, 1)
            c.line(hx_ - 1, hy_ + 3, tip[0], tip[1], GREY, 3)
            c.line(hx_ - 1, hy_ + 3, hx_ + 1, hy_ - 2, DARK, 3)
            _hand(c, hx_, hy_)
        else:
            _sleeve(c, cx - w, sh + 3, cx - w - 2, sh + 16, guard, back)
            _hand(c, cx - w - 2, sh + 18)
            hx_, hy_ = (cx + w + 3, sh + 15) if not up else (cx + w + 4, sh - 7)
            _sleeve(c, cx + w, sh + 3, hx_, hy_, guard)
            tip = (hx_ + 5, hy_ - 22) if not up else (hx_ + 3, 1)
            c.line(hx_ - 1, hy_ + 4, tip[0], tip[1], GREY, 3)
            c.line(hx_ - 1, hy_ + 4, hx_, hy_ - 2, DARK, 3)
            _hand(c, hx_, hy_)
    elif side:
        ax = cx + (3 if phase else -2)
        _sleeve(c, cx, sh + 3, ax, sh + 15, guard)
        _hand(c, ax, sh + 17)
        _paper_ball(c, ax + 1, sh + 20, 3)
    elif back:
        _sleeve(c, cx - w, sh + 3, cx - w - 1, sh + 12, guard)
        _sleeve(c, cx + w, sh + 3, cx + w + 2, sh + 16, guard)
        _hand(c, cx + w + 2, sh + 18)
        _paper_ball(c, cx + w + 3, sh + 21, 3)
    else:
        # Левая рука прижимает папку локтем, кисть спереди.
        _sleeve(c, cx + w, sh + 3, cx + w + 3, sh + 10, guard)
        _sleeve(c, cx + w + 3, sh + 10, cx + w, sh + 14, guard)
        _hand(c, cx + w - 1, sh + 14)
        if mode == "aim":
            _sleeve(c, cx - w, sh + 3, cx - w - 5, sh - 2, guard)
            _sleeve(c, cx - w - 5, sh - 2, cx - w - 3, sh - 9, guard)
            _hand(c, cx - w - 3, sh - 10)
            _paper_ball(c, cx - w - 3, sh - 14, 3.5)
        elif mode == "fire":
            c.line(cx - w, sh + 3, cx - 6, sh + 9, NAVY, 6)
            c.line(cx - w, sh + 3, cx - 6, sh + 9, DARK, 4)
            flash = (cx - 6, sh + 11)
        else:
            _sleeve(c, cx - w, sh + 3, cx - w - 2, sh + 16, guard)
            _hand(c, cx - w - 2, sh + 18)
            _paper_ball(c, cx - w - 3, sh + 21, 3)
    hx = cx + (2 if side else (1 if diag else 0))
    _head(c, hx, 11 - bob, angle, guard, mode)
    c.finish()
    if flash:
        # Бросок в камеру: крупный ком у груди и штрихи разлёта.
        fx, fy = flash
        c.ellipse(fx, fy, 7, 7, K)
        _paper_ball(c, fx, fy, 6)
        for dx, dy in ((-10, -6), (-11, 2), (-8, 9), (9, 8), (10, -4), (0, -10)):
            c.line(fx + dx, fy + dy, fx + dx * 1.3, fy + dy * 1.3, WHITE, 1)
    if mode == "hurt":
        for x in range(T):
            for y in range(T):
                if c.get(x, y) in (SKIN, TAN, WHITE, SEA) and (x + y) % 3 == 0:
                    c.set(x, y, RED)
    return c


def worker_strips():
    out = {}
    for name, guard in (("skel", False), ("cut", True)):
        walk = []
        for a in range(5):
            for ph in range(2):
                walk.append(worker(a, ph, "walk", guard))
        out[name + "_walk"] = strip(walk)
        out[name + "_die"] = strip([worker(0, 0, "die%d" % k, guard) for k in range(3)])
    out["skel_fire"] = strip([worker(0, 0, "aim"), worker(0, 0, "fire")])
    out["cut_slash"] = strip([worker(0, 0, "walk", True), worker(0, 0, "slash", True)])
    return out


# --- Предметы, оружие, лицо --------------------------------------------------------------------

def shot():
    """Снаряд сотрудника: крупный скомканный лист с красным штампом, чтобы не путать с голубой
    скрепкой героя."""
    c = Canvas(16, 16)
    c.poly([(2, 6), (6, 2), (11, 2), (14, 6), (13, 11), (9, 14), (4, 13), (2, 10)], WHITE)
    c.finish()
    c.line(4, 5, 8, 8, GREY, 1)
    c.line(8, 8, 12, 5, GREY, 1)
    c.line(8, 8, 6, 12, GREY, 1)
    c.rect(9, 9, 11, 11, RED)
    c.set(4, 9, RED)
    return c


def bullet():
    """Снаряд героя: голубая канцелярская скрепка, петля в петле, с бликом."""
    c = Canvas(16, 16)
    c.rect(5, 3, 10, 13, AQUA)
    c.rect(6, 4, 9, 12, None)
    c.rect(7, 5, 8, 10, AQUA)
    c.set(5, 3, None)
    c.set(10, 3, None)
    c.set(5, 13, None)
    c.set(10, 13, None)
    c.finish()
    c.rect(5, 5, 5, 8, SKY)
    c.set(6, 3, WHITE)
    return c


def decor(kind):
    """Ориентир зала 64×64, низ на 62-63 строке: 0 кулер с бутылью, 1 коробки с бумагой, 2 фикус
    в горшке, 3 копир, стреляющий бумагой, 4 сейф, 5 серверная стойка с мигалкой."""
    c = Canvas(T, T)
    if kind == 0:
        # Кулер: голубая бутыль горлом вниз, белый корпус с двумя краниками, стопка стаканов.
        c.rect(22, 60, 25, 62, DARK)
        c.rect(38, 60, 41, 62, DARK)
        c.rect(21, 30, 42, 60, WHITE)
        c.rect(21, 30, 42, 31, GREY)
        c.rect(23, 6, 40, 24, AQUA)
        c.ellipse(31.5, 6, 8.5, 3, AQUA)
        c.poly([(23, 24), (40, 24), (35, 30), (28, 30)], AQUA)
        c.rect(25, 7, 26, 22, SKY)
        c.rect(23, 11, 40, 11, SKY)
        c.rect(23, 16, 40, 16, SEA)
        c.rect(23, 20, 40, 20, SEA)
        c.rect(25, 35, 38, 44, GREY)
        c.rect(27, 36, 29, 39, RED)
        c.rect(34, 36, 36, 39, SEA)
        c.rect(26, 45, 37, 46, METAL)
        for y in (50, 53, 56):
            c.rect(26, y, 37, y, GREY)
        c.poly([(45, 34), (50, 34), (49, 46), (46, 46)], WHITE)
        c.rect(43, 46, 51, 47, METAL)
        c.rect(43, 40, 44, 46, METAL)
        for y in (37, 40, 43):
            c.rect(45, y, 50, y, GREY)
    elif kind == 1:
        # Коробки с бумагой: две снизу, одна сверху открыта, из неё торчит пачка листов.
        for x0, y0, w, h, col in ((5, 40, 27, 22, BRASS), (33, 42, 25, 20, TAN), (15, 20, 28, 20, BRASS)):
            c.rect(x0, y0, x0 + w, y0 + h, col)
            c.rect(x0, y0, x0 + w, y0 + 1, SKIN if col == TAN else TAN)
            c.rect(x0, y0 + 5, x0 + w, y0 + 5, DARK)
            c.rect(x0 + w // 2 - 1, y0, x0 + w // 2 + 1, y0 + 9, GREY)
            c.rect(x0 + 3, y0 + 9, x0 + 10, y0 + 15, WHITE)
            c.rect(x0 + 4, y0 + 11, x0 + 8, y0 + 11, DARK)
            c.rect(x0 + 4, y0 + 13, x0 + 7, y0 + 13, GREY)
            c.rect(x0 + w - 8, y0 + 9, x0 + w - 4, y0 + 10, K)
        c.rect(18, 13, 39, 19, WHITE)
        for y in (14, 16, 18):
            c.rect(18, y, 39, y, GREY)
        c.poly([(11, 14), (15, 20), (15, 23), (9, 17)], BRASS)
        c.poly([(43, 20), (48, 13), (50, 16), (43, 23)], BRASS)
        c.rect(22, 9, 34, 12, WHITE)
        c.rect(22, 12, 34, 12, GREY)
    elif kind == 2:
        # Фикус: глиняный горшок, тонкий ствол, крупные листья ярусами.
        c.poly([(22, 46), (42, 46), (39, 62), (25, 62)], BRASS)
        c.rect(20, 44, 44, 47, TAN)
        c.rect(20, 47, 44, 47, DARK)
        c.rect(26, 50, 27, 59, TAN)
        c.rect(24, 42, 40, 43, DARK)
        c.line(32, 44, 31, 20, BRASS, 3)
        c.line(31, 30, 24, 24, BRASS, 2)
        c.line(31, 26, 39, 20, BRASS, 2)
        leaves = ((31, 8, 6, 7), (21, 15, 7, 5), (42, 13, 7, 5), (17, 26, 6, 5), (46, 24, 6, 5),
                  (26, 22, 6, 5), (37, 24, 6, 4), (22, 35, 6, 4), (41, 34, 6, 4), (31, 16, 5, 5))
        for lx, ly, rx, ry in leaves:
            c.ellipse(lx, ly, rx, ry, PLUM)
            c.ellipse(lx - 1, ly - 1, rx - 1.5, ry - 1.5, VIOLET)
            c.line(lx - rx + 2, ly, lx + rx - 3, ly - 1, PLUM, 1)
        c.set(29, 6, SKY)
        c.set(20, 13, SKY)
        c.set(41, 11, SKY)
    elif kind == 3:
        # Копир: тумба с лотками, пульт с экраном, приподнятая крышка, из щели летят листы.
        c.rect(12, 60, 16, 62, DARK)
        c.rect(44, 60, 48, 62, DARK)
        c.rect(10, 30, 50, 60, GREY)
        c.rect(10, 30, 50, 31, WHITE)
        for y in (42, 51):
            c.rect(12, y, 48, y, METAL)
            c.rect(26, y + 3, 34, y + 4, DARK)
        c.rect(8, 24, 52, 30, WHITE)
        c.rect(8, 29, 52, 30, METAL)
        c.poly([(8, 24), (50, 18), (52, 21), (10, 24)], DARK)
        c.poly([(8, 23), (50, 17), (50, 19), (8, 24)], WHITE)
        c.rect(34, 33, 47, 38, DARK)
        c.rect(35, 34, 41, 37, AQUA)
        c.set(36, 35, SKY)
        c.set(44, 35, RED)
        c.set(46, 35, GOLD)
        c.set(44, 37, VIOLET)
        c.rect(12, 34, 30, 36, K)
        c.poly([(50, 34), (60, 31), (60, 34), (50, 38)], METAL)
        # Листы: один выезжает, два в полёте.
        c.poly([(14, 35), (26, 35), (24, 38), (12, 39)], WHITE)
        c.poly([(40, 4), (52, 7), (50, 15), (38, 12)], WHITE)
        c.line(42, 8, 49, 10, GREY, 1)
        c.line(41, 11, 47, 12, GREY, 1)
        c.poly([(18, 6), (28, 3), (30, 10), (20, 13)], WHITE)
        c.line(21, 8, 27, 6, GREY, 1)
    elif kind == 4:
        # Сейф: стальной куб на ножках, дверца с лимбом, штурвал, петли, золотая табличка.
        c.rect(14, 59, 20, 62, DARK)
        c.rect(44, 59, 50, 62, DARK)
        c.rect(10, 16, 54, 59, METAL)
        c.rect(10, 16, 54, 17, GREY)
        c.rect(10, 16, 11, 59, GREY)
        c.rect(15, 21, 49, 54, DARK)
        c.rect(16, 22, 48, 53, METAL)
        c.rect(16, 22, 48, 22, WHITE)
        c.rect(16, 22, 16, 53, GREY)
        for y in (26, 46):
            c.rect(46, y, 50, y + 4, DARK)
        c.ellipse(25, 33, 6, 6, K)
        c.ellipse(25, 33, 5, 5, WHITE)
        c.ellipse(25, 33, 2, 2, DARK)
        for dx, dy in ((0, -4), (4, 0), (0, 4), (-4, 0)):
            c.set(25 + dx, 33 + dy, K)
        c.line(25, 33, 27, 30, RED, 1)
        c.ellipse(39, 38, 6, 6, DARK)
        for dx, dy in ((-6, 0), (6, 0), (0, -6), (0, 6)):
            c.line(39, 38, 39 + dx, 38 + dy, GOLD, 2)
        c.ellipse(39, 38, 2, 2, GOLD)
        c.rect(20, 46, 32, 50, GOLD)
        c.rect(22, 48, 30, 48, BRASS)
        for x, y in ((12, 19), (52, 19), (12, 57), (52, 57)):
            c.set(x, y, DARK)
    else:
        # Серверная стойка: высокий чёрный шкаф, ряды блоков с огоньками, пучок кабелей, сверху
        # красная мигалка.
        c.rect(17, 10, 46, 62, DARK)
        c.rect(17, 10, 46, 11, METAL)
        c.rect(17, 10, 18, 62, METAL)
        for i, y in enumerate(range(14, 56, 7)):
            c.rect(21, y, 43, y + 4, K)
            c.rect(21, y, 43, y, METAL)
            for x in range(23, 33, 2):
                c.set(x, y + 2, (VIOLET, AQUA, GOLD, VIOLET, AQUA)[(x + i) % 5])
            for x in range(35, 42, 2):
                c.rect(x, y + 2, x, y + 3, METAL)
            if i % 3 == 1:
                c.rect(23, y + 2, 26, y + 3, AQUA)
        c.line(40, 56, 44, 61, SEA, 2)
        c.line(36, 56, 39, 61, GOLD, 1)
        c.rect(15, 60, 48, 62, K)
        c.rect(27, 7, 36, 9, METAL)
        c.ellipse(31.5, 5, 4, 4, RED)
        c.rect(27, 6, 36, 7, RED)
        c.set(30, 3, WHITE)
        c.finish()
        # Лучи мигалки.
        for dx, dy in ((-8, -2), (8, -2), (-7, 2), (7, 2)):
            c.line(31.5 + dx, 4 + dy * 0.5, 31.5 + dx * 1.4, 4 + dy, GOLD, 1)
        return c
    return c.finish()


def key():
    """Ключ от кабинета, как в основе: золотой, с круглой головкой и бородкой, на кольце красная
    бирка с номером."""
    c = Canvas(32, 32)
    c.rect(13, 12, 28, 14, GOLD)
    c.rect(13, 12, 28, 12, WHITE)
    c.rect(22, 15, 23, 19, GOLD)
    c.rect(26, 15, 27, 17, GOLD)
    c.ellipse(9, 13, 5.5, 5.5, GOLD)
    c.ellipse(8, 13, 2, 2, None)
    c.line(8, 17, 11, 20, METAL, 1)
    c.poly([(8, 20), (15, 20), (18, 23), (18, 29), (8, 29)], RED)
    c.finish()
    c.rect(10, 23, 15, 23, WHITE)
    c.rect(10, 25, 14, 25, WHITE)
    c.rect(10, 27, 12, 27, WHITE)
    c.set(6, 10, WHITE)
    return c


def medkit():
    """Аптечка, как в основе: белый чемоданчик с тёмной ручкой и защёлками, красный крест."""
    c = Canvas(32, 32)
    c.rect(11, 5, 20, 7, DARK)
    c.rect(13, 7, 18, 7, None)
    c.rect(11, 8, 12, 10, DARK)
    c.rect(19, 8, 20, 10, DARK)
    c.rect(3, 11, 28, 28, WHITE)
    c.rect(3, 11, 28, 13, GREY)
    c.rect(7, 12, 9, 15, METAL)
    c.rect(22, 12, 24, 15, METAL)
    c.rect(13, 16, 18, 26, RED)
    c.rect(10, 19, 21, 23, RED)
    c.rect(4, 27, 27, 27, GREY)
    return c.finish()


def pistol(frame):
    """Степлер в руке снизу по центру, 128×96: закатанный рукав рубашки, голое предплечье с
    часами, кулак, красный степлер носиком вглубь (ось x=64, носик у верхнего края), большой
    палец лежит наискось на заднем краю крышки; кадр 1 со вспышкой и вылетевшей скобой."""
    c = Canvas(128, 96)
    # Предплечье и закатанный рукав: белый валик со складками.
    for y in range(64, 96):
        w = 13 + (y - 64) // 5
        for x in range(64 - w, 64 + w):
            c.set(x, y, SKIN if x < 64 + w - 4 else TAN)
    for y in range(80, 96):
        w = 20 + (y - 80) // 4
        for x in range(64 - w, 64 + w):
            fold = (y - 80) % 6 == 5
            c.set(x, y, GREY if fold or x > 64 + w - 5 else WHITE)
    c.rect(43, 80, 85, 81, GREY)
    # Часы на запястье: тёмный ремешок, золотой корпус, циферблат.
    c.rect(50, 64, 78, 69, DARK)
    c.rect(50, 64, 78, 64, METAL)
    c.rect(58, 62, 70, 71, GOLD)
    c.rect(60, 63, 68, 70, WHITE)
    c.line(64, 67, 64, 64, K, 1)
    c.line(64, 67, 66, 68, K, 1)
    c.rect(58, 71, 70, 71, BRASS)
    # Кулак: ладонь и четыре пальца с костяшками.
    c.ellipse(64, 56, 15, 9, SKIN)
    c.rect(50, 48, 78, 58, SKIN)
    for k in range(4):
        x0 = 50 + k * 7
        c.rect(x0, 42, x0 + 6, 50, SKIN)
        c.rect(x0 + 1, 42, x0 + 5, 42, WHITE)
        c.rect(x0 + 1, 50, x0 + 5, 51, TAN)
        if k:
            c.rect(x0, 43, x0, 54, TAN)
    c.rect(50, 57, 78, 58, TAN)
    # Степлер: стальное основание шире крышки, красная крышка сужается к носику, шарнир сзади.
    c.poly([(54, 42), (74, 42), (71, 5), (57, 5)], METAL)
    c.rect(57, 3, 71, 6, GREY)
    c.rect(60, 2, 68, 3, DARK)
    c.poly([(55, 38), (73, 38), (69, 8), (59, 8)], RED)
    c.poly([(57, 36), (60, 36), (61, 10), (60, 10)], WHITE)
    c.rect(59, 8, 69, 9, GOLD)
    c.line(71, 36, 68, 10, DARK, 1)
    c.ellipse(64, 40, 10, 3.5, DARK)
    c.rect(55, 39, 73, 39, K)
    # Крышка с деталями: тёмная вставка-упор и светлая табличка, чтобы степлер читался целиком.
    c.rect(61, 28, 67, 33, WHITE)
    c.rect(62, 30, 66, 30, GREY)
    c.rect(62, 32, 65, 32, GREY)
    c.rect(61, 14, 67, 16, DARK)
    # Большой палец лежит наискось слева на заднем краю крышки (короткий, не торчит вверх).
    c.poly([(49, 47), (55, 50), (64, 40), (59, 35)], SKIN)
    c.ellipse(61, 38, 3.5, 3.5, SKIN)
    c.rect(60, 36, 62, 38, WHITE)
    c.line(55, 50, 64, 41, TAN, 1)
    c.finish()
    if frame:
        c.ellipse(64, 0, 18, 9, GOLD)
        c.ellipse(64, 0, 10, 5, WHITE)
        # Скоба в полёте и искры.
        c.rect(59, 12, 69, 13, WHITE)
        c.rect(59, 12, 60, 16, WHITE)
        c.rect(68, 12, 69, 16, WHITE)
        for dx in (-22, -14, 14, 22):
            c.line(64 + dx, 8, 64 + dx * 1.25, 12, GOLD, 1)
    return c


def face(mode):
    """Лицо клерка для HUD, 32×32: чуб, очки в тёмной оправе, воротник и красный галстук; 0 прямо,
    1 глянул влево, 2 вправо, 3 больно (очки набок, линза треснула), 4 ухмылка."""
    c = Canvas(32, 32)
    # Воротник и узел галстука.
    c.poly([(5, 31), (9, 25), (23, 25), (27, 31)], WHITE)
    c.rect(13, 22, 19, 27, TAN)
    c.poly([(9, 25), (15, 31), (10, 31)], GREY)
    c.poly([(23, 25), (17, 31), (22, 31)], GREY)
    c.poly([(14, 26), (18, 26), (19, 31), (13, 31)], RED)
    # Голова, уши, волосы с чубом.
    c.ellipse(16, 14, 9.5, 10.5, SKIN)
    c.rect(5, 13, 6, 17, SKIN)
    c.rect(26, 13, 27, 17, SKIN)
    for y in range(2, 12):
        for x in range(5, 28):
            if c.get(x, y) == SKIN and (y <= 6 or (x <= 8 and y <= 11) or (x >= 24 and y <= 11)):
                c.set(x, y, DARK)
    c.poly([(9, 7), (20, 7), (14, 10), (10, 9)], DARK)
    c.ellipse(15, 3, 8, 2, DARK)
    c.line(18, 4, 23, 6, METAL, 1)
    c.finish()
    look = {0: 0, 1: -1, 2: 1, 3: 0, 4: 0}[mode]
    # Очки: линзы в оправе, перемычка, дужки.
    for e in (-5, 5):
        drop = 2 if (mode == 3 and e > 0) else 0
        x0 = 16 + e - 3
        c.rect(x0 - 1, 11 + drop, x0 + 6, 17 + drop, K)
        c.rect(x0, 12 + drop, x0 + 5, 16 + drop, SKY)
        c.set(x0, 12 + drop, WHITE)
        if mode == 3:
            if e > 0:
                c.line(x0, 16 + drop, x0 + 5, 12 + drop, K, 1)
                c.set(x0 + 2, 13 + drop, K)
            else:
                c.line(x0 + 1, 13, x0 + 4, 15, K, 1)
                c.line(x0 + 1, 15, x0 + 4, 13, K, 1)
        else:
            c.rect(x0 + 2 + look, 13, x0 + 3 + look, 15, K)
    c.rect(14, 13, 17, 13, K)
    c.rect(15, 17, 16, 19, TAN)
    c.rect(11, 9, 13, 9, K)
    c.rect(19, 9, 21, 9, K)
    if mode == 4:
        c.rect(11, 21, 21, 23, WHITE)
        c.rect(11, 21, 21, 21, K)
        c.rect(12, 23, 20, 23, K)
        c.set(10, 20, K)
        c.set(22, 20, K)
    elif mode == 3:
        c.ellipse(16, 22, 3, 1.8, K)
        c.rect(15, 23, 17, 23, RED)
        c.rect(7, 18, 8, 20, RED)
        c.set(9, 21, RED)
    else:
        c.rect(13, 22, 19, 22, K)
        c.set(20, 21, K)
    return c


def textures():
    return {"wall_planks": tex_partition(), "wall_stone": tex_archive(), "wall_pillar": tex_pillar(),
            "wall_exit": tex_exit(), "wall_cabin": tex_cabin(), "wall_hull": tex_window(), "wall_cargo": tex_boxes(),
            "floor_planks": tex_floor(), "floor_stone": tex_floor_tile(), "floor_carpet": tex_floor_laminate(),
            "ceiling_beams": tex_ceiling()}


def sprites():
    out = {"shot": shot(), "bullet": bullet(), "key": key(), "medkit": medkit(),
           "hold_decor": strip([decor(k) for k in range(6)]),
           "pistol": strip([pistol(0), pistol(1)]),
           "face": strip([face(i) for i in range(5)])}
    out.update(worker_strips())
    out.update(textures())
    return out


if __name__ == "__main__":
    if "--preview" in sys.argv:
        office16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], office16.shaded(sprites()))
