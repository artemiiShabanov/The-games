#!/usr/bin/env python3
"""Набор «Зомби» для платформера × 16/32-bit «тропа» (#137), зеркало `space_trail16.py` и
`pixel_trail16.py`: те же ключи, размеры холстов, число кадров и точки опоры. Вместо джунглей и
грибов ночная роща у старого кладбища: фон без неба в три слоя (сине-зелёный туман с силуэтом
пригорода, холмом с часовней и колоколом и голыми деревьями вдали; большие мёртвые деревья с
бороздчатой корой, дуплом и паутиной, жухлая крона сплошной полосой наверху, с неё свисают
бороды мха; у земли надгробия, каменные кресты, кованая ограда и сухие кусты в низовом тумане)
и сухие ветки с мхом над кадром спереди; земля из кладбищенской грязи с костями и корнями под
кромкой жухлой травы; арка из старого кирпича склепа.

Свойства слотов, на которые рассчитана демка: ленты фона 512 пикселей стыкуются по краям, у
дали и кустов низ сплошной, у больших деревьев стволы на тех же местах и прозрачно между ними,
у веток спереди прозрачный низ; грунт 64×64 стыкуется в обе стороны, кромка 32×18 с
поверхностью на строке 4, грань арки 32×32 по кругу; украшения стоят на нижней строке холста.

У фона и переднего плана свои палитры по 16 цветов (`ZOMBIES_BG`, `ZOMBIES_FG`); ползущая рука
и ворон в палитре спрайтов `zombies16.PALETTE`, их рисует основа, здесь они получают красную
обводку опасности. Ленты героя рисует `zombies16.py`. Случайность с постоянным зерном: картинка
одна и та же.

    python3 tools/zombies_trail16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zombies16  # noqa: E402
from zombies16 import Canvas, strip, K, RED  # noqa: E402

TAU = math.pi * 2.0

# Палитра фона: ночной туман дали, жухлая крона, мёртвая кора и камень, огни.
HZ0, HZ1, HZ2, HZ3, L0, L1, L2, L3, L4, T0, T1, T2, DK, FL1, FL2, MO = range(16)
ZOMBIES_BG = [
    (0x7A, 0xB4, 0xA8),  # HZ0  светлый туман у земли
    (0x4E, 0x8A, 0x8C),  # HZ1  туман
    (0x32, 0x60, 0x72),  # HZ2  дальние силуэты в тумане
    (0x20, 0x3C, 0x56),  # HZ3  ночная глубина, холм
    (0xD0, 0xC2, 0x7A),  # L0   блик сухого листа
    (0xA0, 0x98, 0x58),  # L1   сухой лист, свет
    (0x70, 0x74, 0x48),  # L2   жухлая листва, мох
    (0x48, 0x54, 0x40),  # L3   листва, тень
    (0x2A, 0x38, 0x36),  # L4   глубокая тень кроны, земля
    (0xA2, 0x98, 0x94),  # T0   мёртвая кора и камень, свет
    (0x6A, 0x5E, 0x62),  # T1   кора, камень
    (0x40, 0x38, 0x44),  # T2   кора, камень, тень
    (0x12, 0x14, 0x1E),  # DK   самая тёмная тень, кованое железо
    (0xF6, 0xDC, 0x6E),  # FL1  свет в окнах, глаза в дупле
    (0xD4, 0x46, 0x36),  # FL2  красное: лампада, тряпка
    (0x8E, 0xE0, 0x6C),  # MO   ядовито-зелёные огоньки тумана
]

# Палитра переднего плана: жухлая трава, грязь, камень и кость, кирпич склепа, пламя.
FK, G0, G1, G2, G3, S0, S1, S2, S3, S4, ST0, ST1, W0, W1, W2, PINK = range(16)
ZOMBIES_FG = [
    (0x12, 0x10, 0x14),  # FK   обводка
    (0xE8, 0xD8, 0x8A),  # G0   кончики сухой травы
    (0xBA, 0xA8, 0x56),  # G1   сухая трава
    (0x88, 0x7E, 0x42),  # G2
    (0x54, 0x56, 0x36),  # G3   тень травы, мох
    (0x92, 0x76, 0x5E),  # S0   ком грязи, свет, дерево креста
    (0x6C, 0x54, 0x48),  # S1   грязь
    (0x4E, 0x3A, 0x38),  # S2   грунт
    (0x36, 0x28, 0x2E),  # S3   тень грунта
    (0x20, 0x18, 0x20),  # S4   щели, корни
    (0xC8, 0xCA, 0xBE),  # ST0  камень и кость, свет
    (0x84, 0x8A, 0x88),  # ST1  камень и кость, тень
    (0xC0, 0x70, 0x54),  # W0   кирпич, свет, стекло лампады
    (0x92, 0x48, 0x40),  # W1   кирпич
    (0x5C, 0x2C, 0x32),  # W2   кирпич, тень
    (0xF8, 0xE2, 0x72),  # PINK пламя лампады, метёлки бурьяна
]

BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, int(y), col)


def _wget(c, x, y):
    return c.get(int(math.floor(x)) % c.w, int(y))


def _wrect(c, x0, y0, x1, y1, col):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            _wset(c, x, y, col)


def _wellipse(c, cx, cy, rx, ry, col, keep=None):
    """Эллипс на ленте, которая стыкуется по краям; `keep` красит только поверх этого цвета."""
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                if keep is None or _wget(c, x, y) == keep:
                    _wset(c, x, y, col)


def _wline(c, x0, y0, x1, y1, col, t=1):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    r = (t - 1) / 2.0
    for i in range(n + 1):
        k = i / n
        x = x0 + (x1 - x0) * k
        y = y0 + (y1 - y0) * k
        if t <= 1:
            _wset(c, x, round(y), col)
        else:
            _wellipse(c, x, y, r, r, col)


def _branch(put, rng, x, y, ang, length, width, depth, bend=0.0):
    """Голая ветка: идёт от (x, y) под углом `ang`, сужается, на ходу раздваивается. `put(x, y,
    u)` красит пиксель, `u` от 0 до 1 поперёк ветки (свет слева или сверху)."""
    n = max(int(length), 1)
    forks = sorted(rng.uniform(0.35, 0.9) for _ in range(2 if depth > 0 else 0))
    for j in range(n):
        k = j / n
        a = ang + bend * k
        x += math.cos(a)
        y += math.sin(a)
        w = max(1, int(round(width * (1.0 - 0.65 * k))))
        steep = abs(math.sin(a)) > 0.7
        for d in range(w):
            u = d / max(w - 1, 1) if w > 1 else 0.5
            if steep:
                put(x + d - (w - 1) / 2.0, y, u)
            else:
                put(x, y + d - (w - 1) / 2.0, u)
        while forks and k >= forks[0]:
            forks.pop(0)
            side = rng.choice((-1, 1))
            _branch(put, rng, x, y, a + side * rng.uniform(0.5, 1.0), length * rng.uniform(0.4, 0.6),
                    max(1.0, width * 0.55), depth - 1, rng.uniform(-0.4, 0.4))


def _clump(c, rng, cx, cy, rx, ry, cols):
    """Ком жухлой листвы: рваный край лопастями, свет сверху слева, рябь из сухих листьев.
    `cols` от светлого к тёмному: блик, свет, тело, тень."""
    hi, light, body, shade = cols
    ph = rng.uniform(0, TAU)
    lobes = rng.randint(5, 8)
    for y in range(int(cy - ry * 1.3 - 1), int(cy + ry * 1.3 + 2)):
        for x in range(int(cx - rx * 1.3 - 1), int(cx + rx * 1.3 + 2)):
            dx = (x - cx) / rx
            dy = (y - cy) / ry
            a = math.atan2(dy, dx)
            rr = 1.0 + 0.13 * math.sin(a * lobes + ph) + 0.08 * math.sin(a * lobes * 2.3 + ph * 2.0)
            d = math.hypot(dx, dy)
            if d > rr:
                continue
            h = ((x * 7 + y * 13) ^ (x * 3 - y * 5)) & 7
            v = -dx * 0.55 - dy * 0.8 + (h - 3.5) * 0.11
            if d > rr - 0.16 and dy > 0.15:
                col = shade
            elif v > 0.66:
                col = hi
            elif v > 0.24:
                col = light
            elif v > -0.34:
                col = body
            else:
                col = shade
            _wset(c, x, y, col)
    # Отдельные сухие листья: косые штрихи светлее и темнее тела.
    for _ in range(int(rx * ry * 0.05)):
        a = rng.uniform(0, TAU)
        d = rng.uniform(0.0, 0.8)
        x = cx + math.cos(a) * rx * d
        y = cy + math.sin(a) * ry * d
        col = light if math.sin(a) < 0.1 else shade
        _wset(c, x, y, col)
        _wset(c, x + 1, y + 1, col)


def _moss(c, rng, x, y0, length, cols):
    """Борода мха: свисает прядью, шире у корня, качается синусом, рваная."""
    light, body, shade = cols
    ph = rng.uniform(0, TAU)
    n = int(length)
    for j in range(n):
        k = j / max(n, 1)
        sx = x + math.sin(j * 0.09 + ph) * 2.0 * k
        w = 3 if k < 0.3 else (2 if k < 0.75 else 1)
        for d in range(w):
            col = light if d == 0 and (j + int(x)) % 5 < 2 else (body if d < 2 else shade)
            if w == 1 and j % 4 == 3:
                continue
            _wset(c, sx + d, y0 + j, col)
        if j % 9 == 4 and k < 0.8:
            _wset(c, sx - 1, y0 + j + 1, body)
            _wset(c, sx + w, y0 + j + 2, shade)


# --- Фон ---------------------------------------------------------------------------------------

def _hill(x):
    """Кромка кладбищенского холма в дали: большой горб с часовней и малый с оградой."""
    d1 = (x - 150 + 256) % 512 - 256
    d2 = (x - 396 + 256) % 512 - 256
    return (216.0 - 30.0 * math.exp(-(d1 / 92.0) ** 2) - 13.0 * math.exp(-(d2 / 64.0) ** 2)
            - 1.5 * math.sin(TAU * 7 * x / 512.0))


def par3_back():
    """Даль на весь экран, 512×277: ночная глубина сверху, к земле светлеет туман полосами;
    в тумане голые деревья и крыши пригорода с огнями в окнах, ближе тёмный холм с часовней,
    крестами и оградой; низ сплошной."""
    rng = random.Random(341)
    c = Canvas(512, 277)
    ramp = (HZ3, HZ2, HZ1, HZ0)
    for y in range(277):
        for x in range(512):
            base_ = min(max(0.0, (y - 64) / 150.0), 1.0)
            wisp = (0.34 * math.sin(TAU * 2 * x / 512.0 + y * 0.045) * math.sin(y * 0.21)
                    + 0.22 * math.sin(TAU * 5 * x / 512.0 - y * 0.03) * math.sin(y * 0.33 + 1.0))
            v = base_ * 2.5 + wisp * (0.35 + base_)
            lvl = int(math.floor(v + BAYER[y % 4][x % 4] / 16.0))
            c.set(x, y, ramp[min(max(lvl, 0), 3)])
    sky = [row[:] for row in c.px]
    darker = {HZ0: HZ1, HZ1: HZ2, HZ2: HZ3, HZ3: DK}

    def dim(x, y, _u=0.0):
        """Силуэт в тумане: на тон темнее того, что за ним."""
        xi = int(math.floor(x)) % 512
        yi = int(round(y))
        if 0 <= yi < 277:
            c.set(xi, yi, darker[sky[yi][xi]])

    # Дальние голые деревья во весь рост.
    for _ in range(24):
        x = rng.uniform(0, 512)
        h = rng.uniform(110, 200)
        w = rng.uniform(3, 6)
        _branch(dim, rng, x, 240, -math.pi / 2 + rng.uniform(-0.08, 0.08), h, w, 3, rng.uniform(-0.2, 0.2))
    # Пригород: дома с двускатными крышами и трубами, столбы с проводами.
    x = 6.0
    while x < 500:
        w = rng.randint(20, 34)
        wall = rng.randint(12, 20)
        top = 210 - wall
        if not 96 < x + w / 2 < 214:
            for yy in range(top, 240):
                for xx in range(int(x), int(x) + w):
                    dim(xx, yy)
            peak = rng.randint(8, 13)
            for j in range(peak):
                half = (w / 2.0 + 2) * (j + 1) / peak
                for xx in range(int(x + w / 2.0 - half), int(x + w / 2.0 + half) + 1):
                    dim(xx, top - peak + j)
            cx = x + w * rng.choice((0.25, 0.72))
            for yy in range(top - peak - 3, top - 2):
                dim(cx, yy)
                dim(cx + 1, yy)
            # Окна: одно светится, остальные тёмные.
            lit = rng.randrange(3)
            for i in range(3):
                wx = int(x) + 4 + i * ((w - 8) // 2)
                if i == lit and rng.random() < 0.7:
                    _wrect(c, wx, top + 4, wx + 1, top + 6, FL1)
        x += w + rng.randint(10, 26)
    for px in range(20, 512, 82):
        for yy in range(176, 240):
            dim(px, yy)
        for dx in range(-4, 5):
            dim(px + dx, 179)
        for dx in range(82):
            dim(px + dx, 180 + 6.0 * math.sin(math.pi * dx / 82.0))
    # Холм: тёмная масса со светлой кромкой.
    for x in range(512):
        top = int(_hill(x))
        c.rect(x, top, x, 238, HZ3)
        c.set(x, top, HZ2)
        if (x * 5 + top) % 7 == 0:
            c.set(x, top + 2, HZ2)
    # Часовня на вершине: неф с крышей, колокольня со шпилем и крестом, в проёме колокол.
    gy = int(_hill(150)) + 2
    c.rect(141, gy - 18, 166, gy, HZ3)
    c.rect(160, gy - 18, 166, gy, DK)
    for j in range(11):
        c.rect(139 + j, gy - 19 - 10 + j, 168 - j + j * 0, gy - 19 - 10 + j, HZ3) if False else None
    for j in range(10):
        half = 15.0 * (j + 1) / 10.0
        c.rect(int(153.5 - half), gy - 28 + j, int(153.5 + half), gy - 28 + j, HZ3)
    c.line(153, gy - 28, 168, gy - 18, DK, 1)
    c.rect(128, gy - 40, 140, gy, HZ3)
    c.rect(137, gy - 40, 140, gy, DK)
    c.rect(126, gy - 42, 142, gy - 41, HZ3)
    for j in range(20):
        half = 7.5 * (j + 1) / 20.0
        c.rect(int(134 - half), gy - 62 + j, int(134 + half), gy - 62 + j, HZ3)
        if half > 2:
            c.set(int(134 + half), gy - 62 + j, DK)
    c.rect(134, gy - 71, 134, gy - 62, HZ3)
    c.rect(131, gy - 68, 137, gy - 68, HZ3)
    # Проём колокольни: туман насквозь и колокол.
    c.rect(131, gy - 36, 136, gy - 28, HZ1)
    c.rect(132, gy - 37, 135, gy - 37, HZ1)
    c.rect(133, gy - 35, 134, gy - 32, DK)
    c.rect(132, gy - 32, 135, gy - 31, DK)
    c.set(134, gy - 30, DK)
    # Стрельчатые окна нефа светятся, дверь тёмная.
    for wx in (146, 153):
        c.rect(wx, gy - 13, wx + 1, gy - 7, FL1)
        c.set(wx, gy - 14, FL1)
    c.rect(131, gy - 9, 135, gy, DK)
    c.rect(132, gy - 10, 134, gy - 10, DK)

    def solid(x, y, u=0.0):
        _wset(c, x, round(y), DK if u > 0.6 else HZ3)

    # Голые деревья на холме.
    for tx, th in ((104, 46), (186, 58), (236, 34), (432, 40)):
        _branch(solid, rng, tx, _hill(tx) + 2, -math.pi / 2 + rng.uniform(-0.15, 0.15), th, 4, 3,
                rng.uniform(-0.3, 0.3))
    # Кресты и плиты по гребню, на малом горбе кованая ограда.
    x = 8.0
    while x < 506:
        if not (120 < x < 176) and not (352 < x < 440):
            gy2 = int(_hill(x))
            kind = rng.randrange(3)
            if kind == 0:
                c.rect(int(x), gy2 - 8, int(x), gy2, HZ3)
                _wrect(c, x - 2, gy2 - 6, x + 2, gy2 - 6, HZ3)
            elif kind == 1:
                _wrect(c, x - 2, gy2 - 5, x + 2, gy2, HZ3)
                _wrect(c, x - 1, gy2 - 6, x + 1, gy2 - 6, HZ3)
                _wset(c, x + 2, gy2 - 4, DK)
            else:
                _wrect(c, x - 1, gy2 - 9, x + 1, gy2, HZ3)
                _wset(c, x, gy2 - 10, HZ3)
        x += rng.uniform(9, 20)
    for x in range(356, 438):
        gy2 = int(_hill(x))
        c.set(x, gy2 - 5, HZ3)
        if x % 4 == 0:
            c.rect(x, gy2 - 8, x, gy2, HZ3)
            c.set(x, gy2 - 9, DK)
    # Зелёные огоньки над туманом.
    for _ in range(26):
        x = rng.uniform(0, 512)
        y = int(rng.uniform(120, 206))
        if _wget(c, x, y) in (HZ1, HZ0, HZ2):
            _wset(c, x, y, MO)
    c.rect(0, 238, 511, 276, HZ3)
    return c


def _trunk(c, x0, x1, y0, y1, rng):
    """Ствол мёртвого дерева: светлый край слева, волнистые борозды коры, сучки."""
    w = x1 - x0
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            k = (x - x0) / max(w, 1)
            _wset(c, x, y, T0 if k < 0.16 else (T1 if k < 0.66 else T2))
    # Борозды: тёмная линия и светлая кромка слева от неё, с разрывами.
    for gx in range(int(x0) + 3, int(x1) - 1, 4):
        ph = rng.uniform(0, TAU)
        gap = rng.randint(17, 29)
        k = (gx - x0) / max(w, 1)
        for y in range(int(y0), int(y1)):
            if (y + gx * 3) % gap < 4:
                continue
            wob = int(round(math.sin(y * 0.07 + ph) * 1.4 + math.sin(y * 0.23 + ph * 2) * 0.6))
            _wset(c, gx + wob, y, DK if k > 0.6 else T2)
            if k < 0.6 and (y + gx) % 3:
                _wset(c, gx + wob - 1, y, T0 if k < 0.4 else T1)
    # Сучки: тёмный глазок со светлым ободком сверху.
    for _ in range(int((y1 - y0) / 60) + 1):
        kx = rng.uniform(x0 + 6, x1 - 6)
        ky = rng.uniform(y0 + 30, y1 - 30)
        _wellipse(c, kx, ky, 3.2, 4.2, T2)
        _wellipse(c, kx, ky + 0.5, 1.8, 2.8, DK)
        for dx in range(-3, 3):
            _wset(c, kx + dx, ky - 4 - (0 if abs(dx) > 1 else 1), T0)


def par3_trees():
    """Большие мёртвые деревья, 512×277, прозрачно между ними: стволы с бороздами, сучками и
    обломками веток расходятся корнями к земле, голые ветви уходят в жухлую крону, которая идёт
    сплошной полосой наверху; с кроны свисают бороды мха, у стволов паутина, в дупле глаза."""
    rng = random.Random(342)
    c = Canvas(512, 277)

    def bark(x, y, u=0.0):
        _wset(c, x, round(y), T0 if u < 0.25 else (T1 if u < 0.7 else T2))

    trunks = ((40, 30), (196, 22), (300, 38), (452, 26))
    # Голые ветви от стволов вверх в крону (рисуются до стволов, чтобы основание пряталось).
    for x, w in trunks:
        for side in (-1, 1):
            y = rng.uniform(96, 150)
            _branch(bark, rng, x + w / 2.0 + side * w * 0.3, y, -math.pi / 2 + side * rng.uniform(0.55, 0.85),
                    rng.uniform(70, 100), w * 0.32, 2, -side * 0.35)
    for x, w in trunks:
        _trunk(c, x, x + w, 40, 262, rng)
        # Основание расходится корнями к земле.
        for side in (-1, 1):
            for i in range(14):
                yy = 248 + i
                spread = int(i * 0.9)
                if side < 0:
                    c.rect(max(x - spread, 0), yy, x + 3, yy, T1)
                    c.set(max(x - spread, 0), yy, T0)
                else:
                    c.rect(x + w - 3, yy, min(x + w + spread, 511), yy, T2)
                    if i % 3 == 0:
                        c.set(min(x + w + spread, 511) - 1, yy, DK)
        # Обломки веток: короткие сучья с рваным концом.
        for _ in range(2):
            side = rng.choice((-1, 1))
            sy = rng.uniform(150, 226)
            n = rng.randint(6, 11)
            for j in range(n):
                sx = (x - 1 - j) if side < 0 else (x + w + j)
                yy = sy - j * 0.5
                thick = 3 if j < n - 2 else (2 if j < n - 1 else 1)
                for d in range(thick):
                    _wset(c, sx, round(yy) + d, T0 if d == 0 else (T1 if side < 0 else T2))
    # Дупло с глазами на самом толстом стволе, следы когтей на правом.
    _wellipse(c, 319, 168, 8, 11, T2)
    _wellipse(c, 319, 169, 6, 9, DK)
    for dx in range(-6, 5):
        _wset(c, 319 + dx, 157 - (1 if abs(dx + 1) < 3 else 0), T0)
    for ex in (316, 322):
        c.rect(ex, 167, ex + 1, 167, FL1)
        c.set(ex, 168, FL2)
    for k in range(3):
        for j in range(15):
            _wset(c, 459 + k * 5 + j * 0.3, 118 + j, DK)
            _wset(c, 458 + k * 5 + j * 0.3, 118 + j, T0)
    # Паутина в углу между стволом и кроной: лучи из угла и провисшие дуги.
    for x0, side in ((70, 1), (300, -1), (218, 1)):
        for ang in (4, 24, 46, 68, 88):
            a = math.radians(ang)
            for j in range(34):
                wx = x0 + side * math.cos(a) * j
                wy = 58 + math.sin(a) * j
                if _wget(c, wx, wy) is None and j % 5 != 4:
                    _wset(c, wx, wy, HZ0)
        for r in (11, 20, 29):
            for ang in range(4, 89, 2):
                a = math.radians(ang)
                sag = 1.0 - 0.1 * abs(math.sin(math.radians(ang - 4) * 4.3))
                wx = x0 + side * math.cos(a) * r * sag
                wy = 58 + math.sin(a) * r * sag
                if _wget(c, wx, wy) is None:
                    _wset(c, wx, wy, HZ1)
    # Крона: сплошная тёмная масса и три ряда комьев жухлой листвы, нижний самый светлый.
    for y in range(0, 36):
        for x in range(512):
            c.set(x, y, DK if ((x * 5 + y * 3) ^ (x + y * 7)) % 11 == 0 else L4)
    for x in range(0, 512, 30):
        _clump(c, rng, x + rng.uniform(-6, 6), rng.uniform(4, 12), rng.uniform(21, 27), rng.uniform(13, 17),
               (L3, L4, L4, DK))
    for x in range(0, 512, 26):
        _clump(c, rng, x + rng.uniform(-6, 6), rng.uniform(20, 30), rng.uniform(21, 28), rng.uniform(13, 17),
               (L2, L3, L4, DK))
    for x in range(0, 512, 32):
        _clump(c, rng, x + rng.uniform(-6, 6), rng.uniform(40, 48), rng.uniform(24, 32), rng.uniform(12, 16),
               (L0, L1, L2, L3))
    # Бороды мха свисают с кроны.
    for _ in range(12):
        x = rng.uniform(0, 512)
        _moss(c, rng, x, 50, rng.uniform(34, 100), (L1, L2, L3))
    return c


def _stone(c, x, base, w, h, kind, lean=0.0):
    """Надгробие от земли `base` вверх на `h`: 0 плита с круглым верхом, 1 каменный крест,
    2 обелиск. Свет слева, тень справа, резьба и мох."""
    def put(dx, y, col):
        _wset(c, x + dx + lean * (base - y), y, col)

    def tone(dx, half):
        u = dx / max(half, 1.0)
        return T0 if u < -0.55 else (T1 if u < 0.45 else T2)

    half = w / 2.0
    if kind == 0:
        for y in range(int(base - h), int(base) + 3):
            k = base - h + half - y
            hw = half if k <= 0 else math.sqrt(max(0.0, half * half - k * k))
            for dx in range(int(-hw), int(hw) + 1):
                put(dx, y, T0 if (k > 0 and dx < hw * 0.3 and k > half * 0.55) else tone(dx, half))
        # Резьба: крестик и строки.
        cy = int(base - h + half * 0.9)
        for d in range(-2, 3):
            put(0, cy + d, T2)
            put(d * 0.8, cy - 1, T2)
        for i, yy in enumerate(range(cy + 6, int(base) - 4, 3)):
            for dx in range(int(-half + 3), int(half - 3 - (i % 2) * 2)):
                put(dx, yy, T2)
        for i in range(5):
            put(half * 0.55 - i * 0.6, base - h + half * 0.5 + i, DK)
    elif kind == 1:
        arm = h * 0.3
        for y in range(int(base - h), int(base) + 3):
            wide = base - h + arm - 2 <= y <= base - h + arm + 2
            hw = half if wide else 2.2
            for dx in range(int(-hw), int(hw) + 1):
                col = tone(dx, hw)
                if wide and y == int(base - h + arm - 2):
                    col = T0
                if wide and y == int(base - h + arm + 2):
                    col = T2
                put(dx, y, col)
        for dx in range(int(-half * 0.75), int(half * 0.75) + 1):
            for y in range(int(base) - 3, int(base) + 3):
                put(dx, y, T0 if y == int(base) - 3 else tone(dx, half * 0.75))
        put(0, base - h + arm, T2)
    else:
        for y in range(int(base - h), int(base) + 3):
            k = (y - (base - h)) / h
            hw = max(0.5, (k / 0.14) * half * 0.55) if k < 0.14 else half * (0.55 + 0.3 * k)
            for dx in range(int(-hw), int(hw) + 1):
                put(dx, y, tone(dx, hw))
        for dx in range(int(-half - 1), int(half) + 2):
            for y in range(int(base) - 4, int(base) + 3):
                put(dx, y, T0 if y == int(base) - 4 else tone(dx, half + 1))
        for yy in range(int(base - h * 0.6), int(base) - 8, 3):
            put(-1, yy, T2)
            put(0, yy, T2)
            put(1, yy, T2)
    # Мох на макушке.
    for d in range(-1, 2):
        put(d - half * 0.2, base - h + (1 if kind != 2 else 3), L2)
    put(-half * 0.2, base - h + 2 + (0 if kind != 2 else 2), L3)


def par3_bushes():
    """Кладбище у земли, 512×120, прозрачный верх: надгробия, каменные кресты, обелиски,
    кованая ограда с пиками, сухие кусты и бурьян в низовом тумане; низ сплошной."""
    rng = random.Random(343)
    c = Canvas(512, 120)
    base = 96

    def twig(x, y, u=0.0):
        _wset(c, x, round(y), L1 if u < 0.3 else L3)

    x = 4.0
    while x < 500:
        kind = rng.choice((0, 0, 1, 2, 3, 3, 4, 5))
        if kind == 0:
            w = rng.randint(13, 18)
            _stone(c, x + w / 2.0, base, w, rng.randint(24, 34), 0, rng.uniform(-0.12, 0.12))
        elif kind == 1:
            w = 14
            _stone(c, x + w / 2.0, base, w, rng.randint(32, 42), 1, rng.uniform(-0.1, 0.1))
        elif kind == 2:
            w = 10
            _stone(c, x + w / 2.0, base, w, rng.randint(40, 52), 2)
        elif kind == 3:
            # Ограда: прутья с пиками, две перекладины, один прут погнут.
            w = rng.randint(30, 44)
            bent = rng.randrange(1, w // 5)
            for i in range(w // 5 + 1):
                px = x + i * 5
                top = 66 if i % 3 else 62
                for yy in range(top, base + 2):
                    lean = (yy - base) * -0.2 if i == bent else 0.0
                    _wset(c, px + lean, yy, DK)
                    if yy % 7 == 3:
                        _wset(c, px + lean + 1, yy, T2)
                tx = px + ((top - base) * -0.2 if i == bent else 0.0)
                _wset(c, tx, top - 1, DK)
                _wset(c, tx, top - 2, T2)
                _wset(c, tx - 1, top + 1, DK)
                _wset(c, tx + 1, top + 1, DK)
            for yy in (71, 90):
                _wrect(c, x, yy, x + (w // 5) * 5, yy, DK)
                _wrect(c, x, yy - 1, x + (w // 5) * 5, yy - 1, T2)
        elif kind == 4:
            # Сухой куст: голые прутья веером.
            w = rng.randint(22, 30)
            for _ in range(6):
                _branch(twig, rng, x + w / 2.0 + rng.uniform(-3, 3), base, -math.pi / 2 + rng.uniform(-0.9, 0.9),
                        rng.uniform(18, 34), 2, 2, rng.uniform(-0.4, 0.4))
        else:
            # Бурьян с метёлками.
            w = rng.randint(12, 18)
            for _ in range(5):
                bx = x + rng.uniform(1, w - 1)
                h = rng.uniform(14, 28)
                bend = rng.uniform(-4, 4)
                for j in range(int(h)):
                    k = j / h
                    _wset(c, bx + bend * k * k, base - j, L2 if j % 4 else L1)
                for j in range(4):
                    _wset(c, bx + bend, base - int(h) - j, L0 if j < 3 else L1)
                    _wset(c, bx + bend + 1, base - int(h) - j + 1, L1)
        x += w + rng.uniform(4, 11)
    # Земля: сплошной низ, по кромке жухлая трава.
    c.rect(0, 93, 511, 119, L4)
    for x in range(512):
        n = rng.choice((0, 1, 2, 2, 3, 4, 6))
        lean = rng.choice((-1, 0, 0, 1))
        for j in range(n):
            _wset(c, x + lean * (j // 3), 93 - j, L3 if j < n * 0.4 else (L2 if j < n - 1 or n < 4 else L1))
        if x % 5 == 0:
            c.set(x, 94, L3)
    for _ in range(300):
        x = rng.uniform(0, 512)
        y = rng.uniform(96, 119)
        _wset(c, x, int(y), L3 if rng.random() < 0.5 else DK)
    # Утонувшие в земле плиты.
    for _ in range(9):
        x = rng.uniform(0, 512)
        y = int(rng.uniform(100, 114))
        w = rng.randint(8, 14)
        _wrect(c, x, y, x + w, y + 1, T2)
        _wrect(c, x, y, x + w - 2, y, T1)
    # Низовой туман шашечкой поверх оснований.
    for y in range(80, 99):
        for x in range(512):
            wisp = (math.sin(TAU * 3 * x / 512.0 + y * 0.5) + math.sin(TAU * 7 * x / 512.0 - y * 0.3)
                    + (y - 80) * 0.09)
            if wisp > 1.25 and (x + y) % 2 == 0:
                c.set(x, y, HZ1 if wisp < 2.0 else HZ0)
    # Зелёные огоньки в воздухе.
    for _ in range(30):
        x = rng.uniform(0, 512)
        y = rng.uniform(20, 84)
        if _wget(c, x, y) is None:
            _wset(c, x, int(y), MO)
    return c


def canopy_front():
    """Ветви над кадром спереди, 256×56, прозрачный низ: тёмные комья жухлой листвы, голые
    сучья вниз и бороды мха."""
    rng = random.Random(344)
    c = Canvas(256, 56)

    def twig(x, y, u=0.0):
        _wset(c, x, round(y), DK if u > 0.4 else L4)

    for _ in range(9):
        _branch(twig, rng, rng.uniform(0, 256), 12, math.pi / 2 + rng.uniform(-0.7, 0.7), rng.uniform(14, 26), 3, 2,
                rng.uniform(-0.5, 0.5))
    for x in range(0, 256, 22):
        _clump(c, rng, x + rng.uniform(-4, 4), rng.uniform(8, 14), rng.uniform(15, 20), rng.uniform(9, 12),
               (L2, L3, L4, DK))
    for x in range(0, 256, 28):
        _clump(c, rng, x + rng.uniform(-4, 4), rng.uniform(-2, 3), rng.uniform(16, 21), rng.uniform(8, 10),
               (L3, L4, DK, DK))
    for _ in range(12):
        x = rng.uniform(0, 256)
        _moss(c, rng, x, 14, rng.uniform(12, 34), (L2, L3, L4))
    return c


# --- Передний план -----------------------------------------------------------------------------

def trail_soil():
    """Кладбищенская грязь, 64×64 по кругу в обе стороны: волнистые пласты, комья со светом
    сверху слева, камешки, кости и череп, корни, червяк."""
    rng = random.Random(351)
    n = 64
    c = Canvas(n, n)

    def put(x, y, col):
        c.set(int(math.floor(x)) % n, int(math.floor(y)) % n, col)

    for y in range(n):
        for x in range(n):
            wave = (math.sin(TAU * 2 * x / n + math.sin(TAU * y / n) * 1.3) * 2.2
                    + math.sin(TAU * 5 * x / n + 1.7) * 0.8)
            b = (y + wave) % 16.0
            col = S3 if b < 1.0 else (S2 if b < 9.0 else (S3 if b < 10.2 else (S2 if (x + y) % 3 else S3)))
            c.set(x, y, col)
    for _ in range(90):
        put(rng.randrange(n), rng.randrange(n), rng.choice((S1, S3, S4, S3)))
    # Комья.
    for _ in range(30):
        cx, cy = rng.uniform(0, n), rng.uniform(0, n)
        rx, ry = rng.uniform(1.8, 4.6), rng.uniform(1.4, 2.8)
        for y in range(int(cy - ry - 1), int(cy + ry + 3)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                u, v = (x - cx) / rx, (y - cy) / ry
                if u * u + v * v <= 1.0:
                    put(x, y, S0 if (u < -0.1 and v < -0.25) else (S3 if v > 0.45 else S1))
                elif u * u + ((y - 1 - cy) / ry) ** 2 <= 1.0:
                    put(x, y, S4)
    # Корни травы сверху вниз.
    for _ in range(4):
        x = rng.uniform(0, n)
        y = rng.uniform(0, n)
        ph = rng.uniform(0, TAU)
        for j in range(rng.randint(9, 15)):
            put(x + math.sin(j * 0.5 + ph) * 1.6, y + j, S4)
            if j == 6:
                for k in range(4):
                    put(x + math.sin(j * 0.5 + ph) * 1.6 + k + 1, y + j + k * 0.7, S4)
    # Кости: длинная с головками и вторая через стык.
    for (x0, y0, x1, y1) in ((9, 21, 23, 26), (54, 50, 70, 46)):
        m = int(max(abs(x1 - x0), abs(y1 - y0))) * 2
        for i in range(m + 1):
            k = i / m
            put(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, ST0)
            put(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k + 1, ST1)
        for ex, ey in ((x0, y0), (x1, y1)):
            put(ex, ey - 1, ST0)
            put(ex + (1 if ex == x1 else -1), ey, ST0)
            put(ex + (1 if ex == x1 else -1), ey + 1, ST1)
            put(ex, ey + 2, S4)
    # Череп боком в грязи.
    for y in range(-4, 5):
        for x in range(-5, 6):
            if (x / 5.2) ** 2 + (y / 4.2) ** 2 <= 1.0:
                put(40 + x, 38 + y, ST1 if (x > 2 or y > 2) else ST0)
    for x in range(-4, 2):
        put(40 + x, 43, ST1 if x % 2 else ST0)
        put(40 + x, 44, S4)
    for ex in (-3, 1):
        put(40 + ex, 38, S4)
        put(40 + ex + 1, 38, S4)
        put(40 + ex, 39, S4)
        put(40 + ex + 1, 39, S3)
    put(39, 41, S4)
    # Камешки.
    for _ in range(9):
        x, y = rng.randrange(n), rng.randrange(n)
        put(x, y, ST0)
        put(x + 1, y, ST1)
        put(x, y + 1, ST1)
        put(x + 1, y + 1, S4)
    # Червяк.
    for j in range(7):
        put(20 + j, 54 + round(math.sin(j * 1.1) * 1.2), W0 if j % 3 else W1)
    return c


def trail_edge():
    """Кромка жухлой травы, 32×18 по кругу: поверхность на строке 4, сухие стебли над ней,
    трава свисает клочьями в грунт; ниже прозрачно, там грунт."""
    rng = random.Random(352)
    c = Canvas(32, 18)
    top = 4
    for x in range(32):
        hang = top + 3 + int(1.5 + 1.8 * math.sin(TAU * 3 * x / 32.0) + rng.uniform(0, 3.0))
        c.rect(x, top, x, hang, G2 if (x * 3 + 1) % 5 == 0 else G1)
        c.rect(x, top, x, top, G0)
        if x % 3 == 1:
            c.set(x, top + 1, G0)
        if x % 4 == 2:
            c.set(x, top + 2, G2)
        c.set(x, hang, G2)
        c.set(x, hang + 1, G3)
        if (x + hang) % 3 == 0:
            c.set(x, hang + 2, S4)
        if rng.random() < 0.5:
            h = rng.randint(1, 3)
            c.rect(x, top - h, x, top - 1, G1 if rng.random() < 0.5 else G2)
            if h == 3:
                c.set(x, top - h, G0)
    # Сухой сломанный стебель лежит на кромке.
    for j in range(7):
        c.set(18 + j, top + 1 - (j // 4), G3)
    return c


def arch_bark():
    """Грань арки, 32×32 по кругу: старый кирпич склепа вперевязку, швы, выпавший кирпич,
    трещина и мох."""
    rng = random.Random(353)
    c = Canvas(32, 32)
    for row in range(4):
        y0 = row * 8
        off = 8 if row % 2 else 0
        for col in range(2):
            x0 = off + col * 16
            tone = rng.choice((0, 0, 1, 2))
            hole = row == 2 and col == 1
            for y in range(y0, y0 + 8):
                for x in range(x0, x0 + 16):
                    dx, dy = x - x0, y - y0
                    if dy == 7 or dx == 15:
                        colr = S4
                    elif hole:
                        colr = S3 if (dx + dy) % 5 else S4
                    elif dy == 0 or dx == 0:
                        colr = W0 if tone < 2 else W1
                    elif dy == 6 or dx == 14:
                        colr = W2
                    else:
                        colr = (W1, W1, W2)[tone] if ((dx * 3 + dy * 5 + row) % 11) else (W0, W2, W1)[tone]
                    c.set(x % 32, y, colr)
            # Сколы по углам.
            if not hole and rng.random() < 0.7:
                cx = x0 + rng.choice((1, 13))
                cy = y0 + rng.choice((1, 5))
                c.set(cx % 32, cy, W2)
                c.set((cx + 1) % 32, cy, S4 if rng.random() < 0.5 else W2)
    # Трещина ступенями по швам и через кирпич.
    x, y = 21, 0
    for _ in range(15):
        c.set(x % 32, y % 32, FK)
        if rng.random() < 0.45:
            x += rng.choice((-1, 1))
            c.set(x % 32, y % 32, FK)
        y += 1
    # Мох пятнами по швам.
    for _ in range(6):
        x = rng.randint(0, 31)
        y = rng.choice((7, 15, 23, 31))
        for dx in range(-2, 4):
            for dy in range(-1, 2):
                if rng.random() < 0.65:
                    c.set((x + dx) % 32, (y + dy) % 32, G3 if dy >= 0 else G2)
    return c


def _blade(c, x, h, bend, col, side, tip=None):
    for j in range(int(h)):
        k = j / h
        c.set(x + bend * k * k, c.h - 1 - j, col)
        if k < 0.55:
            c.set(x + bend * k * k + 1, c.h - 1 - j, side)
    if tip is not None:
        # Метёлка: три пикселя вдоль стебля и один сбоку.
        for j in range(3):
            c.set(x + bend, c.h - int(h) - j, tip)
        c.set(x + bend + 1, c.h - int(h), tip)


def dec_grass(i):
    """Высокий сухой бурьян перед героем, 32×24, два кадра качания; у части стеблей метёлки."""
    rng = random.Random(361)
    c = Canvas(32, 24)
    for _ in range(15):
        x = rng.uniform(3, 29)
        col = rng.choice((G1, G2, G1, G0))
        tip = PINK if rng.random() < 0.4 else None
        h = rng.uniform(9, 20) if tip is not None else rng.uniform(9, 22)
        _blade(c, x, h, rng.uniform(-3, 3) + (1.5 if i else -0.5), col, G3 if col == G2 else G2, tip)
    return c


def dec_tuft(i):
    """Клок жухлой травы, 32×14, два кадра качания."""
    rng = random.Random(362)
    c = Canvas(32, 14)
    for _ in range(11):
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 11), rng.uniform(-2, 2) + (1 if i else 0), rng.choice((G0, G1, G2)), G3)
    return c


def dec_fern():
    """Покосившийся деревянный крест на холмике за героем, 48×32: брус и перекладина с
    волокнами, гвоздь, на перекладине красная тряпка, у подножия сухая трава."""
    c = Canvas(48, 32)
    # Холмик.
    c.ellipse(24, 32, 18, 6, S2)
    c.ellipse(20, 31, 10, 3.5, S1)
    for x, y in ((13, 28), (17, 27), (22, 27), (30, 28), (35, 29)):
        c.set(x, y, S0)
    for x, y in ((27, 30), (33, 31), (10, 31), (38, 30)):
        c.set(x, y, S3)
    # Брус с наклоном вправо.
    bx0, by0, bx1, by1 = 21.0, 29.0, 26.0, 4.0
    c.line(bx0, by0, bx1, by1, S1, 4)
    c.line(bx0 - 1.4, by0, bx1 - 1.4, by1 + 1, S0, 1)
    c.line(bx0 + 1.6, by0, bx1 + 1.6, by1 + 1, S3, 1)
    # Перекладина.
    c.line(14, 14.5, 36, 10, S1, 4)
    c.line(14, 13, 36, 8.6, S0, 1)
    c.line(14, 16, 36, 11.6, S3, 1)
    # Волокна и сколы.
    for x, y in ((23, 22), (23, 18), (25, 8), (18, 14), (30, 11), (33, 10), (22, 26)):
        c.set(x, y, S3)
    c.set(13, 15, None)
    c.set(37, 9, None)
    c.set(26, 3, None)
    # Гвоздь в перекрестье.
    c.set(24, 12, ST0)
    c.set(25, 13, FK)
    # Тряпка на левом плече перекладины.
    c.poly([(16, 14), (20, 13), (21, 20), (19, 24), (18, 20), (16, 23), (15, 18)], W1)
    c.line(16, 15, 15.5, 21, W0, 1)
    c.line(20, 15, 20, 21, W2, 1)
    c.set(18, 17, W2)
    c.rect(16, 13, 20, 13, W2)
    # Сухая трава у подножия.
    for x, h, bend in ((7, 6, -2), (10, 9, -1), (13, 5, 1), (33, 7, 2), (37, 10, 1), (41, 5, 2)):
        _blade(c, x, h, bend, G1 if h > 6 else G2, G3)
    c.outline(FK)
    return c


def dec_bush():
    """Три надгробия за героем, 64×36: слева покосившийся каменный крест, в середине плита с
    круглым верхом, резным крестиком, строками и трещиной, справа расколотая плита с отбитым
    куском; у подножия земля и жухлая трава, на макушках мох."""
    rng = random.Random(364)
    c = Canvas(64, 36)
    # Каменный крест слева, наклон влево.
    c.line(11, 33, 8.5, 12, ST0, 5)
    c.line(3.5, 20, 14.5, 18.5, ST0, 5)
    c.line(13, 33, 10.6, 21, ST1, 2)
    c.line(4, 22, 14, 20.6, ST1, 1)
    c.line(10.6, 16, 10.2, 11, ST1, 1)
    c.set(9, 19, ST1)
    c.rect(5, 31, 16, 33, ST0)
    c.rect(12, 31, 16, 33, ST1)
    c.rect(5, 33, 16, 33, ST1)
    # Плита с круглым верхом.
    for y in range(3, 34):
        k = 13.5 - y
        half = 10.5 if k <= 0 else math.sqrt(max(0.0, 10.5 * 10.5 - k * k))
        for x in range(int(31 - half), int(31 + half) + 1):
            c.set(x, y, ST1 if x > 37 or (k > 0 and x - 31 > half - 2.5) else ST0)
    for d in range(-3, 4):
        c.set(30, 9 + d, ST1)
    for d in range(-2, 3):
        c.set(30 + d, 8, ST1)
    for yy, x0, x1 in ((16, 24, 35), (19, 25, 34), (22, 24, 36), (25, 26, 33)):
        c.rect(x0, yy, x1, yy, ST1)
    for x, y in ((38, 5), (37, 6), (36, 7), (36, 8), (37, 9), (36, 10), (35, 11), (35, 12), (36, 13)):
        c.set(x, y, FK)
    c.rect(21, 30, 41, 33, ST1)
    # Расколотая плита справа и отбитый кусок.
    c.poly([(46, 33), (45, 19), (49, 14), (52, 19), (55, 16), (58, 21), (58, 33)], ST0)
    c.poly([(55, 33), (54, 20), (55, 16), (58, 21), (58, 33)], ST1)
    c.rect(48, 22, 52, 22, ST1)
    c.rect(48, 25, 51, 25, ST1)
    c.line(52, 19, 51, 27, FK, 1)
    c.poly([(54, 34), (55, 29), (60, 28), (62, 34)], ST0)
    c.poly([(59, 34), (59, 29), (60, 28), (62, 34)], ST1)
    # Мох.
    for x, y in ((25, 6), (26, 5), (27, 4), (28, 4), (24, 8), (7, 10), (8, 10), (3, 18), (47, 16), (48, 15), (22, 29),
                 (23, 30), (40, 29)):
        c.set(x, y, G3)
    for x, y in ((27, 5), (26, 6), (8, 11), (48, 16)):
        c.set(x, y, G2)
    # Земля и трава у подножия.
    c.rect(2, 33, 62, 35, S2)
    for x in range(2, 63):
        if rng.random() < 0.5:
            c.set(x, 33, S1)
        if rng.random() < 0.3:
            c.set(x, 35, S3)
    for x, h, bend in ((2, 5, -1), (17, 7, 1), (19, 4, -1), (43, 8, 1), (44, 5, -2), (61, 4, 1), (20, 9, 2)):
        _blade(c, x, h, bend, G1 if h > 5 else G2, G3)
    c.outline(FK)
    return c


def dec_rock():
    """Череп у валуна, 32×20: гранёный камень со мхом слева, к нему привален череп с
    глазницами, носом и зубами."""
    c = Canvas(32, 20)
    # Валун.
    c.poly([(1, 19), (2, 12), (7, 7), (13, 8), (16, 13), (17, 19)], ST1)
    c.poly([(3, 12), (7, 8), (12, 9), (10, 13), (5, 14)], ST0)
    c.line(10, 14, 13, 18, FK, 1)
    for x, y in ((6, 7), (7, 6), (8, 7), (9, 7), (3, 11), (4, 10)):
        c.set(x, y, G3)
    c.set(7, 7, G2)
    c.set(8, 6, G3)
    # Череп: свод, скулы, челюсть.
    c.ellipse(23, 10.5, 6.2, 5.6, ST0)
    c.rect(19, 13, 27, 17, ST0)
    c.rect(20, 18, 26, 19, ST0)
    for y in range(5, 18):
        for x in range(26, 31):
            if c.get(x, y) == ST0 and (x > 27 or y > 14):
                c.set(x, y, ST1)
    c.rect(19, 10, 21, 12, FK)
    c.rect(24, 10, 26, 12, FK)
    c.set(20, 13, FK)
    c.set(25, 13, FK)
    c.set(22, 14, FK)
    c.set(23, 14, FK)
    c.set(23, 15, FK)
    c.rect(20, 17, 26, 17, ST1)
    for x in (21, 23, 25):
        c.set(x, 18, FK)
        c.set(x, 19, ST1)
    c.set(21, 6, ST1)
    c.set(22, 7, ST1)
    c.set(22, 8, ST1)
    # Трава.
    c.poly([(0, 19), (2, 15), (3, 19)], G2)
    c.poly([(15, 19), (17, 14), (18, 19)], G1)
    c.poly([(28, 19), (30, 15), (31, 19)], G2)
    c.outline(FK)
    return c


def dec_flowers():
    """Поминальные лампады в сухой траве, 32×20: три красных стаканчика с огоньком и увядший
    цветок."""
    rng = random.Random(365)
    c = Canvas(32, 20)
    for _ in range(8):
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 9), rng.uniform(-2, 2), rng.choice((G1, G2)), G3)
    jars = Canvas(32, 20)
    for x, top in ((6, 13), (15, 10), (26, 14)):
        jars.rect(x - 2, top, x + 2, 19, W1)
        jars.rect(x - 2, top, x - 2, 19, W0)
        jars.rect(x + 2, top, x + 2, 19, W2)
        jars.rect(x - 2, top, x + 2, top, ST1)
        jars.rect(x - 1, top + 2, x + 1, top + 3, PINK)
        jars.set(x, top + 2, G0)
        jars.rect(x - 2, 19, x + 2, 19, W2)
    # Увядший цветок: стебель дугой, головка поникла.
    jars.line(20, 19, 21, 11, G3, 1)
    jars.line(21, 11, 23, 10, G3, 1)
    jars.rect(23, 11, 24, 13, W1)
    jars.set(24, 13, W2)
    jars.set(22, 15, G2)
    jars.set(23, 14, G2)
    jars.outline(FK)
    c.paste(jars, 0, 0)
    # Пламя над стаканчиком поверх обводки.
    for x, top in ((6, 13), (15, 10), (26, 14)):
        c.set(x, top - 1, PINK)
        c.set(x, top - 2, G0)
    for _ in range(3):
        _blade(c, rng.uniform(9, 23), rng.uniform(3, 6), rng.uniform(-1, 1), G1, G3)
    return c


def dec_mush():
    """Рёбра из земли, 32×16: хребет вдоль земли и четыре ребра дугами разной высоты."""
    c = Canvas(32, 16)
    # Хребет с позвонками.
    c.rect(5, 14, 27, 15, ST1)
    for x in range(5, 28, 3):
        c.rect(x, 13, x + 1, 14, ST0)
    for x0, h in ((6, 9), (11, 12), (16, 11), (21, 8)):
        pts = []
        for i in range(13):
            a = math.pi * (1.0 - 0.72 * i / 12.0)
            pts.append((x0 + 3.5 + 3.5 * math.cos(a), 14.0 - h * math.sin(a)))
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            c.line(ax, ay, bx, by, ST0, 2)
        for (ax, ay) in pts[7:]:
            c.set(ax + 1, ay + 1, ST1)
    c.set(2, 15, ST0)
    c.set(3, 15, ST1)
    c.set(29, 15, ST0)
    c.outline(FK)
    return c


# --- Враги (палитра спрайтов) ------------------------------------------------------------------

def _danger(c):
    """Враг тропы: чёрная внешняя обводка основы становится красной: опасен, убить нельзя.
    Внутренние чёрные линии (щели между пальцами) остаются."""
    src = [row[:] for row in c.px]
    for y in range(c.h):
        for x in range(c.w):
            if src[y][x] != K:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < c.w and 0 <= ny < c.h) or src[ny][nx] is None:
                    c.px[y][x] = RED
                    break
    return c


def crab(i):
    """Ползун тропы: ползущая кисть из основы, четыре кадра шага на пальцах."""
    return _danger(zombies16.hand(i))


def drone(i):
    """Летун тропы: ворон из основы, четыре кадра взмаха, тело по центру кадра."""
    return _danger(zombies16.raven(i))


def sprites():
    """Ленты этой демки в палитре спрайтов (ленты героя в `zombies16.sprites`)."""
    return {
        "crab_walk": strip([crab(i) for i in range(4)]),
        "parrot_fly": strip([drone(i) for i in range(4)]),
    }


def backdrop():
    """Слои фона и ветви над кадром в палитре фона `ZOMBIES_BG`."""
    return {"par3_back": par3_back(), "par3_trees": par3_trees(), "par3_bushes": par3_bushes(),
            "canopy_front": canopy_front()}


def foreground():
    """Земля, арка, украшения в палитре переднего плана `ZOMBIES_FG`."""
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
    items = zombies16.shaded(sprites())
    for key, canvas in foreground().items():
        items[key] = (canvas, ZOMBIES_FG)
    for key, canvas in backdrop().items():
        items[key] = (canvas, ZOMBIES_BG)
    zombies16.save_sheet(path, items, scale=2)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
