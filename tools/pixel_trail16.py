"""Рисунок платформера × 16/32-bit «тропа» (#98) для pixel_sprites16.py. Композиция и плотность
деталей по референсу лесного платформера (решение 2026-11-12): фон без неба, лес в три слоя
(бледная даль, большие деревья с подробной корой и кроной наверху, яркие кусты у земли) и
листва над кадром спереди; земля из булыжного грунта с травяной кромкой; трава, папоротники,
цветы, камни перед героем и за ним. Фон собран из повторяющихся ассетов (дерево, куст, лист).

У фона и переднего плана свои палитры по 16 цветов (`PIRATES_BG`, `PIRATES_FG`), как у слоёв
16-битных приставок; герой, враги, монеты в палитре спрайтов. Ленты фона 512 пикселей шириной
стыкуются по краям. Случайность с постоянным зерном: картинка одна и та же.
"""
import math
import random

from pixel_sprites16 import (Canvas, strip, _stripes, K, NAVY, SEA, AQUA, WHITE, GREY, SKIN, TAN, GOLD, BRASS,
                             WOOD, BARK, RED, LEAF, PINE)

# Палитра фона: дымка дали, листва, кора, тени, цветы.
HZ0, HZ1, HZ2, HZ3, L0, L1, L2, L3, L4, T0, T1, T2, DK, FL1, FL2, MO = range(16)
PIRATES_BG = [
    (0xCC, 0xEC, 0xBE),  # HZ0  просвет в дали
    (0xA2, 0xD8, 0xA6),  # HZ1  дальняя листва, свет
    (0x78, 0xBE, 0x8E),  # HZ2  дальняя листва
    (0x56, 0x9C, 0x7E),  # HZ3  дальние стволы
    (0xD6, 0xF0, 0x6E),  # L0   блик листа
    (0x9A, 0xD6, 0x46),  # L1   лист
    (0x5A, 0xAE, 0x3A),  # L2
    (0x2E, 0x80, 0x38),  # L3
    (0x1A, 0x56, 0x32),  # L4   глубокая тень листвы
    (0x9C, 0x6C, 0x4A),  # T0   кора, свет
    (0x6E, 0x46, 0x34),  # T1   кора
    (0x48, 0x2C, 0x28),  # T2   кора, тень
    (0x14, 0x24, 0x1E),  # DK   самая тёмная тень
    (0xF2, 0xD6, 0x5C),  # FL1  жёлтые цветы, искры
    (0xE8, 0x6A, 0x7C),  # FL2  розовые цветы
    (0x3C, 0x9A, 0x6C),  # MO   мох, бирюзовая листва
]

# Палитра переднего плана: трава, булыжный грунт, камень, дерево, цветы.
FK, G0, G1, G2, G3, S0, S1, S2, S3, S4, ST0, ST1, W0, W1, W2, PINK = range(16)
PIRATES_FG = [
    (0x1A, 0x12, 0x1E),  # FK   обводка
    (0xCE, 0xF0, 0x6A),  # G0   кромка травы
    (0x86, 0xD0, 0x40),  # G1   трава
    (0x46, 0xA0, 0x34),  # G2
    (0x24, 0x68, 0x30),  # G3   тень травы
    (0x8C, 0x6C, 0x58),  # S0   булыжник, свет
    (0x6C, 0x4C, 0x3E),  # S1   булыжник
    (0x4E, 0x36, 0x32),  # S2   грунт
    (0x36, 0x24, 0x2A),  # S3   тень грунта
    (0x24, 0x18, 0x1E),  # S4   щели
    (0xB2, 0xBA, 0xC2),  # ST0  камень
    (0x7A, 0x82, 0x90),  # ST1  тень камня
    (0xC8, 0x9C, 0x64),  # W0   дерево, свет
    (0x8E, 0x5E, 0x3C),  # W1   дерево
    (0x5C, 0x3A, 0x2A),  # W2   тень дерева
    (0xF0, 0x6A, 0x8C),  # PINK цветы
]


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wellipse(c, cx, cy, rx, ry, col, keep=None):
    """Эллипс на ленте, которая стыкуется по краям; `keep` красит только поверх этого цвета."""
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                if keep is None or c.get(int(x) % c.w, y) == keep:
                    _wset(c, x, y, col)


def _foliage(c, rng, cx, cy, r, cols, leaves=1.0):
    """Ком листвы: тень, тело, свет сверху слева, потом мелкие листья по краю и телу.
    `cols` от светлого к тёмному: блик, свет, тело, тень."""
    hi, light, body, shade = cols
    _wellipse(c, cx + r * 0.1, cy + r * 0.15, r, r * 0.82, shade)
    _wellipse(c, cx, cy, r * 0.92, r * 0.74, body)
    _wellipse(c, cx - r * 0.22, cy - r * 0.25, r * 0.62, r * 0.46, light)
    # Листья: короткие штрихи по кругу, свет сверху, тень снизу.
    for _ in range(int(r * r * 0.35 * leaves)):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0.3, 1.0) * r
        x = cx + math.cos(a) * d
        y = cy + math.sin(a) * d * 0.8
        top = math.sin(a) < -0.2
        col = (hi if rng.random() < 0.35 else light) if top else (shade if rng.random() < 0.6 else body)
        dx = 1 if rng.random() < 0.5 else -1
        for k in range(3):
            _wset(c, x + dx * k, int(y + (k // 2)), col)


def _bark(c, x0, x1, y0, y1, cols, rng):
    """Ствол с корой: светлый край слева, борозды, сучки; `cols` свет, тело, тень."""
    light, body, shade = cols
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            k = (x - x0) / max(x1 - x0, 1)
            col = light if k < 0.18 else (body if k < 0.72 else shade)
            _wset(c, x, y, col)
    for gx in range(int(x0) + 4, int(x1) - 2, 5):
        ph = rng.uniform(0, 6)
        for y in range(int(y0), int(y1)):
            wob = int(round(math.sin(y * 0.18 + ph) * 1.3))
            if (y + gx) % 11 < 8:
                _wset(c, gx + wob, y, shade)
    for _ in range(int((y1 - y0) / 40) + 1):
        ky = rng.uniform(y0 + 10, y1 - 10)
        kx = rng.uniform(x0 + 4, x1 - 6)
        _wellipse(c, kx, ky, 2.5, 3.5, shade)
        _wellipse(c, kx - 0.5, ky - 0.5, 1.2, 2, light)


# --- Фон ---------------------------------------------------------------------------------------

def par3_back():
    """Дальний лес на весь экран, 512×277: просветы дымкой, тонкие стволы, бледная листва."""
    rng = random.Random(41)
    c = Canvas(512, 277)
    c.rect(0, 0, 511, 276, HZ0)
    for x in range(0, 512, 9):
        _wellipse(c, x, rng.uniform(150, 180), rng.uniform(14, 24), rng.uniform(26, 40), HZ1)
    for _ in range(26):
        x = rng.uniform(0, 512)
        w = rng.uniform(3, 7)
        for y in range(40, 277):
            for dx in range(int(w)):
                _wset(c, x + dx, y, HZ3 if dx > w * 0.5 else HZ2)
    for _ in range(46):
        _foliage(c, rng, rng.uniform(0, 512), rng.uniform(-10, 95), rng.uniform(14, 26), (HZ0, HZ1, HZ2, HZ3), 0.6)
    for x in range(0, 512, 12):
        _foliage(c, rng, x + rng.uniform(-4, 4), rng.uniform(205, 235), rng.uniform(14, 22), (HZ0, HZ1, HZ2, HZ3), 0.6)
    c.rect(0, 238, 511, 276, HZ3)
    return c


def par3_trees():
    """Большие деревья, 512×277, прозрачно между ними: подробная кора, корни, крона сверху
    сплошной полосой, лианы с кроны."""
    rng = random.Random(42)
    c = Canvas(512, 277)
    for x, w in ((40, 30), (196, 22), (300, 38), (452, 26)):
        _bark(c, x, x + w, 40, 262, (T0, T1, T2), rng)
        # Корни расходятся к земле.
        for side in (-1, 1):
            for i in range(14):
                yy = 248 + i
                spread = int(i * 0.9)
                if side < 0:
                    c.rect(max(x - spread, 0), yy, x + 3, yy, T1)
                else:
                    c.rect(x + w - 3, yy, min(x + w + spread, 511), yy, T2)
    cols = (L1, L2, L3, L4)
    for x in range(0, 512, 16):
        _foliage(c, rng, x + rng.uniform(-6, 6), rng.uniform(18, 52), rng.uniform(18, 30), cols, 1.0)
    for x in range(0, 512, 24):
        _foliage(c, rng, x + rng.uniform(-6, 6), rng.uniform(-6, 18), rng.uniform(18, 26), (L2, L3, L4, DK), 0.8)
    for _ in range(9):
        x = rng.uniform(0, 512)
        length = rng.uniform(40, 110)
        for y in range(40, int(40 + length)):
            _wset(c, x + math.sin(y * 0.08) * 2, y, MO if y % 7 else L2)
            if y % 9 == 0:
                _wset(c, x + math.sin(y * 0.08) * 2 + 1, y, L1)
    return c


def par3_bushes():
    """Яркие кусты у земли, 512×120, прозрачный верх; низ сплошной."""
    rng = random.Random(43)
    c = Canvas(512, 120)
    for x in range(0, 512, 15):
        _foliage(c, rng, x + rng.uniform(-5, 5), rng.uniform(52, 82), rng.uniform(16, 26), (L0, L1, L2, L3), 1.2)
    c.rect(0, 92, 511, 119, L3)
    for _ in range(300):
        x = rng.uniform(0, 512)
        y = rng.uniform(92, 119)
        _wset(c, x, int(y), L4 if rng.random() < 0.6 else L2)
    for _ in range(40):
        x = rng.uniform(0, 512)
        y = rng.uniform(40, 100)
        if c.get(int(x) % 512, int(y)) in (L1, L2):
            _wset(c, x, int(y), FL1 if rng.random() < 0.6 else FL2)
    return c


def canopy_front():
    """Листва над кадром спереди, 256×56, прозрачный низ: тёмные листья свисают сверху."""
    rng = random.Random(44)
    c = Canvas(256, 56)
    for x in range(0, 256, 14):
        _foliage(c, rng, x + rng.uniform(-4, 4), rng.uniform(-8, 10), rng.uniform(12, 22), (L2, L3, L4, DK), 0.9)
    for _ in range(14):
        x = rng.uniform(0, 256)
        n = rng.randint(14, 40)
        for y in range(8, n):
            _wset(c, x + math.sin(y * 0.2) * 1.5, y, L4)
            if y % 5 == 0:
                _wset(c, x + math.sin(y * 0.2) * 1.5 + 1, y, L3)
    return c


# --- Передний план -----------------------------------------------------------------------------

def trail_soil():
    """Булыжный грунт, 64×64 по кругу в обе стороны: камни разного размера вразбежку рядами,
    свет сверху слева, тень снизу, тёмные щели между ними."""
    rng = random.Random(51)
    n = 64
    c = Canvas(n, n)
    c.rect(0, 0, n - 1, n - 1, S4)

    def stone(cx, cy, rx, ry):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d > 1.0:
                    continue
                lit = ((x - cx + rx * 0.35) / (rx * 0.55)) ** 2 + ((y - cy + ry * 0.45) / (ry * 0.45)) ** 2 <= 1.0
                col = S0 if lit else (S3 if y > cy + ry * 0.55 else (S2 if d > 0.6 else S1))
                c.set(x % n, y % n, col)

    y = 0.0
    while y < n:
        h = rng.uniform(3.2, 4.6)
        x = rng.uniform(0, 8)
        while x < n:
            w = rng.uniform(4.5, 8.0)
            stone(x + w, y + h, w - 0.6, h - 0.5)
            x += 2 * w + rng.uniform(0.5, 1.5)
        y += 2 * h + rng.uniform(0.3, 1.0)
    for _ in range(40):
        c.set(rng.randrange(n), rng.randrange(n), S3)
    return c


def trail_edge():
    """Травяная кромка, 32×18 по кругу: поверхность на строке 4, травинки над ней, кромка,
    трава свисает бахромой в грунт; ниже прозрачно, там грунт."""
    rng = random.Random(52)
    c = Canvas(32, 18)
    top = 4
    for x in range(32):
        hang = top + 4 + int(1.5 + 1.5 * math.sin(x * 0.9) + rng.uniform(0, 2.5))
        c.rect(x, top, x, hang, G1)
        c.rect(x, top, x, top, G0)
        if x % 3 == 0:
            c.set(x, top + 1, G0)
        c.set(x, hang, G2)
        c.set(x, hang + 1, G3)
        if rng.random() < 0.45:
            h = rng.randint(1, 3)
            c.rect(x, top - h, x, top - 1, G1 if rng.random() < 0.5 else G0)
    return c


def arch_bark():
    """Кора ствола-арки, 32×32 по кругу."""
    rng = random.Random(53)
    c = Canvas(32, 32)
    c.rect(0, 0, 31, 31, W1)
    for gx in (2, 9, 16, 23, 29):
        for y in range(32):
            wob = int(round(math.sin(y * 2 * math.pi / 32 * 2 + gx) * 1.2))
            c.set((gx + wob) % 32, y, W2)
            c.set((gx + wob + 1) % 32, y, W2 if (y + gx) % 7 else FK)
            c.set((gx + wob - 2) % 32, y, W0 if (y + gx) % 6 < 2 else W1)
    for _ in range(4):
        x = rng.randint(0, 31)
        y = rng.randint(0, 31)
        for dx in range(-2, 3):
            for dy in range(-1, 2):
                if rng.random() < 0.7:
                    c.set((x + dx) % 32, (y + dy) % 32, G2 if dy < 1 else G3)
    return c


def arch_root(right):
    """Корень у края арки, 32×48: расходится к земле, низ на строке 47."""
    c = Canvas(32, 48)
    for y in range(48):
        k = y / 47.0
        w = 14 + int(16 * k * k)
        x0 = 0 if not right else 31 - w
        c.rect(x0, y, x0 + w, y, W1)
        c.set(x0 + (w if not right else 0), y, W2)
        c.set(x0 + (w - 1 if not right else 1), y, W2)
    for i in range(3):
        x = 6 + i * 7
        for y in range(48):
            c.set(x if not right else 31 - x, y, W2)
            c.set((x - 1) if not right else 32 - x, y, W0 if y % 6 < 3 else W1)
    for x in range(32):
        if c.get(x, 2) is not None and x % 4:
            c.rect(x, 0, x, 1 + (x % 3), G2)
    c.outline(FK)
    return c


def arch_lip():
    """Нижний край ствола над просветом, 32×10: корни бахромой, мох свисает."""
    rng = random.Random(54)
    c = Canvas(32, 10)
    for x in range(32):
        d = 3 + int(2 + 2 * math.sin(x * 2 * math.pi / 32 * 3)) + rng.randint(0, 1)
        c.rect(x, 0, x, d, W1)
        c.set(x, d, W2)
        c.set(x, d + 1, FK)
        if rng.random() < 0.25:
            c.rect(x, d - 1, x, d + rng.randint(1, 3), G2)
    return c


def _blade(c, x, h, bend, col, side):
    for j in range(int(h)):
        k = j / h
        c.set(x + bend * k * k, c.h - 1 - j, col)
        if k < 0.55:
            c.set(x + bend * k * k + 1, c.h - 1 - j, side)


def dec_grass(i):
    """Высокая трава перед героем, 32×24, два кадра на ветру."""
    rng = random.Random(61)
    c = Canvas(32, 24)
    for _ in range(16):
        x = rng.uniform(2, 30)
        col = rng.choice((G1, G2, G1, G0))
        _blade(c, x, rng.uniform(9, 22), rng.uniform(-3, 3) + (1.5 if i else -0.5), col, G3 if col == G2 else G2)
    return c


def dec_tuft(i):
    rng = random.Random(62)
    c = Canvas(32, 14)
    for _ in range(10):
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 11), rng.uniform(-2, 2) + (1 if i else 0), rng.choice((G0, G1, G2)), G3)
    return c


def dec_fern():
    """Папоротник за героем, 48×32: веер листьев из одной точки."""
    rng = random.Random(63)
    c = Canvas(48, 32)
    for ang in (-170, -145, -120, -95, -70, -45, -20, -5):
        a = math.radians(ang + rng.uniform(-6, 6))
        length = rng.uniform(16, 24)
        for i in range(int(length)):
            k = i / length
            x = 24 + math.cos(a) * i
            y = 31 + math.sin(a) * i * 0.9 + k * k * 10
            c.set(x, y, G2)
            if 0.15 < k < 0.95 and i % 2 == 0:
                w = int(4 * math.sin(math.pi * k)) + 1
                for d in range(1, w + 1):
                    c.set(x - math.sin(a) * d * 0.6, y - d * 0.5, G1 if d < w else G0)
                    c.set(x + math.sin(a) * d * 0.6, y + d * 0.3, G3)
    c.outline(FK)
    return c


def dec_bush():
    """Куст за героем, 64×36: листва в три тона с бликами, у земли тень."""
    rng = random.Random(64)
    c = Canvas(64, 36)
    for cx, cy, r in ((14, 24, 12), (30, 16, 16), (48, 22, 13), (22, 28, 10), (40, 28, 11)):
        c.ellipse(cx, cy, r, r * 0.85, G2)
    c.rect(4, 31, 58, 35, G3)
    cells = [(x, y) for y in range(36) for x in range(64) if c.px[y][x] == G2]
    for _ in range(320):
        x, y = cells[rng.randrange(len(cells))]
        col = G1 if c.get(x, y - 3) is None or rng.random() < 0.35 else G3
        for dx, dy in ((0, 0), (1, 0), (1, 1)):
            if c.get(x + dx, y + dy) is not None:
                c.set(x + dx, y + dy, col)
    for _ in range(26):
        x, y = cells[rng.randrange(len(cells))]
        if y < 22:
            c.set(x, y, G0)
    for _ in range(5):
        x, y = cells[rng.randrange(len(cells))]
        c.set(x, y, PINK)
    c.outline(FK)
    return c


def dec_rock():
    c = Canvas(32, 20)
    c.poly([(3, 19), (2, 12), (8, 6), (16, 4), (24, 7), (29, 13), (29, 19)], ST1)
    c.poly([(5, 12), (9, 7), (16, 5), (22, 7), (16, 11), (9, 13)], ST0)
    c.line(15, 13, 21, 18, FK, 1)
    c.rect(0, 18, 31, 19, None)
    c.poly([(1, 19), (6, 15), (10, 19)], G2)
    c.poly([(22, 19), (27, 14), (31, 19)], G1)
    c.outline(FK)
    return c


def dec_flowers():
    rng = random.Random(65)
    c = Canvas(32, 20)
    for _ in range(9):
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 9), rng.uniform(-2, 2), rng.choice((G1, G2)), G3)
    for x, y in ((6, 9), (14, 6), (22, 10), (27, 7)):
        c.line(x, y + 2, x, 19, G2, 1)
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            c.set(x + dx, y + dy, PINK)
        c.set(x, y, W0)
    return c


def dec_mush():
    """Грибы у корней, 32×16: три шляпки, светлые точки."""
    c = Canvas(32, 16)
    for x, h, r in ((8, 8, 5), (17, 12, 6), (25, 6, 4)):
        c.rect(x - 1, 15 - h, x + 1, 15, W0)
        c.ellipse(x, 15 - h, r, r * 0.6, PINK)
        c.rect(x - r, 15 - h + 1, x + r, 15 - h + 2, None)
        c.set(x - 2, 15 - h - 1, W0)
        c.set(x + 1, 15 - h - 2, W0)
    c.outline(FK)
    return c


# --- Герой и враги (палитра спрайтов) ----------------------------------------------------------

def _head(c, x, y, face=1):
    """Голова матроса с банданой, лицом вправо."""
    c.ellipse(x, y, 5, 5, SKIN)
    for yy in range(int(y - 6), int(y - 1)):
        for xx in range(int(x - 6), int(x + 7)):
            if c.get(xx, yy) == SKIN:
                c.set(xx, yy, RED)
    c.rect(x - 7 * face, y - 2, x - 6 * face, y, RED)


def sailor_slide(i):
    """Слайд: матрос почти лежит, ноги вперёд, корпус откинут; два кадра, пыль из-под ног."""
    c = Canvas()
    y0 = 24
    c.line(20, y0 + 3, 29, y0 + 4, SEA, 4)
    c.line(19, y0 + 1, 28, y0 + 1 - i, NAVY, 3)
    c.rect(28, y0 + 3, 31, y0 + 5, BARK)
    c.rect(27, y0 - i, 30, y0 + 1 - i, BARK)
    for k in range(6):
        c.line(8 + k, y0 - 2 - k // 2, 19 + k // 2, y0 + 2, WHITE if k % 2 == 0 else SEA, 1)
    c.line(9, y0 - 1, 15, y0 + 5, TAN, 3)
    c.line(12, y0 - 3, 4, y0 + 2, SKIN, 3)
    _head(c, 9, y0 - 8)
    c.finish()
    c.set(12, y0 - 9, K)
    for k, (x, y) in enumerate(((2, 29), (5, 30), (1, 27))):
        if (k + i) % 2 == 0:
            c.set(x, y, GREY)
    return c


def sailor_hang(i):
    """На лиане: руки вверх к точке хвата (центр сверху), ноги свисают и качаются."""
    c = Canvas()
    sw = (-1, 1)[i]
    c.line(14, 12, 15, 1, TAN, 3)
    c.line(18, 12, 17, 1, SKIN, 3)
    _stripes(c, 11, 11, 20, 20)
    for sign, cloth in ((-1, NAVY), (1, SEA)):
        foot = (15.5 + sign * 2 + sw * 2, 29)
        c.line(15.5 + sign * 2, 20, foot[0], foot[1], cloth, 3)
        c.rect(foot[0] - 1, foot[1], foot[0] + 2, foot[1] + 1, BARK)
    c.finish()
    hd = Canvas()
    _head(hd, 16, 8)
    hd.finish()
    hd.set(19, 8, K)
    for y in range(hd.h):
        for x in range(hd.w):
            if hd.px[y][x] is not None and y >= 2:
                c.set(x, y, hd.px[y][x])
    return c


def crab(i):
    """Краб, четыре кадра: ноги по очереди, клешни щёлкают, глаза на стебельках."""
    c = Canvas()
    for k in range(3):
        for sign in (-1, 1):
            lift = 1 if (k + i) % 2 == 0 else 0
            x = 16 + sign * (6 + k * 3)
            c.line(16 + sign * (3 + k * 2), 24, x, 30 - lift, BARK, 2)
    c.ellipse(16, 23, 10, 5.5, RED)
    c.ellipse(16, 21.5, 7, 3, WOOD)
    for sign in (-1, 1):
        open_ = 1 + (i % 2)
        cx = 16 + sign * 11
        c.line(16 + sign * 7, 22, cx, 16, RED, 2)
        c.ellipse(cx, 14, 3.5, 3, RED)
        c.rect(cx - 1, 10 - open_, cx + 1, 11 - open_ + 1, RED)
        c.rect(cx + sign * 2, 10 - open_, cx + sign * 2, 12, RED)
    for sign in (-1, 1):
        c.line(16 + sign * 3, 19, 16 + sign * 3, 15, BARK, 1)
        c.ellipse(16 + sign * 3, 14, 1.5, 1.5, WHITE)
    c.finish()
    c.set(16 - 3, 14, K)
    c.set(16 + 3, 14, K)
    return c


def parrot(i):
    """Попугай летит вправо: красное тело, крыло синее с золотом, длинный хвост; четыре кадра
    взмаха (вверх, середина, вниз, середина)."""
    c = Canvas()
    wing = (-9, -2, 6, -2)[i]
    c.poly([(4, 18), (12, 15), (13, 19), (5, 22)], SEA)
    c.line(1, 20, 6, 19, RED, 2)
    c.ellipse(17, 17, 7, 4.5, RED)
    c.ellipse(24, 13, 4, 4, RED)
    c.poly([(27, 12), (31, 14), (27, 16)], GOLD)
    c.set(27, 15, K)
    c.ellipse(24, 15, 2, 1.5, WHITE)
    c.poly([(13, 15), (21, 15), (17 - 4, 15 + wing), (17 + 2, 15 + wing)], SEA)
    c.line(14, 15, 15 - 2, 15 + wing * 0.7, GOLD, 2)
    c.finish()
    c.set(25, 12, K)
    return c


def sprites():
    """Ленты этой демки в палитре спрайтов."""
    return {
        "hero_slide": strip([sailor_slide(i) for i in range(2)]),
        "hero_hang": strip([sailor_hang(i) for i in range(2)]),
        "crab_walk": strip([crab(i) for i in range(4)]),
        "parrot_fly": strip([parrot(i) for i in range(4)]),
    }


def backdrop():
    """Слои фона и листва над кадром в палитре фона."""
    return {"par3_back": par3_back(), "par3_trees": par3_trees(), "par3_bushes": par3_bushes(),
            "canopy_front": canopy_front()}


def foreground():
    """Земля, арка, украшения в палитре переднего плана."""
    return {
        "trail_soil": trail_soil(),
        "trail_edge": trail_edge(),
        "arch_bark": arch_bark(),
        "arch_root": strip([arch_root(False), arch_root(True)]),
        "arch_lip": arch_lip(),
        "dec_grass": strip([dec_grass(i) for i in range(2)]),
        "dec_tuft": strip([dec_tuft(i) for i in range(2)]),
        "dec_fern": dec_fern(),
        "dec_bush": dec_bush(),
        "dec_rock": dec_rock(),
        "dec_flowers": dec_flowers(),
        "dec_mush": dec_mush(),
    }
