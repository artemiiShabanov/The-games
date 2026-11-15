#!/usr/bin/env python3
"""Персонажи «Космоса» для low poly и «продвинутых» (#136): космонавт, пришелец-пехотинец,
командир пришельцев. Зеркала `pirate_hero`, `pirate_enemy`, `pirate_captain` из
`lowpoly_meshes.py`: те же имена частей, родители и точки вращения (демки анимируют части),
рост, взгляд в −Z, ноль в подошвах; у пехотинца оружие в правой руке на месте сабли скелета.
Плотный набор «продвинутых» получается из этих же функций (плотность и размер атласа задаёт
`lowpoly_meshes`), поэтому геометрия собирается его помощниками.

    python3 tools/space_mesh_chars.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402

rgb, mul = lm.rgb, lm.mul

SUIT, SUIT_D, SUIT_L = rgb("DDE2EA"), rgb("A3ACBE"), rgb("F6F8FB")
METAL, METAL_D, METAL_L = rgb("7A8496"), rgb("444A5A"), rgb("AAB4C6")
CYAN, CYAN_D, CYAN_L = rgb("4FC3D9"), rgb("246E8C"), rgb("C8F2F6")
ORANGE, ORANGE_D = rgb("F06A3A"), rgb("A8401E")
VIOLET, VIOLET_D, VIOLET_L = rgb("9A5FE0"), rgb("57329A"), rgb("BE94F2")
BLACK = rgb("15131C")
BRAIN, BRAIN_D, BRAIN_L = rgb("E08AB4"), rgb("A04E7C"), rgb("F6BCD6")
CLOAK, CLOAK_D, CLOAK_L = rgb("6E1E40"), rgb("3C1026"), rgb("94345A")
GOLD, GOLD_D = rgb("E0B040"), rgb("9A7020")


def _rivets(a, x, y, w, c, step=4):
    for i in range(x + 1, x + w, step):
        a.px(i, y, c)


# --- Космонавт ---------------------------------------------------------------------------------

def space_hero():
    """Космонавт: белый скафандр со швами и шлангами, круглый шлем с бирюзовым визором, ранец,
    оранжевая нашивка на плече, металлические перчатки и ботинки."""
    a = lm.Atlas(64, 64, 111)
    # Торс 32×20: середина куска это грудь. Нагрудный пульт, лямки ранца, шланг к шлему, пояс.
    a.rect(0, 0, 32, 17, SUIT)
    for x in (9, 22):
        a.rect(x, 0, 2, 17, SUIT_D)  # лямки
        a.px(x, 5, METAL), a.px(x + 1, 5, METAL)
    a.rect(12, 5, 8, 7, METAL)
    a.rect(12, 5, 8, 1, METAL_L)
    a.rect(12, 11, 8, 1, METAL_D)
    a.px(13, 7, CYAN), a.px(14, 7, CYAN_L), a.px(16, 7, ORANGE), a.px(18, 7, CYAN)
    a.rect(13, 9, 6, 1, METAL_D)
    a.px(14, 9, CYAN), a.px(17, 9, ORANGE)
    for y in range(1, 5):
        a.px(20 + (y % 2), y, METAL_D)  # шланг от пульта к шлему
    a.rect(13, 0, 6, 2, METAL)  # кольцо ворота
    a.rect(13, 1, 6, 1, METAL_D)
    for y in (13, 15):
        a.rect(0, y, 32, 1, SUIT_D)  # складки на животе
    a.rect(3, 2, 4, 3, ORANGE), a.rect(3, 4, 4, 1, ORANGE_D)  # нашивка у левого плеча
    a.px(4, 3, SUIT_L)
    a.rect(26, 3, 3, 2, CYAN_D)
    a.rect(0, 17, 32, 3, METAL)
    a.rect(0, 17, 32, 1, METAL_L)
    _rivets(a, 0, 18, 32, METAL_D, 3)
    a.rect(14, 17, 4, 3, METAL_D), a.px(15, 18, CYAN), a.px(16, 18, CYAN)
    a.shade(0, 0, 32, 20, 1.06, 0.84, 0.74)
    a.noise(0, 0, 32, 20, 0.05)
    torso = a.region(0, 0, 32, 20)
    # Шлем 32×16: белая скорлупа, визор в середине (перёд), обод, наушные диски, кольцо шеи.
    a.rect(0, 20, 32, 16, SUIT)
    a.rect(0, 20, 32, 2, SUIT_L)
    a.rect(15, 20, 2, 4, ORANGE)  # полоса по темени
    a.rect(8, 23, 16, 10, METAL_D)
    a.rect(9, 24, 14, 8, CYAN)
    a.rect(9, 30, 14, 2, CYAN_D)
    a.rect(9, 24, 14, 1, CYAN_D)
    for i in range(4):
        a.px(11 + i, 28 - i, CYAN_L), a.px(12 + i, 28 - i, CYAN_L)
    a.px(19, 26, CYAN_L), a.px(20, 25, CYAN_L)
    a.rect(4, 26, 3, 4, METAL), a.px(5, 27, METAL_L)
    a.rect(25, 26, 3, 4, METAL), a.px(26, 27, METAL_L)
    for x in (0, 1, 30, 31):
        a.rect(x, 24, 1, 7, SUIT_D)  # шов на затылке
    a.rect(0, 33, 32, 3, METAL)
    a.rect(0, 33, 32, 1, METAL_L)
    _rivets(a, 0, 34, 32, METAL_D, 4)
    a.shade(0, 20, 32, 16, 1.08, 0.9, 0.82)
    a.noise(0, 20, 32, 16, 0.04)
    helmet = a.region(0, 20, 32, 16)
    # Рука 16×16: рукав с кольцами-гармошкой у локтя, оранжевая полоса, металлическая перчатка.
    a.rect(32, 0, 16, 16, SUIT)
    a.rect(32, 2, 16, 2, ORANGE), a.rect(32, 3, 16, 1, ORANGE_D)
    for y in (7, 9):
        a.rect(32, y, 16, 1, SUIT_D)
    a.rect(32, 11, 16, 1, METAL_L)
    a.rect(32, 12, 16, 4, METAL)
    a.rect(32, 14, 16, 1, METAL_D)
    for x in (35, 39, 43):
        a.px(x, 15, METAL_D)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.76)
    a.noise(32, 0, 16, 16, 0.05)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: штанина со швом, наколенник, гармошка под ним, ботинок с ремнём.
    a.rect(48, 0, 16, 18, SUIT)
    a.rect(55, 0, 1, 18, SUIT_D)
    a.rect(52, 9, 8, 4, METAL_L), a.rect(52, 12, 8, 1, METAL_D)
    for y in (3, 6, 14, 16):
        a.rect(48, y, 16, 1, SUIT_D)
    a.rect(49, 1, 3, 2, CYAN_D)
    a.rect(48, 18, 16, 6, METAL)
    a.rect(48, 18, 16, 1, METAL_L)
    a.rect(48, 21, 16, 1, METAL_D)
    a.rect(54, 20, 4, 2, ORANGE)
    a.shade(48, 0, 16, 24, 1.05, 0.85, 0.76)
    a.noise(48, 0, 16, 24, 0.05)
    leg = a.region(48, 0, 16, 24)
    # Ранец 16×12 (бока лентой) и его крышка 8×8, подошва, темя.
    a.rect(32, 16, 16, 12, METAL)
    a.rect(32, 16, 16, 1, METAL_L)
    a.rect(32, 27, 16, 1, METAL_D)
    for x in (36, 44):
        a.rect(x, 17, 1, 10, METAL_D)
    a.rect(38, 19, 4, 2, CYAN), a.px(39, 19, CYAN_L)
    a.rect(37, 23, 6, 3, METAL_D), a.rect(38, 24, 4, 1, ORANGE)
    a.noise(32, 16, 16, 12, 0.07)
    pack = a.region(32, 16, 16, 12)
    a.rect(32, 28, 8, 8, METAL_L)
    a.rect(33, 29, 6, 6, METAL)
    a.px(35, 31, CYAN), a.px(36, 32, METAL_D)
    pack_top = a.region(32, 28, 8, 8)
    a.rect(40, 28, 4, 4, METAL_D)
    a.rect(44, 28, 4, 4, SUIT_L)
    sole, crown = a.region(40, 28, 4, 4), a.region(44, 28, 4, 4)

    parts = lm.biped(leg, torso, helmet, arm, sole, crown)
    # Шлем вместо головы: шар заметно шире шеи, кольцо у основания.
    parts["head"][1] = lm.loft([(1.44, 0.075, 0.08), (1.5, 0.135, 0.145), (1.6, 0.16, 0.17), (1.7, 0.155, 0.165),
                                (1.78, 0.11, 0.12), (1.82, 0.05, 0.055)], helmet, 6, caps=(None, crown))
    # Ранец за спиной (спина это +Z) с выступом баллона сверху.
    parts["body"][1].extend(lm.at(lm.box((0.27, 0.36, 0.13), pack, pack_top, pack_top), 0.0, 1.2, 0.2))
    return lm.assemble("hero", a, parts)


# --- Пришелец-пехотинец ------------------------------------------------------------------------

def space_enemy():
    """Пришелец-пехотинец: тонкий, фиолетовый, большая вытянутая назад голова с чёрными
    миндалевидными глазами, металлический нагрудник, усик, энергожезл в правой руке."""
    a = lm.Atlas(64, 64, 123)
    # Тело 32×20: нагрудник с огоньком на груди, голая кожа на боках и спине, пояс.
    a.rect(0, 0, 32, 20, VIOLET)
    for x in (2, 6, 25, 29):
        a.rect(x, 3, 1, 12, VIOLET_D)  # рёбра-жилы
    a.rect(9, 2, 14, 11, METAL)
    a.rect(9, 2, 14, 1, METAL_L)
    a.rect(9, 12, 14, 1, METAL_D)
    a.rect(15, 2, 2, 11, METAL_D)
    a.rect(14, 5, 4, 3, CYAN_D), a.rect(15, 6, 2, 1, CYAN_L)
    _rivets(a, 9, 10, 14, METAL_L, 3)
    a.rect(12, 0, 8, 2, VIOLET_D)  # шея
    a.rect(0, 14, 32, 2, VIOLET_D)
    a.rect(0, 17, 32, 3, METAL_D)
    a.rect(0, 17, 32, 1, METAL)
    a.rect(14, 17, 4, 3, CYAN_D), a.px(15, 18, CYAN_L)
    a.shade(0, 0, 32, 20, 1.08, 0.82, 0.72)
    a.noise(0, 0, 32, 20, 0.06)
    body = a.region(0, 0, 32, 20)
    # Голова 32×16: лицо в середине, глаза миндалинами с бликом, щель рта, жилы на черепе.
    a.rect(0, 20, 32, 16, VIOLET)
    a.rect(0, 20, 32, 3, VIOLET_L)
    for x, y in ((4, 23), (5, 24), (6, 26), (27, 23), (26, 24), (25, 26), (15, 21), (16, 22)):
        a.px(x, y, VIOLET_D)
    for x0, s in ((9, 1), (22, -1)):
        for k, h in enumerate((2, 4, 5, 4, 2)):
            a.rect(x0 + k * s, 27 - h // 2 - (1 if k < 2 else 0), 1, h, BLACK)
    a.px(10, 25, CYAN_L), a.px(21, 25, CYAN_L)
    a.px(15, 29, VIOLET_D), a.px(16, 29, VIOLET_D)  # ноздри
    a.rect(13, 32, 6, 1, BLACK)
    a.rect(0, 34, 32, 2, VIOLET_D)
    a.shade(0, 20, 32, 16, 1.1, 0.86, 0.78)
    a.noise(0, 20, 32, 16, 0.05)
    head = a.region(0, 20, 32, 16)
    # Конечность 16×16: жилы, сустав посередине, металлический браслет и сапог внизу.
    a.rect(32, 0, 16, 16, VIOLET)
    a.rect(32, 7, 16, 2, VIOLET_D)
    a.rect(39, 0, 1, 12, VIOLET_D)
    a.rect(32, 11, 16, 1, METAL_L)
    a.rect(32, 12, 16, 4, METAL_D)
    a.shade(32, 0, 16, 16, 1.02, 0.9, 0.7)
    a.noise(32, 0, 16, 16, 0.06)
    limb = a.region(32, 0, 16, 16)
    # Жезл 16×4: рукоять у кисти, древко, светящийся наконечник.
    a.rect(32, 16, 16, 4, METAL)
    a.rect(32, 16, 16, 1, METAL_L)
    a.rect(32, 19, 16, 1, METAL_D)
    a.rect(32, 16, 3, 4, METAL_D)
    a.rect(42, 16, 6, 4, CYAN), a.rect(43, 17, 4, 2, CYAN_L)
    a.clear(46, 16), a.clear(47, 16), a.clear(47, 17), a.clear(46, 19), a.clear(47, 19)
    rod = a.region(32, 16, 16, 4)
    # Усик 8×8: стебель и огонёк, остальное прозрачно.
    a.rect(51, 2, 2, 6, VIOLET_D)
    a.rect(50, 0, 4, 3, CYAN), a.px(51, 1, CYAN_L)
    feeler = a.region(48, 0, 8, 8)
    a.rect(56, 8, 4, 4, METAL_D)
    a.rect(60, 8, 4, 4, VIOLET_L)
    chip, crown = a.region(56, 8, 4, 4), a.region(60, 8, 4, 4)

    m = lm.Model("enemy", a)
    for side, x in (("l", -0.09), ("r", 0.09)):
        m.part("leg_" + side, (x, 0.86, 0.0),
               lm.loft([(0.0, 0.055, 0.12, x, -0.04), (0.07, 0.035, 0.04, x, 0.0), (0.46, 0.045, 0.045, x, 0.0),
                        (0.88, 0.04, 0.04, x, 0.0)], limb, 4, math.pi / 4.0, caps=(chip, None)))
    m.part("body", (0.0, 0.86, 0.0),
           lm.loft([(0.84, 0.12, 0.08), (0.96, 0.075, 0.06), (1.1, 0.14, 0.095), (1.36, 0.17, 0.11), (1.46, 0.045, 0.045)],
                   body, 6))
    m.part("head", (0.0, 1.46, 0.0),
           lm.loft([(1.44, 0.05, 0.055), (1.52, 0.105, 0.115, 0.0, 0.0), (1.63, 0.155, 0.175, 0.0, 0.03),
                    (1.75, 0.15, 0.18, 0.0, 0.06), (1.83, 0.08, 0.1, 0.0, 0.08)], head, 6, caps=(None, crown))
           + lm.quad((-0.06, 1.93, -0.04), (0.06, 1.93, -0.04), (0.06, 1.8, 0.0), (-0.06, 1.8, 0.0), feeler), "body")
    m.part("arm_l", (-0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.032, 0.032, -0.22, 0.0), (1.08, 0.036, 0.036, -0.215, 0.0), (1.4, 0.034, 0.034, -0.2, 0.0)],
                   limb, 4, math.pi / 4.0, caps=(chip, None)), "body")
    m.part("arm_r", (0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.032, 0.032, 0.22, 0.0), (1.08, 0.036, 0.036, 0.215, 0.0), (1.4, 0.034, 0.034, 0.2, 0.0)],
                   limb, 4, math.pi / 4.0, caps=(chip, None))
           + lm.quad((0.22, 0.84, -0.02), (0.22, 0.84, -0.72), (0.22, 0.74, -0.72), (0.22, 0.74, -0.02), rod), "body")
    return m


# --- Командир пришельцев -----------------------------------------------------------------------

def space_captain():
    """Командир: второй боец и главарь. Крупный пришелец в мундире с золотом, вместо темени
    большой розовый мозг под куполом в бликах, за спиной плащ до колен."""
    a = lm.Atlas(64, 64, 143)
    coat, coat_d = rgb("3C2A6E"), rgb("241846")
    # Мундир 32×20: борта с золотыми застёжками, ворот-стойка, эполеты, пояс с пряжкой.
    a.rect(0, 0, 32, 17, coat)
    for x in (10, 21):
        a.rect(x, 0, 2, 17, coat_d)
    a.rect(13, 0, 6, 4, VIOLET)
    a.rect(13, 3, 6, 1, VIOLET_D)
    a.rect(12, 0, 1, 5, GOLD), a.rect(19, 0, 1, 5, GOLD)
    for y in (6, 9, 12, 15):
        a.px(14, y, GOLD), a.px(17, y, GOLD)
        a.rect(15, y, 2, 1, GOLD_D)
    a.rect(0, 0, 5, 2, GOLD), a.rect(27, 0, 5, 2, GOLD)
    a.rect(0, 2, 5, 1, GOLD_D), a.rect(27, 2, 5, 1, GOLD_D)
    a.rect(4, 6, 3, 3, CYAN_D), a.px(5, 7, CYAN_L)  # орден
    a.rect(0, 17, 32, 3, BLACK)
    a.rect(14, 17, 4, 3, GOLD)
    a.rect(15, 18, 2, 1, CYAN)
    a.shade(0, 0, 32, 20, 1.1, 0.82, 0.7)
    a.noise(0, 0, 32, 20, 0.07)
    torso = a.region(0, 0, 32, 20)
    # Голова 32×24: сверху мозг (три нижние полосы колец это лицо и обод купола).
    a.rect(0, 20, 32, 12, BRAIN)
    for y in range(20, 32):
        for x in range(32):
            wave = math.sin(x * 1.1 + math.sin(y * 0.9) * 2.0) + math.sin(y * 1.3 + x * 0.35)
            if wave > 1.0:
                a.px(x, y, BRAIN_D)
            elif wave < -1.2:
                a.px(x, y, BRAIN_L)
    a.rect(15, 20, 2, 12, BRAIN_D)  # борозда между полушариями
    for x, y in ((10, 21), (11, 22), (12, 23), (13, 24), (21, 21), (22, 22), (5, 26), (6, 27), (26, 25), (27, 26)):
        a.px(x, y, CYAN_L)  # блики стекла купола
    a.rect(8, 21, 1, 9, CYAN_L), a.rect(9, 22, 1, 6, CYAN_L)
    a.rect(0, 32, 32, 4, METAL)
    a.rect(0, 32, 32, 1, METAL_L)
    a.rect(0, 35, 32, 1, METAL_D)
    _rivets(a, 0, 33, 32, GOLD, 4)
    a.rect(0, 36, 32, 8, VIOLET)
    for x0, s in ((9, 1), (22, -1)):
        for k, h in enumerate((2, 3, 4, 3, 2)):
            a.rect(x0 + k * s, 39 - h // 2, 1, h, BLACK)
    a.px(10, 38, ORANGE), a.px(21, 38, ORANGE)
    a.rect(8, 36, 6, 1, VIOLET_D), a.rect(18, 36, 6, 1, VIOLET_D)  # надбровья
    a.px(15, 40, VIOLET_D), a.px(16, 40, VIOLET_D)
    a.rect(12, 42, 8, 1, BLACK)
    a.rect(0, 37, 4, 6, VIOLET_D), a.rect(28, 37, 4, 6, VIOLET_D)
    a.shade(0, 20, 32, 24, 1.08, 0.88, 0.82)
    a.noise(0, 20, 32, 24, 0.05)
    head = a.region(0, 20, 32, 24)
    # Рукав 16×16 с золотым обшлагом и когтистой кистью.
    a.rect(32, 0, 16, 16, coat)
    a.rect(32, 9, 16, 3, GOLD)
    a.rect(32, 10, 16, 1, GOLD_D)
    a.rect(32, 12, 16, 4, VIOLET)
    a.rect(32, 15, 16, 1, VIOLET_D)
    for x in (35, 39, 43):
        a.px(x, 14, VIOLET_D)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.75)
    a.noise(32, 0, 16, 16, 0.07)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: тёмные штаны с лампасом, высокий сапог с золотой пряжкой.
    a.rect(48, 0, 16, 14, rgb("221C34"))
    a.rect(55, 0, 2, 14, GOLD_D)
    a.rect(48, 14, 16, 10, METAL_D)
    a.rect(48, 14, 16, 2, METAL)
    a.rect(54, 19, 4, 2, GOLD)
    a.shade(48, 0, 16, 24, 1.05, 0.85, 0.75)
    a.noise(48, 0, 16, 24, 0.07)
    leg = a.region(48, 0, 16, 24)
    # Плащ 24×20: складки, золотая кайма по низу и краям, подкладка у ворота.
    a.rect(0, 44, 24, 20, CLOAK)
    for x in (3, 7, 12, 16, 20):
        a.rect(x, 46, 1, 16, CLOAK_D)
        a.rect(x + 1, 47, 1, 14, CLOAK_L)
    a.rect(0, 44, 24, 2, GOLD), a.rect(0, 45, 24, 1, GOLD_D)
    a.rect(0, 62, 24, 2, GOLD), a.rect(0, 62, 24, 1, GOLD_D)
    a.rect(0, 44, 1, 20, GOLD), a.rect(23, 44, 1, 20, GOLD)
    a.shade(0, 44, 24, 20, 1.05, 0.8, 0.85)
    a.noise(0, 44, 24, 20, 0.07)
    a.rect(32, 16, 4, 4, METAL_D)
    a.rect(36, 16, 4, 4, BRAIN_L)
    sole, crown = a.region(32, 16, 4, 4), a.region(36, 16, 4, 4)

    parts = lm.biped(leg, torso, head, arm, sole, crown, 1.18)
    # Голова: лицо, обод купола шире лица, над ним купол с мозгом.
    parts["head"][1] = lm.loft([(1.44, 0.065, 0.07), (1.51, 0.105, 0.115, 0.0, -0.005), (1.6, 0.125, 0.135),
                                (1.64, 0.18, 0.185), (1.76, 0.2, 0.205), (1.87, 0.165, 0.17), (1.93, 0.07, 0.075)],
                               head, 6, caps=(None, crown))
    # Плащ: три полотнища от плеч до колен, книзу шире и дальше от спины.
    cloak = []
    top = [(0.27, 0.19), (0.09, 0.2), (-0.09, 0.2), (-0.27, 0.19)]
    low = [(0.37, 0.3), (0.13, 0.34), (-0.13, 0.34), (-0.37, 0.3)]
    for i in range(3):
        cloak += lm.quad((top[i][0], 1.4, top[i][1]), (top[i + 1][0], 1.4, top[i + 1][1]),
                         (low[i + 1][0], 0.5, low[i + 1][1]), (low[i][0], 0.5, low[i][1]),
                         a.region(i * 8, 44, 8, 20))
    parts["body"][1].extend(cloak)
    return lm.assemble("captain", a, parts)


MODELS = [space_hero, space_enemy, space_captain]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        models = [f() for f in MODELS]
        for m in models:
            print("%-8s частей %d, треугольников %d" % (m.name, len(m.parts), m.tris()))
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
