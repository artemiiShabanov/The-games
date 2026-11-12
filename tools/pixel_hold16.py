"""Рисунок шутера × 16/32-bit «до выхода» (#100) для pixel_sprites16.py, графика по Doom
(решение 2026-11-12): текстуры 64×64 стен трюма (доски), пещеры (камень), колонны-мачты,
двери выхода, пола и потолка; скелет-пират в пяти ракурсах (спереди, вполоборота, сбоку,
вполоборота со спины, со спины; зеркало даёт восемь), выстрел и падение; пистоль в руке;
лицо героя для HUD; ключ, аптечка, пуля. Всё в палитре спрайтов сеттинга.
"""
import math
import random

from pixel_sprites16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, WOOD,
                             BARK, RED, LEAF, PINE)

T = 64


# --- Текстуры ----------------------------------------------------------------------------------

def tex_planks():
    """Доски трюма: горизонтальные, швы, гвозди, сучки, снизу темнее."""
    rng = random.Random(101)
    c = Canvas(T, T)
    for y in range(T):
        row = y // 8
        for x in range(T):
            seam = (x + row * 23) % 64 == 0
            col = WOOD if (y % 8) not in (0, 7) else BARK
            if (y % 8) == 1:
                col = TAN
            if seam:
                col = BARK
            c.set(x, y, col)
    for _ in range(24):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == WOOD:
            c.set(x, y, BARK)
    for row in range(8):
        for x in ((row * 23 + 3) % 64, (row * 23 + 60) % 64):
            c.set(x, row * 8 + 3, GREY)
            c.set(x, row * 8 + 4, K)
    for y in range(56, 64):
        for x in range(T):
            if (x + y) % 2 == 0 and c.get(x, y) == WOOD:
                c.set(x, y, BARK)
    return c


def tex_stone():
    """Камень пещеры: глыбы со светом сверху слева, тёмные щели, редкий мох."""
    rng = random.Random(102)
    c = Canvas(T, T)
    c.rect(0, 0, T - 1, T - 1, K)
    y = 0
    while y < T:
        h = rng.randint(9, 14)
        x = rng.randint(-6, 0)
        while x < T:
            w = rng.randint(12, 22)
            for yy in range(y + 1, min(y + h, T)):
                for xx in range(x + 1, x + w):
                    if 0 <= xx < T:
                        edge_top = yy - y < 3
                        edge_left = xx - x < 3
                        c.set(xx, yy, WHITE if edge_top and edge_left else (GREY if edge_top or edge_left else TAN))
            if rng.random() < 0.3:
                mx = x + rng.randint(2, w - 3)
                for k in range(3):
                    c.set(mx + k, y + 1, LEAF)
                    c.set(mx + k, y + 2, PINE)
            x += w
        y += h
    return c


def tex_pillar():
    """Мачта-колонна: вертикальные доски, железные обручи."""
    c = Canvas(T, T)
    for x in range(T):
        col = WOOD if (x % 16) not in (0, 15) else BARK
        if x % 16 == 2:
            col = TAN
        c.rect(x, 0, x, T - 1, col)
    for y in (10, 48):
        c.rect(0, y, T - 1, y + 4, GREY)
        c.rect(0, y + 4, T - 1, y + 4, K)
        for x in range(4, T, 10):
            c.set(x, y + 2, WHITE)
    return c


def tex_exit():
    """Дверь выхода: тёмные доски, железные полосы, череп над замком, золотой замок."""
    c = tex_planks()
    for x in range(T):
        for y in range(T):
            if c.get(x, y) == WOOD:
                c.set(x, y, BARK)
            elif c.get(x, y) == TAN:
                c.set(x, y, WOOD)
    for y in (8, 52):
        c.rect(0, y, T - 1, y + 3, GREY)
        c.rect(0, y + 3, T - 1, y + 3, K)
    c.rect(0, 0, 3, T - 1, K)
    c.rect(T - 4, 0, T - 1, T - 1, K)
    c.ellipse(32, 24, 7, 6, WHITE)
    c.rect(28, 28, 36, 33, WHITE)
    c.ellipse(29, 24, 2, 2, K)
    c.ellipse(35, 24, 2, 2, K)
    c.rect(30, 33, 34, 33, K)
    c.rect(27, 38, 37, 48, GOLD)
    c.rect(27, 48, 37, 48, BRASS)
    c.rect(31, 41, 33, 45, K)
    return c


def tex_cabin():
    """Каюта: красные крашеные доски, золотая рейка посередине, картина-карта в раме."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = RED if (x % 16) not in (0, 15) else BARK
            if (x % 16) == 1:
                col = WOOD
            c.set(x, y, col)
    c.rect(0, 30, T - 1, 33, GOLD)
    c.rect(0, 33, T - 1, 33, BRASS)
    c.rect(18, 6, 45, 24, BRASS)
    c.rect(20, 8, 43, 22, TAN)
    c.line(22, 18, 30, 11, BARK, 1)
    c.line(30, 11, 40, 16, BARK, 1)
    c.rect(36, 12, 38, 14, RED)
    for x in range(0, T, 8):
        c.set(x + 3, 56, BRASS)
    return c


def tex_hull():
    """Борт: тёмные доски и круглый иллюминатор с морем и бликом."""
    c = tex_planks()
    for x in range(T):
        for y in range(T):
            if c.get(x, y) == WOOD:
                c.set(x, y, BARK if (x + y) % 5 == 0 else WOOD)
    c.ellipse(32, 26, 15, 15, BRASS)
    c.ellipse(32, 26, 12, 12, GREY)
    c.ellipse(32, 26, 10, 10, SEA)
    c.rect(22, 28, 42, 36, NAVY)
    c.ellipse(28, 22, 3, 2, AQUA)
    c.ellipse(32, 26, 10, 10, None) if False else None
    for a in range(0, 360, 45):
        import math as _m
        c.set(32 + 13.5 * _m.cos(_m.radians(a)), 26 + 13.5 * _m.sin(_m.radians(a)), K)
    return c


def tex_cargo():
    """Склад: стена из ящиков с досками крест-накрест."""
    c = Canvas(T, T)
    for by in (0, 32):
        for bx in (0, 32):
            off = 16 if by == 32 else 0
            x0 = (bx + off) % T
            for y in range(by, by + 32):
                for x in range(32):
                    xx = (x0 + x) % T
                    edge = x in (0, 31) or y in (by, by + 31)
                    c.set(xx, y, BARK if edge else (WOOD if (y - by) % 8 else BARK))
            for k in range(30):
                c.set((x0 + 1 + k) % T, by + 1 + k, TAN)
                c.set((x0 + 30 - k) % T, by + 1 + k, TAN)
            c.set((x0 + 3) % T, by + 3, GREY)
            c.set((x0 + 28) % T, by + 28, GREY)
    return c


def tex_floor_stone():
    """Каменный пол пещеры: плиты с тёмными швами."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            seam = x % 16 == 0 or (y + (x // 16) * 8) % 16 == 0
            c.set(x, y, K if seam else (GREY if (x * 7 + y * 3) % 11 else TAN))
    return c


def tex_carpet():
    """Ковёр каюты: красный с золотым узором ромбами."""
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            d = abs((x % 16) - 8) + abs((y % 16) - 8)
            col = RED
            if d == 6:
                col = GOLD
            elif d < 2:
                col = BRASS
            elif (x + y) % 2 == 0 and d > 6:
                col = BARK
            c.set(x, y, col)
    return c


def tex_floor():
    """Пол: доски вдоль, потемнее стен."""
    c = Canvas(T, T)
    for x in range(T):
        for y in range(T):
            board = x // 16
            col = BARK if (x % 16) in (0, 15) else WOOD
            if (y + board * 21) % 64 == 0:
                col = BARK
            if (x % 16) == 1:
                col = TAN if (y // 4) % 3 == 0 else WOOD
            c.set(x, y, col if (x + y) % 7 else BARK)
    return c


def tex_ceiling():
    """Потолок: тёмные доски, через 32 пикселя балка с бликом; без ярких полос, иначе в
    перспективе они расходятся лучами."""
    rng = random.Random(106)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            col = BARK
            if x % 16 == 0:
                col = K
            if y % 32 < 6:
                col = WOOD if y % 32 == 1 else BARK
                if y % 32 == 5:
                    col = K
            c.set(x, y, col)
    for _ in range(30):
        x, y = rng.randrange(T), rng.randrange(T)
        if c.get(x, y) == BARK:
            c.set(x, y, K)
    return c


# --- Скелет ------------------------------------------------------------------------------------

def _bandana(c, cx, top, side, back):
    """Бандана сабельника: красный платок с узлом на затылке."""
    c.ellipse(cx, top + 9, 7 if not side else 6, 4, RED)
    if side or back:
        c.rect(cx - (8 if side else 2), top + 9, cx - (5 if side else -2), top + 13, RED)


def _hat(c, cx, top, side, back):
    """Треуголка: спереди треугольник полями вверх, сбоку и со спины ниже."""
    if side:
        c.poly([(cx - 9, top + 6), (cx + 10, top + 6), (cx + 4, top), (cx - 4, top)], K)
        c.rect(cx - 9, top + 6, cx + 10, top + 7, GOLD)
    else:
        c.poly([(cx - 11, top + 7), (cx + 11, top + 7), (cx, top - 2)], K)
        c.rect(cx - 11, top + 6, cx + 11, top + 7, GOLD)
        if not back:
            c.ellipse(cx, top + 3, 2, 2, WHITE)


def skeleton(angle, phase, mode="walk", cutlass=False):
    """Скелет-пират 64×64 в ракурсе `angle` (0 спереди … 4 со спины, лицом вправо на 1-3),
    шаг `phase` 0/1. `mode`: walk, aim, fire, slash, die0..die2. `cutlass` сабельник: бандана
    вместо треуголки, сабля вместо мушкета."""
    c = Canvas(T, T)
    cx = 32
    side = angle == 2
    back = angle >= 3
    diag = angle in (1, 3)
    if mode.startswith("die"):
        k = int(mode[-1])
        # Падение: кости оседают кучей, череп скатывается.
        if k == 0:
            return skeleton(0, 0, "hurt", cutlass)
        base = 62
        for i in range(6 if k == 1 else 9):
            x = 18 + i * 4 + (i % 2) * 2
            c.line(x, base - (6 if k == 1 else 2) - (i % 3), x + 6, base - (i % 2) * 3, WHITE, 2)
        c.ellipse(cx + (6 if k == 2 else 2), base - (10 if k == 1 else 5), 6, 5, WHITE)
        c.ellipse(cx + (4 if k == 2 else 0), base - (11 if k == 1 else 6), 1.5, 1.5, K)
        c.poly([(cx - 8, base - 2), (cx + 10, base - 2), (cx + 2, base - 9)], K)
        return c.finish()
    bob = 1 if phase else 0
    # Ноги.
    for sign in (-1, 1):
        swing = (sign * 3 if phase else -sign * 3) if mode == "walk" else 0
        hip = (cx + sign * (2 if side else 4), 40 - bob)
        foot = (cx + sign * (2 if side else 5) + swing * (1 if side else 0.3), 61)
        knee = ((hip[0] + foot[0]) / 2 + (2 if side else 0), 51)
        c.line(hip[0], hip[1], knee[0], knee[1], WHITE, 2)
        c.line(knee[0], knee[1], foot[0], foot[1], WHITE, 2)
        c.rect(foot[0] - 2, 61, foot[0] + 3, 62, K)
    # Таз и позвоночник.
    c.ellipse(cx, 39 - bob, 6 if not side else 4, 3, WHITE)
    c.rect(cx - 1, 22 - bob, cx + 1, 38 - bob, WHITE)
    # Рёбра: спереди дугами, сбоку короче, со спины лопатки.
    w = 4 if side else (6 if diag else 8)
    for i in range(4):
        y = 24 + i * 3 - bob
        if back:
            c.rect(cx - w + 1, y, cx + w - 1, y, GREY)
        else:
            c.line(cx - w + i * 0.5, y, cx - 1, y + 1, WHITE, 1)
            c.line(cx + 1, y + 1, cx + w - i * 0.5, y, WHITE, 1)
    c.rect(cx - w, 21 - bob, cx + w, 22 - bob, WHITE)
    # Рваная рубаха: красная лента через грудь.
    c.line(cx - w, 22 - bob, cx + w, 32 - bob, RED, 2)
    # Руки и оружие.
    if cutlass:
        up = mode == "slash"
        hx_ = cx + (10 if side or diag else 9)
        c.line(cx + 6, 23 - bob, hx_, 30 - bob if not up else 16 - bob, WHITE, 2)
        tip = (hx_ + (14 if side or diag else 6), 20 - bob if not up else 2 - bob)
        c.line(hx_, 30 - bob if not up else 16 - bob, tip[0], tip[1], GREY, 2)
        c.line(hx_ + 1, 29 - bob if not up else 15 - bob, tip[0], tip[1] + 1, WHITE, 1)
        c.rect(hx_ - 2, (30 if not up else 16) - bob, hx_ + 2, (31 if not up else 17) - bob, GOLD)
        c.line(cx - 6, 23 - bob, cx - 9, 33 - bob, WHITE, 2)
    elif mode in ("aim", "fire") or not back:
        if side or diag:
            c.line(cx + 2, 23 - bob, cx + 12, 28 - bob, WHITE, 2)
            c.line(cx + 4, 26 - bob, cx + 26, 24 - bob, BARK, 3)
            c.rect(cx + 24, 23 - bob, cx + 29, 24 - bob, GREY)
        else:
            c.line(cx - 8, 23 - bob, cx - 5, 32 - bob, WHITE, 2)
            c.line(cx + 8, 23 - bob, cx + 4, 32 - bob, WHITE, 2)
            if mode in ("aim", "fire"):
                c.ellipse(cx, 31 - bob, 3, 3, BARK)
                c.ellipse(cx, 31 - bob, 1.5, 1.5, K)
            else:
                c.line(cx - 10, 36 - bob, cx + 12, 22 - bob, BARK, 3)
    else:
        c.line(cx - 8, 23 - bob, cx - 9, 34 - bob, WHITE, 2)
        c.line(cx + 8, 23 - bob, cx + 9, 34 - bob, WHITE, 2)
        c.line(cx - 10, 14 - bob, cx + 10, 36 - bob, BARK, 3)
    # Череп.
    hx = cx + (2 if side else (1 if diag else 0))
    c.ellipse(hx, 14 - bob, 6 if not side else 5, 6, WHITE)
    c.rect(hx - 3, 18 - bob, hx + 3, 20 - bob, WHITE)
    if not back:
        if side:
            c.ellipse(hx + 2, 13 - bob, 1.5, 1.5, K)
            c.rect(hx + 3, 18 - bob, hx + 4, 18 - bob, K)
        else:
            for e in (-2.5, 2.5):
                c.ellipse(hx + e + (1 if diag else 0), 13 - bob, 1.6, 1.6, K)
            for t in range(-2, 3, 2):
                c.set(hx + t, 19 - bob, K)
            if mode == "fire":
                c.ellipse(hx + 2.5, 13 - bob, 1, 1, RED)
    if cutlass:
        _bandana(c, hx, 4 - bob, side, back)
    else:
        _hat(c, hx, 4 - bob, side, back)
    c.finish()
    if mode == "fire":
        # Вспышка выстрела у ствола.
        fx, fy = (cx + 30, 24 - bob) if side or diag else (cx, 31 - bob)
        c.ellipse(fx, fy, 5, 4, GOLD)
        c.ellipse(fx, fy, 2.5, 2, WHITE)
    if mode == "hurt":
        for x in range(T):
            for y in range(T):
                if c.get(x, y) == WHITE:
                    c.set(x, y, RED if (x + y) % 3 == 0 else WHITE)
    return c


def skeleton_strips():
    out = {}
    for name, cut in (("skel", False), ("cut", True)):
        walk = []
        for a in range(5):
            for ph in range(2):
                walk.append(skeleton(a, ph, "walk", cut))
        out[name + "_walk"] = strip(walk)
        out[name + "_die"] = strip([skeleton(0, 0, "die%d" % k, cut) for k in range(3)])
    out["skel_fire"] = strip([skeleton(0, 0, "aim"), skeleton(0, 0, "fire")])
    out["cut_slash"] = strip([skeleton(0, 0, "walk", True), skeleton(0, 0, "slash", True)])
    return out


# --- Предметы, оружие, лицо --------------------------------------------------------------------

def shot():
    c = Canvas(16, 16)
    c.ellipse(8, 8, 6, 6, RED)
    c.ellipse(8, 8, 4, 4, GOLD)
    c.ellipse(7, 7, 2, 2, WHITE)
    return c


def bullet():
    """Пуля героя: свинцовый шарик с белым бликом и золотым следом."""
    c = Canvas(16, 16)
    c.ellipse(8, 8, 3.5, 3.5, GREY)
    c.ellipse(7, 7, 1.5, 1.5, WHITE)
    c.ellipse(8, 11, 2, 2, GOLD)
    return c.finish()


def decor(kind):
    """Ориентир зала 64×64: 0 бочки, 1 ящики, 2 фонарь на столбе, 3 пушка, 4 сундук, 5 штурвал."""
    c = Canvas(T, T)
    if kind == 0:
        for bx, by in ((18, 62), (44, 62), (31, 40)):
            c.ellipse(bx, by - 11, 11, 12, WOOD)
            c.rect(bx - 11, by - 17, bx + 11, by - 16, GREY)
            c.rect(bx - 11, by - 6, bx + 11, by - 5, GREY)
    elif kind == 1:
        for x0, y0, w in ((6, 34, 26), (34, 38, 24), (16, 10, 26)):
            c.rect(x0, y0, x0 + w, y0 + 24, WOOD)
            c.line(x0, y0, x0 + w, y0 + 24, TAN, 1)
            c.line(x0 + w, y0, x0, y0 + 24, TAN, 1)
            c.rect(x0, y0, x0 + w, y0 + 1, BARK)
    elif kind == 2:
        c.rect(30, 20, 33, 63, BARK)
        c.rect(24, 6, 39, 22, BRASS)
        c.rect(26, 8, 37, 20, GOLD)
        c.ellipse(31.5, 14, 3, 4, WHITE)
        c.rect(22, 4, 41, 6, K)
    elif kind == 3:
        c.ellipse(20, 54, 9, 9, BARK)
        c.ellipse(44, 54, 9, 9, BARK)
        c.rect(10, 40, 54, 50, WOOD)
        c.poly([(14, 40), (58, 30), (60, 38), (16, 46)], K)
        c.ellipse(58, 34, 4, 5, GREY)
    elif kind == 4:
        c.rect(10, 34, 54, 62, WOOD)
        c.ellipse(32, 34, 22, 10, WOOD)
        c.rect(10, 34, 54, 36, BARK)
        for x in (16, 47):
            c.rect(x, 26, x + 2, 62, BRASS)
        c.rect(29, 37, 35, 44, GOLD)
    else:
        c.rect(30, 30, 33, 63, BARK)
        c.ellipse(31.5, 26, 18, 18, WOOD)
        c.ellipse(31.5, 26, 13, 13, None)
        import math as _m
        for a in range(0, 360, 45):
            r = _m.radians(a)
            c.line(31.5, 26, 31.5 + _m.cos(r) * 22, 26 + _m.sin(r) * 22, BARK, 2)
        c.ellipse(31.5, 26, 4, 4, BRASS)
    return c.finish()


def key():
    c = Canvas(32, 32)
    c.ellipse(10, 16, 7, 7, GOLD)
    c.ellipse(10, 16, 3, 3, None)
    c.rect(16, 14, 29, 17, GOLD)
    c.rect(24, 18, 25, 22, GOLD)
    c.rect(28, 18, 29, 21, GOLD)
    c.rect(16, 14, 29, 14, WHITE)
    return c.finish()


def medkit():
    """Сундучок с красным крестом."""
    c = Canvas(32, 32)
    c.rect(4, 12, 27, 29, WHITE)
    c.rect(4, 10, 27, 13, GREY)
    c.rect(13, 6, 18, 10, GREY)
    c.rect(13, 15, 18, 27, RED)
    c.rect(9, 18, 22, 23, RED)
    return c.finish()


def pistol(frame):
    """Пистоль в руке снизу по центру, 128×96: рука в рукаве тельняшки, кремнёвый пистоль
    стволом вглубь; кадр 1 со вспышкой."""
    c = Canvas(128, 96)
    for y in range(60, 96):
        w = 18 + (y - 60) // 2
        for x in range(64 - w, 64 + w):
            c.set(x, y, WHITE if ((y // 4) % 2 == 0) else SEA)
    c.ellipse(64, 56, 16, 12, SKIN)
    c.rect(52, 50, 76, 60, SKIN)
    for k in range(4):
        c.rect(52 + k * 6, 46, 56 + k * 6, 52, SKIN)
        c.rect(52 + k * 6, 46, 56 + k * 6, 46, TAN)
    c.poly([(56, 46), (72, 46), (70, 18), (58, 18)], BARK)
    c.poly([(58, 40), (70, 40), (68, 22), (60, 22)], WOOD)
    c.rect(60, 4, 68, 22, GREY)
    c.rect(61, 4, 62, 22, WHITE)
    c.rect(59, 2, 69, 6, BRASS)
    c.rect(70, 30, 76, 34, BRASS)
    c.finish()
    if frame:
        c.ellipse(64, 0, 18, 10, GOLD)
        c.ellipse(64, 0, 10, 6, WHITE)
    return c


def face(mode):
    """Лицо матроса для HUD, 32×32: 0 прямо, 1 глянул влево, 2 вправо, 3 больно, 4 ухмылка."""
    c = Canvas(32, 32)
    c.ellipse(16, 17, 11, 13, SKIN)
    c.ellipse(16, 8, 12, 7, RED)
    c.rect(4, 8, 28, 10, RED)
    c.rect(26, 10, 30, 14, RED)
    look = {0: 0, 1: -2, 2: 2, 3: 0, 4: 0}[mode]
    for e in (-5, 5):
        if mode == 3:
            c.line(16 + e - 2, 15, 16 + e + 2, 17, K, 1)
            c.line(16 + e - 2, 17, 16 + e + 2, 15, K, 1)
        else:
            c.rect(16 + e - 2, 14, 16 + e + 2, 17, WHITE)
            c.rect(16 + e + look - 1, 15, 16 + e + look, 17, K)
    c.rect(15, 18, 17, 22, TAN)
    if mode == 4:
        c.rect(10, 24, 22, 26, WHITE)
        c.rect(10, 24, 22, 24, K)
        c.set(9, 23, K)
        c.set(23, 23, K)
    elif mode == 3:
        c.ellipse(16, 26, 4, 2.5, K)
        c.rect(20, 18, 21, 22, RED)
    else:
        c.rect(12, 25, 20, 25, K)
    c.rect(9, 27, 13, 30, BARK)
    return c.finish()


def textures():
    return {"wall_planks": tex_planks(), "wall_stone": tex_stone(), "wall_pillar": tex_pillar(),
            "wall_exit": tex_exit(), "wall_cabin": tex_cabin(), "wall_hull": tex_hull(), "wall_cargo": tex_cargo(),
            "floor_planks": tex_floor(), "floor_stone": tex_floor_stone(), "floor_carpet": tex_carpet(),
            "ceiling_beams": tex_ceiling()}


def sprites():
    out = {"shot": shot(), "bullet": bullet(), "key": key(), "medkit": medkit(),
           "hold_decor": strip([decor(k) for k in range(6)]),
           "pistol": strip([pistol(0), pistol(1)]),
           "face": strip([face(i) for i in range(5)])}
    out.update(skeleton_strips())
    out.update(textures())
    return out
