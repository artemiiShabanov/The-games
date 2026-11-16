#!/usr/bin/env python3
"""Набор «Динозавры» для шутера × 16/32-bit «до выхода» (#144), зеркало `space_hold16.py` и
`pixel_hold16.py`: те же ключи, размеры холстов, число и порядок кадров и точки опоры (ноги
врагов на 61-62 строке по центру кадра, рогатка рожками вверх по оси 64, камень в коже у
верхнего края, текстуры 64×64 со швом по краю).

Тема: пещеры и лавовые ходы под вулканом, логово рапторов. Стены: пласты красной глины с
окаменелостями, базальтовые столбы с жилами лавы, ствол саговника в верёвочной обвязке,
выход: ворота из брёвен в раме из бивней с костяным замком, жилище вождя из натянутой шкуры с
наскальной росписью, пролом с видом на вулкан, кладовая плетёных корзин. Полы: растрескавшаяся
глина, плиты лавового камня с тлеющими трещинами, циновка из папоротника. Враги: прямоходящий
раптор, плюётся сгустком лавы (`skel_*`), и бородатый дикарь с каменной дубиной (`cut_*`).
Рогатка в голой руке героя с костяным браслетом, камень, костяной ключ и окорок из основы,
лицо пещерного человека.

    python3 tools/dinosaurs_hold16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dinosaurs16  # noqa: E402
from dinosaurs16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS,  # noqa: E402
                         METAL, DARK, RED, VIOLET, PLUM)

T = 64


# --- Текстуры ----------------------------------------------------------------------------------

def _cells(seed, count):
    """Ячейки Вороного на торе 64×64: для каждого пикселя (номер ближайшего зерна, зазор до
    второго, смещение от зерна). Трещины и швы плит получаются бесшовными по обоим краям."""
    rng = random.Random(seed)
    # Зёрна не ближе шага друг к другу, иначе ячейки слипаются в тёмные клинья.
    gap_min = 0.62 * T / math.sqrt(count)
    pts = []
    while len(pts) < count:
        p = (rng.uniform(0, T), rng.uniform(0, T))
        if all(math.hypot((p[0] - q[0] + T / 2) % T - T / 2, (p[1] - q[1] + T / 2) % T - T / 2) >= gap_min for q in pts):
            pts.append(p)
    out = {}
    for y in range(T):
        for x in range(T):
            best = []
            for i, (px, py) in enumerate(pts):
                dx = (x - px + T / 2) % T - T / 2
                dy = (y - py + T / 2) % T - T / 2
                best.append((math.hypot(dx, dy), i, dx, dy))
            best.sort()
            out[(x, y)] = (best[0][1], best[1][0] - best[0][0], best[0][2], best[0][3], best[1][1])
    return out


def _ammonite(c, cx, cy, r, shell, dark):
    """Окаменелый аммонит: диск и спираль завитка."""
    c.ellipse(cx, cy, r, r, shell)
    a = 0.0
    while a < math.tau * 2.2:
        rr = r * (1.0 - a / (math.tau * 2.6))
        c.set(cx + math.cos(a) * rr, cy + math.sin(a) * rr, dark)
        a += 0.18
    c.set(cx, cy, dark)


def tex_clay():
    """Основная стена: пласты красной глины с волнистыми границами, галька, в пластах аммонит,
    ребро и позвонки, снизу тёмная осыпь."""
    rng = random.Random(301)
    c = Canvas(T, T)
    bounds = [(7, 2, 1, 0.0), (17, 3, 2, 1.3), (26, 2, 1, 2.2), (38, 3, 2, 0.6), (49, 2, 3, 4.0)]
    for x in range(T):
        ys = [b + a * math.sin(x * math.tau * k / T + ph) for b, a, k, ph in bounds]
        for y in range(T):
            band = sum(1 for v in ys if y > v)
            col = (TAN, TAN, DARK, TAN, TAN, DARK)[band]
            for v in ys:
                if int(round(v)) == y:
                    col = DARK
                elif int(round(v)) + 1 == y and band in (1, 4):
                    col = SKIN
            if col == TAN and band in (0, 3) and (x * 7 + y * 13) % 11 == 0:
                col = RED
            c.set(x, y, col)
    # Галька и рытвины.
    for _ in range(26):
        x, y = rng.randrange(T), rng.randrange(4, 56)
        if c.get(x, y) == TAN:
            c.set(x, y, DARK)
            c.set((x + 1) % T, y, SKIN)
    for _ in range(7):
        x, y = rng.randrange(2, T - 3), rng.randrange(4, 54)
        c.rect(x, y, x + 1, y + 1, METAL)
        c.set(x, y, GREY)
    # Окаменелости: аммонит, ребро дугой, цепочка позвонков.
    _ammonite(c, 15, 30, 5, GOLD, BRASS)
    for i in range(14):
        a = math.pi * (1.1 + 0.8 * i / 13.0)
        c.set(46 + math.cos(a) * 9, 22 + math.sin(a) * 6, WHITE)
        c.set(46 + math.cos(a) * 9, 23 + math.sin(a) * 6, GREY)
    for i in range(5):
        c.rect(36 + i * 4, 43, 37 + i * 4, 44, WHITE)
        c.set(37 + i * 4, 45, GREY)
    # Осыпь у пола.
    for x in range(T):
        top = 58 + (1 if (x * 5) % 7 < 3 else 0)
        c.rect(x, top, x, T - 1, DARK)
        c.set(x, top, K if x % 9 == 4 else DARK)
    for x in range(3, T, 9):
        c.rect(x, 60, x + 2, 61, METAL)
        c.set(x, 60, GREY)
    return c


def tex_basalt():
    """Лавовый ход: базальтовые столбы со сдвинутыми поперечными сколами, по ним жилы лавы с
    жёлтой сердцевиной."""
    rng = random.Random(302)
    c = Canvas(T, T)
    for x in range(T):
        px, col_i = x % 8, x // 8
        for y in range(T):
            py = (y + col_i * 11) % 20
            col = METAL
            if px == 0:
                col = K
            elif px == 1:
                col = GREY
            elif px >= 6:
                col = DARK
            if py == 0 and px:
                col = K
            elif py == 1 and 1 < px < 6:
                col = GREY
            c.set(x, y, col)
    for _ in range(30):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == METAL:
            c.set(x, y, DARK)
    # Жилы лавы: синусоиды, замкнутые по горизонтали.
    for y0, amp, ph in ((14, 5, 0.4), (40, 6, 2.6)):
        for x in range(T):
            y = y0 + amp * math.sin(x * math.tau / 32.0 + ph) + 2.5 * math.sin(x * math.tau * 3 / 64.0 + ph * 2)
            yy = int(round(y))
            c.set(x, (yy - 1) % T, TAN)
            c.set(x, yy % T, RED)
            c.set(x, (yy + 1) % T, GOLD if x % 5 else SKY)
            c.set(x, (yy + 2) % T, RED)
            c.set(x, (yy + 3) % T, TAN)
    # Капли, отошедшие от жил.
    for x, y in ((9, 26), (29, 5), (51, 27), (22, 52), (44, 56)):
        c.rect(x, y, x + 1, y + 2, RED)
        c.set(x, y + 1, GOLD)
    return c


def tex_trunk():
    """Колонна: ствол саговника в ромбах листовых рубцов, две верёвочные обвязки с клыками,
    по стволу лиана."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            u, v = (x + y) % 8, (x - y) % 8
            col = BRASS
            if u == 0 or v == 0:
                col = DARK
            elif u == 1 and v == 1:
                col = K
            elif u == 1 or v == 1:
                col = GOLD if (x % 16) < 6 else BRASS
            if x % 16 >= 12 and col == BRASS:
                col = TAN
            c.set(x, y, col)
    # Лиана с листьями, период 64 по вертикали.
    for y in range(T):
        x = 37 + 3 * math.sin(y * math.tau / 32.0)
        c.set(x, y, PLUM)
        c.set(x + 1, y, VIOLET)
        if y % 11 == 3:
            c.poly([(x + 2, y), (x + 7, y - 2), (x + 6, y + 2)], VIOLET)
            c.set(x + 4, y, PLUM)
        if y % 11 == 8:
            c.poly([(x - 1, y), (x - 6, y - 2), (x - 5, y + 2)], VIOLET)
            c.set(x - 3, y, PLUM)
    # Обвязки: витая верёвка, под ней клыки.
    for y in (10, 46):
        c.rect(0, y, T - 1, y + 4, GOLD)
        c.rect(0, y, T - 1, y, SKY)
        c.rect(0, y + 4, T - 1, y + 4, K)
        for x in range(T):
            if x % 4 == 0:
                c.set(x, y + 1, BRASS)
                c.set(x + 1, y + 2, BRASS)
                c.set(x + 2, y + 3, BRASS)
        for x in range(5, T, 10):
            c.poly([(x - 1, y + 5), (x + 1, y + 5), (x, y + 10)], WHITE)
            c.set(x + 1, y + 6, GREY)
    return c


def tex_exit():
    """Выход: ворота из вертикальных брёвен на двух верёвках, по бокам бивни мамонта, сверху
    перекладина с зубцами клыков, на брёвнах бирюзовые стрелки вверх, посередине костяной
    замок со скважиной под ключ."""
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, DARK)
    # Брёвна.
    for x in range(8, 56):
        px = (x - 8) % 8
        col = BRASS
        if px == 0:
            col = K
        elif px == 1:
            col = GOLD
        elif px >= 6:
            col = DARK
        for y in range(10, 62):
            cc = col
            if col == BRASS and (y * 3 + (x // 8) * 7) % 17 == 0:
                cc = DARK
            c.set(x, y, cc)
        c.set(x, 10, K)
    c.rect(31, 10, 32, 61, K)
    # Земля под воротами.
    c.rect(0, 62, T - 1, T - 1, K)
    # Верёвки.
    for y in (18, 52):
        c.rect(8, y, 55, y + 2, GOLD)
        c.rect(8, y + 2, 55, y + 2, DARK)
        for x in range(8, 56, 3):
            c.set(x, y + 1, BRASS)
    # Перекладина: тёмный камень, зубцы клыков вниз.
    c.rect(0, 0, T - 1, 8, METAL)
    c.rect(0, 0, T - 1, 0, GREY)
    c.rect(0, 8, T - 1, 8, K)
    for x in range(0, T, 8):
        c.poly([(x + 1, 2), (x + 6, 2), (x + 3.5, 8)], WHITE)
        c.set(x + 5, 3, GREY)
        c.set(x + 4, 5, GREY)
    # Бивни: дуги от пола к перекладине, остриём внутрь.
    for sign, bx in ((1, 3), (-1, 60)):
        for i in range(60):
            k = i / 59.0
            y = 61 - k * 50
            x = bx + sign * (4.5 * math.sin(k * math.pi * 0.9) + 2.0 * k * k)
            w = 3.2 * (1.0 - k) + 0.8
            c.rect(x - w / 2 if sign > 0 else x - w / 2, y, x + w / 2, y, WHITE)
            c.set(x + sign * w / 2, y, GREY)
            c.set(x - sign * (w / 2 + 1), y, K)
    # Стрелки.
    for cx in (19, 44):
        c.poly([(cx - 6, 40), (cx + 6, 40), (cx, 28)], AQUA)
        c.rect(cx - 2, 40, cx + 2, 48, AQUA)
        c.set(cx, 30, SKY)
        c.rect(cx - 2, 48, cx + 2, 48, SEA)
    # Замок: костяная пластина со скважиной, оранжевая обмотка как на ключе.
    c.rect(26, 31, 37, 42, K)
    c.rect(27, 32, 36, 41, WHITE)
    c.rect(27, 41, 36, 41, GREY)
    c.rect(36, 32, 36, 41, GREY)
    c.ellipse(31.5, 35.5, 1.6, 1.6, K)
    c.rect(31, 36, 32, 39, K)
    c.rect(27, 32, 36, 33, RED)
    return c


def tex_hide():
    """Жилище вождя: светлая шкура, пришитая к жердям, роспись охрой: мамонт, охотники с
    копьями, отпечатки ладоней, солнце-спираль."""
    rng = random.Random(305)
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, GREY)
    for _ in range(90):
        x, y = rng.randrange(T), rng.randrange(T)
        c.set(x, y, SKY if rng.random() < 0.6 else METAL)
    # Жерди по краям и перекладина сверху, стежки шнура.
    for x in (0, 1, 2, 61, 62, 63):
        c.rect(x, 0, x, T - 1, BRASS if x in (1, 62) else DARK)
    c.rect(0, 0, T - 1, 3, BRASS)
    c.rect(0, 0, T - 1, 0, GOLD)
    c.rect(0, 3, T - 1, 3, K)
    for y in range(7, 56, 6):
        c.rect(3, y, 5, y, DARK)
        c.rect(58, y, 60, y, DARK)
    for x in range(6, 60, 6):
        c.rect(x, 4, x, 6, DARK)
    # Мамонт.
    c.ellipse(24, 28, 9, 6, TAN)
    c.ellipse(15, 25, 5, 5, TAN)
    c.rect(18, 32, 20, 38, TAN)
    c.rect(28, 32, 30, 38, TAN)
    c.line(12, 28, 10, 35, TAN, 2)
    c.line(13, 29, 8, 30, DARK, 1)
    c.line(8, 30, 7, 27, DARK, 1)
    c.set(14, 24, DARK)
    c.line(21, 22, 29, 23, DARK, 1)
    # Охотники с копьями.
    for hx in (40, 50):
        c.ellipse(hx, 22, 1.5, 1.5, DARK)
        c.line(hx, 24, hx, 31, DARK, 1)
        c.line(hx, 31, hx - 2, 37, DARK, 1)
        c.line(hx, 31, hx + 2, 37, DARK, 1)
        c.line(hx, 26, hx - 4, 23, DARK, 1)
        c.line(hx - 7, 26, hx + 1, 18, RED, 1)
    # Солнце-спираль и ладони.
    a = 0.0
    while a < math.tau * 2:
        r = 1 + a * 0.55
        c.set(47 + math.cos(a) * r, 11 + math.sin(a) * r, RED)
        a += 0.2
    for hx, hy in ((12, 47), (24, 49), (52, 47)):
        c.rect(hx, hy, hx + 4, hy + 4, RED)
        for k in range(4):
            c.rect(hx + k + (1 if k > 1 else 0) - 1, hy - 3, hx + k + (1 if k > 1 else 0) - 1, hy - 1, RED if k % 2 == 0 else GREY)
        c.set(hx - 2, hy + 2, RED)
        c.set(hx - 1, hy + 2, RED)
    # Низ: бахрома шкуры и тёмный вал глины.
    for x in range(3, 61):
        if x % 3 != 0:
            c.rect(x, 55, x, 56 + (x % 2), METAL)
    c.rect(0, 58, T - 1, T - 1, DARK)
    c.rect(0, 58, T - 1, 58, K)
    for x in range(2, T, 7):
        c.rect(x, 60, x + 2, 61, TAN)
    return c


def tex_gap():
    """Пролом: глиняная стена, в ней круглая дыра в ободе камней, за ней небо, дымящий вулкан
    с потёком лавы и кромка джунглей."""
    c = tex_clay()
    cx, cy = 32, 27
    c.ellipse(cx, cy, 17, 17, K)
    # Обод из камней.
    for i in range(14):
        a = math.tau * i / 14.0
        x, y = cx + math.cos(a) * 14.5, cy + math.sin(a) * 14.5
        c.ellipse(x, y, 3.2, 3.2, METAL if i % 3 else DARK)
        c.set(x - 1, y - 1, GREY)
    c.ellipse(cx, cy, 11.5, 11.5, AQUA)
    inside = [(x, y) for y in range(cy - 12, cy + 13) for x in range(cx - 12, cx + 13) if c.get(x, y) == AQUA]
    for x, y in inside:
        col = AQUA
        if y < cy - 6:
            col = SEA
        elif y > cy + 1:
            col = SKY
        # Вулкан: трапеция с кратером.
        h = cy + 8 - y
        if 0 <= h <= 14 and abs(x - (cx + 2)) <= 2 + (14 - h) * 0.7:
            col = METAL if x - (cx + 2) < (14 - h) * 0.2 else DARK
            if h >= 13:
                col = RED
            if x == cx + 3 and 6 <= h < 13:
                col = RED if h % 3 else GOLD
        if y >= cy + 8:
            col = PLUM
        elif y == cy + 7 and (x * 3) % 5 < 3:
            col = PLUM
        c.set(x, y, col)
    # Дым из кратера.
    for x, y, r in ((cx + 2, cy - 8, 2.2), (cx, cy - 10, 1.6)):
        for yy in range(int(y - r), int(y + r) + 1):
            for xx in range(int(x - r), int(x + r) + 1):
                if (xx, yy) in set(inside) and (xx - x) ** 2 + (yy - y) ** 2 <= r * r:
                    c.set(xx, yy, GREY)
    return c


def _basket(c, x0, y0, w, h, wrap=True):
    """Плетёная стенка: лоза внахлёст через прут, обод сверху и снизу."""
    for y in range(h):
        for x in range(w):
            xx = (x0 + x) % T if wrap else x0 + x
            edge = x in (0, w - 1) or y in (0, h - 1)
            if edge:
                col = K if (y in (0, h - 1) and x in (0, w - 1)) else DARK
            elif y in (1, 2):
                col = GOLD if y == 1 else BRASS
            elif y == h - 2:
                col = DARK
            else:
                over = ((x // 4) + (y // 3)) % 2 == 0
                col = GOLD if over else BRASS
                if x % 4 == 3:
                    col = DARK
                elif y % 3 == 2 and over:
                    col = BRASS
            c.set(xx, y0 + y, col)


def tex_baskets():
    """Кладовая: штабель плетёных корзин 32×32 со сдвигом ряда, на каждой охрой знак: ладонь
    или аммонит, из щели торчит лист папоротника."""
    c = Canvas(T, T)
    for by in (0, 32):
        for bx in (0, 32):
            x0 = (bx + (16 if by else 0)) % T
            _basket(c, x0, by, 32, 32)
            # Знак на светлой заплате шкуры.
            for x in range(10, 22):
                for y in range(by + 11, by + 21):
                    c.set((x0 + x) % T, y, GREY if y not in (by + 11, by + 20) and x not in (10, 21) else DARK)
            if (bx // 32 + by // 32) % 2 == 0:
                for i in range(14):
                    a = i * 0.55
                    r = 0.6 + i * 0.27
                    c.set((x0 + 16 + int(round(math.cos(a) * r))) % T, by + 16 + int(round(math.sin(a) * r)), RED)
            else:
                for x in range(13, 19):
                    for y in range(by + 15, by + 19):
                        c.set((x0 + x) % T, y, RED)
                for x in (13, 15, 17):
                    c.set((x0 + x) % T, by + 13, RED)
                    c.set((x0 + x) % T, by + 14, RED)
            for k in range(4):
                c.set((x0 + 26 + k) % T, by + 6 - k, VIOLET)
                c.set((x0 + 26 + k) % T, by + 7 - k, PLUM)
    return c


def tex_floor_clay():
    """Пол: растрескавшаяся красная глина, плитки-чешуи со светлым краем, галька."""
    rng = random.Random(307)
    cells = _cells(307, 22)
    c = Canvas(T, T)
    for (x, y), (i, gap, dx, dy, _j) in cells.items():
        col = TAN
        if gap < 1.2:
            col = DARK
        elif gap < 2.2 and dx + dy > 0:
            col = SKIN
        elif (i + x * 3 + y * 5) % 13 == 0:
            col = RED
        c.set(x, y, col)
    for _ in range(12):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == TAN:
            c.set(x, y, METAL)
            c.set((x + 1) % T, y, GREY)
    return c


def tex_floor_lava():
    """Пол лавового хода: плиты тёмного камня, часть трещин между ними тлеет."""
    cells = _cells(308, 12)
    c = Canvas(T, T)
    for (x, y), (i, gap, dx, dy, j) in cells.items():
        col = METAL
        if gap < 1.6:
            hot = (i + j) % 3 == 0
            col = (GOLD if gap < 0.6 else RED) if hot else K
        elif gap < 3.2:
            col = GREY if dx + dy > 0 else DARK
        elif (x * 7 + y * 3 + i) % 9 == 0:
            col = DARK
        c.set(x, y, col)
    return c


def tex_floor_mat():
    """Циновка жилища: полосы папоротника ёлочкой в клетках 16×16, жёлтая лоза по швам,
    оранжевый узелок в углах."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            px, py = x % 16, y % 16
            flip = (x // 16 + y // 16) % 2 == 0
            d = (px + py) % 4 if flip else (px - py) % 4
            col = VIOLET if d == 0 else PLUM
            if d == 2 and (px + py * 3) % 5 == 0:
                col = SEA
            if px == 0 or py == 0:
                col = BRASS
            elif px == 1 or py == 1:
                col = PLUM
            c.set(x, y, col)
    for x in range(0, T, 16):
        for y in range(0, T, 16):
            c.set(x, y, RED)
            for k in (4, 8, 12):
                c.set(x + k, y, GOLD)
                c.set(x, y + k, GOLD)
    return c


def tex_ceiling():
    """Потолок пещеры: тёмный камень в выбоинах, через 32 пикселя ребро-балка с тусклым бликом,
    на балках редкие угольки (без ярких полос, иначе в перспективе они расходятся лучами)."""
    rng = random.Random(309)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = DARK
            if (x + (y // 32) * 8) % 16 == 0:
                col = K
            if y % 32 < 6:
                col = METAL if y % 32 == 1 else DARK
                if y % 32 == 5:
                    col = K
                if y % 32 in (2, 3) and x % 8 == 3:
                    col = K
            c.set(x, y, col)
    for _ in range(34):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == DARK and y % 32 >= 6:
            c.set(x, y, K)
            if rng.random() < 0.4:
                c.set((x + 1) % T, y, K)
    for y in (2, 34):
        for x in (8, 40):
            c.rect(x, y, x + 1, y + 1, RED)
            c.set(x, y, GOLD)
    return c


# --- Раптор ------------------------------------------------------------------------------------

def _claws(c, x, y, n=3, step=2):
    for k in range(n):
        c.set(x + k * step, y, WHITE)


def _raptor_dead(c, k):
    """Падение раптора: 1 осел на колени, шея и морда свесились; 2 лежит на боку, хвост и шея
    по земле, нога торчит вверх."""
    cx, base = 32, 62
    if k == 1:
        # Хвост по земле влево.
        c.line(cx - 6, base - 8, cx - 18, base - 3, VIOLET, 5)
        c.line(cx - 18, base - 3, cx - 27, base - 2, VIOLET, 3)
        # Подломленные ноги.
        for sx in (-6, 7):
            c.ellipse(cx + sx, base - 5, 5, 5, PLUM if sx < 0 else VIOLET)
            c.rect(cx + sx - 2, base - 1, cx + sx + 5, base, VIOLET)
            _claws(c, cx + sx + 1, base, 3)
        c.ellipse(cx, base - 16, 9, 10, VIOLET)
        c.ellipse(cx + 2, base - 14, 5, 8, GOLD)
        for y in (base - 19, base - 15, base - 11):
            c.rect(cx - 1, y, cx + 5, y, BRASS)
        # Руки висят.
        c.line(cx - 8, base - 21, cx - 12, base - 11, VIOLET, 3)
        c.line(cx + 8, base - 21, cx + 12, base - 12, VIOLET, 3)
        _claws(c, cx - 13, base - 9, 2)
        _claws(c, cx + 11, base - 10, 2)
        # Шея вперёд и вниз, морда свесилась вправо.
        c.line(cx + 2, base - 26, cx + 9, base - 30, VIOLET, 6)
        c.ellipse(cx + 12, base - 30, 6, 5, VIOLET)
        c.poly([(cx + 12, base - 33), (cx + 26, base - 27), (cx + 25, base - 22), (cx + 12, base - 25)], VIOLET)
        c.rect(cx + 9, base - 36, cx + 11, base - 34, PLUM)
        c.finish()
        c.line(cx + 10, base - 32, cx + 14, base - 29, K, 1)
        c.line(cx + 14, base - 32, cx + 10, base - 29, K, 1)
        c.line(cx + 16, base - 25, cx + 24, base - 23, K, 1)
        c.set(cx + 19, base - 25, WHITE)
        c.set(cx + 22, base - 24, WHITE)
        return c
    # Лежит: хвост влево, туша, шея и морда вправо, язык наружу.
    c.line(cx - 12, base - 5, cx - 22, base - 3, VIOLET, 5)
    c.line(cx - 22, base - 3, cx - 30, base - 1, VIOLET, 3)
    c.line(cx - 2, base - 8, cx + 3, base - 17, VIOLET, 4)
    c.rect(cx + 1, base - 19, cx + 8, base - 18, VIOLET)
    _claws(c, cx + 9, base - 19, 1)
    c.set(cx + 9, base - 17, WHITE)
    c.set(cx + 2, base - 21, WHITE)
    c.ellipse(cx - 3, base - 5, 13, 5.5, VIOLET)
    c.ellipse(cx - 2, base - 3, 10, 3, GOLD)
    for x in (cx - 8, cx - 3, cx + 2):
        c.rect(x, base - 4, x, base - 1, BRASS)
    for x in (cx - 10, cx - 5, cx):
        c.rect(x, base - 10, x + 1, base - 9, PLUM)
    c.line(cx + 8, base - 6, cx + 15, base - 4, VIOLET, 6)
    c.ellipse(cx + 18, base - 5, 5, 4.5, VIOLET)
    c.poly([(cx + 18, base - 9), (cx + 30, base - 6), (cx + 30, base - 3), (cx + 18, base - 1)], VIOLET)
    c.line(cx + 6, base - 9, cx + 12, base - 13, VIOLET, 3)
    _claws(c, cx + 13, base - 15, 2)
    c.finish()
    c.line(cx + 16, base - 8, cx + 20, base - 5, K, 1)
    c.line(cx + 20, base - 8, cx + 16, base - 5, K, 1)
    c.line(cx + 22, base - 3, cx + 29, base - 3, K, 1)
    c.set(cx + 24, base - 4, WHITE)
    c.set(cx + 27, base - 4, WHITE)
    c.rect(cx + 26, base - 2, cx + 29, base - 2, RED)
    return c


def raptor(angle, phase, mode="walk"):
    """Раптор 64×64 в ракурсе `angle` (0 спереди … 4 со спины, мордой вправо на 1-3), шаг `phase`
    0/1. `mode`: walk, aim (набрал лаву в горло), fire (плевок), die0..die2, hurt. Стоит прямо,
    ростом с героя; ступни на 61-62 строке, ось по центру кадра, как у скелета пиратов."""
    c = Canvas(T, T)
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    if mode.startswith("die"):
        k = int(mode[-1])
        if k == 0:
            return raptor(0, 0, "hurt")
        return _raptor_dead(c, k)
    bob = 1 if phase else 0
    sway = 1 if phase else -1
    walk = mode == "walk"

    def tail_behind():
        # Хвост виден из-за корпуса: спереди уходит вбок и вверх, сбоку тянется назад.
        if side:
            pts = [(cx - 4, 41 - bob), (cx - 14, 40 - bob), (cx - 22, 35 - bob + sway), (cx - 27, 28 - bob + 2 * sway)]
        elif diag:
            pts = [(cx - 3, 42 - bob), (cx - 13, 43 - bob), (cx - 19, 37 - bob + sway), (cx - 22, 30 - bob + 2 * sway)]
        else:
            pts = [(cx + 3, 43 - bob), (cx + 13, 45 - bob), (cx + 19, 39 - bob + sway), (cx + 21, 31 - bob + 2 * sway)]
        for i, t in enumerate((7, 5, 3)):
            c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], VIOLET, t)
        for i in (1, 2):
            c.set(pts[i][0], pts[i][1] - 2, PLUM)
            c.set(pts[i][0] + 1, pts[i][1] - 2, PLUM)

    def tail_front():
        # Со спины хвост висит к зрителю и качается, вполоборота уходит вниз и вбок.
        if diag:
            pts = [(cx - 2, 40 - bob), (cx - 9, 48 - bob), (cx - 15, 52), (cx - 21, 50 + sway)]
        else:
            pts = [(cx, 40 - bob), (cx + sway, 49), (cx + 2 * sway, 55), (cx + 4 * sway, 59)]
        for i, t in enumerate((8, 6, 3)):
            c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], VIOLET, t)
        for i in range(3):
            mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
            c.rect(mx - 1, my, mx + 1, my, PLUM)

    if not back:
        tail_behind()
    # Ноги: мощное бедро, голень назад к пятке, ступня с тремя когтями, серп когтя поднят.
    for sign in (-1, 1):
        col = PLUM if sign < 0 else VIOLET
        if side:
            swing = (sign * 5 if phase else -sign * 5) if walk else sign * 2
            hip = (cx - 1, 45 - bob)
            foot_x = cx - 1 + swing
            c.ellipse(hip[0] + swing * 0.3, hip[1], 5, 6, col)
            knee = (hip[0] + 3 + swing * 0.5, 51 - bob)
            ankle = (foot_x - 3, 57)
            c.line(hip[0] + swing * 0.3, hip[1], knee[0], knee[1], col, 5)
            c.line(knee[0], knee[1], ankle[0], ankle[1], col, 4)
            c.line(ankle[0], ankle[1], foot_x, 60, col, 3)
            c.rect(foot_x - 1, 61, foot_x + 6, 62, col)
            _claws(c, foot_x + 5, 62, 2, 2)
            if sign > 0:
                c.set(foot_x + 4, 60, WHITE)
                c.set(foot_x + 5, 59, WHITE)
                c.set(foot_x + 6, 59, WHITE)
        else:
            lift = 2 if walk and ((sign > 0) == bool(phase)) else 0
            hx = cx + sign * (6 if not diag else 5) + (1 if diag else 0)
            c.ellipse(hx, 46 - bob, 4.6, 6, col)
            c.line(hx, 50 - bob, hx + sign, 59 - lift, col, 4)
            c.rect(hx + sign - 3, 61 - lift, hx + sign + 3, 62 - lift, col)
            if not back:
                _claws(c, hx + sign - 3, 62 - lift, 3, 3)
                c.set(hx - sign * 3, 60 - lift, WHITE)
                c.set(hx - sign * 4, 59 - lift, WHITE)
            else:
                # Со спины видна пятка и шпора.
                c.set(hx + sign, 60 - lift, WHITE)
    # Корпус.
    if side:
        c.ellipse(cx, 37 - bob, 7, 9, VIOLET)
        c.ellipse(cx + 3, 30 - bob, 6, 7, VIOLET)
        c.ellipse(cx + 6, 33 - bob, 2.5, 8, GOLD)
        for y in (28, 31, 34, 37):
            c.rect(cx + 5, y - bob, cx + 8, y - bob, BRASS)
        for x, y in ((cx - 4, 30), (cx - 5, 34), (cx - 5, 38), (cx - 2, 26)):
            c.rect(x, y - bob, x + 2, y - bob, PLUM)
    else:
        w = 8 if diag else 9
        c.ellipse(cx, 34 - bob, w, 11, VIOLET)
        c.ellipse(cx, 27 - bob, w - 1, 5, VIOLET)
        if back:
            # Спина: тёмный хребет и полосы.
            off = 2 if diag else 0
            c.rect(cx - off, 24 - bob, cx - off + 1, 42 - bob, PLUM)
            for y in (27, 31, 35, 39):
                c.rect(cx - off - 4, y - bob, cx - off - 2, y - bob, PLUM)
                c.rect(cx - off + 3, y - bob, cx - off + 5, y - bob, PLUM)
        else:
            off = 3 if diag else 0
            c.ellipse(cx + off, 35 - bob, 5 if not diag else 4, 9, GOLD)
            for y in (28, 31, 34, 37, 40):
                c.rect(cx + off - 3, y - bob, cx + off + 3, y - bob, BRASS)
    if back:
        tail_front()
    # Лапы: короткие, с белыми когтями.
    if side or (diag and not back):
        c.line(cx + 4, 29 - bob, cx + 12, 34 - bob + sway, VIOLET, 3)
        _claws(c, cx + 12, 36 - bob + sway, 2)
        if diag:
            c.line(cx - 7, 28 - bob, cx - 10, 36 - bob - sway, PLUM, 3)
            _claws(c, cx - 11, 38 - bob - sway, 2)
    elif back:
        for sign in (-1, 1):
            c.line(cx + sign * 8, 27 - bob, cx + sign * 11, 36 - bob, VIOLET, 3)
            c.set(cx + sign * 11, 38 - bob, WHITE)
    else:
        for sign in (-1, 1):
            if mode in ("aim", "fire"):
                # Лапы разведены, когти растопырены.
                hx_, hy_ = cx + sign * 14, 21 - bob
                c.line(cx + sign * 8, 28 - bob, cx + sign * 12, 28 - bob, VIOLET, 3)
                c.line(cx + sign * 12, 28 - bob, hx_, hy_, VIOLET, 3)
                c.set(hx_ + sign, hy_ - 2, WHITE)
                c.set(hx_ + sign * 2, hy_, WHITE)
                c.set(hx_ + sign, hy_ + 2, WHITE)
            else:
                hx_, hy_ = cx + sign * 13, 36 - bob - sign * sway
                c.line(cx + sign * 8, 28 - bob, hx_, hy_, VIOLET, 3)
                _claws(c, hx_ - 1, hy_ + 2, 2)
    # Шея и голова.
    hy = 11 - bob - (2 if mode == "aim" else 0)
    if side:
        c.line(cx + 3, 26 - bob, cx + 6, 16 - bob, VIOLET, 7)
        c.line(cx + 8, 25 - bob, cx + 9, 18 - bob, GOLD, 2)
        c.ellipse(cx + 7, hy, 5.5, 5, VIOLET)
        c.poly([(cx + 8, hy - 4), (cx + 23, hy - 1), (cx + 23, hy + 4), (cx + 8, hy + 5)], VIOLET)
        c.rect(cx + 10, hy + 4, cx + 21, hy + 4, GOLD)
        for x in (cx + 1, cx + 4, cx + 7):
            c.poly([(x - 1, hy - 4), (x + 1, hy - 4), (x - 1, hy - 8)], PLUM)
    elif back:
        off = 2 if diag else 0
        c.rect(cx - 3 + off, 17 - bob, cx + 3 + off, 25 - bob, VIOLET)
        c.ellipse(cx + off, hy, 7.5, 6, VIOLET)
        if diag:
            c.poly([(cx + 6, hy - 3), (cx + 16, hy), (cx + 16, hy + 4), (cx + 6, hy + 5)], VIOLET)
        c.rect(cx + off - (1 if diag else 0), hy - 5, cx + off, 24 - bob, PLUM)
        for dx in (-4, 0, 4):
            c.poly([(cx + off + dx - 1, hy - 5), (cx + off + dx + 1, hy - 5), (cx + off + dx, hy - 9)], PLUM)
    else:
        off = 2 if diag else 0
        c.rect(cx - 3 + off, 17 - bob, cx + 3 + off, 25 - bob, VIOLET)
        c.rect(cx - 1 + off, 19 - bob, cx + 1 + off, 25 - bob, GOLD)
        if mode == "aim":
            # Горло раздулось от жара.
            c.ellipse(cx, 21 - bob, 5, 4, RED)
            c.ellipse(cx, 21 - bob, 3, 2.4, GOLD)
        c.ellipse(cx + off, hy - 1, 8, 5.5, VIOLET)
        if diag:
            c.poly([(cx - 4, hy), (cx + 10, hy - 2), (cx + 14, hy + 8), (cx + 7, hy + 11), (cx, hy + 9)], VIOLET)
            c.rect(cx + 6, hy + 9, cx + 12, hy + 9, GOLD)
        else:
            c.poly([(cx - 7, hy), (cx + 7, hy), (cx + 4, hy + 11), (cx - 4, hy + 11)], VIOLET)
        for dx in (-4, 0, 4):
            c.poly([(cx + off + dx - 1, hy - 5), (cx + off + dx + 1, hy - 5), (cx + off + dx, hy - 9)], PLUM)
    c.finish()
    # Глаза, ноздри, пасть поверх обводки.
    if side:
        c.rect(cx + 9, hy - 2, cx + 10, hy - 1, GOLD)
        c.set(cx + 10, hy - 1, K)
        c.rect(cx + 7, hy - 3, cx + 11, hy - 3, K)
        c.set(cx + 21, hy, K)
        c.rect(cx + 12, hy + 2, cx + 22, hy + 2, K)
        for x in (cx + 14, cx + 17, cx + 20):
            c.set(x, hy + 3, WHITE)
    elif not back:
        if diag:
            for ex in (cx - 2, cx + 7):
                c.rect(ex, hy - 2, ex + 1, hy - 1, GOLD)
                c.set(ex + 1, hy - 1, K)
                c.rect(ex - 1, hy - 3, ex + 2, hy - 3, K)
            c.set(cx + 10, hy + 5, K)
            c.rect(cx + 3, hy + 8, cx + 11, hy + 8, K)
            for x in (cx + 5, cx + 8):
                c.set(x, hy + 7, WHITE)
        else:
            for sign in (-1, 1):
                ex = cx + sign * 4
                c.rect(min(ex, ex + sign), hy - 2, max(ex, ex + sign), hy - 1, GOLD if mode != "fire" else RED)
                c.rect(ex, hy - 2, ex, hy - 1, K)
                c.line(ex - sign * 2, hy - 2, ex + sign * 2, hy - 4, K, 1)
                c.set(cx + sign, hy + 7, K)
            if mode == "fire":
                # Пасть настежь: зубы по кругу.
                c.ellipse(cx, hy + 8, 4.5, 4.5, K)
                for dx in (-3, -1, 1, 3):
                    c.set(cx + dx, hy + 5, WHITE)
                    c.set(cx + dx, hy + 11, WHITE)
            else:
                c.rect(cx - 3, hy + 9, cx + 3, hy + 9, K)
                for dx in (-2, 0, 2):
                    c.set(cx + dx, hy + 10, WHITE)
    elif diag:
        c.set(cx + 13, hy + 1, K)
        c.rect(cx + 8, hy - 1, cx + 9, hy - 1, K)
    if mode == "fire":
        c.ellipse(cx, hy + 9, 5, 4.5, RED)
        c.ellipse(cx, hy + 9, 3.2, 2.8, GOLD)
        c.ellipse(cx - 0.5, hy + 8.5, 1.4, 1.2, WHITE)
    if mode == "hurt":
        for x in range(T):
            for y in range(T):
                if c.get(x, y) in (VIOLET, PLUM) and (x + y) % 3 == 0:
                    c.set(x, y, RED)
    return c


# --- Дикарь ------------------------------------------------------------------------------------

def _club(c, hx, hy, tx, ty):
    """Дубина: сук от рукояти (hx, hy) к камню (tx, ty), камень примотан жилой, со сколом."""
    c.line(hx, hy, tx, ty, BRASS, 3)
    c.ellipse(tx, ty, 5, 4.5, METAL)
    c.ellipse(tx - 1, ty - 1, 2.5, 2, GREY)
    dx, dy = tx - hx, ty - hy
    n = math.hypot(dx, dy) or 1.0
    bx, by = tx - dx / n * 4, ty - dy / n * 4
    c.line(bx - dy / n * 3, by + dx / n * 3, bx + dy / n * 3, by - dx / n * 3, GOLD, 2)


def _savage_dead(c, k):
    """Падение дикаря: 1 рухнул на колени, голова на грудь, дубина выпала; 2 лежит навзничь."""
    cx, base = 32, 62
    if k == 1:
        c.rect(cx - 9, base - 3, cx + 8, base, TAN)
        c.rect(cx + 6, base - 1, cx + 14, base, SKIN)
        c.ellipse(cx - 6, base - 5, 4, 4, SKIN)
        c.ellipse(cx + 5, base - 5, 4, 4, SKIN)
        c.poly([(cx - 8, base - 13), (cx + 8, base - 13), (cx + 9, base - 5), (cx - 9, base - 5)], DARK)
        c.poly([(cx - 9, base - 27), (cx + 9, base - 27), (cx + 7, base - 12), (cx - 7, base - 12)], SKIN)
        c.ellipse(cx, base - 27, 12, 3.5, GREY)
        for x in range(cx - 11, cx + 12, 3):
            c.rect(x, base - 25, x + 1, base - 23, METAL)
        c.line(cx - 10, base - 24, cx - 13, base - 10, SKIN, 4)
        c.line(cx + 10, base - 24, cx + 14, base - 11, SKIN, 4)
        # Голова упала на грудь: видны макушка, пучок и борода.
        c.ellipse(cx + 2, base - 30, 7, 6, DARK)
        c.ellipse(cx + 3, base - 27, 5, 4, SKIN)
        c.poly([(cx - 2, base - 26), (cx + 8, base - 26), (cx + 4, base - 17)], DARK)
        c.ellipse(cx + 1, base - 38, 3, 3, DARK)
        c.rect(cx, base - 35, cx + 2, base - 35, WHITE)
        _club(c, cx - 26, base - 3, cx - 15, base - 4)
        c.finish()
        c.rect(cx, base - 28, cx + 2, base - 28, K)
        c.rect(cx + 5, base - 28, cx + 7, base - 28, K)
        return c
    # Лежит навзничь головой вправо, ступни торчат, дубина рядом.
    c.rect(cx - 22, base - 4, cx - 6, base - 1, SKIN)
    c.rect(cx - 25, base - 8, cx - 22, base - 1, SKIN)
    c.rect(cx - 8, base - 6, cx + 2, base - 1, DARK)
    c.rect(cx + 1, base - 7, cx + 13, base - 1, SKIN)
    c.rect(cx + 2, base - 4, cx + 10, base - 4, WHITE)
    c.rect(cx + 11, base - 8, cx + 15, base - 1, GREY)
    c.rect(cx + 12, base - 9, cx + 12, base - 9, METAL)
    c.ellipse(cx + 20, base - 4, 5, 4.5, SKIN)
    c.poly([(cx + 15, base - 6), (cx + 21, base - 9), (cx + 17, base - 13)], DARK)
    c.ellipse(cx + 24, base - 4, 3.5, 4.5, DARK)
    c.ellipse(cx + 28, base - 3, 2.5, 2.5, DARK)
    c.line(cx + 2, base - 7, cx - 4, base - 12, SKIN, 3)
    _club(c, cx - 2, base - 14, cx - 14, base - 12)
    c.finish()
    c.line(cx + 18, base - 6, cx + 20, base - 4, K, 1)
    c.line(cx + 20, base - 6, cx + 18, base - 4, K, 1)
    return c


def savage(angle, phase, mode="walk"):
    """Дикарь 64×64 в тех же ракурсах и кадрах, что раптор. Силуэт: пучок волос на макушке,
    борода клином, мохнатая серая шкура на плечах, тёмная набедренная повязка, каменная дубина
    на плече (в `slash` занесена над головой). `mode`: walk, slash, die0..die2, hurt."""
    c = Canvas(T, T)
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    if mode.startswith("die"):
        k = int(mode[-1])
        if k == 0:
            return savage(0, 0, "hurt")
        return _savage_dead(c, k)
    bob = 1 if phase else 0
    walk = mode == "walk"
    # Ноги: голые, крупные босые ступни.
    for sign in (-1, 1):
        col = TAN if sign < 0 else SKIN
        if side:
            swing = (sign * 5 if phase else -sign * 5) if walk else sign * 2
            hip = (cx, 42 - bob)
            foot_x = cx + swing
            knee = (cx + swing * 0.5 + 1, 51 - bob)
            c.line(hip[0], hip[1], knee[0], knee[1], col, 6)
            c.line(knee[0], knee[1], foot_x - 1, 59, col, 5)
            c.rect(foot_x - 3, 61, foot_x + 4, 62, col)
        else:
            lift = 2 if walk and ((sign > 0) == bool(phase)) else 0
            hx = cx + sign * 5 + (1 if diag and not back else 0)
            c.line(hx, 42 - bob, hx, 51 - bob, SKIN, 6)
            c.line(hx, 51 - bob, hx + sign * 0.5, 59 - lift, SKIN, 5)
            c.rect(hx - 3, 61 - lift, hx + 3, 62 - lift, SKIN)
            c.rect(hx - 3, 50 - bob, hx + 2, 50 - bob, TAN)
            if not back:
                c.set(hx - 1, 62 - lift, TAN)
                c.set(hx + 1, 62 - lift, TAN)
    # Набедренная повязка с рваным подолом и клыком на поясе.
    w = 6 if side else (8 if diag else 9)
    c.poly([(cx - w + 1, 35 - bob), (cx + w - 1, 35 - bob), (cx + w, 45 - bob), (cx - w, 45 - bob)], DARK)
    for i, x in enumerate(range(cx - w, cx + w + 1)):
        d = (2, 0, 3, 1, 2, 0, 1)[i % 7]
        if d:
            c.rect(x, 46 - bob, x, 45 + d - bob, DARK)
    # Торс: голый, широкий в плечах.
    c.poly([(cx - w - 1, 22 - bob), (cx + w + 1, 22 - bob), (cx + w - 1, 36 - bob), (cx - w + 1, 36 - bob)], SKIN)
    c.rect(cx - w + 1, 35 - bob, cx + w - 1, 36 - bob, GOLD)
    if not back:
        c.poly([(cx + w - 4, 37 - bob), (cx + w - 2, 37 - bob), (cx + w - 3, 41 - bob)], WHITE)
    if back:
        # Шкура закрывает лопатки.
        c.poly([(cx - w - 1, 22 - bob), (cx + w + 1, 22 - bob), (cx + w - 1, 31 - bob), (cx - w + 1, 31 - bob)], GREY)
        for i, x in enumerate(range(cx - w + 1, cx + w, 2)):
            c.rect(x, 31 - bob, x, 32 + (i % 3) - bob, GREY)
            c.set(x, 27 - bob + (i % 2), METAL)
    elif not side:
        # Боевая раскраска на груди.
        off = 2 if diag else 0
        for y in (29, 32):
            c.rect(cx + off - 4, y - bob, cx + off - 1, y - bob, WHITE)
            c.rect(cx + off + 2, y - bob, cx + off + 5, y - bob, WHITE)
    else:
        c.rect(cx + 2, 29 - bob, cx + 5, 29 - bob, WHITE)
        c.rect(cx + 2, 32 - bob, cx + 5, 32 - bob, WHITE)
    # Левая рука вдоль тела.
    if not side:
        lx = cx - w - 2
        c.line(lx, 24 - bob, lx - 1, 36 - bob + (1 if phase else -1), TAN if not back else SKIN, 5)
        c.ellipse(lx - 1, 37 - bob + (1 if phase else -1), 2.5, 2.5, TAN if not back else SKIN)
    # Мохнатая шкура на плечах: шире торса, зубчатый край.
    c.ellipse(cx, 23 - bob, w + 4, 3.5, GREY)
    for i, x in enumerate(range(cx - w - 3, cx + w + 4, 2)):
        c.rect(x, 25 - bob, x, 26 + (i % 2) - bob, GREY)
        if i % 2 == 0:
            c.set(x, 22 - bob, METAL)
    # Ожерелье из клыков.
    if not back:
        for dx in (-4, -1, 2, 5) if not side else (3, 6):
            c.rect(cx + dx, 26 - bob, cx + dx, 28 - bob, WHITE)
    # Правая рука с дубиной.
    up = mode == "slash"
    sx = cx + (w + 1 if not side else 2)
    if up:
        hx_, hy_ = cx + (9 if not side else 8), 14 - bob
        tip = (hx_ + (6 if not (side or diag) else 12), 6)
        tail = (hx_ - 2, hy_ + 6)
    else:
        hx_, hy_ = cx + (12 if not side else 10), 33 - bob
        tip = (hx_ + (5 if not (side or diag) else 11), 13 - bob)
        tail = (hx_ - 1, hy_ + 5)
    if back and not diag:
        # Со спины дубина лежит на правом плече, камень за головой.
        hx_, hy_ = cx + 11, 30 - bob
        tip = (cx + 14, 11 - bob)
        tail = (hx_ - 1, hy_ + 6)
    c.line(sx, 24 - bob, hx_, hy_, SKIN, 5)
    _club(c, tail[0], tail[1], tip[0], tip[1])
    c.ellipse(hx_, hy_, 2.8, 2.8, SKIN)
    # Голова.
    hx = cx + (2 if side else (1 if diag else 0))
    hy = 13 - bob
    c.rect(hx - 2, 18 - bob, hx + 2, 22 - bob, TAN)
    if back:
        c.ellipse(hx, hy, 7, 7, DARK)
        c.poly([(hx - 6, hy + 2), (hx + 6, hy + 2), (hx + 3, hy + 9), (hx - 3, hy + 9)], DARK)
        if diag:
            c.rect(hx + 6, hy - 1, hx + 8, hy + 2, SKIN)
    elif side:
        c.ellipse(hx - 1, hy - 1, 7, 6.5, DARK)
        c.ellipse(hx + 2, hy + 1, 5, 5.5, SKIN)
        c.rect(hx + 6, hy, hx + 8, hy + 2, SKIN)
        c.rect(hx - 2, hy - 6, hx + 6, hy - 3, DARK)
        c.poly([(hx - 1, hy + 3), (hx + 7, hy + 3), (hx + 8, hy + 7), (hx + 4, hy + 12), (hx, hy + 8)], DARK)
        c.rect(hx + 2, hy - 1, hx + 7, hy, WHITE)
    else:
        off = 1 if diag else 0
        c.ellipse(hx, hy - 1, 7.5, 6.5, DARK)
        c.ellipse(hx + off, hy + 1, 5.5, 5.5, SKIN)
        c.rect(hx - 5, hy - 6, hx + 5 + off, hy - 3, DARK)
        c.poly([(hx - 6 + off, hy + 3), (hx + 6 + off, hy + 3), (hx + 4 + off, hy + 9), (hx + off, hy + 13), (hx - 4 + off, hy + 9)], DARK)
        # Белая полоса раскраски через глаза.
        c.rect(hx - 5 + off, hy - 1, hx + 5 + off, hy, WHITE)
        c.rect(hx - 1 + off, hy + 1, hx + 1 + off, hy + 3, SKIN)
    # Пучок на макушке, перехвачен костяным кольцом.
    c.rect(hx - 1, hy - 9, hx + 1, hy - 7, WHITE)
    c.ellipse(hx, hy - 11, 3, 2.6, DARK)
    c.finish()
    if not back:
        if side:
            c.set(hx + 5, hy - 1, K)
            c.rect(hx + 3, hy - 2, hx + 7, hy - 2, K)
            c.set(hx + 5, hy + 5, K if mode != "slash" else WHITE)
        else:
            off = 1 if diag else 0
            for e in (-3, 3):
                c.set(hx + e + off, hy, K)
                c.rect(hx + e + off - 1, hy - 2, hx + e + off + 1, hy - 2, K)
            if mode == "slash":
                # Оскал.
                c.rect(hx - 2 + off, hy + 5, hx + 2 + off, hy + 6, K)
                c.rect(hx - 2 + off, hy + 5, hx + 2 + off, hy + 5, WHITE)
            else:
                c.rect(hx - 1 + off, hy + 5, hx + 1 + off, hy + 5, TAN)
    if mode == "hurt":
        for x in range(T):
            for y in range(T):
                if c.get(x, y) in (SKIN, TAN, GREY) and (x + y) % 3 == 0:
                    c.set(x, y, RED)
    return c


def enemy_strips():
    out = {}
    for name, draw in (("skel", raptor), ("cut", savage)):
        walk = []
        for a in range(5):
            for ph in range(2):
                walk.append(draw(a, ph, "walk"))
        out[name + "_walk"] = strip(walk)
        out[name + "_die"] = strip([draw(0, 0, "die%d" % k) for k in range(3)])
    out["skel_fire"] = strip([raptor(0, 0, "aim"), raptor(0, 0, "fire")])
    out["cut_slash"] = strip([savage(0, 0, "walk"), savage(0, 0, "slash")])
    return out


# --- Предметы, оружие, лицо --------------------------------------------------------------------

def shot():
    """Плевок раптора: сгусток лавы из основы, оранжевый с жёлтой сердцевиной, не спутать с
    серым камнем героя."""
    return dinosaurs16.shot()


def bullet():
    """Камень из рогатки: угловатый серый голыш со светлым сколом, за ним щепоть пыли."""
    c = Canvas(16, 16)
    c.poly([(5, 5), (9, 4), (12, 7), (11, 10), (7, 11), (4, 9)], METAL)
    c.rect(7, 12, 8, 13, GREY)
    c.set(6, 14, GREY)
    c.set(9, 14, GREY)
    c.finish()
    c.poly([(6, 6), (9, 5), (9, 7), (7, 8)], GREY)
    c.set(7, 6, WHITE)
    c.set(8, 6, WHITE)
    return c


def _egg(c, cx, cy, rx, ry, spots):
    c.ellipse(cx, cy + ry * 0.15, rx, ry * 0.85, WHITE)
    c.ellipse(cx, cy - ry * 0.25, rx * 0.8, ry * 0.75, WHITE)
    for dx, dy in spots:
        c.rect(cx + dx, cy + dy, cx + dx + 1, cy + dy + 1, AQUA)
        c.set(cx + dx + 1, cy + dy + 1, SEA)


def _wicker(c, x0, y0, x1, y1):
    """Плетёная корзина: прутья и лоза шашкой, обод."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            over = ((x - x0) // 3 + (y - y0) // 3) % 2 == 0
            col = GOLD if over else BRASS
            if (x - x0) % 3 == 2:
                col = DARK
            c.set(x, y, col)
    c.rect(x0 - 1, y0, x1 + 1, y0 + 2, BRASS)
    c.rect(x0 - 1, y0, x1 + 1, y0, GOLD)
    c.rect(x0, y1, x1, y1, DARK)


def decor(kind):
    """Ориентир зала 64×64, низ на 62-63 строке: 0 гнездо с яйцами, 1 корзины с кокосами,
    2 костёр в чаше на костяной стойке, 3 катапульта из бревна, 4 череп трицератопса, 5 тотем
    со шкурой."""
    c = Canvas(T, T)
    if kind == 0:
        # Гнездо: вал из прутьев, три крупных пятнистых яйца, среднее надколото.
        c.ellipse(32, 55, 26, 8, BRASS)
        _egg(c, 32, 34, 10, 15, ((-5, -4), (3, 2), (-2, 7), (4, -8)))
        _egg(c, 16, 42, 9, 13, ((-4, -2), (2, 4), (-1, -8)))
        _egg(c, 48, 43, 9, 13, ((1, -4), (-4, 3), (3, 5)))
        c.ellipse(32, 58, 27, 5.5, BRASS)
        for i in range(13):
            x = 7 + i * 4
            c.line(x, 53 + (i % 3), x + 6, 61 - (i % 2), GOLD if i % 2 else DARK, 1)
            c.line(x + 5, 52 + (i % 2), x - 1, 60, DARK if i % 2 else GOLD, 1)
        c.finish()
        # Трещина на среднем яйце.
        for x, y in ((30, 21), (31, 23), (33, 24), (32, 26), (34, 28), (33, 30)):
            c.set(x, y, K)
    elif kind == 1:
        # Две корзины внизу, третья сверху с кокосами.
        _wicker(c, 5, 40, 29, 62)
        _wicker(c, 35, 42, 58, 62)
        for x in (26, 34, 42):
            c.ellipse(x, 17, 5, 5, DARK)
            c.set(x - 1, 15, BRASS)
            c.set(x + 1, 16, K)
            c.set(x - 1, 17, K)
        _wicker(c, 19, 19, 46, 39)
        c.rect(22, 27, 31, 33, GREY)
        c.rect(24, 29, 29, 31, RED)
        c.poly([(46, 44), (58, 38), (56, 46)], VIOLET)
        c.line(47, 44, 56, 41, PLUM, 1)
        c.finish()
    elif kind == 2:
        # Стойка из трёх связанных костей, каменная чаша, огонь.
        c.line(32, 30, 16, 62, WHITE, 3)
        c.line(32, 30, 48, 62, WHITE, 3)
        c.rect(30, 28, 33, 62, WHITE)
        for x in (15, 49):
            c.ellipse(x - 1.5, 62, 2, 1.6, WHITE)
            c.ellipse(x + 1.5, 62, 2, 1.6, WHITE)
        c.rect(27, 34, 36, 37, GOLD)
        c.rect(27, 36, 36, 36, BRASS)
        c.poly([(18, 20), (45, 20), (39, 30), (24, 30)], METAL)
        c.rect(17, 18, 46, 21, METAL)
        c.rect(17, 18, 46, 18, GREY)
        # Пламя языками.
        c.poly([(21, 18), (26, 4), (30, 12), (34, 0), (38, 11), (42, 6), (43, 18)], RED)
        c.poly([(25, 18), (28, 10), (31, 15), (34, 6), (37, 15), (39, 18)], GOLD)
        c.finish()
        c.poly([(30, 18), (34, 11), (36, 18)], SKY)
        c.set(22, 23, DARK)
        c.set(30, 25, DARK)
        c.set(40, 23, DARK)
    elif kind == 3:
        # Катапульта: козлы из брёвен, рычаг-бревно с корзиной и глыбой, противовес на верёвке.
        c.line(10, 62, 30, 34, BRASS, 5)
        c.line(52, 62, 32, 34, BRASS, 5)
        c.rect(6, 59, 57, 62, DARK)
        c.rect(6, 59, 57, 59, BRASS)
        c.line(8, 48, 56, 10, BRASS, 4)
        c.line(9, 47, 55, 10, GOLD, 1)
        c.rect(27, 30, 36, 37, GOLD)
        c.rect(27, 33, 36, 33, BRASS)
        c.rect(27, 36, 36, 36, BRASS)
        # Корзина на конце рычага и камень в ней.
        c.ellipse(55, 6, 6, 5, METAL)
        c.ellipse(53, 4, 2.5, 2, GREY)
        c.poly([(47, 9), (62, 9), (59, 16), (50, 16)], DARK)
        c.rect(47, 9, 62, 10, GOLD)
        # Противовес.
        c.line(9, 48, 9, 52, GOLD, 1)
        c.poly([(3, 52), (15, 52), (17, 58), (1, 58)], METAL)
        c.rect(4, 53, 9, 54, GREY)
        c.finish()
    elif kind == 4:
        # Череп трицератопса в профиль мордой влево: воротник веером, два рога над глазом,
        # рог на носу, клюв.
        c.poly([(34, 14), (50, 6), (61, 18), (62, 38), (54, 54), (40, 50), (34, 34)], WHITE)
        for a in (0.15, 0.55, 0.95, 1.35):
            c.line(40, 40, 40 + math.cos(-a) * 22, 40 + math.sin(-a) * 22 - 2, GREY, 1)
        c.poly([(8, 44), (20, 34), (38, 30), (44, 44), (40, 60), (20, 62), (8, 56)], WHITE)
        c.poly([(2, 50), (10, 44), (10, 58), (5, 60)], WHITE)
        c.poly([(30, 32), (22, 6), (38, 28)], WHITE)
        c.poly([(14, 40), (11, 26), (19, 36)], WHITE)
        c.rect(22, 60, 40, 62, WHITE)
        c.finish()
        c.ellipse(31, 41, 4, 4.5, K)
        c.ellipse(15, 46, 2, 1.5, K)
        c.rect(8, 55, 26, 55, K)
        for x in (12, 16, 20, 24):
            c.set(x, 56, GREY)
            c.set(x, 54, K)
        c.line(46, 50, 50, 44, GREY, 1)
        c.ellipse(52, 28, 3, 4, GREY)
        c.line(24, 18, 27, 24, GREY, 1)
    else:
        # Тотем: столб с двумя резными мордами, перекладина-крылья, шкура на крюке, камни у
        # основания.
        c.rect(25, 8, 38, 62, BRASS)
        c.rect(25, 8, 26, 62, GOLD)
        c.rect(37, 8, 38, 62, DARK)
        c.poly([(6, 12), (57, 12), (60, 19), (3, 19)], BRASS)
        c.rect(6, 12, 57, 13, GOLD)
        for x in range(8, 24, 5):
            c.rect(x, 15, x + 2, 19, RED)
            c.rect(63 - x - 2, 15, 63 - x, 19, RED)
        c.poly([(27, 8), (31, 0), (36, 8)], WHITE)
        c.rect(22, 34, 41, 36, DARK)
        c.rect(22, 58, 41, 62, METAL)
        c.rect(22, 58, 41, 58, GREY)
        # Шкура висит справа: оранжевая, пятнистая, рваный низ.
        c.poly([(41, 20), (57, 20), (59, 40), (54, 46), (50, 41), (46, 47), (42, 42)], RED)
        for x, y in ((45, 25), (52, 28), (47, 34), (54, 37), (50, 23)):
            c.rect(x, y, x + 1, y + 1, DARK)
        c.finish()
        # Морды: глаза, клыки, раскраска.
        for y0 in (20, 40):
            c.rect(27, y0, 30, y0 + 3, WHITE)
            c.rect(33, y0, 36, y0 + 3, WHITE)
            c.rect(28, y0 + 1, 29, y0 + 2, K)
            c.rect(34, y0 + 1, 35, y0 + 2, K)
            c.rect(27, y0 - 2, 36, y0 - 2, AQUA)
            c.rect(31, y0 + 3, 32, y0 + 6, DARK)
            c.rect(27, y0 + 8, 36, y0 + 10, K)
            for x in (28, 31, 34):
                c.rect(x, y0 + 8, x + 1, y0 + 9, WHITE)
            c.rect(27, y0 + 12, 36, y0 + 12, RED)
    return c


def key():
    """Ключ: костяной из основы, с оранжевой обмоткой."""
    return dinosaurs16.key()


def medkit():
    """Лечение: жареный окорок на кости из основы."""
    return dinosaurs16.medkit()


def pistol(frame):
    """Рогатка в руке снизу по центру, 128×96: голое предплечье с костяным браслетом,
    кулак на рукояти, развилка рожками вглубь (ось x=64, камень в коже между рожками у
    верхнего края); кадр 1 после выстрела: жилы хлестнули вперёд, кожа пустая, сверху хлопок
    пыли."""
    c = Canvas(128, 96)
    # Предплечье: голое, загорелое, слегка расширяется к локтю, тень по дальнему краю.
    for y in range(60, 96):
        w = 13 + (y - 60) // 5
        for x in range(64 - w, 64 + w):
            col = SKIN
            if x > 64 + w - 5:
                col = TAN
            c.set(x, y, col)
    for x, y in ((56, 76), (60, 82), (54, 88), (66, 90), (62, 72)):
        c.rect(x, y, x, y + 2, TAN)
    # Развилка: рукоять и два рожка, обмотка шнуром.
    c.rect(60, 36, 67, 60, BRASS)
    for sign in (-1, 1):
        c.line(64 + sign * 2, 38, 64 + sign * 15, 22, BRASS, 7)
        c.line(64 + sign * 15, 22, 64 + sign * 16, 8, BRASS, 6)
        c.line(64 + sign * 14 - 1, 21, 64 + sign * 15 - 1, 9, GOLD, 1)
        # Обвязка жил на конце рожка.
        c.rect(64 + sign * 16 - 3, 9, 64 + sign * 16 + 3, 13, RED)
        c.rect(64 + sign * 16 - 3, 11, 64 + sign * 16 + 3, 11, DARK)
    c.rect(61, 37, 62, 59, GOLD)
    # Жилы и кожа с камнем.
    for sign in (-1, 1):
        if frame:
            c.line(64 + sign * 16, 10, 64 + sign * 7, 3, TAN, 2)
            c.line(64 + sign * 7, 3, 64 + sign * 3, 5, TAN, 2)
        else:
            c.line(64 + sign * 16, 10, 64 + sign * 5, 16, TAN, 2)
    if frame:
        c.rect(61, 3, 67, 6, DARK)
    else:
        c.poly([(57, 12), (71, 12), (70, 20), (58, 20)], DARK)
        c.rect(57, 12, 71, 12, TAN)
        c.poly([(59, 8), (65, 4), (70, 8), (69, 14), (60, 15)], METAL)
        c.poly([(61, 8), (65, 6), (66, 9), (62, 11)], GREY)
        c.rect(63, 7, 64, 7, WHITE)
    # Кулак: четыре пальца поперёк рукояти, большой сверху, костяшки.
    c.ellipse(64, 54, 15, 9, SKIN)
    c.rect(50, 46, 78, 56, SKIN)
    for k in range(4):
        y0 = 42 + k * 4
        c.rect(52, y0, 76, y0 + 3, SKIN)
        c.rect(52, y0 + 3, 76, y0 + 3, TAN)
        c.rect(73, y0, 76, y0 + 2, TAN)
    c.poly([(50, 44), (56, 38), (62, 40), (58, 48)], SKIN)
    c.rect(56, 39, 59, 40, WHITE)
    # Браслет: бусины-позвонки на шнуре.
    c.rect(49, 62, 78, 67, DARK)
    for x in range(50, 77, 6):
        c.rect(x, 62, x + 3, 67, WHITE)
        c.rect(x, 67, x + 3, 67, GREY)
        c.set(x + 1, 64, GREY)
    c.finish()
    if frame:
        # Хлопок: облачко пыли и осколки.
        c.ellipse(64, 0, 16, 8, SKY)
        c.ellipse(64, 0, 9, 5, WHITE)
        for x, y in ((44, 4), (84, 5), (52, 10), (77, 11)):
            c.rect(x, y, x + 1, y + 1, SKY)
    return c


def face(mode):
    """Лицо пещерного человека для HUD, 32×32: лохматая копна шире головы, кость в волосах,
    тяжёлые брови, крупный нос и челюсть; 0 прямо, 1 глянул влево, 2 вправо, 3 больно
    (зажмурился, кость съехала, красная ссадина), 4 ухмылка во все зубы."""
    c = Canvas(32, 32)
    # Копна: зубчатый контур прядей.
    c.ellipse(16, 13, 13, 11, DARK)
    for i, x in enumerate(range(3, 30, 3)):
        c.poly([(x - 1, 8), (x + 2, 8), (x + (1 if i % 2 else 0), 0 + (i % 3))], DARK)
    for x, d in ((2, 9), (4, 11), (27, 11), (29, 9)):
        c.rect(x, 16, x + 1, 16 + d, DARK)
    # Лицо и челюсть.
    c.ellipse(16, 17, 9, 9, SKIN)
    c.rect(9, 19, 23, 27, SKIN)
    c.rect(11, 28, 21, 29, SKIN)
    c.rect(13, 30, 19, 30, TAN)
    # Чёлка до бровей.
    c.rect(7, 7, 25, 11, DARK)
    for x in (9, 13, 18, 22):
        c.rect(x, 12, x + 1, 12, DARK)
    # Кость в волосах наискось.
    y_bone = 2 if mode == 3 else 0
    c.line(18, 6 + y_bone, 28, 1 + y_bone, WHITE, 2)
    c.ellipse(29, 0 + y_bone, 1.5, 1.5, WHITE)
    c.ellipse(29.5, 3 + y_bone, 1.5, 1.5, WHITE)
    c.ellipse(17, 5 + y_bone, 1.5, 1.5, WHITE)
    c.ellipse(17.5, 8 + y_bone, 1.5, 1.5, WHITE)
    c.finish()
    look = {0: 0, 1: -2, 2: 2, 3: 0, 4: 0}[mode]
    # Брови козырьком.
    c.rect(9, 13, 14, 14, DARK)
    c.rect(18, 13, 23, 14, DARK)
    for e in (-4, 4):
        if mode == 3:
            c.line(16 + e - 2, 16, 16 + e + 2, 18, K, 1)
            c.line(16 + e - 2, 18, 16 + e + 2, 16, K, 1)
        else:
            c.rect(16 + e - 2, 15, 16 + e + 2, 18, WHITE)
            c.rect(16 + e + look - 1, 16, 16 + e + look, 18, K)
    # Нос картошкой.
    c.rect(14, 18, 18, 22, TAN)
    c.rect(15, 18, 17, 21, SKIN)
    c.set(14, 22, K)
    c.set(18, 22, K)
    if mode == 4:
        c.rect(10, 24, 22, 27, K)
        c.rect(11, 25, 21, 26, WHITE)
        for x in (13, 16, 19):
            c.rect(x, 25, x, 26, GREY)
        c.set(9, 23, K)
        c.set(23, 23, K)
    elif mode == 3:
        c.ellipse(16, 26, 3.5, 2, K)
        c.rect(15, 25, 17, 25, WHITE)
        c.rect(21, 20, 23, 21, RED)
        c.set(22, 22, RED)
    else:
        c.rect(12, 25, 20, 25, K)
        if mode == 0:
            c.set(11, 24, K)
    # Щетина по челюсти.
    for x, y in ((10, 26), (12, 28), (20, 28), (22, 26), (16, 29)):
        if c.get(x, y) == SKIN:
            c.set(x, y, TAN)
    return c


def textures():
    return {"wall_planks": tex_clay(), "wall_stone": tex_basalt(), "wall_pillar": tex_trunk(),
            "wall_exit": tex_exit(), "wall_cabin": tex_hide(), "wall_hull": tex_gap(), "wall_cargo": tex_baskets(),
            "floor_planks": tex_floor_clay(), "floor_stone": tex_floor_lava(), "floor_carpet": tex_floor_mat(),
            "ceiling_beams": tex_ceiling()}


def sprites():
    out = {"shot": shot(), "bullet": bullet(), "key": key(), "medkit": medkit(),
           "hold_decor": strip([decor(k) for k in range(6)]),
           "pistol": strip([pistol(0), pistol(1)]),
           "face": strip([face(i) for i in range(5)])}
    out.update(enemy_strips())
    out.update(textures())
    return out


if __name__ == "__main__":
    if "--preview" in sys.argv:
        dinosaurs16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], dinosaurs16.shaded(sprites()))
