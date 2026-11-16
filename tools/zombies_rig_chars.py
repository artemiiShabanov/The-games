#!/usr/bin/env python3
"""Модели на скелете «Зомби» для «продвинутых» (#137, состав в `docs/specs/settings.md`):
выживший (слот `hero`), зомби-мясник (`captain`), зомби-ходок (`enemy`). Те же трое, что в
`zombies_mesh_chars.py`: облик и цвета оттуда и из основы 16/32 (`zombies16.PALETTE`), рисунок
плотнее и подробнее.

Тела строит тот же `rig_models.build_body`, что у пиратов и космоса: скелет из 17 костей, рост,
плечи и кисть `hand_r` под оружие прежние, ширина тел (`bulk`) как у космоса, поэтому позы и
крепления демок сходятся. Свои только толщина рук и ног, головы, навесные детали и рисунок
атласа. Раскладка атласа пиратская (`rig_models.regions`); голова из `build_body` вырезана
прозрачностью (её кусок атласа пустой), вместо неё своя: в бейсболке, заваленная на плечо,
лысая с тесаком. Мелкие свои куски лежат в свободном углу атласа под штаниной.

Пружинные кости на тех же местах, что у космоса: у выжившего `tail` это обрывки сигнальной ленты
на скатке рюкзака, у мясника `skirt` это подол фартука, у ходока `sash` это лохмотья рубахи у
пояса. У ходока в правой руке лопата могильщика на месте жезла пришельца.

    python3 tools/zombies_rig_chars.py --preview out.png
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_models as rm  # noqa: E402
import zombies_mesh_chars as zc  # noqa: E402

rgb, mul, mix = rm.rgb, rm.mul, rm.mix

# Цвета те же, что у low poly (они из палитры основы 16/32), и несколько своих тонов.
BLACK = zc.BLACK
JACKET, JACKET_D, JACKET_L = zc.JACKET, zc.JACKET_D, zc.JACKET_L
DENIM, DENIM_D, DENIM_L = zc.DENIM, zc.DENIM_D, zc.DENIM_L
BONE, BONE_D = zc.BONE, zc.BONE_D
RAG, RAG_D, RAG_L = zc.RAG, zc.RAG_D, zc.RAG_L
SKIN, SKIN_D = zc.SKIN, zc.SKIN_D
LABEL, LABEL_D = zc.LABEL, zc.LABEL_D
LEATHER, LEATHER_D, LEATHER_L = zc.LEATHER, zc.LEATHER_D, zc.LEATHER_L
ROT, ROT_D, ROT_L = zc.ROT, zc.ROT_D, zc.ROT_L
BLOOD, BLOOD_D = zc.BLOOD, zc.BLOOD_D
STEEL, STEEL_D, STEEL_L = zc.STEEL, zc.STEEL_D, zc.STEEL_L
RUBBER, RUBBER_D = zc.RUBBER, zc.RUBBER_D
SKIN_L = mix(SKIN, BONE, 0.45)
HAIR = mul(LEATHER_D, 0.82)
RUST = rgb("8A5A36")
TANK, TANK_D = rgb("5E6660"), rgb("3C423E")
SLACKS, SLACKS_D = rgb("3A3C44"), rgb("24262C")
GLOVE, GLOVE_L = rgb("C8B24A"), rgb("E4D070")
BLANKET, BLANKET_L = ROT_D, mul(ROT_D, 1.28)

# Кусок атласа под голову из `build_body`: он прозрачный, голова у каждого своя.
INNER = (60, 22, 4, 8)
# Свои мелкие куски в свободном углу под штаниной.
EXTRA_A = (16, 56, 10, 8)   # козырёк, клок волос
CROWN = (26, 56, 4, 4)      # макушка
EXTRA_B = (26, 60, 4, 4)    # торец скатки
EXTRA_C = (30, 56, 6, 8)    # верх и дно рюкзака


def regions(p):
    reg = rm.regions(p)
    reg["own_head"] = reg["head"]
    reg["head"] = p.region(*INNER)
    reg["crown"] = p.region(*INNER)
    reg["own_crown"] = p.region(*CROWN)
    p.cut(*INNER)
    return reg


BODY = lambda y: rm.blend(y, [("hips", 0.0, 0.97), ("spine", 1.07, 1.14), ("chest", 1.26, 1.435),
                              ("neck", 1.475, 1.495), ("head", 1.53, 9.0)])


def head_tube(r, reg, rings, top, lean=(0.0, 0.0)):
    """Своя голова вместо вырезанной: кольца `(y, rx, rz)` снизу вверх от шеи внутри ворота, перёд
    по центру куска головы, макушка на высоте `top`; `lean` заваливает голову вбок и вперёд."""
    full = [(y, rx, rz, lean[0] * max(0.0, y - 1.5), -0.005 + lean[1] * max(0.0, y - 1.5)) for y, rx, rz in rings]
    r.tube(full, 16, reg["own_head"], lambda y: rm.blend(y, [("neck", 0.0, 1.49), ("head", 1.53, 9.0)]),
           cap_top=reg["own_crown"], v_range=(rings[0][0], top))


def _hv(low, top):
    """Высота точки головы → строка куска головы (0 макушка, 20 низ шеи)."""
    return lambda y: (top - y) / (top - low) * 20.0


def roll_x(r, x0, x1, y, z, rad, n, region, cap, weights, segs=4):
    """Валик вдоль X (скатка одеяла): развёртка вдоль валика по ширине куска, вокруг по высоте."""
    u0, v0, u1, v1 = region
    rows = []
    for i in range(segs + 1):
        x = x0 + (x1 - x0) * i / segs
        # Валик перетянут ремнями: у ремней чуть тоньше.
        k = 1.0 - 0.07 * (1.0 if i in (1, segs - 1) else 0.0)
        rows.append([r.vert((x, y + rad * k * math.cos(2 * math.pi * j / n), z + rad * k * math.sin(2 * math.pi * j / n)),
                            (u0 + (u1 - u0) * i / segs, v0 + (v1 - v0) * j / n), weights) for j in range(n + 1)])
    for i in range(segs):
        for j in range(n):
            a, b, c, d = rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]
            mid = np.mean([r.verts[q] for q in (a, b, c, d)], axis=0)
            out = (0.0, mid[1] - y, mid[2] - z)
            r.tri(a, b, c, out)
            r.tri(a, c, d, out)
    c0, d0, c1, d1 = cap
    for row, x, out in ((rows[0], x0, (-1.0, 0.0, 0.0)), (rows[-1], x1, (1.0, 0.0, 0.0))):
        hub = r.vert((x, y, z), ((c0 + c1) / 2.0, (d0 + d1) / 2.0), weights)
        rim = [r.vert(r.verts[row[j]], (c0 + (c1 - c0) * (0.5 + 0.48 * math.cos(2 * math.pi * j / n)),
                                         d0 + (d1 - d0) * (0.5 + 0.48 * math.sin(2 * math.pi * j / n))), weights) for j in range(n)]
        for j in range(n):
            r.tri(hub, rim[j], rim[(j + 1) % n], out)


# --- Общие приёмы рисунка -----------------------------------------------------------------------

def _tint(p, x, y, w, h, color, fn):
    """Подмешать цвет по полю `fn(gx, gy)` 0..1: пропитка кровью, синяк, грязь."""
    ys, xs = p._slice(x, y, w, h)
    gx, gy = p._grid(x, y, w, h)
    t = np.clip(fn(gx, gy), 0.0, 1.0)[..., None]
    a = np.asarray(p.im, dtype=np.float32).copy()
    a[ys, xs] = a[ys, xs] * (1.0 - t) + np.array(color, dtype=np.float32) * t
    p.im = rm.Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    p.d = rm.ImageDraw.Draw(p.im)


def _blob(cx, cy, rx, ry):
    return lambda gx, gy: np.exp(-(((gx - cx) / rx) ** 2 + ((gy - cy) / ry) ** 2))


def _cut_poly(p, points):
    rm.ImageDraw.Draw(p.a).polygon([(px * p.k, py * p.k) for px, py in points], fill=0)


def _blood(p, x, y, w, h, count, size=1.0, drip=2.4):
    """Брызги крови: тёмная клякса, свежая середина, мелкие капли вокруг, потёк вниз."""
    for _ in range(count):
        cx, cy = x + p.rng.uniform(0.12, 0.88) * w, y + p.rng.uniform(0.1, 0.8) * h
        s = size * p.rng.uniform(0.55, 1.0)
        p.ellipse(cx, cy, s, s * 0.8, BLOOD_D, 122)
        p.ellipse(cx + s * 0.1, cy - s * 0.05, s * 0.62, s * 0.5, BLOOD)
        for _ in range(5):
            a, d = p.rng.uniform(0.0, 6.28), s * p.rng.uniform(1.1, 2.0)
            q = s * p.rng.uniform(0.12, 0.28)
            px, py = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.8
            if x + q < px < x + w - q and y + q < py < y + h - q:
                p.ellipse(px, py, q, q, BLOOD_D)
        end = min(cy + drip * p.rng.uniform(0.4, 1.0) * s, y + h - 0.1)
        if end > cy + s:
            lx = cx + p.rng.uniform(-0.3, 0.3) * s
            p.line([(lx, cy), (lx + 0.05, end)], BLOOD_D, 0.24 * s)
            p.ellipse(lx + 0.05, end, 0.17 * s, 0.22 * s, BLOOD)


def _ragged(p, x, y, w, color, lo, hi, step=1.0, height=None):
    """Рваный край ткани: клочья разной длины свисают вниз от линии `y`."""
    i = 0.0
    while i < w - 1e-6:
        s = min(step * p.rng.uniform(0.7, 1.3), w - i)
        d = p.rng.uniform(lo, hi)
        p.poly([(x + i, y - 0.15), (x + i + s, y - 0.15), (x + i + s * p.rng.uniform(0.5, 0.95), y + d * 0.55),
                (x + i + s * p.rng.uniform(0.15, 0.5), y + d)], color, height)
        i += s


def _rot_skin(p, x, y, w, h, base=ROT):
    """Мёртвая кожа: зелёная, с трупными пятнами, светлыми проплешинами и крапом."""
    p.rect(x, y, w, h, base, 128)
    p.grain(x, y, w, h, 0.07, 1.0, 8.0)
    p.uneven(x, y, w, h, 0.1, 2.6)
    p.stains(x, y, w, h, max(3, int(w * h / 50)), 1.2, 0.84)
    p.speckle(x, y, w, h, int(w * h / 6), mul(base, 0.76), 0.06)
    p.speckle(x, y, w, h, int(w * h / 14), ROT_L, 0.07)


def _veins(p, x, y, w, h, count, color):
    """Жилы под кожей: тонкие ветвистые линии сверху вниз."""
    for _ in range(count):
        vx, vy = x + p.rng.uniform(0.15, 0.85) * w, y + p.rng.uniform(0.0, 0.3) * h
        pts = [(vx, vy)]
        while pts[-1][1] < y + h * 0.92 and len(pts) < 6:
            pts.append((min(max(pts[-1][0] + p.rng.uniform(-0.7, 0.7), x + 0.2), x + w - 0.2), pts[-1][1] + p.rng.uniform(1.2, 2.6)))
        p.line(pts, color, 0.13, 134)


def _fingers(p, color, width=0.22):
    for fx in (5.2, 7.0, 8.8, 10.6):
        p.line([(fx, 45.4), (fx, 48)], color, width, 106)


# --- Выживший -----------------------------------------------------------------------------------

HERO_HEAD = (1.45, 1.79)


def paint_survivor():
    """Атлас выжившего: красная куртка на молнии с лямками рюкзака, лицо под синей бейсболкой с
    белой панелью и красным крестом, джинсы с потёртым коленом, белые кроссовки, кожаный рюкзак,
    скатка, козырёк, сигнальная лента."""
    p = rm.Paint(211)
    # Торс: куртка, ворот расстёгнут, под ним белая футболка; молния, лямки, карманы, резинка.
    p.rect(0, 0, 32, 22, JACKET, 128)
    p.weave(0, 0, 32, 18.6, 0.4, 0.035, 9.0)
    p.uneven(0, 0, 32, 18.6, 0.08, 3.0)
    p.rect(0, 0, 32, 1.7, JACKET_L, 150)
    p.fold([(0, 1.8), (32, 1.8)], 0.3, 0.7, 40)
    p.poly([(12.8, 0), (19.2, 0), (17.5, 4.3), (16, 5.6), (14.5, 4.3)], BONE, 120)
    p.poly([(13.7, 0), (18.3, 0), (16, 2.9)], SKIN, 114)
    p.line([(13.6, 0.1), (16, 3.1), (18.4, 0.1)], BONE_D, 0.3, 126)
    for sx in (-1.0, 1.0):
        # Отвороты ворота и их тень.
        p.poly([(16 + sx * 3.1, 0), (16 + sx * 4.9, 0), (16 + sx * 2.5, 5.2), (16 + sx * 0.5, 5.8)], JACKET_L, 152)
        p.line([(16 + sx * 4.9, 0.1), (16 + sx * 2.6, 5.2), (16 + sx * 0.5, 5.9)], JACKET_D, 0.22, 110)
        p.stitch([(16 + sx * 4.3, 0.3), (16 + sx * 2.3, 4.7)], mul(JACKET_L, 1.12), 0.08, 0.45)
    # Молния: тёмная планка, зубцы, жёлтый бегунок с язычком.
    p.rect(15.55, 5.7, 0.9, 11.0, JACKET_D, 112)
    p.stitch([(16, 5.9), (16, 16.6)], RAG_L, 0.2, 0.34)
    p.rect(15.5, 5.5, 1.0, 0.9, LABEL, 176)
    p.rect(15.8, 6.4, 0.4, 1.0, LABEL_D, 170)
    for sx in (-1.0, 1.0):
        x = 16 + sx * 6.2
        # Лямки рюкзака: кожа со строчкой, пряжка, петля.
        p.poly([(x - 0.9, 0), (x + 0.9, 0), (x + 0.9 + sx * 0.5, 16.6), (x - 0.9 + sx * 0.5, 16.6)], LEATHER, 158)
        p.line([(x - 0.9 * sx, 0.2), (x - 0.4 * sx, 16.4)], LEATHER_D, 0.2, 140)
        p.stitch([(x + 0.45 * sx, 0.4), (x + 0.95 * sx, 16.2)], LEATHER_L, 0.08, 0.5)
        p.rect(x - 1.1 + sx * 0.25, 8.0, 2.2, 1.3, LABEL_D, 178)
        p.rect(x - 0.6 + sx * 0.25, 8.3, 1.2, 0.7, LEATHER_D, 150)
        # Косой боковой карман с молнией, боковой шов.
        p.fold([(16 + sx * 2.6, 11.4), (16 + sx * 4.6, 15.6)], 0.4, 0.74, 40)
        p.stitch([(16 + sx * 2.2, 11.6), (16 + sx * 4.2, 15.8)], mul(JACKET_L, 1.1), 0.08, 0.4)
        p.fold([(16 + sx * 8.6, 2.4), (16 + sx * 8.4, 16.4)], 0.3, 0.84, 24)
        p.fold([(16 + sx * 9.2, 4.2), (16 + sx * 12.5, 4.9), (16 + sx * 16, 4.4)], 0.3, 0.82, 24)
    # Нашивка на груди: белый прямоугольник с красным крестом.
    p.rect(18.0, 6.6, 2.6, 2.2, BONE, 146)
    p.rect(19.05, 6.9, 0.5, 1.6, JACKET)
    p.rect(18.5, 7.45, 1.6, 0.5, JACKET)
    p.stitch([(18.0, 6.6), (20.6, 6.6), (20.6, 8.8), (18.0, 8.8), (18.0, 6.6)], BONE_D, 0.07, 0.4)
    p.wrinkles(0, 6, 32, 10, 12, 3.2, 0.35, 0.88, 22)
    p.stains(0, 9, 32, 8, 7, 1.3, 0.86)
    p.speckle(0, 3, 32, 14, 50, LEATHER_D, 0.07)
    # Резинка по низу, ремень с пряжкой, пояс джинсов со шлёвками.
    p.rect(0, 16.6, 32, 2.0, JACKET_D, 142)
    for i in range(46):
        p.line([(0.3 + i * 0.7, 16.8), (0.3 + i * 0.7, 18.5)], mul(JACKET_D, 0.78), 0.14, 112)
    p.fold([(0, 16.5), (32, 16.5)], 0.35, 0.66, 46)
    p.rect(0, 18.6, 32, 1.7, LEATHER_D, 152)
    p.stitch([(0, 18.85), (32, 18.85)], LEATHER, 0.08, 0.5)
    p.rect(14.8, 18.4, 2.4, 2.1, LABEL, 178)
    p.rect(15.4, 18.9, 1.2, 1.1, LEATHER_D, 150)
    p.rect(0, 20.3, 32, 1.7, DENIM, 128)
    p.twill(0, 20.3, 32, 1.7, 0.4, 0.07)
    for x in (5.5, 11.5, 20.5, 26.5):
        p.rect(x - 0.35, 18.5, 0.7, 2.4, DENIM_D, 146)
    p.shade_v(0, 1.8, 32, 15, 1.05, 0.9)
    p.shade_round(0, 0, 32, 22, 0.74)
    # Голова: бейсболка сверху, под ней волосы на висках и затылке, лицо в тени козырька.
    hv = _hv(*HERO_HEAD)
    cap = hv(1.672)
    p.rect(32, 0, 32, 20, SKIN, 128)
    p.grain(32, cap, 32, 20 - cap, 0.03, 1.0, 4.0)
    for x0 in (32.0, 55.6):
        p.rect(x0, cap - 0.2, 8.4, hv(1.565) - cap, HAIR, 136)
        _ragged(p, x0, hv(1.565) - 0.2, 8.4, HAIR, 0.5, 1.6, 0.7, 134)
        for i in range(16):
            sx_ = x0 + 0.3 + i * 0.5
            p.line([(sx_, cap), (sx_ + p.rng.uniform(-0.3, 0.3), hv(1.57))], mul(HAIR, p.rng.uniform(0.75, 1.5)), 0.1, 138)
    for sx in (-1.0, 1.0):
        # Бакенбарды и уши.
        p.poly([(48 + sx * 7.5, cap), (48 + sx * 6.7, cap), (48 + sx * 6.9, cap + 3.0), (48 + sx * 7.5, cap + 3.4)], HAIR, 134)
        p.ellipse(48 + sx * 8.3, hv(1.618), 0.95, 1.5, mul(SKIN, 0.94), 142)
        p.ellipse(48 + sx * 8.3, hv(1.618), 0.42, 0.9, SKIN_D, 120)
    # Бейсболка: синие клинья со швами, белая панель с красным крестом, кромка, застёжка сзади.
    p.rect(32, 0, 32, cap, DENIM, 142)
    p.weave(32, 0, 32, cap, 0.36, 0.05, 10.0)
    p.uneven(32, 0, 32, cap, 0.08, 2.4)
    for x in (37.3, 42.7, 53.3, 58.7):
        p.fold([(x, 0.2), (x, cap - 0.8)], 0.3, 0.74, 34)
        p.stitch([(x + 0.4, 0.4), (x + 0.4, cap - 0.9)], DENIM_L, 0.07, 0.4)
    p.poly([(43.4, cap - 0.75), (52.6, cap - 0.75), (51.5, 1.7), (44.5, 1.7)], BONE, 150)
    p.stitch([(43.7, cap - 1.0), (44.7, 1.9), (51.3, 1.9), (52.3, cap - 1.0)], BONE_D, 0.08, 0.4)
    p.rect(47.2, 2.5, 1.6, 3.4, JACKET, 156)
    p.rect(46.3, 3.4, 3.4, 1.6, JACKET, 156)
    p.rect(32, cap - 0.75, 32, 0.75, DENIM_D, 152)
    p.stitch([(32, cap - 0.4), (64, cap - 0.4)], DENIM_L, 0.07, 0.4)
    for x0 in (32.0, 64.0):
        p.ellipse(x0, cap - 0.6, 2.1, 1.9, HAIR, 120)
    p.rect(32, cap - 1.15, 2.2, 0.6, RAG_L, 160)
    p.rect(61.8, cap - 1.15, 2.2, 0.6, RAG_L, 160)
    p.stains(32, 0.5, 32, cap - 1.5, 5, 1.0, 0.86)
    p.shade_v(32, 0, 32, cap, 1.12, 0.92)
    p.fold([(32, cap + 0.1), (64, cap + 0.1)], 0.4, 0.58, 55)
    # Лицо: тень козырька на лбу, глаза, нос, рот, щетина, пластырь на скуле, ссадина.
    _tint(p, 40.5, cap, 15, 2.2, SKIN_D, lambda gx, gy: 0.5 * np.clip(1.0 - (gy - cap) / 2.0, 0, 1))
    ey = hv(1.632)
    for sx in (-1.0, 1.0):
        ex = 48 + sx * 2.9
        p.ellipse(ex, ey, 1.15, 0.7, rgb("F4EEE2"), 132)
        p.ellipse(ex + sx * 0.1, ey + 0.05, 0.52, 0.6, rgb("3C5A70"))
        p.ellipse(ex + sx * 0.1, ey + 0.05, 0.24, 0.3, BLACK)
        p.ellipse(ex + sx * 0.1 - 0.16, ey - 0.16, 0.13, 0.13, rgb("FFFFFF"))
        p.line([(ex - 1.35, ey - 1.05 + 0.25 * sx), (ex, ey - 1.3), (ex + 1.35, ey - 1.05 - 0.25 * sx)], HAIR, 0.44, 138)
        p.line([(ex - 1.2, ey - 0.7), (ex + 1.2, ey - 0.7)], SKIN_D, 0.18)
        p.line([(ex - 1.0, ey + 0.95), (ex + 0.9, ey + 1.05)], mul(SKIN, 0.86), 0.14)
        p.fold([(48 + sx * 1.9, hv(1.6)), (48 + sx * 2.5, hv(1.575))], 0.3, 0.88, 14)
    nose = hv(1.596)
    p.poly([(47.35, ey - 0.2), (48.65, ey - 0.2), (49.3, nose), (46.7, nose)], SKIN_L, 150)
    p.line([(46.9, nose + 0.1), (48, nose + 0.45), (49.1, nose + 0.1)], SKIN_D, 0.3, 112)
    mouth = hv(1.563)
    p.line([(46.1, mouth - 0.1), (48, mouth + 0.2), (49.9, mouth + 0.05)], rgb("8A4A3C"), 0.42, 112)
    p.line([(46.7, mouth + 0.75), (49.3, mouth + 0.75)], mul(SKIN, 0.9), 0.3)
    gx, gy = p._grid(40.5, nose, 15, 6.4)
    side = np.clip(np.abs((gx - 48) / 7.5), 0, 1)
    jaw = rm._smooth_np(np.clip((gy - nose) / 3.2, 0, 1)) * (0.55 + 0.45 * side) * (1.0 - side ** 6)
    p._apply(40.5, nose, 15, 6.4, 1.0 - 0.24 * jaw)
    p.speckle(42, nose + 0.6, 12, 5.0, 170, mul(HAIR, 1.3), 0.05)
    p.poly([(51.2, nose - 0.9), (53.4, nose - 0.4), (53.2, nose + 0.4), (51.0, nose - 0.1)], rgb("E6D2B0"), 150)
    for i in range(3):
        p.ellipse(51.75 + i * 0.5, nose - 0.38 + i * 0.12, 0.07, 0.07, SKIN_D)
    p.line([(43.6, nose - 0.4), (44.9, nose + 0.5)], rgb("A8402E"), 0.16, 118)
    p.line([(43.9, nose + 0.1), (44.6, nose - 0.2)], rgb("A8402E"), 0.1)
    p.stains(41, cap + 0.6, 14, 8, 4, 0.9, 0.9)
    p.fold([(41, hv(1.512)), (48, hv(1.5)), (55, hv(1.512))], 0.9, 0.7, 20)
    p.rect(32, hv(1.49), 32, 20 - hv(1.49), mul(SKIN, 0.9), 124)
    p.shade_round(32, 0, 32, 20, 0.8)
    # Рукав куртки: шов плеча, кожаная заплата на локте, вязаный манжет, кисть.
    p.rect(0, 22, 16, 26, JACKET, 128)
    p.weave(0, 22, 16, 18, 0.4, 0.035, 9.0)
    p.uneven(0, 22, 16, 18, 0.08, 2.6)
    p.fold([(0, 23.3), (16, 23.3)], 0.3, 0.74, 34)
    p.stitch([(0, 23.9), (16, 23.9)], mul(JACKET_L, 1.1), 0.08, 0.45)
    p.rect(0, 25.4, 16, 0.7, BONE, 140)
    p.rect(0, 26.5, 16, 0.4, BONE, 140)
    for ex in (2.6, 13.4):
        p.ellipse(ex, 32.4, 1.9, 2.7, LEATHER, 150)
        p.ellipse(ex, 32.4, 1.5, 2.3, mul(LEATHER, 1.08), 152)
    p.grain(0, 29.5, 16, 6, 0.06, 1.0, 8.0)
    p.wrinkles(0, 27.2, 16, 4, 5, 2.6, 0.3, 0.88, 22)
    p.wrinkles(0, 34.6, 16, 4.8, 6, 2.6, 0.3, 0.86, 24)
    p.fold([(4.5, 30.6), (8, 31.2), (11.5, 30.6)], 0.4, 0.8, 30)
    p.stains(0, 33, 16, 6, 3, 1.0, 0.84)
    p.rect(0, 39.6, 16, 1.8, JACKET_D, 144)
    for i in range(23):
        p.line([(0.3 + i * 0.7, 39.7), (0.3 + i * 0.7, 41.3)], mul(JACKET_D, 0.78), 0.14, 112)
    p.fold([(0, 39.5), (16, 39.5)], 0.3, 0.66, 44)
    p.rect(0, 41.4, 16, 6.6, SKIN, 128)
    p.grain(0, 41.4, 16, 6.6, 0.03, 1.0, 4.0)
    p.fold([(0, 41.5), (16, 41.5)], 0.3, 0.7, 40)
    for fx in (5.2, 7.0, 8.8, 10.6):
        p.ellipse(fx + 0.9, 45.0, 0.5, 0.3, mul(SKIN, 0.9), 140)
    p.fold([(0, 44.0), (16, 44.0)], 0.35, 0.86, 18)
    _fingers(p, SKIN_D, 0.2)
    p.speckle(0, 42, 16, 5, 16, LEATHER_D, 0.06)
    p.shade_round(0, 22, 16, 26, 0.76)
    # Джинсы: рубчик, двойная рыжая строчка, карман, потёртое колено с прорехой, подворот.
    p.rect(16, 22, 20, 34, DENIM, 128)
    p.twill(16, 22, 20, 34, 0.4, 0.07, 14.0)
    p.uneven(16, 22, 20, 34, 0.09, 3.0)
    p.fold([(16, 22.3), (36, 22.3)], 0.4, 0.72, 30)
    p.fold([(26, 22.4), (26.2, 53.0)], 0.25, 0.84, 22)
    p.stitch([(25.4, 22.6), (25.6, 53.0)], LABEL_D, 0.1, 0.5)
    p.stitch([(26.8, 22.6), (27.0, 53.0)], LABEL_D, 0.1, 0.5)
    p.stitch([(18.5, 24.2), (22.6, 24.2), (22.9, 28.0), (20.6, 29.2), (18.3, 28.0), (18.5, 24.2)], LABEL_D, 0.1, 0.45)
    p.ellipse(18.7, 24.4, 0.2, 0.2, LABEL, 170)
    p.ellipse(22.4, 24.4, 0.2, 0.2, LABEL, 170)
    gx, gy = p._grid(27, 36, 9, 7)
    p._apply(27, 36, 9, 7, 1.0 + 0.5 * _blob(31.2, 39.4, 2.6, 2.0)(gx, gy))
    p.poly([(29.8, 39.0), (32.6, 38.7), (32.9, 39.8), (30.0, 40.2)], SKIN_D, 108)
    for i in range(6):
        p.line([(30.0 + i * 0.5, 38.9), (30.05 + i * 0.5, 40.1)], BONE, 0.08, 140)
    for fy, dark in ((37.6, 0.84), (41.2, 0.88)):
        p.fold([(18, fy), (22, fy + 0.5), (25, fy)], 0.5, dark, 26)
    p.wrinkles(16, 24, 20, 12, 9, 3.6, 0.5, 0.9)
    p.wrinkles(16, 43, 20, 9, 10, 3.0, 0.25, 0.88)
    p.stains(16, 44, 20, 9, 7, 1.4, 0.84)
    p.speckle(16, 46, 20, 7, 40, LEATHER_D, 0.08)
    p.rect(16, 53.2, 20, 2.8, DENIM_L, 146)
    p.twill(16, 53.2, 20, 2.8, 0.4, 0.06)
    p.stitch([(16, 53.6), (36, 53.6)], LABEL_D, 0.08, 0.5)
    p.fold([(16, 53.1), (36, 53.1)], 0.3, 0.62, 50)
    p.shade_v(16, 22, 20, 34, 1.03, 0.88)
    p.shade_round(16, 22, 20, 34, 0.74)
    # Кроссовок: белый верх, серый мысок, шнуровка, красная полоса, подошва.
    p.rect(40, 24, 12, 6, BONE, 132)
    p.grain(40, 24, 12, 6, 0.05, 1.0, 8.0)
    p.rect(40, 24, 12, 0.7, RAG, 150)
    p.rect(40, 26.3, 4.2, 0.9, JACKET, 150)
    p.rect(47.8, 26.3, 4.2, 0.9, JACKET, 150)
    p.ellipse(46, 27.9, 2.2, 1.0, BONE_D, 146)
    p.rect(44.9, 24.5, 2.2, 2.4, BONE_D, 140)
    for i in range(4):
        p.line([(44.9, 24.8 + i * 0.55), (47.1, 25.0 + i * 0.55)], RAG_D, 0.12, 150)
    p.rect(40, 28.7, 12, 1.3, RAG_L, 156)
    p.line([(40, 28.7), (52, 28.7)], RAG_D, 0.14, 110)
    p.stains(40, 26.5, 12, 3.5, 4, 0.8, 0.8)
    p.shade_round(40, 24, 12, 6, 0.74)
    p.rect(54, 24, 6, 6, RAG_D, 128)
    p.rect(54, 32, 6, 6, SKIN, 128)
    # Сигнальная лента: жёлтая с чёрными косыми полосами, конец оборван.
    p.rect(40, 34, 12, 8, LABEL, 128)
    for i in range(9):
        p.poly([(38 + i * 2.4, 34), (39.2 + i * 2.4, 34), (36.4 + i * 2.4, 42), (35.2 + i * 2.4, 42)], BLACK, 124)
    p.rect(52, 34, 2, 8, RAG_D, 128)
    p.rect(38, 34, 2, 8, RAG_D, 128)
    p.wrinkles(40, 34, 12, 8, 5, 3.0, 0.6, 0.84)
    p.stains(40, 34, 12, 8, 4, 1.0, 0.82)
    for i in range(6):
        p.cut(40.2 + i * 2.0, 40.7 + (i % 2) * 0.5, 1.0, 1.4)
    # Рюкзак (кусок полы): наружная стенка у краёв куска, середина прижата к спине. Клапан с
    # ремешками и пряжками, карман на шве, сбоку фляга и нашивка с крестом.
    p.rect(36, 44, 28, 20, LEATHER, 128)
    p.grain(36, 44, 28, 20, 0.1, 1.3, 12.0)
    p.uneven(36, 44, 28, 20, 0.08, 3.0)
    p.rect(36, 44, 28, 8.2, mul(LEATHER, 1.1), 146)
    p.grain(36, 44, 28, 8.2, 0.08, 1.2, 10.0)
    p.fold([(36, 52.3), (64, 52.3)], 0.4, 0.62, 56)
    p.stitch([(36, 51.6), (64, 51.6)], LEATHER_L, 0.09, 0.5)
    for x in (38.9, 61.1):
        p.rect(x - 0.65, 44, 1.3, 13.4, LEATHER_D, 160)
        p.stitch([(x, 44.3), (x, 57.0)], LEATHER, 0.07, 0.45)
        p.rect(x - 0.95, 53.4, 1.9, 1.5, LABEL_D, 182)
        p.rect(x - 0.45, 53.8, 0.9, 0.7, LEATHER_D, 150)
    for x0 in (36.0, 61.4):
        p.rect(x0, 57.4, 2.6, 5.0, mul(LEATHER, 0.86), 148)
        p.rect(x0, 57.4, 2.6, 1.3, mul(LEATHER, 0.74), 156)
    p.stitch([(36, 62.2), (38.4, 62.2), (38.4, 57.6)], LEATHER_L, 0.08, 0.4)
    p.stitch([(64, 62.2), (61.6, 62.2), (61.6, 57.6)], LEATHER_L, 0.08, 0.4)
    p.rect(55.9, 52.8, 2.4, 8.6, STEEL, 166)
    p.rect(56.3, 52.8, 0.5, 8.6, STEEL_L, 172)
    p.rect(56.5, 51.6, 1.2, 1.3, STEEL_D, 170)
    p.rect(55.6, 56.4, 3.0, 0.8, LEATHER_D, 172)
    p.rect(41.4, 54.0, 3.2, 3.2, BONE, 150)
    p.rect(42.7, 54.5, 0.6, 2.2, JACKET)
    p.rect(41.9, 55.3, 2.2, 0.6, JACKET)
    p.stitch([(41.4, 54.0), (44.6, 54.0), (44.6, 57.2), (41.4, 57.2), (41.4, 54.0)], BONE_D, 0.07, 0.4)
    p.rect(36, 44, 28, 0.9, LEATHER_D, 160)
    p.rect(36, 63.1, 28, 0.9, LEATHER_D, 160)
    p.wrinkles(36, 53, 28, 9, 8, 2.6, 0.5, 0.84, 24)
    p.stains(36, 52, 28, 11, 7, 1.3, 0.82)
    p.shade_v(36, 44, 28, 20, 1.06, 0.86)
    # Скатка (кусок шляпы): зелёное одеяло в полоску, два ремня, край одеяла вдоль валика.
    p.rect(0, 48, 16, 16, BLANKET, 128)
    p.weave(0, 48, 16, 16, 0.42, 0.08, 14.0)
    p.uneven(0, 48, 16, 16, 0.1, 2.6)
    for x in (1.2, 5.6, 8.0, 10.4, 14.8):
        p.rect(x - 0.2, 48, 0.4, 16, BLANKET_L, 136)
    p.rect(7.6, 48, 0.8, 16, mul(JACKET_D, 0.9), 134)
    p.fold([(0, 53.4), (5, 53.7), (11, 53.3), (16, 53.5)], 0.35, 0.62, 50)
    for x in (4.0, 12.0):
        p.rect(x - 0.7, 48, 1.4, 16, LEATHER_D, 164)
        p.stitch([(x, 48.2), (x, 63.8)], LEATHER, 0.07, 0.45)
        p.rect(x - 0.95, 58.6, 1.9, 1.3, LABEL_D, 182)
        p.fold([(x - 1.0, 48), (x - 1.0, 64)], 0.3, 0.7, 30)
        p.fold([(x + 1.0, 48), (x + 1.0, 64)], 0.3, 0.7, 30)
    p.wrinkles(0, 48, 16, 16, 8, 2.6, 0.3, 0.84, 22)
    # Свои куски: козырёк со строчкой и скруглённым краем, макушка с пуговкой, торец скатки, дно.
    x, y, w, h = EXTRA_A
    p.rect(x, y, w, h, DENIM, 140)
    p.weave(x, y, w, h, 0.36, 0.05, 10.0)
    for i in range(4):
        d = 1.2 + i * 1.5
        p.line([(x + 0.3, y + d - 0.5), (x + w / 2, y + d + 0.6), (x + w - 0.3, y + d - 0.5)], DENIM_L if i % 2 else DENIM_D, 0.09, 150)
    p.cut(x, y + 4.2, w, h - 4.2)
    arc = [(x + w / 2 + (w / 2) * math.cos(math.pi * i / 16), y + 4.2 + 3.6 * math.sin(math.pi * i / 16)) for i in range(17)]
    p.solid([(x + w, y), (x, y)][::-1] + arc)
    p.line(arc, DENIM_D, 0.5, 158)
    p.rect(*CROWN, DENIM, 140)
    p.weave(*CROWN, 0.36, 0.05, 10.0)
    for i in range(6):
        a = math.pi * i / 3.0
        p.line([(28, 58), (28 + 2.2 * math.cos(a), 58 + 2.2 * math.sin(a))], DENIM_D, 0.14, 116)
    p.ellipse(28, 58, 0.6, 0.6, DENIM_L, 180)
    p.rect(*EXTRA_B, BLANKET, 128)
    for i, rr in enumerate((1.8, 1.35, 0.9, 0.45)):
        p.ellipse(28, 62, rr, rr, BLANKET_L if i % 2 else mul(BLANKET, 0.8), 128 + i * 8)
    p.rect(*EXTRA_C, LEATHER, 128)
    p.grain(*EXTRA_C, 0.1, 1.3, 12.0)
    p.stitch([(30.6, 56.6), (35.4, 56.6), (35.4, 63.4), (30.6, 63.4), (30.6, 56.6)], LEATHER_L, 0.08, 0.5)
    return p


def zombies_survivor():
    """Выживший: красная куртка, бейсболка с длинным козырьком, джинсы и кроссовки, за спиной
    кожаный рюкзак со скаткой; обрывки сигнальной ленты на пружине."""
    p = paint_survivor()
    reg = regions(p)
    r, _ = rm.build_body("hero", reg, bulk=1.06, limb=1.02, leg="straight")
    # Голова в кепке: купол шире головы от линии бровей.
    head_tube(r, reg, [(1.45, 0.06, 0.062), (1.5, 0.056, 0.06), (1.525, 0.072, 0.08), (1.555, 0.09, 0.099),
                       (1.59, 0.1, 0.11), (1.63, 0.105, 0.116), (1.668, 0.106, 0.117), (1.674, 0.116, 0.127),
                       (1.71, 0.115, 0.126), (1.745, 0.103, 0.113), (1.772, 0.076, 0.084), (1.788, 0.036, 0.04)], HERO_HEAD[1])
    # Длинный козырёк вперёд, корнем утоплен в купол, к краю чуть опущен.
    head = lambda t: [("head", 1.0)]
    r.strip([(0.0, 1.676, -0.095), (0.0, 1.674, -0.16), (0.0, 1.667, -0.22), (0.0, 1.655, -0.275)], (1.0, 0.0, 0.0), 0.096,
            p.region(*EXTRA_A), head, 0.0, 0.0, 0.12)
    # Рюкзак на спине: скруглённый блок от лопаток до пояса, держится за грудь.
    chest = lambda y: [("chest", 1.0)] if y > 1.2 else [("chest", 0.6), ("spine", 0.4)]
    r.tube([(1.05, 0.1, 0.05, 0, 0.15), (1.075, 0.132, 0.08, 0, 0.158), (1.15, 0.142, 0.09, 0, 0.162), (1.26, 0.14, 0.088, 0, 0.162),
            (1.36, 0.134, 0.082, 0, 0.158), (1.395, 0.118, 0.066, 0, 0.154), (1.41, 0.09, 0.045, 0, 0.15)], 12, reg["skirt"], chest,
           cap_bottom=p.region(*EXTRA_C), cap_top=p.region(*EXTRA_C))
    # Скатка поперёк над рюкзаком.
    roll_x(r, -0.175, 0.175, 1.435, 0.178, 0.056, 10, reg["hat"], p.region(*EXTRA_B), [("chest", 1.0)])
    # Обрывки сигнальной ленты, привязанные к ремню скатки: две ленты на пружинной кости.
    r.bone("tail", "chest", (0.095, 1.43, 0.17))
    r.spring("tail", 45.0, 5.0, 1.0, (0.0, -1.0, 0.15))
    weight = lambda t: [("chest", 1.0 - t), ("tail", t)] if t < 1.0 else [("tail", 1.0)]
    for dx, lean, n in ((0.078, -0.012, 6), (0.112, 0.014, 5)):
        pts = [(dx + lean * i, 1.44 - 0.05 * i, 0.236 + 0.009 * i) for i in range(n)]
        r.strip(pts, (1.0, 0.0, 0.0), 0.02, reg["strip"], weight, 0.2, 1.0, 0.1)
    return r, p


# --- Зомби-мясник -------------------------------------------------------------------------------

BUTCHER_HEAD = (1.44, 1.805)


def paint_butcher():
    """Атлас мясника: майка на голом торсе, завязки фартука, лысая голова с раной от тесака,
    толстые руки в жёлтых резиновых перчатках, штаны в резиновых сапогах, фартук в крови, тесак."""
    p = rm.Paint(243)
    # Торс: майка в рубчик, голые плечи и загривок, лямка фартука на шее, завязки с бантом сзади.
    p.rect(0, 0, 32, 22, TANK, 128)
    p.weave(0, 0, 32, 22, 0.4, 0.04, 9.0)
    for i in range(40):
        p.line([(0.4 + i * 0.8, 3.0), (0.4 + i * 0.8, 18.6)], mul(TANK, 0.9), 0.1, 118)
    p.uneven(0, 0, 32, 22, 0.09, 3.0)
    skin = np.asarray(p.im).copy()
    _rot_skin(p, 0, 0, 32, 5.2)
    rot = np.asarray(p.im).copy()
    # Лямки майки поверх кожи: вернуть ткань в полосах лямок и под вырезами.
    mask = rm.Image.new("L", (p.n, p.n), 0)
    md = rm.ImageDraw.Draw(mask)
    k = p.k
    md.rectangle([0, 3.4 * k, 32 * k, 5.4 * k], fill=255)
    for x in (4.4, 9.4, 22.6, 27.6):
        md.polygon([((x - 1.3) * k, 0), ((x + 1.3) * k, 0), ((x + 1.7) * k, 3.6 * k), ((x - 1.7) * k, 3.6 * k)], fill=255)
    for cx, rx in ((16.0, 5.0), (0.0, 3.2), (32.0, 3.2)):
        md.ellipse([(cx - rx) * k, 1.4 * k, (cx + rx) * k, 5.0 * k], fill=0)
    m = (np.asarray(mask, dtype=np.float32) / 255.0)[..., None]
    p.im = rm.Image.fromarray((rot * (1.0 - m) + skin * m).astype(np.uint8))
    p.d = rm.ImageDraw.Draw(p.im)
    for cx, rx in ((16.0, 5.0), (0.0, 3.2), (32.0, 3.2)):
        arc = [(cx + rx * math.cos(math.pi * i / 12), 3.2 + 1.8 * math.sin(math.pi * i / 12)) for i in range(13)]
        p.line(arc, TANK_D, 0.3, 150)
    for x in (4.4, 9.4, 22.6, 27.6):
        p.stitch([(x - 1.0, 0.2), (x - 1.35, 3.4)], mul(TANK, 1.25), 0.07, 0.4)
    p.fold([(0, 1.6), (32, 1.6)], 0.4, 0.82, 22)
    # Лямка фартука вокруг шеи и завязки на поясе.
    for sx in (-1.0, 1.0):
        p.line([(16 + sx * 4.2, 4.6), (16 + sx * 3.2, 1.4), (16 + sx * 4.4, 0.5), (16 + sx * 16, 0.6)], BONE_D, 0.75, 156)
        p.line([(16 + sx * 4.2, 4.6), (16 + sx * 3.2, 1.4), (16 + sx * 4.4, 0.5), (16 + sx * 16, 0.6)], BONE, 0.4, 162)
        p.line([(16 + sx * 5.0, 14.2), (16 + sx * 16, 14.0)], BONE_D, 0.9, 156)
        p.line([(16 + sx * 5.0, 14.2), (16 + sx * 16, 14.0)], BONE, 0.5, 162)
        x0 = 16 + sx * 16
        p.ellipse(x0 - sx * 1.5, 13.4, 1.4, 0.75, BONE, 166)
        p.ellipse(x0 - sx * 1.5, 13.4, 0.8, 0.3, BONE_D, 140)
        p.line([(x0 - sx * 0.3, 14.2), (x0 - sx * 1.0, 16.4), (x0 - sx * 0.8, 18.2)], BONE, 0.5, 160)
        # Складки жира на боках, вытертые о майку ладони.
        p.fold([(16 + sx * 6.5, 9.2), (16 + sx * 10, 9.9), (16 + sx * 13.5, 9.3)], 0.6, 0.8, 32)
        p.fold([(16 + sx * 6.5, 12.4), (16 + sx * 10, 13.0), (16 + sx * 13.5, 12.5)], 0.5, 0.84, 26)
        for i in range(4):
            fx = 16 + sx * (8.2 + i * 0.8)
            p.line([(fx, 15.2 + (i % 2) * 0.4), (fx + sx * 0.5, 18.0)], BLOOD_D if i % 2 else BLOOD, 0.34, 124)
    p.ellipse(0.2, 14.0, 0.5, 0.5, BONE_D, 170)
    p.ellipse(31.8, 14.0, 0.5, 0.5, BONE_D, 170)
    _blood(p, 2, 5.5, 28, 9, 6, 0.8)
    p.stains(0, 5, 32, 13, 10, 1.5, 0.82)
    p.wrinkles(0, 6, 32, 10, 8, 3.0, 0.3, 0.88, 20)
    # Край майки навыпуск и тёмные штаны.
    p.rect(0, 19.4, 32, 2.6, SLACKS, 128)
    p.twill(0, 19.4, 32, 2.6, 0.4, 0.06)
    p.fold([(0, 19.3), (32, 19.3)], 0.35, 0.62, 46)
    p.stitch([(0, 18.8), (32, 18.8)], mul(TANK, 1.25), 0.07, 0.4)
    p.shade_v(0, 0, 32, 19, 1.06, 0.88)
    p.shade_round(0, 0, 32, 22, 0.74)
    # Голова: лысый череп с раной от тесака, шов на виске, тяжёлый лоб, жёлтый глаз и бельмо,
    # приплюснутый нос, широкая пасть, подбородки.
    hv = _hv(*BUTCHER_HEAD)
    _rot_skin(p, 32, 0, 32, 20)
    gx, gy = p._grid(32, 0, 32, 6)
    p._apply(32, 0, 32, 6, (1.0 + 0.16 * np.clip(1.0 - gy / 6.0, 0, 1)).astype(np.float32))
    for x0, y1 in ((48.0, 3.9), (32.0, 2.6), (64.0, 2.6)):
        p.poly([(x0 - 1.15, 0), (x0 + 1.15, 0), (x0 + 0.5, y1 * 0.7), (x0, y1)], BLOOD_D, 84)
        p.poly([(x0 - 0.55, 0), (x0 + 0.55, 0), (x0, y1 * 0.8)], rgb("3A0E12"), 60)
        p.line([(x0 - 1.2, 0), (x0 - 0.1, y1)], BLOOD, 0.16, 120)
    for dx, y1 in ((-0.7, hv(1.7)), (0.4, hv(1.672)), (1.3, hv(1.61))):
        p.line([(48 + dx * 0.4, 2.6), (48 + dx, 4.4), (48 + dx * 1.2, y1)], BLOOD_D, 0.3, 124)
        p.ellipse(48 + dx * 1.2, y1, 0.24, 0.32, BLOOD)
    p.line([(39.6, 4.6), (41.6, 3.9), (44.0, 4.3)], mul(ROT_D, 0.8), 0.24, 100)
    for i in range(5):
        p.line([(39.9 + i * 1.0, 3.7 + (i % 2) * 0.1), (40.0 + i * 1.0, 5.0)], BLACK, 0.12, 140)
    brow = hv(1.688)
    for sx in (-1.0, 1.0):
        p.fold([(48 + sx * 0.7, brow + 0.5), (48 + sx * 3.0, brow - 0.3), (48 + sx * 5.8, brow + 0.6)], 0.9, 0.66, 44)
    p.fold([(46.6, brow - 1.3), (49.4, brow - 1.3)], 0.25, 0.84, 18)
    p.fold([(46.9, brow - 0.3), (48, brow + 0.6), (49.1, brow - 0.3)], 0.3, 0.8, 22)
    ey = hv(1.656)
    for sx, iris in ((-1.0, LABEL), (1.0, BONE)):
        ex = 48 + sx * 3.0
        p.ellipse(ex, ey, 1.75, 1.2, mul(ROT_D, 0.72), 96)
        p.ellipse(ex, ey + 0.05, 1.05, 0.72, iris, 132)
        if sx < 0:
            p.ellipse(ex + 0.1, ey + 0.05, 0.2, 0.55, BLACK)
            p.ellipse(ex - 0.3, ey - 0.2, 0.13, 0.13, rgb("FFF6C8"))
            for i in range(4):
                p.line([(ex - 1.0 + i * 0.15, ey + 0.3 - i * 0.2), (ex - 0.5, ey)], BLOOD, 0.06)
        else:
            p.ellipse(ex - 0.1, ey + 0.05, 0.38, 0.38, BONE_D)
            p.ellipse(ex - 0.1, ey + 0.05, 0.14, 0.14, RAG_D)
        p.fold([(ex - 1.5, ey + 1.5), (ex, ey + 1.95), (ex + 1.5, ey + 1.5)], 0.4, 0.8, 26)
        p.fold([(ex - 1.3, ey + 2.2), (ex, ey + 2.6), (ex + 1.2, ey + 2.2)], 0.25, 0.86, 16)
        # Уши и брыли.
        p.ellipse(48 + sx * 8.7, hv(1.64), 0.9, 1.4, mul(ROT, 0.9), 142)
        p.ellipse(48 + sx * 8.7, hv(1.64), 0.4, 0.8, ROT_D, 116)
        p.fold([(48 + sx * 2.3, hv(1.615)), (48 + sx * 4.6, hv(1.58)), (48 + sx * 5.2, hv(1.535))], 0.7, 0.74, 34)
    nose = hv(1.618)
    p.poly([(47.0, ey - 0.3), (49.0, ey - 0.3), (50.1, nose), (48, nose + 0.5), (45.9, nose)], mul(ROT, 0.92), 150)
    p.ellipse(47.1, nose, 0.42, 0.34, BLACK, 88)
    p.ellipse(48.9, nose, 0.42, 0.34, BLACK, 88)
    p.fold([(45.8, nose + 0.4), (48, nose + 0.85), (50.2, nose + 0.4)], 0.3, 0.78, 24)
    mouth = hv(1.574)
    lips = [(43.4, mouth - 0.5), (48, mouth - 0.1), (52.6, mouth - 0.7), (53.0, mouth + 0.6), (50.6, mouth + 1.5), (45.4, mouth + 1.5), (43.2, mouth + 0.5)]
    p.poly([(qx + (qx - 48) * 0.07, qy + (qy - mouth - 0.4) * 0.3) for qx, qy in lips], mul(ROT_D, 0.62), 108)
    p.poly(lips, rgb("1E0C10"), 70)
    for i in range(8):
        tx = 44.3 + i * 1.02
        if i == 5:
            continue
        p.rect(tx, mouth - 0.42 + abs(i - 3.5) * 0.02, 0.8, 0.82 + (i % 3) * 0.1, BONE if i % 2 else BONE_D, 150)
    for tx, th in ((45.3, 1.1), (47.3, 0.6), (49.0, 0.7), (50.9, 1.2)):
        p.poly([(tx - 0.42, mouth + 1.45), (tx + 0.42, mouth + 1.45), (tx + 0.25, mouth + 1.45 - th), (tx - 0.25, mouth + 1.45 - th)], BONE, 152)
    p.poly([(49.4, mouth + 1.4), (52.2, mouth + 0.9), (52.0, mouth + 2.6), (50.9, mouth + 3.9), (50.3, mouth + 2.4)], BLOOD, 122)
    p.line([(50.9, mouth + 3.6), (51.0, hv(1.49))], BLOOD_D, 0.3, 122)
    p.line([(45.0, mouth + 1.6), (45.2, mouth + 2.9)], BLOOD_D, 0.24, 122)
    for fy, dark in ((hv(1.524), 0.68), (hv(1.494), 0.74), (hv(1.468), 0.8)):
        p.fold([(32, fy - 0.2), (40, fy + 0.2), (48, fy + 0.5), (56, fy + 0.2), (64, fy - 0.2)], 0.6, dark, 40)
    p.fold([(32, hv(1.63)), (36, hv(1.625))], 0.5, 0.78, 30)
    p.fold([(60, hv(1.625)), (64, hv(1.63))], 0.5, 0.78, 30)
    _veins(p, 33, 1, 9, 6, 3, mul(ROT_D, 0.9))
    _veins(p, 54, 1, 9, 6, 3, mul(ROT_D, 0.9))
    p.shade_round(32, 0, 32, 20, 0.8)
    # Рука: голое плечо с наколкой-сердцем, шов, предплечье в крови, жёлтая перчатка.
    _rot_skin(p, 0, 22, 16, 26)
    p.fold([(0, 22.5), (16, 22.5)], 0.4, 0.8, 26)
    ink = mix(ROT_D, rgb("1E2A44"), 0.6)
    for sx in (-1.0, 1.0):
        p.ellipse(8 + sx * 0.75, 27.6, 0.95, 0.9, ink)
    p.poly([(6.35, 28.0), (9.65, 28.0), (8, 30.2)], ink)
    p.ellipse(7.25, 27.6, 0.45, 0.4, mix(ROT, BLOOD_D, 0.5))
    p.ellipse(8.75, 27.6, 0.45, 0.4, mix(ROT, BLOOD_D, 0.5))
    p.poly([(5.6, 28.3), (10.4, 27.9), (10.4, 29.0), (5.6, 29.4)], mix(ROT_L, BONE, 0.4))
    p.line([(5.6, 28.3), (10.4, 27.9)], ink, 0.12)
    p.line([(5.6, 29.4), (10.4, 29.0)], ink, 0.12)
    for i in range(3):
        p.line([(6.7 + i * 1.1, 28.5), (6.7 + i * 1.1, 29.1)], ink, 0.14)
    p.line([(1.6, 30.4), (4.6, 31.4)], mul(ROT_D, 0.78), 0.22, 102)
    for i in range(4):
        p.line([(1.9 + i * 0.75, 30.0 + i * 0.25), (1.6 + i * 0.75, 31.2 + i * 0.25)], BLACK, 0.1, 140)
    p.fold([(0, 32.8), (5, 33.3), (11, 32.7), (16, 32.9)], 0.5, 0.78, 30)
    _veins(p, 0, 33.4, 16, 5, 4, mul(ROT_D, 0.9))
    _tint(p, 0, 33, 16, 5.6, BLOOD_D, lambda gx, gy: 0.6 * np.clip((gy - 35.6) / 2.6 + 0.3 * np.sin(gx * 2.3) - 0.1, 0, 1))
    _blood(p, 0, 31, 16, 6, 3, 0.6, 2.0)
    p.rect(0, 38.4, 16, 9.6, GLOVE, 140)
    p.grain(0, 38.4, 16, 9.6, 0.05, 1.0, 6.0)
    p.rect(0, 38.4, 16, 1.2, GLOVE_L, 168)
    p.fold([(0, 39.7), (16, 39.7)], 0.3, 0.7, 40)
    p.fold([(0, 38.3), (16, 38.3)], 0.3, 0.6, 50)
    p.wrinkles(0, 40, 16, 3.4, 6, 2.4, 0.3, 0.86, 22)
    p.fold([(0, 44.0), (16, 44.0)], 0.35, 0.84, 20)
    _tint(p, 0, 41.6, 16, 6.4, BLOOD, lambda gx, gy: 0.95 * np.clip(((gy - 44.0) + 0.7 * np.sin(gx * 2.9) + 0.4 * np.sin(gx * 6.1 + 1.0)) / 0.3, 0, 1))
    for fx in (2.0, 6.2, 9.4, 13.6):
        p.line([(fx, 44.0), (fx + 0.1, 42.4 - (fx % 2) * 0.6)], BLOOD, 0.3, 124)
    _fingers(p, BLOOD_D, 0.24)
    p.shade_round(0, 22, 16, 26, 0.74)
    # Нога: тёмные штаны, высокий резиновый сапог с отворотом, блик, брызги.
    p.rect(16, 22, 20, 34, SLACKS, 128)
    p.twill(16, 22, 20, 17.4, 0.42, 0.06, 12.0)
    p.uneven(16, 22, 20, 17.4, 0.08, 3.0)
    p.fold([(16, 22.3), (36, 22.3)], 0.4, 0.72, 30)
    p.fold([(26, 22.4), (26.1, 39.0)], 0.25, 0.82, 22)
    p.wrinkles(16, 24, 20, 13, 10, 3.4, 0.5, 0.86)
    for fy in (36.6, 37.8):
        p.fold([(17.5, fy), (26, fy + 0.6), (34.5, fy)], 0.55, 0.8, 30)
    p.stains(16, 28, 20, 10, 6, 1.4, 0.8)
    p.rect(16, 39.2, 20, 16.8, RUBBER, 140)
    p.grain(16, 39.2, 20, 16.8, 0.05, 1.2, 6.0)
    p.rect(16, 39.2, 20, 1.9, TANK, 160)
    p.rect(16, 40.8, 20, 0.3, TANK_D, 150)
    p.fold([(16, 39.1), (36, 39.1)], 0.35, 0.56, 56)
    gx, gy = p._grid(16, 41.2, 20, 14.8)
    gloss = np.exp(-(((gx - 22.6) / 0.7) ** 2)) * 0.9 + np.exp(-(((gx - 30.4) / 0.35) ** 2)) * 0.45
    p._apply(16, 41.2, 20, 14.8, (1.0 + gloss * np.clip(1.0 - (gy - 41.2) / 16.0, 0.2, 1)).astype(np.float32))
    for fy in (50.6, 52.0):
        p.fold([(17, fy), (26, fy + 0.5), (35, fy)], 0.45, 0.78, 30)
    _blood(p, 16, 41.5, 20, 12, 5, 0.6, 2.2)
    p.stains(16, 50, 20, 6, 5, 1.2, 0.8)
    p.shade_v(16, 22, 20, 34, 1.04, 0.88)
    p.shade_round(16, 22, 20, 34, 0.74)
    # Сапог: чёрная резина, блик на носке, рифлёная подошва, брызги.
    p.rect(40, 24, 12, 6, RUBBER, 132)
    p.grain(40, 24, 12, 6, 0.05, 1.0, 6.0)
    p.ellipse(46, 26.6, 1.9, 0.7, mul(RUBBER, 1.9))
    p.ellipse(46.3, 26.4, 0.9, 0.3, mul(RUBBER, 2.8))
    p.fold([(40, 25.6), (52, 25.6)], 0.4, 0.74, 34)
    p.rect(40, 28.5, 12, 1.5, RUBBER_D, 152)
    for i in range(12):
        p.line([(40.5 + i, 28.7), (40.5 + i, 30)], mul(RUBBER, 1.5), 0.14, 130)
    _blood(p, 40.5, 24.4, 11, 3.6, 2, 0.45, 1.2)
    p.shade_round(40, 24, 12, 6, 0.72)
    p.rect(54, 24, 6, 6, RUBBER_D, 128)
    p.rect(54, 32, 6, 6, BLOOD_D, 128)
    # Тесак (кусок ленты): широкий клинок с отверстием у обуха, кровь по лезвию, рукоять на заклёпках.
    p.rect(40, 34, 12, 8, STEEL, 140)
    p.grain(40, 34, 12, 8, 0.05, 0.8, 5.0)
    gx, gy = p._grid(40, 34, 12, 5.2)
    p._apply(40, 34, 12, 5.2, (0.84 + 0.3 * np.exp(-(((gx - 45.6 - (gy - 34) * 0.3) / 1.6) ** 2))).astype(np.float32))
    for _ in range(12):
        sx_, sy_ = p.rng.uniform(42, 51), p.rng.uniform(34.2, 38.6)
        p.line([(sx_, sy_), (sx_ + p.rng.uniform(-0.3, 0.3), sy_ + p.rng.uniform(0.5, 1.4))], STEEL_L, 0.06, 150)
    p.rect(40, 34, 1.3, 5.2, STEEL_L, 166)
    p.rect(51.4, 34, 0.6, 5.2, STEEL_D, 150)
    p.speckle(42, 34, 9, 5, 30, RUST, 0.09)
    _tint(p, 40, 34, 6, 5.2, BLOOD, lambda gx, gy: 0.95 * np.clip(1.6 - (gx - 40) / 1.9 + 0.6 * np.sin(gy * 4.1) + 0.4 * np.sin(gy * 9.0), 0, 1))
    _blood(p, 43, 34.2, 7, 4.2, 2, 0.4, 0.8)
    p.rect(40, 39.0, 12, 3.0, LEATHER_D, 128)
    p.rect(47.2, 38.6, 3.6, 3.4, LEATHER, 160)
    p.rect(47.2, 38.6, 0.6, 3.4, LEATHER_L, 166)
    p.rect(47.2, 38.6, 3.6, 0.5, STEEL_D, 170)
    for ry in (39.8, 41.0):
        p.ellipse(49.0, ry, 0.3, 0.3, STEEL_L, 180)
    p.cut(40, 39.2, 7.2, 2.8)
    p.cut(50.8, 39.2, 1.2, 2.8)
    p.cut_ellipse(50.3, 35.0, 0.45, 0.4)
    _cut_poly(p, [(51.0, 34.0), (52.0, 34.0), (52.0, 34.8)])
    # Фартук (кусок полы): перёд в середине куска. Нагрудник со строчкой, пояс с люверсами,
    # карман, складки подола; отпечаток ладони, брызги, низ пропитан кровью.
    p.rect(36, 44, 28, 20, BONE, 128)
    p.weave(36, 44, 28, 20, 0.4, 0.05, 10.0)
    p.uneven(36, 44, 28, 20, 0.08, 3.0)
    p.rect(36, 44, 28, 0.9, BONE_D, 150)
    p.stitch([(36, 45.2), (64, 45.2)], RAG_D, 0.08, 0.45)
    for x in (46.9, 53.1):
        p.stitch([(x, 44.4), (x, 50.2)], RAG_D, 0.08, 0.45)
        p.ellipse(x + (0.5 if x < 50 else -0.5), 45.0, 0.3, 0.3, STEEL_D, 172)
    p.fold([(36, 50.5), (64, 50.5)], 0.5, 0.74, 40)
    p.stitch([(36, 51.1), (64, 51.1)], RAG_D, 0.08, 0.45)
    for x in (42.6, 57.4):
        p.ellipse(x, 50.5, 0.42, 0.42, STEEL, 176)
        p.ellipse(x, 50.5, 0.18, 0.18, STEEL_D, 120)
    p.rect(47.0, 53.0, 6.0, 4.4, mul(BONE, 0.95), 142)
    p.stitch([(47.0, 53.0), (47.0, 57.4), (53.0, 57.4), (53.0, 53.0)], RAG_D, 0.08, 0.45)
    p.fold([(47.0, 53.0), (53.0, 53.0)], 0.3, 0.7, 34)
    p.rect(51.0, 51.4, 0.9, 1.7, LEATHER_D, 166)
    for i in range(9):
        x = 41.5 + i * 2.1 + p.rng.uniform(-0.3, 0.3)
        p.fold([(x, 51.4), (x + p.rng.uniform(-0.4, 0.4), 57.0), (x + p.rng.uniform(-0.6, 0.6), 63.6)], p.rng.uniform(0.4, 0.8), 0.82, 40)
    p.wrinkles(44, 45.4, 12, 4.6, 5, 2.6, 0.4, 0.88, 20)
    # Отпечаток ладони на нагруднике: ладонь и четыре смазанных пальца.
    p.ellipse(49.6, 48.6, 1.15, 1.05, BLOOD_D, 122)
    p.ellipse(49.7, 48.5, 0.8, 0.7, BLOOD)
    for i in range(4):
        fx = 48.3 + i * 0.85
        p.line([(fx, 47.6), (fx - 0.2 + i * 0.12, 45.9 + abs(i - 1.5) * 0.3)], BLOOD if i % 2 else BLOOD_D, 0.36, 124)
    p.line([(48.4, 48.9), (47.6, 48.2)], BLOOD_D, 0.34, 124)
    p.line([(49.5, 49.5), (49.4, 52.6)], BLOOD_D, 0.22, 122)
    _blood(p, 41, 45.5, 18, 5, 4, 0.55, 2.0)
    _blood(p, 40, 51.5, 20, 9, 11, 0.95, 2.6)
    _tint(p, 36, 55, 28, 9, BLOOD_D, lambda gx, gy: 0.9 * np.clip((gy - 60.6) / 2.6 + 0.45 * np.sin(gx * 1.7) + 0.3 * np.sin(gx * 4.3 + 0.7) + 0.2 * np.sin(gx * 9.1), 0, 1))
    p.rect(36, 63.2, 28, 0.8, mul(BLOOD_D, 0.8), 150)
    p.shade_v(36, 44, 28, 20, 1.05, 0.86)
    gx, gy = p._grid(36, 44, 28, 20)
    p._apply(36, 44, 28, 20, (1.0 - 0.2 * np.abs((gx - 50) / 9.0) ** 2.0).clip(0.7, 1.0).astype(np.float32))
    # Кусок шляпы свободен: изнанка фартука.
    p.rect(0, 48, 16, 16, BONE_D, 128)
    p.weave(0, 48, 16, 16, 0.4, 0.05)
    # Макушка: лысина с раной от тесака.
    _rot_skin(p, *CROWN)
    p.rect(*CROWN, mix(ROT, ROT_L, 0.6), 128)
    p.rect(27.55, 56, 0.9, 4, BLOOD_D, 80)
    p.rect(27.8, 56, 0.4, 4, rgb("3A0E12"), 60)
    return p


def zombies_butcher():
    """Зомби-мясник: грузный, лысый, с брюхом под заляпанным фартуком, в резиновых сапогах и
    перчатках; в темени застрял тесак, подол фартука на пружине."""
    p = paint_butcher()
    reg = regions(p)
    r, _ = rm.build_body("captain", reg, bulk=1.14, limb=1.16, leg="straight")
    # Брюхо: вторая труба поверх торса с той же развёрткой, выпирает вперёд, краями утоплена в тело.
    r.tube([(0.9, 0.172, 0.128, 0, -0.004), (0.96, 0.192, 0.184, 0, -0.03), (1.04, 0.198, 0.206, 0, -0.036),
            (1.12, 0.198, 0.196, 0, -0.03), (1.2, 0.2, 0.166, 0, -0.016), (1.25, 0.2, 0.134, 0, 0.0)], 16, reg["torso"], BODY,
           v_range=(0.86, 1.47))
    # Голова: бычья шея, тяжёлая челюсть, лысый череп.
    head_tube(r, reg, [(1.44, 0.11, 0.095), (1.47, 0.09, 0.09), (1.5, 0.09, 0.094), (1.53, 0.108, 0.116), (1.57, 0.122, 0.132),
                       (1.62, 0.127, 0.137), (1.67, 0.124, 0.134), (1.72, 0.114, 0.124), (1.76, 0.094, 0.104),
                       (1.79, 0.06, 0.068), (1.803, 0.03, 0.034)], BUTCHER_HEAD[1])
    # Тесак в темени: клинок наискось вдоль черепа, рукоять торчит назад и вверх.
    pts = [(0.004 + 0.008 * i, 1.8 + 0.0125 * i, -0.115 + 0.079 * i) for i in range(5)]
    r.strip(pts, (0.2, 0.98, 0.0), 0.065, reg["strip"], lambda t: [("head", 1.0)], 0.0, 0.0, 0.0)
    # Фартук: нагрудник от груди, ниже пояса подол до колен вокруг брюха; спина открыта. Низ на
    # пружинной кости.
    r.bone("skirt", "hips", (0.0, 1.0, 0.06))
    r.spring("skirt", 60.0, 6.0, 0.5, (0.0, -1.0, 0.0))

    def cw(y):
        if y >= 1.3:
            return [("chest", 1.0)]
        if y >= 1.0:
            t = (1.3 - y) / 0.3
            return [("chest", 1.0 - t), ("spine", t * 0.6), ("hips", t * 0.4)]
        t = max(0.0, min(1.0, (1.0 - y) / 0.5))
        return [("hips", 0.4 * (1.0 - t) + 0.15), ("spine", 0.45 * (1.0 - t)), ("skirt", 0.85 * t)]

    rings = [(0.5, 0.236, 0.2, 0, -0.05), (0.7, 0.226, 0.2, 0, -0.05), (0.88, 0.216, 0.214, 0, -0.046),
             (0.99, 0.212, 0.226, 0, -0.04), (1.08, 0.21, 0.228, 0, -0.036), (1.18, 0.206, 0.206, 0, -0.03),
             (1.28, 0.204, 0.166, 0, -0.016), (1.36, 0.196, 0.14, 0, -0.008)]
    hidden = {(i, kk) for i in range(len(rings) - 1) for kk in range(16) if not (4 <= kk <= 11 if i < 4 else 6 <= kk <= 9)}
    r.tube(rings, 16, reg["skirt"], cw, lambda y: max(0.0, min(1.0, (1.0 - y) / 0.5)) * 0.6, skip=hidden)
    return r, p


# --- Зомби-ходок --------------------------------------------------------------------------------

WALKER_HEAD = (1.45, 1.765)
WALKER_LEAN = (0.2, -0.1)


def paint_walker():
    """Атлас ходока: серая рубаха в лохмотьях с раной до рёбер, голова с белым глазом и пустой
    глазницей, рваный рукав и голое предплечье с укусом, штаны до голени, босая стопа, лохмотья,
    лопата, клок волос."""
    p = rm.Paint(223)
    # Торс: рубаха с растянутым воротом, планка с оторванными пуговицами, дыры, рана, грязь.
    p.rect(0, 0, 32, 22, RAG, 128)
    p.weave(0, 0, 32, 16, 0.44, 0.07, 14.0)
    p.uneven(0, 0, 32, 16, 0.12, 3.0)
    for x in (5.0, 11.0, 21.0, 27.0):
        p.line([(x, 1.8), (x + 0.1, 15.4)], mul(RAG, 0.9), 0.16, 122)
    p.rect(0, 0, 32, 1.5, ROT, 124)
    p.poly([(11.6, 0), (20.4, 0), (17.8, 3.4), (16, 4.4), (14.2, 3.4)], ROT, 116)
    p.grain(0, 0, 32, 1.5, 0.07, 1.0, 6.0)
    p.fold([(13.2, 1.5), (15.0, 2.6)], 0.3, 0.78, 24)
    p.fold([(18.8, 1.5), (17.0, 2.6)], 0.3, 0.78, 24)
    p.line([(0, 1.6), (11.6, 1.5), (14.2, 3.5), (16, 4.6), (17.8, 3.5), (20.4, 1.5), (32, 1.6)], RAG_L, 0.42, 152)
    p.line([(0, 1.95), (11.5, 1.85), (14.1, 3.9), (16, 5.0), (17.9, 3.9), (20.5, 1.85), (32, 1.95)], RAG_D, 0.16, 110)
    p.fold([(16, 5.0), (16.2, 15.2)], 0.3, 0.72, 34)
    p.stitch([(15.4, 5.2), (15.6, 15.0)], RAG_L, 0.07, 0.45)
    for by, kept in ((6.6, True), (9.2, False), (11.8, True), (14.2, False)):
        if kept:
            p.ellipse(16.8, by, 0.36, 0.36, BONE, 170)
            p.ellipse(16.8, by, 0.1, 0.1, RAG_D)
        else:
            p.line([(16.7, by), (17.2, by + 0.7)], RAG_D, 0.07)
            p.line([(16.8, by), (16.5, by + 0.6)], RAG_D, 0.07)
    # Дыры с мёртвой кожей: тёмный рваный край, внутри кожа.
    for cx, cy, rx, ry in ((8.2, 7.2, 1.7, 1.1), (27.6, 5.4, 1.0, 1.6), (3.0, 10.6, 1.2, 1.7), (11.4, 12.6, 1.3, 0.8), (29.6, 12.0, 1.4, 1.0)):
        hole = [(cx + math.cos(a) * rx * q, cy + math.sin(a) * ry * q)
                for a, q in ((6.28 * i / 9, p.rng.uniform(0.6, 1.25)) for i in range(9))]
        p.poly([(cx + (qx - cx) * 1.2, cy + (qy - cy) * 1.2) for qx, qy in hole], mul(RAG_D, 0.85), 108)
        p.poly(hole, mul(ROT, 0.9), 98)
        p.line([hole[0], (cx, cy), hole[4]], ROT_D, 0.1)
        for i in range(5):
            a = p.rng.uniform(0, 6.28)
            p.line([(cx + math.cos(a) * rx, cy + math.sin(a) * ry), (cx + math.cos(a) * (rx + 0.7), cy + math.sin(a) * (ry + 0.7))], RAG_L, 0.08, 150)
    # Рана на боку: дыра в рубахе до рёбер, потёк вниз.
    p.ellipse(22.6, 9.6, 2.9, 3.1, mul(RAG_D, 0.8), 104)
    p.ellipse(22.6, 9.6, 2.5, 2.7, BLOOD_D, 86)
    p.ellipse(22.6, 9.7, 1.9, 2.1, rgb("3A0E12"), 70)
    for i in range(4):
        ry_ = 7.9 + i * 1.15
        half = 2.0 - abs(i - 1.5) * 0.45
        p.line([(22.6 - half, ry_ + 0.2), (22.6, ry_ - 0.1), (22.6 + half, ry_ + 0.2)], BONE, 0.42, 150)
        p.line([(22.6 - half, ry_ + 0.42), (22.6, ry_ + 0.12), (22.6 + half, ry_ + 0.42)], BONE_D, 0.12, 120)
    for dx, ln in ((-1.2, 4.6), (0.2, 6.0), (1.3, 3.4)):
        p.line([(22.6 + dx, 12.0), (22.7 + dx, 12.0 + ln)], BLOOD_D, 0.34, 122)
        p.ellipse(22.7 + dx, 12.0 + ln, 0.26, 0.34, BLOOD)
    _tint(p, 18, 6, 9, 9, BLOOD_D, lambda gx, gy: 0.5 * np.clip(_blob(22.6, 10.2, 4.0, 4.2)(gx, gy) - 0.25, 0, 1))
    # Потёк ото рта на груди.
    _tint(p, 11, 2.5, 6, 9, BLOOD_D, lambda gx, gy: 0.85 * np.clip(_blob(14.3, 5.2, 1.3, 1.9)(gx, gy) * 1.5 - 0.3 + 0.15 * np.sin(gx * 5.0 + gy * 3.0), 0, 1))
    for dx, ln in ((-0.5, 2.2), (0.3, 4.0), (0.9, 1.6)):
        p.line([(14.3 + dx, 6.4), (14.35 + dx, 6.4 + ln)], BLOOD_D, 0.26, 122)
    _blood(p, 2, 3, 12, 9, 3, 0.6, 2.0)
    p.wrinkles(0, 4, 32, 11, 12, 3.2, 0.4, 0.84, 24)
    p.stains(0, 3, 32, 13, 14, 1.5, 0.76)
    p.speckle(0, 2, 32, 14, 110, LEATHER, 0.1)
    # Штаны под рубахой, рваный подол клочьями поверх них, верёвка вместо ремня.
    p.rect(0, 15.2, 32, 6.8, LEATHER, 128)
    p.twill(0, 15.2, 32, 6.8, 0.42, 0.08, 12.0)
    p.uneven(0, 15.2, 32, 6.8, 0.1, 2.6)
    p.line([(0, 18.4), (8, 18.7), (16, 18.3), (24, 18.7), (32, 18.4)], rgb("B8A070"), 0.5, 160)
    p.stitch([(0, 18.4), (8, 18.7), (16, 18.3), (24, 18.7), (32, 18.4)], LEATHER_D, 0.14, 0.4)
    p.stains(0, 15.2, 32, 6.8, 6, 1.3, 0.78)
    _ragged(p, 0, 15.4, 32, mul(RAG, 0.92), 0.6, 3.4, 1.1, 140)
    _ragged(p, 0, 15.2, 32, RAG, 0.2, 1.6, 0.8, 144)
    p.shade_v(0, 1.6, 32, 16, 1.05, 0.86)
    p.shade_round(0, 0, 32, 22, 0.72)
    # Голова: проплешина и клочья волос, надбровья, выкаченный белый глаз, пустая глазница,
    # провал носа, кривой рот с зубами и порванной щекой, кровь по подбородку, укус на шее.
    hv = _hv(*WALKER_HEAD)
    _rot_skin(p, 32, 0, 32, 20)
    gx, gy = p._grid(32, 0, 32, 5)
    p._apply(32, 0, 32, 5, (1.0 + 0.14 * np.clip(1.0 - gy / 5.0, 0, 1) * np.exp(-(((gx - 48) / 7.0) ** 2))).astype(np.float32))
    for i in range(120):
        x = 32 + p.rng.uniform(0, 32)
        back = abs(x - 48) / 16.0
        if p.rng.uniform(0, 1) > 0.12 + back ** 1.5:
            continue
        ln = p.rng.uniform(1.5, 3.5) + 6.0 * back ** 2
        p.line([(x, 0), (x + p.rng.uniform(-0.5, 0.5), ln * 0.6), (x + p.rng.uniform(-0.9, 0.9), ln)],
               mul(HAIR, p.rng.uniform(0.8, 1.5)), p.rng.uniform(0.12, 0.3), 140)
    p.line([(42.4, 3.4), (44.0, 4.4), (43.6, 5.3)], mul(ROT_D, 0.8), 0.2, 100)
    brow = hv(1.676)
    ey = hv(1.642)
    for sx in (-1.0, 1.0):
        ex = 48 + sx * 3.0
        p.fold([(48 + sx * 0.8, brow + 0.3 - sx * 0.2), (ex, brow - 0.4), (48 + sx * 5.6, brow + 0.5 + sx * 0.2)], 0.7, 0.7, 40)
        p.ellipse(ex, ey, 2.0, 1.55, mul(ROT_D, 0.7), 92)
        p.ellipse(48 + sx * 8.2, hv(1.625), 0.9, 1.5, mul(ROT, 0.88), 142)
        p.ellipse(48 + sx * 8.2, hv(1.625), 0.4, 0.9, ROT_D, 116)
        # Впалые щёки и скулы.
        p.fold([(48 + sx * 6.2, hv(1.625)), (48 + sx * 5.0, hv(1.585)), (48 + sx * 3.9, hv(1.545))], 0.8, 0.72, 34)
        p.fold([(48 + sx * 3.4, hv(1.62)), (48 + sx * 5.4, hv(1.612))], 0.3, 0.84, 18)
    p.ellipse(45.0, ey, 1.4, 1.22, BONE, 140)
    p.ellipse(45.2, ey + 0.2, 0.3, 0.3, BLACK)
    for a in (0.4, 1.6, 2.7, 3.8, 5.2):
        p.line([(45.0 + math.cos(a) * 1.3, ey + math.sin(a) * 1.1), (45.0 + math.cos(a + 0.3) * 0.6, ey + math.sin(a + 0.3) * 0.5)], BLOOD, 0.07)
    p.ellipse(51.0, ey, 1.45, 1.2, rgb("120A0C"), 60)
    p.line([(50.3, ey + 0.9), (50.5, ey + 2.6), (50.2, ey + 3.6)], BLOOD_D, 0.3, 120)
    p.line([(51.5, ey + 1.0), (51.6, ey + 1.9)], BLOOD_D, 0.2, 120)
    p.line([(54.4, ey - 1.6), (55.2, ey), (54.6, ey + 1.4)], mul(ROT_D, 0.8), 0.18, 104)
    nose = hv(1.602)
    p.poly([(47.4, ey - 0.2), (48.6, ey - 0.2), (49.2, nose + 0.5), (46.8, nose + 0.5)], ROT_D, 112)
    p.ellipse(47.5, nose, 0.42, 0.7, rgb("120A0C"), 64)
    p.ellipse(48.5, nose, 0.42, 0.7, rgb("120A0C"), 64)
    mouth = hv(1.562)
    lips = [(44.4, mouth - 0.2), (48, mouth - 0.7), (51.6, mouth - 0.9), (54.0, mouth - 1.6), (54.2, mouth - 0.4),
            (52.0, mouth + 0.6), (50.4, mouth + 1.5), (45.4, mouth + 1.2)]
    p.poly([(qx + (qx - 49) * 0.07, qy + (qy - mouth) * 0.28) for qx, qy in lips], mul(ROT_D, 0.6), 104)
    p.poly(lips, rgb("160A0C"), 64)
    for i in range(9):
        if i in (2, 6):
            continue
        tx = 45.0 + i * 1.02
        ty = mouth - 0.5 - max(0, i - 5) * 0.32
        p.rect(tx, ty, 0.74, 0.7 + (i % 3) * 0.14, BONE if i % 2 else BONE_D, 150)
    for i in range(6):
        if i == 3:
            continue
        tx = 45.9 + i * 0.86
        p.rect(tx, mouth + 0.5 - (i % 2) * 0.1, 0.6, 0.6, BONE_D, 148)
    p.poly([(46.2, mouth + 1.3), (49.6, mouth + 1.5), (49.0, mouth + 3.2), (47.6, hv(1.5)), (47.0, mouth + 3.0)], BLOOD, 120)
    p.line([(47.7, mouth + 2.6), (47.8, 20.0)], BLOOD_D, 0.4, 122)
    p.line([(49.0, mouth + 2.0), (49.3, mouth + 3.6)], BLOOD_D, 0.24, 122)
    p.fold([(40.6, hv(1.512)), (48, hv(1.502)), (55.4, hv(1.512))], 0.8, 0.68, 26)
    for sx in (-1.0, 1.0):
        p.fold([(48 + sx * 2.6, hv(1.505)), (48 + sx * 3.0, 20.0)], 0.5, 0.76, 34)
        p.fold([(48 + sx * 7.5, hv(1.52)), (48 + sx * 7.0, 20.0)], 0.4, 0.82, 26)
    p.ellipse(56.4, hv(1.488), 1.5, 1.0, BLOOD_D, 92)
    p.ellipse(56.4, hv(1.488), 1.0, 0.6, rgb("3A0E12"), 76)
    for i in range(5):
        p.ellipse(55.2 + i * 0.6, hv(1.488) - 0.95 + abs(i - 2) * 0.18, 0.13, 0.13, BONE_D)
    p.line([(56.2, hv(1.488) + 0.8), (56.4, 20.0)], BLOOD_D, 0.26, 120)
    _veins(p, 33, hv(1.64), 6, 5, 2, mul(ROT_D, 0.88))
    _veins(p, 57, hv(1.64), 6, 5, 2, mul(ROT_D, 0.88))
    p.shade_round(32, 0, 32, 20, 0.8)
    # Рука: рваный рукав до локтя, голое предплечье с жилами и укусом, когтистая кисть.
    _rot_skin(p, 0, 22, 16, 26)
    _veins(p, 0, 31, 16, 10, 5, mul(ROT_D, 0.88))
    p.ellipse(11.2, 36.0, 1.6, 1.15, BLOOD_D, 92)
    p.ellipse(11.2, 36.0, 1.05, 0.7, rgb("3A0E12"), 76)
    for i in range(5):
        p.ellipse(10.0 + i * 0.6, 34.95 + abs(i - 2) * 0.16, 0.13, 0.13, BONE)
        p.ellipse(10.0 + i * 0.6, 37.05 - abs(i - 2) * 0.16, 0.13, 0.13, BONE)
    p.line([(11.0, 37.0), (11.2, 39.4)], BLOOD_D, 0.26, 120)
    p.line([(3.0, 34.2), (5.2, 35.6)], rgb("3A0E12"), 0.2, 96)
    p.line([(2.6, 36.2), (4.6, 37.4)], rgb("3A0E12"), 0.16, 96)
    p.rect(0, 22, 16, 8.4, RAG, 134)
    p.weave(0, 22, 16, 8.4, 0.44, 0.07, 14.0)
    _ragged(p, 0, 30.4, 16, mul(RAG, 0.92), 0.8, 3.6, 1.0, 138)
    _ragged(p, 0, 30.2, 16, RAG, 0.3, 1.8, 0.8, 142)
    p.fold([(0, 23.3), (16, 23.3)], 0.3, 0.74, 34)
    p.wrinkles(0, 24, 16, 6, 6, 2.6, 0.3, 0.84, 24)
    p.stains(0, 22, 16, 9, 6, 1.2, 0.76)
    _blood(p, 1, 23.5, 14, 6, 2, 0.6, 2.2)
    p.speckle(0, 22, 16, 9, 40, LEATHER, 0.09)
    p.fold([(0, 41.4), (16, 41.4)], 0.35, 0.74, 34)
    _tint(p, 0, 41.4, 16, 6.6, ROT_D, lambda gx, gy: 0.55 * np.clip((gy - 42.0) / 5.0, 0, 1))
    for fx in (5.2, 7.0, 8.8, 10.6):
        p.ellipse(fx + 0.9, 45.0, 0.5, 0.3, mul(ROT, 0.8), 140)
    p.fold([(0, 44.0), (16, 44.0)], 0.35, 0.84, 18)
    _fingers(p, mul(ROT_D, 0.6), 0.24)
    p.rect(0, 47.0, 16, 1.0, BLACK, 150)
    for fx in (5.2, 7.0, 8.8, 10.6):
        p.rect(fx - 0.16, 46.4, 0.32, 1.6, mul(ROT_D, 0.7))
    p.shade_round(0, 22, 16, 26, 0.74)
    # Нога: бурые штаны с дырой на колене, рваная кромка у голени, голая голень, ссадины.
    _rot_skin(p, 16, 22, 20, 34)
    _veins(p, 16, 46, 20, 9, 5, mul(ROT_D, 0.88))
    p.line([(20.5, 49.2), (23.2, 50.2)], rgb("3A0E12"), 0.24, 96)
    p.line([(20.9, 50.4), (22.8, 51.2)], BLOOD_D, 0.18, 110)
    _tint(p, 16, 50, 20, 6, LEATHER_D, lambda gx, gy: 0.6 * np.clip((gy - 52.0) / 4.0 + 0.2 * np.sin(gx * 2.6), 0, 1))
    p.fold([(16, 54.4), (36, 54.4)], 0.4, 0.74, 30)
    p.rect(16, 22, 20, 22.6, LEATHER, 132)
    p.twill(16, 22, 20, 22.6, 0.42, 0.08, 14.0)
    p.uneven(16, 22, 20, 22.6, 0.1, 3.0)
    _ragged(p, 16, 44.6, 20, mul(LEATHER, 0.86), 0.8, 4.0, 1.1, 136)
    _ragged(p, 16, 44.4, 20, LEATHER, 0.3, 2.0, 0.9, 140)
    p.fold([(16, 22.3), (36, 22.3)], 0.4, 0.7, 30)
    p.fold([(26, 22.4), (26.2, 44.0)], 0.25, 0.82, 22)
    p.stitch([(25.4, 22.6), (25.6, 43.6)], LEATHER_L, 0.08, 0.5)
    p.ellipse(29.4, 39.2, 2.5, 2.0, LEATHER_D, 104)
    p.ellipse(29.4, 39.2, 2.1, 1.6, ROT, 96)
    p.ellipse(29.8, 39.5, 1.0, 0.7, ROT_D, 92)
    for i in range(7):
        a = p.rng.uniform(0, 6.28)
        p.line([(29.4 + math.cos(a) * 2.0, 39.2 + math.sin(a) * 1.5), (29.4 + math.cos(a) * 2.9, 39.2 + math.sin(a) * 2.3)], LEATHER_L, 0.08, 150)
    p.rect(18.6, 27.4, 4.0, 3.6, mul(LEATHER, 0.8), 142)
    p.stitch([(18.6, 27.4), (22.6, 27.4), (22.6, 31.0), (18.6, 31.0), (18.6, 27.4)], BONE_D, 0.1, 0.5)
    p.wrinkles(16, 24, 20, 12, 9, 3.4, 0.5, 0.86)
    for fy in (37.0, 41.4):
        p.fold([(18, fy), (22, fy + 0.5), (25, fy)], 0.5, 0.82, 26)
    p.stains(16, 30, 20, 14, 10, 1.5, 0.74)
    _blood(p, 17, 31, 9, 8, 2, 0.6, 2.4)
    p.shade_v(16, 22, 20, 34, 1.03, 0.88)
    p.shade_round(16, 22, 20, 34, 0.74)
    # Босая стопа: пальцы с тёмными ногтями, грязь снизу.
    _rot_skin(p, 40, 24, 12, 6)
    p.fold([(40, 25.3), (46, 25.7), (52, 25.3)], 0.35, 0.8, 24)
    for i in range(6):
        tx = 43.2 + i * 1.12
        p.line([(tx, 27.2), (tx, 29.6)], mul(ROT_D, 0.7), 0.16, 104)
    for i in range(5):
        tx = 43.76 + i * 1.12
        p.ellipse(tx, 28.5, 0.3, 0.36, mul(ROT_D, 0.55), 150)
    _tint(p, 40, 24, 12, 6, LEATHER_D, lambda gx, gy: 0.85 * np.clip((gy - 28.4) / 1.4 + 0.25 * np.sin(gx * 3.3), 0, 1))
    p.shade_round(40, 24, 12, 6, 0.72)
    p.rect(54, 24, 6, 6, mul(ROT_D, 0.8), 128)
    p.rect(54, 32, 6, 6, ROT_D, 128)
    # Лохмотья у пояса: серая ткань, пятна, кровь, рваный конец с дырами.
    p.rect(40, 34, 12, 8, RAG, 128)
    p.weave(40, 34, 12, 8, 0.44, 0.07, 14.0)
    p.wrinkles(40, 34, 12, 8, 6, 3.0, 0.6, 0.82)
    p.stains(40, 34, 12, 8, 7, 1.0, 0.74)
    _blood(p, 40, 34, 12, 5, 2, 0.6, 2.0)
    p.cut_ellipse(43.4, 37.6, 0.7, 0.9)
    p.cut_ellipse(48.8, 36.2, 0.6, 0.6)
    for i in range(7):
        _cut_poly(p, [(40.2 + i * 1.7, 42.1), (41.0 + i * 1.7, 39.4 + (i % 3) * 0.7), (41.7 + i * 1.7, 42.1)])
    # Лопата (кусок полы): слева черенок с обмоткой у рукояти, справа штык с ребром, ржавчиной
    # и кровью на острие; вокруг штыка прозрачно.
    p.rect(36, 44, 28, 20, STEEL_D, 128)
    p.wood(36, 44, 5, 20, 1, True, LEATHER, 0.1)
    p.shade_round(36, 44, 5, 20, 0.6, 1.6)
    for i in range(7):
        p.line([(36, 44.6 + i * 0.7), (41, 45.0 + i * 0.7)], RAG_D if i % 2 else mul(RAG_D, 0.75), 0.4, 150)
    p.stains(36, 50, 5, 14, 5, 0.9, 0.74)
    p.rect(36, 62.2, 5, 1.8, STEEL_D, 160)
    shape = [(47.7, 44), (50.3, 44), (50.5, 47.2), (53.6, 47.6), (55.5, 48.6), (55.7, 52.6), (54.2, 55.6), (49, 58),
             (43.8, 55.6), (42.3, 52.6), (42.5, 48.6), (44.4, 47.6), (47.5, 47.2)]
    p.rect(42, 44, 14, 14, STEEL_D, 128)
    p.poly(shape, STEEL, 150)
    p.grain(42, 44, 14, 14, 0.07, 1.0, 8.0)
    p.line([(49, 44.2), (49, 53.6)], STEEL_L, 0.6, 170)
    p.line([(48.4, 44.2), (48.4, 53.0)], STEEL_D, 0.16, 120)
    p.line([(42.6, 52.7), (44.0, 55.5), (49, 57.8), (54.0, 55.5), (55.4, 52.7)], STEEL_L, 0.34, 164)
    p.rect(47.7, 46.2, 2.6, 0.5, STEEL_D, 150)
    p.ellipse(49, 45.2, 0.3, 0.3, STEEL_D, 110)
    _tint(p, 42, 44, 14, 14, RUST, lambda gx, gy: 0.75 * np.clip(_blob(45.0, 50.0, 2.2, 2.6)(gx, gy) + _blob(53.4, 53.0, 1.8, 2.2)(gx, gy) - 0.25, 0, 1))
    p.speckle(42.5, 47.5, 13, 9, 60, RUST, 0.1)
    _tint(p, 42, 51, 14, 7, BLOOD_D, lambda gx, gy: 0.9 * np.clip((gy - 55.2) / 1.6 + 0.5 * np.sin(gx * 2.3) + 0.25 * np.sin(gx * 5.9), 0, 1))
    p.line([(47.2, 55.0), (47.0, 52.4)], BLOOD_D, 0.24)
    p.line([(51.0, 54.6), (51.1, 53.0)], BLOOD_D, 0.2)
    p.cut(42, 44, 14, 14)
    p.solid(shape)
    # Клок волос: пряди от корня (верх куска) к концам, между ними прозрачно.
    x, y, w, h = EXTRA_A
    p.rect(x, y, w, h, HAIR, 128)
    p.cut(x, y, w, h)
    for i in range(11):
        bx = x + 0.5 + i * 0.86
        tip = (bx + p.rng.uniform(-1.0, 1.0), y + p.rng.uniform(3.0, 7.8))
        p.poly([(bx - 0.45, y), (bx + 0.45, y), tip], mul(HAIR, p.rng.uniform(0.8, 1.5)), 140)
        p.solid([(bx - 0.45, y), (bx + 0.45, y), tip])
    p.solid([(x, y), (x + w, y), (x + w, y + 0.8), (x, y + 0.8)])
    # Макушка: проплешина с редкими волосками.
    p.rect(*CROWN, mix(ROT, ROT_L, 0.5), 128)
    p.speckle(*CROWN, 14, HAIR, 0.12)
    p.rect(0, 48, 16, 16, RAG_D, 128)
    return p


def zombies_walker():
    """Зомби-ходок: худой, голова завалена на плечо, рубаха и штаны в лохмотьях, босой; лохмотья
    у пояса на пружине, в правой руке лопата могильщика."""
    p = paint_walker()
    reg = regions(p)
    r, _ = rm.build_body("enemy", reg, bulk=0.94, limb=0.78, leg="straight")
    # Голова: узкая челюсть, впалые щёки, завалена на плечо и вперёд.
    head_tube(r, reg, [(1.45, 0.055, 0.058), (1.5, 0.05, 0.054), (1.525, 0.064, 0.072), (1.555, 0.08, 0.09),
                       (1.59, 0.092, 0.104), (1.63, 0.101, 0.113), (1.67, 0.104, 0.116), (1.71, 0.098, 0.11),
                       (1.74, 0.08, 0.09), (1.76, 0.046, 0.052)], WALKER_HEAD[1], WALKER_LEAN)
    # Клок волос на темени: две скрещённые ленты с прядями.
    lx, lz = WALKER_LEAN
    pts = [(lx * 0.235 + 0.01 * i, 1.73 + 0.024 * i, -0.005 + lz * 0.235 + 0.012 * i) for i in range(4)]
    for direction in ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)):
        r.strip(pts, direction, 0.055, p.region(*EXTRA_A), lambda t: [("head", 1.0)], 0.0, 0.4, 0.0)
    # Лохмотья рубахи у пояса: два хвоста на пружинной кости.
    r.bone("sash", "hips", (-0.1, 0.98, 0.07))
    r.spring("sash", 40.0, 5.0, 1.0)
    for dx, lean in ((-0.13, -0.03), (-0.07, 0.03)):
        pts = [(dx + lean * i, 0.99 - 0.06 * i, 0.09 + 0.012 * i) for i in range(6)]
        r.strip(pts, (1.0, 0.0, 0.0), 0.034, reg["strip"], lambda t: [("hips", 1.0 - t), ("sash", t)] if t < 1.0 else [("sash", 1.0)], 0.2)
    # Лопата в правой руке: жёсткая, штык вперёд. Черенок из двух скрещённых лент, поперечная
    # рукоять сзади, штык одной лентой наискось, чтобы читался и сбоку, и сверху.
    hand_x = 0.228 * 0.94 * 1.058
    hand = lambda t: [("hand_r", 1.0)]
    shaft = p.region(36, 44, 5, 20)
    pts = [(hand_x, 0.795 + 0.0125 * i, 0.17 - 0.2 * i) for i in range(4)]
    for direction in ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0)):
        r.strip(pts, direction, 0.016, shaft, hand, 0.0, 0.0, 0.0)
    r.strip([(hand_x - 0.055, 0.795, 0.17), (hand_x + 0.055, 0.795, 0.17)], (0.0, 0.7, 0.7), 0.016, p.region(36, 44, 5, 5), hand, 0.0, 0.0, 0.0)
    pts = [(hand_x, 0.829 + 0.006 * i, -0.4 - 0.1 * i) for i in range(4)]
    r.strip(pts, (0.6, 0.8, 0.0), 0.088, p.region(42, 44, 14, 14), hand, 0.0, 0.0, 0.0)
    return r, p


RIGS = [zombies_survivor, zombies_butcher, zombies_walker]


if __name__ == "__main__":
    made = []
    for make in RIGS:
        rig, paint = make()
        color, normal = paint.finish()
        made.append((rig, color))
        print("%-8s костей %d, вершин %d, треугольников %d, пружинных костей %d" % (
            rig.name, len(rig.bones), len(rig.verts), len(rig.tris), len(rig.springs)))
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_rigs(sys.argv[sys.argv.index("--preview") + 1], made)
