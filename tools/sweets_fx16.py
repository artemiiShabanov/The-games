#!/usr/bin/env python3
"""Мелкие эффекты «Сладостей» для 16/32 (#137): те же ленты, что у пиратов (`pixel_fx16.py`) и
космоса (`space_fx16.py`), рисунок свой: клубы сахарной пудры с крошками печенья из-под ног и
колёс, сахарная звёздочка с разлетающейся цветной посыпкой на подборе конфеты, мятный леденец
со спиралью, который раскалывается на дольки при ударе, розетка крема из кондитерского шприца
на выстреле, струя малинового сиропа с круглыми каплями вместо пламени нитро у эклера.

Ключи, кадры и опорные точки как у пиратов, их читает `scripts/demos/fx16.gd`:
`fx16_dust` 5 кадров 24×12 (облако лежит на нижней трети кадра и расходится в стороны),
`fx16_spark` и `fx16_star` по 4 кадра 24×24 с центром в (12, 12), `fx16_flash` 3 кадра 32×32 с
центром в (16, 16), `fx16_fire` 4 кадра 40×64: корень струи узкий вверху по центру (20, 2),
вниз к зрителю она расширяется и рвётся на языки разной длины (`racing_bit16.gd` рисует два
таких языка из-под короба и тянет их по высоте). Палитра та же по составу: обводка и четыре
рампы по четыре тона (`white`, `gold`, `dust`, `fire`), цвета взяты от `sweets16.PALETTE`.

    python3 tools/sweets_fx16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites16 import Canvas, strip  # noqa: E402
from pixel_brawl16 import Pal, ellipse, poly, capsule  # noqa: E402


def fx_pal():
    # Обводка: горький шоколад, как у всего набора.
    p = Pal(0x2B161E)
    # «white» здесь мята: карамель, мята, мятный крем, чистый блик.
    p.add("white", [0x3FA99C, 0x86DBBE, 0xD3F6E4, 0xFFFFFF])
    # Карамель и печенье: тень пряника, вафля, карамель, светлый блик.
    p.add("gold", [0x94522A, 0xD09038, 0xF8CF6A, 0xFFF3C4])
    # Сахарная пудра и крем: розоватая тень, тень белого, крем, глазурь.
    p.add("dust", [0xB88CA8, 0xD6BFCC, 0xF4E6E4, 0xFFF7EC])
    # Малина и сироп: малина, мармелад, розовая глазурь, бледно-розовый блик.
    p.add("fire", [0xB73A70, 0xE63545, 0xFF8EB6, 0xFFE0EA])
    return p


def _fill(c, pts, col):
    for (x, y) in pts:
        c.set(x, y, col)


def _cut(c, pts):
    for (x, y) in pts:
        if 0 <= x < c.w and 0 <= y < c.h:
            c.px[y][x] = None


def _diamond(cx, cy, rx, ry):
    return poly([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)])


def _at(a, r, cx=12.0, cy=12.0):
    return (cx + math.cos(a) * r, cy + math.sin(a) * r)


def _sprinkle(c, x, y, a, col, ln=1.4):
    """Палочка посыпки: короткий штрих под углом `a`."""
    dx, dy = math.cos(a) * ln, math.sin(a) * ln
    _fill(c, capsule((x - dx, y - dy), (x + dx, y + dy), 0.35, 0.35), col)


# --- Сахарная пудра ----------------------------------------------------------------------------

def dust(p):
    """Пудра из-под ног и колёс: два клуба с бугристым верхом, как сахарная вата, катятся от
    центра в стороны, между ними растёт просвет; из середины подпрыгивают две крошки печенья и
    розовая палочка посыпки. К концу клубы редеют шашечкой."""
    frames = []
    d, g, f = p["dust"], p["gold"], p["fire"]
    # Крошки: скорость по x и по y, цвет.
    crumbs = [(-1.1, 2.9, g[1]), (0.5, 3.3, f[2]), (1.3, 2.6, g[2])]
    for i in range(5):
        c = Canvas(24, 12)
        for side in (-1, 1):
            lead = 3.2 + i * 1.0
            # Клуб из трёх бугров: крупный впереди, средний над ним, малый хвостом к центру.
            bumps = [(lead, 9.0, 2.6 + i * 0.25), (lead - 1.6, 7.6 - i * 0.2, 2.0 + i * 0.2),
                     (lead - 3.4, 9.4, 1.7 + i * 0.1)]
            S = set()
            for k, (dx, cy, r) in enumerate(bumps):
                if dx < 0.6 and k == 2:
                    continue
                S |= ellipse(11.5 + side * dx, cy, r, r * 0.85)
            S = {(x, y) for (x, y) in S if 1 <= y <= 11}
            for (x, y) in S:
                # Свет сверху слева: верхняя кромка в глазури, низ и правый бок в розовой тени.
                if (x, y - 1) not in S or ((x - 1, y) not in S and (x, y - 2) not in S):
                    col = d[3]
                elif (x, y + 1) not in S:
                    col = d[0]
                elif (x + 1, y) not in S or (x, y + 2) not in S:
                    col = d[1]
                else:
                    col = d[2]
                c.set(x, y, col)
            # Складка между буграми: короткая тень под средним бугром.
            if i < 4:
                c.set(11.5 + side * (lead - 0.6), 8.6, d[1])
                c.set(11.5 + side * (lead - 1.6), 9.4, d[1])
        # Крошки летят по дуге и падают обратно.
        if i < 4:
            for vx, vy, col in crumbs:
                t = i + 0.6
                x = 11.5 + vx * t * 1.7
                y = 7.5 - vy * t + 0.7 * t * t
                if y < 0.5 or y > 10.5 or c.get(int(round(x)), int(round(y))) is not None:
                    continue
                c.set(x, y, col)
                if col == f[2]:
                    c.set(x + 1, y - 1, col)
        if i >= 3:
            for y in range(12):
                for x in range(24):
                    if c.get(x, y) is not None and ((x + y) % 2 or (i == 4 and y % 3 == 0)):
                        c.px[y][x] = None
        frames.append(c)
    return strip(frames)


# --- Посыпка -----------------------------------------------------------------------------------

def spark(p):
    """Искры подобранной конфеты: карамельная четырёхлучевая звёздочка вспыхивает и пустеет, от
    неё по кругу разлетаются палочки цветной посыпки: розовые, мятные, красные."""
    frames = []
    g, w, f, d = p["gold"], p["white"], p["fire"], p["dust"]
    tints = [f[2], w[2], f[1], g[2], d[3], f[2]]
    n = 6
    for i in range(4):
        c = Canvas(24, 24)
        if i == 0:
            _fill(c, _diamond(12, 12, 2.2, 6.6) | _diamond(12, 12, 6.6, 2.2), g[2])
            _fill(c, _diamond(12, 12, 3.2, 3.2), g[2])
            _fill(c, _diamond(12, 12, 1.0, 4.4) | _diamond(12, 12, 4.4, 1.0), g[3])
            _fill(c, ellipse(12, 12, 1.5, 1.5), w[3])
            for k in range(n):
                a = 0.5 + k * 2 * math.pi / n
                x, y = _at(a, 5.6)
                _sprinkle(c, x, y, a, tints[k], 0.8)
        elif i == 1:
            _fill(c, _diamond(12, 12, 2.4, 9.6) | _diamond(12, 12, 9.6, 2.4), g[1])
            _fill(c, _diamond(12, 12, 1.6, 8.2) | _diamond(12, 12, 8.2, 1.6), g[2])
            _fill(c, _diamond(12, 12, 3.6, 3.6), g[2])
            _fill(c, _diamond(12, 12, 0.6, 5.4) | _diamond(12, 12, 5.4, 0.6), g[3])
            _fill(c, ellipse(12, 12, 1.8, 1.8), w[3])
            for k in range(n):
                a = 0.5 + k * 2 * math.pi / n
                x, y = _at(a, 7.4)
                _sprinkle(c, x, y, a + 0.7, tints[k], 1.5)
        elif i == 2:
            # Звёздочка пустеет: остаются кончики лучей и точка в середине.
            for k in range(4):
                a = k * math.pi / 2
                x, y = _at(a, 9.0)
                _fill(c, _diamond(x, y, 1.6 if k % 2 else 0.8, 0.8 if k % 2 else 1.6), g[2])
                c.set(x, y, g[3])
            c.set(12, 12, g[3])
            for k in range(n):
                a = 0.5 + k * 2 * math.pi / n + 0.12
                x, y = _at(a, 9.4)
                _sprinkle(c, x, y, a + 1.5, tints[k], 1.5)
                x, y = _at(a + 0.5, 4.6)
                c.set(x, y, tints[(k + 2) % n])
        else:
            for k in range(n):
                a = 0.5 + k * 2 * math.pi / n + 0.25
                x, y = _at(a, 10.2)
                _sprinkle(c, x, y, a + 2.2, tints[k], 1.0)
                x, y = _at(a + 0.55, 6.6)
                c.set(x, y, g[2 + k % 2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Удар: мятный леденец ----------------------------------------------------------------------

def _mint_tone(x, y, twist, rot, n=4):
    """Долька леденца по точке: True это красная полоса спирали, False кремовая."""
    dx, dy = x - 12.0, y - 12.0
    a = math.atan2(dy, dx) + math.hypot(dx, dy) * twist + rot
    return int(math.floor(a / (math.pi / n))) % 2 == 0


def _wedge(a, r0, r1, half):
    """Осколок-долька: клин от радиуса `r0` до `r1` с угловой полушириной `half`."""
    pts = [_at(a, r0)]
    for s in range(5):
        b = a - half + 2 * half * s / 4
        pts.append(_at(b, r1))
    return poly(pts)


def star(p):
    """Звезда удара: круглый мятный леденец с красной спиралью и белым бликом, по краю короткие
    лучи; дальше он трескается на восемь долек с просветами, дольки разлетаются и крошатся."""
    frames = []
    d, f, w, g = p["dust"], p["fire"], p["white"], p["gold"]
    for i in range(4):
        c = Canvas(24, 24)
        rot = 0.3 + i * 0.4
        if i == 0:
            # Лучи удара из-под леденца.
            for k in range(8):
                a = rot + k * math.pi / 4 + math.pi / 8
                ln = 10.4 if k % 2 == 0 else 8.8
                _fill(c, poly([_at(a - 0.22, 6.0), _at(a, ln), _at(a + 0.22, 6.0)]), g[2])
                c.set(*_at(a, ln - 1.6), g[3])
            disc = ellipse(12, 12, 6.6, 6.6)
            for (x, y) in disc:
                red = _mint_tone(x, y, 0.24, rot)
                edge = (x + 1, y + 1) not in disc or (x + 1, y) not in disc or (x, y + 1) not in disc
                if red:
                    c.set(x, y, f[0] if edge else f[1])
                else:
                    c.set(x, y, d[1] if edge else d[3])
            # Блик глазури слева сверху и белая точка в центре спирали.
            c.set(9, 8, w[3])
            c.set(8, 9, w[3])
            c.set(10, 8, f[2] if _mint_tone(10, 8, 0.24, rot) else w[3])
            _fill(c, ellipse(12, 12, 1.2, 1.2), d[3])
        elif i == 1:
            # Трещины: восемь долек с просветами, середина выбита, в ней белая вспышка.
            for k in range(8):
                a = rot + k * math.pi / 4
                S = _wedge(a, 4.4, 10.0, 0.26)
                red = k % 2 == 0
                for (x, y) in S:
                    far = math.hypot(x - 12, y - 12) > 9.0
                    if red:
                        c.set(x, y, f[0] if far else f[1])
                    else:
                        c.set(x, y, d[1] if far else d[3])
                if red:
                    c.set(*_at(a - 0.12, 6.0), f[2])
            _fill(c, _diamond(12, 12, 1.6, 1.6), w[3])
        elif i == 2:
            # Дольки разлетелись: красные крупнее, кремовые мельче и ближе.
            for k in range(8):
                a = rot + k * math.pi / 4
                if k % 2 == 0:
                    S = _wedge(a, 7.4, 10.8, 0.2)
                    _fill(c, S, f[1])
                    c.set(*_at(a, 10.2), f[0])
                    c.set(*_at(a - 0.1, 8.8), f[2])
                else:
                    x, y = _at(a, 8.6)
                    _fill(c, ellipse(x, y, 1.1, 1.1), d[3])
                    c.set(x + 1, y + 1, d[1])
                c.set(*_at(a + math.pi / 8, 5.0), g[2] if k % 2 else w[2])
        else:
            for k in range(8):
                a = rot + k * math.pi / 4
                c.set(*_at(a, 10.6), f[1] if k % 2 == 0 else d[3])
                if k % 2 == 0:
                    c.set(*_at(a + 0.14, 9.6), f[2])
                else:
                    c.set(*_at(a + 0.4, 7.0), w[2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Вспышка: розетка крема --------------------------------------------------------------------

def _petals(c, n, r, pr, rot, ramp, cx=16.0, cy=16.0, long=1.25):
    """Венец лепестков крема: `n` овалов на радиусе `r`, каждый со своей тенью и бликом."""
    for k in range(n):
        a = rot + k * 2 * math.pi / n
        x, y = _at(a, r, cx, cy)
        S = ellipse(x, y, pr * long, pr, math.degrees(a))
        for (px, py) in S:
            if (px + 1, py + 1) not in S or (px, py + 1) not in S:
                col = ramp[0]
            elif (px - 1, py - 1) not in S or (px, py - 1) not in S:
                col = ramp[3]
            else:
                col = ramp[2]
            c.set(px, py, col)


def flash(p):
    """Вспышка выстрела: крем из кондитерского шприца. Розетка из восьми розовых лепестков с
    кремовой звёздочкой и мятным драже в середине; затем лепестки расходятся кольцом, середина
    пустеет до кремового ободка; под конец остаются капли и палочки посыпки."""
    frames = []
    d, f, w, g = p["dust"], p["fire"], p["white"], p["gold"]
    n = 8
    for i in range(3):
        c = Canvas(32, 32)
        rot = 0.2 + i * 0.3
        if i == 0:
            _petals(c, n, 6.4, 3.0, rot, f)
            # Кремовая звёздочка насадки поверх лепестков: лучи в ложбинки между ними.
            for k in range(n):
                a = rot + math.pi / n + k * 2 * math.pi / n
                _fill(c, poly([_at(a - 0.42, 3.0, 16, 16), _at(a, 7.4, 16, 16), _at(a + 0.42, 3.0, 16, 16)]), d[3])
                c.set(*_at(a + 0.2, 4.4, 16, 16), d[1])
            _fill(c, ellipse(16, 16, 4.2, 4.2), d[3])
            _fill(c, ellipse(16.6, 16.6, 3.4, 3.4) - ellipse(15.6, 15.6, 3.4, 3.4), d[1])
            # Драже в середине.
            _fill(c, ellipse(16, 16, 2.4, 2.4), w[0])
            _fill(c, ellipse(15.6, 15.6, 1.7, 1.7), w[1])
            c.set(15, 15, w[3])
        elif i == 1:
            _petals(c, n, 10.4, 3.2, rot, f, long=1.35)
            ring = ellipse(16, 16, 7.4, 7.4) - ellipse(16, 16, 5.0, 5.0)
            for (x, y) in ring:
                r = math.hypot(x - 16, y - 16)
                c.set(x, y, d[3] if r < 6.6 else d[1])
            for k in range(n):
                a = rot + math.pi / n + k * 2 * math.pi / n
                _fill(c, ellipse(*_at(a, 8.2, 16, 16), 1.5, 1.5), d[3])
                c.set(*_at(a, 12.8, 16, 16), g[2])
            _fill(c, ellipse(16, 16, 1.6, 1.6), w[1])
            c.set(16, 16, w[3])
        else:
            for k in range(n):
                a = rot + k * 2 * math.pi / n
                x, y = _at(a, 13.0, 16, 16)
                S = ellipse(x, y, 1.9, 1.9)
                _fill(c, S, f[2])
                c.set(x + 1, y + 1, f[0])
                c.set(x - 1, y - 1, f[3])
                b = a + math.pi / n
                x, y = _at(b, 9.6, 16, 16)
                _sprinkle(c, x, y, b + 1.2, (w[2], d[3], g[2], d[3])[k % 4], 1.3)
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Струя сиропа ------------------------------------------------------------------------------

_DRIPS = ((-9.4, 14.0, 2.6, 4.0), (0.0, 22.0, 2.8, 4.3), (9.4, 15.0, 2.6, 4.0))


def _drip(i, j):
    """Кончик потёка `j` в кадре `i`: длина гуляет по кадрам, потёк чуть качается."""
    ox, ln = _DRIPS[j][0], _DRIPS[j][1]
    ln += 6.0 * math.sin(j * 2.2 + i * math.pi / 2)
    sway = math.sin(i * math.pi / 2 + j * 1.3) * 0.9
    return (20 + ox + sway, 26.0 + ln)


def _jet(i, inset):
    """Силуэт струи в кадре `i`, утопленный внутрь на `inset` пикселей: раструб колоколом от
    узкого корня и три потёка с круглой каплей на конце."""
    S = set()
    # Раструб: сначала тонкая струйка, книзу расходится; край дрожит волной, что бежит вниз.
    for y in range(1, 30):
        t = min(1.0, (y - 1) / 24.0)
        hw = 2.2 + 11.4 * t ** 1.7 + math.sin(y * 0.6 - i * 1.57) * 0.9 * t
        hw -= inset
        if y > 25:
            hw -= (y - 25) * 2.4
        if hw < 0.4:
            continue
        for x in range(int(round(20 - hw)), int(round(20 + hw)) + 1):
            S.add((x, y))
    for j, (ox, _, rr, rb) in enumerate(_DRIPS):
        tip = _drip(i, j)
        rr -= inset
        rb -= inset
        if rr > 0.3:
            S |= capsule((20 + ox, 22.0), tip, rr + 0.8, rr)
        if rb > 0.3:
            S |= ellipse(tip[0], tip[1], rb, rb * 1.15)
    return {q for q in S if q[1] >= 1}


def fire(p):
    """Струя нитро: малиновый сироп из-под эклера. Корень узкий вверху по центру, вниз к зрителю
    раструб расходится колоколом и рвётся на три потёка разной длины с круглыми каплями на
    концах; потёки по кадрам вытягиваются и подбираются. Слои от малинового края через мармелад
    к розовой глазури, по оси вьётся кремовая лента, на каплях блики, под ними оторвавшиеся
    капли и палочки посыпки. 4 кадра 40×64."""
    W, H = 40, 64
    frames = []
    f, d, w, g = p["fire"], p["dust"], p["white"], p["gold"]
    for i in range(4):
        c = Canvas(W, H)
        rng = random.Random(50 + i)
        outer = _jet(i, 0.0)
        _fill(c, outer, f[0])
        _fill(c, _jet(i, 1.3), f[1])
        _fill(c, _jet(i, 2.6), f[2])
        # Кремовая лента по оси: от корня до начала среднего потёка, вьётся волной и сходит на нет.
        y1 = 33
        for y in range(2, y1):
            t = (y - 2) / float(y1 - 2)
            cx = 20 + math.sin(y * 0.5 - i * 1.57) * 2.6 * min(1.0, y / 10.0)
            hw = 0.4 + 2.0 * math.sin(min(1.0, t / 0.3) * math.pi / 2) * (1.0 - t ** 1.3)
            for x in range(int(round(cx - hw - 1)), int(round(cx + hw + 1)) + 1):
                if (x, y) in outer and c.get(x, y) != f[0]:
                    c.set(x, y, d[3] if abs(x - cx) <= hw else f[3])
        # Розовые складки раструба по сторонам от ленты.
        for side in (-1, 1):
            for y in range(12, 25):
                t = (y - 12) / 12.0
                x = 20 + side * (2.5 + 5.4 * t ** 1.4)
                if c.get(int(round(x)), y) == f[2]:
                    c.set(x, y, f[1] if y % 4 else f[3])
        for j in range(3):
            tx, ty = _drip(i, j)
            # Блик на капле слева сверху.
            c.set(tx - 1, ty - 1, f[3])
            c.set(tx - 2, ty - 1, d[3])
            c.set(tx - 1, ty - 2, d[3])
            # Оторвавшаяся капля под потёком, если есть место в кадре.
            if j % 2 == (i % 2) and ty + 12 < H - 2:
                dy = ty + 9.5 + rng.uniform(0, 2.5)
                _fill(c, ellipse(tx, dy, 1.4, 2.0), f[1])
                c.set(tx, dy - 1, f[3])
        # Палочки посыпки по сторонам от потёков.
        for k in range(4):
            x = (6, 33, 13, 27)[k] + rng.randint(-1, 1)
            y = rng.randint(40, H - 5)
            if any(c.get(x + dx, y + dy) is not None for dx in (-3, 0, 3) for dy in (-3, 0, 3)):
                continue
            _sprinkle(c, x, y, rng.uniform(0, math.pi), (w[2], g[2], d[3], f[3])[k], 1.0)
        c.outline(0)
        frames.append(c)
    return strip(frames)


def sprites_own():
    p = fx_pal()
    return {
        "fx16_dust": (dust(p), p.colors),
        "fx16_spark": (spark(p), p.colors),
        "fx16_star": (star(p), p.colors),
        "fx16_flash": (flash(p), p.colors),
        "fx16_fire": (fire(p), p.colors),
    }


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import sweets16
        sweets16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own())
