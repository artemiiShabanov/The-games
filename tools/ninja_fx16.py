#!/usr/bin/env python3
"""Мелкие эффекты «Ниндзя» для 16/32 (#137): те же ленты, что у пиратов (`pixel_fx16.py`) и
космоса (`space_fx16.py`), рисунок свой: плоские облачка пыли с гравюры и кленовые листья из-под
ног, блик монеты с квадратным отверстием, удар в виде сюрикена и двух росчерков клинка, вспышка
хризантемой фейерверка, пламя с завитками на концах языков.

Ключи, кадры и опорные точки как у пиратов, их читает `scripts/demos/fx16.gd` (эффект ставится
центром кадра в точку мира): `fx16_dust` 5 кадров 24×12 (облако лежит на нижней трети кадра и
расходится в стороны), `fx16_spark` и `fx16_star` по 4 кадра 24×24 с центром в (12, 12),
`fx16_flash` 3 кадра 32×32 с центром в (16, 16), `fx16_fire` 4 кадра 40×64: корень пламени узкий
вверху по центру (20, 2), вниз к зрителю оно расширяется и рвётся на языки. Палитра та же по
составу: обводка и четыре рампы по четыре тона (`white`, `gold`, `dust`, `fire`), цвета взяты
от `ninja16.PALETTE`: сталь и обмотки, золото монеты, сумеречная дымка, красное шарфа и коралл
заката.

    python3 tools/ninja_fx16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites16 import Canvas, strip  # noqa: E402
from pixel_brawl16 import Pal, ellipse, poly, capsule  # noqa: E402


def fx_pal():
    p = Pal(0x121018)
    # Сталь клинка: камень, тень белого, белое обмоток, блик.
    p.add("white", [0x787A8A, 0xB7B4B2, 0xF3EEE2, 0xFFFFFF])
    # «gold» и «fire» это роли в рисунках пиратов: искры подбора и огонь. Здесь золото монеты
    # (бронза, золото, бледное золото горизонта) и красное шарфа с кораллом заката.
    p.add("gold", [0x7E4A22, 0xB2762E, 0xF4CB52, 0xFFF0B4])
    # Пыль каменной дорожки в сумерках: лиловая тень, камень, светлая дымка.
    p.add("dust", [0x4A4560, 0x7C7A92, 0xB4AEB8, 0xE6DED6])
    p.add("fire", [0x86202E, 0xD93632, 0xE97B52, 0xFBDC92])
    return p


def _fill(c, pts, col):
    for (x, y) in pts:
        c.set(x, y, col)


def _polar(cx, cy, a, r):
    return (cx + math.cos(a) * r, cy + math.sin(a) * r)


# --- Пыль --------------------------------------------------------------------------------------

def dust(p):
    """Пыль из-под таби и колёс: плоское облачко как на гравюре (ровный низ, три круглых горба)
    стелется по дорожке и расходится в стороны, из него взлетают два кленовых листа и кружатся;
    к концу облако редеет шашечкой."""
    frames = []
    d, f = p["dust"], p["fire"]
    # Горб: сдвиг по x, радиус.
    humps = [(-5.5, 2.5), (0.0, 3.3), (5.5, 2.7)]
    # Лист: сторона, скорость по x и вверх.
    leaves = [(-1, 1.5, 1.6), (1, 1.9, 1.25)]
    for i in range(5):
        c = Canvas(24, 12)
        spread = 1 + i * 0.17
        S = set()
        for dx, r in humps:
            rr = r + i * 0.38
            S |= ellipse(12 + dx * spread, 9.8 - rr * 0.9 - i * 0.15, rr, rr * 0.85)
        # Полоса-подошва связывает горбы: силуэт цельный, низ ровный.
        x0 = 12 - 5.5 * spread - 2
        x1 = 12 + 5.5 * spread + 2
        S |= {(x, y) for x in range(int(x0), int(x1) + 1) for y in (9, 10)}
        S = {(x, y) for (x, y) in S if 0 <= x < 24 and 0 <= y <= 10}
        _fill(c, S, d[2])
        # Светлые шапки горбов сверху слева и блик.
        for dx, r in humps:
            rr = r + i * 0.38
            cx, cy = 12 + dx * spread, 9.8 - rr * 0.9 - i * 0.15
            _fill(c, ellipse(cx - 0.6, cy - rr * 0.3, rr * 0.75, rr * 0.6) & S, d[3])
        # Низ темнеет в два шага: строка тени и тёмная подошва под ней.
        for (x, y) in S:
            if (x, y + 1) not in S:
                c.px[y][x] = d[0] if y == 10 else d[1]
            elif y == 9:
                c.px[y][x] = d[1]
        if i >= 3:
            for y in range(12):
                for x in range(24):
                    if c.get(x, y) is not None and ((x + y) % 2 or (i == 4 and x % 4 == 0)):
                        c.px[y][x] = None
        # Кленовые листья: летят по дуге, по кадрам поворачиваются плашмя и ребром.
        for k, (side, vx, vy) in enumerate(leaves):
            t = i + 0.5
            x = int(round(12 + side * (2.5 + vx * t * 1.55)))
            y = int(round(6.5 - vy * t * 1.5 + 0.34 * t * t))
            if not (1 <= x <= 22 and 1 <= y <= 9):
                continue
            if (i + k) % 2 == 0:
                # Плашмя: три зубца вверх.
                c.set(x - 1, y, f[1])
                c.set(x, y, f[2])
                c.set(x + 1, y, f[1])
                c.set(x, y - 1, f[1])
            else:
                # Ребром: косая чёрточка с черешком.
                c.set(x, y, f[2])
                c.set(x + side, y - 1, f[1])
                c.set(x - side, y + 1, f[0])
        frames.append(c)
    return strip(frames)


# --- Блик монеты -------------------------------------------------------------------------------

def _square_ring(cx, cy, half, turn=0.0):
    """Квадратная рамка в один пиксель: стороны на расстоянии `half` от центра, повёрнута на
    `turn`."""
    pts = set()
    corners = [_polar(cx, cy, turn + math.pi / 4 + k * math.pi / 2, half * 1.4142) for k in range(4)]
    for k in range(4):
        pts |= capsule(corners[k], corners[(k + 1) % 4], 0.25, 0.25)
    return pts


def spark(p):
    """Блик подобранной монеты: монета с квадратным отверстием вспыхивает, обод уходит кольцом
    с четырьмя лучами по осям, отверстие остаётся рамкой в середине; под конец кольцо рвётся на
    дуги и рассыпается на четыре крошечные монетки."""
    frames = []
    g, w = p["gold"], p["white"]
    for i in range(4):
        c = Canvas(24, 24)
        if i == 0:
            disc = ellipse(11.5, 11.5, 5.2, 5.2)
            _fill(c, disc, g[2])
            # Тень обода снизу справа, блик сверху слева.
            _fill(c, disc - ellipse(10.7, 10.7, 5.0, 5.0), g[1])
            _fill(c, (ellipse(11.5, 11.5, 4.0, 4.0) - ellipse(12.1, 12.1, 4.0, 4.0)), g[3])
            # Короткие лучи по осям: монета блеснула.
            for k in range(4):
                a = k * math.pi / 2
                _fill(c, capsule(_polar(11.5, 11.5, a, 6.5), _polar(11.5, 11.5, a, 8.5), 0.3, 0.2), w[3])
            # Квадратное отверстие: обводка зальёт его тёмным.
            for y in (10, 11, 12, 13):
                for x in (10, 11, 12, 13):
                    c.px[y][x] = None
            for (x, y) in ((9, 9), (14, 9), (9, 14), (14, 14)):
                c.set(x, y, g[1])
        elif i == 1:
            ring = ellipse(11.5, 11.5, 7.6, 7.6) - ellipse(11.5, 11.5, 5.6, 5.6)
            _fill(c, ring, g[2])
            _fill(c, ring - ellipse(11.0, 11.0, 7.2, 7.2), g[1])
            _fill(c, ring & (ellipse(11.5, 11.5, 6.6, 6.6) - ellipse(12.2, 12.2, 6.6, 6.6)), g[3])
            for k in range(4):
                a = k * math.pi / 2
                _fill(c, capsule(_polar(11.5, 11.5, a, 8.6), _polar(11.5, 11.5, a, 11.2), 0.55, 0.2), g[3])
            # Отверстие стало светлой рамкой.
            _fill(c, _square_ring(11.5, 11.5, 2.5), w[3])
        elif i == 2:
            ring = ellipse(11.5, 11.5, 9.6, 9.6) - ellipse(11.5, 11.5, 8.3, 8.3)
            # Кольцо рвётся на четыре дуги: разрывы на осях.
            arcs = {(x, y) for (x, y) in ring if min(abs(x - 11.5), abs(y - 11.5)) > 2.6}
            _fill(c, arcs, g[2])
            _fill(c, arcs - ellipse(11.0, 11.0, 9.3, 9.3), g[1])
            for k in range(4):
                a = k * math.pi / 2
                q = _polar(11.5, 11.5, a, 10.6)
                c.set(q[0], q[1], g[3])
            # Рамка отверстия повернулась ромбом и гаснет.
            _fill(c, _square_ring(11.5, 11.5, 2.4, math.pi / 4), g[2])
        else:
            # Четыре крошечные монетки с отверстием по диагоналям и блёстки по осям.
            for sx in (-1, 1):
                for sy in (-1, 1):
                    cx, cy = 12 + sx * 7 - (sx > 0), 12 + sy * 7 - (sy > 0)
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            if dx or dy:
                                c.set(cx + dx, cy + dy, g[3] if dx + dy < 0 else g[2])
            for k in range(4):
                a = k * math.pi / 2
                q = _polar(11.5, 11.5, a, 10.4)
                c.set(q[0], q[1], g[3])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Удар --------------------------------------------------------------------------------------

def _shuriken(cx, cy, r_in, r_tip, turn):
    """Сюрикен: четыре лезвия вертушкой (остриё уведено по ходу вращения) вокруг ступицы."""
    pts = ellipse(cx, cy, r_in * 0.8, r_in * 0.8)
    for k in range(4):
        a = turn + k * math.pi / 2
        pts |= poly([_polar(cx, cy, a - 0.95, r_in), _polar(cx, cy, a + 0.30, r_tip),
                     _polar(cx, cy, a + 0.80, r_in * 0.9)])
    return pts


def _slash(cx, cy, r, a0, a1, thick):
    """Росчерк клинка: дуга, толстая в середине и сходящая в волос к концам."""
    pts = set()
    n = 26
    for s in range(n + 1):
        t = s / n
        a = a0 + (a1 - a0) * t
        w = thick * math.sin(t * math.pi) ** 0.8
        q = _polar(cx, cy, a, r - w * 0.5)
        pts |= ellipse(q[0], q[1], max(w, 0.3), max(w, 0.3))
    return pts


def star(p):
    """Звезда удара: сюрикен. Стальная вертушка с белыми кромками и золотыми брызгами между
    лезвий; дальше она проворачивается и растёт, ступица пустеет; потом два встречных росчерка
    клинка и редкие искры на их концах."""
    frames = []
    w, g = p["white"], p["gold"]
    for i in range(4):
        c = Canvas(24, 24)
        if i < 2:
            turn = 0.25 + i * 0.6
            r_in = (2.7, 4.2)[i]
            r_tip = (9.2, 11.0)[i]
            # Брызги между лезвиями.
            for k in range(4):
                a = turn + math.pi / 4 + k * math.pi / 2 - 0.25
                _fill(c, capsule(_polar(12, 12, a, r_in + 0.5), _polar(12, 12, a, (7.0, 9.6)[i]), 0.8, 0.2),
                      g[2 if k % 2 else 3])
            S = _shuriken(12, 12, r_in, r_tip, turn)
            _fill(c, S, w[2])
            # Тёмная спинка лезвия и белая режущая кромка.
            for k in range(4):
                a = turn + k * math.pi / 2
                back = poly([_polar(12, 12, a + 0.30, r_tip), _polar(12, 12, a + 0.80, r_in * 0.9),
                             _polar(12, 12, a + 0.25, r_in * 0.7)])
                _fill(c, back & S, w[1])
                _fill(c, capsule(_polar(12, 12, a - 0.80, r_in), _polar(12, 12, a + 0.30, r_tip - 0.6), 0.3, 0.2) & S,
                      w[3])
            if i == 0:
                _fill(c, ellipse(12, 12, 1.7, 1.7), g[2])
                c.set(12, 12, 0)
            else:
                # Ступица пустеет: золотое кольцо и дыра.
                _fill(c, ellipse(12, 12, 3.4, 3.4), g[2])
                for (x, y) in ellipse(12, 12, 1.9, 1.9):
                    c.px[y][x] = None
        elif i == 2:
            # Два встречных росчерка клинка.
            for k, a0 in enumerate((math.radians(205), math.radians(25))):
                S = _slash(12, 12, 10.2, a0, a0 + math.radians(118), 1.25)
                _fill(c, S, w[2])
                _fill(c, _slash(12, 12, 10.0, a0 + 0.35, a0 + math.radians(118) - 0.35, 0.5) & S, w[3])
            for k in range(4):
                a = 0.25 + 1.2 + k * math.pi / 2
                _fill(c, capsule(_polar(12, 12, a, 4.5), _polar(12, 12, a, 6.5), 0.5, 0.2), g[2 + k % 2])
        else:
            # Концы росчерков и искры.
            for a0 in (math.radians(205), math.radians(25)):
                for da in (10, 45, 75, 108):
                    q = _polar(12, 12, a0 + math.radians(da), 10.4)
                    c.set(q[0], q[1], w[2] if da in (45, 75) else w[1])
            for k in range(4):
                q = _polar(12, 12, 0.25 + 1.2 + k * math.pi / 2, 7.5)
                c.set(q[0], q[1], g[2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Вспышка -----------------------------------------------------------------------------------

def flash(p):
    """Вспышка выстрела: хризантема фейерверка. Тугой бутон с короткими лепестками, потом
    двенадцать тонких струй разной длины с каплями света на концах, под конец струи гаснут с
    середины, капли провисают вниз."""
    frames = []
    f, w = p["fire"], p["white"]
    n = 12
    for i in range(3):
        c = Canvas(32, 32)
        turn = 0.13 + i * 0.09
        for j in range(n):
            a = turn + j * 2 * math.pi / n
            long_ = j % 2 == 0
            if i == 0:
                r1 = 8.6 if long_ else 6.6
                _fill(c, capsule(_polar(16, 16, a, 3.0), _polar(16, 16, a, r1), 1.5, 0.5), f[1])
                _fill(c, capsule(_polar(16, 16, a, 3.0), _polar(16, 16, a, r1 - 1.6), 0.8, 0.2), f[2])
            elif i == 1:
                r1 = 13.2 if long_ else 10.4
                _fill(c, capsule(_polar(16, 16, a, 4.5), _polar(16, 16, a, r1), 1.1, 0.4), f[1])
                _fill(c, capsule(_polar(16, 16, a, 4.5), _polar(16, 16, a, r1 - 3.0), 0.5, 0.2), f[2])
                # Капля света на конце струи.
                q = _polar(16, 16, a, r1)
                _fill(c, ellipse(q[0], q[1], 1.0, 1.0), f[3])
            else:
                r1 = 14.2 if long_ else 11.6
                # Капли провисают: чем дальше от верха, тем ниже.
                sag = 0.9 + 0.5 * math.sin(a)
                q0 = _polar(16, 16, a, r1 - 3.2)
                q1 = _polar(16, 16, a, r1)
                _fill(c, capsule((q0[0], q0[1] + sag * 0.4), (q1[0], q1[1] + sag), 0.5, 0.3), f[1])
                c.set(q1[0], q1[1] + sag, f[3])
                if long_:
                    q = _polar(16, 16, a + 0.26, 7.0)
                    c.set(q[0], q[1], f[2])
        if i == 0:
            _fill(c, ellipse(16, 16, 5.0, 5.0), f[2])
            _fill(c, ellipse(16, 16, 3.8, 3.8), f[3])
            _fill(c, ellipse(15.5, 15.5, 2.0, 2.0), w[3])
        elif i == 1:
            _fill(c, ellipse(16, 16, 5.4, 5.4) - ellipse(16, 16, 3.4, 3.4), f[3])
            _fill(c, ellipse(16, 16, 3.4, 3.4), f[2])
            for (x, y) in ellipse(16, 16, 1.6, 1.6):
                c.px[y][x] = None
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Пламя -------------------------------------------------------------------------------------

def _tongue(root, dx, length, r_mid, bend, curl, cut=1.0, fat=1.0, steps=40):
    """Язык пламени с гравюры: от корня вниз, брюхо на трети длины, на конце завиток в сторону
    `curl` (остриё загибается вбок и чуть назад). `cut` обрезает язык по длине, `fat` сужает:
    так внутренние слои ложатся строго внутрь внешних."""
    pts = set()
    for s in range(steps + 1):
        t = s / steps
        if t > cut:
            break
        x = root[0] + dx * t + math.sin(t * math.pi) * bend
        y = root[1] + length * t
        if t > 0.68:
            u = (t - 0.68) / 0.32
            x += curl * 5.5 * u * u
            y -= 7.0 * u * u * u
        if t < 0.36:
            r = r_mid * (0.30 + 0.70 * math.sin(t / 0.36 * math.pi / 2))
        else:
            r = r_mid * (1.0 - ((t - 0.36) / 0.64) ** 1.1) + 0.55
        # Обрезанный слой сходит в остриё, а не обрывается кругом.
        if cut < 1.0:
            r *= min(1.0, (cut - t) / 0.22 + 0.25)
        r = r * fat
        pts |= ellipse(x, y, max(r, 0.5), max(r * 1.2, 0.5))
    return pts


def fire(p):
    """Пламя нитро: огонь из фейерверочной трубы под повозкой со змеем. Корень узкий вверху по
    центру, вниз к зрителю три языка расходятся веером, концы закручены завитками в разные
    стороны и качаются по кадрам; слои от тёмно-красного края к бледному золоту у корня, в
    просветах между языками летят капли огня и искры-крестики. 4 кадра 40×64."""
    W, H = 40, 64
    frames = []
    f, w = p["fire"], p["white"]
    root = (20, 2)
    # Язык: смещение кончика по x, длина, толщина брюха, завиток, фаза качания.
    tongues = [(-8.5, 43.0, 5.6, -1.0, 0.0), (0.5, 55.0, 7.0, 1.0, 2.1), (8.5, 47.0, 5.8, 1.0, 4.0),
               (-2.0, 31.0, 4.6, -1.0, 1.0)]
    # Слой: доля длины, доля толщины, тон.
    layers = [(1.0, 1.0, 0), (0.86, 0.74, 1), (0.66, 0.50, 2), (0.42, 0.28, 3)]
    for i in range(4):
        c = Canvas(W, H)
        rng = random.Random(70 + i)
        ph = i * math.pi / 2
        for cut, fat, tone in layers:
            S = set()
            for dx, ln, r, curl, off in tongues:
                sway = math.sin(ph + off)
                S |= _tongue(root, dx + sway * 2.0, ln * (1 + 0.05 * math.cos(ph + off)), r, sway * 2.6,
                             curl, cut, fat)
            # Горловина у трубы: общий корень не уже трёх пикселей.
            S |= ellipse(20, 4, 1.6 + 2.6 * fat, 3.0)
            _fill(c, S, f[tone])
        # Белое ядро у самого корня.
        _fill(c, ellipse(20, 6, 1.5, 3.2), w[3])
        # Оторвавшиеся капли огня: острый хвост вверх, круглый низ.
        for k in range(3):
            tx = 20 + (k - 1) * 11 + rng.uniform(-2, 2)
            ty = H - 9 + rng.uniform(-3, 3) - (5 if k != 1 else 0)
            drop = ellipse(tx, ty, 1.6, 1.8) | poly([(tx - 1.2, ty), (tx + 0.4, ty - 5.0), (tx + 1.2, ty)])
            if all(c.get(x, y) is None for (x, y) in drop):
                _fill(c, drop, f[1])
                c.set(tx, ty, f[2])
                c.set(tx, ty + 1, f[3])
        # Искры-крестики по краям.
        for _ in range(5):
            x, y = rng.randint(5, 34), rng.randint(H - 30, H - 4)
            cross = [(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
            near = [(x + dx, y + dy) for dx in range(-2, 3) for dy in range(-2, 3)]
            if all(c.get(qx, qy) is None for (qx, qy) in near):
                _fill(c, cross, f[2])
                c.set(x, y, f[3])
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
        import ninja16
        ninja16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own())
