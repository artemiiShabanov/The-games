#!/usr/bin/env python3
"""Набор «Зомби» для шутера × 16/32-bit «до выхода» (#137), зеркало `space_hold16.py` и
`pixel_hold16.py`: те же ключи, размеры холстов, число и порядок кадров и точки опоры (ноги
врагов на 61-62 строке по центру кадра, ствол револьвера вверх по оси 64, текстуры 64×64 со
швом по краю).

Тема: подвалы и склеп под кладбищенской часовней, дорога к убежищу. Стены: кирпич подвала с
трубой, кладка склепа с нишей и черепом, каменная колонна в плюще, дверь убежища, сторожка в
обоях с портретом, заколоченное окно с луной, ячейки морга. Полы: бетон, грязь с костями,
линолеум в шашку. Враги: зомби-ходок в лохмотьях, плюётся (`skel_*`), и зомби-могильщик в
шляпе с лопатой (`cut_*`). Револьвер в руке выжившего, гвоздь, ключ и аптечка из основы,
лицо выжившего в бейсболке.

    python3 tools/zombies_hold16.py --preview out.png [--keys=a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zombies16  # noqa: E402
from zombies16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                       DARK, RED, VIOLET, PLUM)

T = 64


def _oval(c, cx, cy, rx, ry, ang, col):
    """Эллипс с поворотом на `ang` радиан: голова набок, штык лопаты."""
    ca, sa = math.cos(ang), math.sin(ang)
    r = int(max(rx, ry)) + 2
    for y in range(int(cy) - r, int(cy) + r + 1):
        for x in range(int(cx) - r, int(cx) + r + 1):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1.0:
                c.set(x, y, col)


# --- Текстуры ----------------------------------------------------------------------------------

def _bricks(c, y0=0, y1=T - 1, seed=301):
    """Кирпич 16×8 со сдвигом ряда на полкирпича: бурый, шов тёмный, сверху у кирпича светлая
    кромка, часть кирпичей выщерблена."""
    rng = random.Random(seed)
    tone = {}
    for y in range(y0, y1 + 1):
        row = y // 8
        for x in range(T):
            bx = ((x + (8 if row % 2 else 0)) % T) // 16
            px, py = (x + (8 if row % 2 else 0)) % 16, y % 8
            kind = tone.setdefault((row, bx), rng.random())
            col = METAL
            if px == 0 or py == 0:
                col = DARK
            elif py == 1 and kind > 0.35:
                col = TAN
            elif kind < 0.18:
                col = DARK if (x + y) % 2 else METAL
            elif py == 7 or px == 15:
                col = DARK if (x + y) % 3 == 0 else METAL
            c.set(x, y, col)
    for _ in range(14):
        x, y = rng.randrange(T), rng.randrange(y0, y1 + 1)
        if c.get(x, y) == METAL:
            c.set(x, y, DARK)


def tex_brick():
    """Основная стена: кирпич подвала, под потолком ржавая труба на хомутах с потёком, снизу
    бетонный цоколь."""
    c = Canvas(T, T)
    _bricks(c)
    # Труба: серая с бликом, хомуты через 32, стык с фланцем.
    c.rect(0, 9, T - 1, 14, GREY)
    c.rect(0, 10, T - 1, 10, WHITE)
    c.rect(0, 13, T - 1, 13, METAL)
    c.rect(0, 14, T - 1, 14, K)
    c.rect(0, 8, T - 1, 8, K)
    for x in (10, 42):
        c.rect(x, 7, x + 3, 15, DARK)
        c.rect(x + 1, 7, x + 1, 15, METAL)
    c.rect(26, 8, 29, 14, METAL)
    c.rect(26, 8, 26, 14, TAN)
    # Потёк ржавчины и зелёная слизь от стыка.
    for y in range(15, 34):
        c.set(27, y, BRASS if y % 3 else DARK)
        if y < 26:
            c.set(28, y, PLUM)
    c.set(27, 34, VIOLET)
    # Цоколь.
    c.rect(0, 55, T - 1, T - 1, GREY)
    c.rect(0, 55, T - 1, 55, WHITE)
    c.rect(0, 56, T - 1, 56, METAL)
    for x in range(T):
        if (x * 7) % 11 < 3:
            c.set(x, 59 + (x % 3), METAL)
        if x % 16 == 5:
            c.rect(x, 57, x, T - 1, METAL)
    c.rect(0, T - 1, T - 1, T - 1, DARK)
    return c


def tex_crypt():
    """Склеп: крупные серые блоки, сверху мох, посередине ниша с черепом и огарком."""
    rng = random.Random(302)
    c = Canvas(T, T)
    for y in range(T):
        row = y // 16
        for x in range(T):
            px, py = (x + (16 if row % 2 else 0)) % 32, y % 16
            col = GREY
            if px == 0 or py == 0:
                col = DARK
            elif px == 1 or py == 1:
                col = WHITE
            elif px == 31 or py == 15:
                col = METAL
            c.set(x, y, col)
    for _ in range(40):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == GREY:
            c.set(x, y, METAL)
    # Трещина через блоки.
    x = 52.0
    for y in range(18, 46):
        x += rng.choice((-1, 0, 0, 1))
        c.set(x, y, DARK)
    # Мох: бахрома сверху, длина по синусу с периодом, делящим 64.
    for x in range(T):
        d = int(4 + 3 * math.sin(x * math.tau / 32.0) + 2 * math.sin(x * math.tau / 64.0 * 5 + 1.0))
        for y in range(0, max(d, 1) + 1):
            c.set(x, y, PLUM if y >= d - 1 else VIOLET)
        if x % 9 == 4:
            for y in range(d, d + 6):
                c.set(x, y, PLUM)
    # Ниша: арка, в ней череп на полке и свеча.
    c.ellipse(24, 30, 10, 9, K)
    c.rect(14, 30, 34, 46, K)
    c.rect(12, 47, 36, 49, WHITE)
    c.rect(12, 49, 36, 49, METAL)
    c.rect(12, 50, 36, 50, DARK)
    c.ellipse(22, 37, 6, 5.5, WHITE)
    c.rect(19, 41, 25, 45, WHITE)
    c.rect(18, 36, 20, 38, K)
    c.rect(23, 36, 25, 38, K)
    c.set(22, 40, K)
    for xx in (20, 22, 24):
        c.set(xx, 44, K)
    c.rect(17, 34, 17, 40, GREY)
    c.rect(19, 46, 25, 46, GREY)
    c.rect(30, 40, 32, 46, WHITE)
    c.rect(32, 40, 32, 46, GREY)
    c.set(31, 39, K)
    c.ellipse(31, 36.5, 1.2, 2, GOLD)
    c.set(31, 37, WHITE)
    return c


def tex_pillar():
    """Колонна: каннелюры с бликом, два каменных пояса, по стволу вьётся плющ."""
    c = Canvas(T, T)
    for x in range(T):
        px = x % 16
        col = GREY
        if px in (0, 15):
            col = DARK
        elif px in (2, 3):
            col = WHITE
        elif px in (11, 12, 13, 14):
            col = METAL
        c.rect(x, 0, x, T - 1, col)
    for y in (6, 50):
        c.rect(0, y, T - 1, y + 6, GREY)
        c.rect(0, y, T - 1, y, WHITE)
        c.rect(0, y + 5, T - 1, y + 5, METAL)
        c.rect(0, y + 6, T - 1, y + 6, K)
        for x in range(3, T, 8):
            c.rect(x, y + 2, x + 3, y + 3, METAL)
            c.set(x, y + 2, DARK)
    # Плющ: две плети, замкнутые по горизонтали, с листьями.
    for i, ph in enumerate((0.0, 2.2)):
        for x in range(T):
            y = 30 + (i * 2 - 1) * 4 + 8 * math.sin(x * math.tau / 64.0 * (1 + i) + ph)
            c.set(x, y, PLUM)
            c.set(x, y + 1, PLUM)
            if x % 5 == i:
                up = -1 if (x // 5) % 2 else 1
                c.ellipse(x, y + up * 3, 2, 1.6, VIOLET)
                c.set(x, y + up * 2, PLUM)
    return c


def tex_exit():
    """Дверь убежища: бетонная рама, армейская зелёная сталь в две створки, слева белая
    стрелка вверх по трафарету, справа штурвал запора, над дверью горит табло, порог в
    жёлто-чёрную полосу."""
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, GREY)
    for y in range(T):
        for x in range(T):
            if (x * 5 + y * 3) % 17 == 0:
                c.set(x, y, METAL)
    c.rect(0, 0, 0, T - 1, DARK)
    c.rect(T - 1, 0, T - 1, T - 1, DARK)
    c.rect(1, 0, 1, T - 1, WHITE)
    # Проём и створки.
    c.rect(6, 12, 57, 59, K)
    for y in range(13, 60):
        for x in range(7, 57):
            col = VIOLET
            if (y - 13) % 16 == 15:
                col = PLUM
            elif (y - 13) % 16 == 0:
                col = SKY if x % 2 else VIOLET
            elif x in (7, 33):
                col = SKY
            elif x in (30, 56):
                col = PLUM
            c.set(x, y, col)
    c.rect(31, 13, 32, 59, K)
    for y in range(16, 58, 8):
        for x in (9, 28, 35, 54):
            c.set(x, y, PLUM)
            c.set(x, y - 1, SKY)
    # Табло: чёрная коробка, жёлтые буквы-штрихи, красная лампа.
    c.rect(14, 2, 49, 10, K)
    c.rect(16, 4, 43, 8, BRASS)
    for x0 in (17, 24, 31, 38):
        c.rect(x0, 4, x0 + 4, 8, GOLD)
        c.rect(x0 + 1, 5, x0 + 3, 5, K)
        c.rect(x0 + 1, 7, x0 + 3, 7, K)
    c.rect(45, 4, 47, 8, RED)
    c.set(45, 4, WHITE)
    # Стрелка вверх по трафарету на левой створке.
    c.poly([(11, 34), (27, 34), (19, 20)], WHITE)
    c.rect(16, 34, 22, 48, WHITE)
    c.rect(19, 20, 19, 48, VIOLET)
    c.rect(11, 51, 27, 52, WHITE)
    c.rect(18, 51, 20, 52, VIOLET)
    # Штурвал запора на правой.
    c.ellipse(44.5, 34, 9, 9, K)
    c.ellipse(44.5, 34, 8, 8, GREY)
    c.ellipse(44.5, 34, 5.5, 5.5, VIOLET)
    for a in range(0, 180, 45):
        dx, dy = math.cos(math.radians(a)) * 7, math.sin(math.radians(a)) * 7
        c.line(44.5 - dx, 34 - dy, 44.5 + dx, 34 + dy, GREY, 1)
    c.ellipse(44.5, 34, 2, 2, WHITE)
    c.set(45, 34, K)
    c.rect(38, 26, 41, 26, WHITE)
    # Кровавый отпечаток ладони у шва.
    c.ellipse(37, 50, 2.5, 3, RED)
    for d in (-2, 0, 2):
        c.rect(37 + d, 44, 37 + d, 47, RED)
    c.set(40, 49, RED)
    c.rect(37, 53, 37, 57, DARK)
    # Порог.
    for y in range(60, T):
        for x in range(T):
            c.set(x, y, GOLD if ((x + y) // 4) % 2 == 0 else K)
    return c


def tex_cabin():
    """Сторожка: выцветшие полосатые обои с потёками, деревянная панель снизу, портрет в
    золотой раме висит криво, следы когтей."""
    rng = random.Random(305)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px = x % 16
            col = WHITE if px < 8 else SKY
            if px in (0, 8):
                col = GREY
            elif px in (3, 4) and y % 8 in (2, 3):
                col = GOLD if y % 16 < 8 else AQUA
            elif px in (11, 12) and y % 8 in (6, 7):
                col = AQUA
            c.set(x, y, col)
    # Потёки сырости из-под потолка.
    for x in range(T):
        d = int(3 + 2 * math.sin(x * math.tau / 64.0 * 3) + (5 if x % 13 == 2 else 0))
        for y in range(d + 1):
            c.set(x, y, BRASS if y == d else METAL)
    # Панель: планки, рейка сверху.
    for y in range(40, T):
        for x in range(T):
            px = x % 8
            col = METAL
            if px == 0:
                col = DARK
            elif px == 1:
                col = TAN
            c.set(x, y, col)
    c.rect(0, 38, T - 1, 39, TAN)
    c.rect(0, 40, T - 1, 40, DARK)
    c.rect(0, 60, T - 1, T - 1, DARK)
    c.rect(0, 60, T - 1, 60, METAL)
    for _ in range(12):
        x, y = rng.randrange(T), rng.randrange(42, 59)
        if c.get(x, y) == METAL:
            c.set(x, y, DARK)
    # Портрет: рама накренилась на гвозде.
    c.line(32, 6, 22, 11, K, 1)
    c.line(32, 6, 43, 13, K, 1)
    c.set(32, 5, GREY)
    c.poly([(17, 12), (45, 15), (44, 35), (16, 32)], BRASS)
    c.poly([(18, 13), (44, 16), (43, 33), (17, 31)], GOLD)
    c.poly([(21, 16), (41, 18), (40, 31), (20, 29)], NAVY)
    c.ellipse(30.5, 22, 4, 4.5, SKIN)
    c.poly([(24, 30), (37, 31), (35, 26), (26, 26)], DARK)
    c.rect(27, 17, 34, 18, DARK)
    c.set(29, 22, K)
    c.set(32, 22, K)
    c.rect(29, 25, 32, 25, TAN)
    # Когти: три борозды и кровь.
    for d in (0, 4, 8):
        c.line(50 + d, 14, 46 + d, 34, DARK, 1)
        c.line(51 + d, 14, 47 + d, 34, GREY, 1)
    c.ellipse(8, 26, 2.5, 3, RED)
    for d in (-2, 0, 2):
        c.rect(8 + d, 20, 8 + d, 23, RED)
    c.rect(8, 30, 8, 36, RED)
    return c


def tex_window():
    """Стена с окном: кирпич, окно заколочено досками крест-накрест, в щелях ночное небо с
    луной, на подоконнике пальцы снаружи."""
    c = Canvas(T, T)
    _bricks(c, seed=306)
    c.rect(0, 55, T - 1, T - 1, GREY)
    c.rect(0, 55, T - 1, 55, WHITE)
    c.rect(0, 56, T - 1, 56, METAL)
    c.rect(0, T - 1, T - 1, T - 1, DARK)
    # Рама и стекло.
    c.rect(11, 5, 52, 46, K)
    c.rect(12, 6, 51, 45, GREY)
    c.rect(12, 6, 51, 6, WHITE)
    c.rect(15, 9, 48, 42, NAVY)
    for y in range(30, 43):
        for x in range(15, 49):
            if (x + y) % 2 == 0 and y > 36 or y > 39:
                c.set(x, y, SEA)
    c.ellipse(38, 18, 6.5, 6.5, WHITE)
    c.ellipse(40, 16, 1.5, 1.5, GREY)
    c.set(36, 20, GREY)
    c.set(37, 15, SKY)
    for x, y in ((18, 12), (24, 20), (20, 28), (46, 28), (28, 11)):
        c.set(x, y, SKY)
    # Сухая ветка на фоне неба.
    c.line(15, 36, 30, 24, K, 2)
    c.line(24, 29, 27, 17, K, 1)
    c.line(30, 24, 36, 26, K, 1)
    c.line(20, 32, 17, 23, K, 1)
    c.rect(31, 9, 32, 42, GREY)
    c.rect(15, 25, 48, 26, GREY)
    # Доски: три, внахлёст, с гвоздями.
    for (x0, y0, x1, y1) in ((9, 14, 54, 20), (10, 34, 55, 28), (13, 43, 50, 8)):
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy)
        nx, ny = -dy / n, dx / n
        for k, col in ((-3, DARK), (-2, TAN), (-1, METAL), (0, METAL), (1, METAL), (2, DARK)):
            c.line(x0 + nx * k, y0 + ny * k, x1 + nx * k, y1 + ny * k, col, 1)
            c.line(x0 + nx * k + 0.5, y0 + ny * k, x1 + nx * k + 0.5, y1 + ny * k, col, 1)
        for t in (0.06, 0.94):
            c.set(x0 + dx * t, y0 + dy * t, WHITE)
            c.set(x0 + dx * t + 1, y0 + dy * t, K)
    # Подоконник и пальцы.
    c.rect(9, 46, 54, 49, GREY)
    c.rect(9, 46, 54, 46, WHITE)
    c.rect(9, 49, 54, 49, K)
    for x in (20, 23, 26, 29):
        c.rect(x, 42, x + 1, 46, VIOLET)
        c.set(x + 1, 44, PLUM)
        c.rect(x, 47, x + 1, 47, PLUM)
    return c


def tex_morgue():
    """Ячейки морга 32×32 со сдвигом ряда: стальные дверцы с кромкой, ручка-скоба, петли,
    бирка, из-под одной течёт."""
    c = Canvas(T, T)
    for by in (0, 32):
        for bx in (0, 32):
            off = 16 if by == 32 else 0
            x0 = (bx + off) % T
            odd = (bx // 32 + by // 32) % 2
            body = (GREY, SKY)[odd]
            for y in range(by, by + 32):
                for x in range(32):
                    py = y - by
                    col = body
                    if x in (0, 31) or py in (0, 31):
                        col = K
                    elif x in (1, 30) or py in (1, 30):
                        col = DARK
                    elif x == 3 or py == 3:
                        col = WHITE
                    elif x == 28 or py == 28:
                        col = METAL if not odd else AQUA
                    elif (x + py * 3) % 11 == 0:
                        col = WHITE if odd else METAL
                    c.set((x0 + x) % T, y, col)
            # Петли слева, ручка-скоба справа.
            for py in (7, 22):
                for x in range(2, 6):
                    for yy in range(py, py + 4):
                        c.set((x0 + x) % T, by + yy, DARK if x in (2, 5) else METAL)
            for yy in range(11, 21):
                c.set((x0 + 24) % T, by + yy, K)
                c.set((x0 + 25) % T, by + yy, WHITE)
                c.set((x0 + 26) % T, by + yy, K)
            for x in (23, 27):
                c.set((x0 + x) % T, by + 11, K)
                c.set((x0 + x) % T, by + 20, K)
            # Бирка в рамке: номер штрихами.
            for x in range(9, 20):
                for yy in range(8, 15):
                    edge = x in (9, 19) or yy in (8, 14)
                    c.set((x0 + x) % T, by + yy, DARK if edge else WHITE)
            for x in (11, 13, 14, 16, 17):
                c.set((x0 + x) % T, by + 10 + (x % 2), K)
            for x in range(11, 18):
                c.set((x0 + x) % T, by + 12, GREY)
            if odd:
                # Кровь из-под дверцы.
                for x, n in ((8, 5), (9, 9), (10, 6), (15, 4), (16, 7)):
                    for yy in range(n):
                        c.set((x0 + x) % T, (by + 29 + yy) % T, RED if yy < n - 1 else DARK)
            else:
                # Зелёная слизь из щели и вмятина.
                for x, n in ((20, 4), (21, 8), (22, 5)):
                    for yy in range(n):
                        c.set((x0 + x) % T, (by + 29 + yy) % T, VIOLET if yy < n - 1 else PLUM)
                for x in range(8, 16):
                    c.set((x0 + x) % T, by + 22 + (x % 3 == 0), METAL)
    return c


def tex_floor():
    """Бетон: серые плиты 32×32 с тёмным швом, трещины, пятна грязи, решётка слива и
    размазанный след."""
    rng = random.Random(308)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 32, y % 32
            col = GREY
            if px == 0 or py == 0:
                col = K
            elif px == 1 or py == 1:
                col = WHITE
            elif px == 31 or py == 31:
                col = METAL
            elif (x * 3 + y * 5) % 13 == 0:
                col = METAL
            c.set(x, y, col)
    for sx, sy, n in ((6, 8, 20), (40, 36, 22), (44, 4, 12)):
        x, y = float(sx), float(sy)
        for _ in range(n):
            c.set(x, y, DARK)
            x += rng.choice((0, 1, 1))
            y += rng.choice((-1, 0, 1, 1))
    for _ in range(5):
        x, y = rng.randrange(4, T - 6), rng.randrange(4, T - 6)
        c.ellipse(x, y, rng.randint(2, 4), rng.randint(1, 3), METAL)
    # Слив.
    c.rect(10, 42, 21, 53, K)
    c.rect(11, 43, 20, 52, DARK)
    for x in range(12, 20, 2):
        c.rect(x, 44, x, 51, GREY)
    # След волочения: тёмно-красные мазки.
    for i in range(9):
        x = 36 + i * 2
        y = 20 + int(2 * math.sin(i * 0.9))
        c.rect(x, y, x + 1, y + 1 + (i % 2), RED if i % 3 else DARK)
    return c


def tex_floor_mud():
    """Грязь склепа: тёмная земля с комьями, зелёные лужи, кости и камешки. Рисунок замкнут
    по краям."""
    rng = random.Random(309)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = DARK
            if (x * 7 + y * 11) % 9 == 0:
                col = METAL
            elif (x * 5 - y * 3) % 14 == 0:
                col = K
            c.set(x, y, col)

    def blob(cx, cy, rx, ry, col):
        for yy in range(int(cy - ry - 1), int(cy + ry + 2)):
            for xx in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                    c.set(xx % T, yy % T, col)

    for _ in range(10):
        x, y = rng.randrange(T), rng.randrange(T)
        blob(x, y, rng.randint(2, 4), rng.randint(1, 2), METAL)
        c.set((x - 1) % T, (y - 1) % T, TAN)
    for x, y, rx, ry in ((14, 16, 8, 4), (46, 44, 9, 5), (60, 10, 5, 3)):
        blob(x, y, rx + 1, ry + 1, K)
        blob(x, y, rx, ry, PLUM)
        blob(x - 1, y - 1, rx - 2, ry - 2, VIOLET)
        c.set((x - 3) % T, (y - 2) % T, WHITE)
    # Кости: берцовая и рёбра.
    c.line(30, 24, 42, 20, WHITE, 2)
    c.ellipse(30, 24, 1.6, 1.6, WHITE)
    c.ellipse(42, 20, 1.6, 1.6, WHITE)
    c.line(31, 25, 41, 22, GREY, 1)
    for i in range(4):
        c.line(8 + i * 4, 50, 10 + i * 4, 44, WHITE, 1)
        c.set(10 + i * 4, 43, GREY)
    c.line(7, 51, 21, 51, GREY, 1)
    for _ in range(8):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == DARK:
            c.set(x, y, GREY)
    return c


def tex_floor_lino():
    """Линолеум сторожки: шашка 16×16, светлые клетки затёрты, синие с бликом, по шву грязь,
    кое-где капли крови."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 16, y % 16
            light = (x // 16 + y // 16) % 2 == 0
            if light:
                col = WHITE
                if (px + py) % 7 == 0 or (px * 3 + py) % 13 == 0:
                    col = GREY
            else:
                col = SEA
                if px == 1 or py == 1:
                    col = AQUA
                elif (px - py) % 9 == 0:
                    col = NAVY
            if px == 0 or py == 0:
                col = METAL if light else NAVY
            c.set(x, y, col)
    for x, y in ((22, 9), (24, 12), (27, 10), (52, 40), (55, 43)):
        c.rect(x, y, x + 1, y + 1, RED)
        c.set(x + 1, y + 1, DARK)
    c.ellipse(40, 54, 3, 2, RED)
    c.set(39, 53, WHITE)
    return c


def tex_ceiling():
    """Потолок: тёмный настил, через 32 пикселя балка со светлой кромкой, паутина в углах и
    редкие точки ламп (без ярких полос, иначе в перспективе они расходятся лучами)."""
    rng = random.Random(311)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = DARK
            if x % 8 == 0:
                col = K
            if y % 32 < 6:
                col = METAL if y % 32 in (1, 2) else DARK
                if y % 32 == 5:
                    col = K
                if y % 32 == 1 and x % 16 == 3:
                    col = TAN
            c.set(x, y, col)
    for _ in range(30):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == DARK:
            c.set(x, y, K)
    # Паутина под балками.
    for by in (6, 38):
        for bx in (16, 48):
            for k in range(1, 6):
                c.set(bx + k, by + k, GREY)
                c.set(bx - k, by + k, GREY)
            for k in (-3, -2, 2, 3):
                c.set(bx + k, by + 4, GREY)
            c.set(bx, by + 2, GREY)
    for y in (3, 35):
        for x in (8, 40):
            c.rect(x, y, x + 1, y + 1, GOLD)
    return c


# --- Зомби -------------------------------------------------------------------------------------
# Ходок: сутулый, голова завалена к плечу, серые лохмотья с дырой на рёбрах, одна штанина
# оборвана, руки тянутся вперёд. Могильщик: прямой, в широкополой шляпе, с седой бородой, в
# синем комбинезоне и сапогах, лопата штыком вверх. Различаются силуэтом (шляпа и лопата).

def _hand(c, x, y, skin, dx, dy):
    """Кисть с тремя пальцами в сторону (dx, dy)."""
    c.ellipse(x, y, 2.3, 2.3, skin)
    n = math.hypot(dx, dy) or 1.0
    dx, dy = dx / n, dy / n
    for k in (-2, 0, 2):
        bx, by = x - dy * k, y + dx * k
        c.line(bx + dx * 2, by + dy * 2, bx + dx * (5 if k == 0 else 4), by + dy * (5 if k == 0 else 4), skin, 1)


def _arm(c, sh, el, hd, sleeve, skin, fingers):
    """Рука: рваный рукав до локтя, голое предплечье, кисть."""
    c.line(el[0], el[1], hd[0], hd[1], skin, 3)
    c.line(sh[0], sh[1], el[0], el[1], sleeve, 4)
    if fingers:
        _hand(c, hd[0], hd[1], skin, fingers[0], fingers[1])
    else:
        c.ellipse(hd[0], hd[1], 2.3, 2.3, skin)


def _shovel(c, tail, tip):
    """Лопата: черенок от `tail` до `tip`, дальше штык со светлой кромкой и кровью на острие."""
    dx, dy = tip[0] - tail[0], tip[1] - tail[1]
    n = math.hypot(dx, dy) or 1.0
    dx, dy = dx / n, dy / n
    ang = math.atan2(dy, dx)
    c.line(tail[0], tail[1], tip[0], tip[1], METAL, 2)
    c.line(tail[0] - dy * 2.5, tail[1] + dx * 2.5, tail[0] + dy * 2.5, tail[1] - dx * 2.5, METAL, 2)
    bx, by = tip[0] + dx * 5, tip[1] + dy * 5
    _oval(c, bx, by, 6.2, 4.6, ang, GREY)
    c.poly([(bx - dy * 4.2 + dx * 2, by + dx * 4.2 + dy * 2), (bx + dy * 4.2 + dx * 2, by - dx * 4.2 + dy * 2),
            (bx + dx * 9, by + dy * 9)], GREY)
    c.line(tip[0] - dy * 3.6, tip[1] + dx * 3.6, tip[0] + dy * 3.6, tip[1] - dx * 3.6, GREY, 2)
    c.line(tip[0], tip[1], bx + dx * 4, by + dy * 4, WHITE, 1)
    c.set(bx + dx * 8, by + dy * 8, RED)
    c.set(bx + dx * 7 - dy, by + dy * 7 + dx, RED)
    c.set(bx + dx * 6 + dy * 2, by + dy * 6 - dx * 2, RED)


def _fallen(k, digger):
    """Падение: 1 осел на колени и заваливается назад, 2 лежит на полу в луже, рука торчит."""
    c = Canvas(T, T)
    cx, base = 32, 62
    cloth = SEA if digger else METAL
    if k == 1:
        # Голени на полу, бёдра вверх, корпус откинут, голова запрокинута.
        far = NAVY if digger else DARK
        # Ступни за коленями носками наружу, голени уходят вглубь.
        c.rect(cx + 8, base - 2, cx + 12, base, DARK if digger else VIOLET)
        c.rect(cx - 12, base - 2, cx - 8, base, DARK if digger else PLUM)
        for s in (-1, 1):
            c.rect(cx + s * 5 - 3, base - 13, cx + s * 5 + 3, base - 3, cloth)
            c.ellipse(cx + s * 5, base - 2.5, 4, 3, cloth)
            c.rect(cx + s * 5 - 2, base - 1, cx + s * 5 + 2, base, far)
        c.rect(cx - 1, base - 13, cx + 1, base - 5, far)
        c.poly([(cx - 8, base - 12), (cx + 8, base - 12), (cx + 5, base - 30), (cx - 12, base - 28)], GREY)
        if digger:
            c.poly([(cx - 7, base - 12), (cx + 7, base - 12), (cx + 4, base - 22), (cx - 9, base - 21)], SEA)
        else:
            c.rect(cx - 6, base - 22, cx - 3, base - 18, VIOLET)
            c.rect(cx - 6, base - 21, cx - 3, base - 21, K)
            c.rect(cx - 6, base - 19, cx - 3, base - 19, K)
            c.rect(cx + 1, base - 26, cx + 2, base - 23, RED)
        # Руки повисли до пола.
        c.line(cx + 6, base - 28, cx + 12, base - 17, GREY, 4)
        c.line(cx + 12, base - 17, cx + 14, base - 6, VIOLET, 3)
        _hand(c, cx + 14, base - 5, VIOLET, 0, 1)
        c.line(cx - 12, base - 27, cx - 16, base - 17, GREY, 4)
        c.line(cx - 16, base - 17, cx - 17, base - 7, PLUM, 3)
        _hand(c, cx - 17, base - 6, PLUM, 0, 1)
        c.line(cx - 4, base - 29, cx - 6, base - 33, VIOLET, 4)
        hx, hy = cx - 8, base - 38
        _oval(c, hx, hy, 5.5, 6.2, -0.5, VIOLET)
        if digger:
            c.poly([(hx - 3, hy + 2), (hx + 5, hy + 1), (hx + 3, hy + 9)], GREY)
            # Шляпа слетает.
            c.ellipse(cx + 12, base - 44, 9, 2, DARK)
            c.ellipse(cx + 12, base - 47, 5.5, 3.5, DARK)
            c.rect(cx + 7, base - 46, cx + 17, base - 46, BRASS)
        else:
            for x in range(hx - 6, hx + 2):
                c.set(x, hy - 6 + abs(x - hx + 2) // 2, DARK)
                c.set(x, hy - 5 + abs(x - hx + 2) // 2, DARK)
        c.line(hx - 3, hy - 2, hx - 1, hy, K, 1)
        c.line(hx - 3, hy, hx - 1, hy - 2, K, 1)
        c.line(hx + 2, hy - 3, hx + 4, hy - 1, K, 1)
        c.line(hx + 2, hy - 1, hx + 4, hy - 3, K, 1)
        c.ellipse(hx + 1, hy + 3.5, 2, 1.5, K)
        c.set(hx + 1, hy + 5, RED)
    else:
        # Лужа, тело плашмя головой вправо, ноги влево.
        c.ellipse(cx, base, 24, 2, DARK)
        c.ellipse(cx + 2, base, 17, 1.4, RED)
        c.line(cx - 12, base - 5, cx - 26, base - 3, cloth, 5)
        c.line(cx - 12, base - 3, cx - 22, base - 2, NAVY if digger else DARK, 4)
        c.rect(cx - 29, base - 6, cx - 27, base - 1, DARK if digger else VIOLET)
        c.poly([(cx - 13, base - 9), (cx + 7, base - 10), (cx + 8, base - 2), (cx - 13, base - 1)], GREY)
        if digger:
            c.poly([(cx - 13, base - 8), (cx - 2, base - 9), (cx - 2, base - 2), (cx - 13, base - 1)], SEA)
        else:
            c.rect(cx - 5, base - 8, cx - 1, base - 5, VIOLET)
            c.rect(cx - 4, base - 8, cx - 4, base - 5, K)
            c.rect(cx - 2, base - 8, cx - 2, base - 5, K)
        hx, hy = cx + 14, base - 5
        c.ellipse(hx, hy, 6, 5, VIOLET)
        c.rect(cx + 7, base - 7, cx + 9, base - 3, PLUM)
        c.line(hx - 1, hy - 2, hx + 1, hy, K, 1)
        c.line(hx - 1, hy, hx + 1, hy - 2, K, 1)
        c.rect(hx + 2, hy + 1, hx + 4, hy + 2, K)
        # Рука торчит вверх, скрюченная.
        c.line(cx + 2, base - 9, cx + 1, base - 16, GREY, 4)
        c.line(cx + 1, base - 16, cx + 4, base - 22, VIOLET, 3)
        _hand(c, cx + 5, base - 23, VIOLET, 0.4, -1)
        if digger:
            c.poly([(hx - 2, hy + 1), (hx + 5, hy + 1), (hx + 6, hy + 5), (hx, hy + 4)], GREY)
            c.ellipse(cx + 24, base - 2, 6, 1.8, DARK)
            c.ellipse(cx + 24, base - 5, 4, 3, DARK)
            _shovel(c, (cx - 4, base - 14), (cx - 20, base - 17))
        else:
            for x in range(hx - 5, hx + 4):
                c.set(x, hy - 5 + abs(x - hx) // 3, DARK)
    return c.finish()


def zombie(angle, phase, mode="walk", digger=False):
    """Зомби 64×64 в ракурсе `angle` (0 спереди … 4 со спины, лицом вправо на 1-3), шаг `phase`
    0/1. `mode`: walk, aim, fire, slash, die0..die2, hurt. `digger` могильщик: шляпа, борода,
    комбинезон и лопата вместо плевка. Ступни на 61-62 строке, ось по центру кадра, как у
    скелета пиратов."""
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    if mode.startswith("die"):
        k = int(mode[-1])
        if k == 0:
            return zombie(0, 0, "hurt", digger)
        return _fallen(k, digger)
    c = Canvas(T, T)
    bob = 1 if phase else 0
    turn = 1.0 if side else (0.55 if diag else 0.0)
    cloth_far, cloth_near = (NAVY, SEA) if digger else (DARK, METAL)
    top, bot = 21 - bob, 42 - bob
    w = 9 - 4 * turn
    lean = (1.5 if digger else 3.0) * turn
    sx = cx + lean
    ph = 1 if phase else -1
    spit = mode in ("aim", "fire")
    slash = mode == "slash"

    # Точки рук по ракурсу: (плечо, локоть, кисть, цвет кожи, пальцы, позади корпуса).
    arms = []
    shovel = None
    if digger:
        if slash:
            # Замах: обе руки вверх, лопата над головой штыком влево.
            arms.append(((sx + w, top + 3), (sx + w + 4, top - 2), (sx + w + 2, top - 7), VIOLET, None, True))
            arms.append(((sx - w, top + 3), (sx - w - 4, top - 2), (sx - w + 1, top - 8), VIOLET, None, True))
            shovel = ((sx + w + 6, top - 5), (cx - 12, top - 12))
        elif angle == 0:
            arms.append(((sx - w, top + 3), (sx - w - 2, top + 11), (sx - w - 2, top + 19), PLUM, (0, 1), False))
            arms.append(((sx + w, top + 3), (sx + w + 3, top + 10), (sx + w + 3, top + 14), VIOLET, None, False))
            shovel = ((sx + w + 3, 52), (sx + w + 4, 15 - bob))
        elif angle == 4:
            arms.append(((sx + w, top + 3), (sx + w + 2, top + 11), (sx + w + 2, top + 19), PLUM, (0, 1), False))
            arms.append(((sx - w, top + 3), (sx - w - 3, top + 10), (sx - w - 3, top + 14), VIOLET, None, False))
            shovel = ((sx - w - 3, 52), (sx - w - 4, 15 - bob))
        elif angle == 3:
            # Со спины вполоборота: лопата на плече, штык за спиной вверху.
            arms.append(((sx - w + 1, top + 4), (sx + 1, top + 10), (sx + 7, top + 6), VIOLET, None, False))
            shovel = ((sx + 11, top + 10), (sx - 8, top - 6))
        else:
            arms.append(((sx + 1, top + 3), (sx + 7, top + 5), (sx + 12, top + 2), PLUM, None, True))
            arms.append(((sx - 1, top + 4), (sx + 3, top + 11), (sx + 8, top + 9), VIOLET, None, False))
            shovel = ((sx - 6, top + 17), (sx + 16, top - 2))
    elif spit:
        arms.append(((sx - w, top + 3), (sx - w - 3, top + 11), (sx - w - 3, top + 19), PLUM, (0, 1), False))
        arms.append(((sx + w, top + 3), (sx + w + 3, top + 11), (sx + w + 3, top + 19), VIOLET, (0, 1), False))
    elif angle == 0:
        arms.append(((sx - w, top + 3), (sx - w - 4, top + 11), (sx - w - 5, top + 3 - ph), VIOLET, (0, -1), False))
        arms.append(((sx + w, top + 3), (sx + w + 3, top + 9), (sx + w + 4, top + 15 + ph), VIOLET, (0, 1), False))
    elif angle == 1:
        arms.append(((sx - w + 1, top + 3), (sx + 2, top + 4), (sx + 10, top + 1 - ph), PLUM, (1, 0.2), True))
        arms.append(((sx + w - 1, top + 4), (sx + w + 4, top + 9), (sx + w + 9, top + 8 + ph), VIOLET, (1, 0.5), False))
    elif angle == 2:
        arms.append(((sx, top + 3), (sx + 8, top + 2), (sx + 15, top + 1 - ph), PLUM, (1, 0.2), True))
        arms.append(((sx - 1, top + 4), (sx + 6, top + 8), (sx + 14, top + 7 + ph), VIOLET, (1, 0.5), False))
    elif angle == 3:
        arms.append(((sx + w - 2, top + 3), (sx + w + 3, top + 3), (sx + w + 8, top + 1 - ph), PLUM, (1, 0.2), True))
        arms.append(((sx - w + 1, top + 4), (sx - w + 1, top + 11), (sx - w + 7, top + 12 + ph), VIOLET, (1, 0.4), False))
    else:
        arms.append(((sx - w, top + 3), (sx - w - 3, top + 10), (sx - w - 4, top + 2 - ph), VIOLET, (0, -1), False))
        arms.append(((sx + w, top + 3), (sx + w + 3, top + 10), (sx + w + 4, top + 3 + ph), VIOLET, (0, -1), False))

    if shovel and (slash or angle == 3):
        _shovel(c, shovel[0], shovel[1])
    for sh, el, hd, skin, fingers, behind in arms:
        if behind:
            _arm(c, sh, el, hd, GREY, skin, fingers)

    # Ноги: шаркающий шаг, у ходока ближняя голень голая и ступни босые, у могильщика сапоги.
    for sign in (-1, 1):
        near = sign > 0
        step = (sign if phase else -sign) if mode == "walk" else 0
        hip = (cx + sign * (4 - 2.5 * turn), 41 - bob)
        lift = 2 if (step > 0 and turn == 0.0) else 0
        fx = cx + sign * (5 - 3.5 * turn) + step * 5 * turn
        fy = 60 - lift
        knee = ((hip[0] + fx) / 2 + 2 * turn + (0 if turn else sign), (hip[1] + fy) / 2)
        cloth = cloth_near if near else cloth_far
        skin = VIOLET if near else PLUM
        if near and not digger:
            c.line(knee[0], knee[1], fx, fy - 1, skin, 3)
            c.line(hip[0], hip[1], knee[0], knee[1], cloth, 5)
            for d in (-2, 0, 2):
                c.set(knee[0] + d, knee[1] + 3, cloth)
        else:
            c.line(hip[0], hip[1], knee[0], knee[1], cloth, 5)
            c.line(knee[0], knee[1], fx, fy - 1, cloth, 4)
            if not digger:
                c.line(fx, fy - 3, fx, fy - 1, skin, 3)
        if digger:
            c.rect(fx - 2, fy - 5, fx + 2, fy, DARK)
            c.rect(fx - 2, fy - 5, fx + 2, fy - 5, METAL)
        toe = 2 * turn if not back else 0
        c.rect(fx - 3 + toe, fy + 1, fx + 3 + 2 * toe, fy + 2, DARK if digger else skin)

    # Корпус: у ходока плечи уходят вперёд, подол рваный.
    for y in range(top, bot + 1):
        k = (y - top) / float(bot - top)
        off = lean * (1 - k)
        ww = w - 1.5 * k
        c.rect(int(round(cx + off - ww)), y, int(round(cx + off + ww)), y, GREY)
        if digger and y >= top + 7:
            c.rect(int(round(cx + off - ww)), y, int(round(cx + off + ww)), y, SEA)
    if digger:
        # Лямки комбинезона и нагрудник.
        for s in ((-1, 1) if not side else (1,)):
            lx = sx + s * (w - 3) * (0.3 if side else 1)
            if back:
                c.line(lx, top, sx - s * 1, top + 7, SEA, 2)
            else:
                c.line(lx, top, lx, top + 7, SEA, 2)
                c.set(lx, top + 6, GOLD)
        if not back and not side:
            d = 2 if diag else 0
            c.rect(sx - 3 + d, top + 10, sx + 3 + d, top + 10, NAVY)
            c.rect(sx - 3 + d, top + 10, sx - 3 + d, top + 14, NAVY)
            c.rect(sx + 3 + d, top + 10, sx + 3 + d, top + 14, NAVY)
            c.rect(sx - 3 + d, top + 14, sx + 3 + d, top + 14, NAVY)
        c.rect(int(cx - w + 2), bot - 1, int(cx + w - 2), bot - 1, NAVY)
        if back:
            # Спина: пояс, средний шов и накладные карманы, иначе это синий щит.
            px = int(round(cx + lean * 0.3))
            for x in range(px - 9, px + 10):
                if c.get(x, top + 12) == SEA:
                    c.set(x, top + 12, NAVY)
            for y in range(top + 13, bot - 1):
                if c.get(px, y) == SEA:
                    c.set(px, y, NAVY)
            for s in (-1, 1):
                x0 = px + s * 4
                for x, y in ((x0 - 1, top + 15), (x0, top + 15), (x0 + 1, top + 15), (x0 - 1, top + 16),
                             (x0 + 1, top + 16), (x0 - 1, top + 17), (x0, top + 18), (x0 + 1, top + 17)):
                    if c.get(x, y) == SEA:
                        c.set(x, y, NAVY)
        # Земля на коленях и рубахе.
        c.set(sx - 2, top + 3, METAL)
        c.set(sx + 3, top + 4, METAL)
    else:
        x0, x1 = int(round(cx - w + 1.5)), int(round(cx + w - 1.5))
        for x in range(x0, x1 + 1):
            if (x * 5) % 3 == 0:
                c.set(x, bot + 1, GREY)
            if (x * 7) % 5 == 0:
                c.rect(x, bot + 1, x, bot + 3, GREY)
        if back:
            # Прореха вдоль хребта.
            c.rect(sx - 2, top + 5, sx + 1, top + 15, VIOLET)
            for y in range(top + 6, top + 15, 2):
                c.rect(sx - 1, y, sx, y, PLUM)
            c.line(sx - 7 + 3 * turn, top + 4, sx - 5 + 3 * turn, top + 12, METAL, 1)
        elif side:
            c.rect(sx - 2, top + 8, sx, top + 13, VIOLET)
            c.rect(sx - 2, top + 9, sx, top + 9, K)
            c.rect(sx - 2, top + 11, sx, top + 11, K)
            c.rect(sx + 1, top + 4, sx + 2, top + 6, RED)
        else:
            d = 2 if diag else 0
            # Дыра на рёбрах и кровь на груди.
            c.rect(sx - 6 + d, top + 9, sx - 2 + d, top + 14, VIOLET)
            for y in (top + 10, top + 12):
                c.rect(sx - 6 + d, y, sx - 2 + d, y, K)
            c.rect(sx + 1 + d, top + 3, sx + 3 + d, top + 6, RED)
            c.set(sx + 2 + d, top + 7, RED)
            c.set(sx + 2 + d, top + 9, RED)
            c.line(sx + 4, top + 11, sx + 6, top + 17, METAL, 1)

    # Голова.
    if digger:
        hx, hy, tilt = sx + 2 * turn, 14 - bob, 0.0
    elif spit:
        hx, hy, tilt = sx, (12 if mode == "aim" else 14) - bob, 0.0
    elif angle == 4:
        hx, hy, tilt = sx - 3, 13 - bob, -0.4
    elif angle == 3:
        hx, hy, tilt = sx + 1, 13 - bob, -0.2
    elif angle == 2:
        hx, hy, tilt = sx + 4, 13 - bob, 0.5
    else:
        hx, hy, tilt = sx + 3, 13 - bob, 0.4
    hx, hy = int(round(hx)), int(round(hy))
    c.line(sx, top + 1, hx, hy + 5, PLUM if back else VIOLET, 4)
    _oval(c, hx, hy, 5.5, 6.2, tilt, VIOLET)
    if side and not digger:
        c.ellipse(hx + 3, hy + 4, 3, 2.5, VIOLET)
    if mode == "aim":
        # Щёки раздуты перед плевком.
        c.ellipse(hx - 4.5, hy + 3, 2.6, 2.6, VIOLET)
        c.ellipse(hx + 4.5, hy + 3, 2.6, 2.6, VIOLET)
    if digger:
        # Седые волосы из-под шляпы на затылке, борода клином спереди.
        if back:
            # Только по пикселям головы, чтобы затылок остался круглым; вполоборота справа
            # видны щека и ухо.
            x1 = hx + (1 if angle == 3 else 6)
            for y in range(hy - 3, hy + 5):
                for x in range(hx - 6, x1 + 1):
                    if c.get(x, y) == VIOLET and (y < hy + 4 or x % 2 == 0):
                        c.set(x, y, GREY)
            if angle == 3:
                c.rect(hx + 2, hy, hx + 3, hy + 1, PLUM)
        elif side:
            c.poly([(hx + 1, hy + 2), (hx + 6, hy + 2), (hx + 5, hy + 9)], GREY)
            c.rect(hx - 5, hy - 2, hx - 3, hy + 2, GREY)
        else:
            d = 1 if diag else 0
            c.poly([(hx - 4 + d, hy + 2), (hx + 4 + d, hy + 2), (hx + d, hy + 10)], GREY)
            c.rect(hx - 5 + d, hy, hx - 5 + d, hy + 3, GREY)
            c.rect(hx + 5 + d, hy, hx + 5 + d, hy + 3, GREY)
    else:
        # Клочья волос: спереди редкие, со спины шапкой с проплешиной.
        for x in range(hx - 6, hx + 7):
            for y in range(0, hy + 2):
                if c.get(x, y) == VIOLET:
                    if back:
                        depth = 6 + (x % 3) - (3 if abs(x - hx) < 2 and angle == 4 else 0)
                        if angle == 3 and x > hx + 2:
                            depth = 2
                    elif side:
                        depth = 5 if x <= hx else 1
                    else:
                        depth = 2 if x % 3 else 1
                    if not (x % 4 == 1 and not back and not side):
                        for yy in range(y, y + depth):
                            if c.get(x, yy) == VIOLET:
                                c.set(x, yy, DARK)
                    break
    # Лицо.
    if not back:
        if side:
            c.rect(hx + 2, hy - 2, hx + 3, hy - 1, WHITE)
            c.set(hx + 3, hy - 1, K)
            c.rect(hx + 1, hy - 3, hx + 4, hy - 3, PLUM)
            c.set(hx + 6, hy + 1, VIOLET)
            if digger:
                c.rect(hx + 3, hy + 3, hx + 5, hy + 3, K)
            else:
                c.rect(hx + 3, hy + 3, hx + 5, hy + 5, K)
                c.set(hx + 4, hy + 3, WHITE)
                c.set(hx + 4, hy + 6, RED)
        else:
            d = (2 if diag else 0) + (0 if digger or spit else 1)
            if digger:
                # Оба глаза горят из тени шляпы.
                c.rect(hx - 5, hy - 2, hx + 5, hy - 2, PLUM)
                for e in (-3, 2):
                    c.rect(hx + e + d, hy - 1, hx + e + 1 + d, hy, GOLD)
                    c.set(hx + e + (1 if e > 0 else 0) + d, hy, K)
                c.rect(hx - 2 + d, hy + 4, hx + 2 + d, hy + 5, K)
                c.set(hx - 1 + d, hy + 4, WHITE)
                c.set(hx + 1 + d, hy + 4, WHITE)
            else:
                # Белый глаз с точкой, пустая глазница, оскал с кровью.
                c.rect(hx - 4 + d, hy - 2, hx - 2 + d, hy, WHITE)
                c.set(hx - 3 + d, hy - 1, K)
                c.rect(hx - 4 + d, hy - 3, hx - 2 + d, hy - 3, PLUM)
                c.rect(hx + 1 + d, hy - 1, hx + 2 + d, hy, K)
                c.set(hx + d - 1, hy + 1, PLUM)
                if mode == "fire":
                    c.ellipse(hx, hy + 4, 3, 2.6, K)
                    c.set(hx - 1, hy + 2, WHITE)
                    c.set(hx + 1, hy + 2, WHITE)
                elif mode == "aim":
                    c.rect(hx - 1, hy + 4, hx + 1, hy + 4, K)
                    c.set(hx + 2, hy + 5, PLUM)
                else:
                    c.rect(hx - 3 + d, hy + 3, hx + 1 + d, hy + 4, K)
                    c.set(hx - 2 + d, hy + 3, WHITE)
                    c.set(hx + d, hy + 3, WHITE)
                    c.set(hx - 1 + d, hy + 4, WHITE)
                    c.rect(hx - 2 + d, hy + 5, hx - 2 + d, hy + 6, RED)
    if digger:
        # Шляпа: широкие поля, мятая тулья с лентой.
        bx = hx + (2 if side else (1 if diag else 0)) * (-1 if back and diag else 1) * (1 if not back else 0)
        c.ellipse(hx, hy - 9, 5.5, 3.6, DARK)
        c.rect(hx - 5, hy - 9, hx + 5, hy - 5, DARK)
        c.ellipse(bx, hy - 4.5, 10, 1.9, DARK)
        c.rect(hx - 5, hy - 6, hx + 5, hy - 6, BRASS)
        c.set(hx - 2, hy - 12, METAL)

    for sh, el, hd, skin, fingers, behind in arms:
        if not behind:
            _arm(c, sh, el, hd, GREY, skin, fingers)
    if shovel and not (slash or angle == 3):
        _shovel(c, shovel[0], shovel[1])
        # Кулак поверх черенка.
        for sh, el, hd, skin, fingers, behind in arms:
            if fingers is None and not behind:
                c.ellipse(hd[0], hd[1], 2.3, 2.3, skin)
    c.finish()
    if mode == "fire":
        # Плевок летит в камеру: зелёный сгусток у рта и брызги.
        c.ellipse(hx, hy + 5, 6, 5, PLUM)
        c.ellipse(hx, hy + 5, 4.4, 3.6, VIOLET)
        c.ellipse(hx - 1, hy + 4, 1.8, 1.4, WHITE)
        for dx, dy in ((-8, 2), (8, 4), (-6, 9), (6, 10), (0, 12)):
            c.set(hx + dx, hy + dy, VIOLET)
    if mode == "hurt":
        for x in range(T):
            for y in range(T):
                if c.get(x, y) in (VIOLET, PLUM) and (x + y) % 3 == 0:
                    c.set(x, y, RED)
    return c


def zombie_strips():
    out = {}
    for name, digger in (("skel", False), ("cut", True)):
        walk = []
        for a in range(5):
            for ph in range(2):
                walk.append(zombie(a, ph, "walk", digger))
        out[name + "_walk"] = strip(walk)
        out[name + "_die"] = strip([zombie(0, 0, "die%d" % k, digger) for k in range(3)])
    out["skel_fire"] = strip([zombie(0, 0, "aim"), zombie(0, 0, "fire")])
    out["cut_slash"] = strip([zombie(0, 0, "walk", True), zombie(0, 0, "slash", True)])
    return out


# --- Предметы, оружие, лицо --------------------------------------------------------------------

def bullet():
    """Гвоздь героя: летит шляпкой к игроку, остриём вглубь. Толстый стержень и широкая шляпка,
    чтобы читался на тёмной стене, блик по левой грани."""
    c = Canvas(16, 16)
    c.rect(7, 4, 9, 11, GREY)
    c.rect(7, 2, 8, 3, GREY)
    c.ellipse(8, 12.5, 4, 1.8, GREY)
    c.finish()
    c.rect(7, 3, 7, 10, WHITE)
    c.set(7, 1, WHITE)
    c.rect(5, 12, 9, 12, WHITE)
    for y in (5, 8):
        c.set(9, y, METAL)
    return c


def decor(kind):
    """Ориентир зала 64×64, низ на 62-63 строке: 0 надгробия, 1 гроб с откинутой крышкой,
    2 уличный фонарь, 3 самодельный миномёт, 4 мусорный бак с мешком, 5 колокол на раме."""
    c = Canvas(T, T)
    if kind == 0:
        # Земляной холмик, плита с полукруглым верхом, каменный крест, малая плита.
        c.ellipse(32, 62, 28, 4, METAL)
        c.ellipse(17, 30, 10, 10, GREY)
        c.rect(7, 30, 27, 62, GREY)
        c.rect(9, 28, 10, 60, WHITE)
        c.rect(12, 32, 22, 33, METAL)
        c.rect(12, 37, 22, 37, METAL)
        c.rect(13, 41, 21, 41, METAL)
        c.rect(16, 24, 17, 29, METAL)
        c.rect(14, 26, 19, 26, METAL)
        c.line(22, 44, 19, 52, DARK, 1)
        c.line(19, 52, 22, 58, DARK, 1)
        c.rect(42, 10, 49, 62, GREY)
        c.rect(33, 20, 58, 27, GREY)
        c.rect(43, 11, 43, 60, WHITE)
        c.rect(34, 21, 57, 21, WHITE)
        c.ellipse(45.5, 23.5, 2.5, 2.5, METAL)
        c.poly([(26, 46), (38, 44), (40, 62), (27, 62)], GREY)
        c.line(29, 50, 36, 49, METAL, 1)
        c.line(29, 54, 36, 53, METAL, 1)
        # Мох и сухая трава.
        for x in range(8, 26, 3):
            c.set(x, 61 - (x % 2), VIOLET)
        c.rect(42, 10, 46, 11, VIOLET)
        c.rect(48, 27, 51, 28, PLUM)
        for x in (4, 30, 52, 57):
            c.line(x, 62, x - 1, 55, BRASS, 1)
            c.line(x + 1, 62, x + 3, 56, GOLD, 1)
    elif kind == 1:
        # Гроб стоймя: шестигранник, внутри темно, оттуда рука; крышка прислонена справа.
        c.poly([(12, 8), (28, 8), (35, 22), (29, 63), (11, 63), (5, 22)], METAL)
        c.poly([(14, 11), (26, 11), (32, 22), (27, 59), (13, 59), (8, 22)], K)
        c.poly([(15, 12), (25, 12), (30, 22), (26, 58), (14, 58), (10, 22)], DARK)
        for y in range(14, 58, 6):
            c.set(12 if y > 22 else 13, y, GREY)
        c.line(22, 38, 30, 34, VIOLET, 3)
        _hand(c, 32, 33, VIOLET, 1, -0.4)
        c.rect(18, 30, 22, 31, PLUM)
        c.poly([(40, 10), (54, 12), (60, 26), (52, 63), (36, 63), (33, 24)], METAL)
        c.line(40, 12, 37, 60, TAN, 1)
        c.line(47, 13, 44, 61, DARK, 1)
        c.line(54, 16, 50, 61, DARK, 1)
        c.rect(45, 22, 47, 40, GOLD)
        c.rect(40, 27, 52, 29, GOLD)
        for x, y in ((38, 20), (56, 24), (39, 56), (50, 57)):
            c.set(x, y, GREY)
    elif kind == 2:
        # Чугунный фонарь: столб с перекладиной, гранёная лампа горит жёлтым.
        c.rect(26, 58, 37, 63, DARK)
        c.rect(28, 54, 35, 58, DARK)
        c.rect(30, 22, 33, 54, DARK)
        c.rect(30, 22, 30, 54, GREY)
        c.rect(28, 40, 35, 41, GREY)
        c.rect(22, 26, 41, 27, DARK)
        c.ellipse(22, 26, 1.5, 1.5, DARK)
        c.ellipse(41, 26, 1.5, 1.5, DARK)
        c.poly([(25, 8), (38, 8), (36, 22), (27, 22)], GOLD)
        c.ellipse(31.5, 15, 2.5, 4, WHITE)
        c.rect(31, 8, 32, 22, DARK)
        c.line(25, 8, 27, 22, DARK, 1)
        c.line(38, 8, 36, 22, DARK, 1)
        c.poly([(22, 8), (41, 8), (34, 2), (29, 2)], DARK)
        c.rect(22, 7, 41, 8, GREY)
        c.rect(31, 0, 32, 2, GREY)
        c.rect(27, 22, 36, 23, GREY)
    elif kind == 3:
        # Миномёт из трубы: плита, ствол на сошках, хомуты из проволоки, рядом мины.
        c.rect(8, 58, 30, 62, DARK)
        c.rect(8, 58, 30, 58, METAL)
        c.line(40, 30, 52, 62, METAL, 2)
        c.line(40, 30, 31, 62, DARK, 2)
        c.line(18, 56, 44, 12, VIOLET, 10)
        c.line(16, 55, 41, 12, SKY, 1)
        c.line(22, 58, 48, 14, PLUM, 2)
        _oval(c, 44.5, 11, 5, 2.6, math.atan2(-44, 26) + math.pi / 2, K)
        for t in (0.25, 0.55, 0.85):
            x, y = 18 + 26 * t, 56 - 44 * t
            c.line(x - 5, y - 3, x + 5, y + 3, GOLD, 2)
        c.rect(36, 28, 43, 32, GREY)
        for x in (50, 59):
            c.ellipse(x, 52, 3, 5, GREY)
            c.rect(x - 3, 52, x + 3, 60, GREY)
            c.poly([(x - 3, 48), (x + 3, 48), (x, 42)], RED)
            c.rect(x - 4, 60, x + 4, 62, DARK)
            c.rect(x - 1, 50, x - 1, 58, WHITE)
    elif kind == 4:
        # Бак: ребристая жесть, крышка набекрень, сбоку чёрный мешок, из бака слизь.
        c.poly([(12, 26), (42, 26), (40, 62), (14, 62)], GREY)
        for x in range(16, 40, 5):
            c.rect(x, 30, x, 59, METAL)
            c.rect(x + 1, 30, x + 1, 59, WHITE)
        c.rect(12, 26, 42, 28, WHITE)
        c.rect(13, 44, 41, 45, METAL)
        c.rect(14, 60, 40, 62, DARK)
        c.ellipse(27, 25, 14, 2.5, K)
        _oval(c, 30, 17, 17, 4, -0.28, GREY)
        _oval(c, 30, 16, 12, 2.2, -0.28, WHITE)
        c.line(27, 13, 33, 11, DARK, 2)
        c.rect(10, 34, 12, 40, DARK)
        c.rect(42, 34, 44, 40, DARK)
        for x, n in ((22, 12), (23, 16), (24, 9), (33, 7)):
            c.rect(x, 26, x, 26 + n, VIOLET)
        c.set(23, 43, PLUM)
        c.ellipse(52, 53, 9, 9, NAVY)
        c.ellipse(49, 50, 3, 4, SEA)
        c.poly([(49, 44), (55, 44), (56, 38), (52, 41), (48, 38)], NAVY)
        c.rect(50, 43, 54, 44, GOLD)
        c.line(56, 50, 58, 58, K, 1)
    else:
        # Колокол: рама из бруса с укосинами, бронзовый колокол, язык и верёвка.
        c.rect(8, 10, 12, 62, METAL)
        c.rect(51, 10, 55, 62, METAL)
        c.rect(4, 5, 59, 10, METAL)
        c.rect(4, 5, 59, 5, TAN)
        c.rect(8, 10, 8, 62, TAN)
        c.rect(51, 10, 51, 62, TAN)
        c.line(13, 22, 22, 11, DARK, 2)
        c.line(50, 22, 41, 11, DARK, 2)
        c.rect(5, 60, 15, 62, DARK)
        c.rect(48, 60, 58, 62, DARK)
        c.rect(30, 10, 33, 15, DARK)
        c.ellipse(31.5, 24, 9, 9, GOLD)
        c.poly([(22, 24), (41, 24), (45, 40), (18, 40)], GOLD)
        c.rect(17, 40, 46, 42, BRASS)
        c.rect(25, 20, 26, 38, WHITE)
        c.rect(22, 30, 41, 30, BRASS)
        c.rect(37, 20, 40, 39, BRASS)
        c.ellipse(31.5, 45, 2.5, 2.5, DARK)
        c.rect(31, 42, 32, 44, DARK)
        c.line(31.5, 47, 30, 58, GREY, 1)
        c.line(30, 58, 33, 62, GREY, 1)
        for x, y in ((10, 12), (53, 12), (10, 58), (53, 58)):
            c.set(x, y, GREY)
    return c.finish()


def pistol(frame):
    """Револьвер в руке снизу по центру, 128×96: рукав красной куртки с вязаной манжетой, голая
    кисть в бинте видна с тыла, большой палец слева вдоль рамки, указательный справа. Револьвер
    стволом вглубь (ось x=64, мушка у верхнего края): деревянная рукоять, курок, широкий барабан
    с долами и латунными донцами патронов, верхняя планка с прорезью, длинный ствол; кадр 1 со
    вспышкой."""
    c = Canvas(128, 96)
    # Рукав: расширяется книзу, складки и шов.
    for y in range(64, 96):
        w = 17 + (y - 64) // 4
        for x in range(64 - w, 64 + w):
            fold = (y - 64) % 11 == 9 and abs(x - 64) < w - 3
            col = DARK if fold else RED
            if x == 64 + w - 6:
                col = DARK
            c.set(x, y, col)
    for y in range(68, 96, 4):
        c.set(64 + 17 + (y - 64) // 4 - 8, y, GOLD)
    # Манжета: тёмная резинка в рубчик.
    c.rect(46, 59, 82, 66, DARK)
    for x in range(47, 82, 3):
        c.rect(x, 60, x, 65, METAL)
    # Револьвер. Рукоять: деревянные щёчки в насечку, стальная спинка.
    c.poly([(57, 44), (71, 44), (70, 33), (58, 33)], METAL)
    for y in range(35, 44, 2):
        c.rect(58, y, 61, y, DARK)
        c.rect(67, y, 70, y, DARK)
    c.rect(63, 33, 65, 44, GREY)
    # Щиток рамки за барабаном.
    c.ellipse(64, 30, 9.5, 4.5, GREY)
    # Барабан шире рамки: скруглённый, доли тёмными канавками.
    c.rect(53, 18, 75, 27, GREY)
    c.rect(54, 16, 74, 29, GREY)
    c.rect(56, 15, 72, 30, GREY)
    for x in (55, 58, 70, 73):
        c.rect(x, 17, x, 27, DARK)
    # Ствол сужается вдаль, под ним кожух экстрактора тенью справа.
    c.poly([(60, 16), (68, 16), (67, 4), (61, 4)], GREY)
    c.rect(67, 6, 68, 15, METAL)
    # Верхняя планка поверх барабана и целик.
    c.rect(61, 14, 67, 30, GREY)
    c.rect(62, 29, 66, 30, DARK)
    # Мушка.
    c.rect(63, 1, 65, 5, DARK)
    # Курок со спицей.
    c.rect(62, 31, 66, 37, DARK)
    c.rect(61, 31, 67, 32, DARK)
    # Кисть с тыла: широкая у запястья, сходится к рукояти.
    c.poly([(50, 59), (78, 59), (78, 48), (73, 41), (55, 41), (50, 48)], SKIN)
    for x0, x1 in ((57, 55), (64, 64), (71, 73)):
        c.line(x0, 43, x1, 50, TAN, 1)
    # Большой палец слева вдоль рамки, указательный справа у спуска.
    c.line(52, 48, 55, 36, SKIN, 5)
    c.line(76, 48, 74, 37, SKIN, 5)
    c.line(54, 44, 55, 40, TAN, 1)
    # Бинт через ладонь с пятном.
    c.rect(49, 51, 79, 56, WHITE)
    c.rect(49, 53, 79, 53, GREY)
    c.rect(49, 56, 79, 56, GREY)
    c.ellipse(59, 54, 2.5, 1.5, RED)
    c.line(71, 51, 75, 56, GREY, 1)
    c.finish()
    # Блики и мелочь после светотени: грани барабана, донца патронов, прорезь планки, ногти.
    for x in (54, 57, 69, 72):
        c.rect(x, 18, x, 26, WHITE)
    c.rect(62, 5, 62, 28, WHITE)
    c.rect(64, 6, 64, 28, DARK)
    for x in (56, 72):
        c.rect(x, 28, x + (1 if x < 64 else -1), 29, GOLD)
        c.set(x, 29, BRASS)
    c.set(64, 29, GREY)
    c.set(64, 1, GOLD)
    c.set(64, 2, GOLD)
    c.rect(63, 31, 65, 31, WHITE)
    for y in (33, 35):
        c.rect(63, y, 65, y, GREY)
    c.rect(54, 35, 56, 36, WHITE)
    c.rect(73, 36, 75, 37, WHITE)
    if frame:
        c.ellipse(64, 1, 19, 10, RED)
        c.ellipse(64, 0, 15, 8, GOLD)
        c.ellipse(64, 0, 8, 5, WHITE)
        for dx in (-22, 22):
            c.line(64 + dx * 0.6, 6, 64 + dx, 12, GOLD, 2)
    return c


def face(mode):
    """Лицо выжившего для HUD, 32×32: синяя бейсболка (купол с пуговкой и швами, белая нашивка,
    короткий козырёк дугой), волосы у висков, щетина, ворот красной куртки; 0 прямо, 1 глянул
    влево, 2 вправо, 3 больно (кровь из-под кепки), 4 ухмылка."""
    c = Canvas(32, 32)
    # Ворот и шея.
    c.poly([(5, 31), (27, 31), (24, 26), (8, 26)], RED)
    c.rect(13, 25, 19, 29, TAN)
    # Голова, уши, волосы у висков.
    c.ellipse(16, 18, 9, 9.5, SKIN)
    c.rect(6, 17, 7, 20, SKIN)
    c.rect(25, 17, 26, 20, SKIN)
    c.rect(7, 13, 8, 17, DARK)
    c.rect(24, 13, 25, 17, DARK)
    # Щетина по челюсти.
    for y in range(21, 28):
        for x in range(8, 25):
            if c.get(x, y) == SKIN and (x + y) % 2 == 0 and (abs(x - 16) > 5 or y > 24):
                c.set(x, y, TAN)
    # Кепка: купол уже козырька, сужается кверху, пуговка на макушке.
    for y, half in zip(range(2, 12), (3, 5, 7, 8, 8, 9, 9, 9, 9, 9)):
        c.rect(16 - half, y, 16 + half, y, SEA)
    c.rect(15, 1, 17, 1, SEA)
    # Козырёк дугой не шире купола (широкий читается каской): середина выше, края загнуты вниз.
    c.rect(8, 11, 24, 11, NAVY)
    c.rect(6, 12, 26, 12, NAVY)
    c.rect(6, 13, 10, 13, NAVY)
    c.rect(22, 13, 26, 13, NAVY)
    c.rect(11, 13, 21, 13, TAN)
    c.finish()
    # Швы клиньев, нашивка и кант козырька поверх светотени.
    for y in range(3, 11):
        c.set(11 - (y - 3) // 4, y, NAVY)
        c.set(21 + (y - 3) // 4, y, NAVY)
    c.rect(13, 5, 19, 9, WHITE)
    c.rect(15, 6, 17, 8, RED)
    c.set(16, 1, WHITE)
    c.rect(9, 11, 23, 11, AQUA)
    look = {0: 0, 1: -2, 2: 2, 3: 0, 4: 0}[mode]
    for e in (-4, 4):
        if mode == 3:
            c.line(16 + e - 2, 16, 16 + e + 2, 18, K, 1)
            c.line(16 + e - 2, 18, 16 + e + 2, 16, K, 1)
        else:
            c.rect(16 + e - 2, 16, 16 + e + 2, 18, WHITE)
            c.rect(16 + e + look - 1, 16, 16 + e + look, 18, K)
            c.rect(16 + e - 2, 15, 16 + e + 2, 15, DARK)
    c.rect(15, 18, 17, 21, TAN)
    c.set(17, 21, DARK)
    if mode == 4:
        c.rect(11, 23, 21, 25, WHITE)
        c.rect(11, 23, 21, 23, K)
        c.set(10, 22, K)
        c.set(22, 22, K)
        c.set(14, 24, GREY)
        c.set(18, 24, GREY)
    elif mode == 3:
        c.ellipse(16, 24.5, 3.5, 2, K)
        c.rect(14, 23, 18, 23, WHITE)
        # Кровь из-под козырька по щеке.
        c.rect(21, 14, 22, 21, RED)
        c.set(22, 22, RED)
        c.set(21, 24, RED)
        c.rect(9, 20, 10, 21, RED)
    else:
        c.rect(12, 24, 20, 24, K)
        c.set(20 if mode != 1 else 12, 23, K)
    return c


# --- Имена зеркала -----------------------------------------------------------------------------
# Те же публичные имена, что у `space_hold16.py`: сборщик и проверки берут слоты по ним.

def alien(angle, phase, mode="walk", rod=False):
    """Враг в ракурсе, имя зеркала: `rod` это второй враг (у зомби могильщик с лопатой)."""
    return zombie(angle, phase, mode, rod)


def alien_strips():
    return zombie_strips()


def shot():
    """Плевок зомби из основы: зелёный сгусток, с гвоздём героя не спутать."""
    return zombies16.shot()


def key():
    """Ключ от убежища из основы: латунный, с красной биркой."""
    return zombies16.key()


def medkit():
    """Аптечка из основы: белая сумка с красным крестом."""
    return zombies16.medkit()


tex_panels = tex_brick
tex_growth = tex_crypt
tex_hull = tex_window
tex_cargo = tex_morgue
tex_floor_grate = tex_floor_mud
tex_floor_tiles = tex_floor_lino


def textures():
    return {"wall_planks": tex_brick(), "wall_stone": tex_crypt(), "wall_pillar": tex_pillar(),
            "wall_exit": tex_exit(), "wall_cabin": tex_cabin(), "wall_hull": tex_window(), "wall_cargo": tex_morgue(),
            "floor_planks": tex_floor(), "floor_stone": tex_floor_mud(), "floor_carpet": tex_floor_lino(),
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
        zombies16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], zombies16.shaded(items))
