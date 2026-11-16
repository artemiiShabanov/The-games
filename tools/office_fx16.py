#!/usr/bin/env python3
"""Мелкие эффекты «Офиса» для 16/32 (#137): те же ленты, что у пиратов (`pixel_fx16.py`) и
космоса (`space_fx16.py`), рисунок свой: катышки ковролиновой пыли с кружками из дырокола
из-под ног и колёсиков, жёлтые стикеры веером на подобранном жетоне, рваный бумажный «бац» на
ударе, вспышка лампы копира крестом на выстреле степлера, струя кофе с пенкой вместо нитро.

Ключи, кадры и опорные точки как у пиратов, их читает `scripts/demos/fx16.gd`:
`fx16_dust` 5 кадров 24×12 (облако лежит на нижней трети кадра и расходится в стороны),
`fx16_spark` и `fx16_star` по 4 кадра 24×24 с центром в (12, 12), `fx16_flash` 3 кадра 32×32 с
центром в (16, 16), `fx16_fire` 4 кадра 40×64: корень струи узкий вверху по центру (20, 2),
вниз к зрителю она расширяется и рвётся на языки. Палитра та же по составу: обводка и четыре
рампы по четыре тона (`white`, `gold`, `dust`, `fire`), цвета взяты от `office16.PALETTE`.

    python3 tools/office_fx16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites16 import Canvas, strip  # noqa: E402
from pixel_brawl16 import Pal, ellipse, poly, capsule  # noqa: E402


def fx_pal():
    p = Pal(0x14141C)
    # Бумага: серый пластик в тени, тень листа, лист, блик под лампой.
    p.add("white", [0x7A8294, 0xB7BFCF, 0xF4F5F8, 0xFFFFFF])
    # «gold» и «fire» это роли в рисунках пиратов: искры подбора и огонь; здесь стикеры и кофе.
    p.add("gold", [0x8A5A22, 0xBB843A, 0xF6CD4C, 0xFFF4B0])
    # Пыль ковролина: серые катышки от тёмного низа к светлой шапке.
    p.add("dust", [0x4A4E5E, 0x7A8294, 0xA9B1C2, 0xD8DDE8])
    # Кофе: чёрный, с молоком, пенка крема, свет лампы копира.
    p.add("fire", [0x5A2E16, 0xB8642A, 0xF0B45A, 0xFFF4D8])
    return p


def _fill(c, pts, col):
    for (x, y) in pts:
        c.set(x, y, col)


def _clear(c, pts):
    for (x, y) in pts:
        if 0 <= x < c.w and 0 <= y < c.h:
            c.px[y][x] = None


def _at(cx, cy, a, r):
    return (cx + math.cos(a) * r, cy + math.sin(a) * r)


def _quad(cx, cy, a, hw, hh):
    """Прямоугольник листа со сторонами 2*hw на 2*hh, повёрнутый на угол `a`."""
    ca, sa = math.cos(a), math.sin(a)
    return poly([(cx + ca * sx * hw - sa * sy * hh, cy + sa * sx * hw + ca * sy * hh)
                 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


# --- Пыль --------------------------------------------------------------------------------------

def dust(p):
    """Пыль ковролина из-под ботинок и колёсиков: низкий валик из серых катышков расползается в
    стороны и оседает, над ним по дуге летят белые кружки из дырокола и один жёлтый."""
    frames = []
    d = p["dust"]
    rng = random.Random(11)
    lumps = [(-7.6, 3.0), (-2.6, 3.9), (3.0, 3.3), (7.8, 3.6)]
    dots = [(rng.uniform(-1.4, 1.4), rng.uniform(1.1, 1.7)) for _ in range(5)]
    for i in range(5):
        c = Canvas(24, 12)
        spread = 0.62 + i * 0.13
        for k, (dx, r) in enumerate(lumps):
            rr = r + i * 0.28
            ry = rr * (0.95 - i * 0.07)
            cx = 12 + dx * spread
            cy = 10.4 - ry
            S = ellipse(cx, cy, rr, ry)
            _fill(c, S, d[1])
            # Светлая шапка катышка: свет ламп сверху.
            _fill(c, ellipse(cx - 0.4, cy - ry * 0.38, rr * 0.72, ry * 0.55) & S, d[2])
            if i < 3 and k % 2 == 1:
                c.set(cx - 0.6, cy - ry * 0.6, d[3])
                c.set(cx + 0.4, cy - ry * 0.6, d[3])
        # Тёмная подошва валика на полу.
        for x in range(24):
            for y in range(11, 4, -1):
                if c.get(x, y) is not None:
                    if c.get(x, y + 1) is None:
                        c.px[y][x] = d[0]
                    break
        if i >= 3:
            for y in range(12):
                for x in range(24):
                    if c.get(x, y) is not None and ((x + y) % 2 or (i == 4 and x % 3 == 0)):
                        c.px[y][x] = None
        # Кружки из дырокола: взлетают и падают обратно.
        for k, (vx, vy) in enumerate(dots):
            t = i + 0.6
            x = 12 + vx * t * 2.6 + (k - 2) * 1.5
            y = 6.5 - vy * t * 1.9 + 0.42 * t * t
            if y > 10.5 or y < 0 or i == 4:
                continue
            c.set(x, y, p["gold"][2] if k == 2 else p["white"][2])
        frames.append(c)
    return strip(frames)


# --- Искры жетона ------------------------------------------------------------------------------

def _sticker(c, p, cx, cy, a, h):
    """Стикер: жёлтый квадрат, клейкая полоса темнее, уголок отогнут и светлый."""
    g = p["gold"]
    S = _quad(cx, cy, a, h, h)
    _fill(c, S, g[2])
    # Клейкая полоса у одной стороны и загнутый уголок у противоположной.
    ca, sa = math.cos(a), math.sin(a)
    _fill(c, _quad(cx + sa * h * 0.7, cy - ca * h * 0.7, a, h, h * 0.3) & S, g[1])
    kx, ky = cx + ca * h * 0.7 - sa * h * 0.7, cy + sa * h * 0.7 + ca * h * 0.7
    _fill(c, ellipse(kx, ky, h * 0.5, h * 0.5) & S, g[3])


def spark(p):
    """Искры жетона на кофе: из белого блика веером вылетают четыре жёлтых стикера, кружатся,
    мельчают и тают точками."""
    frames = []
    g, w = p["gold"], p["white"]
    for i in range(4):
        c = Canvas(24, 24)
        if i < 3:
            r = (6.6, 8.0, 9.4)[i]
            h = (2.5, 2.5, 1.5)[i]
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2 + i * 0.35
                x, y = _at(12, 12, a, r)
                _sticker(c, p, x, y, (k + i) % 2 * math.pi / 4, h)
            if i == 0:
                # Блик жетона: белый ромб с жёлтой каймой.
                _fill(c, poly([(12, 8.5), (14.4, 12), (12, 15.5), (9.6, 12)]), g[3])
                _fill(c, poly([(12, 10), (13.2, 12), (12, 14), (10.8, 12)]), w[3])
            elif i == 1:
                for k in range(4):
                    a = k * math.pi / 2
                    _fill(c, capsule(_at(12, 12, a, 1.5), _at(12, 12, a, 4.0), 0.4, 0.2), g[3])
            else:
                for k in range(4):
                    c.set(*_at(12, 12, k * math.pi / 2 + 0.2, 5.0), g[3])
        else:
            for k in range(8):
                a = 0.5 + k * math.pi / 4
                x, y = _at(12, 12, a, 10.2 if k % 2 == 0 else 6.8)
                c.set(x, y, g[2] if k % 2 == 0 else g[3])
                if k % 2 == 0:
                    c.set(x + 1, y, g[2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Удар --------------------------------------------------------------------------------------

def _torn(cx, cy, n, r_out, r_in, turn, seed):
    """Рваный бумажный «бац»: звезда с неровными зубцами разной длины."""
    rng = random.Random(seed)
    pts = []
    for k in range(n * 2):
        a = turn + k * math.pi / n + rng.uniform(-0.09, 0.09)
        r = (r_out * rng.uniform(0.82, 1.0)) if k % 2 == 0 else (r_in * rng.uniform(0.9, 1.15))
        pts.append(_at(cx, cy, a, r))
    return poly(pts)


def star(p):
    """Звезда удара: рваный лист бумаги зубцами наружу, как «бац» в комиксе; из-под него торчат
    жёлтые клинья стикеров. Потом середина выгорает, зубцы разлетаются клочками и кружками."""
    frames = []
    w, g = p["white"], p["gold"]
    for i in range(4):
        c = Canvas(24, 24)
        if i < 2:
            ro, ri = (11.0, 11.8)[i], (4.6, 5.6)[i]
            # Жёлтые клинья под листом, между белыми зубцами.
            _fill(c, _torn(12, 12, 6, ro - 0.6, ri - 1.6, 0.22 + math.pi / 6, 5), g[2])
            T = _torn(12, 12, 6, ro, ri, 0.22, 3)
            _fill(c, T, w[2])
            # Тень по нижней кромке листа и блик в середине.
            for (x, y) in T:
                if y > 12 and ((x, y + 1) not in T or (x + 1, y + 1) not in T):
                    c.set(x, y, w[1])
            if i == 0:
                _fill(c, _torn(12, 12, 6, 5.0, 2.8, 0.22, 3), w[3])
                # Строчки текста на листе: клочок документа.
                for k, ln in enumerate((5, 3)):
                    for x in range(ln):
                        c.set(9.5 + x + k, 11 + k * 2, w[0])
            else:
                _fill(c, ellipse(12, 12, 4.8, 4.8) - ellipse(12, 12, 3.4, 3.4), g[2])
                _clear(c, ellipse(12, 12, 3.4, 3.4))
        elif i == 2:
            # Клочки: прямоугольные обрывки на окружности, каждый повёрнут по-своему.
            for k in range(7):
                a = 0.22 + k * 2 * math.pi / 7
                x, y = _at(12, 12, a, 9.0 if k % 2 == 0 else 7.6)
                S = _quad(x, y, a * 2.0 + k, 1.9, 1.2)
                _fill(c, S, w[2])
                for (px, py) in S:
                    if (px, py + 1) not in S:
                        c.set(px, py, w[1])
                c.set(*_at(12, 12, a + 0.45, 5.0), g[2])
        else:
            for k in range(8):
                a = 0.4 + k * math.pi / 4
                x, y = _at(12, 12, a, 10.4 if k % 2 == 0 else 7.8)
                c.set(x, y, w[2] if k % 2 == 0 else g[2])
                if k % 4 == 0:
                    c.set(x, y + 1, w[1])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Вспышка -----------------------------------------------------------------------------------

def _beam(cx, cy, a, ln, w):
    """Луч: ромб от центра, широкий у ядра, острый на конце."""
    tip = _at(cx, cy, a, ln)
    back = _at(cx, cy, a, -w)
    side = (-math.sin(a) * w, math.cos(a) * w)
    return poly([(cx + side[0], cy + side[1]), tip, (cx - side[0], cy - side[1]), back])


def flash(p):
    """Вспышка выстрела степлера: лампа копира. Длинная горизонтальная полоса света и короткая
    вертикальная крестом, между ними короткие косые лучи; ядро белое, потом пустое кольцо, под
    конец остаются штрихи на концах лучей."""
    frames = []
    f = p["fire"]
    for i in range(3):
        c = Canvas(32, 32)
        lh, lv, ld = (12.5, 15.0, 15.0)[i], (9.0, 11.5, 12.5)[i], (6.0, 8.5, 9.5)[i]
        wd = (3.4, 2.6, 1.2)[i]
        if i < 2:
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2
                _fill(c, _beam(16, 16, a, ld, wd * 0.8), f[1])
            for tone, kk in ((1, 1.0), (2, 0.66)):
                for k in range(4):
                    a = k * math.pi / 2
                    ln = (lh if k % 2 == 0 else lv) * (1.0 if tone == 1 else 0.82)
                    _fill(c, _beam(16, 16, a, ln, wd * kk), f[tone])
            # Светлая жила вдоль полосы копира.
            for x in range(int(16 - lh * 0.6), int(16 + lh * 0.6) + 1):
                c.set(x, 16, f[3])
            for y in range(int(16 - lv * 0.5), int(16 + lv * 0.5) + 1):
                c.set(16, y, f[3])
            if i == 0:
                _fill(c, ellipse(16, 16, 4.6, 4.6), f[2])
                _fill(c, ellipse(16, 16, 3.4, 3.4), f[3])
                _fill(c, ellipse(15.6, 15.6, 1.8, 1.8), p["white"][3])
            else:
                _fill(c, ellipse(16, 16, 6.0, 6.0) - ellipse(16, 16, 4.2, 4.2), f[2])
                _fill(c, ellipse(16, 16, 4.2, 4.2) - ellipse(16, 16, 3.0, 3.0), f[3])
                _clear(c, ellipse(16, 16, 3.0, 3.0))
        else:
            # Угасание: от лучей остались концы, от ядра пунктир кольца.
            for k in range(4):
                a = k * math.pi / 2
                ln = lh if k % 2 == 0 else lv
                _fill(c, capsule(_at(16, 16, a, ln * 0.55), _at(16, 16, a, ln), 1.0, 0.3), f[1])
                _fill(c, capsule(_at(16, 16, a, ln * 0.6), _at(16, 16, a, ln * 0.8), 0.4, 0.2), f[2])
                d = math.pi / 4 + a
                _fill(c, capsule(_at(16, 16, d, ld * 0.7), _at(16, 16, d, ld), 0.6, 0.3), f[0])
            for (x, y) in ellipse(16, 16, 6.2, 6.2) - ellipse(16, 16, 4.8, 4.8):
                ang = math.atan2(y - 16, x - 16)
                if math.sin(ang * 4 + math.pi / 2) < 0.2:
                    c.set(x, y, f[1])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Струя -------------------------------------------------------------------------------------

def fire(p):
    """Нитро: струя кофе. Корень у трубы вверху узкий (20, 2), вниз к зрителю струя расходится
    волной и рвётся на языки с круглыми каплями на концах. Слои от чёрного кофе по краю к
    молочной жиле в середине, у корня блик; по кромке нижней части пузыри пенки, ниже летят
    отдельные капли. Волна и языки дрожат по кадрам. 4 кадра 40×64."""
    W, H = 40, 64
    frames = []
    f, w = p["fire"], p["white"]
    layers = [(1.0, 0), (0.8, 1), (0.3, 2)]
    for i in range(4):
        c = Canvas(W, H)
        rng = random.Random(70 + i)
        ph = i * 1.57
        for li, (k, tone) in enumerate(layers):
            S = set()
            L = 40.0 * (0.6 + 0.4 * k)
            for yy in range(int(L) + 1):
                t = yy / L
                mid = 20 + math.sin(yy * 0.2 + ph) * 2.2 * t
                half = (2.6 + 11.4 * t ** 0.75) * k + 0.5
                # Волна по кромке: струя идёт толчками.
                half += math.sin(yy * 0.55 - ph * 2) * 1.1 * t * k
                for x in range(int(math.floor(mid - half)), int(math.ceil(mid + half)) + 1):
                    S.add((x, 2 + yy))
            # Языки внизу: капля на конце каждого.
            base_y = 2 + L - 2
            for t in range(5):
                tx = 20 + (t - 2) * 5.6 * k + math.sin(ph + t * 1.7) * 1.5
                ln = (9.0 + 7.0 * math.sin(t * 2.1 + ph * 1.3 + 0.6)) * (0.4 + 0.6 * k)
                ex, ey = tx + (t - 2) * 1.1, base_y + ln
                S |= capsule((tx, base_y), (ex, ey), 2.6 * k + 0.4, 1.2 * k + 0.3)
                S |= ellipse(ex, ey, 2.4 * k + 0.5, 2.8 * k + 0.5)
            _fill(c, S, f[tone])
        # Блик у корня.
        _fill(c, capsule((20, 3), (20, 8), 0.6, 0.9), f[3])
        # Пузыри пенки по кромке струи: светлый шарик с тенью снизу.
        for k in range(7):
            yy = rng.uniform(16, 44)
            side = -1 if k % 2 == 0 else 1
            t = yy / 40.0
            bx = 20 + math.sin(yy * 0.2 + ph) * 2.2 * t + side * (2.6 + 11.4 * min(t, 1.0) ** 0.75) * rng.uniform(0.75, 1.0)
            r = rng.uniform(1.4, 2.6)
            B = ellipse(bx, 2 + yy, r, r)
            _fill(c, B, w[2])
            for (x, y) in B:
                if (x, y + 1) not in B:
                    c.set(x, y, w[1])
            c.set(bx - 0.5, 2 + yy - 0.5, w[3])
        # Оторвавшиеся капли: вытянуты вниз, с бликом.
        for k in range(4):
            tx = 20 + rng.uniform(-13, 13)
            ty = H - 13 + rng.uniform(0, 8)
            _fill(c, ellipse(tx, ty, 1.5, 2.3), f[1])
            c.set(tx - 0.4, ty - 0.8, f[2])
        for _ in range(4):
            c.set(rng.randint(5, 35), rng.randint(H - 16, H - 3), f[2])
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
        import office16
        office16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own())
