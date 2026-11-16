#!/usr/bin/env python3
"""Набор «Супергерои» для платформера × 16/32-bit «тропа» (#137), зеркало `space_trail16.py` и
`pixel_trail16.py`: те же ключи, размеры холстов, число кадров и точки опоры. Вместо джунглей и
грибов крыши мегаполиса на закате: фон без неба в три слоя (коралловое зарево, в дымке стена
небоскрёбов с огнями окон, дирижабль и высотка с двумя лучами прожектора; большие опоры на
прежних местах стволов: кирпичная труба с обручами, решётчатая мачта, бетонная колонна с афишей
и клёпаная стальная стойка, наверху сплошной полосой комиксные рекламные щиты на ферме, с фермы
свисают лампы на проводах; у земли водяные баки, антенны, тарелки, будки и вытяжки за
парапетом) и стальная балка с гирляндой флажков над кадром спереди; земля из кирпичной кладки
под бетонной плитой крыши со стальным уголком; арка из клёпаных бирюзовых балок с раскосами.

Свойства слотов, на которые рассчитана демка: ленты фона 512 пикселей стыкуются по краям, у
дали и клади крыш низ сплошной, у больших опор стойки на тех же местах, что стволы, и прозрачно
между ними, у балки спереди прозрачный низ; кладка 64×64 стыкуется в обе стороны, кромка 32×18
с поверхностью на строке 4, грань арки 32×32 по кругу; украшения стоят на нижней строке холста.

У фона и переднего плана свои палитры по 16 цветов (`SUPERHEROES_BG`, `SUPERHEROES_FG`);
робот-паук и дрон-шпион в палитре спрайтов `superheroes16.PALETTE`, их рисует основа, здесь они
получают красную обводку опасности. Ленты героя рисует `superheroes16.py`. Случайность с
постоянным зерном: картинка одна и та же.

    python3 tools/superheroes_trail16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import superheroes16  # noqa: E402
from superheroes16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, GOLD, BRASS, METAL, DARK, RED,  # noqa: E402,F401
                           VIOLET, PLUM)

TAU = math.pi * 2.0

# Палитра фона: закатная дымка дали, щиты и баки в закатном свете, бетон и сталь опор, неон.
HZ0, HZ1, HZ2, HZ3, L0, L1, L2, L3, L4, T0, T1, T2, DK, FL1, FL2, MO = range(16)
SUPERHEROES_BG = [
    (0xF0, 0x9C, 0x8A),  # HZ0  зарево у горизонта, горящие окна вдали
    (0xB4, 0x6E, 0x98),  # HZ1  сиреневая дымка
    (0x76, 0x50, 0x96),  # HZ2  дальние дома в дымке
    (0x44, 0x34, 0x7A),  # HZ3  ближние дома дали, сумерки
    (0xFF, 0xE4, 0xB0),  # L0   блик: бумага афиш, лампы
    (0xF2, 0x90, 0x76),  # L1   грань в закатном свете
    (0xB6, 0x5C, 0x7A),  # L2   щит, бак, будка
    (0x72, 0x40, 0x76),  # L3   тень
    (0x3E, 0x2A, 0x5E),  # L4   глубокая тень, леса за щитами
    (0xDC, 0xB2, 0x9C),  # T0   бетон и сталь, свет
    (0x98, 0x74, 0x86),  # T1   бетон, сталь, кирпич трубы
    (0x5C, 0x44, 0x68),  # T2   тень опор, швы
    (0x18, 0x12, 0x2C),  # DK   самая тёмная тень
    (0xFF, 0xDC, 0x5A),  # FL1  жёлтый свет: окна, лампы, звезда
    (0x58, 0xE2, 0xDA),  # FL2  бирюзовый неон
    (0xF4, 0x54, 0x96),  # MO   малиновый неон, маячки
]

# Палитра переднего плана: бетон плиты, кирпич, сталь, бирюзовые балки, свет ламп.
FK, G0, G1, G2, G3, S0, S1, S2, S3, S4, ST0, ST1, W0, W1, W2, PINK = range(16)
SUPERHEROES_FG = [
    (0x15, 0x11, 0x1F),  # FK   обводка
    (0xF6, 0xE8, 0xD2),  # G0   кромка плиты, свет
    (0xC6, 0xBA, 0xB6),  # G1   бетон
    (0x90, 0x88, 0x9A),  # G2   бетон, тень
    (0x5A, 0x54, 0x70),  # G3   глубокая тень бетона
    (0xC2, 0x86, 0x72),  # S0   кирпич, свет
    (0x9A, 0x62, 0x5E),  # S1   кирпич
    (0x74, 0x48, 0x52),  # S2   тёмный кирпич
    (0x50, 0x32, 0x46),  # S3   тень кирпича
    (0x2C, 0x1C, 0x30),  # S4   швы кладки
    (0xCC, 0xD4, 0xE0),  # ST0  сталь, свет
    (0x7C, 0x86, 0xA2),  # ST1  сталь, тень
    (0x8E, 0xE6, 0xD6),  # W0   крашеная балка, свет
    (0x38, 0xA8, 0xA4),  # W1   крашеная балка
    (0x1E, 0x62, 0x74),  # W2   тень балки
    (0xFF, 0xD8, 0x4A),  # PINK свет ламп, искры
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


def _wline(c, x0, y0, x1, y1, col):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        k = i / n
        _wset(c, x0 + (x1 - x0) * k, round(y0 + (y1 - y0) * k), col)


def _wpoly(c, pts, col):
    """Заливка многоугольника построчно на ленте со стыком по краям."""
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        xs = []
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            if (a[1] <= y < b[1]) or (b[1] <= y < a[1]):
                xs.append(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(int(round(xs[i])), int(round(xs[i + 1])) + 1):
                _wset(c, x, y, col)


def _burst(cx, cy, rx, ry, n, inner=0.5, rot=-math.pi / 2):
    """Точки звезды или комиксной вспышки: `n` лучей, впадины на доле `inner`."""
    pts = []
    for k in range(n * 2):
        a = rot + math.pi * k / n
        r = 1.0 if k % 2 == 0 else inner
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    return pts


def _board(c, rng, x0, y0, w, h, kind):
    """Рекламный щит в рамке: `kind` выбирает рисунок (звезда в лучах, вспышка, неоновые стрелки,
    закат над городом, маска героя, молния, бегущая строка, мишень)."""
    x1 = x0 + w - 1
    y1 = y0 + h - 1
    _wrect(c, x0, y0, x1, y1, T2)
    _wrect(c, x0, y0, x1, y0, T0)
    _wrect(c, x0, y0, x0, y1 - 1, T0)
    _wrect(c, x0 + 1, y1, x1, y1, DK)
    fx0, fy0, fx1, fy1 = x0 + 2, y0 + 2, x1 - 2, y1 - 2
    fh = fy1 - fy0 + 1
    cx = (fx0 + fx1) / 2.0
    cy = (fy0 + fy1) / 2.0

    def face(col, dots=None):
        for y in range(fy0, fy1 + 1):
            for x in range(fx0, fx1 + 1):
                # Растр комикса: точки в шахматном порядке через строку.
                dy = (y - fy0) % 4
                dot = dots is not None and dy % 2 == 0 and (x - fx0) % 4 == dy
                _wset(c, x, y, dots if dot else col)

    kind %= 8
    if kind == 0:
        face(L3)
        for y in range(fy0, fy1 + 1):
            for x in range(fx0, fx1 + 1):
                a = math.atan2(y - cy, x - cx)
                if int((a + math.pi) / (math.pi / 8.0)) % 2 == 0:
                    _wset(c, x, y, L2)
        r = fh * 0.46
        _wpoly(c, _burst(cx, cy + 1, r, r, 5, 0.42), FL1)
        _wpoly(c, _burst(cx, cy + 1, r * 0.45, r * 0.45, 5, 0.45), L0)
    elif kind == 1:
        face(L4, L3)
        rx = min(w * 0.4, fh * 1.0)
        ry = fh * 0.48
        _wpoly(c, _burst(cx, cy, rx, ry, 9, 0.62, 0.2), MO)
        _wpoly(c, _burst(cx, cy, rx * 0.84, ry * 0.84, 9, 0.62, 0.2), L1)
        _wpoly(c, _burst(cx, cy, rx * 0.5, ry * 0.5, 9, 0.7, 0.2), L0)
        _wrect(c, cx - 1, cy - 5, cx + 1, cy + 1, DK)
        _wrect(c, cx - 1, cy + 3, cx + 1, cy + 4, DK)
    elif kind == 2:
        face(L4)
        half = (fh - 6) // 2
        n = max(2, int((fx1 - fx0 - 8) // 11))
        start = cx - (n * 11 - 4) / 2.0
        for k in range(n):
            for dy in range(-half, half + 1):
                xx = start + k * 11 + (half - abs(dy)) * 0.8
                _wset(c, xx, cy + dy, FL2)
                _wset(c, xx + 1, cy + dy, FL2)
                _wset(c, xx + 2, cy + dy, L3)
        for x in range(fx0, fx1 + 1, 4):
            _wset(c, x, fy0, FL1)
            _wset(c, x, fy1, FL1)
    elif kind == 3:
        for y in range(fy0, fy1 + 1):
            t = (y - fy0) / float(fh)
            _wrect(c, fx0, y, fx1, y, L3 if t < 0.28 else (L2 if t < 0.52 else L1))
        sy = fy0 + fh * 0.62
        r = fh * 0.34
        for y in range(int(sy - r), fy1 + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                if (x - cx) ** 2 + (y - sy) ** 2 <= r * r and not (y > sy and y % 3 == 0):
                    _wset(c, x, y, L0)
        x = fx0
        while x <= fx1:
            bw = rng.randint(3, 6)
            bh = rng.randint(3, int(fh * 0.42))
            _wrect(c, x, fy1 - bh, min(x + bw - 1, fx1), fy1, L4)
            if bh > 5:
                _wset(c, x + 1, fy1 - bh + 2, FL1)
            x += bw
    elif kind == 4:
        face(L1, L0)
        for s in (-1, 1):
            _wellipse(c, cx + s * 7, cy, 7.5, 4.6, DK)
            _wpoly(c, [(cx + s * 11, cy - 3), (cx + s * 19, cy - 7), (cx + s * 12, cy + 3)], DK)
        _wrect(c, cx - 3, cy - 2, cx + 3, cy + 1, DK)
        for s in (-1, 1):
            _wellipse(c, cx + s * 7, cy, 3.4, 1.7, L0)
            _wset(c, cx + s * 7 + s * 3, cy - 2, L0)
    elif kind == 5:
        face(L3)
        for x in range(fx0 + 1, fx1):
            _wset(c, x, fy0 + 1, MO)
            _wset(c, x, fy1 - 1, MO)
        for y in range(fy0 + 1, fy1):
            _wset(c, fx0 + 1, y, MO)
            _wset(c, fx1 - 1, y, MO)
        bolt = [(cx + 2, fy0 + 3), (cx - 7, cy + 1), (cx - 1, cy + 1), (cx - 4, fy1 - 2), (cx + 8, cy - 2),
                (cx + 2, cy - 2), (cx + 7, fy0 + 3)]
        _wpoly(c, [(px + 1, py + 1) for px, py in bolt], L4)
        _wpoly(c, bolt, FL1)
        _wline(c, cx + 2, fy0 + 3, cx - 6, cy, L0)
    elif kind == 6:
        face(L4)
        _wrect(c, fx0 + 3, fy0 + 2, fx0 + 3 + int((fx1 - fx0) * 0.45), fy0 + 4, MO)
        for y in range(fy0 + 8, fy1 - 1, 4):
            x = fx0 + 3
            while x < fx1 - 14:
                n = rng.randint(2, 7)
                _wrect(c, x, y, min(x + n, fx1 - 14), y + 1, FL2)
                x += n + 3
        _wrect(c, fx1 - 11, fy0 + 3, fx1 - 2, fy1 - 3, L2)
        _wrect(c, fx1 - 11, fy0 + 3, fx1 - 2, fy0 + 3, L0)
        _wellipse(c, fx1 - 6.5, cy - 1, 2.2, 2.2, L0)
        _wrect(c, fx1 - 9, cy + 3, fx1 - 4, fy1 - 3, L0)
    else:
        face(L2, L1)
        r = fh * 0.47
        for y in range(fy0, fy1 + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = math.hypot(x - cx, y - cy) / r
                if d <= 1.0:
                    _wset(c, x, y, MO if d < 0.3 else (L0 if d < 0.56 else (L4 if d < 0.8 else L0)))


# --- Фон ---------------------------------------------------------------------------------------

def par3_back():
    """Даль на весь экран, 512×277: сумерки сверху переходят в коралловое зарево полосами
    облаков; в дымке стена небоскрёбов (чем ниже, тем светлее), над ними дирижабль и два луча
    прожектора от высотки-ориентира; ближе тёмные дома с огнями окон, баками и антеннами; низ
    сплошной."""
    rng = random.Random(541)
    c = Canvas(512, 277)
    ramp = (HZ2, HZ1, HZ0)
    for y in range(277):
        for x in range(512):
            k = min(max((y - 24) / 176.0, 0.0), 1.0)
            streak = (0.32 * math.sin(TAU * 3 * x / 512.0 + y * 0.05) * math.sin(y * 0.37)
                      + 0.2 * math.sin(TAU * 7 * x / 512.0 - y * 0.02) * math.sin(y * 0.23 + 1.0))
            v = k * 2.0 + streak * (0.3 + 0.5 * k)
            lvl = int(math.floor(v + BAYER[y % 4][x % 4] / 16.0))
            c.set(x, y, ramp[min(max(lvl, 0), 2)])
    # Лучи прожектора: конус светлее неба на тон, с редеющим краем.
    lx, ly = 331, 58
    lighter = {HZ2: HZ1, HZ1: HZ0, HZ0: HZ0}
    for y in range(0, ly):
        dy = ly - y
        for slope in (-0.62, 0.34):
            mid = lx + slope * dy
            half = 1.5 + dy * 0.085
            for x in range(int(mid - half - 1), int(mid + half + 2)):
                d = abs(x - mid) / half
                if d <= 1.0 and (d < 0.7 or BAYER[y % 4][x % 4] < 7):
                    _wset(c, x, y, lighter[_wget(c, x, y)])
    sky = [row[:] for row in c.px]
    darker = {HZ0: HZ1, HZ1: HZ2, HZ2: HZ3, HZ3: HZ3}

    def dim(x, y):
        """Силуэт в дымке: на тон темнее того, что за ним."""
        xi = int(math.floor(x)) % 512
        yi = int(round(y))
        if 0 <= yi < 277:
            c.set(xi, yi, darker[sky[yi][xi]])

    def dim_rect(x0, y0, x1, y1):
        for yy in range(int(y0), int(y1) + 1):
            for xx in range(int(x0), int(x1) + 1):
                dim(xx, yy)

    # Дирижабль: сигара с оперением и гондолой, светлая полоса по борту.
    ax, ay = 118, 46
    for yy in range(ay - 11, ay + 12):
        for xx in range(ax - 36, ax + 37):
            if ((xx - ax) / 35.0) ** 2 + ((yy - ay) / 10.0) ** 2 <= 1.0:
                dim(xx, yy)
    for j in range(10):
        dim_rect(ax - 44 + j, ay - 10 + j, ax - 34, ay - 10 + j)
        dim_rect(ax - 44 + j, ay + 10 - j, ax - 34, ay + 10 - j)
    dim_rect(ax - 9, ay + 11, ax + 9, ay + 14)
    for xx in range(ax - 30, ax + 31):
        c.set(xx, ay - 1, sky[ay - 1][xx])
    for xx in range(ax - 7, ax + 8, 3):
        c.set(xx, ay + 12, HZ0)
    # Дальние небоскрёбы стеной: надстройки, шпили, баки; окна светятся цветом неба за домом.
    x = 0
    while x < 512:
        w = min(rng.randint(13, 27), 512 - x)
        if 512 - (x + w) < 8:
            w = 512 - x
        top = rng.randint(64, 158)
        dim_rect(x, top, x + w - 1, 240)
        kind = rng.randint(0, 4)
        if kind == 0 and w >= 12:
            dim_rect(x + 3, top - 6, x + w - 4, top - 1)
            dim_rect(x + w // 2, top - 20, x + w // 2, top - 7)
        elif kind == 1 and w >= 12:
            dim_rect(x + 2, top - 4, x + w - 3, top - 1)
            dim_rect(x + 5, top - 8, x + w - 6, top - 5)
        elif kind == 2:
            dim_rect(x + 3, top - 8, x + 9, top - 3)
            dim_rect(x + 4, top - 10, x + 8, top - 9)
            dim_rect(x + 3, top - 2, x + 3, top - 1)
            dim_rect(x + 9, top - 2, x + 9, top - 1)
        elif kind == 3:
            for j in range(8):
                dim_rect(x + j, top - 8 + j, x + j, top - 1)
        for wy in range(top + 4, 234, 5):
            for wx in range(x + 2, x + w - 2, 4):
                if rng.random() < 0.2:
                    c.set(wx, wy, sky[wy][wx])
                    c.set(wx, wy + 1, sky[wy + 1][wx])
        x += w + rng.choice((0, 0, 2, 6))

    def tower(x0, w, top, feature):
        _wrect(c, x0, top, x0 + w - 1, 240, HZ3)
        _wrect(c, x0, top, x0, 240, HZ2)
        _wrect(c, x0, top, x0 + w - 1, top, HZ2)
        mid = x0 + w // 2
        if feature == 0:
            _wrect(c, mid, top - 16, mid, top - 1, HZ3)
            _wrect(c, mid - 3, top - 10, mid + 3, top - 10, HZ3)
            _wset(c, mid, top - 17, MO)
        elif feature == 1 and w >= 22:
            # Водяной бак на ножках с конусом.
            _wrect(c, mid - 5, top - 13, mid + 5, top - 5, HZ3)
            _wrect(c, mid - 5, top - 13, mid - 5, top - 5, HZ2)
            _wpoly(c, [(mid - 6, top - 13), (mid, top - 18), (mid + 6, top - 13)], HZ3)
            for lx_ in (mid - 5, mid, mid + 5):
                _wrect(c, lx_, top - 4, lx_, top - 1, HZ3)
        elif feature == 2 and w >= 22:
            _wrect(c, x0 + 4, top - 7, x0 + w - 5, top - 1, HZ3)
            _wrect(c, x0 + 4, top - 7, x0 + w - 5, top - 7, HZ2)
        elif w >= 24:
            # Щит рекламы на двух стойках.
            _wrect(c, x0 + 3, top - 12, x0 + 21, top - 4, HZ3)
            _wrect(c, x0 + 4, top - 11, x0 + 20, top - 5, HZ2)
            _wrect(c, x0 + 6, top - 9, x0 + 14, top - 9, MO if rng.random() < 0.5 else FL2)
            _wrect(c, x0 + 6, top - 7, x0 + 11, top - 7, HZ1)
            _wrect(c, x0 + 6, top - 3, x0 + 6, top - 1, HZ3)
            _wrect(c, x0 + 18, top - 3, x0 + 18, top - 1, HZ3)
        for wy in range(top + 5, 232, 7):
            for wx in range(x0 + 3, x0 + w - 4, 6):
                r = rng.random()
                if r < 0.05:
                    _wrect(c, wx, wy, wx + 2, wy + 3, FL1)
                elif r < 0.2:
                    _wrect(c, wx, wy, wx + 2, wy + 3, HZ0)
                    _wrect(c, wx, wy + 2, wx + 2, wy + 3, HZ1)
                elif r < 0.5:
                    _wrect(c, wx, wy, wx + 2, wy + 3, HZ2)

    # Ближние дома дали: тёмные, со светлой гранью от заката.
    x = 8
    while x < 496:
        w = rng.randint(22, 42)
        if not (300 < x + w and x < 362) and x + w < 508:
            tower(x, w, rng.randint(122, 200), rng.randint(0, 3))
        x += w + rng.randint(8, 34)
    # Высотка-ориентир с прожектором: уступы, шпиль, полосы окон, огни короны.
    _wrect(c, 316, 100, 346, 240, HZ3)
    _wrect(c, 321, 78, 341, 99, HZ3)
    _wrect(c, 326, 64, 336, 77, HZ3)
    _wrect(c, 331, 46, 331, 63, HZ3)
    for x0, y0, y1 in ((316, 100, 240), (321, 78, 99), (326, 64, 77)):
        _wrect(c, x0, y0, x0 + 1, y1, HZ2)
    for wx in range(320, 344, 4):
        for wy in range(104, 232):
            if wy % 9 < 6:
                c.set(wx, wy, HZ2 if (wx + wy // 9) % 3 else HZ0)
    for wx in range(324, 340, 3):
        _wrect(c, wx, 82, wx, 96, HZ2)
        c.set(wx, 80, FL1)
    for wx in range(328, 336, 2):
        c.set(wx, 66, FL1)
    _wrect(c, 329, 57, 333, 59, L0)
    c.set(331, 45, MO)
    # Кромка ближних крыш и сплошной низ.
    x = 0
    while x < 512:
        w = min(rng.randint(26, 52), 512 - x)
        top = rng.randint(222, 235)
        _wrect(c, x, top, x + w - 1, 240, HZ3)
        _wrect(c, x, top, x + w - 2, top, HZ2)
        if rng.random() < 0.6 and w > 16:
            ax_ = x + rng.randint(4, w - 6)
            _wrect(c, ax_, top - rng.randint(6, 12), ax_, top - 1, HZ3)
        for wx in range(x + 4, x + w - 4, 7):
            if rng.random() < 0.3:
                _wrect(c, wx, top + 4, wx + 1, top + 6, HZ0 if rng.random() < 0.7 else FL1)
        x += w
    c.rect(0, 238, 511, 276, HZ3)
    return c


def _footing(c, x, w):
    """Основание опоры расходится к земле, как у стволов: бетонный башмак с болтами."""
    for side in (-1, 1):
        for i in range(14):
            yy = 248 + i
            spread = int(i * 0.9)
            if side < 0:
                c.rect(max(x - spread, 0), yy, x + 3, yy, T1)
                c.set(max(x - spread, 0), yy, T0)
            else:
                c.rect(x + w - 3, yy, min(x + w + spread, 511), yy, T2)
    c.rect(x, 248, x + w - 1, 249, T0)
    c.rect(x, 250, x + w - 1, 250, T2)
    for bx in range(x + 4, x + w - 3, 6):
        c.rect(bx, 255, bx + 1, 256, DK)
        c.set(bx, 254, T0)


def _chimney(c, x, w):
    """Кирпичная труба: кладка вперевязку, свет слева, железные обручи."""
    for y in range(40, 262):
        row = (y - 40) // 6
        for xx in range(x, x + w):
            k = (xx - x) / float(w)
            seam = (y - 40) % 6 == 5 or (xx - x + (5 if row % 2 else 0)) % 10 == 0
            if k < 0.2:
                col = T1 if seam else T0
            elif k < 0.72:
                col = T2 if seam else T1
            else:
                col = DK if seam else T2
            c.set(xx, y, col)
    for by in (86, 148, 210):
        c.rect(x - 1, by, x + w, by, T0)
        c.rect(x - 1, by + 1, x + w, by + 2, L4)
        c.rect(x - 1, by + 3, x + w, by + 3, DK)
        for bx in range(x + 2, x + w - 1, 7):
            c.set(bx, by + 1, T1)
    # Скобы лестницы по тёмной стороне.
    for ry in range(96, 244, 8):
        if not any(by - 2 <= ry <= by + 4 for by in (86, 148, 210)):
            c.rect(x + w - 9, ry, x + w - 4, ry, T0)
            c.set(x + w - 9, ry + 1, DK)
            c.set(x + w - 4, ry + 1, DK)


def _pylon(c, x, w):
    """Решётчатая мачта: два уголка и раскосы крестом, между ними прозрачно; маячки на узлах."""
    for y in range(40, 262):
        for d, col in enumerate((T0, T1, T1, T2)):
            c.set(x + d, y, col)
        for d, col in enumerate((T1, T1, T2, DK)):
            c.set(x + w - 4 + d, y, col)
    step = 24
    for n, y0 in enumerate(range(52, 240, step)):
        for j in range(step):
            k = j / float(step)
            xa = x + 3 + (w - 7) * k
            xb = x + w - 4 - (w - 7) * k
            c.set(xb, y0 + j, T2)
            c.set(xb + 1, y0 + j, T2)
            c.set(xa, y0 + j, T1)
            c.set(xa + 1, y0 + j, T0 if j % 2 else T1)
        c.rect(x, y0 - 2, x + w - 1, y0 - 2, T0)
        c.rect(x, y0 - 1, x + w - 1, y0 - 1, T1)
        c.rect(x, y0, x + w - 1, y0, DK)
        if n % 3 == 1:
            c.rect(x - 2, y0 - 3, x - 1, y0 - 2, MO)
            c.set(x - 2, y0 - 3, L0)


def _column(c, x, w, rng):
    """Бетонная колонна: швы опалубки, водосточная труба, настенная лампа, рваная афиша."""
    for y in range(40, 262):
        for xx in range(x, x + w):
            k = (xx - x) / float(w)
            col = T0 if k < 0.16 else (T1 if k < 0.74 else T2)
            if (y - 40) % 37 == 36:
                col = T2 if k < 0.74 else DK
            elif (y - 40) % 37 == 0 and k < 0.74:
                col = T0
            c.set(xx, y, col)
    for y in range(58, 250, 37):
        for xx in (x + 7, x + 19):
            c.set(xx, y, T2)
    for _ in range(40):
        xx = rng.randint(x + 2, x + w - 12)
        yy = rng.randint(44, 244)
        c.set(xx, yy, T2)
        c.set(xx, yy + 1, T2)
    # Труба по правой стороне с хомутами.
    for y in range(40, 248):
        c.set(x + w - 9, y, L1)
        c.set(x + w - 8, y, L2)
        c.set(x + w - 7, y, L3)
        c.set(x + w - 6, y, L4)
    for y in range(70, 240, 42):
        c.rect(x + w - 10, y, x + w - 5, y + 1, DK)
        c.set(x + w - 10, y, T0)
    # Лампа на кронштейне.
    c.rect(x + 8, 84, x + 16, 85, DK)
    c.poly([(x + 9, 86), (x + 15, 86), (x + 17, 90), (x + 7, 90)], T2)
    c.rect(x + 9, 91, x + 15, 92, FL1)
    c.rect(x + 11, 91, x + 13, 91, L0)
    for j in range(8):
        for xx in range(x + 8 - j // 2, x + 17 + j // 2):
            if BAYER[(93 + j) % 4][xx % 4] < 8 - j and c.get(xx, 93 + j) in (T1, T0):
                c.set(xx, 93 + j, T0 if c.get(xx, 93 + j) == T1 else L0)
    # Афиша: бумага, вспышка, маска героя, оторванный угол.
    px, py = x + 4, 124
    c.rect(px, py, px + 21, py + 34, L0)
    c.rect(px + 21, py, px + 21, py + 34, T0)
    c.rect(px, py + 34, px + 21, py + 34, T2)
    tmp = Canvas(512, 277)
    _wpoly(tmp, _burst(px + 10.5, py + 13, 10, 11, 8, 0.6, 0.3), L1)
    _wpoly(tmp, _burst(px + 10.5, py + 13, 6, 7, 8, 0.65, 0.3), FL1)
    for yy in range(py + 1, py + 26):
        for xx in range(px + 1, px + 21):
            if tmp.get(xx, yy) is not None:
                c.set(xx, yy, tmp.get(xx, yy))
    c.rect(px + 5, py + 11, px + 16, py + 14, DK)
    c.rect(px + 7, py + 12, px + 9, py + 13, L0)
    c.rect(px + 12, py + 12, px + 14, py + 13, L0)
    for row, n in ((27, 14), (30, 10)):
        c.rect(px + 3, py + row, px + 3 + n, py + row, MO if row == 27 else L3)
    for j in range(6):
        c.rect(px, py + 34 - j, px + 5 - j, py + 34 - j, T1)
    c.line(px + 5, py + 34, px, py + 29, T2, 1)


def _stanchion(c, x, w):
    """Стальная двутавровая стойка: светлые полки, тёмная стенка, заклёпки, рёбра, внизу
    полосатая разметка."""
    for y in range(40, 262):
        for d, col in enumerate((T0, T0, T1, T1, T2)):
            c.set(x + d, y, col)
        c.rect(x + 5, y, x + w - 6, y, L4)
        c.set(x + 5, y, DK)
        for d, col in enumerate((T1, T1, T2, T2, DK)):
            c.set(x + w - 5 + d, y, col)
    for y in range(48, 258, 11):
        c.set(x + 2, y, DK)
        c.set(x + 2, y - 1, T0)
        c.set(x + w - 3, y, DK)
        c.set(x + w - 4, y - 1, T0)
    for y in range(72, 220, 46):
        c.rect(x + 5, y, x + w - 6, y, T1)
        c.rect(x + 5, y + 1, x + w - 6, y + 1, T2)
        c.rect(x + 5, y + 2, x + w - 6, y + 2, DK)
        for bx in range(x + 7, x + w - 7, 4):
            c.set(bx, y, T0)
    for y in range(220, 244):
        for xx in range(x, x + w):
            band = ((xx - x) + (y - 220)) // 6 % 2
            lit = xx < x + 5
            c.set(xx, y, (FL1 if lit or xx < x + w - 5 else T1) if band == 0 else DK)
    c.rect(x, 219, x + w - 1, 219, T0)
    c.rect(x, 244, x + w - 1, 244, DK)


def par3_trees():
    """Большие опоры, 512×277, прозрачно между ними: кирпичная труба, решётчатая мачта,
    бетонная колонна с афишей и стальная стойка стоят на местах стволов и расходятся к земле;
    наверху сплошной полосой рекламные щиты на лесах и клёпаная ферма, с фермы свисают лампы."""
    rng = random.Random(542)
    c = Canvas(512, 277)
    _chimney(c, 40, 30)
    _pylon(c, 196, 22)
    _column(c, 300, 38, rng)
    _stanchion(c, 452, 26)
    for x, w in ((40, 30), (196, 22), (300, 38), (452, 26)):
        _footing(c, x, w)
    # Леса за щитами: тёмная решётка до верха кадра.
    for y in range(0, 44):
        for x in range(512):
            cross = (x + y) % 8 == 0 or (x - y) % 8 == 0
            c.set(x, y, DK if cross else L4)
    # Щиты встык на всю ленту, разной высоты.
    x = 0
    for w, kind, top in ((76, 0, 3), (54, 2, 9), (62, 4, 1), (48, 5, 7), (66, 1, 2), (58, 6, 8), (60, 3, 0),
                         (56, 7, 5)):
        _board(c, rng, x, top, w, 42 - top, kind)
        for px in range(x + 6, x + w - 4, 14):
            c.rect(px, 42, px + 1, 43, T2)
        # Лампы подсветки на выносах над щитом.
        if top >= 5:
            for px in range(x + 8, x + w - 6, 16):
                c.rect(px, top - 3, px, top - 1, T1)
                c.rect(px - 1, top - 4, px + 2, top - 4, T0)
                c.set(px + 2, top - 3, FL1)
        x += w + 4
    # Ферма: пояса с заклёпками, раскосы зигзагом по тёмной стенке.
    for x in range(512):
        tri = abs((x % 16) - 8)
        c.set(x, 44, T0)
        c.rect(x, 45, x, 46, T1)
        c.set(x, 47, T2)
        c.rect(x, 48, x, 55, L4)
        zy = 48 + int(tri * 7 / 8.0)
        c.set(x, zy, T1)
        if zy + 1 <= 55:
            c.set(x, zy + 1, T2)
        c.set(x, 56, T0)
        c.rect(x, 57, x, 58, T1)
        c.set(x, 59, T2)
        c.set(x, 60, DK)
        if x % 8 == 3:
            c.set(x, 45, T0)
            c.set(x, 46, T2)
            c.set(x, 57, T0)
            c.set(x, 58, T2)
    # Лампы на проводах: провод чуть качается, колпак и горящая колба.
    for _ in range(11):
        x = rng.uniform(0, 512)
        length = rng.uniform(30, 96)
        ph = rng.uniform(0, TAU)
        for y in range(61, int(61 + length)):
            _wset(c, x + math.sin(y * 0.05 + ph) * 1.5, y, T2 if y % 7 else DK)
        ex = x + math.sin((61 + length) * 0.05 + ph) * 1.5
        ey = int(61 + length)
        _wrect(c, ex - 1, ey, ex + 1, ey, T1)
        _wrect(c, ex - 2, ey + 1, ex + 2, ey + 1, T2)
        _wrect(c, ex - 1, ey + 2, ex + 1, ey + 3, FL1)
        _wset(c, ex, ey + 2, L0)
    return c


def _tank(c, cx, base, cols, metal, scale=1.0):
    """Водяной бак на ножках: бочка из досок с обручами, коническая крыша, шпиль."""
    hi, light, body, shade = cols
    m0, m1, m2 = metal
    hw = int(11 * scale)
    leg = int(24 * scale)
    bh = int(26 * scale)
    plat = base - leg
    for lx in (-hw + 2, -hw // 3, hw // 3, hw - 2):
        _wrect(c, cx + lx, plat, cx + lx, base, m2)
    _wline(c, cx - hw + 2, plat + 2, cx + hw - 2, base - 2, m2)
    _wline(c, cx + hw - 2, plat + 2, cx - hw + 2, base - 2, m2)
    _wrect(c, cx - hw - 1, plat - 2, cx + hw + 1, plat - 2, m0)
    _wrect(c, cx - hw - 1, plat - 1, cx + hw + 1, plat - 1, m2)
    top = plat - 2 - bh
    for y in range(top, plat - 2):
        for x in range(cx - hw, cx + hw + 1):
            k = (x - cx + hw) / float(2 * hw)
            col = light if k < 0.26 else (body if k < 0.7 else shade)
            if (x - cx) % 4 == 0 and k >= 0.1:
                col = body if k < 0.26 else shade
            if k < 0.1:
                col = hi
            _wset(c, x, y, col)
    for hy in (top + int(bh * 0.25), top + int(bh * 0.72)):
        _wrect(c, cx - hw, hy, cx + hw, hy, m0)
        _wrect(c, cx - hw, hy + 1, cx + hw, hy + 1, m2)
    rh = int(10 * scale)
    for j in range(rh):
        half = (hw + 2) * (j + 1) / float(rh)
        for x in range(int(cx - half), int(cx + half) + 1):
            _wset(c, x, top - rh + j, light if x < cx - half * 0.3 else (body if x < cx + half * 0.35 else shade))
    _wrect(c, cx, top - rh - 3, cx, top - rh - 1, m1)


def _mast(c, cx, base, h, metal, tip):
    """Антенна: мачта с перекладинами ёлочкой, растяжки, маячок."""
    m0, m1, m2 = metal
    _wline(c, cx, base - h * 0.6, cx - 9, base, m2)
    _wline(c, cx + 1, base - h * 0.6, cx + 10, base, m2)
    for y in range(int(base - h), base + 1):
        _wset(c, cx, y, m0 if y < base - h * 0.5 else m1)
        if y > base - h * 0.55:
            _wset(c, cx + 1, y, m2)
    for n, half in enumerate((7, 5, 4, 2)):
        yy = int(base - h) + 3 + n * 4
        _wrect(c, cx - half, yy, cx + half, yy, m1)
        _wset(c, cx - half, yy, m0)
    _wset(c, cx, int(base - h) - 1, tip)


def _vent(c, cx, base, h, metal):
    """Вытяжка-грибок: труба и колпак."""
    m0, m1, m2 = metal
    _wrect(c, cx - 1, base - h, cx + 1, base, m1)
    _wrect(c, cx - 1, base - h, cx - 1, base, m0)
    _wrect(c, cx + 1, base - h, cx + 1, base, m2)
    _wrect(c, cx - 2, base - h - 4, cx + 2, base - h - 4, m0)
    _wrect(c, cx - 4, base - h - 3, cx + 4, base - h - 3, m1)
    _wrect(c, cx - 5, base - h - 2, cx + 5, base - h - 2, m1)
    _wrect(c, cx - 5, base - h - 2, cx - 2, base - h - 2, m0)
    _wrect(c, cx - 4, base - h - 1, cx + 4, base - h - 1, m2)


def par3_bushes():
    """Кладь крыш у земли, 512×120, прозрачный верх: за парапетом водяные баки, антенны,
    тарелки, будки выхода на крышу, кондиционеры, вытяжки, малые щиты; позади ряд темнее; низ
    сплошной: парапет из тёмного кирпича со светлой кромкой."""
    rng = random.Random(543)
    c = Canvas(512, 120)
    base = 96
    back_cols = (L2, L3, L3, L4)
    back_metal = (L3, L3, L4)
    # Задний ряд темнее: баки и антенны силуэтами.
    x = rng.uniform(10, 30)
    while x < 500:
        if rng.random() < 0.45:
            _tank(c, int(x), base, back_cols, back_metal, rng.uniform(0.85, 1.1))
            x += rng.uniform(46, 80)
        else:
            _mast(c, int(x), base, rng.uniform(40, 62), back_metal, MO)
            x += rng.uniform(28, 52)
    cols = (L0, L1, L2, L3)
    metal = (T0, T1, T2)
    x = 8.0
    n = 0
    order = (0, 3, 1, 5, 2, 4, 6, 1, 3, 0, 5, 4, 2, 6)
    while x < 498:
        kind = order[n % len(order)]
        n += 1
        ix = int(x)
        if kind == 0:
            _tank(c, ix + 13, base, cols, metal, 0.8)
            x += 30
        elif kind == 1:
            # Кондиционер: короб с решёткой и вентилятором.
            _wrect(c, ix, 78, ix + 21, base, T1)
            _wrect(c, ix, 78, ix + 21, 79, T0)
            _wrect(c, ix + 18, 80, ix + 21, base, T2)
            _wellipse(c, ix + 8, 87, 5.5, 5.5, DK)
            _wline(c, ix + 4, 87, ix + 12, 87, T2)
            _wline(c, ix + 8, 83, ix + 8, 91, T2)
            _wset(c, ix + 8, 87, T0)
            for yy in (82, 85, 88):
                _wrect(c, ix + 15, yy, ix + 17, yy, DK)
            x += 26
        elif kind == 2:
            _mast(c, ix + 9, base, rng.uniform(34, 50), metal, MO)
            x += 20
        elif kind == 3:
            # Будка выхода на крышу: скат, дверь с окошком, лампа над дверью.
            _wrect(c, ix, 68, ix + 25, base, L2)
            _wrect(c, ix, 68, ix + 6, base, L1)
            _wrect(c, ix + 20, 68, ix + 25, base, L3)
            _wpoly(c, [(ix - 2, 68), (ix + 27, 68), (ix + 27, 64), (ix - 2, 58)], L3)
            _wline(c, ix - 2, 58, ix + 27, 64, L0)
            _wrect(c, ix - 2, 68, ix + 27, 68, L4)
            _wrect(c, ix + 9, 76, ix + 17, base, L4)
            _wrect(c, ix + 11, 79, ix + 15, 83, FL1)
            _wrect(c, ix + 11, 79, ix + 15, 79, L0)
            _wset(c, ix + 13, 73, FL1)
            for yy in range(72, base, 6):
                _wrect(c, ix + 1, yy, ix + 7, yy, L2)
            x += 32
        elif kind == 4:
            # Тарелка на стойке: чаша серпом и облучатель.
            cx, cy = ix + 9, 76
            for yy in range(cy - 10, cy + 11):
                for xx in range(cx - 10, cx + 11):
                    d1 = math.hypot(xx - cx, yy - cy)
                    d2 = math.hypot(xx - cx - 5, yy - cy + 5)
                    if d1 <= 9.5 and d2 > 9.5:
                        _wset(c, xx, yy, L0 if d2 < 11.5 else (T1 if d1 < 8 else T2))
            _wline(c, cx - 2, cy + 3, cx + 7, cy - 7, T2)
            _wrect(c, cx + 7, cy - 8, cx + 8, cy - 7, FL2)
            _wrect(c, cx - 2, cy + 9, cx - 1, base, T1)
            _wrect(c, cx - 5, base - 2, cx + 3, base, T2)
            x += 22
        elif kind == 5:
            # Малый щит на двух стойках.
            _wrect(c, ix + 5, 80, ix + 6, base, T2)
            _wrect(c, ix + 29, 80, ix + 30, base, T2)
            _wline(c, ix + 6, 82, ix + 29, 94, T2)
            _board(c, rng, ix, 52, 36, 29, (5, 0, 7, 2)[n % 4])
            x += 40
        else:
            for k, h in enumerate((16, 24, 12)):
                _vent(c, ix + 5 + k * 11, base, h, metal)
            x += 36
        x += rng.uniform(1, 7)
    # Парапет: светлая кромка, тёмная кладка, потёки.
    c.rect(0, 92, 511, 119, L4)
    for xx in range(512):
        c.set(xx, 92, L0 if xx % 32 not in (0, 1) else L2)
        c.set(xx, 93, L1)
        c.set(xx, 94, L2)
        c.set(xx, 95, L3)
        c.set(xx, 96, DK)
    for y in range(97, 120):
        row = (y - 97) // 5
        for xx in range(512):
            if (y - 97) % 5 == 4 or (xx + (6 if row % 2 else 0)) % 12 == 0:
                c.set(xx, y, DK if (xx * 7 + y * 3) % 5 else L4)
            elif ((xx + (6 if row % 2 else 0)) // 12 * 5 + row * 3) % 7 == 0:
                c.set(xx, y, L3)
    for _ in range(26):
        xx = rng.randrange(512)
        for j in range(rng.randint(3, 10)):
            c.set(xx, 97 + j, L3)
    # Водосливы в парапете.
    for xx in range(40, 512, 128):
        c.rect(xx, 100, xx + 5, 103, DK)
        c.rect(xx, 99, xx + 5, 99, L2)
        c.rect(xx + 2, 104, xx + 3, 112, L3)
    return c


def canopy_front():
    """Балка над кадром спереди, 256×56, прозрачный низ: тёмная клёпаная балка с раскосами,
    под ней гирлянда флажков на провисшем тросе, провод и лампы под колпаками."""
    rng = random.Random(544)
    c = Canvas(256, 56)
    for x in range(256):
        tri = abs((x % 16) - 8)
        c.rect(x, 0, x, 1, L4)
        c.set(x, 2, L3)
        c.rect(x, 3, x, 9, DK)
        zy = 3 + int(tri * 6 / 8.0)
        c.set(x, zy, L4)
        c.set(x, 10, L3)
        c.rect(x, 11, x, 12, L4)
        c.set(x, 13, DK)
        if x % 8 == 3:
            c.set(x, 11, L2)
            c.set(x, 0, L3)
    # Длинный провод с пологим провисом.
    for x in range(256):
        c.set(x, 14 + int(round(9 * math.sin(math.pi * ((x + 40) % 256) / 256.0))), L4)
    # Гирлянда: трос в два пролёта, флажки треугольниками через один светлее.
    def rope(x):
        return 14 + 15 * math.sin(math.pi * (x % 128) / 128.0)

    for x in range(256):
        c.set(x, int(round(rope(x))), DK)
    for n, x in enumerate(range(8, 256, 12)):
        col = (L2, L4, L3)[n % 3]
        y0 = int(round(rope(x))) + 1
        for j in range(9):
            half = 3.6 * (1.0 - j / 9.0)
            for d in range(int(-half), int(half) + 1):
                c.set(x + d, y0 + j, col)
            if col != L4:
                c.set(x + int(half), y0 + j, L4)
        if col == L2:
            c.set(x - 1, y0 + 1, L1)
    # Лампы под колпаками на подвесах от балки.
    for x in (30, 94, 158, 222):
        n = rng.randint(30, 44)
        for y in range(14, n):
            c.set(x, y, DK)
        c.rect(x - 1, n, x + 1, n, L4)
        c.rect(x - 2, n + 1, x + 2, n + 1, L4)
        c.rect(x - 4, n + 2, x + 4, n + 2, L4)
        c.set(x - 3, n + 2, L3)
        c.rect(x - 1, n + 3, x + 1, n + 4, L1)
        c.set(x, n + 3, L0)
    return c


# --- Передний план -----------------------------------------------------------------------------

def trail_soil():
    """Кирпичная кладка, 64×64 по кругу в обе стороны: ряды вперевязку, кирпичи разного тона,
    кое-где тычки, сколы и трещины, свет сверху слева, тёмные швы."""
    rng = random.Random(551)
    n = 64
    c = Canvas(n, n)
    c.rect(0, 0, n - 1, n - 1, S4)
    lighter = {S1: S0, S2: S1}
    darker = {S1: S2, S2: S3}

    def brick(x0, y0, w, tone, pale):
        for y in range(y0, y0 + 7):
            for x in range(x0, x0 + w - 1):
                col = tone
                if y == y0 or (pale and y == y0 + 1):
                    col = lighter[tone]
                elif y == y0 + 6 or x == x0 + w - 2:
                    col = darker[tone]
                c.set(x % n, y % n, col)
        for _ in range(3):
            c.set(rng.randint(x0 + 1, x0 + w - 3) % n, rng.randint(y0 + 2, y0 + 5) % n,
                  darker[tone] if rng.random() < 0.7 else lighter[tone])
        if rng.random() < 0.16:
            # Скол угла.
            cx_ = x0 if rng.random() < 0.5 else x0 + w - 2
            cy_ = y0 if rng.random() < 0.5 else y0 + 6
            c.set(cx_ % n, cy_ % n, S4)
            c.set((cx_ + (1 if cx_ == x0 else -1)) % n, cy_ % n, S3)

    for row in range(8):
        off = 8 if row % 2 else 0
        for b in range(4):
            bx = off + b * 16
            parts = [(bx, 16)] if rng.random() < 0.74 else [(bx, 8), (bx + 8, 8)]
            for px, pw in parts:
                brick(px, row * 8, pw, rng.choice((S1, S1, S1, S2, S2)), rng.random() < 0.3)
    # Две трещины ступеньками через кирпич.
    for x0, y0 in ((21, 17), (50, 41)):
        x = x0
        for j in range(6):
            c.set(x % n, (y0 + j) % n, S4)
            c.set((x + 1) % n, (y0 + j) % n, S3)
            x += rng.choice((-1, 0, 1))
    return c


def trail_edge():
    """Бетонная плита крыши, 32×18 по кругу: поверхность на строке 4, на ней щебень и анкеры,
    под плитой стальной уголок с заклёпками, тень и потёки свисают на кладку; ниже прозрачно."""
    rng = random.Random(552)
    c = Canvas(32, 18)
    top = 4
    for x in range(32):
        c.set(x, top, G0)
        c.set(x, top + 1, G1 if x % 5 else G0)
        c.set(x, top + 2, G1 if rng.random() < 0.8 else G2)
        c.set(x, top + 3, G2)
        c.set(x, top + 4, ST0 if x % 4 == 1 else ST1)
        c.set(x, top + 5, FK)
        hang = top + 6 + int(0.8 + 1.2 * math.sin(x * TAU * 3 / 32.0) + rng.uniform(0, 1.6))
        c.rect(x, top + 6, x, hang, G3)
        c.set(x, hang + 1, S4)
        if x % 16 == 0:
            c.rect(x, top + 1, x, top + 3, G3)
        elif x % 16 == 1:
            c.rect(x, top + 1, x, top + 3, G0)
    # Потёки под уголком.
    for x, n in ((5, 3), (14, 1), (22, 3), (29, 2)):
        c.rect(x, top + 6, x, top + 8 + n, G3)
        c.set(x, top + 9 + n, S4)
    # Щебень и анкерные болты на поверхности.
    for x in range(32):
        if rng.random() < 0.3 and x % 16 not in (6, 7, 8):
            c.set(x, top - 1, G1 if rng.random() < 0.5 else G2)
    for x in (7, 23):
        c.rect(x, top - 2, x, top - 1, ST1)
        c.set(x, top - 3, ST0)
        c.set(x + 1, top - 1, G2)
    return c


def arch_bark():
    """Грань арки из крашеных балок, 32×32 по кругу: полки с заклёпками, по тёмной стенке
    раскосы зигзагом со светлой гранью и тенью, потёртости."""
    rng = random.Random(553)
    c = Canvas(32, 32)
    for y in range(32):
        yy = y % 16
        for x in range(32):
            if yy == 0:
                col = W0
            elif yy == 1:
                col = W0 if x % 4 == 1 else (W2 if x % 4 == 2 else W1)
            elif yy == 2:
                col = W1
            elif yy == 3:
                col = FK
            else:
                col = W2
                t = (yy - 4) / 11.0
                cell = (x // 16 + y // 16) % 2
                pos = t * 15.0 if cell == 0 else 15.0 - t * 15.0
                d = (x % 16) - pos
                if -2.0 <= d < -0.5:
                    col = W0
                elif -0.5 <= d <= 1.5:
                    col = W1
                elif 1.5 < d <= 2.6:
                    col = FK
            c.set(x, y, col)
    # Косынки в узлах, где раскосы сходятся к полке.
    for gx, gy in ((0, 14), (16, 30), (16, 5), (0, 21)):
        for dx in range(-2, 3):
            c.set((gx + dx) % 32, gy % 32, W1)
            c.set((gx + dx) % 32, (gy + 1) % 32, W1 if abs(dx) < 2 else W2)
        c.set(gx % 32, gy % 32, W0)
    for _ in range(7):
        x = rng.randrange(32)
        y = rng.randrange(32)
        if c.get(x, y) == W2:
            c.set(x, y, FK)
            c.set((x + 1) % 32, y, S2)
    return c


def _rod(c, x, h, bend, tip, flag=0):
    """Штыревая антенна от нижней строки: тонкий прут, у основания втулка, огонёк на конце."""
    for j in range(int(h)):
        k = j / float(h)
        px = x + bend * k * k
        c.set(px, c.h - 1 - j, ST1 if k < 0.5 else ST0)
        if j < 3:
            c.set(px + 1, c.h - 1 - j, G3)
            c.set(px - 1, c.h - 1 - j, G2)
    tx = x + bend
    c.set(tx, c.h - 1 - int(h), tip)
    if flag:
        # Вымпел на пруте треплет ветер.
        fy = c.h - 1 - int(h * 0.72)
        fx = x + bend * 0.5
        for d in range(1, 5):
            c.set(fx + d, fy + (d // 2 if flag > 0 else -(d // 3)), S0 if d < 3 else S1)
            c.set(fx + d, fy + 1 + (d // 2 if flag > 0 else -(d // 3)), S1 if d < 4 else None)


def dec_grass(i):
    """Пучок штыревых антенн перед героем, 32×24, два кадра качания на ветру; на концах
    огоньки, на высоком пруте вымпел."""
    rng = random.Random(561)
    c = Canvas(32, 24)
    for k, (x, h) in enumerate(((4, 16), (8, 10), (13, 22), (18, 13), (23, 19), (27, 8), (29, 14))):
        bend = rng.uniform(-2.5, 2.5) + (1.5 if i else -0.5)
        _rod(c, x, h, bend, PINK if k % 2 == 0 else W0, (1 if i else -1) if k == 2 else 0)
    return c


def dec_tuft(i):
    """Оборванные провода торчат из крыши, 32×14, два кадра: медные концы искрят по очереди."""
    c = Canvas(32, 14)
    for k, (x, h, side) in enumerate(((5, 8, 1), (12, 11, -1), (20, 7, 1), (26, 10, -1))):
        for j in range(h):
            t = j / float(h)
            px = x + side * 3.0 * t * t
            c.set(px, 13 - j, G3 if k % 2 else FK)
            if t < 0.5:
                c.set(px + 1, 13 - j, ST1)
        tx = int(round(x + side * 3.0))
        ty = 13 - h
        c.set(tx, ty, S0)
        if (k + i) % 2 == 0:
            c.set(tx, ty - 1, PINK)
            c.set(tx + side, ty, PINK)
            c.set(tx + side, ty - 1, G0)
            c.set(tx + side * 2, ty - 2, PINK)
            c.set(tx - side, ty - 2, PINK)
        else:
            c.set(tx + side * 2, ty + 1, PINK)
    return c


def dec_fern():
    """Спутниковая тарелка на треноге за героем, 48×32: чаша овалом смотрит вверх вправо,
    облучатель на штангах с огоньком, опорная плита."""
    c = Canvas(48, 32)
    for fx in (12, 23, 34):
        c.line(23, 22, fx, 30, ST1, 2)
    c.rect(21, 17, 25, 25, ST1)
    c.rect(21, 17, 22, 25, ST0)
    c.rect(11, 30, 35, 31, G2)
    c.rect(11, 30, 35, 30, G1)
    # Чаша вполоборота: тёмная спинка, светлое зеркало овалом с ободом и кольцом тени.
    cx, cy = 20.0, 13.0
    r2 = math.sqrt(0.5)
    for y in range(0, 30):
        for x in range(0, 48):
            u = ((x - cx) - (y - cy)) * r2
            v = ((x - cx) + (y - cy)) * r2
            back = ((u + 3.0) / 7.5) ** 2 + (v / 12.6) ** 2
            face = (u / 5.6) ** 2 + (v / 12.6) ** 2
            if face <= 1.0:
                if face > 0.74:
                    col = G0
                elif 0.3 < face < 0.42:
                    col = G2
                else:
                    col = G1 if v < 3.0 else G2
                c.set(x, y, col)
            elif back <= 1.0 and u < 0:
                c.set(x, y, ST1 if back > 0.6 or v > 2 else ST0)
    # Штанги сходятся к облучателю перед зеркалом.
    for v in (-10.0, 10.0):
        c.line(cx + v * r2, cy + v * r2, 31, 3, ST1, 1)
    c.line(cx, cy, 31, 3, FK, 1)
    c.rect(30, 1, 33, 4, W1)
    c.rect(30, 1, 33, 1, W0)
    c.set(34, 2, PINK)
    c.outline(FK)
    return c


def dec_bush():
    """Кладь крыши за героем, 64×36: кондиционер с вентилятором и жалюзи, вытяжка-грибок,
    труба коленом, щиток с молнией; стоят на бетонной плите."""
    c = Canvas(64, 36)
    # Короб кондиционера.
    c.rect(18, 10, 46, 33, G1)
    c.rect(18, 10, 46, 12, G0)
    c.rect(42, 13, 46, 33, G2)
    c.rect(18, 32, 46, 33, G2)
    c.rect(18, 13, 18, 31, G0)
    c.ellipse(29.5, 22.5, 8.5, 8.5, G3)
    c.ellipse(29.5, 22.5, 7.2, 7.2, FK)
    for a in (25, 115, 205, 295):
        r = math.radians(a)
        c.line(29.5 + math.cos(r) * 1.5, 22.5 + math.sin(r) * 1.5, 29.5 + math.cos(r) * 6.0,
               22.5 + math.sin(r) * 6.0, ST1, 3)
        c.line(29.5, 22.5, 29.5 + math.cos(r + 0.3) * 6.0, 22.5 + math.sin(r + 0.3) * 6.0, ST0, 1)
    c.ellipse(29.5, 22.5, 1.6, 1.6, G0)
    for y in (15, 18, 21, 24):
        c.rect(40, y, 44, y, FK)
        c.rect(40, y + 1, 44, y + 1, G3)
    c.rect(40, 28, 41, 29, PINK)
    c.rect(43, 28, 44, 29, W1)
    c.rect(19, 34, 23, 35, G3)
    c.rect(41, 34, 45, 35, G3)
    # Вытяжка-грибок слева.
    c.rect(7, 17, 11, 35, ST1)
    c.rect(7, 17, 8, 35, ST0)
    for dy, half in enumerate((3, 5, 6.5, 7)):
        c.rect(int(9 - half), 12 + dy, int(9 + half), 12 + dy, W1)
        c.rect(int(9 - half), 12 + dy, int(9 - half * 0.2), 12 + dy, W0)
    c.rect(2, 16, 16, 16, W2)
    c.rect(6, 22, 12, 23, G3)
    # Труба коленом справа и щиток.
    c.rect(47, 18, 55, 21, W1)
    c.rect(47, 18, 55, 18, W0)
    c.rect(52, 18, 55, 35, W1)
    c.rect(52, 19, 52, 35, W0)
    c.rect(55, 19, 55, 35, W2)
    c.rect(47, 21, 51, 21, W2)
    c.rect(51, 27, 56, 28, W2)
    c.rect(57, 23, 62, 35, ST1)
    c.rect(57, 23, 62, 24, ST0)
    for x, y in ((60, 26), (59, 27), (58, 28), (59, 28), (60, 28), (59, 29), (58, 30)):
        c.set(x, y, PINK)
    c.rect(58, 33, 61, 33, G3)
    # Плита под всем.
    c.rect(4, 34, 60, 35, G2)
    c.rect(13, 34, 50, 34, G1)
    c.outline(FK)
    return c


def dec_rock():
    """Шлакоблок и стопка кирпичей, 32×20: блок с двумя пустотами, три кирпича и половинка."""
    c = Canvas(32, 20)
    c.rect(1, 8, 14, 19, G1)
    c.rect(1, 8, 14, 9, G0)
    c.rect(12, 10, 14, 19, G2)
    for x in (3, 8):
        c.rect(x, 11, x + 3, 17, G3)
        c.rect(x, 11, x + 3, 12, FK)
        c.set(x + 3, 17, G2)
    for x0, y0, w, tone in ((16, 15, 7, S1), (24, 15, 7, S2), (19, 10, 9, S1)):
        c.rect(x0, y0, x0 + w - 1, y0 + 4, tone)
        c.rect(x0, y0, x0 + w - 1, y0, S0)
        c.rect(x0 + w - 1, y0 + 1, x0 + w - 1, y0 + 4, S2 if tone == S1 else S3)
        c.rect(x0, y0 + 4, x0 + w - 2, y0 + 4, S2 if tone == S1 else S3)
        c.set(x0 + 2, y0 + 2, S0)
    c.rect(23, 15, 23, 19, S4)
    c.poly([(22, 9), (26, 4), (30, 6), (27, 10)], S2)
    c.line(22, 9, 26, 4, S0, 1)
    c.set(15, 19, G2)
    c.outline(FK)
    return c


def dec_flowers():
    """Гирлянда лампочек на низких стойках, 32×20: провод провисает между стойками, лампы
    жёлтые и бирюзовые через одну."""
    c = Canvas(32, 20)
    posts = ((2, 8), (11, 5), (21, 9), (29, 6))
    n = 0
    for (x0, t0), (x1, t1) in zip(posts, posts[1:]):
        for x in range(x0, x1 + 1):
            k = (x - x0) / float(x1 - x0)
            y = t0 + (t1 - t0) * k + 3.0 * math.sin(math.pi * k)
            c.set(x, y, FK)
        for k in (0.3, 0.72):
            bx = int(round(x0 + (x1 - x0) * k))
            by = int(round(t0 + (t1 - t0) * k + 3.0 * math.sin(math.pi * k))) + 1
            col = PINK if n % 2 == 0 else W0
            c.rect(bx, by, bx + 1, by + 1, col)
            c.set(bx, by, G0)
            c.set(bx + 1, by + 2, W1 if col == W0 else S0)
            n += 1
    for x, t in posts:
        c.rect(x, t, x, 19, ST1)
        c.set(x, t - 1, ST0)
        c.set(x + 1, 19, G3)
        c.set(x - 1, 19, G2)
    return c


def dec_mush():
    """Три вытяжки-грибка у земли, 32×16: трубы разной высоты под бирюзовыми колпаками."""
    c = Canvas(32, 16)
    for x, h, r in ((7, 9, 4), (17, 13, 5), (26, 7, 3.5)):
        top = 15 - h
        c.rect(x - 1, top + 3, x + 1, 15, ST1)
        c.rect(x - 1, top + 3, x - 1, 15, ST0)
        for dy, k in enumerate((0.5, 0.85, 1.0)):
            half = int(round(r * k))
            c.rect(x - half, top + dy, x + half, top + dy, W1)
            c.rect(x - half, top + dy, x - half + max(half // 2, 1), top + dy, W0)
        c.rect(x + 1, top + 2, x + int(round(r)), top + 2, W2)
        c.set(x, top + 3, FK)
        c.set(x + 1, top + 3, FK)
    c.set(12, 15, G2)
    c.set(21, 15, G1)
    c.set(22, 15, G2)
    c.outline(FK)
    return c


# --- Враги (палитра спрайтов) ------------------------------------------------------------------

def _danger(c):
    """Враг тропы: чёрная внешняя обводка основы становится красной: опасен, убить нельзя."""
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
    """Ползун тропы: робот-паук из основы, четыре кадра, ноги переступают через одну."""
    return _danger(superheroes16.spider(i))


def drone(i):
    """Летун тропы: дрон-шпион из основы, четыре кадра винтов, корпус по центру кадра."""
    return _danger(superheroes16.drone(i))


def sprites():
    """Ленты этой демки в палитре спрайтов (ленты героя в `superheroes16.sprites`)."""
    return {
        "crab_walk": strip([crab(i) for i in range(4)]),
        "parrot_fly": strip([drone(i) for i in range(4)]),
    }


def backdrop():
    """Слои фона и балка над кадром в палитре фона `SUPERHEROES_BG`."""
    return {"par3_back": par3_back(), "par3_trees": par3_trees(), "par3_bushes": par3_bushes(),
            "canopy_front": canopy_front()}


def foreground():
    """Земля, арка, украшения в палитре переднего плана `SUPERHEROES_FG`."""
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
    items = superheroes16.shaded(sprites())
    for key, canvas in foreground().items():
        items[key] = (canvas, SUPERHEROES_FG)
    for key, canvas in backdrop().items():
        items[key] = (canvas, SUPERHEROES_BG)
    superheroes16.save_sheet(path, items, scale=2)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
