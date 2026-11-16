#!/usr/bin/env python3
"""Набор «Сладости» для шутера × 16/32-bit «до выхода» (#137), зеркало `space_hold16.py` и
`pixel_hold16.py`: те же ключи, размеры холстов, число и порядок кадров и точки опоры (ноги
врагов на 61-62 строке по центру кадра, ствол оружия вверх по оси 64, текстуры 64×64 со швом
по краю).

Тема: пряничная кондитерская, которую заняли мармеладные мишки. Стены: пряничная кладка на
глазури, шоколадный погреб с орехами, колонны из карамельных тростей, дверь-плитка шоколада в
раме из тростей, лавка в розовую полоску с картиной торта, окно из леденца, штабель коробок
конфет. Полы: вафля, плитка шоколада, розовая глазурь с посыпкой. Враги: красный мишка с
трубочкой-плевалкой и патронташем драже (`skel_*`) и мятный мишка в повязке с карамельной
тростью (`cut_*`). Кондитерский шприц в пряничной руке, капля крема, ключ-бублик, капкейк,
лицо пряничного человечка.

    python3 tools/sweets_hold16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweets16  # noqa: E402
from sweets16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, METAL,  # noqa: E402
                      DARK, RED, VIOLET, PLUM)

T = 64
SPRINKLES = (AQUA, WHITE, GOLD, RED, SKY)


# --- Текстуры ----------------------------------------------------------------------------------

def _drip(x, seed=0.0):
    """Нижний край потёка глазури в столбце `x`: период 64, поэтому шов по краю сходится."""
    return 5 + 3 * math.sin(x * math.tau / 32.0 + seed) + 2.5 * math.sin(x * math.tau / 64.0 * 3 + 1.0 + seed)


def tex_ginger():
    """Основная стена: пряничные кирпичи 32×16 вперевязку на белой глазури, сверху стекает
    розовая глазурь, на кирпичах редкие драже, снизу шоколадный плинтус."""
    rng = random.Random(301)
    c = Canvas(T, T)
    for y in range(T):
        row = y // 16
        for x in range(T):
            px, py = (x + row * 16) % 32, y % 16
            col = SKIN
            if px in (0, 1) or py in (0, 1):
                col = WHITE
            elif px == 2 or py == 2:
                col = TAN
            elif px == 31 or py == 15:
                col = GOLD
            c.set(x, y, col)
    for _ in range(46):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == SKIN:
            c.set(x, y, TAN)
    # Драже, вдавленные в пряник: по одному на кирпич через один.
    for row in range(4):
        for k in range(2):
            x = (k * 32 + 16 - row * 16 + (7 if (row + k) % 2 else -6)) % T
            y = row * 16 + 8
            col = (AQUA, VIOLET, GOLD, RED)[(row + k * 3) % 4]
            for dx in (0, 1):
                for dy in (0, 1):
                    c.set((x + dx) % T, y + dy, col)
            c.set((x + 2) % T, y + 1, TAN)
            c.set(x, y + 2, TAN)
            c.set((x + 1) % T, y + 2, TAN)
    # Потёки розовой глазури сверху.
    for x in range(T):
        h = int(round(_drip(x)))
        for y in range(0, h + 1):
            c.set(x, y, VIOLET)
        c.set(x, h + 1, PLUM)
        if h >= 6:
            c.set(x, 1, WHITE)
    # Шоколадный плинтус.
    c.rect(0, 57, T - 1, T - 1, METAL)
    c.rect(0, 57, T - 1, 57, K)
    c.rect(0, 58, T - 1, 58, TAN)
    for x in range(T):
        if x % 8 == 0:
            c.rect(x, 59, x, T - 1, DARK)
    return c


def tex_choco():
    """Шоколадный погреб: колотые глыбы шоколада со светом сверху слева, тёмные щели, в глыбах
    орехи, по щелям течёт карамель."""
    rng = random.Random(302)
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, K)
    y = 0
    heights = [13, 11, 14, 12, 14]
    for h in heights:
        x = rng.randrange(0, 12)
        left = T
        while left > 0:
            w = rng.randint(11, 19)
            if left - w < 8:
                w = left
            body = METAL if rng.random() < 0.7 else DARK
            for yy in range(y + 1, y + h - 1):
                for i in range(1, w - 1):
                    xx = (x + i) % T
                    col = body
                    if yy == y + 1 or i == 1:
                        col = TAN if body == METAL else METAL
                    elif yy == y + h - 2 or i == w - 2:
                        col = DARK if body == METAL else K
                    c.set(xx, yy, col)
            # Скол в углу и орех.
            c.set((x + 1) % T, y + 1, K)
            c.set((x + w - 2) % T, y + h - 2, K)
            if w > 13 and rng.random() < 0.6:
                nx, ny = x + rng.randint(4, w - 6), y + rng.randint(4, h - 5)
                for dx, dy, col in ((0, 0, GOLD), (1, 0, GOLD), (2, 0, BRASS), (0, 1, GOLD), (1, 1, BRASS), (2, 1, BRASS)):
                    c.set((nx + dx) % T, ny + dy, col)
                c.set(nx % T, ny - 1, BRASS)
                c.set((nx + 1) % T, ny + 2, K)
            x += w
            left -= w
        y += h
    # Карамельные потёки по щелям: две струйки с каплей на конце.
    for x0, y0, n in ((9, 0, 21), (41, 24, 17), (54, 0, 9)):
        for i in range(n):
            x = x0 + (1 if (i // 5) % 2 else 0)
            c.set(x, (y0 + i) % T, GOLD)
            c.set(x + 1, (y0 + i) % T, BRASS)
        c.rect(x0, (y0 + n) % T, x0 + 2, (y0 + n) % T + 1, GOLD)
        c.set(x0, (y0 + n) % T, WHITE)
    return c


def tex_cane():
    """Колонна: четыре карамельные трости в красно-белую косую полосу, круглые по тени, два
    шоколадных обруча с золотыми драже."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px = x % 16
            red = ((y + px) % 16) < 8
            if px in (0, 15):
                col = K
            elif px in (1, 13, 14):
                col = PLUM if red else GREY
            elif px in (3, 4) and red:
                col = VIOLET
            else:
                col = RED if red else WHITE
            c.set(x, y, col)
    for y in (10, 48):
        c.rect(0, y, T - 1, y + 4, METAL)
        c.rect(0, y, T - 1, y, TAN)
        c.rect(0, y + 4, T - 1, y + 4, K)
        for x in range(4, T, 8):
            c.set(x, y + 2, GOLD)
            c.set(x + 1, y + 2, BRASS)
    return c


def tex_exit():
    """Дверь выхода: две створки из плитки шоколада дольками, рама из карамельной трости в
    красно-белую полосу, над створками розовая вывеска, на створках мятные стрелки вверх и
    замок-сердце из леденца."""
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, DARK)
    # Створки: дольки 13×12 с фаской.
    for y in range(12, 60):
        for x in range(6, 58):
            px, py = (x - 6) % 13, (y - 12) % 12
            col = METAL
            if px == 0 or py == 0:
                col = K
            elif px == 1 or py == 1:
                col = TAN
            elif px == 12 or py == 11:
                col = DARK
            c.set(x, y, col)
    c.rect(31, 12, 32, 59, K)
    c.rect(30, 12, 30, 59, TAN)
    # Рама в полосу трости.
    for y in range(T):
        for x in range(T):
            if x < 6 or x > 57 or y > 59 or y < 3:
                c.set(x, y, RED if ((x + y) // 4) % 2 == 0 else WHITE)
    for y in range(T):
        c.set(5, y, PLUM if c.get(5, y) == RED else GREY)
        c.set(58, y, K)
    # Вывеска: розовая табличка с белыми штрихами глазури.
    c.rect(14, 3, 49, 11, K)
    c.rect(15, 4, 48, 10, VIOLET)
    c.rect(15, 10, 48, 10, PLUM)
    for x in (19, 25, 31, 37, 43):
        c.rect(x, 6, x + 2, 8, WHITE)
    # Стрелки на створках.
    for cx in (18, 45):
        c.poly([(cx - 7, 41), (cx + 7, 41), (cx, 27)], K)
        c.rect(cx - 3, 41, cx + 3, 52, K)
        c.poly([(cx - 5, 40), (cx + 5, 40), (cx, 29)], AQUA)
        c.rect(cx - 2, 40, cx + 2, 51, AQUA)
        c.line(cx - 1, 31, cx - 3, 38, SKY, 1)
    # Замок: красное сердце-леденец в золотой оправе.
    c.ellipse(31.5, 37, 6, 6, K)
    c.ellipse(31.5, 37, 5, 5, GOLD)
    c.ellipse(29.5, 35.5, 2, 2, RED)
    c.ellipse(33.5, 35.5, 2, 2, RED)
    c.poly([(28, 37), (35, 37), (31.5, 41)], RED)
    c.set(29, 35, WHITE)
    return c


def tex_shop():
    """Лавка: обои в розово-белую полоску, золотая рейка, под ней мятные панели с драже, на стене
    картина с тортом в карамельной раме."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px = x % 16
            col = VIOLET if px < 8 else WHITE
            if px == 7:
                col = PLUM
            if px == 15:
                col = GREY
            c.set(x, y, col)
    # Рейка и панели.
    c.rect(0, 30, T - 1, 33, GOLD)
    c.rect(0, 30, T - 1, 30, WHITE)
    c.rect(0, 33, T - 1, 33, BRASS)
    c.rect(0, 34, T - 1, 55, AQUA)
    c.rect(0, 34, T - 1, 34, METAL)
    for x in range(0, T, 16):
        c.rect(x, 35, x, 55, SEA)
        c.rect(x + 3, 38, x + 13, 52, SEA)
        c.rect(x + 4, 39, x + 13, 52, SKY)
        c.rect(x + 4, 39, x + 12, 51, AQUA)
        c.rect(x + 7, 44, x + 8, 45, (RED, GOLD, VIOLET, WHITE)[(x // 16) % 4])
        c.set(x + 9, 46, SEA)
        c.set(x + 8, 46, SEA)
    c.rect(0, 56, T - 1, T - 1, METAL)
    c.rect(0, 56, T - 1, 56, K)
    c.rect(0, 57, T - 1, 57, TAN)
    # Картина: торт на мятном фоне.
    c.rect(15, 4, 48, 26, K)
    c.rect(16, 5, 47, 25, GOLD)
    c.rect(16, 5, 47, 5, WHITE)
    c.rect(17, 24, 47, 25, BRASS)
    c.rect(19, 8, 44, 22, SKY)
    c.rect(19, 20, 44, 22, AQUA)
    c.rect(24, 15, 39, 20, SKIN)
    c.rect(24, 17, 39, 17, WHITE)
    c.rect(24, 13, 39, 15, VIOLET)
    for x in (25, 29, 33, 37):
        c.rect(x, 16, x, 16, VIOLET)
    c.rect(24, 20, 39, 20, TAN)
    c.rect(22, 21, 41, 21, WHITE)
    c.rect(31, 9, 32, 12, WHITE)
    c.set(31, 8, GOLD)
    c.set(32, 7, RED)
    c.set(26, 12, RED)
    c.set(37, 12, RED)
    return c


def tex_window():
    """Борт: пряничная кладка и круглое окно из леденца в кольце белой глазури с красными
    карамельками; за стеклом мятное небо, гора мороженого и облако ваты."""
    c = tex_ginger()
    c.ellipse(32, 30, 17, 17, K)
    c.ellipse(32, 30, 16, 16, WHITE)
    for y in range(12, 49):
        for x in range(14, 51):
            d = math.hypot(x - 32, y - 30)
            if 13.5 < d <= 16 and (y > 30 and x > 28 or x > 43):
                c.set(x, y, GREY)
    c.ellipse(32, 30, 12, 12, K)
    c.ellipse(32, 30, 11, 11, SKY)
    # Вид за стеклом, только внутри стекла.
    for y in range(19, 42):
        for x in range(21, 44):
            if c.get(x, y) != SKY:
                continue
            if y > 22 + (x - 21) * 0.2 and y < 27:
                pass
            # Гора: розовый шарик с белой шапкой и вафельный склон.
            dm = math.hypot(x - 37, y - 36)
            if dm <= 8:
                c.set(x, y, WHITE if y < 31 + (x % 3 == 0) else VIOLET)
            elif y >= 38 and x < 34:
                c.set(x, y, AQUA)
    for x, y in ((24, 26), (25, 25), (26, 25), (27, 26), (25, 26), (26, 26), (28, 26), (23, 27), (24, 27)):
        if c.get(x, y) == SKY:
            c.set(x, y, WHITE)
    for x, y in ((36, 35), (40, 37), (34, 38)):
        if c.get(x, y) == VIOLET:
            c.set(x, y, PLUM)
    # Блик леденца и карамельки на кольце.
    c.line(24, 29, 28, 22, WHITE, 1)
    c.line(26, 30, 28, 27, WHITE, 1)
    for a in range(0, 360, 45):
        x = 32 + 14 * math.cos(math.radians(a + 22))
        y = 30 + 14 * math.sin(math.radians(a + 22))
        c.rect(x - 0.5, y - 0.5, x + 0.5, y + 0.5, RED)
        c.set(x - 0.5, y - 0.5, VIOLET)
    return c


def tex_boxes():
    """Склад: штабель коробок конфет 32×32 со сдвигом ряда: розовые и мятные в белый горошек,
    золотая лента крестом, красный бант."""
    c = Canvas(T, T)
    for by in (0, 32):
        for bx in (0, 32):
            off = 16 if by == 32 else 0
            x0 = (bx + off) % T
            pink = (bx // 32 + by // 32) % 2 == 0
            body, dark, light = (VIOLET, PLUM, WHITE) if pink else (AQUA, SEA, SKY)
            for y in range(by, by + 32):
                for x in range(32):
                    py = y - by
                    col = body
                    if x in (0, 31) or py in (0, 31):
                        col = K
                    elif x == 30 or py == 30:
                        col = dark
                    elif x == 1 or py == 1:
                        col = light
                    elif py in (7, 8):
                        # Край крышки.
                        col = dark if py == 8 else body
                    elif (x % 8 == 4 and py % 8 == 4) or (x % 8 == 0 and py % 8 == 0):
                        col = WHITE
                    if 1 < x < 30 and 1 < py < 30:
                        if 14 <= x <= 17 or 16 <= py <= 19:
                            col = GOLD
                            if x == 17 or py == 19:
                                col = BRASS
                    c.set((x0 + x) % T, y, col)
            # Бант на перекрестье лент.
            for sign in (-1, 1):
                for i in range(1, 7):
                    hgt = min(i, 4)
                    for dy in range(-hgt, hgt + 1):
                        c.set((x0 + 15.5 + sign * (i + 0.5)) % T, by + 17 + dy, RED if dy < hgt else PLUM)
            for dx in (15, 16):
                for dy in (16, 17, 18):
                    c.set((x0 + dx) % T, by + dy, PLUM)
            c.set((x0 + 12) % T, by + 15, VIOLET if not pink else WHITE)
            c.set((x0 + 19) % T, by + 15, VIOLET if not pink else WHITE)
    return c


def tex_waffle():
    """Пол: вафля в клетку 16×16, рёбра светлые, ямки с тенью сверху слева, кое-где капля
    сиропа."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 16, y % 16
            if px < 4 or py < 4:
                col = GOLD
                if px == 0 or py == 0:
                    col = WHITE if (px == 0 and py < 4) or (py == 0 and px < 4) else GOLD
                if (px == 3 and py >= 3) or (py == 3 and px >= 3):
                    col = BRASS
            elif px in (4, 5) or py in (4, 5):
                col = METAL
            elif px == 15 or py == 15:
                col = GOLD
            else:
                col = BRASS
            c.set(x, y, col)
    for bx, by in ((16, 0), (48, 32), (0, 48)):
        c.rect(bx + 8, by + 8, bx + 12, by + 12, VIOLET)
        c.rect(bx + 8, by + 12, bx + 12, by + 12, PLUM)
        c.set(bx + 9, by + 9, WHITE)
    return c


def tex_floor_choco():
    """Пол погреба: плитка шоколада дольками 16×16 с фаской и вдавленным ромбом."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 16, y % 16
            d = abs(px - 8) + abs(py - 8)
            col = METAL
            if px == 0 or py == 0:
                col = K
            elif px == 1 or py == 1:
                col = TAN
            elif px == 15 or py == 15:
                col = DARK
            elif d == 4:
                col = DARK if (px + py) < 16 else TAN
            elif d < 4 and (x // 16 + y // 16) % 2 == 0:
                col = DARK
            c.set(x, y, col)
    return c


def tex_floor_glaze():
    """Пол лавки: розовая глазурь, белая решётка ромбами, в ромбах цветная посыпка."""
    rng = random.Random(305)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            d = abs((x % 16) - 8) + abs((y % 16) - 8)
            col = VIOLET
            if d == 8:
                col = WHITE
            elif d == 7:
                col = PLUM if (x % 16) + (y % 16) > 16 else VIOLET
            c.set(x, y, col)
    for by in range(0, T, 16):
        for bx in range(0, T, 16):
            for k in range(2):
                x, y = bx + rng.randint(5, 10), by + rng.randint(5, 10)
                col = SPRINKLES[rng.randrange(len(SPRINKLES))]
                dx, dy = ((1, 0), (0, 1), (1, 1))[rng.randrange(3)]
                c.set(x, y, col)
                c.set(x + dx, y + dy, col)
            c.set(bx, by, GOLD)
    return c


def tex_ceiling():
    """Потолок: тёмный шоколад, через 32 пикселя балка с бликом, на балках редкие розовые драже
    (без ярких полос, иначе в перспективе они расходятся лучами)."""
    rng = random.Random(306)
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
            c.rect(x, y, x + 1, y + 1, VIOLET)
    return c


# --- Мармеладные мишки -------------------------------------------------------------------------
# Литой мишка в рост человека: круглая голова с ушами, тело грушей, толстые лапы. Стрелок
# красный, с патронташем драже и трубочкой-плевалкой; рубака мятный, в белой повязке, с
# карамельной тростью. Блики белые сверху слева, просвет снизу справа, как у желе на свету.

def _striped(c, x0, y0, x1, y1, a, b, t=3, step=3.0):
    """Полосатая палочка: отрезок толщиной `t`, цвета чередуются через `step` пикселей."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    length = math.hypot(x1 - x0, y1 - y0)
    r = (t - 1) / 2.0
    for i in range(n + 1):
        k = i / n
        col = a if int(k * length / step) % 2 == 0 else b
        c.ellipse(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, r, r, col)


def _cane(c, x0, y0, x1, y1, r=4.0, flip=1):
    """Карамельная трость от конца `x0, y0` до сгиба `x1, y1`, крюк загнут в сторону `flip`."""
    _striped(c, x0, y0, x1, y1, WHITE, RED)
    n = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / n, (y1 - y0) / n
    nx, ny = -uy * flip, ux * flip
    ox, oy = x1 + nx * r, y1 + ny * r
    steps = 28
    for i in range(steps + 1):
        t = math.pi * i / steps
        x = ox + r * (-nx * math.cos(t) + ux * math.sin(t))
        y = oy + r * (-ny * math.cos(t) + uy * math.sin(t))
        c.ellipse(x, y, 1.0, 1.0, RED if (i // 5) % 2 == 0 else WHITE)


def _gloss(c, pts, col=WHITE, only=None):
    for x, y in pts:
        v = c.get(x, y)
        if v is not None and v != K and (only is None or v in only):
            c.set(x, y, col)


def _x_eyes(c, hx, y):
    for e in (-4, 4):
        c.line(hx + e - 1, y - 1, hx + e + 1, y + 1, K, 1)
        c.line(hx + e - 1, y + 1, hx + e + 1, y - 1, K, 1)


def bear(angle, phase, mode="walk", cane=False):
    """Мишка 64×64 в ракурсе `angle` (0 спереди … 4 со спины, лицом вправо на 1-3), шаг `phase`
    0/1. `mode`: walk, aim, fire, slash, die0..die2, hurt. `cane` рубака: мятный, в повязке, с
    тростью вместо трубочки. Ступни на 61-62 строке, ось по центру кадра, как у скелета пиратов."""
    c = Canvas(T, T)
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    body, dark, light = (SEA, NAVY, AQUA) if cane else (RED, PLUM, VIOLET)
    if mode.startswith("die"):
        k = int(mode[-1])
        if k == 0:
            return bear(0, 0, "hurt", cane)
        base = 62
        if k == 1:
            # Осел на пол: лапы вперёд подошвами к камере, голова набок, глаза крестиками.
            for sign in (-1, 1):
                c.line(cx + sign * 8, 34, cx + sign * 13, 46, dark if sign < 0 else body, 5)
            c.ellipse(cx, 49, 13, 11, body)
            for sign in (-1, 1):
                c.ellipse(cx + sign * 11, base - 5, 5.5, 5, body)
                c.ellipse(cx + sign * 11, base - 4, 3, 2.6, light)
            hx, hy = cx + 3, 30
            for sign in (-1, 1):
                c.ellipse(hx + sign * 8, hy - 8 + sign, 3.4, 3.4, body)
            c.ellipse(hx, hy, 10, 8.5, body)
            if cane:
                c.rect(hx - 9, hy - 6, hx + 9, hy - 4, WHITE)
            c.finish()
            c.ellipse(hx, hy + 4, 3.6, 2.4, light)
            c.rect(hx - 1, hy + 3, hx, hy + 3, K)
            _x_eyes(c, hx, hy - 1)
            _gloss(c, ((cx - 7, 42), (cx - 8, 43), (cx - 8, 44), (hx - 5, hy - 6), (hx - 4, hy - 7)), only=(body,))
        else:
            # Лежит на спине: пузо горкой, голова справа, задние лапы торчат вверх слева.
            for dx in (0, 7):
                c.line(cx - 15 + dx, base - 5, cx - 19 + dx, base - 14, dark if dx == 0 else body, 5)
                c.ellipse(cx - 19 + dx, base - 15, 3.4, 2.6, light)
            c.ellipse(cx - 3, base - 6, 17, 7, body)
            hx, hy = cx + 17, base - 8
            for sign in (-1, 1):
                c.ellipse(hx + sign * 6 + 2, hy - 7, 3, 3, body)
            c.ellipse(hx, hy, 9, 8, body)
            if cane:
                c.rect(hx - 8, hy - 6, hx + 8, hy - 4, WHITE)
            c.line(cx + 4, base - 6, cx + 2, base - 1, dark, 4)
            c.finish()
            c.ellipse(hx, hy + 3, 3.2, 2.2, light)
            c.rect(hx - 1, hy + 2, hx, hy + 2, K)
            _x_eyes(c, hx, hy - 2)
            _gloss(c, ((cx - 9, base - 11), (cx - 8, base - 11), (cx - 7, base - 12), (cx - 6, base - 12)), only=(body,))
        # Выпавшее оружие, на полу перед мишкой.
        drop = Canvas(T, T)
        if cane:
            _cane(drop, 10 if k == 1 else 6, base - 1, 28 if k == 1 else 22, base - 1, 3.0, -1)
        else:
            _striped(drop, 38, base - 1, 56, base - 1, WHITE, VIOLET)
        drop.outline()
        c.paste(drop, 0, 0)
        return c
    bob = 1 if phase else 0
    # Задние лапы: короткие и толстые, ступня-брусок с розовой подошвой.
    for sign in (-1, 1):
        swing = (sign * 3 if phase else -sign * 3) if mode == "walk" else 0
        col = dark if sign < 0 and (side or diag) else body
        hip = (cx + sign * (2 if side else 5), 44 - bob)
        foot = (cx + sign * (2 if side else 6) + swing * (1.4 if side else 0.4), 59)
        c.line(hip[0], hip[1], foot[0], foot[1], col, 7)
        toe = 2 if (side or diag) else 0
        c.rect(foot[0] - 4, 59, foot[0] + 4 + toe, 62, col)
    if back or side:
        # Хвостик.
        c.ellipse(cx - (9 if side else 0), 44 - bob, 2.6, 2.6, dark if back else body)
    # Тело грушей.
    w = 8 if side else (10 if diag else 11)
    if rod_far := (cane and not back):
        # Дальняя лапа рубаки за телом.
        c.line(cx - w + 2, 27 - bob, cx - w - 2, 38 - bob, dark, 5)
    c.ellipse(cx, 33 - bob, w - 1, 10, body)
    c.ellipse(cx, 39 - bob, w, 8.5, body)
    # Уши и голова.
    hx = cx + (2 if side else (1 if diag else 0))
    ears = ((-3, dark), (4, body)) if side else ((-8, body), (8, body))
    for dx, col in ears:
        c.ellipse(hx + dx, 6 - bob, 3.6, 3.6, col)
    c.ellipse(hx, 14 - bob, 10 if not side else 9, 8.5, body)
    if side:
        c.ellipse(hx + 8, 17 - bob, 4, 3.2, body)
    if cane:
        # Повязка по лбу, на затылке и сбоку хвосты.
        for y in range(8 - bob, 11 - bob):
            for x in range(hx - 11, hx + 12):
                if c.get(x, y) == body and ((x - hx) / 10.0) ** 2 + ((y - 14 + bob) / 8.5) ** 2 <= 1.0:
                    c.set(x, y, WHITE)
        if side:
            c.line(hx - 8, 10 - bob, hx - 13, 14 - bob, WHITE, 2)
            c.line(hx - 8, 10 - bob, hx - 12, 9 - bob, WHITE, 2)
        elif back:
            c.rect(hx - 1, 8 - bob, hx + 1, 10 - bob, GREY)
            c.line(hx - 1, 11 - bob, hx - 4, 17 - bob, WHITE, 2)
            c.line(hx + 1, 11 - bob, hx + 3, 18 - bob, WHITE, 2)
    elif not side:
        # Патронташ драже через плечо.
        sgn = -1 if back else 1
        c.line(cx - sgn * (w - 2), 27 - bob, cx + sgn * (w - 2), 41 - bob, GOLD, 3)
    # Передние лапы и оружие.
    face_marks = []
    if cane:
        up = mode == "slash"
        hx_ = cx + (11 if side or diag else 12)
        hy_ = (31 if not up else 17) - bob
        tip = (hx_ + (11 if side or diag else 4), (13 if not up else 6) - bob)
        tail = (hx_ - (5 if side or diag else 2), hy_ + 9)
        if back:
            c.line(cx - w + 1, 27 - bob, cx - w - 2, 38 - bob, body, 5)
        _cane(c, tail[0], tail[1], tip[0], tip[1], 4.0, 1 if not up else -1)
        c.line(cx + w - 3, 27 - bob, hx_, hy_, body, 5)
        c.ellipse(hx_, hy_, 3, 3, light)
    elif side or diag:
        if not back or mode in ("aim", "fire"):
            # Трубочка у рта, лапа поддерживает снизу.
            sy = 19 - bob
            _striped(c, hx + 9, sy, cx + 29, sy, WHITE, VIOLET)
            c.line(cx + 3, 28 - bob, cx + 15, 22 - bob, body, 5)
            c.ellipse(cx + 15, 22 - bob, 3, 2.6, light)
        else:
            # Вполоборота со спины: трубочка у плеча, виден её конец.
            _striped(c, cx + 8, 22 - bob, cx + 27, 16 - bob, WHITE, VIOLET)
            c.line(cx + 4, 28 - bob, cx + 13, 22 - bob, body, 5)
    elif not back:
        if mode in ("aim", "fire"):
            # Трубочка смотрит в камеру: кольцо у рта, обе лапы держат её.
            for sign in (-1, 1):
                c.line(cx + sign * 10, 27 - bob, cx + sign * 5, 22 - bob, body if sign > 0 else dark, 5)
            c.ellipse(cx, 20 - bob, 4.2, 4.2, WHITE)
            c.ellipse(cx, 20 - bob, 2.4, 2.4, K)
        else:
            # Трубочка стоймя в лапе у бока, как посох; вторая лапа висит.
            c.line(cx - 10, 27 - bob, cx - 13, 38 - bob, body, 5)
            _striped(c, cx + 15, 47 - bob, cx + 15, 9 - bob, WHITE, VIOLET)
            c.line(cx + 10, 27 - bob, cx + 15, 33 - bob, body, 5)
            c.ellipse(cx + 15, 33 - bob, 3, 2.6, light)
    else:
        # Со спины трубочка стоймя в той же лапе, с другой стороны кадра.
        _striped(c, cx - 15, 47 - bob, cx - 15, 9 - bob, WHITE, VIOLET)
        c.line(cx - 10, 27 - bob, cx - 15, 33 - bob, body, 5)
        c.line(cx + 10, 27 - bob, cx + 13, 38 - bob, body, 5)
    c.finish()
    # Патронташ: цветные драже на ремне.
    if not cane and not side:
        sgn = -1 if back else 1
        for i, col in enumerate((AQUA, WHITE, VIOLET, AQUA)):
            k = 0.14 + i * 0.24
            x = int(round(cx - sgn * (w - 2) + 2 * sgn * (w - 2) * k))
            y = int(round(27 - bob + 14 * k))
            if c.get(x, y) == GOLD or c.get(x, y) == BRASS:
                c.set(x, y, col)
    # Морда.
    if not back:
        if side:
            c.rect(hx + 4, 12 - bob, hx + 5, 14 - bob, K)
            c.set(hx + 5, 12 - bob, WHITE)
            c.line(hx + 2, 10 - bob, hx + 6, 11 - bob, K, 1)
            if c.get(hx + 11, 16 - bob) not in (None,):
                c.rect(hx + 10, 15 - bob, hx + 11, 16 - bob, K)
            if cane:
                c.line(hx + 6, 20 - bob, hx + 10, 19 - bob, K, 1)
        else:
            off = 1.5 if diag else 0
            mouth_free = cane or mode not in ("aim", "fire")
            if (mouth_free and not diag) or (diag and cane):
                c.ellipse(hx + off, 18 - bob, 4, 2.8, light)
                c.rect(hx + off - 1, 16 - bob, hx + off, 16 - bob, K)
                c.rect(hx + off - 1, 19 - bob, hx + off + 1, 19 - bob, K)
            for e in (-4, 4):
                ex = hx + e + off
                if mode == "hurt":
                    c.line(ex - 1, 12 - bob, ex + 1, 14 - bob, K, 1)
                    c.line(ex - 1, 14 - bob, ex + 1, 12 - bob, K, 1)
                    continue
                c.rect(ex - 1, 12 - bob, ex, 14 - bob, K)
                c.set(ex - 1, 12 - bob, WHITE)
                # Хмурые брови домиком.
                c.line(ex - (2 if e < 0 else -1), 9 - bob + (0 if e < 0 else 1), ex + (1 if e < 0 else -2),
                       9 - bob + (1 if e < 0 else 0), K, 1)
    else:
        # Затылок: шов литья посередине.
        c.line(hx, 8 - bob, hx, 12 - bob, dark, 1) if not cane else None
    # Блики желе и просвет.
    if side:
        _gloss(c, ((hx - 3, 9 - bob), (hx - 2, 8 - bob), (hx - 1, 8 - bob), (cx - 4, 30 - bob), (cx - 5, 31 - bob),
                   (cx - 5, 32 - bob)), only=(body,))
    else:
        _gloss(c, ((hx - 6, 10 - bob + (3 if cane else 0)), (hx - 5, 9 - bob + (3 if cane else 0)),
                   (cx - w + 3, 31 - bob), (cx - w + 2, 32 - bob), (cx - w + 2, 33 - bob)), only=(body,))
    _gloss(c, ((cx + w - 3, 42 - bob), (cx + w - 4, 43 - bob), (cx + w - 5, 44 - bob), (cx + w - 3, 41 - bob)),
           light, only=(body, dark))
    if mode == "fire":
        fx, fy = (cx + 30, 19 - bob) if side or diag else (cx, 20 - bob)
        c.ellipse(fx, fy, 5, 4, GOLD)
        c.ellipse(fx, fy, 2.5, 2, WHITE)
    if mode == "hurt":
        for x in range(T):
            for y in range(T):
                if c.get(x, y) in (body, dark) and (x + y) % 3 == 0:
                    c.set(x, y, WHITE)
    return c


def bear_strips():
    out = {}
    for name, cane in (("skel", False), ("cut", True)):
        walk = []
        for a in range(5):
            for ph in range(2):
                walk.append(bear(a, ph, "walk", cane))
        out[name + "_walk"] = strip(walk)
        out[name + "_die"] = strip([bear(0, 0, "die%d" % k, cane) for k in range(3)])
    out["skel_fire"] = strip([bear(0, 0, "aim"), bear(0, 0, "fire")])
    out["cut_slash"] = strip([bear(0, 0, "walk", True), bear(0, 0, "slash", True)])
    return out


# --- Предметы, оружие, лицо --------------------------------------------------------------------

def shot():
    """Выстрел мишки: красное драже в малиновой кромке с белым бликом, чтобы не путать с каплей
    крема героя."""
    c = Canvas(16, 16)
    c.ellipse(8, 8, 6, 6, PLUM)
    c.ellipse(8, 8, 4.5, 4.5, RED)
    c.ellipse(6.5, 6.5, 1.6, 1.6, WHITE)
    c.set(10, 10, VIOLET)
    c.set(9, 11, VIOLET)
    return c


def bullet():
    """Выстрел героя: капля белого крема с мятным хвостом и розовой верхушкой."""
    c = Canvas(16, 16)
    c.ellipse(8, 8, 3.5, 3.5, WHITE)
    c.ellipse(8, 11, 2, 2, AQUA)
    c.finish()
    c.set(7, 6, VIOLET)
    c.set(8, 6, VIOLET)
    c.set(7, 7, VIOLET)
    return c


def _jar(c, bx, by, jam):
    """Банка варенья: стекло с бликом, варенье на три четверти, крышка под тканью с завязкой."""
    c.rect(bx - 9, by - 17, bx + 9, by - 3, SKY)
    c.rect(bx - 8, by - 2, bx + 8, by, SKY)
    c.rect(bx - 9, by - 13, bx + 9, by - 3, jam)
    c.rect(bx - 8, by - 2, bx + 8, by, jam)
    c.rect(bx - 9, by - 14, bx + 9, by - 14, WHITE)
    c.rect(bx - 7, by - 19, bx + 7, by - 17, GREY)
    c.poly([(bx - 11, by - 19), (bx + 11, by - 19), (bx + 8, by - 24), (bx - 8, by - 24)], VIOLET)
    c.rect(bx - 11, by - 19, bx + 11, by - 19, PLUM)
    for x in range(bx - 7, bx + 8, 4):
        c.set(x, by - 22, WHITE)
    # Этикетка с ягодой.
    c.rect(bx - 5, by - 11, bx + 5, by - 5, WHITE)
    c.rect(bx - 1, by - 9, bx + 1, by - 7, jam)
    c.set(bx, by - 10, SEA)
    c.rect(bx - 8, by - 16, bx - 7, by - 6, WHITE)


def _sugar(c, x0, y0, w):
    """Кубик сахара: белая грань с крупинками, светлый верх, тень справа."""
    c.poly([(x0, y0 + 4), (x0 + 4, y0), (x0 + w + 4, y0), (x0 + w, y0 + 4)], SKY)
    c.poly([(x0 + w, y0 + 4), (x0 + w + 4, y0), (x0 + w + 4, y0 + 18), (x0 + w, y0 + 22)], GREY)
    c.rect(x0, y0 + 4, x0 + w, y0 + 22, WHITE)
    c.rect(x0, y0 + 4, x0 + w, y0 + 4, K)
    c.rect(x0 + w, y0 + 4, x0 + w, y0 + 22, K)
    c.line(x0 + w, y0 + 4, x0 + w + 4, y0, K, 1)
    for i in range(14):
        x = x0 + 2 + (i * 7) % (w - 3)
        y = y0 + 7 + (i * 5) % 14
        c.set(x, y, GREY)
        c.set(x + 1, y + 1, SKY)


def decor(kind):
    """Ориентир зала 64×64, низ на 62-63 строке: 0 банки варенья, 1 кубики сахара, 2 леденец-
    вертушка на палочке, 3 пушка с попкорном, 4 торт со свечой, 5 пончик на подставке."""
    c = Canvas(T, T)
    if kind == 0:
        _jar(c, 18, 62, RED)
        _jar(c, 45, 62, GOLD)
        _jar(c, 31, 39, PLUM)
    elif kind == 1:
        _sugar(c, 4, 40, 24)
        _sugar(c, 32, 40, 24)
        _sugar(c, 17, 20, 25)
    elif kind == 2:
        c.rect(30, 26, 33, 60, WHITE)
        c.rect(33, 26, 33, 60, GREY)
        c.ellipse(31.5, 60, 9, 3.4, METAL)
        c.rect(23, 60, 40, 62, METAL)
        for y in range(0, 32):
            for x in range(14, 50):
                d = math.hypot(x - 31.5, y - 15.5)
                if d > 14.2:
                    continue
                t = math.atan2(y - 15.5, x - 31.5) + d * 0.22
                red = int(math.floor(t / (math.pi / 3.0))) % 2 == 0
                c.set(x, y, RED if red else WHITE)
        # Бант под леденцом.
        c.poly([(31, 32), (23, 29), (23, 36)], VIOLET)
        c.poly([(32, 32), (40, 29), (40, 36)], VIOLET)
        c.rect(30, 31, 33, 34, PLUM)
    elif kind == 3:
        # Пушка с попкорном: ствол в красно-белую полосу на лафете с колёсами-печеньем.
        for y in range(18, 52):
            for x in range(14, 58):
                u = (x - 20) * 0.894 - (y - 44) * 0.447
                v = (x - 20) * 0.447 + (y - 44) * 0.894
                if 0 <= u <= 36 and abs(v) <= 8 - u * 0.04:
                    c.set(x, y, RED if int(u // 6) % 2 == 0 else WHITE)
        c.ellipse(20, 44, 8, 8, RED)
        c.ellipse(52.5, 27.5, 3.4, 6.4, DARK)
        c.rect(14, 48, 44, 54, METAL)
        c.rect(14, 48, 44, 48, TAN)
        for wx in (19, 40):
            c.ellipse(wx, 55, 7, 7, GOLD)
            c.ellipse(wx, 55, 5, 5, BRASS)
            for dx, dy in ((-2, -2), (2, -1), (0, 2), (-3, 1)):
                c.set(wx + dx, 55 + dy, DARK)
        for px, py, r in ((57, 19, 3.2), (60, 13, 2.6), (54, 12, 2.8), (61, 23, 2.0)):
            c.ellipse(px, py, r, r, WHITE)
            c.ellipse(px + 1, py + 1, r * 0.45, r * 0.45, GOLD)
    elif kind == 4:
        # Торт в два яруса: бисквит, крем, розовая глазурь с потёками, вишни, свеча.
        c.ellipse(32, 60, 26, 2.6, GREY)
        for x0, x1, y0, y1 in ((9, 54, 40, 59), (17, 46, 24, 40)):
            c.rect(x0, y0, x1, y1, SKIN)
            mid = (y0 + y1) // 2 + 2
            c.rect(x0, mid, x1, mid + 1, WHITE)
            c.rect(x0, y0, x1, y0 + 4, VIOLET)
            for x in range(x0, x1 + 1):
                d = int(round(1.6 + 1.6 * math.sin((x - x0) * 0.9)))
                c.rect(x, y0 + 4, x, y0 + 4 + d, VIOLET)
            c.rect(x0 + 2, y0 + 1, x1 - 6, y0 + 1, WHITE)
            for x in range(x0 + 4, x1 - 2, 8):
                c.ellipse(x, y0 - 1, 2.2, 2.2, RED)
        c.rect(30, 9, 33, 23, WHITE)
        for y in range(11, 23, 4):
            c.rect(30, y, 33, y + 1, RED)
        c.ellipse(31.5, 4.5, 2.4, 3.6, GOLD)
    else:
        # Пончик стоймя на шоколадной подставке: тесто, розовая глазурь волной, посыпка.
        c.rect(29, 44, 34, 60, METAL)
        c.ellipse(31.5, 60, 11, 3, METAL)
        c.rect(21, 60, 42, 62, METAL)
        for y in range(2, 50):
            for x in range(8, 56):
                d = math.hypot(x - 31.5, y - 25)
                if d > 21 or d < 6.5:
                    continue
                a = math.atan2(y - 25, x - 31.5)
                edge = 17.6 + 1.6 * math.sin(a * 7)
                inner = 9.4 + 0.8 * math.sin(a * 5)
                c.set(x, y, VIOLET if inner < d < edge else GOLD)
    c.finish()
    # Мелочи поверх обводки.
    if kind == 2:
        c.line(24, 8, 27, 5, SKY, 1)
    elif kind == 4:
        c.set(31, 4, WHITE)
        c.set(31, 5, WHITE)
        for x in (13, 21, 29, 37, 45, 21 + 0, 29 + 8):
            if c.get(x, 39) == RED:
                c.set(x - 1, 38, WHITE)
    elif kind == 5:
        rng = random.Random(315)
        n = 0
        while n < 16:
            a = rng.random() * math.tau
            d = rng.uniform(11.0, 15.5)
            x, y = int(31.5 + d * math.cos(a)), int(25 + d * math.sin(a))
            if c.get(x, y) == VIOLET and c.get(x + 1, y) == VIOLET and c.get(x, y + 1) == VIOLET:
                col = (AQUA, WHITE, GOLD, RED)[n % 4]
                c.set(x, y, col)
                c.set(x + (1 if n % 2 else 0), y + (0 if n % 2 else 1), col)
                n += 1
        for a in (3.5, 3.7, 3.9, 4.1):
            x, y = int(31.5 + 16 * math.cos(a)), int(25 + 16 * math.sin(a))
            if c.get(x, y) == VIOLET:
                c.set(x, y, WHITE)
    return c


def key():
    """Ключ: карамельный бублик в розовой глазури с посыпкой, тот же, что в основе набора."""
    return sweets16.key()


def medkit():
    """Аптечка: капкейк в белой формочке с красным крестом, тот же, что в основе набора."""
    return sweets16.cupcake()


def pistol(frame):
    """Кондитерский шприц в руке снизу по центру, 128×96: пряничная рука с каймой глазури,
    шприц стволом вглубь (ось x=64, насадка у верхнего края): колба с розовым кремом, белые
    кольца, упор под пальцы, золотая насадка-звёздочка; кадр 1 с брызгом крема."""
    c = Canvas(128, 96)
    # Рука: пряник, расширяется книзу, по краям тень, кайма глазури зигзагом и пуговица-драже.
    for y in range(60, 96):
        w = 14 + (y - 60) // 5
        for x in range(64 - w, 64 + w):
            col = SKIN
            if x >= 64 + w - 4:
                col = TAN
            elif x == 64 - w + 2 and y > 66:
                col = GOLD
            c.set(x, y, col)
    for x in range(64 - 15, 64 + 15):
        zy = 68 + (abs((x % 8) - 4) - 2)
        c.rect(x, zy, x, zy + 2, WHITE)
        c.set(x, zy + 3, TAN)
    c.ellipse(64, 84, 3.4, 3.4, AQUA)
    c.ellipse(63, 83, 1.2, 1.2, SKY)
    # Упор под пальцы: белая перекладина за варежкой.
    c.rect(44, 41, 84, 45, WHITE)
    c.rect(44, 45, 84, 45, GREY)
    c.rect(44, 41, 45, 45, GREY)
    c.rect(83, 41, 84, 45, GREY)
    # Колба: прозрачная, внутри розовый крем, мерные риски.
    for y in range(15, 42):
        w = 9 + (y - 15) // 9
        for x in range(64 - w, 64 + w + 1):
            dx = x - 64
            col = VIOLET
            if dx <= -w + 1:
                col = SKY
            elif dx == -w + 2 or dx == -w + 3:
                col = WHITE
            elif dx >= w - 2:
                col = PLUM
            if y < 20 and col in (VIOLET, PLUM):
                col = SKY if col == VIOLET else AQUA
            c.set(x, y, col)
    c.rect(55, 20, 73, 20, PLUM)
    for y in (24, 29, 34, 39):
        c.rect(67, y, 71 if y % 10 == 4 else 69, y, K)
    # Кольца: у насадки и у упора.
    c.rect(53, 12, 75, 15, WHITE)
    c.rect(53, 15, 75, 15, GREY)
    c.rect(72, 12, 75, 15, GREY)
    c.rect(52, 38, 76, 41, WHITE)
    c.rect(73, 38, 76, 41, GREY)
    # Насадка: золотой конус с рёбрами, на кончике капля крема.
    c.poly([(57, 12), (71, 12), (66, 3), (62, 3)], GOLD)
    for x0, x1 in ((59, 62.6), (64, 64), (69, 65.6)):
        c.line(x0, 11, x1, 4, BRASS, 1)
    c.line(58, 11, 62, 4, WHITE, 1)
    c.ellipse(64, 2.5, 2.6, 1.8, WHITE)
    # Варежка: круглая пряничная кисть обхватывает колбу под упором, большой палец слева.
    c.ellipse(64, 53, 16, 10, SKIN)
    c.ellipse(47, 50, 4.5, 6.5, SKIN)
    for y in range(44, 64):
        for x in range(70, 81):
            if c.get(x, y) == SKIN and ((x - 60) / 16.0) ** 2 + ((y - 51) / 10.0) ** 2 > 1.0:
                c.set(x, y, TAN)
    c.line(52, 47, 50, 55, TAN, 1)
    for x in (58, 65, 72):
        c.line(x, 45, x + 1, 50, TAN, 1)
    c.line(52, 61, 76, 61, TAN, 1)
    c.finish()
    c.set(63, 2, SKY)
    c.line(54, 46, 57, 45, GOLD, 1)
    if frame:
        # Брызг крема: розовая клякса с белой серединой и каплями в стороны.
        c.ellipse(64, 0, 18, 10, VIOLET)
        c.ellipse(64, 0, 10, 6, WHITE)
        for x, y in ((43, 4), (86, 5), (50, 12), (78, 13), (64, 14)):
            c.ellipse(x, y, 1.6, 1.6, VIOLET)
    return c


def face(mode):
    """Лицо пряничного человечка для HUD, 32×32: круглая голова, чёлка глазурью, румянец,
    красный бантик; 0 прямо, 1 глянул влево, 2 вправо, 3 больно (откушен край, крошки), 4
    ухмылка."""
    c = Canvas(32, 32)
    c.ellipse(15.5, 13, 13, 12, SKIN)
    if mode == 3:
        # Откушенный край: две дуги зубов.
        c.ellipse(27, 5, 4.2, 4.2, None)
        c.ellipse(29, 10, 3, 3, None)
    # Бантик под подбородком.
    c.poly([(15, 27), (9, 24), (9, 30)], RED)
    c.poly([(16, 27), (22, 24), (22, 30)], RED)
    c.rect(14, 25, 17, 29, RED)
    c.finish()
    c.rect(13, 26, 13, 28, K)
    c.rect(18, 26, 18, 28, K)
    c.set(15, 26, VIOLET)
    # Чёлка: волна глазури по макушке.
    for x in range(5, 27):
        y = 3 + (1 if x % 6 in (2, 3, 4) else 0) + (1 if x % 6 == 3 else 0)
        for dy in (0, 1):
            if c.get(x, y + dy) in (SKIN, TAN):
                c.set(x, y + dy, WHITE)
    look = {0: 0, 1: -2, 2: 2, 3: 0, 4: 0}[mode]
    for e in (-5, 5):
        ex = 15.5 + e
        if mode == 3:
            c.line(ex - 1.5, 12, ex + 1.5, 15, K, 1)
            c.line(ex - 1.5, 15, ex + 1.5, 12, K, 1)
        else:
            c.rect(ex - 1.5, 11, ex + 1.5, 15, WHITE)
            c.rect(ex + look - 0.5, 12, ex + look + 0.5, 15, K)
        # Румянец.
        c.rect(15.5 + e * 1.7 - 1, 17, 15.5 + e * 1.7 + 0.5, 18, VIOLET)
    if mode == 4:
        c.rect(10, 19, 21, 22, K)
        c.rect(11, 20, 20, 21, WHITE)
        c.set(9, 18, K)
        c.set(22, 18, K)
        for x in (13, 16, 19):
            c.set(x, 21, GREY)
    elif mode == 3:
        c.ellipse(15.5, 21, 3.4, 2.4, K)
        c.rect(14, 22, 17, 22, RED)
        for x, y in ((29, 3), (30, 7), (27, 1)):
            c.set(x, y, TAN)
    else:
        # Улыбка глазурью.
        c.rect(11, 21, 20, 21, WHITE)
        c.set(10, 20, WHITE)
        c.set(21, 20, WHITE)
        c.set(9, 19, WHITE)
        c.set(22, 19, WHITE)
    return c


def textures():
    return {"wall_planks": tex_ginger(), "wall_stone": tex_choco(), "wall_pillar": tex_cane(),
            "wall_exit": tex_exit(), "wall_cabin": tex_shop(), "wall_hull": tex_window(), "wall_cargo": tex_boxes(),
            "floor_planks": tex_waffle(), "floor_stone": tex_floor_choco(), "floor_carpet": tex_floor_glaze(),
            "ceiling_beams": tex_ceiling()}


def sprites():
    out = {"shot": shot(), "bullet": bullet(), "key": key(), "medkit": medkit(),
           "hold_decor": strip([decor(k) for k in range(6)]),
           "pistol": strip([pistol(0), pistol(1)]),
           "face": strip([face(i) for i in range(5)])}
    out.update(bear_strips())
    out.update(textures())
    return out


if __name__ == "__main__":
    if "--preview" in sys.argv:
        sweets16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sweets16.shaded(sprites()))
