#!/usr/bin/env python3
"""Крупный реквизит и транспорт «Фэнтези» для low poly и «продвинутых» (#137): зеркала моделей
космоса из `space_mesh_big.py` (а те зеркала пиратских из `lowpoly_meshes.py`) с теми же именами
слотов, частей и точками вращения, тем же нулём и габаритами, чтобы десять 3D-демок работали
без правок. Цвета из основы 16/32 (`fantasy16.PALETTE`) через `fantasy_mesh_chars`.

  cannon      кристалл на треноге: гранёный кристалл в золотых обоймах (остриё в −Z, как
              ствол пушки), деревянная вилка и три ноги
  palm        дерево с сиреневой листвой; атлас: слева кора ствола, справа ветка листвы с
              вырезом по прозрачности, корень ветки вверху (эти же половины берёт
              `ThreedScreen.add_palm`, кора повторяется по высоте без шва)
  flag        знамя гильдии с ласточкиным хвостом: части `pole` и `cloth`
  lighthouse  башня мага: скала, кривая каменная башня, светлица с фахверком, синяя крыша
              шляпой с загнутым кончиком, боковая башенка; высота маяка
  cart        гномья вагонетка с кристаллом: `body`, оси `axle_f`, `axle_r`; на месте паруса
              рунный змей-ромб на мачте
  cart_rival  гоблинская вагонетка: те же части, рог-таран, котёл со слизью, рваный парус
              из шкуры
  pistol      волшебная палочка в руке мага (синий рукав с золотой каймой), вид от первого
              лица, кристалл смотрит в −Z, ноль в кулаке
  hoop        рунное кольцо на каменной плите с лианами вместо сетки, стойка из ствола;
              кольцо там же и того же размера

    python3 tools/fantasy_mesh_big.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from lowpoly_meshes import Atlas, Model, at, box, flip, loft, mul, quad, rgb, rot  # noqa: E402
from fantasy_mesh_chars import (BLACK, BONE, CRYSTAL, CRYSTAL_D, CRYSTAL_L, DUSK, DUSK_D, GOBLIN,  # noqa: E402
                                GOBLIN_D, GOBLIN_L, GOLD, GOLD_D, GOLD_L, PLUM, RED, RED_D, ROBE,
                                ROBE_D, ROBE_L, SKIN, SKIN_D, STONE, STONE_D, VIOLET, WOOD, WOOD_D,
                                WOOD_L)

# Остальные цвета набора из той же палитры: светлая листва, железо гномов, шкура, светлый камень.
LILAC = rgb("C89AF0")
IRON, IRON_D, IRON_L = rgb("5C5676"), rgb("322C48"), rgb("8E88AA")
HIDE, HIDE_D = rgb("B8905E"), rgb("7A5638")
STONE_L = rgb("CEC8E0")

# Руны 3×5: строки сверху вниз.
GLYPHS = (("101", "101", "010", "010", "010"), ("010", "111", "010", "010", "101"),
          ("110", "101", "110", "100", "100"), ("111", "001", "010", "100", "111"),
          ("010", "101", "111", "101", "101"), ("100", "110", "101", "110", "100"))


def rune(a, x, y, k, c):
    """Руна номер `k` в клетке 3×5."""
    for j, row in enumerate(GLYPHS[k % len(GLYPHS)]):
        for i, bit in enumerate(row):
            if bit == "1":
                a.px(x + i, y + j, c)


def bark(a, x, y, w, h, base=WOOD, dark=WOOD_D, light=WOOD_L):
    """Кора и волокно: волнистые борозды вдоль высоты; по высоте повторяется без шва."""
    for j in range(h):
        t = 2.0 * math.pi * j / h
        for i in range(w):
            v = math.sin((i + 1.3 * math.sin(t * 2.0 + i * 0.7)) * 1.9)
            if v > 0.6:
                c = dark
            elif v < -0.7:
                c = light
            else:
                c = mul(base, 1.0 + 0.07 * math.sin(t * 3.0 + i * 0.9))
            # Короткие поперечные трещины, чтобы борозды не шли сплошными полосами.
            if (i * 5 + j * 3) % 23 == 0:
                c = dark
            a.px(x + i, y + j, c)


def masonry(a, x, y, w, h, base=STONE, bw=8, bh=4):
    """Кладка: камни вперевязку, у каждого свой тон, тёмный шов и светлая верхняя кромка."""
    for row, j0 in enumerate(range(0, h, bh)):
        shift = (row % 2) * (bw // 2)
        tones = [a.rng.uniform(0.86, 1.08) for _ in range(w // bw + 2)]
        for j in range(j0, min(j0 + bh, h)):
            for i in range(w):
                k = (i + shift) // bw
                c = mul(base, tones[k])
                if j == j0 or (i + shift) % bw == 0:
                    c = mul(base, 0.56)
                elif j == j0 + 1:
                    c = mul(base, tones[k] * 1.13)
                a.px(x + i, y + j, c)
    a.noise(x, y, w, h, 0.05)


def facets(a, x, y, w, h, n=6, glow=True):
    """Кристалл: `n` граней вокруг, у каждой свой тон и светлое ребро, внутри белые искры;
    кверху куска (к острию) светлее."""
    tones = (1.0, 0.7, 1.22, 0.84, 1.1, 0.62)
    for j in range(h):
        lift = 1.0 + (0.28 * (1.0 - j / max(h - 1, 1)) if glow else 0.0)
        for i in range(w):
            f = i * n // w
            c = mul(CRYSTAL, tones[f % 6] * lift)
            if (i * n) % w < n:
                c = CRYSTAL_L
            elif (i * 3 + j * 5) % 17 == 0:
                c = BONE
            elif (i + j * 2) % 9 == 0:
                c = mul(CRYSTAL_D, lift)
            a.px(x + i, y + j, c)


def moss(a, x, y, w, h, amount=0.35):
    """Мох поверх нарисованного: пятна гуще к верху куска."""
    for j in range(h):
        for i in range(w):
            if a.rng.random() < amount * (1.0 - j / max(h, 1)):
                a.px(x + i, y + j, GOBLIN_D if (i + j) % 3 else GOBLIN)


def gold_band(a, x, y, w, h):
    """Золотая обойма: светлая кромка сверху, тёмная снизу, насечка рун."""
    a.rect(x, y, w, h, GOLD)
    a.rect(x, y, w, 1, GOLD_L)
    a.rect(x, y + h - 1, w, 1, GOLD_D)
    for i in range(1, w, 3):
        a.px(x + i, y + h // 2, GOLD_D)


def fantasy_cannon():
    """Кристалл на треноге: длинный гранёный кристалл лежит в деревянной вилке, две золотые
    обоймы держат его, остриё смотрит в −Z; снизу каменная ступица и три расставленные ноги."""
    a = Atlas(64, 32, 419)
    facets(a, 0, 0, 32, 16)
    crys = a.region(0, 0, 32, 16)
    gold_band(a, 32, 0, 16, 4)
    band = a.region(32, 0, 16, 4)
    # Торец обоймы: золотое кольцо, внутри бирюза.
    a.rect(48, 0, 8, 8, GOLD_D)
    a.rect(49, 1, 6, 6, GOLD)
    a.rect(50, 2, 4, 4, CRYSTAL_D)
    a.rect(51, 3, 2, 2, CRYSTAL_L)
    face = a.region(48, 0, 8, 8)
    # Дерево вилки и ног: волокно, золотые гвозди, внизу тёмный башмак.
    bark(a, 0, 16, 32, 16)
    a.rect(0, 30, 32, 2, IRON_D)
    a.rect(0, 29, 32, 1, GOLD_D)
    for x in range(3, 32, 8):
        a.px(x, 19, GOLD), a.px(x + 4, 25, GOLD)
    a.shade(0, 16, 32, 16, 1.1, 0.85, 0.85)
    a.noise(0, 16, 32, 16, 0.06)
    wood = a.region(0, 16, 32, 16)
    # Ступица: сиреневый камень со светящимися рунами по кругу.
    masonry(a, 32, 8, 24, 8, STONE, 6, 8)
    for k in range(4):
        rune(a, 34 + k * 6, 10, k, CRYSTAL)
    hub = a.region(32, 8, 24, 8)
    a.rect(32, 16, 8, 8, STONE_D)
    a.rect(33, 17, 6, 6, STONE)
    a.rect(35, 19, 2, 2, CRYSTAL)
    cap = a.region(32, 16, 8, 8)

    lay = lambda tris: at(rot(tris, rx=-90.0), 0.0, 0.56, -0.1)
    tris = lay(loft([(-0.5, 0.0, 0.0), (-0.36, 0.15, 0.15), (0.16, 0.17, 0.17), (0.56, 0.0, 0.0)], crys, 6, flat=True))
    for y in (-0.31, 0.06):
        tris += lay(loft([(y, 0.2, 0.2), (y + 0.09, 0.2, 0.2)], band, 8, caps=(face, face)))
    # Вилка: поперечина под кристаллом и два рога по бокам до обойм.
    tris += at(box((0.5, 0.08, 0.5), wood, wood, wood), 0.0, 0.36, 0.02)
    for x in (-0.22, 0.22):
        tris += at(box((0.07, 0.3, 0.14), wood, wood, wood), x, 0.5, 0.02)
    tris += at(loft([(0.2, 0.11, 0.11), (0.33, 0.15, 0.15)], hub, 6, caps=(cap, cap), flat=True), 0.0, 0.0, 0.02)
    # Ноги: одна вперёд, две назад в стороны; верх уходит в ступицу.
    for fx, fz in ((0.0, -0.46), (-0.29, 0.44), (0.29, 0.44)):
        tris += loft([(0.0, 0.045, 0.045, fx, fz), (0.3, 0.035, 0.035, fx * 0.12, 0.02 + (fz - 0.02) * 0.12)], wood, 4,
                     math.pi / 4.0, caps=(cap, None))
    return Model("cannon", a).part("body", (0.0, 0.0, 0.0), tris)


# Гроздья ветки: (x, y, радиус) в клетке 16×32, корень ветки вверху.
BOUGH = ((7.5, 2.5, 2.0), (5.0, 6.5, 3.0), (10.5, 8.5, 3.0), (4.5, 12.5, 3.7), (11.0, 14.5, 3.7), (5.0, 19.5, 3.8),
         (10.5, 21.5, 3.6), (7.5, 26.5, 3.9), (7.5, 30.0, 1.6))


def fantasy_palm():
    """Дерево с сиреневой листвой: перекрученный ствол с корнями и крона куполом из трёх ярусов
    веток. Ветка это плоскость с вырезом по прозрачности: гроздья круглых листьев вдоль прутика
    с бирюзовыми цветками. Половины атласа те же, что у пальмы."""
    a = Atlas(32, 32, 421)
    # Кора: тёплое дерево, сиреневая тень, мох и светящиеся точки; по высоте без шва.
    bark(a, 0, 0, 16, 32)
    for k in range(7):
        x, y = (k * 5 + 2) % 16, (k * 9 + 3) % 32
        a.px(x, y, GOBLIN_D), a.px((x + 1) % 16, y, GOBLIN), a.px(x, (y + 1) % 32, GOBLIN_D)
    for k in range(4):
        a.px((k * 7 + 4) % 16, (k * 8 + 6) % 32, CRYSTAL)
    a.shade(0, 0, 16, 32, 1.0, 1.0, 0.68)
    a.noise(0, 0, 16, 32, 0.06)
    trunk = a.region(0, 0, 16, 32)
    # Ветка: прутик и гроздья; свет сверху слева, тень снизу справа.
    for y in range(0, 27):
        a.px(23, y, WOOD_D), a.px(24, y, WOOD)
    for cx, cy, r in BOUGH:
        for y in range(32):
            for x in range(16):
                dx, dy = x - cx, y - cy
                d = math.hypot(dx, dy)
                if d > r:
                    continue
                c = VIOLET
                if dx + dy < -r * 0.55:
                    c = LILAC
                elif dx + dy > r * 0.5 or d > r - 0.8:
                    c = PLUM
                elif (x * 3 + y * 5) % 7 == 0:
                    c = mul(VIOLET, 1.15)
                a.px(16 + x, y, c)
    for x, y in ((5, 6), (10, 13), (4, 19), (11, 22), (7, 27)):
        a.px(16 + x, y, CRYSTAL_L), a.px(17 + x, y, CRYSTAL)
    a.noise(16, 0, 16, 32, 0.05)
    leaf = a.region(16, 0, 16, 32)
    top = (0.55, 4.2, 0.1)
    tris = loft([(0.0, 0.34, 0.34), (0.3, 0.22, 0.22, 0.02, 0.0), (1.2, 0.18, 0.18, 0.12, -0.04), (2.3, 0.16, 0.16, 0.3, 0.06),
                 (3.3, 0.14, 0.14, 0.46, 0.1), (4.25, 0.1, 0.1, 0.55, 0.1)], trunk, 5)
    # Три яруса веток: нижние длинные свисают, средние в стороны, верхние короткие; вместе купол.
    for count, turn, lift, reach, droop, near, far in ((7, 0.3, 0.05, 1.45, 1.25, 0.45, 0.95), (6, 0.8, 0.26, 1.4, 0.6, 0.42, 0.9),
                                                       (4, 0.1, 0.42, 0.85, 0.12, 0.38, 0.7)):
        for k in range(count):
            ang = 2.0 * math.pi * k / count + turn
            d = (math.sin(ang), math.cos(ang))
            q = (math.cos(ang), -math.sin(ang))
            fall = droop + 0.1 * (k % 2)
            mid = (top[0] - d[0] * 0.25, top[1] + lift, top[2] - d[1] * 0.25)
            end = (top[0] + d[0] * reach, top[1] + lift - fall, top[2] + d[1] * reach)
            tris += quad((mid[0] - q[0] * near, mid[1], mid[2] - q[1] * near), (mid[0] + q[0] * near, mid[1], mid[2] + q[1] * near),
                         (end[0] + q[0] * far, end[1], end[2] + q[1] * far), (end[0] - q[0] * far, end[1], end[2] - q[1] * far), leaf)
    return Model("palm", a).part("body", (0.0, 0.0, 0.0), tris)


def fantasy_flag():
    """Знамя гильдии: фиолетовое полотно с ласточкиным хвостом, золотой круг и бирюзовый
    кристалл в нём; посох-древко с золотой обвивкой, наверху кристалл, внизу рунный камень.
    Полотно отдельной частью у древка."""
    a = Atlas(64, 32, 423)
    a.rect(0, 0, 32, 20, VIOLET)
    for x in (6, 13, 20, 27):
        a.rect(x, 0, 1, 20, PLUM)
        a.rect(x + 1, 0, 1, 20, mul(VIOLET, 1.14))
    a.rect(0, 0, 32, 2, GOLD), a.rect(0, 18, 32, 2, GOLD)
    a.rect(0, 2, 32, 1, GOLD_D), a.rect(0, 17, 32, 1, PLUM)
    # Знак гильдии: золотой круг, в нём кристалл ромбом, по сторонам звёзды.
    for j in range(20):
        for i in range(32):
            d = math.hypot(i - 13.5, j - 9.5)
            if 4.6 < d < 6.2:
                a.px(i, j, GOLD if (i + j) % 5 else GOLD_L)
            elif abs(i - 13.5) * 1.5 + abs(j - 9.5) < 4.6:
                a.px(i, j, CRYSTAL_L if i < 13 and j < 10 else CRYSTAL if i < 14 else CRYSTAL_D)
    for x, y in ((4, 6), (4, 13), (23, 5), (23, 14)):
        a.px(x, y, GOLD_L), a.px(x - 1, y, GOLD), a.px(x + 1, y, GOLD), a.px(x, y - 1, GOLD), a.px(x, y + 1, GOLD)
    # Кромка у древка и вырез хвоста.
    a.rect(0, 0, 2, 20, GOLD_D)
    for y in (3, 9, 15):
        a.px(0, y, GOLD_L), a.px(1, y, GOLD_L)
    a.noise(0, 0, 32, 20, 0.06)
    for i in range(22, 32):
        half = (i - 22) * 0.72
        for j in range(20):
            if abs(j - 9.5) < half:
                a.clear(i, j)
            elif abs(j - 9.5) < half + 1.2 and 2 <= j < 18:
                a.px(i, j, GOLD)
    cloth = a.region(0, 0, 32, 20)
    # Древко: дерево, золотая обвивка наискось, кольца.
    bark(a, 32, 0, 8, 32)
    for y in range(32):
        a.px(32 + (y // 2) % 8, y, GOLD)
    for y in (0, 10, 21):
        a.rect(32, y, 8, 2, GOLD), a.rect(32, y + 2, 8, 1, GOLD_D)
    a.shade(32, 0, 8, 32, 1.0, 0.9, 0.62)
    pole = a.region(32, 0, 8, 32)
    masonry(a, 40, 0, 8, 8, STONE, 4, 4)
    rune(a, 42, 2, 1, CRYSTAL)
    moss(a, 40, 0, 8, 3, 0.5)
    base = a.region(40, 0, 8, 8)
    facets(a, 48, 0, 8, 8, 4)
    gem = a.region(48, 0, 8, 8)
    gold_band(a, 56, 0, 8, 4)
    band = a.region(56, 0, 8, 4)
    m = Model("flag", a)
    m.part("pole", (0.0, 0.0, 0.0),
           loft([(0.0, 0.05, 0.05), (2.7, 0.04, 0.04)], pole, 4, caps=(None, base))
           + loft([(0.0, 0.26, 0.26), (0.14, 0.18, 0.18)], base, 5, caps=(None, base), flat=True)
           + loft([(2.62, 0.06, 0.06), (2.7, 0.06, 0.06)], band, 4, math.pi / 4.0, caps=(band, band), flat=True)
           + loft([(2.66, 0.0, 0.0), (2.74, 0.075, 0.075), (2.86, 0.0, 0.0)], gem, 4, flat=True))
    m.part("cloth", (0.04, 2.3, 0.0),
           quad((0.04, 2.62, 0.0), (1.0, 2.56, 0.0), (1.0, 2.02, 0.0), (0.04, 1.98, 0.0), cloth), "pole")
    return m


def window(a, x, y, glow=CRYSTAL, h=6):
    """Стрельчатое окно 4×h: тёмная рама, свет внутри, переплёт."""
    a.rect(x, y + 1, 4, h - 1, BLACK)
    a.rect(x + 1, y, 2, 1, BLACK)
    a.rect(x + 1, y + 1, 2, h - 2, glow)
    a.px(x + 1, y + 1, mul(glow, 1.3))
    a.rect(x + 1, y + h // 2, 2, 1, mul(glow, 0.6))


def fantasy_lighthouse():
    """Башня мага: ориентир на горизонте высотой с маяк. Обломок скалы с мхом, кривая башня из
    сиреневого камня с окнами по спирали и дверью, шире неё светлица с фахверком и золотыми
    окнами, синяя крыша шляпой с загнутым кончиком и звёздами (как шляпа героя), сбоку
    башенка, под светлицей знамя гильдии."""
    a = Atlas(64, 64, 425)
    # Ствол башни: кладка, окна по спирали, дверь, плющ, у земли темнее.
    masonry(a, 0, 0, 64, 28, STONE, 8, 4)
    for wx, wy in ((30, 3), (46, 8), (14, 13), (54, 18)):
        window(a, wx, wy)
    a.rect(29, 19, 6, 9, BLACK)
    a.rect(30, 18, 4, 1, BLACK)
    a.rect(30, 20, 4, 8, WOOD)
    a.rect(32, 20, 1, 8, WOOD_D)
    a.rect(30, 22, 4, 1, IRON_D), a.rect(30, 26, 4, 1, IRON_D)
    a.px(33, 24, GOLD)
    for x0, top in ((5, 9), (22, 15), (40, 17), (60, 6)):
        for y in range(top, 28):
            x = x0 + int(round(1.3 * math.sin(y * 0.8 + x0)))
            a.px(x, y, GOBLIN_D)
            if y % 3 == 0:
                a.px(x + 1, y, GOBLIN), a.px(x - 1, y + 1, GOBLIN_L)
    a.shade(0, 0, 64, 28, 1.06, 0.8, 0.72)
    hull = a.region(0, 0, 64, 28)
    # Светлица: светлая штукатурка в деревянном каркасе, окна через одну клетку.
    a.rect(0, 28, 64, 12, STONE_L)
    for x in range(0, 64, 8):
        a.rect(x, 28, 1, 12, WOOD_D)
        for j in range(8):
            if (x // 8) % 2 == 1:
                a.px(x + 1 + (j * 7) // 8, 30 + j, WOOD)
    for x in range(0, 64, 16):
        window(a, x + 3, 31, GOLD, 6)
    a.rect(0, 28, 64, 2, WOOD), a.rect(0, 28, 64, 1, WOOD_D)
    a.rect(0, 38, 64, 2, WOOD_D)
    for x in range(2, 64, 4):
        a.px(x, 39, WOOD_L)
    a.shade(0, 28, 64, 12, 1.0, 0.86, 0.75)
    a.noise(0, 28, 64, 12, 0.05)
    room = a.region(0, 28, 64, 12)
    # Крыша: синяя чешуя черепицы, золотые звёзды, по свесу золотая кайма.
    for j in range(16):
        for i in range(32):
            row = j // 3
            col = (i + (row % 2) * 2) % 4
            c = ROBE
            if j % 3 == 2:
                c = ROBE_D
            elif j % 3 == 0 and col in (1, 2):
                c = ROBE_L
            elif col == 0:
                c = ROBE_D
            a.px(i, 40 + j, c)
    for x, y in ((5, 43), (17, 46), (27, 42), (11, 50), (23, 51)):
        a.px(x, y, GOLD_L), a.px(x - 1, y, GOLD), a.px(x + 1, y, GOLD), a.px(x, y - 1, GOLD), a.px(x, y + 1, GOLD)
    a.rect(0, 54, 32, 2, GOLD), a.rect(0, 55, 32, 1, GOLD_D)
    a.shade(0, 40, 32, 16, 1.2, 0.9, 0.78)
    a.noise(0, 40, 32, 16, 0.05)
    roof = a.region(0, 40, 32, 16)
    # Скала: сверху мох и трава, ниже слоистый камень с корнями.
    a.rect(32, 40, 16, 12, STONE_D)
    for y in range(43, 52, 3):
        a.rect(32, y, 16, 1, mul(STONE_D, 0.66))
        for x in range(32, 48, 5):
            a.px(x + (y % 4), y + 1, mul(STONE_D, 1.25))
    for x in range(32, 48, 4):
        for y in range(44, 50):
            a.px(x + (y // 2) % 2, y, WOOD_D)
    a.rect(32, 40, 16, 2, GOBLIN_D)
    for x in range(32, 48):
        a.px(x, 40, GOBLIN if x % 3 else GOBLIN_L)
        if x % 2:
            a.px(x, 42, GOBLIN_D)
    a.noise(32, 40, 16, 12, 0.08)
    rock = a.region(32, 40, 16, 12)
    a.rect(48, 40, 8, 8, GOBLIN_D)
    for k in range(10):
        a.px(48 + (k * 3) % 8, 40 + (k * 5) % 8, GOBLIN if k % 2 else GOBLIN_L)
    grass = a.region(48, 40, 8, 8)
    a.rect(56, 40, 8, 8, DUSK_D)
    a.noise(56, 40, 8, 8, 0.15)
    dark = a.region(56, 40, 8, 8)
    # Башенка: мелкая кладка и окно.
    masonry(a, 48, 48, 16, 16, STONE, 4, 3)
    window(a, 54, 53, CRYSTAL, 6)
    a.shade(48, 48, 16, 16, 1.05, 0.82, 0.75)
    turret = a.region(48, 48, 16, 16)
    # Знамя: фиолетовое с золотой руной, низ клином.
    a.rect(32, 52, 8, 12, VIOLET)
    a.rect(32, 52, 8, 1, GOLD), a.rect(32, 53, 8, 1, GOLD_D)
    a.rect(32, 52, 1, 12, PLUM), a.rect(39, 52, 1, 12, PLUM)
    rune(a, 35, 55, 4, GOLD)
    for j in range(4):
        for i in range(8):
            if abs(i - 3.5) > 3.6 - j * 1.1:
                a.clear(32 + i, 60 + j)
    banner = a.region(32, 52, 8, 12)

    tris = (loft([(0.0, 1.1, 1.1), (0.4, 1.5, 1.5), (0.7, 1.32, 1.32)], rock, 8, caps=(dark, grass), flat=True)
            + loft([(0.6, 1.0, 1.0), (1.6, 0.84, 0.84), (3.6, 0.76, 0.76, 0.05, 0.0), (5.6, 0.72, 0.72, 0.1, 0.0)], hull, 8)
            + loft([(5.5, 0.72, 0.72, 0.1, 0.0), (5.95, 1.1, 1.1, 0.1, 0.0), (6.9, 1.12, 1.12, 0.12, 0.0)], room, 8)
            + loft([(6.8, 1.38, 1.38, 0.12, 0.0), (7.5, 0.86, 0.86, 0.12, 0.0), (8.2, 0.46, 0.46, 0.16, 0.0),
                    (8.7, 0.2, 0.2, 0.28, 0.0), (9.0, 0.03, 0.03, 0.46, 0.0)], roof, 8, caps=(dark, None))
            # Башенка на консоли: низ сходит в стену, сверху свой колпак.
            + loft([(3.2, 0.0, 0.0, -0.6, -0.1), (3.8, 0.36, 0.36, -0.86, -0.1), (4.9, 0.36, 0.36, -0.86, -0.1)], turret, 6)
            + loft([(4.8, 0.52, 0.52, -0.86, -0.1), (5.3, 0.24, 0.24, -0.86, -0.1), (5.75, 0.0, 0.0, -0.9, -0.1)], roof, 6,
                   caps=(dark, None))
            + quad((-0.2, 5.8, -0.9), (0.4, 5.8, -0.9), (0.4, 4.45, -0.9), (-0.2, 4.45, -0.9), banner))
    return Model("lighthouse", a).part("body", (0.0, 0.0, 0.0), tris)


def paint_wheel(a, x0, y0, rival):
    """Колесо 16×16. Гномье: кованое, с ребордой, четырьмя спицами и золотой ступицей.
    Гоблинское: дощатый диск с тёмным ободом, крестовиной и красными шляпками гвоздей. Вокруг
    прозрачно."""
    for i in range(16):
        for j in range(16):
            dx, dy = i - 7.5, j - 7.5
            d = math.hypot(dx, dy)
            if d > 7.6:
                a.clear(x0 + i, y0 + j)
                continue
            if rival:
                c = WOOD_D if i % 4 else BLACK
                if d > 6.2:
                    c = IRON_D if int((math.atan2(dy, dx) + math.pi) * 8 / math.pi) % 2 else BLACK
                elif abs(abs(dx) - abs(dy)) < 1.0:
                    c = WOOD
                if d < 1.6:
                    c = RED
                elif 4.2 < d < 5.2 and (i + j) % 4 == 0:
                    c = RED_D
            else:
                c = DUSK_D
                if d > 6.3:
                    c = IRON_L if dx + dy < -4.0 else IRON
                elif d > 5.2:
                    c = IRON_D
                elif abs(dx) < 1.0 or abs(dy) < 1.0:
                    c = IRON
                if d < 2.4:
                    c = GOLD_D
                if d < 1.5:
                    c = GOLD
            a.px(x0 + i, y0 + j, c)
    return a.region(x0, y0, 16, 16)


def make_cart(name, rival):
    """Транспорт гонок. Герой: гномья вагонетка, дощатый кузов в железных полосах с золотой
    рунной табличкой, в кузове друза кристаллов, на мачте рунный змей-ромб там, где у повозки
    парус. Соперник: гоблинская вагонетка, тёмный борт с красными зубами, спереди рог-таран, в
    кузове котёл со слизью, на кривой мачте рваная шкура с красным глазом. Части и точки
    вращения как у пиратской повозки: `body`, `axle_f`, `axle_r`."""
    a = Atlas(64, 64, 427 if not rival else 429)
    # Борт: доски вдоль, окантовка сверху и снизу.
    plank = DUSK if rival else WOOD
    for y in range(12):
        tone = (1.0, 1.12, 0.9, 1.05)[(y // 3) % 4]
        for x in range(64):
            c = mul(plank, tone * (1.0 + 0.06 * math.sin(x * 0.9 + y)))
            if y % 3 == 0:
                c = mul(plank, 0.58)
            a.px(x, y, c)
    if rival:
        # Заплаты, красные зубы по верху, шипы.
        for x in (9, 30, 51):
            a.rect(x, 5, 5, 4, HIDE_D)
            a.px(x, 5, BLACK), a.px(x + 4, 5, BLACK), a.px(x, 8, BLACK), a.px(x + 4, 8, BLACK)
        for x in range(64):
            if (x % 6) < 3 - abs((x % 6) - 1) + 1:
                a.px(x, 1, RED), a.px(x, 2, RED if x % 6 == 1 else RED_D)
        a.rect(0, 0, 64, 1, BLACK)
        for x in range(3, 64, 8):
            a.px(x, 10, BONE), a.px(x, 9, STONE)
    else:
        # Железные полосы с заклёпками, золотая табличка с рунами, бирюзовые огни.
        a.rect(0, 0, 64, 2, IRON), a.rect(0, 0, 64, 1, IRON_L)
        for x in range(0, 64, 16):
            a.rect(x, 2, 3, 10, IRON)
            a.rect(x, 2, 1, 10, IRON_D)
            a.px(x + 1, 4, IRON_L), a.px(x + 1, 9, IRON_L)
        a.rect(26, 4, 12, 7, GOLD_D)
        a.rect(27, 5, 10, 5, GOLD)
        rune(a, 28, 5, 0, DUSK_D), rune(a, 33, 5, 2, DUSK_D)
        for x in (10, 54):
            a.px(x, 6, CRYSTAL_L), a.px(x, 7, CRYSTAL)
    a.rect(0, 11, 64, 1, BLACK if rival else IRON_D)
    a.shade(0, 0, 64, 12, 1.08, 0.8, 1.0)
    a.noise(0, 0, 64, 12, 0.05)
    hull = a.region(0, 0, 64, 12)
    # Рама и днище: тёмные брусья с железными накладками.
    for y in range(16):
        for x in range(16):
            c = mul(WOOD_D if not rival else DUSK_D, 1.0 + 0.1 * math.sin(x * 1.3))
            if y % 4 == 0:
                c = BLACK
            a.px(x, 12 + y, c)
    a.rect(0, 12, 16, 1, IRON_D if not rival else BLACK)
    for x in (2, 13):
        a.px(x, 14, IRON_L if not rival else RED_D), a.px(x, 22, IRON_L if not rival else RED_D)
    a.noise(0, 12, 16, 16, 0.07)
    deck = a.region(0, 12, 16, 16)
    wheel = paint_wheel(a, 16, 12, rival)
    a.rect(32, 12, 8, 4, IRON_D if not rival else BLACK)
    for x in range(32, 40, 2):
        a.px(x, 13, IRON_L if not rival else WOOD_D)
    rim = a.region(32, 12, 8, 4)
    # Железо бруса-отбойника (герой) или рог (соперник).
    if rival:
        a.rect(32, 16, 8, 12, BONE)
        for y in range(16, 28, 3):
            a.rect(32, y, 8, 1, STONE)
        a.shade(32, 16, 8, 12, 1.1, 0.75, 0.8)
    else:
        a.rect(32, 16, 8, 12, IRON)
        a.rect(32, 16, 8, 1, IRON_L), a.rect(32, 27, 8, 1, IRON_D)
        for x in (33, 38):
            a.px(x, 19, GOLD), a.px(x, 24, GOLD)
        a.noise(32, 16, 8, 12, 0.08)
    iron = a.region(32, 16, 8, 12)
    # Мачта.
    bark(a, 40, 12, 8, 16, WOOD if not rival else WOOD_D, WOOD_D if not rival else BLACK, WOOD_L if not rival else WOOD)
    if not rival:
        for y in (12, 20):
            a.rect(40, y, 8, 1, GOLD), a.rect(40, y + 1, 8, 1, GOLD_D)
    mast = a.region(40, 12, 8, 16)
    if rival:
        # Котёл: чёрное железо с ободьями и подтёками слизи от края.
        a.rect(48, 12, 16, 16, IRON_D)
        for y in (13, 20, 26):
            a.rect(48, y, 16, 1, IRON), a.rect(48, y + 1, 16, 1, BLACK)
        for x in range(48, 64, 3):
            for y in range(12, 12 + 2 + (x * 7) % 6):
                a.px(x, y, GOBLIN if y % 2 else GOBLIN_L)
        a.rect(48, 12, 16, 1, GOBLIN_L)
        a.shade(48, 12, 16, 16, 1.1, 0.75, 0.8)
        a.noise(48, 12, 16, 16, 0.07)
    else:
        facets(a, 48, 12, 16, 16)
    cargo = a.region(48, 12, 16, 16)
    if rival:
        # Парус: шкура с заплатами и швами, красный глаз; низ и края рваные.
        a.rect(0, 32, 32, 28, HIDE)
        for y in range(32, 60, 7):
            for x in range(0, 32, 2):
                a.px(x, y + (x // 6) % 2, HIDE_D)
        a.rect(3, 36, 7, 6, mul(HIDE, 0.82)), a.rect(22, 47, 7, 6, mul(HIDE, 1.12))
        for x in range(3, 10, 2):
            a.px(x, 36, BLACK), a.px(x, 41, BLACK)
        for x in range(22, 29, 2):
            a.px(x, 47, BLACK), a.px(x, 52, BLACK)
        for j in range(28):
            for i in range(32):
                dx, dy = i - 15.5, (j - 11.5) * 1.6
                d = math.hypot(dx, dy)
                if d < 7.5:
                    a.px(i, 32 + j, RED if d > 5.8 else BONE if d > 2.6 else BLACK)
                if abs(dx) < 1.0 and 4.5 < abs(j - 11.5) < 7.5:
                    a.px(i, 32 + j, RED_D)
        a.shade(0, 32, 32, 28, 1.05, 0.82, 0.9)
        a.noise(0, 32, 32, 28, 0.06)
        for i in range(32):
            cut = 3 + int(2.6 * abs(math.sin(i * 0.9)) + (i * 5) % 3)
            a.clear(i, 60 - cut, 1, cut)
            if i in (0, 1, 30, 31):
                for j in range(28):
                    if (j * 3 + i) % 5 == 0:
                        a.clear(i, 32 + j)
        for x, y in ((6, 50), (7, 50), (6, 51), (25, 38), (25, 39), (26, 39), (17, 55)):
            a.clear(x, y)
    else:
        # Змей-ромб: синее полотно в золотой раме, большая руна, от неё бирюзовые лучи, по
        # осям деревянные рейки. Вокруг ромба прозрачно.
        for j in range(28):
            for i in range(32):
                dx, dy = abs(i - 15.5) / 15.8, abs(j - 13.5) / 13.8
                d = dx + dy
                if d > 1.0:
                    continue
                c = ROBE if (i + j) % 2 or d < 0.5 else mul(ROBE, 0.9)
                if d > 0.86:
                    c = GOLD if d < 0.95 else GOLD_D
                elif d > 0.78:
                    c = ROBE_D
                elif (i in (15, 16) or j in (13, 14)) and d > 0.34:
                    c = WOOD_D
                elif abs(dx * 15.8 - dy * 13.8) < 0.8 and d > 0.36:
                    c = CRYSTAL
                elif d < 0.3:
                    c = ROBE_D
                a.px(i, 32 + j, c)
        for dx_, k in ((11, 0), (17, 3)):
            for j, row in enumerate(GLYPHS[k]):
                for i, bit in enumerate(row):
                    if bit == "1":
                        a.px(dx_ + i + 1, 43 + j, GOLD_L)
        a.px(15, 37, CRYSTAL_L), a.px(16, 37, CRYSTAL_L), a.px(15, 54, CRYSTAL_L), a.px(16, 54, CRYSTAL_L)
        a.noise(0, 32, 32, 28, 0.04)
    sail = a.region(0, 32, 32, 28)
    # Верх кузова: руда с осколками кристаллов или бурая куча с костями.
    a.rect(32, 32, 16, 16, IRON_D if not rival else DUSK_D)
    for k in range(40):
        x, y = 32 + (k * 7) % 16, 32 + (k * 11) % 16
        a.px(x, y, (IRON, STONE_D, IRON_L, CRYSTAL_D)[k % 4] if not rival else (WOOD_D, HIDE_D, BLACK, GOBLIN_D)[k % 4])
    if not rival:
        for x, y in ((35, 35), (44, 37), (38, 44), (45, 45)):
            a.px(x, y, CRYSTAL_L), a.px(x + 1, y, CRYSTAL)
    a.rect(32, 32, 16, 1, IRON if not rival else BLACK), a.rect(32, 47, 16, 1, IRON if not rival else BLACK)
    a.rect(32, 32, 1, 16, IRON if not rival else BLACK), a.rect(47, 32, 1, 16, IRON if not rival else BLACK)
    ore = a.region(32, 32, 16, 16)
    # Слизь в котле (соперник) или фонарь на отбойнике (герой).
    if rival:
        for j in range(8):
            for i in range(8):
                a.px(48 + i, 32 + j, GOBLIN_L if (i * 3 + j * 5) % 7 == 0 else GOBLIN if (i + j) % 3 else GOBLIN_D)
    else:
        a.rect(48, 32, 8, 8, GOLD_D)
        a.rect(49, 33, 6, 6, CRYSTAL)
        a.rect(50, 34, 3, 3, CRYSTAL_L)
        a.rect(51, 33, 1, 6, GOLD_D)
    glow = a.region(48, 32, 8, 8)

    m = Model(name, a)
    body = at(box((0.84, 0.12, 1.9), deck, deck, deck), 0.0, 0.42, -0.1)
    if rival:
        body += at(box((0.98, 0.44, 1.8), hull, ore, deck, (0.9, 0.96)), 0.0, 0.69, -0.1)
        # Рог-таран загнут кверху, по бокам рога поменьше.
        for x, k in ((0.0, 1.0), (-0.34, 0.6), (0.34, 0.6)):
            body += at(rot(loft([(0.0, 0.13 * k, 0.13 * k), (0.3 * k, 0.09 * k, 0.09 * k, 0.0, 0.05 * k),
                                 (0.55 * k, 0.0, 0.0, 0.0, 0.16 * k)], iron, 5), rx=-90.0), x, 0.62, -0.96)
        # Котёл со слизью в кормовой половине.
        body += at(loft([(0.86, 0.22, 0.22), (1.0, 0.36, 0.36), (1.25, 0.4, 0.4), (1.42, 0.32, 0.32), (1.48, 0.36, 0.36)],
                        cargo, 8, caps=(None, glow)), 0.0, 0.0, 0.38)
        body += (at(loft([(0.0, 0.05, 0.05), (1.0, 0.045, 0.045, 0.07, 0.0), (2.0, 0.035, 0.035, -0.03, 0.0)], mast, 4),
                    0.0, 0.76, -0.25)
                 + at(rot(box((1.5, 0.07, 0.07), mast, mast, mast), rz=5.0), 0.0, 2.62, -0.25))
    else:
        body += at(box((0.9, 0.5, 1.8), hull, ore, deck, (1.16, 1.06)), 0.0, 0.72, -0.1)
        # Отбойники спереди и сзади, на переднем фонарь.
        body += at(box((0.62, 0.14, 0.2), iron, iron, iron), 0.0, 0.52, -1.08)
        body += at(box((0.62, 0.14, 0.16), iron, iron, iron), 0.0, 0.52, 0.86)
        body += at(box((0.16, 0.18, 0.16), glow, glow, glow), 0.0, 0.68, -1.1)
        # Друза в кормовой половине: большой кристалл и три поменьше, наклонены в стороны.
        body += at(loft([(0.9, 0.17, 0.17), (1.15, 0.28, 0.28), (1.62, 0.22, 0.22), (1.98, 0.0, 0.0)], cargo, 6, flat=True),
                   0.0, 0.0, 0.36)
        for x, z, rx_, rz_, k in ((-0.2, 0.3, 0.0, 30.0, 1.0), (0.2, 0.4, 14.0, -30.0, 0.85), (0.0, 0.6, 34.0, 0.0, 0.7)):
            body += at(rot(loft([(-0.1, 0.1 * k, 0.1 * k), (0.4 * k, 0.13 * k, 0.13 * k), (0.72 * k, 0.0, 0.0)], cargo, 5,
                                flat=True), rx=rx_, rz=rz_), x, 0.95, z)
        body += (at(loft([(0.0, 0.05, 0.05), (2.0, 0.035, 0.035)], mast, 4), 0.0, 0.76, -0.25)
                 + at(box((1.44, 0.06, 0.06), mast, mast, mast), 0.0, 1.9, -0.3))
    body += quad((-0.72, 2.6, -0.28), (0.72, 2.6, -0.28), (0.62, 1.2, -0.38), (-0.62, 1.2, -0.38), sail)
    m.part("body", (0.0, 0.0, 0.0), body)
    for part, z in (("axle_f", -0.72), ("axle_r", 0.72)):
        tris = []
        for x in (-0.6, 0.6):
            tris += at(rot(loft([(-0.07 if not rival else -0.05, 0.32, 0.32), (0.07 if not rival else 0.05, 0.32, 0.32)], rim, 8,
                                caps=(wheel, wheel), flat=True), rz=90.0), x, 0.32, z)
        m.part(part, (0.0, 0.32, z), tris, "body")
    return m


def fantasy_cart():
    return make_cart("cart", False)


def fantasy_cart_rival():
    return make_cart("cart_rival", True)


def fantasy_pistol():
    """Волшебная палочка в руке мага: оружие вида от первого лица. Узловатая палочка с золотой
    проволокой и обоймой, на конце кристалл, смотрит в −Z и чуть вверх; кулак с большим пальцем
    поверх, широкий синий рукав мантии с золотой каймой. Ноль в кулаке."""
    a = Atlas(32, 32, 431)
    # Палочка: волокно, узлы, золотая проволока наискось (верх куска это конец с кристаллом).
    bark(a, 0, 0, 16, 8)
    for x in range(16):
        a.px(x, (x // 2) % 8, GOLD)
    a.px(5, 5, WOOD_D), a.px(11, 2, WOOD_D)
    a.noise(0, 0, 16, 8, 0.06)
    wood = a.region(0, 0, 16, 8)
    facets(a, 16, 0, 8, 8, 4)
    gem = a.region(16, 0, 8, 8)
    gold_band(a, 24, 0, 8, 4)
    a.rect(24, 4, 8, 4, GOLD_D)
    a.rect(25, 5, 6, 2, GOLD)
    band = a.region(24, 0, 8, 4)
    knob = a.region(24, 4, 8, 4)
    # Кулак: пальцы с суставами и ногтями, тень между ними.
    a.rect(0, 8, 16, 8, SKIN)
    for x in (3, 7, 11, 15):
        a.rect(x, 8, 1, 6, SKIN_D)
    a.rect(0, 11, 16, 1, SKIN_D)
    for x in (1, 5, 9, 13):
        a.px(x, 9, BONE)
    a.rect(0, 14, 16, 2, SKIN_D)
    a.shade(0, 8, 16, 8, 1.06, 0.86, 0.85)
    a.noise(0, 8, 16, 8, 0.04)
    hand = a.region(0, 8, 16, 8)
    # Рукав: синяя ткань со складками, у запястья золотая кайма со звёздами.
    a.rect(16, 8, 16, 16, ROBE)
    for x in (18, 22, 27):
        a.rect(x, 8, 1, 12, ROBE_D)
        a.rect(x + 1, 9, 1, 10, ROBE_L)
    a.rect(16, 20, 16, 4, GOLD)
    a.rect(16, 20, 16, 1, GOLD_L), a.rect(16, 23, 16, 1, GOLD_D)
    for x in range(18, 32, 4):
        a.px(x, 22, GOLD_D)
    a.shade(16, 8, 16, 16, 0.85, 1.05, 0.78)
    a.noise(16, 8, 16, 16, 0.05)
    sleeve = a.region(16, 8, 16, 16)
    a.rect(0, 16, 8, 8, ROBE_D)
    a.rect(2, 18, 4, 4, DUSK_D)
    inner = a.region(0, 16, 8, 8)

    lay = lambda tris: at(rot(tris, rx=-75.0), 0.0, -0.03, 0.03)
    tris = (lay(loft([(-0.1, 0.022, 0.022), (-0.07, 0.028, 0.028), (0.05, 0.022, 0.022), (0.2, 0.017, 0.017),
                      (0.3, 0.014, 0.014)], wood, 6, caps=(knob, None)))
            + lay(loft([(0.27, 0.024, 0.024), (0.31, 0.026, 0.026)], band, 6, caps=(knob, knob)))
            + lay(loft([(0.3, 0.0, 0.0), (0.345, 0.042, 0.042), (0.44, 0.0, 0.0)], gem, 4, flat=True))
            # Кулак обхватывает палочку, большой палец лежит сверху вдоль неё.
            + at(box((0.085, 0.1, 0.1), hand, hand, hand), 0.0, -0.04, 0.03)
            + at(rot(box((0.032, 0.03, 0.1), hand, hand, hand), rx=15.0), 0.012, 0.012, 0.0)
            + at(rot(loft([(-0.02, 0.056, 0.056), (0.05, 0.064, 0.064), (0.5, 0.072, 0.072)], sleeve, 6,
                          caps=(inner, None)), rx=65.0), 0.0, -0.08, 0.07))
    return Model("pistol", a).part("body", (0.0, 0.0, 0.0), tris)


def fantasy_hoop():
    """Рунное кольцо: цель спорта. Щит это каменная плита с вырезанной светящейся рамкой
    прицела и рунами, кольцо золотое с рунной насечкой, вместо сетки свисают лианы с листьями и
    цветками, стойка из перекрученного ствола во мху. Кольцо и щит там же и тех же размеров, что
    у пиратов."""
    a = Atlas(64, 64, 433)
    # Плита: крупные камни, трещина, рамка из бирюзы, руны по углам, мох понизу.
    masonry(a, 0, 0, 32, 24, STONE, 16, 8)
    for x, y, w, h in ((10, 9, 12, 1), (10, 18, 12, 1), (10, 9, 1, 10), (21, 9, 1, 10)):
        a.rect(x, y, w, h, CRYSTAL_L)
    for x, y, w, h in ((9, 8, 14, 1), (9, 19, 14, 1), (9, 8, 1, 12), (22, 8, 1, 12)):
        a.rect(x, y, w, h, CRYSTAL_D)
    for k, (x, y) in enumerate(((3, 2), (26, 2), (3, 12), (26, 12), (14, 2))):
        rune(a, x, y, k, CRYSTAL)
    rune(a, 14, 11, 5, GOLD), rune(a, 17, 11, 0, GOLD)
    for i in range(7):
        a.px(24 + i // 2, 17 + i, mul(STONE, 0.5))
    for x in range(1, 31):
        for y in range(20, 23):
            if (x * 7 + y * 3) % 5 < 23 - y + 1:
                a.px(x, y, GOBLIN_D if (x + y) % 3 else GOBLIN)
    a.rect(0, 0, 32, 1, STONE_D), a.rect(0, 23, 32, 1, STONE_D), a.rect(0, 0, 1, 24, STONE_D), a.rect(31, 0, 1, 24, STONE_D)
    board = a.region(0, 0, 32, 24)
    gold_band(a, 32, 0, 16, 4)
    for x in range(34, 48, 4):
        a.px(x, 1, CRYSTAL_L)
    ring = a.region(32, 0, 16, 4)
    # Лианы: восемь волнистых плетей с листьями и сиреневыми цветками, между ними прозрачно.
    for k in range(8):
        length = 16 - (k * 5) % 4
        for y in range(length):
            x = 33 + k * 4 + int(round(0.9 * math.sin(y * 0.8 + k * 1.7)))
            a.px(x, 8 + y, GOBLIN_D)
            if y % 3 == 1:
                a.px(x + 1, 8 + y, GOBLIN), a.px(x + 2, 8 + y, GOBLIN_L)
            if y % 3 == 2:
                a.px(x - 1, 8 + y, GOBLIN)
        end = 33 + k * 4 + int(round(0.9 * math.sin((length - 1) * 0.8 + k * 1.7)))
        a.px(end, 8 + length - 1, LILAC if k % 2 else CRYSTAL_L)
        a.px(end + 1, 8 + length - 1, VIOLET if k % 2 else CRYSTAL)
    a.rect(32, 8, 32, 1, GOBLIN_D)
    net = a.region(32, 8, 32, 16)
    # Стойка: кора, мох пятнами, вьюнок наискось, у кольца светящаяся руна.
    bark(a, 0, 24, 8, 32)
    for y in range(24, 56):
        a.px((y // 3) % 8, y, GOBLIN_D)
        if y % 5 == 0:
            a.px(((y // 3) + 1) % 8, y, GOBLIN_L)
    rune(a, 3, 30, 3, CRYSTAL)
    a.shade(0, 24, 8, 32, 1.0, 0.9, 0.62)
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
    edge = (u0, v0, u0 + (u1 - u0) / 16.0, v1)
    for x in (-0.65, 0.65):
        faces += quad((x, 3.875, -0.15), (x, 3.875, -0.09), (x, 2.925, -0.09), (x, 2.925, -0.15), edge)
    for y in (2.925, 3.875):
        faces += quad((0.65, y, -0.15), (-0.65, y, -0.15), (-0.65, y, -0.09), (0.65, y, -0.09), edge)
    return Model("hoop", a).part("body", (0.0, 0.0, 0.0),
                                 loft([(0.0, 0.11, 0.11), (1.3, 0.09, 0.09, 0.03, 0.0), (2.6, 0.085, 0.085, -0.02, 0.0),
                                       (3.9, 0.07, 0.07)], post, 5)
                                 + loft([(0.0, 0.3, 0.3), (0.12, 0.2, 0.2)], post, 5, flat=True)
                                 + at(box((0.06, 0.06, 0.2), ring, ring, ring), 0.0, rim_y, -0.2)
                                 + faces + ring_tris + basket + flip(basket))


MODELS = [fantasy_cannon, fantasy_palm, fantasy_flag, fantasy_lighthouse, fantasy_cart, fantasy_cart_rival, fantasy_pistol,
          fantasy_hoop]


if __name__ == "__main__":
    models = [f() for f in MODELS]
    for m in models:
        print("%-11s частей %d, треугольников %3d%s" % (m.name, len(m.parts), m.tris(),
                                                        "  БОЛЬШЕ %d" % lm.MAX_TRIS if m.tris() > lm.MAX_TRIS else ""))
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
