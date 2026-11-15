#!/usr/bin/env python3
"""Мелкий реквизит «Замков» для low poly и «продвинутых» (#137): восемь моделей в слотах пиратов.

Зеркало `space_mesh_items.py`, а через него `pirate_coin`, `pirate_bottle`, `pirate_ball`,
`pirate_rock`, `pirate_barrel`, `pirate_crate`, `pirate_chest`, `pirate_keg` из `lowpoly_meshes.py`.
У каждой модели одна часть `body` с той же точкой вращения и теми же габаритами, что у пиратской
и космической: демки ставят их, крутят и кидают по этим числам. Атласы тех же размеров, лицо
ящика и ларя во второй четверти ленты (как у зеркала), крышки и торцы в тех же местах атласа.
Плотный набор «продвинутых» выходит из тех же функций (`lm.DENSE`).

Слоты по составу сеттинга (`docs/specs/settings.md`):
    coin   золотая монета с короной (бонус),
    bottle зелье в круглой колбе с пробкой (бонус, мишень и снаряд метателя),
    ball   горящий смоляной шар катапульты (снаряд),
    rock   замшелый валун с осколком (препятствие),
    barrel стог сена с куполом, стянутый верёвкой (препятствие),
    crate  тюк парусины в верёвках с красной печатью (препятствие),
    chest  окованный дубовый ларь с золотым замком (проп),
    keg    кожаный набивной мяч со шнуровкой (мяч).

    python3 tools/castles_mesh_items.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Цвета сеттинга (как в `castles_mesh_chars` и палитре 16/32 `castles16.PALETTE`).
BLACK = rgb("0E0D14")
WHITE = rgb("EEF0F4")
STEEL, STEEL_D, STEEL_L, STEEL_DD = rgb("A9B1BE"), rgb("626A7A"), rgb("DCE2EC"), rgb("3C4150")
RED, RED_D, RED_L = rgb("B02A2E"), rgb("6E1618"), rgb("DA4A4C")
GOLD, GOLD_D, GOLD_L = rgb("E0B040"), rgb("9A7020"), rgb("F6DC86")
LEATHER, LEATHER_L, LEATHER_D = rgb("9A6638"), rgb("C08A52"), rgb("5E3C22")
WOOD, WOOD_D, WOOD_L = rgb("B87C4A"), rgb("7A4F2E"), rgb("D49A62")
OAK, OAK_D, OAK_L = rgb("6A4428"), rgb("3A2418"), rgb("8C5E38")
STRAW, STRAW_D, STRAW_L = rgb("E3C25A"), rgb("B58A32"), rgb("F5E08E")
MOSS, MOSS_D, MOSS_L = rgb("388A4A"), rgb("1C4038"), rgb("8FCF58")
GRANITE, GRANITE_D, GRANITE_L = rgb("8A8C98"), rgb("575A68"), rgb("B8BAC4")
CANVAS, CANVAS_D, CANVAS_L = rgb("D8C79A"), rgb("A8956A"), rgb("EBDFB8")
ROPE, ROPE_D, ROPE_L = rgb("B08852"), rgb("6E4E2C"), rgb("D4AC72")
PITCH, PITCH_D = rgb("2E2220"), rgb("150E0E")
EMBER, FLAME = rgb("F0802A"), rgb("F8D24C")
GLASS, GLASS_D = rgb("D6ECF2"), rgb("8FB4C4")


def planks_h(a, x, y, w, h, step, base=OAK, dark=OAK_D, light=OAK_L):
    """Горизонтальные доски: тёмные щели, светлая кромка, редкие сучки и волокна."""
    a.rect(x, y, w, h, base)
    for j in range(0, h, step):
        tone = a.rng.uniform(0.88, 1.1)
        a.rect(x, y + j, w, step, mul(base, tone))
        a.rect(x, y + j, w, 1, light if j else mul(light, 0.9))
        if j + step - 1 < h:
            a.rect(x, y + j + step - 1, w, 1, dark)
    for _ in range(max(2, w * h // 60)):
        a.px(x + a.rng.randrange(w), y + a.rng.randrange(h), dark)
    for _ in range(max(1, w * h // 120)):
        i, j = a.rng.randrange(w), a.rng.randrange(h)
        a.px(x + i, y + j, mul(light, 1.1))


def studs(a, xs, y, light=STEEL_L, dark=STEEL_DD):
    """Заклёпки с бликом и тенью под ним."""
    for x in xs:
        a.px(x, y, light)
        a.px(x, y + 1, dark)


def straw_field(a, x, y, w, h, tone=1.0):
    """Солома: вертикальные соломины разной яркости, редкие тёмные и светлые нити."""
    a.rect(x, y, w, h, mul(STRAW, tone))
    for i in range(w):
        for j in range(h):
            r = a.rng.random()
            if r < 0.18:
                a.px(x + i, y + j, mul(STRAW_D, tone))
            elif r < 0.3:
                a.px(x + i, y + j, mul(STRAW_L, tone))
        if a.rng.random() < 0.45:
            top = a.rng.randrange(h)
            for j in range(top, min(h, top + a.rng.randrange(3, 7))):
                a.px(x + i, y + j, mul(STRAW_L, tone))


def castles_coin():
    """Золотая монета с короной: восьмигранный диск на ребре, на аверсе трёхзубая корона с
    камнями, по краю гладкий валик и рубчатый гурт."""
    a = lm.Atlas(32, 32, 205)
    field = mul(GOLD, 0.6)
    a.rect(0, 0, 16, 16, field)
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            if d > 6.7:
                a.px(i, j, GOLD_D)
            elif d > 5.6:
                a.px(i, j, GOLD_L if i + j < 15 else GOLD)
            elif d > 5.0:
                a.px(i, j, GOLD_D)
    # Корона: маска зубцов и тульи, вокруг тёмная обводка, камни в тулье.
    mask = ("#...##...#",
            "##.####.##",
            "##########",
            "##########",
            "##########",
            "##########")
    crown = set()
    for j, row in enumerate(mask):
        for i, ch in enumerate(row):
            if ch == "#":
                crown.add((3 + i, 5 + j))
    for x, y in crown:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in crown:
                a.px(x + dx, y + dy, mul(GOLD_D, 0.5))
    for x, y in crown:
        a.px(x, y, GOLD_L if y < 8 else GOLD)
    a.rect(3, 10, 10, 1, GOLD_D)
    for x, y in ((3, 5), (7, 5), (8, 5), (12, 5)):
        a.px(x, y, WHITE)
    a.px(5, 8, RED), a.px(7, 8, STEEL_L), a.px(8, 8, STEEL_L), a.px(10, 8, RED)
    # Блики на валике.
    for x, y in ((3, 3), (4, 2), (12, 12), (11, 13)):
        a.px(x, y, WHITE)
    a.noise(0, 0, 16, 16, 0.05)
    face = a.region(0, 0, 16, 16)
    for j in range(4):
        a.rect(16, j, 16, 1, GOLD_D if j % 2 == 0 else GOLD)
    for x in range(16, 32, 2):
        a.px(x, 1, GOLD_L)
    edge = a.region(16, 0, 16, 4)
    return lm.Model("coin", a).part(
        "body", (0.0, 0.35, 0.0),
        lm.at(lm.rot(lm.loft([(-0.04, 0.28, 0.28), (0.04, 0.28, 0.28)], edge, 8, math.pi / 8.0, caps=(face, face), flat=True),
                     rx=90.0), 0.0, 0.35))


def castles_bottle():
    """Зелье: круглая стеклянная колба с рубиновой жидкостью, длинным горлом и сургучной пробкой.
    Мишень и снаряд метателя, размеры бутылки."""
    a = lm.Atlas(16, 16, 247)
    # Колонка строк сверху вниз: пробка 0..2, горло 2..4, плечо 4..6, пузырь 6..12 (семь колец).
    a.rect(0, 0, 16, 12, GLASS)
    # Жидкость от плеча до дна, глубже книзу.
    a.rect(0, 5, 16, 7, RED)
    a.rect(0, 5, 16, 1, RED_L)
    a.rect(0, 9, 16, 3, RED_D)
    a.rect(0, 11, 16, 1, mul(RED_D, 0.7))
    for x in (1, 5, 9, 13):
        a.px(x, 8, RED_L)
    # Горло: стекло с тенью справа от оси и светлой полосой.
    for x in range(16):
        a.px(x, 3, GLASS if x % 4 != 3 else GLASS_D)
        a.px(x, 2, GLASS_D if x % 4 == 3 else GLASS)
        a.px(x, 4, GLASS if x % 4 != 3 else GLASS_D)
    # Пробка с золотой печатью-кольцом под ней.
    a.rect(0, 0, 16, 2, WOOD), a.rect(0, 0, 16, 1, WOOD_L)
    a.rect(0, 2, 16, 1, GOLD)
    for x in (2, 6, 10, 14):
        a.px(x, 1, WOOD_D)
    # Этикетка спереди (середина ленты) с красным пятном и блик вдоль колбы.
    a.rect(6, 7, 5, 3, CANVAS_L), a.rect(6, 9, 5, 1, CANVAS_D)
    a.px(8, 8, RED), a.px(9, 8, RED_D)
    a.rect(3, 6, 1, 4, RED_L)
    a.px(3, 6, WHITE)
    a.shade(0, 0, 16, 12, 1.1, 0.85, 0.78)
    a.noise(0, 0, 16, 12, 0.04)
    body = a.region(0, 0, 16, 12)
    a.rect(0, 12, 4, 4, WOOD), a.px(1, 13, WOOD_L), a.px(2, 14, WOOD_D)
    cork = a.region(0, 12, 4, 4)
    a.rect(4, 12, 4, 4, RED_D), a.px(5, 13, RED)
    under = a.region(4, 12, 4, 4)
    rings = [(0.0, 0.07, 0.07), (0.03, 0.105, 0.105), (0.13, 0.115, 0.115), (0.23, 0.095, 0.095),
             (0.31, 0.045, 0.045), (0.4, 0.04, 0.04), (0.5, 0.06, 0.06)]
    return lm.Model("bottle", a).part("body", (0.0, 0.25, 0.0), lm.loft(rings, body, 6, caps=(under, cork)))


def castles_ball():
    """Смоляной шар катапульты: снаряд. Чёрный ком смолы в трещинах горящего угля, сверху
    жарче, обвязан тёмными витками верёвки."""
    a = lm.Atlas(16, 16, 249)
    a.rect(0, 0, 16, 16, PITCH)
    # Трещины жара: ломаные ленты вокруг, к верху всё ярче.
    for k in range(6):
        x = k * 16 // 6 + 1
        for j in range(16):
            xx = x + (1 if (j // 3 + k) % 2 else 0)
            if (j + k) % 5 != 4:
                a.px(xx, j, EMBER if j > 4 else FLAME)
            if j > 2 and (j + k) % 3 == 0:
                a.px(xx + 1, j, PITCH_D)
    # Живой жар сверху (макушка и верхний пояс).
    a.rect(0, 0, 16, 2, FLAME)
    for x in range(16):
        if x % 2:
            a.px(x, 2, EMBER)
        if x % 3 == 0:
            a.px(x, 3, EMBER)
    # Две витка верёвки поперёк, чёрные пятна смолы.
    for x in range(16):
        a.px(x, 7, ROPE_D)
        a.px(x, 12, ROPE_D)
        if x % 2 == 0:
            a.px(x, 8, PITCH_D)
    for x, y in ((3, 10), (9, 5), (12, 9), (6, 14), (14, 14)):
        a.px(x, y, PITCH_D), a.px(x + 1, y, PITCH_D)
    a.shade(0, 0, 16, 16, 1.2, 0.6, 0.85)
    a.noise(0, 0, 16, 16, 0.07)
    glow = a.region(0, 0, 16, 16)
    r = 0.18
    rings = [(r - r * math.cos(t), r * math.sin(t), r * math.sin(t)) for t in (0.35, 1.0, math.pi / 2.0, math.pi - 1.0, math.pi - 0.35)]
    return lm.Model("ball", a).part("body", (0.0, r, 0.0), lm.loft(rings, glow, 6, caps=(glow, glow)))


def castles_rock():
    """Валун: серый гранит в трещинах, на макушке и в складках мох с жёлтыми цветочками, рядом
    осколок камня."""
    a = lm.Atlas(32, 32, 207)
    a.rect(0, 0, 32, 32, GRANITE)
    for _ in range(50):
        x, y = a.rng.randrange(32), a.rng.randrange(32)
        a.rect(x, y, a.rng.randrange(1, 4), 1, GRANITE_D if a.rng.random() < 0.55 else GRANITE_L)
    # Трещины и сколы: тёмные изломанные линии.
    for x0, y0, dx in ((6, 14, 1), (20, 18, -1), (12, 26, 1), (26, 8, -1)):
        x, y = x0, y0
        for k in range(9):
            a.px(x, y, BLACK if k % 3 else GRANITE_D)
            y += 1
            x += dx if k % 3 != 1 else 0
    # Мох: заплатки сверху (верхние кольца и крышка в середине куска) и в нижних складках.
    for cx, cy, rx, ry in ((16, 16, 5, 5), (6, 4, 7, 3), (22, 6, 8, 3), (14, 10, 4, 2), (28, 22, 4, 3), (4, 25, 5, 3)):
        for j in range(-ry - 1, ry + 2):
            for i in range(-rx - 1, rx + 2):
                d = math.hypot(i / rx, j / ry)
                if d <= 1.0 and a.rng.random() < 0.9 - 0.4 * d:
                    a.px(cx + i, cy + j, MOSS_L if (i + j) % 3 == 0 else (MOSS if a.rng.random() < 0.7 else MOSS_D))
    for x, y in ((7, 4), (21, 6), (16, 15), (28, 22), (5, 25)):
        a.px(x, y, GOLD_L)
    a.shade(0, 0, 32, 32, 1.15, 0.75, 0.9)
    a.noise(0, 0, 32, 32, 0.1)
    stone = a.region(0, 0, 32, 32)
    return lm.Model("rock", a).part(
        "body", (0.0, 0.0, 0.0),
        lm.loft([(0.0, 0.52, 0.5), (0.16, 0.57, 0.48, -0.03, 0.02), (0.44, 0.44, 0.34, 0.04, -0.04), (0.66, 0.2, 0.16, 0.08, 0.0)],
                stone, 6, 0.9, caps=(None, stone), flat=True)
        + lm.at(lm.loft([(0.0, 0.26, 0.28), (0.12, 0.25, 0.22, -0.02, 0.0), (0.3, 0.1, 0.09)], stone, 5, 0.2,
                        caps=(None, stone), flat=True), 0.5, 0.0, 0.3))


def castles_barrel():
    """Стог сена: золотой цилиндр с куполом, перетянутый верёвкой под куполом, соломины стоят
    вертикально, на макушке вихрь соломы."""
    a = lm.Atlas(32, 32, 209)
    # Лента из пяти колец: низ 24..18, тулово 18..12, плечо 12..6, купол 6..0.
    straw_field(a, 0, 0, 32, 24)
    for x in range(32):
        # Купол светлее, у земли тёмная подгнившая кромка.
        if x % 3 != 1:
            a.px(x, 1, STRAW_L)
        a.px(x, 23, STRAW_D)
        if x % 2 == 0:
            a.px(x, 22, STRAW_D)
    # Две верёвки: под куполом и у земли, с узлами.
    for y in (12, 19):
        a.rect(0, y, 32, 2, ROPE)
        a.rect(0, y, 32, 1, ROPE_L)
        a.rect(0, y + 1, 32, 1, ROPE_D)
        for x in range(1, 32, 4):
            a.px(x, y, ROPE_D)
    a.rect(14, 12, 3, 3, ROPE_D), a.px(15, 12, ROPE_L)
    # Торчащие прутья соломы над верёвкой.
    for x in range(0, 32, 3):
        a.px(x, 10, STRAW_D), a.px(x + 1, 9, STRAW_L)
    a.shade(0, 0, 32, 24, 1.15, 0.8, 0.82)
    a.noise(0, 0, 32, 24, 0.05)
    side = a.region(0, 0, 32, 24)
    # Макушка: солома завитком к центру.
    a.rect(0, 24, 8, 8, STRAW)
    for i in range(8):
        for j in range(8):
            d = math.hypot(i - 3.5, j - 3.5)
            ang = math.atan2(j - 3.5, i - 3.5)
            if int(d * 1.6 + ang * 1.2 / math.pi * 2) % 2 == 0:
                a.px(i, 24 + j, STRAW_D)
    a.px(3, 27, STRAW_L), a.px(4, 28, STRAW_L)
    a.noise(0, 24, 8, 8, 0.05)
    lid = a.region(0, 24, 8, 8)
    rings = [(0.0, 0.31, 0.31), (0.08, 0.37, 0.37), (0.6, 0.37, 0.37), (0.76, 0.27, 0.27), (0.86, 0.1, 0.1)]
    return lm.Model("barrel", a).part("body", (0.0, 0.0, 0.0), lm.loft(rings, side, 8, caps=(lid, lid)))


def castles_crate():
    """Тюк: куб парусины, туго обвязан верёвками крест-накрест, на лице красная печать с
    золотой короной, на другой грани торговая метка."""
    a = lm.Atlas(32, 32, 211)
    # Лента из четырёх граней 8×16: плетение парусины.
    a.rect(0, 0, 32, 16, CANVAS)
    for j in range(16):
        for i in range(32):
            if (i + j) % 2 == 0:
                a.px(i, j, CANVAS_L)
            elif (i // 2 + j) % 3 == 0:
                a.px(i, j, CANVAS_D)
    for x in (0, 8, 16, 24):
        # Шов по краю грани и складка парусины.
        a.rect(x, 0, 1, 16, CANVAS_D)
        a.rect(x + 7, 0, 1, 16, mul(CANVAS_D, 0.85))
        # Верёвки: две перетяжки поперёк и одна по центру грани вдоль.
        for y in (3, 11):
            a.rect(x, y, 8, 2, ROPE)
            a.rect(x, y, 8, 1, ROPE_L)
            a.rect(x, y + 1, 8, 1, ROPE_D)
        a.rect(x + 3, 0, 1, 16, ROPE), a.rect(x + 4, 0, 1, 16, ROPE_D)
        for y in (3, 11):
            a.px(x + 3, y, ROPE_L), a.px(x + 3, y + 1, ROPE_D)
    # Передняя грань (вторая четверть): сургучная печать с короной на пересечении верёвок.
    for j in range(5, 11):
        for i in range(10, 14):
            d = math.hypot((i - 11.5) / 2.3, (j - 7.5) / 3.2)
            if d <= 1.0:
                a.px(i, j, RED if d < 0.8 else RED_D)
    a.px(10, 5, CANVAS), a.px(13, 5, CANVAS)
    a.px(11, 6, RED_L), a.px(10, 7, RED_L)
    a.rect(10, 7, 4, 2, GOLD), a.px(10, 6, GOLD_L), a.px(12, 6, GOLD_L), a.px(13, 6, GOLD_L)
    a.rect(10, 9, 4, 1, GOLD_D)
    # Задняя грань: трафаретная метка торговца (ключ и две полосы) тёмной краской.
    a.rect(26, 6, 3, 1, STEEL_DD), a.rect(26, 8, 2, 1, STEEL_DD), a.rect(27, 7, 1, 4, STEEL_DD)
    a.shade(0, 0, 32, 16, 1.05, 0.8, 1.0)
    a.noise(0, 0, 32, 16, 0.04)
    side = a.region(0, 0, 32, 16)
    # Верх: парусина с крестом верёвок, узлом по центру и биркой.
    a.rect(0, 16, 16, 16, CANVAS)
    for j in range(16):
        for i in range(16):
            if (i + j) % 2 == 0:
                a.px(i, 16 + j, CANVAS_L)
            elif (i // 2 + j) % 3 == 0:
                a.px(i, 16 + j, CANVAS_D)
    a.rect(0, 16, 16, 1, CANVAS_D), a.rect(0, 31, 16, 1, mul(CANVAS_D, 0.8))
    a.rect(0, 16, 1, 16, CANVAS_D), a.rect(15, 16, 1, 16, mul(CANVAS_D, 0.8))
    a.rect(7, 17, 2, 14, ROPE), a.rect(1, 23, 14, 2, ROPE)
    a.rect(7, 17, 1, 14, ROPE_L), a.rect(1, 23, 14, 1, ROPE_L)
    a.rect(8, 17, 1, 14, ROPE_D), a.rect(1, 24, 14, 1, ROPE_D)
    a.rect(6, 22, 4, 4, ROPE_D), a.rect(7, 23, 2, 2, ROPE_L)
    a.rect(10, 18, 4, 3, CANVAS_L), a.rect(10, 20, 4, 1, CANVAS_D), a.px(11, 19, RED)
    a.noise(0, 16, 16, 16, 0.04)
    top = a.region(0, 16, 16, 16)
    return lm.Model("crate", a).part("body", (0.0, 0.0, 0.0), lm.at(lm.box((0.85, 0.85, 0.85), side, top, top), 0.0, 0.425))


def castles_chest():
    """Окованный ларь: тёмный дуб, стальные полосы с заклёпками, на лице золотой замок с
    замочной скважиной и скоба на крышке, на верху герб-корона."""
    a = lm.Atlas(64, 32, 213)
    # Корпус (двенадцать строк): доски, полосы по центру граней, кант сверху и снизу.
    planks_h(a, 0, 0, 64, 12, 4)
    a.rect(0, 0, 64, 1, STEEL_D), a.rect(0, 11, 64, 1, STEEL_DD)
    for x in (7, 23, 39, 55):
        a.rect(x, 0, 3, 12, STEEL_D)
        a.rect(x, 0, 1, 12, STEEL)
        a.rect(x + 2, 0, 1, 12, STEEL_DD)
        studs(a, (x + 1,), 2), studs(a, (x + 1,), 8)
    # Лицо (16..32): золотая накладка замка на центральной полосе и тёмная скважина.
    a.rect(21, 3, 6, 6, GOLD), a.rect(21, 3, 6, 1, GOLD_L), a.rect(21, 8, 6, 1, GOLD_D)
    a.rect(21, 3, 1, 6, GOLD_L), a.rect(26, 3, 1, 6, GOLD_D)
    a.rect(23, 4, 2, 2, OAK_D), a.rect(23, 6, 2, 2, OAK_D), a.px(24, 5, BLACK)
    a.px(22, 4, STEEL_L), a.px(25, 7, STEEL_L)
    for x, y in ((4, 6), (12, 4), (36, 5), (44, 7), (60, 4)):
        a.px(x, y, OAK_L)
    a.shade(0, 0, 64, 12, 1.05, 0.8, 1.0)
    a.noise(0, 0, 64, 12, 0.04)
    side = a.region(0, 0, 64, 12)
    # Бока крышки (восемь строк): доски, полосы, скоба замка на лице, стальной кант снизу.
    planks_h(a, 0, 12, 64, 8, 4)
    for x in (7, 23, 39, 55):
        a.rect(x, 12, 3, 8, STEEL_D)
        a.rect(x, 12, 1, 8, STEEL)
        a.rect(x + 2, 12, 1, 8, STEEL_DD)
    a.rect(22, 12, 4, 7, GOLD), a.rect(22, 12, 1, 7, GOLD_L), a.rect(25, 12, 1, 7, GOLD_D)
    a.px(23, 17, BLACK), a.px(24, 17, BLACK)
    a.rect(0, 19, 64, 1, STEEL_DD)
    a.noise(0, 12, 64, 8, 0.04)
    lid_side = a.region(0, 12, 64, 8)
    # Верх крышки: доски вдоль, две полосы, золотая корона в центре на тёмной плашке.
    planks_h(a, 0, 20, 24, 12, 4)
    for x in (3, 18):
        a.rect(x, 20, 3, 12, STEEL_D)
        a.rect(x, 20, 1, 12, STEEL)
        a.rect(x + 2, 20, 1, 12, STEEL_DD)
        studs(a, (x + 1,), 22), studs(a, (x + 1,), 28)
    a.rect(8, 23, 8, 6, OAK_D)
    a.rect(9, 24, 6, 4, RED_D)
    for x, y in ((9, 24), (12, 23), (14, 24)):
        a.px(x, y, GOLD)
    a.rect(9, 25, 6, 2, GOLD), a.rect(9, 27, 6, 1, GOLD_D)
    a.px(10, 26, RED), a.px(13, 26, RED), a.px(9, 25, GOLD_L)
    a.noise(0, 20, 24, 12, 0.04)
    lid_top = a.region(0, 20, 24, 12)
    a.rect(24, 20, 4, 4, OAK_D)
    under = a.region(24, 20, 4, 4)
    return lm.Model("chest", a).part("body", (0.0, 0.0, 0.0),
                                     lm.at(lm.box((0.8, 0.4, 0.5), side, None, under), 0.0, 0.2)
                                     + lm.at(lm.box((0.82, 0.2, 0.52), lid_side, lid_top, None, (0.8, 0.55)), 0.0, 0.5))


def castles_keg():
    """Набивной мяч: круглый кожаный шар из четырёх долек со шнуровкой по швам и по экватору,
    летит и крутится."""
    a = lm.Atlas(16, 16, 269)
    a.rect(0, 0, 16, 12, LEATHER)
    for j in range(12):
        for i in range(16):
            r = a.rng.random()
            if r < 0.07:
                a.px(i, j, LEATHER_D)
            elif r < 0.15:
                a.px(i, j, LEATHER_L)
    # Дольки светлее к середине, швы: четыре меридиана и экватор, по ним шнуровка через раз.
    for x in (0, 4, 8, 12):
        a.rect(x, 0, 1, 12, LEATHER_D)
        for y in range(1, 12, 3):
            a.px(x, y, CANVAS_L)
            a.px((x + 15) % 16, y, CANVAS)
            a.px((x + 1) % 16, y, CANVAS)
    a.rect(0, 6, 16, 1, LEATHER_D)
    for x in range(1, 16, 3):
        a.px(x, 6, CANVAS_L)
        a.px(x, 5, CANVAS)
        a.px(x, 7, CANVAS)
    for x in (2, 6, 10, 14):
        a.px(x, 3, LEATHER_L), a.px(x, 4, LEATHER_L)
    a.shade(0, 0, 16, 12, 1.15, 0.78, 0.85)
    a.noise(0, 0, 16, 12, 0.05)
    side = a.region(0, 0, 16, 12)
    a.rect(0, 12, 4, 4, LEATHER)
    a.rect(0, 13, 4, 1, LEATHER_D), a.rect(1, 12, 1, 4, LEATHER_D)
    a.px(0, 12, CANVAS_L), a.px(2, 14, CANVAS_L), a.px(3, 15, LEATHER_L)
    cap = a.region(0, 12, 4, 4)
    rings = [(0.0, 0.06, 0.06), (0.04, 0.115, 0.115), (0.09, 0.142, 0.142), (0.15, 0.15, 0.15),
             (0.21, 0.142, 0.142), (0.26, 0.115, 0.115), (0.3, 0.06, 0.06)]
    return lm.Model("keg", a).part("body", (0.0, 0.15, 0.0), lm.loft(rings, side, 8, caps=(cap, cap)))


MODELS = [castles_coin, castles_bottle, castles_ball, castles_rock, castles_barrel, castles_crate, castles_chest, castles_keg]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        out = sys.argv[sys.argv.index("--preview") + 1]
        models = [f() for f in MODELS]
        # Лист выше 1500 пикселей делится: по шесть моделей, суффиксы _b, _c.
        base, ext = os.path.splitext(out)
        for n in range(0, len(models), 6):
            mesh_preview.save_models(out if n == 0 else "%s_%s%s" % (base, "bcdef"[n // 6 - 1], ext), models[n:n + 6])
    for f in MODELS:
        m = f()
        print("%-7s частей %d, треугольников %d, атлас %d×%d" % (m.name, len(m.parts), m.tris(), m.atlas.w, m.atlas.h))
