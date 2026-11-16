#!/usr/bin/env python3
"""Персонажи «Фэнтези» для low poly и «продвинутых» (#137): юный маг, гоблин с дубинкой, тёмный
чародей в рогатой короне. Зеркала `pirate_hero`, `pirate_enemy`, `pirate_captain` из
`lowpoly_meshes.py` и космических из `space_mesh_chars.py`: те же имена частей, родители и точки
вращения (демки анимируют части), взгляд в −Z, ноль в подошвах, рост не выше 1,93 м; у гоблина
оружие в правой руке на месте сабли скелета (дубинка с шипами вдоль −Z). Цвета и облик из основы
16/32 (`fantasy16.PALETTE`): синяя мантия с золотой каймой, остроконечная шляпа с загнутым назад
кончиком и посох с бирюзовым кристаллом у мага, зелёная кожа, уши шире плеч и бурая рубаха у
гоблина. Плотный набор «продвинутых» получается из этих же функций (плотность и размер атласа
задаёт `lowpoly_meshes`), поэтому геометрия собирается его помощниками.

    python3 tools/fantasy_mesh_chars.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import fantasy16 as f16  # noqa: E402

rgb, mul = lm.rgb, lm.mul


def _pal(i):
    return tuple(f16.PALETTE[i])


# Цвета из палитры основы 16/32, светлые и тёмные тона к ним.
BLACK = _pal(f16.K)
ROBE, ROBE_D, ROBE_L = _pal(f16.SEA), _pal(f16.NAVY), rgb("6C8CEA")
GOLD, GOLD_D, GOLD_L = _pal(f16.GOLD), _pal(f16.BRASS), rgb("FFF0A8")
CRYSTAL, CRYSTAL_D, CRYSTAL_L = _pal(f16.AQUA), rgb("1E8A92"), _pal(f16.SKY)
BONE, STONE, STONE_D = _pal(f16.WHITE), _pal(f16.GREY), rgb("7C7498")
SKIN, SKIN_D = _pal(f16.SKIN), rgb("C48E68")
WOOD, WOOD_D, WOOD_L = _pal(f16.METAL), _pal(f16.DARK), rgb("BE8A54")
GOBLIN, GOBLIN_D, GOBLIN_L = _pal(f16.TAN), rgb("3C7436"), rgb("A2DA6A")
RED, RED_D = _pal(f16.RED), rgb("8E2440")
VIOLET, PLUM = _pal(f16.VIOLET), _pal(f16.PLUM)
DUSK, DUSK_D, DUSK_L = rgb("34225A"), rgb("1E1436"), rgb("4E3482")
PALE, PALE_D = rgb("CCC4E0"), rgb("8C84AE")


def _dots(a, points, c):
    for x, y in points:
        a.px(x, y, c)


def _folds(a, x, y, w, h, cols, dark, light):
    """Складки ткани: тёмная полоса и светлая рядом, чуть разной длины."""
    for i, cx in enumerate(cols):
        a.rect(x + cx, y + (i % 2), 1, h - (i % 2), dark)
        a.rect(x + cx + 1, y + 1 + (i % 2), 1, h - 2 - (i % 2), light)


def _star(a, x, y, c, core):
    """Звезда в пять пикселей: вышивка на шляпе и подоле."""
    _dots(a, ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)), c)
    a.px(x, y, core)


def _thighs(parts, k, chip):
    """Бёдра под подолом: ящик без крышек вместо бедра `biped`, точка вращения прежняя."""
    for side, x in (("l", -0.1 * k), ("r", 0.1 * k)):
        parts["leg_" + side][1] = lm.loft([(0.44, 0.072 * k, 0.078 * k, x, 0.0), (0.88, 0.09 * k, 0.095 * k, x, 0.0)],
                                          chip, 4, math.pi / 4.0)


def _cuff(parts, k, region, inner):
    """Раструб рукава у запястья: верх уходит внутрь предплечья, низ закрыт тёмной крышкой."""
    for side, x in (("l", -0.25 * k), ("r", 0.25 * k)):
        cx = x * 1.07
        parts["fore_" + side][1].extend(
            lm.loft([(0.9, 0.088, 0.094, cx, 0.0), (1.04, 0.034 * k, 0.038 * k, x * 1.06, 0.0)],
                    region, 4, math.pi / 4.0, caps=(inner, None)))


# --- Маг ---------------------------------------------------------------------------------------

def fantasy_hero():
    """Юный маг: синяя мантия колоколом с золотой каймой и звёздами по подолу, остроконечная
    шляпа с широкими полями и загнутым назад кончиком, каштановые волосы, раструбы рукавов,
    за спиной наискось посох с бирюзовым кристаллом над плечом."""
    a = lm.Atlas(64, 64, 311)
    # Верх мантии 32×18, три полосы колец по 6 строк: плечи с воротом, грудь, живот с поясом.
    # Середина куска это грудь: золотой ворот углом, застёжка-кристалл, ремень посоха наискось.
    a.rect(0, 0, 32, 20, ROBE)
    a.rect(0, 0, 32, 1, ROBE_L)
    a.rect(13, 0, 6, 3, SKIN)  # шея
    a.rect(13, 2, 6, 1, SKIN_D)
    a.rect(0, 0, 5, 3, WOOD), a.rect(27, 0, 5, 3, WOOD)  # волосы на загривке
    a.rect(0, 3, 4, 1, WOOD_D), a.rect(28, 3, 4, 1, WOOD_D)
    for i in range(5):  # ворот углом: две золотые ленты сходятся к застёжке
        a.px(11 + i, 2 + i, GOLD), a.px(12 + i, 2 + i, GOLD_D)
        a.px(20 - i, 2 + i, GOLD), a.px(19 - i, 2 + i, GOLD_D)
    a.rect(14, 3, 4, 3, SKIN), a.rect(15, 6, 2, 1, SKIN_D)
    a.rect(15, 7, 2, 2, CRYSTAL), a.px(15, 7, CRYSTAL_L)  # застёжка
    a.rect(14, 9, 4, 1, GOLD_D)
    a.rect(15, 10, 2, 5, GOLD), a.rect(16, 10, 1, 5, GOLD_D)  # золотая планка
    for i in range(12):  # ремень посоха с правого плеча на левый бок
        a.px(22 - i, 3 + i, WOOD), a.px(23 - i, 3 + i, WOOD_D)
    a.px(19, 6, GOLD), a.px(18, 7, GOLD_D)  # пряжка ремня
    for i in range(10):  # и по спине: шов сзади, поэтому две половины
        a.px(31 - i, 12 - i, WOOD), a.px(i, 2 + i // 2, WOOD)
    _folds(a, 0, 6, 32, 8, (4, 8, 25), ROBE_D, ROBE_L)
    for x in (6, 26):
        a.rect(x, 0, 3, 2, GOLD), a.rect(x, 2, 3, 1, GOLD_D)  # кайма на плечах
    a.rect(0, 14, 32, 1, ROBE_D)
    a.rect(0, 15, 32, 5, WOOD_D)  # пояс
    a.rect(0, 15, 32, 1, WOOD)
    a.rect(14, 15, 4, 3, GOLD), a.rect(15, 16, 2, 1, GOLD_D)
    a.rect(22, 15, 3, 3, RED), a.px(23, 15, BONE), a.px(22, 16, GOLD_L)  # склянка на поясе
    a.rect(7, 15, 3, 3, WOOD_L), a.px(8, 16, WOOD_D)  # кошель
    a.shade(0, 0, 32, 20, 1.08, 0.86, 0.76)
    a.noise(0, 0, 32, 20, 0.05)
    torso = a.region(0, 0, 32, 18)
    # Голова 32×15, три полосы по 5 строк: лоб с чёлкой под полями, глаза и нос, рот и шея.
    a.rect(0, 20, 32, 16, SKIN)
    a.rect(0, 20, 32, 4, WOOD)
    for x in (9, 11, 14, 17, 20, 22):
        a.px(x, 24, WOOD)  # чёлка прядями
    a.px(12, 24, WOOD_D), a.px(19, 24, WOOD_D)
    a.rect(0, 24, 8, 9, WOOD), a.rect(24, 24, 8, 9, WOOD)  # волосы до шеи
    for x in (2, 5, 26, 29):
        a.rect(x, 21, 1, 11, WOOD_D)
    a.rect(1, 33, 6, 1, WOOD_D), a.rect(25, 33, 6, 1, WOOD_D)
    a.rect(8, 26, 1, 3, SKIN_D), a.rect(23, 26, 1, 3, SKIN_D)  # уши
    a.rect(11, 25, 3, 1, WOOD_D), a.rect(18, 25, 3, 1, WOOD_D)  # брови
    a.rect(11, 26, 2, 2, BONE), a.rect(19, 26, 2, 2, BONE)  # большие глаза
    a.rect(12, 26, 1, 2, ROBE_D), a.rect(19, 26, 1, 2, ROBE_D)
    a.px(12, 26, BLACK), a.px(19, 26, BLACK)
    a.rect(15, 27, 2, 2, mul(SKIN, 0.92))
    a.px(15, 29, SKIN_D), a.px(16, 29, SKIN_D)
    a.px(10, 29, rgb("F0A894")), a.px(21, 29, rgb("F0A894"))  # румянец
    a.rect(14, 31, 4, 1, rgb("B05A56"))  # рот
    a.px(13, 30, rgb("B05A56")), a.px(18, 30, rgb("B05A56"))
    a.rect(0, 33, 32, 2, SKIN_D)
    a.rect(12, 33, 8, 1, mul(SKIN_D, 0.86))
    a.shade(0, 20, 32, 15, 1.0, 0.9, 0.84)
    a.noise(0, 20, 32, 15, 0.04)
    head = a.region(0, 20, 32, 15)
    # Рука 16×16: рукав с каймой на плече и складками, белый подрукавник в раструбе, кисть.
    a.rect(32, 0, 16, 10, ROBE)
    a.rect(32, 0, 16, 1, GOLD), a.rect(32, 1, 16, 1, GOLD_D)
    _folds(a, 32, 2, 16, 8, (3, 8, 12), ROBE_D, ROBE_L)
    a.rect(32, 10, 16, 3, STONE), a.rect(32, 10, 16, 1, BONE)
    a.rect(32, 13, 16, 3, SKIN)
    a.rect(32, 15, 16, 1, SKIN_D)
    for x in (35, 39, 43):
        a.px(x, 14, SKIN_D)
    a.shade(32, 0, 16, 16, 1.05, 0.92, 0.78)
    a.noise(32, 0, 16, 16, 0.05)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: тёмные рейтузы (бедро под подолом), башмак с отворотом и золотой пряжкой.
    a.rect(48, 0, 16, 15, ROBE_D)
    a.rect(55, 0, 1, 15, mul(ROBE_D, 0.75))
    for y in (11, 13):
        a.rect(48, y, 16, 1, mul(ROBE_D, 1.3))  # вязаные полосы на голени
    a.rect(48, 15, 16, 9, WOOD_D)
    a.rect(48, 15, 16, 2, WOOD), a.rect(48, 15, 16, 1, WOOD_L)  # отворот
    a.rect(54, 19, 4, 2, GOLD), a.px(55, 20, GOLD_D), a.px(56, 20, GOLD_D)
    a.rect(48, 23, 16, 1, BLACK)
    a.shade(48, 0, 16, 24, 1.05, 0.88, 0.78)
    a.noise(48, 0, 16, 24, 0.06)
    leg = a.region(48, 0, 16, 24)
    # Тулья шляпы 16×12, три полосы по 4 строки: кончик, середина со звёздами, золотая лента.
    a.rect(32, 16, 16, 12, ROBE)
    a.rect(32, 16, 16, 3, ROBE_L)
    for x in (34, 41, 45):
        a.rect(x, 17, 1, 7, ROBE_D)  # заломы
    _star(a, 38, 21, GOLD, GOLD_L)
    a.px(44, 19, GOLD), a.px(35, 18, GOLD)
    a.rect(36, 22, 3, 2, VIOLET), a.px(36, 22, PLUM), a.px(38, 23, PLUM)  # заплата
    a.rect(32, 24, 16, 3, GOLD)
    a.rect(32, 24, 16, 1, GOLD_L), a.rect(32, 26, 16, 1, GOLD_D)
    a.rect(39, 24, 3, 3, GOLD_D), a.px(40, 25, CRYSTAL)  # пряжка ленты
    a.rect(32, 27, 16, 1, ROBE_D)
    a.noise(32, 16, 16, 12, 0.05)
    cone = a.region(32, 16, 16, 12)
    # Поля 16×4: от тульи к краю, по краю светлый кант.
    a.rect(32, 28, 16, 4, ROBE)
    a.rect(32, 28, 16, 1, ROBE_D)
    a.rect(32, 31, 16, 1, ROBE_L)
    for x in (35, 43):
        a.px(x, 30, GOLD)
    a.noise(32, 28, 16, 4, 0.05)
    brim = a.region(32, 28, 16, 4)
    a.rect(32, 32, 4, 4, WOOD_D)
    a.rect(36, 32, 4, 4, mul(ROBE_D, 0.6))
    a.rect(40, 32, 4, 4, ROBE_D)
    sole, inner, tights = a.region(32, 32, 4, 4), a.region(36, 32, 4, 4), a.region(40, 32, 4, 4)
    # Посох 4×12 и кристалл 8×8: дерево с обмоткой и золотой оправой, бирюзовые грани с бликом.
    a.rect(48, 24, 4, 12, WOOD)
    a.rect(48, 24, 1, 12, WOOD_L), a.rect(51, 24, 1, 12, WOOD_D)
    a.rect(48, 24, 4, 2, GOLD), a.rect(48, 25, 4, 1, GOLD_D)
    a.rect(48, 30, 4, 1, WOOD_D), a.rect(48, 32, 4, 1, WOOD_D)
    staff = a.region(48, 24, 4, 12)
    a.rect(52, 24, 8, 8, CRYSTAL)
    for i in range(8):
        a.px(52 + i, 31 - i, CRYSTAL_L)
        a.px(52 + i, 24 + (i * 3) % 8, CRYSTAL_D)
    a.rect(52, 24, 8, 2, CRYSTAL_L), a.rect(54, 24, 3, 1, BONE)
    a.rect(52, 30, 8, 2, CRYSTAL_D)
    gem = a.region(52, 24, 8, 8)
    # Раструб рукава 16×4 с золотой каймой по краю.
    a.rect(48, 36, 16, 4, ROBE)
    a.rect(48, 36, 16, 1, ROBE_L)
    a.rect(48, 38, 16, 2, GOLD), a.rect(48, 39, 16, 1, GOLD_D)
    a.noise(48, 36, 16, 4, 0.05)
    cuff = a.region(48, 36, 16, 4)
    # Подол 32×20, две полосы по 10 строк: складки, золотая планка спереди, по низу звёзды,
    # бирюзовые руны и кайма в два тона.
    a.rect(0, 36, 32, 20, ROBE)
    _folds(a, 0, 36, 32, 16, (2, 6, 10, 20, 24, 28), ROBE_D, ROBE_L)
    a.rect(15, 36, 2, 15, GOLD), a.rect(16, 36, 1, 15, GOLD_D)
    for x in (4, 12, 22, 30):
        _star(a, x, 48, GOLD, GOLD_L)
    for x in (8, 18, 26):
        a.px(x, 49, CRYSTAL), a.px(x, 47, CRYSTAL), a.px(x + 1, 48, CRYSTAL_L)
    a.rect(0, 51, 32, 1, ROBE_D)
    a.rect(0, 52, 32, 3, GOLD)
    a.rect(0, 52, 32, 1, GOLD_L)
    for x in range(1, 32, 4):
        a.px(x, 53, GOLD_D), a.px(x + 1, 53, GOLD_D)
    a.rect(0, 55, 32, 1, GOLD_D)
    a.shade(0, 36, 32, 20, 1.0, 0.86, 0.8)
    a.noise(0, 36, 32, 20, 0.05)
    skirt = a.region(0, 36, 32, 20)

    parts = lm.biped(leg, torso, head, arm, sole, inner)
    _thighs(parts, 1.0, tights)
    # Мантия: верх до пояса и подол колоколом от того же кольца (стык общий, без щели), низ
    # закрыт тёмной крышкой, из неё выходят голени.
    waist = (1.02, 0.158, 0.102)
    parts["body"][1] = (lm.loft([waist, (1.27, 0.2, 0.125), (1.42, 0.17, 0.105), (1.47, 0.06, 0.06)], torso, 6)
                        + lm.loft([(0.36, 0.27, 0.28), (0.68, 0.215, 0.2), waist], skirt, 6, caps=(inner, None)))
    # Посох за спиной наискось: пята у правого бедра, кристалл над левым плечом ниже полей шляпы.
    rod = lm.loft([(0.0, 0.017, 0.017), (0.8, 0.017, 0.017)], staff, 3, caps=(sole, None), flat=True)
    rod += lm.loft([(0.78, 0.014, 0.014), (0.86, 0.05, 0.05), (0.97, 0.004, 0.004)], gem, 3, flat=True)
    parts["body"][1].extend(lm.at(lm.rot(rod, 0.0, 0.0, 40.0), 0.22, 0.92, 0.135))
    # Голова без макушки: её закрывает шляпа. Поля провисают к краю и уходят внутрь головы,
    # изнанка видна снизу; тулья в три кольца клонится назад, кончик загнут.
    parts["head"][1] = lm.loft([(1.44, 0.055, 0.06), (1.52, 0.09, 0.1, 0.0, -0.005), (1.64, 0.105, 0.115),
                                (1.74, 0.07, 0.08)], head, 6)
    flap = lm.loft([(1.665, 0.27, 0.28), (1.71, 0.08, 0.09)], brim, 6)
    parts["head"][1].extend(flap + lm.flip(flap))
    parts["head"][1].extend(lm.loft([(1.7, 0.125, 0.135), (1.79, 0.085, 0.09, 0.0, 0.02),
                                     (1.88, 0.045, 0.045, 0.0, 0.07), (1.925, 0.005, 0.005, 0.0, 0.16)],
                                    cone, 4, math.pi / 4.0))
    _cuff(parts, 1.0, cuff, inner)
    return lm.assemble("hero", a, parts)


# --- Гоблин ------------------------------------------------------------------------------------

def fantasy_enemy():
    """Гоблин: зелёный, сутулый, большая голова с длинным носом и ушами шире плеч, жёлтые
    глаза, клыки снизу, бурая рубаха с рваным подолом, в правой руке дубинка с шипами."""
    a = lm.Atlas(64, 64, 323)
    # Рубаха 32×18, три полосы по 6 строк: плечи и шея, грудь со шнуровкой, живот с ремнём.
    a.rect(0, 0, 32, 20, WOOD)
    a.rect(0, 0, 32, 2, GOBLIN_D)  # шея
    a.rect(11, 0, 10, 4, GOBLIN), a.rect(13, 4, 6, 2, GOBLIN)  # вырез до груди
    a.rect(11, 3, 2, 1, GOBLIN_D), a.rect(19, 3, 2, 1, GOBLIN_D)
    for y in (6, 8, 10):  # шнуровка крест-накрест
        a.px(14, y, BONE), a.px(17, y, BONE), a.px(15, y + 1, STONE), a.px(16, y + 1, STONE)
    a.rect(15, 6, 2, 6, WOOD_D)
    for x in (3, 8, 23, 28):
        a.rect(x, 3, 1, 10, WOOD_D)  # складки
        a.px(x + 1, 5, WOOD_L)
    a.rect(24, 7, 4, 4, WOOD_L), a.rect(24, 10, 4, 1, WOOD_D)  # заплата
    _dots(a, ((24, 7), (27, 7), (24, 9), (27, 9)), BONE)
    a.rect(0, 2, 6, 2, WOOD_D), a.rect(26, 2, 6, 2, WOOD_D)  # горб в тени
    a.rect(0, 13, 32, 3, WOOD_D)  # ремень
    a.rect(0, 13, 32, 1, BLACK)
    a.rect(14, 13, 4, 3, STONE), a.rect(15, 14, 2, 1, STONE_D)
    a.rect(5, 14, 2, 2, BONE), a.rect(9, 14, 1, 2, BONE)  # зубы-трофеи на ремне
    a.rect(0, 16, 32, 4, WOOD)
    a.shade(0, 0, 32, 20, 1.08, 0.84, 0.74)
    a.noise(0, 0, 32, 20, 0.07)
    shirt = a.region(0, 0, 32, 18)
    # Голова 32×16, четыре полосы по 4 строки: темя с бородавками, брови и глаза, пасть, челюсть.
    a.rect(0, 20, 32, 16, GOBLIN)
    a.rect(0, 20, 32, 2, GOBLIN_L)
    _dots(a, ((5, 22), (12, 21), (20, 22), (27, 21), (3, 26), (29, 27), (8, 23)), GOBLIN_D)
    for x in (14, 16, 18):
        a.rect(x, 20, 1, 2 + (x % 4) // 2, WOOD_D)  # клок волос
    a.rect(8, 24, 6, 1, GOBLIN_D), a.rect(18, 24, 6, 1, GOBLIN_D)  # надбровья
    a.px(13, 25, GOBLIN_D), a.px(18, 25, GOBLIN_D)
    a.rect(9, 25, 4, 2, GOLD), a.rect(19, 25, 4, 2, GOLD)  # жёлтые глаза
    a.rect(11, 25, 1, 2, BLACK), a.rect(20, 25, 1, 2, BLACK)
    a.px(9, 25, GOLD_L), a.px(22, 25, GOLD_L)
    a.rect(9, 27, 4, 1, GOBLIN_D), a.rect(19, 27, 4, 1, GOBLIN_D)
    a.rect(14, 26, 4, 3, GOBLIN_D)  # тень под носом
    a.rect(8, 30, 16, 2, BLACK)  # пасть до ушей
    a.rect(11, 31, 10, 1, RED_D)
    for x in (9, 13, 18, 22):
        a.px(x, 30, BONE)  # клыки снизу вверх
    a.px(9, 29, BONE), a.px(22, 29, BONE)
    a.rect(0, 28, 4, 6, GOBLIN_D), a.rect(28, 28, 4, 6, GOBLIN_D)  # затылок в тени
    a.rect(0, 33, 32, 3, GOBLIN_D)
    a.rect(10, 33, 12, 1, GOBLIN)  # подбородок
    a.shade(0, 20, 32, 16, 1.08, 0.86, 0.8)
    a.noise(0, 20, 32, 16, 0.06)
    head = a.region(0, 20, 32, 16)
    # Конечность 16×16: кожа с жилами и пятнами, кожаная обмотка, когти на кисти и ступне.
    a.rect(32, 0, 16, 16, GOBLIN)
    a.rect(39, 0, 1, 9, GOBLIN_D)
    _dots(a, ((34, 2), (44, 4), (36, 6), (42, 1)), GOBLIN_D)
    a.rect(32, 5, 16, 1, GOBLIN_D)  # сустав
    a.rect(32, 9, 16, 3, WOOD)
    a.rect(32, 9, 16, 1, WOOD_L), a.rect(32, 11, 16, 1, WOOD_D)
    for x in range(33, 48, 3):
        a.px(x, 10, WOOD_D)
    a.rect(32, 14, 16, 2, GOBLIN_D)
    for x in (34, 38, 42, 46):
        a.px(x, 15, BONE), a.px(x, 14, GOBLIN)
    a.shade(32, 0, 16, 16, 1.04, 0.9, 0.72)
    a.noise(32, 0, 16, 16, 0.06)
    limb = a.region(32, 0, 16, 16)
    # Дубинка 16×12, четыре полосы по 3 строки от конца к рукояти: торец, толстый конец с
    # железным обручем и сучками, шейка, рукоять в обмотке.
    a.rect(32, 16, 16, 12, WOOD)
    a.rect(32, 16, 16, 3, WOOD_L)
    for x in (34, 39, 44):
        a.rect(x, 16, 1, 9, WOOD_D)  # волокна
    a.rect(32, 20, 16, 2, STONE_D), a.rect(32, 20, 16, 1, STONE)  # обруч
    for x in (33, 37, 41, 45):
        a.px(x, 20, BONE)  # заклёпки
    a.rect(36, 17, 2, 2, WOOD_D), a.px(42, 23, WOOD_D), a.px(43, 23, WOOD_D)  # сучки
    a.rect(32, 25, 16, 3, WOOD_D)
    for x in range(32, 48, 2):
        a.px(x + (x // 2) % 2, 26, WOOD_L)
    a.noise(32, 16, 16, 12, 0.07)
    club = a.region(32, 16, 16, 12)
    # Ухо 16×8: острый треугольник от головы (слева) к кончику, внутри сиреневая тень.
    a.rect(48, 0, 16, 8, GOBLIN)
    for x in range(16):
        up = x // 4  # верхний край поднимается к кончику полого
        low = 8 - (x + 1) // 2 if x > 2 else 8  # нижний срезан круче
        for y in range(8):
            if y < 3 - up or y >= low:
                a.clear(48 + x, y)
    for x in range(2, 12):
        a.px(48 + x, max(3 - x // 4, 0) + 2, PLUM if x < 9 else GOBLIN_D)
    a.rect(48, 3, 2, 4, GOBLIN_D)
    a.px(61, 1, GOBLIN_L), a.px(60, 1, GOBLIN_L)
    ear = a.region(48, 0, 16, 8)
    # Нос 8×4 (кончик темнее), обломок кости для шипов, тёмный и зелёный лоскуты.
    a.rect(48, 8, 8, 4, GOBLIN)
    a.rect(48, 8, 8, 1, GOBLIN_D), a.rect(51, 9, 2, 1, GOBLIN_L)
    nose = a.region(48, 8, 8, 4)
    a.rect(56, 8, 4, 4, GOBLIN_D)
    a.rect(60, 8, 4, 4, GOBLIN_L)
    a.rect(48, 12, 4, 4, BONE), a.rect(48, 14, 4, 2, STONE)
    a.rect(52, 12, 4, 4, mul(WOOD_D, 0.6))
    chip, crown, spike, dark = (a.region(56, 8, 4, 4), a.region(60, 8, 4, 4), a.region(48, 12, 4, 4),
                                a.region(52, 12, 4, 4))
    # Подол рубахи 32×8: зубцы прозрачными пикселями, по краю тёмная кромка, штопка.
    a.rect(0, 36, 32, 8, WOOD)
    for x in (3, 8, 15, 23, 28):
        a.rect(x, 36, 1, 6, WOOD_D)
    for x in range(32):
        cut = (0, 1, 2, 3, 2, 1, 0, 2, 3, 1)[(x * 3) % 10]
        for j in range(cut):
            a.clear(x, 43 - j)
        a.px(x, 43 - cut, WOOD_D)
    a.rect(19, 38, 3, 2, GOBLIN_D)  # дыра до кожи
    a.noise(0, 36, 32, 8, 0.07)
    hem = a.region(0, 36, 32, 8)
    # Повязка на бёдрах 16×4 под подолом.
    a.rect(32, 28, 16, 4, WOOD_D)
    a.rect(32, 28, 16, 1, BLACK)
    a.noise(32, 28, 16, 4, 0.08)
    hips = a.region(32, 28, 16, 4)

    m = lm.Model("enemy", a)
    for side, x in (("l", -0.09), ("r", 0.09)):
        m.part("leg_" + side, (x, 0.86, 0.0),
               lm.loft([(0.0, 0.07, 0.135, x, -0.05), (0.07, 0.042, 0.048, x, 0.0), (0.46, 0.056, 0.056, x, 0.0),
                        (0.88, 0.062, 0.062, x, 0.0)], limb, 4, math.pi / 4.0, caps=(chip, None)))
    # Тело: бёдра, рубаха с горбом (плечи уходят назад), рваный подол от пояса с изнанкой.
    belt = (0.98, 0.125, 0.09)
    skirt = lm.loft([(0.7, 0.2, 0.155), belt], hem, 6)
    m.part("body", (0.0, 0.86, 0.0),
           lm.loft([(0.84, 0.13, 0.09), belt], hips, 6)
           + lm.loft([belt, (1.12, 0.155, 0.115, 0.0, 0.01), (1.34, 0.185, 0.135, 0.0, 0.035), (1.46, 0.05, 0.05)],
                     shirt, 6)
           + skirt + lm.flip(skirt))
    # Голова крупная, с тяжёлой челюстью вперёд; нос конусом вперёд и вниз, уши в стороны.
    skull = lm.loft([(1.44, 0.05, 0.055), (1.5, 0.125, 0.13, 0.0, -0.025), (1.6, 0.155, 0.155, 0.0, -0.02),
                     (1.7, 0.135, 0.14), (1.76, 0.06, 0.07)], head, 6, caps=(None, crown))
    beak = lm.at(lm.rot(lm.loft([(0.0, 0.04, 0.034), (0.2, 0.004, 0.004)], nose, 3, flat=True), -112.0), 0.0, 1.615, -0.15)
    ears = (lm.quad((0.12, 1.7, 0.02), (0.43, 1.83, 0.09), (0.43, 1.61, 0.09), (0.12, 1.5, 0.02), ear)
            + lm.quad((-0.12, 1.7, 0.02), (-0.43, 1.83, 0.09), (-0.43, 1.61, 0.09), (-0.12, 1.5, 0.02), ear))
    m.part("head", (0.0, 1.46, 0.0), skull + beak + ears, "body")
    m.part("arm_l", (-0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.045, 0.045, -0.22, 0.0), (1.08, 0.042, 0.042, -0.215, 0.0), (1.4, 0.04, 0.04, -0.2, 0.0)],
                   limb, 4, math.pi / 4.0, caps=(chip, None)), "body")
    # Дубинка вдоль −Z на месте сабли скелета: рукоять проходит сквозь кисть, толстый конец
    # впереди, три костяных шипа.
    bat = lm.loft([(0.0, 0.022, 0.022), (0.34, 0.028, 0.028), (0.48, 0.066, 0.066), (0.7, 0.078, 0.078),
                   (0.76, 0.04, 0.04)], club, 4, math.pi / 4.0, caps=(dark, dark))
    for turn in (20.0, 140.0, 260.0):
        thorn = lm.at(lm.rot(lm.loft([(0.0, 0.022, 0.022), (0.075, 0.003, 0.003)], spike, 3, flat=True), 0.0, 0.0, -90.0),
                      0.04, 0.6, 0.0)
        bat += lm.rot(thorn, 0.0, turn, 0.0)
    m.part("arm_r", (0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.045, 0.045, 0.22, 0.0), (1.08, 0.042, 0.042, 0.215, 0.0), (1.4, 0.04, 0.04, 0.2, 0.0)],
                   limb, 4, math.pi / 4.0, caps=(chip, None))
           + lm.at(lm.rot(bat, -90.0), 0.22, 0.79, 0.04), "body")
    return m


# --- Тёмный чародей ----------------------------------------------------------------------------

def fantasy_captain():
    """Тёмный чародей: второй боец и главарь. Крупный, в чёрно-фиолетовой мантии до пят с
    золотой каймой и красным амулетом, бледное лицо с горящими глазами и седой бородой клином,
    золотая корона с загнутыми рогами, стоячий ворот, за спиной плащ до колен."""
    a = lm.Atlas(64, 64, 343)
    # Верх мантии 32×18, три полосы по 6 строк: плечи с оплечьями, грудь с амулетом, живот.
    a.rect(0, 0, 32, 20, DUSK)
    a.rect(13, 0, 6, 2, PALE_D)  # шея
    for i in range(6):  # борта мантии сходятся углом, по краю золото
        a.rect(12 + i // 2, i, 1, 1, GOLD), a.rect(19 - i // 2, i, 1, 1, GOLD)
        a.rect(13 + i // 2, i, 6 - 2 * (i // 2), 1, DUSK_D)
    a.rect(13, 0, 6, 2, PALE_D)
    for x in (6, 23):
        a.rect(x, 0, 4, 3, GOLD), a.rect(x, 2, 4, 1, GOLD_D)  # оплечья
        a.px(x + 1, 1, RED), a.px(x + 2, 1, RED_D)
    for i in range(4):  # цепь амулета
        a.px(13 + i // 2, 5 + i, GOLD_D), a.px(18 - i // 2, 5 + i, GOLD_D)
    a.rect(14, 8, 4, 4, GOLD), a.rect(15, 9, 2, 2, RED)
    a.px(15, 9, rgb("FF9AA0")), a.px(16, 10, RED_D)
    a.rect(14, 11, 4, 1, GOLD_D)
    _folds(a, 0, 4, 32, 10, (3, 9, 21, 27), DUSK_D, DUSK_L)
    for x, y in ((6, 8), (25, 9), (10, 12), (21, 6)):  # руны вышивкой
        a.px(x, y, VIOLET), a.px(x, y + 1, VIOLET), a.px(x + 1, y, PLUM)
    a.rect(0, 14, 32, 1, DUSK_D)
    a.rect(0, 15, 32, 5, BLACK)  # кушак
    a.rect(0, 15, 32, 1, GOLD_D)
    a.rect(13, 15, 6, 3, GOLD), a.rect(14, 16, 4, 1, GOLD_D)
    a.px(15, 16, VIOLET), a.px(16, 16, VIOLET)
    a.shade(0, 0, 32, 20, 1.1, 0.84, 0.72)
    a.noise(0, 0, 32, 20, 0.07)
    torso = a.region(0, 0, 32, 18)
    # Голова 32×24, три полосы по 8 строк: лоб под короной, глаза и нос, усы и шея. По бокам и
    # сзади длинные седые волосы.
    a.rect(0, 20, 32, 24, PALE)
    a.rect(0, 20, 32, 2, BONE)
    for x in (10, 14, 19):
        a.rect(x, 25, 3, 1, PALE_D)  # морщины лба
    a.rect(0, 20, 9, 22, STONE), a.rect(23, 20, 9, 22, STONE)
    for x in (1, 4, 7, 24, 27, 30):
        a.rect(x, 21, 1, 21, STONE_D)
        a.rect(x + 1, 22, 1, 18, BONE)
    a.rect(9, 28, 6, 1, STONE_D), a.rect(17, 28, 6, 1, STONE_D)  # брови вразлёт
    a.px(14, 29, STONE_D), a.px(17, 29, STONE_D), a.px(9, 27, STONE_D), a.px(22, 27, STONE_D)
    a.rect(10, 29, 4, 3, PLUM), a.rect(18, 29, 4, 3, PLUM)  # глазницы
    a.rect(11, 30, 2, 1, RED), a.rect(19, 30, 2, 1, RED)  # горящие глаза
    a.px(12, 30, rgb("FFC0A0")), a.px(19, 30, rgb("FFC0A0"))
    a.rect(15, 30, 2, 5, mul(PALE, 0.92))  # длинный нос
    a.px(15, 35, PALE_D), a.px(16, 35, PALE_D)
    a.rect(10, 33, 2, 2, PALE_D), a.rect(20, 33, 2, 2, PALE_D)  # впалые щёки
    a.rect(11, 36, 10, 2, BONE)  # усы
    a.rect(14, 36, 4, 1, STONE)
    a.rect(13, 38, 6, 1, BLACK)  # рот
    a.rect(10, 39, 12, 5, BONE)  # начало бороды
    for x in (11, 14, 17, 20):
        a.rect(x, 39, 1, 5, STONE)
    a.rect(0, 42, 32, 2, PALE_D)
    a.rect(10, 42, 12, 2, STONE)
    a.shade(0, 20, 32, 24, 1.06, 0.88, 0.82)
    a.noise(0, 20, 32, 24, 0.05)
    head = a.region(0, 20, 32, 24)
    # Рукав 16×16: складки, золотой обшлаг с рунами, бледная кисть с тёмными ногтями.
    a.rect(32, 0, 16, 16, DUSK)
    _folds(a, 32, 0, 16, 9, (3, 8, 12), DUSK_D, DUSK_L)
    a.rect(32, 9, 16, 3, GOLD)
    a.rect(32, 9, 16, 1, GOLD_L), a.rect(32, 11, 16, 1, GOLD_D)
    for x in (34, 38, 42, 46):
        a.px(x, 10, VIOLET)
    a.rect(32, 12, 16, 4, PALE)
    a.rect(32, 14, 16, 1, PALE_D)
    for x in (35, 39, 43):
        a.px(x, 15, PLUM)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.75)
    a.noise(32, 0, 16, 16, 0.07)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: тёмные штаны (под подолом), остроносый сапог с золотой пряжкой и отворотом.
    a.rect(48, 0, 16, 14, DUSK_D)
    a.rect(55, 0, 1, 14, BLACK)
    a.rect(48, 14, 16, 10, BLACK)
    a.rect(48, 14, 16, 2, PLUM), a.rect(48, 14, 16, 1, VIOLET)
    a.rect(54, 19, 4, 2, GOLD), a.px(55, 20, GOLD_D), a.px(56, 20, GOLD_D)
    a.rect(48, 22, 16, 1, DUSK)
    a.shade(48, 0, 16, 24, 1.05, 0.88, 0.78)
    a.noise(48, 0, 16, 24, 0.07)
    leg = a.region(48, 0, 16, 24)
    # Плащ 24×20: багрово-сиреневый с изнанки ночи, складки, золотая кайма, руна в середине.
    a.rect(0, 44, 24, 20, PLUM)
    for x in (3, 7, 12, 16, 20):
        a.rect(x, 46, 1, 16, DUSK)
        a.rect(x + 1, 47, 1, 14, VIOLET)
    for x, y in ((11, 52), (12, 51), (13, 52), (12, 53), (12, 55), (11, 56), (13, 56)):
        a.px(x, y, GOLD)
    a.rect(0, 44, 24, 2, GOLD), a.rect(0, 45, 24, 1, GOLD_D)
    a.rect(0, 61, 24, 1, GOLD_D)
    for x in range(24):
        a.px(x, 62, GOLD), a.px(x, 63, GOLD if x % 4 < 2 else DUSK)  # зубчатая кайма
    a.rect(0, 44, 1, 20, GOLD), a.rect(23, 44, 1, 20, GOLD)
    a.shade(0, 44, 24, 20, 1.05, 0.8, 0.85)
    a.noise(0, 44, 24, 20, 0.07)
    # Подол 40×20, две полосы по 10 строк: складки, руны столбцом спереди, кайма в два ряда.
    a.rect(24, 44, 40, 20, DUSK)
    _folds(a, 24, 44, 40, 16, (2, 7, 12, 26, 31, 36), DUSK_D, DUSK_L)
    a.rect(43, 44, 2, 16, DUSK_D)
    for y in (47, 51, 55):
        a.px(43, y, VIOLET), a.px(44, y, VIOLET), a.px(43 + (y // 4) % 2, y + 1, CRYSTAL)
    a.rect(24, 59, 40, 1, VIOLET)
    a.rect(24, 60, 40, 3, GOLD)
    a.rect(24, 60, 40, 1, GOLD_L)
    for x in range(25, 64, 4):
        a.px(x, 61, RED_D), a.px(x + 1, 61, GOLD_D)
    a.rect(24, 63, 40, 1, GOLD_D)
    a.shade(24, 44, 40, 20, 1.0, 0.86, 0.8)
    a.noise(24, 44, 40, 20, 0.06)
    skirt = a.region(24, 44, 40, 20)
    a.rect(32, 16, 4, 4, BLACK)
    a.rect(36, 16, 4, 4, BONE)
    a.rect(40, 16, 4, 4, DUSK_D)
    sole, crown, inner = a.region(32, 16, 4, 4), a.region(36, 16, 4, 4), a.region(40, 16, 4, 4)
    # Рог 4×8: тёмное основание, кольца роста, светлый кончик.
    a.rect(44, 16, 4, 8, STONE_D)
    a.rect(44, 16, 4, 3, BONE), a.rect(44, 19, 4, 2, STONE)
    a.rect(44, 21, 4, 1, PLUM), a.px(44, 18, STONE), a.px(46, 20, STONE_D)
    horn = a.region(44, 16, 4, 8)
    # Корона 12×6: зубцы прозрачными пикселями, обод с красными камнями.
    a.rect(32, 20, 12, 6, GOLD)
    for x in range(12):
        for j in range((2, 1, 0, 1)[x % 4] + (1 if x % 4 == 0 else 0)):
            a.clear(32 + x, 20 + j)
    a.rect(32, 23, 12, 1, GOLD_L)
    a.rect(32, 25, 12, 1, GOLD_D)
    for x in (34, 38, 42):
        a.px(x, 24, RED), a.px(x, 22, GOLD_L)
    band = a.region(32, 20, 12, 6)
    # Борода 12×10: седые пряди клином.
    a.rect(32, 26, 12, 10, BONE)
    for x in (33, 36, 39, 42):
        a.rect(x, 26, 1, 10, STONE)
    for x in (35, 41):
        a.rect(x, 29, 1, 7, STONE_D)
    a.rect(32, 34, 12, 2, STONE)
    a.noise(32, 26, 12, 10, 0.05)
    beard = a.region(32, 26, 12, 10)
    # Стоячий ворот 24×8, три полотнища: тёмный снаружи, золотой кант, зубец кверху у краёв.
    a.rect(32, 36, 24, 8, DUSK)
    a.rect(32, 36, 24, 1, GOLD), a.rect(32, 37, 24, 1, GOLD_D)
    for x in (35, 39, 43, 47, 51):
        a.rect(x, 38, 1, 6, DUSK_D), a.px(x + 1, 39, VIOLET)
    a.rect(32, 36, 1, 8, GOLD), a.rect(55, 36, 1, 8, GOLD)
    a.rect(43, 40, 2, 2, VIOLET)
    for j in range(3):  # передние углы срезаны
        a.clear(32, 41 + j, 3 - j + (0 if j else 0), 1)
        a.clear(53 + j, 41 + j, 3 - j, 1)
    a.clear(32, 41, 3, 1), a.clear(32, 42, 2, 1), a.clear(32, 43, 1, 1)
    a.noise(32, 36, 24, 8, 0.06)

    k = 1.18
    parts = lm.biped(leg, torso, head, arm, sole, crown, k)
    _thighs(parts, k, inner)
    # Мантия до пят: верх и подол от общего кольца на поясе, низ закрыт тёмной крышкой.
    waist = (1.02, 0.158 * k, 0.102 * k)
    parts["body"][1] = (lm.loft([waist, (1.27, 0.2 * k, 0.125 * k), (1.42, 0.17 * k, 0.105 * k), (1.47, 0.06, 0.06)],
                                torso, 6)
                        + lm.loft([(0.2, 0.3, 0.27), (0.62, 0.245, 0.215), waist], skirt, 6, caps=(inner, None)))
    # Голова: вытянутое лицо, корона расходится кверху от висков, рога от обода в стороны и вверх
    # до 1,93 м, борода клином от подбородка на грудь.
    parts["head"][1] = lm.loft([(1.44, 0.065, 0.07), (1.53, 0.108, 0.118, 0.0, -0.005), (1.66, 0.114, 0.124),
                                (1.77, 0.07, 0.08)], head, 6, caps=(None, crown))
    ring = lm.loft([(1.685, 0.098, 0.108), (1.8, 0.145, 0.155)], band, 6)
    parts["head"][1].extend(ring + lm.flip(ring))
    for s in (-1.0, 1.0):
        parts["head"][1].extend(lm.loft([(1.7, 0.042, 0.042, s * 0.1, 0.0), (1.79, 0.036, 0.036, s * 0.2, 0.0),
                                         (1.93, 0.004, 0.004, s * 0.225, -0.04)], horn, 3, flat=True))
    parts["head"][1].extend(lm.loft([(1.22, 0.006, 0.006, 0.0, -0.18), (1.5, 0.072, 0.05, 0.0, -0.08)],
                                    beard, 4, math.pi / 4.0))
    # Ворот: три полотнища дугой за головой, от плеч вверх и наружу.
    low = [(0.21 * math.sin(t), 0.035 + 0.15 * math.cos(t)) for t in (-1.35, -0.45, 0.45, 1.35)]
    top = [(0.29 * math.sin(t), 0.07 + 0.2 * math.cos(t)) for t in (-1.5, -0.5, 0.5, 1.5)]
    for i in range(3):
        parts["body"][1].extend(lm.quad((top[i + 1][0], 1.66, top[i + 1][1]), (top[i][0], 1.66, top[i][1]),
                                        (low[i][0], 1.38, low[i][1]), (low[i + 1][0], 1.38, low[i + 1][1]),
                                        a.region(32 + i * 8, 36, 8, 8)))
    # Плащ: три полотнища от плеч до колен, книзу шире и дальше от спины.
    cloak = []
    top = [(0.27, 0.19), (0.09, 0.2), (-0.09, 0.2), (-0.27, 0.19)]
    low = [(0.37, 0.32), (0.13, 0.36), (-0.13, 0.36), (-0.37, 0.32)]
    for i in range(3):
        cloak += lm.quad((top[i][0], 1.4, top[i][1]), (top[i + 1][0], 1.4, top[i + 1][1]),
                         (low[i + 1][0], 0.5, low[i + 1][1]), (low[i][0], 0.5, low[i][1]),
                         a.region(i * 8, 44, 8, 20))
    parts["body"][1].extend(cloak)
    return lm.assemble("captain", a, parts)


MODELS = [fantasy_hero, fantasy_enemy, fantasy_captain]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        models = [f() for f in MODELS]
        for m in models:
            print("%-8s частей %d, треугольников %d" % (m.name, len(m.parts), m.tris()))
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
