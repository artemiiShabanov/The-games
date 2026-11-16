#!/usr/bin/env python3
"""Набор «Офис» для платформера × 16/32-bit «тропа» (#138), зеркало `space_trail16.py` и
`pixel_trail16.py`: те же ключи, размеры холстов, число кадров и точки опоры. Вместо леса вечерний
опенспейс: фон без неба в три слоя (синяя даль с окнами на город и дальними перегородками,
колонны под подвесным потолком с воздуховодом сплошной полосой наверху, яркий ряд перегородок с
мониторами, фикусами, кактусами и вешалками у земли) и балка с гирляндой флажков над кадром
спереди; земля это архивные полки с корешками папок под кромкой ковролина; арка из картонных
коробок.

У фона и переднего плана свои палитры по 16 цветов (`OFFICE_BG`, `OFFICE_FG`); робот-пылесос
(слот краба) и бумажный самолётик (слот попугая) в палитре спрайтов `office16.PALETTE`, с красной
обводкой опасности. Ленты героя рисует `office16.py`.

    python3 tools/office_trail16.py --preview out.png

Лист высокий, поэтому пишется тремя файлами: `out.png` (спрайты и передний план), `out_b.png`
(даль и колонны), `out_c.png` (перегородки и балка над кадром).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import office16  # noqa: E402
from office16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, GOLD, BRASS, METAL, DARK, RED,  # noqa: E402
                      VIOLET, PLUM)

# Палитра фона: синяя даль, потолок и лампы, колонны, зелень в горшках, стикеры.
HZ0, HZ1, HZ2, HZ3, L0, L1, L2, L3, L4, T0, T1, T2, DK, FL1, FL2, MO = range(16)
OFFICE_BG = [
    (0x7C, 0x9C, 0xD2),  # HZ0  огни города, экраны, кромка дальних перегородок
    (0x4C, 0x6A, 0xAC),  # HZ1  стекло у горизонта, ткань перегородок
    (0x38, 0x52, 0x90),  # HZ2  стекло, дальние перегородки, крап ткани
    (0x26, 0x3A, 0x6E),  # HZ3  стена дали, глубокая холодная тень
    (0xFA, 0xF6, 0xDA),  # L0   свет ламп, бумага
    (0xD2, 0xD8, 0xE4),  # L1   плитка потолка, свет; алюминиевая планка
    (0xA0, 0xAA, 0xC0),  # L2   плитка потолка, жесть воздуховода
    (0x68, 0x72, 0x90),  # L3   тень потолка и металла
    (0x2A, 0x60, 0x5C),  # L4   тень зелени, ковролин внизу
    (0xE6, 0xDE, 0xCE),  # T0   колонна, свет; горшок, свет
    (0xB8, 0xAC, 0x9C),  # T1   колонна, штукатурка
    (0x80, 0x74, 0x70),  # T2   колонна, тень; ствол фикуса
    (0x14, 0x16, 0x26),  # DK   самая тёмная тень, корпуса мониторов
    (0xF6, 0xCD, 0x4C),  # FL1  жёлтые стикеры
    (0xE2, 0x4A, 0x44),  # FL2  красное: огнетушитель, стикеры, шарф
    (0x52, 0xA8, 0x86),  # MO   листья фикуса, кактус, табличка выхода
]

# Палитра переднего плана: ковролин, папки архива, бумага, картон, стикер.
FK, G0, G1, G2, G3, S0, S1, S2, S3, S4, ST0, ST1, W0, W1, W2, PINK = range(16)
OFFICE_FG = [
    (0x14, 0x14, 0x1C),  # FK   обводка
    (0xA6, 0xDE, 0xC4),  # G0   кромка ворса ковролина, экран
    (0x58, 0xA8, 0x90),  # G1   ковролин, зелень
    (0x38, 0x80, 0x74),  # G2
    (0x22, 0x52, 0x54),  # G3   тень ковролина
    (0xA8, 0xB2, 0xC8),  # S0   корешок папки, свет; пластик
    (0x7E, 0x8A, 0xA8),  # S1   корешок папки
    (0x5A, 0x64, 0x86),  # S2   корешок, тень
    (0x3E, 0x44, 0x62),  # S3   полка, тень
    (0x24, 0x26, 0x3C),  # S4   щели между папками
    (0xF4, 0xF5, 0xF8),  # ST0  бумага
    (0xB4, 0xBC, 0xD0),  # ST1  тень бумаги
    (0xE8, 0xC4, 0x8A),  # W0   картон, свет
    (0xC0, 0x90, 0x52),  # W1   картон, столешница
    (0x84, 0x5A, 0x32),  # W2   тень картона
    (0xF6, 0xCD, 0x4C),  # PINK жёлтый стикер, карандаш, цветок кактуса
]


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wrect(c, x0, y0, x1, y1, col):
    """Прямоугольник на ленте, которая стыкуется по краям."""
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            _wset(c, x, y, col)


def _wline(c, x0, y0, x1, y1, col):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        k = i / n
        _wset(c, x0 + (x1 - x0) * k, int(round(y0 + (y1 - y0) * k)), col)


def _wellipse(c, cx, cy, rx, ry, col, keep=None):
    """Эллипс на ленте, которая стыкуется по краям; `keep` красит только поверх этого цвета."""
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                if keep is None or c.get(int(x) % c.w, y) == keep:
                    _wset(c, x, y, col)


def _leaf(c, x, y, ang, length, wide, cols, wrap=True):
    """Лист фикуса от черенка (x, y) под углом `ang`: широкая середина, острый кончик, сверху свет,
    снизу тень, по оси жилка. `cols` это свет, тело, тень."""
    light, body, shade = cols
    put = _wset if wrap else (lambda cc, px, py, col: cc.set(px, py, col))
    ca, sa = math.cos(ang), math.sin(ang)
    n = int(length * 2)
    for j in range(n + 1):
        k = j / n
        half = wide * math.sin(math.pi * min(1.0, k * 1.08)) ** 0.8
        px, py = x + ca * length * k, y + sa * length * k
        m = int(half * 2)
        for d in range(-m, m + 1):
            u = d / 2.0
            # Свет на стороне, что смотрит вверх.
            up = (-sa * u * 0 + ca * u) < 0
            col = body
            if abs(u) > half - 0.9 and half > 1.0:
                col = light if up else shade
            put(c, px - sa * u, int(round(py + ca * u)), col)
    for j in range(2, n - 2):
        k = j / n
        if j % 3:
            put(c, x + ca * length * k, int(round(y + sa * length * k)), shade)


def _pot(c, cx, top, base, half, cols):
    """Горшок: трапеция шире кверху, ободок, свет слева."""
    light, body, shade = cols
    for y in range(int(top), int(base) + 1):
        k = (base - y) / max(base - top, 1.0)
        hw = half * (0.72 + 0.28 * k)
        for x in range(int(round(cx - hw)), int(round(cx + hw)) + 1):
            u = (x - cx) / max(hw, 0.5)
            _wset(c, x, y, light if u < -0.45 else (body if u < 0.4 else shade))
    _wrect(c, cx - half - 1, top - 1, cx + half + 1, top, body)
    _wrect(c, cx - half - 1, top - 1, cx - 1, top - 1, light)
    _wset(c, cx + half + 1, top, shade)


def _ficus(c, rng, cx, base, h):
    """Фикус в горшке высотой `h` от пола `base`: ствол и веер крупных листьев."""
    _pot(c, cx, base - 10, base, 6, (T0, T1, T2))
    top = base - h
    for y in range(int(top + h * 0.3), int(base - 10)):
        wob = math.sin(y * 0.15) * 1.2
        _wset(c, cx + wob, y, T2)
        _wset(c, cx + wob + 1, y, T1)
    n = 11
    for i in range(n):
        k = i / (n - 1)
        ang = math.radians(-170 + 160 * k + rng.uniform(-8, 8))
        ly = top + h * (0.34 + 0.2 * abs(k - 0.5) * 2) + rng.uniform(-3, 3)
        _leaf(c, cx + math.sin(ly * 0.15) * 1.2, ly, ang, rng.uniform(10, 15), 3.2, (MO, MO, L4))
    # Верхние листья поверх: светлая макушка.
    for ang in (-118, -92, -64):
        _leaf(c, cx, top + h * 0.34, math.radians(ang + rng.uniform(-5, 5)), rng.uniform(11, 15), 3.0, (MO, MO, L4))


def _cactus(c, cx, base, h):
    """Кактус-столбик в горшке: два отростка, рёбра и колючки."""
    _pot(c, cx, base - 7, base, 5, (T0, T1, T2))
    top = base - h

    def column(x, y0, y1, w):
        for y in range(int(y0), int(y1) + 1):
            r = w if y > y0 + 1 else w - 1
            for dx in range(-r, r + 1):
                _wset(c, x + dx, y, L4 if dx >= r - 1 else MO)
            if (y - int(y0)) % 3 == 1:
                _wset(c, x - 1, y, L0)
            if (y - int(y0)) % 4 == 2:
                _wset(c, x + r + 1, y, L0)
                _wset(c, x - r - 1, y, L0)

    column(cx, top, base - 8, 3)
    _wrect(c, cx - 8, base - 8 - h * 0.45, cx - 4, base - 7 - h * 0.45 + 1, MO)
    column(cx - 8, base - 8 - h * 0.45 - 7, base - 8 - h * 0.45, 2)
    _wrect(c, cx + 4, base - 8 - h * 0.6, cx + 8, base - 7 - h * 0.6 + 1, L4)
    column(cx + 8, base - 8 - h * 0.6 - 5, base - 8 - h * 0.6, 2)
    _wrect(c, cx - 1, top - 2, cx + 1, top - 1, FL2)
    _wset(c, cx, top - 3, FL1)


def _rack(c, cx, base, h):
    """Вешалка-стойка: ножки, рожки наверху, на рожках плащ и шляпа, красный шарф."""
    top = base - h
    _wrect(c, cx, top, cx + 1, base - 2, L3)
    _wrect(c, cx, top, cx, base - 2, L1)
    for d in range(1, 8):
        _wset(c, cx - d, base - 1 - (0 if d > 3 else 1), L3)
        _wset(c, cx + 1 + d, base - 1 - (0 if d > 3 else 1), L3)
    for sign in (-1, 1):
        for d in range(1, 6):
            _wset(c, cx + (0 if sign < 0 else 1) + sign * d, top + 4 - d // 2, L3)
        _wset(c, cx + (0 if sign < 0 else 1) + sign * 6, top + 1, L1)
    _wellipse(c, cx + 0.5, top - 1, 1.5, 1.5, L1)
    # Плащ на левом рожке: плечо и полы.
    for y in range(int(top + 5), int(top + 34)):
        k = (y - top - 5) / 29.0
        w = 4 + k * 5
        for x in range(int(cx - 4 - w), int(cx - 1) + 1):
            edge = x <= cx - 4 - w + 1
            _wset(c, x, y, HZ2 if edge else (HZ3 if (x + y // 3) % 5 else HZ2))
    for y in range(int(top + 8), int(top + 30), 6):
        _wset(c, cx - 3, y, FL1)
    # Шарф и шляпа на правом рожке.
    for y in range(int(top + 3), int(top + 22)):
        _wrect(c, cx + 5, y, cx + 7, y, FL2)
    _wrect(c, cx + 5, top + 22, cx + 7, top + 23, FL1)
    _wrect(c, cx + 3, top - 1, cx + 11, top, DK)
    _wrect(c, cx + 5, top - 4, cx + 9, top - 2, DK)
    _wrect(c, cx + 5, top - 2, cx + 9, top - 2, L3)


def _monitor(c, x0, top, lit, w=20, h=13):
    """Монитор на ножке, низ ножки на строке `top`: экран с графиком к нам или тёмный затылок."""
    _wrect(c, x0 + w // 2 - 2, top - 3, x0 + w // 2 + 1, top - 1, L3)
    _wrect(c, x0 + w // 2 - 5, top - 1, x0 + w // 2 + 4, top - 1, L3)
    _wrect(c, x0, top - 3 - h, x0 + w - 1, top - 4, DK)
    if lit:
        _wrect(c, x0 + 1, top - 2 - h, x0 + w - 2, top - 5, HZ0)
        _wrect(c, x0 + 2, top - 1 - h, x0 + w - 8, top - 1 - h, L0)
        for k, bar in enumerate((3, 5, 4, 7, 6)):
            _wrect(c, x0 + 3 + k * 3, top - 6 - bar, x0 + 4 + k * 3, top - 6, HZ2 if k % 2 else L1)
    else:
        _wrect(c, x0 + 1, top - 2 - h, x0 + w - 2, top - 5, L3)
        _wrect(c, x0 + 1, top - 2 - h, x0 + w - 2, top - 2 - h, L2)
        _wrect(c, x0 + w // 2 - 3, top - h + 2, x0 + w // 2 + 2, top - 8, DK)
        _wset(c, x0 + w - 4, top - 6, FL1)


def _sheet(c, x, y, w, h, pin=FL2):
    """Листок на кнопке: строчки текста."""
    _wrect(c, x, y, x + w - 1, y + h - 1, L0)
    _wrect(c, x + w - 1, y + 1, x + w - 1, y + h - 1, L1)
    for yy in range(y + 2, y + h - 1, 2):
        _wrect(c, x + 1, yy, x + w - 3 - (yy % 3), yy, L2)
    _wset(c, x + w // 2, y, pin)


def _sticker(c, x, y, col, n=4):
    _wrect(c, x, y, x + n - 1, y + n - 1, col)
    _wrect(c, x + 1, y + 1, x + n - 2, y + 1, DK if col != DK else L0)
    _wset(c, x + n - 1, y + n - 1, T2)


# --- Фон ---------------------------------------------------------------------------------------

def par3_back():
    """Даль на весь экран, 512×277: синяя стена опенспейса с высокими окнами, за стеклом вечерний
    город с огнями, на части окон жалюзи; под окнами дальний ряд перегородок; низ сплошной."""
    rng = random.Random(341)
    c = Canvas(512, 277)
    c.rect(0, 0, 511, 276, HZ3)
    # Силуэт города общий на все окна: дома разной высоты с антеннами.
    skyline = [0] * 512
    lights = {}
    x = 0
    while x < 512:
        w = rng.randint(11, 24)
        h = rng.randint(34, 118)
        for xx in range(x, min(x + w, 512)):
            skyline[xx] = h
        if rng.random() < 0.4 and x + w // 2 < 512:
            for k in range(1, 10):
                skyline[x + w // 2] = h + k
        for _ in range(int(w * h / 46)):
            lx = rng.randint(x + 1, x + w - 2)
            ly = rng.randint(4, h - 3)
            lights[(lx % 512, ly)] = True
        x += w + rng.choice((0, 0, 2, 5))
    top, bot = 28, 196
    for k in range(8):
        x0 = k * 64 + 9
        x1 = x0 + 45
        for y in range(top, bot + 1):
            t = (y - top) / float(bot - top)
            for xx in range(x0, x1 + 1):
                # Небо за стеклом: темнее наверху, светлее к горизонту, переход растром.
                if t > 0.62 or (t > 0.46 and (xx + y) % 2 == 0) or (t > 0.36 and xx % 2 == 0 and y % 4 == 0):
                    col = HZ1
                else:
                    col = HZ2
                up = bot - y
                if up < skyline[xx % 512]:
                    col = HZ3
                    if (xx % 512, up) in lights:
                        col = HZ0
                c.set(xx, y, col)
        # Блик на стекле наискось.
        for j in range(26):
            for dx in (0, 1, 5):
                xx, yy = x0 + 6 + j + dx, top + 44 - j * 2
                if x0 <= xx <= x1 and c.get(xx, yy) == HZ2 and (j + dx) % 2 == 0:
                    c.set(xx, yy, HZ1)
        # Переплёт: стойка посередине и перекладина, рама светлой кромкой сверху и слева.
        c.rect(x0 + 22, top, x0 + 23, bot, HZ3)
        c.rect(x0, top + 58, x1, top + 59, HZ3)
        c.rect(x0 - 1, top - 1, x1 + 1, top - 1, HZ2)
        c.rect(x0 - 1, top - 1, x0 - 1, bot, HZ2)
        # Жалюзи на части окон: ламели до разной высоты и шнур.
        if k in (1, 4, 6):
            drop = (96, 54, 132)[(1, 4, 6).index(k)]
            for y in range(top, top + drop, 3):
                c.rect(x0, y, x1, y, HZ1)
                c.rect(x0, y + 1, x1, y + 1, HZ2)
                c.rect(x0, y + 2, x1, y + 2, HZ3)
            c.rect(x0, top + drop, x1, top + drop + 1, HZ0)
            c.rect(x1 - 4, top + drop + 2, x1 - 4, top + drop + 16, HZ1)
        # Подоконник.
        c.rect(x0 - 3, bot + 1, x1 + 3, bot + 2, HZ1)
        c.rect(x0 - 3, bot + 3, x1 + 3, bot + 3, HZ2)
    # Дальние лампы под потолком.
    for x0 in range(20, 512, 64):
        c.rect(x0, 10, x0 + 30, 11, HZ1)
        c.rect(x0 + 2, 12, x0 + 28, 12, HZ0)
        c.rect(x0 + 6, 0, x0 + 6, 9, HZ2)
        c.rect(x0 + 24, 0, x0 + 24, 9, HZ2)
    # На простенках: часы, листки, огнетушитель.
    for k in range(8):
        px = k * 64 + 60
        kind = k % 4
        if kind == 0:
            _wellipse(c, px + 3, 92, 5, 5, HZ2)
            _wellipse(c, px + 3, 92, 3.4, 3.4, HZ1)
            _wset(c, px + 3, 90, HZ3)
            _wset(c, px + 3, 91, HZ3)
            _wset(c, px + 4, 92, HZ3)
        elif kind == 1:
            _wrect(c, px - 1, 80, px + 7, 94, HZ2)
            for yy in range(83, 93, 3):
                _wrect(c, px + 1, yy, px + 5, yy, HZ1)
            _wrect(c, px, 104, px + 6, 112, HZ1)
        elif kind == 2:
            _wrect(c, px + 1, 120, px + 5, 136, HZ2)
            _wrect(c, px + 2, 117, px + 3, 119, HZ1)
            _wrect(c, px + 2, 124, px + 4, 127, HZ1)
        else:
            _wrect(c, px - 1, 70, px + 7, 76, HZ1)
            _wrect(c, px + 1, 72, px + 3, 74, HZ0)
    # Дальний ряд перегородок с мониторами и зеленью: силуэты, светлая планка сверху.
    for k in range(16):
        x0 = k * 32
        ptop = (214, 210, 214, 218, 210, 212, 218, 214)[k % 8]
        _wrect(c, x0, ptop, x0 + 31, 238, HZ2)
        _wrect(c, x0, ptop, x0 + 31, ptop, HZ0)
        _wrect(c, x0, ptop + 1, x0 + 31, ptop + 1, HZ1)
        _wrect(c, x0 + 31, ptop + 2, x0 + 31, 238, HZ3)
        for yy in range(ptop + 5, 238, 4):
            for xx in range(x0 + 2 + (yy % 8) // 2, x0 + 30, 6):
                _wset(c, xx, yy, HZ3)
        what = (k * 5 + 2) % 7
        if what in (0, 3, 5):
            _wrect(c, x0 + 8, ptop - 11, x0 + 22, ptop - 2, HZ2)
            _wrect(c, x0 + 9, ptop - 10, x0 + 21, ptop - 3, HZ1 if what != 5 else HZ3)
            if what != 5:
                _wrect(c, x0 + 10, ptop - 9, x0 + 16, ptop - 9, HZ0)
            _wrect(c, x0 + 14, ptop - 1, x0 + 16, ptop - 1, HZ2)
        elif what == 1:
            # Силуэт фикуса над перегородкой.
            for ang in (-150, -120, -90, -60, -30):
                a = math.radians(ang)
                for j in range(11):
                    _wellipse(c, x0 + 16 + math.cos(a) * j, ptop - 2 + math.sin(a) * j, 1.4, 1.4, HZ2)
        elif what == 4:
            _wrect(c, x0 + 12, ptop - 6, x0 + 20, ptop - 1, HZ1)
            _wrect(c, x0 + 12, ptop - 6, x0 + 20, ptop - 6, HZ0)
        # Стикеры: огоньки на ткани.
        if k % 3 != 1:
            _wrect(c, x0 + 6 + (k * 7) % 14, ptop + 6, x0 + 8 + (k * 7) % 14, ptop + 8, HZ0)
    c.rect(0, 238, 511, 276, HZ3)
    return c


def par3_trees():
    """Колонны опенспейса, 512×277, прозрачно между ними: штукатуреные колонны с плинтусом,
    листками, часами и огнетушителем, наверху сплошной полосой подвесной потолок с лампами и
    воздуховод, с потолка свисают лампы на шнурах и кашпо с плющом."""
    rng = random.Random(342)
    c = Canvas(512, 277)
    cols = ((40, 30), (196, 22), (300, 38), (452, 26))
    for idx, (x, w) in enumerate(cols):
        for y in range(40, 263):
            for xx in range(x, x + w):
                k = (xx - x) / float(w)
                col = T0 if k < 0.2 else (T1 if k < 0.72 else T2)
                c.set(xx, y, col)
        # Фаска и швы штукатурки, редкие сколы.
        c.rect(x + 1, 66, x + 1, 247, T1)
        for yy in range(96, 246, 50):
            c.rect(x, yy, x + w - 1, yy, T2)
            c.rect(x, yy + 1, x + int(w * 0.7), yy + 1, T0)
        for _ in range(w // 3):
            sx = rng.randint(x + 3, x + w - 4)
            sy = rng.randint(70, 240)
            c.set(sx, sy, T2)
            c.set(sx + 1, sy + 1, T2)
        # Капитель под воздуховодом и плинтус ступенями у пола.
        c.rect(x - 3, 60, x + w + 2, 65, T1)
        c.rect(x - 3, 60, x + w + 2, 60, T0)
        c.rect(x + int(w * 0.7), 61, x + w + 2, 65, T2)
        c.rect(x - 3, 66, x + w + 2, 66, T2)
        c.rect(x - 3, 248, x + w + 2, 253, T1)
        c.rect(x - 3, 248, x + w + 2, 248, T0)
        c.rect(x - 6, 254, x + w + 5, 262, T1)
        c.rect(x - 6, 254, x + w + 5, 254, T0)
        c.rect(x + int(w * 0.7), 249, x + w + 2, 253, T2)
        c.rect(x + int(w * 0.7), 255, x + w + 5, 262, T2)
        c.rect(x - 6, 262, x + w + 5, 262, DK)
    # Колонна 0: доска объявлений и огнетушитель.
    c.rect(44, 106, 65, 140, L3)
    c.rect(45, 107, 64, 139, T2)
    _sheet(c, 47, 109, 8, 11)
    _sheet(c, 56, 112, 7, 9, FL1)
    _sticker(c, 47, 123, FL1, 5)
    _sticker(c, 54, 126, FL2, 5)
    _sheet(c, 57, 124, 6, 12, MO)
    c.rect(51, 186, 59, 212, FL2)
    c.rect(51, 186, 52, 212, L0)
    c.rect(58, 187, 59, 212, T2)
    c.rect(53, 181, 57, 185, DK)
    c.rect(50, 180, 55, 181, L3)
    c.line(57, 183, 62, 190, DK, 1)
    c.rect(53, 194, 57, 201, L0)
    c.rect(54, 196, 56, 196, FL2)
    c.rect(50, 213, 60, 214, L3)
    # Колонна 1: часы, кабель-канал и розетка.
    c.ellipse(207, 100, 8.5, 8.5, L3)
    c.ellipse(207, 100, 7, 7, L0)
    for a in range(0, 360, 30):
        c.set(207 + math.cos(math.radians(a)) * 6, 100 + math.sin(math.radians(a)) * 6, L3)
    c.line(207, 100, 207, 95, DK, 1)
    c.line(207, 100, 211, 102, DK, 1)
    c.set(207, 100, FL2)
    c.rect(213, 66, 214, 222, L2)
    c.rect(214, 66, 214, 222, L3)
    c.rect(209, 222, 216, 231, L1)
    c.rect(209, 231, 216, 231, L3)
    c.set(211, 226, DK)
    c.set(214, 226, DK)
    _sticker(c, 199, 150, FL1, 5)
    _sticker(c, 203, 157, FL1, 5)
    _sticker(c, 199, 164, FL2, 5)
    # Колонна 2: плакат с графиком, план эвакуации, термостат.
    c.rect(306, 96, 331, 134, L0)
    c.rect(331, 97, 331, 134, L1)
    c.rect(306, 134, 331, 134, L2)
    for k, bar in enumerate((6, 10, 9, 15, 21)):
        c.rect(309 + k * 4, 129 - bar, 311 + k * 4, 129, HZ1 if k < 4 else MO)
    c.line(309, 121, 328, 101, FL2, 1)
    c.poly([(328, 99), (329, 104), (324, 101)], FL2)
    c.rect(308, 131, 329, 131, L3)
    c.set(318, 96, FL2)
    c.rect(308, 160, 327, 176, L3)
    c.rect(309, 161, 326, 175, L0)
    c.rect(311, 163, 318, 168, MO)
    c.rect(320, 163, 324, 165, MO)
    c.rect(311, 170, 324, 173, L2)
    c.line(313, 172, 322, 164, FL2, 1)
    c.rect(322, 196, 329, 205, L1)
    c.rect(323, 197, 328, 200, HZ0)
    c.rect(322, 205, 329, 205, L3)
    c.set(325, 203, FL2)
    # Колонна 3: табличка выхода, стикеры и листок.
    c.rect(455, 84, 474, 94, MO)
    c.rect(455, 84, 474, 84, L0)
    c.rect(455, 94, 474, 94, L4)
    c.rect(458, 88, 464, 90, L0)
    c.poly([(465, 86), (470, 89), (465, 92)], L0)
    _sheet(c, 457, 130, 10, 14)
    _sticker(c, 469, 133, FL1, 5)
    _sticker(c, 462, 148, FL2, 5)
    _sticker(c, 468, 152, FL1, 5)
    c.rect(458, 196, 472, 197, L3)
    for hx in (460, 465, 470):
        c.rect(hx, 198, hx, 200, L3)
        c.set(hx + 1, 200, L3)
    # Подвесной потолок: плитки сеткой, свет слева сверху, встроенные лампы, тёмный торец.
    c.rect(0, 0, 511, 39, L2)
    for yy in range(0, 40, 13):
        c.rect(0, yy, 511, yy, L3)
        c.rect(0, yy + 1, 511, yy + 1, L1)
    for xx in range(0, 512, 32):
        c.rect(xx, 0, xx, 39, L3)
        c.rect(xx + 1, 0, xx + 1, 38, L1)
    for _ in range(150):
        c.set(rng.randrange(512), rng.randrange(39), L3 if rng.random() < 0.7 else L1)
    for k, x0 in enumerate(range(32, 512, 96)):
        yy = 13 if k % 2 == 0 else 26
        c.rect(x0 + 2, yy + 2, x0 + 31, yy + 12, L0)
        c.rect(x0 + 2, yy + 2, x0 + 31, yy + 2, L1)
        for xx in range(x0 + 7, x0 + 30, 6):
            c.rect(xx, yy + 3, xx, yy + 12, L1)
    # Решётка вентиляции и пятно протечки.
    for x0 in (130, 386):
        c.rect(x0, 2, x0 + 28, 11, L3)
        for yy in range(3, 11, 2):
            c.rect(x0 + 1, yy, x0 + 27, yy, DK)
    for x0, y0 in ((230, 30), (470, 6)):
        _wellipse(c, x0, y0, 7, 3.5, T1, L2)
        _wellipse(c, x0 + 1, y0, 4, 2, L2, T1)
    c.rect(0, 39, 511, 42, L3)
    c.rect(0, 39, 511, 39, L1)
    c.rect(0, 43, 511, 44, DK)
    # Воздуховод под потолком: жестяная труба с фланцами на подвесах.
    for y, col in ((45, L3), (46, L1), (47, L1), (48, L0), (49, L1), (50, L2), (51, L2), (52, L2), (53, L2),
                   (54, L3), (55, L3), (56, L3), (57, HZ3), (58, DK)):
        c.rect(0, y, 511, y, col)
    for x0 in range(14, 512, 48):
        c.rect(x0, 44, x0 + 3, 59, L3)
        c.rect(x0, 44, x0, 58, L1)
        c.rect(x0 + 3, 45, x0 + 3, 59, HZ3)
        c.rect(x0, 59, x0 + 3, 59, DK)
        for yy in (47, 51, 55):
            c.set(x0 + 1, yy, DK)
    for x0 in range(38, 512, 96):
        for xx in range(x0, x0 + 20):
            if (xx - x0) % 3 != 2:
                c.rect(xx, 50, xx, 53, DK)
        c.rect(x0 - 1, 49, x0 + 20, 49, L3)
    # Лампы на шнурах: колпак конусом, под ним пятно света.
    for x in (98, 150, 246, 362, 412, 498):
        length = rng.randint(34, 84)
        y1 = 59 + length
        c.rect(x, 59, x, y1, DK)
        for j in range(6):
            _wrect(c, x - 1 - j, y1 + j, x + 1 + j, y1 + j, L3 if j else DK)
            _wset(c, x - 1 - j, y1 + j, L2)
        _wrect(c, x - 6, y1 + 6, x + 6, y1 + 6, L0)
        _wrect(c, x - 2, y1 + 7, x + 2, y1 + 8, L0)
        for j in range(1, 9):
            for dx in range(-6 - j // 2, 7 + j // 2):
                if (dx + j) % 3 == 0 and j % 2 == 1 and c.get((x + dx) % 512, y1 + 8 + j) is None:
                    _wset(c, x + dx, y1 + 8 + j, L0)
    # Кашпо с плющом на трёх тросиках.
    for x in (20, 124, 274, 388):
        length = rng.randint(22, 40)
        y1 = 59 + length
        _wline(c, x - 4, y1, x, 59, L3)
        _wline(c, x + 4, y1, x, 59, L3)
        _pot(c, x, y1, y1 + 7, 5, (T0, T1, T2))
        for dx in (-5, -2, 1, 4):
            n = rng.randint(12, 34)
            ph = rng.uniform(0, 6)
            for j in range(n):
                vx = x + dx + math.sin(j * 0.3 + ph) * 2.2
                _wset(c, vx, y1 - 1 + j, L4 if j % 4 else MO)
                if j % 4 == 1:
                    side = 1 if (j // 4) % 2 else -1
                    _wrect(c, vx + side, y1 - 1 + j, vx + side * 2, y1 + j, MO)
                    _wset(c, vx + side * 2, y1 + j + 1, L4)
        _wellipse(c, x, y1 - 2, 6, 2.5, MO)
        _wellipse(c, x + 2, y1 - 1, 3, 1.4, L4)
    return c


def par3_bushes():
    """Ближний ряд у земли, 512×120, прозрачный верх: синие перегородки с алюминиевой планкой,
    мониторы, листки и стикеры, перед ними фикусы и кактусы в горшках, вешалки, стопки бумаги;
    низ сплошной, ковролин."""
    rng = random.Random(343)
    c = Canvas(512, 120)
    tops = (62, 68, 62, 72, 66, 62, 70, 66)
    for k in range(8):
        x0 = k * 64
        top = tops[k]
        _wrect(c, x0, top, x0 + 63, 96, HZ1)
        # Крап ткани и тень у правого края секции.
        for yy in range(top + 4, 96, 2):
            for xx in range(x0 + (yy // 2) % 5, x0 + 64, 5):
                _wset(c, xx, yy, HZ2)
        _wrect(c, x0 + 61, top + 3, x0 + 63, 96, HZ2)
        _wrect(c, x0, top, x0 + 63, top + 1, L1)
        _wrect(c, x0, top + 2, x0 + 63, top + 2, L3)
        # Стойка между секциями выше планки.
        _wrect(c, x0 - 1, top - 3, x0 + 2, 96, L2)
        _wrect(c, x0 - 1, top - 3, x0 - 1, 96, L1)
        _wrect(c, x0 + 2, top - 2, x0 + 2, 96, L3)
        _wrect(c, x0 - 1, top - 4, x0 + 2, top - 4, L1)
    # Мониторы, лампы, кружки и папки на планках.
    _monitor(c, 10, 62, True)
    _monitor(c, 88, 68, False)
    _monitor(c, 150, 62, True, 24, 15)
    _monitor(c, 276, 66, True)
    _monitor(c, 340, 62, False, 22, 14)
    _monitor(c, 400, 70, True)
    _monitor(c, 470, 66, True, 22, 14)
    for x, top in ((40, 62), (300, 66), (430, 70)):
        # Кружка с паром.
        _wrect(c, x, top - 6, x + 4, top - 1, L0)
        _wrect(c, x + 4, top - 6, x + 4, top - 1, L1)
        _wrect(c, x + 5, top - 5, x + 6, top - 3, L1)
        _wset(c, x + 1, top - 8, L1)
        _wset(c, x + 2, top - 10, L1)
        _wset(c, x + 3, top - 12, L2)
    for x, top in ((120, 68), (220, 72), (372, 62)):
        # Настольная лампа: колено и жёлтый колпак.
        _wrect(c, x, top - 2, x + 7, top - 1, DK)
        _wline(c, x + 3, top - 2, x + 7, top - 10, L3)
        _wline(c, x + 7, top - 10, x + 2, top - 15, L3)
        for j in range(4):
            _wrect(c, x - 3 - j // 2, top - 17 + j, x + 3 + j // 2, top - 17 + j, FL1)
        _wrect(c, x - 3, top - 13, x + 3, top - 13, L0)
    for x, top in ((196, 72), (236, 72), (500, 66)):
        # Стопка папок: корешки разного цвета.
        for j, col in enumerate((T1, L2, FL2, T0)):
            _wrect(c, x + (j % 2), top - 3 - j * 3, x + 13 + (j % 2), top - 1 - j * 3, col)
            _wrect(c, x + (j % 2), top - 1 - j * 3, x + 13 + (j % 2), top - 1 - j * 3, T2 if col != FL2 else DK)
            _wrect(c, x + 3 + (j % 2), top - 2 - j * 3, x + 6 + (j % 2), top - 2 - j * 3, L0)
    # Листки и стикеры на ткани.
    for x, y, w, h, pin in ((8, 70, 10, 13, FL2), (44, 68, 8, 10, FL1), (74, 76, 12, 14, FL2), (140, 70, 9, 12, MO),
                            (208, 78, 10, 12, FL2), (262, 72, 8, 10, FL1), (292, 74, 11, 14, FL2),
                            (332, 68, 9, 11, FL1), (396, 78, 10, 12, FL2), (458, 72, 9, 13, MO),
                            (488, 74, 8, 10, FL2)):
        _sheet(c, x, y, w, h, pin)
    for x, y, col in ((22, 72, FL1), (28, 78, FL1), (58, 72, FL2), (104, 74, FL1), (110, 80, L0), (160, 68, FL1),
                      (166, 74, FL2), (172, 69, FL1), (244, 78, FL1), (310, 70, FL1), (348, 70, FL2),
                      (354, 76, FL1), (416, 80, FL1), (422, 76, MO), (444, 74, FL1), (474, 72, FL1),
                      (504, 76, FL1), (124, 84, MO), (268, 86, FL2)):
        _sticker(c, x, y, col, 5)
    # Ковролин: сплошной низ, светлая кромка, крап ворса.
    c.rect(0, 92, 511, 119, L4)
    c.rect(0, 92, 511, 92, MO)
    for x in range(512):
        if (x * 7) % 5 < 2:
            c.set(x, 93, MO)
    for _ in range(300):
        x = rng.randrange(512)
        y = rng.randint(95, 119)
        c.set(x, y, DK if rng.random() < 0.55 else MO)
    # Стопки бумаги и коробки у плинтуса.
    for x in (30, 136, 248, 326, 440):
        n = rng.randint(3, 6)
        for j in range(n):
            _wrect(c, x + (j % 2), 96 - j * 2, x + 15 + (j % 2), 97 - j * 2, L0)
            _wrect(c, x + (j % 2), 97 - j * 2, x + 15 + (j % 2), 97 - j * 2, L2)
        _wrect(c, x, 98, x + 16, 98, DK)
    for x in (92, 380):
        _wrect(c, x, 82, x + 19, 98, T1)
        _wrect(c, x, 82, x + 19, 83, T0)
        _wrect(c, x + 16, 84, x + 19, 98, T2)
        _wrect(c, x + 8, 82, x + 10, 98, L1)
        _wrect(c, x + 3, 88, x + 6, 91, L0)
        _wrect(c, x, 99, x + 19, 99, DK)
    # Зелень и вешалки перед перегородками.
    for x, h in ((62, 62), (232, 54), (360, 66), (486, 58)):
        _ficus(c, rng, x, 100, h)
    for x, h in ((126, 30), (192, 24), (300, 34), (426, 26)):
        _cactus(c, x, 100, h)
    _rack(c, 170, 101, 76)
    _rack(c, 412, 101, 70)
    # Листки в воздухе: сквозняк от кондиционера.
    for _ in range(9):
        x = rng.uniform(0, 512)
        y = int(rng.uniform(8, 44))
        if c.get(int(x) % 512, y) is None and c.get(int(x + 3) % 512, y + 2) is None:
            _wrect(c, x, y, x + 3, y, L0)
            _wrect(c, x + 1, y + 1, x + 4, y + 1, L0)
            _wrect(c, x + 2, y + 2, x + 4, y + 2, L1)
    return c


def canopy_front():
    """Балка над кадром спереди, 256×56, прозрачный низ: тёмная балка с коробами ламп, провисшие
    провода и гирлянда флажков «пятницы», лампа на шнуре и табличка выхода на цепочках."""
    c = Canvas(256, 56)
    # Балка с заклёпками.
    c.rect(0, 0, 255, 7, HZ3)
    c.rect(0, 0, 255, 1, L3)
    c.rect(0, 7, 255, 8, DK)
    for x in range(6, 256, 16):
        c.set(x, 4, L3)
        c.set(x, 5, DK)
    # Короба ламп с решёткой.
    for x0 in (24, 152):
        c.rect(x0, 9, x0 + 47, 15, L3)
        c.rect(x0, 9, x0 + 47, 9, HZ3)
        c.rect(x0 + 44, 10, x0 + 47, 15, HZ3)
        for xx in range(x0 + 3, x0 + 44, 4):
            c.rect(xx, 11, xx, 14, HZ3)
        c.rect(x0 + 1, 16, x0 + 46, 16, L1)
        c.rect(x0, 17, x0 + 47, 17, DK)

    def sag(x0, y0, x1, y1, drop, col, flags=None):
        n = int(x1 - x0) * 2
        for i in range(n + 1):
            t = i / float(n)
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t + drop * 4 * t * (1 - t)
            _wset(c, x, int(round(y)), col)
        if flags:
            k = 0
            for xx in range(int(x0) + 5, int(x1) - 6, 10):
                t = (xx + 3 - x0) / float(x1 - x0)
                y = int(round(y0 + (y1 - y0) * t + drop * 4 * t * (1 - t)))
                fc = flags[k % len(flags)]
                for j in range(8):
                    half = (7 - j) // 2
                    for dx in range(-half, half + 1):
                        _wset(c, xx + 3 + dx, y + 1 + j, fc if dx < half or half == 0 else (DK if fc in (HZ3, L3) else T2))
                _wset(c, xx + 2, y + 2, L1 if fc in (HZ3, L3) else L0)
                k += 1

    # Провода в глубине и гирлянда поверх.
    sag(0, 8, 92, 8, 12, DK)
    sag(92, 8, 256, 8, 20, DK)
    sag(60, 8, 200, 8, 30, HZ3)
    sag(200, 8, 316, 8, 16, HZ3)
    sag(0, 9, 128, 9, 22, L3, (L3, FL1, HZ3, FL2, L3, HZ3, FL1, L3, MO, HZ3, FL2, L3))
    sag(128, 9, 256, 9, 28, L3, (HZ3, L3, FL1, HZ3, L3, FL2, HZ3, FL1, L3, HZ3, MO, L3))
    # Лампа на шнуре: тёмный колпак со светлой кромкой.
    c.rect(110, 9, 110, 34, DK)
    for j in range(6):
        c.rect(109 - j, 35 + j, 111 + j, 35 + j, HZ3 if j else DK)
        c.set(109 - j, 35 + j, L3)
    c.rect(104, 41, 116, 41, L1)
    c.rect(108, 42, 112, 43, L0)
    # Табличка выхода на двух цепочках.
    for x in (214, 236):
        for y in range(9, 34):
            c.set(x, y, DK if y % 2 else L3)
    c.rect(208, 34, 242, 46, L4)
    c.rect(208, 34, 242, 34, MO)
    c.rect(208, 46, 242, 46, DK)
    c.rect(208, 34, 208, 46, MO)
    c.rect(213, 39, 224, 41, L0)
    c.poly([(225, 36), (232, 40), (225, 44)], L0)
    c.rect(235, 37, 238, 43, MO)
    return c


# --- Передний план -----------------------------------------------------------------------------

def trail_soil():
    """Архив, 64×64 по кругу в обе стороны: четыре полки с корешками папок разной ширины и
    высоты, на корешках ярлыки и кольца, между папками тёмные щели, кое-где картонная коробка и
    папка, завалившаяся набок."""
    rng = random.Random(351)
    n = 64
    c = Canvas(n, n)
    c.rect(0, 0, n - 1, n - 1, S4)
    for row in range(4):
        y0 = row * 16
        # Доска полки: свет сверху, тень снизу.
        c.rect(0, y0 + 14, n - 1, y0 + 14, S2)
        c.rect(0, y0 + 15, n - 1, y0 + 15, S3)
        x = rng.randint(0, 3)
        start = x
        while x < start + n:
            left = start + n - x
            w = rng.choice((4, 5, 5, 6, 7))
            box = rng.random() < 0.14 and left >= 12
            if box:
                w = rng.randint(10, 12)
            if left - w < 4:
                w = left
            if w > 8 and not box:
                w = left // 2
            h = rng.randint(10, 13)
            top = y0 + 14 - h
            if box:
                # Коробка: картон, лента и ярлык.
                for xx in range(x, x + w - 1):
                    for yy in range(top + 2, y0 + 14):
                        c.set(xx % n, yy, W1)
                    c.set(xx % n, top + 2, W0)
                    c.set(xx % n, y0 + 13, W2)
                for yy in range(top + 2, y0 + 14):
                    c.set((x + w - 2) % n, yy, W2)
                    c.set((x + w // 2 - 1) % n, yy, W0)
                for xx in range(x + 2, x + 5):
                    c.set(xx % n, top + 6, ST1)
                    c.set(xx % n, top + 7, ST1)
            else:
                tone = rng.choice(((S0, S1, S2), (S1, S2, S3), (S0, S1, S2), (S1, S2, S3), (ST1, S0, S1)))
                for xx in range(x, x + w - 1):
                    k = xx - x
                    col = tone[0] if k == 0 else (tone[2] if k == w - 2 and w > 3 else tone[1])
                    for yy in range(top, y0 + 14):
                        c.set(xx % n, yy, col)
                    c.set(xx % n, top, tone[0])
                if w >= 4:
                    # Ярлык, кольцо для пальца и полоска внизу корешка.
                    for xx in range(x + 1, x + w - 2):
                        c.set(xx % n, top + 2, ST0)
                        c.set(xx % n, top + 3, ST0)
                        c.set(xx % n, top + 4, ST1)
                        c.set(xx % n, y0 + 12, tone[2])
                    mid = (x + (w - 1) // 2) % n
                    c.set(mid, top + 7, S4)
                    c.set(mid, top + 8, tone[0])
                    if rng.random() < 0.22:
                        c.set(mid, top + 3, PINK)
                        c.set((mid - 1) % n, top + 3, PINK)
            x += w
    # Пыль и царапины.
    for _ in range(18):
        x, y = rng.randrange(n), rng.randrange(n)
        if c.get(x, y) in (S1, S2):
            c.set(x, y, S3 if c.get(x, y) == S2 else S2)
    return c


def trail_edge():
    """Кромка ковролина, 32×18 по кругу: поверхность на строке 4, над ней торчит ворс и уголки
    стикеров, край свисает бахромой кистей на полки; ниже прозрачно, там архив."""
    rng = random.Random(352)
    c = Canvas(32, 18)
    top = 4
    for x in range(32):
        # Кисти бахромы по четыре пикселя: длинная пара, короткая пара.
        tassel = (x // 2) % 2
        hang = top + 4 + (3 if tassel else 1) + (1 if (x // 4) % 3 == 0 and tassel else 0)
        c.rect(x, top, x, hang, G1)
        c.rect(x, top, x, top, G0)
        if x % 3 == 0:
            c.set(x, top + 1, G0)
        # Петли ворса: крап в теле ковра.
        if (x * 5 + 1) % 4 == 0:
            c.set(x, top + 2, G2)
        if (x * 3) % 5 == 0:
            c.set(x, top + 3, G2)
        c.rect(x, top + 4, x, top + 4, G2)
        if x % 2 == 1:
            c.rect(x, top + 5, x, hang, G2)
        c.set(x, hang, G2 if x % 2 == 0 else G3)
        c.set(x, hang + 1, G3)
        if rng.random() < 0.4:
            h = rng.randint(1, 2)
            c.rect(x, top - h, x, top - 1, G1 if rng.random() < 0.5 else G0)
    # Уголки стикеров и скрепка в ворсе.
    c.rect(6, top - 2, 8, top - 1, PINK)
    c.set(8, top - 2, None)
    c.rect(22, top - 3, 24, top - 1, PINK)
    c.set(22, top - 3, None)
    c.set(15, top - 1, ST0)
    c.set(16, top - 2, ST0)
    c.set(17, top - 1, ST1)
    return c


def arch_bark():
    """Стенка арки из картонных коробок, 32×32 по кругу: коробки вперевязку, клапаны, скотч,
    ярлыки и стрелки «верх», гофра по краям."""
    rng = random.Random(353)
    c = Canvas(32, 32)
    for row in range(2):
        y0 = row * 16
        for k in range(2):
            x0 = k * 16 + row * 8
            for y in range(y0, y0 + 16):
                for x in range(x0, x0 + 16):
                    dx, dy = x - x0, y - y0
                    if dx == 15 or dy == 15:
                        col = FK
                    elif dy == 0 or dx == 0:
                        col = W0
                    elif dx == 14 or dy == 14:
                        col = W2
                    elif dy == 4:
                        col = W2
                    elif dy == 5:
                        col = W0
                    else:
                        col = W1
                    c.set(x % 32, y, col)
            # Скотч по клапанам и вниз по стенке.
            for y in range(y0 + 1, y0 + 9):
                c.set((x0 + 7) % 32, y, ST0)
                c.set((x0 + 8) % 32, y, ST1)
            kind = (row * 2 + k) % 4
            if kind == 0:
                # Ярлык со строчками.
                for y in range(y0 + 8, y0 + 13):
                    for x in range(x0 + 2, x0 + 7):
                        c.set(x % 32, y, ST0 if (y - y0) % 2 == 0 or x == x0 + 2 else ST1)
            elif kind == 1:
                # Стрелки «верх».
                for ax in (x0 + 10, x0 + 13):
                    for y in range(y0 + 8, y0 + 13):
                        c.set(ax % 32, y, W2)
                    c.set((ax - 1) % 32, y0 + 9, W2)
                    c.set((ax + 1) % 32, y0 + 9, W2) if ax + 1 < x0 + 14 else None
            elif kind == 2:
                # Жёлтый стикер.
                for y in range(y0 + 8, y0 + 12):
                    for x in range(x0 + 10, x0 + 14):
                        c.set(x % 32, y, PINK)
                c.set((x0 + 13) % 32, y0 + 11, W2)
            else:
                # Ручка-прорезь.
                for x in range(x0 + 3, x0 + 7):
                    c.set(x % 32, y0 + 9, FK)
                    c.set(x % 32, y0 + 10, W2)
    # Гофра: редкие штрихи и потёртости.
    for _ in range(26):
        x, y = rng.randrange(32), rng.randrange(32)
        if c.get(x, y) == W1:
            c.set(x, y, W2 if rng.random() < 0.6 else W0)
    return c


def _blade(c, x, h, bend, col, side, tip=None):
    for j in range(int(h)):
        k = j / h
        c.set(x + bend * k * k, c.h - 1 - j, col)
        if k < 0.55:
            c.set(x + bend * k * k + 1, c.h - 1 - j, side)
    if tip is not None:
        c.set(x + bend, c.h - int(h), tip)


def dec_grass(i):
    """Провода из-под фальшпола перед героем, 32×24, два кадра качания: серые и зелёные жилы
    пучками, на концах вилки и жёлтые штекеры."""
    rng = random.Random(361)
    c = Canvas(32, 24)
    for _ in range(13):
        x = rng.uniform(3, 29)
        h = rng.uniform(9, 20)
        bend = rng.uniform(-3, 3) + (1.5 if i else -0.5)
        col = rng.choice((S1, G1, S0, G2, S2))
        side = {S1: S3, G1: G3, S0: S2, G2: G3, S2: S4}[col]
        _blade(c, x, h, bend, col, side)
        # Штекер на конце: колодка и два штырька или жёлтый наконечник.
        tx = int(round(x + bend))
        ty = c.h - int(h)
        kind = rng.random()
        if kind < 0.4:
            c.rect(tx - 1, ty - 2, tx + 1, ty, ST0)
            c.set(tx + 1, ty, ST1)
            c.set(tx - 1, ty - 3, S3)
            c.set(tx + 1, ty - 3, S3)
        elif kind < 0.7:
            c.rect(tx, ty - 1, tx, ty, PINK)
            c.set(tx, ty - 2, S0)
    return c


def dec_tuft(i):
    """Бумажная лапша из шредера, 32×14, два кадра: белые полоски пучком."""
    rng = random.Random(362)
    c = Canvas(32, 14)
    for _ in range(12):
        col = rng.choice((ST0, ST0, ST1, PINK))
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 11), rng.uniform(-3, 3) + (1 if i else 0), col,
               S1 if col != PINK else W2)
    return c


def dec_fern():
    """Фикус в горшке за героем, 48×32: веер широких листьев из одной точки над картонного цвета
    кашпо."""
    rng = random.Random(363)
    c = Canvas(48, 32)
    # Листья: дальние темнее, потом ближние.
    for ang, length, cols in ((-168, 14, (G1, G2, G3)), (-12, 14, (G1, G2, G3)), (-140, 18, (G0, G1, G3)),
                              (-40, 18, (G0, G1, G3)), (-112, 20, (G0, G1, G2)), (-68, 20, (G0, G1, G2)),
                              (-90, 19, (G0, G1, G2))):
        _leaf(c, 24, 23, math.radians(ang + rng.uniform(-3, 3)), length, 3.6, cols, wrap=False)
    # Кашпо: трапеция с ободком и полоской.
    for y in range(23, 32):
        hw = 7.0 - (y - 23) * 0.3
        for x in range(int(round(24 - hw)), int(round(24 + hw)) + 1):
            u = (x - 24) / hw
            c.set(x, y, W0 if u < -0.4 else (W1 if u < 0.45 else W2))
    c.rect(16, 22, 32, 23, W1)
    c.rect(16, 22, 24, 22, W0)
    c.rect(18, 27, 30, 27, ST0)
    c.rect(27, 27, 30, 27, ST1)
    c.outline(FK)
    return c


def dec_bush():
    """Рабочее место за героем, 64×36: стол с тумбой, монитор с графиком, клавиатура, кружка,
    лампа, стопка бумаги, под столом системный блок; у пола тень на ковролине."""
    c = Canvas(64, 36)
    # Тень на ковролине.
    c.rect(3, 33, 60, 35, G3)
    for x in range(3, 61):
        if (x * 7) % 5 < 2:
            c.set(x, 33, G2)
    # Боковина слева, тумба с ящиками справа, столешница.
    c.rect(5, 23, 8, 33, W1)
    c.rect(8, 23, 8, 33, W2)
    c.rect(41, 23, 58, 33, W1)
    c.rect(56, 23, 58, 33, W2)
    c.rect(41, 28, 58, 28, W2)
    c.rect(41, 23, 58, 23, W2)
    c.rect(47, 25, 51, 25, ST0)
    c.rect(47, 30, 51, 30, ST0)
    c.rect(3, 20, 60, 22, W1)
    c.rect(3, 20, 60, 20, W0)
    c.rect(3, 22, 60, 22, W2)
    # Системный блок под столом и провод.
    c.rect(14, 24, 22, 33, S2)
    c.rect(14, 24, 15, 33, S1)
    c.rect(21, 24, 22, 33, S3)
    c.rect(16, 26, 20, 26, S4)
    c.rect(16, 28, 20, 28, S4)
    c.set(19, 31, G0)
    c.set(17, 31, PINK)
    c.line(23, 30, 30, 33, S4, 1)
    c.line(30, 33, 36, 30, S4, 1)
    # Монитор: рамка, экран с графиком, ножка.
    c.rect(13, 2, 35, 16, S3)
    c.rect(13, 2, 35, 2, S1)
    c.rect(15, 4, 33, 14, G0)
    for k, bar in enumerate((3, 5, 4, 7, 8)):
        c.rect(17 + k * 3, 13 - bar, 18 + k * 3, 13, G2 if k % 2 else G1)
    c.rect(16, 5, 24, 5, ST0)
    c.set(33, 15, PINK)
    c.rect(22, 17, 26, 18, S2)
    c.rect(19, 19, 29, 19, S1)
    # Клавиатура, кружка, стопка бумаги.
    c.rect(31, 18, 40, 19, S0)
    c.rect(31, 19, 40, 19, S2)
    c.rect(5, 15, 11, 19, ST0)
    c.rect(5, 16, 11, 16, ST1)
    c.rect(5, 18, 11, 18, ST1)
    c.rect(6, 13, 12, 14, ST0)
    c.rect(8, 12, 10, 12, PINK)
    c.rect(43, 15, 46, 19, ST0)
    c.rect(46, 15, 46, 19, ST1)
    c.rect(47, 16, 48, 18, ST1)
    c.set(47, 17, None)
    c.rect(43, 15, 45, 15, W2)
    # Лампа: основание, два колена, жёлтый колпак.
    c.rect(52, 18, 58, 19, S2)
    c.line(55, 18, 59, 11, S1, 1)
    c.line(59, 11, 54, 6, S1, 1)
    c.poly([(48, 7), (55, 3), (57, 6), (50, 10)], PINK)
    c.line(50, 10, 56, 6, W2, 1)
    c.outline(FK)
    return c


def dec_rock():
    """Стопка папок, 32×20: три папки вразнобой с торчащими листами, сверху и рядом комки мятой
    бумаги."""
    c = Canvas(32, 20)
    # Нижняя серая папка.
    c.rect(2, 14, 27, 19, S1)
    c.rect(2, 14, 27, 14, S0)
    c.rect(2, 19, 27, 19, S2)
    c.rect(24, 15, 27, 18, ST0)
    c.rect(24, 16, 27, 16, ST1)
    c.rect(24, 18, 27, 18, ST1)
    c.rect(5, 16, 10, 17, ST0)
    # Средняя картонная, сдвинута вправо, из неё торчат листы.
    c.rect(5, 9, 29, 13, W1)
    c.rect(5, 9, 29, 9, W0)
    c.rect(5, 13, 29, 13, W2)
    c.rect(3, 10, 5, 12, ST0)
    c.rect(3, 11, 5, 11, ST1)
    c.rect(18, 10, 24, 11, PINK)
    c.rect(18, 11, 24, 11, W2)
    # Верхняя тёмная, лежит косо.
    c.poly([(3, 8), (4, 4), (24, 5), (25, 8)], S2)
    c.line(4, 4, 24, 5, S0, 1)
    c.rect(8, 6, 13, 7, ST0)
    c.set(21, 7, S4)
    # Комки бумаги: на стопке и у подножия.
    for cx, cy, r in ((19, 3, 2.6), (29.5, 17.5, 1.8)):
        c.ellipse(cx, cy, r, r, ST0)
        c.set(cx + 1, cy + 1, ST1)
        c.set(cx - 1, cy, ST1)
        c.set(cx + 1, cy - 1, ST1)
    c.outline(FK)
    return c


def dec_flowers():
    """Кактусы в горшочках, 32×20: шар с цветком, столбик с отростком и малыш; колючки светлыми
    точками."""
    c = Canvas(32, 20)

    def pot(cx, half):
        for y in range(15, 20):
            hw = half - (y - 15) * 0.3
            for x in range(int(round(cx - hw)), int(round(cx + hw)) + 1):
                c.set(x, y, W0 if x < cx - hw * 0.4 else (W1 if x < cx + hw * 0.4 else W2))
        c.rect(cx - half - 1, 14, cx + half + 1, 14, W1)
        c.rect(cx - half - 1, 14, cx - 1, 14, W0)

    # Шар.
    pot(6, 3)
    c.ellipse(6, 9.5, 4.2, 4.2, G1)
    for y in range(5, 14):
        for x in range(1, 12):
            if c.get(x, y) == G1:
                if x <= 3:
                    c.set(x, y, G0)
                elif x >= 9:
                    c.set(x, y, G2)
                elif x in (5, 7) and y % 2 == 0:
                    c.set(x, y, G2)
    c.set(4, 7, ST0)
    c.set(8, 9, ST0)
    c.set(5, 11, ST0)
    c.rect(5, 3, 7, 4, PINK)
    c.set(6, 2, PINK)
    # Столбик с отростком.
    pot(17, 3)
    c.rect(15, 2, 19, 13, G1)
    c.rect(16, 1, 18, 1, G1)
    c.rect(15, 2, 15, 13, G0)
    c.rect(19, 2, 19, 13, G2)
    c.rect(20, 8, 22, 9, G2)
    c.rect(22, 5, 23, 9, G1)
    c.rect(23, 5, 23, 9, G2)
    c.rect(12, 9, 14, 10, G1)
    c.rect(12, 6, 13, 10, G1)
    c.rect(12, 6, 12, 9, G0)
    for x, y in ((17, 3), (17, 6), (17, 9), (17, 12), (22, 6), (13, 7)):
        c.set(x, y, ST0)
    c.set(17, 0, PINK)
    # Малыш с двумя ушами.
    pot(27, 2)
    c.ellipse(27, 11, 2.4, 2.6, G1)
    c.ellipse(25, 8, 1.4, 1.6, G1)
    c.ellipse(29, 7.5, 1.4, 1.6, G2)
    c.set(26, 10, G0)
    c.set(25, 7, G0)
    c.set(28, 12, G2)
    c.set(27, 11, ST0)
    c.set(29, 6, PINK)
    c.outline(FK)
    return c


def dec_mush():
    """Мелочь со стола, 32×16: стакан с карандашами и ручкой, ластик, скрепка и кнопка."""
    c = Canvas(32, 16)
    # Карандаши и ручка торчат из стакана.
    c.line(13, 8, 9, 2, PINK, 2)
    c.set(8, 1, W0)
    c.set(8, 0, S4)
    c.rect(15, 1, 16, 8, S3)
    c.rect(15, 0, 16, 1, ST0)
    c.line(19, 8, 22, 2, PINK, 2)
    c.rect(22, 0, 23, 1, W2)
    c.line(17, 8, 18, 3, G1, 1)
    c.set(18, 2, G0)
    # Стакан: сетка, ободок.
    c.rect(11, 8, 21, 15, S1)
    c.rect(11, 8, 12, 15, S0)
    c.rect(20, 8, 21, 15, S2)
    c.rect(11, 8, 21, 8, S0)
    for y in range(10, 15, 2):
        for x in range(13, 20, 2):
            c.set(x + (y // 2) % 2, y, S3)
    # Ластик, скрепка, кнопка.
    c.rect(24, 13, 29, 15, ST0)
    c.rect(24, 13, 26, 15, G1)
    c.rect(24, 15, 29, 15, ST1)
    c.rect(2, 14, 7, 14, S0)
    c.rect(2, 15, 7, 15, S2)
    c.set(2, 13, S0)
    c.set(7, 13, S0)
    c.rect(3, 12, 6, 12, S0)
    c.set(27, 10, PINK)
    c.set(28, 10, PINK)
    c.set(27, 11, S3)
    c.outline(FK)
    return c


# --- Враги (палитра спрайтов) ------------------------------------------------------------------

def _danger(c):
    """Враг: тень как у всех, но обводка красная, а не чёрная: опасен, убить нельзя."""
    c.shade()
    c.outline(RED)
    return c


def crab(i):
    """Робот-пылесос в слоте краба, четыре кадра: плоская шайба с башенкой датчика и антенной с
    огоньком, боковые щётки крутятся, корпус подрагивает, датчик бегает по башенке. Корпус серый
    со светлой крышкой, чтобы красная обводка читалась."""
    c = Canvas()
    up = i % 2
    # Щётки по бокам крутятся, колёса под днищем.
    for sign in (-1, 1):
        ang = i * 0.8 + (0.0 if sign > 0 else 1.6)
        for k in range(3):
            a = ang + k * 2.094
            c.line(16 + sign * 10, 27.5, 16 + sign * 10 + math.cos(a) * 4, 27.8 + math.sin(a) * 1.2, GOLD, 1)
        c.rect(16 + sign * 6 - 1, 27, 16 + sign * 6 + 1, 28, DARK)
    # Шайба: тёмный борт и светлая крышка с кольцом.
    c.ellipse(16, 24 - up, 11.5, 4, DARK)
    c.rect(5, 20 - up, 27, 24 - up, DARK)
    c.ellipse(16, 20 - up, 11.5, 4, GREY)
    c.ellipse(16, 20 - up, 8, 2.4, METAL)
    c.ellipse(15, 19.5 - up, 4.5, 1.2, GREY)
    # Башенка датчика и антенна.
    c.rect(13, 13 - up, 19, 18 - up, METAL)
    c.ellipse(16, 13 - up, 3.5, 1.5, GREY)
    c.line(19, 13 - up, 22, 7 - up, DARK, 1)
    c.ellipse(22.5, 6 - up, 1.2, 1.2, GOLD)
    _danger(c)
    # Поверх обводки: окно датчика, огни-глаза на борту, бампер, кнопка.
    c.rect(14, 16 - up, 18, 16 - up, NAVY)
    c.set(14 + i, 16 - up, AQUA)
    c.set(15 + (i % 3), 16 - up, SKY)
    for x in (10, 11, 21, 22):
        c.set(x, 25 - up, RED)
        c.set(x, 24 - up, GOLD if x in (10, 22) else RED)
    c.rect(14, 26 - up, 18, 26 - up, METAL)
    c.set(9, 20 - up, AQUA)
    c.set(23, 19 - up, WHITE)
    return c


def drone(i):
    """Бумажный самолётик в слоте попугая летит вправо, четыре кадра: крылья машут (вверх,
    середина, вниз, середина), нос клюёт. Лист в линейку с красным полем; тело по центру кадра,
    чтобы при развороте не прыгало."""
    c = Canvas()
    f = (-4, 0, 4, 0)[i]
    dip = (0, 1, 0, -1)[i]
    nose = (29, 17 + dip)
    root = (8, 17)
    # Киль снизу, дальнее крыло, ближнее крыло.
    c.poly([nose, root, (12, 25 - abs(f) * 0.3)], METAL)
    c.poly([nose, (10, 16), (5, 8 + f)], GREY)
    c.poly([nose, root, (2, 13 + f * 1.6), (5, 18 + f)], WHITE)
    _danger(c)
    # Линовка тетрадного листа вдоль ближнего крыла, красное поле у хвоста, сгиб.
    tail = (3.5, 15.5 + f * 1.3)
    for k in (0.3, 0.45, 0.6, 0.75):
        x = int(round(nose[0] + (tail[0] - nose[0]) * k))
        y = int(round(nose[1] + (tail[1] - nose[1]) * k))
        if c.get(x, y) in (WHITE, GREY):
            c.set(x, y, AQUA)
    for k in (0.84, 0.9):
        x = int(round(nose[0] + (tail[0] - nose[0]) * k))
        y = int(round(nose[1] + (tail[1] - nose[1]) * k))
        if c.get(x, y) in (WHITE, GREY):
            c.set(x, y, RED)
    for x in range(10, 27, 2):
        y = int(round(root[1] + (nose[1] - root[1]) * (x - root[0]) / float(nose[0] - root[0])))
        if c.get(x, y) in (WHITE, GREY, METAL):
            c.set(x, y, DARK)
    return c


def sprites():
    """Ленты этой демки в палитре спрайтов (ленты героя в `office16.sprites`)."""
    return {
        "crab_walk": strip([crab(i) for i in range(4)]),
        "parrot_fly": strip([drone(i) for i in range(4)]),
    }


def backdrop():
    """Слои фона и балка над кадром в палитре фона `OFFICE_BG`."""
    return {"par3_back": par3_back(), "par3_trees": par3_trees(), "par3_bushes": par3_bushes(),
            "canopy_front": canopy_front()}


def foreground():
    """Земля, арка, украшения в палитре переднего плана `OFFICE_FG`."""
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
    """Лист набора тремя файлами (целиком он выше полутора тысяч пикселей): спрайты и передний
    план, даль и колонны (`_b`), перегородки и балка (`_c`)."""
    items = office16.shaded(sprites())
    for key, canvas in foreground().items():
        items[key] = (canvas, OFFICE_FG)
    office16.save_sheet(path, items, scale=2)
    back = backdrop()
    stem, ext = os.path.splitext(path)
    office16.save_sheet(stem + "_b" + ext, {k: (back[k], OFFICE_BG) for k in ("par3_back", "par3_trees")}, scale=2)
    office16.save_sheet(stem + "_c" + ext, {k: (back[k], OFFICE_BG) for k in ("par3_bushes", "canopy_front")},
                        scale=2)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
