#!/usr/bin/env python3
"""Персонажи «Супергероев» для low poly и «продвинутых» (#137): герой в синем трико с жёлтым
плащом, робот-приспешник, злодей-учёный. Зеркала `space_hero`, `space_enemy`, `space_captain` из
`space_mesh_chars.py` (а те `pirate_hero`, `pirate_enemy`, `pirate_captain` из
`lowpoly_meshes.py`): те же имена частей, родители и точки вращения (демки анимируют части),
рост, взгляд в −Z, ноль в подошвах; у робота оружие в правой руке на месте сабли скелета
(здесь выдвижная клешня). Плотный набор «продвинутых» получается из этих же функций (плотность
и размер атласа задаёт `lowpoly_meshes`), поэтому геометрия собирается его помощниками. Цвета
из палитры основы 16/32 `superheroes16.PALETTE`, облик персонажей тот же: хохолок, маска-домино
и звезда у героя, бочонок с обручами и один красный глаз у робота.

    python3 tools/superheroes_mesh_chars.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import superheroes16 as s16  # noqa: E402

rgb, mul = lm.rgb, lm.mul


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


P = s16.PALETTE
BLACK, WHITE, GREY = P[s16.K], P[s16.WHITE], P[s16.GREY]
SUIT, SUIT_D, SUIT_L = P[s16.SEA], P[s16.NAVY], mix(P[s16.SEA], P[s16.WHITE], 0.3)
GOLD, GOLD_D, GOLD_L = P[s16.GOLD], P[s16.BRASS], mix(P[s16.GOLD], P[s16.WHITE], 0.45)
SKIN, SKIN_D = P[s16.SKIN], P[s16.TAN]
METAL, METAL_D, METAL_L = P[s16.METAL], P[s16.DARK], mix(P[s16.METAL], P[s16.WHITE], 0.4)
HAIR, HAIR_L = P[s16.DARK], mix(P[s16.DARK], P[s16.METAL], 0.6)
RED, RED_D = P[s16.RED], mix(P[s16.RED], P[s16.K], 0.45)
BOT, BOT_D, BOT_L = P[s16.VIOLET], P[s16.PLUM], mix(P[s16.VIOLET], P[s16.WHITE], 0.35)
PEACH = P[s16.SKY]
# Зелёного плаща злодея в палитре 16/32 нет (там зелёно-серый только корпус роботов): изумруд
# насыщеннее корпуса, чтобы главарь не сливался со своими приспешниками.
GREEN = rgb("2E9A5A")
GREEN_D, GREEN_L = mix(GREEN, BLACK, 0.45), mix(GREEN, PEACH, 0.35)


def _rivets(a, x, y, w, c, step=4):
    for i in range(x + 1, x + w, step):
        a.px(i, y, c)


def _stamp(a, x, y, rows, c):
    """Рисунок по буквам: `#` ставит цвет, левый верхний угол в (x, y)."""
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == "#":
                a.px(x + dx, y + dy, c)


def _disc(a, cx, cy, r, c):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                a.px(x, y, c)


def _drape(top, low, y_top, y_low, yoke, regions, yoke_regions):
    """Полотнища плаща от плеч вниз и кокетка от их верха к шее (закрывает щель между тканью и
    спиной). `top` и `low`: точки (x, z) верхнего и нижнего края, `yoke`: (y, z) у шеи."""
    tris = []
    for i in range(len(top) - 1):
        tris += lm.quad((top[i][0], y_top, top[i][1]), (top[i + 1][0], y_top, top[i + 1][1]),
                        (low[i + 1][0], y_low, low[i + 1][1]), (low[i][0], y_low, low[i][1]), regions[i])
        tris += lm.quad((top[i][0] * 0.7, yoke[0], yoke[1]), (top[i + 1][0] * 0.7, yoke[0], yoke[1]),
                        (top[i + 1][0], y_top, top[i + 1][1]), (top[i][0], y_top, top[i][1]), yoke_regions[i])
    return tris


# --- Герой -------------------------------------------------------------------------------------

def superheroes_hero():
    """Герой: синее трико со звездой на груди, жёлтые пояс, перчатки и сапоги с отворотом,
    чёрная маска-домино с белыми глазами, тёмные волосы с хохолком вперёд, за спиной жёлтый
    плащ до колен с зубчатым подолом."""
    a = lm.Atlas(64, 64, 211)
    # Торс 32×20: середина куска это грудь. Верхние пять строк это плечи (ворот плаща с
    # застёжками), ниже звезда, тени мышц, пояс с пряжкой.
    a.rect(0, 0, 32, 17, SUIT)
    a.rect(0, 0, 32, 2, GOLD)
    a.rect(0, 2, 32, 1, GOLD_D)
    for x in (11, 20):
        a.rect(x, 1, 2, 2, WHITE), a.px(x + 1, 2, GREY)  # застёжки плаща
    a.rect(0, 3, 32, 2, mul(SUIT, 1.12))  # свет на плечах
    for x in (4, 27):
        a.rect(x, 6, 1, 11, SUIT_D)  # тень под руками
    a.rect(8, 10, 6, 1, SUIT_D), a.rect(18, 10, 6, 1, SUIT_D)  # низ грудных мышц
    a.px(7, 9, SUIT_D), a.px(24, 9, SUIT_D)
    for y in (12, 14):
        a.rect(13, y, 2, 1, SUIT_D), a.rect(17, y, 2, 1, SUIT_D)  # пресс
    a.rect(15, 11, 2, 6, mul(SUIT, 0.86))
    a.px(9, 6, SUIT_L), a.px(10, 6, SUIT_L), a.px(21, 6, SUIT_L)
    _stamp(a, 13, 4, s16.STAR7, GOLD)
    a.px(16, 4, GOLD_L), a.px(15, 6, GOLD_L), a.px(16, 6, GOLD_L)
    a.px(14, 9, GOLD_D), a.px(14, 10, GOLD_D), a.px(18, 10, GOLD_D)
    a.rect(0, 17, 32, 3, GOLD)
    a.rect(0, 17, 32, 1, GOLD_L)
    a.rect(0, 19, 32, 1, GOLD_D)
    a.rect(14, 17, 4, 3, GOLD_D), a.rect(15, 18, 2, 1, WHITE)
    for x in (6, 10, 21, 25):
        a.px(x, 18, GOLD_D)  # кармашки пояса
    a.shade(0, 0, 32, 20, 1.06, 0.86, 0.74)
    a.noise(0, 0, 32, 20, 0.05)
    torso = a.region(0, 0, 32, 20)
    # Голова 32×16: волосы шапкой, на висках и затылке, лицо в середине, маска-домино с белыми
    # глазами и вырезом под переносицу, уши, усмешка, шея.
    a.rect(0, 20, 32, 16, SKIN)
    a.rect(0, 20, 32, 4, HAIR)
    a.rect(0, 24, 8, 8, HAIR), a.rect(24, 24, 8, 8, HAIR)
    a.rect(8, 24, 2, 2, HAIR), a.rect(22, 24, 2, 2, HAIR)  # виски
    a.rect(10, 23, 3, 1, SKIN), a.rect(19, 23, 3, 1, SKIN)  # залысины по бокам хохолка
    a.rect(14, 24, 4, 1, HAIR)  # корень хохолка на лбу
    for x, y in ((2, 21), (3, 22), (6, 21), (12, 21), (13, 20), (17, 20), (18, 21), (25, 21), (28, 22), (29, 21),
                 (1, 26), (2, 27), (5, 25), (5, 29), (26, 26), (29, 27), (30, 25), (27, 29)):
        a.px(x, y, HAIR_L)  # пряди
    a.rect(9, 26, 14, 3, BLACK)
    a.rect(8, 27, 16, 1, BLACK)
    a.rect(10, 29, 4, 1, BLACK), a.rect(18, 29, 4, 1, BLACK)
    a.rect(11, 27, 3, 2, WHITE), a.rect(18, 27, 3, 2, WHITE)
    a.px(11, 28, GREY), a.px(20, 28, GREY)
    a.rect(8, 28, 1, 3, SKIN_D), a.rect(23, 28, 1, 3, SKIN_D)  # уши
    a.rect(15, 29, 2, 2, mul(SKIN, 0.9))
    a.px(16, 31, SKIN_D)
    a.rect(13, 32, 5, 1, SKIN_D), a.px(18, 31, SKIN_D)  # усмешка
    a.rect(14, 33, 4, 1, mul(SKIN, 1.06))
    a.rect(0, 32, 9, 2, mul(SKIN, 0.9)), a.rect(23, 32, 9, 2, mul(SKIN, 0.9))
    a.rect(0, 34, 32, 2, SKIN_D)
    a.shade(0, 20, 32, 16, 1.06, 0.92, 0.82)
    a.noise(0, 20, 32, 16, 0.04)
    head = a.region(0, 20, 32, 16)
    # Рука 16×16: рукав трико с тенью бицепса, перчатка с раструбом от середины предплечья.
    a.rect(32, 0, 16, 10, SUIT)
    a.rect(32, 0, 16, 2, mul(SUIT, 1.12))
    a.rect(34, 5, 6, 1, SUIT_D), a.rect(42, 7, 4, 1, SUIT_D)
    a.rect(32, 10, 16, 6, GOLD)
    a.rect(32, 10, 16, 1, GOLD_L)
    a.rect(32, 11, 16, 1, GOLD_D)
    a.rect(38, 9, 3, 1, GOLD_L)  # зубец раструба
    a.rect(32, 14, 16, 1, GOLD_D)
    for x in (35, 39, 43):
        a.px(x, 15, GOLD_D)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.76)
    a.noise(32, 0, 16, 16, 0.05)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: тёмные плавки, трико с бликом колена, сапог с отворотом и вырезом спереди.
    a.rect(48, 0, 16, 14, SUIT)
    a.rect(48, 0, 16, 3, SUIT_D)
    a.rect(48, 3, 16, 1, mul(SUIT, 0.84))
    a.rect(55, 4, 1, 10, SUIT_D)
    a.rect(51, 6, 3, 1, mul(SUIT, 1.12)), a.rect(58, 8, 3, 1, SUIT_D)
    a.rect(55, 11, 2, 1, SUIT_L)  # колено
    a.rect(48, 14, 16, 10, GOLD)
    a.rect(48, 14, 16, 1, GOLD_L)
    a.rect(48, 16, 16, 1, GOLD_D)
    a.rect(55, 14, 2, 2, SUIT), a.px(54, 14, SUIT), a.px(57, 14, SUIT)
    a.rect(51, 19, 10, 1, GOLD_D)  # сгиб подъёма
    a.rect(54, 21, 4, 1, GOLD_L)
    a.rect(48, 23, 16, 1, GOLD_D)
    a.shade(48, 0, 16, 24, 1.05, 0.86, 0.76)
    a.noise(48, 0, 16, 24, 0.05)
    leg = a.region(48, 0, 16, 24)
    # Плащ: кокетка 24×4 у плеч и полотно 24×20 со складками, подол вырезан зубцами.
    a.rect(0, 40, 24, 4, GOLD)
    a.rect(0, 40, 24, 1, GOLD_L)
    a.rect(0, 43, 24, 1, GOLD_D)
    a.rect(0, 44, 24, 20, GOLD)
    for x, top, low in ((2, 46, 62), (6, 45, 60), (10, 47, 63), (14, 45, 61), (18, 46, 63), (21, 45, 60)):
        a.rect(x, top, 1, low - top, GOLD_D)
        a.rect(x + 1, top + 1, 1, low - top - 2, GOLD_L)
    a.rect(0, 44, 1, 20, GOLD_D), a.rect(23, 44, 1, 20, GOLD_D)
    a.shade(0, 44, 24, 20, 1.06, 0.82, 0.9)
    a.noise(0, 40, 24, 24, 0.06)
    for x in range(24):
        for k in range(max(0, 3 - abs(x % 8 - 4))):
            a.clear(x, 63 - k)  # зубцы подола
    cape = [a.region(i * 8, 44, 8, 20) for i in range(3)]
    yoke = [a.region(i * 8, 40, 8, 4) for i in range(3)]
    # Хохолок 8×8, подошва, темя.
    a.rect(32, 16, 8, 8, HAIR)
    for x, y in ((33, 17), (34, 18), (35, 19), (36, 17), (37, 18), (38, 20), (34, 21), (36, 22)):
        a.px(x, y, HAIR_L)
    a.noise(32, 16, 8, 8, 0.08)
    tuft = a.region(32, 16, 8, 8)
    a.rect(40, 16, 4, 4, GOLD_D)
    a.rect(44, 16, 4, 4, HAIR)
    sole, crown = a.region(40, 16, 4, 4), a.region(44, 16, 4, 4)

    parts = lm.biped(leg, torso, head, arm, sole, crown)
    # Хохолок: клин надо лбом, носом вперёд и вверх, корнем утоплен в темя.
    parts["head"][1].extend(lm.at(lm.rot(lm.box((0.1, 0.06, 0.15), tuft, tuft, tuft, (0.55, 0.8)), 22.0),
                                  0.0, 1.735, -0.06))
    # Плащ за спиной (спина это +Z): от плеч до колен, книзу шире и дальше от спины.
    parts["body"][1].extend(_drape([(0.2, 0.12), (0.07, 0.135), (-0.07, 0.135), (-0.2, 0.12)],
                                   [(0.3, 0.26), (0.1, 0.3), (-0.1, 0.3), (-0.3, 0.26)],
                                   1.4, 0.5, (1.455, 0.02), cape, yoke))
    return lm.assemble("hero", a, parts)


# --- Робот-приспешник --------------------------------------------------------------------------

def superheroes_enemy():
    """Робот-приспешник: зелёно-серый корпус-бочонок с обручами и пультом на груди, голова
    куполом с одним красным глазом в тёмной глазнице, антенна с огоньком, поршневые ноги на
    широких ступнях, руки на шарнирах: левая с клешнёй, правая с выдвижной клешнёй вперёд."""
    a = lm.Atlas(64, 64, 223)
    # Корпус 32×20, пять поясов по четыре строки: крышка, верхний обруч, пульт на груди,
    # нижний обруч, сужение ко дну.
    a.rect(0, 0, 32, 20, BOT)
    a.rect(0, 0, 32, 4, METAL)
    a.rect(0, 0, 32, 1, METAL_D)
    a.rect(0, 3, 32, 1, METAL_L)
    _rivets(a, 0, 2, 32, METAL_D, 4)
    for y in (4, 14):
        a.rect(0, y, 32, 2, BOT_D)
        _rivets(a, 0, y, 32, BOT_L, 4)
    for x in (3, 8, 23, 28):
        a.rect(x, 6, 1, 8, BOT_D)  # клёпки бочонка
        a.rect(x + 1, 7, 1, 6, BOT_L)
    a.rect(10, 6, 12, 7, METAL_D)
    a.rect(10, 6, 12, 1, METAL), a.rect(10, 12, 12, 1, BLACK)
    a.rect(11, 8, 2, 2, RED), a.px(11, 8, WHITE)
    a.px(11, 11, GOLD), a.px(13, 11, GOLD_D)
    for y in (8, 10):
        a.rect(15, y, 6, 1, METAL)  # решётка динамика
        a.rect(15, y + 1, 6, 1, BLACK)
    a.rect(0, 8, 2, 3, METAL_D), a.rect(30, 8, 2, 3, METAL_D)  # выхлоп на спине
    a.px(0, 9, BLACK), a.px(31, 9, BLACK)
    for x, y in ((5, 9), (6, 10), (25, 7), (26, 8), (20, 16), (6, 17)):
        a.px(x, y, GOLD_D)  # ржавчина
    a.rect(0, 16, 32, 4, BOT_D)
    a.rect(0, 16, 32, 1, BOT)
    a.rect(0, 19, 32, 1, METAL_D)
    a.shade(0, 0, 32, 20, 1.08, 0.84, 0.72)
    a.noise(0, 0, 32, 20, 0.06)
    body = a.region(0, 0, 32, 20)
    # Голова 32×16: купол, в середине глазница с красным глазом и бликом, хмурый козырёк,
    # болты на висках, жалюзи на затылке, внизу ворот в жёлто-чёрную полосу.
    a.rect(0, 20, 32, 16, BOT)
    a.rect(0, 20, 32, 2, BOT_L)
    a.rect(15, 20, 2, 3, BOT_D)  # шов купола
    _disc(a, 15.5, 27.5, 5.2, METAL)
    _disc(a, 15.5, 27.5, 4.4, METAL_D)
    _disc(a, 15.5, 27.5, 3.1, RED)
    _disc(a, 15.5, 27.5, 1.2, mix(RED, PEACH, 0.6))
    a.px(13, 25, WHITE), a.px(14, 25, WHITE), a.px(13, 26, WHITE)
    a.px(17, 30, RED_D), a.px(18, 29, RED_D)
    for k in range(6):
        a.px(9 + k, 22 + k // 3, BLACK), a.px(22 - k, 22 + k // 3, BLACK)  # козырёк углом
    for x in (4, 25):
        a.rect(x, 26, 3, 4, METAL), a.px(x + 1, 27, METAL_L), a.px(x + 1, 28, METAL_D)
    for y in (25, 27, 29):
        a.rect(0, y, 3, 1, BOT_D), a.rect(29, y, 3, 1, BOT_D)
    a.rect(0, 32, 32, 4, METAL_D)
    for x in range(32):
        for y in (32, 33):
            a.px(x, y, GOLD if (x + (y - 32)) // 2 % 2 == 0 else BLACK)
    a.rect(0, 34, 32, 1, METAL)
    a.shade(0, 20, 32, 16, 1.1, 0.86, 0.8)
    a.noise(0, 20, 32, 16, 0.05)
    head = a.region(0, 20, 32, 16)
    # Рука 16×16, четыре пояса: диск шарнира, шток, переход, манжета кисти.
    a.rect(32, 0, 16, 4, METAL_D)
    a.rect(32, 0, 16, 1, METAL), a.rect(38, 1, 4, 2, METAL_L), a.px(39, 2, BLACK)
    a.rect(32, 4, 16, 4, METAL)
    a.rect(32, 5, 16, 1, METAL_L), a.rect(32, 7, 16, 1, METAL_D)
    a.rect(32, 8, 16, 4, METAL_D)
    a.rect(32, 8, 16, 1, BLACK)
    a.rect(32, 12, 16, 4, BOT)
    a.rect(32, 12, 16, 1, BOT_L), a.rect(32, 15, 16, 1, BOT_D)
    _rivets(a, 32, 13, 16, BOT_D, 3)
    a.shade(32, 0, 16, 16, 1.04, 0.9, 0.72)
    a.noise(32, 0, 16, 16, 0.06)
    limb = a.region(32, 0, 16, 16)
    # Нога 16×20, пять поясов: гильза у бедра, её торец, блестящий шток, верх ступни, борт
    # ступни с протектором и жёлтым носком.
    a.rect(48, 12, 16, 4, BOT)
    a.rect(48, 12, 16, 1, BOT_D), a.rect(48, 14, 16, 1, BOT_D)
    _rivets(a, 48, 13, 16, BOT_L, 3)
    a.rect(48, 16, 16, 4, METAL_D)
    a.rect(48, 19, 16, 1, BLACK)
    a.rect(48, 20, 16, 4, METAL)
    a.rect(54, 20, 2, 4, METAL_L), a.rect(60, 20, 2, 4, METAL_D)
    a.rect(48, 22, 16, 1, METAL_D)
    a.rect(48, 24, 16, 4, METAL_D)
    a.rect(48, 27, 16, 1, METAL)
    a.rect(48, 28, 16, 4, METAL)
    a.rect(48, 28, 16, 1, METAL_L)
    a.rect(53, 29, 6, 2, GOLD), a.rect(53, 30, 6, 1, GOLD_D)
    for x in range(48, 64, 2):
        a.px(x, 31, BLACK)
    a.shade(48, 12, 16, 20, 1.04, 0.88, 0.74)
    a.noise(48, 12, 16, 20, 0.06)
    leg = a.region(48, 12, 16, 20)
    # Выдвижная клешня 32×6: гнездо у кисти, колена штока, шарнир, две губы с красной кромкой;
    # между губами и вокруг штока прозрачно.
    a.rect(0, 36, 4, 6, METAL_D)
    a.rect(4, 38, 14, 2, METAL)
    a.rect(4, 38, 14, 1, METAL_L)
    for x in (8, 13):
        a.rect(x, 37, 2, 4, METAL_D)
    a.rect(17, 37, 4, 4, METAL_D), a.rect(18, 38, 2, 2, GREY)
    for y, inner in ((36, 37), (41, 40)):
        a.rect(20, y, 10, 1, METAL_L if y == 36 else METAL)
        a.rect(20, inner, 3, 1, METAL), a.rect(27, inner, 5, 1, METAL)
        a.rect(23, inner, 4, 1, RED)
    a.px(31, 38, METAL_L), a.px(31, 39, METAL)
    claw = a.region(0, 36, 32, 6)
    # Клешня левой руки 8×8 полумесяцем вниз, антенна 8×8: стебель и красный огонёк.
    _disc(a, 35.5, 19.0, 3.6, METAL)
    _disc(a, 35.5, 21.2, 2.3, BLACK)
    for y in range(16, 24):
        for x in range(32, 40):
            if a.get(x, y)[:3] == tuple(BLACK) or y > 22:
                a.clear(x, y)
    a.rect(34, 16, 3, 1, METAL_D), a.px(33, 18, METAL_L), a.px(38, 18, METAL_D)
    a.px(33, 21, RED), a.px(38, 21, RED)
    pincer = a.region(32, 16, 8, 8)
    a.rect(51, 3, 2, 5, METAL_D)
    a.rect(50, 0, 4, 3, RED), a.px(50, 0, WHITE), a.px(53, 2, RED_D)
    a.px(49, 1, RED_D), a.px(54, 1, RED_D)
    feeler = a.region(48, 0, 8, 8)
    a.rect(56, 0, 4, 4, METAL_D)
    a.rect(60, 0, 4, 4, BOT_L)
    chip, crown = a.region(56, 0, 4, 4), a.region(60, 0, 4, 4)

    m = lm.Model("enemy", a)
    for side, x in (("l", -0.09), ("r", 0.09)):
        m.part("leg_" + side, (x, 0.86, 0.0),
               lm.loft([(0.0, 0.075, 0.13, x, -0.03), (0.09, 0.068, 0.115, x, -0.03), (0.13, 0.034, 0.034, x, 0.0),
                        (0.5, 0.034, 0.034, x, 0.0), (0.54, 0.054, 0.054, x, 0.0), (0.88, 0.054, 0.054, x, 0.0)],
                       leg, 4, math.pi / 4.0, caps=(chip, None)))
    m.part("body", (0.0, 0.86, 0.0),
           lm.loft([(0.62, 0.12, 0.115), (0.7, 0.172, 0.168), (0.9, 0.19, 0.186), (1.16, 0.19, 0.186),
                    (1.4, 0.176, 0.17), (1.46, 0.08, 0.08)], body, 6, caps=(chip, None)))
    m.part("head", (0.0, 1.46, 0.0),
           lm.loft([(1.43, 0.085, 0.085), (1.48, 0.165, 0.165), (1.62, 0.175, 0.175), (1.74, 0.13, 0.13),
                    (1.8, 0.045, 0.045)], head, 6, caps=(None, crown))
           + lm.quad((-0.06, 1.93, 0.0), (0.06, 1.93, 0.0), (0.06, 1.77, 0.0), (-0.06, 1.77, 0.0), feeler)
           + lm.quad((0.0, 1.93, -0.06), (0.0, 1.93, 0.06), (0.0, 1.77, 0.06), (0.0, 1.77, -0.06), feeler), "body")
    # Руки вынесены за бока бочонка: диск шарнира утоплен в корпус, шток висит снаружи.
    rings = lambda x: [(0.74, 0.05, 0.055, x * 1.05, 0.0), (0.86, 0.05, 0.055, x * 1.05, 0.0),
                       (0.9, 0.03, 0.03, x * 1.04, 0.0), (1.33, 0.03, 0.03, x, 0.0), (1.42, 0.056, 0.056, x, 0.0)]
    m.part("arm_l", (-0.2, 1.38, 0.0),
           lm.loft(rings(-0.225), limb, 4, math.pi / 4.0, caps=(chip, chip))
           + lm.quad((-0.236, 0.78, -0.07), (-0.236, 0.78, 0.07), (-0.236, 0.6, 0.07), (-0.236, 0.6, -0.07), pincer),
           "body")
    m.part("arm_r", (0.2, 1.38, 0.0),
           lm.loft(rings(0.225), limb, 4, math.pi / 4.0, caps=(chip, chip))
           + lm.quad((0.236, 0.85, -0.02), (0.236, 0.85, -0.72), (0.236, 0.73, -0.72), (0.236, 0.73, -0.02), claw), "body")
    return m


# --- Злодей-учёный -----------------------------------------------------------------------------

def superheroes_captain():
    """Злодей-учёный: второй боец и главарь. Белый лабораторный халат с косой застёжкой, чёрные
    резиновые перчатки, стальной шлем с полями, зелёными колбами и двумя электродами с искрой,
    красные очки, оскал и бородка; за спиной зелёный плащ до колен со стоячим воротом."""
    a = lm.Atlas(64, 64, 243)
    pants, pants_d = mix(SUIT_D, BLACK, 0.45), mix(SUIT_D, BLACK, 0.7)
    # Халат 32×20: плечи под воротом плаща с золотой цепью, косой борт с пуговицами, карман с
    # ручками, значок, пояс с пряжкой и подсумками.
    a.rect(0, 0, 32, 17, WHITE)
    a.rect(0, 0, 32, 2, GREEN_D)
    a.rect(0, 2, 32, 1, GREEN)
    for x in (9, 21):
        a.rect(x, 2, 2, 2, GOLD), a.px(x, 3, GOLD_D)
    for x in range(11, 21, 2):
        a.px(x, 4, GOLD), a.px(x + 1, 3, GOLD_D)  # цепь застёжки
    for x in (5, 26):
        a.rect(x, 5, 1, 12, GREY)  # складки на боках
    a.rect(18, 5, 1, 12, GREY)  # косой борт
    a.rect(19, 5, 1, 12, mul(WHITE, 0.93))
    for y in (7, 10, 13):
        a.px(16, y, METAL_D), a.px(20, y, METAL_D)
    a.rect(8, 8, 4, 4, mul(WHITE, 0.9)), a.rect(8, 8, 4, 1, GREY)
    a.px(9, 7, RED), a.px(10, 7, SUIT), a.px(11, 7, METAL_D)  # ручки в кармане
    a.rect(22, 6, 3, 3, GREEN_D), a.px(23, 7, GOLD)  # значок
    for x, y in ((12, 14), (13, 15), (24, 12), (7, 14)):
        a.px(x, y, mix(WHITE, GREEN_L, 0.5))  # пятна реактивов
    a.rect(0, 17, 32, 3, METAL_D)
    a.rect(0, 17, 32, 1, METAL)
    a.rect(14, 17, 4, 3, GOLD), a.rect(15, 18, 2, 1, RED)
    for x in (5, 24):
        a.rect(x, 17, 3, 3, METAL), a.px(x + 1, 18, GREEN_L)
    a.shade(0, 0, 32, 20, 1.08, 0.84, 0.74)
    a.noise(0, 0, 32, 20, 0.05)
    torso = a.region(0, 0, 32, 20)
    # Голова 32×24, шесть поясов по четыре строки сверху вниз: макушка шлема, купол с колбами
    # и молнией (два пояса), поля снизу, лицо с очками, оскал с бородкой и шея.
    a.rect(0, 20, 32, 12, METAL)
    a.rect(0, 20, 32, 2, METAL_L)
    for x in (5, 15, 16, 26):
        a.rect(x, 22, 1, 10, METAL_D)  # швы пластин
    _rivets(a, 0, 23, 32, METAL_L, 4)
    _rivets(a, 0, 30, 32, METAL_D, 4)
    for x in (8, 21):
        a.rect(x, 24, 3, 6, BLACK)
        a.rect(x, 26, 3, 4, GREEN), a.rect(x + 1, 26, 1, 3, GREEN_L)
        a.px(x + 1, 25, GREEN_L)  # пузырёк в колбе
    _stamp(a, 13, 24, ("..##.", ".##..", "####.", ".###.", "..##.", ".##..", "#...."), GOLD)
    a.px(15, 24, GOLD_L), a.px(14, 26, GOLD_L)
    a.rect(0, 32, 32, 4, METAL_D)
    a.rect(0, 32, 32, 1, METAL_L)
    a.rect(0, 35, 32, 1, BLACK)
    _rivets(a, 0, 33, 32, GOLD, 4)
    a.rect(0, 36, 32, 8, SKIN)
    a.rect(0, 36, 8, 8, METAL_D), a.rect(24, 36, 8, 8, METAL_D)  # назатыльник шлема
    a.rect(0, 39, 8, 1, METAL), a.rect(24, 39, 8, 1, METAL)
    a.rect(8, 37, 16, 1, BLACK)  # ремень очков
    for x in (10, 18):
        a.rect(x, 36, 4, 4, BLACK)
        a.rect(x + 1, 37, 2, 2, RED), a.px(x + 1, 37, WHITE)
    a.rect(14, 37, 4, 1, METAL)
    a.rect(15, 38, 2, 2, mul(SKIN, 0.88))
    a.rect(11, 40, 10, 2, BLACK)
    for x in range(12, 20):
        a.px(x, 40, WHITE if x % 2 == 0 else GREY)  # оскал
        a.px(x, 41, GREY if x % 2 == 0 else WHITE)
    a.px(10, 39, SKIN_D), a.px(21, 39, SKIN_D)  # складки у рта
    a.rect(14, 42, 4, 2, GREY), a.px(15, 43, WHITE), a.px(13, 42, GREY), a.px(18, 42, GREY)
    a.rect(8, 42, 5, 2, SKIN_D), a.rect(19, 42, 5, 2, SKIN_D)
    a.shade(0, 20, 32, 24, 1.08, 0.9, 0.84)
    a.noise(0, 20, 32, 24, 0.05)
    head = a.region(0, 20, 32, 24)
    # Рукав 16×16: халат со складками, красная кромка, чёрная резиновая перчатка с бликом.
    a.rect(32, 0, 16, 9, WHITE)
    a.rect(32, 0, 16, 1, GREEN_D)
    for x in (36, 43):
        a.rect(x, 2, 1, 6, GREY)
    a.rect(32, 8, 16, 1, GREY)
    a.rect(32, 9, 16, 1, RED)
    a.rect(32, 10, 16, 6, BLACK)
    a.rect(32, 10, 16, 1, METAL_D)
    a.rect(38, 11, 2, 3, METAL_D), a.px(38, 11, METAL)
    for x in (35, 39, 43):
        a.px(x, 15, METAL_D)
    a.shade(32, 0, 16, 16, 1.05, 0.9, 0.76)
    a.noise(32, 0, 16, 16, 0.05)
    arm = a.region(32, 0, 16, 16)
    # Нога 16×24: пола халата до колена, тёмные брюки со стрелкой, сапог с ремнями и
    # стальным носком.
    a.rect(48, 0, 16, 14, pants)
    a.rect(48, 0, 16, 10, WHITE)
    a.rect(48, 9, 16, 1, GREY)
    a.rect(52, 0, 1, 9, GREY), a.rect(59, 1, 1, 8, GREY)
    a.px(56, 7, mix(WHITE, GREEN_L, 0.5))
    a.rect(55, 10, 1, 4, pants_d)
    a.rect(50, 12, 3, 1, pants_d)
    a.rect(48, 14, 16, 10, METAL_D)
    a.rect(48, 14, 16, 1, METAL)
    for y in (16, 18):
        a.rect(48, y, 16, 1, BLACK)
        a.rect(55, y, 2, 1, GOLD)
    a.rect(52, 20, 8, 3, METAL), a.rect(52, 20, 8, 1, METAL_L)
    a.rect(48, 23, 16, 1, BLACK)
    a.shade(48, 0, 16, 24, 1.05, 0.86, 0.76)
    a.noise(48, 0, 16, 24, 0.06)
    leg = a.region(48, 0, 16, 24)
    # Плащ 24×20: складки, по подолу тёмная кайма углами, светлые края.
    a.rect(0, 44, 24, 20, GREEN)
    for x in (3, 7, 12, 16, 20):
        a.rect(x, 45, 1, 17, GREEN_D)
        a.rect(x + 1, 46, 1, 15, GREEN_L)
    a.rect(0, 60, 24, 4, GREEN_D)
    for x in range(24):
        a.px(x, 60 + abs(x % 4 - 2), GOLD)
    a.rect(0, 44, 1, 20, GREEN_L), a.rect(23, 44, 1, 20, GREEN_L)
    a.shade(0, 44, 24, 20, 1.05, 0.8, 0.86)
    a.noise(0, 44, 24, 20, 0.07)
    cloak = [a.region(i * 8, 44, 8, 20) for i in range(3)]
    # Кокетка 24×4 и стоячий ворот 24×8 с золотым кантом.
    a.rect(24, 44, 24, 4, GREEN_D)
    a.rect(24, 44, 24, 1, GOLD_D)
    a.rect(24, 48, 24, 8, GREEN_D)
    a.rect(24, 48, 24, 1, GOLD), a.rect(24, 49, 24, 1, GOLD_D)
    for x in (27, 31, 35, 40, 44):
        a.rect(x, 50, 1, 6, mix(GREEN_D, BLACK, 0.4))
        a.rect(x + 1, 51, 1, 5, GREEN)
    a.noise(24, 44, 24, 12, 0.07)
    yoke = [a.region(24 + i * 8, 44, 8, 4) for i in range(3)]
    collar = [a.region(24 + i * 8, 48, 8, 8) for i in range(3)]
    # Электроды 16×8: два стержня с витками и красными шарами, между шарами искра.
    for x0, d in ((32, 1), (47, -1)):
        for k in range(5):
            x = x0 + d * (1 + (k + 1) // 2)
            a.px(x, 27 + k, METAL if k % 2 == 0 else METAL_D)
            a.px(x + d, 27 + k, METAL_L if k % 2 == 0 else METAL)
        a.rect(min(x0, x0 + d * 2), 24, 3, 3, RED)
        a.px(x0 + d, 24, GOLD_L), a.px(x0 + d, 26, RED_D)
    for x, y in ((35, 25), (36, 24), (37, 25), (38, 26), (39, 25), (40, 24), (41, 25), (42, 26), (43, 25), (44, 24)):
        a.px(x, y, WHITE if x % 2 else PEACH)
    rods = a.region(32, 24, 16, 8)
    a.rect(32, 16, 4, 4, BLACK)
    a.rect(36, 16, 4, 4, METAL_L)
    a.px(37, 17, METAL_D), a.px(38, 18, METAL_D)
    sole, crown = a.region(32, 16, 4, 4), a.region(36, 16, 4, 4)

    parts = lm.biped(leg, torso, head, arm, sole, crown, 1.18)
    # Голова: лицо, поля шлема шире лица, над ними высокий купол; электроды из купола врозь и
    # вверх, корнями утоплены в сталь.
    parts["head"][1] = lm.loft([(1.44, 0.065, 0.07), (1.51, 0.105, 0.115, 0.0, -0.005), (1.6, 0.125, 0.135),
                                (1.64, 0.175, 0.18), (1.69, 0.14, 0.15), (1.79, 0.13, 0.14), (1.84, 0.06, 0.065)],
                               head, 6, caps=(None, crown))
    parts["head"][1].extend(lm.quad((-0.2, 1.93, 0.0), (0.2, 1.93, 0.0), (0.2, 1.73, 0.0), (-0.2, 1.73, 0.0), rods))
    # Плащ: три полотнища от плеч до колен, книзу шире и дальше от спины; над плечами ворот.
    top = [(0.27, 0.19), (0.09, 0.2), (-0.09, 0.2), (-0.27, 0.19)]
    low = [(0.37, 0.3), (0.13, 0.34), (-0.13, 0.34), (-0.37, 0.3)]
    high = [(0.25, 0.12), (0.09, 0.23), (-0.09, 0.23), (-0.25, 0.12)]
    cloth = _drape(top, low, 1.4, 0.5, (1.46, 0.03), cloak, yoke)
    for i in range(3):
        cloth += lm.quad((high[i][0], 1.62, high[i][1]), (high[i + 1][0], 1.62, high[i + 1][1]),
                         (top[i + 1][0], 1.4, top[i + 1][1]), (top[i][0], 1.4, top[i][1]), collar[i])
    parts["body"][1].extend(cloth)
    return lm.assemble("captain", a, parts)


MODELS = [superheroes_hero, superheroes_enemy, superheroes_captain]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        models = [f() for f in MODELS]
        for m in models:
            print("%-8s частей %d, треугольников %d" % (m.name, len(m.parts), m.tris()))
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
