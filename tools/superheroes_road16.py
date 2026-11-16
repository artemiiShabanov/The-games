#!/usr/bin/env python3
"""Набор «Супергерои» для гонки × 16/32-bit «псевдо-3D» (#137), зеркало `space_road16.py` и
`pixel_road16.py`: те же ключи, размеры холстов и порядок кадров, чтобы `racing_bit16.gd` брала
их без правок. Герой едет на своей машине с плавником (вид сзади): низкий синий родстер с
низким жёлтым плавником-спойлером со звездой (не выше 0.3 м, без мачт и парусов), турбиной в корме и персиковым от заката стеклом; за рулём герой со
спины, хохолок и жёлтый плащ, подол бьётся на ветру. Соперники на машинах злодеев: высокий
зелёно-серый броневик на шипастых колёсах, красные фары-«злые глаза», зубастый бампер, две
выхлопные трубы с огнём, из люка торчит робот-приспешник и машет клешнями; полоса и молния на
корме цвета экипажа. У дороги рекламный щит на столбе и красно-белая радиомачта с тарелками
вместо пальм, водяной бак на ногах с будкой выхода на крышу вместо хижины, обломок бетона с
арматурой, пожарный гидрант, заграждения со стрелкой и мигалками. На горизонте закат комикса:
индиго сверху, персик у горизонта, большое солнце, плоские облака, дирижабль и сигнал-звезда
в луче прожектора; небоскрёбы с огнями окон, улицы с огнями далеко внизу вместо моря. Дорога
асфальт, бордюр жёлто-чёрный, обочина бетон крыши.

Машины и пропы в палитре `superheroes16.PALETTE`, горизонт в своей (`SUPERHEROES_SKY`), цвета
дороги лентой `road_colors` по местам `ROAD_COLORS`.

    python3 tools/superheroes_road16.py --preview out.png [--keys=a,b]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import superheroes16  # noqa: E402
from superheroes16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD,  # noqa: E402
                           BRASS, METAL, DARK, RED, VIOLET, PLUM)

# Палитра горизонта: небо, солнце с облаками, улицы внизу, небоскрёбы. Места те же по смыслу, что
# у пиратов и космоса.
S0, S1, S2, S3, C0, C1, C2, M0, M1, M2, M3, I0, I1, I2, I3, SUN = range(16)
SUPERHEROES_SKY = [
    (0x25, 0x1D, 0x5E),  # S0  небо наверху, индиго
    (0x62, 0x2A, 0x86),  # S1  пурпур
    (0xD0, 0x48, 0x7A),  # S2  малиновый
    (0xFF, 0x96, 0x5A),  # S3  небо у горизонта, оранжевый
    (0xEF, 0x6F, 0x7C),  # C0  облако, коралл
    (0xFF, 0xC8, 0x6E),  # C1  край солнца, подсвеченный низ облака, луч прожектора
    (0xFF, 0xF4, 0xCC),  # C2  диск солнца, звёзды, сигнал
    (0x6E, 0x3A, 0x7E),  # M0  улицы вдали, в дымке
    (0x3E, 0x2A, 0x66),  # M1  кварталы
    (0x2C, 0x20, 0x50),  # M2  крыши у дороги
    (0xFF, 0xD2, 0x3A),  # M3  огни улиц
    (0x8E, 0x48, 0x88),  # I0  небоскрёбы в дымке
    (0x2A, 0x1E, 0x56),  # I1  ближние небоскрёбы
    (0xE8, 0x7C, 0x6C),  # I2  стена, освещённая закатом
    (0xFF, 0xDC, 0x6E),  # I3  свет в окнах
    (0xB4, 0xA4, 0xB4),  # SUN бетон у кромки дороги
]

# Цвета дороги по местам ленты `road_colors` (демка берёт их по индексу).
ROAD_COLORS = [
    (0x54, 0x50, 0x6E),  # 0 асфальт светлый
    (0x4A, 0x46, 0x64),  # 1 асфальт тёмный
    (0xFF, 0xD2, 0x3A),  # 2 бордюр жёлтый
    (0x24, 0x1E, 0x3C),  # 3 бордюр чёрный
    (0xF6, 0xF2, 0xEA),  # 4 разметка
    (0xB4, 0xA4, 0xB4),  # 5 бетон крыши светлый
    (0xA4, 0x94, 0xA6),  # 6 бетон крыши тёмный
    (0x6E, 0x3A, 0x7E),  # 7 дымка вдали
]


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wellipse(c, cx, cy, rx, ry, col):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                _wset(c, x, y, col)


def _star(cx, cy, r_out, r_in, n=5, sx=1.0, rot=-90.0):
    """Точки звезды или вспышки: `n` лучей, `sx` растягивает по ширине."""
    pts = []
    for k in range(n * 2):
        r = r_out if k % 2 == 0 else r_in
        a = math.radians(rot) + k * math.pi / n
        pts.append((cx + math.cos(a) * r * sx, cy + math.sin(a) * r))
    return pts


# --- Горизонт ----------------------------------------------------------------------------------

def sky():
    """Небо, 512×128, стыкуется по краям: индиго наверху, через пурпур и малиновый к оранжевому
    у горизонта (переходы точками, как растр комикса), редкие звёзды, большое солнце с ореолом,
    плоские облака с подсвеченным низом, дирижабль, два луча прожекторов и сигнал-звезда."""
    rng = random.Random(371)
    c = Canvas(512, 128)
    bands = [(0, S0), (30, S1), (58, S2), (86, S3)]
    for y in range(128):
        col = S0
        prev = S0
        start_y = 0
        for start, b in bands:
            if y >= start:
                prev = col
                col = b
                start_y = start
        for x in range(512):
            v = col
            d = y - start_y
            # Растр: над границей редкие точки нового цвета, под ней точки прежнего, всё реже.
            if start_y > 0 and d < 8:
                if d < 3 and (x + y) % 2 == 0:
                    v = prev
                elif d < 6 and x % 4 == (y % 2) * 2 and y % 2 == 0:
                    v = prev
                elif x % 8 == (y % 4) * 2 and y % 2 == 1:
                    v = prev
            c.set(x, y, v)
    for start, b in bands[1:]:
        for y in range(start - 5, start):
            for x in range(512):
                if x % 4 == ((y // 2) % 2) * 2 and y % 2 == 0 and start - y <= 4:
                    c.set(x, y, b)
    # Звёзды: только в индиго, яркие крестиком.
    for _ in range(46):
        c.set(rng.randint(0, 511), rng.randint(0, 34), S1 if rng.random() < 0.5 else C0)
    for _ in range(9):
        x = rng.randint(2, 509)
        y = rng.randint(2, 22)
        c.set(x, y, C2)
        if rng.random() < 0.6:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.set(x + dx, y + dy, C0)
    # Лучи прожекторов из-за домов: клин точками, расходится кверху.
    for bx, tx, ty in ((352, 420, 26), (470, 428, 30)):
        for y in range(ty, 128):
            k = (y - ty) / float(128 - ty)
            cx = tx + (bx - tx) * k
            half = 9 - 7 * k
            for x in range(int(cx - half), int(cx + half) + 1):
                if (x + y) % 2 == 0 and (y % 2 == 0 or abs(x - cx) < half * 0.5):
                    _wset(c, x, y, C1)
    # Солнце: ореол шашечкой, край, диск, две полосы облака поперёк.
    px, py, pr = 150, 98, 27
    for y in range(py - pr - 10, 128):
        for x in range(px - pr - 10, px + pr + 11):
            d = math.hypot(x - px, y - py)
            if pr < d <= pr + 5 and (x + y) % 2 == 0:
                c.set(x, y, C1)
            elif pr + 5 < d <= pr + 10 and (x + y) % 2 == 0 and y % 2 == 0:
                c.set(x, y, C1)
    _wellipse(c, px, py, pr, pr, C1)
    _wellipse(c, px, py, pr - 3, pr - 3, C2)
    # Облака: плоские полосы с бугристым верхом; высокие малиновые на индиго, низкие коралловые
    # с жёлтым от солнца низом.
    clouds = [(60, 20, 34, S1, S2), (250, 14, 46, S1, S2), (440, 46, 40, S2, C0), (20, 50, 38, S2, C0),
              (190, 44, 30, S2, C0), (330, 72, 54, C0, C1), (90, 76, 44, C0, C1), (500, 80, 36, C0, C1),
              (150, 96, 50, C0, C1), (270, 104, 40, C0, C1), (410, 106, 46, C0, C1), (30, 110, 30, C0, C1)]
    for cx, cy, w, body, lit in clouds:
        for i in range(6):
            ox = (i - 2.5) * w * 0.34 + rng.uniform(-3, 3)
            rx = w * rng.uniform(0.26, 0.42)
            ry = rng.uniform(2.0, 4.6) * (1.0 if i in (1, 2, 3, 4) else 0.6)
            for y in range(int(cy - ry - 1), int(cy) + 1):
                for x in range(int(cx + ox - rx - 1), int(cx + ox + rx + 2)):
                    if ((x - cx - ox) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                        _wset(c, x, y, body)
        for x in range(int(cx - w * 1.05), int(cx + w * 1.05)):
            _wset(c, x, cy + 1, lit)
        for x in range(int(cx - w * 0.7), int(cx + w * 0.8)):
            if (x // 2) % 2 == 0:
                _wset(c, x, cy + 2, lit)
    # Дирижабль: сигара, подсвеченное снизу брюхо, оперение, гондола с огнями.
    bx, by = 320, 40
    _wellipse(c, bx, by, 30, 9, I1)
    for y in range(by + 1, by + 10):
        for x in range(bx - 30, bx + 31):
            if c.get(x, y) == I1 and ((x - bx) / 30.0) ** 2 + ((y - by) / 9.0) ** 2 > 0.62:
                c.set(x, y, C0)
    for x in range(bx - 22, bx + 23):
        if c.get(x, by + 8) in (I1, C0):
            c.set(x, by + 8, C1)
    c.poly([(bx + 22, by - 3), (bx + 36, by - 10), (bx + 36, by - 3)], I1)
    c.poly([(bx + 22, by + 3), (bx + 36, by + 10), (bx + 36, by + 3)], I1)
    c.rect(bx + 28, by - 1, bx + 37, by + 1, I0)
    for x in range(bx - 24, bx + 20, 6):
        c.rect(x, by - 1, x + 2, by, I0)
    c.rect(bx - 9, by + 10, bx + 7, by + 13, I1)
    for x in range(bx - 7, bx + 6, 4):
        c.set(x, by + 11, I3)
        c.set(x + 1, by + 11, I3)
    c.set(bx - 31, by, I3)
    # Сигнал героя: светлый круг на облаках, в нём звезда.
    gx, gy = 424, 24
    _wellipse(c, gx, gy, 13, 11, C1)
    _wellipse(c, gx, gy, 11, 9, C2)
    c.poly(_star(gx, gy, 9, 3.6, sx=1.15), S1)
    return c


def _windows(c, rng, x0, x1, top, bottom, lit, step_x=3, step_y=3):
    """Окна сеткой: часть горит."""
    for y in range(top, bottom, step_y):
        for x in range(x0, x1, step_x):
            if rng.random() < lit:
                _wset(c, x, y, I3)


def islands():
    """Небоскрёбы на горизонте, 512×40, прозрачный верх: дальний ряд в дымке сплошной стеной,
    ближние тёмные башни с освещённой закатом гранью и огнями окон: ступенчатая со шпилем,
    башня с часами-прожектором, башня с водяным баком и антеннами."""
    rng = random.Random(373)
    c = Canvas(512, 40)
    # Дальний ряд: коробки разной высоты встык, низ сплошной.
    x = 0
    while x < 512:
        w = rng.randint(9, 20)
        h = rng.randint(7, 19)
        for xx in range(x, min(512, x + w)):
            for y in range(39 - h, 40):
                c.set(xx, y, I0)
        if rng.random() < 0.4 and x + w < 510:
            for y in range(39 - h - rng.randint(3, 6), 39 - h):
                c.set(x + w // 2, y, I0)
        if rng.random() < 0.3 and w > 12:
            for xx in range(x + 2, x + w - 2):
                c.set(xx, 39 - h - 1, I0)
                c.set(xx, 39 - h - 2, I0)
        for y in range(39 - h + 2, 38, 3):
            for xx in range(x + 1, min(511, x + w - 1), 2):
                if rng.random() < 0.16:
                    c.set(xx, y, C1)
        x += w
    # Ближние башни: (левый край, ширина, высота, вид).
    towers = ((18, 20, 22, "flat"), (62, 16, 30, "spire"), (112, 26, 18, "tank"), (168, 14, 26, "flat"),
              (214, 22, 33, "clock"), (262, 18, 20, "tank"), (300, 30, 26, "steps"), (352, 14, 34, "spire"),
              (392, 24, 16, "flat"), (436, 18, 28, "steps"), (478, 20, 21, "tank"))
    for x0, w, h, kind in towers:
        top = 39 - h
        for xx in range(x0, x0 + w):
            for y in range(top, 40):
                _wset(c, xx, y, I1)
        # Освещённая грань слева: солнце низко.
        for y in range(top, 40):
            _wset(c, x0, y, I2)
            if (y + x0) % 2 == 0:
                _wset(c, x0 + 1, y, I2)
        _windows(c, rng, x0 + 3, x0 + w - 1, top + 3, 39, 0.42)
        mid = x0 + w // 2
        if kind == "spire":
            for i in range(4):
                for xx in range(x0 + 2 + i, x0 + w - 2 - i):
                    _wset(c, xx, top - 1 - i, I1)
                _wset(c, x0 + 2 + i, top - 1 - i, I2)
            for y in range(max(0, top - 11), top - 4):
                _wset(c, mid, y, I1)
            _wset(c, mid, max(0, top - 12), I3)
        elif kind == "steps":
            for i, inset in enumerate((3, 6)):
                for xx in range(x0 + inset, x0 + w - inset):
                    for y in range(top - 3 * (i + 1), top - 3 * i):
                        _wset(c, xx, y, I1)
                for y in range(top - 3 * (i + 1), top - 3 * i):
                    _wset(c, x0 + inset, y, I2)
            for y in range(top - 10, top - 6):
                _wset(c, mid, y, I1)
        elif kind == "tank":
            tx = x0 + 5
            for xx in range(tx - 3, tx + 4):
                for y in range(top - 6, top - 2):
                    _wset(c, xx, y, I1)
            _wset(c, tx, top - 7, I1)
            _wset(c, tx - 1, top - 7, I1)
            _wset(c, tx + 1, top - 7, I1)
            _wset(c, tx - 3, top - 5, I2)
            for xx in (tx - 2, tx + 2):
                _wset(c, xx, top - 2, I1)
                _wset(c, xx, top - 1, I1)
            ax = x0 + w - 4
            for y in range(top - 8, top):
                _wset(c, ax, y, I1)
            for xx in (ax - 2, ax - 1, ax + 1, ax + 2):
                _wset(c, xx, top - 6, I1)
        elif kind == "clock":
            # Светящийся круг под крышей и зубцы короны.
            for xx in range(x0, x0 + w, 3):
                _wset(c, xx, top - 1, I1)
                _wset(c, xx, top - 2, I1)
            _wellipse(c, mid, top + 6, 4, 4, I3)
            _wellipse(c, mid, top + 6, 2.4, 2.4, C2)
            _wset(c, mid, top + 6, I1)
            _wset(c, mid, top + 5, I1)
            _wset(c, mid + 1, top + 6, I1)
        else:
            for xx in range(x0 + 3, x0 + w - 6):
                _wset(c, xx, top - 1, I1)
                _wset(c, xx, top - 2, I1)
    return c


def sea():
    """Улицы с огнями далеко внизу, 512×24 (место моря): вдали кварталы в дымке, ближе тёмные
    крыши разного тона, между ними улицы цепочками огней, у нижней кромки парапет и полоса бетона."""
    rng = random.Random(379)
    c = Canvas(512, 24)
    for y in range(24):
        col = M0 if y < 5 else (M1 if y < 14 else M2)
        c.rect(0, y, 511, y, col)
        if y in (5, 14):
            for x in range(0, 512, 2):
                c.set(x + (y % 2), y, M0 if y == 5 else M1)
    # Крыши кварталов: чем ближе, тем крупнее.
    for y0, h, wmin, wmax, a, b in ((1, 2, 6, 14, M1, M0), (6, 3, 10, 22, M2, M1), (10, 3, 12, 26, M2, M1),
                                    (15, 5, 18, 40, M1, M2)):
        x = rng.randint(0, 8)
        while x < 512:
            w = rng.randint(wmin, wmax)
            if rng.random() < 0.6:
                for xx in range(x, x + w):
                    for y in range(y0, y0 + h):
                        _wset(c, xx, y, a)
            x += w + rng.randint(2, 6)
    # Улицы: цепочки огней вдоль, гуще и реже по рядам; проспекты поперёк короткими столбиками.
    for y, step in ((0, 3), (4, 4), (9, 5), (13, 6), (20, 8)):
        off = rng.randint(0, 4)
        for x in range(off, 512, step):
            if rng.random() < 0.8:
                c.set(x, y, M3)
    for _ in range(26):
        x = rng.randint(0, 511)
        y = rng.randint(1, 16)
        for i in range(rng.randint(2, 4)):
            c.set(x + i * (1 if y > 9 else 0), y + i, M3 if i % 2 == 0 else M0)
    for _ in range(40):
        _wset(c, rng.uniform(0, 512), rng.randint(15, 19), M3 if rng.random() < 0.4 else M0)
    # Парапет крыши и бетон у дороги.
    c.rect(0, 21, 511, 21, M2)
    c.rect(0, 22, 511, 23, SUN)
    for x in range(0, 512, 16):
        c.set(x, 22, M0)
    return c


# --- Машины и пропы (палитра спрайтов) ----------------------------------------------------------

def _tire(c, cx, top, bot, half, phase, spikes=0):
    """Колесо сзади: широкая шина, протектор ёлочкой бежит вниз (`phase` 0..1). `spikes`: шипы
    наружу в эту сторону (−1 влево, 1 вправо)."""
    cx = int(round(cx))
    c.rect(cx - half, top + 3, cx + half, bot - 3, K)
    c.rect(cx - half + 2, top, cx + half - 2, bot, K)
    c.rect(cx - half + 2, top + 3, cx + half - 2, bot - 3, DARK)
    c.rect(cx - half + 2, top + 3, cx - half + 3, bot - 3, METAL)
    step = 6
    off = int(phase * step)
    for y in range(top + 2 + off, bot - 5, step):
        c.line(cx - half + 4, y, cx, y + 2, K, 1)
        c.line(cx, y + 2, cx + half - 3, y, K, 1)
        c.line(cx - half + 4, y + 1, cx, y + 3, METAL, 1)
    if spikes:
        edge = cx + spikes * half
        for y in range(top + 8 + off * 2, bot - 8, 12):
            c.poly([(edge, y - 3), (edge + spikes * 6, y), (edge, y + 3)], GREY)


def supercar(lean, phase, accent):
    """Машина героя со спины, 160×104: низкий синий родстер во всю ширину кадра, низкий жёлтый плавник со
    звездой посреди кормы (не выше 0.3 м), турбина с огнём (мерцает по `phase`), широкие фонари, полоса цвета
    `accent` на бампере и законцовке киля; за стеклом герой со спины: хохолок, жёлтый плащ, подол
    бьётся по `phase`. `lean` −1..1 крен."""
    c = Canvas(160, 104)
    sh = lean * 6
    lo = sh * 0.3
    mid = sh * 0.7
    flick = 1 if phase < 0.25 else 0
    _tire(c, 24 + lo, 58, 102, 11, phase)
    _tire(c, 136 + lo, 58, 102, 11, phase)
    # Диффузор под кормой: тёмная решётка с рёбрами.
    c.rect(34 + lo, 80, 126 + lo, 95, DARK)
    for x in range(42, 124, 12):
        c.rect(x + lo, 84, x + lo + 1, 95, METAL)
    # Стекло впереди: рама, персиковый отсвет заката, блики.
    c.poly([(42 + sh, 29), (118 + sh, 29), (128 + sh, 50), (32 + sh, 50)], SKY)
    c.poly([(36 + sh, 42), (124 + sh, 42), (128 + sh, 50), (32 + sh, 50)], AQUA)
    c.rect(42 + sh, 27, 118 + sh, 29, METAL)
    c.line(42 + sh, 28, 32 + sh, 50, METAL, 2)
    c.line(118 + sh, 28, 128 + sh, 50, METAL, 2)
    c.line(96 + sh, 32, 102 + sh, 40, WHITE, 2)
    c.line(104 + sh, 32, 108 + sh, 38, WHITE, 1)
    # Подголовник пустого кресла справа.
    c.ellipse(106 + sh, 44, 9, 9, DARK)
    c.ellipse(106 + sh, 44, 6, 6, RED if accent != RED else METAL)
    # Корма: тёмный низ с бампером, синий верх, крылья над колёсами, палуба багажника.
    c.poly([(13 + mid, 66), (147 + mid, 66), (145 + lo, 83), (15 + lo, 83)], NAVY)
    c.poly([(17 + mid, 58), (143 + mid, 58), (147 + mid, 64), (147 + mid, 71), (13 + mid, 71), (13 + mid, 64)], SEA)
    c.poly([(34 + sh, 48), (126 + sh, 48), (143 + mid, 59), (17 + mid, 59)], SEA)
    c.line(37 + sh, 50, 123 + sh, 50, WHITE, 1)
    c.line(52 + sh, 49, 44 + mid, 59, NAVY, 1)
    c.line(108 + sh, 49, 116 + mid, 59, NAVY, 1)
    c.line(19 + mid, 60, 141 + mid, 60, NAVY, 1)
    # Герой со спины: плечи в трико, плащ с подолом зубцами, шея, затылок с хохолком, уши.
    hx = 54 + sh * 1.1
    flap = 3 if flick else -2
    c.ellipse(hx, 40, 14, 6, SEA)
    c.poly([(hx - 10, 35), (hx + 10, 35), (hx + 15 + flap, 55), (hx + 9 + flap * 0.6, 51), (hx + 3 + flap * 0.5, 56),
            (hx - 3, 51), (hx - 9 + flap * 0.3, 55), (hx - 14, 50)], GOLD)
    c.line(hx - 4, 38, hx - 6 + flap * 0.3, 50, BRASS, 1)
    c.line(hx + 4, 38, hx + 7 + flap * 0.5, 50, BRASS, 1)
    c.rect(hx - 3, 31, hx + 3, 35, SKIN)
    c.ellipse(hx, 23, 9, 9, DARK)
    c.poly([(hx - 1, 15), (hx + 9, 11), (hx + 7, 17)], DARK)
    c.rect(hx - 10, 23, hx - 9, 28, SKIN)
    c.rect(hx + 9, 23, hx + 10, 28, SKIN)
    c.rect(hx - 4, 31, hx + 4, 31, TAN)
    # Киль посреди кормы: жёлтый, правая грань в тени, законцовка цвета экипажа, звезда.
    fx = 80 + sh * 1.2
    tx = 80 + sh * 1.45
    # Вид сзади: низкий плавник-спойлер не выше головы героя (около 0.3 м), не мачта и не парус;
    # к палубе расходится обтекателем.
    for y in range(37, 59):
        k = (y - 37) / 21.0
        cx = tx + (fx - tx) * k
        hw = 2.0 + 10.0 * k ** 1.7
        c.rect(cx - hw, y, cx + hw, y, GOLD)
        c.rect(cx + hw * 0.35, y, cx + hw, y, BRASS)
        if 39 <= y <= 41:
            c.rect(cx - hw, y, cx + hw, y, accent)
    c.poly(_star(fx * 0.85 + tx * 0.15 - 1.5, 51, 4.5, 1.9), SEA)
    c.rect(fx - 15, 57, fx + 15, 59, NAVY)
    # Фонари по краям кормы.
    lamp = RED if accent != RED else GOLD
    for side in (-1, 1):
        x0 = 80 + mid + side * 48
        c.rect(x0 - 14, 63, x0 + 14, 68, DARK)
        c.rect(x0 - 13, 64, x0 + 13, 67, lamp)
        c.rect(x0 - 13, 64, x0 - 9, 64, WHITE)
    # Бампер с полосой экипажа и турбина: кольца, огонь.
    c.rect(16 + lo, 74, 144 + lo, 77, accent)
    nx = 80 + lo * 1.6
    c.ellipse(nx, 79, 13, 11, DARK)
    c.ellipse(nx, 79, 11, 9, METAL)
    c.ellipse(nx, 79, 9, 7, K)
    c.ellipse(nx, 79, 5.5 + flick * 1.5, 4.2 + flick * 1.3, AQUA)
    c.ellipse(nx, 79, 3 + flick, 2.2 + flick, SKY)
    c.finish()
    c.rect(nx - 1, 78, nx + 1, 79, WHITE)
    return c


def villain_car(lean, phase, accent):
    """Машина злодея со спины, 160×104: высокий зелёно-серый броневик на шипастых колёсах,
    клёпаные листы, щель окна с решёткой, красные фары «злыми глазами», зубастый бампер, две
    выхлопные трубы (огонь и дым меняются по `phase`); из люка торчит робот-приспешник с красным
    глазом и машет клешнями. Полоса и круг с молнией цвета `accent`."""
    c = Canvas(160, 104)
    sh = lean * 6
    lo = sh * 0.3
    mid = sh * 0.7
    flick = 1 if phase < 0.25 else 0
    _tire(c, 22 + lo, 52, 102, 11, phase, -1)
    _tire(c, 138 + lo, 52, 102, 11, phase, 1)
    # Рама и бампер зубьями.
    c.rect(30 + lo, 80, 130 + lo, 90, DARK)
    for x in range(34, 124, 12):
        c.poly([(x + lo, 88), (x + lo + 10, 88), (x + lo + 5, 97)], GREY)
    # Робот в люке: бочонок с обручами, глаз, антенна, руки с клешнями.
    rx = 80 + sh * 1.2
    for side in (-1, 1):
        up = flick if side < 0 else 1 - flick
        ex = rx + side * 19
        ey = 17 - up * 3
        hx = rx + side * (24 + up * 2)
        hy = 8 - up * 4 + (1 - up) * 3
        c.line(rx + side * 9, 20, ex, ey, METAL, 3)
        c.line(ex, ey, hx, hy + 3, METAL, 3)
        claw = Canvas(160, 104)
        claw.ellipse(hx, hy, 5.2, 5.2, GREY)
        _carve(claw, hx + side * 1.0, hy - 3.4, 1.6 + up * 0.9, 3.6)
        c.paste(claw, 0, 0)
        c.ellipse(ex, ey, 2.4, 2.4, DARK)
    c.ellipse(rx, 18, 11.5, 13, VIOLET)
    c.rect(rx - 8, 6, rx + 8, 7, METAL)
    c.rect(rx - 10, 11, rx + 10, 11, PLUM)
    c.rect(rx - 11, 24, rx + 11, 24, PLUM)
    c.ellipse(rx, 17, 5.2, 5.2, DARK)
    c.ellipse(rx, 17, 3.6, 3.6, RED)
    c.line(rx + 4, 6, rx + 7, 1, DARK, 1)
    # Крыша скосом и короб кузова.
    c.poly([(42 + sh, 27), (118 + sh, 27), (131 + mid, 41), (29 + mid, 41)], PLUM)
    c.rect(42 + sh, 27, 118 + sh, 28, METAL)
    c.rect(rx - 17, 25, rx + 17, 28, DARK)
    c.poly([(29 + mid, 40), (131 + mid, 40), (135 + lo, 84), (25 + lo, 84)], VIOLET)
    # Листы брони: швы и заклёпки.
    c.line(29 + mid, 57, 131 + mid, 57, PLUM, 1)
    c.line(56 + mid, 41, 54 + lo, 83, PLUM, 1)
    c.line(104 + mid, 41, 106 + lo, 83, PLUM, 1)
    for x in range(34, 130, 9):
        c.set(x + mid, 43, DARK)
        c.set(x + lo, 81, DARK)
    for y in range(48, 80, 8):
        c.set(31 + mid * 0.8, y, DARK)
        c.set(129 + mid * 0.8, y, DARK)
    # Щель окна с решёткой.
    c.rect(48 + mid, 45, 112 + mid, 53, DARK)
    c.rect(50 + mid, 47, 110 + mid, 51, K)
    for x in range(56, 110, 9):
        c.rect(x + mid, 46, x + mid + 1, 52, METAL)
    # Полоса экипажа, фары «злыми глазами», круг с молнией.
    c.rect(28 + lo * 1.5, 61, 132 + lo * 1.5, 65, accent)
    lamp = RED if accent != RED else GOLD
    for side in (-1, 1):
        x0 = 80 + lo * 1.5 + side * 34
        c.poly([(x0 - side * 12, 74), (x0 + side * 12, 68), (x0 + side * 12, 77), (x0 - side * 12, 78)], K)
        c.poly([(x0 - side * 10, 75), (x0 + side * 10, 70), (x0 + side * 10, 76), (x0 - side * 10, 77)], lamp)
        c.rect(x0 + side * 5 - 1, 72, x0 + side * 5 + 1, 73, WHITE)
    ex = 80 + lo * 1.5
    c.ellipse(ex, 70, 10, 10, DARK)
    c.ellipse(ex, 70, 8, 8, accent)
    c.poly([(ex + 2, 62), (ex - 4, 71), (ex, 71), (ex - 2, 78), (ex + 4, 69), (ex, 69)], K)
    # Выхлопные трубы по углам: кольца, срез, огонь или дым.
    for side in (-1, 1):
        px = 80 + sh + side * 45
        c.rect(px - 3, 10, px + 3, 46, METAL)
        c.rect(px - 3, 10, px - 2, 46, GREY)
        c.rect(px - 4, 10, px + 4, 12, DARK)
        c.rect(px - 4, 28, px + 4, 29, DARK)
        c.rect(px - 5, 44, px + 5, 47, DARK)
        fire = flick if side < 0 else 1 - flick
        if fire:
            c.poly([(px - 3, 9), (px - 4, 4), (px - 1, 6), (px, 0), (px + 2, 5), (px + 4, 3), (px + 3, 9)], AQUA)
            c.poly([(px - 1, 9), (px, 4), (px + 1, 9)], SKY)
        else:
            c.ellipse(px + side * 1, 6, 3.5, 2.5, GREY)
            c.ellipse(px - side * 2, 3, 2.5, 2, GREY)
    c.finish()
    c.rect(rx - 2, 15, rx - 1, 16, WHITE)
    c.set(rx + 7, 1, RED)
    c.set(rx + 7, 0, RED)
    return c


def _carve(c, cx, cy, rx, ry):
    """Вырезать эллипс из холста (раствор клешни)."""
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if 0 <= x < c.w and 0 <= y < c.h and ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                c.px[y][x] = None


def carts_strip(accent, villain):
    """Три крена (влево, прямо, вправо) по два кадра: лента 6 кадров по 160, порядок как у пиратов."""
    frames = []
    for lean in (-1.0, 0.0, 1.0):
        for ph in (0.0, 0.5):
            frames.append(villain_car(lean, ph, accent) if villain else supercar(lean, ph, accent))
    return strip(frames)


def billboard():
    """Рекламный щит на столбе у обочины, 120×240 (место пальмы): широкий щит с комиксной
    вспышкой и звездой на синем в точку, полоса подписи, сверху три лампы на кронштейнах, под
    щитом мостик с перилами; столб с обручами, подкосами и лесенкой, бетонная тумба."""
    c = Canvas(120, 240)
    # Тумба и столб.
    c.poly([(36, 239), (42, 226), (78, 226), (84, 239)], GREY)
    c.rect(42, 226, 78, 228, WHITE)
    c.rect(54, 92, 66, 228, GREY)
    c.rect(54, 92, 56, 228, WHITE)
    c.rect(63, 92, 66, 228, METAL)
    for y in range(118, 226, 34):
        c.rect(53, y, 67, y + 2, DARK)
    # Лесенка справа от столба.
    c.rect(71, 96, 72, 224, METAL)
    for y in range(100, 224, 7):
        c.rect(66, y, 72, y, METAL)
    # Подкосы к мостику.
    c.line(58, 124, 22, 94, METAL, 3)
    c.line(62, 124, 98, 94, METAL, 3)
    # Мостик с перилами.
    c.rect(2, 89, 117, 92, DARK)
    c.rect(2, 89, 117, 89, METAL)
    # Щит: рама, синее поле в точку, вспышка, звезда, полоса подписи.
    c.rect(3, 10, 116, 86, DARK)
    c.rect(6, 13, 113, 83, SEA)
    for y in range(15, 70, 4):
        for x in range(8 + (y // 4 % 2) * 2, 113, 4):
            c.set(x, y, NAVY)
    c.poly(_star(60, 42, 30, 19, n=11, sx=1.55, rot=-82), RED)
    c.poly(_star(60, 42, 26, 16, n=11, sx=1.55, rot=-82), GOLD)
    c.poly(_star(60, 43, 17, 7.2), WHITE)
    c.poly(_star(60, 43, 13, 5.4), SEA)
    c.rect(6, 71, 113, 83, WHITE)
    for x0, w in ((12, 16), (32, 8), (44, 22), (70, 12), (86, 20)):
        c.rect(x0, 75, x0 + w, 79, K)
    c.rect(6, 70, 113, 70, DARK)
    # Лампы на кронштейнах над щитом.
    for x in (24, 60, 96):
        c.rect(x, 4, x + 1, 10, METAL)
        c.rect(x - 4, 2, x + 5, 4, DARK)
        c.rect(x - 3, 5, x + 4, 6, GOLD)
    c.finish()
    # Заклёпки рамы после обводки.
    for x in range(8, 114, 15):
        c.set(x, 11, METAL)
        c.set(x, 85, METAL)
    return c


def mast():
    """Радиомачта у обочины, 120×240 (место второй пальмы): решётчатая башня красными и белыми
    поясами сужается кверху, две тарелки, перекладины антенн, шпиль с красным маяком; у подножия
    шкаф аппаратуры с жалюзи."""
    c = Canvas(120, 240)
    top_y, base_y = 44, 239

    def half(y):
        return 3 + (22 - 3) * (y - top_y) / float(base_y - top_y)

    # Пояса: ноги, ригели и раскосы; верхние узкие пояса сплошные.
    edges = [top_y, 70, 100, 134, 170, 206, base_y]
    for i in range(len(edges) - 1):
        y0, y1 = edges[i], edges[i + 1]
        col = RED if i % 2 == 0 else WHITE
        h0, h1 = half(y0), half(y1)
        if h1 < 9:
            c.poly([(60 - h0, y0), (60 + h0, y0), (60 + h1, y1), (60 - h1, y1)], col)
            c.line(60 - h0 + 2, y0 + 2, 60 + h1 - 2, y1 - 2, DARK, 1)
            c.line(60 + h0 - 2, y0 + 2, 60 - h1 + 2, y1 - 2, DARK, 1)
        else:
            c.line(60 - h0, y0, 60 - h1, y1, col, 4)
            c.line(60 + h0, y0, 60 + h1, y1, col, 4)
            c.line(60 - h0, y0, 60 + h1, y1, col, 2)
            c.line(60 + h0, y0, 60 - h1, y1, col, 2)
        c.rect(60 - h0 - 1, y0 - 1, 60 + h0 + 1, y0 + 1, DARK)
    # Шпиль с маяком и перекладины антенн.
    c.rect(59, 12, 61, top_y, METAL)
    for y, w in ((22, 9), (30, 13), (38, 9)):
        c.rect(60 - w, y, 60 + w, y + 1, METAL)
        c.rect(60 - w, y - 2, 60 - w, y + 3, METAL)
        c.rect(60 + w, y - 2, 60 + w, y + 3, METAL)
    c.ellipse(60, 8, 4.5, 4.5, RED)
    # Тарелки: слева большая, справа поменьше, смотрят в стороны и вверх.
    for cx, cy, r, side in ((34, 92, 15, -1), (84, 128, 12, 1)):
        c.line(60 + side * 6, cy + 6, cx + side * 4, cy + 2, METAL, 3)
        c.ellipse(cx, cy, r * 0.62, r, WHITE)
        c.ellipse(cx - side * 2, cy, r * 0.36, r * 0.74, GREY)
        c.line(cx - side * 2, cy, cx - side * (r * 0.62 + 6), cy - 4, DARK, 2)
        c.ellipse(cx - side * (r * 0.62 + 6), cy - 4, 2, 2, RED)
    # Шкаф аппаратуры и кабель.
    c.rect(4, 208, 30, 239, GREY)
    c.rect(4, 208, 30, 210, WHITE)
    c.rect(26, 211, 30, 239, METAL)
    for y in range(216, 230, 4):
        c.rect(8, y, 22, y + 1, DARK)
    c.rect(9, 232, 12, 235, GOLD)
    c.rect(15, 232, 18, 235, RED)
    c.line(30, 222, 42, 232, DARK, 2)
    c.finish()
    c.rect(59, 6, 60, 7, WHITE)
    return c


def debris():
    """Обломок бетона у дороги, 96×64: наклонная плита со светлым сколом и трещинами, остаток
    жёлто-чёрной разметки на грани, гнутые прутья ржавой арматуры, рядом кусок кирпичной кладки."""
    c = Canvas(96, 64)
    # Арматура за плитой.
    c.line(60, 16, 70, 3, BRASS, 3)
    c.line(70, 3, 81, 7, BRASS, 3)
    c.line(26, 24, 23, 7, BRASS, 3)
    c.line(23, 7, 12, 9, BRASS, 3)
    c.line(86, 40, 94, 36, BRASS, 3)
    # Плита: прямые сколы, плоская верхняя грань.
    c.poly([(8, 63), (5, 38), (16, 24), (44, 23), (52, 13), (76, 15), (88, 30), (92, 50), (86, 63)], GREY)
    c.poly([(11, 36), (19, 26), (45, 26), (53, 16), (74, 18), (83, 30), (48, 38)], WHITE)
    # Остаток разметки по нижней грани: косые жёлтые и чёрные полосы.
    for y in range(48, 58):
        for x in range(12, 84):
            if c.get(x, y) == GREY:
                c.set(x, y, GOLD if ((x + y) // 6) % 2 == 0 else DARK)
    c.line(48, 38, 43, 47, METAL, 1)
    c.line(66, 33, 72, 47, METAL, 1)
    c.line(72, 47, 80, 44, METAL, 1)
    c.line(24, 39, 20, 47, METAL, 1)
    c.line(30, 58, 36, 63, METAL, 1)
    for x, y in ((16, 42), (58, 42), (84, 40), (34, 44), (62, 60), (20, 60), (78, 59)):
        c.rect(x, y, x + 1, y, METAL)
    c.rect(26, 30, 31, 30, GREY)
    c.rect(58, 22, 64, 22, GREY)
    # Кусок кладки и крошка.
    c.poly([(0, 63), (1, 51), (15, 48), (20, 63)], TAN)
    c.line(1, 56, 17, 54, DARK, 1)
    c.line(9, 50, 9, 55, DARK, 1)
    c.line(5, 57, 5, 63, DARK, 1)
    c.line(14, 56, 15, 63, DARK, 1)
    c.poly([(84, 63), (88, 56), (95, 58), (95, 63)], GREY)
    c.finish()
    for x, y in ((66, 9), (17, 8), (24, 15)):
        c.set(x, y, TAN)
    return c


def hydrant():
    """Пожарный гидрант, 48×64: красный столбик с куполом и гайкой, два боковых патрубка и
    передний с жёлтыми крышками, цепочка, фланец на болтах."""
    c = Canvas(48, 64)
    # Фланец и основание.
    c.rect(8, 58, 39, 63, DARK)
    c.rect(10, 54, 37, 58, RED)
    for x in (12, 20, 27, 35):
        c.rect(x, 55, x + 1, 56, GOLD)
    # Столбик.
    c.rect(15, 22, 32, 54, RED)
    c.rect(17, 24, 18, 52, WHITE)
    c.rect(15, 48, 32, 49, DARK)
    # Купол, поясок и гайка.
    dome = Canvas(48, 64)
    dome.ellipse(23.5, 22, 11.5, 13, RED)
    for y in range(23, 64):
        for x in range(48):
            dome.px[y][x] = None
    c.paste(dome, 0, 0)
    c.rect(11, 21, 36, 24, RED)
    c.rect(11, 24, 36, 24, DARK)
    c.rect(19, 4, 28, 9, GOLD)
    c.rect(21, 1, 26, 4, GOLD)
    c.rect(19, 9, 28, 9, BRASS)
    c.line(19, 13, 22, 11, WHITE, 1)
    # Боковые патрубки с крышками.
    for side in (-1, 1):
        x0 = 15 if side < 0 else 32
        c.rect(min(x0, x0 + side * 7), 31, max(x0, x0 + side * 7), 41, RED)
        cap = x0 + side * 8
        c.rect(min(cap, cap + side * 3), 29, max(cap, cap + side * 3), 43, GOLD)
        c.rect(cap + side * 4, 34, cap + side * 4 + (1 if side > 0 else -1), 38, BRASS)
    # Передний патрубок: крышка с гайкой.
    c.ellipse(23.5, 36, 6.5, 6.5, DARK)
    c.ellipse(23.5, 36, 5.2, 5.2, GOLD)
    c.ellipse(23.5, 36, 2.6, 2.6, BRASS)
    # Цепочка от крышки к столбику.
    for i in range(7):
        a = i / 6.0
        c.set(24 + a * 7, 43 + math.sin(a * math.pi) * 4, METAL if i % 2 == 0 else GREY)
    return c.finish()


def sign(right):
    """Заграждение с указателем поворота, 96×112: на двух расставленных ногах синий щит с белой
    стрелкой в сторону поворота, ниже красно-белая косая балка, сверху две жёлтые мигалки."""
    c = Canvas(96, 112)
    d = 1 if right else -1
    # Ноги козлами и поперечина.
    for side in (-1, 1):
        c.line(48 + side * 22, 58, 48 + side * 34, 110, METAL, 4)
        c.rect(48 + side * 34 - 6, 108, 48 + side * 34 + 6, 111, DARK)
    c.rect(18, 98, 78, 100, DARK)
    # Балка: косые красные и белые полосы.
    c.rect(5, 70, 90, 85, WHITE)
    for y in range(71, 85):
        for x in range(6, 90):
            if ((x - d * (y - 70)) // 9) % 2 == 0:
                c.set(x, y, RED)
    c.rect(5, 70, 90, 70, GREY)
    c.rect(5, 85, 90, 85, DARK)
    # Щит со стрелкой.
    c.rect(4, 12, 91, 60, WHITE)
    c.rect(7, 15, 88, 57, SEA)
    c.rect(7, 54, 88, 57, NAVY)
    c.rect(min(48 - d * 32, 48 + d * 8), 30, max(48 - d * 32, 48 + d * 8), 41, WHITE)
    c.poly([(48 + d * 8, 20), (48 + d * 35, 35.5), (48 + d * 8, 51)], WHITE)
    # Мигалки на стойках.
    for x in (18, 77):
        c.rect(x - 1, 8, x + 2, 12, DARK)
        c.ellipse(x + 0.5, 5, 5, 5, BRASS)
        c.ellipse(x + 0.5, 5, 3.6, 3.6, GOLD)
    c.finish()
    for x in (18, 77):
        c.rect(x - 1, 3, x, 4, WHITE)
    for x, y in ((6, 14), (89, 14), (6, 58), (89, 58)):
        c.set(x, y, METAL)
    return c


def rooftop():
    """Водяной бак с будкой выхода на крышу, 192×160 (место хижины): дощатый бак в обручах под
    конической крышей на стальных ногах с раскосами, на боку эмблема героя, лесенка и труба;
    рядом кирпичная будка с дверью, лампой, листовкой «разыскивается» и вентилятором на крыше;
    всё на бетонном парапете."""
    c = Canvas(192, 160)
    # Парапет.
    c.rect(0, 150, 191, 159, GREY)
    c.rect(0, 150, 191, 151, WHITE)
    for x in range(14, 190, 30):
        c.rect(x, 152, x, 159, METAL)
    # Ноги бака: четыре стойки, пояс, раскосы крестом, сливная труба.
    for x in (26, 50, 82, 106):
        c.rect(x - 2, 96, x + 2, 150, METAL)
        c.rect(x - 2, 96, x - 1, 150, GREY)
    c.line(27, 104, 105, 146, DARK, 2)
    c.line(105, 104, 27, 146, DARK, 2)
    c.rect(22, 124, 110, 126, DARK)
    c.rect(64, 96, 69, 150, DARK)
    c.rect(18, 94, 114, 99, DARK)
    c.rect(18, 94, 114, 95, METAL)
    # Бак: доски, слева светлее от заката, обручи.
    c.rect(20, 38, 112, 94, TAN)
    c.rect(20, 38, 44, 94, BRASS)
    for x in range(28, 112, 8):
        c.rect(x, 39, x, 93, DARK if x > 44 else TAN)
    for y in (46, 64, 84):
        c.rect(19, y, 113, y + 2, METAL)
        c.rect(19, y, 113, y, GREY)
        c.rect(60, y - 1, 64, y + 3, DARK)
    # Эмблема героя на боку: синий круг со звездой.
    c.ellipse(72, 66, 15, 15, WHITE)
    c.ellipse(72, 66, 13, 13, SEA)
    c.poly(_star(72, 66.5, 11, 4.4), GOLD)
    # Крыша конусом, свет слева, шов и шпиль.
    c.poly([(12, 38), (66, 8), (120, 38)], DARK)
    c.poly([(12, 38), (66, 8), (60, 38)], METAL)
    c.line(66, 9, 40, 37, DARK, 1)
    c.line(66, 9, 92, 37, K, 1)
    c.rect(12, 37, 120, 39, DARK)
    c.rect(65, 2, 67, 9, METAL)
    c.ellipse(66, 2, 2.5, 2.5, GOLD)
    # Лесенка по правому боку бака до парапета.
    c.rect(96, 34, 97, 150, GREY)
    c.rect(106, 34, 107, 150, GREY)
    for y in range(38, 150, 7):
        c.rect(97, y, 106, y, GREY)
    # Будка: кирпич, скат крыши, дверь, лампа, листовка.
    c.rect(124, 88, 186, 150, TAN)
    for row, y in enumerate(range(94, 150, 6)):
        c.rect(124, y, 186, y, DARK)
        for x in range(128 + (row % 2) * 6, 186, 12):
            c.rect(x, y - 5, x, y - 1, DARK)
    c.rect(124, 88, 127, 150, BRASS)
    c.poly([(119, 90), (190, 74), (190, 81), (119, 95)], DARK)
    c.line(119, 90, 190, 74, METAL, 2)
    c.rect(134, 108, 158, 150, DARK)
    c.rect(136, 110, 156, 150, METAL)
    c.rect(136, 110, 138, 150, GREY)
    c.rect(141, 114, 151, 124, DARK)
    c.rect(142, 115, 150, 123, GOLD)
    c.rect(146, 115, 146, 123, BRASS)
    c.rect(152, 132, 154, 134, GOLD)
    c.rect(143, 100, 149, 102, DARK)
    c.rect(144, 103, 148, 105, GOLD)
    # Листовка: лицо злодея в зелёном шлеме, строчки.
    c.rect(164, 110, 181, 134, WHITE)
    c.ellipse(172.5, 118, 5, 5, VIOLET)
    c.rect(169, 118, 176, 119, K)
    c.rect(166, 126, 179, 127, K)
    c.rect(167, 130, 178, 130, DARK)
    # Вентилятор-грибок на скате.
    c.rect(168, 68, 174, 80, METAL)
    c.ellipse(171, 64, 10, 7, GREY)
    for x in (164, 168, 172, 176):
        c.line(x, 58, x + 2, 70, DARK, 1)
    c.rect(161, 69, 181, 70, DARK)
    c.finish()
    return c


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
        "palm": billboard(),
        "palm_b": mast(),
        "road_rock": debris(),
        "road_barrel": hydrant(),
        "sign_left": sign(False),
        "sign_right": sign(True),
        "road_hut": rooftop(),
    }
    for i, accent in enumerate((SEA, GOLD, RED, AQUA)):
        out["cart_%d" % i] = carts_strip(accent, True)
    return out


def horizon():
    """Горизонт в своей палитре `SUPERHEROES_SKY`."""
    return {"road_sky": sky(), "road_islands": islands(), "road_sea": sea()}


def road_palette():
    return {"road_colors": road_colors()}


def preview(path, keys=None):
    """Лист набора как в игре; `keys`: только эти ленты."""
    items = superheroes16.shaded(sprites())
    for key, canvas in horizon().items():
        items[key] = (canvas, SUPERHEROES_SKY)
    for key, canvas in road_palette().items():
        items[key] = (canvas, ROAD_COLORS)
    if keys:
        items = {k: items[k] for k in keys}
    superheroes16.save_sheet(path, items, scale=2, max_w=512)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        keys_ = None
        for arg in sys.argv[1:]:
            if arg.startswith("--keys="):
                keys_ = [k for k in arg.split("=", 1)[1].split(",") if k]
        preview(sys.argv[sys.argv.index("--preview") + 1], keys_)
