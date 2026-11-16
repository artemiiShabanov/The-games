#!/usr/bin/env python3
"""Набор «Фэнтези» для платформера × 16/32-bit «тропа» (#137), зеркало `space_trail16.py` и
`pixel_trail16.py`: те же ключи, размеры холстов, число кадров и точки опоры. Вместо джунглей и
грибов волшебный лес в сиреневых сумерках: фон без неба в три слоя (розово-сиреневая дымка с
силуэтами великого дерева, летающих островов с водопадами и башни мага; большие деревья с
витой корой, светящимися рунами и обвившей ствол лианой, сиреневая крона сплошной полосой
наверху, с неё свисают лианы с бутонами; у земли живая изгородь сиреневых кустов, гигантские
цветы, цветы-фонари и завитки ростков) и листва с лианами над кадром спереди; земля из тёмной
почвы, оплетённой корнями, под шапкой мха; арка из витой коры с рунами.

Свойства слотов, на которые рассчитана демка: ленты фона 512 пикселей стыкуются по краям, у
дали и кустов низ сплошной, у больших деревьев стволы на тех же местах и прозрачно между ними,
у листвы спереди прозрачный низ; грунт 64×64 стыкуется в обе стороны, кромка 32×18 с
поверхностью на строке 4, грань арки 32×32 по кругу; украшения стоят на нижней строке холста.

У фона и переднего плана свои палитры по 16 цветов (`FANTASY_BG`, `FANTASY_FG`); слизь и
блуждающий огонёк в палитре спрайтов `fantasy16.PALETTE`, их рисует основа, здесь они получают
красную обводку опасности. Ленты героя рисует `fantasy16.py`. Случайность с постоянным зерном:
картинка одна и та же.

    python3 tools/fantasy_trail16.py --preview out.png [--keys=a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fantasy16  # noqa: E402
from fantasy16 import Canvas, strip, K, RED  # noqa: E402

TAU = math.pi * 2.0

# Палитра фона: сумеречная дымка, сиреневая листва, кора, огни.
HZ0, HZ1, HZ2, HZ3, L0, L1, L2, L3, L4, T0, T1, T2, DK, FL1, FL2, MO = range(16)
FANTASY_BG = [
    (0xF0, 0xC6, 0xE6),  # HZ0  розовый свет в глубине леса
    (0xC0, 0x98, 0xDA),  # HZ1  дымка
    (0x8E, 0x70, 0xC2),  # HZ2  дальние силуэты
    (0x5E, 0x4A, 0x9C),  # HZ3  глубина дали, дальняя крона
    (0xF6, 0xD6, 0xFA),  # L0   блик листвы, лепестка
    (0xD2, 0x98, 0xF0),  # L1   листва, свет
    (0x9E, 0x60, 0xD8),  # L2   листва
    (0x6A, 0x3C, 0xAC),  # L3   листва, тень
    (0x40, 0x26, 0x78),  # L4   глубокая тень кроны
    (0xB8, 0x82, 0x5E),  # T0   кора, свет
    (0x80, 0x50, 0x46),  # T1   кора
    (0x4C, 0x2E, 0x3E),  # T2   кора, тень
    (0x1A, 0x12, 0x2C),  # DK   самая тёмная тень
    (0xF8, 0xDC, 0x6C),  # FL1  светлячки, сердцевины цветов, окна башни
    (0xF2, 0x6E, 0xAA),  # FL2  розовые лепестки
    (0x3E, 0xD6, 0xBA),  # MO   бирюза: руны, лианы, водопады, ростки
]

# Палитра переднего плана: мох, корни и почва, рунный камень, сиреневые лепестки, свечение.
FK, G0, G1, G2, G3, S0, S1, S2, S3, S4, ST0, ST1, W0, W1, W2, PINK = range(16)
FANTASY_FG = [
    (0x15, 0x10, 0x1E),  # FK   обводка
    (0xCE, 0xF0, 0x82),  # G0   кромка мха, роса
    (0x7C, 0xC2, 0x52),  # G1   мох
    (0x44, 0x8E, 0x4C),  # G2
    (0x26, 0x5A, 0x4A),  # G3   тень мха
    (0xCC, 0x92, 0x60),  # S0   корень, свет
    (0x98, 0x62, 0x48),  # S1   корень, кора
    (0x64, 0x42, 0x4E),  # S2   ком почвы, тень корня
    (0x44, 0x2C, 0x46),  # S3   почва
    (0x26, 0x1A, 0x30),  # S4   щели
    (0xCC, 0xC4, 0xE4),  # ST0  рунный камень, свет
    (0x86, 0x7A, 0xAE),  # ST1  камень, тень
    (0xEC, 0xBE, 0xF8),  # W0   лепесток, свет
    (0xAE, 0x6C, 0xE2),  # W1   лепесток, сиреневая листва
    (0x62, 0x38, 0xA0),  # W2   тень лепестка
    (0x62, 0xEC, 0xD4),  # PINK бирюзовое свечение: руны, огоньки, тычинки
]

BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))

# Знаки рун в клетке 5×9: отрезки (x0, y0, x1, y1).
RUNES = (
    ((2, 0, 2, 8), (2, 1, 4, 3), (2, 4, 4, 6)),
    ((2, 0, 2, 8), (2, 4, 0, 1), (2, 4, 4, 1)),
    ((2, 0, 4, 2), (4, 2, 2, 4), (2, 4, 0, 2), (0, 2, 2, 0), (2, 4, 2, 8)),
    ((0, 0, 0, 8), (0, 0, 4, 3), (4, 3, 0, 5), (0, 5, 4, 8)),
)


def _noise(x, y):
    """Постоянный шум 0..1 по координате пикселя."""
    n = (int(x) * 374761393 + int(y) * 668265263) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, int(y), col)


def _wget(c, x, y):
    return c.get(int(math.floor(x)) % c.w, int(y))


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


def _rune(put, x, y, kind, col, shadow=None):
    """Руна 5×9 с левым верхним углом (x, y): `put(x, y, col)` красит пиксель. Тень резьбы
    кладётся справа снизу до самого знака."""
    marks = []
    for x0, y0, x1, y1 in RUNES[kind % len(RUNES)]:
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            marks.append((x + x0 + int(round((x1 - x0) * i / max(n, 1))), y + y0 + (y1 - y0) * i // max(n, 1)))
    if shadow is not None:
        for px, py in marks:
            put(px + 1, py + 1, shadow)
    for px, py in marks:
        put(px, py, col)


def _ball(c, cx, cy, r, cols):
    """Гроздь листвы шаром: свет сверху слева, тень серпом снизу справа, рябь листьев шумом.
    `cols` от светлого к тёмному: блик, свет, тело, тень."""
    hi, light, body, shade = cols
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            u = (x - cx) / r
            v = (y - cy) / r
            d = u * u + v * v
            if d > 1.0:
                continue
            t = -u * 0.55 - v * 0.8 + (_noise(x, y) - 0.5) * 0.3
            if d > 0.7 and v > 0.3:
                col = shade
            elif t > 0.74:
                col = hi
            elif t > 0.28:
                col = light
            elif t > -0.42:
                col = body
            else:
                col = shade
            _wset(c, x, y, col)


def _clump(c, rng, cx, cy, rx, ry, cols, r=6.0, dots=None):
    """Крона или куст из гроздьев: шары сверху вниз, нижние перекрывают тень верхних, край
    выходит фестонами. `dots` это цвет редких бутонов."""
    n = max(3, int(rx * ry / (r * r) * 2.2))
    balls = []
    for _ in range(n):
        a = rng.uniform(0, TAU)
        d = math.sqrt(rng.random())
        balls.append((cy + math.sin(a) * ry * d, cx + math.cos(a) * rx * d, r * rng.uniform(0.75, 1.2)))
    balls.sort()
    for by, bx, br in balls:
        _ball(c, bx, by, br, cols)
    if dots is not None:
        for by, bx, br in balls[::3]:
            _wset(c, bx - 1, by - br * 0.3, dots)
            _wset(c, bx, by - br * 0.3 - 1, dots)
            _wset(c, bx, by - br * 0.3, dots)


def _liana(c, rng, x, y0, length, stem, shade, leaf, bud=None):
    """Лиана свисает от (x, y0): качается синусом, по сторонам парные листки, на конце бутон."""
    ph = rng.uniform(0, TAU)
    n = int(length)
    sx = x
    for j in range(n):
        k = j / max(n, 1)
        sx = x + math.sin(j * 0.07 + ph) * 3.0 * k
        _wset(c, sx, y0 + j, stem if j % 6 else shade)
        if j % 10 == 6 and j < n - 5:
            side = 1 if (j // 10) % 2 else -1
            _wset(c, sx + side, y0 + j, leaf)
            _wset(c, sx + side * 2, y0 + j - 1, leaf)
            _wset(c, sx + side * 2, y0 + j, shade)
    if bud is not None:
        ey = y0 + n
        for dy, half in ((0, 0), (1, 1), (2, 1), (3, 0)):
            for d in range(-half, half + 1):
                _wset(c, sx + d, ey + dy, bud[0] if d <= 0 else bud[1])
        _wset(c, sx, ey + 4, bud[2])


def _bell(put, x, y, halves, cols, glow):
    """Цветок-фонарь колокольчиком: верх в (x, y), `halves` это полуширина по строкам, край
    фестонами, под ним язычок света."""
    hi, body, shade = cols
    n = len(halves)
    for r, half in enumerate(halves):
        for d in range(-half, half + 1):
            if half >= 2 and d == -half + 1:
                col = hi
            elif half >= 1 and d >= half - (1 if half >= 4 else 0):
                col = shade
            else:
                col = body
            put(x + d, y + r, col)
    last = halves[-1]
    for d in range(-last, last + 1, 2):
        put(x + d, y + n, shade if d > 0 else body)
    put(x, y + n, glow)
    put(x, y + n + 1, glow)


def _bloom(c, cx, cy, r, petals, cols, heart, rot=0.0):
    """Гигантский цветок лицом к зрителю: лепестки розеткой, тёмные щели между ними, светлая
    жилка у верхних левых, жёлтая сердцевина. `cols`: блик, лепесток, щель."""
    hi, body, gap = cols
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dx = x - cx
            dy = y - cy
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx) + rot
            lobe = abs(math.cos(a * petals / 2.0))
            rr = r * (0.5 + 0.5 * lobe ** 0.6)
            if d > rr:
                continue
            if d < r * 0.3:
                col = heart if d < r * 0.3 - 1 or dx + dy < 0 else gap
            elif lobe < 0.32 or d > rr - 1.0 and dx * 0.5 + dy > 0:
                col = gap
            elif lobe > 0.9 and dx * 0.6 + dy < r * 0.25 and d > r * 0.42:
                col = hi
            else:
                col = body
            _wset(c, x, y, col)
    _wset(c, cx, cy, gap)
    _wset(c, cx + 1, cy + 1, gap)


def _stem(c, x0, y0, x1, y1, bend, stem, shade, width=2):
    """Стебель дугой от цветка (x0, y0) к земле (x1, y1); отдаёт точки для листьев."""
    pts = []
    n = int(abs(y1 - y0))
    for j in range(n + 1):
        k = j / max(n, 1)
        x = x0 + (x1 - x0) * k + math.sin(k * math.pi) * bend
        for d in range(width):
            _wset(c, x + d, y0 + j, stem if d < width - 1 or width == 1 else shade)
        pts.append((x, y0 + j))
    return pts


def _leaf(c, x, y, side, length, cols):
    """Лист от стебля вбок и вверх: остроконечный, светлая верхняя кромка."""
    light, body = cols
    for j in range(int(length)):
        k = j / length
        half = max(0.0, math.sin(k * math.pi) * length * 0.2)
        px = x + side * j
        py = y - j * 0.45
        for d in range(int(-half), int(half) + 1):
            _wset(c, px, py + d, light if d <= -half + 0.9 else body)


def _curl(c, x, base, top, r, stem, shade):
    """Росток завитком: стебель от земли и спираль наверху, закрученная влево."""
    for y in range(int(top + r), int(base)):
        sx = x + math.sin((y - top) * 0.07) * 1.5
        _wset(c, sx, y, stem)
        _wset(c, sx + 1, y, shade)
    cx = x - r
    cy = top + r
    steps = int(r * 14)
    for i in range(steps + 1):
        k = i / steps
        a = -k * TAU * 1.35
        rr = r * (1.0 - k * 0.78)
        px = cx + math.cos(a) * rr
        py = cy + math.sin(a) * rr
        _wset(c, px, py, stem)
        _wset(c, px + 1, py, stem if k < 0.6 else shade)
    _wset(c, cx, cy, shade)


# --- Фон ---------------------------------------------------------------------------------------

def _haze(x, y):
    """Тон дымки 0..3 (индексы HZ0..HZ3): темно под кроной, розовый свет на высоте островов,
    к земле снова темнеет; свет лежит пятнами."""
    stops = ((0, 3.0), (36, 2.6), (86, 1.6), (165, 0.35), (212, 1.0), (240, 2.3), (277, 3.0))
    t = 3.0
    for (y0, t0), (y1, t1) in zip(stops, stops[1:]):
        if y0 <= y <= y1:
            t = t0 + (t1 - t0) * (y - y0) / float(y1 - y0)
            break
    t += 0.3 * math.sin(TAU * x / 512.0 * 3 + y * 0.021) + 0.16 * math.sin(TAU * x / 512.0 * 7 - y * 0.05)
    return t


def _far_island(c, rng, cx, cy, w, h, fall=None, trees=()):
    """Летающий остров вдали: ровный верх с рощей, скала клином вниз, сбоку водопад в пустоту."""
    half = float(w)
    for d in range(h):
        k = 1.0 - d / float(h)
        half = max(0.0, min(half, w * k ** 0.6 + rng.uniform(-1.6, 0.8)))
        lo = int(round(cx - half))
        hi = int(round(cx + half * 0.9))
        if hi < lo:
            break
        for x in range(lo, hi + 1):
            u = (x - lo) / float(max(hi - lo, 1))
            col = HZ2 if u < 0.6 else HZ3
            if u < 0.16 and d < h * 0.7:
                col = HZ1 if (x + d) % 3 else HZ2
            # Уступы скалы: редкие тёмные полки.
            if d % 7 == 5 and 0.2 < u < 0.8 and (x // 5 + d) % 3 == 0:
                col = HZ3
            _wset(c, x, cy + d, col)
    for x in range(cx - w - 1, cx + w + 1):
        _wset(c, x, cy - 1, HZ2)
        _wset(c, x, cy - 2, HZ1 if (x * 5) % 7 < 5 else HZ2)
    for tx, tr in trees:
        _wline(c, cx + tx, cy - 2, cx + tx, cy - 2 - tr * 1.6, HZ3, 2)
        _wellipse(c, cx + tx, cy - 3 - tr * 1.9, tr, tr * 0.85, HZ2)
        _wellipse(c, cx + tx - tr * 0.3, cy - 3 - tr * 2.2, tr * 0.55, tr * 0.4, HZ1)
    if fall is not None:
        fx, length = fall
        fx += cx
        for d in range(length):
            k = d / float(length)
            if k > 0.65 and (d * 7) % 5 < 2:
                continue
            _wset(c, fx, cy - 1 + d, L0 if d < 3 else MO)
            if k < 0.8 and d % 4 != 3:
                _wset(c, fx + 1, cy - 1 + d, MO)
        for dx, dy in ((-3, 0), (4, 1), (0, 3), (-2, -3), (5, -2), (2, 5)):
            _wset(c, fx + dx, cy + length + dy, L0)


def par3_back():
    """Даль на весь экран, 512×277: розово-сиреневая дымка, великое дерево, летающие острова с
    водопадами и башней мага, тонкие дальние стволы, светлячки; низ сплошной."""
    rng = random.Random(341)
    c = Canvas(512, 277)
    for y in range(277):
        for x in range(512):
            t = _haze(x, y) + BAYER[y & 3][x & 3] / 16.0
            c.px[y][x] = max(0, min(3, int(t)))
    # Острова в самой дали: большой с башней, с рощей, два малых.
    _far_island(c, rng, 404, 150, 40, 38, fall=(26, 62), trees=((22, 5), (31, 4), (-30, 4)))
    # Башня мага: ствол с балконом, остроконечная крыша, окна светятся.
    for y in range(104, 149):
        for x in range(392, 403):
            _wset(c, x, y, HZ1 if x == 392 else (HZ2 if x < 398 else HZ3))
    for x in range(389, 406):
        _wset(c, x, 118, HZ3)
        _wset(c, x, 117, HZ2 if x < 398 else HZ3)
    for j in range(20):
        half = j * 0.42 + 0.5
        for x in range(int(397 - half), int(397 + half) + 1):
            _wset(c, x, 84 + j, HZ3 if x >= 397 else HZ2)
    _wline(c, 397, 84, 397, 78, HZ3, 1)
    _wset(c, 398, 79, FL2)
    _wset(c, 399, 79, FL2)
    _wset(c, 398, 80, FL2)
    for wx, wy in ((396, 109), (396, 126), (399, 138)):
        _wset(c, wx, wy, FL1)
        _wset(c, wx, wy + 1, FL1)
        _wset(c, wx + 1, wy + 1, FL1)
    _far_island(c, rng, 96, 132, 34, 34, fall=(-24, 54), trees=((-14, 6), (-2, 8), (12, 6), (24, 4)))
    _far_island(c, rng, 176, 184, 15, 16, trees=((0, 4),))
    _far_island(c, rng, 492, 196, 14, 15, fall=(8, 22), trees=((-5, 3),))
    _far_island(c, rng, 318, 96, 13, 13, trees=((2, 3),))
    # Великое дерево: ствол расходится к корням, ветви уходят в крону.
    for y in range(92, 252):
        k = (y - 92) / 160.0
        half = 12.0 + 3.0 * math.sin(k * 5.0) + 30.0 * k ** 4
        lo = int(256 - half)
        hi = int(256 + half * 0.92)
        for x in range(lo, hi + 1):
            u = (x - lo) / float(max(hi - lo, 1))
            col = HZ2 if u < 0.58 else HZ3
            if u < 0.1:
                col = HZ1
            elif (x - lo + int(y * 0.5)) % 9 == 0 and 0.12 < u < 0.9:
                col = HZ3
            _wset(c, x, y, col)
    # Дупло со светом.
    _wellipse(c, 254, 150, 4, 7, HZ3)
    _wellipse(c, 254, 151, 2, 4, FL1)
    for x1, y1, t in ((196, 64, 7), (318, 58, 7), (228, 40, 6), (288, 36, 6), (170, 84, 5), (344, 80, 5)):
        _wline(c, 256, 110, x1, y1, HZ3, t)
        _wline(c, 256, 108, x1, y1 - 2, HZ2, max(t - 3, 2))
    for cx, cy, rx, ry in ((256, 40, 44, 16), (196, 58, 30, 12), (318, 52, 32, 12), (166, 80, 20, 9),
                           (346, 76, 20, 9)):
        _clump(c, rng, cx, cy, rx, ry, (HZ1, HZ2, HZ2, HZ3), 8.0)
    # Дальняя крона вверху и тонкие стволы.
    for x, w in ((18, 6), (58, 4), (140, 7), (214, 4), (300, 5), (356, 7), (448, 5), (474, 8)):
        for y in range(0, 244):
            for dx in range(w):
                _wset(c, x + dx, y, HZ1 if dx == 0 and y > 70 else (HZ2 if dx < w * 0.6 else HZ3))
        _wline(c, x + w / 2.0, 70, x - 14, 44, HZ3, 2)
        _wline(c, x + w / 2.0, 62, x + w + 12, 40, HZ3, 2)
    for x in range(0, 512, 30):
        _clump(c, rng, x + rng.uniform(-6, 6), rng.uniform(22, 36), 20, 9, (HZ2, HZ2, HZ3, HZ3), 7.0)
    c.rect(0, 0, 511, 10, HZ3)
    # Светлячки и блёстки в дымке.
    for _ in range(46):
        x = rng.uniform(0, 512)
        y = int(rng.uniform(70, 232))
        _wset(c, x, y, FL1)
        if rng.random() < 0.3:
            _wset(c, x + 1, y, L0)
    for _ in range(60):
        _wset(c, rng.uniform(0, 512), int(rng.uniform(60, 228)), HZ0)
    # Подлесок у земли и сплошной низ.
    for x in range(0, 512, 16):
        _clump(c, rng, x + rng.uniform(-4, 4), rng.uniform(232, 240), 10, 5, (HZ2, HZ2, HZ3, HZ3), 5.0)
    c.rect(0, 238, 511, 276, HZ3)
    return c


def _trunk(c, rng, x0, x1, y0, y1):
    """Ствол волшебного дерева: кора свита жгутом (косые борозды), свет слева, сучки."""
    w = x1 - x0
    ph = rng.uniform(0, TAU)
    tones = (T0, T1, T2, DK)
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            k = (x - x0) / float(w)
            tone = 0 if k < 0.2 else (1 if k < 0.68 else 2)
            s = (x - x0 + y * 0.45 + 2.0 * math.sin(y * 0.05 + ph)) % 8.0
            if s < 1.0:
                tone += 1
            elif s < 2.0 and k < 0.6 and tone > 0:
                tone -= 1
            elif s > 6.0 and tone < 2 and _noise(x, y) < 0.35:
                tone += 1
            _wset(c, x, y, tones[min(tone, 3)])
    for _ in range(int((y1 - y0) / 70) + 1):
        kx = rng.uniform(x0 + 6, x1 - 6)
        ky = rng.uniform(y0 + 50, y1 - 30)
        _wellipse(c, kx, ky, 4, 5, T2)
        _wellipse(c, kx - 0.5, ky - 0.5, 2.5, 3.5, T1)
        _wellipse(c, kx, ky, 1.2, 2, DK)
        _wset(c, kx - 3, ky - 4, T0)
        _wset(c, kx - 2, ky - 5, T0)


def par3_trees():
    """Большие деревья, 512×277, прозрачно между ними: стволы с витой корой расходятся корнями к
    земле, на коре светятся руны, ствол обвивает лиана; сиреневая крона наверху сплошной
    полосой, с неё свисают лианы с бутонами."""
    rng = random.Random(342)
    c = Canvas(512, 277)
    for n, (x, w) in enumerate(((40, 30), (196, 22), (300, 38), (452, 26))):
        # Сучья уходят в крону.
        _wline(c, x + 4, 108, x - 22, 62, T2, 5)
        _wline(c, x + 4, 106, x - 22, 60, T1, 3)
        _wline(c, x + w - 4, 96, x + w + 20, 58, DK, 5)
        _wline(c, x + w - 5, 94, x + w + 19, 56, T2, 3)
        _trunk(c, rng, x, x + w, 40, 262)
        # Корни расходятся к земле.
        for i in range(14):
            yy = 248 + i
            spread = int(i * 0.5 + i * i * 0.05)
            for xx in range(x - spread, x + 3):
                _wset(c, xx, yy, T0 if xx == x - spread else T1)
            for xx in range(x + w - 3, x + w + spread + 1):
                _wset(c, xx, yy, DK if xx == x + w + spread else T2)
        # Лиана обвивает ствол: бирюзовая лента с тенью под ней.
        for turn in range(2):
            ty = 120 + turn * 62 + n * 9
            for dx in range(-1, w + 1):
                yy = ty + dx * 0.55
                _wset(c, x + dx, yy, MO if (dx + turn) % 5 else L0)
                _wset(c, x + dx, yy + 1, MO if dx < w * 0.5 else L3)
                _wset(c, x + dx, yy + 2, DK)
            for dx in range(3, w - 2, 7):
                yy = ty + dx * 0.55
                _wset(c, x + dx, yy - 1, MO)
                _wset(c, x + dx + 1, yy - 2, MO)
        # Руны в коре: два знака на ствол, вокруг тёмная резьба.
        for m, ry in enumerate((92 + n * 7, 206 - n * 11)):
            rx = x + w * 0.42 - 2 + m * 2

            def put(px, py, col):
                _wset(c, px, py, col)

            for dx in range(-2, 8):
                for dy in range(-2, 12):
                    if _wget(c, rx + dx, ry + dy) == T0:
                        _wset(c, rx + dx, ry + dy, T1)
            _rune(put, rx + 1, ry + 1, n + m * 2, DK)
            _rune(put, rx, ry, n + m * 2, MO)
            _wset(c, rx + 2, ry + 3, L0)
    # Крона: сплошная тёмная полоса, поверх три ряда гроздьев, нижний самый светлый.
    c.rect(0, 0, 511, 26, L4)
    for x in range(0, 512, 24):
        _clump(c, rng, x + rng.uniform(-5, 5), rng.uniform(4, 10), 18, 7, (L3, L3, L4, DK), 8.0)
    for x in range(0, 512, 22):
        _clump(c, rng, x + rng.uniform(-5, 5), rng.uniform(22, 32), 17, 8, (L1, L2, L3, L4), 8.0)
    for x in range(0, 512, 27):
        _clump(c, rng, x + rng.uniform(-6, 6), rng.uniform(46, 58), 18, 8, (L0, L1, L2, L3), 7.5,
               FL2 if rng.random() < 0.55 else None)
    # Лианы от нижней кромки кроны.
    for _ in range(12):
        x = rng.uniform(0, 512)
        y0 = 74
        while y0 > 30 and _wget(c, x, y0) is None:
            y0 -= 1
        _liana(c, rng, x, y0 + 1, rng.uniform(34, 100), MO, L3, L1, (FL2, L3, FL1))
    return c


def par3_bushes():
    """Подлесок у земли, 512×120, прозрачный верх: гигантские цветы и цветы-фонари на высоких
    стеблях, завитки ростков, живая изгородь сиреневых кустов; низ сплошной."""
    rng = random.Random(343)
    c = Canvas(512, 120)
    # Высокие цветы за изгородью.
    for n, x in enumerate(range(20, 512, 62)):
        cx = x + rng.uniform(-8, 8)
        kind = n % 3
        if kind == 0:
            r = rng.uniform(10, 12.5)
            cy = rng.uniform(24, 38)
            pts = _stem(c, cx, cy, cx + rng.uniform(-6, 6), 96, rng.uniform(-5, 5), MO, L4, 3)
            _leaf(c, pts[len(pts) // 2][0], pts[len(pts) // 2][1], -1, 15, (L0, MO))
            _leaf(c, pts[len(pts) * 2 // 3][0] + 2, pts[len(pts) * 2 // 3][1], 1, 13, (MO, L3))
            _bloom(c, cx + 1, cy, r, 7, (L0, FL2, L3), FL1, rng.uniform(0, 1))
        elif kind == 1:
            # Фонарь: стебель загибается крюком, колокольчик висит и светит вниз.
            top = rng.uniform(26, 36)
            pts = _stem(c, cx, top, cx + rng.uniform(-4, 4), 96, rng.uniform(-4, 4), MO, L4, 2)
            for j in range(12):
                a = math.pi * j / 11.0
                _wset(c, cx + 6 - math.cos(a) * 6, top - math.sin(a) * 6, MO)
                _wset(c, cx + 7 - math.cos(a) * 6, top - math.sin(a) * 6, MO)
            _leaf(c, pts[len(pts) // 2][0], pts[len(pts) // 2][1], 1, 14, (L0, MO))
            _bell(lambda px, py, col: _wset(c, px, py, col), cx + 12, top + 1,
                  (1, 2, 3, 4, 5, 5, 6, 6, 6, 7, 7), (L0, L1, L3), FL1)
            _wellipse(c, cx + 12, top + 14, 1.5, 1.5, FL1)
            for dx, dy in ((-4, 17), (4, 18), (0, 21), (-2, 24), (3, 26)):
                _wset(c, cx + 12 + dx, top + dy, FL1)
        else:
            r = rng.uniform(7.5, 9)
            cy = rng.uniform(44, 54)
            pts = _stem(c, cx, cy, cx + rng.uniform(-4, 4), 96, rng.uniform(-3, 3), MO, L4, 2)
            _leaf(c, pts[len(pts) // 2][0], pts[len(pts) // 2][1], -1, 11, (L0, MO))
            _bloom(c, cx, cy, r, 5, (L0, L1, L4), FL1, rng.uniform(0, 1))
        # Между цветами завиток ростка.
        _curl(c, cx + 31 + rng.uniform(-4, 4), 96, rng.uniform(50, 62), rng.uniform(5, 7), MO, L3)
    # Изгородь: дальний ряд темнее, ближний со светом и бутонами.
    for x in range(0, 512, 20):
        _clump(c, rng, x + rng.uniform(-4, 4), rng.uniform(76, 82), 13, 7, (L1, L2, L3, L4), 6.0)
    for x in range(10, 512, 26):
        _clump(c, rng, x + rng.uniform(-5, 5), rng.uniform(84, 90), 14, 6, (L0, L1, L2, L3), 6.0,
               FL2 if rng.random() < 0.6 else FL1)
    c.rect(0, 92, 511, 119, L4)
    for x in range(0, 512, 9):
        _ball(c, x + rng.uniform(-2, 2), rng.uniform(93, 98), rng.uniform(4.5, 6.5), (L1, L2, L3, L4))
    for _ in range(260):
        x = rng.uniform(0, 512)
        y = rng.uniform(102, 119)
        _wset(c, x, int(y), L3 if rng.random() < 0.6 else DK)
    for _ in range(18):
        x = rng.uniform(0, 512)
        y = int(rng.uniform(104, 117))
        _wset(c, x, y, MO)
        _wset(c, x, y - 1, L0)
    # Светлячки в воздухе.
    for _ in range(40):
        x = rng.uniform(0, 512)
        y = rng.uniform(8, 76)
        if _wget(c, x, y) is None and _wget(c, x + 1, y) is None and _wget(c, x - 1, y) is None:
            _wset(c, x, int(y), FL1)
    return c


def canopy_front():
    """Листва над кадром спереди, 256×56, прозрачный низ: тёмные сиреневые гроздья и лианы с
    бутонами."""
    rng = random.Random(344)
    c = Canvas(256, 56)
    c.rect(0, 0, 255, 6, DK)
    for x in range(0, 256, 22):
        _clump(c, rng, x + rng.uniform(-4, 4), rng.uniform(12, 19), 15, 6, (L2, L3, L4, DK), 6.5)
    for x in range(0, 256, 26):
        _clump(c, rng, x + rng.uniform(-4, 4), rng.uniform(2, 6), 16, 5, (L3, L4, DK, DK), 6.5)
    for _ in range(13):
        x = rng.uniform(0, 256)
        y0 = 30
        while y0 > 6 and _wget(c, x, y0) is None:
            y0 -= 1
        n = rng.randint(10, 46 - y0) if y0 < 36 else 6
        _liana(c, rng, x, y0 + 1, n, L3, L4, L2, (FL2, L3, FL1) if rng.random() < 0.6 else (MO, L3, L0))
    return c


# --- Передний план -----------------------------------------------------------------------------

def trail_soil():
    """Почва под корнями, 64×64 по кругу в обе стороны: тёмные комья, сквозь них идут корни
    разной толщины (тонкий наискось уходит под толстые, толстый поперёк лежит сверху), свет
    сверху слева; в земле обломки рунных плит с бирюзовой резьбой и редкая галька."""
    rng = random.Random(351)
    n = 64
    c = Canvas(n, n)
    c.rect(0, 0, n - 1, n - 1, S4)
    # Комья.
    for _ in range(150):
        cx = rng.uniform(0, n)
        cy = rng.uniform(0, n)
        rx = rng.uniform(1.6, 3.6)
        ry = rng.uniform(1.2, 2.6)
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                u = (x - cx) / rx
                v = (y - cy) / ry
                if u * u + v * v > 1.0:
                    continue
                c.set(x % n, y % n, S2 if u + v < -0.5 else (S4 if u + v > 1.0 else S3))

    def put(x, y, col):
        c.set(int(x) % n, int(y) % n, col)

    # Обломки рунных плит: гранёный камень со светлой гранью сверху слева, на большом резьба.
    for cx, cy, rx, ry, glow in ((14, 46, 6, 4, True), (49, 9, 4, 3, False), (38, 55, 3, 2, False)):
        for y in range(cy - ry - 1, cy + ry + 2):
            for x in range(cx - rx - 1, cx + rx + 2):
                u = abs(x - cx) / float(rx)
                v = abs(y - cy) / float(ry)
                if u > 1.0 or v > 1.0 or u + v > 1.45:
                    continue
                lit = (y - cy) <= -ry + 1 or (x - cx) <= -rx + 1
                put(x, y, ST0 if lit else ST1)
        for x in range(cx - rx + 1, cx + rx + 1):
            put(x, cy + ry + 1, S4)
        if glow:
            for dx, dy in ((0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (1, -1), (2, 0), (-1, 1), (-2, 2)):
                put(cx + dx, cy + dy, PINK)
            put(cx + 3, cy + 2, FK)
            put(cx - 3, cy - 1, FK)
        else:
            # Малый обломок без резьбы: только трещина.
            put(cx, cy, S3)
            put(cx + 1, cy + 1, S3)

    def root(points, thick_at, across):
        """Корень по точкам оси: круглое сечение (свет, тело, тень), под ним щель тени.
        `across` это ось толщины: 0 корень идёт вдоль x, 1 вдоль y."""
        for k, (a, b) in enumerate(points):
            t = thick_at(k)
            for d in range(t):
                if t <= 2:
                    col = S1 if d == 0 else S2
                else:
                    col = S0 if d == 0 else (S2 if d == t - 1 else S1)
                # Кольца коры: редкие насечки поперёк.
                if t > 3 and 0 < d < t - 1 and (k * 3) % 11 == 0:
                    col = S2
                if across == 0:
                    put(a, b + d, col)
                else:
                    put(a + d, b, col)
            if across == 0:
                put(a, b + t, S4)
                if k % 3 == 0:
                    put(a, b + t + 1, S4)
            else:
                put(a + t, b, S4)

    # Тонкий корень наискось: уклон один к одному, поэтому стыкуется в обе стороны.
    root([(k + 22 + int(round(2.0 * math.sin(TAU * k / 32.0))), k) for k in range(n)], lambda k: 2, 1)
    # Средний корень сверху вниз, гуляет вбок.
    root([(41 + int(round(5.0 * math.sin(TAU * k / n + 2.2) + 1.5 * math.sin(TAU * k * 3 / n))), k)
          for k in range(n)], lambda k: 3 if (k // 16) % 2 else 2, 1)
    # Толстый корень поперёк: одна волна на плитку, толщина дышит от четырёх до шести.
    root([(k, 22 + int(round(6.0 * math.sin(TAU * k / n + 1.0) + 1.5 * math.sin(TAU * k * 2 / n))))
          for k in range(n)], lambda k: 5 + int(round(math.sin(TAU * k / n + 4.0))), 0)
    # Отростки от толстого корня вниз, сходят на нет.
    for x0, y0, dx, length in ((9, 33, 1, 9), (30, 23, -1, 11), (55, 24, 1, 8)):
        for j in range(length):
            put(x0 + dx * (j // 2), y0 + j, S1 if j < length - 3 else S2)
            put(x0 + dx * (j // 2) + 1, y0 + j, S4)
    # Корешки-волоски и галька.
    for _ in range(9):
        x, y = rng.randrange(n), rng.randrange(n)
        if c.get(x, y) in (S3, S4):
            for j in range(rng.randint(2, 4)):
                if c.get((x + j) % n, (y + j // 2) % n) in (S3, S4, S2):
                    put(x + j, y + j // 2, S2)
    for _ in range(6):
        x, y = rng.randrange(n), rng.randrange(n)
        if c.get(x, y) in (S3, S4) and c.get((x + 1) % n, y) in (S3, S4, S2):
            put(x, y, ST1)
            put(x + 1, y, ST1)
            put(x, y - 1, ST0)
    return c


def trail_edge():
    """Шапка мха, 32×18 по кругу: поверхность на строке 4, над ней ростки и два цветка, вниз мох
    свисает подушками и прядями; ниже прозрачно, там грунт."""
    rng = random.Random(352)
    c = Canvas(32, 18)
    top = 4
    for x in range(32):
        cushion = 2.4 * abs(math.sin(math.pi * x / 8.0 + 0.4)) + 1.0 * math.sin(TAU * x / 16.0 + 1.0)
        hang = top + 4 + int(round(cushion))
        for y in range(top, hang + 1):
            c.set(x, y, G1 if y < top + 3 else G2)
        c.set(x, top, G0)
        if x % 3 == 0:
            c.set(x, top + 1, G0)
        if (x * 5) % 7 == 2:
            c.set(x, top + 2, G2)
        c.set(x, hang, G3)
        c.set(x, hang + 1, G3 if x % 2 else FK)
    # Пряди свисают в грунт.
    for x, m in ((3, 4), (11, 2), (14, 5), (22, 3), (29, 4)):
        base = top + 5
        while c.get(x, base + 1) is not None:
            base += 1
        for j in range(m):
            c.set(x, base + j, G2 if j < m - 1 else G3)
        c.set(x, base + m, FK)
    # Ростки и цветы над поверхностью.
    for x in range(32):
        if rng.random() < 0.45:
            h = rng.randint(1, 3)
            c.rect(x, top - h, x, top - 1, G1 if rng.random() < 0.5 else G0)
    for x in (8, 25):
        c.rect(x, top - 2, x, top - 1, G2)
        c.set(x, top - 3, W0)
        c.set(x - 1, top - 3, W1)
        c.set(x + 1, top - 3, W1)
        c.set(x, top - 4, W1)
    for x in (5, 18, 28):
        c.set(x, top + 2, PINK)
    return c


def arch_bark():
    """Грань арки, 32×32 по кругу: кора, свитая жгутом (косые пряди со светлым ребром и тёмной
    бороздой), сучок, светящаяся руна, пятна мха."""
    rng = random.Random(353)
    c = Canvas(32, 32)
    for y in range(32):
        wob = int(round(2.0 * math.sin(TAU * y / 32.0)))
        for x in range(32):
            s = (2 * x + y + wob) % 16
            if s == 0:
                col = S4
            elif s <= 2:
                col = S0
            elif s <= 9:
                col = S1
            elif s <= 13:
                col = S2
            else:
                col = S3
            if col == S1 and _noise(x, y) < 0.14:
                col = S2
            c.set(x, y, col)
    # Поперечные трещины коры.
    for _ in range(9):
        x = rng.randint(0, 31)
        y = rng.randint(0, 31)
        for k in range(rng.randint(2, 4)):
            c.set((x + k) % 32, y, S3)
    # Сучок.
    for y in range(4, 13):
        for x in range(19, 29):
            d = ((x - 23.5) / 4.5) ** 2 + ((y - 8) / 4.0) ** 2
            if d <= 1.0:
                c.set(x, y, S4 if d < 0.12 else (S2 if d < 0.5 else (S0 if x < 23 and y < 8 else S3)))
    # Мох в бороздах.
    for mx, my in ((3, 27), (27, 19), (13, 3)):
        for dx in range(-2, 3):
            for dy in range(-1, 2):
                if rng.random() < 0.75:
                    c.set((mx + dx) % 32, (my + dy) % 32, G2 if dy < 1 else G3)
        c.set(mx % 32, (my - 1) % 32, G1)

    def put(px, py, col):
        c.set(px % 32, py % 32, col)

    for rx, ry, kind in ((7, 17, 2),):
        for dx in range(-1, 7):
            for dy in range(-1, 11):
                if c.get((rx + dx) % 32, (ry + dy) % 32) == S0:
                    put(rx + dx, ry + dy, S1)
        _rune(put, rx, ry, kind, PINK, S4)
    return c


def _blade(c, x, h, bend, col, side, tip=None, curl=0):
    """Травинка от нижней строки: гнётся к вершине, у основания толще; `curl` закручивает
    кончик завитком в эту сторону, `tip` красит его."""
    for j in range(int(h)):
        k = j / h
        c.set(x + bend * k * k, c.h - 1 - j, col)
        if k < 0.55:
            c.set(x + bend * k * k + 1, c.h - 1 - j, side)
    tx = x + bend
    ty = c.h - int(h)
    if curl:
        c.set(tx + curl, ty - 1, col)
        c.set(tx + curl * 2, ty, col)
        c.set(tx + curl * 2, ty + 1, tip if tip is not None else col)
    elif tip is not None:
        c.set(tx, ty, tip)


def dec_grass(i):
    """Высокие ростки с завитками перед героем, 32×24, два кадра качания; часть кончиков
    светится."""
    rng = random.Random(361)
    c = Canvas(32, 24)
    for _ in range(15):
        x = rng.uniform(3, 29)
        col = rng.choice((G1, G2, G1, G0))
        glow = PINK if rng.random() < 0.35 else None
        curl = rng.choice((-1, 1, 0))
        h = rng.uniform(9, 20)
        _blade(c, x, h, rng.uniform(-3, 3) + (1.5 if i else -0.5), col, G3 if col == G2 else G2, glow, curl)
    return c


def dec_tuft(i):
    """Низкий пучок мха с двумя сиреневыми цветками, 32×14, два кадра качания."""
    rng = random.Random(362)
    c = Canvas(32, 14)
    for _ in range(11):
        _blade(c, rng.uniform(2, 30), rng.uniform(4, 10), rng.uniform(-2, 2) + (1 if i else 0), rng.choice((G0, G1, G2)), G3)
    for x, h in ((9, 10), (22, 8)):
        sx = x + (1 if i else 0)
        c.line(x, 13, sx, 14 - h, G2, 1)
        c.set(sx, 13 - h, W0)
        c.set(sx - 1, 13 - h, W1)
        c.set(sx + 1, 13 - h, W1)
        c.set(sx, 12 - h, W1)
    return c


def _petal(c, x, y, ang, length, width, cols):
    """Лепесток от точки (x, y) под углом `ang`: остроконечный, шире всего у середины, свет по
    верхней кромке, тень по нижней, жилка посередине."""
    light, body, shade = cols
    a = math.radians(ang)
    for j in range(int(length * 2)):
        k = j / (length * 2.0)
        half = width * 0.5 * math.sin(math.pi * k ** 0.75) + 0.6
        cx = x + math.cos(a) * j * 0.5
        cy = y + math.sin(a) * j * 0.5
        steps = int(half * 2) + 1
        for s in range(-steps, steps + 1):
            d = s * 0.5
            u = d / max(half, 0.5)
            # Свет на стороне лепестка, обращённой вверх.
            up = u * (1 if math.cos(a) > 0 else -1)
            col = light if up < -0.35 else (shade if up > 0.55 or abs(u) < 0.12 and k > 0.25 else body)
            c.set(cx - math.sin(a) * d, cy + math.cos(a) * d, col)


def dec_fern():
    """Гигантский цветок за героем, 48×32: чаша сиреневых лепестков веером из одной точки, в
    середине светящиеся тычинки, у земли два листа."""
    c = Canvas(48, 32)
    # Листья стелются по земле.
    for side in (-1, 1):
        for j in range(19):
            k = j / 19.0
            half = 3.4 * math.sin(math.pi * k ** 0.8)
            px = 24 + side * (3 + j)
            py = 29.5 - 2.5 * math.sin(k * math.pi * 0.9)
            for d in range(int(-half), int(half) + 1):
                c.set(px, py + d, G0 if d <= -half + 1 else (G1 if d < half - 1 else G2))
        c.line(24 + side * 4, 29, 24 + side * 19, 29, G3, 1)
    # Дальние лепестки темнее, ближние светлее и ниже.
    for ang, length, w in ((-116, 26, 11), (-64, 26, 11), (-90, 28, 12)):
        _petal(c, 24, 30, ang, length, w, (W1, W2, W2))
    # Тычинки с огоньками.
    for dx, top in ((-3, 6), (0, 3), (4, 7)):
        c.line(24, 20, 24 + dx, top + 2, G0, 1)
        c.rect(24 + dx - 1, top, 24 + dx + 1, top + 1, PINK)
        c.set(24 + dx, top - 1, PINK)
    for ang, length, w in ((-158, 20, 10), (-22, 20, 10), (-136, 23, 11), (-44, 23, 11)):
        _petal(c, 24, 30, ang, length, w, (W0, W1, W2))
    # Чашелистик у основания.
    c.poly([(19, 31), (21, 26), (24, 28), (27, 26), (29, 31)], G2)
    c.line(21, 27, 24, 29, G1, 1)
    c.outline(FK)
    return c


def dec_bush():
    """Сиреневый куст за героем, 64×36: гроздья листвы шарами, светящиеся ягоды, мох у корней."""
    rng = random.Random(364)
    c = Canvas(64, 36)
    # Ветки видны в просветах у земли.
    for x0, x1 in ((30, 22), (32, 34), (34, 44)):
        c.line(x0, 33, x1, 22, S1, 2)
    balls = [(14, 24, 8.5), (48, 23, 9), (24, 13, 9.5), (39, 12, 9), (31, 20, 10), (9, 28, 5.5), (55, 28, 5.5),
             (20, 27, 6.5), (43, 27, 6.5)]
    for bx, by, br in sorted(balls, key=lambda b: b[1]):
        _ball(c, bx, by, br, (W0, W1, W1, W2))
    for _ in range(16):
        bx, by, br = rng.choice(balls)
        x = bx + rng.uniform(-br * 0.6, br * 0.6)
        y = by + rng.uniform(-br * 0.6, br * 0.4)
        c.set(x, y, W2)
        c.set(x + 1, y - 1, W0)
    for x, y in ((12, 21), (27, 9), (41, 16), (50, 26), (22, 24), (35, 25), (45, 9)):
        c.rect(x, y, x + 1, y + 1, PINK)
        c.set(x, y, G0)
    # Кочка мха у корней: неровный верх, светлые макушки, тень снизу.
    for x in range(5, 59):
        top = 32 - int(round(1.2 * abs(math.sin(x * 0.55)) + (1 if rng.random() < 0.3 else 0)))
        for y in range(top, 36):
            c.set(x, y, G1 if y == top else (G2 if y < 34 else G3))
        if x % 4 == 1:
            c.set(x, top, G0)
    c.outline(FK)
    return c


def dec_rock():
    """Рунный камень, 32×20: обломок плиты наклонён, на светлой грани горит руна, сверху и у
    подножия мох."""
    c = Canvas(32, 20)
    c.poly([(5, 19), (4, 9), (9, 3), (19, 1), (26, 5), (28, 19)], ST1)
    c.poly([(6, 17), (6, 9), (10, 4), (18, 3), (21, 6), (21, 17)], ST0)
    # Скол и трещина.
    c.line(21, 6, 26, 8, ST0, 1)
    c.line(22, 10, 25, 15, FK, 1)
    c.set(8, 15, ST1)
    c.set(9, 16, ST1)
    _rune(c.set, 11, 6, 0, PINK, W2)
    c.set(13, 8, G0)
    c.set(17, 4, PINK)
    c.set(8, 7, PINK)
    # Мох шапкой и у земли.
    c.poly([(9, 3), (13, 1), (19, 1), (16, 3), (11, 4)], G1)
    c.line(11, 2, 16, 1, G0, 1)
    c.poly([(1, 19), (5, 15), (9, 19)], G2)
    c.poly([(21, 19), (26, 15), (31, 19)], G1)
    c.set(26, 16, G0)
    c.outline(FK)
    return c


def dec_flowers():
    """Цветы-фонари среди мха, 32×20: три колокольчика висят на загнутых стеблях и светят вниз."""
    rng = random.Random(365)
    c = Canvas(32, 20)
    for _ in range(9):
        _blade(c, rng.uniform(2, 30), rng.uniform(3, 7), rng.uniform(-2, 2), rng.choice((G1, G2)), G3)
    for x, top, side in ((6, 3, 1), (17, 1, -1), (25, 5, 1)):
        c.line(x, 19, x, top + 1, G2, 1)
        c.set(x + side, top, G2)
        c.set(x + side * 2, top, G2)
        c.set(x + side * 3, top + 1, G2)
        _bell(c.set, x + side * 3, top + 2, (0, 1, 2, 2), (W0, W1, W2), PINK)
        c.set(x + side * 3, top + 9, PINK)
        # Листок на стебле.
        c.set(x - side, top + 9, G1)
        c.set(x - side * 2, top + 8, G1)
        c.set(x - side * 2, top + 9, G2)
    return c


def dec_mush():
    """Пень у тропы, 32×16: срез с годовыми кольцами, кора в бороздах, корни в стороны, мох на
    краю и росток с двумя листками."""
    c = Canvas(32, 16)
    # Корни и бока.
    c.poly([(3, 15), (8, 11), (9, 15)], S1)
    c.poly([(23, 15), (24, 11), (29, 15)], S2)
    c.rect(8, 7, 24, 15, S1)
    c.rect(19, 7, 24, 15, S2)
    for x in (10, 13, 17, 21):
        c.line(x, 9, x, 14, S3, 1)
    c.rect(8, 7, 8, 14, S0)
    # Срез.
    c.ellipse(16, 6.5, 8.5, 3, S0)
    for x, y in ((11, 6), (12, 5), (14, 5), (16, 4), (18, 5), (20, 5), (21, 6), (20, 8), (18, 8), (16, 9), (14, 8),
                 (12, 8)):
        c.set(x, y, S1)
    c.rect(15, 6, 17, 7, S1)
    c.set(16, 6, S3)
    # Мох на левом краю, росток справа.
    c.rect(7, 5, 10, 6, G1)
    c.rect(7, 7, 8, 9, G2)
    c.set(8, 4, G0)
    c.set(9, 4, G0)
    c.line(21, 5, 21, 2, G2, 1)
    c.rect(22, 1, 23, 1, G1)
    c.rect(19, 2, 20, 2, G0)
    c.set(24, 0, G0)
    c.outline(FK)
    return c


# --- Враги (палитра спрайтов) ------------------------------------------------------------------

def _danger(c):
    """Враг тропы: чёрная внешняя обводка основы становится красной: опасен, убить нельзя.
    Внутренние чёрные линии (глаза, рот) остаются."""
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
    """Ползун тропы: слизь из основы, четыре кадра (купол сжимается и вытягивается)."""
    return _danger(fantasy16.slime(i))


def drone(i):
    """Летун тропы: блуждающий огонёк из основы, четыре кадра мерцания, тело по центру кадра."""
    return _danger(fantasy16.wisp(i))


def sprites():
    """Ленты этой демки в палитре спрайтов (ленты героя в `fantasy16.sprites`)."""
    return {
        "crab_walk": strip([crab(i) for i in range(4)]),
        "parrot_fly": strip([drone(i) for i in range(4)]),
    }


def backdrop():
    """Слои фона и листва над кадром в палитре фона `FANTASY_BG`."""
    return {"par3_back": par3_back(), "par3_trees": par3_trees(), "par3_bushes": par3_bushes(),
            "canopy_front": canopy_front()}


def foreground():
    """Земля, арка, украшения в палитре переднего плана `FANTASY_FG`."""
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


def preview(path, keys=None, scale=2):
    """Лист модуля: ленты врагов после светотени, передний план и фон в своих палитрах. `keys`
    оставляет часть лент (лист целиком выше полутора тысяч пикселей)."""
    items = fantasy16.shaded(sprites())
    for key, canvas in foreground().items():
        items[key] = (canvas, FANTASY_FG)
    for key, canvas in backdrop().items():
        items[key] = (canvas, FANTASY_BG)
    if keys:
        items = {k: items[k] for k in keys if k in items}
    fantasy16.save_sheet(path, items, scale=scale)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        keys_ = None
        scale_ = 2
        for arg in sys.argv:
            if arg.startswith("--keys="):
                keys_ = arg.split("=", 1)[1].split(",")
            if arg.startswith("--scale="):
                scale_ = int(arg.split("=", 1)[1])
        preview(sys.argv[sys.argv.index("--preview") + 1], keys_, scale_)
