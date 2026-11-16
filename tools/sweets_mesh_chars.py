#!/usr/bin/env python3
"""Персонажи «Сладостей» для low poly и «продвинутых» (#137): пряничный человечек, мармеладный
мишка, шоколадный король. Зеркала `pirate_hero`, `pirate_enemy`, `pirate_captain` из
`lowpoly_meshes.py` и `space_mesh_chars.py`: те же имена частей, родители и точки вращения
(демки анимируют части), рост, взгляд в −Z, ноль в подошвах; у мишки оружие в правой лапе на
месте сабли скелета (вафельная трубочка с кремом, остриём вперёд). Облик и цвета из основы
16/32 (`sweets16.py`): пряник с белой каймой глазури у концов рук и ног, двумя пуговицами-драже
и красным бантиком; литой красный мишка с круглыми ушами, белыми бликами и розовым просветом.
Плотный набор «продвинутых» получается из этих же функций (плотность и размер атласа задаёт
`lowpoly_meshes`), поэтому геометрия собирается его помощниками.

    python3 tools/sweets_mesh_chars.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Цвета из палитры `sweets16.PALETTE`; светлые тона пряника, мармелада и шоколада подобраны к ней.
BREAD, BREAD_D, BREAD_L = rgb("C9803E"), rgb("945228"), rgb("E2A460")
ICING, ICING_D = rgb("FFF7EC"), rgb("D6BFCC")
MINT, MINT_D, MINT_L = rgb("86DBBE"), rgb("3FA99C"), rgb("D3F6E4")
PINK, PINK_D, PINK_L = rgb("FF8EB6"), rgb("B73A70"), rgb("FFC4DA")
JELLY, JELLY_D, JELLY_L = rgb("E63545"), rgb("A42244"), rgb("FF7482")
CARAMEL, CARAMEL_D, CARAMEL_L = rgb("F8CF6A"), rgb("D09038"), rgb("FFE9A8")
CHOCO, CHOCO_D, CHOCO_L = rgb("7C4838"), rgb("4A2826"), rgb("A86C50")
BLACK = rgb("2B161E")


def _crumbs(a, x, y, w, h, n, dark, light):
    """Крошки и поры выпечки: тёмные и светлые точки вразброс."""
    for i in range(n):
        a.px(x + a.rng.randrange(w), y + a.rng.randrange(h), dark if i % 3 else light)


def _wave(a, x, y, w, c=ICING, shadow=None):
    """Кайма глазури: сплошная строка и фестоны под ней через два пикселя, ниже тень."""
    for i in range(w):
        drop = 1 if i % 4 < 2 else 0
        a.px(x + i, y, c)
        if drop:
            a.px(x + i, y + 1, c)
        if shadow is not None:
            a.px(x + i, y + 1 + drop, shadow)


def _dragee(a, x, y, c, c_l, c_d, w=4, h=3):
    """Пуговица-драже: блик сверху слева, тень снизу."""
    a.rect(x, y, w, h, c)
    a.rect(x, y + h - 1, w, 1, c_d)
    a.px(x, y, c_l), a.px(x + 1, y, c_l)


# --- Пряничный человечек -----------------------------------------------------------------------

def sweets_hero():
    """Пряничный человечек: румяный пряник в крошках, большая круглая голова с глазами-изюминами
    и белой улыбкой, волнистая кайма глазури у запястий, щиколоток и по подолу, две пуговицы-драже
    (мятная и розовая), красный бантик под подбородком."""
    a = lm.Atlas(64, 64, 211)
    # Торс 32×20: середина куска это грудь. Пуговицы, кайма у плеч и по подолу, завиток на спине.
    a.rect(0, 0, 32, 20, BREAD)
    _crumbs(a, 0, 0, 32, 20, 46, BREAD_D, BREAD_L)
    a.rect(12, 0, 8, 1, BREAD_D)  # тень под подбородком
    _wave(a, 0, 3, 32, ICING, BREAD_D)
    a.rect(13, 3, 6, 3, BREAD)  # под бантом кайма прервана
    _dragee(a, 14, 7, MINT, MINT_L, MINT_D)
    _dragee(a, 14, 12, PINK, PINK_L, PINK_D, 4, 2)
    for x, y in ((1, 8), (2, 9), (1, 10), (0, 11), (30, 8), (29, 9), (30, 10), (31, 11)):
        a.px(x, y, ICING)  # завиток глазури на спине (шов куска)
    _wave(a, 0, 16, 32, ICING, BREAD_D)
    a.rect(0, 19, 32, 1, BREAD_D)
    a.shade(0, 0, 32, 20, 1.08, 0.86, 0.78)
    a.noise(0, 0, 32, 20, 0.05)
    torso = a.region(0, 0, 32, 20)
    # Голова 32×16: лицо в середине. Чёлка глазурью, глаза-изюмины с бликом, щёки, улыбка.
    a.rect(0, 20, 32, 16, BREAD)
    a.rect(0, 20, 32, 2, BREAD_L)
    _crumbs(a, 0, 22, 32, 14, 30, BREAD_D, BREAD_L)
    _wave(a, 0, 23, 32, ICING, BREAD_D)
    a.rect(10, 22, 12, 4, BREAD)  # лоб над глазами чистый
    for x, y in ((12, 22), (13, 21), (14, 22), (15, 23), (16, 22), (17, 21), (18, 22), (19, 23)):
        a.px(x, y, ICING)  # завиток чёлки
    a.rect(11, 26, 2, 3, BLACK), a.rect(19, 26, 2, 3, BLACK)
    a.px(11, 26, ICING), a.px(19, 26, ICING)
    a.rect(8, 30, 2, 2, PINK), a.rect(22, 30, 2, 2, PINK)
    for x, y in ((12, 30), (13, 31), (14, 31), (15, 31), (16, 31), (17, 31), (18, 31), (19, 30)):
        a.px(x, y, ICING)
    a.rect(0, 35, 32, 1, BREAD_D)
    a.shade(0, 20, 32, 16, 1.1, 0.9, 0.8)
    a.noise(0, 20, 32, 16, 0.04)
    head = a.region(0, 20, 32, 16)
    # Рука 16×16: гладкий пряник, у запястья волна глазури, конец руки круглый, без кисти.
    a.rect(32, 0, 16, 16, BREAD)
    _crumbs(a, 32, 0, 16, 12, 14, BREAD_D, BREAD_L)
    _wave(a, 32, 12, 16, ICING, BREAD_D)
    a.rect(32, 15, 16, 1, BREAD_D)
    a.shade(32, 0, 16, 16, 1.06, 0.9, 0.78)
    a.noise(32, 0, 16, 16, 0.05)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: бедро в крошках, над ступнёй волна глазури, подпечённый низ.
    a.rect(48, 0, 16, 24, BREAD)
    _crumbs(a, 48, 0, 16, 24, 24, BREAD_D, BREAD_L)
    _wave(a, 48, 14, 16, ICING, BREAD_D)
    a.rect(48, 22, 16, 2, BREAD_D)
    a.shade(48, 0, 16, 24, 1.06, 0.86, 0.78)
    a.noise(48, 0, 16, 24, 0.05)
    leg = a.region(48, 0, 16, 24)
    # Бант: крыло 16×8 лентой (складки к узлу), узел 8×8.
    a.rect(32, 16, 16, 8, JELLY)
    a.rect(32, 16, 16, 1, JELLY_L)
    a.rect(32, 23, 16, 1, JELLY_D)
    for x in (34, 38, 42, 46):
        a.rect(x, 18, 1, 4, JELLY_D)
        a.px(x + 1, 18, JELLY_L)
    a.noise(32, 16, 16, 8, 0.05)
    wing = a.region(32, 16, 16, 8)
    a.rect(32, 24, 8, 8, JELLY)
    a.rect(32, 24, 8, 1, JELLY_L), a.rect(32, 31, 8, 1, JELLY_D)
    a.rect(35, 26, 2, 4, JELLY_D), a.px(34, 26, JELLY_L)
    knot = a.region(32, 24, 8, 8)
    # Подошва и конец руки подпечённые, темя светлое.
    a.rect(40, 24, 4, 4, BREAD_D)
    a.px(41, 25, BREAD), a.px(42, 26, BREAD)
    a.rect(44, 24, 4, 4, BREAD_L)
    sole, crown = a.region(40, 24, 4, 4), a.region(44, 24, 4, 4)

    parts = lm.biped(leg, torso, head, arm, sole, crown)
    # Голова пряника: большой шар без шеи, заметно шире плеч космонавта не становится.
    parts["head"][1] = lm.loft([(1.44, 0.07, 0.075), (1.5, 0.14, 0.14), (1.6, 0.175, 0.17), (1.7, 0.165, 0.16),
                                (1.78, 0.11, 0.11), (1.82, 0.045, 0.045)], head, 6, caps=(None, crown))
    # Бантик под подбородком спереди (−Z): два крыла сужаются к узлу, утоплены в грудь.
    bow = lm.at(lm.rot(lm.box((0.11, 0.1, 0.045), wing, knot, knot, (0.35, 0.7)), rz=90.0), 0.055, 1.42, -0.105)
    bow += lm.at(lm.rot(lm.box((0.11, 0.1, 0.045), wing, knot, knot, (0.35, 0.7)), rz=-90.0), -0.055, 1.42, -0.105)
    bow += lm.at(lm.box((0.045, 0.055, 0.055), knot, knot, knot), 0.0, 1.42, -0.11)
    parts["body"][1].extend(bow)
    return lm.assemble("hero", a, parts)


# --- Мармеладный мишка -------------------------------------------------------------------------

def sweets_enemy():
    """Мармеладный мишка: литой красный, тело грушей, круглые уши, розовая морда с чёрным носом,
    хмурые брови, белые блики сверху и розовый просвет снизу; в правой лапе вафельная трубочка
    с шапкой розового крема."""
    a = lm.Atlas(64, 64, 223)
    # Тело 32×20: светлое пузо на груди, литейный шов по бокам, блик, просвет у низа.
    a.rect(0, 0, 32, 20, JELLY)
    for y in range(5, 16):
        half = (3, 4, 5, 5, 6, 6, 6, 5, 5, 4, 3)[y - 5]
        a.rect(16 - half, y, half * 2, 1, JELLY_L)
    a.rect(13, 9, 6, 1, JELLY), a.px(15, 12, JELLY_D), a.px(16, 12, JELLY_D)  # складка и пупок
    for x in (7, 24):
        a.rect(x, 1, 1, 18, JELLY_D)  # шов формы
    for i in range(4):
        a.px(10 + i, 5 - i, ICING), a.px(11 + i, 5 - i, ICING)
    a.px(20, 4, ICING), a.px(3, 6, ICING), a.px(3, 7, ICING), a.px(28, 5, ICING)
    a.rect(12, 0, 8, 2, JELLY_D)  # шея в тени головы
    a.rect(0, 18, 32, 2, JELLY_L)  # просвет желе у низа
    a.rect(0, 19, 32, 1, PINK)
    a.shade(0, 0, 32, 20, 1.08, 0.9, 0.74)
    a.noise(0, 0, 32, 20, 0.04)
    body = a.region(0, 0, 32, 20)
    # Голова 32×16: глаза с блестящим зрачком под хмурыми бровями, морда поверх это отдельный кусок.
    a.rect(0, 20, 32, 16, JELLY)
    a.rect(0, 20, 32, 2, JELLY_L)
    for x0, s in ((10, 1), (21, -1)):
        a.rect(x0 if s > 0 else x0 - 1, 25, 2, 3, BLACK)
        a.px(x0, 25, ICING)
        for k in range(4):
            a.px(x0 - s + k * s, 22 + (k + 1) // 2, BLACK)  # бровь: к переносице ниже
    for x, y in ((5, 22), (6, 22), (5, 23), (6, 24), (25, 23), (26, 22)):
        a.px(x, y, ICING)  # блики литья на висках
    a.px(15, 21, ICING), a.px(16, 21, ICING)
    for x in (0, 1, 30, 31):
        a.rect(x, 23, 1, 10, JELLY_D)  # шов формы на затылке
    a.rect(0, 34, 32, 2, JELLY_L)
    a.shade(0, 20, 32, 16, 1.1, 0.9, 0.78)
    a.noise(0, 20, 32, 16, 0.04)
    head = a.region(0, 20, 32, 16)
    # Лапа 16×16: длинный блик, шов, тёмная подушечка с тремя пальцами внизу.
    a.rect(32, 0, 16, 16, JELLY)
    a.rect(36, 1, 1, 2, ICING), a.px(37, 1, ICING), a.px(36, 7, ICING)
    a.rect(44, 0, 1, 12, JELLY_D)
    a.rect(32, 10, 16, 1, JELLY_L)
    a.rect(32, 12, 16, 4, JELLY_D)
    for x in (35, 39, 43):
        a.rect(x, 13, 1, 3, PINK_D)
    a.rect(32, 15, 16, 1, PINK_D)
    a.shade(32, 0, 16, 16, 1.06, 0.92, 0.76)
    a.noise(32, 0, 16, 16, 0.04)
    limb = a.region(32, 0, 16, 16)
    # Ухо 8×8: красное, спереди розовая серединка.
    a.rect(48, 0, 8, 8, JELLY)
    a.rect(48, 0, 8, 1, JELLY_L)
    a.rect(51, 2, 2, 4, PINK), a.px(51, 6, PINK_D), a.px(52, 6, PINK_D)
    a.rect(48, 7, 8, 1, JELLY_D)
    ear = a.region(48, 0, 8, 8)
    # Морда: бока 8×8 розовые с тенью у щёк, торец 8×8 с чёрным носом и пастью.
    a.rect(56, 0, 8, 8, PINK)
    a.rect(56, 6, 8, 2, PINK_D)
    a.rect(56, 0, 8, 1, PINK_L)
    muzzle = a.region(56, 0, 8, 8)
    a.rect(56, 8, 8, 8, PINK)
    a.rect(58, 12, 4, 2, BLACK), a.px(59, 11, BLACK), a.px(60, 11, BLACK)  # нос (торец перевёрнут)
    a.px(58, 12, ICING)
    a.rect(58, 10, 4, 1, PINK_D)  # пасть
    nose = a.region(56, 8, 8, 8)
    # Вафельная трубочка 8×16: клетка вафли по кругу, подпечённые края.
    a.rect(48, 16, 8, 16, CARAMEL)
    for y in range(16, 32):
        for x in range(48, 56):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                a.px(x, y, CARAMEL_D)
            elif (x + y) % 4 == 1:
                a.px(x, y, CARAMEL_L)
    a.rect(48, 16, 8, 1, CARAMEL_L)
    a.rect(48, 31, 8, 1, CARAMEL_D)
    a.noise(48, 16, 8, 16, 0.05)
    wafer = a.region(48, 16, 8, 16)
    # Крем 8×8: розовые витки с бликом, внизу волна наплыва на вафлю.
    a.rect(56, 16, 8, 8, PINK)
    for y in (17, 20, 23):
        a.rect(56, y, 8, 1, PINK_D)
    for y in (18, 21):
        a.rect(57, y, 3, 1, PINK_L)
    a.px(58, 16, ICING), a.px(59, 16, ICING)
    cream = a.region(56, 16, 8, 8)
    a.rect(56, 24, 4, 4, CHOCO_D)
    a.rect(57, 25, 2, 2, CARAMEL_D)
    a.rect(60, 24, 4, 4, JELLY_D)
    a.rect(56, 28, 4, 4, JELLY_L), a.px(57, 29, ICING)
    hole, chip, crown = a.region(56, 24, 4, 4), a.region(60, 24, 4, 4), a.region(56, 28, 4, 4)

    m = lm.Model("enemy", a)
    for side, x in (("l", -0.09), ("r", 0.09)):
        m.part("leg_" + side, (x, 0.86, 0.0),
               lm.loft([(0.0, 0.085, 0.14, x, -0.04), (0.08, 0.08, 0.095, x, -0.01), (0.9, 0.095, 0.105, x, 0.0)],
                       limb, 5, caps=(chip, None)))
    m.part("body", (0.0, 0.86, 0.0),
           lm.loft([(0.8, 0.2, 0.165), (0.98, 0.235, 0.2), (1.16, 0.225, 0.185), (1.34, 0.185, 0.135),
                    (1.47, 0.08, 0.08)], body, 6))
    ears = []
    for x in (-0.135, 0.135):
        ears += lm.loft([(1.74, 0.04, 0.03, x, 0.0), (1.84, 0.066, 0.04, x, 0.0), (1.91, 0.036, 0.024, x, 0.0)],
                        ear, 6, caps=(None, crown))
    # Морда: короткий усечённый конус вперёд из лица, торец с носом.
    snout = lm.at(lm.rot(lm.loft([(0.0, 0.085, 0.062), (0.085, 0.055, 0.04)],
                                 muzzle, 6, caps=(None, nose)), rx=-90.0), 0.0, 1.565, -0.125)
    m.part("head", (0.0, 1.46, 0.0),
           lm.loft([(1.44, 0.07, 0.07), (1.5, 0.15, 0.15, 0.0, -0.005), (1.62, 0.19, 0.185), (1.73, 0.175, 0.17),
                    (1.81, 0.1, 0.1)], head, 6, caps=(None, crown)) + ears + snout, "body")
    m.part("arm_l", (-0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.058, 0.064, -0.27, 0.0), (1.4, 0.068, 0.07, -0.215, 0.0)],
                   limb, 5, caps=(chip, None)), "body")
    # Трубочка на месте сабли скелета: от лапы вперёд на 0,7 м, на конце шапка крема.
    tube = lm.loft([(0.0, 0.04, 0.04), (0.57, 0.05, 0.05)], wafer, 6, caps=(hole, None))
    tube += lm.loft([(0.55, 0.052, 0.052), (0.6, 0.066, 0.066), (0.66, 0.045, 0.045), (0.7, 0.012, 0.012)],
                    cream, 6, caps=(None, None))
    tube = lm.at(lm.rot(tube, rx=-90.0), 0.27, 0.79, -0.02)
    m.part("arm_r", (0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.058, 0.064, 0.27, 0.0), (1.4, 0.068, 0.07, 0.215, 0.0)],
                   limb, 5, caps=(chip, None)) + tube, "body")
    return m


# --- Шоколадный король -------------------------------------------------------------------------

def sweets_captain():
    """Шоколадный король: второй боец и главарь. Крупный, торс плиткой молочного шоколада с
    потёками глазури на плечах и карамельным поясом, на голове корона из белой глазури с
    зубцами и драже, белые усы и бородка, за спиной малиновая мантия до колен в кремовой
    опушке."""
    a = lm.Atlas(64, 64, 241)
    # Торс 32×20: дольки плитки с фаской, потёки глазури от плеч, пуговицы-карамельки, пояс.
    a.rect(0, 0, 32, 17, CHOCO)
    for ty in (0, 6, 12):
        for tx in range(0, 32, 8):
            h = 6 if ty < 12 else 5
            a.rect(tx, ty, 8, 1, CHOCO_L), a.rect(tx, ty, 1, h, CHOCO_L)
            a.rect(tx, ty + h - 1, 8, 1, CHOCO_D), a.rect(tx + 7, ty, 1, h, CHOCO_D)
            a.px(tx + 2, ty + 2, CHOCO_L)
    a.rect(0, 0, 32, 2, ICING)
    for x in range(32):
        drip = (1, 2, 3, 2, 1, 0, 1, 4, 2, 1, 0, 2, 3, 1, 0, 1)[x % 16]
        a.rect(x, 2, 1, drip, ICING)
        a.px(x, 2 + drip, ICING_D)
    a.rect(13, 0, 6, 2, CHOCO_D)  # шея
    for y in (6, 10, 14):
        a.rect(15, y, 2, 2, CARAMEL), a.px(15, y, CARAMEL_L), a.rect(15, y + 2, 2, 1, CHOCO_D)
    a.rect(4, 8, 3, 3, MINT), a.px(4, 8, MINT_L), a.rect(4, 10, 3, 1, MINT_D)  # орден-драже
    a.rect(0, 17, 32, 3, CARAMEL)
    a.rect(0, 17, 32, 1, CARAMEL_L)
    a.rect(0, 19, 32, 1, CARAMEL_D)
    a.rect(13, 17, 6, 3, CARAMEL_L), a.rect(13, 19, 6, 1, CARAMEL_D)  # пряжка с вишней
    a.rect(15, 18, 2, 1, JELLY)
    a.shade(0, 0, 32, 20, 1.1, 0.84, 0.74)
    a.noise(0, 0, 32, 20, 0.05)
    torso = a.region(0, 0, 32, 20)
    # Голова 32×24, шесть полос по четыре строки сверху вниз: раструб короны, обод с драже,
    # потёки глазури на лбу, глаза под белыми бровями, усы и рот, подбородок с бородкой.
    a.rect(0, 20, 32, 8, ICING)
    for x in range(0, 32, 4):
        a.rect(x, 20, 1, 4, ICING_D)
        a.px(x + 2, 20, PINK)
    a.rect(0, 24, 32, 1, ICING_D)
    a.rect(0, 27, 32, 1, ICING_D)
    for x, c, c_l in ((14, JELLY, JELLY_L), (6, MINT, MINT_L), (22, MINT, MINT_L), (30, PINK, PINK_L)):
        w = 4 if x == 14 else 2
        a.rect(x, 25, w, 2, c), a.px(x, 25, c_l)
    a.px(0, 25, PINK), a.px(1, 25, PINK), a.px(0, 26, PINK), a.px(1, 26, PINK)
    a.rect(0, 28, 32, 16, CHOCO)
    a.rect(0, 28, 32, 1, ICING)
    for x in range(32):
        drip = (2, 3, 1, 1, 2, 4, 3, 1, 0, 1, 2, 1, 0, 1, 2, 1)[(x + 5) % 16]
        if 9 <= x <= 22:
            drip = min(drip, 2)  # над глазами потёки короткие
        a.rect(x, 29, 1, drip, ICING)
        a.px(x, 29 + drip, CHOCO_D)
    a.rect(10, 32, 4, 1, ICING), a.px(13, 33, ICING)  # хмурые брови глазурью
    a.rect(18, 32, 4, 1, ICING), a.px(18, 33, ICING)
    a.rect(11, 34, 2, 2, CARAMEL_L), a.px(12, 34, BLACK), a.px(12, 35, BLACK)
    a.rect(19, 34, 2, 2, CARAMEL_L), a.px(19, 34, BLACK), a.px(19, 35, BLACK)
    a.rect(15, 35, 2, 2, CHOCO_L), a.px(15, 37, CHOCO_D), a.px(16, 37, CHOCO_D)  # нос
    a.rect(12, 38, 3, 1, ICING), a.rect(17, 38, 3, 1, ICING)  # усы с завитком вверх
    a.rect(10, 39, 3, 1, ICING), a.rect(19, 39, 3, 1, ICING)
    a.px(9, 38, ICING), a.px(22, 38, ICING), a.px(9, 37, ICING), a.px(22, 37, ICING)
    a.rect(14, 40, 4, 1, CHOCO_D)  # рот
    a.rect(15, 41, 2, 3, ICING), a.px(14, 41, ICING), a.px(17, 41, ICING)  # бородка
    a.rect(0, 33, 4, 10, CHOCO_D), a.rect(28, 33, 4, 10, CHOCO_D)
    for x in (2, 29):
        a.rect(x, 34, 1, 8, CHOCO)  # бороздка дольки на затылке
    a.shade(0, 20, 32, 24, 1.06, 0.88, 0.84)
    a.noise(0, 20, 32, 24, 0.04)
    head = a.region(0, 20, 32, 24)
    # Рукав 16×16: дольки шоколада, манжета глазури с волной, тёмная кисть.
    a.rect(32, 0, 16, 16, CHOCO)
    for ty in (0, 5):
        for tx in (32, 40):
            a.rect(tx, ty, 8, 1, CHOCO_L), a.rect(tx, ty, 1, 5, CHOCO_L)
            a.rect(tx, ty + 4, 8, 1, CHOCO_D), a.rect(tx + 7, ty, 1, 5, CHOCO_D)
    a.rect(32, 9, 16, 2, ICING)
    _wave(a, 32, 11, 16, ICING, CHOCO_D)
    a.rect(32, 9, 16, 1, ICING_D)
    a.rect(32, 13, 16, 3, CHOCO_D)
    for x in (35, 39, 43):
        a.px(x, 15, BLACK)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.76)
    a.noise(32, 0, 16, 16, 0.05)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: тёмный шоколад с карамельным лампасом, сапог с каймой глазури и драже.
    a.rect(48, 0, 16, 14, CHOCO_D)
    a.rect(55, 0, 1, 14, CARAMEL_D)
    for y in (4, 9):
        a.rect(48, y, 16, 1, BLACK)
    a.rect(48, 14, 16, 10, CHOCO)
    a.rect(48, 14, 16, 1, ICING)
    _wave(a, 48, 15, 16, ICING, CHOCO_D)
    a.rect(54, 19, 4, 2, CARAMEL), a.px(54, 19, CARAMEL_L)
    a.rect(48, 22, 16, 2, CHOCO_D)
    a.shade(48, 0, 16, 24, 1.05, 0.86, 0.76)
    a.noise(48, 0, 16, 24, 0.05)
    leg = a.region(48, 0, 16, 24)
    # Мантия 24×20: малиновые складки, кремовая опушка с шоколадной крошкой сверху, снизу и по краям.
    a.rect(0, 44, 24, 20, PINK_D)
    for x in (3, 7, 12, 16, 20):
        a.rect(x, 47, 1, 14, rgb("8A2A58"))
        a.rect(x + 1, 48, 1, 12, PINK)
    a.rect(0, 44, 24, 3, ICING), a.rect(0, 46, 24, 1, ICING_D)
    a.rect(0, 61, 24, 3, ICING), a.rect(0, 61, 24, 1, ICING_D)
    a.rect(0, 44, 1, 20, ICING), a.rect(23, 44, 1, 20, ICING)
    for x in range(2, 24, 4):
        a.px(x, 45, CHOCO_D), a.px(x + 2, 62, CHOCO_D), a.px(x, 63, CHOCO)
    a.shade(0, 44, 24, 20, 1.05, 0.82, 0.88)
    a.noise(0, 44, 24, 20, 0.05)
    # Верх короны 16×16: кольцо глазури, внутри малиновая подушка с крошкой.
    a.rect(32, 24, 16, 16, ICING)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if d < 5.2:
                a.px(32 + x, 24 + y, PINK_D if d > 4.2 else PINK)
    for x, y in ((38, 30), (41, 33), (37, 34), (42, 29)):
        a.px(x, y, PINK_L)
    top = a.region(32, 24, 16, 16)
    # Зубец короны 8×12 лентой по четырём граням: розовая капля на острие.
    a.rect(48, 24, 8, 12, ICING)
    a.rect(48, 24, 8, 3, PINK), a.rect(48, 26, 8, 1, PINK_D)
    for x in (48, 50, 52, 54):
        a.rect(x, 27, 1, 9, ICING_D)
    spike = a.region(48, 24, 8, 12)
    a.rect(32, 16, 4, 4, CHOCO_D)
    a.rect(36, 16, 4, 4, PINK)
    sole, crown = a.region(32, 16, 4, 4), a.region(36, 16, 4, 4)

    parts = lm.biped(leg, torso, head, arm, sole, crown, 1.18)
    # Голова: лицо, наплыв глазури на лбу, обод короны и раструб кверху.
    crowned = lm.loft([(1.44, 0.07, 0.075), (1.5, 0.125, 0.13, 0.0, -0.005), (1.6, 0.15, 0.155), (1.7, 0.15, 0.155),
                       (1.75, 0.168, 0.172), (1.8, 0.155, 0.16), (1.88, 0.19, 0.195)], head, 6, caps=(None, top))
    # Шесть зубцов по краю раструба, основанием утоплены в корону: пирамидки в четыре грани, без
    # донца (оно внутри короны) и со сведённым в точку остриём, иначе модель тяжелее предела.
    for k in range(6):
        ang = math.radians(30.0 + 60.0 * k)
        crowned += lm.at(lm.rot(lm.box((0.075, 0.1, 0.075), spike, None, None, (0.0, 0.0)), ry=math.degrees(ang)),
                         0.148 * math.sin(ang), 1.88, 0.152 * math.cos(ang))
    parts["head"][1] = crowned
    # Мантия: три полотнища от плеч до колен, книзу шире и дальше от спины.
    cloak = []
    hi = [(0.27, 0.19), (0.09, 0.2), (-0.09, 0.2), (-0.27, 0.19)]
    low = [(0.37, 0.3), (0.13, 0.34), (-0.13, 0.34), (-0.37, 0.3)]
    for i in range(3):
        cloak += lm.quad((hi[i][0], 1.4, hi[i][1]), (hi[i + 1][0], 1.4, hi[i + 1][1]),
                         (low[i + 1][0], 0.5, low[i + 1][1]), (low[i][0], 0.5, low[i][1]),
                         a.region(i * 8, 44, 8, 20))
    parts["body"][1].extend(cloak)
    return lm.assemble("captain", a, parts)


MODELS = [sweets_hero, sweets_enemy, sweets_captain]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        models = [f() for f in MODELS]
        for m in models:
            print("%-8s частей %d, треугольников %d" % (m.name, len(m.parts), m.tris()))
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
