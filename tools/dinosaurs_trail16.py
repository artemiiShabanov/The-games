#!/usr/bin/env python3
"""Набор «Динозавры» для платформера × 16/32-bit «тропа» (#144), зеркало `space_trail16.py` и
`pixel_trail16.py`: те же ключи, размеры холстов, число кадров и точки опоры. Вместо леса и
грибов доисторические джунгли днём: фон без неба в три слоя (тёплая дымка дали с вулканом,
шеями зауроподов и силуэтами древовидных папоротников; большие саговники с ромбической
чешуёй стволов и лианами, перистые вайи сплошной полосой наверху; у земли папоротники, хвощи
и низкие саговники с рыжими шишками) и тёмные вайи над кадром спереди; земля из слоёной
красной глины с лавовой галькой, трещинами и окаменелостями под кромкой папоротниковой
подстилки; арка из гигантской кости.

Свойства слотов, на которые рассчитана демка: ленты фона 512 пикселей стыкуются по краям, у
дали и поросли низ сплошной, у больших стволов те же места и прозрачно между ними, у вай
спереди прозрачный низ; грунт 64×64 стыкуется в обе стороны, кромка 32×18 с поверхностью на
строке 4, грань арки 32×32 по кругу; украшения стоят на нижней строке холста.

У фона и переднего плана свои палитры по 16 цветов (`DINOSAURS_BG`, `DINOSAURS_FG`); трилобит
и птеродактиль в палитре спрайтов `dinosaurs16.PALETTE`, их рисует основа вместе с оранжевой
обводкой опасности. Ленты героя рисует `dinosaurs16.py`. Случайность с постоянным зерном:
картинка одна и та же.

    python3 tools/dinosaurs_trail16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dinosaurs16  # noqa: E402
from dinosaurs16 import Canvas, strip  # noqa: E402

# Палитра фона: тёплая дымка дали, вайи, чешуя стволов, тени, шишки.
HZ0, HZ1, HZ2, HZ3, L0, L1, L2, L3, L4, T0, T1, T2, DK, FL1, FL2, MO = range(16)
DINOSAURS_BG = [
    (0xEE, 0xE8, 0xB8),  # HZ0  дымка, просвет в дали
    (0xC2, 0xDA, 0xA0),  # HZ1  воздух дали
    (0x8E, 0xBC, 0x8E),  # HZ2  дальняя зелень, склон вулкана
    (0x5C, 0x96, 0x80),  # HZ3  шеи зауроподов, дальние стволы
    (0xD4, 0xEE, 0x6C),  # L0   блик вайи
    (0x8E, 0xCC, 0x44),  # L1   вайя, свет
    (0x52, 0xA4, 0x3C),  # L2   вайя
    (0x2A, 0x78, 0x3A),  # L3   вайя, тень
    (0x18, 0x50, 0x34),  # L4   глубокая тень зелени
    (0xC2, 0x8C, 0x58),  # T0   чешуя ствола, свет
    (0x8A, 0x56, 0x38),  # T1   ствол
    (0x56, 0x32, 0x28),  # T2   ствол, тень
    (0x14, 0x20, 0x1C),  # DK   самая тёмная тень
    (0xF4, 0xCC, 0x52),  # FL1  пыльца, мошки, верхушки хвощей
    (0xEC, 0x5E, 0x24),  # FL2  рыжие шишки саговников, лава вдали
    (0x2C, 0x80, 0x84),  # MO   бирюзовые хвощи
]

# Палитра переднего плана: подстилка, красная глина, лавовый камень, кость, жар.
FK, G0, G1, G2, G3, S0, S1, S2, S3, S4, ST0, ST1, W0, W1, W2, PINK = range(16)
DINOSAURS_FG = [
    (0x18, 0x10, 0x10),  # FK   обводка
    (0xD6, 0xEE, 0x72),  # G0   кромка подстилки
    (0x8E, 0xCC, 0x44),  # G1   папоротник
    (0x4E, 0x9E, 0x3C),  # G2
    (0x24, 0x68, 0x38),  # G3   тень зелени
    (0xDA, 0x8A, 0x5A),  # S0   глина, свет
    (0xB2, 0x56, 0x36),  # S1   красная глина
    (0x88, 0x3C, 0x2E),  # S2   глина, тень
    (0x5E, 0x2A, 0x26),  # S3   тёмный слой
    (0x38, 0x1A, 0x1C),  # S4   трещины
    (0x96, 0x82, 0x86),  # ST0  лавовый камень
    (0x5C, 0x48, 0x50),  # ST1  тень лавового камня
    (0xF4, 0xEE, 0xDA),  # W0   кость, свет
    (0xCC, 0xBE, 0xA2),  # W1   кость
    (0x8E, 0x7C, 0x6A),  # W2   тень кости
    (0xF4, 0x9A, 0x2C),  # PINK жар лавы, шишки, споры
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


def _frond(put, x, y, ang, length, width, cols, droop=0.03):
    """Перистая вайя: стержень из точки (x, y) под углом `ang` градусов гнётся к земле, по обе
    стороны гребёнкой листочки, к концу короче. `cols`: свет, тело, тень; верхний ряд листочков
    светлый, нижний в тени. `put(x, y, цвет)` ставит точку."""
    light, body, shade = cols
    a = math.radians(ang)
    sgn = 1.0 if math.cos(a) >= 0 else -1.0
    n = int(length)
    for j in range(n):
        k = j / max(length, 1.0)
        x += math.cos(a)
        y += math.sin(a)
        a += sgn * droop * (0.4 + k * 1.6)
        if j % 2 == 0 and j > 1:
            ll = width * (math.sin(math.pi * min(1.0, k * 0.88 + 0.1)) ** 0.7)
            for side in (-1, 1):
                la = a + side * math.radians(64)
                col = light if math.sin(la) < math.sin(a) else shade
                for t in range(1, int(ll) + 1):
                    put(x + math.cos(la) * t, y + math.sin(la) * t, col)
        put(x, y, body)


def _crown(put, rng, x, y, n, length, width, cols, droop=0.03, lo=-172, hi=-8):
    """Крона веером из `n` вай из одной точки: задние (к краям веера) идут первыми."""
    angs = [lo + (hi - lo) * (i + 0.5) / n + rng.uniform(-5, 5) for i in range(n)]
    angs.sort(key=lambda v: -abs(v + 90))
    for ang in angs:
        _frond(put, x, y, ang, length * rng.uniform(0.8, 1.1), width, cols, droop * rng.uniform(0.8, 1.25))


def _scale_trunk(c, x0, x1, y0, y1, cols, dark, step=10):
    """Ствол саговника: свет слева, ромбическая чешуя от старых черешков, блик под каждой
    бороздой."""
    light, body, shade = cols
    w = max(x1 - x0, 1)
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            u = x - int(x0)
            k = u / w
            col = light if k < 0.22 else (body if k < 0.7 else shade)
            d1 = (u + y) % step
            d2 = (u - y) % step
            if d1 == 0 or d2 == 0:
                col = dark if col == shade else shade
            elif (d1 == 1 or d2 == step - 1) and k < 0.7:
                col = light
            _wset(c, x, y, col)


def _horsetail(c, x, base, h, cols, tip=None):
    """Хвощ: членистый стебель от земли `base` вверх на `h`, на каждом узле мутовка веточек
    вверх и в стороны, к верхушке короче; наверху колосок."""
    stem, light, shade = cols
    for j in range(int(h)):
        y = int(base - j)
        _wset(c, x, y, light if j % 6 == 0 else stem)
        _wset(c, x + 1, y, stem)
        _wset(c, x + 2, y, shade)
        if j % 6 == 5:
            for dx in range(3):
                _wset(c, x + dx, y, shade)
            reach = max(3, int(10 * (1.0 - j / h) + 3))
            for t in range(1, reach + 1):
                _wset(c, x - t, y - t * 0.55, light)
                _wset(c, x - t, y - t * 0.55 + 1, stem)
                _wset(c, x + 2 + t, y - t * 0.55, stem)
                _wset(c, x + 2 + t, y - t * 0.55 + 1, shade)
    if tip is not None:
        for dy in range(5):
            _wset(c, x + 1, int(base - h - dy), tip)
            if 0 < dy < 4:
                _wset(c, x, int(base - h - dy), tip)
                _wset(c, x + 2, int(base - h - dy), tip)


# --- Фон ---------------------------------------------------------------------------------------

def _sauropod(c, x, base, h, face):
    """Силуэт зауропода вдали: спина горбом, длинная шея дугой, маленькая голова."""
    _wellipse(c, x, base, 44, 26, HZ3)
    pts = 60
    for i in range(pts + 1):
        t = i / pts
        px = x + face * (24 + 30 * t + 16 * math.sin(t * math.pi * 0.9))
        py = base - 12 - h * (t ** 0.85)
        r = 8.0 - 5.0 * t
        _wellipse(c, px, py, r, r, HZ3)
    hx = x + face * (24 + 30 + 16 * math.sin(math.pi * 0.9))
    hy = base - 12 - h
    _wellipse(c, hx + face * 2, hy, 5, 4, HZ3)
    _wellipse(c, hx + face * 7, hy + 2, 6, 3, HZ3)
    _wellipse(c, hx + face * 11, hy + 4, 3, 2, HZ3)
    # Свет по хребту со стороны солнца.
    for i in range(pts + 1):
        t = i / pts
        px = x + face * (24 + 30 * t + 16 * math.sin(t * math.pi * 0.9)) - (8.0 - 5.0 * t) + 1
        _wset(c, px, int(base - 12 - h * (t ** 0.85)), HZ2)


def par3_back():
    """Даль на весь экран, 512×277: тёплая дымка, вулкан с дымом и нитями лавы, шеи зауроподов
    над зеленью, тонкие древовидные папоротники; низ сплошной."""
    rng = random.Random(441)
    c = Canvas(512, 277)
    c.rect(0, 0, 511, 276, HZ1)
    # Дымка полосами: светлее к середине высоты.
    for x in range(0, 512, 9):
        _wellipse(c, x, rng.uniform(60, 130), rng.uniform(18, 34), rng.uniform(8, 16), HZ0)
    # Вулкан: конус со срезанной вершиной, правый склон в тени штрихом.
    vx = 372
    for y in range(52, 240):
        k = (y - 52) / 188.0
        half = 14 + 150 * (k ** 1.25)
        for x in range(int(vx - half), int(vx + half) + 1):
            u = (x - vx) / half
            col = HZ2
            if u > 0.15 and (x + y) % 2 == 0:
                col = HZ3
            if x < vx - half + 3:
                col = HZ0
            _wset(c, x, y, col)
    for x in range(vx - 9, vx + 10):
        c.rect(x, 52, x, 54 + int(2 * math.sin(x * 0.9)), HZ1)
    # Нити лавы по склону и дым столбом в сторону.
    for sx, bend in ((vx - 4, -0.32), (vx + 5, 0.24), (vx + 1, -0.06)):
        px = float(sx)
        for y in range(56, int(rng.uniform(110, 150))):
            px += bend + math.sin(y * 0.3) * 0.4
            _wset(c, px, y, FL2 if y % 5 else FL1)
    for i in range(16):
        t = i / 15.0
        _wellipse(c, vx + 6 + t * 70 + rng.uniform(-4, 4), 44 - t * 30 + rng.uniform(-3, 3), 9 + t * 13, 6 + t * 7, HZ0)
    for i in range(12):
        t = i / 11.0
        _wellipse(c, vx + 12 + t * 66, 48 - t * 28, 5 + t * 7, 3 + t * 3, HZ1, HZ0)
    # Дальняя зелень холмами.
    for x in range(0, 512, 12):
        _wellipse(c, x + rng.uniform(-4, 4), rng.uniform(206, 232), rng.uniform(16, 28), rng.uniform(22, 40), HZ2)
    # Зауроподы: двое смотрят навстречу друг другу, третий поодаль.
    _sauropod(c, 70, 232, 128, 1)
    _sauropod(c, 214, 240, 96, -1)
    _sauropod(c, 500, 236, 112, -1)
    # Птеродактили галочками в дымке.
    for bx, by in ((150, 44), (168, 58), (268, 30), (40, 70)):
        for d in range(5):
            _wset(c, bx - d, by - d * 0.6, HZ3)
            _wset(c, bx + d, by - d * 0.6, HZ3)
    # Тонкие древовидные папоротники.
    for _ in range(22):
        x = rng.uniform(0, 512)
        top = rng.uniform(96, 190)
        w = rng.uniform(3, 5)
        for y in range(int(top), 262):
            for dx in range(int(w)):
                _wset(c, x + dx, y, HZ2 if dx < 1 else HZ3)
        _crown(lambda px, py, col: _wset(c, px, int(py), col), rng, x + w / 2, top, 9, rng.uniform(20, 30), 4,
               (HZ2, HZ3, HZ3), 0.05)
    # Поросль у земли и сплошной низ.
    for x in range(0, 512, 9):
        _crown(lambda px, py, col: _wset(c, px, int(py), col), rng, x + rng.uniform(-3, 3), rng.uniform(238, 246), 7,
               rng.uniform(12, 18), 3, (HZ2, HZ3, HZ3), 0.06)
    c.rect(0, 244, 511, 276, HZ3)
    return c


def par3_trees():
    """Большие саговники, 512×277, прозрачно между ними: стволы в ромбической чешуе расходятся
    к земле, по ним вьются лианы; перистые вайи наверху сплошной полосой, из сердцевины крон
    рыжие шишки, вниз свисают лианы с листьями."""
    rng = random.Random(442)
    c = Canvas(512, 277)

    def put(px, py, col):
        _wset(c, px, int(py), col)

    trunks = ((40, 30), (196, 22), (300, 38), (452, 26))
    for x, w in trunks:
        _scale_trunk(c, x, x + w, 40, 262, (T0, T1, T2), DK, 10 if w > 24 else 8)
        # Основание расходится к земле.
        for side in (-1, 1):
            for i in range(14):
                yy = 248 + i
                spread = int(i * 0.9)
                if side < 0:
                    c.rect(max(x - spread, 0), yy, x + 3, yy, T1)
                else:
                    c.rect(x + w - 3, yy, min(x + w + spread, 511), yy, T2)
        # Лиана вокруг ствола: видна только на его передней стороне.
        ph = rng.uniform(0, 6)
        for y in range(70, 250):
            s = math.sin(y * 0.045 + ph)
            if math.cos(y * 0.045 + ph) > -0.2:
                lx = x + w / 2 + s * (w / 2 + 1)
                _wset(c, lx, y, L3)
                _wset(c, lx + 1, y, L4)
                if y % 9 == 0:
                    for d in range(1, 4):
                        _wset(c, lx - d, y - d, L2)
                        _wset(c, lx - d, y - d + 1, L3)
        # Пятна мха на тёмной стороне.
        for _ in range(4):
            _wellipse(c, x + w * rng.uniform(0.55, 0.9), rng.uniform(90, 240), rng.uniform(2, 4), rng.uniform(4, 9), L4, T2)
    # Полоса вай: тёмная глубина, дальние кроны, потом кроны над стволами.
    c.rect(0, 0, 511, 30, DK)
    for x in range(0, 512, 6):
        _wellipse(c, x, 30, 5, rng.uniform(3, 10), DK)
    for x in range(0, 512, 30):
        _crown(put, rng, x + rng.uniform(-6, 6), rng.uniform(6, 16), 9, rng.uniform(34, 46), 6, (L3, L4, DK), 0.045,
               -200, 20)
    for x in range(14, 512, 44):
        _crown(put, rng, x + rng.uniform(-8, 8), rng.uniform(22, 34), 10, rng.uniform(40, 54), 7, (L2, L3, L4), 0.04,
               -205, 25)
    for x, w in trunks:
        cx = x + w / 2
        _wellipse(c, cx, 44, w / 2 + 7, 11, L4)
        _crown(put, rng, cx, 44, 6, 34, 7, (L2, L3, L4), 0.03, 20, 160)
        _crown(put, rng, cx, 42, 12, 62, 8, (L1, L2, L3), 0.036, -212, 32)
        _crown(put, rng, cx, 40, 7, 40, 7, (L0, L1, L2), 0.034, -160, -20)
        # Шишка в сердцевине.
        _wellipse(c, cx, 37, 4, 7, FL2)
        for dy in range(-6, 7, 2):
            for dx in range(-3, 4, 2):
                if c.get(int(cx + dx + (dy // 2) % 2) % 512, 37 + dy) == FL2:
                    _wset(c, cx + dx + (dy // 2) % 2, 37 + dy, FL1 if dx < 0 else T1)
    # Свисающие лианы с парными листьями.
    for _ in range(11):
        x = rng.uniform(0, 512)
        length = rng.uniform(40, 110)
        for y in range(40, int(40 + length)):
            lx = x + math.sin(y * 0.07) * 2.5
            _wset(c, lx, y, L3 if y % 6 else L4)
            if y % 8 == 3:
                for d in (1, 2):
                    _wset(c, lx - d, y + d - 1, L2)
                    _wset(c, lx + d, y + d - 1, L3)
        ex = x + math.sin((40 + length) * 0.07) * 2.5
        _wellipse(c, ex, 40 + length, 2, 2.5, L2)
        _wset(c, ex - 1, int(40 + length - 1), L1)
    return c


def par3_bushes():
    """Поросль у земли, 512×120, прозрачный верх: розетки папоротников, бирюзовые хвощи с
    мутовками, низкие саговники с рыжей шишкой; низ сплошной."""
    rng = random.Random(443)
    c = Canvas(512, 120)

    def put(px, py, col):
        _wset(c, px, int(py), col)

    # Задний ряд темнее.
    for x in range(0, 512, 17):
        _crown(put, rng, x + rng.uniform(-5, 5), 96, 8, rng.uniform(26, 38), 5, (L3, L4, DK), 0.05)
    for x in range(0, 512, 13):
        cx = x + rng.uniform(-4, 4)
        r = rng.random()
        if r < 0.28:
            _horsetail(c, cx, 97, rng.uniform(38, 68), (MO, L1, L4), FL1 if rng.random() < 0.6 else None)
        elif r < 0.46:
            h = rng.uniform(14, 26)
            _scale_trunk(c, cx - 4, cx + 5, 96 - h, 97, (T0, T1, T2), DK, 6)
            _crown(put, rng, cx, 96 - h, 9, rng.uniform(24, 32), 5, (L0, L1, L3), 0.03, -195, 15)
            _wellipse(c, cx, 96 - h - 3, 2.5, 4, FL2)
            _wset(c, cx - 1, int(96 - h - 5), FL1)
        else:
            _crown(put, rng, cx, 97, 8, rng.uniform(24, 40), 6, (L0, L1, L2) if rng.random() < 0.5 else (L1, L2, L3),
                   0.05)
    c.rect(0, 92, 511, 119, L4)
    for x in range(0, 512, 7):
        _crown(put, rng, x + rng.uniform(-2, 2), rng.uniform(98, 104), 6, rng.uniform(9, 14), 3, (L1, L2, L3), 0.08)
    for _ in range(260):
        x = rng.uniform(0, 512)
        y = rng.uniform(104, 119)
        _wset(c, x, int(y), L3 if rng.random() < 0.6 else DK)
    for _ in range(40):
        x = rng.uniform(0, 512)
        y = rng.uniform(30, 100)
        if c.get(int(x) % 512, int(y)) is None:
            _wset(c, x, int(y), FL1)
    return c


def canopy_front():
    """Вайи над кадром спереди, 256×56, прозрачный низ: тёмные перья свисают сверху, между ними
    лианы."""
    rng = random.Random(444)
    c = Canvas(256, 56)

    def put(px, py, col):
        _wset(c, px, int(py), col)

    c.rect(0, 0, 255, 5, DK)
    for x in range(0, 256, 5):
        _wellipse(c, x, 5, 4, rng.uniform(2, 6), DK)
    for x in range(0, 256, 26):
        _crown(put, rng, x + rng.uniform(-4, 4), -4, 7, rng.uniform(30, 44), 6, (L4, DK, DK), 0.02, 18, 162)
    for x in range(13, 256, 32):
        _crown(put, rng, x + rng.uniform(-4, 4), -2, 6, rng.uniform(26, 38), 6, (L3, L4, DK), 0.02, 22, 158)
    for _ in range(9):
        x = rng.uniform(0, 256)
        n = rng.randint(22, 46)
        for y in range(4, n):
            lx = x + math.sin(y * 0.2) * 1.5
            _wset(c, lx, y, L4 if y % 5 else L3)
            if y % 7 == 2:
                _wset(c, lx - 1, y + 1, L3)
                _wset(c, lx + 1, y + 1, L4)
        _wset(c, x + math.sin(n * 0.2) * 1.5, n, L2)
    return c


# --- Передний план -----------------------------------------------------------------------------

# Высоты слоёв глины, в сумме 64: рисунок стыкуется по вертикали.
_STRATA = (6, 5, 7, 4, 6, 5, 7, 6, 5, 7, 6)


def trail_soil():
    """Красная глина, 64×64 по кругу в обе стороны: волнистые слои разного тона со светлой
    кромкой, трещины усыхания, вмятая лавовая галька, окаменелости: спираль аммонита, обломок
    хребта, косточка."""
    rng = random.Random(451)
    n = 64
    c = Canvas(n, n)
    tau = 2 * math.pi / n
    for x in range(n):
        off = 2.4 * math.sin(x * tau * 2) + 1.4 * math.sin(x * tau * 5 + 1.0)
        for y in range(n):
            yy = (y + off) % n
            acc = 0
            for bi, bh in enumerate(_STRATA):
                if yy < acc + bh:
                    v = yy - acc
                    dark = bi % 3 == 1
                    if v < 1.0:
                        col = S1 if dark else S0
                    elif v >= bh - 1.0:
                        col = S3
                    else:
                        col = S2 if dark else S1
                    c.set(x, y, col)
                    break
                acc += bh
    # Зерно глины.
    for _ in range(150):
        x, y = rng.randrange(n), rng.randrange(n)
        cur = c.get(x, y)
        c.set(x, y, S2 if cur == S1 else (S1 if cur == S2 else cur))
    # Трещины усыхания: ломаные сверху вниз.
    for _ in range(9):
        x = rng.randrange(n)
        y = rng.randrange(n)
        for _k in range(rng.randint(5, 11)):
            c.set(x % n, y % n, S4)
            y += 1
            x += rng.choice((-1, 0, 0, 1))
    # Лавовая галька: свет сверху слева, тень снизу.
    for _ in range(9):
        cx, cy = rng.uniform(0, n), rng.uniform(0, n)
        rx, ry = rng.uniform(2.2, 4.4), rng.uniform(1.6, 3.0)
        for y in range(int(cy - ry - 1), int(cy + ry + 3)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                u, v = (x - cx) / rx, (y - cy) / ry
                if u * u + v * v <= 1.0:
                    c.set(x % n, y % n, ST0 if u + v < -0.25 else ST1)
                elif u * u + ((y - 1 - cy) / ry) ** 2 <= 1.0:
                    c.set(x % n, y % n, S4)
    # Аммонит: спираль в полтора оборота.
    ax, ay = 20, 40
    for i in range(70):
        t = i / 69.0
        a = t * math.pi * 3.4
        r = 0.8 + t * 5.2
        px, py = ax + math.cos(a) * r, ay + math.sin(a) * r
        c.set(int(round(px)) % n, int(round(py)) % n, W1 if i % 4 else W2)
    c.set(ax, ay, W0)
    # Обломок хребта: позвонки рядком.
    for i in range(6):
        x = 44 + i * 3
        y = 12 + int(i * 0.5)
        c.rect(x % n, y % n, (x + 1) % n if (x + 1) % n > x % n else x % n, y % n, W1)
        c.set(x % n, (y - 1) % n, W0)
        c.set(x % n, (y + 1) % n, W2)
    # Косточка.
    for i in range(7):
        c.set((6 + i) % n, (9 - i // 3) % n, W1)
    for dx, dy in ((5, 8), (5, 10), (13, 6), (13, 8)):
        c.set(dx % n, dy % n, W0)
    return c


def trail_edge():
    """Кромка подстилки, 32×18 по кругу: поверхность на строке 4, над ней перья молодых
    папоротников, вниз листья свисают округлыми языками в грунт; ниже прозрачно, там грунт."""
    rng = random.Random(452)
    c = Canvas(32, 18)
    top = 4
    for x in range(32):
        # Языки по 8 пикселей: дуга, а не ровная бахрома.
        lobe = abs(math.sin((x + 2) * math.pi / 8.0))
        hang = top + 3 + int(round(lobe * 4.5 + rng.uniform(0, 1.2)))
        c.rect(x, top, x, hang, G1)
        c.rect(x, top, x, top, G0)
        if x % 4 == 1:
            c.set(x, top + 1, G0)
        # Жилка языка и тень между языками.
        if (x + 2) % 8 == 4:
            c.rect(x, top + 2, x, hang - 1, G2)
        if lobe < 0.4:
            c.rect(x, top + 2, x, hang, G2)
        c.set(x, hang, G2)
        c.set(x, hang + 1, G3)
        if rng.random() < 0.4:
            h = rng.randint(1, 3)
            c.rect(x, top - h, x, top - 1, G1 if rng.random() < 0.5 else G0)
            if h == 3:
                c.set((x + 1) % 32, top - 2, G2)
                c.set((x - 1) % 32, top - 3, G0)
    return c


def arch_bark():
    """Грань костяной арки, 32×32 по кругу: гладкая кость с продольными светлыми волокнами,
    тонкие трещины, поры, пятна мха."""
    rng = random.Random(453)
    n = 32
    c = Canvas(n, n)
    c.rect(0, 0, n - 1, n - 1, W1)
    # Волокна вдоль кости: светлые и тёмные нити с плавным изгибом.
    for x0 in range(0, n, 4):
        ph = rng.uniform(0, 6)
        col = W0 if (x0 // 4) % 2 == 0 else W2
        for y in range(n):
            wob = int(round(math.sin(y * 2 * math.pi / n + ph) * 1.3))
            if (y * 5 + x0 * 3) % 11 < (8 if col == W0 else 5):
                c.set((x0 + wob) % n, y, col)
            if col == W0 and (y + x0) % 7 < 4:
                c.set((x0 + wob + 1) % n, y, W0)
    # Суставные перетяжки поперёк: кость собрана из звеньев.
    for y0 in (7, 23):
        for x in range(n):
            wob = int(round(math.sin(x * 2 * math.pi / n * 2) * 1.0))
            c.set(x, (y0 + wob) % n, W2)
            c.set(x, (y0 + wob + 1) % n, W0)
    # Трещины.
    for _ in range(4):
        x, y = rng.randrange(n), rng.randrange(n)
        for _k in range(rng.randint(4, 8)):
            c.set(x % n, y % n, FK if _k % 3 else W2)
            y += 1
            x += rng.choice((-1, 0, 1))
    # Поры.
    for _ in range(14):
        c.set(rng.randrange(n), rng.randrange(n), W2)
    # Мох.
    for _ in range(3):
        x, y = rng.randrange(n), rng.randrange(n)
        for dx in range(-2, 3):
            for dy in range(-1, 2):
                if rng.random() < 0.7:
                    c.set((x + dx) % n, (y + dy) % n, G2 if dy < 1 else G3)
    return c


def _blade(c, x, h, bend, col, side, tip=None):
    for j in range(int(h)):
        k = j / h
        c.set(x + bend * k * k, c.h - 1 - j, col)
        if k < 0.55:
            c.set(x + bend * k * k + 1, c.h - 1 - j, side)
    if tip is not None:
        c.set(x + bend, c.h - int(h), tip)


def _reed(c, x, h, bend, col, side, tip=None):
    """Стебель хвоща перед героем: узлы через четыре пикселя, на узле мутовка в обе стороны."""
    for j in range(int(h)):
        k = j / h
        px = x + bend * k * k
        y = c.h - 1 - j
        c.set(px, y, side if j % 4 == 3 else col)
        if k < 0.5:
            c.set(px + 1, y, side)
        if j % 4 == 3 and 2 < j < h - 3:
            c.set(px - 1, y - 1, col)
            c.set(px - 2, y - 2, col)
            c.set(px + 2, y - 1, side)
            c.set(px + 3, y - 2, side)
    if tip is not None:
        c.set(x + bend, c.h - int(h), tip)
        c.set(x + bend, c.h - int(h) - 1, tip)


def dec_grass(i):
    """Хвощи перед героем, 32×24, два кадра качания; у части рыжий колосок на конце."""
    rng = random.Random(461)
    c = Canvas(32, 24)
    for _ in range(7):
        _blade(c, rng.uniform(2, 30), rng.uniform(5, 10), rng.uniform(-2, 2) + (1 if i else 0), G2, G3)
    for _ in range(8):
        x = rng.uniform(3, 29)
        col = rng.choice((G1, G2, G1, G0))
        tip = PINK if rng.random() < 0.45 else None
        _reed(c, x, rng.uniform(11, 21), rng.uniform(-2.5, 2.5) + (1.5 if i else -0.5), col,
              G3 if col == G2 else G2, tip)
    return c


def dec_tuft(i):
    """Молодые перья папоротника, 32×14, два кадра."""
    rng = random.Random(462)
    c = Canvas(32, 14)
    for _ in range(14):
        x = rng.uniform(3, 29)
        h = rng.uniform(5, 12)
        bend = rng.uniform(-3, 3) + (1 if i else 0)
        col = rng.choice((G0, G1, G2))
        _blade(c, x, h, bend, col, G3)
        # Листочки гребёнкой по одной стороне.
        for j in range(3, int(h) - 1, 2):
            k = j / h
            c.set(x + bend * k * k + (-1 if bend > 0 else 2), c.h - 1 - j, G2 if col != G2 else G1)
    return c


def dec_fern():
    """Низкий саговник за героем, 48×32: бочонок ствола в ромбической чешуе, жёсткие перистые
    вайи веером, в сердцевине рыжая шишка."""
    rng = random.Random(463)
    c = Canvas(48, 32)

    def put(px, py, col):
        c.set(int(round(px)), int(round(py)), col)

    # Задние вайи темнее.
    for ang, length in ((-176, 19), (-150, 21), (-30, 21), (-4, 19)):
        _frond(put, 24, 19, ang, length, 4, (G2, G3, G3), 0.03)
    # Ствол бочонком.
    for y in range(18, 32):
        half = 4 if y < 20 or y > 29 else 5
        for x in range(24 - half, 24 + half):
            u = x - 19
            k = (x - (24 - half)) / (2.0 * half)
            col = S0 if k < 0.25 else (S1 if k < 0.65 else S2)
            if (u + y) % 5 == 0 or (u - y) % 5 == 0:
                col = S3
            c.set(x, y, col)
    for ang, length in ((-128, 22), (-106, 20), (-74, 20), (-52, 22)):
        _frond(put, 24, 18, ang + rng.uniform(-3, 3), length, 4, (G0, G1, G2), 0.035)
    # Шишка.
    c.ellipse(24, 15, 2.2, 3.6, PINK)
    for x, y in ((23, 13), (25, 15), (23, 17), (24, 11)):
        c.set(x, y, S1)
    c.outline(FK)
    return c


def dec_bush():
    """Остов ящера за героем, 64×36: хребет дугой с остистыми позвонками, рёбра клеткой до
    земли (дальний ряд в тени), хвост уходит в папоротник; у земли тень."""
    rng = random.Random(464)
    c = Canvas(64, 36)

    def spine_y(x):
        return 9.0 + 0.011 * (x - 36) ** 2

    # Дальние рёбра.
    for x0 in (20, 28, 36, 44, 52):
        y0 = spine_y(x0) + 2
        for i in range(40):
            t = i / 39.0
            rx = x0 + 4 + 5.5 * math.sin(math.pi * t * 0.85)
            ry = y0 + (32 - y0) * t
            c.set(int(round(rx)), int(round(ry)), W2)
            c.set(int(round(rx)) + 1, int(round(ry)), W2)
    # Хребет и хвост.
    for x in range(4, 58):
        y = spine_y(x) if x >= 14 else spine_y(14) + (14 - x) * 1.55
        yi = int(round(y))
        thick = 3 if x >= 14 else 2
        c.rect(x, yi, x, yi + thick - 1, W1)
        c.set(x, yi, W0)
        c.set(x, yi + thick - 1, W2)
        # Остистые отростки и швы между позвонками.
        if x >= 12 and x % 4 == 0:
            c.rect(x, yi - 3, x, yi - 1, W0)
            c.set(x + 1, yi - 2, W1)
            c.set(x + 2, yi + 1, W2)
    # Ближние рёбра: дугой наружу и обратно к земле.
    for x0 in (16, 24, 32, 40, 48):
        y0 = spine_y(x0) + 2
        for i in range(48):
            t = i / 47.0
            rx = x0 - 1 + 7.0 * math.sin(math.pi * t * 0.85)
            ry = y0 + (33 - y0) * t
            xi, yi = int(round(rx)), int(round(ry))
            c.set(xi, yi, W0)
            c.set(xi + 1, yi, W1)
            c.set(xi + 2, yi, W2)
    c.outline(FK)
    # Папоротник и тень у земли поверх концов рёбер.
    c.rect(3, 33, 60, 35, G3)
    for x in range(3, 61):
        if rng.random() < 0.55:
            c.set(x, 32, G2)
        if rng.random() < 0.3:
            c.rect(x, 30, x, 31, G1 if rng.random() < 0.6 else G0)
    for bx in (6, 13, 58):
        _blade(c, bx, rng.uniform(7, 11), rng.uniform(-3, 3), G1, G2)
        _blade(c, bx + 2, rng.uniform(5, 8), rng.uniform(-3, 3), G2, G3)
    return c


def dec_rock():
    """Глыба лавы, 32×20: тёмный угловатый камень, сверху пепельный свет, по трещинам жар;
    папоротник у подножия."""
    c = Canvas(32, 20)
    c.poly([(2, 19), (3, 11), (7, 5), (14, 2), (22, 4), (28, 9), (30, 19)], ST1)
    c.poly([(5, 10), (8, 6), (14, 3), (21, 5), (17, 9), (10, 11)], ST0)
    c.poly([(22, 6), (27, 10), (28, 15), (24, 11)], ST0)
    # Пузыри застывшей лавы.
    for x, y in ((11, 7), (16, 6), (25, 12)):
        c.set(x, y, ST1)
    # Трещины с жаром: светлое ядро, красная кайма.
    for pts in (((13, 11), (15, 14), (13, 17), (15, 19)), ((20, 9), (22, 13), (21, 16), (24, 19)),
                ((6, 13), (8, 16), (7, 19))):
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            c.line(xa + 1, ya, xb + 1, yb, S1, 1)
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            c.line(xa, ya, xb, yb, PINK, 1)
    c.set(15, 14, W0)
    c.set(22, 13, W0)
    c.poly([(0, 19), (3, 15), (6, 19)], G2)
    c.poly([(25, 19), (29, 14), (31, 19)], G1)
    c.set(3, 14, G1)
    c.set(29, 13, G0)
    c.outline(FK)
    return c


def dec_flowers():
    """Улитки молодых папоротников, 32×20: стебли закручены на конце спиралью, у основания
    листочки, между ними рыжие спороносные колоски."""
    rng = random.Random(465)
    c = Canvas(32, 20)
    for _ in range(8):
        _blade(c, rng.uniform(2, 30), rng.uniform(3, 7), rng.uniform(-2, 2), rng.choice((G2, G3)), G3)
    curl = ((0, 0), (0, -1), (1, -2), (2, -2), (3, -1), (3, 0), (2, 1), (1, 0))
    for x, y, f in ((5, 9, 1), (13, 5, -1), (20, 8, 1), (27, 6, -1)):
        c.line(x, y, x, 19, G2, 1)
        c.line(x + f, y + 3, x + f, 19, G3, 1)
        for n, (dx, dy) in enumerate(curl):
            c.set(x + dx * f, y + dy, G1 if n < 5 else G0)
        c.set(x + 2 * f, y - 1, G0)
        # Листочки на стебле.
        for yy in range(y + 4, 18, 3):
            c.set(x - f, yy, G1)
            c.set(x - 2 * f, yy - 1, G1)
    for x, h in ((9, 6), (17, 8), (24, 5)):
        c.line(x, 19 - h + 3, x, 19, G3, 1)
        c.rect(x, 19 - h, x, 19 - h + 2, PINK)
        c.set(x, 19 - h + 1, W0)
    return c


def dec_mush():
    """Череп мелкого ящера и кость у корней, 32×16: вытянутая морда с зубами, глазница, рядом
    берцовая кость с головками."""
    c = Canvas(32, 16)
    # Кость позади черепа.
    c.line(21, 13, 28, 10, W1, 2)
    c.ellipse(29, 9.5, 1.6, 1.6, W0)
    c.ellipse(28.5, 12, 1.4, 1.4, W1)
    c.ellipse(20.5, 14, 1.6, 1.4, W1)
    # Череп мордой влево: свод, морда клином, нижняя челюсть.
    c.ellipse(15, 8.5, 5, 4.5, W1)
    c.poly([(2, 9), (5, 7), (12, 5), (15, 5), (15, 11), (3, 11)], W1)
    c.poly([(5, 13), (16, 13), (18, 11), (18, 15), (6, 15)], W1)
    # Свет по своду и переносице.
    c.line(6, 7, 12, 5, W0, 1)
    c.line(12, 5, 17, 5, W0, 1)
    c.set(18, 7, W0)
    # Глазница, ноздря, височное окно.
    c.ellipse(13, 8.5, 1.8, 1.8, FK)
    c.set(4, 9, FK)
    c.set(18, 9, W2)
    c.set(17, 10, W2)
    # Зубы: верхние вниз, щель пасти.
    for x in range(4, 14, 2):
        c.set(x, 12, W0)
        c.set(x + 1, 12, FK)
    for x in range(6, 14, 2):
        c.set(x + 1, 13, W0)
    c.rect(6, 15, 17, 15, W2)
    c.outline(FK)
    return c


# --- Враги (палитра спрайтов) ------------------------------------------------------------------

def crab(i):
    """Ползун тропы: трилобит основы, четыре кадра, оранжевая обводка опасности уже на нём."""
    return dinosaurs16.trilobite(i)


def drone(i):
    """Летун тропы: птеродактиль основы летит вправо, четыре кадра взмаха, тело по центру
    кадра, чтобы при развороте не прыгало."""
    return dinosaurs16.pterodactyl(i)


def sprites():
    """Ленты этой демки в палитре спрайтов (ленты героя в `dinosaurs16.sprites`)."""
    return {
        "crab_walk": strip([crab(i) for i in range(4)]),
        "parrot_fly": strip([drone(i) for i in range(4)]),
    }


def backdrop():
    """Слои фона и вайи над кадром в палитре фона `DINOSAURS_BG`."""
    return {"par3_back": par3_back(), "par3_trees": par3_trees(), "par3_bushes": par3_bushes(),
            "canopy_front": canopy_front()}


def foreground():
    """Земля, арка, украшения в палитре переднего плана `DINOSAURS_FG`."""
    return {
        "trail_soil": trail_soil(),
        "trail_edge": trail_edge(),
        "arch_bark": arch_bark(),
        "dec_grass": strip([dec_grass(i) for i in range(2)]),
        "dec_tuft": strip([dec_tuft(i) for i in range(2)]),
        "dec_fern": dec_fern(),
        "dec_bush": dec_bush(),
        "dec_rock": dec_rock(),
        "dec_flowers": dec_flowers(),
        "dec_mush": dec_mush(),
    }


def preview(path):
    items = dinosaurs16.shaded(sprites())
    for key, canvas in foreground().items():
        items[key] = (canvas, DINOSAURS_FG)
    for key, canvas in backdrop().items():
        items[key] = (canvas, DINOSAURS_BG)
    dinosaurs16.save_sheet(path, items, scale=2)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
