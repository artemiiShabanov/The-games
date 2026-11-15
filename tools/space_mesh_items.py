#!/usr/bin/env python3
"""Мелкий реквизит «Космоса» для low poly и «продвинутых» (#136): восемь моделей в слотах пиратов.

Зеркало `pirate_coin`, `pirate_bottle`, `pirate_ball`, `pirate_rock`, `pirate_barrel`,
`pirate_crate`, `pirate_chest`, `pirate_keg` из `lowpoly_meshes.py`. У каждой модели одна часть
`body` с той же точкой вращения и теми же габаритами, что у пиратской: демки ставят их, крутят
и кидают по этим числам. Плотный набор «продвинутых» выходит из тех же функций (`lm.DENSE`).

    python3 tools/space_mesh_items.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Цвета сеттинга (как в палитре 16/32, `space16.PALETTE`).
BLACK = rgb("12101A")
WHITE = rgb("EEF1F6")
GREY = rgb("B3BACB")
METAL = rgb("747D92")
DARK = rgb("3A4054")
AQUA = rgb("4FC3D9")
GLOW = rgb("C2EEF4")
DEEP = rgb("1F6F92")
ORANGE = rgb("F06A3A")
ORANGE_D = rgb("A8431F")
VIOLET = rgb("9A5FE0")
PLUM = rgb("552F98")
GOLD = rgb("F4D35E")
BRASS = rgb("C08A2A")
AMBER = rgb("8A5A14")
BASALT = rgb("5C5E72")
BASALT_D = rgb("3A3B4C")
BASALT_L = rgb("8A8DA2")


def rivets(a, xs, y, light=WHITE, dark=DARK):
    for x in xs:
        a.px(x, y, light)
        a.px(x, y + 1, dark)


def hazard(a, x, y, w, h, c0=ORANGE, c1=BLACK):
    """Косая полосатая лента опасности."""
    for j in range(h):
        for i in range(w):
            a.px(x + i, y + j, c0 if ((i + j) // 2) % 2 == 0 else c1)


def panel_seams(a, x, y, w, h, step, base=WHITE):
    """Листы обшивки: вертикальные швы с бликом слева и тенью справа."""
    a.rect(x, y, w, h, base)
    for i in range(x, x + w, step):
        a.rect(i, y, 1, h, mul(base, 0.72))
        if i + 1 < x + w:
            a.rect(i + 1, y, 1, h, mul(base, 1.06))


def space_coin():
    """Кристалл-бонус: гранёная золотистая двойная пирамида, стоит на вершине и вращается."""
    a = lm.Atlas(32, 32, 105)
    # Грани: шесть вертикальных полос разной яркости, поперёк пояс и блики на рёбрах.
    for k in range(6):
        tone = (1.18, 0.92, 0.7, 1.05, 0.82, 0.62)[k]
        x = k * 5 + (1 if k > 2 else 0)
        a.rect(x, 0, 6, 32, mul(GOLD, tone))
        a.rect(x, 0, 1, 32, mul(GOLD, min(tone + 0.25, 1.3)))
    a.rect(30, 0, 2, 32, mul(GOLD, 0.62))
    for j in range(32):
        # Верх и низ сходятся в вершину: темнее к концам, пояс светлее.
        k = 1.0 - abs(j - 15.5) / 15.5
        for i in range(32):
            c = a.get(i, j)
            a.px(i, j, mul(c, 0.72 + 0.4 * k))
    a.rect(0, 15, 32, 1, mul(GOLD, 1.3))
    a.rect(0, 16, 32, 1, BRASS)
    for x, y in ((2, 6), (3, 5), (12, 9), (17, 22), (23, 7), (27, 20)):
        a.px(x, y, WHITE)
    for x, y in ((8, 24), (20, 12), (14, 4)):
        a.px(x, y, AMBER)
    a.noise(0, 0, 32, 32, 0.05)
    face = a.region(0, 0, 32, 32)
    rings = [(0.07, 0.015, 0.012), (0.24, 0.2, 0.13), (0.42, 0.22, 0.14), (0.63, 0.015, 0.012)]
    return lm.Model("coin", a).part("body", (0.0, 0.35, 0.0), lm.loft(rings, face, 6, math.pi / 6.0, flat=True))


def space_bottle():
    """Энергоячейка: стеклянная колба с бирюзовым зарядом в металлических обоймах. Мишень и
    снаряд метателя, размеры бутылки."""
    a = lm.Atlas(16, 16, 147)
    a.rect(0, 0, 16, 12, DEEP)
    # Столб заряда: светящаяся сердцевина и деления.
    a.rect(0, 3, 16, 6, AQUA)
    a.rect(0, 4, 16, 1, GLOW)
    for x in (2, 6, 10, 14):
        a.rect(x, 3, 1, 6, DEEP)
    a.rect(9, 3, 1, 6, WHITE)
    # Обоймы сверху и снизу, оранжевая метка заряда.
    a.rect(0, 0, 16, 3, METAL), a.rect(0, 0, 16, 1, GREY), a.rect(0, 2, 16, 1, DARK)
    a.rect(0, 9, 16, 3, METAL), a.rect(0, 9, 16, 1, GREY), a.rect(0, 11, 16, 1, DARK)
    a.rect(4, 10, 3, 1, ORANGE)
    rivets(a, (1, 5, 9, 13), 1, WHITE, DARK)
    a.shade(0, 0, 16, 12, 1.1, 0.85, 0.75)
    a.noise(0, 0, 16, 12, 0.05)
    body = a.region(0, 0, 16, 12)
    a.rect(0, 12, 4, 4, GREY), a.rect(1, 13, 2, 2, AQUA)
    cork = a.region(0, 12, 4, 4)
    a.rect(4, 12, 4, 4, DARK), a.px(5, 13, METAL)
    under = a.region(4, 12, 4, 4)
    return lm.Model("bottle", a).part("body", (0.0, 0.25, 0.0),
                                      lm.loft([(0.0, 0.1, 0.1), (0.04, 0.115, 0.115), (0.3, 0.115, 0.115), (0.35, 0.07, 0.07),
                                               (0.46, 0.06, 0.06), (0.5, 0.075, 0.075)], body, 6, caps=(under, cork)))


def space_ball():
    """Энергосфера: снаряд. Бирюзовый шар с белым ядром блика и тёмными витками поля."""
    a = lm.Atlas(16, 16, 149)
    a.rect(0, 0, 16, 16, AQUA)
    # Витки поля: две наклонные тёмные ленты и яркий экватор.
    for i in range(16):
        a.px(i, (4 + i // 3) % 16, DEEP)
        a.px(i, (11 + i // 4) % 16, DEEP)
        a.px(i, 8, GLOW)
    a.rect(5, 3, 4, 3, GLOW), a.rect(6, 3, 2, 2, WHITE)
    for x, y in ((12, 5), (2, 12), (10, 13), (14, 10)):
        a.px(x, y, WHITE)
    a.shade(0, 0, 16, 16, 1.25, 0.65, 0.85)
    a.noise(0, 0, 16, 16, 0.07)
    glow = a.region(0, 0, 16, 16)
    r = 0.18
    rings = [(r - r * math.cos(t), r * math.sin(t), r * math.sin(t)) for t in (0.35, 1.0, math.pi / 2.0, math.pi - 1.0, math.pi - 0.35)]
    return lm.Model("ball", a).part("body", (0.0, r, 0.0), lm.loft(rings, glow, 6, caps=(glow, glow)))


def space_rock():
    """Метеорит: угловатая глыба базальта с кратерами и жилой фиолетового кристалла, рядом осколок."""
    a = lm.Atlas(32, 32, 107)
    a.rect(0, 0, 32, 32, BASALT)
    for _ in range(46):
        x, y = a.rng.randrange(32), a.rng.randrange(32)
        a.rect(x, y, a.rng.randrange(1, 4), 1, BASALT_D if a.rng.random() < 0.6 else BASALT_L)
    # Кратеры: тёмное дно, светлый вал сверху слева, тень снизу справа.
    for cx, cy, r in ((7, 7, 3), (22, 12, 4), (12, 23, 3), (27, 26, 2), (3, 18, 2)):
        for j in range(-r - 1, r + 2):
            for i in range(-r - 1, r + 2):
                d = math.hypot(i, j)
                if d <= r - 0.6:
                    a.px(cx + i, cy + j, BASALT_D)
                elif d <= r + 0.5:
                    a.px(cx + i, cy + j, BASALT_L if i + j < 0 else BLACK)
    # Жила кристалла наискось с бликами.
    for i in range(14):
        x, y = 14 + i, 2 + i * 2 // 3 + (1 if i % 5 == 2 else 0)
        a.px(x, y, VIOLET), a.px(x, y + 1, PLUM)
        if i % 4 == 1:
            a.px(x, y, GLOW)
    for x, y in ((4, 27), (5, 28), (6, 28), (7, 29)):
        a.px(x, y, VIOLET)
    a.shade(0, 0, 32, 32, 1.15, 0.75, 0.9)
    a.noise(0, 0, 32, 32, 0.1)
    stone = a.region(0, 0, 32, 32)
    return lm.Model("rock", a).part(
        "body", (0.0, 0.0, 0.0),
        lm.loft([(0.0, 0.5, 0.52), (0.2, 0.56, 0.46, 0.04, -0.02), (0.5, 0.4, 0.3, -0.05, 0.05), (0.72, 0.12, 0.1, -0.1, 0.03)],
                stone, 6, 0.5, caps=(None, stone), flat=True)
        + lm.at(lm.loft([(0.0, 0.28, 0.3), (0.18, 0.26, 0.2, 0.02, 0.0), (0.36, 0.07, 0.08)], stone, 5, 0.9, caps=(None, stone), flat=True),
                0.5, 0.0, 0.3))


def space_barrel():
    """Топливный баллон: белый бак с оранжевым поясом, лентой опасности и вентилем на крышке."""
    a = lm.Atlas(32, 32, 109)
    panel_seams(a, 0, 0, 32, 24, 8)
    # Обручи сверху и снизу, оранжевый пояс с маркировкой посередине.
    for y in (2, 20):
        a.rect(0, y, 32, 2, METAL), a.rect(0, y, 32, 1, GREY)
        rivets(a, range(3, 32, 8), y, WHITE, DARK)
    a.rect(0, 9, 32, 5, ORANGE), a.rect(0, 9, 32, 1, mul(ORANGE, 1.2)), a.rect(0, 13, 32, 1, ORANGE_D)
    for x in (4, 20):
        a.rect(x, 10, 5, 3, WHITE)
        a.rect(x + 1, 11, 3, 1, BLACK)
    hazard(a, 0, 16, 32, 2)
    # Указатель уровня и потёртости.
    a.rect(13, 5, 2, 3, DARK), a.px(13, 6, AQUA), a.px(14, 6, AQUA)
    for x, y in ((6, 6), (27, 5), (10, 18), (22, 7), (30, 18)):
        a.px(x, y, GREY)
    a.shade(0, 0, 32, 24, 1.1, 0.8, 0.85)
    a.noise(0, 0, 32, 24, 0.04)
    side = a.region(0, 0, 32, 24)
    # Крышка: металл, кольцо, вентиль.
    a.rect(0, 24, 8, 8, METAL)
    for i in range(8):
        for j in range(8):
            d = math.hypot(i - 3.5, j - 3.5)
            if 2.2 < d <= 3.3:
                a.px(i, 24 + j, GREY)
    a.rect(3, 27, 2, 2, ORANGE), a.px(3, 27, WHITE)
    lid = a.region(0, 24, 8, 8)
    return lm.Model("barrel", a).part("body", (0.0, 0.0, 0.0),
                                      lm.loft([(0.0, 0.31, 0.31), (0.08, 0.37, 0.37), (0.78, 0.37, 0.37), (0.86, 0.31, 0.31)],
                                              side, 8, caps=(lid, lid)))


def space_crate():
    """Грузовой контейнер: рама, рёбра жёсткости, оранжевая полоса, трафарет, индикатор замка."""
    a = lm.Atlas(32, 32, 151)
    a.rect(0, 0, 32, 16, GREY)
    for x in (0, 8, 16, 24):
        # Рама грани и рёбра жёсткости.
        a.rect(x, 0, 8, 2, METAL), a.rect(x, 14, 8, 2, METAL)
        a.rect(x, 0, 1, 16, METAL), a.rect(x + 7, 0, 1, 16, DARK)
        a.rect(x + 1, 0, 6, 1, WHITE)
        for i in (2, 4):
            a.rect(x + i, 3, 1, 10, mul(GREY, 0.8))
            a.rect(x + i + 1, 3, 1, 10, WHITE)
        a.rect(x + 1, 10, 6, 2, ORANGE)
        a.px(x + 1, 2, WHITE), a.px(x + 6, 2, WHITE), a.px(x + 1, 13, DARK), a.px(x + 6, 13, DARK)
    # На передней грани (вторая четверть ленты) трафарет и индикатор замка.
    a.rect(10, 4, 4, 3, DARK), a.rect(11, 5, 2, 1, AQUA)
    a.rect(26, 5, 3, 1, BLACK), a.rect(26, 7, 2, 1, BLACK)
    a.shade(0, 0, 32, 16, 1.05, 0.8, 1.0)
    a.noise(0, 0, 32, 16, 0.04)
    side = a.region(0, 0, 32, 16)
    # Крышка: лист с рамой, крестом усиления и угловыми замками.
    a.rect(0, 16, 16, 16, GREY)
    a.rect(0, 16, 16, 1, METAL), a.rect(0, 31, 16, 1, DARK), a.rect(0, 16, 1, 16, METAL), a.rect(15, 16, 1, 16, DARK)
    a.rect(7, 17, 2, 14, mul(GREY, 0.82)), a.rect(1, 23, 14, 2, mul(GREY, 0.82))
    for x, y in ((2, 18), (12, 18), (2, 28), (12, 28)):
        a.rect(x, y, 2, 2, ORANGE)
    a.rect(6, 22, 4, 4, DARK), a.rect(7, 23, 2, 2, AQUA)
    a.noise(0, 16, 16, 16, 0.04)
    top = a.region(0, 16, 16, 16)
    return lm.Model("crate", a).part("body", (0.0, 0.0, 0.0), lm.at(lm.box((0.85, 0.85, 0.85), side, top, top), 0.0, 0.425))


def space_chest():
    """Грузовая капсула: металлический корпус с оранжевой полосой и скошенная крышка с окошком,
    за стеклом бирюзовое свечение."""
    a = lm.Atlas(64, 32, 113)
    # Корпус: листы обшивки, стяжки, полоса, замок спереди (вторая четверть ленты).
    panel_seams(a, 0, 0, 64, 12, 8, GREY)
    for x in (7, 23, 39, 55):
        a.rect(x, 0, 3, 12, METAL)
        a.rect(x, 0, 1, 12, WHITE)
        a.px(x + 1, 2, WHITE), a.px(x + 1, 9, DARK)
    a.rect(0, 7, 64, 2, ORANGE), a.rect(0, 9, 64, 1, ORANGE_D)
    a.rect(26, 2, 5, 4, DARK), a.rect(27, 3, 3, 2, AQUA), a.px(27, 3, GLOW)
    hazard(a, 10, 10, 12, 2)
    hazard(a, 42, 10, 12, 2)
    a.shade(0, 0, 64, 12, 1.05, 0.8, 1.0)
    a.noise(0, 0, 64, 12, 0.04)
    side = a.region(0, 0, 64, 12)
    # Бока крышки: светлый металл, окошко спереди, кант снизу.
    panel_seams(a, 0, 12, 64, 8, 8, WHITE)
    for x in (7, 23, 39, 55):
        a.rect(x, 12, 3, 8, METAL)
    a.rect(18, 13, 12, 5, DARK), a.rect(19, 14, 10, 3, AQUA), a.rect(19, 14, 10, 1, GLOW)
    a.rect(22, 14, 1, 3, DEEP), a.rect(26, 14, 1, 3, DEEP)
    a.rect(0, 19, 64, 1, DARK)
    a.noise(0, 12, 64, 8, 0.04)
    lid_side = a.region(0, 12, 64, 8)
    # Верх крышки: люк с ручкой и маркировкой.
    a.rect(0, 20, 24, 12, WHITE)
    a.rect(0, 20, 24, 1, GREY), a.rect(0, 31, 24, 1, METAL)
    for x in (4, 18):
        a.rect(x, 20, 3, 12, METAL)
        a.rect(x, 20, 1, 12, GREY)
    a.rect(9, 23, 6, 6, DARK), a.rect(10, 24, 4, 4, AQUA), a.px(10, 24, GLOW), a.px(11, 24, GLOW)
    a.rect(8, 30, 8, 1, ORANGE)
    a.noise(0, 20, 24, 12, 0.04)
    lid_top = a.region(0, 20, 24, 12)
    a.rect(24, 20, 4, 4, DARK)
    under = a.region(24, 20, 4, 4)
    return lm.Model("chest", a).part("body", (0.0, 0.0, 0.0),
                                     lm.at(lm.box((0.8, 0.4, 0.5), side, None, under), 0.0, 0.2)
                                     + lm.at(lm.box((0.82, 0.2, 0.52), lid_side, lid_top, None, (0.8, 0.55)), 0.0, 0.5))


def space_keg():
    """Малый баллон: мяч. Белый бачок с оранжевыми торцами и бирюзовым указателем, летит и крутится."""
    a = lm.Atlas(16, 16, 169)
    panel_seams(a, 0, 0, 16, 12, 4)
    a.rect(0, 0, 16, 2, ORANGE), a.rect(0, 10, 16, 2, ORANGE)
    a.rect(0, 2, 16, 1, METAL), a.rect(0, 9, 16, 1, METAL)
    a.rect(6, 4, 4, 3, DARK), a.rect(7, 5, 2, 1, AQUA)
    a.px(2, 6, BLACK), a.px(3, 6, BLACK), a.px(13, 5, GREY)
    a.shade(0, 0, 16, 12, 1.15, 0.75, 0.85)
    side = a.region(0, 0, 16, 12)
    a.rect(0, 12, 4, 4, METAL)
    a.px(1, 13, WHITE), a.px(2, 14, ORANGE)
    lid = a.region(0, 12, 4, 4)
    return lm.Model("keg", a).part("body", (0.0, 0.15, 0.0),
                                   lm.loft([(0.0, 0.09, 0.09), (0.06, 0.15, 0.15), (0.24, 0.15, 0.15), (0.3, 0.09, 0.09)],
                                           side, 6, caps=(lid, lid)))


MODELS = [space_coin, space_bottle, space_ball, space_rock, space_barrel, space_crate, space_chest, space_keg]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], [f() for f in MODELS])
    for f in MODELS:
        m = f()
        print("%-7s частей %d, треугольников %d, атлас %d×%d" % (m.name, len(m.parts), m.tris(), m.atlas.w, m.atlas.h))
