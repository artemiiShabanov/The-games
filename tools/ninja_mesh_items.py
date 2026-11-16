#!/usr/bin/env python3
"""Мелкий реквизит «Ниндзя» для low poly и «продвинутых» (#137): восемь моделей в слотах пиратов.

Зеркало `pirate_coin`, `pirate_bottle`, `pirate_ball`, `pirate_rock`, `pirate_barrel`,
`pirate_crate`, `pirate_chest`, `pirate_keg` из `lowpoly_meshes.py` (и `space_mesh_items.py`).
У каждой модели одна часть `body` с той же точкой вращения и теми же габаритами, что у
пиратской: демки ставят их, крутят и кидают по этим числам. Плотный набор «продвинутых» выходит
из тех же функций (`lm.DENSE`).

Состав по `docs/specs/settings.md`: монета с квадратным отверстием, тыква-горлянка, глиняная
бомба в верёвочной оплётке, священный валун с верёвкой симэнава, бочка сакэ в соломе, бамбуковая
клетка, лакированный ларец, расшитый мяч тэмари. Цвета из основы 16/32 (`ninja16.PALETTE`
через `ninja_mesh_chars`).

    python3 tools/ninja_mesh_items.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import ninja_mesh_chars as nc  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Цвета сеттинга: основа из `ninja_mesh_chars` (палитра 16/32), свои тона для дерева, камня и зелени.
BLACK = nc.BLACK
WHITE, GREY = nc.WHITE, nc.GREY
RED, RED_D, RED_L = nc.RED, nc.RED_D, nc.RED_L
BLUE, BLUE_D = nc.BLUE, nc.BLUE_D
GOLD, GOLD_D, GOLD_L = nc.GOLD, nc.GOLD_D, nc.GOLD_L
STEEL, STEEL_D = nc.STEEL, nc.STEEL_D
LACQ, LACQ_D, LACQ_L = nc.LACQ, nc.LACQ_D, nc.LACQ_L
STRAW, STRAW_D = nc.STRAW, nc.STRAW_D
STRAW_L = rgb("EDD08A")
GOURD, GOURD_D, GOURD_L = rgb("C98A3C"), rgb("8A5424"), rgb("E8B666")
CLAY, CLAY_D, CLAY_L = rgb("4A3A3C"), rgb("2A2026"), rgb("6E5A56")
STONE, STONE_D, STONE_L = nc.STEEL, rgb("4E5062"), rgb("A2A4B0")
MOSS, MOSS_D, MOSS_L = rgb("6FA94B"), rgb("27563F"), rgb("9CCB62")
BAMBOO, BAMBOO_D, BAMBOO_L = rgb("7FAE4A"), rgb("3F6E38"), rgb("BFDC7A")
WOOD, WOOD_D, WOOD_L = rgb("D8B984"), rgb("9A7444"), rgb("F0DCAE")
CORAL = rgb("E97B52")


def rope(a, x, y, w, h=2, light=STRAW_L, dark=STRAW_D):
    """Кручёная соломенная верёвка: косые витки, сверху блик, снизу тень."""
    for j in range(h):
        for i in range(w):
            a.px(x + i, y + j, light if (i + j) % 3 == 0 else (STRAW if (i + j) % 3 == 1 else dark))
    a.rect(x, y + h, w, 1, mul(dark, 0.6))


def straw_mat(a, x, y, w, h):
    """Соломенная циновка: вертикальные стебли разного тона, редкие тёмные щели."""
    for i in range(w):
        tone = (1.0, 1.12, 0.9, 1.05, 0.82)[(i * 7 + i // 3) % 5]
        for j in range(h):
            a.px(x + i, y + j, mul(STRAW, tone))
    for _ in range(w * h // 14):
        i, j = a.rng.randrange(w), a.rng.randrange(h - 2)
        a.rect(x + i, y + j, 1, a.rng.randrange(2, 4), STRAW_D)


def _face(vs, uvs, out):
    """Треугольник лицом в сторону `out`: порядок вершин подбирается по нормали."""
    n = lm._cross(lm._sub(vs[1], vs[0]), lm._sub(vs[2], vs[0]))
    if n[0] * out[0] + n[1] * out[1] + n[2] * out[2] < 0.0:
        vs, uvs = [vs[0], vs[2], vs[1]], [uvs[0], uvs[2], uvs[1]]
    return lm._tri(vs, uvs)


def holed_disc(r, hole, t, face, edge, inner):
    """Диск на ребре с квадратным сквозным отверстием: восьмиугольник с плоским верхом, толщина
    `2t` вдоль Z, центр в нуле. `face` кладётся на обе стороны, `edge` на гурт, `inner` на
    стенки отверстия."""
    outer = [(r * math.cos(math.pi / 8.0 + k * math.pi / 4.0), r * math.sin(math.pi / 8.0 + k * math.pi / 4.0)) for k in range(8)]
    hr = hole * math.sqrt(2.0)
    inn = [(hr * math.cos(math.pi / 4.0 + k * math.pi / 2.0), hr * math.sin(math.pi / 4.0 + k * math.pi / 2.0)) for k in range(4)]
    u0, v0, u1, v1 = face

    def uv(p):
        return (u0 + (u1 - u0) * (0.5 + p[0] / (2.0 * r)), v0 + (v1 - v0) * (0.5 - p[1] / (2.0 * r)))

    flat = []
    for k in range(4):
        o0, o1, o2 = outer[2 * k], outer[2 * k + 1], outer[(2 * k + 2) % 8]
        i0, i1 = inn[k], inn[(k + 1) % 4]
        flat += [(o0, o1, i0), (o1, i1, i0), (o1, o2, i1)]
    tris = []
    for z in (-t, t):
        for tri in flat:
            tris.append(_face([(p[0], p[1], z) for p in tri], [uv(p) for p in tri], (0.0, 0.0, z)))

    def band(pts, region, sign):
        e0, f0, e1, f1 = region
        n = len(pts)
        for k in range(n):
            a, b = pts[k], pts[(k + 1) % n]
            ua, ub = e0 + (e1 - e0) * k / n, e0 + (e1 - e0) * (k + 1) / n
            mid = ((a[0] + b[0]) * 0.5 * sign, (a[1] + b[1]) * 0.5 * sign, 0.0)
            q = [(a[0], a[1], -t), (b[0], b[1], -t), (b[0], b[1], t), (a[0], a[1], t)]
            tris.append(_face([q[0], q[1], q[2]], [(ua, f0), (ub, f0), (ub, f1)], mid))
            tris.append(_face([q[0], q[2], q[3]], [(ua, f0), (ub, f1), (ua, f1)], mid))

    band(outer, edge, 1.0)
    band(inn, inner, -1.0)
    return tris


def ninja_coin():
    """Монета с квадратным отверстием: золотой диск на ребре, дыра сквозная, вокруг неё четыре
    знака и два выпуклых канта. Стоит и вращается, как дублон."""
    a = lm.Atlas(32, 32, 305)
    # Лицо 16×16: поле, внешний кант, кант у отверстия, четыре знака крестом.
    a.rect(0, 0, 16, 16, GOLD)
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            if d > 6.4:
                a.px(i, j, GOLD_D)
            elif d > 5.3:
                a.px(i, j, GOLD_L)
            elif d > 4.6:
                a.px(i, j, mul(GOLD, 0.82))
    a.rect(4, 4, 8, 8, GOLD_D)
    a.rect(5, 5, 6, 6, GOLD_L)
    a.rect(6, 6, 4, 4, mul(GOLD_D, 0.55))
    # Знаки: по два тёмных штриха с бликом между кантами.
    for x, y, w, h in ((7, 2, 2, 1), (6, 3, 4, 1), (7, 12, 2, 1), (6, 13, 4, 1), (2, 7, 1, 2), (3, 6, 1, 4), (13, 7, 1, 2), (12, 6, 1, 4)):
        a.rect(x, y, w, h, mul(GOLD_D, 0.75))
    for x, y in ((3, 3), (4, 2), (11, 12), (12, 11)):
        a.px(x, y, WHITE)
    a.shade(0, 0, 16, 16, 1.12, 0.86, 0.95)
    a.noise(0, 0, 16, 16, 0.05)
    face = a.region(0, 0, 16, 16)
    # Гурт: насечка. Стенки отверстия: тёмное золото с бликом.
    for i in range(16):
        a.rect(16 + i, 0, 1, 4, GOLD if i % 2 == 0 else GOLD_D)
    a.rect(16, 0, 16, 1, GOLD_L)
    edge = a.region(16, 0, 16, 4)
    a.rect(16, 4, 16, 4, GOLD_D), a.rect(16, 4, 16, 1, GOLD), a.rect(16, 7, 16, 1, mul(GOLD_D, 0.7))
    inner = a.region(16, 4, 16, 4)
    return lm.Model("coin", a).part("body", (0.0, 0.35, 0.0),
                                    lm.at(holed_disc(0.28, 0.085, 0.035, face, edge, inner), 0.0, 0.35))


def ninja_bottle():
    """Тыква-горлянка: два пузатых яруса с перехватом, красный шнур с кистью на талии, деревянная
    пробка. Мишень и снаряд метателя, размеры бутылки."""
    a = lm.Atlas(16, 16, 347)
    a.rect(0, 0, 16, 12, GOURD)
    # Долевые прожилки кожуры и светлый бок.
    for x in (1, 5, 9, 13):
        a.rect(x, 0, 1, 12, mul(GOURD, 0.88))
    a.rect(6, 2, 2, 3, GOURD_L), a.rect(6, 8, 3, 3, GOURD_L), a.px(7, 8, WHITE)
    for x, y in ((2, 9), (11, 10), (12, 3), (3, 2), (14, 8)):
        a.px(x, y, GOURD_D)
    # Горлышко сверху темнее, донце в тени.
    a.rect(0, 0, 16, 2, GOURD_D), a.rect(0, 1, 16, 1, mul(GOURD, 0.8))
    a.rect(0, 11, 16, 1, GOURD_D)
    # Шнур на перехвате: два витка, узел и кисть спереди.
    a.rect(0, 5, 16, 2, RED), a.rect(0, 5, 16, 1, RED_L), a.rect(0, 7, 16, 1, GOURD_D)
    for x in range(1, 16, 3):
        a.px(x, 6, RED_D)
    a.rect(7, 5, 2, 2, GOLD), a.px(7, 5, GOLD_L)
    a.rect(8, 7, 1, 3, RED), a.px(8, 9, RED_D), a.px(8, 10, GOLD)
    a.shade(0, 0, 16, 12, 1.08, 0.86, 0.74)
    a.noise(0, 0, 16, 12, 0.05)
    body = a.region(0, 0, 16, 12)
    # Пробка: срез дерева с кольцом. Донце: тёмная кожура с пупком.
    a.rect(0, 12, 4, 4, WOOD_D), a.rect(1, 13, 2, 2, WOOD), a.px(1, 13, WOOD_L)
    cork = a.region(0, 12, 4, 4)
    a.rect(4, 12, 4, 4, GOURD_D), a.px(5, 13, mul(GOURD_D, 0.6)), a.px(6, 14, GOURD)
    under = a.region(4, 12, 4, 4)
    rings = [(0.0, 0.06, 0.06), (0.03, 0.1, 0.1), (0.1, 0.115, 0.115), (0.18, 0.105, 0.105), (0.25, 0.05, 0.05),
             (0.31, 0.078, 0.078), (0.37, 0.078, 0.078), (0.43, 0.038, 0.038), (0.5, 0.034, 0.034)]
    return lm.Model("bottle", a).part("body", (0.0, 0.25, 0.0), lm.loft(rings, body, 6, caps=(under, cork)))


def ninja_ball():
    """Глиняная бомба хороку: снаряд. Тёмный обожжённый шар в редкой соломенной оплётке с поясом, красная
    печать на боку, сверху тлеющий фитиль."""
    a = lm.Atlas(16, 16, 349)
    a.rect(0, 0, 16, 12, CLAY)
    for _ in range(14):
        x, y = a.rng.randrange(16), a.rng.randrange(12)
        a.px(x, y, CLAY_L if a.rng.random() < 0.5 else CLAY_D)
    # Оплётка: редкая косая сетка и пояс по экватору.
    for j in range(12):
        for i in range(16):
            if (i + j) % 8 == 2 or (i - j) % 8 == 5:
                a.px(i, j, STRAW if j % 2 == 0 else STRAW_D)
    a.rect(0, 5, 16, 2, STRAW), a.rect(0, 5, 16, 1, STRAW_L)
    for x in range(0, 16, 2):
        a.px(x, 6, STRAW_D)
    # Печать спереди: красный листок со знаком.
    a.rect(6, 2, 4, 7, RED), a.rect(6, 2, 4, 1, RED_L), a.rect(7, 4, 2, 1, BLACK), a.rect(7, 6, 2, 1, BLACK), a.px(8, 5, BLACK)
    a.shade(0, 0, 16, 12, 1.3, 0.7, 0.85)
    a.noise(0, 0, 16, 12, 0.06)
    side = a.region(0, 0, 16, 12)
    # Макушка: узел оплётки и огонёк фитиля. Низ: голая глина.
    a.rect(0, 12, 4, 4, STRAW_D), a.rect(1, 13, 2, 2, CORAL), a.px(1, 13, GOLD_L), a.px(2, 14, RED)
    top = a.region(0, 12, 4, 4)
    a.rect(4, 12, 4, 4, CLAY_D), a.px(5, 13, CLAY)
    under = a.region(4, 12, 4, 4)
    r = 0.18
    rings = [(r - r * math.cos(t), r * math.sin(t), r * math.sin(t)) for t in (0.35, 1.0, math.pi / 2.0, math.pi - 1.0, math.pi - 0.35)]
    return lm.Model("ball", a).part("body", (0.0, r, 0.0), lm.loft(rings, side, 6, caps=(under, top)))


def ninja_rock():
    """Священный валун: серая глыба с моховой шапкой, опоясана соломенной верёвкой симэнава с
    бумажными зигзагами, рядом малый замшелый камень."""
    a = lm.Atlas(32, 32, 307)
    a.rect(0, 0, 32, 32, STONE)
    for _ in range(50):
        x, y = a.rng.randrange(32), a.rng.randrange(32)
        a.rect(x, y, a.rng.randrange(1, 4), 1, STONE_D if a.rng.random() < 0.6 else STONE_L)
    # Трещины: ломаные тёмные линии со светлой кромкой.
    for x0, y0, n in ((4, 20, 8), (19, 21, 9), (27, 8, 5), (10, 9, 4)):
        x, y = x0, y0
        for k in range(n):
            a.px(x, y, BLACK), a.px(x + 1, y, STONE_L)
            y += 1
            x += (-1, 0, 1, 0)[(k + x0) % 4]
    # Моховая шапка сверху с рваным краем и пятна мха у земли.
    for i in range(32):
        d = 5 + (i * 5 % 4) + (1 if i % 7 == 3 else 0)
        a.rect(i, 0, 1, d, MOSS)
        a.px(i, d, MOSS_D)
        a.px(i, (i * 3) % 4, MOSS_L)
    for x, y, w in ((2, 29, 5), (13, 30, 4), (22, 28, 6), (29, 30, 3)):
        a.rect(x, y, w, 32 - y, MOSS_D), a.rect(x + 1, y, w - 2, 1, MOSS)
    # Симэнава: толстая верёвка вокруг глыбы, под ней бумажные зигзаги и соломенные кисти.
    rope(a, 0, 13, 32, 3)
    for x in (3, 11, 19, 27):
        a.rect(x, 17, 2, 2, WHITE), a.rect(x + 1, 19, 2, 2, WHITE), a.rect(x, 21, 2, 2, WHITE)
        a.px(x + 1, 18, GREY), a.px(x + 2, 20, GREY), a.px(x + 1, 22, GREY)
    for x in (7, 15, 23, 31):
        a.rect(x, 17, 1, 3, STRAW), a.px(x, 20, STRAW_D)
    a.shade(0, 0, 32, 32, 1.15, 0.78, 0.92)
    a.noise(0, 0, 32, 32, 0.08)
    stone = a.region(0, 0, 32, 32)
    moss = a.region(1, 0, 12, 4)
    low = a.region(0, 22, 32, 10)
    return lm.Model("rock", a).part(
        "body", (0.0, 0.0, 0.0),
        lm.loft([(0.0, 0.5, 0.52), (0.24, 0.55, 0.47, 0.03, -0.02), (0.52, 0.42, 0.34, -0.04, 0.04), (0.72, 0.15, 0.12, -0.09, 0.03)],
                stone, 6, 0.5, caps=(None, moss), flat=True)
        + lm.at(lm.loft([(0.0, 0.28, 0.3), (0.17, 0.27, 0.21, 0.02, 0.0), (0.36, 0.08, 0.09)], low, 5, 0.9, caps=(None, moss), flat=True),
                0.5, 0.0, 0.3))


def ninja_barrel():
    """Бочка сакэ в соломе: циновка, два верёвочных пояса и косая стяжка, спереди белый ярлык с красным кругом
    и мазками туши, на крышке дощечки и верёвочный узел."""
    a = lm.Atlas(32, 32, 309)
    straw_mat(a, 0, 0, 32, 24)
    # Лента делится на пять поясов по высоте: крайние ложатся на скосы у крышек, три средних на
    # стенку. Скосы: подвёрнутая солома темнее.
    for y, h in ((0, 5), (19, 5)):
        for j in range(h):
            for i in range(32):
                a.px(i, y + j, mul(a.get(i, y + j), 0.8))
    # Ярлык: белая бумага спереди, красный круг и знаки тушью.
    a.rect(10, 7, 12, 10, WHITE), a.rect(10, 7, 12, 1, GREY), a.rect(10, 16, 12, 1, GREY)
    a.rect(10, 7, 1, 10, GREY), a.rect(21, 7, 1, 10, GREY)
    for j in range(-2, 3):
        for i in range(-2, 3):
            if math.hypot(i, j) <= 2.3:
                a.px(16 + i, 10 + j, RED)
    a.px(15, 9, RED_L)
    for x, y, w, h in ((12, 14, 3, 1), (13, 13, 1, 3), (17, 13, 1, 3), (16, 14, 4, 1), (19, 13, 1, 1)):
        a.rect(x, y, w, h, BLACK)
    # Пояса: верёвки у верхнего и нижнего края стенки, косая стяжка по бокам от ярлыка.
    rope(a, 0, 5, 32, 2)
    rope(a, 0, 17, 32, 2)
    for i in range(9):
        for x0, d in ((0, 1), (31, -1)):
            a.px(x0 + d * i, 8 + i, STRAW_L), a.px(x0 + d * i, 9 + i, STRAW_D)
            a.px(x0 + d * i, 16 - i, STRAW_L), a.px(x0 + d * i, 17 - i, STRAW_D)
    a.shade(0, 0, 32, 24, 1.1, 0.8, 0.82)
    a.noise(0, 0, 32, 24, 0.04)
    side = a.region(0, 0, 32, 24)
    # Крышка: светлые дощечки, соломенный валик по краю, узел в середине.
    a.rect(0, 24, 8, 8, STRAW_D)
    for i in range(8):
        for j in range(8):
            d = math.hypot(i - 3.5, j - 3.5)
            if d <= 2.9:
                a.px(i, 24 + j, WOOD if i % 3 else WOOD_D)
            elif d <= 3.8:
                a.px(i, 24 + j, STRAW_L if (i + j) % 2 else STRAW)
    a.rect(3, 27, 2, 2, STRAW_D), a.px(3, 27, STRAW_L)
    lid = a.region(0, 24, 8, 8)
    return lm.Model("barrel", a).part("body", (0.0, 0.0, 0.0),
                                      lm.loft([(0.0, 0.33, 0.33), (0.07, 0.37, 0.37), (0.31, 0.37, 0.37), (0.55, 0.37, 0.37),
                                               (0.79, 0.37, 0.37), (0.86, 0.32, 0.32)],
                                              side, 8, caps=(lid, lid)))


def ninja_crate():
    """Бамбуковая клетка: зелёные стволы с коленцами, между ними темнота, углы и пояса перевязаны
    соломой, спереди бумажный оберег и пара глаз в глубине."""
    a = lm.Atlas(32, 32, 351)
    a.rect(0, 0, 32, 16, LACQ_D)
    for x in (0, 8, 16, 24):
        # Прутья: угловые стволы толще, два прута между ними.
        for i, wide in ((0, 2), (3, 1), (5, 1), (7, 1)):
            a.rect(x + i, 0, wide, 16, BAMBOO)
            a.rect(x + i, 0, 1, 16, BAMBOO_L if i in (0, 3, 5) else BAMBOO_D)
            if wide == 2:
                a.rect(x + i + 1, 0, 1, 16, BAMBOO)
            for y in (4, 10):
                a.rect(x + i, y + (i % 2), wide, 1, BAMBOO_D)
        # Глубина клетки: дальние прутья едва видны.
        for i in (2, 4, 6):
            a.px(x + i, 6, LACQ), a.px(x + i, 9, LACQ)
        # Перекладины сверху и снизу и соломенная вязка на них.
        for y in (0, 13):
            a.rect(x, y, 8, 3, BAMBOO), a.rect(x, y, 8, 1, BAMBOO_L), a.rect(x, y + 2, 8, 1, BAMBOO_D)
            a.px(x + 4, y + 1, BAMBOO_D)
            for i in (0, 1, 7):
                a.rect(x + i, y, 1, 3, STRAW if i != 1 else STRAW_D)
            a.px(x, y, STRAW_L)
    # На передней грани (вторая четверть ленты) оберег и глаза пленника.
    a.px(10, 7, GOLD), a.px(12, 7, GOLD)
    a.rect(13, 3, 2, 6, WHITE), a.px(13, 5, RED), a.px(14, 5, RED), a.px(13, 7, BLACK), a.px(14, 8, GREY)
    a.shade(0, 0, 32, 16, 1.08, 0.82, 1.0)
    a.noise(0, 0, 32, 16, 0.04)
    side = a.region(0, 0, 32, 16)
    # Крышка: решётка из стволов поперёк, рама, вязка по углам, верёвочная ручка.
    a.rect(0, 16, 16, 16, LACQ_D)
    for x in range(1, 16, 3):
        a.rect(x, 16, 2, 16, BAMBOO), a.rect(x, 16, 1, 16, BAMBOO_L)
        a.px(x, 21, BAMBOO_D), a.px(x + 1, 21, BAMBOO_D), a.px(x, 27, BAMBOO_D), a.px(x + 1, 27, BAMBOO_D)
    for y in (16, 30):
        a.rect(0, y, 16, 2, BAMBOO), a.rect(0, y, 16, 1, BAMBOO_L if y == 16 else BAMBOO_D)
    a.rect(0, 16, 1, 16, BAMBOO_L), a.rect(15, 16, 1, 16, BAMBOO_D)
    for x, y in ((0, 16), (14, 16), (0, 30), (14, 30)):
        a.rect(x, y, 2, 2, STRAW), a.px(x, y, STRAW_L)
    a.rect(5, 23, 6, 2, STRAW), a.rect(5, 23, 6, 1, STRAW_L), a.px(5, 25, STRAW_D), a.px(10, 25, STRAW_D)
    a.noise(0, 16, 16, 16, 0.04)
    top = a.region(0, 16, 16, 16)
    return lm.Model("crate", a).part("body", (0.0, 0.0, 0.0), lm.at(lm.box((0.85, 0.85, 0.85), side, top, top), 0.0, 0.425))


def _mon(a, cx, cy, c=GOLD, hi=GOLD_L):
    """Герб клана: кольцо с точкой, 5×5 пикселей."""
    for i in range(-2, 3):
        for j in range(-2, 3):
            d = math.hypot(i, j)
            if 1.5 < d < 2.6:
                a.px(cx + i, cy + j, c)
    a.px(cx, cy, c), a.px(cx - 1, cy - 2, hi)


def ninja_chest():
    """Лакированный ларец: чёрный лак с бликом, золотые уголки и гербы, красный шнур вокруг
    корпуса и через крышку, бант с кистями спереди."""
    a = lm.Atlas(64, 32, 313)
    # Корпус: лак, золотые накладки на рёбрах, кант сверху, герб на каждой грани.
    a.rect(0, 0, 64, 12, LACQ)
    a.rect(0, 0, 64, 1, LACQ_L), a.rect(0, 10, 64, 2, LACQ_D)
    for x in (0, 16, 32, 48):
        a.rect(x, 0, 2, 12, GOLD), a.rect(x, 0, 1, 12, GOLD_L)
        a.rect(x + 14, 0, 2, 12, GOLD), a.rect(x + 15, 0, 1, 12, GOLD_D)
        a.rect(x + 2, 0, 2, 2, GOLD), a.rect(x + 12, 0, 2, 2, GOLD)
        a.rect(x + 2, 10, 2, 2, GOLD_D), a.rect(x + 12, 10, 2, 2, GOLD_D)
        a.px(x + 1, 3, BLACK), a.px(x + 14, 3, BLACK), a.px(x + 1, 8, BLACK), a.px(x + 14, 8, BLACK)
        for i in range(3, 12, 2):
            a.px(x + i + (i % 3 == 0), 3 + i % 5, LACQ_L)
    for x in (8, 40, 56):
        _mon(a, x, 5)
    # Шнур вокруг корпуса спереди (вторая четверть ленты) с бантом и кистями.
    a.rect(23, 0, 2, 12, RED), a.rect(23, 0, 1, 12, RED_L)
    a.rect(20, 3, 3, 2, RED), a.rect(25, 3, 3, 2, RED), a.px(20, 3, RED_L), a.px(25, 3, RED_L)
    a.px(19, 4, RED_D), a.px(28, 4, RED_D)
    a.rect(23, 3, 2, 2, GOLD), a.px(23, 3, GOLD_L)
    a.rect(21, 6, 1, 4, RED_D), a.rect(26, 6, 1, 4, RED_D), a.px(21, 9, GOLD), a.px(26, 9, GOLD)
    a.rect(55, 0, 2, 12, RED), a.rect(55, 0, 1, 12, RED_L), a.rect(55, 4, 2, 3, RED_D)
    a.shade(0, 0, 64, 12, 1.08, 0.82, 1.0)
    a.noise(0, 0, 64, 12, 0.04)
    side = a.region(0, 0, 64, 12)
    # Бока крышки: лак с золотой каймой снизу, уголки, волна росписи, шнур спереди и сзади.
    a.rect(0, 12, 64, 8, LACQ)
    a.rect(0, 12, 64, 1, LACQ_L)
    a.rect(0, 18, 64, 1, GOLD), a.rect(0, 19, 64, 1, GOLD_D)
    for x in (0, 16, 32, 48):
        a.rect(x, 12, 2, 7, GOLD), a.rect(x, 12, 1, 7, GOLD_L)
        a.rect(x + 14, 12, 2, 7, GOLD), a.rect(x + 15, 12, 1, 7, GOLD_D)
        for i in range(3, 13):
            if i not in (7, 8):
                a.px(x + i, 15 + (0, 1, 1, 0, -1, -1)[i % 6], GOLD_D)
    a.rect(23, 12, 2, 8, RED), a.rect(23, 12, 1, 8, RED_L)
    a.rect(55, 12, 2, 8, RED), a.rect(55, 12, 1, 8, RED_L)
    a.noise(0, 12, 64, 8, 0.04)
    lid_side = a.region(0, 12, 64, 8)
    # Верх крышки: золотая рамка, герб, шнур поперёк, блик лака.
    a.rect(0, 20, 24, 12, LACQ)
    a.rect(0, 20, 24, 1, GOLD), a.rect(0, 31, 24, 1, GOLD_D), a.rect(0, 20, 1, 12, GOLD), a.rect(23, 20, 1, 12, GOLD_D)
    for x, y in ((1, 21), (21, 21), (1, 29), (21, 29)):
        a.rect(x, y, 2, 2, GOLD)
    for i in range(5):
        a.px(3 + i, 23 + (i % 2), LACQ_L), a.px(15 + i, 27 + (i % 2), LACQ_L)
    a.rect(11, 20, 2, 12, RED), a.rect(11, 20, 1, 12, RED_L)
    _mon(a, 6, 26), _mon(a, 18, 26)
    a.rect(10, 25, 4, 2, GOLD), a.px(10, 25, GOLD_L)
    a.noise(0, 20, 24, 12, 0.04)
    lid_top = a.region(0, 20, 24, 12)
    a.rect(24, 20, 4, 4, LACQ_D)
    under = a.region(24, 20, 4, 4)
    return lm.Model("chest", a).part("body", (0.0, 0.0, 0.0),
                                     lm.at(lm.box((0.8, 0.4, 0.5), side, None, under), 0.0, 0.2)
                                     + lm.at(lm.box((0.82, 0.2, 0.52), lid_side, lid_top, None, (0.8, 0.55)), 0.0, 0.5))


def ninja_keg():
    """Мяч тэмари: шар, расшитый цветными зигзагами в несколько слоёв, пояс золотой нити, на
    полюсах звёздочки. Летит и крутится."""
    a = lm.Atlas(16, 16, 369)
    for j in range(12):
        for i in range(16):
            # Зигзаги стежков от экватора к полюсам: золото, красный, белый, синий, золотая кайма.
            k = abs(j - 5.5) + abs((i % 4) - 2) * 0.9
            c = GOLD if k < 1.0 else RED if k < 2.3 else WHITE if k < 3.3 else BLUE if k < 4.6 else BLUE_D if k < 5.2 else GOLD
            a.px(i, j, c)
    for i in range(16):
        # Узелки золотой нити на вершинах зигзага.
        if i % 4 == 0:
            a.px(i, 5, GOLD_L), a.px(i, 6, GOLD_D)
    a.rect(0, 0, 16, 1, RED), a.rect(0, 11, 16, 1, RED)
    a.shade(0, 0, 16, 12, 1.2, 0.78, 0.9)
    a.noise(0, 0, 16, 12, 0.04)
    side = a.region(0, 0, 16, 12)
    # Полюс: красная звёздочка с золотым сердцем.
    a.rect(0, 12, 4, 4, RED), a.rect(1, 13, 2, 2, GOLD), a.px(0, 12, WHITE), a.px(3, 12, WHITE), a.px(0, 15, WHITE), a.px(3, 15, WHITE)
    pole = a.region(0, 12, 4, 4)
    r = 0.15
    rings = [(r - r * math.cos(t), r * math.sin(t), r * math.sin(t))
             for t in (0.35, 0.95, math.pi / 2.0, math.pi - 0.95, math.pi - 0.35)]
    return lm.Model("keg", a).part("body", (0.0, 0.15, 0.0), lm.loft(rings, side, 8, caps=(pole, pole)))


MODELS = [ninja_coin, ninja_bottle, ninja_ball, ninja_rock, ninja_barrel, ninja_crate, ninja_chest, ninja_keg]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], [f() for f in MODELS])
    for f in MODELS:
        m = f()
        print("%-7s частей %d, треугольников %d, атлас %d×%d" % (m.name, len(m.parts), m.tris(), m.atlas.w, m.atlas.h))
