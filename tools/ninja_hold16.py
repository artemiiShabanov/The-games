#!/usr/bin/env python3
"""Набор «Ниндзя» для шутера × 16/32-bit «до выхода» (#137), зеркало `space_hold16.py` и
`pixel_hold16.py`: те же ключи, размеры холстов, число и порядок кадров и точки опоры (ноги
врагов на 60-62 строке по центру кадра, клинок куная вверх по оси 64, текстуры 64×64 со швом
по краю).

Тема: покои и погреба замка чужого клана. Стены: белёная стена в деревянном каркасе с решёткой
под потолком, замшелая кладка подвала, красные лаковые колонны с золотыми обручами, ворота-выход
в красной раме с золотым гербом, покои с золотой ширмой (сосна и солнце), круглое окно на закат,
кладовая с бочками сакэ в соломе. Полы: доски, камни дорожки в гравии, татами. Враги: ниндзя
чужого клана в красном и чёрной маске, мечет сюрикены (`skel_*`), и стражник клана в соломенной
шляпе-конусе с катаной (`cut_*`). Кунай в руке героя (синий рукав, белая обмотка запястья,
красная кисть шнура), летящий кунай, ключ, ящичек лекаря, лицо ниндзя в капюшоне.

    python3 tools/ninja_hold16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ninja16  # noqa: E402
from ninja16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                     DARK, RED, VIOLET, PLUM)

T = 64


# --- Текстуры ----------------------------------------------------------------------------------

def _wall(period=32, lattice=True):
    """Белёная стена в деревянном каркасе: стойки через `period`, две балки, под верхней решётка
    (на каждой второй панели), внизу обшивка из досок и тёмный плинтус."""
    rng = random.Random(301)
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, WHITE)
    for _ in range(46):
        x, y = rng.randrange(T), rng.randrange(5, 40)
        c.set(x, y, GREY)
        if rng.random() < 0.3:
            c.set(x + 1, y, GREY)
    # Трещина в штукатурке и подтёк.
    x, y = 46, 26
    for _ in range(9):
        c.set(x, y, METAL)
        y += 1
        x += rng.choice((-1, 0, 0, 1))
    for y in range(25, 31):
        c.set(13, y, GREY)
    # Обшивка: вертикальные доски со швами и волокном.
    for y in range(40, 58):
        for x in range(T):
            px = x % 8
            col = BRASS
            if px == 0:
                col = DARK
            elif (x * 7 + y * 3) % 17 == 0 or (px == 5 and (y + x) % 9 < 4):
                col = TAN
            c.set(x, y, col)
    c.rect(0, 40, T - 1, 40, DARK)
    c.rect(0, 41, T - 1, 41, GOLD)
    # Плинтус.
    c.rect(0, 58, T - 1, T - 1, DARK)
    c.rect(0, 58, T - 1, 58, K)
    for x in range(2, T, 4):
        c.set(x, 61, METAL)
    # Балки: под потолком и на высоте притолоки, под каждой тень на штукатурке.
    for y0, h in ((0, 5), (20, 4)):
        c.rect(0, y0, T - 1, y0 + h - 1, BRASS)
        c.rect(0, y0, T - 1, y0, DARK if y0 == 0 else GOLD)
        c.rect(0, y0 + h - 1, T - 1, y0 + h - 1, DARK)
        c.rect(0, y0 + h, T - 1, y0 + h, GREY)
        for x in range(T):
            if (x * 5 + y0) % 13 == 0:
                c.set(x, y0 + 2, TAN)
    # Решётка под потолком: тёмный проём, тонкие рейки.
    if lattice:
        for x0 in range(0, T, period * 2):
            c.rect(x0 + 6, 7, x0 + period - 3, 18, DARK)
            for x in range(x0 + 6, x0 + period - 2, 4):
                c.rect(x, 7, x, 18, BRASS)
            c.rect(x0 + 6, 12, x0 + period - 3, 12, BRASS)
            c.rect(x0 + 5, 6, x0 + period - 2, 6, BRASS)
            c.rect(x0 + 5, 19, x0 + period - 2, 19, BRASS)
    # Стойки с золотыми шляпками гвоздей на перекрестьях.
    for x0 in range(0, T, period):
        c.rect(x0, 0, x0 + 3, 57, BRASS)
        c.rect(x0, 0, x0, 57, DARK)
        c.rect(x0 + 3, 0, x0 + 3, 57, DARK)
        c.rect(x0 + 4, 5, x0 + 4, 39, GREY)
        for y in (2, 21, 40):
            c.rect(x0 + 1, y, x0 + 2, y + 1, GOLD)
    return c


def tex_plaster():
    """Основная стена: штукатурка в каркасе, решётка, обшивка."""
    return _wall()


def tex_stone():
    """Подвал: кладка из крупных неровных камней (ряды со сдвигом, шов замкнут по горизонтали),
    светлая кромка сверху, мох на уступах."""
    rng = random.Random(302)
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, K)
    y0 = 0
    for h in (12, 10, 11, 10, 11, 10):
        start = rng.randrange(0, 12)
        pos = start
        cuts = []
        while pos < start + T:
            w = rng.randint(10, 19)
            if start + T - (pos + w) < 7:
                w = start + T - pos
            cuts.append((pos, w))
            pos += w
        for sx, w in cuts:
            body = rng.choice((METAL, METAL, METAL, GREY))
            light = WHITE if body == GREY else GREY
            dark = METAL if body == GREY else DARK
            mossy = rng.random() < 0.45
            for yy in range(1, h):
                for xx in range(1, w):
                    corner = (xx in (1, w - 1)) and (yy in (1, h - 1))
                    if corner:
                        continue
                    col = body
                    if yy == 1 or (yy == 2 and xx < w // 2 and (xx + sx) % 3):
                        col = light
                    elif yy == h - 1 or xx == w - 1:
                        col = dark
                    elif rng.random() < 0.08:
                        col = dark
                    c.set((sx + xx) % T, y0 + yy, col)
            if mossy:
                a = rng.randint(1, w // 2)
                b = rng.randint(a + 3, w - 1)
                for xx in range(a, b):
                    c.set((sx + xx) % T, y0 + 1, VIOLET)
                    drip = rng.choice((0, 1, 1, 2, 3))
                    for d in range(drip):
                        c.set((sx + xx) % T, y0 + 2 + d, PLUM if d == drip - 1 else VIOLET)
        y0 += h
    return c


def tex_pillar():
    """Колоннада: красные лаковые столбы с бликом, золотые обручи с заклёпками, тёмные капитель
    и база, на одном столбе бумажный оберег."""
    c = Canvas(T, T)
    ramp = {0: K, 1: TAN, 2: RED, 3: AQUA, 11: TAN, 12: TAN, 13: TAN, 14: DARK, 15: K}
    for x in range(T):
        c.rect(x, 0, x, T - 1, ramp.get(x % 16, RED))
    # Оберег: полоска бумаги с печатью и строкой знаков.
    c.rect(37, 20, 42, 39, WHITE)
    c.rect(37, 39, 42, 39, GREY)
    c.rect(38, 22, 41, 25, RED)
    for y in (28, 30, 33, 35):
        c.rect(38 + (y % 2), y, 40 + (y % 3) % 2, y, DARK)
    c.rect(39, 27, 39, 36, DARK)
    for y in (9, 47):
        c.rect(0, y, T - 1, y + 4, GOLD)
        c.rect(0, y, T - 1, y, SKY)
        c.rect(0, y + 4, T - 1, y + 4, BRASS)
        c.rect(0, y + 5, T - 1, y + 5, DARK)
        for x in range(T):
            if x % 16 in (0, 15):
                c.rect(x, y, x, y + 5, K)
            elif x % 16 in (12, 13, 14):
                c.rect(x, y + 1, x, y + 3, BRASS)
            elif x % 8 == 6:
                c.set(x, y + 2, DARK)
    for x in range(T):
        edge = x % 16 in (0, 15)
        c.rect(x, 0, x, 2, K if edge else DARK)
        c.set(x, 3, K if edge else METAL)
        c.rect(x, 58, x, T - 1, K if edge else DARK)
        c.set(x, 58, K if edge else METAL)
    return c


def tex_exit():
    """Ворота-выход: красная рама как у тории, табличка под перекладиной, створки из досок с
    железными полосами, большой золотой герб на обеих створках, кольца-ручки."""
    rng = random.Random(303)
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, DARK)
    # Створки.
    for y in range(12, 60):
        for x in range(7, 57):
            px = (x - 7) % 10
            col = BRASS
            if px == 0:
                col = DARK
            elif rng.random() < 0.12:
                col = TAN
            c.set(x, y, col)
    for y0 in (15, 51):
        c.rect(7, y0, 56, y0 + 3, DARK)
        c.rect(7, y0, 56, y0, METAL)
        for x in range(10, 56, 6):
            c.set(x, y0 + 2, GREY)
    # Герб: золотое кольцо, красный круг, золотой ромб в середине.
    c.ellipse(31.5, 33, 11, 11, K)
    c.ellipse(31.5, 33, 10, 10, GOLD)
    c.ellipse(31.5, 33, 7.5, 7.5, RED)
    c.poly([(31.5, 27), (37, 33), (31.5, 39), (26, 33)], GOLD)
    c.ellipse(31.5, 33, 1.6, 1.6, RED)
    for a in range(0, 360, 45):
        c.set(31.5 + 9 * math.cos(math.radians(a + 22)), 33 + 9 * math.sin(math.radians(a + 22)), BRASS)
    # Шов между створками и кольца.
    c.rect(31, 12, 32, 59, K)
    for cx in (25, 38):
        c.ellipse(cx, 47, 2.6, 2.6, GOLD)
        c.ellipse(cx, 47, 1.2, 1.2, DARK)
        c.set(cx, 44, SKY)
    # Рама: столбы и перекладины.
    for x0 in (0, 57):
        c.rect(x0, 0, x0 + 6, T - 1, RED)
        c.rect(x0 + 1, 0, x0 + 1, T - 1, AQUA)
        c.rect(x0 + 5, 0, x0 + 5, T - 1, TAN)
        c.rect(x0, 0, x0, T - 1, K)
        c.rect(x0 + 6, 0, x0 + 6, T - 1, K)
        c.rect(x0, 56, x0 + 6, T - 1, DARK)
        c.rect(x0, 56, x0 + 6, 56, METAL)
    c.rect(0, 0, T - 1, 3, DARK)
    c.rect(0, 0, T - 1, 0, K)
    c.rect(0, 3, T - 1, 3, GOLD)
    c.rect(7, 4, 56, 10, RED)
    c.rect(7, 5, 56, 5, AQUA)
    c.rect(7, 10, 56, 10, TAN)
    c.rect(7, 11, 56, 11, K)
    # Табличка с названием клана.
    c.rect(21, 2, 42, 10, GOLD)
    c.rect(22, 3, 41, 9, WHITE)
    for x in (25, 31, 37):
        c.rect(x, 4, x + 2, 4, DARK)
        c.rect(x + 1, 4, x + 1, 8, DARK)
        c.rect(x, 7, x + 2, 7, DARK)
        c.set(x + (x % 2) * 2, 8, DARK)
    # Порог.
    c.rect(7, 60, 56, T - 1, METAL)
    c.rect(7, 60, 56, 60, GREY)
    c.rect(7, 63, 56, 63, DARK)
    return c


def tex_cabin():
    """Покои господина: золотая ширма в шесть створок (облака заката, красное солнце, сосна),
    чёрная лаковая рама, внизу шкафчики с золотыми ручками."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = SKY if y < 22 or (y < 30 and (x + y) % 2 == 0) else GOLD
            c.set(x, y, col)
    # Облака полосами через всю ширму (замкнуты по горизонтали).
    for y0, ph in ((9, 0.0), (33, 2.0)):
        for x in range(T):
            y = y0 + 2 * math.sin(x * math.tau / 32.0 + ph)
            if math.sin(x * math.tau / 64.0 * 3 + ph) > -0.3:
                c.set(x, y, AQUA)
                c.set(x, y + 1, AQUA)
                c.set(x, y + 2, WHITE if y0 == 9 else SKY)
    # Солнце.
    c.ellipse(48, 15, 7, 7, RED)
    c.ellipse(46, 13, 2.5, 2.5, AQUA)
    # Сосна: кривой ствол и плоские шапки хвои.
    pts = [(9, 41), (11, 33), (16, 27), (17, 20), (23, 15)]
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], DARK, 3)
        c.line(a[0], a[1], b[0], b[1], BRASS, 1)
    c.line(13, 30, 26, 29, DARK, 2)
    c.line(17, 21, 8, 18, DARK, 2)
    for x, y, r in ((26, 13, 7), (8, 16, 5), (29, 27, 6), (17, 9, 5)):
        c.ellipse(x, y, r, 3, PLUM)
        c.ellipse(x - 1, y - 1, r - 1.5, 1.6, VIOLET)
    # Створки.
    for x in range(0, T, 16):
        c.rect(x, 0, x, 42, BRASS)
    for x in range(T):
        if x % 16 == 15:
            c.rect(x, 3, x, 42, GOLD if c.get(x, 20) == SKY else BRASS)
    # Рама.
    c.rect(0, 0, T - 1, 2, DARK)
    c.rect(0, 2, T - 1, 2, K)
    c.rect(0, 43, T - 1, 46, DARK)
    c.rect(0, 43, T - 1, 43, K)
    c.rect(0, 46, T - 1, 46, K)
    for x in range(7, T, 16):
        c.rect(x, 44, x + 1, 45, GOLD)
        c.set(x, 1, GOLD)
    # Шкафчики под ширмой.
    for y in range(47, 58):
        for x in range(T):
            px = x % 16
            col = BRASS
            if px in (0, 15) or y in (47, 57):
                col = DARK
            elif y == 48:
                col = GOLD
            elif (x * 3 + y * 5) % 11 == 0:
                col = TAN
            c.set(x, y, col)
    for x in range(7, T, 16):
        c.rect(x, 52, x + 1, 53, GOLD)
    c.rect(0, 58, T - 1, T - 1, DARK)
    c.rect(0, 58, T - 1, 58, K)
    return c


def tex_hull():
    """Стена с круглым окном: в проёме закат, красное солнце, горы и ветка клёна, поверх крест
    тонких реек."""
    c = _wall(64, False)
    cx, cy = 32, 27
    c.ellipse(cx, cy, 17, 17, K)
    c.ellipse(cx, cy, 16, 16, BRASS)
    c.ellipse(cx, cy, 14, 14, DARK)
    for y in range(cy - 13, cy + 14):
        for x in range(cx - 13, cx + 14):
            if (x - cx) ** 2 + (y - cy) ** 2 > 13 ** 2:
                continue
            d = y - (cy - 13)
            col = NAVY if d < 5 else (SEA if d < 10 else (AQUA if d < 17 else SKY))
            if d in (5, 10, 17) and x % 2:
                col = {5: NAVY, 10: SEA, 17: AQUA}[d]
            # Солнце над горами.
            if (x - 35) ** 2 + (y - 29) ** 2 <= 22:
                col = RED
            # Горы: два пологих силуэта.
            ridge = cy + 9 - 6 * max(0.0, 1 - abs(x - 25) / 9.0) - 4 * max(0.0, 1 - abs(x - 41) / 7.0)
            if y >= ridge:
                col = NAVY
            c.set(x, y, col)
    # Ветка клёна сверху слева.
    c.line(20, 20, 28, 18, DARK, 1)
    for x, y in ((23, 21), (27, 20), (30, 17)):
        c.set(x, y, RED)
        c.set(x + 1, y, RED)
        c.set(x, y + 1, RED)
    # Крест тонких реек и блик рамы.
    c.rect(cx, cy - 13, cx, cy + 13, BRASS)
    c.rect(cx - 13, cy + 3, cx + 13, cy + 3, BRASS)
    for a in range(200, 260, 4):
        c.set(cx + 15.5 * math.cos(math.radians(a)), cy + 15.5 * math.sin(math.radians(a)), GOLD)
    return c


def tex_cargo():
    """Кладовая: штабель бочек сакэ в соломенной оплётке 32×32 со сдвигом ряда: верёвки, косая
    штриховка соломы, бумажный ярлык со знаком."""
    c = Canvas(T, T)
    for by in (0, 32):
        for bx in (0, 32):
            off = 16 if by == 32 else 0
            x0 = (bx + off) % T
            mark = (bx // 32 + by // 32) % 2
            for ly in range(32):
                for x in range(32):
                    col = SKY
                    if x in (0, 31) or ly in (0, 31):
                        col = K
                    elif x < 3:
                        col = GOLD
                    elif x > 27:
                        col = BRASS
                    elif x > 22:
                        col = GOLD
                    if col != K:
                        if ly in (1, 2, 29, 30):
                            col = DARK if ly in (2, 29) else BRASS
                        elif ly in (6, 7, 24, 25):
                            col = BRASS if (x + ly) % 4 else DARK
                        elif (x + ly) % 6 == 0 and col == SKY:
                            col = GOLD
                        elif (x - ly) % 9 == 0 and col == SKY:
                            col = BRASS
                    c.set((x0 + x) % T, by + ly, col)
            # Ярлык.
            for x in range(8, 23):
                for ly in range(10, 22):
                    edge = x in (8, 22) or ly in (10, 21)
                    c.set((x0 + x) % T, by + ly, GREY if edge else WHITE)
            if mark:
                for x in range(12, 19):
                    for ly in range(12, 20):
                        if (x - 15) ** 2 + (ly - 15.5) ** 2 <= 10:
                            c.set((x0 + x) % T, by + ly, RED)
            else:
                for x in range(11, 20):
                    c.set((x0 + x) % T, by + 13, DARK)
                    c.set((x0 + x) % T, by + 17, DARK)
                for ly in range(12, 20):
                    c.set((x0 + 15) % T, by + ly, DARK)
                c.set((x0 + 12) % T, by + 19, DARK)
                c.set((x0 + 18) % T, by + 19, DARK)
                c.set((x0 + 20) % T, by + 19, RED)
                c.set((x0 + 20) % T, by + 18, RED)
    return c


def tex_floor():
    """Дощатый пол: узкие доски со стыками вразбежку, волокно, гвозди у стыков."""
    rng = random.Random(304)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            board = x // 8
            px = x % 8
            joint = (y + board * 19) % T == 0
            col = BRASS
            if px == 0 or joint:
                col = DARK
            elif px == 1 and (y + board * 5) % 13 < 3:
                col = GOLD
            c.set(x, y, col)
    for _ in range(40):
        x, y = rng.randrange(T), rng.randrange(T)
        n = rng.randint(3, 7)
        for d in range(n):
            if c.get(x, (y + d) % T) == BRASS:
                c.set(x, (y + d) % T, TAN)
    for board in range(8):
        y = (-board * 19) % T
        for dy in (2, -3):
            c.set(board * 8 + 4, (y + dy) % T, K)
    return c


def tex_floor_stone():
    """Дорожка: плоские камни в гравии, мох по краям камней."""
    rng = random.Random(305)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            r = rng.random()
            c.set(x, y, DARK if r < 0.22 else (GREY if r < 0.30 else METAL))
    for sx, sy, rx, ry in ((15, 13, 11, 8), (47, 18, 10, 9), (13, 45, 9, 9), (44, 49, 12, 8)):
        c.ellipse(sx + 1, sy + 1, rx + 0.5, ry + 0.5, K)
        c.ellipse(sx, sy, rx, ry, METAL)
        c.ellipse(sx - 0.5, sy - 0.5, rx - 1, ry - 1, GREY)
        c.ellipse(sx - 2, sy - 2, rx - 4, ry - 4, WHITE)
        c.ellipse(sx - 1, sy - 1, rx - 5, ry - 5, GREY)
        for _ in range(7):
            a = rng.uniform(1.6, 3.4)
            c.set(sx + (rx - 1) * math.cos(a), sy + (ry - 1) * math.sin(a), VIOLET)
            c.set(sx + rx * math.cos(a + 0.1), sy + ry * math.sin(a + 0.1), PLUM)
        c.set(sx + 2, sy + 1, METAL)
        c.set(sx + 3, sy + 2, METAL)
    return c


def tex_floor_tatami():
    """Татами: маты 32×32, плетение через мат то вдоль, то поперёк, тёмно-зелёная кайма с золотой
    ниткой."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 32, y % 32
            along = (x // 32 + y // 32) % 2 == 0
            u, v = (px, py) if along else (py, px)
            col = SKY
            if v % 4 == 3:
                col = GOLD
            elif (u + v * 3) % 11 == 0:
                col = GOLD
            if v < 3 or v > 29:
                col = PLUM
                if v in (1, 31) and u % 4 == 1:
                    col = GOLD
            if v == 0 or u == 0:
                col = DARK
            c.set(x, y, col)
    return c


def tex_ceiling():
    """Потолок: тёмные кессоны, через 32 пикселя балка со светлой кромкой, на балках редкие
    огоньки фонарей (без ярких полос, иначе в перспективе они расходятся лучами)."""
    rng = random.Random(306)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = DARK
            if x % 16 == 0:
                col = K
            if y % 32 < 6:
                col = BRASS if y % 32 == 1 and x % 16 else DARK
                if y % 32 == 5:
                    col = K
            c.set(x, y, col)
    for _ in range(26):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == DARK:
            c.set(x, y, K)
    for y in (2, 34):
        for x in (8, 40):
            c.rect(x, y, x + 1, y + 1, GOLD)
            c.set(x, y + 2, RED)
            c.set(x + 1, y + 2, RED)
    return c


# --- Чужой клан --------------------------------------------------------------------------------

def _star(c, x, y, r=3):
    """Сюрикен в четыре луча с отверстием."""
    c.line(x - r, y, x + r, y, GREY, 1)
    c.line(x, y - r, x, y + r, GREY, 1)
    c.rect(x - 1, y - 1, x + 1, y + 1, GREY)
    c.set(x, y, K)
    c.set(x - 1, y - 1, WHITE)


def _katana(c, hand, tip, tail):
    """Катана: рукоять от `tail` до кисти, золотая цуба, клинок до `tip` со светлой кромкой."""
    c.line(tail[0], tail[1], hand[0], hand[1], DARK, 2)
    dx, dy = tip[0] - hand[0], tip[1] - hand[1]
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    sx, sy = hand[0] + ux * 3, hand[1] + uy * 3
    c.line(sx, sy, tip[0], tip[1], GREY, 2)
    c.line(sx - 1, sy, tip[0] - 1, tip[1] + 1, WHITE, 1)
    c.line(sx - uy * 2.5, sy + ux * 2.5, sx + uy * 2.5, sy - ux * 2.5, GOLD, 2)
    c.ellipse(hand[0], hand[1], 2, 2, DARK)


def _kasa(c, hx, y, tilt=0):
    """Соломенная шляпа-конус: поля на строке `y`, макушка на девять строк выше."""
    c.poly([(hx - 12, y + tilt), (hx, y - 9), (hx + 12, y - tilt)], GOLD)
    c.line(hx - 12, y + 1 + tilt, hx + 12, y + 1 - tilt, BRASS, 1)
    c.line(hx, y - 8, hx - 6, y - 1 + tilt * 0.5, BRASS, 1)
    c.line(hx + 1, y - 8, hx + 6, y - 1 - tilt * 0.5, BRASS, 1)
    c.line(hx - 9, y - 2 + tilt, hx + 9, y - 2 - tilt, BRASS, 1)
    c.rect(hx - 1, y - 10, hx + 1, y - 9, DARK)


def _fallen(k, guard):
    """Падение: кадр 1 на коленях, заваливается вперёд; кадр 2 лежит, оружие рядом."""
    c = Canvas(T, T)
    cx = 32
    thigh = DARK if guard else RED
    shin = WHITE if guard else DARK
    if k == 1:
        c.rect(cx - 12, 58, cx + 1, 61, shin)
        c.rect(cx - 16, 57, cx - 12, 62, DARK)
        c.rect(cx - 12, 62, cx + 1, 62, DARK if guard else K)
        c.line(cx - 1, 56, cx + 5, 49, thigh, 8)
        c.line(cx + 5, 47, cx + 8, 35, RED, 12)
        c.line(cx + 1, 48, cx + 11, 51, DARK, 3)
        if guard:
            for t in (0.25, 0.5, 0.75):
                for d in range(-4, 5, 2):
                    c.set(cx + 5 + 3 * t + d, 47 - 12 * t - d * 0.25, GOLD)
        else:
            c.line(cx + 9, 36, cx + 3, 46, TAN, 1)
        # Рука повисла, кисть у пола.
        c.line(cx + 11, 35, cx + 16, 48, RED, 4)
        c.ellipse(cx + 17, 51, 2, 2, DARK)
        hx, hy = cx + 12, 26
        c.line(cx + 9, 31, hx, hy, DARK, 4)
        if guard:
            c.ellipse(hx, hy, 4.5, 5, SKIN)
            for yy in range(hy + 2, hy + 6):
                for xx in range(hx - 5, hx + 6):
                    if c.get(xx, yy) == SKIN:
                        c.set(xx, yy, DARK)
            for yy in range(hy - 6, hy - 2):
                for xx in range(hx - 5, hx + 6):
                    if c.get(xx, yy) == SKIN:
                        c.set(xx, yy, DARK)
            c.rect(hx - 2, hy - 7, hx, hy - 6, DARK)
            # Шляпа слетает назад.
            _kasa(c, hx - 9, hy - 8, 3)
            c.line(hx - 3, hy - 4, hx - 6, hy - 8, RED, 1)
        else:
            c.line(hx - 4, hy - 2, hx - 10, hy - 6, DARK, 2)
            c.line(hx - 4, hy, hx - 11, hy - 1, DARK, 2)
            c.ellipse(hx, hy, 5, 5.5, DARK)
            c.rect(hx - 1, hy - 1, hx + 5, hy, SKIN)
            c.line(cx + 3, 34, cx - 2, 27, DARK, 2)
            c.rect(cx - 3, 26, cx - 2, 27, GOLD)
        # Оружие выпало.
        if guard:
            _katana(c, (cx + 21, 50), (cx + 27, 30), (cx + 20, 55))
        else:
            _star(c, cx + 23, 44, 3)
        c.finish()
        if guard:
            c.rect(hx + 1, hy, hx + 3, hy, K)
        else:
            c.rect(hx + 1, hy, hx + 3, hy, K)
        return c
    # Лежит на спине, головой вправо.
    c.line(cx - 21, 59, cx - 12, 59, shin, 4)
    c.rect(cx - 26, 55, cx - 23, 61, DARK)
    c.line(cx - 12, 58, cx - 3, 58, thigh, 6)
    c.line(cx - 1, 57, cx + 9, 57, RED, 9)
    c.rect(cx - 4, 54, cx - 3, 61, DARK)
    c.rect(cx - 5, 56, cx - 5, 57, GOLD)
    if guard:
        for x in range(cx, cx + 9, 2):
            c.set(x, 55, GOLD)
            c.set(x + 1, 58, GOLD)
    else:
        c.line(cx - 2, 55, cx + 8, 60, TAN, 1)
    c.line(cx + 2, 60, cx + 10, 61, RED, 3)
    c.ellipse(cx + 12, 61, 1.6, 1.4, DARK)
    hx, hy = cx + 15, 57
    if guard:
        c.ellipse(hx, hy, 5, 4.5, SKIN)
        for yy in range(hy - 5, hy + 6):
            for xx in range(hx - 6, hx - 1):
                if c.get(xx, yy) == SKIN:
                    c.set(xx, yy, DARK)
        # Шляпа откатилась и стоит на ребре.
        c.poly([(cx + 17, 49), (cx + 27, 46), (cx + 26, 61)], GOLD)
        c.line(cx + 27, 47, cx + 26, 61, BRASS, 1)
        c.line(cx + 18, 50, cx + 26, 54, BRASS, 1)
        c.line(cx + 22, 48, cx + 26, 57, BRASS, 1)
        # Катана воткнулась в пол.
        c.rect(cx - 29, 30, cx - 28, 39, DARK)
        c.rect(cx - 31, 40, cx - 27, 41, GOLD)
        c.rect(cx - 29, 42, cx - 28, 61, GREY)
        c.rect(cx - 29, 42, cx - 29, 61, WHITE)
        c.rect(cx - 29, 33, cx - 28, 33, GREY)
        c.rect(cx - 29, 36, cx - 28, 36, GREY)
    else:
        c.ellipse(hx, hy, 5.5, 5, DARK)
        c.rect(hx, hy - 3, hx + 1, hy + 2, SKIN)
        c.line(hx + 4, hy + 3, hx + 10, hy + 4, DARK, 2)
        c.line(hx + 4, hy + 1, hx + 9, hy - 1, DARK, 2)
        # Меч в ножнах под спиной.
        c.line(cx - 8, 62, cx + 12, 62, DARK, 1)
        c.rect(cx + 12, 62, cx + 14, 62, GOLD)
    c.finish()
    c.set(hx, hy - 1, K) if not guard else c.rect(hx + 1, hy - 2, hx + 1, hy - 1, K)
    return c


def clansman(angle, phase, mode="walk", guard=False):
    """Боец чужого клана 64×64 в ракурсе `angle` (0 спереди … 4 со спины, лицом вправо на 1-3),
    шаг `phase` 0/1. `mode`: walk, aim, fire, slash, die0..die2, hurt. Без `guard` ниндзя в
    красном и чёрной маске с завязками, рукоять меча над плечом, в руке сюрикен. `guard`
    стражник: шляпа-конус, полумаска, красный доспех с золотой шнуровкой, тёмные хакама, катана.
    Ступни на 60-62 строке, ось по центру кадра, как у скелета пиратов."""
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    turned = side or diag
    if mode.startswith("die"):
        k = int(mode[-1])
        if k == 0:
            return clansman(0, 0, "hurt", guard)
        return _fallen(k, guard)
    c = Canvas(T, T)
    bob = 1 if phase else 0
    # Ноги: у ниндзя красные штаны до колена и тёмные голени, у стражника широкие хакама и
    # белые обмотки; таби тёмные.
    for sign in (-1, 1):
        near = sign > 0 or not turned
        if turned:
            amp = 6 if side else 4
            hip = cx + sign * (1 if side else 3)
            foot = hip + sign * amp * (1 if phase == 0 else -1)
            knee = (hip + foot) / 2.0 + 2
            lift = 0
        else:
            hip = cx + sign * 4
            lift = 2 if (sign > 0) == bool(phase) and mode == "walk" else 0
            foot = hip + sign
            knee = hip + sign * 0.5
        if guard:
            c.line(hip, 41 - bob, knee, 50 - lift, DARK, 8)
            c.line(knee, 52 - lift, foot, 58 - lift, WHITE if near else GREY, 4)
        else:
            c.line(hip, 41 - bob, knee, 50 - lift, RED if near else TAN, 6)
            c.line(knee, 51 - lift, foot, 58 - lift, DARK, 4)
            c.rect(knee - 2, 51 - lift, knee + 2, 51 - lift, GOLD if near else BRASS)
        c.rect(foot - (2 if turned else 3), 60 - lift, foot + (4 if turned else 2), 62 - lift, DARK)
    top = 20 - bob
    sh = top + 2
    w = 5 if side else (7 if diag else 8)
    f = 2 if turned else 0
    # Дальняя рука за корпусом.
    if turned:
        c.line(cx - 2, sh + 1, cx - 6, 31 - bob, TAN, 4)
        c.ellipse(cx - 7, 33 - bob, 1.8, 1.8, DARK)
    # Корпус.
    c.rect(cx - w, top, cx + w, 39 - bob, RED)
    c.rect(cx - w, top, cx - w, top, None)
    c.rect(cx + w, top, cx + w, top, None)
    if guard:
        # Доспех: ряды золотой шнуровки, юбка из пластин.
        for yy in (top + 4, top + 8, top + 12):
            for xx in range(cx - w + 2, cx + w - 1, 2):
                c.set(xx, yy, GOLD)
            c.rect(cx - w + 1, yy + 1, cx + w - 1, yy + 1, TAN)
        c.rect(cx - w - 1, 39 - bob, cx + w + 1, 44 - bob, RED)
        for xx in range(cx - w - 1, cx + w + 2):
            if (xx - cx) % 5 == 2:
                c.rect(xx, 39 - bob, xx, 44 - bob, DARK)
            elif (xx - cx) % 5 == 4:
                c.set(xx, 43 - bob, GOLD)
    elif back:
        # Меч в ножнах наискось через спину, ремень.
        c.line(cx + w - 1, top + 2, cx - w + 1, 35 - bob, TAN, 1)
        c.line(cx - 5, top + 1, cx + 6, 36 - bob, DARK, 3)
        c.rect(cx + 6, 36 - bob, cx + 7, 37 - bob, GOLD)
    else:
        # Запах куртки и тёмный ворот.
        c.poly([(cx - 3 + f, top), (cx + 3 + f, top), (cx + f, top + 6)], DARK)
        c.line(cx + 2 + f, top + 4, cx - w + 2 + f, 35 - bob, TAN, 1)
        c.line(cx - 2 + f, top + 4, cx - 3 + f, top + 6, TAN, 1)
    c.rect(cx - w, 36 - bob, cx + w, 38 - bob, DARK)
    if not back:
        c.rect(cx - 1 + f, 36 - bob, cx + f, 37 - bob, GOLD)
    else:
        c.rect(cx - 1, 35 - bob, cx + 1, 38 - bob, DARK)
    # Рукоять меча над левым плечом ниндзя.
    if not guard:
        hx0 = cx - (3 if side else 6)
        c.line(hx0, top + 1, hx0 - 4, top - 6, DARK, 2)
        c.rect(hx0 - 2, top - 1, hx0 + 1, top - 1, GOLD)
        c.rect(hx0 - 5, top - 7, hx0 - 4, top - 6, GOLD)
    # Голова.
    hx = cx + (2 if side else (1 if diag else 0))
    hy = 12 - bob
    c.rect(hx - 2, 17 - bob, hx + 2, top, DARK)
    if guard:
        c.ellipse(hx, hy + 2, 4.5, 5, DARK if back else SKIN)
        if back:
            c.rect(hx - 1, hy + 6, hx + 1, hy + 9, DARK)
            c.rect(hx - 1, hy + 7, hx + 1, hy + 7, RED)
        else:
            for yy in range(hy + 4, hy + 8):
                for xx in range(hx - 5, hx + 6):
                    if c.get(xx, yy) == SKIN:
                        c.set(xx, yy, DARK)
            if turned:
                for yy in range(hy, hy + 5):
                    for xx in range(hx - 5, hx - (2 if side else 3) + 1):
                        if c.get(xx, yy) == SKIN:
                            c.set(xx, yy, DARK)
            # Шнур шляпы под подбородок.
            if turned:
                c.line(hx - 1, hy + 2, hx, hy + 6, RED, 1)
            else:
                c.set(hx - 4, hy + 4, RED)
                c.set(hx + 4, hy + 4, RED)
                c.rect(hx - 1, hy + 7, hx + 1, hy + 7, RED)
        _kasa(c, hx, hy)
    else:
        s = 1 if phase else 0
        if angle == 4:
            pass
        elif turned:
            c.line(hx - 4, hy - 1, hx - 10, hy - 3 + s, DARK, 2)
            c.line(hx - 4, hy + 1, hx - 9, hy + 4 - s, DARK, 2)
        else:
            c.line(hx + 4, hy - 1, hx + 9, hy - 3 + s, DARK, 2)
            c.line(hx + 4, hy + 1, hx + 9, hy + 4 - s, DARK, 2)
        c.ellipse(hx, hy, 5, 5.5, DARK)
        if angle == 4:
            # Узел маски на затылке и два конца вниз.
            c.rect(hx - 1, hy + 1, hx + 1, hy + 2, METAL)
            c.line(hx - 1, hy + 3, hx - 3, hy + 11 + s, DARK, 2)
            c.line(hx + 1, hy + 3, hx + 3, hy + 10 - s, DARK, 2)
        elif angle == 3:
            c.rect(hx - 4, hy, hx - 3, hy + 1, METAL)
        elif side:
            c.rect(hx + 1, hy - 1, hx + 5, hy, SKIN)
        elif diag:
            c.rect(hx - 2, hy - 1, hx + 5, hy, SKIN)
        else:
            c.rect(hx - 4, hy - 1, hx + 4, hy, SKIN)
    # Руки и оружие.
    star = None
    if guard:
        if not side:
            # Наплечники.
            for sx in ((cx - w - 3, cx + w) if not diag else (cx - w - 2,)):
                c.rect(sx, top, sx + 3, top + 6, DARK)
                c.rect(sx, top + 3, sx + 3, top + 3, RED)
                c.rect(sx, top + 6, sx + 3, top + 6, GOLD)
        if turned:
            c.line(cx + 1, sh + 1, cx + 9, 29 - bob, RED, 4)
            c.rect(cx - 2, top, cx + 4, top + 5, DARK)
            c.rect(cx - 2, top + 3, cx + 4, top + 3, RED)
            c.rect(cx - 2, top + 6, cx + 4, top + 6, GOLD)
            _katana(c, (cx + 11, 30 - bob), (cx + 25, 12 - bob), (cx + 8, 35 - bob))
        elif mode == "slash":
            c.line(cx - w - 1, sh + 1, cx - w - 2, 30, RED, 4)
            c.ellipse(cx - w - 2, 32, 2, 2, DARK)
            c.line(cx + w + 1, sh + 1, cx + 14, 16, RED, 4)
            _katana(c, (cx + 14, 13), (cx + 19, 1), (cx + 12, 18))
        else:
            d = 1 if phase else 0
            c.line(cx - w - 1, sh + 1, cx - w - 2, 30 - bob + d, RED, 4)
            c.ellipse(cx - w - 2, 32 - bob + d, 2, 2, DARK)
            c.line(cx + w + 1, sh + 1, cx + w + 3, 29 - bob, RED, 4)
            _katana(c, (cx + w + 3, 31 - bob), (cx + w + 10, 9 - bob), (cx + w + 2, 36 - bob))
    elif turned:
        c.line(cx + 1, sh + 1, cx + 8, 29 - bob, RED, 4)
        c.line(cx, sh + 3, cx + 6, 31 - bob, TAN, 1)
        c.ellipse(cx + 10, 30 - bob, 2, 2, DARK)
        if not back:
            star = (cx + 14, 29 - bob, 3)
    elif mode == "aim":
        # Замах: рука с сюрикеном отведена к уху, другая вытянута на цель.
        c.line(cx - w - 1, sh + 1, cx - w - 3, 30, RED, 4)
        c.ellipse(cx - w - 3, 33, 2, 2, DARK)
        c.line(cx - w + 1, sh + 3, cx - w + 1, 34, TAN, 1)
        c.line(cx + w + 1, sh + 1, cx + 14, 15, RED, 4)
        c.ellipse(cx + 14, 12, 2, 2, DARK)
        star = (cx + 14, 7, 4)
    elif mode == "fire":
        # Бросок: рука выброшена на игрока, кисть крупнее.
        c.line(cx - w - 1, sh + 1, cx - w - 3, 30, RED, 4)
        c.ellipse(cx - w - 3, 32, 2, 2, DARK)
        c.line(cx + w + 1, sh + 1, cx + 5, 28, RED, 5)
        c.ellipse(cx + 3, 30, 3, 3, DARK)
    else:
        d = 1 if phase else -1
        c.line(cx - w - 1, sh + 1, cx - w - 2, 30 - bob + d, RED, 4)
        c.ellipse(cx - w - 2, 33 - bob + d, 2, 2, DARK)
        c.line(cx + w + 1, sh + 1, cx + w + 2, 30 - bob - d, RED, 4)
        c.ellipse(cx + w + 2, 33 - bob - d, 2, 2, DARK)
        c.line(cx - w + 1, sh + 3, cx - w + 1, 34 - bob, TAN, 1)
        c.line(cx + w - 1, sh + 3, cx + w - 1, 34 - bob, TAN, 1)
        if not back:
            star = (cx + w + 3, 37 - bob - d, 2)
    if star:
        _star(c, *star)
    c.finish()
    # Глаза после обводки.
    ey = hy + 3 if guard else hy
    if not back:
        if side:
            c.set(hx + 3, ey, K)
            c.set(hx + 3, ey - 1, K)
        elif diag:
            c.set(hx, ey, K)
            c.set(hx + 3, ey, K)
        else:
            c.set(hx - 2, ey, K)
            c.set(hx + 2, ey, K)
            if not guard:
                c.rect(hx - 1, ey - 1, hx + 1, ey - 1, DARK)
                c.set(hx, ey, DARK)
    if mode == "fire":
        # Сюрикен летит в камеру: крупная звезда со светом на лучах.
        fx, fy = cx + 3, 30
        c.poly([(fx, fy - 8), (fx + 2, fy - 2), (fx + 8, fy), (fx + 2, fy + 2), (fx, fy + 8), (fx - 2, fy + 2),
                (fx - 8, fy), (fx - 2, fy - 2)], WHITE)
        c.line(fx - 5, fy - 5, fx + 5, fy + 5, SKY, 1)
        c.line(fx - 5, fy + 5, fx + 5, fy - 5, SKY, 1)
        c.rect(fx - 1, fy - 1, fx + 1, fy + 1, GREY)
        c.set(fx, fy, K)
    if mode == "hurt":
        for x in range(T):
            for y in range(T):
                if c.get(x, y) in (RED, TAN, DARK) and (x + y) % 3 == 0:
                    c.set(x, y, WHITE)
    return c


def clan_strips():
    out = {}
    for name, guard in (("skel", False), ("cut", True)):
        walk = []
        for a in range(5):
            for ph in range(2):
                walk.append(clansman(a, ph, "walk", guard))
        out[name + "_walk"] = strip(walk)
        out[name + "_die"] = strip([clansman(0, 0, "die%d" % k, guard) for k in range(3)])
    out["skel_fire"] = strip([clansman(0, 0, "aim"), clansman(0, 0, "fire")])
    out["cut_slash"] = strip([clansman(0, 0, "walk", True), clansman(0, 0, "slash", True)])
    return out


# --- Предметы, оружие, лицо --------------------------------------------------------------------

def shot():
    """Снаряд чужого клана: сюрикен основы, обводка красная."""
    return ninja16.shot()


def bullet():
    """Кунай героя остриём вглубь: светлый лист клинка, тёмная рукоять, золотое кольцо."""
    c = Canvas(16, 16)
    c.poly([(7.5, 1), (10, 6), (8, 9), (7, 9), (5, 6)], GREY)
    c.rect(7, 2, 7, 8, WHITE)
    c.rect(6, 5, 6, 7, WHITE)
    c.rect(7, 9, 8, 11, DARK)
    c.rect(6, 12, 9, 14, GOLD)
    c.rect(7, 13, 8, 13, None)
    return c.finish()


def decor(kind):
    """Ориентир зала 64×64, низ на 62-63 строке: 0 рисовые тюки пирамидой, 1 лаковые ларцы,
    2 каменный фонарь, 3 мортира для фейерверка, 4 бамбуковая клетка, 5 барабан тайко."""
    c = Canvas(T, T)
    if kind == 0:
        for bx, by in ((18, 62), (46, 62), (32, 46)):
            c.rect(bx - 10, by - 16, bx + 10, by - 1, GOLD)
            c.ellipse(bx - 10, by - 8.5, 3.4, 7.6, SKY)
            c.ellipse(bx + 10, by - 8.5, 3.4, 7.6, GOLD)
            c.rect(bx - 10, by - 15, bx + 10, by - 14, SKY)
            # Солома: редкие длинные штрихи, три верёвки, торец с узлом.
            for y, x0, x1 in ((by - 11, bx - 8, bx - 3), (by - 6, bx - 9, bx - 5), (by - 9, bx + 3, bx + 8),
                              (by - 4, bx + 2, bx + 9)):
                c.rect(x0, y, x1, y, BRASS)
            for x in (bx - 6, bx, bx + 6):
                c.rect(x, by - 16, x + 1, by - 1, BRASS)
                c.rect(x + 1, by - 16, x + 1, by - 1, DARK)
            c.ellipse(bx - 12, by - 8.5, 1.3, 3, BRASS)
            c.set(bx - 12, by - 9, DARK)
    elif kind == 1:
        # Нижний ларь в чёрном лаке, на нём красный ларец с гербом и свиток.
        c.rect(8, 38, 55, 62, DARK)
        c.rect(8, 38, 55, 39, METAL)
        c.rect(8, 44, 55, 44, K)
        for x in (8, 51):
            c.rect(x, 38, x + 4, 42, GOLD)
            c.rect(x, 58, x + 4, 62, GOLD)
        c.rect(29, 42, 34, 49, GOLD)
        c.rect(31, 45, 32, 47, K)
        c.line(12, 52, 51, 52, RED, 1)
        c.rect(18, 18, 45, 37, RED)
        c.rect(18, 18, 45, 19, AQUA)
        c.rect(18, 23, 45, 23, TAN)
        c.ellipse(31.5, 30, 4.5, 4.5, GOLD)
        c.ellipse(31.5, 30, 2.5, 2.5, RED)
        for x in (18, 43):
            c.rect(x, 34, x + 2, 37, GOLD)
        c.rect(22, 13, 40, 17, WHITE)
        c.rect(22, 13, 23, 17, BRASS)
        c.rect(39, 13, 40, 17, BRASS)
        c.rect(30, 13, 32, 17, RED)
    elif kind == 2:
        # Каменный фонарь: основание, столб, площадка, камера с огнём, крыша с загнутыми углами.
        c.rect(21, 58, 42, 63, METAL)
        c.rect(24, 55, 39, 58, GREY)
        c.rect(28, 35, 35, 55, GREY)
        c.rect(33, 35, 35, 55, METAL)
        c.rect(20, 31, 43, 35, GREY)
        c.rect(20, 34, 43, 35, METAL)
        c.rect(24, 17, 39, 31, GREY)
        c.rect(27, 19, 36, 29, DARK)
        c.rect(28, 20, 35, 28, GOLD)
        c.ellipse(31.5, 25, 2.5, 3, SKY)
        c.rect(31, 19, 32, 29, DARK)
        c.poly([(13, 17), (50, 17), (40, 9), (23, 9)], METAL)
        c.rect(13, 16, 50, 17, GREY)
        c.rect(12, 13, 14, 16, GREY)
        c.rect(49, 13, 51, 16, GREY)
        c.rect(29, 6, 34, 9, GREY)
        c.ellipse(31.5, 4, 2.6, 2.6, GREY)
        for x, y in ((18, 15), (20, 14), (25, 11), (27, 10), (22, 57), (24, 56), (29, 43), (29, 44)):
            c.set(x, y, VIOLET)
            c.set(x + 1, y, VIOLET)
            c.set(x + 1, y + 1, PLUM)
    elif kind == 3:
        # Мортира: толстый ствол в обручах наклонён на станке, рядом ракета с фитилём.
        c.line(22, 46, 12, 62, BRASS, 4)
        c.line(30, 44, 42, 62, BRASS, 4)
        c.rect(9, 60, 46, 62, BRASS)
        c.rect(9, 62, 46, 62, DARK)
        c.line(22, 48, 38, 20, DARK, 17)
        for t in (0.12, 0.45, 0.8):
            px, py = 22 + 16 * t, 48 - 28 * t
            c.line(px - 7.4, py - 4.2, px + 7.4, py + 4.2, GOLD, 3)
        c.ellipse(39, 18, 7, 4.5, METAL)
        c.ellipse(39.5, 17.5, 4.5, 2.6, K)
        c.line(16, 50, 11, 46, BRASS, 1)
        c.ellipse(10, 45, 1.6, 1.6, GOLD)
        # Ракета у станка.
        c.rect(52, 34, 53, 62, BRASS)
        c.rect(49, 32, 56, 48, RED)
        c.rect(49, 37, 56, 39, WHITE)
        c.rect(49, 44, 56, 45, GOLD)
        c.poly([(49, 32), (56, 32), (52.5, 24)], RED)
    elif kind == 4:
        # Клетка: бамбуковые прутья с перевязками, шест для переноски, замок.
        c.rect(14, 18, 50, 56, DARK)
        for x in range(17, 50, 6):
            c.rect(x, 18, x, 56, NAVY)
        for x in range(14, 51, 6):
            c.rect(x - 1, 14, x + 1, 60, GOLD)
            c.rect(x + 1, 14, x + 1, 60, BRASS)
            for y in (26, 46):
                c.rect(x - 1, y, x + 1, y, PLUM)
        c.rect(10, 14, 54, 18, GOLD)
        c.rect(10, 17, 54, 18, BRASS)
        c.rect(10, 56, 54, 61, GOLD)
        c.rect(10, 60, 54, 61, BRASS)
        c.rect(12, 35, 52, 37, GOLD)
        c.rect(12, 37, 52, 37, BRASS)
        for x in range(14, 51, 6):
            c.rect(x - 1, 15, x + 1, 16, DARK)
            c.rect(x - 1, 57, x + 1, 58, DARK)
            c.rect(x - 1, 35, x + 1, 36, DARK)
        c.rect(4, 8, 60, 11, BRASS)
        c.rect(4, 8, 60, 8, GOLD)
        for x in (18, 44):
            c.rect(x, 11, x + 1, 14, DARK)
        c.rect(12, 62, 16, 62, BRASS)
        c.rect(48, 62, 52, 62, BRASS)
        c.rect(29, 38, 35, 44, METAL)
        c.rect(31, 40, 33, 42, K)
        c.rect(30, 36, 34, 37, GREY)
    else:
        # Тайко: кожа с красным знаком, обод в заклёпках, на козлах крест-накрест, палочки.
        c.line(22, 40, 12, 62, BRASS, 4)
        c.line(42, 40, 52, 62, BRASS, 4)
        c.rect(15, 54, 49, 56, BRASS)
        c.rect(15, 56, 49, 56, DARK)
        c.ellipse(32, 25, 21, 21, RED)
        c.ellipse(32, 25, 19, 19, BRASS)
        c.ellipse(32, 25, 16, 16, WHITE)
        c.ellipse(34, 27, 13, 13, SKY)
        c.ellipse(31, 24, 13, 13, WHITE)
        for a in range(0, 360, 20):
            c.set(32 + 17.6 * math.cos(math.radians(a)), 25 + 17.6 * math.sin(math.radians(a)), DARK)
        # Знак из трёх запятых.
        for a in (90, 210, 330):
            ax, ay = 32 + 5 * math.cos(math.radians(a)), 25 + 5 * math.sin(math.radians(a))
            c.ellipse(ax, ay, 3, 3, RED)
            bx, by = 32 + 7 * math.cos(math.radians(a + 55)), 25 + 7 * math.sin(math.radians(a + 55))
            c.line(ax, ay, bx, by, RED, 2)
    return c.finish()


def key():
    """Ключ основы: головка-монета с квадратным отверстием, красная кисть."""
    return ninja16.key()


def medkit():
    """Аптечка основы: ящичек лекаря с красным крестом на ярлыке."""
    return ninja16.medkit()


def hand(frame):
    """Кунай в руке снизу по центру, 128×96: синий рукав, белая обмотка запястья с красным
    шнуром, тыльная накладка, голые пальцы на рукояти, клинок листом вглубь (ось x=64, остриё у
    верхнего края); кадр 1 бросок: ладонь раскрыта, кунай уходит вверх по оси со следом."""
    c = Canvas(128, 96)
    # Рукав: расширяется книзу, складки.
    for y in range(66, 96):
        w = 17 + (y - 66) // 4
        for x in range(64 - w, 64 + w):
            c.set(x, y, SEA)
    for x0, x1 in ((52, 46), (60, 58), (70, 73), (77, 84)):
        c.line(x0, 70, x1, 95, NAVY, 1)
    c.line(66, 78, 67, 95, NAVY, 1)
    # Обмотка запястья: белая лента витками, красный шнур с узлом.
    c.rect(48, 57, 80, 67, WHITE)
    for y in range(57, 68):
        for x in range(48, 81):
            if (x + y) % 6 == 0:
                c.set(x, y, GREY)
    c.rect(48, 66, 80, 67, RED)
    c.rect(62, 64, 66, 69, RED)
    c.rect(63, 65, 65, 66, TAN)
    # Кисть шнура свисает справа.
    c.line(79, 66, 87, 71, RED, 3)
    c.line(87, 71, 86, 80, RED, 3)
    c.rect(84, 80, 88, 88, RED)
    c.rect(84, 82, 88, 82, WHITE)
    c.rect(86, 84, 86, 88, TAN)
    if frame == 0:
        # Кунай: клинок листом, грань посередине, рукоять в обмотке.
        c.poly([(64, 1), (73, 20), (67, 29), (61, 29), (55, 20)], GREY)
        c.poly([(64, 4), (64, 28), (61, 28), (57, 20)], WHITE)
        c.line(64, 3, 64, 28, METAL, 1)
        c.line(70, 17, 66, 27, METAL, 1)
        c.rect(61, 29, 67, 44, DARK)
        for y in range(30, 44, 3):
            c.rect(61, y, 67, y, GREY)
            c.set(64, y + 1, METAL)
        c.rect(60, 29, 68, 29, K)
    # Тыльная сторона: синяя накладка с прошивкой и золотой клёпкой.
    c.ellipse(64, 54, 15, 9, SEA)
    c.rect(51, 47, 77, 58, SEA)
    c.poly([(57, 49), (71, 49), (64, 58)], NAVY)
    c.rect(63, 51, 65, 53, GOLD)
    c.rect(51, 47, 77, 47, NAVY)
    # Большой палец слева.
    if frame == 0:
        c.ellipse(49, 49, 3.2, 6, SKIN)
        c.rect(48, 44, 50, 45, WHITE)
        tops = (40, 39, 39, 40)
        low = 46
    else:
        c.line(50, 52, 45, 46, SKIN, 7)
        tops = (31, 27, 28, 33)
        low = 46
    # Пальцы: четыре, швы между ними, ногти и костяшки.
    for k in range(4):
        x0 = 51 + k * 7
        c.rect(x0, tops[k], x0 + 5, low, SKIN)
        c.rect(x0 + 1, tops[k] - 1, x0 + 4, tops[k] - 1, SKIN)
        c.rect(x0 + 1, tops[k], x0 + 4, tops[k] + 1, WHITE if frame else SKIN)
        c.rect(x0, low - 1, x0 + 5, low, TAN)
        if frame:
            c.rect(x0 + 1, (tops[k] + low) // 2, x0 + 4, (tops[k] + low) // 2, TAN)
        else:
            c.rect(x0 + 1, tops[k] + 3, x0 + 4, tops[k] + 3, TAN)
        if k:
            c.rect(x0 - 1, tops[k] + 1, x0 - 1, low, TAN)
    if frame:
        # Кунай ушёл вперёд: маленький, у верхнего края.
        c.poly([(64, 0), (68, 9), (65, 14), (63, 14), (60, 9)], GREY)
        c.rect(63, 2, 63, 13, WHITE)
        c.rect(62, 7, 62, 11, WHITE)
        c.rect(63, 14, 65, 19, DARK)
        c.rect(62, 20, 66, 23, GOLD)
        c.rect(63, 21, 65, 22, None)
    c.finish()
    if frame:
        for x, y0, y1, col in ((57, 12, 25, WHITE), (71, 12, 25, WHITE), (53, 18, 26, SKY), (75, 18, 26, SKY),
                               (64, 26, 30, SKY)):
            c.rect(x, y0, x, y1, col)
    return c


def face(mode):
    """Лицо ниндзя для HUD, 32×32: синий капюшон, прорезь глаз, красный шарф на подбородке с
    узлом сбоку; 0 прямо, 1 глянул влево, 2 вправо, 3 больно (зажмурился, шарф сполз, рот открыт,
    ссадина), 4 ухмылка (шарф спущен, глаза дугой)."""
    c = Canvas(32, 32)
    low = mode in (3, 4)
    # Концы шарфа за головой справа.
    c.line(25, 24, 30, 21, RED, 3)
    c.line(25, 26, 30, 28, RED, 3)
    c.ellipse(15.5, 15, 12.5, 13, SEA)
    # Складки капюшона.
    c.line(6, 9, 10, 4, NAVY, 1)
    c.line(21, 4, 25, 9, NAVY, 1)
    c.line(15, 3, 16, 7, NAVY, 1)
    # Прорезь: лоб, глаза, переносица; с опущенным шарфом видно и рот.
    c.ellipse(15.5, 15, 9.5, 4.5 if not low else 5, SKIN)
    if low:
        c.ellipse(15.5, 20, 7.5, 5, SKIN)
    c.rect(6, 10, 25, 10, NAVY)
    # Шарф.
    sy = 27 if low else 24
    c.ellipse(15.5, sy + 1, 11, 4.5, RED)
    c.line(6, sy, 25, sy - 1, TAN, 1)
    c.line(8, sy + 3, 22, sy + 2, TAN, 1)
    c.rect(23, sy - 1, 26, sy + 2, RED)
    c.finish()
    look = {0: 0, 1: -2, 2: 2, 3: 0, 4: 0}[mode]
    for e in (-5, 4):
        x = 15.5 + e + 0.5
        if mode == 3:
            sign = 1 if e < 0 else -1
            c.line(x - 2 * sign, 13, x + 1 * sign, 15, K, 1)
            c.line(x + 1 * sign, 15, x - 2 * sign, 17, K, 1)
        elif mode == 4:
            c.line(x - 2, 15, x, 13, K, 1)
            c.line(x, 13, x + 2, 15, K, 1)
        else:
            c.rect(x - 2, 13, x + 2, 16, WHITE)
            c.rect(x + look - 1, 14, x + look, 16, K)
            sign = 1 if e < 0 else -1
            c.line(x - 2 * sign, 11, x + 2 * sign, 12, K, 1)
    c.rect(15, 15, 16, 18, TAN)
    if mode == 4:
        c.rect(11, 20, 20, 22, WHITE)
        c.rect(11, 20, 20, 20, K)
        c.set(10, 19, K)
        c.set(21, 19, K)
        c.set(13, 21, GREY)
        c.set(16, 21, GREY)
        c.set(19, 21, GREY)
    elif mode == 3:
        c.ellipse(15.5, 21.5, 3, 2, K)
        c.rect(14, 22, 17, 22, RED)
        # Ссадина на скуле и капля пота.
        c.line(21, 17, 23, 19, RED, 1)
        c.set(5, 13, WHITE)
        c.set(5, 14, WHITE)
        c.set(4, 14, WHITE)
    return c


def textures():
    return {"wall_planks": tex_plaster(), "wall_stone": tex_stone(), "wall_pillar": tex_pillar(),
            "wall_exit": tex_exit(), "wall_cabin": tex_cabin(), "wall_hull": tex_hull(), "wall_cargo": tex_cargo(),
            "floor_planks": tex_floor(), "floor_stone": tex_floor_stone(), "floor_carpet": tex_floor_tatami(),
            "ceiling_beams": tex_ceiling()}


def sprites():
    out = {"shot": shot(), "bullet": bullet(), "key": key(), "medkit": medkit(),
           "hold_decor": strip([decor(k) for k in range(6)]),
           "pistol": strip([hand(0), hand(1)]),
           "face": strip([face(i) for i in range(5)])}
    out.update(clan_strips())
    out.update(textures())
    return out


# Имена зеркала (`space_hold16.py`), чтобы код, который берёт функции по имени, нашёл их и здесь.
tex_panels = tex_plaster
tex_growth = tex_stone
tex_floor_grate = tex_floor_stone
tex_floor_tiles = tex_floor_tatami
alien = clansman
alien_strips = clan_strips
pistol = hand


if __name__ == "__main__":
    if "--preview" in sys.argv:
        ninja16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], ninja16.shaded(sprites()))
