#!/usr/bin/env python3
"""Набор «Замки» для шутера × 16/32-bit «до выхода» (#137), зеркало `space_hold16.py` и
`pixel_hold16.py`: те же ключи, размеры холстов, число и порядок кадров и точки опоры (ноги
врагов на 61-62 строке по центру кадра, ложе арбалета вверх по оси 64, текстуры 64×64 со швом
по краю).

Тема: залы и подземелья чужого замка. Стены: тёсаная кладка, замшелый подвал с плющом, каменные
колонны, дубовые ворота-выход в арке, покои с гобеленом, стрельчатое окно на холмы, оружейная со
щитами. Полы: плиты, булыжник, багровый ковёр. Враги: стражник-арбалетчик в шлеме-котелке
(`skel_*`) и алебардист в остроконечном шлеме с наносником (`cut_*`), оба в чёрной кольчуге и
багровой тунике. Арбалет в латной перчатке рыцаря, болт, ключ, зелье, лицо рыцаря в шлеме.

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

def _masonry(seed, plinth=True):
    """Тёсаная кладка: ряды по 16, блоки 32 со сдвигом через ряд, у каждого блока свой тон,
    светлая кромка сверху и слева, тёмный шов снизу и справа. `plinth` затемняет нижний ряд."""
    rng = random.Random(seed)
    tone = {}
    c = Canvas(T, T)
    for y in range(T):
        row = y // 16
        off = 16 if row % 2 else 0
        for x in range(T):
            px = (x - off) % 32
            py = y % 16
            block = (row, ((x - off) % T) // 32)
            if block not in tone:
                tone[block] = rng.choice((0, 0, 1, 2))
            t = tone[block]
            dark = plinth and row == 3
            if py == 15 or px == 31:
                col = DARK if not dark else K
            elif py == 0 or px == 0:
                col = GREY if not dark else METAL
            elif dark:
                col = METAL if (px * 5 + py * 3) % 9 == 0 else DARK
            elif t == 1 and (px * 5 + py * 3) % 7 == 0:
                col = GREY
            elif t == 2 and (px * 3 + py * 5) % 7 == 0:
                col = DARK
            else:
                col = METAL
            c.set(x, y, col)
    # Щербины и сколы.
    for _ in range(26):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == METAL and c.get(x + 1, y) == METAL and not (plinth and y >= 48):
            c.set(x, y, DARK)
            c.set(x + 1, y, GREY)
    return c


def tex_panels():
    """Основная стена: тёсаная серая кладка, трещина, железное кольцо на скобе, тёмный цоколь
    с мхом в шве."""
    c = _masonry(301)
    # Трещина через блок второго ряда.
    pts = [(38, 17), (40, 21), (39, 24), (42, 27), (41, 30)]
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], DARK, 1)
    # Кольцо для цепи.
    c.rect(11, 36, 12, 38, DARK)
    c.ellipse(11.5, 42, 3.5, 3.5, DARK)
    c.ellipse(11.5, 42, 1.8, 1.8, METAL)
    c.set(10, 40, GREY)
    # Цоколь: выступ с бликом и мох в шве.
    c.rect(0, 47, T - 1, 47, K)
    c.rect(0, 48, T - 1, 48, GREY)
    c.rect(0, 62, T - 1, T - 1, K)
    for x in (3, 4, 5, 20, 21, 33, 34, 35, 36, 50, 58, 59):
        c.set(x, 47, PLUM)
        if x % 2:
            c.set(x, 46, VIOLET)
    return c


def tex_growth():
    """Подвал: тёмный бут неровными рядами, пятна мха и плети плюща с листьями сверху вниз."""
    rng = random.Random(302)
    c = Canvas(T, T)
    y0 = 0
    for h in (10, 12, 10, 12, 10, 10):
        x = rng.randrange(8)
        start = x
        while x < start + T:
            w = min(rng.randint(8, 16), start + T - x)
            if start + T - (x + w) < 6:
                w = start + T - x
            for yy in range(h):
                for xx in range(w):
                    col = DARK
                    if yy == h - 1 or xx == w - 1:
                        col = K
                    elif yy == 0 or xx == 0:
                        col = METAL
                    elif (xx * 3 + yy * 5 + x) % 11 == 0:
                        col = METAL
                    c.set((x + xx) % T, y0 + yy, col)
            x += w
        y0 += h
    # Мох на швах.
    for _ in range(11):
        x, y = rng.randrange(T), rng.randrange(4, T - 3)
        for dx in range(-3, 4):
            for dy in range(-1, 2):
                if abs(dx) + abs(dy) * 2 <= 3 + rng.randint(0, 1):
                    c.set((x + dx) % T, y + dy, VIOLET if dy < 0 else PLUM)
    # Плющ: стебель с волной, листья парами.
    for x0, length in ((6, 58), (21, 34), (37, 50), (53, 26)):
        ph = rng.random() * math.tau
        for y in range(length):
            x = x0 + 2.2 * math.sin(y * 0.35 + ph)
            c.set(int(round(x)) % T, y, PLUM)
            if y % 5 == 2:
                s = 1 if (y // 5) % 2 else -1
                lx = int(round(x)) + s * 2
                for dx, dy, col in ((0, 0, VIOLET), (s, 0, VIOLET), (0, 1, VIOLET), (s, 1, PLUM), (s, -1, VIOLET)):
                    c.set((lx + dx) % T, min(y + dy, T - 1), col)
    return c


def tex_pillar():
    """Колонны: два круглых каменных ствола по 32 с каннелюрами и светом слева, швы барабанов,
    пояса с зубцами и багровой полосой."""
    ramp = [K, DARK, DARK, METAL, METAL, METAL, GREY, GREY, GREY, GREY, GREY, GREY, METAL, METAL, METAL, METAL,
            METAL, METAL, METAL, METAL, METAL, METAL, METAL, METAL, METAL, DARK, METAL, DARK, DARK, DARK, DARK, K]
    darker = {WHITE: GREY, GREY: METAL, METAL: DARK, DARK: DARK, K: K}
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px = x % 32
            col = ramp[px]
            if px in (10, 20):
                col = darker[col]
            if y % 16 == 15:
                col = darker[col]
            elif y % 16 == 0 and col == METAL:
                col = GREY
            elif col == METAL and (px * 7 + y * 3) % 23 == 0:
                col = DARK
            elif col == GREY and (px * 3 + y * 7) % 19 == 0:
                col = WHITE
            c.set(x, y, col)
    for y0 in (5, 50):
        for x in range(T):
            px = x % 32
            edge = px in (0, 31)
            c.set(x, y0, WHITE if not edge else GREY)
            for k in range(1, 7):
                col = GREY if px < 20 else METAL
                if k in (3, 4):
                    col = TAN if k == 3 else DARK
                if k in (1, 2) and px % 4 >= 2:
                    col = METAL if px < 20 else DARK
                c.set(x, y0 + k, K if edge else col)
            c.set(x, y0 + 7, K)
    return c


def tex_exit():
    """Ворота-выход: полукруглая арка из клиньев, дубовые створки с железными полосами и
    кольцами, золотой замок на стыке, корона на замковом камне, два факела по углам."""
    c = _masonry(304, plinth=False)
    ax, ay = 31.5, 28.0
    for y in range(T):
        for x in range(T):
            d = math.hypot(x - ax, y - ay)
            door = (y >= ay and 11 <= x <= 52) or (y < ay and d <= 21.0)
            frame = not door and ((y >= ay and 5 <= x <= 58) or (y < ay and d <= 27.0))
            if frame:
                if y >= ay:
                    k = int((y - ay) // 9)
                    col = (GREY, METAL)[k % 2]
                    if (y - int(ay)) % 9 == 8 or x in (5, 58):
                        col = DARK
                    elif (y - int(ay)) % 9 == 0:
                        col = WHITE if k % 2 == 0 else GREY
                else:
                    a = math.atan2(ay - y, x - ax) / math.pi * 9.0
                    col = (GREY, METAL)[int(a) % 2]
                    if a - int(a) < 0.14:
                        col = DARK
                    elif d > 26.0:
                        col = DARK
                    elif d > 25.0 and int(a) % 2 == 0:
                        col = WHITE
                c.set(x, y, col)
            elif door:
                px = (x - 11) % 7
                col = BRASS
                if px == 6:
                    col = DARK
                elif (x * 7 + y * 3) % 17 == 0:
                    col = DARK
                # Тень арки на створках.
                if (y < ay and d > 19.5) or (y >= ay and x in (11, 52)):
                    col = K
                c.set(x, y, col)
    # Железные полосы с заклёпками.
    for y0 in (24, 50):
        for x in range(11, 53):
            if c.get(x, y0) in (BRASS, DARK):
                c.set(x, y0, METAL)
                c.set(x, y0 + 1, DARK)
                c.set(x, y0 + 2, DARK)
                c.set(x, y0 + 3, K)
                if x % 5 == 2:
                    c.set(x, y0 + 1, GREY)
    c.rect(31, 8, 32, 61, K)
    # Кольца-ручки.
    for hx in (22, 41):
        c.ellipse(hx, 39, 3.6, 3.6, K)
        c.ellipse(hx, 39, 2.6, 2.6, GREY)
        c.ellipse(hx, 39, 1.4, 1.4, BRASS)
        c.rect(hx - 1, 34, hx + 1, 35, DARK)
    # Замок на стыке створок.
    c.rect(27, 35, 36, 45, K)
    c.rect(28, 36, 35, 44, GOLD)
    c.rect(28, 44, 35, 44, BRASS)
    c.rect(35, 37, 35, 44, BRASS)
    c.ellipse(31.5, 39, 1.5, 1.5, K)
    c.rect(31, 40, 32, 42, K)
    # Порог.
    c.rect(11, 61, 52, 61, DARK)
    c.rect(5, 62, 58, 63, K)
    # Корона на замковом камне.
    c.rect(27, 1, 36, 6, GREY)
    c.rect(27, 6, 36, 6, DARK)
    c.rect(29, 4, 34, 5, GOLD)
    for x in (29, 31, 32, 34):
        c.set(x, 3, GOLD)
    c.set(29, 2, GOLD)
    c.set(34, 2, GOLD)
    # Факелы в углах над аркой.
    for tx in (3, 59):
        c.rect(tx, 9, tx + 1, 15, K)
        c.rect(tx - 1, 9, tx + 2, 10, DARK)
        c.ellipse(tx + 0.5, 5.5, 2.4, 3.4, RED)
        c.ellipse(tx + 0.5, 6.5, 1.4, 2.2, GOLD)
        c.set(tx, 7, WHITE)
        c.set(tx + 1, 1, RED)
    return c


def tex_cabin():
    """Покои лорда: белёная стена в дубовом каркасе, багровый гобелен с золотой короной и
    бахромой, резная рейка и дубовые филёнки внизу."""
    rng = random.Random(305)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = WHITE
            if (x * 5 + y * 9) % 23 == 0:
                col = SKY
            c.set(x, y, col)
    for _ in range(30):
        c.set(rng.randrange(T), rng.randrange(36), GREY)
    # Каркас: стойка на шве плитки и верхняя балка.
    c.rect(0, 0, T - 1, 3, BRASS)
    c.rect(0, 3, T - 1, 3, DARK)
    for x in range(2, T, 9):
        c.set(x, 1, DARK)
    c.rect(0, 0, 2, 36, BRASS)
    c.rect(61, 0, T - 1, 36, BRASS)
    c.rect(3, 4, 3, 36, DARK)
    c.rect(60, 4, 60, 36, GREY)
    # Гобелен.
    c.rect(13, 7, 50, 8, K)
    c.rect(12, 6, 13, 9, GOLD)
    c.rect(50, 6, 51, 9, GOLD)
    for y in range(9, 31):
        for x in range(17, 47):
            col = TAN
            if (x - 17) % 6 == 5:
                col = DARK
            elif (x - 17) % 6 == 1:
                col = RED
            c.set(x, y, col)
    for x in range(17, 47):
        c.set(x, 10, GOLD)
        c.set(x, 28, GOLD)
        c.set(x, 31, GOLD if x % 2 else WHITE)
        c.set(x, 32, GOLD if x % 2 else WHITE)
    c.rect(17, 9, 17, 30, GOLD)
    c.rect(46, 9, 46, 30, GOLD)
    c.rect(16, 9, 16, 31, K)
    c.rect(47, 9, 47, 31, K)
    # Корона: обод, три зубца, камни.
    c.rect(24, 19, 39, 24, K)
    c.rect(25, 20, 38, 23, GOLD)
    c.rect(25, 23, 38, 23, BRASS)
    for px in (25, 31, 37):
        c.poly([(px - 1, 20), (px + 2, 20), (px + 0.5, 13)], GOLD)
        c.set(px, 13, WHITE)
        c.set(px + 1, 13, WHITE)
    c.set(28, 21, RED)
    c.set(35, 21, RED)
    c.rect(31, 21, 32, 22, SEA)
    # Рейка и филёнки.
    c.rect(0, 36, T - 1, 39, BRASS)
    c.rect(0, 36, T - 1, 36, GOLD)
    c.rect(0, 39, T - 1, 39, K)
    for y in range(40, T):
        for x in range(T):
            px = x % 16
            col = BRASS
            if px in (0, 15):
                col = DARK
            elif 3 <= px <= 12 and 43 <= y <= 57:
                col = K if px == 3 or y == 43 else BRASS
                if px == 12 or y == 57:
                    col = DARK
                elif (px * 3 + y) % 11 == 0 and px != 3 and y != 43:
                    col = DARK
            c.set(x, y, col)
    c.rect(0, 60, T - 1, T - 1, DARK)
    c.rect(0, 60, T - 1, 60, K)
    return c


def tex_hull():
    """Стена с окном: стрельчатый проём в светлой раме, за ним небо, холмы и дальняя башня,
    железная решётка крестом, подоконник."""
    c = _masonry(306)
    wx, w, spring = 31.5, 9.0, 22.0

    def glass(x, y):
        if not 5 <= y <= 44 or abs(x - wx) > w:
            return False
        if y >= spring:
            return True
        return math.hypot(x - (wx - w), y - spring) <= 2 * w and math.hypot(x - (wx + w), y - spring) <= 2 * w

    for y in range(T):
        for x in range(T):
            if glass(x, y):
                if y < 16:
                    col = SEA
                elif y < 27:
                    col = AQUA
                else:
                    col = SKY
                hill = 36 + 2.5 * math.sin(x * 0.45) + 1.5 * math.sin(x * 0.2 + 1)
                if y >= hill:
                    col = VIOLET if y < hill + 4 else PLUM
                c.set(x, y, col)
            elif any(glass(x + dx, y + dy) for dx in (-3, -2, -1, 0, 1, 2, 3) for dy in (-3, -2, -1, 0, 1, 2, 3)
                     if abs(dx) + abs(dy) <= 4):
                near = any(glass(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                far = not any(glass(x + dx, y + dy) for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)
                              if abs(dx) + abs(dy) <= 3)
                col = K if near else (DARK if far else (WHITE if x < wx and y < 30 else GREY))
                c.set(x, y, col)
    # Облако, дальняя башня с красной крышей.
    for x, y, r in ((27, 13, 2.2), (30, 12, 2.6), (33, 13.5, 2)):
        for yy in range(9, 17):
            for xx in range(22, 41):
                if glass(xx, yy) and math.hypot(xx - x, (yy - y) * 1.3) <= r:
                    c.set(xx, yy, WHITE)
    c.rect(35, 29, 37, 37, METAL)
    c.rect(35, 29, 35, 37, GREY)
    c.poly([(34, 28), (38, 28), (36, 23)], RED)
    c.set(36, 32, K)
    # Решётка.
    for x in (28, 35):
        for y in range(5, 45):
            if glass(x, y):
                c.set(x, y, DARK)
    for y in (20, 32):
        for x in range(22, 42):
            if glass(x, y):
                c.set(x, y, DARK)
    # Подоконник.
    c.rect(18, 45, 45, 48, GREY)
    c.rect(18, 45, 45, 45, WHITE)
    c.rect(18, 48, 45, 48, DARK)
    c.rect(18, 49, 45, 49, K)
    return c


def _shield(c, cx, top, field, draw):
    """Щит-тарч на стене: прямой верх, остриё внизу, стальная кромка, чёрная обводка."""
    rows = {}
    for y in range(top, top + 25):
        k = y - top
        hw = 9.0 if k < 10 else 9.0 * math.sqrt(max(0.0, 1 - ((k - 10) / 14.5) ** 2))
        rows[y] = hw
    for y, hw in rows.items():
        for x in range(int(cx - hw - 1), int(cx + hw + 2)):
            d = abs(x - cx)
            if d <= hw + 1:
                c.set(x, y, K)
    c.rect(cx - 10, top - 1, cx + 10, top - 1, K)
    for y, hw in rows.items():
        for x in range(int(cx - hw), int(cx + hw + 1)):
            d = abs(x - cx)
            if d <= hw:
                edge = d > hw - 1.2 or y == top or (y + 1 in rows and abs(x - cx) > rows[y + 1] - 1.2) or y == top + 24
                c.set(x, y, GREY if edge else draw(x - cx, y - top, field))


def tex_cargo():
    """Оружейная: дощатая стена, на рейке два щита с гербами (багровый с золотой перевязью,
    синий с белым крестом), ниже стойка с мечами и секирой."""
    rng = random.Random(307)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px = x % 8
            col = BRASS
            if px == 0:
                col = K
            elif px == 7:
                col = DARK
            elif (x * 11 + y * 2 + (x // 8) * 5) % 19 == 0:
                col = DARK
            c.set(x, y, col)
    for _ in range(5):
        x, y = rng.randrange(1, T - 2), rng.randrange(T)
        if x % 8 in (2, 3, 4):
            c.rect(x, y, x + 1, y + 1, DARK)
    # Рейки с гвоздями.
    for y0 in (4, 44):
        c.rect(0, y0, T - 1, y0 + 2, DARK)
        c.rect(0, y0, T - 1, y0, METAL)
        c.rect(0, y0 + 3, T - 1, y0 + 3, K)
        for x in range(4, T, 8):
            c.set(x, y0 + 1, GREY)

    def bend(dx, dy, field):
        return GOLD if abs(dx - (dy - 9) * 0.9) <= 2.2 else field

    def cross(dx, dy, field):
        return WHITE if abs(dx) <= 1 or 6 <= dy <= 8 else field

    for cx, field, draw in ((16, TAN, bend), (48, NAVY, cross)):
        c.rect(cx - 1, 7, cx, 10, K)
        _shield(c, cx, 11, field, draw)
    # Мечи остриём вниз и секира посередине.
    for sx in (9, 54):
        c.rect(sx - 1, 37, sx + 2, 38, K)
        c.rect(sx, 37, sx + 1, 38, GOLD)
        c.rect(sx, 39, sx + 1, 43, DARK)
        c.rect(sx - 4, 47, sx + 5, 49, K)
        c.rect(sx - 3, 48, sx + 4, 48, GOLD)
        c.rect(sx - 1, 49, sx + 2, 61, K)
        c.rect(sx, 49, sx, 60, WHITE)
        c.rect(sx + 1, 49, sx + 1, 59, GREY)
    c.rect(30, 38, 33, 61, K)
    c.rect(31, 38, 32, 60, DARK)
    c.rect(31, 38, 31, 60, METAL)
    c.poly([(34, 48), (41, 45), (43, 53), (41, 60), (34, 57)], K)
    c.poly([(34, 50), (40, 47), (41, 53), (40, 58), (34, 55)], GREY)
    c.line(40, 48, 41, 53, WHITE, 1)
    c.line(41, 53, 40, 57, WHITE, 1)
    c.poly([(29, 50), (25, 52), (29, 55)], GREY)
    c.rect(0, 62, T - 1, T - 1, K)
    return c


def tex_floor():
    """Плиты: каменные квадраты 32×32 со сдвигом ряда, светлая кромка, тёмный шов, выбоины."""
    rng = random.Random(308)
    c = Canvas(T, T)
    tone = {}
    for y in range(T):
        row = y // 32
        off = 16 if row else 0
        for x in range(T):
            px, py = (x - off) % 32, y % 32
            block = (row, ((x - off) % T) // 32)
            if block not in tone:
                tone[block] = (0, 2, 1, 0)[len(tone) % 4]
            t = tone[block]
            col = METAL
            if px == 0 or py == 0:
                col = K
            elif px == 1 or py == 1:
                col = GREY
            elif px == 31 or py == 31:
                col = DARK
            elif t == 1 and (px * 5 + py * 3) % 7 == 0:
                col = GREY
            elif t == 2 and (px * 3 + py * 5) % 5 == 0:
                col = DARK
            c.set(x, y, col)
    for _ in range(16):
        x, y = rng.randrange(3, T - 3), rng.randrange(3, T - 3)
        if c.get(x, y) != K and c.get(x + 1, y) != K and x % 32 > 2 and y % 32 > 2:
            c.set(x, y, DARK)
            c.set(x + 1, y, DARK)
            c.set(x, y + 1, GREY)
    return c


def tex_floor_grate():
    """Булыжник двора: круглые камни в шахматном порядке, блик сверху слева, тёмные щели с мхом."""
    c = Canvas(T, T)
    for y in range(T):
        row = y // 16
        off = 8 if row % 2 else 0
        cy = row * 16 + 7.5
        for x in range(T):
            col_i = ((x - off) % T) // 16
            ccx = col_i * 16 + 7.5 + off
            dx = (x - ccx + 32) % T - 32
            dy = y - cy
            d = (dx / 7.2) ** 2 + (dy / 6.8) ** 2
            dark = (row * 3 + col_i * 5) % 4 == 1
            if d > 1.0:
                col = K
            elif ((dx + 2) / 3.6) ** 2 + ((dy + 2.2) / 2.8) ** 2 <= 1.0:
                col = GREY if not dark else METAL
            elif d > 0.62 and dx + dy > 3:
                col = DARK
            else:
                col = METAL if not dark else DARK
            c.set(x, y, col)
    for x, y in ((0, 15), (16, 31), (40, 47), (31, 0), (56, 16), (8, 63), (47, 32)):
        if c.get(x, y) == K:
            c.set(x, y, PLUM)
    return c


def tex_floor_tiles():
    """Ковёр: красный ворс, багровая сетка ромбов, в ромбах через один золотой крестик."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 16, y % 16
            d = abs(px - 8) + abs(py - 8)
            cell = (x // 16 + y // 16) % 2
            col = RED
            if d == 8 or (px == 0 and py == 0):
                col = TAN
            elif d == 7 and (x + y) % 2 == 0:
                col = TAN
            elif cell == 0 and ((px == 8 and 6 <= py <= 10) or (py == 8 and 6 <= px <= 10)):
                col = GOLD
            elif cell == 1 and d <= 1:
                col = TAN
            elif (x * 3 + y * 5) % 11 == 0:
                col = TAN
            c.set(x, y, col)
    return c


def tex_ceiling():
    """Потолок: тёмный настил, через 32 пикселя дубовая балка, редкие шляпки кованых гвоздей (без
    ярких полос, иначе в перспективе они расходятся лучами)."""
    rng = random.Random(309)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = DARK
            if x % 16 == 0:
                col = K
            b = y % 32
            if b < 6:
                col = (K, BRASS, BRASS, DARK, DARK, K)[b]
                if b == 3 and x % 2:
                    col = BRASS
                if b in (1, 2) and (x * 3 + b) % 13 == 0:
                    col = DARK
            c.set(x, y, col)
    for _ in range(26):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == DARK and y % 32 >= 6:
            c.set(x, y, K)
    for y in (2, 34):
        for x in (8, 40):
            c.set(x, y, METAL)
    return c


# --- Стража ------------------------------------------------------------------------------------

def _dome(c, cx, cy, rx, ry, col):
    """Верхняя половина эллипса: купол шлема."""
    for y in range(int(cy - ry - 1), int(cy) + 1):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                c.set(x, y, col)


def _helm(c, hx, top, rod, side=False):
    """Шлем: у арбалетчика котелок с широкими полями, у алебардиста остроконечный с ободом."""
    if rod:
        c.poly([(hx - 6, top + 7), (hx, top - 2), (hx + 6, top + 7)], GREY)
        c.rect(hx - 1, top - 2, hx, top, GREY)
        c.line(hx - 3, top + 5, hx - 1, top + 1, WHITE, 1)
        c.rect(hx - 6, top + 6, hx + 6, top + 7, METAL)
    else:
        _dome(c, hx, top + 6, 6, 6, GREY)
        c.line(hx - 3, top + 3, hx - 1, top + 1, WHITE, 1)
        d = 1 if side else 0
        c.rect(hx - 9 + d, top + 6, hx + 9 + d, top + 7, GREY)
        c.rect(hx - 8 + d, top + 6, hx + 3, top + 6, WHITE)


def _halberd(c, x, top, bottom, f):
    """Алебарда: древко в два пикселя от `top` до `bottom`, пика, лезвие топора в сторону `f` и
    крюк с обратной."""
    c.rect(x, top + 4, x + 1, bottom, BRASS)
    c.poly([(x - 1, top + 5), (x + 2, top + 5), (x + 0.5, top - 2)], GREY)
    xb = x + 2 if f > 0 else x - 1
    c.poly([(xb, top + 5), (xb + f * 5, top + 3), (xb + f * 7, top + 9), (xb + f * 5, top + 15), (xb, top + 12)], GREY)
    c.line(xb + f * 5, top + 4, xb + f * 6, top + 9, WHITE, 1)
    c.line(xb + f * 6, top + 9, xb + f * 5, top + 14, WHITE, 1)
    xh = x - 1 if f > 0 else x + 2
    c.poly([(xh, top + 6), (xh - f * 4, top + 9), (xh, top + 11)], GREY)
    c.rect(x, top + 16, x + 1, top + 17, DARK)


def _fallen(c, k, rod):
    """Падение: кадр 1 оседает на колени, шлем съезжает; кадр 2 лежит ничком, шлем откатился,
    оружие рядом."""
    cx = 32
    if k == 1:
        if rod:
            c.line(cx - 21, 22, cx - 15, 61, BRASS, 2)
            c.poly([(cx - 22, 22), (cx - 27, 25), (cx - 26, 33), (cx - 20, 30)], GREY)
            c.line(cx - 22, 22, cx - 23, 16, GREY, 2)
        else:
            c.rect(cx + 13, 57, cx + 26, 59, BRASS)
            c.line(cx + 22, 50, cx + 26, 57, GREY, 2)
            c.line(cx + 26, 57, cx + 23, 62, GREY, 2)
        c.rect(cx - 8, 57, cx + 10, 61, DARK)
        c.rect(cx + 9, 56, cx + 14, 61, BRASS)
        c.poly([(cx - 9, 45), (cx + 7, 45), (cx + 8, 58), (cx - 9, 58)], DARK)
        c.ellipse(cx - 7, 58, 2.5, 2.5, GREY)
        c.ellipse(cx + 4, 58, 2.5, 2.5, GREY)
        c.poly([(cx - 9, 31), (cx + 6, 29), (cx + 9, 49), (cx - 9, 50)], TAN)
        c.line(cx - 9, 43, cx + 8, 42, DARK, 2)
        c.rect(cx - 2, 42, cx - 1, 43, GOLD)
        c.line(cx - 9, 32, cx - 13, 46, DARK, 4)
        c.line(cx + 7, 31, cx + 12, 45, DARK, 4)
        c.ellipse(cx - 13, 48, 1.8, 1.8, SKIN)
        c.ellipse(cx + 12, 47, 1.8, 1.8, SKIN)
        c.ellipse(cx - 1, 25, 5.5, 6.5, DARK)
        c.ellipse(cx - 1, 27, 3.6, 3.6, SKIN)
        if rod:
            c.poly([(cx - 6, 21), (cx + 7, 18), (cx + 5, 9)], GREY)
            c.line(cx - 6, 21, cx + 7, 18, METAL, 2)
        else:
            c.ellipse(cx + 2, 16, 6, 4.5, GREY)
            c.line(cx - 8, 21, cx + 11, 17, GREY, 2)
            c.line(cx - 7, 20, cx + 3, 18, WHITE, 1)
        c.finish()
        c.rect(cx - 3, 27, cx - 2, 27, K)
        c.rect(cx, 27, cx + 1, 27, K)
        return c
    if rod:
        c.rect(cx - 26, 50, cx + 16, 51, BRASS)
        c.poly([(cx + 16, 49), (cx + 23, 50.5), (cx + 16, 52)], GREY)
        c.poly([(cx + 9, 49), (cx + 11, 44), (cx + 16, 43), (cx + 15, 49)], GREY)
    else:
        c.rect(cx - 22, 49, cx - 8, 51, BRASS)
        c.line(cx - 10, 44, cx - 7, 50, GREY, 2)
        c.line(cx - 7, 50, cx - 10, 53, GREY, 2)
    c.rect(cx - 24, 56, cx - 6, 60, DARK)
    c.rect(cx - 28, 54, cx - 24, 61, BRASS)
    c.ellipse(cx - 14, 57, 2.4, 2.4, GREY)
    c.rect(cx - 8, 54, cx - 6, 61, DARK)
    c.rect(cx - 6, 53, cx + 9, 61, TAN)
    c.rect(cx - 2, 53, cx - 1, 61, DARK)
    c.rect(cx - 2, 56, cx - 1, 57, GOLD)
    c.rect(cx + 9, 54, cx + 10, 61, DARK)
    c.ellipse(cx + 14, 57, 5, 5, DARK)
    c.ellipse(cx + 15, 58, 3.2, 3.2, SKIN)
    c.line(cx + 5, 55, cx + 2, 60, DARK, 4)
    c.ellipse(cx + 1, 61, 1.6, 1.6, SKIN)
    if rod:
        c.poly([(cx + 21, 53), (cx + 21, 62), (cx + 30, 58)], GREY)
        c.rect(cx + 21, 53, cx + 22, 62, METAL)
    else:
        c.ellipse(cx + 26, 57, 4, 4.5, GREY)
        c.rect(cx + 21, 51, cx + 22, 62, GREY)
        c.set(cx + 25, 55, WHITE)
    c.finish()
    c.rect(cx + 14, 58, cx + 15, 58, K)
    c.set(cx + 17, 58, K)
    return c


def guard(angle, phase, mode="walk", rod=False):
    """Стражник 64×64 в ракурсе `angle` (0 спереди … 4 со спины, лицом вправо на 1-3), шаг `phase`
    0/1. `mode`: walk, aim, fire, slash, die0..die2, hurt. `rod` алебардист: остроконечный шлем,
    наплечники и алебарда вместо арбалета. Ступни на 61-62 строке, ось по центру кадра, как у
    скелета пиратов и пришельца космоса."""
    c = Canvas(T, T)
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    turned = side or diag
    if mode.startswith("die"):
        k = int(mode[-1])
        if k == 0:
            return guard(0, 0, "hurt", rod)
        return _fallen(c, k, rod)
    bob = 1 if phase else 0
    sh = 22 - bob
    top = 6 - bob
    walk = mode == "walk"
    # Ноги: кольчужные чулки, стальной наколенник, бурые сапоги. Шагающая нога спереди и со
    # спины приподнята, сбоку вынесена вперёд.
    for sign in (-1, 1):
        fwd = (sign > 0) == bool(phase)
        lift = 0
        if side:
            hipx = cx + sign
            footx = cx + ((4 if fwd else -4) if walk else sign * 3)
        elif diag:
            hipx = cx + sign * 3
            footx = cx + sign * 4 + ((2 if fwd else -2) if walk else 0)
            lift = 1 if fwd and walk else 0
        else:
            hipx = cx + sign * 4
            footx = cx + sign * 5
            lift = 2 if fwd and walk else 0
        footy = 61 - lift
        kneex = (hipx + footx) / 2.0 + (1.5 if turned and not back else 0)
        kneey = 52 - lift
        c.line(hipx, 43 - bob, kneex, kneey, DARK, 5)
        c.line(kneex, kneey, footx, footy - 3, DARK, 4)
        if not back:
            c.ellipse(kneex + (1 if turned else 0), kneey, 2, 2, GREY)
        c.rect(footx - 2, footy - 6, footx + 2, footy - 1, BRASS)
        if turned and not back:
            c.rect(footx - 2, footy, footx + 4, footy + 1, BRASS)
        elif turned:
            c.rect(footx - 2, footy, footx + 3, footy + 1, BRASS)
        else:
            c.rect(footx - 3, footy, footx + 3, footy + 1, BRASS)
    w = 5 if side else (7 if diag else 8)
    # Алебарда за корпусом, когда стражник повёрнут боком или спиной: руку рисуем поверх.
    if rod and mode != "slash":
        hx_ = cx - 14 if angle == 0 else (cx + 11 if not back else cx + 13)
        _halberd(c, hx_, 4 - bob, 61, -1 if angle == 0 else 1)
    # Колчан за спиной арбалетчика.
    if not rod and back:
        c.line(cx + 6, sh - 1, cx - 1, sh + 15, BRASS, 5)
        c.rect(cx + 5, sh - 5, cx + 6, sh - 3, WHITE)
        c.rect(cx + 8, sh - 4, cx + 9, sh - 2, RED)
        c.set(cx + 7, sh - 5, RED)
    # Корпус: кольчужный подол, багровая туника клином, ворот, ремень.
    c.rect(cx - w, sh + 20, cx + w, sh + 24, DARK)
    c.poly([(cx - w, sh), (cx + w, sh), (cx + w + 1, sh + 21), (cx - w - 1, sh + 21)], TAN)
    c.rect(cx - 4 + (1 if turned else 0), sh - 2, cx + 4 + (1 if turned else 0), sh + 1, DARK)
    c.rect(cx - w, sh + 12, cx + w, sh + 13, DARK)
    if back:
        if rod:
            c.line(cx - w + 1, sh + 2, cx + w - 1, sh + 11, BRASS, 2)
        else:
            c.line(cx + 6, sh + 1, cx, sh + 14, BRASS, 5)
            c.line(cx + 4, sh + 4, cx + 1, sh + 11, DARK, 1)
        c.rect(cx, sh + 15, cx, sh + 21, DARK)
    elif side:
        c.rect(cx + w - 2, sh + 12, cx + w - 1, sh + 13, GOLD)
    else:
        o = 2 if diag else 0
        c.line(cx - 3 + o, sh + 4, cx + o, sh + 7, GOLD, 1)
        c.line(cx + o, sh + 7, cx + 3 + o, sh + 4, GOLD, 1)
        c.line(cx - 3 + o, sh + 5, cx + o, sh + 8, GOLD, 1)
        c.line(cx + o, sh + 8, cx + 3 + o, sh + 5, GOLD, 1)
        c.rect(cx - 1 + o, sh + 12, cx + o, sh + 13, GOLD)
        c.rect(cx + o, sh + 15, cx + o, sh + 21, DARK)
    hands = []
    tip = None
    # Руки и оружие.
    if rod:
        if mode == "slash":
            # Рубящий удар на камеру: древко наискось, большое лезвие внизу слева у самого зрителя.
            c.line(cx + 9, sh + 2, cx + 12, 15, DARK, 4)
            c.line(cx - 9, sh + 2, cx - 4, sh + 13, DARK, 4)
            c.line(cx + 14, 9, cx - 9, 43, BRASS, 3)
            c.line(cx - 9, 43, cx - 15, 53, GREY, 3)
            c.poly([(cx - 8, 41), (cx - 17, 34), (cx - 25, 41), (cx - 22, 52), (cx - 13, 49)], GREY)
            c.line(cx - 17, 35, cx - 24, 41, WHITE, 1)
            c.line(cx - 24, 41, cx - 22, 51, WHITE, 1)
            c.poly([(cx - 5, 44), (cx - 1, 49), (cx - 7, 48)], GREY)
            hands = [(cx + 12, 13), (cx - 3, sh + 13)]
        elif angle == 0:
            c.line(cx - 9, sh + 2, hx_ + 1, sh + 11, DARK, 4)
            c.line(cx + 9, sh + 2, cx + 10, sh + 13, DARK, 4)
            hands = [(hx_ + 0.5, sh + 12), (cx + 10, sh + 15)]
        elif back:
            c.line(cx + 9 - (2 if diag else 0), sh + 2, hx_, sh + 11, DARK, 4)
            c.line(cx - 9 + (2 if diag else 0), sh + 2, cx - 10 + (2 if diag else 0), sh + 13, DARK, 4)
            hands = [(hx_ + 0.5, sh + 12), (cx - 10 + (2 if diag else 0), sh + 15)]
        else:
            if diag:
                c.line(cx - 7, sh + 2, cx - 8, sh + 13, DARK, 4)
                hands.append((cx - 8, sh + 15))
            c.line(cx + 1, sh + 3, hx_, sh + 9, DARK, 4)
            hands.append((hx_ + 0.5, sh + 10))
        for sx in ((cx,) if side else (cx - w, cx + w)):
            c.ellipse(sx, sh + 1, 3.2, 2.6, GREY)
            c.set(sx - 1, sh, WHITE)
    elif turned and not back:
        # Арбалет наведён вперёд: ложе у плеча, дуга стоймя, тетива взведена.
        if diag:
            c.line(cx - 7, sh + 2, cx - 2, sh + 9, DARK, 4)
        c.line(cx + 1, sh + 3, cx + 10, sh + 7, DARK, 4)
        c.rect(cx + 4, sh + 5, cx + 21, sh + 7, BRASS)
        c.line(cx + 18, sh - 3, cx + 13, sh + 6, DARK, 1)
        c.line(cx + 13, sh + 6, cx + 18, sh + 15, DARK, 1)
        c.line(cx + 18, sh - 3, cx + 22, sh + 6, GREY, 2)
        c.line(cx + 22, sh + 6, cx + 18, sh + 15, GREY, 2)
        c.rect(cx + 23, sh + 5, cx + 26, sh + 6, WHITE)
        hands = [(cx + 11, sh + 8)]
        tip = (cx + 28, sh + 5)
    elif back:
        if diag:
            # Вполоборота со спины: дуга арбалета выглядывает из-за плеча.
            c.rect(cx + 7, sh + 6, cx + 17, sh + 8, BRASS)
            c.line(cx + 15, sh - 1, cx + 18, sh + 7, GREY, 2)
            c.line(cx + 18, sh + 7, cx + 15, sh + 15, GREY, 2)
            c.line(cx + 5, sh + 2, cx + 9, sh + 9, DARK, 4)
            c.line(cx - 7, sh + 2, cx - 8, sh + 13, DARK, 4)
            hands = [(cx + 10, sh + 10), (cx - 8, sh + 15)]
        else:
            c.line(cx - 9, sh + 2, cx - 10, sh + 13, DARK, 4)
            c.line(cx + 9, sh + 2, cx + 10, sh + 13, DARK, 4)
            hands = [(cx - 10, sh + 15), (cx + 10, sh + 15)]
    elif mode in ("aim", "fire"):
        # Арбалет смотрит в камеру: дуга поперёк груди, торец ложа и остриё болта по центру.
        c.line(cx - 9, sh + 2, cx - 5, sh + 9, DARK, 4)
        c.line(cx + 9, sh + 2, cx + 5, sh + 9, DARK, 4)
        pts = [(cx - 15, sh + 11), (cx - 8, sh + 7), (cx + 8, sh + 7), (cx + 15, sh + 11)]
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1], b[0], b[1], GREY, 2)
        if mode == "aim":
            c.line(cx - 15, sh + 11, cx, sh + 13, DARK, 1)
            c.line(cx, sh + 13, cx + 15, sh + 11, DARK, 1)
        c.rect(cx - 2, sh + 5, cx + 2, sh + 11, BRASS)
        hands = [(cx - 5, sh + 10), (cx + 5, sh + 10)]
        tip = (cx, sh + 8)
    else:
        # Идёт: арбалет наискось у груди, дуга у правого плеча.
        c.line(cx - 9, sh + 2, cx - 6, sh + 12, DARK, 4)
        c.line(cx + 9, sh + 2, cx + 6, sh + 8, DARK, 4)
        c.line(cx - 9, sh + 16, cx + 9, sh + 4, BRASS, 3)
        c.line(cx + 3, sh - 2, cx + 9, sh + 4, GREY, 3)
        c.line(cx + 9, sh + 4, cx + 14, sh + 11, GREY, 3)
        hands = [(cx - 5, sh + 13), (cx + 5, sh + 8)]
    for hx0, hy0 in hands:
        c.ellipse(hx0, hy0, 1.8, 1.8, SKIN)
    # Голова: кольчужный капюшон, лицо, шлем.
    hx = cx + (2 if side else (1 if diag else 0))
    if back and diag:
        hx = cx + 1
    c.rect(hx - 3, top + 14, hx + 3, top + 16, DARK)
    c.rect(hx - 5, top + 7, hx + 5, top + 13, DARK)
    c.ellipse(hx, top + 13, 5, 3.5, DARK)
    if back:
        for y in range(top + 8, top + 16):
            for x in range(hx - 4, hx + 5):
                if c.get(x, y) == DARK and (x + y * 2) % 4 == 0:
                    c.set(x, y, METAL)
    elif side:
        c.rect(hx + 1, top + 8, hx + 5, top + 13, SKIN)
        c.ellipse(hx + 3, top + 13, 2.5, 2.5, SKIN)
        c.set(hx + 6, top + 11, SKIN)
    elif diag:
        c.rect(hx - 1, top + 8, hx + 4, top + 13, SKIN)
        c.ellipse(hx + 1.5, top + 13, 3, 2.5, SKIN)
    else:
        c.rect(hx - 3, top + 8, hx + 3, top + 13, SKIN)
        c.ellipse(hx, top + 13, 3.5, 2.5, SKIN)
    _helm(c, hx, top, rod, side)
    if rod and not back:
        nx = hx + (5 if side else (2 if diag else 0))
        c.rect(nx, top + 8, nx, top + 11, GREY)
    c.finish()
    # Глаза, усы и остриё болта после обводки, чтобы не ушли в тень.
    if not back:
        if side:
            c.set(hx + 3, top + 10, K)
            c.rect(hx + 3, top + 13, hx + 5, top + 13, K)
        else:
            o = 1.5 if diag else 0
            c.set(hx - 2 + o, top + 10, K)
            c.set(hx + 2 + o, top + 10, K)
            c.rect(hx - 1 + o, top + 13, hx + 1 + o, top + 13, K)
            if mode == "fire":
                c.set(hx - 2 + o, top + 9, K)
                c.set(hx + 2 + o, top + 9, K)
    if tip and mode == "aim" and not turned:
        c.rect(tip[0] - 1, tip[1] - 1, tip[0], tip[1], WHITE)
    if mode == "fire":
        # Щелчок тетивы: болт сорвался, белая искра у ложа.
        fx, fy = tip if tip else (cx, sh + 8)
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0), (2, 0), (0, -2), (0, 2), (-3, 0), (3, 0),
                       (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            c.set(fx + dx, fy + dy, WHITE if abs(dx) + abs(dy) < 3 else GOLD)
    if mode == "hurt":
        for x in range(T):
            for y in range(T):
                if c.get(x, y) in (TAN, DARK, SKIN) and (x + y) % 3 == 0:
                    c.set(x, y, RED)
    return c


def guard_strips():
    out = {}
    for name, rod in (("skel", False), ("cut", True)):
        walk = []
        for a in range(5):
            for ph in range(2):
                walk.append(guard(a, ph, "walk", rod))
        out[name + "_walk"] = strip(walk)
        out[name + "_die"] = strip([guard(0, 0, "die%d" % k, rod) for k in range(3)])
    out["skel_fire"] = strip([guard(0, 0, "aim"), guard(0, 0, "fire")])
    out["cut_slash"] = strip([guard(0, 0, "walk", True), guard(0, 0, "slash", True)])
    return out


# Имена зеркала: демки и сборщик зовут врагов шутера так же, как у космоса.
alien = guard
alien_strips = guard_strips


# --- Предметы, оружие, лицо --------------------------------------------------------------------

def shot():
    """Выстрел стражи: болт летит прямо в камеру. Гранёный наконечник ромбом по центру, за ним
    крестом багровое оперение, всё в красной обводке опасности, чтобы не путать с болтом героя
    (тот узкий, остриём вверх, в чёрной обводке)."""
    c = Canvas(16, 16)
    # Оперение: четыре лопасти крестом, сужаются к краю кадра.
    c.poly([(8, 1), (10, 6), (6, 6)], TAN)
    c.poly([(8, 15), (10, 10), (6, 10)], TAN)
    c.poly([(1, 8), (6, 6), (6, 10)], TAN)
    c.poly([(15, 8), (10, 6), (10, 10)], TAN)
    # Наконечник: тёмное железо, светлые верхние грани и белый блик на острие.
    c.poly([(8, 3.5), (12.5, 8), (8, 12.5), (3.5, 8)], DARK)
    c.poly([(8, 4.5), (11.5, 8), (8, 8), (4.5, 8)], GREY)
    c.poly([(8, 5.5), (8, 8), (5.5, 8)], WHITE)
    c.outline(RED)
    c.rect(7, 7, 8, 8, WHITE)
    c.set(9, 9, K)
    return c


def bullet():
    """Болт героя летит вглубь: стальное остриё вверху, древко, красное оперение ласточкиным
    хвостом."""
    c = Canvas(16, 16)
    c.poly([(7.5, 0), (4.5, 6), (10.5, 6)], WHITE)
    c.rect(7, 6, 8, 12, BRASS)
    # Две лопасти уходят от древка назад и в стороны, между ними вырез.
    c.poly([(7, 8), (4, 11), (4, 15), (7, 12)], RED)
    c.poly([(8, 8), (11, 11), (11, 15), (8, 12)], RED)
    c.finish()
    c.rect(7, 2, 7, 4, WHITE)
    return c


def decor(kind):
    """Ориентир зала 64×64, низ на 62-63 строке: 0 мешки с зерном, 1 окованные лари (верхний
    открыт, в нём золото), 2 жаровня на треноге, 3 баллиста, 4 латы на стойке, 5 знамя чужого
    замка на подставке."""
    c = Canvas(T, T)
    if kind == 0:
        for bx, by, lean in ((18, 62, -1), (45, 62, 1), (31, 42, 0)):
            c.ellipse(bx, by - 10, 12, 10, SKIN)
            c.rect(bx - 10, by - 6, bx + 10, by, SKIN)
            c.poly([(bx - 4 + lean, by - 19), (bx + 4 + lean, by - 19), (bx + 6 + lean * 2, by - 25),
                    (bx - 6 + lean * 2, by - 25)], SKIN)
            c.rect(bx - 4 + lean, by - 20, bx + 4 + lean, by - 19, BRASS)
            c.line(bx - 8, by - 13, bx - 6, by - 3, BRASS, 1)
            c.line(bx + 3, by - 16, bx + 6, by - 9, BRASS, 1)
            c.line(bx - 2, by - 18, bx - 3, by - 13, BRASS, 1)
            for k in range(4):
                c.set(bx + 2 + k * 2, by - 4, BRASS)
    elif kind == 1:
        # Нижний ларь с выпуклой крышкой.
        c.rect(7, 40, 56, 62, BRASS)
        c.ellipse(31.5, 40, 24.5, 7, BRASS)
        c.rect(7, 40, 56, 41, DARK)
        for x in (13, 47):
            c.rect(x, 34, x + 3, 62, DARK)
            for y in (37, 46, 54, 60):
                c.set(x + 1, y, GREY)
        c.rect(7, 60, 56, 62, DARK)
        c.rect(28, 39, 35, 47, GOLD)
        c.rect(31, 42, 32, 45, K)
        for y in (48, 54):
            for x in range(19, 46, 6):
                c.rect(x, y, x + 2, y, DARK)
        # Верхний ларь: крышка откинута, внутри монеты.
        c.poly([(19, 16), (44, 16), (46, 4), (17, 4)], BRASS)
        c.poly([(21, 15), (42, 15), (43, 7), (20, 7)], DARK)
        c.rect(17, 3, 46, 4, DARK)
        c.ellipse(31.5, 16, 12, 4, GOLD)
        c.rect(17, 17, 46, 32, BRASS)
        c.rect(17, 17, 46, 18, DARK)
        c.rect(17, 30, 46, 32, DARK)
        for x in (21, 40):
            c.rect(x, 17, x + 2, 32, DARK)
            c.set(x + 1, 21, GREY)
            c.set(x + 1, 27, GREY)
        c.rect(29, 20, 34, 25, GOLD)
        for x, y in ((26, 14), (30, 13), (35, 14), (33, 12)):
            c.set(x, y, WHITE)
    elif kind == 2:
        # Жаровня: тренога, чаша с ободом, угли, пламя языками.
        c.line(32, 38, 17, 62, DARK, 3)
        c.line(32, 38, 47, 62, DARK, 3)
        c.rect(31, 38, 33, 62, DARK)
        c.rect(24, 51, 40, 52, METAL)
        c.poly([(16, 29), (48, 29), (41, 40), (23, 40)], DARK)
        c.rect(15, 27, 49, 29, METAL)
        c.rect(15, 27, 49, 27, GREY)
        for x in range(20, 46, 5):
            c.rect(x, 32, x + 1, 36, RED)
        c.poly([(20, 27), (23, 15), (27, 21), (32, 3), (37, 19), (41, 11), (44, 27)], RED)
        c.poly([(24, 27), (27, 21), (30, 23), (33, 10), (36, 22), (39, 20), (40, 27)], GOLD)
        c.poly([(29, 27), (32, 18), (35, 27)], WHITE)
        c.set(18, 12, RED)
        c.set(45, 6, GOLD)
        c.set(26, 8, GOLD)
    elif kind == 3:
        # Баллиста на колёсах: станина, ложе с болтом, дуга, тетива до ворота.
        c.line(12, 33, 56, 23, BRASS, 5)
        c.rect(27, 30, 32, 50, BRASS)
        c.line(14, 48, 29, 34, BRASS, 3)
        c.rect(8, 47, 54, 51, BRASS)
        c.rect(8, 51, 54, 51, DARK)
        c.line(47, 6, 24, 29, DARK, 1)
        c.line(24, 29, 53, 41, DARK, 1)
        c.line(46, 5, 53, 22, GREY, 3)
        c.line(53, 22, 53, 42, GREY, 3)
        c.line(18, 30, 58, 21, GREY, 1)
        c.poly([(57, 18), (63, 20), (58, 24)], WHITE)
        c.ellipse(13, 33, 4.5, 4.5, DARK)
        c.ellipse(13, 33, 2, 2, METAL)
        c.line(13, 33, 7, 27, DARK, 2)
        for wx in (17, 45):
            c.ellipse(wx, 55, 8, 8, BRASS)
            c.ellipse(wx, 55, 5.5, 5.5, DARK)
            c.line(wx - 5, 55, wx + 5, 55, BRASS, 1)
            c.line(wx, 50, wx, 60, BRASS, 1)
            c.ellipse(wx, 55, 1.8, 1.8, GREY)
    elif kind == 4:
        # Латы на стойке: шлем-ведро с плюмажем, кираса, наплечники, юбка из пластин.
        c.rect(20, 60, 43, 62, BRASS)
        c.rect(30, 44, 33, 60, BRASS)
        c.line(31, 54, 23, 60, BRASS, 2)
        c.line(32, 54, 40, 60, BRASS, 2)
        c.poly([(21, 25), (42, 25), (40, 43), (23, 43)], GREY)
        c.poly([(22, 43), (41, 43), (44, 51), (19, 51)], METAL)
        for x in (25, 31, 37):
            c.rect(x, 44, x, 50, DARK)
        c.rect(22, 41, 41, 42, GOLD)
        c.ellipse(18, 26, 6, 4.5, GREY)
        c.ellipse(45, 26, 6, 4.5, GREY)
        c.rect(14, 28, 19, 36, METAL)
        c.rect(44, 28, 49, 36, METAL)
        c.line(31.5, 27, 31.5, 39, WHITE, 1)
        c.line(25, 28, 25, 36, WHITE, 1)
        c.rect(28, 21, 35, 24, DARK)
        c.rect(25, 8, 38, 21, GREY)
        c.rect(26, 9, 29, 9, WHITE)
        c.rect(25, 20, 38, 21, METAL)
        c.rect(27, 4, 36, 7, RED)
        c.line(27, 5, 21, 8, RED, 3)
        c.line(21, 8, 19, 14, RED, 3)
        c.finish()
        c.rect(27, 13, 36, 14, K)
        c.rect(31, 13, 32, 19, K)
        for x in (28, 35):
            c.set(x, 17, DARK)
        return c
    else:
        # Знамя на крестовине: багровое полотнище с ласточкиным хвостом, золотая башня.
        c.rect(22, 60, 41, 62, DARK)
        c.line(31.5, 56, 24, 61, DARK, 2)
        c.line(31.5, 56, 39, 61, DARK, 2)
        c.rect(31, 5, 32, 60, BRASS)
        c.poly([(30, 5), (33, 5), (31.5, 0)], GOLD)
        c.rect(15, 7, 48, 8, BRASS)
        c.ellipse(15, 7.5, 1.5, 1.5, GOLD)
        c.ellipse(48, 7.5, 1.5, 1.5, GOLD)
        c.poly([(17, 9), (46, 9), (46, 44), (31.5, 36), (17, 44)], TAN)
        for x in (22, 29, 36, 42):
            c.line(x, 11, x, 34, DARK, 1)
        c.rect(17, 9, 46, 10, GOLD)
        c.line(17, 43, 31.5, 35, GOLD, 1)
        c.line(31.5, 35, 46, 43, GOLD, 1)
        # Башня-герб.
        c.rect(27, 17, 36, 30, GOLD)
        for x in (27, 31, 35):
            c.rect(x, 14, x + 1, 16, GOLD)
        c.rect(30, 24, 33, 30, TAN)
        c.rect(31, 19, 32, 21, TAN)
    return c.finish()


def key():
    """Ключ от ворот из основы: золотой, головка трилистником, две бородки."""
    return castles16.key()


def medkit():
    """Лечебное зелье из основы: пузатая склянка с красным настоем и белым крестом."""
    return castles16.medkit()


def pistol(frame):
    """Арбалет в руке снизу по центру, 128×96: латный наруч рыцаря с золотым обручем, стальная
    перчатка, арбалет ложем вглубь (ось x=64, остриё болта у верхнего края); кадр 1 после
    выстрела: тетива спущена, болта нет, белый след у стремени."""
    c = Canvas(128, 96)
    # Наруч: стальные пластины внахлёст, расширяется книзу.
    for y in range(62, 96):
        w = 17 + (y - 62) // 4
        for x in range(64 - w, 64 + w):
            k = (y - 62) % 11
            col = GREY
            if k == 10:
                col = DARK
            elif k == 0:
                col = WHITE
            elif k == 9:
                col = METAL
            c.set(x, y, col)
        if (y - 62) % 11 == 5:
            c.set(64 - w + 3, y, DARK)
            c.set(64 + w - 4, y, DARK)
    # Дуга арбалета: стальная, концы отогнуты к стрелку.
    arc = [(64, 15), (50, 16), (38, 20), (29, 26), (23, 34)]
    for sx in (1, -1):
        pts = [(64 + (x - 64) * sx, y) for x, y in arc]
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1], b[0], b[1], GREY, 5)
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1] - 1.5, b[0], b[1] - 1.5, WHITE, 1)
        c.ellipse(pts[-1][0], pts[-1][1], 3, 3, DARK)
    # Тетива: взведена углом к ореху или спущена прямой.
    if frame:
        c.line(23, 34, 105, 34, SKY, 1)
        c.line(40, 35, 88, 35, WHITE, 1)
    else:
        c.line(23, 34, 64, 46, SKY, 1)
        c.line(105, 34, 64, 46, SKY, 1)
    # Стремя у переднего конца.
    c.ellipse(64, 6, 7, 5, METAL)
    c.ellipse(64, 6, 4, 2.5, None)
    # Ложе: дубовое, с жёлобом, обмотка у дуги, орех.
    c.rect(59, 10, 69, 50, BRASS)
    c.rect(59, 10, 59, 50, DARK)
    c.rect(69, 10, 69, 50, DARK)
    c.rect(63, 20, 65, 44, DARK)
    c.rect(57, 12, 71, 19, DARK)
    for y in (13, 15, 17):
        c.rect(57, y, 71, y, TAN)
    c.ellipse(64, 46, 3, 2.5, GREY)
    c.rect(61, 22, 61, 42, GOLD)
    if not frame:
        # Болт в жёлобе: остриё за стременем, красное оперение у ореха.
        c.rect(63, 8, 65, 42, METAL)
        c.poly([(64, 0), (60, 9), (68, 9)], WHITE)
        c.poly([(62, 34), (59, 40), (62, 43)], RED)
        c.poly([(66, 34), (69, 40), (66, 43)], RED)
    # Перчатка: ладонь и четыре пальца-пластины поперёк ложа, костяшки с бликом.
    c.ellipse(64, 57, 16, 9, GREY)
    c.rect(50, 50, 78, 60, GREY)
    for k in range(4):
        x0 = 50 + k * 7
        c.rect(x0, 46, x0 + 6, 53, GREY)
        c.rect(x0 + 1, 46, x0 + 5, 46, WHITE)
        c.rect(x0, 50, x0 + 6, 50, METAL)
        c.rect(x0, 53, x0 + 6, 53, METAL)
        if k:
            c.rect(x0, 46, x0, 57, DARK)
    c.rect(78, 46, 78, 57, DARK)
    c.rect(50, 46, 50, 57, DARK)
    c.rect(51, 58, 77, 58, METAL)
    # Обруч наруча: золото на тёмной стали.
    c.rect(45, 60, 83, 66, METAL)
    c.rect(45, 60, 83, 60, GREY)
    c.rect(45, 62, 83, 64, GOLD)
    c.rect(45, 66, 83, 66, DARK)
    for x in range(49, 83, 8):
        c.rect(x, 63, x, 63, BRASS)
    c.finish()
    if frame:
        c.rect(63, 0, 65, 3, WHITE)
        c.line(58, 0, 60, 3, SKY, 1)
        c.line(70, 0, 68, 3, SKY, 1)
    return c


def face(mode):
    """Лицо рыцаря для HUD, 32×32: шлем с плоским верхом, красным гребнем и наносником, лицо в
    вырезе; 0 прямо, 1 глянул влево, 2 вправо, 3 больно (вмятина и кровь), 4 ухмылка."""
    c = Canvas(32, 32)
    # Гребень и хвост плюмажа.
    c.rect(11, 0, 20, 2, RED)
    c.line(11, 1, 5, 2, RED, 3)
    c.line(5, 2, 2, 6, RED, 3)
    # Шлем: коробка, блик на темени, обод, нащёчники.
    c.rect(5, 3, 26, 28, GREY)
    c.rect(4, 5, 27, 26, GREY)
    c.rect(7, 4, 13, 4, WHITE)
    c.rect(6, 5, 6, 9, WHITE)
    c.rect(5, 27, 26, 28, METAL)
    c.rect(8, 29, 23, 30, METAL)
    # Вырез с лицом.
    c.rect(8, 10, 23, 24, SKIN)
    c.rect(9, 25, 22, 26, SKIN)
    c.rect(8, 9, 23, 9, DARK)
    c.rect(7, 10, 7, 25, DARK)
    c.rect(24, 10, 24, 25, METAL)
    # Наносник.
    c.rect(15, 5, 16, 16, GREY)
    c.rect(15, 5, 15, 15, WHITE)
    for x, y in ((6, 13), (6, 22), (25, 13), (25, 22), (10, 6), (21, 6)):
        c.set(x, y, DARK)
    look = {0: 0, 1: -1, 2: 1, 3: 0, 4: 0}[mode]
    for e in (-4, 5):
        ex = 15 + e
        if mode == 3:
            c.line(ex - 2, 13, ex + 1, 16, K, 1)
            c.line(ex - 2, 16, ex + 1, 13, K, 1)
        else:
            c.rect(ex - 2, 13, ex + 1, 16, WHITE)
            c.rect(ex - 1 + look, 14, ex + look, 16, K)
            c.rect(ex - 2, 12, ex + 1, 12, BRASS if mode != 4 else K)
    c.rect(15, 17, 16, 19, BRASS)
    if mode == 4:
        c.rect(11, 21, 20, 23, WHITE)
        c.rect(11, 21, 20, 21, K)
        c.rect(11, 24, 20, 24, K)
        c.set(10, 20, K)
        c.set(21, 20, K)
    elif mode == 3:
        c.ellipse(15.5, 22.5, 3.5, 2, K)
        # Вмятина на шлеме и кровь из-под обода.
        c.line(20, 4, 24, 8, DARK, 1)
        c.line(24, 8, 22, 9, DARK, 1)
        c.rect(19, 10, 20, 13, RED)
        c.set(20, 14, RED)
    else:
        c.rect(12, 22, 19, 22, K)
        c.set(11, 21, K) if mode == 1 else None
        c.set(20, 21, K) if mode == 2 else None
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
    out.update(guard_strips())
    out.update(textures())
    return out


if __name__ == "__main__":
    if "--preview" in sys.argv:
        castles16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], castles16.shaded(sprites()))
