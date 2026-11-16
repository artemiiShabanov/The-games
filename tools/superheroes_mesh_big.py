#!/usr/bin/env python3
"""Крупный реквизит и транспорт «Супергероев» для low poly и «продвинутых» (#137): зеркала
моделей космоса из `space_mesh_big.py` (а те зеркала пиратских из `lowpoly_meshes.py`) с теми же
именами слотов, частей и точками вращения, тем же нулём и габаритами, чтобы десять 3D-демок
работали без правок. Цвета из основы 16/32 (`superheroes16.PALETTE`) через
`superheroes_mesh_chars`, облик тот же, что в наборах 16/32 (`superheroes_road16`,
`superheroes_hold16`).

  cannon      лучевая пушка злодея на гусеницах: ребристый ствол с раструбом и красной линзой
              (ствол в −Z, как у пушки)
  palm        красно-белая радиомачта с антеннами и тарелками; атлас: слева ферма мачты,
              справа антенна-«ёлочка» с вырезом по прозрачности (эти же половины берёт
              `ThreedScreen.add_palm`)
  flag        флаг героя со звездой: части `pole` и `cloth`
  lighthouse  небоскрёб с уступами и прожектором на крыше, высота маяка
  cart        машина героя: `body`, оси `axle_f`, `axle_r`; на месте паруса низкий жёлтый
              спойлер на двух стойках (паруса и мачты только у пиратов)
  cart_rival  броневик злодеев: те же части, на месте паруса красная мигалка-«глаз» на крыше
              рубки, шипы в ступицах
  pistol      перчатка-бластер на синем рукаве, вид от первого лица
  hoop        неоновый обруч на щите-вывеске со звездой и лампочками, сетка из цепей; кольцо
              там же и того же размера

    python3 tools/superheroes_mesh_big.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from lowpoly_meshes import Atlas, Model, at, box, flip, loft, mul, quad, rot  # noqa: E402
import superheroes_mesh_chars as sc  # noqa: E402
import superheroes_mesh_items as si  # noqa: E402

mix, stamp = sc.mix, si.stamp
STAR7, STAR9 = sc.s16.STAR7, si.STAR9

# Цвета набора из палитры основы: трико и жёлтое героя, металл, корпус роботов, закат.
BLACK, WHITE, GREY = sc.BLACK, sc.WHITE, sc.GREY
BLUE, BLUE_D, BLUE_L = sc.SUIT, sc.SUIT_D, sc.SUIT_L
GOLD, GOLD_D, GOLD_L = sc.GOLD, sc.GOLD_D, sc.GOLD_L
METAL, METAL_D, METAL_L = sc.METAL, sc.METAL_D, sc.METAL_L
RED, RED_D = sc.RED, sc.RED_D
BOT, BOT_D, BOT_L = sc.BOT, sc.BOT_D, sc.BOT_L
PEACH, CORAL = sc.PEACH, sc.P[sc.s16.AQUA]
CONCRETE, CONCRETE_D, CONCRETE_L = GREY, mix(GREY, METAL, 0.6), mix(GREY, WHITE, 0.6)
NIGHT = mix(BLUE_D, BLACK, 0.45)


# --- Помощники ---------------------------------------------------------------------------------

def plates(a, x, y, w, h, base, sx=8, sy=6):
    """Броневые листы: тёмные швы вразбежку, светлая кромка под швом, болты по углам."""
    a.rect(x, y, w, h, base)
    for row, j in enumerate(range(0, h, sy)):
        a.rect(x, y + j, w, 1, mul(base, 0.6))
        if j + 1 < h:
            a.rect(x, y + j + 1, w, 1, mul(base, 1.16))
        for i in range((row % 2) * (sx // 2), w, sx):
            a.rect(x + i, y + j, 1, min(sy, h - j), mul(base, 0.6))
            for dj in (2, sy - 2):
                if j + dj < h and i + 1 < w:
                    a.px(x + i + 1, y + j + dj, mul(base, 1.3))
    a.noise(x, y, w, h, 0.06)


def hazard(a, x, y, w, h, c0=GOLD, c1=BLACK):
    """Полосы опасности наискось."""
    for j in range(h):
        for i in range(w):
            a.px(x + i, y + j, c0 if ((i + j) // 3) % 2 == 0 else c1)


def tube(rings, regs, n=6, phase=0.0, caps=(None, None), flat=False):
    """Тело вращения, у каждого пояса между соседними кольцами свой кусок атласа: рисунок не
    тянется, когда пояса разной длины. Крышки только на концах."""
    tris = []
    last = len(rings) - 2
    for i in range(len(rings) - 1):
        tris += loft([rings[i], rings[i + 1]], regs[i], n, phase,
                     (caps[0] if i == 0 else None, caps[1] if i == last else None), flat)
    return tris


def prism(pts, side, edges, cx=0.0):
    """Кузов по выпуклому контуру сбоку. `pts`: точки (вперёд, вверх, полуширина); «вперёд»
    это −Z модели. Борта развёрнуты в `side` по габариту контура (перёд слева), грань между
    точками i и i+1 берёт `edges[i]` (None пропускает): поперёк куска идёт ширина, сверху
    вниз путь от i к i+1."""
    fs, ys = [p[0] for p in pts], [p[1] for p in pts]
    f0, f1, y0, y1 = min(fs), max(fs), min(ys), max(ys)
    mf, my = sum(fs) / len(pts), sum(ys) / len(pts)
    tris = []
    if side:
        uv = lambda p: si._uv(side, (f1 - p[0]) / (f1 - f0), (y1 - p[1]) / (y1 - y0))
        for sgn in (-1.0, 1.0):
            for k in range(1, len(pts) - 1):
                tri = (pts[0], pts[k], pts[k + 1])
                tris.append(si._face([(cx + sgn * p[2], p[1], -p[0]) for p in tri], [uv(p) for p in tri], (sgn, 0.0, 0.0)))
    for i, reg in enumerate(edges):
        if reg is None:
            continue
        p, q = pts[i], pts[(i + 1) % len(pts)]
        out = (0.0, (p[1] + q[1]) / 2.0 - my, -((p[0] + q[0]) / 2.0 - mf))
        v = [(cx - p[2], p[1], -p[0]), (cx + p[2], p[1], -p[0]), (cx + q[2], q[1], -q[0]), (cx - q[2], q[1], -q[0])]
        t = [si._uv(reg, 0.0, 0.0), si._uv(reg, 1.0, 0.0), si._uv(reg, 1.0, 1.0), si._uv(reg, 0.0, 1.0)]
        tris += [si._face([v[0], v[1], v[2]], [t[0], t[1], t[2]], out), si._face([v[0], v[2], v[3]], [t[0], t[2], t[3]], out)]
    return tris


def paint_wheel(a, x0, y0, rival):
    """Колесо 16×16, вокруг прозрачно. Герой: чёрная шина, жёлтый обод, синий диск с жёлтой
    звездой. Злодеи: шина с шипами-грунтозацепами, тёмный диск с пилой и красной ступицей."""
    a.rect(x0, y0, 16, 16, BLACK)
    for j in range(16):
        for i in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            ang = math.atan2(j - 7.5, i - 7.5)
            sector = int((ang + math.pi) * 8 / math.pi)
            if d > 7.7:
                a.clear(x0 + i, y0 + j)
                continue
            if d > 5.3:
                c = (METAL_D if sector % 2 else BLACK) if not rival else (BOT_D if sector % 2 else BLACK)
            elif d > 4.3:
                c = RED_D if rival else GOLD
            elif d < 1.5:
                c = RED if rival else GOLD_L
            elif rival:
                c = BOT if int((ang + math.pi + d * 0.45) * 3 / math.pi) % 2 == 0 else BOT_D
            else:
                c = GOLD if d <= si._star_radius(-ang, 4.3, 1.9) else BLUE_D
            a.px(x0 + i, y0 + j, c)
    if rival:
        a.px(x0 + 7, y0 + 7, GOLD), a.px(x0 + 8, y0 + 8, CORAL)
    else:
        a.px(x0 + 7, y0 + 7, WHITE)
    return a.region(x0, y0, 16, 16)


def tread(a, x, y, w, h, rival):
    """Протектор шины лентой: ёлочка."""
    a.rect(x, y, w, h, BLACK)
    for i in range(w):
        for j in range(h):
            if (i + abs(j - h // 2)) % 3 == 0:
                a.px(x + i, y + j, BOT_D if rival else METAL_D)
    return a.region(x, y, w, h)


# --- Модели ------------------------------------------------------------------------------------

def superheroes_cannon():
    """Лучевая пушка злодея: зелёно-серая камера накачки с манометром, тонкий ствол с тремя
    жёлтыми рёбрами-изоляторами, раструб с красной линзой-глазом; станок на двух гусеницах."""
    a = Atlas(64, 32, 319)
    # Камера накачки: листы корпуса роботов, красное окошко манометра, полоса опасности.
    plates(a, 0, 0, 32, 8, BOT, 8, 4)
    a.rect(14, 1, 5, 4, BLACK)
    a.rect(15, 2, 3, 2, RED), a.px(15, 2, CORAL), a.px(17, 3, GOLD)
    hazard(a, 0, 6, 32, 2)
    a.shade(0, 0, 32, 8, 1.1, 0.9, 0.62)
    chamber = a.region(0, 0, 32, 8)
    # Тёмный металл казённика и ствола: продольные блики.
    a.rect(0, 8, 32, 2, METAL_D)
    for x in range(0, 32, 4):
        a.px(x + 1, 8, METAL), a.px(x + 3, 9, BLACK)
    a.shade(0, 8, 32, 2, 1.0, 1.0, 0.6)
    steel = a.region(0, 8, 32, 2)
    # Ребро-изолятор: торец с лучами и скат от светлого края к тёмному.
    for x in range(32):
        a.px(x, 10, GOLD_D if x % 4 else BLACK), a.px(x, 11, GOLD if x % 4 else GOLD_D)
    fin_face = a.region(0, 10, 32, 2)
    for j, c in enumerate((GOLD_L, GOLD, GOLD, GOLD_D)):
        a.rect(0, 12 + j, 32, 1, c)
    for x in range(0, 32, 4):
        a.rect(x, 13, 1, 3, GOLD_D)
    a.shade(0, 12, 32, 4, 1.0, 1.0, 0.65)
    fin_cone = a.region(0, 12, 32, 4)
    # Раструб: корпус роботов с красными шевронами к срезу.
    a.rect(32, 0, 16, 8, BOT)
    a.rect(32, 0, 16, 1, BOT_L), a.rect(32, 1, 16, 1, RED), a.rect(32, 7, 16, 1, BOT_D)
    for x in range(32, 48, 4):
        a.px(x + 1, 3, RED), a.px(x, 4, RED), a.px(x + 2, 4, RED), a.px(x + 3, 6, BOT_D)
    a.shade(32, 0, 16, 8, 1.1, 0.8, 0.65)
    a.noise(32, 0, 16, 8, 0.05)
    flare = a.region(32, 0, 16, 8)
    # Линза: красный глаз, как у роботов, с жёлтым зрачком и бликом.
    for j in range(8):
        for i in range(8):
            d = math.hypot(i - 3.5, j - 3.5)
            a.px(48 + i, j, BLACK if d > 3.9 else RED_D if d > 3.0 else RED if d > 1.6 else GOLD)
    a.px(50, 2, WHITE), a.px(51, 3, GOLD_L), a.px(52, 4, CORAL)
    lens = a.region(48, 0, 8, 8)
    # Задняя крышка: решётка охлаждения.
    a.rect(56, 0, 8, 8, METAL_D)
    for y in (1, 3, 5):
        a.rect(57, y, 6, 1, BLACK)
    a.px(59, 7, RED)
    back = a.region(56, 0, 8, 8)
    # Тумба: листы, пульт с огнями, полоса опасности понизу.
    plates(a, 0, 16, 32, 12, BOT, 8, 6)
    hazard(a, 0, 25, 32, 3)
    a.rect(12, 18, 7, 4, BLACK)
    a.px(13, 19, RED), a.px(15, 19, GOLD), a.px(17, 20, CORAL), a.px(14, 20, METAL)
    a.shade(0, 16, 32, 12, 1.1, 0.8, 0.85)
    body = a.region(0, 16, 32, 12)
    # Гусеница сбоку: лента траков, внутри четыре катка и ведущая звёздочка.
    a.rect(32, 16, 32, 8, BLACK)
    a.rect(33, 17, 30, 6, BOT_D)
    for x in range(32, 64, 2):
        a.px(x, 16, METAL_D), a.px(x + 1, 23, METAL_D)
    for cx in (37, 44, 51, 58):
        for j in range(4):
            for i in range(4):
                if (i, j) not in ((0, 0), (3, 0), (0, 3), (3, 3)):
                    a.px(cx - 2 + i, 19 + j, METAL if (i, j) not in ((1, 1), (2, 2)) else METAL_L)
        a.px(cx, 21, BLACK)
    a.rect(33, 17, 3, 2, METAL), a.px(34, 17, GOLD)
    track = a.region(32, 16, 32, 8)
    a.rect(32, 24, 16, 8, BLACK)
    for y in range(24, 32, 2):
        a.rect(32, y, 16, 1, METAL_D)
        a.px(34, y, METAL), a.px(45, y, METAL)
    lugs = a.region(32, 24, 16, 8)
    barrel = tube([(-0.5, 0.13, 0.13), (-0.45, 0.2, 0.2), (-0.15, 0.2, 0.2), (-0.1, 0.085, 0.085), (-0.04, 0.085, 0.085),
                   (-0.04, 0.155, 0.155), (0.06, 0.075, 0.075), (0.06, 0.145, 0.145), (0.16, 0.07, 0.07),
                   (0.16, 0.135, 0.135), (0.26, 0.065, 0.065), (0.38, 0.065, 0.065), (0.56, 0.21, 0.21)],
                  [steel, chamber, steel, steel, fin_face, fin_cone, fin_face, fin_cone, fin_face, fin_cone, steel, flare],
                  8, caps=(back, lens))
    crawler = [(0.3, 0.0, 0.08), (0.4, 0.1, 0.08), (0.34, 0.26, 0.08), (-0.5, 0.26, 0.08), (-0.58, 0.1, 0.08), (-0.48, 0.0, 0.08)]
    m = Model("cannon", a)
    return m.part("body", (0.0, 0.0, 0.0),
                  at(rot(barrel, rx=-90.0), 0.0, 0.52, -0.1)
                  + at(box((0.36, 0.26, 0.56), body, body, None, (0.85, 0.8)), 0.0, 0.31, 0.12)
                  + prism(crawler, track, [lugs] * 6, -0.25) + prism(crawler, track, [lugs] * 6, 0.25))


def superheroes_palm():
    """Радиомачта на крыше: красно-белая ферма с маячком наверху, от неё в стороны антенны
    «ёлочкой» и две тарелки. Антенна это пара скрещённых плоскостей с вырезом по прозрачности,
    как лист пальмы: `ThreedScreen.add_palm` кладёт на свои ленты ту же правую половину
    атласа, а на ствол левую."""
    a = Atlas(32, 32, 345)
    # Ферма: четыре пояса по восемь строк, на каждой из четырёх граней стойки и раскос зигзагом.
    for y in range(32):
        band = RED if (y // 8) % 2 == 0 else WHITE
        for x in range(16):
            lx = x % 4
            c = band
            if lx == 0:
                c = mul(band, 0.55)
            elif lx == 1 + (y % 4 if y % 4 < 3 else 1):
                c = mul(band, 0.72)
            if y % 8 == 0:
                c = mul(band, 0.6)
            a.px(x, y, c)
    a.shade(0, 0, 16, 32, 1.0, 1.0, 0.78)
    a.noise(0, 0, 16, 32, 0.05)
    trunk = a.region(0, 0, 16, 32)
    red_band, white_band = a.region(0, 1, 16, 6), a.region(0, 9, 16, 6)
    # Антенна: стрела по оси, шесть поперечин всё короче к концу, растяжки у мачты, на конце
    # красный огонь.
    for y in range(0, 30):
        a.px(23, y, METAL_L), a.px(24, y, METAL_D)
    for k, half in enumerate((7, 7, 6, 5, 4, 3)):
        y = 3 + k * 5
        for dx in range(-half, half + 2):
            x = 23 + dx
            if 16 <= x < 32:
                a.px(x, y, METAL_L), a.px(x, y + 1, METAL)
        a.px(max(23 - half, 16), y, GOLD), a.px(min(24 + half, 31), y, GOLD)
    for k in range(1, 7):
        a.px(23 - k, k // 2 + (k % 2), METAL_D), a.px(24 + k, k // 2 + (k % 2), METAL_D)
    a.rect(21, 0, 6, 2, METAL_D), a.rect(22, 0, 4, 1, GOLD_D)
    a.rect(22, 29, 4, 3, RED), a.px(23, 30, CORAL), a.px(24, 30, WHITE), a.px(22, 29, RED_D), a.px(25, 31, RED_D)
    leaf = a.region(16, 0, 16, 32)
    sq = lambda rings, reg, caps=(None, None): loft(rings, reg, 4, math.pi / 4.0, caps, True)
    tris = (sq([(0.0, 0.2, 0.2), (4.2, 0.1, 0.1)], trunk)
            + sq([(0.0, 0.42, 0.42), (0.26, 0.3, 0.3)], red_band, (None, white_band))
            + sq([(4.16, 0.17, 0.17), (4.34, 0.17, 0.17)], red_band, (red_band, red_band))
            + loft([(4.3, 0.035, 0.035), (4.62, 0.008, 0.008)], white_band, 4))

    def boom(y, ang, length, w=0.42, rise=0.12):
        d = (math.sin(ang), math.cos(ang))
        q = (math.cos(ang), -math.sin(ang))
        far = (d[0] * length, y + rise, d[1] * length)
        return (quad((0.0, y + w, 0.0), (0.0, y - w, 0.0), (far[0], far[1] - w, far[2]), (far[0], far[1] + w, far[2]), leaf)
                + quad((-q[0] * w, y, -q[1] * w), (q[0] * w, y, q[1] * w),
                       (far[0] + q[0] * w, far[1], far[2] + q[1] * w), (far[0] - q[0] * w, far[1], far[2] - q[1] * w), leaf))

    for y, ang, length in ((3.85, 0.45, 1.5), (3.85, 0.45 + math.pi, 1.35), (3.2, 0.45 + math.pi / 2.0, 1.25),
                           (3.2, 0.45 - math.pi / 2.0, 1.15), (2.55, 1.1 + math.pi, 0.95)):
        tris += boom(y, ang, length)
    # Тарелки: неглубокие чаши на боку мачты, смотрят в разные стороны и чуть вверх.
    dish = loft([(0.0, 0.04, 0.04), (0.1, 0.26, 0.26), (0.14, 0.36, 0.36)], white_band, 6, caps=(None, white_band))
    arm = box((0.07, 0.07, 0.34), red_band, red_band, red_band)
    tris += at(rot(dish, rx=-72.0, ry=-25.0), 0.12, 2.75, -0.26) + at(rot(arm, ry=-25.0), 0.06, 2.76, -0.13)
    tris += at(rot(dish, rx=-72.0, ry=150.0), -0.14, 1.9, 0.24) + at(rot(arm, ry=150.0), -0.07, 1.91, 0.12)
    return Model("palm", a).part("body", (0.0, 0.0, 0.0), tris)


def superheroes_flag():
    """Флаг героя: синее полотнище с вырезом на конце, жёлтая звезда в белом кольце, жёлтые
    канты; стальное древко с жёлтым шаром на бетонной тумбе. Полотно отдельной частью у древка."""
    a = Atlas(64, 32, 317)
    a.rect(0, 0, 32, 20, BLUE)
    # Складки под эмблемой, канты сверху и снизу.
    for x in (7, 15, 23):
        a.rect(x, 0, 1, 20, mul(BLUE, 0.82)), a.rect(x + 1, 0, 1, 20, mix(BLUE, BLUE_L, 0.5))
    a.rect(0, 0, 32, 2, GOLD), a.rect(0, 2, 32, 1, GOLD_D)
    a.rect(0, 18, 32, 2, GOLD), a.rect(0, 17, 32, 1, GOLD_D)
    for j in range(3, 17):
        for i in range(4, 24):
            d = math.hypot(i - 13.0, j - 9.5)
            if 5.6 <= d < 6.7:
                a.px(i, j, WHITE)
            elif d < 5.6:
                a.px(i, j, BLUE_D)
    stamp(a, 9, 5, STAR9, GOLD)
    a.px(13, 8, GOLD_L), a.px(13, 9, WHITE), a.px(12, 9, GOLD_L)
    a.rect(0, 0, 2, 20, WHITE)
    a.shade(0, 0, 32, 20, 1.06, 0.88, 1.0)
    a.noise(0, 0, 32, 20, 0.06)
    # Вырез «ласточкин хвост» на свободном конце.
    for y in range(2, 18):
        depth = int(round(7.0 - abs(y - 9.5) * 0.9))
        if depth > 0:
            a.clear(32 - depth, y, depth, 1)
    cloth = a.region(0, 0, 32, 20)
    a.rect(32, 0, 8, 32, METAL)
    a.rect(34, 0, 1, 32, METAL_L), a.rect(38, 0, 2, 32, METAL_D)
    for y in (3, 19):
        a.rect(32, y, 8, 2, GOLD), a.rect(32, y + 2, 8, 1, GOLD_D)
    for y in range(7, 32, 3):
        a.px(36, y, PEACH)
    a.noise(32, 0, 8, 32, 0.05)
    pole = a.region(32, 0, 8, 32)
    # Тумба: бетон с крапом и жёлто-чёрной каймой.
    a.rect(40, 0, 8, 8, CONCRETE)
    si.speckle(a, 40, 0, 8, 5, (CONCRETE_D, CONCRETE_L), 8)
    hazard(a, 40, 5, 8, 2)
    a.rect(40, 7, 8, 1, CONCRETE_D)
    base = a.region(40, 0, 8, 8)
    a.rect(48, 0, 8, 8, GOLD)
    a.rect(48, 5, 8, 3, GOLD_D), a.rect(49, 1, 3, 2, GOLD_L), a.px(50, 1, WHITE)
    ball = a.region(48, 0, 8, 8)
    m = Model("flag", a)
    m.part("pole", (0.0, 0.0, 0.0),
           loft([(0.0, 0.05, 0.05), (2.7, 0.04, 0.04)], pole, 5)
           + loft([(0.0, 0.3, 0.3), (0.16, 0.23, 0.23)], base, 4, math.pi / 4.0, caps=(None, base), flat=True)
           + at(loft(si.ball_rings(0.075, 5), ball, 6, caps=(ball, ball)), 0.0, 2.67, 0.0))
    m.part("cloth", (0.04, 2.3, 0.0),
           quad((0.04, 2.62, 0.0), (1.0, 2.56, 0.0), (1.0, 2.02, 0.0), (0.04, 1.98, 0.0), cloth), "pole")
    return m


def _facade(a, x0, y0, w, h):
    """Стена небоскрёба лентой на четыре грани по 16 пикселей: пилоны по краям, пять столбцов
    окон, этаж это два пикселя окна и перемычка. Часть окон горит. Грани разного тона: на одну
    светит закат, две в тени."""
    lit = {}
    for j in range(h):
        for i in range(w):
            face, lx = divmod(i, 16)
            row = j % 3
            if lx == 0 or lx == 15:
                c = CONCRETE_L if lx == 0 else CONCRETE_D
            elif lx % 3 == 0:
                c = CONCRETE
            elif row == 2:
                c = CONCRETE_D
            else:
                key = (face, lx // 3, j // 3)
                if key not in lit:
                    lit[key] = a.rng.random()
                r = lit[key]
                if r < 0.3:
                    c = GOLD if row == 0 else mix(GOLD, GOLD_D, 0.5)
                elif r < 0.4:
                    c = PEACH if row == 0 else CORAL
                else:
                    c = mix(BLUE_D, BLUE, 0.45) if row == 0 and lx % 3 == 1 else BLUE_D
            if face == 0:
                c = mix(c, CORAL, 0.2)
            elif face == 2:
                c = mul(c, 0.76)
            elif face == 3:
                c = mul(c, 0.86)
            a.px(x0 + i, y0 + j, c)


def superheroes_lighthouse():
    """Небоскрёб с прожектором: ориентир на горизонте высотой с маяк. Подиум с витринами и
    полосатым навесом, две ступени башни с карнизами и огнями окон, на верхней ступени эмблема
    героя, жёлтый венец ар-деко, на крыше прожектор с лучом в небо и красно-белый шпиль."""
    a = Atlas(64, 64, 353)
    _facade(a, 0, 0, 64, 40)
    # Эмблема на фасаде верхней ступени: жёлтая звезда в тёмном круге.
    for j in range(14):
        for i in range(16, 32):
            d = math.hypot(i - 23.5, j - 6.0)
            if d < 6.3:
                a.px(i, j, GOLD_D if d > 5.3 else NIGHT)
    stamp(a, 19, 2, STAR9, GOLD)
    a.px(23, 5, WHITE), a.px(23, 6, GOLD_L)
    a.shade(0, 0, 64, 14, 1.08, 0.96, 1.0)
    a.shade(0, 14, 64, 26, 1.02, 0.8, 1.0)
    a.noise(0, 0, 64, 40, 0.04)
    shaft_b, shaft_a = a.region(0, 0, 64, 14), a.region(0, 14, 64, 26)
    # Подиум: карниз, красно-белый навес, витрины, на фасаде дверь.
    for i in range(64):
        face, lx = divmod(i, 16)
        for j in range(8):
            if j == 0:
                c = CONCRETE_L
            elif j < 3:
                c = RED if (i // 2) % 2 == 0 else WHITE
                c = mul(c, 0.85) if j == 2 else c
            elif j == 7 or lx in (0, 15):
                c = CONCRETE_D
            elif lx % 5 == 0:
                c = NIGHT
            else:
                c = GOLD if j < 5 else mix(GOLD, CORAL, 0.45)
            if face == 1 and 6 <= lx <= 9 and j >= 3:
                c = BLUE_D if lx in (6, 9) or j == 3 else BLUE
                if (lx, j) == (8, 5):
                    c = GOLD
            if face in (2, 3):
                c = mul(c, 0.82)
            a.px(i, 40 + j, c)
    podium = a.region(0, 40, 64, 8)
    # Венец: жёлтые рёбра ар-деко с тёмными щелями окон.
    for i in range(32):
        lx = i % 8
        for j in range(8):
            c = GOLD_L if j == 0 else GOLD_D if lx in (0, 7) else (GOLD if (lx + j // 2) % 2 == 0 else mix(GOLD, GOLD_D, 0.6))
            if lx in (2, 5) and 3 <= j <= 5:
                c = NIGHT
            a.px(i, 48 + j, c)
    a.shade(0, 48, 32, 8, 1.1, 0.85, 1.0)
    crown = a.region(0, 48, 32, 8)
    # Карниз: светлый бетон, коралловая полоса, зубчики.
    a.rect(0, 56, 32, 8, CONCRETE_L)
    a.rect(0, 59, 32, 2, CORAL)
    for x in range(0, 32, 2):
        a.rect(x, 62, 1, 2, CONCRETE_D)
    a.rect(0, 56, 32, 1, WHITE)
    trim = a.region(0, 56, 32, 8)
    a.rect(32, 48, 8, 8, METAL_D)
    a.noise(32, 48, 8, 8, 0.14)
    a.px(34, 50, METAL), a.px(37, 53, METAL), a.px(35, 54, BLACK)
    roof = a.region(32, 48, 8, 8)
    # Кожух прожектора: металл с обручами и жёлтым поясом.
    a.rect(40, 48, 8, 8, METAL)
    a.rect(40, 48, 8, 1, GOLD), a.rect(40, 49, 8, 1, GOLD_D), a.rect(40, 52, 8, 1, METAL_D), a.rect(40, 53, 8, 1, METAL_L)
    a.rect(40, 55, 8, 1, METAL_D)
    for x in (41, 45):
        a.px(x, 51, METAL_L)
    lamp = a.region(40, 48, 8, 8)
    for j in range(8):
        for i in range(8):
            d = math.hypot(i - 3.5, j - 3.5)
            a.px(48 + i, 48 + j, METAL_D if d > 3.9 else GOLD if d > 2.8 else GOLD_L if d > 1.5 else WHITE)
    lens = a.region(48, 48, 8, 8)
    # Луч: струи света с вырезом по прозрачности, к дальнему концу редеют.
    for j in range(16):
        for i in range(8):
            ray = i in (1, 3, 4, 6) and (j > 5 or (i + j) % 2 == 0)
            if ray or i in (2, 5) and j > 9:
                a.px(56 + i, 48 + j, mix(GOLD_L, WHITE, 0.45) if i in (3, 4) else GOLD_L)
    beam = a.region(56, 48, 8, 16)
    for j in range(8):
        a.rect(32, 56 + j, 8, 1, RED if (j // 2) % 2 == 0 else WHITE)
    spire = a.region(32, 56, 8, 8)
    a.rect(40, 56, 16, 8, METAL_D)
    sq = lambda rings, reg, caps=(None, None): loft(rings, reg, 4, math.pi / 4.0, caps, True)
    tris = (sq([(0.0, 1.9, 1.9), (1.0, 1.9, 1.9)], podium, (None, roof))
            + sq([(1.0, 2.05, 2.05), (1.15, 2.05, 2.05)], trim, (roof, roof))
            + sq([(1.15, 1.5, 1.5), (4.7, 1.5, 1.5)], shaft_a, (None, roof))
            + sq([(4.7, 1.64, 1.64), (4.82, 1.64, 1.64)], trim, (roof, roof))
            + sq([(4.82, 1.2, 1.2), (6.7, 1.2, 1.2)], shaft_b, (None, roof))
            + sq([(6.7, 1.33, 1.33), (6.84, 1.33, 1.33)], trim, (roof, roof))
            + sq([(6.84, 0.98, 0.98), (7.5, 0.8, 0.8)], crown, (None, roof))
            + at(loft([(0.0, 0.05, 0.05), (1.35, 0.012, 0.012)], spire, 4), -0.3, 7.5, 0.3))
    # Прожектор на вилке смотрит вперёд и вверх, луч упирается в высоту маяка.
    aim = lambda t: at(rot(t, rx=-50.0, ry=35.0), 0.08, 7.93, -0.08)
    tris += at(box((0.34, 0.3, 0.34), lamp, roof, None, (0.7, 0.7)), 0.08, 7.65, -0.08)
    tris += aim(loft([(-0.24, 0.19, 0.19), (0.2, 0.27, 0.27)], lamp, 8, caps=(roof, lens)))
    tris += aim(quad((-0.45, 1.15, 0.0), (0.45, 1.15, 0.0), (0.24, 0.2, 0.0), (-0.24, 0.2, 0.0), beam)
                + quad((0.0, 1.15, -0.45), (0.0, 1.15, 0.45), (0.0, 0.2, 0.24), (0.0, 0.2, -0.24), beam))
    return Model("lighthouse", a).part("body", (0.0, 0.0, 0.0), tris)


def make_cart(name, rival):
    """Транспорт гонок. Герой: низкий синий родстер с жёлтой молнией по борту, персиковым
    стеклом кабины, турбиной в корме и низким жёлтым спойлером на двух стойках там, где у
    повозки парус. Соперник: высокий зелёно-серый броневик злодеев, красные фары-«злые глаза»,
    зубастый бампер, рубка со щелью, две выхлопные трубы с огнём, на крыше рубки низкая
    красная мигалка-«глаз» на месте паруса, шипы в ступицах. Паруса, мачты и кили только у
    пиратов: деталь на месте паруса не выше 0.3 м над кузовом. Части и точки вращения как у пиратской повозки: `body`, `axle_f`,
    `axle_r`."""
    a = Atlas(64, 64, 361 if not rival else 363)
    # Борт 64×12 по габариту кузова, перёд слева.
    if rival:
        plates(a, 0, 0, 64, 12, BOT, 8, 6)
        a.rect(0, 8, 64, 3, BOT_D)
        a.rect(0, 3, 64, 2, RED)
        for x in range(2, 64, 9):
            a.px(x, 3, GOLD), a.px(x + 1, 4, GOLD)
        # Знак экипажа: красный глаз.
        a.rect(27, 5, 7, 5, BLACK)
        a.rect(28, 6, 5, 3, RED), a.px(30, 7, GOLD), a.px(29, 6, CORAL)
    else:
        a.rect(0, 0, 64, 12, BLUE)
        a.rect(0, 0, 64, 2, BLUE_L)
        a.rect(0, 9, 64, 3, BLUE_D)
        # Молния по борту: полоса с изломом.
        for x in range(64):
            y = 3 if x < 22 else 4 if x < 26 else 5 if x < 30 else 3
            a.px(x, y, GOLD), a.px(x, y + 1, GOLD if 22 <= x < 30 else GOLD_D)
        stamp(a, 35, 4, STAR7, GOLD)
        a.px(38, 7, WHITE)
        a.rect(31, 2, 1, 9, BLUE_D), a.rect(46, 2, 1, 9, BLUE_D)
        a.rect(0, 2, 2, 4, GOLD_L), a.rect(62, 2, 2, 4, RED)
    # Колёсные ниши: тёмные арки над осями.
    for cx in (14.5, 52.5):
        for j in range(12):
            for i in range(-8, 9):
                if math.hypot(i, (11.5 - j) * 1.0) < 7.6 and j >= 4:
                    a.px(int(cx + i), j, BLACK if not rival else NIGHT)
    a.rect(0, 11, 64, 1, METAL_D)
    a.shade(0, 0, 64, 12, 1.1, 0.82, 1.0)
    a.noise(0, 0, 64, 12, 0.05)
    hull = a.region(0, 0, 64, 12)
    # Капот и палуба 16×16, вдоль хода сверху вниз.
    if rival:
        plates(a, 0, 12, 16, 16, BOT, 8, 4)
        a.rect(6, 12, 4, 16, BOT_D)
        for y in range(14, 28, 3):
            a.rect(6, y, 4, 1, BLACK)
        a.px(2, 14, RED), a.px(13, 14, RED)
    else:
        a.rect(0, 12, 16, 16, BLUE)
        a.rect(5, 12, 6, 16, GOLD), a.rect(5, 12, 1, 16, GOLD_D), a.rect(10, 12, 1, 16, GOLD_D)
        a.rect(7, 12, 2, 16, GOLD_L)
        for y in (22, 24, 26):
            a.rect(1, y, 3, 1, BLUE_D), a.rect(12, y, 3, 1, BLUE_D)
        a.rect(0, 12, 1, 16, BLUE_L), a.rect(15, 12, 1, 16, BLUE_D)
        a.noise(0, 12, 16, 16, 0.05)
    deck = a.region(0, 12, 16, 16)
    wheel = paint_wheel(a, 16, 12, rival)
    rim = tread(a, 32, 12, 8, 4, rival)
    # Тёмный низ и арки.
    a.rect(32, 16, 8, 12, METAL_D if not rival else BOT_D)
    for y in range(16, 28, 3):
        a.rect(32, y, 8, 1, BLACK)
    a.noise(32, 16, 8, 12, 0.08)
    dark = a.region(32, 16, 8, 12)
    # Стекло героя: персик заката с бликами в синей раме. У злодеев броня рубки со смотровой
    # щелью, в ней красный отсвет.
    if rival:
        plates(a, 40, 12, 8, 16, BOT, 8, 8)
        a.rect(40, 16, 8, 3, BLACK)
        a.rect(41, 17, 6, 1, RED), a.px(43, 17, CORAL)
        a.px(41, 22, BOT_L), a.px(46, 25, BOT_L)
    else:
        a.rect(40, 12, 8, 16, PEACH)
        for y in range(12, 28):
            a.px(41 + (27 - y) // 3, y, WHITE), a.px(44 + (27 - y) // 4, y, mix(PEACH, WHITE, 0.6))
        a.rect(40, 23, 8, 5, mix(PEACH, CORAL, 0.5))
        a.rect(40, 12, 8, 1, BLUE_D), a.rect(40, 27, 8, 1, BLUE_D), a.rect(40, 12, 1, 16, BLUE_D), a.rect(47, 12, 1, 16, BLUE_D)
    glass = a.region(40, 12, 8, 16)
    # Нос 16×8: фары и решётка. Корма 16×8: фонари.
    if rival:
        a.rect(48, 12, 16, 8, BOT_D)
        for x, s in ((49, 1), (58, -1)):
            for i in range(5):
                top = 13 + (i if s > 0 else 4 - i) // 2
                a.rect(x + i, top, 1, 3, RED)
            a.px(x + 2, 14, GOLD), a.px(x + 2, 15, CORAL)
        a.rect(48, 17, 16, 3, BLACK)
        for x in range(48, 64):
            a.px(x, 17 if (x % 4) < 2 else 18, WHITE)
            a.px(x, 19 if (x % 4) >= 2 else 18, GREY if (x % 4) >= 2 else WHITE)
    else:
        a.rect(48, 12, 16, 8, BLUE)
        a.rect(53, 14, 6, 5, BLACK)
        for y in (15, 17):
            a.rect(53, y, 6, 1, METAL)
        for x in (49, 60):
            a.rect(x, 14, 3, 4, GOLD_L), a.px(x + 1, 15, WHITE), a.rect(x, 18, 3, 1, GOLD_D)
        a.rect(48, 12, 16, 1, BLUE_L), a.rect(48, 19, 16, 1, METAL_D)
        a.px(55, 13, GOLD), a.px(56, 13, GOLD)
    nose = a.region(48, 12, 16, 8)
    a.rect(48, 20, 16, 8, BLUE_D if not rival else BOT_D)
    for x in (49, 60):
        a.rect(x, 22, 3, 3, RED), a.px(x + 1, 23, CORAL)
    a.rect(54, 21, 4, 6, BLACK)
    a.rect(48, 27, 16, 1, METAL_D if not rival else BLACK)
    if rival:
        hazard(a, 53, 25, 6, 2)
    tail = a.region(48, 20, 16, 8)
    # Кусок на месте паруса 32×28: полотно спойлера героя (поперёк ширина машины, сверху
    # передняя кромка) или лицо мигалки злодеев с красным глазом.
    if rival:
        a.rect(0, 32, 32, 28, BOT_D)
        for k in range(-28, 32, 6):
            for j in range(28):
                a.px(k + j // 2, 32 + j, BLACK)
                a.px(k + j // 2 + 1, 32 + j, BOT)
        # Красный глаз со зрачком и зубцы понизу.
        for j in range(28):
            for i in range(32):
                dx, dy = (i - 16.0) / 6.5, (j - 15.0) / 3.6
                d = dx * dx + dy * dy
                if d < 1.0:
                    a.px(i, 32 + j, RED if d > 0.25 else GOLD if d > 0.06 else BLACK)
                elif d < 1.5:
                    a.px(i, 32 + j, BLACK)
        for x in range(0, 32, 4):
            a.rect(x, 56, 2, 4, RED_D), a.px(x, 55, RED_D)
    else:
        a.rect(0, 32, 32, 28, GOLD)
        for y in range(36, 60, 5):
            a.rect(0, y, 32, 1, GOLD_D)
        # Светлая передняя кромка, белая полоса по оси, синие законцовки и синяя кайма сзади.
        a.rect(0, 32, 32, 3, GOLD_L), a.rect(0, 32, 32, 1, WHITE)
        a.rect(14, 35, 4, 25, WHITE), a.rect(13, 35, 1, 25, BLUE), a.rect(18, 35, 1, 25, BLUE)
        a.rect(0, 32, 4, 28, BLUE), a.rect(28, 32, 4, 28, BLUE)
        a.rect(0, 32, 1, 28, BLUE_L), a.rect(31, 32, 1, 28, BLUE_D)
        a.rect(4, 55, 24, 2, BLUE), a.rect(4, 57, 24, 3, GOLD_D)
    a.noise(0, 32, 32, 28, 0.05)
    sail = a.region(0, 32, 32, 28)
    # Турбина героя или труба злодеев: бок 16×8 и торец 8×8.
    a.rect(32, 32, 16, 8, METAL if not rival else METAL_D)
    for y in (32, 36):
        a.rect(32, y, 16, 1, METAL_L if not rival else METAL), a.rect(32, y + 1, 16, 1, METAL_D if not rival else BLACK)
    a.rect(32, 38, 16, 2, GOLD if not rival else RED_D)
    for x in range(33, 48, 4):
        a.px(x, 34, METAL_D if not rival else BOT)
    pipe = a.region(32, 32, 16, 8)
    for j in range(8):
        for i in range(8):
            d = math.hypot(i - 3.5, j - 3.5)
            a.px(48 + i, 32 + j, METAL_D if d > 3.9 else RED if d > 2.9 else CORAL if d > 1.9 else GOLD if d > 0.9 else WHITE)
    fire = a.region(48, 32, 8, 8)
    # Кромка спойлера и мигалки, крылья над колёсами.
    edge_c = GOLD if not rival else BOT_D
    a.rect(56, 32, 8, 8, edge_c)
    a.rect(56, 32, 8, 1, mul(edge_c, 1.25)), a.rect(56, 39, 8, 1, mul(edge_c, 0.7))
    a.rect(59, 32, 2, 8, mul(edge_c, 1.15))
    edge = a.region(56, 32, 8, 8)
    wing_c = BLUE if not rival else BOT
    a.rect(32, 40, 16, 8, wing_c)
    a.rect(32, 40, 16, 2, mul(wing_c, 1.25)), a.rect(32, 46, 16, 2, mul(wing_c, 0.65))
    for x in range(32, 48, 4):
        a.px(x, 43, mul(wing_c, 0.7))
    wing = a.region(32, 40, 16, 8)
    # Бок кабины 16×12: стекло со стойкой или броня с красной щелью.
    if rival:
        plates(a, 48, 40, 16, 12, BOT, 8, 6)
        a.rect(51, 43, 10, 3, BLACK)
        a.rect(52, 44, 8, 1, RED), a.px(55, 44, CORAL)
    else:
        a.rect(48, 40, 16, 12, PEACH)
        for y in range(40, 52):
            a.px(50 + (51 - y) // 2, y, WHITE)
        a.rect(48, 47, 16, 5, mix(PEACH, CORAL, 0.5))
        a.rect(48, 40, 16, 1, BLUE_D), a.rect(55, 40, 1, 12, BLUE_D), a.rect(48, 51, 16, 1, BLUE_D)
    cab_side = a.region(48, 40, 16, 12)
    a.rect(32, 48, 16, 16, METAL_D), a.rect(48, 52, 16, 12, METAL_D), a.rect(0, 60, 32, 4, METAL_D), a.rect(0, 28, 64, 4, METAL_D)
    m = Model(name, a)
    if rival:
        body = (prism([(1.1, 0.3, 0.46), (1.3, 0.42, 0.46), (1.2, 0.8, 0.46), (0.35, 0.9, 0.5), (-1.05, 0.9, 0.5),
                       (-1.15, 0.45, 0.5), (-1.0, 0.3, 0.5)], hull, [dark, nose, deck, deck, tail, dark, dark])
                + prism([(0.32, 0.86, 0.42), (0.14, 1.3, 0.36), (-0.55, 1.3, 0.36), (-0.72, 0.86, 0.42)], cab_side,
                        [glass, deck, glass, None])
                # Мигалка на крыше рубки: низкий брусок во всю ширину, глаз смотрит вперёд и назад.
                + prism([(-0.02, 1.28, 0.3), (-0.3, 1.28, 0.3), (-0.27, 1.46, 0.26), (-0.05, 1.46, 0.26)], edge,
                        [None, sail, edge, sail]))
        stack = tube([(0.0, 0.06, 0.06), (0.62, 0.06, 0.06), (0.74, 0.095, 0.095)], [pipe, pipe], 5, caps=(None, fire))
        body += at(stack, -0.38, 0.86, 0.98) + at(stack, 0.38, 0.86, 0.98)
    else:
        body = (prism([(1.12, 0.3, 0.42), (1.26, 0.4, 0.42), (1.22, 0.62, 0.42), (0.3, 0.78, 0.5), (-1.0, 0.76, 0.5),
                       (-1.14, 0.6, 0.5), (-1.05, 0.3, 0.5)], hull, [dark, nose, deck, deck, tail, dark, dark])
                + prism([(0.34, 0.74, 0.36), (0.04, 1.06, 0.26), (-0.42, 1.06, 0.26), (-0.72, 0.74, 0.36)], cab_side,
                        [glass, glass, glass, None])
                # Спойлер: полотно во всю ширину на двух стойках, верх не выше крыши кабины.
                + prism([(-0.84, 0.97, 0.52), (-1.2, 0.99, 0.52), (-1.22, 1.04, 0.52), (-0.86, 1.02, 0.52)], edge,
                        [dark, edge, sail, edge])
                + prism([(-0.9, 0.72, 0.035), (-1.08, 0.72, 0.035), (-1.14, 0.99, 0.035), (-0.98, 0.99, 0.035)], edge,
                        [None, edge, None, edge], -0.3)
                + prism([(-0.9, 0.72, 0.035), (-1.08, 0.72, 0.035), (-1.14, 0.99, 0.035), (-0.98, 0.99, 0.035)], edge,
                        [None, edge, None, edge], 0.3)
                + at(rot(tube([(-0.22, 0.15, 0.15), (0.1, 0.19, 0.19), (0.16, 0.15, 0.15)], [pipe, pipe], 6, caps=(None, fire)),
                         rx=90.0), 0.0, 0.55, 1.14))
        for z in (-0.72, 0.72):
            for x in (-0.57, 0.57):
                body += at(box((0.32, 0.06, 0.76), wing, wing, dark, (1.0, 0.72)), x, 0.68, z)
    m.part("body", (0.0, 0.0, 0.0), body)
    half = 0.08 if rival else 0.07
    for part, z in (("axle_f", -0.72), ("axle_r", 0.72)):
        tris = []
        for x in (-0.6, 0.6):
            tris += at(rot(loft([(-half, 0.32, 0.32), (half, 0.32, 0.32)], rim, 8, caps=(wheel, wheel), flat=True), rz=90.0),
                       x, 0.32, z)
            if rival:
                # Шип в ступице наружу.
                s = 1.0 if x > 0 else -1.0
                tris += at(rot(loft([(0.0, 0.09, 0.09), (0.16, 0.0, 0.0)], edge, 4, flat=True), rz=-90.0 * s), x + s * half, 0.32, z)
        m.part(part, (0.0, 0.32, z), tris, "body")
    return m


def superheroes_cart():
    return make_cart("cart", False)


def superheroes_cart_rival():
    return make_cart("cart_rival", True)


def superheroes_pistol():
    """Перчатка-бластер: оружие вида от первого лица, излучатель смотрит в −Z, ноль в кулаке.
    Синий рукав трико, жёлтая перчатка с раструбом, кулак костяшками вперёд; на тыле кисти
    стальной блок со звездой и коралловой колбой заряда, из него ствол с тремя жёлтыми
    кольцами и синей линзой."""
    a = Atlas(32, 32, 365)
    # Сталь ствола, жёлтое кольцо, тёмный казённик.
    a.rect(0, 0, 16, 4, METAL)
    a.rect(0, 0, 16, 1, METAL_L), a.rect(0, 3, 16, 1, METAL_D)
    for x in (2, 7, 12):
        a.px(x, 1, GREY), a.px(x + 1, 2, METAL_D)
    steel = a.region(0, 0, 16, 4)
    a.rect(0, 4, 16, 1, GOLD_L), a.rect(0, 5, 16, 1, GOLD_D)
    for x in range(0, 16, 3):
        a.px(x, 4, GOLD)
    ring = a.region(0, 4, 16, 2)
    a.rect(0, 6, 16, 2, METAL_D)
    for x in range(1, 16, 2):
        a.px(x, 6, BLACK)
    a.px(4, 7, RED), a.px(5, 7, GOLD)
    breech = a.region(0, 6, 16, 2)
    # Линза: синее стекло с персиковым огнём.
    a.rect(16, 0, 4, 4, BLUE)
    a.rect(17, 1, 2, 2, PEACH), a.px(17, 1, WHITE)
    lens = a.region(16, 0, 4, 4)
    a.rect(20, 0, 4, 4, METAL_D), a.px(21, 1, METAL), a.px(22, 2, BLACK)
    cap = a.region(20, 0, 4, 4)
    # Табличка на блоке: жёлтая звезда на синем.
    a.rect(24, 0, 8, 8, BLUE)
    a.rect(24, 0, 8, 1, BLUE_D)
    stamp(a, 24, 1, STAR7, GOLD)
    a.px(27, 4, WHITE)
    plate = a.region(24, 0, 8, 8)
    # Колба заряда: коралл с бликом в стальных торцах.
    a.rect(16, 4, 8, 4, CORAL)
    a.rect(16, 4, 8, 1, PEACH), a.rect(16, 7, 8, 1, RED_D), a.px(18, 5, WHITE), a.px(21, 5, PEACH)
    flask = a.region(16, 4, 8, 4)
    # Блок: сталь с болтами, ремень через ладонь понизу.
    a.rect(0, 8, 16, 8, METAL)
    a.rect(0, 8, 16, 1, GREY), a.rect(0, 13, 16, 3, METAL_D), a.rect(0, 13, 16, 1, BLACK)
    for x in range(1, 16, 4):
        a.px(x, 10, METAL_L), a.px(x + 2, 11, METAL_D)
    a.noise(0, 8, 16, 8, 0.06)
    block = a.region(0, 8, 16, 8)
    # Раструб перчатки: жёлтый с кантом и швами.
    a.rect(16, 8, 16, 8, GOLD)
    a.rect(16, 8, 16, 1, GOLD_L), a.rect(16, 9, 16, 1, GOLD_D), a.rect(16, 14, 16, 2, GOLD_D)
    for x in range(18, 32, 4):
        a.rect(x, 10, 1, 4, GOLD_D), a.px(x + 1, 11, GOLD_L)
    a.shade(16, 8, 16, 8, 1.05, 0.9, 0.8)
    cuff = a.region(16, 8, 16, 8)
    # Кулак лентой на четыре грани по четыре пикселя: бок, костяшки (четыре пальца), бок, запястье.
    a.rect(0, 16, 16, 8, GOLD)
    for x in range(4, 8):
        a.rect(x, 16, 1, 8, GOLD if x % 2 == 0 else mix(GOLD, GOLD_L, 0.6))
        a.px(x, 17, GOLD_L), a.px(x, 20, GOLD_D), a.px(x, 23, GOLD_D)
    for x in (0, 8):
        a.rect(x, 16, 4, 1, GOLD_L)
        a.rect(x, 19, 4, 1, GOLD_D), a.rect(x, 22, 4, 2, GOLD_D)
        a.px(x + 1, 20, GOLD_L)
    a.rect(12, 16, 4, 8, GOLD_D)
    a.noise(0, 16, 16, 8, 0.05)
    fist = a.region(0, 16, 16, 8)
    # Тыл кисти и большой палец.
    a.rect(0, 24, 16, 8, GOLD)
    a.rect(0, 24, 16, 1, GOLD_L), a.rect(0, 31, 16, 1, GOLD_D)
    for x in (3, 7, 11):
        a.rect(x, 25, 1, 3, GOLD_D)
    a.px(5, 29, GOLD_L), a.px(9, 29, GOLD_L)
    a.noise(0, 24, 16, 8, 0.05)
    back = a.region(0, 24, 16, 8)
    # Рукав трико: синяя ткань со складками и бликом.
    a.rect(16, 16, 16, 16, BLUE)
    for y in range(18, 32, 4):
        a.rect(16, y, 16, 1, BLUE_D)
        a.rect(16, y + 1, 16, 1, mix(BLUE, BLUE_L, 0.5))
    a.rect(19, 16, 1, 16, BLUE_L)
    a.shade(16, 16, 16, 16, 1.0, 0.85, 0.7)
    a.noise(16, 16, 16, 16, 0.05)
    sleeve = a.region(16, 16, 16, 16)
    arm = lambda t: at(rot(t, rx=65.0), 0.0, -0.08, 0.07)
    gun = lambda t: at(rot(t, rx=-90.0), 0.0, 0.06, -0.2)
    tris = (arm(loft([(0.0, 0.045, 0.045), (0.5, 0.06, 0.06)], sleeve, 6))
            + arm(loft([(-0.01, 0.052, 0.052), (0.03, 0.06, 0.06), (0.15, 0.082, 0.082)], cuff, 6, caps=(None, cap)))
            + at(box((0.09, 0.085, 0.11), fist, back, back), 0.0, -0.04, 0.02)
            + at(box((0.03, 0.04, 0.075), back, back, back), -0.058, -0.035, 0.005)
            + at(box((0.074, 0.05, 0.13), block, block, None), 0.0, 0.03, -0.02)
            + quad((-0.03, 0.0556, -0.02), (0.03, 0.0556, -0.02), (0.03, 0.0556, 0.04), (-0.03, 0.0556, 0.04), plate, False)
            + gun(loft([(-0.17, 0.036, 0.036), (-0.07, 0.038, 0.038), (-0.05, 0.026, 0.026)], breech, 6, caps=(cap, None)))
            + gun(loft([(-0.05, 0.023, 0.023), (0.12, 0.02, 0.02)], steel, 6))
            + gun(loft([(0.12, 0.02, 0.02), (0.17, 0.038, 0.038)], breech, 6, caps=(None, lens))))
    for y, r in ((-0.02, 0.035), (0.035, 0.032), (0.09, 0.029)):
        tris += gun(loft([(y - 0.011, r, r), (y + 0.011, r, r)], ring, 6, caps=(ring, ring)))
    # Колба сбоку блока, вдоль ствола.
    tris += at(rot(loft([(-0.05, 0.016, 0.016), (0.05, 0.016, 0.016)], flask, 5, caps=(cap, cap)), rx=-90.0), 0.05, 0.035, -0.02)
    return Model("pistol", a).part("body", (0.0, 0.0, 0.0), tris)


def superheroes_hoop():
    """Неоновый обруч: цель спорта. Щит это вывеска с крыши: тёмное поле, по кромке лампочки,
    в середине неоновая звезда; обруч светится кораллом, сетка из цепей, стойка стальная с
    полосой опасности. Кольцо и щит там же и тех же размеров, что у пиратов."""
    a = Atlas(64, 64, 367)
    a.rect(0, 0, 32, 24, NIGHT)
    # Неоновая звезда: жёлтая трубка по контуру, вокруг отсвет, внутри синее свечение.
    for j in range(24):
        for i in range(32):
            dx, dy = i - 15.5, 11.5 - j
            d = math.hypot(dx, dy)
            r = si._star_radius(math.atan2(dy, dx), 9.0, 4.0)
            if abs(d - r) < 0.75:
                a.px(i, j, GOLD_L if (i + j) % 5 else WHITE)
            elif d < r:
                a.px(i, j, BLUE if d < r - 2.0 else mix(BLUE, GOLD, 0.3))
            elif d < r + 1.4:
                a.px(i, j, mix(NIGHT, GOLD_D, 0.5))
    # Рама и лампочки по кромке через одну: жёлтая, коралловая.
    for x, y, w, h in ((0, 0, 32, 1), (0, 23, 32, 1), (0, 0, 1, 24), (31, 0, 1, 24)):
        a.rect(x, y, w, h, METAL_D)
    k = 0
    for x in range(2, 30, 3):
        for y in (2, 21):
            a.px(x, y, GOLD_L if k % 2 == 0 else CORAL), a.px(x + 1, y, GOLD if k % 2 == 0 else RED)
        k += 1
    for y in range(5, 20, 3):
        for x in (2, 28):
            a.px(x, y, CORAL if k % 2 == 0 else GOLD_L), a.px(x + 1, y, RED if k % 2 == 0 else GOLD)
        k += 1
    board = a.region(0, 0, 32, 24)
    # Обруч: коралловая трубка с белой сердцевиной.
    a.rect(32, 0, 16, 4, CORAL)
    a.rect(32, 1, 16, 1, WHITE), a.rect(32, 0, 16, 1, PEACH), a.rect(32, 3, 16, 1, RED)
    ring = a.region(32, 0, 16, 4)
    # Сетка из цепей: ромбы звеньев, в узлах светлые кольца.
    for y in range(16):
        for x in range(32):
            p, q = (x + y) % 4, (x - y) % 4
            if p == 0 and q == 0:
                a.px(32 + x, 8 + y, WHITE)
            elif p == 0 or q == 0:
                a.px(32 + x, 8 + y, METAL_L if (x + y // 2) % 3 else METAL)
    net = a.region(32, 8, 32, 16)
    # Стойка: стальная балка с клёпками, у земли полоса опасности.
    a.rect(0, 24, 8, 32, METAL)
    a.rect(1, 24, 1, 32, METAL_L), a.rect(6, 24, 2, 32, METAL_D)
    for y in range(26, 56, 5):
        a.px(3, y, METAL_D), a.px(4, y, GREY)
    hazard(a, 0, 48, 8, 6)
    a.rect(0, 54, 8, 2, METAL_D)
    post = a.region(0, 24, 8, 32)
    plates(a, 8, 24, 8, 8, METAL_D, 4, 4)
    a.px(11, 27, RED), a.px(12, 28, GOLD)
    bracket = a.region(8, 24, 8, 8)
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
    edge = (u0, v0, u0 + (u1 - u0) / 32.0, v1)
    for x in (-0.65, 0.65):
        faces += quad((x, 3.875, -0.15), (x, 3.875, -0.09), (x, 2.925, -0.09), (x, 2.925, -0.15), edge)
    for y in (2.925, 3.875):
        faces += quad((0.65, y, -0.15), (-0.65, y, -0.15), (-0.65, y, -0.09), (0.65, y, -0.09), edge)
    return Model("hoop", a).part("body", (0.0, 0.0, 0.0),
                                 loft([(0.0, 0.09, 0.09), (3.9, 0.07, 0.07)], post, 5)
                                 + loft([(0.0, 0.3, 0.3), (0.12, 0.2, 0.2)], post, 5, flat=True)
                                 + at(box((0.3, 0.4, 0.1), bracket, bracket, bracket), 0.0, 3.4, -0.05)
                                 + at(box((0.06, 0.06, 0.2), ring, ring, ring), 0.0, rim_y, -0.2)
                                 + faces + ring_tris + basket + flip(basket))


MODELS = [superheroes_cannon, superheroes_palm, superheroes_flag, superheroes_lighthouse, superheroes_cart,
          superheroes_cart_rival, superheroes_pistol, superheroes_hoop]


if __name__ == "__main__":
    models = [f() for f in MODELS]
    for m in models:
        print("%-11s частей %d, треугольников %3d%s" % (m.name, len(m.parts), m.tris(),
                                                        "  БОЛЬШЕ %d" % lm.MAX_TRIS if m.tris() > lm.MAX_TRIS else ""))
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
