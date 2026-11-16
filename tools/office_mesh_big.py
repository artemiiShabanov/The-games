#!/usr/bin/env python3
"""Крупный реквизит и транспорт «Офиса» для low poly и «продвинутых» (#137): зеркала моделей
космоса из `space_mesh_big.py` (а те зеркала пиратских из `lowpoly_meshes.py`) с теми же именами
слотов, частей и точками вращения, тем же нулём и габаритами, чтобы десять 3D-демок работали
без правок. Цвета из основы 16/32 (`office16.PALETTE`) через `office_mesh_chars`.

  cannon      копир, стреляющий бумагой: тумба на роликах, сканер вытянут вперёд соплом
              (выход бумаги в −Z, как ствол пушки), из щели торчит лист
  palm        фикус в горшке; атлас: слева ствол (внизу земля и горшок), справа лист
              (эти же половины берёт `ThreedScreen.add_palm`)
  flag        флажок «пятница» на стойке с кнопкой-навершием: части `pole` и `cloth`
  lighthouse  серверная стойка с мигалкой на фальшполе, высота маяка
  cart        почтовая тележка на колёсиках: `body`, оси `axle_f`, `axle_r`; тележка без мачты
              и паруса: короб с письмами, посылки, мешок, ручка сзади, флажок ящика ниже 0.3 м
  cart_rival  офисное кресло начальника на колёсах: те же части и точки вращения; сиденье,
              спинка с подголовником, подлокотники, подножка
  pistol      степлер в руке клерка (манжета рубашки, часы), вид от первого лица
  hoop        мусорная корзина из сетки под маркерной доской; кольцо там же и того же размера

    python3 tools/office_mesh_big.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from lowpoly_meshes import Atlas, Model, at, box, flip, loft, mul, quad, rgb, rot  # noqa: E402
from office_mesh_chars import (AQUA, BRASS, COFFEE, DARK, DARK_D, DARK_L, GOLD, GOLD_L, GREY, GREY_D, K,  # noqa: E402
                               METAL, METAL_L, NAVY, RED, RED_D, SEA, SEA_L, SKIN, SKIN_L, SKY, TAN, WHITE)

# Зелень в горшках и ковролин из той же палитры, картон и скотч посылок.
GREEN, GREEN_D, GREEN_L = rgb("4F9C86"), rgb("2A605C"), rgb("7CC4A8")
CARD, CARD_D, TAPE = rgb("C99A5A"), rgb("9A6E3A"), rgb("E6CF9E")
LED = rgb("7CF29A")


def plastic(a, x, y, w, h, base, step=6):
    """Корпус техники: гладкий пластик со швами панелей и светлой кромкой под швом."""
    a.rect(x, y, w, h, base)
    for j in range(step - 1, h, step):
        a.rect(x, y + j, w, 1, mul(base, 0.7))
        if j + 1 < h:
            a.rect(x, y + j + 1, w, 1, mul(base, 1.08))
    a.noise(x, y, w, h, 0.04)


def slats(a, x, y, w, h, base):
    """Жалюзи вентиляции: тёмные щели через строку."""
    for j in range(h):
        a.rect(x, y + j, w, 1, mul(base, 0.5) if j % 2 == 0 else mul(base, 1.1))


def hazard(a, x, y, w, h, c0=GOLD, c1=K):
    """Полосы опасности наискось."""
    for j in range(h):
        for i in range(w):
            a.px(x + i, y + j, c0 if ((i + j) // 3) % 2 == 0 else c1)


def paper(a, x, y, w, h, chart=False):
    """Лист бумаги: строчки текста, загнутая тень по краю, по желанию график."""
    a.rect(x, y, w, h, WHITE)
    for j in range(2, h - 1, 2):
        a.rect(x + 2, y + j, w - 4 - (j * 3) % 4, 1, GREY)
    if chart and w >= 12 and h >= 12:
        a.rect(x + 2, y + h - 7, w - 4, 5, WHITE)
        for i, v in enumerate((1, 2, 2, 4, 3, 5)):
            a.rect(x + 3 + i * 2, y + h - 2 - v, 1, v, AQUA if i % 2 else RED)
    a.rect(x, y + h - 1, w, 1, GREY), a.rect(x + w - 1, y, 1, h, GREY)


def paint_tire(a, x0, y0, tire, disc, hub):
    """Колёсико 16×16: резиновая шина с насечкой, диск со спицами, ступица. Вокруг прозрачно."""
    a.rect(x0, y0, 16, 16, tire)
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            ang = math.atan2(j - 7.5, i - 7.5)
            if d > 7.6:
                a.clear(x0 + i, y0 + j)
            elif d > 5.2:
                a.px(x0 + i, y0 + j, tire if int((ang + math.pi) * 10 / math.pi) % 2 == 0 else mul(tire, 1.35))
            elif d < 1.8:
                a.px(x0 + i, y0 + j, hub)
            elif d > 4.2:
                a.px(x0 + i, y0 + j, mul(disc, 0.72))
            else:
                a.px(x0 + i, y0 + j, mul(disc, 0.78) if abs(math.sin(ang * 2.5)) < 0.3 else disc)
    return a.region(x0, y0, 16, 16)


def tube(rings, region, caps=(None, None)):
    """Прямоугольный короб вдоль хода: кольца `(вперёд, полуширина, полувысота)`, перёд это −Z.
    Лента `region` четвертями: правый бок, низ, левый бок, верх; сверху вниз от носа к корме."""
    s = math.sqrt(2.0)
    return rot(loft([(y, hx * s, hy * s) for y, hx, hy in rings], region, 4, math.pi / 4.0, caps, True), rx=-90.0)


def office_cannon():
    """Копир, стреляющий бумагой: тумба с лотками на роликах, сверху блок сканера, который
    вытянут вперёд соплом с раструбом; из щели торчит лист. Сбоку лоток с пачкой бумаги."""
    a = Atlas(64, 32, 219)
    # Блок сканера лентой: правый бок, низ, левый бок, верх; сверху вниз от сопла к корме.
    plastic(a, 0, 0, 32, 16, WHITE, 8)
    for x0 in (0, 16):
        a.rect(x0, 0, 8, 3, GREY_D)
        a.rect(x0 + 2, 3, 3, 13, SEA)
        a.rect(x0 + 5, 3, 1, 13, SEA_L)
        slats(a, x0, 11, 2, 5, GREY)
        a.rect(x0 + 7, 0, 1, 16, GREY)
    a.rect(8, 0, 8, 16, DARK)
    for y in range(1, 16, 3):
        a.rect(9, y, 6, 1, DARK_D)
    # Верх: раструб, крышка со стеклом, пульт с экраном и кнопками.
    a.rect(24, 0, 8, 3, GREY_D)
    a.px(27, 1, WHITE), a.px(28, 1, WHITE), a.px(27, 0, WHITE), a.px(28, 0, WHITE), a.px(26, 1, WHITE), a.px(29, 1, WHITE)
    a.rect(24, 3, 8, 7, GREY)
    a.rect(25, 4, 6, 5, AQUA)
    a.px(25, 4, SKY), a.px(26, 4, SKY), a.px(25, 5, SKY), a.px(29, 7, SEA), a.px(30, 8, SEA)
    a.rect(24, 10, 8, 6, DARK)
    a.rect(25, 11, 4, 2, AQUA), a.px(25, 11, SKY)
    a.px(30, 11, LED), a.px(30, 13, RED), a.px(25, 14, GOLD), a.px(27, 14, GREY), a.px(29, 14, GREY)
    a.noise(0, 0, 32, 16, 0.04)
    head = a.region(0, 0, 32, 16)
    # Срез сопла: тёмная щель с белым листом.
    a.rect(32, 0, 8, 8, GREY_D)
    a.rect(33, 2, 6, 4, K)
    a.rect(33, 3, 6, 2, WHITE)
    mouth = a.region(32, 0, 8, 8)
    a.rect(32, 8, 8, 8, DARK)
    a.rect(32, 8, 8, 1, DARK_L)
    back = a.region(32, 8, 8, 8)
    # Тумба лентой: правый бок, перёд с двумя лотками, левый бок, задняя стенка.
    plastic(a, 0, 16, 32, 12, GREY, 6)
    for x0 in (0, 16):
        slats(a, x0 + 1, 18, 5, 4, GREY)
        a.rect(x0 + 4, 23, 3, 3, GOLD), a.px(x0 + 6, 25, BRASS)
    for y in (17, 22):
        a.rect(9, y, 6, 4, WHITE)
        a.rect(9, y + 3, 6, 1, GREY_D)
        a.rect(11, y + 1, 2, 1, DARK)
    a.rect(24, 16, 8, 12, GREY_D)
    a.rect(26, 18, 4, 3, DARK), a.px(27, 22, K), a.px(27, 23, K), a.px(28, 24, K)
    a.rect(0, 27, 32, 1, DARK)
    a.shade(0, 16, 32, 12, 1.08, 0.82, 0.9)
    body = a.region(0, 16, 32, 12)
    paper(a, 40, 0, 16, 16, True)
    sheet = a.region(40, 0, 16, 16)
    a.rect(56, 0, 8, 4, DARK_D)
    a.rect(56, 1, 8, 1, METAL)
    rim = a.region(56, 0, 8, 4)
    m = Model("cannon", a)
    tris = (at(tube([(-0.46, 0.27, 0.09), (0.16, 0.27, 0.09), (0.24, 0.21, 0.07), (0.44, 0.2, 0.065), (0.5, 0.24, 0.09)],
                    head, (back, mouth)), 0.0, 0.55, -0.1)
            + at(box((0.56, 0.38, 0.66), body, back, back), 0.0, 0.27, 0.05)
            # Лист из щели: полетит следующим.
            + quad((-0.16, 0.56, -0.58), (0.16, 0.56, -0.58), (0.16, 0.5, -0.7), (-0.16, 0.5, -0.7), sheet)
            # Боковой лоток с пачкой бумаги.
            + at(rot(box((0.2, 0.04, 0.34), rim, sheet, rim), rz=-14.0), 0.36, 0.33, 0.05))
    for x in (-0.2, 0.2):
        for z in (-0.2, 0.3):
            tris += at(box((0.09, 0.08, 0.12), rim, None, rim), x, 0.04, z)
    return m.part("body", (0.0, 0.0, 0.0), tris)


def office_palm():
    """Фикус в горшке: белый кашпо с синей полосой, плетёный ствол с лёгким изгибом и крона из
    глянцевых листьев в два яруса. Лист это плоскость с вырезом по прозрачности, как лист пальмы:
    `ThreedScreen.add_palm` кладёт на свои ленты ту же правую половину атласа, на ствол левую
    (у земли на ней горшок)."""
    a = Atlas(32, 32, 245)
    # Ствол: три переплетённых побега.
    bark, bark_d, bark_l = rgb("9A6E4A"), COFFEE, TAN
    a.rect(0, 0, 16, 24, bark)
    for y in range(24):
        for x in range(16):
            k = (x + y) % 6
            if k == 0:
                a.px(x, y, bark_d)
            elif k == 1:
                a.px(x, y, bark_l)
            elif (x - y) % 8 == 0:
                a.px(x, y, mul(bark, 0.8))
    for y in (5, 13, 20):
        a.px((y * 5) % 16, y, GREEN), a.px((y * 5 + 1) % 16, y, GREEN_D)
    a.shade(0, 0, 16, 24, 1.0, 0.9, 0.7)
    a.noise(0, 0, 16, 24, 0.07)
    trunk = a.region(0, 0, 16, 24)
    # Земля в горшке и сам горшок.
    a.rect(0, 24, 16, 2, COFFEE)
    for x in range(0, 16, 3):
        a.px(x, 24, mul(COFFEE, 0.7)), a.px(x + 1, 25, mul(COFFEE, 1.3))
    soil = a.region(0, 24, 16, 2)
    a.rect(0, 26, 16, 6, WHITE)
    a.rect(0, 26, 16, 1, GREY), a.rect(0, 28, 16, 2, SEA), a.rect(0, 28, 16, 1, SEA_L), a.rect(0, 31, 16, 1, GREY_D)
    a.shade(0, 26, 16, 6, 1.0, 0.9, 0.75)
    pot = a.region(0, 26, 16, 6)
    # Лист фикуса: черешок, широкий овал с острым кончиком, светлая жилка, блик, тёмная кромка.
    for y in range(32):
        t = y / 31.0
        half = 0.6 if y < 3 else 0.8 + 6.4 * math.sin(math.pi * ((t - 0.08) / 0.92) ** 0.7) ** 0.8
        for x in range(16):
            dx = abs(x - 7.5)
            if dx <= half:
                c = GREEN
                if y < 3:
                    c = GREEN_D
                elif dx < 1.0:
                    c = GREEN_L
                elif dx > half - 1.2:
                    c = GREEN_D
                elif (int(dx) + y) % 5 == 0:
                    c = mul(GREEN, 0.86)
                elif x < 7 and (x + y) % 9 == 0:
                    c = SKY
                a.px(16 + x, y, c)
    a.noise(16, 0, 16, 32, 0.06)
    leaf = a.region(16, 0, 16, 32)
    top = (0.55, 4.2, 0.1)
    tris = (loft([(0.0, 0.26, 0.26), (0.6, 0.33, 0.33), (0.62, 0.37, 0.37), (0.76, 0.37, 0.37)], pot, 6, caps=(None, soil))
            + loft([(0.7, 0.14, 0.14), (1.6, 0.11, 0.11, 0.1, 0.0), (2.6, 0.1, 0.1, 0.3, 0.05), (3.4, 0.09, 0.09, 0.45, 0.08),
                    (4.2, 0.1, 0.1, 0.55, 0.1)], trunk, 5))
    for k in range(9):
        ang = 2.0 * math.pi * k / 9.0 + 0.3
        d = (math.sin(ang), 0.0, math.cos(ang))
        q = (math.cos(ang) * 0.85, 0.0, -math.sin(ang) * 0.85)
        droop = 0.45 + 0.14 * (k % 2)
        far = (top[0] + d[0] * 1.45, top[1] - droop, top[2] + d[2] * 1.45)
        mid = (top[0] - d[0] * 0.3, top[1] + 0.42, top[2] - d[2] * 0.3)
        tris += quad((mid[0] - q[0] * 0.5, mid[1], mid[2] - q[2] * 0.5), (mid[0] + q[0] * 0.5, mid[1], mid[2] + q[2] * 0.5),
                     (far[0] + q[0], far[1], far[2] + q[2]), (far[0] - q[0], far[1], far[2] - q[2]), leaf)
    # Нижний ярус: шесть листьев от ствола в стороны и чуть вверх.
    low = (0.42, 3.2, 0.07)
    for k in range(6):
        ang = 2.0 * math.pi * k / 6.0 + 0.8
        d = (math.sin(ang), 0.0, math.cos(ang))
        q = (math.cos(ang) * 0.42, 0.0, -math.sin(ang) * 0.42)
        far = (low[0] + d[0] * 1.2, low[1] + 0.1 - 0.2 * (k % 2), low[2] + d[2] * 1.2)
        tris += quad((low[0] - q[0], low[1] + 0.25, low[2] - q[2]), (low[0] + q[0], low[1] + 0.25, low[2] + q[2]),
                     (far[0] + q[0], far[1], far[2] + q[2]), (far[0] - q[0], far[1], far[2] - q[2]), leaf)
    return Model("palm", a).part("body", (0.0, 0.0, 0.0), tris)


def office_flag():
    """Флажок «пятница»: жёлтое полотно-стикер с буквами «ПТ» на хромированной стойке с тяжёлым
    основанием, наверху красная головка канцелярской кнопки; полотно отдельной частью у стойки."""
    a = Atlas(64, 32, 217)
    a.rect(0, 0, 32, 20, GOLD)
    for y in range(0, 20, 5):
        a.rect(0, y, 32, 1, mul(GOLD, 0.9))
    # Буквы «ПТ» крупно, с тенью.
    for dx, dy, c in ((1, 1, BRASS), (0, 0, RED_D)):
        a.rect(6 + dx, 4 + dy, 9, 2, c), a.rect(6 + dx, 4 + dy, 2, 12, c), a.rect(13 + dx, 4 + dy, 2, 12, c)
        a.rect(18 + dx, 4 + dy, 10, 2, c), a.rect(22 + dx, 4 + dy, 2, 12, c)
    # Кромка у стойки, светлая клейкая полоса сверху, загнутый уголок.
    a.rect(0, 0, 2, 20, WHITE), a.rect(2, 0, 30, 1, GOLD_L), a.rect(0, 19, 32, 1, BRASS)
    for i in range(4):
        a.rect(31 - i, 19 - (3 - i), i + 1, 1, GOLD_L)
        a.px(31 - i, 19 - (3 - i) - 1, BRASS)
    a.noise(0, 0, 32, 20, 0.05)
    cloth = a.region(0, 0, 32, 20)
    a.rect(32, 0, 8, 32, METAL_L)
    for y in range(0, 32, 6):
        a.rect(32, y, 8, 1, METAL)
        a.rect(32, y + 1, 8, 1, WHITE)
    a.rect(32, 20, 8, 3, DARK)
    a.shade(32, 0, 8, 32, 1.0, 0.9, 0.6)
    pole = a.region(32, 0, 8, 32)
    a.rect(40, 0, 8, 8, DARK)
    a.rect(40, 0, 8, 1, DARK_L), a.rect(40, 4, 8, 1, DARK_D)
    a.px(42, 2, METAL), a.px(46, 6, METAL)
    base = a.region(40, 0, 8, 8)
    a.rect(48, 0, 8, 8, RED)
    a.rect(49, 1, 3, 3, rgb("F28A7A"))
    a.rect(48, 7, 8, 1, RED_D), a.rect(55, 0, 1, 8, RED_D)
    pin = a.region(48, 0, 8, 8)
    m = Model("flag", a)
    m.part("pole", (0.0, 0.0, 0.0),
           loft([(0.0, 0.05, 0.05), (2.7, 0.04, 0.04)], pole, 4, caps=(None, base))
           + loft([(0.0, 0.26, 0.26), (0.14, 0.18, 0.18)], base, 5, caps=(None, base), flat=True)
           + at(box((0.12, 0.12, 0.12), pin, pin, pin), 0.0, 2.76, 0.0))
    m.part("cloth", (0.04, 2.3, 0.0),
           quad((0.04, 2.62, 0.0), (1.0, 2.56, 0.0), (1.0, 2.02, 0.0), (0.04, 1.98, 0.0), cloth), "pole")
    return m


def office_lighthouse():
    """Серверная стойка с мигалкой: ориентир на горизонте высотой с маяк. Чёрный шкаф с рядами
    блоков и огоньками за стеклянной дверью, жалюзи и наклейки на боках, жгуты кабелей сзади,
    плита фальшпола с полосой опасности, косые упоры, наверху красный проблесковый маячок."""
    a = Atlas(64, 64, 253)
    # Шкаф лентой, четыре грани по 16: правый бок, перёд, левый бок, зад.
    a.rect(0, 0, 64, 40, DARK)
    for x0 in range(0, 64, 16):
        a.rect(x0, 0, 1, 40, DARK_D), a.rect(x0 + 15, 0, 1, 40, DARK_D)
        a.rect(x0 + 1, 0, 14, 3, DARK_L)
        a.rect(x0 + 1, 37, 14, 3, DARK_D)
    # Перёд и зад: блоки по четыре строки, у каждого ручки и огни.
    for x0, front in ((16, True), (48, False)):
        for row, y in enumerate(range(4, 36, 4)):
            a.rect(x0 + 2, y, 12, 3, METAL if (row + (0 if front else 1)) % 3 else GREY_D)
            a.rect(x0 + 2, y + 2, 12, 1, mul(METAL, 0.6))
            if front:
                a.px(x0 + 3, y + 1, LED if row % 4 != 2 else GOLD)
                a.px(x0 + 5, y + 1, AQUA if row % 3 else LED)
                a.px(x0 + 7, y + 1, RED if row == 5 else LED)
                a.rect(x0 + 10, y, 3, 1, K), a.rect(x0 + 10, y + 1, 3, 1, DARK_L)
            else:
                # Сзади разъёмы и цветные кабели вниз.
                a.px(x0 + 4, y + 1, K), a.px(x0 + 7, y + 1, K), a.px(x0 + 10, y + 1, K)
        if front:
            a.rect(x0 + 4, 1, 8, 1, AQUA), a.px(x0 + 5, 1, SKY)
            # Блик стеклянной двери наискось.
            for j in range(4, 36):
                c = a.get(x0 + 3 + (j // 3) % 9, j)
                a.px(x0 + 3 + (j // 3) % 9, j, mul(c, 1.35))
        else:
            for x, c in ((x0 + 4, AQUA), (x0 + 7, GOLD), (x0 + 10, RED)):
                a.rect(x, 6, 1, 30, c)
                a.rect(x + 1, 6, 1, 30, mul(c, 0.6))
    # Бока: поле перфорации, наклейка, ручка.
    for x0 in (0, 32):
        for j in range(5, 35):
            for i in range(3, 13):
                if (i + j) % 2 == 0:
                    a.px(x0 + i, j, DARK_D)
        a.rect(x0 + 4, 9, 8, 6, GOLD)
        a.rect(x0 + 5, 11, 6, 1, BRASS), a.rect(x0 + 5, 13, 4, 1, BRASS)
        a.rect(x0 + 4, 24, 8, 4, WHITE)
        hazard(a, x0 + 4, 26, 8, 2, RED, WHITE)
        a.rect(x0 + 2, 18, 1, 5, METAL_L)
    a.shade(0, 0, 64, 40, 1.08, 0.85, 1.0)
    a.noise(0, 0, 64, 40, 0.05)
    hull = a.region(0, 0, 64, 40)
    # Маячок: красное стекло с рёбрами и бликом.
    a.rect(0, 40, 32, 8, RED)
    for x in range(0, 32, 4):
        a.rect(x, 40, 1, 8, RED_D)
        a.px(x + 2, 42, rgb("F7A08A")), a.px(x + 2, 43, rgb("F7A08A"))
    a.rect(0, 40, 32, 1, rgb("F7A08A")), a.rect(0, 46, 32, 2, METAL)
    a.shade(0, 40, 32, 8, 1.2, 0.9, 0.85)
    lamp = a.region(0, 40, 32, 8)
    # Плита фальшпола с полосой опасности.
    plastic(a, 32, 40, 16, 8, GREY, 4)
    hazard(a, 32, 45, 16, 3)
    table = a.region(32, 40, 16, 8)
    a.rect(48, 40, 8, 8, DARK_D)
    for x in range(48, 56, 2):
        a.px(x, 41 + (x // 2) % 2 * 3, DARK_L)
    a.noise(48, 40, 8, 8, 0.12)
    dark = a.region(48, 40, 8, 8)
    # Упор: жёлтый уголок с отверстиями.
    a.rect(0, 48, 16, 16, GOLD)
    a.rect(0, 48, 16, 2, GOLD_L), a.rect(0, 48, 2, 16, BRASS), a.rect(0, 62, 16, 2, BRASS)
    for x, y in ((5, 53), (10, 53), (5, 58), (10, 58)):
        a.rect(x, y, 2, 2, K)
    a.noise(0, 48, 16, 16, 0.06)
    fin = a.region(0, 48, 16, 16)
    tris = (at(box((2.9, 0.6, 2.9), table, dark, None), 0.0, 0.3)
            + at(box((1.9, 7.0, 1.9), hull, dark, None), 0.0, 4.1)
            + at(box((1.5, 0.36, 1.5), table, dark, None), 0.0, 7.78)
            + loft([(7.96, 0.5, 0.5), (8.12, 0.44, 0.44)], dark, 8, caps=(None, dark), flat=True)
            + loft([(8.12, 0.38, 0.38), (8.66, 0.38, 0.38), (8.9, 0.26, 0.26), (9.0, 0.04, 0.04)], lamp, 8))
    # Косые упоры от плиты к стенкам шкафа, по одному на грань.
    for k in range(4):
        ang = math.pi / 2.0 * k
        d = (math.sin(ang), math.cos(ang))
        tris += quad((d[0] * 0.95, 2.6, d[1] * 0.95), (d[0] * 0.95, 0.6, d[1] * 0.95),
                     (d[0] * 1.45, 0.6, d[1] * 1.45), (d[0] * 1.2, 1.3, d[1] * 1.2), fin)
    return Model("lighthouse", a).part("body", (0.0, 0.0, 0.0), tris)


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


def office_cart():
    """Почтовая тележка героя: низкая рама на четырёх колёсиках, синий тканевый короб с белым
    кантом и конвертом на бортах, в коробе посылки, мешок и письма, сзади хромированная ручка
    с тёмной накладкой, на борту красный флажок почтового ящика. Паруса и мачты нет. Части и
    точки вращения как у пиратской повозки: `body`, `axle_f`, `axle_r`."""
    a = Atlas(64, 64, 261)
    # Борт лентой вокруг короба: четверти это правый борт, перёд, левый борт, зад.
    a.rect(0, 0, 64, 12, SEA)
    for x in range(0, 64, 4):
        a.rect(x, 2, 1, 8, mul(SEA, 0.86))
    a.rect(0, 0, 64, 2, WHITE), a.rect(0, 2, 64, 1, NAVY)
    for x in range(1, 64, 3):
        a.px(x, 1, GREY)
    for x0 in (0, 32):
        # Конверт на борту.
        a.rect(x0 + 4, 4, 9, 5, WHITE)
        for i in range(5):
            a.px(x0 + 4 + i, 4 + min(i, 2), GREY_D), a.px(x0 + 12 - i, 4 + min(i, 2), GREY_D)
        a.px(x0 + 11, 7, RED)
    # Перёд: табличка с адресом и два отражателя.
    a.rect(20, 4, 8, 4, WHITE)
    a.rect(21, 5, 6, 1, DARK), a.rect(21, 7, 4, 1, GREY_D)
    a.rect(17, 5, 2, 2, GOLD), a.rect(29, 5, 2, 2, GOLD)
    # Зад: планшет с накладной и красные катафоты.
    a.rect(53, 3, 7, 6, BRASS)
    a.rect(54, 4, 5, 4, WHITE), a.rect(55, 5, 3, 1, GREY_D), a.rect(55, 7, 2, 1, GREY_D), a.rect(55, 3, 3, 1, METAL_L)
    a.rect(49, 5, 2, 2, RED), a.rect(61, 5, 2, 2, RED)
    a.rect(0, 10, 64, 2, METAL), a.rect(0, 11, 64, 1, DARK)
    for x in range(2, 64, 5):
        a.px(x, 10, METAL_L)
    for x in (0, 16, 32, 48):
        a.rect(x, 0, 1, 10, NAVY)
    a.shade(0, 0, 64, 12, 1.08, 0.82, 1.0)
    a.noise(0, 0, 64, 12, 0.05)
    hull = a.region(0, 0, 64, 12)
    # Нутро короба сверху: письма внахлёст на тёмном дне.
    a.rect(0, 12, 16, 16, NAVY)
    for x, y, w, h, c in ((1, 13, 7, 4, WHITE), (6, 16, 8, 5, TAPE), (2, 20, 6, 4, WHITE), (9, 22, 6, 5, WHITE),
                          (3, 24, 5, 3, SKY)):
        a.rect(x, y, w, h, c)
        a.rect(x, y + h - 1, w, 1, mul(c, 0.75))
        a.px(x + w - 2, y + 1, RED)
        a.rect(x + 1, y + 2, max(w - 4, 1), 1, GREY_D)
    a.rect(0, 12, 16, 1, WHITE), a.rect(0, 27, 16, 1, WHITE), a.rect(0, 12, 1, 16, WHITE), a.rect(15, 12, 1, 16, WHITE)
    deck = a.region(0, 12, 16, 16)
    wheel = paint_tire(a, 16, 12, DARK, GREY, AQUA)
    a.rect(32, 12, 8, 4, DARK_D)
    for x in range(32, 40, 2):
        a.px(x, 13, DARK_L)
    rim = a.region(32, 12, 8, 4)
    # Рама: серый металл, заклёпки, жёлтая полоса-отражатель.
    a.rect(32, 16, 8, 12, METAL)
    a.rect(32, 16, 8, 2, METAL_L), a.rect(32, 20, 8, 2, GOLD), a.rect(32, 26, 8, 2, DARK)
    for x in (33, 38):
        a.px(x, 24, DARK), a.px(x, 18, DARK)
    a.noise(32, 16, 8, 12, 0.05)
    rail = a.region(32, 16, 8, 12)
    # Бок посылки: картон, полоса скотча, штамп.
    a.rect(40, 12, 8, 16, CARD)
    a.rect(40, 12, 8, 2, TAPE), a.rect(40, 14, 8, 1, CARD_D), a.rect(40, 27, 8, 1, CARD_D)
    a.rect(42, 18, 4, 4, RED), a.rect(43, 19, 2, 2, CARD)
    for y in (16, 24):
        a.rect(41, y, 6, 1, mul(CARD, 0.9))
    a.noise(40, 12, 8, 16, 0.07)
    card = a.region(40, 12, 8, 16)
    # Конверт авиапочты: красно-синяя кайма, клапан, марка.
    a.rect(48, 12, 16, 16, WHITE)
    for i in range(16):
        c = RED if (i // 2) % 2 == 0 else SEA
        a.px(48 + i, 12, c), a.px(48 + i, 27, c), a.px(48, 12 + i, c), a.px(63, 12 + i, c)
    for i in range(7):
        a.px(49 + i, 13 + i, GREY_D), a.px(62 - i, 13 + i, GREY_D)
    a.rect(58, 21, 4, 5, AQUA), a.px(59, 23, WHITE), a.px(60, 22, GOLD)
    a.rect(50, 23, 6, 1, DARK), a.rect(50, 25, 4, 1, GREY_D)
    envelope = a.region(48, 12, 16, 16)
    # Верх посылки: клапаны, скотч крестом, адресная наклейка, знак «хрупкое».
    a.rect(0, 32, 32, 28, CARD)
    a.rect(0, 32, 32, 1, CARD_D), a.rect(0, 59, 32, 1, CARD_D), a.rect(0, 32, 1, 28, CARD_D), a.rect(31, 32, 1, 28, CARD_D)
    a.rect(13, 32, 6, 28, TAPE), a.rect(0, 44, 32, 4, TAPE)
    a.rect(15, 32, 1, 28, mul(TAPE, 0.82)), a.rect(0, 46, 32, 1, mul(TAPE, 0.82))
    a.rect(2, 34, 10, 8, WHITE)
    a.rect(3, 36, 8, 1, DARK), a.rect(3, 38, 6, 1, GREY_D), a.rect(3, 40, 7, 1, GREY_D)
    a.rect(21, 50, 8, 8, RED)
    a.rect(23, 52, 4, 3, WHITE), a.rect(24, 55, 2, 2, WHITE)
    a.rect(21, 34, 8, 6, GOLD), a.rect(22, 36, 5, 1, BRASS)
    a.noise(0, 32, 32, 28, 0.06)
    lid = a.region(0, 32, 32, 28)
    # Труба ручки: хром с бликом; накладка: тёмная резина с насечкой.
    a.rect(32, 32, 16, 16, METAL_L)
    a.rect(36, 32, 3, 16, WHITE), a.rect(44, 32, 3, 16, METAL)
    for y in range(35, 48, 6):
        a.rect(32, y, 16, 1, METAL)
    chrome = a.region(32, 32, 16, 16)
    a.rect(48, 32, 16, 16, DARK)
    for x in range(48, 64, 2):
        a.rect(x, 32, 1, 16, DARK_D)
    a.rect(48, 36, 16, 2, DARK_L), a.rect(48, 32, 2, 16, METAL_L), a.rect(62, 32, 2, 16, METAL_L)
    grip = a.region(48, 32, 16, 16)
    # Мешок: холст со складками, синяя полоса, завязка.
    a.rect(32, 48, 16, 16, TAPE)
    for x in range(33, 48, 3):
        a.rect(x, 50, 1, 14, mul(TAPE, 0.84))
    a.rect(32, 48, 16, 3, BRASS), a.rect(32, 49, 16, 1, COFFEE)
    a.rect(32, 56, 16, 3, SEA), a.rect(32, 56, 16, 1, SEA_L)
    a.shade(32, 48, 16, 16, 1.05, 0.8, 0.8)
    a.noise(32, 48, 16, 16, 0.06)
    sack = a.region(32, 48, 16, 16)
    # Флажок почтового ящика.
    a.rect(48, 48, 8, 8, RED)
    a.rect(48, 48, 8, 1, rgb("F28A7A")), a.rect(48, 55, 8, 1, RED_D), a.rect(50, 51, 4, 2, WHITE)
    tab = a.region(48, 48, 8, 8)
    m = Model("cart", a)
    body = (at(box((0.84, 0.1, 2.06), rail, rail, rail), 0.0, 0.42)
            # Короб расширяется кверху.
            + at(box((0.86, 0.46, 1.6), hull, deck, None, (1.08, 1.04)), 0.0, 0.7, -0.12)
            # Посылки: большая у носа, малая за ней наискось.
            + at(rot(box((0.52, 0.28, 0.6), card, lid, None), ry=10.0), -0.06, 1.0, -0.46)
            + at(rot(box((0.36, 0.2, 0.42), card, lid, None), ry=-24.0), 0.16, 0.99, 0.02)
            # Мешок с завязанной горловиной у задней стенки.
            + at(loft([(0.0, 0.2, 0.2), (0.16, 0.25, 0.23), (0.32, 0.15, 0.15), (0.38, 0.05, 0.05), (0.45, 0.1, 0.1)], sack, 5),
                 0.18, 0.88, 0.42)
            # Письма торчат из короба.
            + quad((-0.4, 1.2, 0.3), (-0.04, 1.24, 0.36), (-0.04, 0.9, 0.42), (-0.4, 0.88, 0.36), envelope)
            + quad((-0.36, 1.12, 0.1), (-0.02, 1.1, 0.02), (-0.02, 0.88, 0.06), (-0.36, 0.88, 0.14), envelope)
            # Ручка: две стойки с наклоном назад и перекладина с накладкой.
            + at(box((0.82, 0.06, 0.07), grip, grip, grip), 0.0, 1.16, 1.03))
    for x in (-0.36, 0.36):
        body += at(rot(box((0.05, 0.74, 0.05), chrome, None, None), rx=10.0), x, 0.81, 0.965)
    # Флажок почтового ящика на правом борту: не выше 0.3 м над кромкой.
    body += (at(box((0.03, 0.26, 0.03), chrome, chrome, None), 0.49, 1.04, 0.56)
             + quad((0.49, 1.17, 0.56), (0.49, 1.17, 0.36), (0.49, 1.05, 0.36), (0.49, 1.05, 0.56), tab))
    m.part("body", (0.0, 0.0, 0.0), body)
    cart_axles(m, rim, wheel, 0.32, 0.09, 0.6, 8, rim)
    return m


def office_cart_rival():
    """Кресло соперников: чёрное кожаное кресло начальника на гоночной раме с четырьмя
    колёсиками. Стёганое сиденье и спинка с красным кантом, подголовник, подлокотники, хромовая
    стойка газлифта, спереди подножка, на спинке сзади красная полоса и жёлтый номер. Колёса на
    осях `axle_f`, `axle_r`; части и точки вращения те же, что у тележки."""
    a = Atlas(64, 64, 263)
    # Спинка лентой: правый торец, лицо (стёжка с пуговицами), левый торец, тыл (жёсткая чаша).
    a.rect(0, 0, 64, 16, DARK)
    for x0 in (0, 32):
        a.rect(x0, 0, 16, 16, DARK_D)
        a.rect(x0 + 7, 0, 2, 16, RED_D)
    a.rect(16, 0, 16, 16, DARK)
    for j in range(16):
        for i in range(16):
            if (i + j) % 6 == 0 or (i - j) % 6 == 0:
                a.px(16 + i, j, DARK_D)
            elif (i + j) % 6 == 1:
                a.px(16 + i, j, DARK_L)
    for i, j in ((3, 3), (9, 3), (15, 3), (6, 6), (12, 6), (3, 9), (9, 9), (15, 9), (6, 12), (12, 12)):
        a.px(15 + i, j, GOLD)
    a.rect(16, 0, 1, 16, RED), a.rect(31, 0, 1, 16, RED), a.rect(16, 0, 16, 1, RED)
    a.rect(48, 0, 16, 16, DARK_L)
    a.rect(48, 0, 16, 1, METAL), a.rect(48, 5, 16, 3, RED), a.rect(48, 8, 16, 1, RED_D)
    a.rect(53, 10, 6, 5, GOLD)
    a.rect(55, 11, 1, 3, K), a.rect(57, 11, 1, 3, K), a.px(56, 11, K), a.px(56, 13, K)
    for x in (49, 62):
        a.px(x, 2, METAL_L), a.px(x, 13, METAL_L)
    a.shade(0, 0, 64, 16, 1.1, 0.85, 1.0)
    a.noise(0, 0, 64, 16, 0.05)
    hull = a.region(0, 0, 64, 16)
    # Кромка сиденья: валик кожи, красный кант, строчка, снизу пластик.
    a.rect(0, 16, 64, 8, DARK)
    a.rect(0, 16, 64, 1, DARK_L), a.rect(0, 18, 64, 1, RED), a.rect(0, 22, 64, 2, DARK_D)
    for x in range(1, 64, 3):
        a.px(x, 20, METAL)
    a.noise(0, 16, 64, 8, 0.05)
    skirt = a.region(0, 16, 64, 8)
    # Подушка сиденья сверху: стёжка ромбом, кант по краю.
    a.rect(0, 24, 16, 16, DARK)
    for j in range(16):
        for i in range(16):
            if (i + j) % 5 == 0 or (i - j) % 5 == 0:
                a.px(i, 24 + j, DARK_D)
            elif (i + j) % 5 == 1:
                a.px(i, 24 + j, DARK_L)
    a.rect(0, 24, 16, 1, RED), a.rect(0, 39, 16, 1, RED), a.rect(0, 24, 1, 16, RED), a.rect(15, 24, 1, 16, RED)
    a.noise(0, 24, 16, 16, 0.05)
    deck = a.region(0, 24, 16, 16)
    wheel = paint_tire(a, 16, 24, DARK_D, DARK_L, RED)
    a.rect(32, 24, 8, 4, K)
    for x in range(32, 40, 2):
        a.px(x, 25, DARK_L)
    rim = a.region(32, 24, 8, 4)
    # Хром стойки.
    a.rect(40, 24, 8, 8, METAL_L)
    a.rect(42, 24, 2, 8, WHITE), a.rect(46, 24, 2, 8, METAL), a.rect(40, 27, 8, 1, METAL)
    chrome = a.region(40, 24, 8, 8)
    # Пластик рамы: рёбра жёсткости, винты.
    a.rect(0, 40, 32, 16, DARK_L)
    for x in range(0, 32, 4):
        a.rect(x, 40, 1, 16, DARK)
    a.rect(0, 40, 32, 1, METAL), a.rect(0, 55, 32, 1, DARK_D), a.rect(0, 47, 32, 2, DARK)
    for x in (2, 14, 26):
        a.px(x, 43, METAL_L), a.px(x, 52, METAL_L)
    a.noise(0, 40, 32, 16, 0.06)
    frame = a.region(0, 40, 32, 16)
    # Мягкие накладки подлокотников и подголовника.
    a.rect(32, 32, 32, 16, DARK)
    for y in range(32, 48, 4):
        a.rect(32, y, 32, 1, DARK_L)
        a.rect(32, y + 3, 32, 1, DARK_D)
    for x in range(34, 64, 6):
        a.rect(x, 32, 1, 16, DARK_D)
    a.rect(32, 46, 32, 2, RED_D)
    a.noise(32, 32, 32, 16, 0.05)
    pad = a.region(32, 32, 32, 16)
    m = Model("cart_rival", a)
    body = (at(box((0.22, 0.1, 1.66), frame, frame, frame), 0.0, 0.34)
            # Подножка спереди.
            + at(box((0.56, 0.05, 0.24), frame, frame, frame), 0.0, 0.36, -0.9)
            # Кожух и хромовая стойка газлифта.
            + at(loft([(0.39, 0.17, 0.17), (0.46, 0.07, 0.07), (0.62, 0.06, 0.06)], chrome, 6, flat=True), 0.0, 0.0, 0.08)
            + at(box((0.84, 0.16, 0.86), skirt, deck, frame, (0.94, 0.96)), 0.0, 0.68, 0.05)
            # Спинка с наклоном назад и подголовник.
            + at(rot(box((0.78, 0.62, 0.13), hull, pad, None, (0.86, 1.0)), rx=9.0), 0.0, 1.05, 0.5)
            + at(rot(box((0.42, 0.17, 0.13), pad, pad, pad), rx=9.0), 0.0, 1.43, 0.57))
    for x in (-0.43, 0.43):
        body += (at(box((0.08, 0.28, 0.07), frame, None, None), x, 0.84, 0.2)
                 + at(box((0.11, 0.05, 0.48), pad, pad, pad), x, 0.995, 0.08))
    m.part("body", (0.0, 0.0, 0.0), body)
    cart_axles(m, rim, wheel, 0.32, 0.07, 0.53, 6, rim)
    return m


def office_pistol():
    """Степлер в руке клерка: оружие вида от первого лица, носик смотрит в −Z, ноль в рукояти.
    Красная крышка с бликом приподнята у носа, под ней магазин со скобами, тёмное основание с
    площадкой; большой палец лежит на крышке, манжета белой рубашки с пуговицей и часами."""
    a = Atlas(32, 32, 265)
    # Крышка лентой: правый бок, низ (магазин), левый бок, верх; сверху вниз от носа к шарниру.
    a.rect(0, 0, 16, 8, RED)
    for x0 in (0, 8):
        a.rect(x0, 0, 4, 8, RED)
        a.rect(x0 + 3, 0, 1, 8, RED_D)
    a.rect(4, 0, 4, 8, METAL_L)
    for y in range(0, 8, 2):
        a.rect(5, y, 2, 1, METAL)
    a.rect(12, 0, 4, 8, RED)
    a.rect(13, 1, 1, 5, rgb("F28A7A"))
    a.px(14, 6, WHITE), a.px(13, 6, WHITE)
    a.rect(0, 0, 16, 1, DARK), a.rect(0, 7, 16, 1, RED_D)
    a.noise(0, 0, 16, 8, 0.05)
    iron = a.region(0, 0, 16, 8)
    # Срез носика: щель со скобой.
    a.rect(16, 0, 4, 4, DARK)
    a.rect(17, 1, 2, 1, METAL_L), a.px(17, 2, METAL_L), a.px(18, 2, METAL_L)
    bore = a.region(16, 0, 4, 4)
    # Основание: тёмный пластик, площадка-наковальня, резиновые ножки.
    a.rect(0, 8, 16, 8, DARK)
    a.rect(0, 8, 16, 1, DARK_L), a.rect(0, 15, 16, 1, K)
    for x in range(1, 16, 3):
        a.rect(x, 11, 1, 3, DARK_D)
    a.rect(6, 9, 4, 1, METAL_L), a.px(12, 13, RED)
    a.noise(0, 8, 16, 8, 0.07)
    grip = a.region(0, 8, 16, 8)
    # Кисть: пальцы, суставы, ноготь.
    a.rect(0, 16, 16, 8, SKIN)
    a.rect(0, 19, 16, 1, TAN)
    for x in (3, 7, 11):
        a.rect(x, 16, 1, 3, TAN)
        a.px(x + 1, 17, SKIN_L)
    a.rect(13, 21, 2, 2, SKIN_L)
    a.shade(0, 16, 16, 8, 1.05, 0.85, 0.8)
    a.noise(0, 16, 16, 8, 0.05)
    hand = a.region(0, 16, 16, 8)
    # Рукав рубашки: у кисти (низ куска) манжета с пуговицей и золотые часы.
    a.rect(16, 8, 16, 16, WHITE)
    for y in range(9, 19, 3):
        a.rect(16, y, 16, 1, GREY)
    for x in range(17, 32, 5):
        a.rect(x, 8, 1, 11, mul(WHITE, 0.93))
    a.rect(16, 19, 16, 1, GREY_D), a.rect(16, 20, 16, 2, WHITE), a.px(24, 21, GREY_D)
    a.rect(16, 22, 16, 2, GOLD), a.rect(22, 22, 4, 2, SKY), a.px(23, 22, WHITE), a.rect(16, 23, 16, 1, BRASS)
    a.rect(22, 23, 4, 1, AQUA)
    a.shade(16, 8, 16, 16, 1.0, 0.9, 0.75)
    a.noise(16, 8, 16, 16, 0.04)
    sleeve = a.region(16, 8, 16, 16)
    arm = rot(loft([(y, hx * math.sqrt(2.0), hy * math.sqrt(2.0)) for y, hx, hy in
                    ((-0.04, 0.03, 0.026), (0.26, 0.03, 0.026), (0.33, 0.026, 0.016), (0.37, 0.02, 0.01))],
                   iron, 4, math.pi / 4.0, (bore, bore), True), rx=-82.0)
    return Model("pistol", a).part("body", (0.0, 0.0, 0.0),
                                   at(arm, 0.0, 0.062, 0.0)
                                   # Основание и шарнир.
                                   + at(box((0.06, 0.024, 0.37), grip, grip, grip), 0.0, 0.012, -0.17)
                                   + at(box((0.066, 0.075, 0.06), grip, grip, grip), 0.0, 0.04, 0.02)
                                   # Кисть снизу, большой палец на крышке.
                                   + at(box((0.09, 0.1, 0.11), hand, hand, hand), 0.0, -0.04, 0.02)
                                   + at(box((0.026, 0.11, 0.04), hand, hand, hand), 0.05, 0.035, 0.03)
                                   + at(rot(box((0.03, 0.026, 0.1), hand, hand, hand), ry=-28.0, rx=6.0), 0.03, 0.105, -0.02)
                                   + at(rot(loft([(0.0, 0.045, 0.045), (0.5, 0.06, 0.06)], sleeve, 4, math.pi / 4.0), rx=65.0), 0.0, -0.08, 0.07))


def office_hoop():
    """Мусорная корзина под маркерной доской: цель спорта. Щит это белая доска в алюминиевой
    раме с красным квадратом прицела, стикерами и маркерами в лотке; кольцо это обод корзины,
    сетка из чёрной проволоки; стойка хромированная. Кольцо и щит там же и тех же размеров,
    что у пиратов."""
    a = Atlas(64, 64, 267)
    a.rect(0, 0, 32, 24, WHITE)
    # Следы стёртого маркера и график.
    for i in range(9):
        a.px(3 + i, 17 - i // 2, SKY), a.px(22 + i // 2, 4 + i % 3, SKY)
    for x, y, w, h in ((10, 9, 12, 1), (10, 18, 12, 1), (10, 9, 1, 10), (21, 9, 1, 10)):
        a.rect(x, y, w, h, RED)
    a.rect(2, 2, 5, 5, GOLD), a.rect(2, 6, 5, 1, BRASS), a.rect(3, 4, 3, 1, BRASS)
    a.rect(25, 12, 5, 5, AQUA), a.rect(25, 16, 5, 1, SEA), a.rect(26, 14, 3, 1, SEA)
    a.rect(24, 2, 5, 5, GREEN_L), a.rect(24, 6, 5, 1, GREEN), a.px(26, 2, RED)
    for i in range(6):
        a.px(3 + i, 12 - (i * 5) % 4, SEA)
    a.rect(0, 0, 32, 1, METAL_L), a.rect(0, 0, 1, 24, METAL_L), a.rect(31, 0, 1, 24, METAL)
    # Лоток с маркерами понизу.
    a.rect(0, 21, 32, 3, METAL)
    a.rect(0, 21, 32, 1, METAL_L)
    for x, c in ((4, RED), (10, SEA), (16, GREEN), (23, K)):
        a.rect(x, 22, 4, 1, c), a.px(x + 4, 22, WHITE)
    a.noise(0, 0, 32, 24, 0.03)
    board = a.region(0, 0, 32, 24)
    a.rect(32, 0, 16, 4, DARK)
    a.rect(32, 0, 16, 1, METAL_L), a.rect(32, 1, 16, 1, DARK_L), a.rect(32, 3, 16, 1, K)
    ring = a.region(32, 0, 16, 4)
    # Проволочная сетка корзины: ромбы, сверху и снизу обручи.
    for y in range(16):
        for x in range(32):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                a.px(32 + x, 8 + y, DARK if (x + y) % 8 else METAL)
    a.rect(32, 8, 32, 1, DARK), a.rect(32, 22, 32, 2, DARK), a.rect(32, 15, 32, 1, DARK_L)
    net = a.region(32, 8, 32, 16)
    a.rect(0, 24, 8, 32, METAL_L)
    for y in range(24, 56, 6):
        a.rect(0, y, 8, 1, METAL)
        a.rect(0, y + 1, 8, 1, WHITE)
    a.rect(0, 40, 8, 3, GOLD), a.rect(0, 43, 8, 1, BRASS)
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
    edge = (u0, v0, u0 + (u1 - u0) / 32.0, v1)
    for x in (-0.65, 0.65):
        faces += quad((x, 3.875, -0.15), (x, 3.875, -0.09), (x, 2.925, -0.09), (x, 2.925, -0.15), edge)
    for y in (2.925, 3.875):
        faces += quad((0.65, y, -0.15), (-0.65, y, -0.15), (-0.65, y, -0.09), (0.65, y, -0.09), edge)
    return Model("hoop", a).part("body", (0.0, 0.0, 0.0),
                                 loft([(0.0, 0.09, 0.09), (3.9, 0.07, 0.07)], post, 5)
                                 + loft([(0.0, 0.3, 0.3), (0.12, 0.2, 0.2)], post, 5, flat=True)
                                 + at(box((0.06, 0.06, 0.2), ring, ring, ring), 0.0, rim_y, -0.2)
                                 + faces + ring_tris + basket + flip(basket))


MODELS = [office_cannon, office_palm, office_flag, office_lighthouse, office_cart, office_cart_rival, office_pistol,
          office_hoop]


if __name__ == "__main__":
    models = [f() for f in MODELS]
    for m in models:
        print("%-11s частей %d, треугольников %3d%s" % (m.name, len(m.parts), m.tris(),
                                                        "  БОЛЬШЕ %d" % lm.MAX_TRIS if m.tris() > lm.MAX_TRIS else ""))
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
