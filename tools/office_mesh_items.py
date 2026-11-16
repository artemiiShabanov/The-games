#!/usr/bin/env python3
"""Мелкий реквизит «Офиса» для low poly и «продвинутых» (#137): восемь моделей в слотах пиратов.

Зеркало `pirate_coin`, `pirate_bottle`, `pirate_ball`, `pirate_rock`, `pirate_barrel`,
`pirate_crate`, `pirate_chest`, `pirate_keg` из `lowpoly_meshes.py` и `space_mesh_items.py`.
У каждой модели одна часть `body` с той же точкой вращения и теми же габаритами, что у
пиратской: демки ставят их, крутят и кидают по этим числам. Плотный набор «продвинутых»
выходит из тех же функций (`lm.DENSE`).

Состав по `docs/specs/settings.md`: жетон на кофе, стакан кофе, скомканный лист (снаряд),
коробка бумаги, кулер, принтер, сейф, мяч-антистресс. Цвета из основы 16/32
(`office16.PALETTE`) через `office_mesh_chars`.

    python3 tools/office_mesh_items.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import office_mesh_chars as oc  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Цвета сеттинга: те же, что у персонажей (`office16.PALETTE`), и ступени картона и воды к ним.
K = oc.K
NAVY, SEA, SEA_L = oc.NAVY, oc.SEA, oc.SEA_L
AQUA, SKY = oc.AQUA, oc.SKY
WHITE, GREY, GREY_D = oc.WHITE, oc.GREY, oc.GREY_D
GOLD, BRASS, GOLD_L = oc.GOLD, oc.BRASS, oc.GOLD_L
METAL, METAL_L = oc.METAL, oc.METAL_L
DARK, DARK_L, DARK_D = oc.DARK, oc.DARK_L, oc.DARK_D
RED, RED_D = oc.RED, oc.RED_D
COFFEE = oc.COFFEE
GREEN, GREEN_D = rgb("4F9C86"), rgb("2A605C")
CARD, CARD_L, CARD_D = BRASS, rgb("D6A257"), rgb("8C5F28")


def disc(a, cx, cy, r, c):
    """Закрашенный круг с центром в долях пикселя."""
    for j in range(int(cy - r - 1), int(cy + r + 2)):
        for i in range(int(cx - r - 1), int(cx + r + 2)):
            if math.hypot(i - cx, j - cy) <= r:
                a.px(i, j, c)


def text_lines(a, x, y, w, rows, c=GREY_D):
    """Строчки текста на бумаге: штрихи разной длины через строку."""
    for k in range(rows):
        n = w - (k * 3) % 4
        a.rect(x, y + k * 2, n, 1, c)
        a.px(x + (k * 5) % max(n, 1), y + k * 2, WHITE)


def office_coin():
    """Жетон на кофе: золотой диск на ребре с рифлёным гуртом, на лице чашка с паром."""
    a = lm.Atlas(32, 32, 205)
    a.rect(0, 0, 16, 16, BRASS)
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            if d <= 5.0:
                a.px(i, j, GOLD)
            elif d <= 6.3:
                a.px(i, j, GOLD_L if i + j < 15 else mul(GOLD, 0.86))
    # Чашка на блюдце, ручка справа, две струйки пара.
    a.rect(5, 8, 5, 4, COFFEE), a.rect(5, 8, 5, 1, mul(COFFEE, 1.5)), a.rect(6, 11, 3, 1, mul(COFFEE, 0.7))
    a.px(10, 9, COFFEE), a.px(11, 9, COFFEE), a.px(11, 10, COFFEE), a.px(10, 11, COFFEE)
    a.rect(4, 12, 8, 1, BRASS)
    for x, y in ((6, 6), (6, 5), (7, 4), (9, 6), (9, 5), (8, 4)):
        a.px(x, y, mul(COFFEE, 1.5))
    a.px(3, 5, WHITE), a.px(4, 4, WHITE), a.px(5, 3, WHITE)
    a.noise(0, 0, 16, 16, 0.05)
    face = a.region(0, 0, 16, 16)
    # Гурт: частые насечки.
    lm.stripes(a, 16, 0, 16, 4, BRASS, GOLD, 1)
    a.rect(16, 0, 16, 1, GOLD_L)
    edge = a.region(16, 0, 16, 4)
    return lm.Model("coin", a).part(
        "body", (0.0, 0.35, 0.0),
        lm.at(lm.rot(lm.loft([(-0.04, 0.28, 0.28), (0.04, 0.28, 0.28)], edge, 12, math.pi / 12.0, caps=(face, face), flat=True),
                     rx=90.0), 0.0, 0.35))


def office_bottle():
    """Стакан кофе навынос: белый бумажный стакан расширяется кверху, картонная манжета с
    зелёным значком, тёмная крышка с бортиком. Мишень и снаряд метателя, размеры бутылки."""
    a = lm.Atlas(16, 16, 247)
    # Лента сверху вниз по звеньям тела: скат крышки, борт крышки, край стакана, верх, манжета, дно.
    a.rect(0, 0, 16, 12, WHITE)
    a.rect(0, 0, 16, 2, DARK_L), a.rect(0, 0, 16, 1, mul(DARK_L, 1.3))
    a.rect(0, 2, 16, 2, DARK), a.rect(0, 2, 16, 1, DARK_L), a.rect(0, 3, 16, 1, DARK_D)
    a.rect(0, 4, 16, 1, GREY)
    a.rect(0, 7, 16, 3, CARD), a.rect(0, 7, 16, 1, CARD_L), a.rect(0, 9, 16, 1, CARD_D)
    for x in range(0, 16, 2):
        a.px(x, 8, CARD_L)
    # Значок на манжете спереди (середина ленты) и сзади на шве.
    a.rect(7, 7, 2, 3, GREEN), a.px(7, 8, WHITE), a.px(8, 7, GREEN_D)
    a.rect(0, 10, 16, 2, WHITE), a.rect(0, 11, 16, 1, GREY)
    a.px(3, 5, GREY), a.px(12, 6, GREY), a.px(4, 10, GREY)
    a.shade(0, 0, 16, 12, 1.08, 0.9, 0.78)
    a.noise(0, 0, 16, 12, 0.04)
    body = a.region(0, 0, 16, 12)
    # Крышка сверху: тёмный пластик, питьевая прорезь и вдавленный кружок.
    a.rect(0, 12, 4, 4, DARK_L), a.rect(1, 13, 2, 2, DARK), a.px(1, 12, K), a.px(2, 12, K), a.px(3, 15, mul(DARK_L, 1.3))
    lid = a.region(0, 12, 4, 4)
    a.rect(4, 12, 4, 4, GREY), a.rect(5, 13, 2, 2, GREY_D)
    under = a.region(4, 12, 4, 4)
    return lm.Model("bottle", a).part(
        "body", (0.0, 0.25, 0.0),
        lm.loft([(0.0, 0.074, 0.074), (0.1, 0.084, 0.084), (0.28, 0.1, 0.1), (0.385, 0.108, 0.108),
                 (0.4, 0.12, 0.12), (0.44, 0.12, 0.12), (0.5, 0.092, 0.092)], body, 6, caps=(under, lid)))


def office_ball():
    """Скомканный лист: снаряд. Мятый гранёный ком белой бумаги со сгибами, обрывками строк и
    куском красного штампа."""
    a = lm.Atlas(16, 16, 249)
    a.rect(0, 0, 16, 16, WHITE)
    # Грани смятия: светлые и серые лоскуты, по их краям тёмные сгибы.
    for x, y, w, h, k in ((0, 0, 5, 4, 0.9), (9, 1, 6, 3, 0.84), (3, 6, 6, 4, 0.92), (11, 8, 5, 5, 0.86),
                          (0, 11, 6, 5, 0.82), (7, 12, 4, 4, 0.94)):
        a.rect(x, y, w, h, mul(WHITE, k))
        a.rect(x, y + h - 1, w, 1, GREY)
        a.px(x + w - 1, y, GREY_D)
    for i in range(6):
        a.px(5 + i, 4 + i // 2, GREY_D)
        a.px(15 - i, 5 + i, GREY)
    # Строчки текста и обрывок штампа.
    a.rect(1, 2, 3, 1, METAL), a.rect(4, 8, 4, 1, METAL), a.rect(1, 13, 3, 1, METAL), a.rect(12, 10, 3, 1, METAL)
    for x, y in ((10, 4), (11, 3), (12, 3), (13, 4), (13, 5), (12, 6), (11, 6), (10, 5)):
        a.px(x, y, RED)
    a.px(11, 5, RED_D), a.px(12, 4, RED_D)
    a.shade(0, 0, 16, 16, 1.1, 0.8, 0.92)
    a.noise(0, 0, 16, 16, 0.05)
    paper = a.region(0, 0, 16, 16)
    r = 0.18
    rings = [(0.015, 0.075, 0.065, 0.01, 0.0), (0.08, 0.165, 0.14, -0.02, 0.012), (0.185, 0.165, 0.18, 0.016, -0.012),
             (0.29, 0.15, 0.125, -0.012, 0.018), (0.35, 0.06, 0.078, 0.012, 0.0)]
    return lm.Model("ball", a).part("body", (0.0, r, 0.0), lm.loft(rings, paper, 7, 0.3, caps=(paper, paper), flat=True))


def office_rock():
    """Коробка бумаги: открытая картонная коробка с отогнутыми клапанами, из неё торчит стопка
    листов; рядом две пачки бумаги в обёртке с синей полосой."""
    a = lm.Atlas(32, 32, 207)
    # Бока коробки: четыре грани по 8, скотч, прорези ручек на торцах, наклейка спереди.
    a.rect(0, 0, 32, 10, CARD)
    for x in (0, 8, 16, 24):
        a.rect(x, 0, 1, 10, CARD_L), a.rect(x + 7, 0, 1, 10, CARD_D)
        a.rect(x, 0, 8, 1, CARD_L)
        for y in (3, 6):
            a.px(x + 2 + (y % 4), y, CARD_D), a.px(x + 5, y + 1, CARD_L)
    for x in (2, 18):
        a.rect(x, 3, 4, 2, K), a.rect(x, 3, 4, 1, CARD_D)
    for x in (11, 27):
        a.rect(x, 0, 2, 10, mul(CARD_L, 1.12))
    a.rect(9, 3, 6, 5, WHITE), a.rect(10, 4, 4, 1, SEA), a.rect(10, 6, 3, 1, GREY_D), a.rect(9, 7, 6, 1, GREY)
    a.rect(25, 6, 3, 2, RED), a.px(26, 6, WHITE)
    a.shade(0, 0, 32, 10, 1.08, 0.82, 1.0)
    a.noise(0, 0, 32, 10, 0.06)
    side = a.region(0, 0, 32, 10)
    # Верх стопки: лист со строчками, из-под него видны съехавшие листы.
    a.rect(0, 10, 12, 10, GREY)
    a.rect(0, 10, 11, 9, WHITE)
    a.rect(1, 11, 5, 1, SEA)
    text_lines(a, 1, 13, 8, 3)
    a.rect(8, 17, 2, 1, RED)
    top = a.region(0, 10, 12, 10)
    # Торец стопки: слои листов.
    for j in range(4):
        a.rect(12, 10 + j, 16, 1, WHITE if j % 2 == 0 else GREY)
    a.px(15, 11, GREY_D), a.px(22, 13, GREY_D), a.px(26, 11, GREY_D)
    stack = a.region(12, 10, 16, 4)
    # Нутро и дно коробки.
    a.rect(28, 10, 4, 4, CARD_D), a.px(29, 11, mul(CARD_D, 0.75)), a.px(30, 12, mul(CARD_D, 0.75))
    inner = a.region(28, 10, 4, 4)
    # Клапан: картон со сгибом у основания и следом скотча.
    a.rect(0, 20, 8, 6, CARD), a.rect(0, 20, 8, 1, CARD_L), a.rect(0, 25, 8, 1, CARD_D)
    a.rect(3, 20, 2, 3, mul(CARD_L, 1.12)), a.px(1, 23, CARD_D), a.px(6, 22, CARD_D)
    a.noise(0, 20, 8, 6, 0.06)
    flap = a.region(0, 20, 8, 6)
    # Пачка бумаги: белая обёртка, синяя полоса с названием, на торцах складки.
    a.rect(12, 14, 16, 4, WHITE), a.rect(12, 15, 16, 2, SEA), a.rect(12, 15, 16, 1, SEA_L)
    for x in (13, 21):
        a.rect(x, 15, 3, 1, WHITE)
    a.rect(12, 17, 16, 1, GREY)
    ream_side = a.region(12, 14, 16, 4)
    a.rect(12, 18, 8, 8, WHITE), a.rect(12, 20, 8, 3, SEA), a.rect(12, 20, 8, 1, SEA_L)
    a.rect(14, 21, 4, 1, WHITE), a.rect(12, 25, 8, 1, GREY), a.px(13, 18, GREY), a.px(18, 24, GREY)
    ream_top = a.region(12, 18, 8, 8)
    bx, bw, bh, bd = -0.06, 0.78, 0.46, 0.66
    tris = lm.at(lm.box((bw, bh, bd), side, inner, inner), bx, bh / 2.0)
    # Стопка листов выше кромки, чуть повёрнута.
    tris += lm.at(lm.rot(lm.box((0.64, 0.2, 0.52), stack, top, None), ry=5.0), bx, 0.5)
    # Клапаны спереди и сзади отогнуты наружу и вниз, на торцах стоят торчком.
    x0, x1 = bx - bw / 2.0, bx + bw / 2.0
    for s in (-1.0, 1.0):
        z0, z1 = s * bd / 2.0, s * (bd / 2.0 + 0.16)
        tris += lm.quad((x0, bh, z0), (x1, bh, z0), (x1, bh - 0.1, z1), (x0, bh - 0.1, z1), flap)
    for s, xe in ((-1.0, x0), (1.0, x1)):
        tris += lm.quad((xe, bh, -bd / 2.0), (xe, bh, bd / 2.0), (xe + s * 0.07, bh + 0.15, bd / 2.0), (xe + s * 0.07, bh + 0.15, -bd / 2.0), flap)
    # Две пачки рядом: нижняя лежит, верхняя съехала.
    tris += lm.at(lm.rot(lm.box((0.3, 0.12, 0.42), ream_side, ream_top, inner), ry=24.0), 0.5, 0.06, 0.3)
    tris += lm.at(lm.rot(lm.box((0.3, 0.12, 0.42), ream_side, ream_top, None), ry=-8.0), 0.51, 0.18, 0.29)
    return lm.Model("rock", a).part("body", (0.0, 0.0, 0.0), tris)


def office_barrel():
    """Кулер: белая тумба с синим и красным краниками и поддоном, сверху перевёрнутая синяя
    бутыль с рёбрами и уровнем воды."""
    a = lm.Atlas(32, 32, 209)
    # Тумба: четыре грани по 8. Спереди (вторая четверть) ниша с краниками и поддон.
    a.rect(0, 0, 32, 12, WHITE)
    for x in (0, 8, 16, 24):
        a.rect(x, 0, 1, 12, WHITE), a.rect(x + 7, 0, 1, 12, GREY)
        a.rect(x, 0, 8, 1, GREY), a.rect(x, 11, 8, 1, GREY_D)
    a.rect(9, 2, 6, 5, GREY), a.rect(9, 2, 6, 1, GREY_D), a.rect(9, 6, 6, 1, METAL)
    a.rect(10, 3, 1, 2, SEA), a.rect(13, 3, 1, 2, RED_D)
    a.rect(10, 8, 4, 2, GREY), a.px(10, 9, AQUA), a.px(13, 9, RED)
    # Торцы и спина: жалюзи вентиляции.
    for x in (1, 17, 25):
        for y in (3, 5, 7):
            a.rect(x + 1, y, 4, 1, GREY_D)
            a.rect(x + 1, y + 1, 4, 1, WHITE)
    a.rect(26, 9, 3, 1, GOLD)
    a.shade(0, 0, 32, 12, 1.06, 0.84, 1.0)
    a.noise(0, 0, 32, 12, 0.03)
    side = a.region(0, 0, 32, 12)
    # Бутыль: лента сверху вниз (перевёрнута горлом вниз): дно, пустой верх, вода с рёбрами, плечи, горло.
    a.rect(0, 12, 32, 10, AQUA)
    a.rect(0, 12, 32, 2, SKY), a.rect(0, 14, 32, 1, WHITE)
    a.rect(0, 15, 32, 1, SEA_L)
    for y in (17, 19):
        a.rect(0, y, 32, 1, SEA_L)
    a.rect(0, 20, 32, 2, SEA)
    for x in (4, 20):
        a.rect(x, 13, 2, 7, SKY), a.rect(x, 15, 1, 4, WHITE)
    a.rect(12, 16, 5, 3, WHITE), a.rect(13, 17, 3, 1, SEA)
    a.shade(0, 12, 32, 10, 1.1, 0.9, 0.8)
    a.noise(0, 12, 32, 10, 0.04)
    jug = a.region(0, 12, 32, 10)
    # Дно бутыли сверху: концентрические кольца.
    a.rect(0, 22, 8, 8, AQUA)
    for i in range(8):
        for j in range(8):
            d = math.hypot(i - 3.5, j - 3.5)
            if 1.5 < d <= 2.6:
                a.px(i, 22 + j, SKY)
    a.px(3, 25, SEA_L), a.px(4, 26, SEA_L), a.px(2, 23, WHITE)
    jug_top = a.region(0, 22, 8, 8)
    # Крышка тумбы: кольцо гнезда под горло.
    a.rect(8, 22, 8, 8, WHITE), a.rect(8, 22, 8, 1, GREY), a.rect(8, 29, 8, 1, GREY)
    disc(a, 11.5, 25.5, 2.8, GREY_D)
    disc(a, 11.5, 25.5, 1.8, SEA)
    top = a.region(8, 22, 8, 8)
    a.rect(16, 22, 4, 4, SEA), a.rect(16, 22, 4, 1, AQUA), a.px(17, 24, SKY)
    tap_cold = a.region(16, 22, 4, 4)
    a.rect(20, 22, 4, 4, RED_D), a.rect(20, 22, 4, 1, RED), a.px(21, 24, WHITE)
    tap_hot = a.region(20, 22, 4, 4)
    a.rect(24, 22, 4, 4, GREY_D), a.rect(24, 22, 4, 1, GREY), a.px(25, 24, METAL), a.px(27, 24, METAL)
    tray = a.region(24, 22, 4, 4)
    a.rect(28, 22, 4, 4, DARK), a.px(29, 23, METAL)
    under = a.region(28, 22, 4, 4)
    tris = lm.at(lm.box((0.62, 0.5, 0.58), side, top, under), 0.0, 0.25)
    tris += lm.loft([(0.5, 0.11, 0.11), (0.54, 0.12, 0.12), (0.6, 0.28, 0.28), (0.7, 0.29, 0.29),
                     (0.81, 0.29, 0.29), (0.86, 0.24, 0.24)], jug, 8, caps=(None, jug_top))
    # Краники торчат из ниши, под ними поддон.
    tris += lm.at(lm.box((0.07, 0.09, 0.08), tap_cold, tap_cold, tap_cold), -0.11, 0.37, -0.33)
    tris += lm.at(lm.box((0.07, 0.09, 0.08), tap_hot, tap_hot, tap_hot), 0.11, 0.37, -0.33)
    tris += lm.at(lm.box((0.36, 0.03, 0.1), tray, tray, tray), 0.0, 0.2, -0.34)
    return lm.Model("barrel", a).part("body", (0.0, 0.0, 0.0), tris)


def office_crate():
    """Принтер: светлый напольный аппарат. Спереди пульт с голубым экраном, щель с листом на
    лотке и два ящика бумаги, на торцах жалюзи, сверху крышка сканера."""
    a = lm.Atlas(32, 32, 251)
    a.rect(0, 0, 32, 16, WHITE)
    for x in (0, 8, 16, 24):
        a.rect(x, 0, 1, 16, WHITE), a.rect(x + 7, 0, 1, 16, GREY_D)
        a.rect(x, 0, 8, 2, GREY), a.rect(x, 0, 8, 1, WHITE)
        a.rect(x, 14, 8, 2, DARK_L), a.rect(x, 14, 8, 1, METAL)
    # Перед (вторая четверть ленты): пульт, щель выдачи, два ящика с ручками.
    a.rect(9, 2, 6, 3, DARK), a.rect(10, 3, 2, 1, AQUA), a.px(10, 3, SKY), a.px(13, 3, GREEN), a.px(14, 3, RED)
    a.rect(9, 6, 6, 2, K), a.rect(10, 7, 4, 1, WHITE)
    for y in (9, 12):
        a.rect(9, y, 6, 2, GREY), a.rect(9, y, 6, 1, WHITE), a.rect(11, y + 1, 2, 1, DARK_L)
    a.rect(9, 11, 6, 1, GREY_D)
    # Торцы: жалюзи и лючок; спина: решётка, гнездо и наклейка.
    for x in (1, 17):
        for y in (4, 6, 8):
            a.rect(x + 1, y, 4, 1, GREY_D)
        a.rect(x, 11, 5, 2, GREY), a.px(x + 4, 12, DARK_L)
    for y in (3, 5, 7, 9):
        a.rect(26, y, 4, 1, GREY_D)
    a.rect(25, 11, 2, 2, DARK), a.rect(28, 11, 2, 2, GOLD)
    a.shade(0, 0, 32, 16, 1.06, 0.84, 1.0)
    a.noise(0, 0, 32, 16, 0.03)
    side = a.region(0, 0, 32, 16)
    # Верх: крышка сканера с ручкой, полоса пульта к переду, жёлтый стикер.
    a.rect(0, 16, 16, 16, WHITE)
    a.rect(0, 16, 16, 1, GREY), a.rect(0, 31, 16, 1, GREY_D), a.rect(0, 16, 1, 16, GREY), a.rect(15, 16, 1, 16, GREY_D)
    a.rect(2, 21, 12, 9, GREY), a.rect(2, 21, 12, 1, WHITE), a.rect(2, 29, 12, 1, GREY_D), a.rect(13, 21, 1, 9, GREY_D)
    a.rect(6, 27, 4, 1, METAL)
    a.rect(1, 17, 14, 3, DARK), a.rect(2, 18, 4, 1, AQUA), a.px(8, 18, GREEN), a.px(10, 18, RED), a.px(12, 18, GREY)
    a.rect(10, 23, 3, 3, GOLD), a.px(11, 24, BRASS)
    a.noise(0, 16, 16, 16, 0.03)
    top = a.region(0, 16, 16, 16)
    # Лист на лотке и пластик лотка.
    a.rect(16, 16, 8, 8, WHITE), a.rect(16, 23, 8, 1, GREY)
    a.rect(17, 17, 4, 1, SEA)
    text_lines(a, 17, 19, 6, 2)
    sheet = a.region(16, 16, 8, 8)
    a.rect(24, 16, 4, 4, GREY_D), a.rect(24, 16, 4, 1, GREY)
    plastic = a.region(24, 16, 4, 4)
    a.rect(28, 16, 4, 4, DARK)
    under = a.region(28, 16, 4, 4)
    tris = lm.at(lm.box((0.85, 0.85, 0.85), side, top, under), 0.0, 0.425)
    # Лоток выдачи: полка под щелью и лист на ней.
    tris += lm.at(lm.box((0.5, 0.03, 0.16), plastic, plastic, plastic), 0.0, 0.47, -0.49)
    tris += lm.quad((0.2, 0.5, -0.42), (-0.2, 0.5, -0.42), (-0.2, 0.49, -0.6), (0.2, 0.49, -0.6), sheet)
    return lm.Model("crate", a).part("body", (0.0, 0.0, 0.0), tris)


def office_chest():
    """Сейф: стальной ящик на ножках. Спереди утопленная дверца с петлями, выпуклый лимб с
    рисками и золотая ручка; сверху забытый стикер и след от кружки."""
    a = lm.Atlas(64, 32, 213)
    # Бока: четыре грани по 16, рама с заклёпками. Перед это вторая четверть ленты.
    a.rect(0, 0, 64, 16, METAL)
    for x in (0, 16, 32, 48):
        a.rect(x, 0, 16, 1, METAL_L), a.rect(x, 15, 16, 1, DARK_L)
        a.rect(x, 0, 1, 16, METAL_L), a.rect(x + 15, 0, 1, 16, DARK_L)
        for px, py in ((2, 2), (13, 2), (2, 13), (13, 13)):
            a.px(x + px, py, WHITE), a.px(x + px, py + 1, DARK)
    for x in (0, 32, 48):
        a.rect(x + 3, 4, 10, 8, mul(METAL, 0.9)), a.rect(x + 3, 4, 10, 1, DARK_L), a.rect(x + 3, 11, 10, 1, METAL_L)
    a.rect(52, 6, 6, 3, WHITE), a.rect(53, 7, 4, 1, K)
    # Дверца: тёмный паз вокруг, светлая плита, петли слева, под лимбом и ручкой тени.
    a.rect(18, 2, 12, 12, K)
    a.rect(19, 3, 10, 10, METAL_L), a.rect(19, 3, 10, 1, WHITE), a.rect(19, 12, 10, 1, METAL), a.rect(28, 3, 1, 10, METAL)
    a.rect(17, 4, 2, 2, DARK), a.rect(17, 10, 2, 2, DARK)
    disc(a, 22.5, 7.5, 2.6, DARK_L)
    a.rect(26, 5, 2, 6, DARK_L)
    a.rect(20, 11, 3, 1, GOLD)
    a.shade(0, 0, 64, 16, 1.08, 0.82, 1.0)
    a.noise(0, 0, 64, 16, 0.04)
    side = a.region(0, 0, 64, 16)
    # Верх: стальной лист, жёлтый стикер со строчками и кольцо от кружки.
    a.rect(0, 16, 24, 12, METAL_L)
    a.rect(0, 16, 24, 1, WHITE), a.rect(0, 27, 24, 1, METAL), a.rect(0, 16, 1, 12, WHITE), a.rect(23, 16, 1, 12, METAL)
    for px, py in ((2, 18), (21, 18), (2, 25), (21, 25)):
        a.px(px, py, DARK)
    a.rect(4, 19, 6, 6, GOLD), a.rect(4, 19, 6, 1, GOLD_L), a.rect(5, 21, 4, 1, BRASS), a.rect(5, 23, 3, 1, BRASS)
    for i in range(24):
        for j in range(12):
            d = math.hypot(i - 16.5, j - 5.5)
            if 2.4 < d <= 3.3 and (i + j) % 5 != 0:
                a.px(i, 16 + j, mul(COFFEE, 1.4))
    a.noise(0, 16, 24, 12, 0.04)
    top = a.region(0, 16, 24, 12)
    # Лимб: чёрный диск с белыми рисками и стрелкой, стальной обод.
    a.rect(24, 16, 8, 8, METAL)
    disc(a, 27.5, 19.5, 3.6, GREY)
    disc(a, 27.5, 19.5, 2.7, DARK)
    for px, py in ((27, 17), (28, 17), (25, 19), (30, 20), (27, 22), (28, 22)):
        a.px(px, py, WHITE)
    a.rect(27, 19, 2, 2, GREY), a.px(27, 19, WHITE), a.px(28, 18, RED)
    dial = a.region(24, 16, 8, 8)
    a.rect(24, 24, 8, 2, GREY), a.rect(24, 24, 8, 1, WHITE), a.px(26, 25, METAL), a.px(30, 25, METAL)
    dial_rim = a.region(24, 24, 8, 2)
    # Ручка: золотой брусок.
    a.rect(32, 16, 4, 8, GOLD), a.rect(32, 16, 1, 8, GOLD_L), a.rect(35, 16, 1, 8, BRASS), a.rect(32, 23, 4, 1, BRASS)
    a.px(33, 17, WHITE)
    grip = a.region(32, 16, 4, 8)
    a.rect(36, 16, 4, 4, DARK), a.px(37, 17, DARK_L)
    under = a.region(36, 16, 4, 4)
    a.rect(40, 16, 4, 4, DARK_L), a.rect(40, 16, 4, 1, METAL), a.rect(40, 19, 4, 1, K)
    foot = a.region(40, 16, 4, 4)
    w, h, d, leg = 0.8, 0.54, 0.46, 0.06
    tris = lm.at(lm.box((w, h, d), side, top, under), 0.0, leg + h / 2.0)
    for sx in (-1.0, 1.0):
        for sz in (-1.0, 1.0):
            tris += lm.at(lm.box((0.12, leg + 0.02, 0.1), foot, None, under), sx * 0.31, (leg + 0.02) / 2.0, sz * 0.16)
    # Лимб и ручка выступают из дверцы: дверца на ленте занимает доли 3/16..13/16 грани.
    front = -d / 2.0
    tris += lm.at(lm.rot(lm.loft([(0.0, 0.085, 0.085), (0.04, 0.075, 0.075)], dial_rim, 8, math.pi / 8.0, caps=(None, dial)),
                         rx=-90.0), 0.1, leg + h * 0.53, front)
    tris += lm.at(lm.box((0.05, 0.2, 0.05), grip, grip, grip), -0.17, leg + h * 0.5, front - 0.025)
    return lm.Model("chest", a).part("body", (0.0, 0.0, 0.0), tris)


def office_keg():
    """Мяч-антистресс: жёлтый поролоновый шар с улыбкой, летит и крутится."""
    a = lm.Atlas(16, 16, 269)
    a.rect(0, 0, 16, 12, GOLD)
    # Рожица спереди (середина ленты): глаза, улыбка с уголками, румянец; сзади шов и клеймо.
    # Лента оборачивает весь шар, поэтому рожица узкая: иначе глаза расползаются на полшара.
    a.rect(6, 4, 1, 2, K), a.rect(9, 4, 1, 2, K)
    a.rect(6, 8, 4, 1, K), a.px(5, 7, K), a.px(10, 7, K), a.rect(7, 9, 2, 1, RED_D)
    a.px(4, 6, mul(RED, 1.1)), a.px(11, 6, mul(RED, 1.1))
    a.rect(0, 0, 1, 12, BRASS), a.rect(15, 0, 1, 12, BRASS)
    a.rect(13, 9, 2, 1, BRASS), a.px(1, 4, GOLD_L), a.px(2, 3, GOLD_L)
    # Поры поролона.
    for x, y in ((2, 9), (7, 1), (12, 2), (13, 5), (3, 1), (8, 11), (1, 7)):
        a.px(x, y, mul(GOLD, 0.84))
    a.shade(0, 0, 16, 12, 1.14, 0.78, 0.9)
    a.noise(0, 0, 16, 12, 0.04)
    side = a.region(0, 0, 16, 12)
    a.rect(0, 12, 4, 4, GOLD), a.px(1, 13, GOLD_L), a.px(2, 14, mul(GOLD, 0.84))
    cap = a.region(0, 12, 4, 4)
    r = 0.15
    rings = [(r - r * math.cos(t), r * math.sin(t), r * math.sin(t)) for t in (0.4, 1.05, math.pi / 2.0, math.pi - 1.05, math.pi - 0.4)]
    return lm.Model("keg", a).part("body", (0.0, 0.15, 0.0), lm.loft(rings, side, 6, caps=(cap, cap)))


MODELS = [office_coin, office_bottle, office_ball, office_rock, office_barrel, office_crate, office_chest, office_keg]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], [f() for f in MODELS])
    for f in MODELS:
        m = f()
        print("%-7s частей %d, треугольников %d, атлас %d×%d" % (m.name, len(m.parts), m.tris(), m.atlas.w, m.atlas.h))
