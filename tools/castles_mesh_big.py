#!/usr/bin/env python3
"""Крупный реквизит и транспорт «Замков» для low poly и «продвинутых» (#137): зеркала моделей
космоса из `space_mesh_big.py` (а те зеркала пиратских из `lowpoly_meshes.py`) с теми же именами
слотов, частей и точками вращения, тем же нулём и габаритами, чтобы десять 3D-демок работали
без правок. Цвета из основы 16/32 (`castles16.PALETTE`) через `castles_mesh_chars`.

  cannon      баллиста на колёсном станке (болт смотрит в −Z, как ствол пушки)
  palm        дуб; атлас: слева кора ствола, справа ветка листвы с вырезом по прозрачности
              (эти же половины берёт `ThreedScreen.add_palm`)
  flag        знамя с гербом: части `pole` и `cloth`
  lighthouse  сторожевая башня с зубцами и красным шатром, высота маяка
  cart        боевая повозка на четырёх колёсах: `body`, оси `axle_f`, `axle_r`; без мачты и
              паруса (#137), сзади будка возницы с гербовой попоной, на крыше флажок 0.3 м
  cart_rival  повозка чужого герба: те же части, чёрный борт, частокол, шип-таран, будка
  pistol      арбалет в латной перчатке, вид от первого лица
  hoop        турнирное кольцо с лентами на гербовом щите; кольцо там же и того же размера

    python3 tools/castles_mesh_big.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from lowpoly_meshes import Atlas, Model, at, box, flip, loft, mul, quad, rgb, rot  # noqa: E402
from castles_mesh_chars import (BLACK, CRIMSON, CRIMSON_D, CRIMSON_L, GOLD, GOLD_D, IRON, IRON_D,  # noqa: E402
                                IRON_L, RED, RED_D, RED_L, STEEL, STEEL_D, STEEL_L)

# Остальные цвета набора из той же палитры: дерево, камень кладки, зелень, синий герба.
WOOD, WOOD_D, WOOD_L = rgb("9C642C"), rgb("5E3A1C"), rgb("C08A48")
TAR, TAR_L = rgb("2E2622"), rgb("4A3E38")
STONE, STONE_D, STONE_L = rgb("8C8A8C"), rgb("4E5060"), rgb("B4B8C4")
GREEN, GREEN_D, GREEN_L = rgb("5CAE4A"), rgb("2A6A3E"), rgb("8ED060")
BLUE, BLUE_D = rgb("4676C0"), rgb("273B76")
WHITE = rgb("E8ECF2")
ROPE = rgb("D8C08C")


def boards(a, x, y, w, h, base, width=4, vertical=False):
    """Доски: у каждой свой тон, тёмная щель, светлое волокно, редкие сучки."""
    span = w if vertical else h
    for k in range(0, span, width):
        tone = a.rng.uniform(0.88, 1.1)
        for j in range(h):
            for i in range(w):
                pos, run = (i, j) if vertical else (j, i)
                if k <= pos < k + width:
                    c = mul(base, tone * (1.0 + 0.05 * math.sin(run * 1.3 + k)))
                    if pos == k:
                        c = mul(base, 0.55)
                    elif pos == k + 1:
                        c = mul(base, tone * 1.14)
                    a.px(x + i, y + j, c)
    for _ in range(max(1, w * h // 70)):
        a.px(x + a.rng.randrange(w), y + a.rng.randrange(h), mul(base, 0.6))
    a.noise(x, y, w, h, 0.06)


def masonry(a, x, y, w, h, base, bw=8, bh=4):
    """Кладка вперевязку: тёсаные блоки разного тона, тёмный шов снизу и справа, светлая грань."""
    for row, j in enumerate(range(0, h, bh)):
        off = (row % 2) * (bw // 2)
        for i in range(-off, w, bw):
            tone = a.rng.uniform(0.86, 1.1)
            for yy in range(j, min(j + bh, h)):
                for xx in range(max(i, 0), min(i + bw, w)):
                    c = mul(base, tone)
                    if yy == j + bh - 1 or xx == i + bw - 1:
                        c = mul(base, 0.52)
                    elif yy == j:
                        c = mul(base, tone * 1.16)
                    a.px(x + xx, y + yy, c)
    a.noise(x, y, w, h, 0.07)


def strap(a, x, y, w, h, c=IRON):
    """Железная полоса с заклёпками."""
    a.rect(x, y, w, h, c)
    if w >= h:
        a.rect(x, y, w, 1, mul(c, 1.45))
        for i in range(1, w, 4):
            a.px(x + i, y + h // 2, IRON_L)
    else:
        a.rect(x, y, 1, h, mul(c, 1.45))
        for j in range(1, h, 4):
            a.px(x + w // 2, y + j, IRON_L)


def crest(a, x, y):
    """Герб основы 16/32: золотой щит 7×8 с синим крестом, тёмная кромка снизу."""
    for row, (x0, x1) in enumerate(((0, 6), (0, 6), (0, 6), (0, 6), (0, 6), (1, 5), (2, 4), (3, 3))):
        for i in range(x0, x1 + 1):
            a.px(x + i, y + row, GOLD if i not in (x0, x1) or row < 5 else GOLD_D)
    a.rect(x + 3, y, 1, 7, BLUE)
    a.rect(x, y + 2, 7, 1, BLUE)


def rook(a, x, y, c):
    """Чужой герб: башня-ладья 7×8 с тремя зубцами."""
    for i in (0, 3, 6):
        a.rect(x + i, y, 1, 2, c)
    a.rect(x, y + 2, 7, 1, c)
    a.rect(x + 1, y + 3, 5, 4, c)
    a.rect(x, y + 7, 7, 1, c)
    a.px(x + 3, y + 5, BLACK), a.px(x + 3, y + 6, BLACK)


def paint_wheel(a, x0, y0, rival=False):
    """Колесо 16×16. Своё: железная шина с гвоздями, деревянный обод, восемь спиц, ступица.
    Чужое: глухой диск из тёмных досок с железным крестом и багровой ступицей. Вокруг прозрачно."""
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            ang = math.atan2(j - 7.5, i - 7.5)
            if d > 7.7:
                a.clear(x0 + i, y0 + j)
                continue
            if d > 6.3:
                c = IRON_L if int((ang + math.pi) * 8 / math.pi + 0.5) % 2 == 0 and d < 7.2 else IRON
            elif rival:
                if d < 1.8:
                    c = CRIMSON_L if d < 0.9 else CRIMSON
                elif min(abs(i - 7.5), abs(j - 7.5)) < 1.0:
                    c = IRON_L if int(d) % 2 == 0 else IRON
                else:
                    c = TAR if i % 3 == 0 else TAR_L
            elif d > 4.7:
                c = WOOD_D if abs(math.sin(ang * 2.0 + 0.4)) < 0.16 else (WOOD_L if d > 5.6 else WOOD)
            elif d < 1.0:
                c = GOLD
            elif d < 2.3:
                c = IRON if d > 1.6 else IRON_L
            else:
                c = WOOD_L if abs(math.sin(ang * 4.0)) < 0.42 else mul(WOOD_D, 0.45)
            a.px(x0 + i, y0 + j, c)
    return a.region(x0, y0, 16, 16)


def beam(p0, p1, t, region, cap=None, w=None):
    """Брус от точки до точки: сечение `w`×`t` (ширина поперёк, толщина по высоте), развёртка
    лентой вокруг, длина по вертикали куска."""
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    tris = rot(box((t, length, t if w is None else w), region, cap, cap), rz=-90.0)
    tris = rot(tris, rz=math.degrees(math.atan2(dy, math.hypot(dx, dz))))
    tris = rot(tris, ry=math.degrees(math.atan2(-dz, dx)))
    return at(tris, (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0, (p0[2] + p1[2]) / 2.0)


def wedge(depth, back, front, region, cap=None):
    """Клин носом в −Z: сечение `back` (ширина, высота) у нуля сужается до `front` на `depth`."""
    k = math.sqrt(2.0) / 2.0
    return rot(loft([(0.0, back[0] * k, back[1] * k), (depth, front[0] * k, front[1] * k)], region, 4, math.pi / 4.0,
                    (None, cap), True), rx=-90.0)


def castles_cannon():
    """Баллиста: дубовый станок на двух колёсах, ложе с болтом, рама с торсионами и плечи лука,
    отведённые назад тетивой, сзади ворот. Болт лежит на месте ствола и смотрит в −Z."""
    a = Atlas(64, 32, 219)
    # Ложе: продольные доски, три железных обруча, жёлоб под болт.
    boards(a, 0, 0, 32, 12, WOOD_L, 4)
    for x in (0, 8, 16, 24):
        for dx in (2, 6):
            strap(a, x + dx, 0, 1, 12)
    a.shade(0, 0, 32, 12, 1.1, 0.8, 1.0)
    stock = a.region(0, 0, 32, 12)
    # Станок: четыре грани по 8, на передней герб, по кромкам оковка.
    boards(a, 0, 12, 32, 16, WOOD, 4, True)
    strap(a, 0, 12, 32, 2), strap(a, 0, 25, 32, 3)
    for x in (0, 8, 16, 24):
        a.rect(x, 12, 1, 16, WOOD_D)
    for x in (0, 16):
        a.rect(x + 3, 17, 2, 5, BLACK), a.px(x + 3, 16, BLACK), a.px(x + 4, 16, BLACK)
    a.rect(8, 15, 8, 9, RED), a.rect(8, 15, 8, 1, RED_L)
    crest(a, 8, 15)
    a.rect(26, 16, 4, 6, IRON), a.rect(27, 17, 2, 4, IRON_L)
    a.shade(0, 12, 32, 16, 1.08, 0.8, 1.0)
    body = a.region(0, 12, 32, 16)
    # Болт: сверху стальной наконечник, ниже ясеневое древко с обмоткой.
    a.rect(32, 0, 8, 4, STEEL_L), a.rect(32, 2, 8, 2, STEEL)
    a.rect(32, 4, 8, 4, STEEL_D), a.rect(32, 4, 8, 1, IRON)
    a.rect(32, 8, 8, 8, WOOD_L)
    for y in (9, 14):
        a.rect(32, y, 8, 1, RED)
    a.rect(32, 11, 8, 1, WOOD)
    bolt = a.region(32, 0, 8, 16)
    disc = paint_wheel(a, 40, 0)
    a.rect(56, 0, 8, 4, IRON), a.rect(56, 1, 8, 1, IRON_L)
    for x in range(57, 64, 3):
        a.px(x, 2, STEEL)
    rim = a.region(56, 0, 8, 4)
    strap(a, 56, 4, 8, 4)
    iron = a.region(56, 4, 8, 4)
    # Тетива: кручёный канат.
    for y in range(8):
        for x in range(8):
            a.px(56 + x, 8 + y, ROPE if (x + y) % 3 else mul(ROPE, 0.6))
    rope = a.region(56, 8, 8, 8)
    # Оперение болта: красное перо с бородками, край вырезан.
    for y in range(6):
        for x in range(8):
            if y <= x * 0.9 + 1:
                a.px(32 + x, 16 + y, RED if (x + y) % 2 else RED_D)
    a.rect(32, 21, 8, 1, WOOD_L)
    feather = a.region(32, 16, 8, 6)
    # Плечи лука: светлый тис с обмоткой жилами и стальным наконечником.
    a.rect(40, 16, 16, 12, rgb("D8B070"))
    for x in range(40, 56, 4):
        a.rect(x, 16, 1, 12, rgb("A87C40"))
        a.rect(x + 1, 16, 1, 12, rgb("ECD090"))
    for y in (18, 19, 24):
        a.rect(40, y, 16, 1, ROPE if y != 19 else mul(ROPE, 0.7))
    a.rect(40, 16, 16, 1, STEEL_L), a.rect(40, 27, 16, 1, IRON)
    a.noise(40, 16, 16, 12, 0.05)
    limb = a.region(40, 16, 16, 12)
    m = Model("cannon", a)
    side = lambda x: at(rot(loft([(-0.04, 0.24, 0.24), (0.04, 0.24, 0.24)], rim, 8, caps=(disc, disc), flat=True), rz=90.0),
                        x, 0.24, 0.2)
    y = 0.57
    tris = (at(box((0.46, 0.22, 0.85), body, stock, None, (0.8, 1.0)), 0.0, 0.3, 0.1)
            + at(box((0.3, 0.2, 0.3), body, body, None, (0.7, 0.7)), 0.0, 0.1, 0.1)
            + side(-0.28) + side(0.28)
            # Ложе и болт на нём.
            + at(box((0.15, 0.13, 1.08), stock, stock, stock), 0.0, 0.475, -0.1)
            + at(rot(loft([(-0.3, 0.022, 0.022), (0.4, 0.022, 0.022), (0.42, 0.06, 0.03), (0.6, 0.004, 0.004)], bolt, 5),
                     rx=-90.0), 0.0, y, -0.1)
            + quad((0.0, y + 0.08, 0.38), (0.0, y + 0.08, 0.2), (0.0, y, 0.2), (0.0, y, 0.38), feather)
            + quad((0.08, y, 0.38), (0.08, y, 0.2), (0.0, y, 0.2), (0.0, y, 0.38), feather)
            + quad((-0.08, y, 0.38), (-0.08, y, 0.2), (0.0, y, 0.2), (0.0, y, 0.38), feather)
            # Рама торсионов: две стойки и перекладина над болтом.
            + at(box((0.09, 0.36, 0.12), body, iron, iron), -0.17, 0.58, -0.5)
            + at(box((0.09, 0.36, 0.12), body, iron, iron), 0.17, 0.58, -0.5)
            + at(box((0.46, 0.06, 0.14), iron, iron, iron), 0.0, 0.78, -0.5)
            # Ворот с рукоятями.
            + at(rot(loft([(-0.2, 0.045, 0.045), (0.2, 0.045, 0.045)], rope, 6, caps=(iron, iron)), rz=90.0), 0.0, 0.6, 0.4)
            + beam((0.22, 0.48, 0.4), (0.22, 0.72, 0.4), 0.03, iron, iron)
            + beam((-0.22, 0.48, 0.4), (-0.22, 0.72, 0.4), 0.03, iron, iron))
    for s in (-1.0, 1.0):
        # Плечо лука в два колена и тетива от его конца к замку на ложе.
        tris += beam((s * 0.17, y, -0.5), (s * 0.36, y, -0.45), 0.05, limb, limb, 0.06)
        tris += beam((s * 0.35, y, -0.455), (s * 0.5, y, -0.3), 0.04, limb, limb, 0.05)
        tris += beam((s * 0.5, y, -0.3), (0.0, y + 0.01, 0.22), 0.014, rope)
    return m.part("body", (0.0, 0.0, 0.0), tris)


def castles_palm():
    """Дуб: толстый кривой ствол с корнями и широкая округлая крона. Середина кроны это плотный
    ком листвы, из него во все стороны торчат ветки: плоскости с вырезом по прозрачности, как
    листья пальмы. `ThreedScreen.add_palm` кладёт на свои ленты ту же правую половину атласа."""
    a = Atlas(32, 32, 245)
    bark, bark_d, bark_l = rgb("7A5230"), rgb("46301E"), rgb("A07848")
    a.rect(0, 0, 16, 32, bark)
    # Кора: извилистые борозды, светлые гребни, дупло, мох у корней.
    for x in range(0, 16, 3):
        for y in range(32):
            sx = (x + int(round(math.sin(y * 0.45 + x) * 1.1))) % 16
            a.px(sx, y, bark_d)
            a.px((sx + 1) % 16, y, bark_l if y % 5 else bark)
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2)):
        a.px(7 + dx, 12 + dy, BLACK)
    a.px(6, 12, bark_l), a.px(9, 13, bark_l), a.px(7, 15, bark_l)
    for x in range(16):
        for y in range(27 + (x * 7) % 4, 32):
            a.px(x, y, GREEN_D if (x + y) % 3 else GREEN)
    a.shade(0, 0, 16, 32, 0.9, 1.0, 0.72)
    a.noise(0, 0, 16, 32, 0.07)
    trunk = a.region(0, 0, 16, 32)
    # Ветка: гроздь округлых пучков листьев с волнистым краем, свет сверху слева, жёлуди.
    for y in range(32):
        half = 1.0 + 6.4 * math.sin(math.pi * min(y / 30.0, 1.0)) ** 0.5 + 0.9 * math.sin(y * 1.4)
        for x in range(16):
            dx = x - 7.5
            if abs(dx) <= half:
                cx, cy = (x + (y // 5) * 2) % 5, y % 5
                c = GREEN
                if cx + cy <= 1:
                    c = GREEN_L
                elif cx == 4 or cy == 4:
                    c = GREEN_D
                if abs(dx) > half - 1.0 and dx > 0:
                    c = GREEN_D
                a.px(16 + x, y, c)
    for x, y in ((21, 9), (26, 17), (22, 23)):
        a.px(x, y, GOLD), a.px(x, y + 1, WOOD)
    a.noise(16, 0, 16, 32, 0.07)
    leaf = a.region(16, 0, 16, 32)
    core = a.region(20, 7, 8, 18)
    cx, cy, cz = 0.34, 3.5, 0.06
    tris = loft([(0.0, 0.44, 0.44), (0.35, 0.3, 0.3, 0.02, 0.0), (1.5, 0.25, 0.25, 0.12, 0.02), (2.5, 0.22, 0.22, 0.26, 0.04),
                 (3.2, 0.14, 0.14, 0.32, 0.06)], trunk, 6)
    # Два сука под кроной.
    tris += beam((0.2, 2.2, 0.03), (-0.55, 3.0, 0.3), 0.11, trunk)
    tris += beam((0.24, 2.4, 0.04), (0.95, 3.05, -0.35), 0.1, trunk)
    tris += loft([(2.5, 0.45, 0.45, cx, cz), (2.9, 1.12, 1.12, cx, cz), (3.5, 1.32, 1.32, cx, cz), (4.1, 1.0, 1.0, cx, cz),
                  (4.48, 0.4, 0.4, cx, cz)], core, 7, 0.2, caps=(core, core))

    def bough(ang, rise0, reach0, rise1, reach1, w0, w1):
        d = (math.sin(ang), math.cos(ang))
        q = (math.cos(ang), -math.sin(ang))
        near = (cx + d[0] * reach0, cy + rise0, cz + d[1] * reach0)
        far = (cx + d[0] * reach1, cy + rise1, cz + d[1] * reach1)
        return quad((near[0] - q[0] * w0, near[1], near[2] - q[1] * w0), (near[0] + q[0] * w0, near[1], near[2] + q[1] * w0),
                    (far[0] + q[0] * w1, far[1], far[2] + q[1] * w1), (far[0] - q[0] * w1, far[1], far[2] - q[1] * w1), leaf)

    for k in range(8):
        ang = 2.0 * math.pi * k / 8.0 + 0.3
        tris += bough(ang, 0.45, 0.35, -0.75 - 0.14 * (k % 2), 1.9, 0.5, 0.8)
    for k in range(5):
        ang = 2.0 * math.pi * k / 5.0 + 0.9
        tris += bough(ang, 1.12, 0.0, 0.3 + 0.1 * (k % 2), 1.5, 0.35, 0.7)
    return Model("palm", a).part("body", (0.0, 0.0, 0.0), tris)


def castles_flag():
    """Знамя с гербом: красное полотнище с косицами и золотым щитом с синим крестом, древко с
    золотыми кольцами и навершием-копьём, каменная тумба; полотно отдельной частью у древка."""
    a = Atlas(64, 32, 217)
    a.rect(0, 0, 32, 20, RED)
    for y in range(0, 20, 5):
        a.rect(0, y + 3, 32, 1, RED_D)
        a.rect(0, y + 1, 32, 1, RED_L)
    a.rect(0, 0, 32, 1, GOLD), a.rect(0, 19, 32, 1, GOLD)
    a.rect(0, 1, 32, 1, GOLD_D), a.rect(0, 18, 32, 1, GOLD_D)
    a.rect(10, 5, 11, 10, RED)
    crest(a, 12, 6)
    for x in (5, 24):
        a.px(x, 9, GOLD), a.px(x - 1, 10, GOLD), a.px(x + 1, 10, GOLD), a.px(x, 11, GOLD), a.px(x, 10, GOLD_D)
    a.rect(0, 0, 2, 20, GOLD_D), a.rect(1, 0, 1, 20, GOLD)
    # Косицы: клин выреза с вольного края.
    for x in range(26, 32):
        for y in range(20):
            if abs(y - 9.5) < (x - 25) * 1.0:
                a.clear(x, y)
    a.noise(0, 0, 32, 20, 0.07)
    cloth = a.region(0, 0, 32, 20)
    boards(a, 32, 0, 8, 32, WOOD, 4, True)
    for y in (2, 12, 22):
        a.rect(32, y, 8, 2, GOLD), a.rect(32, y + 2, 8, 1, GOLD_D)
    a.shade(32, 0, 8, 32, 1.0, 0.9, 0.6)
    pole = a.region(32, 0, 8, 32)
    masonry(a, 40, 0, 8, 8, STONE, 4, 4)
    base = a.region(40, 0, 8, 8)
    a.rect(48, 0, 8, 8, GOLD)
    a.rect(48, 0, 8, 2, rgb("FFF0A8")), a.rect(48, 6, 8, 2, GOLD_D)
    for x in range(48, 56, 2):
        a.px(x, 4, GOLD_D)
    tip = a.region(48, 0, 8, 8)
    m = Model("flag", a)
    m.part("pole", (0.0, 0.0, 0.0),
           loft([(0.0, 0.05, 0.05), (2.7, 0.04, 0.04)], pole, 4, caps=(None, base))
           + loft([(0.0, 0.26, 0.26), (0.14, 0.18, 0.18)], base, 5, caps=(None, base), flat=True)
           + loft([(2.66, 0.07, 0.07), (2.72, 0.07, 0.07)], tip, 4, caps=(tip, tip), flat=True)
           + loft([(2.72, 0.035, 0.03), (2.8, 0.085, 0.03), (3.0, 0.004, 0.004)], tip, 4, flat=True))
    m.part("cloth", (0.04, 2.3, 0.0),
           quad((0.04, 2.62, 0.0), (1.0, 2.56, 0.0), (1.0, 2.02, 0.0), (0.04, 1.98, 0.0), cloth), "pole")
    return m


def castles_lighthouse():
    """Сторожевая башня: ориентир на горизонте высотой с маяк. Цоколь из валунов во мху,
    восьмигранный ствол тёсаной кладки с дверью, бойницами и гербовым полотнищем, выносной пояс
    с зубцами, красный черепичный шатёр и вымпел на шпиле."""
    a = Atlas(64, 64, 253)
    ph = math.pi / 8.0  # грани смотрят по осям: дверь на грани −Z, столбцы 24..31
    masonry(a, 0, 0, 64, 36, STONE, 8, 4)
    # Дверь с аркой, окно над ней и полотнище с гербом между ними.
    a.rect(25, 26, 6, 10, STONE_D), a.rect(26, 25, 4, 1, STONE_D)
    a.rect(26, 27, 4, 9, WOOD), a.rect(27, 26, 2, 1, WOOD)
    a.rect(28, 27, 1, 9, WOOD_D), a.rect(26, 29, 4, 1, IRON), a.rect(26, 33, 4, 1, IRON)
    a.px(29, 31, GOLD)
    a.rect(26, 4, 4, 5, BLACK), a.rect(27, 3, 2, 1, BLACK), a.rect(25, 9, 6, 1, STONE_L)
    a.rect(25, 11, 6, 10, RED), a.rect(25, 11, 6, 1, GOLD), a.rect(25, 12, 1, 9, RED_D)
    for x in (25, 30):
        a.clear(x, 20)
    a.px(27, 20, RED_D), a.px(28, 20, RED_D)
    a.rect(26, 13, 4, 4, GOLD), a.rect(27, 17, 2, 1, GOLD), a.rect(27, 13, 1, 5, BLUE), a.rect(26, 14, 4, 1, BLUE)
    a.rect(25, 20, 1, 1, STONE), a.rect(30, 20, 1, 1, STONE)
    # Бойницы на остальных гранях в два яруса и пара тёмных окон.
    for f in (0, 1, 2, 4, 5, 6, 7):
        x = f * 8 + 3
        y = 6 if f % 2 == 0 else 22
        a.rect(x, y, 2, 6, BLACK), a.rect(x - 1, y + 2, 4, 1, BLACK), a.rect(x - 1, y + 6, 4, 1, STONE_L)
    # Плющ ползёт от цоколя.
    for x in range(64):
        top = 36 - int(3 + 5 * abs(math.sin(x * 0.37)) * (1.0 if (x // 8) in (0, 1, 5, 6) else 0.25))
        for y in range(top, 36):
            if not 24 <= x <= 31 and (x * 3 + y * 5) % 4:
                a.px(x, y, GREEN_D if (x + y) % 3 else GREEN)
    a.shade(0, 0, 64, 36, 1.06, 0.84, 0.75)
    wall = a.region(0, 0, 64, 36)
    # Выносной пояс: сверху парапет, снизу арочки машикулей.
    masonry(a, 0, 36, 64, 4, STONE_L, 4, 4)
    a.rect(0, 36, 64, 1, WHITE)
    a.rect(0, 40, 64, 4, STONE)
    for x in range(0, 64, 4):
        a.rect(x + 1, 41, 2, 3, STONE_D), a.px(x + 1, 41, STONE), a.px(x + 2, 41, STONE)
        a.rect(x + 1, 43, 2, 1, BLACK)
    a.rect(0, 40, 64, 1, STONE_D)
    a.noise(0, 36, 64, 8, 0.05)
    belt = a.region(0, 36, 64, 8)
    # Шатёр: ряды красной черепицы вперевязку, золотой свес.
    for y in range(12):
        for x in range(32):
            sx = x + (y // 3 % 2) * 2
            c = RED_D if y % 3 == 2 or sx % 4 == 0 else (RED_L if y % 3 == 0 and sx % 4 == 1 else RED)
            a.px(x, 44 + y, c)
    a.rect(0, 55, 32, 1, GOLD_D)
    a.shade(0, 44, 32, 12, 1.2, 0.85, 0.8)
    a.noise(0, 44, 32, 12, 0.05)
    roof = a.region(0, 44, 32, 12)
    boards(a, 32, 44, 8, 8, WOOD_D, 3)
    dark = a.region(32, 44, 8, 8)
    masonry(a, 40, 44, 8, 8, STONE_L, 4, 4)
    a.rect(40, 44, 8, 1, WHITE)
    merlon = a.region(40, 44, 8, 8)
    # Вымпел: красный клин с золотой каймой.
    for x in range(16):
        for y in range(8):
            if abs(y - 3.5) <= 4.0 - x * 0.25:
                a.px(48 + x, 44 + y, GOLD if abs(y - 3.5) > 2.8 - x * 0.25 else (RED if x % 5 else RED_D))
    pennant = a.region(48, 44, 16, 8)
    # Цоколь: крупные валуны, мох по низу.
    masonry(a, 0, 56, 64, 8, mul(STONE, 0.82), 8, 4)
    for x in range(64):
        for y in range(62 - (x * 5) % 3, 64):
            a.px(x, y, GREEN_D if (x + y) % 2 else GREEN)
    a.shade(0, 56, 64, 8, 1.1, 0.85, 1.0)
    plinth = a.region(0, 56, 64, 8)
    a.rect(32, 52, 8, 4, GOLD), a.rect(32, 52, 8, 1, rgb("FFF0A8")), a.rect(32, 55, 8, 1, GOLD_D)
    gold = a.region(32, 52, 8, 4)
    tris = (loft([(0.0, 1.5, 1.5), (0.7, 1.32, 1.32)], plinth, 8, ph, caps=(None, merlon), flat=True)
            + loft([(0.7, 1.08, 1.08), (3.4, 1.0, 1.0), (6.2, 0.95, 0.95)], wall, 8, ph)
            + loft([(6.2, 0.95, 0.95), (6.55, 1.27, 1.27), (7.0, 1.27, 1.27)], belt, 8, ph, caps=(None, dark), flat=True)
            + loft([(7.0, 0.86, 0.86), (7.5, 0.86, 0.86)], merlon, 8, ph, flat=True)
            + loft([(7.42, 1.08, 1.08), (8.0, 0.56, 0.56), (8.62, 0.03, 0.03)], roof, 8, ph, caps=(dark, None))
            + loft([(8.5, 0.035, 0.035), (9.0, 0.02, 0.02)], gold, 4)
            + quad((0.0, 8.99, 0.0), (0.95, 8.86, 0.0), (0.95, 8.8, 0.0), (0.0, 8.67, 0.0), pennant))
    for k in range(4):
        ang = math.pi / 4.0 + math.pi / 2.0 * k
        tris += at(rot(box((0.56, 0.36, 0.2), merlon, merlon, None), ry=math.degrees(ang)),
                   math.sin(ang) * 1.07, 7.18, math.cos(ang) * 1.07)
    return Model("lighthouse", a).part("body", (0.0, 0.0, 0.0), tris)


def make_cart(name, rival):
    """Транспорт гонок. Герой: боевая повозка, дубовый кузов с красным поясом и щитами по
    бортам, окованный клин-таран, башенка с зубцами спереди, сзади будка возницы, на её задней стенке
    гербовая попона, на крыше флажок на древке 0.3 м. Соперник: повозка чужого герба, смолёный
    чёрный кузов, шип-таран, частокол вместо башенки, чёрная попона с багровой ладьёй, глухие
    колёса. Паруса и мачты нет: это колёсная повозка, силуэт низкий, как у машины (#137).
    Части и точки вращения как у пиратской повозки: `body`, `axle_f`, `axle_r`."""
    a = Atlas(64, 64, 261 if not rival else 263)
    main, belt, belt_l = (TAR_L, CRIMSON, CRIMSON_L) if rival else (WOOD, RED, RED_L)
    # Борт: четыре грани по 16 (правая, нос, левая, корма).
    boards(a, 0, 0, 64, 12, main, 4)
    a.rect(0, 0, 64, 1, IRON_L if rival else GOLD), a.rect(0, 1, 64, 2, belt), a.rect(0, 1, 64, 1, belt_l)
    strap(a, 0, 10, 64, 2, IRON_D if rival else IRON)
    for q in range(4):
        strap(a, q * 16, 3, 1, 7), strap(a, q * 16 + 15, 3, 1, 7)
    for q in (0, 2):
        # Борта: бойницы-кресты.
        for x in (4, 11):
            a.rect(q * 16 + x, 4, 1, 5, BLACK), a.rect(q * 16 + x - 1, 6, 3, 1, BLACK)
    a.rect(17, 3, 14, 7, IRON if rival else STEEL_D)
    for x in range(18, 31, 3):
        a.px(x, 4, IRON_L if rival else STEEL_L), a.px(x, 8, IRON_L if rival else STEEL_L)
    if rival:
        rook(a, 20, 3, CRIMSON_L)
    else:
        crest(a, 20, 3)
    for x in range(49, 63, 4):
        a.rect(x, 3, 1, 7, mul(main, 0.5))
    a.rect(54, 6, 4, 2, IRON_L), a.px(55, 7, BLACK), a.px(56, 7, BLACK)
    a.shade(0, 0, 64, 12, 1.08, 0.8, 1.0)
    hull = a.region(0, 0, 64, 12)
    # Настил: доски, люк на железных петлях.
    boards(a, 0, 12, 16, 16, mul(main, 1.12), 4, True)
    a.rect(5, 16, 6, 7, mul(main, 0.7)), a.rect(6, 17, 4, 5, mul(main, 0.95))
    a.rect(5, 17, 6, 1, IRON), a.rect(5, 21, 6, 1, IRON), a.px(8, 19, IRON_L if rival else GOLD)
    deck = a.region(0, 12, 16, 16)
    wheel = paint_wheel(a, 16, 12, rival)
    a.rect(32, 12, 8, 4, IRON), a.rect(32, 13, 8, 1, IRON_L)
    for x in range(32, 40, 2):
        a.px(x, 14, STEEL if not rival else CRIMSON)
    rim = a.region(32, 12, 8, 4)
    # Древко флажка: дерево с кольцами (у соперника смолёное с багровыми).
    boards(a, 40, 12, 8, 16, TAR_L if rival else WOOD_L, 4, True)
    for y in (14, 20, 26):
        a.rect(40, y, 8, 1, CRIMSON if rival else GOLD), a.rect(40, y + 1, 8, 1, BLACK if rival else GOLD_D)
    staff = a.region(40, 12, 8, 16)
    # Оковка тарана: железные листы клином, заклёпки, зазубрины.
    a.rect(48, 12, 16, 16, IRON if rival else STEEL_D)
    for y in range(12, 28, 4):
        a.rect(48, y, 16, 1, IRON_L if rival else STEEL_L), a.rect(48, y + 3, 16, 1, IRON_D)
        for x in range(49, 64, 4):
            a.px(x + (y // 4) % 2 * 2, y + 2, IRON_L if rival else STEEL_L)
    if rival:
        a.rect(48, 12, 16, 3, CRIMSON), a.rect(48, 14, 16, 1, CRIMSON_D)
    else:
        a.rect(48, 24, 16, 2, RED), a.rect(48, 26, 16, 2, GOLD_D)
    a.noise(48, 12, 16, 16, 0.06)
    ram = a.region(48, 12, 16, 16)
    # Попона на задней стенке будки: три косицы понизу вырезаны.
    field, edge = (BLACK, CRIMSON) if rival else (RED, GOLD)
    a.rect(0, 32, 32, 28, field if not rival else rgb("26222C"))
    for x in range(0, 32, 8):
        a.rect(x + 6, 32, 1, 28, mul(field if not rival else rgb("26222C"), 0.75))
        a.rect(x + 2, 32, 1, 28, mul(field if not rival else rgb("3A3440"), 1.1))
    a.rect(0, 32, 32, 2, edge), a.rect(0, 34, 32, 1, GOLD_D if not rival else CRIMSON_D)
    a.rect(0, 32, 2, 28, edge), a.rect(30, 32, 2, 28, edge)
    if rival:
        # Багровый столб и крупная ладья.
        a.rect(13, 35, 6, 25, CRIMSON_D)
        for j in range(8):
            for i in range(7):
                probe = Atlas(8, 8)
                rook(probe, 0, 0, CRIMSON_L)
                if probe.get(i, j)[3] > 0:
                    a.rect(9 + i * 2, 38 + j * 2, 2, 2, CRIMSON_L if probe.get(i, j)[:3] != BLACK else BLACK)
    else:
        # Крупный золотой щит с синим крестом, по бокам белые полосы.
        a.rect(3, 35, 2, 25, WHITE), a.rect(27, 35, 2, 25, WHITE)
        for j in range(8):
            for i in range(7):
                probe = Atlas(8, 8)
                crest(probe, 0, 0)
                if probe.get(i, j)[3] > 0:
                    a.rect(9 + i * 2, 38 + j * 2, 2, 2, probe.get(i, j)[:3])
    for x in range(32):
        cut = 4 - abs((x % 11) - 5) if x < 33 else 0
        for y in range(60 - max(cut, 0) - 1, 60):
            if abs((x % 11) - 5) < 4 and x < 31:
                a.clear(x, y)
    a.noise(0, 32, 32, 28, 0.05)
    drape = a.region(0, 32, 32, 28)
    # Флажок: клин.
    for x in range(32):
        for y in range(8):
            if abs(y - 3.5) <= 4.0 - x * 0.12:
                a.px(32 + x, 32 + y, edge if abs(y - 3.5) < 1.0 or x < 2 else (field if not rival else CRIMSON_D))
    pennant = a.region(32, 32, 32, 8)
    # Круглый щит на борт.
    for j in range(12):
        for i in range(12):
            d = math.hypot(i - 5.5, j - 5.5)
            if d < 5.8:
                if rival:
                    c = IRON_L if d > 4.6 else (CRIMSON_L if d < 1.6 else (BLACK if (i < 6) == (j < 6) else CRIMSON))
                else:
                    c = STEEL_L if d > 4.6 else (GOLD if d < 1.6 else (RED if (i < 6) == (j < 6) else WHITE))
                a.px(32 + i, 40 + j, c)
    shield = a.region(32, 40, 12, 12)
    # Башенка героя с зубцами (верх вырезан) или частокол соперника с остриями.
    boards(a, 32, 52, 32, 12, mul(main, 1.05), 4, True)
    if rival:
        for x in range(32):
            for y in range(4):
                if abs((x % 4) - 1.5) > 0.5 + y * 0.5:
                    a.clear(32 + x, 52 + y)
        strap(a, 32, 58, 32, 2), a.rect(32, 60, 32, 1, CRIMSON)
    else:
        for x in range(32):
            if (x % 8) in (0, 1, 6, 7):
                a.clear(32 + x, 52, 1, 3)
        a.rect(32, 55, 32, 1, WOOD_L), a.rect(32, 60, 32, 2, RED), a.rect(32, 62, 32, 1, GOLD_D)
        for f in range(4):
            a.rect(32 + f * 8 + 3, 56, 2, 3, BLACK)
    fort = a.region(32, 52, 32, 12)
    m = Model(name, a)
    body = at(box((1.0, 0.36, 2.0), hull, deck, deck, (0.86, 0.96) if rival else (1.12, 1.0)), 0.0, 0.58)
    # Будка возницы сзади: дощатые стенки с поясом, крыша чуть уже, спереди облучок.
    cab_w, cab_h, cab_y = (0.8, 0.36, 0.76) if rival else (0.9, 0.4, 0.76)
    body += (at(box((cab_w, cab_h, 0.66), hull, deck, None, (0.86, 0.9)), 0.0, cab_y + cab_h / 2.0, 0.6)
             + at(box((cab_w - 0.1, 0.1, 0.16), deck, deck, deck), 0.0, 0.81, 0.17))
    if rival:
        body += (at(wedge(0.5, (0.5, 0.3), (0.03, 0.03), ram), 0.0, 0.56, -1.0)
                 + quad((-0.5, 1.3, -0.82), (0.5, 1.3, -0.82), (0.46, 0.74, -0.7), (-0.46, 0.74, -0.7), fort))
        for s in (-1.0, 1.0):
            body += quad((s * 0.5, 1.12, -0.82), (s * 0.5, 1.12, 0.1), (s * 0.44, 0.74, 0.1), (s * 0.46, 0.74, -0.7), fort)
    else:
        turret = at(box((0.62, 0.34, 0.52), fort, None, None), 0.0, 0.93, -0.6)
        body += (at(wedge(0.5, (0.8, 0.34), (0.3, 0.14), ram, ram), 0.0, 0.57, -1.0)
                 + turret + flip(turret)
                 + at(box((0.6, 0.02, 0.5), deck, deck, None), 0.0, 1.0, -0.6))
    for s in (-1.0, 1.0):
        # Щиты на бортах лицом наружу.
        for z in (-0.25, 0.5):
            x = s * (0.53 if not rival else 0.5)
            body += quad((x, 0.8, z - s * 0.22), (x, 0.8, z + s * 0.22), (x, 0.36, z + s * 0.22), (x, 0.36, z - s * 0.22), shield)
    # Попона на задней стенке будки и флажок на крыше: древко 0.3 м, не мачта.
    top = cab_y + cab_h
    back, lean = 0.6 + 0.33 + 0.012, 0.03
    body += (quad((0.3, top - 0.02, back - lean), (-0.3, top - 0.02, back - lean),
                  (-0.3, top - 0.5, back + 0.02), (0.3, top - 0.5, back + 0.02), drape)
             + at(loft([(0.0, 0.03, 0.03), (0.3, 0.02, 0.02)], staff, 4), 0.0, top, 0.5)
             + quad((0.0, top + 0.3, 0.5), (0.0, top + 0.27, 0.86), (0.0, top + 0.22, 0.86), (0.0, top + 0.16, 0.5), pennant))
    m.part("body", (0.0, 0.0, 0.0), body)
    for part, z in (("axle_f", -0.72), ("axle_r", 0.72)):
        tris = []
        for x in (-0.6, 0.6):
            tris += at(rot(loft([(-0.07 if not rival else -0.05, 0.32, 0.32), (0.07 if not rival else 0.05, 0.32, 0.32)], rim, 8,
                                caps=(wheel, wheel), flat=True), rz=90.0), x, 0.32, z)
        m.part(part, (0.0, 0.32, z), tris, "body")
    return m


def castles_cart():
    return make_cart("cart", False)


def castles_cart_rival():
    return make_cart("cart_rival", True)


def castles_pistol():
    """Арбалет в латной перчатке: оружие вида от первого лица, болт смотрит в −Z, ноль в
    рукояти. Ореховое ложе, стальной лук поперёк, тетива к замку, болт с красным оперением."""
    a = Atlas(32, 32, 265)
    # Ложе: орех с продольным волокном, костяная накладка, стальная оковка у лука.
    boards(a, 0, 0, 16, 8, WOOD, 4)
    a.rect(0, 0, 16, 1, rgb("E6DEC6")), a.rect(0, 7, 16, 1, WOOD_D)
    for x in (0, 4, 8, 12):
        a.px(x + 1, 4, GOLD), a.px(x + 3, 5, WOOD_D)
    stock = a.region(0, 0, 16, 8)
    # Болт: сверху наконечник, ниже древко.
    a.rect(16, 0, 4, 3, STEEL_L), a.rect(16, 3, 4, 2, STEEL_D)
    a.rect(16, 5, 4, 3, WOOD_L), a.px(17, 6, RED), a.px(19, 6, RED)
    bolt = a.region(16, 0, 4, 8)
    # Стальной лук: полоса с бликом и обмоткой.
    a.rect(20, 0, 12, 4, STEEL), a.rect(20, 0, 12, 1, STEEL_L), a.rect(20, 3, 12, 1, STEEL_D)
    for x in (22, 26, 30):
        a.rect(x, 0, 1, 4, IRON)
    prod = a.region(20, 0, 12, 4)
    a.rect(20, 4, 12, 4, ROPE)
    for x in range(20, 32):
        a.px(x, 4 + x % 4, mul(ROPE, 0.6))
    string = a.region(20, 4, 12, 4)
    # Рукоять и замок: тёмное железо с насечкой, спуск.
    a.rect(0, 8, 16, 8, IRON), a.rect(0, 8, 16, 1, IRON_L)
    for x in range(1, 16, 3):
        a.rect(x, 11, 1, 4, IRON_D)
    a.px(4, 9, GOLD), a.px(11, 9, GOLD)
    a.noise(0, 8, 16, 8, 0.08)
    grip = a.region(0, 8, 16, 8)
    # Латная перчатка: пластины пальцев, костяшки, заклёпки.
    a.rect(0, 16, 16, 8, STEEL)
    a.rect(0, 19, 16, 1, STEEL_D), a.rect(0, 20, 16, 1, STEEL_L), a.rect(0, 23, 16, 1, STEEL_D)
    for x in (3, 7, 11, 15):
        a.rect(x, 16, 1, 3, STEEL_D)
        a.px(x - 2, 17, STEEL_L), a.px(x - 2, 21, GOLD)
    a.shade(0, 16, 16, 8, 1.05, 0.85, 0.8)
    a.noise(0, 16, 16, 8, 0.05)
    hand = a.region(0, 16, 16, 8)
    # Наруч: стальные пластины внахлёст, золотая кайма у кисти, красный край рукава у локтя.
    a.rect(16, 8, 16, 16, STEEL)
    for y in range(12, 22, 4):
        a.rect(16, y, 16, 1, STEEL_D), a.rect(16, y + 1, 16, 1, STEEL_L)
        for x in range(18, 32, 5):
            a.px(x, y + 2, IRON)
    a.rect(16, 8, 16, 1, GOLD), a.rect(16, 9, 16, 1, GOLD_D)
    a.rect(16, 21, 16, 3, RED), a.rect(16, 21, 16, 1, RED_D)
    a.shade(16, 8, 16, 16, 1.0, 0.85, 0.75)
    a.noise(16, 8, 16, 16, 0.05)
    sleeve = a.region(16, 8, 16, 16)
    # Оперение.
    for y in range(4):
        for x in range(8):
            if y >= 3 - x:
                a.px(x, 24 + y, RED if (x + y) % 2 else RED_D)
    feather = a.region(0, 24, 8, 4)
    y = 0.068
    tris = (at(box((0.046, 0.05, 0.4), stock, stock, stock), 0.0, 0.03, -0.19)
            + at(rot(loft([(-0.13, 0.008, 0.008), (0.13, 0.008, 0.008), (0.14, 0.02, 0.01), (0.2, 0.001, 0.001)], bolt, 4),
                     rx=-90.0), 0.0, y, -0.2)
            + quad((0.0, y + 0.03, -0.07), (0.0, y + 0.03, -0.14), (0.0, y, -0.14), (0.0, y, -0.07), feather)
            + at(rot(box((0.045, 0.15, 0.06), grip, grip, grip), rx=-20.0), 0.0, -0.05, 0.03)
            + at(box((0.03, 0.034, 0.05), grip, grip, grip), 0.0, 0.07, -0.035)
            + at(box((0.085, 0.1, 0.1), hand, hand, hand), 0.0, -0.04, 0.03)
            + at(rot(loft([(0.0, 0.045, 0.045), (0.5, 0.06, 0.06)], sleeve, 4, math.pi / 4.0), rx=65.0), 0.0, -0.08, 0.07))
    for s in (-1.0, 1.0):
        # Плечо лука в два колена, тетива от конца к замку.
        tris += beam((0.0, 0.05, -0.37), (s * 0.11, 0.05, -0.35), 0.022, prod, prod, 0.016)
        tris += beam((s * 0.105, 0.05, -0.352), (s * 0.19, 0.05, -0.29), 0.018, prod, prod, 0.012)
        tris += beam((s * 0.19, 0.05, -0.29), (0.0, 0.062, -0.05), 0.005, string)
    return Model("pistol", a).part("body", (0.0, 0.0, 0.0), tris)


def castles_hoop():
    """Турнирное кольцо: цель спорта. Щит это гербовая доска в красно-белую четверть с золотой
    рамкой прицела, кольцо золотое, вместо сетки ленты; столб турнирный, в красно-белую спираль.
    Кольцо и щит там же и тех же размеров, что у пиратов."""
    a = Atlas(64, 64, 267)
    # Доска: четверти по дереву, золотая рама с гвоздями, рамка прицела, корона.
    for qx in range(2):
        for qy in range(2):
            boards(a, qx * 16, qy * 12, 16, 12, RED if qx == qy else WHITE, 4, True)
    for x, y, w, h in ((10, 9, 12, 1), (10, 18, 12, 1), (10, 9, 1, 10), (21, 9, 1, 10)):
        a.rect(x, y, w, h, GOLD)
    a.rect(11, 10, 10, 8, BLUE_D)
    a.rect(13, 14, 6, 2, GOLD), a.rect(13, 16, 6, 1, GOLD_D)
    for x in (13, 15, 16, 18):
        a.rect(x, 12, 1, 2, GOLD)
    a.px(14, 15, RED), a.px(17, 15, RED)
    for x, y, w, h in ((0, 0, 32, 1), (0, 23, 32, 1), (0, 0, 1, 24), (31, 0, 1, 24)):
        a.rect(x, y, w, h, GOLD_D)
    for x, y, w, h in ((1, 1, 30, 1), (1, 22, 30, 1), (1, 1, 1, 22), (30, 1, 1, 22)):
        a.rect(x, y, w, h, GOLD)
    for x, y in ((3, 3), (28, 3), (3, 20), (28, 20)):
        a.px(x, y, IRON)
    board = a.region(0, 0, 32, 24)
    a.rect(32, 0, 16, 4, GOLD)
    a.rect(32, 0, 16, 1, rgb("FFF0A8")), a.rect(32, 3, 16, 1, GOLD_D)
    for x in range(34, 48, 4):
        a.px(x, 2, GOLD_D)
    ring = a.region(32, 0, 16, 4)
    # Ленты: красные, белые и золотые, с раздвоенными концами, между ними просвет.
    for k in range(8):
        c = (RED, WHITE, GOLD, WHITE)[k % 4]
        for y in range(16 - (k % 2) * 3):
            last = 15 - (k % 2) * 3
            for i in range(3):
                if y == last and i == 1:
                    continue
                a.px(32 + k * 4 + i, 8 + y, mul(c, 0.8) if i == 2 or y % 5 == 4 else c)
    a.rect(32, 8, 32, 1, GOLD_D)
    net = a.region(32, 8, 32, 16)
    # Столб: красно-белая спираль, золотые кольца.
    for y in range(32):
        for x in range(8):
            a.px(x, 24 + y, RED if ((x + y) // 4) % 2 == 0 else WHITE)
    for y in (24, 40, 54):
        a.rect(0, y, 8, 2, GOLD), a.rect(0, y + 1, 8, 1, GOLD_D)
    a.shade(0, 24, 8, 32, 1.0, 0.9, 0.6)
    a.noise(0, 24, 8, 32, 0.05)
    post = a.region(0, 24, 8, 32)
    masonry(a, 8, 24, 16, 8, STONE, 4, 4)
    foot = a.region(8, 24, 16, 8)
    rim_y, rim_z = 3.05, -0.42
    ring_tris = []
    for k in range(8):
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        p = lambda r, t: (r * math.sin(t), rim_y, rim_z + r * math.cos(t))
        ring_tris += quad(p(0.19, a0), p(0.19, a1), p(0.245, a1), p(0.245, a0), ring)
    basket = at(loft([(rim_y - 0.42, 0.13, 0.13), (rim_y, 0.215, 0.215)], net, 8), 0.0, 0.0, rim_z)
    faces = []
    u0, v0, u1, v1 = board
    for z, mirror in ((-0.15, 1.0), (-0.09, -1.0)):
        for ix in range(2):
            for iy in range(2):
                xa, xb = 0.65 - 0.65 * ix, 0.65 - 0.65 * (ix + 1)
                ya, yb = 3.875 - 0.475 * iy, 3.875 - 0.475 * (iy + 1)
                part = (u0 + (u1 - u0) * ix / 2.0, v0 + (v1 - v0) * iy / 2.0, u0 + (u1 - u0) * (ix + 1) / 2.0, v0 + (v1 - v0) * (iy + 1) / 2.0)
                faces += quad((xa * mirror, ya, z), (xb * mirror, ya, z), (xb * mirror, yb, z), (xa * mirror, yb, z), part, False)
    edge = (u0, v0, u0 + (u1 - u0) / 16.0, v1)
    for x in (-0.65, 0.65):
        faces += quad((x, 3.875, -0.15), (x, 3.875, -0.09), (x, 2.925, -0.09), (x, 2.925, -0.15), edge)
    for y in (2.925, 3.875):
        faces += quad((0.65, y, -0.15), (-0.65, y, -0.15), (-0.65, y, -0.09), (0.65, y, -0.09), edge)
    return Model("hoop", a).part("body", (0.0, 0.0, 0.0),
                                 loft([(0.0, 0.09, 0.09), (3.9, 0.07, 0.07)], post, 5, caps=(None, ring))
                                 + loft([(0.0, 0.3, 0.3), (0.12, 0.2, 0.2)], foot, 5, caps=(None, foot), flat=True)
                                 + at(box((0.06, 0.06, 0.2), ring, ring, ring), 0.0, rim_y, -0.2)
                                 + faces + ring_tris + basket + flip(basket))


MODELS = [castles_cannon, castles_palm, castles_flag, castles_lighthouse, castles_cart, castles_cart_rival, castles_pistol,
          castles_hoop]


if __name__ == "__main__":
    models = [f() for f in MODELS]
    for m in models:
        print("%-11s частей %d, треугольников %3d%s" % (m.name, len(m.parts), m.tris(),
                                                        "  БОЛЬШЕ %d" % lm.MAX_TRIS if m.tris() > lm.MAX_TRIS else ""))
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
