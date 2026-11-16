#!/usr/bin/env python3
"""Персонажи «Динозавров» для low poly и «продвинутых» (#144): пещерный человек, прямоходящий
раптор, вождь-шаман в черепе тираннозавра. Зеркала `pirate_hero`, `pirate_enemy`,
`pirate_captain` из `lowpoly_meshes.py` и космических из `space_mesh_chars.py`: те же имена
частей, родители и точки вращения (демки анимируют части), взгляд в −Z, ноль в подошвах, рост
не выше 1,93 м; у раптора оружие в правой руке на месте сабли скелета (челюсть с зубами на
кости). Цвета и облик из основы 16/32 (`dinosaurs16.PALETTE`): оранжевая пятнистая шкура через
одно плечо, лохматая копна и кость в волосах у героя, зелёная чешуя и жёлтое брюхо у раптора.
Плотный набор «продвинутых» получается из этих же функций (плотность и размер атласа задаёт
`lowpoly_meshes`), поэтому геометрия собирается его помощниками.

    python3 tools/dinosaurs_mesh_chars.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import dinosaurs16 as d16  # noqa: E402

rgb, mul = lm.rgb, lm.mul


def _pal(i):
    return tuple(d16.PALETTE[i])


# Цвета из палитры основы 16/32, светлые и тёмные тона к ним.
BLACK = _pal(d16.K)
SKIN, SKIN_D, SKIN_L = _pal(d16.SKIN), _pal(d16.TAN), rgb("F0B888")
HIDE, HIDE_D, HIDE_L = _pal(d16.RED), rgb("B03E1A"), rgb("F88C44")
FUR = _pal(d16.SKY)
HAIR, HAIR_D, HAIR_L = _pal(d16.DARK), rgb("2E1C18"), rgb("7C4C38")
BONE, BONE_D, BONE_DD = _pal(d16.WHITE), _pal(d16.GREY), rgb("8C8270")
SCALE, SCALE_D, SCALE_L = _pal(d16.VIOLET), _pal(d16.PLUM), rgb("94D85E")
BELLY, BELLY_D = _pal(d16.GOLD), _pal(d16.BRASS)
STONE, STONE_D = _pal(d16.METAL), rgb("4E4046")
TEAL, TEAL_D = _pal(d16.AQUA), _pal(d16.SEA)
CLAY = rgb("8A3A26")


def _spots(a, x0, y0, spots, c=HAIR):
    """Пятна шкуры: `(x, y, w, h)` от угла куска."""
    for x, y, w, h in spots:
        a.rect(x0 + x, y0 + y, w, h, c)


def _zigzag(a, x, y, w, depths):
    """Рваный край: снизу куска вырезаются зубцы, глубина по столбцам из `depths`."""
    for i in range(w):
        d = depths[i % len(depths)]
        if d:
            a.clear(x + i, y - d, 1, d)


def _bone(length, r, knob, region, cap, n=4):
    """Кость вдоль Y с центром в нуле: стержень и утолщения на концах."""
    h = length / 2.0
    return lm.loft([(-h, knob * 0.5, knob * 0.5), (-h + knob * 0.5, knob, knob), (-h + knob * 1.6, knob * 0.9, knob * 0.9),
                    (-h + knob * 2.2, r, r), (h - knob * 2.2, r, r), (h - knob * 1.6, knob * 0.9, knob * 0.9),
                    (h - knob * 0.5, knob, knob), (h, knob * 0.5, knob * 0.5)], region, n, caps=(cap, cap))


# --- Пещерный человек --------------------------------------------------------------------------

def dinosaurs_hero():
    """Пещерный человек: оранжевая пятнистая шкура через левое плечо с меховой кромкой и рваным
    подолом, ожерелье из клыков, лохматая копна шире головы, кость в волосах, босые ступни."""
    a = lm.Atlas(64, 64, 211)
    # Торс 32×20: середина куска это грудь. Шкура наискось от правого бока к левому плечу,
    # спереди и сзади; ниже пояса шкура целиком, верёвка с костяной застёжкой.
    for y in range(20):
        for x in range(32):
            if 8 <= x < 24:
                hide = (x - 16) >= 6.0 - y
            else:
                hide = ((x - 24) % 32) <= 4.0 + 0.8 * y
            a.px(x, y, HIDE if hide or y >= 15 else SKIN)
    for y in range(15):
        for x in range(32):
            # Меховая кромка по косому краю шкуры.
            if a.get(x, y)[:3] == HIDE and a.get((x - 1) % 32, y)[:3] == SKIN:
                a.px(x, y, FUR)
            if a.get(x, y)[:3] == HIDE and a.get((x + 1) % 32, y)[:3] == SKIN:
                a.px(x, y, FUR)
    _spots(a, 0, 0, [(21, 4, 2, 2), (25, 2, 2, 1), (26, 7, 2, 2), (18, 9, 2, 1), (14, 12, 2, 1), (5, 17, 2, 2),
                     (22, 12, 2, 2), (29, 12, 2, 2), (28, 3, 1, 2), (9, 17, 2, 1), (20, 17, 1, 2), (1, 13, 2, 1)])
    for x, y in ((24, 5), (24, 9), (11, 18), (27, 15), (17, 13), (30, 8)):
        a.px(x, y, HIDE_L)
    # Грудь и живот: ключицы, грудная мышца, пупок.
    for x in (9, 10, 11, 12):
        a.px(x, 9, SKIN_D)
    a.px(8, 10, SKIN_D), a.px(10, 7, SKIN_L), a.px(11, 7, SKIN_L), a.px(9, 12, SKIN_D)
    for x in range(2, 8):
        a.px(x, 5, SKIN_D)
    a.rect(13, 0, 6, 3, SKIN), a.rect(14, 2, 4, 1, SKIN_D)  # шея
    # Ожерелье: шнур по основанию шеи и клыки на груди.
    for x in range(6, 26):
        a.px(x, 4, HAIR_D)
    for x in (9, 12, 15, 18):
        a.px(x, 5, BONE), a.px(x, 6, BONE)
    a.px(15, 7, BONE_D), a.px(12, 7, BONE_D)
    # Пояс-верёвка и костяная застёжка.
    for x in range(32):
        a.px(x, 15, BELLY_D if x % 3 else HAIR)
        a.px(x, 16, HAIR if x % 3 == 1 else BELLY_D)
    a.rect(14, 15, 5, 2, BONE), a.px(13, 15, BONE_D), a.px(19, 16, BONE_D), a.px(16, 16, BONE_D)
    a.rect(0, 18, 32, 2, HIDE_D)
    a.shade(0, 0, 32, 20, 1.08, 0.86, 0.74)
    a.noise(0, 0, 32, 20, 0.06)
    torso = a.region(0, 0, 32, 20)
    # Голова 32×16, четыре полосы по 4 строки: макушка, копна с чёлкой, лицо, челюсть с шеей.
    a.rect(0, 20, 32, 16, HAIR)
    a.rect(0, 20, 32, 2, HAIR_L)
    for x in range(32):
        # Пряди: светлые и тёмные вертикальные штрихи по всей копне.
        c = (HAIR_L, HAIR, HAIR_D, HAIR)[(x * 7 + 3) % 4]
        a.rect(x, 22 + (x * 5) % 3, 1, 5, c)
        if x < 8 or x >= 24:
            a.rect(x, 28 + (x % 2), 1, 5 - (x % 3), c)
    a.rect(9, 28, 14, 8, SKIN)
    a.rect(8, 29, 1, 4, SKIN), a.rect(23, 29, 1, 4, SKIN)  # уши
    a.px(8, 30, SKIN_D), a.px(23, 30, SKIN_D)
    for x, d in ((9, 1), (11, 2), (12, 1), (14, 1), (16, 2), (17, 1), (19, 1), (20, 2), (22, 1)):
        a.rect(x, 27, 1, d + 1, HAIR)  # зубцы чёлки
    a.rect(10, 29, 4, 1, HAIR_D), a.rect(18, 29, 4, 1, HAIR_D)  # брови козырьком
    a.px(11, 30, BONE), a.px(12, 30, BLACK), a.px(19, 30, BLACK), a.px(20, 30, BONE)
    a.rect(15, 30, 2, 2, SKIN_L), a.px(15, 32, SKIN_D), a.px(16, 32, SKIN_D)  # нос
    a.rect(10, 32, 3, 1, SKIN_D), a.rect(19, 32, 3, 1, SKIN_D)  # скулы
    a.rect(14, 33, 4, 1, SKIN_D), a.px(13, 33, HAIR)  # рот с ухмылкой набок
    for x in range(9, 23):
        if x % 2:
            a.px(x, 34, SKIN_D)  # щетина на челюсти
    a.rect(9, 35, 14, 1, SKIN_D)
    a.shade(0, 20, 32, 16, 1.1, 0.88, 0.8)
    a.noise(0, 20, 32, 16, 0.06)
    head = a.region(0, 20, 32, 16)
    # Рука 16×16: голая, кожаный ремешок с клыком на плече, обмотка на запястье, кулак.
    a.rect(32, 0, 16, 16, SKIN)
    a.rect(32, 3, 16, 2, HAIR), a.rect(32, 3, 16, 1, HAIR_L)
    a.px(39, 5, BONE), a.px(40, 5, BONE), a.px(39, 6, BONE)
    a.rect(39, 6, 1, 3, SKIN_D)  # мышца плеча
    a.rect(32, 10, 16, 2, FUR), a.rect(32, 11, 16, 1, BELLY_D)
    for x in (34, 38, 42, 46):
        a.px(x, 10, BELLY_D)
    a.rect(32, 13, 16, 3, SKIN)
    a.rect(32, 15, 16, 1, SKIN_D)
    for x in (35, 39, 43):
        a.px(x, 14, SKIN_D)
    a.shade(32, 0, 16, 16, 1.06, 0.9, 0.76)
    a.noise(32, 0, 16, 16, 0.05)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: вверху шкура до середины бедра, колено, меховая обмотка на голени, босая
    # ступня с пальцами спереди.
    a.rect(48, 0, 16, 24, SKIN)
    a.rect(48, 0, 16, 5, HIDE)
    for i, d in enumerate((2, 1, 3, 1, 2, 0, 2, 1, 2, 1, 3, 1, 2, 0, 1, 2)):
        a.rect(48 + i, 5, 1, d, HIDE)
    _spots(a, 48, 0, [(2, 1, 2, 2), (9, 2, 2, 1), (13, 0, 2, 2), (6, 4, 1, 2)])
    a.px(55, 9, SKIN_L), a.px(56, 9, SKIN_L), a.px(54, 11, SKIN_D), a.px(57, 11, SKIN_D)  # колено
    a.rect(48, 14, 16, 3, FUR)
    for x in range(48, 64, 3):
        a.px(x, 14, BELLY_D), a.px(x + 1, 16, BELLY_D)
    a.rect(48, 15, 16, 1, HAIR)
    a.rect(48, 20, 16, 4, SKIN)
    a.rect(48, 23, 16, 1, SKIN_D)
    for x in (53, 55, 57, 59):
        a.px(x, 22, SKIN_D), a.px(x, 21, SKIN_D)  # пальцы
    for x in (52, 54, 56, 58):
        a.px(x, 22, SKIN_L)
    a.shade(48, 0, 16, 24, 1.05, 0.86, 0.76)
    a.noise(48, 0, 16, 24, 0.05)
    leg = a.region(48, 0, 16, 24)
    # Кость 16×4: белая, тени у утолщений.
    a.rect(32, 16, 16, 4, BONE)
    a.rect(32, 19, 16, 1, BONE_D)
    for x in (33, 36, 43, 46):
        a.px(x, 17, BONE_D)
    bone = a.region(32, 16, 16, 4)
    # Подол 32×10: шкура с пятнами, снизу рваные зубцы.
    a.rect(0, 36, 32, 10, HIDE)
    a.rect(0, 36, 32, 1, HIDE_D)
    _spots(a, 0, 36, [(2, 2, 2, 2), (7, 5, 2, 1), (11, 2, 2, 2), (15, 5, 2, 2), (20, 1, 2, 1), (23, 4, 2, 2),
                      (28, 2, 2, 2), (30, 6, 1, 2), (5, 7, 1, 1), (18, 3, 1, 1)])
    for x in (4, 13, 22, 27):
        a.px(x, 40, HIDE_L)
    a.shade(0, 36, 32, 10, 1.0, 0.82, 0.8)
    a.noise(0, 36, 32, 10, 0.06)
    _zigzag(a, 0, 46, 32, (3, 1, 2, 0, 1, 4, 2, 0, 1, 3, 0, 2, 1))
    hem = a.region(0, 36, 32, 10)
    a.rect(40, 28, 4, 4, SKIN_D)
    a.rect(44, 28, 4, 4, HAIR)
    a.rect(36, 28, 4, 4, BONE_D)
    sole, crown, knob = a.region(40, 28, 4, 4), a.region(44, 28, 4, 4), a.region(36, 28, 4, 4)

    parts = lm.biped(leg, torso, head, arm, sole, crown)
    # Голова с копной: лицо обычное, выше бровей волосы шире черепа и сдвинуты к затылку.
    parts["head"][1] = lm.loft([(1.44, 0.055, 0.06), (1.52, 0.092, 0.102, 0.0, -0.005), (1.63, 0.108, 0.118, 0.0, -0.003),
                                (1.72, 0.146, 0.152, 0.0, 0.022), (1.81, 0.09, 0.098, 0.0, 0.03)],
                               head, 6, caps=(None, crown))
    # Кость в волосах: наискось через затылок, концы торчат по бокам копны.
    parts["head"][1].extend(lm.at(lm.rot(_bone(0.46, 0.014, 0.03, bone, knob), 0.0, 0.0, 62.0), 0.0, 1.735, 0.1))
    # Подол: юбка шкуры от пояса до середины бедра, шире бёдер, с изнанкой.
    skirt = lm.loft([(0.6, 0.24, 0.165), (0.8, 0.222, 0.148), (0.94, 0.166, 0.112)], hem, 8)
    parts["body"][1].extend(skirt + lm.flip(skirt))
    return lm.assemble("hero", a, parts)


# --- Раптор ------------------------------------------------------------------------------------

def dinosaurs_enemy():
    """Прямоходящий раптор: зелёная чешуя с тёмными полосами по спине, жёлтое брюхо, длинная
    узкая морда с зубами, гребень красных перьев, ноги коленом вперёд и пяткой назад с серпом
    когтя, хвост за спиной, в правой лапе челюсть с зубами на кости."""
    a = lm.Atlas(64, 64, 223)
    # Тело 32×20: брюхо в середине (перёд) с поперечными складками, спина с полосами.
    a.rect(0, 0, 32, 20, SCALE)
    for y in range(20):
        half = 3 if y < 4 else 5 if y < 14 else 4
        a.rect(16 - half, y, half * 2, 1, BELLY)
        a.px(16 - half - 1, y, SCALE_L), a.px(16 + half, y, SCALE_L)
    for y in (5, 8, 11, 14, 17):
        a.rect(12, y, 8, 1, BELLY_D)
    for y in (2, 6, 10, 14, 18):
        a.rect(0, y, 5, 1, SCALE_D), a.rect(27, y, 5, 1, SCALE_D)  # полосы через хребет
        a.rect(5, y + 1, 2, 1, SCALE_D), a.rect(25, y + 1, 2, 1, SCALE_D)
    for x, y in ((8, 3), (9, 7), (7, 11), (9, 15), (23, 4), (22, 8), (24, 12), (22, 16), (3, 4), (28, 8), (2, 12)):
        a.px(x, y, SCALE_L)  # чешуйки
    a.shade(0, 0, 32, 20, 1.08, 0.84, 0.74)
    a.noise(0, 0, 32, 20, 0.06)
    body = a.region(0, 0, 32, 20)
    # Голова 32×16, лежит горизонтально: по вертикали от кончика морды (верх куска) к затылку,
    # по горизонтали вокруг морды: края куска это темя, середина это подбородок, четверти это бока.
    a.rect(0, 20, 32, 16, SCALE)
    a.rect(12, 20, 8, 16, BELLY)
    a.rect(13, 22, 6, 1, BELLY_D), a.rect(13, 27, 6, 1, BELLY_D), a.rect(13, 32, 6, 1, BELLY_D)
    for y in (24, 27, 30, 33):
        a.rect(0, y, 3, 1, SCALE_D), a.rect(29, y, 3, 1, SCALE_D)
    a.rect(0, 34, 32, 2, SCALE_D)
    for x0, s in ((10, -1), (21, 1)):
        a.rect(x0, 20, 1, 11, BLACK)  # щель пасти вдоль морды
        for y in range(21, 31, 2):
            a.px(x0 - s, y, BONE)  # зубы
        a.px(x0, 31, BLACK), a.px(x0 + s, 32, BLACK)  # уголок пасти вверх
    for x0, s in ((6, -1), (25, 1)):
        a.rect(x0 - 1, 29, 3, 3, BELLY)  # глаз с щелью зрачка
        a.rect(x0, 29, 1, 3, BLACK)
        a.rect(x0 + s - 1, 28, 3, 1, SCALE_D), a.px(x0 + 2 * s, 29, SCALE_D)  # надбровье
    a.px(3, 21, BLACK), a.px(28, 21, BLACK)  # ноздри
    a.rect(4, 22, 2, 1, SCALE_L), a.rect(26, 22, 2, 1, SCALE_L)
    a.shade(0, 20, 32, 16, 1.0, 0.9, 1.0)
    a.noise(0, 20, 32, 16, 0.05)
    head = a.region(0, 20, 32, 16)
    # Лапа 16×16: чешуя, складка локтя, жёлтая кисть с тремя белыми когтями.
    a.rect(32, 0, 16, 16, SCALE)
    a.rect(32, 7, 16, 1, SCALE_D)
    a.rect(39, 0, 2, 7, SCALE_L)
    for y in (2, 5, 9):
        a.rect(32, y, 3, 1, SCALE_D), a.rect(45, y, 3, 1, SCALE_D)
    a.rect(32, 11, 16, 5, BELLY)
    a.rect(32, 11, 16, 1, BELLY_D)
    for x in (34, 39, 44):
        a.rect(x, 13, 2, 3, BONE), a.px(x, 13, BONE_D)
    a.shade(32, 0, 16, 16, 1.04, 0.9, 0.72)
    a.noise(32, 0, 16, 16, 0.06)
    limb = a.region(32, 0, 16, 16)
    # Челюсть на кости 16×6: рукоять в обмотке у кисти, дальше челюсть зубами вниз.
    a.rect(32, 18, 16, 2, BONE)
    a.rect(32, 19, 16, 1, BONE_D)
    a.rect(32, 17, 4, 4, HAIR), a.px(33, 17, HAIR_L), a.px(35, 20, HAIR_L)
    a.rect(39, 17, 9, 3, BONE), a.rect(41, 16, 6, 1, BONE)
    a.rect(39, 19, 9, 1, BONE_D)
    for x in (40, 42, 44, 46):
        a.rect(x, 20, 1, 2, BONE), a.px(x, 21, BONE_D)
    a.px(47, 17, BONE_D), a.px(44, 17, BONE_DD)
    jaw = a.region(32, 16, 16, 6)
    # Гребень 8×8: три красных пера с тёмными стержнями, наклонены назад, остальное прозрачно.
    for y, line in enumerate(("......oO", "...oO.oO", "oO.oO.or", "oO.or.r.", "or.or.r.", ".rr.rrr.", ".rrrrrr.", "gggggggg")):
        for x, ch in enumerate(line):
            if ch != ".":
                a.px(48 + x, y, {"o": HIDE, "O": HIDE_L, "r": HIDE_D, "g": SCALE_D}[ch])
    crest = a.region(48, 0, 8, 8)
    a.rect(56, 8, 4, 4, SCALE_D)
    a.rect(60, 8, 4, 4, SCALE)
    chip, crown = a.region(56, 8, 4, 4), a.region(60, 8, 4, 4)
    # Нога 16×24, пять полос: бедро, колено, голень к пятке, плюсна, ступня с когтями.
    a.rect(48, 16, 16, 24, SCALE)
    a.rect(55, 16, 2, 10, SCALE_L)
    for y in (18, 22, 26, 30):
        a.rect(48, y, 4, 1, SCALE_D), a.rect(60, y, 4, 1, SCALE_D)
    a.rect(48, 25, 16, 1, SCALE_D)
    a.rect(52, 30, 8, 5, BELLY), a.rect(52, 32, 8, 1, BELLY_D)
    a.rect(48, 35, 16, 5, SCALE_D)
    a.rect(52, 35, 8, 2, SCALE)
    for x in (52, 55, 58):
        a.rect(x, 37, 2, 3, BONE), a.px(x, 37, BONE_D)
    a.rect(60, 34, 2, 3, BONE), a.px(61, 33, BONE)  # серп когтя сбоку
    a.shade(48, 16, 16, 24, 1.06, 0.86, 0.76)
    a.noise(48, 16, 16, 24, 0.05)
    leg = a.region(48, 16, 16, 24)
    # Шея 16×8: жёлтое горло спереди, полосы сзади.
    a.rect(32, 24, 16, 8, SCALE)
    a.rect(38, 24, 4, 8, BELLY)
    for y in (25, 28, 31):
        a.rect(38, y, 4, 1, BELLY_D)
        a.rect(32, y, 2, 1, SCALE_D), a.rect(46, y, 2, 1, SCALE_D)
    a.noise(32, 24, 16, 8, 0.05)
    neck = a.region(32, 24, 16, 8)
    # Хвост 32×12, лежит горизонтально: середина куска это верх с полосами, края это жёлтый низ.
    a.rect(0, 40, 32, 12, SCALE)
    a.rect(0, 40, 4, 12, BELLY), a.rect(28, 40, 4, 12, BELLY)
    a.rect(4, 40, 1, 12, SCALE_L), a.rect(27, 40, 1, 12, SCALE_L)
    for y in (41, 43, 45, 47, 49, 51):
        a.rect(11, y, 10, 1, SCALE_D)
        a.rect(9, y, 2, 1, SCALE_D if y % 4 == 1 else SCALE)
        a.rect(21, y, 2, 1, SCALE_D if y % 4 == 1 else SCALE)
    a.rect(15, 40, 2, 12, SCALE_D)
    a.shade(0, 40, 32, 12, 0.9, 1.05, 1.0)
    a.noise(0, 40, 32, 12, 0.05)
    tail = a.region(0, 40, 32, 12)

    m = lm.Model("enemy", a)
    for side, x in (("l", -0.09), ("r", 0.09)):
        # Ступня вперёд, пятка поднята и уведена назад, колено вперёд, мощное бедро.
        m.part("leg_" + side, (x, 0.86, 0.0),
               lm.loft([(0.0, 0.06, 0.13, x, -0.06), (0.07, 0.04, 0.05, x, 0.02), (0.3, 0.036, 0.042, x, 0.075),
                        (0.52, 0.055, 0.07, x, -0.045), (0.74, 0.085, 0.115, x, 0.0), (0.9, 0.06, 0.08, x, 0.0)],
                       leg, 5, caps=(chip, None)))
    # Хвост: от крестца назад и вверх, кончик загнут.
    tail_tris = lm.loft([(0.0, 0.1, 0.1), (0.2, 0.085, 0.08), (0.45, 0.055, 0.05, 0.0, -0.03),
                         (0.7, 0.03, 0.028, 0.0, -0.09), (0.88, 0.008, 0.008, 0.0, -0.16)], tail, 6)
    m.part("body", (0.0, 0.86, 0.0),
           lm.loft([(0.84, 0.13, 0.11), (0.98, 0.115, 0.105), (1.12, 0.15, 0.125, 0.0, -0.01), (1.36, 0.17, 0.115),
                    (1.46, 0.06, 0.06)], body, 6)
           + lm.at(lm.rot(tail_tris, 75.0), 0.0, 0.94, 0.03))
    # Голова: шея столбиком, на ней горизонтальный череп с длинной мордой вперёд и чуть вниз.
    skull = lm.loft([(-0.14, 0.05, 0.05), (-0.08, 0.108, 0.098), (0.04, 0.118, 0.105), (0.17, 0.08, 0.072),
                     (0.32, 0.06, 0.052), (0.41, 0.034, 0.03)], head, 6, caps=(chip, crown))
    m.part("head", (0.0, 1.46, 0.0),
           lm.loft([(1.42, 0.058, 0.062), (1.52, 0.05, 0.055), (1.64, 0.055, 0.06)], neck, 6)
           + lm.at(lm.rot(skull, -97.0), 0.0, 1.65, 0.0)
           + lm.quad((0.0, 1.91, -0.1), (0.0, 1.91, 0.2), (0.0, 1.71, 0.2), (0.0, 1.71, -0.1), crest), "body")
    m.part("arm_l", (-0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.04, 0.05, -0.22, -0.01), (1.08, 0.042, 0.042, -0.215, 0.0), (1.4, 0.046, 0.046, -0.2, 0.0)],
                   limb, 4, math.pi / 4.0, caps=(chip, None)), "body")
    m.part("arm_r", (0.2, 1.38, 0.0),
           lm.loft([(0.76, 0.04, 0.05, 0.22, -0.01), (1.08, 0.042, 0.042, 0.215, 0.0), (1.4, 0.046, 0.046, 0.2, 0.0)],
                   limb, 4, math.pi / 4.0, caps=(chip, None))
           + lm.quad((0.22, 0.87, -0.02), (0.22, 0.87, -0.72), (0.22, 0.72, -0.72), (0.22, 0.72, -0.02), jaw), "body")
    return m


# --- Вождь-шаман -------------------------------------------------------------------------------

def dinosaurs_captain():
    """Вождь-шаман: второй боец и главарь. Крупный дикарь в боевой раскраске, на голове череп
    тираннозавра с верхней челюстью козырьком и зубами над лицом, за черепом веер перьев,
    ожерелье из когтей, за спиной накидка из пятнистой шкуры до колен с рваным низом."""
    a = lm.Atlas(64, 64, 243)
    # Торс 32×20: голая грудь в раскраске, меховой ворот, ожерелье из когтей, пояс с черепком,
    # шкура на бёдрах.
    a.rect(0, 0, 32, 17, SKIN)
    a.rect(0, 0, 32, 4, HAIR)
    for x in range(32):
        a.px(x, 4, HAIR if x % 2 else SKIN)
        a.px(x, 1 + (x % 3 == 0), HAIR_L)
    a.rect(13, 0, 6, 3, SKIN), a.rect(14, 2, 4, 1, SKIN_D)
    for x in range(9, 23):
        a.px(x, 6, HAIR_D)
    for x in (10, 12, 14, 17, 19, 21):
        a.rect(x, 7, 1, 2 + (x in (14, 17)), BONE)
        a.px(x, 7, BONE_D)
    a.rect(15, 7, 2, 2, TEAL), a.px(15, 7, TEAL_D)  # бирюзовый камень в середине
    # Раскраска: белые полосы на рёбрах, красная ладонь на животе.
    for y in (10, 12, 14):
        a.rect(6, y, 5, 1, BONE), a.rect(21, y, 5, 1, BONE)
    a.rect(14, 11, 4, 3, CLAY), a.px(14, 10, CLAY), a.px(16, 10, CLAY), a.px(17, 10, CLAY)
    a.rect(11, 9, 3, 1, SKIN_D), a.rect(18, 9, 3, 1, SKIN_D)  # грудные мышцы
    for x in (0, 1, 30, 31):
        a.rect(x, 5, 1, 12, SKIN_D)  # хребет
    a.rect(0, 15, 32, 2, STONE)
    for x in range(0, 32, 4):
        a.px(x, 15, STONE_D), a.px(x + 2, 16, STONE_D)
    a.rect(14, 14, 4, 4, BONE), a.px(15, 15, BLACK), a.px(16, 15, BLACK), a.rect(15, 17, 2, 1, BONE_D)
    a.rect(0, 17, 32, 3, HIDE)
    a.rect(14, 18, 4, 2, HIDE)
    _spots(a, 0, 17, [(3, 1, 2, 1), (9, 0, 1, 2), (21, 1, 2, 1), (27, 0, 2, 2)])
    a.shade(0, 0, 32, 20, 1.1, 0.84, 0.72)
    a.noise(0, 0, 32, 20, 0.06)
    torso = a.region(0, 0, 32, 20)
    # Голова 32×24, шесть полос по 4 строки: три верхние это свод черепа с глазницами, затем
    # край черепа с зубами над лбом, лицо и челюсть с шеей.
    a.rect(0, 20, 32, 12, BONE)
    a.rect(0, 20, 32, 2, BONE_D)
    for x0 in (9, 19):
        a.rect(x0, 25, 4, 4, BLACK)  # глазницы
        a.rect(x0, 24, 4, 1, BONE_DD), a.px(x0 - 1, 26, BONE_DD), a.px(x0 + 4, 26, BONE_DD)
    a.rect(15, 22, 2, 9, BONE_D)  # шов по своду
    for x, y in ((4, 23), (5, 24), (5, 25), (6, 26), (26, 22), (26, 23), (25, 24), (27, 27), (2, 28), (29, 29),
                 (14, 29), (17, 30), (22, 22), (8, 22)):
        a.px(x, y, BONE_DD)  # трещины
    a.rect(0, 24, 2, 6, BONE_D), a.rect(30, 24, 2, 6, BONE_D)
    a.rect(0, 32, 32, 4, BONE)
    a.rect(0, 32, 32, 1, BONE_D)
    a.rect(6, 34, 20, 2, HAIR_D)  # тень под козырьком черепа
    for x in range(6, 26, 3):
        a.rect(x, 33, 2, 2, BONE), a.px(x, 35, BONE), a.px(x + 1, 33, BONE_D)
    a.rect(0, 33, 6, 3, HAIR), a.rect(26, 33, 6, 3, HAIR)
    a.rect(0, 36, 32, 8, SKIN)
    a.rect(0, 36, 7, 8, HAIR), a.rect(25, 36, 7, 8, HAIR)  # волосы на затылке
    for x in (1, 3, 5, 26, 28, 30):
        a.rect(x, 37, 1, 6, HAIR_D if x % 2 else HAIR_L)
    a.rect(7, 36, 18, 1, SKIN_D)
    a.rect(9, 37, 5, 1, HAIR_D), a.rect(18, 37, 5, 1, HAIR_D)  # брови
    a.px(10, 38, BONE), a.px(11, 38, BLACK), a.px(20, 38, BLACK), a.px(21, 38, BONE)
    a.rect(8, 39, 6, 1, CLAY), a.rect(18, 39, 6, 1, CLAY)  # красная полоса раскраски через скулы
    a.rect(15, 38, 2, 2, SKIN_L), a.px(15, 40, SKIN_D), a.px(16, 40, SKIN_D)
    a.rect(12, 41, 8, 1, HAIR_D), a.px(13, 41, BONE), a.px(18, 41, BONE)
    a.rect(15, 42, 2, 2, BONE)  # белая черта на подбородке
    a.rect(7, 43, 18, 1, SKIN_D)
    a.shade(0, 20, 32, 24, 1.08, 0.88, 0.84)
    a.noise(0, 20, 32, 24, 0.05)
    head = a.region(0, 20, 32, 24)
    # Рука 16×16: меховой наплечник, белые кольца раскраски, костяной браслет, кулак.
    a.rect(32, 0, 16, 16, SKIN)
    a.rect(32, 0, 16, 3, HAIR)
    for x in range(32, 48, 2):
        a.px(x, 3, HAIR), a.px(x + 1, 1, HAIR_L)
    a.rect(32, 5, 16, 1, BONE), a.rect(32, 7, 16, 1, BONE)
    a.rect(32, 10, 16, 2, BONE), a.rect(32, 11, 16, 1, BONE_D)
    for x in (34, 38, 42, 46):
        a.px(x, 10, BONE_DD)
    a.rect(32, 12, 16, 4, SKIN)
    a.rect(32, 15, 16, 1, SKIN_D)
    for x in (35, 39, 43):
        a.px(x, 14, SKIN_D)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.75)
    a.noise(32, 0, 16, 16, 0.06)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: шкура с рваным краем на бедре, красная полоса раскраски, меховые обмотки с
    # костяной завязкой, босая ступня.
    a.rect(48, 0, 16, 24, SKIN)
    a.rect(48, 0, 16, 6, HIDE)
    for i, d in enumerate((1, 3, 1, 2, 0, 2, 1, 3, 1, 2, 0, 1, 2, 1, 3, 1)):
        a.rect(48 + i, 6, 1, d, HIDE)
    _spots(a, 48, 0, [(1, 2, 2, 2), (7, 1, 2, 1), (12, 3, 2, 2), (5, 5, 1, 1)])
    a.rect(48, 10, 16, 1, CLAY)
    a.rect(48, 13, 16, 6, HAIR)
    a.rect(48, 13, 16, 1, HAIR_L)
    for x in range(48, 64, 2):
        a.px(x, 16, HAIR_L), a.px(x + 1, 18, HAIR_D), a.px(x, 19, HAIR)
    a.rect(54, 15, 4, 1, BONE), a.px(55, 16, BONE), a.px(56, 16, BONE_D)
    a.rect(48, 20, 16, 4, SKIN)
    a.rect(48, 23, 16, 1, SKIN_D)
    for x in (53, 55, 57, 59):
        a.px(x, 22, SKIN_D), a.px(x, 21, SKIN_D)
    a.shade(48, 0, 16, 24, 1.05, 0.85, 0.75)
    a.noise(48, 0, 16, 24, 0.06)
    leg = a.region(48, 0, 16, 24)
    # Накидка 24×20: пятнистая шкура, меховая кромка у плеч и по краям, рваный низ с клыками.
    a.rect(0, 44, 24, 20, HIDE)
    _spots(a, 0, 44, [(2, 4, 2, 2), (6, 7, 3, 2), (11, 4, 2, 3), (16, 6, 2, 2), (20, 3, 2, 2), (3, 11, 3, 2),
                      (9, 12, 2, 2), (14, 10, 2, 2), (19, 12, 3, 2), (6, 15, 2, 1), (12, 16, 2, 1), (17, 15, 1, 2),
                      (21, 8, 1, 1), (1, 8, 1, 1)])
    for x, y in ((3, 5), (7, 8), (12, 5), (17, 7), (4, 12), (15, 11), (20, 13)):
        a.px(x, 44 + y, HIDE_D)
    for x in (7, 15):
        a.rect(x, 46, 1, 16, HIDE_D)  # складки между полотнищами
        a.rect(x + 1, 47, 1, 14, HIDE_L)
    a.rect(0, 44, 24, 3, FUR)
    for x in range(24):
        a.px(x, 46 + (x % 2), FUR), a.px(x, 44 + (x % 3 == 0), BELLY_D)
    a.rect(0, 47, 1, 14, FUR), a.rect(23, 47, 1, 14, FUR)
    a.shade(0, 44, 24, 20, 1.05, 0.8, 0.88)
    a.noise(0, 44, 24, 20, 0.06)
    _zigzag(a, 0, 64, 24, (1, 3, 0, 2, 4, 1, 0, 3, 2, 0, 1))
    for x in (2, 9, 13, 20):
        if a.get(x, 62)[3]:
            a.px(x, 63, BONE), a.px(x, 62, BONE)  # клыки по подолу
    a.rect(32, 16, 4, 4, SKIN_D)
    a.rect(36, 16, 4, 4, BONE)
    a.px(37, 17, BONE_D), a.px(38, 18, BONE_DD)
    sole, crown = a.region(32, 16, 4, 4), a.region(36, 16, 4, 4)
    # Верхняя челюсть 32×12, лежит горизонтально: верх куска это кончик морды, края куска это
    # спинка морды с ноздрями, середина это тёмное нёбо, четверти это бока с десной.
    a.rect(32, 24, 32, 12, BONE)
    a.rect(44, 24, 8, 12, HAIR_D)
    a.rect(43, 24, 1, 12, BONE_DD), a.rect(52, 24, 1, 12, BONE_DD)
    a.rect(34, 25, 2, 2, BLACK), a.rect(60, 25, 2, 2, BLACK)  # ноздри
    a.rect(32, 24, 1, 12, BONE_D), a.rect(63, 24, 1, 12, BONE_D)
    for x, y in ((37, 29), (38, 30), (38, 31), (58, 28), (57, 29), (57, 30), (35, 33), (61, 33), (40, 26), (55, 33)):
        a.px(x, y, BONE_DD)
    a.rect(38, 33, 3, 2, BONE_D), a.rect(55, 29, 2, 2, BONE_D)  # впадины
    a.shade(32, 24, 32, 12, 0.94, 1.02, 1.0)
    a.noise(32, 24, 32, 12, 0.04)
    snout = a.region(32, 24, 32, 12)
    # Зубы 16×5: ряд клыков разной длины, между ними прозрачно.
    for i, d in enumerate((4, 5, 3, 5, 4, 5, 3, 4)):
        a.rect(32 + i * 2, 36, 1, d, BONE)
        a.rect(33 + i * 2, 36, 1, max(d - 2, 1), BONE_D)
    teeth = a.region(32, 36, 16, 5)
    # Веер перьев 16×12: красные и бирюзовые перья с белыми кончиками, расходятся от середины.
    for i in range(8):
        col, tip = ((HIDE, HIDE_L), (TEAL_D, TEAL))[i % 2]
        top = (4, 2, 1, 0, 0, 1, 2, 4)[i]
        a.rect(48 + i * 2, 42 + top, 2, 12 - top, col)
        a.rect(48 + i * 2, 42 + top, 1, 12 - top, tip)
        a.rect(48 + i * 2, 42 + top, 2, 2, BONE)
        a.px(48 + i * 2 + 1, 42 + top, BONE_D)
    fan = a.region(48, 42, 16, 12)

    parts = lm.biped(leg, torso, head, arm, sole, crown, 1.18)
    # Голова: лицо, над бровями край черепа шире лица, выше свод черепа.
    parts["head"][1] = lm.loft([(1.44, 0.065, 0.07), (1.51, 0.105, 0.115, 0.0, -0.005), (1.6, 0.125, 0.135),
                                (1.64, 0.168, 0.176), (1.75, 0.176, 0.19), (1.85, 0.14, 0.16), (1.9, 0.06, 0.07)],
                               head, 6, caps=(None, crown))
    # Верхняя челюсть тираннозавра козырьком вперёд, по её бокам ряды зубов над лицом.
    jaw = lm.loft([(0.0, 0.125, 0.095), (0.14, 0.12, 0.095), (0.28, 0.105, 0.085), (0.36, 0.07, 0.055)],
                  snout, 6, caps=(None, crown))
    parts["head"][1].extend(lm.at(lm.rot(jaw, -96.0), 0.0, 1.77, -0.07))
    for s in (-1.0, 1.0):
        parts["head"][1].extend(lm.quad((s * 0.114, 1.7, -0.17), (s * 0.085, 1.68, -0.42), (s * 0.085, 1.58, -0.42),
                                        (s * 0.114, 1.6, -0.17), teeth))
    parts["head"][1].extend(lm.quad((-0.075, 1.685, -0.43), (0.075, 1.685, -0.43), (0.075, 1.585, -0.43),
                                    (-0.075, 1.585, -0.43), a.region(32, 36, 8, 5)))
    # Веер перьев за черепом.
    parts["head"][1].extend(lm.quad((-0.24, 1.93, 0.17), (0.24, 1.93, 0.17), (0.2, 1.68, 0.14), (-0.2, 1.68, 0.14), fan))
    # Накидка: три полотнища от плеч до колен, книзу шире и дальше от спины.
    cloak = []
    top = [(0.27, 0.19), (0.09, 0.2), (-0.09, 0.2), (-0.27, 0.19)]
    low = [(0.37, 0.3), (0.13, 0.34), (-0.13, 0.34), (-0.37, 0.3)]
    for i in range(3):
        cloak += lm.quad((top[i][0], 1.4, top[i][1]), (top[i + 1][0], 1.4, top[i + 1][1]),
                         (low[i + 1][0], 0.5, low[i + 1][1]), (low[i][0], 0.5, low[i][1]),
                         a.region(i * 8, 44, 8, 20))
    parts["body"][1].extend(cloak)
    return lm.assemble("captain", a, parts)


MODELS = [dinosaurs_hero, dinosaurs_enemy, dinosaurs_captain]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        models = [f() for f in MODELS]
        for m in models:
            print("%-8s частей %d, треугольников %d" % (m.name, len(m.parts), m.tris()))
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
