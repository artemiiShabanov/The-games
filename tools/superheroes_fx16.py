#!/usr/bin/env python3
"""Мелкие эффекты «Супергероев» для 16/32 (#137): те же ленты, что у пиратов (`pixel_fx16.py`) и
космоса (`space_fx16.py`), рисунок свой, комиксовый: бетонная крошка крыши с клубом «пуф» и
чёрточками скорости, вспышка значка пятиконечной звездой, зубчатая клякса удара «бац» с красным
кантом, энергетический разряд перчатки кольцом с молниями, форсажный факел машины героя
трезубцем с ромбами скачков уплотнения.

Ключи, кадры и опорные точки как у пиратов, их читает `scripts/demos/fx16.gd`:
`fx16_dust` 5 кадров 24×12 (облако лежит на нижней трети кадра и расходится в стороны),
`fx16_spark` и `fx16_star` по 4 кадра 24×24 с центром в (12, 12), `fx16_flash` 3 кадра 32×32 с
центром в (16, 16), `fx16_fire` 4 кадра 40×64: корень пламени узкий вверху по центру (20, 2),
вниз к зрителю оно расширяется и рвётся на языки. Палитра та же по составу: обводка и четыре
рампы по четыре тона (`white`, `gold`, `dust`, `fire`), цвета взяты от `superheroes16.PALETTE`:
бетон парапета, жёлтое плаща и значка, энергия от красного глаза робота через коралл заката
к жёлтому.

    python3 tools/superheroes_fx16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites16 import Canvas, strip  # noqa: E402
from pixel_brawl16 import Pal, ellipse, poly, capsule  # noqa: E402


def fx_pal():
    p = Pal(0x15111F)
    # Блик и белое ядро: от бетона к чистому белому.
    p.add("white", [0xB6B4C0, 0xD9D8E2, 0xF6F2EA, 0xFFFFFF])
    # Значок-звезда: тень жёлтого, латунь, жёлтое плаща, блик.
    p.add("gold", [0x8A5416, 0xCE861E, 0xFFD23A, 0xFFF6C0])
    # Бетонная пыль крыши: тёмный металл, дымка, бетон, светлый скол.
    p.add("dust", [0x38394E, 0x767C90, 0xB6B4C0, 0xE6E4EC])
    # Энергия: вишнёвый край, красный, коралл с жёлтым, кремовое ядро.
    p.add("fire", [0x8E1E3C, 0xE43A32, 0xFF9A3E, 0xFFEFA6])
    return p


def _fill(c, pts, col):
    for (x, y) in pts:
        c.set(x, y, col)


def _at(a, r, cx=12.0, cy=12.0):
    return (cx + math.cos(a) * r, cy + math.sin(a) * r)


def _star5(cx, cy, r_out, r_in, rot=0.0):
    """Пятиконечная звезда лучом вверх."""
    pts = []
    for k in range(10):
        a = -math.pi / 2.0 + rot + k * math.pi / 5.0
        pts.append(_at(a, r_out if k % 2 == 0 else r_in, cx, cy))
    return poly(pts)


def _burst(cx, cy, radii, r_in, rot=0.0, k=1.0):
    """Комиксовая клякса: зубцы разной длины `radii` вокруг центра, впадины на `r_in`."""
    n = len(radii)
    pts = []
    for j, r in enumerate(radii):
        a = rot + j * 2.0 * math.pi / n
        pts.append(_at(a, r * k, cx, cy))
        pts.append(_at(a + math.pi / n, r_in * k, cx, cy))
    return poly(pts)


# --- Пыль --------------------------------------------------------------------------------------

def dust(p):
    """Бетонная крошка из-под сапог и колёс: комиксовый «пуф» из круглых клубов в ряд, средний
    выше и подпрыгивает, крайние раскатываются в стороны; из середины вылетают угловатые
    осколки бетона, у земли чёрточки скорости. К концу клубы редеют шашечкой."""
    frames = []
    d = p["dust"]
    for i in range(5):
        c = Canvas(24, 12)
        spread = 1.0 + i * 0.42
        # Клубы: (сдвиг от центра, радиус); средний крупнее.
        puffs = [(-6.4 * spread, 2.0 + i * 0.2), (-3.4 * spread, 2.7 + i * 0.3), (0.0, 3.5 + i * 0.3),
                 (3.6 * spread, 2.6 + i * 0.3), (6.6 * spread, 1.9 + i * 0.2)]
        S = set()
        for dx, r in puffs:
            lift = 0.9 * i if dx == 0.0 else 0.0
            S |= ellipse(12 + dx, 10.6 - r * 0.9 - lift * 0.5, r, r * 0.9)
        S = {(x, y) for (x, y) in S if 0 <= x < 24 and 0 <= y <= 11}
        _fill(c, S, d[2])
        # Светлые шапки клубов сверху слева и тень снизу: мультяшная светотень в три тона.
        for dx, r in puffs:
            lift = 0.9 * i if dx == 0.0 else 0.0
            cy = 10.6 - r * 0.9 - lift * 0.5
            _fill(c, ellipse(12 + dx - 0.7, cy - r * 0.35, r * 0.6, r * 0.45) & S, d[3])
        for (x, y) in S:
            if (x, y + 1) not in S or y == 11:
                c.set(x, y, d[1])
        # Чёрточки скорости у земли по краям облака.
        if i < 4:
            for side in (-1, 1):
                x0 = 12 + side * (7.5 * spread + 1.5)
                for k in range(2):
                    xx = x0 + side * k
                    if 0 <= xx < 24:
                        c.set(xx, 10, d[1])
        # Осколки бетона: угловатые, летят по дуге, светлая грань сверху.
        if i < 4:
            t = i + 0.6
            for k, (vx, vy) in enumerate(((-1.5, 1.5), (1.2, 1.75), (0.3, 2.0))):
                x = 12 + vx * t * 1.9
                y = 7.0 - vy * t * 1.7 + 0.5 * t * t
                if y < 0.5 or y > 9.5:
                    continue
                c.set(x, y, d[3])
                c.set(x + 1, y, d[2])
                c.set(x + (0 if k % 2 else 1), y + 1, d[0])
        if i >= 3:
            for y in range(12):
                for x in range(24):
                    if c.get(x, y) is not None and ((x + y) % 2 or (i == 4 and y % 2 == 0)):
                        c.px[y][x] = None
        frames.append(c)
    return strip(frames)


# --- Вспышка значка ----------------------------------------------------------------------------

def spark(p):
    """Подобранный значок-звезда: плотная пятиконечная звезда с белой серединой, затем она
    раздувается в контур с маленькой звездой внутри, затем пять звёздочек разлетаются по лучам,
    под конец блёстки."""
    frames = []
    g, w = p["gold"], p["white"]
    for i in range(4):
        c = Canvas(24, 24)
        if i == 0:
            _fill(c, _star5(12, 12.5, 7.5, 3.4), g[2])
            _fill(c, _star5(12, 12.5, 7.5, 3.4) & poly([(12, 12.5), (24, 12.5), (24, 24), (12, 24)]), g[1])
            _fill(c, _star5(12, 12.5, 4.2, 2.0), g[3])
            _fill(c, ellipse(11.5, 12, 1.3, 1.3), w[3])
        elif i == 1:
            ring = _star5(12, 12.5, 10.8, 5.0) - _star5(12, 12.5, 7.4, 3.4)
            _fill(c, ring, g[2])
            _fill(c, ring & poly([(12, 13), (24, 13), (24, 24), (12, 24)]), g[1])
            _fill(c, _star5(12, 12.5, 3.6, 1.7), g[3])
            c.set(12, 12, w[3])
        elif i == 2:
            for k in range(5):
                a = -math.pi / 2.0 + k * 2.0 * math.pi / 5.0
                x, y = _at(a, 8.4, 12, 12.5)
                _fill(c, _star5(x, y, 2.9, 1.3), g[2])
                c.set(x, y, g[3])
            for k in range(5):
                a = -math.pi / 2.0 + (k + 0.5) * 2.0 * math.pi / 5.0
                c.set(*_at(a, 4.5, 12, 12.5), g[3])
        else:
            for k in range(5):
                a = -math.pi / 2.0 + k * 2.0 * math.pi / 5.0
                x, y = _at(a, 10.2, 12, 12.5)
                c.set(x, y, g[3])
                x, y = _at(a + math.pi / 5.0, 7.0, 12, 12.5)
                c.set(x, y, g[2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Удар --------------------------------------------------------------------------------------

# Зубцы кляксы «бац»: длины по кругу, нарочно неровно.
JAGS = [1.0, 0.72, 0.95, 0.66, 1.0, 0.78, 0.9, 0.68, 1.0, 0.74]


def star(p):
    """Звезда удара: комиксовая клякса. Зубчатое пятно с красным кантом, жёлтым полем и белым
    ядром; на втором кадре оно больше и пустое внутри, из впадин бьют чёрточки; потом зубцы
    летят отдельными клиньями и гаснут точками."""
    frames = []
    f, g, w = p["fire"], p["gold"], p["white"]
    for i in range(4):
        c = Canvas(24, 24)
        if i == 0:
            radii = [r * 9.6 for r in JAGS]
            _fill(c, _burst(12, 12, radii, 5.2, 0.15), f[1])
            _fill(c, _burst(12, 12, radii, 5.2, 0.15, 0.76), g[2])
            _fill(c, _burst(12, 12, radii, 5.2, 0.15, 0.48), g[3])
            _fill(c, ellipse(12, 12, 2.2, 2.2), w[3])
        elif i == 1:
            radii = [r * 11.4 for r in JAGS]
            S = _burst(12, 12, radii, 6.6, 0.15)
            _fill(c, S, f[1])
            _fill(c, _burst(12, 12, radii, 6.6, 0.15, 0.8), g[2])
            hole = _burst(12, 12, radii, 6.6, 0.15, 0.46)
            for (x, y) in hole:
                c.px[y][x] = None
            # Белый блик по кромке дыры сверху слева.
            for (x, y) in hole:
                for q in ((x - 1, y), (x, y - 1)):
                    if q not in hole and q in S:
                        c.set(q[0], q[1], g[3])
        elif i == 2:
            n = len(JAGS)
            for j, r in enumerate(JAGS):
                a = 0.15 + j * 2.0 * math.pi / n
                tip = _at(a, 7.0 + 4.4 * r)
                b0 = _at(a - 0.2, 6.2)
                b1 = _at(a + 0.2, 6.2)
                _fill(c, poly([b0, tip, b1]), f[1] if j % 2 else g[2])
                c.set(*_at(a, 7.4), g[3])
        else:
            n = len(JAGS)
            for j, r in enumerate(JAGS):
                a = 0.15 + j * 2.0 * math.pi / n
                c.set(*_at(a, 8.6 + 2.2 * r), g[2] if j % 2 == 0 else f[1])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Разряд ------------------------------------------------------------------------------------

def _bolt(cx, cy, a, r0, r1, amp, steps=3):
    """Молния зигзагом от r0 до r1 по направлению a."""
    S = set()
    prev = _at(a, r0, cx, cy)
    for k in range(1, steps + 1):
        r = r0 + (r1 - r0) * k / steps
        side = 0.0 if k == steps else (amp if k % 2 else -amp)
        x, y = _at(a, r, cx, cy)
        cur = (x - math.sin(a) * side, y + math.cos(a) * side)
        S |= capsule(prev, cur, 1.0 - 0.25 * k, 0.75 - 0.2 * k)
        prev = cur
    return S


BOLTS = (-100, -28, 35, 110, 178, 232)


def flash(p):
    """Вспышка выстрела: энергозаряд перчатки-бластера. Яркий шар с красной короной и шестью
    молниями-зигзагами; на втором кадре шар раскрывается в кольцо, молнии длиннее; на третьем
    кольцо рвётся на дуги, от молний остаются концы."""
    frames = []
    f, w = p["fire"], p["white"]
    for i in range(3):
        c = Canvas(32, 32)
        if i == 0:
            for deg in BOLTS:
                a = math.radians(deg)
                _fill(c, _bolt(16, 16, a, 4.0, 11.5, 1.8), f[2])
            _fill(c, ellipse(16, 16, 6.6, 6.6), f[1])
            _fill(c, ellipse(16, 16, 5.2, 5.2), f[2])
            _fill(c, ellipse(15.6, 15.6, 3.8, 3.8), f[3])
            _fill(c, ellipse(15.2, 15.2, 2.2, 2.2), w[3])
        elif i == 1:
            for deg in BOLTS:
                a = math.radians(deg + 8)
                _fill(c, _bolt(16, 16, a, 7.0, 14.6, 2.0), f[2])
                _fill(c, capsule(_at(a, 7.0, 16, 16), _at(a, 9.0, 16, 16), 0.5, 0.3), f[3])
            ring = ellipse(16, 16, 8.6, 8.6) - ellipse(16, 16, 5.4, 5.4)
            _fill(c, ring, f[2])
            _fill(c, ring - ellipse(16, 16, 7.6, 7.6), f[1])
            _fill(c, (ellipse(16, 16, 6.6, 6.6) - ellipse(16, 16, 5.4, 5.4)) & ring, f[3])
            _fill(c, ellipse(16, 16, 2.0, 2.0), f[3])
            c.set(16, 16, w[3])
        else:
            ring = ellipse(16, 16, 11.2, 11.2) - ellipse(16, 16, 9.4, 9.4)
            for (x, y) in ring:
                ang = math.degrees(math.atan2(y - 16, x - 16)) % 360.0
                # Три дуги с просветами.
                if (ang + 25.0) % 120.0 < 84.0:
                    c.set(x, y, f[1] if (x - 16) ** 2 + (y - 16) ** 2 > 106 else f[2])
            # Концы молний улетают через просветы, внутри гаснут искры.
            for k in range(3):
                a = math.radians(77.0 + k * 120.0)
                _fill(c, _bolt(16, 16, a, 9.5, 15.0, 1.6), f[2])
            for deg in BOLTS:
                c.set(*_at(math.radians(deg + 16), 5.5, 16, 16), f[3])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Форсаж ------------------------------------------------------------------------------------

def _tongues(x, i):
    """Длина факела в столбце x (0..1 от полной): три больших языка трезубцем, средний самый
    длинный; по кадрам языки дышат и качаются."""
    sway = (0.0, 1.0, 0.0, -1.0)[i]
    spec = ((20.0 + sway, 7.5, (1.0, 0.92, 1.0, 0.9)[i]),
            (10.0 - sway * 0.6, 6.4, (0.70, 0.80, 0.66, 0.76)[i]),
            (30.0 - sway * 0.6, 6.4, (0.78, 0.66, 0.74, 0.70)[i]))
    best = 0.0
    for cx, wd, ln in spec:
        dx = abs(x - cx) / wd
        if dx < 1.0:
            best = max(best, ln * (1.0 - dx ** 2.4))
    return best


def fire(p):
    """Пламя нитро: форсажный факел машины героя. Корень узкий вверху по центру, вниз к зрителю
    струя раскрывается колоколом и делится на три острых языка трезубцем; слои плоские,
    как в комиксе: вишнёвый край, красный, оранжевый, кремовое ядро; по оси цепочка белых ромбов
    скачков уплотнения бежит вниз, у кончиков крестики искр. 4 кадра 40×64."""
    W, H = 40, 64
    frames = []
    f, w = p["fire"], p["white"]
    layers = [(1.0, 0), (0.82, 1), (0.60, 2), (0.36, 3)]
    full = H - 5.0
    for i in range(4):
        c = Canvas(W, H)
        rng = random.Random(90 + i)
        for k, tone in layers:
            for y in range(2, H - 1):
                t = (y - 2) / full
                half = (1.4 + 1.6 * k) + 15.0 * k * min(t / 0.36, 1.0) ** 0.75
                for x in range(W):
                    if abs(x - 19.5) > half:
                        continue
                    # Внутренние слои: тот же трезубец, сжатый к оси и короче.
                    xs = 19.5 + (x - 19.5) / k
                    if (y - 2) <= full * (0.34 + 0.66 * k) * _tongues(xs, i):
                        c.set(x, y, f[tone])
        # Ромбы скачков уплотнения: три по оси, мельчают книзу и съезжают по кадрам.
        for n in range(3):
            cy = 7.0 + n * 8.5 + i * 2.1
            rx = 3.0 - n * 0.7
            ry = 3.6 - n * 0.6
            D = poly([(19.5, cy - ry), (19.5 + rx, cy), (19.5, cy + ry), (19.5 - rx, cy)])
            for (x, y) in D:
                if c.get(x, y) in (f[3], f[2]):
                    c.set(x, y, w[3])
        # Белый корень у самой трубы.
        _fill(c, ellipse(19.5, 3.5, 1.6, 1.8), w[3])
        # Искры крестиками возле кончиков языков.
        for n in range(3):
            sx = (6, 20, 33)[n] + rng.randint(-2, 2)
            sy = (50, 60, 52)[n] + rng.randint(-3, 1)
            if any(c.get(sx + dx, sy + dy) is not None for dx in (-2, 0, 2) for dy in (-2, 0, 2)):
                continue
            if (n + i) % 2 == 0:
                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    c.set(sx + dx, sy + dy, f[3] if (dx, dy) == (0, 0) else f[2])
            else:
                c.set(sx, sy, f[3])
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
        import superheroes16
        superheroes16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own())
