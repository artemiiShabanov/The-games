#!/usr/bin/env python3
"""Крупный реквизит и транспорт «Сладостей» для low poly и «продвинутых» (#137): зеркала пиратских
моделей из `lowpoly_meshes.py` и космических из `space_mesh_big.py` с теми же именами слотов,
частей и точками вращения, тем же нулём и габаритами, чтобы десять 3D-демок работали без правок.
Цвета и облик из основы 16/32 (`sweets16.py`, `sweets_road16.py`, `sweets_hold16.py`).

  cannon      пушка с попкорном: полосатый ствол с раструбом, лафет-коробка, колёса из печенья
              (ствол в −Z, как у пушки)
  palm        дерево сахарной ваты; атлас: слева ствол (вафельная трубочка), справа клок ваты
              (эти же половины берёт `ThreedScreen.add_palm`)
  flag        флаг-леденец: части `pole` (трость с леденцом-спиралью наверху) и `cloth`
  lighthouse  торт со свечой в три яруса на блюде, высота маяка
  cart        эклер на вафельном подносе: `body`, оси `axle_f`, `axle_r` с печеньем-сэндвичем;
              паруса и мачты нет: бампер-трость и низкий вафельный спойлер
  cart_rival  кекс в гофрированной формочке: те же части, колёса из печенья с шоколадной
              крошкой, фары-леденцы, спойлером плитка шоколада плашмя
  pistol      кондитерский шприц в пряничной варежке, вид от первого лица
  hoop        пончик на вафельном щите; кольцо там же и с тем же просветом

    python3 tools/sweets_mesh_big.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from lowpoly_meshes import Atlas, Model, at, box, flip, loft, mul, quad, rgb, rot  # noqa: E402
from sweets_mesh_chars import (BLACK, BREAD, BREAD_D, BREAD_L, CARAMEL, CARAMEL_D, CARAMEL_L, CHOCO,  # noqa: E402
                               CHOCO_D, CHOCO_L, ICING, ICING_D, JELLY, JELLY_D, JELLY_L, MINT, MINT_D,
                               MINT_L, PINK, PINK_D, PINK_L)

# Посыпка: цвета вперемешку по кругу.
SPRINKLES = (ICING, MINT, CARAMEL, JELLY, MINT_L)
# Длины потёков глазури по кругу: соседние не совпадают.
DRIPS = (3, 1, 4, 2, 0, 3, 5, 1, 2, 4, 0, 2)


def crumbs(a, x, y, w, h, n, dark, light):
    """Крошки и поры выпечки: тёмные и светлые точки вразброс."""
    for i in range(n):
        a.px(x + a.rng.randrange(w), y + a.rng.randrange(h), dark if i % 3 else light)


def candy(a, x, y, w, h, c0, c1, period=8, lean=1):
    """Карамельная трость: полосы наискось, у края светлой полосы блик. `period` делит ширину
    куска, чтобы шов сзади сходился."""
    for j in range(h):
        for i in range(w):
            k = (i + j * lean) % period
            c = c0 if k < period // 2 else c1
            if k == period // 2:
                c = mul(c1, 0.9)
            a.px(x + i, y + j, c)


def waffle(a, x, y, w, h, step=4, base=CARAMEL, dark=CARAMEL_D, light=CARAMEL_L):
    """Вафля: клетки с тёмной бороздой и светлым ребром за ней."""
    a.rect(x, y, w, h, base)
    for j in range(h):
        for i in range(w):
            if i % step == 0 or j % step == 0:
                a.px(x + i, y + j, dark)
            elif i % step == 1 or j % step == 1:
                a.px(x + i, y + j, light)
    a.noise(x, y, w, h, 0.05)


def glaze(a, x, y, w, band, c, c_l, c_d, shift=0, sprinkle=True):
    """Глазурь сверху куска: полоса высотой `band` и потёки под ней по два пикселя шириной, блик
    слева, тёмная кромка под каплей. Потёки идут парами колонок, период 24: кусок шириной 24, 48
    или 96 сходится по шву, у прочих ширин шов прячется сзади."""
    a.rect(x, y, w, band, c)
    a.rect(x, y, w, 1, c_l)
    for i in range(w):
        drop = DRIPS[((i + shift) // 2) % len(DRIPS)]
        for j in range(drop):
            a.px(x + i, y + band + j, c_l if (i + shift) % 2 == 0 and j < drop - 1 else c)
        a.px(x + i, y + band + drop, c_d)
    if sprinkle:
        for k, i in enumerate(range(1, w - 1, 3)):
            a.px(x + i, y + 1 + (k * 2) % max(band - 1, 1), SPRINKLES[k % len(SPRINKLES)])


def beads(a, x, y, w, c=ICING, c_d=ICING_D, step=4):
    """Бортик из крема: ряд горошин в три пикселя с тенью снизу и просветом между ними."""
    for i in range(w):
        k = i % step
        if k < step - 1:
            a.px(x + i, y + 1, c), a.px(x + i, y + 2, c_d)
            if k == (step - 1) // 2 or step > 4:
                a.px(x + i, y, c)


def paint_cookie(a, x0, y0, chip):
    """Колесо 16×16 лицом. Печенье-сэндвич героя: тиснёный кружок с зубчатым краем, дырочками и
    кремом в середине. Печенье соперника: румяное, с шоколадной крошкой. Углы залиты краем, чтобы
    крышка колеса не дала прозрачных уголков."""
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            ang = math.atan2(j - 7.5, i - 7.5)
            if chip:
                c = BREAD_L if d < 6.2 else BREAD
                if d > 7.2:
                    c = BREAD_D
            else:
                tooth = int((ang + math.pi) * 8 / math.pi) % 2 == 0
                c = CHOCO
                if d > 6.3:
                    c = CHOCO_D if tooth else CHOCO
                elif 4.2 < d < 5.2:
                    c = CHOCO_L
                elif d < 2.4:
                    c = ICING if d < 1.7 else ICING_D
            a.px(x0 + i, y0 + j, c)
    if chip:
        for cx, cy in ((4, 4), (10, 3), (12, 8), (9, 12), (4, 10), (7, 7)):
            a.rect(x0 + cx, y0 + cy, 2, 2, CHOCO_D)
            a.px(x0 + cx, y0 + cy, CHOCO_L)
        a.px(x0 + 2, y0 + 7, BREAD_D), a.px(x0 + 12, y0 + 12, BREAD_D), a.px(x0 + 7, y0 + 2, BREAD_D)
    else:
        for k in range(8):
            ang = math.pi * k / 4.0 + 0.4
            a.px(x0 + int(round(7.5 + 3.3 * math.cos(ang))), y0 + int(round(7.5 + 3.3 * math.sin(ang))), CHOCO_D)
    a.noise(x0, y0, 16, 16, 0.05)
    return a.region(x0, y0, 16, 16)


def paint_cherry(a, x, y):
    """Вишенка 8×8: красный мармелад, блик сверху слева, тень снизу."""
    a.rect(x, y, 8, 8, JELLY)
    a.rect(x, y + 6, 8, 2, JELLY_D)
    a.rect(x + 1, y + 1, 2, 2, JELLY_L), a.px(x + 1, y + 1, ICING)
    a.rect(x + 5, y + 1, 2, 1, JELLY_L)
    return a.region(x, y, 8, 8)


def paint_cream(a, x, y, w, h):
    """Крем витками: белая лента с косой тенью между витками."""
    for j in range(h):
        for i in range(w):
            k = (i + j * 2) % 6
            a.px(x + i, y + j, ICING_D if k == 0 else (mul(ICING, 0.95) if k == 1 else ICING))
    a.shade(x, y, w, h, 1.03, 0.9, 1.0)
    return a.region(x, y, w, h)


def along_z(rings, region, n=6, caps=(None, None)):
    """Тело вращения вдоль Z: кольца `(z, rx, ry)` спереди назад. Середина куска ложится на верх
    тела, шов снизу; первая крышка смотрит вперёд (−Z), вторая назад."""
    return rot(loft([(z, rx, ry) for z, rx, ry in rings], region, n, 0.0, caps), rx=90.0)


def sweets_cannon():
    """Пушка с попкорном: красно-белый полосатый ствол с карамельными обручами и раструбом, из
    дула лезет попкорн; лафет это полосатая коробка от попкорна с золотым ярлыком, сзади горка
    попкорна, колёса из печенья с крошкой."""
    a = Atlas(64, 32, 419)
    # Ствол: полосы вдоль, карамельные обручи у казённика и по краю раструба.
    for i in range(32):
        k = i % 8
        a.rect(i, 0, 1, 16, JELLY if k < 4 else ICING)
        if k == 0:
            a.rect(i, 0, 1, 16, JELLY_L)
        elif k == 3:
            a.rect(i, 0, 1, 16, JELLY_D)
        elif k == 7:
            a.rect(i, 0, 1, 16, ICING_D)
    for y0, hh in ((0, 3), (13, 3)):
        a.rect(0, y0, 32, hh, CARAMEL)
        a.rect(0, y0, 32, 1, CARAMEL_L), a.rect(0, y0 + hh - 1, 32, 1, CARAMEL_D)
    a.rect(0, 9, 32, 1, CARAMEL_D), a.rect(0, 8, 32, 1, CARAMEL)
    for x in range(1, 32, 4):
        a.px(x, 14, CHOCO), a.px(x + 2, 1, CHOCO)
    a.shade(0, 0, 32, 16, 1.0, 1.0, 0.66)
    a.noise(0, 0, 32, 16, 0.05)
    barrel = a.region(0, 0, 32, 16)
    # Срез дула: карамельная кромка, тёмное нутро, зёрна попкорна.
    a.rect(32, 0, 8, 8, CARAMEL_D)
    a.rect(33, 1, 6, 6, CHOCO_D)
    for x, y, c in ((34, 2, ICING), (36, 2, CARAMEL_L), (35, 4, ICING), (37, 4, ICING), (34, 5, CARAMEL_L), (36, 5, ICING_D)):
        a.px(x, y, c)
    lens = a.region(32, 0, 8, 8)
    # Попкорн: кремовые хлопья, жёлтые бока, тёмные щели между зёрнами.
    a.rect(32, 16, 16, 12, ICING)
    for j in range(12):
        for i in range(16):
            k = (i * 5 + j * 7 + (i // 3) * (j // 3)) % 9
            if k == 0:
                a.px(32 + i, 16 + j, CARAMEL_D)
            elif k in (1, 2):
                a.px(32 + i, 16 + j, CARAMEL_L)
            elif k == 3:
                a.px(32 + i, 16 + j, CARAMEL)
    for x, y in ((34, 18), (39, 21), (44, 17), (36, 25), (42, 25), (46, 22)):
        a.px(x, y, CHOCO)
    a.noise(32, 16, 16, 12, 0.04)
    pop = a.region(32, 16, 16, 12)
    # Коробка: вертикальные красные и белые полосы, зубчатый верх, по бокам золотой ярлык.
    for i in range(32):
        a.rect(i, 16, 1, 12, JELLY if i % 4 < 2 else ICING)
    a.rect(0, 16, 32, 1, CARAMEL_L)
    for i in range(32):
        if i % 4 >= 2:
            a.px(i, 17, CARAMEL)
    a.rect(0, 27, 32, 1, JELLY_D)
    for x0 in (1, 17):
        a.rect(x0 + 1, 20, 4, 5, CARAMEL), a.rect(x0, 21, 6, 3, CARAMEL)
        a.rect(x0 + 1, 24, 4, 1, CARAMEL_D)
        a.rect(x0 + 2, 21, 2, 3, JELLY), a.px(x0 + 2, 21, JELLY_L)
    a.shade(0, 16, 32, 12, 1.06, 0.84, 0.9)
    a.noise(0, 16, 32, 12, 0.04)
    body = a.region(0, 16, 32, 12)
    disc = paint_cookie(a, 40, 0, True)
    a.rect(56, 0, 8, 4, BREAD)
    a.rect(56, 0, 8, 1, BREAD_L), a.rect(56, 3, 8, 1, BREAD_D)
    a.px(58, 1, CHOCO_D), a.px(62, 2, CHOCO_D)
    rim = a.region(56, 0, 8, 4)
    m = Model("cannon", a)
    side = lambda x: at(rot(loft([(-0.04, 0.24, 0.24), (0.04, 0.24, 0.24)], rim, 8, caps=(disc, disc), flat=True), rz=90.0),
                        x, 0.24, 0.2)
    turn = lambda tris: at(rot(tris, rx=-90.0), 0.0, 0.52, -0.1)
    return m.part("body", (0.0, 0.0, 0.0),
                  turn(loft([(-0.5, 0.16, 0.16), (-0.42, 0.2, 0.2), (-0.28, 0.15, 0.15), (0.3, 0.12, 0.12),
                             (0.44, 0.19, 0.19), (0.5, 0.21, 0.21)], barrel, 8, caps=(lens, lens)))
                  + turn(loft([(0.47, 0.18, 0.18), (0.53, 0.13, 0.13), (0.56, 0.05, 0.05)], pop, 6, caps=(None, pop)))
                  + at(box((0.46, 0.22, 0.85), body, pop, None, (1.0, 1.0)), 0.0, 0.3, 0.1)
                  + at(box((0.3, 0.2, 0.3), body, body, None, (0.8, 0.8)), 0.0, 0.1, 0.1)
                  + at(loft([(0.0, 0.15, 0.15), (0.09, 0.11, 0.11), (0.14, 0.04, 0.04)], pop, 5, caps=(None, pop)), 0.0, 0.41, 0.36)
                  + side(-0.28) + side(0.28))


def sweets_palm():
    """Дерево сахарной ваты: изогнутый ствол из вафельной трубочки и розовое облако ваты на
    макушке. Облако это два клуба и девять клочьев по кругу; клок это плоскость с вырезом по
    прозрачности, как лист пальмы: `ThreedScreen.add_palm` кладёт на свои ленты ту же правую
    половину атласа, а клубы берут из неё сплошную середину."""
    a = Atlas(32, 32, 421)
    # Ствол: вафельная трубочка, витки наискось, вдоль витка светлое ребро, шов сходится.
    for j in range(32):
        for i in range(16):
            k = (i + j) % 8
            c = CARAMEL
            if k == 0:
                c = CARAMEL_D
            elif k == 1:
                c = CARAMEL_L
            elif (i - j) % 4 == 0:
                c = mul(CARAMEL, 0.9)
            a.px(i, j, c)
    for y in range(3, 32, 9):
        a.rect(0, y, 16, 1, BREAD)
    a.rect(0, 29, 16, 3, BREAD), a.rect(0, 29, 16, 1, BREAD_D)
    a.shade(0, 0, 16, 32, 1.0, 0.92, 0.68)
    a.noise(0, 0, 16, 32, 0.06)
    trunk = a.region(0, 0, 16, 32)
    # Клок ваты: пухлая лента с волнистым краем и круглым концом, сверху светлее, завитки
    # волокон, по краю тёмно-розовая кромка.
    for y in range(32):
        half = 2.0 + 5.4 * min(1.0, y / 4.0) + 0.75 * math.sin(y * 1.15)
        if y > 25:
            half *= math.sqrt(max(0.0, 1.0 - ((y - 25) / 6.6) ** 2))
        for x in range(16):
            dx = abs(x - 7.5)
            if dx <= half:
                swirl = math.sin(x * 0.95 + y * 0.6 + 1.3 * math.sin(y * 0.45))
                c = PINK
                if swirl > 0.62:
                    c = PINK_L
                elif swirl < -0.8:
                    c = mul(PINK, 0.88)
                if y < 7 and swirl > 0.0:
                    c = PINK_L if swirl < 0.62 else ICING
                if dx > half - 1.1 or y == 31:
                    c = mul(PINK, 0.8) if y > 14 else PINK
                a.px(16 + x, y, c)
    for x, y in ((21, 9), (26, 13), (22, 18), (25, 23), (23, 5)):
        a.px(x, y, ICING)
    a.px(21, 26, PINK_D), a.px(26, 20, PINK_D)
    a.noise(16, 0, 16, 32, 0.04)
    leaf = a.region(16, 0, 16, 32)
    puff = a.region(20, 6, 8, 19)
    top = (0.55, 4.2, 0.1)
    tris = loft([(0.0, 0.24, 0.24), (1.0, 0.18, 0.18, 0.08, 0.0), (2.2, 0.16, 0.16, 0.26, 0.04), (3.3, 0.15, 0.15, 0.44, 0.08),
                 (4.2, 0.17, 0.17, 0.55, 0.1)], trunk, 5)
    tris += loft([(3.4, 0.36, 0.36, top[0], top[2]), (3.72, 0.9, 0.9, top[0], top[2]), (4.15, 1.08, 1.08, top[0], top[2]),
                  (4.56, 0.86, 0.86, top[0], top[2]), (4.82, 0.4, 0.4, top[0], top[2])], puff, 7, 0.2, (None, puff))
    tris += loft([(4.2, 0.3, 0.3, top[0] + 0.5, top[2] - 0.35), (4.5, 0.52, 0.52, top[0] + 0.5, top[2] - 0.35),
                  (4.8, 0.26, 0.26, top[0] + 0.5, top[2] - 0.35)], puff, 6, 0.0, (None, puff))
    for k in range(9):
        ang = 2.0 * math.pi * k / 9.0 + 0.3
        d = (math.sin(ang), 0.0, math.cos(ang))
        q = (math.cos(ang) * 0.62, 0.0, -math.sin(ang) * 0.62)
        droop = 0.72 + 0.16 * (k % 2)
        far = (top[0] + d[0] * 1.14, top[1] - droop, top[2] + d[2] * 1.14)
        mid = (top[0] + d[0] * 0.25, top[1] + 0.56, top[2] + d[2] * 0.25)
        tris += quad((mid[0] - q[0] * 0.55, mid[1], mid[2] - q[2] * 0.55), (mid[0] + q[0] * 0.55, mid[1], mid[2] + q[2] * 0.55),
                     (far[0] + q[0], far[1], far[2] + q[2]), (far[0] - q[0], far[1], far[2] - q[2]), leaf)
    return Model("palm", a).part("body", (0.0, 0.0, 0.0), tris)


def sweets_flag():
    """Флаг-леденец: розово-белая карамельная трость, наверху круглый леденец-спираль, внизу
    печенье; полотно отдельной частью у трости, розовое, с ласточкиным хвостом, белой каймой и
    тем же леденцом на палочке."""
    a = Atlas(64, 32, 423)
    a.rect(0, 0, 32, 20, PINK)
    for y in range(0, 20, 5):
        a.rect(0, y + 2, 32, 1, mul(PINK, 0.9))
    # Кайма глазури фестонами сверху и снизу.
    a.rect(0, 0, 32, 2, ICING), a.rect(0, 18, 32, 2, ICING)
    for x in range(0, 32, 4):
        a.rect(x + 1, 2, 2, 1, ICING), a.rect(x + 1, 17, 2, 1, ICING)
    a.rect(0, 0, 2, 20, ICING_D)
    # Эмблема: леденец-спираль на палочке, шоколадный контур.
    for j in range(20):
        for i in range(32):
            d = math.hypot(i - 12.5, j - 8.5)
            if d < 5.6:
                ang = math.atan2(j - 8.5, i - 12.5)
                c = JELLY if math.sin(ang * 2.0 + d * 1.5) > 0.0 else ICING
                a.px(i, j, CHOCO_D if d > 4.6 else c)
    for k in range(6):
        a.px(16 + k, 12 + (k * 2) // 3, CHOCO_D), a.px(16 + k, 13 + (k * 2) // 3, ICING)
    a.px(11, 6, ICING), a.px(10, 7, ICING)
    # Ласточкин хвост: клин вырезан у свободного края.
    for j in range(20):
        for i in range(32):
            if i >= 24 + abs(j - 9.5) * 0.85:
                a.clear(i, j)
            elif i >= 22.6 + abs(j - 9.5) * 0.85:
                a.px(i, j, PINK_D)
    a.noise(0, 0, 32, 20, 0.05)
    cloth = a.region(0, 0, 32, 20)
    candy(a, 32, 0, 8, 32, PINK, ICING, 8, 1)
    a.shade(32, 0, 8, 32, 1.0, 0.92, 0.62)
    pole = a.region(32, 0, 8, 32)
    # Основание: печенье с крошкой.
    a.rect(40, 0, 8, 8, BREAD_L)
    a.rect(40, 7, 8, 1, BREAD_D), a.rect(40, 0, 8, 1, BREAD)
    for x, y in ((41, 2), (44, 4), (46, 2), (42, 5)):
        a.px(x, y, CHOCO_D)
    base = a.region(40, 0, 8, 8)
    # Леденец наверху: спираль красного и белого от середины, блик.
    for j in range(16):
        for i in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            ang = math.atan2(j - 7.5, i - 7.5)
            c = JELLY if math.sin(ang * 2.0 + d * 1.3) > 0.0 else ICING
            if d > 7.0:
                c = JELLY_D
            a.px(48 + i, j, c)
    a.px(52, 3, ICING), a.px(53, 3, ICING), a.px(52, 4, ICING)
    disc = a.region(48, 0, 16, 16)
    a.rect(40, 8, 8, 4, JELLY)
    for x in range(40, 48, 4):
        a.rect(x, 8, 2, 4, ICING)
    a.rect(40, 11, 8, 1, JELLY_D)
    edge = a.region(40, 8, 8, 4)
    m = Model("flag", a)
    m.part("pole", (0.0, 0.0, 0.0),
           loft([(0.0, 0.05, 0.05), (2.62, 0.04, 0.04)], pole, 4, caps=(None, base))
           + loft([(0.0, 0.26, 0.26), (0.14, 0.18, 0.18)], base, 5, caps=(None, base), flat=True)
           + at(rot(loft([(-0.035, 0.17, 0.17), (0.035, 0.17, 0.17)], edge, 8, caps=(disc, disc), flat=True), rx=90.0),
                0.0, 2.75, 0.0))
    m.part("cloth", (0.04, 2.3, 0.0),
           quad((0.04, 2.62, 0.0), (1.0, 2.56, 0.0), (1.0, 2.02, 0.0), (0.04, 1.98, 0.0), cloth), "pole")
    return m


def sweets_lighthouse():
    """Торт со свечой: ориентир на горизонте высотой с маяк. Три яруса на карамельном блюде:
    шоколадный под белой глазурью, бисквитный под розовой с посыпкой, мятный с белой гирляндой;
    по уступам розетки крема и вишни, наверху полосатая свеча с огоньком."""
    a = Atlas(64, 64, 425)
    # Нижний ярус: шоколадный корж с прослойкой крема, белая глазурь потёками, понизу бортик.
    a.rect(0, 0, 64, 14, CHOCO)
    a.rect(0, 9, 64, 1, CARAMEL_L), a.rect(0, 10, 64, 1, CHOCO_D)
    crumbs(a, 0, 5, 64, 6, 40, CHOCO_D, CHOCO_L)
    glaze(a, 0, 0, 64, 3, ICING, ICING, ICING_D, 0, False)
    for x in range(3, 64, 8):
        a.rect(x, 1, 2, 1, JELLY)
    beads(a, 0, 11, 64, ICING, ICING_D, 4)
    a.shade(0, 0, 64, 14, 1.04, 0.86, 0.72)
    tier1 = a.region(0, 0, 64, 14)
    # Средний ярус: бисквит с малиновой прослойкой, розовая глазурь с посыпкой.
    a.rect(0, 14, 64, 13, CARAMEL)
    a.rect(0, 22, 64, 1, PINK_D), a.rect(0, 23, 64, 1, CARAMEL_L)
    crumbs(a, 0, 19, 64, 5, 36, CARAMEL_D, CARAMEL_L)
    glaze(a, 0, 14, 64, 3, PINK, PINK_L, PINK_D, 5, True)
    beads(a, 0, 24, 64, PINK_L, PINK_D, 4)
    a.shade(0, 14, 64, 13, 1.04, 0.88, 0.72)
    tier2 = a.region(0, 14, 64, 13)
    # Верхний ярус: мятный крем, белая гирлянда дугами, на стыках дуг красные драже.
    a.rect(0, 27, 64, 13, MINT)
    a.rect(0, 27, 64, 2, ICING), a.rect(0, 29, 64, 1, MINT_L)
    for i in range(64):
        sag = int(round(3.2 * math.sin(math.pi * (i % 8) / 8.0)))
        a.px(i, 31 + sag, ICING), a.px(i, 32 + sag, MINT_D)
        if i % 8 == 0:
            a.rect(i, 30, 2, 2, JELLY), a.px(i, 30, JELLY_L)
    beads(a, 0, 37, 64, ICING, MINT_D, 4)
    a.shade(0, 27, 64, 13, 1.04, 0.9, 0.72)
    tier3 = a.region(0, 27, 64, 13)
    # Верх ярусов: глазурь с посыпкой.
    tops = []
    for k, (c, c_d) in enumerate(((ICING, ICING_D), (PINK, PINK_D), (MINT_L, MINT))):
        x0 = k * 16
        a.rect(x0, 40, 16, 8, c)
        for n in range(9):
            a.px(x0 + (n * 7 + 2) % 16, 40 + (n * 3 + 1) % 8, SPRINKLES[(n + k) % len(SPRINKLES)] if k else c_d)
        a.noise(x0, 40, 16, 8, 0.03)
        tops.append(a.region(x0, 40, 16, 8))
    # Блюдо: карамель с кружевной белой каймой по краю.
    a.rect(48, 40, 16, 8, CARAMEL)
    a.rect(48, 40, 16, 1, CARAMEL_L), a.rect(48, 44, 16, 1, CARAMEL_D)
    for x in range(48, 64, 2):
        a.px(x, 41, ICING), a.px(x + 1, 42, ICING)
    a.rect(48, 47, 16, 1, CARAMEL_D)
    a.shade(48, 40, 16, 8, 1.05, 0.8, 0.85)
    plate = a.region(48, 40, 16, 8)
    # Огонёк: капля с прозрачным фоном, красный край, карамельная середина, белое ядро.
    for j in range(16):
        for i in range(16):
            t = j / 15.0
            half = 5.6 * math.sin(math.pi * t ** 1.7) ** 0.8 if 0.0 < t < 1.0 else 0.0
            dx = abs(i - 7.5)
            if dx <= half and half > 0.4:
                c = JELLY_L
                if dx < half - 1.3 and j > 4:
                    c = CARAMEL
                if dx < half - 3.0 and j > 8:
                    c = ICING
                a.px(i, 48 + j, c)
    flame = a.region(0, 48, 16, 16)
    # Свеча: красные и белые витки, наверху оплыв воска.
    candy(a, 16, 48, 8, 16, JELLY, ICING, 8, 1)
    a.rect(16, 48, 8, 1, ICING), a.px(18, 49, ICING), a.px(22, 49, ICING), a.px(22, 50, ICING)
    a.shade(16, 48, 8, 16, 1.0, 0.92, 0.68)
    candle = a.region(16, 48, 8, 16)
    cream = paint_cream(a, 24, 48, 16, 8)
    cherry = paint_cherry(a, 40, 48)
    a.rect(48, 48, 8, 8, ICING)
    a.rect(50, 50, 4, 4, CHOCO_D), a.rect(51, 51, 2, 2, BLACK)
    wick = a.region(48, 48, 8, 8)
    tris = (loft([(0.0, 1.0, 1.0), (0.42, 0.45, 0.45), (0.64, 1.44, 1.44), (0.8, 1.44, 1.44)], plate, 8, caps=(None, plate))
            + loft([(0.8, 1.32, 1.32), (3.3, 1.32, 1.32)], tier1, 8, caps=(None, tops[0]))
            + loft([(3.3, 0.94, 0.94), (5.2, 0.94, 0.94)], tier2, 8, caps=(None, tops[1]))
            + loft([(5.2, 0.62, 0.62), (6.6, 0.62, 0.62)], tier3, 8, caps=(None, tops[2]))
            + loft([(6.6, 0.2, 0.2), (8.2, 0.2, 0.2)], candle, 6, caps=(None, wick)))
    for k in range(8):
        ang = math.pi / 8.0 + math.pi / 4.0 * k
        tris += at(loft([(3.3, 0.2, 0.2), (3.64, 0.04, 0.04)], cream, 4, ang),
                   math.sin(ang) * 1.1, 0.0, math.cos(ang) * 1.1)
    for k in range(5):
        ang = 0.3 + 2.0 * math.pi * k / 5.0
        tris += at(loft([(5.2, 0.14, 0.14), (5.42, 0.09, 0.09)], cherry, 4, ang, (None, cherry)),
                   math.sin(ang) * 0.76, 0.0, math.cos(ang) * 0.76)
    for ang in (0.5, 0.5 + math.pi / 2.0):
        d = (math.sin(ang) * 0.42, math.cos(ang) * 0.42)
        tris += quad((-d[0], 9.0, -d[1]), (d[0], 9.0, d[1]), (d[0], 8.12, d[1]), (-d[0], 8.12, -d[1]), flame)
    return Model("lighthouse", a).part("body", (0.0, 0.0, 0.0), tris)


def make_cart(name, rival):
    """Транспорт гонок. Герой: эклер под розовой глазурью с потёками и посыпкой лежит на вафельном
    подносе, на спине розетки крема с вишней; колёса из шоколадного печенья-сэндвича. Соперник: кекс
    в красной гофрированной формочке под шапкой крема с вишней, колёса из печенья с крошкой.
    Паруса и мачты нет (паруса только у пиратов): у обоих спереди бампер-палочка, на корме
    низкий спойлер: у героя вафельный под глазурью, у соперника плитка шоколада и фары-леденцы. Части и точки вращения как у пиратской повозки: `body`,
    `axle_f`, `axle_r`."""
    a = Atlas(64, 64, 427 if not rival else 429)
    if rival:
        # Формочка: гофры красного мармелада, белая кромка, понизу тень.
        for i in range(32):
            k = i % 4
            a.rect(i, 0, 1, 16, JELLY_D if k == 0 else (JELLY_L if k == 2 else JELLY))
        a.rect(0, 0, 32, 2, ICING), a.rect(0, 2, 32, 1, ICING_D)
        for i in range(0, 32, 4):
            a.px(i, 1, ICING_D)
        a.shade(0, 0, 32, 16, 1.05, 0.72, 0.85)
        a.noise(0, 0, 32, 16, 0.04)
        skin = a.region(0, 0, 32, 16)
        # Шапка крема: витки наискось, розовая посыпка.
        for j in range(16):
            for i in range(32):
                k = (i + j * 2) % 8
                a.px(i, 16 + j, ICING_D if k == 0 else (mul(ICING, 0.94) if k == 1 else ICING))
        for n in range(14):
            a.px((n * 7 + 3) % 32, 17 + (n * 5) % 14, (PINK, MINT, JELLY, CARAMEL)[n % 4])
        a.rect(0, 30, 32, 2, ICING_D)
        a.shade(0, 16, 32, 16, 1.04, 0.9, 0.85)
        frost = a.region(0, 16, 32, 16)
    else:
        # Эклер: 32 пикселя вокруг (середина это верх), 32 вдоль. Сверху розовая глазурь, от неё
        # потёки на румяные бока заварного теста, по низу тень.
        a.rect(0, 0, 32, 32, CARAMEL)
        for j in range(32):
            for i in range(32):
                side = abs(i - 15.5)
                drip = DRIPS[(j // 2) % len(DRIPS)] * 0.7
                if side < 6.0 + drip:
                    c = PINK
                    if side > 4.8 + drip:
                        c = PINK_D
                    elif 1.0 < side < 2.6:
                        c = PINK_L
                elif side > 13.0:
                    c = BREAD
                elif (i * 3 + j * 5) % 13 == 0:
                    c = CARAMEL_D
                elif (i + j * 3) % 11 == 0:
                    c = CARAMEL_L
                else:
                    c = CARAMEL
                a.px(i, j, c)
        for n in range(22):
            x, y = 11 + (n * 5) % 10, (n * 7 + 2) % 32
            if a.get(x, y)[:3] in (PINK, PINK_L):
                a.px(x, y, SPRINKLES[n % len(SPRINKLES)])
        # Поперечные трещинки теста на боках.
        for y in (5, 13, 20, 27):
            a.rect(2, y, 5, 1, BREAD), a.rect(25, y + 2, 5, 1, BREAD)
        a.noise(0, 0, 32, 32, 0.05)
        skin = a.region(0, 0, 32, 32)
        frost = None
    # Поднос: вафля с бороздами, торец темнее.
    waffle(a, 32, 0, 32, 8, 4)
    a.rect(32, 0, 32, 1, CARAMEL_L), a.rect(32, 7, 32, 1, BREAD)
    tray = a.region(32, 0, 32, 8)
    waffle(a, 32, 8, 16, 16, 4)
    deck = a.region(32, 8, 16, 16)
    wheel = paint_cookie(a, 48, 8, rival)
    if rival:
        a.rect(32, 24, 8, 4, BREAD)
        a.rect(32, 24, 8, 1, BREAD_L), a.rect(32, 27, 8, 1, BREAD_D)
        a.px(34, 25, CHOCO_D), a.px(38, 26, CHOCO_D)
    else:
        # Обод сэндвича: два шоколадных печенья и крем между ними.
        a.rect(32, 24, 8, 4, CHOCO)
        a.rect(32, 25, 8, 2, ICING)
        for x in range(32, 40, 2):
            a.px(x, 24, CHOCO_D), a.px(x, 27, CHOCO_D)
    rim = a.region(32, 24, 8, 4)
    cream = paint_cream(a, 40, 24, 8, 8)
    cherry = paint_cherry(a, 48, 24)
    a.rect(56, 24, 8, 8, BREAD_L if not rival else ICING)
    a.rect(58, 26, 4, 4, CARAMEL if not rival else PINK)
    cap = a.region(56, 24, 8, 8)
    if rival:
        # Бампер и стойки спойлера: вафельная палочка.
        for j in range(32):
            for i in range(8):
                a.px(32 + i, 32 + j, CARAMEL_D if (i + j) % 4 == 0 else (CARAMEL_L if (i + j) % 4 == 1 else CARAMEL))
        # Спойлер: плитка шоколада плашмя, дольки с фаской; ниже полоска торца плитки.
        a.rect(0, 32, 32, 14, CHOCO)
        for j in range(2):
            for i in range(4):
                x0, y0 = i * 8, 32 + j * 7
                a.rect(x0, y0, 8, 1, CHOCO_L), a.rect(x0, y0, 1, 7, CHOCO_L)
                a.rect(x0 + 7, y0, 1, 7, CHOCO_D), a.rect(x0, y0 + 6, 8, 1, CHOCO_D)
                a.rect(x0 + 2, y0 + 2, 4, 3, mul(CHOCO, 1.12))
                a.px(x0 + 2, y0 + 2, CHOCO_L)
        a.rect(0, 46, 32, 4, CHOCO)
        a.rect(0, 46, 32, 1, CHOCO_L), a.rect(0, 49, 32, 1, CHOCO_D)
        # Фара: лимонный леденец с бликом.
        a.rect(56, 24, 8, 8, CARAMEL_L)
        a.rect(56, 24, 8, 1, CARAMEL), a.rect(56, 31, 8, 1, CARAMEL_D)
        a.rect(58, 26, 3, 3, ICING)
    else:
        # Бампер и стойки спойлера: карамельная трость.
        candy(a, 32, 32, 8, 32, JELLY, ICING, 8, 1)
        # Спойлер: вафельная пластина, вдоль неё полоса розовой глазури с посыпкой; ниже торец.
        waffle(a, 0, 32, 32, 14, 4)
        a.rect(0, 36, 32, 6, PINK)
        a.rect(0, 36, 32, 1, PINK_L), a.rect(0, 41, 32, 1, PINK_D)
        for n in range(10):
            a.px(1 + n * 3, 37 + (n * 2) % 4, SPRINKLES[n % len(SPRINKLES)])
        a.rect(0, 46, 32, 4, CARAMEL)
        a.rect(0, 46, 32, 1, CARAMEL_L), a.rect(0, 49, 32, 1, BREAD)
    a.noise(0, 32, 32, 18, 0.04)
    wing = a.region(0, 32, 32, 14)
    wing_edge = a.region(0, 46, 32, 4)
    stick = a.region(32, 32, 8, 32)
    m = Model(name, a)
    body = at(box((1.08, 0.1, 2.0), tray, deck, deck), 0.0, 0.4, -0.1)
    if rival:
        body += (loft([(0.42, 0.42, 0.8), (0.86, 0.6, 1.02)], skin, 8)
                 + loft([(0.86, 0.64, 1.06), (1.0, 0.58, 0.96), (1.14, 0.4, 0.68), (1.28, 0.16, 0.28)], frost, 8, caps=(frost, frost))
                 + at(loft([(0.0, 0.11, 0.11), (0.16, 0.07, 0.07)], cherry, 4, 0.0, (None, cherry)), 0.0, 1.2, 0.3))
        wing_y, wing_z, post_y, post_x, lamp_z = 1.2, 0.84, 0.9, 0.26, -0.98
    else:
        body += (at(along_z([(-1.42, 0.14, 0.1), (-1.24, 0.38, 0.23), (-0.8, 0.5, 0.3), (0.55, 0.5, 0.3), (0.86, 0.38, 0.23),
                             (0.98, 0.14, 0.1)], skin, 8, (cap, cap)), 0.0, 0.72)
                 + at(loft([(0.0, 0.17, 0.17), (0.12, 0.12, 0.12), (0.24, 0.03, 0.03)], cream, 4), 0.0, 0.99, 0.2)
                 + at(loft([(0.0, 0.17, 0.17), (0.1, 0.13, 0.13)], cream, 4, 0.0, (None, cream)), 0.0, 0.98, 0.55)
                 + at(loft([(0.0, 0.1, 0.1), (0.14, 0.06, 0.06)], cherry, 4, 0.0, (None, cherry)), 0.0, 1.07, 0.55))
        wing_y, wing_z, post_y, post_x, lamp_z = 1.12, 0.86, 0.8, 0.24, -1.0
    # Вместо паруса и мачты мелкие детали машины: передний бампер-палочка поперёк подноса, две
    # фары на его углах, на корме низкий спойлер на двух стойках.
    body += at(rot(loft([(-0.6, 0.06, 0.06), (0.6, 0.06, 0.06)], stick, 4, caps=(cap, cap), flat=True), rz=90.0),
               0.0, 0.42, -1.15)
    body += at(box((1.04, 0.05, 0.3), wing_edge, wing, wing_edge), 0.0, wing_y, wing_z)
    for x in (-post_x, post_x):
        body += quad((x, wing_y, wing_z - 0.05), (x, wing_y, wing_z + 0.05), (x, post_y, wing_z + 0.05),
                     (x, post_y, wing_z - 0.05), stick)
    # Фары только у кекса: у эклера угол подноса закрыт носом, и запас граней там вышел.
    for x in ((-0.4, 0.4) if rival else ()):
        body += at(loft([(0.0, 0.11, 0.11), (0.12, 0.08, 0.08)], cap, 4, math.pi / 4.0, (None, cap), True), x, 0.45, lamp_z)
    m.part("body", (0.0, 0.0, 0.0), body)
    for part, z in (("axle_f", -0.72), ("axle_r", 0.72)):
        tris = []
        for x in (-0.6, 0.6):
            tris += at(rot(loft([(-0.07, 0.32, 0.32), (0.07, 0.32, 0.32)], rim, 8, caps=(wheel, wheel), flat=True), rz=90.0),
                       x, 0.32, z)
        m.part(part, (0.0, 0.32, z), tris, "body")
    return m


def sweets_cart():
    return make_cart("cart", False)


def sweets_cart_rival():
    return make_cart("cart_rival", True)


def sweets_pistol():
    """Кондитерский шприц в пряничной варежке: оружие вида от первого лица, насадка смотрит в −Z,
    ноль в рукояти. Колба с розовым кремом и делениями, белые кольца, золотая ребристая насадка
    с каплей крема, сзади упор и шток с пяткой; рука пряничная, у запястья кайма глазури."""
    a = Atlas(32, 32, 431)
    # Колба 16 вокруг (середина это верх) на 8 вдоль (низ куска это перёд): крем, блик по верху,
    # деления сбоку, кольца спереди и сзади, у штока пустое стекло.
    a.rect(0, 0, 16, 8, PINK)
    a.rect(0, 1, 16, 1, MINT_L), a.rect(0, 2, 16, 1, PINK_L)
    a.rect(7, 2, 2, 5, PINK_L), a.rect(7, 1, 2, 1, ICING)
    for y in (3, 5):
        a.rect(11, y, 2, 1, BLACK), a.rect(3, y, 1, 1, PINK_D)
    a.rect(0, 0, 16, 1, ICING), a.rect(0, 7, 16, 1, ICING)
    a.rect(0, 6, 16, 1, ICING_D)
    a.rect(0, 2, 2, 5, PINK_D), a.rect(14, 2, 2, 5, PINK_D)
    a.noise(0, 0, 16, 8, 0.04)
    tube = a.region(0, 0, 16, 8)
    # Насадка: золотой конус, рёбра через пиксель.
    for i in range(8):
        a.rect(16 + i, 0, 1, 8, CARAMEL_D if i % 2 else CARAMEL)
    a.rect(19, 0, 2, 8, CARAMEL_L)
    a.rect(16, 0, 8, 1, CARAMEL_D), a.rect(16, 6, 8, 2, ICING)
    nozzle = a.region(16, 0, 8, 8)
    a.rect(24, 0, 4, 4, ICING)
    a.px(25, 1, PINK_L)
    drop = a.region(24, 0, 4, 4)
    # Упор и пятка штока: белый диск с тенью по краю и розовой серединой.
    a.rect(24, 4, 8, 4, ICING)
    a.rect(24, 7, 8, 1, ICING_D), a.rect(27, 5, 2, 2, PINK)
    flange = a.region(24, 4, 8, 4)
    # Рукоять и шток: малиновый пластик с насечкой и бликом.
    a.rect(0, 8, 16, 8, PINK_D)
    a.rect(0, 8, 16, 1, PINK)
    for x in range(1, 16, 3):
        a.rect(x, 10, 1, 5, mul(PINK_D, 0.7))
        a.px(x + 1, 10, PINK)
    a.noise(0, 8, 16, 8, 0.05)
    grip = a.region(0, 8, 16, 8)
    # Варежка: пряник в крошках, бороздки пальцев, понизу тень.
    a.rect(0, 16, 16, 8, BREAD)
    a.rect(0, 16, 16, 1, BREAD_L)
    crumbs(a, 0, 17, 16, 6, 14, BREAD_D, BREAD_L)
    for x in (3, 7, 11):
        a.rect(x, 16, 1, 4, BREAD_D)
    a.rect(0, 23, 16, 1, BREAD_D)
    a.shade(0, 16, 16, 8, 1.06, 0.86, 0.82)
    a.noise(0, 16, 16, 8, 0.04)
    hand = a.region(0, 16, 16, 8)
    # Рука: пряник, у запястья (низ куска) волнистая кайма глазури, как у героя.
    a.rect(16, 8, 16, 16, BREAD)
    crumbs(a, 16, 8, 16, 16, 30, BREAD_D, BREAD_L)
    for i in range(16):
        a.px(16 + i, 20, ICING), a.px(16 + i, 22, BREAD_D)
        if i % 4 < 2:
            a.px(16 + i, 19, ICING)
        else:
            a.px(16 + i, 21, ICING)
    a.shade(16, 8, 16, 16, 0.86, 1.04, 0.76)
    a.noise(16, 8, 16, 16, 0.05)
    sleeve = a.region(16, 8, 16, 16)
    return Model("pistol", a).part("body", (0.0, 0.0, 0.0),
                                   at(along_z([(-0.3, 0.04, 0.04), (-0.02, 0.04, 0.04)], tube, 6, (flange, flange)), 0.0, 0.06)
                                   + at(along_z([(-0.39, 0.009, 0.009), (-0.3, 0.036, 0.036)], nozzle, 6, (drop, None)), 0.0, 0.06)
                                   + at(along_z([(-0.035, 0.064, 0.064), (-0.012, 0.064, 0.064)], flange, 6, (flange, flange)), 0.0, 0.06)
                                   + at(along_z([(-0.012, 0.013, 0.013), (0.075, 0.013, 0.013)], grip, 4), 0.0, 0.06)
                                   + at(along_z([(0.075, 0.04, 0.04), (0.092, 0.04, 0.04)], flange, 6, (flange, flange)), 0.0, 0.06)
                                   + at(rot(box((0.045, 0.15, 0.06), grip, grip, grip), rx=-20.0), 0.0, -0.05, 0.03)
                                   + at(box((0.09, 0.1, 0.1), hand, hand, hand, (0.8, 0.85)), 0.0, -0.04, 0.03)
                                   + at(box((0.035, 0.06, 0.05), hand, hand, hand, (0.8, 0.8)), -0.05, -0.02, 0.01)
                                   + at(rot(loft([(0.0, 0.045, 0.045), (0.5, 0.06, 0.06)], sleeve, 4, math.pi / 4.0), rx=65.0), 0.0, -0.08, 0.07))


def sweets_hoop():
    """Пончик: цель спорта. Щит это большая вафля с розовой глазурью по верху и белым квадратом
    прицела, кольцо это пончик в розовой глазури с посыпкой, вместо сетки с него стекают потёки
    глазури; стойка карамельной тростью на печенье. Просвет кольца и щит там же и тех же
    размеров, что у пиратов."""
    a = Atlas(64, 64, 433)
    waffle(a, 0, 0, 32, 24, 4)
    glaze(a, 0, 0, 32, 3, PINK, PINK_L, PINK_D, 3, True)
    for x, y, w, h in ((10, 9, 12, 1), (10, 18, 12, 1), (10, 9, 1, 10), (21, 9, 1, 10)):
        a.rect(x, y, w, h, ICING)
    for x, y, w, h in ((11, 19, 12, 1), (22, 10, 1, 10)):
        a.rect(x, y, w, h, CARAMEL_D)
    a.rect(0, 23, 32, 1, BREAD), a.rect(0, 3, 1, 21, BREAD), a.rect(31, 3, 1, 21, BREAD)
    a.rect(2, 20, 2, 2, JELLY), a.px(2, 20, JELLY_L), a.rect(28, 20, 2, 2, MINT), a.px(28, 20, MINT_L)
    board = a.region(0, 0, 32, 24)
    # Глазурь пончика: блик по гребню, посыпка.
    a.rect(32, 0, 32, 4, PINK)
    a.rect(32, 1, 32, 1, PINK_L), a.rect(32, 3, 32, 1, PINK_D)
    for k, x in enumerate(range(33, 64, 3)):
        a.px(x, (k * 2) % 3, SPRINKLES[k % len(SPRINKLES)])
    ring = a.region(32, 0, 32, 4)
    # Тесто пончика: румяный бок, светлый поясок.
    a.rect(32, 4, 32, 4, BREAD_L)
    a.rect(32, 4, 32, 1, CARAMEL_L), a.rect(32, 7, 32, 1, BREAD)
    for x in range(34, 64, 5):
        a.px(x, 6, BREAD)
    dough = a.region(32, 4, 32, 4)
    # Вместо сетки потёки глазури: капли разной длины с бликом и круглым концом, между ними насквозь.
    a.rect(32, 8, 32, 2, PINK)
    for k, x in enumerate(range(0, 32, 4)):
        length = (13, 8, 15, 6, 11, 14, 7, 10)[k]
        for y in range(2, length):
            a.px(32 + x + 1, 8 + y, PINK_L), a.px(32 + x + 2, 8 + y, PINK)
            if y > length - 4:
                a.px(32 + x, 8 + y, PINK), a.px(32 + x + 3, 8 + y, PINK_D)
        a.px(32 + x + 1, 8 + length, PINK_D), a.px(32 + x + 2, 8 + length, PINK_D)
        a.px(32 + x + 1, 8 + length - 2, ICING)
    net = a.region(32, 8, 32, 16)
    candy(a, 0, 24, 8, 32, JELLY, ICING, 8, 1)
    a.shade(0, 24, 8, 32, 1.0, 0.92, 0.62)
    post = a.region(0, 24, 8, 32)
    # Кронштейн: карамель.
    a.rect(8, 24, 8, 8, CARAMEL)
    a.rect(8, 24, 8, 1, CARAMEL_L), a.rect(8, 31, 8, 1, CARAMEL_D)
    a.px(10, 27, CARAMEL_D), a.px(13, 27, CARAMEL_D)
    arm = a.region(8, 24, 8, 8)
    # Основание: печенье с крошкой.
    a.rect(8, 32, 8, 8, BREAD_L)
    a.rect(8, 32, 8, 1, BREAD), a.rect(8, 39, 8, 1, BREAD_D)
    for x, y in ((9, 34), (12, 36), (14, 34), (10, 37)):
        a.px(x, y, CHOCO_D)
    cookie = a.region(8, 32, 8, 8)
    rim_y, rim_z = 3.05, -0.42
    # Пончик: тор из десяти долек, сечение шестиугольником; верхние грани в глазури, остальные из
    # теста. Просвет как у пиратского кольца, наружный край упирается в щит.
    section = ((0.192, -0.02), (0.2275, 0.01), (0.268, -0.02), (0.268, -0.09), (0.2275, -0.12), (0.192, -0.09))
    ring_tris = []
    seg = 10
    for k in range(seg):
        a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
        p = lambda s, t: (s[0] * math.sin(t), rim_y + s[1], rim_z + s[0] * math.cos(t))
        for f in range(6):
            s0, s1 = section[f], section[(f + 1) % 6]
            src = ring if f < 2 else dough
            u0, v0, u1, v1 = src
            part = (u0 + (u1 - u0) * k / seg, v0, u0 + (u1 - u0) * (k + 1) / seg, v1)
            ring_tris += quad(p(s0, a0), p(s0, a1), p(s1, a1), p(s1, a0), part, False)
    basket = at(loft([(rim_y - 0.46, 0.13, 0.13), (rim_y - 0.04, 0.2, 0.2)], net, 8), 0.0, 0.0, rim_z)
    faces = []
    u0, v0, u1, v1 = board
    for z, mirror in ((-0.15, 1.0), (-0.09, -1.0)):
        for ix in range(2):
            for iy in range(2):
                xa, xb = 0.65 - 0.65 * ix, 0.65 - 0.65 * (ix + 1)
                ya, yb = 3.875 - 0.475 * iy, 3.875 - 0.475 * (iy + 1)
                part = (u0 + (u1 - u0) * ix / 2.0, v0 + (v1 - v0) * iy / 2.0, u0 + (u1 - u0) * (ix + 1) / 2.0, v0 + (v1 - v0) * (iy + 1) / 2.0)
                faces += quad((xa * mirror, ya, z), (xb * mirror, ya, z), (xb * mirror, yb, z), (xa * mirror, yb, z), part, False)
    edge = (u0, v0 + (v1 - v0) / 4.0, u0 + (u1 - u0) / 16.0, v1)
    for x in (-0.65, 0.65):
        faces += quad((x, 3.875, -0.15), (x, 3.875, -0.09), (x, 2.925, -0.09), (x, 2.925, -0.15), edge)
    for y in (2.925, 3.875):
        faces += quad((0.65, y, -0.15), (-0.65, y, -0.15), (-0.65, y, -0.09), (0.65, y, -0.09), edge)
    return Model("hoop", a).part("body", (0.0, 0.0, 0.0),
                                 loft([(0.0, 0.09, 0.09), (3.9, 0.07, 0.07)], post, 5)
                                 + loft([(0.0, 0.3, 0.3), (0.12, 0.2, 0.2)], cookie, 5, caps=(None, cookie), flat=True)
                                 + at(box((0.06, 0.06, 0.2), arm, arm, arm), 0.0, rim_y - 0.055, -0.2)
                                 + faces + ring_tris + basket + flip(basket))


MODELS = [sweets_cannon, sweets_palm, sweets_flag, sweets_lighthouse, sweets_cart, sweets_cart_rival, sweets_pistol, sweets_hoop]


if __name__ == "__main__":
    models = [f() for f in MODELS]
    for m in models:
        print("%-11s частей %d, треугольников %3d%s" % (m.name, len(m.parts), m.tris(),
                                                        "  БОЛЬШЕ %d" % lm.MAX_TRIS if m.tris() > lm.MAX_TRIS else ""))
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
