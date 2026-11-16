#!/usr/bin/env python3
"""Мелкий реквизит «Сладостей» для low poly и «продвинутых» (#137): восемь моделей в слотах пиратов.

Зеркало `pirate_coin`, `pirate_bottle`, `pirate_ball`, `pirate_rock`, `pirate_barrel`,
`pirate_crate`, `pirate_chest`, `pirate_keg` из `lowpoly_meshes.py` и модуля космоса
`space_mesh_items.py`. У каждой модели одна часть `body` с той же точкой вращения и теми же
габаритами, что у пиратской: демки ставят их, крутят и кидают по этим числам. Плотный набор
«продвинутых» выходит из тех же функций (`lm.DENSE`).

Состав по столбцу «Сладости» (`docs/specs/settings.md`): бонус это конфета в фантике, мишень и
снаряд метателя это бутылочка сиропа, снаряд это драже, препятствия это рафинад, кубик желе на
блюдце и коробка конфет, сундук это коробка с бантом, мяч это шар жвачки. Цвета из основы
16/32 (`sweets16.PALETTE`) через `sweets_mesh_chars`.

    python3 tools/sweets_mesh_items.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from sweets_mesh_chars import (  # noqa: E402
    BLACK, CARAMEL, CARAMEL_D, CARAMEL_L, CHOCO, CHOCO_D, CHOCO_L, ICING, ICING_D,
    JELLY, JELLY_D, JELLY_L, MINT, MINT_D, MINT_L, PINK, PINK_D, PINK_L)

rgb, mul = lm.rgb, lm.mul

SQ2 = math.sqrt(2.0)


def _ball_rings(cy, ry, rxz, angles=(0.35, 1.0, math.pi / 2.0, math.pi - 1.0, math.pi - 0.35)):
    """Кольца шара или сплюснутой горошины с центром на высоте `cy`."""
    return [(cy - ry * math.cos(t), rxz * math.sin(t), rxz * math.sin(t)) for t in angles]


def _gloss(a, x, y, w=2, h=2, c=ICING):
    """Блик глазури: светлое пятно с точкой рядом."""
    a.rect(x, y, w, h, c)
    a.px(x + w, y + h, c)


def _dots(a, x, y, w, h, step, c, shift=0):
    """Горошек в шахматном порядке."""
    for j in range(y, y + h, step):
        off = (step // 2) if ((j - y) // step) % 2 else 0
        for i in range(x + off + shift, x + w, step):
            a.px(i, j, c)


def sweets_coin():
    """Бонус: карамель в золотом фантике с красным пояском, по бокам белые веера хвостов.
    Лежит наискось вокруг точки вращения и крутится, как монета."""
    a = lm.Atlas(32, 32, 305)
    # Лента 32×28 вдоль конфеты, семь поясов по четыре строки: веер, скрутка, золото, поясок,
    # золото, скрутка, веер.
    a.rect(0, 0, 32, 28, CARAMEL)
    for y0, flip_ in ((0, False), (24, True)):
        # Веер: белые складки, тёмная линия через три пикселя, золотая кромка у края.
        a.rect(0, y0, 32, 4, ICING)
        for x in range(0, 32, 3):
            a.rect(x, y0, 1, 4, ICING_D)
        edge = y0 + (3 if flip_ else 0)
        for x in range(32):
            a.px(x, edge, CARAMEL_L if x % 3 else CARAMEL_D)
    for y0, flip_ in ((4, False), (20, True)):
        # Скрутка: от белого узла к золоту, косые складки.
        for j in range(4):
            k = j if not flip_ else 3 - j
            for x in range(32):
                c = ICING if k == 0 else (CARAMEL_L if k == 1 else CARAMEL)
                if (x + k) % 4 == 0:
                    c = ICING_D if k == 0 else CARAMEL_D
                a.px(x, y0 + j, c)
    # Тело: золото с продольными бликами фольги, красный поясок с белой строчкой.
    for x in range(32):
        tone = (1.12, 1.0, 0.9, 1.0)[x % 4]
        for y in list(range(8, 12)) + list(range(16, 20)):
            a.px(x, y, mul(CARAMEL, tone))
    a.rect(0, 8, 32, 1, CARAMEL_L), a.rect(0, 19, 32, 1, CARAMEL_D)
    a.rect(0, 12, 32, 4, JELLY)
    a.rect(0, 12, 32, 1, JELLY_L), a.rect(0, 15, 32, 1, JELLY_D)
    for x in range(1, 32, 4):
        a.rect(x, 13, 2, 1, ICING)
    for x, y in ((3, 9), (4, 9), (18, 10), (19, 10), (11, 17), (26, 17)):
        a.px(x, y, ICING)
    for x, y in ((8, 18), (22, 9), (29, 17), (14, 10)):
        a.px(x, y, CARAMEL_D)
    a.noise(0, 0, 32, 28, 0.04)
    face = a.region(0, 0, 32, 28)
    # Торец веера: белые складки лучами.
    a.rect(0, 28, 8, 4, ICING)
    for x in (1, 3, 5, 7):
        a.rect(x, 28, 1, 4, ICING_D)
    a.rect(0, 28, 8, 1, CARAMEL_L)
    tail = a.region(0, 28, 8, 4)
    rings = [(-0.24, 0.12, 0.04), (-0.13, 0.03, 0.03), (-0.1, 0.085, 0.085), (-0.045, 0.125, 0.125),
             (0.045, 0.125, 0.125), (0.1, 0.085, 0.085), (0.13, 0.03, 0.03), (0.24, 0.12, 0.04)]
    candy = lm.rot(lm.loft(rings, face, 6, caps=(tail, tail)), rz=65.0)
    return lm.Model("coin", a).part("body", (0.0, 0.35, 0.0), lm.at(candy, 0.0, 0.35))


def sweets_bottle():
    """Бутылочка сиропа: пузатая склянка с розовым сиропом, узкое горло, широкая золотая крышка,
    белая этикетка с красным сердечком. Мишень и снаряд метателя, размеры бутылки."""
    a = lm.Atlas(16, 16, 347)
    # Лента 16×14, семь поясов по две строки сверху вниз: крышка, испод крышки, горло, плечи,
    # два пояса брюшка с этикеткой, донце.
    a.rect(0, 0, 16, 2, CARAMEL), a.rect(0, 0, 16, 1, CARAMEL_L)
    for x in range(0, 16, 2):
        a.px(x, 1, CARAMEL_D)  # рифление крышки
    a.rect(0, 2, 16, 2, CARAMEL_D)
    a.rect(0, 4, 16, 2, PINK_L), a.rect(0, 5, 16, 1, PINK)  # горло: стекло, ниже уровень сиропа
    a.rect(0, 6, 16, 8, PINK)
    a.rect(0, 6, 16, 1, PINK_L)
    a.rect(0, 12, 16, 2, PINK_D)
    # Блик стекла слева от этикетки и пузырьки.
    a.rect(3, 6, 1, 3, ICING), a.px(3, 10, ICING), a.px(11, 4, ICING)
    for x, y in ((12, 7), (14, 10), (1, 9), (13, 12)):
        a.px(x, y, PINK_L)
    # Этикетка спереди (середина ленты): белый ярлык, красное сердечко, строчка.
    a.rect(6, 8, 5, 4, ICING), a.rect(6, 11, 5, 1, ICING_D)
    a.px(7, 8, JELLY), a.px(9, 8, JELLY), a.rect(7, 9, 3, 1, JELLY), a.px(8, 10, JELLY)
    a.shade(0, 0, 16, 14, 1.08, 0.88, 0.8)
    a.noise(0, 0, 16, 14, 0.04)
    body = a.region(0, 0, 16, 14)
    a.rect(0, 14, 4, 2, CARAMEL), a.rect(1, 14, 2, 1, CARAMEL_L), a.px(3, 15, CARAMEL_D)
    cork = a.region(0, 14, 4, 2)
    a.rect(4, 14, 4, 2, PINK_D), a.px(5, 14, PINK)
    under = a.region(4, 14, 4, 2)
    return lm.Model("bottle", a).part(
        "body", (0.0, 0.25, 0.0),
        lm.loft([(0.0, 0.095, 0.095), (0.03, 0.115, 0.115), (0.12, 0.115, 0.115), (0.21, 0.105, 0.105),
                 (0.3, 0.04, 0.04), (0.4, 0.036, 0.036), (0.41, 0.068, 0.068), (0.5, 0.062, 0.062)],
                body, 6, caps=(under, cork)))


def sweets_ball():
    """Драже: снаряд. Сплюснутая красная горошина в глянцевой глазури, белый блик, светлый
    поясок по ребру."""
    a = lm.Atlas(16, 16, 349)
    a.rect(0, 0, 16, 16, JELLY)
    a.rect(0, 0, 16, 3, JELLY_L)
    a.rect(0, 12, 16, 4, JELLY_D)
    # Ребро горошины: светлая строчка с разрывами, под ней тень.
    for x in range(16):
        a.px(x, 7, JELLY_L)
        a.px(x, 8, mul(JELLY, 0.86))
    # Блики глазури спереди и сзади, сахарная пыль.
    _gloss(a, 6, 2, 3, 2)
    _gloss(a, 14, 3, 1, 1)
    for x, y in ((2, 5), (11, 10), (4, 11), (13, 13), (9, 5)):
        a.px(x, y, PINK_L)
    a.shade(0, 0, 16, 16, 1.2, 0.7, 0.88)
    a.noise(0, 0, 16, 16, 0.05)
    glaze = a.region(0, 0, 16, 16)
    # Макушка и донце берут чистые полосы той же ленты: светлую сверху, тёмную снизу.
    crown, sole = a.region(0, 0, 16, 2), a.region(0, 14, 16, 2)
    r = 0.18
    return lm.Model("ball", a).part("body", (0.0, r, 0.0), lm.loft(_ball_rings(r, 0.15, r), glaze, 6, caps=(sole, crown)))


def _sugar_side(a, x0, y0, w, h, faces=4):
    """Грани рафинада: белый сахар в зёрнах, светлое ребро слева, сиреневая тень справа и снизу."""
    fw = w // faces
    a.rect(x0, y0, w, h, ICING)
    for f in range(faces):
        x = x0 + f * fw
        tone = (1.0, 0.93, 0.86, 0.95)[f % 4]
        for j in range(h):
            for i in range(fw):
                # Зёрна: шашечка из двух близких тонов, реже крупная сиреневая крупинка.
                c = ICING if (i + j) % 2 else mul(ICING, 0.95)
                a.px(x + i, y0 + j, mul(c, tone))
        a.rect(x, y0, fw, 1, ICING)
        a.rect(x, y0, 1, h, ICING)
        a.rect(x + fw - 1, y0 + 1, 1, h - 1, ICING_D)
        a.rect(x + 1, y0 + h - 1, fw - 1, 1, ICING_D)
        for _ in range(max(2, fw * h // 14)):
            i, j = a.rng.randrange(1, fw - 1), a.rng.randrange(1, h - 1)
            a.px(x + i, y0 + j, ICING_D if a.rng.random() < 0.6 else MINT_L)
        # Искра кристалла: белый крестик на сиреневой подложке.
        i, j = a.rng.randrange(2, fw - 2), a.rng.randrange(2, h - 2)
        a.px(x + i, y0 + j, (255, 255, 255))
        a.px(x + i + 1, y0 + j, ICING_D), a.px(x + i, y0 + j + 1, ICING_D)


def _sugar_top(a, x0, y0, s):
    """Верх куска: самый светлый, кромка в тени, скол в углу и розовая капля сиропа."""
    for j in range(s):
        for i in range(s):
            a.px(x0 + i, y0 + j, (255, 252, 246) if (i + j) % 2 else ICING)
    a.rect(x0, y0, s, 1, ICING_D), a.rect(x0, y0 + s - 1, s, 1, ICING_D)
    a.rect(x0, y0, 1, s, ICING_D), a.rect(x0 + s - 1, y0, 1, s, ICING_D)
    a.px(x0 + 1, y0 + 1, ICING_D), a.px(x0 + 2, y0 + 1, ICING_D), a.px(x0 + 1, y0 + 2, ICING_D)
    for i, j in ((s // 2, s // 3), (s - 4, s - 4), (3, s - 3)):
        a.px(x0 + i, y0 + j, MINT_L)
    a.rect(x0 + s - 5, y0 + 2, 2, 2, PINK_L), a.px(x0 + s - 4, y0 + 4, PINK)


def sweets_rock():
    """Рафинад: большой белый куб сахара, на нём второй кусок набекрень, рядом отколотый кубик.
    Грани в зёрнах и искрах, рёбра светлые, тени сиреневые."""
    a = lm.Atlas(32, 32, 307)
    _sugar_side(a, 0, 0, 32, 12)
    a.shade(0, 0, 32, 12, 1.04, 0.86, 1.0)
    side = a.region(0, 0, 32, 12)
    _sugar_top(a, 0, 12, 12)
    top = a.region(0, 12, 12, 12)
    # Малые куски: свои грани покрупнее зерном и верх с подтёком сиропа.
    _sugar_side(a, 0, 24, 32, 8)
    a.shade(0, 24, 32, 8, 1.04, 0.88, 1.0)
    side_s = a.region(0, 24, 32, 8)
    _sugar_top(a, 12, 12, 10)
    top_s = a.region(12, 12, 10, 10)
    a.rect(22, 12, 10, 12, ICING_D)
    _dots(a, 22, 12, 10, 12, 2, ICING)
    under = a.region(22, 12, 10, 12)
    big = lm.at(lm.rot(lm.box((0.78, 0.46, 0.74), side, top, None), ry=14.0), 0.0, 0.23)
    # Верхний кусок сидит ребром в большом: наклон и поворот, низ утоплен на пару сантиметров.
    upper = lm.at(lm.rot(lm.box((0.34, 0.27, 0.32), side_s, top_s, under), rx=9.0, ry=-32.0, rz=-7.0), -0.1, 0.575, 0.06)
    chip = lm.at(lm.rot(lm.box((0.27, 0.25, 0.26), side_s, top_s, None), ry=38.0), 0.5, 0.125, 0.3)
    return lm.Model("rock", a).part("body", (0.0, 0.0, 0.0), big + upper + chip)


def sweets_barrel():
    """Кубик желе: мятный дрожащий куб на белом блюдце с розовым кантом, сверху шапка взбитых
    сливок и красная ягода. Высота и поперечник бочки."""
    a = lm.Atlas(32, 32, 309)
    # Грани желе 8×18: прозрачная мята светлее к середине и к верху, белый блик, пузырьки.
    for f in range(4):
        x = f * 8
        for j in range(18):
            for i in range(8):
                core = 1.0 - (abs(i - 3.5) / 3.5) ** 2 * 0.22
                depth = 1.14 - 0.3 * j / 17.0
                a.px(x + i, j, mul(MINT, core * depth))
        a.rect(x, 0, 8, 1, MINT_L)
        a.rect(x, 1, 1, 17, mul(MINT_L, 0.96))
        a.rect(x + 7, 1, 1, 17, MINT_D)
        a.rect(x + 1, 16, 6, 2, MINT_D), a.rect(x + 2, 16, 3, 1, mul(MINT, 0.85))
        # Блик: длинный штрих и точка под ним.
        a.rect(x + 2, 2, 1, 6, ICING), a.px(x + 2, 10, ICING)
        for i, j in ((5, 6), (4, 12), (6, 10)):
            a.px(x + i, j, MINT_L)
            a.px(x + i, j + 1, MINT_D)
    # Внутри желе видны ягоды: красные пятна в глубине, спереди и сзади.
    for x in (12, 28):
        a.rect(x, 11, 2, 2, JELLY_D), a.px(x, 11, JELLY)
    a.px(5, 13, JELLY_D), a.px(21, 9, JELLY_D)
    a.noise(0, 0, 32, 18, 0.03)
    side = a.region(0, 0, 32, 18)
    # Верх желе: светлая мята, глянец в углу, тень под сливками.
    a.rect(0, 18, 10, 10, MINT_L)
    a.rect(0, 18, 10, 1, MINT), a.rect(0, 27, 10, 1, MINT), a.rect(0, 18, 1, 10, MINT), a.rect(9, 18, 1, 10, MINT)
    a.rect(3, 21, 4, 4, MINT)
    a.rect(1, 19, 2, 1, ICING), a.px(1, 20, ICING)
    top = a.region(0, 18, 10, 10)
    # Сливки: белые витки с сиреневой тенью наискось.
    a.rect(10, 18, 16, 8, ICING)
    for j in range(8):
        for i in range(16):
            if (i + j * 2) % 5 == 0:
                a.px(10 + i, 18 + j, ICING_D)
            elif (i + j * 2) % 5 == 1:
                a.px(10 + i, 18 + j, (255, 255, 255))
    a.rect(10, 25, 16, 1, ICING_D)
    cream = a.region(10, 18, 16, 8)
    # Блюдце: белое, розовый кант фестонами по краю.
    a.rect(26, 18, 6, 6, ICING)
    for i in range(6):
        a.px(26 + i, 18, PINK if i % 2 else PINK_L), a.px(26 + i, 23, PINK if i % 2 else PINK_D)
        a.px(26, 18 + i, PINK if i % 2 else PINK_L), a.px(31, 18 + i, PINK if i % 2 else PINK_D)
    a.rect(28, 20, 2, 2, ICING_D)
    plate = a.region(26, 18, 6, 6)
    a.rect(26, 24, 6, 2, ICING), a.rect(26, 24, 6, 1, PINK), a.rect(26, 25, 6, 1, ICING_D)
    rim = a.region(26, 24, 6, 2)
    # Ягода.
    a.rect(26, 26, 4, 4, JELLY), a.px(27, 27, ICING), a.rect(26, 29, 4, 1, JELLY_D), a.px(29, 26, JELLY_L)
    berry = a.region(26, 26, 4, 4)
    half = (0.29, 0.32, 0.31, 0.295, 0.245)
    ys = (0.035, 0.2, 0.37, 0.54, 0.7)
    jelly = lm.loft([(y, h * SQ2, h * SQ2) for y, h in zip(ys, half)], side, 4, math.pi / 4.0, (None, top), True)
    saucer = lm.loft([(0.0, 0.34, 0.34), (0.02, 0.44, 0.44), (0.04, 0.46, 0.46)], rim, 8, caps=(None, plate))
    whip = lm.loft([(0.69, 0.17, 0.17), (0.735, 0.185, 0.185), (0.775, 0.13, 0.13), (0.81, 0.07, 0.07), (0.835, 0.02, 0.02)],
                   cream, 6, 0.3)
    cherry = lm.loft(_ball_rings(0.825, 0.035, 0.04), berry, 5, caps=(berry, berry))
    return lm.Model("barrel", a).part("body", (0.0, 0.0, 0.0), saucer + jelly + whip + cherry)


def _bonbon(a, x, y, c, c_l, c_d, mark=None):
    """Конфета 3×3 в бумажной розетке: блик сверху слева, тень снизу, сверху завиток или орех."""
    a.rect(x - 1, y - 1, 5, 5, CARAMEL_D)
    a.px(x - 1, y - 1, CHOCO_D), a.px(x + 3, y - 1, CHOCO_D), a.px(x - 1, y + 3, CHOCO_D), a.px(x + 3, y + 3, CHOCO_D)
    a.rect(x, y, 3, 3, c)
    a.px(x, y, c_l)
    a.rect(x, y + 2, 3, 1, c_d)
    if mark is not None:
        a.px(x + 1, y + 1, mark)


def sweets_crate():
    """Коробка конфет: розовая в белую полоску, кружевная кайма по верху, спереди ярлык с
    конфетой; коробка открыта, сверху видны девять конфет в розетках."""
    a = lm.Atlas(32, 32, 351)
    for f in range(4):
        x = f * 8
        # Полоски, кружево по верху, тёмный низ, светлое и тёмное ребро грани.
        for i in range(8):
            a.rect(x + i, 0, 1, 16, PINK if (i // 2) % 2 == 0 else PINK_L)
        a.rect(x, 0, 8, 2, ICING)
        for i in range(8):
            if i % 2 == 0:
                a.px(x + i, 2, ICING)
            a.px(x + i, 3 if i % 2 == 0 else 2, PINK_D)
        a.rect(x, 14, 8, 1, PINK_D), a.rect(x, 15, 8, 1, mul(PINK_D, 0.8))
        a.rect(x, 3, 1, 11, PINK_L), a.rect(x + 7, 3, 1, 11, PINK_D)
    # Перёд (вторая четверть ленты): белый овальный ярлык с шоколадной конфетой.
    a.rect(10, 6, 4, 6, ICING), a.rect(9, 7, 6, 4, ICING)
    a.rect(11, 8, 2, 2, CHOCO), a.px(11, 8, CHOCO_L), a.px(12, 10, ICING_D), a.px(11, 10, ICING_D)
    # Зад: красное сердечко; бока: золотая печать.
    a.px(26, 7, JELLY), a.px(28, 7, JELLY), a.rect(26, 8, 3, 1, JELLY), a.px(27, 9, JELLY)
    for x in (3, 19):
        a.rect(x, 7, 2, 3, CARAMEL), a.px(x, 7, CARAMEL_L), a.rect(x - 1, 8, 4, 1, CARAMEL), a.rect(x, 10, 2, 1, PINK_D)
    a.shade(0, 0, 32, 16, 1.05, 0.84, 1.0)
    a.noise(0, 0, 32, 16, 0.03)
    side = a.region(0, 0, 32, 16)
    # Верх: розовый борт с белым кантом, тёмный поддон, девять конфет.
    a.rect(0, 16, 16, 16, PINK)
    a.rect(0, 16, 16, 1, PINK_L), a.rect(0, 31, 16, 1, PINK_D), a.rect(0, 16, 1, 16, PINK_L), a.rect(15, 16, 1, 16, PINK_D)
    a.rect(1, 17, 14, 14, ICING)
    a.rect(2, 18, 12, 12, CHOCO_D)
    kinds = [(CHOCO, CHOCO_L, CHOCO_D, ICING), (PINK, PINK_L, PINK_D, None), (ICING, (255, 255, 255), ICING_D, JELLY),
             (CARAMEL, CARAMEL_L, CARAMEL_D, None), (CHOCO_L, CARAMEL_L, CHOCO, CARAMEL), (MINT, MINT_L, MINT_D, None),
             (JELLY, JELLY_L, JELLY_D, None), (CHOCO, CHOCO_L, CHOCO_D, PINK), (ICING, (255, 255, 255), ICING_D, CHOCO)]
    for k, (c, c_l, c_d, mark) in enumerate(kinds):
        _bonbon(a, 3 + (k % 3) * 4, 19 + (k // 3) * 4, c, c_l, c_d, mark)
    a.noise(0, 16, 16, 16, 0.03)
    top = a.region(0, 16, 16, 16)
    # Дно: картон.
    a.rect(16, 16, 8, 8, PINK_D)
    _dots(a, 16, 16, 8, 8, 2, mul(PINK_D, 0.85))
    under = a.region(16, 16, 8, 8)
    return lm.Model("crate", a).part("body", (0.0, 0.0, 0.0), lm.at(lm.box((0.85, 0.85, 0.85), side, top, under), 0.0, 0.425))


def sweets_chest():
    """Коробка с бантом: мятная коробка в горошек под светлой крышкой, красная лента
    крест-накрест и пышный бант из двух петель с узлом."""
    a = lm.Atlas(64, 32, 313)
    # Бока коробки 64×12: мята в горошек, тень под крышкой, лента посередине каждой грани.
    a.rect(0, 0, 64, 12, MINT)
    _dots(a, 0, 2, 64, 9, 3, MINT_L)
    a.rect(0, 0, 64, 1, MINT_D), a.rect(0, 1, 64, 1, mul(MINT, 0.9))
    a.rect(0, 11, 64, 1, MINT_D)
    for x in (0, 16, 32, 48):
        a.rect(x, 0, 1, 12, mul(MINT, 1.1)), a.rect(x + 15, 0, 1, 12, MINT_D)
        a.rect(x + 6, 0, 4, 12, JELLY), a.rect(x + 6, 0, 1, 12, JELLY_L), a.rect(x + 9, 0, 1, 12, JELLY_D)
        a.rect(x + 6, 0, 4, 1, JELLY_D)
    # Ярлычок на ниточке спереди (вторая четверть ленты).
    a.rect(27, 4, 3, 4, ICING), a.px(28, 5, JELLY), a.px(28, 6, PINK), a.px(27, 3, BLACK)
    a.shade(0, 0, 64, 12, 1.04, 0.84, 1.0)
    a.noise(0, 0, 64, 12, 0.03)
    side = a.region(0, 0, 64, 12)
    # Бока крышки 64×8: светлая мята, белый кант сверху, тёмная кромка снизу, лента.
    a.rect(0, 12, 64, 8, MINT_L)
    a.rect(0, 12, 64, 1, ICING)
    a.rect(0, 18, 64, 1, MINT), a.rect(0, 19, 64, 1, MINT_D)
    for x in range(1, 64, 4):
        a.px(x, 15, MINT)
    for x in (0, 16, 32, 48):
        a.rect(x + 15, 12, 1, 8, MINT)
        a.rect(x + 6, 12, 4, 8, JELLY), a.rect(x + 6, 12, 1, 8, JELLY_L), a.rect(x + 9, 12, 1, 8, JELLY_D)
    a.noise(0, 12, 64, 8, 0.03)
    lid_side = a.region(0, 12, 64, 8)
    # Верх крышки 24×12: лента крестом, горошек, тень от банта у узла.
    a.rect(0, 20, 24, 12, MINT_L)
    _dots(a, 1, 21, 22, 10, 3, MINT)
    a.rect(0, 20, 24, 1, ICING), a.rect(0, 31, 24, 1, MINT), a.rect(0, 20, 1, 12, ICING), a.rect(23, 20, 1, 12, MINT)
    a.rect(0, 25, 24, 2, JELLY), a.rect(0, 25, 24, 1, JELLY_L)
    a.rect(10, 20, 4, 12, JELLY), a.rect(10, 20, 1, 12, JELLY_L), a.rect(13, 20, 1, 12, JELLY_D)
    a.rect(9, 24, 6, 4, JELLY_D)
    lid_top = a.region(0, 20, 24, 12)
    a.rect(24, 20, 4, 4, MINT_D)
    under = a.region(24, 20, 4, 4)
    # Петля банта 12×12: красный атлас, светлая складка вдоль, малиновая тень у узла и по краю.
    a.rect(28, 20, 12, 12, JELLY)
    for x in range(28, 40):
        k = (x - 28) % 6
        if k == 2:
            a.rect(x, 20, 1, 12, JELLY_L)
        elif k == 5:
            a.rect(x, 20, 1, 12, JELLY_D)
    a.rect(28, 20, 12, 2, JELLY_L), a.rect(28, 28, 12, 4, JELLY_D)
    a.px(31, 23, ICING), a.px(37, 23, ICING)
    loop = a.region(28, 20, 12, 12)
    a.rect(40, 20, 6, 6, JELLY), a.rect(40, 20, 6, 1, JELLY_L), a.rect(40, 25, 6, 1, JELLY_D)
    a.px(41, 22, ICING), a.rect(45, 20, 1, 6, JELLY_D)
    knot = a.region(40, 20, 6, 6)
    box = lm.at(lm.box((0.8, 0.4, 0.5), side, None, under), 0.0, 0.2)
    lid = lm.at(lm.box((0.86, 0.11, 0.56), lid_side, lid_top, under), 0.0, 0.445)
    # Петли растут из узла в стороны и вверх; узел утоплен в крышку.
    petal = lm.loft([(0.0, 0.02, 0.025), (0.05, 0.06, 0.08), (0.12, 0.075, 0.095), (0.175, 0.045, 0.06), (0.195, 0.01, 0.012)], loop, 6)
    bow = (lm.at(lm.rot(petal, rz=72.0), 0.0, 0.5) + lm.at(lm.rot(petal, rz=-72.0), 0.0, 0.5)
           + lm.at(lm.box((0.09, 0.08, 0.1), knot, knot, None, (0.8, 0.8)), 0.0, 0.53))
    return lm.Model("chest", a).part("body", (0.0, 0.0, 0.0), box + lid + bow)


def sweets_keg():
    """Шар жвачки: мяч. Розовый шар в белых закрученных дольках, блик глазури;
    дольки видно, когда он катится и крутится."""
    a = lm.Atlas(16, 16, 369)
    for j in range(12):
        for i in range(16):
            # Дольки по меридианам с лёгким закрутом: три пикселя белой, пять розовой.
            k = (i + j // 4) % 8
            c = PINK
            if k in (0, 1, 2):
                c = ICING
            elif k == 3:
                c = PINK_L
            elif k == 7:
                c = PINK_D
            a.px(i, j, c)
    _gloss(a, 6, 2, 2, 2, (255, 255, 255))
    a.shade(0, 0, 16, 12, 1.15, 0.74, 0.9)
    a.noise(0, 0, 16, 12, 0.04)
    side = a.region(0, 0, 16, 12)
    # Полюса: розовый кружок с белой точкой завитка.
    a.rect(0, 12, 4, 4, PINK), a.px(1, 13, ICING), a.px(2, 14, PINK_D), a.px(2, 13, PINK_L)
    lid = a.region(0, 12, 4, 4)
    r = 0.15
    return lm.Model("keg", a).part("body", (0.0, 0.15, 0.0), lm.loft(_ball_rings(r, r, r), side, 6, caps=(lid, lid)))


MODELS = [sweets_coin, sweets_bottle, sweets_ball, sweets_rock, sweets_barrel, sweets_crate, sweets_chest, sweets_keg]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], [f() for f in MODELS])
    for f in MODELS:
        m = f()
        print("%-7s частей %d, треугольников %d, атлас %d×%d" % (m.name, len(m.parts), m.tris(), m.atlas.w, m.atlas.h))
