#!/usr/bin/env python3
"""Мелкие эффекты «Замков» для 16/32 (#137): те же пять лент и размеры, что у пиратов
(`pixel_fx16.py`) и космоса (`space_fx16.py`), но рисунок свой, а не перекраска: каменная крошка
с обломками из-под ног и колёс, золотой блик-крестик монеты, звон стали с острыми осколками,
вспышка арбалета или пушки с рваными языками и дымным кольцом, факельное пламя с углями.
Ключи, размеры кадров и число кадров те же: `fx16_dust` 5×24×12, `fx16_spark` 4×24×24,
`fx16_star` 4×24×24, `fx16_flash` 3×32×32, `fx16_fire` 4×40×64 (корень пламени вверху у трубы).
Основа сеттинга `castles16`, обводка и тёплые тона как у рыцаря и стражника."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites16 import Canvas, strip  # noqa: E402
from pixel_brawl16 import Pal, ellipse, poly, capsule, put  # noqa: E402


def fx_pal():
    p = Pal(0x1A1418)
    # «white» это сталь: холодный блик клинка и звон.
    p.add("white", [0xA8B4C4, 0xD0DAE6, 0xF0F4FA, 0xFFFFFF])
    # «gold» и «fire» это роли в рисунках пиратов: блеск монеты и огонь; здесь червонное золото
    # и факельное пламя.
    p.add("gold", [0x8A5A10, 0xD8A020, 0xF8D048, 0xFFF4B0])
    p.add("dust", [0x4E4840, 0x7C766A, 0xA8A194, 0xCFC8B8])
    p.add("fire", [0x7A1A0C, 0xD0400E, 0xF89424, 0xFFEA9C])
    return p


def dust(p):
    """Каменная крошка: серое облако и летящие обломки-квадратики, к концу редеет."""
    frames = []
    rng = random.Random(7)
    puffs = [(rng.uniform(-7, 7), rng.uniform(-1, 1), rng.uniform(2.0, 3.0)) for _ in range(3)]
    chips = [(rng.uniform(-8, 8), rng.uniform(1.0, 2.6), rng.randint(1, 2)) for _ in range(5)]
    for i in range(5):
        c = Canvas(24, 12)
        for dx, dy, r in puffs:
            rr = r + i * 0.6
            put(c, p, ellipse(12 + dx * (1 + i * 0.25), 8 + dy - i * 0.5, rr, rr * 0.7),
                p["dust"], soft=False, cast=False)
        for k, (dx, vy, s) in enumerate(chips):
            if i == 4 and k % 2:
                continue
            x = 12 + dx * (1 + i * 0.35)
            y = 8 - vy * i * 1.1 + 0.55 * i * i * 0.5
            for yy in range(s):
                for xx in range(s):
                    c.set(x + xx, y + yy, p["dust"][3 if (xx + yy) == 0 else 2])
        if i >= 3:
            for y in range(12):
                for x in range(24):
                    if c.get(x, y) is not None and ((x + y) % 2 or (i == 4 and x % 2)):
                        c.px[y][x] = None
        c.outline(0)
        frames.append(c)
    return strip(frames)


def _diamond(c, cx, cy, rx, ry, col):
    for (x, y) in poly([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]):
        c.set(x, y, col)


def spark(p):
    """Блик червонца: четырёхлучевой крестик-огранка, лучи вытягиваются и гаснут; рядом
    маленькие крестики."""
    frames = []
    g = p["gold"]
    for i in range(4):
        c = Canvas(24, 24)
        if i < 3:
            ln = 4 + i * 3
            th = 1.4 - i * 0.3
            _diamond(c, 12, 12, th, ln, g[2])
            _diamond(c, 12, 12, ln, th, g[2])
            _diamond(c, 12, 12, th * 0.8, ln * 0.5, g[3])
            _diamond(c, 12, 12, ln * 0.5, th * 0.8, g[3])
            if i >= 1:
                for (dx, dy) in ((-8, -6), (8, 5), (6, -8)):
                    for (ox, oy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                        c.set(12 + dx + ox, 12 + dy + oy, g[3] if (ox, oy) == (0, 0) else g[1])
        else:
            for (dx, dy) in ((-9, -2), (8, -6), (5, 8), (-5, 8)):
                c.set(12 + dx, 12 + dy, g[3])
                c.set(12 + dx, 12 + dy + 1, g[1])
        c.outline(0)
        frames.append(c)
    return strip(frames)


def _shards(c, cx, cy, n, r0, r1, w, col, phase):
    """Острые неровные осколки: длина через один разная, чтобы не было правильной звезды."""
    for k in range(n):
        a = phase + k * 2 * math.pi / n + (0.18 if k % 3 == 0 else 0.0)
        ln = r1 * (1.0 if k % 3 == 0 else 0.7 if k % 3 == 1 else 0.5)
        tip = (cx + math.cos(a) * ln, cy + math.sin(a) * ln)
        nx, ny = -math.sin(a) * w, math.cos(a) * w
        bx, by = cx + math.cos(a) * r0, cy + math.sin(a) * r0
        mx, my = bx + (tip[0] - bx) * 0.35, by + (tip[1] - by) * 0.35
        for (x, y) in poly([(bx + nx, by + ny), (mx + nx * 1.5, my + ny * 1.5), tip,
                            (mx - nx * 0.4, my - ny * 0.4), (bx - nx, by - ny)]):
            c.set(x, y, col)


def star(p):
    """Звон стали о сталь: белый крест-вспышка, косые осколки, дуга искр и угасание."""
    frames = []
    w, g = p["white"], p["gold"]
    for i in range(4):
        c = Canvas(24, 24)
        if i == 0:
            _shards(c, 12, 12, 7, 2, 9, 1.5, w[1], 0.2)
            _diamond(c, 12, 12, 1.4, 8, w[3])
            _diamond(c, 12, 12, 8, 1.4, w[3])
            for (x, y) in ellipse(12, 12, 2.6, 2.6):
                c.set(x, y, w[3])
        elif i == 1:
            _shards(c, 12, 12, 7, 4, 11, 1.2, g[2], 0.55)
            _diamond(c, 12, 12, 1.0, 6, w[2])
            _diamond(c, 12, 12, 6, 1.0, w[2])
            for (x, y) in ellipse(12, 12, 1.8, 1.8):
                c.set(x, y, w[3])
        elif i == 2:
            for k in range(9):
                a = -2.4 + k * 0.6
                r = 9 + (k % 2)
                for (ox, oy) in ((0, 0), (1, 0)) if k % 3 == 0 else ((0, 0),):
                    c.set(12 + math.cos(a) * r + ox, 12 + math.sin(a) * r, g[2] if k % 2 else w[2])
            for k in range(5):
                a = 0.7 + k * 1.1
                c.set(12 + math.cos(a) * 6, 12 + math.sin(a) * 6, g[1])
        else:
            for k in range(6):
                a = 0.3 + k * math.pi / 3
                c.set(12 + math.cos(a) * 10.5, 12 + math.sin(a) * 10.5, w[1])
        c.outline(0)
        frames.append(c)
    return strip(frames)


def flash(p):
    """Вспышка арбалета и пушки: рваные языки неровной длины, дымное кольцо и летящие угли,
    3 кадра 32×32."""
    frames = []
    f, d = p["fire"], p["dust"]
    for i in range(3):
        c = Canvas(32, 32)
        r = 6 + i * 3
        if i >= 1:
            rg = min(r + 3, 14.5)
            for (x, y) in ellipse(16, 16, rg, rg) - ellipse(16, 16, rg - 1.5, rg - 1.5):
                if (x + y + i) % 2 == 0:
                    c.set(x, y, d[1])
        _shards(c, 16, 16, 7, 2, min(r + 6, 14), 2.6 - i * 0.55, f[1], 0.1 + i * 0.25)
        _shards(c, 16, 16, 7, 1, r + 2, 1.5 - i * 0.3, f[2], 0.1 + i * 0.25 + 0.2)
        for (x, y) in ellipse(16, 16, max(4 - i, 1.5), max(4 - i, 1.5)):
            c.set(x, y, f[3])
        rng = random.Random(11 + i)
        for _ in range(4 + i):
            a = rng.uniform(0, 2 * math.pi)
            rr = min(r + 4 + rng.uniform(0, 3), 14.5)
            c.set(16 + math.cos(a) * rr, 16 + math.sin(a) * rr, f[2] if i < 2 else f[0])
        c.outline(0)
        frames.append(c)
    return strip(frames)


def fire(p):
    """Факельное пламя нитро (корень у трубы вверху узкий, вниз расширяется и рвётся на языки):
    слои от тёмно-красного края к светлому ядру, у корня дрожащий жар, ниже летят угли и клочья
    дыма. 4 кадра 40×64."""
    W, H = 40, 64
    frames = []
    layers = [(1.0, 0), (0.8, 1), (0.58, 2), (0.34, 3)]
    for i in range(4):
        c = Canvas(W, H)
        rng = random.Random(50 + i)
        for li, (k, tone) in enumerate(layers):
            half = 14.0 * k + 1.2
            lmax = (H - 10) * (0.52 + 0.48 * k)
            for xi in range(-int(half), int(half) + 1):
                dx = abs(xi) / half
                # Языки каплями: острые вершины, провалы между ними глубже, чем у ровной волны.
                wave = abs(math.sin(xi * 0.7 + i * 2.1 + li * 1.3))
                tongue = 0.5 + 0.5 * wave ** 0.7
                col = lmax * (1.0 - dx ** 1.5) * tongue
                for y in range(int(col)):
                    hw = 2.6 + (half - 2.6) * min(1.0, y / (lmax * 0.3))
                    if abs(xi) <= hw:
                        hot = tone == 3 and y < col * 0.55
                        c.set(20 + xi, y + 2, f_col(p, tone, hot))
        # Угли: пары пикселей, ниже дымные клочья.
        for k in range(5):
            ex = 20 + rng.uniform(-10, 10)
            ey = H - 18 + rng.uniform(0, 10)
            c.set(ex, ey, p["fire"][2])
            c.set(ex, ey + 1, p["fire"][1])
        for k in range(2):
            for (x, y) in ellipse(20 + rng.uniform(-8, 8), H - 5 + rng.uniform(-1, 1), 2.2, 1.4):
                c.set(x, y, p["dust"][0] if k else p["dust"][1])
        for _ in range(4):
            c.set(rng.randint(8, 32), rng.randint(H - 16, H - 4), p["fire"][3])
        c.outline(0)
        frames.append(c)
    return strip(frames)


def f_col(p, tone, hot):
    return p["white"][3] if hot else p["fire"][tone]


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
