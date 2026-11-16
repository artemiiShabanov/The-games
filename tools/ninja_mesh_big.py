#!/usr/bin/env python3
"""Крупный реквизит и транспорт «Ниндзя» для low poly и «продвинутых» (#137): зеркала моделей
космоса из `space_mesh_big.py` (а те зеркала пиратских из `lowpoly_meshes.py`) с теми же именами
слотов, частей и точками вращения, тем же нулём и габаритами, чтобы десять 3D-демок работали
без правок. Цвета из основы 16/32 (`ninja16.PALETTE`) через `ninja_mesh_chars` и
`ninja_mesh_items`.

  cannon      мортира для фейерверка на красном лаковом станке (жерло в −Z, как у пушки)
  palm        красный клён; атлас: слева кора ствола, справа ветка с листвой и вырезом по
              прозрачности (эти же половины берёт `ThreedScreen.add_palm`)
  flag        знамя нобори: части `pole` (бамбуковый шест с перекладиной) и `cloth` (узкое
              высокое полотнище с солнцем)
  lighthouse  пагода в пять ярусов с золотым шпилем, высота маяка
  cart        повозка-рикша героя: `body`, оси `axle_f`, `axle_r`; машина без паруса и мачты:
              чёрный лаковый кузов с красной подушкой, оглобли с перекладиной, два бумажных
              фонаря вместо фар, сложенный верх за спинкой
  cart_rival  повозка чужого клана: те же части, красный лаковый короб-паланкин под низкой
              крышей, клин-таран спереди, два флажка сасимоно на корме (ниже 0,3 м)
  pistol      кунай в руке ниндзя (синий рукав, белая обмотка), вид от первого лица, остриё в −Z
  hoop        обруч под тории: красный столб с перекладиной тории, щит-дощечка с солнцем;
              кольцо там же и того же размера

    python3 tools/ninja_mesh_big.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from lowpoly_meshes import Atlas, Model, at, box, flip, loft, mul, quad, rgb, rot  # noqa: E402
from ninja_mesh_chars import (BLACK, BLUE, BLUE_D, BLUE_L, GOLD, GOLD_D, GOLD_L, GREY, LACQ, LACQ_D,  # noqa: E402
                              LACQ_L, RED, RED_D, RED_L, SKIN, SKIN_D, STEEL, STEEL_D, WHITE)
from ninja_mesh_items import (BAMBOO, BAMBOO_D, BAMBOO_L, CORAL, MOSS, MOSS_D, STONE, STONE_D,  # noqa: E402
                              STONE_L, STRAW, STRAW_D, STRAW_L, WOOD, WOOD_D, WOOD_L, rope)

# Свои тона набора: кора клёна, сухой бамбук шестов, бумага фонарей, черепица.
BARK, BARK_D, BARK_L = rgb("6A4630"), rgb("3A2622"), rgb("94684A")
CANE, CANE_D, CANE_L = rgb("B2762E"), rgb("70461E"), rgb("DCA85A")
PAPER, PAPER_D = rgb("F6E6B4"), rgb("D8B66A")
TILE, TILE_D, TILE_L = rgb("3E4258"), rgb("24263A"), rgb("666C86")
SQ2 = math.sqrt(2.0)


def lacquer(a, x, y, w, h, base, hi):
    """Лак: ровный тон с косыми бликами и тёмной нижней кромкой."""
    a.rect(x, y, w, h, base)
    for j in range(h):
        for i in range(w):
            if (i + j * 2) % 13 == 0 and j < h - 2:
                a.px(x + i, y + j, hi)
    a.rect(x, y + h - 1, w, 1, mul(base, 0.6))


def planks(a, x, y, w, h, base, dark, step=4):
    """Доски вдоль: швы, волокна и шляпки гвоздей."""
    a.rect(x, y, w, h, base)
    for i in range(0, w, step):
        a.rect(x + i, y, 1, h, dark)
        for j in range(1 + (i // step) % 3, h, 5):
            a.px(x + i + 2, y + j, mul(base, 0.86))
        a.px(x + i + 1, y + 1, mul(base, 1.2))
    a.noise(x, y, w, h, 0.07)


def cane(a, x, y, w, h, base=CANE, dark=CANE_D, light=CANE_L, step=6):
    """Бамбук стоймя: блик вдоль ствола, узлы кольцами."""
    a.rect(x, y, w, h, base)
    a.rect(x + w // 2 - 1, y, 2, h, light)
    a.rect(x, y, 1, h, dark), a.rect(x + w - 1, y, 1, h, dark)
    for j in range(2, h, step):
        a.rect(x, y + j, w, 1, dark)
        if j + 1 < h:
            a.rect(x, y + j + 1, w, 1, light)
    a.noise(x, y, w, h, 0.05)


def mon(a, cx, cy, c=GOLD, hi=GOLD_L):
    """Герб клана: кольцо с точкой, 5×5 пикселей."""
    for i in range(-2, 3):
        for j in range(-2, 3):
            if 1.5 < math.hypot(i, j) < 2.6:
                a.px(cx + i, cy + j, c)
    a.px(cx, cy, c), a.px(cx - 1, cy - 2, hi)


def paint_wheel(a, x0, y0, felloe=WOOD, spoke=WOOD_L, hub=GOLD, back=LACQ_D):
    """Деревянное колесо 16×16: железная шина, обод, восемь спиц, ступица. Вокруг прозрачно."""
    a.rect(x0, y0, 16, 16, back)
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            ang = math.atan2(j - 7.5, i - 7.5)
            if d > 7.7:
                a.clear(x0 + i, y0 + j)
            elif d > 6.5:
                a.px(x0 + i, y0 + j, STEEL_D if int((ang + math.pi) * 8 / math.pi) % 2 == 0 else BLACK)
            elif d > 4.9:
                a.px(x0 + i, y0 + j, felloe if d > 5.6 else mul(felloe, 0.72))
            elif d < 1.2:
                a.px(x0 + i, y0 + j, BLACK)
            elif d < 2.4:
                a.px(x0 + i, y0 + j, hub)
            elif abs(math.sin(ang * 4.0)) < 0.34:
                a.px(x0 + i, y0 + j, spoke)
    return a.region(x0, y0, 16, 16)


def cart_axles(m, rim, wheel, radius, half, x, n, rod=None):
    """Оси гонок `axle_f` и `axle_r`: точки вращения как у пиратской повозки, демки крутят их
    вокруг X и поворачивают переднюю. `rod` рисует балку моста между колёсами."""
    for part, z in (("axle_f", -0.72), ("axle_r", 0.72)):
        tris = []
        for side in (-x, x):
            tris += at(rot(loft([(-half, radius, radius), (half, radius, radius)], rim, n,
                                caps=(wheel, wheel), flat=True), rz=90.0), side, 0.32, z)
        if rod:
            tris += at(rot(loft([(-x, 0.045, 0.045), (x, 0.045, 0.045)], rod, 4, flat=True), rz=90.0), 0.0, 0.32, z)
        m.part(part, (0.0, 0.32, z), tris, "body")


def ninja_cannon():
    """Мортира для фейерверка: короткий толстый ствол из тёмной бронзы с раструбом, золотыми
    обручами и верёвочной обвязкой, по бокам бумажные обереги; станок красного лака с гербом,
    по бокам деревянные колёса."""
    a = Atlas(64, 32, 411)
    # Ствол: верх куска это жерло. Золотой обруч, бронза, две обвязки, у казны тёмный пояс.
    a.rect(0, 0, 32, 16, STEEL_D)
    for y in range(16):
        for x in range(32):
            if (x * 3 + y) % 7 == 0:
                a.px(x, y, mul(STEEL_D, 1.25))
    a.rect(0, 0, 32, 2, GOLD), a.rect(0, 2, 32, 1, GOLD_D)
    a.rect(0, 3, 32, 1, RED)
    rope(a, 0, 6, 32)
    rope(a, 0, 11, 32)
    a.rect(0, 14, 32, 2, BLACK)
    for x in range(1, 32, 4):
        a.px(x, 14, GOLD_D)
    # Обереги: белые полоски с тушью на обоих бортах ствола.
    for x0 in (6, 23):
        a.rect(x0, 4, 3, 7, WHITE)
        a.px(x0 + 1, 5, BLACK), a.px(x0 + 1, 7, BLACK), a.px(x0, 8, BLACK), a.px(x0 + 2, 8, BLACK)
        a.rect(x0, 10, 3, 1, RED)
    a.shade(0, 0, 32, 16, 1.0, 1.0, 0.7)
    a.noise(0, 0, 32, 16, 0.07)
    barrel = a.region(0, 0, 32, 16)
    # Жерло: золотой край, чёрный канал, красная искра заряда.
    a.rect(32, 0, 8, 8, GOLD_D)
    a.rect(33, 1, 6, 6, LACQ_D)
    a.rect(34, 2, 4, 4, BLACK)
    a.px(35, 3, RED), a.px(36, 4, CORAL)
    bore = a.region(32, 0, 8, 8)
    # Станок: красный лак в чёрной раме, золотой герб, заклёпки.
    lacquer(a, 0, 16, 32, 12, RED, RED_L)
    a.rect(0, 16, 32, 1, LACQ), a.rect(0, 26, 32, 2, LACQ)
    for x in range(0, 32, 8):
        a.rect(x, 16, 1, 12, LACQ)
        a.px(x + 1, 18, GOLD), a.px(x + 1, 24, GOLD)
    mon(a, 4, 22), mon(a, 12, 22), mon(a, 20, 22), mon(a, 28, 22)
    a.shade(0, 16, 32, 12, 1.08, 0.8, 0.9)
    a.noise(0, 16, 32, 12, 0.05)
    body = a.region(0, 16, 32, 12)
    disc = paint_wheel(a, 40, 0, RED, WOOD_L, GOLD, LACQ_D)
    a.rect(56, 0, 8, 4, BLACK)
    a.rect(56, 1, 8, 1, STEEL_D)
    rim = a.region(56, 0, 8, 4)
    m = Model("cannon", a)
    side = lambda x: at(rot(loft([(-0.04, 0.24, 0.24), (0.04, 0.24, 0.24)], rim, 8, caps=(disc, disc), flat=True), rz=90.0),
                        x, 0.24, 0.2)
    return m.part("body", (0.0, 0.0, 0.0),
                  at(rot(loft([(-0.5, 0.1, 0.1), (-0.44, 0.19, 0.19), (-0.3, 0.2, 0.2), (-0.24, 0.16, 0.16),
                               (0.28, 0.16, 0.16), (0.36, 0.22, 0.22), (0.52, 0.25, 0.25), (0.56, 0.2, 0.2)], barrel, 8,
                              caps=(bore, bore)), rx=-90.0), 0.0, 0.54, -0.1)
                  + at(box((0.46, 0.24, 0.85), body, body, None, (0.8, 1.0)), 0.0, 0.3, 0.1)
                  + at(box((0.3, 0.2, 0.3), body, body, None, (0.7, 0.7)), 0.0, 0.1, 0.1)
                  + side(-0.28) + side(0.28))


def ninja_palm():
    """Красный клён: тёмный изогнутый ствол со мхом и раскидистая крона в два яруса из плоских
    веток. Ветка это плоскость с вырезом по прозрачности, как лист пальмы: `ThreedScreen.add_palm`
    кладёт на свои ленты ту же правую половину атласа."""
    a = Atlas(32, 32, 413)
    a.rect(0, 0, 16, 32, BARK)
    for x in range(16):
        tone = (1.0, 0.8, 1.15, 0.9, 0.7, 1.05)[(x * 5 + x // 4) % 6]
        for y in range(32):
            a.px(x, y, mul(BARK, tone))
    for k in range(18):
        x, y = a.rng.randrange(16), a.rng.randrange(29)
        a.rect(x, y, 1, a.rng.randrange(2, 4), BARK_D)
    for x, y in ((3, 26), (4, 27), (3, 27), (11, 20), (12, 21), (7, 29), (8, 30), (13, 28)):
        a.px(x, y, MOSS), a.px(x, y + 1, MOSS_D)
    a.px(9, 9, BARK_L), a.px(9, 10, BARK_D), a.px(10, 10, BARK_D)
    a.shade(0, 0, 16, 32, 1.0, 0.9, 0.65)
    a.noise(0, 0, 16, 32, 0.06)
    trunk = a.region(0, 0, 16, 32)
    # Ветка: тёмный сучок по оси, вокруг резные листья красного, коралла и золота, край зубцами.
    for y in range(32):
        k = min(y / 30.0, 1.0)
        half = 1.5 + 6.0 * math.sin(math.pi * k) ** 0.5 + 0.9 * math.sin(y * 1.9)
        for x in range(16):
            dx = abs(x - 7.5)
            if dx > half or (dx > half - 1.6 and (x * 3 + y * 5) % 3 == 0):
                continue
            c = RED
            n = (x * 7 + y * 11 + (x * y) % 5) % 13
            if dx < 1.0 and y < 24:
                c = BARK_D
            elif n == 0:
                c = GOLD
            elif n in (1, 2):
                c = CORAL
            elif n in (3, 4):
                c = RED_L
            elif n in (5, 6) or dx > half - 1.2:
                c = RED_D
            a.px(16 + x, y, c)
    a.noise(16, 0, 16, 32, 0.05)
    leaf = a.region(16, 0, 16, 32)
    top = (0.55, 4.2, 0.1)
    tris = loft([(0.0, 0.26, 0.26), (1.0, 0.17, 0.17, 0.1, 0.0), (2.2, 0.14, 0.14, 0.3, 0.04), (3.3, 0.11, 0.11, 0.46, 0.08),
                 (4.3, 0.05, 0.05, 0.55, 0.1)], trunk, 5)

    def bough(cx, cy, cz, ang, length, droop, lift, width):
        d = (math.sin(ang), 0.0, math.cos(ang))
        q = (math.cos(ang) * width, 0.0, -math.sin(ang) * width)
        far = (cx + d[0] * length, cy - droop, cz + d[2] * length)
        mid = (cx - d[0] * 0.3, cy + lift, cz - d[2] * 0.3)
        return quad((mid[0] - q[0] * 0.5, mid[1], mid[2] - q[2] * 0.5), (mid[0] + q[0] * 0.5, mid[1], mid[2] + q[2] * 0.5),
                    (far[0] + q[0], far[1], far[2] + q[2]), (far[0] - q[0], far[1], far[2] - q[2]), leaf)

    # Нижний ярус шире и свисает, верхний короче и приподнят: крона шапкой, а не зонтом.
    for k in range(6):
        tris += bough(top[0] - 0.08, top[1] - 0.75, top[2], 2.0 * math.pi * k / 6.0 + 0.2, 1.75, 0.3 + 0.1 * (k % 2), 0.3, 0.8)
    for k in range(5):
        tris += bough(top[0], top[1], top[2], 2.0 * math.pi * k / 5.0 + 0.7, 1.25, 0.28, 0.42, 0.7)
    return Model("palm", a).part("body", (0.0, 0.0, 0.0), tris)


def ninja_flag():
    """Знамя нобори: бамбуковый шест на каменном основании, наверху перекладина и золотое
    навершие; узкое высокое белое полотнище на красных петлях, с красным солнцем, тушью и синей
    каймой понизу. Полотнище отдельной частью у шеста."""
    a = Atlas(64, 32, 415)
    # Полотнище 16×32: слева край у шеста с петлями, сверху петли перекладины.
    a.rect(0, 0, 16, 32, WHITE)
    for y in range(4, 32, 6):
        a.rect(0, y, 16, 1, GREY)
    for j in range(11):
        for i in range(11):
            d = math.hypot(i - 5.0, j - 5.0)
            if d < 4.6:
                a.px(3 + i, 3 + j, RED if d < 3.8 or (i + j) % 2 else RED_D)
    # Знаки тушью: три столбика штрихов.
    for x, y, w, h in ((5, 16, 7, 1), (8, 15, 1, 5), (5, 19, 3, 1), (10, 19, 2, 1),
                       (5, 22, 1, 4), (7, 22, 5, 1), (11, 22, 1, 4), (7, 25, 5, 1), (8, 23, 2, 1)):
        a.rect(x, y, w, h, BLACK)
    a.rect(0, 28, 16, 4, BLUE)
    a.rect(0, 28, 16, 1, BLUE_D)
    for x in range(1, 16, 3):
        a.px(x, 30, BLUE_L)
    for y in range(1, 28, 4):
        a.rect(0, y, 2, 2, RED)
    for x in range(3, 16, 4):
        a.rect(x, 0, 2, 2, RED)
    a.rect(15, 0, 1, 28, GREY)
    a.noise(0, 0, 16, 32, 0.06)
    cloth = a.region(0, 0, 16, 32)
    cane(a, 32, 0, 8, 32)
    pole = a.region(32, 0, 8, 32)
    # Основание: тёсаный камень со мхом.
    a.rect(40, 0, 8, 8, STONE)
    a.rect(40, 0, 8, 1, STONE_L), a.rect(40, 7, 8, 1, STONE_D), a.rect(44, 0, 1, 8, STONE_D)
    a.px(41, 5, MOSS), a.px(42, 6, MOSS), a.px(46, 6, MOSS_D)
    a.noise(40, 0, 8, 8, 0.1)
    base = a.region(40, 0, 8, 8)
    a.rect(48, 0, 8, 8, GOLD)
    a.rect(48, 0, 8, 2, GOLD_L), a.rect(48, 6, 8, 2, GOLD_D)
    a.px(51, 3, WHITE)
    knob = a.region(48, 0, 8, 8)
    m = Model("flag", a)
    m.part("pole", (0.0, 0.0, 0.0),
           loft([(0.0, 0.05, 0.05), (2.7, 0.04, 0.04)], pole, 4, caps=(None, knob))
           + loft([(0.0, 0.26, 0.26), (0.14, 0.18, 0.18)], base, 5, caps=(None, base), flat=True)
           # Перекладина держит верх полотнища.
           + at(rot(loft([(-0.36, 0.022, 0.022), (0.36, 0.022, 0.022)], pole, 4, flat=True), rz=90.0), 0.33, 2.64, 0.0)
           + at(loft([(0.0, 0.03, 0.03), (0.05, 0.065, 0.065), (0.12, 0.0, 0.0)], knob, 5), 0.0, 2.7, 0.0))
    m.part("cloth", (0.04, 2.3, 0.0),
           quad((0.04, 2.62, 0.0), (0.66, 2.62, 0.0), (0.66, 1.2, 0.0), (0.04, 1.2, 0.0), cloth), "pole")
    return m


def ninja_lighthouse():
    """Пагода: ориентир на горизонте высотой с маяк. Каменное основание, пять ярусов белёных
    стен в красном каркасе, над каждым широкая черепичная крыша с красным карнизом, сверху
    золотой шпиль с кольцами."""
    a = Atlas(64, 64, 417)
    # Стена лентой вокруг яруса, четыре грани по 16: балка, решётчатое окно, перила.
    a.rect(0, 0, 64, 16, WHITE)
    for x0 in range(0, 64, 16):
        a.rect(x0, 0, 2, 16, RED_D), a.rect(x0 + 14, 0, 2, 16, RED_D)
        a.rect(x0 + 5, 4, 6, 6, LACQ)
        for i in (6, 8):
            a.rect(x0 + i, 5, 1, 4, GOLD)
        a.px(x0 + 9, 5, PAPER), a.px(x0 + 9, 7, PAPER_D)
        for i in range(2, 14, 2):
            a.px(x0 + i, 13, RED)
    a.rect(0, 0, 64, 2, RED), a.rect(0, 2, 64, 1, RED_D)
    a.rect(0, 11, 64, 1, GREY)
    a.rect(0, 12, 64, 1, RED), a.rect(0, 14, 64, 2, RED_D)
    a.shade(0, 0, 64, 16, 0.8, 1.05, 1.0)
    a.noise(0, 0, 64, 16, 0.04)
    wall = a.region(0, 0, 64, 16)
    # Крыша: ряды черепицы, книзу красный карниз с золотыми торцами.
    a.rect(0, 16, 64, 12, TILE)
    for y in range(16, 24, 2):
        a.rect(0, y, 64, 1, TILE_D)
    for x in range(0, 64, 2):
        a.rect(x, 16, 1, 8, TILE_D)
        a.px(x + 1, 17 + (x // 2) % 2 * 2, TILE_L)
    a.rect(0, 24, 64, 1, TILE_L)
    a.rect(0, 25, 64, 2, RED), a.rect(0, 27, 64, 1, RED_D)
    for x in range(1, 64, 4):
        a.px(x, 26, GOLD)
    for x0 in range(0, 64, 16):
        a.rect(x0 + 7, 16, 2, 9, TILE_L)
    a.noise(0, 16, 64, 12, 0.05)
    roof = a.region(0, 16, 64, 12)
    # Основание: каменная кладка со мхом.
    a.rect(0, 28, 32, 12, STONE)
    for row, y in enumerate(range(28, 40, 4)):
        a.rect(0, y, 32, 1, STONE_D)
        for x in range((row % 2) * 4, 32, 8):
            a.rect(x, y, 1, 4, STONE_D)
            a.px(x + 2, y + 1, STONE_L)
    for x in range(0, 32, 3):
        a.px(x, 38 + x % 2, MOSS_D if x % 2 else MOSS)
    a.noise(0, 28, 32, 12, 0.08)
    stone = a.region(0, 28, 32, 12)
    # Шпиль: золото с кольцами.
    a.rect(32, 28, 16, 12, GOLD)
    for y in range(28, 40, 3):
        a.rect(32, y, 16, 1, GOLD_D)
        a.rect(32, y + 1, 16, 1, GOLD_L)
    a.shade(32, 28, 16, 12, 1.0, 0.9, 0.7)
    gold = a.region(32, 28, 16, 12)
    # Испод крыши: тёмное дерево с красными стропилами.
    a.rect(48, 28, 16, 12, LACQ_D)
    for x in range(48, 64, 3):
        a.rect(x, 28, 1, 12, RED_D)
    under = a.region(48, 28, 16, 12)
    ph = math.pi / 4.0
    tris = (loft([(0.0, 1.5, 1.5), (0.5, 1.42, 1.42)], stone, 4, ph, (None, stone), True)
            + loft([(0.5, 1.3, 1.3), (0.8, 1.26, 1.26)], stone, 4, ph, (None, stone), True))
    y = 0.8
    for i in range(5):
        w = (0.84 - 0.115 * i) * SQ2
        nxt = (0.84 - 0.115 * (i + 1)) * SQ2
        e = w + (0.5 - 0.03 * i) * SQ2
        tall = 0.78 if i else 0.95
        tris += loft([(y, w, w), (y + tall, w, w)], wall, 4, ph, (None, None), True)
        yb = y + tall
        if i < 4:
            tris += loft([(yb - 0.03, e, e), (yb + 0.07, e, e), (yb + 0.2, 0.55 * e + 0.45 * nxt, 0.55 * e + 0.45 * nxt),
                          (yb + 0.46, nxt, nxt)], roof, 4, ph, (under, None), True)
            y = yb + 0.44
        else:
            # Верхняя крыша шатром до шпиля.
            tris += loft([(yb - 0.03, e, e), (yb + 0.07, e, e), (yb + 0.26, 0.5 * e, 0.5 * e), (yb + 0.72, 0.1, 0.1)],
                         roof, 4, ph, (under, None), True)
            y = yb + 0.66
    tris += loft([(y, 0.07, 0.07), (y + 0.2, 0.2, 0.2), (y + 0.34, 0.07, 0.07), (y + 0.56, 0.16, 0.16), (y + 0.66, 0.06, 0.06),
                  (y + 0.86, 0.12, 0.12), (y + 0.96, 0.04, 0.04), (9.0, 0.012, 0.012)], gold, 5)
    return Model("lighthouse", a).part("body", (0.0, 0.0, 0.0), tris)


def paint_lantern(a, x0, y0, sign=RED):
    """Бумажный фонарь 16×8 лентой вокруг: чёрные обручи сверху и снизу, тёплая бумага с рёбрами,
    на гранях знак."""
    a.rect(x0, y0, 16, 8, PAPER)
    for x in range(x0, x0 + 16, 4):
        a.rect(x, y0, 1, 8, PAPER_D)
        a.px(x + 2, y0 + 3, sign), a.px(x + 2, y0 + 4, sign)
    a.rect(x0, y0 + 2, 16, 1, GOLD_L)
    a.rect(x0, y0, 16, 1, BLACK), a.rect(x0, y0 + 7, 16, 1, BLACK)
    return a.region(x0, y0, 16, 8)


def ninja_cart():
    """Повозка-рикша героя: низкая колёсная машина без паруса и мачты. Дощатая рама, чёрный
    лаковый кузов с красным поручнем и золотым гербом на бортах, красная стёганая подушка,
    высокая спинка, за ней сложенный гармошкой синий верх; вперёд идут две оглобли с перекладиной
    в красной обмотке, на них два бумажных фонаря вместо фар; над задними колёсами красные
    крылья. Колёса деревянные со спицами в железной шине. Части и точки вращения как у пиратской
    повозки: `body`, `axle_f`, `axle_r`."""
    a = Atlas(64, 64, 419)
    # Борт лентой вокруг ящика: четверти это правый борт, перёд, левый борт, корма.
    lacquer(a, 0, 0, 64, 12, LACQ, LACQ_L)
    a.rect(0, 0, 64, 2, RED), a.rect(0, 2, 64, 1, GOLD_D)
    for x in range(0, 64, 16):
        a.rect(x, 3, 1, 9, LACQ_D)
        a.px(x + 1, 4, GOLD), a.px(x + 14, 4, GOLD), a.px(x + 1, 10, GOLD), a.px(x + 14, 10, GOLD)
    mon(a, 8, 7), mon(a, 40, 7)
    # Перёд: плетёная бамбуковая вставка; корма: красный шнур с кистями.
    for j in range(5):
        for i in range(10):
            a.px(19 + i, 4 + j, CANE_L if (i + j) % 2 else CANE_D)
    a.rect(52, 5, 8, 1, RED)
    for x in (53, 58):
        a.rect(x, 6, 1, 3, RED), a.px(x, 9, GOLD)
    a.shade(0, 0, 64, 12, 1.1, 0.82, 1.0)
    a.noise(0, 0, 64, 12, 0.04)
    hull = a.region(0, 0, 64, 12)
    # Подушка: красная стёжка ромбами с золотыми узелками.
    a.rect(0, 12, 16, 16, RED)
    for j in range(16):
        for i in range(16):
            if (i + j) % 6 == 0 or (i - j) % 6 == 0:
                a.px(i, 12 + j, RED_D)
            if (i + j) % 6 == 0 and (i - j) % 6 == 0:
                a.px(i, 12 + j, GOLD)
    a.rect(0, 12, 16, 1, LACQ), a.rect(0, 27, 16, 1, LACQ), a.rect(0, 12, 1, 16, LACQ), a.rect(15, 12, 1, 16, LACQ)
    a.noise(0, 12, 16, 16, 0.05)
    seat = a.region(0, 12, 16, 16)
    wheel = paint_wheel(a, 16, 12)
    a.rect(32, 12, 8, 4, BLACK)
    for x in range(32, 40, 2):
        a.px(x, 13, STEEL_D)
    a.rect(32, 15, 8, 1, WOOD_D)
    rim = a.region(32, 12, 8, 4)
    # Крыло и поручень: красный лак с золотой кромкой.
    lacquer(a, 32, 16, 8, 12, RED, RED_L)
    a.rect(32, 16, 8, 1, GOLD), a.rect(32, 27, 8, 1, RED_D)
    fender = a.region(32, 16, 8, 12)
    # Оглобля: светлое дерево, у конца красная обмотка.
    a.rect(40, 12, 8, 16, WOOD)
    a.rect(40, 12, 1, 16, WOOD_D), a.rect(43, 12, 2, 16, WOOD_L), a.rect(47, 12, 1, 16, WOOD_D)
    for y in range(12, 17):
        for x in range(40, 48):
            a.px(x, y, RED if (x + y) % 3 else RED_D)
    a.noise(40, 12, 8, 16, 0.05)
    shaft = a.region(40, 12, 8, 16)
    planks(a, 48, 12, 16, 16, WOOD, WOOD_D)
    floor = a.region(48, 12, 16, 16)
    # Сложенный верх: синяя ткань гармошкой с бамбуковыми дугами.
    a.rect(0, 32, 32, 16, BLUE)
    for y in range(32, 48, 4):
        a.rect(0, y, 32, 1, BLUE_D)
        a.rect(0, y + 1, 32, 1, BLUE_L)
        a.rect(0, y + 3, 32, 1, CANE)
    a.rect(0, 32, 2, 16, LACQ), a.rect(30, 32, 2, 16, LACQ)
    a.noise(0, 32, 32, 16, 0.05)
    hood = a.region(0, 32, 32, 16)
    lamp = paint_lantern(a, 32, 32)
    a.rect(48, 32, 8, 8, LACQ)
    a.rect(50, 34, 4, 4, GOLD)
    lamp_cap = a.region(48, 32, 8, 8)
    m = Model("cart", a)
    body = (at(box((0.8, 0.1, 2.0), floor, floor, None), 0.0, 0.45)
            # Кузов с подушкой, спинка и передний щиток.
            + at(box((0.88, 0.34, 0.92), hull, seat, None, (1.06, 1.04)), 0.0, 0.66, 0.36)
            + at(box((0.92, 0.42, 0.14), hull, fender, None), 0.0, 0.94, 0.84)
            + at(rot(box((0.78, 0.3, 0.06), hull, fender, None), rx=-22.0), 0.0, 0.62, -0.5)
            # Сложенный верх валиком за спинкой.
            + at(rot(loft([(-0.44, 0.12, 0.14), (0.44, 0.12, 0.14)], hood, 5, caps=(lamp_cap, lamp_cap)), rz=90.0), 0.0, 1.0, 0.98)
            # Перекладина оглобель.
            + at(rot(loft([(-0.42, 0.03, 0.03), (0.42, 0.03, 0.03)], shaft, 4, flat=True), rz=90.0), 0.0, 0.56, -1.46))
    for x in (-0.36, 0.36):
        # Оглобля от рамы вперёд, на ней фонарь.
        body += at(rot(box((0.055, 0.055, 1.0), shaft, shaft, None), rx=4.0), x, 0.53, -0.98)
        body += at(loft([(0.0, 0.05, 0.05), (0.04, 0.085, 0.085), (0.17, 0.085, 0.085), (0.21, 0.05, 0.05)], lamp, 4,
                        caps=(lamp_cap, lamp_cap)), x, 0.57, -1.2)
    for x in (-0.6, 0.6):
        # Крылья над задними колёсами.
        body += at(box((0.2, 0.05, 0.84), rim, fender, rim), x, 0.675, 0.72)
    m.part("body", (0.0, 0.0, 0.0), body)
    cart_axles(m, rim, wheel, 0.32, 0.05, 0.6, 8, shaft)
    return m


def ninja_cart_rival():
    """Повозка чужого клана: закрытый короб-паланкин на колёсах, без паруса и мачты. Красный
    лаковый короб в чёрной раме с бамбуковыми шторками и чёрным гербом, низкая чёрная крыша с
    красным коньком и вылетом карниза, спереди окованный клин-таран, на корме фонарь и два
    флажка сасимоно ниже 0,3 м. Колёса красные с чёрными спицами. Части и точки вращения те же,
    что у рикши."""
    a = Atlas(64, 64, 421)
    # Борт короба лентой: четверти это правый борт, перёд, левый борт, корма.
    lacquer(a, 0, 0, 64, 16, RED, RED_L)
    a.rect(0, 0, 64, 2, LACQ), a.rect(0, 14, 64, 2, LACQ)
    for x in range(0, 64, 16):
        a.rect(x, 0, 2, 16, LACQ), a.rect(x + 14, 0, 2, 16, LACQ)
        a.px(x + 1, 1, GOLD), a.px(x + 14, 1, GOLD), a.px(x + 1, 14, GOLD), a.px(x + 14, 14, GOLD)
    for x0 in (0, 32):
        # Окно со шторкой из бамбука и чёрный герб под ним.
        a.rect(x0 + 4, 3, 8, 5, LACQ_D)
        for y in range(4, 8):
            a.rect(x0 + 5, y, 6, 1, CANE_L if y % 2 else CANE)
        mon(a, x0 + 8, 11, BLACK, LACQ_L)
    # Перёд: смотровая щель; корма: дверца с золотой скобой.
    a.rect(19, 4, 10, 2, BLACK)
    a.px(21, 4, GOLD), a.px(26, 4, GOLD)
    a.rect(20, 9, 8, 1, RED_D)
    a.rect(52, 3, 8, 10, RED_D)
    a.rect(52, 3, 8, 1, LACQ), a.rect(55, 3, 1, 10, LACQ)
    a.px(57, 8, GOLD), a.px(57, 9, GOLD)
    a.shade(0, 0, 64, 16, 1.08, 0.82, 1.0)
    a.noise(0, 0, 64, 16, 0.04)
    hull = a.region(0, 0, 64, 16)
    # Крыша: чёрный лак с рёбрами, по карнизу красная кромка с золотом.
    a.rect(0, 16, 64, 8, LACQ)
    for x in range(0, 64, 4):
        a.rect(x, 16, 1, 6, LACQ_D)
        a.px(x + 2, 17, LACQ_L)
    a.rect(0, 16, 64, 1, RED)
    a.rect(0, 22, 64, 2, RED), a.rect(0, 23, 64, 1, RED_D)
    for x in range(2, 64, 8):
        a.px(x, 22, GOLD)
    a.noise(0, 16, 64, 8, 0.05)
    roof = a.region(0, 16, 64, 8)
    # Рама и таран: тёмное дерево в железных полосах.
    planks(a, 0, 24, 16, 16, rgb("5A3A30"), BARK_D)
    for y in (26, 36):
        a.rect(0, y, 16, 2, STEEL_D)
        for x in range(1, 16, 4):
            a.px(x, y, STEEL)
    deck = a.region(0, 24, 16, 16)
    wheel = paint_wheel(a, 16, 24, RED, LACQ_L, GOLD, BLACK)
    a.rect(32, 24, 8, 4, BLACK)
    for x in range(32, 40, 2):
        a.px(x, 25, RED_D)
    rim = a.region(32, 24, 8, 4)
    # Конёк крыши: красный брус с золотыми торцами.
    a.rect(40, 24, 8, 8, RED)
    a.rect(40, 24, 8, 1, RED_L), a.rect(40, 31, 8, 1, RED_D)
    a.rect(40, 24, 1, 8, GOLD), a.rect(47, 24, 1, 8, GOLD)
    ridge = a.region(40, 24, 8, 8)
    # Таран: железный лист с заклёпками и красным зубом.
    a.rect(48, 24, 16, 16, STEEL_D)
    for y in range(24, 40, 4):
        a.rect(48, y, 16, 1, BLACK)
        for x in range(49, 64, 4):
            a.px(x, y + 2, STEEL)
    for j in range(6):
        a.rect(56 - j // 2 - 1, 28 + j, 2 + (j // 2) * 2, 1, RED)
    a.noise(48, 24, 16, 16, 0.06)
    ram = a.region(48, 24, 16, 16)
    # Флажок сасимоно: красное поле, чёрная полоса, белый круг.
    a.rect(0, 40, 16, 24, RED)
    a.rect(0, 40, 16, 4, BLACK)
    for j in range(8):
        for i in range(8):
            if math.hypot(i - 3.5, j - 3.5) < 3.6:
                a.px(4 + i, 48 + j, WHITE if math.hypot(i - 3.5, j - 3.5) > 1.6 else BLACK)
    a.rect(0, 40, 1, 24, LACQ)
    a.noise(0, 40, 16, 24, 0.05)
    banner = a.region(0, 40, 16, 24)
    lamp = paint_lantern(a, 16, 40, BLACK)
    a.rect(32, 40, 8, 8, LACQ_D)
    a.rect(34, 42, 4, 4, RED)
    dark = a.region(32, 40, 8, 8)
    m = Model("cart_rival", a)
    e = 0.6 * SQ2
    ph = math.pi / 4.0
    body = (at(box((0.84, 0.1, 1.96), deck, deck, None), 0.0, 0.45)
            # Короб и крыша с вылетом.
            + at(box((0.82, 0.36, 1.2), hull, dark, None), 0.0, 0.68, 0.22)
            + at(loft([(0.0, e * 0.8, e * 1.12), (0.04, e * 0.8, e * 1.12), (0.16, e * 0.3, e * 0.86)], roof, 4, ph,
                      (dark, ridge), True), 0.0, 0.85, 0.22)
            + at(box((0.1, 0.05, 1.3), ridge, ridge, None), 0.0, 1.02, 0.22)
            # Клин-таран спереди: сужается к носу.
            + at(rot(box((0.8, 0.5, 0.26), ram, ram, deck, (0.3, 0.6)), rx=-90.0), 0.0, 0.53, -0.75)
            + at(box((0.86, 0.07, 0.08), rim, rim, rim), 0.0, 0.44, 0.98)
            # Фонарь на корме.
            + at(loft([(0.0, 0.04, 0.04), (0.03, 0.07, 0.07), (0.14, 0.07, 0.07), (0.17, 0.04, 0.04)], lamp, 5,
                      caps=(dark, dark)), 0.0, 0.5, 0.9))
    for x in (-0.36, 0.36):
        # Флажки на коротких древках по углам кормы.
        body += at(loft([(0.0, 0.012, 0.012), (0.3, 0.012, 0.012)], rim, 3, flat=True), x, 0.98, 0.74)
        body += quad((x, 1.27, 0.75), (x, 1.27, 0.9), (x, 1.03, 0.9), (x, 1.03, 0.75), banner)
    m.part("body", (0.0, 0.0, 0.0), body)
    cart_axles(m, rim, wheel, 0.32, 0.06, 0.6, 8, rim)
    return m


def ninja_pistol():
    """Кунай в руке ниндзя: оружие вида от первого лица, остриё смотрит в −Z, ноль в рукояти.
    Клинок ромбом с долом, рукоять в белой обмотке, кольцо с красной кистью; кулак в синей
    накладке, синий рукав с белой обмоткой запястья."""
    a = Atlas(32, 32, 423)
    # Клинок: верх куска это остриё. Четыре грани по 4: светлая, тёмная через одну, дол по ребру.
    a.rect(0, 0, 16, 8, STEEL)
    for x0 in range(0, 16, 4):
        tone = (1.3, 0.85, 1.1, 0.7)[x0 // 4]
        for y in range(8):
            for x in range(4):
                a.px(x0 + x, y, mul(STEEL, tone))
        a.rect(x0, 0, 1, 8, WHITE)
    a.rect(0, 7, 16, 1, STEEL_D)
    a.px(5, 2, WHITE), a.px(13, 4, WHITE)
    a.noise(0, 0, 16, 8, 0.05)
    blade = a.region(0, 0, 16, 8)
    # Кольцо и торцы: тёмная сталь с бликом.
    a.rect(16, 0, 8, 4, STEEL_D)
    a.rect(16, 0, 8, 1, STEEL)
    a.px(18, 1, WHITE)
    iron = a.region(16, 0, 8, 4)
    a.rect(24, 0, 8, 4, RED)
    a.rect(24, 0, 8, 1, RED_L), a.rect(24, 3, 8, 1, GOLD)
    for x in range(25, 32, 2):
        a.px(x, 2, RED_D)
    tassel = a.region(24, 0, 8, 4)
    # Рукоять: белая обмотка косыми витками.
    for y in range(8):
        for x in range(16):
            a.px(x, 8 + y, WHITE if (x + y * 2) % 4 < 2 else GREY)
    for x in range(0, 16, 4):
        a.px(x, 8 + (x // 2) % 8, BLACK)
    a.shade(0, 8, 16, 8, 1.0, 0.85, 0.8)
    grip = a.region(0, 8, 16, 8)
    # Кулак: пальцы с костяшками, сверху синяя накладка с золотой заклёпкой.
    a.rect(0, 16, 16, 8, SKIN)
    a.rect(0, 16, 16, 3, BLUE), a.rect(0, 19, 16, 1, BLUE_D)
    for x in (3, 7, 11, 15):
        a.rect(x, 20, 1, 4, SKIN_D)
    for x in (1, 5, 9, 13):
        a.px(x, 21, mul(SKIN, 1.1))
    a.px(8, 17, GOLD)
    a.shade(0, 16, 16, 8, 1.05, 0.85, 0.85)
    a.noise(0, 16, 16, 8, 0.04)
    hand = a.region(0, 16, 16, 8)
    # Рукав: синяя ткань со складками, у кисти белая обмотка витками.
    a.rect(16, 8, 16, 16, BLUE)
    for y in range(9, 19, 3):
        a.rect(16, y, 16, 1, BLUE_D)
        a.px(18 + y % 5, y + 1, BLUE_L)
    # Низ куска это запястье: кольца рукава идут от кисти к локтю.
    for y in range(19, 24):
        for x in range(16, 32):
            a.px(x, y, WHITE if (x + y * 2) % 5 else GREY)
    a.rect(16, 18, 16, 1, RED)
    a.shade(16, 8, 16, 16, 1.0, 0.85, 0.75)
    a.noise(16, 8, 16, 16, 0.05)
    sleeve = a.region(16, 8, 16, 16)
    ring = []
    for k in range(6):
        a0, a1 = 2 * math.pi * k / 6, 2 * math.pi * (k + 1) / 6
        p = lambda r, t: (r * math.sin(t), 0.06, 0.135 + r * math.cos(t))
        ring += quad(p(0.016, a0), p(0.016, a1), p(0.032, a1), p(0.032, a0), iron)
    return Model("pistol", a).part("body", (0.0, 0.0, 0.0),
                                   # Клинок ромбом: широкий в плечах, сходится к острию.
                                   at(rot(loft([(0.0, 0.014, 0.012), (0.035, 0.05, 0.014), (0.13, 0.042, 0.011),
                                                (0.31, 0.003, 0.003)], blade, 4, flat=True), rx=-90.0), 0.0, 0.06, -0.06)
                                   # Рукоять сквозь кулак до кольца.
                                   + at(rot(loft([(-0.11, 0.015, 0.015), (0.07, 0.017, 0.017)], grip, 5, caps=(iron, iron)),
                                            rx=-90.0), 0.0, 0.06, 0.0)
                                   + ring
                                   + quad((-0.012, 0.058, 0.16), (0.012, 0.058, 0.16), (0.016, -0.02, 0.19), (-0.016, -0.02, 0.19), tassel)
                                   # Кулак и большой палец поверх рукояти.
                                   + at(box((0.085, 0.1, 0.1), hand, hand, hand), 0.0, 0.035, 0.03)
                                   + at(box((0.03, 0.03, 0.08), hand, hand, hand), -0.02, 0.095, 0.01)
                                   + at(rot(loft([(0.0, 0.045, 0.045), (0.5, 0.06, 0.06)], sleeve, 4, math.pi / 4.0), rx=65.0), 0.0, -0.03, 0.07))


def ninja_hoop():
    """Обруч под тории: цель спорта. Красный лаковый столб на каменной пяте, наверху перекладина
    тории с чёрной кровлей; щит это дощечка эма с белым полем и красным солнцем-прицелом, обруч
    золотой, сетка из соломенных верёвок с белыми бумажными лентами. Кольцо и щит там же и тех
    же размеров, что у пиратов."""
    a = Atlas(64, 64, 425)
    # Щит: светлые доски в чёрной раме, белое поле, красное солнце с рамкой прицела.
    planks(a, 0, 0, 32, 24, WOOD, WOOD_D, 8)
    a.rect(4, 4, 24, 17, WHITE)
    for y in range(8, 21, 4):
        a.rect(4, y, 24, 1, GREY)
    for j in range(13):
        for i in range(13):
            d = math.hypot(i - 6.0, j - 6.0)
            if d < 5.6:
                a.px(10 + i, 7 + j, RED if d < 4.6 else RED_D)
    for x, y, w, h in ((10, 9, 12, 1), (10, 18, 12, 1), (10, 9, 1, 10), (21, 9, 1, 10)):
        a.rect(x, y, w, h, GOLD_L)
    a.rect(0, 0, 32, 2, LACQ), a.rect(0, 22, 32, 2, LACQ), a.rect(0, 0, 2, 24, LACQ), a.rect(30, 0, 2, 24, LACQ)
    for x, y in ((1, 1), (30, 1), (1, 22), (30, 22)):
        a.px(x, y, GOLD)
    a.noise(0, 0, 32, 24, 0.04)
    board = a.region(0, 0, 32, 24)
    a.rect(32, 0, 16, 4, GOLD)
    a.rect(32, 0, 16, 1, GOLD_L), a.rect(32, 3, 16, 1, GOLD_D)
    for x in range(33, 48, 4):
        a.px(x, 2, RED)
    ring = a.region(32, 0, 16, 4)
    # Сетка: верёвки ромбами, сверху белые бумажные ленты зигзагом.
    for y in range(16):
        for x in range(32):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                a.px(32 + x, 8 + y, STRAW_L if (x + y) % 8 else STRAW_D)
    for x0 in range(34, 64, 8):
        for j in range(6):
            a.rect(x0 + (j // 2) % 2, 8 + j, 2, 1, WHITE)
    rope(a, 32, 8, 32, 1)
    net = a.region(32, 8, 32, 16)
    # Столб: красный лак, чёрный пояс у земли, золотой обруч.
    lacquer(a, 0, 24, 8, 32, RED, RED_L)
    a.rect(0, 24, 1, 32, RED_D), a.rect(7, 24, 1, 32, RED_D)
    a.rect(0, 48, 8, 8, LACQ), a.rect(0, 47, 8, 1, GOLD)
    a.rect(0, 24, 8, 1, LACQ)
    a.shade(0, 24, 8, 32, 1.0, 0.9, 0.6)
    post = a.region(0, 24, 8, 32)
    # Перекладина тории: красный брус под чёрной кровлей.
    a.rect(8, 24, 24, 8, RED)
    a.rect(8, 24, 24, 3, LACQ), a.rect(8, 27, 24, 1, GOLD_D)
    a.rect(8, 31, 24, 1, RED_D)
    a.noise(8, 24, 24, 8, 0.04)
    beam = a.region(8, 24, 24, 8)
    a.rect(8, 32, 8, 8, LACQ)
    a.rect(8, 32, 8, 1, LACQ_L)
    cap = a.region(8, 32, 8, 8)
    a.rect(16, 32, 8, 8, STONE)
    a.rect(16, 32, 8, 1, STONE_L), a.rect(16, 39, 8, 1, STONE_D)
    a.px(18, 37, MOSS), a.px(21, 38, MOSS_D)
    a.noise(16, 32, 8, 8, 0.1)
    foot = a.region(16, 32, 8, 8)
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
    # Перекладина тории над щитом: брус и кровля с вылетом, концы шире низа.
    torii = (at(box((1.5, 0.1, 0.12), beam, cap, cap), 0.0, 3.94, -0.06)
             + at(box((1.74, 0.07, 0.2), cap, cap, cap, (1.08, 1.0)), 0.0, 4.02, -0.06))
    return Model("hoop", a).part("body", (0.0, 0.0, 0.0),
                                 loft([(0.0, 0.09, 0.09), (3.9, 0.07, 0.07)], post, 5)
                                 + loft([(0.0, 0.3, 0.3), (0.12, 0.2, 0.2)], foot, 5, caps=(None, foot), flat=True)
                                 + at(box((0.06, 0.06, 0.2), ring, ring, ring), 0.0, rim_y, -0.2)
                                 + faces + ring_tris + basket + flip(basket) + torii)


MODELS = [ninja_cannon, ninja_palm, ninja_flag, ninja_lighthouse, ninja_cart, ninja_cart_rival, ninja_pistol, ninja_hoop]


if __name__ == "__main__":
    models = [f() for f in MODELS]
    for m in models:
        print("%-11s частей %d, треугольников %3d%s" % (m.name, len(m.parts), m.tris(),
                                                        "  БОЛЬШЕ %d" % lm.MAX_TRIS if m.tris() > lm.MAX_TRIS else ""))
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
