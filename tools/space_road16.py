#!/usr/bin/env python3
"""Набор «Космос» для гонки × 16/32-bit «псевдо-3D» (#136), зеркало `pixel_road16.py`: те же
ключи, размеры холстов и порядок кадров, чтобы `racing_bit16.gd` брала их без правок. Герой едет
на луноходе (вид сзади), соперники на ховерах пришельцев; у дороги светящийся гриб и кристалл
вместо пальм, купол станции вместо хижины, метеорит, топливный баллон, указатели. На горизонте
чёрно-синее небо со звёздами и планетой с кольцом, далёкие купола и гряды, лунная равнина с
кратерами вместо моря. Дорога из плит, обочина реголит.

Луноход, ховеры и пропы в палитре `space16.PALETTE`, горизонт в своей (`SPACE_SKY`), цвета
дороги лентой `road_colors` по местам `ROAD_COLORS`.

    python3 tools/space_road16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import space16  # noqa: E402
from space16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, GOLD, BRASS, METAL, DARK,  # noqa: E402
                     RED, VIOLET, PLUM)

# Палитра горизонта: небо, планета, равнина, гряды и купола. Места те же по смыслу, что у пиратов.
S0, S1, S2, S3, C0, C1, C2, M0, M1, M2, M3, I0, I1, I2, I3, SUN = range(16)
SPACE_SKY = [
    (0x07, 0x07, 0x18),  # S0  небо наверху
    (0x0D, 0x0C, 0x28),  # S1
    (0x17, 0x14, 0x3E),  # S2
    (0x2A, 0x22, 0x5C),  # S3  небо у горизонта, зарево
    (0x8A, 0x4A, 0x7C),  # C0  тень планеты
    (0xE0, 0x8A, 0x6A),  # C1  планета
    (0xFA, 0xF2, 0xE0),  # C2  свет планеты, яркие звёзды
    (0x3C, 0x3E, 0x62),  # M0  равнина вдали
    (0x5A, 0x5E, 0x84),  # M1  равнина
    (0x7E, 0x84, 0xA4),  # M2  равнина у дороги
    (0x2A, 0x2A, 0x4C),  # M3  тень кратера
    (0x33, 0x2E, 0x62),  # I0  гряда в дымке
    (0x24, 0x22, 0x48),  # I1  гряда
    (0xB8, 0xC0, 0xD4),  # I2  купол станции
    (0x4F, 0xC3, 0xD9),  # I3  окна и огни
    (0xA6, 0xAC, 0xBE),  # SUN реголит у кромки дороги
]

# Цвета дороги по местам ленты `road_colors` (демка берёт их по индексу).
ROAD_COLORS = [
    (0x6C, 0x74, 0x8C),  # 0 плита светлая
    (0x60, 0x68, 0x80),  # 1 плита тёмная
    (0xF0, 0x6A, 0x3A),  # 2 бордюр оранжевый
    (0xEE, 0xF1, 0xF6),  # 3 бордюр белый
    (0xC2, 0xEE, 0xF4),  # 4 разметка
    (0xA6, 0xAC, 0xBE),  # 5 реголит светлый
    (0x94, 0x9A, 0xAE),  # 6 реголит тёмный
    (0x3C, 0x3E, 0x62),  # 7 дымка вдали
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
    """Небо, 512×128, стыкуется по краям: чернота наверху, зарево у горизонта, звёзды, планета
    с кольцом и малая луна."""
    rng = random.Random(171)
    c = Canvas(512, 128)
    bands = [(0, S0), (40, S1), (78, S2), (106, S3)]
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
    # Звёзды: много тусклых, мало ярких крестиком.
    for _ in range(230):
        x = rng.randint(0, 511)
        y = rng.randint(0, 112)
        c.set(x, y, S3 if rng.random() < 0.55 else I2)
    for _ in range(26):
        x = rng.randint(2, 509)
        y = rng.randint(2, 96)
        c.set(x, y, C2)
        if rng.random() < 0.5:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.set(x + dx, y + dy, I2)
    # Планета с кольцом: кольцо позади, диск, тень справа снизу, полосы, кольцо спереди.
    px, py, pr = 150, 50, 26
    for a in range(0, 360, 1):
        ra = math.radians(a)
        x = px + math.cos(ra) * 46
        y = py + math.sin(ra) * 9 - math.cos(ra) * 6
        if math.sin(ra) < 0:
            c.set(x, y, C0)
            c.set(x, y + 1, C0)
    _wellipse(c, px, py, pr, pr, C1)
    for y in range(py - pr, py + pr + 1):
        for x in range(px - pr, px + pr + 1):
            d = math.hypot(x - px, y - py)
            if d > pr:
                continue
            if math.hypot(x - (px - 9), y - (py - 9)) > pr * 1.02:
                c.set(x, y, C0)
            elif (y - py) in (-12, -11, 3, 4, 14) and (x + y) % 5 != 0:
                c.set(x, y, C0)
            elif math.hypot(x - (px - 10), y - (py - 11)) < 8 and (x + y) % 2 == 0:
                c.set(x, y, C2)
    for a in range(0, 360, 1):
        ra = math.radians(a)
        x = px + math.cos(ra) * 46
        y = py + math.sin(ra) * 9 - math.cos(ra) * 6
        if math.sin(ra) >= 0:
            c.set(x, y, C2)
            c.set(x, y + 1, C1)
    # Малая луна серпом.
    _wellipse(c, 392, 34, 9, 9, I2)
    _wellipse(c, 396, 31, 9, 9, S0)
    return c


def islands():
    """Гряды и купола на горизонте, 512×40, прозрачный верх: дальние гряды в дымке, ближняя
    гряда зубцами, на ней купола станции с огнями и мачта."""
    c = Canvas(512, 40)
    for cx, w, h, near in ((60, 70, 13, False), (190, 46, 9, False), (300, 110, 22, True), (430, 64, 12, False)):
        for x in range(int(cx - w), int(cx + w) + 1):
            k = (x - cx) / w
            jag = (abs((x * 7) % 13 - 6) * 0.7 if near else abs((x * 5) % 9 - 4) * 0.4)
            top = 39 - int(h * max(0.0, 1.0 - k * k) ** 0.7 + jag)
            for y in range(top, 40):
                _wset(c, x, y, I0 if not near else (I0 if y < top + 2 else I1))
    # Купола: большой и два малых, окна огнями, мачта с маячком.
    for cx, r in ((300, 13), (268, 7), (338, 8), (62, 6), (432, 6)):
        base = 39 if cx in (62, 432) else 32
        for y in range(base - r, base + 1):
            half = int(math.sqrt(max(0.0, r * r - (base - y) ** 2)) * 1.25)
            for x in range(cx - half, cx + half + 1):
                _wset(c, x, y, I2)
        for x in range(cx - r + 2, cx + r - 1, 4):
            _wset(c, x, base - 2, I3)
            _wset(c, x + 1, base - 2, I3)
        _wset(c, cx - int(r * 0.5), base - int(r * 0.7), C2)
    for i in range(16):
        _wset(c, 320, 30 - i, I2)
    _wset(c, 320, 13, SUN)
    _wset(c, 321, 14, C1)
    _wset(c, 319, 14, C1)
    return c


def sea():
    """Лунная равнина от горизонта, 512×24: тёмная вдали, светлее у дороги, кратеры сплюснутыми
    овалами (тень сверху, светлая кромка снизу), у нижней кромки полоса реголита."""
    rng = random.Random(173)
    c = Canvas(512, 24)
    for y in range(24):
        col = M0 if y < 5 else (M1 if y < 15 else M2)
        c.rect(0, y, 511, y, col)
        if y in (5, 15):
            for x in range(0, 512, 2):
                c.set(x + (y % 2), y, M0 if y == 5 else M1)
    c.rect(0, 22, 511, 23, SUN)
    for _ in range(46):
        y = rng.randint(2, 20)
        x = rng.uniform(0, 512)
        w = rng.randint(2, 4) + y // 4
        for i in range(-w, w + 1):
            _wset(c, x + i, y, M3)
        for i in range(-w + 1, w):
            _wset(c, x + i, y + 1, SUN if y > 12 else M2)
    for _ in range(60):
        _wset(c, rng.uniform(0, 512), rng.randint(1, 21), M3 if rng.random() < 0.5 else SUN)
    return c


# --- Луноход, ховеры и пропы (палитра спрайтов) -------------------------------------------------

def _wheel(c, cx, cy, r, phase):
    """Колесо лунохода сзади: широкая шина с грунтозацепами, полоски бегут вниз (`phase` 0..1)."""
    w = 8
    c.rect(cx - w, cy - r + 3, cx + w, cy + r - 3, K)
    c.rect(cx - w + 2, cy - r, cx + w - 2, cy + r, K)
    c.rect(cx - w + 2, cy - r + 3, cx + w - 2, cy + r - 3, DARK)
    c.rect(cx - w + 2, cy - r + 3, cx - w + 3, cy + r - 3, METAL)
    step = 6
    off = int(phase * step)
    for y in range(int(cy - r + 4) + off, int(cy + r - 3), step):
        c.rect(cx - w + 3, y, cx + w - 3, y + 1, K)
        c.rect(cx - w + 3, y + 2, cx + w - 3, y + 2, METAL)


def rover(lean, phase, accent):
    """Луноход со спины, 160×104: два больших колеса, белый корпус с панелями, задний борт с
    фонарями, на деке плоская солнечная панель, низкая тарелка и короткий хлыст с флажком цвета
    `accent` (всё ниже шлема, без мачты); за рулём космонавт. `lean` −1..1 крен."""
    c = Canvas(160, 104)
    sh = lean * 6
    _wheel(c, 22 + sh * 0.3, 78, 24, phase)
    _wheel(c, 138 + sh * 0.3, 78, 24, phase)
    # Ось и рама.
    c.rect(24, 84, 136, 88, DARK)
    c.rect(34, 88, 126, 92, METAL)
    # Корпус: белая ванна, швы панелей, пояс металлом.
    c.poly([(30 + sh, 46), (130 + sh, 46), (128 + sh * 0.6, 90), (32 + sh * 0.6, 90)], WHITE)
    for y in (62, 78):
        c.line(31 + sh * 0.8, y, 129 + sh * 0.8, y, GREY, 1)
    for x in (58, 102):
        c.line(x + sh, 47, x + sh * 0.6, 89, GREY, 1)
    c.rect(28 + sh, 44, 132 + sh, 48, METAL)
    c.rect(30 + sh, 45, 130 + sh, 45, SKY)
    # Табличка с полосой цвета экипажа посередине борта.
    c.rect(66 + sh * 0.8, 66, 94 + sh * 0.8, 74, DARK)
    c.rect(68 + sh * 0.8, 68, 92 + sh * 0.8, 72, accent)
    # Задние фонари по углам.
    for x in (38, 122):
        c.rect(x + sh - 4, 54, x + sh + 4, 60, DARK)
        c.rect(x + sh - 3, 55, x + sh + 3, 59, RED if accent != RED else GOLD)
    # Сопла под бортом.
    for x in (50, 110):
        c.rect(x + sh * 0.6 - 5, 82, x + sh * 0.6 + 5, 88, DARK)
        c.rect(x + sh * 0.6 - 3, 84, x + sh * 0.6 + 3, 86, AQUA)
    # Крылья над колёсами: машина, а не платформа.
    for wx in (22, 138):
        c.rect(wx + sh * 0.5 - 11, 49, wx + sh * 0.5 + 11, 53, WHITE)
        c.rect(wx + sh * 0.5 - 11, 53, wx + sh * 0.5 + 11, 53, GREY)
    # Низкая тарелка антенны слева: ниже шлема.
    c.line(44 + sh, 44, 40 + sh * 1.2, 34, METAL, 2)
    c.ellipse(39 + sh * 1.2, 31, 9, 5, GREY)
    c.ellipse(39 + sh * 1.2, 31, 5, 2.5, METAL)
    # Топливный баллон на деке.
    c.ellipse(58 + sh, 40, 7, 7, RED)
    c.rect(52 + sh, 36, 64 + sh, 37, DARK)
    # Плоская солнечная панель на корпусе справа: лежит на деке, ячейки сеткой.
    c.poly([(96 + sh * 1.1, 34), (126 + sh * 1.1, 34), (130 + sh, 45), (94 + sh, 45)], METAL)
    c.poly([(98 + sh * 1.1, 36), (124 + sh * 1.1, 36), (127 + sh, 43), (97 + sh, 43)], NAVY)
    for x in (106, 115):
        c.line(x + sh * 1.1, 36, x + sh, 43, SEA, 1)
    c.line(98 + sh * 1.05, 39, 126 + sh * 1.05, 39, SEA, 1)
    c.line(100 + sh * 1.1, 37, 104 + sh * 1.1, 37, SKY, 1)
    # Короткий хлыст с флажком цвета экипажа у заднего угла: ниже головы водителя.
    flap = 2 * math.sin(phase * math.pi * 2)
    c.rect(134 + sh * 1.2, 30, 135 + sh * 1.2, 46, METAL)
    c.poly([(136 + sh * 1.2, 30), (146 + sh * 1.2, 33 + flap), (136 + sh * 1.2, 37)], accent)
    # Космонавт со спины: шлем, ранец с баллонами, руки на рычагах.
    x0 = 72 + sh * 1.2
    c.rect(x0 - 1, 22, x0 + 17, 42, WHITE)
    c.rect(x0 + 2, 24, x0 + 14, 40, METAL)
    c.rect(x0 + 3, 26, x0 + 6, 38, GREY)
    c.rect(x0 + 10, 26, x0 + 13, 38, GREY)
    c.rect(x0 + 7, 27, x0 + 9, 29, AQUA)
    for side in (-1, 1):
        sx = x0 + (0 if side < 0 else 16)
        c.ellipse(sx, 26, 4, 4, WHITE)
        c.line(sx, 26, sx + side * 6, 34, WHITE, 6)
        c.line(sx + side * 6, 34, sx + side * 3, 41, GREY, 5)
        c.ellipse(sx + side * 2.5, 42, 3, 2.5, METAL)
    c.ellipse(x0 + 8, 14, 9, 9, WHITE)
    c.rect(x0 + 2, 11, x0 + 14, 11, GREY)
    c.rect(x0 + 4, 22, x0 + 12, 22, METAL)
    c.finish()
    return c


def hover(lean, phase, accent):
    """Ховер пришельца со спины, 160×104: широкий фиолетовый корпус-блюдце без колёс, по бокам
    гондолы с соплами, снизу свечение подушки (мерцает по `phase`), сверху стеклянный колпак с
    головой пилота; полоса и низкий спойлер на корме цвета `accent`, без киля и мачт."""
    c = Canvas(160, 104)
    sh = lean * 6
    glow = 1 if phase < 0.25 else 0
    # Подушка: свечение под днищем и пылинки.
    c.ellipse(80 + sh * 0.3, 94, 52 + glow * 4, 5, SEA)
    c.ellipse(80 + sh * 0.3, 93, 38 + glow * 4, 3, AQUA)
    c.ellipse(80 + sh * 0.3, 92, 20 + glow * 6, 1.5, SKY)
    # Гондолы по бокам: на месте колёс лунохода, чтобы силуэт был той же ширины.
    for gx in (20, 140):
        x = gx + sh * 0.4
        c.ellipse(x, 68, 14, 20, PLUM)
        c.ellipse(x, 66, 11, 16, VIOLET)
        c.ellipse(x, 70, 8, 8, DARK)
        c.ellipse(x, 70, 5 + glow, 5 + glow, AQUA)
        c.ellipse(x, 70, 2, 2, SKY)
        c.rect(x - 9, 50, x + 9, 52, accent)
    # Корпус-блюдце: кромка, брюхо, верхняя палуба.
    c.ellipse(80 + sh * 0.6, 72, 62, 16, PLUM)
    c.ellipse(80 + sh * 0.8, 66, 60, 14, VIOLET)
    c.ellipse(80 + sh, 58, 44, 10, PLUM)
    c.ellipse(80 + sh, 55, 42, 8, VIOLET)
    # Полоса экипажа и огни по кромке.
    c.rect(34 + sh * 0.8, 70, 126 + sh * 0.8, 73, accent)
    for i, x in enumerate(range(30, 132, 14)):
        on = (i + (0 if phase < 0.25 else 1)) % 2 == 0
        c.rect(x + sh * 0.7, 78, x + sh * 0.7 + 3, 80, GOLD if on else DARK)
    # Колпак и пилот: большая голова, два усика.
    cx = 80 + sh * 1.2
    c.ellipse(cx, 38, 22, 20, SEA)
    c.ellipse(cx, 37, 19, 17, AQUA)
    c.ellipse(cx, 40, 11, 11, PLUM)
    c.ellipse(cx, 38, 10, 10, VIOLET)
    c.line(cx - 5, 30, cx - 9, 22, VIOLET, 2)
    c.line(cx + 5, 30, cx + 9, 22, VIOLET, 2)
    c.ellipse(cx - 9, 21, 2, 2, GOLD)
    c.ellipse(cx + 9, 21, 2, 2, GOLD)
    c.line(cx - 15, 28, cx - 9, 22, SKY, 1)
    c.rect(cx - 22, 52, cx + 22, 54, DARK)
    # Низкий спойлер на корме: крыло на двух стойках с шайбами по краям, ниже головы пилота.
    wx = 80 + sh * 1.1
    for side in (-1, 1):
        c.rect(wx + side * 30 - 2, 50, wx + side * 30 + 2, 60, PLUM)
    c.rect(wx - 46, 46, wx + 46, 51, DARK)
    c.rect(wx - 45, 47, wx + 45, 50, accent)
    c.rect(wx - 45, 47, wx + 45, 47, WHITE if accent != GOLD else SKY)
    for side in (-1, 1):
        c.rect(wx + side * 48 - 3, 42, wx + side * 48 + 3, 56, DARK)
        c.rect(wx + side * 48 - 2, 43, wx + side * 48 + 2, 55, accent)
    c.finish()
    return c


def carts_strip(accent, alien):
    """Три крена (влево, прямо, вправо) по два кадра: лента 6 кадров по 160, порядок как у пиратов."""
    frames = []
    for lean in (-1.0, 0.0, 1.0):
        for ph in (0.0, 0.5):
            frames.append(hover(lean, ph, accent) if alien else rover(lean, ph, accent))
    return strip(frames)


def mushroom():
    """Гигантский светящийся гриб у обочины, 120×240 (место пальмы): изогнутая ножка с кольцами,
    широкая шляпка с пятнами-огнями, под шляпкой пластинки, у ножки грибы поменьше."""
    rng = random.Random(181)
    c = Canvas(120, 240)
    bend = -16
    pts = []
    for i in range(176):
        k = i / 175
        pts.append((60 + bend * math.sin(k * math.pi), 239 - i))
    for i, (x, y) in enumerate(pts):
        w = 9 - i / 40
        c.rect(x - w, y, x + w, y, GREY if (i // 9) % 2 == 0 else WHITE)
        c.set(x + w, y, METAL)
        c.set(x + w - 1, y, METAL)
    top = pts[-1]
    # Шляпка на своём холсте: купол, срезанный снизу, с тёмной кромкой и пятнами-огнями.
    cap = Canvas(120, 240)
    cy = top[1] + 4
    cap.ellipse(60, cy, 56, 44, VIOLET)
    for y in range(int(cy) + 1, 240):
        for x in range(120):
            cap.px[y][x] = None
    cap.rect(5, int(cy) - 3, 115, int(cy), PLUM)
    for sx, sy, r in ((-32, -16, 8), (-6, -30, 10), (24, -20, 7), (40, -8, 5), (-46, -6, 4), (8, -10, 5)):
        cap.ellipse(60 + sx, cy + sy, r, r * 0.7, AQUA)
        cap.ellipse(60 + sx - 1, cy + sy - 1, r * 0.5, r * 0.35, SKY)
    # Юбочка и пластинки под шляпкой поверх ножки, потом сама шляпка.
    c.ellipse(60, cy + 5, 34, 6, PLUM)
    for dx in range(-30, 31, 5):
        c.line(60 + dx, cy + 1, 60 + dx * 1.08, cy + 9, VIOLET, 1)
    c.paste(cap, 0, 0)
    # Грибы поменьше у основания.
    for bx, h, r in ((26, 34, 13), (94, 24, 10)):
        c.rect(bx - 3, 239 - h, bx + 3, 239, GREY)
        c.ellipse(bx, 239 - h, r, r * 0.6, VIOLET)
        c.ellipse(bx - 2, 239 - h - 2, r * 0.4, r * 0.25, AQUA)
    for _ in range(18):
        c.set(rng.uniform(8, 112), rng.uniform(70, 230), SKY)
    c.finish()
    return c


def crystal():
    """Гроздь кристаллов у обочины, 120×240 (место второй пальмы): высокий шпиль и осколки
    поменьше, грани светлая и тёмная, у основания камни."""
    c = Canvas(120, 240)
    shards = ((60, 8, 22, 0), (34, 92, 15, -10), (88, 70, 16, 12), (18, 168, 10, -8), (104, 150, 11, 10), (70, 130, 12, 4))
    for cx, top, w, tilt in sorted(shards, key=lambda s: s[1]):
        tip = (cx + tilt, top)
        left = (cx - w, top + 34 + w)
        right = (cx + w, top + 30 + w)
        base_l = (cx - w * 0.8 - tilt * 0.3, 239)
        base_r = (cx + w * 0.8 - tilt * 0.3, 239)
        c.poly([tip, right, base_r, base_l, left], AQUA)
        # Правая грань темнее, блик вдоль левого ребра.
        c.poly([tip, right, base_r, (cx - tilt * 0.3, 239), (cx, top + 34 + w)], SEA)
        c.line(tip[0], tip[1] + 2, cx, top + 34 + w, SKY, 1)
        c.line(cx, top + 34 + w, cx - tilt * 0.3, 238, SKY, 1)
        c.line(left[0] + 3, left[1], base_l[0] + 3, 236, SKY, 2)
    c.poly([(0, 239), (10, 222), (30, 228), (42, 239)], GREY)
    c.poly([(74, 239), (88, 224), (112, 230), (119, 239)], METAL)
    c.finish()
    return c


def meteor():
    """Метеорит у дороги, 96×64: угловатая глыба, каверны, светящиеся трещины."""
    c = Canvas(96, 64)
    c.poly([(6, 63), (2, 42), (14, 20), (40, 6), (68, 10), (90, 30), (94, 63)], METAL)
    c.poly([(12, 40), (20, 22), (42, 10), (62, 14), (48, 28), (26, 42)], GREY)
    for cx, cy, r in ((34, 26, 5), (66, 34, 7), (24, 50, 4), (78, 52, 4)):
        c.ellipse(cx, cy, r, r * 0.7, DARK)
        c.ellipse(cx + 1, cy + 1, r * 0.6, r * 0.4, K)
    c.line(50, 30, 58, 46, AQUA, 2)
    c.line(58, 46, 52, 62, AQUA, 2)
    c.line(58, 46, 70, 54, SKY, 1)
    c.line(38, 40, 44, 58, AQUA, 1)
    c.poly([(0, 63), (12, 54), (24, 63)], GREY)
    c.poly([(72, 63), (84, 52), (96, 63)], GREY)
    return c.finish()


def canister():
    """Топливный баллон, 48×64: оранжевый цилиндр со скруглёнными торцами, обручи, вентиль,
    знак опасности."""
    c = Canvas(48, 64)
    c.rect(6, 12, 42, 58, RED)
    c.ellipse(24, 12, 18, 7, RED)
    c.ellipse(24, 58, 18, 5, RED)
    for y in (20, 48):
        c.rect(5, y, 43, y + 3, METAL)
    c.rect(19, 1, 29, 6, METAL)
    c.rect(15, 0, 33, 2, DARK)
    c.poly([(24, 27), (33, 43), (15, 43)], GOLD)
    c.rect(23, 32, 25, 38, K)
    c.rect(23, 40, 25, 41, K)
    c.rect(9, 14, 11, 56, GOLD)
    return c.finish()


def sign(right):
    """Указатель поворота, 96×112: светящийся щит на металлической стойке, чёрные шевроны в
    сторону поворота, огни по углам."""
    c = Canvas(96, 112)
    c.rect(44, 50, 51, 111, METAL)
    c.rect(40, 104, 55, 111, DARK)
    c.rect(4, 4, 91, 56, GOLD)
    c.rect(4, 4, 91, 7, SKY)
    c.rect(4, 53, 91, 56, BRASS)
    d = 1 if right else -1
    for k in range(3):
        cx = 48 + d * (k * 20 - 20)
        c.poly([(cx - d * 8, 14), (cx + d * 10, 30), (cx - d * 8, 46), (cx - d * 2, 30)], K)
    for x, y in ((8, 10), (87, 10), (8, 50), (87, 50)):
        c.rect(x - 1, y - 1, x + 1, y + 1, AQUA)
    return c.finish()


def dome():
    """Купол станции у дороги, 192×160 (место хижины): белая полусфера из панелей на кольце
    основания, шлюз с дверью, окна огнями, антенна и тарелка наверху."""
    c = Canvas(192, 160)
    # Основание и опоры.
    c.rect(10, 138, 182, 159, METAL)
    c.rect(10, 138, 182, 141, GREY)
    for x in range(18, 180, 16):
        c.rect(x, 146, x + 6, 159, DARK)
    # Купол.
    cx, base, r = 96, 138, 84
    for y in range(base - r, base + 1):
        half = int(math.sqrt(max(0.0, r * r - (base - y) ** 2)))
        c.rect(cx - half, y, cx + half, y, WHITE)
    # Швы панелей: параллели и меридианы.
    for k in (0.35, 0.62, 0.84):
        y = base - int(r * k)
        half = int(math.sqrt(max(0.0, r * r - (base - y) ** 2)))
        c.line(cx - half, y, cx + half, y, GREY, 1)
    for m in (-0.75, -0.4, 0.0, 0.4, 0.75):
        prev = None
        for y in range(base - r + 2, base + 1, 2):
            half = math.sqrt(max(0.0, r * r - (base - y) ** 2))
            p = (cx + half * m, y)
            if prev is not None:
                c.line(prev[0], prev[1], p[0], p[1], GREY, 1)
            prev = p
    # Окна огнями в два ряда.
    for x in (34, 58, 134, 158):
        c.rect(x - 7, 104, x + 7, 114, DARK)
        c.rect(x - 5, 106, x + 5, 112, AQUA)
        c.rect(x - 5, 106, x - 2, 107, SKY)
    for x in (62, 96, 130):
        c.ellipse(x, 78, 7, 7, DARK)
        c.ellipse(x, 78, 5, 5, AQUA)
    # Шлюз: выступ с дверью и оранжевой полосой.
    c.rect(74, 100, 118, 138, GREY)
    c.rect(74, 100, 118, 104, RED)
    c.rect(82, 110, 110, 138, DARK)
    c.rect(95, 110, 97, 138, METAL)
    c.rect(86, 118, 91, 122, AQUA)
    # Антенна и тарелка на макушке.
    c.rect(95, 28, 97, 56, METAL)
    c.ellipse(96, 26, 3, 3, RED)
    c.line(120, 62, 132, 40, METAL, 2)
    c.ellipse(134, 36, 13, 7, GREY)
    c.ellipse(134, 36, 7, 3, METAL)
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
        "palm": mushroom(),
        "palm_b": crystal(),
        "road_rock": meteor(),
        "road_barrel": canister(),
        "sign_left": sign(False),
        "sign_right": sign(True),
        "road_hut": dome(),
    }
    for i, accent in enumerate((SEA, GOLD, RED, AQUA)):
        out["cart_%d" % i] = carts_strip(accent, True)
    return out


def horizon():
    """Горизонт в своей палитре `SPACE_SKY`."""
    return {"road_sky": sky(), "road_islands": islands(), "road_sea": sea()}


def road_palette():
    return {"road_colors": road_colors()}


def preview(path):
    items = space16.shaded(sprites())
    for key, canvas in horizon().items():
        items[key] = (canvas, SPACE_SKY)
    for key, canvas in road_palette().items():
        items[key] = (canvas, ROAD_COLORS)
    space16.save_sheet(path, items, scale=2, max_w=512)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
