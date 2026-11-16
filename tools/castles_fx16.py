#!/usr/bin/env python3
"""Мелкие эффекты «Замков» для 16/32 (#137): те же ленты, что у пиратов (`pixel_fx16.py`) и
космоса (`space_fx16.py`), рисунок свой: дорожная пыль с комьями земли и соломой, геральдический
блик монеты с короной, звон стали о сталь, сноп искр с огнива, факельное пламя из-под повозки.

Ключи, кадры и опорные точки как у пиратов, их читает `scripts/demos/fx16.gd`:
`fx16_dust` 5 кадров 24×12 (облако лежит на нижней трети кадра и расходится в стороны),
`fx16_spark` и `fx16_star` по 4 кадра 24×24 с центром в (12, 12), `fx16_flash` 3 кадра 32×32 с
центром в (16, 16), `fx16_fire` 4 кадра 40×64: корень пламени узкий вверху по центру (20, 2),
вниз к зрителю оно расширяется и рвётся на языки. Палитра та же по составу: обводка и четыре
рампы по четыре тона (`white`, `gold`, `dust`, `fire`), цвета взяты от `castles16.PALETTE`.

    python3 tools/castles_fx16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites16 import Canvas, strip  # noqa: E402
from pixel_brawl16 import Pal, ellipse, poly, capsule  # noqa: E402


def fx_pal():
    p = Pal(0x15131A)
    # Сталь лат: от тёмного железа к блику.
    p.add("white", [0x7C8498, 0x9EA8BA, 0xE8ECF2, 0xFFFFFF])
    # Золото короны на монете и искры огнива.
    p.add("gold", [0x9C642C, 0xD89A30, 0xF4C84A, 0xFFF4B8])
    # Пыль просёлка: сырая земля, глина, сухая пыль, солома.
    p.add("dust", [0x5C4630, 0x8E7450, 0xBCA47C, 0xE2D4A8])
    # Факел: багровый край, красный табарда, рыжий, жёлтое ядро.
    p.add("fire", [0x94283A, 0xD2302C, 0xF08A2C, 0xFFE68A])
    return p


def _fill(c, pts, col):
    for (x, y) in pts:
        c.set(x, y, col)


def _diamond(cx, cy, rx, ry):
    """Ромб блика: острые концы по осям."""
    return poly([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)])


def _plus(c, x, y, col, arm=1):
    for k in range(-arm, arm + 1):
        c.set(x + k, y, col)
        c.set(x, y + k, col)


# --- Пыль --------------------------------------------------------------------------------------

def dust(p):
    """Пыль из-под сапог и колёс: три клуба стелются по земле и расходятся в стороны, из них
    летят комья земли и соломинки; к концу клубы редеют шашечкой."""
    frames = []
    rng = random.Random(11)
    puffs = [(-5.5, 0.0, 2.3), (-0.5, -0.6, 2.9), (5.0, 0.0, 2.5)]
    clods = [(rng.uniform(-1.0, 1.0), rng.uniform(0.9, 1.5)) for _ in range(4)]
    for i in range(5):
        c = Canvas(24, 12)
        spread = 1 + i * 0.16
        for k, (dx, dy, r) in enumerate(puffs):
            rr = r + i * 0.42
            ry = rr * 0.78
            # Клуб лежит на земле: низ на предпоследней строке кадра, растёт вверх.
            cy = 10.4 - ry + dy - i * 0.25
            S = ellipse(12 + dx * spread, cy, rr, ry)
            _fill(c, S, p["dust"][1])
            # Светлая шапка клуба сверху слева и блик.
            _fill(c, ellipse(12 + dx * spread - 0.7, cy - ry * 0.3, rr * 0.72, ry * 0.6) & S, p["dust"][2])
            if i < 3:
                c.set(12 + dx * spread - 1, cy - ry * 0.45, p["dust"][3])
        # Тёмный низ облака там, где оно лежит на дороге.
        for x in range(24):
            for y in range(11, 5, -1):
                if c.get(x, y) is not None:
                    if c.get(x, y + 1) is None:
                        c.px[y][x] = p["dust"][0]
                    break
        # Комья и соломинки: взлетают по дуге и падают.
        for k, (vx, vy) in enumerate(clods):
            t = i + 0.6
            x = 12 + vx * t * 2.6 + (k - 1.5) * 1.5
            y = 7.5 - vy * t * 1.9 + 0.42 * t * t
            if y > 10.5 or i == 4:
                continue
            if k:
                c.set(x, y, p["dust"][0])
            else:
                c.set(x, y, p["gold"][2])
                c.set(x + (1 if vx > 0 else -1), y - 1, p["gold"][2])
        if i >= 3:
            for y in range(12):
                for x in range(24):
                    if c.get(x, y) is not None and ((x + y) % 2 or (i == 4 and x % 4 == 0)):
                        c.px[y][x] = None
        frames.append(c)
    return strip(frames)


# --- Блик монеты -------------------------------------------------------------------------------

def spark(p):
    """Блик подобранной монеты: геральдическая четырёхлучевая звезда (длинные лучи по осям,
    короткие по диагоналям) вспыхивает, раскрывается в кольцо и рассыпается на мелкие крестики."""
    frames = []
    g = p["gold"]
    for i in range(4):
        c = Canvas(24, 24)
        if i < 3:
            long_r = (5.0, 8.5, 10.0)[i]
            wide = (1.6, 2.0, 1.3)[i]
            _fill(c, _diamond(12, 12, long_r, wide) | _diamond(12, 12, wide, long_r), g[2])
            d = long_r * 0.42
            for sx in (-1, 1):
                for sy in (-1, 1):
                    _fill(c, capsule((12, 12), (12 + sx * d, 12 + sy * d), 0.9, 0.2), g[1])
            # Светлая сердцевина лучей и ядро.
            _fill(c, _diamond(12, 12, long_r * 0.6, 0.6) | _diamond(12, 12, 0.6, long_r * 0.6), g[3])
            if i < 2:
                _fill(c, ellipse(12, 12, 2.4 - i * 0.6, 2.4 - i * 0.6), p["white"][3])
            else:
                # Раскрытие: середина пустеет, остаётся золотое кольцо на лучах.
                ring = ellipse(12, 12, 5.2, 5.2) - ellipse(12, 12, 3.8, 3.8)
                _fill(c, ring, g[2])
                for (x, y) in ellipse(12, 12, 3.0, 3.0):
                    c.px[y][x] = None
        else:
            for k, (dx, dy) in enumerate(((0, -9), (9, 0), (0, 9), (-9, 0))):
                _plus(c, 12 + dx, 12 + dy, g[2])
                c.set(12 + dx, 12 + dy, g[3])
            for sx in (-1, 1):
                for sy in (-1, 1):
                    c.set(12 + sx * 5, 12 + sy * 5, g[3])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Удар --------------------------------------------------------------------------------------

def star(p):
    """Звезда удара: сталь о сталь. Белое ядро и косой крест клинков, из стыка брызжут рыжие
    искры; дальше ядро гаснет, крест расходится, искры летят штрихами и тают точками."""
    frames = []
    w, g = p["white"], p["gold"]
    cross = [math.radians(a) for a in (38, 142, 218, 322)]
    spits = [math.radians(a) for a in (0, 72, 95, 180, 255, 285)]
    for i in range(4):
        c = Canvas(24, 24)
        if i < 2:
            r0, r1 = (1.0, 9.5) if i == 0 else (3.5, 11.0)
            # Искры под крестом.
            for k, a in enumerate(spits):
                ln = (6.5, 9.5)[i] * (0.8 + 0.2 * (k % 2))
                st = (2.0, 5.0)[i]
                _fill(c, capsule((12 + math.cos(a) * st, 12 + math.sin(a) * st),
                                 (12 + math.cos(a) * ln, 12 + math.sin(a) * ln), 0.9, 0.2), g[1 + (k % 2)])
            # Крест клинков: стальные клинья с белой осью.
            for a in cross:
                tip = (12 + math.cos(a) * r1, 12 + math.sin(a) * r1)
                base = (12 + math.cos(a) * r0, 12 + math.sin(a) * r0)
                side = (-math.sin(a) * 1.5, math.cos(a) * 1.5)
                _fill(c, poly([(base[0] + side[0], base[1] + side[1]), tip,
                               (base[0] - side[0], base[1] - side[1])]), w[1 if a > math.pi else 2])
                _fill(c, capsule(base, ((base[0] + tip[0]) / 2, (base[1] + tip[1]) / 2), 0.4, 0.2), w[3])
            if i == 0:
                _fill(c, ellipse(12, 12, 3.4, 3.4), g[3])
                _fill(c, ellipse(12, 12, 2.2, 2.2), w[3])
            else:
                _fill(c, ellipse(12, 12, 4.6, 4.6) - ellipse(12, 12, 3.2, 3.2), g[3])
        elif i == 2:
            # Разлёт: короткие штрихи по кругу, стальные по кресту и рыжие между ними.
            for a in cross:
                _fill(c, capsule((12 + math.cos(a) * 7, 12 + math.sin(a) * 7),
                                 (12 + math.cos(a) * 10.4, 12 + math.sin(a) * 10.4), 0.7, 0.2), w[2])
            for k, a in enumerate(spits):
                _fill(c, capsule((12 + math.cos(a) * 6.5, 12 + math.sin(a) * 6.5),
                                 (12 + math.cos(a) * 9, 12 + math.sin(a) * 9), 0.6, 0.2), g[1 + (k % 2)])
        else:
            for a in cross:
                c.set(12 + math.cos(a) * 10.5, 12 + math.sin(a) * 10.5, w[2])
            for k, a in enumerate(spits):
                c.set(12 + math.cos(a) * 9.5, 12 + math.sin(a) * 9.5 + 1, g[2 if k % 2 else 1])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Вспышка -----------------------------------------------------------------------------------

def _petal(cx, cy, a, r0, r1, w):
    """Лепесток огня: пузатая капля от `r0` к острию на `r1`."""
    ca, sa = math.cos(a), math.sin(a)
    mid = r0 + (r1 - r0) * 0.38
    return poly([(cx + ca * r0, cy + sa * r0),
                 (cx + ca * mid - sa * w, cy + sa * mid + ca * w),
                 (cx + ca * r1, cy + sa * r1),
                 (cx + ca * mid + sa * w, cy + sa * mid - ca * w)])


def flash(p):
    """Вспышка выстрела: сноп искр с огнива. Шесть пузатых лепестков огня вокруг жёлтого ядра,
    потом лепестки вытягиваются и отрываются, под конец остаётся рваное кольцо и угольки."""
    frames = []
    f = p["fire"]
    for i in range(3):
        c = Canvas(32, 32)
        n = 6
        turn = 0.52 + i * 0.26
        r0 = (1.0, 4.0, 9.5)[i]
        r1 = (10.5, 13.5, 14.0)[i]
        w = (3.6, 3.0, 2.1)[i]
        for tone, k in ((0, 1.0), (1, 0.84), (2, 0.62)):
            if i == 2 and tone == 2:
                continue
            for j in range(n):
                a = turn + j * 2 * math.pi / n
                ln = r1 * (1.0 if j % 2 == 0 else 0.88)
                _fill(c, _petal(16, 16, a, r0, r0 + (ln - r0) * k, w * k), f[tone + (1 if i == 2 else 0)])
        if i == 0:
            _fill(c, ellipse(16, 16, 5.6, 5.6), f[2])
            _fill(c, ellipse(16, 16, 4.2, 4.2), f[3])
            _fill(c, ellipse(15.4, 15.4, 2.2, 2.2), p["white"][3])
        elif i == 1:
            _fill(c, ellipse(16, 16, 6.4, 6.4) - ellipse(16, 16, 3.2, 3.2), f[3])
            _fill(c, ellipse(16, 16, 3.2, 3.2), f[2])
            # Угольки между лепестками.
            for j in range(n):
                a = turn + (j + 0.5) * 2 * math.pi / n
                c.set(16 + math.cos(a) * 10.5, 16 + math.sin(a) * 10.5, f[3])
        else:
            for j in range(n):
                a = turn + (j + 0.5) * 2 * math.pi / n
                _plus(c, int(round(16 + math.cos(a) * 7.5)), int(round(16 + math.sin(a) * 7.5)), f[2], 0)
                c.set(16 + math.cos(a) * 12.5, 16 + math.sin(a) * 12.5, f[3])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Пламя -------------------------------------------------------------------------------------

def _tongue(root, tip, r_mid, bend, steps=14):
    """Язык факельного пламени: цепочка кружков от корня к острию, пузатая на трети длины и
    изогнутая в сторону `bend`."""
    pts = set()
    for s in range(steps + 1):
        t = s / steps
        x = root[0] + (tip[0] - root[0]) * t + math.sin(t * math.pi) * bend
        y = root[1] + (tip[1] - root[1]) * t
        # Корень узкий, брюхо на трети, дальше плавно в остриё.
        r = r_mid * (0.35 + 0.65 * math.sin(min(t / 0.38, 1.0) * math.pi / 2)) if t < 0.38 \
            else r_mid * (1.0 - ((t - 0.38) / 0.62) ** 1.4) + 0.4
        pts |= ellipse(x, y, r, r * 1.25)
    return pts


def fire(p):
    """Пламя нитро: факельный огонь из-под короба повозки. Корень узкий вверху по центру, вниз
    к зрителю три языка разной длины расходятся веером и качаются по кадрам; слои от багрового
    края к жёлтому ядру у корня, от кончиков отрываются клочки огня и летят угольки.
    4 кадра 40×64."""
    W, H = 40, 64
    frames = []
    f = p["fire"]
    # Язык: смещение кончика по x, длина, толщина брюха, фаза качания.
    tongues = [(-10.0, 44.0, 6.0, 0.0), (0.0, 58.0, 7.5, 2.1), (10.0, 48.0, 6.0, 4.0), (-3.0, 34.0, 5.0, 1.0)]
    layers = [(1.0, 0), (0.80, 1), (0.58, 2), (0.34, 3)]
    for i in range(4):
        c = Canvas(W, H)
        rng = random.Random(50 + i)
        ph = i * math.pi / 2
        for k, tone in layers:
            S = set()
            for tx, ln, r, off in tongues:
                sway = math.sin(ph + off)
                tip = (20 + tx * (0.55 + 0.45 * k) + sway * 2.5, 2 + ln * (0.50 + 0.50 * k) * (1 + 0.06 * math.cos(ph + off)))
                S |= _tongue((20, 2), tip, r * k + 0.6, sway * 3.0 * k)
            # Горловина у трубы: общий корень не уже трёх пикселей.
            S |= ellipse(20, 4, 2.0 + 2.2 * k, 3.0)
            _fill(c, S, f[tone])
        # Белое ядро у самого корня.
        _fill(c, ellipse(20, 6, 1.6, 3.4), p["white"][3])
        # Оторвавшиеся клочки огня под языками.
        for k in range(3):
            tx = 20 + (k - 1) * 10 + rng.uniform(-2, 2)
            ty = H - 12 + rng.uniform(-3, 5) - (6 if k != 1 else 0)
            if c.get(int(tx), int(ty)) is None:
                _fill(c, ellipse(tx, ty, 1.5, 2.3), f[1])
                c.set(tx, ty - 1, f[2])
        # Угольки по краям.
        for _ in range(6):
            x, y = rng.randint(5, 34), rng.randint(H - 26, H - 3)
            if c.get(x, y) is None:
                c.set(x, y, f[3] if rng.random() < 0.5 else f[2])
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
        import castles16
        castles16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own())
