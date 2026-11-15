#!/usr/bin/env python3
"""Набор «Космос» для шутера × 16/32-bit «до выхода» (#136), зеркало `pixel_hold16.py`: те же
ключи, размеры холстов, число и порядок кадров и точки опоры (ноги врагов на 61-62 строке по
центру кадра, ствол пистолета вверх по оси 64, текстуры 64×64 со швом по краю).

Тема: коридоры станции, захваченной пришельцами. Стены: панели, заросший отсек, колонна с
трубами, шлюз-выход, командная каюта с экраном, иллюминатор, грузовой отсек. Полы: настил,
решётка, плитка каюты. Враги: пришелец-пехотинец с бластером (`skel_*`) и пришелец с жезлом
(`cut_*`). Лучевой пистолет в белой перчатке, плазма, ключ-карта, аптечка, лицо космонавта.

    python3 tools/space_hold16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import space16  # noqa: E402
from space16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                     DARK, RED, VIOLET, PLUM)

T = 64


# --- Текстуры ----------------------------------------------------------------------------------

def tex_panels():
    """Основная стена: светлые панели 32×32 с тёмными швами, заклёпки, полоса кабеля, снизу
    плинтус темнее."""
    rng = random.Random(201)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 32, y % 32
            col = GREY
            if px in (0, 31) or py in (0, 31):
                col = DARK
            elif px == 1 or py == 1:
                col = WHITE
            elif px == 30 or py == 30:
                col = METAL
            c.set(x, y, col)
    for by in (0, 32):
        for bx in (0, 32):
            for dx, dy in ((4, 4), (27, 4), (4, 27), (27, 27)):
                c.set(bx + dx, by + dy, DARK)
            # Вентиляционная решётка на каждой второй панели.
            if (bx + by) % 64 == 0:
                for k in range(4):
                    c.rect(bx + 9, by + 10 + k * 3, bx + 22, by + 10 + k * 3, METAL)
    for _ in range(18):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == GREY:
            c.set(x, y, METAL)
    # Кабель-канал с бирюзовой жилой.
    c.rect(0, 44, T - 1, 47, METAL)
    c.rect(0, 45, T - 1, 45, AQUA)
    c.rect(0, 47, T - 1, 47, DARK)
    for x in range(6, T, 16):
        c.rect(x, 44, x + 1, 47, DARK)
    c.rect(0, 58, T - 1, T - 1, METAL)
    c.rect(0, 58, T - 1, 58, DARK)
    for x in range(T):
        if x % 4 == 0:
            c.set(x, 61, DARK)
    return c


def tex_growth():
    """Заросший отсек: тёмный металл, оплетённый фиолетовой биомассой, светящиеся споры."""
    rng = random.Random(202)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = DARK
            if x % 32 == 0 or y % 32 == 0:
                col = K
            elif (x * 5 + y * 3) % 13 == 0:
                col = METAL
            c.set(x, y, col)
    # Жилы: синусоиды, замкнутые по горизонтали (период делит 64).
    for i in range(5):
        y0 = 6 + i * 12 + rng.randint(-2, 2)
        amp = rng.randint(3, 6)
        ph = rng.random() * math.tau
        for x in range(T):
            y = y0 + amp * math.sin(x * math.tau / 32.0 + ph) + 2 * math.sin(x * math.tau / 64.0 * 3 + ph)
            for t in range(3):
                c.set(x, (int(round(y)) + t) % T, PLUM if t == 2 else VIOLET)
    # Наросты и споры.
    for _ in range(9):
        x, y = rng.randrange(4, T - 4), rng.randrange(4, T - 4)
        r = rng.randint(2, 4)
        c.ellipse(x, y, r, r, PLUM)
        c.ellipse(x - 0.5, y - 0.5, r - 1, r - 1, VIOLET)
        c.set(x - 1, y - 1, SKY if r > 2 else AQUA)
    return c


def tex_pillar():
    """Колонна: вертикальные трубы с бликом, обручи с заклёпками, световая полоса."""
    c = Canvas(T, T)
    for x in range(T):
        px = x % 16
        col = METAL if px not in (0, 15) else DARK
        if px == 2:
            col = GREY
        if px == 3:
            col = WHITE
        if px in (12, 13):
            col = DARK
        c.rect(x, 0, x, T - 1, col)
    for x in (7, 39):
        c.rect(x, 0, x + 1, T - 1, AQUA)
    for y in (10, 48):
        c.rect(0, y, T - 1, y + 4, GREY)
        c.rect(0, y, T - 1, y, WHITE)
        c.rect(0, y + 4, T - 1, y + 4, K)
        for x in range(4, T, 10):
            c.set(x, y + 2, DARK)
    return c


def tex_exit():
    """Шлюз-выход: тёмные створки со швом посередине, рама в жёлто-чёрную полосу, стрелка вверх и
    бирюзовое табло над створками."""
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, DARK)
    # Створки.
    for y in range(12, 60):
        for x in range(6, 58):
            col = METAL
            if (y - 12) % 12 == 0:
                col = DARK
            elif (y - 12) % 12 == 1:
                col = GREY
            c.set(x, y, col)
    c.rect(31, 12, 32, 59, K)
    c.rect(30, 12, 30, 59, GREY)
    # Рама в предупреждающую полосу.
    for y in range(T):
        for x in range(T):
            frame = x < 6 or x > 57 or y > 59 or y < 3
            if frame:
                c.set(x, y, GOLD if ((x + y) // 4) % 2 == 0 else K)
    # Табло.
    c.rect(14, 3, 49, 11, K)
    c.rect(16, 5, 47, 9, AQUA)
    for x in (20, 26, 32, 38, 44):
        c.rect(x, 6, x + 1, 8, SKY)
    # Стрелки на створках.
    for cx in (18, 45):
        c.poly([(cx - 6, 40), (cx + 6, 40), (cx, 28)], AQUA)
        c.rect(cx - 2, 40, cx + 2, 50, AQUA)
        c.set(cx, 30, SKY)
    # Замок.
    c.rect(27, 32, 36, 41, DARK)
    c.rect(29, 34, 34, 39, RED)
    c.rect(29, 34, 34, 34, GOLD)
    return c


def tex_cabin():
    """Командная каюта: белые панели, оранжевая полоса, экран со звёздной картой."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px = x % 16
            col = WHITE if px not in (0, 15) else GREY
            if px == 14:
                col = GREY
            c.set(x, y, col)
    c.rect(0, 30, T - 1, 33, RED)
    c.rect(0, 33, T - 1, 33, DARK)
    c.rect(0, 29, T - 1, 29, GOLD)
    # Экран.
    c.rect(16, 5, 47, 25, DARK)
    c.rect(18, 7, 45, 23, NAVY)
    c.ellipse(28, 15, 5, 5, SEA)
    c.ellipse(27, 14, 2, 2, AQUA)
    c.line(20, 20, 43, 10, VIOLET, 1)
    for x, y in ((21, 9), (38, 19), (42, 13), (34, 9), (24, 21)):
        c.set(x, y, SKY)
    c.rect(40, 20, 43, 21, RED)
    # Пульт под полосой.
    for x in range(4, T, 8):
        c.rect(x, 38, x + 3, 40, METAL)
        c.set(x + 1, 39, AQUA if (x // 8) % 2 else GOLD)
    c.rect(0, 56, T - 1, T - 1, GREY)
    c.rect(0, 56, T - 1, 56, METAL)
    return c


def tex_hull():
    """Борт: панели и круглый иллюминатор со звёздами и краем планеты."""
    c = tex_panels()
    c.ellipse(32, 26, 16, 16, DARK)
    c.ellipse(32, 26, 14, 14, METAL)
    c.ellipse(32, 26, 12, 12, GREY)
    c.ellipse(32, 26, 10, 10, NAVY)
    # Край планеты снизу справа, только внутри стекла.
    for y in range(16, 37):
        for x in range(22, 43):
            if c.get(x, y) == NAVY and (x - 44) ** 2 + (y - 40) ** 2 <= 13 ** 2:
                c.set(x, y, VIOLET if (x - 44) ** 2 + (y - 40) ** 2 <= 11 ** 2 else SEA)
    for x, y in ((26, 20), (30, 24), (36, 19), (27, 29), (33, 30), (38, 23)):
        if c.get(x, y) == NAVY:
            c.set(x, y, SKY)
    c.line(25, 21, 28, 18, AQUA, 1)
    for a in range(0, 360, 45):
        c.set(32 + 13 * math.cos(math.radians(a)), 26 + 13 * math.sin(math.radians(a)), K)
    return c


def tex_cargo():
    """Грузовой отсек: штабель контейнеров 32×32 со сдвигом ряда, рёбра жёсткости, маркировка."""
    c = Canvas(T, T)
    for by in (0, 32):
        for bx in (0, 32):
            off = 16 if by == 32 else 0
            x0 = (bx + off) % T
            body = (METAL, GREY)[(bx // 32 + by // 32) % 2]
            for y in range(by, by + 32):
                for x in range(32):
                    xx = (x0 + x) % T
                    edge = x in (0, 31) or y in (by, by + 31)
                    rib = x % 6 == 3 and 4 <= y - by <= 27
                    col = DARK if edge else (DARK if rib else body)
                    if not edge and not rib and y - by == 1:
                        col = WHITE
                    c.set(xx, y, col)
            # Маркировка: оранжевая табличка и бирюзовый индикатор.
            for x in range(10, 22):
                for y in range(by + 12, by + 19):
                    c.set((x0 + x) % T, y, RED if y not in (by + 12, by + 18) else DARK)
            for x in range(12, 20, 3):
                c.set((x0 + x) % T, by + 15, WHITE)
            c.set((x0 + 26) % T, by + 5, AQUA)
            c.set((x0 + 27) % T, by + 5, AQUA)
    return c


def tex_floor():
    """Настил: стальные листы 32×32 с рифлением «ёлочкой» и тёмными швами."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 32, y % 32
            col = METAL
            if px == 0 or py == 0:
                col = K
            elif px == 1 or py == 1:
                col = GREY
            elif ((px + py) % 8 == 0 and (px // 8 + py // 8) % 2 == 0) or ((px - py) % 8 == 0 and (px // 8 + py // 8) % 2 == 1):
                col = DARK
            c.set(x, y, col)
    for bx in (0, 32):
        for by in (0, 32):
            for dx, dy in ((3, 3), (29, 3), (3, 29), (29, 29)):
                c.set(bx + dx, by + dy, GREY)
    return c


def tex_floor_grate():
    """Решётка: тёмный провал под прутьями, рамы 16×16."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 16, y % 16
            if px == 0 or py == 0:
                col = METAL
            elif px == 1 or py == 1:
                col = DARK
            elif px % 4 == 2:
                col = DARK
            else:
                col = K
            c.set(x, y, col)
    # Под решёткой кое-где светится кабель.
    for x in range(T):
        if c.get(x, 38) == K:
            c.set(x, 38, NAVY)
        if c.get(x, 10) == K and (x // 16) % 2 == 0:
            c.set(x, 10, SEA)
    return c


def tex_floor_tiles():
    """Плитка каюты: белая, в шахматном порядке ромбы бирюзы и оранжевая точка в углах."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 16, y % 16
            d = abs(px - 8) + abs(py - 8)
            col = WHITE
            if px == 0 or py == 0:
                col = METAL
            elif d == 5 and (x // 16 + y // 16) % 2 == 0:
                col = AQUA
            elif d < 2 and (x // 16 + y // 16) % 2 == 0:
                col = SEA
            elif (x + y) % 2 == 0 and d > 9:
                col = GREY
            c.set(x, y, col)
    for x in range(0, T, 16):
        for y in range(0, T, 16):
            c.set(x, y, RED)
    return c


def tex_ceiling():
    """Потолок: тёмные панели, через 32 пикселя балка с бликом, на балках редкие лампы-точки (без
    ярких полос, иначе в перспективе они расходятся лучами)."""
    rng = random.Random(206)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = DARK
            if x % 16 == 0:
                col = K
            if y % 32 < 6:
                col = METAL if y % 32 == 1 else DARK
                if y % 32 == 5:
                    col = K
            c.set(x, y, col)
    for _ in range(26):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == DARK:
            c.set(x, y, K)
    for y in (2, 34):
        for x in (8, 40):
            c.rect(x, y, x + 1, y + 1, AQUA)
    return c


# --- Пришельцы ---------------------------------------------------------------------------------

def _crest(c, cx, top, side, back):
    """Гребень рубаки: тёмный плавник по макушке."""
    if side:
        c.poly([(cx - 9, top + 6), (cx + 2, top - 2), (cx + 4, top + 4)], PLUM)
    else:
        c.poly([(cx - 2, top + 6), (cx, top - 3), (cx + 2, top + 6)], PLUM)
        c.rect(cx - 1, top + 6, cx + 1, top + 10, PLUM)
    if back:
        c.rect(cx - 1, top + 6, cx + 1, top + 16, PLUM)


def _antennae(c, cx, top, side, back):
    """Усики пехотинца с бирюзовыми шариками."""
    for sign in ((1,) if side else (-1, 1)):
        x1 = cx + sign * (5 if not side else 3)
        c.line(cx + sign * 3, top + 5, x1, top - 1, PLUM, 1)
        c.ellipse(x1, top - 2, 1.4, 1.4, AQUA)


def alien(angle, phase, mode="walk", rod=False):
    """Пришелец 64×64 в ракурсе `angle` (0 спереди … 4 со спины, лицом вправо на 1-3), шаг `phase`
    0/1. `mode`: walk, aim, fire, slash, die0..die2, hurt. `rod` рубака: гребень вместо усиков,
    жезл вместо бластера. Ступни на 61-62 строке, ось по центру кадра, как у скелета пиратов."""
    c = Canvas(T, T)
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    if mode.startswith("die"):
        k = int(mode[-1])
        if k == 0:
            return alien(0, 0, "hurt", rod)
        base = 62
        # Оседает и растекается лужей слизи, голова сверху с потухшими глазами.
        w = 14 if k == 1 else 22
        h = 9 if k == 1 else 4
        c.ellipse(cx, base - h + 1, w, h, PLUM)
        c.ellipse(cx - 2, base - h, w - 3, max(h - 2, 1.5), VIOLET)
        head_y = base - (17 if k == 1 else 8)
        hx = cx + (2 if k == 1 else 7)
        c.ellipse(hx, head_y, 9, 7 if k == 1 else 5, VIOLET)
        for e in (-4, 4):
            c.line(hx + e - 2, head_y, hx + e + 2, head_y, K, 1)
        for x in (cx - 16, cx + 12) if k == 2 else ():
            c.ellipse(x, base - 1, 3, 1.5, VIOLET)
        # Выпавшее оружие.
        if rod:
            c.line(cx - 18, base - 1, cx + 2, base - 3, METAL, 2)
            c.ellipse(cx - 19, base - 2, 2, 2, AQUA)
        else:
            c.rect(cx + 12, base - 4, cx + 22, base - 2, METAL)
        return c.finish()
    bob = 1 if phase else 0
    # Ноги: тонкие, с суставом назад, широкая трёхпалая ступня.
    for sign in (-1, 1):
        swing = (sign * 3 if phase else -sign * 3) if mode == "walk" else 0
        hip = (cx + sign * (2 if side else 4), 41 - bob)
        foot = (cx + sign * (2 if side else 5) + swing * (1 if side else 0.3), 61)
        knee = ((hip[0] + foot[0]) / 2 + (-2 if side else sign * 1.5), 51)
        c.line(hip[0], hip[1], knee[0], knee[1], PLUM if sign < 0 else VIOLET, 5)
        c.line(knee[0], knee[1], foot[0], foot[1], PLUM if sign < 0 else VIOLET, 4)
        c.rect(foot[0] - 3, 61, foot[0] + 4, 62, DARK)
    # Корпус: узкий, в тёмной броне с пластиной на груди.
    w = 5 if side else (7 if diag else 8)
    c.poly([(cx - w, 24 - bob), (cx + w, 24 - bob), (cx + w - 2, 42 - bob), (cx - w + 2, 42 - bob)], DARK)
    c.rect(cx - w, 23 - bob, cx + w, 25 - bob, METAL)
    if back:
        # Ранец-баллон на спине.
        c.rect(cx - 3, 27 - bob, cx + 3, 37 - bob, METAL)
        c.rect(cx - 1, 29 - bob, cx + 1, 31 - bob, AQUA)
    else:
        c.rect(cx - w + 2, 28 - bob, cx + w - 2, 33 - bob, METAL)
        c.rect(cx - 1 + (2 if side or diag else 0), 30 - bob, cx + 1 + (2 if side or diag else 0), 31 - bob, AQUA)
    c.rect(cx - w + 1, 40 - bob, cx + w - 1, 41 - bob, RED)
    # Руки и оружие.
    if rod:
        up = mode == "slash"
        hx_ = cx + (10 if side or diag else 9)
        hy_ = (30 if not up else 16) - bob
        c.line(cx + 6, 26 - bob, hx_, hy_, VIOLET, 4)
        tip = (hx_ + (14 if side or diag else 6), (16 if not up else 2) - bob)
        tail = (hx_ - (6 if side or diag else 3), hy_ + 8)
        c.line(tail[0], tail[1], tip[0], tip[1], METAL, 3)
        c.ellipse(tip[0], tip[1], 3, 3, AQUA)
        c.ellipse(tip[0] - 0.5, tip[1] - 0.5, 1.3, 1.3, SKY)
        c.line(cx - 7, 26 - bob, cx - 10, 35 - bob, PLUM, 4)
    elif mode in ("aim", "fire") or not back:
        if side or diag:
            c.line(cx + 2, 26 - bob, cx + 12, 29 - bob, VIOLET, 4)
            c.rect(cx + 6, 24 - bob, cx + 22, 28 - bob, METAL)
            c.rect(cx + 10, 28 - bob, cx + 13, 32 - bob, DARK)
            c.rect(cx + 22, 25 - bob, cx + 27, 27 - bob, DARK)
            c.rect(cx + 27, 24 - bob, cx + 29, 28 - bob, AQUA)
        else:
            c.line(cx - 9, 26 - bob, cx - 5, 33 - bob, PLUM, 4)
            c.line(cx + 9, 26 - bob, cx + 4, 33 - bob, VIOLET, 4)
            if mode in ("aim", "fire"):
                # Бластер смотрит в камеру: кольцо ствола.
                c.ellipse(cx, 32 - bob, 4, 4, METAL)
                c.ellipse(cx, 32 - bob, 2.2, 2.2, K)
                c.ellipse(cx, 32 - bob, 1, 1, AQUA)
            else:
                c.line(cx - 10, 37 - bob, cx + 10, 25 - bob, METAL, 3)
                c.rect(cx + 9, 23 - bob, cx + 12, 26 - bob, AQUA)
    else:
        c.line(cx - 9, 26 - bob, cx - 10, 36 - bob, VIOLET, 4)
        c.line(cx + 9, 26 - bob, cx + 10, 36 - bob, VIOLET, 4)
        c.line(cx - 10, 18 - bob, cx + 10, 37 - bob, METAL, 3)
    # Голова: большая, вытянутая назад, огромные чёрные глаза.
    hx = cx + (2 if side else (1 if diag else 0))
    c.rect(hx - 2, 19 - bob, hx + 2, 24 - bob, PLUM)
    c.ellipse(hx - (2 if side else 0), 12 - bob, 10 if not side else 9, 8, VIOLET)
    c.ellipse(hx, 17 - bob, 5, 4, VIOLET)
    if not back:
        if side:
            c.ellipse(hx + 4, 13 - bob, 2.6, 3.4, K)
            c.set(hx + 5, 12 - bob, SKY)
            c.rect(hx + 3, 19 - bob, hx + 5, 19 - bob, K)
        else:
            for e in (-4, 4):
                ex = hx + e + (1.5 if diag else 0)
                c.ellipse(ex, 13 - bob, 2.8, 3.6, K)
                c.set(ex - 1, 11 - bob, SKY if mode != "fire" else RED)
            c.rect(hx - 1, 19 - bob, hx + 1, 19 - bob, K)
    else:
        # Затылок: складки.
        c.line(hx - 5, 9 - bob, hx + 5, 9 - bob, PLUM, 1)
        c.line(hx - 4, 13 - bob, hx + 4, 13 - bob, PLUM, 1)
    if rod:
        _crest(c, hx, 4 - bob, side, back)
    else:
        _antennae(c, hx, 4 - bob, side, back)
    c.finish()
    if mode == "fire":
        fx, fy = (cx + 30, 26 - bob) if side or diag else (cx, 32 - bob)
        c.ellipse(fx, fy, 5, 4, AQUA)
        c.ellipse(fx, fy, 2.5, 2, WHITE)
    if mode == "hurt":
        for x in range(T):
            for y in range(T):
                if c.get(x, y) in (VIOLET, PLUM) and (x + y) % 3 == 0:
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
    """Выстрел пришельца: фиолетовый сгусток с оранжевой кромкой, чтобы не путать с плазмой героя."""
    c = Canvas(16, 16)
    c.ellipse(8, 8, 6, 6, RED)
    c.ellipse(8, 8, 4.5, 4.5, VIOLET)
    c.ellipse(7, 7, 2, 2, WHITE)
    return c


def bullet():
    """Плазма героя: бирюзовый шарик с белым ядром и хвостом."""
    c = Canvas(16, 16)
    c.ellipse(8, 8, 3.5, 3.5, AQUA)
    c.ellipse(8, 11, 2, 2, SEA)
    c.finish()
    c.ellipse(7.5, 7.5, 1.5, 1.5, WHITE)
    return c


def decor(kind):
    """Ориентир зала 64×64, низ на 62-63 строке: 0 топливные баллоны, 1 контейнеры, 2 световая
    мачта, 3 лазерная турель, 4 грузовая капсула, 5 антенна-тарелка."""
    c = Canvas(T, T)
    if kind == 0:
        for bx, by in ((18, 62), (44, 62), (31, 40)):
            c.rect(bx - 9, by - 20, bx + 9, by - 2, RED)
            c.ellipse(bx, by - 20, 9, 4, RED)
            c.ellipse(bx, by - 2, 9, 3, RED)
            c.rect(bx - 9, by - 14, bx + 9, by - 11, GOLD)
            c.rect(bx - 2, by - 26, bx + 2, by - 23, METAL)
            c.rect(bx - 6, by - 8, bx - 4, by - 5, WHITE)
    elif kind == 1:
        for x0, y0, w, col in ((6, 38, 26, METAL), (34, 40, 24, GREY), (16, 14, 26, GREY)):
            c.rect(x0, y0, x0 + w, y0 + 22, col)
            for x in range(x0 + 4, x0 + w, 6):
                c.rect(x, y0 + 3, x, y0 + 19, DARK)
            c.rect(x0, y0, x0 + w, y0 + 1, WHITE)
            c.rect(x0 + 8, y0 + 8, x0 + 16, y0 + 13, RED)
            c.set(x0 + w - 3, y0 + 4, AQUA)
    elif kind == 2:
        c.rect(30, 22, 33, 63, METAL)
        c.rect(26, 58, 37, 63, DARK)
        c.rect(24, 6, 39, 22, DARK)
        c.rect(26, 8, 37, 20, AQUA)
        c.ellipse(31.5, 14, 3, 4, SKY)
        c.rect(22, 4, 41, 6, METAL)
        c.rect(30, 0, 33, 4, METAL)
    elif kind == 3:
        # Турель: тренога, поворотный блок, ствол с линзой.
        c.line(32, 44, 14, 62, METAL, 3)
        c.line(32, 44, 50, 62, METAL, 3)
        c.rect(30, 44, 34, 62, DARK)
        c.ellipse(30, 36, 13, 10, GREY)
        c.rect(22, 30, 38, 33, WHITE)
        c.poly([(38, 30), (58, 28), (58, 36), (38, 40)], METAL)
        c.ellipse(58, 32, 3, 5, AQUA)
        c.ellipse(26, 36, 3, 3, RED)
    elif kind == 4:
        # Капсула: цилиндр на боку с окном и опорами.
        c.rect(14, 56, 18, 62, DARK)
        c.rect(46, 56, 50, 62, DARK)
        c.rect(14, 32, 50, 56, WHITE)
        c.ellipse(14, 44, 8, 12, GREY)
        c.ellipse(50, 44, 8, 12, WHITE)
        c.rect(22, 32, 24, 56, METAL)
        c.rect(40, 32, 42, 56, METAL)
        c.ellipse(32, 43, 5, 5, DARK)
        c.ellipse(32, 43, 3.5, 3.5, AQUA)
        c.rect(26, 52, 38, 53, RED)
    else:
        # Антенна: мачта, тарелка, облучатель.
        c.rect(30, 30, 33, 63, METAL)
        c.rect(24, 58, 39, 63, DARK)
        c.ellipse(31.5, 22, 20, 14, GREY)
        c.ellipse(31.5, 20, 16, 10, WHITE)
        c.ellipse(31.5, 19, 10, 6, GREY)
        c.line(31.5, 20, 44, 4, METAL, 2)
        c.ellipse(44, 4, 2.5, 2.5, RED)
    return c.finish()


def key():
    """Ключ-карта: золотая карта с чипом, полосой и вырезом."""
    c = Canvas(32, 32)
    c.poly([(4, 9), (24, 9), (28, 13), (28, 23), (4, 23)], GOLD)
    c.rect(4, 9, 24, 10, WHITE)
    c.rect(7, 13, 13, 18, METAL)
    c.rect(9, 14, 11, 17, DARK)
    c.rect(4, 20, 28, 21, RED)
    c.rect(17, 13, 25, 14, BRASS)
    c.rect(17, 16, 22, 17, BRASS)
    return c.finish()


def medkit():
    """Аптечка: белый контейнер с ручкой и оранжево-красным крестом."""
    c = Canvas(32, 32)
    c.rect(4, 12, 27, 29, WHITE)
    c.rect(4, 10, 27, 13, GREY)
    c.rect(12, 6, 19, 10, METAL)
    c.rect(14, 8, 17, 10, None)
    c.rect(13, 15, 18, 27, RED)
    c.rect(9, 18, 22, 23, RED)
    c.rect(24, 15, 25, 16, AQUA)
    return c.finish()


def pistol(frame):
    """Лучевой пистолет в руке снизу по центру, 128×96: рукав скафандра с кольцом манжеты, белая
    перчатка, пистолет стволом вглубь (ось x=64, излучатель у верхнего края); кадр 1 со вспышкой."""
    c = Canvas(128, 96)
    # Рукав: белый, слегка расширяется книзу, тёмные кольца сочленений.
    for y in range(62, 96):
        w = 17 + (y - 62) // 4
        for x in range(64 - w, 64 + w):
            ring = (y - 62) % 10 in (8, 9)
            c.set(x, y, METAL if ring and (y - 62) % 10 == 9 else (GREY if ring else WHITE))
    # Перчатка: ладонь и четыре пальца, швы между пальцами, костяшки.
    c.ellipse(64, 55, 15, 10, WHITE)
    c.rect(51, 48, 77, 58, WHITE)
    for k in range(4):
        x0 = 51 + k * 7
        c.rect(x0, 42, x0 + 5, 50, WHITE)
        c.rect(x0, 42, x0 + 5, 42, GREY)
        c.rect(x0 + 1, 50, x0 + 4, 51, GREY)
        if k:
            c.rect(x0 - 1, 43, x0 - 1, 54, METAL)
    c.rect(51, 56, 77, 57, GREY)
    # Манжета: металлическое кольцо с бирюзовой жилой.
    c.rect(46, 60, 82, 65, METAL)
    c.rect(46, 60, 82, 60, GREY)
    c.rect(46, 63, 82, 63, AQUA)
    c.rect(46, 65, 82, 65, DARK)
    # Корпус пистолета: рукоять, кожух, ствол с рёбрами, излучатель.
    c.poly([(57, 42), (71, 42), (71, 26), (57, 26)], DARK)
    c.poly([(54, 30), (74, 30), (72, 16), (56, 16)], METAL)
    c.rect(57, 18, 59, 28, GREY)
    c.rect(61, 6, 67, 16, GREY)
    for y in (8, 11, 14):
        c.rect(59, y, 69, y, DARK)
    c.rect(62, 6, 63, 16, WHITE)
    c.ellipse(64, 4, 5, 3.5, AQUA)
    c.ellipse(63, 3, 2, 1.2, SKY)
    # Плавник-радиатор и индикатор заряда.
    c.poly([(74, 22), (80, 26), (74, 30)], RED)
    c.rect(66, 20, 70, 26, AQUA)
    c.rect(66, 20, 70, 21, SKY)
    c.finish()
    if frame:
        c.ellipse(64, 0, 18, 10, AQUA)
        c.ellipse(64, 0, 10, 6, WHITE)
    return c


def face(mode):
    """Лицо космонавта для HUD, 32×32: шлем с открытым стеклом, 0 прямо, 1 глянул влево, 2 вправо,
    3 больно (трещина на стекле), 4 ухмылка."""
    c = Canvas(32, 32)
    c.ellipse(16, 16, 14, 14, WHITE)
    c.rect(8, 27, 24, 30, METAL)
    c.ellipse(16, 16, 11, 10.5, DARK)
    c.ellipse(16, 17, 9.5, 9, SKIN)
    # Блик стекла сверху.
    c.line(9, 12, 13, 8, SKY, 1)
    c.line(11, 13, 13, 11, AQUA, 1)
    look = {0: 0, 1: -2, 2: 2, 3: 0, 4: 0}[mode]
    for e in (-4, 4):
        if mode == 3:
            c.line(16 + e - 2, 14, 16 + e + 2, 16, K, 1)
            c.line(16 + e - 2, 16, 16 + e + 2, 14, K, 1)
        else:
            c.rect(16 + e - 2, 13, 16 + e + 2, 16, WHITE)
            c.rect(16 + e + look - 1, 14, 16 + e + look, 16, K)
    c.rect(15, 17, 17, 20, TAN)
    if mode == 4:
        c.rect(11, 22, 21, 24, WHITE)
        c.rect(11, 22, 21, 22, K)
        c.set(10, 21, K)
        c.set(22, 21, K)
    elif mode == 3:
        c.ellipse(16, 23, 3.5, 2, K)
        # Трещина и красная лампа тревоги.
        c.line(21, 8, 24, 13, WHITE, 1)
        c.line(24, 13, 22, 16, WHITE, 1)
        c.rect(3, 15, 4, 18, RED)
    else:
        c.rect(12, 23, 20, 23, K)
    # Оранжевая нашивка на шлеме.
    c.rect(26, 14, 28, 18, RED)
    return c.finish()


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
        space16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], space16.shaded(sprites()))
