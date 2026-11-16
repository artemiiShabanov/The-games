#!/usr/bin/env python3
"""Набор «Зомби» для гонки × 16/32-bit «псевдо-3D» (#137), зеркало `space_road16.py` и
`pixel_road16.py`: те же ключи, размеры холстов и порядок кадров, чтобы `racing_bit16.gd` брала
их без правок. Герой едет на пикапе с решёткой (вид сзади): голубой кузов в ржавчине, откидной
борт с полосой цвета экипажа, дуга с фарами и сварная решётка за кабиной, в кузове канистра,
лопата и запаска, на антенне рваный флаг; за рулём выживший в синей бейсболке и красной куртке.
Соперники на катафалках: высокий чёрный кузов с плавниками-фонарями, в заднем окне гроб и
шторки цвета экипажа, венок с лентой, по углам крыши лампады, из люка торчит зомби и машет
руками. У дороги мёртвое дерево с качелями из шины и вороном и каменный кельтский крест вместо
пальм, часовня с колоколом вместо хижины, надгробие с рукой из земли, мусорный бак, дощатые
указатели с дорожным конусом. На горизонте ночное небо с большой луной, тучами и зелёным
туманом, силуэт пригорода и холм с часовней, заболоченный погост вместо моря. Дорога асфальт,
обочина жухлая трава.

Пикап, катафалки и пропы в палитре `zombies16.PALETTE`, горизонт в своей (`ZOMBIES_SKY`), цвета
дороги лентой `road_colors` по местам `ROAD_COLORS`.

    python3 tools/zombies_road16.py --preview out.png [--keys=a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zombies16  # noqa: E402
from zombies16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS,  # noqa: E402
                       METAL, DARK, RED, VIOLET, PLUM)

# Палитра горизонта: небо, луна, погост, силуэты и туман. Места те же по смыслу, что у пиратов
# и космоса.
S0, S1, S2, S3, C0, C1, C2, M0, M1, M2, M3, I0, I1, I2, I3, SUN = range(16)
ZOMBIES_SKY = [
    (0x0A, 0x0C, 0x1E),  # S0  небо наверху
    (0x10, 0x16, 0x30),  # S1
    (0x18, 0x24, 0x44),  # S2
    (0x2C, 0x48, 0x4C),  # S3  небо у горизонта, зелёная дымка
    (0xB0, 0xB4, 0x98),  # C0  кратеры луны
    (0xE2, 0xE0, 0xC2),  # C1  луна
    (0xFA, 0xF8, 0xE6),  # C2  свет луны, яркие звёзды
    (0x2E, 0x40, 0x3E),  # M0  погост вдали
    (0x3C, 0x4A, 0x38),  # M1  погост
    (0x4E, 0x54, 0x34),  # M2  погост у дороги
    (0x18, 0x22, 0x26),  # M3  тень, кресты, вода
    (0x26, 0x36, 0x50),  # I0  тучи, пригород в дымке
    (0x0E, 0x12, 0x20),  # I1  холм с часовней, ближние силуэты
    (0x62, 0x92, 0x66),  # I2  зелёный туман
    (0xE8, 0xC2, 0x4A),  # I3  свет в окнах
    (0x5E, 0x62, 0x3C),  # SUN жухлая трава у кромки дороги
]

# Цвета дороги по местам ленты `road_colors` (демка берёт их по индексу).
ROAD_COLORS = [
    (0x52, 0x56, 0x62),  # 0 асфальт светлый
    (0x48, 0x4C, 0x58),  # 1 асфальт тёмный
    (0xB4, 0x3A, 0x2E),  # 2 бордюр красный, облезлый
    (0xD8, 0xD6, 0xC8),  # 3 бордюр белый
    (0xD8, 0xB8, 0x50),  # 4 разметка жёлтая
    (0x5E, 0x62, 0x3C),  # 5 жухлая трава светлая
    (0x52, 0x56, 0x34),  # 6 жухлая трава тёмная
    (0x2E, 0x40, 0x3E),  # 7 дымка вдали
]


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wellipse(c, cx, cy, rx, ry, col):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                _wset(c, x, y, col)


# --- Горизонт ----------------------------------------------------------------------------------

def sky():
    """Небо, 512×128, стыкуется по краям: чернота наверху, зелёная дымка и туман у горизонта,
    редкие звёзды, большая луна с кратерами и ореолом, плоские тучи, на диске луны две летучие
    мыши."""
    rng = random.Random(271)
    c = Canvas(512, 128)
    bands = [(0, S0), (38, S1), (74, S2), (104, S3)]
    for y in range(128):
        col = S0
        for start, b in bands:
            if y >= start:
                col = b
        for x in range(512):
            for start, b in bands[1:]:
                if start <= y < start + 3 and (x + y) % 2 == 0:
                    col = bands[bands.index((start, b)) - 1][1]
            c.set(x, y, col)
    # Звёзды: ночь мутная, их немного.
    for _ in range(110):
        x = rng.randint(0, 511)
        y = rng.randint(0, 96)
        c.set(x, y, S2 if y < 60 else S3)
    for _ in range(16):
        x = rng.randint(2, 509)
        y = rng.randint(2, 70)
        c.set(x, y, C2)
        if rng.random() < 0.3:
            c.set(x + 1, y, C0)
            c.set(x, y + 1, C0)
    # Луна: ореол шашечкой, диск, тень справа снизу, кратеры, блик слева сверху.
    px, py, pr = 150, 44, 23
    for y in range(py - pr - 9, py + pr + 10):
        for x in range(px - pr - 9, px + pr + 10):
            d = math.hypot(x - px, y - py)
            if pr < d <= pr + 4 and (x + y) % 2 == 0:
                c.set(x, y, S2)
            elif pr + 4 < d <= pr + 8 and (x + y) % 2 == 0 and y % 2 == 0:
                c.set(x, y, S2)
    _wellipse(c, px, py, pr, pr, C1)
    for y in range(py - pr, py + pr + 1):
        for x in range(px - pr, px + pr + 1):
            if math.hypot(x - px, y - py) > pr:
                continue
            if math.hypot(x - (px - 7), y - (py - 7)) > pr * 1.06:
                c.set(x, y, C0)
            elif math.hypot(x - (px - 9), y - (py - 10)) < 7 and (x + y) % 2 == 0:
                c.set(x, y, C2)
    for cx, cy, r in ((158, 36, 5), (143, 52, 4), (160, 56, 3), (140, 36, 2), (152, 46, 2), (166, 46, 2)):
        _wellipse(c, cx, cy, r, r * 0.85, C0)
        _wellipse(c, cx - 0.6, cy - 0.8, r - 1.2, (r - 1.2) * 0.8, C1)
        c.set(cx + r - 1, cy + r - 2, C0)
    # Летучие мыши на диске: тельце и ломаные крылья.
    for bx, by in ((139, 44), (156, 30)):
        for dx, dy in ((0, 0), (0, 1), (-1, -1), (1, -1), (-2, -1), (2, -1), (-3, 0), (3, 0), (-4, 1), (4, 1),
                       (-2, 0), (2, 0)):
            c.set(bx + dx, by + dy, I1)
    # Тучи: плоское дно, бугристый верх, одна наползает на луну.
    clouds = [(160, 60, 40), (40, 30, 34), (300, 22, 46), (420, 52, 38), (250, 84, 52), (500, 90, 44),
              (90, 96, 36), (370, 100, 30)]
    for cx, cy, w in clouds:
        for i in range(5):
            ox = (i - 2) * w * 0.38 + rng.uniform(-4, 4)
            rx = w * rng.uniform(0.3, 0.5)
            ry = rng.uniform(2.5, 5.5) * (1.0 if i in (1, 2, 3) else 0.7)
            for y in range(int(cy - ry - 1), int(cy) + 1):
                for x in range(int(cx + ox - rx - 1), int(cx + ox + rx + 2)):
                    if ((x - cx - ox) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                        _wset(c, x, y, I0)
        for x in range(int(cx - w * 0.9), int(cx + w * 0.9)):
            if (x // 3) % 2 == 0:
                _wset(c, x, cy + 1, I0)
    # Туман у горизонта: зелёные пряди, книзу гуще.
    for y in range(110, 128):
        for x in range(512):
            wave = math.sin(x * math.pi / 64 + y * 0.9) + math.sin(x * math.pi / 32 - y * 0.4)
            if y >= 122 and (x + y) % 2 == 0:
                c.set(x, y, I2)
            elif wave > 1.0 - (y - 110) * 0.06 and (x + y) % 2 == 0:
                c.set(x, y, I2)
    return c


def islands():
    """Пригород и холм с часовней на горизонте, 512×40, прозрачный верх: в дымке крыши домов с
    трубами, столбы с проводами и водонапорная башня, ближе чёрный холм с часовней, крестами и
    мёртвыми деревьями; в окнах редкий свет, понизу туман."""
    rng = random.Random(277)
    c = Canvas(512, 40)
    # Дома пригорода: коробка, двускатная крыша, труба.
    x = 4
    while x < 500:
        w = rng.randint(14, 24)
        h = rng.randint(6, 10)
        if 222 < x + w and x < 398:
            x += w + 4
            continue
        for xx in range(x, x + w + 1):
            for y in range(39 - h, 40):
                _wset(c, xx, y, I0)
        roof = w // 2 + 2
        for i in range(roof + 1):
            for xx in range(x + w // 2 - i, x + w // 2 + i + 1):
                _wset(c, xx, 39 - h - (roof * 0.6) + i * 0.6, I1)
        cxh = x + (3 if rng.random() < 0.5 else w - 4)
        for y in range(int(39 - h - roof * 0.6), 39 - h):
            _wset(c, cxh, y, I1)
            _wset(c, cxh + 1, y, I1)
        if rng.random() < 0.45:
            wx = x + rng.randint(3, w - 4)
            _wset(c, wx, 39 - h + 3, I3)
            _wset(c, wx + 1, 39 - h + 3, I3)
            _wset(c, wx, 39 - h + 4, I3)
        x += w + rng.randint(3, 14)
    # Водонапорная башня: бак на ногах.
    for tx in (446,):
        for y in range(8, 18):
            for xx in range(tx - 6, tx + 7):
                _wset(c, xx, y, I0)
        for xx in range(tx - 4, tx + 5):
            _wset(c, xx, 7, I0)
            _wset(c, xx, 18, I0)
        for y in range(18, 40):
            _wset(c, tx - 5 - (y - 18) * 0.12, y, I0)
            _wset(c, tx + 5 + (y - 18) * 0.12, y, I0)
            if y % 7 == 0:
                for xx in range(tx - 6, tx + 7):
                    _wset(c, xx, y, I0)
    # Столбы с перекладиной и провисшие провода между ними.
    poles = (30, 110, 190, 410, 490)
    for p in poles:
        for y in range(14, 40):
            _wset(c, p, y, I0)
        for xx in range(p - 4, p + 5):
            _wset(c, xx, 16, I0)
    for a, b in ((30, 110), (110, 190), (410, 490), (490, 542)):
        for xx in range(a, b):
            k = (xx - a) / (b - a)
            _wset(c, xx, 16 + 5 * math.sin(k * math.pi), I0)
    # Ближний холм: пологий, чтобы часовня со шпилем и крестом помещалась в 40 строк.
    cx, w, h = 310, 86, 13
    top_of = {}
    for xx in range(cx - w, cx + w + 1):
        k = (xx - cx) / w
        top = 39 - int(h * max(0.0, 1.0 - k * k) ** 0.8 + abs((xx * 5) % 7 - 3) * 0.3)
        top_of[xx] = top
        for y in range(top, 40):
            _wset(c, xx, y, I1)
    # Часовня на вершине: неф с крутой крышей, башня со шпилем и крестом, окна светятся.
    base = top_of[306]
    c.rect(294, base - 7, 312, base + 2, I1)
    for i in range(7):
        c.rect(293 + i, base - 8 - i, 313 - i, base - 8 - i, I1)
    c.rect(313, base - 13, 320, base + 2, I1)
    c.rect(312, base - 14, 321, base - 14, I1)
    for i in range(7):
        half = 4 - i * 0.6
        c.rect(int(round(316.5 - half)), base - 15 - i, int(round(316.5 + half)), base - 15 - i, I1)
    c.rect(316, base - 26, 317, base - 21, I1)
    c.rect(315, base - 25, 318, base - 25, I1)
    c.rect(301, base - 5, 302, base - 1, I3)
    c.set(306, base - 4, I3)
    c.set(306, base - 3, I3)
    c.rect(316, base - 11, 317, base - 9, I3)
    # Мёртвые деревья и кресты по гребню.
    for tx, th in ((262, 12), (346, 14), (372, 9)):
        ty = top_of[tx]
        for i in range(th):
            _wset(c, tx + (1 if i > th * 0.6 else 0), ty - i, I1)
        for i in range(5):
            _wset(c, tx - i, ty - th * 0.5 - i, I1)
            _wset(c, tx + 1 + i, ty - th * 0.65 - i * 0.8, I1)
            _wset(c, tx - 2 - i * 0.5, ty - th * 0.8 - i, I1)
    for kx in (244, 254, 276, 286, 332, 358, 384):
        ky = top_of[kx]
        for i in range(5):
            _wset(c, kx, ky - i, I1)
        _wset(c, kx - 1, ky - 3, I1)
        _wset(c, kx + 1, ky - 3, I1)
    # Туман понизу.
    for xx in range(512):
        if (xx // 2) % 2 == 0:
            _wset(c, xx, 39, I2)
        if math.sin(xx * math.pi / 32) > 0.3 and xx % 2 == 0:
            _wset(c, xx, 38, I2)
        if math.sin(xx * math.pi / 64 + 1.0) > 0.6 and xx % 2 == 1:
            _wset(c, xx, 36, I2)
    return c


def sea():
    """Заболоченный погост от горизонта, 512×24: тёмный вдали, светлее у дороги, лужи с лунной
    дорожкой, кресты и надгробия, пряди тумана, у нижней кромки полоса жухлой травы."""
    rng = random.Random(281)
    c = Canvas(512, 24)
    for y in range(24):
        col = M0 if y < 5 else (M1 if y < 15 else M2)
        c.rect(0, y, 511, y, col)
        if y in (5, 15):
            for x in range(0, 512, 2):
                c.set(x + (y % 2), y, M0 if y == 5 else M1)
    c.rect(0, 22, 511, 23, SUN)
    # Пряди тумана вдали.
    for _ in range(16):
        y = rng.randint(0, 6)
        x = rng.uniform(0, 512)
        for i in range(rng.randint(10, 30)):
            if i % 2 == 0:
                _wset(c, x + i, y, I2)
    # Лужи: тёмный овал, блик луны штрихом.
    for _ in range(18):
        y = rng.randint(4, 19)
        x = rng.uniform(0, 512)
        w = rng.randint(3, 5) + y // 3
        for i in range(-w, w + 1):
            _wset(c, x + i, y, M3)
        for i in range(-w + 2, w - 1):
            _wset(c, x + i, y + 1, M3)
        for i in range(-w // 2, 1):
            _wset(c, x + i, y, C0 if y > 10 else I0)
    # Кресты и надгробия: чем ближе, тем выше.
    for _ in range(40):
        y = rng.randint(3, 20)
        x = rng.uniform(0, 512)
        h = 2 + y // 6
        if rng.random() < 0.5:
            for i in range(h + 1):
                _wset(c, x, y - i, M3)
            _wset(c, x - 1, y - h + 1, M3)
            _wset(c, x + 1, y - h + 1, M3)
        else:
            for i in range(h):
                _wset(c, x, y - i, M3)
                _wset(c, x + 1, y - i, M3)
                if y > 12:
                    _wset(c, x + 2, y - i, M3)
            if y > 12:
                _wset(c, x, y - h + 1, I0)
        _wset(c, x + 2, y + 1, M3)
        _wset(c, x + 3, y + 1, M3)
    for _ in range(60):
        _wset(c, rng.uniform(0, 512), rng.randint(8, 21), M3 if rng.random() < 0.5 else SUN)
    return c


# --- Пикап, катафалки и пропы (палитра спрайтов) ------------------------------------------------

def _tire(c, cx, cy, r, w, phase):
    """Колесо сзади: широкая шина, протектор ёлочкой бежит вниз (`phase` 0..1), понизу грязь."""
    c.rect(cx - w, cy - r + 3, cx + w, cy + r - 3, K)
    c.rect(cx - w + 2, cy - r, cx + w - 2, cy + r, K)
    c.rect(cx - w + 2, cy - r + 3, cx + w - 2, cy + r - 3, NAVY)
    c.rect(cx - w + 2, cy - r + 3, cx - w + 3, cy + r - 3, SEA)
    step = 6
    off = int(phase * step)
    for y in range(int(cy - r + 4) + off, int(cy + r - 4), step):
        for i in range(0, w - 2):
            c.set(cx - i, y + i * 0.5, K)
            c.set(cx + i, y + i * 0.5, K)
            c.set(cx - i, y + i * 0.5 + 1, K)
            c.set(cx + i, y + i * 0.5 + 1, K)
        c.rect(cx - 2, y + 2, cx + 2, y + 2, GREY)
    c.rect(cx - w + 3, cy + r - 4, cx + w - 4, cy + r - 2, METAL)


def pickup(lean, phase, accent):
    """Пикап со спины, 160×104: два широких колеса, голубой кузов в ржавчине, откидной борт с
    полосой цвета `accent`, дуга с фарами и сварная решётка за кабиной, в кузове канистра,
    лопата и запаска, антенна с рваным флагом цвета `accent`; за рулём выживший. `lean` −1..1
    крен."""
    c = Canvas(160, 104)
    sh = lean * 6
    lo = sh * 0.3
    mid = sh * 0.6
    _tire(c, 22 + lo, 79, 23, 9, phase)
    _tire(c, 138 + lo, 79, 23, 9, phase)
    # Мост, редуктор, брызговики.
    c.rect(26 + lo, 86, 134 + lo, 89, DARK)
    c.ellipse(80 + lo, 90, 9, 6, DARK)
    c.ellipse(80 + lo, 90, 4, 3, METAL)
    for x in (39, 121):
        c.rect(x - 6 + lo, 84, x + 6 + lo, 97, K)
        c.rect(x - 4 + lo, 90, x + 4 + lo, 92, RED)
    # Выхлопная труба и дым: клуб растёт и отлетает.
    c.rect(54 + lo, 91, 61 + lo, 94, GREY)
    if phase < 0.25:
        c.ellipse(56 + lo, 98, 4, 3, GREY)
    else:
        c.ellipse(51 + lo, 98, 5, 3.5, GREY)
        c.ellipse(60 + lo, 99, 2, 2, WHITE)
    # Кабина без крыши: задняя стенка, дуга из трубы, решётка в проёме.
    top = sh * 1.3
    c.poly([(46 + top, 10), (114 + top, 10), (116 + sh, 48), (44 + sh, 48)], NAVY)
    for i in range(1, 9):
        x = 46 + i * 7.5
        c.line(x + top, 11, x + sh, 34, GREY, 1)
    for y in (17, 25):
        k = (y - 10) / 38.0
        s = top + (sh - top) * k
        c.line(47 + s, y, 113 + s, y, GREY, 1)
    c.line(46 + top, 9, 44 + sh, 48, METAL, 4)
    c.line(114 + top, 9, 116 + sh, 48, METAL, 4)
    c.line(46 + top, 9, 114 + top, 9, METAL, 4)
    # Фары на дуге: корпус и горящее стекло.
    for x in (57, 72, 88, 103):
        c.rect(x - 5 + top, 1, x + 5 + top, 7, DARK)
        c.rect(x - 3 + top, 2, x + 3 + top, 5, GOLD)
        c.rect(x - 3 + top, 2, x - 1 + top, 3, WHITE)
    # Выживший со спины: куртка, шея, бейсболка козырьком вперёд.
    x0 = 80 + sh * 1.2
    c.ellipse(x0, 41, 19, 11, RED)
    c.line(x0 - 13, 37, x0 - 20, 46, RED, 7)
    c.line(x0 + 13, 37, x0 + 20, 46, RED, 7)
    c.rect(x0 - 6, 31, x0 + 6, 34, DARK)
    c.rect(x0 - 1, 34, x0, 46, DARK)
    c.rect(x0 - 3, 27, x0 + 3, 31, SKIN)
    c.ellipse(x0, 21, 8, 8, SKIN)
    for y in range(20, 30):
        for x in range(int(x0) - 9, int(x0) + 10):
            if c.get(x, y) == SKIN and y < 28 and abs(x - x0) < 7.5:
                c.set(x, y, DARK)
    c.set(x0 - 8, 22, SKIN)
    c.set(x0 + 8, 22, SKIN)
    cap = Canvas(160, 104)
    cap.ellipse(x0, 19, 9.5, 8, SEA)
    for y in range(21, 40):
        for x in range(160):
            cap.px[y][x] = None
    c.paste(cap, 0, 0)
    c.rect(x0 - 3, 18, x0 + 3, 20, DARK)
    c.rect(x0 - 2, 17, x0 + 2, 17, NAVY)
    c.rect(x0 - 1, 11, x0 + 1, 11, WHITE)
    # Стенка кабины до плеч.
    c.poly([(44 + sh, 40), (116 + sh, 40), (118 + sh, 50), (42 + sh, 50)], SKY)
    c.line(44 + sh, 40, 116 + sh, 40, WHITE, 1)
    c.rect(70 + sh, 43, 90 + sh, 47, AQUA)
    # Груз по бокам кабины: канистра и лопата слева, запаска справа.
    c.line(35 + sh, 48, 31 + sh * 1.3, 14, METAL, 2)
    c.poly([(26 + sh * 1.3, 2), (36 + sh * 1.3, 2), (37 + sh * 1.3, 12), (31 + sh * 1.3, 17), (25 + sh * 1.3, 12)], GREY)
    c.rect(30 + sh * 1.3, 4, 31 + sh * 1.3, 10, WHITE)
    c.rect(33 + sh, 30, 43 + sh, 48, RED)
    c.rect(35 + sh, 26, 38 + sh, 30, RED)
    c.rect(40 + sh, 27, 42 + sh, 29, GREY)
    c.line(35 + sh, 33, 41 + sh, 45, DARK, 1)
    c.line(41 + sh, 33, 35 + sh, 45, DARK, 1)
    c.ellipse(126 + sh, 38, 10, 10, K)
    c.ellipse(126 + sh, 38, 8, 8, NAVY)
    c.ellipse(126 + sh, 38, 4, 4, GREY)
    c.ellipse(126 + sh, 38, 1.5, 1.5, DARK)
    # Антенна с рваным флагом у правого заднего угла.
    c.rect(137 + sh, 2, 138 + sh, 50, GREY)
    flap = 3 * math.sin(phase * math.pi * 2)
    # Флаг короткий: при крене вправо кончик с обводкой остаётся в кадре.
    fx = 139 + sh
    c.poly([(fx, 3), (fx + 12, 4 + flap), (fx + 9, 8 + flap), (fx + 12, 11 + flap), (fx + 9, 14 + flap * 0.5),
            (fx + 12, 18 + flap * 0.5), (fx, 17)], accent)
    c.rect(fx + 2, 9 + flap * 0.3, fx + 7, 10 + flap * 0.3, WHITE)
    c.rect(fx + 4, 7 + flap * 0.3, fx + 5, 12 + flap * 0.3, WHITE)
    # Кузов: борта, откидной борт с тиснением, ржавчина.
    c.poly([(28 + sh, 48), (132 + sh, 48), (130 + mid, 86), (30 + mid, 86)], SKY)
    c.rect(28 + sh, 47, 132 + sh, 49, AQUA)
    c.line(29 + sh, 47, 131 + sh, 47, WHITE, 1)
    for x in (42, 118):
        c.line(x + sh, 51, x + mid, 85, AQUA, 1)
    c.line(47 + sh * 0.9, 55, 113 + sh * 0.9, 55, AQUA, 1)
    c.line(47 + mid, 81, 113 + mid, 81, AQUA, 1)
    c.line(47 + sh * 0.9, 55, 47 + mid, 81, AQUA, 1)
    c.line(113 + sh * 0.9, 55, 113 + mid, 81, AQUA, 1)
    c.rect(52 + sh * 0.8, 64, 108 + sh * 0.8, 71, accent)
    c.rect(52 + sh * 0.8, 64, 108 + sh * 0.8, 64, WHITE)
    c.rect(73 + sh * 0.9, 57, 87 + sh * 0.9, 60, DARK)
    c.rect(75 + sh * 0.9, 58, 85 + sh * 0.9, 58, GREY)
    for rx, ry, rw, rh in ((52, 78, 7, 3), (104, 80, 9, 3), (96, 58, 4, 2), (60, 52, 5, 1.5), (120, 74, 4, 5)):
        c.ellipse(rx + mid, ry, rw, rh, METAL)
        c.ellipse(rx + mid + 1, ry + 0.5, rw * 0.5, rh * 0.5, DARK)
    # Фонари по углам: стоп и поворотник.
    for x in (35, 125):
        c.rect(x + sh * 0.9 - 4, 53, x + sh * 0.9 + 4, 73, DARK)
        c.rect(x + sh * 0.9 - 3, 54, x + sh * 0.9 + 3, 65, RED)
        c.rect(x + sh * 0.9 - 3, 54, x + sh * 0.9 - 2, 56, WHITE)
        c.rect(x + sh * 0.9 - 3, 67, x + sh * 0.9 + 3, 72, GOLD)
    # Бампер с номером и крюком.
    c.rect(26 + mid, 84, 134 + mid, 91, GREY)
    c.rect(26 + mid, 84, 134 + mid, 84, WHITE)
    c.rect(70 + mid, 85, 90 + mid, 90, WHITE)
    for i in range(5):
        c.rect(72 + mid + i * 4, 87, 73 + mid + i * 4, 88, K)
    c.rect(78 + lo, 92, 82 + lo, 96, DARK)
    c.finish()
    return c


def hearse(lean, phase, accent):
    """Катафалк со спины, 160×104: высокий чёрный кузов с хромом и плавниками-фонарями, в заднем
    окне гроб и шторки цвета `accent`, на двери венок с лентой и полоса цвета `accent`, по углам
    крыши лампады (мерцают по `phase`), из-под днища зелёный туман; из люка в крыше торчит зомби
    и машет руками."""
    c = Canvas(160, 104)
    sh = lean * 6
    lo = sh * 0.3
    mid = sh * 0.7
    blink = phase < 0.25
    # Туман из-под днища.
    c.ellipse(80 + lo, 98, 50 + (4 if blink else 0), 4.5, PLUM)
    c.ellipse(80 + lo, 97, 34 + (0 if blink else 6), 2.5, VIOLET)
    _tire(c, 28 + lo, 84, 18, 8, phase)
    _tire(c, 132 + lo, 84, 18, 8, phase)
    # Зомби из люка: лохмотья, плечи, руки вверх по очереди, лысеющая голова.
    zx = 80 + sh * 1.3
    c.ellipse(zx, 24, 13, 10, GREY)
    c.rect(zx - 5, 18, zx - 3, 30, METAL)
    c.rect(zx + 4, 20, zx + 6, 24, RED)
    up_l, up_r = (7, 14) if blink else (14, 7)
    for side, hy in ((-1, up_l), (1, up_r)):
        sx = zx + side * 11
        c.line(sx, 21, sx + side * 9, hy + 6, GREY, 6)
        c.line(sx + side * 9, hy + 6, sx + side * 12, hy, VIOLET, 5)
        c.ellipse(sx + side * 12, hy - 1, 3, 3, VIOLET)
        for f in (-1, 0, 1):
            c.line(sx + side * 12 + f * 2, hy - 2, sx + side * 12 + f * 3, hy - 6, VIOLET, 1)
    c.rect(zx - 3, 12, zx + 3, 17, VIOLET)
    c.ellipse(zx, 8, 7, 7.5, VIOLET)
    c.ellipse(zx - 3, 4, 3, 2, DARK)
    c.ellipse(zx + 4, 6, 2, 3, DARK)
    c.rect(zx - 1, 9, zx + 2, 10, PLUM)
    c.set(zx - 7, 9, PLUM)
    c.set(zx + 7, 9, PLUM)
    # Кузов: крыша дугой, высокая надстройка, широкий низ.
    c.ellipse(80 + sh, 33, 56, 9, NAVY)
    c.poly([(24 + sh, 32), (136 + sh, 32), (142 + mid, 56), (18 + mid, 56)], NAVY)
    c.poly([(18 + mid, 54), (142 + mid, 54), (140 + lo, 88), (20 + lo, 88)], NAVY)
    c.ellipse(80 + sh, 28, 44, 3, SEA)
    # Лампады по углам крыши.
    for x in (33, 127):
        lx = x + sh * 1.1
        c.rect(lx - 1, 21, lx + 1, 27, GREY)
        c.rect(lx - 4, 11, lx + 4, 21, DARK)
        c.rect(lx - 2, 13, lx + 2, 19, GOLD if blink else BRASS)
        c.rect(lx - 1, 15 if blink else 16, lx + 1, 19, WHITE if blink else GOLD)
        c.poly([(lx - 5, 11), (lx + 5, 11), (lx, 5)], GREY)
    # Плавники с высокими фонарями.
    for side in (-1, 1):
        ex = 80 + side * 62 + mid
        c.poly([(ex - side * 6, 46), (ex + side * 6, 38), (ex + side * 5, 80), (ex - side * 6, 82)], NAVY)
        c.poly([(ex + side * 1, 46), (ex + side * 5, 42), (ex + side * 4, 74), (ex + side * 1, 74)], RED)
        c.line(ex + side * 6, 38, ex + side * 1, 44, GREY, 2)
        c.rect(ex + min(side * 1, side * 4), 50, ex + max(side * 1, side * 4), 51, GOLD if blink else RED)
    # Заднее окно в хромовой раме: гроб торцом, шторки, кисти.
    c.poly([(40 + sh, 36), (120 + sh, 36), (124 + mid, 56), (36 + mid, 56)], GREY)
    c.poly([(43 + sh, 38), (117 + sh, 38), (120 + mid, 53), (40 + mid, 53)], K)
    gx = 80 + sh * 0.85
    c.poly([(gx - 9, 40), (gx + 9, 40), (gx + 14, 46), (gx + 10, 53), (gx - 10, 53), (gx - 14, 46)], METAL)
    c.poly([(gx - 7, 42), (gx + 7, 42), (gx + 11, 46), (gx + 8, 53), (gx - 8, 53), (gx - 11, 46)], DARK)
    c.rect(gx - 1, 43, gx, 52, GOLD)
    c.rect(gx - 4, 45, gx + 3, 46, GOLD)
    for side in (-1, 1):
        wx = 80 + side * 37 + sh * 0.9
        c.poly([(wx, 38), (wx - side * 17, 38), (wx - side * 6, 46), (wx + side * 2, 53), (wx + side * 2, 46)], accent)
        c.line(wx - side * 14, 39, wx - side * 3, 47, WHITE, 1)
        c.rect(wx - side * 6 - 1, 46, wx - side * 6 + 1, 49, GOLD)
    # Хромовый пояс, полоса экипажа, шов дверей и ручки.
    c.rect(18 + mid, 57, 142 + mid, 58, GREY)
    c.rect(22 + mid * 0.8, 78, 138 + mid * 0.8, 80, accent)
    c.line(80 + mid, 59, 80 + lo, 77, SEA, 1)
    c.rect(72 + mid * 0.9, 62, 76 + mid * 0.9, 63, GREY)
    c.rect(84 + mid * 0.9, 62, 88 + mid * 0.9, 63, GREY)
    c.line(28 + mid, 60, 60 + mid, 60, SEA, 1)
    c.line(100 + mid, 60, 132 + mid, 60, SEA, 1)
    # Венок на двери: кольцо, цветы, лента.
    wx, wy = 80 + mid * 0.9, 69
    for a in range(0, 360, 12):
        ra = math.radians(a)
        c.ellipse(wx + math.cos(ra) * 7, wy + math.sin(ra) * 6, 2, 2, PLUM if (a // 12) % 2 else VIOLET)
    for a in (40, 150, 260):
        ra = math.radians(a)
        c.set(wx + math.cos(ra) * 7, wy + math.sin(ra) * 6, WHITE)
    c.poly([(wx - 9, 71), (wx - 3, 68), (wx - 2, 71), (wx - 10, 76)], accent)
    c.poly([(wx + 9, 71), (wx + 3, 68), (wx + 2, 71), (wx + 10, 76)], accent)
    c.rect(wx - 2, 67, wx + 2, 70, accent)
    # Бампер и номер.
    c.rect(16 + lo, 85, 144 + lo, 91, GREY)
    c.rect(16 + lo, 85, 144 + lo, 85, WHITE)
    c.rect(70 + lo, 86, 90 + lo, 90, WHITE)
    c.rect(73 + lo, 88, 87 + lo, 88, K)
    for x in (30, 130):
        c.rect(x + lo - 3, 82, x + lo + 3, 84, GOLD if blink else BRASS)
    c.finish()
    return c


def carts_strip(accent, alien):
    """Три крена (влево, прямо, вправо) по два кадра: лента 6 кадров по 160, порядок как у пиратов.
    `alien`: соперник (катафалк), иначе пикап героя."""
    frames = []
    for lean in (-1.0, 0.0, 1.0):
        for ph in (0.0, 0.5):
            frames.append(hearse(lean, ph, accent) if alien else pickup(lean, ph, accent))
    return strip(frames)


def _limb(c, pts, w0, w1, col):
    """Сук ломаной линией: толщина плавно убывает от `w0` к `w1`."""
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    done = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(seg * 2) + 1
        for i in range(n + 1):
            k = i / n
            w = w0 + (w1 - w0) * (done + seg * k) / total
            c.ellipse(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, w / 2, w / 2, col)
        done += seg


def dead_tree():
    """Мёртвое дерево у обочины, 120×240 (место пальмы): кривой ствол с дуплом и корнями, три
    голых сука с ветками, на левом качели из шины, на правом ворон, у корней бурьян и
    покосившийся крест."""
    c = Canvas(120, 240)
    # Корни и ствол.
    c.poly([(36, 239), (50, 222), (58, 239)], METAL)
    c.poly([(62, 239), (70, 224), (88, 239)], METAL)
    _limb(c, [(60, 239), (56, 204), (62, 166), (57, 128), (60, 104)], 22, 13, METAL)
    # Суки: левый, средний вверх, правый; на каждом ветки.
    _limb(c, [(58, 126), (42, 100), (27, 86), (15, 62), (11, 40)], 10, 2, METAL)
    _limb(c, [(27, 86), (10, 86), (3, 76)], 4, 1.5, METAL)
    _limb(c, [(15, 62), (25, 46), (23, 30)], 3, 1.5, METAL)
    _limb(c, [(11, 40), (4, 28)], 2, 1, METAL)
    _limb(c, [(60, 106), (66, 76), (60, 50), (66, 26), (62, 6)], 11, 2, METAL)
    _limb(c, [(60, 50), (46, 38), (43, 20)], 4, 1.5, METAL)
    _limb(c, [(66, 26), (78, 16), (81, 4)], 3, 1.5, METAL)
    _limb(c, [(64, 66), (76, 54), (76, 42)], 3, 1.5, METAL)
    _limb(c, [(61, 116), (80, 96), (98, 88), (110, 68), (114, 48)], 9, 2, METAL)
    _limb(c, [(98, 88), (113, 92), (118, 104)], 4, 1.5, METAL)
    _limb(c, [(110, 68), (99, 54), (101, 38)], 3, 1.5, METAL)
    _limb(c, [(80, 96), (87, 78), (83, 64)], 3, 1.5, METAL)
    # Кора: борозды, дупло, сломанный сучок.
    for x0, y0, x1, y1 in ((54, 232, 52, 206), (62, 226, 64, 196), (58, 190, 56, 150), (64, 160, 62, 132),
                           (54, 140, 55, 118), (66, 228, 68, 212)):
        c.line(x0, y0, x1, y1, DARK, 1)
    c.ellipse(60, 176, 5, 8, DARK)
    c.ellipse(60, 177, 3, 6, K)
    c.poly([(68, 150), (78, 144), (77, 149), (69, 155)], METAL)
    c.rect(76, 145, 77, 148, TAN)
    # Лунный свет по левой кромке ствола.
    for y in range(112, 236):
        for x in range(30, 70):
            if c.get(x, y) == METAL and c.get(x - 1, y) is None:
                c.set(x, y, TAN)
                break
    # Качели из шины на верёвке.
    c.rect(26, 88, 26, 132, TAN)
    c.ellipse(26, 144, 12, 13, NAVY)
    c.ellipse(26, 144, 9, 10, K)
    hole = Canvas(120, 240)
    hole.ellipse(26, 144, 6, 7, K)
    for y in range(240):
        for x in range(120):
            if hole.px[y][x] is not None:
                c.px[y][x] = None
    c.rect(24, 131, 28, 134, TAN)
    # Ворон на правом суку.
    c.ellipse(100, 80, 7, 5, K)
    c.ellipse(105, 74, 4, 4, K)
    c.poly([(93, 80), (84, 86), (86, 80)], K)
    c.poly([(108, 74), (114, 76), (108, 77)], BRASS)
    c.line(96, 79, 103, 82, SEA, 1)
    c.mark(106, 73, WHITE)
    # Бурьян и крест у корней.
    for x, h, lean_ in ((8, 22, -3), (14, 30, 2), (20, 18, 4), (32, 14, -2), (90, 16, 3), (112, 24, -4), (116, 14, 2)):
        c.line(x, 239, x + lean_, 239 - h, BRASS, 1)
        c.line(x + 1, 239, x + lean_ + 2, 239 - h * 0.7, GOLD, 1)
    c.line(100, 239, 104, 204, WHITE, 3)
    c.line(94, 218, 112, 214, WHITE, 3)
    c.finish()
    return c


def celtic_cross():
    """Каменный крест на постаменте, 120×240 (место второй пальмы): кельтский крест с кольцом,
    трещины и мох, ступени постамента с табличкой, свеча, бурьян и малый деревянный крест."""
    c = Canvas(120, 240)
    # Постамент ступенями.
    c.rect(16, 222, 104, 239, GREY)
    c.rect(26, 204, 94, 221, GREY)
    c.rect(38, 190, 82, 203, GREY)
    for x0, x1, y in ((16, 104, 222), (26, 94, 204), (38, 82, 190)):
        c.rect(x0, y, x1, y + 1, WHITE)
        c.rect(x0, y + 12, x1, y + 12, METAL)
    # Кольцо, ствол, перекладина с расширением к концам, навершие.
    for y in range(36, 112):
        for x in range(20, 100):
            d = math.hypot(x - 60, y - 73)
            if 25 <= d <= 32:
                c.set(x, y, GREY)
    c.poly([(51, 190), (69, 190), (67, 44), (53, 44)], GREY)
    c.poly([(48, 12), (72, 12), (68, 46), (52, 46)], GREY)
    c.poly([(48, 12), (60, 5), (72, 12)], GREY)
    c.poly([(18, 60), (53, 65), (53, 81), (18, 86)], GREY)
    c.poly([(102, 60), (67, 65), (67, 81), (102, 86)], GREY)
    c.rect(52, 64, 68, 82, GREY)
    # Свет слева: кромки ствола, кольца и перекладины.
    c.line(54, 46, 52, 188, WHITE, 2)
    c.line(50, 14, 54, 44, WHITE, 2)
    c.line(19, 61, 52, 66, WHITE, 1)
    c.line(68, 66, 101, 61, WHITE, 1)
    for a in range(150, 250, 2):
        ra = math.radians(a)
        c.set(60 + math.cos(ra) * 31, 73 + math.sin(ra) * 31, WHITE)
        c.set(60 + math.cos(ra) * 30, 73 + math.sin(ra) * 30, WHITE)
    # Резьба: узел в перекрестье, плетёнка на стволе, насечки на перекладине.
    c.ellipse(60, 73, 7, 7, WHITE)
    c.ellipse(60, 73, 4, 4, METAL)
    c.ellipse(60, 73, 1.5, 1.5, WHITE)
    for y in range(96, 180, 14):
        c.line(56, y, 64, y + 7, METAL, 1)
        c.line(64, y, 56, y + 7, METAL, 1)
    for x in (26, 34, 42, 78, 86, 94):
        c.rect(x, 70, x + 1, 76, METAL)
    c.rect(57, 20, 63, 21, METAL)
    c.rect(59, 17, 60, 36, METAL)
    # Трещины и отбитый край.
    c.line(66, 112, 60, 124, DARK, 1)
    c.line(60, 124, 64, 136, DARK, 1)
    c.line(90, 66, 84, 74, DARK, 1)
    c.line(84, 74, 88, 82, DARK, 1)
    c.line(30, 206, 38, 214, DARK, 1)
    c.line(38, 214, 34, 221, DARK, 1)
    # Мох.
    for mx, my, rx, ry in ((22, 61, 5, 2), (56, 190, 9, 2), (30, 205, 8, 2), (96, 223, 8, 2), (66, 44, 3, 5),
                           (40, 96, 4, 3)):
        c.ellipse(mx, my, rx, ry, VIOLET)
        c.ellipse(mx + 1, my + 1, rx * 0.5, ry * 0.5, PLUM)
    # Табличка.
    c.rect(44, 208, 76, 218, METAL)
    c.rect(46, 210, 74, 216, BRASS)
    for y in (211, 213, 215):
        c.rect(49, y, 71 - (y % 3) * 4, y, DARK)
    # Свеча на ступени.
    c.rect(86, 196, 88, 203, WHITE)
    c.rect(87, 192, 87, 195, GOLD)
    c.mark(87, 193, WHITE)
    # Малый деревянный крест и бурьян.
    c.line(8, 239, 12, 204, METAL, 3)
    c.line(3, 216, 19, 212, METAL, 3)
    for x, h, lean_ in ((2, 16, 2), (22, 20, -3), (28, 12, 2), (98, 22, 3), (106, 30, -2), (112, 18, 4), (117, 24, -3)):
        c.line(x, 239, x + lean_, 239 - h, BRASS, 1)
        c.line(x + 1, 239, x + lean_ + 2, 239 - h * 0.7, GOLD, 1)
    c.finish()
    return c


# Буквы 3×5 для надписи на камне.
_GLYPHS = {"R": ("##.", "#.#", "##.", "#.#", "#.#"), "I": ("###", ".#.", ".#.", ".#.", "###"),
           "P": ("##.", "#.#", "##.", "#..", "#..")}


def headstone():
    """Надгробие у дороги, 96×64: камень с полукруглым верхом, надпись, трещина и мох, перед ним
    свежий холмик, из которого тянется рука зомби, сбоку покосившийся крест."""
    c = Canvas(96, 64)
    # Покосившийся крест слева позади.
    c.line(10, 63, 14, 30, METAL, 3)
    c.line(4, 42, 21, 39, METAL, 3)
    # Камень.
    c.ellipse(46, 22, 21, 18, GREY)
    c.rect(25, 22, 67, 60, GREY)
    c.rect(25, 22, 27, 58, WHITE)
    for a in range(180, 262, 2):
        ra = math.radians(a)
        c.set(46 + math.cos(ra) * 20, 22 + math.sin(ra) * 17, WHITE)
        c.set(46 + math.cos(ra) * 19, 22 + math.sin(ra) * 16, WHITE)
    # Рамка и надпись.
    for a in range(180, 361, 3):
        ra = math.radians(a)
        c.set(46 + math.cos(ra) * 15, 23 + math.sin(ra) * 12, METAL)
    c.rect(31, 23, 31, 50, METAL)
    c.rect(61, 23, 61, 50, METAL)
    for i, ch in enumerate("RIP"):
        for ry, row in enumerate(_GLYPHS[ch]):
            for rx, v in enumerate(row):
                if v == "#":
                    c.rect(36 + i * 8 + rx * 2, 18 + ry * 2, 37 + i * 8 + rx * 2, 19 + ry * 2, DARK)
    for y, x0, x1 in ((33, 36, 57), (37, 38, 55), (41, 36, 52)):
        c.rect(x0, y, x1, y, METAL)
    # Трещина, скол, мох.
    c.line(58, 6, 55, 14, DARK, 1)
    c.line(55, 14, 60, 22, DARK, 1)
    c.line(60, 22, 58, 30, DARK, 1)
    for x, y in ((66, 9), (67, 10), (65, 8), (67, 11)):
        c.px[y][x] = None
    c.ellipse(31, 50, 6, 4, VIOLET)
    c.ellipse(32, 51, 3, 2, PLUM)
    c.ellipse(40, 6, 5, 1.5, VIOLET)
    # Холмик свежей земли.
    c.ellipse(52, 66, 44, 13, METAL)
    for x, y in ((20, 60), (34, 57), (48, 59), (62, 56), (76, 60), (88, 61), (56, 61), (28, 62), (70, 62)):
        c.rect(x, y, x + 2, y + 1, DARK)
    for x, y in ((40, 61), (66, 59), (84, 58)):
        c.set(x, y, TAN)
    # Рука зомби из земли: рукав, кисть, растопыренные пальцы.
    c.line(80, 60, 79, 40, VIOLET, 6)
    c.rect(76, 50, 83, 57, GREY)
    c.rect(76, 57, 78, 59, GREY)
    c.rect(81, 57, 83, 60, GREY)
    c.ellipse(79, 35, 5, 5, VIOLET)
    for x0, y0, x1, y1 in ((75, 33, 71, 25), (78, 31, 77, 21), (81, 31, 83, 22), (83, 34, 88, 27), (75, 37, 70, 36)):
        c.line(x0, y0, x1, y1, VIOLET, 2)
    c.rect(78, 36, 80, 37, PLUM)
    # Бурьян.
    for x, h, lean_ in ((2, 12, 2), (22, 9, -2), (90, 14, 3), (94, 9, -1)):
        c.line(x, 63, x + lean_, 63 - h, BRASS, 1)
    return c.finish()


def trash_can():
    """Мусорный бак, 48×64: ребристый жестяной бак с обручами и ручкой, крышка съехала набок,
    в щели горят глаза крысы, по стенке течёт зелёная слизь."""
    c = Canvas(48, 64)
    c.poly([(8, 18), (40, 18), (37, 62), (11, 62)], GREY)
    for x in (14, 19, 24, 29, 34):
        c.line(x, 22, x + (24 - x) * -0.08, 59, METAL, 1)
        c.line(x - 1, 22, x - 1 + (24 - x) * -0.08, 59, WHITE, 1)
    c.rect(8, 24, 40, 26, WHITE)
    c.rect(8, 27, 40, 27, METAL)
    c.rect(10, 51, 38, 53, WHITE)
    c.rect(10, 54, 38, 54, METAL)
    c.rect(11, 60, 37, 62, METAL)
    # Боковые ручки.
    c.rect(4, 32, 8, 34, METAL)
    c.rect(4, 34, 5, 42, METAL)
    c.rect(40, 32, 44, 34, METAL)
    c.rect(43, 34, 44, 42, METAL)
    # Щель под крышкой и крышка набекрень.
    c.poly([(9, 12), (40, 9), (40, 19), (8, 19)], K)
    zombies16._oval(c, 23, 10, 22, 5.5, -0.16, GREY)
    zombies16._oval(c, 22, 8.5, 16, 3, -0.16, WHITE)
    zombies16._oval(c, 23, 9.5, 14, 2.5, -0.16, GREY)
    c.rect(18, 1, 28, 2, METAL)
    c.rect(18, 2, 19, 6, METAL)
    c.rect(27, 1, 28, 5, METAL)
    c.mark(30, 15, GOLD)
    c.mark(34, 14, GOLD)
    # Вмятина и слизь.
    c.ellipse(30, 40, 4, 6, METAL)
    c.ellipse(31, 40, 2, 4, DARK)
    c.rect(12, 18, 16, 21, VIOLET)
    c.rect(13, 21, 15, 36, VIOLET)
    c.ellipse(14, 37, 2.5, 2.5, VIOLET)
    c.rect(21, 18, 22, 28, VIOLET)
    c.set(14, 30, WHITE)
    return c.finish()


def sign(right):
    """Указатель поворота, 96×112: жёлтый щит из трёх досок с обломанными концами на деревянном
    столбе, чёрные шевроны в сторону поворота, гвозди, дырки от пуль, красный отпечаток ладони;
    столб обмотан колючей проволокой, у основания дорожный конус."""
    c = Canvas(96, 112)
    d = 1 if right else -1
    # Столб и подпорка.
    c.rect(44, 50, 51, 111, METAL)
    c.rect(44, 57, 45, 111, TAN)
    for y in (66, 80, 97):
        c.rect(48, y, 49, y + 6, DARK)
    c.line(48 - d * 16, 111, 48 - d * 2, 86, METAL, 4)
    # Колючая проволока витками.
    for y in (70, 76):
        c.line(40, y + 2, 55, y - 2, GREY, 1)
        for x in (41, 47, 53):
            c.set(x, y - 1 + (47 - x) // 6, WHITE)
            c.set(x, y + 3 + (47 - x) // 6, GREY)
    # Конус у основания со стороны поворота.
    kx = 48 + d * 26
    c.poly([(kx - 3, 82), (kx + 3, 82), (kx + 9, 107), (kx - 9, 107)], RED)
    c.poly([(kx - 5, 90), (kx + 5, 90), (kx + 6, 96), (kx - 6, 96)], WHITE)
    c.rect(kx - 12, 107, kx + 12, 111, RED)
    # Щит: три доски, концы обломаны по-разному.
    ends = ((4, 89), (6, 91), (4, 87)) if right else ((6, 91), (4, 89), (8, 91))
    for i, (x0, x1) in enumerate(ends):
        y0 = 4 + i * 18
        c.rect(x0, y0, x1, y0 + 16, GOLD)
        c.rect(x0, y0, x1, y0, WHITE)
        c.rect(x0 + 2, y0 + 16, x1 - 2, y0 + 16, BRASS)
        if i < 2:
            c.rect(max(x0, ends[i + 1][0]) + 1, y0 + 17, min(x1, ends[i + 1][1]) - 1, y0 + 17, BRASS)
    # Шевроны.
    for k in range(3):
        cx = 48 + d * (k * 20 - 20)
        c.poly([(cx - d * 8, 12), (cx + d * 10, 30), (cx - d * 8, 48), (cx - d * 2, 30)], K)
    # Гвозди, дырки от пуль, ржавые подтёки, отпечаток ладони.
    for x, y in ((9, 8), (86, 8), (9, 52), (84, 52), (47, 8), (47, 52)):
        c.mark(x, y, WHITE)
        c.mark(x + 1, y + 1, DARK)
    for x, y in ((48 - d * 34, 44), (48 + d * 30, 9)):
        c.rect(x - 1, y - 1, x + 1, y + 1, BRASS)
        c.rect(x, y, x + 1, y + 1, K)
    for x, h in ((20, 4), (62, 6), (74, 3)):
        c.rect(x, 53 - h, x, 55, BRASS)
    hx = 48 - d * 36
    c.rect(hx - 2, 14, hx + 2, 19, RED)
    for f in (-2, 0, 2):
        c.rect(hx + f, 10, hx + f, 13, RED)
    c.rect(hx + d * 3, 15, hx + d * 4, 16, RED)
    c.rect(hx, 20, hx, 25, RED)
    return c.finish()


def chapel():
    """Часовня с колоколом у дороги, 192×160 (место хижины): каменный фасад с двускатной
    крышей и крестом, круглое окно светится, дверь забита досками, сбоку колокольня с колоколом
    в проёме и острым шпилем, на шесте флаг убежища, у стен надгробия и плющ."""
    c = Canvas(192, 160)
    # Шест с флагом убежища из-за стены.
    c.line(30, 100, 12, 46, METAL, 2)
    c.poly([(12, 46), (36, 48), (31, 54), (38, 60), (16, 62)], VIOLET)
    c.rect(22, 52, 27, 53, WHITE)
    c.rect(24, 50, 25, 56, WHITE)
    # Колокольня: стены, карниз, шпиль с крестом.
    c.rect(126, 54, 176, 155, GREY)
    c.rect(126, 54, 128, 155, WHITE)
    c.poly([(123, 52), (151, 8), (179, 52)], DARK)
    c.line(151, 9, 125, 51, METAL, 2)
    for k in (0.3, 0.55, 0.8):
        y = 8 + 44 * k
        c.line(151 - 26 * k, y, 151 + 26 * k, y, METAL, 1)
    c.rect(120, 52, 182, 57, WHITE)
    c.rect(120, 57, 182, 58, METAL)
    c.rect(150, 0, 152, 12, WHITE)
    c.rect(146, 3, 156, 5, WHITE)
    # Проём с колоколом.
    c.ellipse(151, 74, 12, 11, K)
    c.rect(139, 74, 163, 98, K)
    c.rect(150, 64, 152, 70, METAL)
    c.ellipse(151, 76, 6, 6, GOLD)
    c.poly([(145, 76), (157, 76), (160, 90), (142, 90)], GOLD)
    c.rect(141, 90, 161, 92, BRASS)
    c.rect(147, 78, 148, 88, WHITE)
    c.ellipse(151, 95, 2, 2, GREY)
    c.rect(135, 99, 167, 101, WHITE)
    # Бойница и кладка колокольни.
    c.rect(148, 114, 154, 132, K)
    c.ellipse(151, 114, 3.5, 4, K)
    for y in range(64, 152, 9):
        for x in range(130 + (y // 9 % 2) * 8, 174, 16):
            if not (136 <= x <= 166 and y < 104) and not (144 <= x <= 156 and 108 <= y <= 134):
                c.rect(x, y, x + 6, y, METAL)
    # Неф: фасад с щипцом, скаты крыши, крест.
    c.rect(22, 92, 128, 155, GREY)
    c.poly([(22, 93), (75, 46), (128, 93)], GREY)
    c.rect(22, 92, 24, 155, WHITE)
    for y in range(100, 152, 9):
        for x in range(28 + (y // 9 % 2) * 8, 124, 16):
            if not (56 <= x <= 92 and y > 104):
                c.rect(x, y, x + 6, y, METAL)
    c.line(14, 98, 75, 43, DARK, 8)
    c.line(75, 43, 134, 96, DARK, 8)
    c.line(14, 95, 75, 40, METAL, 2)
    c.rect(74, 22, 76, 40, WHITE)
    c.rect(69, 27, 81, 29, WHITE)
    # Круглое окно: свет и переплёт.
    c.ellipse(75, 78, 12, 12, DARK)
    c.ellipse(75, 78, 9, 9, GOLD)
    c.ellipse(75, 78, 4, 4, WHITE)
    c.rect(66, 78, 84, 78, DARK)
    c.rect(75, 69, 75, 87, DARK)
    c.line(69, 72, 81, 84, DARK, 1)
    c.line(81, 72, 69, 84, DARK, 1)
    # Стрельчатые окна по сторонам: одно светится, другое забито.
    for x, lit in ((38, True), (110, False)):
        c.poly([(x - 6, 112), (x, 102), (x + 6, 112), (x + 6, 136), (x - 6, 136)], DARK)
        c.poly([(x - 4, 113), (x, 106), (x + 4, 113), (x + 4, 134), (x - 4, 134)], GOLD if lit else K)
        if lit:
            c.rect(x, 108, x, 134, DARK)
            c.rect(x - 4, 122, x + 4, 122, DARK)
        else:
            c.line(x - 7, 116, x + 7, 120, METAL, 3)
            c.line(x - 7, 130, x + 7, 126, METAL, 3)
    # Дверь под аркой, забитая досками, ступени.
    c.ellipse(75, 118, 15, 14, DARK)
    c.rect(60, 118, 90, 155, DARK)
    c.ellipse(75, 119, 12, 11, METAL)
    c.rect(63, 119, 87, 155, METAL)
    for x in (69, 75, 81):
        c.rect(x, 110, x, 155, DARK)
    c.rect(84, 136, 85, 139, GOLD)
    c.line(57, 124, 93, 132, TAN, 4)
    c.line(57, 146, 93, 138, TAN, 4)
    for x, y in ((59, 124), (91, 131), (59, 145), (91, 138)):
        c.mark(x, y, K)
    c.rect(54, 153, 96, 156, WHITE)
    c.rect(50, 157, 100, 159, GREY)
    # Цоколь и земля.
    c.rect(18, 156, 49, 159, METAL)
    c.rect(101, 156, 180, 159, METAL)
    # Плющ на колокольне.
    for mx, my, r in ((170, 150, 6), (172, 138, 5), (168, 126, 4), (173, 116, 3), (160, 152, 5), (174, 104, 2)):
        c.ellipse(mx, my, r, r, PLUM)
        c.ellipse(mx - 1, my - 1, r * 0.6, r * 0.6, VIOLET)
    # Надгробия и крест у стен.
    c.ellipse(9, 142, 7, 6, GREY)
    c.rect(2, 142, 16, 159, GREY)
    c.rect(2, 142, 3, 158, WHITE)
    c.rect(6, 144, 12, 144, METAL)
    c.rect(6, 148, 11, 148, METAL)
    c.line(186, 159, 185, 134, WHITE, 3)
    c.line(180, 143, 191, 142, WHITE, 3)
    for x, h, lean_ in ((19, 10, 2), (104, 8, -2), (118, 12, 3), (181, 9, -2)):
        c.line(x, 159, x + lean_, 159 - h, BRASS, 1)
    return c.finish()


def road_colors():
    """Лента цветов дороги 8×1: индекс это место в `ROAD_COLORS`."""
    c = Canvas(8, 1)
    for i in range(8):
        c.set(i, 0, i)
    return c


def sprites():
    """Ленты гонки в палитре спрайтов, ключи как у пиратов."""
    out = {
        "cart_hero": carts_strip(RED, False),
        "palm": dead_tree(),
        "palm_b": celtic_cross(),
        "road_rock": headstone(),
        "road_barrel": trash_can(),
        "sign_left": sign(False),
        "sign_right": sign(True),
        "road_hut": chapel(),
    }
    for i, accent in enumerate((SEA, GOLD, RED, AQUA)):
        out["cart_%d" % i] = carts_strip(accent, True)
    return out


def horizon():
    """Горизонт в своей палитре `ZOMBIES_SKY`."""
    return {"road_sky": sky(), "road_islands": islands(), "road_sea": sea()}


def road_palette():
    return {"road_colors": road_colors()}


def preview(path, keys=None):
    """Лист набора как в игре; `keys`: только эти ленты."""
    items = zombies16.shaded(sprites())
    for key, canvas in horizon().items():
        items[key] = (canvas, ZOMBIES_SKY)
    for key, canvas in road_palette().items():
        items[key] = (canvas, ROAD_COLORS)
    if keys:
        items = {k: items[k] for k in keys}
    zombies16.save_sheet(path, items, scale=2, max_w=512)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        keys_ = None
        for arg in sys.argv[1:]:
            if arg.startswith("--keys="):
                keys_ = [k for k in arg.split("=", 1)[1].split(",") if k]
        preview(sys.argv[sys.argv.index("--preview") + 1], keys_)
