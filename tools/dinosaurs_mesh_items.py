#!/usr/bin/env python3
"""Мелкий реквизит «Динозавров» для low poly и «продвинутых» (#144): восемь моделей в слотах пиратов.

Зеркало `space_mesh_items.py` и через него `pirate_coin`, `pirate_bottle`, `pirate_ball`,
`pirate_rock`, `pirate_barrel`, `pirate_crate`, `pirate_chest`, `pirate_keg` из
`lowpoly_meshes.py`. У каждой модели одна часть `body` с той же точкой вращения и теми же
габаритами, что у пиратской: демки ставят их, крутят и кидают по этим числам. Плотный набор
«продвинутых» выходит из тех же функций (`lm.DENSE`). Состав по столбцу «Динозавры» в
`docs/specs/settings.md`: монета это аммонит, бутылка это кокос с соломинкой, ядро это камень
для рогатки, камень это глыба лавы в горячих трещинах, бочка это гигантская кость торчком,
ящик это плетёная корзина, сундук это гнездо с яйцами, бочонок-мяч это яйцо динозавра. Цвета
из основы (`dinosaurs_mesh_chars`, палитра `dinosaurs16.PALETTE`).

    python3 tools/dinosaurs_mesh_items.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import dinosaurs_mesh_chars as dmc  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Цвета сеттинга: те же, что у персонажей, и свои тона прутьев, лавы и скорлупы.
BLACK = dmc.BLACK
BONE, BONE_D, BONE_DD = dmc.BONE, dmc.BONE_D, dmc.BONE_DD
HIDE, HIDE_D, HIDE_L = dmc.HIDE, dmc.HIDE_D, dmc.HIDE_L
HAIR, HAIR_D, HAIR_L = dmc.HAIR, dmc.HAIR_D, dmc.HAIR_L
GOLD, BRASS = dmc.BELLY, dmc.BELLY_D
SKIN, CLAY = dmc.SKIN, dmc.CLAY
LEAF, LEAF_D, LEAF_L = dmc.SCALE, dmc.SCALE_D, dmc.SCALE_L
STONE, STONE_D = dmc.STONE, dmc.STONE_D
TEAL, TEAL_D = dmc.TEAL, dmc.TEAL_D
STONE_L = rgb("A8949A")
CRUST = rgb("30262A")
STRAW = rgb("E8B45C")
GLOW = rgb("FFF0A0")


def weave(a, x, y, w, h, light=STRAW, mid=BRASS, dark=HAIR_L, step=4):
    """Плетение: лозы идут то поверх, то под стойками, шахматкой по клеткам `step`×2."""
    for j in range(h):
        row = j // 2
        for i in range(w):
            cell = i // step
            over = (cell + row) % 2 == 0
            c = light if over else mid
            if j % 2 == 1:
                c = mul(c, 0.8)
            if i % step == 0:
                # Стойка: сплошная вертикаль, лоза поверх неё через ряд.
                c = mul(light, 1.1) if over and j % 2 == 0 else dark
            a.px(x + i, y + j, c)


def speckles(a, x, y, w, h, count, colors):
    """Крапины скорлупы и поры кости: одиночные пиксели и пары."""
    for _ in range(count):
        i, j = x + a.rng.randrange(w), y + a.rng.randrange(h)
        c = colors[a.rng.randrange(len(colors))]
        a.px(i, j, c)
        if a.rng.random() < 0.35 and i + 1 < x + w:
            a.px(i + 1, j, c)


def egg_shell(a, x, y, w, h, count):
    """Скорлупа: костяная, к низу теплее, в рыжих и тёмных крапинах, блик слева сверху."""
    a.rect(x, y, w, h, BONE)
    a.rect(x, y + h * 2 // 3, w, h - h * 2 // 3, mul(BONE, 0.93))
    speckles(a, x, y + 1, w, h - 1, count, (HIDE, HIDE_D, HIDE_D, HAIR_L))
    a.shade(x, y, w, h, 1.08, 0.8, 0.82)


def dinosaurs_coin():
    """Аммонит-бонус: золотистая раковина-диск стоит на ребре и вращается. На щеках спираль
    завитка, по ободу рёбра, сбоку снизу раструб устья."""
    a = lm.Atlas(32, 32, 305)
    # Щека 24×24: спираль от пупка к краю, бороздка тёмная, витки в поперечных рёбрах.
    for j in range(24):
        for i in range(24):
            dx, dy = i - 11.5, j - 11.5
            r = math.hypot(dx, dy)
            th = (math.atan2(dy, dx) + 2.0 * math.pi) % (2.0 * math.pi)
            t = (r / 5.6 - th / (2.0 * math.pi)) % 1.0
            if r < 1.3:
                c = HAIR
            elif t < 0.3:
                c = HIDE_D if t < 0.16 else BRASS
            else:
                rib = int(th * 16.0 / (2.0 * math.pi)) % 2
                c = mul(GOLD, 1.12 if t > 0.66 else 1.0) if rib or r < 5.0 else mul(GOLD, 0.86)
            a.px(i, j, c)
    for x, y in ((6, 5), (7, 4), (16, 6), (5, 14)):
        a.px(x, y, GLOW)
    a.shade(0, 0, 24, 24, 1.12, 0.8, 0.95)
    a.noise(0, 0, 24, 24, 0.05)
    face = a.region(0, 0, 24, 24)
    # Обод 32×8: поперечные рёбра внешнего витка, по килю тёмная бороздка.
    for i in range(32):
        k = (1.12, 0.95, 0.74)[i % 3]
        a.rect(i, 24, 1, 8, mul(GOLD, k))
    a.rect(0, 27, 32, 1, BRASS), a.rect(0, 28, 32, 1, mul(BRASS, 0.8))
    a.rect(0, 24, 32, 1, mul(GOLD, 1.2))
    a.noise(0, 24, 32, 8, 0.05)
    rim = a.region(0, 24, 32, 8)
    # Устье: светлая губа и тёмный зев.
    a.rect(24, 0, 8, 8, BONE), a.rect(25, 1, 6, 6, HIDE_D), a.rect(26, 2, 4, 4, HAIR_D)
    mouth = a.region(24, 0, 8, 8)
    a.rect(24, 8, 8, 8, GOLD)
    for i in range(0, 8, 2):
        a.rect(24 + i, 8, 1, 8, BRASS)
    a.rect(24, 14, 8, 2, BONE)
    lip = a.region(24, 8, 8, 8)
    disc = lm.rot(lm.loft([(-0.07, 0.19, 0.19), (-0.045, 0.27, 0.27), (0.045, 0.27, 0.27), (0.07, 0.19, 0.19)],
                          rim, 10, caps=(face, face)), rx=90.0)
    # Раструб устья: конец внешнего витка уходит вниз по касательной справа.
    horn = lm.loft([(0.0, 0.1, 0.075), (0.07, 0.085, 0.065), (0.2, 0.06, 0.05)], lip, 5, caps=(mouth, None))
    return lm.Model("coin", a).part("body", (0.0, 0.35, 0.0), lm.at(disc, 0.0, 0.35) + lm.at(horn, 0.215, 0.1))


def dinosaurs_bottle():
    """Кокос с соломинкой: волосатый орех со срезанной макушкой, белая мякоть, тростинка и лист.
    Мишень и снаряд метателя, размеры бутылки."""
    a = lm.Atlas(16, 16, 347)
    # Скорлупа 16×12: волокна вдоль, три глазка спереди, светлая кромка среза.
    a.rect(0, 0, 16, 12, HAIR)
    for i in range(16):
        k = (1.0, 1.25, 0.8, 1.1, 0.7)[(i * 3) % 5]
        a.rect(i, 1, 1, 11, mul(HAIR, k))
    for x, y in ((1, 3), (4, 7), (11, 4), (13, 8), (6, 10), (15, 2), (9, 9)):
        a.px(x, y, HAIR_L), a.px(x, y + 1, HAIR_D)
    a.px(7, 4, HAIR_D), a.px(9, 4, HAIR_D), a.px(8, 6, HAIR_D)
    a.rect(0, 0, 16, 1, BONE), a.rect(0, 1, 16, 1, BONE_D)
    a.shade(0, 2, 16, 10, 1.15, 0.7, 0.8)
    a.noise(0, 2, 16, 10, 0.08)
    shell = a.region(0, 0, 16, 12)
    # Срез: кольцо мякоти, в середине кокосовая вода.
    a.rect(0, 12, 4, 4, BONE), a.rect(1, 13, 2, 2, TEAL), a.px(1, 13, GLOW)
    flesh = a.region(0, 12, 4, 4)
    a.rect(4, 12, 4, 4, HAIR_D), a.px(5, 13, HAIR)
    under = a.region(4, 12, 4, 4)
    # Тростинка в поперечных узлах и лист.
    a.rect(8, 12, 4, 4, STRAW), a.rect(8, 13, 4, 1, BRASS), a.rect(8, 15, 4, 1, HIDE)
    reed = a.region(8, 12, 4, 4)
    a.rect(12, 12, 4, 4, LEAF), a.rect(12, 13, 4, 1, LEAF_L), a.rect(12, 15, 4, 1, LEAF_D)
    leaf = a.region(12, 12, 4, 4)
    body = lm.loft([(0.0, 0.055, 0.055), (0.04, 0.1, 0.1), (0.13, 0.12, 0.12), (0.24, 0.115, 0.115), (0.31, 0.085, 0.085)],
                   shell, 6, caps=(under, flesh))
    straw = lm.loft([(0.29, 0.016, 0.016, 0.02, 0.0), (0.5, 0.016, 0.016, 0.075, -0.01)], reed, 4, caps=(None, reed))
    blade = lm.quad((-0.03, 0.33, 0.035), (-0.15, 0.43, 0.01), (-0.16, 0.41, -0.01), (-0.03, 0.3, -0.035), leaf)
    return lm.Model("bottle", a).part("body", (0.0, 0.25, 0.0), body + straw + blade)


def dinosaurs_ball():
    """Камень для рогатки: снаряд. Гранёный серый голыш со сколами и светлой жилой."""
    a = lm.Atlas(16, 16, 349)
    a.rect(0, 0, 16, 16, STONE)
    for _ in range(18):
        x, y = a.rng.randrange(16), a.rng.randrange(16)
        a.rect(x, y, a.rng.randrange(1, 3), 1, STONE_D if a.rng.random() < 0.5 else STONE_L)
    # Светлая жила наискось и скол с белым краем.
    for i in range(16):
        a.px(i, (5 + i // 3) % 16, STONE_L)
        if i % 5 == 1:
            a.px(i, (5 + i // 3) % 16, BONE)
    a.rect(9, 10, 4, 3, STONE_D), a.rect(9, 10, 4, 1, BONE_D), a.px(9, 11, BLACK)
    a.rect(2, 11, 2, 2, STONE_D), a.px(2, 11, STONE_L)
    a.shade(0, 0, 16, 16, 1.25, 0.7, 0.9)
    a.noise(0, 0, 16, 16, 0.08)
    stone = a.region(0, 0, 16, 16)
    r = 0.18
    rings = [(0.02, 0.08, 0.1), (0.1, 0.17, 0.15, 0.01, 0.0), (0.2, 0.18, 0.17, -0.01, 0.01),
             (0.3, 0.13, 0.15, 0.015, -0.01), (0.36, 0.05, 0.07, 0.02, 0.0)]
    return lm.Model("ball", a).part("body", (0.0, r, 0.0), lm.loft(rings, stone, 6, 0.4, caps=(stone, stone), flat=True))


def dinosaurs_rock():
    """Глыба лавы: тёмная запёкшаяся корка в сетке раскалённых трещин, острая верхушка, рядом
    обломок."""
    a = lm.Atlas(32, 32, 307)
    a.rect(0, 0, 32, 32, CRUST)
    for _ in range(50):
        x, y = a.rng.randrange(32), a.rng.randrange(32)
        a.rect(x, y, a.rng.randrange(1, 4), 1, STONE_D if a.rng.random() < 0.65 else STONE)
    # Плиты корки: светлая кромка сверху у нескольких пластов.
    for x, y, w in ((2, 4, 6), (14, 2, 7), (24, 8, 6), (5, 17, 7), (18, 20, 8), (10, 27, 6), (26, 26, 5)):
        a.rect(x, y, w, 1, STONE)
        a.rect(x + 1, y + 1, w - 1, 1, STONE_D)
    a.shade(0, 0, 32, 32, 1.2, 0.8, 0.9)
    a.noise(0, 0, 32, 32, 0.1)
    # Трещины поверх светотени, чтобы жар не гас: ломаные с жёлтой сердцевиной, внизу шире.
    for x0, y0, steps, dx in ((3, 0, 30, 1), (15, 6, 26, -1), (22, 0, 20, 1), (29, 12, 20, -1), (9, 14, 18, 1)):
        x = x0
        for s in range(steps):
            y = y0 + s
            if y >= 32:
                break
            if a.rng.random() < 0.45:
                x += dx if a.rng.random() < 0.7 else -dx
            x %= 32
            a.px(x, y, HIDE if y < 20 else GOLD)
            if y >= 12:
                a.px((x + 1) % 32, y, HIDE_D if y < 22 else HIDE)
            if y >= 24:
                a.px((x - 1) % 32, y, HIDE)
            if s % 6 == 3:
                a.px(x, y, GLOW)
    # Поперечные перемычки между трещинами.
    for x, y, w in ((4, 10, 5), (16, 16, 6), (23, 23, 6), (8, 25, 4)):
        a.rect(x, y, w, 1, HIDE_D)
        a.px(x + w // 2, y, GOLD)
    stone = a.region(0, 0, 32, 32)
    return lm.Model("rock", a).part(
        "body", (0.0, 0.0, 0.0),
        lm.loft([(0.0, 0.5, 0.52), (0.18, 0.56, 0.46, 0.04, -0.02), (0.44, 0.36, 0.3, -0.05, 0.05), (0.6, 0.2, 0.2, 0.02, 0.0),
                 (0.72, 0.05, 0.05, -0.1, 0.03)],
                stone, 6, 0.5, caps=(None, stone), flat=True)
        + lm.at(lm.loft([(0.0, 0.28, 0.3), (0.16, 0.24, 0.2, 0.02, 0.0), (0.36, 0.04, 0.05, 0.06, 0.02)], stone, 5, 0.9,
                        caps=(None, stone), flat=True),
                0.5, 0.0, 0.3))


def dinosaurs_barrel():
    """Гигантская кость торчком: толстый стержень в трещинах с обмоткой из шкуры, сверху и
    снизу по два бугра сустава. Габариты бочки."""
    a = lm.Atlas(32, 32, 309)
    # Стержень 32×24: волокна кости вдоль, поры, трещина, посередине обмотка шкурой.
    a.rect(0, 0, 32, 24, BONE)
    for i in range(32):
        k = (1.0, 0.94, 1.04, 0.9)[(i * 5) % 4]
        a.rect(i, 0, 1, 24, mul(BONE, k))
    for x, y, h in ((3, 1, 6), (9, 15, 7), (14, 2, 4), (21, 16, 6), (27, 1, 7), (30, 14, 5)):
        a.rect(x, y, 1, h, BONE_D)
    for i in range(9):
        a.px(17 + (i // 3) % 2, 14 + i, BONE_DD)
    speckles(a, 0, 0, 32, 24, 26, (BONE_D, BONE_D, BONE_DD))
    a.rect(0, 8, 32, 6, HIDE), a.rect(0, 8, 32, 1, HIDE_L), a.rect(0, 13, 32, 1, HIDE_D)
    for x, y in ((2, 9), (8, 11), (13, 9), (19, 10), (24, 11), (29, 9)):
        a.rect(x, y, 2, 2, HAIR)
    a.rect(0, 11, 32, 1, mul(HIDE, 0.85))
    a.rect(15, 7, 3, 8, BONE_D), a.rect(15, 7, 1, 8, BONE)
    a.shade(0, 0, 32, 24, 1.08, 0.82, 0.8)
    a.noise(0, 0, 32, 24, 0.04)
    shaft = a.region(0, 0, 32, 24)
    # Бугор сустава 16×8: гладкая головка, пористый поясок у стержня.
    a.rect(0, 24, 16, 8, BONE)
    a.rect(0, 24, 16, 2, mul(BONE, 1.05))
    speckles(a, 0, 27, 16, 5, 16, (BONE_D, BONE_DD))
    a.rect(0, 31, 16, 1, BONE_D)
    for x in (3, 9, 13):
        a.rect(x, 26, 1, 3, BONE_D)
    a.shade(0, 24, 16, 8, 1.1, 0.8, 0.85)
    knob = a.region(0, 24, 16, 8)
    a.rect(16, 24, 8, 8, BONE_D), a.rect(18, 26, 4, 4, BONE_DD), a.px(19, 27, HAIR_L)
    cut = a.region(16, 24, 8, 8)
    lobe = [(-0.15, 0.03, 0.03), (-0.11, 0.15, 0.14), (0.0, 0.2, 0.19), (0.1, 0.16, 0.15), (0.15, 0.04, 0.04)]
    tris = lm.loft([(0.1, 0.22, 0.2), (0.3, 0.16, 0.15), (0.56, 0.16, 0.15), (0.76, 0.22, 0.2)], shaft, 6, caps=(cut, cut))
    for x, y in ((-0.17, 0.15), (0.17, 0.15), (-0.17, 0.71), (0.17, 0.71)):
        tris += lm.at(lm.loft(lobe, knob, 6), x, y, 0.0)
    return lm.Model("barrel", a).part("body", (0.0, 0.0, 0.0), tris)


def dinosaurs_crate():
    """Плетёная корзина-короб: стенки из лозы на тёмных стойках, костяной обод, пояс из шкуры
    с застёжкой-клыком спереди, плетёная крышка с ручкой из кости."""
    a = lm.Atlas(32, 32, 351)
    weave(a, 0, 0, 32, 16)
    for x in (0, 8, 16, 24):
        # Угловые жерди грани, костяной обод сверху, тёмное донце.
        a.rect(x, 0, 1, 16, HAIR_L), a.rect(x + 7, 0, 1, 16, HAIR_D)
        a.rect(x, 0, 8, 2, BONE), a.rect(x, 1, 8, 1, BONE_D)
        a.rect(x, 15, 8, 1, HAIR_D)
        a.rect(x, 7, 8, 3, HIDE), a.rect(x, 7, 8, 1, HIDE_L), a.rect(x, 9, 8, 1, HIDE_D)
        a.px(x + 2, 8, HAIR), a.px(x + 5, 8, HAIR)
        a.px(x + 3, 0, BONE_DD)
    # На передней грани (вторая четверть ленты) застёжка: клык на петле.
    a.rect(11, 6, 2, 5, BONE), a.px(11, 10, BONE_D), a.px(12, 11, BONE), a.rect(10, 6, 4, 1, HAIR_D)
    a.shade(0, 0, 32, 16, 1.08, 0.78, 1.0)
    a.noise(0, 0, 32, 16, 0.05)
    side = a.region(0, 0, 32, 16)
    # Крышка: плетение кольцами к середине, обод, ручка-кость поперёк и лист под ней.
    for j in range(16):
        for i in range(16):
            ring = max(abs(i - 7.5), abs(j - 7.5))
            along = i if abs(j - 7.5) > abs(i - 7.5) else j
            c = STRAW if (int(ring) + along // 2) % 2 == 0 else BRASS
            if int(ring) % 3 == 2:
                c = mul(c, 0.8)
            a.px(i, 16 + j, c)
    a.rect(0, 16, 16, 1, BONE), a.rect(0, 31, 16, 1, BONE_D), a.rect(0, 16, 1, 16, BONE), a.rect(15, 16, 1, 16, BONE_D)
    a.rect(9, 20, 4, 2, LEAF), a.px(12, 19, LEAF_L), a.px(9, 22, LEAF_D)
    a.rect(4, 23, 8, 2, BONE), a.rect(4, 25, 8, 1, HAIR_D)
    a.rect(3, 22, 2, 4, BONE), a.rect(11, 22, 2, 4, BONE), a.px(3, 25, BONE_D), a.px(12, 25, BONE_D)
    a.noise(0, 16, 16, 16, 0.05)
    top = a.region(0, 16, 16, 16)
    a.rect(16, 16, 8, 8, HAIR_D)
    for i in range(0, 8, 2):
        a.rect(16 + i, 16, 1, 8, HAIR)
    under = a.region(16, 16, 8, 8)
    return lm.Model("crate", a).part("body", (0.0, 0.0, 0.0), lm.at(lm.box((0.85, 0.85, 0.85), side, top, under), 0.0, 0.425))


def dinosaurs_chest():
    """Гнездо с яйцами: овальная чаша из прутьев с листьями в плетении, в ней три крупных
    крапчатых яйца. Габариты сундука: чаша на месте корпуса, яйца на месте крышки."""
    a = lm.Atlas(64, 32, 313)
    # Стенка чаши 64×12: прутья внахлёст наискось в обе стороны, торчащие концы, листья.
    a.rect(0, 0, 64, 12, HAIR)
    for k in range(-12, 64, 3):
        tone = (BRASS, mul(BRASS, 0.8), STRAW)[(k // 3) % 3]
        for j in range(12):
            a.px((k + j) % 64, j, tone)
    for k in range(1, 76, 5):
        tone = (mul(BRASS, 1.1), HAIR_L)[(k // 5) % 2]
        for j in range(12):
            a.px((k - j) % 64, j, tone)
            if j % 4 == 1:
                a.px((k - j - 1) % 64, j, HAIR_D)
    a.rect(0, 0, 64, 1, STRAW), a.rect(0, 11, 64, 1, HAIR_D)
    for x, y in ((5, 3), (19, 6), (30, 2), (44, 5), (57, 3)):
        a.rect(x, y, 3, 2, LEAF), a.px(x + 3, y, LEAF_L), a.px(x, y + 1, LEAF_D)
    for x in (11, 26, 38, 51):
        a.rect(x, 0, 1, 3, BONE_D)
    a.shade(0, 0, 64, 12, 1.12, 0.7, 0.9)
    a.noise(0, 0, 64, 12, 0.06)
    side = a.region(0, 0, 64, 12)
    # Нутро чаши 24×12: кольца прутьев темнеют к середине, подстилка из травы и пуха.
    for j in range(12):
        for i in range(24):
            d = math.hypot((i - 11.5) / 12.0, (j - 5.5) / 6.0)
            c = STRAW if d > 0.9 else (BRASS if d > 0.72 else (HAIR_L if d > 0.5 else HAIR))
            if (i + j * 2) % 5 == 0:
                c = mul(c, 0.75)
            a.px(i, 12 + j, c)
    for x, y in ((6, 17), (10, 20), (15, 16), (17, 19), (12, 14)):
        a.px(x, y, BONE), a.px(x + 1, y, LEAF)
    a.noise(0, 12, 24, 12, 0.05)
    inner = a.region(0, 12, 24, 12)
    a.rect(24, 12, 4, 4, HAIR_D), a.px(25, 13, HAIR)
    under = a.region(24, 12, 4, 4)
    # Скорлупа 16×16: общая для трёх яиц.
    egg_shell(a, 32, 12, 16, 16, 30)
    a.noise(32, 12, 16, 16, 0.03)
    shell = a.region(32, 12, 16, 16)
    bowl = lm.loft([(0.0, 0.3, 0.18), (0.08, 0.39, 0.245), (0.26, 0.41, 0.26), (0.36, 0.37, 0.23)], side, 8, caps=(under, inner))
    egg = [(0.0, 0.035, 0.035), (0.06, 0.095, 0.095), (0.15, 0.115, 0.115), (0.24, 0.085, 0.085), (0.3, 0.03, 0.03)]
    tris = bowl
    for x, y, z, tilt in ((-0.19, 0.27, 0.03, 9.0), (0.19, 0.26, 0.04, -11.0), (0.0, 0.3, -0.05, 0.0)):
        tris += lm.at(lm.rot(lm.loft(egg, shell, 6, caps=(None, shell)), rz=tilt), x, y, z)
    return lm.Model("chest", a).part("body", (0.0, 0.0, 0.0), tris)


def dinosaurs_keg():
    """Яйцо динозавра: мяч. Костяная скорлупа в рыжих крапинах, тупой конец шире, летит и
    крутится."""
    a = lm.Atlas(16, 16, 369)
    egg_shell(a, 0, 0, 16, 12, 16)
    # Крупные пятна, по ним видно вращение.
    a.rect(3, 4, 2, 2, HIDE), a.px(5, 5, HIDE_D), a.rect(11, 7, 2, 2, HIDE_D), a.px(13, 3, HIDE), a.px(8, 9, HAIR_L)
    side = a.region(0, 0, 16, 12)
    a.rect(0, 12, 4, 4, BONE), a.px(1, 13, HIDE), a.px(2, 14, BONE_D)
    tip = a.region(0, 12, 4, 4)
    a.rect(4, 12, 4, 4, BONE_D), a.px(5, 13, HIDE_D), a.px(6, 14, BONE_DD)
    base = a.region(4, 12, 4, 4)
    return lm.Model("keg", a).part("body", (0.0, 0.15, 0.0),
                                   lm.loft([(0.0, 0.06, 0.06), (0.05, 0.125, 0.125), (0.13, 0.15, 0.15), (0.21, 0.12, 0.12),
                                            (0.27, 0.075, 0.075), (0.3, 0.03, 0.03)],
                                           side, 6, caps=(base, tip)))


MODELS = [dinosaurs_coin, dinosaurs_bottle, dinosaurs_ball, dinosaurs_rock, dinosaurs_barrel, dinosaurs_crate,
          dinosaurs_chest, dinosaurs_keg]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], [f() for f in MODELS])
    for f in MODELS:
        m = f()
        print("%-7s частей %d, треугольников %d, атлас %d×%d" % (m.name, len(m.parts), m.tris(), m.atlas.w, m.atlas.h))
