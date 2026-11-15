#!/usr/bin/env python3
"""Крупный реквизит и транспорт «Замков» для low poly и «продвинутых» (#137): зеркала пиратских
моделей из `lowpoly_meshes.py` через космический набор `space_mesh_big.py`, с теми же именами
слотов, частей, родителей и точками вращения, тем же нулём и габаритами, чтобы десять 3D-демок
работали без правок. Цвета те же, что у рыцаря и стражника в `castles_mesh_chars.py`.

  cannon      баллиста на колёсах: ложе с воротом, дуга с тетивой, болт, щиток (ствол в −Z)
  palm        дуб: кривой ствол с корневыми лапами; атлас: слева кора, справа долька кроны
              (эти же половины берёт `ThreedScreen.add_palm`)
  flag        знамя с гербом: части `pole` (древко с золотым наконечником) и `cloth` (полотнище)
  lighthouse  сторожевая башня: каменный ствол с контрфорсами, галерея с зубцами, красная кровля
  cart        боевая повозка: `body`, оси `axle_f`, `axle_r`; на месте паруса вымпел на шесте
  cart_rival  повозка чужого герба: чёрная, с тараном, багровый вымпел; те же части
  pistol      арбалет в латной перчатке, вид от первого лица (болт в −Z, ноль в рукояти)
  hoop        турнирное кольцо: щит с гербом и цепная сетка; кольцо там же и того же размера

    python3 tools/castles_mesh_big.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from lowpoly_meshes import Atlas, Model, at, box, flip, loft, mul, quad, rgb, rot  # noqa: E402
from castles_mesh_chars import (BLACK, CRIM, CRIM_D, CRIM_L, GOLD, GOLD_D, GOLD_L, RAV, RAV_D, RAV_L,  # noqa: E402,F401
                                RED, RED_D, RED_L, STEEL, STEEL_D, STEEL_DD, STEEL_L, WHITE)

# Цвета набора сверх рыцаря: дерево, камень кладки, листва, черепица.
WOOD, WOOD_D, WOOD_L, WOOD_DD = rgb("A06C3A"), rgb("6A4424"), rgb("C48E54"), rgb("3E2814")
STONE, STONE_D, STONE_L = rgb("8C8E96"), rgb("565862"), rgb("B4B6BC")
MOSS = rgb("5E8A44")
LEAF, LEAF_D, LEAF_L = rgb("3E8C46"), rgb("1F5A32"), rgb("8FCF58")
BARK, BARK_D, BARK_L = rgb("6A4A30"), rgb("3A2818"), rgb("8E6844")
GRASS = rgb("5FA64A")


def wood(a, x, y, w, h, base=WOOD, vertical=False):
    """Доски со щелями, волокнами и сучками; `vertical` ставит доски стоймя."""
    a.rect(x, y, w, h, base)
    span = h if not vertical else w
    step = 4
    for k in range(0, span, step):
        tone = a.rng.uniform(0.9, 1.1)
        for j in range(h):
            for i in range(w):
                pos = j if not vertical else i
                if k <= pos < k + step:
                    c = mul(base, tone * (1.0 + 0.07 * math.sin(((i if not vertical else j) * 0.9) + k * 2.0)))
                    a.px(x + i, y + j, mul(base, 0.6) if pos == k else c)
    for _ in range(max(1, w * h // 110)):
        kx, ky = a.rng.randrange(w), a.rng.randrange(h)
        a.px(x + kx, y + ky, mul(base, 0.5))
    a.noise(x, y, w, h, 0.06)


def stone(a, x, y, w, h, base=STONE, bw=8, bh=5, mortar=None):
    """Кладка: ряды камней вразбежку, раствор, светлая кромка сверху, редкий мох."""
    mortar = mortar or mul(base, 0.55)
    a.rect(x, y, w, h, mortar)
    for row, j in enumerate(range(0, h, bh)):
        off = (row % 2) * (bw // 2)
        for i in range(-off, w, bw):
            tone = a.rng.uniform(0.88, 1.1)
            for jj in range(j + 1, min(j + bh, h)):
                for ii in range(max(i + 1, 0), min(i + bw, w)):
                    a.px(x + ii, y + jj, mul(base, tone * (1.1 if jj == j + 1 else 1.0)))
    for _ in range(max(1, w * h // 150)):
        a.px(x + a.rng.randrange(w), y + a.rng.randrange(h), MOSS)
    a.noise(x, y, w, h, 0.05)


def paint_wheel(a, x0, y0, iron=STEEL_DD, hub=GOLD):
    """Колесо 16×16: железный обод, дубовый венец, восемь спиц и ступица; вокруг прозрачно."""
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            ang = math.atan2(j - 7.5, i - 7.5)
            if d > 7.6:
                a.clear(x0 + i, y0 + j)
            elif d > 6.2:
                a.px(x0 + i, y0 + j, iron if int((ang + math.pi) * 8 / math.pi) % 2 == 0 else mul(iron, 1.5))
            elif d > 4.5:
                a.px(x0 + i, y0 + j, WOOD if int((ang + math.pi) * 4 / math.pi) % 2 == 0 else WOOD_D)
            elif d < 1.9:
                a.px(x0 + i, y0 + j, hub if d > 0.9 else GOLD_D)
            else:
                spoke = min(abs(math.sin(ang * 4.0)), 1.0) < 0.34
                a.px(x0 + i, y0 + j, WOOD_L if spoke else WOOD_DD)
    return a.region(x0, y0, 16, 16)


def band(a, x, y, w, h, c=STEEL_DD):
    """Железная скоба: тёмная полоса с заклёпками."""
    a.rect(x, y, w, h, c)
    a.rect(x, y, w, 1, mul(c, 1.5))
    for i in range(x + 1, x + w, 3):
        a.px(i, y + h // 2, STEEL_L if h > 2 else mul(c, 1.8))


def shield(a, x, y, w, h, field, charge, edge=GOLD):
    """Гербовый щит с прозрачным вырезом: сверху прямо, книзу сужается в острие; золотая кайма."""
    for j in range(h):
        k = 1.0 if j < h * 0.55 else max(0.0, 1.0 - (j - h * 0.55) / (h * 0.45)) ** 0.75
        half = (w / 2.0) * k
        for i in range(w):
            dx = abs(i - (w - 1) / 2.0)
            if dx <= half:
                c = field
                if dx > half - 1.1 or j == 0:
                    c = edge
                a.px(x + i, y + j, c)
            else:
                a.clear(x + i, y + j)
    # Фигура: крест (по умолчанию золотой) по центру.
    cx = x + w // 2
    a.rect(cx - 1, y + 2, 2, int(h * 0.6), charge)
    a.rect(x + w // 4, y + h // 3, w // 2, 2, charge)


# --- Баллиста ------------------------------------------------------------------------------------

def castle_cannon():
    """Баллиста: дубовое ложе, дуга-лук с тетивой, стальной болт с гербовым щитком, ворот с
    храповиком, колёса со спицами. Ствол (направляющая с болтом) смотрит в −Z, как у пушки."""
    a = Atlas(64, 32, 121)
    # Ложе: дубовые доски с железными скобами.
    wood(a, 0, 0, 32, 16, WOOD)
    band(a, 4, 0, 3, 16), band(a, 24, 0, 3, 16)
    a.rect(0, 0, 32, 1, WOOD_L)
    a.shade(0, 0, 32, 16, 1.05, 0.85, 0.8)
    stock = a.region(0, 0, 32, 16)
    # Остриё болта: сталь с тёмным остриём.
    a.rect(32, 0, 8, 8, STEEL_DD)
    a.rect(33, 1, 6, 6, STEEL)
    a.rect(35, 2, 2, 4, STEEL_L)
    tip = a.region(32, 0, 8, 8)
    # Станина: тёмное дерево, красная полоса дома, скобы.
    wood(a, 0, 16, 32, 12, WOOD_D)
    a.rect(0, 20, 32, 2, RED)
    a.rect(0, 22, 32, 1, RED_D)
    for x in range(3, 32, 8):
        a.px(x, 18, GOLD), a.px(x + 4, 25, GOLD)
    a.shade(0, 16, 32, 12, 1.05, 0.8, 0.85)
    frame = a.region(0, 16, 32, 12)
    disc = paint_wheel(a, 40, 0)
    wood(a, 56, 0, 8, 4, WOOD_D)
    a.rect(56, 0, 8, 1, STEEL_DD)
    rim = a.region(56, 0, 8, 4)
    # Болт: стальной стержень и оперение.
    a.rect(32, 16, 16, 8, STEEL)
    a.rect(32, 16, 16, 1, STEEL_L), a.rect(32, 21, 16, 1, STEEL_D)
    for x in range(33, 48, 5):
        a.rect(x, 18, 1, 3, STEEL_DD)
    shaft = a.region(32, 16, 16, 8)
    # Дуга: дерево с железной обмоткой и красной лентой.
    wood(a, 48, 16, 16, 8, WOOD_D)
    for x in (50, 57):
        band(a, x, 16, 2, 8)
    a.rect(48, 19, 16, 1, RED)
    limb = a.region(48, 16, 16, 8)
    # Щиток: красно-золотой, с золотым крестом, стороной к стрелку.
    a.rect(48, 24, 16, 8, RED)
    a.rect(48, 24, 16, 1, GOLD), a.rect(48, 31, 16, 1, GOLD_D)
    a.rect(55, 25, 2, 6, GOLD), a.rect(51, 27, 10, 2, GOLD)
    plate = a.region(48, 24, 16, 8)
    m = Model("cannon", a)
    side = lambda x: at(rot(loft([(-0.04, 0.24, 0.24), (0.04, 0.24, 0.24)], rim, 8, caps=(disc, disc), flat=True), rz=90.0),
                        x, 0.24, 0.2)
    limbs = []
    for s in (-1.0, 1.0):
        limbs += at(rot(box((0.56, 0.07, 0.09), limb, limb, limb), ry=-12.0 * s), s * 0.29, 0.68, -0.46)
    # Тетива: две тонкие ленты от концов дуги к ложу.
    string = []
    for dy in (0.0, 0.025):
        string += quad((-0.57, 0.7 + dy, -0.35), (-0.57, 0.725 + dy, -0.35), (0.0, 0.725 + dy, -0.12), (0.0, 0.7 + dy, -0.12), shaft)
        string += quad((0.57, 0.7 + dy, -0.35), (0.57, 0.725 + dy, -0.35), (0.0, 0.725 + dy, -0.12), (0.0, 0.7 + dy, -0.12), shaft)
    bolt = at(rot(loft([(-0.5, 0.018, 0.018), (0.34, 0.018, 0.018), (0.4, 0.032, 0.032), (0.58, 0.004, 0.004)], shaft, 5,
                       caps=(None, tip)), rx=-90.0), 0.0, 0.73, -0.04)
    return m.part("body", (0.0, 0.0, 0.0),
                  at(box((0.14, 0.12, 1.05), stock, stock, stock), 0.0, 0.62, -0.02)
                  + at(box((0.34, 0.1, 0.8), frame, frame, frame, (0.8, 1.0)), 0.0, 0.34, 0.1)
                  + at(box((0.12, 0.26, 0.12), frame, frame, None, (0.8, 0.8)), 0.0, 0.47, -0.05)
                  + at(rot(loft([(-0.1, 0.06, 0.06), (0.1, 0.06, 0.06)], frame, 6, caps=(plate, plate), flat=True), rz=90.0), 0.0, 0.72, 0.42)
                  + limbs + string + bolt
                  + at(box((0.34, 0.26, 0.03), plate, plate, plate), 0.0, 0.8, -0.22)
                  + side(-0.28) + side(0.28))


# --- Дуб -----------------------------------------------------------------------------------------

def castle_palm():
    """Дуб: толстый кривой ствол с корневыми лапами, вилкой у макушки и девятью дольками кроны,
    расходящимися от макушки. Долька это плоскость с вырезом по прозрачности, лист дуба с
    волнистой кромкой: `ThreedScreen.add_palm` кладёт на свои ленты ту же правую половину атласа."""
    a = Atlas(32, 32, 147)
    # Кора: вертикальные борозды, светлые гребни, сучки и пятна мха.
    a.rect(0, 0, 16, 32, BARK)
    for x in range(0, 16, 3):
        h0 = (x * 5) % 7
        for y in range(32):
            a.px(x, y, BARK_D if (y + h0) % 9 else BARK)
            a.px(x + 1, y, BARK_L if (y * 3 + x) % 8 == 0 else BARK)
    for k in range(3):
        a.rect(2 + k * 5, 6 + k * 9, 2, 3, BARK_D)
    for _ in range(14):
        a.px(a.rng.randrange(16), a.rng.randrange(32), MOSS)
    a.shade(0, 0, 16, 32, 0.95, 1.0, 0.7)
    a.noise(0, 0, 16, 32, 0.07)
    trunk = a.region(0, 0, 16, 32)
    # Долька кроны: листовая гроздь с волнистой кромкой, жилкой и светлыми бликами.
    for y in range(32):
        base = 1.0 + 6.8 * math.sin(math.pi * min(y / 30.0, 1.0)) ** 0.6
        half = int(base + 0.9 * math.sin(y * 1.3))
        for x in range(16):
            dx = abs(x - 7.5)
            if dx <= half:
                c = LEAF
                if dx < 0.9:
                    c = LEAF_D
                elif dx > half - 1.3:
                    c = LEAF_D
                elif (x * 5 + y * 3) % 9 == 0:
                    c = LEAF_L
                elif (x + y * 2) % 6 == 0:
                    c = mul(LEAF, 0.85)
                a.px(16 + x, y, c)
    for y in range(4, 30, 5):
        for k in range(1, 4):
            a.px(16 + 8 + k, y + k // 2, LEAF_D), a.px(16 + 7 - k, y + k // 2, LEAF_D)
    a.noise(16, 0, 16, 32, 0.06)
    leaf = a.region(16, 0, 16, 32)
    top = (0.5, 4.0, 0.1)
    # Ствол: корневой раструб, изгиб вправо и вилка у макушки.
    tris = loft([(0.0, 0.46, 0.46), (0.22, 0.3, 0.3), (0.7, 0.24, 0.24, 0.02, 0.0), (1.8, 0.21, 0.21, 0.12, 0.02),
                 (3.0, 0.19, 0.19, 0.35, 0.06), (4.0, 0.2, 0.2, 0.5, 0.1)], trunk, 6)
    # Корневые лапы: три клина, лежащие на земле.
    for k in range(3):
        ang = 2.0 * math.pi * k / 3.0 + 0.5
        d = (math.sin(ang), math.cos(ang))
        q = (d[1], -d[0])
        tris += quad((d[0] * 0.2 + q[0] * 0.09, 0.5, d[1] * 0.2 + q[1] * 0.09), (d[0] * 0.2 - q[0] * 0.09, 0.5, d[1] * 0.2 - q[1] * 0.09),
                     (d[0] * 0.7 - q[0] * 0.14, 0.0, d[1] * 0.7 - q[1] * 0.14), (d[0] * 0.7 + q[0] * 0.14, 0.0, d[1] * 0.7 + q[1] * 0.14),
                     (trunk[0], trunk[1], trunk[0] + (trunk[2] - trunk[0]) * 0.5, trunk[3]))
    # Две ветви-вилки наклонно вверх, из них растёт крона.
    tris += at(rot(loft([(0.0, 0.1, 0.1), (0.9, 0.07, 0.07)], trunk, 4), rz=-35.0), 0.38, 3.3, 0.06)
    tris += at(rot(loft([(0.0, 0.1, 0.1), (0.8, 0.07, 0.07)], trunk, 4), rz=40.0), 0.42, 3.4, 0.1)
    for k in range(9):
        ang = 2.0 * math.pi * k / 9.0 + 0.3
        d = (math.sin(ang), 0.0, math.cos(ang))
        q = (math.cos(ang) * 1.05, 0.0, -math.sin(ang) * 1.05)
        droop = 0.35 + 0.12 * (k % 2)
        far = (top[0] + d[0] * 1.5, top[1] - droop + 0.3, top[2] + d[2] * 1.5)
        mid = (top[0] - d[0] * 0.2, top[1] + 0.62, top[2] - d[2] * 0.2)
        tris += quad((mid[0] - q[0] * 0.5, mid[1], mid[2] - q[2] * 0.5), (mid[0] + q[0] * 0.5, mid[1], mid[2] + q[2] * 0.5),
                     (far[0] + q[0], far[1], far[2] + q[2]), (far[0] - q[0], far[1], far[2] - q[2]), leaf)
    # Верхний ярус: пять коротких долек стоймя, чтобы крона была плотной сверху.
    for k in range(5):
        ang = 2.0 * math.pi * k / 5.0 + 0.9
        d = (math.sin(ang), 0.0, math.cos(ang))
        q = (math.cos(ang) * 0.8, 0.0, -math.sin(ang) * 0.8)
        far = (top[0] + d[0] * 0.8, top[1] + 0.35, top[2] + d[2] * 0.8)
        base = (top[0] - d[0] * 0.1, top[1] - 0.15, top[2] - d[2] * 0.1)
        tris += quad((far[0] - q[0] * 0.3, far[1] + 0.5, far[2] - q[2] * 0.3), (far[0] + q[0] * 0.3, far[1] + 0.5, far[2] + q[2] * 0.3),
                     (base[0] + q[0], base[1], base[2] + q[2]), (base[0] - q[0], base[1], base[2] - q[2]), leaf)
    return Model("palm", a).part("body", (0.0, 0.0, 0.0), tris)


# --- Знамя ---------------------------------------------------------------------------------------

def castle_flag():
    """Знамя с гербом на древке с золотым наконечником; полотнище отдельной частью у древка.
    Красное поле, золотой щит с короной, ласточкин хвост по нижней кромке (прозрачный вырез)."""
    a = Atlas(64, 32, 119)
    a.rect(0, 0, 32, 20, RED)
    for y in range(0, 20, 5):
        a.rect(0, y, 32, 1, mul(RED, 0.86))
    # Золотая кайма и герб: щит с белым крестом под золотой короной.
    a.rect(0, 0, 32, 1, GOLD), a.rect(0, 19, 32, 1, GOLD_D)
    a.rect(0, 0, 1, 20, GOLD), a.rect(31, 0, 1, 20, GOLD_D)
    for j in range(5, 17):
        k = 1.0 if j < 12 else max(0.0, 1.0 - (j - 12) / 6.0) ** 0.8
        half = 5.5 * k
        for i in range(32):
            dx = abs(i - 15.5)
            if dx <= half:
                a.px(i, j, GOLD if dx > half - 1.0 or j == 5 else WHITE)
    a.rect(15, 6, 2, 8, RED), a.rect(12, 8, 8, 2, RED)
    # Корона над щитом: три зубца и ободок.
    a.rect(11, 3, 10, 2, GOLD)
    for x in (11, 15, 20):
        a.rect(x, 1, 1, 2, GOLD_L)
    a.px(16, 0, GOLD_L)
    # Ласточкин хвост: вырез треугольником у свободного края.
    for j in range(20):
        w = max(0, 7 - abs(j - 9.5) * 0.74)
        for i in range(int(w)):
            a.clear(31 - i, j)
    a.noise(0, 0, 32, 20, 0.07)
    cloth = a.region(0, 0, 32, 20)
    # Древко: дерево с золотыми кольцами и красной полосой.
    a.rect(32, 0, 8, 32, WOOD)
    for y in range(0, 32, 4):
        a.rect(32, y, 8, 1, WOOD_D)
    for y in (0, 14, 28):
        a.rect(32, y, 8, 2, GOLD)
    a.rect(32, 20, 8, 3, RED)
    a.shade(32, 0, 8, 32, 1.0, 0.9, 0.6)
    pole = a.region(32, 0, 8, 32)
    stone(a, 40, 0, 8, 8, STONE_D, 4, 4)
    base = a.region(40, 0, 8, 8)
    a.rect(48, 0, 8, 8, GOLD)
    a.rect(50, 1, 4, 5, GOLD_L)
    a.rect(48, 7, 8, 1, GOLD_D)
    tipc = a.region(48, 0, 8, 8)
    m = Model("flag", a)
    m.part("pole", (0.0, 0.0, 0.0),
           loft([(0.0, 0.05, 0.05), (2.7, 0.04, 0.04)], pole, 4, caps=(None, base))
           + loft([(0.0, 0.26, 0.26), (0.14, 0.18, 0.18)], base, 5, caps=(None, base), flat=True)
           # Наконечник-копьё: шар и ромб остриём вверх.
           + loft([(2.68, 0.06, 0.06), (2.74, 0.075, 0.075), (2.8, 0.06, 0.06)], tipc, 5)
           + loft([(2.8, 0.06, 0.06), (2.9, 0.055, 0.02), (3.04, 0.01, 0.005)], tipc, 4))
    m.part("cloth", (0.04, 2.3, 0.0),
           quad((0.04, 2.62, 0.0), (1.0, 2.56, 0.0), (1.0, 2.02, 0.0), (0.04, 1.98, 0.0), cloth), "pole")
    return m


# --- Сторожевая башня ----------------------------------------------------------------------------

def castle_lighthouse():
    """Сторожевая башня: ориентир на горизонте высотой с маяк. Каменный ствол с бойницами и
    дверью, четыре контрфорса, выступающая галерея с зубцами, красная конусная кровля и
    вымпел на шпиле."""
    a = Atlas(64, 64, 153)
    # Ствол: кладка, бойницы, дверь с аркой, факельное окно, пояс над основанием.
    stone(a, 0, 0, 64, 40, STONE, 8, 5)
    for wx, wy in ((6, 10), (22, 22), (46, 8), (54, 24)):
        a.rect(wx, wy, 2, 6, BLACK)
        a.rect(wx - 1, wy - 1, 4, 1, STONE_L)
    a.rect(27, 26, 10, 14, RAV_D)
    a.rect(28, 25, 8, 1, STONE_D)
    a.rect(26, 25, 1, 15, STONE_L), a.rect(37, 25, 1, 15, STONE_L)
    for x in (29, 32, 35):
        a.rect(x, 27, 1, 13, WOOD_D)
    a.rect(28, 33, 8, 1, STEEL_DD)
    a.px(34, 34, GOLD)
    a.rect(14, 13, 4, 4, BLACK), a.rect(15, 14, 2, 2, GOLD_L)
    a.rect(0, 36, 64, 4, STONE_D)
    for x in range(0, 64, 4):
        a.px(x, 37, STONE_L)
    a.shade(0, 0, 64, 40, 1.08, 0.85, 0.7)
    a.noise(0, 0, 64, 40, 0.05)
    hull = a.region(0, 0, 64, 40)
    # Кровля: красная черепица рядами, золотой поясок.
    a.rect(0, 40, 32, 8, RED)
    for y in range(40, 48, 2):
        a.rect(0, y, 32, 1, RED_D)
        for x in range((y // 2) % 2 * 2, 32, 4):
            a.px(x, y + 1, RED_L)
    a.rect(0, 46, 32, 2, RED_D)
    a.shade(0, 40, 32, 8, 1.2, 0.85, 0.8)
    cone = a.region(0, 40, 32, 8)
    # Цоколь: крупные камни.
    stone(a, 32, 40, 16, 8, STONE_D, 8, 4)
    table = a.region(32, 40, 16, 8)
    # Галерея: консоли-кронштейны под зубцами.
    a.rect(48, 40, 8, 8, STONE_D)
    for x in range(48, 56, 4):
        a.rect(x, 40, 2, 5, STONE_L)
        a.rect(x + 2, 44, 2, 4, BLACK)
    a.noise(48, 40, 8, 8, 0.1)
    dark = a.region(48, 40, 8, 8)
    # Контрфорс: светлый камень со швами.
    stone(a, 0, 48, 16, 16, STONE_L, 8, 4, STONE)
    fin = a.region(0, 48, 16, 16)
    # Зубец и вымпел.
    stone(a, 16, 48, 8, 8, STONE, 4, 4)
    crenel = a.region(16, 48, 8, 8)
    a.rect(24, 48, 8, 16, RED)
    a.rect(24, 48, 8, 1, GOLD)
    a.rect(24, 63, 8, 1, GOLD_D)
    for j in range(48, 64):
        a.clear(31, j) if (j - 56) % 2 and abs(j - 56) > 5 else None
    pennon = a.region(24, 48, 8, 16)
    tris = (loft([(0.0, 1.5, 1.5), (0.7, 1.4, 1.4)], table, 8, caps=(None, dark), flat=True)
            + loft([(0.7, 1.3, 1.3), (1.3, 1.12, 1.12)], table, 8)
            + loft([(1.3, 1.08, 1.08), (3.6, 1.02, 1.02), (6.4, 0.95, 0.95)], hull, 8)
            # Галерея: расширяется кронштейнами и обрывается ровным полом.
            + loft([(6.4, 0.95, 0.95), (6.5, 1.25, 1.25), (6.95, 1.28, 1.28)], dark, 8, caps=(None, dark), flat=True)
            # Кровля: свес над зубцами, дальше конус.
            + loft([(7.4, 1.4, 1.4), (7.55, 1.1, 1.1), (8.2, 0.7, 0.7), (8.7, 0.34, 0.34), (9.0, 0.04, 0.04)], cone, 8,
                   caps=(dark, None)))
    for k in range(8):
        ang = 2.0 * math.pi * k / 8.0
        tris += at(rot(box((0.42, 0.45, 0.2), crenel, crenel, None), ry=math.degrees(ang)),
                   math.sin(ang) * 1.14, 7.2, math.cos(ang) * 1.14)
    # Контрфорсы: клин от стены к земле, три грани.
    for k in range(4):
        ang = math.pi / 4.0 + math.pi / 2.0 * k
        d = (math.sin(ang), math.cos(ang))
        q = (d[1], -d[0])
        t = lambda r, y, w: (d[0] * r + q[0] * w, y, d[1] * r + q[1] * w)
        tris += quad(t(1.0, 3.2, -0.12), t(1.0, 3.2, 0.12), t(1.8, 0.7, 0.26), t(1.8, 0.7, -0.26), fin)
        tris += quad(t(1.0, 3.2, 0.12), t(1.0, 3.2, 0.12), t(1.8, 0.7, 0.26), t(1.1, 1.0, 0.12), fin)
        tris += quad(t(1.0, 3.2, -0.12), t(1.0, 3.2, -0.12), t(1.8, 0.7, -0.26), t(1.1, 1.0, -0.12), fin)
    # Шпиль и вымпел.
    tris += loft([(8.98, 0.025, 0.025), (9.5, 0.02, 0.02)], hull, 3)
    tris += quad((0.02, 9.46, 0.0), (0.72, 9.3, 0.04), (0.72, 9.12, 0.04), (0.02, 9.0, 0.0), pennon)
    # Вырожденные грани клиньев (боковые треугольники из четырёхугольников) не нужны.
    tris = [t for t in tris if len({tuple(v) for v in t[0]}) == 3]
    return Model("lighthouse", a).part("body", (0.0, 0.0, 0.0), tris)


# --- Повозки -------------------------------------------------------------------------------------

def make_cart(name, rival):
    """Транспорт гонок. Герой: боевая повозка, дубовый борт с красно-золотой полосой, гербовые
    щиты по бортам, на шесте вымпел там, где у пиратской повозки парус. Соперник: повозка чужого
    герба, чёрная с багровым, с таранным шипом и багровым вымпелом; на осях колёса с чёрным
    ободом. Части и точки вращения как у пиратской повозки: `body`, `axle_f`, `axle_r`."""
    a = Atlas(64, 64, 171 if not rival else 173)
    field, field_d, trim, hi = (RAV, RAV_D, CRIM, CRIM_L) if rival else (WOOD, WOOD_D, RED, RED_L)
    mark = CRIM_L if rival else GOLD
    # Борт: доски, цветная полоса с зубчиком, скобы.
    wood(a, 0, 0, 64, 12, field if not rival else RAV)
    a.rect(0, 2, 64, 2 if rival else 3, trim)
    a.rect(0, 2, 64, 1, hi)
    for x in range(0, 64, 4):
        a.px(x, 4, mark)
    for x in range(0, 64, 16):
        band(a, x, 5, 2, 7, STEEL_DD if not rival else BLACK)
    if rival:
        # Чёрный борт с багровым шевроном и костяным знаком.
        for x in range(0, 64, 8):
            a.rect(x, 7, 4, 1, CRIM_D), a.rect(x + 2, 8, 4, 1, CRIM_D), a.rect(x + 4, 9, 4, 1, CRIM_D)
    a.rect(0, 11, 64, 1, mul(field, 0.5))
    a.shade(0, 0, 64, 12, 1.08, 0.8, 1.0)
    a.noise(0, 0, 64, 12, 0.04)
    hull = a.region(0, 0, 64, 12)
    # Настил: доски вдоль, сундучок-ящик со скобой.
    wood(a, 0, 12, 16, 16, WOOD_D if not rival else RAV_D, vertical=True)
    band(a, 0, 20, 16, 3, STEEL_DD)
    a.px(7, 21, GOLD if not rival else CRIM_L), a.px(8, 21, GOLD if not rival else CRIM_L)
    deck = a.region(0, 12, 16, 16)
    wheel = paint_wheel(a, 16, 12, BLACK if rival else STEEL_DD, CRIM_L if rival else GOLD)
    wood(a, 32, 12, 8, 4, WOOD_DD)
    a.rect(32, 12, 8, 1, STEEL_DD)
    rim = a.region(32, 12, 8, 4)
    # Шест: тёмное дерево с железными кольцами.
    a.rect(40, 12, 8, 16, WOOD_D if not rival else RAV_D)
    for y in range(12, 28, 4):
        a.rect(40, y, 8, 1, STEEL_DD if not rival else BLACK)
    for y in (13, 25):
        a.rect(40, y, 8, 1, mark)
    mast = a.region(40, 12, 8, 16)
    # Гербовый щит борта: тот же рисунок под вырез.
    a.rect(48, 12, 16, 16, (0, 0, 0), 0)
    shield(a, 51, 12, 10, 14, trim if not rival else RAV_D, mark if not rival else CRIM_L, GOLD if not rival else STEEL)
    badge = a.region(51, 12, 10, 14)
    # Вымпел: длинный треугольник с ласточкиным хвостом и каймой.
    sail_field, sail_edge = (CRIM, GOLD) if rival else (RED, GOLD)
    for j in range(28):
        half = 13.0 * (1.0 - 0.0)
        for i in range(32):
            top_edge = 14 - 13.0 * (1.0 - i / 31.0) ** 0.9 - 0.0
            bottom_edge = 14 + 13.0 * (1.0 - i / 31.0) ** 0.9
            ty = 32 + j
            yy = j + 0.5
            if top_edge <= yy <= bottom_edge and not (i > 24 and abs(yy - 14) < (i - 24) * 1.5):
                c = sail_field
                if yy - top_edge < 1.5 or bottom_edge - yy < 1.5 or i == 0:
                    c = sail_edge
                elif rival and (i + j) % 11 == 0:
                    c = CRIM_D
                a.px(i, ty, c)
    if rival:
        # Чёрный шеврон и костяной зуб на багровом поле.
        for k in range(6):
            a.rect(4 + k * 2, 36 + k, 3, 2, BLACK), a.rect(4 + k * 2, 53 - k, 3, 2, BLACK)
        a.rect(15, 41, 4, 12, BLACK), a.rect(16, 43, 2, 8, rgb("D8D2BC"))
    else:
        a.rect(5, 45, 8, 2, GOLD), a.rect(8, 41, 2, 10, GOLD)
    a.noise(0, 32, 32, 28, 0.05)
    sail = a.region(0, 32, 32, 28)
    m = Model(name, a)
    spike = []
    if rival:
        # Корпус чужой повозки: низкий чёрный борт, высокий щит спереди и таран-шип.
        body = (at(box((1.0, 0.3, 2.0), hull, deck, deck, (1.1, 1.0)), 0.0, 0.58)
                + at(box((0.08, 0.38, 1.7), hull, hull, hull), -0.5, 0.88, 0.05)
                + at(box((0.08, 0.38, 1.7), hull, hull, hull), 0.5, 0.88, 0.05)
                + at(box((1.0, 0.5, 0.08), hull, deck, deck), 0.0, 0.98, -0.94)
                + at(box((1.0, 0.3, 0.08), hull, deck, deck), 0.0, 0.88, 0.96)
                + at(box((0.7, 0.1, 0.3), deck, deck, deck), 0.0, 0.82, 0.45)
                + at(rot(loft([(0.0, 0.16, 0.16), (0.12, 0.12, 0.12), (0.5, 0.0, 0.0)], mast, 5), rx=-90.0), 0.0, 0.68, -1.0))
    else:
        # Корпус боевой повозки: настил, борта-доски, передний щиток, сиденье возницы.
        body = (at(box((1.0, 0.26, 2.0), hull, deck, deck, (1.08, 1.0)), 0.0, 0.58)
                + at(box((0.07, 0.3, 1.9), hull, hull, hull), -0.5, 0.85, 0.0)
                + at(box((0.07, 0.3, 1.9), hull, hull, hull), 0.5, 0.85, 0.0)
                + at(box((1.0, 0.42, 0.07), hull, deck, deck), 0.0, 0.92, -0.97)
                + at(box((0.8, 0.1, 0.34), deck, deck, deck), 0.0, 0.84, 0.55)
                + at(box((0.8, 0.28, 0.06), hull, deck, deck), 0.0, 1.0, 0.76))
    # Гербовые щиты вдоль бортов.
    for x in (-0.54, 0.54):
        for z in (-0.5, 0.1, 0.7):
            body += quad((x, 1.12, z - 0.18), (x, 1.12, z + 0.18), (x, 0.7, z + 0.18), (x, 0.7, z - 0.18), badge)
    body += (at(loft([(0.0, 0.05, 0.05), (2.0, 0.035, 0.035)], mast, 4), 0.0, 0.76, -0.25)
             + at(box((0.12, 0.1, 0.12), mast, mast, mast), 0.0, 2.8, -0.25)
             # Вымпел летит вправо и назад: виден и сзади, и сбоку.
             + quad((0.03, 2.66, -0.25), (1.0, 2.5, 0.1), (1.0, 2.1, 0.1), (0.03, 1.94, -0.25), sail))
    m.part("body", (0.0, 0.0, 0.0), body)
    for part, z in (("axle_f", -0.72), ("axle_r", 0.72)):
        tris = []
        for x in (-0.6, 0.6):
            tris += at(rot(loft([(-0.07, 0.32, 0.32), (0.07, 0.32, 0.32)], rim, 8, caps=(wheel, wheel), flat=True), rz=90.0),
                       x, 0.32, z)
        m.part(part, (0.0, 0.32, z), tris, "body")
    return m


def castle_cart():
    return make_cart("cart", False)


def castle_cart_rival():
    return make_cart("cart_rival", True)


# --- Арбалет -------------------------------------------------------------------------------------

def castle_pistol():
    """Арбалет в латной перчатке: оружие вида от первого лица, болт смотрит в −Z, ноль в
    рукоятке. Дубовое ложе, стальная дуга с тетивой, болт на жёлобе, стремя спереди; рука в
    стальной перчатке, рукав красной туники с кольчужной манжетой."""
    a = Atlas(32, 32, 175)
    # Ложе: дерево с золотой инкрустацией.
    wood(a, 0, 0, 16, 8, WOOD)
    a.rect(0, 0, 16, 1, WOOD_L), a.rect(0, 7, 16, 1, WOOD_D)
    for x in (4, 11):
        a.px(x, 3, GOLD)
    a.rect(0, 5, 16, 1, GOLD_D)
    stock = a.region(0, 0, 16, 8)
    # Остриё болта.
    a.rect(16, 0, 4, 4, STEEL_DD)
    a.rect(17, 1, 2, 2, STEEL_L)
    tip = a.region(16, 0, 4, 4)
    # Дуга и скобы: воронёная сталь с бликом и заклёпками.
    a.rect(0, 8, 16, 8, STEEL_D)
    a.rect(0, 8, 16, 1, STEEL_L)
    a.rect(0, 15, 16, 1, STEEL_DD)
    for x in range(1, 16, 3):
        a.px(x, 11, STEEL_L), a.px(x, 12, STEEL_DD)
    a.noise(0, 8, 16, 8, 0.06)
    prod = a.region(0, 8, 16, 8)
    # Перчатка: стальные пластины с суставами.
    a.rect(0, 16, 16, 8, STEEL)
    a.rect(0, 19, 16, 1, STEEL_D)
    for x in (3, 7, 11):
        a.rect(x, 16, 1, 3, STEEL_D)
        a.px(x + 1, 17, STEEL_L)
    a.shade(0, 16, 16, 8, 1.05, 0.85, 0.8)
    a.noise(0, 16, 16, 8, 0.05)
    hand = a.region(0, 16, 16, 8)
    # Рукав: красная туника, кольчужная манжета у кисти, золотая нашивка.
    a.rect(16, 8, 16, 16, RED)
    for y in range(10, 24, 3):
        a.rect(16, y, 16, 1, RED_D)
    for j in range(8, 11):
        for i in range(16):
            a.px(16 + i, j, STEEL_D if (i + j) % 2 == 0 else STEEL_DD)
    a.rect(22, 15, 5, 3, GOLD)
    a.rect(23, 16, 3, 1, GOLD_D)
    a.shade(16, 8, 16, 16, 1.0, 0.85, 0.75)
    a.noise(16, 8, 16, 16, 0.05)
    sleeve = a.region(16, 8, 16, 16)
    # Тетива: тонкая полоса поперёк, светлая.
    a.rect(16, 4, 12, 2, WOOD_L)
    string = a.region(16, 4, 12, 2)
    limbs = []
    for s in (-1.0, 1.0):
        limbs += at(rot(box((0.15, 0.025, 0.04), prod, prod, prod), ry=-18.0 * s), s * 0.075, 0.068, -0.31)
    stirrup = (at(box((0.01, 0.07, 0.01), prod, prod, prod), -0.02, 0.07, -0.4)
               + at(box((0.01, 0.07, 0.01), prod, prod, prod), 0.02, 0.07, -0.4)
               + at(box((0.05, 0.01, 0.01), prod, prod, prod), 0.0, 0.035, -0.4))
    return Model("pistol", a).part("body", (0.0, 0.0, 0.0),
                                   # Болт в жёлобе: остриё смотрит в −Z.
                                   at(rot(loft([(-0.17, 0.011, 0.011), (0.1, 0.011, 0.011), (0.14, 0.022, 0.022), (0.2, 0.003, 0.003)],
                                                prod, 5, caps=(None, tip)), rx=-90.0), 0.0, 0.082, -0.2)
                                   + at(box((0.05, 0.05, 0.3), stock, stock, stock), 0.0, 0.03, -0.17)
                                   + at(rot(box((0.045, 0.15, 0.06), stock, stock, stock), rx=-20.0), 0.0, -0.05, 0.03)
                                   + limbs + stirrup
                                   + quad((-0.19, 0.07, -0.34), (-0.19, 0.075, -0.34), (0.0, 0.085, -0.1), (0.0, 0.08, -0.1), string)
                                   + quad((0.19, 0.07, -0.34), (0.19, 0.075, -0.34), (0.0, 0.085, -0.1), (0.0, 0.08, -0.1), string)
                                   + at(box((0.085, 0.1, 0.1), hand, hand, hand), 0.0, -0.04, 0.03)
                                   + at(rot(loft([(0.0, 0.045, 0.045), (0.5, 0.06, 0.06)], sleeve, 4, math.pi / 4.0), rx=65.0), 0.0, -0.08, 0.07))


# --- Турнирное кольцо ----------------------------------------------------------------------------

def castle_hoop():
    """Турнирное кольцо: цель спорта. Щит это гербовая доска красно-белой шахматкой в золотой
    кайме с бляхой-мишенью, кольцо золотое, сетка из стальных цепных звеньев; стойка это
    красно-белое турнирное копьё. Кольцо и щит там же и тех же размеров, что у пиратов."""
    a = Atlas(64, 64, 177)
    # Доска: шахматка красного и белого, золотая кайма, бляха-мишень против кольца.
    for j in range(24):
        for i in range(32):
            a.px(i, j, RED if ((i // 4) + (j // 4)) % 2 == 0 else WHITE)
    for x, y, w, h in ((0, 0, 32, 1), (0, 23, 32, 1), (0, 0, 1, 24), (31, 0, 1, 24)):
        a.rect(x, y, w, h, GOLD)
    a.rect(1, 1, 30, 1, GOLD_D), a.rect(1, 22, 30, 1, GOLD_D)
    for j in range(24):
        for i in range(32):
            d = math.hypot(i - 15.5, j - 11.5)
            if d < 5.6:
                a.px(i, j, GOLD_D if d > 4.4 else (RED_D if d > 2.4 else GOLD_L))
    a.px(3, 3, GOLD_L), a.px(28, 3, GOLD_L)
    a.noise(0, 0, 32, 24, 0.04)
    board = a.region(0, 0, 32, 24)
    a.rect(32, 0, 16, 4, GOLD)
    a.rect(32, 0, 16, 1, GOLD_L), a.rect(32, 3, 16, 1, GOLD_D)
    ring = a.region(32, 0, 16, 4)
    # Цепная сетка: ромбы стальных звеньев, между ними прозрачно.
    for y in range(16):
        for x in range(32):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                a.px(32 + x, 8 + y, STEEL_L if (x + y) % 8 else STEEL)
    net = a.region(32, 8, 32, 16)
    # Стойка: турнирное копьё в красно-белую спираль, золотые кольца и держатель.
    for y in range(24, 56):
        for x in range(8):
            a.px(x, y, RED if ((x + y) // 4) % 2 == 0 else WHITE)
    for y in (24, 40, 54):
        a.rect(0, y, 8, 2, GOLD)
    a.shade(0, 24, 8, 32, 1.0, 0.9, 0.6)
    post = a.region(0, 24, 8, 32)
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
    edge = (u0, v0, u0 + (u1 - u0) / 16.0, v0 + (v1 - v0) / 8.0)
    for x in (-0.65, 0.65):
        faces += quad((x, 3.875, -0.15), (x, 3.875, -0.09), (x, 2.925, -0.09), (x, 2.925, -0.15), edge)
    for y in (2.925, 3.875):
        faces += quad((0.65, y, -0.15), (-0.65, y, -0.15), (-0.65, y, -0.09), (0.65, y, -0.09), edge)
    return Model("hoop", a).part("body", (0.0, 0.0, 0.0),
                                 loft([(0.0, 0.09, 0.09), (3.9, 0.07, 0.07)], post, 5)
                                 + loft([(0.0, 0.3, 0.3), (0.12, 0.2, 0.2)], post, 5, flat=True)
                                 + at(box((0.06, 0.06, 0.2), ring, ring, ring), 0.0, rim_y, -0.2)
                                 + faces + ring_tris + basket + flip(basket))


MODELS = [castle_cannon, castle_palm, castle_flag, castle_lighthouse, castle_cart, castle_cart_rival, castle_pistol, castle_hoop]


if __name__ == "__main__":
    models = [f() for f in MODELS]
    for m in models:
        print("%-11s частей %d, треугольников %3d%s" % (m.name, len(m.parts), m.tris(),
                                                        "  БОЛЬШЕ %d" % lm.MAX_TRIS if m.tris() > lm.MAX_TRIS else ""))
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
