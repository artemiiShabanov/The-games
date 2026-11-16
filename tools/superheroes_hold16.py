#!/usr/bin/env python3
"""Набор «Супергерои» для шутера × 16/32-bit «до выхода» (#137), зеркало `space_hold16.py` и
`pixel_hold16.py`: те же ключи, размеры холстов, число и порядок кадров и точки опоры (ноги
врагов на 61-62 строке по центру кадра, излучатель перчатки вверх по оси 64, текстуры 64×64 со
швом по краю).

Тема: логово злодея-учёного в небоскрёбе, дорога к лифту. Стены: кирпич техэтажа с плакатом
злодея, плиты лаборатории с колбой и манометром, клёпаная ферма-колонна, двери лифта со
стрелочным указателем, стена слежения из шести мониторов над пультом, окно на закатный город с
дирижаблем, ячейки зарядки роботов. Полы: бетон крыши, резина лаборатории в пупырышек, красный
ковёр кабинета. Враги: робот-приспешник с рукой-пушкой (`skel_*`, бочонок с одним глазом из
основы) и робот с клинком (`cut_*`, узкий корпус, шлем с гребнем и красной щелью визора).
Перчатка-бластер героя, энергозаряд, ключ, аптечка и выстрел из основы, лицо героя в маске.

    python3 tools/superheroes_hold16.py --preview out.png [--keys=a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import superheroes16  # noqa: E402
from superheroes16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS,  # noqa: E402
                           METAL, DARK, RED, VIOLET, PLUM, STAR7, _stamp)

T = 64


# --- Текстуры ----------------------------------------------------------------------------------

def _bricks(c, y0=0, y1=T - 1, seed=401):
    """Кирпич 16×8 со сдвигом ряда на полкирпича, как в крыше основы: тёплый, шов тёмный, по
    верху кирпича светлая кромка, часть кирпичей обожжена темнее."""
    rng = random.Random(seed)
    tone = {}
    for y in range(y0, y1 + 1):
        row = y // 8
        off = 8 if row % 2 else 0
        for x in range(T):
            bx = ((x + off) % T) // 16
            px, py = (x + off) % 16, y % 8
            kind = tone.setdefault((row, bx), rng.random())
            col = TAN
            if px == 0 or py == 0:
                col = DARK
            elif py == 1 and kind > 0.3:
                col = SKIN
            elif kind < 0.2:
                col = BRASS if (py != 7) else DARK
            elif py == 7 and (x + y) % 3 == 0:
                col = BRASS
            c.set(x, y, col)


def tex_brick():
    """Основная стена: кирпич техэтажа под бетонным карнизом, плакат злодея с оторванным углом,
    кабель в трубе с распределительной коробкой, звезда героя мелом, снизу бетонный цоколь."""
    rng = random.Random(402)
    c = Canvas(T, T)
    _bricks(c)
    # Карниз.
    c.rect(0, 0, T - 1, 5, GREY)
    c.rect(0, 0, T - 1, 0, WHITE)
    c.rect(0, 4, T - 1, 4, METAL)
    c.rect(0, 5, T - 1, 5, DARK)
    for x in range(T):
        if (x * 5) % 13 < 2:
            c.set(x, 2, METAL)
        if x % 32 == 20:
            c.rect(x, 1, x, 4, METAL)
    # Плакат: персиковая бумага, на коралловом круге голова в зелёном шлеме с красным визором,
    # ниже красная плашка со «строчками». Правый нижний угол оторван.
    c.rect(7, 12, 27, 39, K)
    c.rect(8, 13, 26, 38, SKY)
    c.ellipse(17, 22, 7.5, 7.5, AQUA)
    c.ellipse(17, 21, 4.5, 5, VIOLET)
    c.rect(13, 21, 21, 26, VIOLET)
    c.rect(12, 26, 22, 28, PLUM)
    c.rect(14, 20, 20, 21, RED)
    c.poly([(16, 15), (17, 11), (18, 15)], PLUM)
    c.rect(9, 30, 25, 34, RED)
    for x in range(11, 24, 2):
        c.set(x, 32, WHITE)
    c.rect(11, 36, 22, 36, TAN)
    for y in range(33, 40):
        for x in range(20, 28):
            if (x - 20) + (y - 33) >= 9:
                row = y // 8
                off = 8 if row % 2 else 0
                px, py = (x + off) % 16, y % 8
                c.set(x, y, DARK if px == 0 or py == 0 else TAN)
    c.line(22, 39, 27, 34, WHITE, 1)
    # Труба с кабелем и коробка с лампой.
    c.rect(43, 6, 45, 28, METAL)
    c.rect(43, 6, 43, 28, GREY)
    c.rect(46, 6, 46, 28, K)
    for y in (11, 22):
        c.rect(42, y, 46, y + 1, DARK)
    c.rect(39, 28, 50, 38, DARK)
    c.rect(40, 29, 49, 37, METAL)
    c.rect(40, 29, 49, 29, GREY)
    c.rect(42, 32, 43, 33, GOLD)
    c.rect(46, 32, 47, 33, RED)
    c.rect(42, 35, 47, 35, DARK)
    # Звезда героя мелом.
    _stamp(c, 51, 42, STAR7, GOLD)
    # Цоколь.
    c.rect(0, 54, T - 1, T - 1, GREY)
    c.rect(0, 54, T - 1, 54, WHITE)
    c.rect(0, 55, T - 1, 55, METAL)
    c.rect(0, 53, T - 1, 53, K)
    for _ in range(26):
        c.set(rng.randrange(T), rng.randrange(56, T - 1), METAL)
    for x in (13, 45):
        c.rect(x, 56, x, T - 1, METAL)
    c.rect(0, T - 1, T - 1, T - 1, DARK)
    return c


def tex_lab():
    """Лаборатория: зелёно-серые плиты 32×32 на заклёпках, справа колба с коралловой жидкостью
    и пузырями, слева манометр, знак опасности и провисший кабель, понизу жёлто-чёрная полоса."""
    rng = random.Random(403)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 32, y % 32
            col = VIOLET
            if px in (0, 31) or py in (0, 31):
                col = DARK
            elif px == 1 or py == 1:
                col = GREY
            elif px == 30 or py == 30:
                col = PLUM
            c.set(x, y, col)
    for by in (0, 32):
        for bx in (0, 32):
            for dx, dy in ((4, 4), (27, 4), (4, 27), (27, 27)):
                c.set(bx + dx, by + dy, DARK)
                c.set(bx + dx, by + dy - 1, GREY)
    for _ in range(30):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == VIOLET:
            c.set(x, y, PLUM)
    # Колба: стальные крышки, стекло с бликом слева, жидкость до уровня, пузыри.
    c.rect(38, 7, 57, 50, K)
    c.rect(39, 8, 56, 12, METAL)
    c.rect(39, 8, 56, 8, GREY)
    c.rect(39, 45, 56, 49, METAL)
    c.rect(39, 45, 56, 45, GREY)
    c.rect(39, 49, 56, 49, DARK)
    for x in (41, 47, 54):
        c.set(x, 10, DARK)
        c.set(x, 47, DARK)
    c.rect(40, 13, 55, 44, NAVY)
    c.rect(40, 19, 55, 44, AQUA)
    c.rect(40, 19, 55, 19, SKY)
    c.rect(41, 14, 42, 43, SKY)
    c.rect(54, 20, 55, 44, RED)
    for x, y, r in ((47, 38, 1.6), (51, 30, 1.2), (45, 26, 1.0), (50, 22, 0.8)):
        c.ellipse(x, y, r, r, SKY)
        c.set(x, y - 1, WHITE)
    c.rect(46, 3, 49, 7, DARK)
    c.rect(47, 0, 48, 3, METAL)
    # Манометр.
    c.ellipse(15, 15, 8, 8, K)
    c.ellipse(15, 15, 7, 7, METAL)
    c.ellipse(15, 15, 5.5, 5.5, WHITE)
    for a in (200, 240, 270, 300, 340):
        c.set(15 + 4.6 * math.cos(math.radians(a)), 15 + 4.6 * math.sin(math.radians(a)), DARK)
    c.set(19, 13, RED)
    c.set(19, 14, RED)
    c.line(15, 15, 18, 12, RED, 1)
    c.set(15, 15, K)
    # Знак опасности.
    c.poly([(8, 46), (22, 46), (15, 34)], K)
    c.poly([(10, 45), (20, 45), (15, 36)], GOLD)
    c.rect(15, 39, 15, 42, K)
    c.set(15, 44, K)
    # Кабель от манометра к колбе, провисает.
    for x in range(22, 39):
        k = (x - 22) / 16.0
        y = 17 + 12 * math.sin(k * math.pi) + 26 * k * 0
        c.set(x, y, K)
        c.set(x, y + 1, RED)
    # Полоса опасности понизу: диагональ с шагом 8 смыкается по краю.
    c.rect(0, 55, T - 1, 55, K)
    for y in range(56, 62):
        for x in range(T):
            c.set(x, y, GOLD if ((x + y) // 4) % 2 == 0 else K)
    c.rect(0, 62, T - 1, T - 1, DARK)
    c.rect(0, 62, T - 1, 62, METAL)
    return c


def tex_pillar():
    """Колонна: клёпаная стальная ферма. Две полки с рядами заклёпок по краям, между ними тёмный
    просвет с крест-накрест раскосами и косынками, пояс посередине, шевроны опасности внизу."""
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, K)
    # Просвет: за фермой темно, редкие огни шахты.
    for y in range(T):
        for x in range(13, 51):
            c.set(x, y, DARK if (x * 3 + y) % 11 else K)
    # Раскосы: два креста по 32 в высоту.
    for y0 in (0, 32):
        for t in range(-2, 3):
            c.line(13, y0 + t, 50, y0 + 31 + t, METAL if t < 2 else K, 1)
            c.line(50, y0 + t, 13, y0 + 31 + t, METAL if t < 2 else K, 1)
        c.line(13, y0 - 2, 50, y0 + 29, GREY, 1)
        c.line(50, y0 - 2, 13, y0 + 29, GREY, 1)
        # Косынка в перекрестье.
        c.rect(27, y0 + 11, 36, y0 + 20, K)
        c.rect(28, y0 + 12, 35, y0 + 19, METAL)
        c.rect(28, y0 + 12, 35, y0 + 12, GREY)
        for dx, dy in ((29, 13), (34, 13), (29, 18), (34, 18)):
            c.set(dx, y0 + dy, DARK)
    # Полки.
    for x0 in (0, 51):
        c.rect(x0, 0, x0 + 12, T - 1, METAL)
        c.rect(x0 + 1, 0, x0 + 2, T - 1, GREY)
        c.rect(x0 + 3, 0, x0 + 3, T - 1, WHITE)
        c.rect(x0 + 11, 0, x0 + 12, T - 1, DARK)
        c.rect(x0, 0, x0, T - 1, K)
        for y in range(3, T, 8):
            c.set(x0 + 6, y, DARK)
            c.set(x0 + 6, y - 1, WHITE)
            c.set(x0 + 9, y + 4, DARK)
            c.set(x0 + 9, y + 3, GREY)
    c.rect(12, 0, 12, T - 1, K)
    c.rect(51, 0, 51, T - 1, K)
    # Пояс и шевроны.
    c.rect(0, 29, T - 1, 34, GREY)
    c.rect(0, 29, T - 1, 29, WHITE)
    c.rect(0, 34, T - 1, 34, K)
    c.rect(0, 28, T - 1, 28, K)
    for x in range(3, T, 8):
        c.set(x, 31, DARK)
        c.set(x, 32, METAL)
    for x0 in (1, 52):
        for y in range(48, 57):
            for x in range(x0, x0 + 11):
                c.set(x, y, GOLD if ((abs(x - x0 - 5) + y) // 3) % 2 == 0 else K)
        c.rect(x0, 47, x0 + 10, 47, K)
        c.rect(x0, 57, x0 + 10, 57, K)
    return c


def tex_exit():
    """Выход: двери лифта. Стальные створки с тиснёными стрелками вверх и швом посередине,
    латунный наличник, сверху стрелочный указатель этажа полукругом и две жёлтые стрелки,
    справа кнопка вызова."""
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, GREY)
    for y in range(T):
        for x in range(T):
            if (x * 7 + y * 3) % 17 == 0:
                c.set(x, y, METAL)
    c.rect(0, 0, 0, T - 1, METAL)
    c.rect(T - 1, 0, T - 1, T - 1, METAL)
    # Шапка с указателем.
    c.rect(4, 1, 59, 14, K)
    c.rect(5, 2, 58, 13, DARK)
    c.ellipse(32, 13, 11, 10, BRASS)
    c.ellipse(32, 13, 9.5, 8.5, SKY)
    c.rect(20, 14, 44, 16, None)
    for a in range(180, 361, 30):
        c.set(32 + 7.5 * math.cos(math.radians(a)), 13 + 6.5 * math.sin(math.radians(a)), DARK)
    c.line(32, 12, 37, 6, RED, 1)
    c.line(32, 12, 36, 6, RED, 1)
    c.ellipse(32, 12, 1.5, 1.5, K)
    for cx in (12, 52):
        c.poly([(cx - 5, 10), (cx + 5, 10), (cx, 4)], GOLD)
        c.rect(cx - 1, 10, cx + 1, 12, GOLD)
        c.set(cx, 5, WHITE)
    # Наличник.
    c.rect(4, 14, 59, T - 1, BRASS)
    c.rect(4, 14, 59, 14, GOLD)
    c.rect(4, 14, 5, T - 1, GOLD)
    c.rect(7, 16, 56, 16, K)
    c.rect(7, 16, 7, T - 1, K)
    c.rect(56, 16, 56, T - 1, K)
    # Створки: шлифованная сталь, рамка-тиснение, стрелка.
    for y in range(17, T):
        for x in range(8, 56):
            col = METAL
            if x % 4 == 1:
                col = GREY
            if y == 17:
                col = DARK
            c.set(x, y, col)
    for x0 in (10, 34):
        c.rect(x0, 20, x0 + 19, 58, DARK)
        c.rect(x0 + 1, 21, x0 + 19, 58, GREY)
        c.rect(x0 + 1, 21, x0 + 18, 57, METAL)
        for y in range(22, 57, 3):
            c.rect(x0 + 2, y, x0 + 17, y, GREY)
        ax = x0 + 9.5
        c.poly([(ax - 6, 38), (ax + 6, 38), (ax, 27)], K)
        c.rect(ax - 2, 38, ax + 2, 49, K)
        c.poly([(ax - 4, 37), (ax + 4, 37), (ax, 29)], SKY)
        c.rect(ax - 1, 37, ax + 1, 48, SKY)
        c.set(ax, 30, WHITE)
    c.rect(31, 17, 32, T - 1, K)
    c.rect(30, 18, 30, T - 1, WHITE)
    c.rect(33, 18, 33, T - 1, DARK)
    # Порог.
    c.rect(4, 61, 59, T - 1, DARK)
    c.rect(4, 61, 59, 61, GOLD)
    for x in range(6, 58, 4):
        c.set(x, 62, METAL)
    # Кнопка вызова.
    c.rect(60, 32, 62, 43, K)
    c.rect(60, 33, 62, 42, DARK)
    c.rect(61, 35, 61, 36, GOLD)
    c.rect(61, 39, 61, 40, RED)
    return c


def _monitor(c, x0, y0, kind):
    """Монитор 18×15 со скруглённым кинескопом и картинкой по номеру."""
    c.rect(x0, y0, x0 + 17, y0 + 14, K)
    c.rect(x0 + 1, y0 + 1, x0 + 16, y0 + 13, METAL)
    c.rect(x0 + 1, y0 + 1, x0 + 16, y0 + 1, GREY)
    c.rect(x0 + 2, y0 + 2, x0 + 15, y0 + 11, K)
    sx, sy = x0 + 3, y0 + 3
    if kind == 0:
        # Герой в прицеле: синий торс, жёлтый плащ, красное перекрестье.
        c.rect(sx, sy, sx + 11, sy + 7, NAVY)
        c.rect(sx + 4, sy + 3, sx + 7, sy + 7, SEA)
        c.rect(sx + 2, sy + 4, sx + 3, sy + 7, GOLD)
        c.rect(sx + 5, sy + 1, sx + 6, sy + 2, SKIN)
        c.rect(sx + 5, sy, sx + 7, sy, DARK)
        c.rect(sx, sy + 3, sx + 11, sy + 3, RED)
        c.rect(sx + 9, sy, sx + 9, sy + 7, RED)
    elif kind == 1:
        # Город: закат и силуэты.
        c.rect(sx, sy, sx + 11, sy + 2, SEA)
        c.rect(sx, sy + 3, sx + 11, sy + 4, AQUA)
        c.rect(sx, sy + 5, sx + 11, sy + 7, SKY)
        for x, h in ((0, 3), (2, 5), (5, 2), (7, 6), (10, 4)):
            c.rect(sx + x, sy + 8 - h, sx + x + 1, sy + 7, NAVY)
        c.set(sx + 7, sy + 4, GOLD)
        c.set(sx + 2, sy + 5, GOLD)
    elif kind == 2:
        # Помехи.
        for y in range(8):
            for x in range(12):
                c.set(sx + x, sy + y, (GREY, DARK, WHITE, METAL)[(x * 7 + y * 13 + x * y) % 4])
    elif kind == 3:
        # Кривая на зелёной сетке.
        c.rect(sx, sy, sx + 11, sy + 7, PLUM)
        for x in range(0, 12, 4):
            c.rect(sx + x, sy, sx + x, sy + 7, DARK)
        pts = (6, 5, 6, 3, 1, 4, 5, 2, 3, 1, 2, 4)
        for x, y in enumerate(pts):
            c.set(sx + x, sy + y, GOLD)
            c.set(sx + x, sy + y + 1, VIOLET)
    elif kind == 4:
        # Тревога: красный экран с восклицательным знаком в треугольнике.
        c.rect(sx, sy, sx + 11, sy + 7, RED)
        c.poly([(sx + 2, sy + 7), (sx + 9, sy + 7), (sx + 5.5, sy)], GOLD)
        c.rect(sx + 5, sy + 2, sx + 6, sy + 4, K)
        c.rect(sx + 5, sy + 6, sx + 6, sy + 6, K)
    else:
        # Карта: синяя сетка улиц и красная метка.
        c.rect(sx, sy, sx + 11, sy + 7, NAVY)
        for x in (2, 6, 10):
            c.rect(sx + x, sy, sx + x, sy + 7, SEA)
        for y in (2, 5):
            c.rect(sx, sy + y, sx + 11, sy + y, SEA)
        c.rect(sx + 6, sy + 2, sx + 7, sy + 3, RED)
        c.set(sx + 7, sy + 1, WHITE)
    # Блик стекла и лампочка питания.
    c.set(x0 + 3, y0 + 3, WHITE)
    c.set(x0 + 4, y0 + 3, WHITE)
    c.set(x0 + 3, y0 + 4, WHITE)
    c.set(x0 + 14, y0 + 12, RED if kind == 2 else GOLD)
    c.rect(x0 + 3, y0 + 12, x0 + 8, y0 + 12, DARK)


def tex_cabin():
    """Командная: стена слежения. Шесть мониторов в два ряда (герой в прицеле, город, помехи,
    кривая, тревога, карта) на тёмной панели, под ними наклонный пульт с кнопками, ползунками и
    большой красной кнопкой."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = DARK
            if x % 32 == 0:
                col = K
            elif x % 32 == 1:
                col = METAL
            elif (x + y * 2) % 9 == 0:
                col = K
            c.set(x, y, col)
    c.rect(0, 0, T - 1, 1, METAL)
    c.rect(0, 2, T - 1, 2, K)
    for row, y0 in enumerate((4, 22)):
        for col_, x0 in enumerate((3, 23, 43)):
            _monitor(c, x0, y0, row * 3 + col_)
    # Пульт: светлая столешница с фаской.
    c.rect(0, 40, T - 1, 40, K)
    c.rect(0, 41, T - 1, 42, WHITE)
    c.rect(0, 43, T - 1, 53, GREY)
    c.rect(0, 54, T - 1, 54, METAL)
    c.rect(0, 55, T - 1, 55, K)
    for i, x in enumerate(range(3, 28, 4)):
        col = (RED, GOLD, SKY, VIOLET, GOLD, SEA, RED)[i]
        c.rect(x, 45, x + 2, 46, col)
        c.rect(x, 47, x + 2, 47, DARK)
    for x in (4, 10, 16, 22):
        c.rect(x, 49, x, 53, DARK)
        c.rect(x - 1, 50 + (x // 6) % 3, x + 1, 51 + (x // 6) % 3, WHITE)
    # Большая красная кнопка под колпаком и ключ-тумблер.
    c.ellipse(40, 48, 6, 4.5, K)
    c.ellipse(40, 48, 5, 3.5, GOLD)
    c.ellipse(40, 47, 3.6, 2.6, RED)
    c.set(39, 46, WHITE)
    c.rect(52, 44, 59, 52, DARK)
    c.rect(53, 45, 58, 51, METAL)
    c.line(55, 49, 57, 45, K, 1)
    c.set(57, 44, RED)
    c.set(54, 50, GOLD)
    # Тумба.
    c.rect(0, 56, T - 1, T - 1, METAL)
    c.rect(0, 56, T - 1, 56, GREY)
    for x in range(4, T, 16):
        for y in (58, 60):
            c.rect(x, y, x + 7, y, DARK)
    c.rect(0, T - 1, T - 1, T - 1, DARK)
    return c


def tex_window():
    """Окно пентхауса в кирпичной стене: закат в четыре полосы с дрожанием на границах, солнце
    у горизонта, небоскрёбы с огнями, дирижабль; тёмная рама с переплётом и бетонный подоконник."""
    c = tex_brick()
    rng = random.Random(404)
    c.rect(3, 7, 60, 50, K)
    c.rect(4, 8, 59, 49, DARK)
    c.rect(4, 8, 59, 8, METAL)
    x0, x1, y0, y1 = 6, 57, 10, 46
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            k = y - y0
            band = (NAVY, SEA, AQUA, SKY)[min(k // 8, 3)]
            if k < 24 and k % 8 >= 6 and (x + y) % 2 == 0:
                band = (SEA, AQUA, SKY)[k // 8]
            c.set(x, y, band)
    # Звёзды и облако.
    for x, y in ((9, 11), (21, 12), (40, 11), (52, 14), (30, 13)):
        c.set(x, y, WHITE)
    c.rect(36, 24, 52, 24, AQUA)
    c.rect(40, 23, 49, 23, AQUA)
    c.rect(38, 25, 50, 25, SKY)
    # Солнце садится за дома.
    c.ellipse(20, 44, 7, 7, WHITE)
    for y in range(36, 47):
        for x in range(12, 29):
            if c.get(x, y) == WHITE and (x - 20) ** 2 + (y - 44) ** 2 > 25:
                c.set(x, y, GOLD)
    # Дирижабль.
    c.ellipse(23, 18, 7, 2.6, GREY)
    c.rect(18, 19, 28, 20, METAL)
    c.poly([(15, 18), (13, 15), (13, 21)], RED)
    c.rect(21, 21, 25, 22, DARK)
    c.rect(19, 17, 27, 17, WHITE)
    # Дальние дома в дымке и ближние с окнами.
    for x, w, h in ((6, 6, 9), (15, 5, 13), (27, 7, 10), (38, 5, 16), (47, 6, 8), (53, 5, 12)):
        c.rect(x, y1 - h, min(x + w, x1), y1, METAL)
    for x, w, h in ((8, 7, 6), (22, 6, 15), (31, 8, 8), (43, 7, 19), (52, 6, 7)):
        c.rect(x, y1 - h, min(x + w, x1), y1, NAVY)
        c.rect(x, y1 - h, x, y1, AQUA)
        for wy in range(y1 - h + 2, y1, 3):
            for wx in range(x + 2, min(x + w, x1), 2):
                if rng.random() < 0.5:
                    c.set(wx, wy, GOLD)
    c.rect(46, y1 - 23, 46, y1 - 20, NAVY)
    c.set(46, y1 - 24, RED)
    # Переплёт и блики стекла.
    c.rect(31, 9, 32, 48, DARK)
    c.rect(31, 9, 31, 48, METAL)
    c.rect(5, 28, 58, 29, DARK)
    c.rect(5, 28, 58, 28, METAL)
    c.rect(4, 47, 59, 49, DARK)
    for d in range(7):
        c.set(9 + d, 19 - d, WHITE)
        c.set(37 + d, 21 - d, WHITE)
    # Подоконник.
    c.rect(1, 50, 62, 53, GREY)
    c.rect(1, 50, 62, 50, WHITE)
    c.rect(1, 53, 62, 53, METAL)
    c.rect(1, 54, 62, 54, K)
    return c


def _pod_robot(c, cx, y0, awake):
    """Приспешник в ячейке: бочонок с обручами и глазницей, в тени; у бодрого горит глаз."""
    tmp = Canvas(T, T)
    tmp.ellipse(cx, y0 + 14, 10, 20, PLUM)
    for y in range(T):
        for x in range(T):
            if tmp.px[y][x] is not None and y0 <= y <= y0 + 28:
                col = PLUM
                if x <= cx - 3 and x >= cx - 6:
                    col = VIOLET
                if y in (y0 + 5, y0 + 23):
                    col = DARK
                c.set(x, y, col)
    for x in range(cx - 8, cx + 9):
        if tmp.get(x, y0) is not None:
            c.set(x, y0, METAL)
    c.ellipse(cx, y0 + 11, 4.5, 4.5, K)
    c.ellipse(cx, y0 + 11, 3, 3, RED if awake else DARK)
    if awake:
        c.set(cx - 1, y0 + 10, WHITE)
    else:
        c.rect(cx - 2, y0 + 11, cx + 2, y0 + 11, METAL)
    # Антенна, ноги-поршни, опущенные клешни.
    c.line(cx + 2, y0 - 1, cx + 4, y0 - 5, METAL, 1)
    c.set(cx + 4, y0 - 6, RED if awake else METAL)
    for s in (-1, 1):
        c.rect(cx + s * 4 - 1, y0 + 29, cx + s * 4 + 1, y0 + 36, METAL)
        c.rect(cx + s * 4 - 2, y0 + 37, cx + s * 4 + 2, y0 + 38, K)
        c.rect(cx + s * 11, y0 + 12, cx + s * 11, y0 + 22, METAL)
        c.rect(cx + s * 11 - 1, y0 + 23, cx + s * 11 + 1, y0 + 25, GREY)
        c.set(cx + s * 11, y0 + 25, K)


def tex_pods():
    """Ячейки зарядки: две ниши в стальной раме, в каждой приспешник на подзарядке (левый спит,
    правый уже открыл глаз), сверху номер и лампа, кабель к макушке, понизу полоса опасности."""
    c = Canvas(T, T)
    for bx in (0, 32):
        awake = bx == 32
        c.rect(bx, 0, bx + 31, T - 1, METAL)
        c.rect(bx, 0, bx, T - 1, K)
        c.rect(bx + 31, 0, bx + 31, T - 1, DARK)
        c.rect(bx + 1, 0, bx + 1, T - 1, GREY)
        # Шапка с номером и лампой.
        c.rect(bx + 1, 0, bx + 30, 0, GREY)
        c.rect(bx + 4, 2, bx + 14, 6, WHITE)
        c.rect(bx + 4, 2, bx + 14, 2, GREY)
        for x in ((6, 9) if not awake else (6, 8, 10)):
            c.rect(bx + x, 3, bx + x, 5, K)
        if awake:
            c.set(bx + 11, 3, K)
            c.set(bx + 11, 5, K)
        c.rect(bx + 23, 2, bx + 27, 6, K)
        c.rect(bx + 24, 3, bx + 26, 5, RED if awake else GOLD)
        c.set(bx + 24, 3, WHITE)
        # Ниша.
        c.rect(bx + 3, 8, bx + 28, 56, K)
        for y in range(9, 56):
            for x in range(bx + 4, bx + 28):
                c.set(x, y, DARK if (x + y) % 6 == 0 or x in (bx + 4, bx + 27) else K)
        c.rect(bx + 4, 9, bx + 27, 9, DARK)
        # Кабель от потолка ниши к макушке.
        c.line(bx + 10, 9, bx + 14, 15, GOLD if awake else BRASS, 1)
        c.line(bx + 11, 9, bx + 15, 15, K, 1)
        _pod_robot(c, bx + 16, 17, awake)
        # Захваты по бокам.
        for x in (bx + 4, bx + 25):
            c.rect(x, 30, x + 2, 33, GREY)
            c.rect(x, 33, x + 2, 33, DARK)
        for x, y in ((bx + 2, 12), (bx + 29, 12), (bx + 2, 50), (bx + 29, 50), (bx + 2, 31), (bx + 29, 31)):
            c.set(x, y, DARK)
    c.rect(0, 57, T - 1, 57, K)
    for y in range(58, 63):
        for x in range(T):
            c.set(x, y, GOLD if ((x + y) // 4) % 2 == 0 else K)
    c.rect(0, 63, T - 1, 63, DARK)
    return c


def tex_floor():
    """Бетон крыши: плиты 32×32 с тёмным швом и светлой фаской, крапины, трещина, пятна
    битума, в углах плит дюбели."""
    rng = random.Random(405)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 32, y % 32
            col = GREY
            if px == 0 or py == 0:
                col = DARK
            elif px == 1 or py == 1:
                col = WHITE
            elif px == 31 or py == 31:
                col = METAL
            c.set(x, y, col)
    for _ in range(90):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == GREY:
            c.set(x, y, METAL if rng.random() < 0.75 else WHITE)
    # Трещины: ломаные внутри плит.
    for sx, sy, n in ((6, 9, 14), (44, 38, 16), (40, 6, 8)):
        x, y = float(sx), float(sy)
        for _ in range(n):
            if c.get(int(x), int(y)) in (GREY, METAL, WHITE) and int(x) % 32 > 1 and int(y) % 32 > 1:
                c.set(x, y, DARK)
            x += rng.choice((1, 1, 0))
            y += rng.choice((-1, 0, 1, 1))
    # Пятна битума.
    for x, y, r in ((20, 22, 3), (52, 14, 2), (12, 50, 2.5)):
        for yy in range(int(y - r), int(y + r) + 1):
            for xx in range(int(x - r - 1), int(x + r + 2)):
                if ((xx - x) / (r + 1)) ** 2 + ((yy - y) / r) ** 2 <= 1.0 and (xx + yy) % 2 == 0:
                    c.set(xx, yy, METAL)
    for bx in (0, 32):
        for by in (0, 32):
            for dx, dy in ((4, 4), (28, 4), (4, 28), (28, 28)):
                c.set(bx + dx, by + dy, DARK)
                c.set(bx + dx + 1, by + dy, WHITE)
    return c


def tex_floor_studs():
    """Пол лаборатории: зелёно-серая резина в круглый пупырышек, ряды со сдвигом, листы 32×32
    с тёмным швом."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 32, y % 32
            col = PLUM
            if px == 0 or py == 0:
                col = K
            elif px == 1 or py == 1:
                col = DARK
            c.set(x, y, col)
    for row, y in enumerate(range(5, T, 8)):
        for x in range(5 + (4 if row % 2 else 0), T, 8):
            if x % 32 < 3 or y % 32 < 3:
                continue
            c.rect(x - 1, y - 1, x + 1, y + 1, VIOLET)
            c.set(x - 1, y - 1, GREY)
            c.set(x + 1, y + 1, DARK)
            c.set(x + 2, y + 1, DARK)
            c.set(x + 1, y + 2, DARK)
            c.set(x, y + 2, DARK)
    return c


def tex_floor_carpet():
    """Ковёр кабинета: красный ворс, ромбы 16×16 жёлтой нитью, в ромбах через один звезда-крест
    и тёмная розетка."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 16, y % 16
            d = abs(px - 8) + abs(py - 8)
            cell = (x // 16 + y // 16) % 2
            col = RED
            if d == 8:
                col = BRASS
            elif d == 7:
                col = DARK
            elif cell == 0 and (px == 8 or py == 8) and d <= 3:
                col = GOLD
            elif cell == 0 and d == 2:
                col = BRASS
            elif cell == 1 and d in (2, 3) and (px + py) % 2 == 0:
                col = DARK
            elif cell == 1 and d == 0:
                col = GOLD
            elif (x * 3 + y * 5) % 7 == 0:
                col = DARK
            c.set(x, y, col)
    return c


def tex_ceiling():
    """Потолок: тёмные кессоны 32×32 между бетонными рёбрами, вдоль идёт тёмная труба, в
    перекрестьях рёбер редкие лампы-точки (без ярких полос, иначе в перспективе расходятся
    лучами)."""
    rng = random.Random(406)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 32, y % 32
            col = DARK if (x + y) % 2 or (x * 5 + y * 3) % 7 else K
            if 6 <= px <= 7 or 6 <= py <= 7:
                col = K
            if px < 6 or py < 6:
                col = METAL if (px == 1 and py >= 1) or (py == 1 and px >= 1) else DARK
                if px == 0 or py == 0:
                    col = K
                if (px == 5 and py >= 5) or (py == 5 and px >= 5):
                    col = K
            c.set(x, y, col)
    for _ in range(30):
        x, y = rng.randrange(T), rng.randrange(T)
        if x % 32 > 8 and y % 32 > 8:
            c.set(x, y, K)
    # Труба поперёк кессонов.
    for x in range(T):
        c.set(x, 19, METAL if x % 16 not in (0, 1) else GREY)
        c.set(x, 20, DARK)
        c.set(x, 21, K)
        c.set(x, 18, K)
    for y in (2, 34):
        for x in (2, 34):
            c.rect(x, y, x + 1, y + 1, GOLD)
            c.set(x, y, SKY)
    return c


# --- Роботы ------------------------------------------------------------------------------------
# Приспешник с пушкой: бочонок с обручами из основы, один красный глаз-объектив, антенна,
# вместо правой клешни труба лучевой пушки. Робот с клинком: узкий корпус с широкими плечами,
# шлем с гребнем и щелью визора, правое предплечье это клинок. Оба на поршневых ногах.

def _barrel(c, cx, y0, y1, rx):
    """Бочонок: выпуклые бока, плоские крышка и дно, два обруча с заклёпками, купол крышки."""
    tmp = Canvas(T, T)
    mid = (y0 + y1) / 2.0
    tmp.ellipse(cx, mid, rx, (y1 - y0) / 2.0 + 7, VIOLET)
    for y in range(T):
        if y < y0 or y > y1:
            for x in range(T):
                tmp.px[y][x] = None
    c.ellipse(cx, y0 + 1, rx - 4, 2.6, METAL)
    c.paste(tmp, 0, 0)
    for y in (y0 + 5, y0 + 6, y1 - 6, y1 - 5):
        for x in range(T):
            if tmp.get(x, y) is not None:
                c.set(x, y, PLUM)
    for x in range(T):
        if tmp.get(x, y0) is not None:
            c.set(x, y0, METAL)
        if tmp.get(x, y1) is not None:
            c.set(x, y1, PLUM)


def _claw(c, x, y, dx, dy, col=METAL, r=4.6):
    """Клешня полумесяцем с центром (x, y), раскрыта в сторону (dx, dy)."""
    tmp = Canvas(T, T)
    tmp.ellipse(x, y, r, r, col)
    tmp.ellipse(x + dx * 3.0, y + dy * 3.0, 3.3 if dx else 1.9, 3.3 if dy else 1.9, None)
    c.paste(tmp, 0, 0)


def _legs(c, cx, phase, walking, angle, hip_y, thick=5):
    """Поршневые ноги: бедро, шар колена, голень, башмак. Сбоку шаг ножницами, спереди и сзади
    ноги поднимаются по очереди. Подошвы на 61-62 строке."""
    side = angle == 2
    diag = angle in (1, 3)
    for sign in (-1, 1):
        near = sign > 0 or not (side or diag)
        col = METAL if near else DARK
        if side:
            swing = (sign * 5 if phase else -sign * 5) if walking else sign * 2
            lift = 2 if walking and swing < 0 else 0
            hip = (cx + sign, hip_y)
            foot = (cx + swing, 61 - lift)
            knee = ((hip[0] + foot[0]) / 2.0 + 2, (hip_y + foot[1]) / 2.0)
            toe = (-3, 5)
        else:
            spread = 4 if diag else 5
            lift = 2 if walking and ((sign > 0) == bool(phase)) else 0
            hip = (cx + sign * spread, hip_y)
            foot = (cx + sign * (spread + 1) + (1 if diag else 0), 61 - lift)
            knee = (foot[0] + (1.5 if diag else sign * 0.5), (hip_y + foot[1]) / 2.0 - lift * 0.5)
            toe = (-3, 5) if diag else (-4, 4)
        c.line(hip[0], hip[1], knee[0], knee[1], col, thick)
        c.line(knee[0], knee[1], foot[0], foot[1] - 2, col, thick - 1)
        c.ellipse(knee[0], knee[1], 2.6, 2.6, GREY if near else METAL)
        c.rect(foot[0] + toe[0], foot[1], foot[0] + toe[1], foot[1] + 1, DARK)
        c.rect(foot[0] + toe[0] + 1, foot[1] - 1, foot[0] + toe[1] - 2, foot[1] - 1, DARK)


def _cannon_h(c, x0, x1, y):
    """Пушка-рука горизонтально, дулом вправо: тёмная труба с рёбрами охлаждения и раструбом."""
    c.rect(x0, y - 3, x1, y + 3, DARK)
    c.rect(x0, y - 3, x1, y - 2, METAL)
    for x in range(x0 + 4, x1 - 2, 5):
        c.rect(x, y - 4, x + 1, y + 4, METAL)
    c.rect(x1 + 1, y - 4, x1 + 3, y + 4, GREY)
    c.rect(x1 + 4, y - 2, x1 + 4, y + 2, RED)


def _cannon_v(c, x, y0, y1):
    """Пушка-рука вниз вдоль корпуса."""
    c.rect(x - 3, y0, x + 3, y1, DARK)
    c.rect(x - 3, y0, x - 2, y1, METAL)
    for y in range(y0 + 4, y1 - 2, 5):
        c.rect(x - 4, y, x + 4, y + 1, METAL)
    c.rect(x - 4, y1 + 1, x + 4, y1 + 3, GREY)
    c.rect(x - 2, y1 + 4, x + 2, y1 + 4, RED)


def _gunner(angle, phase, mode):
    """Приспешник с пушкой в ракурсе: 0 спереди, 1 вполоборота, 2 сбоку, 3 вполоборота со
    спины, 4 со спины; на 1-3 смотрит вправо."""
    c = Canvas(T, T)
    cx = 32
    side = angle == 2
    back = angle >= 3
    turned = angle in (1, 2, 3)
    walking = mode == "walk"
    bob = 1 if (phase and walking) else 0
    sw = (1 if phase else -1) if walking else 0
    y0, y1 = 12 - bob, 43 - bob
    rx = 11 if side else 12
    sy = y0 + 11
    # Дальняя рука с клешнёй за корпусом.
    if turned:
        fx = cx + (13 if angle == 1 else (10 if side else 12))
        c.line(cx + 6, sy + 1, fx, sy + 9 + sw, DARK, 3)
        _claw(c, fx + 2, sy + 12 + sw, 1, 0, METAL if angle == 1 else DARK)
    _legs(c, cx, phase, walking, angle, y1)
    _barrel(c, cx, y0, y1, rx)
    # Морда или спина.
    ey = y0 + 10
    if not back:
        ex = {0: 0, 1: 5, 2: 9}[angle]
        srx = {0: 6, 1: 5, 2: 3.2}[angle]
        c.ellipse(cx + ex, ey, srx, 6 if angle < 2 else 5.5, DARK)
        c.ellipse(cx + ex + (0.6 if turned else 0), ey, srx - 2, 4 if angle < 2 else 3.6, RED)
        # Решётка динамика под глазом и табличка.
        gx0, gx1 = {0: (cx - 4, cx + 4), 1: (cx + 1, cx + 9), 2: (cx + 6, cx + 10)}[angle]
        for k in range(3):
            c.rect(gx0, y0 + 20 + k * 2, gx1, y0 + 20 + k * 2, DARK)
        if angle == 0:
            c.rect(cx + 6, y0 + 20, cx + 8, y0 + 22, GOLD)
    else:
        # Ранец-батарея: рёбра, лампа, кабель к макушке.
        bx0, bx1 = (cx - 6, cx + 6) if angle == 4 else (cx - 10, cx - 1)
        c.rect(bx0, y0 + 8, bx1, y0 + 23, METAL)
        c.rect(bx0, y0 + 8, bx1, y0 + 9, GREY)
        for y in range(y0 + 12, y0 + 22, 3):
            c.rect(bx0 + 2, y, bx1 - 2, y, DARK)
        c.rect(bx1 - 3, y0 + 10, bx1 - 2, y0 + 10, GOLD)
    # Заклёпки на обручах.
    for x in range(cx - rx + 3, cx + rx - 1, 4):
        c.set(x, y0 + 5, DARK)
        c.set(x + 2, y1 - 5, DARK)
    # Руки.
    eye = None
    muzzle = None
    if turned:
        gx0, gx1 = {1: (cx - 5, cx + 16), 2: (cx - 2, cx + 20), 3: (cx + 1, cx + 15)}[angle]
        gy = y0 + 21 + (sw if walking else 0) * 0
        c.line(gx0 - 1, sy, gx0 + 2, gy - 2, METAL, 5)
        _cannon_h(c, gx0, gx1, gy)
        c.ellipse(gx0 - 1, sy, 3.4, 3.4, METAL)
        c.ellipse(gx0 - 1, sy, 1.4, 1.4, DARK)
        muzzle = (gx1 + 4, gy)
    else:
        gs = -1 if angle == 0 else 1
        # Клешня на другой стороне.
        px = cx - gs * 12
        c.line(px, sy, px - gs * 4, sy + 8, METAL, 4)
        c.line(px - gs * 4, sy + 8, px - gs * 4, sy + 14 - sw, METAL, 3)
        _claw(c, px - gs * 4, sy + 18 - sw, 0, 1)
        c.ellipse(px, sy, 3.2, 3.2, METAL)
        c.ellipse(px, sy, 1.3, 1.3, DARK)
        qx = cx + gs * 12
        if mode in ("aim", "fire"):
            # Пушка смотрит в камеру: кольца раструба одно в другом.
            mx, my = cx - 3, 34
            c.line(qx, sy, mx - 3, my - 3, METAL, 6)
            c.ellipse(mx, my, 7, 7, GREY)
            c.ellipse(mx, my, 5.6, 5.6, METAL)
            c.ellipse(mx, my, 4.2, 4.2, DARK)
            c.ellipse(mx, my, 2.6, 2.6, K)
            muzzle = (mx, my)
        else:
            c.line(qx, sy, qx + gs * 4, sy + 5, METAL, 5)
            _cannon_v(c, qx + gs * 4, sy + 4 + sw, sy + 18 + sw)
        c.ellipse(qx, sy, 3.2, 3.2, METAL)
        c.ellipse(qx, sy, 1.3, 1.3, DARK)
    # Антенна с огоньком.
    ax = cx + (-3 if back else 3)
    c.line(ax, y0 - 2, ax + 2, 6 - bob, DARK, 2)
    c.ellipse(ax + 2, 5 - bob, 1.6, 1.6, RED)
    c.finish()
    # Блики после светотени.
    if not back:
        ex = {0: 0, 1: 5, 2: 9}[angle]
        c.set(cx + ex - 1, ey - 2, WHITE)
        c.set(cx + ex, ey - 2, WHITE if angle < 2 else RED)
        if mode == "fire":
            c.ellipse(cx + ex, ey, 2, 2, GOLD)
    c.set(ax + 2, 4 - bob, GOLD)
    if mode in ("aim", "fire") and muzzle:
        c.ellipse(muzzle[0], muzzle[1], 1.3, 1.3, RED)
    if mode == "fire" and muzzle:
        mx, my = muzzle
        for a in range(0, 360, 45):
            r = 11 if a % 90 == 0 else 7
            c.line(mx, my, mx + r * math.cos(math.radians(a)), my + r * math.sin(math.radians(a)), RED, 2)
        c.ellipse(mx, my, 6, 6, RED)
        c.ellipse(mx, my, 4.2, 4.2, GOLD)
        c.ellipse(mx, my, 2.2, 2.2, WHITE)
    return c


def _blade(c, hub, tip, w=5.0):
    """Клинок от шарнира `hub` к острию `tip`: светлая грань и тёмная, жёлтая гарда у шарнира."""
    dx, dy = tip[0] - hub[0], tip[1] - hub[1]
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    nx, ny = -uy, ux
    k = 0.78
    sh = (hub[0] + dx * k, hub[1] + dy * k)
    left = [(hub[0] + nx * w / 2, hub[1] + ny * w / 2), (sh[0] + nx * w / 2, sh[1] + ny * w / 2)]
    right = [(sh[0] - nx * w / 2, sh[1] - ny * w / 2), (hub[0] - nx * w / 2, hub[1] - ny * w / 2)]
    c.poly(left + [tip] + right, WHITE)
    c.poly([hub, sh, tip] + right, GREY)
    c.line(hub[0] + nx * (w / 2 + 2), hub[1] + ny * (w / 2 + 2), hub[0] - nx * (w / 2 + 2), hub[1] - ny * (w / 2 + 2),
           GOLD, 3)


def _slasher(angle, phase, mode):
    """Робот с клинком в ракурсе: узкая талия, наплечники, шлем с красным гребнем и щелью
    визора. `slash` это удар: клинок идёт наискось через корпус, за ним белая дуга."""
    c = Canvas(T, T)
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    turned = side or diag
    walking = mode == "walk"
    bob = 1 if (phase and walking) else 0
    sw = (1 if phase else -1) if walking else 0
    top = 21 - bob
    ws = 6 if side else (10 if diag else 11)
    ww = 4 if side else 6
    hx = cx + (2 if side else (1 if diag else 0))
    # Дальняя рука с кулаком.
    if turned:
        fx = cx + (12 if angle == 1 else (7 if side else 11))
        c.line(cx + 5, top + 3, fx, top + 11 + sw, PLUM, 4)
        c.ellipse(fx + 1, top + 14 + sw, 2.8, 2.8, DARK)
    _legs(c, cx, phase, walking, angle, 44 - bob, 4)
    # Таз и корпус: тёмная броня клином, светлая грудная плита.
    c.rect(cx - ww, 41 - bob, cx + ww, 45 - bob, DARK)
    c.poly([(cx - ws, top), (cx + ws, top), (cx + ww, 42 - bob), (cx - ww, 42 - bob)], PLUM)
    if back:
        # Хребет из сегментов и два сопла.
        sx = cx - (4 if diag else 0)
        c.rect(sx - 2, top + 2, sx + 2, 40 - bob, METAL)
        for y in range(top + 4, 40 - bob, 4):
            c.rect(sx - 2, y, sx + 2, y, DARK)
        for s in (-1, 1):
            c.rect(sx + s * 6 - 1, top + 5, sx + s * 6 + 1, top + 9, DARK)
    else:
        px = cx + (0 if angle == 0 else (3 if diag else 2))
        pw = ws - (3 if angle == 0 else 4)
        c.poly([(px - pw, top + 2), (px + pw, top + 2), (px + pw - 3, top + 13), (px - pw + 3, top + 13)], VIOLET)
        # Красный шеврон и пластины живота.
        c.line(px - pw + 2, top + 4, px, top + 9, RED, 2)
        c.line(px + pw - 2, top + 4, px, top + 9, RED, 2)
        for y in (top + 15, top + 18):
            c.rect(px - ww + 1, y, px + ww - 1, y, DARK)
    c.rect(cx - ww, 41 - bob, cx + ww, 42 - bob, METAL)
    c.rect(cx - 1 + (hx - cx), 41 - bob, cx + 1 + (hx - cx), 42 - bob, GOLD)
    # Шея и шлем.
    c.rect(hx - 2, 17 - bob, hx + 2, top, DARK)
    c.ellipse(hx, 12 - bob, 6.5, 7, VIOLET)
    c.poly([(hx - 5, 14 - bob), (hx + 5, 14 - bob), (hx + 3, 20 - bob), (hx - 3, 20 - bob)], VIOLET)
    if not back:
        v0, v1 = {0: (hx - 5, hx + 5), 1: (hx - 2, hx + 6), 2: (hx + 1, hx + 6)}[angle]
        c.rect(v0, 11 - bob, v1, 14 - bob, K)
        c.rect(v0 + 1, 12 - bob, v1 - (0 if side else 1), 13 - bob, RED)
        # Решётка рта.
        m0, m1 = {0: (hx - 2, hx + 2), 1: (hx, hx + 4), 2: (hx + 3, hx + 5)}[angle]
        for x in range(m0, m1 + 1, 2):
            c.rect(x, 16 - bob, x, 18 - bob, DARK)
    else:
        for y in (10, 13, 16):
            c.rect(hx - 3 - (2 if diag else 0), y - bob, hx + 3 - (2 if diag else 0), y - bob, PLUM)
    # Гребень: красный плавник по макушке.
    if side or diag:
        c.poly([(hx - 7, 9 - bob), (hx - 4, 3 - bob), (hx + 2, 1 - bob), (hx + 4, 6 - bob)], RED)
    else:
        c.poly([(hx - 2, 7 - bob), (hx, 1 - bob), (hx + 2, 7 - bob)], RED)
        c.rect(hx - 1, 6 - bob, hx + 1, (10 if not back else 17) - bob, RED)
    # Руки. Клинок на правой руке робота: спереди она слева от зрителя, со спины справа.
    arc = None
    if turned:
        sh = (cx + (-2 if angle == 1 else (0 if side else 2)), top + 3)
        hub = (sh[0] + (8 if side else 6), top + 11 + sw * 0.5)
        tip = (hub[0] + (14 if side else (12 if angle == 1 else 8)), 9 - bob)
        c.line(sh[0], sh[1], hub[0], hub[1], VIOLET, 5)
        _blade(c, hub, tip)
        c.ellipse(hub[0], hub[1], 2.8, 2.8, METAL)
        c.ellipse(sh[0], sh[1] - 1, 4.6, 4.2, VIOLET)
        c.rect(sh[0] - 2, sh[1] - 5, sh[0] + 2, sh[1] - 5, METAL)
    else:
        gs = -1 if angle == 0 else 1
        # Кулак на другой стороне.
        fx = cx - gs * (ws + 1)
        c.line(fx, top + 3, fx - gs * 3, top + 11, PLUM, 4)
        c.line(fx - gs * 3, top + 11, fx - gs * 2, top + 18 - sw, VIOLET, 4)
        c.ellipse(fx - gs * 2, top + 20 - sw, 3, 3, METAL)
        c.ellipse(fx, top + 2, 4.8, 4.2, VIOLET)
        c.rect(fx - 2, top - 2, fx + 2, top - 2, METAL)
        bx = cx + gs * (ws + 1)
        if mode == "slash":
            hub = (bx - gs * 5, top + 9)
            tip = (cx - gs * 19, 54)
            c.line(bx, top + 3, hub[0], hub[1], VIOLET, 5)
            _blade(c, hub, tip, 6.0)
            arc = (hub, tip, gs)
        else:
            hub = (bx + gs * 3, top + 12 + sw)
            tip = (bx + gs * 8, 7 - bob + sw)
            c.line(bx, top + 3, hub[0], hub[1], VIOLET, 5)
            _blade(c, hub, tip)
        c.ellipse(hub[0], hub[1], 2.8, 2.8, METAL)
        c.ellipse(bx, top + 2, 4.8, 4.2, VIOLET)
        c.rect(bx - 2, top - 2, bx + 2, top - 2, METAL)
    c.finish()
    # После светотени: огонь визора, след удара.
    if not back:
        v0, v1 = {0: (hx - 5, hx + 5), 1: (hx - 2, hx + 6), 2: (hx + 1, hx + 6)}[angle]
        c.set(v0 + 2, 12 - bob, GOLD if mode == "slash" else WHITE)
        if mode == "slash":
            c.rect(v0 + 1, 12 - bob, v1 - 1, 12 - bob, GOLD)
    if arc:
        hub, tip, gs = arc
        # Дуга от замаха сверху до острия: выгнута наружу.
        ox, oy = hub[0], hub[1] - 2
        r = math.hypot(tip[0] - ox, tip[1] - oy)
        a1 = math.atan2(tip[1] - oy, tip[0] - ox)
        for i in range(34):
            a = a1 + gs * (0.12 + i * 0.03)
            x, y = int(round(ox + r * math.cos(a))), int(round(oy + r * math.sin(a)))
            if c.get(x, y) is None or c.get(x, y) == K:
                c.set(x, y, WHITE if i < 22 else SKY)
            if i < 20 and c.get(x - gs, y) is None:
                c.set(x - gs, y, WHITE if i < 10 else SKY)
    return c


def _wreck(k, blade):
    """Падение, кадры 1 и 2: робот оседает на подломленных ногах и искрит, потом лежит грудой:
    корпус на боку, глаз погас, оружие и башмак рядом. Низ на 62 строке."""
    c = Canvas(T, T)
    cx, base = 32, 62
    if not blade:
        if k == 1:
            for s in (-1, 1):
                c.line(cx + s * 5, 50, cx + s * 13, 55, METAL, 4)
                c.line(cx + s * 13, 55, cx + s * 9, 60, METAL, 3)
                c.ellipse(cx + s * 13, 55, 2.4, 2.4, GREY)
                c.rect(cx + s * 9 - 4, 61, cx + s * 9 + 4, 62, DARK)
            _barrel(c, cx + 1, 23, 52, 12)
            c.ellipse(cx + 2, 33, 6, 6, DARK)
            c.rect(cx - 2, 33, cx + 6, 34, RED)
            for kk in range(3):
                c.rect(cx - 3, 43 + kk * 2, cx + 5, 43 + kk * 2, DARK)
            # Руки повисли: клешня и пушка упёрлись в пол.
            c.line(cx + 13, 34, cx + 19, 46, METAL, 4)
            _claw(c, cx + 20, 51, 0, 1)
            c.line(cx - 11, 34, cx - 17, 42, METAL, 5)
            _cannon_v(c, cx - 17, 42, 55)
            c.line(cx + 4, 21, cx + 11, 17, DARK, 2)
            c.ellipse(cx + 12, 17, 1.6, 1.6, DARK)
            c.ellipse(cx - 6, 14, 4.5, 3.5, GREY)
            c.ellipse(cx - 2, 9, 3.5, 3, GREY)
            c.ellipse(cx - 7, 5, 2.5, 2, GREY)
        else:
            # Бочонок на боку, крышка отлетела.
            tmp = Canvas(T, T)
            tmp.ellipse(cx - 2, base - 10, 23, 10.5, VIOLET)
            for y in range(T):
                for x in range(T):
                    if tmp.px[y][x] is not None and (x < cx - 18 or x > cx + 13):
                        tmp.px[y][x] = None
            c.paste(tmp, 0, 0)
            for x in (cx - 13, cx - 12, cx + 7, cx + 8):
                for y in range(T):
                    if tmp.get(x, y) is not None:
                        c.set(x, y, PLUM)
            for y in range(T):
                if tmp.get(cx + 13, y) is not None:
                    c.set(cx + 13, y, DARK)
                    c.set(cx + 12, y, DARK)
            c.ellipse(cx - 3, base - 11, 4.6, 4.6, DARK)
            c.ellipse(cx + 20, base - 3, 6, 2.6, METAL)
            c.rect(cx + 15, base - 3, cx + 25, base - 3, GREY)
            # Ноги торчат, пушка рядом, клешня отлетела.
            c.line(cx - 18, base - 8, cx - 26, base - 14, METAL, 4)
            c.rect(cx - 29, base - 19, cx - 27, base - 12, DARK)
            c.line(cx - 18, base - 4, cx - 27, base - 1, METAL, 4)
            c.rect(cx - 30, base - 5, cx - 28, base, DARK)
            c.line(cx - 6, base - 20, cx - 2, base - 26, DARK, 2)
            _claw(c, cx + 16, base - 14, 1, -1 * 0, METAL, 4.2)
    else:
        if k == 1:
            # На коленях, клинок воткнут в пол, голова упала на грудь.
            for s in (-1, 1):
                c.line(cx + s * 4, 46, cx + s * 9, 56, METAL, 4)
                c.line(cx + s * 9, 56, cx + s * 17, 60, METAL, 3)
                c.ellipse(cx + s * 9, 56, 2.4, 2.4, GREY)
                c.rect(cx + s * 17 - 3, 60, cx + s * 17 + 3, 62, DARK)
            c.rect(cx - 6, 43, cx + 6, 48, DARK)
            c.poly([(cx - 10, 26), (cx + 12, 28), (cx + 7, 46), (cx - 6, 45)], PLUM)
            c.poly([(cx - 6, 29), (cx + 8, 30), (cx + 5, 39), (cx - 3, 38)], VIOLET)
            c.line(cx - 4, 31, cx + 1, 36, RED, 2)
            c.line(cx + 6, 32, cx + 1, 36, RED, 2)
            c.ellipse(cx + 4, 21, 6.5, 6.5, VIOLET)
            c.rect(cx, 22, cx + 9, 24, K)
            c.poly([(cx - 2, 17), (cx + 3, 11), (cx + 7, 15)], RED)
            c.line(cx - 10, 28, cx - 17, 38, VIOLET, 5)
            _blade(c, (cx - 18, 40), (cx - 21, 61))
            c.ellipse(cx - 18, 39, 2.8, 2.8, METAL)
            c.ellipse(cx - 10, 27, 4.6, 4.2, VIOLET)
            c.line(cx + 12, 29, cx + 17, 40, PLUM, 4)
            c.ellipse(cx + 17, 43, 3, 3, METAL)
            c.ellipse(cx + 12, 28, 4.6, 4.2, VIOLET)
            c.ellipse(cx + 14, 12, 4.5, 3.5, GREY)
            c.ellipse(cx + 18, 6, 3.5, 3, GREY)
        else:
            # Лежит ничком: корпус клином, шлем откатился, клинок вдоль пола.
            _blade(c, (cx + 2, base - 1), (cx + 29, base - 2), 4.0)
            c.poly([(cx - 20, base - 10), (cx + 2, base - 13), (cx + 4, base - 1), (cx - 22, base - 1)], PLUM)
            c.rect(cx - 12, base - 12, cx - 9, base - 5, METAL)
            c.rect(cx - 5, base - 13, cx - 2, base - 6, METAL)
            c.line(cx - 22, base - 6, cx - 29, base - 3, METAL, 4)
            c.rect(cx - 31, base - 7, cx - 29, base, DARK)
            c.ellipse(cx + 3, base - 9, 4.6, 4.2, VIOLET)
            c.line(cx + 4, base - 7, cx + 9, base - 3, VIOLET, 4)
            c.ellipse(cx + 16, base - 7, 6.5, 6.5, VIOLET)
            c.rect(cx + 14, base - 8, cx + 22, base - 6, K)
            c.poly([(cx + 12, base - 12), (cx + 17, base - 17), (cx + 21, base - 12)], RED)
    c.finish()
    # Искры и дымящий глаз после светотени.
    rng = random.Random(410 + k + (5 if blade else 0))
    for _ in range(7 if k == 1 else 4):
        x, y = cx + rng.randint(-20, 20), rng.randint(14, 40) if k == 1 else base - rng.randint(14, 24)
        if c.get(x, y) is None:
            c.set(x, y, GOLD)
            c.set(x + rng.choice((-1, 1)), y - 1, WHITE)
    if not blade and k == 2:
        c.line(cx - 5, base - 13, cx - 1, base - 9, METAL, 1)
        c.line(cx - 1, base - 13, cx - 5, base - 9, METAL, 1)
    return c


def robot(angle, phase, mode="walk", blade=False):
    """Робот 64×64 в ракурсе `angle` (0 спереди … 4 со спины, лицом вправо на 1-3), шаг `phase`
    0/1. `mode`: walk, aim, fire, slash, die0..die2, hurt. `blade` это робот с клинком. Подошвы на
    61-62 строке, ось по центру кадра, как у скелета пиратов."""
    if mode.startswith("die"):
        k = int(mode[-1])
        if k == 0:
            return robot(0, 0, "hurt", blade)
        return _wreck(k, blade)
    inner = "walk" if mode == "hurt" else mode
    c = _slasher(angle, phase, inner) if blade else _gunner(angle, phase, inner)
    if mode == "hurt":
        # Попадание: корпус идёт красной рябью, из швов искры.
        for x in range(T):
            for y in range(T):
                if c.get(x, y) in (VIOLET, PLUM) and (x + y) % 3 == 0:
                    c.set(x, y, RED)
        for x, y in ((20, 18), (44, 30), (26, 40), (40, 14)):
            c.set(x, y, WHITE)
            c.set(x + 1, y - 1, GOLD)
            c.set(x - 1, y + 1, GOLD)
    return c


def robot_strips():
    out = {}
    for name, blade in (("skel", False), ("cut", True)):
        walk = []
        for a in range(5):
            for ph in range(2):
                walk.append(robot(a, ph, "walk", blade))
        out[name + "_walk"] = strip(walk)
        out[name + "_die"] = strip([robot(0, 0, "die%d" % k, blade) for k in range(3)])
    out["skel_fire"] = strip([robot(0, 0, "aim"), robot(0, 0, "fire")])
    out["cut_slash"] = strip([robot(0, 0, "walk", True), robot(0, 0, "slash", True)])
    return out


# --- Предметы, оружие, лицо --------------------------------------------------------------------

def bullet():
    """Энергозаряд героя: синий шар с белым ядром, жёлтые искры крестом и хвост; с красным
    выстрелом робота не спутать."""
    c = Canvas(16, 16)
    for dx, dy in ((0, -5), (-5, 0), (5, 0)):
        c.line(8, 7, 8 + dx, 7 + dy, GOLD, 1)
    c.ellipse(8, 7, 3.6, 3.6, SEA)
    c.poly([(6, 9), (10, 9), (8, 14)], SEA)
    c.finish()
    c.ellipse(7.5, 6.5, 1.6, 1.6, WHITE)
    c.set(8, 11, SKY)
    return c


def decor(kind):
    """Ориентир зала 64×64, низ на 62-63 строке: 0 катушка с молниями, 1 штабель бронированных
    кейсов, 2 прожектор на треноге, 3 лучевая пушка на лафете, 4 колба с роботом, 5 пульт с
    рубильником."""
    c = Canvas(T, T)
    if kind == 0:
        # Катушка: тумба, медная обмотка, тор и шар наверху.
        c.poly([(16, 63), (48, 63), (44, 50), (20, 50)], DARK)
        c.rect(20, 50, 44, 51, METAL)
        c.rect(27, 55, 37, 59, GOLD)
        c.line(20, 50, 22, 20, METAL, 2)
        c.line(44, 50, 42, 20, METAL, 2)
        for y in range(22, 50):
            c.rect(26, y, 38, y, GOLD if y % 3 else BRASS)
        c.rect(26, 22, 27, 49, BRASS)
        c.rect(24, 48, 40, 50, GREY)
        c.ellipse(32, 17, 15, 6, METAL)
        c.ellipse(32, 15, 12, 3, GREY)
        c.rect(30, 6, 34, 12, METAL)
        c.ellipse(32, 6, 4.5, 4.5, GREY)
    elif kind == 1:
        # Кейсы: два внизу, третий сверху наискось, у верхнего ручка.
        for x0, y0, w, h in ((5, 42, 26, 20), (33, 45, 26, 17), (15, 21, 30, 20)):
            c.rect(x0, y0, x0 + w, y0 + h, METAL)
            c.rect(x0, y0, x0 + w, y0 + 2, GREY)
            c.rect(x0, y0 + 6, x0 + w, y0 + 6, DARK)
            for xa in (x0, x0 + w - 4):
                c.rect(xa, y0, xa + 4, y0 + 4, DARK)
                c.rect(xa, y0 + h - 4, xa + 4, y0 + h, DARK)
            for x in range(x0 + 8, x0 + w - 6, 6):
                c.rect(x, y0 + 9, x, y0 + h - 3, DARK)
            c.rect(x0 + w // 2 - 3, y0 + 4, x0 + w // 2 + 3, y0 + 10, GOLD)
            c.rect(x0 + w // 2 - 1, y0 + 6, x0 + w // 2, y0 + 8, DARK)
        c.rect(25, 15, 35, 16, DARK)
        c.rect(25, 15, 26, 20, DARK)
        c.rect(34, 15, 35, 20, DARK)
        c.poly([(9, 52), (15, 52), (12, 46)], RED)
    elif kind == 2:
        # Прожектор: тренога, вилка, барабан с линзой смотрит вверх и вправо.
        c.line(31, 42, 15, 62, METAL, 3)
        c.line(33, 42, 49, 62, METAL, 3)
        c.rect(30, 40, 34, 62, DARK)
        c.rect(26, 60, 38, 62, DARK)
        c.line(16, 36, 20, 16, DARK, 3)
        c.line(46, 38, 50, 22, DARK, 3)
        c.rect(16, 36, 46, 40, DARK)
        c.ellipse(31, 24, 16, 14, METAL)
        c.ellipse(27, 28, 11, 9, DARK)
        for d in range(0, 9, 3):
            c.line(18 + d, 30, 22 + d, 36, METAL, 1)
        c.ellipse(36, 20, 12.5, 11.5, GOLD)
        c.ellipse(36, 20, 10.5, 9.5, SKY)
        c.ellipse(34, 18, 5, 4.5, WHITE)
        c.line(27, 20, 45, 20, GOLD, 1)
        c.line(36, 11, 36, 29, GOLD, 1)
    elif kind == 3:
        # Лучевая пушка: лафет на двух колёсах, пузатый корпус, ствол с тремя кольцами и шаром.
        c.line(12, 60, 30, 46, DARK, 3)
        c.rect(18, 44, 46, 48, DARK)
        c.rect(28, 40, 34, 46, METAL)
        c.ellipse(24, 32, 13, 10, VIOLET)
        c.rect(18, 22, 30, 24, PLUM)
        c.ellipse(24, 21, 6, 5, AQUA)
        c.ellipse(22, 19, 2, 1.6, SKY)
        c.rect(20, 31, 28, 32, PLUM)
        c.rect(20, 35, 28, 36, PLUM)
        c.poly([(34, 26), (54, 29), (54, 35), (34, 38)], METAL)
        c.rect(34, 27, 52, 28, GREY)
        for x, r in ((40, 9), (46, 7.5), (52, 6)):
            c.ellipse(x, 32, 2, r, GOLD)
            c.ellipse(x + 0.6, 32, 1, r - 1.5, BRASS)
        c.rect(54, 31, 57, 33, DARK)
        c.ellipse(59, 32, 3.2, 3.2, RED)
        c.rect(8, 27, 12, 37, DARK)
        for wx in (20, 44):
            c.ellipse(wx, 54, 8, 8, DARK)
            c.ellipse(wx, 54, 5.5, 5.5, METAL)
            c.ellipse(wx, 54, 2, 2, GREY)
            for a in range(0, 360, 60):
                c.set(wx + 4 * math.cos(math.radians(a)), 54 + 4 * math.sin(math.radians(a)), DARK)
    elif kind == 4:
        # Колба: тумба с лампами, стекло с коралловой жидкостью, внутри спящий приспешник.
        c.rect(18, 53, 46, 62, DARK)
        c.rect(18, 53, 46, 54, METAL)
        for x in (23, 29, 35, 41):
            c.rect(x, 57, x + 1, 58, GOLD if x != 35 else RED)
        c.rect(18, 4, 46, 12, DARK)
        c.rect(18, 4, 46, 5, METAL)
        c.rect(28, 0, 36, 3, METAL)
        c.line(46, 8, 54, 8, DARK, 3)
        c.line(54, 8, 54, 62, DARK, 3)
        c.rect(21, 13, 43, 52, AQUA)
        c.rect(21, 13, 43, 17, NAVY)
        c.rect(21, 18, 43, 18, SKY)
        c.rect(22, 14, 24, 51, SKY)
        c.rect(41, 19, 43, 52, RED)
        tmp = Canvas(T, T)
        tmp.ellipse(33, 35, 7.5, 13, PLUM)
        for y in range(27, 45):
            for x in range(T):
                if tmp.px[y][x] is not None:
                    c.set(x, y, DARK if y in (30, 41) else PLUM)
        c.ellipse(33, 33, 3, 3, K)
        c.rect(31, 33, 35, 33, METAL)
        for s in (-1, 1):
            c.rect(33 + s * 3 - 1, 45, 33 + s * 3, 49, PLUM)
        c.line(34, 26, 36, 22, PLUM, 1)
    else:
        # Пульт с рубильником: шкаф, два циферблата, ряд кнопок, рычаг с красным шаром, лампы.
        c.rect(15, 34, 49, 62, METAL)
        c.poly([(13, 34), (51, 34), (48, 28), (16, 28)], GREY)
        c.rect(15, 58, 49, 62, DARK)
        c.rect(15, 34, 49, 35, DARK)
        for gx in (24, 40):
            c.ellipse(gx, 43, 5.5, 5.5, DARK)
            c.ellipse(gx, 43, 4.2, 4.2, WHITE)
            c.line(gx, 43, gx + (2 if gx < 32 else -3), 40, RED, 1)
        for i, x in enumerate(range(19, 46, 5)):
            c.rect(x, 52, x + 2, 54, (RED, GOLD, SKY, GOLD, RED, SEA)[i])
        for y in range(56, 62):
            for x in range(16, 49):
                if y in (56, 57):
                    c.set(x, y, GOLD if (x // 3) % 2 else K)
        c.rect(27, 26, 37, 29, DARK)
        c.line(32, 28, 43, 10, DARK, 4)
        c.line(32, 28, 43, 10, METAL, 2)
        c.ellipse(44, 8, 5, 5, RED)
        c.ellipse(42, 6, 1.5, 1.5, AQUA)
        for lx, col in ((19, GOLD), (11, SKY)):
            c.rect(lx, 20 if lx == 19 else 26, lx + 1, 34, DARK)
            c.ellipse(lx + 0.5, 17 if lx == 19 else 23, 3.4, 3.8, col)
        c.rect(9, 34, 13, 62, DARK)
        c.rect(9, 34, 13, 35, METAL)
    c.finish()
    if kind == 0:
        # Молнии от тора в стороны.
        for pts in (((17, 17), (11, 12), (13, 20), (5, 17), (8, 25)), ((47, 17), (54, 13), (51, 21), (59, 20), (56, 28)),
                    ((36, 3), (41, 1), (40, 6), (46, 4))):
            for a, b in zip(pts, pts[1:]):
                c.line(a[0], a[1], b[0], b[1], SKY, 1)
            c.set(pts[1][0], pts[1][1], WHITE)
            c.set(pts[-1][0], pts[-1][1], WHITE)
    elif kind == 4:
        for x, y in ((27, 24), (38, 30), (28, 46), (39, 44), (26, 36)):
            c.set(x, y, WHITE)
            c.set(x, y + 1, SKY)
    return c


def pistol(frame):
    """Перчатка-бластер снизу по центру, 128×96: синий рукав трико, жёлтая перчатка с раструбом,
    кулак костяшками вперёд; на тыле кисти стальной блок бластера со звездой и коралловой
    колбой заряда, от него ствол вглубь (ось x=64) с тремя жёлтыми кольцами и линзой у верхнего
    края; кадр 1 со вспышкой."""
    c = Canvas(128, 96)
    # Рукав трико: расширяется книзу, складки тенью, блик по левому краю.
    for y in range(74, 96):
        w = 16 + (y - 62) // 4
        for x in range(64 - w, 64 + w):
            fold = (y - 74) % 8 == 5 and abs(x - 62 - (y % 3)) < w - 6
            col = NAVY if fold or x > 64 + w - 5 else SEA
            if x == 64 - w + 2:
                col = SKY
            c.set(x, y, col)
    # Раструб перчатки: шире рукава, с кантом.
    c.poly([(44, 78), (84, 78), (81, 62), (47, 62)], GOLD)
    c.rect(44, 76, 84, 79, GOLD)
    c.rect(44, 79, 84, 79, BRASS)
    c.rect(46, 73, 82, 73, BRASS)
    for x in (52, 76):
        c.line(x, 64, x - (1 if x < 64 else -1), 72, BRASS, 1)
    # Кулак с тыла: кисть, четыре пальца вперёд со скруглёнными костяшками, большой палец слева.
    c.poly([(48, 63), (80, 63), (81, 48), (79, 44), (49, 44), (47, 48)], GOLD)
    for i in range(4):
        x0 = 48 + i * 8
        c.rect(x0, 36, x0 + 7, 46, GOLD)
        c.ellipse(x0 + 3.5, 36, 3.7, 3.2, GOLD)
    c.line(45, 60, 43, 48, GOLD, 6)
    c.ellipse(43, 46, 3, 3.5, GOLD)
    # Блок бластера на тыле кисти: стальная коробка на ремне через ладонь.
    c.rect(46, 56, 82, 59, DARK)
    c.rect(55, 41, 73, 58, METAL)
    c.rect(55, 41, 73, 42, GREY)
    c.rect(55, 41, 56, 58, GREY)
    c.rect(71, 43, 73, 58, DARK)
    c.rect(58, 47, 70, 56, SEA)
    # Колба заряда справа и кабель к раструбу.
    c.rect(75, 45, 80, 57, DARK)
    c.rect(76, 47, 79, 55, AQUA)
    c.line(78, 58, 79, 63, DARK, 2)
    # Казённик между пальцами и ствол с кольцами, линза.
    c.poly([(58, 41), (70, 41), (68, 24), (60, 24)], DARK)
    c.rect(60, 6, 68, 24, METAL)
    c.rect(60, 6, 61, 24, GREY)
    for y, w in ((20, 9), (15, 8), (10, 7)):
        c.rect(64 - w, y - 1, 64 + w, y + 1, GOLD)
        c.rect(64 - w, y + 1, 64 + w, y + 1, BRASS)
    c.ellipse(64, 4, 5.5, 3.6, SEA)
    c.finish()
    # После светотени: звезда на блоке, блики, швы пальцев, костяшки, уровень заряда.
    _stamp(c, 61, 48, STAR7, GOLD)
    c.set(64, 51, WHITE)
    for i in (1, 3):
        c.rect(48 + i * 8, 35, 48 + i * 8, 45, BRASS)
    for i in (0, 3):
        c.rect(50 + i * 8, 34, 52 + i * 8, 34, WHITE)
        c.rect(50 + i * 8, 43, 53 + i * 8, 43, BRASS)
    c.rect(76, 47, 79, 49, SKY)
    c.set(76, 51, WHITE)
    c.ellipse(64, 4, 3.4, 2, SKY)
    c.rect(62, 3, 64, 3, WHITE)
    for x in (58, 70):
        c.set(x, 44, DARK)
    c.rect(62, 29, 66, 32, RED)
    c.rect(62, 29, 66, 29, GOLD)
    c.rect(61, 35, 67, 35, METAL)
    if frame:
        for dx in (-24, -13, 13, 24):
            c.line(64 + dx * 0.4, 5, 64 + dx, 13 if abs(dx) > 20 else 16, GOLD, 2)
        c.ellipse(64, 1, 19, 10, SEA)
        c.ellipse(64, 0, 14, 7.5, SKY)
        c.ellipse(64, 0, 8, 5, WHITE)
    return c


def face(mode):
    """Лицо героя для HUD, 32×32: тёмные волосы с хохолком, чёрная маска-домино с белыми
    глазами, ворот синего трико и жёлтый плащ на плечах; 0 прямо, 1 глянул влево, 2 вправо,
    3 больно (зажмурился, ссадина, пот), 4 ухмылка."""
    c = Canvas(32, 32)
    # Плечи: плащ и трико, застёжка-звезда.
    c.poly([(3, 31), (28, 31), (25, 26), (6, 26)], GOLD)
    c.poly([(10, 31), (21, 31), (19, 25), (12, 25)], SEA)
    c.rect(13, 23, 18, 26, SKIN)
    # Голова и уши.
    c.ellipse(15.5, 15, 9, 10, SKIN)
    c.ellipse(6, 16, 1.8, 2.6, SKIN)
    c.ellipse(25, 16, 1.8, 2.6, SKIN)
    # Волосы шапкой, виски, хохолок вверх и вбок.
    for y in range(3, 14):
        for x in range(5, 27):
            if c.get(x, y) == SKIN and (y <= 8 or (y <= 11 and (x <= 8 or x >= 23)) or (y == 9 and (x <= 11 or x >= 21))):
                c.set(x, y, DARK)
    c.ellipse(18, 5.5, 6, 3, DARK)
    c.poly([(19, 4), (24, 2), (26, 4), (24, 7), (20, 7)], DARK)
    # Маска-домино: полоса с выемкой над носом, острые края к вискам.
    c.poly([(5, 11), (9, 13), (22, 13), (26, 11), (26, 15), (23, 18), (18, 18), (16, 15), (15, 15), (13, 18), (8, 18), (5, 15)], K)
    # Нос, скулы.
    c.rect(15, 17, 16, 20, TAN)
    c.set(14, 20, TAN)
    c.rect(9, 21, 10, 21, TAN)
    c.rect(21, 21, 22, 21, TAN)
    c.rect(12, 25, 19, 25, TAN)
    c.finish()
    # Глаза, рот и мелочь после светотени.
    look = {0: 0, 1: -1, 2: 1, 3: 0, 4: 0}[mode]
    for ex in (10, 21):
        if mode == 3:
            c.line(ex - 2, 14, ex + 1, 16, WHITE, 1)
            c.line(ex - 2, 16, ex + 1, 14, WHITE, 1)
        else:
            c.rect(ex - 2, 14, ex + 2, 16, WHITE)
            c.set(ex - 2, 16, K)
            c.set(ex + 2, 14 if ex > 16 else 16, K)
            c.set(ex + (2 if ex < 16 else -2), 14, K)
            if mode == 4:
                c.rect(ex - 2, 14, ex + 2, 14, K)
            c.rect(ex + look, 15, ex + look, 16, K)
    if mode == 4:
        c.rect(11, 22, 20, 23, WHITE)
        c.rect(11, 21, 20, 21, K)
        c.rect(12, 24, 19, 24, K)
        c.set(10, 21, K)
        c.set(21, 20, K)
        c.set(22, 19, K)
        for x in (13, 16, 18):
            c.set(x, 23, GREY)
    elif mode == 3:
        c.ellipse(15.5, 23, 3, 1.8, K)
        c.rect(14, 22, 17, 22, WHITE)
        c.line(22, 20, 24, 23, RED, 1)
        c.set(23, 20, RED)
        c.set(4, 9, SKY)
        c.set(4, 10, WHITE)
        c.set(3, 11, SKY)
    else:
        c.rect(12, 23, 19, 23, K)
        c.set(20 if mode != 1 else 11, 22, K)
    c.set(15, 28, GOLD)
    c.set(16, 28, GOLD)
    c.set(15, 29, WHITE)
    return c


# --- Имена зеркала -----------------------------------------------------------------------------
# Те же публичные имена, что у `space_hold16.py`: сборщик и проверки берут слоты по ним.

def alien(angle, phase, mode="walk", rod=False):
    """Враг в ракурсе, имя зеркала: `rod` это второй враг (у супергероев робот с клинком)."""
    return robot(angle, phase, mode, rod)


def alien_strips():
    return robot_strips()


def shot():
    """Выстрел робота из основы: красный сгусток с жёлтым ядром и лучами."""
    return superheroes16.shot()


def key():
    """Ключ от лифта из основы: жёлтый, головка звездой."""
    return superheroes16.key()


def medkit():
    """Аптечка из основы: белый чемоданчик с красным крестом."""
    return superheroes16.medkit()


tex_panels = tex_brick
tex_growth = tex_lab
tex_hull = tex_window
tex_cargo = tex_pods
tex_floor_grate = tex_floor_studs
tex_floor_tiles = tex_floor_carpet


def textures():
    return {"wall_planks": tex_brick(), "wall_stone": tex_lab(), "wall_pillar": tex_pillar(),
            "wall_exit": tex_exit(), "wall_cabin": tex_cabin(), "wall_hull": tex_window(), "wall_cargo": tex_pods(),
            "floor_planks": tex_floor(), "floor_stone": tex_floor_studs(), "floor_carpet": tex_floor_carpet(),
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
        items = sprites()
        for arg in sys.argv[1:]:
            if arg.startswith("--keys="):
                items = {k: items[k] for k in arg.split("=", 1)[1].split(",") if k}
        superheroes16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], superheroes16.shaded(items))
